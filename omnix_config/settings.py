"""
OMNIX Configuration - Centralized Settings
Enterprise Grade | 50K+ users scalability
"""

# ============================================================
# VERSION CONTROL - SINGLE SOURCE OF TRUTH
# ============================================================
VERSION = "6.5.4"
VERSION_NAME = "INSTITUTIONAL+"
VERSION_BANNER = f"V{VERSION} {VERSION_NAME}"
# ============================================================

import os
from dataclasses import dataclass
from typing import Optional

# Import centralized env config
from omnix_config.env_manager import env_config


@dataclass
class RedisConfig:
    """Configuración Redis Cache"""
    url: Optional[str] = env_config.get('REDIS_URL')  # Priority: Full URL (Railway)
    host: str = env_config.get('REDIS_HOST', default='localhost')
    port: int = env_config.get('REDIS_PORT', default=6379, cast_type=int)
    db: int = env_config.get('REDIS_DB', default=0, cast_type=int)
    password: Optional[str] = env_config.get('REDIS_PASSWORD')
    ttl: int = 300  # 5 minutos default


@dataclass
class DatabaseConfig:
    """Configuración PostgreSQL"""
    url: str = env_config.get('DATABASE_URL', default='')
    pool_size: int = 20
    max_overflow: int = 40
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class AIConfig:
    """Configuración servicios IA"""
    openai_key: str = env_config.get('OPENAI_API_KEY', default='')
    gemini_key: str = env_config.get('GEMINI_API_KEY', default='')
    primary_model: str = 'gemini-2.0-flash-exp'
    fallback_models: Optional[list] = None
    max_retries: int = 1
    timeout: int = 10
    
    def __post_init__(self):
        if self.fallback_models is None:
            self.fallback_models = ['gpt-4o', 'claude-sonnet-4-20250514']


@dataclass
class TradingConfig:
    """Configuración Trading"""
    kraken_key: str = env_config.get('KRAKEN_API_KEY', default='')
    kraken_secret: str = env_config.get('KRAKEN_API_SECRET', default='')
    max_trade_size: float = 1000.0
    min_trade_size: float = 10.0
    rate_limit: int = 15  # requests per minute


@dataclass
class CeleryConfig:
    """Configuración Celery Workers"""
    broker_url: str = env_config.get('CELERY_BROKER_URL', default='redis://localhost:6379/1')
    result_backend: str = env_config.get('CELERY_RESULT_BACKEND', default='redis://localhost:6379/2')
    task_serializer: str = 'json'
    accept_content: Optional[list] = None
    timezone: str = 'UTC'
    
    def __post_init__(self):
        if self.accept_content is None:
            self.accept_content = ['json']


@dataclass
class MonitoringConfig:
    """Configuración Monitoring"""
    sentry_dsn: Optional[str] = env_config.get('SENTRY_DSN')
    log_level: str = env_config.get('LOG_LEVEL', default='INFO')
    metrics_enabled: bool = True


class Settings:
    """Settings centralizados OMNIX V6.0 Enterprise - Powered by env_manager.py"""
    
    redis = RedisConfig()
    database = DatabaseConfig()
    ai = AIConfig()
    trading = TradingConfig()
    celery = CeleryConfig()
    monitoring = MonitoringConfig()
    
    # General
    ENV: str = env_config.get('ENVIRONMENT', default='development')
    DEBUG: bool = env_config.get('DEBUG', default='false', cast_type=bool)
    SECRET_KEY: str = env_config.get('SECRET_KEY', default='omnix-enterprise-secret-key-change-in-prod')
    
    # Telegram
    TELEGRAM_TOKEN: str = env_config.get_required('TELEGRAM_BOT_TOKEN')
    TELEGRAM_ADMIN_ID: str = env_config.get('TELEGRAM_ADMIN_USER_ID', default='7014748854')  # TODO: Move to Replit Secrets
    
    # Rate Limiting
    RATE_LIMIT_PER_USER: int = 60  # requests per minute
    RATE_LIMIT_PER_IP: int = 100
    
    # Sharia Compliance
    SHARIA_COMPLIANCE_ENABLED: bool = True
    
    # Post-Quantum Cryptography
    PQC_ENABLED: bool = True
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production"""
        return cls.ENV == 'production'
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration"""
        errors = []
        
        if not cls.TELEGRAM_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        
        if not cls.ai.openai_key and not cls.ai.gemini_key:
            errors.append("At least one AI API key required (OpenAI or Gemini)")
        
        if not cls.trading.kraken_key or not cls.trading.kraken_secret:
            errors.append("Kraken API credentials required for trading")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")


# Global settings instance
settings = Settings()
