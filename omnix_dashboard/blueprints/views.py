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
    """Root: redirect browsers to terminal; return JSON for automated health checks."""
    ua = request.headers.get('User-Agent', '')
    accept = request.headers.get('Accept', '')
    # If the request accepts HTML (real browser), redirect to dashboard.
    # If it's a health check / scanner with no HTML preference, return JSON.
    is_browser = 'text/html' in accept or 'Mozilla' in ua
    if is_browser:
        return redirect('/terminal')
    return jsonify({
        'service': 'OMNIX Internal API',
        'port': 5000,
        'note': 'Internal governance API. Public web at port 3000.'
    })


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
