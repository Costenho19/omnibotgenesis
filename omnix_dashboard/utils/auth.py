"""
OMNIX Dashboard - Authentication & Rate Limiting Middleware
ADR-015: Dashboard Security Enhancement

Security Features:
- Basic HTTP Authentication with env vars (DASHBOARD_USER, DASHBOARD_PASSWORD)
- Rate limiting per IP (configurable via DASHBOARD_RATE_LIMIT, default 60/min)
- Optional IP allowlist (DASHBOARD_IP_ALLOWLIST)
- Health endpoint exemption for Railway healthchecks

PRODUCTION BEHAVIOR:
- In Railway (IS_RAILWAY=true): Auth is REQUIRED unless DASHBOARD_AUTH_OPTIONAL=true
- Without auth env vars in Railway: Dashboard returns 503 (fail-closed)

Usage:
    from omnix_dashboard.utils.auth import init_security
    init_security(app)
"""

import os
import time
import hmac
import logging
from collections import defaultdict
from typing import Optional, Set, Tuple
from flask import Flask, request, Response, g

logger = logging.getLogger(__name__)

_rate_limit_store: dict = defaultdict(list)
_RATE_LIMIT_WINDOW = 60
_MAX_TRACKED_IPS = 10000


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


def init_security(app: Flask) -> None:
    dashboard_user = os.environ.get('DASHBOARD_USER', '')
    dashboard_password = os.environ.get('DASHBOARD_PASSWORD', '')
    rate_limit = int(os.environ.get('DASHBOARD_RATE_LIMIT', '60'))
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
    
    @app.before_request
    def security_middleware():
        path = request.path
        client_ip = _get_client_ip()
        
        if _is_exempt_path(path):
            return None
        
        if auth_required_but_missing:
            logger.error(f"ACCESS DENIED: Auth not configured in production for path {path}")
            return Response(
                'Service unavailable - authentication not configured',
                status=503,
                mimetype='text/plain'
            )
        
        if allowed_ips and client_ip not in allowed_ips:
            logger.warning(f"IP BLOCKED: {client_ip} not in allowlist for path {path}")
            return Response(
                'Access denied - IP not in allowlist',
                status=403,
                mimetype='text/plain'
            )
        
        is_limited, reset_seconds = _is_rate_limited(client_ip, rate_limit)
        if is_limited:
            logger.warning(f"RATE LIMITED: {client_ip} exceeded {rate_limit}/min for path {path}")
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
                logger.debug(f"Auth required for {client_ip} accessing {path}")
                return Response(
                    'Authentication required',
                    status=401,
                    headers={'WWW-Authenticate': 'Basic realm="OMNIX Dashboard"'},
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
        
        if 'X-RateLimit-Limit' not in response.headers:
            response.headers['X-RateLimit-Limit'] = str(rate_limit)
        
        return response
    
    logger.info("Dashboard security middleware initialized successfully")
