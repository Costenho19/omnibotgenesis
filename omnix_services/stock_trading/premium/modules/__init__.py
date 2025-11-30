"""
📦 Stock Trading Premium Modules
Módulos avanzados para trading institucional de acciones
"""

from .monte_carlo import StockMonteCarlo, MonteCarloResult
from .kalman_filter import StockKalmanFilter, AdaptiveKalmanFilter, KalmanState
from .hmm_regime import StockHMMRegime, MarketRegime, RegimeState
from .ares_stock import ARESStock, ARESSignal, StrategyMode
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
    'ARESStock',
    'ARESSignal',
    'StrategyMode',
    'StockMemoryKernel',
    'MemoryState',
    'MemoryPattern'
]
