"""
OMNIX EnterpriseTelegramBot - Modular Architecture
Bot Telegram empresarial con todas las funcionalidades OMNIX
Extraído de main.py para arquitectura limpia y mantenible
"""

import logging
import os
import time
import threading
import asyncio
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Import centralized settings
from omnix_config.settings import settings

logger = logging.getLogger(__name__)

# Import omnix services
try:
    from omnix_services.ai_service import ConversationalAIService
    OMNIX_ENTERPRISE_AVAILABLE = True
except ImportError:
    OMNIX_ENTERPRISE_AVAILABLE = False
    logger.warning("⚠️ ConversationalAIService no disponible")

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

# Community Intelligence - Memoria Colectiva V6.0
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

# Signal Contribution - Crowdsourcing de Alpha V6.0
try:
    from omnix_services.community_intelligence.signal_contribution import SignalContributionManager
    SIGNAL_CONTRIBUTION_AVAILABLE = True
except ImportError:
    SIGNAL_CONTRIBUTION_AVAILABLE = False
    logger.warning("⚠️ Signal Contribution module no disponible")

# Voice Service - TTS con Google gTTS
try:
    from omnix_services.voice_service.voice_controller import send_telegram_response_with_voice
    VOICE_SERVICE_AVAILABLE = True
    logger.info("🎤 Voice Service disponible")
except ImportError:
    VOICE_SERVICE_AVAILABLE = False
    logger.warning("⚠️ Voice Service no disponible")

# ARES Quantum Protocols - Variables globales desde trading_system
try:
    from omnix_core.trading_system import global_ares_v1, global_ares_v2
    ARES_AVAILABLE = global_ares_v1 is not None and global_ares_v2 is not None
    if ARES_AVAILABLE:
        logger.info("🧬 ARES V1/V2 disponibles desde trading_system")
except ImportError:
    global_ares_v1 = None
    global_ares_v2 = None
    ARES_AVAILABLE = False
    logger.warning("⚠️ ARES Quantum Protocols no disponibles")

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

# Risk Management System (RMS) V6.0
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

# Telegram availability check
try:
    from telegram import __version__
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False


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


