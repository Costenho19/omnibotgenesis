"""
OMNIX V7.0 Monte Carlo Strategy
=================================
Re-export from legacy location for backward compatibility.

Original: omnix_services/trading_service/monte_carlo.py
Migration Status: RE-EXPORT (Phase 2 Wave 2)
"""

from omnix_services.trading_service.monte_carlo import (
    MonteCarloSimulator,
    MonteCarloSimulator as MonteCarlo,
)

__all__ = ["MonteCarloSimulator", "MonteCarlo"]
