from fastapi import FastAPI
import psutil
import subprocess
from pathlib import Path

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parents[1]

SERVICES = ["nginx", "ssh", "mysql"]

@app.get("/api/metrics")
def metrics():
    return {
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent
    }

@app.get("/api/incidents")
def incidents():
    log = BASE_DIR / "logs/incidents.log"
    if not log.exists():
        return []
    return log.read_text().splitlines()[-20:]

@app.get("/api/services")
def services():
    data = {}
    for s in SERVICES:
        r = subprocess.run(
            ["systemctl", "is-active", s],
            stdout=subprocess.PIPE
        )
        data[s] = r.stdout.decode().strip()
    return data

@app.post("/api/service/restart")
def restart(service: dict):
    subprocess.run(["systemctl", "restart", service["name"]])
    return {"status": "restarted", "service": service["name"]}
