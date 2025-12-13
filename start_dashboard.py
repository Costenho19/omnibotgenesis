#!/usr/bin/env python3
"""
OMNIX Dashboard Launcher
========================
Thin wrapper for backward compatibility.
Delegates to src/omnix/bootstrap/wsgi_entry.py

This file is maintained for scripts that reference start_dashboard.py.
Consider using wsgi.py or the modular entrypoint directly.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    os.environ.setdefault('PORT', '8000')
    
    try:
        from src.omnix.bootstrap.wsgi_entry import run_development_server
        run_development_server()
    except ImportError:
        from omnix_dashboard.app import app, logger
        
        port = int(os.environ.get('PORT', 8000))
        logger.info(f"OMNIX Dashboard starting on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
