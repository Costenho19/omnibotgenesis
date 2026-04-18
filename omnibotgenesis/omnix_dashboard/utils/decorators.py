"""
OMNIX Dashboard - Decorators
Authentication and utility decorators
"""

import os
import logging
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)


def is_railway():
    """Check if running in Railway environment."""
    return bool(os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PROJECT_ID'))


def require_api_key(f):
    """Decorator to protect sensitive endpoints with API key authentication.

    Behavior:
    - If DASHBOARD_API_KEY is not set: endpoints are public (development mode)
    - If DASHBOARD_API_KEY is set: requires X-API-Key header (header only — never query param)

    In Railway production, DASHBOARD_API_KEY should be set to protect sensitive data.

    Security: API keys are accepted via header only. Query-param fallback is intentionally
    removed to prevent key exposure in server logs, browser history, and proxy caches.

    NOTE: API key is resolved per-request to support dynamic configuration
    and WSGI deployments where env vars may be set after import time.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        dashboard_api_key = os.environ.get('DASHBOARD_API_KEY')

        if not dashboard_api_key:
            return f(*args, **kwargs)

        api_key = request.headers.get('X-API-Key')

        if api_key != dashboard_api_key:
            logger.warning(f"Unauthorized API access attempt to {request.path} from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized', 'code': 401}), 401

        return f(*args, **kwargs)
    return decorated
