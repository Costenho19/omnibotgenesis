#!/usr/bin/env python3
"""
OMNIX V7.0 Main Entry Point
============================
Phase 4: Modular entrypoint for the main OMNIX bot and services.

This module serves as the new modular entrypoint for OMNIX, replacing the
monolithic main.py. It uses the DI Container and delegates to appropriate
services based on the USE_APP_LAYER feature flag.

Usage:
    # Direct execution
    python -m src.omnix.bootstrap.main_entry
    
    # From legacy wrapper (main.py)
    from src.omnix.bootstrap.main_entry import run_omnix
    run_omnix()
"""

import os
import sys
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)


def clean_pycache() -> int:
    """Clean Python cache files before imports."""
    import shutil
    
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    deleted_count = 0
    
    for root, dirs, files in os.walk(current_dir):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                deleted_count += 1
            except Exception:
                pass
        
        for file in files:
            if file.endswith('.pyc'):
                pyc_path = os.path.join(root, file)
                try:
                    os.remove(pyc_path)
                    deleted_count += 1
                except Exception:
                    pass
    
    return deleted_count


def fix_database_url() -> Optional[str]:
    """Fix DATABASE_URL if it contains malformed prefix."""
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        if db_url.startswith('DATABASE_URL='):
            db_url = db_url[len('DATABASE_URL='):]
            os.environ['DATABASE_URL'] = db_url
            logger.warning("FIX: Removed 'DATABASE_URL=' prefix from value")
        elif db_url.startswith('DATABASE_URL:'):
            db_url = db_url[len('DATABASE_URL:'):]
            os.environ['DATABASE_URL'] = db_url
            logger.warning("FIX: Removed 'DATABASE_URL:' prefix from value")
    return db_url


def run_migrations(db_url: str) -> dict:
    """Run pending database migrations."""
    try:
        from omnix_services.database_service.migrations import MigrationRunner, MIGRATIONS
        
        logger.info("Running database migrations...")
        migration_runner = MigrationRunner(db_url)
        result = migration_runner.run_pending_migrations(MIGRATIONS)
        
        if result['success']:
            if result['applied'] > 0:
                logger.info(f"Migrations applied: {result['applied']}")
            else:
                logger.info("Database up to date - no pending migrations")
        else:
            logger.error(f"Migration errors: {result['errors']}")
        
        return result
    except ImportError as e:
        logger.warning(f"Migration system not available: {e}")
        return {'success': True, 'applied': 0, 'skipped': True}
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        return {'success': False, 'errors': [str(e)]}


def initialize_services_legacy():
    """
    Initialize OMNIX services using legacy path.
    
    This imports and initializes all services from the legacy modules.
    Used when USE_APP_LAYER=false (default).
    """
    from omnix_config import env_config, VERSION_BANNER
    
    logger.info("=" * 70)
    logger.info(f"OMNIX {VERSION_BANNER} - Legacy Bootstrap Path")
    logger.info("=" * 70)
    
    from omnix_services.market_data import (
        fetch_market_snapshot,
        get_fear_greed_index,
    )
    from omnix_services.trading_service.analyzers import AdvancedOrderBookAnalyzer
    from omnix_services.voice_service import VoiceEngine, initialize_voice_engine
    from omnix_services.concurrency import (
        IntelligentCacheSystem,
        OptimizedConcurrencyManager,
        ScalableResourceManager
    )
    from omnix_services.analytics import AutoFibonacciAnalyzer, VolumeProfileAnalyzer
    from omnix_services.market_data.intelligence import (
        FreeNewsAnalyzer,
        FreeEconomicCalendar,
        MultiExchangeArbitragePremium,
        ArbitrageExecutorPremium
    )
    from omnix_services.optimization import MathematicalOptimizer, PerformanceOptimizer
    from omnix_services.database_service import DatabaseManager
    from omnix_services.ai_service import ConversationalAI
    from omnix_services.monitoring import AdvancedPerformanceTracker
    from omnix_services.trading_service import MultiCurrencyTradingEngine, EnhancedTradingSystem
    from omnix_services.telegram_service import EnterpriseTelegramBot
    from omnix_core import TradingSystem
    
    logger.info("Legacy services loaded successfully")
    
    return {
        'database_manager': DatabaseManager,
        'performance_tracker': AdvancedPerformanceTracker(),
        'intelligent_cache': IntelligentCacheSystem(max_size=1000, ttl_seconds=300),
        'concurrency_manager': OptimizedConcurrencyManager(),
        'performance_optimizer': PerformanceOptimizer(),
        'resource_manager': ScalableResourceManager(),
    }


