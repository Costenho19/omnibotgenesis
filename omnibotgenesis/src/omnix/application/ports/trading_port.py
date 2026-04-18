"""
OMNIX V7.0 Trading Ports
=========================
Protocols for trading operations.
"""

from typing import Protocol, Optional, List, Dict, Any
from src.omnix.domain.trading.entities import Trade, Position, TradeDirection


class IOrderExecutor(Protocol):
    """Port for executing orders on exchanges."""
    
    async def execute_order(
        self,
        pair: str,
        direction: TradeDirection,
        quantity: float,
        price: Optional[float] = None,
        order_type: str = "market",
    ) -> Trade:
        """Execute a trade order."""
        ...
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        ...
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get current order status."""
        ...


class ITradingService(Protocol):
    """Port for high-level trading operations."""
    
    async def open_position(
        self,
        pair: str,
        direction: TradeDirection,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        strategy: str = "",
    ) -> Trade:
        """Open a new trading position."""
        ...
    
    async def close_position(
        self,
        position_id: str,
        exit_price: Optional[float] = None,
    ) -> Trade:
        """Close an existing position."""
        ...
    
    async def get_open_positions(self, user_id: Optional[str] = None) -> List[Position]:
        """Get all open positions."""
        ...
    
    async def get_balance(self) -> Dict[str, float]:
        """Get current account balance."""
        ...
    
    async def get_trade_history(
        self,
        limit: int = 100,
        user_id: Optional[str] = None,
    ) -> List[Trade]:
        """Get recent trade history."""
        ...
