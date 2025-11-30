"""
OMNIX V6.4 INSTITUTIONAL+ Portfolio Optimizer
Markowitz Mean-Variance + Black-Litterman Views Integration
Goldman Sachs Asset Management methodology
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class OptimizationMode(Enum):
    """Portfolio optimization modes"""
    MIN_VARIANCE = "min_variance"
    MAX_SHARPE = "max_sharpe"
    RISK_PARITY = "risk_parity"
    BLACK_LITTERMAN = "black_litterman"


@dataclass
class OptimizationResult:
    """Container for optimization results"""
    weights: Dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    mode: OptimizationMode
    optimization_date: datetime
    iterations: int
    converged: bool


class PortfolioOptimizer:
    """
    INSTITUTIONAL+ Portfolio Optimizer V6.4
    
    Implements:
    - Markowitz Mean-Variance Optimization
    - Black-Litterman Model (views integration)
    - Risk Parity Allocation
    - Constrained Optimization (max weights, long-only)
    
    Key Innovation: Blends your module signals (HMM, ARES, Monte Carlo)
    with market equilibrium returns using Black-Litterman framework.
    """
    
    VERSION = "6.4.0"
    
    def __init__(
        self,
        risk_aversion: float = 3.0,
        risk_free_rate: float = 0.045,
        max_iterations: int = 1000,
        convergence_threshold: float = 1e-8
    ):
        self.risk_aversion = risk_aversion
        self.risk_free_rate = risk_free_rate
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        
        logger.info(f"PortfolioOptimizer V{self.VERSION} initialized | λ={risk_aversion}")
    
    def mean_variance_optimize(
        self,
        expected_returns: np.ndarray,
        cov_matrix: np.ndarray,
        symbols: List[str],
        max_weight: float = 0.20,
        min_weight: float = 0.0,
        mode: OptimizationMode = OptimizationMode.MAX_SHARPE
    ) -> OptimizationResult:
        """
        Markowitz Mean-Variance Optimization
        
        Args:
            expected_returns: Vector of expected returns (N,)
            cov_matrix: Covariance matrix (N,N)
            symbols: List of asset symbols
            max_weight: Maximum weight per asset
            min_weight: Minimum weight per asset (0 = long-only)
            mode: Optimization objective
        
        Returns:
            OptimizationResult with optimal weights
        """
        n = len(expected_returns)
        
        if n == 0:
            return self._empty_result(mode)
        
        if n != cov_matrix.shape[0]:
            raise ValueError(f"Dimension mismatch: returns({n}) vs cov({cov_matrix.shape})")
        
        w = np.ones(n) / n
        
        learning_rate = 0.01
        momentum = 0.9
        velocity = np.zeros(n)
        
        converged = False
        iteration = 0
        
        for iteration in range(self.max_iterations):
            if mode == OptimizationMode.MAX_SHARPE:
                port_return = w @ expected_returns
                port_vol = np.sqrt(w @ cov_matrix @ w)
                
                if port_vol > 0:
                    grad_return = expected_returns
                    grad_vol = (cov_matrix @ w) / port_vol
                    excess_return = port_return - self.risk_free_rate
                    
                    grad = (grad_return * port_vol - excess_return * grad_vol) / (port_vol ** 2)
                else:
                    grad = expected_returns
                    
            elif mode == OptimizationMode.MIN_VARIANCE:
                grad = -2 * (cov_matrix @ w)
                
            elif mode == OptimizationMode.RISK_PARITY:
                port_vol = np.sqrt(w @ cov_matrix @ w)
                marginal_risk = (cov_matrix @ w) / port_vol if port_vol > 0 else np.ones(n)
                risk_contribution = w * marginal_risk
                target_rc = port_vol / n
                grad = -(risk_contribution - target_rc)
                
            else:
                grad = -expected_returns + self.risk_aversion * (cov_matrix @ w)
            
            velocity = momentum * velocity + learning_rate * grad
            w_new = w + velocity
            
            w_new = np.clip(w_new, min_weight, max_weight)
            
            if np.sum(w_new) > 0:
                w_new = w_new / np.sum(w_new)
            else:
                w_new = np.ones(n) / n
            
            if np.max(np.abs(w_new - w)) < self.convergence_threshold:
                converged = True
                w = w_new
                break
            
            w = w_new
        
        port_return = float(w @ expected_returns)
        port_vol = float(np.sqrt(w @ cov_matrix @ w))
        sharpe = (port_return - self.risk_free_rate) / port_vol if port_vol > 0 else 0
        
        weights_dict = {symbols[i]: round(float(w[i]), 6) for i in range(n)}
        
        result = OptimizationResult(
            weights=weights_dict,
            expected_return=round(port_return, 6),
            expected_volatility=round(port_vol, 6),
            sharpe_ratio=round(sharpe, 4),
            mode=mode,
            optimization_date=datetime.now(),
            iterations=iteration + 1,
            converged=converged
        )
        
        logger.info(
            f"Optimization complete | Mode: {mode.value} | "
            f"Sharpe: {sharpe:.2f} | Converged: {converged}"
        )
        
        return result
    
    def black_litterman_blend(
        self,
        equilibrium_returns: np.ndarray,
        view_returns: np.ndarray,
        view_confidence: float = 0.5,
        tau: float = 0.05
    ) -> np.ndarray:
        """
        Black-Litterman Model - Blend equilibrium with views
        
        This is the KEY innovation for institutional portfolios:
        - Equilibrium returns: What the market implies (from CAPM/historical)
        - View returns: What YOUR modules predict (HMM, ARES, Monte Carlo)
        - Confidence: How much to trust your views vs market
        
        Args:
            equilibrium_returns: Market-implied expected returns
            view_returns: Returns predicted by your modules
            view_confidence: Confidence in views (0=ignore views, 1=only views)
            tau: Uncertainty scalar (typically 0.025-0.05)
        
        Returns:
            Blended expected returns vector
        """
        confidence = np.clip(view_confidence, 0.0, 1.0)
        
        blended = (1 - confidence) * equilibrium_returns + confidence * view_returns
        
        uncertainty_adjustment = 1 / (1 + tau * (1 - confidence))
        blended = blended * uncertainty_adjustment
        
        return blended
    
    def compute_equilibrium_returns(
        self,
        cov_matrix: np.ndarray,
        market_weights: np.ndarray,
        risk_aversion: Optional[float] = None
    ) -> np.ndarray:
        """
        Compute equilibrium returns (reverse optimization)
        
        This computes the implied expected returns that would make
        the current market weights optimal. Used as the starting
        point for Black-Litterman.
        
        Args:
            cov_matrix: Asset covariance matrix
            market_weights: Current market capitalization weights
            risk_aversion: Risk aversion parameter (default: self.risk_aversion)
        
        Returns:
            Implied equilibrium returns
        """
        if risk_aversion is None:
            risk_aversion = self.risk_aversion
        
        equilibrium = risk_aversion * (cov_matrix @ market_weights)
        
        return equilibrium
    
    def views_from_signals(
        self,
        signals: Dict[str, Dict],
        symbols: List[str],
        base_return: float = 0.10
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert OMNIX module signals to Black-Litterman views
        
        Args:
            signals: Dict of signals per symbol, each containing:
                - 'direction': 'LONG', 'SHORT', 'NEUTRAL'
                - 'confidence': 0.0-1.0
                - 'source': 'HMM', 'ARES', 'MONTE_CARLO', etc.
            symbols: List of symbols in order
            base_return: Base annual return for strong signals
        
        Returns:
            Tuple of (view_returns, view_confidences)
        """
        n = len(symbols)
        view_returns = np.zeros(n)
        view_confidences = np.zeros(n)
        
        direction_multiplier = {
            'LONG': 1.0,
            'STRONG_LONG': 1.5,
            'SHORT': -1.0,
            'STRONG_SHORT': -1.5,
            'NEUTRAL': 0.0
        }
        
        source_weight = {
            'HMM': 1.2,
            'ARES': 1.1,
            'MONTE_CARLO': 1.0,
            'KALMAN': 1.0,
            'MEMORY_KERNEL': 1.15,
            'COHERENCE': 0.9,
            'DEFAULT': 1.0
        }
        
        for i, symbol in enumerate(symbols):
            if symbol not in signals:
                continue
            
            signal = signals[symbol]
            direction = signal.get('direction', 'NEUTRAL').upper()
            confidence = signal.get('confidence', 0.5)
            source = signal.get('source', 'DEFAULT').upper()
            
            mult = direction_multiplier.get(direction, 0.0)
            src_weight = source_weight.get(source, 1.0)
            
            view_returns[i] = base_return * mult * src_weight * confidence
            view_confidences[i] = confidence
        
        return view_returns, view_confidences
    
    def optimize_with_views(
        self,
        cov_matrix: np.ndarray,
        symbols: List[str],
        signals: Dict[str, Dict],
        market_weights: Optional[np.ndarray] = None,
        view_confidence: float = 0.5,
        max_weight: float = 0.20
    ) -> OptimizationResult:
        """
        Full Black-Litterman optimization pipeline
        
        This is the MAIN entry point for institutional portfolio optimization.
        
        Args:
            cov_matrix: Asset covariance matrix
            symbols: List of asset symbols
            signals: Module signals (HMM, ARES, etc.)
            market_weights: Market cap weights (default: equal weight)
            view_confidence: Overall confidence in views
            max_weight: Maximum weight per asset
        
        Returns:
            OptimizationResult with optimal portfolio
        """
        n = len(symbols)
        
        if n == 0:
            return self._empty_result(OptimizationMode.BLACK_LITTERMAN)
        
        if market_weights is None:
            market_weights = np.ones(n) / n
        
        equilibrium = self.compute_equilibrium_returns(cov_matrix, market_weights)
        
        view_returns, _ = self.views_from_signals(signals, symbols)
        
        blended_returns = self.black_litterman_blend(
            equilibrium, view_returns, view_confidence
        )
        
        result = self.mean_variance_optimize(
            expected_returns=blended_returns,
            cov_matrix=cov_matrix,
            symbols=symbols,
            max_weight=max_weight,
            mode=OptimizationMode.BLACK_LITTERMAN
        )
        
        return result
    
    def _empty_result(self, mode: OptimizationMode) -> OptimizationResult:
        """Return empty result for edge cases"""
        return OptimizationResult(
            weights={},
            expected_return=0.0,
            expected_volatility=0.0,
            sharpe_ratio=0.0,
            mode=mode,
            optimization_date=datetime.now(),
            iterations=0,
            converged=True
        )
    
    def get_status(self) -> Dict:
        """Get optimizer status"""
        return {
            "engine": "PortfolioOptimizer",
            "version": self.VERSION,
            "risk_aversion": self.risk_aversion,
            "risk_free_rate": self.risk_free_rate,
            "max_iterations": self.max_iterations
        }
