"""
OMNIX Decision Governance Dashboard
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
            r'https://.*\.railway\.app',
            r'https://.*\.up\.railway\.app',
            r'https://.*\.replit\.dev',
            r'https://.*\.replit\.app',
            r'https://.*\.repl\.co',
            r'https://.*\.worf\.replit\.dev',
        ]
        if not IS_RAILWAY:
            ALLOWED_ORIGINS.extend(['http://localhost:5000', 'http://127.0.0.1:5000', 'http://localhost:3000', 'http://127.0.0.1:3000'])
        ALLOWED_ORIGINS.extend(['https://www.omnixquantum.net', 'https://omnixquantum.net'])
    CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True, allow_headers=['Content-Type', 'Authorization'])
    
    DASHBOARD_API_KEY = os.environ.get('DASHBOARD_API_KEY')
    if IS_RAILWAY and not DASHBOARD_API_KEY:
        logger.warning("DASHBOARD_API_KEY not configured - sensitive endpoints will be public in production!")
    
    from omnix_dashboard.blueprints import (
        views_bp, core_bp, market_bp, intelligence_bp, system_bp,
        snapshots_bp, verification_bp, governance_bp,
        governance_risk_bp, governance_metrics_bp,
        governance_oversight_bp, governance_incidents_bp, governance_reports_bp,
        governance_sandbox_bp, governance_alerts_bp,
        public_sandbox_bp, public_verify_bp,
    )
    from omnix_dashboard.blueprints import credit_bp, insurance_bp, robotics_bp
    from omnix_dashboard.blueprints.live_metrics import live_metrics_bp

    # domain vertical blueprints FIRST — ensure /api/* routes take priority over views_bp catch-all
    app.register_blueprint(live_metrics_bp)
    app.register_blueprint(credit_bp)
    app.register_blueprint(insurance_bp)
    app.register_blueprint(robotics_bp)
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

    # Ensure credit tables exist BEFORE any request arrives (Railway fresh DB fix)
    try:
        import psycopg2 as _psycopg2
        _db_url = os.environ.get("DATABASE_URL")
        if _db_url:
            from omnix_core.credit.credit_simulator import _ensure_tables
            _credit_conn = _psycopg2.connect(_db_url)
            _ensure_tables(_credit_conn)
            _credit_conn.close()
    except Exception as _tbl_err:
        logger.warning(f"[Credit] Table init skipped: {_tbl_err}")

    # Start Islamic Credit Governance simulation engine in background
    try:
        from omnix_core.credit.credit_simulator import start_credit_simulation_background
        start_credit_simulation_background()
        logger.info("✅ [Credit] Islamic Credit Governance engine started (24/7 simulation)")
    except Exception as _credit_err:
        logger.warning(f"[Credit] Simulation engine startup skipped: {_credit_err}")

    # Start Insurance Governance simulation engine in background
    try:
        from omnix_core.insurance.insurance_simulator import start_background_simulator as _ins_start
        _ins_start()
        logger.info("✅ [Insurance] Insurance Governance engine started (24/7 simulation)")
    except Exception as _ins_err:
        logger.warning(f"[Insurance] Simulation engine startup skipped: {_ins_err}")

    # Start Robotics Governance simulation engine in background
    try:
        from omnix_core.robotics.robotics_simulator import start_background_simulator as _rbt_start
        _rbt_start()
        logger.info("✅ [Robotics] Robotics Governance engine started (24/7 simulation)")
    except Exception as _rbt_err:
        logger.warning(f"[Robotics] Simulation engine startup skipped: {_rbt_err}")

    try:
        from scripts.initialize_avm_baselines import initialize_avm_baselines
        initialize_avm_baselines()
    except Exception as _avm_err:
        logger.warning(f"[AVM.Init] Baseline initialization skipped: {_avm_err}")

    from omnix_dashboard.utils.database import shutdown_pool
    atexit.register(shutdown_pool)

    from omnix_dashboard.utils.auth import init_security
    init_security(app)
    
    return app


app = create_app()


# ─── Credit API direct routes (top-level, bypass blueprint routing conflicts) ───
@app.route('/api/credit/metrics')
@app.route('/api/credit/metrics.json')
def _credit_metrics_direct():
    from omnix_dashboard.blueprints.credit_governance import get_metrics
    return get_metrics()


@app.route('/api/credit/applications')
@app.route('/api/credit/applications.json')
def _credit_applications_direct():
    from omnix_dashboard.blueprints.credit_governance import get_applications
    return get_applications()


@app.route('/api/credit/sectors')
@app.route('/api/credit/sectors.json')
def _credit_sectors_direct():
    from omnix_dashboard.blueprints.credit_governance import get_sectors
    return get_sectors()


@app.route('/api/credit/health')
def _credit_health_direct():
    from omnix_dashboard.blueprints.credit_governance import get_health
    return get_health()


# ─── Insurance API direct routes ─────────────────────────────────────────────
@app.route('/api/insurance/metrics')
@app.route('/api/insurance/metrics.json')
def _insurance_metrics_direct():
    from omnix_dashboard.blueprints.insurance_governance import get_metrics
    return get_metrics()

@app.route('/api/insurance/claims')
def _insurance_claims_direct():
    from omnix_dashboard.blueprints.insurance_governance import get_claims
    return get_claims()

@app.route('/api/insurance/by-type')
def _insurance_by_type_direct():
    from omnix_dashboard.blueprints.insurance_governance import get_by_type
    return get_by_type()

@app.route('/api/insurance/by-region')
def _insurance_by_region_direct():
    from omnix_dashboard.blueprints.insurance_governance import get_by_region
    return get_by_region()

@app.route('/api/insurance/timeline')
def _insurance_timeline_direct():
    from omnix_dashboard.blueprints.insurance_governance import get_timeline
    return get_timeline()

@app.route('/api/insurance/health')
def _insurance_health_direct():
    from omnix_dashboard.blueprints.insurance_governance import health
    return health()

@app.route('/api/insurance/evaluate', methods=['POST'])
def _insurance_evaluate_direct():
    from omnix_dashboard.blueprints.insurance_governance import manual_evaluate
    return manual_evaluate()


# ─── Robotics API direct routes ───────────────────────────────────────────────
@app.route('/api/robotics/metrics')
@app.route('/api/robotics/metrics.json')
def _robotics_metrics_direct():
    from omnix_dashboard.blueprints.robotics_governance import get_metrics
    return get_metrics()

@app.route('/api/robotics/actions')
def _robotics_actions_direct():
    from omnix_dashboard.blueprints.robotics_governance import get_actions
    return get_actions()

@app.route('/api/robotics/by-industry')
def _robotics_by_industry_direct():
    from omnix_dashboard.blueprints.robotics_governance import get_by_industry
    return get_by_industry()

@app.route('/api/robotics/by-robot')
def _robotics_by_robot_direct():
    from omnix_dashboard.blueprints.robotics_governance import get_by_robot
    return get_by_robot()

@app.route('/api/robotics/fleet')
def _robotics_fleet_direct():
    from omnix_dashboard.blueprints.robotics_governance import get_fleet
    return get_fleet()

@app.route('/api/robotics/timeline')
def _robotics_timeline_direct():
    from omnix_dashboard.blueprints.robotics_governance import get_timeline
    return get_timeline()

@app.route('/api/robotics/health')
def _robotics_health_direct():
    from omnix_dashboard.blueprints.robotics_governance import health
    return health()

@app.route('/api/robotics/evaluate', methods=['POST'])
def _robotics_evaluate_direct():
    from omnix_dashboard.blueprints.robotics_governance import manual_evaluate
    return manual_evaluate()


@app.after_request
def strip_server_header(response):
    response.headers['Server'] = 'OMNIX-DGI'
    return response


@app.errorhandler(404)
def not_found(e):
    from flask import request, jsonify, send_from_directory
    if request.path.startswith('/api/'):
        return jsonify({'error': 'endpoint not found', 'path': request.path}), 404
    import os as _os
    react_dist = _os.path.normpath(_os.path.join(_os.path.dirname(__file__), '..', 'omnix_web', 'dist'))
    return send_from_directory(react_dist, 'index.html')


@app.errorhandler(500)
def internal_error(e):
    from flask import request, jsonify
    if request.path.startswith('/api/'):
        return jsonify({'error': 'internal server error', 'detail': str(e)}), 500
    return jsonify({'error': 'server error'}), 500


@app.errorhandler(Exception)
def unhandled_exception(e):
    from flask import request, jsonify
    logger.error(f"Unhandled exception on {request.path}: {e}", exc_info=True)
    if request.path.startswith('/api/'):
        return jsonify({'error': 'unexpected error', 'detail': str(e)}), 500
    return jsonify({'error': 'server error'}), 500


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
            logger.info("Dashboard will show 'Awaiting traders' until connection is fixed")
    else:
        logger.warning("No DATABASE_URL found - Dashboard will show empty state")
        logger.info("Set DATABASE_URL, POSTGRES_URL, or DATABASE_PUBLIC_URL in environment")
    
    logger.info(f"Debug endpoint: http://localhost:{port}/api/debug")
    app.run(host='0.0.0.0', port=port, debug=False)
