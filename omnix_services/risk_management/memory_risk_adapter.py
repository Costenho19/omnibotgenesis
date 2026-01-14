"""
OMNIX V6.2 ULTRA - Memory Risk Adapter
=======================================
Puente entre Non-Markovian Kernel y Risk Management System.

Este adaptador transforma las señales temporales del kernel en
métricas de riesgo predictivas, permitiendo al RMS actuar de
forma proactiva en lugar de reactiva.

MÉTRICAS PREDICTIVAS:
1. Memory Coherence Risk: Pérdida de coherencia temporal = riesgo elevado
2. Regime Transition Risk: Transiciones inminentes detectadas por kernel
3. Memory Divergence Risk: Divergencias extremas preceden movimientos bruscos
4. Cyclical Phase Risk: Fase del ciclo indica timing de riesgo

Creado: Nov 29, 2025
OMNIX V6.2 ULTRA - Institutional Trading System
"""

import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MemoryRiskLevel(Enum):
    """Niveles de riesgo basados en memoria temporal"""
    STABLE = 'stable'
    ELEVATED = 'elevated'
    HIGH = 'high'
    CRITICAL = 'critical'


@dataclass
class MemoryRiskMetrics:
    """Métricas de riesgo derivadas del kernel Non-Markoviano"""
    
    coherence_risk: float = 0.0
    transition_risk: float = 0.0
    divergence_risk: float = 0.0
    cyclical_risk: float = 0.0
    
    overall_memory_risk: float = 0.0
    risk_level: MemoryRiskLevel = MemoryRiskLevel.STABLE
    
    regime_stability: float = 100.0
    predicted_volatility_change: float = 0.0
    
    timestamp: Optional[datetime] = None
    
    confidence: float = 0.0
    data_quality: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'coherence_risk': round(self.coherence_risk, 2),
            'transition_risk': round(self.transition_risk, 2),
            'divergence_risk': round(self.divergence_risk, 2),
            'cyclical_risk': round(self.cyclical_risk, 2),
            'overall_memory_risk': round(self.overall_memory_risk, 2),
            'risk_level': self.risk_level.value,
            'regime_stability': round(self.regime_stability, 2),
            'predicted_volatility_change': round(self.predicted_volatility_change, 2),
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'confidence': round(self.confidence, 2),
            'data_quality': round(self.data_quality, 2)
        }


