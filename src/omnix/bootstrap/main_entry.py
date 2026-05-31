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
    from omnix_services.ai_service.conversational_ai_adapter import ConversationalAI
    from omnix_services.monitoring import AdvancedPerformanceTracker
    from omnix_services.trading_service import MultiCurrencyTradingEngine, EnhancedTradingSystem
    from omnix_services.telegram_service import EnterpriseTelegramBot
    from omnix_core import TradingSystem
    
    logger.info("Legacy services loaded successfully")
    
    use_ai_port = os.environ.get('USE_AI_PORT', 'false').lower() == 'true'
    use_voice_port = os.environ.get('USE_VOICE_PORT', 'false').lower() == 'true'
    
    if use_ai_port or use_voice_port:
        try:
            from omnix_services.ai_service.container import initialize_v7_services
            v7_status = initialize_v7_services()
            logger.info(f"V7 AI/Voice services initialized: {v7_status}")
        except ImportError:
            logger.info("V7 container not available - using pure legacy mode")
        except Exception as e:
            logger.warning(f"V7 services initialization failed: {e}")
    else:
        logger.info("V7 feature flags disabled - skipping V7 initialization")
    
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


async def start_verification_server_task():
    """Start the public verification web server.

    Uses the PORT env var (set by Railway/Cloud) so the platform health-check
    succeeds.  Falls back to 8000 for local development.
    """
    port = int(os.environ.get("PORT", "8000"))
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "verification_server",
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))))),
                "omnix_core", "evidence", "verification_server.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        runner = await mod.start_verification_server(port=port)
        logger.info(f"Public verification server started on port {port}")
        return runner
    except Exception as e:
        logger.warning(f"Verification server failed to start on port {port}: {e}")
        return None


async def run_telegram_bot_legacy(services: dict):
    """Run the Telegram bot using EnterpriseTelegramBot.

    Selects WEBHOOK or POLLING mode automatically at startup:

    WEBHOOK mode (Railway production):
        Set TELEGRAM_WEBHOOK_URL to the public URL of this Railway service
        (e.g. "https://omnix-bot.up.railway.app") and optionally
        TELEGRAM_WEBHOOK_SECRET to a 32+ char random string.
        Telegram POSTs updates to {URL}/telegram/webhook — no polling race,
        zero "Conflict: terminated by other getUpdates" errors, immune to
        Railway deploy overlaps where old and new instances coexist briefly.

    POLLING mode (local development / fallback):
        No TELEGRAM_WEBHOOK_URL set → classic long-polling.  Simple, no
        extra infra, but triggers Conflict errors whenever Railway restarts
        the service with more than one instance running simultaneously.
    """
    import signal

    try:
        from omnix_services.telegram_service import EnterpriseTelegramBot
        from omnix_config import env_config

        print("[BOT] Step 1/5 — Validating TELEGRAM_BOT_TOKEN...", flush=True)
        token = env_config.get_required('TELEGRAM_BOT_TOKEN')
        print(f"[BOT] Step 1/5 — Token OK ({len(token)} chars)", flush=True)

        # ── Detect mode from environment ──────────────────────────────────────
        webhook_url    = os.environ.get("TELEGRAM_WEBHOOK_URL", "").strip()
        webhook_secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "").strip()
        port           = int(os.environ.get("PORT", "8080"))
        use_webhook    = bool(webhook_url)

        if use_webhook:
            # WEBHOOK — Railway $PORT is consumed by the Telegram webhook server;
            # skip the internal verification server to avoid port conflict.
            print(
                f"[BOT] Step 2/5 — WEBHOOK mode detected "
                f"(TELEGRAM_WEBHOOK_URL={webhook_url}) "
                f"— verification server SKIPPED (port {port} reserved for Telegram)",
                flush=True,
            )
        else:
            print("[BOT] Step 2/5 — POLLING mode — starting verification server...", flush=True)
            try:
                await asyncio.wait_for(start_verification_server_task(), timeout=15.0)
                print("[BOT] Step 2/5 — Verification server done", flush=True)
            except Exception as vs_err:
                print(f"[BOT] Step 2/5 — Verification server failed (non-fatal): {vs_err}", flush=True)

        print("[BOT] Step 3/5 — Instantiating EnterpriseTelegramBot...", flush=True)
        bot = EnterpriseTelegramBot()
        print("[BOT] Step 3/5 — Bot instance created", flush=True)

        loop = asyncio.get_event_loop()

        def _sigterm_handler():
            logger.info("🛑 [SIGTERM] Received — iniciando shutdown graceful del bot...")
            print("[BOT] SIGTERM received — stopping bot gracefully", flush=True)
            bot.is_running = False
            asyncio.ensure_future(bot.stop_async(), loop=loop)

        try:
            loop.add_signal_handler(signal.SIGTERM, _sigterm_handler)
            loop.add_signal_handler(signal.SIGINT, _sigterm_handler)
            logger.info("✅ [SIGTERM] Handler registrado — shutdown graceful habilitado")
        except (NotImplementedError, RuntimeError) as sig_err:
            logger.warning(f"⚠️ No se pudo registrar signal handler: {sig_err}")

        if use_webhook:
            print(
                f"[BOT] Step 4/5 — WEBHOOK mode: "
                f"{webhook_url}/telegram/webhook on port {port}",
                flush=True,
            )
            logger.info("Starting Telegram bot (WEBHOOK mode — zero-conflict Railway deploys)...")
            await bot.start_webhook(
                webhook_url=webhook_url,
                secret_token=webhook_secret,
                port=port,
            )
        else:
            print("[BOT] Step 4/5 — POLLING mode: calling start_polling()...", flush=True)
            logger.info("Starting Telegram bot (async native POLLING mode)...")
            await bot.start_polling()

        print("[BOT] Step 4/5 — Bot returned from main loop", flush=True)

    except Exception as exc:
        import traceback
        print(f"[BOT] FATAL ERROR in run_telegram_bot_legacy: {exc}", flush=True)
        traceback.print_exc()
        raise


