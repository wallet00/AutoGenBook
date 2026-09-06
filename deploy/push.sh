#!/usr/bin/env bash
# AutoGenBook — build + push na Docker Hub (Linux/macOS/WSL)
set -euo pipefail
cd "$(dirname "$0")/.."
echo "=== Build image wallet007/autogenbook:latest ==="
docker build -t wallet007/autogenbook:latest .
echo "=== Login na Docker Hub ==="
docker login
echo "=== Push image ==="
docker push wallet007/autogenbook:latest
echo "=== Hotovo: wallet007/autogenbook:latest ==="