class MemoryRiskAdapter:
    """
    🧠 Adaptador de Riesgo Basado en Memoria Non-Markoviana
    
    Transforma análisis temporal del kernel en señales de riesgo
    que el RMS puede utilizar para decisiones predictivas.
    
    INTEGRACIÓN:
    - LimitsEngine: Ajuste dinámico de límites según coherencia
    - CircuitBreaker: Nuevo trigger MEMORY_INCOHERENCE
    - PositionMonitor: Factor de ajuste por divergencia de memoria
    - AlertDispatcher: Alertas predictivas de transición de régimen
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, kernel=None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.kernel = kernel
        
        # ADR-007 Phase 1 Calibration (Jan 14, 2026) - 5-point reduction
        self._coherence_threshold_critical = 30.0   # was 35.0
        self._coherence_threshold_high = 45.0       # was 50.0
        self._coherence_threshold_elevated = 60.0   # was 65.0
        
        self._divergence_threshold_critical = 5.0
        self._divergence_threshold_high = 3.0
        self._divergence_threshold_elevated = 1.5
        
        self._cyclical_weakness_threshold = 30.0
        
        self._transition_sensitivity = 0.7
        
        self._risk_history: list = []
        self._max_history = 100
        
        self._last_metrics: Optional[MemoryRiskMetrics] = None
        self._last_coherence: Optional[Dict] = None
        
        self._initialized = True
        logger.info("🧠 MemoryRiskAdapter V6.2 inicializado")
        logger.info(f"   Coherence thresholds: {self._coherence_threshold_elevated}/{self._coherence_threshold_high}/{self._coherence_threshold_critical}")
        logger.info(f"   Divergence thresholds: ±{self._divergence_threshold_elevated}/{self._divergence_threshold_high}/{self._divergence_threshold_critical}%")
    
    def set_kernel(self, kernel) -> None:
        """Configurar kernel después de inicialización"""
        self.kernel = kernel
        if kernel:
            logger.info("🧠 MemoryRiskAdapter: Non-Markovian Kernel conectado")
    
    def compute_memory_risk(self, current_price: float) -> MemoryRiskMetrics:
        """
        Calcular métricas de riesgo completas basadas en memoria temporal.
        
        Args:
            current_price: Precio actual del activo
            
        Returns:
            MemoryRiskMetrics con análisis completo
        """
        metrics = MemoryRiskMetrics(timestamp=datetime.utcnow())
        
        if not self.kernel:
            logger.warning("⚠️ Kernel no disponible para análisis de riesgo")
            metrics.confidence = 0.0
            return metrics
        
        history_length = self.kernel.get_history_length()
        if history_length < 24:
            metrics.data_quality = (history_length / 24) * 100
            metrics.confidence = metrics.data_quality * 0.3
            return metrics
        
        metrics.data_quality = min(100, (history_length / 100) * 100)
        
        coherence = self.kernel.compute_regime_coherence()
        if coherence:
            self._last_coherence = coherence
            metrics.coherence_risk = self._compute_coherence_risk(coherence)
            metrics.regime_stability = coherence.get('overall_coherence', 50.0)
        
        divergence = self.kernel.compute_memory_divergence(current_price)
        if divergence is not None:
            metrics.divergence_risk = self._compute_divergence_risk(divergence)
        
        momentum = self.kernel.compute_memory_momentum()
        if momentum is not None and coherence:
            metrics.transition_risk = self._compute_transition_risk(
                momentum, coherence, divergence
            )
        
        cyclical = self.kernel.compute_cyclical_strength()
        if cyclical is not None:
            metrics.cyclical_risk = self._compute_cyclical_risk(cyclical)
        
        metrics.overall_memory_risk = self._compute_overall_risk(metrics)
        metrics.risk_level = self._determine_risk_level(metrics.overall_memory_risk)
        
        if coherence and self._last_coherence:
            metrics.predicted_volatility_change = self._predict_volatility_change(
                coherence, momentum
            )
        
        metrics.confidence = self._compute_confidence(metrics)
        
        self._last_metrics = metrics
        self._update_history(metrics)
        
        return metrics
    
    def _compute_coherence_risk(self, coherence: Dict) -> float:
        """Calcular riesgo por pérdida de coherencia temporal"""
        overall = coherence.get('overall_coherence', 50.0)
        
        if overall < self._coherence_threshold_critical:
            base_risk = 80.0 + ((self._coherence_threshold_critical - overall) / 
                               self._coherence_threshold_critical) * 20
        elif overall < self._coherence_threshold_high:
            base_risk = 50.0 + ((self._coherence_threshold_high - overall) / 
                               (self._coherence_threshold_high - self._coherence_threshold_critical)) * 30
        elif overall < self._coherence_threshold_elevated:
            base_risk = 25.0 + ((self._coherence_threshold_elevated - overall) / 
                               (self._coherence_threshold_elevated - self._coherence_threshold_high)) * 25
        else:
            base_risk = max(0, 25.0 - (overall - self._coherence_threshold_elevated) * 0.5)
        
        trend_coherence = coherence.get('trend_coherence', 50.0)
        vol_coherence = coherence.get('volatility_coherence', 50.0)
        
        if abs(trend_coherence - vol_coherence) > 30:
            base_risk += 10.0
        
        return min(100.0, max(0.0, base_risk))
    
    def _compute_divergence_risk(self, divergence: float) -> float:
        """Calcular riesgo por divergencia extrema de memoria"""
        abs_div = abs(divergence)
        
        if abs_div > self._divergence_threshold_critical:
            risk = 75.0 + ((abs_div - self._divergence_threshold_critical) / 
                          self._divergence_threshold_critical) * 25
        elif abs_div > self._divergence_threshold_high:
            risk = 45.0 + ((abs_div - self._divergence_threshold_high) / 
                          (self._divergence_threshold_critical - self._divergence_threshold_high)) * 30
        elif abs_div > self._divergence_threshold_elevated:
            risk = 20.0 + ((abs_div - self._divergence_threshold_elevated) / 
                          (self._divergence_threshold_high - self._divergence_threshold_elevated)) * 25
        else:
            risk = abs_div / self._divergence_threshold_elevated * 20
        
        return min(100.0, max(0.0, risk))
    
    def _compute_transition_risk(self, momentum: float, coherence: Dict, 
                                  divergence: Optional[float]) -> float:
        """
        Detectar riesgo de transición de régimen inminente.
        
        Señales de transición:
        1. Momentum cambiando dirección con coherencia baja
        2. Divergencia extrema con pérdida de coherencia
        3. Volatilidad no coherente con tendencia
        """
        risk = 0.0
        
        vol_coherence = coherence.get('volatility_coherence', 50.0)
        trend_coherence = coherence.get('trend_coherence', 50.0)
        
        if vol_coherence < 40 and trend_coherence > 60:
            risk += 25.0
        elif vol_coherence > 70 and trend_coherence < 30:
            risk += 20.0
        
        if abs(momentum) > 30 and coherence.get('overall_coherence', 50) < 50:
            risk += 30.0
        elif abs(momentum) > 50 and coherence.get('overall_coherence', 50) < 65:
            risk += 15.0
        
        if divergence is not None:
            if abs(divergence) > self._divergence_threshold_high:
                if coherence.get('overall_coherence', 50) < self._coherence_threshold_high:
                    risk += 25.0
        
        if len(self._risk_history) >= 5:
            recent_coherence_risks = [
                r.coherence_risk for r in self._risk_history[-5:]
            ]
            coherence_trend = recent_coherence_risks[-1] - recent_coherence_risks[0]
            if coherence_trend > 15:
                risk += 15.0
        
        return min(100.0, max(0.0, risk * self._transition_sensitivity))
    
    def _compute_cyclical_risk(self, cyclical_strength: float) -> float:
        """
        Calcular riesgo por fase del ciclo.
        
        Cyclical strength bajo = menos predictibilidad = más riesgo
        """
        if cyclical_strength < self._cyclical_weakness_threshold:
            risk = 40.0 + ((self._cyclical_weakness_threshold - cyclical_strength) / 
                          self._cyclical_weakness_threshold) * 30
        elif cyclical_strength < 50:
            risk = 20.0 + ((50 - cyclical_strength) / 20) * 20
        else:
            risk = max(0, 20.0 - (cyclical_strength - 50) * 0.4)
        
        return min(100.0, max(0.0, risk))
    
    def _compute_overall_risk(self, metrics: MemoryRiskMetrics) -> float:
        """
        Calcular riesgo general ponderado.
        
        Ponderación institucional:
        - Transition Risk: 35% (más crítico - anticipa cambios)
        - Coherence Risk: 30% (estabilidad del régimen)
        - Divergence Risk: 25% (tensión de precios)
        - Cyclical Risk: 10% (predictibilidad)
        """
        overall = (
            metrics.transition_risk * 0.35 +
            metrics.coherence_risk * 0.30 +
            metrics.divergence_risk * 0.25 +
            metrics.cyclical_risk * 0.10
        )
        
        max_component = max(
            metrics.transition_risk,
            metrics.coherence_risk,
            metrics.divergence_risk
        )
        if max_component > 80:
            overall = max(overall, max_component * 0.9)
        
        return min(100.0, max(0.0, overall))
    
    def _determine_risk_level(self, overall_risk: float) -> MemoryRiskLevel:
        """Determinar nivel de riesgo categórico"""
        if overall_risk >= 75:
            return MemoryRiskLevel.CRITICAL
        elif overall_risk >= 55:
            return MemoryRiskLevel.HIGH
        elif overall_risk >= 35:
            return MemoryRiskLevel.ELEVATED
        else:
            return MemoryRiskLevel.STABLE
    
    def _predict_volatility_change(self, coherence: Dict, momentum: Optional[float]) -> float:
        """
        Predecir cambio de volatilidad basado en patrones de memoria.
        
        Returns:
            Cambio esperado en volatilidad (%). Positivo = aumento, Negativo = disminución.
        """
        vol_coherence = coherence.get('volatility_coherence', 50.0)
        
        base_change = (50 - vol_coherence) * 0.5
        
        if momentum is not None and abs(momentum) > 30:
            base_change += abs(momentum) * 0.1
        
        return max(-50, min(50, base_change))
    
    def _compute_confidence(self, metrics: MemoryRiskMetrics) -> float:
        """Calcular confianza en las métricas"""
        data_factor = metrics.data_quality / 100.0
        
        if len(self._risk_history) >= 10:
            recent_risks = [r.overall_memory_risk for r in self._risk_history[-10:]]
            variance = sum((r - sum(recent_risks)/len(recent_risks))**2 for r in recent_risks) / len(recent_risks)
            stability_factor = max(0.5, 1.0 - (variance / 1000))
        else:
            stability_factor = 0.7
        
        base_confidence = 70 + (data_factor * 20) + (stability_factor * 10)
        
        return min(100.0, max(0.0, base_confidence))
    
    def _update_history(self, metrics: MemoryRiskMetrics) -> None:
        """Actualizar historial de métricas"""
        self._risk_history.append(metrics)
        if len(self._risk_history) > self._max_history:
            self._risk_history = self._risk_history[-self._max_history:]
    
    def get_limit_adjustment_factor(self) -> float:
        """
        Obtener factor de ajuste para límites de riesgo.
        
        Retorna un multiplicador [0.5, 1.5] para ajustar límites:
        - < 1.0: Reducir límites (más conservador)
        - = 1.0: Sin cambio
        - > 1.0: Relajar límites (más agresivo)
        
        Returns:
            Factor de ajuste para límites
        """
        if self._last_metrics is None:
            return 1.0
        
        overall_risk = self._last_metrics.overall_memory_risk
        
        if overall_risk >= 75:
            return 0.5
        elif overall_risk >= 55:
            return 0.7
        elif overall_risk >= 35:
            return 0.85
        else:
            stability = self._last_metrics.regime_stability
            if stability > 75:
                return min(1.2, 1.0 + (stability - 75) * 0.01)
            return 1.0
    
    def should_trigger_circuit_breaker(self) -> Tuple[bool, str]:
        """
        Determinar si se debe activar el circuit breaker por memoria.
        
        Returns:
            (should_trigger, reason_message)
        """
        if self._last_metrics is None:
            return False, ""
        
        if self._last_metrics.risk_level == MemoryRiskLevel.CRITICAL:
            if self._last_metrics.transition_risk > 80:
                return True, f"⚠️ Transición de régimen crítica detectada (Risk: {self._last_metrics.transition_risk:.0f}%)"
            if self._last_metrics.coherence_risk > 85:
                return True, f"⚠️ Pérdida crítica de coherencia temporal (Risk: {self._last_metrics.coherence_risk:.0f}%)"
        
        if len(self._risk_history) >= 5:
            recent = self._risk_history[-5:]
            if all(r.risk_level in [MemoryRiskLevel.CRITICAL, MemoryRiskLevel.HIGH] for r in recent):
                if sum(r.transition_risk for r in recent) / 5 > 60:
                    return True, "⚠️ Riesgo de memoria persistentemente alto (5 períodos consecutivos)"
        
        return False, ""
    
    def get_position_risk_factor(self) -> float:
        """
        Obtener factor de riesgo para ajuste de posiciones.
        
        Retorna multiplicador [0.3, 1.0] para tamaño de posiciones.
        
        Returns:
            Factor de ajuste para posiciones
        """
        if self._last_metrics is None:
            return 1.0
        
        if self._last_metrics.risk_level == MemoryRiskLevel.CRITICAL:
            return 0.3
        elif self._last_metrics.risk_level == MemoryRiskLevel.HIGH:
            return 0.6
        elif self._last_metrics.risk_level == MemoryRiskLevel.ELEVATED:
            return 0.8
        else:
            return 1.0
    
    def get_predictive_alerts(self) -> list:
        """
        Generar alertas predictivas basadas en análisis de memoria.
        
        Returns:
            Lista de alertas con severity y mensaje
        """
        alerts = []
        
        if self._last_metrics is None:
            return alerts
        
        if self._last_metrics.transition_risk > 60:
            severity = 'critical' if self._last_metrics.transition_risk > 80 else 'warning'
            alerts.append({
                'type': 'REGIME_TRANSITION',
                'severity': severity,
                'message': f"Transición de régimen probable en próximas horas (Riesgo: {self._last_metrics.transition_risk:.0f}%)",
                'recommended_action': 'Reducir exposición y aumentar stops'
            })
        
        if self._last_metrics.coherence_risk > 70:
            alerts.append({
                'type': 'COHERENCE_LOSS',
                'severity': 'warning',
                'message': f"Pérdida de coherencia temporal detectada ({self._last_metrics.coherence_risk:.0f}%)",
                'recommended_action': 'Considerar posiciones más conservadoras'
            })
        
        if self._last_metrics.predicted_volatility_change > 20:
            alerts.append({
                'type': 'VOLATILITY_INCREASE',
                'severity': 'info',
                'message': f"Aumento de volatilidad esperado: +{self._last_metrics.predicted_volatility_change:.0f}%",
                'recommended_action': 'Ajustar stops y tamaño de posiciones'
            })
        elif self._last_metrics.predicted_volatility_change < -20:
            alerts.append({
                'type': 'VOLATILITY_DECREASE',
                'severity': 'info',
                'message': f"Disminución de volatilidad esperada: {self._last_metrics.predicted_volatility_change:.0f}%",
                'recommended_action': 'Posible oportunidad de posiciones más grandes'
            })
        
        return alerts
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Obtener resumen de estado del adaptador"""
        return {
            'adapter_version': '6.2.0',
            'kernel_connected': self.kernel is not None,
            'history_length': len(self._risk_history),
            'last_metrics': self._last_metrics.to_dict() if self._last_metrics else None,
            'limit_adjustment_factor': self.get_limit_adjustment_factor(),
            'position_risk_factor': self.get_position_risk_factor(),
            'pending_alerts': len(self.get_predictive_alerts())
        }
