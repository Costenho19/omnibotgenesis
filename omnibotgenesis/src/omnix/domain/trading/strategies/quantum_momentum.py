"""
OMNIX V7.0 Quantum Momentum Strategy
======================================
Re-export from legacy location for backward compatibility.

Original: omnix_services/trading_service/quantum_momentum.py
Migration Status: RE-EXPORT (Phase 2 Wave 2)
"""

from omnix_services.trading_service.quantum_momentum import (
    QuantumMomentumAnalyzer,
    QuantumMomentumAnalyzer as QuantumMomentum,
)

__all__ = ["QuantumMomentumAnalyzer", "QuantumMomentum"]
