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

__all__ = [
    'fetch_market_snapshot',
    'get_fear_greed_index',
    'get_btc_dominance',
    'get_free_market_metrics',
    'get_multi_exchange_prices',
    'detect_arbitrage_opportunities'
]
