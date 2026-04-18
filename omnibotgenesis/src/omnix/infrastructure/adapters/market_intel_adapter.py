"""
OMNIX V7.0 Market Intelligence Adapter
=======================================
Bridges V7 Hexagonal Architecture with Legacy Market Intelligence services.

ARCHITECTURE DECISION (Dec 17, 2025):
This adapter is a PURE BRIDGE that delegates to legacy services:
- FearGreedService (Alternative.me API)
- AlphaVantageService (technical indicators)
- FinnhubService (news, earnings, sentiment)

The adapter ONLY translates between:
- V7 MarketIntelPort DTOs ↔ Legacy service responses

This follows the Strangler Fig pattern: new interface wraps legacy implementation.
Feature Flag: USE_MARKET_INTEL_PORT
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.omnix.ports.driven.market_intel_port import (
    MarketIntelPort,
    SentimentSnapshot,
    SentimentLevel,
    TechnicalIndicator,
    IndicatorType,
    NewsArticle,
    NewsCategory,
    MacroEvent,
    EarningsEvent,
    MarketIntelRequest,
    MarketIntelResponse,
)

logger = logging.getLogger(__name__)


class MarketIntelAdapter:
    """
    Adapter that implements MarketIntelPort.
    
    DELEGATES to legacy market intelligence services for actual data.
    This ensures USE_MARKET_INTEL_PORT=true uses the same proven services
    as the legacy system.
    
    Translation:
    - V7 DTOs ↔ Legacy service responses
    """
    
    def __init__(
        self,
        fear_greed_service: Optional[Any] = None,
        alpha_vantage_service: Optional[Any] = None,
        finnhub_service: Optional[Any] = None,
    ):
        """
        Initialize the Market Intelligence Adapter.
        
        Args:
            fear_greed_service: Legacy FearGreedService instance
            alpha_vantage_service: Legacy AlphaVantageService instance
            finnhub_service: Legacy FinnhubService instance
        """
        self._fear_greed = fear_greed_service
        self._alpha_vantage = alpha_vantage_service
        self._finnhub = finnhub_service
        
        self._request_count = 0
        self._error_count = 0
        self._last_request: Optional[datetime] = None
        self._initialized = False
    
    def _ensure_services(self) -> bool:
        """Lazy initialize services if not injected."""
        if self._initialized:
            return True
        
        try:
            if self._fear_greed is None:
                from omnix_services.market_intelligence.fear_greed_service import FearGreedService
                self._fear_greed = FearGreedService()
                logger.info("MarketIntelAdapter: Initialized FearGreedService")
            
            if self._alpha_vantage is None:
                from omnix_services.market_intelligence.alpha_vantage_service import AlphaVantageService
                self._alpha_vantage = AlphaVantageService()
                logger.info("MarketIntelAdapter: Initialized AlphaVantageService")
            
            if self._finnhub is None:
                from omnix_services.market_intelligence.finnhub_service import FinnhubService
                self._finnhub = FinnhubService()
                logger.info("MarketIntelAdapter: Initialized FinnhubService")
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"MarketIntelAdapter: Failed to initialize services: {e}")
            return False
    
    def _map_sentiment_level(self, value: int) -> SentimentLevel:
        """Map numeric value to SentimentLevel enum."""
        if value <= 24:
            return SentimentLevel.EXTREME_FEAR
        elif value <= 49:
            return SentimentLevel.FEAR
        elif value == 50:
            return SentimentLevel.NEUTRAL
        elif value <= 75:
            return SentimentLevel.GREED
        else:
            return SentimentLevel.EXTREME_GREED
    
    def _map_indicator_type(self, indicator_name: str) -> IndicatorType:
        """Map string indicator name to IndicatorType enum."""
        mapping = {
            'rsi': IndicatorType.RSI,
            'macd': IndicatorType.MACD,
            'ema': IndicatorType.EMA,
            'sma': IndicatorType.SMA,
            'bbands': IndicatorType.BBANDS,
            'adx': IndicatorType.ADX,
        }
        return mapping.get(indicator_name.lower(), IndicatorType.RSI)
    
    def _map_news_category(self, category: str) -> NewsCategory:
        """Map string category to NewsCategory enum."""
        mapping = {
            'general': NewsCategory.GENERAL,
            'forex': NewsCategory.FOREX,
            'crypto': NewsCategory.CRYPTO,
            'merger': NewsCategory.MERGER,
        }
        return mapping.get(category.lower(), NewsCategory.GENERAL)
    
    def get_sentiment_snapshot(self) -> Optional[SentimentSnapshot]:
        """Get current Fear & Greed Index snapshot."""
        self._request_count += 1
        self._last_request = datetime.now()
        
        if not self._ensure_services():
            self._error_count += 1
            return None
        
        try:
            data = self._fear_greed.get_current_index()
            if not data:
                return None
            
            return SentimentSnapshot(
                value=data.get('value', 50),
                level=self._map_sentiment_level(data.get('value', 50)),
                classification=data.get('classification', 'Neutral'),
                timestamp=data.get('timestamp', datetime.now()),
                recommendation=data.get('recommendation', 'Hold'),
                color=data.get('color', 'gray'),
                description=data.get('description', ''),
                trend='stable'
            )
        except Exception as e:
            logger.error(f"MarketIntelAdapter: Error getting sentiment: {e}")
            self._error_count += 1
            return None
    
    def get_sentiment_history(self, days: int = 30) -> List[SentimentSnapshot]:
        """Get historical Fear & Greed Index data."""
        self._request_count += 1
        self._last_request = datetime.now()
        
        if not self._ensure_services():
            self._error_count += 1
            return []
        
        try:
            history = self._fear_greed.get_historical(days)
            if not history:
                return []
            
            return [
                SentimentSnapshot(
                    value=item.get('value', 50),
                    level=self._map_sentiment_level(item.get('value', 50)),
                    classification=item.get('classification', 'Neutral'),
                    timestamp=item.get('date', datetime.now()),
                    recommendation='',
                    trend='stable'
                )
                for item in history
            ]
        except Exception as e:
            logger.error(f"MarketIntelAdapter: Error getting sentiment history: {e}")
            self._error_count += 1
            return []
    
    def get_technical_indicator(
        self,
        symbol: str,
        indicator: IndicatorType,
        interval: str = "daily"
    ) -> Optional[TechnicalIndicator]:
        """Get technical indicator value from Alpha Vantage."""
        self._request_count += 1
        self._last_request = datetime.now()
        
        if not self._ensure_services():
            self._error_count += 1
            return None
        
        if not self._alpha_vantage.is_available():
            logger.warning("MarketIntelAdapter: Alpha Vantage not configured")
            return None
        
        try:
            data = None
            if indicator == IndicatorType.RSI:
                data = self._alpha_vantage.get_rsi(symbol, interval)
            elif indicator == IndicatorType.MACD:
                data = self._alpha_vantage.get_macd(symbol, interval)
            elif indicator == IndicatorType.EMA:
                data = self._alpha_vantage.get_ema(symbol, interval)
            elif indicator == IndicatorType.SMA:
                data = self._alpha_vantage.get_sma(symbol, interval)
            elif indicator == IndicatorType.BBANDS:
                data = self._alpha_vantage.get_bbands(symbol, interval)
            elif indicator == IndicatorType.ADX:
                data = self._alpha_vantage.get_adx(symbol, interval)
            
            if not data:
                return None
            
            return TechnicalIndicator(
                symbol=symbol,
                indicator_type=indicator,
                value=data.get('value', 0.0),
                date=data.get('date', ''),
                interpretation=data.get('interpretation', ''),
                signal=data.get('signal', 'neutral'),
                metadata=data
            )
        except Exception as e:
            logger.error(f"MarketIntelAdapter: Error getting {indicator.value} for {symbol}: {e}")
            self._error_count += 1
            return None
    
    def get_multiple_indicators(
        self,
        symbol: str,
        indicators: List[IndicatorType],
        interval: str = "daily"
    ) -> List[TechnicalIndicator]:
        """Get multiple technical indicators for a symbol."""
        results = []
        for indicator in indicators:
            result = self.get_technical_indicator(symbol, indicator, interval)
            if result:
                results.append(result)
        return results
    
    def get_company_news(
        self,
        symbol: str,
        days: int = 7
    ) -> List[NewsArticle]:
        """Get recent news for a specific company/crypto."""
        self._request_count += 1
        self._last_request = datetime.now()
        
        if not self._ensure_services():
            self._error_count += 1
            return []
        
        if not self._finnhub.is_available():
            logger.warning("MarketIntelAdapter: Finnhub not configured")
            return []
        
        try:
            news = self._finnhub.get_company_news(symbol, days)
            if not news:
                return []
            
            return [
                NewsArticle(
                    headline=item.get('headline', ''),
                    summary=item.get('summary', ''),
                    source=item.get('source', ''),
                    url=item.get('url', ''),
                    published_at=item.get('datetime', datetime.now()),
                    category=self._map_news_category(item.get('category', 'general')),
                    related_symbols=[item.get('related', symbol)],
                )
                for item in news
            ]
        except Exception as e:
            logger.error(f"MarketIntelAdapter: Error getting news for {symbol}: {e}")
            self._error_count += 1
            return []
    
    def get_general_news(
        self,
        category: NewsCategory = NewsCategory.GENERAL
    ) -> List[NewsArticle]:
        """Get general market news."""
        self._request_count += 1
        self._last_request = datetime.now()
        
        if not self._ensure_services():
            self._error_count += 1
            return []
        
        if not self._finnhub.is_available():
            return []
        
        try:
            news = self._finnhub.get_general_news(category.value)
            if not news:
                return []
            
            return [
                NewsArticle(
                    headline=item.get('headline', ''),
                    summary=item.get('summary', ''),
                    source=item.get('source', ''),
                    url=item.get('url', ''),
                    published_at=item.get('datetime', datetime.now()),
                    category=category,
                    related_symbols=[],
                )
                for item in news
            ]
        except Exception as e:
            logger.error(f"MarketIntelAdapter: Error getting general news: {e}")
            self._error_count += 1
            return []
    
    def get_earnings_calendar(
        self,
        symbols: Optional[List[str]] = None,
        days_ahead: int = 7
    ) -> List[EarningsEvent]:
        """Get upcoming earnings events."""
        self._request_count += 1
        self._last_request = datetime.now()
        
        if not self._ensure_services():
            self._error_count += 1
            return []
        
        if not self._finnhub.is_available():
            return []
        
        try:
            earnings = self._finnhub.get_earnings_calendar(symbols, days_ahead)
            if not earnings:
                return []
            
            return [
                EarningsEvent(
                    symbol=item.get('symbol', ''),
                    company_name=item.get('company', ''),
                    earnings_date=item.get('date', datetime.now()),
                    eps_estimate=item.get('eps_estimate'),
                    eps_actual=item.get('eps_actual'),
                    revenue_estimate=item.get('revenue_estimate'),
                    revenue_actual=item.get('revenue_actual'),
                    quarter=item.get('quarter', '')
                )
                for item in earnings
            ]
        except Exception as e:
            logger.error(f"MarketIntelAdapter: Error getting earnings calendar: {e}")
            self._error_count += 1
            return []
    
    def refresh_macro_calendar(self) -> List[MacroEvent]:
        """Refresh economic calendar events."""
        self._request_count += 1
        self._last_request = datetime.now()
        
        if not self._ensure_services():
            self._error_count += 1
            return []
        
        if not self._finnhub.is_available():
            return []
        
        try:
            events = self._finnhub.get_economic_calendar()
            if not events:
                return []
            
            return [
                MacroEvent(
                    event_name=item.get('event', ''),
                    country=item.get('country', ''),
                    impact=item.get('impact', 'low'),
                    estimate=item.get('estimate'),
                    actual=item.get('actual'),
                    previous=item.get('previous'),
                    scheduled_at=item.get('time'),
                )
                for item in events
            ]
        except Exception as e:
            logger.error(f"MarketIntelAdapter: Error getting macro calendar: {e}")
            self._error_count += 1
            return []
    
    def get_aggregated_intel(
        self,
        request: MarketIntelRequest
    ) -> MarketIntelResponse:
        """Get aggregated market intelligence."""
        self._request_count += 1
        self._last_request = datetime.now()
        
        providers_used = []
        sentiment = None
        indicators = []
        news = []
        earnings = []
        
        if request.include_sentiment:
            sentiment = self.get_sentiment_snapshot()
            if sentiment:
                providers_used.append('fear_greed')
        
        if request.include_indicators and request.symbols:
            for symbol in request.symbols:
                for ind_type in [IndicatorType.RSI, IndicatorType.MACD]:
                    result = self.get_technical_indicator(
                        symbol, ind_type, request.indicator_interval
                    )
                    if result:
                        indicators.append(result)
                        if 'alpha_vantage' not in providers_used:
                            providers_used.append('alpha_vantage')
        
        if request.include_news and request.symbols:
            for symbol in request.symbols:
                symbol_news = self.get_company_news(symbol, request.news_days)
                news.extend(symbol_news)
                if symbol_news and 'finnhub' not in providers_used:
                    providers_used.append('finnhub')
        
        if request.include_earnings and request.symbols:
            earnings = self.get_earnings_calendar(request.symbols)
            if earnings and 'finnhub' not in providers_used:
                providers_used.append('finnhub')
        
        return MarketIntelResponse(
            sentiment=sentiment,
            indicators=indicators,
            news=news[:50],
            earnings=earnings,
            macro_events=[],
            timestamp=datetime.now(),
            success=True,
            providers_used=providers_used
        )
    
    def is_provider_available(self, provider: str) -> bool:
        """Check if a specific data provider is available."""
        if not self._ensure_services():
            return False
        
        if provider == 'fear_greed':
            return self._fear_greed is not None
        elif provider == 'alpha_vantage':
            return self._alpha_vantage is not None and self._alpha_vantage.is_available()
        elif provider == 'finnhub':
            return self._finnhub is not None and self._finnhub.is_available()
        
        return False
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of market intelligence services."""
        providers = {}
        
        if self._ensure_services():
            providers['fear_greed'] = self._fear_greed is not None
            providers['alpha_vantage'] = (
                self._alpha_vantage is not None and 
                self._alpha_vantage.is_available()
            )
            providers['finnhub'] = (
                self._finnhub is not None and 
                self._finnhub.is_available()
            )
        
        healthy = any(providers.values())
        
        return {
            'healthy': healthy,
            'adapter': 'MarketIntelAdapter',
            'providers': providers,
            'request_count': self._request_count,
            'error_count': self._error_count,
            'last_request': self._last_request.isoformat() if self._last_request else None,
            'cache_status': {
                'fear_greed_cached': hasattr(self._fear_greed, '_cache') and bool(self._fear_greed._cache) if self._fear_greed else False,
            }
        }
