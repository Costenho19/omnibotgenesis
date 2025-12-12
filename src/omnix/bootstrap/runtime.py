"""
OMNIX V7.0 Bootstrap Runtime
=============================
Phase 1: Bootstrap & Config - Environment loading and service wiring.

This module handles the bootstrap sequence for OMNIX:
1. Environment validation
2. Logging configuration
3. Redis cache priming
4. Database connection verification
5. Service initialization

Usage:
    from src.omnix.bootstrap import bootstrap_omnix
    container = bootstrap_omnix()
"""

import logging
import sys
from typing import Optional
from dataclasses import dataclass

from .container import Container, get_container

logger = logging.getLogger(__name__)


@dataclass
class BootstrapResult:
    success: bool
    container: Optional[Container]
    errors: list[str]
    warnings: list[str]
    
    def __bool__(self) -> bool:
        return self.success


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)


def validate_environment() -> tuple[bool, list[str], list[str]]:
    from src.omnix.config.settings import get_settings
    
    settings = get_settings()
    errors = []
    warnings = []
    
    if not settings.database_url:
        errors.append("DATABASE_URL is not set")
    
    if not settings.redis_url:
        warnings.append("REDIS_URL is not set - caching will be disabled")
    
    if not settings.telegram_bot_token:
        warnings.append("TELEGRAM_BOT_TOKEN is not set - Telegram bot will be disabled")
    
    if not settings.gemini_api_key and not settings.openai_api_key:
        warnings.append("No AI API keys configured - AI features will be limited")
    
    if settings.is_railway:
        logger.info("Running in Railway environment")
    elif settings.is_replit:
        logger.info("Running in Replit environment")
    else:
        logger.info("Running in local/unknown environment")
    
    return len(errors) == 0, errors, warnings


def prime_redis_cache(container: Container) -> bool:
    try:
        cache = container.cache
        if not cache.is_connected():
            logger.warning("Redis cache not connected, skipping priming")
            return False
        
        cache.set("omnix:bootstrap:timestamp", str(__import__('time').time()), ttl=3600)
        logger.info("Redis cache primed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to prime Redis cache: {e}")
        return False


def verify_database(container: Container) -> bool:
    try:
        db = container.database
        if not db.is_connected():
            logger.warning("Database not connected")
            return False
        
        result = db.execute_one("SELECT 1")
        if result:
            logger.info("Database connection verified")
            return True
        return False
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return False


def bootstrap_omnix(
    configure_logs: bool = True,
    validate_env: bool = True,
    prime_cache: bool = True,
    verify_db: bool = True,
    fail_fast: bool = False
) -> BootstrapResult:
    """
    Bootstrap the OMNIX application.
    
    Args:
        configure_logs: Whether to configure logging
        validate_env: Whether to validate environment variables
        prime_cache: Whether to prime the Redis cache
        verify_db: Whether to verify database connection
        fail_fast: Whether to fail immediately on errors
    
    Returns:
        BootstrapResult with container and status
    """
    errors = []
    warnings = []
    
    logger.info("=" * 60)
    logger.info("OMNIX V6.5.4d INSTITUTIONAL+ Bootstrap Sequence")
    logger.info("=" * 60)
    
    from src.omnix.config.settings import get_settings
    settings = get_settings()
    
    if configure_logs:
        configure_logging(settings.log_level)
    
    if validate_env:
        valid, env_errors, env_warnings = validate_environment()
        errors.extend(env_errors)
        warnings.extend(env_warnings)
        
        if not valid and fail_fast:
            logger.error(f"Environment validation failed: {env_errors}")
            return BootstrapResult(
                success=False,
                container=None,
                errors=errors,
                warnings=warnings
            )
    
    container = get_container()
    
    if verify_db:
        if not verify_database(container):
            if fail_fast:
                errors.append("Database verification failed")
                return BootstrapResult(
                    success=False,
                    container=container,
                    errors=errors,
                    warnings=warnings
                )
            else:
                warnings.append("Database verification failed - some features may be unavailable")
    
    if prime_cache:
        if not prime_redis_cache(container):
            warnings.append("Redis cache priming failed - caching may be degraded")
    
    health = container.health_check()
    logger.info(f"Bootstrap complete. Health: {health}")
    logger.info(f"Trading Profile: {settings.trading_profile}")
    logger.info(f"Paper Mode: {settings.paper_mode}")
    logger.info("=" * 60)
    
    for warning in warnings:
        logger.warning(f"Bootstrap warning: {warning}")
    
    return BootstrapResult(
        success=True,
        container=container,
        errors=errors,
        warnings=warnings
    )


def quick_bootstrap() -> Container:
    result = bootstrap_omnix(
        configure_logs=False,
        validate_env=False,
        prime_cache=False,
        verify_db=False
    )
    return result.container or get_container()
