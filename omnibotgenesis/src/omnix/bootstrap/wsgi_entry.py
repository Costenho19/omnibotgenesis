#!/usr/bin/env python3
"""
OMNIX V7.0 WSGI Entry Point
============================
Phase 4: Modular WSGI entrypoint for Flask application.

This module serves as the new modular WSGI entrypoint for OMNIX Dashboard,
using the Flask application factory pattern with DI Container.

Usage:
    # Gunicorn
    gunicorn --bind 0.0.0.0:$PORT src.omnix.bootstrap.wsgi_entry:app
    
    # From legacy wrapper (wsgi.py)
    from src.omnix.bootstrap.wsgi_entry import app, create_wsgi_app
    
    # Direct execution
    python -m src.omnix.bootstrap.wsgi_entry
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)


def create_wsgi_app(use_app_layer: bool = False):
    """
    Create WSGI application using appropriate factory.
    
    Args:
        use_app_layer: Override USE_APP_LAYER setting. Defaults to False.
    
    Returns:
        Flask application instance
    """
    env_use_app_layer = os.environ.get('USE_APP_LAYER', 'false').lower() == 'true'
    use_app_layer = use_app_layer or env_use_app_layer
    
    if use_app_layer:
        from src.omnix.interfaces.flask_app import create_app
        from src.omnix.bootstrap import get_container
        
        container = get_container()
        logger.info("Creating Flask app with V7.0 factory (hexagonal)")
        return create_app(container=container)
    else:
        from omnix_dashboard.app import app as legacy_app
        logger.info("Using legacy Flask app from omnix_dashboard")
        return legacy_app


app = create_wsgi_app()


def run_development_server(host: str = '0.0.0.0', port: int = 8000):
    """Run Flask development server."""
    env_port = os.environ.get('PORT')
    if env_port:
        port = int(env_port)
    
    logger.info(f"Starting OMNIX Dashboard on {host}:{port}")
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    run_development_server()
