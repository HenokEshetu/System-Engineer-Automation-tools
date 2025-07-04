#!/bin/bash

LOGFILE="/var/log/sys-maintenance.log"
echo "=== System Maintenance: $(date) ===" >> $LOGFILE

echo "Updating packages..." | tee -a $LOGFILE
sudo apt update && sudo apt upgrade -y | tee -a $LOGFILE

echo "Cleaning up unused packages..." | tee -a $LOGFILE
sudo apt autoremove -y && sudo apt autoclean | tee -a $LOGFILE

echo "System maintenance completed!" | tee -a $LOGFILE
