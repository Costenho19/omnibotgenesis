"""
OMNIX Strategies Package - Institutional Trading Strategies V6.5.4d

Available Strategies:
- NonMarkovianKernel: Temporal Memory for Regime Detection
- EMARegimeSignal: Primary driver (40 pts)

Note: ARES V1/V2 deprecated Dec 24, 2025 (archived to archive/deprecated_ares/)
"""

from .non_markovian_kernel import NonMarkovianKernel

__all__ = [
    'NonMarkovianKernel'
]