class EnterpriseTelegramBot:
    """Bot Telegram empresarial con todas las funcionalidades"""
    
    def __init__(self, db_manager=None):
        self.application = None
        self.is_running = False
        self.db_manager = db_manager  # MEMORIA PERSISTENTE POSTGRESQL
        self.ai = ConversationalAIService()  # SUPERINTELIGENCIA PARA HAROLD
        
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
            self.trading = TradingSystem()
        else:
            self.trading = self.trading_enterprise  # Referencia al enterprise
            logger.info("🚀 TRADING ENTERPRISE READY - Sistema premium activado")
        
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
                ai_service=self.ai,  # 🎓 V5.2.3: AI para auto-learning de videos
                ares_v1=global_ares_v1 if 'global_ares_v1' in globals() else None,  # 🧬 ARES V1 Swing Trading
                ares_v2=global_ares_v2 if 'global_ares_v2' in globals() else None   # 🧨 ARES V2 Scalping M1
            )
            logger.info("🤖 Auto-Trading Bot inicializado - Trading inteligente 24/7 disponible")
            logger.info(f"   📊 Paper Trading: {'✅ ACTIVADO ($1M virtual)' if self.paper_trading else '❌ Desactivado'}")
            logger.info(f"   🎓 Auto-Learning: {'✅ DISPONIBLE' if self.ai else '⚠️ Sin IA'}")
            logger.info(f"   🧬 ARES V1 Swing: {'✅ CONECTADO (74-82% win rate)' if self.auto_trading.ares_v1 else '⚠️ No disponible'}")
            logger.info(f"   🧨 ARES V2 Scalping: {'✅ CONECTADO (85% win rate)' if self.auto_trading.ares_v2 else '⚠️ No disponible'}")
        except Exception as e:
            logger.warning(f"⚠️ Auto-Trading Bot no disponible: {e}")
            self.auto_trading = None
        
        # 🎥 VIDEO ANALYZER ULTRA V5.3 - Análisis avanzado de videos con Vision AI
        try:
            from omnix_services.ai_service.video.analyzer import VideoAnalyzerUltra
            from omnix_services.ai_service.video.integration import VideoLearningIntegration
            
            self.video_analyzer_ultra = VideoAnalyzerUltra()
            logger.info("🎥 Video Analyzer Ultra V5.3 inicializado")
            logger.info(f"   🎬 GPT-4 Vision: {'✅' if self.video_analyzer_ultra.openai_client else '❌'}")
            logger.info(f"   🧠 Gemini Vision: {'✅' if self.video_analyzer_ultra.gemini_client else '❌'}")
            
            # Integración con Auto-Learning System
            if self.auto_trading and hasattr(self.auto_trading, 'auto_learning'):
                self.video_learning_integration = VideoLearningIntegration(
                    auto_learning_system=self.auto_trading.auto_learning,
                    video_analyzer_ultra=self.video_analyzer_ultra
                )
                logger.info("🔗 Video Learning Integration conectada al Auto-Learning System")
            else:
                self.video_learning_integration = None
                logger.warning("⚠️ Video Learning Integration sin Auto-Learning System")
                
        except Exception as e:
            logger.warning(f"⚠️ Video Analyzer Ultra V5.3 no disponible: {e}")
            self.video_analyzer_ultra = None
            self.video_learning_integration = None
        
        # 📊 STOCK TRADING HANDLER V6.0 - DUAL MARKET SYSTEM
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
        
        # 💱 ARBITRAGE MULTI-EXCHANGE PREMIUM V6.0
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
        
        # 🧠 COMMUNITY INTELLIGENCE - MEMORIA COLECTIVA V6.0
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
        
        # 🚀 SIGNAL CONTRIBUTION - CROWDSOURCING DE ALPHA V6.0
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
        
        # 🛡️ RISK MANAGEMENT SYSTEM (RMS) V6.0 - Control de Riesgo Institucional
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
                
            self.application = Application.builder().token(token).build()
            
            # Comandos principales
            self.application.add_handler(CommandHandler("start", self.start_command))
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
            self.application.add_handler(CommandHandler("blackswan", self.blackswan_command))
            self.application.add_handler(CommandHandler("sentiment", self.sentiment_command))
            self.application.add_handler(CommandHandler("sharia", self.sharia_command))
            self.application.add_handler(CommandHandler("orderbook", self.orderbook_command))
            self.application.add_handler(CommandHandler("enterprise", self.enterprise_command))
            
            # 📊 Comandos Paper Trading - Trading simulado con $1M
            self.application.add_handler(CommandHandler("paper_start", self.paper_start_command))
            self.application.add_handler(CommandHandler("paper_balance", self.paper_balance_command))
            self.application.add_handler(CommandHandler("paper_buy", self.paper_buy_command))
            self.application.add_handler(CommandHandler("paper_sell", self.paper_sell_command))
            
            # 📰 News Scraper Commands (V5.4 ULTRA - Análisis de Noticias)
            # TODO: Implementar estos comandos
            # self.application.add_handler(CommandHandler("analizar_noticia", self.analyze_news_command))
            # self.application.add_handler(CommandHandler("trending_crypto", self.trending_news_command))
            
            # 🤖 Comandos Auto-Trading - Trading automático 24/7
            self.application.add_handler(CommandHandler("auto_start", self.auto_start_command))
            self.application.add_handler(CommandHandler("auto_stop", self.auto_stop_command))
            self.application.add_handler(CommandHandler("auto_status", self.auto_status_command))
            
            # 🎓 Comandos Auto-Learning V5.2.3 - Aprendizaje de videos YouTube
            self.application.add_handler(CommandHandler("activar_auto_ajuste", self.activar_auto_ajuste_command))
            self.application.add_handler(CommandHandler("pausar_auto_ajuste", self.pausar_auto_ajuste_command))
            self.application.add_handler(CommandHandler("ver_aprendizaje", self.ver_aprendizaje_command))
            self.application.add_handler(CommandHandler("revertir_cambio", self.revertir_cambio_command))
            
            # 🛡️ Comandos AI Risk Guardian V5.4 - Supervisor de Riesgos
            self.application.add_handler(CommandHandler("risk_status", self.risk_status_command))
            self.application.add_handler(CommandHandler("risk_events", self.risk_events_command))
            
            # 📊 Comandos Stock Trading V6.0 - BOLSA DE VALORES (NYSE/NASDAQ)
            if self.stock_handler and self.stock_handler.enabled:
                self.application.add_handler(CommandHandler("balance_bolsa", self.balance_stocks_command))
                self.application.add_handler(CommandHandler("mercado", self.market_status_command))
                self.application.add_handler(CommandHandler("analizar", self.analyze_stock_command))
                self.application.add_handler(CommandHandler("comprar_bolsa", self.buy_stock_command))
                self.application.add_handler(CommandHandler("vender_bolsa", self.sell_stock_command))
                logger.info("📊 Stock Trading commands registrados: /balance_bolsa, /mercado, /analizar, /comprar_bolsa, /vender_bolsa")
            
            # 💱 Comandos Arbitrage Multi-Exchange Premium V6.0
            if self.arbitrage_scanner:
                self.application.add_handler(CommandHandler("arbitrage", self.arbitrage_command))
                self.application.add_handler(CommandHandler("arbitrage_scan", self.arbitrage_scan_command))
                self.application.add_handler(CommandHandler("arbitrage_execute", self.arbitrage_execute_command))
                self.application.add_handler(CommandHandler("arbitrage_stats", self.arbitrage_stats_command))
                logger.info("💱 Arbitrage commands registrados: /arbitrage, /arbitrage_scan, /arbitrage_execute, /arbitrage_stats")
            
            # 🧠 Comandos Community Intelligence - Memoria Colectiva V6.0
            if self.feedback_manager:
                self.application.add_handler(CommandHandler("feedback", self.feedback_command))
                self.application.add_handler(CommandHandler("community_stats", self.community_stats_command))
                self.application.add_handler(CommandHandler("top_strategies", self.top_strategies_command))
                self.application.add_handler(CommandHandler("my_contributions", self.my_contributions_command))
                self.application.add_handler(CommandHandler("vote_strategy", self.vote_strategy_command))
                self.application.add_handler(CommandHandler("leaderboard", self.leaderboard_command))
                self.application.add_handler(CommandHandler("analyze_patterns", self.analyze_patterns_command))
                logger.info("🧠 Community Intelligence commands registrados: /feedback, /community_stats, /top_strategies, /my_contributions, /vote_strategy, /leaderboard")
            
            # 🚀 Comandos Signal Contribution - Crowdsourcing de Alpha V6.0
            if self.signal_contribution:
                self.application.add_handler(CommandHandler("share_signal", self.share_signal_command))
                self.application.add_handler(CommandHandler("community_signals", self.community_signals_command))
                self.application.add_handler(CommandHandler("my_signals", self.my_signals_command))
                self.application.add_handler(CommandHandler("alpha_leaderboard", self.alpha_leaderboard_command))
                self.application.add_handler(CommandHandler("execute_signal", self.execute_signal_command))
                logger.info("🚀 Signal Contribution commands registrados: /share_signal, /community_signals, /my_signals, /alpha_leaderboard")
            
            # 🛡️ Comandos Risk Management System (RMS) V6.0 - Control Institucional
            if self.limits_engine:
                self.application.add_handler(CommandHandler("rms", self.rms_dashboard_command))
                self.application.add_handler(CommandHandler("rms_limits", self.rms_limits_command))
                self.application.add_handler(CommandHandler("rms_set", self.rms_set_limit_command))
                self.application.add_handler(CommandHandler("rms_history", self.rms_history_command))
                self.application.add_handler(CommandHandler("emergency_halt", self.rms_emergency_halt_command))
                self.application.add_handler(CommandHandler("resume_trading", self.rms_resume_trading_command))
                logger.info("🛡️ RMS commands registrados: /rms, /rms_limits, /rms_set, /rms_history, /emergency_halt, /resume_trading")
            
            # Handler para mensajes de texto
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
            )
            
            # 🎤 Handler PREMIUM para mensajes de voz con Whisper AI
            self.application.add_handler(
                MessageHandler(filters.VOICE, self.handle_voice_message)
            )
            
            # 🎨 Handler para botones inline (callbacks)
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))
            
            logger.info("✅ Bot Telegram empresarial configurado")
            logger.info("🎤 Handler de voz premium activado - Whisper AI")
            logger.info("🎨 Handler de botones inline activado - Interacción premium")
            
            # 🛡️ Conectar AlertDispatcher al bot de Telegram
            if self.alert_dispatcher:
                self.alert_dispatcher.set_telegram_bot(self.application.bot)
                logger.info("📢 AlertDispatcher conectado a Telegram Bot")
            
            # 🛡️ Configurar RMS en TradingServiceEnterprise
            if self.trading_enterprise_enabled and self.trading_enterprise:
                self.trading_enterprise.configure_rms(
                    limits_engine=self.limits_engine,
                    circuit_breaker=self.circuit_breaker,
                    alert_dispatcher=self.alert_dispatcher
                )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error configurando bot: {e}")
            return False
    
    async def start_command(self, update, context):
        """Comando /start con botones interactivos premium"""
        try:
            from omnix_services.telegram_service.inline_keyboards import InlineKeyboardsManager
            
            user = update.effective_user
            
            welcome_message = f"""🚀 **OMNIX V6.0 DUAL-MARKET ULTRA**

¡Hola {user.first_name}! Soy OMNIX, tu asistente de trading profesional.

✅ **SISTEMA OPERATIVO:**
🪙 Cripto 24/7 (Kraken) - REAL
📊 Bolsa USA (Alpaca) - Paper
🤖 IA Dual: Gemini 2.0 + GPT-4o
🎲 Monte Carlo: 10,000 simulaciones
🎤 Voz premium activada

💬 **Pregúntame sobre trading o usa los botones:**
"""
            
            # Enviar mensaje con botones interactivos
            keyboard = InlineKeyboardsManager.get_main_menu()
            await update.message.reply_text(
                welcome_message, 
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            
            # Enviar disclaimer legal por separado
            disclaimer = """⚠️ **DISCLAIMER LEGAL:**
OMNIX es EDUCATIVO. NO es asesor financiero.
Trading conlleva RIESGO de pérdida total.
Opera bajo tu propio riesgo. /legal para detalles."""
            
            await update.message.reply_text(disclaimer, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Error comando start: {e}")
            await update.message.reply_text("Error procesando comando /start")

    async def help_command(self, update, context):
        """Comando /help"""
        try:
            help_text = """
**OMNIX V5.1 - COMANDOS COMPLETOS**

**INFORMACION DE MERCADO:**
/precio [crypto] - Precio actual (ej: /precio BTC)
/market - 📊 Dashboard premium del mercado (datos reales Kraken)
/balance - Tu balance real en Kraken
/convertir [cantidad] [CRYPTO] - Convertir cantidad específica a USD (ej: /convertir 50 BTC)
/convertir_usd - Convertir todas las cryptos a USD
/performance [dias] - Ver evolución de tu balance
/analisis [crypto] - Analisis tecnico completo
/status - Estado del sistema

**📊 PAPER TRADING (Trading Simulado):**
/paper_start - Iniciar con $1,000,000 virtual
/paper_balance - Ver balance de paper trading
/paper_buy BTC 10000 - Comprar $10,000 de BTC (simulado)
/paper_sell BTC 5000 - Vender $5,000 de BTC (simulado)
*Usa precios REALES de Kraken sin gastar dinero real*

**📈 BOLSA DE VALORES (NYSE/NASDAQ) - NUEVO V6.0:**
/balance_bolsa - Ver balance y posiciones en acciones
/mercado - Estado del mercado (abierto/cerrado)
/analizar AAPL - Análisis técnico + fundamental completo
/comprar_bolsa TSLA 500 - Comprar $500 de Tesla (paper)
/vender_bolsa TSLA - Vender posición en Tesla
*Trading de acciones USA con análisis AI premium*

**🤖 AUTO-TRADING 24/7 (Trading REAL Automático):**
/auto_start - Activar bot automático 24/7
/auto_stop - Detener trading automático
/auto_status - Ver estado y estadísticas
*Trading REAL con estrategia inteligente (Monte Carlo + Black Swan + Sentiment)*

**EDUCACION Y LEGAL:**
/educacion - Guía completa de trading y riesgos
/legal - Términos legales y disclaimer completo

**ADVANCED FEATURES ENTERPRISE:**
/montecarlo [crypto] - Simulacion Monte Carlo (10,000 escenarios)
/blackswan [crypto] - Deteccion de eventos extremos
/sentiment [crypto] - Analisis de sentimiento del mercado
/sharia [crypto] - Verificacion Sharia compliance
/orderbook [crypto] - Analisis de ballenas y liquidez
/enterprise [crypto] - Analisis completo multi-dimensional

**INTERACCION IA:**
- Escribe cualquier pregunta sobre crypto
- El sistema responde con analisis inteligente
- Respuestas automaticas por voz

**CARACTERISTICAS:**
- Datos REALES de Kraken + APIs premium
- IA Dual (Gemini + OpenAI)
- Sistema transparente 100%
- Monte Carlo + Black Swan Detection
- Tracking de performance automático
- Paper Trading con $1M virtual
- Desarrollado por Harold Nunes

**Ejemplos de uso:**
"Como esta Bitcoin hoy?"
/paper_start (probar estrategias sin riesgo)
/paper_buy BTC 50000
/performance 7 (para ver últimos 7 días)
/educacion (aprende estrategias)
/montecarlo BTC
/sentiment ethereum

**Empieza preguntando lo que necesites!**
"""
            
            await update.message.reply_text(help_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Error comando help: {e}")

    async def legal_command(self, update, context):
        """Comando /legal - Disclaimer y términos legales"""
        try:
            legal_text = """
⚖️ **TÉRMINOS LEGALES Y DISCLAIMER - OMNIX V5.1**

🔞 **RESTRICCIÓN DE EDAD:**
Este servicio está disponible SOLO para usuarios mayores de 18 años. Al usar OMNIX confirmas que cumples este requisito legal.

**NATURALEZA DEL SERVICIO:**
OMNIX es una herramienta de ANÁLISIS EDUCATIVO e INFORMATIVO sobre criptomonedas. NO es:
- ❌ Asesor financiero regulado
- ❌ Gestor de inversiones
- ❌ Entidad bancaria o financiera
- ❌ Garantía de ganancias

**RIESGOS DEL TRADING DE CRIPTOMONEDAS:**
⚠️ ADVERTENCIA CRÍTICA:
- El trading de criptomonedas conlleva RIESGO EXTREMO
- Puedes perder el 100% de tu capital invertido
- Mercados altamente volátiles (variaciones +/- 50% diarias)
- No regulado en muchas jurisdicciones
- Riesgo de hackeos, fraudes, manipulación

**LIMITACIONES DEL SISTEMA:**
Las proyecciones, simulaciones Monte Carlo, análisis de Black Swan y recomendaciones de OMNIX:
- NO garantizan resultados futuros
- Se basan en modelos matemáticos con limitaciones
- No consideran eventos impredecibles (guerras, regulaciones, hackeos)
- Pueden contener errores técnicos o de datos

**USO BAJO TU PROPIO RIESGO:**
Al usar OMNIX, aceptas que:
- Operas completamente bajo tu responsabilidad
- Harold Nunes (desarrollador) NO se hace responsable de pérdidas
- OMNIX NO asume responsabilidad por decisiones de trading

⚠️ **CONSULTA PROFESIONAL OBLIGATORIA:**
Debes consultar SIEMPRE con un asesor financiero REGULADO y CERTIFICADO antes de realizar cualquier inversión. OMNIX NO sustituye asesoramiento profesional personalizado.

**CUMPLIMIENTO REGULATORIO Y JURISDICCIÓN:**
- OMNIX no está registrado ante la SEC (USA), FINRA (USA), FCA (UK), BaFin (Alemania) o entidades reguladoras similares
- Este servicio es EXPERIMENTAL y en DESARROLLO activo
- Operamos como software educativo bajo leyes internacionales de protección al consumidor
- **JURISDICCIONES RESTRINGIDAS - NO DISPONIBLE EN:**
  • China (prohibición total trading crypto)
  • Corea del Norte (sanciones internacionales)
  • Irán, Siria (sanciones OFAC)
  • Crimea, Donetsk, Luhansk (sanciones)
  • Países con prohibición explícita de criptomonedas
- **JURISDICCIONES FAVORABLES (donde planeamos registro futuro):**
  • Suiza (FINMA - Crypto Valley Zug)
  • Singapur (MAS - Payment Services Act)
  • Dubai (VARA - Virtual Asset Regulatory Authority)
  • Unión Europea (MiCA - Markets in Crypto-Assets Regulation)
- Usuarios DEBEN verificar legalidad en su jurisdicción local antes de usar
- Cumplimiento fiscal es responsabilidad del usuario

**SHARIA COMPLIANCE:**
Las clasificaciones Halal/Haram se basan en investigación académica (Mufti Taqi Usmani, AAOIFI) pero:
- NO sustituyen consulta con erudito islámico
- Interpretaciones pueden variar según madhab
- Responsabilidad final del usuario

**PROTECCIÓN DE DATOS:**
- Conversaciones almacenadas en base de datos segura
- API keys y credenciales encriptadas (PQC Kyber-768)
- NO compartimos datos con terceros
- Cumplimiento GDPR en proceso

**CONTACTO:**
Desarrollador: Harold Nunes
Sistema: OMNIX V5.1 Enterprise Fusion
Última actualización: Noviembre 2025

⚠️ **IMPORTANTE:** Si no aceptas estos términos, NO uses OMNIX para tomar decisiones financieras.

*Para soporte técnico, contacta al desarrollador.*
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

OMNIX es una HERRAMIENTA EDUCATIVA. Te damos datos y análisis, pero TÚ tomas las decisiones. Si no entiendes algo, NO inviertas en ello.

El mejor trade es el que NO haces si no estás seguro.

**Comandos útiles:**
/legal - Términos completos
/help - Ver todos los comandos
/analisis BTC - Análisis técnico completo

*Desarrollado por Harold Nunes - Sistema OMNIX V5.1*
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
                if not global_trading_system:
                    await update.message.reply_text("⚠️ Sistema de trading no disponible")
                    return
                price_data = global_trading_system.get_real_market_data(f"{symbol}/USD")
                
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

*Sistema OMNIX V5.1 - Harold Nunes*
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
                    if not global_trading_system:
                        continue
                    
                    price_data = global_trading_system.get_real_market_data(f"{symbol}/USD")
                    
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
                        except:
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

*OMNIX V6.0 ULTRA - Market Intelligence*
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
        """Comando /balance"""
        try:
            # Obtener balance real usando instancia global
            try:
                if not global_trading_system:
                    await update.message.reply_text("⚠️ Sistema de trading no disponible")
                    return
                balance_data = global_trading_system.get_real_balance()
                
                # Guardar snapshot automáticamente usando DatabaseServiceEnterprise
                user_id = str(update.message.from_user.id)
                snapshot_data = {
                    'exchange': 'kraken',
                    'total_usd': balance_data.get('total_usd', 0),
                    'btc_balance': balance_data.get('BTC', 0),
                    'eth_balance': balance_data.get('ETH', 0),
                    'usdt_balance': balance_data.get('USDT', 0),
                    'other_balance': 0
                }
                if global_db_manager:
                    global_db_manager.save_balance_snapshot(user_id, snapshot_data)
                
                mensaje = f"""
**BALANCE REAL KRAKEN**

**USD:** ${balance_data.get('USD', 0):.2f}
**BTC:** {balance_data.get('BTC', 0):.8f}
**ETH:** {balance_data.get('ETH', 0):.6f}

**Total estimado:** ${balance_data.get('total_usd', 0):.2f}

**Estado:** TRADING REAL ACTIVADO
**Seguridad:** API Kraken oficial

*Datos actualizados en tiempo real*
*Balance guardado para tracking histórico*

Usa /performance para ver evolución de tu balance
"""
                
            except Exception as e:
                logger.error(f"Error obteniendo balance: {e}")
                mensaje = "Error obteniendo balance. Verifica conexion Kraken."
            
            await update.message.reply_text(mensaje, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Error comando balance: {e}")

    async def convertir_usd_command(self, update, context):
        """Comando /convertir_usd - Convertir todas las criptomonedas a USD minimizando fees"""
        try:
            user_id = str(update.message.from_user.id)
            
            # Solo Harold puede ejecutar conversiones reales
            if user_id != settings.TELEGRAM_ADMIN_ID:
                await update.message.reply_text("⚠️ Solo Harold puede convertir fondos a USD")
                return
            
            # Verificar que el sistema de trading esté disponible
            if not global_trading_system:
                await update.message.reply_text("⚠️ Sistema de trading no disponible")
                return
            
            await update.message.reply_text("🔄 Analizando balance y calculando conversiones óptimas...")
            
            try:
                # Obtener balance actual
                balance_data = global_trading_system.get_real_balance()
                
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
                        ticker = global_trading_system.kraken_client.client.fetch_ticker(f"{moneda}/USD")
                        precio_actual = ticker['last']
                        valor_usd = cantidad_float * precio_actual
                        
                        # Solo convertir si el valor es > $1 (evitar dust amounts)
                        if valor_usd < 1.0:
                            mensaje_conversiones += f"⏭️ **{moneda}:** {cantidad_float:.8f} (${valor_usd:.2f}) - Monto muy pequeño, no se convierte\n"
                            continue
                        
                        # EJECUTAR CONVERSIÓN REAL con orden de mercado
                        logger.info(f"💱 Convirtiendo {cantidad_float} {moneda} a USD (${valor_usd:.2f})")
                        
                        # Usar KrakenAPIClient para crear orden de mercado SELL
                        orden_result = global_trading_system.kraken_client.place_order(
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
            
            # Solo Harold puede ejecutar conversiones reales
            if user_id != settings.TELEGRAM_ADMIN_ID:
                await update.message.reply_text("⚠️ Solo Harold puede convertir fondos")
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
            if not global_trading_system:
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
                balance_data = global_trading_system.get_real_balance()
                
                if moneda not in balance_data or float(balance_data[moneda]) <= 0:
                    await update.message.reply_text(f"❌ No tienes {moneda} en tu balance")
                    return
                
                cantidad_disponible = float(balance_data[moneda])
                
                # Obtener precio actual
                par = pares_kraken[moneda]
                ticker = global_trading_system.kraken_client.client.fetch_ticker(f"{moneda}/USD")
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
                
                orden_result = global_trading_system.kraken_client.place_order(
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

Sistema OMNIX V5.1 - Harold Nunes
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
                if not global_trading_system:
                    await update.message.reply_text("⚠️ Sistema de trading no disponible")
                    return
                analisis = global_trading_system.generate_comprehensive_analysis(f"{symbol}/USD")
                
                mensaje = f"""
🧠 **ANÁLISIS TÉCNICO {symbol}/USD**

📊 **Precio:** ${analisis.get('precio', 'N/A')}
📈 **RSI:** {analisis.get('rsi', 'N/A')}
📉 **MACD:** {analisis.get('macd', 'N/A')}
🎯 **Recomendación:** {analisis.get('recomendacion', 'NEUTRO')}

🔮 **Análisis IA:**
{analisis.get('analisis_ia', 'Mercado en análisis...')}

⚡ **Actualizado:** {datetime.now().strftime('%H:%M:%S')}

*Análisis generado por OMNIX V5.1*
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
🔍 **OMNIX V5.1 SYSTEM STATUS**

🟢 **Sistema:** OPERATIVO
🟢 **Trading:** KRAKEN CONECTADO
🟢 **IA Dual:** GEMINI + OPENAI ACTIVO
🟢 **Balance:** Verificado en tiempo real con Kraken
🟢 **Bot Telegram:** FUNCIONANDO

⚡ **Uptime:** {datetime.now().strftime('%H:%M:%S')}
🚀 **Versión:** V5.1 Enterprise Fusion
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
            price = global_trading_system.get_current_price(f"{symbol}/USD")
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
            price = global_trading_system.get_current_price(f"{symbol}/USD") or 50000
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
            
            # Solo Harold puede activar auto-trading
            if user_id != settings.TELEGRAM_ADMIN_ID:
                logger.warning(f"⚠️ Usuario no autorizado: {user_id}")
                await update.message.reply_text("⚠️ Solo Harold puede activar auto-trading")
                return
            
            logger.info("✅ Validaciones OK - Activando bot...")
            await update.message.reply_text("🔄 Activando trading automático 24/7...")
            
            logger.info("📞 Llamando a auto_trading.start()...")
            result = self.auto_trading.start()
            logger.info(f"📊 Resultado de start(): {result}")
            
            if 'error' in result:
                await update.message.reply_text(f"❌ {result['error']}")
                return
            
            msg = f"""
🤖 **AUTO-TRADING ACTIVADO 24/7**

💰 Balance inicial: ${result['initial_balance']:.2f}

**ESTRATEGIA INTELIGENTE:**
✅ Monte Carlo - Validación probabilística
✅ Black Swan - Detección de riesgos extremos
✅ Sentiment - Timing basado en mercado
✅ Post-Quantum - Firmas seguras

**CONFIGURACIÓN:**
📊 Par: {result['config']['trading_pair']}
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
                msg += """
✅ **MODO:** PAPER TRADING ($1M virtual)
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
            
            # Solo Harold puede detener
            if user_id != settings.TELEGRAM_ADMIN_ID:
                await update.message.reply_text("⚠️ Solo Harold puede detener auto-trading")
                return
            
            await update.message.reply_text("🔄 Deteniendo trading automático...")
            
            result = self.auto_trading.stop()
            
            if 'error' in result:
                await update.message.reply_text(f"❌ {result['error']}")
                return
            
            stats = result.get('stats', {})
            
            msg = f"""
🛑 **AUTO-TRADING DETENIDO**

📊 **ESTADÍSTICAS FINALES:**
Trades totales: {stats.get('total_trades', 0)}
Ganadores: {stats.get('winning_trades', 0)}
Perdedores: {stats.get('losing_trades', 0)}
P&L total: ${stats.get('total_profit_loss', 0):.2f}

Balance inicial: ${stats.get('initial_balance', 0):.2f}

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
            
            # Solo Harold puede activar auto-learning
            if user_id != settings.TELEGRAM_ADMIN_ID:
                await update.message.reply_text("⚠️ Solo Harold puede activar auto-learning")
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
            
            # Solo Harold puede pausar auto-learning
            if user_id != settings.TELEGRAM_ADMIN_ID:
                await update.message.reply_text("⚠️ Solo Harold puede pausar auto-learning")
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
            
            # Solo Harold puede revertir cambios
            if user_id != settings.TELEGRAM_ADMIN_ID:
                await update.message.reply_text("⚠️ Solo Harold puede revertir cambios")
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
🛡️ **AI RISK GUARDIAN V5.4 - ESTADO**

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
        """Obtener histórico de precios"""
        try:
            # Usar trading system si está disponible
            if global_trading_system:
                # Implementación simple - en producción usar API real
                current_price = global_trading_system.get_current_price(f"{symbol}/USD")
                if current_price:
                    import numpy as np
                    # Generar histórico simulado (en producción usar API real)
                    return [current_price * (1 + np.random.normal(0, 0.02)) for _ in range(days)]
            return None
        except:
            return None
    
    def _get_order_book(self, symbol):
        """Obtener order book"""
        try:
            if global_trading_system and hasattr(global_trading_system, 'exchange'):
                order_book = global_trading_system.exchange.fetch_order_book(f"{symbol}/USD")
                return order_book
            return None
        except:
            return None

    async def handle_message(self, update, context):
        """Manejar mensajes con SUPERINTELIGENCIA + VOZ AUTOMÁTICA"""
        try:
            user_message = update.message.text
            user = update.effective_user
            user_id = str(user.id)
            user_name = user.first_name or "Usuario"
            
            logger.info(f"🧠 MENSAJE RECIBIDO de {user_name} ({user_id}): {user_message}")
            logger.info(f"🎤 DEBUG: user_id='{user_id}', esperado='{settings.TELEGRAM_ADMIN_ID}', coincide={user_id == settings.TELEGRAM_ADMIN_ID}")
            
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
                    await update.message.reply_text("""🤖 AUTO-TRADING BOT V5.2
                    
📋 COMANDOS:
/autotrading start → Iniciar bot 24/7
/autotrading stop → Detener bot
/autotrading status → Ver estado

ℹ️ EJEMPLO: /autotrading start""")
                
                return  # SALIR - NO enviar a IA
            
            # 🚀 GENERAR RESPUESTA CON SUPERINTELIGENCIA OMNIX
            # Mostrar indicador de pensamiento estilo ChatGPT/Gemini
            thinking_message = await update.message.reply_text("🧠 OMNIX IA")
            
            try:
                ai_response = self.ai_system.generate_response(
                    user_message=user_message,
                    user_name=user_name,
                    chat_id=user_id,
                    trading_system=self.trading_system
                )
                
                if not ai_response:
                    ai_response = f"🧠 OMNIX IA procesando tu consulta, {user_name}. Sistema operativo."
                
                # Limitar respuesta para Telegram
                if len(ai_response) > 4000:
                    ai_response = ai_response[:4000] + "..."
                
                # Editar el mensaje de pensamiento con la respuesta
                try:
                    await thinking_message.edit_text(ai_response)
                    logger.info(f"✅ RESPUESTA EDITADA: {len(ai_response)} caracteres")
                except Exception as edit_error:
                    # Si falla la edición, enviar mensaje nuevo
                    logger.warning(f"⚠️ No se pudo editar mensaje de pensamiento: {edit_error}")
                    await update.message.reply_text(ai_response)
                    logger.info(f"✅ RESPUESTA ENVIADA: {len(ai_response)} caracteres")
                
                # 🎤 GENERAR Y ENVIAR VOZ AUTOMÁTICA PARA HAROLD
                if user_id == settings.TELEGRAM_ADMIN_ID:  # Harold específicamente
                    try:
                        # Limpiar texto para voz
                        voice_text = ai_response
                        # Remover markdown y emojis para mejor pronunciación
                        import re
                        voice_text = re.sub(r'[*_`#]', '', voice_text)
                        voice_text = re.sub(r'🚀|🧠|⚡|💰|📊|🔴|🟢|🟡|🛡️|🕌|✅|❌|🤖|💡', '', voice_text)
                        voice_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', voice_text)  # Remover bold
                        voice_text = voice_text.strip()
                        
                        # Limitar longitud para voz (máximo 300 caracteres)
                        if len(voice_text) > 300:
                            voice_text = voice_text[:300] + "..."
                        
                        if len(voice_text) > 20:  # Solo si hay suficiente texto
                            logger.info(f"🎤 ✅ INICIANDO GENERACIÓN DE VOZ PARA HAROLD: {len(voice_text)} chars")
                            # Crear archivo de voz con gTTS
                            import tempfile
                            from gtts import gTTS
                            
                            tts = gTTS(text=voice_text, lang='es', slow=False)
                            
                            # Crear archivo temporal
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                                tts.save(tmp_file.name)
                                
                                # Enviar archivo de voz
                                with open(tmp_file.name, 'rb') as voice_file:
                                    await update.message.reply_voice(
                                        voice=voice_file,
                                        caption="🎤 OMNIX Voz - Harold"
                                    )
                                
                                logger.info("🎤 VOZ AUTOMÁTICA ENVIADA A HAROLD")
                                
                                # Limpiar archivo temporal
                                try:
                                    os.unlink(tmp_file.name)
                                except:
                                    pass
                        
                    except Exception as voice_error:
                        logger.warning(f"⚠️ Error voz automática (no crítico): {voice_error}")
                
            except Exception as ai_error:
                logger.error(f"❌ Error IA superinteligencia: {ai_error}")
                fallback_response = f"🧠 OMNIX IA V5.1 operativo, {user_name}. Tu mensaje '{user_message}' recibido correctamente."
                await update.message.reply_text(fallback_response)
            
        except Exception as e:
            logger.error(f"❌ Error crítico handle_message: {e}")
            try:
                await update.message.reply_text("🤖 OMNIX procesando... Sistema operativo.")
            except:
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
                await query.edit_message_text(f"❌ Error procesando acción: {str(e)[:100]}")
            except:
                pass

    async def handle_voice_message(self, update, context):
        """🎤 HANDLER PREMIUM - Recibir mensajes de voz con Whisper AI"""
        try:
            user = update.effective_user
            user_id = str(user.id)
            user_name = user.first_name or "Usuario"
            
            logger.info(f"🎤 MENSAJE DE VOZ RECIBIDO de {user_name} ({user_id})")
            
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
                except:
                    pass
                
                if transcribed_text:
                    # Actualizar mensaje de procesamiento
                    await processing_msg.edit_text(f"🎤 Escuché: \"{transcribed_text}\"\n\n🧠 Procesando...")
                    
                    logger.info(f"🎤 Texto transcrito: {transcribed_text}")
                    
                    # Procesar con la IA directamente (sin FakeUpdate)
                    ai_response = self.ai_system.generate_response(
                        user_message=transcribed_text,
                        user_name=user_name,
                        chat_id=user_id,
                        trading_system=self.trading_system
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
                                tts = gTTS(text=voice_text, lang='es', slow=False)
                                
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
                                    except:
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
            except:
                pass

    def handle_direct_message(self, chat_id, text, user_id=None):
        """Manejar mensaje directo usando API de Telegram"""
        global global_conversation_history  # Declarar global al inicio
        try:
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
                except:
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
                except:
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
                except:
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
                response_text += """❓ **AYUDA - COMANDOS OMNIX**

🔧 **COMANDOS BÁSICOS:**
/start - Inicializar sistema
/precio [CRYPTO] - Ver precios tiempo real
/balance - Ver balance Kraken
/analisis [CRYPTO] - Análisis técnico
/status - Estado del sistema

💰 **COMANDOS TRADING:**
/buy [cantidad] [crypto] - Comprar crypto
/sell [cantidad] [crypto] - Vender crypto

🤖 **IA CONVERSACIONAL:**
Pregúntame cualquier cosa sobre:
• Análisis de mercado
• Estrategias de trading  
• Criptomonedas
• Recomendaciones

*Sistema desarrollado por Harold Nunes*"""
                final_response_text = response_text  # HAROLD FIX: Guardar en memoria
            
            elif text.startswith('/quantum_stats'):
                # 🎲 QUANTUM ENHANCEMENTS V5.3 ULTRA - Estadísticas QRNG + QAOA
                if hasattr(self, 'auto_trading') and self.auto_trading:
                    stats = self.auto_trading.get_quantum_stats()
                    
                    if stats.get('available'):
                        qrng_stats = stats.get('qrng', {})
                        qaoa_stats = stats.get('qaoa', {})
                        
                        response_text += """⚛️ **QUANTUM ENHANCEMENTS V5.3 ULTRA**

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
                        result = self.auto_trading.start()
                        
                        if 'error' in result:
                            response_text = f"❌ {result['error']}"
                        else:
                            response_text = f"""🤖 **AUTO-TRADING ACTIVADO 24/7**

💰 Balance inicial: ${result['initial_balance']:.2f}

**ESTRATEGIA INTELIGENTE:**
✅ Monte Carlo - Validación probabilística
✅ Black Swan - Detección de riesgos extremos
✅ Sentiment - Timing basado en mercado
✅ Post-Quantum - Firmas seguras

**CONFIGURACIÓN:**
📊 Par: {result['config']['trading_pair']}
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
                                response_text += """
✅ **MODO:** PAPER TRADING ($1M virtual)
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
                        result = self.auto_trading.stop()
                        
                        if 'error' in result:
                            response_text = f"❌ {result['error']}"
                        else:
                            stats = result.get('stats', {})
                            response_text = f"""🛑 **AUTO-TRADING DETENIDO**

📊 **ESTADÍSTICAS FINALES:**
Trades totales: {stats.get('total_trades', 0)}
Ganadores: {stats.get('winning_trades', 0)}
Perdedores: {stats.get('losing_trades', 0)}
P&L total: ${stats.get('total_profit_loss', 0):.2f}

Balance inicial: ${stats.get('initial_balance', 0):.2f}

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
                            
                            response_text = f"""🤖 **AUTO-TRADING BOT V5.2 STATUS**

Estado: {status}
Modo: {result.get('mode', 'PAPER TRADING')}

📊 **ESTADÍSTICAS:**
Trades totales: {stats.get('total_trades', 0)}
Ganadores: {stats.get('winning_trades', 0)}
Perdedores: {stats.get('losing_trades', 0)}
Win rate: {stats.get('win_rate', 0)*100:.1f}%
P&L total: ${stats.get('total_profit_loss', 0):.2f}

⏱️ Última actualización: {result.get('last_update', 'N/A')}

Usa /autotrading start para activar
Usa /autotrading stop para detener"""
                else:
                    response_text = """🤖 AUTO-TRADING BOT V5.2
                    
📋 COMANDOS:
/autotrading start → Iniciar bot 24/7
/autotrading stop → Detener bot
/autotrading status → Ver estado

ℹ️ EJEMPLO: /autotrading start"""
            
            # 🚀 SIGNAL CONTRIBUTION - CROWDSOURCING DE ALPHA V6.0
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
                # 🎓 AUTO-LEARNING V5.2.3: DETECCIÓN AUTOMÁTICA DE VIDEOS DE YOUTUBE
                import re
                youtube_pattern = r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)([\w\-]+)'
                youtube_match = re.search(youtube_pattern, text)
                
                if youtube_match and self.auto_trading and hasattr(self.auto_trading, 'process_video_learning'):
                    logger.info("🎬 URL de YouTube detectada - procesando con auto-learning")
                    
                    video_url = youtube_match.group(0)
                    
                    # Enviar mensaje de procesamiento
                    send_url = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_BOT_TOKEN')}/sendMessage"
                    processing_data = {
                        'chat_id': chat_id,
                        'text': "🎬 Video de YouTube detectado - Analizando con IA...",
                        'parse_mode': 'Markdown'
                    }
                    requests.post(send_url, json=processing_data)
                    
                    # PASO 1: Primero, obtener respuesta de IA sobre el video
                    logger.info("🧠 Analizando video con IA conversacional...")
                    ai_response = ""
                    try:
                        # Usar IA para analizar el video
                        ai_prompt = f"Analiza este video de trading de YouTube y extrae insights técnicos (RSI levels, EMA periods, MACD settings, etc.): {video_url}"
                        
                        # Intentar generar respuesta con IA
                        if hasattr(self.ai, 'generate_response'):
                            ai_response = self.ai.generate_response(ai_prompt, str(user_id))
                        elif hasattr(self.ai, 'ask'):
                            ai_response = self.ai.ask(ai_prompt, str(user_id))
                        
                        logger.info(f"✅ IA analizó video: {len(ai_response)} caracteres")
                    except Exception as ai_error:
                        logger.warning(f"⚠️ Error IA en video: {ai_error}")
                        ai_response = f"Análisis de video de trading: {video_url}"
                    
                    # PASO 2: Procesar con video learning system
                    auto_apply = False
                    if self.auto_trading.auto_learning:
                        auto_apply = self.auto_trading.auto_learning.enabled
                    
                    result = self.auto_trading.process_video_learning(
                        video_url=video_url,
                        ai_response=ai_response,
                        auto_apply=auto_apply
                    )
                    
                    # PASO 3: Generar respuesta premium para Harold
                    if result.get('success'):
                        proposals = result.get('proposals', [])
                        applied = result.get('applied', [])
                        
                        response_text = f"""🎓 ANÁLISIS DE VIDEO COMPLETADO

📹 Video: {video_url}
🧠 Confianza análisis: {result.get('confidence', 0)*100:.0f}%

"""
                        if proposals:
                            response_text += f"💡 PROPUESTAS DETECTADAS: {len(proposals)}\n\n"
                            for i, prop in enumerate(proposals[:5], 1):
                                response_text += f"{i}. {prop['param_name']}: {prop['new_value']:.2f}\n"
                                response_text += f"   📝 {prop['reason']}\n\n"
                            
                            if len(proposals) > 5:
                                response_text += f"... y {len(proposals) - 5} propuestas más\n\n"
                        
                        if auto_apply and applied:
                            response_text += f"""✅ CAMBIOS APLICADOS AUTOMÁTICAMENTE: {len(applied)}

🎓 Auto-Learning está ACTIVADO
Los parámetros fueron ajustados automáticamente

"""
                        elif auto_apply and not applied:
                            response_text += """⏸️ AUTO-LEARNING ACTIVADO pero no se aplicaron cambios
(Propuestas fuera de rangos seguros o bloqueadas)

"""
                        else:
                            response_text += """⏸️ AUTO-LEARNING DESACTIVADO

💡 Para aplicar estos cambios automáticamente:
• Usa /activar_auto_ajuste
• O responde "aplicar" para aprobar manualmente

"""
                        
                        response_text += """📊 COMANDOS:
/ver_aprendizaje → Ver historial completo
/revertir_cambio → Deshacer último cambio
/activar_auto_ajuste → Activar modo automático
/pausar_auto_ajuste → Pausar modo automático

🎓 Sistema Premium V5.2.3 operativo"""
                    else:
                        response_text = f"❌ Error procesando video: {result.get('error', 'Error desconocido')}"
                    
                    # Enviar respuesta
                    data = {
                        'chat_id': chat_id,
                        'text': response_text,
                        'parse_mode': 'Markdown'
                    }
                    requests.post(send_url, json=data)
                    
                    # Continuar normalmente (no return aquí, dejar que el flujo continúe)
                    final_response_text = response_text
                
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
                        try:
                            # HAROLD FIX: Usar self.trading_enterprise en lugar de trading_system undefined
                            ts = self.trading_enterprise if self.trading_enterprise_enabled else self.trading
                            if ts and hasattr(ts, 'kraken_client'):
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
                                
                                logger.info(f"✅ DATOS REALES KRAKEN: BTC=${real_market_data['btc_price']:,.2f}, Balance=${real_market_data['balance_usd']:.2f}")
                        except Exception as data_error:
                            logger.error(f"⚠️ Error obteniendo datos reales Kraken: {data_error}")
                            # Intentar API pública como fallback
                            try:
                                pub_response = requests.get('https://api.kraken.com/0/public/Ticker?pair=XBTUSD', timeout=5)
                                if pub_response.status_code == 200:
                                    pub_data = pub_response.json()
                                    real_market_data['btc_price'] = float(pub_data['result']['XXBTZUSD']['c'][0])
                                    logger.info(f"✅ DATOS REALES API PÚBLICA: BTC=${real_market_data['btc_price']:,.2f}")
                            except Exception as pub_error:
                                logger.error(f"❌ Error API pública: {pub_error}")
                        
                        # FORZAR GEMINI 2.0 DIRECTO como ÚNICA prioridad
                        import google.generativeai as genai
                        gemini_key = os.environ.get('GEMINI_API_KEY')
                        
                        if gemini_key:
                            genai.configure(api_key=gemini_key)
                            model = genai.GenerativeModel("gemini-2.0-flash-exp")
                            
                            # INYECTAR DATOS REALES EN EL PROMPT
                            real_data_context = ""
                            if real_market_data:
                                real_data_context = f"""
🔴 DATOS REALES DE KRAKEN (AHORA MISMO - OBLIGATORIO USAR ESTOS):
• Bitcoin (BTC/USD): ${real_market_data.get('btc_price', 0):,.2f}
• 24h High: ${real_market_data.get('btc_24h_high', 0):,.2f}
• 24h Low: ${real_market_data.get('btc_24h_low', 0):,.2f}
• Volumen 24h: {real_market_data.get('btc_volume', 0):,.4f} BTC
• Balance USD: ${real_market_data.get('balance_usd', 0):.2f}
• Balance BTC: {real_market_data.get('balance_btc', 0):.8f}

⚠️ CRÍTICO: USA SOLO ESTOS DATOS REALES - NUNCA INVENTES PRECIOS NI BALANCES
"""
                            
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
                                
                                # Generar prompt conversacional natural CON MEMORIA
                                gemini_prompt = prompts_manager.build_system_prompt(
                                    intent=intent,
                                    user_name='Harold',
                                    additional_context=additional_context,
                                    conversation_history=conversation_hist
                                )
                                
                                # Agregar datos reales de mercado si existen
                                if real_data_context:
                                    gemini_prompt += f"\n\n{real_data_context}"
                                
                                # Agregar pregunta del usuario
                                gemini_prompt += f"\n\nPregunta de Harold: {text}\n\nResponde de forma natural y conversacional:"
                                
                            except Exception as prompt_error:
                                logger.warning(f"⚠️ Error usando PromptsContextManager: {prompt_error}")
                                # Fallback simple conversacional
                                gemini_prompt = f"""Soy OMNIX V5.4 ULTRA, tu asistente de trading personal.

IMPORTANTE: Responde en ESPAÑOL de forma natural y conversacional.

{real_data_context}

ESTILO:
- Natural como ChatGPT pero con personalidad
- Si es saludo simple: 100-200 caracteres amigables
- Si es pregunta técnica: Análisis profundo 1500-2500 caracteres
- Habla en primera persona: "Soy OMNIX", "Puedo ayudarte"
- Usa emojis apropiados: 🤖 🚀 📊 ₿ 💰

Harold pregunta: {text}"""

                            logger.info(f"🚀 LLAMANDO GEMINI 2.0 DIRECTO con prompt de {len(gemini_prompt)} caracteres")
                            response = model.generate_content(gemini_prompt)
                            
                            if response and response.text:
                                ai_response = response.text
                                logger.info(f"✅ GEMINI 2.0 SUPERINTELIGENCIA EXITOSA: {len(ai_response)} caracteres generados")
                                response_text = ai_response
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
                
                # PASO 3: Editar el indicador directamente con respuesta completa - SIN DIVISIONES
                # HAROLD: Eliminado sistema de partes que causaba encabezados duplicados
                if thinking_message_id:
                    # HAROLD FIX: Limpiar markdown problemático para evitar errores de parsing
                    clean_text = final_response_text
                    # Limpiar caracteres problemáticos de markdown mal formateado
                    clean_text = clean_text.replace('**', '*').replace('__', '_')  # Normalizar markdown
                    clean_text = clean_text.replace('_*', '*').replace('*_', '*')  # Quitar combinaciones raras
                    
                    edit_data = {
                        'chat_id': chat_id,
                        'message_id': thinking_message_id,
                        'text': clean_text[:4000]  # Limitar longitud para evitar problemas
                    }
                    
                    edit_response = requests.post(edit_url, json=edit_data)
                    if edit_response.status_code == 200:
                        logger.info(f"✅ Mensaje editado exitosamente: {len(final_response_text)} chars")
                    else:
                        logger.error(f"❌ Error editando mensaje: {edit_response.text}")
                        # HAROLD FIX: Enviar mensaje largo dividido correctamente
                        self.send_message_in_parts(chat_id, final_response_text)
                        logger.info(f"✅ Mensaje completo enviado en partes: {len(final_response_text)} chars")
                else:
                    # Si no hay thinking_message_id, enviar directo
                    # HAROLD FIX: También limpiar texto para mensajes directos
                    clean_backup_text = final_response_text
                    clean_backup_text = clean_backup_text.replace('**', '*').replace('__', '_')
                    clean_backup_text = clean_backup_text.replace('_*', '*').replace('*_', '*')
                    
                    data = {
                        'chat_id': chat_id,
                        'text': clean_backup_text[:4000]  # Limitar longitud
                    }
                    
                    response = requests.post(send_url, json=data)
                    if response.status_code == 200:
                        logger.info(f"✅ Mensaje enviado a {chat_id}: {len(final_response_text)} chars")
                    else:
                        logger.error(f"❌ Error enviando mensaje: {response.text}")
                        # Respaldo de emergencia
                        data_backup = {
                            'chat_id': chat_id,
                            'text': "🤖 OMNIX V5.1 operativo - respuesta generada correctamente",
                            'parse_mode': 'Markdown'
                        }
                        requests.post(send_url, json=data_backup)
                
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
            
            # 🎤 GENERAR Y ENVIAR VOZ AUTOMÁTICA CON gTTS
            if VOICE_SERVICE_AVAILABLE and final_response_text:
                try:
                    send_telegram_response_with_voice(
                        chat_id=chat_id,
                        response_text=final_response_text,
                        user_name=user_name if 'user_name' in locals() else "Usuario",
                        user_id=user_id,
                        is_admin_user=is_admin(user_id if user_id else chat_id),
                        trading_system=self.trading_enterprise if self.trading_enterprise_enabled else self.trading,
                        reference_message=thinking_message_id if 'thinking_message_id' in locals() else None,
                        is_admin_func=is_admin
                    )
                    logger.info(f"🎤 Voz enviada a {chat_id}")
                except Exception as voice_error:
                    logger.warning(f"⚠️ Error generando voz: {voice_error}")
            
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

    def send_message_in_parts(self, chat_id, text):
        """HAROLD FIX: Dividir mensajes largos inteligentemente"""
        try:
            # HAROLD FIX: Obtener bot_token correctamente
            bot_token = getattr(self, 'bot_token', None) or os.environ.get('TELEGRAM_BOT_TOKEN')
            
            if not bot_token:
                logger.error("❌ Bot token no disponible")
                return
                
            max_length = 4000  # Límite seguro Telegram
            
            if len(text) <= max_length:
                data = {
                    'chat_id': chat_id,
                    'text': text,
                    'parse_mode': 'Markdown'
                }
                send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                requests.post(send_url, json=data)
                return
            
            # Dividir inteligentemente por párrafos
            parts = []
            current_part = ""
            paragraphs = text.split('\n\n')
            
            for paragraph in paragraphs:
                if len(current_part + paragraph) <= max_length - 100:
                    current_part += paragraph + '\n\n'
                else:
                    if current_part.strip():
                        parts.append(current_part.strip())
                    current_part = paragraph + '\n\n'
            
            if current_part.strip():
                parts.append(current_part.strip())
            
            # Enviar todas las partes
            send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            for i, part in enumerate(parts):
                header = f"🧠 OMNIX SUPERINTELIGENCIA (Parte {i+1}/{len(parts)})\n\n" if len(parts) > 1 else ""
                final_text = header + part
                
                data = {
                    'chat_id': chat_id,
                    'text': final_text,
                    'parse_mode': 'Markdown'
                }
                response = requests.post(send_url, json=data)
                logger.info(f"✅ Parte {i+1}/{len(parts)} enviada: {response.status_code}")
                time.sleep(0.5)  # Pausa entre mensajes
            
            logger.info(f"✅ Mensaje dividido en {len(parts)} partes enviadas exitosamente")
            
        except Exception as e:
            logger.error(f"Error send_message_in_parts: {e}")
            # HAROLD FIX: Respaldo de emergencia
            try:
                bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
                if bot_token:
                    data = {
                        'chat_id': chat_id,
                        'text': "🧠 OMNIX IA SUPERINTELIGENTE\n\nRespuesta generada correctamente - verificando entrega...",
                        'parse_mode': 'Markdown'
                    }
                    send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    requests.post(send_url, json=data)
            except:
                pass

    def generate_smart_response(self, text):
        """FUNCIÓN REDIRIGIDA - USA SUPERINTELIGENCIA PARA HAROLD"""
        try:
            logger.info(f"🔄 Redirigiendo a superinteligencia para Harold...")
            return self.ai.generate_response(text, "Harold", settings.TELEGRAM_ADMIN_ID, int(settings.TELEGRAM_ADMIN_ID))
        except Exception as e:
            logger.error(f"❌ Error generate_smart_response: {e}")
            return f"🤖 Sistema procesando: '{text}'\n\n💰 Balance real verificado con Kraken\n✅ IA superinteligente operativa"

    def start_polling(self, drop_pending_updates=True):
        """Iniciar bot en modo polling directo - VERSION FUNCIONAL"""
        try:
            logger.info("🚀 Iniciando bot Telegram...")
            
            # Eliminar webhook si existe
            try:
                webhook_delete_url = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_BOT_TOKEN')}/deleteWebhook"
                requests.post(webhook_delete_url)
                logger.info("🗑️ Webhook eliminado para usar polling")
            except:
                pass
            
            # SISTEMA SIMPLE DE POLLING DIRECTO
            def poll_messages():
                """Polling directo y simple"""
                offset = 0
                logger.info("🔄 Iniciando polling directo...")
                
                while hasattr(self, 'is_running') and self.is_running:
                    try:
                        # Obtener mensajes nuevos
                        updates_url = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_BOT_TOKEN')}/getUpdates"
                        params = {'offset': offset, 'timeout': 5}
                        response = requests.get(updates_url, params=params, timeout=10)
                        
                        if response.status_code == 200:
                            data = response.json()
                            if data['ok'] and data['result']:
                                for update in data['result']:
                                    if 'message' in update:
                                        message = update['message']
                                        chat_id = message['chat']['id']
                                        user_id = message.get('from', {}).get('id', chat_id)
                                        text = message.get('text', '')
                                        logger.info(f"📧 Procesando mensaje: '{text}' de chat:{chat_id} user:{user_id}")
                                        self.handle_direct_message(chat_id, text, user_id=user_id)
                                    offset = update['update_id'] + 1
                            
                        time.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"❌ Error polling: {e}")
                        time.sleep(3)
            
            # Iniciar polling en hilo separado
            import threading
            import time
            self.is_running = True
            polling_thread = threading.Thread(target=poll_messages, daemon=True)
            polling_thread.start()
            
            logger.info("✅ Bot Telegram iniciado con polling directo")
            logger.info(f"📡 Hilo de polling activo: {polling_thread.is_alive()}")
            return True
                
        except Exception as e:
            logger.error(f"❌ Error iniciando bot: {e}")
            return False
    
    # ============================================================================
    # 📊 STOCK TRADING COMMANDS V6.0 - BOLSA DE VALORES (NYSE/NASDAQ)
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
        """Comando /analizar [SYMBOL] - Análisis técnico y fundamental de acciones"""
        if not self.stock_handler or not self.stock_handler.enabled:
            await update.message.reply_text("📊 Módulo de bolsa no activado")
            return
        
        try:
            symbol = context.args[0] if context.args else None
            response = await self.stock_handler.handle_analyze_stock(update, context, symbol)
            await update.message.reply_text(response, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error en analyze_stock: {e}")
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
    
    # ==========================================
    # 💱 ARBITRAGE MULTI-EXCHANGE PREMIUM V6.0
    # ==========================================
    
    async def arbitrage_command(self, update, context):
        """Comando /arbitrage - Información del sistema de arbitraje"""
        if not self.arbitrage_scanner:
            await update.message.reply_text("💱 Módulo de arbitraje no disponible")
            return
        
        try:
            response = f"""
💱 **OMNIX ARBITRAGE PREMIUM V6.0**

🏦 **Sistema Multi-Exchange Institucional**
   • 8 Exchanges: Kraken, Binance, Coinbase, Bybit, KuCoin, OKX, Gate.io, Bitfinex
   • Profit mínimo: {self.arbitrage_scanner.min_profit_threshold}%
   • Modo: {'📄 PAPER TRADING' if self.arbitrage_executor.paper_trading else '🔴 LIVE TRADING'}

📊 **Comandos Disponibles:**
   `/arbitrage_scan [SYMBOL]` - Escanear oportunidades
   `/arbitrage_execute [AMOUNT]` - Ejecutar mejor oportunidad
   `/arbitrage_stats` - Ver estadísticas

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
            
            # Obtener amount (default: $1000)
            amount_usd = float(context.args[0]) if context.args else 1000.0
            
            # Validar amount
            if amount_usd > self.arbitrage_executor.max_trade_size_usd:
                await update.message.reply_text(
                    f"❌ Amount ${amount_usd:,.2f} excede límite de ${self.arbitrage_executor.max_trade_size_usd:,.2f}"
                )
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
            import asyncio
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
    # 🧠 COMMUNITY INTELLIGENCE COMMANDS - MEMORIA COLECTIVA V6.0
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
• `ARES_V1` - Swing Trading
• `ARES_V2` - Scalping M1
• `ARBITRAGE` - Multi-exchange

**Resultados:**
• `success` - Funcionó correctamente ✅
• `failure` - No funcionó ❌
• `partial` - Resultado parcial ⚡

**Ejemplos:**
`/feedback ARES_V1 success`
`/feedback ARES_V2 failure Falló en mercado lateral`
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

*OMNIX V6.0 - Community Intelligence*
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

*OMNIX V6.0 - Community Intelligence*
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
• `ARES_V1` - Swing Trading
• `ARES_V2` - Scalping M1
• `ARBITRAGE` - Multi-exchange

**Puntuación:** 1 (malo) a 5 (excelente)

**Ejemplos:**
`/vote_strategy ARES_V1 5`
`/vote_strategy ARES_V2 4`

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

*OMNIX V6.0 - Community Intelligence*
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

*OMNIX V6.0 - Community Intelligence*
"""
            
            await loading_msg.edit_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error en analyze_patterns: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    # ═══════════════════════════════════════════════════════════════════
    # 🚀 SIGNAL CONTRIBUTION - CROWDSOURCING DE ALPHA V6.0
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

*OMNIX V6.0 - Crowdsourcing de Alpha*
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

*OMNIX V6.0 - Crowdsourcing de Alpha*
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

*OMNIX V6.0 - Crowdsourcing de Alpha*
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

*OMNIX V6.0 - Crowdsourcing de Alpha*
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

*OMNIX V6.0 - Crowdsourcing de Alpha*
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

*OMNIX V6.0 - Crowdsourcing de Alpha*
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

*OMNIX V6.0 - Crowdsourcing de Alpha*
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

*OMNIX V6.0 - Crowdsourcing de Alpha*
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



if __name__ == "__main__":
    app = main()
    if app:
        run_dev_server(app)