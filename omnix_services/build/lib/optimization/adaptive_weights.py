"""
⚡ OMNIX V5.2 QUANTUM ULTIMATE - ADAPTIVE WEIGHT SYSTEM
Sistema de Pesos Adaptativos entre Kalman Filter y Monte Carlo

📊 FUNCIONALIDAD PREMIUM INSTITUCIONAL:
- Ajuste dinámico de pesos ω(t) basado en multifractalidad
- Cálculo de Hurst Exponent H(t) en tiempo real (R/S Analysis)
- Estimación de α-stable tail index para colas pesadas (Hill Estimator)
- Ecuación adaptativa con función sigmoide para suavizado
- Criterios de cambio de régimen con umbrales dinámicos

🎯 USO:
El sistema ajusta automáticamente qué modelo (Kalman vs Monte Carlo) 
tiene más peso según las condiciones del mercado:
- H > 0.7: Mercado con memoria larga → favorece Monte Carlo
- α < 1.8: Colas pesadas (eventos extremos) → favorece Monte Carlo
- Condiciones normales → balance equilibrado

Desarrollado por Harold Nunes - Noviembre 2025
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AdaptiveWeights:
    """Pesos adaptativos del sistema"""
    omega: float  # Peso actual ω(t) ∈ [0,1], donde 0=100% Kalman, 1=100% Monte Carlo
    hurst: float  # Exponente de Hurst H(t)
    alpha: float  # Índice de estabilidad α(t)
    regime: str   # Régimen actual: NORMAL, TRENDING, VOLATILE, EXTREME
    confidence: float  # Confianza en la estimación [0,1]


class AdaptiveWeightSystem:
    """
    Sistema de Pesos Adaptativos Cuánticos V5.2
    
    Implementa la ecuación de pesos dinámicos para balancear Kalman vs Monte Carlo:
    ω(t) = ω(t-1) + Δω(t)
    Δω(t) = γ * [ sigmoid(H(t) - 0.7) * sigmoid(1.8 - α(t)) - ω(t-1) ]
    
    Comportamiento:
    - H > 0.7 (persistencia alta) → ω aumenta → favorece Monte Carlo
    - α < 1.8 (colas pesadas) → ω aumenta → favorece Monte Carlo
    - H ≈ 0.5, α ≈ 2.0 (normal) → ω ≈ 0 → balance Kalman/Monte Carlo
    - ω ∈ [0,1]: 0 = 100% Kalman, 1 = 100% Monte Carlo
    """
    
    def __init__(self, initial_omega: float = 0.5, learning_rate: float = 0.1):
        """
        Args:
            initial_omega: Peso inicial [0,1]. 0.5 = balance 50/50
            learning_rate: Tasa de aprendizaje γ para actualización adaptativa
        """
        self.omega = initial_omega  # Peso actual
        self.gamma = learning_rate  # Tasa de aprendizaje
        
        # Umbrales críticos
        self.HURST_THRESHOLD = 0.7  # H > 0.7 indica persistencia/memoria larga
        self.ALPHA_THRESHOLD = 1.8  # α < 1.8 indica colas pesadas
        
        # Historia para análisis
        self.history = {
            'omega': [],
            'hurst': [],
            'alpha': [],
            'regime': []
        }
        
        logger.info(f"⚡ Adaptive Weight System inicializado - ω(0)={initial_omega:.3f}, γ={learning_rate}")
    
    def update_weights(self, prices: List[float], returns: Optional[List[float]] = None) -> AdaptiveWeights:
        """
        Actualiza pesos adaptativos basado en datos de mercado
        
        Args:
            prices: Serie temporal de precios
            returns: Serie temporal de retornos (opcional, se calcula automáticamente)
        
        Returns:
            AdaptiveWeights con pesos actualizados
        """
        try:
            if len(prices) < 50:
                logger.warning(f"⚠️ Datos insuficientes ({len(prices)} < 50) - usando pesos por defecto")
                return AdaptiveWeights(
                    omega=self.omega,
                    hurst=0.5,
                    alpha=2.0,
                    regime='INSUFFICIENT_DATA',
                    confidence=0.0
                )
            
            # Calcular retornos si no se proporcionan
            if returns is None:
                returns = self._calculate_returns(prices)
            
            # 1. Calcular Hurst Exponent H(t)
            hurst = self._calculate_hurst_exponent(prices)
            
            # 2. Calcular α-stable tail index
            alpha = self._calculate_alpha_stable(returns)
            
            # 3. Actualizar ω(t) con ecuación adaptativa
            delta_omega = self._calculate_delta_omega(hurst, alpha)
            self.omega = np.clip(self.omega + delta_omega, 0.0, 1.0)
            
            # 4. Determinar régimen
            regime = self._determine_regime(hurst, alpha)
            
            # 5. Calcular confianza en la estimación
            confidence = self._calculate_confidence(len(prices), hurst, alpha)
            
            # Guardar en historia
            self.history['omega'].append(self.omega)
            self.history['hurst'].append(hurst)
            self.history['alpha'].append(alpha)
            self.history['regime'].append(regime)
            
            logger.info(f"📊 Pesos actualizados: ω={self.omega:.3f}, H={hurst:.3f}, α={alpha:.3f}, Régimen={regime}")
            
            return AdaptiveWeights(
                omega=self.omega,
                hurst=hurst,
                alpha=alpha,
                regime=regime,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"❌ Error actualizando pesos adaptativos: {e}")
            return AdaptiveWeights(
                omega=self.omega,
                hurst=0.5,
                alpha=2.0,
                regime='ERROR',
                confidence=0.0
            )
    
    def _calculate_delta_omega(self, hurst: float, alpha: float) -> float:
        """
        Calcula Δω(t) usando la ecuación adaptativa con sigmoides
        
        Δω(t) = γ * [ sigmoid(H - 0.7) * sigmoid(1.8 - α) - ω(t-1) ]
        
        CORRECCIÓN CRÍTICA:
        - H > 0.7 → sigmoid(H - 0.7) ≈ 1 → ω aumenta → favorece Monte Carlo ✓
        - α < 1.8 → sigmoid(1.8 - α) ≈ 1 → ω aumenta → favorece Monte Carlo ✓
        - Ambos extremos → ω → 1 (100% Monte Carlo) ✓
        """
        # Sigmoides para suavizar transiciones
        sigmoid_hurst = self._sigmoid(hurst - self.HURST_THRESHOLD)
        sigmoid_alpha = self._sigmoid(self.ALPHA_THRESHOLD - alpha)
        
        # Ecuación adaptativa CORREGIDA (sin el "1 -" que invertía la lógica)
        target_omega = sigmoid_hurst * sigmoid_alpha
        delta = self.gamma * (target_omega - self.omega)
        
        return delta
    
    def _sigmoid(self, x: float, steepness: float = 10.0) -> float:
        """
        Función sigmoide para transiciones suaves
        
        σ(x) = 1 / (1 + e^(-steepness * x))
        """
        return 1.0 / (1.0 + np.exp(-steepness * x))
    
    def _calculate_hurst_exponent(self, prices: List[float]) -> float:
        """
        Calcula el Exponente de Hurst usando R/S Analysis (Rescaled Range)
        
        H = 0.5: Random walk (Brownian motion)
        H > 0.5: Persistent/trending (memoria larga)
        H < 0.5: Mean-reverting (anti-persistente)
        
        Crítico: H > 0.7 indica fuerte persistencia → favorece Monte Carlo
        """
        try:
            prices_array = np.array(prices)
            n = len(prices_array)
            
            # Calcular retornos logarítmicos
            log_returns = np.diff(np.log(prices_array))
            
            # R/S Analysis con múltiples ventanas
            lags = range(10, min(n // 4, 100))
            rs_values = []
            
            for lag in lags:
                # Dividir serie en sub-períodos
                num_periods = len(log_returns) // lag
                if num_periods < 2:
                    continue
                
                rs_period = []
                for i in range(num_periods):
                    period = log_returns[i*lag:(i+1)*lag]
                    
                    # Mean-adjusted cumulative sum
                    mean = np.mean(period)
                    cumsum = np.cumsum(period - mean)
                    
                    # Range
                    R = np.max(cumsum) - np.min(cumsum)
                    
                    # Standard deviation
                    S = np.std(period, ddof=1)
                    
                    if S > 0:
                        rs_period.append(R / S)
                
                if rs_period:
                    rs_values.append(np.mean(rs_period))
            
            if len(rs_values) < 2:
                return 0.5  # Default: random walk
            
            # Hurst = pendiente de log(R/S) vs log(lag)
            log_lags = np.log(list(lags)[:len(rs_values)])
            log_rs = np.log(rs_values)
            
            # Regresión lineal
            hurst = np.polyfit(log_lags, log_rs, 1)[0]
            
            # Clip al rango válido [0, 1]
            hurst = np.clip(hurst, 0.0, 1.0)
            
            return hurst
            
        except Exception as e:
            logger.error(f"❌ Error calculando Hurst: {e}")
            return 0.5  # Default
    
    def _calculate_alpha_stable(self, returns: List[float]) -> float:
        """
        Estima el índice α-stable usando Hill Estimator para colas pesadas
        
        α = 2.0: Distribución normal (colas ligeras)
        α < 2.0: Colas pesadas (eventos extremos frecuentes)
        α < 1.8: CRÍTICO - colas muy pesadas → favorece Monte Carlo
        
        El Hill estimator usa los valores extremos (orden estadístico)
        """
        try:
            returns_array = np.abs(np.array(returns))
            n = len(returns_array)
            
            if n < 20:
                return 2.0  # Default: normal
            
            # Ordenar retornos en orden descendente
            sorted_returns = np.sort(returns_array)[::-1]
            
            # Usar top 10% para estimar colas
            k = max(int(n * 0.1), 10)
            
            # Hill Estimator
            # α̂ = 1 / (1/k * Σ log(X_i / X_{k+1}))
            if sorted_returns[k] > 0:
                log_ratios = np.log(sorted_returns[:k] / sorted_returns[k])
                hill_estimate = 1.0 / np.mean(log_ratios)
                
                # α-stable típicamente en rango [1.0, 2.0]
                # Valores fuera sugieren distribuciones extremas
                alpha = np.clip(hill_estimate, 0.5, 2.5)
            else:
                alpha = 2.0
            
            return alpha
            
        except Exception as e:
            logger.error(f"❌ Error calculando α-stable: {e}")
            return 2.0  # Default: normal
    
    def _determine_regime(self, hurst: float, alpha: float) -> str:
        """
        Determina el régimen de mercado basado en H y α
        
        Regímenes:
        - NORMAL: Condiciones normales (H≈0.5, α≈2.0)
        - TRENDING: Persistencia fuerte (H>0.7)
        - VOLATILE: Colas pesadas (α<1.8)
        - EXTREME: Ambos extremos (H>0.7 AND α<1.8)
        """
        if hurst > self.HURST_THRESHOLD and alpha < self.ALPHA_THRESHOLD:
            return 'EXTREME'  # Crítico: persistencia + colas pesadas
        elif hurst > self.HURST_THRESHOLD:
            return 'TRENDING'  # Fuerte memoria/tendencia
        elif alpha < self.ALPHA_THRESHOLD:
            return 'VOLATILE'  # Eventos extremos frecuentes
        else:
            return 'NORMAL'  # Condiciones normales
    
    def _calculate_confidence(self, n_samples: int, hurst: float, alpha: float) -> float:
        """
        Calcula confianza en la estimación basada en:
        - Cantidad de datos disponibles
        - Estabilidad de H y α (qué tan lejos están de extremos)
        """
        # Confianza por cantidad de datos
        sample_confidence = min(n_samples / 200.0, 1.0)  # 200+ samples = max confidence
        
        # Penalizar estimaciones en extremos (menos confiables)
        hurst_confidence = 1.0 - abs(hurst - 0.5) * 2.0  # Max en H=0.5
        alpha_confidence = min(abs(alpha - 2.0) / 1.0, 1.0)  # Penalizar lejos de 2.0
        
        # Confianza combinada
        confidence = (sample_confidence + hurst_confidence + alpha_confidence) / 3.0
        
        return np.clip(confidence, 0.0, 1.0)
    
    def _calculate_returns(self, prices: List[float]) -> List[float]:
        """Calcula retornos logarítmicos"""
        prices_array = np.array(prices)
        return list(np.diff(np.log(prices_array)))
    
    def get_model_weights(self, omega: float) -> Dict[str, float]:
        """
        Convierte ω en pesos para cada modelo
        
        ω = 0.0 → 100% Kalman, 0% Monte Carlo
        ω = 0.5 → 50% Kalman, 50% Monte Carlo
        ω = 1.0 → 0% Kalman, 100% Monte Carlo
        """
        return {
            'kalman_weight': 1.0 - omega,
            'monte_carlo_weight': omega
        }
    
    def should_switch_regime(self, threshold: float = 0.7) -> bool:
        """
        Determina si se debe cambiar de régimen basado en ω(t)
        
        Args:
            threshold: Umbral para cambio (default 0.7)
        
        Returns:
            True si ω está en extremo (>threshold o <1-threshold)
        """
        return self.omega > threshold or self.omega < (1.0 - threshold)
    
    def get_statistics(self) -> Dict:
        """Obtiene estadísticas del sistema adaptativo"""
        if not self.history['omega']:
            return {}
        
        return {
            'current_omega': self.omega,
            'avg_omega': np.mean(self.history['omega']),
            'avg_hurst': np.mean(self.history['hurst']),
            'avg_alpha': np.mean(self.history['alpha']),
            'regime_distribution': {
                regime: self.history['regime'].count(regime) / len(self.history['regime'])
                for regime in set(self.history['regime'])
            },
            'n_updates': len(self.history['omega'])
        }


# ============================================
# FUNCIONES DE UTILIDAD
# ============================================

def create_adaptive_system(config: Optional[Dict] = None) -> AdaptiveWeightSystem:
    """
    Factory function para crear sistema adaptativo
    
    Args:
        config: Configuración opcional con 'initial_omega' y 'learning_rate'
    """
    if config is None:
        config = {}
    
    return AdaptiveWeightSystem(
        initial_omega=config.get('initial_omega', 0.5),
        learning_rate=config.get('learning_rate', 0.1)
    )


def interpret_regime(regime: str) -> str:
    """Interpreta régimen para usuarios"""
    interpretations = {
        'NORMAL': '✅ Condiciones normales de mercado - Balance equilibrado',
        'TRENDING': '📈 Mercado con tendencia fuerte - Favorece Monte Carlo',
        'VOLATILE': '⚡ Alta volatilidad con eventos extremos - Favorece Monte Carlo',
        'EXTREME': '🔥 CRÍTICO: Tendencia + Volatilidad extrema - Monte Carlo dominante',
        'INSUFFICIENT_DATA': '⚠️ Datos insuficientes - Usando configuración por defecto',
        'ERROR': '❌ Error en cálculo - Usando valores seguros'
    }
    return interpretations.get(regime, regime)
