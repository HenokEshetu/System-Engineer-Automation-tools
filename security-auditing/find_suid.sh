#!/bin/bash

# ------------------------------------
# SUID Scanner (Linux/macOS)
# ------------------------------------

OUTFILE="suid_files.txt"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
HOSTNAME=$(hostname)
OS=$(uname -s)

echo "[Success] SUID Scanner Started - $TIMESTAMP on $HOSTNAME"
echo "[+] Detected OS: $OS"

# ------------------------------------
# Platform Support Check
# ------------------------------------
case "$OS" in
    Linux|Darwin)
        ;;
    *)
        echo "[Error] Unsupported OS: $OS"
        exit 1
        ;;
esac

# ------------------------------------
# Scan for SUID Binaries
# ------------------------------------
echo "[+] Scanning system for SUID binaries (this may take a while)..."
if [[ "$EUID" -ne 0 ]]; then
    echo "[!] It's recommended to run this as root to detect all files."
fi

find / -perm -4000 -type f 2>/dev/null | tee "$OUTFILE"

echo "[Success] Scan complete. Results saved to: $OUTFILE"
