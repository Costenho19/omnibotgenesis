"""
OMNIX V5.3 ULTRA - Coherence Service
Sistema de validación de coherencia entre estrategias de trading
"""

from .coherence_engine import (
    CoherenceEngine,
    CoherenceReport,
    StrategySignal,
    Signal,
    CoherenceLevel
)

__all__ = [
    'CoherenceEngine',
    'CoherenceReport',
    'StrategySignal',
    'Signal',
    'CoherenceLevel'
]
