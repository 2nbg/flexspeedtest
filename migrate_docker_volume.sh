#!/bin/sh
for v in $(sudo docker volume ls -q); do
  echo "Volume: $v"
  sudo docker ps -a --filter volume=$v --format "  -> {{.Names}}"
  echo ""
done

sudo docker volume inspect bwt3_prometheus-data
sudo docker volume inspect bwt3_grafana-data

sudo docker volume create fst_grafana-data
sudo docker volume create fst_prometheus-data

sudo docker run --rm \
  -v bwt3_prometheus-data:/from \
  -v fst_prometheus-data:/to \
  alpine sh -c "cd /from && cp -a . /to"

sudo docker run --rm \
  -v bwt3_grafana-data:/from \
  -v fst_grafana-data:/to \
  alpine sh -c "cd /from && cp -a . /to"

sudo docker run --rm -v bwt3_prometheus-data:/data alpine du -sh /data
sudo docker run --rm -v bwt3_grafana-data:/data alpine du -sh /data

sudo docker run --rm -v fst_prometheus-data:/data alpine du -sh /data
sudo docker run --rm -v fst_grafana-data:/data alpine du -sh /data
