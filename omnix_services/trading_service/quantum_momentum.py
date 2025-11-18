"""
OMNIX Quantum Momentum Strategy
Estrategia propietaria que combina 6 componentes técnicos avanzados
"""

import logging
from typing import Dict, List, Optional
import numpy as np
from scipy import signal

logger = logging.getLogger(__name__)

class QuantumMomentumStrategy:
    """
    Estrategia propietaria OMNIX Quantum Momentum
    
    Componentes:
    1. Triple EMA Crossover (rápida, media, lenta)
    2. RSI Adaptivo (sobrecompra/sobreventa dinámicos)
    3. MACD con señal
    4. Volume Confirmation (volumen relativo)
    5. HP Filter (Hodrick-Prescott para tendencia subyacente)
    6. ATR (Average True Range para volatilidad)
    
    Señal BUY cuando:
    - EMA rápida > EMA media > EMA lenta (tendencia alcista)
    - RSI entre 30-70 (no extremos)
    - MACD > Señal (momentum positivo)
    - Volumen > promedio (confirmación)
    - Precio cerca de HP trend (no sobreextendido)
    - ATR moderado (no demasiado volátil)
    
    Señal SELL cuando condiciones opuestas
    """
    
    def __init__(
        self,
        ema_fast: int = 8,
        ema_mid: int = 21,
        ema_slow: int = 55,
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        volume_period: int = 20,
        atr_period: int = 14,
        hp_lambda: float = 1600.0
    ):
        """
        Args:
            ema_fast/mid/slow: Períodos para Triple EMA
            rsi_period: Período RSI
            macd_fast/slow/signal: Períodos MACD
            volume_period: Período para volumen promedio
            atr_period: Período ATR
            hp_lambda: Parámetro Hodrick-Prescott (1600 = mensual, 129600 = diario)
        """
        self.ema_fast = ema_fast
        self.ema_mid = ema_mid
        self.ema_slow = ema_slow
        self.rsi_period = rsi_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.volume_period = volume_period
        self.atr_period = atr_period
        self.hp_lambda = hp_lambda
        
        logger.info("⚛️ OMNIX Quantum Momentum Strategy initialized")
        logger.info(f"   Triple EMA: {ema_fast}/{ema_mid}/{ema_slow}")
        logger.info(f"   RSI: {rsi_period}, MACD: {macd_fast}/{macd_slow}/{macd_signal}")
    
    def analyze(
        self,
        prices: List[float],
        highs: List[float],
        lows: List[float],
        volumes: List[float]
    ) -> Dict:
        """
        Analiza mercado con estrategia Quantum Momentum
        
        Args:
            prices: Close prices
            highs: High prices
            lows: Low prices
            volumes: Volúmenes
        
        Returns:
            Dict con signal, score, components, recommendation
        """
        if len(prices) < max(self.ema_slow, self.rsi_period, self.macd_slow) + 10:
            logger.warning("⚠️ Datos insuficientes para Quantum Momentum")
            return self._insufficient_data_result()
        
        # Convertir a numpy
        prices_arr = np.array(prices)
        highs_arr = np.array(highs)
        lows_arr = np.array(lows)
        volumes_arr = np.array(volumes)
        
        # Calcular componentes
        components = {}
        
        # 1. Triple EMA
        ema_fast_val = self._calculate_ema(prices_arr, self.ema_fast)
        ema_mid_val = self._calculate_ema(prices_arr, self.ema_mid)
        ema_slow_val = self._calculate_ema(prices_arr, self.ema_slow)
        
        components['ema_fast'] = ema_fast_val[-1]
        components['ema_mid'] = ema_mid_val[-1]
        components['ema_slow'] = ema_slow_val[-1]
        components['ema_alignment'] = self._check_ema_alignment(
            ema_fast_val[-1], ema_mid_val[-1], ema_slow_val[-1]
        )
        
        # 2. RSI
        rsi = self._calculate_rsi(prices_arr, self.rsi_period)
        components['rsi'] = rsi[-1]
        components['rsi_signal'] = self._interpret_rsi(rsi[-1])
        
        # 3. MACD
        macd_line, signal_line, histogram = self._calculate_macd(
            prices_arr, self.macd_fast, self.macd_slow, self.macd_signal
        )
        components['macd'] = macd_line[-1]
        components['macd_signal'] = signal_line[-1]
        components['macd_histogram'] = histogram[-1]
        components['macd_crossover'] = "BULLISH" if macd_line[-1] > signal_line[-1] else "BEARISH"
        
        # 4. Volume Confirmation
        avg_volume = np.mean(volumes_arr[-self.volume_period:])
        current_volume = volumes_arr[-1]
        components['volume_ratio'] = current_volume / avg_volume if avg_volume > 0 else 1.0
        components['volume_confirmed'] = current_volume > avg_volume * 1.2
        
        # 5. HP Filter (Hodrick-Prescott)
        hp_trend = self._calculate_hp_filter(prices_arr)
        components['hp_trend'] = hp_trend[-1]
        components['price_vs_trend'] = (prices_arr[-1] - hp_trend[-1]) / hp_trend[-1] * 100
        components['trend_aligned'] = abs(components['price_vs_trend']) < 2.0  # Dentro de 2%
        
        # 6. ATR (Average True Range)
        atr = self._calculate_atr(highs_arr, lows_arr, prices_arr, self.atr_period)
        components['atr'] = atr[-1]
        components['atr_pct'] = atr[-1] / prices_arr[-1] * 100
        components['volatility_acceptable'] = components['atr_pct'] < 5.0  # ATR < 5%
        
        # Calcular señal final
        signal, score = self._calculate_signal(components)
        
        # Generar recomendación
        recommendation = self._generate_recommendation(signal, score, components)
        
        result = {
            'signal': signal,
            'score': score,
            'confidence': self._calculate_confidence(components),
            'components': components,
            'recommendation': recommendation,
            'entry_price': prices_arr[-1],
            'stop_loss': self._calculate_stop_loss(prices_arr[-1], signal, atr[-1]),
            'take_profit': self._calculate_take_profit(prices_arr[-1], signal, atr[-1])
        }
        
        logger.info(
            f"⚛️ Quantum Momentum: {signal} (score: {score:.1f}/10, confidence: {result['confidence']})"
        )
        
        return result
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """
        Calcula Exponential Moving Average
        """
        ema = np.zeros_like(prices)
        ema[0] = prices[0]
        multiplier = 2 / (period + 1)
        
        for i in range(1, len(prices)):
            ema[i] = (prices[i] - ema[i-1]) * multiplier + ema[i-1]
        
        return ema
    
    def _calculate_rsi(self, prices: np.ndarray, period: int) -> np.ndarray:
        """
        Calcula Relative Strength Index
        """
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.zeros(len(prices))
        avg_loss = np.zeros(len(prices))
        
        # Primer valor
        avg_gain[period] = np.mean(gains[:period])
        avg_loss[period] = np.mean(losses[:period])
        
        # Smoothed averages
        for i in range(period + 1, len(prices)):
            avg_gain[i] = (avg_gain[i-1] * (period - 1) + gains[i-1]) / period
            avg_loss[i] = (avg_loss[i-1] * (period - 1) + losses[i-1]) / period
        
        rs = np.divide(avg_gain, avg_loss, where=avg_loss!=0, out=np.ones_like(avg_gain))
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(
        self,
        prices: np.ndarray,
        fast: int,
        slow: int,
        signal_period: int
    ) -> tuple:
        """
        Calcula MACD, Signal, Histogram
        """
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = self._calculate_ema(macd_line, signal_period)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def _calculate_hp_filter(self, prices: np.ndarray) -> np.ndarray:
        """
        Hodrick-Prescott Filter para extraer tendencia subyacente
        """
        n = len(prices)
        
        # Matriz identidad
        I = np.eye(n)
        
        # Matriz de segundas diferencias
        D2 = np.zeros((n-2, n))
        for i in range(n-2):
            D2[i, i] = 1
            D2[i, i+1] = -2
            D2[i, i+2] = 1
        
        # HP filter: (I + lambda * D2' * D2)^-1 * prices
        try:
            trend = np.linalg.solve(I + self.hp_lambda * D2.T @ D2, prices)
        except np.linalg.LinAlgError:
            # Si falla, usar EMA como fallback
            trend = self._calculate_ema(prices, 50)
        
        return trend
    
    def _calculate_atr(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        period: int
    ) -> np.ndarray:
        """
        Calcula Average True Range
        """
        high_low = highs - lows
        high_close = np.abs(highs[1:] - closes[:-1])
        low_close = np.abs(lows[1:] - closes[:-1])
        
        tr = np.maximum(high_low[1:], np.maximum(high_close, low_close))
        
        # ATR = EMA of TR
        atr = np.zeros(len(closes))
        atr[:period] = np.mean(tr[:period])
        
        multiplier = 1 / period
        for i in range(period, len(tr)):
            atr[i] = (tr[i] - atr[i-1]) * multiplier + atr[i-1]
        
        return atr
    
    def _check_ema_alignment(self, fast: float, mid: float, slow: float) -> str:
        """
        Verifica alineación de EMAs
        """
        if fast > mid > slow:
            return "BULLISH"
        elif fast < mid < slow:
            return "BEARISH"
        else:
            return "MIXED"
    
    def _interpret_rsi(self, rsi: float) -> str:
        """
        Interpreta valor RSI
        """
        if rsi >= 70:
            return "OVERBOUGHT"
        elif rsi <= 30:
            return "OVERSOLD"
        elif 40 <= rsi <= 60:
            return "NEUTRAL"
        else:
            return "NORMAL"
    
    def _calculate_signal(self, components: Dict) -> tuple:
        """
        Calcula señal final basada en todos los componentes
        Retorna (signal, score)
        """
        score = 0
        max_score = 10
        
        # 1. Triple EMA (2 puntos)
        if components['ema_alignment'] == "BULLISH":
            score += 2
        elif components['ema_alignment'] == "BEARISH":
            score -= 2
        
        # 2. RSI (1.5 puntos)
        if components['rsi_signal'] in ["NORMAL", "NEUTRAL"]:
            score += 1.5
        elif components['rsi_signal'] == "OVERSOLD":
            score += 1.0  # Posible rebote
        elif components['rsi_signal'] == "OVERBOUGHT":
            score -= 1.0  # Posible caída
        
        # 3. MACD (2 puntos)
        if components['macd_crossover'] == "BULLISH" and components['macd_histogram'] > 0:
            score += 2
        elif components['macd_crossover'] == "BEARISH" and components['macd_histogram'] < 0:
            score -= 2
        
        # 4. Volume (1.5 puntos)
        if components['volume_confirmed']:
            score += 1.5
        
        # 5. HP Trend (2 puntos)
        if components['trend_aligned']:
            score += 2
        elif abs(components['price_vs_trend']) > 5:
            score -= 1  # Muy alejado de tendencia
        
        # 6. ATR Volatilidad (1 punto)
        if components['volatility_acceptable']:
            score += 1
        else:
            score -= 0.5  # Volatilidad alta
        
        # Normalizar score a -10 a +10
        score = np.clip(score, -max_score, max_score)
        
        # Determinar señal
        if score >= 6:
            signal = "STRONG_BUY"
        elif score >= 3:
            signal = "BUY"
        elif score <= -6:
            signal = "STRONG_SELL"
        elif score <= -3:
            signal = "SELL"
        else:
            signal = "HOLD"
        
        return signal, score
    
    def _calculate_confidence(self, components: Dict) -> str:
        """
        Calcula confianza en la señal
        """
        confirmations = 0
        
        if components['ema_alignment'] in ["BULLISH", "BEARISH"]:
            confirmations += 1
        if components['rsi_signal'] not in ["OVERBOUGHT", "OVERSOLD"]:
            confirmations += 1
        if abs(components['macd_histogram']) > 0:
            confirmations += 1
        if components['volume_confirmed']:
            confirmations += 1
        if components['trend_aligned']:
            confirmations += 1
        if components['volatility_acceptable']:
            confirmations += 1
        
        if confirmations >= 5:
            return "HIGH"
        elif confirmations >= 3:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_recommendation(self, signal: str, score: float, components: Dict) -> str:
        """
        Genera recomendación textual
        """
        recommendations = {
            'STRONG_BUY': f"Strong buy signal detected (score: {score:.1f}/10). All indicators aligned bullish.",
            'BUY': f"Buy signal detected (score: {score:.1f}/10). Most indicators favor uptrend.",
            'HOLD': f"Hold position (score: {score:.1f}/10). Mixed signals, wait for confirmation.",
            'SELL': f"Sell signal detected (score: {score:.1f}/10). Most indicators favor downtrend.",
            'STRONG_SELL': f"Strong sell signal detected (score: {score:.1f}/10). All indicators aligned bearish."
        }
        return recommendations.get(signal, "No clear signal")
    
    def _calculate_stop_loss(self, entry_price: float, signal: str, atr: float) -> float:
        """
        Calcula stop loss basado en ATR
        """
        atr_multiplier = 2.0  # 2x ATR
        
        if "BUY" in signal:
            return entry_price - (atr * atr_multiplier)
        elif "SELL" in signal:
            return entry_price + (atr * atr_multiplier)
        else:
            return entry_price - (atr * atr_multiplier)
    
    def _calculate_take_profit(self, entry_price: float, signal: str, atr: float) -> float:
        """
        Calcula take profit basado en ATR (risk:reward 1:2)
        """
        atr_multiplier = 4.0  # 4x ATR para 1:2 ratio
        
        if "BUY" in signal:
            return entry_price + (atr * atr_multiplier)
        elif "SELL" in signal:
            return entry_price - (atr * atr_multiplier)
        else:
            return entry_price + (atr * atr_multiplier)
    
    def _insufficient_data_result(self) -> Dict:
        """
        Resultado cuando no hay datos suficientes
        """
        return {
            'signal': 'HOLD',
            'score': 0.0,
            'confidence': 'LOW',
            'components': {},
            'recommendation': 'Insufficient data for Quantum Momentum analysis',
            'entry_price': 0,
            'stop_loss': 0,
            'take_profit': 0
        }


# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Simular datos de mercado
    np.random.seed(42)
    n = 200
    trend = np.linspace(100, 120, n)
    noise = np.random.randn(n) * 2
    prices = trend + noise
    highs = prices + np.random.rand(n) * 1.5
    lows = prices - np.random.rand(n) * 1.5
    volumes = np.random.randint(1000, 5000, n)
    
    strategy = QuantumMomentumStrategy()
    result = strategy.analyze(prices.tolist(), highs.tolist(), lows.tolist(), volumes.tolist())
    
    print(f"\n⚛️ OMNIX QUANTUM MOMENTUM ANALYSIS:")
    print(f"Signal: {result['signal']}")
    print(f"Score: {result['score']:.1f}/10")
    print(f"Confidence: {result['confidence']}")
    print(f"Recommendation: {result['recommendation']}")
    print(f"\n📊 Entry: ${result['entry_price']:.2f}")
    print(f"Stop Loss: ${result['stop_loss']:.2f}")
    print(f"Take Profit: ${result['take_profit']:.2f}")
