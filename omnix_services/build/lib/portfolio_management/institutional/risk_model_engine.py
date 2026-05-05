"""
OMNIX V6.4 INSTITUTIONAL+ Risk Model Engine
Computes: Covariance Matrix, Correlations, Beta vs Benchmark
Foundation for all portfolio optimization decisions
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Container for computed risk metrics"""
    covariance_matrix: np.ndarray
    correlation_matrix: np.ndarray
    betas: Dict[str, float]
    volatilities: Dict[str, float]
    benchmark_volatility: float
    computation_date: datetime
    symbols: List[str]
    data_quality_score: float


class RiskModelEngine:
    """
    INSTITUTIONAL+ Risk Model Engine V6.4
    
    Computes institutional-grade risk metrics:
    - Covariance matrix (portfolio variance calculation)
    - Correlation matrix (diversification analysis)
    - Beta vs benchmark (systematic risk exposure)
    - Individual asset volatilities
    
    Used by: PortfolioOptimizer, ExposureManager, ClusteringRiskDetector
    """
    
    VERSION = "6.4.0"
    
    def __init__(
        self,
        benchmark_symbol: str = "SPY",
        lookback_days: int = 90,
        min_data_points: int = 30,
        annualization_factor: int = 252
    ):
        self.benchmark_symbol = benchmark_symbol
        self.lookback_days = lookback_days
        self.min_data_points = min_data_points
        self.annualization_factor = annualization_factor
        
        self._cached_metrics: Optional[RiskMetrics] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_minutes = 60
        
        logger.info(f"RiskModelEngine V{self.VERSION} initialized | Benchmark: {benchmark_symbol}")
    
    def compute_returns(
        self,
        prices: Dict[str, List[float]],
        log_returns: bool = True
    ) -> Dict[str, np.ndarray]:
        """
        Compute returns from price series
        
        Args:
            prices: Dict mapping symbol to list of prices (oldest first)
            log_returns: Use log returns (more accurate for compounding)
        
        Returns:
            Dict mapping symbol to numpy array of returns
        """
        returns = {}
        
        for symbol, price_series in prices.items():
            if len(price_series) < 2:
                logger.warning(f"Insufficient data for {symbol}: {len(price_series)} points")
                continue
            
            prices_arr = np.array(price_series, dtype=float)
            
            if log_returns:
                rets = np.diff(np.log(prices_arr))
            else:
                rets = np.diff(prices_arr) / prices_arr[:-1]
            
            rets = np.nan_to_num(rets, nan=0.0, posinf=0.0, neginf=0.0)
            returns[symbol] = rets
        
        return returns
    
    def compute_covariance(
        self,
        returns: Dict[str, np.ndarray],
        shrinkage: float = 0.1
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Compute covariance matrix with Ledoit-Wolf shrinkage
        
        Args:
            returns: Dict of returns per symbol
            shrinkage: Shrinkage intensity (0 = sample cov, 1 = diagonal)
        
        Returns:
            Tuple of (covariance matrix, symbol list)
        """
        symbols = list(returns.keys())
        n_assets = len(symbols)
        
        if n_assets == 0:
            return np.array([[]]), []
        
        min_length = min(len(r) for r in returns.values())
        returns_matrix = np.zeros((min_length, n_assets))
        
        for i, symbol in enumerate(symbols):
            returns_matrix[:, i] = returns[symbol][-min_length:]
        
        sample_cov = np.cov(returns_matrix.T)
        
        if shrinkage > 0:
            diagonal = np.diag(np.diag(sample_cov))
            cov = (1 - shrinkage) * sample_cov + shrinkage * diagonal
        else:
            cov = sample_cov
        
        if n_assets == 1:
            cov = np.array([[cov]])
        
        return cov, symbols
    
    def compute_correlation(
        self,
        returns: Dict[str, np.ndarray]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Compute correlation matrix
        
        Returns:
            Tuple of (correlation matrix, symbol list)
        """
        symbols = list(returns.keys())
        n_assets = len(symbols)
        
        if n_assets == 0:
            return np.array([[]]), []
        
        min_length = min(len(r) for r in returns.values())
        returns_matrix = np.zeros((min_length, n_assets))
        
        for i, symbol in enumerate(symbols):
            returns_matrix[:, i] = returns[symbol][-min_length:]
        
        corr = np.corrcoef(returns_matrix.T)
        
        if n_assets == 1:
            corr = np.array([[1.0]])
        
        corr = np.nan_to_num(corr, nan=0.0)
        
        return corr, symbols
    
    def compute_beta(
        self,
        returns: Dict[str, np.ndarray]
    ) -> Dict[str, float]:
        """
        Compute beta of each asset vs benchmark
        
        Beta > 1: More volatile than market
        Beta < 1: Less volatile than market
        Beta < 0: Inverse to market
        Beta = 0: Uncorrelated (e.g., market-neutral)
        
        Returns:
            Dict mapping symbol to beta value
        """
        betas = {}
        
        if self.benchmark_symbol not in returns:
            logger.warning(f"Benchmark {self.benchmark_symbol} not in returns data")
            for symbol in returns:
                betas[symbol] = 1.0
            return betas
        
        bench_returns = returns[self.benchmark_symbol]
        bench_var = np.var(bench_returns)
        
        if bench_var == 0:
            logger.warning("Benchmark variance is zero")
            for symbol in returns:
                betas[symbol] = 1.0 if symbol != self.benchmark_symbol else 1.0
            return betas
        
        for symbol, asset_returns in returns.items():
            if symbol == self.benchmark_symbol:
                betas[symbol] = 1.0
                continue
            
            min_len = min(len(asset_returns), len(bench_returns))
            asset_r = asset_returns[-min_len:]
            bench_r = bench_returns[-min_len:]
            
            covariance = np.cov(asset_r, bench_r)[0, 1]
            beta = covariance / bench_var
            
            beta = np.clip(beta, -3.0, 3.0)
            betas[symbol] = round(float(beta), 4)
        
        return betas
    
    def compute_volatilities(
        self,
        returns: Dict[str, np.ndarray],
        annualize: bool = True
    ) -> Dict[str, float]:
        """
        Compute annualized volatility for each asset
        
        Returns:
            Dict mapping symbol to annualized volatility
        """
        volatilities = {}
        
        for symbol, rets in returns.items():
            daily_vol = np.std(rets)
            
            if annualize:
                annual_vol = daily_vol * np.sqrt(self.annualization_factor)
            else:
                annual_vol = daily_vol
            
            volatilities[symbol] = round(float(annual_vol), 4)
        
        return volatilities
    
    def compute_all_metrics(
        self,
        prices: Dict[str, List[float]],
        use_cache: bool = True
    ) -> RiskMetrics:
        """
        Compute all risk metrics in one call
        
        Args:
            prices: Dict mapping symbol to price history
            use_cache: Use cached results if available and fresh
        
        Returns:
            RiskMetrics dataclass with all computed metrics
        """
        if use_cache and self._is_cache_valid():
            logger.debug("Using cached risk metrics")
            return self._cached_metrics
        
        logger.info(f"Computing risk metrics for {len(prices)} assets")
        
        returns = self.compute_returns(prices)
        
        data_quality = self._compute_data_quality(prices, returns)
        
        cov_matrix, symbols = self.compute_covariance(returns)
        corr_matrix, _ = self.compute_correlation(returns)
        betas = self.compute_beta(returns)
        volatilities = self.compute_volatilities(returns)
        
        bench_vol = volatilities.get(self.benchmark_symbol, 0.15)
        
        metrics = RiskMetrics(
            covariance_matrix=cov_matrix,
            correlation_matrix=corr_matrix,
            betas=betas,
            volatilities=volatilities,
            benchmark_volatility=bench_vol,
            computation_date=datetime.now(),
            symbols=symbols,
            data_quality_score=data_quality
        )
        
        self._cached_metrics = metrics
        self._cache_timestamp = datetime.now()
        
        logger.info(f"Risk metrics computed | Quality: {data_quality:.1%} | Assets: {len(symbols)}")
        
        return metrics
    
    def _compute_data_quality(
        self,
        prices: Dict[str, List[float]],
        returns: Dict[str, np.ndarray]
    ) -> float:
        """Compute data quality score (0-1)"""
        if not prices:
            return 0.0
        
        total_expected = len(prices) * self.lookback_days
        total_actual = sum(len(p) for p in prices.values())
        
        completeness = min(total_actual / max(total_expected, 1), 1.0)
        
        zero_returns = 0
        total_returns = 0
        for rets in returns.values():
            zero_returns += np.sum(rets == 0)
            total_returns += len(rets)
        
        non_zero_ratio = 1 - (zero_returns / max(total_returns, 1))
        
        quality = 0.6 * completeness + 0.4 * non_zero_ratio
        
        return round(quality, 4)
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if self._cached_metrics is None or self._cache_timestamp is None:
            return False
        
        age_minutes = (datetime.now() - self._cache_timestamp).total_seconds() / 60
        return age_minutes < self._cache_ttl_minutes
    
    def get_status(self) -> Dict:
        """Get engine status for monitoring"""
        return {
            "engine": "RiskModelEngine",
            "version": self.VERSION,
            "benchmark": self.benchmark_symbol,
            "lookback_days": self.lookback_days,
            "cache_valid": self._is_cache_valid(),
            "last_computation": self._cache_timestamp.isoformat() if self._cache_timestamp else None
        }
