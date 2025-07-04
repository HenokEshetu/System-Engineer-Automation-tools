#!/bin/bash

# Ensure the script is run with sudo/root
if [[ "$EUID" -ne 0 ]]; then
    echo "[Error] Please run this script as root (e.g., sudo $0)"
    exit 1
fi

# -------------------------------
# CONFIGURATION
# -------------------------------

# Default log directories to check based on OS
LINUX_LOG_DIRS=("/var/log")
MAC_LOG_DIRS=("/private/var/log")
WINDOWS_LOG_DIRS=("/c/Windows/System32/winevt/Logs")

# Default log file extensions to look for
LOG_EXTENSIONS=("log" "out")

# Log rotation settings
MAX_SIZE_MB=10       # Rotate logs over 10 MB
MAX_BACKUPS=5        # Keep last 5 compressed archives
ROTATOR_LOG="/var/log/log_rotator_activity.log"

# Date format for rotated logs
TIMESTAMP=$(date "+%Y%m%d_%H%M%S")

# -------------------------------
# Detect OS
# -------------------------------
OS=$(uname -s)
LOG_DIRS=()

case "$OS" in
    Linux)
        LOG_DIRS=("${LINUX_LOG_DIRS[@]}")
        ;;
    Darwin)
        LOG_DIRS=("${MAC_LOG_DIRS[@]}")
        ;;
    MINGW*|MSYS*|CYGWIN*)
        LOG_DIRS=("${WINDOWS_LOG_DIRS[@]}")
        ;;
    *)
        echo "[Error] Unsupported OS: $OS" | tee -a "$ROTATOR_LOG"
        exit 1
        ;;
esac

# -------------------------------
# Rotate a Single Log File
# -------------------------------
rotate_log() {
    local logfile="$1"
    local size_mb
    size_mb=$(du -m "$logfile" | cut -f1)

    if [[ "$size_mb" -ge "$MAX_SIZE_MB" ]]; then
        local dir
        dir=$(dirname "$logfile")
        local base
        base=$(basename "$logfile")
        local rotated="$dir/${base}_${TIMESTAMP}.gz"

        echo "[ℹ] Rotating $logfile ($size_mb MB) → $rotated" | tee -a "$ROTATOR_LOG"

        # Compress and archive
        gzip -c "$logfile" > "$rotated" && truncate -s 0 "$logfile"

        # Clean up old backups
        find "$dir" -name "${base}_*.gz" -type f -printf "%T@ %p\n" 2>/dev/null \
            | sort -n | awk 'NR>'"$MAX_BACKUPS"'{print $2}' | xargs -r rm -f
    fi
}

# -------------------------------
# Find and Rotate Logs
# -------------------------------
echo "Starting log rotation at $TIMESTAMP" | tee -a "$ROTATOR_LOG"

for log_dir in "${LOG_DIRS[@]}"; do
    if [[ -d "$log_dir" ]]; then
        while IFS= read -r -d '' logfile; do
            rotate_log "$logfile"
        done < <(find "$log_dir" -type f \( $(printf -- '-name "*.%s" -o ' "${LOG_EXTENSIONS[@]}" | sed 's/ -o $//') \) -print0)
    fi
done

echo "[Success] Log rotation completed." | tee -a "$ROTATOR_LOG"