async def run_telegram_bot_v7(services: dict):
    """Run the Telegram bot using V7.0 TelegramBotAdapter.

    Inherits the same WEBHOOK / POLLING mode selection as the legacy path:
    set TELEGRAM_WEBHOOK_URL to enable webhook mode (recommended for Railway).
    """
    import signal

    container = services.get('container')

    if not container:
        logger.error("Container not available, falling back to legacy")
        return await run_telegram_bot_legacy(services)

    telegram_adapter = container.telegram_adapter

    if telegram_adapter:
        # ── Detect mode from environment ──────────────────────────────────
        webhook_url    = os.environ.get("TELEGRAM_WEBHOOK_URL", "").strip()
        webhook_secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "").strip()
        port           = int(os.environ.get("PORT", "8080"))
        use_webhook    = bool(webhook_url)

        if use_webhook:
            logger.info(
                "[BOT-V7] WEBHOOK mode — %s/telegram/webhook on port %d",
                webhook_url, port,
            )
        else:
            # Only start verification server in polling mode (same port logic)
            await start_verification_server_task()

        bot = getattr(telegram_adapter, 'enterprise_bot', None) or getattr(telegram_adapter, '_bot', None)
        if bot is not None:
            loop = asyncio.get_event_loop()

            def _sigterm_handler_v7():
                logger.info("🛑 [SIGTERM-V7] Received — iniciando shutdown graceful del bot...")
                print("[BOT-V7] SIGTERM received — stopping bot gracefully", flush=True)
                bot.is_running = False
                asyncio.ensure_future(bot.stop_async(), loop=loop)

            try:
                loop.add_signal_handler(signal.SIGTERM, _sigterm_handler_v7)
                loop.add_signal_handler(signal.SIGINT, _sigterm_handler_v7)
                logger.info("✅ [SIGTERM-V7] Handler registrado — shutdown graceful habilitado")
            except (NotImplementedError, RuntimeError) as sig_err:
                logger.warning(f"⚠️ No se pudo registrar signal handler V7: {sig_err}")

        logger.info("Starting Telegram bot (V7.0 mode — %s)...", "WEBHOOK" if use_webhook else "POLLING")
        # NOTE: Do NOT call telegram_adapter.start() separately.
        # run_polling/run_webhook delegate to enterprise_bot methods which
        # handle initialization and handler registration internally.
        if use_webhook:
            await telegram_adapter.run_webhook(
                webhook_url=webhook_url,
                secret_token=webhook_secret,
                port=port,
            )
        else:
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
