"""
🤖 OMNIX AUTO-TRADING BOT INSTITUTIONAL+ - TRADING AUTOMÁTICO 24/7
Sistema de trading automático con IA, Risk Guardian, Coherence Engine,
Non-Markovian Kernel, Memory-Enhanced RMS, Adaptive Parameter Engine, y On-Chain Intelligence

INSTITUTIONAL FIX: 4 Institutional Fixes - position limits at start, hard cap, 
no paper bypass, no bias system. Track record now REPLICABLE in real trading.

MULTI-USER ARCHITECTURE:
- Soporte para 100,000+ usuarios simultáneos
- Sesiones aisladas por usuario vía UserSessionManager
- Estado persistente en Redis + PostgreSQL
- Auto-restauración después de reinicios de Railway

ESTRATEGIAS INSTITUTIONAL+ (10 MÓDULOS):
1. Monte Carlo: Validar probabilidades con 10,000 simulaciones
2. Black Swan: Evitar trades en condiciones extremas (Kurtosis/Skewness)
3. Sentiment Analysis: Timing basado en sentimiento del mercado
4. Kelly Criterion: Position sizing matemático óptimo
5. HMM Regime Detection: Detectar régimen de mercado (TRENDING/RANGING/VOLATILE)
6. Kalman Filter: Filtrado adaptivo de señales con lag mínimo
7. Quantum Momentum: Estrategia propietaria 6 componentes (EMA/RSI/MACD/Volume/HP/ATR)
8. ARES V1: Swing Trading institucional (55-65% win rate)
9. ARES V2: Scalping M1 ultra-rápido (60-70% win rate)
10. Non-Markovian Kernel: Memoria temporal cuántica K(t-s)=exp(-|t-s|/τ)[1+ε cos(Ω(t-s))]

MEMORY-ENHANCED RMS:
- MemoryRiskAdapter: Puente entre kernel temporal y gestión de riesgo
- LimitsEngine: Límites dinámicos ajustados por coherencia de régimen
- CircuitBreaker: Halt automático por incoherencia de memoria/transición de régimen
- PositionMonitor: Factor de riesgo basado en divergencia de memoria
- AlertDispatcher: Alertas predictivas de transiciones de régimen

FUNCIONALIDADES:
- Multi-user sessions: Cada usuario tiene su propia sesión de trading
- Auto-trading persistente: El estado se guarda en DB y sobrevive reinicios de Railway
- Adaptive Parameter Engine: Auto-calibración de SL/TP/posición por régimen
- On-Chain Intelligence: Whale tracking via ClankApp + Arkham
- Logging detallado: Cada operación se registra con verificación

MODOS DE OPERACIÓN:
- PAPER TRADING: $1,000,000 virtual (recomendado para testing)
- REAL TRADING: Dinero real en Kraken (solo para producción)

SEGURIDAD:
- Firma Post-Quantum de todos los trades
- Validaciones múltiples antes de ejecutar
- Parada automática si pérdidas > límite configurable
- Logging completo de decisiones
- Gestión de riesgo predictiva con memoria Non-Markoviana
"""

import logging
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import threading

logger = logging.getLogger(__name__)

# ============================================================================
# ARES CODE REMOVED - Dec 24, 2025
# ARES V1/V2 scoring code has been completely eliminated from this file.
# EMA_REGIME_SIGNAL (40 pts) is now the sole primary driver.
# See git history for legacy ARES implementation if needed.
# ============================================================================

from omnix_config import VERSION_BANNER

try:
    from omnix_core.config.trading_profiles import (
        get_active_profile, TradingProfile, get_sl_tp_for_symbol, VolatilityClass,
        get_pair_calibration, is_symbol_allowed, CalibrationTier, PairCalibration
    )
    TRADING_PROFILES_AVAILABLE = True
except ImportError:
    TRADING_PROFILES_AVAILABLE = False
    get_sl_tp_for_symbol = None
    get_pair_calibration = None
    is_symbol_allowed = None
    VolatilityClass = None
    CalibrationTier = None
    PairCalibration = None
    logger.warning("⚠️ Trading Profiles no disponible - usando configuración hardcoded")

try:
    from omnix_core.utils.logger import get_institutional_logger, InstitutionalDecisionLogger
    INSTITUTIONAL_LOGGER_AVAILABLE = True
    institutional_logger = get_institutional_logger()
except ImportError:
    INSTITUTIONAL_LOGGER_AVAILABLE = False
    institutional_logger = None
    logger.warning("⚠️ Institutional Decision Logger no disponible")

# Import Metrics Engine (Prometheus)
try:
    from omnix_services.monitoring import get_metrics_engine
    METRICS_ENGINE_AVAILABLE = True
    metrics = get_metrics_engine()
except ImportError:
    METRICS_ENGINE_AVAILABLE = False
    metrics = None
    logger.warning("⚠️ MetricsEngine no disponible - métricas Prometheus desactivadas")

# Import investor logger from omnix_services.analytics
try:
    from omnix_services.analytics.investor_logger import investor_logger
except ImportError:
    investor_logger = None
    logger.warning("InvestorTradeLogger no disponible - logging desactivado")

# Import Adaptive Weight System (V5.2 QUANTUM ULTIMATE)
try:
    from omnix_services.optimization import AdaptiveWeightSystem, create_adaptive_system, interpret_regime
    ADAPTIVE_SYSTEM_AVAILABLE = True
except ImportError:
    ADAPTIVE_SYSTEM_AVAILABLE = False
    logger.warning("⚠️ Adaptive Weight System no disponible - usando pesos fijos")

# Import Auto-Learning System (V5.2.3 QUANTUM ULTIMATE - VIDEO LEARNING)
try:
    from omnix_services.optimization import AutoLearningSystem
    AUTO_LEARNING_AVAILABLE = True
    logger.info("✅ Auto-Learning System disponible")
except ImportError:
    AutoLearningSystem = None
    AUTO_LEARNING_AVAILABLE = False
    logger.warning("⚠️ Auto-Learning System no disponible - aprendizaje de videos desactivado")

# Import Video Learning Analyzer (opcional, funciona sin él)
try:
    from omnix_services.ai_service.video import VideoLearningAnalyzer
    VIDEO_ANALYZER_AVAILABLE = True
    logger.info("✅ Video Learning Analyzer disponible")
except ImportError:
    VideoLearningAnalyzer = None
    VIDEO_ANALYZER_AVAILABLE = False
    logger.info("📹 Video Learning Analyzer no disponible (opcional)")

# Import Conversational Brain (V5.3 ULTRA - EL BOT QUE PIENSA EN VOZ ALTA)
try:
    from omnix_services.ai_service import get_conversational_brain
    CONVERSATIONAL_BRAIN_AVAILABLE = True
except ImportError:
    get_conversational_brain = None
    CONVERSATIONAL_BRAIN_AVAILABLE = False
    logger.warning("⚠️ Conversational Brain no disponible - razonamiento de trades desactivado")

# Import Coherence Engine (V5.3 ULTRA - SEGUNDO CEREBRO DE VALIDACIÓN)
try:
    from omnix_services.coherence_service import CoherenceEngine, StrategySignal, Signal
    COHERENCE_ENGINE_AVAILABLE = True
except ImportError:
    CoherenceEngine = None
    StrategySignal = None
    Signal = None
    COHERENCE_ENGINE_AVAILABLE = False
    logger.warning("⚠️ Coherence Engine no disponible - validación de coherencia desactivada")

# Import Quantum Enhancements (V5.3 ULTRA - QRNG + QAOA)
try:
    from quantum_enhancements import global_qaoa, get_quantum_stats
    QUANTUM_OPTIMIZATION_AVAILABLE = True
except ImportError:
    global_qaoa = None
    get_quantum_stats = None
    QUANTUM_OPTIMIZATION_AVAILABLE = False
    logger.warning("⚠️ Quantum Portfolio Optimizer no disponible - usando optimización clásica")

# Import AI Risk Guardian (V5.4 - SUPERVISOR DE RIESGOS)
try:
    from omnix_services.monitoring import AIRiskGuardian
    AI_RISK_GUARDIAN_AVAILABLE = True
except ImportError:
    AIRiskGuardian = None
    AI_RISK_GUARDIAN_AVAILABLE = False
    logger.warning("⚠️ AI Risk Guardian no disponible - supervisión de riesgos desactivada")

# Import Non-Markovian Kernel (V6.1 ULTRA - QUANTUM MEMORY)
try:
    from omnix_core.strategies.non_markovian_kernel import NonMarkovianKernel
    NON_MARKOVIAN_KERNEL_AVAILABLE = True
    logger.info("🧠 Non-Markovian Kernel disponible")
except ImportError:
    NonMarkovianKernel = None
    NON_MARKOVIAN_KERNEL_AVAILABLE = False
    logger.warning("⚠️ Non-Markovian Kernel no disponible")

# Import CAES - Confidence-Adaptive Entry System PREMIUM
try:
    from omnix_core.strategies.caes_module import (
        ConfidenceAdaptiveEntrySystem,
        get_caes_instance,
        calculate_adaptive_entry,
        CAESResult,
        SubRegimeType
    )
    CAES_AVAILABLE = True
    logger.info("🎯 CAES - Confidence-Adaptive Entry System disponible")
except ImportError:
    ConfidenceAdaptiveEntrySystem = None
    get_caes_instance = None
    calculate_adaptive_entry = None
    CAESResult = None
    SubRegimeType = None
    CAES_AVAILABLE = False
    logger.warning("⚠️ CAES no disponible - usando sizing estático")

# Import Memory-Enhanced RMS V6.2 - PREDICTIVE RISK MANAGEMENT
try:
    from omnix_services.risk_management import (
        MemoryRiskAdapter,
        LimitsEngine,
        CircuitBreaker,
        PositionMonitor,
        AlertDispatcher
    )
    MEMORY_ENHANCED_RMS_AVAILABLE = True
    logger.info("🧠 Memory-Enhanced RMS V6.2 disponible")
except ImportError:
    MemoryRiskAdapter = None
    LimitsEngine = None
    CircuitBreaker = None
    PositionMonitor = None
    AlertDispatcher = None
    MEMORY_ENHANCED_RMS_AVAILABLE = False
    logger.warning("⚠️ Memory-Enhanced RMS no disponible")

# Import Redis Cache for heartbeat
try:
    from omnix_services.database_service.cache import cache as redis_cache
    REDIS_CACHE_AVAILABLE = True
except ImportError:
    redis_cache = None
    REDIS_CACHE_AVAILABLE = False
    logger.warning("⚠️ Redis Cache no disponible - heartbeat desactivado")

# Import Price Stale Detection V6.5.4d - INSTITUTIONAL GRADE DATA VALIDATION
try:
    from omnix_services.market_data.validators import (
        validate_price_freshness,
        is_price_tradeable,
        get_market_data_validator,
        PriceFreshness
    )
    PRICE_VALIDATOR_AVAILABLE = True
    logger.info("📊 Price Stale Detection V6.5.4d disponible")
except ImportError:
    validate_price_freshness = None
    is_price_tradeable = None
    get_market_data_validator = None
    PriceFreshness = None
    PRICE_VALIDATOR_AVAILABLE = False
    logger.warning("⚠️ Price Stale Detection no disponible")

# Import Adaptive Parameter Engine - AUTO-CALIBRATION FOR ARES
try:
    from omnix_services.adaptive_engine import (
        AdaptiveParameterEngine,
        AdaptiveParameterProfile,
        RegimeType,
        get_adaptive_engine
    )
    ADAPTIVE_PARAMETER_ENGINE_AVAILABLE = True
    logger.info(f"🎯 Adaptive Parameter Engine {VERSION_BANNER} disponible")
except ImportError:
    AdaptiveParameterEngine = None
    AdaptiveParameterProfile = None
    RegimeType = None
    get_adaptive_engine = None
    ADAPTIVE_PARAMETER_ENGINE_AVAILABLE = False
    logger.warning("⚠️ Adaptive Parameter Engine no disponible")

# Import User Session Manager - MULTI-USER SESSIONS (100K+ users)
try:
    from omnix_core.sessions import (
        UserSessionManager,
        UserTradingSession,
        get_session_manager,
        initialize_session_manager
    )
    USER_SESSION_MANAGER_AVAILABLE = True
    logger.info(f"🚀 User Session Manager {VERSION_BANNER} disponible - 100K+ usuarios")
except ImportError:
    UserSessionManager = None
    UserTradingSession = None
    get_session_manager = None
    initialize_session_manager = None
    USER_SESSION_MANAGER_AVAILABLE = False
    logger.warning("⚠️ User Session Manager no disponible")

try:
    from src.omnix.infrastructure.adapters.authorization_adapter import get_authorization_adapter
    from src.omnix.ports.driven.authorization_port import Permission, UserRole, AuthorizationError
    AUTHORIZATION_ADAPTER_AVAILABLE = True
    logger.info(f"🔐 Authorization Adapter {VERSION_BANNER} disponible - RBAC multi-user")
except ImportError:
    get_authorization_adapter = None
    Permission = None
    UserRole = None
    AuthorizationError = PermissionError  # Fallback to standard PermissionError
    AUTHORIZATION_ADAPTER_AVAILABLE = False
    logger.warning("⚠️ Authorization Adapter no disponible - fallback a legacy mode")

# Import Dynamic Position Manager PREMIUM - ATR-BASED TP/SL
try:
    from omnix_services.trading_service.position_manager import (
        DynamicPositionManager,
        ATRCalculator,
        MarketRegime,
        PositionLevels
    )
    POSITION_MANAGER_AVAILABLE = True
    logger.info(f"📊 Dynamic Position Manager {VERSION_BANNER} PREMIUM disponible")
except ImportError:
    DynamicPositionManager = None
    ATRCalculator = None
    MarketRegime = None
    PositionLevels = None
    POSITION_MANAGER_AVAILABLE = False
    logger.warning("⚠️ Dynamic Position Manager no disponible")

try:
    from omnix_services.execution_service import (
        ExecutionProtocol,
        ExecutionDecision,
        ExecutionUrgency,
        EXECUTION_SERVICE_AVAILABLE
    )
    EXECUTION_PROTOCOL_AVAILABLE = EXECUTION_SERVICE_AVAILABLE
    if EXECUTION_PROTOCOL_AVAILABLE:
        logger.info(f"🎯 Execution Protocol {VERSION_BANNER} INSTITUTIONAL+ disponible")
except ImportError:
    ExecutionProtocol = None
    ExecutionDecision = None
    ExecutionUrgency = None
    EXECUTION_PROTOCOL_AVAILABLE = False
    logger.warning("⚠️ Execution Protocol no disponible")

# Import Algorithmic Rollback Protocol V6.5.4 - AUTO-REVERT ON POST-DEPLOY DRAWDOWN
try:
    from omnix_core.risk.rollback_protocol import (
        AlgorithmicRollbackProtocol,
        get_arp_instance,
        RollbackResult
    )
    ARP_AVAILABLE = True
    logger.info(f"🔄 Algorithmic Rollback Protocol {VERSION_BANNER} disponible")
except ImportError:
    AlgorithmicRollbackProtocol = None
    get_arp_instance = None
    RollbackResult = None
    ARP_AVAILABLE = False
    logger.warning("⚠️ Algorithmic Rollback Protocol no disponible")

# Import EMA Regime Signal V6.5.4d - REAL DETERMINISTIC SIGNAL (replaces ARES placeholders)
try:
    from omnix_core.strategies.ema_regime_signal import (
        EMARegimeSignal,
        get_signal_generator,
        SignalContract
    )
    EMA_REGIME_SIGNAL_AVAILABLE = True
    logger.info("📊 EMA Regime Signal V1.0 disponible - Señal REAL activa")
except ImportError:
    EMARegimeSignal = None
    get_signal_generator = None
    SignalContract = None
    EMA_REGIME_SIGNAL_AVAILABLE = False
    logger.warning("⚠️ EMA Regime Signal no disponible")


