"""
OMNIX Market Data Ports - Data Provider Interface Contracts

This module defines contracts for market data operations:
- MarketDataPort: Real-time and historical market data
- TechnicalIndicatorPort: Technical analysis calculations

SOLID Principles:
- SRP: Separated market data from technical calculations
- ISP: Segregated interfaces per concern
- DIP: Depend on abstractions for data providers
"""

from typing import Protocol, List, Dict, Any, runtime_checkable


@runtime_checkable
class MarketDataPort(Protocol):
    """
    Contract for market data providers.
    All methods are ASYNC for optimal network I/O.
    
    Implementations:
    - omnix_services.kraken_service.KrakenClient
    - omnix_services.alpaca_service.AlpacaClient
    - omnix_services.market_data_service.MarketDataService
    """
    
    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get OHLCV candles.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            timeframe: Candle interval ('1m', '5m', '1h', '1d')
            limit: Number of candles
            
        Returns:
            List of dicts with:
            - timestamp: datetime
            - open: float
            - high: float
            - low: float
            - close: float
            - volume: float
        """
        ...
    
    async def get_orderbook(
        self,
        symbol: str,
        depth: int = 20
    ) -> Dict[str, Any]:
        """
        Get order book.
        
        Args:
            symbol: Trading pair
            depth: Number of levels each side
            
        Returns:
            Dict with:
            - bids: List[[price, amount]]
            - asks: List[[price, amount]]
            - timestamp: datetime
        """
        ...
    
    async def get_recent_trades(
        self,
        symbol: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent trades.
        
        Args:
            symbol: Trading pair
            limit: Number of trades
            
        Returns:
            List of dicts with:
            - price: float
            - amount: float
            - side: str ('buy'/'sell')
            - timestamp: datetime
        """
        ...
    
    async def get_fear_greed_index(self) -> Dict[str, Any]:
        """
        Get Fear & Greed Index.
        
        Returns:
            Dict with:
            - value: int (0-100)
            - classification: str ('Extreme Fear', 'Fear', etc.)
            - timestamp: datetime
        """
        ...


@runtime_checkable
class TechnicalIndicatorPort(Protocol):
    """
    Contract for technical analysis calculations.
    All methods are SYNC (pure computation).
    
    Implementation: omnix_services.technical_analysis_service.TechnicalAnalysis
    """
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """
        Calculate Relative Strength Index.
        
        Args:
            prices: List of close prices
            period: RSI period
            
        Returns:
            RSI value (0-100)
        """
        ...
    
    def calculate_macd(
        self, 
        prices: List[float]
    ) -> Dict[str, float]:
        """
        Calculate MACD indicator.
        
        Args:
            prices: List of close prices
            
        Returns:
            Dict with:
            - macd: float
            - signal: float
            - histogram: float
        """
        ...
    
    def calculate_bollinger_bands(
        self, 
        prices: List[float], 
        period: int = 20
    ) -> Dict[str, float]:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: List of close prices
            period: Moving average period
            
        Returns:
            Dict with:
            - upper: float
            - middle: float
            - lower: float
        """
        ...
