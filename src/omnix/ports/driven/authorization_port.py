"""
OMNIX V7.0 Authorization Port
===============================
Interface for role-based access control in multi-tenant trading context.

This port abstracts authorization operations allowing different implementations
(PostgreSQL, Redis cache, in-memory) while maintaining consistent interface.

SOLID Principles:
- SRP: Only authorization operations
- ISP: Minimal interface for permission checks
- DIP: Depend on this abstraction, not DatabaseService directly

Security Model:
- OWNER: Full access (real trading, admin functions) - Harold only
- PREMIUM: Paper trading + advanced features
- PRO: Paper trading + alerts
- BASIC: Limited paper trading
- FREE: Read-only + limited analysis
"""

from typing import Protocol, Optional, Set, Dict, Any, runtime_checkable
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime


class UserRole(Enum):
    """
    User subscription tiers with hierarchical permissions.
    
    Order matters: higher value = more permissions.
    """
    FREE = 1
    BASIC = 2
    PRO = 3
    PREMIUM = 4
    OWNER = 5


class Permission(Enum):
    """
    Granular permissions for trading operations.
    
    Each permission maps to specific system capabilities.
    """
    READ_MARKET_DATA = auto()
    BASIC_ANALYSIS = auto()
    ADVANCED_ANALYSIS = auto()
    PAPER_TRADING = auto()
    PAPER_AUTO_TRADING = auto()
    REAL_TRADING = auto()
    REAL_AUTO_TRADING = auto()
    VIEW_BALANCE = auto()
    VIEW_REAL_BALANCE = auto()
    MANAGE_ALERTS = auto()
    VOICE_RESPONSES = auto()
    PORTFOLIO_OPTIMIZATION = auto()
    DERIVATIVES_TRADING = auto()
    ADMIN_FUNCTIONS = auto()
    UNLIMITED_REQUESTS = auto()


ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.FREE: {
        Permission.READ_MARKET_DATA,
        Permission.BASIC_ANALYSIS,
    },
    UserRole.BASIC: {
        Permission.READ_MARKET_DATA,
        Permission.BASIC_ANALYSIS,
        Permission.PAPER_TRADING,
        Permission.VIEW_BALANCE,
    },
    UserRole.PRO: {
        Permission.READ_MARKET_DATA,
        Permission.BASIC_ANALYSIS,
        Permission.ADVANCED_ANALYSIS,
        Permission.PAPER_TRADING,
        Permission.PAPER_AUTO_TRADING,
        Permission.VIEW_BALANCE,
        Permission.MANAGE_ALERTS,
    },
    UserRole.PREMIUM: {
        Permission.READ_MARKET_DATA,
        Permission.BASIC_ANALYSIS,
        Permission.ADVANCED_ANALYSIS,
        Permission.PAPER_TRADING,
        Permission.PAPER_AUTO_TRADING,
        Permission.VIEW_BALANCE,
        Permission.MANAGE_ALERTS,
        Permission.VOICE_RESPONSES,
        Permission.PORTFOLIO_OPTIMIZATION,
        Permission.UNLIMITED_REQUESTS,
    },
    UserRole.OWNER: {
        Permission.READ_MARKET_DATA,
        Permission.BASIC_ANALYSIS,
        Permission.ADVANCED_ANALYSIS,
        Permission.PAPER_TRADING,
        Permission.PAPER_AUTO_TRADING,
        Permission.REAL_TRADING,
        Permission.REAL_AUTO_TRADING,
        Permission.VIEW_BALANCE,
        Permission.VIEW_REAL_BALANCE,
        Permission.MANAGE_ALERTS,
        Permission.VOICE_RESPONSES,
        Permission.PORTFOLIO_OPTIMIZATION,
        Permission.DERIVATIVES_TRADING,
        Permission.ADMIN_FUNCTIONS,
        Permission.UNLIMITED_REQUESTS,
    },
}


