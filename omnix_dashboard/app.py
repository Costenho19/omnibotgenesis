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
    from omnix_dashboard.blueprints import credit_bp, insurance_bp, robotics_bp, medical_bp, agents_bp, real_estate_bp, energy_bp, stablecoin_bp
    from omnix_dashboard.blueprints.live_metrics import live_metrics_bp
    from omnix_dashboard.blueprints.receipt_verification import receipt_pki_bp

    # domain vertical blueprints FIRST — ensure /api/* routes take priority over views_bp catch-all
    app.register_blueprint(live_metrics_bp)
    app.register_blueprint(credit_bp)
    app.register_blueprint(insurance_bp)
    app.register_blueprint(robotics_bp)
    app.register_blueprint(medical_bp)
    app.register_blueprint(agents_bp)
    app.register_blueprint(real_estate_bp)
    app.register_blueprint(energy_bp)
    app.register_blueprint(stablecoin_bp)
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
    app.register_blueprint(receipt_pki_bp)

    # Ensure credit tables exist BEFORE any request arrives (Railway fresh DB fix)
    try:
        import psycopg2 as _psycopg2
        _db_url = os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
        if _db_url:
            from omnix_core.credit.credit_simulator import _ensure_tables
            _credit_conn = _psycopg2.connect(_db_url)
            _ensure_tables(_credit_conn)
            _credit_conn.close()
    except Exception as _tbl_err:
        logger.warning(f"[Credit] Table init skipped: {_tbl_err}")

    # Ensure Medical AI tables exist BEFORE any request arrives
    try:
        import psycopg2 as _psycopg2
        _db_url = os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
        if _db_url:
            from omnix_core.medical.medical_simulator import _create_medical_decisions_table
            _med_conn = _psycopg2.connect(_db_url)
            _create_medical_decisions_table(_med_conn)
            _med_conn.close()
            logger.info("✅ [Medical] Tables initialized")
    except Exception as _med_tbl_err:
        logger.warning(f"[Medical] Table init skipped: {_med_tbl_err}")

    # Ensure Autonomous Agent tables exist BEFORE any request arrives
    try:
        import psycopg2 as _psycopg2
        _db_url = os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
        if _db_url:
            from omnix_core.agents.agents_simulator import _create_agent_decisions_table
            _agt_conn = _psycopg2.connect(_db_url)
            _create_agent_decisions_table(_agt_conn)
            _agt_conn.close()
            logger.info("✅ [Agents] Tables initialized")
    except Exception as _agt_tbl_err:
        logger.warning(f"[Agents] Table init skipped: {_agt_tbl_err}")

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

    # Start Medical AI Governance simulation engine in background
    try:
        from omnix_core.medical.medical_simulator import start_background_simulator as _med_start
        _med_start()
        logger.info("✅ [Medical] Medical AI Governance engine started (24/7 simulation)")
    except Exception as _med_err:
        logger.warning(f"[Medical] Simulation engine startup skipped: {_med_err}")

    # Start Autonomous Agent Governance simulation engine in background
    try:
        from omnix_core.agents.agents_simulator import start_background_simulator as _agt_start
        _agt_start()
        logger.info("✅ [Agents] Autonomous Agent Governance engine started (24/7 simulation)")
    except Exception as _agt_err:
        logger.warning(f"[Agents] Simulation engine startup skipped: {_agt_err}")

    # Ensure Real Estate tables exist BEFORE any request arrives
    try:
        import psycopg2 as _psycopg2
        _db_url = os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
        if _db_url:
            from omnix_core.real_estate.real_estate_simulator import _create_property_decisions_table
            _res_conn = _psycopg2.connect(_db_url)
            _create_property_decisions_table(_res_conn)
            _res_conn.close()
            logger.info("✅ [RealEstate] Tables initialized")
    except Exception as _res_tbl_err:
        logger.warning(f"[RealEstate] Table init skipped: {_res_tbl_err}")

    # Start Real Estate Governance simulation engine in background
    try:
        from omnix_core.real_estate.real_estate_simulator import start_background_simulator as _res_start
        _res_start()
        logger.info("✅ [RealEstate] Real Estate Governance engine started (24/7 simulation)")
    except Exception as _res_err:
        logger.warning(f"[RealEstate] Simulation engine startup skipped: {_res_err}")

    # Initialize Energy Governance tables
    try:
        import psycopg2 as _psycopg2
        _db_url = os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
        if _db_url:
            from omnix_core.energy.energy_simulator import _create_energy_tables
            _egy_conn = _psycopg2.connect(_db_url)
            _create_energy_tables(_egy_conn)
            _egy_conn.close()
            logger.info("✅ [Energy] Tables initialized")
    except Exception as _egy_tbl_err:
        logger.warning(f"[Energy] Table init skipped: {_egy_tbl_err}")

    # Start Energy Governance simulation engine in background
    try:
        from omnix_core.energy.energy_simulator import start_background_simulator as _egy_start
        _egy_start()
        logger.info("✅ [Energy] Energy Governance engine started (24/7 simulation)")
    except Exception as _egy_err:
        logger.warning(f"[Energy] Simulation engine startup skipped: {_egy_err}")

    # Initialize Stablecoin Reserve Governance tables
    try:
        import psycopg2 as _psycopg2
        _db_url = os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
        if _db_url:
            from omnix_core.stablecoin.stablecoin_simulator import _create_stablecoin_tables
            _srg_conn = _psycopg2.connect(_db_url)
            _create_stablecoin_tables(_srg_conn)
            _srg_conn.close()
            logger.info("✅ [Stablecoin] Tables initialized")
    except Exception as _srg_tbl_err:
        logger.warning(f"[Stablecoin] Table init skipped: {_srg_tbl_err}")

    # Start Stablecoin Reserve Governance simulation engine in background
    try:
        from omnix_core.stablecoin.stablecoin_simulator import start_background_simulator as _srg_start
        _srg_start()
        logger.info("✅ [Stablecoin] Reserve Governance engine started (24/7 simulation)")
    except Exception as _srg_err:
        logger.warning(f"[Stablecoin] Simulation engine startup skipped: {_srg_err}")

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


