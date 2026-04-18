"""
OMNIX V5.3 ULTRA - Quantum-Enhanced Monte Carlo Simulation Engine
Simulaciones probabilísticas con QRNG (Quantum Random Number Generator)
Utiliza números verdaderamente aleatorios de fuentes cuánticas
"""

import numpy as np
from typing import Dict, Any, List, Optional
from omnix_config.settings import settings
from omnix_core.utils.logger import get_logger

logger = get_logger(__name__)

# Importar QRNG cuántico
global_qrng = None
try:
    from omnix_core.quantum import global_qrng
    QUANTUM_AVAILABLE = True
    logger.info("✅ Quantum RNG disponible - Monte Carlo usará números cuánticos")
except ImportError:
    try:
        from omnix_core.quantum.enhancements import global_qrng
        QUANTUM_AVAILABLE = True
        logger.info("✅ Quantum RNG disponible (fallback import)")
    except ImportError:
        QUANTUM_AVAILABLE = False
        global_qrng = None
        logger.warning("⚠️ Quantum RNG no disponible - usando generador clásico")


class MonteCarloSimulator:
    """
    Enterprise Monte Carlo simulation engine
    Uses Geometric Brownian Motion for realistic price simulations
    """
    
    def __init__(self, num_simulations: int = 10000):
        self.num_simulations = num_simulations
        self.time_horizon = 30  # days
        self.quantum_enabled = QUANTUM_AVAILABLE
        mode = "QUANTUM (ANU QRNG)" if self.quantum_enabled else "Classical"
        logger.info(f"🎲 Monte Carlo Simulator initialized: {num_simulations} simulations ({mode})")
    
    def simulate(
        self,
        current_price: float,
        volatility: float,
        drift: float = 0.0,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation using Geometric Brownian Motion
        
        Args:
            current_price: Current asset price
            volatility: Historical volatility (annualized)
            drift: Expected return (annualized)
            days: Simulation time horizon
            
        Returns:
            Dictionary with simulation results and statistics
        """
        try:
            dt = 1 / 365  # Daily time step
            num_steps = days
            
            # Generate random walks using QUANTUM or classical RNG
            if self.quantum_enabled and QUANTUM_AVAILABLE and global_qrng is not None:
                # QUANTUM: Números verdaderamente aleatorios de ANU Quantum API
                total_randoms = self.num_simulations * num_steps
                quantum_randoms = global_qrng.random_array(total_randoms)
                
                # CRITICAL: Clamp to (epsilon, 1-epsilon) to avoid log(0) in Box-Muller
                epsilon = 1e-12
                quantum_randoms = np.clip(quantum_randoms, epsilon, 1 - epsilon)
                
                # Convertir uniforme (0-1) a distribución normal usando Box-Muller
                # Transform: U1, U2 ~ Uniform(0,1) → Z1, Z2 ~ Normal(0,1)
                if total_randoms % 2 != 0:
                    extra_random = global_qrng.random()
                    extra_random = np.clip(extra_random, epsilon, 1 - epsilon)
                    quantum_randoms = np.append(quantum_randoms, extra_random)
                
                u1 = quantum_randoms[0::2]
                u2 = quantum_randoms[1::2]
                
                # Box-Muller transform (safe with clamped inputs)
                z1 = np.sqrt(-2 * np.log(u1)) * np.cos(2 * np.pi * u2)
                z2 = np.sqrt(-2 * np.log(u1)) * np.sin(2 * np.pi * u2)
                
                normal_randoms = np.concatenate([z1, z2])[:total_randoms]
                
                # Defensive check: if any NaNs detected, fall back to classical
                if np.any(np.isnan(normal_randoms)):
                    logger.warning("⚠️ QRNG produced NaNs - falling back to classical RNG")
                    rand = np.random.standard_normal((self.num_simulations, num_steps))
                else:
                    rand = normal_randoms.reshape((self.num_simulations, num_steps))
                    logger.debug(f"🎲 QUANTUM RNG: {total_randoms} números cuánticos generados")
            else:
                # CLASSICAL: Pseudorandom (numpy default)
                rand = np.random.standard_normal((self.num_simulations, num_steps))
            
            # Geometric Brownian Motion
            price_paths = np.zeros((self.num_simulations, num_steps + 1))
            price_paths[:, 0] = current_price
            
            for t in range(1, num_steps + 1):
                price_paths[:, t] = price_paths[:, t-1] * np.exp(
                    (drift - 0.5 * volatility**2) * dt +
                    volatility * np.sqrt(dt) * rand[:, t-1]
                )
            
            final_prices = price_paths[:, -1]
            returns = (final_prices - current_price) / current_price
            
            # Calculate statistics
            var_95 = np.percentile(returns, 5)  # 95% VaR
            var_99 = np.percentile(returns, 1)  # 99% VaR
            expected_return = np.mean(returns)
            std_return = np.std(returns)
            
            win_rate = np.sum(returns > 0) / len(returns)
            loss_rate = 1 - win_rate
            
            avg_win = np.mean(returns[returns > 0]) if np.any(returns > 0) else 0
            avg_loss = np.mean(returns[returns < 0]) if np.any(returns < 0) else 0
            
            result = {
                'num_simulations': self.num_simulations,
                'current_price': current_price,
                'final_price_mean': np.mean(final_prices),
                'final_price_median': np.median(final_prices),
                'final_price_std': np.std(final_prices),
                'expected_return': expected_return,
                'volatility': std_return,
                'var_95': var_95,
                'var_99': var_99,
                'win_rate': win_rate,
                'loss_rate': loss_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'risk_reward_ratio': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
                'best_case': np.max(returns),
                'worst_case': np.min(returns),
                'confidence_95_range': (
                    np.percentile(final_prices, 2.5),
                    np.percentile(final_prices, 97.5)
                )
            }
            
            logger.info(
                f"✅ Monte Carlo complete: Win rate={win_rate:.1%}, "
                f"VaR95={var_95:.2%}, Expected return={expected_return:.2%}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Monte Carlo simulation error: {e}")
            return {}
    
    def calculate_optimal_position_size(
        self,
        current_price: float,
        volatility: float,
        account_balance: float,
        risk_tolerance: float = 0.02
    ) -> Dict[str, Any]:
        """
        Calculate optimal position size using Kelly Criterion and Monte Carlo
        
        Args:
            current_price: Current price
            volatility: Asset volatility
            account_balance: Available capital
            risk_tolerance: Maximum acceptable loss (default 2%)
        """
        try:
            # Run simulation
            sim_result = self.simulate(current_price, volatility)
            
            if not sim_result:
                return {}
            
            win_rate = sim_result['win_rate']
            avg_win = sim_result['avg_win']
            avg_loss = abs(sim_result['avg_loss'])
            
            # Kelly Criterion: f = (p*b - q) / b
            # where p=win_rate, q=loss_rate, b=avg_win/avg_loss
            if avg_loss > 0:
                b = avg_win / avg_loss
                kelly_fraction = (win_rate * b - (1 - win_rate)) / b
                kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
            else:
                kelly_fraction = 0
            
            # Conservative position sizing
            kelly_position = account_balance * kelly_fraction
            var_based_position = account_balance * risk_tolerance / abs(sim_result['var_95'])
            
            recommended_position = min(kelly_position, var_based_position)
            recommended_position = max(10.0, recommended_position)  # Minimum $10
            
            return {
                'kelly_fraction': kelly_fraction,
                'kelly_position_usd': kelly_position,
                'var_based_position_usd': var_based_position,
                'recommended_position_usd': recommended_position,
                'recommended_units': recommended_position / current_price,
                'max_loss_usd': recommended_position * abs(sim_result['var_95']),
                'confidence': sim_result['win_rate']
            }
            
        except Exception as e:
            logger.error(f"Position size calculation error: {e}")
            return {}
