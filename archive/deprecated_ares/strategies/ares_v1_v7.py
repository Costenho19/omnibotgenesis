"""
OMNIX V7.0 ARES V1 Strategy (Swing Trading)
=============================================
Re-export from legacy location for backward compatibility.

Original: omnix_core/strategies/ares_v1.py
Migration Status: RE-EXPORT (Phase 2 Wave 2)

This file serves as a bridge during migration. Once migration is complete,
the implementation will be moved here and the legacy location will re-export from here.
"""

from omnix_core.strategies.ares_v1 import (
    ARESProtocolV1,
    ARESProtocolV1 as AresV1Strategy,
)

__all__ = ["ARESProtocolV1", "AresV1Strategy"]
