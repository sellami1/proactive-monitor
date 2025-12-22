import psutil
import subprocess
import time
import yaml
import logging
import csv
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

with open(BASE_DIR / "monitoring/config.yaml") as f:
    config = yaml.safe_load(f)

SERVICES = config["services"]
THRESHOLDS = config["thresholds"]
INTERVAL = config["interval"]

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "incidents.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def check_service(service):
    r = subprocess.run(
        ["systemctl", "is-active", service],
        stdout=subprocess.PIPE
    )
    return r.stdout.decode().strip()

def restart_service(service):
    r = subprocess.run(
        ["systemctl", "restart", service],
        stderr=subprocess.PIPE
    )
    if r.returncode == 0:
        logging.warning(f"Service {service} restarted")
    else:
        logging.error(f"Restart failed for {service}: {r.stderr.decode()}")

def cleanup_disk():
    subprocess.run(["rm", "-rf", "/tmp/*"])
    logging.warning("Disk cleanup executed")

def collect_metrics():
    return {
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent
    }

def save_metrics(m):
    file = LOG_DIR / "metrics.csv"
    new = not file.exists()

    with open(file, "a", newline="") as f:
        writer = csv.writer(f)
        if new:
            writer.writerow(["timestamp", "cpu", "ram", "disk"])
        writer.writerow([
            datetime.now().isoformat(),
            m["cpu"], m["ram"], m["disk"]
        ])

def main():
    while True:
        metrics = collect_metrics()
        save_metrics(metrics)

        if metrics["cpu"] > THRESHOLDS["cpu"]:
            logging.error("CPU overload")

        if metrics["ram"] > THRESHOLDS["ram"]:
            logging.error("RAM overload")

        if metrics["disk"] > THRESHOLDS["disk"]:
            logging.error("Disk usage critical")
            cleanup_disk()

        for svc in SERVICES:
            if check_service(svc) != "active":
                logging.error(f"Service {svc} is DOWN")
                restart_service(svc)

        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
