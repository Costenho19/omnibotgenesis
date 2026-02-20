"""
OMNIX Dashboard - Institutional Security Middleware
ADR-015: Dashboard Security Enhancement + Feb 2026 Hardening

Security Controls:
- Basic HTTP Authentication with env vars (DASHBOARD_USER, DASHBOARD_PASSWORD)
- Rate limiting per IP (configurable via DASHBOARD_RATE_LIMIT, default 300/min)
- Optional IP allowlist (DASHBOARD_IP_ALLOWLIST)
- Health endpoint exemption for Railway healthchecks
- Institutional security headers (HSTS, CSP, Permissions-Policy)
- Server identity concealment (no version fingerprinting)
- Centralized error sanitization (no stack trace leakage)
- Security event audit logging
- Log redaction of secrets/API keys

PRODUCTION BEHAVIOR:
- In Railway (IS_RAILWAY=true): Auth is REQUIRED unless DASHBOARD_AUTH_OPTIONAL=true
- Without auth env vars in Railway: Dashboard returns 503 (fail-closed)

Usage:
    from omnix_dashboard.utils.auth import init_security
    init_security(app)
"""

import os
import re
import time
import hmac
import uuid
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional, Set, Tuple
from flask import Flask, request, Response, g, jsonify

logger = logging.getLogger(__name__)
security_logger = logging.getLogger('omnix.security')

_rate_limit_store: dict = defaultdict(list)
_RATE_LIMIT_WINDOW = 60
_MAX_TRACKED_IPS = 10000

_SECRET_PATTERNS = [
    re.compile(r'(sk-[a-zA-Z0-9]{20,})', re.IGNORECASE),
    re.compile(r'(AIza[a-zA-Z0-9_-]{35})', re.IGNORECASE),
    re.compile(r'(xox[bpoas]-[a-zA-Z0-9-]+)', re.IGNORECASE),
    re.compile(r'([0-9]+:AA[a-zA-Z0-9_-]{33})', re.IGNORECASE),
    re.compile(r'(tvly-[a-zA-Z0-9]{20,})', re.IGNORECASE),
    re.compile(r'(ghp_[a-zA-Z0-9]{36})', re.IGNORECASE),
    re.compile(r'(postgres(?:ql)?://[^\s"\']+)', re.IGNORECASE),
    re.compile(r'(redis://[^\s"\']+)', re.IGNORECASE),
    re.compile(r'(mongodb(?:\+srv)?://[^\s"\']+)', re.IGNORECASE),
    re.compile(r'(?:password|passwd|pwd|secret|token|api_key|apikey)[\s]*[=:]\s*["\']?([^\s"\']{8,})', re.IGNORECASE),
]


def redact_secrets(text: str) -> str:
    if not isinstance(text, str):
        return str(text)
    result = text
    for pattern in _SECRET_PATTERNS:
        result = pattern.sub(lambda m: m.group(0)[:6] + '***REDACTED***', result)
    return result


class SecretRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = redact_secrets(record.msg)
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, dict):
                record.args = {k: redact_secrets(str(v)) if isinstance(v, str) else v for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(redact_secrets(str(a)) if isinstance(a, str) else a for a in record.args)
        return True


def _log_security_event(event_type: str, details: dict) -> None:
    event = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event': event_type,
        **details
    }
    security_logger.warning(f"SECURITY_EVENT | {event_type} | {details.get('client_ip', 'unknown')} | {details.get('path', '/')} | {details.get('reason', '')}")


def _get_client_ip() -> str:
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr or '127.0.0.1'


def _check_basic_auth(auth_header: Optional[str], username: str, password: str) -> bool:
    if not auth_header or not auth_header.startswith('Basic '):
        return False
    
    import base64
    try:
        encoded = auth_header[6:]
        decoded = base64.b64decode(encoded).decode('utf-8')
        provided_user, provided_pass = decoded.split(':', 1)
        user_match = hmac.compare_digest(provided_user, username)
        pass_match = hmac.compare_digest(provided_pass, password)
        return user_match and pass_match
    except Exception:
        return False


def _is_rate_limited(client_ip: str, max_requests: int) -> Tuple[bool, int]:
    global _rate_limit_store
    now = time.time()
    window_start = now - _RATE_LIMIT_WINDOW
    
    if len(_rate_limit_store) > _MAX_TRACKED_IPS:
        cutoff = now - (_RATE_LIMIT_WINDOW * 2)
        _rate_limit_store = defaultdict(list, {
            ip: [ts for ts in timestamps if ts > cutoff]
            for ip, timestamps in _rate_limit_store.items()
            if any(ts > cutoff for ts in timestamps)
        })
        logger.info(f"Rate limit store cleaned: {len(_rate_limit_store)} IPs tracked")
    
    _rate_limit_store[client_ip] = [
        ts for ts in _rate_limit_store[client_ip] if ts > window_start
    ]
    
    current_count = len(_rate_limit_store[client_ip])
    
    if current_count >= max_requests:
        reset_time = int(_rate_limit_store[client_ip][0] + _RATE_LIMIT_WINDOW - now)
        return True, max(reset_time, 1)
    
    _rate_limit_store[client_ip].append(now)
    return False, 0


