"""
OMNIX Execution Protocol INSTITUTIONAL+
Institutional-grade execution analysis and optimization

Components:
- LiquidityAnalyzer: True Bid Liquidity Recovery, Order Book Depth, Hidden Liquidity
- MicroVolatilityEngine: Tick volatility clustering, regime detection, asymmetric response
- CrossAssetCorrelationEngine: Correlation breakdown, contagion risk, safe-haven flows
- ExecutionProtocol: Main orchestrator with execution decision matrix
"""

import logging
from omnix_config import VERSION_BANNER

logger = logging.getLogger(__name__)

LIQUIDITY_AVAILABLE = False
MICRO_VOLATILITY_AVAILABLE = False
CORRELATION_AVAILABLE = False
EXECUTION_PROTOCOL_AVAILABLE = False

LiquidityAnalyzer = None
MicroVolatilityEngine = None
CrossAssetCorrelationEngine = None
ExecutionProtocol = None
ExecutionDecision = None

try:
    from .liquidity_analyzer import LiquidityAnalyzer
    LIQUIDITY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LiquidityAnalyzer not available: {e}")

try:
    from .micro_volatility import MicroVolatilityEngine
    MICRO_VOLATILITY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"MicroVolatilityEngine not available: {e}")

try:
    from .correlation_engine import CrossAssetCorrelationEngine
    CORRELATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"CrossAssetCorrelationEngine not available: {e}")

try:
    from .execution_protocol import ExecutionProtocol, ExecutionDecision, ExecutionUrgency
    EXECUTION_PROTOCOL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ExecutionProtocol not available: {e}")
    ExecutionUrgency = None

EXECUTION_SERVICE_AVAILABLE = (
    LIQUIDITY_AVAILABLE or 
    MICRO_VOLATILITY_AVAILABLE or 
    CORRELATION_AVAILABLE or
    EXECUTION_PROTOCOL_AVAILABLE
)

if EXECUTION_SERVICE_AVAILABLE:
    logger.info(f"[{VERSION_BANNER}] Execution Service INSTITUTIONAL+ loaded")
    logger.info(f"   Liquidity: {'✅' if LIQUIDITY_AVAILABLE else '❌'}")
    logger.info(f"   Volatility: {'✅' if MICRO_VOLATILITY_AVAILABLE else '❌'}")
    logger.info(f"   Correlation: {'✅' if CORRELATION_AVAILABLE else '❌'}")
    logger.info(f"   Protocol: {'✅' if EXECUTION_PROTOCOL_AVAILABLE else '❌'}")

__all__ = [
    'LiquidityAnalyzer',
    'MicroVolatilityEngine', 
    'CrossAssetCorrelationEngine',
    'ExecutionProtocol',
    'ExecutionDecision',
    'ExecutionUrgency',
    'EXECUTION_SERVICE_AVAILABLE',
    'LIQUIDITY_AVAILABLE',
    'MICRO_VOLATILITY_AVAILABLE',
    'CORRELATION_AVAILABLE',
    'EXECUTION_PROTOCOL_AVAILABLE'
]
