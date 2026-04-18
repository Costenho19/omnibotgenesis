"""
OMNIX V7.0 CAES Strategy (Confidence-Adaptive Entry System)
=============================================================
Re-export from legacy location for backward compatibility.

Original: omnix_core/strategies/caes_module.py
Migration Status: RE-EXPORT (Phase 2 Wave 2)
"""

from omnix_core.strategies.caes_module import (
    CAESModule,
    CAESModule as ConfidenceAdaptiveEntrySystem,
)

__all__ = ["CAESModule", "ConfidenceAdaptiveEntrySystem"]
