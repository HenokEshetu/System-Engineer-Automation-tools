#!/bin/bash

echo "[+] Scanning for SUID binaries..."
find / -perm -4000 -type f 2>/dev/null > suid_files.txt
echo "[+] Results saved to suid_files.txt"
