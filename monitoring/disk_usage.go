package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/dustin/go-humanize"
	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/disk"
	"github.com/shirou/gopsutil/v3/mem"
	"github.com/shirou/gopsutil/v3/net"
	"gopkg.in/natefinch/lumberjack.v2"
)

// Config holds application configuration
type Config struct {
	Interval    time.Duration `json:"interval"`
	LogPath     string        `json:"log_path"`
	Thresholds  Thresholds    `json:"thresholds"`
	MonitorDisk string        `json:"monitor_disk"`
}

// Thresholds defines alert thresholds
type Thresholds struct {
	CPU    float64 `json:"cpu"`
	Memory float64 `json:"memory"`
	Disk   float64 `json:"disk"`
}

// SystemMetrics holds collected system metrics
type SystemMetrics struct {
	Timestamp time.Time `json:"timestamp"`
	CPU       struct {
		Total    float64   `json:"total"`
		PerCore  []float64 `json:"per_core,omitempty"`
		Load     []float64 `json:"load,omitempty"`
	} `json:"cpu"`
	Memory struct {
		Total     uint64  `json:"total"`
		Available uint64  `json:"available"`
		Used      uint64  `json:"used"`
		UsedPct   float64 `json:"used_percent"`
	} `json:"memory"`
	Disk struct {
		Path      string  `json:"path"`
		Total     uint64  `json:"total"`
		Free      uint64  `json:"free"`
		Used      uint64  `json:"used"`
		UsedPct   float64 `json:"used_percent"`
		ReadRate  uint64  `json:"read_rate,omitempty"`
		WriteRate uint64  `json:"write_rate,omitempty"`
	} `json:"disk"`
	Network struct {
		BytesSent uint64 `json:"bytes_sent"`
		BytesRecv uint64 `json:"bytes_recv"`
	} `json:"network"`
	Alerts []string `json:"alerts,omitempty"`
}

var (
	prevDiskIO  *disk.IOCountersStat
	prevNetIO   *net.IOCountersStat
	lastIORead  time.Time
)

func main() {
	// Load configuration (could be extended to read from file)
	config := Config{
		Interval:    30 * time.Second,
		LogPath:     "/var/log/system_monitor.log",
		MonitorDisk: "/",
		Thresholds: Thresholds{
			CPU:    90,
			Memory: 85,
			Disk:   90,
		},
	}

	// Setup log rotation
	log.SetOutput(&lumberjack.Logger{
		Filename:   config.LogPath,
		MaxSize:    10, // MB
		MaxBackups: 5,
		MaxAge:     30, // days
		Compress:   true,
	})

	// Setup signal handling for graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	defer signal.Stop(sigChan)

	log.Println("=== Starting System Monitor ===")
	log.Printf("Config: Interval=%s, Disk=%s, Thresholds: CPU=%.0f%%, Memory=%.0f%%, Disk=%.0f%%",
		config.Interval, config.MonitorDisk, config.Thresholds.CPU, config.Thresholds.Memory, config.Thresholds.Disk)

	// Initial disk I/O reading
	initDiskIO(config.MonitorDisk)
	
	// Main monitoring loop
	ticker := time.NewTicker(config.Interval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			metrics := collectMetrics(config.MonitorDisk)
			checkThresholds(&metrics, config.Thresholds)
			logMetrics(metrics)
			
		case sig := <-sigChan:
			log.Printf("Received signal %v. Shutting down...", sig)
			return
		}
	}
}

func initDiskIO(diskPath string) {
	partitions, err := disk.Partitions(true)
	if err != nil {
		log.Printf("Error getting partitions: %v", err)
		return
	}

	for _, p := range partitions {
		if p.Mountpoint == diskPath {
			io, err := disk.IOCounters(p.Device)
			if err == nil && len(io) > 0 {
				// Get first (and should be only) counter for this device
				for _, v := range io {
					prevDiskIO = &v
					break
				}
				lastIORead = time.Now()
				return
			}
		}
	}
	log.Printf("Could not initialize disk I/O for %s", diskPath)
}

