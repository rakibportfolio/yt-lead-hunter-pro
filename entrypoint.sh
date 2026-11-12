#!/bin/bash
set -e

echo "=========================================================="
echo "🚀 [ZENTIC MEDIA] Initializing VPS Production Container"
echo "=========================================================="

# Export python path
export PYTHONPATH="/app/backend:/app"
export PYTHONUNBUFFERED=1

# Start the 24/7 Autonomous Lead Hunter Daemon in background supervisor loop
(
  while true; do
    echo "[24/7 Hunter Daemon] Starting worker daemon..."
    python /app/backend/worker_daemon.py || true
    echo "[24/7 Hunter Daemon] Worker exited or restarted. Sleeping 10s before auto-revival..."
    sleep 10
  done
) &

echo "✅ 24/7 Background Lead Hunter Worker successfully launched in background!"
echo "🌐 Starting FastAPI Web Server on port 8000..."

# Start FastAPI server in foreground (keeps Docker container running)
exec python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

