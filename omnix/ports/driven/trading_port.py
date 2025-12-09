"""
OMNIX Trading Port - Exchange Interface Contract

This Protocol defines the contract for exchange adapters (Kraken, Alpaca, Paper).
All methods are SYNCHRONOUS because ccxt is sync by default.
Use asyncio.to_thread() for async contexts if needed.

SOLID Principles:
- SRP: Only exchange trading operations
- ISP: Minimal interface for trading operations
- DIP: Depend on this abstraction, not concrete implementations
"""

from typing import Protocol, List, Dict, Any, runtime_checkable
from decimal import Decimal


@runtime_checkable
class TradingPort(Protocol):
    """
    Contract for exchange adapters (Kraken, Alpaca, Paper).
    
    Implementations:
    - omnix_services.kraken_service.KrakenClient
    - omnix_services.alpaca_service.AlpacaClient
    - omnix_core.paper_trading.PaperTradingManager
    """
    
    def execute_order(
        self,
        symbol: str,
        side: str,
        amount: Decimal,
        order_type: str = 'market'
    ) -> Dict[str, Any]:
        """
        Execute a trade order.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            side: 'buy' or 'sell'
            amount: Order quantity
            order_type: 'market' or 'limit'
            
        Returns:
            Dict with order result including:
            - order_id: str
            - status: str
            - filled_amount: Decimal
            - price: Decimal
            - timestamp: datetime
        """
        ...
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Get current price for symbol.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            
        Returns:
            Dict with:
            - bid: Decimal
            - ask: Decimal
            - last: Decimal
            - volume: Decimal
            - timestamp: datetime
        """
        ...
    
    def get_balance(self) -> Dict[str, Decimal]:
        """
        Get account balances.
        
        Returns:
            Dict mapping currency to balance.
            Example: {'USD': Decimal('10000'), 'BTC': Decimal('0.5')}
        """
        ...
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions.
        
        Returns:
            List of position dicts with:
            - symbol: str
            - side: str
            - amount: Decimal
            - entry_price: Decimal
            - unrealized_pnl: Decimal
        """
        ...
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an open order.
        
        Args:
            order_id: The order ID to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        ...
    
    def is_connected(self) -> bool:
        """
        Check if exchange connection is active.
        
        Returns:
            True if connected and authenticated
        """
        ...
