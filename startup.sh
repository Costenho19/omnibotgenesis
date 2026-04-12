#!/bin/bash
# OMNIX startup — clear stale bytecode, start gunicorn directly on $PORT.
# No Caddy needed: Flask/gunicorn handles all routing (static + API).

set -e

echo "[STARTUP] Clearing stale Python bytecode..."
find /app -name "*.pyc" -delete 2>/dev/null || true
find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "[STARTUP] Bytecode cache cleared."

echo "[STARTUP] Starting gunicorn on port ${PORT:-8080}..."
exec gunicorn \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --worker-class sync \
    --access-logfile - \
    --error-logfile - \
    omnix_dashboard.app:app
