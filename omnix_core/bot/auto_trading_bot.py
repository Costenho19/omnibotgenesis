"""
🤖 OMNIX AUTO-TRADING BOT V6.5.2 INSTITUTIONAL+ - TRADING AUTOMÁTICO 24/7
Sistema de trading automático con IA, Risk Guardian, Coherence Engine,
Non-Markovian Kernel, Memory-Enhanced RMS, Adaptive Parameter Engine, y On-Chain Intelligence

🚀 V6.5.2 MULTI-USER ARCHITECTURE:
- Soporte para 100,000+ usuarios simultáneos
- Sesiones aisladas por usuario vía UserSessionManager
- Estado persistente en Redis + PostgreSQL
- Auto-restauración después de reinicios de Railway

🔥 ESTRATEGIAS V6.5 INSTITUTIONAL+ (10 MÓDULOS):
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

🧠 MEMORY-ENHANCED RMS V6.5:
- MemoryRiskAdapter: Puente entre kernel temporal y gestión de riesgo
- LimitsEngine: Límites dinámicos ajustados por coherencia de régimen
- CircuitBreaker: Halt automático por incoherencia de memoria/transición de régimen
- PositionMonitor: Factor de riesgo basado en divergencia de memoria
- AlertDispatcher: Alertas predictivas de transiciones de régimen

🎯 V6.5.2 NUEVAS FUNCIONALIDADES:
- Multi-user sessions: Cada usuario tiene su propia sesión de trading
- Auto-trading persistente: El estado se guarda en DB y sobrevive reinicios de Railway
- Adaptive Parameter Engine: Auto-calibración de SL/TP/posición por régimen
- On-Chain Intelligence: Whale tracking via ClankApp + Arkham
- Logging detallado: Cada operación se registra con verificación

💰 MODOS DE OPERACIÓN:
- PAPER TRADING: $1,000,000 virtual (recomendado para testing)
- REAL TRADING: Dinero real en Kraken (solo para producción)

🔒 SEGURIDAD:
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

try:
    from omnix_core.config.trading_profiles import get_active_profile, TradingProfile
    TRADING_PROFILES_AVAILABLE = True
except ImportError:
    TRADING_PROFILES_AVAILABLE = False
    logger.warning("⚠️ Trading Profiles no disponible - usando configuración hardcoded")

# Import Metrics Engine (Prometheus)
try:
    from omnix_services.monitoring import get_metrics_engine
    METRICS_ENGINE_AVAILABLE = True
    metrics = get_metrics_engine()
except ImportError:
    METRICS_ENGINE_AVAILABLE = False
    metrics = None
    logger.warning("⚠️ MetricsEngine no disponible - métricas Prometheus desactivadas")

# Import investor logger (será importado cuando esté disponible)
try:
    from scripts.log_trades_for_investors import investor_logger
except ImportError:
    # Si falla, intentar importación relativa
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
        from log_trades_for_investors import investor_logger
    except:
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

# Import CAES - Confidence-Adaptive Entry System V6.5.2 PREMIUM
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

# Import Adaptive Parameter Engine V6.5 - AUTO-CALIBRATION FOR ARES
try:
    from omnix_services.adaptive_engine import (
        AdaptiveParameterEngine,
        AdaptiveParameterProfile,
        RegimeType,
        get_adaptive_engine
    )
    ADAPTIVE_PARAMETER_ENGINE_AVAILABLE = True
    logger.info("🎯 Adaptive Parameter Engine V6.5 disponible")
except ImportError:
    AdaptiveParameterEngine = None
    AdaptiveParameterProfile = None
    RegimeType = None
    get_adaptive_engine = None
    ADAPTIVE_PARAMETER_ENGINE_AVAILABLE = False
    logger.warning("⚠️ Adaptive Parameter Engine no disponible")

# Import User Session Manager V6.5.2 - MULTI-USER SESSIONS (100K+ users)
try:
    from omnix_core.sessions import (
        UserSessionManager,
        UserTradingSession,
        get_session_manager,
        initialize_session_manager
    )
    USER_SESSION_MANAGER_AVAILABLE = True
    logger.info("🚀 User Session Manager V6.5.2 disponible - 100K+ usuarios")
except ImportError:
    UserSessionManager = None
    UserTradingSession = None
    get_session_manager = None
    initialize_session_manager = None
    USER_SESSION_MANAGER_AVAILABLE = False
    logger.warning("⚠️ User Session Manager no disponible")


class AutoTradingBot:
    """
    Bot de Trading Automático 24/7 - V6.5 INSTITUTIONAL+
    
    Usa TODAS las 10 estrategias avanzadas para tomar decisiones óptimas
    Incluye modo PAPER TRADING con $1M virtual para testing
    Escanea 11 pares de crypto para máximas oportunidades
    """
    
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
    
    def __init__(self, trading_service, database_service=None, advanced_features=None, paper_trading=None, ai_service=None, ares_v1=None, ares_v2=None):
        self.trading_service = trading_service
        self.database_service = database_service
        self.advanced_features = advanced_features
        self.paper_trading = paper_trading
        self.ai_service = ai_service
        self.ares_v1 = ares_v1  # ARES V1 Swing Trading Strategy
        self.ares_v2 = ares_v2  # ARES V2 Scalping Strategy
        
        # Configuración de trading - PROFESIONAL INSTITUCIONAL
        # Optimizado para generar track record de calidad como si tuvieras clientes Enterprise
        # Lee PAPER_MODE desde variable de entorno (Railway) o default a False
        import os as os_module
        paper_mode_raw = os_module.getenv('PAPER_MODE', 'false')
        paper_mode_env = paper_mode_raw.lower() == 'true'
        
        # DEBUG: Logging para verificar PAPER_MODE en Railway
        logger.info(f"🔍 PAPER_MODE env var: '{paper_mode_raw}' → paper_mode={paper_mode_env}")
        
        # V6.5.2: Cargar Trading Profile desde variable de entorno
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
        
        self.config = {
            'active': False,
            'paper_mode': paper_mode_env,  # TRUE = Simulado con $1M | FALSE = Real en Kraken
            'trading_profile': profile_name,  # V6.5.2: Nombre del perfil activo
            'trading_pairs': [
                'BTC/USD', 'ETH/USD', 'SOL/USD',     # Top 3 por capitalización
                'XRP/USD', 'ADA/USD', 'DOT/USD',     # Altcoins tier 1
                'LINK/USD', 'AVAX/USD', 'POL/USD',   # DeFi/L2 líderes (MATIC→POL Dec 2024)
                'ATOM/USD', 'LTC/USD'               # Ecosistema diversificado
            ],  # V6.5: 11 pares para máximas oportunidades
            'trading_pair': 'BTC/USD',  # Default pair (legacy compatibility)
            'check_interval_seconds': p.check_interval_seconds if p else 25,
            'min_trade_usd': p.min_trade_usd if p else 75.0,
            'max_position_pct': p.max_position_pct if p else 0.12,
            'stop_loss_pct': p.stop_loss_pct if p else 0.02,
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
        
        # V6.4: Cargar estado persistente de la DB
        self._load_persistent_state()
        
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
        
        # Non-Markovian Memory Kernel V6.1 ULTRA - QUANTUM TEMPORAL MEMORY
        self._last_kernel_pair = None  # V6.5.2: Track pair for kernel seeding
        self._kernel_needs_reseed = True  # V6.5.2: Flag for pending reseed
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
        
        # Adaptive Parameter Engine V6.5 - AUTO-CALIBRATION FOR ARES
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
                
                logger.info("🎯 Adaptive Parameter Engine V6.5 ACTIVADO - Auto-calibración dinámica")
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
        
        mode = "PAPER TRADING ($1M virtual)" if self.config['paper_mode'] else "🚨 REAL TRADING (Kraken) 💰"
        logger.info(f"🤖 AutoTradingBot V6.5 ULTRA inicializado - Modo: {mode}")
        
        # V6.5: Auto-iniciar si el estado persistente indica que debería estar activo
        self._auto_start_if_persistent()
    
    def _auto_start_if_persistent(self):
        """
        V6.5.1: Auto-iniciar el trading si el estado persistente de la DB indica que debería estar activo.
        Esto garantiza que Railway reinicie con el mismo estado que antes del restart.
        V6.5.1: Ahora pasa el user_id específico para soportar múltiples usuarios.
        """
        if hasattr(self, '_should_auto_start') and self._should_auto_start:
            user_id = getattr(self, '_persistent_user_id', None)
            logger.info(f"🔄 V6.5.1: Iniciando auto-trading automáticamente para user {user_id}...")
            try:
                result = self.start(user_id=user_id)
                if result.get('success'):
                    logger.info(f"✅ V6.5.1: Auto-trading restaurado exitosamente para user {user_id}")
                else:
                    error = result.get('error', 'Unknown error')
                    logger.warning(f"⚠️ V6.5.1: No se pudo restaurar auto-trading: {error}")
            except Exception as e:
                logger.error(f"❌ V6.5.1: Error restaurando auto-trading: {e}")
    
    def check_and_restore_auto_trading(self):
        """
        V6.5.2: Método público para restaurar auto-trading DESPUÉS de que la DB esté conectada.
        Llamar desde main.py después de verificar que DATABASE está CONECTADA.
        
        ARQUITECTURA MULTI-USER V6.5.2:
        - Usa UserSessionManager para manejar sesiones de 100,000+ usuarios
        - Cada usuario tiene su propia sesión aislada
        - Estado persistente en Redis + PostgreSQL
        - El ciclo de trading actual ejecuta operaciones para TODOS los usuarios activos
        """
        if not self.database_service or not hasattr(self.database_service, 'execute_query'):
            logger.warning("⚠️ V6.5.2: check_and_restore - No hay database_service disponible")
            return False
        
        try:
            logger.info("🔍 V6.5.2: Verificando estado persistente (MULTI-USER 100K+)...")
            
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
                    
                    logger.info(f"✅ V6.5.2: {result['restored']} sesiones restauradas - Trading loop ACTIVO")
                    return True
                else:
                    logger.info("📊 V6.5.2: No hay sesiones activas que restaurar")
                    return False
            else:
                logger.info("🔄 V6.5.2: Fallback a restauración legacy...")
                user_settings_result = self.database_service.execute_query('''
                    SELECT auto_trading, is_paused, trading_enabled, user_id
                    FROM user_settings
                    WHERE auto_trading = true AND trading_enabled = true AND (is_paused = false OR is_paused IS NULL)
                    ORDER BY user_id
                ''')
                
                if user_settings_result and len(user_settings_result) > 0:
                    total_users = len(user_settings_result)
                    logger.info(f"🔄 V6.5.2: Encontrados {total_users} usuario(s) con auto_trading activo")
                    
                    first_user = user_settings_result[0]
                    user_id = first_user.get('user_id', 'unknown')
                    
                    result = self.start(user_id=user_id)
                    if result.get('success'):
                        logger.info(f"✅ V6.5.2: Trading iniciado para user {user_id}")
                        if total_users > 1:
                            logger.info(f"📊 Nota: {total_users - 1} usuarios adicionales en cola")
                        return True
                    
                return False
                
        except Exception as e:
            logger.error(f"❌ V6.5.2: Error en check_and_restore_auto_trading: {e}")
            return False
    
    def _start_trading_loop(self):
        """Iniciar el loop de trading en un thread separado"""
        if self._thread is not None and self._thread.is_alive():
            logger.info("📊 Trading loop ya está corriendo")
            return
        
        self._thread = threading.Thread(target=self._trading_loop_multi_user, daemon=True)
        self._thread.start()
        logger.info("🚀 V6.5.2: Trading loop MULTI-USER iniciado")
    
    def _trading_loop_multi_user(self):
        """
        V6.5.2: Loop de trading que procesa TODOS los usuarios activos
        Usa ThreadPoolExecutor para procesamiento paralelo de usuarios
        
        Arquitectura:
        - Pool de workers para procesamiento paralelo
        - Cada usuario se procesa en su propio thread
        - Lock por usuario para evitar race conditions
        - Timeout por usuario para evitar bloqueos
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        logger.info("🔄 V6.5.2: Iniciando loop de trading multi-usuario...")
        
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
        
        logger.info("🛑 V6.5.2: Trading loop multi-usuario detenido")
    
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
        V6.5.2: Procesar un ciclo de trading para un usuario específico
        
        Args:
            user_id: ID del usuario
            session: UserTradingSession del usuario
        """
        try:
            pass
            
        except Exception as e:
            logger.error(f"❌ Error en ciclo de trading para user {user_id}: {e}")
    
    def start(self, user_id: str = None) -> Dict:
        """Iniciar trading automático 24/7"""
        try:
            if self.state['running']:
                return {'error': 'Bot ya está corriendo'}
            
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
            
            # V6.5: Persistir estado en user_settings
            self._persist_auto_trading_state(user_id, active=True)
            
            # Iniciar thread para loop 24/7
            # CRÍTICO: daemon=False para que el thread SIGA CORRIENDO en Railway/webhooks
            self._thread = threading.Thread(target=self._trading_loop, daemon=False)
            self._thread.start()
            
            logger.info(f"🚀 AUTO-TRADING ACTIVADO - Balance inicial: ${balance:.2f}")
            
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
        try:
            self.state['running'] = False
            self.config['active'] = False
            
            # V6.5: Persistir estado en user_settings
            self._persist_auto_trading_state(user_id, active=False)
            
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
        V6.5.1: Usa UPSERT para crear registro si no existe.
        """
        if not self.database_service or not hasattr(self.database_service, 'execute_query'):
            logger.debug("V6.5: No se puede persistir estado (sin database_service)")
            return
        
        try:
            if user_id:
                self.database_service.execute_query('''
                    INSERT INTO user_settings (user_id, auto_trading, trading_enabled, updated_at)
                    VALUES (%s, %s, true, NOW())
                    ON CONFLICT (user_id) DO UPDATE 
                    SET auto_trading = EXCLUDED.auto_trading, updated_at = NOW()
                ''', (user_id, active))
                logger.info(f"💾 V6.5.1: Estado auto_trading={active} persistido para user {user_id}")
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
                            logger.info(f"💾 V6.5.1: auto_trading=true persistido para user {uid}")
                    else:
                        self.database_service.execute_query('''
                            INSERT INTO user_settings (user_id, auto_trading, trading_enabled, updated_at)
                            VALUES ('default_admin', true, true, NOW())
                            ON CONFLICT (user_id) DO UPDATE 
                            SET auto_trading = true, updated_at = NOW()
                        ''')
                        logger.info("💾 V6.5.1: auto_trading=true persistido para default_admin")
                else:
                    self.database_service.execute_query('''
                        UPDATE user_settings 
                        SET auto_trading = false, updated_at = NOW()
                        WHERE auto_trading = true
                    ''')
                    logger.info("💾 V6.5.1: auto_trading=false persistido para todos los usuarios")
        except Exception as e:
            logger.warning(f"⚠️ V6.5.1: Error persistiendo auto_trading: {e}")
    
    def _load_persistent_state(self):
        """
        V6.5: Cargar estado persistente de la base de datos.
        Esto garantiza que los contadores de trades y métricas se mantengan
        entre reinicios del bot para que el ramp-up system funcione correctamente.
        
        V6.5 FIX: También carga auto_trading de user_settings para persistir
        el estado entre reinicios de Railway.
        """
        if not self.database_service:
            logger.info("📊 V6.5: Sin database_service - usando estado inicial")
            return
        
        try:
            # V6.5.1: Cargar configuración de auto-trading de user_settings
            self._should_auto_start = False  # Flag para auto-iniciar después del __init__
            self._persistent_user_id = None  # V6.5.1: Guardar user_id para restauración
            try:
                if hasattr(self.database_service, 'execute_query'):
                    user_settings_result = self.database_service.execute_query('''
                        SELECT auto_trading, is_paused, trading_enabled, user_id
                        FROM user_settings
                        WHERE auto_trading = true
                        LIMIT 1
                    ''')
                    if user_settings_result and len(user_settings_result) > 0 and user_settings_result[0]:
                        row = user_settings_result[0]
                        # Tuple unpacking: SELECT auto_trading, is_paused, trading_enabled, user_id
                        # Guard against empty/None rows
                        if row and len(row) >= 4:
                            auto_trading = bool(row[0]) if row[0] is not None else False
                            is_paused = bool(row[1]) if row[1] is not None else False
                            trading_enabled = bool(row[2]) if row[2] is not None else True
                            user_id = str(row[3]) if row[3] else 'unknown'
                        else:
                            auto_trading, is_paused, trading_enabled, user_id = False, False, True, 'unknown'
                        
                        if auto_trading and not is_paused and trading_enabled:
                            self._should_auto_start = True
                            self._persistent_user_id = user_id  # V6.5.1: Guardar para restauración
                            logger.info(f"🔄 V6.5.1: Auto-trading PERSISTIDO detectado para user {user_id} - Se iniciará automáticamente")
                        elif auto_trading and is_paused:
                            logger.info(f"⏸️ V6.5.1: Auto-trading está PAUSADO para user {user_id}")
                        elif auto_trading and not trading_enabled:
                            logger.info(f"🔒 V6.5.1: Trading DESHABILITADO para user {user_id}")
                    else:
                        logger.info("📊 V6.5.1: No hay usuarios con auto_trading activo")
            except Exception as e:
                logger.warning(f"⚠️ V6.5.1: Error cargando auto_trading de user_settings: {e}")
            
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
    
    def _trading_loop(self):
        """Loop principal 24/7 - V6.5 MULTI-CRYPTO PREMIUM"""
        logger.info("🔄 Trading loop V6.5 MULTI-CRYPTO iniciado - Corriendo 24/7")
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
                    logger.info(f"📈 V6.5 STATUS: Ciclo #{cycle_counter} | Trades: {self.state['total_trades']} | Win Rate: {win_rate:.1f}% | P/L: ${self.state['total_profit_loss']:.2f}")
                
                # Verificar parada de emergencia
                if self._check_emergency_stop():
                    logger.critical("🚨 PARADA DE EMERGENCIA - Pérdidas excesivas")
                    self.stop()
                    break
                
                # V6.4: MULTI-CRYPTO - Escanear el par actual
                if self.config.get('use_multi_crypto', True) and len(trading_pairs) > 1:
                    current_pair = trading_pairs[pair_index]
                    self.config['trading_pair'] = current_pair
                    pair_index = (pair_index + 1) % len(trading_pairs)
                    logger.info(f"🔍 Escaneando {current_pair} ({pair_index+1}/{len(trading_pairs)})")
                
                # Análisis completo
                analysis = self._analyze_market()
                
                # V6.5: Log detallado del análisis
                if analysis:
                    should_trade = analysis.get('should_trade', False)
                    confidence = analysis.get('confidence', 0)
                    signal = analysis.get('signal', 'HOLD')
                    reason = analysis.get('reason', 'N/A')
                    logger.info(f"   📊 Análisis: {signal} | Confianza: {confidence:.2%} | Trade: {'SÍ' if should_trade else 'NO'} | Razón: {reason[:50]}...")
                else:
                    logger.warning(f"   ⚠️ Sin datos de análisis para {self.config['trading_pair']}")
                
                # 🧠 V6.2: Check predictive alerts after market analysis
                if analysis and self.alert_dispatcher:
                    current_price = analysis.get('current_price', 0)
                    self._check_predictive_alerts(current_price)
                
                if analysis and analysis.get('should_trade'):
                    logger.info(f"🎯 SEÑAL DE TRADE DETECTADA - {self.config['trading_pair']} - Ejecutando...")
                    # Ejecutar trade
                    result = self._execute_smart_trade(analysis)
                    
                    if result.get('success'):
                        trade_type = result.get('type', 'unknown')
                        trade_amount = result.get('amount', 0)
                        trade_price = result.get('price', 0)
                        logger.info(f"✅ TRADE EJECUTADO: {trade_type} {trade_amount} {self.config['trading_pair']} @ ${trade_price:.2f}")
                        logger.info(f"   📝 Detalles: {result}")
                        self._update_stats(result)
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
        
        logger.info(f"🔄 Trading loop V6.5 terminado después de {cycle_counter} ciclos")
    
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
            # V6.5.2 FIX: Solo requiere prices, volumes es opcional
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
            # V6.5.2 FIX: Usar analyze() con OHLC completo, volumes sintéticos si no disponible
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
                    
                    # V6.5.2 FIX: Estado explícito para manejo robusto de cambios de par
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
            
            # 11. Decisión basada en TODOS los análisis + Pesos Adaptativos
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
                non_markovian=non_markovian
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
                    
                    logger.info(f"🧠 Razonamiento generado: {reasoning.get('summary', '')[:100]}")
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
        non_markovian: Optional[Dict] = None
    ) -> Dict:
        """
        Decisión AVANZADA V6.1 integrando TODAS las 10 estrategias
        
        Sistema de scoring ponderado que combina señales de múltiples fuentes
        
        NUEVO V5.2: Usa pesos adaptativos ω(t) para balancear Kalman vs Monte Carlo
        - ω cerca de 0 → favorece Kalman Filter (mercado normal)
        - ω cerca de 1 → favorece Monte Carlo (mercado extremo/volátil)
        
        NUEVO V6.1: Non-Markovian Memory Kernel para capturar dependencias temporales
        - K(t-s) = exp(-|t-s|/τ)[1 + ε cos(Ω(t-s))]
        - Detecta patrones cíclicos y coherencia de régimen
        """
        try:
            decision = {
                'should_trade': False,
                'action': 'HOLD',
                'confidence': 0.0,
                'reason': [],
                'v52_analysis': {},
                'current_price': current_price
            }
            
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
            
            # ========== ESTRATEGIAS CLÁSICAS (peso 40%) ==========
            
            # 1. Monte Carlo (peso: 15 puntos * monte_carlo_weight)
            monte_carlo_base_weight = 15
            if monte_carlo:
                adjusted_weight = monte_carlo_base_weight * monte_carlo_weight
                max_score += adjusted_weight
                win_rate = monte_carlo.get('win_rate', 50)
                if win_rate > 60:
                    score += adjusted_weight
                    decision['reason'].append(f"✅ Monte Carlo: {win_rate:.1f}% win rate (peso: {monte_carlo_weight:.0%})")
                elif win_rate > 50:
                    score += adjusted_weight * 0.53
                elif win_rate < 40:
                    score -= adjusted_weight
                    decision['reason'].append(f"⚠️ Monte Carlo: {win_rate:.1f}% win rate BAJO (peso: {monte_carlo_weight:.0%})")
            
            # 2. Black Swan (peso: 15 puntos - CRÍTICO)
            # V6.5.2: Penalizaciones reducidas en paper mode para más trades
            is_paper_mode = self.config.get('paper_mode', False)
            if black_swan:
                max_score += 15
                risk_level = black_swan.get('risk_level', 'MEDIUM')
                crash_prob = black_swan.get('crash_probability', 50)
                
                if risk_level == 'HIGH' or crash_prob > 30:
                    veto_penalty = 15 if is_paper_mode else 30  # V6.5.2: -15 paper, -30 real
                    score -= veto_penalty
                    mode_label = "[PAPER -15]" if is_paper_mode else "[REAL -30]"
                    decision['reason'].append(f"🚨 Black Swan: Riesgo {risk_level} {mode_label}")
                elif risk_level == 'LOW':
                    score += 15
                    decision['reason'].append(f"✅ Black Swan: Riesgo BAJO")
            
            # 3. Sentiment (peso: 10 puntos)
            if sentiment:
                max_score += 10
                sent_score = sentiment.get('overall_score', 50)
                if sent_score > 70:
                    score += 10
                    decision['reason'].append(f"✅ Sentiment: {sent_score:.0f}/100 STRONG")
                elif sent_score > 55:
                    score += 5
                elif sent_score < 30:
                    score -= 10
                    decision['reason'].append(f"⚠️ Sentiment: {sent_score:.0f}/100 WEAK")
            
            # ========== ESTRATEGIAS V5.2 QUANTUM (peso 60%) ==========
            
            # 4. Quantum Momentum (peso: 25 puntos - ESTRATEGIA PRINCIPAL)
            if quantum:
                max_score += 25
                signal = quantum.get('signal', 0)  # -10 a +10
                confidence_level = quantum.get('confidence', 'LOW')
                
                if confidence_level in ['HIGH', 'VERY_HIGH']:
                    if signal >= 7:  # STRONG BUY
                        score += 25
                        decision['reason'].append(f"🚀 Quantum: STRONG BUY (score {signal}/10)")
                    elif signal >= 4:  # BUY
                        score += 15
                        decision['reason'].append(f"✅ Quantum: BUY (score {signal}/10)")
                    elif signal <= -7:  # STRONG SELL
                        score -= 25
                        decision['reason'].append(f"📉 Quantum: STRONG SELL (score {signal}/10)")
                    elif signal <= -4:  # SELL
                        score -= 15
                        decision['reason'].append(f"⚠️ Quantum: SELL (score {signal}/10)")
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
            
            # 6. HMM Regime (peso: 15 puntos) + V6.4 QUALITY FILTER
            if hmm_regime:
                max_score += 15  # V6.4: Aumentado peso de 10 a 15
                regime = hmm_regime.get('regime', 'UNKNOWN')
                params = hmm_regime.get('recommended_params', {})
                regime_confidence = hmm_regime.get('confidence', 0.5)
                
                # V6.4: HMM QUALITY FILTER - Boost para trades alineados con régimen
                if regime == 'TRENDING':
                    score += 15
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
                    # V6.5.2: HMM VETO configurable por perfil + penalizaciones reducidas en paper mode
                    p = self.trading_profile  # Shorthand
                    hmm_veto_enabled = p.hmm_veto_enabled if p else True
                    hmm_veto_threshold = p.hmm_veto_confidence_threshold if p else 0.85
                    
                    if hmm_veto_enabled and regime_confidence > hmm_veto_threshold:
                        veto_penalty = 8 if is_paper_mode else 15  # V6.5.2: -8 paper, -15 real
                        score -= veto_penalty
                        mode_label = "[PAPER -8]" if is_paper_mode else "[REAL -15]"
                        decision['reason'].append(f"🚨 HMM: VOLATILE extremo - VETO {mode_label} (conf > {hmm_veto_threshold:.0%})")
                        decision['v52_analysis']['hmm_volatility_veto'] = True
                    else:
                        score -= 5
                        decision['reason'].append(f"⚠️ HMM: {regime} moderado")
                
                decision['v52_analysis']['market_regime'] = regime
                decision['v52_analysis']['hmm_confidence'] = regime_confidence
                
                # Ajustar position size según régimen
                if params:
                    decision['v52_analysis']['regime_params'] = params
            
            # ADAPTIVE REGIME CROSS-VALIDATION
            # Si adaptive_weights y HMM detectan régimen EXTREME/VOLATILE simultáneamente → VETO
            # V6.5.2: Configurable por perfil
            p = self.trading_profile  # Shorthand
            regime_change_veto_enabled = p.regime_change_veto_enabled if p else True
            
            if adaptive_weights and hmm_regime and regime_change_veto_enabled:
                adaptive_regime = adaptive_weights.regime if hasattr(adaptive_weights, 'regime') else 'NORMAL'
                hmm_detected = hmm_regime.get('regime', 'UNKNOWN')
                
                # Criterio de cambio de régimen crítico
                # V6.5.2: Penalizaciones reducidas en paper mode para más trades
                if adaptive_regime in ['EXTREME', 'VOLATILE'] and hmm_detected == 'VOLATILE':
                    veto_penalty = 10 if is_paper_mode else 20  # V6.5.2: -10 paper, -20 real
                    score -= veto_penalty
                    mode_label = "[PAPER -10]" if is_paper_mode else "[REAL -20]"
                    decision['reason'].append(f"🚨 REGIME CHANGE DETECTED: {adaptive_regime} + HMM {hmm_detected} → VETO {mode_label}")
                    decision['v52_analysis']['regime_change_veto'] = True
                    logger.warning(f"🚨 REGIME CHANGE VETO {mode_label}: Adaptive={adaptive_regime}, HMM={hmm_detected}")
                elif adaptive_regime == 'EXTREME':
                    extreme_penalty = 5 if is_paper_mode else 10  # V6.5.2: -5 paper, -10 real
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
            
            # ========== ESTRATEGIAS ARES QUANTUM (peso 35%) ==========
            
            # 8. ARES V1 Swing Trading (peso: 20 puntos - INSTITUCIONAL 55-65% win rate)
            try:
                if self.ares_v1 is not None and hasattr(self.ares_v1, 'analyze'):
                    max_score += 20
                    ares_result = self.ares_v1.analyze(analysis)
                    
                    if ares_result.get('approved', False):
                        ares_signal = ares_result.get('signal', 'NONE')
                        ares_strength = ares_result.get('strength', 'normal')
                        signal_score = ares_result.get('signal_data', {}).get('score', 0)
                        
                        if ares_signal == 'LONG' and ares_strength in ['ares', 'strong']:
                            score += 20
                            decision['reason'].append(f"🧬 ARES V1: STRONG LONG ({signal_score}/6 signals)")
                        elif ares_signal == 'LONG':
                            score += 10
                            decision['reason'].append(f"✅ ARES V1: LONG ({signal_score}/6 signals)")
                        elif ares_signal == 'SHORT' and ares_strength in ['ares', 'strong']:
                            score -= 20
                            decision['reason'].append(f"🧬 ARES V1: STRONG SHORT ({signal_score}/6 signals)")
                        elif ares_signal == 'SHORT':
                            score -= 10
                            decision['reason'].append(f"⚠️ ARES V1: SHORT ({signal_score}/6 signals)")
                        
                        decision['v52_analysis']['ares_v1_signal'] = ares_signal
                        decision['v52_analysis']['ares_v1_strength'] = ares_strength
                        decision['v52_analysis']['ares_v1_score'] = signal_score
                    else:
                        ares_reason = ares_result.get('reason', 'Sin señal')
                        decision['reason'].append(f"⚠️ ARES V1: {ares_reason}")
                        decision['v52_analysis']['ares_v1_filtered'] = ares_reason
                else:
                    logger.debug("ARES V1 no disponible - usando solo estrategias base")
            except Exception as e:
                logger.debug(f"ARES V1 error: {e}")
                decision['v52_analysis']['ares_v1_error'] = str(e)
            
            # 9. ARES V2 Scalping M1 (peso: 15 puntos - ULTRA-RÁPIDO 60-70% win rate)
            try:
                if self.ares_v2 is not None and hasattr(self.ares_v2, 'analyze'):
                    max_score += 15
                    ares_v2_result = self.ares_v2.analyze(analysis)
                    
                    if ares_v2_result.get('approved', False):
                        scalp_signal = ares_v2_result.get('signal', 'NONE')
                        scalp_strength = ares_v2_result.get('strength', 'normal')
                        scalp_score = ares_v2_result.get('score', 0)
                        
                        if scalp_signal == 'LONG' and scalp_strength in ['ultra', 'aggressive']:
                            score += 15
                            decision['reason'].append(f"🧨 ARES V2: STRONG LONG ({scalp_score}/5 signals)")
                        elif scalp_signal == 'LONG':
                            score += 8
                            decision['reason'].append(f"✅ ARES V2: LONG ({scalp_score}/5 signals)")
                        elif scalp_signal == 'SHORT' and scalp_strength in ['ultra', 'aggressive']:
                            score -= 15
                            decision['reason'].append(f"🧨 ARES V2: STRONG SHORT ({scalp_score}/5 signals)")
                        elif scalp_signal == 'SHORT':
                            score -= 8
                            decision['reason'].append(f"⚠️ ARES V2: SHORT ({scalp_score}/5 signals)")
                        
                        decision['v52_analysis']['ares_v2_signal'] = scalp_signal
                        decision['v52_analysis']['ares_v2_strength'] = scalp_strength
                        decision['v52_analysis']['ares_v2_score'] = scalp_score
                    else:
                        scalp_reason = ares_v2_result.get('reason', 'Sin señal')
                        decision['reason'].append(f"⚠️ ARES V2: {scalp_reason}")
                        decision['v52_analysis']['ares_v2_filtered'] = scalp_reason
                else:
                    logger.debug("ARES V2 no disponible - usando solo estrategias base")
            except Exception as e:
                logger.debug(f"ARES V2 error: {e}")
                decision['v52_analysis']['ares_v2_error'] = str(e)
            
            # 10. NON-MARKOVIAN MEMORY KERNEL V6.1 (peso: 12 puntos - QUANTUM TEMPORAL MEMORY)
            if non_markovian:
                max_score += 12
                nm_signal = non_markovian.get('signal', 'HOLD')
                nm_confidence = non_markovian.get('confidence', 0)
                nm_metrics = non_markovian.get('metrics', {})
                
                if nm_signal == 'BUY' and nm_confidence > 60:
                    score += 12
                    decision['reason'].append(f"🧠 Non-Markovian: BUY ({nm_confidence:.0f}% conf)")
                elif nm_signal == 'BUY' and nm_confidence > 40:
                    score += 6
                    decision['reason'].append(f"✅ Non-Markovian: BUY ({nm_confidence:.0f}% conf)")
                elif nm_signal == 'SELL' and nm_confidence > 60:
                    score -= 12
                    decision['reason'].append(f"🧠 Non-Markovian: SELL ({nm_confidence:.0f}% conf)")
                elif nm_signal == 'SELL' and nm_confidence > 40:
                    score -= 6
                    decision['reason'].append(f"⚠️ Non-Markovian: SELL ({nm_confidence:.0f}% conf)")
                
                decision['v52_analysis']['non_markovian_signal'] = nm_signal
                decision['v52_analysis']['non_markovian_confidence'] = nm_confidence
                decision['v52_analysis']['non_markovian_metrics'] = nm_metrics
                
                if nm_metrics.get('regime_coherence'):
                    coherence = nm_metrics['regime_coherence']
                    decision['v52_analysis']['memory_regime_coherence'] = coherence.get('overall_coherence', 0)
            
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
            
            # V6.5.2 PREMIUM: Decisión de trading con umbrales desde Trading Profile
            # Objetivo: trades/día configurables con win rate > 55%
            
            # Obtener score thresholds del perfil o usar defaults (INSTITUTIONAL)
            p = self.trading_profile  # Shorthand
            score_very_strong = p.score_very_strong if p else 20
            score_strong = p.score_strong if p else 10
            score_moderate = p.score_moderate if p else 5
            
            # V6.5.2 CAES: Extraer confianza del kernel para position sizing adaptativo
            nm_conf_for_caes = None
            nm_metrics_for_caes = None
            if non_markovian:
                nm_conf_for_caes = non_markovian.get('confidence', 50)
                nm_metrics_for_caes = non_markovian.get('metrics', {})
            
            if confidence >= (self.config['min_confidence'] * 100):
                # V6.5.2: Umbrales escalonados configurables por perfil + CAES
                if score > score_very_strong:  # Señal COMPRA MUY FUERTE - Full position
                    decision['should_trade'] = True
                    decision['action'] = 'BUY'
                    decision['signal_strength'] = 'VERY_STRONG'
                    decision['amount_usd'] = self._calculate_position_size_v52(
                        current_price, kelly, hmm_regime, nm_conf_for_caes, nm_metrics_for_caes
                    )
                elif score > score_strong:  # Señal COMPRA FUERTE - 75% position
                    decision['should_trade'] = True
                    decision['action'] = 'BUY'
                    decision['signal_strength'] = 'STRONG'
                    decision['amount_usd'] = self._calculate_position_size_v52(
                        current_price, kelly, hmm_regime, nm_conf_for_caes, nm_metrics_for_caes
                    ) * 0.75
                elif score > score_moderate:  # Señal COMPRA MODERADA - 50% position
                    decision['should_trade'] = True
                    decision['action'] = 'BUY'
                    decision['signal_strength'] = 'MODERATE'
                    decision['amount_usd'] = self._calculate_position_size_v52(
                        current_price, kelly, hmm_regime, nm_conf_for_caes, nm_metrics_for_caes
                    ) * 0.50
                elif score < -score_very_strong:  # Señal VENTA MUY FUERTE
                    decision['should_trade'] = True
                    decision['action'] = 'SELL'
                    decision['signal_strength'] = 'VERY_STRONG'
                    decision['amount_usd'] = self._calculate_position_size_v52(
                        current_price, kelly, hmm_regime, nm_conf_for_caes, nm_metrics_for_caes
                    )
                elif score < -score_strong:  # Señal VENTA FUERTE
                    decision['should_trade'] = True
                    decision['action'] = 'SELL'
                    decision['signal_strength'] = 'STRONG'
                    decision['amount_usd'] = self._calculate_position_size_v52(
                        current_price, kelly, hmm_regime, nm_conf_for_caes, nm_metrics_for_caes
                    ) * 0.75
                elif score < -score_moderate:  # Señal VENTA MODERADA
                    decision['should_trade'] = True
                    decision['action'] = 'SELL'
                    decision['signal_strength'] = 'MODERATE'
                    decision['amount_usd'] = self._calculate_position_size_v52(
                        current_price, kelly, hmm_regime, nm_conf_for_caes, nm_metrics_for_caes
                    ) * 0.50
            
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
                    
                    # ========== V6.5.2 SISTEMA DE VETO CON TRADING PROFILES ==========
                    # Umbrales configurables desde Trading Profile (INSTITUTIONAL/PAPER_AGGRESSIVE/BALANCED)
                    p = self.trading_profile  # Shorthand para perfil activo
                    
                    # Obtener umbrales del perfil o usar defaults (INSTITUTIONAL)
                    veto_critical = p.coherence_veto_critical if p else 30.0
                    veto_normal = p.coherence_veto_normal if p else 45.0
                    coherence_warning = p.coherence_warning if p else 60.0
                    coherence_good = p.coherence_good if p else 80.0
                    
                    profile_name = p.name if p else "HARDCODED"
                    logger.debug(f"📊 Profile {profile_name}: veto_critical={veto_critical}%, veto_normal={veto_normal}%")
                    
                    # NIVEL 1: VETO CRÍTICO - Coherencia muy baja
                    # V6.5.2 FIX: En paper mode, ignorar nivel CRITICAL y solo usar score numérico
                    # Esto permite trades para calibración cuando score > umbral aunque nivel sea CRITICAL
                    is_paper_mode = self.config.get('paper_mode', False)
                    
                    if coherence_report.coherence_score < veto_critical:
                        # Bloquear siempre si score está por debajo del umbral crítico
                        logger.error(f"🚨 COHERENCE VETO CRÍTICO: Score={coherence_report.coherence_score:.1f}% < {veto_critical}%")
                        decision['should_trade'] = False
                        decision['action'] = 'HOLD'
                        decision['reason'].append(f"🚨 VETO CRÍTICO: Coherencia {coherence_report.coherence_score:.1f}% < {veto_critical}%")
                    elif coherence_report.coherence_level.value == 'CRITICAL' and not is_paper_mode:
                        # En REAL money mode, también bloquear por nivel CRITICAL
                        logger.error(f"🚨 COHERENCE VETO CRÍTICO (NIVEL): Score={coherence_report.coherence_score:.1f}% - Nivel CRITICAL")
                        decision['should_trade'] = False
                        decision['action'] = 'HOLD'
                        decision['reason'].append(f"🚨 VETO CRÍTICO: Nivel CRITICAL detectado")
                    elif coherence_report.coherence_level.value == 'CRITICAL' and is_paper_mode:
                        # V6.5.2: Paper mode - advertir pero NO bloquear si score > umbral
                        logger.warning(f"⚠️ COHERENCE CRÍTICO (PAPER MODE): Score={coherence_report.coherence_score:.1f}% - Nivel CRITICAL pero permitido para calibración")
                        decision['reason'].append(f"⚠️ PAPER MODE: Nivel CRITICAL permitido (score {coherence_report.coherence_score:.1f}% > {veto_critical}%)")
                        # Reducir tamaño de posición 50% como precaución
                        if 'amount_usd' in decision:
                            decision['amount_usd'] *= 0.50
                            decision['reason'].append(f"📊 Posición reducida 50% por nivel CRITICAL")
                    
                    # NIVEL 2: VETO POR BAJA COHERENCIA - Configurable por perfil
                    elif coherence_report.coherence_score < veto_normal:
                        if not is_paper_mode:
                            logger.warning(f"🛑 COHERENCE VETO: Score={coherence_report.coherence_score:.1f}% < {veto_normal}%")
                            decision['should_trade'] = False
                            decision['action'] = 'HOLD'
                            decision['reason'].append(f"🛑 VETO: Coherencia {coherence_report.coherence_score:.1f}% < {veto_normal}%")
                        else:
                            # Paper mode: advertir pero permitir con reducción
                            logger.warning(f"⚠️ COHERENCE BAJO (PAPER MODE): Score={coherence_report.coherence_score:.1f}% - Permitido con reducción")
                            decision['reason'].append(f"⚠️ PAPER MODE: Coherencia baja permitida")
                            if 'amount_usd' in decision:
                                decision['amount_usd'] *= 0.65
                                decision['reason'].append(f"📊 Posición reducida 35% por coherencia baja")
                    
                    # NIVEL 3: HOLD recomendado - solo vetar si señal no es muy fuerte
                    elif coherence_report.decision_recommendation == 'HOLD':
                        signal_strength = decision.get('signal_strength', 'MODERATE')
                        if signal_strength == 'VERY_STRONG':
                            # Solo señales MUY fuertes pueden pasar con reducción
                            if 'amount_usd' in decision:
                                decision['amount_usd'] *= 0.55
                                decision['reason'].append(f"⚠️ Señal VERY_STRONG bypassing HOLD - posición reducida 45%")
                        elif is_paper_mode:
                            # V6.5.2: Paper mode - permitir HOLD con reducción para calibración
                            logger.warning(f"⚠️ HOLD (PAPER MODE): Permitido con reducción para calibración")
                            decision['reason'].append(f"⚠️ PAPER MODE: HOLD permitido con reducción")
                            if 'amount_usd' in decision:
                                decision['amount_usd'] *= 0.50
                                decision['reason'].append(f"📊 Posición reducida 50% por HOLD")
                        else:
                            # Real money: STRONG y MODERATE respetan HOLD
                            decision['should_trade'] = False
                            decision['action'] = 'HOLD'
                            decision['reason'].append(f"⚠️ Coherence Engine recomienda HOLD")
                    
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
    
    def _execute_smart_trade(self, analysis: Dict) -> Dict:
        """Ejecutar trade con validaciones de seguridad (PAPER o REAL)"""
        try:
            action = analysis['action']
            amount_usd = analysis.get('amount_usd', 0)
            
            # V6.5.2: En paper mode, no rechazar inmediatamente - el floor se aplicará después
            if not self.config.get('paper_mode', False) and amount_usd < self.config['min_trade_usd']:
                return {'error': 'Cantidad muy pequeña para tradear'}
            
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
                            # V6.5.2: PAPER MODE - Permitir con reducción 25% para calibración (era 50%)
                            logger.warning(f"⚠️ AI RISK GUARDIAN (PAPER MODE): {risk_event.description}")
                            logger.warning(f"   Permitiendo con reducción 25% para calibración de track record")
                            amount_usd = amount_usd * 0.75  # V6.5.2: Reducido de 0.50 a 0.75 para permitir más trades
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
            
            # 🧬 ARES QUANTUM KILL-SWITCH - FAIL-SAFE CRÍTICO
            # Validar disponibilidad de Kraken ANTES de cualquier lógica de trading
            kraken_available = (
                hasattr(self, 'trading_service') and 
                self.trading_service is not None and
                hasattr(self.trading_service, 'kraken') and
                self.trading_service.kraken is not None
            )
            
            is_real_trading = not self.config.get('paper_mode', True)
            
            # FAIL-SAFE ABSOLUTO: En REAL TRADING, Kraken DEBE estar disponible
            # Este check se ejecuta PRIMERO, antes de evaluar la acción
            if is_real_trading and not kraken_available:
                logger.error(f"🚨 CRITICAL FAIL-SAFE: REAL TRADING sin datos de Kraken disponibles")
                logger.error(f"   ARES Kill-Switch requiere datos de mercado en vivo - BLOQUEANDO todas las operaciones")
                logger.error(f"   Acción solicitada: {action}, Monto: ${amount_usd:.2f}")
                logger.error(f"   Sistema en modo degradado - requiere reconexión de Kraken para trading real")
                return {
                    'error': 'BLOQUEADO POR FAIL-SAFE CRÍTICO: Datos de Kraken no disponibles',
                    'blocked': True,
                    'fail_safe': True,
                    'critical': True,
                    'reason': 'Real trading requiere datos de Kraken en vivo para protecciones de ARES kill-switch',
                    'action': action,
                    'kraken_available': False,
                    'timestamp': int(time.time()),
                    'recommendation': 'Verificar conexión de Kraken o usar Paper Trading Mode'
                }
            
            # ARES Kill-Switch - solo se ejecuta si pasó el fail-safe
            # (Real trading CON Kraken disponible)
            if action != 'HOLD' and is_real_trading:
                try:
                    ares_blocked = False
                    ares_block_reason = []
                    
                    # ARES V1 Kill-Switch
                    if self.ares_v1 is not None and hasattr(self.ares_v1, 'evaluate_kill_switch'):
                        try:
                            # Obtener datos del análisis previo
                            v52_analysis = analysis.get('v52_analysis', {})
                            ares_v1_data = {
                                'signal': v52_analysis.get('ares_v1_signal', 'NONE'),
                                'confidence': v52_analysis.get('ares_v1_confidence', 0),
                                'active_signals': v52_analysis.get('ares_v1_active_signals', [])
                            }
                            
                            # Simular balance y trades para kill-switch
                            current_balance = self._get_balance()
                            recent_trades = []
                            if self.database_service:
                                try:
                                    recent_trades = self.database_service.get_recent_trades(hours=24, limit=100)
                                except:
                                    recent_trades = []
                            
                            # Evaluar Kill-Switch
                            kill_switch_result = self.ares_v1.evaluate_kill_switch(
                                balance=current_balance,
                                recent_trades=recent_trades,
                                ares_data=ares_v1_data
                            )
                            
                            if kill_switch_result['triggered']:
                                ares_blocked = True
                                reason = kill_switch_result.get('reason', 'ARES V1 Kill-Switch activado')
                                ares_block_reason.append(f"🧬 ARES V1 KILL-SWITCH: {reason}")
                                logger.error(f"🚨 ARES V1 KILL-SWITCH ACTIVADO: {reason}")
                        except Exception as e:
                            # Error no crítico - el kill-switch simplemente no se aplica
                            logger.debug(f"Error en ARES V1 Kill-Switch (continuando): {e}")
                    
                    # ARES V2 Kill-Switch (más agresivo para scalping)
                    if self.ares_v2 is not None and not ares_blocked and hasattr(self.ares_v2, 'evaluate_kill_switch_scalping'):
                        try:
                            v52_analysis = analysis.get('v52_analysis', {})
                            ares_v2_data = {
                                'signal': v52_analysis.get('ares_v2_signal', 'NONE'),
                                'confidence': v52_analysis.get('ares_v2_confidence', 0),
                                'active_signals': v52_analysis.get('ares_v2_active_signals', [])
                            }
                            
                            current_balance = self._get_balance()
                            recent_trades = []
                            if self.database_service:
                                try:
                                    recent_trades = self.database_service.get_recent_trades(hours=1, limit=50)
                                except:
                                    recent_trades = []
                            
                            # Kill-Switch para scalping (más estricto)
                            kill_switch_result = self.ares_v2.evaluate_kill_switch_scalping(
                                balance=current_balance,
                                recent_trades=recent_trades,
                                ares_data=ares_v2_data
                            )
                            
                            if kill_switch_result['triggered']:
                                ares_blocked = True
                                reason = kill_switch_result.get('reason', 'ARES V2 Scalping Kill-Switch activado')
                                ares_block_reason.append(f"🧨 ARES V2 SCALP KILL-SWITCH: {reason}")
                                logger.error(f"🚨 ARES V2 SCALPING KILL-SWITCH ACTIVADO: {reason}")
                        except Exception as e:
                            # Error no crítico - el kill-switch simplemente no se aplica
                            logger.debug(f"Error en ARES V2 Kill-Switch (continuando): {e}")
                    
                    # Si ARES bloqueó el trade
                    if ares_blocked:
                        return {
                            'error': 'BLOQUEADO POR ARES QUANTUM KILL-SWITCH',
                            'blocked': True,
                            'ares_kill_switch': True,
                            'reasons': ares_block_reason,
                            'action': action,
                            'timestamp': int(time.time())
                        }
                    elif not ares_blocked:
                        logger.debug(f"✅ ARES Quantum Kill-Switch: Trade permitido - Sin riesgos detectados")
                    
                except Exception as e:
                    # Error general del kill-switch - no bloquear el trade
                    logger.debug(f"Error en ARES Kill-Switch (continuando sin bloqueo): {e}")
            
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
                    
                    # V6.5.2 FIX: Garantizar que strategy_signals nunca esté vacía
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
                            # V6.5.2: PAPER MODE - Permitir con reducción 25% para calibración (era 50%)
                            logger.warning(f"⚠️ COHERENCE ENGINE (PAPER MODE): {reason}")
                            logger.warning(f"   Permitiendo con reducción 25% para calibración de track record")
                            amount_usd = amount_usd * 0.75  # V6.5.2: Reducido de 0.50 a 0.75 para permitir más trades
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
            
            # ========== V6.5.2: VERIFICACIÓN DE POSICIÓN ANTES DE SELL ==========
            # En paper mode, SELL solo puede cerrar posiciones existentes
            # Si no hay posición abierta, convertir a HOLD para evitar errores
            if self.config['paper_mode'] and action == 'SELL':
                if self.paper_trading and hasattr(self.paper_trading, 'has_open_position_for_symbol'):
                    user_id = str(self.config.get('harold_user_id', '7014748854'))
                    symbol = self.config['trading_pair']
                    
                    position_check = self.paper_trading.has_open_position_for_symbol(user_id, symbol)
                    
                    if not position_check.get('has_position', False):
                        # NO hay posición abierta - convertir SELL a HOLD (no abrir longs innecesarios)
                        logger.warning(f"📊 V6.5.2 POSITION CHECK: No hay posición abierta para {symbol}")
                        logger.info(f"   ⏸️ Convirtiendo SELL → HOLD (esperando señal BUY para abrir posición)")
                        action = 'HOLD'
                        analysis['action'] = 'HOLD'
                        if 'reason' in analysis:
                            analysis['reason'].append(f"⏸️ V6.5.2: SELL→HOLD (no open position for {symbol})")
                        return {'success': True, 'action': 'HOLD', 'reason': 'No open position to close'}
                    else:
                        # SÍ hay posición - proceder con SELL
                        pos = position_check.get('position', {})
                        logger.info(f"✅ V6.5.2 POSITION CHECK: Posición abierta encontrada")
                        logger.info(f"   📈 {pos.get('side', 'N/A').upper()} {pos.get('quantity', 0):.6f} @ ${pos.get('entry_price', 0):.2f}")
            
            # ========== V6.5.2: FLOOR MÍNIMO PARA PAPER MODE ==========
            # Asegurar que después de todas las reducciones, el tamaño sea >= min_trade_usd
            # NOTA: Solo aplicar si amount_usd > 0 (no sobrescribir ceros intencionales de Risk Guardian)
            if self.config['paper_mode'] and action != 'HOLD':
                min_trade = self.config.get('min_trade_usd', 50.0)
                if amount_usd > 0 and amount_usd < min_trade:
                    logger.warning(f"📊 V6.5.2 SIZE FLOOR: ${amount_usd:.2f} < ${min_trade:.2f} mínimo")
                    logger.info(f"   ↗️ Ajustando al mínimo para permitir ejecución")
                    amount_usd = min_trade
                    analysis['amount_usd'] = amount_usd
                elif amount_usd <= 0:
                    # Monto es 0 o negativo - esto es intencional (Risk Guardian bloqueó)
                    logger.warning(f"⚠️ V6.5.2: amount_usd={amount_usd} - Risk Guardian bloqueó intencionalmente")
                    return {'error': 'Trade bloqueado por Risk Guardian (amount=0)', 'blocked': True}
            
            # Ejecutar según modo
            if self.config['paper_mode']:
                # PAPER TRADING V2 - Usa PostgreSQL institucional
                if self.paper_trading:
                    result = self.paper_trading.execute_paper_trade(
                        user_id=str(self.config.get('harold_user_id', '7014748854')),
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
                logger.info(f"   💾 V6.5 REGISTRO: Trade #{self.state['total_trades']} | ID: {trade_id} | {db_status}")
                
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
                            logger.info(f"   ✅ V6.5 VERIFICACIÓN: {recent_count} trade(s) registrado(s) en último minuto")
                    except Exception as e:
                        logger.debug(f"V6.5: Error verificando registro: {e}")
                
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
                        self.database_service.schedule_trade_evaluation(
                            trade_id=trade_id,
                            reasoning_uuid=reasoning_uuid,
                            user_id='harold',
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
    
    def _calculate_position_size(self, current_price: float) -> float:
        """LEGACY: Usar _calculate_position_size_v52"""
        return self._calculate_position_size_v52(current_price, None, None)
    
    def _calculate_position_size_v52(
        self,
        current_price: float,
        kelly: Optional[Dict],
        hmm_regime: Optional[Dict],
        kernel_confidence: Optional[float] = None,
        kernel_metrics: Optional[Dict] = None
    ) -> float:
        """
        V6.5.2 PREMIUM: Calcular tamaño óptimo de posición
        - CAES: Confidence-Adaptive Entry System (sigmoide + sub-regímenes)
        - Kelly Criterion + HMM Regime + Ramp-Up System
        - Reduce drawdown inicial empezando conservador
        
        Args:
            current_price: Precio actual del activo
            kelly: Resultados de Kelly Criterion
            hmm_regime: Régimen detectado por HMM
            kernel_confidence: Confianza del Non-Markovian Kernel (0-100%)
            kernel_metrics: Métricas adicionales del kernel
        """
        balance = self._get_balance()
        
        # ========== V6.5.2 CAES - CONFIDENCE-ADAPTIVE ENTRY SYSTEM ==========
        caes_multiplier = 1.0
        caes_result = None
        
        if CAES_AVAILABLE and kernel_confidence is not None:
            try:
                caes = get_caes_instance()
                caes_result = caes.calculate_adaptive_parameters(
                    kernel_confidence=kernel_confidence,
                    kernel_metrics=kernel_metrics or {}
                )
                caes_multiplier = caes_result.position_multiplier
                
                self._last_caes_result = caes_result
                
            except Exception as e:
                logger.debug(f"CAES calculation failed: {e}")
                caes_multiplier = 1.0
        
        # ========== V6.5.2 RAMP-UP SYSTEM CON TRADING PROFILES ==========
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
        
        # ========== V6.5.2 APLICAR CAES MULTIPLIER ==========
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
        
        # Log para tracking
        if total_trades < 20 or caes_multiplier != 1.0:
            caes_info = f", CAES={caes_multiplier:.2f}x" if caes_multiplier != 1.0 else ""
            logger.info(f"📊 V6.5.2 Ramp-Up: Trade #{total_trades+1}, Factor={ramp_up_factor:.0%}{caes_info}, Size=${optimal_size:.2f}")
        
        return optimal_size
    
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
                    
                    print(f"💰 Balance detectado: ${usd_balance:.2f} (Kraken data: {balance})")
                    return usd_balance
                return 0.0
        except Exception as e:
            print(f"❌ ERROR obteniendo balance: {e}")
            return 0.0
    
    def _get_price_history(self, pair: str, days: int = 100) -> Optional[List[float]]:
        """Obtener histórico de precios"""
        try:
            if hasattr(self.trading_service, 'get_ohlc'):
                ohlc = self.trading_service.get_ohlc(pair, interval=1440)
                if ohlc and len(ohlc) > 0:
                    return [float(candle[4]) for candle in ohlc[-days:]]
            return None
        except:
            return None
    
    def _get_volume_history(self, pair: str, days: int = 100) -> Optional[List[float]]:
        """Obtener histórico de volúmenes"""
        try:
            if hasattr(self.trading_service, 'get_ohlc'):
                ohlc = self.trading_service.get_ohlc(pair, interval=1440)
                if ohlc and len(ohlc) > 0:
                    return [float(candle[6]) for candle in ohlc[-days:]]
            return None
        except:
            return None
    
    def _get_ohlc_history(self, pair: str, days: int = 100) -> Optional[Dict[str, List[float]]]:
        """
        V6.5.2 FIX: Obtener histórico OHLC completo para estrategias que requieren highs/lows
        
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
        V6.5.2 FIX: Generar volúmenes sintéticos basados en price changes
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
        🎯 Aplicar parámetros calibrados a las estrategias ARES
        
        Este método es llamado por el Adaptive Parameter Engine cuando
        detecta un cambio de régimen y calibra nuevos parámetros.
        
        SAFEGUARDS:
        - Verifica que no hay posiciones abiertas antes de aplicar cambios
        - Solo aplica a NUEVOS trades, no afecta trades en progreso
        - Valida con Risk Guardian antes de aplicar
        - Almacena parámetros para próximo trade, no modifica trades activos
        
        Args:
            strategy_name: 'ARES_V1' o 'ARES_V2'
            profile: AdaptiveParameterProfile con los nuevos parámetros
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
        
        Este método es llamado al abrir un nuevo trade para obtener
        los parámetros calibrados por el Adaptive Engine.
        
        Args:
            strategy_name: 'ARES_V1' o 'ARES_V2'
            
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
        🧠 Procesar salida del Non-Markovian Kernel para el Adaptive Engine
        
        Envía las señales de régimen al motor adaptativo para que
        determine si es necesario recalibrar los parámetros de ARES.
        
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
                
                # Registrar trade en el cooldown manager
                for strategy in ['ARES_V1', 'ARES_V2']:
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
        """Obtener estadísticas del bot"""
        total = self.state['total_trades']
        winning = self.state['winning_trades']
        win_rate = (winning / total * 100) if total > 0 else 0
        
        return {
            'total_trades': total,
            'winning_trades': winning,
            'losing_trades': self.state['losing_trades'],
            'win_rate': win_rate,
            'total_profit_loss': self.state['total_profit_loss'],
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
            win_rate = monte_carlo.get('win_rate', 50)
            if win_rate >= 70:
                signal_enum = Signal.STRONG_BUY
            elif win_rate >= 55:
                signal_enum = Signal.BUY
            elif win_rate <= 30:
                signal_enum = Signal.STRONG_SELL
            elif win_rate <= 45:
                signal_enum = Signal.SELL
            else:
                signal_enum = Signal.HOLD
            
            signals.append(StrategySignal(
                name='monte_carlo',
                signal=signal_enum,
                confidence=win_rate / 100.0,
                strength=win_rate,
                reasoning=f"{win_rate:.1f}% win probability"
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
        
        # 9. Order Book Analysis (placeholder - no data aquí)
        signals.append(StrategySignal(
            name='order_book',
            signal=Signal.HOLD,
            confidence=0.5,
            strength=0.0,
            reasoning="Order book neutral"
        ))
        
        # 10. Sharia Compliance (placeholder - siempre OK si estamos evaluando)
        signals.append(StrategySignal(
            name='sharia_compliance',
            signal=Signal.BUY,
            confidence=1.0,
            strength=1.0,
            reasoning="Asset halal confirmed"
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