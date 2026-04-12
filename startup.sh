#!/bin/bash
# OMNIX startup script — creates correct Caddyfile at runtime, then starts Caddy + gunicorn.
# This guarantees routing /api/* to gunicorn:8080, regardless of what Nixpacks
# puts in /app/Caddyfile during the build phase.

set -e

echo "[STARTUP] Clearing stale Python bytecode..."
find /app -name "*.pyc" -delete 2>/dev/null || true
find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "[STARTUP] Bytecode cache cleared."

echo "[STARTUP] Writing custom Caddyfile to /tmp/omnix.caddyfile..."
cat > /tmp/omnix.caddyfile << 'CADDYEOF'
{
    admin off
    persist_config off
    auto_https off
}

:{$PORT} {
    handle /api/* {
        reverse_proxy localhost:8080
    }

    handle {
        root * /app/omnix_web/dist
        try_files {path} /index.html
        file_server
    }
}
CADDYEOF
echo "[STARTUP] Caddyfile written."

echo "[STARTUP] Starting Caddy on port ${PORT}..."
caddy run --config /tmp/omnix.caddyfile &
CADDY_PID=$!

echo "[STARTUP] Waiting for Caddy to initialise..."
sleep 3

echo "[STARTUP] Starting gunicorn on internal port 8080..."
exec gunicorn \
    --bind "0.0.0.0:8080" \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    omnix_dashboard.app:app
