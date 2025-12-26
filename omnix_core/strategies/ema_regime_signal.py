#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 EMA REGIME SIGNAL - SEÑAL REAL DETERMINÍSTICA
OMNIX V6.5.4d INSTITUTIONAL+

Esta es la SEÑAL PRINCIPAL del sistema - reemplaza outputs pseudo-aleatorios de ARES.
Genera señales explicables basadas en:
- EMA slope (tendencia)
- ATR (volatilidad)
- HMM regime (estado de mercado)

CONTRATO DE SALIDA:
{
    "direction": "LONG" | "SHORT" | "NONE",
    "confidence": 0.0 - 1.0,
    "stop_loss": float,
    "take_profit": float,
    "rationale": ["TREND_UP", "LOW_VOL", "BULLISH_REGIME", ...]
}

Harold Nunes - Diciembre 2025
V6.5.4d-fix2: Raw slope detection for WEAK_TREND (Dec 26 2025)
V6.5.4d-fix3: Import LOW_VOL_MODE from trading_profiles.py (Dec 26 2025)
V6.5.4d-fix4: Add diagnostic logging for WEAK_TREND condition (Dec 26 2025)
"""

import logging
import numpy as np
from typing import Dict, Optional, List, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Import TRACK_RECORD_MODE and LOW_VOL_MODE flags from central config
try:
    from omnix_core.config.trading_profiles import TRACK_RECORD_MODE, LOW_VOL_MODE
except ImportError:
    TRACK_RECORD_MODE = False
    LOW_VOL_MODE = True  # Default to True for safety during low-liquidity periods

@dataclass
class SignalContract:
    direction: str
    confidence: float
    stop_loss: float
    take_profit: float
    rationale: List[str]
    timestamp: datetime
    symbol: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction,
            "confidence": self.confidence,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "rationale": self.rationale,
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol
        }


class EMARegimeSignal:
    """
    Generador de señales REALES y EXPLICABLES.
    NO usa randomización - todas las decisiones son determinísticas.
    """
    
    def __init__(self):
        self.name = "EMA_REGIME_SIGNAL"
        self.version = "1.0.3"
        self.status = "ACTIVE"
        
        # ============================================================
        # SEASONAL: LOW_VOL_MODE - Holiday/Low-Liquidity Markets
        # Dec 26, 2025: Now imported from trading_profiles.py for sync
        # ============================================================
        self.LOW_VOL_MODE = LOW_VOL_MODE  # Use central config value
        
        # Base configuration
        base_min_confidence = 0.35  # Standard threshold
        low_vol_min_confidence = 0.30  # Reduced for low-volatility regimes
        
        # Dec 25, 2025 - Low-volatility market adjustment
        # Reduced trend_strength threshold (0.30 → 0.15) and min_confidence (0.50 → 0.35)
        # to allow signal generation in low-liquidity/holiday market regimes.
        # Risk remains controlled via Monte Carlo VETO and Coherence Gate.
        # This is a Seasonal Parameter Adjustment - review after market normalizes.
        self.config = {
            "ema_fast": 12,
            "ema_slow": 26,
            "atr_period": 14,
            "trend_threshold": 0.001,
            "volatility_low": 0.01,
            "volatility_high": 0.03,
            "min_confidence": low_vol_min_confidence if self.LOW_VOL_MODE else base_min_confidence,
            "min_trend_strength": 0.15,  # Dec 25: 0.30 → 0.15 (low-vol adjustment)
            "default_sl_pct": 0.02,
            "default_tp_pct": 0.04,
        }
        
        logger.info("=" * 70)
        logger.info("📊 EMA REGIME SIGNAL V1.0.3 INICIALIZADO")
        logger.info("   🔬 Señal REAL: EMA slope + ATR + HMM regime")
        logger.info("   ✅ STATUS: ACTIVE (reemplaza ARES placeholders)")
        logger.info(f"   🧪 TRACK_RECORD_MODE: {TRACK_RECORD_MODE}")
        logger.info(f"   ⚠️  LOW_VOL_MODE: {self.LOW_VOL_MODE}")
        if self.LOW_VOL_MODE:
            logger.info("   📅 SEASONAL: Christmas-January low-liquidity (min_confidence=0.30)")
        else:
            logger.info("   📈 NORMAL_MODE: min_confidence=0.35")
        if TRACK_RECORD_MODE and self.LOW_VOL_MODE:
            logger.info("   ✅ WEAK_TREND fallback ENABLED for low-conviction signals")
        logger.info("=" * 70)
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Calcula EMA con el período dado."""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        return ema
    
    def calculate_atr(self, highs: List[float], lows: List[float], 
                      closes: List[float], period: int = 14) -> float:
        """Calcula Average True Range."""
        if len(closes) < 2:
            return 0.0
        
        true_ranges = []
        for i in range(1, min(len(closes), period + 1)):
            high_low = highs[i] - lows[i] if i < len(highs) and i < len(lows) else 0
            high_close = abs(highs[i] - closes[i-1]) if i < len(highs) else 0
            low_close = abs(lows[i] - closes[i-1]) if i < len(lows) else 0
            true_ranges.append(max(high_low, high_close, low_close))
        
        return np.mean(true_ranges) if true_ranges else 0.0
    
    def calculate_ema_slope(self, prices: List[float], period: int = 12) -> float:
        """Calcula la pendiente de la EMA (cambio porcentual reciente)."""
        if len(prices) < period + 5:
            return 0.0
        
        ema_current = self.calculate_ema(prices, period)
        ema_previous = self.calculate_ema(prices[:-5], period)
        
        if ema_previous == 0:
            return 0.0
        
        return (ema_current - ema_previous) / ema_previous
    
    def detect_trend(self, prices: List[float]) -> tuple:
        """
        Detecta tendencia usando cruce de EMAs.
        Returns: (direction, strength)
        """
        if len(prices) < self.config["ema_slow"]:
            return "NEUTRAL", 0.0
        
        ema_fast = self.calculate_ema(prices, self.config["ema_fast"])
        ema_slow = self.calculate_ema(prices, self.config["ema_slow"])
        slope = self.calculate_ema_slope(prices, self.config["ema_fast"])
        
        diff_pct = (ema_fast - ema_slow) / ema_slow if ema_slow != 0 else 0
        
        if diff_pct > self.config["trend_threshold"] and slope > 0:
            strength = min(abs(diff_pct) * 10, 1.0)
            return "BULLISH", strength
        elif diff_pct < -self.config["trend_threshold"] and slope < 0:
            strength = min(abs(diff_pct) * 10, 1.0)
            return "BEARISH", strength
        else:
            return "NEUTRAL", 0.0
    
    def assess_volatility(self, atr: float, current_price: float) -> tuple:
        """
        Evalúa volatilidad relativa.
        Returns: (class, score)
        """
        if current_price == 0:
            return "UNKNOWN", 0.5
        
        atr_pct = atr / current_price
        
        if atr_pct < self.config["volatility_low"]:
            return "LOW", 0.8
        elif atr_pct > self.config["volatility_high"]:
            return "HIGH", 0.3
        else:
            return "NORMAL", 0.6
    
    def interpret_hmm_regime(self, regime_data: Optional[Dict]) -> tuple:
        """
        Interpreta el régimen HMM del mercado.
        Returns: (regime_type, confidence)
        """
        if not regime_data:
            return "UNKNOWN", 0.5
        
        regime_type = regime_data.get("regime", "UNKNOWN")
        confidence = regime_data.get("confidence", 0.5)
        
        if regime_type in ["BULLISH", "TRENDING_UP"]:
            return "BULLISH_REGIME", confidence
        elif regime_type in ["BEARISH", "TRENDING_DOWN"]:
            return "BEARISH_REGIME", confidence
        elif regime_type in ["RANGING", "SIDEWAYS"]:
            return "RANGING_REGIME", confidence * 0.7
        else:
            return "VOLATILE_REGIME", confidence * 0.5
    
    def generate_signal(
        self,
        symbol: str,
        prices: List[float],
        highs: Optional[List[float]] = None,
        lows: Optional[List[float]] = None,
        hmm_regime: Optional[Dict] = None,
        current_price: Optional[float] = None
    ) -> SignalContract:
        """
        Genera señal REAL y EXPLICABLE.
        
        Args:
            symbol: Par de trading (ej: "BTC/USD")
            prices: Lista de precios de cierre históricos
            highs: Lista de máximos (opcional, para ATR)
            lows: Lista de mínimos (opcional, para ATR)
            hmm_regime: Datos del régimen HMM (opcional)
            current_price: Precio actual (si no se provee, usa último de prices)
        
        Returns:
            SignalContract con todos los campos requeridos
        """
        rationale = []
        confidence_factors = []
        
        if not prices or len(prices) < 30:
            logger.warning(f"📊 {symbol}: Datos insuficientes ({len(prices) if prices else 0} precios)")
            return SignalContract(
                direction="NONE",
                confidence=0.0,
                stop_loss=0.0,
                take_profit=0.0,
                rationale=["INSUFFICIENT_DATA"],
                timestamp=datetime.utcnow(),
                symbol=symbol
            )
        
        price = current_price or prices[-1]
        
        trend_dir, trend_strength = self.detect_trend(prices)
        rationale.append(f"TREND_{trend_dir}")
        confidence_factors.append(trend_strength)
        
        if highs and lows and len(highs) >= 14 and len(lows) >= 14:
            atr = self.calculate_atr(highs, lows, prices)
        else:
            returns = np.diff(prices[-20:]) / prices[-20:-1] if len(prices) > 20 else []
            atr = np.std(returns) * price if len(returns) > 0 else price * 0.02
        
        vol_class, vol_score = self.assess_volatility(atr, price)
        rationale.append(f"VOLATILITY_{vol_class}")
        confidence_factors.append(vol_score)
        
        regime_type, regime_conf = self.interpret_hmm_regime(hmm_regime)
        rationale.append(regime_type)
        confidence_factors.append(regime_conf)
        
        # Dec 25, 2025: Use configurable min_trend_strength (was hardcoded 0.3)
        min_trend = self.config.get("min_trend_strength", 0.15)
        
        if trend_dir == "BULLISH" and trend_strength > min_trend:
            direction = "LONG"
            if regime_type == "BULLISH_REGIME":
                rationale.append("TREND_REGIME_ALIGNED")
                confidence_factors.append(0.9)
            elif regime_type == "BEARISH_REGIME":
                rationale.append("TREND_REGIME_CONFLICT")
                confidence_factors.append(0.4)
        elif trend_dir == "BEARISH" and trend_strength > min_trend:
            direction = "SHORT"
            if regime_type == "BEARISH_REGIME":
                rationale.append("TREND_REGIME_ALIGNED")
                confidence_factors.append(0.9)
            elif regime_type == "BULLISH_REGIME":
                rationale.append("TREND_REGIME_CONFLICT")
                confidence_factors.append(0.4)
        else:
            direction = "NONE"
            rationale.append("NO_CLEAR_DIRECTION")
            confidence_factors.append(0.3)
        
        if vol_class == "HIGH":
            rationale.append("HIGH_VOL_CAUTION")
            confidence_factors.append(0.5)
        elif vol_class == "LOW":
            rationale.append("LOW_VOL_FAVORABLE")
            confidence_factors.append(0.8)
        
        confidence = np.mean(confidence_factors) if confidence_factors else 0.0
        confidence = max(0.0, min(1.0, confidence))
        
        if direction == "NONE" or confidence < self.config["min_confidence"]:
            # ============================================================
            # TRACK_RECORD_MODE: Convert NONE to WEAK_TREND for scoring
            # Dec 26, 2025: Allows partial scoring without forcing direction
            # ============================================================
            # DEBUG: Log condition values (INFO level for visibility)
            logger.info(f"🔍 {symbol} WEAK_TREND_CHECK: dir={direction}, TRACK_RECORD={TRACK_RECORD_MODE}, LOW_VOL={self.LOW_VOL_MODE}")
            if TRACK_RECORD_MODE and self.LOW_VOL_MODE and direction == "NONE":
                # ============================================================
                # TRACK_RECORD_MODE: Use raw EMA slope for weak direction
                # Dec 26, 2025: detect_trend returns NEUTRAL when market flat,
                # but we can use the raw slope to determine a weak bias
                # ============================================================
                raw_slope = self.calculate_ema_slope(prices, self.config["ema_fast"])
                
                if trend_dir == "BULLISH" or raw_slope > 0.0001:
                    direction = "LONG"
                    confidence = 0.30  # Fixed low confidence for track record
                    rationale.append("WEAK_TREND_LONG")
                    rationale.append("TRACK_RECORD_MODE_ACTIVE")
                    logger.info(f"🧪 {symbol}: TRACK_RECORD_MODE activated - WEAK_TREND LONG (slope={raw_slope:.6f})")
                elif trend_dir == "BEARISH" or raw_slope < -0.0001:
                    direction = "SHORT"
                    confidence = 0.30
                    rationale.append("WEAK_TREND_SHORT")
                    rationale.append("TRACK_RECORD_MODE_ACTIVE")
                    logger.info(f"🧪 {symbol}: TRACK_RECORD_MODE activated - WEAK_TREND SHORT (slope={raw_slope:.6f})")
                else:
                    # Truly flat market (slope within ±0.0001) - stay NONE
                    direction = "NONE"
                    rationale.append("FLAT_MARKET_NO_BIAS")
                    logger.info(f"🧪 {symbol}: TRACK_RECORD_MODE - FLAT MARKET (slope={raw_slope:.6f}) → HOLD")
            else:
                direction = "NONE"
                rationale.append("BELOW_MIN_CONFIDENCE")
        
        atr_pct = atr / price if price > 0 else self.config["default_sl_pct"]
        sl_pct = max(atr_pct * 1.5, self.config["default_sl_pct"])
        tp_pct = max(atr_pct * 3.0, self.config["default_tp_pct"])
        
        if direction == "LONG":
            stop_loss = price * (1 - sl_pct)
            take_profit = price * (1 + tp_pct)
        elif direction == "SHORT":
            stop_loss = price * (1 + sl_pct)
            take_profit = price * (1 - tp_pct)
        else:
            stop_loss = 0.0
            take_profit = 0.0
        
        signal = SignalContract(
            direction=direction,
            confidence=round(confidence, 4),
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            rationale=rationale,
            timestamp=datetime.utcnow(),
            symbol=symbol
        )
        
        logger.info(
            f"📊 {symbol} SIGNAL: {direction} | Confidence: {confidence:.1%} | "
            f"SL: ${stop_loss:.2f} | TP: ${take_profit:.2f} | "
            f"Rationale: {', '.join(rationale)}"
        )
        
        return signal
    
    def validate_for_execution(self, signal: SignalContract, 
                                min_confidence: float = 0.55) -> tuple:
        """
        Valida si una señal debe ejecutarse.
        Returns: (should_execute, reasons)
        """
        reasons = []
        
        if signal.direction == "NONE":
            reasons.append("NO_DIRECTION")
            return False, reasons
        
        if signal.confidence < min_confidence:
            reasons.append(f"LOW_CONFIDENCE_{signal.confidence:.1%}")
            return False, reasons
        
        if "TREND_REGIME_CONFLICT" in signal.rationale:
            reasons.append("REGIME_CONFLICT")
            return False, reasons
        
        if "HIGH_VOL_CAUTION" in signal.rationale and signal.confidence < 0.7:
            reasons.append("HIGH_VOL_LOW_CONFIDENCE")
            return False, reasons
        
        reasons.append("SIGNAL_VALID")
        return True, reasons


_signal_generator: Optional[EMARegimeSignal] = None

def get_signal_generator() -> EMARegimeSignal:
    """Singleton para el generador de señales."""
    global _signal_generator
    if _signal_generator is None:
        _signal_generator = EMARegimeSignal()
    return _signal_generator
