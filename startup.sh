#!/bin/bash
# OMNIX startup script
# Clears stale Python bytecode cache, then starts gunicorn.
# This guarantees the CURRENT source files are always used,
# preventing Docker layer cache from serving old .pyc files.

set -e

echo "[STARTUP] Clearing stale __pycache__ and .pyc files..."
find /app -name "*.pyc" -delete 2>/dev/null || true
find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "[STARTUP] Bytecode cache cleared."

echo "[STARTUP] Starting gunicorn on port ${PORT:-8080}..."
exec gunicorn \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    omnix_dashboard.app:app
