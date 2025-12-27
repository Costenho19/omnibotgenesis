"""
Kalman Filter for Signal Smoothing
Suaviza señales de trading reduciendo ruido mejor que promedios móviles
"""

import logging
from typing import List, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class KalmanFilter:
    """
    Implementa Filtro de Kalman 1D para suavizado de series temporales
    
    Ventajas sobre SMA/EMA:
    - Adapta dinámicamente a cambios en volatilidad
    - Menor lag que promedios móviles
    - Filtra ruido manteniendo señal real
    """
    
    def __init__(
        self,
        process_variance: float = 1e-5,
        measurement_variance: float = 1e-2,
        initial_value: float = 0.0,
        initial_estimate_error: float = 1.0
    ):
        """
        Args:
            process_variance: Q - Varianza del proceso (ruido del sistema)
            measurement_variance: R - Varianza de medición (ruido del sensor)
            initial_value: Valor inicial estimado
            initial_estimate_error: Error de estimación inicial
        """
        self.q = process_variance  # Process noise
        self.r = measurement_variance  # Measurement noise
        self.x = initial_value  # State estimate
        self.p = initial_estimate_error  # Estimate error
        
        self.k = 0  # Kalman gain
        
        logger.info(
            f"📡 Kalman Filter initialized - Q: {process_variance}, R: {measurement_variance}"
        )
    
    def update(self, measurement: float) -> float:
        """
        Actualiza filtro con nueva medición
        
        Args:
            measurement: Nueva observación (precio)
        
        Returns:
            Estimación filtrada
        """
        # Prediction
        self.p = self.p + self.q
        
        # Update
        self.k = self.p / (self.p + self.r)  # Kalman gain
        self.x = self.x + self.k * (measurement - self.x)  # State update
        self.p = (1 - self.k) * self.p  # Error covariance update
        
        return self.x
    
    def filter_series(self, measurements: List[float]) -> List[float]:
        """
        Filtra serie completa de mediciones
        
        Args:
            measurements: Lista de precios
        
        Returns:
            Lista de valores filtrados
        """
        if not measurements:
            return []
        
        # Reset filter
        self.x = measurements[0]
        self.p = 1.0
        
        filtered = []
        for measurement in measurements:
            filtered_value = self.update(measurement)
            filtered.append(filtered_value)
        
        return filtered
    
    def get_kalman_gain(self) -> float:
        """
        Retorna Kalman gain actual
        Valores altos = filtro confía más en mediciones
        Valores bajos = filtro confía más en predicción
        """
        return self.k


class AdaptiveKalmanFilter(KalmanFilter):
    """
    Filtro de Kalman Adaptivo que ajusta automáticamente varianzas
    basado en volatilidad del mercado
    """
    
    def __init__(
        self,
        initial_value: float = 0.0,
        adaptation_rate: float = 0.1
    ):
        """
        Args:
            initial_value: Valor inicial
            adaptation_rate: Qué tan rápido adapta a cambios (0-1)
        """
        super().__init__(
            process_variance=1e-5,
            measurement_variance=1e-2,
            initial_value=initial_value
        )
        self.adaptation_rate = adaptation_rate
        self.recent_innovations = []  # Errores de predicción recientes
        self.window_size = 20
        
        logger.info(f"📡 Adaptive Kalman Filter initialized - Adaptation: {adaptation_rate}")
    
    def update(self, measurement: float) -> float:
        """
        Actualiza filtro adaptando varianzas basado en errores recientes
        """
        # Calcular innovation (error de predicción)
        innovation = measurement - self.x
        self.recent_innovations.append(abs(innovation))
        
        # Mantener ventana limitada
        if len(self.recent_innovations) > self.window_size:
            self.recent_innovations.pop(0)
        
        # Adaptar varianzas basado en innovación reciente
        if len(self.recent_innovations) >= 5:
            avg_innovation = np.mean(self.recent_innovations)
            
            # Si errores son grandes, aumentar measurement variance (confiar menos en mediciones)
            # Si errores son pequeños, reducir measurement variance (confiar más en mediciones)
            target_r = avg_innovation ** 2
            self.r = self.r + self.adaptation_rate * (target_r - self.r)
            
            # Ajustar process variance proporcionalmente
            self.q = self.r * 0.01  # Mantener ratio Q/R
        
        # Llamar update normal
        return super().update(measurement)


