"""
OMNIX V7.0 User Session Port
==============================
Interface for user session management in multi-user trading context.

This port abstracts session operations allowing different implementations
(Redis, PostgreSQL, in-memory) while maintaining consistent interface.

SOLID Principles:
- SRP: Only user session operations
- ISP: Minimal interface for session management
- DIP: Depend on this abstraction, not UserSessionManager directly
"""

from typing import Protocol, Optional, List, Dict, Any, runtime_checkable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UserSession:
    """
    Value object representing a user's trading session.
    
    Mirrors UserTradingSession from omnix_core.sessions for complete state.
    """
    user_id: str
    status: str = "inactive"
    
    running: bool = False
    paused: bool = False
    emergency_stop: bool = False
    
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit_loss: float = 0.0
    daily_profit_loss: float = 0.0
    
    paper_balance: float = 1_000_000.0
    paper_positions: Dict[str, Any] = field(default_factory=dict)
    
    initial_balance: float = 1_000_000.0
    last_trade_time: Optional[str] = None
    last_activity: Optional[str] = None
    start_time: Optional[str] = None
    
    trading_pairs: List[str] = field(default_factory=lambda: [
        'BTC/USD', 'ETH/USD', 'SOL/USD',
        'XRP/USD', 'ADA/USD', 'DOT/USD',
        'LINK/USD', 'AVAX/USD', 'POL/USD',
        'ATOM/USD', 'LTC/USD'
    ])
    
    min_trade_usd: float = 75.0
    max_position_pct: float = 0.12
    stop_loss_pct: float = 0.02
    max_daily_loss_pct: float = 0.08
    min_confidence: float = 0.14
    
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    config_snapshot: Optional[Dict[str, Any]] = None
    
    @property
    def win_rate(self) -> float:
        """Calculate current win rate."""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100


@runtime_checkable
class UserSessionPort(Protocol):
    """
    Contract for user session management.
    
    Implementations:
    - omnix_core.sessions.UserSessionManager (primary)
    - In-memory mock for testing
    """
    
    def get_session(self, user_id: str) -> UserSession:
        """
        Get or create a session for the given user.
        
        Args:
            user_id: Unique user identifier (e.g., Telegram chat_id)
            
        Returns:
            UserSession instance (creates new if doesn't exist)
        """
        ...
    
    def save_session(self, session: UserSession) -> bool:
        """
        Persist session to storage (Redis + PostgreSQL).
        
        Args:
            session: UserSession to save
            
        Returns:
            True if saved successfully
        """
        ...
    
    def get_active_sessions(self) -> List[UserSession]:
        """
        Get all sessions where running=True.
        
        Returns:
            List of active UserSession instances
        """
        ...
    
    def set_emergency_stop(self, user_id: str, stop: bool = True) -> bool:
        """
        Toggle emergency stop for a user.
        
        Args:
            user_id: User to modify
            stop: True to activate stop, False to deactivate
            
        Returns:
            True if updated successfully
        """
        ...
    
    def pause_session(self, user_id: str, paused: bool = True) -> bool:
        """
        Pause or resume a user's trading session.
        
        Args:
            user_id: User to modify
            paused: True to pause, False to resume
            
        Returns:
            True if updated successfully
        """
        ...
    
    def delete_session(self, user_id: str) -> bool:
        """
        Remove a user's session from storage.
        
        Args:
            user_id: User session to delete
            
        Returns:
            True if deleted successfully
        """
        ...
