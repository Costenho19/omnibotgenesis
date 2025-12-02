"""
OMNIX Dashboard - Decorators
Authentication and utility decorators
"""

import os
import logging
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)

IS_RAILWAY = bool(os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PROJECT_ID'))
DASHBOARD_API_KEY = os.environ.get('DASHBOARD_API_KEY')


def require_api_key(f):
    """Decorator to protect sensitive endpoints with API key authentication.
    
    Behavior:
    - If DASHBOARD_API_KEY is not set: endpoints are public (development mode)
    - If DASHBOARD_API_KEY is set: requires X-API-Key header or api_key query param
    
    In Railway production, DASHBOARD_API_KEY should be set to protect sensitive data.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not DASHBOARD_API_KEY:
            return f(*args, **kwargs)
        
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if api_key != DASHBOARD_API_KEY:
            logger.warning(f"Unauthorized API access attempt to {request.path} from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized', 'code': 401}), 401
        
        return f(*args, **kwargs)
    return decorated
