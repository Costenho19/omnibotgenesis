"""
OMNIX Execution Protocol V6.5.4 INSTITUTIONAL+
Institutional-grade execution analysis and optimization

Components:
- LiquidityAnalyzer: True Bid Liquidity Recovery, Order Book Depth, Hidden Liquidity
- MicroVolatilityEngine: Tick volatility clustering, regime detection, asymmetric response
- CrossAssetCorrelationEngine: Correlation breakdown, contagion risk, safe-haven flows
- ExecutionProtocol: Main orchestrator with execution decision matrix
"""

from omnix_config import VERSION_BANNER

try:
    from .liquidity_analyzer import LiquidityAnalyzer
    LIQUIDITY_ANALYZER_AVAILABLE = True
except ImportError:
    LiquidityAnalyzer = None
    LIQUIDITY_ANALYZER_AVAILABLE = False

try:
    from .micro_volatility import MicroVolatilityEngine
    MICRO_VOLATILITY_AVAILABLE = True
except ImportError:
    MicroVolatilityEngine = None
    MICRO_VOLATILITY_AVAILABLE = False

try:
    from .correlation_engine import CrossAssetCorrelationEngine
    CORRELATION_ENGINE_AVAILABLE = True
except ImportError:
    CrossAssetCorrelationEngine = None
    CORRELATION_ENGINE_AVAILABLE = False

try:
    from .execution_protocol import ExecutionProtocol, ExecutionDecision
    EXECUTION_PROTOCOL_AVAILABLE = True
except ImportError:
    ExecutionProtocol = None
    ExecutionDecision = None
    EXECUTION_PROTOCOL_AVAILABLE = False

EXECUTION_SERVICE_AVAILABLE = LIQUIDITY_ANALYZER_AVAILABLE

__all__ = [
    'LiquidityAnalyzer',
    'MicroVolatilityEngine', 
    'CrossAssetCorrelationEngine',
    'ExecutionProtocol',
    'ExecutionDecision',
    'EXECUTION_SERVICE_AVAILABLE'
]
