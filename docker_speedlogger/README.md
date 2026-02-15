# docker_speedlogger

Ein leichter Netzwerk-Speed-Logger, der zyklisch eine Datei per `curl` herunterlädt, die Downloadgeschwindigkeit (Byte/s) ausgibt, in eine CSV-Datei schreibt und Prometheus-kompatible Metriken unter `/metrics` bereitstellt.

## Features
- Zyklische Messung via `curl -w %{speed_download}`
- Konfigurierbare Ziel-URL, Messintervall, CSV-Pfad, Lock-Datei
- CSV-Output mit Zeitstempel (Unix & ISO) und Host
- Prometheus-Metrics auf Port 8001 (`speedtest_download_bps`, `speedtest_last_timestamp`)
- Dateilock (via `filelock`) für sichere parallele Nutzung

## Voraussetzungen
- Docker oder Python 3.11+
- Bei Docker: Image basiert auf `python:3.11-slim` und installiert `curl`, `pyyaml`, `filelock`

## Konfiguration
Die Standard-Konfiguration liegt in `config.yaml` und wird beim Containerstart nach `/usr/local/bin/config.yaml` kopiert.

```yaml
speed_logger:
  host: www.google.com/robots.txt   # Zu ladende Ressource
  interval: 10s                     # Messintervall (z. B. 30s, 5m, 1.5h)
  logfile: ./data/speed_stats.csv   # CSV-Ziel
  lockfile: ./lock/nettest.lock     # Lock-Datei
```

Unterstützte Einheiten für `interval`: `s|sec|seconds`, `m|min|minutes`, `h|hour|hours`, `d|day|days`, `w|week|weeks`. Ohne Einheit werden Sekunden angenommen.

Hinweis zu Pfaden im Container:
- Empfohlen ist die Nutzung von absoluten Pfaden innerhalb des Containers, z. B. `logfile: /data/speed_stats.csv` und `lockfile: /lock/nettest.lock`, damit gemountete Volumes genutzt werden.

## Nutzung
### Mit Docker Compose (empfohlen)
In der übergeordneten Compose-Datei existiert bereits ein Service-Eintrag (siehe `flexspeedtest/docker-compose.yml`). Typische Volumes:
- `./data:/data`
- `./config.yaml:/usr/local/bin/config.yaml`
- `./lock:/lock`

Starten/Neustarten:
```bash
cd $HOME/dev/flexspeedtest
# Stack starten/aktualisieren
docker compose up -d speed-logger
# Logs ansehen
docker compose logs -f speed-logger
```

### Manuell mit Docker (ohne Compose)
Image bauen und Container starten:
```bash
cd $HOME/dev/flexspeedtest/docker_speedlogger
# Build
docker build -t speed_logger .
# Run (mit Volumes für Persistenz)
docker run --rm \
  -p 8001:8001 \
  -v $(pwd)/../data:/data \
  -v $(pwd)/config.yaml:/usr/local/bin/config.yaml \
  -v $(pwd)/../lock:/lock \
  speed_logger
```

### Direkt lokal (ohne Docker)
```bash
cd $HOME/dev/flexspeedtest/docker_speedlogger
python3 speed_logger.py
# oder mit Parametern: host interval logfile lockfile
python3 speed_logger.py https://www.google.com/robots.txt 30s ./data/speed_stats.csv ./lock/nettest.lock
```

## Ausgaben
### CSV
Spalten: `timestamp_unix, timestamp_iso, speed_bps, host`
Datei: standardmäßig `./data/speed_stats.csv` (empfohlen: `/data/speed_stats.csv` bei Docker)

### Prometheus
- Endpoint: `http://<container-host>:8001/metrics`
- Metriken:
  - `speedtest_download_bps` (Gauge)
  - `speedtest_last_timestamp` (Gauge)

Beispiel-Scrape-Konfiguration in Prometheus:
```yaml
scrape_configs:
  - job_name: 'speed_logger'
    static_configs:
      - targets: ['fst_speed_logger:8001']
```

## Tests
Unit-Tests befinden sich in `test_speed_logger.py`:
```bash
cd $HOME/dev/flexspeedtest/docker_speedlogger
python3 -m unittest -v test_speed_logger.py
```

## Troubleshooting
- Keine CSV-Datei: Pfade in `config.yaml` prüfen und sicherstellen, dass das Zielverzeichnis existiert/montiert ist.
- Metrics leer: Prüfen, ob der Prozess genug Zeit hatte eine Messung durchzuführen (`interval`) und der Port 8001 erreichbar ist.
- Download-Geschwindigkeit `None`: Ziel-URL oder Netzverbindung prüfen; ggf. Timeout (`curl`) anpassen.

## Hinweise
- Die Messung verwendet tatsächlichen Download; wählen Sie eine kleine, stabile Ressource (z. B. `robots.txt`).
- Für Persistenz in Docker immer Volumes setzen und innerhalb des Containers `/data` und `/lock` verwenden.
