"""
OMNIX V7.0 Centralized Settings
================================
Phase 1: Bootstrap & Config - Centralized configuration.

All environment variables are consolidated here. This replaces scattered os.getenv() calls
throughout the codebase while maintaining 100% backward compatibility via re-exports.

Supports Pydantic BaseSettings when available, with fallback to manual implementation.

Usage:
    from src.omnix.config import get_settings
    settings = get_settings()
    print(settings.database_url)
"""

from functools import lru_cache
from typing import Optional
import os


def _create_pydantic_settings_class():
    """Create Pydantic-based Settings class if available."""
    try:
        from pydantic_settings import BaseSettings
        from pydantic import Field
    except ImportError:
        try:
            from pydantic import BaseSettings, Field
        except ImportError:
            return None
    
    class PydanticSettings(BaseSettings):
        database_url: str = Field(default="", validation_alias="DATABASE_URL")
        postgres_url: Optional[str] = Field(default=None, validation_alias="POSTGRES_URL")
        database_public_url: Optional[str] = Field(default=None, validation_alias="DATABASE_PUBLIC_URL")
        redis_url: str = Field(default="", validation_alias="REDIS_URL")
        
        kraken_api_key: str = Field(default="", validation_alias="KRAKEN_API_KEY")
        kraken_api_secret: str = Field(default="", validation_alias="KRAKEN_API_SECRET")
        
        telegram_bot_token: str = Field(default="", validation_alias="TELEGRAM_BOT_TOKEN")
        telegram_webhook_url: Optional[str] = Field(default=None, validation_alias="TELEGRAM_WEBHOOK_URL")
        
        gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
        openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
        anthropic_api_key: str = Field(default="", validation_alias="ANTHROPIC_API_KEY")
        
        alpha_vantage_api_key: str = Field(default="", validation_alias="ALPHA_VANTAGE_API_KEY")
        finnhub_api_key: str = Field(default="", validation_alias="FINNHUB_API_KEY")
        tavily_api_key: str = Field(default="", validation_alias="TAVILY_API_KEY")
        
        stripe_secret_key: str = Field(default="", validation_alias="STRIPE_SECRET_KEY")
        session_secret: str = Field(default="dev-secret-change-in-production", validation_alias="SESSION_SECRET")
        dashboard_api_key: Optional[str] = Field(default=None, validation_alias="DASHBOARD_API_KEY")
        dashboard_allowed_origins: str = Field(default="", validation_alias="DASHBOARD_ALLOWED_ORIGINS")
        
        trading_profile: str = Field(default="PRODUCTION_STABLE", validation_alias="TRADING_PROFILE")
        paper_mode: bool = Field(default=True, validation_alias="PAPER_MODE")
        max_trade_usd: float = Field(default=20000.0, validation_alias="MAX_TRADE_USD")
        drawdown_limit: float = Field(default=0.15, validation_alias="DRAWDOWN_LIMIT")
        
        enable_ares_v1: bool = Field(default=True, validation_alias="ENABLE_ARES_V1")
        enable_ares_v2: bool = Field(default=True, validation_alias="ENABLE_ARES_V2")
        
        db_pool_min: int = Field(default=2, validation_alias="DB_POOL_MIN")
        db_pool_max: int = Field(default=10, validation_alias="DB_POOL_MAX")
        use_unified_gateway: bool = Field(default=False, validation_alias="USE_UNIFIED_GATEWAY")
        disable_auto_migrations: bool = Field(default=False, validation_alias="DISABLE_AUTO_MIGRATIONS")
        
        railway_environment: Optional[str] = Field(default=None, validation_alias="RAILWAY_ENVIRONMENT")
        railway_project_id: Optional[str] = Field(default=None, validation_alias="RAILWAY_PROJECT_ID")
        
        repl_id: Optional[str] = Field(default=None, validation_alias="REPL_ID")
        replit_dev_domain: str = Field(default="localhost", validation_alias="REPLIT_DEV_DOMAIN")
        replit_domains: str = Field(default="", validation_alias="REPLIT_DOMAINS")
        
        log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
        port: int = Field(default=5000, validation_alias="PORT")
        web_concurrency: int = Field(default=4, validation_alias="WEB_CONCURRENCY")
        
        omnix_api_url: str = Field(default="http://localhost:5000", validation_alias="OMNIX_API_URL")
        
        model_config = {"env_file": ".env", "extra": "ignore", "populate_by_name": True}
        
        @property
        def is_railway(self) -> bool:
            return bool(self.railway_environment or self.railway_project_id)
        
        @property
        def is_replit(self) -> bool:
            return bool(self.repl_id)
        
        @property
        def effective_database_url(self) -> str:
            return self.database_url or self.postgres_url or self.database_public_url or ""
        
        def to_dict(self) -> dict:
            return {
                'database_url': '***' if self.effective_database_url else '',
                'redis_url': '***' if self.redis_url else '',
                'trading_profile': self.trading_profile,
                'paper_mode': self.paper_mode,
                'is_railway': self.is_railway,
                'is_replit': self.is_replit,
                'log_level': self.log_level,
                'port': self.port,
            }
    
    return PydanticSettings


