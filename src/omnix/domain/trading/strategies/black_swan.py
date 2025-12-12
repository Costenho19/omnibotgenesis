"""
OMNIX V7.0 Black Swan Strategy
================================
Re-export from legacy location for backward compatibility.

Original: omnix_services/trading_service/black_swan.py
Migration Status: RE-EXPORT (Phase 2 Wave 2)
"""

from omnix_services.trading_service.black_swan import (
    BlackSwanDetector,
    BlackSwanDetector as BlackSwan,
)

__all__ = ["BlackSwanDetector", "BlackSwan"]
