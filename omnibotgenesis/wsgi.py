#!/usr/bin/env python3
"""
OMNIX WSGI Entry Point for Railway Production
==============================================
Thin wrapper that delegates to src/omnix/bootstrap/wsgi_entry.py

This file is maintained for backward compatibility with Railway deployment.
The actual logic resides in the modular entrypoint.

Usage:
    gunicorn --bind 0.0.0.0:$PORT wsgi:app
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.omnix.bootstrap.wsgi_entry import app, create_wsgi_app
except ImportError:
    from omnix_dashboard.app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