def _get_allowed_ips() -> Set[str]:
    allowlist = os.environ.get('DASHBOARD_IP_ALLOWLIST', '')
    if not allowlist:
        return set()
    return {ip.strip() for ip in allowlist.split(',') if ip.strip()}


def _is_exempt_path(path: str) -> bool:
    exempt_paths = [
        '/api/health',
        '/health',
        '/static/',
        '/favicon.ico',
    ]
    return any(path.startswith(p) or path == p for p in exempt_paths)


def _sanitize_error_message(error_msg: str) -> str:
    raw = str(error_msg)
    if any(kw in raw for kw in ['Traceback', 'File "/', 'ModuleNotFoundError', 'psycopg']):
        return 'Internal server error'
    sanitized = re.sub(r'File ".*?", line \d+', '[internal]', raw)
    sanitized = re.sub(r'Traceback \(most recent call last\):.*', '', sanitized, flags=re.DOTALL)
    sanitized = re.sub(r'/home/[^\s"\']+', '[path]', sanitized)
    sanitized = re.sub(r'/app/[^\s"\']+', '[path]', sanitized)
    sanitized = re.sub(r'/usr/[^\s"\']+', '[path]', sanitized)
    sanitized = re.sub(r'[A-Z][A-Z_]{3,}(?:_KEY|_TOKEN|_SECRET|_URL|_PASSWORD|_HOST|_PORT|_USER)', '[CONFIG]', sanitized)
    sanitized = re.sub(r'(?:Replit Secrets|\.env\.local|\.env|environment variables?)', '[config]', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'VARIABLE REQUERIDA NO ENCONTRADA:.*', 'Service configuration required', sanitized)
    sanitized = re.sub(r'Por favor configura.*', '', sanitized)
    sanitized = re.sub(r'(?:KeyError|AttributeError|TypeError|ValueError|ImportError|ModuleNotFoundError):?\s*.*', 'Internal server error', sanitized)
    sanitized = re.sub(r'(?:Connection refused|Connection reset|Broken pipe|Timeout).*', 'Service temporarily unavailable', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'(?:postgres|redis|mongodb|mysql)://[^\s]+', '[database]', sanitized, flags=re.IGNORECASE)
    sanitized = redact_secrets(sanitized)
    if len(sanitized) > 200:
        sanitized = sanitized[:200] + '...'
    return sanitized.strip() or 'Internal server error'


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(400)
    def handle_400(e):
        return jsonify({
            'error': 'Bad request',
            'status': 400,
            'reference': str(uuid.uuid4())[:8]
        }), 400

    @app.errorhandler(401)
    def handle_401(e):
        return jsonify({
            'error': 'Authentication required',
            'status': 401,
            'reference': str(uuid.uuid4())[:8]
        }), 401

    @app.errorhandler(403)
    def handle_403(e):
        return jsonify({
            'error': 'Access denied',
            'status': 403,
            'reference': str(uuid.uuid4())[:8]
        }), 403

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({
            'error': 'Resource not found',
            'status': 404,
            'reference': str(uuid.uuid4())[:8]
        }), 404

    @app.errorhandler(429)
    def handle_429(e):
        return jsonify({
            'error': 'Rate limit exceeded',
            'status': 429,
            'reference': str(uuid.uuid4())[:8]
        }), 429

    @app.errorhandler(500)
    def handle_500(e):
        ref_id = str(uuid.uuid4())[:8]
        logger.error(f"Internal error ref={ref_id}: {redact_secrets(str(e))}")
        return jsonify({
            'error': 'Internal server error',
            'status': 500,
            'reference': ref_id
        }), 500

    @app.errorhandler(503)
    def handle_503(e):
        return jsonify({
            'error': 'Service temporarily unavailable',
            'status': 503,
            'reference': str(uuid.uuid4())[:8]
        }), 503


