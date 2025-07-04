import psutil
import time
from datetime import datetime

log_file = "/var/log/system_resource.log"

while True:
    with open(log_file, "a") as f:
        f.write(f"\n--- {datetime.now()} ---\n")
        f.write(f"CPU Usage: {psutil.cpu_percent()}%\n")
        f.write(f"Memory Usage: {psutil.virtual_memory().percent}%\n")
        f.write(f"Disk Usage: {psutil.disk_usage('/').percent}%\n")
    time.sleep(60)