@dataclass
class UserAuthorization:
    """
    Value object representing a user's authorization state.
    
    Contains role, permissions, and rate limit information.
    """
    user_id: str
    role: UserRole = UserRole.FREE
    permissions: Set[Permission] = field(default_factory=set)
    
    is_admin: bool = False
    subscription_tier: str = "free"
    
    daily_requests_used: int = 0
    daily_requests_limit: int = 10
    
    trading_enabled: bool = False
    auto_trading_enabled: bool = False
    paper_trading_mode: bool = True
    
    cached_at: Optional[datetime] = None
    cache_ttl_seconds: int = 300
    
    @property
    def is_owner(self) -> bool:
        """Check if user has OWNER role."""
        return self.role == UserRole.OWNER
    
    @property
    def can_real_trade(self) -> bool:
        """Check if user can execute real trades."""
        return Permission.REAL_TRADING in self.permissions
    
    @property
    def can_paper_trade(self) -> bool:
        """Check if user can execute paper trades."""
        return Permission.PAPER_TRADING in self.permissions
    
    @property
    def is_cache_valid(self) -> bool:
        """Check if cached authorization is still valid."""
        if self.cached_at is None:
            return False
        elapsed = (datetime.utcnow() - self.cached_at).total_seconds()
        return elapsed < self.cache_ttl_seconds
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions


class AuthorizationError(Exception):
    """Raised when authorization check fails."""
    
    def __init__(self, user_id: str = None, permission: Permission = None, message: str = None):
        """
        Flexible constructor for authorization errors.
        
        Can be called as:
        - AuthorizationError("simple message")  # Legacy fallback
        - AuthorizationError(user_id, permission)  # Standard
        - AuthorizationError(user_id, permission, message)  # Full
        """
        # Handle legacy single-string calls: AuthorizationError("message")
        if user_id is not None and permission is None and message is None:
            # Single argument - treat as message string
            self.user_id = None
            self.permission = None
            self.message = str(user_id)
        else:
            self.user_id = user_id
            self.permission = permission
            if message:
                self.message = message
            elif user_id and permission:
                self.message = f"User {user_id} lacks permission: {permission.name}"
            else:
                self.message = "Authorization denied"
        super().__init__(self.message)


@runtime_checkable
class AuthorizationPort(Protocol):
    """
    Contract for authorization management.
    
    Implementations:
    - AuthorizationAdapter (PostgreSQL + Redis cache)
    - In-memory mock for testing
    
    Thread-safe: All methods must be safe for concurrent access.
    """
    
    def get_authorization(self, user_id: str) -> UserAuthorization:
        """
        Get authorization state for a user.
        
        Args:
            user_id: Unique user identifier (e.g., Telegram user_id)
            
        Returns:
            UserAuthorization with role and permissions
            
        Note:
            Returns FREE role for unknown users (fail-safe)
        """
        ...
    
    def get_role(self, user_id: str) -> UserRole:
        """
        Get user's role from database or cache.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            UserRole enum value
        """
        ...
    
    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            user_id: Unique user identifier
            permission: Permission to check
            
        Returns:
            True if user has permission, False otherwise
        """
        ...
    
    def assert_permission(self, user_id: str, permission: Permission) -> None:
        """
        Assert user has permission, raise if not.
        
        Args:
            user_id: Unique user identifier
            permission: Permission to assert
            
        Raises:
            AuthorizationError: If user lacks permission
        """
        ...
    
    def is_owner(self, user_id: str) -> bool:
        """
        Check if user is the system owner (Harold).
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            True if user is OWNER role
        """
        ...
    
    def invalidate_cache(self, user_id: str) -> bool:
        """
        Invalidate cached authorization for a user.
        
        Args:
            user_id: User whose cache to invalidate
            
        Returns:
            True if cache was invalidated
        """
        ...
    
    def get_rate_limit_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get rate limit status for a user.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            Dict with 'used', 'limit', 'remaining', 'reset_at'
        """
        ...
    
    def increment_request_count(self, user_id: str) -> bool:
        """
        Increment daily request counter for rate limiting.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            True if under limit, False if limit exceeded
        """
        ...
