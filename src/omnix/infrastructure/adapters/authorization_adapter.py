"""
OMNIX V7.0 Authorization Adapter
==================================
Adapter implementing AuthorizationPort with PostgreSQL + Redis cache.

This adapter reads from existing `users` table (is_admin, subscription_tier)
and `user_settings` table (trading_enabled, auto_trading, paper_trading_mode).

Features:
- Redis cache with 5 minute TTL for performance
- Fallback to settings.TELEGRAM_ADMIN_ID for OWNER detection
- Thread-safe operations
- Graceful degradation if database unavailable

SOLID Principles:
- SRP: Only authorization logic
- OCP: Extensible via new role/permission mappings
- DIP: Depends on port abstraction
"""

import os
import json
import logging
import threading
from typing import Optional, Dict, Any, Set
from datetime import datetime, timezone, timedelta

from src.omnix.ports.driven.authorization_port import (
    AuthorizationPort,
    UserAuthorization,
    UserRole,
    Permission,
    ROLE_PERMISSIONS,
    AuthorizationError,
)

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 300
RATE_LIMIT_FREE = 10
RATE_LIMIT_BASIC = 50
RATE_LIMIT_PRO = 200
RATE_LIMIT_PREMIUM = 1000
RATE_LIMIT_OWNER = 999999

ROLE_RATE_LIMITS = {
    UserRole.FREE: RATE_LIMIT_FREE,
    UserRole.BASIC: RATE_LIMIT_BASIC,
    UserRole.PRO: RATE_LIMIT_PRO,
    UserRole.PREMIUM: RATE_LIMIT_PREMIUM,
    UserRole.OWNER: RATE_LIMIT_OWNER,
}


