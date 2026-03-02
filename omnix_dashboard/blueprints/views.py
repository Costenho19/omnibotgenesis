"""
OMNIX Dashboard - Views Blueprint
HTML page routes (/, /terminal, /classic)
Public React SPA routes served via catch-all.
"""

import os
from flask import Blueprint, render_template, send_from_directory
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


@views_bp.route('/', defaults={'path': ''})
@views_bp.route('/<path:path>')
def catch_all(path):
    """
    Serve React SPA for all public routes.
    - If path matches a static file in omnix_web/dist, serve it directly.
    - Otherwise serve index.html and let React Router handle the route.
    Internal Flask routes (/terminal, /classic, /api/*) are matched before this.
    """
    if path:
        file_path = os.path.join(REACT_DIST, path)
        if os.path.isfile(file_path):
            return send_from_directory(REACT_DIST, path)

    index_path = os.path.join(REACT_DIST, 'index.html')
    if os.path.isfile(index_path):
        return send_from_directory(REACT_DIST, 'index.html')

    return render_template('terminal.html')
