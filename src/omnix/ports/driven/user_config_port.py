"""
OMNIX V7.0 User Config Port
============================
Interface for user configuration persistence in multi-user trading context.

Separates persistent USER CONFIGURATION from RUNTIME SESSION STATE (UserSessionPort).

SRP Distinction:
- UserConfigPort: Persistent config (trading pairs, risk limits, preferences)
- UserSessionPort: Runtime state (running, paused, trades count)

SOLID Principles:
- SRP: Only user configuration operations
- ISP: Minimal interface for config management
- DIP: Depend on this abstraction, not database directly
"""

from typing import Protocol, Optional, List, Dict, Any, runtime_checkable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UserConfig:
    """
    Value object representing a user's persistent trading configuration.
    
    This is SEPARATE from UserSession which holds runtime state.
    UserConfig persists between bot restarts and represents user preferences.
    """
    user_id: str
    
    trading_pairs: List[str] = field(default_factory=lambda: [
        'BTC/USD', 'ETH/USD', 'SOL/USD',
        'XRP/USD', 'ADA/USD', 'DOT/USD',
        'LINK/USD', 'AVAX/USD', 'POL/USD',
        'ATOM/USD', 'LTC/USD'
    ])
    
    min_trade_usd: float = 75.0
    max_position_pct: float = 0.12
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.05
    max_daily_loss_pct: float = 0.08
    min_confidence: float = 0.14
    
    paper_mode: bool = True
    auto_trading: bool = False
    trading_enabled: bool = True
    
    initial_balance: float = 1_000_000.0
    
    language: str = 'es'
    timezone: str = 'America/New_York'
    
    telegram_username: Optional[str] = None
    telegram_first_name: Optional[str] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            'user_id': self.user_id,
            'trading_pairs': self.trading_pairs,
            'min_trade_usd': self.min_trade_usd,
            'max_position_pct': self.max_position_pct,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'max_daily_loss_pct': self.max_daily_loss_pct,
            'min_confidence': self.min_confidence,
            'paper_mode': self.paper_mode,
            'auto_trading': self.auto_trading,
            'trading_enabled': self.trading_enabled,
            'initial_balance': self.initial_balance,
            'language': self.language,
            'timezone': self.timezone,
            'telegram_username': self.telegram_username,
            'telegram_first_name': self.telegram_first_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def default_trading_pairs(cls) -> List[str]:
        """Get default trading pairs list."""
        return [
            'BTC/USD', 'ETH/USD', 'SOL/USD',
            'XRP/USD', 'ADA/USD', 'DOT/USD',
            'LINK/USD', 'AVAX/USD', 'POL/USD',
            'ATOM/USD', 'LTC/USD'
        ]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserConfig':
        """Create from dictionary."""
        created_at = data.get('created_at')
        updated_at = data.get('updated_at')
        
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        trading_pairs = data.get('trading_pairs')
        if not trading_pairs or not isinstance(trading_pairs, list):
            trading_pairs = cls.default_trading_pairs()
        
        return cls(
            user_id=data['user_id'],
            trading_pairs=trading_pairs,
            min_trade_usd=data.get('min_trade_usd', 75.0),
            max_position_pct=data.get('max_position_pct', 0.12),
            stop_loss_pct=data.get('stop_loss_pct', 0.02),
            take_profit_pct=data.get('take_profit_pct', 0.05),
            max_daily_loss_pct=data.get('max_daily_loss_pct', 0.08),
            min_confidence=data.get('min_confidence', 0.14),
            paper_mode=data.get('paper_mode', True),
            auto_trading=data.get('auto_trading', False),
            trading_enabled=data.get('trading_enabled', True),
            initial_balance=data.get('initial_balance', 1_000_000.0),
            language=data.get('language', 'es'),
            timezone=data.get('timezone', 'America/New_York'),
            telegram_username=data.get('telegram_username'),
            telegram_first_name=data.get('telegram_first_name'),
            created_at=created_at,
            updated_at=updated_at,
        )


@runtime_checkable
class UserConfigPort(Protocol):
    """
    Contract for user configuration persistence.
    
    Implementations:
    - PostgreSQL adapter (primary - to be created)
    - In-memory mock for testing
    
    Usage:
        config = config_port.get_config(user_id)
        config.min_confidence = 0.20
        config_port.save_config(config)
    """
    
    def get_config(self, user_id: str) -> UserConfig:
        """
        Get or create configuration for the given user.
        
        Args:
            user_id: Unique user identifier (e.g., Telegram chat_id)
            
        Returns:
            UserConfig instance (creates with defaults if doesn't exist)
        """
        ...
    
    def save_config(self, config: UserConfig) -> bool:
        """
        Persist user configuration to storage.
        
        Args:
            config: UserConfig to save
            
        Returns:
            True if saved successfully
        """
        ...
    
    def update_config(
        self, 
        user_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[UserConfig]:
        """
        Partial update of user configuration.
        
        Args:
            user_id: User to update
            updates: Dict of field_name -> new_value
            
        Returns:
            Updated UserConfig if successful, None otherwise
        """
        ...
    
    def delete_config(self, user_id: str) -> bool:
        """
        Remove a user's configuration from storage.
        
        Args:
            user_id: User whose config to delete
            
        Returns:
            True if deleted successfully
        """
        ...
    
    def get_users_with_auto_trading(self) -> List[UserConfig]:
        """
        Get all users who have auto_trading enabled.
        
        Returns:
            List of UserConfig instances where auto_trading=True
        """
        ...
    
    def set_auto_trading(self, user_id: str, enabled: bool) -> bool:
        """
        Toggle auto-trading for a user.
        
        Args:
            user_id: User to modify
            enabled: True to enable, False to disable
            
        Returns:
            True if updated successfully
        """
        ...
    
    def exists(self, user_id: str) -> bool:
        """
        Check if configuration exists for user.
        
        Args:
            user_id: User to check
            
        Returns:
            True if config exists
        """
        ...
