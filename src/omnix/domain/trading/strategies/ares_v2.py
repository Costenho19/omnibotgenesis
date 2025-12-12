"""
OMNIX V7.0 ARES V2 Strategy (Scalping)
=======================================
Re-export from legacy location for backward compatibility.

Original: omnix_core/strategies/ares_v2.py
Migration Status: RE-EXPORT (Phase 2 Wave 2)
"""

from omnix_core.strategies.ares_v2 import (
    ARESProtocolV2,
    ARESProtocolV2 as AresV2Strategy,
)

__all__ = ["ARESProtocolV2", "AresV2Strategy"]
