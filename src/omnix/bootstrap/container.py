"""
OMNIX V7.0 Dependency Injection Container
==========================================
Phase 1: Bootstrap & Config - DI Container with Protocol interfaces.

This container provides dependency injection for OMNIX services,
following the Hexagonal Architecture pattern with ports and adapters.

Usage:
    from src.omnix.bootstrap import Container
    container = Container.create()
    db = container.database
"""

from dataclasses import dataclass, field
from typing import Protocol, Optional, Any, runtime_checkable
import logging

logger = logging.getLogger(__name__)


@runtime_checkable
class IDatabaseGateway(Protocol):
    def execute(self, query: str, params: Optional[tuple] = None) -> list:
        ...
    
    def execute_one(self, query: str, params: Optional[tuple] = None) -> Optional[tuple]:
        ...
    
    def is_connected(self) -> bool:
        ...


@runtime_checkable
class IRedisCache(Protocol):
    def get(self, key: str) -> Optional[str]:
        ...
    
    def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        ...
    
    def delete(self, key: str) -> bool:
        ...
    
    def is_connected(self) -> bool:
        ...


@runtime_checkable
class ITradingService(Protocol):
    def get_balance(self, user_id: str) -> dict:
        ...
    
    def execute_trade(self, user_id: str, symbol: str, side: str, amount: float) -> dict:
        ...


@runtime_checkable
class IMarketDataService(Protocol):
    def get_ticker(self, symbol: str) -> dict:
        ...
    
    def get_orderbook(self, symbol: str, depth: int = 10) -> dict:
        ...


class NullDatabase:
    def execute(self, query: str, params: Optional[tuple] = None) -> list:
        logger.warning("NullDatabase: execute() called but no database configured")
        return []
    
    def execute_one(self, query: str, params: Optional[tuple] = None) -> Optional[tuple]:
        logger.warning("NullDatabase: execute_one() called but no database configured")
        return None
    
    def is_connected(self) -> bool:
        return False


class NullCache:
    def get(self, key: str) -> Optional[str]:
        logger.warning("NullCache: get() called but no cache configured")
        return None
    
    def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        logger.warning("NullCache: set() called but no cache configured")
        return False
    
    def delete(self, key: str) -> bool:
        logger.warning("NullCache: delete() called but no cache configured")
        return False
    
    def is_connected(self) -> bool:
        return False


@dataclass
class Container:
    """
    Dependency Injection Container for OMNIX services.
    
    Provides lazy-loaded access to infrastructure services.
    Uses Null Object pattern for graceful degradation when services unavailable.
    
    Phase 2 Update: Added application layer ports and adapters.
    """
    
    _database: Optional[IDatabaseGateway] = field(default=None, repr=False)
    _cache: Optional[IRedisCache] = field(default=None, repr=False)
    _settings: Optional[Any] = field(default=None, repr=False)
    _initialized: bool = field(default=False, repr=False)
    
    _trading_adapter: Optional[Any] = field(default=None, repr=False)
    _risk_adapter: Optional[Any] = field(default=None, repr=False)
    _coherence_adapter: Optional[Any] = field(default=None, repr=False)
    
    @property
    def settings(self):
        if self._settings is None:
            from src.omnix.config.settings import get_settings
            self._settings = get_settings()
        return self._settings
    
    @property
    def database(self) -> IDatabaseGateway:
        if self._database is None:
            self._database = self._create_database()
        return self._database
    
    @property
    def cache(self) -> IRedisCache:
        if self._cache is None:
            self._cache = self._create_cache()
        return self._cache
    
    @property
    def trading_adapter(self):
        """Get trading adapter (Phase 2)."""
        if self._trading_adapter is None:
            self._trading_adapter = self._create_trading_adapter()
        return self._trading_adapter
    
    @property
    def risk_adapter(self):
        """Get risk adapter (Phase 2)."""
        if self._risk_adapter is None:
            self._risk_adapter = self._create_risk_adapter()
        return self._risk_adapter
    
    @property
    def coherence_adapter(self):
        """Get coherence engine adapter (Phase 2)."""
        if self._coherence_adapter is None:
            self._coherence_adapter = self._create_coherence_adapter()
        return self._coherence_adapter
    
    @property
    def use_app_layer(self) -> bool:
        """Check if application layer is enabled."""
        return getattr(self.settings, 'use_app_layer', False)
    
    def _create_database(self) -> IDatabaseGateway:
        try:
            from omnix_services.database_service.database_gateway import DatabaseGateway
            gateway = DatabaseGateway.get_instance()
            if gateway:
                is_healthy = getattr(gateway, 'is_healthy', lambda: True)()
                if is_healthy:
                    logger.info("Container: DatabaseGateway connected successfully")
                    return gateway  # type: ignore
        except ImportError:
            logger.warning("Container: DatabaseGateway not available, using null database")
        except Exception as e:
            logger.error(f"Container: Failed to initialize DatabaseGateway: {e}")
        
        return NullDatabase()
    
    def _create_cache(self) -> IRedisCache:
        try:
            from omnix_core.cache.redis_cache import RedisCache
            get_instance = getattr(RedisCache, 'get_instance', None)
            if get_instance:
                cache = get_instance()
            else:
                cache = RedisCache()
            if cache:
                is_connected = getattr(cache, 'is_connected', lambda: True)()
                if is_connected:
                    logger.info("Container: RedisCache connected successfully")
                    return cache  # type: ignore
        except ImportError:
            logger.warning("Container: RedisCache not available, using null cache")
        except Exception as e:
            logger.error(f"Container: Failed to initialize RedisCache: {e}")
        
        return NullCache()
    
    def _create_trading_adapter(self):
        """Create trading adapter (Phase 2)."""
        try:
            from src.omnix.infrastructure.adapters.trading_adapter import TradingServiceAdapter
            return TradingServiceAdapter()
        except ImportError:
            logger.warning("Container: TradingServiceAdapter not available")
            return None
    
    def _create_risk_adapter(self):
        """Create risk adapter (Phase 2)."""
        try:
            from src.omnix.infrastructure.adapters.risk_adapter import RiskGuardianAdapter
            return RiskGuardianAdapter()
        except ImportError:
            logger.warning("Container: RiskGuardianAdapter not available")
            return None
    
    def _create_coherence_adapter(self):
        """Create coherence engine adapter (Phase 2)."""
        try:
            from src.omnix.infrastructure.adapters.coherence_adapter import CoherenceEngineAdapter
            return CoherenceEngineAdapter()
        except ImportError:
            logger.warning("Container: CoherenceEngineAdapter not available")
            return None
    
    @classmethod
    def create(cls, lazy: bool = True) -> "Container":
        container = cls()
        if not lazy:
            _ = container.database
            _ = container.cache
            container._initialized = True
        return container
    
    def health_check(self) -> dict:
        return {
            'database': self.database.is_connected() if hasattr(self.database, 'is_connected') else False,
            'cache': self.cache.is_connected() if hasattr(self.cache, 'is_connected') else False,
            'settings': self.settings is not None,
            'trading_adapter': self.trading_adapter is not None,
            'risk_adapter': self.risk_adapter is not None,
            'coherence_adapter': self.coherence_adapter is not None,
            'use_app_layer': self.use_app_layer,
        }
    
    def __repr__(self) -> str:
        health = self.health_check()
        return f"Container(db={health['database']}, cache={health['cache']})"


_global_container: Optional[Container] = None


def get_container() -> Container:
    global _global_container
    if _global_container is None:
        _global_container = Container.create()
    return _global_container


def reset_container():
    global _global_container
    _global_container = None
