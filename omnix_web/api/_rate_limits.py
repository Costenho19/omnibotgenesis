"""
Shared Flask-Limiter instance for PoGR blueprint.
Avoids circular import: pogr_blueprint cannot import from server.py
because server.py already imports pogr_bp from pogr_blueprint.

Usage:
  pogr_blueprint.py  → from api._rate_limits import pogr_limiter
  server.py          → from api._rate_limits import pogr_limiter; pogr_limiter.init_app(app)

ADR-205 §7 — R-M3 rate limiting on public PoGR endpoints.
"""
import os

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

_REDIS_URL = os.environ.get("REDIS_URL", "memory://")

pogr_limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri=_REDIS_URL,
    swallow_errors=True,
)
