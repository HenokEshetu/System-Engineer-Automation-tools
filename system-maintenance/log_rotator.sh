#!/bin/bash

# -------------------------------
# Require root privileges
# -------------------------------
if [[ "$EUID" -ne 0 ]]; then
    echo "[Error] Please run this script as root (e.g., sudo $0)"
    exit 1
fi

# -------------------------------
# CONFIGURATION
# -------------------------------

LINUX_LOG_DIRS=("/var/log")
MAC_LOG_DIRS=("/private/var/log")
WINDOWS_LOG_DIRS=("/c/Windows/System32/winevt/Logs")
LOG_EXTENSIONS=("log" "out")
MAX_SIZE_MB=10
MAX_BACKUPS=5
ROTATOR_LOG="/var/log/log_rotator_activity.log"

# -------------------------------
# Detect Operating System
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
# Log Rotation Function
# -------------------------------
rotate_log() {
    local logfile="$1"
    local size_mb=$(du -m "$logfile" | cut -f1)

    if [[ "$size_mb" -ge "$MAX_SIZE_MB" ]]; then
        local dir base rotated timestamp
        dir=$(dirname "$logfile")
        base=$(basename "$logfile")
        timestamp=$(date "+%Y%m%d_%H%M%S")
        rotated="$dir/${base}_${timestamp}.gz"

        echo "[ℹ] Rotating: $logfile ($size_mb MB) → $rotated" | tee -a "$ROTATOR_LOG"

        if gzip -c "$logfile" > "$rotated" && truncate -s 0 "$logfile"; then
            echo "[Success] Rotated $base" | tee -a "$ROTATOR_LOG"
        else
            echo "[Error] Failed to rotate $logfile" | tee -a "$ROTATOR_LOG"
            return
        fi

        # Prune old backups
        if command -v find > /dev/null; then
            find "$dir" -maxdepth 1 -type f -name "${base}_*.gz" \
                -printf "%T@ %p\n" 2>/dev/null | sort -n | awk "NR>$MAX_BACKUPS {print \$2}" | xargs -r rm -f
        else
            # macOS fallback: use ls + awk
            ls -t "$dir"/${base}_*.gz 2>/dev/null | awk "NR>$MAX_BACKUPS" | xargs -r rm -f
        fi
    fi
}

# -------------------------------
# Main: Scan and Rotate
# -------------------------------
start_time=$(date "+%Y-%m-%d %H:%M:%S")
echo "[...] Log rotation started at $start_time" | tee -a "$ROTATOR_LOG"

for log_dir in "${LOG_DIRS[@]}"; do
    if [[ -d "$log_dir" ]]; then
        while IFS= read -r -d '' logfile; do
            [[ -f "$logfile" && -r "$logfile" && -w "$logfile" ]] && rotate_log "$logfile"
        done < <(find "$log_dir" -type f \( $(printf -- '-name "*.%s" -o ' "${LOG_EXTENSIONS[@]}" | sed 's/ -o $//') \) -print0 2>/dev/null)
    else
        echo "[!] Log directory $log_dir not found or not accessible." | tee -a "$ROTATOR_LOG"
    fi
done

end_time=$(date "+%Y-%m-%d %H:%M:%S")
echo "[Success] Log rotation completed at $end_time" | tee -a "$ROTATOR_LOG"
