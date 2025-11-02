#!/usr/bin/env python3
import sys
import subprocess
import re
import time
import csv
import os
import datetime
import yaml
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from filelock import SoftFileLock  # <--- NEU

# Standardwerte
HOST = "www.google.com/robots.txt"
INTERVAL = 20
LOGFILE = "./data/speed_stats.csv"
LOCKFILE = "/tmp/nettest.lock"

# Hilfsfunktion: Intervalle wie "3h", "60min", "3600s", "1.5h" parsen
def parse_interval(value, default_unit="s"):
    """Wandelt Angaben wie 10, "30s", "5m", "2h", "1.5h" in Sekunden (float) um.

    Erlaubte Einheiten (Groß-/Kleinschreibung egal):
    - Sekunden: s, sec, secs, second, seconds
    - Minuten: m, min, mins, minute, minutes
    - Stunden: h, hr, hrs, hour, hours
    - Tage: d, day, days
    - Wochen: w, week, weeks

    Fällt keine Einheit an, wird default_unit (Standard: Sekunden) verwendet.
    """
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        raise ValueError(f"Unsupported interval type: {type(value)}")

    text = value.strip().lower()
    # Zahl und optionale Einheit extrahieren
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([a-z]+)?\s*", text)
    if not m:
        raise ValueError(f"Invalid interval format: {value}")
    amount = float(m.group(1))
    unit = (m.group(2) or default_unit).lower()

    unit_map = {
        # Sekunden
        "s": 1,
        "sec": 1,
        "secs": 1,
        "second": 1,
        "seconds": 1,
        # Minuten
        "m": 60,
        "min": 60,
        "mins": 60,
        "minute": 60,
        "minutes": 60,
        # Stunden
        "h": 3600,
        "hr": 3600,
        "hrs": 3600,
        "hour": 3600,
        "hours": 3600,
        # Tage
        "d": 86400,
        "day": 86400,
        "days": 86400,
        # Wochen
        "w": 604800,
        "week": 604800,
        "weeks": 604800,
    }

    if unit not in unit_map:
        raise ValueError(f"Unknown interval unit: {unit}")

    return amount * unit_map[unit]

def run_speedtest(host):
    try:
        result = subprocess.run(
            ["curl", "-L", host, "-o", "/dev/null", \
                     "-w", "speed=%{speed_download}\\nsize=%{size_download}\\ntime=%{time_total}\\n",\
                     "-s"],

            capture_output=True,
            text=True,
            timeout=1000
        )
        if result.returncode != 0:
            return None
        for line in result.stdout.splitlines():
            m = re.search(r"speed=(\d+)", line)
            if m:
                return float(m.group(1))
        return None
    except Exception:
        return None

# Globale Variablen für Prometheus
last_speed = None
last_timestamp = None

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-type", "text/plain; version=0.0.4")
            self.end_headers()
            lines = [
                "# HELP speedtest_download_bps Letzte gemessene Downloadgeschwindigkeit in Byte/s",
                "# TYPE speedtest_download_bps gauge",
                f"speedtest_download_bps {last_speed if last_speed is not None else 'NaN'}",
                "# HELP speedtest_last_timestamp Unix-Timestamp der letzten Messung",
                "# TYPE speedtest_last_timestamp gauge",
                f"speedtest_last_timestamp {last_timestamp if last_timestamp is not None else 'NaN'}",
            ]
            self.wfile.write("\n".join(lines).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def start_metrics_server(port=8001):
    server = HTTPServer(("", port), MetricsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

def acquire_file_lock():
    lock = SoftFileLock(LOCKFILE, thread_local=False)  
    lock.acquire()
    return lock

def release_file_lock(lock):
    lock.release()

if __name__ == "__main__":
    #time.sleep(10)  # Warte 10 Sekunden nach dem Start
    if len(sys.argv) > 1 and (sys.argv[1] == "--help" or sys.argv[1] == "-h"):
        print("Usage: speed_logger.py [host] [interval] [output_file] [lockfile]")
        sys.exit(1)

    elif os.path.exists("./config.yaml") is True:
        with open("./config.yaml") as f:
            config = yaml.safe_load(f)["speed_logger"]
            HOST = config.get("host", HOST)
            try:
                INTERVAL = parse_interval(config.get("interval", config.get("interval_seconds", INTERVAL)))
            except Exception:
                # Fallback auf bisherigen Wert
                INTERVAL = float(INTERVAL)
            LOGFILE = config.get("logfile", LOGFILE)
            LOCKFILE = config.get("lockfile", LOCKFILE)
    
    else:
        HOST = sys.argv[1] if len(sys.argv) > 1 else HOST
        if len(sys.argv) > 2:
            try:
                INTERVAL = parse_interval(sys.argv[2])
            except Exception:
                INTERVAL = float(INTERVAL)
        LOGFILE = sys.argv[3] if len(sys.argv) > 3 else LOGFILE
        LOCKFILE = sys.argv[4] if len(sys.argv) > 4 else LOCKFILE

    os.makedirs(os.path.dirname(os.path.abspath(LOGFILE)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(LOCKFILE)), exist_ok=True)

    file_exists = os.path.isfile(LOGFILE)

    # Starte Prometheus-Metrics-Server im Hintergrund
    start_metrics_server(port=8001)
    
    with open(LOGFILE, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["timestamp_unix", "timestamp_iso", "speed_bps", "host"])

        while True:
            start_time = time.time()
             
            lock = acquire_file_lock()
            try:
                speed = run_speedtest(HOST)
                ts_unix = int(time.time())
                ts_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

                writer.writerow([ts_unix, ts_iso, speed, HOST])
                csvfile.flush()

                # Werte für Prometheus bereitstellen
                last_speed = speed
                last_timestamp = ts_unix
            finally:
                release_file_lock(lock)

            elapsed = time.time() - start_time
            sleep_time = max(0, INTERVAL - elapsed)
            time.sleep(sleep_time)
