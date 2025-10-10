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

HOST = "www.google.com"
INTERVAL = 5
STATS_INTERVAL = 600
LOGFILE = "./data/speed_stats.csv"
STATSFILE = "./data/ping_stats.csv"

# Globale Variablen für Prometheus
global last_loss, last_min, last_max, last_avg, last_timestamp
last_loss = None
last_min = None
last_max = None
last_avg = None
last_timestamp = None

def run_ping(host):
    try:
        result = subprocess.run(
            ["ping", "-c", "1", host],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return None
        for line in result.stdout.splitlines():
            m = re.search(r"time=(\d+\.\d+)", line)
            if m:
                return float(m.group(1))
        return None
    except Exception:
        return None

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-type", "text/plain; version=0.0.4")
            self.end_headers()
            lines = [
                "# HELP ping_loss_percent Paketverlust in Prozent (letzte Minute)",
                "# TYPE ping_loss_percent gauge",
                f"ping_loss_percent {last_loss if last_loss is not None else 'NaN'}",
                "# HELP ping_min_latency_ms Minimale Latenz (letzte Minute)",
                "# TYPE ping_min_latency_ms gauge",
                f"ping_min_latency_ms {last_min if last_min is not None else 'NaN'}",
                "# HELP ping_max_latency_ms Maximale Latenz (letzte Minute)",
                "# TYPE ping_max_latency_ms gauge",
                f"ping_max_latency_ms {last_max if last_max is not None else 'NaN'}",
                "# HELP ping_avg_latency_ms Durchschnittliche Latenz (letzte Minute)",
                "# TYPE ping_avg_latency_ms gauge",
                f"ping_avg_latency_ms {last_avg if last_avg is not None else 'NaN'}",
                "# HELP ping_last_timestamp Unix-Timestamp der letzten Messung",
                "# TYPE ping_last_timestamp gauge",
                f"ping_last_timestamp {last_timestamp if last_timestamp is not None else 'NaN'}",
            ]
            self.wfile.write("\n".join(lines).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def start_metrics_server(port=8002):
    server = HTTPServer(("", port), MetricsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

if __name__ == "__main__":
                
    if len(sys.argv) > 1 and (sys.argv[1] == "--help" or sys.argv[1] == "-h"):
        print("Usage: ping_logger.py [host] [interval_seconds] [stats_interval_seconds] [logfile] [statsfile]")
        sys.exit(1)

    elif os.path.exists("./config.yaml") is True:
        with open("./config.yaml") as f:
            config = yaml.safe_load(f)["ping_logger"]
            HOST = config.get("host", HOST)
            INTERVAL = config.get("interval_seconds", INTERVAL)
            STATS_INTERVAL = config.get("stats_interval_seconds", STATS_INTERVAL)
            LOGFILE = config.get("logfile", LOGFILE)
            STATSFILE = config.get("statsfile", STATSFILE)

    else:
        HOST = sys.argv[1] if len(sys.argv) > 1 else HOST
        INTERVAL = int(sys.argv[2]) if len(sys.argv) > 2 else INTERVAL
        STATS_INTERVAL = int(sys.argv[3]) if len(sys.argv) > 3 else STATS_INTERVAL
        LOGFILE = sys.argv[4] if len(sys.argv) > 4 else LOGFILE
        STATSFILE = sys.argv[5] if len(sys.argv) > 5 else STATSFILE

    os.makedirs(os.path.dirname(os.path.abspath(LOGFILE)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(STATSFILE)), exist_ok=True)

    logfile_exists = os.path.isfile(LOGFILE)
    statsfile_exists = os.path.isfile(STATSFILE)

    with open(LOGFILE, "a", newline="") as logfile:
        with open(STATSFILE, "a", newline="") as statsfile:
            logwriter = csv.writer(logfile)
            if not logfile_exists:
                logwriter.writerow(["timestamp_unix", "timestamp_iso", "host", "latency_ms"])

            statswriter = csv.writer(statsfile)
            if not statsfile_exists:
                statswriter.writerow(["timestamp_unix", "timestamp_iso", "host", "stat_min_ms", "stat_max_ms", "stat_avg_ms", "stat_loss_percent"])
            
            start_metrics_server()

            while True:
                start_stats = time.time()
                losses = 0
                latencies = []
                ts_unix = int(time.time())
                ts_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

                while time.time() - start_stats < STATS_INTERVAL:
                    start_ping = time.time()

                    latency = run_ping(HOST)
                    ts_unix = int(time.time())
                    ts_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    logwriter.writerow([ts_unix, ts_iso, HOST, latency if latency else -1])
                    if latency is not None:
                        latencies.append(latency)
                    else:
                        losses += 1
                    logfile.flush()

                    elapsed = time.time() - start_ping
                    sleep_time = max(0, INTERVAL - elapsed)
                    time.sleep(sleep_time)

                # Statistik berechnen und in die CSV schreiben
                if latencies:
                    min_latency = min(latencies)
                    max_latency = max(latencies)
                    avg_latency = round(sum(latencies) / len(latencies), 1)
                else:
                    min_latency = max_latency = avg_latency = -1
                loss = round((losses / (len(latencies) + losses)) * 100 if (len(latencies) + losses) > 0 else 100, 1)

                statswriter.writerow([ts_unix, ts_iso, HOST, min_latency, max_latency, avg_latency, loss])
                statsfile.flush()

                # Update der letzten Werte für Prometheus
                last_loss = loss
                last_min = min_latency
                last_max = max_latency
                last_avg = avg_latency
                last_timestamp = ts_unix