class DualKalmanTrendFilter:
    """
    Sistema dual de Kalman filters para detectar tendencia
    - Filtro rápido: Sigue precio de cerca
    - Filtro lento: Suaviza más
    - Cruce indica cambio de tendencia
    """
    
    def __init__(self):
        """
        Inicializa filtros rápido y lento
        """
        self.fast_filter = AdaptiveKalmanFilter(adaptation_rate=0.3)
        self.slow_filter = AdaptiveKalmanFilter(adaptation_rate=0.05)
        
        self.fast_values = []
        self.slow_values = []
        
        logger.info("📡 Dual Kalman Trend Filter initialized")
    
    def update(self, price: float) -> dict:
        """
        Actualiza ambos filtros
        
        Args:
            price: Precio actual
        
        Returns:
            Dict con fast, slow, trend signal
        """
        fast = self.fast_filter.update(price)
        slow = self.slow_filter.update(price)
        
        self.fast_values.append(fast)
        self.slow_values.append(slow)
        
        # Mantener últimos 100 valores
        if len(self.fast_values) > 100:
            self.fast_values.pop(0)
            self.slow_values.pop(0)
        
        # Detectar tendencia
        trend_signal = self._detect_trend(fast, slow)
        
        # Detectar cruces
        crossover = self._detect_crossover()
        
        return {
            'fast': fast,
            'slow': slow,
            'trend': trend_signal,
            'crossover': crossover,
            'distance': abs(fast - slow),
            'distance_pct': abs(fast - slow) / slow * 100 if slow != 0 else 0
        }
    
    def _detect_trend(self, fast: float, slow: float) -> str:
        """
        Detecta tendencia actual
        """
        diff_pct = (fast - slow) / slow * 100 if slow != 0 else 0
        
        if diff_pct > 0.5:
            return "BULLISH"
        elif diff_pct < -0.5:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def _detect_crossover(self) -> str:
        """
        Detecta cruces entre filtros
        """
        if len(self.fast_values) < 2 or len(self.slow_values) < 2:
            return "NONE"
        
        # Valores actuales vs previos
        fast_curr, fast_prev = self.fast_values[-1], self.fast_values[-2]
        slow_curr, slow_prev = self.slow_values[-1], self.slow_values[-2]
        
        # Golden cross (fast cruza slow hacia arriba)
        if fast_prev <= slow_prev and fast_curr > slow_curr:
            return "GOLDEN_CROSS"
        
        # Death cross (fast cruza slow hacia abajo)
        if fast_prev >= slow_prev and fast_curr < slow_curr:
            return "DEATH_CROSS"
        
        return "NONE"
    
    def filter_series(self, prices: List[float]) -> dict:
        """
        Filtra serie completa de precios
        
        Returns:
            Dict con fast_series, slow_series, trends, crossovers
        """
        # Reset
        self.fast_filter = AdaptiveKalmanFilter(adaptation_rate=0.3)
        self.slow_filter = AdaptiveKalmanFilter(adaptation_rate=0.05)
        self.fast_values = []
        self.slow_values = []
        
        results = []
        for price in prices:
            result = self.update(price)
            results.append(result)
        
        return {
            'fast_series': [r['fast'] for r in results],
            'slow_series': [r['slow'] for r in results],
            'trends': [r['trend'] for r in results],
            'crossovers': [r['crossover'] for r in results]
        }
    
    def filter_and_predict(self, prices: List[float]) -> dict:
        """
        Filtra serie de precios y genera predicción de tendencia.
        
        Este método es el punto de entrada canónico llamado por auto_trading_bot.py
        para obtener señales de Kalman Filter en el análisis de trading.
        
        Args:
            prices: Lista de precios históricos (últimas N velas)
        
        Returns:
            Dict con:
                - filtered_price: Precio filtrado actual
                - predicted_price: Predicción del próximo precio
                - trend: Dirección de tendencia (BULLISH/BEARISH/NEUTRAL)
                - trend_strength: Fuerza de la tendencia (0-1)
                - crossover: Señal de cruce (GOLDEN_CROSS/DEATH_CROSS/NONE)
                - confidence: Nivel de confianza (0-1)
                - fast: Valor del filtro rápido
                - slow: Valor del filtro lento
        """
        if not prices or len(prices) < 2:
            return {
                'filtered_price': 0,
                'predicted_price': 0,
                'trend': 'NEUTRAL',
                'trend_strength': 0,
                'crossover': 'NONE',
                'confidence': 0,
                'fast': 0,
                'slow': 0
            }
        
        # Procesar serie completa
        series_result = self.filter_series(prices)
        
        # Obtener valores finales
        fast_final = series_result['fast_series'][-1] if series_result['fast_series'] else prices[-1]
        slow_final = series_result['slow_series'][-1] if series_result['slow_series'] else prices[-1]
        trend_final = series_result['trends'][-1] if series_result['trends'] else 'NEUTRAL'
        crossover_final = series_result['crossovers'][-1] if series_result['crossovers'] else 'NONE'
        
        # Calcular predicción simple (extrapolación lineal del filtro rápido)
        if len(series_result['fast_series']) >= 2:
            fast_prev = series_result['fast_series'][-2]
            momentum = fast_final - fast_prev
            predicted_price = fast_final + momentum
        else:
            predicted_price = fast_final
        
        # Calcular fuerza de tendencia (distancia normalizada entre fast y slow)
        if slow_final != 0:
            distance_pct = abs(fast_final - slow_final) / slow_final
            trend_strength = min(distance_pct * 10, 1.0)  # Normalizar a 0-1
        else:
            trend_strength = 0
        
        # Calcular confianza basada en consistencia de tendencia
        if len(series_result['trends']) >= 5:
            recent_trends = series_result['trends'][-5:]
            trend_consistency = recent_trends.count(trend_final) / 5
            confidence = trend_consistency * trend_strength
        else:
            confidence = trend_strength * 0.5
        
        return {
            'filtered_price': fast_final,
            'predicted_price': predicted_price,
            'trend': trend_final,
            'trend_strength': round(trend_strength, 3),
            'crossover': crossover_final,
            'confidence': round(min(confidence, 1.0), 3),
            'fast': fast_final,
            'slow': slow_final
        }


# Ejemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Simular precios con ruido
    np.random.seed(42)
    true_trend = np.linspace(100, 110, 100)
    noise = np.random.randn(100) * 2
    noisy_prices = true_trend + noise
    
    # Filtro simple
    kf = KalmanFilter(process_variance=1e-4, measurement_variance=1e-1)
    filtered = kf.filter_series(noisy_prices.tolist())
    
    print(f"\n📡 KALMAN FILTER RESULTS:")
    print(f"Original prices (last 5): {noisy_prices[-5:].tolist()}")
    print(f"Filtered prices (last 5): {filtered[-5:]}")
    print(f"Kalman Gain: {kf.get_kalman_gain():.4f}")
    
    # Dual Kalman para tendencia
    dual = DualKalmanTrendFilter()
    trend_result = dual.update(noisy_prices[-1])
    
    print(f"\n📊 DUAL KALMAN TREND:")
    print(f"Fast: {trend_result['fast']:.2f}")
    print(f"Slow: {trend_result['slow']:.2f}")
    print(f"Trend: {trend_result['trend']}")
    print(f"Crossover: {trend_result['crossover']}")
