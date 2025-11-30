"""
🎯 STOCK HMM REGIME DETECTOR V6.2
Detección de régimen de mercado con Hidden Markov Model
Estados: Bull, Bear, Sideways, Crisis
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    CRISIS = "crisis"
    UNKNOWN = "unknown"


@dataclass
class RegimeState:
    current_regime: MarketRegime
    regime_probability: float
    state_probabilities: Dict[str, float]
    regime_duration: int
    transition_probability: float
    volatility_level: float


class StockHMMRegime:
    """
    Detector de régimen de mercado usando HMM simplificado
    
    Estados:
    - BULL: Tendencia alcista, baja volatilidad
    - BEAR: Tendencia bajista, volatilidad moderada
    - SIDEWAYS: Sin tendencia, baja volatilidad
    - CRISIS: Alta volatilidad, movimientos extremos
    
    Características:
    - Matriz de transición calibrada para mercado de acciones
    - Detección de cambios de régimen
    - Duración estimada del régimen actual
    """
    
    REGIME_PARAMS = {
        MarketRegime.BULL: {
            'mean_return': 0.0008,
            'volatility': 0.012,
            'persistence': 0.92
        },
        MarketRegime.BEAR: {
            'mean_return': -0.001,
            'volatility': 0.018,
            'persistence': 0.88
        },
        MarketRegime.SIDEWAYS: {
            'mean_return': 0.0,
            'volatility': 0.008,
            'persistence': 0.85
        },
        MarketRegime.CRISIS: {
            'mean_return': -0.003,
            'volatility': 0.035,
            'persistence': 0.75
        }
    }
    
    TRANSITION_MATRIX = np.array([
        [0.92, 0.03, 0.04, 0.01],
        [0.04, 0.88, 0.05, 0.03],
        [0.06, 0.06, 0.85, 0.03],
        [0.10, 0.10, 0.05, 0.75]
    ])
    
    def __init__(self, n_states: int = 4, lookback: int = 60):
        self.n_states = n_states
        self.lookback = lookback
        self.states = [MarketRegime.BULL, MarketRegime.BEAR, MarketRegime.SIDEWAYS, MarketRegime.CRISIS]
        
        self.current_state = MarketRegime.UNKNOWN
        self.state_probabilities = np.ones(n_states) / n_states
        self.regime_history = []
        
        logger.info(f"🎯 Stock HMM Regime Detector inicializado: {n_states} estados")
    
    def detect(self, prices: List[Dict]) -> MarketRegime:
        """
        Detectar régimen actual de mercado
        
        Args:
            prices: Lista de OHLCV data
            
        Returns:
            MarketRegime actual
        """
        try:
            state = self.analyze(prices)
            if state:
                return state.current_regime
            return MarketRegime.UNKNOWN
        except Exception as e:
            logger.error(f"Error en detección de régimen: {e}")
            return MarketRegime.UNKNOWN
    
    def analyze(self, prices: List[Dict]) -> Optional[RegimeState]:
        """
        Análisis completo de régimen
        
        Args:
            prices: Lista de OHLCV data
            
        Returns:
            RegimeState con probabilidades y métricas
        """
        try:
            if len(prices) < self.lookback:
                return None
            
            closes = np.array([p['close'] for p in prices[-self.lookback:]])
            returns = np.diff(np.log(closes))
            
            likelihoods = self._calculate_likelihoods(returns)
            
            self._update_probabilities(likelihoods)
            
            best_state_idx = np.argmax(self.state_probabilities)
            current_regime = self.states[best_state_idx]
            regime_prob = self.state_probabilities[best_state_idx]
            
            state_probs_dict = {
                state.value: prob 
                for state, prob in zip(self.states, self.state_probabilities)
            }
            
            regime_duration = self._calculate_regime_duration(current_regime)
            
            transition_prob = 1 - self.TRANSITION_MATRIX[best_state_idx, best_state_idx]
            
            volatility = np.std(returns) * np.sqrt(252)
            
            self.current_state = current_regime
            self.regime_history.append({
                'regime': current_regime,
                'probability': regime_prob,
                'volatility': volatility
            })
            
            if len(self.regime_history) > 500:
                self.regime_history = self.regime_history[-500:]
            
            return RegimeState(
                current_regime=current_regime,
                regime_probability=regime_prob,
                state_probabilities=state_probs_dict,
                regime_duration=regime_duration,
                transition_probability=transition_prob,
                volatility_level=volatility
            )
            
        except Exception as e:
            logger.error(f"Error en análisis de régimen: {e}")
            return None
    
    def _calculate_likelihoods(self, returns: np.ndarray) -> np.ndarray:
        """Calcular likelihood de observaciones para cada estado"""
        likelihoods = np.zeros(self.n_states)
        
        recent_return = np.mean(returns[-5:])
        recent_vol = np.std(returns[-20:])
        
        for i, state in enumerate(self.states):
            params = self.REGIME_PARAMS[state]
            
            mean = params['mean_return']
            vol = params['volatility']
            
            return_diff = (recent_return - mean) ** 2
            vol_diff = (recent_vol - vol) ** 2
            
            likelihood = np.exp(-return_diff / (2 * vol**2) - vol_diff / (2 * 0.01**2))
            likelihoods[i] = likelihood
        
        likelihoods = likelihoods / (np.sum(likelihoods) + 1e-10)
        
        return likelihoods
    
    def _update_probabilities(self, likelihoods: np.ndarray):
        """Actualizar probabilidades de estado con filtro bayesiano"""
        predicted_probs = self.TRANSITION_MATRIX.T @ self.state_probabilities
        
        posterior = predicted_probs * likelihoods
        posterior = posterior / (np.sum(posterior) + 1e-10)
        
        alpha = 0.3
        self.state_probabilities = alpha * posterior + (1 - alpha) * self.state_probabilities
        
        self.state_probabilities = self.state_probabilities / np.sum(self.state_probabilities)
    
    def _calculate_regime_duration(self, current_regime: MarketRegime) -> int:
        """Calcular duración del régimen actual"""
        if not self.regime_history:
            return 1
        
        duration = 0
        for entry in reversed(self.regime_history):
            if entry['regime'] == current_regime:
                duration += 1
            else:
                break
        
        return max(duration, 1)
    
    def get_regime_signal(self) -> float:
        """Obtener señal de trading basada en régimen"""
        if self.current_state == MarketRegime.BULL:
            base = 0.5
        elif self.current_state == MarketRegime.BEAR:
            base = -0.5
        elif self.current_state == MarketRegime.CRISIS:
            base = -0.7
        else:
            base = 0
        
        confidence = self.state_probabilities[self.states.index(self.current_state)]
        
        return base * confidence
    
    def predict_next_regime(self) -> Tuple[MarketRegime, float]:
        """Predecir próximo régimen más probable"""
        predicted_probs = self.TRANSITION_MATRIX.T @ self.state_probabilities
        best_idx = np.argmax(predicted_probs)
        return self.states[best_idx], predicted_probs[best_idx]
    
    def is_regime_change_likely(self, threshold: float = 0.3) -> bool:
        """Determinar si un cambio de régimen es probable"""
        if self.current_state == MarketRegime.UNKNOWN:
            return False
        
        current_idx = self.states.index(self.current_state)
        persistence = self.TRANSITION_MATRIX[current_idx, current_idx]
        
        return (1 - persistence) > threshold
