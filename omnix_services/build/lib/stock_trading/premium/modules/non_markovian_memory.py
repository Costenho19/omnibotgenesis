"""
🧠 STOCK NON-MARKOVIAN MEMORY KERNEL V6.2
Kernel de memoria no-markoviano para patrones de mercado de acciones
Captura dependencias temporales de largo plazo
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class MemoryPattern:
    pattern_type: str
    strength: float
    lag: int
    confidence: float
    last_occurrence: datetime


@dataclass
class MemoryState:
    coherence: float
    dominant_patterns: List[MemoryPattern]
    temporal_correlation: float
    regime_memory: float
    cyclical_component: float


class StockMemoryKernel:
    """
    Kernel de Memoria No-Markoviano para Acciones
    
    Fórmula base: K(t-s) = exp(-|t-s|/τ)[1 + ε cos(Ω(t-s))]
    
    Características:
    - Memoria exponencial decayente (τ = 60 días para acciones)
    - Componente cíclico para patrones estacionales
    - Detección de coherencia temporal
    - Memoria de transiciones de régimen
    
    Diferencias vs Crypto:
    - Decay más lento (60 vs 30 días)
    - Ciclos de mercado más largos
    - Patrones estacionales (earnings, dividendos)
    """
    
    KERNEL_PARAMS = {
        'tau': 60,
        'epsilon': 0.3,
        'omega': 2 * np.pi / 63,
        'min_coherence': 0.3,
        'memory_depth': 252,
        'pattern_threshold': 0.6
    }
    
    def __init__(self, decay_days: int = 60):
        self.tau = decay_days
        self.memory_depth = self.KERNEL_PARAMS['memory_depth']
        
        self.price_memory = {}
        self.pattern_memory = {}
        self.regime_transitions = deque(maxlen=50)
        self.coherence_history = deque(maxlen=100)
        
        logger.info(f"🧠 Stock Non-Markovian Memory Kernel inicializado")
        logger.info(f"   τ (decay): {self.tau} días")
        logger.info(f"   Profundidad: {self.memory_depth} observaciones")
    
    def get_coherence(self, symbol: str, prices: List[Dict]) -> float:
        """
        Calcular coherencia de memoria para símbolo
        
        Args:
            symbol: Símbolo de acción
            prices: Lista de OHLCV data
            
        Returns:
            Coherencia entre 0 y 1
        """
        try:
            state = self.analyze(symbol, prices)
            if state:
                return state.coherence
            return 0.5
        except Exception as e:
            logger.error(f"Error en coherencia: {e}")
            return 0.5
    
    def analyze(self, symbol: str, prices: List[Dict]) -> Optional[MemoryState]:
        """
        Análisis completo de memoria para símbolo
        
        Args:
            symbol: Símbolo de acción
            prices: Lista de OHLCV data
            
        Returns:
            MemoryState con métricas de memoria
        """
        try:
            if len(prices) < 60:
                return None
            
            closes = np.array([p['close'] for p in prices])
            returns = np.diff(np.log(closes))
            
            self._update_memory(symbol, returns)
            
            temporal_corr = self._calculate_temporal_correlation(returns)
            
            patterns = self._detect_patterns(symbol, returns)
            
            regime_memory = self._calculate_regime_memory()
            
            cyclical = self._calculate_cyclical_component(returns)
            
            coherence = self._calculate_coherence(
                temporal_corr,
                patterns,
                regime_memory,
                cyclical
            )
            
            self.coherence_history.append(coherence)
            
            return MemoryState(
                coherence=coherence,
                dominant_patterns=patterns[:3] if patterns else [],
                temporal_correlation=temporal_corr,
                regime_memory=regime_memory,
                cyclical_component=cyclical
            )
            
        except Exception as e:
            logger.error(f"Error en análisis de memoria: {e}")
            return None
    
    def _update_memory(self, symbol: str, returns: np.ndarray):
        """Actualizar memoria con nuevos retornos"""
        if symbol not in self.price_memory:
            self.price_memory[symbol] = deque(maxlen=self.memory_depth)
        
        for ret in returns[-20:]:
            self.price_memory[symbol].append({
                'return': ret,
                'timestamp': datetime.now()
            })
    
    def _calculate_temporal_correlation(self, returns: np.ndarray) -> float:
        """Calcular correlación temporal usando kernel de memoria"""
        if len(returns) < 20:
            return 0
        
        n = len(returns)
        kernel_weights = np.zeros(n)
        
        for i in range(n):
            lag = n - 1 - i
            decay = np.exp(-lag / self.tau)
            cyclical = 1 + self.KERNEL_PARAMS['epsilon'] * np.cos(self.KERNEL_PARAMS['omega'] * lag)
            kernel_weights[i] = decay * cyclical
        
        kernel_weights = kernel_weights / np.sum(kernel_weights)
        
        weighted_returns = returns * kernel_weights
        
        if len(returns) >= 2:
            autocorr = np.corrcoef(returns[:-1], returns[1:])[0, 1]
            if np.isnan(autocorr):
                autocorr = 0
        else:
            autocorr = 0
        
        temporal_corr = np.sum(weighted_returns * np.sign(weighted_returns))
        temporal_corr = np.clip(temporal_corr, -1, 1)
        
        return (temporal_corr + autocorr) / 2
    
    def _detect_patterns(self, symbol: str, returns: np.ndarray) -> List[MemoryPattern]:
        """Detectar patrones repetitivos en memoria"""
        patterns = []
        
        if len(returns) < 60:
            return patterns
        
        window = 20
        pattern_lags = [5, 10, 21, 42, 63, 126]
        
        for lag in pattern_lags:
            if len(returns) >= lag + window:
                current = returns[-window:]
                historical = returns[-(lag + window):-lag]
                
                if len(current) == len(historical):
                    corr = np.corrcoef(current, historical)[0, 1]
                    
                    if not np.isnan(corr) and abs(corr) > self.KERNEL_PARAMS['pattern_threshold']:
                        pattern_type = "momentum" if corr > 0 else "reversal"
                        
                        patterns.append(MemoryPattern(
                            pattern_type=pattern_type,
                            strength=abs(corr),
                            lag=lag,
                            confidence=min(abs(corr), 1.0),
                            last_occurrence=datetime.now() - timedelta(days=lag)
                        ))
        
        patterns.sort(key=lambda x: x.strength, reverse=True)
        
        if symbol not in self.pattern_memory:
            self.pattern_memory[symbol] = []
        self.pattern_memory[symbol] = patterns[:5]
        
        return patterns
    
    def _calculate_regime_memory(self) -> float:
        """Calcular memoria de transiciones de régimen"""
        if len(self.regime_transitions) < 2:
            return 0.5
        
        recent_transitions = list(self.regime_transitions)[-10:]
        
        same_direction = 0
        for i in range(1, len(recent_transitions)):
            if recent_transitions[i] == recent_transitions[i-1]:
                same_direction += 1
        
        persistence = same_direction / max(len(recent_transitions) - 1, 1)
        
        return persistence
    
    def _calculate_cyclical_component(self, returns: np.ndarray) -> float:
        """Calcular componente cíclico (estacionalidad)"""
        if len(returns) < 126:
            return 0
        
        quarterly_returns = []
        for i in range(0, len(returns) - 63, 63):
            quarterly_returns.append(np.sum(returns[i:i+63]))
        
        if len(quarterly_returns) < 2:
            return 0
        
        variance = np.var(quarterly_returns)
        cyclical_strength = 1 - np.exp(-variance * 100)
        
        return np.clip(cyclical_strength, 0, 1)
    
    def _calculate_coherence(
        self,
        temporal_corr: float,
        patterns: List[MemoryPattern],
        regime_memory: float,
        cyclical: float
    ) -> float:
        """Calcular coherencia total de memoria"""
        
        corr_component = (temporal_corr + 1) / 2
        
        if patterns:
            pattern_component = np.mean([p.strength for p in patterns[:3]])
        else:
            pattern_component = 0.5
        
        coherence = (
            corr_component * 0.30 +
            pattern_component * 0.30 +
            regime_memory * 0.25 +
            cyclical * 0.15
        )
        
        return np.clip(coherence, 0, 1)
    
    def add_regime_transition(self, from_regime: str, to_regime: str):
        """Registrar transición de régimen"""
        self.regime_transitions.append({
            'from': from_regime,
            'to': to_regime,
            'timestamp': datetime.now()
        })
    
    def get_memory_signal(self, symbol: str) -> float:
        """Obtener señal basada en memoria"""
        if symbol not in self.price_memory:
            return 0
        
        memory = list(self.price_memory[symbol])
        if len(memory) < 10:
            return 0
        
        n = len(memory)
        weights = [np.exp(-(n - 1 - i) / self.tau) for i in range(n)]
        weights = np.array(weights) / sum(weights)
        
        returns = [m['return'] for m in memory]
        
        weighted_return = np.sum(np.array(returns) * weights)
        
        return np.tanh(weighted_return * 50)
    
    def get_pattern_prediction(self, symbol: str) -> Optional[Dict]:
        """Obtener predicción basada en patrones detectados"""
        if symbol not in self.pattern_memory or not self.pattern_memory[symbol]:
            return None
        
        top_pattern = self.pattern_memory[symbol][0]
        
        if top_pattern.pattern_type == "momentum":
            prediction = "continuation"
            direction = "same as current trend"
        else:
            prediction = "reversal"
            direction = "opposite to current trend"
        
        return {
            'prediction': prediction,
            'direction': direction,
            'confidence': top_pattern.confidence,
            'based_on_lag': top_pattern.lag,
            'pattern_strength': top_pattern.strength
        }
    
    def get_status(self) -> Dict:
        """Obtener estado del kernel de memoria"""
        return {
            'symbols_tracked': list(self.price_memory.keys()),
            'total_patterns': sum(len(p) for p in self.pattern_memory.values()),
            'regime_transitions': len(self.regime_transitions),
            'avg_coherence': np.mean(list(self.coherence_history)) if self.coherence_history else 0,
            'parameters': self.KERNEL_PARAMS
        }
