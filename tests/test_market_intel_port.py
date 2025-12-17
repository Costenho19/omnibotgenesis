"""
OMNIX V7.0 - MarketIntelPort Tests
===================================
Unit and integration tests for MarketIntelPort and MarketIntelAdapter.

Test Categories:
1. Unit tests with mocked services
2. DTO construction tests
3. Health check tests
4. Integration tests (when services available)
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

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
from src.omnix.infrastructure.adapters.market_intel_adapter import MarketIntelAdapter


class TestSentimentDTOs:
    """Test SentimentSnapshot and related DTOs."""
    
    def test_sentiment_snapshot_creation(self):
        """Test SentimentSnapshot dataclass creation."""
        snapshot = SentimentSnapshot(
            value=25,
            level=SentimentLevel.FEAR,
            classification="Fear",
            timestamp=datetime.now(),
            recommendation="Consider buying",
            color="orange",
            description="Market is fearful"
        )
        
        assert snapshot.value == 25
        assert snapshot.level == SentimentLevel.FEAR
        assert snapshot.classification == "Fear"
    
    def test_sentiment_levels(self):
        """Test all SentimentLevel enum values."""
        assert SentimentLevel.EXTREME_FEAR.value == "extreme_fear"
        assert SentimentLevel.FEAR.value == "fear"
        assert SentimentLevel.NEUTRAL.value == "neutral"
        assert SentimentLevel.GREED.value == "greed"
        assert SentimentLevel.EXTREME_GREED.value == "extreme_greed"


class TestTechnicalIndicatorDTOs:
    """Test TechnicalIndicator DTOs."""
    
    def test_technical_indicator_creation(self):
        """Test TechnicalIndicator dataclass creation."""
        indicator = TechnicalIndicator(
            symbol="BTC",
            indicator_type=IndicatorType.RSI,
            value=65.5,
            date="2025-12-17",
            interpretation="Slightly overbought",
            signal="neutral"
        )
        
        assert indicator.symbol == "BTC"
        assert indicator.indicator_type == IndicatorType.RSI
        assert indicator.value == 65.5
    
    def test_indicator_types(self):
        """Test all IndicatorType enum values."""
        assert IndicatorType.RSI.value == "rsi"
        assert IndicatorType.MACD.value == "macd"
        assert IndicatorType.EMA.value == "ema"
        assert IndicatorType.SMA.value == "sma"
        assert IndicatorType.BBANDS.value == "bbands"
        assert IndicatorType.ADX.value == "adx"


class TestNewsDTOs:
    """Test NewsArticle and related DTOs."""
    
    def test_news_article_creation(self):
        """Test NewsArticle dataclass creation."""
        article = NewsArticle(
            headline="Bitcoin reaches new high",
            summary="Bitcoin has reached a new all-time high...",
            source="CryptoNews",
            url="https://example.com/news/1",
            published_at=datetime.now(),
            category=NewsCategory.CRYPTO,
            related_symbols=["BTC", "ETH"]
        )
        
        assert article.headline == "Bitcoin reaches new high"
        assert article.category == NewsCategory.CRYPTO
        assert "BTC" in article.related_symbols
    
    def test_news_categories(self):
        """Test all NewsCategory enum values."""
        assert NewsCategory.GENERAL.value == "general"
        assert NewsCategory.FOREX.value == "forex"
        assert NewsCategory.CRYPTO.value == "crypto"
        assert NewsCategory.MERGER.value == "merger"


class TestMarketIntelRequest:
    """Test MarketIntelRequest DTO."""
    
    def test_request_defaults(self):
        """Test MarketIntelRequest default values."""
        request = MarketIntelRequest()
        
        assert request.symbols == []
        assert request.include_sentiment is True
        assert request.include_news is True
        assert request.include_indicators is True
        assert request.include_earnings is False
        assert request.news_days == 7
        assert request.indicator_interval == "daily"
    
    def test_request_custom_values(self):
        """Test MarketIntelRequest with custom values."""
        request = MarketIntelRequest(
            symbols=["BTC", "ETH"],
            include_sentiment=True,
            include_news=False,
            include_indicators=True,
            news_days=14
        )
        
        assert request.symbols == ["BTC", "ETH"]
        assert request.include_news is False
        assert request.news_days == 14


class TestMarketIntelAdapter:
    """Test MarketIntelAdapter implementation."""
    
    def test_adapter_initialization(self):
        """Test adapter initializes without external services."""
        adapter = MarketIntelAdapter()
        
        assert adapter._fear_greed is None
        assert adapter._alpha_vantage is None
        assert adapter._finnhub is None
        assert adapter._initialized is False
    
    def test_adapter_with_injected_services(self):
        """Test adapter with injected mock services."""
        mock_fear_greed = Mock()
        mock_alpha_vantage = Mock()
        mock_finnhub = Mock()
        
        adapter = MarketIntelAdapter(
            fear_greed_service=mock_fear_greed,
            alpha_vantage_service=mock_alpha_vantage,
            finnhub_service=mock_finnhub
        )
        
        assert adapter._fear_greed == mock_fear_greed
        assert adapter._alpha_vantage == mock_alpha_vantage
        assert adapter._finnhub == mock_finnhub
    
    def test_sentiment_level_mapping(self):
        """Test _map_sentiment_level method."""
        adapter = MarketIntelAdapter()
        
        assert adapter._map_sentiment_level(10) == SentimentLevel.EXTREME_FEAR
        assert adapter._map_sentiment_level(30) == SentimentLevel.FEAR
        assert adapter._map_sentiment_level(50) == SentimentLevel.NEUTRAL
        assert adapter._map_sentiment_level(60) == SentimentLevel.GREED
        assert adapter._map_sentiment_level(80) == SentimentLevel.EXTREME_GREED
    
    def test_indicator_type_mapping(self):
        """Test _map_indicator_type method."""
        adapter = MarketIntelAdapter()
        
        assert adapter._map_indicator_type("rsi") == IndicatorType.RSI
        assert adapter._map_indicator_type("MACD") == IndicatorType.MACD
        assert adapter._map_indicator_type("ema") == IndicatorType.EMA
    
    def test_news_category_mapping(self):
        """Test _map_news_category method."""
        adapter = MarketIntelAdapter()
        
        assert adapter._map_news_category("general") == NewsCategory.GENERAL
        assert adapter._map_news_category("CRYPTO") == NewsCategory.CRYPTO
        assert adapter._map_news_category("forex") == NewsCategory.FOREX
    
    def test_health_check_no_services(self):
        """Test health_check when services not initialized."""
        adapter = MarketIntelAdapter()
        health = adapter.health_check()
        
        assert 'healthy' in health
        assert 'adapter' in health
        assert health['adapter'] == 'MarketIntelAdapter'
        assert 'providers' in health
    
    def test_get_sentiment_with_mock(self):
        """Test get_sentiment_snapshot with mock service."""
        mock_fear_greed = Mock()
        mock_fear_greed.get_current_index.return_value = {
            'value': 45,
            'classification': 'Fear',
            'timestamp': datetime.now(),
            'recommendation': 'Hold',
            'color': 'orange',
            'description': 'Market is somewhat fearful'
        }
        
        adapter = MarketIntelAdapter(fear_greed_service=mock_fear_greed)
        adapter._initialized = True
        
        result = adapter.get_sentiment_snapshot()
        
        assert result is not None
        assert result.value == 45
        assert result.level == SentimentLevel.FEAR
        mock_fear_greed.get_current_index.assert_called_once()
    
    def test_get_aggregated_intel(self):
        """Test get_aggregated_intel with mock services."""
        mock_fear_greed = Mock()
        mock_fear_greed.get_current_index.return_value = {
            'value': 50,
            'classification': 'Neutral',
            'timestamp': datetime.now(),
            'recommendation': 'Hold',
            'color': 'gray',
            'description': 'Market is neutral'
        }
        
        adapter = MarketIntelAdapter(fear_greed_service=mock_fear_greed)
        adapter._initialized = True
        
        request = MarketIntelRequest(
            symbols=[],
            include_sentiment=True,
            include_news=False,
            include_indicators=False
        )
        
        result = adapter.get_aggregated_intel(request)
        
        assert result is not None
        assert result.success is True
        assert result.sentiment is not None
        assert result.sentiment.value == 50


class TestMarketIntelPortProtocol:
    """Test that MarketIntelAdapter implements MarketIntelPort protocol."""
    
    def test_adapter_has_required_methods(self):
        """Verify adapter has all required protocol methods."""
        adapter = MarketIntelAdapter()
        
        required_methods = [
            'get_sentiment_snapshot',
            'get_sentiment_history',
            'get_technical_indicator',
            'get_multiple_indicators',
            'get_company_news',
            'get_general_news',
            'get_earnings_calendar',
            'refresh_macro_calendar',
            'get_aggregated_intel',
            'is_provider_available',
            'health_check',
        ]
        
        for method_name in required_methods:
            assert hasattr(adapter, method_name), f"Missing method: {method_name}"
            assert callable(getattr(adapter, method_name)), f"Not callable: {method_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
