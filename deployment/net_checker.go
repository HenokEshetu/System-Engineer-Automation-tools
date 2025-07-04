package main

import (
	"fmt"
	"net"
	"time"
)

func check(host string) {
	timeout := 2 * time.Second
	_, err := net.DialTimeout("tcp", host, timeout)
	if err != nil {
		fmt.Printf("%s is unreachable\n", host)
	} else {
		fmt.Printf("%s is online\n", host)
	}
}

func main() {
	hosts := []string{"8.8.8.8:53", "1.1.1.1:53", "example.com:80"}
	for _, host := range hosts {
		check(host)
	}
}
