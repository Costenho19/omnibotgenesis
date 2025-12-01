"""
OMNIX On-Chain Data Intelligence Service V6.5
==============================================

Integración de datos on-chain para señales adelantadas:
- Whale transaction tracking (ClankApp, Arkham)
- Exchange flow analysis (in/out flows)
- Network health metrics (active addresses, gas, volume)
- Smart money tracking

Fuentes de datos GRATUITAS:
- ClankApp: 24 blockchains, whale transactions
- Arkham Intelligence: Whale identity, portfolios
- DeBank: DeFi portfolios, smart money
"""

from .models import (
    WhaleTransaction,
    ExchangeFlow,
    NetworkMetrics,
    SmartMoneySignal,
    OnChainSignal,
    FlowDirection,
    TransactionType,
    MarketBias,
    SignalStrength
)

from .on_chain_service import (
    OnChainDataService,
    get_on_chain_service,
    set_kernel_instance
)

from .whale_tracker import WhaleTracker
from .exchange_flow_analyzer import ExchangeFlowAnalyzer
from .network_metrics import NetworkMetricsCollector

__all__ = [
    'OnChainDataService',
    'get_on_chain_service',
    'set_kernel_instance',
    'WhaleTracker',
    'ExchangeFlowAnalyzer',
    'NetworkMetricsCollector',
    'WhaleTransaction',
    'ExchangeFlow',
    'NetworkMetrics',
    'SmartMoneySignal',
    'OnChainSignal',
    'FlowDirection',
    'TransactionType',
    'MarketBias',
    'SignalStrength'
]

__version__ = '6.5.0'
