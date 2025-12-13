"""
OMNIX Services Package - Enterprise Service Layer

Available Subpackages:
- adaptive_engine: Auto-calibration for market regimes
- ai_service: AI models (Gemini, GPT-4, Claude)
- analytics: Chart pattern analysis
- coherence_service: 6-Tier veto system
- community_intelligence: Multi-user collaboration
- concurrency: Resource management
- database_service: PostgreSQL pooling
- derivatives: Futures and margin trading
- market_data: Real-time market intelligence
- market_intelligence: Fear & Greed, Finnhub
- monitoring: Risk Guardian, metrics
- notifications: Trade alerts, daily summary
- optimization: Auto-optimizer, ML modules
- portfolio_management: Markowitz, Black-Litterman
- risk_management: Limits, alerts, circuit breaker
- stock_trading: Alpaca integration
- telegram_service: Enterprise bot
- trading_service: Kraken, paper trading
- user_settings: User preferences
- voice_service: Voice commands
- web_search_service: Tavily web search integration

Root Modules:
- news_scraper: Crypto news aggregation
- symbol_classifier: Crypto/stock detection

Removed in V7.0 Phase 4.10 (Dec 13, 2025):
- alerts: Smart alert engine (0 imports - dormant)
- on_chain_service: Blockchain analytics (0 imports - dormant)
"""

from .news_scraper import NewsScraperService
from .symbol_classifier import SymbolClassifier

__all__ = [
    'NewsScraperService',
    'SymbolClassifier'
]
