#!/bin/bash

set -e

echo "========================================"
echo " Building QoSCOPE EaaS Images"
echo "========================================"

docker build \
    -t qoscope-measurement-tools:local \
    ../docker/measurement-tools

docker build \
    -t qoscope-server-opencv:local \
    ../docker/server-opencv

docker build \
    -t qoscope-server-stream:local \
    ../docker/server-stream

echo ""
echo "Done."
echo ""
docker images | grep qoscope
