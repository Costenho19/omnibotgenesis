"""
OMNIX V7.0 Flask Application Factory
=====================================
Phase 3b: Flask App Factory with DI Container integration.

This module provides a Flask application factory that uses the OMNIX
DI Container for dependency injection, following hexagonal architecture.

Usage:
    from src.omnix.interfaces.flask_app import create_app
    app = create_app()
    
    # With custom container
    from src.omnix.bootstrap import Container
    container = Container.create()
    app = create_app(container=container)
"""

import os
import atexit
import logging
from typing import Optional
from flask import Flask, jsonify
from flask_cors import CORS

logger = logging.getLogger(__name__)

IS_RAILWAY = bool(os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PROJECT_ID'))


def create_app(container=None) -> Flask:
    """
    Application factory pattern for Flask app creation.
    
    Uses OMNIX DI Container for dependency injection.
    Registers all dashboard blueprints.
    
    Args:
        container: Optional DI container. If None, creates default container.
    
    Returns:
        Flask application instance
    """
    from src.omnix.bootstrap.container import get_container
    
    if container is None:
        container = get_container()
    
    app = Flask(__name__)
    app.config['CONTAINER'] = container
    
    SECRET_KEY = os.environ.get('SESSION_SECRET')
    if not SECRET_KEY:
        if IS_RAILWAY:
            raise RuntimeError("CRITICAL: SESSION_SECRET must be configured in Railway production environment")
        logger.warning("SESSION_SECRET not configured - using development mode (insecure)")
        SECRET_KEY = 'dev-only-insecure-key-do-not-use-in-production'
    app.config['SECRET_KEY'] = SECRET_KEY
    
    ALLOWED_ORIGINS = os.environ.get('DASHBOARD_ALLOWED_ORIGINS', '').split(',')
    if not ALLOWED_ORIGINS or ALLOWED_ORIGINS == ['']:
        ALLOWED_ORIGINS = [
            'https://*.railway.app',
            'https://*.up.railway.app', 
            'https://*.replit.dev',
            'https://*.repl.co'
        ]
        if not IS_RAILWAY:
            ALLOWED_ORIGINS.extend(['http://localhost:5000', 'http://127.0.0.1:5000'])
    CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)
    
    DASHBOARD_API_KEY = os.environ.get('DASHBOARD_API_KEY')
    if IS_RAILWAY and not DASHBOARD_API_KEY:
        logger.warning("DASHBOARD_API_KEY not configured - sensitive endpoints will be public in production!")
    
    _register_blueprints(app)
    _register_health_endpoints(app, container)
    _register_cleanup(app)
    
    logger.info(f"OMNIX Flask App created (use_app_layer={container.use_app_layer})")
    
    return app


def _register_blueprints(app: Flask) -> None:
    """Register all dashboard blueprints."""
    try:
        from omnix_dashboard.blueprints import (
            views_bp, core_bp, market_bp,
            intelligence_bp, system_bp, snapshots_bp,
            verification_bp, governance_bp, governance_risk_bp,
            governance_metrics_bp, governance_oversight_bp,
            governance_incidents_bp, governance_reports_bp,
            governance_sandbox_bp, governance_alerts_bp,
            public_sandbox_bp, public_verify_bp, credit_bp
        )

        app.register_blueprint(views_bp)
        app.register_blueprint(core_bp)
        app.register_blueprint(market_bp)
        app.register_blueprint(intelligence_bp)
        app.register_blueprint(system_bp)
        app.register_blueprint(snapshots_bp)
        app.register_blueprint(verification_bp)
        app.register_blueprint(governance_bp)
        app.register_blueprint(governance_risk_bp)
        app.register_blueprint(governance_metrics_bp)
        app.register_blueprint(governance_oversight_bp)
        app.register_blueprint(governance_incidents_bp)
        app.register_blueprint(governance_reports_bp)
        app.register_blueprint(governance_sandbox_bp)
        app.register_blueprint(governance_alerts_bp)
        app.register_blueprint(public_sandbox_bp)
        app.register_blueprint(public_verify_bp)
        app.register_blueprint(credit_bp)

        # Ensure credit tables exist at startup (Railway fresh DB fix)
        try:
            import psycopg2 as _psycopg2
            import os as _os
            _db_url = _os.environ.get("DATABASE_URL")
            if _db_url:
                from omnix_core.credit.credit_simulator import _ensure_tables
                _c = _psycopg2.connect(_db_url)
                _ensure_tables(_c)
                _c.close()
        except Exception as _e:
            logger.warning(f"[Credit] Table init skipped: {_e}")

        # Start credit simulation engine (skip in test mode)
        if not os.environ.get('TESTING'):
            try:
                from omnix_core.credit.credit_simulator import start_credit_simulation_background
                start_credit_simulation_background()
                logger.info("✅ [Credit] Islamic Credit Governance engine started")
            except Exception as _e:
                logger.warning(f"[Credit] Simulation engine skipped: {_e}")

        logger.info("Registered 18 dashboard blueprints")
    except ImportError as e:
        logger.warning(f"Could not register dashboard blueprints: {e}")


def _register_health_endpoints(app: Flask, container) -> None:
    """Register health check endpoints using container."""
    
    @app.route('/health')
    def health():
        """Basic health check."""
        return jsonify({'status': 'healthy', 'use_app_layer': container.use_app_layer})
    
    @app.route('/health/detailed')
    def health_detailed():
        """Detailed health check with container status."""
        return jsonify({
            'status': 'healthy',
            'container': container.health_check(),
        })
    
    @app.route('/api/container/status')
    def container_status():
        """Container DI status endpoint."""
        return jsonify(container.health_check())


def _register_cleanup(app: Flask) -> None:
    """Register cleanup handlers."""
    try:
        from omnix_dashboard.utils.database import shutdown_pool
        atexit.register(shutdown_pool)
        logger.info("Registered database pool cleanup handler")
    except ImportError:
        logger.warning("Could not register database pool cleanup")


def get_app(container=None) -> Flask:
    """
    Get or create Flask application.
    
    This is an alias for create_app() for compatibility.
    """
    return create_app(container=container)
