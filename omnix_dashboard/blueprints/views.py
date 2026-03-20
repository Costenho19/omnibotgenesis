"""
OMNIX Dashboard - Views Blueprint
HTML page routes (/, /terminal, /classic)
Public React SPA routes served via catch-all.
"""

import os
from flask import Blueprint, render_template, send_from_directory, redirect, jsonify, request
from omnix_dashboard.utils.database import init_database

views_bp = Blueprint('views', __name__)

REACT_DIST = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'omnix_web', 'dist')
)


@views_bp.route('/terminal')
def terminal():
    """Bloomberg-style trading terminal (internal dashboard)"""
    init_database()
    return render_template('terminal.html')


@views_bp.route('/classic')
def classic_dashboard():
    """Classic dashboard page (internal)"""
    init_database()
    return render_template('dashboard.html')


@views_bp.route('/')
def index():
    """Root: return API info for automated scanners; redirect humans to dashboard."""
    ua = request.headers.get('User-Agent', '')
    remote = request.remote_addr or ''
    # Replit's internal proxy and health checkers hit / — return JSON so the
    # preview pane doesn't auto-switch to this port (port 5000 is internal API,
    # not the public web interface at port 3000).
    is_automated = (
        remote.startswith('172.31.')
        or 'python-requests' in ua.lower()
        or 'go-http' in ua.lower()
        or ua == ''
    )
    if is_automated:
        return jsonify({
            'service': 'OMNIX Internal API',
            'port': 5000,
            'note': 'Internal governance API. Public web at port 3000.'
        })
    return redirect('/terminal')


@views_bp.route('/<path:path>')
def catch_all(path):
    """
    Serve static assets from React dist (CSS, JS, images).
    Any unknown path falls back to terminal dashboard.
    Internal Flask routes (/terminal, /classic, /api/*) are matched before this.
    """
    file_path = os.path.join(REACT_DIST, path)
    if os.path.isfile(file_path):
        return send_from_directory(REACT_DIST, path)

    return render_template('terminal.html')
