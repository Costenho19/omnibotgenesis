#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 CAES - CONFIDENCE-ADAPTIVE ENTRY SYSTEM
OMNIX INSTITUTIONAL+ - Sistema de Entrada Adaptativa por Confianza

Este módulo implementa un sistema de ajuste dinámico de agresividad de trading
basado en la confianza del Non-Markovian Kernel y el sub-régimen de mercado detectado.

ARQUITECTURA:
    Non-Markovian Kernel (confidence 0-100%)
             ↓
        CAES Module (sigmoide + sub-régimen)
             ↓
        Adaptive Engine (posición/SL/TP)
             ↓
        ARES V1/V2 Execution

FÓRMULA PRINCIPAL:
    aggression = 1 + (2 / (1 + exp(-10 * (confidence - 0.7))))
    final = aggression * regime_multiplier
    
    Resultado:
    - 50% conf → 0.8x tamaño (más conservador)
    - 70% conf → 1.5x tamaño
    - 85% conf → 2.2x tamaño
    - 95% conf → 2.8x tamaño (máximo 3x por límites de riesgo)

Harold Nunes - Diciembre 2025
OMNIX INSTITUTIONAL+ - Fuera de Serie
"""

import logging
import math
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class SubRegimeType(Enum):
    """
    Sub-regímenes de mercado para ajuste fino de parámetros.
    Más granular que BULL/BEAR/SIDEWAYS básicos.
    """
    BULL_STRONG = "bull_strong"
    BULL_WEAK = "bull_weak"
    BEAR_PANIC = "bear_panic"
    BEAR_CONTROLLED = "bear_controlled"
    SIDEWAYS_COMPRESSED = "sideways_compressed"
    SIDEWAYS_EXPANDING = "sideways_expanding"
    BREAKOUT_UP = "breakout_up"
    BREAKOUT_DOWN = "breakout_down"
    REVERSAL_BULLISH = "reversal_bullish"
    REVERSAL_BEARISH = "reversal_bearish"
    UNKNOWN = "unknown"


@dataclass
class CAESResult:
    """Resultado del cálculo CAES con todos los parámetros adaptativos"""
    aggression_factor: float
    position_multiplier: float
    stop_loss_adjustment: float
    take_profit_adjustment: float
    risk_reward_ratio: float
    trailing_start_pct: float
    max_position_pct: float
    confidence_input: float
    sub_regime: SubRegimeType
    recommendation: str
    timestamp: datetime


class ConfidenceAdaptiveEntrySystem:
    """
    🎯 CAES - Confidence-Adaptive Entry System
    
    Sistema que ajusta dinámicamente la agresividad de entrada basándose en:
    1. Confianza del Non-Markovian Kernel (0-100%)
    2. Sub-régimen de mercado detectado
    3. Historial de rendimiento en condiciones similares
    
    Implementa función sigmoide para transiciones suaves entre niveles de agresividad.
    """
    
    def __init__(self, 
                 base_position_size: float = 2.0,
                 min_aggression: float = 0.5,
                 max_aggression: float = 3.0,
                 sigmoid_center: float = 0.70,
                 sigmoid_steepness: float = 10.0):
        """
        Inicializa CAES con configuración base.
        
        Args:
            base_position_size: Tamaño base de posición (% del capital)
            min_aggression: Multiplicador mínimo de agresividad
            max_aggression: Multiplicador máximo de agresividad (cap de seguridad)
            sigmoid_center: Centro de la función sigmoide (70% = punto de inflexión)
            sigmoid_steepness: Pendiente de la sigmoide (10 = transición suave)
        """
        self.base_position_size = base_position_size
        self.min_aggression = min_aggression
        self.max_aggression = max_aggression
        self.sigmoid_center = sigmoid_center
        self.sigmoid_steepness = sigmoid_steepness
        
        self.regime_multipliers = {
            SubRegimeType.BULL_STRONG: 1.20,
            SubRegimeType.BULL_WEAK: 0.85,
            SubRegimeType.BEAR_PANIC: 0.50,
            SubRegimeType.BEAR_CONTROLLED: 0.70,
            SubRegimeType.SIDEWAYS_COMPRESSED: 0.75,
            SubRegimeType.SIDEWAYS_EXPANDING: 0.90,
            SubRegimeType.BREAKOUT_UP: 1.30,
            SubRegimeType.BREAKOUT_DOWN: 0.60,
            SubRegimeType.REVERSAL_BULLISH: 1.10,
            SubRegimeType.REVERSAL_BEARISH: 0.65,
            SubRegimeType.UNKNOWN: 0.80
        }
        
        self.regime_risk_params = {
            SubRegimeType.BULL_STRONG: {
                "sl_factor": 0.8,
                "tp_factor": 1.3,
                "rr_ratio": 2.5,
                "trailing_start": 1.0,
                "max_position": 5.0
            },
            SubRegimeType.BULL_WEAK: {
                "sl_factor": 0.9,
                "tp_factor": 1.0,
                "rr_ratio": 1.8,
                "trailing_start": 1.5,
                "max_position": 3.5
            },
            SubRegimeType.BEAR_PANIC: {
                "sl_factor": 0.6,
                "tp_factor": 0.8,
                "rr_ratio": 3.0,
                "trailing_start": 0.5,
                "max_position": 2.0
            },
            SubRegimeType.BEAR_CONTROLLED: {
                "sl_factor": 0.75,
                "tp_factor": 0.9,
                "rr_ratio": 2.2,
                "trailing_start": 0.8,
                "max_position": 2.5
            },
            SubRegimeType.SIDEWAYS_COMPRESSED: {
                "sl_factor": 0.7,
                "tp_factor": 0.85,
                "rr_ratio": 1.5,
                "trailing_start": 0.3,
                "max_position": 3.0
            },
            SubRegimeType.SIDEWAYS_EXPANDING: {
                "sl_factor": 0.85,
                "tp_factor": 1.1,
                "rr_ratio": 2.0,
                "trailing_start": 1.2,
                "max_position": 3.5
            },
            SubRegimeType.BREAKOUT_UP: {
                "sl_factor": 0.7,
                "tp_factor": 1.5,
                "rr_ratio": 3.0,
                "trailing_start": 0.8,
                "max_position": 4.5
            },
            SubRegimeType.BREAKOUT_DOWN: {
                "sl_factor": 0.5,
                "tp_factor": 0.7,
                "rr_ratio": 2.5,
                "trailing_start": 0.4,
                "max_position": 2.0
            },
            SubRegimeType.REVERSAL_BULLISH: {
                "sl_factor": 0.85,
                "tp_factor": 1.2,
                "rr_ratio": 2.2,
                "trailing_start": 1.0,
                "max_position": 4.0
            },
            SubRegimeType.REVERSAL_BEARISH: {
                "sl_factor": 0.6,
                "tp_factor": 0.8,
                "rr_ratio": 2.0,
                "trailing_start": 0.6,
                "max_position": 2.5
            },
            SubRegimeType.UNKNOWN: {
                "sl_factor": 0.75,
                "tp_factor": 0.9,
                "rr_ratio": 1.8,
                "trailing_start": 1.0,
                "max_position": 3.0
            }
        }
        
        self._last_calculation: Optional[CAESResult] = None
        
        logger.info("=" * 70)
        logger.info("🎯 CAES - CONFIDENCE-ADAPTIVE ENTRY SYSTEM INITIALIZED")
        logger.info(f"   📊 Base Position Size: {base_position_size}%")
        logger.info(f"   🎚️ Aggression Range: {min_aggression}x - {max_aggression}x")
        logger.info(f"   📈 Sigmoid Center: {sigmoid_center*100:.0f}% confidence")
        logger.info(f"   🔧 Sub-Regimes: {len(self.regime_multipliers)} configured")
        logger.info("=" * 70)
    
    def calculate_sigmoid_aggression(self, confidence: float) -> float:
        """
        Calcula el factor de agresividad usando función sigmoide.
        
        La sigmoide proporciona transiciones suaves:
        - Baja confianza (<50%): Valores conservadores ~0.8x
        - Media confianza (70%): Punto de inflexión ~1.5x
        - Alta confianza (>85%): Valores agresivos hasta 3.0x
        
        Args:
            confidence: Confianza del kernel (0.0 - 1.0)
            
        Returns:
            Factor de agresividad (min_aggression - max_aggression)
        """
        confidence = max(0.0, min(1.0, confidence))
        
        exponent = -self.sigmoid_steepness * (confidence - self.sigmoid_center)
        sigmoid_value = 1 / (1 + math.exp(exponent))
        
        aggression_range = self.max_aggression - self.min_aggression
        aggression = self.min_aggression + (sigmoid_value * aggression_range)
        
        return round(aggression, 3)
    
    def detect_sub_regime(self, 
                          kernel_metrics: Dict[str, Any],
                          volatility: float = 0.0,
                          momentum: float = 0.0,
                          volume_ratio: float = 1.0) -> SubRegimeType:
        """
        Detecta el sub-régimen de mercado basado en métricas del kernel.
        
        Args:
            kernel_metrics: Métricas del Non-Markovian Kernel
            volatility: Volatilidad actual (0-1)
            momentum: Momentum actual (-1 a 1)
            volume_ratio: Ratio de volumen vs promedio
            
        Returns:
            SubRegimeType detectado
        """
        regime = kernel_metrics.get('regime', 'UNKNOWN')
        regime_confidence = kernel_metrics.get('regime_confidence', 0)
        memory_coherence = kernel_metrics.get('memory_coherence', 0)
        trend_strength = kernel_metrics.get('trend_strength', 0)
        
        if regime == 'TRENDING' or regime == 'BULLISH':
            if trend_strength > 0.7 and momentum > 0.5:
                return SubRegimeType.BULL_STRONG
            elif trend_strength > 0.3:
                return SubRegimeType.BULL_WEAK
            elif momentum < -0.3:
                return SubRegimeType.REVERSAL_BEARISH
        
        elif regime == 'BEARISH':
            if volatility > 0.7 and momentum < -0.7:
                return SubRegimeType.BEAR_PANIC
            elif trend_strength > 0.3:
                return SubRegimeType.BEAR_CONTROLLED
            elif momentum > 0.3:
                return SubRegimeType.REVERSAL_BULLISH
        
        elif regime == 'RANGING' or regime == 'SIDEWAYS':
            if volatility < 0.3:
                return SubRegimeType.SIDEWAYS_COMPRESSED
            else:
                return SubRegimeType.SIDEWAYS_EXPANDING
        
        elif regime == 'VOLATILE':
            if momentum > 0.5:
                return SubRegimeType.BREAKOUT_UP
            elif momentum < -0.5:
                return SubRegimeType.BREAKOUT_DOWN
        
        return SubRegimeType.UNKNOWN
    
    def calculate_adaptive_parameters(self,
                                       kernel_confidence: float,
                                       kernel_metrics: Optional[Dict] = None,
                                       volatility: float = 0.0,
                                       momentum: float = 0.0,
                                       volume_ratio: float = 1.0,
                                       atr_ratio: float = 1.0) -> CAESResult:
        """
        Calcula todos los parámetros adaptativos basados en confianza y régimen.
        
        Este es el método principal de CAES que produce:
        - Factor de agresividad (multiplicador de posición)
        - Ajustes de Stop Loss
        - Ajustes de Take Profit
        - Risk/Reward ratio óptimo
        - Punto de inicio de trailing stop
        - Límite máximo de posición
        
        MITIGACIÓN DE CONFLICTO DE INTERÉS (V6.5.4):
        El Kernel Confidence es validado por métricas externas independientes:
        1. ATR ratio (volatilidad histórica) - Si ATR > 2x normal, cap aggression at 1.5x
        2. Regime multiplier - Módulo independiente reduce aggression en regímenes adversos
        3. Hard system cap - Máximo absoluto de 3.0x
        
        Args:
            kernel_confidence: Confianza del Non-Markovian Kernel (0-100%)
            kernel_metrics: Métricas adicionales del kernel (opcional)
            volatility: Volatilidad actual (0-1)
            momentum: Momentum actual (-1 a 1)
            volume_ratio: Ratio de volumen vs promedio
            atr_ratio: ATR actual / ATR promedio histórico (1.0 = normal, >2.0 = muy alta)
            
        Returns:
            CAESResult con todos los parámetros calculados
        """
        confidence = kernel_confidence / 100.0 if kernel_confidence > 1 else kernel_confidence
        
        kernel_metrics = kernel_metrics or {}
        sub_regime = self.detect_sub_regime(kernel_metrics, volatility, momentum, volume_ratio)
        
        base_aggression = self.calculate_sigmoid_aggression(confidence)
        
        regime_multiplier = self.regime_multipliers.get(sub_regime, 1.0)
        
        # ============================================================
        # V6.5.4 CONFLICT OF INTEREST MITIGATION: ATR-Based Validation
        # ============================================================
        # El ATR ratio es una métrica EXTERNA e INDEPENDIENTE del Kernel.
        # Si la volatilidad está muy alta, capea la agresividad sin importar
        # qué tan alta sea la confianza del Kernel.
        # Esto previene que el Kernel se "auto-proclame" muy confiable
        # en condiciones de mercado peligrosas.
        
        atr_cap = self.max_aggression  # Default: sin cap adicional
        if atr_ratio > 2.0:
            # Volatilidad muy alta: cap agresivo a 1.5x máximo
            atr_cap = 1.5
            logger.warning(f"⚠️ ATR VALIDATION: ATR ratio {atr_ratio:.2f} > 2.0 → Capping aggression at 1.5x")
        elif atr_ratio > 1.5:
            # Volatilidad elevada: cap a 2.0x
            atr_cap = 2.0
            logger.info(f"📊 ATR VALIDATION: ATR ratio {atr_ratio:.2f} > 1.5 → Capping aggression at 2.0x")
        
        # Aplicar todos los multiplicadores y caps
        final_aggression = base_aggression * regime_multiplier
        final_aggression = min(final_aggression, atr_cap)  # ATR cap (independiente)
        final_aggression = max(self.min_aggression, min(self.max_aggression, final_aggression))  # System caps
        
        risk_params = self.regime_risk_params.get(sub_regime, self.regime_risk_params[SubRegimeType.UNKNOWN])
        
        confidence_sl_adjustment = 1.0 - (confidence * 0.3)
        sl_adjustment = risk_params["sl_factor"] * confidence_sl_adjustment
        
        confidence_tp_adjustment = 1.0 + (confidence * 0.4)
        tp_adjustment = risk_params["tp_factor"] * confidence_tp_adjustment
        
        position_multiplier = final_aggression
        
        recommendation = self._generate_recommendation(
            confidence, sub_regime, final_aggression, risk_params["rr_ratio"]
        )
        
        result = CAESResult(
            aggression_factor=round(final_aggression, 3),
            position_multiplier=round(position_multiplier, 3),
            stop_loss_adjustment=round(sl_adjustment, 3),
            take_profit_adjustment=round(tp_adjustment, 3),
            risk_reward_ratio=risk_params["rr_ratio"],
            trailing_start_pct=risk_params["trailing_start"],
            max_position_pct=risk_params["max_position"],
            confidence_input=round(confidence * 100, 1),
            sub_regime=sub_regime,
            recommendation=recommendation,
            timestamp=datetime.utcnow()
        )
        
        self._last_calculation = result
        
        logger.info(f"🎯 CAES: Confidence={confidence*100:.1f}% | SubRegime={sub_regime.value}")
        logger.info(f"   📊 Aggression={final_aggression:.2f}x | Position={position_multiplier:.2f}x")
        logger.info(f"   🎚️ SL_adj={sl_adjustment:.2f} | TP_adj={tp_adjustment:.2f} | R:R={risk_params['rr_ratio']:.1f}")
        
        return result
    
    def _generate_recommendation(self, 
                                  confidence: float, 
                                  sub_regime: SubRegimeType,
                                  aggression: float,
                                  rr_ratio: float) -> str:
        """Genera recomendación en texto para logging y dashboard"""
        if confidence >= 0.85:
            strength = "MUY ALTA"
            action = "Entrada agresiva recomendada"
        elif confidence >= 0.70:
            strength = "ALTA"
            action = "Entrada normal con tamaño incrementado"
        elif confidence >= 0.55:
            strength = "MEDIA"
            action = "Entrada conservadora"
        elif confidence >= 0.40:
            strength = "BAJA"
            action = "Entrada mínima o esperar"
        else:
            strength = "MUY BAJA"
            action = "NO OPERAR - Señal insuficiente"
        
        return f"{strength} confianza ({confidence*100:.0f}%) en {sub_regime.value} | {action} | Aggression: {aggression:.1f}x | R:R: {rr_ratio:.1f}"
    
    def get_position_size(self, 
                          capital: float, 
                          kernel_confidence: float,
                          kernel_metrics: Optional[Dict] = None) -> Tuple[float, CAESResult]:
        """
        Calcula el tamaño de posición adaptativo.
        
        Args:
            capital: Capital disponible en USD
            kernel_confidence: Confianza del kernel (0-100%)
            kernel_metrics: Métricas adicionales del kernel
            
        Returns:
            Tuple de (position_size_usd, caes_result)
        """
        caes = self.calculate_adaptive_parameters(kernel_confidence, kernel_metrics)
        
        base_position = capital * (self.base_position_size / 100)
        adaptive_position = base_position * caes.position_multiplier
        
        max_allowed = capital * (caes.max_position_pct / 100)
        final_position = min(adaptive_position, max_allowed)
        
        logger.info(f"🎯 CAES Position: ${final_position:,.2f} (Base: ${base_position:,.2f} × {caes.position_multiplier:.2f}x)")
        
        return final_position, caes
    
    def get_stop_loss(self, 
                      entry_price: float, 
                      base_sl_pct: float,
                      caes_result: CAESResult) -> float:
        """
        Calcula el Stop Loss adaptativo.
        
        Args:
            entry_price: Precio de entrada
            base_sl_pct: Stop loss base en porcentaje (negativo, ej: -0.02 para -2%)
            caes_result: Resultado previo de CAES
            
        Returns:
            Precio de stop loss ajustado
        """
        adjusted_sl_pct = base_sl_pct * caes_result.stop_loss_adjustment
        adjusted_sl_pct = max(-0.05, min(-0.005, adjusted_sl_pct))
        
        stop_loss_price = entry_price * (1 + adjusted_sl_pct)
        
        logger.debug(f"🛡️ CAES SL: Base={base_sl_pct*100:.2f}% → Adjusted={adjusted_sl_pct*100:.2f}% → ${stop_loss_price:.2f}")
        
        return stop_loss_price
    
    def get_take_profit(self, 
                        entry_price: float, 
                        base_tp_pct: float,
                        caes_result: CAESResult) -> float:
        """
        Calcula el Take Profit adaptativo.
        
        Args:
            entry_price: Precio de entrada
            base_tp_pct: Take profit base en porcentaje (positivo, ej: 0.025 para +2.5%)
            caes_result: Resultado previo de CAES
            
        Returns:
            Precio de take profit ajustado
        """
        adjusted_tp_pct = base_tp_pct * caes_result.take_profit_adjustment
        adjusted_tp_pct = max(0.005, min(0.10, adjusted_tp_pct))
        
        take_profit_price = entry_price * (1 + adjusted_tp_pct)
        
        logger.debug(f"🎯 CAES TP: Base={base_tp_pct*100:.2f}% → Adjusted={adjusted_tp_pct*100:.2f}% → ${take_profit_price:.2f}")
        
        return take_profit_price
    
    def get_last_calculation(self) -> Optional[CAESResult]:
        """Retorna el último cálculo CAES realizado"""
        return self._last_calculation
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa la configuración actual de CAES"""
        return {
            "base_position_size": self.base_position_size,
            "min_aggression": self.min_aggression,
            "max_aggression": self.max_aggression,
            "sigmoid_center": self.sigmoid_center,
            "sigmoid_steepness": self.sigmoid_steepness,
            "regime_count": len(self.regime_multipliers),
            "last_calculation": {
                "aggression": self._last_calculation.aggression_factor if self._last_calculation else None,
                "regime": self._last_calculation.sub_regime.value if self._last_calculation else None,
                "timestamp": self._last_calculation.timestamp.isoformat() if self._last_calculation else None
            }
        }


_caes_instance: Optional[ConfidenceAdaptiveEntrySystem] = None

def get_caes_instance() -> ConfidenceAdaptiveEntrySystem:
    """Obtiene o crea la instancia singleton de CAES"""
    global _caes_instance
    if _caes_instance is None:
        _caes_instance = ConfidenceAdaptiveEntrySystem()
    return _caes_instance

def calculate_adaptive_entry(kernel_confidence: float,
                              kernel_metrics: Optional[Dict] = None,
                              capital: float = 1000000.0) -> Tuple[float, CAESResult]:
    """
    Función de conveniencia para calcular entrada adaptativa.
    
    Args:
        kernel_confidence: Confianza del Non-Markovian Kernel (0-100%)
        kernel_metrics: Métricas adicionales del kernel
        capital: Capital disponible en USD
        
    Returns:
        Tuple de (position_size_usd, caes_result)
    """
    caes = get_caes_instance()
    return caes.get_position_size(capital, kernel_confidence, kernel_metrics)
