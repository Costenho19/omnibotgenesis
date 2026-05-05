"""
🎲 STOCK MONTE CARLO SIMULATOR V6.2
Simulaciones Monte Carlo adaptadas para mercado de acciones
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MonteCarloResult:
    expected_return: float
    var_95: float
    var_99: float
    probability_profit: float
    max_drawdown: float
    sharpe_estimate: float
    paths_analyzed: int
    signal: float


class StockMonteCarlo:
    """
    Simulador Monte Carlo para acciones
    Adaptado para menor volatilidad vs crypto
    
    Características:
    - 2000 paths de simulación
    - Geometric Brownian Motion calibrado para stocks
    - VaR 95% y 99%
    - Drawdown máximo estimado
    - Sharpe ratio proyectado
    """
    
    def __init__(
        self,
        n_paths: int = 2000,
        n_steps: int = 252,
        volatility_floor: float = 0.006,
        risk_free_rate: float = 0.05
    ):
        self.n_paths = n_paths
        self.n_steps = n_steps
        self.volatility_floor = volatility_floor
        self.risk_free_rate = risk_free_rate
        
        logger.info(f"🎲 Stock Monte Carlo inicializado: {n_paths} paths, {n_steps} steps")
    
    def analyze(self, prices: List[Dict]) -> Optional[float]:
        """
        Ejecutar simulación Monte Carlo y retornar señal
        
        Args:
            prices: Lista de OHLCV data
            
        Returns:
            Señal entre -1 (bearish) y 1 (bullish)
        """
        try:
            result = self.simulate(prices)
            if result:
                return result.signal
            return None
        except Exception as e:
            logger.error(f"Error en Monte Carlo: {e}")
            return None
    
    def simulate(self, prices: List[Dict], horizon_days: int = 20) -> Optional[MonteCarloResult]:
        """
        Ejecutar simulación completa
        
        Args:
            prices: Lista de OHLCV data
            horizon_days: Horizonte de predicción en días
            
        Returns:
            MonteCarloResult con métricas completas
        """
        try:
            closes = np.array([p['close'] for p in prices])
            
            if len(closes) < 30:
                logger.warning("Datos insuficientes para Monte Carlo")
                return None
            
            returns = np.diff(np.log(closes))
            
            mu = np.mean(returns)
            sigma = max(np.std(returns), self.volatility_floor)
            
            S0 = closes[-1]
            dt = 1 / 252
            
            np.random.seed(42)
            Z = np.random.standard_normal((self.n_paths, horizon_days))
            
            drift = (mu - 0.5 * sigma**2) * dt
            diffusion = sigma * np.sqrt(dt) * Z
            
            paths = np.zeros((self.n_paths, horizon_days + 1))
            paths[:, 0] = S0
            
            for t in range(1, horizon_days + 1):
                paths[:, t] = paths[:, t-1] * np.exp(drift + diffusion[:, t-1])
            
            final_prices = paths[:, -1]
            returns_sim = (final_prices - S0) / S0
            
            expected_return = np.mean(returns_sim)
            var_95 = np.percentile(returns_sim, 5)
            var_99 = np.percentile(returns_sim, 1)
            prob_profit = np.mean(returns_sim > 0)
            
            drawdowns = []
            for path in paths:
                peak = np.maximum.accumulate(path)
                dd = (peak - path) / peak
                drawdowns.append(np.max(dd))
            max_drawdown = np.mean(drawdowns)
            
            excess_return = expected_return * 252 - self.risk_free_rate
            annualized_vol = sigma * np.sqrt(252)
            sharpe_estimate = excess_return / annualized_vol if annualized_vol > 0 else 0
            
            signal = self._calculate_signal(
                expected_return, var_95, prob_profit, sharpe_estimate
            )
            
            return MonteCarloResult(
                expected_return=expected_return,
                var_95=var_95,
                var_99=var_99,
                probability_profit=prob_profit,
                max_drawdown=max_drawdown,
                sharpe_estimate=sharpe_estimate,
                paths_analyzed=self.n_paths,
                signal=signal
            )
            
        except Exception as e:
            logger.error(f"Error en simulación Monte Carlo: {e}")
            return None
    
    def _calculate_signal(
        self,
        expected_return: float,
        var_95: float,
        prob_profit: float,
        sharpe: float
    ) -> float:
        """Calcular señal consolidada de Monte Carlo"""
        
        return_signal = np.tanh(expected_return * 50)
        
        risk_signal = 1 - abs(var_95) * 10
        risk_signal = np.clip(risk_signal, -1, 1)
        
        prob_signal = (prob_profit - 0.5) * 2
        
        sharpe_signal = np.tanh(sharpe / 2)
        
        signal = (
            return_signal * 0.30 +
            prob_signal * 0.30 +
            sharpe_signal * 0.25 +
            risk_signal * 0.15
        )
        
        return np.clip(signal, -1, 1)
    
    def get_confidence_intervals(
        self, 
        prices: List[Dict],
        horizon_days: int = 20
    ) -> Optional[Dict]:
        """Obtener intervalos de confianza para precio futuro"""
        try:
            closes = np.array([p['close'] for p in prices])
            returns = np.diff(np.log(closes))
            
            mu = np.mean(returns)
            sigma = max(np.std(returns), self.volatility_floor)
            S0 = closes[-1]
            
            np.random.seed(42)
            final_prices = []
            
            for _ in range(self.n_paths):
                Z = np.random.standard_normal(horizon_days)
                log_return = sum((mu - 0.5 * sigma**2) / 252 + sigma * np.sqrt(1/252) * Z)
                final_prices.append(S0 * np.exp(log_return))
            
            final_prices = np.array(final_prices)
            
            return {
                'current_price': S0,
                'horizon_days': horizon_days,
                'expected_price': np.mean(final_prices),
                'median_price': np.median(final_prices),
                'ci_50': (np.percentile(final_prices, 25), np.percentile(final_prices, 75)),
                'ci_90': (np.percentile(final_prices, 5), np.percentile(final_prices, 95)),
                'ci_99': (np.percentile(final_prices, 0.5), np.percentile(final_prices, 99.5)),
                'prob_above_current': np.mean(final_prices > S0)
            }
            
        except Exception as e:
            logger.error(f"Error calculando intervalos: {e}")
            return None
