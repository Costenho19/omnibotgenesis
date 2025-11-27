"""
OMNIX V6.0 ULTRA - Quantum Enhancements Package
Exports QRNG and QAOA for Monte Carlo and Portfolio Optimization
"""

from omnix_core.quantum.enhancements import (
    global_qrng,
    global_qaoa,
    get_quantum_random,
    optimize_portfolio_quantum,
    get_quantum_stats,
    QuantumRandomNumberGenerator,
    QuantumPortfolioOptimizer
)

__all__ = [
    'global_qrng',
    'global_qaoa',
    'get_quantum_random',
    'optimize_portfolio_quantum',
    'get_quantum_stats',
    'QuantumRandomNumberGenerator',
    'QuantumPortfolioOptimizer'
]
