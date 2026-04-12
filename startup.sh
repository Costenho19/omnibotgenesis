#!/bin/bash
# OMNIX startup — WSGI wrapper guards all /api/* routes from HTML leaks.
# Uses railway_wsgi:app (wraps Flask with middleware) so /api/* always returns JSON.

set -e

echo "[STARTUP] === OMNIX Quantum Railway startup $(date -u) ==="

echo "[STARTUP] Clearing stale Python bytecode..."
find /app -name "*.pyc" -delete 2>/dev/null || true
find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "[STARTUP] Bytecode cache cleared."

echo "[STARTUP] Starting gunicorn with railway_wsgi:app on port ${PORT:-8080}..."
exec gunicorn \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --worker-class sync \
    --access-logfile - \
    --error-logfile - \
    railway_wsgi:app
