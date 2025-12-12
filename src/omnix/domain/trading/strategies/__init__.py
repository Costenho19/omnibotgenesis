"""
OMNIX V7.0 Trading Strategies
==============================
Strategy implementations migrated from legacy locations.

All strategies are re-exported from their original locations for
backward compatibility during migration. Once migration is complete,
implementations will be moved here.

Available Strategies:
- ARESProtocolV1 (Swing Trading)
- ARESProtocolV2 (Scalping)
- NonMarkovianMemoryKernel (Temporal Memory)
- CAESModule (Confidence-Adaptive Entry)
- QuantumMomentumAnalyzer
- MonteCarloSimulator
- KellyCriterionOptimizer
- BlackSwanDetector
- HMMRegimeDetector
- KalmanFilterPredictor

Migration Status: RE-EXPORT (Phase 2 Wave 2)
"""

try:
    from src.omnix.domain.trading.strategies.ares_v1 import ARESProtocolV1, AresV1Strategy
except ImportError:
    ARESProtocolV1 = None
    AresV1Strategy = None

try:
    from src.omnix.domain.trading.strategies.ares_v2 import ARESProtocolV2, AresV2Strategy
except ImportError:
    ARESProtocolV2 = None
    AresV2Strategy = None

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
    "ARESProtocolV1",
    "AresV1Strategy",
    "ARESProtocolV2",
    "AresV2Strategy",
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
