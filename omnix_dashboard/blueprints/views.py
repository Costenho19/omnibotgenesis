"""
OMNIX Dashboard - Views Blueprint
HTML page routes (/, /terminal, /classic)
"""

from flask import Blueprint, render_template, redirect
from omnix_dashboard.utils.database import init_database

views_bp = Blueprint('views', __name__)


@views_bp.route('/')
def dashboard():
    """Main dashboard page - redirects to terminal"""
    return redirect('/terminal')


@views_bp.route('/terminal')
def terminal():
    """Bloomberg-style trading terminal"""
    init_database()
    return render_template('terminal.html')


@views_bp.route('/classic')
def classic_dashboard():
    """Classic dashboard page"""
    init_database()
    return render_template('dashboard.html')


@views_bp.route('/<path:path>')
def catch_all(path):
    """Redirect unknown routes to terminal dashboard"""
    return redirect('/terminal')
