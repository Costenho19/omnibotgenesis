"""
OMNIX Execution Protocol INSTITUTIONAL+ - Micro Volatility Engine
==================================================================
Institutional-grade tick-by-tick volatility analysis and regime detection

Components:
- Tick-by-Tick Volatility Clustering: Buffer ticks, incremental variance, cluster detection
- Volatility Regime Detection: LOW/NORMAL/HIGH/EXTREME with transition cooldowns
- Asymmetric Volatility Response: Uptick vs downtick variance, leverage effect metrics

Author: OMNIX Team
"""

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np

from omnix_config import VERSION_BANNER

logger = logging.getLogger(__name__)


class VolatilityRegime(Enum):
    """
    Volatility regime classification based on realized volatility percentiles.
    
    Regimes:
    - LOW: Below 25th percentile of historical volatility
    - NORMAL: 25th to 75th percentile
    - HIGH: 75th to 95th percentile
    - EXTREME: Above 95th percentile (crisis/event-driven)
    """
    LOW = ("LOW", 0.0, 0.25, "Low volatility environment - Range-bound markets")
    NORMAL = ("NORMAL", 0.25, 0.75, "Normal volatility - Standard market conditions")
    HIGH = ("HIGH", 0.75, 0.95, "High volatility - Trending or uncertain markets")
    EXTREME = ("EXTREME", 0.95, 1.0, "Extreme volatility - Crisis or major event")
    
    def __init__(self, label: str, lower_pct: float, upper_pct: float, description: str):
        self.label = label
        self.lower_pct = lower_pct
        self.upper_pct = upper_pct
        self.description = description


@dataclass
class PriceTick:
    """
    Individual price tick data point.
    
    Stores price, timestamp, and computed return from previous tick
    for incremental volatility calculations.
    """
    price: float
    timestamp: datetime
    log_return: float = 0.0
    direction: str = "NEUTRAL"
    
    @classmethod
    def from_price(
        cls,
        price: float,
        timestamp: datetime,
        prev_price: Optional[float] = None
    ) -> 'PriceTick':
        """Create tick with computed log return"""
        log_return = 0.0
        direction = "NEUTRAL"
        
        if prev_price and prev_price > 0 and price > 0:
            log_return = np.log(price / prev_price)
            if log_return > 1e-8:
                direction = "UP"
            elif log_return < -1e-8:
                direction = "DOWN"
        
        return cls(
            price=price,
            timestamp=timestamp,
            log_return=log_return,
            direction=direction
        )


