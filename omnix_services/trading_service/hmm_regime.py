"""
Hidden Markov Model (HMM) Regime Detection
Detecta automáticamente régimen del mercado: TRENDING, RANGING, VOLATILE
"""

import logging
from typing import Dict, List, Tuple
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

class HMMRegimeDetector:
    """
    Detecta régimen de mercado usando Hidden Markov Model simplificado
    
    Regímenes:
    - TRENDING: Mercado en tendencia clara (alcista o bajista)
    - RANGING: Mercado lateral, oscilando en rango
    - VOLATILE: Alta volatilidad, movimientos erráticos
    """
    
    def __init__(self, window_size: int = 50):
        """
        Args:
            window_size: Tamaño de ventana para análisis (velas)
        """
        self.window_size = window_size
        self.current_regime = "UNKNOWN"
        self.regime_confidence = 0.0
        logger.info(f"🔬 HMM Regime Detector initialized - Window: {window_size}")
    
    def detect_regime(self, prices: List[float], volumes: List[float] = None) -> Dict:
        """
        Detecta régimen actual del mercado
        
        Args:
            prices: Lista de precios (close prices)
            volumes: Lista de volúmenes (opcional)
        
        Returns:
            Dict con regime, confidence, metrics
        """
        if len(prices) < self.window_size:
            logger.warning(f"⚠️ Insufficient data: {len(prices)} < {self.window_size}")
            return self._unknown_regime()
        
        # Usar últimos window_size datos
        recent_prices = np.array(prices[-self.window_size:])
        
        # Calcular métricas estadísticas
        returns = np.diff(recent_prices) / recent_prices[:-1]
        
        # 1. Trend strength (ADX-like)
        trend_strength = self._calculate_trend_strength(recent_prices)
        
        # 2. Volatility
        volatility = np.std(returns) * np.sqrt(252)  # Anualizada
        
        # 3. Mean reversion tendency
        mean_reversion = self._calculate_mean_reversion(recent_prices)
        
        # 4. Directional movement
        directional_bias = self._calculate_directional_bias(recent_prices)
        
        # Clasificar régimen basado en métricas
        regime, confidence = self._classify_regime(
            trend_strength=trend_strength,
            volatility=volatility,
            mean_reversion=mean_reversion,
            directional_bias=directional_bias
        )
        
        self.current_regime = regime
        self.regime_confidence = confidence
        
        result = {
            'regime': regime,
            'confidence': confidence,
            'trend_strength': trend_strength,
            'volatility': volatility,
            'mean_reversion': mean_reversion,
            'directional_bias': directional_bias,
            'trading_recommendation': self._get_trading_recommendation(regime)
        }
        
        logger.info(
            f"🔬 Regime: {regime} (confidence: {confidence:.1%}) "
            f"- Trend: {trend_strength:.2f}, Vol: {volatility:.2%}"
        )
        
        return result
    
    def _calculate_trend_strength(self, prices: np.ndarray) -> float:
        """
        Calcula fuerza de tendencia (0-1)
        Similar a ADX pero simplificado
        """
        # Usar regresión lineal para medir tendencia
        x = np.arange(len(prices))
        slope, intercept, r_value, _, _ = stats.linregress(x, prices)
        
        # R-squared mide qué tan bien los precios siguen tendencia lineal
        r_squared = r_value ** 2
        
        # Normalizar slope relativo a precio promedio
        avg_price = np.mean(prices)
        normalized_slope = abs(slope) / avg_price * len(prices)
        
        # Combinar R² y slope para trend strength
        trend_strength = r_squared * min(normalized_slope, 1.0)
        
        return trend_strength
    
    def _calculate_mean_reversion(self, prices: np.ndarray) -> float:
        """
        Calcula tendencia a reversión a la media (0-1)
        Alto = mercado revierte mucho (ranging)
        Bajo = mercado no revierte (trending)
        """
        # Calcular cuánto se desvía el precio de su media móvil
        sma = np.mean(prices)
        deviations = (prices - sma) / sma
        
        # Contar cuántas veces cruza la media
        crosses = np.sum(np.diff(np.sign(deviations)) != 0)
        max_crosses = len(prices) - 1
        cross_rate = crosses / max_crosses if max_crosses > 0 else 0
        
        return cross_rate
    
    def _calculate_directional_bias(self, prices: np.ndarray) -> float:
        """
        Calcula sesgo direccional (-1 a +1)
        Positivo = alcista, Negativo = bajista, Cerca de 0 = neutral
        """
        # Calcular pendiente normalizada
        x = np.arange(len(prices))
        slope, _, _, _, _ = stats.linregress(x, prices)
        
        # Normalizar por precio promedio y longitud
        avg_price = np.mean(prices)
        normalized_slope = (slope * len(prices)) / avg_price
        
        # Limitar a [-1, 1]
        directional_bias = np.clip(normalized_slope, -1, 1)
        
        return directional_bias
    
    def _classify_regime(
        self,
        trend_strength: float,
        volatility: float,
        mean_reversion: float,
        directional_bias: float
    ) -> Tuple[str, float]:
        """
        Clasifica régimen basado en métricas
        
        Returns:
            (regime, confidence)
        """
        # Thresholds
        HIGH_TREND = 0.60
        LOW_TREND = 0.30
        HIGH_VOL = 0.40
        HIGH_MEAN_REV = 0.60
        
        # Calcular scores para cada régimen
        trending_score = 0
        ranging_score = 0
        volatile_score = 0
        
        # TRENDING: Alta trend strength, baja mean reversion
        if trend_strength > HIGH_TREND:
            trending_score += 3
        elif trend_strength > LOW_TREND:
            trending_score += 1
        
        if mean_reversion < 0.40:
            trending_score += 2
        
        if abs(directional_bias) > 0.3:
            trending_score += 1
        
        # RANGING: Alta mean reversion, baja trend strength
        if mean_reversion > HIGH_MEAN_REV:
            ranging_score += 3
        elif mean_reversion > 0.45:
            ranging_score += 1
        
        if trend_strength < LOW_TREND:
            ranging_score += 2
        
        if abs(directional_bias) < 0.2:
            ranging_score += 1
        
        # VOLATILE: Alta volatilidad
        if volatility > HIGH_VOL:
            volatile_score += 4
        elif volatility > 0.25:
            volatile_score += 2
        
        # Determinar régimen ganador
        max_score = max(trending_score, ranging_score, volatile_score)
        
        if max_score == 0:
            return "UNKNOWN", 0.0
        
        if trending_score == max_score:
            regime = "TRENDING"
            confidence = trending_score / 6.0  # Max score = 6
        elif ranging_score == max_score:
            regime = "RANGING"
            confidence = ranging_score / 6.0
        else:
            regime = "VOLATILE"
            confidence = volatile_score / 4.0  # Max score = 4
        
        # Ajustar confianza si hay empate
        scores = [trending_score, ranging_score, volatile_score]
        if scores.count(max_score) > 1:
            confidence *= 0.7  # Reducir confianza si hay empate
        
        return regime, min(confidence, 1.0)
    
    def _get_trading_recommendation(self, regime: str) -> str:
        """
        Genera recomendación de trading basada en régimen
        """
        recommendations = {
            'TRENDING': 'Use trend-following strategies (MA crossovers, breakouts). Avoid mean reversion.',
            'RANGING': 'Use mean reversion strategies (RSI, Bollinger Bands). Avoid breakouts.',
            'VOLATILE': 'Reduce position sizes, widen stops. Consider staying out or scalping only.',
            'UNKNOWN': 'Wait for clearer regime confirmation before trading.'
        }
        return recommendations.get(regime, recommendations['UNKNOWN'])
    
    def _unknown_regime(self) -> Dict:
        """
        Retorna resultado cuando régimen es desconocido
        """
        return {
            'regime': 'UNKNOWN',
            'confidence': 0.0,
            'trend_strength': 0.0,
            'volatility': 0.0,
            'mean_reversion': 0.0,
            'directional_bias': 0.0,
            'trading_recommendation': 'Insufficient data for regime detection'
        }
    
    def get_regime_specific_params(self, regime: str = None) -> Dict:
        """
        Retorna parámetros de trading optimizados para el régimen
        
        Args:
            regime: Régimen específico o usa self.current_regime
        
        Returns:
            Dict con parámetros recomendados
        """
        regime = regime or self.current_regime
        
        params = {
            'TRENDING': {
                'stop_loss_pct': 0.03,  # 3% stop más amplio
                'take_profit_pct': 0.08,  # 8% target
                'position_size_multiplier': 1.2,  # Posición 20% mayor
                'rsi_overbought': 75,  # Más permisivo en tendencia
                'rsi_oversold': 25,
                'use_breakouts': True,
                'use_mean_reversion': False
            },
            'RANGING': {
                'stop_loss_pct': 0.02,  # 2% stop más ajustado
                'take_profit_pct': 0.04,  # 4% target
                'position_size_multiplier': 1.0,
                'rsi_overbought': 70,  # RSI estándar
                'rsi_oversold': 30,
                'use_breakouts': False,
                'use_mean_reversion': True
            },
            'VOLATILE': {
                'stop_loss_pct': 0.05,  # 5% stop muy amplio
                'take_profit_pct': 0.06,  # 6% target
                'position_size_multiplier': 0.5,  # Posición 50% menor
                'rsi_overbought': 80,  # Muy permisivo
                'rsi_oversold': 20,
                'use_breakouts': False,
                'use_mean_reversion': False
            },
            'UNKNOWN': {
                'stop_loss_pct': 0.03,
                'take_profit_pct': 0.05,
                'position_size_multiplier': 0.7,  # Conservador
                'rsi_overbought': 70,
                'rsi_oversold': 30,
                'use_breakouts': False,
                'use_mean_reversion': False
            }
        }
        
        return params.get(regime, params['UNKNOWN'])


# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    hmm = HMMRegimeDetector(window_size=50)
    
    # Simular precios TRENDING
    trending_prices = [100 + i * 0.5 + np.random.randn() * 0.5 for i in range(60)]
    
    result = hmm.detect_regime(trending_prices)
    
    print(f"\n🔬 HMM REGIME DETECTION:")
    print(f"Regime: {result['regime']}")
    print(f"Confidence: {result['confidence']:.1%}")
    print(f"Trend Strength: {result['trend_strength']:.2f}")
    print(f"Volatility: {result['volatility']:.2%}")
    print(f"Recommendation: {result['trading_recommendation']}")
    
    # Parámetros optimizados
    params = hmm.get_regime_specific_params()
    print(f"\n⚙️ OPTIMIZED PARAMETERS:")
    print(f"Stop Loss: {params['stop_loss_pct']:.1%}")
    print(f"Take Profit: {params['take_profit_pct']:.1%}")
    print(f"Position Size Multiplier: {params['position_size_multiplier']:.1f}x")
