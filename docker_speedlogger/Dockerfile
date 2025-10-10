FROM debian:stable-slim
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    python3-pip \
    && pip3 install pyyaml \
    && rm -rf /var/lib/apt/lists/*

COPY config.yaml /usr/local/bin/config.yaml
COPY speed_logger.py /usr/local/bin/speed_logger.py
RUN chmod +x /usr/local/bin/speed_logger.py

WORKDIR /usr/local/bin

ENTRYPOINT ["python3", "/usr/local/bin/speed_logger.py"]