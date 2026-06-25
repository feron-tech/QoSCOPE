#!/bin/bash

docker compose -f ../docker/docker-compose.yml down

docker rm -f \
    qoscope-measurement-tools \
    qoscope-server-opencv \
    qoscope-server-stream \
    qoscope-nanomq \
    2>/dev/null || true
