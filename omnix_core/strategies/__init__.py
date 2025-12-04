"""
OMNIX Strategies Package - Institutional Trading Strategies

Available Strategies:
- AresProtocolV1: Swing Trading Strategy (55-65% win rate)
- AresProtocolV2: Scalping M1 Strategy (60-70% win rate)
- NonMarkovianKernel: Temporal Memory for Regime Detection
"""

from .ares_v1 import AresProtocolV1
from .ares_v2 import AresProtocolV2
from .non_markovian_kernel import NonMarkovianKernel

__all__ = [
    'AresProtocolV1',
    'AresProtocolV2',
    'NonMarkovianKernel'
]
