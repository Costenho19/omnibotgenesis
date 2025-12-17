"""
OMNIX V7.0 Market Intelligence Port
====================================
Protocol definition for market intelligence and sentiment data.

Wraps legacy services:
- FearGreedService (Alternative.me)
- AlphaVantageService (technical indicators)  
- FinnhubService (news, sentiment, earnings)

Migration Status: Phase 5 - New Ports Implementation
Feature Flag: USE_MARKET_INTEL_PORT
"""

from typing import Protocol, Optional, List, Dict, Any, runtime_checkable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SentimentLevel(Enum):
    """Market sentiment classification."""
    EXTREME_FEAR = "extreme_fear"
    FEAR = "fear"
    NEUTRAL = "neutral"
    GREED = "greed"
    EXTREME_GREED = "extreme_greed"


class IndicatorType(Enum):
    """Technical indicator types."""
    RSI = "rsi"
    MACD = "macd"
    EMA = "ema"
    SMA = "sma"
    BBANDS = "bbands"
    ADX = "adx"


class NewsCategory(Enum):
    """News category types."""
    GENERAL = "general"
    FOREX = "forex"
    CRYPTO = "crypto"
    MERGER = "merger"


@dataclass
class SentimentSnapshot:
    """Market sentiment data from Fear & Greed Index."""
    value: int
    level: SentimentLevel
    classification: str
    timestamp: datetime
    recommendation: str
    color: str = "gray"
    description: str = ""
    historical_avg_7d: Optional[float] = None
    historical_avg_30d: Optional[float] = None
    trend: str = "stable"


@dataclass
class TechnicalIndicator:
    """Technical indicator value from Alpha Vantage."""
    symbol: str
    indicator_type: IndicatorType
    value: float
    date: str
    interpretation: str
    signal: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NewsArticle:
    """News article from Finnhub."""
    headline: str
    summary: str
    source: str
    url: str
    published_at: datetime
    category: NewsCategory
    related_symbols: List[str] = field(default_factory=list)
    sentiment_score: Optional[float] = None


@dataclass
class MacroEvent:
    """Macro economic event from calendar."""
    event_name: str
    country: str
    impact: str
    estimate: Optional[float] = None
    actual: Optional[float] = None
    previous: Optional[float] = None
    scheduled_at: Optional[datetime] = None


@dataclass
class EarningsEvent:
    """Earnings calendar event."""
    symbol: str
    company_name: str
    earnings_date: datetime
    eps_estimate: Optional[float] = None
    eps_actual: Optional[float] = None
    revenue_estimate: Optional[float] = None
    revenue_actual: Optional[float] = None
    quarter: str = ""


@dataclass
class MarketIntelRequest:
    """Request DTO for market intelligence queries."""
    symbols: List[str] = field(default_factory=list)
    include_sentiment: bool = True
    include_news: bool = True
    include_indicators: bool = True
    include_earnings: bool = False
    news_days: int = 7
    indicator_interval: str = "daily"


@dataclass
class MarketIntelResponse:
    """Response DTO with aggregated market intelligence."""
    sentiment: Optional[SentimentSnapshot] = None
    indicators: List[TechnicalIndicator] = field(default_factory=list)
    news: List[NewsArticle] = field(default_factory=list)
    earnings: List[EarningsEvent] = field(default_factory=list)
    macro_events: List[MacroEvent] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None
    providers_used: List[str] = field(default_factory=list)


@runtime_checkable
class MarketIntelPort(Protocol):
    """
    Protocol for market intelligence and sentiment data.
    
    Aggregates data from:
    - Alternative.me (Fear & Greed Index)
    - Alpha Vantage (Technical Indicators)
    - Finnhub (News, Earnings, Sentiment)
    
    SOLID Principles:
    - SRP: Only market intelligence aggregation
    - ISP: Focused interface for sentiment/indicators
    - DIP: High-level code depends on this abstraction
    
    Feature Flag: USE_MARKET_INTEL_PORT
    Fallback: Direct service calls to legacy modules
    """
    
    def get_sentiment_snapshot(self) -> Optional[SentimentSnapshot]:
        """
        Get current Fear & Greed Index snapshot.
        
        Returns:
            SentimentSnapshot with current market sentiment
            None if service unavailable
        """
        ...
    
    def get_sentiment_history(self, days: int = 30) -> List[SentimentSnapshot]:
        """
        Get historical Fear & Greed Index data.
        
        Args:
            days: Number of days of history
            
        Returns:
            List of SentimentSnapshot for each day
        """
        ...
    
    def get_technical_indicator(
        self,
        symbol: str,
        indicator: IndicatorType,
        interval: str = "daily"
    ) -> Optional[TechnicalIndicator]:
        """
        Get technical indicator value from Alpha Vantage.
        
        Args:
            symbol: Stock ticker or crypto symbol
            indicator: Type of indicator (RSI, MACD, etc.)
            interval: Time interval (1min, 5min, daily, weekly)
            
        Returns:
            TechnicalIndicator with value and interpretation
        """
        ...
    
    def get_multiple_indicators(
        self,
        symbol: str,
        indicators: List[IndicatorType],
        interval: str = "daily"
    ) -> List[TechnicalIndicator]:
        """
        Get multiple technical indicators for a symbol.
        
        Args:
            symbol: Stock ticker or crypto symbol
            indicators: List of indicator types
            interval: Time interval
            
        Returns:
            List of TechnicalIndicator results
        """
        ...
    
    def get_company_news(
        self,
        symbol: str,
        days: int = 7
    ) -> List[NewsArticle]:
        """
        Get recent news for a specific company/crypto.
        
        Args:
            symbol: Stock ticker or crypto symbol
            days: Number of days to look back
            
        Returns:
            List of NewsArticle with headlines and sentiment
        """
        ...
    
    def get_general_news(
        self,
        category: NewsCategory = NewsCategory.GENERAL
    ) -> List[NewsArticle]:
        """
        Get general market news.
        
        Args:
            category: News category filter
            
        Returns:
            List of NewsArticle
        """
        ...
    
    def get_earnings_calendar(
        self,
        symbols: Optional[List[str]] = None,
        days_ahead: int = 7
    ) -> List[EarningsEvent]:
        """
        Get upcoming earnings events.
        
        Args:
            symbols: Filter by symbols (None for all)
            days_ahead: Days to look ahead
            
        Returns:
            List of EarningsEvent
        """
        ...
    
    def refresh_macro_calendar(self) -> List[MacroEvent]:
        """
        Refresh economic calendar events.
        
        Returns:
            List of upcoming MacroEvent
        """
        ...
    
    def get_aggregated_intel(
        self,
        request: MarketIntelRequest
    ) -> MarketIntelResponse:
        """
        Get aggregated market intelligence.
        
        Args:
            request: MarketIntelRequest with configuration
            
        Returns:
            MarketIntelResponse with all requested data
        """
        ...
    
    def is_provider_available(self, provider: str) -> bool:
        """
        Check if a specific data provider is available.
        
        Args:
            provider: Provider name (fear_greed, alpha_vantage, finnhub)
            
        Returns:
            True if provider is configured and accessible
        """
        ...
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of market intelligence services.
        
        Returns:
            Dict with:
            - healthy: bool
            - providers: Dict[str, bool] (availability per provider)
            - cache_status: Dict with cache metrics
            - last_update: datetime
        """
        ...
