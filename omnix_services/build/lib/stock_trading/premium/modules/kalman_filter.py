"""
📈 STOCK KALMAN FILTER V6.2
Filtro de Kalman dual adaptado para acciones
Estimación de tendencia y volatilidad
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class KalmanState:
    price_estimate: float
    velocity_estimate: float
    price_variance: float
    velocity_variance: float
    innovation: float
    signal: float


class StockKalmanFilter:
    """
    Filtro de Kalman Dual para acciones
    Estima precio subyacente y tendencia (velocidad)
    
    Estado: [precio, velocidad]
    Observación: precio de cierre
    
    Características:
    - Process noise calibrado para volatilidad diaria de acciones
    - Adaptación automática de parámetros
    - Detección de cambios de tendencia
    """
    
    def __init__(
        self,
        process_noise: float = 0.001,
        measurement_noise: float = 0.01,
        velocity_decay: float = 0.95
    ):
        self.Q_base = process_noise
        self.R = measurement_noise
        self.velocity_decay = velocity_decay
        
        self.state = np.zeros(2)
        self.P = np.eye(2) * 1.0
        
        self.F = np.array([
            [1, 1],
            [0, velocity_decay]
        ])
        
        self.H = np.array([[1, 0]])
        
        self.Q = np.array([
            [process_noise, 0],
            [0, process_noise * 0.1]
        ])
        
        self.initialized = False
        self.history = []
        
        logger.info(f"📈 Stock Kalman Filter inicializado: Q={process_noise}, R={measurement_noise}")
    
    def analyze(self, prices: List[Dict]) -> Optional[float]:
        """
        Analizar precios y retornar señal
        
        Args:
            prices: Lista de OHLCV data
            
        Returns:
            Señal entre -1 (bearish) y 1 (bullish)
        """
        try:
            state = self.filter(prices)
            if state:
                return state.signal
            return None
        except Exception as e:
            logger.error(f"Error en Kalman Filter: {e}")
            return None
    
    def filter(self, prices: List[Dict]) -> Optional[KalmanState]:
        """
        Aplicar filtro de Kalman a serie de precios
        
        Args:
            prices: Lista de OHLCV data
            
        Returns:
            KalmanState con estimaciones actuales
        """
        try:
            closes = [p['close'] for p in prices]
            
            if len(closes) < 5:
                return None
            
            for i, price in enumerate(closes):
                if not self.initialized:
                    self._initialize(price)
                else:
                    self._update(price)
            
            price_estimate = self.state[0]
            velocity_estimate = self.state[1]
            
            current_price = closes[-1]
            innovation = current_price - price_estimate
            
            signal = self._calculate_signal(
                velocity_estimate,
                innovation,
                self.P[0, 0]
            )
            
            return KalmanState(
                price_estimate=price_estimate,
                velocity_estimate=velocity_estimate,
                price_variance=self.P[0, 0],
                velocity_variance=self.P[1, 1],
                innovation=innovation,
                signal=signal
            )
            
        except Exception as e:
            logger.error(f"Error en filtrado Kalman: {e}")
            return None
    
    def _initialize(self, price: float):
        """Inicializar estado con primer precio"""
        self.state = np.array([price, 0])
        self.P = np.array([
            [price * 0.01, 0],
            [0, 0.001]
        ])
        self.initialized = True
    
    def _predict(self):
        """Paso de predicción"""
        self.state = self.F @ self.state
        self.P = self.F @ self.P @ self.F.T + self.Q
    
    def _update(self, observation: float):
        """Paso de actualización con nueva observación"""
        self._predict()
        
        y = observation - self.H @ self.state
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T / S
        
        self.state = self.state + K.flatten() * y
        self.P = (np.eye(2) - K @ self.H) @ self.P
        
        self.history.append({
            'price': observation,
            'estimate': self.state[0],
            'velocity': self.state[1],
            'innovation': y
        })
        
        if len(self.history) > 500:
            self.history = self.history[-500:]
    
    def _calculate_signal(
        self,
        velocity: float,
        innovation: float,
        variance: float
    ) -> float:
        """Calcular señal de trading basada en estado de Kalman"""
        
        velocity_signal = np.tanh(velocity * 100)
        
        if variance > 0:
            std = np.sqrt(variance)
            z_score = innovation / std if std > 0 else 0
        else:
            z_score = 0
        
        if abs(z_score) > 2:
            mean_reversion = -np.sign(innovation) * 0.5
        else:
            mean_reversion = 0
        
        trend_confidence = 1 - min(variance * 100, 1)
        
        signal = (
            velocity_signal * 0.6 * trend_confidence +
            mean_reversion * 0.4
        )
        
        return np.clip(signal, -1, 1)
    
    def get_trend_strength(self) -> float:
        """Obtener fuerza de la tendencia actual"""
        if not self.initialized:
            return 0
        
        velocity = abs(self.state[1])
        variance = self.P[1, 1]
        
        if variance > 0:
            t_stat = velocity / np.sqrt(variance)
            strength = min(t_stat / 2, 1)
        else:
            strength = 0
        
        return strength
    
    def get_volatility_estimate(self) -> float:
        """Obtener estimación de volatilidad implícita"""
        if len(self.history) < 20:
            return 0
        
        innovations = [h['innovation'] for h in self.history[-20:]]
        return np.std(innovations)
    
    def reset(self):
        """Resetear estado del filtro"""
        self.state = np.zeros(2)
        self.P = np.eye(2) * 1.0
        self.initialized = False
        self.history = []


class AdaptiveKalmanFilter(StockKalmanFilter):
    """
    Filtro de Kalman Adaptativo
    Ajusta parámetros automáticamente según volatilidad
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.volatility_window = 20
        self.adaptation_rate = 0.1
    
    def _update(self, observation: float):
        """Actualización con adaptación de parámetros"""
        super()._update(observation)
        
        if len(self.history) >= self.volatility_window:
            recent_innovations = [h['innovation'] for h in self.history[-self.volatility_window:]]
            realized_var = np.var(recent_innovations)
            
            new_R = self.R + self.adaptation_rate * (realized_var - self.R)
            self.R = max(0.001, new_R)
