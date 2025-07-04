package main

import (
	"fmt"
	"syscall"
)

func main() {
	fs := syscall.Statfs_t{}
	err := syscall.Statfs("/", &fs)
	if err != nil {
		panic(err)
	}

	total := fs.Blocks * uint64(fs.Bsize)
	free := fs.Bfree * uint64(fs.Bsize)
	used := total - free

	fmt.Printf("Disk Usage:\nTotal: %d MB\nUsed: %d MB\nFree: %d MB\n",
		total/1024/1024, used/1024/1024, free/1024/1024)
}