def initialize_services_v7():
    """
    Initialize OMNIX services using V7.0 hexagonal architecture.
    
    Uses the DI Container and application layer.
    Used when USE_APP_LAYER=true.
    """
    from src.omnix.bootstrap import bootstrap_omnix, get_container
    from src.omnix.config.settings import get_settings
    
    settings = get_settings()
    
    logger.info("=" * 70)
    logger.info(f"OMNIX V7.0 - Hexagonal Architecture Bootstrap")
    logger.info(f"Trading Profile: {settings.trading_profile}")
    logger.info("=" * 70)
    
    result = bootstrap_omnix(
        configure_logs=True,
        validate_env=True,
        prime_cache=True,
        verify_db=True,
        fail_fast=False
    )
    
    if not result.success:
        logger.error(f"Bootstrap failed: {result.errors}")
    
    for warning in result.warnings:
        logger.warning(f"Bootstrap warning: {warning}")
    
    container = result.container or get_container()
    
    logger.info(f"Container health: {container.health_check()}")
    
    return {
        'container': container,
        'bootstrap_result': result,
    }


async def run_telegram_bot_legacy(services: dict):
    """Run the Telegram bot using EnterpriseTelegramBot (100% async nativo).
    
    Usa Application.run_polling() nativo de python-telegram-bot v20+
    para máxima concurrencia y escalabilidad.
    """
    from omnix_services.telegram_service import EnterpriseTelegramBot
    from omnix_config import env_config
    
    token = env_config.get_required('TELEGRAM_BOT_TOKEN')
    
    logger.info("Starting Telegram bot (async native mode)...")
    
    bot = EnterpriseTelegramBot()
    
    await bot.start_polling()


async def run_telegram_bot_v7(services: dict):
    """Run the Telegram bot using V7.0 TelegramBotAdapter."""
    container = services.get('container')
    
    if not container:
        logger.error("Container not available, falling back to legacy")
        return await run_telegram_bot_legacy(services)
    
    telegram_adapter = container.telegram_adapter
    
    if telegram_adapter:
        logger.info("Starting Telegram bot (V7.0 mode)...")
        await telegram_adapter.start()
        await telegram_adapter.run_polling()
    else:
        logger.warning("TelegramBotAdapter not available, falling back to legacy")
        return await run_telegram_bot_legacy(services)


def run_omnix(use_app_layer: Optional[bool] = None):
    """
    Main entry point for OMNIX.
    
    Args:
        use_app_layer: Override USE_APP_LAYER setting. If None, uses env var.
    """
    print("Cleaning Python cache...")
    deleted = clean_pycache()
    print(f"Cache cleaned: {deleted} items removed")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    db_url = fix_database_url()
    if db_url:
        logger.info(f"DATABASE_URL found: {len(db_url)} characters")
        run_migrations(db_url)
    else:
        logger.error("DATABASE_URL not found - database features will be unavailable")
    
    if use_app_layer is None:
        use_app_layer = os.environ.get('USE_APP_LAYER', 'false').lower() == 'true'
    
    if use_app_layer:
        logger.info("Using V7.0 Hexagonal Architecture")
        services = initialize_services_v7()
        asyncio.run(run_telegram_bot_v7(services))
    else:
        logger.info("Using Legacy Architecture")
        services = initialize_services_legacy()
        asyncio.run(run_telegram_bot_legacy(services))


if __name__ == '__main__':
    run_omnix()
