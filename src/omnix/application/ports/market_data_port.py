"""
OMNIX V7.0 Market Data Ports
=============================
Protocols for market data access.
"""

from typing import Protocol, Optional, List, Dict, Any
from src.omnix.domain.support.market import MarketSnapshot, RegimeState


class IPriceProvider(Protocol):
    """Port for getting current prices."""
    
    async def get_current_price(self, pair: str) -> float:
        """Get current market price for a pair."""
        ...
    
    async def get_bid_ask(self, pair: str) -> tuple[float, float]:
        """Get current bid and ask prices."""
        ...


class IMarketDataService(Protocol):
    """Port for comprehensive market data."""
    
    async def get_snapshot(self, pair: str) -> MarketSnapshot:
        """Get full market snapshot for a pair."""
        ...
    
    async def get_ohlcv(
        self,
        pair: str,
        timeframe: str = "1h",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get OHLCV candlestick data."""
        ...
    
    async def get_orderbook(
        self,
        pair: str,
        depth: int = 10,
    ) -> Dict[str, List[tuple[float, float]]]:
        """Get orderbook with bids and asks."""
        ...
    
    async def get_regime(self, pair: str) -> RegimeState:
        """Get current market regime detection."""
        ...
    
    async def get_volatility(self, pair: str, period: int = 14) -> float:
        """Get current volatility measure."""
        ...
    
    async def get_available_pairs(self) -> List[str]:
        """Get list of tradable pairs."""
        ...
    
    async def get_fear_greed_index(self) -> int:
        """Get current Fear & Greed Index (0-100)."""
        ...
