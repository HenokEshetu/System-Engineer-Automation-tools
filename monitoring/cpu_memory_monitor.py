#!/usr/bin/env python3
"""
System Resource Monitor
Continuously tracks system performance metrics and logs them with alerting capabilities.
"""

"""
How to run:
    sudo python3 system_monitor.py \
        --log-path /var/log/my_monitor.log \
        --interval 30 \
        --cpu-threshold 95 \
        --mem-threshold 90 \
        --disk-threshold 95 \
        --temp-threshold 85
"""

import psutil
import time
import logging
from logging.handlers import RotatingFileHandler
import argparse
import signal
import sys
import json
from datetime import datetime, timezone


class SystemMonitor:
    def __init__(self, log_path, interval, thresholds):
        self.log_path = log_path
        self.interval = interval
        self.thresholds = thresholds
        self.running = True
        self.setup_logging()
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def setup_logging(self):
        """Configure logging with rotation and JSON formatting"""
        self.logger = logging.getLogger("SystemMonitor")
        self.logger.setLevel(logging.INFO)

        # Create log formatter with JSON format
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}',
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
        formatter.converter = time.gmtime  # Use UTC time

        # Create rotating file handler
        handler = RotatingFileHandler(
            filename=self.log_path, maxBytes=10 * 1024 * 1024, backupCount=5  # 10 MB
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def signal_handler(self, signum, frame):
        """Handle termination signals gracefully"""
        self.logger.info("Shutting down monitor")
        self.running = False

    def collect_metrics(self):
        """Gather system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.5)
            cpu_per_core = psutil.cpu_percent(interval=0.5, percpu=True)

            # Memory metrics
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Disk metrics
            disk_usage = psutil.disk_usage("/")
            disk_io = psutil.disk_io_counters()

            # Network metrics
            net_io = psutil.net_io_counters()

            # Temperatures (if available)
            try:
                temps = {
                    sensor.label or f"sensor_{i}": sensor.current
                    for i, sensor in enumerate(
                        psutil.sensors_temperatures().get("coretemp", [])
                    )
                }
            except Exception:
                temps = {}

            # Battery status (if available)
            try:
                battery = psutil.sensors_battery()
                battery_status = (
                    {"percent": battery.percent, "power_plugged": battery.power_plugged}
                    if battery
                    else {}
                )
            except Exception:
                battery_status = {}

            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cpu": {
                    "total": cpu_percent,
                    "per_core": cpu_per_core,
                    "load_avg": [
                        x / psutil.cpu_count() * 100 for x in psutil.getloadavg()
                    ],
                },
                "memory": {
                    "total": mem.total,
                    "available": mem.available,
                    "used": mem.used,
                    "percent": mem.percent,
                    "swap_used": swap.used,
                    "swap_percent": swap.percent,
                },
                "disk": {
                    "total": disk_usage.total,
                    "used": disk_usage.used,
                    "free": disk_usage.free,
                    "percent": disk_usage.percent,
                    "read_bytes": disk_io.read_bytes,
                    "write_bytes": disk_io.write_bytes,
                },
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                },
                "temperatures": temps,
                "battery": battery_status,
            }
        except Exception as e:
            self.logger.error(f"Metrics collection failed: {str(e)}")
            return None

    def check_thresholds(self, metrics):
        """Check metrics against configured thresholds"""
        alerts = []

        if not metrics:
            return alerts

        # CPU threshold check
        if metrics["cpu"]["total"] > self.thresholds["cpu"]:
            alerts.append(f"High CPU usage: {metrics['cpu']['total']}%")

        # Memory threshold check
        if metrics["memory"]["percent"] > self.thresholds["memory"]:
            alerts.append(f"High memory usage: {metrics['memory']['percent']}%")

        # Disk threshold check
        if metrics["disk"]["percent"] > self.thresholds["disk"]:
            alerts.append(f"High disk usage: {metrics['disk']['percent']}%")

        # Temperature threshold check
        for name, temp in metrics["temperatures"].items():
            if temp > self.thresholds["temperature"]:
                alerts.append(f"High temperature ({name}): {temp}°C")

        return alerts

    def run(self):
        """Main monitoring loop"""
        self.logger.info("Starting system monitor")

        while self.running:
            metrics = self.collect_metrics()
            if metrics:
                alerts = self.check_thresholds(metrics)

                # Prepare log entry
                log_entry = {"metrics": metrics, "alerts": alerts}

                # Log with appropriate severity
                if alerts:
                    self.logger.warning(json.dumps(log_entry))
                else:
                    self.logger.info(json.dumps(log_entry))

            # Sleep with interval slicing for faster shutdown
            for _ in range(self.interval * 10):
                if not self.running:
                    break
                time.sleep(0.1)


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="System Resource Monitoring Tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-l",
        "--log-path",
        default="/var/log/system_monitor.log",
        help="Path to log file",
    )
    parser.add_argument(
        "-i", "--interval", type=int, default=60, help="Monitoring interval in seconds"
    )
    parser.add_argument(
        "--cpu-threshold",
        type=float,
        default=90.0,
        help="CPU usage alert threshold (percentage)",
    )
    parser.add_argument(
        "--mem-threshold",
        type=float,
        default=85.0,
        help="Memory usage alert threshold (percentage)",
    )
    parser.add_argument(
        "--disk-threshold",
        type=float,
        default=90.0,
        help="Disk usage alert threshold (percentage)",
    )
    parser.add_argument(
        "--temp-threshold",
        type=float,
        default=80.0,
        help="Temperature alert threshold (Celsius)",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    thresholds = {
        "cpu": args.cpu_threshold,
        "memory": args.mem_threshold,
        "disk": args.disk_threshold,
        "temperature": args.temp_threshold,
    }

    monitor = SystemMonitor(
        log_path=args.log_path, interval=args.interval, thresholds=thresholds
    )
    monitor.run()


if __name__ == "__main__":
    main()
