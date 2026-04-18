"""
OMNIX V7.0 Trading Strategies
==============================
Strategy implementations migrated from legacy locations.

Available Strategies (V6.5.4d):
- NonMarkovianMemoryKernel (Temporal Memory)
- CAESModule (Confidence-Adaptive Entry)
- QuantumMomentumAnalyzer
- MonteCarloSimulator
- KellyCriterionOptimizer
- BlackSwanDetector
- HMMRegimeDetector
- KalmanFilterPredictor

Note: ARES V1/V2 deprecated Dec 24, 2025 (archived)
Migration Status: RE-EXPORT (Phase 2 Wave 2)
"""

try:
    from src.omnix.domain.trading.strategies.non_markovian import NonMarkovianMemoryKernel, NonMarkovianKernel
except ImportError:
    NonMarkovianMemoryKernel = None
    NonMarkovianKernel = None

try:
    from src.omnix.domain.trading.strategies.caes import CAESModule, ConfidenceAdaptiveEntrySystem
except ImportError:
    CAESModule = None
    ConfidenceAdaptiveEntrySystem = None

try:
    from src.omnix.domain.trading.strategies.quantum_momentum import QuantumMomentumAnalyzer, QuantumMomentum
except ImportError:
    QuantumMomentumAnalyzer = None
    QuantumMomentum = None

try:
    from src.omnix.domain.trading.strategies.monte_carlo import MonteCarloSimulator, MonteCarlo
except ImportError:
    MonteCarloSimulator = None
    MonteCarlo = None

try:
    from src.omnix.domain.trading.strategies.kelly import KellyCriterionOptimizer, KellyCriterion
except ImportError:
    KellyCriterionOptimizer = None
    KellyCriterion = None

try:
    from src.omnix.domain.trading.strategies.black_swan import BlackSwanDetector, BlackSwan
except ImportError:
    BlackSwanDetector = None
    BlackSwan = None

try:
    from src.omnix.domain.trading.strategies.hmm_regime import HMMRegimeDetector, HMMRegime
except ImportError:
    HMMRegimeDetector = None
    HMMRegime = None

try:
    from src.omnix.domain.trading.strategies.kalman_filter import KalmanFilterPredictor, KalmanFilter
except ImportError:
    KalmanFilterPredictor = None
    KalmanFilter = None

__all__ = [
    "NonMarkovianMemoryKernel",
    "NonMarkovianKernel",
    "CAESModule",
    "ConfidenceAdaptiveEntrySystem",
    "QuantumMomentumAnalyzer",
    "QuantumMomentum",
    "MonteCarloSimulator",
    "MonteCarlo",
    "KellyCriterionOptimizer",
    "KellyCriterion",
    "BlackSwanDetector",
    "BlackSwan",
    "HMMRegimeDetector",
    "HMMRegime",
    "KalmanFilterPredictor",
    "KalmanFilter",
]
