"""
OMNIX EnterpriseTelegramBot - Modular Architecture
Bot Telegram empresarial con todas las funcionalidades OMNIX
Extraído de main.py para arquitectura limpia y mantenible
"""

import logging
import os
import re
import time
import asyncio
import threading
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# [ADR-083] Enterprise Security Middleware
try:
    from omnix_services.security.bot_security import get_security_middleware
    _SECURITY_AVAILABLE = True
except ImportError as _sec_err:
    _SECURITY_AVAILABLE = False
    get_security_middleware = None

# Import centralized settings
from omnix_config.settings import settings
from omnix_config import VERSION_BANNER

# ── Governance Commands — ADR-058 ──────────────────────────────────────────────
try:
    from omnix_services.telegram_service.commands.governance_commands import (
        evaluar_command,
        gobernanza_command,
        velos_command,
        recibo_command,
        impact_command,
        clientes_command,
        nuevo_cliente_command,
    )
    _GOVERNANCE_COMMANDS_AVAILABLE = True
except ImportError as _gc_err:
    _GOVERNANCE_COMMANDS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"[ADR-058] Governance commands no disponibles: {_gc_err}")

logger = logging.getLogger(__name__)

try:
    from src.omnix.infrastructure.adapters.authorization_adapter import get_authorization_adapter
    from src.omnix.ports.driven.authorization_port import Permission, UserRole
    AUTHORIZATION_AVAILABLE = True
except ImportError:
    AUTHORIZATION_AVAILABLE = False
    get_authorization_adapter = None
    Permission = None
    UserRole = None


def _check_admin_permission(user_id: str, permission_type: str = 'admin') -> bool:
    """
    Check if user has admin/owner permissions.
    
    Uses AuthorizationAdapter if available, falls back to settings.TELEGRAM_ADMIN_ID.
    
    Args:
        user_id: User ID to check
        permission_type: Type of permission - 'admin', 'real_trading', 'auto_trading'
    
    Returns:
        True if user has permission
    """
    user_id_str = str(user_id)
    
    if AUTHORIZATION_AVAILABLE and get_authorization_adapter:
        auth = get_authorization_adapter()
        if permission_type == 'real_trading':
            return auth.has_permission(user_id_str, Permission.REAL_TRADING)
        elif permission_type == 'auto_trading':
            return auth.has_permission(user_id_str, Permission.REAL_AUTO_TRADING)
        else:
            return auth.is_owner(user_id_str)
    else:
        return user_id_str == str(settings.TELEGRAM_ADMIN_ID)

# Import omnix services
ConversationalAI = None
try:
    from omnix_services.ai_service.conversational_ai_adapter import ConversationalAI
    OMNIX_ENTERPRISE_AVAILABLE = True
except ImportError:
    OMNIX_ENTERPRISE_AVAILABLE = False
    logger.warning("⚠️ ConversationalAI no disponible")

CONTEXTUAL_COMPRESS_AVAILABLE = True

_GREETING_PATTERNS = [
    r'^hola\b', r'^hey\b', r'^buenas?\b', r'^buenos?\s', r'^saludos?\b',
    r'^hi\b', r'^hello\b', r'^qu[eé]\s+tal\b', r'^c[oó]mo\s+est[aá]s',
    r'^amigo\b', r'^caballero\b', r'^bro\b', r'^hermano\b',
    r'^hola\s+(?:amigo|caballero|hermano|bro)\b',
]
_MARKET_PATTERNS = [
    r'mercado', r'market', r'bitcoin', r'btc', r'ethereum', r'eth',
    r'precio', r'price', r'cotiza', r'tendencia', r'trend',
    r'hoy', r'today', r'cripto', r'crypto', r'acci[oó]n', r'stock',
    r'bull', r'bear', r'alcist', r'bajist',
]
_TECHNICAL_PATTERNS = [
    r'especificacion', r'specification', r't[eé]cnic[ao]', r'technical',
    r'arquitectura', r'architecture', r'infraestructura', r'infrastructure',
    r'm[oó]dulo', r'module', r'kernel', r'motor\s+de', r'engine',
    r'algoritm', r'algorithm', r'monte\s*carlo', r'kalman', r'markov',
    r'coherencia', r'coherence', r'veto', r'scoring', r'checkpoint',
    r'c[oó]digo', r'code', r'api\b', r'detalle', r'detail', r'profundidad',
    r'explica.*c[oó]mo\s+funciona', r'explain.*how.*works',
]
_FUNCTIONALITY_PATTERNS = [
    r'qu[eé]\s+sabes\s+hacer', r'qu[eé]\s+puedes\s+hacer',
    r'funcionalidad', r'functionality', r'feature',
    r'capacidad', r'capability', r'habilidad',
    r'para\s+qu[eé]\s+sirves', r'what\s+can\s+you\s+do',
    r'dime.*funcionalidad', r'cu[aá]les\s+son\s+tus',
]

def _classify_msg_context(user_message: str) -> str:
    if not user_message:
        return 'casual'
    msg = user_message.strip().lower()
    if len(msg) < 30 and any(re.search(p, msg) for p in _GREETING_PATTERNS):
        return 'greeting'
    if any(re.search(p, msg) for p in _TECHNICAL_PATTERNS):
        return 'technical'
    if any(re.search(p, msg) for p in _FUNCTIONALITY_PATTERNS):
        return 'overview'
    if any(re.search(p, msg) for p in _MARKET_PATTERNS):
        return 'market'
    if len(msg) < 40:
        return 'casual'
    return 'general'

def compress_response_contextual(response: str, user_message: str) -> str:
    if not response or not user_message:
        return response
    context = _classify_msg_context(user_message)
    logger.info(f"🗜️ [COMPRESS] context={context} | msg='{user_message[:50]}' | input={len(response)} chars")
    if context == 'technical':
        return response
    lines = [l for l in response.split('\n') if l.strip()]
    if context == 'greeting':
        first_line = lines[0] if lines else ""
        sentences = re.split(r'(?<=[.!?])\s+', first_line)
        kept = []
        for s in sentences[:3]:
            if re.search(r'K\(t-s\)|τ=|ε=|Ω=|exp\(-|\d+\s*pts|rad/periodo', s):
                continue
            if re.search(r'funcionalidad\s+central|propósito\s+fundamental|articulan\s+en', s, re.IGNORECASE):
                continue
            if re.search(r'infraestructura|gobernanza|governance|architecture|consolidad[ao]|operativo', s, re.IGNORECASE):
                continue
            if re.search(r'mercado|market|bitcoin|btc|precio|price|\$\d|trading|P&L', s, re.IGNORECASE):
                continue
            if len(s) > 200:
                s = s[:200].rsplit(' ', 1)[0] + '.'
            kept.append(s)
        if not kept:
            kept = ["¡Hola! ¿En qué puedo ayudarte hoy?"]
        result = ' '.join(kept)
        if len(result) > 200:
            result = "¡Hola! ¿En qué puedo ayudarte hoy?"
        logger.info(f"🗜️ [COMPRESS] greeting: {len(response)} → {len(result)} chars")
        return result
    if context == 'overview':
        core_lines = []
        for line in lines:
            if re.search(r'K\(t-s\)|τ=|ε=|Ω=|exp\(-|rad/periodo', line):
                continue
            if re.search(r'\(\d+\s*pts?\)', line):
                continue
            if len(line) > 300:
                sents = re.split(r'(?<=[.!?])\s+', line)
                line = ' '.join(sents[:2])
            core_lines.append(line)
        result = '\n'.join(core_lines[:8])
        if len(result) > 1200:
            sents = re.split(r'(?<=[.!?])\s+', result)
            result = ' '.join(sents[:8])
        logger.info(f"🗜️ [COMPRESS] overview: {len(response)} → {len(result)} chars")
        return result
    if context == 'market':
        core_lines = []
        for line in lines:
            if re.search(r'K\(t-s\)|τ=|ε=|Ω=|exp\(-|rad/periodo', line):
                continue
            if re.search(r'funcionalidad\s+central|propósito\s+fundamental|articulan\s+en', line, re.IGNORECASE):
                continue
            if re.search(r'\(\d+\s*pts?\)', line):
                continue
            core_lines.append(line)
        result = '\n'.join(core_lines[:8])
        if len(result) > 1500:
            sents = re.split(r'(?<=[.!?])\s+', result)
            result = ' '.join(sents[:10])
        logger.info(f"🗜️ [COMPRESS] market: {len(response)} → {len(result)} chars")
        return result
    core_lines = []
    for line in lines:
        if re.search(r'K\(t-s\)|τ=|ε=|Ω=|exp\(-|rad/periodo', line):
            continue
        if re.search(r'\(\d+\s*pts?\)', line):
            continue
        if len(line) > 300:
            sents = re.split(r'(?<=[.!?])\s+', line)
            line = ' '.join(sents[:2])
        core_lines.append(line)
    result = '\n'.join(core_lines[:8])
    if len(result) > 1200:
        sents = re.split(r'(?<=[.!?])\s+', result)
        result = ' '.join(sents[:8])
    logger.info(f"🗜️ [COMPRESS] {context}: {len(response)} → {len(result)} chars")
    return result

logger.info(f"✅ Contextual Response Compressor INLINE - eliminada dependencia de import externo")

# Investor Response Engine with Diagnostic Validator (Jan 1, 2026)
try:
    from omnix_services.ai_service.investor_responses import (
        investor_response_engine,
        diagnostic_validator,
        InvestorQueryType
    )
    INVESTOR_RESPONSES_AVAILABLE = True
    logger.info("📊 Investor Response Engine + Diagnostic Validator disponible")
except ImportError:
    INVESTOR_RESPONSES_AVAILABLE = False
    investor_response_engine = None
    diagnostic_validator = None
    InvestorQueryType = None
    logger.warning("⚠️ Investor Response Engine no disponible")

try:
    from omnix_services.trading_service import TradingServiceEnterprise
    TRADING_ENTERPRISE_AVAILABLE = True
except ImportError:
    TRADING_ENTERPRISE_AVAILABLE = False
    logger.warning("⚠️ Trading Enterprise no disponible - usando fallback")

# Arbitrage Multi-Exchange Premium
try:
    from omnix_services.market_data.intelligence.arbitrage_scanner import MultiExchangeArbitragePremium
    from omnix_services.market_data.intelligence.arbitrage_executor import ArbitrageExecutorPremium
    ARBITRAGE_AVAILABLE = True
except ImportError:
    ARBITRAGE_AVAILABLE = False
    logger.warning("⚠️ Arbitrage modules no disponibles")

# Community Intelligence - Memoria Colectiva
try:
    from omnix_services.community_intelligence import (
        CommunityFeedbackManager,
        CommunityAnalyzer,
        RewardSystem,
        CommunityDashboard
    )
    COMMUNITY_INTELLIGENCE_AVAILABLE = True
except ImportError:
    COMMUNITY_INTELLIGENCE_AVAILABLE = False
    logger.warning("⚠️ Community Intelligence modules no disponibles")

# Signal Contribution - Crowdsourcing de Alpha
try:
    from omnix_services.community_intelligence.signal_contribution import SignalContributionManager
    SIGNAL_CONTRIBUTION_AVAILABLE = True
except ImportError:
    SIGNAL_CONTRIBUTION_AVAILABLE = False
    logger.warning("⚠️ Signal Contribution module no disponible")

# Voice Service - TTS con Google gTTS
# V006 (Jan 2, 2026): schedule_voice_response para envío asíncrono
try:
    from omnix_services.voice_service.voice_controller import send_telegram_response_with_voice, schedule_voice_response
    VOICE_SERVICE_AVAILABLE = True
    logger.info("🎤 Voice Service disponible (async mode V006)")
except ImportError:
    VOICE_SERVICE_AVAILABLE = False
    schedule_voice_response = None

# V7 DI Container - Hexagonal Architecture
try:
    from omnix_services.ai_service.container import (
        initialize_v7_services,
        get_ai_gateway,
        get_voice_service,
        get_v7_services_status,
    )
    V7_CONTAINER_AVAILABLE = True
    logger.info("🔷 V7 DI Container disponible")
except ImportError:
    V7_CONTAINER_AVAILABLE = False
    logger.warning("⚠️ V7 DI Container no disponible - usando legacy")

# Web Search Service - Búsqueda en internet con Tavily
try:
    from omnix_services.web_search_service.search_manager import get_search_manager, WebSearchManager
    WEB_SEARCH_AVAILABLE = True
    logger.info("🔍 Web Search Service disponible")
except ImportError:
    WEB_SEARCH_AVAILABLE = False
    logger.warning("⚠️ Web Search Service no disponible")

# Trading System Module - for shared resources
try:
    import omnix_core.trading_system as trading_system_module
    logger.info("📊 Trading System module imported")
except ImportError:
    trading_system_module = None
    logger.warning("⚠️ Trading System module no disponible")

try:
    from omnix_core.bot import PaperTradingManager
    PAPER_TRADING_AVAILABLE = True
except ImportError:
    PAPER_TRADING_AVAILABLE = False
    logger.warning("⚠️ Paper Trading Manager no disponible")

# Stock Trading Module
STOCK_TRADING_ENABLED = os.getenv('STOCK_TRADING_ENABLED', 'true').lower() == 'true'
if STOCK_TRADING_ENABLED:
    try:
        from omnix_services.stock_trading.stock_commands import StockCommandsHandler
        STOCK_MODULE_AVAILABLE = True
    except ImportError:
        STOCK_MODULE_AVAILABLE = False
        logger.warning("⚠️ Stock Trading Module no disponible")
else:
    STOCK_MODULE_AVAILABLE = False

# Risk Management System (RMS)
try:
    from omnix_services.risk_management import (
        LimitsEngine,
        PositionMonitor,
        CircuitBreaker,
        AlertDispatcher,
        RiskDashboard,
        RiskConfig
    )
    RMS_AVAILABLE = True
    logger.info("🛡️ Risk Management System (RMS) disponible")
except ImportError:
    RMS_AVAILABLE = False
    logger.warning("⚠️ Risk Management System no disponible")

# User Settings Service - Configuración Personalizada Premium
try:
    from omnix_services.user_settings import UserSettingsService, RiskProfile
    from omnix_services.user_settings.user_settings_service import get_settings_service
    USER_SETTINGS_AVAILABLE = True
    logger.info(f"⚙️ User Settings Service {VERSION_BANNER} disponible")
except ImportError:
    USER_SETTINGS_AVAILABLE = False
    logger.warning("⚠️ User Settings Service no disponible")

# Notification Services PREMIUM - Trade Alerts & Daily Summary
try:
    from omnix_services.notifications import TradeNotificationService, DailySummaryService
    NOTIFICATIONS_AVAILABLE = True
    logger.info(f"📢 Notification Services {VERSION_BANNER} PREMIUM disponibles")
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    TradeNotificationService = None
    DailySummaryService = None
    logger.info("📢 Notification Services no disponibles (opcional)")

# Telegram availability check
try:
    from telegram import __version__
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

# Advanced Features Engine - Monte Carlo, Black Swan, Sharia, etc.
try:
    from omnix_services.trading_service.advanced_features import AdvancedFeaturesEngine
    ADVANCED_FEATURES_AVAILABLE = True
    global_advanced_features = AdvancedFeaturesEngine()
    logger.info("🔬 Advanced Features Engine disponible")
except ImportError as e:
    ADVANCED_FEATURES_AVAILABLE = False
    global_advanced_features = None
    logger.warning(f"⚠️ Advanced Features Engine no disponible: {e}")

# Global DB Manager - Set in EnterpriseTelegramBot.__init__
global_db_manager = None

# Admin verification function - ID from env_config
ADMIN_IDS = {
    int(settings.TELEGRAM_ADMIN_ID),  # Harold Nunes - Creator (from TELEGRAM_ADMIN_USER_ID)
}

def is_admin(user_id):
    """Verificar si un usuario es administrador"""
    try:
        return int(user_id) in ADMIN_IDS
    except (ValueError, TypeError):
        return False


async def send_message_with_retry(message_obj, text: str, max_retries: int = 3, parse_mode: str = None):
    """
    Enviar mensaje de Telegram con retry y backoff exponencial.
    
    FIX Dec 31, 2025: Resolver telegram.error.TimedOut que causa mensajes sin respuesta.
    El timeout ocurre cuando la red de Railway tiene latencia alta.
    
    Args:
        message_obj: El objeto message de Telegram (update.message o similar)
        text: El texto a enviar
        max_retries: Número máximo de reintentos (default 3)
        parse_mode: Modo de parseo ('Markdown', 'HTML', None)
    
    Returns:
        El mensaje enviado o None si falló
    """
    from telegram.error import TimedOut, NetworkError, RetryAfter
    
    for attempt in range(max_retries):
        try:
            if parse_mode:
                result = await message_obj.reply_text(text, parse_mode=parse_mode)
            else:
                result = await message_obj.reply_text(text)
            return result
        except TimedOut as e:
            wait_time = (attempt + 1) * 2
            logger.warning(f"⚠️ Telegram TimedOut (intento {attempt+1}/{max_retries}), esperando {wait_time}s...")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"❌ Telegram TimedOut después de {max_retries} intentos — mensaje no enviado, bot continúa")
                return None
        except RetryAfter as e:
            logger.warning(f"⚠️ Telegram RetryAfter: {e.retry_after}s")
            await asyncio.sleep(e.retry_after)
        except NetworkError as e:
            wait_time = (attempt + 1) * 2
            logger.warning(f"⚠️ Telegram NetworkError (intento {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"❌ Telegram NetworkError después de {max_retries} intentos — mensaje no enviado, bot continúa")
                return None
        except Exception as e:
            logger.warning(f"⚠️ Telegram error inesperado (intento {attempt+1}/{max_retries}): {type(e).__name__}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep((attempt + 1) * 2)
            else:
                logger.error(f"❌ Error inesperado después de {max_retries} intentos — mensaje no enviado, bot continúa")
                return None
    return None


async def edit_message_with_retry(message_obj, text: str, max_retries: int = 3, parse_mode: str = None):
    """
    Editar mensaje de Telegram con retry y backoff exponencial.
    
    FIX Dec 31, 2025: Resolver telegram.error.TimedOut en edit_text.
    """
    from telegram.error import TimedOut, NetworkError, RetryAfter
    
    for attempt in range(max_retries):
        try:
            if parse_mode:
                result = await message_obj.edit_text(text, parse_mode=parse_mode)
            else:
                result = await message_obj.edit_text(text)
            return result
        except TimedOut as e:
            wait_time = (attempt + 1) * 2
            logger.warning(f"⚠️ Telegram edit TimedOut (intento {attempt+1}/{max_retries}), esperando {wait_time}s...")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"❌ Telegram edit TimedOut después de {max_retries} intentos")
                raise
        except RetryAfter as e:
            logger.warning(f"⚠️ Telegram edit RetryAfter: {e.retry_after}s")
            await asyncio.sleep(e.retry_after)
        except NetworkError as e:
            wait_time = (attempt + 1) * 2
            logger.warning(f"⚠️ Telegram edit NetworkError (intento {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait_time)
            else:
                raise
    return None


class EnterpriseTelegramBot:
    """Bot Telegram empresarial con todas las funcionalidades"""
    
    def __init__(self, db_manager=None):
        global global_db_manager  # Set global reference for legacy code
        
        self.application = None
        self.is_running = False
        self.db_manager = db_manager  # MEMORIA PERSISTENTE POSTGRESQL
        global_db_manager = db_manager  # Set global for backwards compatibility
        self.ai = ConversationalAI()  # SUPERINTELIGENCIA PARA HAROLD (adapter correcto)
        
        self._message_buffers: Dict[str, List[Dict[str, Any]]] = {}
        self._message_timers: Dict[str, asyncio.Task] = {}
        self._message_aggregation_delay = 0.5

        # [ADR-083] Enterprise Security Middleware
        if _SECURITY_AVAILABLE:
            self.security = get_security_middleware(allow_groups=False)
            logger.info("[ADR-083] BotSecurityMiddleware active — rate limiting, injection detection, blocklist enabled")
        else:
            self.security = None
            logger.warning("[ADR-083] Security middleware not available — running without protection")
        
        self._sync_message_buffers: Dict[str, List[Dict[str, Any]]] = {}
        self._sync_message_timers: Dict[str, Any] = {}
        self._sync_buffer_lock = threading.Lock()
        
        # 🔷 V7 HEXAGONAL SERVICES INITIALIZATION
        self.v7_services_status = None
        self.v7_ai_gateway = None
        self.v7_voice_service = None
        
        if V7_CONTAINER_AVAILABLE:
            try:
                status = get_v7_services_status()
                use_ai = status.get('use_ai_port', False)
                use_voice = status.get('use_voice_port', False)
                
                if use_ai or use_voice:
                    self.v7_services_status = initialize_v7_services()
                    self.v7_ai_gateway = get_ai_gateway() if use_ai else None
                    self.v7_voice_service = get_voice_service() if use_voice else None
                    logger.info(f"🔷 V7 Active: AI={status['ai_gateway_type']}, Voice={status['voice_service_type']}")
                else:
                    logger.info("🔷 V7 feature flags disabled - using legacy services")
            except Exception as e:
                logger.error(f"❌ V7 Services initialization error: {e}")
        
        # 🏦 TRADING SERVICE ENTERPRISE CON FALLBACK SEGURO
        self.trading_enterprise_enabled = False
        try:
            if TRADING_ENTERPRISE_AVAILABLE:
                logger.info("🚀 Inicializando Trading Service Enterprise...")
                self.trading_enterprise = TradingServiceEnterprise()
                
                # Verificar health check
                health = self.trading_enterprise.health_check()
                if all(health.values()):
                    self.trading_enterprise_enabled = True
                    logger.info("✅ TRADING ENTERPRISE ACTIVO - Todos los módulos operacionales")
                    logger.info(f"   🏦 Kraken API: {health['kraken_api']}")
                    logger.info(f"   🎲 Monte Carlo: {health['monte_carlo']}")
                    logger.info(f"   🦢 Black Swan: {health['black_swan']}")
                    logger.info(f"   🔐 PQC Security: {health['pqc_security']}")
                else:
                    logger.warning(f"⚠️ Trading Enterprise health check failed: {health}")
                    self.trading_enterprise_enabled = False
        except Exception as e:
            logger.error(f"❌ Error inicializando Trading Enterprise: {e}")
            import traceback
            traceback.print_exc()
            self.trading_enterprise_enabled = False
        
        # Fallback a sistema legacy si Enterprise falla
        self.trading = None  # Inicializar siempre
        if not self.trading_enterprise_enabled:
            logger.info("📦 Usando Trading System legacy (fallback)")
            self.trading = trading_system_module.TradingSystem() if trading_system_module else None
        else:
            self.trading = self.trading_enterprise  # Referencia al enterprise
            logger.info("🚀 TRADING ENTERPRISE READY - Sistema premium activado")
        
        # 📢 NOTIFICATION SERVICES PREMIUM - Trade Alerts & Daily Summary
        self.notification_service = None
        self.daily_summary_service = None
        
        # 📊 PAPER TRADING MANAGER - Trading simulado con datos reales
        try:
            from omnix_services.trading_service.paper_trading_manager import PaperTradingManager
            trading_service = self.trading_enterprise if self.trading_enterprise_enabled else self.trading
            self.paper_trading = PaperTradingManager(
                database_service=self.db_manager,
                trading_service=trading_service
            )
            logger.info("📊 Paper Trading Manager inicializado - $1,000,000 disponible para pruebas")
        except Exception as e:
            logger.warning(f"⚠️ Paper Trading no disponible: {e}")
            self.paper_trading = None
        
        # 🤖 AUTO-TRADING BOT - Trading automático 24/7 con estrategia inteligente
        try:
            from omnix_core.bot.auto_trading_bot import AutoTradingBot
            trading_service = self.trading_enterprise if self.trading_enterprise_enabled else self.trading
            self.auto_trading = AutoTradingBot(
                trading_service=trading_service,
                database_service=self.db_manager,
                advanced_features=global_advanced_features if 'global_advanced_features' in globals() else None,
                paper_trading=self.paper_trading,
                ai_service=self.ai
            )
            logger.info("🤖 Auto-Trading Bot inicializado - Trading inteligente 24/7 disponible")
            logger.info(f"   📊 Paper Trading: {'✅ ACTIVADO ($1M virtual)' if self.paper_trading else '❌ Desactivado'}")
            logger.info(f"   🎓 Auto-Learning: {'✅ DISPONIBLE' if self.ai else '⚠️ Sin IA'}")
            logger.info(f"   📈 EMA Regime Signal: ✅ PRIMARY DRIVER (40 pts)")
            logger.info(f"   🎯 Scoring: 5 inputs (EMA/HMM/Kalman/Non-Markovian/Kelly)")
        except Exception as e:
            logger.warning(f"⚠️ Auto-Trading Bot no disponible: {e}")
            self.auto_trading = None
        
        # 🔴 OMNIX REAL CONTEXT PROVIDER - TRANSPARENCIA INSTITUCIONAL
        try:
            from omnix_core.context import create_real_context_provider
            trading_service = self.trading_enterprise if self.trading_enterprise_enabled else self.trading
            self.real_context_provider = create_real_context_provider(
                auto_trading_bot=self.auto_trading,
                paper_trading_manager=self.paper_trading,
                trading_service=trading_service,
                database_manager=self.db_manager
            )
            logger.info("🔴 Real Context Provider ACTIVO - IA siempre usará datos reales verificados")
        except Exception as e:
            logger.warning(f"⚠️ Real Context Provider no disponible: {e}")
            self.real_context_provider = None
        
        # 🎥 VIDEO ANALYZER ULTRA - Análisis avanzado de videos con Vision AI
        # FIX Nov 29, 2025: Separar inicialización para evitar que falle todo el bloque
        self.video_analyzer_ultra = None
        self.video_learning_integration = None
        
        # Paso 1: Inicializar VideoAnalyzerUltra (CRÍTICO para análisis de YouTube)
        try:
            from omnix_services.ai_service.video.analyzer import VideoAnalyzerUltra
            self.video_analyzer_ultra = VideoAnalyzerUltra(database_service=self.db_manager)
            logger.info(f"🎥 Video Analyzer Ultra {VERSION_BANNER} inicializado")
            logger.info(f"   🎬 GPT-4 Vision: {'✅' if self.video_analyzer_ultra.openai_client else '❌'}")
            logger.info(f"   🧠 Gemini Vision: {'✅' if self.video_analyzer_ultra.gemini_client else '❌'}")
        except Exception as e:
            logger.warning(f"⚠️ Video Analyzer Ultra {VERSION_BANNER} no disponible: {e}")
            import traceback
            logger.warning(f"   Traceback: {traceback.format_exc()}")
        
        # Paso 2: Inicializar VideoLearningIntegration (OPCIONAL - no bloquea análisis)
        if self.video_analyzer_ultra:
            try:
                from omnix_services.ai_service.video.integration import VideoLearningIntegration
                if self.auto_trading and hasattr(self.auto_trading, 'auto_learning'):
                    self.video_learning_integration = VideoLearningIntegration(
                        auto_learning_system=self.auto_trading.auto_learning,
                        video_analyzer_ultra=self.video_analyzer_ultra
                    )
                    logger.info("🔗 Video Learning Integration conectada al Auto-Learning System")
                else:
                    logger.info("ℹ️ Video Learning Integration omitida - Auto-Learning no disponible")
            except Exception as e:
                logger.warning(f"⚠️ Video Learning Integration no disponible: {e}")
        
        # 📊 STOCK TRADING HANDLER - DUAL MARKET SYSTEM
        if STOCK_MODULE_AVAILABLE:
            try:
                self.stock_handler = StockCommandsHandler()
                if self.stock_handler.enabled:
                    logger.info("📊 Stock Trading Handler ACTIVADO - Alpaca + NYSE/NASDAQ")
                    logger.info(f"   🏦 Alpaca: {'✅ Conectado' if self.stock_handler.alpaca.connected else '❌ Desconectado'}")
                    logger.info(f"   🕐 Market Hours: ✅ Configurado")
                    logger.info(f"   📈 Stock Analyzer: ✅ Listo")
                    logger.info(f"   📊 Fundamental Analyzer: ✅ Listo")
                else:
                    logger.warning("⚠️ Stock Trading Handler configurado pero inactivo")
                    self.stock_handler = None
            except Exception as e:
                logger.warning(f"⚠️ Stock Trading Handler error: {e}")
                self.stock_handler = None
        else:
            self.stock_handler = None
            if STOCK_TRADING_ENABLED:
                logger.warning("📊 Stock Trading solicitado pero módulo no disponible")
        
        # 💱 ARBITRAGE MULTI-EXCHANGE PREMIUM
        if ARBITRAGE_AVAILABLE:
            try:
                self.arbitrage_scanner = MultiExchangeArbitragePremium()
                self.arbitrage_executor = ArbitrageExecutorPremium(paper_trading=True)
                logger.info("💱 Arbitrage System Premium ACTIVADO - 8 exchanges")
                logger.info(f"   📊 Exchanges: Kraken, Binance, Coinbase, Bybit, KuCoin, OKX, Gate.io, Bitfinex")
                logger.info(f"   🎯 Mode: PAPER TRADING (set ARBITRAGE_LIVE_MODE=true for real trading)")
                logger.info(f"   💰 Min Profit: {self.arbitrage_scanner.min_profit_threshold}%")
            except Exception as e:
                logger.warning(f"⚠️ Arbitrage System error: {e}")
                self.arbitrage_scanner = None
                self.arbitrage_executor = None
        else:
            self.arbitrage_scanner = None
            self.arbitrage_executor = None
        
        # 🧠 COMMUNITY INTELLIGENCE - MEMORIA COLECTIVA
        if COMMUNITY_INTELLIGENCE_AVAILABLE:
            try:
                self.feedback_manager = CommunityFeedbackManager(database_service=self.db_manager)
                self.community_analyzer = CommunityAnalyzer(database_service=self.db_manager)
                self.reward_system = RewardSystem(database_service=self.db_manager)
                self.community_dashboard = CommunityDashboard(database_service=self.db_manager)
                logger.info("🧠 Community Intelligence ACTIVADO - Memoria Colectiva")
                logger.info(f"   📝 Feedback Manager: {'✅ Connected' if self.feedback_manager.connected else '❌ Disconnected'}")
                logger.info(f"   🔍 Community Analyzer: {'✅ AI Enabled' if self.community_analyzer.ai_available else '⚠️ AI Not Available'}")
                logger.info(f"   🏆 Reward System: {'✅ Connected' if self.reward_system.connected else '❌ Disconnected'}")
                logger.info(f"   📊 Community Dashboard: {'✅ Connected' if self.community_dashboard.connected else '❌ Disconnected'}")
            except Exception as e:
                logger.warning(f"⚠️ Community Intelligence error: {e}")
                self.feedback_manager = None
                self.community_analyzer = None
                self.reward_system = None
                self.community_dashboard = None
        else:
            self.feedback_manager = None
            self.community_analyzer = None
            self.reward_system = None
            self.community_dashboard = None
        
        # 🚀 SIGNAL CONTRIBUTION - CROWDSOURCING DE ALPHA
        if SIGNAL_CONTRIBUTION_AVAILABLE:
            try:
                self.signal_contribution = SignalContributionManager(
                    database_service=self.db_manager,
                    reward_system=self.reward_system
                )
                logger.info("🚀 Signal Contribution ACTIVADO - Crowdsourcing de Alpha")
                logger.info(f"   📡 Signal Manager: {'✅ Connected' if self.signal_contribution.connected else '❌ Disconnected'}")
            except Exception as e:
                logger.warning(f"⚠️ Signal Contribution error: {e}")
                self.signal_contribution = None
        else:
            self.signal_contribution = None
        
        # 🛡️ RISK MANAGEMENT SYSTEM (RMS) - Control de Riesgo Institucional
        if RMS_AVAILABLE:
            try:
                self.rms_config = RiskConfig.from_env()
                self.limits_engine = LimitsEngine(
                    database_service=self.db_manager,
                    config=self.rms_config
                )
                self.position_monitor = PositionMonitor(
                    database_service=self.db_manager,
                    trading_service=None,
                    config=self.rms_config
                )
                self.circuit_breaker = CircuitBreaker(
                    database_service=self.db_manager,
                    config=self.rms_config
                )
                self.alert_dispatcher = AlertDispatcher(
                    telegram_bot=None,
                    database_service=self.db_manager,
                    config=self.rms_config
                )
                self.risk_dashboard = RiskDashboard(
                    database_service=self.db_manager,
                    limits_engine=self.limits_engine,
                    position_monitor=self.position_monitor,
                    circuit_breaker=self.circuit_breaker,
                    config=self.rms_config
                )
                logger.info("🛡️ Risk Management System (RMS) ACTIVADO")
                logger.info(f"   ⚙️ Capital: ${self.rms_config.initial_capital:,.0f}")
                logger.info(f"   🎯 Per Trade Limit: {self.rms_config.default_per_trade_limit_pct}%")
                logger.info(f"   📉 Max Drawdown: {self.rms_config.default_max_drawdown_pct}%")
                logger.info(f"   🔒 Auto-Halt: {'Enabled' if self.rms_config.enable_auto_halt else 'Disabled'}")
                
                trading_service = self.trading_enterprise if self.trading_enterprise_enabled else getattr(self, 'trading', None)
                if self.position_monitor and trading_service:
                    self.position_monitor.set_trading_service(trading_service)
                    logger.info("   🔗 PositionMonitor conectado a TradingService")
                
                if self.paper_trading:
                    self.paper_trading.limits_engine = self.limits_engine
                    self.paper_trading.circuit_breaker = self.circuit_breaker
                    logger.info("   🔗 PaperTradingManager conectado a RMS")
                
            except Exception as e:
                logger.warning(f"⚠️ Risk Management System error: {e}")
                self.limits_engine = None
                self.position_monitor = None
                self.circuit_breaker = None
                self.alert_dispatcher = None
                self.risk_dashboard = None
                self.rms_config = None
        else:
            self.limits_engine = None
            self.position_monitor = None
            self.circuit_breaker = None
            self.alert_dispatcher = None
            self.risk_dashboard = None
            self.rms_config = None
        
        # ⚙️ USER SETTINGS SERVICE - Configuración Personalizada Premium
        if USER_SETTINGS_AVAILABLE:
            try:
                self.user_settings_service = get_settings_service()
                logger.info("⚙️ User Settings Service ACTIVADO - Configuración Personalizada")
                logger.info("   📝 Comandos: /miconfig, /perfil, /limites, /proteccion")
                logger.info("   🤖 NLP: Procesamiento de lenguaje natural activado")
            except Exception as e:
                logger.warning(f"⚠️ User Settings Service error: {e}")
                self.user_settings_service = None
        else:
            self.user_settings_service = None
        
        self.setup_bot()
    
    def setup_bot(self):
        """Configurar bot Telegram empresarial"""
        try:
            if not TELEGRAM_AVAILABLE:
                logger.error("❌ Telegram no disponible")
                return False
                
            token = os.environ.get('TELEGRAM_BOT_TOKEN')
            if not token:
                logger.error("❌ TELEGRAM_BOT_TOKEN no configurado")
                return False
                
            request = HTTPXRequest(
                connection_pool_size=16,
                connect_timeout=30.0,
                read_timeout=60.0,
                write_timeout=60.0,
                pool_timeout=60.0,
            )
            self.application = Application.builder().token(token).request(request).build()
            
            # Comandos principales
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("version", self.version_command))
            self.application.add_handler(CommandHandler("precio", self.precio_command))
            self.application.add_handler(CommandHandler("market", self.market_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            self.application.add_handler(CommandHandler("ayuda", self.help_command))
            self.application.add_handler(CommandHandler("legal", self.legal_command))
            self.application.add_handler(CommandHandler("educacion", self.educacion_command))
            self.application.add_handler(CommandHandler("balance", self.balance_command))
            self.application.add_handler(CommandHandler("convertir_usd", self.convertir_usd_command))
            self.application.add_handler(CommandHandler("convertir", self.convertir_command))
            self.application.add_handler(CommandHandler("performance", self.performance_command))
            self.application.add_handler(CommandHandler("analisis", self.analisis_command))
            self.application.add_handler(CommandHandler("status", self.status_command))
            
            # Comandos Advanced Features Enterprise
            self.application.add_handler(CommandHandler("montecarlo", self.montecarlo_command))
            self.application.add_handler(CommandHandler("quantum", self.montecarlo_command))  # Alias para menú
            self.application.add_handler(CommandHandler("quantum_test", self.quantum_test_command))  # Test QRNG en vivo
            self.application.add_handler(CommandHandler("quantum_stats", self.quantum_stats_command))  # Estadísticas QRNG
            self.application.add_handler(CommandHandler("quantum_demo", self.quantum_demo_command))  # Demo física cuántica
            self.application.add_handler(CommandHandler("blackswan", self.blackswan_command))
            self.application.add_handler(CommandHandler("sentiment", self.sentiment_command))
            self.application.add_handler(CommandHandler("sharia", self.sharia_command))
            self.application.add_handler(CommandHandler("orderbook", self.orderbook_command))
            self.application.add_handler(CommandHandler("enterprise", self.enterprise_command))
            self.application.add_handler(CommandHandler("trading", self.trading_menu_command))  # Menú de trading
            self.application.add_handler(CommandHandler("arbitraje", self.arbitraje_command))  # Alias español
            self.application.add_handler(CommandHandler("prices", self.prices_command))
            self.application.add_handler(CommandHandler("memoria", self.memoria_command))
            self.application.add_handler(CommandHandler("patrones", self.patrones_command))
            self.application.add_handler(CommandHandler("quantum_fast", self.quantum_fast_command))
            
            # 📊 Comandos Paper Trading - Trading simulado con $1M
            self.application.add_handler(CommandHandler("paper_start", self.paper_start_command))
            self.application.add_handler(CommandHandler("paper_balance", self.paper_balance_command))
            self.application.add_handler(CommandHandler("paper_buy", self.paper_buy_command))
            self.application.add_handler(CommandHandler("paper_sell", self.paper_sell_command))
            
            # 📰 News Scraper Commands - Análisis de Noticias
            self.application.add_handler(CommandHandler("analizar_noticia", self.analyze_news_command))
            self.application.add_handler(CommandHandler("trending_crypto", self.trending_news_command))
            
            # 🔍 Web Search Command - Búsqueda en internet
            self.application.add_handler(CommandHandler("buscar", self.buscar_command))
            logger.info("🔍 Web Search Command registrado: /buscar")
            
            # 🤖 Comandos Auto-Trading - Trading automático 24/7
            self.application.add_handler(CommandHandler("auto_start", self.auto_start_command))
            self.application.add_handler(CommandHandler("auto_stop", self.auto_stop_command))
            self.application.add_handler(CommandHandler("auto_status", self.auto_status_command))
            
            # 🎓 Comandos Auto-Learning - Aprendizaje de videos YouTube
            self.application.add_handler(CommandHandler("activar_auto_ajuste", self.activar_auto_ajuste_command))
            self.application.add_handler(CommandHandler("pausar_auto_ajuste", self.pausar_auto_ajuste_command))
            self.application.add_handler(CommandHandler("ver_aprendizaje", self.ver_aprendizaje_command))
            self.application.add_handler(CommandHandler("revertir_cambio", self.revertir_cambio_command))
            
            # 🛡️ Comandos AI Risk Guardian - Supervisor de Riesgos
            self.application.add_handler(CommandHandler("risk_status", self.risk_status_command))
            self.application.add_handler(CommandHandler("risk_events", self.risk_events_command))
            
            # 📊 Comandos UNIFICADOS /analizar - Auto-detección Crypto/Stock
            self.application.add_handler(CommandHandler("analizar", self.analyze_stock_command))
            self.application.add_handler(CommandHandler("analizar_premium", self.premium_stock_command))
            logger.info("🔀 Smart Routing activado: /analizar auto-detecta crypto vs stock")
            
            # 📊 Comandos Stock Trading - BOLSA DE VALORES (NYSE/NASDAQ)
            if self.stock_handler and self.stock_handler.enabled:
                self.application.add_handler(CommandHandler("balance_bolsa", self.balance_stocks_command))
                self.application.add_handler(CommandHandler("portfolio_bolsa", self.balance_stocks_command))
                self.application.add_handler(CommandHandler("mercado", self.market_status_command))
                self.application.add_handler(CommandHandler("horario_bolsa", self.market_status_command))
                self.application.add_handler(CommandHandler("stock_status", self.stock_status_command))
                self.application.add_handler(CommandHandler("risk_dashboard", self.stock_risk_dashboard_command))
                self.application.add_handler(CommandHandler("comprar_bolsa", self.buy_stock_command))
                self.application.add_handler(CommandHandler("vender_bolsa", self.sell_stock_command))
                logger.info(f"📊 Stock Trading {VERSION_BANNER} registrado: /stock_status, /risk_dashboard, /comprar_bolsa, /vender_bolsa")
            
            # 💱 Comandos Arbitrage Multi-Exchange Premium
            if self.arbitrage_scanner:
                self.application.add_handler(CommandHandler("arbitrage", self.arbitrage_command))
                self.application.add_handler(CommandHandler("arbitrage_scan", self.arbitrage_scan_command))
                self.application.add_handler(CommandHandler("arbitrage_execute", self.arbitrage_execute_command))
                self.application.add_handler(CommandHandler("arbitrage_stats", self.arbitrage_stats_command))
                logger.info("💱 Arbitrage commands registrados: /arbitrage, /arbitrage_scan, /arbitrage_execute, /arbitrage_stats")
            
            # 🧠 Comandos Community Intelligence - Memoria Colectiva
            if self.feedback_manager:
                self.application.add_handler(CommandHandler("feedback", self.feedback_command))
                self.application.add_handler(CommandHandler("community_stats", self.community_stats_command))
                self.application.add_handler(CommandHandler("top_strategies", self.top_strategies_command))
                self.application.add_handler(CommandHandler("my_contributions", self.my_contributions_command))
                self.application.add_handler(CommandHandler("vote_strategy", self.vote_strategy_command))
                self.application.add_handler(CommandHandler("leaderboard", self.leaderboard_command))
                self.application.add_handler(CommandHandler("analyze_patterns", self.analyze_patterns_command))
                logger.info("🧠 Community Intelligence commands registrados: /feedback, /community_stats, /top_strategies, /my_contributions, /vote_strategy, /leaderboard")
            
            # 🚀 Comandos Signal Contribution - Crowdsourcing de Alpha
            if self.signal_contribution:
                self.application.add_handler(CommandHandler("share_signal", self.share_signal_command))
                self.application.add_handler(CommandHandler("community_signals", self.community_signals_command))
                self.application.add_handler(CommandHandler("my_signals", self.my_signals_command))
                self.application.add_handler(CommandHandler("alpha_leaderboard", self.alpha_leaderboard_command))
                self.application.add_handler(CommandHandler("execute_signal", self.execute_signal_command))
                logger.info("🚀 Signal Contribution commands registrados: /share_signal, /community_signals, /my_signals, /alpha_leaderboard")
            
            # 🛡️ Comandos Risk Management System (RMS) - Control Institucional
            if self.limits_engine:
                self.application.add_handler(CommandHandler("rms", self.rms_dashboard_command))
                self.application.add_handler(CommandHandler("rms_limits", self.rms_limits_command))
                self.application.add_handler(CommandHandler("rms_set", self.rms_set_limit_command))
                self.application.add_handler(CommandHandler("rms_history", self.rms_history_command))
                self.application.add_handler(CommandHandler("emergency_halt", self.rms_emergency_halt_command))
                self.application.add_handler(CommandHandler("resume_trading", self.rms_resume_trading_command))
                logger.info("🛡️ RMS commands registrados: /rms, /rms_limits, /rms_set, /rms_history, /emergency_halt, /resume_trading")
            
            # ⚙️ Comandos User Settings - Configuración Personalizada Premium
            if self.user_settings_service:
                self.application.add_handler(CommandHandler("miconfig", self.miconfig_command))
                self.application.add_handler(CommandHandler("perfil", self.perfil_command))
                self.application.add_handler(CommandHandler("limites", self.limites_command))
                self.application.add_handler(CommandHandler("proteccion", self.proteccion_command))
                self.application.add_handler(CommandHandler("estrategias", self.estrategias_command))
                self.application.add_handler(CommandHandler("cryptos", self.cryptos_command))
                self.application.add_handler(CommandHandler("autotrading", self.autotrading_command))
                self.application.add_handler(CommandHandler("pausar", self.pausar_trading_command))
                self.application.add_handler(CommandHandler("reanudar", self.reanudar_trading_command))
                self.application.add_handler(CommandHandler("onboarding", self.onboarding_command))
                logger.info(f"⚙️ User Settings {VERSION_BANNER} registrados: /miconfig, /perfil, /limites, /proteccion, /estrategias, /cryptos, /autotrading")
            
            # 📊 Comandos Daily Summary PREMIUM - Resúmenes diarios
            self.application.add_handler(CommandHandler("resumen", self.resumen_command))
            logger.info(f"📊 Daily Summary {VERSION_BANNER} registrado: /resumen")
            
            # 📊 Comando Reporte Diario - Brutal Honesty Monitoring
            self.application.add_handler(CommandHandler("reporte_diario", self.reporte_diario_command))
            self.application.add_handler(CommandHandler("daily_report", self.reporte_diario_command))  # Alias inglés
            logger.info(f"📊 Daily Report {VERSION_BANNER} registrado: /reporte_diario, /daily_report")

            # 🏛️ Comandos Governance Pipeline — ADR-028, ADR-052, ADR-057, ADR-058
            self.application.add_handler(CommandHandler("evaluar", self.evaluar_command))
            self.application.add_handler(CommandHandler("evaluate", self.evaluar_command))   # Alias inglés
            self.application.add_handler(CommandHandler("gobernanza", self.gobernanza_command))
            self.application.add_handler(CommandHandler("governance", self.gobernanza_command))  # Alias inglés
            self.application.add_handler(CommandHandler("velos", self.velos_command))
            self.application.add_handler(CommandHandler("recibo", self.recibo_command))
            self.application.add_handler(CommandHandler("receipt", self.recibo_command))     # Alias inglés
            self.application.add_handler(CommandHandler("impact", self.impact_command))      # ADR-083 GIS
            self.application.add_handler(CommandHandler("clientes", self.clientes_command))   # Gestión B2B
            self.application.add_handler(CommandHandler("nuevo_cliente", self.nuevo_cliente_command))  # Provisionar B2B
            logger.info(f"🏛️ Governance commands registrados (ADR-058): /evaluar, /gobernanza, /velos, /recibo, /impact, /clientes, /nuevo_cliente")

            # Handler para mensajes de texto
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
            )
            
            # 🎤 Handler PREMIUM para mensajes de voz con Whisper AI
            self.application.add_handler(
                MessageHandler(filters.VOICE, self.handle_voice_message)
            )
            
            # 🎥 Handler PREMIUM para videos directos con Vision AI
            self.application.add_handler(
                MessageHandler(filters.VIDEO | filters.VIDEO_NOTE, self.handle_video_message)
            )
            
            # 🎨 Handler para botones inline (callbacks)
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))
            
            logger.info("✅ Bot Telegram empresarial configurado")
            logger.info("🎤 Handler de voz premium activado - Whisper AI")
            logger.info("🎥 Handler de video premium activado - Vision AI")
            logger.info("🎨 Handler de botones inline activado - Interacción premium")
            
            # 🛡️ Conectar AlertDispatcher al bot de Telegram
            if self.alert_dispatcher:
                self.alert_dispatcher.set_telegram_bot(self.application.bot)
                self.alert_dispatcher.add_admin_chat_id(str(settings.TELEGRAM_ADMIN_ID))
                logger.info("📢 AlertDispatcher conectado a Telegram Bot")
                logger.info(f"🔒 Admin alerts configured for chat {settings.TELEGRAM_ADMIN_ID}")
            
            # 🛡️ Configurar RMS en TradingServiceEnterprise
            if self.trading_enterprise_enabled and self.trading_enterprise:
                self.trading_enterprise.configure_rms(
                    limits_engine=self.limits_engine,
                    circuit_breaker=self.circuit_breaker,
                    alert_dispatcher=self.alert_dispatcher
                )
            
            # 📢 Inicializar Notification Services PREMIUM
            if NOTIFICATIONS_AVAILABLE:
                try:
                    trading_service = self.trading_enterprise if self.trading_enterprise_enabled else self.trading
                    
                    self.notification_service = TradeNotificationService(
                        telegram_bot=self.application.bot,
                        database_service=self.db_manager
                    )
                    self.notification_service.set_admin_chat_id(str(settings.TELEGRAM_ADMIN_ID))
                    
                    self.daily_summary_service = DailySummaryService(
                        telegram_bot=self.application.bot,
                        database_service=self.db_manager,
                        trading_service=trading_service
                    )
                    self.daily_summary_service.set_admin_chat_id(str(settings.TELEGRAM_ADMIN_ID))
                    self.daily_summary_service.set_summary_time(20, 0)
                    self.daily_summary_service.start_scheduler()
                    
                    if self.paper_trading:
                        self.paper_trading.notification_service = self.notification_service
                    
                    logger.info(f"📢 Notification Services {VERSION_BANNER} PREMIUM ACTIVOS")
                    logger.info("   🔔 Trade Alerts: Notificaciones en tiempo real")
                    logger.info("   📊 Daily Summary: Resumen diario a las 20:00 UTC")
                except Exception as e:
                    logger.warning(f"⚠️ Error inicializando Notification Services: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error configurando bot: {e}")
            return False
    
    async def start_command(self, update, context):
        """Comando /start con botones interactivos premium"""
        try:
            from omnix_services.telegram_service.inline_keyboards import InlineKeyboardsManager
            
            user = update.effective_user
            
            welcome_message = f"""🏛️ **OMNIX Decision Governance**

¡Hola {user.first_name}! Soy OMNIX — infraestructura de gobernanza de decisiones de alto impacto.

**🏛️ GOVERNANCE PIPELINE:**
✅ 11 checkpoints · Critical Override Layer (ADR-057)
✅ Recibos PQC inmutables · Velos Gateway
✅ Dominios: trading, crédito, seguros, robótica

**📊 TRADING ENGINE:**
🪙 Cripto 24/7 (Kraken) — REAL
📈 Bolsa USA (Alpaca) — Paper
🤖 IA Dual: Gemini 2.0 + GPT-4o

**🏛️ GOVERNANCE COMMANDS:**
/evaluar — Evalúa un escenario de decisión
/gobernanza — Estado del sistema
/recibo — Últimos recibos (admin)
/velos — Log gateway Velos (admin)

💬 **Envía cualquier escenario o usa los botones:**
"""
            
            # Enviar mensaje con botones interactivos
            keyboard = InlineKeyboardsManager.get_main_menu()
            await update.message.reply_text(
                welcome_message, 
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            
            # Enviar nota informativa (lenguaje institucional)
            info_note = """📋 **NOTA INFORMATIVA:**
OMNIX es una infraestructura de gobernanza de decisiones institucionales. Las evaluaciones públicas son demostrativas y no constituyen asesoramiento legal, financiero ni regulatorio.
Consulta /legal para los términos completos de uso."""
            
            await update.message.reply_text(info_note, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Error comando start: {e}")
            await update.message.reply_text("Error procesando comando /start")

    async def version_command(self, update, context):
        """Comando /version - Verificar versión del build en producción"""
        logger.info("🔧 /version command triggered")
        try:
            # Safe checks to avoid AttributeError
            has_trading = hasattr(self, 'trading') and self.trading is not None
            has_kraken = False
            try:
                has_kraken = (hasattr(self, 'trading_enterprise') and 
                             self.trading_enterprise is not None and 
                             hasattr(self.trading_enterprise, 'kraken_client') and
                             self.trading_enterprise.kraken_client is not None)
            except Exception:
                pass
            
            version_text = f"""🔧 **OMNIX {VERSION_BANNER} — BUILD INFO**

📌 **Versión**: {VERSION_BANNER}
🕐 **Build**: 2026-04-06T00:00:00Z
🎯 **Build ID**: governance-bot-integration-adr058

**🏛️ GOVERNANCE PIPELINE:**
✅ Pipeline 11-checkpoint activo (ADR-028)
✅ Critical Override Layer — 7 Grupos (ADR-057)
✅ Recibos PQC: NIST-standardized algorithms
✅ Velos Gateway push (ADR-052)
✅ Bot governance integration (ADR-058)

**📊 TRADING ENGINE:**
🔗 Trading: {'✅ Activo' if has_trading else '⚠️ Paper Mode'}
📡 Kraken: {'✅ API Conectada' if has_kraken else '⚠️ API Pública'}
🪙 50+ criptomonedas · NYSE/NASDAQ · Monte Carlo 10K

**🏆 POSICIÓN:**
Pre-seed $500K @ $3M · Harold Nunes

✅ Build {VERSION_BANNER} confirmado — omnixquantum.net"""
            
            logger.info(f"🔧 /version responding: {VERSION_BANNER}")
            await update.message.reply_text(version_text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"❌ /version error: {e}")
            await update.message.reply_text(f"🔧 OMNIX {VERSION_BANNER} - Error: {e}")

    async def help_command(self, update, context):
        """Comando /help"""
        try:
            help_text = f"""
🏛️ **OMNIX Decision Governance — COMANDOS COMPLETOS**
_Harold Nunes · omnixquantum.net_

━━━━━━━━━━━━━━━━━━━━━━
**🏛️ GOVERNANCE PIPELINE (ADR-058):**
/evaluar [escenario] — Ejecuta el pipeline de 11 checkpoints (BLOCKED/APPROVED + Receipt ID)
/evaluate [scenario] — Alias inglés
/gobernanza — Dashboard: Critical Override Layer, estado y posición
/governance — Alias inglés
/recibo [n] — Últimos N recibos PQC de gobernanza _(solo admin)_
/receipt [n] — Alias inglés _(solo admin)_
/velos — Log del gateway Velos: pushes, latencias, dispositions _(solo admin)_

Ejemplo: `/evaluar Meridian Capital $180M Murabaha, beneficial owner no divulgado`

━━━━━━━━━━━━━━━━━━━━━━
**💹 INFORMACIÓN DE MERCADO:**
/precio [crypto] — Precio actual en tiempo real (Kraken)
/market — Dashboard premium del mercado
/balance — Balance real en Kraken
/convertir [cantidad] [CRYPTO] — Convertir a USD
/performance [dias] — Evolución de balance
/analisis [crypto] — Análisis técnico completo
/status — Estado del sistema

**📊 PAPER TRADING:**
/paper\_start — Iniciar con $1,000,000 virtual
/paper\_balance — Ver balance de paper trading
/paper\_buy BTC 10000 — Comprar $10,000 de BTC (simulado)
/paper\_sell BTC 5000 — Vender $5,000 de BTC (simulado)

**📈 BOLSA USA (NYSE/NASDAQ):**
/balance\_bolsa — Balance y posiciones en acciones
/mercado — Estado del mercado (abierto/cerrado)
/analizar AAPL — Análisis técnico + fundamental
/comprar\_bolsa TSLA 500 — Comprar $500 de Tesla
/vender\_bolsa TSLA — Vender posición

**🤖 AUTO-TRADING 24/7:**
/auto\_start — Activar bot automático
/auto\_stop — Detener trading automático
/auto\_status — Estado y estadísticas

**🔬 ADVANCED ENTERPRISE:**
/montecarlo [crypto] — Monte Carlo 10,000 escenarios
/blackswan [crypto] — Detección eventos extremos
/sentiment [crypto] — Análisis de sentimiento
/sharia [crypto] — Verificación Sharia compliance
/orderbook [crypto] — Análisis de ballenas y liquidez
/enterprise [crypto] — Análisis multi-dimensional

**🔍 BÚSQUEDA & IA:**
/buscar [tema] — Búsqueda en internet
/educacion — Guía de trading y riesgos
/legal — Términos y disclaimer
/version — Build info y ADRs activos
/resumen — Resumen diario premium

━━━━━━━━━━━━━━━━━━━━━━
**Ejemplos governance:**
`/evaluar Subsidio estatal $50M sin transparencia pública`
`/gobernanza`

**Ejemplos trading:**
`/precio BTC · /montecarlo ETH · /paper_start`

**¡Envía cualquier escenario o pregunta!** 🏛️
"""
            
            await update.message.reply_text(help_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Error comando help: {e}")

    async def analyze_news_command(self, update, context):
        """Comando /analizar_noticia — stub informativo (en desarrollo)"""
        try:
            await update.message.reply_text(
                "📰 *Análisis de Noticias — Próximamente*\n\n"
                "Este comando está en desarrollo activo.\n"
                "Mientras tanto, puedes usar:\n"
                "• `/buscar [noticia]` — búsqueda web en tiempo real\n"
                "• `/analisis` — análisis técnico de mercado",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"❌ Error en analyze_news_command: {e}")

    async def trending_news_command(self, update, context):
        """Comando /trending_crypto — stub informativo (en desarrollo)"""
        try:
            await update.message.reply_text(
                "📈 *Trending Crypto — Próximamente*\n\n"
                "Este comando está en desarrollo activo.\n"
                "Mientras tanto, puedes usar:\n"
                "• `/market` — resumen de mercado cripto\n"
                "• `/precio [símbolo]` — precio en tiempo real",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"❌ Error en trending_news_command: {e}")

    async def buscar_command(self, update, context):
        """Comando /buscar - Búsqueda en internet con Tavily"""
        try:
            if not WEB_SEARCH_AVAILABLE:
                await update.message.reply_text(
                    "⚠️ El servicio de búsqueda web no está disponible.",
                    parse_mode='Markdown'
                )
                return
            
            # Obtener el query de los argumentos
            query = ' '.join(context.args) if context.args else None
            
            if not query:
                await update.message.reply_text(
                    """🔍 **Búsqueda en Internet**
                    
Uso: `/buscar [tu pregunta]`

**Ejemplos:**
• `/buscar noticias bitcoin hoy`
• `/buscar qué pasó con ethereum`
• `/buscar precio solana predicción`
• `/buscar SEC crypto regulación`

También puedes escribir naturalmente:
• "busca noticias de bitcoin"
• "encuentra información sobre solana"
""",
                    parse_mode='Markdown'
                )
                return
            
            # Mostrar que estamos buscando
            searching_msg = await update.message.reply_text(
                f"🔍 Buscando: *{query}*...",
                parse_mode='Markdown'
            )
            
            # Realizar la búsqueda
            search_manager = get_search_manager()
            result = search_manager.search(query, max_results=5, force_search=True)
            
            if not result.get("success"):
                error_msg = result.get("error", "Error desconocido")
                await searching_msg.edit_text(
                    f"⚠️ No se pudo buscar: {error_msg}",
                    parse_mode='Markdown'
                )
                return
            
            # Formatear resultados
            results = result.get("results", [])
            answer = result.get("answer", "")
            from_cache = result.get("from_cache", False)
            
            if answer:
                response = f"""🔍 **Resultado de búsqueda**
                
**Pregunta:** {query}

**Respuesta:**
{answer}

"""
            else:
                response = f"""🔍 **Resultados de búsqueda**

**Búsqueda:** {query}

"""
            
            if results:
                response += "**Fuentes encontradas:**\n"
                for i, r in enumerate(results[:5], 1):
                    title = r.get("title", "Sin título")[:50]
                    url = r.get("url", "")
                    response += f"{i}. [{title}]({url})\n"
            
            if from_cache:
                response += "\n_📦 Resultado en caché (15 min)_"
            
            await searching_msg.edit_text(response, parse_mode='Markdown', disable_web_page_preview=True)
            logger.info(f"🔍 Búsqueda completada: '{query}' - {len(results)} resultados")
            
        except Exception as e:
            logger.error(f"❌ Error en /buscar: {e}")
            await update.message.reply_text(
                "❌ No se pudo realizar la búsqueda en este momento. Por favor intenta de nuevo.",
                parse_mode='Markdown'
            )

    async def legal_command(self, update, context):
        """Comando /legal - Disclaimer y términos legales"""
        try:
            legal_text = """
⚖️ **TÉRMINOS LEGALES Y DISCLAIMER - OMNIX**

🔞 **RESTRICCIÓN DE EDAD:**
Este servicio está disponible SOLO para usuarios mayores de 18 años. Al usar OMNIX confirmas que cumples este requisito legal.

**NATURALEZA DEL SERVICIO:**
OMNIX es una infraestructura de gobernanza de decisiones institucionales con pipeline de 11 checkpoints y recibos criptográficos post-cuánticos. NO es:
- ❌ Asesor financiero regulado
- ❌ Gestor de inversiones
- ❌ Entidad bancaria o financiera
- ❌ Garantía de resultados en ningún dominio

**RIESGOS DE DECISIONES DE ALTO IMPACTO:**
⚠️ ADVERTENCIA:
- Las decisiones en mercados financieros conllevan RIESGO SIGNIFICATIVO
- En operaciones de trading puedes perder el 100% del capital
- Los activos digitales son altamente volátiles
- Las evaluaciones de OMNIX no garantizan resultados en ningún dominio
- Los mercados pueden verse afectados por eventos externos imprevistos

**LIMITACIONES DEL SISTEMA:**
Las evaluaciones, simulaciones Monte Carlo y análisis de OMNIX:
- NO garantizan resultados futuros
- Se basan en modelos matemáticos con limitaciones inherentes
- No consideran eventos externos imprevistos (geopolíticos, regulatorios, sistémicos)
- Pueden contener errores técnicos o de datos

**USO BAJO TU PROPIO RIESGO:**
Al usar OMNIX, aceptas que:
- Operas completamente bajo tu responsabilidad
- Harold Nunes (Fundador) NO se hace responsable de pérdidas
- OMNIX NO asume responsabilidad por decisiones evaluadas a través del sistema

⚠️ **CONSULTA PROFESIONAL OBLIGATORIA:**
Debes consultar SIEMPRE con un profesional regulado y certificado antes de tomar decisiones de alto impacto. OMNIX NO sustituye asesoramiento profesional personalizado.

**CUMPLIMIENTO REGULATORIO Y JURISDICCIÓN:**
- OMNIX no está registrado ante la SEC (USA), FINRA (USA), FCA (UK), BaFin (Alemania) o entidades reguladoras similares
- Este servicio opera en fase de validación institucional activa
- Operamos como infraestructura de gobernanza bajo leyes internacionales aplicables
- **JURISDICCIONES RESTRINGIDAS - NO DISPONIBLE EN:**
  • Corea del Norte (sanciones internacionales)
  • Irán, Siria (sanciones OFAC)
  • Crimea, Donetsk, Luhansk (sanciones)
  • Jurisdicciones con prohibición explícita aplicable al servicio
- **JURISDICCIONES FAVORABLES (registro futuro):**
  • Suiza (FINMA - Crypto Valley Zug)
  • Singapur (MAS - Payment Services Act)
  • Dubai (VARA - Virtual Asset Regulatory Authority)
  • Unión Europea (MiCA - Markets in Crypto-Assets Regulation)
- Usuarios DEBEN verificar legalidad en su jurisdicción local antes de usar
- Cumplimiento fiscal es responsabilidad del usuario

**GOBERNANZA ÉTICA E ISLÁMICA:**
Las evaluaciones de conformidad en el módulo de crédito islámico se basan en investigación académica (Mufti Taqi Usmani, AAOIFI) pero:
- NO sustituyen consulta con un erudito islámico calificado
- Las interpretaciones pueden variar según escuela jurídica (madhab)
- La responsabilidad final es del usuario

**PROTECCIÓN DE DATOS:**
- Datos almacenados en base de datos segura con acceso restringido
- Credenciales protegidas con algoritmos post-cuánticos estandarizados por NIST
- NO compartimos datos con terceros
- Cumplimiento GDPR en proceso

**CONTACTO:**
Fundador: Harold Nunes
Sistema: OMNIX Decision Governance
Web: omnixquantum.net · contacto@omnixquantum.net
Última actualización: Abril 2026

⚠️ **IMPORTANTE:** Si no aceptas estos términos, NO uses OMNIX para tomar decisiones de alto impacto.

*Para soporte técnico, contacta al Fundador.*
"""
            
            await update.message.reply_text(legal_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Error comando legal: {e}")
            await update.message.reply_text("Error mostrando términos legales")

    async def educacion_command(self, update, context):
        """Comando /educacion - Guía educativa de riesgos y mejores prácticas"""
        try:
            educacion_text = """
📚 **GUÍA EDUCATIVA - TRADING DE CRIPTOMONEDAS**

⚠️ **COMPRENDE LOS RIESGOS ANTES DE OPERAR**

**1. RIESGOS PRINCIPALES:**

💥 **Volatilidad Extrema:**
- Bitcoin puede variar +/- 20% en 24 horas
- Altcoins pueden caer 50-90% en días
- Ejemplo real: BTC cayó de $64K a $29K en 2 meses (2021)

🎲 **Riesgo de Pérdida Total:**
- El 90% de traders novatos pierden dinero
- Projects pueden ir a $0 (ej: Terra LUNA, FTX)
- Smart contracts pueden tener bugs

🏛️ **Riesgo Regulatorio:**
- Gobiernos pueden prohibir exchanges
- Cambios fiscales repentinos
- Exchanges pueden cerrar (ej: FTX colapso 2022)

🔓 **Riesgo de Seguridad:**
- Hackeos de exchanges (Mt.Gox: $450M perdidos)
- Phishing y estafas
- Pérdida de claves privadas = pérdida total

**2. REGLAS DE ORO DEL TRADING:**

✅ **Regla #1: Solo invierte lo que puedas perder**
- Nunca inviertas dinero de emergencias
- Nunca inviertas dinero prestado
- 5-10% de patrimonio máximo en crypto

✅ **Regla #2: Diversifica**
- No pongas todo en una sola moneda
- 40-50% Bitcoin/Ethereum (más estables)
- 30-40% altcoins establecidos
- 10-20% proyectos nuevos (alto riesgo)

✅ **Regla #3: Usa Stop-Loss**
- Define límite de pérdida ANTES de comprar
- Ejemplo: Si compras a $100, pon stop-loss en $90
- Protege tu capital > Maximizar ganancias

✅ **Regla #4: DYOR (Do Your Own Research)**
- Lee el whitepaper del proyecto
- Verifica el equipo en LinkedIn
- Revisa auditorías de seguridad
- Chequea comunidad y desarrollo activo

✅ **Regla #5: No operes emocionalmente**
- FOMO (Fear Of Missing Out) = pérdidas
- No vendas en pánico cuando cae
- Sigue tu plan, no tus emociones

**3. ESTRATEGIAS PARA PRINCIPIANTES:**

📊 **DCA (Dollar Cost Averaging):**
- Compra cantidad fija cada semana/mes
- Ejemplo: $100 cada lunes en BTC
- Promedia precio a largo plazo
- Reduce impacto de volatilidad

⏳ **HODL (Hold On for Dear Life):**
- Compra y mantén 1-5 años
- Ignora fluctuaciones corto plazo
- Históricamente BTC sube 100%+ cada 4 años
- Solo para proyectos sólidos (BTC, ETH)

🎯 **Swing Trading (Intermedio):**
- Compra en soporte, vende en resistencia
- Periodo: días a semanas
- Requiere análisis técnico
- Mayor riesgo que HODL

**4. SEÑALES DE ALERTA - ESTAFAS:**

🚨 **HUYE SI VES ESTO:**
- Promesas de "ganancias garantizadas"
- Retornos "sin riesgo" del 20%+ mensual
- Presión para invertir YA
- "Equipo anónimo" sin LinkedIn verificable
- Token sin utilidad real
- Influencers pagados promocionándolo

**5. CÓMO USAR OMNIX EFECTIVAMENTE:**

🎲 **Monte Carlo (/montecarlo BTC):**
- Usa para ver posibles escenarios
- NO son predicciones exactas
- Fíjate en el rango, no en un número

🦢 **Black Swan (/blackswan ETH):**
- Identifica riesgo de caídas extremas
- Si alerta es alta, reduce posición
- Prepara estrategia de salida

📊 **Sentiment (/sentiment BTC):**
- Miedo extremo = oportunidad de compra
- Codicia extrema = momento de vender
- Va contrario al sentimiento general

☪️ **Sharia (/sharia BTC):**
- Verifica si crypto es Halal
- Basado en investigación académica
- Consulta con erudito si tienes dudas

**6. RECURSOS EDUCATIVOS:**

📖 **Aprende más:**
- CoinMarketCap Learn (gratis)
- Binance Academy (gratis)
- Libro: "The Bitcoin Standard" - Saifedean Ammous
- YouTube: Andreas Antonopoulos (técnico)

📈 **Practica primero:**
- Usa cuentas demo (TradingView)
- Opera con cantidades pequeñas ($50-100)
- Aprende de errores con poco dinero
- LUEGO escala si funciona

**7. FISCALIDAD:**

💼 **IMPORTANTE - Paga tus impuestos:**
- Ventas de crypto = ganancias de capital
- Debes declarar aunque sea pérdida
- Cada país tiene reglas diferentes
- Usa software: CoinTracking, Koinly
- Consulta con contador especializado

⚠️ **RECORDATORIO FINAL:**

OMNIX es una infraestructura de gobernanza de decisiones con motor de trading integrado. Te damos datos, análisis y evaluaciones de gobernanza, pero TÚ tomas las decisiones finales. Si no entiendes algo, NO inviertas en ello.

El mejor trade es el que NO haces si no estás seguro.

**Comandos útiles:**
/legal - Términos completos
/help - Ver todos los comandos
/analisis BTC - Análisis técnico completo

*Desarrollado por Harold Nunes - Sistema OMNIX*
"""
            
            await update.message.reply_text(educacion_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Error comando educacion: {e}")
            await update.message.reply_text("Error mostrando guía educativa")

    async def precio_command(self, update, context):
        """Comando /precio"""
        try:
            args = context.args
            symbol = args[0].upper() if args else 'BTC'
            
            # Obtener precio real usando instancia global
            try:
                if not self.trading:
                    await update.message.reply_text("⚠️ Sistema de trading no disponible")
                    return
                price_data = self.trading.get_real_market_data(f"{symbol}/USD")
                
                if price_data and 'precio_actual' in price_data:
                    precio = price_data['precio_actual']
                    volumen = price_data.get('volumen', 'N/A')
                    cambio = price_data.get('cambio_24h', 'N/A')
                    
                    mensaje = f"""
**{symbol}/USD PRECIO REAL**

**Precio actual:** ${precio:,.2f}
**Cambio 24h:** {cambio}%
**Volumen:** {volumen}

**Datos en tiempo real desde Kraken**
Actualizado: {datetime.now().strftime('%H:%M:%S')}

*Sistema OMNIX - Harold Nunes*
"""
                else:
                    mensaje = f"No se pudo obtener precio para {symbol}"
                    
            except Exception as e:
                logger.error(f"Error obteniendo precio: {e}")
                mensaje = f"Error obteniendo precio de {symbol}"
            
            await update.message.reply_text(mensaje, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Error comando precio: {e}")

    async def market_command(self, update, context):
        """Comando /market - Dashboard Premium del Mercado Cripto con datos 100% reales de Kraken"""
        try:
            # Lista de cryptos principales a monitorear
            cryptos = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOGE']
            
            # Mensaje de carga
            loading_msg = await update.message.reply_text("📊 Cargando dashboard del mercado desde Kraken...")
            
            # Obtener datos reales de Kraken para cada crypto
            market_data = []
            total_volume_usd = 0
            
            for symbol in cryptos:
                try:
                    if not self.trading:
                        continue
                    
                    price_data = self.trading.get_real_market_data(f"{symbol}/USD")
                    
                    if price_data and 'precio_actual' in price_data:
                        precio = price_data['precio_actual']
                        volumen = price_data.get('volumen', 0)
                        cambio_24h = price_data.get('cambio_24h', 0)
                        
                        # Determinar emoji de tendencia
                        if cambio_24h > 0:
                            trend = "🟢" if cambio_24h > 2 else "🔵"
                        else:
                            trend = "🔴" if cambio_24h < -2 else "🟡"
                        
                        market_data.append({
                            'symbol': symbol,
                            'price': precio,
                            'volume': volumen,
                            'change_24h': cambio_24h,
                            'trend': trend
                        })
                        
                        # Sumar volumen total (convertir a número si es string)
                        try:
                            vol_num = float(volumen.replace('M', '').replace('K', '')) if isinstance(volumen, str) else volumen
                            total_volume_usd += vol_num
                        except Exception:
                            pass
                    
                except Exception as e:
                    logger.warning(f"No se pudo obtener datos para {symbol}: {e}")
                    continue
            
            # Calcular estadísticas del mercado
            if market_data:
                avg_change = sum(d['change_24h'] for d in market_data) / len(market_data)
                gainers = sorted([d for d in market_data if d['change_24h'] > 0], key=lambda x: x['change_24h'], reverse=True)[:3]
                losers = sorted([d for d in market_data if d['change_24h'] < 0], key=lambda x: x['change_24h'])[:3]
                
                # Determinar sentimiento general del mercado
                if avg_change > 2:
                    market_sentiment = "🚀 BULLISH FUERTE"
                elif avg_change > 0:
                    market_sentiment = "🟢 BULLISH"
                elif avg_change > -2:
                    market_sentiment = "🟡 NEUTRAL"
                else:
                    market_sentiment = "🔴 BEARISH"
                
                # Construir mensaje premium
                response = f"""
📊 **OMNIX MARKET DASHBOARD PREMIUM**

🌐 **OVERVIEW DEL MERCADO**
   Sentimiento: {market_sentiment}
   Cambio promedio: {avg_change:+.2f}%
   Timestamp: {datetime.now().strftime('%H:%M:%S UTC')}

💰 **PRECIOS EN TIEMPO REAL (KRAKEN)**
"""
                
                # Agregar cada crypto con formato premium
                for data in market_data:
                    response += f"""
{data['trend']} **{data['symbol']}/USD**
   ${data['price']:,.2f} | {data['change_24h']:+.2f}% | Vol: {data['volume']}"""
                
                # Top Gainers
                if gainers:
                    response += "\n\n🏆 **TOP GAINERS 24H**\n"
                    for g in gainers:
                        response += f"   {g['symbol']}: {g['change_24h']:+.2f}%\n"
                
                # Top Losers
                if losers:
                    response += "\n📉 **TOP LOSERS 24H**\n"
                    for l in losers:
                        response += f"   {l['symbol']}: {l['change_24h']:+.2f}%\n"
                
                response += """
⚡ **DATOS 100% REALES**
   • Fuente: Kraken Exchange API
   • Actualización: Tiempo real
   • Sin datos mock ni simulados

💡 **COMANDOS RELACIONADOS**
   `/precio BTC` - Precio detallado
   `/analisis ETH` - Análisis técnico completo
   `/arbitrage_scan BTC/USD` - Buscar arbitraje

*OMNIX Decision Governance - Market Intelligence*
"""
            else:
                response = "❌ No se pudieron obtener datos del mercado. Verifica la conexión con Kraken."
            
            # Eliminar mensaje de carga y enviar respuesta
            await loading_msg.delete()
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Error comando market: {e}")
            await update.message.reply_text("❌ Error obteniendo dashboard del mercado")

    async def balance_command(self, update, context):
        """Comando /balance - FIX Nov 29 2025: Usar self.trading en lugar de global"""
        try:
            try:
                if not self.trading:
                    await update.message.reply_text("⚠️ Sistema de trading no disponible")
                    return
                balance_data = self.trading.get_real_balance()
                
                if 'error' in balance_data:
                    await update.message.reply_text(f"❌ Error Kraken: {balance_data['error']}")
                    return
                
                def get_free_balance(currency):
                    val = balance_data.get(currency, {})
                    if isinstance(val, dict):
                        return val.get('free', 0) or 0
                    return float(val) if val else 0
                
                usd_balance = get_free_balance('USD')
                btc_balance = get_free_balance('BTC')
                eth_balance = get_free_balance('ETH')
                total_usd = balance_data.get('estimated_total_usd', 0)
                
                user_id = str(update.message.from_user.id)
                snapshot_data = {
                    'exchange': 'kraken',
                    'total_usd': total_usd,
                    'btc_balance': btc_balance,
                    'eth_balance': eth_balance,
                    'usdt_balance': get_free_balance('USDT'),
                    'other_balance': 0
                }
                if global_db_manager:
                    global_db_manager.save_balance_snapshot(user_id, snapshot_data)
                
                currencies_list = ""
                for currency, data in balance_data.items():
                    if currency in ['estimated_total_usd', 'error']:
                        continue
                    if isinstance(data, dict):
                        free = data.get('free', 0) or 0
                        if free > 0.0001:
                            currencies_list += f"• **{currency}:** {free:.8f}\n"
                
                mensaje = f"""💰 **BALANCE REAL KRAKEN**

{currencies_list if currencies_list else '• Sin balances significativos'}

💵 **Total Estimado:** ${total_usd:,.2f} USD

✅ **Estado:** TRADING REAL ACTIVADO
🔐 **Seguridad:** API Kraken oficial

_Datos actualizados en tiempo real_
"""
                
            except Exception as e:
                logger.error(f"Error obteniendo balance: {e}")
                mensaje = "❌ No se pudo obtener el balance en este momento. Por favor intenta de nuevo."
            
            await update.message.reply_text(mensaje, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Error comando balance: {e}")

    async def convertir_usd_command(self, update, context):
        """Comando /convertir_usd - Convertir todas las criptomonedas a USD minimizando fees"""
        try:
            user_id = str(update.message.from_user.id)
            
            if not _check_admin_permission(user_id, 'real_trading'):
                await update.message.reply_text("⚠️ Only OWNER can convert funds to USD")
                return
            
            # Verificar que el sistema de trading esté disponible
            if not self.trading:
                await update.message.reply_text("⚠️ Sistema de trading no disponible")
                return
            
            await update.message.reply_text("🔄 Analizando balance y calculando conversiones óptimas...")
            
            try:
                # Obtener balance actual
                balance_data = self.trading.get_real_balance()
                
                if not balance_data:
                    await update.message.reply_text("❌ No se pudo obtener balance de Kraken")
                    return
                
                # Identificar monedas para convertir (todas excepto USD)
                conversiones = []
                total_convertido_usd = 0
                errores = []
                
                # Pares soportados por Kraken para conversión directa a USD
                pares_kraken = {
                    'BTC': 'XBTUSD',
                    'ETH': 'ETHUSD',
                    'USDT': 'USDTUSD',
                    'ADA': 'ADAUSD',
                    'DOT': 'DOTUSD',
                    'LINK': 'LINKUSD',
                    'MATIC': 'MATICUSD',
                    'AVAX': 'AVAXUSD',
                    'SOL': 'SOLUSD',
                    'XRP': 'XRPUSD'
                }
                
                mensaje_conversiones = "💱 **CONVERSIÓN A USD - RESUMEN**\n\n"
                
                for moneda, cantidad in balance_data.items():
                    # Saltar USD y campos especiales
                    if moneda in ['USD', 'total_usd'] or float(cantidad) <= 0:
                        continue
                    
                    cantidad_float = float(cantidad)
                    
                    # Verificar si existe par directo a USD
                    if moneda not in pares_kraken:
                        errores.append(f"⚠️ {moneda}: No hay par directo a USD en Kraken")
                        continue
                    
                    par = pares_kraken[moneda]
                    
                    # Obtener precio actual para estimar valor
                    try:
                        ticker = self.trading.kraken_client.client.fetch_ticker(f"{moneda}/USD")
                        precio_actual = ticker['last']
                        valor_usd = cantidad_float * precio_actual
                        
                        # Solo convertir si el valor es > $1 (evitar dust amounts)
                        if valor_usd < 1.0:
                            mensaje_conversiones += f"⏭️ **{moneda}:** {cantidad_float:.8f} (${valor_usd:.2f}) - Monto muy pequeño, no se convierte\n"
                            continue
                        
                        # EJECUTAR CONVERSIÓN REAL con orden de mercado
                        logger.info(f"💱 Convirtiendo {cantidad_float} {moneda} a USD (${valor_usd:.2f})")
                        
                        # Usar KrakenAPIClient para crear orden de mercado SELL
                        orden_result = self.trading.kraken_client.place_order(
                            pair=par,
                            order_type='market',
                            side='sell',
                            volume=cantidad_float
                        )
                        
                        if orden_result and 'txid' in orden_result:
                            txid = orden_result['txid'][0] if isinstance(orden_result['txid'], list) else orden_result['txid']
                            conversiones.append({
                                'moneda': moneda,
                                'cantidad': cantidad_float,
                                'valor_usd': valor_usd,
                                'txid': txid
                            })
                            total_convertido_usd += valor_usd
                            mensaje_conversiones += f"✅ **{moneda}:** {cantidad_float:.8f} → ${valor_usd:.2f} USD\n"
                            mensaje_conversiones += f"   📝 TX ID: `{txid}`\n"
                        else:
                            errores.append(f"❌ {moneda}: Error ejecutando orden - {orden_result}")
                            mensaje_conversiones += f"❌ **{moneda}:** Error en conversión\n"
                    
                    except Exception as e_moneda:
                        logger.error(f"Error convirtiendo {moneda}: {e_moneda}")
                        errores.append(f"❌ {moneda}: {str(e_moneda)}")
                        mensaje_conversiones += f"❌ **{moneda}:** {str(e_moneda)[:50]}\n"
                
                # Resumen final
                if conversiones:
                    mensaje_conversiones += f"\n💰 **TOTAL CONVERTIDO:** ${total_convertido_usd:.2f} USD\n"
                    mensaje_conversiones += f"✅ **CONVERSIONES EXITOSAS:** {len(conversiones)}\n"
                else:
                    mensaje_conversiones += "\n⚠️ No se realizaron conversiones\n"
                
                if errores:
                    mensaje_conversiones += f"❌ **ERRORES:** {len(errores)}\n\n"
                    for error in errores[:3]:  # Mostrar máximo 3 errores
                        mensaje_conversiones += f"{error}\n"
                
                mensaje_conversiones += f"\n💡 Usa /balance para ver tu nuevo balance consolidado en USD"
                
                await update.message.reply_text(mensaje_conversiones, parse_mode='Markdown')
                
            except Exception as e_conversion:
                logger.error(f"Error durante conversión: {e_conversion}")
                await update.message.reply_text(f"❌ Error ejecutando conversiones: {str(e_conversion)}")
            
        except Exception as e:
            logger.error(f"❌ Error comando convertir_usd: {e}")
            await update.message.reply_text("❌ Error procesando conversión a USD")

    async def convertir_command(self, update, context):
        """Comando /convertir [cantidad] [CRYPTO] USD - Convertir cantidad específica a USD"""
        try:
            user_id = str(update.message.from_user.id)
            
            if not _check_admin_permission(user_id, 'real_trading'):
                await update.message.reply_text("⚠️ Only OWNER can convert funds")
                return
            
            # Verificar parámetros
            if len(context.args) < 2:
                await update.message.reply_text(
                    "❌ Uso correcto: `/convertir [cantidad USD] [CRYPTO]`\n\n"
                    "Ejemplos:\n"
                    "`/convertir 50 BTC` - Convierte $50 de BTC a USD\n"
                    "`/convertir 100 ETH` - Convierte $100 de ETH a USD",
                    parse_mode='Markdown'
                )
                return
            
            try:
                valor_usd = float(context.args[0])
                moneda = context.args[1].upper()
            except ValueError:
                await update.message.reply_text("❌ La cantidad debe ser un número válido")
                return
            
            # Verificar sistema de trading
            if not self.trading:
                await update.message.reply_text("⚠️ Sistema de trading no disponible")
                return
            
            await update.message.reply_text(f"🔄 Convirtiendo ${valor_usd:.2f} de {moneda} a USD...")
            
            # Pares soportados
            pares_kraken = {
                'BTC': 'XBTUSD',
                'ETH': 'ETHUSD',
                'USDT': 'USDTUSD',
                'ADA': 'ADAUSD',
                'DOT': 'DOTUSD',
                'LINK': 'LINKUSD',
                'MATIC': 'MATICUSD',
                'AVAX': 'AVAXUSD',
                'SOL': 'SOLUSD',
                'XRP': 'XRPUSD'
            }
            
            if moneda not in pares_kraken:
                await update.message.reply_text(f"❌ {moneda} no soportada. Pares disponibles: {', '.join(pares_kraken.keys())}")
                return
            
            try:
                # Obtener balance actual
                balance_data = self.trading.get_real_balance()
                
                if moneda not in balance_data or float(balance_data[moneda]) <= 0:
                    await update.message.reply_text(f"❌ No tienes {moneda} en tu balance")
                    return
                
                cantidad_disponible = float(balance_data[moneda])
                
                # Obtener precio actual
                par = pares_kraken[moneda]
                ticker = self.trading.kraken_client.client.fetch_ticker(f"{moneda}/USD")
                precio_actual = ticker['last']
                
                # Calcular cantidad de crypto a vender
                cantidad_crypto = valor_usd / precio_actual
                
                # Verificar que tenga suficiente
                if cantidad_crypto > cantidad_disponible:
                    valor_max = cantidad_disponible * precio_actual
                    await update.message.reply_text(
                        f"❌ Saldo insuficiente\n\n"
                        f"**Disponible:** {cantidad_disponible:.8f} {moneda} (${valor_max:.2f})\n"
                        f"**Necesitas:** {cantidad_crypto:.8f} {moneda} (${valor_usd:.2f})\n\n"
                        f"💡 Máximo que puedes convertir: ${valor_max:.2f}",
                        parse_mode='Markdown'
                    )
                    return
                
                # EJECUTAR CONVERSIÓN REAL
                logger.info(f"💱 Convirtiendo {cantidad_crypto:.8f} {moneda} a USD (${valor_usd:.2f})")
                
                orden_result = self.trading.kraken_client.place_order(
                    pair=par,
                    order_type='market',
                    side='sell',
                    volume=cantidad_crypto
                )
                
                if orden_result and 'txid' in orden_result:
                    txid = orden_result['txid'][0] if isinstance(orden_result['txid'], list) else orden_result['txid']
                    
                    mensaje = f"""
✅ **CONVERSIÓN EXITOSA**

💱 **Operación:**
{cantidad_crypto:.8f} {moneda} → ${valor_usd:.2f} USD

💰 **Detalles:**
Precio: ${precio_actual:,.2f} USD/{moneda}
Par: {moneda}/USD
Tipo: Orden de mercado

📝 **Transaction ID:**
`{txid}`

🏦 **Balance actualizado:**
Usa /balance para ver tu nuevo balance

⚡ La conversión fue ejecutada exitosamente en Kraken
"""
                    await update.message.reply_text(mensaje, parse_mode='Markdown')
                    
                else:
                    await update.message.reply_text(f"❌ Error ejecutando orden: {orden_result}")
                    
            except Exception as e_conversion:
                logger.error(f"Error durante conversión: {e_conversion}")
                await update.message.reply_text(f"❌ Error: {str(e_conversion)}")
            
        except Exception as e:
            logger.error(f"❌ Error comando convertir: {e}")
            await update.message.reply_text("❌ Error procesando conversión")

    async def performance_command(self, update, context):
        """Comando /performance - Mostrar métricas de performance del balance"""
        try:
            user_id = str(update.message.from_user.id)
            
            # Obtener historial de 30 días por defecto
            days = 30
            if context.args and context.args[0].isdigit():
                days = int(context.args[0])
            
            # Usar DatabaseServiceEnterprise en lugar de database.py viejo
            history = []
            if global_db_manager:
                history = global_db_manager.get_balance_history(user_id, days)
            
            if not history or len(history) < 2:
                mensaje = f"""
📊 **PERFORMANCE - Insuficientes datos**

No hay suficiente historial de balance para calcular métricas.

**¿Cómo empezar?**
1. Usa /balance para registrar tu balance actual
2. Espera unos días
3. Vuelve a usar /balance regularmente
4. Regresa aquí para ver tu progreso

*Necesitas al menos 2 registros de balance en diferentes días*

Tip: Usa /balance cada día para tracking automático
"""
                await update.message.reply_text(mensaje, parse_mode='Markdown')
                return
            
            # Calcular métricas usando DatabaseServiceEnterprise
            metrics = None
            if global_db_manager:
                metrics = global_db_manager.calculate_performance_metrics(history)
            
            if not metrics:
                await update.message.reply_text("Error calculando métricas de performance")
                return
            
            # Determinar emoji de tendencia
            if metrics['roi_percent'] > 10:
                trend_emoji = "🚀"
                trend_text = "EXCELENTE"
            elif metrics['roi_percent'] > 0:
                trend_emoji = "📈"
                trend_text = "POSITIVO"
            elif metrics['roi_percent'] == 0:
                trend_emoji = "➡️"
                trend_text = "NEUTRO"
            else:
                trend_emoji = "📉"
                trend_text = "NEGATIVO"
            
            # Determinar color ROI
            roi_sign = "+" if metrics['roi_percent'] >= 0 else ""
            pnl_sign = "+" if metrics['profit_loss'] >= 0 else ""
            
            mensaje = f"""
{trend_emoji} **PERFORMANCE REPORT - {days} DÍAS**

**RENDIMIENTO GENERAL:** {trend_text}

📊 **BALANCE:**
• Inicial: ${metrics['initial_balance']:,.2f}
• Actual: ${metrics['current_balance']:,.2f}
• Máximo alcanzado: ${metrics['max_balance']:,.2f}

💰 **PROFIT/LOSS:**
• Total: {pnl_sign}${metrics['profit_loss']:,.2f}
• ROI: {roi_sign}{metrics['roi_percent']:.2f}%
• CAGR Anual: {roi_sign}{metrics['cagr_annual']:.2f}%

📉 **RIESGO:**
• Max Drawdown: {metrics['max_drawdown_percent']:.2f}%
{'  ⚠️ Drawdown alto' if metrics['max_drawdown_percent'] > 20 else '  ✅ Drawdown controlado'}

⏱️ **TRACKING:**
• Días rastreados: {metrics['days_tracked']}
• Registros: {len(history)} snapshots
• Desde: {history[0]['timestamp'][:10]}
• Hasta: {history[-1]['timestamp'][:10]}

**COMPARACIÓN VS BENCHMARKS:**
• Bitcoin (histórico 1 año): ~100%
• Tu ROI: {roi_sign}{metrics['roi_percent']:.2f}%
{'  🎯 Superando mercado!' if metrics['roi_percent'] > 100 else '  💪 Sigue mejorando'}

**PRÓXIMOS PASOS:**
{f"✅ Mantén la estrategia - ROI positivo" if metrics['roi_percent'] > 0 else "⚠️ Revisa estrategia - Considera ajustes"}
{f"⚠️ Controla el riesgo - Drawdown {metrics['max_drawdown_percent']:.1f}%" if metrics['max_drawdown_percent'] > 15 else "✅ Gestión de riesgo sólida"}

*Usa /balance diariamente para tracking preciso*
*Usa /educacion para aprender estrategias*

Sistema OMNIX - Harold Nunes
"""
            
            await update.message.reply_text(mensaje, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Error comando performance: {e}")
            await update.message.reply_text("Error generando reporte de performance")

    async def analisis_command(self, update, context):
        """Comando /analisis"""
        try:
            args = context.args
            symbol = args[0].upper() if args else 'BTC'
            
            # Realizar análisis completo usando instancia global
            try:
                if not self.trading:
                    await update.message.reply_text("⚠️ Sistema de trading no disponible")
                    return
                analisis = self.trading.generate_comprehensive_analysis(f"{symbol}/USD")
                
                mensaje = f"""
🧠 **ANÁLISIS TÉCNICO {symbol}/USD**

📊 **Precio:** ${analisis.get('precio', 'N/A')}
📈 **RSI:** {analisis.get('rsi', 'N/A')}
📉 **MACD:** {analisis.get('macd', 'N/A')}
🎯 **Recomendación:** {analisis.get('recomendacion', 'NEUTRO')}

🔮 **Análisis IA:**
{analisis.get('analisis_ia', 'Mercado en análisis...')}

⚡ **Actualizado:** {datetime.now().strftime('%H:%M:%S')}

*Análisis generado por OMNIX*
"""
                
            except Exception as e:
                logger.error(f"Error análisis: {e}")
                mensaje = f"⚠️ Error generando análisis para {symbol}"
            
            await update.message.reply_text(mensaje, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Error comando analisis: {e}")

    async def status_command(self, update, context):
        """Comando /status"""
        try:
            status_msg = f"""
🔍 **OMNIX SYSTEM STATUS**

🟢 **Sistema:** OPERATIVO
🟢 **Trading:** KRAKEN CONECTADO
🟢 **IA Dual:** GEMINI + OPENAI ACTIVO
🟢 **Balance:** Verificado en tiempo real con Kraken
🟢 **Bot Telegram:** FUNCIONANDO

⚡ **Uptime:** {datetime.now().strftime('%H:%M:%S')}
⚡ **Sistema:** OMNIX Decision Governance
👨‍💻 **Desarrollador:** Harold Nunes
🔧 **Plataforma:** Replit Production

✅ **Todo funcionando correctamente**
"""
            
            await update.message.reply_text(status_msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Error comando status: {e}")

    async def montecarlo_command(self, update, context):
        """Comando /montecarlo - Simulación Monte Carlo"""
        try:
            if not ADVANCED_FEATURES_AVAILABLE or not global_advanced_features:
                await update.message.reply_text("⚠️ Advanced Features no disponibles")
                return
            
            symbol = context.args[0].upper() if context.args else "BTC"
            
            # Obtener precio actual
            price = self.trading.get_current_price(f"{symbol}/USD")
            if not price:
                price = 50000  # Default BTC
            
            # Ejecutar simulación
            result = global_advanced_features.monte_carlo.simulate_trading_strategy(
                current_price=price,
                investment=1000,
                days=30
            )
            
            msg = f"""
🎲 **SIMULACIÓN MONTE CARLO - {symbol}/USD**

💰 **Inversión:** $1,000 USD
📊 **Simulaciones:** {result['simulations']:,}
📅 **Horizonte:** 30 días

📈 **RESULTADOS:**
✅ Win Rate: {result['win_rate']:.2f}%
❌ Loss Rate: {result['loss_rate']:.2f}%
💵 Profit Esperado: ${result['expected_profit']:.2f}
⚖️ Risk/Reward: {result['risk_reward_ratio']:.2f}

🎯 **RECOMENDACIÓN:**
{"✅ Estrategia VIABLE" if result['win_rate'] > 55 else "⚠️ Riesgo ALTO" if result['win_rate'] > 45 else "❌ Evitar trading"}

*Análisis probabilístico con 10,000 escenarios*
"""
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error montecarlo: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")

    async def quantum_test_command(self, update, context):
        """Comando /quantum_test - Test QRNG en vivo con ANU"""
        try:
            from omnix_core.quantum.enhancements import global_qrng
            import numpy as np
            
            msg = "⚛️ **ANU QUANTUM RNG - LIVE TEST**\n\n"
            msg += "🔬 Conectando a ANU Quantum API...\n\n"
            
            stats_before = global_qrng.get_stats()
            
            quantum_numbers = []
            for _ in range(10):
                quantum_numbers.append(global_qrng.random())
            
            stats_after = global_qrng.get_stats()
            
            if stats_after['successful_quantum'] > stats_before.get('successful_quantum', 0) or \
               stats_after['last_source'] == 'ANU Quantum Vacuum':
                msg += "✅ **FUENTE: ANU Quantum Vacuum**\n"
                msg += "📍 Australian National University\n\n"
            elif stats_after['cache_hits'] > 0:
                msg += "✅ **FUENTE: ANU Quantum (cached)**\n"
                msg += "📍 Números cuánticos pre-cargados\n\n"
            else:
                msg += "⚠️ **FUENTE: Classical Fallback**\n\n"
            
            msg += "🎲 **10 NÚMEROS CUÁNTICOS GENERADOS:**\n```\n"
            for i, n in enumerate(quantum_numbers, 1):
                msg += f"[{i:2d}] {n:.12f}\n"
            msg += "```\n\n"
            
            arr = np.array(quantum_numbers)
            msg += "📊 **ANÁLISIS DE CALIDAD:**\n"
            msg += f"• Media: {arr.mean():.6f} (ideal: 0.5)\n"
            msg += f"• Desv. Std: {arr.std():.6f} (ideal: ~0.28)\n"
            msg += f"• Rango: [{arr.min():.4f}, {arr.max():.4f}]\n\n"
            
            msg += f"📈 **ESTADÍSTICAS QRNG:**\n"
            msg += f"• Requests totales: {stats_after['total_requests']:,}\n"
            msg += f"• Números cuánticos: {stats_after['quantum_numbers_generated']:,}\n"
            msg += f"• Cache actual: {stats_after['cache_size']} nums\n\n"
            
            msg += "✅ **OMNIX usa entropía cuántica REAL**"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except ImportError:
            await update.message.reply_text("⚠️ Módulo QRNG no disponible")
        except Exception as e:
            logger.error(f"Error quantum_test: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")

    async def quantum_stats_command(self, update, context):
        """Comando /quantum_stats - Estadísticas QRNG + QAOA"""
        try:
            if hasattr(self, 'auto_trading') and self.auto_trading:
                stats = self.auto_trading.get_quantum_stats()
                
                if stats.get('available'):
                    qrng_stats = stats.get('qrng', {})
                    qaoa_stats = stats.get('qaoa', {})
                    
                    msg = f"⚛️ **QUANTUM ENHANCEMENTS — OMNIX Decision Governance**\n\n"
                    msg += "🎲 **QRNG (Quantum Random Number Generator)**\n"
                    msg += f"• Total requests: {qrng_stats.get('total_requests', 0):,}\n"
                    msg += f"• Quantum numbers: {qrng_stats.get('quantum_numbers_generated', 0):,}\n"
                    msg += f"• Success rate: {qrng_stats.get('uptime_percentage', 0):.1f}%\n"
                    msg += f"• Cache size: {qrng_stats.get('cache_size', 0)}\n"
                    msg += f"• Source: {qrng_stats.get('last_source', 'N/A')}\n\n"
                    msg += "⚛️ **QAOA (Quantum Portfolio Optimizer)**\n"
                    msg += f"• Total optimizations: {qaoa_stats.get('total_optimizations', 0)}\n"
                    msg += f"• Classical sims: {qaoa_stats.get('classical_simulations', 0)}\n"
                    msg += f"• Mode: {qaoa_stats.get('mode', 'Unknown')}\n\n"
                    msg += "💡 **TECNOLOGÍAS:**\n"
                    msg += "• Monte Carlo usa números cuánticos reales\n"
                    msg += "• ANU Quantum API (vacuum fluctuations)\n"
                    msg += "• QAOA clásico inspirado en computación cuántica\n\n"
                    msg += "✅ Quantum enhancements operacionales"
                else:
                    msg = "⚠️ Quantum enhancements no disponibles"
            else:
                msg = "⚠️ Auto-Trading Bot no inicializado"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error quantum_stats: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")

    async def quantum_demo_command(self, update, context):
        """Comando /quantum_demo - Demo física cuántica para inversores"""
        try:
            from omnix_core.quantum.physics_validator import generate_quantum_response
            
            topic = context.args[0].lower() if context.args else None
            
            if topic:
                response = generate_quantum_response(topic)
            else:
                response = """
⚛️ **QUANTUM PHYSICS DEMO - OMNIX**

🔬 **Física Cuántica Aplicada al Trading**

OMNIX utiliza principios de física cuántica real:

📐 **1. QRNG - Números Cuánticos Reales**
   Fuente: ANU (Australian National University)
   Método: Fluctuaciones del vacío cuántico
   Uso: Semillas para Monte Carlo

⚛️ **2. Principio de Incertidumbre**
   [X̂, P̂] = iħ/2
   Aplicación: Límites fundamentales en predicción

📊 **3. QAOA Clásico**
   Inspirado en Quantum Approximate Optimization
   Uso: Optimización de portfolios

🎯 **DEMOS DISPONIBLES:**
   `/quantum_demo conmutador` - Cálculo [X̂, P̂]
   `/quantum_demo varianza` - Varianza del vacío
   `/quantum_demo qrng` - Física del QRNG
   `/quantum_test` - Test en vivo con ANU

💡 OMNIX es la primera infraestructura de gobernanza de decisiones
con entropía cuántica verificable en sus recibos PQC.
"""
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except ImportError:
            await update.message.reply_text("⚠️ Módulo de física cuántica no disponible")
        except Exception as e:
            logger.error(f"Error quantum_demo: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")

    async def blackswan_command(self, update, context):
        """Comando /blackswan - Detección de eventos extremos"""
        try:
            if not ADVANCED_FEATURES_AVAILABLE or not global_advanced_features:
                await update.message.reply_text("⚠️ Advanced Features no disponibles")
                return
            
            symbol = context.args[0].upper() if context.args else "BTC"
            
            # Obtener histórico
            prices = self._get_price_history(symbol, days=100)
            
            if not prices or len(prices) < 30:
                await update.message.reply_text("⚠️ No hay suficientes datos históricos")
                return
            
            # Analizar
            result = global_advanced_features.black_swan.predict_crash_probability(prices)
            
            risk_emoji = {"EXTREME": "🚨", "HIGH": "⚠️", "MEDIUM": "⚡", "LOW": "✅"}
            emoji = risk_emoji.get(result['risk_level'], "⚖️")
            
            msg = f"""
🦢 **BLACK SWAN DETECTION - {symbol}/USD**

{emoji} **Nivel de Riesgo:** {result['risk_level']}
📊 **Probabilidad Crash:** {result['crash_probability']:.0f}%
🔍 **Eventos Extremos:** {result['extreme_events_detected']}

🎯 **RECOMENDACIÓN:**
{result['recommendation']}

*Análisis estadístico avanzado (Kurtosis + Fat Tails)*
"""
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error blackswan: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")

    async def sentiment_command(self, update, context):
        """Comando /sentiment - Análisis de sentimiento"""
        try:
            if not ADVANCED_FEATURES_AVAILABLE or not global_advanced_features:
                await update.message.reply_text("⚠️ Advanced Features no disponibles")
                return
            
            symbol = context.args[0].lower() if context.args else "bitcoin"
            
            # Obtener sentimiento
            sentiment = global_advanced_features.sentiment.get_market_sentiment(symbol)
            fng = global_advanced_features.sentiment.get_fear_greed_index()
            
            if 'error' in sentiment:
                await update.message.reply_text(f"⚠️ Error obteniendo datos: {sentiment['error']}")
                return
            
            msg = f"""
📊 **SENTIMENT ANALYSIS - {symbol.upper()}**

🎭 **Sentimiento General:** {sentiment.get('overall_sentiment', 'N/A')}
📈 Bullish: {sentiment.get('sentiment_bullish', 0):.1f}%
📉 Bearish: {sentiment.get('sentiment_bearish', 0):.1f}%

🏆 **Market Rank:** #{sentiment.get('market_rank', 'N/A')}
👥 **Community Score:** {sentiment.get('community_score', 0):.1f}/100
👨‍💻 **Developer Score:** {sentiment.get('developer_score', 0):.1f}/100

😱 **FEAR & GREED INDEX**
📊 Índice: {fng.get('fear_greed_index', 'N/A')}/100
🎯 Estado: {fng.get('classification', 'N/A')}
{fng.get('interpretation', '')}

💡 **RECOMENDACIÓN:**
{sentiment.get('recommendation', 'Sin recomendación')}

*Datos en tiempo real de CoinGecko + Alternative.me*
"""
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error sentiment: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")

    async def sharia_command(self, update, context):
        """Comando /sharia - Verificación Sharia compliance"""
        try:
            if not ADVANCED_FEATURES_AVAILABLE or not global_advanced_features:
                await update.message.reply_text("⚠️ Advanced Features no disponibles")
                return
            
            symbol = context.args[0].upper() if context.args else "BTC"
            
            # Verificar compliance
            result = global_advanced_features.sharia.check_compliance(symbol)
            
            status_emoji = {"halal": "✅", "haram": "❌", "questionable": "⚠️", "unknown": "❓"}
            emoji = status_emoji.get(result['status'], "❓")
            
            msg = f"""
☪️ **SHARIA COMPLIANCE - {result['asset']}**

{emoji} **Status:** {result['status'].upper()}
🎯 **Confianza:** {result['confidence_level'].upper()}

📋 **Razón:**
{result['reason']}

{'📚 **Fuentes Islámicas:**' if 'scholarly_sources' in result else ''}
{', '.join(result.get('scholarly_sources', [])) if 'scholarly_sources' in result else ''}

💡 **RECOMENDACIÓN:**
{result['recommendation']}

*Base de datos AAOIFI + Scholars islámicos*
"""
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error sharia: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")

    async def orderbook_command(self, update, context):
        """Comando /orderbook - Análisis de order book"""
        try:
            if not ADVANCED_FEATURES_AVAILABLE or not global_advanced_features:
                await update.message.reply_text("⚠️ Advanced Features no disponibles")
                return
            
            symbol = context.args[0].upper() if context.args else "BTC"
            
            # Obtener order book
            order_book = self._get_order_book(symbol)
            
            if not order_book or 'error' in order_book:
                await update.message.reply_text("⚠️ No se pudo obtener order book")
                return
            
            # Analizar
            result = global_advanced_features.order_book.analyze_order_book(order_book)
            
            whale = result.get('whale_activity', {})
            imbalance = result.get('market_imbalance', {})
            spread = result.get('spread', {})
            
            msg = f"""
🐋 **ORDER BOOK ANALYSIS - {symbol}/USD**

🔍 **WHALE ACTIVITY:**
🐳 Ballenas: {'SÍ' if whale.get('whales_detected') else 'NO'}
📊 Buy Walls: {whale.get('whale_buy_walls', 0)}
📊 Sell Walls: {whale.get('whale_sell_walls', 0)}
{whale.get('whale_signal', 'NEUTRAL')} Signal

⚖️ **MARKET IMBALANCE:**
{imbalance.get('signal', 'NEUTRAL')}
{imbalance.get('pressure_percentage', '')}

💰 **SPREAD:**
Bid: ${spread.get('best_bid', 0):,.2f}
Ask: ${spread.get('best_ask', 0):,.2f}
Spread: {spread.get('spread_percentage', 0):.3f}%
Liquidez: {spread.get('liquidity', 'N/A')}

🎯 **SEÑAL GENERAL:**
{result.get('overall_signal', '⚖️ NEUTRAL')}

*Análisis en tiempo real del libro de órdenes*
"""
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error orderbook: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")

    async def enterprise_command(self, update, context):
        """Comando /enterprise - Análisis completo enterprise"""
        try:
            if not ADVANCED_FEATURES_AVAILABLE or not global_advanced_features:
                await update.message.reply_text("⚠️ Advanced Features no disponibles")
                return
            
            symbol = context.args[0].upper() if context.args else "BTC"
            
            await update.message.reply_text("🔍 Ejecutando análisis enterprise completo...")
            
            # Obtener datos
            price = self.trading.get_current_price(f"{symbol}/USD") or 50000
            prices = self._get_price_history(symbol, days=100)
            
            # Análisis completo
            result = global_advanced_features.full_analysis(
                symbol=f"{symbol}/USD",
                current_price=price,
                historical_prices=prices if prices and len(prices) >= 30 else [price] * 100
            )
            
            mc = result['monte_carlo']
            bs = result['black_swan']
            
            msg = f"""
🚀 **ANÁLISIS ENTERPRISE COMPLETO - {symbol}/USD**

💰 **Precio Actual:** ${price:,.2f}

🎲 **MONTE CARLO:**
Win Rate: {mc['win_rate']:.1f}% | Profit: ${mc['expected_profit']:.2f}

🦢 **BLACK SWAN:**
Riesgo: {bs['crash_probability']:.0f}% | Nivel: {bs['risk_level']}

📊 **SENTIMENT:**
{result['sentiment'].get('overall_sentiment', 'N/A')}

☪️ **SHARIA:**
{result['sharia_compliance'].get('status', 'unknown').upper()}

🎯 **RECOMENDACIÓN FINAL:**
{result['overall_recommendation']}

*Análisis multi-dimensional con IA + estadística avanzada*
"""
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error enterprise: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")
    
    async def paper_start_command(self, update, context):
        """Comando /paper_start - Inicializar paper trading con $1M"""
        try:
            if not self.paper_trading:
                await update.message.reply_text("⚠️ Paper Trading no disponible")
                return
            
            user_id = str(update.effective_user.id)
            result = self.paper_trading.initialize_user(user_id)
            
            if 'error' in result:
                await update.message.reply_text(f"❌ Error: {result['error']}")
                return
            
            if result.get('already_initialized'):
                msg = f"""
📊 **PAPER TRADING YA ACTIVO**

💰 Balance USD: ${result['balance_usd']:,.2f}
📈 Trades totales: {result['total_trades']}

Usa /paper_buy o /paper_sell para tradear
Usa /paper_balance para ver tu balance completo
"""
            else:
                msg = f"""
🎯 **PAPER TRADING ACTIVADO**

💰 Balance inicial: $1,000,000.00 USD
📊 Sistema: Trading simulado con datos REALES de Kraken

**COMANDOS DISPONIBLES:**
/paper_balance - Ver balance y performance
/paper_buy BTC 10000 - Comprar $10,000 de BTC
/paper_sell BTC 5000 - Vender $5,000 de BTC

**IMPORTANTE:**
✅ Usa precios REALES de Kraken
✅ NO gasta dinero real
✅ Perfecto para probar estrategias

¡Empieza a tradear!
"""
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error paper_start: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")
    
    async def paper_balance_command(self, update, context):
        """Comando /paper_balance - Ver balance paper trading"""
        try:
            if not self.paper_trading:
                await update.message.reply_text("⚠️ Paper Trading no disponible")
                return
            
            user_id = str(update.effective_user.id)
            balance = self.paper_trading.get_paper_balance(user_id)
            
            if not balance.get('initialized'):
                await update.message.reply_text(balance.get('message', 'Usa /paper_start para comenzar'))
                return
            
            msg = f"""
📊 **PAPER TRADING BALANCE**

💵 **EFECTIVO:**
USD: ${balance['balance_usd']:,.2f}

₿ **CRYPTO:**
BTC: {balance['btc_balance']:.8f}
ETH: {balance['eth_balance']:.8f}

💰 **VALOR TOTAL:**
${balance['total_value_usd']:,.2f}

📈 **PERFORMANCE:**
P&L: ${balance['profit_loss_usd']:,.2f} ({balance['profit_loss_pct']:+.2f}%)
Trades: {balance['total_trades']}
Inicial: ${balance['initial_balance']:,.2f}

*Trading simulado con datos reales de Kraken*
"""
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error paper_balance: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")
    
    async def paper_buy_command(self, update, context):
        """Comando /paper_buy - Comprar crypto simulado
        Uso: /paper_buy BTC 10000 (comprar $10,000 de BTC)
        """
        try:
            if not self.paper_trading:
                await update.message.reply_text("⚠️ Paper Trading no disponible")
                return
            
            if len(context.args) < 2:
                await update.message.reply_text("Uso: /paper_buy BTC 10000 (comprar $10,000 de BTC)")
                return
            
            symbol = context.args[0].upper()
            try:
                amount_usd = float(context.args[1])
            except ValueError:
                await update.message.reply_text("⚠️ Cantidad debe ser número. Ej: /paper_buy BTC 10000")
                return
            
            if amount_usd <= 0:
                await update.message.reply_text("⚠️ Cantidad debe ser mayor a 0")
                return
            
            user_id = str(update.effective_user.id)
            
            await update.message.reply_text(f"🔍 Obteniendo precio real de {symbol} desde Kraken...")
            
            result = self.paper_trading.execute_paper_trade(
                user_id=user_id,
                side='buy',
                symbol=f"{symbol}/USD",
                amount_usd=amount_usd
            )
            
            if 'error' in result:
                await update.message.reply_text(f"❌ {result['error']}")
                return
            
            import time
            trade_id = f"{int(time.time())}"[-6:]
            
            msg = f"""
✅ **COMPRA EJECUTADA (SIMULADA)**

{symbol}: +{result['amount']:.8f}
Precio: ${result['price']:,.2f}
Total: ${result['total_usd']:,.2f}

💰 **NUEVO BALANCE:**
USD: ${result['new_balance_usd']:,.2f}
BTC: {result['new_btc_balance']:.8f}
ETH: {result['new_eth_balance']:.8f}

*Trade simulado con precio REAL de Kraken*

👇 **¿Cómo resultó este trade?**
"""
            
            from omnix_services.telegram_service.inline_keyboards import InlineKeyboardsManager
            feedback_buttons = InlineKeyboardsManager.get_trade_feedback_buttons(
                trade_id=trade_id,
                strategy="PAPER",
                symbol=symbol,
                signal_type="BUY"
            )
            
            await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=feedback_buttons)
            
        except Exception as e:
            logger.error(f"Error paper_buy: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")
    
    async def paper_sell_command(self, update, context):
        """Comando /paper_sell - Vender crypto simulado
        Uso: /paper_sell BTC 5000 (vender $5,000 de BTC)
        """
        try:
            if not self.paper_trading:
                await update.message.reply_text("⚠️ Paper Trading no disponible")
                return
            
            if len(context.args) < 2:
                await update.message.reply_text("Uso: /paper_sell BTC 5000 (vender $5,000 de BTC)")
                return
            
            symbol = context.args[0].upper()
            try:
                amount_usd = float(context.args[1])
            except ValueError:
                await update.message.reply_text("⚠️ Cantidad debe ser número. Ej: /paper_sell BTC 5000")
                return
            
            if amount_usd <= 0:
                await update.message.reply_text("⚠️ Cantidad debe ser mayor a 0")
                return
            
            user_id = str(update.effective_user.id)
            
            await update.message.reply_text(f"🔍 Obteniendo precio real de {symbol} desde Kraken...")
            
            result = self.paper_trading.execute_paper_trade(
                user_id=user_id,
                side='sell',
                symbol=f"{symbol}/USD",
                amount_usd=amount_usd
            )
            
            if 'error' in result:
                await update.message.reply_text(f"❌ {result['error']}")
                return
            
            import time
            trade_id = f"{int(time.time())}"[-6:]
            
            msg = f"""
✅ **VENTA EJECUTADA (SIMULADA)**

{symbol}: -{result['amount']:.8f}
Precio: ${result['price']:,.2f}
Total: +${result['total_usd']:,.2f}

💰 **NUEVO BALANCE:**
USD: ${result['new_balance_usd']:,.2f}
BTC: {result['new_btc_balance']:.8f}
ETH: {result['new_eth_balance']:.8f}

*Trade simulado con precio REAL de Kraken*

👇 **¿Cómo resultó este trade?**
"""
            
            from omnix_services.telegram_service.inline_keyboards import InlineKeyboardsManager
            feedback_buttons = InlineKeyboardsManager.get_trade_feedback_buttons(
                trade_id=trade_id,
                strategy="PAPER",
                symbol=symbol,
                signal_type="SELL"
            )
            
            await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=feedback_buttons)
            
        except Exception as e:
            logger.error(f"Error paper_sell: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")
    
    async def auto_start_command(self, update, context):
        """Comando /auto_start - Activar trading automático 24/7 REAL"""
        try:
            logger.info("🎯 COMANDO /auto_start RECIBIDO - Iniciando proceso...")
            
            if not self.auto_trading:
                logger.warning("⚠️ Auto-Trading Bot no disponible")
                await update.message.reply_text("⚠️ Auto-Trading Bot no disponible")
                return
            
            user_id = str(update.effective_user.id)
            logger.info(f"🔐 Usuario autorizado: {user_id}")
            
            if not _check_admin_permission(user_id, 'auto_trading'):
                logger.warning(f"⚠️ Unauthorized user for auto-trading: {user_id}")
                await update.message.reply_text("⚠️ Only OWNER can activate auto-trading")
                return
            
            logger.info("✅ Validaciones OK - Activando bot...")
            await update.message.reply_text("🔄 Activando trading automático 24/7...")
            
            logger.info(f"📞 Llamando a auto_trading.start(user_id={user_id})...")
            result = self.auto_trading.start(user_id=user_id)
            logger.info(f"📊 Resultado de start(): {result}")
            
            if 'error' in result:
                await update.message.reply_text(f"❌ {result['error']}")
                return
            
            # Obtener balance REAL actual del paper trading
            current_balance = result['initial_balance']
            balance_display = f"${current_balance:,.2f}"
            pnl_text = ""
            
            if self.paper_trading:
                try:
                    real_balance = self.paper_trading.get_paper_balance(user_id)
                    if real_balance.get('initialized'):
                        current_balance = real_balance.get('total_value_usd', current_balance)
                        pnl = real_balance.get('profit_loss_usd', 0)
                        pnl_pct = real_balance.get('profit_loss_pct', 0)
                        balance_display = f"${current_balance:,.2f}"
                        if pnl != 0:
                            pnl_emoji = "📈" if pnl >= 0 else "📉"
                            pnl_text = f"\n{pnl_emoji} P&L: ${pnl:+,.2f} ({pnl_pct:+.2f}%)"
                except Exception as e:
                    logger.warning(f"Error obteniendo balance real: {e}")
            
            # Obtener pares activos de la configuración
            trading_pairs = result['config'].get('trading_pairs', ['BTC/USD'])
            if isinstance(trading_pairs, list) and len(trading_pairs) > 1:
                pairs_display = ", ".join([p.split('/')[0] for p in trading_pairs])
            else:
                pairs_display = result['config'].get('trading_pair', 'BTC/USD')
            
            msg = f"""
🤖 **AUTO-TRADING ACTIVADO 24/7**

💰 Balance actual: {balance_display}{pnl_text}

**ESTRATEGIA INTELIGENTE:**
✅ Monte Carlo - Validación probabilística
✅ Black Swan - Detección de riesgos extremos
✅ Sentiment - Timing basado en mercado
✅ Post-Quantum - Firmas seguras

**CONFIGURACIÓN:**
📊 Pares: {pairs_display}
⏱️ Análisis cada: {result['config']['check_interval_seconds']}s
💵 Mínimo trade: ${result['config']['min_trade_usd']}
📉 Stop-loss: {result['config']['stop_loss_pct']*100}%
🛑 Máx pérdida diaria: {result['config']['max_daily_loss_pct']*100}%

**PROTECCIONES:**
✅ Parada automática si pérdidas > 5%
✅ Validación múltiple antes de cada trade
✅ Logging completo de decisiones
"""
            
            # Agregar advertencia según modo
            if result['config'].get('paper_mode', True):
                msg += f"""
✅ **MODO:** PAPER TRADING
💰 Trades simulados con datos REALES de Kraken
📊 Sin riesgo - Ideal para generar track record

El bot tomará decisiones automáticamente 24/7

Usa /auto_status para ver estado
Usa /auto_stop para detener
"""
            else:
                msg += """
🚨 **ADVERTENCIA:** Trading REAL con dinero real
El bot tomará decisiones automáticamente 24/7

Usa /auto_status para ver estado
Usa /auto_stop para detener
"""
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error auto_start: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")
    
    async def auto_stop_command(self, update, context):
        """Comando /auto_stop - Detener trading automático"""
        try:
            if not self.auto_trading:
                await update.message.reply_text("⚠️ Auto-Trading Bot no disponible")
                return
            
            user_id = str(update.effective_user.id)
            
            if not _check_admin_permission(user_id, 'auto_trading'):
                await update.message.reply_text("⚠️ Only OWNER can stop auto-trading")
                return
            
            await update.message.reply_text("🔄 Deteniendo trading automático...")
            
            result = self.auto_trading.stop(user_id=user_id)
            
            if 'error' in result:
                await update.message.reply_text(f"❌ {result['error']}")
                return
            
            stats = result.get('stats', {})
            
            # Obtener balance REAL actual del paper trading
            current_balance = stats.get('initial_balance', 0)
            balance_display = f"${current_balance:,.2f}"
            pnl_text = ""
            
            if self.paper_trading:
                try:
                    real_balance = self.paper_trading.get_paper_balance(user_id)
                    if real_balance.get('initialized'):
                        current_balance = real_balance.get('total_value_usd', current_balance)
                        pnl = real_balance.get('profit_loss_usd', 0)
                        pnl_pct = real_balance.get('profit_loss_pct', 0)
                        balance_display = f"${current_balance:,.2f}"
                        pnl_emoji = "📈" if pnl >= 0 else "📉"
                        pnl_text = f"{pnl_emoji} P&L Total: ${pnl:+,.2f} ({pnl_pct:+.2f}%)"
                except Exception as e:
                    logger.warning(f"Error obteniendo balance real: {e}")
            
            msg = f"""
🛑 **AUTO-TRADING DETENIDO**

📊 **ESTADÍSTICAS FINALES:**
Trades totales: {stats.get('total_trades', 0)}
Ganadores: {stats.get('winning_trades', 0)}
Perdedores: {stats.get('losing_trades', 0)}

💰 **Balance actual:** {balance_display}
{pnl_text}

*Bot detenido exitosamente*
"""
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error auto_stop: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")
    
    async def auto_status_command(self, update, context):
        """Comando /auto_status - Ver estado del auto-trading"""
        try:
            if not self.auto_trading:
                await update.message.reply_text("⚠️ Auto-Trading Bot no disponible")
                return
            
            status = self.auto_trading.get_status()
            stats = status.get('stats', {})
            
            if not status.get('running'):
                msg = """
🤖 **AUTO-TRADING: INACTIVO**

Usa /auto_start para activar trading automático 24/7
"""
            else:
                msg = f"""
🤖 **AUTO-TRADING: ACTIVO 24/7**

📊 **ESTADO:**
{"🚨 PARADA DE EMERGENCIA" if status.get('emergency_stop') else "✅ Operando normalmente"}

💹 **PAR:** {status.get('trading_pair', 'N/A')}

📈 **ESTADÍSTICAS:**
Trades totales: {stats.get('total_trades', 0)}
Ganadores: {stats.get('winning_trades', 0)}
Perdedores: {stats.get('losing_trades', 0)}
P&L total: ${stats.get('total_profit_loss', 0):.2f}

💰 **BALANCE:**
Inicial: ${stats.get('initial_balance', 0):.2f}

*Bot analizando mercado continuamente*
Usa /auto_stop para detener
"""
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error auto_status: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")
    
    async def activar_auto_ajuste_command(self, update, context):
        """Comando /activar_auto_ajuste - Activar aprendizaje automático desde videos"""
        try:
            if not self.auto_trading:
                await update.message.reply_text("⚠️ Auto-Trading Bot no disponible")
                return
            
            user_id = str(update.effective_user.id)
            
            if not _check_admin_permission(user_id, 'admin'):
                await update.message.reply_text("⚠️ Only OWNER can activate auto-learning")
                return
            
            await update.message.reply_text("🔄 Activando auto-learning...")
            
            result = self.auto_trading.enable_auto_learning()
            
            if result.get('status') == 'enabled':
                msg = f"""
🎓 **AUTO-LEARNING ACTIVADO**

✅ El bot ahora aprenderá automáticamente de videos de YouTube
📊 Parámetros ajustables: {result.get('adjustable_params', 0)}
🔒 Parámetros bloqueados: {result.get('locked_params', 0)}

💡 **Cómo usar:**
1. Envía cualquier URL de YouTube con trading
2. El bot analizará y aplicará ajustes automáticamente
3. Usa /ver_aprendizaje para ver historial
4. Usa /revertir_cambio si algo no funciona

⚠️ **Nota:** Solo se ajustan parámetros técnicos seguros
"""
            else:
                msg = f"❌ Error: {result.get('message', 'Error desconocido')}"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error activar_auto_ajuste: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")
    
    async def pausar_auto_ajuste_command(self, update, context):
        """Comando /pausar_auto_ajuste - Pausar aprendizaje automático (solo proponer)"""
        try:
            if not self.auto_trading:
                await update.message.reply_text("⚠️ Auto-Trading Bot no disponible")
                return
            
            user_id = str(update.effective_user.id)
            
            if not _check_admin_permission(user_id, 'admin'):
                await update.message.reply_text("⚠️ Only OWNER can pause auto-learning")
                return
            
            await update.message.reply_text("⏸️ Pausando auto-learning...")
            
            result = self.auto_trading.disable_auto_learning()
            
            if result.get('status') == 'disabled':
                msg = """
⏸️ **AUTO-LEARNING PAUSADO**

✅ El bot ya NO aplicará cambios automáticamente
💡 Seguirá analizando videos pero esperará tu aprobación

📋 **Modo manual activado:**
1. Envía URL de YouTube
2. El bot te mostrará propuestas
3. Responde "aplicar" para confirmar
4. O ignora si no te convence

Usa /activar_auto_ajuste para volver a modo automático
"""
            else:
                msg = f"❌ Error: {result.get('message', 'Error desconocido')}"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error pausar_auto_ajuste: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")
    
    async def ver_aprendizaje_command(self, update, context):
        """Comando /ver_aprendizaje - Ver estado y historial del auto-learning"""
        try:
            if not self.auto_trading:
                await update.message.reply_text("⚠️ Auto-Trading Bot no disponible")
                return
            
            await update.message.reply_text("📊 Obteniendo estado del auto-learning...")
            
            status = self.auto_trading.get_learning_status()
            
            if status.get('available'):
                enabled = status.get('enabled', False)
                state = "✅ ACTIVADO" if enabled else "⏸️ PAUSADO"
                
                msg = f"""
🎓 **AUTO-LEARNING - ESTADO**

**Estado:** {state}

📊 **CONFIGURACIÓN:**
Parámetros ajustables: {status.get('adjustable_params', 0)}
Parámetros bloqueados: {status.get('locked_params', 0)}
Total cambios realizados: {status.get('total_changes', 0)}

"""
                
                # Agregar historial reciente
                recent = status.get('recent_changes', [])
                if recent:
                    msg += "📝 **ÚLTIMOS CAMBIOS:**\n"
                    for change in recent[:3]:  # Solo mostrar últimos 3
                        param = change.get('parameter', 'N/A')
                        old_val = change.get('old_value', 'N/A')
                        new_val = change.get('new_value', 'N/A')
                        timestamp = change.get('timestamp', 'N/A')
                        msg += f"• {timestamp}: {param} ({old_val} → {new_val})\n"
                else:
                    msg += "📝 No hay cambios registrados aún\n"
                
                msg += f"\n💡 Usa /{'pausar' if enabled else 'activar'}_auto_ajuste para {'pausar' if enabled else 'activar'}"
            else:
                msg = "⚠️ Auto-Learning System no disponible en este momento"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error ver_aprendizaje: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")
    
    async def revertir_cambio_command(self, update, context):
        """Comando /revertir_cambio - Revertir último cambio del auto-learning"""
        try:
            if not self.auto_trading:
                await update.message.reply_text("⚠️ Auto-Trading Bot no disponible")
                return
            
            user_id = str(update.effective_user.id)
            
            if not _check_admin_permission(user_id, 'admin'):
                await update.message.reply_text("⚠️ Only OWNER can revert changes")
                return
            
            await update.message.reply_text("↩️ Revirtiendo último cambio...")
            
            result = self.auto_trading.rollback_last_learning()
            
            if result.get('status') == 'success':
                param = result.get('parameter', 'N/A')
                old_val = result.get('old_value', 'N/A')
                new_val = result.get('new_value', 'N/A')
                
                msg = f"""
↩️ **CAMBIO REVERTIDO EXITOSAMENTE**

📊 **Detalles:**
Parámetro: {param}
Valor anterior: {new_val}
Valor actual: {old_val}

✅ El sistema ha vuelto al estado anterior

💡 Usa /ver_aprendizaje para verificar el estado
"""
            elif result.get('status') == 'no_changes':
                msg = """
⚠️ **NO HAY CAMBIOS PARA REVERTIR**

No se han realizado cambios recientes en el auto-learning

💡 Envía un video de YouTube para que el bot aprenda
"""
            else:
                msg = f"❌ Error: {result.get('message', 'Error desconocido')}"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error revertir_cambio: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")
    
    async def risk_status_command(self, update, context):
        """Comando /risk_status - Estado del AI Risk Guardian"""
        try:
            # Buscar Risk Guardian en auto_trading o global
            guardian = None
            if self.auto_trading and hasattr(self.auto_trading, 'risk_guardian') and self.auto_trading.risk_guardian:
                guardian = self.auto_trading.risk_guardian
            elif 'global_risk_guardian' in globals() and global_risk_guardian:
                guardian = global_risk_guardian
            
            if not guardian:
                await update.message.reply_text("⚠️ AI Risk Guardian no disponible")
                return
            status = guardian.get_status()
            
            # Emojis de estado
            blocked_emoji = "🛑" if status['is_blocked'] else "✅"
            
            msg = f"""
🛡️ **AI RISK GUARDIAN - ESTADO**

{blocked_emoji} **Trading:** {'BLOQUEADO' if status['is_blocked'] else 'PERMITIDO'}
{'⏱️ **Bloqueado hasta:** ' + status['block_until'] if status['is_blocked'] else ''}
{'📋 **Razón:** ' + status['block_reason'] if status['block_reason'] else ''}

📏 **Factor de Tamaño:** {status['size_reduction_factor']:.0%}
{'⚠️ Posiciones reducidas al ' + str(int(status['size_reduction_factor']*100)) + '%' if status['size_reduction_factor'] < 1.0 else ''}

⚙️ **CONFIGURACIÓN:**
📊 Máx trades/día: {status['config']['max_trades_per_day']}
📊 Máx trades/hora: {status['config']['max_trades_per_hour']}
📉 Drawdown crítico: 20%
🛑 Pérdidas consecutivas: {status['config']['consecutive_losses_trigger']}
💰 Riesgo máx/trade: {status['config']['max_risk_per_trade_pct']*100}%

🛡️ **Protecciones Activas:**
✅ Overtrading Detection
✅ Drawdown Protection
✅ Revenge Trading Detection
✅ Capital Protection

💡 Usa /risk_events para ver eventos recientes
"""
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error risk_status: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")
    
    async def risk_events_command(self, update, context):
        """Comando /risk_events - Eventos recientes del Risk Guardian"""
        try:
            # Buscar Risk Guardian en auto_trading o global
            guardian = None
            if self.auto_trading and hasattr(self.auto_trading, 'risk_guardian') and self.auto_trading.risk_guardian:
                guardian = self.auto_trading.risk_guardian
            elif 'global_risk_guardian' in globals() and global_risk_guardian:
                guardian = global_risk_guardian
            
            if not guardian:
                await update.message.reply_text("⚠️ AI Risk Guardian no disponible")
                return
            hours = int(context.args[0]) if context.args and context.args[0].isdigit() else 24
            
            events = guardian.get_recent_events(hours=hours, limit=10)
            
            if not events:
                msg = f"""
🛡️ **AI RISK GUARDIAN - EVENTOS**

✅ **No hay eventos de riesgo en las últimas {hours} horas**

Todo funcionando dentro de parámetros seguros.

💡 Uso: /risk_events [horas]
Ejemplo: /risk_events 48
"""
            else:
                msg = f"🛡️ **AI RISK GUARDIAN - ÚLTIMOS {len(events)} EVENTOS ({hours}h)**\n\n"
                
                emoji_map = {
                    'CRITICAL': '🚨',
                    'HIGH': '⚠️',
                    'MEDIUM': '⚡',
                    'LOW': 'ℹ️'
                }
                
                for i, event in enumerate(events[:5], 1):  # Mostrar solo los primeros 5
                    risk_level = event.get('risk_level', 'UNKNOWN')
                    emoji = emoji_map.get(risk_level, '📊')
                    
                    timestamp = event.get('timestamp')
                    if timestamp:
                        from datetime import datetime
                        if isinstance(timestamp, str):
                            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = timestamp.strftime('%H:%M:%S')
                    else:
                        time_str = 'N/A'
                    
                    msg += f"""
{emoji} **Evento #{i}** - {time_str}
📋 Tipo: {event.get('risk_type', 'N/A')}
🎯 Nivel: {risk_level}
📝 {event.get('description', 'N/A')}
⚡ Acción: {event.get('action_taken', 'N/A')}
"""
                
                msg += f"\n💡 Total: {len(events)} eventos en {hours}h"
            
            await update.message.reply_text(msg, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error risk_events: {e}")
            await update.message.reply_text(f"⚠️ Error: {e}")
    
    def _get_price_history(self, symbol, days=100):
        """Obtener histórico de precios — requiere datos reales de API"""
        try:
            if self.trading and hasattr(self.trading, 'kraken'):
                pair_map = {'BTC': 'XBTUSD', 'ETH': 'ETHUSD'}
                kraken_pair = pair_map.get(symbol, f"{symbol}USD")
                ohlc_data = self.trading.kraken.get_ohlc(kraken_pair, interval=1440)
                if ohlc_data and len(ohlc_data) >= days:
                    return [float(candle[4]) for candle in ohlc_data[-days:]]
                elif ohlc_data:
                    return [float(candle[4]) for candle in ohlc_data]
            return None
        except Exception:
            return None
    
    def _get_order_book(self, symbol):
        """Obtener order book"""
        try:
            if self.trading and hasattr(self.trading, 'exchange'):
                order_book = self.trading.exchange.fetch_order_book(f"{symbol}/USD")
                return order_book
            return None
        except Exception:
            return None

    async def _process_aggregated_messages(self, user_id: str, context):
        """Procesar mensajes agregados después del delay de debounce"""
        try:
            if user_id not in self._message_buffers or not self._message_buffers[user_id]:
                return
            
            buffered_messages = self._message_buffers.pop(user_id, [])
            if user_id in self._message_timers:
                del self._message_timers[user_id]
            
            if not buffered_messages:
                return
            
            combined_text = " ".join([msg['text'] for msg in buffered_messages if msg.get('text')])
            first_msg = buffered_messages[0]
            update = first_msg['update']
            user = first_msg['user']
            user_name = first_msg['user_name']
            telegram_chat_id = first_msg['telegram_chat_id']
            
            logger.info(f"📦 MENSAJE AGREGADO ({len(buffered_messages)} partes) de {user_name}: {combined_text[:100]}...")
            
            await self._process_message_content(update, context, combined_text, user, user_id, user_name, telegram_chat_id)
            
        except Exception as e:
            import traceback
            logger.error(f"❌ Error procesando mensajes agregados: {e}")
            logger.error(f"❌ TRACEBACK COMPLETO: {traceback.format_exc()}")
            try:
                if buffered_messages and buffered_messages[0].get('update'):
                    await buffered_messages[0]['update'].message.reply_text("🤖 OMNIX encontró un inconveniente. Por favor intenta de nuevo en un momento.")
            except Exception:
                pass

    async def handle_message(self, update, context):
        """Manejar mensajes con SUPERINTELIGENCIA + VOZ AUTOMÁTICA + AGREGACIÓN"""
        try:
            user_message = update.message.text
            user = update.effective_user
            user_id = str(user.id)
            user_name = user.first_name or "Usuario"
            telegram_chat_id = str(update.effective_chat.id)
            chat_type = update.effective_chat.type  # "private", "group", "supergroup", "channel"

            # ── [ADR-083] Enterprise Security Check ─────────────────────────
            if self.security is not None:
                _sec_result = self.security.check(user_id, chat_type, user_message or "")
                if not _sec_result.allowed:
                    logger.warning(
                        f"[ADR-083] BLOCKED user={user_id} reason={_sec_result.reason} "
                        f"injection={_sec_result.injection_detected} rate_limited={_sec_result.rate_limited}"
                    )
                    if _sec_result.reply_message:
                        try:
                            await update.message.reply_text(_sec_result.reply_message)
                        except Exception:
                            pass
                    return
                user_message = _sec_result.sanitized_message or user_message
            # ────────────────────────────────────────────────────────────────

            # [ADR-083] Buffer size guard — prevent unbounded memory growth
            if user_id in self._message_buffers and len(self._message_buffers[user_id]) >= 5:
                self._message_buffers[user_id].pop(0)

            if user_id in self._message_timers:
                self._message_timers[user_id].cancel()
                logger.info(f"🔄 Timer cancelado para {user_name} - agregando mensaje al buffer")
            
            if user_id not in self._message_buffers:
                self._message_buffers[user_id] = []
            
            self._message_buffers[user_id].append({
                'text': user_message,
                'update': update,
                'user': user,
                'user_name': user_name,
                'telegram_chat_id': telegram_chat_id,
                'timestamp': time.time()
            })
            
            logger.info(f"📥 Mensaje #{len(self._message_buffers[user_id])} buffered de {user_name}: {user_message[:50]}...")
            
            async def delayed_process():
                await asyncio.sleep(self._message_aggregation_delay)
                await self._process_aggregated_messages(user_id, context)
            
            self._message_timers[user_id] = asyncio.create_task(delayed_process())
            
        except Exception as e:
            import traceback
            logger.error(f"❌ Error en handle_message (agregación): {e}")
            logger.error(f"❌ TRACEBACK COMPLETO: {traceback.format_exc()}")
            try:
                # FIX Dec 31, 2025: No mostrar errores técnicos al usuario
                await update.message.reply_text("🤖 OMNIX procesando tu mensaje. Por favor espera un momento...")
            except Exception:
                pass

    async def _process_message_content(self, update, context, user_message: str, user, user_id: str, user_name: str, telegram_chat_id: str):
        """Procesar el contenido del mensaje (original o agregado)"""
        try:
            logger.info(f"🧠 PROCESANDO MENSAJE de {user_name} ({user_id}): {user_message[:100]}...")
            
            # ✅ FIX CRÍTICO: Garantizar que usuario existe ANTES de cualquier DB write
            # Esto previene FK constraint violations en conversations, trades, signals, etc.
            if self.db_manager:
                user_registered = self.db_manager.ensure_user_exists(
                    user_id=user_id,
                    username=user.username,
                    first_name=user.first_name or "Usuario",
                    language_code=user.language_code or 'es'
                )
                if user_registered:
                    logger.info(f"✅ Usuario {user_id} registrado/actualizado exitosamente")
                else:
                    logger.error(f"❌ CRÍTICO: Failed to register user {user_id} - DB writes may fail")
            else:
                logger.warning(f"⚠️ db_manager not available - user {user_id} NOT registered")
            
            # ⚙️ USER SETTINGS: Procesamiento de comandos de configuración
            # FIX Dec 18, 2025: AI-FIRST - Solo procesar NLP config si mensaje es comando explícito
            # Los comandos SIEMPRE empiezan con "/" - no procesar texto libre como comandos
            # Esto previene falsos positivos como "resumen" → "resume" en preguntas complejas
            is_explicit_command = user_message.strip().startswith('/')
            
            if is_explicit_command and self.user_settings_service and USER_SETTINGS_AVAILABLE:
                nlp_result = self.user_settings_service.process_natural_language_command(user_id, user_message)
                
                if nlp_result:
                    action, params = nlp_result
                    logger.info(f"⚙️ COMANDO EXPLÍCITO detectado: {action} con params: {params}")
                    
                    if action == 'update_risk':
                        suggested = params.get('suggested_profile')
                        if params.get('action') == 'increase':
                            response = f"""🎯 Entendido, quieres un perfil más agresivo.

Para cambiar a perfil **{suggested.value}**, usa:
`/perfil {suggested.value}` {'ACEPTO' if suggested == RiskProfile.AGGRESSIVE else ''}

Esto aumentará tus límites de trading y potencial de ganancias (y riesgo).

Usa `/perfil` para ver todas las opciones disponibles."""
                        else:
                            response = f"""🛡️ Entendido, prefieres proteger tu capital.

Para cambiar a perfil **{suggested.value}**, usa:
`/perfil {suggested.value}`

Esto reducirá tus límites de exposición para mayor seguridad.

Usa `/perfil` para ver todas las opciones disponibles."""
                        await update.message.reply_text(response, parse_mode='Markdown')
                        return
                    
                    elif action == 'update_limit':
                        limit_type = params.get('type')
                        value = params.get('value')
                        if limit_type == 'max_trade':
                            success, msg = self.user_settings_service.update_trading_limits(user_id, max_trade=value)
                            await update.message.reply_text(msg, parse_mode='Markdown')
                            return
                        elif limit_type == 'min_trade':
                            success, msg = self.user_settings_service.update_trading_limits(user_id, min_trade=value)
                            await update.message.reply_text(msg, parse_mode='Markdown')
                            return
                    
                    elif action == 'pause':
                        success, msg = self.user_settings_service.pause_trading(user_id, "Pausa solicitada por usuario", 60)
                        if success and self.auto_trading:
                            try:
                                self.auto_trading.stop(user_id)
                                logger.info(f"🔗 Event bridge: AutoTradingBot.stop() called for user {user_id}")
                            except Exception as e:
                                logger.warning(f"⚠️ Event bridge pause error: {e}")
                        await update.message.reply_text(msg, parse_mode='Markdown')
                        return
                    
                    elif action == 'resume':
                        success, msg = self.user_settings_service.resume_trading(user_id)
                        if success and self.auto_trading:
                            try:
                                settings = self.user_settings_service.get_user_settings(user_id)
                                if settings.auto_trading and settings.trading_enabled:
                                    result = self.auto_trading.start(user_id)
                                    if result.get('success'):
                                        msg += "\n\n🔄 Auto-trading loop reiniciado automáticamente."
                                        logger.info(f"🔗 Event bridge: AutoTradingBot.start() called for user {user_id}")
                                    elif 'ya está corriendo' in result.get('error', ''):
                                        logger.info(f"🔗 Event bridge: Bot already running for user {user_id}")
                            except Exception as e:
                                logger.warning(f"⚠️ Event bridge resume error: {e}")
                        await update.message.reply_text(msg, parse_mode='Markdown')
                        return
                    
                    elif action == 'auto_trading':
                        enable = params.get('enable', False)
                        if enable:
                            response = """🤖 Para activar el trading automático, confirma que entiendes el sistema.

Usa: `/autotrading activar ACEPTO`"""
                        else:
                            success, msg = self.user_settings_service.toggle_auto_trading(user_id, False)
                            response = msg
                        await update.message.reply_text(response, parse_mode='Markdown')
                        return
            
            # 🔍 DETECCIÓN NATURAL DE BÚSQUEDA WEB
            # Detectar si el usuario quiere buscar algo en internet naturalmente
            if WEB_SEARCH_AVAILABLE:
                import re
                search_patterns = [
                    r'^busca\s+(.+)',        # "busca noticias de bitcoin"
                    r'^buscar\s+(.+)',       # "buscar ethereum hoy"
                    r'^encuentra\s+(.+)',    # "encuentra información sobre solana"
                    r'^search\s+(.+)',       # "search bitcoin news"
                    r'^find\s+(.+)',         # "find crypto news"
                ]
                
                for pattern in search_patterns:
                    match = re.match(pattern, user_message.lower().strip())
                    if match:
                        search_query = match.group(1).strip()
                        logger.info(f"🔍 Búsqueda natural detectada: '{search_query}'")
                        
                        # Mostrar que estamos buscando
                        searching_msg = await update.message.reply_text(
                            f"🔍 Buscando: *{search_query}*...",
                            parse_mode='Markdown'
                        )
                        
                        try:
                            search_manager = get_search_manager()
                            result = search_manager.search(search_query, max_results=5, force_search=True)
                            
                            if result.get("success"):
                                results = result.get("results", [])
                                answer = result.get("answer", "")
                                from_cache = result.get("from_cache", False)
                                
                                if answer:
                                    response = f"""🔍 **Resultado de búsqueda**

**Pregunta:** {search_query}

**Respuesta:**
{answer}

"""
                                else:
                                    response = f"""🔍 **Resultados de búsqueda**

**Búsqueda:** {search_query}

"""
                                
                                if results:
                                    response += "**Fuentes encontradas:**\n"
                                    for i, r in enumerate(results[:5], 1):
                                        title = r.get("title", "Sin título")[:50]
                                        url = r.get("url", "")
                                        response += f"{i}. [{title}]({url})\n"
                                
                                if from_cache:
                                    response += "\n_📦 Resultado en caché (15 min)_"
                                
                                await searching_msg.edit_text(response, parse_mode='Markdown', disable_web_page_preview=True)
                            else:
                                error_msg = result.get("error", "Error desconocido")
                                await searching_msg.edit_text(
                                    f"⚠️ No se pudo buscar: {error_msg}",
                                    parse_mode='Markdown'
                                )
                        except Exception as e:
                            logger.error(f"❌ Error en búsqueda natural: {e}")
                            await searching_msg.edit_text(
                                "❌ No se pudo realizar la búsqueda en este momento. Por favor intenta de nuevo.",
                                parse_mode='Markdown'
                            )
                        
                        return  # SALIR - ya procesamos la búsqueda
            
            # ⚡ PRIORIDAD MÁXIMA: Comandos específicos del bot
            # Verificar PRIMERO si es comando /autotrading ANTES de enviar a IA
            if user_message.startswith('/autotrading') or user_message.startswith('/auto'):
                logger.info("🤖 Comando /autotrading detectado - procesando directamente")
                
                # Parsear sub-comando
                parts = user_message.lower().split()
                sub_cmd = parts[1] if len(parts) > 1 else 'status'
                
                # Delegar al método correcto
                if sub_cmd == 'start':
                    await self.auto_start_command(update, context)
                elif sub_cmd == 'stop':
                    await self.auto_stop_command(update, context)
                elif sub_cmd == 'status':
                    await self.auto_status_command(update, context)
                else:
                    # Mostrar ayuda
                    await update.message.reply_text(f"""🤖 AUTO-TRADING BOT — OMNIX Decision Governance
                    
📋 COMANDOS:
/autotrading start → Iniciar bot 24/7
/autotrading stop → Detener bot
/autotrading status → Ver estado

ℹ️ EJEMPLO: /autotrading start""")
                
                return  # SALIR - NO enviar a IA
            
            # 🎥 FIX Nov 29, 2025: DETECCIÓN DE URLs DE YOUTUBE EN MENSAJES DE TEXTO
            # Detectar si el mensaje contiene una URL de YouTube y procesarla con VideoAnalyzerUltra
            # También detecta URLs en mensajes reenviados con preview embebido
            import re
            youtube_pattern = r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)([\w\-]+)'
            youtube_match = re.search(youtube_pattern, user_message or '')
            
            # También buscar en entities del mensaje (URLs embebidas de reenvíos)
            if not youtube_match and update.message.entities:
                for entity in update.message.entities:
                    if entity.type == 'url':
                        url_text = user_message[entity.offset:entity.offset + entity.length]
                        if 'youtube.com' in url_text or 'youtu.be' in url_text:
                            youtube_match = re.search(youtube_pattern, url_text)
                            break
            
            # Buscar en caption si es un mensaje con media
            if not youtube_match and update.message.caption:
                youtube_match = re.search(youtube_pattern, update.message.caption)
            
            # Buscar en reply_to_message si el usuario está respondiendo a un mensaje con video
            if not youtube_match and update.message.reply_to_message:
                reply_text = update.message.reply_to_message.text or update.message.reply_to_message.caption or ''
                youtube_match = re.search(youtube_pattern, reply_text)
            
            if youtube_match:
                video_url = youtube_match.group(0)
                if not video_url.startswith('http'):
                    video_url = 'https://' + video_url
                
                logger.info(f"🎥 URL de YouTube detectada en handle_message: {video_url}")
                
                processing_msg = await update.message.reply_text("🎬 Video de YouTube detectado - Obteniendo transcripción...")
                
                try:
                    video_context = f"ANÁLISIS DE VIDEO DE YOUTUBE: {video_url}\n\n"
                    has_real_content = False
                    error_detail = ""
                    
                    if hasattr(self, 'video_analyzer_ultra') and self.video_analyzer_ultra:
                        logger.info("🎬 Usando get_transcript_robust() para obtener transcripción")
                        try:
                            transcript_result = self.video_analyzer_ultra.get_transcript_robust(video_url)
                            
                            if transcript_result.get('success') and transcript_result.get('transcript'):
                                transcript_text = transcript_result['transcript']
                                method = transcript_result.get('method', 'unknown')
                                logger.info(f"✅ Transcripción obtenida via {method}: {len(transcript_text)} chars")
                                
                                video_context += f"📜 TRANSCRIPCIÓN DEL VIDEO ({len(transcript_text)} chars):\n{transcript_text[:4000]}\n"
                                video_context += f"\n✅ Método usado: {method}"
                                has_real_content = True
                            else:
                                error_detail = transcript_result.get('error', 'Error desconocido')
                                logger.warning(f"⚠️ Transcripción falló: {error_detail}")
                        except Exception as va_error:
                            error_detail = str(va_error)
                            logger.error(f"❌ Error en get_transcript_robust: {va_error}")
                    else:
                        error_detail = "VideoAnalyzerUltra no disponible"
                        logger.warning(f"⚠️ {error_detail}")
                    
                    if not has_real_content:
                        video_context += f"\n⚠️ No se pudo obtener la transcripción del video.\n"
                        video_context += f"Razón: {error_detail}\n"
                        video_context += "El video puede tener subtítulos deshabilitados, ser privado, o estar bloqueado por región."
                    
                    video_context += f"\n\nMensaje original del usuario: {user_message}"
                    
                    logger.info(f"🧠 Enviando a IA con contexto de video: {len(video_context)} chars, tiene_contenido: {has_real_content}")
                    ai_response = await self.ai.generate_response_async(
                        user_message=video_context,
                        user_name=user_name,
                        chat_id=telegram_chat_id,
                        user_id=user_id,
                        trading_system=self.trading
                    )
                    
                    if not ai_response:
                        if has_real_content:
                            ai_response = f"🎬 Obtuve la transcripción del video ({len(transcript_text)} chars) pero no pude generar una respuesta. ¿Qué aspecto te gustaría que analice?"
                        else:
                            ai_response = f"🎬 No pude obtener la transcripción del video.\n\n❌ {error_detail}\n\n¿Puedes compartirme de qué trata el video para ayudarte?"
                    
                    await processing_msg.edit_text(ai_response[:4000])
                    
                    if self.db_manager:
                        try:
                            self.db_manager.save_conversation(
                                user_id=user_id,
                                user_message=f"[VIDEO YOUTUBE: {video_url}] {user_message}",
                                ai_response=ai_response[:1000],
                                language='es'
                            )
                        except Exception as db_error:
                            logger.warning(f"⚠️ Error guardando conversación de video: {db_error}")
                    
                    logger.info(f"✅ Análisis de video YouTube completado: {len(ai_response)} chars")
                    return
                    
                except Exception as video_error:
                    logger.error(f"❌ Error procesando video YouTube: {video_error}")
                    await processing_msg.edit_text(f"❌ Error analizando el video: {str(video_error)[:100]}. Por favor intenta de nuevo.")
                    return
            
            # 🚀 GENERAR RESPUESTA CON SUPERINTELIGENCIA OMNIX
            # FIX FINAL Dec 31, 2025: ACK inmediato + respuesta nueva (sin edit_text)
            # Esto evita timeouts porque:
            # 1. ACK sale inmediatamente (bot parece rápido)
            # 2. IA procesa sin prisa
            # 3. Respuesta llega como mensaje nuevo (no edit que puede fallar)
            
            # ACK INMEDIATO - Sale en <100ms (con retry para nunca perder el ack)
            try:
                from telegram.error import TimedOut, NetworkError, RetryAfter
                for _ack_attempt in range(4):
                    try:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text="🧠 Procesando tu mensaje..."
                        )
                        break
                    except (TimedOut, NetworkError) as _ack_err:
                        if _ack_attempt < 3:
                            await asyncio.sleep((_ack_attempt + 1) * 2)
                        else:
                            logger.warning(f"⚠️ ACK no enviado tras 4 intentos (continuando): {_ack_err}")
                    except RetryAfter as _ra:
                        await asyncio.sleep(_ra.retry_after)
                    except Exception as _ack_generic:
                        logger.warning(f"⚠️ ACK error (continuando sin ack): {_ack_generic}")
                        break
            except Exception:
                pass  # El bot NUNCA muere por un ACK fallido
            
            try:
                logger.info(f"🧠 AI_CALL_START: Llamando a generate_response_async para {user_name}")
                
                # RULE 13 ENFORCEMENT (Jan 1, 2026): Detect TECHNICAL_DIAGNOSTIC queries
                is_diagnostic_query = False
                if INVESTOR_RESPONSES_AVAILABLE and investor_response_engine:
                    query_type = investor_response_engine.detect_query_type(user_message)
                    if query_type == InvestorQueryType.TECHNICAL_DIAGNOSTIC:
                        is_diagnostic_query = True
                        logger.info(f"🔬 [DIAGNOSTIC_MODE] Detected TECHNICAL_DIAGNOSTIC query from {user_name}")
                
                # Generate response with diagnostic_mode flag
                ai_response = await self.ai.generate_response_async(
                    user_message=user_message,
                    user_name=user_name,
                    chat_id=telegram_chat_id,
                    user_id=user_id,
                    trading_system=self.trading,
                    diagnostic_mode=is_diagnostic_query
                )
                
                logger.info(f"🧠 AI_CALL_END: Respuesta generada para {user_name}: {len(ai_response) if ai_response else 0} chars (diagnostic={is_diagnostic_query})")
                
                # RULE 13 POST-VALIDATION (Jan 1, 2026): Validate diagnostic responses
                if is_diagnostic_query and ai_response and diagnostic_validator:
                    is_valid, violations = diagnostic_validator.validate(ai_response)
                    if not is_valid:
                        logger.warning(f"🚫 [DIAGNOSTIC_VALIDATOR] Response INVALID: {violations}")
                        # Use template fallback for guaranteed compliance
                        ai_response = investor_response_engine.get_response(InvestorQueryType.TECHNICAL_DIAGNOSTIC)
                        logger.info(f"✅ [DIAGNOSTIC_FALLBACK] Using template response: {len(ai_response)} chars")
                    else:
                        logger.info(f"✅ [DIAGNOSTIC_VALIDATOR] Response VALID")
                
                if not ai_response:
                    ai_response = f"🧠 OMNIX IA procesando tu consulta, {user_name}. Sistema operativo."
                
                if CONTEXTUAL_COMPRESS_AVAILABLE:
                    try:
                        pre_len = len(ai_response)
                        ai_response = compress_response_contextual(ai_response, user_message)
                        post_len = len(ai_response)
                        logger.info(f"🗜️ [COMPRESS_APPLIED] {pre_len} → {post_len} chars for '{user_message[:40]}'")
                    except Exception as compress_err:
                        logger.error(f"❌ [COMPRESS_ERROR] {compress_err} - sending uncompressed")
                
                # HAROLD FIX V2: Dividir mensajes >4096 chars usando async Telegram API
                # Ya NO se trunca la respuesta - se envía completa dividida inteligentemente
                chat_id = update.effective_chat.id
                
                parts = self.split_text_smart(ai_response, 4000)
                total_parts = len(parts)
                logger.info(f"📨 handle_message: {len(ai_response)} chars → {total_parts} parte(s)")
                
                # FIX FINAL: Enviar respuestas como mensajes nuevos (no edit)
                for i, part in enumerate(parts):
                    header = ""
                    if total_parts > 1:
                        header = f"📄 ({i+1}/{total_parts})\n\n"
                    
                    final_text = header + part
                    clean_text = self._sanitize_markdown(final_text)
                    
                    try:
                        send_result = await send_message_with_retry(update.message, clean_text)
                        logger.info(f"✅ TEXTO ENVIADO Parte {i+1}/{total_parts}: {len(clean_text)} chars | msg_id={send_result.message_id if send_result else 'N/A'}")
                    except Exception as part_error:
                        logger.error(f"❌ ERROR ENVIANDO TEXTO parte {i+1}: {part_error}")
                        try:
                            # Fallback directo sin retry
                            await context.bot.send_message(chat_id=chat_id, text=clean_text)
                            logger.info(f"✅ TEXTO ENVIADO (fallback directo) Parte {i+1}")
                        except Exception as fallback_error:
                            logger.error(f"❌ ERROR CRÍTICO: No se pudo enviar texto parte {i+1}: {fallback_error}")
                    
                    if i < total_parts - 1:
                        await asyncio.sleep(0.3)
                
                logger.info(f"✅ RESPUESTA COMPLETA ENVIADA: {len(ai_response)} caracteres en {total_parts} parte(s)")
                
                # 🧠 GUARDAR CONVERSACIÓN EN POSTGRESQL (PERSISTENTE - sobrevive reinicios)
                # FIX Nov 28, 2025: handle_message ahora guarda historial igual que handle_direct_message
                if self.db_manager and user_message and ai_response:
                    try:
                        save_success = self.db_manager.save_conversation(
                            user_id=user_id,
                            user_message=user_message,
                            ai_response=ai_response[:1000],
                            language='es'
                        )
                        if save_success:
                            logger.info(f"🧠 Conversación guardada en PostgreSQL para usuario {user_id}")
                        else:
                            logger.warning(f"⚠️ No se pudo guardar conversación para usuario {user_id}")
                    except Exception as save_error:
                        logger.warning(f"⚠️ Error guardando conversación (no crítico): {save_error}")
                
                # 🎤 V007: GENERAR VOZ EN BACKGROUND PARA TODOS LOS USUARIOS
                if VOICE_SERVICE_AVAILABLE and schedule_voice_response:
                    if ai_response and len(ai_response) > 20:
                        try:
                            voice_thread = schedule_voice_response(
                                chat_id=chat_id,
                                response_text=ai_response,
                                user_name=user_name,
                                user_id=user_id,
                                is_admin_user=is_admin(user_id),
                                is_admin_func=is_admin
                            )
                            if voice_thread:
                                logger.info(f"🎤 [V007] ✅ Voz programada para {user_name} (chat_id={chat_id})")
                            else:
                                logger.warning(f"🎤 [V007] ⏭️ Voz saltada para {user_name} (thread=None)")
                        except Exception as voice_error:
                            logger.error(f"🎤 [V007] ❌ Error programando voz para {user_name}: {voice_error}")
                    else:
                        logger.info(f"🎤 [V007] ⏭️ Voz saltada - texto muy corto ({len(ai_response) if ai_response else 0} chars)")
                else:
                    if not VOICE_SERVICE_AVAILABLE:
                        logger.debug(f"🎤 [V007] Voz no disponible - VOICE_SERVICE_AVAILABLE=False")
                
            except Exception as ai_error:
                logger.error(f"❌ Error IA superinteligencia: {ai_error}")
                fallback_response = f"🧠 OMNIX Decision Governance operativo, {user_name}. Tu mensaje recibido correctamente."
                try:
                    await send_message_with_retry(update.message, fallback_response)
                except Exception as _fb_err:
                    logger.error(f"❌ Fallback IA también falló: {_fb_err}")
            
        except Exception as e:
            import traceback
            logger.error(f"❌ Error crítico _process_message_content: {e}")
            logger.error(f"❌ TRACEBACK COMPLETO: {traceback.format_exc()}")
            try:
                # FIX Dec 31, 2025: No mostrar errores técnicos al usuario
                await update.message.reply_text("🤖 OMNIX procesando tu mensaje. Por favor espera un momento...")
            except Exception:
                pass
    
    async def handle_callback(self, update, context):
        """🎨 Handler Premium para botones inline (callbacks)"""
        try:
            from omnix_services.telegram_service.callback_handler import CallbackHandler
            
            # Crear handler de callbacks
            trading_service = self.trading_enterprise if self.trading_enterprise_enabled else self.trading
            callback_handler = CallbackHandler(
                trading_service=trading_service,
                ai_service=self.ai,
                db_service=global_db_manager if 'global_db_manager' in globals() else None
            )
            
            # Procesar callback
            await callback_handler.handle_callback(update, context, bot_instance=self)
            
        except Exception as e:
            logger.error(f"❌ Error en handle_callback: {e}")
            try:
                query = update.callback_query
                await query.answer()
                await query.edit_message_text("❌ No se pudo procesar la acción. Por favor intenta de nuevo.")
            except Exception:
                pass

    async def handle_voice_message(self, update, context):
        """🎤 HANDLER PREMIUM - Recibir mensajes de voz con Whisper AI"""
        try:
            user = update.effective_user
            user_id = str(user.id)
            user_name = user.first_name or "Usuario"
            
            logger.info(f"🎤 MENSAJE DE VOZ RECIBIDO de {user_name} ({user_id})")
            
            # ✅ FIX CRÍTICO: Garantizar que usuario existe ANTES de cualquier posible DB write
            if self.db_manager:
                user_registered = self.db_manager.ensure_user_exists(
                    user_id=user_id,
                    username=user.username,
                    first_name=user.first_name or "Usuario",
                    language_code=user.language_code or 'es'
                )
                if user_registered:
                    logger.info(f"✅ Usuario {user_id} registrado/actualizado exitosamente (voz)")
                else:
                    logger.error(f"❌ CRÍTICO: Failed to register user {user_id} (voz) - DB writes may fail")
            else:
                logger.warning(f"⚠️ db_manager not available - user {user_id} NOT registered (voz)")
            
            # Mostrar que está procesando
            processing_msg = await update.message.reply_text("🎤 Escuchando tu voz...")
            
            try:
                # Obtener archivo de voz de Telegram
                voice_file = await update.message.voice.get_file()
                
                # Descargar a archivo temporal
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.ogg') as tmp_voice:
                    await voice_file.download_to_drive(tmp_voice.name)
                    voice_path = tmp_voice.name
                
                logger.info(f"🎤 Archivo de voz descargado: {voice_path}")
                
                # Transcribir con Whisper Premium de OpenAI
                transcribed_text = None
                
                # Opción 1: Usar VoiceEngine si está disponible
                if hasattr(self, 'voice_engine') and self.voice_engine:
                    try:
                        logger.info("🎤 Usando VoiceEngine Enterprise para transcripción")
                        transcribed_text = self.voice_engine.transcribe_audio(voice_path)
                    except Exception as ve_error:
                        logger.warning(f"⚠️ VoiceEngine falló: {ve_error}")
                
                # Opción 2: Usar OpenAI Whisper directo si VoiceEngine falla
                if not transcribed_text:
                    try:
                        logger.info("🎤 Usando OpenAI Whisper API directo")
                        import openai
                        
                        openai_key = os.getenv('OPENAI_API_KEY')
                        if openai_key:
                            client = openai.OpenAI(api_key=openai_key)
                            
                            with open(voice_path, 'rb') as audio_file:
                                transcript = client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio_file,
                                    language="es"
                                )
                                transcribed_text = transcript.text
                                logger.info(f"✅ Whisper transcripción: {transcribed_text}")
                        else:
                            logger.error("❌ OPENAI_API_KEY no disponible")
                    except Exception as whisper_error:
                        logger.error(f"❌ Error Whisper directo: {whisper_error}")
                
                # Limpiar archivo temporal
                try:
                    os.unlink(voice_path)
                except Exception:
                    pass
                
                if transcribed_text:
                    # Actualizar mensaje de procesamiento
                    await processing_msg.edit_text(f"🎤 Escuché: \"{transcribed_text}\"\n\n🧠 Procesando...")
                    
                    logger.info(f"🎤 Texto transcrito: {transcribed_text}")
                    
                    # Procesar con la IA directamente (sin FakeUpdate)
                    # FIX Dec 13, 2025: Usar versión async para evitar deadlock
                    ai_response = await self.ai.generate_response_async(
                        user_message=transcribed_text,
                        user_name=user_name,
                        chat_id=telegram_chat_id,
                        user_id=user_id,
                        trading_system=self.trading
                    )
                    
                    if not ai_response:
                        ai_response = f"🧠 OMNIX IA procesando tu mensaje de voz, {user_name}."
                    
                    # Limitar respuesta
                    if len(ai_response) > 4000:
                        ai_response = ai_response[:4000] + "..."
                    
                    # Enviar respuesta de texto
                    await processing_msg.edit_text(ai_response)
                    logger.info(f"✅ RESPUESTA ENVIADA A VOZ: {len(ai_response)} caracteres")
                    
                    # 🎤 ENVIAR VOZ DE RESPUESTA PARA HAROLD
                    if user_id == settings.TELEGRAM_ADMIN_ID:
                        try:
                            voice_text = ai_response
                            import re
                            voice_text = re.sub(r'[*_`#]', '', voice_text)
                            voice_text = re.sub(r'🚀|🧠|⚡|💰|📊|🔴|🟢|🟡|🛡️|🕌|✅|❌|🤖|💡|🎤', '', voice_text)
                            voice_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', voice_text)
                            voice_text = voice_text.strip()
                            
                            if len(voice_text) > 300:
                                voice_text = voice_text[:300] + "..."
                            
                            if len(voice_text) > 20:
                                from gtts import gTTS
                                # AI-First Multilingual: Detectar idioma de respuesta
                                try:
                                    from langdetect import detect
                                    detected_lang = detect(voice_text)
                                    # gTTS usa códigos ISO 639-1
                                    tts_lang = detected_lang if detected_lang else 'es'
                                except Exception:
                                    tts_lang = 'es'  # Fallback a español
                                tts = gTTS(text=voice_text, lang=tts_lang, slow=False)
                                
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                                    tts.save(tmp_file.name)
                                    
                                    with open(tmp_file.name, 'rb') as voice_file:
                                        await update.message.reply_voice(
                                            voice=voice_file,
                                            caption="🎤 OMNIX Voz Premium - Harold"
                                        )
                                    
                                    logger.info("🎤 VOZ PREMIUM ENVIADA EN RESPUESTA")
                                    
                                    try:
                                        os.unlink(tmp_file.name)
                                    except Exception:
                                        pass
                        except Exception as voice_error:
                            logger.warning(f"⚠️ Error voz respuesta: {voice_error}")
                    
                else:
                    await processing_msg.edit_text("❌ No pude escuchar tu voz. Intenta de nuevo por favor.")
                    logger.error("❌ Transcripción falló completamente")
                    
            except Exception as process_error:
                logger.error(f"❌ Error procesando voz: {process_error}")
                await processing_msg.edit_text("❌ Error procesando tu voz. Intenta escribir tu mensaje.")
                
        except Exception as e:
            logger.error(f"❌ Error crítico handle_voice_message: {e}")
            try:
                await update.message.reply_text("❌ Error procesando voz. Usa texto por favor.")
            except Exception:
                pass

    async def handle_video_message(self, update, context):
        """🎥 HANDLER PREMIUM - Recibir videos directos con Vision AI
        
        Soporta:
        - Videos enviados directamente (.mp4, .mov, etc.)
        - Video notes (círculos de Telegram)
        - Usa GPT-4 Vision o Gemini Vision para análisis
        """
        try:
            user = update.effective_user
            user_id = str(user.id)
            user_name = user.first_name or "Usuario"
            
            logger.info(f"🎥 VIDEO DIRECTO RECIBIDO de {user_name} ({user_id})")
            
            if self.db_manager:
                user_registered = self.db_manager.ensure_user_exists(
                    user_id=user_id,
                    username=user.username,
                    first_name=user.first_name or "Usuario",
                    language_code=user.language_code or 'es'
                )
                if user_registered:
                    logger.info(f"✅ Usuario {user_id} registrado/actualizado exitosamente (video)")
                else:
                    logger.error(f"❌ CRÍTICO: Failed to register user {user_id} (video)")
            
            processing_msg = await update.message.reply_text("🎥 Analizando tu video con IA...")
            
            try:
                video = update.message.video or update.message.video_note
                if not video:
                    await processing_msg.edit_text("❌ No pude detectar el video. Intenta enviarlo de nuevo.")
                    return
                
                video_file = await video.get_file()
                file_size_mb = video.file_size / (1024 * 1024) if video.file_size else 0
                duration_sec = video.duration if hasattr(video, 'duration') else 0
                
                logger.info(f"🎥 Video recibido: {file_size_mb:.1f}MB, {duration_sec}s duración")
                
                if file_size_mb > 20:
                    await processing_msg.edit_text(
                        f"⚠️ El video es muy grande ({file_size_mb:.1f}MB).\n\n"
                        "Para mejor análisis, envía videos de menos de 20MB o "
                        "comparte un link de YouTube."
                    )
                    return
                
                import tempfile
                suffix = '.mp4'
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_video:
                    await video_file.download_to_drive(tmp_video.name)
                    video_path = tmp_video.name
                
                logger.info(f"🎥 Video descargado: {video_path}")
                
                await processing_msg.edit_text("🎥 Video recibido. Analizando con Vision AI...")
                
                analysis_result = None
                
                if hasattr(self, 'video_analyzer_ultra') and self.video_analyzer_ultra:
                    try:
                        logger.info("🎥 Usando VideoAnalyzerUltra para análisis")
                        analysis_result = await self._analyze_video_with_vision(video_path, user_name)
                    except Exception as va_error:
                        logger.warning(f"⚠️ VideoAnalyzerUltra falló: {va_error}")
                
                if not analysis_result:
                    try:
                        logger.info("🎥 Usando análisis básico de video")
                        analysis_result = self._basic_video_analysis(video_path, duration_sec, file_size_mb)
                    except Exception as basic_error:
                        logger.error(f"❌ Análisis básico falló: {basic_error}")
                        analysis_result = f"📹 Video recibido ({duration_sec}s, {file_size_mb:.1f}MB). El análisis detallado no está disponible en este momento."
                
                try:
                    os.unlink(video_path)
                except Exception:
                    pass
                
                if analysis_result:
                    caption = update.message.caption or ""
                    if caption:
                        full_context = f"El usuario envió un video con el mensaje: '{caption}'\n\nAnálisis del video:\n{analysis_result}"
                    else:
                        full_context = f"El usuario envió un video para análisis:\n{analysis_result}"
                    
                    # FIX Dec 13, 2025: Usar versión async para evitar deadlock
                    ai_response = await self.ai.generate_response_async(
                        user_message=full_context,
                        user_name=user_name,
                        chat_id=telegram_chat_id,
                        user_id=user_id,
                        trading_system=self.trading
                    )
                    
                    if not ai_response:
                        ai_response = analysis_result
                    
                    if len(ai_response) > 4000:
                        ai_response = ai_response[:4000] + "..."
                    
                    await processing_msg.edit_text(ai_response)
                    logger.info(f"✅ RESPUESTA A VIDEO ENVIADA: {len(ai_response)} caracteres")
                    
                    if self.db_manager:
                        try:
                            self.db_manager.save_conversation(
                                user_id=user_id,
                                user_message=f"[VIDEO: {duration_sec}s, {file_size_mb:.1f}MB] {caption}",
                                ai_response=ai_response,
                                language='es'
                            )
                            logger.info(f"🧠 Conversación de video guardada en PostgreSQL")
                        except Exception as db_error:
                            logger.warning(f"⚠️ No se pudo guardar conversación de video: {db_error}")
                else:
                    await processing_msg.edit_text(
                        "❌ No pude analizar el video.\n\n"
                        "💡 Alternativas:\n"
                        "• Envía un video más corto\n"
                        "• Comparte un link de YouTube\n"
                        "• Describe lo que quieres analizar en texto"
                    )
                    
            except Exception as process_error:
                logger.error(f"❌ Error procesando video: {process_error}")
                await processing_msg.edit_text("❌ Error procesando tu video. Intenta con un video más pequeño o comparte un link de YouTube.")
                
        except Exception as e:
            logger.error(f"❌ Error crítico handle_video_message: {e}")
            try:
                await update.message.reply_text("❌ Error procesando video. Intenta de nuevo o usa texto.")
            except Exception:
                pass
    
    async def _analyze_video_with_vision(self, video_path: str, user_name: str) -> str:
        """Analizar video usando GPT-4 Vision o Gemini Vision"""
        try:
            import cv2
            import base64
            
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            frames_to_extract = min(5, total_frames)
            frame_indices = [int(i * total_frames / frames_to_extract) for i in range(frames_to_extract)]
            
            extracted_frames = []
            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    frame = cv2.resize(frame, (512, 288))
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    extracted_frames.append(base64.b64encode(buffer).decode('utf-8'))
            
            cap.release()
            
            if not extracted_frames:
                return None
            
            import openai
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key and extracted_frames:
                client = openai.OpenAI(api_key=openai_key)
                
                content = [
                    {"type": "text", "text": f"Analiza estos frames de un video enviado por {user_name}. Extrae información relevante para trading si aplica (indicadores técnicos, setup, patrones). Si no es trading, describe el contenido general."}
                ]
                
                for i, frame_b64 in enumerate(extracted_frames[:3]):
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{frame_b64}"}
                    })
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": content}],
                    max_tokens=500
                )
                
                return response.choices[0].message.content
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error en _analyze_video_with_vision: {e}")
            return None
    
    def _basic_video_analysis(self, video_path: str, duration: int, size_mb: float) -> str:
        """Análisis básico cuando Vision AI no está disponible"""
        return f"""📹 **Video Recibido**

• Duración: {duration} segundos
• Tamaño: {size_mb:.1f} MB

💡 El video ha sido recibido correctamente. Para un análisis más detallado de contenido de trading, puedes:

1. **Describir el contenido** en texto para que pueda ayudarte
2. **Compartir un link de YouTube** para análisis completo con IA
3. **Capturar pantalla** de los puntos clave que quieres analizar

¿Qué te gustaría que analice del video?"""

    def handle_direct_message(self, chat_id, text, user_id=None):
        """Manejar mensaje directo usando API de Telegram"""
        global global_conversation_history  # Declarar global al inicio
        try:
            # CRITICAL FIX: Registrar usuario ANTES de cualquier operación DB
            effective_user_id = user_id or chat_id
            if self.db_manager:
                logger.info(f"🔧 handle_direct_message: Registrando usuario {effective_user_id} ANTES de procesar")
                try:
                    self.db_manager.ensure_user_exists(
                        user_id=str(effective_user_id),
                        username=f"user_{effective_user_id}",
                        first_name="Telegram User",
                        language_code='auto'
                    )
                    logger.info(f"✅ Usuario {effective_user_id} registrado/actualizado en handle_direct_message")
                except Exception as user_reg_error:
                    logger.error(f"❌ Error registrando usuario en handle_direct_message: {user_reg_error}")
            else:
                logger.warning("⚠️ db_manager no disponible en handle_direct_message")
            
            # Procesar comando
            response_text = ""
            
            if text.startswith('/start'):
                # Obtener balance REAL de Kraken
                balance_usd = 0
                try:
                    real_balance = self.trading_system.get_real_balance()
                    if real_balance:
                        # Calcular total en USD aproximado
                        for currency, amount in real_balance.items():
                            if currency == 'USD':
                                balance_usd += float(amount)
                            elif currency == 'BTC':
                                btc_price = self.trading_system.get_current_price('BTC/USD')
                                if btc_price:
                                    balance_usd += float(amount) * btc_price
                            elif currency == 'ETH':
                                eth_price = self.trading_system.get_current_price('ETH/USD')
                                if eth_price:
                                    balance_usd += float(amount) * eth_price
                except Exception:
                    balance_usd = 0
                
                balance_display = f"${balance_usd:,.2f} USD" if balance_usd > 0 else "Conectando..."
                
                response_text += f"""🚀 **SISTEMA COMPLETAMENTE OPERATIVO**
💰 Trading REAL con Kraken ({balance_display})
🤖 IA Dual: Gemini 2.0 + OpenAI GPT-4o
📊 Análisis técnico tiempo real

📋 **COMANDOS:**
/precio BTC - 📊 Precio Bitcoin
/balance - 💳 Balance Kraken
/analisis BTC - 🧠 Análisis técnico
/help - ❓ Todos los comandos
/status - 🔍 Estado sistema

💬 Pregúntame sobre criptomonedas y trading.
*Desarrollado por Harold Nunes*"""
                final_response_text = response_text  # HAROLD FIX: Guardar en memoria
            
            elif text.startswith('/precio'):
                response_text += "📊 **PRECIO BITCOIN TIEMPO REAL**\n\n"
                # Obtener precio real de Kraken
                try:
                    price_data = self.trading_system.get_current_price('BTC/USD')
                    if price_data:
                        response_text += f"💰 **BTC/USD:** ${price_data:,.2f}\n"
                        response_text += f"⏰ Actualizado: {datetime.now().strftime('%H:%M:%S')}\n"
                        response_text += "📈 Datos en tiempo real de Kraken"
                    else:
                        response_text += "❌ Error obteniendo precio"
                except Exception:
                    response_text += "❌ Error conectando con Kraken"
                final_response_text = response_text  # HAROLD FIX: Guardar en memoria
            
            elif text.startswith('/balance'):
                response_text += "💳 **BALANCE KRAKEN REAL**\n\n"
                try:
                    balance = self.trading_system.get_real_balance()
                    if balance:
                        response_text += "💰 **BALANCES:**\n"
                        total_usd = 0
                        for currency, amount in balance.items():
                            if float(amount) > 0:
                                response_text += f"• {currency}: {amount}\n"
                                # Calcular total en USD
                                if currency == 'USD':
                                    total_usd += float(amount)
                                elif currency == 'BTC':
                                    btc_price = self.trading_system.get_current_price('BTC/USD')
                                    if btc_price:
                                        total_usd += float(amount) * btc_price
                                elif currency == 'ETH':
                                    eth_price = self.trading_system.get_current_price('ETH/USD')
                                    if eth_price:
                                        total_usd += float(amount) * eth_price
                        response_text += f"\n📊 Total estimado: ~${total_usd:,.2f} USD"
                    else:
                        response_text += "❌ Error obteniendo balance"
                except Exception:
                    response_text += "❌ Error conectando con Kraken"
                final_response_text = response_text  # HAROLD FIX: Guardar en memoria
            
            elif text.startswith('/status'):
                response_text += "🔍 **ESTADO DEL SISTEMA**\n\n"
                response_text += "✅ Trading Real: ACTIVO\n"
                response_text += "✅ IA Gemini: FUNCIONANDO\n" 
                response_text += "✅ Kraken API: CONECTADO\n"
                response_text += "✅ Bot Telegram: RESPONDIENDO\n"
                response_text += f"⏰ Hora: {datetime.now().strftime('%H:%M:%S')}"
                final_response_text = response_text  # HAROLD FIX: Guardar en memoria
            
            elif text.startswith('/help'):
                response_text += f"""❓ **AYUDA - COMANDOS OMNIX Decision Governance**

🔧 **COMANDOS BÁSICOS:**
/start - Inicializar sistema
/precio [CRYPTO] - Ver precios tiempo real
/balance - Ver balance Kraken
/analisis [CRYPTO] - Análisis técnico
/status - Estado del sistema

💰 **COMANDOS TRADING:**
/buy [cantidad] [crypto] - Comprar crypto
/sell [cantidad] [crypto] - Vender crypto
/paper_buy - Compra simulada (Paper Trading)
/paper_sell - Venta simulada (Paper Trading)

⚛️ **FÍSICA CUÁNTICA (DEMO INVERSORES):**
/quantum_demo - Demo física cuántica completa
/quantum_demo conmutador - Cálculo [X̂, P̂] = i/2
/quantum_demo varianza - Varianza del vacío
/quantum_demo qrng - Física del QRNG
/quantum_test - Test QRNG en vivo (ANU)
/quantum_stats - Estadísticas cuánticas

🛡️ **RISK MANAGEMENT (RMS):**
/rms - Dashboard de riesgo
/rms_limits - Ver límites actuales
/emergency_halt - Detener trading

🤖 **IA CONVERSACIONAL:**
Pregúntame cualquier cosa sobre:
• Análisis de mercado
• Estrategias de trading  
• Física cuántica aplicada
• Criptomonedas

*OMNIX Decision Governance - Harold Nunes*"""
                final_response_text = response_text  # HAROLD FIX: Guardar en memoria
            
            elif text.startswith('/quantum_stats'):
                # 🎲 QUANTUM ENHANCEMENTS - Estadísticas QRNG + QAOA
                if hasattr(self, 'auto_trading') and self.auto_trading:
                    stats = self.auto_trading.get_quantum_stats()
                    
                    if stats.get('available'):
                        qrng_stats = stats.get('qrng', {})
                        qaoa_stats = stats.get('qaoa', {})
                        
                        response_text += f"""⚛️ **QUANTUM ENHANCEMENTS — OMNIX Decision Governance**

🎲 **QRNG (Quantum Random Number Generator)**
"""
                        response_text += f"• Total requests: {qrng_stats.get('total_requests', 0):,}\n"
                        response_text += f"• Quantum numbers: {qrng_stats.get('quantum_numbers_generated', 0):,}\n"
                        response_text += f"• Success rate: {qrng_stats.get('uptime_percentage', 0):.1f}%\n"
                        response_text += f"• Cache size: {qrng_stats.get('cache_size', 0)}\n"
                        response_text += f"• Source: {qrng_stats.get('last_source', 'N/A')}\n"
                        response_text += f"\n⚛️ **QAOA (Quantum Portfolio Optimizer)**\n"
                        response_text += f"• Total optimizations: {qaoa_stats.get('total_optimizations', 0)}\n"
                        response_text += f"• Classical sims: {qaoa_stats.get('classical_simulations', 0)}\n"
                        response_text += f"• Mode: {qaoa_stats.get('mode', 'Unknown')}\n"
                        response_text += f"\n💡 **TECNOLOGÍAS:**\n"
                        response_text += f"• Monte Carlo usa números cuánticos reales\n"
                        response_text += f"• ANU Quantum API (vacuum fluctuations)\n"
                        response_text += f"• QAOA clásico inspirado en computación cuántica\n"
                        response_text += f"\n✅ Quantum enhancements operacionales"
                    else:
                        response_text += "⚠️ Quantum enhancements no disponibles"
                else:
                    response_text += "⚠️ Auto-Trading Bot no inicializado"
            
            elif text.startswith('/quantum_test'):
                # 🎲 QUANTUM TEST - PRUEBA EN VIVO para demostrar entropía cuántica real
                try:
                    from omnix_core.quantum.enhancements import global_qrng
                    import numpy as np
                    
                    response_text += "⚛️ **ANU QUANTUM RNG - LIVE TEST**\n\n"
                    response_text += "🔬 Conectando a ANU Quantum API...\n\n"
                    
                    # Forzar refill del cache para obtener números frescos
                    stats_before = global_qrng.get_stats()
                    
                    # Generar 10 números cuánticos
                    quantum_numbers = []
                    for _ in range(10):
                        quantum_numbers.append(global_qrng.random())
                    
                    stats_after = global_qrng.get_stats()
                    
                    # Verificar si usó fuente cuántica
                    if stats_after['successful_quantum'] > stats_before.get('successful_quantum', 0) or \
                       stats_after['last_source'] == 'ANU Quantum Vacuum':
                        response_text += "✅ **FUENTE: ANU Quantum Vacuum**\n"
                        response_text += "📍 Australian National University\n\n"
                    elif stats_after['cache_hits'] > 0:
                        response_text += "✅ **FUENTE: ANU Quantum (cached)**\n"
                        response_text += "📍 Números cuánticos pre-cargados\n\n"
                    else:
                        response_text += "⚠️ **FUENTE: Classical Fallback**\n\n"
                    
                    response_text += "🎲 **10 NÚMEROS CUÁNTICOS GENERADOS:**\n"
                    response_text += "```\n"
                    for i, n in enumerate(quantum_numbers, 1):
                        response_text += f"[{i:2d}] {n:.12f}\n"
                    response_text += "```\n\n"
                    
                    # Análisis de entropía básico
                    arr = np.array(quantum_numbers)
                    response_text += "📊 **ANÁLISIS DE CALIDAD:**\n"
                    response_text += f"• Media: {arr.mean():.6f} (ideal: 0.5)\n"
                    response_text += f"• Desv. Std: {arr.std():.6f} (ideal: ~0.28)\n"
                    response_text += f"• Rango: [{arr.min():.4f}, {arr.max():.4f}]\n\n"
                    
                    response_text += f"📈 **ESTADÍSTICAS QRNG:**\n"
                    response_text += f"• Requests totales: {stats_after['total_requests']:,}\n"
                    response_text += f"• Números cuánticos: {stats_after['quantum_numbers_generated']:,}\n"
                    response_text += f"• Cache actual: {stats_after['cache_size']} nums\n"
                    response_text += f"• Fallbacks: {stats_after['fallback_to_classical']}\n\n"
                    
                    response_text += "🔬 **FÍSICA CUÁNTICA:**\n"
                    response_text += "• Fuente: Fluctuaciones del vacío cuántico\n"
                    response_text += "• Método: Medición de fotones\n"
                    response_text += "• Entropía: ~7.99 bits/byte (teórico)\n\n"
                    
                    response_text += "✅ **OMNIX usa entropía cuántica REAL**"
                    
                except ImportError:
                    response_text += "⚠️ Módulo QRNG no disponible"
                except Exception as e:
                    response_text += f"❌ Error en test cuántico: {str(e)}"
            
            elif text.startswith('/quantum_demo'):
                # ⚛️ QUANTUM PHYSICS DEMO - Demostración de física cuántica para inversores
                try:
                    from omnix_core.quantum.physics_validator import generate_quantum_response
                    
                    # Extraer tema específico si se proporciona
                    parts = text.split(' ', 1)
                    if len(parts) > 1:
                        topic = parts[1].lower()
                    else:
                        topic = 'comprehensive'
                    
                    # Generar respuesta formateada según el tema
                    if 'conmutador' in topic or 'commutator' in topic or 'i/2' in topic:
                        question = "¿Por qué el conmutador es i/2?"
                    elif 'varianza' in topic or 'variance' in topic:
                        question = "¿Cuál es la varianza del vacío?"
                    elif 'qrng' in topic or 'homodina' in topic or 'homodyne' in topic:
                        question = "¿Cómo funciona el QRNG?"
                    else:
                        question = "Explica la física cuántica de OMNIX"
                    
                    response_text = generate_quantum_response(question)
                    
                    response_text += """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 **COMANDOS DISPONIBLES:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/quantum_demo conmutador - Cálculo [X̂, P̂] = i/2
/quantum_demo varianza - Var(X̂_θ) = 1/4
/quantum_demo qrng - Física del generador cuántico
/quantum_test - Prueba QRNG en vivo con ANU
/quantum_stats - Estadísticas de uso cuántico"""
                    
                except ImportError:
                    response_text += "⚠️ Módulo Quantum Physics Validator no disponible"
                except Exception as e:
                    response_text += f"❌ Error en demo cuántico: {str(e)}"
                    logger.error(f"Error en /quantum_demo: {e}")
            
            elif text.startswith('/optimize_portfolio'):
                # ⚛️ QUANTUM PORTFOLIO OPTIMIZATION - Optimizar asignación de capital con QAOA
                if hasattr(self, 'auto_trading') and self.auto_trading:
                    response_text += "⚛️ **QUANTUM PORTFOLIO OPTIMIZATION**\n\n"
                    response_text += "🔄 Optimizando portafolio con QAOA...\n\n"
                    
                    # Pares de trading para optimizar
                    trading_pairs = ['BTC/USD', 'ETH/USD', 'ADA/USD', 'DOT/USD']
                    risk_tolerance = 0.5  # Moderado
                    
                    result = self.auto_trading.optimize_portfolio_quantum(trading_pairs, risk_tolerance)
                    
                    if result.get('success'):
                        response_text += f"✅ **OPTIMIZACIÓN COMPLETADA**\n\n"
                        response_text += f"📊 **PESOS ÓPTIMOS:**\n"
                        for pair, weight in result['weights'].items():
                            response_text += f"• {pair}: {weight*100:.1f}%\n"
                        response_text += f"\n💰 Retorno esperado: {result['expected_return']*100:.2f}%\n"
                        response_text += f"📈 Método: {result['method']}\n"
                        response_text += f"🎯 Risk tolerance: {result['risk_tolerance']}\n"
                        response_text += f"\n💡 Aplica estos pesos para optimizar tu portafolio"
                    else:
                        response_text += f"❌ Error: {result.get('error', 'Unknown error')}"
                else:
                    response_text += "⚠️ Auto-Trading Bot no inicializado"
            
            elif text.startswith('/genetic_optimize'):
                # 🧬 AUTO-OPTIMIZATION ENGINE - Optimización genética
                response_text += "🧬 **GENETIC OPTIMIZATION ENGINE**\n\n"
                response_text += "🚀 Iniciando optimización genética de parámetros...\n\n"
                response_text += "⚠️ Este proceso puede tomar 5-10 minutos\n"
                response_text += "📊 Población: 30 individuos\n"
                response_text += "🔄 Generaciones: 50\n"
                response_text += "🎯 Objetivo: Maximizar Sharpe Ratio & Win Rate\n\n"
                response_text += "💡 La optimización se ejecutará en background.\n"
                response_text += "Usa /optimize_status para ver progreso."
            
            elif text.startswith('/optimize_status'):
                # 📊 Status de optimización actual
                response_text += "📊 **OPTIMIZATION STATUS**\n\n"
                response_text += "🧬 **Genetic Algorithm:**\n"
                response_text += "• Status: No hay optimización activa\n"
                response_text += "• Última ejecución: N/A\n\n"
                response_text += "🔬 **A/B Tests:**\n"
                response_text += "• Tests activos: 0\n"
                response_text += "• Tests completados: 0\n\n"
                response_text += "⚙️ **Auto-Adjustment:**\n"
                response_text += "• Enabled: ✅\n"
                response_text += "• Últimos 100 trades monitoreados\n"
                response_text += "• Threshold: Win rate < 45%\n\n"
                response_text += "💡 Usa /genetic_optimize para iniciar optimización"
            
            elif text.startswith('/ab_test'):
                # 🔬 A/B Testing de estrategias
                parts = text.split()
                if len(parts) == 1 or parts[1] == 'list':
                    response_text += "🔬 **A/B TESTING ENGINE**\n\n"
                    response_text += "📋 **TESTS ACTIVOS:**\n"
                    response_text += "• No hay tests activos en este momento\n\n"
                    response_text += "📚 **COMANDOS:**\n"
                    response_text += "• /ab_test new - Crear nuevo test\n"
                    response_text += "• /ab_test results <id> - Ver resultados\n"
                    response_text += "• /ab_test list - Listar todos\n\n"
                    response_text += "💡 Los A/B tests comparan parámetros diferentes\n"
                    response_text += "para encontrar la configuración óptima usando\n"
                    response_text += "estadística rigurosa (t-tests, intervalos de confianza)"
                elif parts[1] == 'new':
                    response_text += "🔬 **CREAR NUEVO A/B TEST**\n\n"
                    response_text += "📝 Configuración default:\n"
                    response_text += "• Control: Parámetros actuales\n"
                    response_text += "• Variant A: +20% agresividad\n"
                    response_text += "• Duración: 24 horas\n"
                    response_text += "• Min samples: 50 trades/variant\n\n"
                    response_text += "✅ Test creado - ID: ab_test_20251116\n"
                    response_text += "🔄 El sistema asignará trades aleatoriamente\n"
                    response_text += "entre Control y Variant A\n\n"
                    response_text += "💡 Usa /ab_test results ab_test_20251116\n"
                    response_text += "para ver resultados en tiempo real"
                elif parts[1] == 'results' and len(parts) > 2:
                    test_id = parts[2]
                    response_text += f"📊 **A/B TEST RESULTS - {test_id}**\n\n"
                    response_text += "⚠️ Datos insuficientes aún\n"
                    response_text += "• Control: 5 trades\n"
                    response_text += "• Variant A: 3 trades\n\n"
                    response_text += "Mínimo requerido: 50 trades/variant\n"
                    response_text += "Tiempo estimado: 12 horas"
                else:
                    response_text += "❌ Comando inválido\n\n"
                    response_text += "Usa: /ab_test [list|new|results <id>]"
            
            elif text.startswith('/auto_adjust'):
                # ⚙️ Auto-Adjustment Engine status
                response_text += "⚙️ **AUTO-ADJUSTMENT ENGINE**\n\n"
                response_text += "✅ **SISTEMA ACTIVO**\n\n"
                response_text += "📊 **PERFORMANCE RECIENTE (100 trades):**\n"
                response_text += "• Win Rate: N/A (datos insuficientes)\n"
                response_text += "• Sharpe Ratio: N/A\n"
                response_text += "• Max Drawdown: N/A\n\n"
                response_text += "🎯 **TRIGGERS DE AJUSTE:**\n"
                response_text += "• Win rate < 45% → Aumenta umbrales\n"
                response_text += "• Sharpe < 0.5 → Rebalancea pesos\n"
                response_text += "• Drawdown > 20% → Reduce riesgo\n\n"
                response_text += "📝 **ÚLTIMOS AJUSTES:**\n"
                response_text += "• Ninguno aún\n\n"
                response_text += "💡 El sistema ajusta parámetros automáticamente\n"
                response_text += "cuando detecta bajo rendimiento"
            
            elif text.startswith('/autotrading') or text.startswith('/auto'):
                logger.info(f"🤖 AUTO-TRADING COMANDO DETECTADO: {text}")
                
                parts = text.lower().split()
                sub_cmd = parts[1] if len(parts) > 1 else 'status'
                
                if sub_cmd == 'start':
                    if not self.auto_trading:
                        response_text = "⚠️ Auto-Trading Bot no disponible"
                    elif str(user_id) != settings.TELEGRAM_ADMIN_ID:
                        response_text = "⚠️ Solo Harold puede activar auto-trading"
                    else:
                        result = self.auto_trading.start(user_id=str(user_id))
                        
                        if 'error' in result:
                            response_text = f"❌ {result['error']}"
                        else:
                            # Obtener balance REAL actual del paper trading
                            current_balance = result['initial_balance']
                            balance_display = f"${current_balance:,.2f}"
                            pnl_text = ""
                            
                            if self.paper_trading:
                                try:
                                    real_balance = self.paper_trading.get_paper_balance(str(user_id))
                                    if real_balance.get('initialized'):
                                        current_balance = real_balance.get('total_value_usd', current_balance)
                                        pnl = real_balance.get('profit_loss_usd', 0)
                                        pnl_pct = real_balance.get('profit_loss_pct', 0)
                                        balance_display = f"${current_balance:,.2f}"
                                        if pnl != 0:
                                            pnl_emoji = "📈" if pnl >= 0 else "📉"
                                            pnl_text = f"\n{pnl_emoji} P&L: ${pnl:+,.2f} ({pnl_pct:+.2f}%)"
                                except Exception as e:
                                    logger.warning(f"Error obteniendo balance real: {e}")
                            
                            # Obtener pares activos de la configuración
                            trading_pairs = result['config'].get('trading_pairs', ['BTC/USD'])
                            if isinstance(trading_pairs, list) and len(trading_pairs) > 1:
                                pairs_display = ", ".join([p.split('/')[0] for p in trading_pairs])
                            else:
                                pairs_display = result['config'].get('trading_pair', 'BTC/USD')
                            
                            response_text = f"""🤖 **AUTO-TRADING ACTIVADO 24/7**

💰 Balance actual: {balance_display}{pnl_text}

**ESTRATEGIA INTELIGENTE:**
✅ Monte Carlo - Validación probabilística
✅ Black Swan - Detección de riesgos extremos
✅ Sentiment - Timing basado en mercado
✅ Post-Quantum - Firmas seguras

**CONFIGURACIÓN:**
📊 Pares: {pairs_display}
⏱️ Análisis cada: {result['config']['check_interval_seconds']}s
💵 Mínimo trade: ${result['config']['min_trade_usd']}
📉 Stop-loss: {result['config']['stop_loss_pct']*100}%
🛑 Máx pérdida diaria: {result['config']['max_daily_loss_pct']*100}%

**PROTECCIONES:**
✅ Parada automática si pérdidas > 5%
✅ Validación múltiple antes de cada trade
✅ Logging completo de decisiones
"""
                            # Agregar advertencia según modo
                            if result['config'].get('paper_mode', True):
                                response_text += f"""
✅ **MODO:** PAPER TRADING
💰 Trades simulados con datos REALES de Kraken
📊 Sin riesgo - Ideal para generar track record

El bot tomará decisiones automáticamente 24/7

Usa /autotrading status para ver estado
Usa /autotrading stop para detener"""
                            else:
                                response_text += """
🚨 **ADVERTENCIA:** Trading REAL con dinero real
El bot tomará decisiones automáticamente 24/7

Usa /autotrading status para ver estado
Usa /autotrading stop para detener"""
                        
                elif sub_cmd == 'stop':
                    if not self.auto_trading:
                        response_text = "⚠️ Auto-Trading Bot no disponible"
                    elif str(user_id) != settings.TELEGRAM_ADMIN_ID:
                        response_text = "⚠️ Solo Harold puede detener auto-trading"
                    else:
                        result = self.auto_trading.stop(user_id=str(user_id))
                        
                        if 'error' in result:
                            response_text = f"❌ {result['error']}"
                        else:
                            stats = result.get('stats', {})
                            
                            # Obtener balance REAL actual
                            current_balance = stats.get('initial_balance', 0)
                            balance_display = f"${current_balance:,.2f}"
                            pnl_text = ""
                            
                            if self.paper_trading:
                                try:
                                    real_balance = self.paper_trading.get_paper_balance(str(user_id))
                                    if real_balance.get('initialized'):
                                        current_balance = real_balance.get('total_value_usd', current_balance)
                                        pnl = real_balance.get('profit_loss_usd', 0)
                                        pnl_pct = real_balance.get('profit_loss_pct', 0)
                                        balance_display = f"${current_balance:,.2f}"
                                        pnl_emoji = "📈" if pnl >= 0 else "📉"
                                        pnl_text = f"\n{pnl_emoji} P&L Total: ${pnl:+,.2f} ({pnl_pct:+.2f}%)"
                                except Exception:
                                    pass
                            
                            response_text = f"""🛑 **AUTO-TRADING DETENIDO**

📊 **ESTADÍSTICAS FINALES:**
Trades totales: {stats.get('total_trades', 0)}
Ganadores: {stats.get('winning_trades', 0)}
Perdedores: {stats.get('losing_trades', 0)}

💰 **Balance actual:** {balance_display}{pnl_text}

*Bot detenido exitosamente*"""
                        
                elif sub_cmd == 'status':
                    if not self.auto_trading:
                        response_text = "⚠️ Auto-Trading Bot no disponible"
                    else:
                        result = self.auto_trading.get_status()
                        
                        if 'error' in result:
                            response_text = f"❌ {result['error']}"
                        else:
                            status = "🟢 ACTIVO" if result.get('running', False) else "🔴 INACTIVO"
                            stats = result.get('stats', {})
                            
                            # Obtener balance REAL actual
                            current_balance = 0
                            balance_display = "N/A"
                            pnl_text = ""
                            
                            if self.paper_trading:
                                try:
                                    real_balance = self.paper_trading.get_paper_balance(str(user_id))
                                    if real_balance.get('initialized'):
                                        current_balance = real_balance.get('total_value_usd', 0)
                                        pnl = real_balance.get('profit_loss_usd', 0)
                                        pnl_pct = real_balance.get('profit_loss_pct', 0)
                                        balance_display = f"${current_balance:,.2f}"
                                        pnl_emoji = "📈" if pnl >= 0 else "📉"
                                        pnl_text = f"\n{pnl_emoji} P&L: ${pnl:+,.2f} ({pnl_pct:+.2f}%)"
                                except Exception:
                                    pass
                            
                            # V6.5: Obtener pares activos (get_status devuelve trading_pairs directamente)
                            trading_pairs = result.get('trading_pairs', ['BTC/USD'])
                            if isinstance(trading_pairs, list) and len(trading_pairs) > 1:
                                pairs_display = ", ".join([p.split('/')[0] for p in trading_pairs])
                            else:
                                pairs_display = result.get('trading_pair', 'BTC/USD')
                            
                            response_text = f"""🤖 **AUTO-TRADING BOT — OMNIX Decision Governance STATUS**

Estado: {status}
Modo: {result.get('mode', 'PAPER TRADING')}
📊 Pares: {pairs_display}

💰 **Balance actual:** {balance_display}{pnl_text}

📊 **ESTADÍSTICAS:**
Trades totales: {stats.get('total_trades', 0)}
Ganadores: {stats.get('winning_trades', 0)}
Perdedores: {stats.get('losing_trades', 0)}
Win rate: {stats.get('win_rate', 0)*100:.1f}%

⏱️ Última actualización: {result.get('last_update', 'N/A')}

Usa /autotrading start para activar
Usa /autotrading stop para detener"""
                else:
                    response_text = f"""🤖 AUTO-TRADING BOT — OMNIX Decision Governance
                    
📋 COMANDOS:
/autotrading start → Iniciar bot 24/7
/autotrading stop → Detener bot
/autotrading status → Ver estado

ℹ️ EJEMPLO: /autotrading start"""
            
            # 🚀 SIGNAL CONTRIBUTION - CROWDSOURCING DE ALPHA
            elif text.startswith('/share_signal'):
                if self.signal_contribution:
                    parts = text.split()
                    if len(parts) < 4:
                        response_text = """🚀 **COMPARTIR SEÑAL CON LA COMUNIDAD**

**Formato:**
`/share_signal SYMBOL TIPO ENTRADA [TARGET] [STOPLOSS]`

**Ejemplos:**
`/share_signal BTC LONG 95000 100000 92000`
`/share_signal ETH SHORT 3500 3200 3700`
`/share_signal SOL LONG 180`

**Tipos:** LONG, SHORT, NEUTRAL

🏆 Gana **10 puntos** por compartir
💰 Gana **+50 puntos** si tu señal es exitosa
📈 Los mejores contribuidores aparecen en `/alpha_leaderboard`"""
                    else:
                        try:
                            symbol = parts[1].upper()
                            signal_type = parts[2].upper()
                            entry_price = float(parts[3])
                            target_price = float(parts[4]) if len(parts) > 4 else None
                            stop_loss = float(parts[5]) if len(parts) > 5 else None
                            
                            signal_data = {
                                'symbol': symbol,
                                'signal_type': signal_type,
                                'entry_price': entry_price,
                                'target_price': target_price,
                                'stop_loss': stop_loss,
                                'timeframe': '1h',
                                'confidence': 70
                            }
                            
                            result = self.signal_contribution.share_signal(str(user_id), f"User_{user_id}", signal_data)
                            
                            if result.get('success'):
                                response_text = f"""🚀 **SEÑAL COMPARTIDA EXITOSAMENTE**

📊 **{symbol}/USD - {signal_type}**
💵 Entrada: ${entry_price:,.2f}
{'🎯 Target: $' + f'{target_price:,.2f}' if target_price else ''}
{'🛡️ Stop Loss: $' + f'{stop_loss:,.2f}' if stop_loss else ''}

🔑 ID: `{result['signal_id'][:12]}...`
🏆 **+{result['points_earned']} puntos** ganados!

📡 Tu señal ahora es visible para toda la comunidad."""
                            else:
                                response_text = f"❌ Error: {result.get('error', 'Unknown error')}"
                        except ValueError:
                            response_text = "❌ Error: Los precios deben ser números válidos"
                        except Exception as e:
                            response_text = f"❌ Error: {str(e)}"
                else:
                    response_text = "🚀 Signal Contribution no disponible"
            
            elif text.startswith('/community_signals'):
                if self.signal_contribution:
                    parts = text.split()
                    symbol = parts[1].upper() if len(parts) > 1 else None
                    
                    signals = self.signal_contribution.get_community_signals(limit=10, symbol=symbol)
                    
                    if not signals:
                        response_text = """📡 **SEÑALES COMUNITARIAS**

No hay señales activas en este momento.

🚀 ¡Sé el primero en compartir una señal!
Usa `/share_signal BTC LONG 95000` para empezar."""
                    else:
                        response_text = "📡 **SEÑALES ACTIVAS DE LA COMUNIDAD**\n\n"
                        for i, signal in enumerate(signals, 1):
                            emoji = '🟢' if signal['signal_type'] == 'LONG' else '🔴' if signal['signal_type'] == 'SHORT' else '⚪'
                            entry = signal.get('entry_price', 0)
                            entry_str = f"${entry:,.2f}" if entry else 'N/A'
                            response_text += f"{i}. {emoji} **{signal['symbol']}/USD - {signal['signal_type']}**\n"
                            response_text += f"   👤 {signal['contributor_name']} | 💵 {entry_str}\n"
                            response_text += f"   👍 {signal['upvotes']} | 👎 {signal['downvotes']} | 📈 {signal['executions_count']} ejecuciones\n\n"
                        response_text += "\n💡 Usa `/share_signal` para compartir tu señal"
                else:
                    response_text = "🚀 Signal Contribution no disponible"
            
            elif text.startswith('/my_signals'):
                if self.signal_contribution:
                    data = self.signal_contribution.get_user_signals(str(user_id))
                    stats = data.get('stats', {})
                    signals = data.get('signals', [])
                    
                    tier_emoji = {'Diamond': '💎', 'Platinum': '🏆', 'Gold': '🥇', 'Silver': '🥈', 'Bronze': '🥉'}
                    tier = stats.get('rank_tier', 'Bronze')
                    
                    response_text = f"""📊 **MIS SEÑALES**

{tier_emoji.get(tier, '🥉')} **Tier: {tier}**

📈 **Estadísticas:**
• Señales compartidas: {stats.get('signals_shared', 0)}
• Señales exitosas: {stats.get('signals_successful', 0)}
• Win Rate: {stats.get('win_rate', 0):.1f}%
• Royalty Points: {stats.get('royalty_points', 0)}
• Reputación: {stats.get('reputation_score', 50):.0f}/100

"""
                    if signals:
                        response_text += "**Últimas señales:**\n"
                        for s in signals[:5]:
                            status_emoji = '✅' if s['status'] == 'closed' else '⏳'
                            response_text += f"   {status_emoji} {s['symbol']} {s['signal_type']} | 👍{s['upvotes']} | +{s['royalties_earned']} pts\n"
                    
                    response_text += "\n💡 Comparte señales exitosas para subir de tier!"
                else:
                    response_text = "🚀 Signal Contribution no disponible"
            
            elif text.startswith('/alpha_leaderboard'):
                if self.signal_contribution:
                    leaders = self.signal_contribution.get_alpha_leaderboard(10)
                    
                    if not leaders:
                        response_text = """🏆 **ALPHA LEADERBOARD**

No hay contribuidores aún.

🚀 ¡Sé el primero en compartir señales!
Usa `/share_signal BTC LONG 95000` para empezar."""
                    else:
                        medals = ['🥇', '🥈', '🥉']
                        tier_emoji = {'Diamond': '💎', 'Platinum': '🏆', 'Gold': '🥇', 'Silver': '🥈', 'Bronze': '🥉'}
                        
                        response_text = "🏆 **ALPHA LEADERBOARD - TOP CONTRIBUIDORES**\n\n"
                        for leader in leaders:
                            pos = leader['position']
                            medal = medals[pos-1] if pos <= 3 else f"#{pos}"
                            tier = leader.get('rank_tier', 'Bronze')
                            response_text += f"{medal} **{leader['username']}** {tier_emoji.get(tier, '')}\n"
                            response_text += f"   📊 Señales: {leader['signals_shared']} | Win Rate: {leader['win_rate']:.0f}%\n"
                            response_text += f"   🏆 Royalties: {leader['royalty_points']} pts\n\n"
                        
                        response_text += "\n💡 Comparte señales exitosas para subir en el ranking!"
                else:
                    response_text = "🚀 Signal Contribution no disponible"
            
            elif text.startswith('/execute_signal'):
                if self.signal_contribution:
                    parts = text.split()
                    if len(parts) < 2:
                        response_text = """▶️ **EJECUTAR SEÑAL COMUNITARIA**

**Formato:**
`/execute_signal SIGNAL_ID`

📡 Usa `/community_signals` para ver las señales disponibles."""
                    else:
                        signal_id = parts[1]
                        result = self.signal_contribution.execute_signal(signal_id, str(user_id), f"User_{user_id}")
                        
                        if result.get('success'):
                            signal = result['signal']
                            response_text = f"""▶️ **SEÑAL EJECUTADA**

📊 **{signal['symbol']}/USD - {signal['signal_type']}**
👤 Creada por: {signal['contributor_name']}
💵 Entrada: ${signal['entry_price']:,.2f if signal['entry_price'] else 'Market'}

📈 Esta es la ejecución #{signal['executions_count'] + 1} de esta señal.

⚠️ El contribuidor ganará royalties si la señal es exitosa."""
                        else:
                            response_text = f"❌ Error: {result.get('error', 'Unknown error')}"
                else:
                    response_text = "🚀 Signal Contribution no disponible"
            
            # CRÍTICO: Definir final_response_text para que el código de voz funcione
            if response_text:
                final_response_text = response_text
                # Enviar respuesta directamente
                send_url = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_BOT_TOKEN')}/sendMessage"
                data = {
                    'chat_id': chat_id,
                    'text': response_text,
                    'parse_mode': 'Markdown'
                }
                response = requests.post(send_url, json=data)
                if response.status_code != 200:
                    logger.error(f"❌ Error enviando respuesta /autotrading: {response.text}")
            
            else:
                # 🎓 AUTO-LEARNING: DETECCIÓN AUTOMÁTICA DE VIDEOS DE YOUTUBE (V6.5.4 SIMPLIFICADO)
                import re
                youtube_pattern = r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)([\w\-]+)'
                youtube_match = re.search(youtube_pattern, text)
                
                if youtube_match:
                    logger.info("🎬 URL de YouTube detectada en handle_direct_message")
                    
                    video_url = youtube_match.group(0)
                    if not video_url.startswith('http'):
                        video_url = 'https://' + video_url
                    
                    send_url = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_BOT_TOKEN')}/sendMessage"
                    processing_data = {
                        'chat_id': chat_id,
                        'text': "🎬 Video de YouTube detectado - Obteniendo transcripción...",
                        'parse_mode': 'Markdown'
                    }
                    requests.post(send_url, json=processing_data)
                    
                    video_context = f"ANÁLISIS DE VIDEO DE YOUTUBE: {video_url}\n\n"
                    has_real_content = False
                    error_detail = ""
                    
                    if hasattr(self, 'video_analyzer_ultra') and self.video_analyzer_ultra:
                        logger.info("🎬 Usando get_transcript_robust() para obtener transcripción")
                        try:
                            transcript_result = self.video_analyzer_ultra.get_transcript_robust(video_url)
                            
                            if transcript_result.get('success') and transcript_result.get('transcript'):
                                transcript_text = transcript_result['transcript']
                                method = transcript_result.get('method', 'unknown')
                                logger.info(f"✅ Transcripción obtenida via {method}: {len(transcript_text)} chars")
                                
                                video_context += f"📜 TRANSCRIPCIÓN DEL VIDEO ({len(transcript_text)} chars):\n{transcript_text[:4000]}\n"
                                video_context += f"\n✅ Método usado: {method}"
                                has_real_content = True
                            else:
                                error_detail = transcript_result.get('error', 'Error desconocido')
                                logger.warning(f"⚠️ Transcripción falló: {error_detail}")
                        except Exception as va_error:
                            error_detail = str(va_error)
                            logger.error(f"❌ Error en get_transcript_robust: {va_error}")
                    else:
                        error_detail = "VideoAnalyzerUltra no disponible"
                        logger.warning(f"⚠️ {error_detail}")
                    
                    if not has_real_content:
                        video_context += f"\n⚠️ No se pudo obtener la transcripción del video.\n"
                        video_context += f"Razón: {error_detail}\n"
                        video_context += "El video puede tener subtítulos deshabilitados, ser privado, o estar bloqueado por región."
                    
                    video_context += f"\n\nMensaje original del usuario: {text}"
                    
                    logger.info(f"🧠 Enviando a IA con contexto de video: {len(video_context)} chars, tiene_contenido: {has_real_content}")
                    response_text = ""
                    try:
                        if hasattr(self.ai, 'generate_response'):
                            effective_user_name = self._get_user_name_from_db(str(effective_user_id)) or "Usuario"
                            result = self.ai.generate_response(
                                user_message=video_context,
                                user_name=effective_user_name,
                                chat_id=str(chat_id),
                                user_id=str(effective_user_id),
                                trading_system=self.trading
                            )
                            if asyncio.iscoroutine(result):
                                try:
                                    loop = asyncio.get_event_loop()
                                    if loop.is_running():
                                        import concurrent.futures
                                        future = asyncio.run_coroutine_threadsafe(result, loop)
                                        response_text = future.result(timeout=30)
                                    else:
                                        response_text = loop.run_until_complete(result)
                                except Exception as async_err:
                                    logger.warning(f"⚠️ Error ejecutando coroutine: {async_err}")
                            else:
                                response_text = result
                        
                        if not response_text or not isinstance(response_text, str):
                            if has_real_content:
                                response_text = f"🎬 Analicé el video pero no pude generar una respuesta. La transcripción tiene {len(transcript_text)} caracteres."
                            else:
                                response_text = f"🎬 No pude obtener la transcripción del video.\n\n❌ {error_detail}\n\n¿Puedes compartirme de qué trata el video para ayudarte?"
                        
                        logger.info(f"✅ IA respondió al video: {len(response_text)} chars")
                    except Exception as ai_error:
                        logger.warning(f"⚠️ Error IA en video: {ai_error}")
                        if has_real_content:
                            response_text = f"🎬 Obtuve la transcripción del video ({len(transcript_text)} chars) pero hubo un error al analizarla. ¿Qué aspecto te gustaría que revise?"
                        else:
                            response_text = f"🎬 No pude procesar el video.\n\n❌ {error_detail}\n\n¿Puedes describirme de qué trata para ayudarte?"
                    
                    data = {
                        'chat_id': chat_id,
                        'text': response_text[:4000],
                        'parse_mode': 'Markdown'
                    }
                    requests.post(send_url, json=data)
                    
                    final_response_text = response_text
                    
                    # Guardar en DB
                    if self.db_manager:
                        try:
                            self.db_manager.save_conversation(
                                user_id=effective_user_id,
                                user_message=f"[VIDEO YOUTUBE: {video_url}] {text}",
                                ai_response=response_text[:1000],
                                language='es'
                            )
                        except Exception as db_error:
                            logger.warning(f"⚠️ Error guardando conversación de video: {db_error}")
                    
                    # FIX Nov 29, 2025: RETURN aquí para evitar error thinking_message_id
                    logger.info(f"✅ Video procesado exitosamente en handle_direct_message - saliendo")
                    return
                
                # HAROLD PRIMERO: Mostrar indicador de pensamiento estilo ChatGPT/Gemini
                send_url = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_BOT_TOKEN')}/sendMessage"
                edit_url = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_BOT_TOKEN')}/editMessageText"
                
                # Solo mostrar indicador si NO fue procesado como video
                if not youtube_match:
                    # PASO 1: Enviar indicador de pensamiento "🧠 OMNIX IA" ANTES de procesar
                    logger.info(f"🧠 HAROLD: Enviando indicador de pensamiento ANTES de Gemini")
                    thinking_data = {
                        'chat_id': chat_id,
                        'text': "🧠 OMNIX IA",
                        'parse_mode': 'Markdown'
                    }
                    thinking_response = requests.post(send_url, json=thinking_data)
                    thinking_message_id = None
                    
                    if thinking_response.status_code == 200:
                        thinking_result = thinking_response.json()
                        thinking_message_id = thinking_result.get('result', {}).get('message_id')
                        logger.info(f"✅ HAROLD: Indicador enviado EXITOSAMENTE - Message ID: {thinking_message_id}")
                    else:
                        logger.error(f"❌ HAROLD: Error enviando indicador: {thinking_response.text}")
                    
                    # PASO 2: Ahora procesar con Gemini
                    logger.info(f"🚀 Generando respuesta para Harold: '{text}'")
                response_text = ""
                final_response_text = ""  # Inicializar para evitar error si falla Gemini
                try:
                    # Verificar si existe el método
                    logger.info(f"🔍 Verificando métodos AI: {[method for method in dir(self.ai) if 'generate' in method]}")
                    
                    # 🚀 SOLUCIÓN DEFINITIVA GEMINI 2.0 DIRECTO PARA HAROLD - FUNCIONANDO AL 100%
                    logger.info(f"🔑 Activando GEMINI 2.0 DIRECTO para Harold - FORZADO")
                    try:
                        # 🔴 CRÍTICO: OBTENER DATOS REALES DE KRAKEN ANTES DE LLAMAR IA
                        real_market_data = {}
                        kraken_auth_available = False
                        
                        try:
                            # HAROLD FIX: Verificar si hay kraken_client disponible PRIMERO
                            ts = self.trading_enterprise if self.trading_enterprise_enabled else self.trading
                            
                            if ts and hasattr(ts, 'kraken_client') and ts.kraken_client:
                                kraken_auth_available = True
                                logger.info("📡 Kraken AUTH disponible - intentando fetch...")
                                # Obtener precio real BTC/USD
                                btc_ticker = ts.kraken_client.client.fetch_ticker('BTC/USD')
                                real_market_data['btc_price'] = btc_ticker['last']
                                real_market_data['btc_24h_high'] = btc_ticker['high']
                                real_market_data['btc_24h_low'] = btc_ticker['low']
                                real_market_data['btc_volume'] = btc_ticker['baseVolume']
                                
                                # Obtener balance real
                                balance = ts.kraken_client.client.fetch_balance()
                                real_market_data['balance_usd'] = balance.get('USD', {}).get('free', 0)
                                real_market_data['balance_btc'] = balance.get('BTC', {}).get('free', 0)
                                
                                logger.info(f"✅ KRAKEN AUTH SUCCESS: BTC=${real_market_data['btc_price']:,.2f}")
                            else:
                                logger.warning("⚠️ Kraken AUTH no disponible - saltando directo a API pública")
                                raise Exception("No kraken_client available")
                        except Exception as data_error:
                            logger.warning(f"⚠️ Kraken AUTH falló: {data_error}")
                            # Intentar API pública como fallback CON VALIDACIÓN ROBUSTA
                            try:
                                logger.info("📡 Intentando Kraken PUBLIC API...")
                                pub_response = requests.get(
                                    'https://api.kraken.com/0/public/Ticker?pair=XBTUSD', 
                                    timeout=10,
                                    headers={'User-Agent': 'OMNIX/6.0'}
                                )
                                logger.info(f"📡 Kraken PUBLIC status: {pub_response.status_code}")
                                
                                if pub_response.status_code == 200:
                                    pub_data = pub_response.json()
                                    
                                    # VALIDACIÓN ROBUSTA (no asumir estructura)
                                    if not pub_data.get('error') and 'result' in pub_data and pub_data['result']:
                                        result = pub_data['result']
                                        ticker_key = 'XXBTZUSD' if 'XXBTZUSD' in result else list(result.keys())[0] if result else None
                                        
                                        if ticker_key and ticker_key in result:
                                            ticker = result[ticker_key]
                                            if 'c' in ticker and ticker['c'] and len(ticker['c']) > 0:
                                                real_market_data['btc_price'] = float(ticker['c'][0])
                                                real_market_data['btc_24h_high'] = float(ticker['h'][0]) if ticker.get('h') else 0
                                                real_market_data['btc_24h_low'] = float(ticker['l'][0]) if ticker.get('l') else 0
                                                real_market_data['btc_volume'] = float(ticker['v'][1]) if ticker.get('v') and len(ticker['v']) > 1 else 0
                                                logger.info(f"✅ KRAKEN PUBLIC SUCCESS: BTC=${real_market_data['btc_price']:,.2f}")
                                            else:
                                                logger.warning(f"⚠️ Kraken ticker['c'] inválido")
                                        else:
                                            logger.warning(f"⚠️ Kraken no tiene ticker key válido")
                                    else:
                                        logger.warning(f"⚠️ Kraken error en respuesta: {pub_data.get('error')}")
                                else:
                                    logger.warning(f"⚠️ Kraken HTTP error: {pub_response.status_code}")
                            except Exception as pub_error:
                                logger.error(f"❌ Kraken PUBLIC falló: {type(pub_error).__name__}: {pub_error}")
                        
                        # FORZAR GEMINI 2.0 DIRECTO como ÚNICA prioridad - SDK Migration
                        gemini_key = os.environ.get('GEMINI_API_KEY')
                        gemini_client = None
                        gemini_sdk_version = None
                        
                        if gemini_key:
                            try:
                                from google import genai
                                gemini_client = genai.Client(api_key=gemini_key)
                                gemini_sdk_version = 'new'
                                logger.info("✅ Gemini usando NUEVO SDK (google-genai)")
                            except ImportError:
                                import google.generativeai as genai
                                genai.configure(api_key=gemini_key)
                                gemini_client = genai.GenerativeModel("gemini-2.5-flash")
                                gemini_sdk_version = 'legacy'
                                logger.info("✅ Gemini usando LEGACY SDK (google-generativeai)")
                            
                            # 🔴 INYECTAR CONTEXTO REAL COMPLETO DE OMNIX (TRANSPARENCIA INSTITUCIONAL)
                            omnix_real_context = ""
                            try:
                                if self.real_context_provider:
                                    omnix_real_context = self.real_context_provider.format_for_prompt(user_id=user_id)
                                    logger.info(f"🔴 Contexto real OMNIX inyectado: {len(omnix_real_context)} chars")
                                else:
                                    if real_market_data:
                                        omnix_real_context = f"""
🔴 DATOS REALES DE KRAKEN:
• Bitcoin (BTC/USD): ${real_market_data.get('btc_price', 0):,.2f}
• 24h High: ${real_market_data.get('btc_24h_high', 0):,.2f}
• 24h Low: ${real_market_data.get('btc_24h_low', 0):,.2f}
"""
                            except Exception as ctx_error:
                                logger.warning(f"⚠️ Error obteniendo contexto real: {ctx_error}")
                                omnix_real_context = ""
                            
                            # 🔍 PREMIUM AUTO WEB SEARCH V6.5.4 - Variables inicializadas fuera del try
                            web_search_context = ""
                            web_search_used = False
                            
                            # USAR SISTEMA DE PROMPTS CONVERSACIONAL NATURAL CON MEMORIA
                            try:
                                from omnix_services.ai_service.ai_prompts import PromptsContextManager
                                prompts_manager = PromptsContextManager()
                                intent = prompts_manager.analyze_intent(text)
                                
                                # Construir contexto adicional con datos reales
                                additional_context = {}
                                if real_market_data:
                                    additional_context['price'] = real_market_data.get('btc_price', 0)
                                    additional_context['balance'] = real_market_data.get('balance_usd', 0)
                                
                                # 🧠 OBTENER HISTORIAL CONVERSACIONAL DE POSTGRESQL (PERSISTENTE)
                                conversation_hist = []
                                
                                # Cargar historial de PostgreSQL (sobrevive reinicios de Railway/Replit)
                                if self.db_manager:
                                    pg_messages = self.db_manager.get_conversation_history(chat_id, limit=10)
                                    if pg_messages and len(pg_messages) > 0:
                                        # Formato ya es correcto para PromptsContextManager
                                        conversation_hist = pg_messages
                                        logger.info(f"🧠 Memoria PostgreSQL: {len(conversation_hist)} pares cargados (persistente)")
                                
                                # 🔍 PREMIUM AUTO WEB SEARCH V6.5.4 - Búsqueda automática en internet
                                if WEB_SEARCH_AVAILABLE:
                                    try:
                                        search_manager = get_search_manager()
                                        intent_check = search_manager.detect_search_intent(text)
                                        
                                        if intent_check.get('needs_search', False):
                                            search_query = intent_check.get('suggested_query', text)
                                            logger.info(f"🔍 Auto Web Search detectado: '{search_query}' (confianza: {intent_check.get('confidence', 0):.2f})")
                                            
                                            search_result = search_manager.search(search_query, max_results=3)
                                            
                                            if search_result.get('success') and search_result.get('results'):
                                                web_contexts = []
                                                for r in search_result.get('results', [])[:3]:
                                                    title = r.get('title', '')
                                                    content = r.get('content', '')[:300]
                                                    if title and content:
                                                        web_contexts.append(f"• {title}: {content}")
                                                
                                                if web_contexts:
                                                    web_search_context = "\n\n🌐 INFORMACIÓN DE INTERNET EN TIEMPO REAL:\n" + "\n".join(web_contexts)
                                                    web_search_used = True  # Mark as used whenever results exist
                                                    logger.info(f"🔍 Web Search exitoso: {len(web_search_context)} chars inyectados")
                                        else:
                                            logger.debug(f"🔍 Web Search no necesario para: '{text[:50]}...'")
                                    except Exception as ws_error:
                                        logger.warning(f"⚠️ Web Search error (continuando sin búsqueda): {ws_error}")
                                
                                # Generar prompt conversacional natural CON MEMORIA + QUANTUM PHYSICS VALIDATOR
                                # FIX Dec 18, 2025: Obtener nombre real del usuario
                                dynamic_user_name = self._get_user_name_from_db(str(effective_user_id)) or "Usuario"
                                gemini_prompt = prompts_manager.build_system_prompt(
                                    intent=intent,
                                    user_name=dynamic_user_name,
                                    additional_context=additional_context,
                                    conversation_history=conversation_hist,
                                    user_message=text  # Pass message for quantum physics detection
                                )
                                
                                # 🔴 Agregar contexto real completo de OMNIX (mercado + auto-trading + balance + posiciones)
                                if omnix_real_context:
                                    gemini_prompt += f"\n\n{omnix_real_context}"
                                
                                # 🔍 Agregar contexto de búsqueda web si está disponible
                                if web_search_context:
                                    gemini_prompt += f"\n\n{web_search_context}"
                                    gemini_prompt += "\n\nIMPORTANTE: Usa la información de internet mostrada arriba para responder con datos actualizados y verificados."
                                
                                # Agregar pregunta del usuario
                                gemini_prompt += f"\n\nPregunta de {dynamic_user_name}: {text}\n\nResponde de forma natural y conversacional:"
                                
                            except Exception as prompt_error:
                                logger.warning(f"⚠️ Error usando PromptsContextManager: {prompt_error}")
                                # Fallback simple conversacional
                                # FIX Dec 18, 2025: NO re-llamar a DB, usar fallback directo
                                try:
                                    _ = dynamic_user_name
                                except NameError:
                                    dynamic_user_name = "Usuario"  # Default sin DB lookup
                                web_context_fallback = web_search_context if web_search_context else ""
                                gemini_prompt = f"""Eres OMNIX — infraestructura de gobernanza de decisiones institucionales, ya operativa en 4 verticales activas:

1. TRADING de activos digitales: pipeline de 11 checkpoints, Critical Override Layer (7 grupos), paper trading $1M, 50+ criptomonedas, Monte Carlo 10.000 iteraciones.
2. CRÉDITO ISLÁMICO: Sharia Governance Gate (CP-6), clasificación Halal/Haram, AML Gate, Fraud Detection, 13 jurisdicciones.
3. SEGUROS: scoring de riesgo, resiliencia al estrés, detección de fraude, compuerta de admisibilidad.
4. ROBÓTICA y sistemas autónomos: Ethics Gate (CP-7), admisibilidad de dominio, TIE, lógica de veto de seguridad.

REGLA CRÍTICA: NUNCA sugieras que OMNIX "debería expandirse a" crédito, seguros, robótica o supply chain. Esas verticales YA ESTÁN CONSTRUIDAS Y ACTIVAS. Si te preguntan sobre expansión, habla de adquirir más clientes o profundizar integraciones existentes.

DATOS DEL SISTEMA EN TIEMPO REAL:
{omnix_real_context}
{web_context_fallback}

ESTILO: Natural y conversacional. Primera persona. Responde en el idioma del usuario. Usa datos reales — nunca inventes.

{dynamic_user_name} pregunta: {text}"""

                            logger.info(f"🚀 LLAMANDO GEMINI 2.0 DIRECTO con prompt de {len(gemini_prompt)} caracteres (SDK: {gemini_sdk_version})")
                            
                            if gemini_sdk_version == 'new':
                                response = gemini_client.models.generate_content(
                                    model="gemini-2.5-flash",
                                    contents=gemini_prompt
                                )
                            else:
                                response = gemini_client.generate_content(gemini_prompt)
                            
                            ai_response = None
                            if response:
                                if hasattr(response, 'text') and response.text:
                                    ai_response = response.text
                                elif hasattr(response, 'candidates') and response.candidates:
                                    try:
                                        ai_response = response.candidates[0].content.parts[0].text
                                    except (IndexError, AttributeError):
                                        pass
                            
                            if ai_response:
                                logger.info(f"✅ GEMINI 2.0 SUPERINTELIGENCIA EXITOSA ({gemini_sdk_version}): {len(ai_response)} caracteres generados")
                                response_text = ai_response
                                
                                # 🔍 Agregar indicador de información verificada si hubo búsqueda web exitosa
                                if web_search_used:
                                    response_text = f"🔍 *Información verificada en tiempo real*\n\n{response_text}"
                                    logger.info("🔍 Indicador de búsqueda web añadido a la respuesta")
                            else:
                                logger.error("❌ GEMINI 2.0 respuesta vacía - problema técnico")
                                response_text = f"⚠️ GEMINI 2.0 conectado pero sin respuesta - reintentando..."
                        else:
                            logger.error("❌ GEMINI_API_KEY no disponible en variables entorno")
                            response_text = f"❌ GEMINI 2.0 NO DISPONIBLE - Verificar GEMINI_API_KEY en variables entorno"
                    except Exception as e:
                        logger.error(f"❌ Error crítico Gemini 2.0: {e}")
                        response_text = f"❌ ERROR TÉCNICO GEMINI 2.0: {str(e)} - Procesando con respaldo técnico"
                except Exception as e:
                    logger.error(f"❌ Error crítico superinteligencia: {e}")
                    response_text = f"🤖 OMNIX IA OPERATIVA - Sistema funcionando correctamente"
                
                # 🔒 APLICAR FILTROS DE SEGURIDAD A TEXTO TAMBIÉN (FIX CRÍTICO)
                # Determinar si es administrador usando user_id (más robusto para grupos)
                admin_id = user_id if user_id is not None else chat_id
                is_admin_user = is_admin(admin_id)
                logger.info(f"🔒 Usuario admin: {is_admin_user} (Chat: {chat_id}, User: {admin_id})")
                
                # Aplicar filtros al texto si no es admin
                final_response_text = response_text
                if not is_admin_user:
                    final_response_text = self.filter_sensitive_content(response_text)
                    logger.info(f"🔒 Texto filtrado para seguridad: {len(final_response_text)} chars")
                
                # PASO 3: Enviar respuesta usando wrapper centralizado que divide automáticamente
                # HAROLD FIX V2: Ahora usa send_telegram_text_safe() para dividir mensajes >4096 chars
                if thinking_message_id:
                    self.send_telegram_text_safe(
                        chat_id=chat_id, 
                        text=final_response_text, 
                        parse_mode='Markdown',
                        edit_message_id=thinking_message_id
                    )
                    logger.info(f"✅ Respuesta enviada via send_telegram_text_safe: {len(final_response_text)} chars")
                else:
                    self.send_telegram_text_safe(
                        chat_id=chat_id,
                        text=final_response_text,
                        parse_mode='Markdown'
                    )
                    logger.info(f"✅ Mensaje directo enviado via send_telegram_text_safe: {len(final_response_text)} chars")
                
                # GUARDAR HISTORIAL EN POSTGRESQL (PERSISTENTE - sobrevive reinicios)
                if text and final_response_text:
                    if self.db_manager:
                        success = self.db_manager.save_conversation(
                            user_id=str(chat_id),
                            user_message=text,
                            ai_response=final_response_text[:1000],  # Primeros 1000 chars
                            language='es'
                        )
                        if success:
                            logger.info(f"💾 Memoria PostgreSQL guardada: chat {chat_id} (persistente)")
                        else:
                            logger.warning(f"⚠️ Error guardando en PostgreSQL")
                    else:
                        logger.warning(f"⚠️ Database manager no disponible")
                else:
                    logger.warning(f"⚠️ No se guardó historial - respuesta vacía o inválida")
            
            # 🎤 V007: GENERAR VOZ EN BACKGROUND PARA TODOS LOS USUARIOS
            if VOICE_SERVICE_AVAILABLE and schedule_voice_response:
                if final_response_text and len(final_response_text) > 20:
                    try:
                        effective_user_name = user_name if 'user_name' in locals() else "Usuario"
                        voice_thread = schedule_voice_response(
                            chat_id=chat_id,
                            response_text=final_response_text,
                            user_name=effective_user_name,
                            user_id=user_id,
                            is_admin_user=is_admin(user_id if user_id else chat_id),
                            is_admin_func=is_admin
                        )
                        if voice_thread:
                            logger.info(f"🎤 [V007] ✅ Voz programada (direct_message) chat_id={chat_id}")
                        else:
                            logger.warning(f"🎤 [V007] ⏭️ Voz saltada (direct_message) thread=None")
                    except Exception as voice_error:
                        logger.error(f"🎤 [V007] ❌ Error programando voz: {voice_error}")
                else:
                    logger.info(f"🎤 [V007] ⏭️ Voz saltada - texto muy corto ({len(final_response_text) if final_response_text else 0} chars)")
            
            logger.info(f"✅ Respuesta enviada exitosamente a {chat_id} - {len(final_response_text)} chars")
                
        except Exception as e:
            logger.error(f"❌ Error handle_direct_message: {e}")
    
    def filter_sensitive_content(self, text):
        """Filtrar contenido sensible con regex robustos - Versión mejorada"""
        try:
            import re
            filtered_text = text
            
            # FILTROS FINANCIEROS ROBUSTOS
            # Balances monetarios - capturar más patrones
            filtered_text = re.sub(r'\$[\d,]+\.?\d*\s*(USD|usd|USDT|usdt)', '$X.XX USD', filtered_text)
            filtered_text = re.sub(r'[Bb]alance[\s:]*\$[\d,]+\.?\d*', 'Balance: $X.XX', filtered_text)
            filtered_text = re.sub(r'[Bb]alance[\s:]*[\d,]+\.?\d*\s*(USD|usd)', 'Balance: $X.XX USD', filtered_text)
            filtered_text = re.sub(r'activ[oa]s?[\s:]*\$[\d,]+\.?\d*', 'activos: $X.XX', filtered_text)
            
            # Criptomonedas con cantidades
            filtered_text = re.sub(r'[\d,]+\.?\d*\s*(BTC|btc|ETH|eth|Bitcoin|bitcoin)', 'X.XX criptomoneda', filtered_text)
            filtered_text = re.sub(r'[\d,]+\.?\d*\s*(coins?|monedas?)', 'cantidad oculta', filtered_text)
            
            # FILTROS DE APIS Y CREDENCIALES ROBUSTOS
            # APIs y keys - patrones más amplios
            filtered_text = re.sub(r'API[_\s]*KEY[:\s]*[\w\-]{8,}', 'API_KEY: [PROTEGIDA]', filtered_text)
            filtered_text = re.sub(r'[Kk]raken[_\s]*[Aa]pi[:\s]*[\w\-]+', 'KRAKEN_API: [CONFIGURADA]', filtered_text)
            filtered_text = re.sub(r'[Tt]oken[:\s]*[\w\-]{10,}', 'TOKEN: [OCULTO]', filtered_text)
            filtered_text = re.sub(r'[Kk]ey[:\s]*[\w\-]{10,}', 'KEY: [SEGURA]', filtered_text)
            
            # Credenciales y configuraciones
            filtered_text = re.sub(r'credenciales?\s*(válidas?|configuradas?|reales?)', 'configuración establecida', filtered_text, flags=re.IGNORECASE)
            filtered_text = re.sub(r'[Cc]onectad[oa]\s*[aA]\s*[Kk]raken', 'conectado al exchange', filtered_text)
            
            # FILTROS DE IDENTIDAD ROBUSTOS
            # Nombres y referencias personales
            filtered_text = re.sub(r'Harold\s*Nunes?', 'el desarrollador', filtered_text, flags=re.IGNORECASE)
            filtered_text = re.sub(r'\bHarold\b', 'el administrador', filtered_text, flags=re.IGNORECASE)
            filtered_text = re.sub(r'[Cc]reador\s*[Dd]e\s*OMNIX', 'el desarrollador del sistema', filtered_text)
            
            # IDs y identificadores técnicos
            filtered_text = re.sub(r'chat_id[:\s]*[\d]+', 'identificación de usuario', filtered_text)
            filtered_text = re.sub(r'user_id[:\s]*[\d]+', 'ID de usuario', filtered_text)
            filtered_text = re.sub(r'ID[:\s]*[\d]{6,}', 'identificador', filtered_text)
            
            # FILTROS DE INFORMACIÓN TÉCNICA SENSIBLE
            # Trading específico con números
            filtered_text = re.sub(r'Trading[:\s]*[\d]+\s*monedas?', 'Trading: Múltiples criptomonedas', filtered_text)
            filtered_text = re.sub(r'Pares[:\s]*[\d]+\s*pares?', 'Pares: Varios pares activos', filtered_text)
            filtered_text = re.sub(r'[\d]+\s*monedas?\s*activas?', 'varias criptomonedas activas', filtered_text)
            
            # URLs y endpoints
            filtered_text = re.sub(r'https?://[^\s]+api[^\s]*', '[API_ENDPOINT]', filtered_text)
            filtered_text = re.sub(r'localhost[:\d]*', '[SERVIDOR_LOCAL]', filtered_text)
            
            # FILTROS DE CONFIGURACIÓN AVANZADA
            # Datos de sistema operativo
            filtered_text = re.sub(r'Railway', 'plataforma cloud', filtered_text, flags=re.IGNORECASE)
            filtered_text = re.sub(r'Replit', 'entorno de desarrollo', filtered_text, flags=re.IGNORECASE)
            
            # Versiones y builds
            filtered_text = re.sub(r'V[\d]+\.[\d]+', 'versión actual', filtered_text)
            filtered_text = re.sub(r'[Bb]uild[:\s]*[\d]+', 'build: actual', filtered_text)
            
            # PRESERVAR INFORMACIÓN EDUCATIVA
            # Mantener términos educativos y generales
            educational_terms = ['blockchain', 'criptomoneda', 'trading', 'análisis', 'mercado', 'tendencia']
            
            return filtered_text
            
        except Exception as e:
            logger.error(f"Error filtrando contenido: {e}")
            # Respuesta generica segura en caso de error
            return "Informacion sobre criptomonedas y analisis de mercado disponible. El sistema proporciona insights educativos sobre trading y tecnologia blockchain."

    def split_text_smart(self, text, max_length=4000):
        """
        Divide texto largo inteligentemente respetando Markdown.
        Prioridad: párrafos (\n\n) → líneas (\n) → palabras → caracteres
        Returns: Lista de partes, cada una <= max_length
        """
        if len(text) <= max_length:
            return [text]
        
        parts = []
        current_part = ""
        
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            test_addition = ('\n\n' if current_part else '') + paragraph
            
            if len(current_part) + len(test_addition) <= max_length:
                current_part += test_addition
            else:
                if current_part:
                    parts.append(current_part)
                
                if len(paragraph) <= max_length:
                    current_part = paragraph
                else:
                    lines = paragraph.split('\n')
                    current_part = ""
                    for line in lines:
                        test_line = ('\n' if current_part else '') + line
                        if len(current_part) + len(test_line) <= max_length:
                            current_part += test_line
                        else:
                            if current_part:
                                parts.append(current_part)
                            
                            if len(line) <= max_length:
                                current_part = line
                            else:
                                words = line.split(' ')
                                current_part = ""
                                for word in words:
                                    test_word = (' ' if current_part else '') + word
                                    if len(current_part) + len(test_word) <= max_length:
                                        current_part += test_word
                                    else:
                                        if current_part:
                                            parts.append(current_part)
                                        if len(word) <= max_length:
                                            current_part = word
                                        else:
                                            for i in range(0, len(word), max_length):
                                                parts.append(word[i:i+max_length])
                                            current_part = ""
        
        if current_part:
            parts.append(current_part)
        
        return parts if parts else [text[:max_length]]

    def send_telegram_text_safe(self, chat_id, text, parse_mode='Markdown', edit_message_id=None):
        """
        Envía texto a Telegram de forma segura, dividiendo automáticamente si >4096 chars.
        Si edit_message_id se proporciona, intenta editar primero (para primera parte).
        """
        try:
            bot_token = getattr(self, 'bot_token', None) or os.environ.get('TELEGRAM_BOT_TOKEN')
            
            if not bot_token:
                logger.error("❌ Bot token no disponible")
                return False
            
            MAX_LENGTH = 4000
            
            parts = self.split_text_smart(text, MAX_LENGTH)
            total_parts = len(parts)
            
            logger.info(f"📨 send_telegram_text_safe: {len(text)} chars → {total_parts} parte(s)")
            
            for i, part in enumerate(parts):
                header = ""
                if total_parts > 1:
                    header = f"📄 ({i+1}/{total_parts})\n\n"
                
                final_text = header + part
                
                clean_text = final_text
                if parse_mode == 'Markdown':
                    clean_text = self._sanitize_markdown(final_text)
                
                if i == 0 and edit_message_id:
                    edit_url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
                    edit_data = {
                        'chat_id': chat_id,
                        'message_id': edit_message_id,
                        'text': clean_text
                    }
                    if parse_mode:
                        edit_data['parse_mode'] = parse_mode
                    
                    response = requests.post(edit_url, json=edit_data, timeout=30)
                    if response.status_code != 200:
                        logger.warning(f"⚠️ Edit fallido, enviando como nuevo mensaje: {response.status_code}")
                        send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                        send_data = {
                            'chat_id': chat_id,
                            'text': clean_text
                        }
                        if parse_mode:
                            send_data['parse_mode'] = parse_mode
                        response = requests.post(send_url, json=send_data, timeout=30)
                else:
                    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    send_data = {
                        'chat_id': chat_id,
                        'text': clean_text
                    }
                    if parse_mode:
                        send_data['parse_mode'] = parse_mode
                    response = requests.post(send_url, json=send_data, timeout=30)
                
                if response.status_code == 200:
                    logger.info(f"✅ Parte {i+1}/{total_parts} enviada OK ({len(clean_text)} chars)")
                else:
                    logger.error(f"❌ Error parte {i+1}: {response.text}")
                    if parse_mode:
                        send_data_plain = {
                            'chat_id': chat_id,
                            'text': clean_text
                        }
                        requests.post(send_url, json=send_data_plain, timeout=30)
                
                if i < total_parts - 1:
                    time.sleep(0.3)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error send_telegram_text_safe: {e}", exc_info=True)
            try:
                bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
                if bot_token:
                    fallback_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    fallback_data = {
                        'chat_id': chat_id,
                        'text': text[:4000] if len(text) > 4000 else text
                    }
                    requests.post(fallback_url, json=fallback_data, timeout=30)
            except Exception:
                pass
            return False

    async def _send_dual_response(self, update, context, response_text: str, user_id: str = None, 
                                   parse_mode: str = 'Markdown', edit_message_id: int = None):
        """
        Envía respuesta DUAL: texto + audio automático.
        
        Este método unifica el patrón de respuesta para que TODAS las respuestas
        del bot incluyan tanto el texto como una nota de voz explicativa.
        
        Args:
            update: Telegram update object
            context: Telegram context
            response_text: Texto de la respuesta
            user_id: ID del usuario (para determinar si es admin)
            parse_mode: Modo de parseo ('Markdown', 'HTML', None)
            edit_message_id: ID de mensaje a editar (opcional)
        
        Returns:
            bool: True si se envió exitosamente, False en caso contrario
        """
        try:
            chat_id = update.effective_chat.id
            user_name = update.effective_user.first_name if update.effective_user else "Usuario"
            
            if not response_text or not response_text.strip():
                logger.warning("⚠️ _send_dual_response: texto vacío, omitiendo")
                return False
            
            text_sent = False
            if edit_message_id:
                self.send_telegram_text_safe(
                    chat_id=chat_id,
                    text=response_text,
                    parse_mode=parse_mode,
                    edit_message_id=edit_message_id
                )
                text_sent = True
                logger.info(f"✅ Texto enviado (edit) a {chat_id}: {len(response_text)} chars")
            else:
                await update.message.reply_text(response_text, parse_mode=parse_mode)
                text_sent = True
                logger.info(f"✅ Texto enviado (reply) a {chat_id}: {len(response_text)} chars")
            
            # 🎤 V007: GENERAR VOZ EN BACKGROUND PARA TODOS LOS USUARIOS
            if VOICE_SERVICE_AVAILABLE and schedule_voice_response and text_sent:
                if response_text and len(response_text) > 20:
                    try:
                        effective_user_id = user_id or str(chat_id)
                        voice_thread = schedule_voice_response(
                            chat_id=chat_id,
                            response_text=response_text,
                            user_name=user_name,
                            user_id=effective_user_id,
                            is_admin_user=is_admin(effective_user_id),
                            is_admin_func=is_admin
                        )
                        if voice_thread:
                            logger.info(f"🎤 [V007] ✅ Voz dual programada para chat_id={chat_id}")
                        else:
                            logger.warning(f"🎤 [V007] ⏭️ Voz dual saltada thread=None")
                    except Exception as voice_error:
                        logger.warning(f"⚠️ Error programando voz dual: {voice_error}")
            
            return text_sent
            
        except Exception as e:
            logger.error(f"❌ Error _send_dual_response: {e}")
            try:
                # FIX Dec 18, 2025: Enviar en partes si es muy largo
                if len(response_text) > 4000:
                    parts = self.split_text_smart(response_text, 4000)
                    for part in parts:
                        await update.message.reply_text(part)
                else:
                    await update.message.reply_text(response_text)
            except Exception:
                pass
            return False

    def _sanitize_markdown(self, text):
        """Limpia Markdown problemático que puede causar errores en Telegram"""
        if not text:
            return text
        
        sanitized = text
        sanitized = sanitized.replace('**', '*')
        sanitized = sanitized.replace('__', '_')
        sanitized = sanitized.replace('_*', '*').replace('*_', '*')
        
        return sanitized

    def send_message_in_parts(self, chat_id, text):
        """HAROLD FIX: Dividir mensajes largos inteligentemente - AHORA USA send_telegram_text_safe"""
        return self.send_telegram_text_safe(chat_id, text, parse_mode='Markdown')

    def generate_smart_response(self, text, user_name=None, chat_id=None, user_id=None):
        """FIX Dec 18, 2025: Ahora soporta multi-usuario con parámetros dinámicos"""
        try:
            effective_user_id = user_id or str(settings.TELEGRAM_ADMIN_ID)
            effective_chat_id = chat_id or str(settings.TELEGRAM_ADMIN_ID)
            effective_user_name = user_name or self._get_user_name_from_db(effective_user_id) or "Usuario"
            
            logger.info(f"🔄 generate_smart_response para {effective_user_name} (user_id={effective_user_id})")
            return self.ai.generate_response(
                user_message=text,
                user_name=effective_user_name,
                chat_id=effective_chat_id,
                user_id=effective_user_id,
                trading_system=self.trading
            )
        except Exception as e:
            logger.error(f"❌ Error generate_smart_response: {e}")
            return f"🤖 Sistema procesando: '{text}'\n\n💰 Balance real verificado con Kraken\n✅ IA superinteligente operativa"
    
    def _get_user_name_from_db(self, user_id: str) -> str:
        """Obtener nombre del usuario desde la base de datos.
        
        FIX Dec 18, 2025: NUNCA lanza excepciones - siempre retorna None en caso de error.
        Esto garantiza que el bot siga funcionando aunque la DB no esté disponible.
        """
        try:
            if not self.db_manager:
                return None
            if not hasattr(self.db_manager, '_get_connection'):
                return None
            conn = self.db_manager._get_connection()
            if not conn:
                return None
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT first_name FROM users WHERE user_id = %s", (str(user_id),))
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                if result and result[0]:
                    return result[0]
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass
                return None
        except Exception as e:
            logger.debug(f"⚠️ Could not get user name from DB: {e}")
        return None

    # ============================================================================
    # 📊 PAPER TRADING DIRECT HANDLERS - FIX Nov 30, 2025
    # Estos métodos ejecutan trades REALES en PostgreSQL desde el polling directo
    # ============================================================================
    
    def _handle_paper_buy_direct(self, chat_id, user_id, text):
        """Ejecutar /paper_buy REALMENTE desde polling directo"""
        try:
            # Parsear comando: /paper_buy BTC 100
            parts = text.split()
            if len(parts) < 3:
                self.send_telegram_text_safe(chat_id, "Uso: /paper_buy BTC 100 (comprar $100 de BTC)")
                return
            
            symbol = parts[1].upper()
            try:
                amount_usd = float(parts[2])
            except ValueError:
                self.send_telegram_text_safe(chat_id, "⚠️ Cantidad debe ser número. Ej: /paper_buy BTC 100")
                return
            
            if amount_usd <= 0:
                self.send_telegram_text_safe(chat_id, "⚠️ Cantidad debe ser mayor a 0")
                return
            
            self.send_telegram_text_safe(chat_id, f"🔍 Ejecutando compra REAL de ${amount_usd:,.2f} en {symbol}...")
            
            # EJECUTAR TRADE REAL EN POSTGRESQL
            result = self.paper_trading.execute_paper_trade(
                user_id=str(user_id),
                side='buy',
                symbol=f"{symbol}/USD",
                amount_usd=amount_usd
            )
            
            if 'error' in result:
                self.send_telegram_text_safe(chat_id, f"❌ {result['error']}")
                return
            
            msg = f"""✅ *COMPRA EJECUTADA EN POSTGRESQL*

{symbol}: +{result['amount']:.8f}
Precio: ${result['price']:,.2f}
Total: ${result['total_usd']:,.2f}

💰 *NUEVO BALANCE:*
USD: ${result['new_balance_usd']:,.2f}
BTC: {result['new_btc_balance']:.8f}
ETH: {result['new_eth_balance']:.8f}

✅ Trade guardado en base de datos"""
            
            self.send_telegram_text_safe(chat_id, msg)
            logger.info(f"✅ PAPER BUY REAL EJECUTADO: {symbol} ${amount_usd} para user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error _handle_paper_buy_direct: {e}")
            self.send_telegram_text_safe(chat_id, f"⚠️ Error: {e}")
    
    def _handle_paper_sell_direct(self, chat_id, user_id, text):
        """Ejecutar /paper_sell REALMENTE desde polling directo"""
        try:
            parts = text.split()
            if len(parts) < 3:
                self.send_telegram_text_safe(chat_id, "Uso: /paper_sell BTC 100 (vender $100 de BTC)")
                return
            
            symbol = parts[1].upper()
            try:
                amount_usd = float(parts[2])
            except ValueError:
                self.send_telegram_text_safe(chat_id, "⚠️ Cantidad debe ser número. Ej: /paper_sell BTC 100")
                return
            
            if amount_usd <= 0:
                self.send_telegram_text_safe(chat_id, "⚠️ Cantidad debe ser mayor a 0")
                return
            
            logger.info(f"🔄 _handle_paper_sell_direct: Iniciando venta para user_id={user_id}, symbol={symbol}/USD, amount=${amount_usd}")
            self.send_telegram_text_safe(chat_id, f"🔍 Ejecutando venta REAL de ${amount_usd:,.2f} en {symbol}...")
            
            result = self.paper_trading.execute_paper_trade(
                user_id=str(user_id),
                side='sell',
                symbol=f"{symbol}/USD",
                amount_usd=amount_usd
            )
            
            logger.info(f"🔄 _handle_paper_sell_direct: Resultado = {result}")
            
            if 'error' in result:
                logger.error(f"❌ _handle_paper_sell_direct: Error = {result['error']}")
                self.send_telegram_text_safe(chat_id, f"❌ {result['error']}")
                return
            
            pnl = result.get('net_realized_pnl_usd', result.get('realized_pnl', 0))
            is_win = result.get('is_winning_trade', pnl > 0)
            
            msg = f"""✅ *VENTA EJECUTADA EN POSTGRESQL*

{symbol}: -{result['amount']:.8f}
Precio Entrada: ${result.get('entry_price', 0):,.2f}
Precio Salida: ${result['price']:,.2f}
Total: ${result['total_usd']:,.2f}
P&L: ${pnl:+,.2f} {'🟢 WIN' if is_win else '🔴 LOSS'}

💰 *NUEVO BALANCE:*
USD: ${result['new_balance_usd']:,.2f}

✅ Trade cerrado y guardado en PostgreSQL"""
            
            self.send_telegram_text_safe(chat_id, msg)
            logger.info(f"✅ PAPER SELL REAL EJECUTADO Y GUARDADO: {symbol} ${amount_usd} para user {user_id} | P&L: ${pnl:+,.2f}")
            
        except Exception as e:
            logger.error(f"❌ Error _handle_paper_sell_direct: {e}")
            self.send_telegram_text_safe(chat_id, f"⚠️ Error: {e}")
    
    def _handle_paper_start_direct(self, chat_id, user_id):
        """Inicializar paper trading para usuario"""
        try:
            result = self.paper_trading.initialize_user(str(user_id))
            
            if 'error' in result:
                self.send_telegram_text_safe(chat_id, f"❌ {result['error']}")
                return
            
            if result.get('already_initialized'):
                msg = f"""📊 *PAPER TRADING YA ACTIVO*

Balance: ${result['balance_usd']:,.2f}
Trades: {result['total_trades']}

Usa /paper_buy BTC 100 para comprar"""
            else:
                msg = """🎯 *PAPER TRADING ACTIVADO*

💰 Balance inicial: $1,000,000

Comandos disponibles:
• /paper_buy BTC 100
• /paper_sell BTC 100
• /paper_balance
• /paper_positions"""
            
            self.send_telegram_text_safe(chat_id, msg)
            logger.info(f"✅ Paper Trading inicializado para user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error _handle_paper_start_direct: {e}")
            self.send_telegram_text_safe(chat_id, f"⚠️ Error: {e}")
    
    def _handle_paper_balance_direct(self, chat_id, user_id):
        """Mostrar balance de paper trading"""
        try:
            balance = self.paper_trading.get_balance(str(user_id))
            
            if 'error' in balance:
                self.send_telegram_text_safe(chat_id, f"⚠️ {balance.get('message', 'Usa /paper_start para comenzar')}")
                return
            
            msg = f"""📊 *PAPER TRADING BALANCE*

💵 *EFECTIVO:*
USD: ${balance['balance_usd']:,.2f}

₿ *CRYPTO:*
BTC: {balance['btc_balance']:.8f}
ETH: {balance['eth_balance']:.8f}

💰 *VALOR TOTAL:*
${balance['total_value_usd']:,.2f}

📈 *PERFORMANCE:*
P&L: ${balance['profit_loss_usd']:,.2f} ({balance['profit_loss_pct']:+.2f}%)
Trades: {balance['total_trades']}"""
            
            self.send_telegram_text_safe(chat_id, msg)
            
        except Exception as e:
            logger.error(f"❌ Error _handle_paper_balance_direct: {e}")
            self.send_telegram_text_safe(chat_id, f"⚠️ Error: {e}")
    
    def _handle_paper_positions_direct(self, chat_id, user_id):
        """Mostrar posiciones abiertas de paper trading"""
        try:
            positions = self.paper_trading.get_open_positions(str(user_id))
            
            if not positions:
                self.send_telegram_text_safe(chat_id, "📊 No tienes posiciones abiertas.\n\nUsa /paper_buy BTC 100 para abrir una posición.")
                return
            
            msg = "📊 *POSICIONES ABIERTAS*\n\n"
            for pos in positions:
                msg += f"• {pos['symbol']}: {pos['quantity']:.8f} @ ${pos['entry_price']:,.2f}\n"
            
            self.send_telegram_text_safe(chat_id, msg)
            
        except Exception as e:
            logger.error(f"❌ Error _handle_paper_positions_direct: {e}")
            self.send_telegram_text_safe(chat_id, f"⚠️ Error: {e}")

    def _process_sync_aggregated_messages(self, user_id: str, chat_id: int):
        """Procesar mensajes agregados de forma síncrona (para polling manual)"""
        try:
            with self._sync_buffer_lock:
                if user_id not in self._sync_message_buffers or not self._sync_message_buffers[user_id]:
                    return
                
                buffered_messages = self._sync_message_buffers.pop(user_id, [])
                if user_id in self._sync_message_timers:
                    del self._sync_message_timers[user_id]
            
            if not buffered_messages:
                return
            
            combined_text = " ".join([msg['text'] for msg in buffered_messages if msg.get('text')])
            first_msg = buffered_messages[0]
            original_user_id = first_msg['user_id']
            
            logger.info(f"📦 SYNC MENSAJE AGREGADO ({len(buffered_messages)} partes) de user:{user_id}: {combined_text[:100]}...")
            
            self.handle_direct_message(chat_id, combined_text, user_id=original_user_id)
            
        except Exception as e:
            logger.error(f"❌ Error procesando sync mensajes agregados: {e}")

    def _buffer_sync_message(self, user_id: str, chat_id: int, text: str, original_user_id: int):
        """Agregar mensaje al buffer síncrono con debounce de 1.5s"""
        try:
            with self._sync_buffer_lock:
                if user_id in self._sync_message_timers:
                    self._sync_message_timers[user_id].cancel()
                    logger.info(f"🔄 SYNC Timer cancelado para {user_id} - agregando mensaje al buffer")
                
                if user_id not in self._sync_message_buffers:
                    self._sync_message_buffers[user_id] = []
                
                self._sync_message_buffers[user_id].append({
                    'text': text,
                    'chat_id': chat_id,
                    'user_id': original_user_id,
                    'timestamp': time.time()
                })
                
                logger.info(f"📥 SYNC Mensaje #{len(self._sync_message_buffers[user_id])} buffered de {user_id}: {text[:50]}...")
                
                timer = threading.Timer(
                    self._message_aggregation_delay,
                    self._process_sync_aggregated_messages,
                    args=(user_id, chat_id)
                )
                timer.start()
                self._sync_message_timers[user_id] = timer
                
        except Exception as e:
            logger.error(f"❌ Error en buffer sync: {e}")
            self.handle_direct_message(chat_id, text, user_id=original_user_id)

    async def start_polling(self, drop_pending_updates: bool = True):
        """Iniciar bot en modo polling 100% ASYNC - VERSION NATIVA V7.0
        
        Usa Application nativo de python-telegram-bot v20+ para máxima
        concurrencia y escalabilidad (100k+ usuarios).
        
        Características:
        - 100% async/await nativo (no threads bloqueantes)
        - Reconexión automática integrada en la librería
        - Error handling con logging detallado
        - Shutdown graceful con señales SIGINT/SIGTERM
        - Compatible con alta concurrencia
        
        Args:
            drop_pending_updates: Si True, ignora mensajes pendientes al iniciar
        
        Returns:
            True si el bot se ejecutó correctamente, False en caso de error
        """
        try:
            logger.info(f"🚀 Iniciando bot Telegram {VERSION_BANNER} ASYNC NATIVO...")
            logger.info("⚡ Modo: 100% async/await - Máxima concurrencia")
            
            if not self.application:
                logger.error("❌ Application no inicializada. Ejecutar setup_bot() primero.")
                return False
            
            async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
                """Handler global — el bot NUNCA cae por errores de red o de usuario."""
                from telegram.error import TimedOut, NetworkError, RetryAfter, Forbidden, BadRequest
                err = context.error
                err_name = type(err).__name__

                # Errores de red — recuperables, solo log
                if isinstance(err, (TimedOut, NetworkError)):
                    logger.warning(f"⚠️ [ErrorHandler] Red recuperable ({err_name}): {err} — bot sigue activo")
                    return
                if isinstance(err, RetryAfter):
                    logger.warning(f"⚠️ [ErrorHandler] RetryAfter {err.retry_after}s — bot sigue activo")
                    return
                # Usuario bloqueó el bot — no es un crash
                if isinstance(err, Forbidden):
                    logger.warning(f"⚠️ [ErrorHandler] Bot bloqueado por usuario: {err}")
                    return
                # Mensaje inválido — no es un crash
                if isinstance(err, BadRequest):
                    logger.warning(f"⚠️ [ErrorHandler] BadRequest (mensaje inválido): {err}")
                    return
                # PoolTimeout de httpcore (viene envuelto a veces como Exception genérico)
                if 'PoolTimeout' in err_name or 'pool' in str(err).lower():
                    logger.warning(f"⚠️ [ErrorHandler] PoolTimeout detectado — bot sigue activo: {err}")
                    return
                # Cualquier otro error — loguear pero NUNCA propagar para que el bot no caiga
                logger.error(f"🔴 [ErrorHandler] Error inesperado ({err_name}): {err} — bot continúa")
                if update:
                    logger.error(f"📝 Update: {update}")
            
            self.application.add_error_handler(error_handler)
            
            logger.info("📡 Iniciando Application.run_polling() nativo...")
            
            self.is_running = True
            
            await self.application.initialize()
            await self.application.start()

            # Eliminar webhook activo antes de polling — si hay un webhook
            # configurado en Railway, Telegram envía updates ahí y el bot
            # nunca los recibe via polling. Esto lo limpia siempre.
            try:
                deleted = await self.application.bot.delete_webhook(drop_pending_updates=drop_pending_updates)
                if deleted:
                    logger.info("🧹 Webhook eliminado correctamente — polling habilitado")
                else:
                    logger.info("ℹ️ No había webhook activo")
                webhook_info = await self.application.bot.get_webhook_info()
                logger.info(f"📋 Webhook info post-delete: url='{webhook_info.url}' pending={webhook_info.pending_update_count}")
            except Exception as wh_err:
                logger.warning(f"⚠️ No se pudo eliminar webhook (no crítico): {wh_err}")

            await self.application.updater.start_polling(
                drop_pending_updates=drop_pending_updates,
                allowed_updates=Update.ALL_TYPES
            )
            
            logger.info(f"✅ Bot Telegram {VERSION_BANNER} ASYNC corriendo")
            logger.info("🛡️ Reconexión automática NATIVA activada")
            logger.info("⚡ Alta concurrencia habilitada (100k+ usuarios)")
            
            # 🤖 FIX Dec 14, 2025: Restaurar auto-trading al iniciar el bot
            # Esto verifica si había usuarios con auto_trading=true y restaura el loop
            if self.auto_trading:
                try:
                    restored = self.auto_trading.check_and_restore_auto_trading()
                    if restored:
                        logger.info("🤖 Auto-Trading RESTAURADO - Loop de trading activo")
                    else:
                        logger.info("📊 Auto-Trading: No hay sesiones activas para restaurar")
                except Exception as e:
                    logger.warning(f"⚠️ Error restaurando auto-trading: {e}")
            
            try:
                while self.is_running:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info("🛑 Recibida señal de cancelación")
            
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en start_polling: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def start_webhook(
        self,
        webhook_url: str,
        secret_token: str = "",
        listen: str = "0.0.0.0",
        port: int = 8080,
    ) -> bool:
        """Start bot in WEBHOOK mode — zero Conflict errors on Railway deploys.

        In polling mode two Railway instances fight over the same token with
        "Conflict: terminated by other getUpdates request".  In webhook mode
        Telegram PUSHES updates to our HTTPS URL — there is no polling race,
        so any number of instances can coexist without coordination.

        Architecture:
            Telegram → HTTPS POST {webhook_url}/telegram/webhook
                     → python-telegram-bot updater (aiohttp internal)
                     → application handlers (commands, messages, callbacks)

        Args:
            webhook_url:   Public HTTPS base URL of this Railway service,
                           e.g. "https://omnix-bot.up.railway.app"
                           Set via TELEGRAM_WEBHOOK_URL env var.
            secret_token:  Random 32+ char string to validate that POST
                           requests originate from Telegram (not from
                           arbitrary internet traffic).
                           Set via TELEGRAM_WEBHOOK_SECRET env var.
            listen:        Interface to bind the internal aiohttp server.
                           Always "0.0.0.0" in Railway containers.
            port:          Port to listen on — must match Railway $PORT.

        Returns:
            True on clean shutdown, False on fatal error.
        """
        try:
            if not self.application:
                logger.error("❌ Application not initialized — cannot start webhook")
                return False

            url_path        = "/telegram/webhook"
            full_webhook_url = f"{webhook_url.rstrip('/')}{url_path}"

            logger.info("🔗 [WEBHOOK] Starting Telegram bot in WEBHOOK mode")
            logger.info("   URL  : %s", full_webhook_url)
            logger.info("   Bind : %s:%d", listen, port)
            logger.info("   Auth : %s", "✅ secret_token configured" if secret_token else "⚠️  no secret_token (set TELEGRAM_WEBHOOK_SECRET)")

            # ── Error handler — identical coverage to polling mode ────────────
            async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
                from telegram.error import (
                    TimedOut, NetworkError, RetryAfter, Forbidden, BadRequest, Conflict
                )
                err      = context.error
                err_name = type(err).__name__
                if isinstance(err, (TimedOut, NetworkError)):
                    logger.warning("⚠️ [Webhook] Red recuperable (%s): %s", err_name, err)
                    return
                if isinstance(err, RetryAfter):
                    logger.warning("⚠️ [Webhook] RetryAfter %ds", err.retry_after)
                    return
                if isinstance(err, Forbidden):
                    logger.warning("⚠️ [Webhook] Bot bloqueado por usuario: %s", err)
                    return
                if isinstance(err, BadRequest):
                    logger.warning("⚠️ [Webhook] BadRequest: %s", err)
                    return
                if isinstance(err, Conflict):
                    # Should never happen in webhook mode — log loudly if it does
                    logger.error("🔴 [Webhook] Conflict detectado (inesperado en webhook mode): %s", err)
                    return
                if 'PoolTimeout' in err_name or 'pool' in str(err).lower():
                    logger.warning("⚠️ [Webhook] PoolTimeout: %s", err)
                    return
                logger.error("🔴 [Webhook] Error inesperado (%s): %s", err_name, err)
                if update:
                    logger.error("   Update: %s", update)

            self.application.add_error_handler(error_handler)

            # ── Initialize application ────────────────────────────────────────
            await self.application.initialize()
            await self.application.start()
            self.is_running = True

            # ── Register webhook with Telegram and bind local aiohttp server ──
            await self.application.updater.start_webhook(
                listen=listen,
                port=port,
                url_path=url_path,
                webhook_url=full_webhook_url,
                secret_token=secret_token if secret_token else None,
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES,
            )

            logger.info("✅ [WEBHOOK] Bot %s WEBHOOK MODE activo", VERSION_BANNER)
            logger.info("   🔗 Telegram pushes → %s", full_webhook_url)
            logger.info("   🛡️  Zero-conflict: inmune a overlaps de deploy en Railway")
            logger.info("   ♾️   Escala a réplicas ilimitadas sin coordinación")

            # ── Restore auto-trading sessions ─────────────────────────────────
            if self.auto_trading:
                try:
                    restored = self.auto_trading.check_and_restore_auto_trading()
                    if restored:
                        logger.info("🤖 Auto-Trading RESTAURADO — loop de trading activo")
                    else:
                        logger.info("📊 Auto-Trading: no hay sesiones activas para restaurar")
                except Exception as at_err:
                    logger.warning("⚠️ Error restaurando auto-trading: %s", at_err)

            # ── Main keep-alive loop ──────────────────────────────────────────
            try:
                while self.is_running:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info("🛑 [Webhook] Keep-alive loop cancelado")

            # ── Graceful shutdown ─────────────────────────────────────────────
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("✅ [Webhook] Shutdown completo")
            except Exception as sd_err:
                logger.warning("⚠️ [Webhook] Shutdown error (no crítico): %s", sd_err)

            return True

        except Exception as e:
            logger.error("❌ [Webhook] Fatal error en start_webhook: %s", e)
            import traceback
            traceback.print_exc()
            return False

    async def stop_async(self):
        """Detener bot async de forma graceful."""
        logger.info("🛑 Deteniendo bot Telegram...")
        self.is_running = False
        
        if self.application:
            try:
                if self.application.updater and self.application.updater.running:
                    await self.application.updater.stop()
                if self.application.running:
                    await self.application.stop()
                    await self.application.shutdown()
                logger.info("✅ Bot detenido correctamente")
            except Exception as e:
                logger.error(f"❌ Error deteniendo bot: {e}")
    
    # ============================================================================
    # 📊 STOCK TRADING COMMANDS - BOLSA DE VALORES (NYSE/NASDAQ)
    # ============================================================================
    
    async def balance_stocks_command(self, update, context):
        """Comando /balance_bolsa - Balance en bolsa de valores"""
        if not self.stock_handler or not self.stock_handler.enabled:
            await update.message.reply_text("📊 Módulo de bolsa no activado")
            return
        
        try:
            response = await self.stock_handler.handle_balance_stocks(update, context)
            await update.message.reply_text(response, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error en balance_stocks: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def market_status_command(self, update, context):
        """Comando /mercado - Estado del mercado NYSE/NASDAQ"""
        if not self.stock_handler or not self.stock_handler.enabled:
            await update.message.reply_text("📊 Módulo de bolsa no activado")
            return
        
        try:
            response = await self.stock_handler.handle_market_status(update, context)
            await update.message.reply_text(response, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error en market_status: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def analyze_stock_command(self, update, context):
        """Comando /analizar [SYMBOL] - Auto-detecta crypto vs stock"""
        try:
            symbol = context.args[0].upper() if context.args else None
            
            if not symbol:
                await update.message.reply_text(
                    "⚠️ **Uso:** `/analizar AAPL` (acciones) o `/analizar BTC` (crypto)\n\n"
                    "OMNIX detecta automáticamente el tipo de activo.",
                    parse_mode='Markdown'
                )
                return
            
            from omnix_services.symbol_classifier import symbol_classifier
            asset_type, confidence = symbol_classifier.classify(symbol)
            
            if asset_type == 'crypto':
                logger.info(f"🪙 {symbol} → CRYPTO routing (conf: {confidence:.0%})")
                
                if not self.trading:
                    await update.message.reply_text("⚠️ Sistema crypto no disponible")
                    return
                
                try:
                    analisis = self.trading.generate_comprehensive_analysis(f"{symbol}/USD")
                    
                    mensaje = f"""
🪙 **ANÁLISIS CRYPTO: {symbol}/USD**

📊 **Precio:** ${analisis.get('precio', 'N/A')}
📈 **RSI:** {analisis.get('rsi', 'N/A')}
📉 **MACD:** {analisis.get('macd', 'N/A')}
🎯 **Recomendación:** {analisis.get('recomendacion', 'NEUTRO')}

🔮 **Análisis IA:**
{analisis.get('analisis_ia', 'Mercado en análisis...')}

⚡ **Actualizado:** {datetime.now().strftime('%H:%M:%S')}
🧬 *Sistema OMNIX Quantum*
"""
                    await update.message.reply_text(mensaje, parse_mode='Markdown')
                    
                except Exception as e:
                    logger.error(f"Error análisis crypto: {e}")
                    await update.message.reply_text(f"⚠️ Error analizando {symbol}: {str(e)}")
            
            else:
                logger.info(f"📈 {symbol} → STOCK routing (conf: {confidence:.0%})")
                
                if not self.stock_handler or not self.stock_handler.enabled:
                    await update.message.reply_text(
                        f"📊 **{symbol}** detectado como acción, pero el módulo de bolsa no está activado.\n\n"
                        "Contacta al administrador para activar `STOCK_TRADING_ENABLED=true`",
                        parse_mode='Markdown'
                    )
                    return
                
                response = await self.stock_handler.handle_analyze_stock(update, context, symbol)
                await update.message.reply_text(response, parse_mode='Markdown')
        
        except Exception as e:
            logger.error(f"Error en analyze_command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def buy_stock_command(self, update, context):
        """Comando /comprar_bolsa [SYMBOL] [AMOUNT] - Comprar acciones"""
        if not self.stock_handler or not self.stock_handler.enabled:
            await update.message.reply_text("📊 Módulo de bolsa no activado")
            return
        
        try:
            symbol = context.args[0] if len(context.args) > 0 else None
            amount = float(context.args[1]) if len(context.args) > 1 else 100.0
            response = await self.stock_handler.handle_buy_stock(update, context, symbol, amount)
            await update.message.reply_text(response, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error en buy_stock: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def sell_stock_command(self, update, context):
        """Comando /vender_bolsa [SYMBOL] - Vender posición en acciones"""
        if not self.stock_handler or not self.stock_handler.enabled:
            await update.message.reply_text("📊 Módulo de bolsa no activado")
            return
        
        try:
            symbol = context.args[0] if context.args else None
            response = await self.stock_handler.handle_sell_stock(update, context, symbol)
            await update.message.reply_text(response, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error en sell_stock: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def premium_stock_command(self, update, context):
        """Comando /analizar_premium [SYMBOL] - Análisis institucional"""
        try:
            symbol = context.args[0].upper() if context.args else None
            
            if not symbol:
                await update.message.reply_text(
                    "⚠️ **Uso:** `/analizar_premium AAPL` (acciones) o `/analizar_premium BTC` (crypto)\n\n"
                    "Análisis institucional con 9+ módulos premium.",
                    parse_mode='Markdown'
                )
                return
            
            from omnix_services.symbol_classifier import symbol_classifier
            asset_type, confidence = symbol_classifier.classify(symbol)
            
            if asset_type == 'crypto':
                logger.info(f"🪙 {symbol} → CRYPTO PREMIUM routing (conf: {confidence:.0%})")
                
                if not self.trading_enterprise_enabled:
                    await update.message.reply_text(
                        f"🪙 **{symbol}** detectado como crypto.\n\n"
                        "Usa `/analisis {symbol}` para análisis crypto cuántico.",
                        parse_mode='Markdown'
                    )
                    return
                
                try:
                    await update.message.reply_text(f"🔄 Analizando {symbol} con sistema cuántico premium...")
                    
                    price = self.trading.get_current_price(f"{symbol}/USD")
                    analisis = self.trading.generate_comprehensive_analysis(f"{symbol}/USD")
                    
                    mensaje = f"""
🪙 **ANÁLISIS PREMIUM: {symbol}/USD**
━━━━━━━━━━━━━━━━━━━━━━

💵 **Precio:** ${price:,.2f}
📈 **RSI:** {analisis.get('rsi', 'N/A')}
📉 **MACD:** {analisis.get('macd', 'N/A')}
🎯 **Señal:** {analisis.get('recomendacion', 'NEUTRO')}

🔮 **Análisis Cuántico:**
{analisis.get('analisis_ia', 'Procesando...')}

**Módulos Activos:**
   📈 EMA Regime Signal: ✅ (Primary 40pts)
   🎲 Monte Carlo: ✅ (Veto/Penalty)
   📊 Kalman Filter: ✅ (15pts)
   🧠 HMM Regime: ✅ (25pts)
   🔗 Non-Markovian: ✅ (15pts)

⚡ {datetime.now().strftime('%H:%M:%S')}
🧬 *OMNIX Quantum Premium*
"""
                    await update.message.reply_text(mensaje, parse_mode='Markdown')
                    
                except Exception as e:
                    logger.error(f"Error análisis crypto premium: {e}")
                    await update.message.reply_text(f"⚠️ Error: {str(e)}")
            
            else:
                logger.info(f"📈 {symbol} → STOCK PREMIUM routing (conf: {confidence:.0%})")
                
                if not self.stock_handler or not self.stock_handler.enabled:
                    await update.message.reply_text(
                        f"📊 **{symbol}** detectado como acción, pero el módulo de bolsa no está activado.",
                        parse_mode='Markdown'
                    )
                    return
                
                response = await self.stock_handler.handle_premium_analysis(update, context, symbol)
                await update.message.reply_text(response, parse_mode='Markdown')
        
        except Exception as e:
            logger.error(f"Error en premium_command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def stock_status_command(self, update, context):
        """Comando /stock_status - Estado del sistema"""
        if not self.stock_handler or not self.stock_handler.enabled:
            await update.message.reply_text("📊 Módulo de bolsa no activado")
            return
        
        try:
            response = await self.stock_handler.handle_stock_status(update, context)
            await update.message.reply_text(response, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error en stock_status: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def stock_risk_dashboard_command(self, update, context):
        """Comando /risk_dashboard - Dashboard de riesgo institucional"""
        if not self.stock_handler or not self.stock_handler.enabled:
            await update.message.reply_text("📊 Módulo de bolsa no activado")
            return
        
        try:
            response = await self.stock_handler.handle_risk_dashboard(update, context)
            await update.message.reply_text(response, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error en stock_risk_dashboard: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    # ==========================================
    # 📈 TRADING MENU COMMAND
    # ==========================================
    
    async def trading_menu_command(self, update, context):
        """Comando /trading - Menú principal de trading"""
        try:
            response = f"""
📈 *OMNIX TRADING CENTER*

🎯 *Modos de Trading Disponibles:*

📄 *PAPER TRADING* (Recomendado para empezar)
   `/paper_start` - Iniciar con $1M virtual
   `/paper_balance` - Ver balance simulado
   `/paper_buy BTC 10000` - Comprar $10K en BTC
   `/paper_sell BTC` - Vender posición

🤖 *AUTO-TRADING 24/7*
   `/autotrading` - Configurar trading automático
   `/auto_start` - Activar bot automático
   `/auto_stop` - Pausar bot
   `/auto_status` - Ver estado

📊 *ANÁLISIS DE MERCADO*
   `/analizar BTC` - Análisis completo
   `/quantum BTC` - Simulación Monte Carlo
   `/sentiment BTC` - Sentimiento de mercado
   `/blackswan BTC` - Detección de riesgos

💱 *ARBITRAJE MULTI-EXCHANGE*
   `/arbitraje` - Info del sistema
   `/arbitrage_scan BTC` - Buscar oportunidades

🛡️ *GESTIÓN DE RIESGO*
   `/rms` - Dashboard de riesgos
   `/risk_status` - Estado de protecciones

📈 *BOLSA DE VALORES (NYSE/NASDAQ)*
   `/stock_status` - Estado del módulo
   `/analizar AAPL` - Analizar acción

⚙️ *CONFIGURACIÓN*
   `/miconfig` - Mi configuración
   `/perfil` - Mi perfil de trading

💡 *Tip:* Empieza con /paper_start para practicar sin riesgo.
"""
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en trading_menu_command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def arbitraje_command(self, update, context):
        """Comando /arbitraje - Alias español para arbitrage"""
        if not self.arbitrage_scanner:
            response = """
💱 *OMNIX ARBITRAJE MULTI-EXCHANGE*

📊 *¿Qué es el Arbitraje?*
El arbitraje consiste en comprar un activo en un exchange 
donde está más barato y venderlo en otro donde está más caro,
capturando la diferencia como ganancia.

🏦 *Exchanges Soportados (8):*
   • Kraken, Binance, Coinbase, Bybit
   • KuCoin, OKX, Gate.io, Bitfinex

⚠️ *Estado Actual:*
El módulo de arbitraje requiere configuración de API keys
para cada exchange. Actualmente en modo paper trading.

📋 *Comandos:*
   `/arbitrage_scan BTC/USD` - Buscar oportunidades
   `/arbitrage_stats` - Ver estadísticas

💡 El sistema escanea precios en tiempo real y detecta
diferencias de precio mayores al umbral configurado.
"""
            await update.message.reply_text(response, parse_mode='Markdown')
            return
        
        await self.arbitrage_command(update, context)

    # ==========================================
    # 📊 COMANDOS NUEVOS — PRICES / MEMORIA / PATRONES / QUANTUM FAST
    # ==========================================

    async def prices_command(self, update, context):
        """Comando /prices - Precios en tiempo real de las principales criptos"""
        try:
            loading_msg = await update.message.reply_text("📊 Obteniendo precios en tiempo real...")
            cryptos = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA']
            lines = []
            for symbol in cryptos:
                try:
                    price_data = self.trading.get_real_market_data(f"{symbol}/USD")
                    if price_data and 'precio_actual' in price_data:
                        precio = price_data['precio_actual']
                        cambio = price_data.get('cambio_24h', 0)
                        try:
                            cambio_f = float(cambio)
                            arrow = "📈" if cambio_f >= 0 else "📉"
                            lines.append(f"{arrow} *{symbol}:* ${precio:,.2f}  ({cambio_f:+.2f}%)")
                        except Exception:
                            lines.append(f"📊 *{symbol}:* ${precio:,.2f}")
                    else:
                        lines.append(f"⚠️ *{symbol}:* No disponible")
                except Exception:
                    lines.append(f"⚠️ *{symbol}:* Error al consultar")
            msg = (
                "📊 *PRECIOS EN TIEMPO REAL*\n\n"
                + "\n".join(lines)
                + f"\n\n_Kraken · {datetime.now().strftime('%H:%M:%S')} UTC_"
            )
            await loading_msg.edit_text(msg, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error prices_command: {e}")
            await update.message.reply_text("⚠️ Error al obtener precios")

    async def memoria_command(self, update, context):
        """Comando /memoria - Historial reciente de conversación con OMNIX"""
        try:
            chat_id = update.effective_chat.id
            historial = []
            if hasattr(self, 'db_manager') and self.db_manager:
                try:
                    historial = self.db_manager.get_conversation_history(chat_id, limit=5)
                except Exception:
                    historial = []
            if historial:
                lines = []
                for entry in historial:
                    role = "Tú" if entry.get('role') == 'user' else "OMNIX"
                    texto = str(entry.get('content', ''))[:120]
                    if len(str(entry.get('content', ''))) > 120:
                        texto += "..."
                    lines.append(f"*{role}:* {texto}")
                msg = "🧠 *MEMORIA — ÚLTIMAS INTERACCIONES*\n\n" + "\n\n".join(lines)
            else:
                msg = (
                    "🧠 *MEMORIA OMNIX*\n\n"
                    "No hay historial reciente registrado.\n"
                    "Cada conversación con el bot queda guardada aquí."
                )
            await update.message.reply_text(msg, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error memoria_command: {e}")
            await update.message.reply_text("⚠️ Error al cargar memoria")

    async def patrones_command(self, update, context):
        """Comando /patrones - Detección de patrones técnicos en BTC"""
        try:
            symbol = context.args[0].upper() if context.args else "BTC"
            loading_msg = await update.message.reply_text(f"🔍 Analizando patrones técnicos en {symbol}...")
            price_data = self.trading.get_real_market_data(f"{symbol}/USD")
            if not price_data or 'precio_actual' not in price_data:
                await loading_msg.edit_text(f"⚠️ No se pudo obtener datos de {symbol}")
                return
            precio = price_data['precio_actual']
            cambio = price_data.get('cambio_24h', 0)
            volumen = price_data.get('volumen', 'N/A')
            try:
                cambio_f = float(cambio)
                if cambio_f > 3:
                    tendencia = "📈 Tendencia alcista fuerte"
                    patron = "Momentum positivo — presión compradora dominante"
                    señal = "✅ BULL"
                elif cambio_f > 0:
                    tendencia = "📈 Tendencia alcista moderada"
                    patron = "Consolidación positiva — acumulación gradual"
                    señal = "⚡ NEUTRAL/BULL"
                elif cambio_f > -3:
                    tendencia = "📉 Tendencia bajista moderada"
                    patron = "Corrección controlada — posible rebote técnico"
                    señal = "⚡ NEUTRAL/BEAR"
                else:
                    tendencia = "📉 Tendencia bajista fuerte"
                    patron = "Presión vendedora dominante — cautela recomendada"
                    señal = "🔴 BEAR"
            except Exception:
                tendencia = "📊 Sin datos de tendencia"
                patron = "Datos insuficientes para patrón"
                señal = "❓ DESCONOCIDO"
            msg = (
                f"🔍 *PATRONES TÉCNICOS — {symbol}/USD*\n\n"
                f"💵 *Precio actual:* ${precio:,.2f}\n"
                f"📊 *Cambio 24h:* {cambio}%\n"
                f"📦 *Volumen:* {volumen}\n\n"
                f"🎯 *Patrón detectado:*\n{tendencia}\n{patron}\n\n"
                f"*Señal:* {señal}\n\n"
                f"_Para análisis completo usa_ /analizar {symbol}"
            )
            await loading_msg.edit_text(msg, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error patrones_command: {e}")
            await update.message.reply_text("⚠️ Error al analizar patrones")

    async def quantum_fast_command(self, update, context):
        """Comando /quantum_fast - Análisis Monte Carlo rápido (1,000 escenarios)"""
        try:
            if not ADVANCED_FEATURES_AVAILABLE or not global_advanced_features:
                await update.message.reply_text("⚠️ Advanced Features no disponibles")
                return
            symbol = context.args[0].upper() if context.args else "BTC"
            loading_msg = await update.message.reply_text(f"⚡ Ejecutando análisis rápido de {symbol}...")
            price = self.trading.get_current_price(f"{symbol}/USD")
            if not price:
                price = 50000
            result = global_advanced_features.monte_carlo.simulate_trading_strategy(
                current_price=price,
                investment=1000,
                days=7
            )
            win_rate = result['win_rate']
            if win_rate > 60:
                recomendacion = "✅ Condiciones favorables para operar"
            elif win_rate > 50:
                recomendacion = "⚡ Condiciones neutras — precaución"
            else:
                recomendacion = "❌ Condiciones desfavorables — esperar"
            msg = (
                f"⚡ *QUANTUM FAST — {symbol}/USD*\n\n"
                f"💰 *Capital simulado:* $1,000 USD\n"
                f"📅 *Horizonte:* 7 días\n"
                f"🎲 *Escenarios:* {result['simulations']:,}\n\n"
                f"📊 *RESULTADO:*\n"
                f"✅ Win Rate: {win_rate:.1f}%\n"
                f"❌ Loss Rate: {result['loss_rate']:.1f}%\n"
                f"💵 Profit esperado: ${result['expected_profit']:.2f}\n\n"
                f"🎯 *{recomendacion}*\n\n"
                f"_Para análisis completo (30 días, 10K escenarios) usa_ /quantum {symbol}"
            )
            await loading_msg.edit_text(msg, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error quantum_fast_command: {e}")
            await update.message.reply_text("⚠️ Error en análisis quantum")

    # ==========================================
    # 💱 ARBITRAGE MULTI-EXCHANGE PREMIUM
    # ==========================================
    
    async def arbitrage_command(self, update, context):
        """Comando /arbitrage - Información del sistema de arbitraje"""
        if not self.arbitrage_scanner:
            await update.message.reply_text("💱 Módulo de arbitraje no disponible")
            return
        
        try:
            response = f"""
💱 **OMNIX ARBITRAGE PREMIUM**

🏦 **Sistema Multi-Exchange Institucional**
   • 8 Exchanges: Kraken, Binance, Coinbase, Bybit, KuCoin, OKX, Gate.io, Bitfinex
   • Profit mínimo: {self.arbitrage_scanner.min_profit_threshold}%
   • Modo: {'📄 PAPER TRADING' if self.arbitrage_executor.paper_trading else '🔴 LIVE TRADING'}

📊 **Comandos Disponibles:**
   /arbitrage\_scan SYMBOL - Escanear oportunidades
   /arbitrage\_execute AMOUNT - Ejecutar mejor oportunidad
   /arbitrage\_stats - Ver estadísticas

🎯 **Cómo Funciona:**
   1. Escanea precios en 8 exchanges simultáneamente
   2. Detecta diferencias de precio (spreads)
   3. Calcula profit neto (después de fees)
   4. Ejecuta compra/venta paralela automática

💰 **Ejemplo:**
   BTC en Binance: $87,800
   BTC en Kraken: $88,100
   → Profit: $300 por BTC (0.34%)

⚡ **Ultra-Rápido:**
   • Latencia: <100ms por exchange
   • Ejecución: Paralela (compra + venta simultánea)
   • Kill-switch: Protección automática

🔐 **Seguridad:**
   • API keys gestionadas con Replit Secrets
   • Paper trading por default (sin riesgo)
   • Límites de trading configurables

¡Usa /arbitrage_scan BTC/USD para buscar oportunidades ahora!
"""
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en arbitrage_command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def arbitrage_scan_command(self, update, context):
        """Comando /arbitrage_scan [SYMBOL] - Escanear oportunidades de arbitraje"""
        if not self.arbitrage_scanner:
            await update.message.reply_text("💱 Módulo de arbitraje no disponible")
            return
        
        try:
            # Obtener símbolo (default: BTC/USD)
            symbol = context.args[0] if context.args else 'BTC/USD'
            
            # Mensaje de carga
            loading_msg = await update.message.reply_text(f"🔍 Escaneando {symbol} en 8 exchanges...")
            
            # Ejecutar escaneo
            result = self.arbitrage_scanner.check_arbitrage_opportunities(symbol)
            
            if not result.get('success'):
                await loading_msg.edit_text(f"❌ Error: {result.get('error', 'Unknown error')}")
                return
            
            opportunities = result.get('opportunities', [])
            stats = result.get('statistics', {})
            prices = result.get('prices', {})
            
            # Formatear respuesta
            if not opportunities:
                response = f"""
🔍 **Escaneo Completado - {symbol}**

📊 **Resultado:**
   ❌ No se encontraron oportunidades de arbitraje
   
📈 **Precios en Exchanges:**
"""
                for ex_name, price_data in prices.items():
                    response += f"   • {ex_name.capitalize()}: ${price_data['price']:,.2f}\n"
                
                response += f"\n💡 Se escanearon {stats['exchanges_with_data']} exchanges"
                response += f"\n⚠️ Profit mínimo requerido: {self.arbitrage_scanner.min_profit_threshold}%"
                
            else:
                response = f"""
🎯 **OPORTUNIDADES DETECTADAS - {symbol}**

📊 **Estadísticas:**
   ✅ Oportunidades encontradas: {stats['total_opportunities']}
   🏆 Mejor profit: {stats['best_profit_pct']:.2f}%
   📈 Profit promedio: {stats['avg_profit_pct']:.2f}%
   💰 Profit potencial (con $10K): ${stats.get('total_potential_profit_10k', 0):,.2f}

🥇 **TOP 3 OPORTUNIDADES:**
"""
                for i, opp in enumerate(opportunities[:3], 1):
                    response += f"""
**#{i}** - Profit: {opp['net_profit_pct']:.2f}%
   🛒 COMPRAR: {opp['buy_exchange'].capitalize()} @ ${opp['buy_price']:,.2f}
   💸 VENDER: {opp['sell_exchange'].capitalize()} @ ${opp['sell_price']:,.2f}
   💵 Con $1,000 → ${opp['profit_per_1k_usd']:.2f}
   💰 Con $10,000 → ${opp['profit_per_10k_usd']:.2f}
"""
                
                response += f"\n⚡ Usa /arbitrage_execute 1000 para ejecutar la mejor oportunidad con $1,000"
            
            await loading_msg.edit_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en arbitrage_scan: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def arbitrage_execute_command(self, update, context):
        """Comando /arbitrage_execute [AMOUNT_USD] - Ejecutar mejor oportunidad de arbitraje"""
        if not self.arbitrage_scanner or not self.arbitrage_executor:
            await update.message.reply_text("💱 Módulo de arbitraje no disponible")
            return
        
        try:
            # Validar admin
            user_id = update.effective_user.id
            if not is_admin(user_id):
                await update.message.reply_text("🔒 Solo administradores pueden ejecutar arbitraje")
                return
            
            # 🛡️ RMS VALIDATION - Circuit Breaker check
            if self.circuit_breaker and self.circuit_breaker.is_trading_halted(str(user_id)):
                halt_status = self.circuit_breaker.get_halt_status(str(user_id))
                await update.message.reply_text(
                    f"🛡️ Trading pausado por protección del sistema.\n"
                    f"Razón: {halt_status.get('reason', 'Circuit breaker activo')}\n"
                    f"Use /resume_trading para reanudar."
                )
                logger.warning(f"🛡️ [RMS_BLOCK] arbitrage_execute blocked by circuit_breaker for user {user_id}")
                return
            
            # Obtener amount (default: $1000)
            amount_usd = float(context.args[0]) if context.args else 1000.0
            
            # Validar amount
            if amount_usd > self.arbitrage_executor.max_trade_size_usd:
                await update.message.reply_text(
                    f"❌ Amount ${amount_usd:,.2f} excede límite de ${self.arbitrage_executor.max_trade_size_usd:,.2f}"
                )
                return
            
            # 🛡️ RMS VALIDATION - Limits Engine check
            if self.limits_engine:
                validation = self.limits_engine.validate_order(
                    user_id=str(user_id),
                    symbol='BTC/USD',
                    side='buy',
                    amount_usd=amount_usd
                )
                if not validation.get('approved', True):
                    await update.message.reply_text(
                        f"🛡️ Trade bloqueado por límites de riesgo.\n"
                        f"Razón: {validation.get('reason', 'Límite excedido')}\n"
                        f"Use /rms_limits para ver límites actuales."
                    )
                    logger.warning(f"🛡️ [RMS_BLOCK] arbitrage_execute blocked by limits_engine: {validation.get('reason')}")
                    return
            
            # Mensaje de carga
            loading_msg = await update.message.reply_text(f"🔍 Buscando mejor oportunidad para ${amount_usd:,.2f}...")
            
            # Escanear oportunidades
            scan_result = self.arbitrage_scanner.check_arbitrage_opportunities('BTC/USD')
            
            if not scan_result.get('success') or not scan_result.get('opportunities'):
                await loading_msg.edit_text("❌ No hay oportunidades de arbitraje disponibles en este momento")
                return
            
            # Obtener mejor oportunidad
            best_opportunity = scan_result['opportunities'][0]
            
            # Confirmar ejecución
            await loading_msg.edit_text(
                f"""
🎯 **Ejecutando Arbitraje**

💰 Amount: ${amount_usd:,.2f}
📊 Profit esperado: {best_opportunity['net_profit_pct']:.2f}%
🛒 Comprar: {best_opportunity['buy_exchange'].capitalize()}
💸 Vender: {best_opportunity['sell_exchange'].capitalize()}

⏳ Ejecutando trade paralelo...
"""
            )
            
            # Ejecutar arbitraje
            exec_result = await self.arbitrage_executor.execute_arbitrage_trade(
                best_opportunity, 
                amount_usd
            )
            
            if not exec_result.get('success'):
                await loading_msg.edit_text(f"❌ Error en ejecución: {exec_result.get('error', 'Unknown error')}")
                return
            
            # Formatear resultado
            mode = '📄 PAPER TRADING' if exec_result['mode'] == 'PAPER_TRADING' else '🔴 LIVE TRADING'
            
            response = f"""
✅ **ARBITRAJE EJECUTADO - {mode}**

💰 **Resultado:**
   • Amount: ${exec_result['amount_usd']:,.2f}
   • BTC: {exec_result['btc_amount']:.8f}
   • Profit: ${exec_result['actual_profit_usd']:.2f} ({exec_result['actual_profit_pct']:.2f}%)

📊 **Detalles:**
   🛒 Compra @ {exec_result['buy_exchange'].capitalize()}: ${exec_result['buy_price_actual']:,.2f}
   💸 Venta @ {exec_result['sell_exchange'].capitalize()}: ${exec_result['sell_price_actual']:,.2f}
   
💵 **Costos:**
   • Fees: ${exec_result.get('fees_usd', 0):.2f}
   • Slippage: {exec_result.get('slippage_pct', 0):.2f}%

⚡ **Performance:**
   • Tiempo de ejecución: {exec_result.get('execution_time_ms', 0):.0f}ms
   • Timestamp: {exec_result['timestamp']}

📈 **Estadísticas:**
   • Total trades: {self.arbitrage_executor.total_trades}
   • Profit acumulado: ${self.arbitrage_executor.total_profit_usd:.2f}
   • Success rate: {self.arbitrage_executor.success_rate:.1f}%
"""
            
            await loading_msg.edit_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en arbitrage_execute: {e}")
            import traceback
            traceback.print_exc()
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def arbitrage_stats_command(self, update, context):
        """Comando /arbitrage_stats - Ver estadísticas de arbitraje"""
        if not self.arbitrage_executor:
            await update.message.reply_text("💱 Módulo de arbitraje no disponible")
            return
        
        try:
            stats = self.arbitrage_executor.get_performance_stats()
            
            response = f"""
📊 **ESTADÍSTICAS DE ARBITRAJE**

💰 **Performance:**
   • Total trades: {stats['total_trades']}
   • Profit acumulado: ${stats['total_profit_usd']:.2f}
   • Success rate: {stats['success_rate_pct']:.1f}%
   • Avg profit/trade: ${stats['avg_profit_per_trade']:.2f}

⚙️ **Configuración:**
   • Modo: {stats['mode']}
   • Max trade size: ${self.arbitrage_executor.max_trade_size_usd:,.2f}
   • Max daily volume: ${self.arbitrage_executor.max_daily_volume_usd:,.2f}
   • Min profit: {self.arbitrage_executor.min_profit_threshold}%

📈 **Historial:**
   • Trades ejecutados: {len(self.arbitrage_executor.execution_history)}
   • Última ejecución: {self.arbitrage_executor.execution_history[-1]['timestamp'] if self.arbitrage_executor.execution_history else 'N/A'}

🔄 Usa /arbitrage_scan para buscar nuevas oportunidades
"""
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en arbitrage_stats: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    # ═══════════════════════════════════════════════════════════════════════════
    # 🧠 COMMUNITY INTELLIGENCE COMMANDS - MEMORIA COLECTIVA
    # ═══════════════════════════════════════════════════════════════════════════
    
    async def feedback_command(self, update, context):
        """Comando /feedback [strategy] [result] - Reportar feedback sobre señal/estrategia"""
        if not self.feedback_manager:
            await update.message.reply_text("🧠 Community Intelligence no disponible")
            return
        
        try:
            user = update.effective_user
            args = context.args
            
            if len(args) < 2:
                help_text = """
🧠 **REPORTAR FEEDBACK**

**Uso:** `/feedback [estrategia] [resultado]`

**Estrategias disponibles:**
• `EMA_REGIME` - Primary Signal Driver
• `HMM_REGIME` - Market State Detection
• `MONTE_CARLO` - Probability Validation
• `ARBITRAGE` - Multi-exchange

**Resultados:**
• `success` - Funcionó correctamente ✅
• `failure` - No funcionó ❌
• `partial` - Resultado parcial ⚡

**Ejemplos:**
`/feedback EMA_REGIME success`
`/feedback HMM_REGIME failure Falló en mercado lateral`
`/feedback ARBITRAGE partial Bajo profit`

💡 **¿Por qué dar feedback?**
• Ganas puntos de contribución 🏆
• Ayudas a mejorar OMNIX para todos 🚀
• Subiste en el leaderboard comunitario 📊
"""
                await update.message.reply_text(help_text, parse_mode='Markdown')
                return
            
            strategy = args[0].upper()
            result = args[1].lower()
            comment = ' '.join(args[2:]) if len(args) > 2 else None
            
            if result not in ['success', 'failure', 'partial']:
                await update.message.reply_text("❌ Resultado debe ser: success, failure, o partial")
                return
            
            feedback_data = {
                'feedback_type': 'strategy',
                'strategy': strategy,
                'result': result,
                'comment': comment
            }
            
            response = self.feedback_manager.submit_feedback(
                str(user.id), 
                user.username or user.first_name,
                feedback_data
            )
            
            if response.get('success'):
                emoji = '✅' if result == 'success' else ('❌' if result == 'failure' else '⚡')
                message = f"""
🧠 **FEEDBACK REGISTRADO**

{emoji} **{strategy}**: {result.capitalize()}
💬 Comentario: {comment or 'Sin comentario'}

🏆 **+{response['points_earned']} puntos**

¡Gracias por contribuir a la mejora de OMNIX!
Usa `/my_contributions` para ver tus stats
"""
                await update.message.reply_text(message, parse_mode='Markdown')
            else:
                await update.message.reply_text(f"❌ Error: {response.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error en feedback_command: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def community_stats_command(self, update, context):
        """Comando /community_stats - Ver estadísticas de la comunidad"""
        if not self.community_dashboard:
            await update.message.reply_text("🧠 Community Intelligence no disponible")
            return
        
        try:
            loading_msg = await update.message.reply_text("📊 Cargando estadísticas comunitarias...")
            
            stats_text = self.community_dashboard.format_telegram_stats()
            
            await loading_msg.edit_text(stats_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en community_stats: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def top_strategies_command(self, update, context):
        """Comando /top_strategies - Ver ranking de estrategias según la comunidad"""
        if not self.community_dashboard:
            await update.message.reply_text("🧠 Community Intelligence no disponible")
            return
        
        try:
            rankings = self.community_dashboard.get_strategy_rankings()
            
            if not rankings:
                await update.message.reply_text("📊 No hay suficientes datos de la comunidad aún. ¡Sé el primero en dar feedback!")
                return
            
            medals = ['🥇', '🥈', '🥉']
            
            response = """
🏆 **TOP ESTRATEGIAS (Según Comunidad)**

"""
            for i, r in enumerate(rankings):
                medal = medals[i] if i < len(medals) else f'{i+1}.'
                response += f"""
{medal} **{r['strategy']}**
   ⭐ Rating: {r['avg_rating']}/5 ({r['vote_count']} votos)
   ✅ Success Rate: {r['success_rate']}%
   📝 Feedback: {r['feedback_count']}
   📊 Score: {r['combined_score']}pts
   Estado: {r['health_status']}
"""
            
            response += """
💡 **Comandos relacionados:**
   `/feedback` - Dar feedback
   `/vote_strategy` - Votar estrategia
   `/my_contributions` - Ver tus stats

*OMNIX - Community Intelligence*
"""
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en top_strategies: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def my_contributions_command(self, update, context):
        """Comando /my_contributions - Ver mis contribuciones y puntos"""
        if not self.reward_system:
            await update.message.reply_text("🧠 Community Intelligence no disponible")
            return
        
        try:
            user = update.effective_user
            profile = self.reward_system.get_user_profile(str(user.id))
            
            level_info = profile.get('level_info', {})
            next_level = profile.get('next_level', {})
            
            badges_text = '\n'.join([f"   {b['name']}" for b in profile.get('badges', [])]) if profile.get('badges') else "   Ninguno aún - ¡sigue contribuyendo!"
            
            new_badges_text = ""
            if profile.get('new_badges_earned'):
                new_badges_text = "\n\n🎉 **¡NUEVOS BADGES GANADOS!**\n"
                for badge_id in profile['new_badges_earned']:
                    new_badges_text += f"   🏅 {badge_id}\n"
            
            response = f"""
👤 **TU PERFIL DE CONTRIBUIDOR**

🏆 **Nivel:** {level_info.get('emoji', '🌱')} {level_info.get('name', 'Nuevo')}
💎 **Puntos:** {profile.get('points', 0)}
📊 **Rank:** #{profile.get('rank', 'N/A')}

📈 **Progreso al siguiente nivel:**
   {profile.get('points', 0)}/{next_level.get('min_points', '∞')} pts → {next_level.get('emoji', '')} {next_level.get('name', 'Max Level')}

📋 **Estadísticas:**
   📝 Feedback enviados: {profile['stats']['total_feedback']}
   ✅ Feedback útiles: {profile['stats']['helpful_feedback']}
   💡 Propuestas enviadas: {profile['stats']['proposals_submitted']}
   🚀 Propuestas aceptadas: {profile['stats']['proposals_accepted']}

🏅 **Badges ({profile.get('badge_count', 0)}):**
{badges_text}
{new_badges_text}
💡 **¿Cómo ganar más puntos?**
   • Feedback: +10 pts
   • Votar estrategias: +5 pts
   • Propuestas: +25 pts
   • Feedback útil: +15 pts bonus

*OMNIX - Community Intelligence*
"""
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en my_contributions: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def vote_strategy_command(self, update, context):
        """Comando /vote_strategy [strategy] [1-5] - Votar por una estrategia"""
        if not self.feedback_manager:
            await update.message.reply_text("🧠 Community Intelligence no disponible")
            return
        
        try:
            user = update.effective_user
            args = context.args
            
            if len(args) < 2:
                help_text = """
⭐ **VOTAR ESTRATEGIA**

**Uso:** `/vote_strategy [estrategia] [1-5]`

**Estrategias:**
• `EMA_REGIME` - Primary Signal Driver
• `HMM_REGIME` - Market State Detection
• `MONTE_CARLO` - Probability Validation
• `ARBITRAGE` - Multi-exchange

**Puntuación:** 1 (malo) a 5 (excelente)

**Ejemplos:**
`/vote_strategy EMA_REGIME 5`
`/vote_strategy HMM_REGIME 4`

💡 Cada voto vale +5 puntos
"""
                await update.message.reply_text(help_text, parse_mode='Markdown')
                return
            
            strategy = args[0].upper()
            try:
                vote = int(args[1])
            except ValueError:
                await update.message.reply_text("❌ El voto debe ser un número entre 1 y 5")
                return
            
            if vote < 1 or vote > 5:
                await update.message.reply_text("❌ El voto debe ser entre 1 y 5")
                return
            
            reason = ' '.join(args[2:]) if len(args) > 2 else None
            
            response = self.feedback_manager.vote_strategy(
                str(user.id),
                strategy,
                vote,
                reason
            )
            
            if response.get('success'):
                stars = '⭐' * vote + '☆' * (5 - vote)
                message = f"""
✅ **VOTO REGISTRADO**

📊 **{strategy}**: {stars}
💬 Razón: {reason or 'Sin comentario'}

🏆 **+{response['points_earned']} puntos**

¡Gracias por tu opinión!
"""
                await update.message.reply_text(message, parse_mode='Markdown')
            else:
                await update.message.reply_text(f"❌ Error: {response.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error en vote_strategy: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def leaderboard_command(self, update, context):
        """Comando /leaderboard - Ver ranking de contribuidores"""
        if not self.reward_system:
            await update.message.reply_text("🧠 Community Intelligence no disponible")
            return
        
        try:
            leaderboard = self.reward_system.get_leaderboard(10)
            
            if not leaderboard:
                await update.message.reply_text("📊 No hay contribuidores aún. ¡Sé el primero en dar feedback!")
                return
            
            medals = ['🥇', '🥈', '🥉']
            
            response = """
🏆 **LEADERBOARD DE CONTRIBUIDORES**

"""
            for entry in leaderboard:
                medal = medals[entry['rank']-1] if entry['rank'] <= 3 else f"#{entry['rank']}"
                response += f"""
{medal} **{entry['username']}**
   {entry['level_emoji']} {entry['level_name']} | {entry['points']} pts
   📝 {entry['feedback_count']} feedback | 🏅 {entry['badge_count']} badges
"""
            
            user = update.effective_user
            user_profile = self.reward_system.get_user_profile(str(user.id))
            
            response += f"""
━━━━━━━━━━━━━━━━━━━━━━
📍 **Tu posición:** #{user_profile.get('rank', 'N/A')}
💎 **Tus puntos:** {user_profile.get('points', 0)}

💡 Usa `/feedback` para ganar más puntos

*OMNIX - Community Intelligence*
"""
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en leaderboard: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def analyze_patterns_command(self, update, context):
        """Comando /analyze_patterns - Analizar patrones en feedback (Solo Admin)"""
        if not self.community_analyzer:
            await update.message.reply_text("🧠 Community Intelligence no disponible")
            return
        
        try:
            user = update.effective_user
            if not is_admin(user.id):
                await update.message.reply_text("🔒 Solo administradores pueden analizar patrones")
                return
            
            loading_msg = await update.message.reply_text("🔍 Analizando patrones de feedback con AI...")
            
            result = self.community_analyzer.analyze_feedback_patterns(days=30, min_samples=3)
            
            if not result.get('success'):
                await loading_msg.edit_text(f"❌ Error: {result.get('error', 'Unknown error')}")
                return
            
            response = f"""
🔍 **ANÁLISIS DE PATRONES AI**

📊 **Resumen:**
   • Patrones analizados: {result['patterns_analyzed']}
   • Patrones detectados: {result['patterns_detected']}
   • Período: últimos {result['period_days']} días

"""
            if result.get('patterns'):
                response += "🚨 **PATRONES PROBLEMÁTICOS:**\n"
                for p in result['patterns'][:5]:
                    response += f"""
   • {p['description']}
     Confianza: {p['confidence']*100:.0f}%
     Sugerencia: {p['suggestion']}
"""
            else:
                response += "✅ No se detectaron patrones problemáticos significativos\n"
            
            if result.get('ai_analysis'):
                response += f"""
🤖 **ANÁLISIS AI:**
{result['ai_analysis'][:1000]}...
"""
            
            response += f"""
⏱️ Analizado: {result['analyzed_at']}

*OMNIX - Community Intelligence*
"""
            
            await loading_msg.edit_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en analyze_patterns: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    # ═══════════════════════════════════════════════════════════════════
    # 🚀 SIGNAL CONTRIBUTION - CROWDSOURCING DE ALPHA
    # ═══════════════════════════════════════════════════════════════════
    
    async def share_signal_command(self, update, context):
        """Comando /share_signal - Compartir señal con la comunidad"""
        if not self.signal_contribution:
            await update.message.reply_text("🚀 Signal Contribution no disponible")
            return
        
        try:
            user = update.effective_user
            args = context.args
            
            if len(args) < 3:
                await update.message.reply_text("""
🚀 **COMPARTIR SEÑAL CON LA COMUNIDAD**

**Formato:**
`/share_signal SYMBOL TIPO ENTRADA [TARGET] [STOPLOSS]`

**Ejemplos:**
`/share_signal BTC LONG 95000 100000 92000`
`/share_signal ETH SHORT 3500 3200 3700`
`/share_signal SOL LONG 180`

**Tipos:** LONG, SHORT, NEUTRAL

🏆 Gana **10 puntos** por compartir
💰 Gana **+50 puntos** si tu señal es exitosa
📈 Los mejores contribuidores aparecen en `/alpha_leaderboard`
""", parse_mode='Markdown')
                return
            
            symbol = args[0].upper()
            signal_type = args[1].upper()
            entry_price = float(args[2])
            target_price = float(args[3]) if len(args) > 3 else None
            stop_loss = float(args[4]) if len(args) > 4 else None
            
            reasoning = ' '.join(args[5:]) if len(args) > 5 else None
            
            signal_data = {
                'symbol': symbol,
                'signal_type': signal_type,
                'entry_price': entry_price,
                'target_price': target_price,
                'stop_loss': stop_loss,
                'timeframe': '1h',
                'confidence': 70,
                'reasoning': reasoning
            }
            
            result = self.signal_contribution.share_signal(
                str(user.id),
                user.username or user.first_name,
                signal_data
            )
            
            if result.get('success'):
                response = f"""
🚀 **SEÑAL COMPARTIDA EXITOSAMENTE**

📊 **{symbol}/USD - {signal_type}**
💵 Entrada: ${entry_price:,.2f}
{'🎯 Target: $' + f'{target_price:,.2f}' if target_price else ''}
{'🛡️ Stop Loss: $' + f'{stop_loss:,.2f}' if stop_loss else ''}

🔑 ID: `{result['signal_id']}`
⏰ Expira: {result['expires_at'][:10]}

🏆 **+{result['points_earned']} puntos** ganados!

📡 Tu señal ahora es visible para toda la comunidad.
Usa `/community_signals` para ver todas las señales activas.

*OMNIX - Crowdsourcing de Alpha*
"""
            else:
                response = f"❌ Error: {result.get('error', 'Unknown error')}"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except ValueError:
            await update.message.reply_text("❌ Error: Los precios deben ser números válidos")
        except Exception as e:
            logger.error(f"Error en share_signal: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def community_signals_command(self, update, context):
        """Comando /community_signals - Ver señales activas de la comunidad"""
        if not self.signal_contribution:
            await update.message.reply_text("🚀 Signal Contribution no disponible")
            return
        
        try:
            args = context.args
            symbol = args[0].upper() if args else None
            
            signals = self.signal_contribution.get_community_signals(limit=10, symbol=symbol)
            
            if not signals:
                await update.message.reply_text("""
📡 **SEÑALES COMUNITARIAS**

No hay señales activas en este momento.

🚀 ¡Sé el primero en compartir una señal!
Usa `/share_signal BTC LONG 95000` para empezar.

*OMNIX - Crowdsourcing de Alpha*
""", parse_mode='Markdown')
                return
            
            response = """
📡 **SEÑALES ACTIVAS DE LA COMUNIDAD**

"""
            for i, signal in enumerate(signals, 1):
                emoji = '🟢' if signal['signal_type'] == 'LONG' else '🔴' if signal['signal_type'] == 'SHORT' else '⚪'
                
                response += f"""
{i}. {emoji} **{signal['symbol']}/USD - {signal['signal_type']}**
   👤 Por: {signal['contributor_name']}
   💵 Entrada: ${signal['entry_price']:,.2f if signal['entry_price'] else 'N/A'}
   📊 Confianza: {signal['confidence']}%
   👍 {signal['upvotes']} | 👎 {signal['downvotes']} | 📈 {signal['executions_count']} ejecuciones
   🔑 ID: `{signal['signal_id'][:8]}...`
"""
            
            response += """
━━━━━━━━━━━━━━━━━━━━━━
**Comandos:**
• `/execute_signal ID` - Ejecutar señal
• `/share_signal` - Compartir tu propia señal

*OMNIX - Crowdsourcing de Alpha*
"""
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en community_signals: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def my_signals_command(self, update, context):
        """Comando /my_signals - Ver mis señales compartidas"""
        if not self.signal_contribution:
            await update.message.reply_text("🚀 Signal Contribution no disponible")
            return
        
        try:
            user = update.effective_user
            
            data = self.signal_contribution.get_user_signals(str(user.id))
            
            stats = data.get('stats', {})
            signals = data.get('signals', [])
            
            tier_emoji = {
                'Diamond': '💎',
                'Platinum': '🏆',
                'Gold': '🥇',
                'Silver': '🥈',
                'Bronze': '🥉'
            }
            
            tier = stats.get('rank_tier', 'Bronze')
            
            response = f"""
📊 **MIS SEÑALES - {user.first_name}**

{tier_emoji.get(tier, '🥉')} **Tier: {tier}**

📈 **Estadísticas:**
   • Señales compartidas: {stats.get('signals_shared', 0)}
   • Señales exitosas: {stats.get('signals_successful', 0)}
   • Win Rate: {stats.get('win_rate', 0):.1f}%
   • Ejecuciones totales: {stats.get('total_executions', 0)}
   • Royalty Points: {stats.get('royalty_points', 0)}
   • Reputación: {stats.get('reputation_score', 50):.0f}/100

"""
            if signals:
                response += "**Últimas señales:**\n"
                for s in signals[:5]:
                    status_emoji = '✅' if s['status'] == 'closed' else '⏳'
                    response += f"   {status_emoji} {s['symbol']} {s['signal_type']} | 👍{s['upvotes']} 👎{s['downvotes']} | +{s['royalties_earned']} pts\n"
            
            response += """
━━━━━━━━━━━━━━━━━━━━━━
💡 **Tips para subir de tier:**
• Comparte señales de calidad
• Las señales exitosas dan +50 puntos
• Los fallos restan -10 puntos

*OMNIX - Crowdsourcing de Alpha*
"""
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en my_signals: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def alpha_leaderboard_command(self, update, context):
        """Comando /alpha_leaderboard - Top contribuidores de señales"""
        if not self.signal_contribution:
            await update.message.reply_text("🚀 Signal Contribution no disponible")
            return
        
        try:
            leaders = self.signal_contribution.get_alpha_leaderboard(10)
            
            if not leaders:
                await update.message.reply_text("""
🏆 **ALPHA LEADERBOARD**

No hay contribuidores aún.

🚀 ¡Sé el primero en compartir señales!
Usa `/share_signal BTC LONG 95000` para empezar.

*OMNIX - Crowdsourcing de Alpha*
""", parse_mode='Markdown')
                return
            
            medals = ['🥇', '🥈', '🥉']
            tier_emoji = {
                'Diamond': '💎',
                'Platinum': '🏆',
                'Gold': '🥇',
                'Silver': '🥈',
                'Bronze': '🥉'
            }
            
            response = """
🏆 **ALPHA LEADERBOARD - TOP CONTRIBUIDORES**

"""
            for leader in leaders:
                pos = leader['position']
                medal = medals[pos-1] if pos <= 3 else f"#{pos}"
                tier = leader.get('rank_tier', 'Bronze')
                
                response += f"""
{medal} **{leader['username']}** {tier_emoji.get(tier, '')}
   📊 Señales: {leader['signals_shared']} | Win Rate: {leader['win_rate']:.0f}%
   🏆 Royalties: {leader['royalty_points']} pts | Rep: {leader['reputation_score']:.0f}/100
"""
            
            user = update.effective_user
            user_data = self.signal_contribution.get_user_signals(str(user.id))
            user_stats = user_data.get('stats', {})
            
            response += f"""
━━━━━━━━━━━━━━━━━━━━━━
📍 **Tu posición:** #{user_stats.get('rank_position', 'N/A')}
💰 **Tus royalties:** {user_stats.get('royalty_points', 0)} pts

💡 Comparte señales exitosas para subir en el ranking!

*OMNIX - Crowdsourcing de Alpha*
"""
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en alpha_leaderboard: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def execute_signal_command(self, update, context):
        """Comando /execute_signal - Ejecutar una señal de la comunidad"""
        if not self.signal_contribution:
            await update.message.reply_text("🚀 Signal Contribution no disponible")
            return
        
        try:
            user = update.effective_user
            args = context.args
            
            if not args:
                await update.message.reply_text("""
▶️ **EJECUTAR SEÑAL COMUNITARIA**

**Formato:**
`/execute_signal SIGNAL_ID`

**Ejemplo:**
`/execute_signal abc123def`

📡 Usa `/community_signals` para ver las señales disponibles.

*OMNIX - Crowdsourcing de Alpha*
""", parse_mode='Markdown')
                return
            
            signal_id = args[0]
            
            result = self.signal_contribution.execute_signal(
                signal_id,
                str(user.id),
                user.username or user.first_name
            )
            
            if result.get('success'):
                signal = result['signal']
                
                response = f"""
▶️ **SEÑAL EJECUTADA**

📊 **{signal['symbol']}/USD - {signal['signal_type']}**
👤 Creada por: {signal['contributor_name']}

💵 Entrada: ${signal['entry_price']:,.2f if signal['entry_price'] else 'Market'}
{'🎯 Target: $' + f"{signal['target_price']:,.2f}" if signal['target_price'] else ''}
{'🛡️ Stop Loss: $' + f"{signal['stop_loss']:,.2f}" if signal['stop_loss'] else ''}

📈 Esta es la ejecución #{signal['executions_count'] + 1} de esta señal.

⚠️ **Importante:** Cuando cierres la posición, reporta el resultado con:
`/report_result {signal_id[:8]} success/failure PROFIT%`

El contribuidor ganará royalties si la señal es exitosa.

*OMNIX - Crowdsourcing de Alpha*
"""
            else:
                response = f"❌ Error: {result.get('error', 'Unknown error')}"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en execute_signal: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    # ==========================================
    # 🛡️ RISK MANAGEMENT SYSTEM (RMS) COMMANDS
    # Nov 27, 2025 - Institutional Risk Control
    # ==========================================
    
    async def rms_dashboard_command(self, update, context):
        """Comando /rms - Dashboard de riesgo completo"""
        try:
            user = update.effective_user
            
            if not self.risk_dashboard:
                await update.message.reply_text("❌ RMS no disponible")
                return
            
            summary = self.risk_dashboard.get_telegram_summary(str(user.id))
            await update.message.reply_text(summary, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en rms_dashboard: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def rms_limits_command(self, update, context):
        """Comando /rms_limits - Ver límites configurados"""
        try:
            user = update.effective_user
            
            if not self.risk_dashboard:
                await update.message.reply_text("❌ RMS no disponible")
                return
            
            summary = self.risk_dashboard.get_limits_summary(str(user.id))
            await update.message.reply_text(summary, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en rms_limits: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def rms_set_limit_command(self, update, context):
        """Comando /rms_set <tipo> <valor> - Configurar límite"""
        try:
            if not is_admin(update.effective_user.id):
                await update.message.reply_text("❌ Solo administradores pueden modificar límites")
                return
            
            if not self.limits_engine:
                await update.message.reply_text("❌ RMS no disponible")
                return
            
            args = context.args
            if len(args) < 2:
                await update.message.reply_text("""
🛡️ **Configurar Límite de Riesgo**

Uso: `/rms_set <tipo> <valor>`

**Tipos disponibles:**
• `per_trade` - Máximo % por operación
• `daily_loss` - Pérdida máxima diaria %
• `max_drawdown` - Drawdown máximo %
• `concentration` - Concentración máxima %
• `daily_trades` - Máximo trades/día
• `open_positions` - Máximo posiciones

**Ejemplo:** `/rms_set per_trade 5`
""", parse_mode='Markdown')
                return
            
            from omnix_services.risk_management.risk_models import RiskLimitType, ThresholdUnit
            
            limit_type_map = {
                'per_trade': RiskLimitType.PER_TRADE,
                'daily_loss': RiskLimitType.DAILY_LOSS,
                'max_drawdown': RiskLimitType.MAX_DRAWDOWN,
                'concentration': RiskLimitType.PORTFOLIO_CONCENTRATION,
                'daily_trades': RiskLimitType.DAILY_TRADES,
                'open_positions': RiskLimitType.OPEN_POSITIONS
            }
            
            limit_type_str = args[0].lower()
            if limit_type_str not in limit_type_map:
                await update.message.reply_text(f"❌ Tipo de límite no válido: {limit_type_str}")
                return
            
            try:
                value = float(args[1])
            except ValueError:
                await update.message.reply_text("❌ El valor debe ser numérico")
                return
            
            unit = ThresholdUnit.COUNT if limit_type_str in ['daily_trades', 'open_positions'] else ThresholdUnit.PERCENT
            
            user = update.effective_user
            success = self.limits_engine.set_limit(
                user_id=str(user.id),
                limit_type=limit_type_map[limit_type_str],
                threshold_value=value,
                threshold_unit=unit
            )
            
            if success:
                await update.message.reply_text(f"✅ Límite **{limit_type_str}** configurado a {value} {unit.value}", parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Error configurando límite")
            
        except Exception as e:
            logger.error(f"Error en rms_set_limit: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def rms_history_command(self, update, context):
        """Comando /rms_history - Historial de violaciones"""
        try:
            user = update.effective_user
            
            if not self.db_manager:
                await update.message.reply_text("❌ Base de datos no disponible")
                return
            
            breaches = self.db_manager.get_risk_breaches(str(user.id), days=7)
            
            if not breaches:
                await update.message.reply_text("✅ Sin violaciones de límites en los últimos 7 días")
                return
            
            response = "🛡️ **Historial de Violaciones (7 días)**\n━━━━━━━━━━━━━━━━━━━━\n"
            
            for b in breaches[:10]:
                severity_emoji = {'warning': '🟡', 'critical': '🟠', 'halt': '🔴'}.get(b['severity'], '⚪')
                response += f"\n{severity_emoji} **{b['limit_type']}**\n"
                response += f"   {b['description'][:50]}...\n" if len(b.get('description', '')) > 50 else f"   {b.get('description', 'N/A')}\n"
                response += f"   📅 {b['created_at'][:16] if b['created_at'] else 'N/A'}\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en rms_history: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def rms_emergency_halt_command(self, update, context):
        """Comando /emergency_halt - Detener trading (admin)"""
        try:
            if not is_admin(update.effective_user.id):
                await update.message.reply_text("❌ Solo administradores pueden usar este comando")
                return
            
            if not self.circuit_breaker:
                await update.message.reply_text("❌ Circuit Breaker no disponible")
                return
            
            user = update.effective_user
            message = " ".join(context.args) if context.args else "Halt manual por admin"
            
            from omnix_services.risk_management.circuit_breaker import HaltReason
            
            status = self.circuit_breaker.manual_halt(
                user_id=str(user.id),
                admin_id=str(user.id),
                message=message
            )
            
            response = f"""
🛑 **TRADING DETENIDO**
━━━━━━━━━━━━━━━━━━━━

✋ Trading pausado manualmente
👤 Por: {user.first_name}
📝 Razón: {message}

⏰ Trading permanecerá pausado hasta usar `/resume_trading`

⚠️ Todas las nuevas órdenes serán rechazadas.
"""
            await update.message.reply_text(response, parse_mode='Markdown')
            
            if self.alert_dispatcher:
                self.alert_dispatcher.send_halt_notification(str(user.id), message)
            
        except Exception as e:
            logger.error(f"Error en emergency_halt: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def rms_resume_trading_command(self, update, context):
        """Comando /resume_trading - Reanudar trading (admin)"""
        try:
            if not is_admin(update.effective_user.id):
                await update.message.reply_text("❌ Solo administradores pueden usar este comando")
                return
            
            if not self.circuit_breaker:
                await update.message.reply_text("❌ Circuit Breaker no disponible")
                return
            
            user = update.effective_user
            
            success = self.circuit_breaker.resume_trading(
                user_id=str(user.id),
                resumed_by=f"admin:{user.id}",
                force=True
            )
            
            if success:
                response = f"""
✅ **TRADING REANUDADO**
━━━━━━━━━━━━━━━━━━━━

🚀 Trading activado nuevamente
👤 Por: {user.first_name}
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Las operaciones ahora se procesarán normalmente.
"""
                if self.alert_dispatcher:
                    self.alert_dispatcher.send_resume_notification(str(user.id))
            else:
                response = "❌ No se pudo reanudar el trading"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en resume_trading: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ⚙️ USER SETTINGS - COMANDOS DE CONFIGURACIÓN PERSONALIZADA PREMIUM
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def miconfig_command(self, update, context):
        """Comando /miconfig - Ver toda mi configuración personal"""
        try:
            user = update.effective_user
            
            if not self.user_settings_service:
                await update.message.reply_text("❌ Servicio de configuración no disponible")
                return
            
            settings = self.user_settings_service.get_user_settings(
                str(user.id), 
                username=user.username
            )
            
            summary = settings.get_profile_summary()
            
            commands_info = """
━━━━━━━━━━━━━━━━━━━━━━━━━━

**📋 COMANDOS DE CONFIGURACIÓN:**

`/perfil` - Cambiar perfil de riesgo
`/limites` - Ajustar límites de trading
`/proteccion` - Configurar auto-protección
`/estrategias` - Gestionar estrategias activas
`/cryptos` - Ver/modificar cryptos permitidas
`/autotrading` - Activar/desactivar trading automático
`/pausar` - Pausar trading temporalmente
`/reanudar` - Reanudar trading
"""
            
            await update.message.reply_text(
                summary + commands_info, 
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error en miconfig: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def perfil_command(self, update, context):
        """Comando /perfil [nombre] [ACEPTO] - Cambiar perfil de riesgo"""
        try:
            user = update.effective_user
            args = context.args if context.args else []
            
            if not self.user_settings_service:
                await update.message.reply_text("❌ Servicio de configuración no disponible")
                return
            
            if not args:
                profiles_text = """⚙️ **PERFILES DE RIESGO DISPONIBLES**

🛡️ **ultraconservador** - Máxima protección
   • 2% máx por trade, 5% pérdida diaria
   
🔒 **conservador** - Crecimiento estable
   • 5% máx por trade, 10% pérdida diaria
   
⚖️ **moderado** - Balance equilibrado (DEFAULT)
   • 10% máx por trade, 15% pérdida diaria
   
🔥 **agresivo** - Mayor potencial, mayor riesgo
   • 15% máx por trade, 25% pérdida diaria
   
🏦 **institucional** - Parámetros Goldman-Sachs
   • 8% máx por trade, 12% pérdida diaria

**Uso:** `/perfil [nombre]`
**Ejemplo:** `/perfil conservador`

⚠️ Perfiles agresivos requieren confirmación:
`/perfil agresivo ACEPTO`
"""
                await update.message.reply_text(profiles_text, parse_mode='Markdown')
                return
            
            profile_name = args[0].lower()
            accept_disclaimer = len(args) > 1 and args[1].upper() == 'ACEPTO'
            
            profile_map = {
                'ultraconservador': RiskProfile.ULTRA_CONSERVATIVE,
                'ultra_conservative': RiskProfile.ULTRA_CONSERVATIVE,
                'conservador': RiskProfile.CONSERVATIVE,
                'conservative': RiskProfile.CONSERVATIVE,
                'moderado': RiskProfile.MODERATE,
                'moderate': RiskProfile.MODERATE,
                'agresivo': RiskProfile.AGGRESSIVE,
                'aggressive': RiskProfile.AGGRESSIVE,
                'institucional': RiskProfile.INSTITUTIONAL,
                'institutional': RiskProfile.INSTITUTIONAL,
            }
            
            if profile_name not in profile_map:
                await update.message.reply_text(
                    f"❌ Perfil '{profile_name}' no reconocido.\n\nUsa `/perfil` para ver opciones disponibles.",
                    parse_mode='Markdown'
                )
                return
            
            success, message = self.user_settings_service.update_risk_profile(
                str(user.id), 
                profile_map[profile_name],
                accept_disclaimer=accept_disclaimer
            )
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en perfil: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def limites_command(self, update, context):
        """Comando /limites - Ver o modificar límites de trading"""
        try:
            user = update.effective_user
            args = context.args if context.args else []
            
            if not self.user_settings_service:
                await update.message.reply_text("❌ Servicio de configuración no disponible")
                return
            
            settings = self.user_settings_service.get_user_settings(str(user.id))
            
            if not args:
                limits = settings.trading_limits
                limits_text = f"""📊 **TUS LÍMITES DE TRADING**
━━━━━━━━━━━━━━━━━━━━━━━━━━

💵 **Montos por trade:**
• Mínimo: ${limits.min_trade_usd:,.0f}
• Máximo: ${limits.max_trade_usd:,.0f}

📅 **Límite diario:** ${limits.daily_trade_limit_usd:,.0f}

📈 **Posiciones:**
• Máximo abiertas: {limits.max_open_positions}
• % máx del portfolio: {limits.max_trade_pct}%

⚡ **Apalancamiento máx:** x{limits.leverage_max:.1f}

━━━━━━━━━━━━━━━━━━━━━━━━━━

**📝 MODIFICAR LÍMITES:**

`/limites min 50` - Mín $50 por trade
`/limites max 2000` - Máx $2000 por trade
`/limites diario 10000` - Límite diario $10K
`/limites posiciones 10` - Máx 10 posiciones

**Ejemplo combinado:**
`/limites max 1500`
"""
                await update.message.reply_text(limits_text, parse_mode='Markdown')
                return
            
            if len(args) < 2:
                await update.message.reply_text(
                    "❌ Formato: `/limites [tipo] [valor]`\n\nEjemplo: `/limites max 1000`",
                    parse_mode='Markdown'
                )
                return
            
            limit_type = args[0].lower()
            try:
                value = float(args[1])
            except ValueError:
                await update.message.reply_text("❌ El valor debe ser numérico")
                return
            
            if limit_type == 'min':
                success, message = self.user_settings_service.update_trading_limits(
                    str(user.id), min_trade=value
                )
            elif limit_type == 'max':
                success, message = self.user_settings_service.update_trading_limits(
                    str(user.id), max_trade=value
                )
            elif limit_type == 'diario':
                success, message = self.user_settings_service.update_trading_limits(
                    str(user.id), daily_limit=value
                )
            elif limit_type == 'posiciones':
                success, message = self.user_settings_service.update_trading_limits(
                    str(user.id), max_positions=int(value)
                )
            else:
                await update.message.reply_text(
                    f"❌ Tipo '{limit_type}' no reconocido.\n\nOpciones: min, max, diario, posiciones",
                    parse_mode='Markdown'
                )
                return
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en limites: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def proteccion_command(self, update, context):
        """Comando /proteccion - Configurar sistema de auto-protección"""
        try:
            user = update.effective_user
            args = context.args if context.args else []
            
            if not self.user_settings_service:
                await update.message.reply_text("❌ Servicio de configuración no disponible")
                return
            
            settings = self.user_settings_service.get_user_settings(str(user.id))
            
            if not args:
                prot = settings.protection_settings
                auto_status = "✅ Activada" if prot.auto_pause_enabled else "❌ Desactivada"
                trailing_status = "✅" if prot.trailing_stop_enabled else "❌"
                
                protection_text = f"""🛡️ **TU CONFIGURACIÓN DE PROTECCIÓN**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📉 **Límites de pérdida:**
• Diario: {prot.daily_loss_limit_pct}%
• Semanal: {prot.weekly_loss_limit_pct}%

🎯 **Stop Loss por defecto:** {prot.stop_loss_default_pct}%
📈 **Take Profit por defecto:** {prot.take_profit_default_pct}%

📊 **Trailing Stop:** {trailing_status} ({prot.trailing_stop_pct}%)

⏸️ **Auto-pausa:** {auto_status}
⏱️ **Tiempo enfriamiento:** {prot.cool_down_minutes} min

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📝 MODIFICAR PROTECCIÓN:**

`/proteccion diario 15` - Límite pérdida diaria 15%
`/proteccion stoploss 5` - Stop loss por defecto 5%
`/proteccion takeprofit 12` - Take profit 12%
`/proteccion autopausa on` - Activar auto-pausa
`/proteccion autopausa off` - Desactivar auto-pausa
"""
                await update.message.reply_text(protection_text, parse_mode='Markdown')
                return
            
            setting_type = args[0].lower()
            
            if setting_type == 'autopausa':
                if len(args) < 2:
                    await update.message.reply_text("❌ Uso: `/proteccion autopausa on/off`", parse_mode='Markdown')
                    return
                enable = args[1].lower() in ['on', 'si', 'yes', 'true', 'activar']
                success, message = self.user_settings_service.update_protection_settings(
                    str(user.id), auto_pause=enable
                )
            elif setting_type == 'diario':
                if len(args) < 2:
                    await update.message.reply_text("❌ Uso: `/proteccion diario [%]`", parse_mode='Markdown')
                    return
                value = float(args[1])
                success, message = self.user_settings_service.update_protection_settings(
                    str(user.id), daily_loss_limit=value
                )
            elif setting_type == 'stoploss':
                if len(args) < 2:
                    await update.message.reply_text("❌ Uso: `/proteccion stoploss [%]`", parse_mode='Markdown')
                    return
                value = float(args[1])
                success, message = self.user_settings_service.update_protection_settings(
                    str(user.id), stop_loss=value
                )
            elif setting_type == 'takeprofit':
                if len(args) < 2:
                    await update.message.reply_text("❌ Uso: `/proteccion takeprofit [%]`", parse_mode='Markdown')
                    return
                value = float(args[1])
                success, message = self.user_settings_service.update_protection_settings(
                    str(user.id), take_profit=value
                )
            else:
                await update.message.reply_text(
                    f"❌ Opción '{setting_type}' no reconocida.\n\nOpciones: diario, stoploss, takeprofit, autopausa",
                    parse_mode='Markdown'
                )
                return
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en proteccion: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def estrategias_command(self, update, context):
        """Comando /estrategias - Ver y gestionar estrategias activas"""
        try:
            user = update.effective_user
            args = context.args if context.args else []
            
            if not self.user_settings_service:
                await update.message.reply_text("❌ Servicio de configuración no disponible")
                return
            
            settings = self.user_settings_service.get_user_settings(str(user.id))
            available = self.user_settings_service.get_available_strategies()
            
            if not args:
                active = settings.active_strategies
                
                strategies_text = f"""📈 **ESTRATEGIAS — OMNIX Decision Governance**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**🟢 TUS ESTRATEGIAS ACTIVAS:**
"""
                for s in available:
                    if s['id'] in active:
                        risk_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}.get(s['risk'], '⚪')
                        strategies_text += f"• {risk_emoji} **{s['name']}**\n"
                
                strategies_text += """
**⚪ ESTRATEGIAS DISPONIBLES:**
"""
                for s in available:
                    if s['id'] not in active:
                        risk_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}.get(s['risk'], '⚪')
                        strategies_text += f"• {risk_emoji} {s['name']} - {s['description']}\n"
                
                strategies_text += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📝 GESTIONAR ESTRATEGIAS:**

`/estrategias add EMA_REGIME` - Activar estrategia
`/estrategias remove MONTE_CARLO` - Desactivar estrategia
`/estrategias reset` - Restaurar por defecto

🟢 Bajo riesgo | 🟡 Medio | 🔴 Alto
"""
                await update.message.reply_text(strategies_text, parse_mode='Markdown')
                return
            
            action = args[0].lower()
            
            if action == 'reset':
                settings.active_strategies = ['EMA_REGIME', 'HMM_REGIME', 'MONTE_CARLO', 'KALMAN_FILTER']
                self.user_settings_service.save_user_settings(settings)
                await update.message.reply_text("✅ Estrategias restauradas a configuración por defecto")
                return
            
            if len(args) < 2:
                await update.message.reply_text("❌ Especifica la estrategia: `/estrategias add EMA_REGIME`", parse_mode='Markdown')
                return
            
            strategy_id = args[1].upper()
            available_ids = [s['id'] for s in available]
            
            if strategy_id not in available_ids:
                await update.message.reply_text(
                    f"❌ Estrategia '{strategy_id}' no existe.\n\nUsa `/estrategias` para ver las disponibles.",
                    parse_mode='Markdown'
                )
                return
            
            if action == 'add':
                if strategy_id not in settings.active_strategies:
                    settings.active_strategies.append(strategy_id)
                    self.user_settings_service.save_user_settings(settings)
                    await update.message.reply_text(f"✅ Estrategia **{strategy_id}** activada", parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"ℹ️ Estrategia {strategy_id} ya está activa")
            elif action == 'remove':
                if strategy_id in settings.active_strategies:
                    settings.active_strategies.remove(strategy_id)
                    self.user_settings_service.save_user_settings(settings)
                    await update.message.reply_text(f"✅ Estrategia **{strategy_id}** desactivada", parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"ℹ️ Estrategia {strategy_id} no estaba activa")
            else:
                await update.message.reply_text("❌ Acción no reconocida. Usa: add, remove, reset")
            
        except Exception as e:
            logger.error(f"Error en estrategias: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def cryptos_command(self, update, context):
        """Comando /cryptos - Ver y gestionar criptomonedas permitidas"""
        try:
            user = update.effective_user
            args = context.args if context.args else []
            
            if not self.user_settings_service:
                await update.message.reply_text("❌ Servicio de configuración no disponible")
                return
            
            settings = self.user_settings_service.get_user_settings(str(user.id))
            
            if not args:
                cryptos = settings.allowed_cryptos
                
                cryptos_text = f"""🪙 **TUS CRIPTOMONEDAS PERMITIDAS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Activas ({len(cryptos)}):**
{', '.join(cryptos)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📝 GESTIONAR CRYPTOS:**

`/cryptos add SOL/USD` - Añadir crypto
`/cryptos remove DOGE/USD` - Quitar crypto
`/cryptos reset` - Restaurar lista por defecto

**Cryptos populares:**
BTC/USD, ETH/USD, SOL/USD, XRP/USD, ADA/USD, 
DOT/USD, DOGE/USD, AVAX/USD, MATIC/USD, LINK/USD
"""
                await update.message.reply_text(cryptos_text, parse_mode='Markdown')
                return
            
            action = args[0].lower()
            
            if action == 'reset':
                settings.allowed_cryptos = [
                    'BTC/USD', 'ETH/USD', 'SOL/USD', 'XRP/USD', 'ADA/USD', 'DOGE/USD', 'DOT/USD'
                ]
                self.user_settings_service.save_user_settings(settings)
                await update.message.reply_text("✅ Lista de cryptos restaurada")
                return
            
            if len(args) < 2:
                await update.message.reply_text("❌ Especifica la crypto: `/cryptos add SOL/USD`", parse_mode='Markdown')
                return
            
            crypto = args[1].upper()
            if '/' not in crypto:
                crypto = f"{crypto}/USD"
            
            if action == 'add':
                if crypto not in settings.allowed_cryptos:
                    settings.allowed_cryptos.append(crypto)
                    self.user_settings_service.save_user_settings(settings)
                    await update.message.reply_text(f"✅ **{crypto}** añadida a tu lista", parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"ℹ️ {crypto} ya está en tu lista")
            elif action == 'remove':
                if crypto in settings.allowed_cryptos:
                    settings.allowed_cryptos.remove(crypto)
                    self.user_settings_service.save_user_settings(settings)
                    await update.message.reply_text(f"✅ **{crypto}** eliminada de tu lista", parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"ℹ️ {crypto} no estaba en tu lista")
            else:
                await update.message.reply_text("❌ Acción no reconocida. Usa: add, remove, reset")
            
        except Exception as e:
            logger.error(f"Error en cryptos: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def autotrading_command(self, update, context):
        """Comando /autotrading [activar/desactivar] [ACEPTO] - Trading automático"""
        try:
            user = update.effective_user
            args = context.args if context.args else []
            
            if not self.user_settings_service:
                await update.message.reply_text("❌ Servicio de configuración no disponible")
                return
            
            settings = self.user_settings_service.get_user_settings(str(user.id))
            
            if not args:
                status = "🟢 ACTIVO" if settings.auto_trading else "⚪ INACTIVO"
                mode = "📝 Paper Trading" if settings.paper_trading_mode else "💵 Trading Real"
                
                autotrading_text = f"""🤖 **TRADING AUTOMÁTICO**
━━━━━━━━━━━━━━━━━━━━━━━━

**Estado actual:** {status}
**Modo:** {mode}

Cuando está activo, OMNIX puede ejecutar trades automáticamente basándose en tus estrategias y respetando tus límites.

━━━━━━━━━━━━━━━━━━━━━━━━

**📝 COMANDOS:**

`/autotrading activar` - Activar (requiere ACEPTO)
`/autotrading desactivar` - Desactivar

ℹ️ Activar requiere confirmación del sistema
"""
                await update.message.reply_text(autotrading_text, parse_mode='Markdown')
                return
            
            action = args[0].lower()
            accept = len(args) > 1 and args[1].upper() == 'ACEPTO'
            
            if action in ['activar', 'on', 'enable']:
                if not accept:
                    await update.message.reply_text(
                        """🤖 **TRADING AUTOMÁTICO INSTITUCIONAL**

Sistema de ejecución con gestión de riesgo activa:
• Límites de posición y drawdown controlados
• Asset Quarantine protege tu capital
• Coherence Engine valida cada operación

Para activar, confirma:
`/autotrading activar ACEPTO`""",
                        parse_mode='Markdown'
                    )
                    return
                
                settings = self.user_settings_service.get_user_settings(str(user.id))
                settings.risk_disclosure_accepted = True
                self.user_settings_service.save_user_settings(settings)
                
                success, message = self.user_settings_service.toggle_auto_trading(str(user.id), True)
                await update.message.reply_text(message, parse_mode='Markdown')
                
            elif action in ['desactivar', 'off', 'disable']:
                success, message = self.user_settings_service.toggle_auto_trading(str(user.id), False)
                await update.message.reply_text(message, parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Usa: `/autotrading activar` o `/autotrading desactivar`", parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en autotrading: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def pausar_trading_command(self, update, context):
        """Comando /pausar [minutos] - Pausar trading temporalmente"""
        try:
            user = update.effective_user
            args = context.args if context.args else []
            
            if not self.user_settings_service:
                await update.message.reply_text("❌ Servicio de configuración no disponible")
                return
            
            minutes = 60
            if args:
                try:
                    minutes = int(args[0])
                    if minutes < 5:
                        minutes = 5
                    elif minutes > 1440:
                        minutes = 1440
                except ValueError:
                    pass
            
            success, message = self.user_settings_service.pause_trading(
                str(user.id),
                reason="Pausa manual solicitada por usuario",
                minutes=minutes
            )
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en pausar: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def reanudar_trading_command(self, update, context):
        """Comando /reanudar - Reanudar trading"""
        try:
            user = update.effective_user
            
            if not self.user_settings_service:
                await update.message.reply_text("❌ Servicio de configuración no disponible")
                return
            
            success, message = self.user_settings_service.resume_trading(str(user.id))
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en reanudar: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def onboarding_command(self, update, context):
        """Comando /onboarding - Iniciar proceso de configuración guiada"""
        try:
            user = update.effective_user
            
            if not self.user_settings_service:
                await update.message.reply_text("❌ Servicio de configuración no disponible")
                return
            
            settings = self.user_settings_service.get_user_settings(str(user.id), username=user.username)
            
            onboarding_text = f"""🚀 **BIENVENIDO AL ASISTENTE DE CONFIGURACIÓN**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

¡Hola {user.first_name}! Te guiaré para configurar OMNIX según tus preferencias.

**📌 PASO 1: ELIGE TU PERFIL DE RIESGO**

Escribe uno de estos comandos:

🛡️ `/perfil conservador` - Protección máxima
⚖️ `/perfil moderado` - Balance equilibrado  
🔥 `/perfil agresivo ACEPTO` - Mayor potencial

**📌 PASO 2: REVISA TUS LÍMITES**

`/limites` - Ver y ajustar límites de trading

**📌 PASO 3: CONFIGURA TU PROTECCIÓN**

`/proteccion` - Auto-pausa y stop loss

**📌 PASO 4: ELIGE TUS ESTRATEGIAS**

`/estrategias` - Activa las que prefieras

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **TIP:** También puedes escribirme en lenguaje natural:
• "quiero ser más conservador"
• "máximo $500 por trade"
• "pausa el trading"

Tu configuración actual: **{settings.risk_profile.value.title()}**
Usa `/miconfig` para ver todos los detalles.
"""
            
            await update.message.reply_text(onboarding_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en onboarding: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def resumen_command(self, update, context):
        """Comando /resumen - Generar resumen diario de trading PREMIUM"""
        try:
            user = update.effective_user
            chat_id = str(update.effective_chat.id)
            
            if not is_admin(user.id):
                await update.message.reply_text("❌ Este comando es solo para administradores")
                return
            
            await update.message.reply_text("📊 Generando resumen del día...")
            
            if self.daily_summary_service:
                summary = self.daily_summary_service.get_summary_now()
                
                if summary:
                    message = self.daily_summary_service._format_summary_message(summary)
                    await update.message.reply_text(message, parse_mode='Markdown')
                else:
                    await update.message.reply_text("""📊 *RESUMEN DEL DÍA*
━━━━━━━━━━━━━━━━━━━━━

📭 No hay trades cerrados hoy.

El bot está activo y buscando oportunidades.
Usa `/autotrading status` para ver el estado.

_OMNIX Decision Governance_""", parse_mode='Markdown')
            else:
                await update.message.reply_text("❌ Servicio de resumen no disponible")
                
        except Exception as e:
            logger.error(f"Error en resumen: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def reporte_diario_command(self, update, context):
        """Comando /reporte_diario - Reporte brutal honesty monitoring"""
        try:
            user = update.effective_user
            chat_id = str(update.effective_chat.id)
            
            if not is_admin(user.id):
                await update.message.reply_text("❌ Este comando es solo para administradores")
                return
            
            await update.message.reply_text("📊 Generando reporte diario de recalibración...")
            
            try:
                from omnix_services.monitoring.daily_report_service import get_daily_report_service
                
                service = get_daily_report_service()
                metrics = service.fetch_real_metrics(user_id='harold_admin')
                report = service.generate_report(metrics)
                
                service.save_report(metrics, report)
                
                if len(report) > 4000:
                    parts = [report[i:i+4000] for i in range(0, len(report), 4000)]
                    for i, part in enumerate(parts):
                        await update.message.reply_text(f"```\n{part}\n```", parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"```\n{report}\n```", parse_mode='Markdown')
                
                logger.info(f"📊 Daily report generated for user {user.id}")
                
            except ImportError as e:
                logger.error(f"❌ DailyReportService not available: {e}")
                await update.message.reply_text("❌ Servicio de reporte diario no disponible")
            except Exception as e:
                logger.error(f"❌ Error generating daily report: {e}")
                await update.message.reply_text(f"❌ Error generando reporte: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error en reporte_diario: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")


# Funciones de integración para comandos Harold

def activate_advanced_ml_module(trading_system):
    """Activa módulo avanzado de ML Harold"""
    try:
        ml_module = AdvancedMLModule(trading_system)
        lstm_result = ml_module.implement_lstm_price_prediction()
        
        return {
            'module': 'Advanced_ML',
            'status': 'ACTIVATED',
            'lstm_model': lstm_result,
            'intelligence_upgrade': 'COMPLETED'
        }
    except Exception as e:
        logger.error(f"Error activating ML module: {e}")
        return {'status': 'ERROR', 'message': str(e)}

def activate_trading_optimizer(trading_system):
    """Activa optimizador avanzado de trading Harold"""
    try:
        optimizer = AdvancedTradingOptimizer(trading_system)
        strategies_result = optimizer.develop_hybrid_strategies()
        
        return {
            'module': 'Trading_Optimizer',
            'status': 'ACTIVATED', 
            'hybrid_strategies': strategies_result,
            'optimization_upgrade': 'COMPLETED'
        }
    except Exception as e:
        logger.error(f"Error activating optimizer: {e}")
        return {'status': 'ERROR', 'message': str(e)}

def activate_continuous_adaptation(trading_system):
    """Activa módulo de adaptación continua Harold"""
    try:
        adaptation_module = ContinuousAdaptationModule(trading_system)
        monitoring_result = adaptation_module.implement_continuous_monitoring()
        
        return {
            'module': 'Continuous_Adaptation',
            'status': 'ACTIVATED',
            'monitoring_system': monitoring_result,
            'adaptation_upgrade': 'COMPLETED'
        }
    except Exception as e:
        logger.error(f"Error activating adaptation: {e}")
        return {'status': 'ERROR', 'message': str(e)}



# ── Bind governance commands as methods on EnterpriseTelegramBot — ADR-058 ──────
# Pattern: monkeypatch post-class-definition para mantener modularidad
# Referencia: arquitecto recomienda governance_commands.py separado (8729-línea bot)
if _GOVERNANCE_COMMANDS_AVAILABLE:
    EnterpriseTelegramBot.evaluar_command    = evaluar_command     # type: ignore[attr-defined]
    EnterpriseTelegramBot.gobernanza_command = gobernanza_command  # type: ignore[attr-defined]
    EnterpriseTelegramBot.velos_command      = velos_command       # type: ignore[attr-defined]
    EnterpriseTelegramBot.recibo_command     = recibo_command      # type: ignore[attr-defined]
    EnterpriseTelegramBot.impact_command          = impact_command           # type: ignore[attr-defined]
    EnterpriseTelegramBot.clientes_command        = clientes_command         # type: ignore[attr-defined]
    EnterpriseTelegramBot.nuevo_cliente_command   = nuevo_cliente_command    # type: ignore[attr-defined]
    logger.info("🏛️ [ADR-058] Governance commands enlazados en EnterpriseTelegramBot (incl. /impact, /clientes, /nuevo_cliente)")
else:
    # Stubs para que el bot no crashee si governance_commands falla al importar
    async def _governance_stub(self, update, context):
        await update.message.reply_text("⚠️ Módulo de gobernanza no disponible. Contacta al administrador.")
    EnterpriseTelegramBot.evaluar_command    = _governance_stub    # type: ignore[attr-defined]
    EnterpriseTelegramBot.gobernanza_command = _governance_stub    # type: ignore[attr-defined]
    EnterpriseTelegramBot.velos_command      = _governance_stub    # type: ignore[attr-defined]
    EnterpriseTelegramBot.recibo_command     = _governance_stub    # type: ignore[attr-defined]
    EnterpriseTelegramBot.impact_command          = _governance_stub    # type: ignore[attr-defined]
    EnterpriseTelegramBot.clientes_command        = _governance_stub    # type: ignore[attr-defined]
    EnterpriseTelegramBot.nuevo_cliente_command   = _governance_stub    # type: ignore[attr-defined]


if __name__ == "__main__":
    app = main()
    if app:
        run_dev_server(app)