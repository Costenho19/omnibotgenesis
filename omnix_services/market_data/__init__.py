"""
OMNIX Market Data Service
Real-time market data, sentiment analysis, and arbitrage detection
"""

from .kraken_data import fetch_market_snapshot
from .sentiment_data import (
    get_fear_greed_index,
    get_btc_dominance,
    get_free_market_metrics
)
from .arbitrage import (
    get_multi_exchange_prices,
    detect_arbitrage_opportunities
)
from .analysis_helpers import (
    analyze_volume_patterns,
    get_external_market_factors,
    analyze_historical_patterns,
    generate_predictive_insights,
    calculate_confidence_score
)

__all__ = [
    'fetch_market_snapshot',
    'get_fear_greed_index',
    'get_btc_dominance',
    'get_free_market_metrics',
    'get_multi_exchange_prices',
    'detect_arbitrage_opportunities',
    'analyze_volume_patterns',
    'get_external_market_factors',
    'analyze_historical_patterns',
    'generate_predictive_insights',
    'calculate_confidence_score'
]
