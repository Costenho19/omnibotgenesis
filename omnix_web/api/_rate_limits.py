"""
Shared Flask-Limiter instance for PoGR blueprint.
Avoids circular import: pogr_blueprint cannot import from server.py
because server.py already imports pogr_bp from pogr_blueprint.

Usage:
  pogr_blueprint.py  → from api._rate_limits import pogr_limiter
  server.py          → from api._rate_limits import pogr_limiter; pogr_limiter.init_app(app)

ADR-205 §7 — R-M3 rate limiting on public PoGR endpoints.

Storage strategy (ADR-205 R-M3):
  1. Attempt Redis (REDIS_URL env var) with a 2-second connect timeout.
  2. If Redis is unreachable or REDIS_URL is unset, fall back to memory://.
     In-process memory is effective for Replit autoscale single-instance bursts.
  3. swallow_errors=False — any storage failure after initialisation surfaces as
     an HTTP 500 rather than silently allowing unlimited requests through.
"""
import logging
import os

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)

_REDIS_URL = os.environ.get("REDIS_URL", "")


def _resolve_storage_uri() -> str:
    """
    Probe Redis availability at module load time.
    Returns the Redis URI if reachable within 2 s, otherwise 'memory://'.
    Logs clearly so production deployments show which backend is active.
    """
    if _REDIS_URL:
        try:
            import redis as _redis_lib
            _client = _redis_lib.from_url(
                _REDIS_URL,
                socket_connect_timeout=2,
                socket_timeout=2,
                decode_responses=True,
            )
            _client.ping()
            _host = _REDIS_URL.split("@")[-1] if "@" in _REDIS_URL else _REDIS_URL
            logger.info(
                "[PoGR.RateLimit] Redis storage active — host=%s "
                "(ADR-205 R-M3, distributed counter)", _host
            )
            return _REDIS_URL
        except Exception as exc:
            logger.warning(
                "[PoGR.RateLimit] Redis unreachable at startup (%s) — "
                "falling back to memory:// (per-process counter, single-instance effective). "
                "ADR-205 R-M3 rate limit still enforced.", exc
            )
    else:
        logger.info(
            "[PoGR.RateLimit] REDIS_URL not configured — "
            "using memory:// storage (ADR-205 R-M3)"
        )
    return "memory://"


_STORAGE_URI = _resolve_storage_uri()

pogr_limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri=_STORAGE_URI,
    swallow_errors=False,
)