def init_security(app: Flask) -> None:
    root_logger = logging.getLogger()
    redaction_filter = SecretRedactionFilter()
    root_logger.addFilter(redaction_filter)
    for handler in root_logger.handlers:
        handler.addFilter(redaction_filter)

    dashboard_user = os.environ.get('DASHBOARD_USER', '')
    dashboard_password = os.environ.get('DASHBOARD_PASSWORD', '')
    rate_limit = int(os.environ.get('DASHBOARD_RATE_LIMIT', '300'))
    is_railway = bool(os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PROJECT_ID'))
    auth_optional = os.environ.get('DASHBOARD_AUTH_OPTIONAL', '').lower() == 'true'
    
    auth_enabled = bool(dashboard_user and dashboard_password)
    auth_required_but_missing = is_railway and not auth_enabled and not auth_optional
    
    if auth_required_but_missing:
        logger.critical("SECURITY FAIL-CLOSED: DASHBOARD_USER/PASSWORD required in production!")
        logger.critical("Set DASHBOARD_AUTH_OPTIONAL=true to override (NOT RECOMMENDED)")
    elif auth_enabled:
        logger.info(f"Dashboard Basic Auth ENABLED (user: {dashboard_user[:3]}***)")
    else:
        if is_railway and auth_optional:
            logger.warning("SECURITY WARNING: Auth disabled via DASHBOARD_AUTH_OPTIONAL - dashboard is PUBLIC!")
        else:
            logger.info("Dashboard auth disabled (development mode) - set DASHBOARD_USER and DASHBOARD_PASSWORD to enable")
    
    logger.info(f"Dashboard rate limit: {rate_limit} requests/minute per IP")
    
    allowed_ips = _get_allowed_ips()
    if allowed_ips:
        logger.info(f"Dashboard IP allowlist ENABLED: {len(allowed_ips)} IPs configured")

    _register_error_handlers(app)
    
    @app.before_request
    def security_middleware():
        path = request.path
        client_ip = _get_client_ip()
        g.request_id = str(uuid.uuid4())[:8]
        
        if _is_exempt_path(path):
            return None
        
        if auth_required_but_missing:
            _log_security_event('AUTH_NOT_CONFIGURED', {
                'client_ip': client_ip,
                'path': path,
                'reason': 'Production auth not configured'
            })
            return Response(
                'Service unavailable - authentication not configured',
                status=503,
                mimetype='text/plain'
            )
        
        if allowed_ips and client_ip not in allowed_ips:
            _log_security_event('IP_BLOCKED', {
                'client_ip': client_ip,
                'path': path,
                'reason': f'IP not in allowlist ({len(allowed_ips)} allowed)'
            })
            return Response(
                'Access denied - IP not in allowlist',
                status=403,
                mimetype='text/plain'
            )
        
        is_limited, reset_seconds = _is_rate_limited(client_ip, rate_limit)
        if is_limited:
            _log_security_event('RATE_LIMITED', {
                'client_ip': client_ip,
                'path': path,
                'reason': f'Exceeded {rate_limit}/min'
            })
            return Response(
                f'Rate limit exceeded. Retry after {reset_seconds} seconds.',
                status=429,
                headers={
                    'Retry-After': str(reset_seconds),
                    'X-RateLimit-Limit': str(rate_limit),
                    'X-RateLimit-Reset': str(int(time.time()) + reset_seconds)
                },
                mimetype='text/plain'
            )
        
        if auth_enabled:
            auth_header = request.headers.get('Authorization')
            if not _check_basic_auth(auth_header, dashboard_user, dashboard_password):
                _log_security_event('AUTH_FAILED', {
                    'client_ip': client_ip,
                    'path': path,
                    'reason': 'Invalid or missing credentials'
                })
                return Response(
                    'Authentication required',
                    status=401,
                    headers={'WWW-Authenticate': 'Basic realm="OMNIX Decision Governance"'},
                    mimetype='text/plain'
                )
        
        g.client_ip = client_ip
        return None
    
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=(), payment=()'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://cdn.plot.ly; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.coingecko.com https://api.alternative.me https://finnhub.io; "
            "frame-ancestors 'self'"
        )
        
        response.headers.pop('Server', None)
        response.headers.pop('X-Powered-By', None)
        
        if 'X-RateLimit-Limit' not in response.headers:
            response.headers['X-RateLimit-Limit'] = str(rate_limit)

        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id

        if response.status_code >= 400 and response.content_type and 'json' in response.content_type:
            try:
                import json
                data = response.get_json(silent=True)
                if data and isinstance(data, dict) and 'error' in data:
                    raw_error = str(data.get('error', ''))
                    data['error'] = _sanitize_error_message(raw_error)
                    if 'success' in data:
                        data['success'] = False
                    ref_id = g.request_id if hasattr(g, 'request_id') else str(uuid.uuid4())[:8]
                    data['reference'] = ref_id
                    logger.error(f"Error response ref={ref_id} status={response.status_code}: {redact_secrets(raw_error[:200])}")
                    response.set_data(json.dumps(data))
            except Exception:
                pass
        
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        
        return response
    
    logger.info("Dashboard institutional security middleware initialized")
    logger.info(f"Security controls: Headers(12) | RateLimit({rate_limit}/min) | Auth({'ON' if auth_enabled else 'OFF'}) | ErrorSanitization(ON) | LogRedaction(ON) | CacheControl(ON)")
