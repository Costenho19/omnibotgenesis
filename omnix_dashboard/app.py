"""
OMNIX Performance Dashboard INSTITUTIONAL+
Professional Institutional-Grade Trading & Portfolio Analytics
Premium 2025 Design with Portfolio Management - REAL DATA

Architecture:
- Flask Blueprints: Modular route organization
- Connection Pooling: psycopg_pool for efficient DB connections
- WSGI Server: Gunicorn with gevent workers (production)
- External APIs: ThreadPoolExecutor with timeout and fallback
"""

import os
import sys
import atexit
import logging
from flask import Flask
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IS_RAILWAY = bool(os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PROJECT_ID'))


def create_app():
    """Application factory pattern for Flask app creation"""
    app = Flask(__name__)
    
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
    
    from omnix_dashboard.blueprints import views_bp, core_bp, market_bp, intelligence_bp, system_bp, snapshots_bp
    
    app.register_blueprint(views_bp)
    app.register_blueprint(core_bp)
    app.register_blueprint(market_bp)
    app.register_blueprint(intelligence_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(snapshots_bp)
    
    from omnix_dashboard.utils.database import shutdown_pool
    atexit.register(shutdown_pool)
    
    return app


app = create_app()


if __name__ == '__main__':
    from .utils.database import get_database_url, init_database, DB_AVAILABLE, DB_ERROR_MESSAGE
    
    port = int(os.environ.get('PORT', 5000))
    from omnix_config import VERSION_BANNER
    logger.info(f"OMNIX Dashboard {VERSION_BANNER} starting on port {port}")
    
    database_url = get_database_url()
    if database_url:
        logger.info("DATABASE_URL detected - attempting connection...")
        if init_database():
            logger.info("Database connected successfully - REAL DATA MODE")
        else:
            logger.error(f"Database connection FAILED: {DB_ERROR_MESSAGE}")
            logger.info("Dashboard will show 'Esperando traders' until connection is fixed")
    else:
        logger.warning("No DATABASE_URL found - Dashboard will show empty state")
        logger.info("Set DATABASE_URL, POSTGRES_URL, or DATABASE_PUBLIC_URL in environment")
    
    logger.info(f"Debug endpoint: http://localhost:{port}/api/debug")
    app.run(host='0.0.0.0', port=port, debug=False)
