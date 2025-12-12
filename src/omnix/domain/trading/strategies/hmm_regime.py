"""
OMNIX V7.0 HMM Regime Strategy
================================
Re-export from legacy location for backward compatibility.

Original: omnix_services/trading_service/hmm_regime.py
Migration Status: RE-EXPORT (Phase 2 Wave 2)
"""

from omnix_services.trading_service.hmm_regime import (
    HMMRegimeDetector,
    HMMRegimeDetector as HMMRegime,
)

__all__ = ["HMMRegimeDetector", "HMMRegime"]
