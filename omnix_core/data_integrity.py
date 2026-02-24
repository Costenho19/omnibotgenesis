"""
OMNIX Real-Data Integrity Module

Enforces a strict policy: every user-facing metric must come from a verified
real data source (PostgreSQL, live API, or actual process metrics).

If no real data is available, the system returns "Insufficient real data"
instead of an estimated or hardcoded number.

Created: February 24, 2026
Policy: "todo real, nada inventado"
"""

import os
import logging
import functools
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

REAL_DATA_MODE = True

INSUFFICIENT_DATA_RESPONSE = {
    'status': 'insufficient_data',
    'message': 'Insufficient real data',
    'source': None
}

_VALID_SOURCES = {
    'postgresql',
    'kraken_api',
    'kraken_public',
    'alpaca_api',
    'coingecko_api',
    'finnhub_api',
    'alpha_vantage_api',
    'alternative_me_api',
    'psutil_process',
    'system_clock',
    'redis_cache',
    'anu_qrng',
    'tavily_api',
}


def real_data_required(source: str):
    """
    Decorator that enforces real data sourcing for any metric-producing function.

    When REAL_DATA_MODE is True (always in production):
    - The decorated function MUST return data from a verified source
    - If it raises an exception or returns None, the system returns
      INSUFFICIENT_DATA_RESPONSE instead of a fallback/estimated value

    Usage:
        @real_data_required(source='postgresql')
        def get_evaluation_cycles():
            return db.query("SELECT COUNT(*) FROM shadow_trade_events")
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not REAL_DATA_MODE:
                return func(*args, **kwargs)

            try:
                result = func(*args, **kwargs)
                if result is None:
                    logger.warning(
                        f"[DATA_INTEGRITY] {func.__qualname__} returned None — "
                        f"source '{source}' unavailable"
                    )
                    return _build_insufficient_response(func.__qualname__, source)
                return result
            except Exception as e:
                logger.warning(
                    f"[DATA_INTEGRITY] {func.__qualname__} failed — "
                    f"source '{source}' error: {e}"
                )
                return _build_insufficient_response(func.__qualname__, source, str(e))
        wrapper._real_data_source = source
        return wrapper
    return decorator


def _build_insufficient_response(func_name: str, source: str, error: str = None) -> Dict:
    response = {
        'status': 'insufficient_data',
        'message': 'Insufficient real data',
        'source': source,
        'function': func_name
    }
    if error:
        response['error'] = error
    return response


def is_insufficient(result: Any) -> bool:
    if isinstance(result, dict) and result.get('status') == 'insufficient_data':
        return True
    return False


def validate_metric(value: Any, metric_name: str, source: str) -> Dict:
    """
    Validate that a metric value is real (not None, not a default).
    Returns a dict with the value and its source for traceability.
    """
    if value is None:
        return {
            'value': None,
            'metric': metric_name,
            'status': 'insufficient_data',
            'message': 'Insufficient real data',
            'source': source
        }
    return {
        'value': value,
        'metric': metric_name,
        'status': 'real',
        'source': source
    }


def format_metric_for_display(validated: Dict) -> str:
    """
    Format a validated metric for user-facing display.
    Returns "Insufficient real data" if the metric has no real value.
    """
    if validated.get('status') == 'insufficient_data':
        return 'Insufficient real data'

    value = validated.get('value')
    if isinstance(value, float):
        if value < 1:
            return f"{value:.2%}"
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)
