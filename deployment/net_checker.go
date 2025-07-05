package main

import (
	"bufio"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net"
	"os"
	"os/exec"
	"os/signal"
	"strings"
	"sync"
	"syscall"
	"time"
)

// Config holds application configuration
type Config struct {
	Hosts       []string      `json:"hosts"`
	Concurrency int           `json:"concurrency"`
	Timeout     time.Duration `json:"timeout"`
	Interval    time.Duration `json:"interval"`
	Count       int           `json:"count"`
	OutputJSON  bool          `json:"output_json"`
	ICMP        bool          `json:"icmp"`
	Verbose     bool          `json:"verbose"`
}

// CheckResult holds the result of a connectivity check
type CheckResult struct {
	Host     string        `json:"host"`
	Reachable bool         `json:"reachable"`
	Latency  time.Duration `json:"latency,omitempty"`
	Error    string        `json:"error,omitempty"`
	Protocol string        `json:"protocol"`
	Timestamp time.Time    `json:"timestamp"`
}

func main() {
	// Parse command-line flags
	var (
		hostsFile   = flag.String("f", "", "File containing hosts to check (one per line)")
		concurrency = flag.Int("c", 10, "Number of concurrent checks")
		timeout     = flag.Duration("t", 2*time.Second, "Connection timeout")
		interval    = flag.Duration("i", 0, "Continuous check interval (0 for single check)")
		count       = flag.Int("n", 0, "Number of checks to run (0 for infinite)")
		outputJSON  = flag.Bool("j", false, "Output in JSON format")
		icmp        = flag.Bool("icmp", false, "Use ICMP (ping) instead of TCP")
		verbose     = flag.Bool("v", false, "Verbose output")
	)

	flag.Parse()

	// Load hosts from command-line arguments and/or file
	hosts := flag.Args()
	if *hostsFile != "" {
		fileHosts, err := loadHostsFromFile(*hostsFile)
		if err != nil {
			log.Fatalf("Error loading hosts from file: %v", err)
		}
		hosts = append(hosts, fileHosts...)
	}

	if len(hosts) == 0 {
		log.Fatal("No hosts specified. Provide hosts as arguments or via -f option")
	}

	config := Config{
		Hosts:       hosts,
		Concurrency: *concurrency,
		Timeout:     *timeout,
		Interval:    *interval,
		Count:       *count,
		OutputJSON:  *outputJSON,
		ICMP:        *icmp,
		Verbose:     *verbose,
	}

	// Handle graceful shutdown
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-sigCh
		if config.Verbose {
			fmt.Println("\nShutting down...")
		}
		cancel()
	}()

	// Run the checks
	if config.Interval > 0 {
		runContinuousChecks(ctx, config)
	} else {
		runSingleCheck(ctx, config)
	}
}

func runSingleCheck(ctx context.Context, config Config) {
	results := checkHosts(ctx, config, config.Hosts)
	printResults(results, config.OutputJSON)
}

func runContinuousChecks(ctx context.Context, config Config) {
	ticker := time.NewTicker(config.Interval)
	defer ticker.Stop()

	checkCount := 0
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			if config.Verbose {
				log.Printf("Starting check cycle #%d\n", checkCount+1)
			}

			results := checkHosts(ctx, config, config.Hosts)
			printResults(results, config.OutputJSON)

			checkCount++
			if config.Count > 0 && checkCount >= config.Count {
				return
			}
		}
	}
}

func checkHosts(ctx context.Context, config Config, hosts []string) []CheckResult {
	var wg sync.WaitGroup
	results := make(chan CheckResult, len(hosts))
	sem := make(chan struct{}, config.Concurrency)

	for _, host := range hosts {
		wg.Add(1)
		go func(h string) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()

			select {
			case <-ctx.Done():
				return
			default:
				results <- checkHost(ctx, h, config)
			}
		}(host)
	}

	wg.Wait()
	close(results)

	var resultSlice []CheckResult
	for res := range results {
		resultSlice = append(resultSlice, res)
	}

	return resultSlice
}

func checkHost(ctx context.Context, host string, config Config) CheckResult {
	start := time.Now()
	protocol := "tcp"
	if config.ICMP {
		protocol = "icmp"
	}

	result := CheckResult{
		Host:      host,
		Protocol:  protocol,
		Timestamp: time.Now().UTC(),
	}

	ctx, cancel := context.WithTimeout(ctx, config.Timeout)
	defer cancel()

	var err error
	if config.ICMP {
		err = pingHost(ctx, host)
	} else {
		err = connectTCP(ctx, host)
	}

	if err != nil {
		result.Reachable = false
		result.Error = err.Error()
	} else {
		result.Reachable = true
		result.Latency = time.Since(start).Round(time.Millisecond)
	}

	return result
}

func pingHost(ctx context.Context, host string) error {
	// Using system ping command for simplicity (cross-platform alternative would require raw sockets)
	// Note: This works on Linux/macOS. For Windows, use "ping -n 1 -w <timeout_ms> <host>"
	// In production, consider using a proper ICMP library like go-ping
	cmd := exec.CommandContext(ctx, "ping", "-c", "1", "-W", "1", host)
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("ICMP unreachable: %w", err)
	}
	return nil
}

func connectTCP(ctx context.Context, host string) error {
	var d net.Dialer
	conn, err := d.DialContext(ctx, "tcp", host)
	if err != nil {
		return fmt.Errorf("TCP unreachable: %w", err)
	}
	conn.Close()
	return nil
}

func printResults(results []CheckResult, outputJSON bool) {
	if outputJSON {
		jsonData, err := json.Marshal(results)
		if err != nil {
			log.Printf("Error marshaling results: %v", err)
			return
		}
		fmt.Println(string(jsonData))
		return
	}

	for _, res := range results {
		if res.Reachable {
			fmt.Printf("\033[32m✓ %s is reachable via %s (latency: %s)\033[0m\n",
				res.Host, res.Protocol, res.Latency)
		} else {
			fmt.Printf("\033[31m✗ %s is unreachable via %s: %s\033[0m\n",
				res.Host, res.Protocol, res.Error)
		}
	}
}

func loadHostsFromFile(filename string) ([]string, error) {
	file, err := os.Open(filename)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	var hosts []string
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		host := strings.TrimSpace(scanner.Text())
		if host != "" && !strings.HasPrefix(host, "#") {
			hosts = append(hosts, host)
		}
	}

	if err := scanner.Err(); err != nil {
		return nil, err
	}

	return hosts, nil
}
