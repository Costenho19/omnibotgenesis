"""
Stock Trading Premium Modules
Módulos avanzados para trading institucional de acciones

Note: ARES-STOCK deprecated Dec 24, 2025 (archived to archive/deprecated_ares/)
"""

from .monte_carlo import StockMonteCarlo, MonteCarloResult
from .kalman_filter import StockKalmanFilter, AdaptiveKalmanFilter, KalmanState
from .hmm_regime import StockHMMRegime, MarketRegime, RegimeState
from .non_markovian_memory import StockMemoryKernel, MemoryState, MemoryPattern

__all__ = [
    'StockMonteCarlo',
    'MonteCarloResult',
    'StockKalmanFilter',
    'AdaptiveKalmanFilter',
    'KalmanState',
    'StockHMMRegime',
    'MarketRegime',
    'RegimeState',
    'StockMemoryKernel',
    'MemoryState',
    'MemoryPattern'
]
