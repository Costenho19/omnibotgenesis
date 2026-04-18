#!/usr/bin/env python3
"""
OMNIX V7.0 Main Entry Point for Railway Production
===================================================
Thin wrapper that delegates to src/omnix/bootstrap/main_entry.py

This file is maintained for backward compatibility with Railway deployment.
The actual logic resides in the modular entrypoint.

Usage:
    python main.py
    python -u main.py  # Unbuffered output for Railway
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.omnix.bootstrap.main_entry import run_omnix
    run_omnix()
except ImportError as e:
    print(f"[FALLBACK] New entrypoint not available: {e}")
    print("[FALLBACK] Using legacy main module...")
    
    from omnix_services.telegram_service import EnterpriseTelegramBot
    import asyncio
    
    async def run_legacy():
        bot = EnterpriseTelegramBot()
        if hasattr(bot, 'run'):
            await bot.run()
        elif hasattr(bot, 'run_polling'):
            await bot.run_polling()
    
    asyncio.run(run_legacy())
