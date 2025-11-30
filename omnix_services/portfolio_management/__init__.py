"""
OMNIX V6.4 INSTITUTIONAL+ Portfolio Management
Enterprise-grade portfolio optimization and risk management
"""

from .institutional.risk_model_engine import RiskModelEngine
from .institutional.portfolio_optimizer import PortfolioOptimizer
from .institutional.volatility_targeting import VolatilityTargetingEngine
from .institutional.exposure_manager import ExposureManager
from .institutional.clustering_risk import ClusteringRiskDetector
from .institutional.portfolio_engine import OmnixPortfolioEngine

__all__ = [
    'RiskModelEngine',
    'PortfolioOptimizer', 
    'VolatilityTargetingEngine',
    'ExposureManager',
    'ClusteringRiskDetector',
    'OmnixPortfolioEngine'
]

__version__ = "6.4.0"
__codename__ = "INSTITUTIONAL+"