@app.route('/api/public/<path:subpath>', methods=['GET', 'POST', 'OPTIONS'])
def proxy_public_api(subpath):
    """Forward /api/public/* to OMNIX Web API on port 8080 (dev only)."""
    import requests as _req
    from flask import request, Response
    target = f"http://127.0.0.1:8080/api/public/{subpath}"
    try:
        resp = _req.request(
            method=request.method,
            url=target,
            params=request.args,
            data=request.get_data(),
            headers={k: v for k, v in request.headers if k.lower() not in ('host', 'content-length')},
            timeout=30,
            allow_redirects=False,
        )
        excluded = {'content-encoding', 'content-length', 'transfer-encoding', 'connection'}
        headers = [(k, v) for k, v in resp.headers.items() if k.lower() not in excluded]
        return Response(resp.content, status=resp.status_code, headers=headers)
    except Exception as _e:
        from flask import jsonify
        return jsonify({'success': False, 'error': str(_e)}), 503


@app.after_request
def strip_server_header(response):
    response.headers['Server'] = 'OMNIX-DGI'
    return response


@app.after_request
def add_security_headers(response):
    is_api = response.content_type and 'application/json' in response.content_type
    if not is_api:
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    if IS_RAILWAY:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    return response


@app.after_request
def block_api_html_leak(response):
    """Nuclear guard: if any /api/* path somehow gets an HTML response,
    convert it to 404 JSON. This prevents the SPA catch-all from leaking
    into API routes regardless of blueprint registration order or cache issues."""
    from flask import request as _req, jsonify as _jsonify
    response.headers['X-OMNIX-Guard'] = '1'
    if _req.path.startswith('/api/') and response.status_code == 200 and \
            response.content_type and 'text/html' in response.content_type:
        new_resp = _jsonify({'error': 'API endpoint not found', 'path': _req.path})
        new_resp.headers['X-OMNIX-Guard'] = 'blocked'
        return new_resp, 404
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
