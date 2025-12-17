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
    
    _kraken_adapter: Optional[Any] = field(default=None, repr=False)
    _gemini_adapter: Optional[Any] = field(default=None, repr=False)
    _telegram_adapter: Optional[Any] = field(default=None, repr=False)
    _notification_adapter: Optional[Any] = field(default=None, repr=False)
    _cache_adapter: Optional[Any] = field(default=None, repr=False)
    _database_adapter: Optional[Any] = field(default=None, repr=False)
    _database_manager: Optional[Any] = field(default=None, repr=False)
    _onchain_adapter: Optional[Any] = field(default=None, repr=False)
    _market_intel_adapter: Optional[Any] = field(default=None, repr=False)
    _execution_adapter: Optional[Any] = field(default=None, repr=False)
    _risk_control_adapter: Optional[Any] = field(default=None, repr=False)
    _derivatives_adapter: Optional[Any] = field(default=None, repr=False)
    _portfolio_adapter: Optional[Any] = field(default=None, repr=False)
    _optimization_adapter: Optional[Any] = field(default=None, repr=False)
    
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
    def kraken_adapter(self):
        """Get Kraken exchange adapter (Phase 3)."""
        if self._kraken_adapter is None:
            self._kraken_adapter = self._create_kraken_adapter()
        return self._kraken_adapter
    
    @property
    def gemini_adapter(self):
        """Get Gemini AI adapter (Phase 3)."""
        if self._gemini_adapter is None:
            self._gemini_adapter = self._create_gemini_adapter()
        return self._gemini_adapter
    
    @property
    def telegram_adapter(self):
        """Get Telegram bot adapter (Phase 3b)."""
        if self._telegram_adapter is None:
            self._telegram_adapter = self._create_telegram_adapter()
        return self._telegram_adapter
    
    @property
    def database_manager(self):
        """Get legacy DatabaseManager (for backward compatibility)."""
        if self._database_manager is None:
            self._database_manager = self._create_database_manager()
        return self._database_manager
    
    @property
    def notification_adapter(self):
        """Get notification adapter (Phase 4A)."""
        if self._notification_adapter is None:
            self._notification_adapter = self._create_notification_adapter()
        return self._notification_adapter
    
    @property
    def cache_adapter(self):
        """Get cache adapter (Phase 4B)."""
        if self._cache_adapter is None:
            self._cache_adapter = self._create_cache_adapter()
        return self._cache_adapter
    
    @property
    def database_adapter(self):
        """Get database adapter (Phase 4C)."""
        if self._database_adapter is None:
            self._database_adapter = self._create_database_adapter()
        return self._database_adapter
    
    @property
    def use_app_layer(self) -> bool:
        """Check if application layer is enabled."""
        return getattr(self.settings, 'use_app_layer', False)
    
    @property
    def use_notification_port(self) -> bool:
        """Check if NotificationPort is enabled (Phase 4A)."""
        import os
        return os.getenv("USE_NOTIFICATION_PORT", "false").lower() == "true"
    
    @property
    def use_cache_port(self) -> bool:
        """Check if CachePort is enabled (Phase 4B)."""
        import os
        return os.getenv("USE_CACHE_PORT", "false").lower() == "true"
    
    @property
    def use_database_port(self) -> bool:
        """Check if DatabasePort is enabled (Phase 4C)."""
        import os
        return os.getenv("USE_DATABASE_PORT", "false").lower() == "true"
    
    @property
    def use_telegram_port(self) -> bool:
        """Check if TelegramPort is enabled (Phase 4D)."""
        import os
        return os.getenv("USE_TELEGRAM_PORT", "false").lower() == "true"
    
    @property
    def use_onchain_port(self) -> bool:
        """Check if OnChainDataPort is enabled (Phase 5)."""
        import os
        return os.getenv("USE_ONCHAIN_PORT", "false").lower() == "true"
    
    @property
    def onchain_adapter(self):
        """Get on-chain data adapter (Phase 5)."""
        if self._onchain_adapter is None:
            self._onchain_adapter = self._create_onchain_adapter()
        return self._onchain_adapter
    
    @property
    def use_market_intel_port(self) -> bool:
        """Check if MarketIntelPort is enabled (Phase 5)."""
        import os
        return os.getenv("USE_MARKET_INTEL_PORT", "false").lower() == "true"
    
    @property
    def use_execution_port(self) -> bool:
        """Check if ExecutionPort is enabled (Phase 5)."""
        import os
        return os.getenv("USE_EXECUTION_PORT", "false").lower() == "true"
    
    @property
    def use_risk_control_port(self) -> bool:
        """Check if RiskControlPort is enabled (Phase 5)."""
        import os
        return os.getenv("USE_RISK_CONTROL_PORT", "false").lower() == "true"
    
    @property
    def use_derivatives_port(self) -> bool:
        """Check if DerivativesPort is enabled (Phase 5)."""
        import os
        return os.getenv("USE_DERIVATIVES_PORT", "false").lower() == "true"
    
    @property
    def use_portfolio_port(self) -> bool:
        """Check if PortfolioPort is enabled (Phase 5)."""
        import os
        return os.getenv("USE_PORTFOLIO_PORT", "false").lower() == "true"
    
    @property
    def use_optimization_port(self) -> bool:
        """Check if OptimizationPort is enabled (Phase 5)."""
        import os
        return os.getenv("USE_OPTIMIZATION_PORT", "false").lower() == "true"
    
    @property
    def market_intel_adapter(self):
        """Get market intelligence adapter (Phase 5)."""
        if self._market_intel_adapter is None:
            self._market_intel_adapter = self._create_market_intel_adapter()
        return self._market_intel_adapter
    
    @property
    def execution_adapter(self):
        """Get execution adapter (Phase 5)."""
        if self._execution_adapter is None:
            self._execution_adapter = self._create_execution_adapter()
        return self._execution_adapter
    
    @property
    def risk_control_adapter(self):
        """Get risk control adapter (Phase 5)."""
        if self._risk_control_adapter is None:
            self._risk_control_adapter = self._create_risk_control_adapter()
        return self._risk_control_adapter
    
    @property
    def derivatives_adapter(self):
        """Get derivatives adapter (Phase 5)."""
        if self._derivatives_adapter is None:
            self._derivatives_adapter = self._create_derivatives_adapter()
        return self._derivatives_adapter
    
    @property
    def portfolio_adapter(self):
        """Get portfolio adapter (Phase 5)."""
        if self._portfolio_adapter is None:
            self._portfolio_adapter = self._create_portfolio_adapter()
        return self._portfolio_adapter
    
    @property
    def optimization_adapter(self):
        """Get optimization adapter (Phase 5)."""
        if self._optimization_adapter is None:
            self._optimization_adapter = self._create_optimization_adapter()
        return self._optimization_adapter
    
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
    
    def _create_kraken_adapter(self):
        """Create Kraken exchange adapter (Phase 3)."""
        try:
            from src.omnix.infrastructure.adapters.kraken_adapter import KrakenAdapter
            logger.info("Container: Initializing KrakenAdapter...")
            adapter = KrakenAdapter()
            if hasattr(adapter, 'health_check'):
                health = adapter.health_check()
                if health.get('connected', False):
                    logger.info("Container: KrakenAdapter initialized - connected to Kraken API")
                else:
                    logger.warning("Container: KrakenAdapter initialized but not connected to Kraken API")
            else:
                logger.info("Container: KrakenAdapter initialized (no health_check available)")
            return adapter
        except ImportError:
            logger.warning("Container: KrakenAdapter not available (import failed)")
            return None
        except Exception as e:
            logger.error(f"Container: Failed to initialize KrakenAdapter: {e}")
            return None
    
    def _create_gemini_adapter(self):
        """Create Gemini AI adapter (Phase 3)."""
        try:
            from src.omnix.infrastructure.adapters.gemini_adapter import GeminiAdapter
            logger.info("Container: Initializing GeminiAdapter...")
            adapter = GeminiAdapter()
            if hasattr(adapter, 'health_check'):
                health = adapter.health_check()
                provider = health.get('provider', 'unknown')
                if health.get('healthy', False):
                    logger.info(f"Container: GeminiAdapter initialized - active provider: {provider}")
                else:
                    logger.warning(f"Container: GeminiAdapter initialized but unhealthy - provider: {provider}")
            else:
                logger.info("Container: GeminiAdapter initialized (no health_check available)")
            return adapter
        except ImportError:
            logger.warning("Container: GeminiAdapter not available (import failed)")
            return None
        except Exception as e:
            logger.error(f"Container: Failed to initialize GeminiAdapter: {e}")
            return None
    
    def _create_telegram_adapter(self):
        """Create Telegram bot adapter (Phase 3b)."""
        try:
            from src.omnix.infrastructure.adapters.telegram_adapter import TelegramBotAdapter
            logger.info("Container: Initializing TelegramBotAdapter...")
            db_manager = self.database_manager
            adapter = TelegramBotAdapter(_db_manager=db_manager)
            logger.info("Container: TelegramBotAdapter initialized")
            return adapter
        except ImportError:
            logger.warning("Container: TelegramBotAdapter not available (import failed)")
            return None
        except Exception as e:
            logger.error(f"Container: Failed to initialize TelegramBotAdapter: {e}")
            return None
    
    def _create_database_manager(self):
        """Create legacy DatabaseManager (for backward compatibility)."""
        try:
            from omnix_services.database_service import DatabaseManager
            return DatabaseManager()
        except ImportError:
            logger.warning("Container: DatabaseManager not available")
            return None
    
    def _create_notification_adapter(self):
        """Create notification adapter (Phase 4A)."""
        try:
            from src.omnix.infrastructure.adapters.notification_adapter import NotificationAdapter
            logger.info("Container: Initializing NotificationAdapter...")
            telegram_adapter = self.telegram_adapter
            adapter = NotificationAdapter(telegram_adapter=telegram_adapter)
            if hasattr(adapter, 'health_check'):
                health = adapter.health_check()
                if health.get('healthy', False):
                    logger.info("Container: NotificationAdapter initialized - healthy")
                else:
                    logger.warning("Container: NotificationAdapter initialized but unhealthy")
            else:
                logger.info("Container: NotificationAdapter initialized")
            return adapter
        except ImportError:
            logger.warning("Container: NotificationAdapter not available (import failed)")
            return None
        except Exception as e:
            logger.error(f"Container: Failed to initialize NotificationAdapter: {e}")
            return None
    
    def _create_cache_adapter(self):
        """Create cache adapter (Phase 4B)."""
        try:
            from src.omnix.infrastructure.adapters.cache_adapter import CacheAdapter
            logger.info("Container: Initializing CacheAdapter...")
            adapter = CacheAdapter()
            if hasattr(adapter, 'health_check'):
                health = adapter.health_check()
                if health.get('connected', False):
                    logger.info("Container: CacheAdapter initialized - connected to Redis")
                else:
                    logger.warning("Container: CacheAdapter initialized but not connected to Redis")
            else:
                logger.info("Container: CacheAdapter initialized")
            return adapter
        except ImportError:
            logger.warning("Container: CacheAdapter not available (import failed)")
            return None
        except Exception as e:
            logger.error(f"Container: Failed to initialize CacheAdapter: {e}")
            return None
    
    def _create_database_adapter(self):
        """Create database adapter (Phase 4C)."""
        try:
            from src.omnix.infrastructure.adapters.database_adapter import DatabaseAdapter
            logger.info("Container: Initializing DatabaseAdapter...")
            adapter = DatabaseAdapter()
            if hasattr(adapter, 'health_check'):
                health = adapter.health_check()
                if health.get('connected', False):
                    logger.info("Container: DatabaseAdapter initialized - connected to PostgreSQL")
                else:
                    logger.warning("Container: DatabaseAdapter initialized but not connected to PostgreSQL")
            else:
                logger.info("Container: DatabaseAdapter initialized")
            return adapter
        except ImportError:
            logger.warning("Container: DatabaseAdapter not available (import failed)")
            return None
        except Exception as e:
            logger.error(f"Container: Failed to initialize DatabaseAdapter: {e}")
            return None
    
    def _create_onchain_adapter(self):
        """Create on-chain data adapter (Phase 5)."""
        try:
            from src.omnix.infrastructure.adapters.onchain import OnChainDataAdapter, BlockchainInfoProvider
            logger.info("Container: Initializing OnChainDataAdapter...")
            
            legacy_service = None
            try:
                from omnix_services.monitoring.advanced_intelligence import MarketIntelligenceSystem
                legacy_service = MarketIntelligenceSystem()
            except Exception:
                pass
            
            provider = BlockchainInfoProvider()
            adapter = OnChainDataAdapter(
                blockchain_info_provider=provider,
                legacy_service=legacy_service
            )
            
            logger.info(f"Container: OnChainDataAdapter initialized (enabled={self.use_onchain_port})")
            return adapter
        except ImportError as e:
            logger.warning(f"Container: OnChainDataAdapter not available (import failed): {e}")
            return None
        except Exception as e:
            logger.error(f"Container: Failed to initialize OnChainDataAdapter: {e}")
            return None
    
    def _create_market_intel_adapter(self):
        """Create market intelligence adapter (Phase 5)."""
        try:
            from src.omnix.infrastructure.adapters.market_intel_adapter import MarketIntelAdapter
            logger.info("Container: Initializing MarketIntelAdapter...")
            adapter = MarketIntelAdapter()
            if hasattr(adapter, 'health_check'):
                health = adapter.health_check()
                if health.get('healthy', False):
                    logger.info("Container: MarketIntelAdapter initialized - healthy")
                else:
                    logger.warning("Container: MarketIntelAdapter initialized but unhealthy")
            else:
                logger.info("Container: MarketIntelAdapter initialized")
            return adapter
        except ImportError as e:
            logger.warning(f"Container: MarketIntelAdapter not available (import failed): {e}")
            return None
        except Exception as e:
            logger.error(f"Container: Failed to initialize MarketIntelAdapter: {e}")
            return None
    
    def _create_execution_adapter(self):
        """Create execution adapter (Phase 5)."""
        try:
            from src.omnix.infrastructure.adapters.execution_adapter import ExecutionAdapter
            logger.info("Container: Initializing ExecutionAdapter...")
            adapter = ExecutionAdapter()
            if hasattr(adapter, 'health_check'):
                health = adapter.health_check()
                if health.get('healthy', False):
                    logger.info("Container: ExecutionAdapter initialized - healthy")
                else:
                    logger.warning("Container: ExecutionAdapter initialized but unhealthy")
            else:
                logger.info("Container: ExecutionAdapter initialized")
            return adapter
        except ImportError as e:
            logger.warning(f"Container: ExecutionAdapter not available (import failed): {e}")
            return None
        except Exception as e:
            logger.error(f"Container: Failed to initialize ExecutionAdapter: {e}")
            return None
    
    def _create_risk_control_adapter(self):
        """Create risk control adapter (Phase 5) - placeholder."""
        logger.warning("Container: RiskControlAdapter not yet implemented")
        return None
    
    def _create_derivatives_adapter(self):
        """Create derivatives adapter (Phase 5) - placeholder."""
        logger.warning("Container: DerivativesAdapter not yet implemented")
        return None
    
    def _create_portfolio_adapter(self):
        """Create portfolio adapter (Phase 5) - placeholder."""
        logger.warning("Container: PortfolioAdapter not yet implemented")
        return None
    
    def _create_optimization_adapter(self):
        """Create optimization adapter (Phase 5) - placeholder."""
        logger.warning("Container: OptimizationAdapter not yet implemented")
        return None
    
    @classmethod
    def create(cls, lazy: bool = True) -> "Container":
        logger.info(f"Container: Creating new DI Container (lazy={lazy})")
        container = cls()
        if not lazy:
            logger.info("Container: Eager initialization - loading database and cache...")
            _ = container.database
            _ = container.cache
            container._initialized = True
            logger.info("Container: Eager initialization complete")
        return container
    
    def health_check(self) -> dict:
        health = {
            'database': self.database.is_connected() if hasattr(self.database, 'is_connected') else False,
            'cache': self.cache.is_connected() if hasattr(self.cache, 'is_connected') else False,
            'settings': self.settings is not None,
            'trading_adapter': self.trading_adapter is not None,
            'risk_adapter': self.risk_adapter is not None,
            'coherence_adapter': self.coherence_adapter is not None,
            'kraken_adapter': self._kraken_adapter is not None,
            'gemini_adapter': self._gemini_adapter is not None,
            'telegram_adapter': self._telegram_adapter is not None,
            'notification_adapter': self._notification_adapter is not None,
            'cache_adapter': self._cache_adapter is not None,
            'database_adapter': self._database_adapter is not None,
            'database_manager': self._database_manager is not None,
            'onchain_adapter': self._onchain_adapter is not None,
            'market_intel_adapter': self._market_intel_adapter is not None,
            'execution_adapter': self._execution_adapter is not None,
            'use_app_layer': self.use_app_layer,
            'use_notification_port': self.use_notification_port,
            'use_cache_port': self.use_cache_port,
            'use_database_port': self.use_database_port,
            'use_telegram_port': self.use_telegram_port,
            'use_onchain_port': self.use_onchain_port,
            'use_market_intel_port': self.use_market_intel_port,
            'use_execution_port': self.use_execution_port,
        }
        
        if self._kraken_adapter is not None and hasattr(self._kraken_adapter, 'health_check'):
            kraken_health = self._kraken_adapter.health_check()
            health['kraken_connected'] = kraken_health.get('connected', False)
        
        if self._gemini_adapter is not None and hasattr(self._gemini_adapter, 'health_check'):
            gemini_health = self._gemini_adapter.health_check()
            health['gemini_provider'] = gemini_health.get('provider', 'unknown')
        
        if self._telegram_adapter is not None and hasattr(self._telegram_adapter, 'health_check'):
            telegram_health = self._telegram_adapter.health_check()
            health['telegram_running'] = telegram_health.get('running', False)
        
        return health
    
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