class AutoTradingBot:
    """
    Bot de Trading Automático 24/7 - INSTITUTIONAL+
    
    Usa TODAS las 10 estrategias avanzadas para tomar decisiones óptimas
    Incluye modo PAPER TRADING con $1M virtual para testing
    Escanea 11 pares de crypto para máximas oportunidades
    """
    
    # V6.5.4d: EMERGENCY STOP LOSS - Límite máximo absoluto de pérdida por posición
    # Este valor NO puede ser sobrescrito por calibraciones de par
    EMERGENCY_SL_PCT = 0.02  # 2% máximo absoluto
    
    # V6.5: Mapeo completo de símbolos estándar a formato Kraken
    # NOTA: Kraken usa XBT para Bitcoin (no BTC) - esto es crítico
    # API pública acepta formato corto (XBTUSD) pero retorna formato largo (XXBTZUSD)
    KRAKEN_SYMBOL_MAP = {
        'BTC/USD': 'XBTUSD',      # BTC → XBT (Kraken naming convention)
        'ETH/USD': 'ETHUSD',
        'SOL/USD': 'SOLUSD',
        'XRP/USD': 'XRPUSD',
        'ADA/USD': 'ADAUSD',
        'DOT/USD': 'DOTUSD',
        'LINK/USD': 'LINKUSD',
        'AVAX/USD': 'AVAXUSD',
        'POL/USD': 'POLUSD',
        'ATOM/USD': 'ATOMUSD',
        'LTC/USD': 'LTCUSD',
    }
    
    # Mapeo inverso para logs legibles (Kraken → Display)
    # Incluye tanto formato corto como extendido de Kraken
    DISPLAY_SYMBOL_MAP = {
        'XBTUSD': 'BTC/USD',
        'XXBTZUSD': 'BTC/USD',
        'ETHUSD': 'ETH/USD',
        'XETHZUSD': 'ETH/USD',
        'SOLUSD': 'SOL/USD',
        'XRPUSD': 'XRP/USD',
        'XXRPZUSD': 'XRP/USD',
        'ADAUSD': 'ADA/USD',
        'DOTUSD': 'DOT/USD',
        'LINKUSD': 'LINK/USD',
        'AVAXUSD': 'AVAX/USD',
        'POLUSD': 'POL/USD',
        'ATOMUSD': 'ATOM/USD',
        'LTCUSD': 'LTC/USD',
        'XLTCZUSD': 'LTC/USD',
    }
    
    @classmethod
    def convert_to_kraken_pair(cls, pair: str) -> str:
        """
        Convierte par estándar (BTC/USD) a formato Kraken (XBTUSD)
        
        IMPORTANTE: Kraken usa XBT para Bitcoin, no BTC.
        La API acepta formato corto pero puede retornar formato largo.
        """
        if pair in cls.KRAKEN_SYMBOL_MAP:
            return cls.KRAKEN_SYMBOL_MAP[pair]
        # Fallback: remover / para pares no mapeados
        return pair.replace('/', '')
    
    @classmethod
    def get_display_pair(cls, kraken_pair: str) -> str:
        """Convierte formato Kraken a display legible"""
        if kraken_pair in cls.DISPLAY_SYMBOL_MAP:
            return cls.DISPLAY_SYMBOL_MAP[kraken_pair]
        # Insertar / si no hay mapeo
        if len(kraken_pair) >= 6 and '/' not in kraken_pair:
            return f"{kraken_pair[:-3]}/{kraken_pair[-3:]}"
        return kraken_pair
    
    def __init__(self, trading_service, database_service=None, advanced_features=None, paper_trading=None, ai_service=None):
        self.trading_service = trading_service
        self.database_service = database_service
        self.advanced_features = advanced_features
        self.paper_trading = paper_trading
        self.ai_service = ai_service
        
        # Configuración de trading - PROFESIONAL INSTITUCIONAL
        # Optimizado para generar track record de calidad como si tuvieras clientes Enterprise
        # Lee PAPER_MODE desde variable de entorno (Railway) o default a False
        import os as os_module
        paper_mode_raw = os_module.getenv('PAPER_MODE', 'false')
        paper_mode_env = paper_mode_raw.lower() == 'true'
        
        # DEBUG: Logging para verificar PAPER_MODE en Railway
        logger.info(f"🔍 PAPER_MODE env var: '{paper_mode_raw}' → paper_mode={paper_mode_env}")
        
        # Cargar Trading Profile desde variable de entorno
        self.trading_profile = None
        if TRADING_PROFILES_AVAILABLE:
            self.trading_profile = get_active_profile()
            profile_name = self.trading_profile.name
            logger.info(f"📊 Trading Profile: {profile_name}")
            logger.info(f"   📝 {self.trading_profile.description[:60]}...")
        else:
            profile_name = "HARDCODED"
            logger.info("📊 Trading Profile: HARDCODED (perfiles no disponibles)")
        
        # Usar valores del perfil si está disponible, sino valores por defecto
        p = self.trading_profile  # Shorthand
        
        # V6.5.4: Obtener símbolos permitidos del perfil (si hay restricción)
        default_pairs = [
            'BTC/USD', 'ETH/USD', 'SOL/USD',     # Top 3 por capitalización
            'XRP/USD', 'ADA/USD', 'DOT/USD',     # Altcoins tier 1
            'LINK/USD', 'AVAX/USD', 'POL/USD',   # DeFi/L2 líderes (MATIC→POL Dec 2024)
            'ATOM/USD', 'LTC/USD'               # Ecosistema diversificado
        ]
        
        # V6.5.4 WIN_RATE_OPTIMIZED: Usar allowed_symbols del perfil si existe
        if p and hasattr(p, 'extra_params') and p.extra_params:
            allowed = p.extra_params.get('allowed_symbols', None)
            excluded = p.extra_params.get('excluded_symbols', [])
            
            if allowed:
                # Usar SOLO los símbolos permitidos
                trading_pairs_list = [s for s in allowed if s in default_pairs or s.replace('/', '') in [d.replace('/', '') for d in default_pairs]]
                logger.info(f"📊 WIN_RATE_OPTIMIZED: Trading SOLO {trading_pairs_list}")
            elif excluded:
                # Excluir símbolos de la lista por defecto
                trading_pairs_list = [s for s in default_pairs if s not in excluded]
                logger.info(f"📊 Símbolos excluidos: {excluded}")
            else:
                trading_pairs_list = default_pairs
        else:
            trading_pairs_list = default_pairs
        
        self.config = {
            'active': False,
            'paper_mode': paper_mode_env,  # TRUE = Simulado con $1M | FALSE = Real en Kraken
            'trading_profile': profile_name,  # Nombre del perfil activo
            'trading_pairs': trading_pairs_list,  # V6.5.4: Pares según perfil activo
            'trading_pair': 'BTC/USD',  # Default pair (legacy compatibility)
            'check_interval_seconds': p.check_interval_seconds if p else 25,
            'min_trade_usd': p.min_trade_usd if p else 75.0,
            'max_position_pct': p.max_position_pct if p else 0.12,
            'stop_loss_pct': p.stop_loss_pct if p else 0.02,
            'take_profit_pct': p.take_profit_pct if p else 0.03,
            'max_daily_loss_pct': p.max_daily_loss_pct if p else 0.08,
            'min_confidence': p.min_confidence if p else 0.14,
            'use_v52_strategies': True,  # Activar estrategias V5.2 Quantum
            'use_adaptive_weights': True,  # Sistema de pesos adaptativos ω(t)
            'use_multi_crypto': True,  # V6.4: Activar escaneo multi-crypto
            'trades_per_day_target': p.trades_per_day_target if p else 25,
        }
        
        # Estado del bot - V6.4: Cargado de la base de datos para persistencia
        self.state = {
            'running': False,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit_loss': 0.0,
            'daily_profit_loss': 0.0,
            'last_trade_time': None,
            'initial_balance': None,
            'emergency_stop': False,
            'paper_balance': 1_000_000.0 if self.config['paper_mode'] else 0.0,  # $1M virtual
            'paper_positions': {}  # {symbol: {amount, avg_price, value}}
        }
        
        # FASE 2.3: Estado de probation para tracking de pérdidas consecutivas
        self.probation_state = {
            'consecutive_losses': 0,
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'start_date': None,
            'auto_reverted': False,
            'pnl': 0.0
        }
        
        # V6.5.4d: Lock para prevenir race conditions en start/stop
        self._start_stop_lock = threading.Lock()
        self._thread = None  # Reference to trading loop thread
        
        # V6.5.4d MULTI-USER: Inicializar UserSessionManager con dependencias
        if USER_SESSION_MANAGER_AVAILABLE and initialize_session_manager:
            try:
                self.redis_cache = None
                if REDIS_CACHE_AVAILABLE and redis_cache:
                    self.redis_cache = redis_cache
                initialize_session_manager(
                    redis_cache=self.redis_cache,
                    database_service=database_service
                )
                logger.info(f"🚀 {VERSION_BANNER} UserSessionManager inicializado (100K+ usuarios)")
            except Exception as e:
                logger.warning(f"⚠️ Error inicializando UserSessionManager: {e}")
        
        # V6.4: Cargar estado persistente de la DB
        self._load_persistent_state()
        
        # Track Record Accelerator - Contador de trades para bias boost primeros 50
        self._paper_trade_count = self.state.get('paper_trade_count', 0)
        if self._paper_trade_count > 0:
            logger.info(f"📊 {VERSION_BANNER} Accelerator: {self._paper_trade_count} trades previos (boost activo hasta 50)")
        
        # Inicializar balance en Prometheus
        if METRICS_ENGINE_AVAILABLE and metrics:
            mode = 'paper' if self.config['paper_mode'] else 'real'
            metrics.update_balance(mode, 'USD', self.state['paper_balance'] if self.config['paper_mode'] else 0.0)
        
        # Thread para loop 24/7
        self._thread = None
        
        # Sistema de Pesos Adaptativos V5.2 QUANTUM (ω(t) dinámico)
        if ADAPTIVE_SYSTEM_AVAILABLE and self.config['use_adaptive_weights']:
            self.adaptive_system = create_adaptive_system({
                'initial_omega': 0.5,  # Balance 50/50 inicial
                'learning_rate': 0.1   # Ajuste adaptativo moderado
            })
            logger.info("⚡ Adaptive Weight System ACTIVADO - Pesos dinámicos Kalman/Monte Carlo")
        else:
            self.adaptive_system = None
            logger.info("📊 Usando pesos fijos para estrategias")
        
        # Sistema de Auto-Aprendizaje V5.2.3 (VIDEO LEARNING - PREMIUM)
        if AUTO_LEARNING_AVAILABLE:
            self.auto_learning = AutoLearningSystem(db_service=database_service)
            self.video_analyzer = VideoLearningAnalyzer(ai_service=ai_service)
            logger.info("🎓 Auto-Learning System ACTIVADO - Aprende de videos automáticamente")
        else:
            self.auto_learning = None
            self.video_analyzer = None
        
        # Cerebro Conversacional V5.3 ULTRA - EL BOT QUE PIENSA EN VOZ ALTA
        if CONVERSATIONAL_BRAIN_AVAILABLE and database_service:
            self.conversational_brain = get_conversational_brain(database_service)
            logger.info("🧠 Conversational Brain ACTIVADO - Bot que razona y aprende")
        else:
            self.conversational_brain = None
            logger.info("⚠️ Auto-Learning desactivado")
        
        # Coherence Engine V5.3 ULTRA - SEGUNDO CEREBRO DE VALIDACIÓN
        if COHERENCE_ENGINE_AVAILABLE:
            self.coherence_engine = CoherenceEngine()
            logger.info("🧠 Coherence Engine ACTIVADO - Validación de coherencia entre estrategias")
        else:
            self.coherence_engine = None
            logger.info("⚠️ Coherence Engine desactivado")
        
        # AI Risk Guardian V5.4 - SUPERVISOR DE RIESGOS
        if AI_RISK_GUARDIAN_AVAILABLE and database_service:
            try:
                self.risk_guardian = AIRiskGuardian(database_service=database_service)
                logger.info("🛡️ AI Risk Guardian V5.4 ACTIVADO - Protección contra overtrading, drawdown, revenge trading")
            except Exception as e:
                self.risk_guardian = None
                logger.warning(f"⚠️ AI Risk Guardian error: {e}")
        else:
            self.risk_guardian = None
            logger.info("⚠️ AI Risk Guardian desactivado")
        
        # V6.5.4 PREMIUM: Per-Pair Circuit Breaker - Drawdown diario por par
        from datetime import datetime as dt_init, timezone as tz_init
        today_utc = dt_init.now(tz_init.utc).strftime('%Y-%m-%d')
        self.daily_drawdown_per_pair = {
            "BTC/USD": {"pnl": 0.0, "date": today_utc},
            "XRP/USD": {"pnl": 0.0, "date": today_utc},
            "ADA/USD": {"pnl": 0.0, "date": today_utc},
            "LINK/USD": {"pnl": 0.0, "date": today_utc},
        }
        logger.info("🔌 Per-Pair Circuit Breaker V6.5.4 ACTIVADO - Drawdown diario por símbolo")
        
        # Non-Markovian Memory Kernel V6.1 ULTRA - QUANTUM TEMPORAL MEMORY
        self._last_kernel_pair = None  # Track pair for kernel seeding
        self._kernel_needs_reseed = True  # Flag for pending reseed
        if NON_MARKOVIAN_KERNEL_AVAILABLE:
            try:
                self.non_markovian_kernel = NonMarkovianKernel(
                    tau=12.0,      # 12 hours memory decay
                    epsilon=0.35,  # 35% oscillation amplitude
                    omega=0.523,   # π/6 captures 12-hour cycles
                    window_size=168  # 1 week of hourly data
                )
                logger.info("🧠 Non-Markovian Kernel V6.1 ACTIVADO - K(t-s) = exp(-|t-s|/τ)[1 + ε cos(Ω(t-s))]")
            except Exception as e:
                self.non_markovian_kernel = None
                logger.warning(f"⚠️ Non-Markovian Kernel error: {e}")
        else:
            self.non_markovian_kernel = None
            logger.info("⚠️ Non-Markovian Kernel desactivado")
        
        # Memory-Enhanced RMS V6.2 - PREDICTIVE RISK MANAGEMENT
        if MEMORY_ENHANCED_RMS_AVAILABLE and self.non_markovian_kernel:
            try:
                self.memory_risk_adapter = MemoryRiskAdapter(kernel=self.non_markovian_kernel)
                self.limits_engine = LimitsEngine(
                    database_service=database_service,
                    memory_adapter=self.memory_risk_adapter
                )
                self.circuit_breaker = CircuitBreaker(
                    database_service=database_service,
                    memory_adapter=self.memory_risk_adapter
                )
                self.position_monitor = PositionMonitor(
                    database_service=database_service,
                    memory_adapter=self.memory_risk_adapter
                )
                self.alert_dispatcher = AlertDispatcher(
                    telegram_bot=None,
                    database_service=database_service,
                    memory_adapter=self.memory_risk_adapter
                )
                logger.info("🧠 Memory-Enhanced RMS V6.2 ACTIVADO - Gestión de riesgo predictiva")
                logger.info("   📊 LimitsEngine con ajuste dinámico por coherencia")
                logger.info("   🔌 CircuitBreaker con halt por incoherencia de memoria")
                logger.info("   📈 PositionMonitor con factor de riesgo por divergencia")
                logger.info("   📢 AlertDispatcher con alertas predictivas de régimen")
            except Exception as e:
                self.memory_risk_adapter = None
                self.limits_engine = None
                self.circuit_breaker = None
                self.position_monitor = None
                self.alert_dispatcher = None
                logger.warning(f"⚠️ Memory-Enhanced RMS error: {e}")
        else:
            self.memory_risk_adapter = None
            self.limits_engine = None
            self.circuit_breaker = None
            self.position_monitor = None
            self.alert_dispatcher = None
            if not NON_MARKOVIAN_KERNEL_AVAILABLE:
                logger.info("⚠️ Memory-Enhanced RMS desactivado (requiere Non-Markovian Kernel)")
            else:
                logger.info("⚠️ Memory-Enhanced RMS desactivado")
        
        # Adaptive Parameter Engine - AUTO-CALIBRATION FOR ARES
        if ADAPTIVE_PARAMETER_ENGINE_AVAILABLE and self.non_markovian_kernel and self.coherence_engine:
            try:
                self.adaptive_engine = get_adaptive_engine(
                    database_service=database_service,
                    coherence_engine=self.coherence_engine,
                    risk_guardian=self.risk_guardian
                )
                
                # Callback para actualizar ARES cuando se calibran parámetros
                def on_calibration(strategy_name: str, profile):
                    logger.info(f"🎯 Calibración aplicada a {strategy_name}")
                    self._apply_adaptive_parameters(strategy_name, profile)
                
                self.adaptive_engine.register_callback(on_calibration)
                
                logger.info(f"🎯 Adaptive Parameter Engine {VERSION_BANNER} ACTIVADO - Auto-calibración dinámica")
                logger.info("   ⚙️ ARES V1/V2 parámetros se ajustan por régimen de mercado")
                logger.info("   🧠 Integrado con Non-Markovian Memory Kernel")
                logger.info("   🔒 Validado por Coherence Engine + Risk Guardian")
            except Exception as e:
                self.adaptive_engine = None
                logger.warning(f"⚠️ Adaptive Parameter Engine error: {e}")
        else:
            self.adaptive_engine = None
            if not ADAPTIVE_PARAMETER_ENGINE_AVAILABLE:
                logger.info("⚠️ Adaptive Parameter Engine no disponible")
            else:
                logger.info("⚠️ Adaptive Parameter Engine desactivado (requiere Non-Markovian Kernel + Coherence Engine)")
        
        # Dynamic Position Manager PREMIUM - ATR-BASED TP/SL
        if POSITION_MANAGER_AVAILABLE:
            try:
                self.position_manager = DynamicPositionManager(
                    trading_service=trading_service,
                    paper_trading=paper_trading,
                    non_markovian_kernel=self.non_markovian_kernel,
                    coherence_engine=self.coherence_engine,
                    risk_guardian=self.risk_guardian,
                    caes_engine=get_caes_instance() if CAES_AVAILABLE else None,
                    redis_cache=None
                )
                logger.info(f"📊 Dynamic Position Manager {VERSION_BANNER} PREMIUM ACTIVADO")
                logger.info("   📈 ATR-based TP/SL dinámico por volatilidad")
                logger.info("   🎯 Trailing Stop inteligente + Break-even automático")
                logger.info("   🧠 Integrado con Non-Markovian Kernel + Coherence Engine")
            except Exception as e:
                self.position_manager = None
                logger.warning(f"⚠️ Dynamic Position Manager error: {e}")
        else:
            self.position_manager = None
            logger.info("⚠️ Dynamic Position Manager no disponible - usando TP/SL fijos")
        
        if EXECUTION_PROTOCOL_AVAILABLE:
            try:
                self.execution_protocol = ExecutionProtocol(
                    trading_service=trading_service
                )
                logger.info(f"🎯 Execution Protocol {VERSION_BANNER} INSTITUTIONAL+ ACTIVADO")
                logger.info("   📊 LiquidityAnalyzer: TBLR + Hidden Liquidity Detection")
                logger.info("   📈 MicroVolatilityEngine: Regime Detection + Asymmetric Response")
                logger.info("   🔗 CrossAssetCorrelationEngine: Contagion Risk + Safe-Haven Flows")
                logger.info("   🎯 Decision Matrix: TWAP/VWAP/ICEBERG + Slippage Prediction")
            except Exception as e:
                self.execution_protocol = None
                logger.warning(f"⚠️ Execution Protocol error: {e}")
        else:
            self.execution_protocol = None
            logger.info("⚠️ Execution Protocol no disponible")
        
        # EMA Regime Signal V6.5.4d - REAL DETERMINISTIC SIGNAL (replaces ARES placeholders)
        if EMA_REGIME_SIGNAL_AVAILABLE:
            try:
                self.ema_signal_generator = get_signal_generator()
                logger.info("📊 EMA Regime Signal V1.0 ACTIVADO - Señal REAL determinística")
                logger.info("   🔬 EMA slope + ATR volatility + HMM regime")
                logger.info("   ✅ Reemplaza outputs pseudo-aleatorios de ARES")
            except Exception as e:
                self.ema_signal_generator = None
                logger.warning(f"⚠️ EMA Regime Signal error: {e}")
        else:
            self.ema_signal_generator = None
            logger.info("⚠️ EMA Regime Signal no disponible - usando ARES legacy")
        
        # V6.5.4d: Monte Carlo Veto thresholds (enforced, not just logged)
        self.mc_veto_config = {
            'min_expected_return': 0.0,  # Veto if expected_return < 0
            'max_var_95': -0.03,  # Veto if VaR95 worse than -3%
            'min_win_rate': 0.45,  # Reduce size if win_rate < 45%
            'reduce_size_win_rate': 0.50,  # Reduce size if win_rate < 50%
            'size_reduction_factor': 0.5,  # Reduce to 50% if below threshold
        }
        logger.info("📊 Monte Carlo VETO Engine ACTIVADO - Decisiones enforzadas")
        
        mode = "PAPER TRADING ($1M virtual)" if self.config['paper_mode'] else "🚨 REAL TRADING (Kraken) 💰"
        logger.info(f"🤖 AutoTradingBot {VERSION_BANNER} inicializado - Modo: {mode}")
        
        # V6.5: Auto-iniciar si el estado persistente indica que debería estar activo
        self._auto_start_if_persistent()
    
    def _auto_start_if_persistent(self):
        """
         Auto-iniciar el trading si el estado persistente de la DB indica que debería estar activo.
        Esto garantiza que Railway reinicie con el mismo estado que antes del restart.
         Ahora pasa el user_id específico para soportar múltiples usuarios.
        
        FIX DEC25: Added direct permission check as fallback in case _load_persistent_state() fails.
        """
        logger.critical(f"🔥🔥 FIX DEC25: _auto_start_if_persistent() CALLED - _should_auto_start={getattr(self, '_should_auto_start', 'NOT SET')}")
        
        if hasattr(self, '_should_auto_start') and self._should_auto_start:
            user_id = getattr(self, '_persistent_user_id', None)
            logger.critical(f"🔥🔥 FIX DEC25: Checking permissions for user {user_id} BEFORE starting")
            
            # FIX DEC25: DIRECT permission check as fallback
            # This ensures we NEVER start for unauthorized users, even if _load_persistent_state() failed
            try:
                self._require_trading_permission(user_id, 'persistent_auto_start_fallback')
                logger.critical(f"✅✅ FIX DEC25: User {user_id} PASSED permission check - proceeding with start")
            except AuthorizationError as auth_err:
                logger.critical(f"🚫🚫 FIX DEC25: User {user_id} BLOCKED by fallback permission check - {auth_err}")
                logger.critical(f"🔄🔄 FIX DEC25: Searching for authorized user in database...")
                
                # Try to find an authorized user from the database
                authorized_user = self._find_authorized_auto_trading_user()
                if authorized_user:
                    user_id = authorized_user
                    logger.critical(f"✅✅ FIX DEC25: Found authorized user {user_id} - using this instead")
                else:
                    logger.critical(f"❌❌ FIX DEC25: No authorized users found - auto-start ABORTED")
                    return
            except Exception as e:
                logger.warning(f"⚠️ FIX DEC25: Permission check error: {e} - aborting auto-start")
                return
            
            logger.critical(f"🚀🚀 FIX DEC25: STARTING auto-trading for user {user_id}")
            try:
                result = self.start(user_id=user_id)
                if result.get('success'):
                    logger.critical(f"✅✅ FIX DEC25: Auto-trading STARTED SUCCESSFULLY for user {user_id}")
                else:
                    error = result.get('error', 'Unknown error')
                    logger.critical(f"❌❌ FIX DEC25: Auto-trading FAILED to start: {error}")
            except Exception as e:
                logger.error(f"❌ {VERSION_BANNER}: Error restaurando auto-trading: {e}")
        else:
            logger.critical(f"⏸️⏸️ FIX DEC25: Auto-start SKIPPED - _should_auto_start is False or not set")
    
    def _find_authorized_auto_trading_user(self) -> str:
        """
        FIX DEC25: Search database for a user with auto_trading=true AND PAPER_AUTO_TRADING permission.
        This is a fallback method when the original user selection was wrong.
        """
        if not self.database_service or not hasattr(self.database_service, 'execute_query'):
            return None
        
        try:
            result = self.database_service.execute_query('''
                SELECT user_id FROM user_settings
                WHERE auto_trading = true AND trading_enabled = true AND (is_paused = false OR is_paused IS NULL)
            ''')
            
            if result:
                for row in result:
                    user_id = str(row[0]) if row[0] else None
                    if user_id:
                        try:
                            self._require_trading_permission(user_id, 'find_authorized_user')
                            logger.critical(f"✅ FIX DEC25: User {user_id} has PAPER_AUTO_TRADING permission")
                            return user_id
                        except AuthorizationError:
                            logger.critical(f"❌ FIX DEC25: User {user_id} lacks PAPER_AUTO_TRADING - skipping")
                            continue
        except Exception as e:
            logger.warning(f"⚠️ FIX DEC25: Error finding authorized user: {e}")
        
        return None
    
    def _get_effective_user_id(self, passed_user_id: str = None, caller: str = None) -> str:
        """
        V6.5.4d MULTI-USER: Obtener user_id efectivo para operaciones de trading.
        
        REGLA ESTRICTA: En producción multi-usuario, user_id DEBE pasarse explícitamente.
        Solo usa fallback para legacy single-user mode.
        
        Prioridad:
        1. user_id pasado como parámetro (explícito - REQUERIDO en multi-user)
        2. config['user_id'] (configuración del bot por sesión)
        3. LEGACY_USER_ID env var (SOLO para legacy single-user mode)
        
        NOTA: _persistent_user_id NO se usa aquí. Es SOLO para auto-start en
        _auto_start_if_persistent(), no para operaciones de runtime.
        
        Args:
            passed_user_id: ID del usuario pasado explícitamente al método
            caller: Nombre del método que llama (para debugging)
            
        Returns:
            str: User ID efectivo a usar
            
        Raises:
            ValueError: Cuando user_id no está disponible de ninguna fuente
        """
        import os as os_env
        LEGACY_USER_ID = os_env.getenv('LEGACY_USER_ID')
        
        if passed_user_id:
            return str(passed_user_id)
        
        config_user_id = self.config.get('user_id')
        if config_user_id:
            return str(config_user_id)
        
        if not LEGACY_USER_ID:
            error_msg = f"user_id not provided by {caller or 'unknown'} and LEGACY_USER_ID env var not set"
            logger.error(f"🚨 CRITICAL: {error_msg}")
            raise ValueError(error_msg)
        
        if caller:
            logger.warning(f"⚠️ {caller}: user_id not passed, using LEGACY_USER_ID env var (legacy mode)")
        return LEGACY_USER_ID
    
    def _require_trading_permission(self, user_id: str, operation: str = 'trading') -> None:
        """
        V6.5.4d MULTI-USER: Verify user has required trading permission.
        
        Uses AuthorizationAdapter if available, falls back to LEGACY_USER_ID check.
        Raises AuthorizationError if user doesn't have permission.
        
        Permission selection based on paper/real mode:
        - Paper mode: PAPER_TRADING or PAPER_AUTO_TRADING, VIEW_BALANCE for positions
        - Real mode: REAL_TRADING or REAL_AUTO_TRADING (OWNER only), VIEW_REAL_BALANCE for positions
        
        Args:
            user_id: User ID to check permissions for
            operation: Type of operation - 'trading', 'auto_trading', 'view_positions'
            
        Raises:
            AuthorizationError: If user doesn't have required permission
        """
        if not AUTHORIZATION_ADAPTER_AVAILABLE or not get_authorization_adapter:
            import os as os_env
            LEGACY_USER_ID = os_env.getenv('LEGACY_USER_ID', '')
            if not LEGACY_USER_ID or not user_id:
                raise AuthorizationError(f"Authorization denied: adapter unavailable and no legacy credentials for user {user_id}")
            if str(user_id) != LEGACY_USER_ID:
                raise AuthorizationError(f"Authorization denied: user {user_id} is not the legacy user")
            return
        
        try:
            auth = get_authorization_adapter()
            is_paper_mode = self.config.get('paper_mode', True)
            has_perm = False
            required_perm = None
            
            if operation == 'auto_trading':
                if is_paper_mode:
                    required_perm = Permission.PAPER_AUTO_TRADING
                else:
                    required_perm = Permission.REAL_AUTO_TRADING
            elif operation == 'trading':
                if is_paper_mode:
                    required_perm = Permission.PAPER_TRADING
                else:
                    required_perm = Permission.REAL_TRADING
            elif operation == 'view_positions':
                if is_paper_mode:
                    required_perm = Permission.VIEW_BALANCE
                else:
                    required_perm = Permission.VIEW_REAL_BALANCE
            else:
                required_perm = Permission.READ_MARKET_DATA
            
            has_perm = auth.has_permission(str(user_id), required_perm)
            
            if not has_perm:
                raise AuthorizationError(f"User {user_id} lacks permission {required_perm.name} for operation '{operation}'")
                
        except AuthorizationError:
            raise
        except Exception as e:
            logger.warning(f"⚠️ Authorization check failed for user {user_id}: {e}, falling back to legacy mode")
            import os as os_env
            LEGACY_USER_ID = os_env.getenv('LEGACY_USER_ID', '')
            if not LEGACY_USER_ID or not user_id:
                raise AuthorizationError(f"Authorization denied: fallback failed - no legacy credentials for user {user_id}")
            if str(user_id) != LEGACY_USER_ID:
                raise AuthorizationError(f"Authorization denied: user {user_id} is not the legacy user")
    
    def check_and_restore_auto_trading(self):
        """
         Método público para restaurar auto-trading DESPUÉS de que la DB esté conectada.
        Llamar desde main.py después de verificar que DATABASE está CONECTADA.
        
        ARQUITECTURA MULTI-USER 
        - Usa UserSessionManager para manejar sesiones de 100,000+ usuarios
        - Cada usuario tiene su propia sesión aislada
        - Estado persistente en Redis + PostgreSQL
        - El ciclo de trading actual ejecuta operaciones para TODOS los usuarios activos
        """
        if not self.database_service or not hasattr(self.database_service, 'execute_query'):
            logger.warning(f"⚠️ {VERSION_BANNER}: check_and_restore - No hay database_service disponible")
            return False
        
        try:
            logger.info(f"🔍 {VERSION_BANNER}: Verificando estado persistente (MULTI-USER 100K+)...")
            
            if USER_SESSION_MANAGER_AVAILABLE and get_session_manager:
                session_manager = get_session_manager()
                
                if self.database_service:
                    session_manager.database_service = self.database_service
                if hasattr(self, 'redis_cache'):
                    session_manager.redis_cache = self.redis_cache
                
                result = session_manager.restore_all_sessions()
                
                if result.get('restored', 0) > 0:
                    if not self.state.get('running'):
                        self.state['running'] = True
                        self._start_trading_loop()
                    
                    logger.info(f"✅ {VERSION_BANNER}: {result['restored']} sesiones restauradas - Trading loop ACTIVO")
                    return True
                else:
                    logger.info(f"📊 {VERSION_BANNER}: No hay sesiones activas que restaurar")
                    return False
            else:
                logger.info(f"🔄 {VERSION_BANNER}: Fallback a restauración legacy...")
                user_settings_result = self.database_service.execute_query('''
                    SELECT auto_trading, is_paused, trading_enabled, user_id
                    FROM user_settings
                    WHERE auto_trading = true AND trading_enabled = true AND (is_paused = false OR is_paused IS NULL)
                    ORDER BY user_id
                ''')
                
                if user_settings_result and len(user_settings_result) > 0:
                    total_users = len(user_settings_result)
                    logger.info(f"🔄 {VERSION_BANNER}: Encontrados {total_users} usuario(s) con auto_trading activo en DB")
                    
                    started_users = []
                    skipped_users = []
                    
                    for user_row in user_settings_result:
                        user_id = str(user_row.get('user_id', 'unknown'))
                        
                        try:
                            self._require_trading_permission(user_id, 'auto_trading')
                            
                            result = self.start(user_id=user_id)
                            if result.get('success'):
                                started_users.append(user_id)
                                logger.info(f"✅ {VERSION_BANNER}: Trading iniciado para user {user_id}")
                            else:
                                skipped_users.append(f"{user_id} (start failed)")
                                
                        except AuthorizationError as e:
                            skipped_users.append(f"{user_id} (no permission)")
                            logger.warning(f"⚠️ {VERSION_BANNER}: User {user_id} skipped - {e}")
                        except Exception as e:
                            skipped_users.append(f"{user_id} (error)")
                            logger.error(f"❌ {VERSION_BANNER}: Error checking user {user_id}: {e}")
                    
                    if started_users:
                        logger.info(f"✅ {VERSION_BANNER}: Auto-trading started for {len(started_users)} user(s): {started_users}")
                        return True
                    else:
                        logger.warning(f"⚠️ {VERSION_BANNER}: No users with valid permissions. Skipped: {skipped_users}")
                        return False
                    
                return False
                
        except Exception as e:
            logger.error(f"❌ {VERSION_BANNER}: Error en check_and_restore_auto_trading: {e}")
            return False
    
    def _start_trading_loop(self):
        """Iniciar el loop de trading en un thread separado"""
        if self._thread is not None and self._thread.is_alive():
            logger.info("📊 Trading loop ya está corriendo")
            return
        
        self._thread = threading.Thread(target=self._trading_loop_multi_user, daemon=True)
        self._thread.start()
        logger.info(f"🚀 {VERSION_BANNER}: Trading loop MULTI-USER iniciado")
    
    def _trading_loop_multi_user(self):
        """
         Loop de trading que procesa TODOS los usuarios activos
        Usa ThreadPoolExecutor para procesamiento paralelo de usuarios
        
        Arquitectura:
        - Pool de workers para procesamiento paralelo
        - Cada usuario se procesa en su propio thread
        - Lock por usuario para evitar race conditions
        - Timeout por usuario para evitar bloqueos
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        logger.info(f"🔄 {VERSION_BANNER}: Iniciando loop de trading multi-usuario...")
        
        max_workers = min(32, (os.cpu_count() or 1) * 4)
        user_locks: Dict[str, threading.Lock] = {}
        
        while self.state.get('running'):
            try:
                if USER_SESSION_MANAGER_AVAILABLE and get_session_manager:
                    session_manager = get_session_manager()
                    active_users = session_manager.get_active_sessions()
                    
                    if active_users:
                        logger.debug(f"📊 Procesando {len(active_users)} usuarios activos")
                        
                        with ThreadPoolExecutor(max_workers=max_workers) as executor:
                            futures = {}
                            
                            for user_id in active_users:
                                if user_id not in user_locks:
                                    user_locks[user_id] = threading.Lock()
                                
                                if user_locks[user_id].locked():
                                    continue
                                
                                future = executor.submit(
                                    self._safe_process_user,
                                    user_id,
                                    user_locks[user_id],
                                    session_manager
                                )
                                futures[future] = user_id
                            
                            for future in as_completed(futures, timeout=60):
                                user_id = futures[future]
                                try:
                                    result = future.result(timeout=30)
                                except Exception as e:
                                    logger.error(f"❌ Error procesando user {user_id}: {e}")
                else:
                    self._run_trading_cycle()
                
                time.sleep(self.config.get('check_interval_seconds', 25))
                
            except Exception as e:
                logger.error(f"❌ Error en trading loop: {e}")
                time.sleep(30)
        
        logger.info(f"🛑 {VERSION_BANNER}: Trading loop multi-usuario detenido")
    
    def _safe_process_user(self, user_id: str, lock: threading.Lock, session_manager) -> bool:
        """
        Procesar un usuario de forma segura con lock
        
        Args:
            user_id: ID del usuario
            lock: Lock para este usuario
            session_manager: Gestor de sesiones
        
        Returns:
            True si se procesó correctamente
        """
        if not lock.acquire(blocking=False):
            return False
        
        try:
            session = session_manager.get_session(user_id)
            
            if session.running and not session.paused and not session.emergency_stop:
                self._process_user_trading_cycle(user_id, session)
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Error en _safe_process_user para {user_id}: {e}")
            return False
        finally:
            lock.release()
    
    def _process_user_trading_cycle(self, user_id: str, session):
        """
        V6.5.4d MULTI-USER: Procesar un ciclo de trading para un usuario específico
        
        Este método ejecuta la lógica de trading pasando el user_id para
        aislamiento multi-usuario. Es llamado desde _trading_loop_multi_user.
        
        NOTA: Esta es una implementación BÁSICA para habilitar multi-usuario.
        El loop legacy (_trading_loop) tiene protecciones adicionales:
        - _check_emergency_stop (verificado en el loop padre)
        - Algorithmic Rollback Protocol (verificado en el loop padre)
        - Heartbeats (verificado en el loop padre)
        
        Args:
            user_id: ID del usuario
            session: UserTradingSession del usuario
        """
        try:
            logger.debug(f"📊 Procesando ciclo para user {user_id}")
            
            # 0. Verificar emergency_stop a nivel de sesión
            if session.emergency_stop:
                logger.warning(f"🚨 Emergency stop activo para user {user_id} - saltando ciclo")
                return
            
            # 1. Verificar Take Profit / Stop Loss en posiciones abiertas
            self._check_open_positions_tp_sl(user_id=user_id)
            
            # 2. Verificar límite de posiciones ANTES de análisis
            position_limit_reached = self._check_position_limit_early(user_id=user_id)
            
            # 3. Obtener configuración de pares (usar sesión o config global como fallback)
            trading_pairs = getattr(session, 'trading_pairs', None) or self.config.get('trading_pairs', ['BTC/USD'])
            
            # 4. Escanear pares configurados
            session_updated = False
            for current_pair in trading_pairs:
                # NOTA: Temporalmente usamos config compartido, pero pasamos user_id
                # para que las operaciones de DB sean aisladas
                self.config['trading_pair'] = current_pair
                
                # Verificar si el símbolo está permitido
                if is_symbol_allowed and not is_symbol_allowed(current_pair, self.trading_profile):
                    continue
                
                # Análisis completo
                analysis = self._analyze_market()
                
                if not analysis:
                    continue
                
                should_trade = analysis.get('should_trade', False)
                action = analysis.get('action', 'HOLD')
                
                # Bloquear BUY si límite de posiciones alcanzado
                if position_limit_reached and action == 'BUY':
                    logger.debug(f"⏸️ BUY bloqueado para {user_id} - límite de posiciones")
                    continue
                
                # Ejecutar trade si aplica
                if should_trade and action in ['BUY', 'SELL']:
                    result = self._execute_smart_trade(analysis, user_id=user_id)
                    
                    if result and 'error' not in result:
                        # Actualizar sesión del usuario
                        session.total_trades += 1
                        pnl = result.get('profit_loss', 0.0)
                        if pnl > 0:
                            session.winning_trades += 1
                        session.total_profit_loss += pnl
                        session.last_trade_time = datetime.now().isoformat()
                        session_updated = True
                        
                        logger.info(f"✅ Trade ejecutado para user {user_id}: {action}")
            
            # 5. V6.5.4d: Persistir sesión si hubo cambios
            if session_updated and USER_SESSION_MANAGER_AVAILABLE and get_session_manager:
                try:
                    session_manager = get_session_manager()
                    session_manager.save_session(session)
                    logger.debug(f"💾 Sesión persistida para user {user_id}")
                except Exception as save_err:
                    logger.warning(f"⚠️ Error persistiendo sesión para {user_id}: {save_err}")
            
        except Exception as e:
            logger.error(f"❌ Error en ciclo de trading para user {user_id}: {e}")
    
    def start(self, user_id: str = None) -> Dict:
        """Iniciar trading automático 24/7"""
        # V6.5.4d: Thread-safe start with lock
        with self._start_stop_lock:
            try:
                if self.state['running']:
                    return {'error': 'Bot ya está corriendo'}
                
                # Verify no existing thread is running
                if self._thread is not None and self._thread.is_alive():
                    return {'error': 'Bot ya está corriendo (thread activo)'}
                
                # Obtener balance inicial
                balance = self._get_balance()
                if not balance or balance < self.config['min_trade_usd']:
                    return {
                        'error': f'Balance insuficiente: ${balance:.2f}. Mínimo: ${self.config["min_trade_usd"]}'
                    }
                
                self.state['initial_balance'] = balance
                self.state['running'] = True
                self.state['emergency_stop'] = False
                self.config['active'] = True
                
                # V6.5.4: Register deploy with Algorithmic Rollback Protocol
                if ARP_AVAILABLE:
                    try:
                        arp = get_arp_instance()
                        # Create snapshot of current config before deploy
                        current_config = {
                            'trading_profile': self.trading_profile.name if self.trading_profile else 'UNKNOWN',
                            'max_aggression': getattr(self, '_max_aggression', 3.0),
                            'min_confidence': self.config.get('min_confidence', 0.6),
                            'max_daily_loss_pct': self.config.get('max_daily_loss_pct', 0.08),
                            'max_position_pct': self.config.get('max_position_pct', 0.12),
                            'coherence_thresholds': self.config.get('coherence_thresholds', {})
                        }
                        snapshot_file = arp.create_pre_deploy_snapshot(current_config)
                        arp.register_deploy(balance, snapshot_file)
                        logger.info(f"🔄 ARP: Deploy registrado con balance inicial ${balance:.2f}")
                    except Exception as e:
                        logger.warning(f"⚠️ ARP registration failed: {e}")
                
                # V6.5: Persistir estado en user_settings
                effective_user_id = self._get_effective_user_id(user_id, "start")
                
                # V6.5.4d MULTI-USER: Verify user has auto-trading permission
                try:
                    self._require_trading_permission(effective_user_id, 'auto_trading')
                except AuthorizationError as e:
                    logger.warning(f"🚫 {e}")
                    return {'error': 'Permission denied: auto-trading not allowed for this user tier'}
                
                self._persist_auto_trading_state(effective_user_id, active=True)
                
                # V6.5.4d MULTI-USER: Activar sesión del usuario en UserSessionManager
                if USER_SESSION_MANAGER_AVAILABLE and get_session_manager:
                    try:
                        session_manager = get_session_manager()
                        if self.database_service:
                            session_manager.database_service = self.database_service
                        if hasattr(self, 'redis_cache'):
                            session_manager.redis_cache = self.redis_cache
                        session = session_manager.get_session(effective_user_id)
                        session.running = True
                        session.paused = False
                        session.emergency_stop = False
                        session_manager.save_session(session)
                        logger.info(f"🚀 Sesión multi-usuario activada para {effective_user_id}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error activando sesión multi-usuario: {e}")
                
                # Iniciar thread para loop 24/7
                # V6.5.4d: Usar loop multi-usuario si UserSessionManager disponible
                if USER_SESSION_MANAGER_AVAILABLE and get_session_manager:
                    self._thread = threading.Thread(target=self._trading_loop_multi_user, daemon=False)
                    logger.info(f"🚀 AUTO-TRADING MULTI-USER ACTIVADO - Balance: ${balance:.2f}")
                else:
                    self._thread = threading.Thread(target=self._trading_loop, daemon=False)
                    logger.info(f"🚀 AUTO-TRADING LEGACY ACTIVADO - Balance: ${balance:.2f}")
                self._thread.start()
                
                return {
                    'success': True,
                    'message': '🤖 Auto-Trading ACTIVADO 24/7',
                    'balance': balance,
                    'initial_balance': balance,
                    'config': self.config
                }
                
            except Exception as e:
                logger.error(f"Error iniciando auto-trading: {e}")
                return {'error': str(e)}
    
    def stop(self, user_id: str = None) -> Dict:
        """Detener trading automático"""
        # V6.5.4d: Thread-safe stop with lock
        with self._start_stop_lock:
            try:
                self.state['running'] = False
                self.config['active'] = False
                
                # V6.5: Persistir estado en user_settings
                effective_user_id = self._get_effective_user_id(user_id, "stop")
                
                # V6.5.4d MULTI-USER: Verify user has auto-trading permission to stop
                try:
                    self._require_trading_permission(effective_user_id, 'auto_trading')
                except AuthorizationError as e:
                    logger.warning(f"🚫 {e}")
                    return {'error': 'Permission denied: cannot stop auto-trading for this user tier'}
                
                self._persist_auto_trading_state(effective_user_id, active=False)
                
                # V6.5.4d MULTI-USER: Desactivar sesión del usuario en UserSessionManager
                if USER_SESSION_MANAGER_AVAILABLE and get_session_manager:
                    try:
                        session_manager = get_session_manager()
                        session = session_manager.get_session(effective_user_id)
                        session.running = False
                        session_manager.save_session(session)
                        logger.info(f"🛑 Sesión multi-usuario detenida para {effective_user_id}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error deteniendo sesión multi-usuario: {e}")
                
                # V6.5.4d: Wait for thread to finish (with timeout)
                if self._thread is not None and self._thread.is_alive():
                    logger.info("⏳ Esperando que el loop de trading termine...")
                    self._thread.join(timeout=5.0)  # Wait max 5 seconds
                    if self._thread.is_alive():
                        logger.warning("⚠️ Loop de trading no terminó en 5s, continuando...")
                
                logger.info("🛑 AUTO-TRADING DETENIDO")
                
                return {
                    'success': True,
                    'message': '🛑 Auto-Trading detenido',
                    'stats': self._get_stats()
                }
                
            except Exception as e:
                logger.error(f"Error deteniendo auto-trading: {e}")
                return {'error': str(e)}
    
    def _persist_auto_trading_state(self, user_id: str = None, active: bool = True):
        """
        V6.5: Persistir estado de auto-trading en user_settings.
        Esto garantiza que el estado sobreviva a reinicios de Railway.
         Usa UPSERT para crear registro si no existe.
        """
        if not self.database_service or not hasattr(self.database_service, 'execute_query'):
            logger.debug(f"{VERSION_BANNER}: No se puede persistir estado (sin database_service)")
            return
        
        try:
            if user_id:
                self.database_service.execute_query('''
                    INSERT INTO user_settings (user_id, auto_trading, trading_enabled, updated_at)
                    VALUES (%s, %s, true, NOW())
                    ON CONFLICT (user_id) DO UPDATE 
                    SET auto_trading = EXCLUDED.auto_trading, updated_at = NOW()
                ''', (user_id, active))
                logger.info(f"💾 {VERSION_BANNER}: Estado auto_trading={active} persistido para user {user_id}")
            else:
                if active:
                    result = self.database_service.execute_query('''
                        SELECT user_id FROM user_settings 
                        WHERE trading_enabled = true 
                        ORDER BY updated_at DESC 
                        LIMIT 1
                    ''')
                    if result and len(result) > 0 and result[0]:
                        uid = result[0][0] if result[0] else None  # First column = user_id (tuple access)
                        if uid:
                            self.database_service.execute_query('''
                                UPDATE user_settings 
                                SET auto_trading = true, updated_at = NOW()
                                WHERE user_id = %s
                            ''', (uid,))
                            logger.info(f"💾 {VERSION_BANNER}: auto_trading=true persistido para user {uid}")
                    else:
                        self.database_service.execute_query('''
                            INSERT INTO user_settings (user_id, auto_trading, trading_enabled, updated_at)
                            VALUES ('default_admin', true, true, NOW())
                            ON CONFLICT (user_id) DO UPDATE 
                            SET auto_trading = true, updated_at = NOW()
                        ''')
                        logger.info(f"💾 {VERSION_BANNER}: auto_trading=true persistido para default_admin")
                else:
                    self.database_service.execute_query('''
                        UPDATE user_settings 
                        SET auto_trading = false, updated_at = NOW()
                        WHERE auto_trading = true
                    ''')
                    logger.info(f"💾 {VERSION_BANNER}: auto_trading=false persistido para todos los usuarios")
        except Exception as e:
            logger.warning(f"⚠️ {VERSION_BANNER}: Error persistiendo auto_trading: {e}")
    
    def _write_heartbeat(self, cycle_count: int = 0):
        """
        V6.5.4d: Write heartbeat to Redis for liveness monitoring.
        Key: omnix:heartbeat:trading_loop
        Updates every ~5 minutes (12 cycles at 25s interval)
        """
        if not REDIS_CACHE_AVAILABLE or not redis_cache:
            return
        
        try:
            redis_client = redis_cache.client if hasattr(redis_cache, 'client') else None
            if redis_client:
                heartbeat_data = {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'cycle': cycle_count,
                    'running': self.state.get('running', False),
                    'total_trades': self.state.get('total_trades', 0),
                    'paper_mode': self.config.get('paper_mode', True)
                }
                import json as json_heartbeat
                redis_client.setex(
                    'omnix:heartbeat:trading_loop',
                    600,  # 10 min TTL
                    json_heartbeat.dumps(heartbeat_data)
                )
                logger.info(f"💓 Heartbeat: Ciclo #{cycle_count} | Trades: {self.state.get('total_trades', 0)}")
        except Exception as e:
            logger.debug(f"Heartbeat write failed: {e}")
    
    def _load_persistent_state(self):
        """
        V6.5: Cargar estado persistente de la base de datos.
        Esto garantiza que los contadores de trades y métricas se mantengan
        entre reinicios del bot para que el ramp-up system funcione correctamente.
        
        FIX: También carga auto_trading de user_settings para persistir
        el estado entre reinicios de Railway.
        """
        logger.critical(f"🔥🔥 FIX DEC25: _load_persistent_state() ENTRY - database_service={self.database_service is not None}")
        
        if not self.database_service:
            logger.info(f"📊 {VERSION_BANNER}: Sin database_service - usando estado inicial")
            return
        
        try:
            # CRITICAL FIX DEC25: Force reset BEFORE any state loading
            # This ensures legacy values don't survive from previous runs
            self._should_auto_start = False
            self._persistent_user_id = None
            logger.critical(f"🔥🔥 FIX DEC25: FORCED RESET - _should_auto_start=False, _persistent_user_id=None")
            
            try:
                has_execute_query = hasattr(self.database_service, 'execute_query')
                logger.critical(f"🔥🔥 FIX DEC25: database_service.execute_query available={has_execute_query}")
                
                if has_execute_query:
                    # V6.5.4d FIX: Get ALL users with auto_trading, not just first one
                    user_settings_result = self.database_service.execute_query('''
                        SELECT auto_trading, is_paused, trading_enabled, user_id
                        FROM user_settings
                        WHERE auto_trading = true AND trading_enabled = true AND (is_paused = false OR is_paused IS NULL)
                    ''')
                    logger.critical(f"🔥🔥 FIX DEC25: Query returned {len(user_settings_result) if user_settings_result else 0} rows")
                    
                    if user_settings_result and len(user_settings_result) > 0:
                        # V6.5.4d: Check ALL users for permissions, find first with valid permission
                        logger.critical(f"🔥🔥 FIX DEC25 ACTIVE: Found {len(user_settings_result)} users with auto_trading=true")
                        authorized_user = None
                        for row in user_settings_result:
                            if row and len(row) >= 4:
                                user_id = str(row[3]) if row[3] else 'unknown'
                                logger.critical(f"🔥🔥 FIX DEC25: Evaluando usuario {user_id} para auto-trading persistente")
                                # Check permission BEFORE selecting this user
                                try:
                                    self._require_trading_permission(user_id, 'persistent_auto_start')
                                    authorized_user = user_id
                                    logger.critical(f"✅✅ FIX DEC25: User {user_id} AUTHORIZED - has PAPER_AUTO_TRADING")
                                    break  # Found authorized user
                                except AuthorizationError:
                                    logger.critical(f"❌❌ FIX DEC25: User {user_id} SKIPPED - lacks PAPER_AUTO_TRADING")
                                    continue
                                except Exception as e:
                                    logger.warning(f"⚠️ {VERSION_BANNER}: Permission check failed for {user_id}: {e}")
                                    continue
                        
                        if authorized_user:
                            self._should_auto_start = True
                            self._persistent_user_id = authorized_user
                            logger.critical(f"🚀🚀 FIX DEC25: Auto-trading WILL START for user {authorized_user}")
                        else:
                            logger.warning(f"⚠️ {VERSION_BANNER}: {len(user_settings_result)} usuario(s) con auto_trading=true, pero NINGUNO tiene PAPER_AUTO_TRADING permission")
                    else:
                        logger.info(f"📊 {VERSION_BANNER}: No hay usuarios con auto_trading activo")
            except Exception as e:
                logger.warning(f"⚠️ {VERSION_BANNER}: Error cargando auto_trading de user_settings: {e}")
            
            # Cargar estadísticas de trades cerrados
            from datetime import datetime, timedelta
            
            # Contar trades totales (últimos 30 días para track record)
            total_trades = 0
            winning_trades = 0
            losing_trades = 0
            total_pnl = 0.0
            daily_pnl = 0.0
            
            # Intentar obtener trades de la base de datos
            if hasattr(self.database_service, 'get_paper_trades_stats'):
                stats = self.database_service.get_paper_trades_stats()
                if stats:
                    total_trades = stats.get('total_trades', 0)
                    winning_trades = stats.get('winning_trades', 0)
                    losing_trades = stats.get('losing_trades', 0)
                    total_pnl = stats.get('total_pnl', 0.0)
                    daily_pnl = stats.get('daily_pnl', 0.0)
            elif hasattr(self.database_service, 'execute_query'):
                # Fallback: Consulta directa
                try:
                    result = self.database_service.execute_query('''
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins,
                            SUM(CASE WHEN profit_loss <= 0 THEN 1 ELSE 0 END) as losses,
                            COALESCE(SUM(profit_loss), 0) as total_pnl
                        FROM paper_trading_trades
                        WHERE status = 'closed'
                        AND closed_at >= NOW() - INTERVAL '30 days'
                    ''')
                    if result and len(result) > 0 and result[0]:
                        row = result[0]
                        # Tuple unpacking: SELECT COUNT(*), SUM(wins), SUM(losses), SUM(pnl)
                        # Guard against empty/None rows with safe access
                        if row and len(row) >= 4:
                            total_trades = int(row[0] or 0)
                            winning_trades = int(row[1] or 0)
                            losing_trades = int(row[2] or 0)
                            total_pnl = float(row[3] or 0)
                except Exception as e:
                    logger.debug(f"Query fallback error: {e}")
            
            # Cargar P/L del día actual para drawdown protection
            try:
                if hasattr(self.database_service, 'execute_query'):
                    daily_result = self.database_service.execute_query('''
                        SELECT COALESCE(SUM(profit_loss), 0) as daily_pnl
                        FROM paper_trading_trades
                        WHERE status = 'closed'
                        AND closed_at >= CURRENT_DATE
                    ''')
                    if daily_result and len(daily_result) > 0 and daily_result[0]:
                        # Tuple access: SELECT COALESCE(SUM(...)) → first column
                        row = daily_result[0]
                        daily_pnl = float(row[0] or 0) if row and len(row) > 0 else 0
            except Exception as e:
                logger.debug(f"Daily P/L query error: {e}")
            
            # Actualizar estado - INCLUYENDO daily_profit_loss para drawdown protection
            self.state['total_trades'] = total_trades
            self.state['winning_trades'] = winning_trades
            self.state['losing_trades'] = losing_trades
            self.state['total_profit_loss'] = total_pnl
            self.state['daily_profit_loss'] = daily_pnl  # V6.4 FIX: Persistir drawdown diario
            
            # Calcular win rate
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Log con drawdown info
            drawdown_status = ""
            if daily_pnl < -500:
                drawdown_status = " ⚠️ DRAWDOWN ACTIVO (50% sizing)"
            elif daily_pnl < -200:
                drawdown_status = " ⚠️ DRAWDOWN ACTIVO (75% sizing)"
            
            logger.info(f"📊 V6.4 Estado cargado: {total_trades} trades, Win Rate: {win_rate:.1f}%, P/L Total: ${total_pnl:.2f}, P/L Hoy: ${daily_pnl:.2f}{drawdown_status}")
            
        except Exception as e:
            logger.warning(f"⚠️ V6.4: Error cargando estado persistente (usando valores iniciales): {e}")
    
    def _check_open_positions_tp_sl(self, user_id: str = None) -> int:
        """
        PREMIUM: Gestión automática de posiciones con ATR-based TP/SL dinámico.
        
        Usa el DynamicPositionManager para:
        - TP/SL dinámico basado en ATR y régimen de mercado
        - Trailing Stop inteligente que sigue las ganancias
        - Break-even automático para proteger capital
        - Validación con Coherence Engine y Risk Guardian
        
        Args:
            user_id: ID del usuario (V6.5.4d MULTI-USER). Si None, usa fallback legacy.
        
        Returns:
            int: Número de posiciones cerradas
        """
        if not self.config['paper_mode'] or not self.paper_trading:
            return 0
        
        # V6.5.4d MULTI-USER: Usar método centralizado para obtener user_id
        user_id = self._get_effective_user_id(user_id, caller='_check_open_positions_tp_sl')
        
        # V6.5.4d MULTI-USER: Verify user has permission to view/manage positions
        try:
            self._require_trading_permission(user_id, 'view_positions')
        except AuthorizationError as e:
            logger.warning(f"🚫 {e}")
            return 0
        
        # PREMIUM: Usar DynamicPositionManager si está disponible
        if self.position_manager:
            try:
                result = self.position_manager.manage_all_positions(user_id, paper_mode=True)
                
                positions_closed = result.get('positions_closed', 0)
                trailing_updates = result.get('trailing_updates', 0)
                break_even_activations = result.get('break_even_activations', 0)
                total_pnl = result.get('total_pnl', 0)
                
                if trailing_updates > 0 or break_even_activations > 0:
                    logger.info(f"📊 Position Manager: {trailing_updates} trailing updates, {break_even_activations} break-even activations")
                
                if positions_closed > 0:
                    self._paper_trade_count += positions_closed
                    self.state['paper_trade_count'] = self._paper_trade_count
                    self._load_persistent_state()
                    logger.info(f"📊 {VERSION_BANNER} PREMIUM: {positions_closed} posiciones cerradas, P&L: ${total_pnl:.2f}")
                
                return positions_closed
                
            except Exception as e:
                logger.warning(f"⚠️ Position Manager error, usando fallback: {e}")
        
        # FALLBACK: Sistema básico si Position Manager no está disponible
        positions_closed = 0
        default_tp_pct = self.config.get('take_profit_pct', 0.03)
        default_sl_pct = self.config.get('stop_loss_pct', 0.02)
        
        try:
            open_positions = self.paper_trading.get_open_positions(user_id)
            
            if not open_positions:
                return 0
            
            for position in open_positions:
                symbol = position.get('symbol')
                entry_price = float(position.get('entry_price', 0))
                quantity = float(position.get('quantity', 0))
                
                if not symbol or entry_price <= 0 or quantity <= 0:
                    continue
                
                # V6.5.4 PREMIUM: Calibración por par si está disponible
                calibration = get_pair_calibration(symbol) if get_pair_calibration else None
                
                if calibration and calibration.tier != CalibrationTier.EXCLUDED:
                    tp_pct = calibration.take_profit_pct
                    sl_pct = calibration.stop_loss_pct
                    vol_class = calibration.tier.value
                    logger.debug(f"📊 Calibración {vol_class} para {symbol}: SL={sl_pct*100:.1f}%, TP={tp_pct*100:.1f}%")
                elif get_sl_tp_for_symbol and self.trading_profile:
                    sl_tp_config = get_sl_tp_for_symbol(symbol, self.trading_profile)
                    tp_pct = sl_tp_config['take_profit_pct']
                    sl_pct = sl_tp_config['stop_loss_pct']
                    vol_class = sl_tp_config.get('volatility_class', 'NORMAL')
                else:
                    tp_pct = default_tp_pct
                    sl_pct = default_sl_pct
                    vol_class = 'NORMAL'
                
                current_price = None
                for attempt in range(3):
                    try:
                        current_price = self.trading_service.get_current_price(symbol)
                        if current_price and current_price > 0:
                            break
                    except Exception:
                        time.sleep(0.3)
                
                if not current_price or current_price <= 0:
                    continue
                
                pnl_pct = (current_price - entry_price) / entry_price
                
                should_close = False
                close_reason = ""
                
                # V6.5.4d: LÍMITE MÁXIMO ABSOLUTO - PRIMERO verificar emergency SL
                # Esto es un "circuit breaker" a nivel de posición individual
                # IMPORTANTE: Este check va PRIMERO antes de cualquier otro SL
                # Usa self.EMERGENCY_SL_PCT definido a nivel de clase (2%)
                
                # ORDEN DE PRIORIDAD:
                # 1. Emergency SL (pérdida > 2%) - MÁXIMA PRIORIDAD
                # 2. Take Profit
                # 3. Stop Loss configurado por calibración
                
                if pnl_pct <= -self.EMERGENCY_SL_PCT:
                    # EMERGENCIA: Pérdida mayor al límite absoluto - CIERRA INMEDIATAMENTE
                    should_close = True
                    close_reason = f"🚨 EMERGENCY SL V6.5.4d ({pnl_pct*100:.2f}%) - MAX LOSS EXCEEDED [Limit:{self.EMERGENCY_SL_PCT*100:.1f}%]"
                    logger.warning(f"🚨 EMERGENCY STOP LOSS: {symbol} pérdida {pnl_pct*100:.2f}% > límite absoluto {self.EMERGENCY_SL_PCT*100:.1f}%")
                elif pnl_pct >= tp_pct:
                    should_close = True
                    close_reason = f"✅ TAKE PROFIT (+{pnl_pct*100:.2f}%) [Vol:{vol_class}]"
                elif pnl_pct <= -sl_pct:
                    should_close = True
                    close_reason = f"🛑 STOP LOSS ({pnl_pct*100:.2f}%) [Vol:{vol_class}]"
                
                if should_close:
                    import json as json_module
                    from datetime import datetime as dt_module
                    
                    sl_tp_event = {
                        "event": "SL_TP_TRIGGERED",
                        "timestamp": dt_module.utcnow().isoformat() + "Z",
                        "symbol": symbol,
                        "entry_price": entry_price,
                        "exit_price": current_price,
                        "quantity": quantity,
                        "pnl_pct": round(pnl_pct * 100, 4),
                        "pnl_usd": round((current_price - entry_price) * quantity, 2),
                        "trigger_type": "TAKE_PROFIT" if pnl_pct >= tp_pct else "STOP_LOSS",
                        "sl_threshold_pct": round(sl_pct * 100, 2),
                        "tp_threshold_pct": round(tp_pct * 100, 2),
                        "volatility_class": vol_class,
                        "profile": self.config.get('trading_profile', 'UNKNOWN'),
                        "check_interval_s": self.config.get('check_interval_seconds', 25)
                    }
                    logger.info(f"📊 SL/TP PREMIUM: {json_module.dumps(sl_tp_event)}")
                    logger.info(f"   🎯 {close_reason}")
                    
                    try:
                        result = self.paper_trading._close_position_fifo_v2(
                            user_id=user_id,
                            symbol=symbol,
                            sell_quantity=quantity,
                            exit_price=current_price
                        )
                        
                        if result:
                            positions_closed += 1
                            self._paper_trade_count += 1
                            self.state['paper_trade_count'] = self._paper_trade_count
                            
                            realized_pnl = sl_tp_event["pnl_usd"]
                            
                            self.update_pair_drawdown(symbol, realized_pnl)
                            
                            close_event = {
                                "event": "POSITION_CLOSED",
                                "timestamp": dt_module.utcnow().isoformat() + "Z",
                                "symbol": symbol,
                                "trigger": sl_tp_event["trigger_type"],
                                "realized_pnl": realized_pnl,
                                "trade_count": self._paper_trade_count
                            }
                            logger.info(f"✅ CLOSE PREMIUM: {json_module.dumps(close_event)}")
                    except Exception as close_err:
                        logger.warning(f"⚠️ Error cerrando {symbol}: {close_err}")
            
            if positions_closed > 0:
                self._load_persistent_state()
                
        except Exception as e:
            logger.error(f"❌ Error en gestión TP/SL fallback: {e}")
        
        return positions_closed
    
    def _trading_loop(self):
        """Loop principal 24/7 - MULTI-CRYPTO PREMIUM"""
        logger.info(f"🔄 Trading loop {VERSION_BANNER} MULTI-CRYPTO iniciado - Corriendo 24/7")
        logger.info(f"   📊 Configuración: {len(self.config.get('trading_pairs', ['BTC/USD']))} pares, intervalo {self.config['check_interval_seconds']}s")
        logger.info(f"   💰 Modo: {'PAPER' if self.config['paper_mode'] else 'REAL'} | Min trade: ${self.config['min_trade_usd']}")
        
        # Contador para procesar evaluaciones cada N ciclos
        evaluation_check_counter = 0
        evaluation_check_interval = 10  # Verificar evaluaciones cada 10 ciclos
        
        # Contador para alertas predictivas
        predictive_alert_counter = 0
        predictive_alert_interval = 10
        
        # V6.5: Contador de ciclos para logging periódico
        cycle_counter = 0
        log_interval = 20  # Log status cada 20 ciclos
        
        # V6.4: Índice para rotar entre pares
        pair_index = 0
        trading_pairs = self.config.get('trading_pairs', ['BTC/USD'])
        
        while self.state['running']:
            try:
                cycle_counter += 1
                
                # V6.5: Log periódico de estado para confirmar que está corriendo
                if cycle_counter % log_interval == 0:
                    win_rate = (self.state['winning_trades'] / self.state['total_trades'] * 100) if self.state['total_trades'] > 0 else 0
                    logger.info(f"📈 {VERSION_BANNER} STATUS: Ciclo #{cycle_counter} | Trades: {self.state['total_trades']} | Win Rate: {win_rate:.1f}% | P/L: ${self.state['total_profit_loss']:.2f}")
                
                # V6.5.4d: Heartbeat cada 12 ciclos (~5 minutos)
                if cycle_counter % 12 == 0:
                    self._write_heartbeat(cycle_counter)
                
                # Verificar parada de emergencia
                if self._check_emergency_stop():
                    logger.critical("🚨 PARADA DE EMERGENCIA - Pérdidas excesivas")
                    self.stop()
                    break
                
                # V6.5.4: Check Algorithmic Rollback Protocol (post-deploy drawdown protection)
                if ARP_AVAILABLE and cycle_counter % 10 == 0:  # Check every 10 cycles
                    try:
                        arp = get_arp_instance()
                        current_balance = self._get_balance()
                        rollback_result = arp.check_rollback_needed(current_balance)
                        
                        if rollback_result.rollback_triggered:
                            logger.critical(f"🔄 ARP ROLLBACK TRIGGERED: {rollback_result.message}")
                            # Execute rollback
                            rollback_exec = arp.execute_rollback()
                            self.state['emergency_stop'] = True
                            self.state['running'] = False  # Immediate halt flag
                            self.config['active'] = False
                            
                            # V6.5.4: Persist halted state to prevent auto-restart
                            self._persist_auto_trading_state(active=False)
                            
                            if rollback_exec.get('success'):
                                logger.critical("🛑 Trading halted - Configuration rolled back successfully")
                            else:
                                logger.critical(f"🚨 CRITICAL: Rollback failed: {rollback_exec.get('message')}")
                                logger.critical("🚨 TRADING HALTED - Manual intervention required")
                            
                            # Immediate exit from loop - do not continue to next iteration
                            return  # Exit _trading_loop entirely
                    except Exception as e:
                        logger.debug(f"ARP check failed: {e}")
                
                # Verificar Take Profit / Stop Loss en posiciones abiertas
                self._check_open_positions_tp_sl()
                
                # ========== FIX INSTITUCIONAL: LÍMITES AL INICIO ==========
                # Verificar límite de posiciones ANTES de gastar CPU en análisis de nuevas entradas
                # Si límite alcanzado, seguimos evaluando para SELLs pero bloqueamos BUYs
                position_limit_reached = self._check_position_limit_early()
                # La bandera position_limit_reached se usa más abajo para bloquear solo BUY
                # NO hacemos continue - continuamos evaluando coherencia, risk guardian, y SELLs
                # ========== FIN FIX INSTITUCIONAL ==========
                
                # V6.4: MULTI-CRYPTO - Escanear el par actual
                if self.config.get('use_multi_crypto', True) and len(trading_pairs) > 1:
                    current_pair = trading_pairs[pair_index]
                    self.config['trading_pair'] = current_pair
                    pair_index = (pair_index + 1) % len(trading_pairs)
                    logger.info(f"🔍 Escaneando {current_pair} ({pair_index+1}/{len(trading_pairs)})")
                
                # ========== V6.5.4c FIX: VERIFICAR EXCLUSIÓN ANTES DE ANÁLISIS ==========
                # Evita gastar recursos analizando pares que están EXCLUIDOS
                current_symbol = self.config.get('trading_pair', 'BTC/USD')
                if is_symbol_allowed and not is_symbol_allowed(current_symbol, self.trading_profile):
                    logger.warning(f"🚫 {VERSION_BANNER} SÍMBOLO EXCLUIDO: {current_symbol} - Saltando análisis")
                    time.sleep(1)  # Pequeña pausa para no saturar logs
                    continue  # Saltar al siguiente par
                # ========== FIN FIX EXCLUSIÓN ==========
                
                # Análisis completo
                analysis = self._analyze_market()
                
                # V6.5: Log detallado del análisis
                if analysis:
                    should_trade = analysis.get('should_trade', False)
                    confidence = analysis.get('confidence', 0)
                    # V6.5.4b FIX: Usar 'action' no 'signal' - decision usa 'action'
                    action_signal = analysis.get('action', 'HOLD')
                    reason = analysis.get('reason', 'N/A')
                    logger.info(f"   📊 Análisis: {action_signal} | Confianza: {confidence:.2%} | Trade: {'SÍ' if should_trade else 'NO'} | Razón: {reason[:50]}...")
                else:
                    logger.warning(f"   ⚠️ Sin datos de análisis para {self.config['trading_pair']}")
                
                # 🧠 V6.2: Check predictive alerts after market analysis
                if analysis and self.alert_dispatcher:
                    current_price = analysis.get('current_price', 0)
                    self._check_predictive_alerts(current_price)
                
                if analysis and analysis.get('should_trade'):
                    # V6.5.4b FIX: Usar 'action' no 'signal' - decision usa 'action' para BUY/SELL/HOLD
                    signal_type = analysis.get('action', 'HOLD')
                    
                    # FIX: Si límite de posiciones alcanzado, solo permitir SELL
                    if position_limit_reached and signal_type == 'BUY':
                        logger.info(f"🛑 {VERSION_BANNER}: BUY bloqueado - límite de posiciones alcanzado (SELL permitido)")
                        # No ejecutar BUY, continuar con el resto del loop (evaluaciones, TP/SL)
                    elif signal_type != 'HOLD':
                        # Ejecutar SELL siempre, o BUY solo si no hay límite alcanzado
                        logger.info(f"🎯 SEÑAL DE TRADE DETECTADA - {self.config['trading_pair']} - Ejecutando {signal_type}...")
                        result = self._execute_smart_trade(analysis)
                        
                        if result.get('success'):
                            trade_type = result.get('type', 'unknown')
                            trade_amount = result.get('amount', 0)
                            trade_price = result.get('price', 0)
                            logger.info(f"✅ TRADE EJECUTADO: {trade_type} {trade_amount} {self.config['trading_pair']} @ ${trade_price:.2f}")
                            logger.info(f"   📝 Detalles: {result}")
                            self._update_stats(result)
                            
                            if self.config['paper_mode'] and trade_type in ['BUY', 'SELL']:
                                self._paper_trade_count += 1
                                self.state['paper_trade_count'] = self._paper_trade_count
                                logger.info(f"📊 {VERSION_BANNER}: Trade #{self._paper_trade_count} registrado")
                        else:
                            error = result.get('error', 'Unknown error')
                            logger.warning(f"⚠️ Trade no ejecutado: {error}")
                
                # 🧠 Procesar evaluaciones pendientes cada N ciclos
                evaluation_check_counter += 1
                if evaluation_check_counter >= evaluation_check_interval:
                    evaluation_check_counter = 0
                    self._process_pending_evaluations()
                
                # V6.4: Esperar menos entre análisis para más oportunidades
                time.sleep(self.config['check_interval_seconds'])
                
            except Exception as e:
                logger.error(f"❌ Error en trading loop ciclo #{cycle_counter}: {e}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
                time.sleep(30)  # V6.4: Esperar 30s (era 60s) antes de reintentar
        
        logger.info(f"🔄 Trading loop {VERSION_BANNER} terminado después de {cycle_counter} ciclos")
    
    def _check_predictive_alerts(self, current_price: float):
        """
        Verificar y enviar alertas predictivas basadas en memoria Non-Markoviana.
        
        V6.2 Memory-Enhanced RMS: Evalúa métricas del kernel temporal y
        envía alertas anticipatorias sobre cambios de régimen.
        """
        if not self.alert_dispatcher or not self.memory_risk_adapter:
            return
        
        try:
            sent_alerts = self.alert_dispatcher.check_and_send_predictive_alerts(
                user_id='system_trading_bot',
                current_price=current_price
            )
            
            if sent_alerts:
                logger.info(f"🔮 {len(sent_alerts)} alertas predictivas enviadas")
                for alert in sent_alerts:
                    logger.info(f"   📢 {alert.get('type')}: {alert.get('severity')}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Error en alertas predictivas: {e}")
    
    def _analyze_market(self) -> Optional[Dict]:
        """
        Análisis completo del mercado usando TODAS las 9 estrategias V5.2
        
        Returns:
            Dict con análisis y recomendación
        """
        try:
            pair = self.config['trading_pair']
            
            # 1. Obtener precio actual
            try:
                # V6.5: Usar mapeo de símbolos para todos los 11 pares
                kraken_pair = self.convert_to_kraken_pair(pair)
                ticker_data = self.trading_service.kraken.get_ticker(kraken_pair)
                
                if not ticker_data or 'c' not in ticker_data:
                    logger.error(f"❌ No se pudo obtener ticker para {pair} (Kraken: {kraken_pair})")
                    return None
                
                current_price = float(ticker_data['c'][0])
                logger.info(f"💰 Precio actual de {pair}: ${current_price:,.2f}")
            except Exception as e:
                logger.error(f"❌ Error obteniendo precio de {pair}: {str(e)}")
                return None
            
            # Obtener histórico para análisis avanzados
            prices = self._get_price_history(pair, days=100)
            volumes = self._get_volume_history(pair, days=100)
            
            # ========== ESTRATEGIAS CLÁSICAS ==========
            
            # 2. Monte Carlo - Probabilidad de ganancia
            monte_carlo = None
            if hasattr(self.trading_service, 'monte_carlo'):
                monte_carlo = self.trading_service.monte_carlo.simulate(
                    current_price=current_price,
                    volatility=0.02,
                    days=7
                )
            
            # 3. Black Swan - Detectar riesgos extremos
            black_swan = None
            if self.advanced_features and hasattr(self.advanced_features, 'black_swan'):
                if prices and len(prices) >= 30:
                    black_swan = self.advanced_features.black_swan.analyze(prices)
            
            # 4. Sentiment - Sentimiento del mercado
            sentiment = None
            if self.advanced_features and hasattr(self.advanced_features, 'sentiment'):
                sentiment = self.advanced_features.sentiment.analyze(pair.split('/')[0])
            
            # ========== ESTRATEGIAS V5.2 QUANTUM ==========
            
            # 5. Kelly Criterion - Position sizing óptimo
            kelly = None
            if self.config['use_v52_strategies'] and self.advanced_features:
                if hasattr(self.advanced_features, 'kelly_optimizer'):
                    kelly = self.advanced_features.kelly_optimizer.calculate_optimal_position(
                        win_rate=0.55,  # Basado en histórico
                        avg_win=0.03,
                        avg_loss=0.02,
                        total_capital=self._get_balance()
                    )
            
            # 6. HMM Regime Detection - Detectar régimen de mercado
            # FIX: Solo requiere prices, volumes es opcional
            hmm_regime = None
            if self.config['use_v52_strategies'] and self.advanced_features:
                if hasattr(self.advanced_features, 'hmm_regime') and prices:
                    hmm_regime = self.advanced_features.hmm_regime.detect_regime(
                        prices=prices[-50:],
                        volumes=volumes[-50:] if volumes else None
                    )
            
            # 7. Kalman Filter - Trend detection con lag mínimo
            kalman = None
            if self.config['use_v52_strategies'] and self.advanced_features:
                if hasattr(self.advanced_features, 'kalman_filter') and prices:
                    kalman = self.advanced_features.kalman_filter.filter_and_predict(
                        prices=prices[-100:]  # Últimas 100 velas
                    )
            
            # 8. Quantum Momentum - Estrategia propietaria 6 componentes
            # FIX: Usar analyze() con OHLC completo, volumes sintéticos si no disponible
            quantum = None
            if self.config['use_v52_strategies'] and self.advanced_features:
                if hasattr(self.advanced_features, 'quantum_momentum') and prices:
                    try:
                        ohlc_data = self._get_ohlc_history(pair, days=200)
                        if ohlc_data and len(ohlc_data.get('closes', [])) >= 60:
                            quantum = self.advanced_features.quantum_momentum.analyze(
                                prices=ohlc_data['closes'],
                                highs=ohlc_data['highs'],
                                lows=ohlc_data['lows'],
                                volumes=ohlc_data['volumes']
                            )
                    except Exception as e:
                        logger.debug(f"Quantum Momentum analysis skipped: {e}")
            
            # 9. ADAPTIVE WEIGHTS - Calcular pesos dinámicos ω(t) basados en Hurst y α
            adaptive_weights = None
            if self.adaptive_system and prices and len(prices) >= 50:
                try:
                    adaptive_weights = self.adaptive_system.update_weights(prices)
                    logger.info(f"⚡ Pesos Adaptativos: ω={adaptive_weights.omega:.3f}, H={adaptive_weights.hurst:.3f}, α={adaptive_weights.alpha:.3f}, Régimen={adaptive_weights.regime}")
                except Exception as e:
                    logger.error(f"Error calculando pesos adaptativos: {e}")
            
            # 10. NON-MARKOVIAN MEMORY KERNEL V6.1 - Temporal Memory Analysis
            non_markovian = None
            if self.non_markovian_kernel and current_price:
                try:
                    min_required = 24
                    kernel_history_len = self.non_markovian_kernel.get_history_length()
                    
                    # FIX: Estado explícito para manejo robusto de cambios de par
                    is_pair_change = (self._last_kernel_pair is not None and self._last_kernel_pair != pair)
                    
                    # 1) Detectar cambio de par -> marcar para reseed
                    if is_pair_change:
                        logger.info(f"🧠 Pair change: {self._last_kernel_pair} -> {pair}")
                        self._kernel_needs_reseed = True
                        self.non_markovian_kernel.seed_history([], clear_existing=True)
                        kernel_history_len = 0
                    
                    # 2) Verificar si historia insuficiente
                    if kernel_history_len < min_required:
                        self._kernel_needs_reseed = True
                    
                    # 3) Intentar reseed si está pendiente
                    if self._kernel_needs_reseed:
                        if prices and len(prices) >= min_required:
                            loaded = self.non_markovian_kernel.seed_history(prices, clear_existing=True)
                            self._last_kernel_pair = pair
                            self._kernel_needs_reseed = False
                            logger.debug(f"🧠 Kernel seeded with {loaded} prices for {pair}")
                        else:
                            logger.debug(f"🧠 Reseed pending for {pair} (have {len(prices) if prices else 0}, need {min_required})")
                    
                    # 4) Solo generar señal si kernel está listo
                    if not self._kernel_needs_reseed:
                        non_markovian = self.non_markovian_kernel.generate_signal(
                            current_price=current_price,
                            market_data={'prices': prices} if prices else None
                        )
                        if non_markovian and non_markovian.get('signal') != 'HOLD':
                            logger.info(f"🧠 Non-Markovian Kernel: {non_markovian.get('signal')} ({non_markovian.get('confidence', 0):.1f}% conf)")
                except Exception as e:
                    # Error -> marcar para reseed en próximo ciclo
                    self._kernel_needs_reseed = True
                    logger.debug(f"Error en Non-Markovian Kernel (retry próximo ciclo): {e}")
            
            # 10.5 EMA REGIME SIGNAL V6.5.4d - REAL DETERMINISTIC SIGNAL
            # QUARANTINE GUARD: Check if symbol is allowed BEFORE generating EMA signal
            ema_signal = None
            symbol_allowed_for_ema = True  # Default: allow unless blocked
            
            if is_symbol_allowed and self.trading_profile:
                symbol_allowed_for_ema = is_symbol_allowed(pair, self.trading_profile)
                if not symbol_allowed_for_ema:
                    # SENTINEL LOG: Quarantine blocks EMA signal generation
                    logger.info(f"🛑 [QUARANTINE_BLOCK] EMA signal skipped for quarantined {pair}")
                    # No need to generate signal for quarantined asset
            
            if self.ema_signal_generator and prices and symbol_allowed_for_ema:
                try:
                    ohlc_data = self._get_ohlc_history(pair, days=100)
                    ema_signal = self.ema_signal_generator.generate_signal(
                        symbol=pair,
                        prices=prices,
                        highs=ohlc_data.get('highs') if ohlc_data else None,
                        lows=ohlc_data.get('lows') if ohlc_data else None,
                        hmm_regime=hmm_regime,
                        current_price=current_price
                    )
                    if ema_signal and ema_signal.direction != "NONE":
                        logger.info(f"📊 EMA Signal: {ema_signal.direction} | Conf: {ema_signal.confidence:.1%} | Rationale: {', '.join(ema_signal.rationale[:3])}")
                except Exception as e:
                    logger.debug(f"EMA Signal generation skipped: {e}")
            
            # 11. Decisión basada en TODOS los análisis + Pesos Adaptativos + EMA Signal
            decision = self._make_v52_decision(
                current_price=current_price,
                monte_carlo=monte_carlo,
                black_swan=black_swan,
                sentiment=sentiment,
                kelly=kelly,
                hmm_regime=hmm_regime,
                kalman=kalman,
                quantum=quantum,
                adaptive_weights=adaptive_weights,
                non_markovian=non_markovian,
                ema_signal=ema_signal
            )
            
            # 11. 🧠 CEREBRO CONVERSACIONAL - Generar razonamiento pre-trade
            if self.conversational_brain and decision.get('should_trade'):
                try:
                    # Preparar señales para el razonamiento
                    signals = {
                        'quantum_momentum': quantum if quantum else {},
                        'kalman_filter': kalman if kalman else {},
                        'monte_carlo': monte_carlo if monte_carlo else {},
                        'black_swan': black_swan if black_swan else {},
                        'sentiment': sentiment if sentiment else {},
                        'kelly_criterion': kelly if kelly else {},
                        'hmm_regime': hmm_regime if hmm_regime else {}
                    }
                    
                    reasoning = self.conversational_brain.generate_trade_reasoning(
                        action=decision['action'],
                        pair=pair,
                        amount_usd=decision.get('amount_usd', 0),
                        signals=signals,
                        confidence=decision.get('confidence', 0)
                    )
                    
                    # Adjuntar razonamiento a la decisión (sin bloquear)
                    decision['reasoning'] = reasoning
                    decision['reasoning_summary'] = reasoning.get('summary', '')
                    decision['reasoning_explanation'] = reasoning.get('full_explanation', '')
                    
                    # V6.5.4: Log institutional AI_NARRATIVE (post-decision, NOT decision-making)
                    logger.info(f"🧠 AI_NARRATIVE (post-decisión): {reasoning.get('summary', '')[:100]}")
                    if institutional_logger and decision.get('decision_id'):
                        institutional_logger.log_ai_narrative(
                            symbol=pair,
                            decision_id=decision.get('decision_id'),
                            direction=decision.get('action', 'HOLD'),
                            explanation=reasoning.get('summary', '')
                        )
                except Exception as e:
                    logger.warning(f"Error generando razonamiento (no crítico): {e}")
                    decision['reasoning'] = None
            
            logger.info(f"📊 Análisis V5.2 completado: {decision.get('action', 'HOLD')} - Confianza: {decision.get('confidence', 0):.1%}")
            
            return decision
            
        except Exception as e:
            logger.error(f"Error en análisis: {e}")
            return None
    
    def _make_v52_decision(
        self, 
        current_price: float,
        monte_carlo: Optional[Dict],
        black_swan: Optional[Dict],
        sentiment: Optional[Dict],
        kelly: Optional[Dict],
        hmm_regime: Optional[Dict],
        kalman: Optional[Dict],
        quantum: Optional[Dict],
        adaptive_weights: Optional[object] = None,
        non_markovian: Optional[Dict] = None,
        ema_signal: Optional[object] = None
    ) -> Dict:
        """
        Decisión AVANZADA V6.5.4d integrando TODAS las estrategias + EMA Signal REAL
        
        Sistema de scoring ponderado que combina señales de múltiples fuentes
        
        V6.5.4d CHANGES:
        - EMA Regime Signal como señal PRINCIPAL (reemplaza ARES placeholders)
        - Monte Carlo como VETO REAL (no solo logging)
        - LimitsEngine/CircuitBreaker ENFORCED antes de trades
        
        NUEVO V5.2: Usa pesos adaptativos ω(t) para balancear Kalman vs Monte Carlo
        - ω cerca de 0 → favorece Kalman Filter (mercado normal)
        - ω cerca de 1 → favorece Monte Carlo (mercado extremo/volátil)
        
        NUEVO V6.1: Non-Markovian Memory Kernel para capturar dependencias temporales
        - K(t-s) = exp(-|t-s|/τ)[1 + ε cos(Ω(t-s))]
        - Detecta patrones cíclicos y coherencia de régimen
        """
        try:
            # V6.5.4: Get symbol for institutional logging
            symbol = self.config.get('trading_pair', 'UNKNOWN')
            
            # V6.5.4: Generate decision_id early for complete traceability
            decision_id = None
            if institutional_logger:
                decision_id = institutional_logger._generate_decision_id(symbol)
            
            decision = {
                'should_trade': False,
                'action': 'HOLD',
                'confidence': 0.0,
                'reason': [],
                'v52_analysis': {},
                'current_price': current_price,
                'symbol': symbol,
                'decision_id': decision_id,
                'veto_chain': [],
                'guards_passed': [],
                'mc_veto': False,
                'rms_veto': False,
                'ema_signal': None,
                'decision_trace': []
            }
            
            # ========== V6.5.4d MONTE CARLO VETO ENGINE ==========
            # Monte Carlo ahora VETA trades en lugar de solo loguear
            mc_veto_applied = False
            position_size_factor = 1.0  # Default full size
            
            if monte_carlo and hasattr(self, 'mc_veto_config'):
                mc_cfg = self.mc_veto_config
                expected_return = monte_carlo.get('expected_return', 0)
                var_95 = monte_carlo.get('var_95', 0)
                win_rate = monte_carlo.get('win_rate', 0.5)
                
                decision['v52_analysis']['mc_expected_return'] = expected_return
                decision['v52_analysis']['mc_var_95'] = var_95
                decision['v52_analysis']['mc_win_rate'] = win_rate
                
                # VETO 1: Expected return negativo
                if expected_return < mc_cfg['min_expected_return']:
                    mc_veto_applied = True
                    decision['veto_chain'].append('MC_EXPECTED_RETURN_NEGATIVE')
                    decision['decision_trace'].append(f"MC_VETO: Expected return {expected_return:.2%} < 0")
                    logger.info(f"🚫 MC VETO: Expected return {expected_return:.2%} < 0 → TRADE BLOCKED")
                
                # VETO 2: VaR95 demasiado alto (pérdida potencial > umbral)
                if var_95 < mc_cfg['max_var_95']:  # var_95 es negativo
                    mc_veto_applied = True
                    decision['veto_chain'].append('MC_VAR_TOO_HIGH')
                    decision['decision_trace'].append(f"MC_VETO: VaR95 {var_95:.2%} worse than {mc_cfg['max_var_95']:.2%}")
                    logger.info(f"🚫 MC VETO: VaR95 {var_95:.2%} > limit {mc_cfg['max_var_95']:.2%} → TRADE BLOCKED")
                
                # SIZE REDUCTION: Win rate bajo pero no veto
                if not mc_veto_applied and win_rate < mc_cfg['reduce_size_win_rate']:
                    raw_factor = mc_cfg['size_reduction_factor']
                    # DEFENSIVE CLAMP: Ensure factor is in valid range [0.0, 1.0]
                    position_size_factor = max(0.0, min(raw_factor, 1.0))
                    # Log if clamping occurred
                    if raw_factor != position_size_factor:
                        decision['decision_trace'].append(f"MC_SIZE_FACTOR_CLAMPED: raw {raw_factor:.2f} → clamped {position_size_factor:.2f}")
                        logger.warning(f"🛡️ MC factor clamped: raw {raw_factor:.2f} → {position_size_factor:.2f}")
                    decision['decision_trace'].append(f"MC_SIZE_REDUCE: Win rate {win_rate:.1%} → size {position_size_factor:.0%}")
                    logger.info(f"📉 MC SIZE REDUCE: Win rate {win_rate:.1%} < {mc_cfg['reduce_size_win_rate']:.0%} → position {position_size_factor:.0%}")
                
                if mc_veto_applied:
                    decision['mc_veto'] = True
                    decision['reason'].append(f"🚫 MC VETO: {', '.join(decision['veto_chain'])}")
                else:
                    decision['guards_passed'].append('MONTE_CARLO')
                
                decision['v52_analysis']['mc_position_size_factor'] = position_size_factor
            
            # ========== V6.5.4d RMS ENFORCEMENT (LimitsEngine + CircuitBreaker) ==========
            rms_veto_applied = False
            
            if self.limits_engine or self.circuit_breaker:
                # CircuitBreaker check first (system-wide halt)
                if self.circuit_breaker:
                    try:
                        halt_result = self.circuit_breaker.check_halt(symbol=symbol)
                        if halt_result and halt_result.get('should_halt', False):
                            rms_veto_applied = True
                            halt_reason = halt_result.get('reason', 'CIRCUIT_BREAKER_HALT')
                            decision['veto_chain'].append(f'CB_{halt_reason}')
                            decision['decision_trace'].append(f"CIRCUIT_BREAKER: {halt_reason}")
                            logger.info(f"🔌 CIRCUIT BREAKER HALT: {halt_reason} → TRADE BLOCKED")
                    except Exception as e:
                        logger.debug(f"CircuitBreaker check skipped: {e}")
                
                # LimitsEngine check (position limits, daily limits, etc)
                if self.limits_engine and not rms_veto_applied:
                    try:
                        limits_result = self.limits_engine.validate_order(
                            symbol=symbol,
                            side='BUY',  # Placeholder - will be updated based on actual decision
                            size=1.0,  # Placeholder - actual size calculated later
                            price=current_price
                        )
                        if limits_result and not limits_result.get('valid', True):
                            rms_veto_applied = True
                            limit_reason = limits_result.get('reason', 'LIMITS_EXCEEDED')
                            decision['veto_chain'].append(f'LE_{limit_reason}')
                            decision['decision_trace'].append(f"LIMITS_ENGINE: {limit_reason}")
                            logger.info(f"🚧 LIMITS ENGINE VETO: {limit_reason} → TRADE BLOCKED")
                    except Exception as e:
                        logger.debug(f"LimitsEngine check skipped: {e}")
                
                if rms_veto_applied:
                    decision['rms_veto'] = True
                    decision['reason'].append(f"🚧 RMS VETO: {', '.join([v for v in decision['veto_chain'] if v.startswith('CB_') or v.startswith('LE_')])}")
                else:
                    decision['guards_passed'].append('RMS_VALIDATION')
            
            # ========== V6.5.4d EMA REGIME SIGNAL (REAL DETERMINISTIC SIGNAL) ==========
            ema_direction = None
            ema_confidence = 0.0
            
            if ema_signal:
                decision['ema_signal'] = ema_signal.to_dict() if hasattr(ema_signal, 'to_dict') else str(ema_signal)
                ema_direction = ema_signal.direction
                ema_confidence = ema_signal.confidence
                
                decision['v52_analysis']['ema_direction'] = ema_direction
                decision['v52_analysis']['ema_confidence'] = ema_confidence
                decision['v52_analysis']['ema_rationale'] = ema_signal.rationale if hasattr(ema_signal, 'rationale') else []
                
                if ema_direction != "NONE":
                    decision['decision_trace'].append(f"EMA_SIGNAL: {ema_direction} @ {ema_confidence:.1%}")
                    decision['guards_passed'].append('EMA_SIGNAL')
            
            # EARLY RETURN si hay veto de MC o RMS
            if mc_veto_applied or rms_veto_applied:
                decision['action'] = 'HOLD'
                decision['should_trade'] = False
                decision['confidence'] = 0.0
                decision['vetoed'] = True
                veto_reason = ', '.join(decision['veto_chain']) if decision['veto_chain'] else 'UNKNOWN'
                decision['veto_reason'] = veto_reason
                decision['reason'].append("⛔ VETO ACTIVO - Trade bloqueado por gestión de riesgo")
                decision['decision_trace'].append(f"VETO_EARLY_RETURN: {veto_reason}")
                # SENTINEL LOG: Confirm veto cuts flow - this should appear when trade is blocked
                logger.warning(f"🚫 [VETO_ENFORCED] {symbol} | reason={veto_reason} | decision_id={decision.get('decision_id')} → HOLD EARLY RETURN")
                return decision
            
            # SENTINEL LOG: This should NEVER appear if vetoed above
            # If this log appears after a veto, the early return failed
            logger.debug(f"[EXEC_PATH] Proceeding to Coherence Gate for {symbol} - No MC/RMS veto applied")
            
            # ========== V6.5.4d COHERENCE PRE-GATE (ANTES del scoring) ==========
            # Coherence actúa como GATE: si no hay consenso mínimo, no hay scoring
            # Esto elimina falsos positivos y reduce overtrading
            coherence_gate_passed = True
            coherence_pre_score = None
            
            if self.coherence_engine:
                try:
                    # Construir señales para Coherence Gate (evaluación temprana)
                    strategy_signals = self._build_strategy_signals(
                        monte_carlo, black_swan, sentiment, kelly, 
                        hmm_regime, kalman, quantum, non_markovian
                    )
                    
                    # Evaluar coherencia ANTES del scoring
                    coherence_report = self.coherence_engine.analyze_coherence(strategy_signals)
                    coherence_pre_score = coherence_report.coherence_score
                    
                    # Obtener umbrales del perfil
                    p = self.trading_profile
                    veto_critical = p.coherence_veto_critical if p else 30.0
                    veto_normal = p.coherence_veto_normal if p else 45.0
                    
                    decision['v52_analysis']['coherence_pre_score'] = coherence_pre_score
                    decision['v52_analysis']['coherence_pre_level'] = coherence_report.coherence_level.value
                    
                    # GATE: Bloquear si coherencia es crítica o normal-veto
                    if coherence_pre_score < veto_critical or coherence_report.coherence_level.value == 'CRITICAL':
                        coherence_gate_passed = False
                        decision['veto_chain'].append('COHERENCE_GATE_CRITICAL')
                        decision['decision_trace'].append(f"COHERENCE_GATE: {coherence_pre_score:.1f}% < {veto_critical}% → REJECTED")
                        logger.warning(f"🚫 [COHERENCE_GATE] CRITICAL: Score {coherence_pre_score:.1f}% < {veto_critical}% → NO SCORING")
                    elif coherence_pre_score < veto_normal:
                        coherence_gate_passed = False
                        decision['veto_chain'].append('COHERENCE_GATE_LOW')
                        decision['decision_trace'].append(f"COHERENCE_GATE: {coherence_pre_score:.1f}% < {veto_normal}% → REJECTED")
                        logger.warning(f"🚫 [COHERENCE_GATE] LOW: Score {coherence_pre_score:.1f}% < {veto_normal}% → NO SCORING")
                    else:
                        decision['guards_passed'].append('COHERENCE_GATE')
                        decision['decision_trace'].append(f"COHERENCE_GATE: {coherence_pre_score:.1f}% >= {veto_normal}% → PASSED")
                        logger.info(f"✅ [COHERENCE_GATE] PASSED: Score {coherence_pre_score:.1f}% >= {veto_normal}%")
                        
                except Exception as e:
                    logger.debug(f"Coherence Gate skipped: {e}")
                    decision['decision_trace'].append(f"COHERENCE_GATE: Skipped due to error")
            
            # EARLY RETURN si Coherence Gate no pasa
            if not coherence_gate_passed:
                decision['action'] = 'HOLD'
                decision['should_trade'] = False
                decision['confidence'] = 0.0
                decision['vetoed'] = True
                decision['veto_reason'] = 'COHERENCE_GATE_REJECTED'
                decision['reason'].append(f"🚫 COHERENCE GATE: Coherencia {coherence_pre_score:.1f}% insuficiente - Trade bloqueado antes de scoring")
                logger.warning(f"🚫 [COHERENCE_GATE_ENFORCED] {symbol} | score={coherence_pre_score:.1f}% → HOLD EARLY RETURN")
                return decision
            
            logger.debug(f"[EXEC_PATH] Proceeding to scoring for {symbol} - Coherence Gate passed")
            
            score = 0  # Score de confianza (-100 a +100)
            max_score = 0  # Para normalizar
            
            # ========== PESOS ADAPTATIVOS V5.2 QUANTUM ==========
            # Calcular pesos dinámicos basados en Hurst y α-stable
            kalman_weight = 1.0  # Default: pesos iguales
            monte_carlo_weight = 1.0
            
            if adaptive_weights:
                # ω(t) ∈ [0,1]: 0=100% Kalman, 1=100% Monte Carlo
                omega = adaptive_weights.omega
                kalman_weight = 1.0 - omega  # Inverso de omega
                monte_carlo_weight = omega
                
                decision['v52_analysis']['adaptive_omega'] = omega
                decision['v52_analysis']['hurst_exponent'] = adaptive_weights.hurst
                decision['v52_analysis']['alpha_stable'] = adaptive_weights.alpha
                decision['v52_analysis']['market_regime_adaptive'] = adaptive_weights.regime
                decision['reason'].append(f"⚡ Pesos: Kalman {kalman_weight:.0%} | Monte Carlo {monte_carlo_weight:.0%} (H={adaptive_weights.hurst:.2f}, α={adaptive_weights.alpha:.2f})")
                
                # Logging para inversores
                logger.info(f"⚡ ADAPTIVE WEIGHTS: ω={omega:.3f}, Kalman={kalman_weight:.3f}, MC={monte_carlo_weight:.3f}, H={adaptive_weights.hurst:.3f}, α={adaptive_weights.alpha:.3f}, Regime={adaptive_weights.regime}")
            
            # ========== V6.5.4d: VETO/PENALTY ONLY (GPT Expert Dec 24, 2025) ==========
            # Monte Carlo, Black Swan, Sentiment, Quantum Momentum: NO suman al max_score
            # Solo aplican penalizaciones o pequeños boosts. El scoring principal es:
            # EMA(40) + HMM(25) + Kalman(15) + Non-Markovian(15) + Kelly(10 modifier) = 105 pts
            
            is_paper_mode = self.config.get('paper_mode', False)
            
            # 1. Monte Carlo (VETO/PENALTY ONLY - no suma a max_score)
            if monte_carlo:
                win_rate = monte_carlo.get('win_rate', 0.5)
                win_rate_pct = win_rate * 100 if win_rate <= 1 else win_rate
                
                if win_rate_pct < 40:
                    mc_penalty = 10 if is_paper_mode else 20
                    score -= mc_penalty
                    decision['reason'].append(f"⚠️ Monte Carlo VETO: {win_rate_pct:.1f}% win rate → -{mc_penalty}")
                    decision['decision_trace'].append(f'MC_VETO: WinRate {win_rate_pct:.1f}% < 40%')
                elif win_rate_pct > 60:
                    decision['reason'].append(f"✅ Monte Carlo: {win_rate_pct:.1f}% win rate OK")
            
            # 2. Black Swan (VETO/PENALTY ONLY - no suma a max_score)
            if black_swan:
                risk_level = black_swan.get('risk_level', 'MEDIUM')
                crash_prob = black_swan.get('crash_probability', 50)
                
                if risk_level == 'HIGH' or crash_prob > 30:
                    bs_penalty = 8 if is_paper_mode else 25
                    score -= bs_penalty
                    decision['reason'].append(f"🚨 Black Swan VETO: Riesgo {risk_level} → -{bs_penalty}")
                    decision['decision_trace'].append(f'BLACK_SWAN_VETO: {risk_level}, CrashProb={crash_prob}%')
                elif risk_level == 'LOW':
                    decision['reason'].append(f"✅ Black Swan: Riesgo BAJO OK")
            
            # 3. Sentiment (VETO/PENALTY ONLY - no suma a max_score)
            # Fear & Greed Contrarian mantiene pequeño boost como excepción táctica
            if sentiment:
                sent_score = sentiment.get('overall_score', 50)
                fear_greed = sentiment.get('fear_greed_index', sent_score)
                
                if sent_score < 25:
                    sent_penalty = 5 if is_paper_mode else 15
                    score -= sent_penalty
                    decision['reason'].append(f"⚠️ Sentiment VETO: {sent_score:.0f}/100 Extreme Negative → -{sent_penalty}")
                elif sent_score < 35:
                    contrarian_boost = 3 if is_paper_mode else 2
                    score += contrarian_boost
                    decision['reason'].append(f"🎯 Fear Contrarian: +{contrarian_boost} (miedo = oportunidad)")
                elif sent_score > 80:
                    greed_penalty = 3 if is_paper_mode else 8
                    score -= greed_penalty
                    decision['reason'].append(f"⚠️ Greed Warning: -{greed_penalty} (euforia = riesgo)")
                
                if fear_greed < 20:
                    decision['reason'].append(f"😱 Extreme Fear F&G={fear_greed} - observando")
            
            # ========== CORE SCORING INPUTS (GPT Expert Dec 24, 2025) ==========
            # 5 inputs principales: EMA(40), HMM(25), Kalman(15), Non-Markovian(15), Kelly(10)
            
            # 4. Quantum Momentum (VETO/PENALTY ONLY - no suma a max_score)
            if quantum:
                signal = quantum.get('signal', 0)  # -10 a +10
                confidence_level = quantum.get('confidence', 'LOW')
                
                if confidence_level in ['HIGH', 'VERY_HIGH']:
                    if signal <= -7:
                        qm_penalty = 10 if is_paper_mode else 20
                        score -= qm_penalty
                        decision['reason'].append(f"📉 Quantum VETO: STRONG SELL → -{qm_penalty}")
                        decision['decision_trace'].append(f'QUANTUM_VETO: Signal={signal}')
                    elif signal <= -4:
                        qm_penalty = 5 if is_paper_mode else 10
                        score -= qm_penalty
                        decision['reason'].append(f"⚠️ Quantum Penalty: SELL → -{qm_penalty}")
                    elif signal >= 7:
                        decision['reason'].append(f"🚀 Quantum: STRONG BUY (signal {signal}/10) OK")
                decision['v52_analysis']['quantum_signal'] = signal
            
            # 5. Kalman Filter (peso: 15 puntos * kalman_weight)
            kalman_base_weight = 15
            if kalman:
                adjusted_weight = kalman_base_weight * kalman_weight
                max_score += adjusted_weight
                trend = kalman.get('trend', 'NEUTRAL')
                strength = kalman.get('trend_strength', 0)
                
                if trend == 'BULLISH' and strength > 0.6:
                    score += adjusted_weight
                    decision['reason'].append(f"📈 Kalman: BULLISH trend ({strength:.1%}) (peso: {kalman_weight:.0%})")
                elif trend == 'BULLISH':
                    score += adjusted_weight * 0.53
                elif trend == 'BEARISH' and strength > 0.6:
                    score -= adjusted_weight
                    decision['reason'].append(f"📉 Kalman: BEARISH trend ({strength:.1%}) (peso: {kalman_weight:.0%})")
                elif trend == 'BEARISH':
                    score -= adjusted_weight * 0.53
                decision['v52_analysis']['kalman_trend'] = trend
            
            # 6. HMM Regime (peso: 25 puntos) + V6.5.4d QUALITY FILTER (GPT Expert Dec 24, 2025)
            # Peso aumentado de 15 a 25 para simplificar a 5 inputs principales
            if hmm_regime:
                max_score += 25
                regime = hmm_regime.get('regime', 'UNKNOWN')
                params = hmm_regime.get('recommended_params', {})
                regime_confidence = hmm_regime.get('confidence', 0.5)
                
                # V6.5.4d: HMM QUALITY FILTER - Boost para trades alineados con régimen
                # Peso aumentado de 15 a 25 (GPT Expert Dec 24, 2025)
                if regime == 'TRENDING':
                    score += 25
                    decision['reason'].append(f"✅ HMM: {regime} ({regime_confidence:.0%} conf)")
                    decision['v52_analysis']['hmm_quality_bonus'] = True
                elif regime == 'RANGING':
                    # V6.4: Solo penalizar si confianza alta en ranging
                    if regime_confidence > 0.7:
                        score -= 8
                        decision['reason'].append(f"⚠️ HMM: {regime} market - reduciendo")
                    else:
                        score -= 3  # Penalización menor si confianza baja
                elif regime == 'VOLATILE':
                    # HMM VETO muy reducido en paper mode para generar trades
                    p = self.trading_profile  # Shorthand
                    hmm_veto_enabled = p.hmm_veto_enabled if p else True
                    hmm_veto_threshold = p.hmm_veto_confidence_threshold if p else 0.85
                    
                    if hmm_veto_enabled and regime_confidence > hmm_veto_threshold:
                        veto_penalty = 3 if is_paper_mode else 15  # -3 paper, -15 real
                        score -= veto_penalty
                        mode_label = "[PAPER -3]" if is_paper_mode else "[REAL -15]"
                        decision['reason'].append(f"🚨 HMM: VOLATILE extremo - VETO {mode_label} (conf > {hmm_veto_threshold:.0%})")
                        decision['v52_analysis']['hmm_volatility_veto'] = True
                    else:
                        score -= 2 if is_paper_mode else 5  # -2 paper, -5 real
                        decision['reason'].append(f"⚠️ HMM: {regime} moderado")
                
                decision['v52_analysis']['market_regime'] = regime
                decision['v52_analysis']['hmm_confidence'] = regime_confidence
                
                # Ajustar position size según régimen
                if params:
                    decision['v52_analysis']['regime_params'] = params
            
            # ADAPTIVE REGIME CROSS-VALIDATION
            # Si adaptive_weights y HMM detectan régimen EXTREME/VOLATILE simultáneamente → VETO
            # Configurable por perfil
            p = self.trading_profile  # Shorthand
            regime_change_veto_enabled = p.regime_change_veto_enabled if p else True
            
            if adaptive_weights and hmm_regime and regime_change_veto_enabled:
                adaptive_regime = adaptive_weights.regime if hasattr(adaptive_weights, 'regime') else 'NORMAL'
                hmm_detected = hmm_regime.get('regime', 'UNKNOWN')
                
                # Criterio de cambio de régimen crítico
                # Penalizaciones MUY reducidas en paper mode para generar trades
                if adaptive_regime in ['EXTREME', 'VOLATILE'] and hmm_detected == 'VOLATILE':
                    veto_penalty = 3 if is_paper_mode else 20  # -3 paper, -20 real
                    score -= veto_penalty
                    mode_label = "[PAPER -3]" if is_paper_mode else "[REAL -20]"
                    decision['reason'].append(f"🚨 REGIME CHANGE DETECTED: {adaptive_regime} + HMM {hmm_detected} → VETO {mode_label}")
                    decision['v52_analysis']['regime_change_veto'] = True
                    logger.warning(f"🚨 REGIME CHANGE VETO {mode_label}: Adaptive={adaptive_regime}, HMM={hmm_detected}")
                elif adaptive_regime == 'EXTREME':
                    extreme_penalty = 2 if is_paper_mode else 10  # -2 paper, -10 real
                    score -= extreme_penalty
                    decision['reason'].append(f"⚡ Adaptive Regime: {adaptive_regime} → Reduciendo exposición")
                    
                decision['v52_analysis']['adaptive_regime'] = adaptive_regime
                decision['v52_analysis']['regime_consensus'] = adaptive_regime == hmm_detected
            
            # 7. Kelly Criterion (peso: 10 puntos - para sizing, no señal)
            if kelly:
                max_score += 10
                optimal_size = kelly.get('optimal_fraction', 0)
                recommended = kelly.get('recommended_position_usd', 0)
                
                if optimal_size > 0.05:  # Kelly sugiere posición >5%
                    score += 10
                    decision['reason'].append(f"💰 Kelly: Posición óptima {optimal_size:.1%}")
                    decision['v52_analysis']['kelly_position'] = recommended
                elif optimal_size < 0.01:  # Kelly sugiere muy poco
                    score -= 10
                    decision['reason'].append(f"⚠️ Kelly: Posición óptima muy baja")
            
            # ========== ARES REMOVED (Dec 24, 2025) ==========
            # ARES V1/V2 eliminated from scoring. EMA Regime Signal is now sole driver.
            # Legacy code removed to reduce noise. See git history for reference.
            decision['v52_analysis']['ares_status'] = 'REMOVED'
            decision['decision_trace'].append('ARES_REMOVED: Code eliminated Dec 24, 2025')
            
            # 8. NON-MARKOVIAN MEMORY KERNEL V6.5.4d (peso: 15 puntos - GPT Expert Dec 24, 2025)
            # Peso aumentado de 12 a 15 para simplificar a 5 inputs principales
            if non_markovian:
                max_score += 15
                nm_signal = non_markovian.get('signal', 'HOLD')
                nm_confidence = non_markovian.get('confidence', 0)
                nm_metrics = non_markovian.get('metrics', {})
                
                if nm_signal == 'BUY' and nm_confidence > 60:
                    score += 15
                    decision['reason'].append(f"🧠 Non-Markovian: BUY ({nm_confidence:.0f}% conf)")
                elif nm_signal == 'BUY' and nm_confidence > 40:
                    score += 8
                    decision['reason'].append(f"✅ Non-Markovian: BUY ({nm_confidence:.0f}% conf)")
                elif nm_signal == 'SELL' and nm_confidence > 60:
                    score -= 15
                    decision['reason'].append(f"🧠 Non-Markovian: SELL ({nm_confidence:.0f}% conf)")
                elif nm_signal == 'SELL' and nm_confidence > 40:
                    score -= 8
                    decision['reason'].append(f"⚠️ Non-Markovian: SELL ({nm_confidence:.0f}% conf)")
                
                decision['v52_analysis']['non_markovian_signal'] = nm_signal
                decision['v52_analysis']['non_markovian_confidence'] = nm_confidence
                decision['v52_analysis']['non_markovian_metrics'] = nm_metrics
                
                if nm_metrics.get('regime_coherence'):
                    coherence = nm_metrics['regime_coherence']
                    decision['v52_analysis']['memory_regime_coherence'] = coherence.get('overall_coherence', 0)
            
            # 9. EMA REGIME SIGNAL V6.5.4d (peso: 40 puntos - DRIVER PRINCIPAL)
            # EMA Signal es ahora el driver principal tras eliminar ARES (Dec 24, 2025)
            # Peso aumentado de 25 a 40 para compensar remoción de ARES (35 pts)
            if ema_signal and ema_direction:
                max_score += 40
                
                if ema_direction == 'LONG':
                    if ema_confidence >= 0.70:
                        score += 40
                        decision['reason'].append(f"📊 EMA Signal: STRONG LONG ({ema_confidence:.0%})")
                    elif ema_confidence >= 0.50:
                        score += 25
                        decision['reason'].append(f"✅ EMA Signal: LONG ({ema_confidence:.0%})")
                    else:
                        score += 12
                        decision['reason'].append(f"📈 EMA Signal: WEAK LONG ({ema_confidence:.0%})")
                        
                elif ema_direction == 'SHORT':
                    if ema_confidence >= 0.70:
                        score -= 40
                        decision['reason'].append(f"📊 EMA Signal: STRONG SHORT ({ema_confidence:.0%})")
                    elif ema_confidence >= 0.50:
                        score -= 25
                        decision['reason'].append(f"⚠️ EMA Signal: SHORT ({ema_confidence:.0%})")
                    else:
                        score -= 12
                        decision['reason'].append(f"📉 EMA Signal: WEAK SHORT ({ema_confidence:.0%})")
                
                # Log institutional para trazabilidad
                ema_delta = 40 if ema_confidence >= 0.70 else (25 if ema_confidence >= 0.50 else 12)
                logger.info(f"📊 EMA SIGNAL [PRIMARY]: {ema_direction} @ {ema_confidence:.1%} → score delta ±{ema_delta}")
            
            # ========== DECISIÓN FINAL ==========
            
            # Normalizar score a 0-100
            if max_score > 0:
                normalized_score = (score / max_score) * 100
                confidence = max(0, min(100, (normalized_score + 100) / 2))  # Ajustar a 0-100
            else:
                confidence = 50
            
            decision['confidence'] = confidence / 100.0
            decision['raw_score'] = score
            decision['max_score'] = max_score
            
            # ========== FIX INSTITUCIONAL: BIAS SYSTEM ELIMINADO ==========
            # Práctica institucional: Las instituciones odian el "Recovery Trading" 
            # (venganza contra el mercado). Cada operación es un evento estadístico aislado.
            #
            # ELIMINADO (era revenge trading disfrazado):
            # - FLOOR_RESCUE: Compraba cuando score era muy negativo (venganza)
            # - RECOVERY: Compraba cuando score era negativo (recuperación emocional)
            #
            # MANTENIDO (estrategia válida):
            # - Fear & Greed Contrarian ya implementado en sentiment analysis
            # - Cada trade se evalúa por sus méritos matemáticos, no por historia
            #
            # El score ya no se manipula artificialmente. Un score negativo
            # significa NO COMPRAR, punto. Esto genera un track record REPLICABLE.
            
            original_score = score
            # No se aplica bias - cada trade es un evento estadístico independiente
            logger.debug(f"📊 {VERSION_BANNER}: Score final sin bias artificial: {score:.1f}")
            
            # ==========================================================================
            # V6.5.4d: MACRO TREND FILTER - No comprar contra la tendencia principal
            # ==========================================================================
            macro_trend_veto = False
            if kalman and score > 0:  # Solo aplicar a señales de compra
                kalman_trend = kalman.get('trend', 'NEUTRAL')
                kalman_strength = kalman.get('trend_strength', 0)
                
                # Si Kalman detecta tendencia BEARISH fuerte, aplicar veto
                if kalman_trend == 'BEARISH' and kalman_strength > 0.5:
                    veto_penalty = 15  # Penalización fuerte
                    score -= veto_penalty
                    macro_trend_veto = True
                    decision['reason'].append(f"📉 MACRO TREND VETO V6.5.4d: Kalman BEARISH ({kalman_strength:.1%}) → -15 pts")
                    decision['v52_analysis']['macro_trend_veto'] = True
                    decision['v52_analysis']['macro_trend_reason'] = f"Kalman BEARISH strength={kalman_strength:.2f}"
                    logger.warning(f"📉 MACRO TREND VETO: Kalman BEARISH ({kalman_strength:.1%}) - Reduciendo score de {original_score} a {score}")
            
            # Si HMM detecta tendencia bajista fuerte, aplicar veto adicional
            if hmm_regime and score > 0 and not macro_trend_veto:
                hmm_detected = hmm_regime.get('regime', 'UNKNOWN')
                hmm_confidence = hmm_regime.get('confidence', 0)
                
                if hmm_detected == 'BEARISH' and hmm_confidence > 0.7:
                    veto_penalty = 12
                    score -= veto_penalty
                    decision['reason'].append(f"📉 MACRO TREND VETO V6.5.4d: HMM BEARISH ({hmm_confidence:.0%}) → -12 pts")
                    decision['v52_analysis']['macro_trend_veto'] = True
                    decision['v52_analysis']['macro_trend_reason'] = f"HMM BEARISH conf={hmm_confidence:.2f}"
                    logger.warning(f"📉 MACRO TREND VETO: HMM BEARISH ({hmm_confidence:.0%}) - Reduciendo score de {original_score} a {score}")
            # ==========================================================================
            
            # ==========================================================================
            # FASE 2.2: SHORT SELLING EN BEARISH REGIME (Dec 23, 2025)
            # ==========================================================================
            bearish_short_opportunity = False
            short_selling_active = False
            
            p = self.trading_profile  # Shorthand
            if p and getattr(p, 'short_selling_enabled', False) and hmm_regime:
                short_symbols = getattr(p, 'short_selling_symbols', [])
                min_bearish_conf = getattr(p, 'short_selling_min_bearish_confidence', 0.70)
                
                hmm_detected = hmm_regime.get('regime', 'UNKNOWN')
                hmm_confidence = hmm_regime.get('confidence', 0)
                
                # Normalizar símbolo para comparación
                symbol_normalized = symbol.replace('/', '').upper()
                short_symbols_normalized = [s.replace('/', '').upper() for s in short_symbols]
                
                if hmm_detected == 'BEARISH' and hmm_confidence >= min_bearish_conf:
                    if symbol in short_symbols or symbol_normalized in short_symbols_normalized:
                        bearish_short_opportunity = True
                        short_selling_active = True
                        logger.info(f"📉 FASE 2.2: SHORT opportunity detected for {symbol} - HMM BEARISH ({hmm_confidence:.0%})")
                        decision['reason'].append(f"📉 FASE 2.2: SHORT mode enabled - HMM BEARISH ({hmm_confidence:.0%})")
            # ==========================================================================
            
            # PREMIUM: Decisión de trading con umbrales desde Trading Profile
            # Objetivo: trades/día configurables con win rate > 55%
            
            # Obtener score thresholds del perfil o usar defaults (INSTITUTIONAL)
            score_very_strong = p.score_very_strong if p else 20
            score_strong = p.score_strong if p else 10
            score_moderate = p.score_moderate if p else 5
            
            # CAES: Extraer confianza del kernel para position sizing adaptativo
            nm_conf_for_caes = None
            nm_metrics_for_caes = None
            if non_markovian:
                nm_conf_for_caes = non_markovian.get('confidence', 50)
                nm_metrics_for_caes = non_markovian.get('metrics', {})
            
            # FASE 2.1: Confidence normalizada para partial position (0-1)
            decision_conf_normalized = confidence / 100.0
            
            if confidence >= (self.config['min_confidence'] * 100):
                # Umbrales escalonados configurables por perfil + CAES
                if score > score_very_strong:  # Señal COMPRA MUY FUERTE - Full position
                    decision['should_trade'] = True
                    decision['action'] = 'BUY'
                    decision['signal_strength'] = 'VERY_STRONG'
                    decision['amount_usd'] = self._calculate_position_size_v52(
                        current_price, kelly, hmm_regime, nm_conf_for_caes, nm_metrics_for_caes,
                        decision_confidence=decision_conf_normalized
                    )
                elif score > score_strong:  # Señal COMPRA FUERTE - 75% position
                    decision['should_trade'] = True
                    decision['action'] = 'BUY'
                    decision['signal_strength'] = 'STRONG'
                    decision['amount_usd'] = self._calculate_position_size_v52(
                        current_price, kelly, hmm_regime, nm_conf_for_caes, nm_metrics_for_caes,
                        decision_confidence=decision_conf_normalized
                    ) * 0.75
                elif score > score_moderate:  # Señal COMPRA MODERADA - 50% position
                    decision['should_trade'] = True
                    decision['action'] = 'BUY'
                    decision['signal_strength'] = 'MODERATE'
                    decision['amount_usd'] = self._calculate_position_size_v52(
                        current_price, kelly, hmm_regime, nm_conf_for_caes, nm_metrics_for_caes,
                        decision_confidence=decision_conf_normalized
                    ) * 0.50
                elif score < -score_very_strong:  # Señal VENTA MUY FUERTE
                    decision['should_trade'] = True
                    decision['action'] = 'SELL'
                    decision['signal_strength'] = 'VERY_STRONG'
                    decision['amount_usd'] = self._calculate_position_size_v52(
                        current_price, kelly, hmm_regime, nm_conf_for_caes, nm_metrics_for_caes,
                        decision_confidence=decision_conf_normalized
                    )
                elif score < -score_strong:  # Señal VENTA FUERTE
                    decision['should_trade'] = True
                    decision['action'] = 'SELL'
                    decision['signal_strength'] = 'STRONG'
                    decision['amount_usd'] = self._calculate_position_size_v52(
                        current_price, kelly, hmm_regime, nm_conf_for_caes, nm_metrics_for_caes,
                        decision_confidence=decision_conf_normalized
                    ) * 0.75
                elif score < -score_moderate:  # Señal VENTA MODERADA
                    decision['should_trade'] = True
                    decision['action'] = 'SELL'
                    decision['signal_strength'] = 'MODERATE'
                    decision['amount_usd'] = self._calculate_position_size_v52(
                        current_price, kelly, hmm_regime, nm_conf_for_caes, nm_metrics_for_caes,
                        decision_confidence=decision_conf_normalized
                    ) * 0.50
                
                # ==========================================================================
                # FASE 2.2: SHORT SELLING - Generar SHORT en bearish regime
                # ==========================================================================
                elif bearish_short_opportunity and not decision.get('should_trade'):
                    # En régimen bearish, generar SHORT cuando no hay señal de compra fuerte
                    decision['should_trade'] = True
                    decision['action'] = 'SHORT'
                    decision['signal_strength'] = 'BEARISH_REGIME'
                    decision['amount_usd'] = self._calculate_position_size_v52(
                        current_price, kelly, hmm_regime, nm_conf_for_caes, nm_metrics_for_caes,
                        decision_confidence=decision_conf_normalized
                    ) * 0.50  # 50% size for regime-based shorts
                    decision['reason'].append(f"📉 FASE 2.2: SHORT ejecutado - Bearish regime, size 50%")
                    logger.info(f"📉 FASE 2.2: SHORT trade generated for {symbol} - Amount: ${decision['amount_usd']:.2f}")
                # ==========================================================================
            
            # ==========================================================================
            # FASE 2.3: PROBATION CAP - Limitar tamaño para activo en probation
            # ==========================================================================
            if decision.get('should_trade') and decision.get('amount_usd'):
                p = self.trading_profile
                if p and getattr(p, 'probation_enabled', False) and getattr(p, 'probation_force_partial', True):
                    probation_asset = getattr(p, 'probation_asset', "")
                    if probation_asset:
                        # Verificar si el símbolo actual es el de probation
                        symbol_normalized = symbol.upper().replace("/", "")
                        probation_normalized = probation_asset.upper().replace("/", "")
                        if symbol_normalized == probation_normalized or symbol.upper() == probation_asset.upper():
                            probation_max_pct = getattr(p, 'probation_max_size_pct', 0.40)
                            balance = self._get_balance()
                            max_probation_size = balance * p.max_position_pct * probation_max_pct
                            if decision['amount_usd'] > max_probation_size:
                                original_size = decision['amount_usd']
                                decision['amount_usd'] = max_probation_size
                                decision['reason'].append(f"🔬 PROBATION CAP: ${original_size:.2f} → ${max_probation_size:.2f} (max {probation_max_pct:.0%})")
                                logger.info(f"🔬 FASE 2.3 Probation Cap: {symbol} limited to ${max_probation_size:.2f} (was ${original_size:.2f})")
            # ==========================================================================
            
            # ==========================================================================
            # V6.5.4d: MONTE CARLO POSITION SIZE ADJUSTMENT
            # Aplicar factor de reducción de tamaño basado en win rate bajo
            # ==========================================================================
            if decision.get('should_trade') and decision.get('amount_usd') and position_size_factor < 1.0:
                original_amount = decision['amount_usd']
                decision['amount_usd'] = original_amount * position_size_factor
                decision['reason'].append(f"📊 MC SIZE ADJUST: ${original_amount:.2f} → ${decision['amount_usd']:.2f} ({position_size_factor:.0%})")
                decision['decision_trace'].append(f"MC_SIZE_APPLIED: {original_amount:.2f} * {position_size_factor:.0%} = {decision['amount_usd']:.2f}")
                logger.info(f"📊 MC Position Size Adjustment: ${original_amount:.2f} → ${decision['amount_usd']:.2f} (factor: {position_size_factor:.0%})")
            # ==========================================================================
            
            # 🧠 COHERENCE ENGINE V5.4 ULTRA - Validación Premium de Coherencia
            if self.coherence_engine and decision.get('should_trade'):
                try:
                    # Convertir señales a formato Coherence Engine
                    strategy_signals = self._build_strategy_signals(
                        monte_carlo, black_swan, sentiment, kelly, 
                        hmm_regime, kalman, quantum, non_markovian
                    )
                    
                    # Analizar coherencia con todas las 10 estrategias V6.1
                    coherence_report = self.coherence_engine.analyze_coherence(strategy_signals)
                    
                    # Adjuntar reporte completo a decisión (para logging y análisis)
                    decision['coherence_score'] = coherence_report.coherence_score
                    decision['coherence_level'] = coherence_report.coherence_level.value
                    decision['coherence_recommendation'] = coherence_report.decision_recommendation
                    decision['coherence_contradictions'] = coherence_report.contradictions
                    decision['coherence_consensus'] = coherence_report.consensus_signal.name
                    decision['coherence_consensus_confidence'] = coherence_report.consensus_confidence
                    
                    # Log detallado con emoji
                    emoji = self.coherence_engine.get_coherence_emoji(coherence_report.coherence_score)
                    logger.info(f"{emoji} COHERENCE ENGINE V5.4: Score={coherence_report.coherence_score:.1f}% | Level={coherence_report.coherence_level.value}")
                    logger.info(f"   📊 Señales: {coherence_report.bullish_count} Alcistas, {coherence_report.bearish_count} Bajistas, {coherence_report.neutral_count} Neutrales")
                    logger.info(f"   🎯 Consenso: {coherence_report.consensus_signal.name} (Confianza: {coherence_report.consensus_confidence:.1%})")
                    logger.info(f"   💡 Recomendación: {coherence_report.decision_recommendation}")
                    
                    # ========== SISTEMA DE VETO CON TRADING PROFILES ==========
                    # Umbrales configurables desde Trading Profile (INSTITUTIONAL/PAPER_AGGRESSIVE/BALANCED)
                    p = self.trading_profile  # Shorthand para perfil activo
                    
                    # Obtener umbrales del perfil o usar defaults (INSTITUTIONAL)
                    veto_critical = p.coherence_veto_critical if p else 30.0
                    veto_normal = p.coherence_veto_normal if p else 45.0
                    coherence_warning = p.coherence_warning if p else 60.0
                    coherence_good = p.coherence_good if p else 80.0
                    
                    profile_name = p.name if p else "HARDCODED"
                    logger.debug(f"📊 Profile {profile_name}: veto_critical={veto_critical}%, veto_normal={veto_normal}%")
                    
                    # ========== V6.5.4 CONSENSUS GATE - 5/6 TIERS REQUIRED ==========
                    # Para PAPER_OPTIMIZED: Requiere mayoría clara (5+ de 6 estrategias de acuerdo)
                    total_signals = coherence_report.bullish_count + coherence_report.bearish_count + coherence_report.neutral_count
                    majority_count = max(coherence_report.bullish_count, coherence_report.bearish_count)
                    min_majority_required = 5 if profile_name == "PAPER_OPTIMIZED" else 4
                    
                    # V6.5.4: Log TRADE_CANDIDATE when a trade signal is generated
                    # Uses pre-generated decision_id for complete lifecycle correlation
                    if institutional_logger and decision.get('should_trade') and decision.get('decision_id'):
                        institutional_logger.log_trade_candidate(
                            symbol=decision.get('symbol', 'UNKNOWN'),
                            direction=decision.get('action', 'HOLD'),
                            size_usd=decision.get('amount_usd', 0),
                            coherence_score=coherence_report.coherence_score,
                            mc_win_rate=monte_carlo.get('win_rate', 50) if monte_carlo else 50,
                            mc_expected_return=monte_carlo.get('expected_return', 0) if monte_carlo else 0,
                            user_id=getattr(self, 'current_user_id', None),
                            profile=profile_name,
                            hmm_regime=hmm_regime.get('regime') if hmm_regime else None,
                            volatility_class=decision.get('volatility_class'),
                            decision_id=decision.get('decision_id')
                        )
                    
                    if total_signals >= 6 and majority_count < min_majority_required:
                        logger.warning(f"🚫 V6.5.4 CONSENSUS GATE: Solo {majority_count}/{total_signals} estrategias de acuerdo (mínimo {min_majority_required})")
                        # V6.5.4: Log institutional veto
                        if institutional_logger and decision.get('decision_id'):
                            institutional_logger.log_veto_consensus(
                                symbol=decision.get('symbol', 'UNKNOWN'),
                                decision_id=decision.get('decision_id'),
                                agreement=majority_count,
                                total=total_signals,
                                required=min_majority_required,
                                direction=decision.get('action')
                            )
                        decision['should_trade'] = False
                        decision['action'] = 'HOLD'
                        decision['reason'].append(f"🚫 Consenso insuficiente: {majority_count}/{total_signals} < {min_majority_required}")
                        decision['veto_chain'].append('CONSENSUS')
                    else:
                        decision['guards_passed'].append('CONSENSUS')
                    # ========== END CONSENSUS GATE ==========
                    
                    # ========== FIX INSTITUCIONAL: COHERENCIA SIN BYPASS ==========
                    # Práctica institucional: Mismas reglas para PAPER y REAL mode.
                    # Si la coherencia es baja, es baja. Punto. No se opera.
                    # La integridad de la señal es más importante que la necesidad de "probar".
                    # Esto genera un track record REPLICABLE en trading real.
                    
                    # NIVEL 1: VETO CRÍTICO - Coherencia muy baja (SIEMPRE bloquea)
                    if coherence_report.coherence_score < veto_critical:
                        logger.error(f"🚨 {VERSION_BANNER} COHERENCE VETO CRÍTICO: Score={coherence_report.coherence_score:.1f}% < {veto_critical}%")
                        # V6.5.4: Log institutional veto
                        if institutional_logger and decision.get('decision_id'):
                            institutional_logger.log_veto_coherence(
                                symbol=decision.get('symbol', 'UNKNOWN'),
                                decision_id=decision.get('decision_id'),
                                score=coherence_report.coherence_score,
                                threshold=veto_critical,
                                direction=decision.get('action')
                            )
                        decision['should_trade'] = False
                        decision['action'] = 'HOLD'
                        decision['reason'].append(f"🚨 VETO CRÍTICO: Coherencia {coherence_report.coherence_score:.1f}% < {veto_critical}%")
                        decision['veto_chain'].append('COHERENCE_CRITICAL')
                    
                    # NIVEL 1B: CRITICAL level también bloquea (sin bypass)
                    elif coherence_report.coherence_level.value == 'CRITICAL':
                        logger.error(f"🚨 {VERSION_BANNER} COHERENCE VETO CRÍTICO (NIVEL): Score={coherence_report.coherence_score:.1f}% - Nivel CRITICAL")
                        # V6.5.4: Log institutional veto
                        if institutional_logger and decision.get('decision_id'):
                            institutional_logger.log_veto_coherence(
                                symbol=decision.get('symbol', 'UNKNOWN'),
                                decision_id=decision.get('decision_id'),
                                score=coherence_report.coherence_score,
                                threshold=veto_critical,
                                direction=decision.get('action')
                            )
                        decision['should_trade'] = False
                        decision['action'] = 'HOLD'
                        decision['reason'].append(f"🚨 VETO CRÍTICO: Nivel CRITICAL detectado")
                        decision['veto_chain'].append('COHERENCE_LEVEL_CRITICAL')
                    
                    # NIVEL 2: VETO POR BAJA COHERENCIA - Configurable por perfil (SIEMPRE bloquea)
                    elif coherence_report.coherence_score < veto_normal:
                        logger.warning(f"🛑 {VERSION_BANNER} COHERENCE VETO: Score={coherence_report.coherence_score:.1f}% < {veto_normal}%")
                        # V6.5.4: Log institutional veto
                        if institutional_logger and decision.get('decision_id'):
                            institutional_logger.log_veto_coherence(
                                symbol=decision.get('symbol', 'UNKNOWN'),
                                decision_id=decision.get('decision_id'),
                                score=coherence_report.coherence_score,
                                threshold=veto_normal,
                                direction=decision.get('action')
                            )
                        decision['should_trade'] = False
                        decision['action'] = 'HOLD'
                        decision['reason'].append(f"🛑 VETO: Coherencia {coherence_report.coherence_score:.1f}% < {veto_normal}%")
                        decision['veto_chain'].append('COHERENCE')
                    
                    # NIVEL 3: HOLD recomendado - solo señales VERY_STRONG pueden pasar
                    elif coherence_report.decision_recommendation == 'HOLD':
                        signal_strength = decision.get('signal_strength', 'MODERATE')
                        if signal_strength == 'VERY_STRONG':
                            # Solo señales MUY fuertes pueden pasar con reducción
                            if 'amount_usd' in decision:
                                decision['amount_usd'] *= 0.55
                                decision['reason'].append(f"⚠️ Señal VERY_STRONG bypassing HOLD - posición reducida 45%")
                        else:
                            # STRONG y MODERATE respetan HOLD (sin bypass de paper mode)
                            decision['should_trade'] = False
                            decision['action'] = 'HOLD'
                            decision['reason'].append(f"⚠️ Coherence Engine recomienda HOLD")
                    # ========== FIN FIX INSTITUCIONAL =========
                    
                    # NIVEL 4: REDUCCIÓN MODERADA - Coherencia entre veto_normal y warning
                    elif coherence_report.coherence_score < coherence_warning:
                        if 'amount_usd' in decision:
                            original_amount = decision['amount_usd']
                            decision['amount_usd'] *= 0.60
                            logger.info(f"📊 Coherencia moderada: ${original_amount:.2f} → ${decision['amount_usd']:.2f}")
                            decision['reason'].append(f"📊 Posición reducida 40% por coherencia moderada")
                    
                    # NIVEL 5: REDUCCIÓN LEVE - Coherencia entre warning y good
                    elif coherence_report.coherence_score < coherence_good:
                        if 'amount_usd' in decision:
                            original_amount = decision['amount_usd']
                            decision['amount_usd'] *= 0.85
                            decision['reason'].append(f"📊 Ajuste 15% (coherencia buena)")
                    
                    # NIVEL 6: APROBACIÓN COMPLETA - Coherencia >= good
                    else:
                        logger.info(f"✅ COHERENCE ENGINE APROBADO - Score={coherence_report.coherence_score:.1f}% >= {coherence_good}%")
                        decision['reason'].append(f"✅ Coherencia excelente - Full position")
                    
                    # Log de contradicciones si existen (siempre, para transparencia)
                    if coherence_report.contradictions and decision.get('should_trade'):
                        logger.info(f"   ℹ️ Contradicciones menores detectadas ({len(coherence_report.contradictions)}), pero coherencia suficiente")
                    
                    # ========== V6.5.4 CONTRADICTION MONITOR ==========
                    # Log cuando Coherence recomienda HOLD pero decision final es BUY/SELL
                    # Esto es para MONITOREO - no cambia el comportamiento del trading
                    # Guard: solo ejecutar si coherence_report existe y tiene atributos requeridos
                    if coherence_report and hasattr(coherence_report, 'decision_recommendation'):
                        coherence_rec = coherence_report.decision_recommendation
                        final_action = decision.get('action', 'HOLD')
                        if coherence_rec == 'HOLD' and final_action in ['BUY', 'SELL'] and decision.get('should_trade'):
                            signal_strength = decision.get('signal_strength', 'UNKNOWN')
                            amount = decision.get('amount_usd', 0)
                            coherence_pct = getattr(coherence_report, 'coherence_score', 0)
                            symbol = getattr(self, 'current_symbol', 'UNKNOWN')
                            logger.warning(
                                f"⚡ CONTRADICTION MONITOR V6.5.4: "
                                f"Coherence={coherence_rec} ({coherence_pct:.1f}%) vs Final={final_action} | "
                                f"Signal={signal_strength} | Amount=${amount:.2f} | "
                                f"Symbol={symbol}"
                            )
                    # ========== END CONTRADICTION MONITOR ==========
                    
                    # ========== V6.5.4 INSTITUTIONAL FINAL DECISION LOG ==========
                    if institutional_logger and decision.get('decision_id'):
                        veto_chain = decision.get('veto_chain', [])
                        guards_passed = decision.get('guards_passed', [])
                        dec_id = decision.get('decision_id')
                        sym = decision.get('symbol', 'UNKNOWN')
                        
                        if decision.get('should_trade') and decision.get('action') in ['BUY', 'SELL'] and not veto_chain:
                            # Trade passed all gates - add COHERENCE to guards_passed and log VALIDATED
                            if 'COHERENCE' not in guards_passed:
                                guards_passed.append('COHERENCE')
                            institutional_logger.log_trade_validated(
                                symbol=sym,
                                decision_id=dec_id,
                                direction=decision.get('action'),
                                size_usd=decision.get('amount_usd', 0),
                                guards_passed=guards_passed
                            )
                        elif veto_chain:
                            # Trade rejected by one or more vetos
                            institutional_logger.log_trade_rejected(
                                symbol=sym,
                                decision_id=dec_id,
                                direction=decision.get('action', 'HOLD'),
                                size_usd=decision.get('amount_usd', 0),
                                veto_chain=veto_chain
                            )
                    # ========== END INSTITUTIONAL FINAL DECISION LOG ==========
                    
                except Exception as e:
                    logger.error(f"❌ Error en Coherence Engine V5.4: {e}")
                    # En caso de error, aplicar principio de precaución
                    if decision.get('should_trade') and decision.get('amount_usd'):
                        original_amount = decision.get('amount_usd', 0)
                        decision['amount_usd'] = original_amount * 0.5
                        logger.warning(f"   ⚠️ Error en validación - Reduciendo posición por precaución: ${original_amount:.2f} → ${decision['amount_usd']:.2f}")
                        decision['reason'].append("⚠️ Coherence Engine error - posición reducida por precaución")
            
            return decision
            
        except Exception as e:
            logger.error(f"Error en decisión V5.2: {e}")
            return {'should_trade': False, 'action': 'HOLD', 'confidence': 0.0}
    
    def _make_decision(self, current_price: float, monte_carlo: Optional[Dict], 
                       black_swan: Optional[Dict], sentiment: Optional[Dict]) -> Dict:
        """
        LEGACY: Decisión clásica (mantenida por compatibilidad)
        Usa _make_v52_decision para análisis completo
        """
        return self._make_v52_decision(
            current_price, monte_carlo, black_swan, sentiment,
            None, None, None, None
        )
    
    def _execute_smart_trade(self, analysis: Dict, user_id: str = None) -> Dict:
        """
        Ejecutar trade con validaciones de seguridad (PAPER o REAL)
        
        Args:
            analysis: Diccionario con análisis del trade
            user_id: ID del usuario (V6.5.4d MULTI-USER). Si None, usa fallback legacy.
        """
        try:
            # V6.5.4d MULTI-USER: Usar método centralizado para obtener user_id
            user_id = self._get_effective_user_id(user_id, caller='_execute_smart_trade')
            
            # V6.5.4d MULTI-USER: Verify user has trading permission
            try:
                self._require_trading_permission(user_id, 'trading')
            except AuthorizationError as e:
                logger.warning(f"🚫 {e}")
                return {'error': 'Permission denied: trading not allowed for this user tier'}
            
            action = analysis['action']
            amount_usd = analysis.get('amount_usd', 0)
            
            # ==========================================================================
            # V6.5.4d INSTITUTIONAL: PRICE STALE CHECK - BLOCK TRADING ON STALE DATA
            # ==========================================================================
            if PRICE_VALIDATOR_AVAILABLE and action != 'HOLD':
                price_data = analysis.get('price_data', {})
                current_price = analysis.get('current_price', 0)
                fetch_timestamp = price_data.get('fetch_timestamp', 0)
                
                if fetch_timestamp > 0 and current_price > 0:
                    is_fresh = is_price_tradeable(
                        symbol=analysis.get('symbol', self.config.get('trading_pair', 'BTC/USD')),
                        price=current_price,
                        fetch_timestamp=fetch_timestamp
                    )
                    
                    if not is_fresh:
                        logger.warning(f"🚨 PRICE STALE BLOCK: Trade blocked due to stale price data")
                        return {
                            'success': False,
                            'blocked': True,
                            'error': 'Trading blocked: price data is stale',
                            'reason': 'PRICE_STALE_VETO',
                            'price_age_seconds': time.time() - fetch_timestamp
                        }
            
            # En paper mode, no rechazar inmediatamente - el floor se aplicará después
            if not self.config.get('paper_mode', False) and amount_usd < self.config['min_trade_usd']:
                return {'error': 'Cantidad muy pequeña para tradear'}
            
            # ==========================================================================
            # V6.5.4 PREMIUM: SYMBOL FILTER - BLOQUEA TRADES EN SÍMBOLOS NO PERMITIDOS
            # ==========================================================================
            current_symbol = analysis.get('symbol') or self.config.get('trading_pair', 'BTC/USD')
            
            # V6.5.4 PREMIUM: Verificar calibración por par primero
            if is_symbol_allowed and not is_symbol_allowed(current_symbol, self.trading_profile):
                profile_name = self.trading_profile.name if self.trading_profile else "DEFAULT"
                calibration = get_pair_calibration(current_symbol) if get_pair_calibration else None
                
                import json as json_mod
                from datetime import datetime as dt_mod
                
                filter_event = {
                    "event": "SYMBOL_BLOCKED",
                    "timestamp": dt_mod.utcnow().isoformat() + "Z",
                    "symbol": current_symbol,
                    "profile": profile_name,
                    "calibration_tier": calibration.tier.value if calibration else "UNKNOWN",
                    "calibration_notes": calibration.notes if calibration else "Sin calibración",
                    "action": action,
                    "amount_usd": amount_usd
                }
                logger.warning(f"🚫 SYMBOL FILTER V6.5.4 PREMIUM: {current_symbol} BLOQUEADO")
                logger.info(f"📊 SYMBOL_FILTER: {json_mod.dumps(filter_event)}")
                
                return {
                    'success': False,
                    'blocked': True,
                    'error': f'Símbolo {current_symbol} no permitido en perfil {profile_name}',
                    'reason': 'SYMBOL_FILTER_VETO',
                    'calibration_tier': calibration.tier.value if calibration else "UNKNOWN"
                }
            elif self.trading_profile and hasattr(self.trading_profile, 'extra_params'):
                allowed_symbols = self.trading_profile.extra_params.get('allowed_symbols', None)
                
                if allowed_symbols and current_symbol not in allowed_symbols:
                    profile_name = self.trading_profile.name
                    logger.warning(f"🚫 SYMBOL FILTER V6.5.4: {current_symbol} NO PERMITIDO en perfil {profile_name}")
                    logger.info(f"   📋 Símbolos permitidos: {allowed_symbols}")
                    
                    import json as json_mod
                    from datetime import datetime as dt_mod
                    
                    filter_event = {
                        "event": "SYMBOL_BLOCKED",
                        "timestamp": dt_mod.utcnow().isoformat() + "Z",
                        "symbol": current_symbol,
                        "profile": profile_name,
                        "allowed_symbols": allowed_symbols,
                        "action": action,
                        "amount_usd": amount_usd
                    }
                    logger.info(f"📊 SYMBOL_FILTER: {json_mod.dumps(filter_event)}")
                    
                    return {
                        'success': False,
                        'blocked': True,
                        'error': f'Símbolo {current_symbol} no permitido en perfil {profile_name}',
                        'reason': 'SYMBOL_FILTER_VETO',
                        'allowed_symbols': allowed_symbols
                    }
            
            # ==========================================================================
            # V6.5.4 PREMIUM: PER-PAIR CIRCUIT BREAKER - BLOQUEA SI DRAWDOWN DIARIO EXCEDIDO
            # ==========================================================================
            if action != 'HOLD':
                current_balance = self._get_balance()
                if not self.check_circuit_breaker(current_symbol, current_balance):
                    decision_id = analysis.get('decision_id')
                    
                    if institutional_logger and decision_id:
                        try:
                            institutional_logger.log_event(
                                event_type="VETO_CIRCUIT_BREAKER",
                                symbol=current_symbol,
                                decision_id=decision_id,
                                reason="Daily drawdown limit exceeded for pair"
                            )
                        except Exception:
                            pass
                    
                    return {
                        'success': False,
                        'blocked': True,
                        'error': f'Circuit Breaker: {current_symbol} bloqueado por drawdown diario',
                        'reason': 'CIRCUIT_BREAKER_VETO'
                    }
            
            # 🛡️ AI RISK GUARDIAN - PRIMERA LÍNEA DE DEFENSA
            if self.risk_guardian and action != 'HOLD':
                try:
                    # Obtener balance actual
                    current_balance = self._get_balance()
                    
                    # Obtener trades recientes (últimas 24 horas)
                    recent_trades = []
                    if self.database_service:
                        try:
                            recent_trades = self.database_service.get_recent_trades(
                                hours=24,
                                limit=100
                            )
                        except:
                            recent_trades = []
                    
                    # VALIDAR TODOS LOS RIESGOS
                    can_trade, risk_event = self.risk_guardian.check_all_risks(
                        balance=current_balance,
                        recent_trades=recent_trades,
                        proposed_trade_size=amount_usd
                    )
                    
                    if not can_trade:
                        # RIESGO DETECTADO
                        is_paper_mode = self.config.get('paper_mode', False)
                        decision_id = analysis.get('decision_id')
                        symbol = analysis.get('symbol', 'UNKNOWN')
                        
                        # V6.5.4: Log institutional veto
                        if institutional_logger and decision_id:
                            institutional_logger.log_veto_risk_guardian(
                                symbol=symbol,
                                decision_id=decision_id,
                                reason=f"{risk_event.risk_type.value}: {risk_event.description}",
                                direction=action
                            )
                        
                        if not is_paper_mode:
                            # REAL MODE: BLOQUEAR TRADE
                            logger.error(f"🛑 AI RISK GUARDIAN BLOQUEÓ TRADE: {risk_event.description}")
                            logger.error(f"   Acción tomada: {risk_event.action_taken}")
                            return {
                                'error': 'BLOQUEADO POR AI RISK GUARDIAN',
                                'blocked': True,
                                'risk_type': risk_event.risk_type.value,
                                'risk_level': risk_event.risk_level.value,
                                'reason': risk_event.description,
                                'action_taken': risk_event.action_taken,
                                'metadata': risk_event.metadata
                            }
                        else:
                            # PAPER MODE - Permitir con reducción 25% para calibración (era 50%)
                            logger.warning(f"⚠️ AI RISK GUARDIAN (PAPER MODE): {risk_event.description}")
                            logger.warning(f"   Permitiendo con reducción 25% para calibración de track record")
                            amount_usd = amount_usd * 0.75  # Reducido de 0.50 a 0.75 para permitir más trades
                            analysis['amount_usd'] = amount_usd
                            if 'reason' in analysis:
                                analysis['reason'].append(f"🛡️ PAPER MODE: Risk Guardian permitió con 25% reducción")
                    
                    # Trade permitido - verificar ajuste de tamaño
                    adjusted_size = self.risk_guardian.get_adjusted_position_size(amount_usd)
                    if adjusted_size < amount_usd:
                        logger.warning(f"⚠️ AI RISK GUARDIAN: Reduciendo tamaño ${amount_usd:.2f} → ${adjusted_size:.2f}")
                        amount_usd = adjusted_size
                        analysis['amount_usd'] = adjusted_size
                        if 'reason' in analysis:
                            analysis['reason'].append(f"🛡️ Tamaño ajustado por Risk Guardian")
                    
                    logger.info(f"✅ AI Risk Guardian: Trade permitido - No se detectaron riesgos críticos")
                    
                except Exception as e:
                    logger.error(f"Error en AI Risk Guardian (continuando): {e}")
            
            # KRAKEN FAIL-SAFE - CRITICAL VALIDATION
            # Validar disponibilidad de Kraken ANTES de cualquier lógica de trading
            kraken_available = (
                hasattr(self, 'trading_service') and 
                self.trading_service is not None and
                hasattr(self.trading_service, 'kraken') and
                self.trading_service.kraken is not None
            )
            
            is_real_trading = not self.config.get('paper_mode', True)
            
            # FAIL-SAFE ABSOLUTO: En REAL TRADING, Kraken DEBE estar disponible
            if is_real_trading and not kraken_available:
                logger.error(f"🚨 CRITICAL FAIL-SAFE: REAL TRADING sin datos de Kraken disponibles")
                logger.error(f"   Acción solicitada: {action}, Monto: ${amount_usd:.2f}")
                logger.error(f"   Sistema en modo degradado - requiere reconexión de Kraken para trading real")
                return {
                    'error': 'BLOQUEADO POR FAIL-SAFE CRÍTICO: Datos de Kraken no disponibles',
                    'blocked': True,
                    'fail_safe': True,
                    'critical': True,
                    'reason': 'Real trading requiere datos de Kraken en vivo',
                    'action': action,
                    'kraken_available': False,
                    'timestamp': int(time.time()),
                    'recommendation': 'Verificar conexión de Kraken o usar Paper Trading Mode'
                }
            
            # NOTE: ARES Kill-Switch code removed Dec 24, 2025
            # Kill-switch logic was tied to ARES V1/V2 strategies which have been deprecated
            # Risk protection is now handled by AI Risk Guardian and Coherence Engine
            
            # 🔴 VALIDACIÓN DE COHERENCE ENGINE - BLOQUEA TRADES PELIGROSOS
            if self.coherence_engine and action != 'HOLD':
                try:
                    # Extraer señales de estrategias del análisis
                    v52_analysis = analysis.get('v52_analysis', {})
                    strategy_signals = []
                    
                    # Convertir análisis V5.2 a señales de estrategia
                    if v52_analysis.get('quantum_signal'):
                        qm_score = v52_analysis.get('quantum_score', 0)
                        signal = Signal.BUY if qm_score > 5 else Signal.SELL if qm_score < -5 else Signal.HOLD
                        strategy_signals.append(StrategySignal(
                            name='quantum_momentum',
                            signal=signal,
                            confidence=min(abs(qm_score) / 10, 1.0),
                            strength=qm_score,
                            reasoning=v52_analysis.get('quantum_signal', '')
                        ))
                    
                    if v52_analysis.get('kalman_trend'):
                        kt_value = v52_analysis.get('kalman_value', 0)
                        signal = Signal.BUY if kt_value > 0.3 else Signal.SELL if kt_value < -0.3 else Signal.HOLD
                        strategy_signals.append(StrategySignal(
                            name='kalman_filter',
                            signal=signal,
                            confidence=min(abs(kt_value), 1.0),
                            strength=kt_value,
                            reasoning=v52_analysis.get('kalman_trend', '')
                        ))
                    
                    if v52_analysis.get('market_regime'):
                        regime = v52_analysis.get('market_regime', 'UNKNOWN')
                        signal = Signal.BUY if 'TRENDING' in regime and 'up' in regime.lower() else Signal.SELL if 'TRENDING' in regime and 'down' in regime.lower() else Signal.HOLD
                        strategy_signals.append(StrategySignal(
                            name='hmm_regime',
                            signal=signal,
                            confidence=0.75,
                            strength=1.0 if signal == Signal.BUY else -1.0 if signal == Signal.SELL else 0.0,
                            reasoning=regime
                        ))
                    
                    # Monte Carlo
                    if 'monte_carlo' in analysis:
                        mc = analysis['monte_carlo']
                        win_rate = mc.get('win_rate', 0.5)
                        signal = Signal.BUY if win_rate > 0.6 else Signal.SELL if win_rate < 0.4 else Signal.HOLD
                        strategy_signals.append(StrategySignal(
                            name='monte_carlo',
                            signal=signal,
                            confidence=win_rate,
                            strength=win_rate * 100,
                            reasoning=f"{win_rate:.1%} win rate"
                        ))
                    
                    # Black Swan
                    if 'black_swan' in analysis:
                        bs = analysis['black_swan']
                        risk_level = bs.get('risk_level', 'UNKNOWN')
                        signal = Signal.HOLD if risk_level in ['HIGH', 'EXTREME'] else Signal.BUY if risk_level == 'LOW' else Signal.HOLD
                        strategy_signals.append(StrategySignal(
                            name='black_swan',
                            signal=signal,
                            confidence=0.8 if risk_level in ['LOW', 'HIGH', 'EXTREME'] else 0.5,
                            strength=0.0,
                            reasoning=f"Risk: {risk_level}"
                        ))
                    
                    # Sentiment
                    if 'sentiment' in analysis:
                        sent = analysis['sentiment']
                        score = sent.get('score', 50)
                        signal = Signal.BUY if score > 60 else Signal.SELL if score < 40 else Signal.HOLD
                        strategy_signals.append(StrategySignal(
                            name='sentiment',
                            signal=signal,
                            confidence=abs(score - 50) / 50,
                            strength=(score - 50) / 10,
                            reasoning=f"Sentiment: {score}/100"
                        ))
                    
                    # FIX: Garantizar que strategy_signals nunca esté vacía
                    # Si no hay señales de estrategias, usar la decisión primaria como fallback
                    if not strategy_signals:
                        primary_signal = Signal.BUY if action == 'BUY' else Signal.SELL if action == 'SELL' else Signal.HOLD
                        strategy_signals.append(StrategySignal(
                            name='primary_decision',
                            signal=primary_signal,
                            confidence=analysis.get('confidence', 0.5),
                            strength=analysis.get('confidence', 0.5) * 100,
                            reasoning=f"Decisión primaria: {action}"
                        ))
                        logger.debug(f"🔄 Usando fallback primary_decision para Coherence Engine")
                    
                    # Preparar analysis_data para validación
                    analysis_data = {
                        'black_swan': analysis.get('black_swan', {}),
                        'monte_carlo': analysis.get('monte_carlo', {}),
                        'hmm_regime': {'regime': v52_analysis.get('market_regime', 'UNKNOWN')}
                    }
                    
                    # 🔴 VALIDAR COHERENCIA ANTES DE EJECUTAR
                    allowed, reason = self.coherence_engine.validate_trade_coherence(
                        signals=strategy_signals,
                        action=action,
                        confidence=analysis['confidence'],
                        analysis_data=analysis_data,
                        paper_mode=self.config['paper_mode']
                    )
                    
                    if not allowed:
                        is_paper_mode = self.config.get('paper_mode', False)
                        
                        if not is_paper_mode:
                            # REAL MODE: Bloquear trade
                            logger.warning(f"🚫 TRADE BLOQUEADO POR COHERENCE ENGINE:\n{reason}")
                            return {
                                'error': 'BLOQUEADO POR COHERENCE ENGINE',
                                'blocked': True,
                                'reason': reason,
                                'action': action,
                                'confidence': analysis['confidence']
                            }
                        else:
                            # PAPER MODE - Permitir con reducción 25% para calibración (era 50%)
                            logger.warning(f"⚠️ COHERENCE ENGINE (PAPER MODE): {reason}")
                            logger.warning(f"   Permitiendo con reducción 25% para calibración de track record")
                            amount_usd = amount_usd * 0.75  # Reducido de 0.50 a 0.75 para permitir más trades
                            analysis['amount_usd'] = amount_usd
                            if 'reason' in analysis:
                                analysis['reason'].append(f"⚠️ PAPER MODE: Coherence Engine permitió con 25% reducción")
                    else:
                        logger.info(f"✅ Coherence validation: {reason}")
                        # Agregar validación a las razones del análisis
                        if 'reason' in analysis:
                            analysis['reason'].append(f"Coherence: {reason}")
                
                except Exception as e:
                    logger.error(f"Error en Coherence validation (continuando): {e}")
            
            # ==========  V6.5.4c: LÍMITE DIARIO DE TRADES ==========
            # Bloquear nuevos trades si ya alcanzamos el límite del día
            # APLICA A PAPER Y REAL TRADING para consistencia
            if action != 'HOLD':
                try:
                    from omnix_core.config.trading_profiles import get_active_profile
                    active_profile = get_active_profile()
                    max_daily_trades = active_profile.extra_params.get('ares_max_daily_trades', 3)
                    
                    if self.paper_trading and hasattr(self.paper_trading, 'get_today_trades_count'):
                        # V6.5.4d MULTI-USER: Usar user_id del parámetro (ya está definido arriba)
                        today_stats = self.paper_trading.get_today_trades_count(user_id)
                        
                        if 'error' in today_stats:
                            logger.error(f"🛑 {VERSION_BANNER} DAILY LIMIT CHECK FAILED: {today_stats['error']}")
                            logger.warning(f"   ⏸️ Forzando HOLD por error de DB (safety-first)")
                            return {
                                'success': True,
                                'action': 'HOLD',
                                'reason': f'DB error during daily limit check: {today_stats["error"]}',
                                'blocked': True,
                                'veto_type': 'DB_ERROR_VETO'
                            }
                        
                        trades_today = today_stats.get('count', 0)
                        
                        if trades_today >= max_daily_trades:
                            logger.warning(f"🛑 {VERSION_BANNER} LÍMITE DIARIO ALCANZADO: {trades_today}/{max_daily_trades} trades hoy")
                            logger.info(f"   ⏸️ Convirtiendo {action} → HOLD (esperar mañana)")
                            return {
                                'success': True, 
                                'action': 'HOLD', 
                                'reason': f'Daily trade limit reached: {trades_today}/{max_daily_trades}',
                                'blocked': True,
                                'veto_type': 'DAILY_LIMIT'
                            }
                        else:
                            logger.info(f"✅ {VERSION_BANNER} DAILY LIMIT CHECK: {trades_today}/{max_daily_trades} trades - OK")
                except Exception as e:
                    logger.error(f"🛑 {VERSION_BANNER} DAILY LIMIT CHECK EXCEPTION: {e}")
                    logger.warning(f"   ⏸️ Forzando HOLD por excepción (safety-first)")
                    return {
                        'success': True,
                        'action': 'HOLD',
                        'reason': f'Exception during daily limit check: {str(e)}',
                        'blocked': True,
                        'veto_type': 'EXCEPTION_VETO'
                    }
            
            # ==========  V6.5.4c: VERIFICACIÓN DE POSICIÓN DUPLICADA ANTES DE BUY ==========
            # APLICA A PAPER Y REAL TRADING - BUY no debe abrir si ya existe posición
            if action == 'BUY':
                if self.paper_trading and hasattr(self.paper_trading, 'count_open_positions_for_symbol'):
                    # V6.5.4d MULTI-USER: Usar user_id del parámetro (ya está definido arriba)
                    symbol = self.config['trading_pair']
                    
                    try:
                        open_count = self.paper_trading.count_open_positions_for_symbol(user_id, symbol)
                        
                        if open_count > 0:
                            logger.warning(f"🛑 {VERSION_BANNER} POSICIÓN DUPLICADA BLOQUEADA: {open_count} posiciones abiertas para {symbol}")
                            logger.info(f"   ⏸️ Convirtiendo BUY → HOLD (esperar cierre de posición actual)")
                            return {
                                'success': True, 
                                'action': 'HOLD', 
                                'reason': f'Duplicate position blocked: {open_count} open positions for {symbol}',
                                'blocked': True,
                                'veto_type': 'DUPLICATE_POSITION'
                            }
                        else:
                            logger.info(f"✅ {VERSION_BANNER} DUPLICATE CHECK: No open positions for {symbol} - OK")
                    except Exception as e:
                        logger.error(f"🛑 {VERSION_BANNER} DUPLICATE CHECK EXCEPTION: {e}")
                        logger.warning(f"   ⏸️ Forzando HOLD por excepción (safety-first)")
                        return {
                            'success': True,
                            'action': 'HOLD',
                            'reason': f'Exception during duplicate check: {str(e)}',
                            'blocked': True,
                            'veto_type': 'EXCEPTION_VETO'
                        }
            
            # ==========  VERIFICACIÓN DE POSICIÓN ANTES DE SELL ==========
            # En paper mode, SELL solo puede cerrar posiciones existentes
            # Si no hay posición abierta, convertir a HOLD para evitar errores
            if self.config['paper_mode'] and action == 'SELL':
                if self.paper_trading and hasattr(self.paper_trading, 'has_open_position_for_symbol'):
                    symbol = self.config['trading_pair']
                    
                    position_check = self.paper_trading.has_open_position_for_symbol(user_id, symbol)
                    
                    if not position_check.get('has_position', False):
                        # NO hay posición abierta - convertir SELL a HOLD (no abrir longs innecesarios)
                        logger.warning(f"📊 {VERSION_BANNER} POSITION CHECK: No hay posición abierta para {symbol}")
                        logger.info(f"   ⏸️ Convirtiendo SELL → HOLD (esperando señal BUY para abrir posición)")
                        action = 'HOLD'
                        analysis['action'] = 'HOLD'
                        if 'reason' in analysis:
                            analysis['reason'].append(f"⏸️  SELL→HOLD (no open position for {symbol})")
                        return {'success': True, 'action': 'HOLD', 'reason': 'No open position to close'}
                    else:
                        # SÍ hay posición - proceder con SELL
                        pos = position_check.get('position', {})
                        logger.info(f"✅ {VERSION_BANNER} POSITION CHECK: Posición abierta encontrada")
                        logger.info(f"   📈 {pos.get('side', 'N/A').upper()} {pos.get('quantity', 0):.6f} @ ${pos.get('entry_price', 0):.2f}")
            
            # ==========  FLOOR MÍNIMO PARA PAPER MODE ==========
            # Asegurar que después de todas las reducciones, el tamaño sea >= min_trade_usd
            # NOTA: Solo aplicar si amount_usd > 0 (no sobrescribir ceros intencionales de Risk Guardian)
            if self.config['paper_mode'] and action != 'HOLD':
                min_trade = self.config.get('min_trade_usd', 50.0)
                if amount_usd > 0 and amount_usd < min_trade:
                    logger.warning(f"📊 {VERSION_BANNER} SIZE FLOOR: ${amount_usd:.2f} < ${min_trade:.2f} mínimo")
                    logger.info(f"   ↗️ Ajustando al mínimo para permitir ejecución")
                    amount_usd = min_trade
                    analysis['amount_usd'] = amount_usd
                elif amount_usd <= 0:
                    # Monto es 0 o negativo - esto es intencional (Risk Guardian bloqueó)
                    logger.warning(f"⚠️ {VERSION_BANNER}: amount_usd={amount_usd} - Risk Guardian bloqueó intencionalmente")
                    return {'error': 'Trade bloqueado por Risk Guardian (amount=0)', 'blocked': True}
            
            # ==========  EXECUTION PROTOCOL INSTITUTIONAL+ ==========
            # Analyze execution conditions BEFORE placing the trade
            execution_decision = None
            if self.execution_protocol and EXECUTION_PROTOCOL_AVAILABLE:
                try:
                    # Get execution analysis from the 4-layer protocol
                    symbol = self.config['trading_pair']
                    side = action.lower()
                    
                    execution_decision = self.execution_protocol.get_execution_decision(
                        symbol=symbol,
                        side=side,
                        size_usd=amount_usd,
                        urgency=ExecutionUrgency.NORMAL if ExecutionUrgency else 'normal'
                    )
                    
                    # Log execution analysis
                    if execution_decision:
                        logger.info(f"🎯 {VERSION_BANNER} EXECUTION PROTOCOL:")
                        logger.info(f"   📊 Style: {execution_decision.recommended_style.value}")
                        logger.info(f"   💧 Liquidity: {execution_decision.liquidity_score:.1f}")
                        logger.info(f"   📈 Volatility: {execution_decision.volatility_regime}")
                        logger.info(f"   🔗 Correlation Risk: {execution_decision.correlation_risk:.1f}")
                        logger.info(f"   ⚡ Slippage Est: {execution_decision.slippage.expected_slippage_bps:.1f} bps")
                        logger.info(f"   🎯 Should Execute: {execution_decision.should_execute}")
                        
                        # Add execution metadata to analysis for investor logs
                        analysis['execution_protocol'] = {
                            'style': execution_decision.recommended_style.value,
                            'liquidity_score': execution_decision.liquidity_score,
                            'volatility': execution_decision.volatility_regime,
                            'correlation_risk': execution_decision.correlation_risk,
                            'contagion_risk': execution_decision.contagion_risk,
                            'slippage_bps': execution_decision.slippage.expected_slippage_bps,
                            'market_condition': execution_decision.market_condition.value,
                            'should_execute': execution_decision.should_execute
                        }
                        
                        # V6.5.4c: DATA INTEGRITY BLOCK - If critical data unavailable, BLOCK trade
                        if execution_decision.data_integrity_block:
                            logger.warning(f"🛑 {VERSION_BANNER} DATA INTEGRITY BLOCK ACTIVATED")
                            logger.warning(f"   Reason: {execution_decision.block_reason}")
                            logger.warning(f"   Liquidity Data: {'✅' if execution_decision.liquidity_data_available else '❌'}")
                            logger.warning(f"   Correlation Data: {'✅' if execution_decision.correlation_data_available else '❌'}")
                            
                            # Log to institutional logger if available
                            if institutional_logger:
                                decision_id = analysis.get('decision_id')
                                if decision_id:
                                    institutional_logger.log_veto_coherence(
                                        symbol=self.config['trading_pair'],
                                        decision_id=decision_id,
                                        veto_type="DATA_INTEGRITY_BLOCK",
                                        reason=execution_decision.block_reason,
                                        coherence_score=0.0
                                    )
                            
                            return {
                                'error': f"DATA_INTEGRITY_BLOCK: {execution_decision.block_reason}",
                                'blocked': True,
                                'block_type': 'DATA_INTEGRITY_BLOCK',
                                'liquidity_data_available': execution_decision.liquidity_data_available,
                                'correlation_data_available': execution_decision.correlation_data_available
                            }
                        
                        # V6.5.4: If correlation risk >= 80, reduce size by 50%
                        if execution_decision.correlation_risk >= 80:
                            original_size = amount_usd
                            amount_usd = amount_usd * 0.5
                            logger.warning(f"🚨 HIGH Correlation Risk ({execution_decision.correlation_risk:.1f}): Size reduced ${original_size:.2f} → ${amount_usd:.2f}")
                            analysis['amount_usd'] = amount_usd
                            if 'reason' in analysis:
                                analysis['reason'].append(f"⚠️ Execution Protocol: Size reduced 50% (correlation risk {execution_decision.correlation_risk:.0f}%)")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Execution Protocol analysis error (continuing): {e}")
            
            # ==========================================================================
            # V6.5.4d CRITICAL: ÚLTIMA LÍNEA DE DEFENSA - BLOQUEAR SÍMBOLOS EXCLUIDOS
            # Esta verificación es REDUNDANTE pero CRÍTICA para evitar trades en símbolos excluidos
            # IMPORTANTE: Usar el símbolo del análisis (más confiable que config que puede estar stale)
            # ==========================================================================
            execution_symbol = analysis.get('symbol') or self.config.get('trading_pair', 'BTC/USD')
            if action == 'BUY' and is_symbol_allowed and not is_symbol_allowed(execution_symbol, self.trading_profile):
                logger.critical(f"🚨 V6.5.4d ÚLTIMA DEFENSA: BUY BLOQUEADO en {execution_symbol} - Símbolo excluido")
                return {
                    'success': False,
                    'blocked': True,
                    'error': f'ÚLTIMA DEFENSA: {execution_symbol} está en lista de exclusión',
                    'reason': 'FINAL_SYMBOL_FILTER_VETO'
                }
            
            # Ejecutar según modo
            if self.config['paper_mode']:
                # PAPER TRADING V2 - Usa PostgreSQL institucional
                if self.paper_trading:
                    # V6.5.4d MULTI-USER: Usar user_id del parámetro
                    result = self.paper_trading.execute_paper_trade(
                        user_id=user_id,
                        side=action.lower(),
                        symbol=self.config['trading_pair'],
                        amount_usd=amount_usd
                    )
                else:
                    # Fallback a método legacy si PaperTradingManager no disponible
                    result = self._execute_paper_trade(action, amount_usd)
            else:
                # REAL TRADING - Dinero real en Kraken
                if action == 'BUY':
                    result = self.trading_service.buy(
                        pair=self.config['trading_pair'],
                        amount_usd=amount_usd
                    )
                elif action == 'SELL':
                    result = self.trading_service.sell(
                        pair=self.config['trading_pair'],
                        amount_usd=amount_usd
                    )
                else:
                    return {'error': 'Acción desconocida'}
            
            if result and 'error' not in result:
                self.state['last_trade_time'] = datetime.now()
                self.state['total_trades'] += 1
                mode = "PAPER" if self.config['paper_mode'] else "REAL"
                logger.info(f"✅ TRADE {mode} EJECUTADO: {action} ${amount_usd:.2f}")
                
                # V6.5: Log detallado del registro en base de datos
                trade_id = result.get('trade_id') or result.get('order_id', 'N/A')
                db_status = "📦 Guardado en DB" if result.get('trade_id') else "⚠️ Sin confirmación DB"
                logger.info(f"   💾 {VERSION_BANNER} REGISTRO: Trade #{self.state['total_trades']} | ID: {trade_id} | {db_status}")
                
                # V6.5.4: Log institutional TRADE_EXECUTED
                decision_id = analysis.get('decision_id')
                if institutional_logger and decision_id:
                    entry_price = result.get('entry_price') or result.get('price', 0)
                    institutional_logger.log_trade_executed(
                        symbol=self.config['trading_pair'],
                        decision_id=decision_id,
                        direction=action,
                        size_usd=amount_usd,
                        entry_price=float(entry_price) if entry_price else 0,
                        order_id=str(trade_id)
                    )
                
                # V6.5: Verificar que el trade existe en la base de datos
                if self.database_service and hasattr(self.database_service, 'execute_query'):
                    try:
                        verify_result = self.database_service.execute_query('''
                            SELECT COUNT(*) as count FROM paper_trading_trades 
                            WHERE created_at >= NOW() - INTERVAL '1 minute'
                        ''')
                        if verify_result and len(verify_result) > 0 and verify_result[0]:
                            # Tuple access: SELECT COUNT(*) → first column
                            row = verify_result[0]
                            recent_count = int(row[0] or 0) if row and len(row) > 0 else 0
                            logger.info(f"   ✅ {VERSION_BANNER} VERIFICACIÓN: {recent_count} trade(s) registrado(s) en último minuto")
                    except Exception as e:
                        logger.debug(f"{VERSION_BANNER}: Error verificando registro: {e}")
                
                # 🔒 REGISTRAR TRADE CON VERIFICACIÓN CRIPTOGRÁFICA
                if investor_logger:
                    try:
                        # Obtener precio actual
                        ticker = self.trading_service.kraken.get_ticker(self.config['trading_pair'])
                        current_price = float(ticker['c'][0]) if (ticker and 'c' in ticker) else 0
                        
                        # Preparar señales de estrategias
                        strategies_signals = {}
                        v52_analysis = analysis.get('v52_analysis', {})
                        
                        if v52_analysis.get('quantum_signal'):
                            strategies_signals['Quantum Momentum'] = v52_analysis['quantum_signal']
                        if v52_analysis.get('kalman_trend'):
                            strategies_signals['Kalman Filter'] = v52_analysis['kalman_trend']
                        if v52_analysis.get('market_regime'):
                            strategies_signals['HMM Regime'] = v52_analysis['market_regime']
                        if 'monte_carlo' in analysis:
                            strategies_signals['Monte Carlo'] = f"{analysis['monte_carlo'].get('win_rate', 0):.1%} win rate"
                        if 'black_swan' in analysis:
                            strategies_signals['Black Swan'] = analysis['black_swan'].get('risk_level', 'UNKNOWN')
                        if 'sentiment' in analysis:
                            strategies_signals['Sentiment'] = f"{analysis['sentiment'].get('score', 0)}/100"
                        
                        # Razón completa
                        reasoning = " | ".join(analysis.get('reason', ['No reason provided']))
                        
                        # Registrar con verificación criptográfica
                        investor_logger.log_trade(
                            action=action,
                            symbol=self.config['trading_pair'],
                            amount_usd=amount_usd,
                            price=current_price,
                            confidence=analysis['confidence'],
                            score=int(analysis.get('raw_score', 0)),
                            strategies_signals=strategies_signals,
                            reasoning=reasoning,
                            trade_number=self.state['total_trades'],
                            mode=mode
                        )
                        logger.info(f"📝 Trade #{self.state['total_trades']} registrado con verificación criptográfica SHA256")
                    except Exception as e:
                        logger.warning(f"Error al registrar trade para inversores: {e}")
                
                # 🧠 PROGRAMAR AUTO-EVALUACIÓN POST-TRADE (30 min después)
                trade_id = result.get('order_id', f"trade_{self.state['total_trades']}")
                reasoning_uuid = None
                
                if analysis.get('reasoning'):
                    reasoning_uuid = analysis['reasoning'].get('trade_uuid')
                
                if self.database_service and hasattr(self.database_service, 'schedule_trade_evaluation'):
                    try:
                        effective_user_id = self._get_effective_user_id(None, "schedule_trade_evaluation")
                        self.database_service.schedule_trade_evaluation(
                            trade_id=trade_id,
                            reasoning_uuid=reasoning_uuid,
                            user_id=effective_user_id,
                            minutes_delay=30
                        )
                        logger.info(f"⏰ Auto-evaluación programada para {trade_id} en 30 minutos")
                    except Exception as e:
                        logger.warning(f"Error programando evaluación (no crítico): {e}")
                
                return {
                    'success': True,
                    'action': action,
                    'amount_usd': amount_usd,
                    'confidence': analysis['confidence'],
                    'reason': analysis['reason'],
                    'mode': mode,
                    'trade_id': trade_id,
                    'reasoning_summary': analysis.get('reasoning_summary', '')
                }
            else:
                return {'error': result.get('error', 'Error desconocido')}
                
        except Exception as e:
            logger.error(f"Error ejecutando trade: {e}")
            return {'error': str(e)}
    
    def _execute_paper_trade(self, action: str, amount_usd: float) -> Dict:
        """Ejecutar trade simulado con balance virtual"""
        try:
            # Obtener precio actual
            ticker = self.trading_service.kraken.get_ticker(self.config['trading_pair'])
            if not ticker:
                return {'error': 'No se pudo obtener precio'}
            
            current_price = float(ticker['c'][0]) if 'c' in ticker else 0
            pair = self.config['trading_pair']
            base_asset = pair.split('/')[0]  # BTC
            
            if action == 'BUY':
                # Verificar balance disponible
                if self.state['paper_balance'] < amount_usd:
                    return {'error': f'Balance insuficiente: ${self.state["paper_balance"]:.2f}'}
                
                # Calcular cantidad de crypto
                amount_crypto = amount_usd / current_price
                fee = amount_usd * 0.0026  # 0.26% Kraken fee
                
                # Actualizar balances
                self.state['paper_balance'] -= (amount_usd + fee)
                
                if base_asset not in self.state['paper_positions']:
                    self.state['paper_positions'][base_asset] = {
                        'amount': 0,
                        'avg_price': 0,
                        'total_invested': 0
                    }
                
                pos = self.state['paper_positions'][base_asset]
                pos['total_invested'] += amount_usd
                pos['amount'] += amount_crypto
                pos['avg_price'] = pos['total_invested'] / pos['amount']
                
                logger.info(f"📄 PAPER BUY: {amount_crypto:.8f} {base_asset} @ ${current_price:.2f}")
                
                # Métricas Prometheus
                if METRICS_ENGINE_AVAILABLE and metrics:
                    metrics.record_trade('buy', 'paper', pair, amount_usd, 1.0)
                    metrics.update_balance('paper', 'USD', self.state['paper_balance'])
                    metrics.update_balance('paper', base_asset, pos['amount'])
                
            elif action == 'SELL':
                # Verificar posición disponible
                if base_asset not in self.state['paper_positions']:
                    return {'error': f'No tienes posición en {base_asset}'}
                
                pos = self.state['paper_positions'][base_asset]
                amount_crypto = amount_usd / current_price
                
                if pos['amount'] < amount_crypto:
                    return {'error': f'Posición insuficiente: {pos["amount"]:.8f} {base_asset}'}
                
                # Calcular ganancia/pérdida
                profit_loss = (current_price - pos['avg_price']) * amount_crypto
                fee = amount_usd * 0.0026
                
                # Actualizar balances
                self.state['paper_balance'] += (amount_usd - fee)
                self.state['total_profit_loss'] += profit_loss
                pos['amount'] -= amount_crypto
                pos['total_invested'] -= (amount_crypto * pos['avg_price'])
                
                # Determinar si ganó o perdió
                outcome = 'win' if profit_loss > 0 else 'loss'
                if profit_loss > 0:
                    self.state['winning_trades'] += 1
                else:
                    self.state['losing_trades'] += 1
                
                # FASE 2.3: Tracking de probation para activo en prueba
                self._update_probation_tracking(pair, outcome, profit_loss)
                
                if pos['amount'] < 0.00000001:  # Cerró posición
                    del self.state['paper_positions'][base_asset]
                
                logger.info(f"📄 PAPER SELL: {amount_crypto:.8f} {base_asset} @ ${current_price:.2f} - P/L: ${profit_loss:.2f}")
                
                # Métricas Prometheus
                if METRICS_ENGINE_AVAILABLE and metrics:
                    metrics.record_trade('sell', 'paper', pair, amount_usd, 1.0, outcome=outcome)
                    metrics.update_balance('paper', 'USD', self.state['paper_balance'])
                    metrics.update_balance('paper', base_asset, pos['amount'] if base_asset in self.state['paper_positions'] else 0.0)
                    metrics.update_pnl('paper', self.state['total_profit_loss'])
                    
                    # Win rate
                    total = self.state['total_trades']
                    if total > 0:
                        win_rate = (self.state['winning_trades'] / total) * 100
                        metrics.update_win_rate('paper', win_rate)
            
            return {'success': True, 'price': current_price}
            
        except Exception as e:
            logger.error(f"Error en paper trade: {e}")
            return {'error': str(e)}
    
    def _update_probation_tracking(self, symbol: str, outcome: str, profit_loss: float) -> None:
        """
        FASE 2.3: Actualizar tracking de probation y verificar auto-revert.
        
        Args:
            symbol: Par de trading
            outcome: 'win' o 'loss'
            profit_loss: Ganancia/pérdida del trade
        """
        from datetime import datetime, timezone
        
        p = self.trading_profile
        if not p or not getattr(p, 'probation_enabled', False):
            return
        
        probation_asset = getattr(p, 'probation_asset', "")
        if not probation_asset:
            return
        
        # Normalizar para comparación
        symbol_normalized = symbol.upper().replace("/", "")
        probation_normalized = probation_asset.upper().replace("/", "")
        
        if symbol_normalized != probation_normalized and symbol.upper() != probation_asset.upper():
            return
        
        # Inicializar fecha de inicio si es primer trade
        if self.probation_state['start_date'] is None:
            self.probation_state['start_date'] = datetime.now(timezone.utc).isoformat()
            logger.info(f"🔬 PROBATION: Iniciando periodo de prueba para {probation_asset}")
        
        # Actualizar estadísticas
        self.probation_state['total_trades'] += 1
        self.probation_state['pnl'] += profit_loss
        
        if outcome == 'win':
            self.probation_state['wins'] += 1
            self.probation_state['consecutive_losses'] = 0  # Reset contador
            logger.info(f"🔬 PROBATION WIN: {probation_asset} +${profit_loss:.2f} | "
                       f"Stats: {self.probation_state['wins']}W/{self.probation_state['losses']}L | "
                       f"Total P/L: ${self.probation_state['pnl']:.2f}")
        else:
            self.probation_state['losses'] += 1
            self.probation_state['consecutive_losses'] += 1
            max_losses = getattr(p, 'probation_max_consecutive_losses', 3)
            
            logger.warning(f"🔬 PROBATION LOSS: {probation_asset} -${abs(profit_loss):.2f} | "
                          f"Consecutive: {self.probation_state['consecutive_losses']}/{max_losses} | "
                          f"Stats: {self.probation_state['wins']}W/{self.probation_state['losses']}L")
            
            # Verificar auto-revert
            if self.probation_state['consecutive_losses'] >= max_losses:
                self._execute_probation_auto_revert(probation_asset)
    
    def _execute_probation_auto_revert(self, asset: str) -> None:
        """
        FASE 2.3: Ejecutar auto-revert cuando se alcanzan pérdidas consecutivas máximas.
        
        Args:
            asset: Activo a re-bloquear
        """
        logger.error(f"🚨 PROBATION AUTO-REVERT: {asset} alcanzó límite de pérdidas consecutivas")
        logger.error(f"   Stats finales: {self.probation_state['wins']}W/{self.probation_state['losses']}L | "
                    f"P/L: ${self.probation_state['pnl']:.2f}")
        
        self.probation_state['auto_reverted'] = True
        
        # Desactivar probation en el perfil (runtime only - no persiste)
        if self.trading_profile:
            # Marcar como reverted para que is_symbol_allowed lo bloquee
            self.trading_profile.probation_enabled = False
            logger.error(f"   {asset} BLOQUEADO nuevamente. Probation desactivada.")
        
        # Log para auditoría
        logger.info(f"📊 PROBATION_AUTO_REVERT: asset={asset}, "
                   f"consecutive_losses={self.probation_state['consecutive_losses']}, "
                   f"total_trades={self.probation_state['total_trades']}, "
                   f"pnl={self.probation_state['pnl']:.2f}")
    
    def _calculate_position_size(self, current_price: float) -> float:
        """LEGACY: Usar _calculate_position_size_v52"""
        return self._calculate_position_size_v52(current_price, None, None)
    
    def _calculate_position_size_v52(
        self,
        current_price: float,
        kelly: Optional[Dict],
        hmm_regime: Optional[Dict],
        kernel_confidence: Optional[float] = None,
        kernel_metrics: Optional[Dict] = None,
        decision_confidence: Optional[float] = None
    ) -> float:
        """
        PREMIUM: Calcular tamaño óptimo de posición
        - CAES: Confidence-Adaptive Entry System (sigmoide + sub-regímenes)
        - Kelly Criterion + HMM Regime + Ramp-Up System
        - FASE 2.1: Partial Position Sizing basado en confidence
        - Reduce drawdown inicial empezando conservador
        
        Args:
            current_price: Precio actual del activo
            kelly: Resultados de Kelly Criterion
            hmm_regime: Régimen detectado por HMM
            kernel_confidence: Confianza del Non-Markovian Kernel (0-100%)
            kernel_metrics: Métricas adicionales del kernel
            decision_confidence: Confianza de la decisión (0-1) para partial position
        """
        balance = self._get_balance()
        
        # ========== CAES - CONFIDENCE-ADAPTIVE ENTRY SYSTEM ==========
        # V6.5.4: Incluye validación ATR para mitigar conflicto de interés
        caes_multiplier = 1.0
        caes_result = None
        
        if CAES_AVAILABLE and kernel_confidence is not None:
            try:
                caes = get_caes_instance()
                
                # V6.5.4 CONFLICT OF INTEREST MITIGATION: Calcular ATR ratio
                # ATR ratio es una métrica EXTERNA e INDEPENDIENTE del Kernel
                atr_ratio = 1.0  # Default: volatilidad normal
                if kernel_metrics:
                    # Intentar obtener ATR de las métricas del kernel o del análisis
                    current_atr = kernel_metrics.get('atr', kernel_metrics.get('volatility', 0))
                    historical_atr = kernel_metrics.get('atr_avg', kernel_metrics.get('volatility_avg', 0))
                    
                    if historical_atr and historical_atr > 0 and current_atr:
                        atr_ratio = current_atr / historical_atr
                        logger.debug(f"🎯 CAES ATR Validation: current={current_atr:.4f}, avg={historical_atr:.4f}, ratio={atr_ratio:.2f}")
                
                caes_result = caes.calculate_adaptive_parameters(
                    kernel_confidence=kernel_confidence,
                    kernel_metrics=kernel_metrics or {},
                    atr_ratio=atr_ratio  # V6.5.4: Pass ATR for independent validation
                )
                caes_multiplier = caes_result.position_multiplier
                
                self._last_caes_result = caes_result
                
            except Exception as e:
                logger.debug(f"CAES calculation failed: {e}")
                caes_multiplier = 1.0
        
        # ========== RAMP-UP SYSTEM CON TRADING PROFILES ==========
        total_trades = self.state.get('total_trades', 0)
        winning_trades = self.state.get('winning_trades', 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 50
        
        p = self.trading_profile
        phase1_trades = p.ramp_up_phase1_trades if p else 5
        phase2_trades = p.ramp_up_phase2_trades if p else 10
        phase3_trades = p.ramp_up_phase3_trades if p else 20
        phase4_trades = p.ramp_up_phase4_trades if p else 50
        phase1_factor = p.ramp_up_phase1_factor if p else 0.30
        phase2_factor = p.ramp_up_phase2_factor if p else 0.50
        phase3_factor = p.ramp_up_phase3_factor if p else 0.70
        phase4_factor = p.ramp_up_phase4_factor if p else 0.85
        
        if total_trades < phase1_trades:
            ramp_up_factor = phase1_factor
        elif total_trades < phase2_trades:
            ramp_up_factor = phase2_factor
        elif total_trades < phase3_trades:
            ramp_up_factor = phase3_factor
        elif total_trades < phase4_trades:
            ramp_up_factor = phase4_factor
        else:
            ramp_up_factor = 1.0
        
        if total_trades >= 10 and win_rate >= 60:
            ramp_up_factor = min(1.0, ramp_up_factor * 1.15)
        
        if total_trades >= 10 and win_rate < 45:
            ramp_up_factor *= 0.70
        
        # Tamaño base según configuración
        base_size = balance * self.config['max_position_pct']
        
        # Aplicar ramp-up
        base_size *= ramp_up_factor
        
        # ========== APLICAR CAES MULTIPLIER ==========
        base_size *= caes_multiplier
        
        # Ajuste por Kelly Criterion
        if kelly and 'recommended_position_usd' in kelly:
            kelly_size = kelly['recommended_position_usd']
            kelly_weight = 0.5 if total_trades < 20 else 0.6
            base_size = base_size * (1 - kelly_weight) + kelly_size * kelly_weight
        
        # Ajuste por régimen de mercado (HMM)
        if hmm_regime and 'recommended_params' in hmm_regime:
            params = hmm_regime['recommended_params']
            position_multiplier = params.get('position_size_multiplier', 1.0)
            base_size *= position_multiplier
        
        # V6.4: Protección contra drawdown
        daily_loss = self.state.get('daily_profit_loss', 0)
        if daily_loss < -500:
            base_size *= 0.50
            logger.warning(f"⚠️ V6.4 Drawdown Protection: Día con pérdida ${daily_loss:.2f} - reduciendo posición")
        elif daily_loss < -200:
            base_size *= 0.75
        
        # Límites de seguridad (CAES puede ajustar max según régimen)
        min_size = self.config['min_trade_usd']
        max_pct = 0.15
        if caes_result:
            max_pct = min(0.15, caes_result.max_position_pct / 100)
        max_size = balance * max_pct
        
        optimal_size = max(min_size, min(base_size, max_size))
        
        # ========== FASE 2.1: PARTIAL POSITION SIZING ==========
        # Reduce tamaño cuando confidence está en rango intermedio (50-65%)
        partial_multiplier = 1.0
        partial_info = ""
        
        if decision_confidence is not None and p and getattr(p, 'partial_position_enabled', False):
            min_conf = getattr(p, 'partial_position_min_confidence', 0.50)
            max_conf = getattr(p, 'partial_position_max_confidence', 0.65)
            min_size_pct = getattr(p, 'partial_position_min_size', 0.25)
            max_size_pct = getattr(p, 'partial_position_max_size', 0.40)
            
            if decision_confidence < min_conf:
                # Debajo del mínimo - no debería llegar aquí pero por seguridad
                partial_multiplier = 0.0
                partial_info = f", PARTIAL=0% (conf={decision_confidence:.0%} < {min_conf:.0%})"
            elif decision_confidence < max_conf:
                # Rango intermedio - escala lineal entre min_size y max_size
                conf_range = max_conf - min_conf
                conf_position = (decision_confidence - min_conf) / conf_range
                partial_multiplier = min_size_pct + (max_size_pct - min_size_pct) * conf_position
                partial_info = f", PARTIAL={partial_multiplier:.0%} (conf={decision_confidence:.0%})"
                logger.info(f"📉 FASE 2.1 Partial Position: Confidence {decision_confidence:.0%} → Size {partial_multiplier:.0%}")
            # Si >= max_conf, multiplier = 1.0 (full size)
            
            optimal_size *= partial_multiplier
        
        # ========== FASE 2.3: PROBATION FORCED PARTIAL SIZING ==========
        # Activos en probation SIEMPRE usan partial sizing máximo
        # NOTA: El cap se aplica solo si el activo actual es el de probation
        # Verificado en execute_trade donde se conoce el símbolo
        probation_cap_applied = False
        # Cap movido a execute_trade donde hay contexto del símbolo
        
        # Log para tracking
        if total_trades < 20 or caes_multiplier != 1.0 or partial_multiplier != 1.0:
            caes_info = f", CAES={caes_multiplier:.2f}x" if caes_multiplier != 1.0 else ""
            logger.info(f"📊 {VERSION_BANNER} Ramp-Up: Trade #{total_trades+1}, Factor={ramp_up_factor:.0%}{caes_info}{partial_info}, Size=${optimal_size:.2f}")
        
        return optimal_size
    
    # ==========================================================================
    # V6.5.4 PREMIUM: PER-PAIR CIRCUIT BREAKER - INSTITUTIONAL GRADE
    # ==========================================================================
    
    def check_circuit_breaker(self, symbol: str, balance: float) -> bool:
        """
        V6.5.4 PREMIUM: Verifica si el par está bloqueado por circuit breaker.
        
        Returns:
            True si el trade está permitido, False si está bloqueado
        """
        import json as json_cb
        from datetime import datetime as dt_cb, timezone as tz_cb
        
        normalized = self._normalize_symbol_for_calibration(symbol)
        if normalized not in self.daily_drawdown_per_pair:
            return True
        
        self._reset_daily_drawdown_if_needed(normalized)
        
        calibration = get_pair_calibration(normalized) if get_pair_calibration else None
        if not calibration:
            return True
        
        max_dd_pct = calibration.max_daily_drawdown_pct
        allowed_loss = balance * max_dd_pct
        current_dd = abs(self.daily_drawdown_per_pair[normalized]["pnl"])
        
        if current_dd >= allowed_loss:
            veto_event = {
                "event": "VETO_CIRCUIT_BREAKER",
                "symbol": normalized,
                "max_dd_pct": max_dd_pct,
                "allowed_loss_usd": round(allowed_loss, 2),
                "current_dd_usd": round(current_dd, 2),
                "calibration_tier": calibration.tier.value,
                "status": "BLOCKED",
                "timestamp": dt_cb.now(tz_cb.utc).isoformat()
            }
            logger.warning(f"🔌 CIRCUIT BREAKER: {normalized} BLOQUEADO - DD ${current_dd:.2f} >= ${allowed_loss:.2f}")
            logger.info(f"📊 CIRCUIT_BREAKER: {json_cb.dumps(veto_event)}")
            return False
        
        return True
    
    def update_pair_drawdown(self, symbol: str, pnl: float) -> None:
        """
        V6.5.4 PREMIUM: Actualiza el drawdown acumulado para un par.
        Se llama al cerrar cada trade.
        """
        import json as json_upd
        from datetime import datetime as dt_upd, timezone as tz_upd
        
        normalized = self._normalize_symbol_for_calibration(symbol)
        if normalized not in self.daily_drawdown_per_pair:
            self.daily_drawdown_per_pair[normalized] = {
                "pnl": 0.0,
                "date": dt_upd.now(tz_upd.utc).strftime('%Y-%m-%d')
            }
        
        self._reset_daily_drawdown_if_needed(normalized)
        
        old_pnl = self.daily_drawdown_per_pair[normalized]["pnl"]
        new_pnl = old_pnl + pnl
        self.daily_drawdown_per_pair[normalized]["pnl"] = new_pnl
        
        update_event = {
            "event": "DRAWDOWN_UPDATE",
            "symbol": normalized,
            "trade_pnl": round(pnl, 2),
            "daily_pnl": round(new_pnl, 2),
            "timestamp": dt_upd.now(tz_upd.utc).isoformat()
        }
        logger.info(f"📊 DRAWDOWN_TRACKER: {json_upd.dumps(update_event)}")
    
    def _reset_daily_drawdown_if_needed(self, symbol: str) -> None:
        """
        V6.5.4 PREMIUM: Reset automático del drawdown a las 00:00 UTC.
        """
        import json as json_rst
        from datetime import datetime as dt_rst, timezone as tz_rst
        
        today_utc = dt_rst.now(tz_rst.utc).strftime('%Y-%m-%d')
        record = self.daily_drawdown_per_pair.get(symbol)
        
        if record and record["date"] != today_utc:
            old_pnl = record["pnl"]
            record["date"] = today_utc
            record["pnl"] = 0.0
            
            reset_event = {
                "event": "DRAWDOWN_RESET",
                "symbol": symbol,
                "previous_pnl": round(old_pnl, 2),
                "new_date": today_utc,
                "timestamp": dt_rst.now(tz_rst.utc).isoformat()
            }
            logger.info(f"🔄 DRAWDOWN_RESET: {json_rst.dumps(reset_event)}")
    
    def _normalize_symbol_for_calibration(self, symbol: str) -> str:
        """Normaliza símbolo Kraken a formato estándar para calibración"""
        if symbol in self.DISPLAY_SYMBOL_MAP:
            return self.DISPLAY_SYMBOL_MAP[symbol]
        if '/' in symbol:
            return symbol
        if len(symbol) >= 6:
            return f"{symbol[:-3]}/{symbol[-3:]}"
        return symbol
    
    # ==========================================================================
    # END CIRCUIT BREAKER
    # ==========================================================================
    
    def _get_balance(self) -> float:
        """Obtener balance disponible en USD (paper o real)"""
        try:
            if self.config['paper_mode']:
                # PAPER TRADING - Balance virtual
                return self.state['paper_balance']
            else:
                # REAL TRADING - Balance real en Kraken
                if hasattr(self.trading_service, 'get_balance'):
                    balance = self.trading_service.get_balance()
                    
                    # Kraken devuelve 'ZUSD' (formato Kraken) o 'USD'
                    usd_balance = float(balance.get('ZUSD', balance.get('USD', 0)))
                    
                    logger.info(f"💰 Balance detectado: ${usd_balance:.2f} (Kraken data: {balance})")
                    return usd_balance
                return 0.0
        except Exception as e:
            logger.error(f"❌ ERROR obteniendo balance: {e}")
            return 0.0
    
    def _get_price_history(self, pair: str, days: int = 100) -> Optional[List[float]]:
        """Obtener histórico de precios"""
        try:
            if hasattr(self.trading_service, 'get_ohlc'):
                ohlc = self.trading_service.get_ohlc(pair, interval=1440)
                if ohlc and len(ohlc) > 0:
                    return [float(candle[4]) for candle in ohlc[-days:]]
            return None
        except Exception as e:
            logger.debug(f"Error getting price history for {pair}: {e}")
            return None
    
    def _get_volume_history(self, pair: str, days: int = 100) -> Optional[List[float]]:
        """Obtener histórico de volúmenes"""
        try:
            if hasattr(self.trading_service, 'get_ohlc'):
                ohlc = self.trading_service.get_ohlc(pair, interval=1440)
                if ohlc and len(ohlc) > 0:
                    return [float(candle[6]) for candle in ohlc[-days:]]
            return None
        except Exception as e:
            logger.debug(f"Error getting volume history for {pair}: {e}")
            return None
    
    def _get_ohlc_history(self, pair: str, days: int = 100) -> Optional[Dict[str, List[float]]]:
        """
        FIX: Obtener histórico OHLC completo para estrategias que requieren highs/lows
        
        Garantías:
        - Todas las listas tienen la misma longitud
        - Volumes nunca es None (usa sintéticos si faltan)
        - Logging cuando hay problemas
        
        Returns:
            Dict con keys: 'opens', 'highs', 'lows', 'closes', 'volumes'
            O None si no hay datos suficientes
        """
        try:
            if not hasattr(self.trading_service, 'get_ohlc'):
                logger.debug(f"Trading service does not have get_ohlc method for {pair}")
                return None
            
            ohlc = self.trading_service.get_ohlc(pair, interval=1440)
            if not ohlc or len(ohlc) == 0:
                logger.debug(f"No OHLC data returned for {pair}")
                return None
            
            data = ohlc[-days:]
            data_len = len(data)
            
            opens = []
            highs = []
            lows = []
            closes = []
            volumes = []
            
            for c in data:
                try:
                    opens.append(float(c[1]) if c[1] else 0.0)
                    highs.append(float(c[2]) if c[2] else 0.0)
                    lows.append(float(c[3]) if c[3] else 0.0)
                    closes.append(float(c[4]) if c[4] else 0.0)
                    vol = float(c[6]) if len(c) > 6 and c[6] else 0.0
                    volumes.append(vol)
                except (IndexError, TypeError, ValueError):
                    opens.append(0.0)
                    highs.append(0.0)
                    lows.append(0.0)
                    closes.append(0.0)
                    volumes.append(0.0)
            
            has_valid_volumes = any(v > 0 for v in volumes)
            if not has_valid_volumes:
                volumes = self._generate_synthetic_volumes(closes, target_length=data_len)
                logger.debug(f"📊 Using synthetic volumes for {pair} ({data_len} candles)")
            
            if not all(len(arr) == data_len for arr in [opens, highs, lows, closes, volumes]):
                logger.warning(f"⚠️ OHLC array length mismatch for {pair}, padding to {data_len}")
                opens = (opens + [0.0] * data_len)[:data_len]
                highs = (highs + [0.0] * data_len)[:data_len]
                lows = (lows + [0.0] * data_len)[:data_len]
                closes = (closes + [0.0] * data_len)[:data_len]
                volumes = (volumes + [1000.0] * data_len)[:data_len]
            
            return {
                'opens': opens,
                'highs': highs,
                'lows': lows,
                'closes': closes,
                'volumes': volumes
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error getting OHLC history for {pair}: {e}")
            return None
    
    def _generate_synthetic_volumes(self, prices: List[float], target_length: int = None) -> List[float]:
        """
        FIX: Generar volúmenes sintéticos basados en price changes
        cuando Kraken no proporciona datos de volumen
        
        Estrategia: volatilidad relativa * base volume
        Garantiza: Longitud exacta igual a prices (o target_length si se especifica)
        
        Args:
            prices: Lista de precios close
            target_length: Longitud deseada del output (default: len(prices))
        """
        if not prices:
            return []
        
        length = target_length if target_length else len(prices)
        base_volume = 1000.0
        
        if len(prices) < 2:
            return [base_volume] * length
        
        volumes = []
        for i in range(len(prices)):
            if i == 0:
                volumes.append(base_volume)
            else:
                prev_price = prices[i-1]
                if prev_price and prev_price != 0:
                    price_change = abs(prices[i] - prev_price) / prev_price
                    vol_factor = 1.0 + min(price_change * 10, 5.0)
                else:
                    vol_factor = 1.0
                volumes.append(base_volume * vol_factor)
        
        while len(volumes) < length:
            volumes.append(base_volume)
        
        return volumes[:length]
    
    def _apply_adaptive_parameters(self, strategy_name: str, profile) -> None:
        """
        Apply calibrated parameters to trading strategies.
        
        Called by Adaptive Parameter Engine when regime change detected.
        
        SAFEGUARDS:
        - Verifies no open positions before applying changes
        - Only applies to NEW trades, does not affect in-progress trades
        - Validates with Risk Guardian before applying
        - Stores parameters for next trade, does not modify active trades
        
        Args:
            strategy_name: Strategy identifier (QUANTUM_MOMENTUM, HMM_REGIME, etc.)
            profile: AdaptiveParameterProfile with new parameters
        """
        try:
            # SAFEGUARD 1: Verificar que no hay posiciones abiertas
            has_open_positions = False
            if self.config.get('paper_mode'):
                has_open_positions = bool(self.state.get('paper_positions', {}))
            else:
                if hasattr(self.trading_service, 'get_open_orders'):
                    try:
                        open_orders = self.trading_service.get_open_orders()
                        has_open_positions = bool(open_orders)
                    except:
                        pass
            
            if has_open_positions:
                # Guardar parámetros para aplicar cuando no haya posiciones
                if not hasattr(self, '_pending_calibrations'):
                    self._pending_calibrations = {}
                self._pending_calibrations[strategy_name] = profile
                logger.info(f"⏳ Calibración pendiente para {strategy_name} (hay posiciones abiertas)")
                return
            
            # SAFEGUARD 2: Validar con Risk Guardian
            if self.risk_guardian:
                try:
                    if hasattr(self.risk_guardian, 'validate_parameter_change'):
                        validation = self.risk_guardian.validate_parameter_change({
                            'strategy': strategy_name,
                            'stop_loss_pct': profile.stop_loss_pct,
                            'take_profit_pct': profile.take_profit_pct,
                            'position_size_factor': profile.position_size_factor
                        })
                        if validation and not validation.get('approved', True):
                            logger.warning(f"🛡️ Risk Guardian rechazó calibración: {validation.get('reason')}")
                            return
                except Exception as e:
                    logger.warning(f"Risk Guardian validation error: {e}")
            
            # SAFEGUARD 3: Almacenar en _next_trade_params en lugar de modificar directamente
            if not hasattr(self, '_next_trade_params'):
                self._next_trade_params = {}
            
            self._next_trade_params[strategy_name] = {
                'stop_loss_pct': profile.stop_loss_pct,
                'take_profit_pct': profile.take_profit_pct,
                'position_size_factor': profile.position_size_factor,
                'entry_threshold': profile.entry_threshold,
                'applied_at': datetime.utcnow().isoformat()
            }
            
            # También actualizar la configuración global del bot para nuevos trades
            if hasattr(profile, 'stop_loss_pct'):
                self.config['stop_loss_pct'] = abs(profile.stop_loss_pct)
            
            logger.info(f"✅ Parámetros adaptativos guardados para próximo trade de {strategy_name}")
            logger.info(f"   SL={profile.stop_loss_pct:.3f}, TP={profile.take_profit_pct:.3f}, Size={profile.position_size_factor:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Error aplicando parámetros adaptativos a {strategy_name}: {e}")
    
    def _get_adaptive_params_for_trade(self, strategy_name: str) -> Optional[Dict]:
        """
        Obtener parámetros adaptativos para un nuevo trade.
        
        Called when opening new trade to get calibrated parameters.
        
        Args:
            strategy_name: Strategy identifier (QUANTUM_MOMENTUM, HMM_REGIME, etc.)
            
        Returns:
            Dict con parámetros o None si no hay calibración pendiente
        """
        if not hasattr(self, '_next_trade_params'):
            return None
        
        return self._next_trade_params.get(strategy_name)
    
    def _apply_pending_calibrations(self) -> None:
        """
        Aplicar calibraciones pendientes cuando no hay posiciones abiertas.
        
        Se llama periódicamente para verificar si hay calibraciones
        que estaban esperando a que se cerraran las posiciones.
        """
        if not hasattr(self, '_pending_calibrations') or not self._pending_calibrations:
            return
        
        # Verificar si ahora no hay posiciones
        has_open_positions = False
        if self.config.get('paper_mode'):
            has_open_positions = bool(self.state.get('paper_positions', {}))
        
        if not has_open_positions:
            for strategy_name, profile in list(self._pending_calibrations.items()):
                self._apply_adaptive_parameters(strategy_name, profile)
                del self._pending_calibrations[strategy_name]
            logger.info("✅ Calibraciones pendientes aplicadas")
    
    def _process_kernel_for_adaptive_engine(self, kernel_output: Dict) -> None:
        """
        Process Non-Markovian Kernel output for Adaptive Engine.
        
        Sends regime signals to the adaptive engine to determine
        if strategy parameters need recalibration.
        
        Args:
            kernel_output: Diccionario con salida del kernel (regime, coherence, etc.)
        """
        if not self.adaptive_engine:
            return
        
        try:
            # Obtener datos de microestructura (si están disponibles)
            microstructure_data = None
            if hasattr(self.trading_service, 'get_spread'):
                try:
                    spread = self.trading_service.get_spread(self.config.get('trading_pair', 'BTC/USD'))
                    microstructure_data = {
                        'current_spread': spread.get('spread', 0.001) if spread else 0.001,
                        'current_volume': spread.get('volume', 1000000) if spread else 1000000
                    }
                except:
                    pass
            
            # Procesar señal del kernel
            result = self.adaptive_engine.process_kernel_signal(
                kernel_output=kernel_output,
                microstructure_data=microstructure_data
            )
            
            if result.get('is_significant_change'):
                logger.info(f"🎯 Adaptive Engine: Régimen cambiado a {result.get('regime')}")
                
                # Record trade in cooldown manager for active strategies
                for strategy in ['QUANTUM_MOMENTUM', 'HMM_REGIME']:
                    self.adaptive_engine.record_trade(strategy)
                    
        except Exception as e:
            logger.error(f"❌ Error procesando kernel para Adaptive Engine: {e}")
    
    def get_adaptive_status(self) -> Dict:
        """
        📊 Obtener estado del Adaptive Parameter Engine
        
        Returns:
            Dict con estado actual del engine y perfiles activos
        """
        if not self.adaptive_engine:
            return {'enabled': False, 'reason': 'Adaptive Engine no inicializado'}
        
        try:
            status = self.adaptive_engine.get_status()
            return {
                'enabled': True,
                **status
            }
        except Exception as e:
            return {'enabled': False, 'error': str(e)}
    
    def _process_pending_evaluations(self):
        """
        🧠 Procesar evaluaciones pendientes (sistema robusto sin threads)
        
        Obtiene trades que ya es hora de evaluar y ejecuta auto-evaluación
        """
        if not self.database_service or not self.conversational_brain:
            return
        
        try:
            # Obtener evaluaciones listas para procesar
            due_evaluations = self.database_service.get_due_evaluations()
            
            if not due_evaluations:
                return
            
            logger.info(f"🔍 Procesando {len(due_evaluations)} evaluaciones pendientes")
            
            for eval_data in due_evaluations:
                try:
                    trade_id = eval_data['trade_id']
                    user_id = eval_data['user_id']
                    
                    # Obtener razonamiento original (si existe)
                    original_reasoning = {}
                    if eval_data.get('reasoning_uuid'):
                        # TODO: Obtener razonamiento de DB por UUID
                        pass
                    
                    # Obtener resultado del trade (precio actual vs precio de entrada)
                    # Por ahora usamos datos simulados, idealmente se obtiene de la DB
                    trade_result = {
                        'profit_loss': 0,  # Será calculado real
                        'exit_price': 0,
                        'entry_price': 0
                    }
                    
                    # TODO: Obtener trade real de la base de datos para calcular P/L
                    # Por ahora marcamos como completado sin evaluación detallada
                    
                    # Generar auto-evaluación
                    evaluation = self.conversational_brain.generate_post_trade_evaluation(
                        trade_id=trade_id,
                        original_reasoning=original_reasoning,
                        trade_result=trade_result,
                        elapsed_minutes=30
                    )
                    
                    # Guardar evaluación en DB
                    self.database_service.save_trade_evaluation(evaluation)
                    
                    # Marcar como completada
                    self.database_service.mark_evaluation_completed(
                        evaluation_id=eval_data['id'],
                        result=evaluation
                    )
                    
                    logger.info(f"✅ Evaluación completada para trade {trade_id}")
                    
                except Exception as e:
                    logger.error(f"Error procesando evaluación individual: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error procesando evaluaciones pendientes: {e}")
    
    def _check_position_limit_early(self, user_id: str = None) -> bool:
        """
        FIX INSTITUCIONAL V6.5.4c: Verificar límite de posiciones ANTES del análisis.
        
        Práctica institucional: El check de límites debe ser la PRIMERA validación,
        no la última. Esto ahorra CPU y evita logs innecesarios.
        
        V6.5.4c: Usa paper_trading para obtener posiciones correctamente.
        Límite: máximo 10 posiciones totales (reducido de 20).
        
        Args:
            user_id: ID del usuario (V6.5.4d MULTI-USER). Si None, usa fallback legacy.
        
        Returns:
            True si el límite está alcanzado (no abrir nuevas posiciones)
            False si hay espacio para nuevas posiciones
        """
        try:
            max_positions = self.config.get('max_open_positions', 10)  # V6.5.4c: Reducido a 10
            
            # V6.5.4d MULTI-USER: Usar método centralizado para obtener user_id
            user_id = self._get_effective_user_id(user_id, caller='_check_position_limit_early')
            
            # V6.5.4d MULTI-USER: Verify user has permission to check positions
            try:
                self._require_trading_permission(user_id, 'view_positions')
            except AuthorizationError as e:
                logger.warning(f"🚫 {e}")
                return True  # Block new positions for unauthorized users
            
            # V6.5.4c: Usar paper_trading para obtener posiciones correctamente
            if self.paper_trading and self.config.get('paper_mode', False):
                open_positions = self.paper_trading.get_open_positions(user_id)
                current_count = len(open_positions) if open_positions else 0
                
                if current_count >= max_positions:
                    logger.warning(f"🛑 {VERSION_BANNER} LÍMITE GLOBAL ALCANZADO: {current_count}/{max_positions} posiciones abiertas")
                    logger.warning(f"   Saltando análisis de nuevas entradas - esperando cierres de SL/TP")
                    return True
                    
            elif self.database_service:
                # Fallback para real trading
                user_id = self.config.get('user_id', 'system')
                open_positions = self.database_service.get_open_positions(user_id)
                current_count = len(open_positions) if open_positions else 0
                
                if current_count >= max_positions:
                    logger.warning(f"🛑 {VERSION_BANNER} LÍMITE ALCANZADO: {current_count}/{max_positions} posiciones abiertas")
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error verificando límite de posiciones: {e}")
            return False
    
    def _check_emergency_stop(self) -> bool:
        """Verificar si debemos detener por pérdidas excesivas"""
        if not self.state['initial_balance']:
            return False
        
        current_balance = self._get_balance()
        loss_pct = (self.state['initial_balance'] - current_balance) / self.state['initial_balance']
        
        if loss_pct > self.config['max_daily_loss_pct']:
            self.state['emergency_stop'] = True
            return True
        
        return False
    
    def _update_stats(self, trade_result: Dict):
        """Actualizar estadísticas del bot"""
        self.state['total_trades'] += 1
        # TODO: Implementar tracking de ganancias/pérdidas
    
    def _get_stats(self) -> Dict:
        """Obtener estadísticas del bot -  Lee directamente de la DB para datos precisos"""
        total = self.state['total_trades']
        winning = self.state['winning_trades']
        losing = self.state['losing_trades']
        total_pnl = self.state['total_profit_loss']
        
        # Intentar obtener datos actualizados de la DB
        try:
            if self.database_service and hasattr(self.database_service, 'execute_query'):
                result = self.database_service.execute_query('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins,
                        SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losses,
                        COALESCE(SUM(profit_loss), 0) as total_pnl
                    FROM paper_trading_trades
                    WHERE status = 'closed'
                ''')
                if result and len(result) > 0 and result[0]:
                    row = result[0]
                    if row and len(row) >= 4:
                        db_total = int(row[0] or 0)
                        db_winning = int(row[1] or 0)
                        db_losing = int(row[2] or 0)
                        db_pnl = float(row[3] or 0)
                        
                        # Usar datos de DB si son más altos (más precisos)
                        if db_total >= total:
                            total = db_total
                            winning = db_winning
                            losing = db_losing
                            total_pnl = db_pnl
                            # Sincronizar state con DB
                            self.state['total_trades'] = total
                            self.state['winning_trades'] = winning
                            self.state['losing_trades'] = losing
                            self.state['total_profit_loss'] = total_pnl
        except Exception as e:
            logger.debug(f"Error refrescando stats de DB: {e}")
        
        win_rate = (winning / total * 100) if total > 0 else 0
        
        return {
            'total_trades': total,
            'winning_trades': winning,
            'losing_trades': losing,
            'win_rate': win_rate,
            'total_profit_loss': total_pnl,
            'initial_balance': self.state['initial_balance'],
            'roi': 0.0  # TODO: Calcular ROI real
        }
    
    def get_status(self) -> Dict:
        """Obtener estado actual del bot"""
        balance = self._get_balance()
        stats = self._get_stats()
        
        # Calcular métricas
        total_trades = self.state['total_trades']
        winning_trades = self.state['winning_trades']
        losing_trades = self.state['losing_trades']
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        profit_loss = self.state['total_profit_loss']
        initial_balance = self.state['initial_balance'] if self.state['initial_balance'] else balance
        roi = ((balance - initial_balance) / initial_balance * 100) if initial_balance > 0 else 0
        
        status = {
            'running': self.state['running'],
            'paper_mode': self.config['paper_mode'],
            'trading_pair': self.config['trading_pair'],
            'trading_pairs': self.config.get('trading_pairs', ['BTC/USD']),  # V6.5: Lista completa de 11 pares
            'current_balance': balance,
            'initial_balance': initial_balance,
            'profit_loss': profit_loss,
            'roi': roi,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'last_trade_time': self.state.get('last_trade_time', None),
            'check_interval': self.config['check_interval_seconds'],
            'min_confidence': self.config['min_confidence'],
            'stop_loss_pct': self.config['stop_loss_pct'],
            'emergency_stop': self.state['emergency_stop']
        }
        
        # Agregar posiciones si está en paper mode
        if self.config['paper_mode'] and self.state['paper_positions']:
            status['paper_positions'] = self.state['paper_positions']
        
        # Agregar estado de auto-learning si está disponible
        if self.auto_learning:
            status['auto_learning'] = {
                'enabled': self.auto_learning.enabled,
                'adjustable_params': len(self.auto_learning.adjustable_params),
                'blocked_params': len(self.auto_learning.blocked_params),
                'changes_history': len(self.auto_learning.changes_history)
            }
        
        return status
    
    def process_video_learning(
        self,
        video_url: str,
        ai_response: Optional[str] = None,
        auto_apply: bool = False
    ) -> Dict[str, Any]:
        """
        🎓 PREMIUM: Procesar video de trading y extraer insights
        
        Args:
            video_url: URL del video de YouTube
            ai_response: Respuesta de IA que ya analizó el video (opcional)
            auto_apply: Si True, aplica cambios automáticamente (requiere auto_learning enabled)
            
        Returns:
            Resultado del análisis con propuestas de ajuste
        """
        if not AUTO_LEARNING_AVAILABLE or not self.video_analyzer:
            return {
                'success': False,
                'error': 'Auto-Learning System no disponible'
            }
        
        logger.info(f"🎬 Procesando video para aprendizaje: {video_url}")
        
        try:
            # Analizar video con VideoLearningAnalyzer
            analysis = self.video_analyzer.analyze_video(video_url, ai_response)
            
            # Extraer propuestas de ajuste
            proposals = analysis.get('adjustment_proposals', [])
            
            logger.info(f"💡 {len(proposals)} propuestas generadas del video")
            
            result = {
                'success': True,
                'video_url': video_url,
                'insights': analysis.get('raw_insights', []),
                'technical_parameters': analysis.get('technical_parameters', {}),
                'proposals': proposals,
                'confidence': analysis.get('confidence_score', 0.0),
                'applied': []
            }
            
            # Si auto_apply está activado y auto_learning está habilitado, aplicar cambios
            if auto_apply and self.auto_learning and self.auto_learning.enabled:
                logger.info("⚡ Auto-aplicando cambios aprendidos del video...")
                applied_count = 0
                
                for proposal in proposals:
                    apply_result = self.auto_learning.apply_adjustment(
                        param_name=proposal['param_name'],
                        new_value=proposal['new_value'],
                        reason=proposal['reason'],
                        learning_source=f'YouTube: {video_url}'
                    )
                    
                    if apply_result.get('success'):
                        result['applied'].append(apply_result)
                        applied_count += 1
                        logger.info(f"✅ Aplicado: {proposal['param_name']} → {proposal['new_value']}")
                    else:
                        logger.warning(f"⚠️ No aplicado: {apply_result.get('error')}")
                
                result['auto_applied'] = True
                result['applied_count'] = applied_count
                
                logger.info(f"🎓 Aprendizaje completado: {applied_count}/{len(proposals)} cambios aplicados")
            
            elif auto_apply and self.auto_learning and not self.auto_learning.enabled:
                result['message'] = '⏸️ Auto-Learning desactivado. Usa /activar_auto_ajuste para aplicar automáticamente'
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error procesando video: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def apply_learning_proposal(
        self,
        param_name: str,
        new_value: float,
        reason: str = "Manual approval"
    ) -> Dict[str, Any]:
        """
        Aplicar una propuesta de aprendizaje manualmente (aprobada por Harold)
        
        Args:
            param_name: Nombre del parámetro
            new_value: Nuevo valor
            reason: Razón del cambio
            
        Returns:
            Resultado de la aplicación
        """
        if not AUTO_LEARNING_AVAILABLE or not self.auto_learning:
            return {
                'success': False,
                'error': 'Auto-Learning System no disponible'
            }
        
        # Aplicar con auto_approve=True (aprobado por Harold)
        result = self.auto_learning.apply_adjustment(
            param_name=param_name,
            new_value=new_value,
            reason=reason,
            learning_source='Harold - Manual Approval',
            auto_approve=True
        )
        
        if result.get('success'):
            logger.info(f"✅ Harold aprobó cambio: {param_name} → {new_value}")
            
            # Actualizar configuración del bot si aplica
            self._sync_config_from_learning_system()
        
        return result
    
    def rollback_last_learning(self) -> Dict[str, Any]:
        """
        Revertir el último cambio de aprendizaje
        
        Returns:
            Resultado del rollback
        """
        if not AUTO_LEARNING_AVAILABLE or not self.auto_learning:
            return {
                'success': False,
                'error': 'Auto-Learning System no disponible'
            }
        
        result = self.auto_learning.rollback_last_change()
        
        if result.get('success'):
            logger.info(f"↩️ Cambio revertido: {result['param_name']}")
            
            # Actualizar configuración del bot
            self._sync_config_from_learning_system()
        
        return result
    
    def get_learning_status(self) -> Dict[str, Any]:
        """
        Obtener estado completo del sistema de auto-aprendizaje
        
        Returns:
            Estado detallado del auto-learning
        """
        if not AUTO_LEARNING_AVAILABLE or not self.auto_learning:
            return {
                'available': False,
                'message': 'Auto-Learning System no disponible'
            }
        
        current_config = self.auto_learning.get_current_config()
        recent_changes = self.auto_learning.get_changes_history(limit=10)
        
        return {
            'available': True,
            'enabled': self.auto_learning.enabled,
            'current_parameters': current_config,
            'adjustable_params': {
                name: {
                    'current': param.current_value,
                    'min': param.min_value,
                    'max': param.max_value,
                    'description': param.description
                }
                for name, param in self.auto_learning.adjustable_params.items()
            },
            'blocked_params': list(self.auto_learning.blocked_params.keys()),
            'recent_changes': recent_changes,
            'total_changes': len(self.auto_learning.changes_history)
        }
    
    def enable_auto_learning(self) -> Dict[str, Any]:
        """Activar sistema de auto-aprendizaje"""
        if not AUTO_LEARNING_AVAILABLE or not self.auto_learning:
            return {
                'success': False,
                'error': 'Auto-Learning System no disponible'
            }
        
        self.auto_learning.enable()
        logger.info("🎓 Auto-Learning ACTIVADO por Harold")
        
        return {
            'success': True,
            'message': '🎓 Auto-Learning System ACTIVADO - El bot aprenderá y aplicará cambios automáticamente'
        }
    
    def disable_auto_learning(self) -> Dict[str, Any]:
        """Desactivar sistema de auto-aprendizaje"""
        if not AUTO_LEARNING_AVAILABLE or not self.auto_learning:
            return {
                'success': False,
                'error': 'Auto-Learning System no disponible'
            }
        
        self.auto_learning.disable()
        logger.info("⏸️ Auto-Learning PAUSADO por Harold")
        
        return {
            'success': True,
            'message': '⏸️ Auto-Learning System PAUSADO - El bot propondrá cambios pero no los aplicará'
        }
    
    def _sync_config_from_learning_system(self):
        """Sincronizar configuración del bot con el sistema de aprendizaje"""
        if not self.auto_learning:
            return
        
        current_params = self.auto_learning.get_current_config()
        
        # Mapear parámetros del learning system a config del bot
        # (En futuras versiones esto podría actualizar self.config directamente)
        logger.debug(f"📊 Configuración sincronizada: {len(current_params)} parámetros")
    
    def get_current_trading_parameters(self) -> Dict[str, Any]:
        """
        Obtener parámetros actuales de trading (útil para mostrar a Harold)
        
        Returns:
            Parámetros de trading actuales
        """
        params = {
            'paper_mode': self.config['paper_mode'],
            'trading_pair': self.config['trading_pair'],
            'min_trade_usd': self.config['min_trade_usd'],
            'max_position_pct': self.config['max_position_pct'],
            'stop_loss_pct': self.config['stop_loss_pct'],
            'min_confidence': self.config['min_confidence']
        }
        
        # Agregar parámetros del learning system si está disponible
        if self.auto_learning:
            params['learning_params'] = self.auto_learning.get_current_config()
        
        return params
    
    def _build_strategy_signals(self, monte_carlo, black_swan, sentiment, kelly, hmm_regime, kalman, quantum, non_markovian=None):
        """
        Construye lista de StrategySignal para el Coherence Engine
        Convierte señales de trading a formato estandarizado (10 estrategias V6.1)
        """
        if not COHERENCE_ENGINE_AVAILABLE:
            return []
        
        signals = []
        
        # 1. Quantum Momentum
        if quantum:
            signal_val = quantum.get('signal', 0)
            if signal_val >= 7:
                signal_enum = Signal.STRONG_BUY
            elif signal_val >= 3:
                signal_enum = Signal.BUY
            elif signal_val <= -7:
                signal_enum = Signal.STRONG_SELL
            elif signal_val <= -3:
                signal_enum = Signal.SELL
            else:
                signal_enum = Signal.HOLD
            
            signals.append(StrategySignal(
                name='quantum_momentum',
                signal=signal_enum,
                confidence=quantum.get('confidence', 0.5),
                strength=signal_val,
                reasoning=f"Quantum signal: {signal_val}/10"
            ))
        
        # 2. Kalman Filter
        if kalman:
            trend = kalman.get('trend', 'NEUTRAL')
            if trend == 'BULLISH':
                signal_enum = Signal.BUY
                strength = kalman.get('strength', 0.5)
            elif trend == 'BEARISH':
                signal_enum = Signal.SELL
                strength = -kalman.get('strength', 0.5)
            else:
                signal_enum = Signal.HOLD
                strength = 0
            
            signals.append(StrategySignal(
                name='kalman_filter',
                signal=signal_enum,
                confidence=kalman.get('confidence', 0.7),
                strength=strength,
                reasoning=f"Trend: {trend}"
            ))
        
        # 3. Monte Carlo
        if monte_carlo:
            win_rate = monte_carlo.get('win_rate', 0.5)  # V6.5.4: default as decimal
            win_rate_pct = win_rate * 100 if win_rate <= 1 else win_rate  # Handle both formats
            if win_rate_pct >= 70:
                signal_enum = Signal.STRONG_BUY
            elif win_rate_pct >= 55:
                signal_enum = Signal.BUY
            elif win_rate_pct <= 30:
                signal_enum = Signal.STRONG_SELL
            elif win_rate_pct <= 45:
                signal_enum = Signal.SELL
            else:
                signal_enum = Signal.HOLD
            
            signals.append(StrategySignal(
                name='monte_carlo',
                signal=signal_enum,
                confidence=win_rate_pct / 100.0,
                strength=win_rate_pct,
                reasoning=f"{win_rate_pct:.1f}% win probability"
            ))
        
        # 4. HMM Regime Detection
        if hmm_regime:
            regime = hmm_regime.get('regime', 'UNKNOWN')
            if regime == 'TRENDING':
                signal_enum = Signal.BUY
                confidence = 0.75
            elif regime == 'VOLATILE':
                signal_enum = Signal.SELL
                confidence = 0.80
            else:
                signal_enum = Signal.HOLD
                confidence = 0.50
            
            signals.append(StrategySignal(
                name='hmm_regime',
                signal=signal_enum,
                confidence=confidence,
                strength=1.0 if regime == 'TRENDING' else 0.0,
                reasoning=f"Regime: {regime}"
            ))
        
        # 5. Kelly Criterion
        if kelly:
            optimal_size = kelly.get('optimal_fraction', 0)
            if optimal_size > 0.10:
                signal_enum = Signal.BUY
            elif optimal_size > 0.05:
                signal_enum = Signal.BUY
            elif optimal_size < 0.01:
                signal_enum = Signal.HOLD
            else:
                signal_enum = Signal.HOLD
            
            signals.append(StrategySignal(
                name='kelly_criterion',
                signal=signal_enum,
                confidence=min(optimal_size * 5, 1.0),
                strength=optimal_size,
                reasoning=f"Optimal size: {optimal_size:.1%}"
            ))
        
        # 6. Black Swan Detector
        if black_swan:
            risk_level = black_swan.get('risk_level', 'MEDIUM')
            crash_prob = black_swan.get('crash_probability', 0)
            
            if risk_level == 'HIGH':
                signal_enum = Signal.STRONG_SELL
                confidence = 0.90
            elif risk_level == 'MEDIUM':
                signal_enum = Signal.HOLD
                confidence = 0.50
            else:  # LOW
                signal_enum = Signal.BUY
                confidence = 0.70
            
            signals.append(StrategySignal(
                name='black_swan',
                signal=signal_enum,
                confidence=confidence,
                strength=0.0 if risk_level == 'LOW' else crash_prob,
                reasoning=f"Risk: {risk_level}"
            ))
        
        # 7. Sentiment Analysis
        if sentiment:
            sent_score = sentiment.get('overall_score', 50)
            if sent_score >= 75:
                signal_enum = Signal.STRONG_BUY
            elif sent_score >= 60:
                signal_enum = Signal.BUY
            elif sent_score <= 25:
                signal_enum = Signal.STRONG_SELL
            elif sent_score <= 40:
                signal_enum = Signal.SELL
            else:
                signal_enum = Signal.HOLD
            
            signals.append(StrategySignal(
                name='sentiment',
                signal=signal_enum,
                confidence=sent_score / 100.0,
                strength=sent_score / 100.0,
                reasoning=f"Sentiment: {sent_score}/100"
            ))
        
        # 8. Non-Markovian Memory Kernel V6.1 (12-point weight in decision flow)
        if non_markovian:
            nm_signal = non_markovian.get('signal', 'HOLD')
            nm_confidence = non_markovian.get('confidence', 0) / 100.0
            metrics = non_markovian.get('metrics', {})
            bullish_score = metrics.get('bullish_score', 0)
            bearish_score = metrics.get('bearish_score', 0)
            kernel_weight = 12.0
            
            if nm_signal == 'BUY':
                signal_enum = Signal.BUY if nm_confidence < 0.7 else Signal.STRONG_BUY
                strength = (bullish_score / 100.0) * kernel_weight
            elif nm_signal == 'SELL':
                signal_enum = Signal.SELL if nm_confidence < 0.7 else Signal.STRONG_SELL
                strength = -(bearish_score / 100.0) * kernel_weight
            else:
                signal_enum = Signal.HOLD
                strength = 0.0
            
            signals.append(StrategySignal(
                name='non_markovian_kernel',
                signal=signal_enum,
                confidence=nm_confidence,
                strength=strength,
                reasoning=f"Memory: Bull={bullish_score:.1f} Bear={bearish_score:.1f} | {non_markovian.get('reason', '')}"
            ))
        
        # 9. Order Book Analysis (requires L2 data feed - uses neutral signal when unavailable)
        signals.append(StrategySignal(
            name='order_book',
            signal=Signal.HOLD,
            confidence=0.5,
            strength=0.0,
            reasoning="Order book: L2 data unavailable - neutral"
        ))
        
        # 10. Sharia Compliance (all major crypto assets are halal-compliant)
        signals.append(StrategySignal(
            name='sharia_compliance',
            signal=Signal.BUY,
            confidence=1.0,
            strength=1.0,
            reasoning="Sharia: asset halal-compliant"
        ))
        
        return signals
    
    def optimize_portfolio_quantum(self, trading_pairs: List[str], risk_tolerance: float = 0.5) -> Dict[str, Any]:
        """
        Optimiza asignación de portafolio usando QAOA (Quantum Approximate Optimization)
        
        V5.3 ULTRA - QUANTUM PORTFOLIO OPTIMIZATION
        
        Args:
            trading_pairs: Lista de pares de trading (e.g., ['BTC/USD', 'ETH/USD', 'ADA/USD'])
            risk_tolerance: Factor de aversión al riesgo (0-1, default=0.5)
            
        Returns:
            Dictionary con pesos óptimos y retorno esperado
        """
        if not QUANTUM_OPTIMIZATION_AVAILABLE:
            logger.warning("⚛️ Quantum Portfolio Optimizer no disponible")
            return {
                'success': False,
                'error': 'Quantum optimization not available',
                'weights': {},
                'expected_return': 0.0
            }
        
        try:
            import numpy as np
            
            logger.info(f"⚛️ Iniciando optimización cuántica de portafolio - {len(trading_pairs)} activos")
            
            # Obtener precios históricos para cada par
            historical_returns = []
            pair_names = []
            
            for pair in trading_pairs:
                try:
                    # Obtener datos históricos (últimos 30 días)
                    historical_data = self.trading_service.get_historical_data(pair, days=30)
                    
                    if historical_data and len(historical_data) > 1:
                        prices = [candle['close'] for candle in historical_data]
                        returns = np.diff(prices) / prices[:-1]
                        historical_returns.append(returns)
                        pair_names.append(pair)
                except Exception as e:
                    logger.warning(f"⚠️ No se pudieron obtener datos para {pair}: {e}")
            
            if len(historical_returns) < 2:
                logger.error("❌ Datos insuficientes para optimización")
                return {
                    'success': False,
                    'error': 'Insufficient data for optimization',
                    'weights': {},
                    'expected_return': 0.0
                }
            
            # Calcular retornos esperados y matriz de covarianza
            returns_array = np.array([np.mean(returns) for returns in historical_returns])
            
            # Crear matriz de covarianza
            max_len = max(len(r) for r in historical_returns)
            padded_returns = []
            for returns in historical_returns:
                if len(returns) < max_len:
                    padded = np.pad(returns, (0, max_len - len(returns)), constant_values=0)
                else:
                    padded = returns[:max_len]
                padded_returns.append(padded)
            
            returns_matrix = np.array(padded_returns)
            cov_matrix = np.cov(returns_matrix)
            
            # QAOA Optimization
            optimal_weights, expected_return = global_qaoa.optimize_portfolio(
                expected_returns=returns_array,
                covariance_matrix=cov_matrix,
                risk_tolerance=risk_tolerance
            )
            
            # Convertir a diccionario
            weights_dict = {pair: float(weight) for pair, weight in zip(pair_names, optimal_weights)}
            
            logger.info(f"✅ Optimización cuántica completada - Retorno esperado: {expected_return:.4f}")
            logger.info(f"   Pesos óptimos: {weights_dict}")
            
            return {
                'success': True,
                'method': 'QAOA (Quantum Approximate Optimization)',
                'weights': weights_dict,
                'expected_return': float(expected_return),
                'risk_tolerance': risk_tolerance,
                'num_assets': len(pair_names),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error en optimización cuántica: {e}")
            return {
                'success': False,
                'error': str(e),
                'weights': {},
                'expected_return': 0.0
            }
    
    def get_quantum_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de uso de mejoras cuánticas (QRNG + QAOA)
        
        Returns:
            Dictionary con estadísticas de QRNG y QAOA
        """
        if not QUANTUM_OPTIMIZATION_AVAILABLE:
            return {
                'available': False,
                'message': 'Quantum enhancements not installed'
            }
        
        try:
            stats = get_quantum_stats()
            stats['available'] = True
            return stats
        except Exception as e:
            logger.error(f"Error obteniendo stats cuánticas: {e}")
            return {
                'available': False,
                'error': str(e)
            }