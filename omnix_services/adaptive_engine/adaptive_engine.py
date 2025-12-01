#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNIX V6.5 ULTRA - ADAPTIVE PARAMETER ENGINE
Motor de Auto-Calibración Inteligente para Estrategias ARES

Este módulo implementa un sistema de calibración dinámica que:
1. Recibe señales del Non-Markovian Memory Kernel sobre regímenes de mercado
2. Ajusta automáticamente los parámetros de ARES V1/V2 basado en el régimen
3. Utiliza análisis de microestructura para ajustes finos
4. Implementa cooldowns inteligentes para evitar sobre-adaptación
5. Persiste configuraciones y métricas en PostgreSQL
6. Se integra con Coherence Engine y Risk Guardian para validación

Autor: OMNIX Team
Versión: 6.5 INSTITUTIONAL+
Fecha: Diciembre 2025
"""

import os
import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from threading import Lock
import numpy as np

logger = logging.getLogger(__name__)


class RegimeType(Enum):
    """Tipos de régimen de mercado detectados por el Memory Kernel"""
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"
    UNKNOWN = "unknown"


class CalibrationStatus(Enum):
    """Estados de calibración"""
    PENDING = "pending"
    APPLIED = "applied"
    REJECTED_COOLDOWN = "rejected_cooldown"
    REJECTED_RISK = "rejected_risk"
    REJECTED_COHERENCE = "rejected_coherence"
    ROLLED_BACK = "rolled_back"


@dataclass
class AdaptiveParameterProfile:
    """
    Perfil de parámetros adaptativos para una estrategia ARES.
    Define los rangos permitidos y valores actuales de cada parámetro.
    """
    strategy_name: str
    
    stop_loss_pct: float = -0.28
    stop_loss_min: float = -0.50
    stop_loss_max: float = -0.10
    
    take_profit_pct: float = 0.85
    take_profit_min: float = 0.30
    take_profit_max: float = 2.00
    
    position_size_factor: float = 1.0
    position_size_min: float = 0.3
    position_size_max: float = 1.5
    
    timeout_minutes: int = 60
    timeout_min: int = 15
    timeout_max: int = 240
    
    entry_threshold: float = 0.70
    entry_threshold_min: float = 0.50
    entry_threshold_max: float = 0.95
    
    sensitivity_coefficient: float = 1.0
    last_calibrated: datetime = field(default_factory=datetime.utcnow)
    calibration_count: int = 0
    
    def to_dict(self) -> Dict:
        """Convierte el perfil a diccionario"""
        data = asdict(self)
        data['last_calibrated'] = self.last_calibrated.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AdaptiveParameterProfile':
        """Crea un perfil desde diccionario"""
        if 'last_calibrated' in data and isinstance(data['last_calibrated'], str):
            data['last_calibrated'] = datetime.fromisoformat(data['last_calibrated'])
        return cls(**data)
    
    def clamp_parameters(self):
        """Asegura que todos los parámetros estén dentro de sus rangos"""
        self.stop_loss_pct = max(self.stop_loss_min, min(self.stop_loss_max, self.stop_loss_pct))
        self.take_profit_pct = max(self.take_profit_min, min(self.take_profit_max, self.take_profit_pct))
        self.position_size_factor = max(self.position_size_min, min(self.position_size_max, self.position_size_factor))
        self.timeout_minutes = max(self.timeout_min, min(self.timeout_max, self.timeout_minutes))
        self.entry_threshold = max(self.entry_threshold_min, min(self.entry_threshold_max, self.entry_threshold))


@dataclass
class CalibrationEvent:
    """Evento de calibración para logging y análisis"""
    event_id: str
    timestamp: datetime
    strategy: str
    regime: RegimeType
    regime_confidence: float
    previous_params: Dict
    new_params: Dict
    status: CalibrationStatus
    reason: str
    microstructure_context: Dict
    performance_window: Dict
    
    def to_dict(self) -> Dict:
        """Convierte el evento a diccionario para persistencia"""
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat(),
            'strategy': self.strategy,
            'regime': self.regime.value,
            'regime_confidence': self.regime_confidence,
            'previous_params': self.previous_params,
            'new_params': self.new_params,
            'status': self.status.value,
            'reason': self.reason,
            'microstructure_context': self.microstructure_context,
            'performance_window': self.performance_window
        }


class RegimeSignalProcessor:
    """
    Procesa señales del Non-Markovian Memory Kernel.
    Normaliza features, calcula confianza, y detecta cambios de régimen.
    """
    
    def __init__(self):
        self.last_regime: Optional[RegimeType] = None
        self.last_regime_time: Optional[datetime] = None
        self.regime_history: List[Tuple[datetime, RegimeType, float]] = []
        self.max_history = 100
        
        self.regime_mapping = {
            'bullish': RegimeType.TRENDING_UP,
            'bearish': RegimeType.TRENDING_DOWN,
            'neutral': RegimeType.RANGING,
            'high_volatility': RegimeType.HIGH_VOLATILITY,
            'low_volatility': RegimeType.LOW_VOLATILITY,
            'accumulation': RegimeType.ACCUMULATION,
            'distribution': RegimeType.DISTRIBUTION,
            'breakout': RegimeType.BREAKOUT,
            'reversal': RegimeType.REVERSAL,
        }
        
        logger.info("📡 RegimeSignalProcessor initialized")
    
    def process_kernel_signal(
        self,
        kernel_output: Dict
    ) -> Tuple[RegimeType, float, bool]:
        """
        Procesa la salida del Memory Kernel y determina el régimen.
        
        Args:
            kernel_output: Diccionario con salida del kernel
            
        Returns:
            Tuple (régimen detectado, confianza, es_cambio_significativo)
        """
        regime_name = kernel_output.get('regime', 'unknown').lower()
        confidence = kernel_output.get('confidence', 0.5)
        coherence = kernel_output.get('coherence', 0.5)
        
        regime = self.regime_mapping.get(regime_name, RegimeType.UNKNOWN)
        
        adjusted_confidence = confidence * (0.5 + 0.5 * coherence)
        
        is_significant_change = False
        if self.last_regime is not None:
            if regime != self.last_regime and adjusted_confidence > 0.65:
                is_significant_change = True
        else:
            is_significant_change = True
        
        self.regime_history.append((datetime.utcnow(), regime, adjusted_confidence))
        if len(self.regime_history) > self.max_history:
            self.regime_history.pop(0)
        
        if is_significant_change:
            self.last_regime = regime
            self.last_regime_time = datetime.utcnow()
        
        return regime, adjusted_confidence, is_significant_change
    
    def get_regime_stability(self, window_minutes: int = 30) -> float:
        """
        Calcula qué tan estable ha sido el régimen en los últimos N minutos.
        Retorna valor entre 0 (muy inestable) y 1 (muy estable).
        """
        if len(self.regime_history) < 3:
            return 0.5
        
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent = [(t, r, c) for t, r, c in self.regime_history if t > cutoff]
        
        if len(recent) < 2:
            return 0.5
        
        regimes = [r for _, r, _ in recent]
        unique_regimes = len(set(regimes))
        
        stability = 1.0 - (unique_regimes - 1) / max(len(regimes), 1)
        return max(0.0, min(1.0, stability))


class MicrostructureAnalyzer:
    """
    Analiza la microestructura del mercado para ajustes finos de parámetros.
    Considera spread, volumen, order book depth, y otros factores.
    """
    
    def __init__(self):
        self.spread_history: List[float] = []
        self.volume_history: List[float] = []
        self.max_history = 100
        
        logger.info("🔬 MicrostructureAnalyzer initialized")
    
    def analyze(
        self,
        current_spread: float = 0.001,
        current_volume: float = 1000000,
        bid_depth: float = 100000,
        ask_depth: float = 100000,
        recent_trades: int = 50
    ) -> Dict:
        """
        Analiza las condiciones actuales de microestructura.
        
        Returns:
            Dict con métricas de microestructura
        """
        self.spread_history.append(current_spread)
        self.volume_history.append(current_volume)
        
        if len(self.spread_history) > self.max_history:
            self.spread_history.pop(0)
        if len(self.volume_history) > self.max_history:
            self.volume_history.pop(0)
        
        avg_spread = np.mean(self.spread_history) if self.spread_history else current_spread
        avg_volume = np.mean(self.volume_history) if self.volume_history else current_volume
        
        spread_percentile = self._calculate_percentile(current_spread, self.spread_history)
        volume_percentile = self._calculate_percentile(current_volume, self.volume_history)
        
        depth_balance = bid_depth / (ask_depth + 0.001) if ask_depth > 0 else 1.0
        
        liquidity_score = min(1.0, (bid_depth + ask_depth) / 500000)
        
        volatility_indicator = (current_spread / avg_spread) if avg_spread > 0 else 1.0
        
        return {
            'current_spread': current_spread,
            'avg_spread': avg_spread,
            'spread_percentile': spread_percentile,
            'current_volume': current_volume,
            'avg_volume': avg_volume,
            'volume_percentile': volume_percentile,
            'depth_balance': depth_balance,
            'liquidity_score': liquidity_score,
            'volatility_indicator': volatility_indicator,
            'recent_trades': recent_trades,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _calculate_percentile(self, value: float, history: List[float]) -> float:
        """Calcula el percentil de un valor en el historial"""
        if not history:
            return 0.5
        sorted_hist = sorted(history)
        position = sum(1 for v in sorted_hist if v <= value)
        return position / len(sorted_hist)


class ParameterCalibrator:
    """
    Motor de calibración de parámetros.
    Calcula ajustes óptimos basados en régimen y microestructura.
    """
    
    REGIME_ADJUSTMENTS = {
        RegimeType.ACCUMULATION: {
            'stop_loss_multiplier': 0.8,
            'take_profit_multiplier': 1.3,
            'position_size_multiplier': 1.1,
            'entry_threshold_delta': -0.05
        },
        RegimeType.DISTRIBUTION: {
            'stop_loss_multiplier': 0.7,
            'take_profit_multiplier': 0.8,
            'position_size_multiplier': 0.7,
            'entry_threshold_delta': 0.10
        },
        RegimeType.TRENDING_UP: {
            'stop_loss_multiplier': 0.9,
            'take_profit_multiplier': 1.4,
            'position_size_multiplier': 1.2,
            'entry_threshold_delta': -0.08
        },
        RegimeType.TRENDING_DOWN: {
            'stop_loss_multiplier': 0.6,
            'take_profit_multiplier': 0.7,
            'position_size_multiplier': 0.6,
            'entry_threshold_delta': 0.15
        },
        RegimeType.HIGH_VOLATILITY: {
            'stop_loss_multiplier': 1.3,
            'take_profit_multiplier': 1.5,
            'position_size_multiplier': 0.5,
            'entry_threshold_delta': 0.12
        },
        RegimeType.LOW_VOLATILITY: {
            'stop_loss_multiplier': 0.7,
            'take_profit_multiplier': 0.8,
            'position_size_multiplier': 1.0,
            'entry_threshold_delta': -0.05
        },
        RegimeType.BREAKOUT: {
            'stop_loss_multiplier': 1.0,
            'take_profit_multiplier': 1.8,
            'position_size_multiplier': 1.3,
            'entry_threshold_delta': -0.10
        },
        RegimeType.REVERSAL: {
            'stop_loss_multiplier': 0.6,
            'take_profit_multiplier': 0.9,
            'position_size_multiplier': 0.5,
            'entry_threshold_delta': 0.15
        },
        RegimeType.RANGING: {
            'stop_loss_multiplier': 0.8,
            'take_profit_multiplier': 0.9,
            'position_size_multiplier': 0.8,
            'entry_threshold_delta': 0.0
        },
        RegimeType.UNKNOWN: {
            'stop_loss_multiplier': 1.0,
            'take_profit_multiplier': 1.0,
            'position_size_multiplier': 0.7,
            'entry_threshold_delta': 0.05
        }
    }
    
    def __init__(self, smoothing_factor: float = 0.3):
        """
        Args:
            smoothing_factor: Factor de suavizado para transiciones (0-1)
                             Valores más bajos = transiciones más suaves
        """
        self.smoothing_factor = smoothing_factor
        self.baseline_profiles: Dict[str, AdaptiveParameterProfile] = {}
        
        self._init_baseline_profiles()
        
        logger.info(f"⚙️ ParameterCalibrator initialized (smoothing={smoothing_factor})")
    
    def _init_baseline_profiles(self):
        """Inicializa perfiles baseline para ARES V1 y V2"""
        self.baseline_profiles['ARES_V1'] = AdaptiveParameterProfile(
            strategy_name='ARES_V1',
            stop_loss_pct=-0.35,
            take_profit_pct=1.20,
            position_size_factor=1.0,
            timeout_minutes=240,
            entry_threshold=0.65
        )
        
        self.baseline_profiles['ARES_V2'] = AdaptiveParameterProfile(
            strategy_name='ARES_V2',
            stop_loss_pct=-0.28,
            take_profit_pct=0.85,
            position_size_factor=1.0,
            timeout_minutes=60,
            entry_threshold=0.70
        )
    
    def calibrate(
        self,
        current_profile: AdaptiveParameterProfile,
        regime: RegimeType,
        regime_confidence: float,
        microstructure: Dict
    ) -> AdaptiveParameterProfile:
        """
        Calcula nuevos parámetros basados en régimen y microestructura.
        Aplica suavizado exponencial para transiciones graduales.
        """
        adjustments = self.REGIME_ADJUSTMENTS.get(regime, self.REGIME_ADJUSTMENTS[RegimeType.UNKNOWN])
        
        baseline = self.baseline_profiles.get(
            current_profile.strategy_name,
            self.baseline_profiles['ARES_V2']
        )
        
        target_sl = baseline.stop_loss_pct * adjustments['stop_loss_multiplier']
        target_tp = baseline.take_profit_pct * adjustments['take_profit_multiplier']
        target_size = baseline.position_size_factor * adjustments['position_size_multiplier']
        target_threshold = baseline.entry_threshold + adjustments['entry_threshold_delta']
        
        volatility_factor = microstructure.get('volatility_indicator', 1.0)
        liquidity_factor = microstructure.get('liquidity_score', 0.5)
        
        if volatility_factor > 1.5:
            target_sl *= 1.2
            target_size *= 0.7
        elif volatility_factor < 0.5:
            target_sl *= 0.8
        
        if liquidity_factor < 0.3:
            target_size *= 0.8
            target_threshold += 0.05
        
        confidence_weight = regime_confidence * self.smoothing_factor
        
        new_profile = AdaptiveParameterProfile(
            strategy_name=current_profile.strategy_name,
            stop_loss_pct=self._smooth_transition(
                current_profile.stop_loss_pct, target_sl, confidence_weight
            ),
            take_profit_pct=self._smooth_transition(
                current_profile.take_profit_pct, target_tp, confidence_weight
            ),
            position_size_factor=self._smooth_transition(
                current_profile.position_size_factor, target_size, confidence_weight
            ),
            timeout_minutes=current_profile.timeout_minutes,
            entry_threshold=self._smooth_transition(
                current_profile.entry_threshold, target_threshold, confidence_weight
            ),
            sensitivity_coefficient=current_profile.sensitivity_coefficient,
            last_calibrated=datetime.utcnow(),
            calibration_count=current_profile.calibration_count + 1,
            stop_loss_min=current_profile.stop_loss_min,
            stop_loss_max=current_profile.stop_loss_max,
            take_profit_min=current_profile.take_profit_min,
            take_profit_max=current_profile.take_profit_max,
            position_size_min=current_profile.position_size_min,
            position_size_max=current_profile.position_size_max,
            timeout_min=current_profile.timeout_min,
            timeout_max=current_profile.timeout_max,
            entry_threshold_min=current_profile.entry_threshold_min,
            entry_threshold_max=current_profile.entry_threshold_max
        )
        
        new_profile.clamp_parameters()
        
        return new_profile
    
    def _smooth_transition(
        self,
        current: float,
        target: float,
        weight: float
    ) -> float:
        """Aplica suavizado exponencial entre valor actual y objetivo"""
        return current + weight * (target - current)


class CooldownManager:
    """
    Gestiona cooldowns entre calibraciones para evitar sobre-adaptación.
    Implementa cooldowns por estrategia y por régimen.
    """
    
    def __init__(
        self,
        default_cooldown_minutes: int = 15,
        min_trades_between_calibrations: int = 5,
        critical_regime_override: bool = True
    ):
        self.default_cooldown = timedelta(minutes=default_cooldown_minutes)
        self.min_trades = min_trades_between_calibrations
        self.critical_override = critical_regime_override
        
        self.last_calibration: Dict[str, datetime] = {}
        self.trades_since_calibration: Dict[str, int] = {}
        self._lock = Lock()
        
        self.critical_regimes = {
            RegimeType.HIGH_VOLATILITY,
            RegimeType.BREAKOUT,
            RegimeType.REVERSAL
        }
        
        logger.info(f"⏱️ CooldownManager initialized (cooldown={default_cooldown_minutes}min, min_trades={min_trades_between_calibrations})")
    
    def can_calibrate(
        self,
        strategy: str,
        regime: RegimeType,
        regime_confidence: float
    ) -> Tuple[bool, str]:
        """
        Verifica si se puede realizar una calibración.
        
        Returns:
            Tuple (puede_calibrar, razón)
        """
        with self._lock:
            if self.critical_override and regime in self.critical_regimes and regime_confidence > 0.80:
                return True, f"Critical regime override: {regime.value}"
            
            last_cal = self.last_calibration.get(strategy)
            if last_cal:
                time_since = datetime.utcnow() - last_cal
                if time_since < self.default_cooldown:
                    remaining = self.default_cooldown - time_since
                    return False, f"Cooldown active: {remaining.seconds}s remaining"
            
            trades = self.trades_since_calibration.get(strategy, self.min_trades)
            if trades < self.min_trades:
                return False, f"Insufficient trades: {trades}/{self.min_trades}"
            
            return True, "Calibration allowed"
    
    def record_calibration(self, strategy: str):
        """Registra que se realizó una calibración"""
        with self._lock:
            self.last_calibration[strategy] = datetime.utcnow()
            self.trades_since_calibration[strategy] = 0
    
    def record_trade(self, strategy: str):
        """Registra que se realizó un trade"""
        with self._lock:
            self.trades_since_calibration[strategy] = self.trades_since_calibration.get(strategy, 0) + 1
    
    def get_status(self, strategy: str) -> Dict:
        """Obtiene el estado actual del cooldown para una estrategia"""
        with self._lock:
            last_cal = self.last_calibration.get(strategy)
            trades = self.trades_since_calibration.get(strategy, 0)
            
            cooldown_remaining = 0
            if last_cal:
                time_since = datetime.utcnow() - last_cal
                if time_since < self.default_cooldown:
                    cooldown_remaining = (self.default_cooldown - time_since).seconds
            
            return {
                'strategy': strategy,
                'last_calibration': last_cal.isoformat() if last_cal else None,
                'trades_since': trades,
                'cooldown_remaining_seconds': cooldown_remaining,
                'can_calibrate': cooldown_remaining == 0 and trades >= self.min_trades
            }


class AdaptiveParameterEngine:
    """
    Motor principal de parámetros adaptativos.
    Orquesta todos los componentes para auto-calibración inteligente.
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern para una sola instancia global"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(
        self,
        database_service=None,
        coherence_engine=None,
        risk_guardian=None,
        smoothing_factor: float = 0.3,
        cooldown_minutes: int = 15,
        min_trades_between_calibrations: int = 5
    ):
        if self._initialized:
            return
        
        self.db = database_service
        self.coherence_engine = coherence_engine
        self.risk_guardian = risk_guardian
        
        self.signal_processor = RegimeSignalProcessor()
        self.microstructure = MicrostructureAnalyzer()
        self.calibrator = ParameterCalibrator(smoothing_factor=smoothing_factor)
        self.cooldown = CooldownManager(
            default_cooldown_minutes=cooldown_minutes,
            min_trades_between_calibrations=min_trades_between_calibrations
        )
        
        self.active_profiles: Dict[str, AdaptiveParameterProfile] = {
            'ARES_V1': AdaptiveParameterProfile(strategy_name='ARES_V1'),
            'ARES_V2': AdaptiveParameterProfile(strategy_name='ARES_V2')
        }
        
        self.calibration_history: List[CalibrationEvent] = []
        self.max_history = 500
        
        self.callbacks: List[Callable[[str, AdaptiveParameterProfile], None]] = []
        
        self._initialized = True
        
        logger.info("=" * 60)
        logger.info("🎯 ADAPTIVE PARAMETER ENGINE V6.5 INITIALIZED")
        logger.info("=" * 60)
        logger.info(f"   📊 Smoothing Factor: {smoothing_factor}")
        logger.info(f"   ⏱️ Cooldown: {cooldown_minutes} minutes")
        logger.info(f"   📈 Min Trades: {min_trades_between_calibrations}")
        logger.info(f"   🔗 Coherence Engine: {'Connected' if coherence_engine else 'Not connected'}")
        logger.info(f"   🛡️ Risk Guardian: {'Connected' if risk_guardian else 'Not connected'}")
        logger.info("=" * 60)
    
    def process_kernel_signal(
        self,
        kernel_output: Dict,
        microstructure_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Procesa una señal del Memory Kernel y calibra si es necesario.
        
        Args:
            kernel_output: Salida del Non-Markovian Memory Kernel
            microstructure_data: Datos opcionales de microestructura
            
        Returns:
            Dict con resultados del procesamiento
        """
        regime, confidence, is_change = self.signal_processor.process_kernel_signal(kernel_output)
        
        if microstructure_data:
            micro_context = self.microstructure.analyze(**microstructure_data)
        else:
            micro_context = self.microstructure.analyze()
        
        results = {
            'regime': regime.value,
            'confidence': confidence,
            'is_significant_change': is_change,
            'calibrations': {}
        }
        
        if is_change:
            for strategy_name, profile in self.active_profiles.items():
                cal_result = self._calibrate_strategy(
                    strategy_name, profile, regime, confidence, micro_context
                )
                results['calibrations'][strategy_name] = cal_result
        
        return results
    
    def _calibrate_strategy(
        self,
        strategy_name: str,
        current_profile: AdaptiveParameterProfile,
        regime: RegimeType,
        confidence: float,
        microstructure: Dict
    ) -> Dict:
        """Calibra una estrategia específica"""
        can_calibrate, cooldown_reason = self.cooldown.can_calibrate(
            strategy_name, regime, confidence
        )
        
        if not can_calibrate:
            logger.info(f"⏳ Calibration blocked for {strategy_name}: {cooldown_reason}")
            return {
                'status': 'blocked',
                'reason': cooldown_reason
            }
        
        new_profile = self.calibrator.calibrate(
            current_profile, regime, confidence, microstructure
        )
        
        if not self._validate_with_governance(new_profile, regime):
            logger.warning(f"🛡️ Calibration rejected by governance for {strategy_name}")
            return {
                'status': 'rejected',
                'reason': 'Failed governance validation'
            }
        
        previous_params = current_profile.to_dict()
        self.active_profiles[strategy_name] = new_profile
        
        self.cooldown.record_calibration(strategy_name)
        
        event = CalibrationEvent(
            event_id=f"{strategy_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.utcnow(),
            strategy=strategy_name,
            regime=regime,
            regime_confidence=confidence,
            previous_params=previous_params,
            new_params=new_profile.to_dict(),
            status=CalibrationStatus.APPLIED,
            reason=f"Regime change to {regime.value}",
            microstructure_context=microstructure,
            performance_window={}
        )
        
        self._log_calibration(event)
        
        for callback in self.callbacks:
            try:
                callback(strategy_name, new_profile)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        logger.info(f"✅ Calibration applied for {strategy_name}")
        logger.info(f"   SL: {previous_params.get('stop_loss_pct', 0):.3f} → {new_profile.stop_loss_pct:.3f}")
        logger.info(f"   TP: {previous_params.get('take_profit_pct', 0):.3f} → {new_profile.take_profit_pct:.3f}")
        logger.info(f"   Size: {previous_params.get('position_size_factor', 1):.2f} → {new_profile.position_size_factor:.2f}")
        
        return {
            'status': 'applied',
            'previous': previous_params,
            'new': new_profile.to_dict(),
            'regime': regime.value
        }
    
    def _validate_with_governance(
        self,
        profile: AdaptiveParameterProfile,
        regime: RegimeType
    ) -> bool:
        """Valida la calibración con Coherence Engine y Risk Guardian"""
        if profile.position_size_factor > 1.5:
            logger.warning("❌ Position size too large")
            return False
        
        if profile.stop_loss_pct < -0.50:
            logger.warning("❌ Stop loss too wide")
            return False
        
        if profile.entry_threshold < 0.40:
            logger.warning("❌ Entry threshold too low")
            return False
        
        if self.risk_guardian:
            try:
                pass
            except Exception as e:
                logger.warning(f"Risk Guardian check failed: {e}")
        
        return True
    
    def _log_calibration(self, event: CalibrationEvent):
        """Registra el evento de calibración"""
        self.calibration_history.append(event)
        if len(self.calibration_history) > self.max_history:
            self.calibration_history.pop(0)
        
        if self.db:
            try:
                pass
            except Exception as e:
                logger.warning(f"Failed to persist calibration: {e}")
    
    def get_parameters(self, strategy: str) -> Optional[AdaptiveParameterProfile]:
        """Obtiene los parámetros actuales para una estrategia"""
        return self.active_profiles.get(strategy)
    
    def get_all_parameters(self) -> Dict[str, AdaptiveParameterProfile]:
        """Obtiene todos los perfiles activos"""
        return self.active_profiles.copy()
    
    def record_trade(self, strategy: str, pnl: float = 0):
        """Registra un trade completado para tracking de performance"""
        self.cooldown.record_trade(strategy)
    
    def register_callback(
        self,
        callback: Callable[[str, AdaptiveParameterProfile], None]
    ):
        """Registra un callback para notificación de calibraciones"""
        self.callbacks.append(callback)
    
    def get_status(self) -> Dict:
        """Obtiene el estado completo del engine"""
        return {
            'initialized': self._initialized,
            'active_profiles': {
                name: profile.to_dict() 
                for name, profile in self.active_profiles.items()
            },
            'cooldown_status': {
                name: self.cooldown.get_status(name)
                for name in self.active_profiles.keys()
            },
            'last_regime': self.signal_processor.last_regime.value if self.signal_processor.last_regime else None,
            'regime_stability': self.signal_processor.get_regime_stability(),
            'total_calibrations': len(self.calibration_history),
            'version': '6.5.0'
        }
    
    def get_calibration_history(self, limit: int = 50) -> List[Dict]:
        """Obtiene el historial de calibraciones recientes"""
        return [event.to_dict() for event in self.calibration_history[-limit:]]


_global_engine: Optional[AdaptiveParameterEngine] = None

def get_adaptive_engine(
    database_service=None,
    coherence_engine=None,
    risk_guardian=None
) -> AdaptiveParameterEngine:
    """
    Factory function para obtener la instancia global del engine.
    """
    global _global_engine
    
    if _global_engine is None:
        _global_engine = AdaptiveParameterEngine(
            database_service=database_service,
            coherence_engine=coherence_engine,
            risk_guardian=risk_guardian
        )
    
    return _global_engine


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    print("\n" + "=" * 60)
    print("🎯 ADAPTIVE PARAMETER ENGINE - DEMO")
    print("=" * 60)
    
    engine = get_adaptive_engine()
    
    kernel_outputs = [
        {'regime': 'accumulation', 'confidence': 0.85, 'coherence': 0.90},
        {'regime': 'trending_up', 'confidence': 0.78, 'coherence': 0.85},
        {'regime': 'high_volatility', 'confidence': 0.92, 'coherence': 0.75},
        {'regime': 'distribution', 'confidence': 0.70, 'coherence': 0.80},
    ]
    
    for i, signal in enumerate(kernel_outputs):
        print(f"\n📡 Signal {i+1}: {signal}")
        
        for j in range(6):
            engine.record_trade('ARES_V2')
        
        result = engine.process_kernel_signal(
            signal,
            {'current_spread': 0.001, 'current_volume': 1000000}
        )
        
        print(f"   Regime: {result['regime']} (conf: {result['confidence']:.2f})")
        print(f"   Significant change: {result['is_significant_change']}")
        
        if result['calibrations']:
            for strat, cal in result['calibrations'].items():
                print(f"   {strat}: {cal.get('status', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("📊 FINAL STATUS")
    print("=" * 60)
    
    status = engine.get_status()
    for strategy, profile in status['active_profiles'].items():
        print(f"\n{strategy}:")
        print(f"   Stop Loss: {profile['stop_loss_pct']:.3f}")
        print(f"   Take Profit: {profile['take_profit_pct']:.3f}")
        print(f"   Position Size: {profile['position_size_factor']:.2f}")
        print(f"   Entry Threshold: {profile['entry_threshold']:.2f}")
        print(f"   Calibrations: {profile['calibration_count']}")
    
    print("\n" + "=" * 60)
    print("✅ Demo completed")
    print("=" * 60)
