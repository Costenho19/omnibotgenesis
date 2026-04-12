"""
OMNIX Dashboard - Views Blueprint
HTML page routes (/, /terminal, /classic)
Public React SPA routes served via catch-all.
"""

import io
import os
import zipfile
from flask import Blueprint, render_template, send_from_directory, redirect, jsonify, request, send_file
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


ZENODO_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'zenodo')
)


@views_bp.route('/download/zenodo-package')
def download_zenodo_package():
    """Serve all zenodo files as a single ZIP for easy download."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(ZENODO_DIR):
            fpath = os.path.join(ZENODO_DIR, fname)
            if os.path.isfile(fpath):
                zf.write(fpath, fname)
    buf.seek(0)
    return send_file(
        buf,
        mimetype='application/zip',
        as_attachment=True,
        download_name='omnix_zenodo_package.zip'
    )


@views_bp.route('/')
def index():
    """Root route.

    - Production (Railway): serve React SPA so omnixquantum.net shows the
      commercial landing page.
    - Development (Replit): redirect to /terminal so the Flask dashboard is
      immediately visible when accessing port 5000 — avoids confusion with
      the Vite dev server on port 3000 which already serves the React SPA.
    - Automated health checks (non-browser): return JSON status.
    """
    accept = request.headers.get('Accept', '')
    ua = request.headers.get('User-Agent', '')
    is_browser = 'text/html' in accept or 'Mozilla' in ua

    if not is_browser:
        return jsonify({'service': 'OMNIX Decision Governance', 'status': 'operational'})

    env = os.environ.get('ENVIRONMENT', 'development').lower()
    if env != 'production':
        return redirect('/terminal')

    react_index = os.path.join(REACT_DIST, 'index.html')
    if os.path.isfile(react_index):
        return send_from_directory(REACT_DIST, 'index.html')
    return redirect('/terminal')


@views_bp.route('/<path:path>')
def catch_all(path):
    """
    Serve static assets from React dist (CSS, JS, images, logo, etc.).
    For unknown SPA routes (e.g. /credit, /try, /verify), serve React index.html
    so React Router handles navigation client-side.
    NEVER return HTML for /api/* routes — return 404 JSON so frontend shows real errors.
    """
    # API routes must NEVER be served as HTML
    if path.startswith('api/'):
        return jsonify({'error': 'API endpoint not found', 'path': f'/{path}'}), 404

    file_path = os.path.join(REACT_DIST, path)
    if os.path.isfile(file_path):
        return send_from_directory(REACT_DIST, path)

    react_index = os.path.join(REACT_DIST, 'index.html')
    if os.path.isfile(react_index):
        return send_from_directory(REACT_DIST, 'index.html')

    return render_template('terminal.html')
