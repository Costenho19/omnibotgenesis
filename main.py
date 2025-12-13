#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNIX INSTITUTIONAL+ - SISTEMA DUAL-MARKET INSTITUCIONAL  
Sistema de Trading Automático: CRIPTO (24/7) + BOLSA (NYSE/NASDAQ)
IA Avanzada + AI Risk Guardian + Professional Trading Strategy 73% Win Rate
Post-Quantum Cryptography + Multi-Model AI (GPT-4o + Gemini 2.0 Flash)
Desarrollado por Harold Nunes - Diciembre 2025

BUILD_TIMESTAMP = "2025-12-06T00:00:00Z"
FORCE_REBUILD_VERSION = "position-manager-fix"
"""

# 🧹 LIMPIEZA DE CACHE RAILWAY - EJECUTAR ANTES DE CUALQUIER IMPORT
import os
import sys
import shutil

print("🧹 Limpiando cache Python...")

current_dir = os.path.dirname(os.path.abspath(__file__))
deleted_count = 0

for root, dirs, files in os.walk(current_dir):
    if '__pycache__' in dirs:
        pycache_path = os.path.join(root, '__pycache__')
        try:
            shutil.rmtree(pycache_path)
            deleted_count += 1
        except:
            pass
    
    for file in files:
        if file.endswith('.pyc'):
            pyc_path = os.path.join(root, file)
            try:
                os.remove(pyc_path)
                deleted_count += 1
            except:
                pass

print(f"✅ Cache limpiado: {deleted_count} elementos eliminados")

import logging
import time
import threading
import random  # Para nonce único en Kraken
import uuid     # Para IDs únicos
import requests
import asyncio
import re
import tempfile
from datetime import datetime, timedelta

# 🔧 OMNIX INSTITUTIONAL+ - Configuración Centralizada
from omnix_config import env_config, VERSION_BANNER

# 📊 STOCK TRADING MODULE - DUAL MARKET SYSTEM
STOCK_TRADING_ENABLED = env_config.get('STOCK_TRADING_ENABLED', default='true', cast_type=bool)
# Configurar logging ANTES de cualquier uso
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
logger.info("=" * 70)
logger.info(f"🔥 OMNIX {VERSION_BANNER} - BUILD 2025-12-06T00:00:00Z")
logger.info("🎯 POSITION MANAGER FIX - TP/SL dinámico + Symbol tracking")
logger.info(f"📊 DynamicPositionManager PREMIUM INCLUIDO")
logger.info("=" * 70)

# 🔍 DIAGNÓSTICO CRÍTICO DE BASE DE DATOS - VISIBLE AL INICIO
db_url = os.environ.get('DATABASE_URL')
if db_url:
    # 🔧 FIX Nov 29, 2025: Detectar si el VALUE incluye la KEY como prefijo
    if db_url.startswith('DATABASE_URL='):
        db_url = db_url[len('DATABASE_URL='):]
        os.environ['DATABASE_URL'] = db_url
        logger.warning("🔧 FIX: Removido prefijo 'DATABASE_URL=' del valor - Corrige tu Railway config")
    elif db_url.startswith('DATABASE_URL:'):
        db_url = db_url[len('DATABASE_URL:'):]
        os.environ['DATABASE_URL'] = db_url
        logger.warning("🔧 FIX: Removido prefijo 'DATABASE_URL:' del valor - Corrige tu Railway config")
    
    logger.info(f"✅ DATABASE_URL ENCONTRADA: {len(db_url)} caracteres")
    # Mostrar primeros caracteres seguros (sin exponer credenciales)
    if db_url.startswith(('postgres://', 'postgresql://')):
        logger.info(f"   Preview: {db_url[:25]}...")
    else:
        logger.info(f"   Preview: {db_url[:15]}... (formato inusual)")
    
    # 🔄 MIGRACIONES AUTOMÁTICAS V6.5.4 - Ejecutar ANTES de inicializar servicios
    try:
        from omnix_services.database_service.migrations import MigrationRunner, MIGRATIONS
        
        logger.info("🔄 Ejecutando migraciones de base de datos...")
        migration_runner = MigrationRunner(db_url)
        migration_result = migration_runner.run_pending_migrations(MIGRATIONS)
        
        if migration_result['success']:
            if migration_result['applied'] > 0:
                logger.info(f"✅ Migraciones aplicadas: {migration_result['applied']}")
            else:
                logger.info("✅ Base de datos actualizada - sin migraciones pendientes")
        else:
            logger.error(f"❌ Error en migraciones: {migration_result['errors']}")
            # No detener el bot, solo advertir
    except ImportError as e:
        logger.warning(f"⚠️ Sistema de migraciones no disponible: {e}")
    except Exception as e:
        logger.error(f"❌ Error ejecutando migraciones: {e}")
        # Continuar con el arranque del bot
else:
    logger.error("❌ DATABASE_URL NO ENCONTRADA - LA MEMORIA NO FUNCIONARÁ")
    logger.error("   Variables disponibles: " + ", ".join(sorted([k for k in os.environ.keys() if 'DATA' in k.upper() or 'PG' in k.upper() or 'SQL' in k.upper()][:5])))

# Stock Trading Module - Conditional Import (AFTER logger is configured)
if STOCK_TRADING_ENABLED:
    try:
        from omnix_services.stock_trading import (
            AlpacaService,
            MarketHoursManager,
            StockAnalyzer,
            FundamentalAnalyzer
        )
        from omnix_services.stock_trading.stock_commands import StockCommandsHandler
        STOCK_MODULE_AVAILABLE = True
        logger.info("📊 Stock Trading Module cargado - Modo ACTIVO")
    except ImportError as e:
        STOCK_MODULE_AVAILABLE = False
        logger.warning(f"⚠️ Stock Trading Module no disponible: {e}")
else:
    STOCK_MODULE_AVAILABLE = False
    logger.info("📊 Stock Trading Module: DORMIDO (STOCK_TRADING_ENABLED=false)")

# Stripe payment integration
try:
    from omnix_api.payments.stripe_integration import setup_stripe_routes
    STRIPE_INTEGRATION_AVAILABLE = True
except ImportError:
    STRIPE_INTEGRATION_AVAILABLE = False
    logger.warning("⚠️ stripe_integration no disponible")

# Imports necesarios para trading automático
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False
# Monitoreo básico sin dependencias externas
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# IA y Trading APIs - SISTEMA MÚLTIPLE ANTI-FALLAS
try:
    # IMPORTANTE: Usar nuevo SDK google.genai (no google.generativeai)
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
    # Configurar cliente Gemini directamente
    GEMINI_MODEL = None
    if env_config.get('GEMINI_API_KEY'):
        try:
            GEMINI_MODEL = genai.Client(api_key=env_config.get('GEMINI_API_KEY'))
            print("✅ GEMINI 2.0 CLIENT INICIALIZADO CORRECTAMENTE")
        except Exception as e:
            print(f"❌ Error configurando Gemini: {e}")
            GEMINI_MODEL = None
except ImportError:
    try:
        # Fallback al SDK anterior si no está disponible el nuevo
        import google.generativeai as genai
        GEMINI_AVAILABLE = True
        # Configurar con SDK anterior
        GEMINI_MODEL = None
        if env_config.get('GEMINI_API_KEY'):
            try:
                genai.configure(api_key=env_config.get('GEMINI_API_KEY'))
                GEMINI_MODEL = genai.GenerativeModel('gemini-2.0-flash-exp')
                print("✅ GEMINI CLASSIC CLIENT INICIALIZADO")
            except Exception as e:
                print(f"❌ Error configurando Gemini classic: {e}")
                GEMINI_MODEL = None
    except ImportError:
        genai = None
        GEMINI_AVAILABLE = False
        GEMINI_MODEL = None

# Sistema de respaldo OpenAI + WHISPER SPEECH-TO-TEXT
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    # SPEECH-TO-TEXT ACTIVADO POR HAROLD - FUNCIONANDO COMPLETAMENTE
    SPEECH_TO_TEXT_ENABLED = True  # ACTIVADO - OpenAI Whisper operacional
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False
    SPEECH_TO_TEXT_ENABLED = False

# Sistema de respaldo Anthropic Claude
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    anthropic = None
    ANTHROPIC_AVAILABLE = False

# Sistema Telegram Bot
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    # Define dummy classes when telegram is not available
    class Update:
        pass
    class ContextTypes:
        DEFAULT_TYPE = None
    class Application:
        @staticmethod
        def builder():
            return None
    class CommandHandler:
        def __init__(self, *args, **kwargs):
            pass
    class MessageHandler:
        def __init__(self, *args, **kwargs):
            pass
    class filters:
        TEXT = None
        VOICE = None
    TELEGRAM_AVAILABLE = False

try:
    import ccxt
    TRADING_AVAILABLE = True
except ImportError:
    ccxt = None
    TRADING_AVAILABLE = False

# =============================================================================
# 🔐 SEGURIDAD POST-CUÁNTICA - INTEGRACIÓN COMPLETA NIST 2024
# =============================================================================
try:
    from omnix_core.security.pqc_security import PostQuantumSecurity
    PQC_AVAILABLE = True
    print("✅ SEGURIDAD POST-CUÁNTICA DISPONIBLE (Kyber-768 + Dilithium-3)")
except ImportError:
    PostQuantumSecurity = None
    PQC_AVAILABLE = False
    print("⚠️ PQC no disponible - Instalar: pip install pypqc")

# =============================================================================
# 🚀 ADVANCED FEATURES ENTERPRISE - 100% REAL Y FUNCIONAL
# =============================================================================
try:
    from omnix_services.trading_service.advanced_features import AdvancedFeaturesEngine
    ADVANCED_FEATURES_AVAILABLE = True
    print("✅ ADVANCED FEATURES DISPONIBLES (Monte Carlo, Black Swan, Sentiment, Sharia, Order Book)")
except ImportError as e:
    AdvancedFeaturesEngine = None
    ADVANCED_FEATURES_AVAILABLE = False
    print(f"⚠️ Advanced Features no disponibles: {e}")

# =============================================================================
# 🧬 ARES QUANTUM PROTOCOLS - ESTRATEGIAS INSTITUCIONALES
# =============================================================================
try:
    print("🔥 INICIANDO BLOQUE IMPORT ARES")
    print(f"🔍 Python Path: {sys.path[:3]}")
    print(f"🔍 CWD: {os.getcwd()}")
    print(f"🔍 omnix_core/strategies/ exists: {os.path.exists('omnix_core/strategies')}")
    
    from omnix_core.strategies.ares_v1 import AresProtocolV1
    from omnix_core.strategies.ares_v2 import AresProtocolV2
    ARES_STRATEGIES_AVAILABLE = True
    print("✅ ARES QUANTUM PROTOCOLS LOADED:")
    print("   🧬 ARES V1 - Swing Trading (55-65% win rate)")
    print("   🧨 ARES V2 - Scalping M1 (60-70% win rate)")
except ImportError as e:
    AresProtocolV1 = None
    AresProtocolV2 = None
    ARES_STRATEGIES_AVAILABLE = False
    print(f"❌ ARES ImportError COMPLETO: {type(e).__name__}: {str(e)}")
    import traceback
    print(traceback.format_exc())
except Exception as e:
    AresProtocolV1 = None
    AresProtocolV2 = None
    ARES_STRATEGIES_AVAILABLE = False
    print(f"❌ ARES Exception COMPLETO: {type(e).__name__}: {str(e)}")
    import traceback
    print(traceback.format_exc())

# =============================================================================
# 🆕 OMNIX MODULAR SERVICES - ARQUITECTURA REFACTORIZADA
# =============================================================================

# Market Data Services (migrated from monolithic main.py)
from omnix_services.market_data import (
    fetch_market_snapshot,
    get_fear_greed_index,
    get_btc_dominance,
    get_free_market_metrics,
    get_multi_exchange_prices,
    detect_arbitrage_opportunities,
    analyze_volume_patterns,
    get_external_market_factors,
    analyze_historical_patterns,
    generate_predictive_insights,
    calculate_confidence_score
)

# Advanced Trading Analyzers (migrated from monolithic main.py)
from omnix_services.trading_service.analyzers import (
    AdvancedOrderBookAnalyzer,
    AdvancedVolatilityAnalyzer,
    MicrostructureAnalyzer,
    AdvancedRiskManagement
)

# Voice Controller Service (migrated from monolithic main.py)
from omnix_services.voice_service import (
    VoiceEngine,
    send_telegram_response_with_voice,
    initialize_voice_engine
)

# Concurrency & Cache Services (migrated from monolithic main.py)
from omnix_services.concurrency import (
    IntelligentCacheSystem,
    OptimizedConcurrencyManager,
    ScalableResourceManager
)

# Analytics Services (migrated from monolithic main.py)
from omnix_services.analytics import (
    AutoFibonacciAnalyzer,
    VolumeProfileAnalyzer
)

# Market Intelligence Services (migrated from monolithic main.py)
from omnix_services.market_data.intelligence import (
    FreeNewsAnalyzer,
    FreeEconomicCalendar,
    MultiExchangeArbitragePremium,
    ArbitrageExecutorPremium
)

# Optimization Services (migrated from monolithic main.py)
from omnix_services.optimization import MathematicalOptimizer, PerformanceOptimizer

# Database Services (migrated from monolithic main.py)
from omnix_services.database_service import DatabaseManager

# AI Services (migrated from monolithic main.py)
from omnix_services.ai_service import ConversationalAI

# Monitoring Services (migrated from monolithic main.py)
from omnix_services.monitoring import AdvancedPerformanceTracker

# Trading Services (migrated from monolithic main.py)
from omnix_services.trading_service import MultiCurrencyTradingEngine, EnhancedTradingSystem

# Derivatives Trading Module (institutional-grade futures/perpetuals)
try:
    from omnix_services.derivatives import (
        DerivativesManager,
        MarginEngine,
        KrakenFuturesClient,
        PaperDerivativesManager,
        HedgingService,
        FundingArbitrageAnalyzer
    )
    DERIVATIVES_AVAILABLE = True
    logger.info("✅ Derivatives Module loaded - Institutional futures/perpetuals ready")
except ImportError as e:
    DERIVATIVES_AVAILABLE = False
    logger.warning(f"⚠️ Derivatives Module not available: {e}")

from omnix_services.telegram_service import EnterpriseTelegramBot
from omnix_core import TradingSystem

logger.info("✅ Servicios modulares cargados: market_data + analyzers + voice_controller + concurrency + analytics + intelligence + optimization + database + ai_adapter + monitoring + TradingSystem")

# Global voice engine instance (managed by voice_controller)
global_voice_engine = None

# =============================================================================
# 🔒 CONFIGURACIÓN DE SEGURIDAD CENTRALIZADA - MEJORAS CRÍTICAS
# =============================================================================

# Lista de IDs de administradores autorizados
ADMIN_IDS = {
    7014748854,  # Harold Nunes - Creator
    # Agregar más IDs de admin aquí si es necesario
}

def is_admin(user_id):
    """Verificar si un usuario es administrador de forma centralizada y robusta"""
    try:
        return int(user_id) in ADMIN_IDS
    except (ValueError, TypeError):
        return False

# =============================================================================
# =============================================================================

# ACTIVAR MÓDULOS AVANZADOS
ADVANCED_MODULES_AVAILABLE = True

# Capacidades de análisis avanzado de datos
try:
    import trafilatura
    import feedparser
    WEB_ANALYSIS_AVAILABLE = True
except ImportError:
    WEB_ANALYSIS_AVAILABLE = False

# MEJORAS GRATUITAS REALES IMPLEMENTADAS - AGOSTO 2025
# Sistema de análisis sentiment gratuito con noticias RSS
try:
    import textblob
    SENTIMENT_ANALYSIS_AVAILABLE = True
except ImportError:
    try:
        from textblob import TextBlob
        SENTIMENT_ANALYSIS_AVAILABLE = True
    except:
        SENTIMENT_ANALYSIS_AVAILABLE = False

# Economic Calendar gratuito
try:
    import json
    import urllib.parse
    ECONOMIC_CALENDAR_AVAILABLE = True
except ImportError:
    ECONOMIC_CALENDAR_AVAILABLE = False

# ACTIVAR NUEVOS MÓDULOS GRATUITOS
FREE_MODULES_ACTIVE = True
news_analyzer = FreeNewsAnalyzer()
economic_calendar = FreeEconomicCalendar()
arbitrage_scanner = MultiExchangeArbitragePremium()
arbitrage_executor = ArbitrageExecutorPremium(paper_trading=True)

# Sistema de voz - FUNDAMENTAL PARA OMNIX
try:
    from gtts import gTTS
    import tempfile
    TTS_AVAILABLE = True
except ImportError:
    gTTS = None
    TTS_AVAILABLE = False

# Logging ya configurado al inicio del archivo (línea 30)

# 🚀 OMNIX ENTERPRISE - Sistema Modular Premium
# Importar DESPUÉS de logger para evitar NameError
OMNIX_ENTERPRISE_AVAILABLE = False
TRADING_ENTERPRISE_AVAILABLE = False

try:
    from omnix_services.ai_service import ConversationalAIService
    from omnix_services.ai_service.ai_prompts import PromptsContextManager
    from omnix_core.cache.redis_cache import cache
    from omnix_core.cache.redis_state import conversation_history, user_preferences
    from omnix_core.utils.rate_limiter import RateLimitExceeded
    OMNIX_ENTERPRISE_AVAILABLE = True
    logger.info("✅ OMNIX ENTERPRISE AI MODULES LOADED - Sistema Premium Activado")
except ImportError as e:
    logger.warning(f"⚠️ OMNIX Enterprise AI modules not available: {e}")
    OMNIX_ENTERPRISE_AVAILABLE = False

# 🏦 OMNIX TRADING SERVICE ENTERPRISE
try:
    from omnix_services.trading_service import TradingServiceEnterprise
    TRADING_ENTERPRISE_AVAILABLE = True
    logger.info("✅ TRADING SERVICE ENTERPRISE LOADED - 931 líneas código premium")
except ImportError as e:
    logger.warning(f"⚠️ Trading Service Enterprise not available: {e}")
    TRADING_ENTERPRISE_AVAILABLE = False

# 🎤 OMNIX VOICE SERVICE ENTERPRISE
VoiceServiceEnterprise = None  # Type hint fix
VOICE_ENTERPRISE_AVAILABLE = False
try:
    from omnix_services.voice_service import VoiceServiceEnterprise
    VOICE_ENTERPRISE_AVAILABLE = True
    logger.info("✅ VOICE SERVICE ENTERPRISE LOADED - TTS + STT + Biometría")
except ImportError as e:
    logger.warning(f"⚠️ Voice Service Enterprise not available: {e}")
    VOICE_ENTERPRISE_AVAILABLE = False

# 🗄️ OMNIX DATABASE SERVICE ENTERPRISE
DatabaseServiceEnterprise = None  # Type hint fix
DATABASE_ENTERPRISE_AVAILABLE = False
try:
    from omnix_services.database_service import DatabaseServiceEnterprise
    DATABASE_ENTERPRISE_AVAILABLE = True
    logger.info("✅ DATABASE SERVICE ENTERPRISE LOADED - PostgreSQL 8 tablas")
except ImportError as e:
    logger.warning(f"⚠️ Database Service Enterprise not available: {e}")
    DATABASE_ENTERPRISE_AVAILABLE = False

# Configuración integrada (migrado a EnvConfig centralizado)
class Config:
    TELEGRAM_BOT_TOKEN = env_config.get_required('TELEGRAM_BOT_TOKEN')
    # Sistema de múltiples IA para máxima confiabilidad
    GEMINI_API_KEY = env_config.get('GEMINI_API_KEY')
    OPENAI_API_KEY = env_config.get('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = env_config.get('ANTHROPIC_API_KEY')
    HOST = '0.0.0.0'
    PORT = env_config.get('PORT', default=8000, cast_type=int)
    DEBUG = False

config = Config()

# Inicializar sistema de IA múltiple - ANTI-FALLAS HAROLD
ai_status = {
    'gemini': False,
    'openai': False, 
    'anthropic': False,
    'primary': None,
    'backup': []
}

# Inicializar Gemini IA (PRIMARIA)
if GEMINI_AVAILABLE and env_config.get('GEMINI_API_KEY'):
    try:
        if hasattr(genai, 'Client'):
            genai_client = genai.Client(api_key=env_config.get('GEMINI_API_KEY'))
            logger.info("IA Gemini 2.0 (nuevo SDK) configurada correctamente")
        else:
            genai.configure(api_key=env_config.get('GEMINI_API_KEY'))
            genai_client = None
            logger.info("IA Gemini (SDK anterior) configurada correctamente")
        ai_status['gemini'] = True
        ai_status['backup'].append('gemini')
    except Exception as e:
        logger.error(f"Error configurando Gemini: {e}")
        GEMINI_AVAILABLE = False

# Inicializar OpenAI (PRIMARIA - MEJOR CALIDAD)
if OPENAI_AVAILABLE and env_config.get('OPENAI_API_KEY'):
    try:
        openai_client = OpenAI(api_key=env_config.get('OPENAI_API_KEY'))
        ai_status['openai'] = True
        ai_status['primary'] = 'openai'  # OpenAI como primaria
        logger.info("IA OpenAI GPT-4o configurada como PRIMARIA")
    except Exception as e:
        logger.error(f"Error configurando OpenAI: {e}")
        OPENAI_AVAILABLE = False

# Inicializar Anthropic (RESPALDO 2)  
if ANTHROPIC_AVAILABLE and env_config.get('ANTHROPIC_API_KEY'):
    try:
        anthropic_client = anthropic.Anthropic(api_key=env_config.get('ANTHROPIC_API_KEY'))
        ai_status['anthropic'] = True
        ai_status['backup'].append('anthropic')
        logger.info("IA Anthropic Claude configurada como respaldo")
    except Exception as e:
        logger.error(f"Error configurando Anthropic: {e}")
        ANTHROPIC_AVAILABLE = False

# Determinar IA primaria si Gemini falló
if not ai_status['primary'] and ai_status['backup']:
    ai_status['primary'] = ai_status['backup'][0]
    logger.info(f"IA primaria cambiada a {ai_status['primary']}")

logger.info(f"SISTEMA IA MÚLTIPLE: Primaria={ai_status['primary']}, Respaldos={ai_status['backup']}")

# Módulos avanzados simplificados - SOLO LO QUE FUNCIONA
ADVANCED_MODULES_AVAILABLE = True  # Módulos internos siempre disponibles
logger.info("✅ MÓDULOS BÁSICOS ACTIVADOS: Análisis técnico, Risk management, Portfolio optimization")

# 🚀 CARACTERÍSTICAS ULTRA COMPETITIVAS - NINGÚN COMPETIDOR LAS TIENE
OMNIX_COMPETITIVE_ADVANTAGES = {
    '🔐 Enterprise Security': 'Advanced encryption and protection',
    '🎤 Voice Bidirectional': 'Speech-to-Text + Text-to-Speech real',
    '☪️ Sharia Compliant': 'Automated Islamic finance validation',
    '🌍 10 Languages': 'Multilingual with cultural context',
    '💰 Real Trading': 'Kraken API live trading execution',
    '📈 Advanced Analytics': 'Mathematical optimization algorithms',
    '🧠 Emotional AI': 'Advanced sentiment & psychology',
    '🎨 Visual Interface': 'Rich emoji conversation experience',
    '📊 Enterprise Analytics': 'Automated reports every 15 minutes',
    '🔄 Real-time Learning': 'Continuous self-improvement'
}

# Instancia global del sistema de métricas
performance_tracker = AdvancedPerformanceTracker()

# Instancia global del cache
intelligent_cache = IntelligentCacheSystem(max_size=1000, ttl_seconds=300)

# Instancia global del gestor de concurrencia
concurrency_manager = OptimizedConcurrencyManager()

# Instancias globales de optimización
performance_optimizer = PerformanceOptimizer()
resource_manager = ScalableResourceManager()

# ==================== TELEGRAM BOT INITIALIZATION ====================

# =============================================================================
# 🏗️ USE_APP_LAYER FEATURE FLAG - V7.0 Hexagonal Architecture Migration
# =============================================================================
# Set USE_APP_LAYER=true to use the new hexagonal architecture with:
# - Flask App Factory (src/omnix/interfaces/flask_app.py)
# - DI Container (src/omnix/bootstrap/container.py)
# - TelegramBotAdapter (src/omnix/infrastructure/adapters/telegram_adapter.py)
#
# Default: false (use legacy architecture for production stability)
# =============================================================================

USE_APP_LAYER = env_config.get('USE_APP_LAYER', default='false', cast_type=bool)

if __name__ == "__main__":
    import signal
    import sys
    
    logger.info("=" * 80)
    logger.info(f"🚀 OMNIX {VERSION_BANNER} - INICIANDO SISTEMA PRINCIPAL")
    logger.info(f"🏗️ USE_APP_LAYER: {USE_APP_LAYER}")
    logger.info("=" * 80)
    
    # =============================================================================
    # NEW PATH: Hexagonal Architecture with DI Container (USE_APP_LAYER=true)
    # =============================================================================
    # STATUS: EXPERIMENTAL - Infrastructure ready, handler wiring pending
    # 
    # This path demonstrates V7.0 hexagonal architecture:
    # - DI Container for service resolution
    # - Flask App Factory for dashboard
    # - TelegramBotAdapter for bot operations
    #
    # PENDING (requires application layer orchestration):
    # - Command/message handlers registration via use cases
    # - Full lifecycle coordination with Flask
    # - Integration tests for end-to-end flow
    # =============================================================================
    if USE_APP_LAYER:
        logger.info("🏗️ Usando nueva arquitectura hexagonal V7.0 (EXPERIMENTAL)...")
        try:
            from src.omnix.bootstrap.container import get_container
            from src.omnix.interfaces.flask_app import create_app
            
            container = get_container()
            logger.info(f"✅ DI Container inicializado")
            
            db_manager = container.database_manager
            if db_manager:
                logger.info("✅ DatabaseManager obtenido del Container")
                db_health = db_manager.health_check() if hasattr(db_manager, 'health_check') else {}
                logger.info(f"   📊 DB Connected: {db_health.get('database_connected', 'N/A')}")
            else:
                logger.warning("⚠️ DatabaseManager no disponible en Container")
            
            telegram_adapter = container.telegram_adapter
            if telegram_adapter:
                logger.info(f"✅ TelegramBotAdapter obtenido del Container")
                logger.info(f"   📊 Adapter Health: {telegram_adapter.health_check()}")
            else:
                logger.error("❌ TelegramBotAdapter no disponible - V7.0 no puede iniciar sin Telegram")
                sys.exit(1)
            
            flask_app = create_app(container=container)
            logger.info("✅ Flask App Factory creado con Container DI")
            
            shutdown_event = threading.Event()
            telegram_task = None
            
            def signal_handler(sig, frame):
                logger.info(f"\n🛑 Señal {sig} recibida - Apagando sistema V7.0...")
                shutdown_event.set()
                if telegram_task and not telegram_task.done():
                    telegram_task.cancel()
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            import asyncio
            
            async def start_v7_system():
                started = await telegram_adapter.start()
                if started:
                    logger.info("✅ TelegramBotAdapter iniciado correctamente")
                else:
                    logger.warning("⚠️ TelegramBotAdapter.start() retornó False")
                return started
            
            async def stop_v7_system():
                if telegram_adapter:
                    await telegram_adapter.stop()
                    logger.info("✅ TelegramBotAdapter detenido")
            
            def start_flask_dashboard():
                dashboard_port = int(os.environ.get('PORT', 5000))
                logger.info(f"🌐 Dashboard V7.0 iniciando en puerto {dashboard_port}...")
                flask_app.run(host='0.0.0.0', port=dashboard_port, debug=False, use_reloader=False)
            
            dashboard_thread = threading.Thread(target=start_flask_dashboard, name="DashboardV7Thread", daemon=True)
            dashboard_thread.start()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                bot_started = loop.run_until_complete(start_v7_system())
                
                if not bot_started:
                    logger.error("❌ TelegramBotAdapter no pudo iniciar")
                    sys.exit(1)
                
                logger.info("=" * 80)
                logger.info(f"✅ OMNIX V7.0 HEXAGONAL - SISTEMA OPERATIVO")
                logger.info("🏗️ Arquitectura: Flask Factory + DI Container + Adapters")
                logger.info(f"📊 Container Health: {container.health_check()}")
                logger.info("=" * 80)
                
                while not shutdown_event.is_set():
                    time.sleep(5)
                    if not dashboard_thread.is_alive():
                        logger.error("❌ Dashboard V7.0 murió - reiniciando...")
                        sys.exit(1)
                    if telegram_adapter and not telegram_adapter.is_running():
                        logger.warning("⚠️ TelegramAdapter ya no está corriendo")
                        
            except KeyboardInterrupt:
                logger.info("🛑 Interrupción recibida - apagando V7.0...")
            finally:
                loop.run_until_complete(stop_v7_system())
                loop.close()
                sys.exit(0)
                
        except Exception as e:
            logger.error(f"❌ Error crítico en V7.0: {e}")
            import traceback
            logger.error(traceback.format_exc())
            sys.exit(1)
    
    # =============================================================================
    # LEGACY PATH: Original Architecture (USE_APP_LAYER=false, default)
    # =============================================================================
    logger.info("🔧 Usando arquitectura legacy...")
    
    # Crear instancias de servicios necesarios
    try:
        logger.info("🔧 Instanciando servicios principales...")
        
        # 1. ConversationalAIService (sin parámetros - auto-configura)
        conversational_ai = ConversationalAIService()
        logger.info("✅ ConversationalAIService instanciado")
        
        # 2. TradingSystem (sin parámetros - usa configuración por defecto)
        trading_system = TradingSystem()
        logger.info("✅ TradingSystem instanciado")
        
        # 2.5. DerivativesManager (institutional futures/perpetuals)
        derivatives_manager = None
        if DERIVATIVES_AVAILABLE:
            try:
                derivatives_manager = DerivativesManager()
                logger.info("✅ DerivativesManager instanciado - Mode: PAPER TRADING ($100K)")
                logger.info(f"   📊 MarginEngine: Max {MarginEngine.MAX_LEVERAGE}x leverage")
                logger.info(f"   🛡️ Risk Controls: Warning at {MarginEngine.WARNING_THRESHOLD*100}%, Critical at {MarginEngine.CRITICAL_THRESHOLD*100}%")
            except Exception as e:
                logger.warning(f"⚠️ DerivativesManager initialization failed: {e}")
                derivatives_manager = None
        
        # 3. MetricsEngine (singleton)
        metrics_engine = None  # Se auto-instancia como singleton
        
        # 4. Adaptive Weight System y Auto Learner (opcionales)
        adaptive_weight_system = None
        auto_learning_system = None
        
        # 5. DatabaseManager para AI Risk Guardian y otros servicios
        db_manager = DatabaseManager()
        logger.info("✅ DatabaseManager instanciado")
        
        # 🔍 DIAGNÓSTICO CRÍTICO DE BASE DE DATOS - MUY VISIBLE
        logger.info("=" * 60)
        logger.info("🗄️ ESTADO DE BASE DE DATOS:")
        db_health = db_manager.health_check()
        logger.info(f"   📊 Connected: {db_health.get('database_connected', False)}")
        logger.info(f"   🔧 Enterprise: {db_health.get('enterprise', db_manager.using_enterprise if hasattr(db_manager, 'using_enterprise') else 'N/A')}")
        logger.info(f"   🔗 URL Config: {db_health.get('database_url_configured', False)}")
        if not db_health.get('database_connected', False):
            logger.error("   ❌ MEMORIA NO FUNCIONARÁ - Base de datos desconectada")
        else:
            logger.info("   ✅ MEMORIA ACTIVA - Conversaciones se guardarán")
        logger.info("=" * 60)
        
        logger.info("📱 Instanciando EnterpriseTelegramBot...")
        # EnterpriseTelegramBot instancia ConversationalAI y TradingSystem internamente
        telegram_bot = EnterpriseTelegramBot(db_manager=db_manager)
        logger.info("✅ EnterpriseTelegramBot instanciado correctamente")
        
        # Configurar signal handlers para shutdown limpio
        def signal_handler(sig, frame):
            logger.info(f"\n🛑 Señal {sig} recibida - Apagando bot...")
            if hasattr(telegram_bot, 'is_running'):
                telegram_bot.is_running = False
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Iniciar bot en modo polling
        logger.info("🔄 Iniciando bot Telegram en modo polling...")
        success = telegram_bot.start_polling(drop_pending_updates=True)
        
        if success:
            logger.info("=" * 80)
            logger.info(f"✅ OMNIX {VERSION_BANNER} - BOT TELEGRAM OPERATIVO")
            logger.info("📡 Modo: PAPER TRADING - Capital Virtual: $1,000,000")
            logger.info("🧬 ARES V1 (Swing 55-65%) + V2 (Scalping 60-70%) ACTIVOS")
            if derivatives_manager:
                logger.info("📈 DERIVATIVES MODULE ACTIVO - Futures/Perpetuals ($100K)")
            logger.info("🤖 Gemini 2.0 Flash + GPT-4o LISTOS")
            logger.info("=" * 80)
            
            # 🔍 DIAGNÓSTICO FINAL DE BASE DE DATOS - APARECE AL FINAL
            logger.info("")
            logger.info("🗄️ ═══════════ ESTADO DATABASE ═══════════")
            db_connected = False
            if db_manager and hasattr(db_manager, 'connected'):
                if db_manager.connected:
                    logger.info("🗄️ ✅ DATABASE: CONECTADA - Memoria ACTIVA")
                    db_connected = True
                else:
                    logger.error("🗄️ ❌ DATABASE: NO CONECTADA - Memoria OFF")
                    logger.error("🗄️    Revisa DATABASE_URL en Railway")
            else:
                logger.error("🗄️ ❌ DATABASE: No disponible")
            logger.info("🗄️ ═════════════════════════════════════════")
            
            # Inicializar UserSessionManager y restaurar sesiones multi-usuario
            if db_connected:
                logger.info("")
                logger.info("🔄 ═══════════ AUTO-TRADING RESTORE ═══════════")
                try:
                    from omnix_core.sessions import initialize_session_manager, get_session_manager
                    from omnix_core.cache import get_redis_cache
                    
                    redis_cache = get_redis_cache()
                    session_manager = initialize_session_manager(
                        redis_cache=redis_cache,
                        database_service=db_manager
                    )
                    logger.info(f"🚀 UserSessionManager inicializado - 100K+ usuarios")
                    
                    if hasattr(telegram_bot, 'auto_trading') and telegram_bot.auto_trading:
                        telegram_bot.auto_trading.redis_cache = redis_cache
                        
                        restored = telegram_bot.auto_trading.check_and_restore_auto_trading()
                        if restored:
                            logger.info("🔄 ✅ Sesiones multi-usuario restauradas")
                        else:
                            logger.info("🔄 ℹ️ No hay sesiones activas que restaurar")
                    else:
                        logger.warning("🔄 ⚠️ auto_trading no disponible en telegram_bot")
                except Exception as e:
                    logger.error(f"🔄 ❌ Error en restauración: {e}")
                logger.info("🔄 ═════════════════════════════════════════════════════")
            
            # Iniciar Dashboard en hilo secundario con monitoreo
            dashboard_failed = threading.Event()
            
            def start_dashboard():
                try:
                    from omnix_dashboard.app import app
                    dashboard_port = int(os.environ.get('PORT', 5000))
                    logger.info(f"🌐 Dashboard iniciando en puerto {dashboard_port}...")
                    app.run(host='0.0.0.0', port=dashboard_port, debug=False, use_reloader=False)
                except Exception as e:
                    logger.error(f"❌ Error iniciando Dashboard: {e}")
                finally:
                    dashboard_failed.set()
            
            dashboard_thread = threading.Thread(target=start_dashboard, name="DashboardThread")
            dashboard_thread.start()
            logger.info("✅ Dashboard iniciado en hilo secundario")
            
            # Loop de monitoreo: verifica dashboard cada 5 segundos
            logger.info("🔄 Entrando en loop de monitoreo...")
            try:
                while True:
                    time.sleep(5)
                    if dashboard_failed.is_set() or not dashboard_thread.is_alive():
                        logger.error("❌ Dashboard murió - reiniciando proceso...")
                        sys.exit(1)
            except KeyboardInterrupt:
                logger.info("🛑 Interrupción recibida - apagando...")
                sys.exit(0)
        else:
            logger.error("❌ Error iniciando bot Telegram")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Error crítico en main: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
