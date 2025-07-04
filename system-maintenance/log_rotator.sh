#!/bin/bash

LOGFILE="/var/log/syslog"
MAXSIZE=5242880 # 5MB

if [ -f "$LOGFILE" ] && [ $(stat -c%s "$LOGFILE") -ge $MAXSIZE ]; then
    mv "$LOGFILE" "$LOGFILE.bak"
    touch "$LOGFILE"
    echo "Log rotated at $(date)"
fi