class Settings:
    """
    Centralized settings for OMNIX V6.5.4d INSTITUTIONAL+.
    
    This fallback class works without Pydantic dependency.
    Uses property-based lazy loading for efficiency.
    """
    
    def __init__(self):
        self._cache: dict = {}
    
    def _get(self, key: str, default: str = "") -> str:
        if key not in self._cache:
            self._cache[key] = os.environ.get(key, default)
        return self._cache[key]
    
    def _get_bool(self, key: str, default: bool = False) -> bool:
        val = self._get(key, str(default)).lower()
        return val in ('true', '1', 'yes')
    
    def _get_int(self, key: str, default: int) -> int:
        try:
            return int(self._get(key, str(default)))
        except ValueError:
            return default
    
    def _get_float(self, key: str, default: float) -> float:
        try:
            return float(self._get(key, str(default)))
        except ValueError:
            return default
    
    @property
    def database_url(self) -> str:
        return self._get('DATABASE_URL') or self._get('POSTGRES_URL') or self._get('DATABASE_PUBLIC_URL')
    
    @property
    def effective_database_url(self) -> str:
        return self.database_url
    
    @property
    def redis_url(self) -> str:
        return self._get('REDIS_URL')
    
    @property
    def kraken_api_key(self) -> str:
        return self._get('KRAKEN_API_KEY')
    
    @property
    def kraken_api_secret(self) -> str:
        return self._get('KRAKEN_API_SECRET')
    
    @property
    def telegram_bot_token(self) -> str:
        return self._get('TELEGRAM_BOT_TOKEN')
    
    @property
    def telegram_webhook_url(self) -> Optional[str]:
        val = self._get('TELEGRAM_WEBHOOK_URL')
        return val if val else None
    
    @property
    def gemini_api_key(self) -> str:
        return self._get('GEMINI_API_KEY')
    
    @property
    def openai_api_key(self) -> str:
        return self._get('OPENAI_API_KEY')
    
    @property
    def anthropic_api_key(self) -> str:
        return self._get('ANTHROPIC_API_KEY')
    
    @property
    def alpha_vantage_api_key(self) -> str:
        return self._get('ALPHA_VANTAGE_API_KEY')
    
    @property
    def finnhub_api_key(self) -> str:
        return self._get('FINNHUB_API_KEY')
    
    @property
    def tavily_api_key(self) -> str:
        return self._get('TAVILY_API_KEY')
    
    @property
    def stripe_secret_key(self) -> str:
        return self._get('STRIPE_SECRET_KEY')
    
    @property
    def session_secret(self) -> str:
        return self._get('SESSION_SECRET', 'dev-secret-change-in-production')
    
    @property
    def dashboard_api_key(self) -> Optional[str]:
        val = self._get('DASHBOARD_API_KEY')
        return val if val else None
    
    @property
    def dashboard_allowed_origins(self) -> str:
        return self._get('DASHBOARD_ALLOWED_ORIGINS')
    
    @property
    def trading_profile(self) -> str:
        return self._get('TRADING_PROFILE', 'PRODUCTION_STABLE')
    
    @property
    def paper_mode(self) -> bool:
        return self._get_bool('PAPER_MODE', True)
    
    @property
    def max_trade_usd(self) -> float:
        return self._get_float('MAX_TRADE_USD', 20000.0)
    
    @property
    def drawdown_limit(self) -> float:
        return self._get_float('DRAWDOWN_LIMIT', 0.15)
    
    @property
    def enable_ares_v1(self) -> bool:
        return self._get_bool('ENABLE_ARES_V1', True)
    
    @property
    def enable_ares_v2(self) -> bool:
        return self._get_bool('ENABLE_ARES_V2', True)
    
    @property
    def db_pool_min(self) -> int:
        return self._get_int('DB_POOL_MIN', 2)
    
    @property
    def db_pool_max(self) -> int:
        return self._get_int('DB_POOL_MAX', 10)
    
    @property
    def use_unified_gateway(self) -> bool:
        return self._get_bool('USE_UNIFIED_GATEWAY', False)
    
    @property
    def disable_auto_migrations(self) -> bool:
        return self._get_bool('DISABLE_AUTO_MIGRATIONS', False)
    
    @property
    def is_railway(self) -> bool:
        return bool(self._get('RAILWAY_ENVIRONMENT') or self._get('RAILWAY_PROJECT_ID'))
    
    @property
    def is_replit(self) -> bool:
        return bool(self._get('REPL_ID'))
    
    @property
    def replit_dev_domain(self) -> str:
        return self._get('REPLIT_DEV_DOMAIN', 'localhost')
    
    @property
    def replit_domains(self) -> str:
        return self._get('REPLIT_DOMAINS')
    
    @property
    def log_level(self) -> str:
        return self._get('LOG_LEVEL', 'INFO')
    
    @property
    def port(self) -> int:
        return self._get_int('PORT', 5000)
    
    @property
    def web_concurrency(self) -> int:
        import multiprocessing
        default = multiprocessing.cpu_count() * 2 + 1
        return self._get_int('WEB_CONCURRENCY', default)
    
    @property
    def omnix_api_url(self) -> str:
        return self._get('OMNIX_API_URL', 'http://localhost:5000')
    
    def to_dict(self) -> dict:
        return {
            'database_url': '***' if self.database_url else '',
            'redis_url': '***' if self.redis_url else '',
            'trading_profile': self.trading_profile,
            'paper_mode': self.paper_mode,
            'is_railway': self.is_railway,
            'is_replit': self.is_replit,
            'log_level': self.log_level,
            'port': self.port,
        }
    
    def __repr__(self) -> str:
        return f"Settings(trading_profile={self.trading_profile}, paper_mode={self.paper_mode})"


_PydanticSettings = _create_pydantic_settings_class()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get centralized settings instance.
    
    Uses Pydantic BaseSettings if available, falls back to manual implementation.
    Instance is cached for performance.
    """
    if _PydanticSettings is not None:
        try:
            return _PydanticSettings()  # type: ignore
        except Exception:
            pass
    return Settings()


def clear_settings_cache():
    """Clear the settings cache. Useful for testing."""
    get_settings.cache_clear()