func collectMetrics(diskPath string) SystemMetrics {
	var metrics SystemMetrics
	metrics.Timestamp = time.Now().UTC()

	// CPU Metrics
	if percents, err := cpu.Percent(0, true); err == nil {
		metrics.CPU.PerCore = percents
		total := 0.0
		for _, p := range percents {
			total += p
		}
		metrics.CPU.Total = total / float64(len(percents))
	}

	if load, err := cpu.LoadAvg(); err == nil {
		metrics.CPU.Load = []float64{load.Load1, load.Load5, load.Load15}
	}

	// Memory Metrics
	if memStat, err := mem.VirtualMemory(); err == nil {
		metrics.Memory.Total = memStat.Total
		metrics.Memory.Available = memStat.Available
		metrics.Memory.Used = memStat.Used
		metrics.Memory.UsedPct = memStat.UsedPercent
	}

	// Disk Metrics
	if diskStat, err := disk.Usage(diskPath); err == nil {
		metrics.Disk.Path = diskPath
		metrics.Disk.Total = diskStat.Total
		metrics.Disk.Free = diskStat.Free
		metrics.Disk.Used = diskStat.Used
		metrics.Disk.UsedPct = diskStat.UsedPercent
	}

	// Disk I/O Rate
	if prevDiskIO != nil {
		if io, err := disk.IOCounters(prevDiskIO.Name); err == nil && len(io) > 0 {
			var currentIO disk.IOCountersStat
			for _, v := range io {
				if v.Name == prevDiskIO.Name {
					currentIO = v
					break
				}
			}

			duration := time.Since(lastIORead).Seconds()
			if duration > 0 {
				metrics.Disk.ReadRate = uint64(float64(currentIO.ReadBytes-prevDiskIO.ReadBytes) / duration)
				metrics.Disk.WriteRate = uint64(float64(currentIO.WriteBytes-prevDiskIO.WriteBytes) / duration)
			}
			prevDiskIO = &currentIO
			lastIORead = time.Now()
		}
	}

	// Network Metrics
	if netIO, err := net.IOCounters(false); err == nil && len(netIO) > 0 {
		metrics.Network.BytesSent = netIO[0].BytesSent
		metrics.Network.BytesRecv = netIO[0].BytesRecv
	}

	return metrics
}

func checkThresholds(metrics *SystemMetrics, thresholds Thresholds) {
	metrics.Alerts = []string{}

	if metrics.CPU.Total > thresholds.CPU {
		metrics.Alerts = append(metrics.Alerts, 
			fmt.Sprintf("High CPU usage: %.1f%% > %.0f%%", metrics.CPU.Total, thresholds.CPU))
	}

	if metrics.Memory.UsedPct > thresholds.Memory {
		metrics.Alerts = append(metrics.Alerts, 
			fmt.Sprintf("High memory usage: %.1f%% > %.0f%%", metrics.Memory.UsedPct, thresholds.Memory))
	}

	if metrics.Disk.UsedPct > thresholds.Disk {
		metrics.Alerts = append(metrics.Alerts, 
			fmt.Sprintf("High disk usage: %.1f%% > %.0f%%", metrics.Disk.UsedPct, thresholds.Disk))
	}
}

func logMetrics(metrics SystemMetrics) {
	jsonData, err := json.Marshal(metrics)
	if err != nil {
		log.Printf("Error marshaling metrics: %v", err)
		return
	}

	if len(metrics.Alerts) > 0 {
		log.Printf("ALERT: %s", string(jsonData))
	} else {
		log.Println(string(jsonData))
	}
}

// Helper function for human-readable output (not used in logging, but available for debugging)
func formatBytes(bytes uint64) string {
	return humanize.Bytes(bytes)
}