class AuthorizationAdapter:
    """
    Adapter for authorization using PostgreSQL + Redis cache.
    
    Implements AuthorizationPort by reading from existing database tables.
    Provides both sync and async methods for flexibility.
    """
    
    def __init__(
        self,
        db_url: Optional[str] = None,
        redis_url: Optional[str] = None,
        admin_user_id: Optional[str] = None,
    ):
        """
        Initialize adapter with database and cache connections.
        
        Args:
            db_url: PostgreSQL connection URL (defaults to DATABASE_URL env)
            redis_url: Redis connection URL (defaults to REDIS_URL env)
            admin_user_id: Override admin user ID (defaults to TELEGRAM_ADMIN_ID)
        """
        self.db_url = db_url or os.environ.get('DATABASE_URL')
        self.redis_url = redis_url or os.environ.get('REDIS_URL')
        
        self._admin_user_id = admin_user_id
        self._lock = threading.RLock()
        self._local_cache: Dict[str, UserAuthorization] = {}
        
        self._db_conn = None
        self._redis_client = None
        self._db_available = False
        self._redis_available = False
        
        self._init_connections()
    
    def _init_connections(self):
        """Initialize database and Redis connections."""
        if self.db_url:
            try:
                import psycopg
                self._db_available = True
            except ImportError:
                logger.warning("psycopg not available for AuthorizationAdapter")
        
        if self.redis_url:
            try:
                import redis
                self._redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_timeout=2.0,
                    socket_connect_timeout=2.0,
                )
                self._redis_client.ping()
                self._redis_available = True
                logger.info("Redis connected for authorization cache")
            except Exception as e:
                logger.warning(f"Redis not available for auth cache: {e}")
                self._redis_available = False
    
    def _get_admin_user_id(self) -> str:
        """Get admin user ID from config or settings."""
        if self._admin_user_id:
            return self._admin_user_id
        
        try:
            from omnix_config.settings import settings
            return str(settings.TELEGRAM_ADMIN_ID)
        except ImportError:
            return os.environ.get('TELEGRAM_ADMIN_USER_ID', '7014748854')
    
    def _get_db_connection(self):
        """Get database connection."""
        if not self._db_available:
            return None
        try:
            import psycopg
            return psycopg.connect(self.db_url)
        except Exception as e:
            logger.error(f"DB connection failed: {e}")
            return None
    
    def _cache_key(self, user_id: str) -> str:
        """Generate Redis cache key for user."""
        return f"omnix:auth:{user_id}"
    
    def _rate_limit_key(self, user_id: str) -> str:
        """Generate Redis rate limit key for user."""
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        return f"omnix:rate:{user_id}:{today}"
    
    def _get_from_cache(self, user_id: str) -> Optional[UserAuthorization]:
        """Get authorization from cache (Redis then local)."""
        cache_key = self._cache_key(user_id)
        
        if self._redis_available and self._redis_client:
            try:
                cached = self._redis_client.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    return self._dict_to_authorization(data)
            except Exception as e:
                logger.debug(f"Redis cache miss: {e}")
        
        with self._lock:
            if user_id in self._local_cache:
                auth = self._local_cache[user_id]
                if auth.is_cache_valid:
                    return auth
                del self._local_cache[user_id]
        
        return None
    
    def _set_cache(self, auth: UserAuthorization) -> None:
        """Store authorization in cache (Redis and local)."""
        cache_key = self._cache_key(auth.user_id)
        auth.cached_at = datetime.utcnow()
        
        if self._redis_available and self._redis_client:
            try:
                data = self._authorization_to_dict(auth)
                self._redis_client.setex(
                    cache_key,
                    CACHE_TTL_SECONDS,
                    json.dumps(data)
                )
            except Exception as e:
                logger.debug(f"Redis cache write failed: {e}")
        
        with self._lock:
            self._local_cache[auth.user_id] = auth
    
    def _authorization_to_dict(self, auth: UserAuthorization) -> Dict[str, Any]:
        """Convert UserAuthorization to dict for caching."""
        return {
            'user_id': auth.user_id,
            'role': auth.role.name,
            'permissions': [p.name for p in auth.permissions],
            'is_admin': auth.is_admin,
            'subscription_tier': auth.subscription_tier,
            'daily_requests_used': auth.daily_requests_used,
            'daily_requests_limit': auth.daily_requests_limit,
            'trading_enabled': auth.trading_enabled,
            'auto_trading_enabled': auth.auto_trading_enabled,
            'paper_trading_mode': auth.paper_trading_mode,
            'cached_at': auth.cached_at.isoformat() if auth.cached_at else None,
        }
    
    def _dict_to_authorization(self, data: Dict[str, Any]) -> UserAuthorization:
        """Convert dict back to UserAuthorization."""
        role = UserRole[data.get('role', 'FREE')]
        permissions = {Permission[p] for p in data.get('permissions', [])}
        cached_at = None
        if data.get('cached_at'):
            try:
                cached_at = datetime.fromisoformat(data['cached_at'])
            except (ValueError, TypeError):
                pass
        
        return UserAuthorization(
            user_id=data['user_id'],
            role=role,
            permissions=permissions,
            is_admin=data.get('is_admin', False),
            subscription_tier=data.get('subscription_tier', 'free'),
            daily_requests_used=data.get('daily_requests_used', 0),
            daily_requests_limit=data.get('daily_requests_limit', RATE_LIMIT_FREE),
            trading_enabled=data.get('trading_enabled', False),
            auto_trading_enabled=data.get('auto_trading_enabled', False),
            paper_trading_mode=data.get('paper_trading_mode', True),
            cached_at=cached_at,
        )
    
    def _load_from_database(self, user_id: str) -> UserAuthorization:
        """Load authorization data from PostgreSQL."""
        user_id_str = str(user_id)
        admin_id = self._get_admin_user_id()
        
        is_admin = False
        subscription_tier = 'free'
        trading_enabled = False
        auto_trading = False
        paper_mode = True
        
        conn = self._get_db_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT is_admin, subscription_tier
                        FROM users
                        WHERE user_id = %s
                    """, (user_id_str,))
                    row = cur.fetchone()
                    if row:
                        is_admin = row[0] or False
                        subscription_tier = row[1] or 'free'
                    
                    cur.execute("""
                        SELECT trading_enabled, auto_trading, paper_trading_mode
                        FROM user_settings
                        WHERE user_id = %s
                    """, (user_id_str,))
                    settings_row = cur.fetchone()
                    if settings_row:
                        trading_enabled = settings_row[0] or False
                        auto_trading = settings_row[1] or False
                        paper_mode = settings_row[2] if settings_row[2] is not None else True
                
                conn.close()
            except Exception as e:
                logger.error(f"DB query failed for user {user_id}: {e}")
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
        
        if user_id_str == admin_id:
            is_admin = True
            subscription_tier = 'owner'
        
        role = self._tier_to_role(subscription_tier, is_admin)
        permissions = self._get_permissions_for_role(role)
        rate_limit = ROLE_RATE_LIMITS.get(role, RATE_LIMIT_FREE)
        
        return UserAuthorization(
            user_id=user_id_str,
            role=role,
            permissions=permissions,
            is_admin=is_admin,
            subscription_tier=subscription_tier,
            daily_requests_used=0,
            daily_requests_limit=rate_limit,
            trading_enabled=trading_enabled,
            auto_trading_enabled=auto_trading,
            paper_trading_mode=paper_mode,
        )
    
    def _tier_to_role(self, tier: str, is_admin: bool) -> UserRole:
        """Convert subscription tier string to UserRole enum."""
        if is_admin:
            return UserRole.OWNER
        
        tier_lower = (tier or 'free').lower()
        tier_map = {
            'owner': UserRole.OWNER,
            'premium': UserRole.PREMIUM,
            'pro': UserRole.PRO,
            'basic': UserRole.BASIC,
            'free': UserRole.FREE,
        }
        return tier_map.get(tier_lower, UserRole.FREE)
    
    def _get_permissions_for_role(self, role: UserRole) -> Set[Permission]:
        """Get all permissions for a role."""
        return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS[UserRole.FREE]).copy()
    
    def get_authorization(self, user_id: str) -> UserAuthorization:
        """
        Get authorization state for a user.
        
        Checks cache first, then loads from database.
        """
        user_id_str = str(user_id)
        
        cached = self._get_from_cache(user_id_str)
        if cached:
            return cached
        
        auth = self._load_from_database(user_id_str)
        self._set_cache(auth)
        
        return auth
    
    def get_role(self, user_id: str) -> UserRole:
        """Get user's role."""
        auth = self.get_authorization(user_id)
        return auth.role
    
    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        auth = self.get_authorization(user_id)
        return permission in auth.permissions
    
    def assert_permission(self, user_id: str, permission: Permission) -> None:
        """Assert user has permission, raise if not."""
        if not self.has_permission(user_id, permission):
            raise AuthorizationError(user_id, permission)
    
    def is_owner(self, user_id: str) -> bool:
        """Check if user is the system owner."""
        user_id_str = str(user_id)
        
        if user_id_str == self._get_admin_user_id():
            return True
        
        auth = self.get_authorization(user_id)
        return auth.role == UserRole.OWNER
    
    def invalidate_cache(self, user_id: str) -> bool:
        """Invalidate cached authorization for a user."""
        user_id_str = str(user_id)
        cache_key = self._cache_key(user_id_str)
        
        with self._lock:
            if user_id_str in self._local_cache:
                del self._local_cache[user_id_str]
        
        if self._redis_available and self._redis_client:
            try:
                self._redis_client.delete(cache_key)
            except Exception:
                pass
        
        return True
    
    def get_rate_limit_status(self, user_id: str) -> Dict[str, Any]:
        """Get rate limit status for a user."""
        auth = self.get_authorization(user_id)
        used = auth.daily_requests_used
        
        if self._redis_available and self._redis_client:
            try:
                rate_key = self._rate_limit_key(user_id)
                count = self._redis_client.get(rate_key)
                if count:
                    used = int(count)
            except Exception:
                pass
        
        limit = auth.daily_requests_limit
        remaining = max(0, limit - used)
        
        tomorrow = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
        
        return {
            'used': used,
            'limit': limit,
            'remaining': remaining,
            'reset_at': tomorrow.isoformat(),
        }
    
    def increment_request_count(self, user_id: str) -> bool:
        """Increment daily request counter for rate limiting."""
        auth = self.get_authorization(user_id)
        
        if auth.role == UserRole.OWNER:
            return True
        
        if self._redis_available and self._redis_client:
            try:
                rate_key = self._rate_limit_key(user_id)
                current = self._redis_client.incr(rate_key)
                
                if current == 1:
                    seconds_until_midnight = self._seconds_until_midnight()
                    self._redis_client.expire(rate_key, seconds_until_midnight)
                
                return current <= auth.daily_requests_limit
            except Exception as e:
                logger.warning(f"Rate limit increment failed: {e}")
                return True
        
        return True
    
    def _seconds_until_midnight(self) -> int:
        """Calculate seconds until next UTC midnight."""
        now = datetime.now(timezone.utc)
        tomorrow = now.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
        return int((tomorrow - now).total_seconds())


_authorization_adapter: Optional[AuthorizationAdapter] = None
_adapter_lock = threading.Lock()


def get_authorization_adapter() -> AuthorizationAdapter:
    """
    Get singleton AuthorizationAdapter instance.
    
    Thread-safe factory function for global access.
    """
    global _authorization_adapter
    
    if _authorization_adapter is None:
        with _adapter_lock:
            if _authorization_adapter is None:
                _authorization_adapter = AuthorizationAdapter()
    
    return _authorization_adapter


def reset_authorization_adapter() -> None:
    """Reset singleton for testing."""
    global _authorization_adapter
    with _adapter_lock:
        _authorization_adapter = None