@dataclass
class VolatilityCluster:
    """
    Detected volatility cluster representing a period of elevated volatility.
    
    Clusters are identified when consecutive ticks exceed the volatility threshold.
    """
    start_time: datetime
    end_time: Optional[datetime]
    peak_volatility: float
    mean_volatility: float
    tick_count: int
    trigger_return: float
    is_active: bool = True
    
    @property
    def duration_seconds(self) -> float:
        """Cluster duration in seconds"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()


@dataclass
class AsymmetricMetrics:
    """
    Asymmetric volatility metrics tracking up vs down move behavior.
    
    Captures the leverage effect where negative returns typically
    lead to higher subsequent volatility than positive returns.
    """
    timestamp: datetime
    uptick_variance: float
    downtick_variance: float
    uptick_count: int
    downtick_count: int
    leverage_effect: float
    asymmetry_ratio: float
    response_half_life_seconds: float
    shock_decay_rate: float
    
    @property
    def has_leverage_effect(self) -> bool:
        """Check if significant leverage effect exists (down vol > up vol)"""
        return self.leverage_effect > 0.1
    
    @property
    def volatility_bias(self) -> str:
        """Determine direction of volatility bias"""
        if self.asymmetry_ratio > 1.2:
            return "DOWNSIDE_BIAS"
        elif self.asymmetry_ratio < 0.8:
            return "UPSIDE_BIAS"
        return "SYMMETRIC"


@dataclass
class VolatilityState:
    """
    Complete volatility state snapshot for execution decisions.
    
    Contains current regime, metrics, clustering info, and asymmetric behavior.
    """
    timestamp: datetime
    symbol: str
    regime: VolatilityRegime
    realized_volatility: float
    realized_volatility_annualized: float
    volatility_percentile: float
    current_variance: float
    tick_count: int
    window_seconds: float
    regime_duration_seconds: float
    regime_transition_cooldown: bool
    active_clusters: int
    asymmetric_metrics: Optional[AsymmetricMetrics] = None
    historical_bands: Dict[str, float] = field(default_factory=dict)
    
    @property
    def is_elevated(self) -> bool:
        """Check if volatility is elevated (HIGH or EXTREME)"""
        return self.regime in (VolatilityRegime.HIGH, VolatilityRegime.EXTREME)
    
    @property
    def execution_risk_level(self) -> str:
        """Assess execution risk based on current state"""
        if self.regime == VolatilityRegime.EXTREME:
            return "CRITICAL"
        elif self.regime == VolatilityRegime.HIGH:
            return "ELEVATED"
        elif self.active_clusters > 0:
            return "MODERATE"
        return "NORMAL"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'regime': self.regime.label,
            'regime_description': self.regime.description,
            'realized_volatility': round(self.realized_volatility, 6),
            'realized_volatility_annualized': round(self.realized_volatility_annualized, 4),
            'volatility_percentile': round(self.volatility_percentile, 4),
            'current_variance': round(self.current_variance, 10),
            'tick_count': self.tick_count,
            'window_seconds': round(self.window_seconds, 2),
            'regime_duration_seconds': round(self.regime_duration_seconds, 2),
            'regime_transition_cooldown': self.regime_transition_cooldown,
            'active_clusters': self.active_clusters,
            'is_elevated': self.is_elevated,
            'execution_risk_level': self.execution_risk_level,
            'historical_bands': self.historical_bands,
            'asymmetric_metrics': {
                'uptick_variance': round(self.asymmetric_metrics.uptick_variance, 10),
                'downtick_variance': round(self.asymmetric_metrics.downtick_variance, 10),
                'leverage_effect': round(self.asymmetric_metrics.leverage_effect, 4),
                'asymmetry_ratio': round(self.asymmetric_metrics.asymmetry_ratio, 4),
                'response_half_life_seconds': round(self.asymmetric_metrics.response_half_life_seconds, 2),
                'volatility_bias': self.asymmetric_metrics.volatility_bias
            } if self.asymmetric_metrics else None
        }


class MicroVolatilityEngine:
    """
    OMNIX Micro Volatility Engine - Institutional Grade
    
    Provides tick-by-tick volatility analysis including:
    - Incremental variance calculation with Welford's algorithm
    - Volatility clustering detection with threshold-based grouping
    - Regime classification (LOW/NORMAL/HIGH/EXTREME)
    - Asymmetric volatility response (leverage effect)
    - Response half-life calculation for shock decay
    
    Thread-safe implementation with configurable rolling windows.
    
    Usage:
        engine = MicroVolatilityEngine(window_ticks=100, window_seconds=300)
        engine.update(price=50000.0, timestamp=datetime.now(), symbol='BTC/USD')
        state = engine.get_volatility_state('BTC/USD')
    """
    
    DEFAULT_PERCENTILES = {
        'p10': 10,
        'p25': 25,
        'p50': 50,
        'p75': 75,
        'p90': 90,
        'p95': 95,
        'p99': 99
    }
    
    ANNUALIZATION_FACTOR = np.sqrt(365.25 * 24 * 60 * 60)
    
    def __init__(
        self,
        window_ticks: int = 100,
        window_seconds: float = 300.0,
        cluster_threshold_sigma: float = 2.0,
        regime_cooldown_seconds: float = 60.0,
        min_ticks_for_regime: int = 20,
        historical_window_hours: int = 24
    ):
        """
        Initialize MicroVolatilityEngine.
        
        Args:
            window_ticks: Maximum ticks to retain (default 100)
            window_seconds: Time-based window in seconds (default 300 = 5 min)
            cluster_threshold_sigma: Sigma threshold for cluster detection (default 2.0)
            regime_cooldown_seconds: Minimum time between regime transitions (default 60)
            min_ticks_for_regime: Minimum ticks needed for regime classification (default 20)
            historical_window_hours: Hours of history for percentile bands (default 24)
        """
        self.window_ticks = window_ticks
        self.window_seconds = window_seconds
        self.cluster_threshold_sigma = cluster_threshold_sigma
        self.regime_cooldown_seconds = regime_cooldown_seconds
        self.min_ticks_for_regime = min_ticks_for_regime
        self.historical_window_hours = historical_window_hours
        
        self._lock = threading.RLock()
        
        self._ticks: Dict[str, Deque[PriceTick]] = {}
        self._historical_volatility: Dict[str, Deque[float]] = {}
        self._clusters: Dict[str, List[VolatilityCluster]] = {}
        self._current_regime: Dict[str, VolatilityRegime] = {}
        self._regime_start_time: Dict[str, datetime] = {}
        self._last_regime_change: Dict[str, datetime] = {}
        
        self._welford_state: Dict[str, Dict[str, float]] = {}
        self._uptick_welford: Dict[str, Dict[str, float]] = {}
        self._downtick_welford: Dict[str, Dict[str, float]] = {}
        
        self._shock_timestamps: Dict[str, Deque[Tuple[datetime, float]]] = {}
        
        logger.info(f"MicroVolatilityEngine {VERSION_BANNER} initialized")
        logger.info(f"Window: {window_ticks} ticks / {window_seconds}s, Cluster threshold: {cluster_threshold_sigma}σ")
        logger.info(f"Regime cooldown: {regime_cooldown_seconds}s, Historical window: {historical_window_hours}h")
    
    def _init_symbol(self, symbol: str) -> None:
        """Initialize data structures for a new symbol"""
        if symbol not in self._ticks:
            self._ticks[symbol] = deque(maxlen=self.window_ticks)
            self._historical_volatility[symbol] = deque(maxlen=10000)
            self._clusters[symbol] = []
            self._current_regime[symbol] = VolatilityRegime.NORMAL
            self._regime_start_time[symbol] = datetime.now()
            self._last_regime_change[symbol] = datetime.now() - timedelta(seconds=self.regime_cooldown_seconds + 1)
            self._welford_state[symbol] = {'n': 0, 'mean': 0.0, 'M2': 0.0}
            self._uptick_welford[symbol] = {'n': 0, 'mean': 0.0, 'M2': 0.0}
            self._downtick_welford[symbol] = {'n': 0, 'mean': 0.0, 'M2': 0.0}
            self._shock_timestamps[symbol] = deque(maxlen=100)
    
    def _welford_update(
        self,
        state: Dict[str, float],
        value: float
    ) -> Dict[str, float]:
        """
        Welford's online algorithm for incremental variance calculation.
        
        Numerically stable single-pass algorithm for computing
        running mean and variance.
        
        Args:
            state: Current Welford state {n, mean, M2}
            value: New value to incorporate
            
        Returns:
            Updated state
        """
        n = state['n'] + 1
        delta = value - state['mean']
        mean = state['mean'] + delta / n
        delta2 = value - mean
        M2 = state['M2'] + delta * delta2
        
        return {'n': n, 'mean': mean, 'M2': M2}
    
    def _welford_variance(self, state: Dict[str, float]) -> float:
        """Extract variance from Welford state"""
        if state['n'] < 2:
            return 0.0
        return state['M2'] / (state['n'] - 1)
    
    def _prune_old_ticks(self, symbol: str) -> None:
        """Remove ticks outside the time window"""
        cutoff = datetime.now() - timedelta(seconds=self.window_seconds)
        
        while self._ticks[symbol] and self._ticks[symbol][0].timestamp < cutoff:
            self._ticks[symbol].popleft()
    
    def _recalculate_welford(self, symbol: str) -> None:
        """Recalculate Welford state from current ticks (after pruning)"""
        self._welford_state[symbol] = {'n': 0, 'mean': 0.0, 'M2': 0.0}
        self._uptick_welford[symbol] = {'n': 0, 'mean': 0.0, 'M2': 0.0}
        self._downtick_welford[symbol] = {'n': 0, 'mean': 0.0, 'M2': 0.0}
        
        for tick in self._ticks[symbol]:
            if tick.log_return != 0:
                self._welford_state[symbol] = self._welford_update(
                    self._welford_state[symbol],
                    tick.log_return ** 2
                )
                
                if tick.direction == "UP":
                    self._uptick_welford[symbol] = self._welford_update(
                        self._uptick_welford[symbol],
                        tick.log_return ** 2
                    )
                elif tick.direction == "DOWN":
                    self._downtick_welford[symbol] = self._welford_update(
                        self._downtick_welford[symbol],
                        tick.log_return ** 2
                    )
    
    def _detect_cluster(
        self,
        symbol: str,
        current_return: float,
        current_variance: float
    ) -> None:
        """
        Detect and manage volatility clusters.
        
        A cluster starts when |return| exceeds threshold * sqrt(variance)
        and ends when returns normalize.
        """
        if current_variance <= 0:
            return
        
        std_dev = np.sqrt(current_variance)
        threshold = self.cluster_threshold_sigma * std_dev
        is_extreme = abs(current_return) > threshold
        
        active_cluster = None
        for cluster in self._clusters[symbol]:
            if cluster.is_active:
                active_cluster = cluster
                break
        
        now = datetime.now()
        
        if is_extreme:
            if active_cluster:
                active_cluster.tick_count += 1
                active_cluster.peak_volatility = max(
                    active_cluster.peak_volatility,
                    abs(current_return)
                )
                active_cluster.mean_volatility = (
                    (active_cluster.mean_volatility * (active_cluster.tick_count - 1) + 
                     abs(current_return)) / active_cluster.tick_count
                )
            else:
                new_cluster = VolatilityCluster(
                    start_time=now,
                    end_time=None,
                    peak_volatility=abs(current_return),
                    mean_volatility=abs(current_return),
                    tick_count=1,
                    trigger_return=current_return,
                    is_active=True
                )
                self._clusters[symbol].append(new_cluster)
                logger.debug(f"[{symbol}] Volatility cluster started: |return|={abs(current_return):.6f} > threshold={threshold:.6f}")
        else:
            if active_cluster:
                active_cluster.is_active = False
                active_cluster.end_time = now
                logger.debug(f"[{symbol}] Volatility cluster ended: duration={active_cluster.duration_seconds:.1f}s, peak={active_cluster.peak_volatility:.6f}")
        
        max_clusters = 50
        if len(self._clusters[symbol]) > max_clusters:
            self._clusters[symbol] = [c for c in self._clusters[symbol] if c.is_active][-max_clusters:]
    
    def _calculate_percentile_bands(self, symbol: str) -> Dict[str, float]:
        """
        Calculate historical volatility percentile bands.
        
        Uses stored historical volatility samples to compute
        percentile thresholds for regime classification.
        """
        hist_vol = list(self._historical_volatility[symbol])
        
        if len(hist_vol) < 10:
            return {
                'p10': 0.0001,
                'p25': 0.0002,
                'p50': 0.0005,
                'p75': 0.001,
                'p90': 0.002,
                'p95': 0.003,
                'p99': 0.005
            }
        
        arr = np.array(hist_vol)
        return {
            name: float(np.percentile(arr, pct))
            for name, pct in self.DEFAULT_PERCENTILES.items()
        }
    
    def _classify_regime(
        self,
        symbol: str,
        current_volatility: float,
        bands: Dict[str, float]
    ) -> VolatilityRegime:
        """
        Classify current volatility into a regime.
        
        Uses percentile bands to determine regime with cooldown
        to prevent rapid oscillation.
        """
        now = datetime.now()
        time_since_change = (now - self._last_regime_change[symbol]).total_seconds()
        in_cooldown = time_since_change < self.regime_cooldown_seconds
        
        if current_volatility <= bands['p25']:
            new_regime = VolatilityRegime.LOW
        elif current_volatility <= bands['p75']:
            new_regime = VolatilityRegime.NORMAL
        elif current_volatility <= bands['p95']:
            new_regime = VolatilityRegime.HIGH
        else:
            new_regime = VolatilityRegime.EXTREME
        
        current_regime = self._current_regime[symbol]
        
        if new_regime != current_regime:
            if in_cooldown:
                current_order = [VolatilityRegime.LOW, VolatilityRegime.NORMAL, 
                                VolatilityRegime.HIGH, VolatilityRegime.EXTREME]
                new_idx = current_order.index(new_regime)
                cur_idx = current_order.index(current_regime)
                
                if abs(new_idx - cur_idx) <= 1:
                    return current_regime
            
            logger.info(f"[{symbol}] Regime transition: {current_regime.label} -> {new_regime.label}")
            self._current_regime[symbol] = new_regime
            self._regime_start_time[symbol] = now
            self._last_regime_change[symbol] = now
        
        return self._current_regime[symbol]
    
    def _calculate_volatility_percentile(
        self,
        symbol: str,
        current_volatility: float
    ) -> float:
        """Calculate where current volatility sits in historical distribution"""
        hist_vol = list(self._historical_volatility[symbol])
        
        if len(hist_vol) < 10:
            return 0.5
        
        arr = np.array(hist_vol)
        percentile = np.searchsorted(np.sort(arr), current_volatility) / len(arr)
        return float(np.clip(percentile, 0.0, 1.0))
    
    def _calculate_asymmetric_metrics(self, symbol: str) -> AsymmetricMetrics:
        """
        Calculate asymmetric volatility metrics.
        
        Computes uptick vs downtick variance, leverage effect,
        and response half-life for volatility shocks.
        """
        uptick_var = self._welford_variance(self._uptick_welford[symbol])
        downtick_var = self._welford_variance(self._downtick_welford[symbol])
        uptick_n = int(self._uptick_welford[symbol]['n'])
        downtick_n = int(self._downtick_welford[symbol]['n'])
        
        if uptick_var > 0:
            asymmetry_ratio = downtick_var / uptick_var
        else:
            asymmetry_ratio = 1.0 if downtick_var == 0 else 2.0
        
        total_var = uptick_var + downtick_var
        if total_var > 0:
            leverage_effect = (downtick_var - uptick_var) / total_var
        else:
            leverage_effect = 0.0
        
        half_life = self._calculate_shock_half_life(symbol)
        decay_rate = np.log(2) / half_life if half_life > 0 else 0.0
        
        return AsymmetricMetrics(
            timestamp=datetime.now(),
            uptick_variance=uptick_var,
            downtick_variance=downtick_var,
            uptick_count=uptick_n,
            downtick_count=downtick_n,
            leverage_effect=leverage_effect,
            asymmetry_ratio=asymmetry_ratio,
            response_half_life_seconds=half_life,
            shock_decay_rate=decay_rate
        )
    
    def _calculate_shock_half_life(self, symbol: str) -> float:
        """
        Calculate half-life of volatility shocks.
        
        Measures how quickly elevated volatility returns to normal
        after a shock event. Uses exponential decay fitting.
        """
        shocks = list(self._shock_timestamps[symbol])
        
        if len(shocks) < 3:
            return 30.0
        
        now = datetime.now()
        recent_shocks = [
            (ts, mag) for ts, mag in shocks
            if (now - ts).total_seconds() < 3600
        ]
        
        if len(recent_shocks) < 2:
            return 30.0
        
        times = np.array([(now - ts).total_seconds() for ts, _ in recent_shocks])
        magnitudes = np.array([mag for _, mag in recent_shocks])
        
        if np.std(magnitudes) < 1e-10:
            return 30.0
        
        try:
            sorted_idx = np.argsort(times)
            times = times[sorted_idx]
            magnitudes = magnitudes[sorted_idx]
            
            log_mag = np.log(magnitudes + 1e-10)
            
            if len(times) >= 2 and np.std(times) > 0:
                slope = np.polyfit(times, log_mag, 1)[0]
                if slope < 0:
                    half_life = -np.log(2) / slope
                    return float(np.clip(half_life, 1.0, 3600.0))
        except Exception:
            pass
        
        return 30.0
    
    def update(
        self,
        price: float,
        timestamp: Optional[datetime] = None,
        symbol: str = "BTC/USD"
    ) -> None:
        """
        Update volatility engine with new price tick.
        
        Performs incremental variance update, cluster detection,
        and regime classification.
        
        Args:
            price: Current price
            timestamp: Tick timestamp (defaults to now)
            symbol: Trading pair symbol
        """
        if price <= 0:
            logger.warning(f"Invalid price {price} for {symbol}")
            return
        
        ts = timestamp or datetime.now()
        
        with self._lock:
            self._init_symbol(symbol)
            
            prev_price = None
            if self._ticks[symbol]:
                prev_price = self._ticks[symbol][-1].price
            
            tick = PriceTick.from_price(price, ts, prev_price)
            
            old_count = len(self._ticks[symbol])
            self._ticks[symbol].append(tick)
            self._prune_old_ticks(symbol)
            
            if len(self._ticks[symbol]) < old_count:
                self._recalculate_welford(symbol)
            elif tick.log_return != 0:
                self._welford_state[symbol] = self._welford_update(
                    self._welford_state[symbol],
                    tick.log_return ** 2
                )
                
                if tick.direction == "UP":
                    self._uptick_welford[symbol] = self._welford_update(
                        self._uptick_welford[symbol],
                        tick.log_return ** 2
                    )
                elif tick.direction == "DOWN":
                    self._downtick_welford[symbol] = self._welford_update(
                        self._downtick_welford[symbol],
                        tick.log_return ** 2
                    )
            
            current_var = self._welford_variance(self._welford_state[symbol])
            current_vol = np.sqrt(current_var) if current_var > 0 else 0.0
            
            if current_vol > 0:
                self._historical_volatility[symbol].append(current_vol)
            
            if tick.log_return != 0:
                self._detect_cluster(symbol, tick.log_return, current_var)
            
            bands = self._calculate_percentile_bands(symbol)
            std_dev = np.sqrt(current_var) if current_var > 0 else 0.0
            
            if std_dev > 0 and abs(tick.log_return) > 2 * std_dev:
                self._shock_timestamps[symbol].append((ts, abs(tick.log_return)))
            
            if len(self._ticks[symbol]) >= self.min_ticks_for_regime:
                self._classify_regime(symbol, current_vol, bands)
    
    def get_volatility_state(self, symbol: str = "BTC/USD") -> Optional[VolatilityState]:
        """
        Get current volatility state for a symbol.
        
        Returns comprehensive volatility metrics including regime,
        variance, clustering info, and asymmetric behavior.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            VolatilityState or None if insufficient data
        """
        with self._lock:
            if symbol not in self._ticks:
                self._init_symbol(symbol)
                return None
            
            ticks = self._ticks[symbol]
            if len(ticks) < 2:
                return None
            
            current_var = self._welford_variance(self._welford_state[symbol])
            current_vol = np.sqrt(current_var) if current_var > 0 else 0.0
            
            time_span = (ticks[-1].timestamp - ticks[0].timestamp).total_seconds()
            if time_span > 0:
                annualized_vol = current_vol * np.sqrt(self.ANNUALIZATION_FACTOR / time_span)
            else:
                annualized_vol = 0.0
            
            bands = self._calculate_percentile_bands(symbol)
            percentile = self._calculate_volatility_percentile(symbol, current_vol)
            
            regime = self._current_regime.get(symbol, VolatilityRegime.NORMAL)
            regime_duration = (datetime.now() - self._regime_start_time.get(symbol, datetime.now())).total_seconds()
            time_since_change = (datetime.now() - self._last_regime_change.get(symbol, datetime.now())).total_seconds()
            in_cooldown = time_since_change < self.regime_cooldown_seconds
            
            active_clusters = sum(1 for c in self._clusters.get(symbol, []) if c.is_active)
            
            asymmetric = self._calculate_asymmetric_metrics(symbol)
            
            return VolatilityState(
                timestamp=datetime.now(),
                symbol=symbol,
                regime=regime,
                realized_volatility=current_vol,
                realized_volatility_annualized=annualized_vol,
                volatility_percentile=percentile,
                current_variance=current_var,
                tick_count=len(ticks),
                window_seconds=time_span,
                regime_duration_seconds=regime_duration,
                regime_transition_cooldown=in_cooldown,
                active_clusters=active_clusters,
                asymmetric_metrics=asymmetric,
                historical_bands=bands
            )
    
    def get_state(self, symbol: str = "BTC/USD") -> Optional[VolatilityState]:
        """
        Alias for get_volatility_state for API consistency.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            VolatilityState or None
        """
        return self.get_volatility_state(symbol)
    
    def get_active_clusters(self, symbol: str = "BTC/USD") -> List[VolatilityCluster]:
        """
        Get currently active volatility clusters.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            List of active VolatilityCluster objects
        """
        with self._lock:
            if symbol not in self._clusters:
                return []
            return [c for c in self._clusters[symbol] if c.is_active]
    
    def get_recent_clusters(
        self,
        symbol: str = "BTC/USD",
        max_age_seconds: float = 3600.0
    ) -> List[VolatilityCluster]:
        """
        Get recent volatility clusters (active or closed).
        
        Args:
            symbol: Trading pair symbol
            max_age_seconds: Maximum cluster age to include
            
        Returns:
            List of recent VolatilityCluster objects
        """
        with self._lock:
            if symbol not in self._clusters:
                return []
            
            cutoff = datetime.now() - timedelta(seconds=max_age_seconds)
            return [
                c for c in self._clusters[symbol]
                if c.start_time >= cutoff
            ]
    
    def reset(self, symbol: Optional[str] = None) -> None:
        """
        Reset volatility engine state.
        
        Args:
            symbol: Specific symbol to reset, or None for all
        """
        with self._lock:
            if symbol:
                if symbol in self._ticks:
                    self._ticks[symbol].clear()
                    self._historical_volatility[symbol].clear()
                    self._clusters[symbol] = []
                    self._current_regime[symbol] = VolatilityRegime.NORMAL
                    self._regime_start_time[symbol] = datetime.now()
                    self._last_regime_change[symbol] = datetime.now()
                    self._welford_state[symbol] = {'n': 0, 'mean': 0.0, 'M2': 0.0}
                    self._uptick_welford[symbol] = {'n': 0, 'mean': 0.0, 'M2': 0.0}
                    self._downtick_welford[symbol] = {'n': 0, 'mean': 0.0, 'M2': 0.0}
                    self._shock_timestamps[symbol].clear()
                logger.info(f"Reset volatility state for {symbol}")
            else:
                self._ticks.clear()
                self._historical_volatility.clear()
                self._clusters.clear()
                self._current_regime.clear()
                self._regime_start_time.clear()
                self._last_regime_change.clear()
                self._welford_state.clear()
                self._uptick_welford.clear()
                self._downtick_welford.clear()
                self._shock_timestamps.clear()
                logger.info("Reset all volatility state")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all tracked symbols.
        
        Returns:
            Dictionary with symbol summaries and engine stats
        """
        with self._lock:
            summaries = {}
            
            for symbol in self._ticks.keys():
                state = self.get_volatility_state(symbol)
                if state:
                    summaries[symbol] = {
                        'regime': state.regime.label,
                        'volatility': state.realized_volatility,
                        'percentile': state.volatility_percentile,
                        'tick_count': state.tick_count,
                        'active_clusters': state.active_clusters,
                        'risk_level': state.execution_risk_level
                    }
            
            return {
                'version': VERSION_BANNER,
                'symbols_tracked': len(self._ticks),
                'config': {
                    'window_ticks': self.window_ticks,
                    'window_seconds': self.window_seconds,
                    'cluster_threshold_sigma': self.cluster_threshold_sigma,
                    'regime_cooldown_seconds': self.regime_cooldown_seconds
                },
                'symbols': summaries
            }
