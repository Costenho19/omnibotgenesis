#!/usr/bin/env python3
"""
OMNIX WSGI Entry Point for Railway Production
Gunicorn WSGI Server Configuration

Usage:
    gunicorn --bind 0.0.0.0:$PORT wsgi:app
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from omnix_dashboard.app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
