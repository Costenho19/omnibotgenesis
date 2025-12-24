"""
🧬 ARES-STOCK V6.2 - Adaptive Regime-based Execution System for Stocks
Sistema de ejecución adaptativo basado en régimen para acciones
Portado de ARES V1/V2 crypto con parámetros ajustados
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    CRISIS = "crisis"
    UNKNOWN = "unknown"


class StrategyMode(Enum):
    SWING = "swing"
    POSITION = "position"
    DEFENSIVE = "defensive"


@dataclass
class ARESSignal:
    signal: float
    mode: StrategyMode
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    position_size: float
    confidence: float
    reasons: List[str]


class ARESStock:
    """
    ARES-STOCK: Sistema de Trading Adaptativo para Acciones
    
    Características:
    - Swing Trading (días a semanas) en régimen Bull/Sideways
    - Position Trading (semanas a meses) en régimen estable
    - Modo Defensivo en régimen Bear/Crisis
    
    Diferencias vs ARES Crypto:
    - Volatilidad floor más baja (0.6% vs 2%)
    - Leverage máximo 2x vs 5x
    - Stops más ajustados (5% vs 15%)
    - Sin trading 24/7 (respeta horarios de mercado)
    """
    
    STOCK_CONFIG = {
        StrategyMode.SWING: {
            'lookback': 20,
            'min_volatility': 0.005,
            'max_volatility': 0.025,
            'stop_loss_pct': 0.03,
            'take_profit_pct': 0.06,
            'max_position_pct': 0.10,
            'min_confidence': 0.60
        },
        StrategyMode.POSITION: {
            'lookback': 60,
            'min_volatility': 0.003,
            'max_volatility': 0.015,
            'stop_loss_pct': 0.05,
            'take_profit_pct': 0.12,
            'max_position_pct': 0.15,
            'min_confidence': 0.70
        },
        StrategyMode.DEFENSIVE: {
            'lookback': 10,
            'min_volatility': 0.01,
            'max_volatility': 0.05,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.03,
            'max_position_pct': 0.03,
            'min_confidence': 0.80
        }
    }
    
    def __init__(
        self,
        volatility_floor: float = 0.006,
        max_leverage: float = 2.0,
        capital: float = 100000
    ):
        self.volatility_floor = volatility_floor
        self.max_leverage = max_leverage
        self.capital = capital
        
        self.current_mode = StrategyMode.SWING
        self.active_positions = {}
        self.trade_history = []
        
        logger.info(f"🧬 ARES-STOCK V6.2 inicializado")
        logger.info(f"   💰 Capital: ${capital:,.0f}")
        logger.info(f"   📊 Max Leverage: {max_leverage}x")
    
    def analyze(self, prices: List[Dict], regime: MarketRegime = None) -> Optional[float]:
        """
        Analizar precios y generar señal
        
        Args:
            prices: Lista de OHLCV data
            regime: Régimen de mercado actual
            
        Returns:
            Señal entre -1 y 1
        """
        try:
            signal = self.generate_signal(prices, regime)
            if signal:
                return signal.signal
            return None
        except Exception as e:
            logger.error(f"Error en ARES-STOCK: {e}")
            return None
    
    def generate_signal(
        self, 
        prices: List[Dict], 
        regime: MarketRegime = None
    ) -> Optional[ARESSignal]:
        """
        Generar señal completa con niveles de entrada/salida
        
        Args:
            prices: Lista de OHLCV data
            regime: Régimen de mercado actual
            
        Returns:
            ARESSignal con detalles completos
        """
        try:
            if len(prices) < 60:
                return None
            
            self._select_mode(regime)
            config = self.STOCK_CONFIG[self.current_mode]
            
            closes = np.array([p['close'] for p in prices])
            highs = np.array([p['high'] for p in prices])
            lows = np.array([p['low'] for p in prices])
            volumes = np.array([p['volume'] for p in prices])
            
            lookback = config['lookback']
            
            returns = np.diff(np.log(closes[-lookback:]))
            volatility = np.std(returns)
            
            if not (config['min_volatility'] <= volatility <= config['max_volatility']):
                return ARESSignal(
                    signal=0,
                    mode=self.current_mode,
                    entry_price=None,
                    stop_loss=None,
                    take_profit=None,
                    position_size=0,
                    confidence=0,
                    reasons=[f"Volatilidad fuera de rango: {volatility:.4f}"]
                )
            
            trend_signal = self._calculate_trend(closes, lookback)
            momentum_signal = self._calculate_momentum(closes, lookback)
            volume_signal = self._calculate_volume_profile(closes, volumes, lookback)
            support_resistance = self._find_support_resistance(highs, lows, closes)
            
            combined = (
                trend_signal * 0.35 +
                momentum_signal * 0.35 +
                volume_signal * 0.30
            )
            
            reasons = []
            
            if trend_signal > 0.3:
                reasons.append(f"Tendencia alcista ({trend_signal:.2f})")
            elif trend_signal < -0.3:
                reasons.append(f"Tendencia bajista ({trend_signal:.2f})")
            
            if momentum_signal > 0.3:
                reasons.append(f"Momentum positivo ({momentum_signal:.2f})")
            elif momentum_signal < -0.3:
                reasons.append(f"Momentum negativo ({momentum_signal:.2f})")
            
            if volume_signal > 0.3:
                reasons.append("Volumen confirma movimiento")
            
            confidence = min(abs(combined), 1.0)
            
            if self.current_mode == StrategyMode.DEFENSIVE:
                combined *= 0.5
            
            current_price = closes[-1]
            entry_price = current_price
            
            if combined > 0:
                stop_loss = current_price * (1 - config['stop_loss_pct'])
                take_profit = current_price * (1 + config['take_profit_pct'])
            else:
                stop_loss = current_price * (1 + config['stop_loss_pct'])
                take_profit = current_price * (1 - config['take_profit_pct'])
            
            if support_resistance['nearest_support']:
                if combined > 0:
                    stop_loss = max(stop_loss, support_resistance['nearest_support'] * 0.99)
            
            if support_resistance['nearest_resistance']:
                if combined > 0:
                    take_profit = min(take_profit, support_resistance['nearest_resistance'] * 0.99)
            
            position_size = self._calculate_position_size(
                volatility, 
                config['max_position_pct'],
                confidence
            )
            
            return ARESSignal(
                signal=np.clip(combined, -1, 1),
                mode=self.current_mode,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                confidence=confidence,
                reasons=reasons
            )
            
        except Exception as e:
            logger.error(f"Error generando señal ARES: {e}")
            return None
    
    def _select_mode(self, regime: MarketRegime):
        """Seleccionar modo de trading según régimen"""
        if regime in [MarketRegime.CRISIS, MarketRegime.BEAR]:
            self.current_mode = StrategyMode.DEFENSIVE
        elif regime == MarketRegime.BULL:
            self.current_mode = StrategyMode.POSITION
        else:
            self.current_mode = StrategyMode.SWING
    
    def _calculate_trend(self, closes: np.ndarray, lookback: int) -> float:
        """Calcular señal de tendencia"""
        if len(closes) < lookback:
            return 0
        
        ema_short = self._ema(closes, lookback // 3)
        ema_long = self._ema(closes, lookback)
        
        current_price = closes[-1]
        
        if ema_long != 0:
            trend = (ema_short - ema_long) / ema_long * 10
        else:
            trend = 0
        
        slope = (closes[-1] - closes[-lookback]) / closes[-lookback] if closes[-lookback] != 0 else 0
        slope_signal = np.tanh(slope * 20)
        
        return np.clip((trend + slope_signal) / 2, -1, 1)
    
    def _calculate_momentum(self, closes: np.ndarray, lookback: int) -> float:
        """Calcular señal de momentum (RSI-based)"""
        if len(closes) < lookback:
            return 0
        
        returns = np.diff(closes[-lookback:])
        gains = np.where(returns > 0, returns, 0)
        losses = np.where(returns < 0, -returns, 0)
        
        avg_gain = np.mean(gains) if len(gains) > 0 else 0
        avg_loss = np.mean(losses) if len(losses) > 0 else 0
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        momentum_signal = (rsi - 50) / 50
        
        roc = (closes[-1] - closes[-lookback]) / closes[-lookback] if closes[-lookback] != 0 else 0
        roc_signal = np.tanh(roc * 10)
        
        return np.clip((momentum_signal + roc_signal) / 2, -1, 1)
    
    def _calculate_volume_profile(
        self, 
        closes: np.ndarray, 
        volumes: np.ndarray, 
        lookback: int
    ) -> float:
        """Calcular señal basada en volumen"""
        if len(volumes) < lookback:
            return 0
        
        recent_vol = volumes[-lookback:]
        avg_vol = np.mean(recent_vol)
        
        if avg_vol == 0:
            return 0
        
        vol_ratio = volumes[-1] / avg_vol
        
        returns = np.diff(closes[-lookback:])
        
        if len(returns) > 0:
            vol_weighted_return = np.sum(returns * recent_vol[1:]) / np.sum(recent_vol[1:])
            direction = np.sign(vol_weighted_return)
        else:
            direction = 0
        
        signal = direction * min(vol_ratio - 1, 1)
        
        return np.clip(signal, -1, 1)
    
    def _find_support_resistance(
        self, 
        highs: np.ndarray, 
        lows: np.ndarray,
        closes: np.ndarray
    ) -> Dict:
        """Encontrar niveles de soporte y resistencia"""
        current_price = closes[-1]
        
        local_highs = []
        local_lows = []
        
        for i in range(5, len(highs) - 5):
            if highs[i] == max(highs[i-5:i+6]):
                local_highs.append(highs[i])
            if lows[i] == min(lows[i-5:i+6]):
                local_lows.append(lows[i])
        
        supports = [l for l in local_lows if l < current_price]
        resistances = [h for h in local_highs if h > current_price]
        
        return {
            'nearest_support': max(supports) if supports else None,
            'nearest_resistance': min(resistances) if resistances else None,
            'support_levels': sorted(supports, reverse=True)[:3],
            'resistance_levels': sorted(resistances)[:3]
        }
    
    def _calculate_position_size(
        self, 
        volatility: float, 
        max_position_pct: float,
        confidence: float
    ) -> float:
        """Calcular tamaño de posición ajustado por volatilidad"""
        base_size = self.capital * max_position_pct
        
        vol_multiplier = 0.01 / max(volatility, self.volatility_floor)
        vol_multiplier = min(vol_multiplier, 2.0)
        
        adjusted_size = base_size * vol_multiplier * confidence
        
        max_size = self.capital * max_position_pct * self.max_leverage
        
        return min(adjusted_size, max_size)
    
    def _ema(self, data: np.ndarray, period: int) -> float:
        """Calcular EMA"""
        if len(data) < period:
            return data[-1] if len(data) > 0 else 0
        
        multiplier = 2 / (period + 1)
        ema = data[0]
        
        for price in data[1:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def get_status(self) -> Dict:
        """Obtener estado actual de ARES"""
        return {
            'mode': self.current_mode.value,
            'capital': self.capital,
            'max_leverage': self.max_leverage,
            'active_positions': len(self.active_positions),
            'total_trades': len(self.trade_history),
            'config': self.STOCK_CONFIG[self.current_mode]
        }
