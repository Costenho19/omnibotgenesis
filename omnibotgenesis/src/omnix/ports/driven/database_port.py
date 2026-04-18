"""
OMNIX Database Ports - Repository Interface Contracts

This module defines contracts for database operations following ISP:
- DatabasePort: Low-level query execution
- TradeRepositoryPort: Trade persistence
- PositionRepositoryPort: Position persistence
- UserRepositoryPort: User persistence

SOLID Principles:
- SRP: Each repository handles one entity type
- ISP: Segregated interfaces per domain entity
- DIP: Depend on these abstractions, not DatabaseService directly
"""

from typing import Protocol, Optional, List, Dict, Any, Tuple, runtime_checkable


@runtime_checkable
class DatabasePort(Protocol):
    """
    Low-level database operations contract.
    
    Implementation: omnix_services.database_service.DatabaseService
    """
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Tuple] = None,
        fetch: bool = True
    ) -> Optional[List[Tuple]]:
        """
        Execute raw SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            fetch: Whether to fetch results
            
        Returns:
            List of tuples if fetch=True, None otherwise
        """
        ...
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check database connectivity.
        
        Returns:
            Dict with:
            - connected: bool
            - latency_ms: float
            - version: str
        """
        ...


@runtime_checkable
class TradeRepositoryPort(Protocol):
    """
    Contract for trade persistence operations.
    
    Implementation: omnix_services.database_service.DatabaseService
    """
    
    def save_trade(self, trade: Dict[str, Any]) -> Optional[str]:
        """
        Save a trade record.
        
        Args:
            trade: Trade data dict with symbol, side, amount, price, etc.
            
        Returns:
            trade_id if successful, None otherwise
        """
        ...
    
    def get_trade_by_id(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve trade by ID.
        
        Args:
            trade_id: The trade ID
            
        Returns:
            Trade dict if found, None otherwise
        """
        ...
    
    def get_trades_by_user(
        self, 
        user_id: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get trades for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum trades to return
            
        Returns:
            List of trade dicts, newest first
        """
        ...
    
    def update_trade(self, trade_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update trade record.
        
        Args:
            trade_id: The trade ID
            updates: Fields to update
            
        Returns:
            True if updated successfully
        """
        ...


@runtime_checkable
class PositionRepositoryPort(Protocol):
    """
    Contract for position persistence operations.
    
    Implementation: omnix_services.database_service.DatabaseService
    """
    
    def save_position(self, position: Dict[str, Any]) -> Optional[str]:
        """
        Save a position record.
        
        Args:
            position: Position data dict
            
        Returns:
            position_id if successful, None otherwise
        """
        ...
    
    def get_open_positions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all open positions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of open position dicts
        """
        ...
    
    def close_position(self, position_id: str, close_data: Dict[str, Any]) -> bool:
        """
        Close a position.
        
        Args:
            position_id: The position ID
            close_data: Close price, timestamp, PnL, etc.
            
        Returns:
            True if closed successfully
        """
        ...


@runtime_checkable
class UserRepositoryPort(Protocol):
    """
    Contract for user persistence operations.
    
    Implementation: omnix_services.database_service.DatabaseService
    """
    
    def ensure_user_exists(
        self, 
        user_id: str, 
        username: Optional[str] = None
    ) -> bool:
        """
        Ensure user exists in database, create if not.
        
        Args:
            user_id: User identifier (Telegram ID)
            username: Optional username
            
        Returns:
            True if user exists or was created
        """
        ...
    
    def get_user_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user settings.
        
        Args:
            user_id: User identifier
            
        Returns:
            Settings dict if found, None otherwise
        """
        ...
    
    def update_user_settings(self, user_id: str, settings: Dict[str, Any]) -> bool:
        """
        Update user settings.
        
        Args:
            user_id: User identifier
            settings: Settings to update
            
        Returns:
            True if updated successfully
        """
        ...
