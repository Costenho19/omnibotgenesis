"""
📊 OMNIX METRICS ENGINE - PROMETHEUS + GRAFANA INTEGRATION
Sistema de métricas institucional para tracking de trading en tiempo real

Métricas exportadas:
- Señales generadas por estrategia
- Trades ejecutados (buy/sell)
- Win rate en tiempo real
- P/L acumulado
- Rendimiento por módulo (Kalman, Quantum, Monte Carlo, etc.)
- Latencia de APIs
- Uptime del bot
"""

import logging
import time
from typing import Dict, Optional, List
from datetime import datetime
from prometheus_client import Counter, Gauge, Histogram, Summary, Info, generate_latest, REGISTRY
from prometheus_client.core import CollectorRegistry

logger = logging.getLogger(__name__)


class MetricsEngine:
    """
    Engine de métricas institucional para OMNIX
    
    Exporta métricas en formato Prometheus para visualización en Grafana
    """
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        Initialize Metrics Engine
        
        Args:
            registry: Prometheus registry (usa default si no se provee)
        """
        self.registry = registry or REGISTRY
        
        # =============================================================================
        # MÉTRICAS DE TRADING
        # =============================================================================
        
        # Trades ejecutados
        self.trades_total = Counter(
            'omnix_trades_total',
            'Total de trades ejecutados',
            ['action', 'mode', 'pair'],  # buy/sell, paper/real, BTC/USD
            registry=self.registry
        )
        
        # Trades ganadores/perdedores
        self.trades_outcome = Counter(
            'omnix_trades_outcome_total',
            'Trades por resultado',
            ['outcome', 'mode'],  # win/loss, paper/real
            registry=self.registry
        )
        
        # Profit/Loss acumulado
        self.pnl_total = Gauge(
            'omnix_pnl_usd',
            'Profit/Loss acumulado en USD',
            ['mode'],  # paper/real
            registry=self.registry
        )
        
        # Win rate actual
        self.win_rate = Gauge(
            'omnix_win_rate_percent',
            'Win rate en porcentaje',
            ['mode'],
            registry=self.registry
        )
        
        # Balance actual
        self.balance = Gauge(
            'omnix_balance_usd',
            'Balance actual en USD',
            ['mode', 'asset'],  # paper/real, USD/BTC/ETH
            registry=self.registry
        )
        
        # =============================================================================
        # MÉTRICAS DE ESTRATEGIAS
        # =============================================================================
        
        # Señales generadas por estrategia
        self.signals_generated = Counter(
            'omnix_signals_total',
            'Señales generadas por estrategia',
            ['strategy', 'signal'],  # strategy_name, buy/sell/hold
            registry=self.registry
        )
        
        # Confianza promedio por estrategia
        self.strategy_confidence = Gauge(
            'omnix_strategy_confidence',
            'Confianza promedio de la estrategia (0-1)',
            ['strategy'],
            registry=self.registry
        )
        
        # Rendimiento por estrategia (win rate individual)
        self.strategy_win_rate = Gauge(
            'omnix_strategy_win_rate',
            'Win rate individual por estrategia',
            ['strategy'],
            registry=self.registry
        )
        
        # =============================================================================
        # MÉTRICAS V5.2 QUANTUM
        # =============================================================================
        
        # Adaptive Weights (ω, Hurst, α)
        self.adaptive_omega = Gauge(
            'omnix_adaptive_omega',
            'Peso adaptativo omega (0-1)',
            registry=self.registry
        )
        
        self.hurst_exponent = Gauge(
            'omnix_hurst_exponent',
            'Exponente de Hurst para detección de memoria larga',
            registry=self.registry
        )
        
        self.alpha_stable = Gauge(
            'omnix_alpha_stable',
            'Índice α-stable para colas pesadas',
            registry=self.registry
        )
        
        # Régimen de mercado detectado
        self.market_regime = Info(
            'omnix_market_regime',
            'Régimen de mercado actual detectado',
            registry=self.registry
        )
        
        # Quantum Momentum signal
        self.quantum_signal = Gauge(
            'omnix_quantum_signal',
            'Señal Quantum Momentum (-10 a +10)',
            registry=self.registry
        )
        
        # Kalman Filter trend
        self.kalman_trend_strength = Gauge(
            'omnix_kalman_trend_strength',
            'Fuerza del trend Kalman (0-1)',
            registry=self.registry
        )
        
        # Monte Carlo win rate
        self.monte_carlo_win_rate = Gauge(
            'omnix_monte_carlo_win_rate',
            'Win rate de Monte Carlo simulation',
            registry=self.registry
        )
        
        # Black Swan risk level (0=LOW, 1=MEDIUM, 2=HIGH)
        self.black_swan_risk = Gauge(
            'omnix_black_swan_risk',
            'Nivel de riesgo Black Swan (0-2)',
            registry=self.registry
        )
        
        # =============================================================================
        # MÉTRICAS DE SISTEMA
        # =============================================================================
        
        # Latencia de Kraken API
        self.kraken_api_latency = Histogram(
            'omnix_kraken_api_latency_seconds',
            'Latencia de llamadas a Kraken API',
            ['endpoint'],  # ticker, balance, order, etc.
            registry=self.registry
        )
        
        # Uptime del bot
        self.bot_uptime = Gauge(
            'omnix_bot_uptime_seconds',
            'Tiempo que el bot ha estado corriendo',
            registry=self.registry
        )
        
        # Errores de API
        self.api_errors = Counter(
            'omnix_api_errors_total',
            'Errores de API por servicio',
            ['service', 'error_type'],  # kraken/openai/gemini, timeout/auth/rate_limit
            registry=self.registry
        )
        
        # Auto-Learning
        self.auto_learning_changes = Counter(
            'omnix_auto_learning_changes_total',
            'Cambios aplicados por auto-learning',
            ['parameter'],
            registry=self.registry
        )
        
        # =============================================================================
        # V6.5.4 PREMIUM: MÉTRICAS SL/TP MONITORING
        # =============================================================================
        
        self.sl_tp_checks_total = Counter(
            'omnix_sl_tp_checks_total',
            'Total de checks SL/TP ejecutados',
            ['symbol', 'profile'],
            registry=self.registry
        )
        
        self.sl_tp_triggers = Counter(
            'omnix_sl_tp_triggers_total',
            'SL/TP triggers ejecutados',
            ['symbol', 'trigger_type'],
            registry=self.registry
        )
        
        self.sl_tp_check_interval = Gauge(
            'omnix_sl_tp_check_interval_seconds',
            'Intervalo real entre checks SL/TP',
            registry=self.registry
        )
        
        self.sl_tp_last_check = Gauge(
            'omnix_sl_tp_last_check_timestamp',
            'Timestamp del último check SL/TP',
            registry=self.registry
        )
        
        self.positions_monitored = Gauge(
            'omnix_positions_monitored',
            'Número de posiciones siendo monitoreadas',
            ['symbol'],
            registry=self.registry
        )
        
        self.profile_active = Info(
            'omnix_trading_profile',
            'Perfil de trading activo',
            registry=self.registry
        )
        
        # Video analysis
        self.video_analyses = Counter(
            'omnix_video_analyses_total',
            'Videos analizados para learning',
            ['status'],  # success/failed
            registry=self.registry
        )
        
        # Info general
        self.system_info = Info(
            'omnix_system',
            'Información del sistema OMNIX',
            registry=self.registry
        )
        
        # Inicializar info del sistema
        self.system_info.info({
            'version': 'v5.2',
            'name': 'OMNIX Quantum Ultimate',
            'strategies': '9',
            'security': 'Post-Quantum (Kyber-768 + Dilithium-3)'
        })
        
        # Timestamp de inicio
        self.start_time = time.time()
        
        logger.info("📊 MetricsEngine inicializado - Prometheus metrics activos")
    
    # =============================================================================
    # MÉTODOS DE TRACKING - TRADING
    # =============================================================================
    
    def record_trade(
        self,
        action: str,
        mode: str,
        pair: str,
        amount_usd: float,
        confidence: float,
        outcome: Optional[str] = None  # 'win' o 'loss'
    ):
        """
        Registrar trade ejecutado
        
        Args:
            action: 'buy' o 'sell'
            mode: 'paper' o 'real'
            pair: 'BTC/USD', etc.
            amount_usd: Monto en USD
            confidence: Confianza 0-1
            outcome: 'win' o 'loss' (opcional, si ya se conoce)
        """
        self.trades_total.labels(action=action.lower(), mode=mode, pair=pair).inc()
        
        if outcome:
            self.trades_outcome.labels(outcome=outcome, mode=mode).inc()
        
        logger.debug(f"📊 Trade registrado: {action} {pair} ${amount_usd:.2f} ({mode})")
    
    def update_pnl(self, mode: str, pnl: float):
        """Actualizar P/L acumulado"""
        self.pnl_total.labels(mode=mode).set(pnl)
    
    def update_win_rate(self, mode: str, win_rate: float):
        """Actualizar win rate (0-100)"""
        self.win_rate.labels(mode=mode).set(win_rate)
    
    def update_balance(self, mode: str, asset: str, amount: float):
        """Actualizar balance"""
        self.balance.labels(mode=mode, asset=asset).set(amount)
    
    # =============================================================================
    # MÉTODOS DE TRACKING - ESTRATEGIAS
    # =============================================================================
    
    def record_signal(self, strategy: str, signal: str):
        """
        Registrar señal generada por estrategia
        
        Args:
            strategy: Nombre de la estrategia
            signal: 'buy', 'sell', 'hold'
        """
        self.signals_generated.labels(strategy=strategy, signal=signal.lower()).inc()
    
    def update_strategy_confidence(self, strategy: str, confidence: float):
        """Actualizar confianza de estrategia (0-1)"""
        self.strategy_confidence.labels(strategy=strategy).set(confidence)
    
    def update_strategy_win_rate(self, strategy: str, win_rate: float):
        """Actualizar win rate individual de estrategia"""
        self.strategy_win_rate.labels(strategy=strategy).set(win_rate)
    
    # =============================================================================
    # MÉTODOS DE TRACKING - V5.2 QUANTUM
    # =============================================================================
    
    def update_adaptive_weights(self, omega: float, hurst: float, alpha: float):
        """Actualizar pesos adaptativos"""
        self.adaptive_omega.set(omega)
        self.hurst_exponent.set(hurst)
        self.alpha_stable.set(alpha)
    
    def update_market_regime(self, regime: str, adaptive_regime: str):
        """Actualizar régimen de mercado"""
        self.market_regime.info({
            'hmm_regime': regime,
            'adaptive_regime': adaptive_regime,
            'timestamp': datetime.now().isoformat()
        })
    
    def update_quantum_signal(self, signal: float):
        """Actualizar señal Quantum Momentum (-10 a +10)"""
        self.quantum_signal.set(signal)
    
    def update_kalman_trend(self, trend: str, strength: float):
        """Actualizar trend Kalman"""
        self.kalman_trend_strength.set(strength)
    
    def update_monte_carlo_win_rate(self, win_rate: float):
        """Actualizar win rate de Monte Carlo"""
        self.monte_carlo_win_rate.set(win_rate)
    
    def update_black_swan_risk(self, risk_level: str):
        """Actualizar riesgo Black Swan"""
        risk_map = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2}
        self.black_swan_risk.set(risk_map.get(risk_level, 1))
    
    # =============================================================================
    # MÉTODOS DE TRACKING - SISTEMA
    # =============================================================================
    
    def record_kraken_api_call(self, endpoint: str, duration: float):
        """Registrar latencia de llamada a Kraken"""
        self.kraken_api_latency.labels(endpoint=endpoint).observe(duration)
    
    def update_uptime(self):
        """Actualizar uptime del bot"""
        uptime = time.time() - self.start_time
        self.bot_uptime.set(uptime)
    
    def record_api_error(self, service: str, error_type: str):
        """Registrar error de API"""
        self.api_errors.labels(service=service, error_type=error_type).inc()
    
    def record_auto_learning_change(self, parameter: str):
        """Registrar cambio de auto-learning"""
        self.auto_learning_changes.labels(parameter=parameter).inc()
    
    def record_video_analysis(self, status: str):
        """Registrar análisis de video"""
        self.video_analyses.labels(status=status).inc()
    
    # =============================================================================
    # V6.5.4 PREMIUM: MÉTODOS SL/TP MONITORING
    # =============================================================================
    
    def record_sl_tp_check(self, symbol: str, profile: str):
        """Registrar check SL/TP ejecutado"""
        self.sl_tp_checks_total.labels(symbol=symbol, profile=profile).inc()
        self.sl_tp_last_check.set(time.time())
    
    def record_sl_tp_trigger(self, symbol: str, trigger_type: str):
        """
        Registrar SL/TP trigger ejecutado
        
        Args:
            symbol: Par de trading
            trigger_type: 'STOP_LOSS' o 'TAKE_PROFIT'
        """
        self.sl_tp_triggers.labels(symbol=symbol, trigger_type=trigger_type).inc()
    
    def update_sl_tp_interval(self, interval_seconds: float):
        """Actualizar intervalo real de checks SL/TP"""
        self.sl_tp_check_interval.set(interval_seconds)
    
    def update_positions_monitored(self, symbol: str, count: int):
        """Actualizar número de posiciones monitoreadas por símbolo"""
        self.positions_monitored.labels(symbol=symbol).set(count)
    
    def set_active_profile(self, profile_name: str, allowed_symbols: list):
        """Registrar perfil activo y símbolos permitidos"""
        self.profile_active.info({
            'name': profile_name,
            'allowed_symbols': ','.join(allowed_symbols) if allowed_symbols else 'ALL',
            'timestamp': datetime.now().isoformat()
        })
    
    # =============================================================================
    # EXPORT
    # =============================================================================
    
    def get_metrics(self) -> bytes:
        """
        Obtener métricas en formato Prometheus
        
        Returns:
            Métricas en texto plano para scraping de Prometheus
        """
        # Actualizar uptime antes de exportar
        self.update_uptime()
        
        return generate_latest(self.registry)
    
    def get_stats_summary(self) -> Dict:
        """
        Obtener resumen de estadísticas actuales
        
        Returns:
            Dict con métricas principales
        """
        return {
            'uptime_seconds': time.time() - self.start_time,
            'timestamp': datetime.now().isoformat(),
            'status': 'active'
        }


# Singleton global
_metrics_engine = None


def get_metrics_engine(registry: Optional[CollectorRegistry] = None) -> MetricsEngine:
    """
    Obtener instancia singleton de MetricsEngine
    
    Args:
        registry: Prometheus registry (solo primera vez)
        
    Returns:
        MetricsEngine instance
    """
    global _metrics_engine
    
    if _metrics_engine is None:
        _metrics_engine = MetricsEngine(registry=registry)
        logger.info("📊 MetricsEngine singleton creado")
    
    return _metrics_engine
