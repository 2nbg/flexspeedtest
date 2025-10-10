# Bandwidthtest – Netzwerk- und Speed-Logger mit Docker, Prometheus & Grafana

Dieses Projekt misst regelmäßig die Netzwerk-Latenz (Ping) und die Download-Geschwindigkeit (Speedtest) zu konfigurierbaren Hosts. Die Ergebnisse werden als CSV-Dateien gespeichert, als Prometheus-Metriken bereitgestellt und können in Grafana visualisiert werden.

## Features

- **Ping-Logger:** Misst Latenz und Paketverlust, schreibt CSV und Prometheus-Metriken.
- **Speed-Logger:** Misst Download-Geschwindigkeit, schreibt CSV und Prometheus-Metriken.
- **Prometheus:** Sammelt die Metriken automatisch.
- **Grafana:** Visualisiert die Daten aus Prometheus.
- **Flexible Konfiguration:** Über `config.yaml` (Intervalle als `3h`, `60min`, `3600s` etc.)

## Schnellstart

### Voraussetzungen

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Starten

1. **Konfiguration anpassen:**  
   Passe die Datei [`config.yaml`](./config.yaml) nach deinen Wünschen an (Hosts, Intervalle, Dateipfade).

2. **Container bauen und starten:**  
   ```bash
   docker-compose up --build
   ```

3. **Grafana öffnen:**  
   [http://localhost:3010](http://localhost:3010)  
   (Standardmäßig ohne Login, siehe `docker-compose.yml`)

4. **Prometheus öffnen:**  
   [http://localhost:9090](http://localhost:9090)

### Daten & Visualisierung

- **CSV-Dateien:**  
  Werden im `data/`-Verzeichnis gespeichert (z.B. `data/speed_stats.csv`).
- **Prometheus-Metriken:**  
  Werden von den Logger-Containern auf `/metrics` bereitgestellt.
- **Grafana Dashboards:**  
  Werden automatisch provisioniert (siehe `grafana/provisioning`).

### Beispiel für `config.yaml`

```yaml
ping_logger:
  host: google.com
  interval: 5s
  stats_interval: 10min
  logfile: /data/ping_results.csv
  statsfile: /data/ping_stats.csv

speed_logger:
  host: https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-13.1.0-amd64-netinst.iso
  interval: 3h
  logfile: /data/speed_stats.csv
```

**Erlaubte Zeitangaben:**  
- Sekunden: `30s`, `60sec`
- Minuten: `10min`, `5m`
- Stunden: `3h`, `1hr`

### Prometheus Scrape-Konfiguration (`prometheus.yml`)

```yaml
scrape_configs:
  - job_name: 'speed_logger'
    static_configs:
      - targets: ['speed-logger:8001']
  - job_name: 'ping_logger'
    static_configs:
      - targets: ['ping-logger:8002']
```

### Hinweise

- Änderungen an provisionierten Dashboards in Grafana werden **nicht** in den JSON-Dateien gespeichert. Exportiere das Dashboard nach Änderungen und ersetze die Datei im Provisioning-Ordner.
- Prometheus- und Grafana-Daten werden in Docker-Volumes gespeichert und sind nach Neustart erhalten.

---

**Lizenz:** MIT  
**Autor:** 2nbg