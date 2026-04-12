#!/bin/bash
# OMNIX startup script — patches views.py then starts gunicorn
# This guarantees /api/* routes always return JSON even if the
# Docker layer cache has stale Python source files.

set -e

VIEWS="/app/omnix_dashboard/blueprints/views.py"
echo "[STARTUP] Applying views.py runtime patch..."

python3 - << 'PYEOF'
import os

views_path = "/app/omnix_dashboard/blueprints/views.py"

patch_content = """\
import os
from flask import Blueprint, render_template, send_from_directory, redirect, jsonify, request, send_file

views_bp = Blueprint("views", __name__)

REACT_DIST = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "omnix_web", "dist")
)


@views_bp.route("/")
def index():
    accept = request.headers.get("Accept", "")
    ua = request.headers.get("User-Agent", "")
    is_browser = "text/html" in accept or "Mozilla" in ua
    if not is_browser:
        return jsonify({"service": "OMNIX Decision Governance", "status": "operational"})
    react_index = os.path.join(REACT_DIST, "index.html")
    if os.path.isfile(react_index):
        return send_from_directory(REACT_DIST, "index.html")
    return redirect("/terminal")


@views_bp.route("/terminal")
def terminal():
    from omnix_dashboard.utils.database import init_database
    init_database()
    return render_template("terminal.html")


@views_bp.route("/classic")
def classic_dashboard():
    from omnix_dashboard.utils.database import init_database
    init_database()
    return render_template("dashboard.html")


@views_bp.route("/api/<path:api_path>")
def api_not_found(api_path):
    return jsonify({
        "error": "API endpoint not found",
        "path": f"/api/{api_path}",
        "status": 404,
        "guard": "startup-v3",
    }), 404


@views_bp.route("/<path:path>")
def catch_all(path):
    rpath = request.path
    if rpath.startswith("/api/") or path.startswith("api/"):
        return jsonify({
            "error": "API endpoint not found",
            "path": rpath,
            "status": 404,
            "guard": "catchall-v3",
        }), 404
    file_path = os.path.join(REACT_DIST, path)
    if os.path.isfile(file_path):
        return send_from_directory(REACT_DIST, path)
    react_index = os.path.join(REACT_DIST, "index.html")
    if os.path.isfile(react_index):
        return send_from_directory(REACT_DIST, "index.html")
    return render_template("terminal.html")
"""

with open(views_path, "w") as f:
    f.write(patch_content)

print(f"[STARTUP] views.py patched at {views_path}")
PYEOF

echo "[STARTUP] Starting gunicorn on port ${PORT:-8080}..."
exec gunicorn \
    --bind "0.0.0.0:${PORT:-8080}" \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    omnix_dashboard.app:app
