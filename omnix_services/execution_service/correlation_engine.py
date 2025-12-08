"""
OMNIX Execution Protocol INSTITUTIONAL+ - Cross-Asset Correlation Engine
=========================================================================
Institutional-grade cross-asset correlation analysis for systemic risk detection

Components:
- Rolling Correlation Matrix: Pearson & Spearman correlations with configurable windows
- Correlation Breakdown Detection: Z-score divergence with severity scoring
- Contagion Risk Index: Weighted breakdown severity and volume spillover
- Safe-Haven Flow Analysis: Flight-to-quality and BTC dominance tracking

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
from scipy import stats

from omnix_config import VERSION_BANNER

logger = logging.getLogger(__name__)


class BreakdownSeverity(Enum):
    """
    Correlation breakdown severity classification.
    
    Levels:
    - MINOR: Small deviation, within 1-2 sigma
    - MODERATE: Notable deviation, 2-3 sigma
    - SEVERE: Significant breakdown, 3-4 sigma
    - CRITICAL: Extreme breakdown, >4 sigma (regime shift likely)
    """
    MINOR = ("MINOR", 0, 30, "Minor correlation shift - Monitor")
    MODERATE = ("MODERATE", 30, 50, "Moderate breakdown - Adjust exposure")
    SEVERE = ("SEVERE", 50, 70, "Severe breakdown - Reduce positions")
    CRITICAL = ("CRITICAL", 70, 100, "Critical breakdown - Hedge immediately")
    
    def __init__(self, label: str, lower: int, upper: int, description: str):
        self.label = label
        self.lower = lower
        self.upper = upper
        self.description = description


class ContagionLevel(Enum):
    """
    Contagion risk level classification.
    
    Levels based on aggregate breakdown severity and volume spillover.
    """
    LOW = ("LOW", 0, 30, "Low contagion risk - Normal conditions")
    ELEVATED = ("ELEVATED", 30, 50, "Elevated risk - Increased monitoring")
    HIGH = ("HIGH", 50, 70, "High contagion risk - Defensive positioning")
    EXTREME = ("EXTREME", 70, 100, "Extreme contagion - Crisis mode")
    
    def __init__(self, label: str, lower: int, upper: int, description: str):
        self.label = label
        self.lower = lower
        self.upper = upper
        self.description = description


class FlowDirection(Enum):
    """Safe-haven flow direction classification"""
    RISK_ON = ("RISK_ON", "Capital flowing into risk assets")
    NEUTRAL = ("NEUTRAL", "No significant flow direction")
    RISK_OFF = ("RISK_OFF", "Capital flowing to safe havens")
    FLIGHT_TO_QUALITY = ("FLIGHT_TO_QUALITY", "Extreme flight to safety")
    
    def __init__(self, label: str, description: str):
        self.label = label
        self.description = description


@dataclass
class PriceUpdate:
    """
    Price update for a single asset.
    
    Stores price, volume, and timestamp for correlation tracking.
    """
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    log_return: float = 0.0
    
    @classmethod
    def from_price(
        cls,
        symbol: str,
        price: float,
        volume: float,
        timestamp: datetime,
        prev_price: Optional[float] = None
    ) -> 'PriceUpdate':
        """Create update with computed log return"""
        log_return = 0.0
        if prev_price and prev_price > 0 and price > 0:
            log_return = np.log(price / prev_price)
        
        return cls(
            symbol=symbol,
            price=price,
            volume=volume,
            timestamp=timestamp,
            log_return=log_return
        )


@dataclass
class CorrelationPair:
    """
    Correlation metrics for a single asset pair.
    
    Contains Pearson and Spearman correlations with historical context.
    """
    asset_a: str
    asset_b: str
    pearson_correlation: float
    spearman_correlation: float
    sample_count: int
    historical_mean: float
    historical_std: float
    z_score: float
    last_updated: datetime
    
    @property
    def pair_key(self) -> str:
        """Canonical pair identifier (alphabetically sorted)"""
        return f"{min(self.asset_a, self.asset_b)}/{max(self.asset_a, self.asset_b)}"
    
    @property
    def is_stable(self) -> bool:
        """Check if correlation is within 2 sigma of historical mean"""
        return abs(self.z_score) <= 2.0
    
    @property
    def deviation_pct(self) -> float:
        """Percentage deviation from historical mean"""
        if self.historical_std == 0:
            return 0.0
        return abs(self.pearson_correlation - self.historical_mean) / (self.historical_std + 1e-10) * 100


@dataclass
class CorrelationBreakdown:
    """
    Detected correlation breakdown event.
    
    Represents significant deviation from historical correlation norms
    with severity scoring and actionable insights.
    """
    pair_key: str
    asset_a: str
    asset_b: str
    current_correlation: float
    historical_mean: float
    historical_std: float
    z_score: float
    severity: BreakdownSeverity
    severity_score: float
    direction: str
    start_time: datetime
    duration_seconds: float
    is_active: bool = True
    
    @property
    def is_significant(self) -> bool:
        """Check if breakdown requires action"""
        return self.severity_score >= 30.0


@dataclass
class ContagionRisk:
    """
    Aggregate contagion risk assessment.
    
    Combines breakdown severity, volume spillover, and cross-asset
    dynamics to produce systemic risk score.
    """
    timestamp: datetime
    risk_score: float
    level: ContagionLevel
    active_breakdowns: int
    weighted_severity: float
    volume_spillover_score: float
    cross_correlation_stress: float
    affected_pairs: List[str]
    primary_driver: Optional[str]
    recommendation: str
    
    @property
    def is_elevated(self) -> bool:
        """Check if risk level requires action"""
        return self.risk_score >= 50.0
    
    @property
    def is_critical(self) -> bool:
        """Check if risk is at critical levels"""
        return self.risk_score >= 70.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'risk_score': round(self.risk_score, 2),
            'level': self.level.label,
            'level_description': self.level.description,
            'active_breakdowns': self.active_breakdowns,
            'weighted_severity': round(self.weighted_severity, 2),
            'volume_spillover_score': round(self.volume_spillover_score, 2),
            'cross_correlation_stress': round(self.cross_correlation_stress, 4),
            'affected_pairs': self.affected_pairs,
            'primary_driver': self.primary_driver,
            'recommendation': self.recommendation,
            'is_elevated': self.is_elevated,
            'is_critical': self.is_critical
        }


@dataclass
class SafeHavenFlow:
    """
    Safe-haven flow analysis for flight-to-quality detection.
    
    Tracks capital movement from risk assets to safe havens (stablecoins, BTC).
    """
    timestamp: datetime
    flow_direction: FlowDirection
    flow_intensity: float
    btc_dominance_delta: float
    stablecoin_inflow_ratio: float
    risk_asset_outflow_ratio: float
    flight_to_quality_score: float
    alt_to_btc_flow: float
    indicators: Dict[str, float] = field(default_factory=dict)
    
    @property
    def is_risk_off(self) -> bool:
        """Check if market is in risk-off mode"""
        return self.flow_direction in (FlowDirection.RISK_OFF, FlowDirection.FLIGHT_TO_QUALITY)
    
    @property
    def severity(self) -> str:
        """Assess flow severity"""
        if self.flight_to_quality_score >= 70:
            return "EXTREME"
        elif self.flight_to_quality_score >= 50:
            return "HIGH"
        elif self.flight_to_quality_score >= 30:
            return "MODERATE"
        return "LOW"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'flow_direction': self.flow_direction.label,
            'flow_description': self.flow_direction.description,
            'flow_intensity': round(self.flow_intensity, 4),
            'btc_dominance_delta': round(self.btc_dominance_delta, 4),
            'stablecoin_inflow_ratio': round(self.stablecoin_inflow_ratio, 4),
            'risk_asset_outflow_ratio': round(self.risk_asset_outflow_ratio, 4),
            'flight_to_quality_score': round(self.flight_to_quality_score, 2),
            'alt_to_btc_flow': round(self.alt_to_btc_flow, 4),
            'is_risk_off': self.is_risk_off,
            'severity': self.severity,
            'indicators': {k: round(v, 4) for k, v in self.indicators.items()}
        }


@dataclass
class CorrelationState:
    """
    Complete correlation engine state snapshot.
    
    Contains correlation matrix, breakdown detection, contagion risk,
    and safe-haven flow analysis for execution decisions.
    """
    timestamp: datetime
    correlation_matrix: Dict[str, Dict[str, float]]
    spearman_matrix: Dict[str, Dict[str, float]]
    pair_metrics: Dict[str, CorrelationPair]
    active_breakdowns: List[CorrelationBreakdown]
    contagion_risk: ContagionRisk
    safe_haven_flow: SafeHavenFlow
    sample_count: int
    tracked_assets: List[str]
    window_samples: int
    
    @property
    def is_stable(self) -> bool:
        """Check if overall correlation structure is stable"""
        return len(self.active_breakdowns) == 0 and self.contagion_risk.risk_score < 30
    
    @property
    def execution_risk_level(self) -> str:
        """Assess execution risk based on correlation state"""
        if self.contagion_risk.is_critical:
            return "CRITICAL"
        elif self.contagion_risk.is_elevated:
            return "ELEVATED"
        elif len(self.active_breakdowns) > 2:
            return "MODERATE"
        return "NORMAL"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'correlation_matrix': self.correlation_matrix,
            'spearman_matrix': self.spearman_matrix,
            'pair_metrics': {
                k: {
                    'pearson': v.pearson_correlation,
                    'spearman': v.spearman_correlation,
                    'z_score': v.z_score,
                    'sample_count': v.sample_count
                } for k, v in self.pair_metrics.items()
            },
            'active_breakdowns': [
                {
                    'pair': b.pair_key,
                    'severity': b.severity.label,
                    'severity_score': b.severity_score,
                    'z_score': b.z_score,
                    'duration_seconds': b.duration_seconds
                } for b in self.active_breakdowns
            ],
            'contagion_risk': self.contagion_risk.to_dict(),
            'safe_haven_flow': self.safe_haven_flow.to_dict(),
            'sample_count': self.sample_count,
            'tracked_assets': self.tracked_assets,
            'window_samples': self.window_samples,
            'is_stable': self.is_stable,
            'execution_risk_level': self.execution_risk_level
        }


class CrossAssetCorrelationEngine:
    """
    OMNIX Cross-Asset Correlation Engine - Institutional Grade
    
    Provides comprehensive cross-asset correlation analysis including:
    - Rolling Pearson and Spearman correlation matrices
    - Correlation breakdown detection with z-score divergence
    - Contagion risk index with volume spillover
    - Safe-haven flow analysis for flight-to-quality detection
    
    Thread-safe implementation with configurable rolling windows.
    
    Usage:
        engine = CrossAssetCorrelationEngine(window_samples=100)
        engine.update({
            'BTC': {'price': 50000.0, 'volume': 1000.0},
            'ETH': {'price': 3000.0, 'volume': 5000.0}
        })
        state = engine.get_correlation_state()
        breakdowns = engine.detect_breakdown()
    """
    
    DEFAULT_ASSETS = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'AVAX', 'DOT', 'LINK', 'MATIC']
    STABLECOINS = ['USDT', 'USDC', 'BUSD', 'DAI', 'TUSD']
    
    BREAKDOWN_THRESHOLDS = {
        'minor': 2.0,
        'moderate': 3.0,
        'severe': 4.0,
        'critical': 5.0
    }
    
    PAIR_WEIGHTS = {
        'BTC/ETH': 1.5,
        'BTC/SOL': 1.2,
        'ETH/SOL': 1.2,
        'BTC/BNB': 1.0,
        'ETH/BNB': 1.0
    }
    
    def __init__(
        self,
        window_samples: int = 100,
        history_samples: int = 1000,
        breakdown_cooldown_seconds: float = 300.0,
        min_samples_for_correlation: int = 20,
        tracked_assets: Optional[List[str]] = None
    ):
        """
        Initialize CrossAssetCorrelationEngine.
        
        Args:
            window_samples: Rolling window size for correlations (default 100)
            history_samples: Historical samples for z-score calculation (default 1000)
            breakdown_cooldown_seconds: Cooldown between breakdown alerts (default 300)
            min_samples_for_correlation: Minimum samples needed (default 20)
            tracked_assets: List of assets to track (default: major cryptos)
        """
        self.window_samples = window_samples
        self.history_samples = history_samples
        self.breakdown_cooldown_seconds = breakdown_cooldown_seconds
        self.min_samples_for_correlation = min_samples_for_correlation
        self.tracked_assets = tracked_assets or self.DEFAULT_ASSETS.copy()
        
        self._lock = threading.RLock()
        
        self._price_history: Dict[str, Deque[PriceUpdate]] = {}
        self._return_history: Dict[str, Deque[float]] = {}
        self._volume_history: Dict[str, Deque[float]] = {}
        
        self._correlation_history: Dict[str, Deque[float]] = {}
        
        self._active_breakdowns: Dict[str, CorrelationBreakdown] = {}
        self._breakdown_timestamps: Dict[str, datetime] = {}
        
        self._last_prices: Dict[str, float] = {}
        self._last_volumes: Dict[str, float] = {}
        self._total_market_volume: Deque[float] = deque(maxlen=history_samples)
        
        self._btc_dominance_history: Deque[float] = deque(maxlen=history_samples)
        self._stablecoin_volume_history: Deque[float] = deque(maxlen=history_samples)
        
        self._init_data_structures()
        
        logger.info(f"CrossAssetCorrelationEngine {VERSION_BANNER} initialized")
        logger.info(f"Window: {window_samples} samples, History: {history_samples} samples")
        logger.info(f"Tracking {len(self.tracked_assets)} assets: {self.tracked_assets[:5]}...")
    
    def _init_data_structures(self) -> None:
        """Initialize data structures for all tracked assets"""
        for asset in self.tracked_assets:
            self._price_history[asset] = deque(maxlen=self.window_samples)
            self._return_history[asset] = deque(maxlen=self.window_samples)
            self._volume_history[asset] = deque(maxlen=self.window_samples)
        
        for i, asset_a in enumerate(self.tracked_assets):
            for asset_b in self.tracked_assets[i + 1:]:
                pair_key = self._get_pair_key(asset_a, asset_b)
                self._correlation_history[pair_key] = deque(maxlen=self.history_samples)
    
    def _get_pair_key(self, asset_a: str, asset_b: str) -> str:
        """Generate canonical pair key (alphabetically sorted)"""
        return f"{min(asset_a, asset_b)}/{max(asset_a, asset_b)}"
    
    def add_asset(self, symbol: str) -> None:
        """
        Add a new asset to track.
        
        Args:
            symbol: Asset symbol (e.g., 'BTC', 'ETH')
        """
        with self._lock:
            if symbol not in self.tracked_assets:
                self.tracked_assets.append(symbol)
                self._price_history[symbol] = deque(maxlen=self.window_samples)
                self._return_history[symbol] = deque(maxlen=self.window_samples)
                self._volume_history[symbol] = deque(maxlen=self.window_samples)
                
                for existing_asset in self.tracked_assets[:-1]:
                    pair_key = self._get_pair_key(symbol, existing_asset)
                    self._correlation_history[pair_key] = deque(maxlen=self.history_samples)
                
                logger.info(f"Added asset {symbol} to correlation tracking")
    
    def update(
        self,
        price_data: Dict[str, Dict[str, float]],
        timestamp: Optional[datetime] = None
    ) -> None:
        """
        Update engine with new price data for multiple assets.
        
        Args:
            price_data: Dict mapping symbol to {'price': float, 'volume': float}
            timestamp: Update timestamp (defaults to now)
            
        Example:
            engine.update({
                'BTC': {'price': 50000.0, 'volume': 1000.0},
                'ETH': {'price': 3000.0, 'volume': 5000.0},
                'SOL': {'price': 100.0, 'volume': 10000.0}
            })
        """
        ts = timestamp or datetime.now()
        
        with self._lock:
            total_volume = 0.0
            stablecoin_volume = 0.0
            btc_market_cap = 0.0
            total_market_cap = 0.0
            
            for symbol, data in price_data.items():
                if symbol not in self.tracked_assets:
                    self.add_asset(symbol)
                
                price = data.get('price', 0.0)
                volume = data.get('volume', 0.0)
                
                if price <= 0:
                    continue
                
                prev_price = self._last_prices.get(symbol)
                update = PriceUpdate.from_price(symbol, price, volume, ts, prev_price)
                
                self._price_history[symbol].append(update)
                if prev_price and prev_price > 0:
                    self._return_history[symbol].append(update.log_return)
                self._volume_history[symbol].append(volume)
                
                self._last_prices[symbol] = price
                self._last_volumes[symbol] = volume
                total_volume += volume * price
                
                if symbol in self.STABLECOINS:
                    stablecoin_volume += volume * price
                
                if symbol == 'BTC':
                    btc_market_cap = price * volume
                total_market_cap += price * volume
            
            self._total_market_volume.append(total_volume)
            self._stablecoin_volume_history.append(stablecoin_volume)
            
            if total_market_cap > 0:
                btc_dominance = btc_market_cap / total_market_cap
                self._btc_dominance_history.append(btc_dominance)
            
            self._update_correlations()
            self._detect_breakdowns()
    
    def _update_correlations(self) -> None:
        """Calculate and update correlation matrix"""
        for i, asset_a in enumerate(self.tracked_assets):
            for asset_b in self.tracked_assets[i + 1:]:
                returns_a = list(self._return_history.get(asset_a, []))
                returns_b = list(self._return_history.get(asset_b, []))
                
                min_len = min(len(returns_a), len(returns_b))
                if min_len < self.min_samples_for_correlation:
                    continue
                
                returns_a = returns_a[-min_len:]
                returns_b = returns_b[-min_len:]
                
                try:
                    pearson_corr = np.corrcoef(returns_a, returns_b)[0, 1]
                    if np.isnan(pearson_corr):
                        pearson_corr = 0.0
                    
                    pair_key = self._get_pair_key(asset_a, asset_b)
                    self._correlation_history[pair_key].append(pearson_corr)
                except Exception as e:
                    logger.debug(f"Error calculating correlation for {asset_a}/{asset_b}: {e}")
    
    def _detect_breakdowns(self) -> None:
        """Detect correlation breakdowns using z-score divergence"""
        now = datetime.now()
        
        for pair_key, corr_history in self._correlation_history.items():
            if len(corr_history) < self.min_samples_for_correlation:
                continue
            
            corr_array = np.array(list(corr_history))
            current_corr = corr_array[-1]
            historical_mean = np.mean(corr_array[:-1]) if len(corr_array) > 1 else current_corr
            historical_std = np.std(corr_array[:-1]) if len(corr_array) > 1 else 0.1
            
            if historical_std < 0.01:
                historical_std = 0.01
            
            z_score = (current_corr - historical_mean) / historical_std
            
            existing = self._active_breakdowns.get(pair_key)
            last_alert = self._breakdown_timestamps.get(pair_key, datetime.min)
            cooldown_active = (now - last_alert).total_seconds() < self.breakdown_cooldown_seconds
            
            severity, severity_score = self._calculate_breakdown_severity(abs(z_score))
            
            if severity_score >= 30:
                if not existing or not cooldown_active:
                    assets = pair_key.split('/')
                    breakdown = CorrelationBreakdown(
                        pair_key=pair_key,
                        asset_a=assets[0],
                        asset_b=assets[1],
                        current_correlation=current_corr,
                        historical_mean=historical_mean,
                        historical_std=historical_std,
                        z_score=z_score,
                        severity=severity,
                        severity_score=severity_score,
                        direction="DIVERGING" if z_score < 0 else "CONVERGING",
                        start_time=existing.start_time if existing else now,
                        duration_seconds=(now - (existing.start_time if existing else now)).total_seconds(),
                        is_active=True
                    )
                    self._active_breakdowns[pair_key] = breakdown
                    self._breakdown_timestamps[pair_key] = now
                    
                    if not existing:
                        logger.warning(f"Correlation breakdown detected: {pair_key} z={z_score:.2f} severity={severity.label}")
                elif existing:
                    existing.duration_seconds = (now - existing.start_time).total_seconds()
                    existing.severity_score = severity_score
                    existing.severity = severity
            elif existing and severity_score < 20:
                existing.is_active = False
                logger.info(f"Correlation breakdown resolved: {pair_key}")
    
    def _calculate_breakdown_severity(self, abs_z_score: float) -> Tuple[BreakdownSeverity, float]:
        """Calculate breakdown severity from z-score"""
        if abs_z_score >= self.BREAKDOWN_THRESHOLDS['critical']:
            severity = BreakdownSeverity.CRITICAL
            score = min(100, 70 + (abs_z_score - 5.0) * 10)
        elif abs_z_score >= self.BREAKDOWN_THRESHOLDS['severe']:
            severity = BreakdownSeverity.SEVERE
            score = 50 + (abs_z_score - 4.0) * 20
        elif abs_z_score >= self.BREAKDOWN_THRESHOLDS['moderate']:
            severity = BreakdownSeverity.MODERATE
            score = 30 + (abs_z_score - 3.0) * 20
        elif abs_z_score >= self.BREAKDOWN_THRESHOLDS['minor']:
            severity = BreakdownSeverity.MINOR
            score = (abs_z_score - 2.0) * 30
        else:
            severity = BreakdownSeverity.MINOR
            score = 0.0
        
        return severity, float(np.clip(score, 0, 100))
    
    def _calculate_correlation_matrix(self) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Dict[str, float]]]:
        """Calculate full Pearson and Spearman correlation matrices"""
        pearson_matrix: Dict[str, Dict[str, float]] = {}
        spearman_matrix: Dict[str, Dict[str, float]] = {}
        
        for asset in self.tracked_assets:
            pearson_matrix[asset] = {}
            spearman_matrix[asset] = {}
            pearson_matrix[asset][asset] = 1.0
            spearman_matrix[asset][asset] = 1.0
        
        for i, asset_a in enumerate(self.tracked_assets):
            for asset_b in self.tracked_assets[i + 1:]:
                returns_a = list(self._return_history.get(asset_a, []))
                returns_b = list(self._return_history.get(asset_b, []))
                
                min_len = min(len(returns_a), len(returns_b))
                if min_len < self.min_samples_for_correlation:
                    pearson_corr = 0.0
                    spearman_corr = 0.0
                else:
                    returns_a = returns_a[-min_len:]
                    returns_b = returns_b[-min_len:]
                    
                    try:
                        pearson_corr = np.corrcoef(returns_a, returns_b)[0, 1]
                        if np.isnan(pearson_corr):
                            pearson_corr = 0.0
                        
                        spearman_corr, _ = stats.spearmanr(returns_a, returns_b)
                        if np.isnan(spearman_corr):
                            spearman_corr = 0.0
                    except Exception:
                        pearson_corr = 0.0
                        spearman_corr = 0.0
                
                pearson_matrix[asset_a][asset_b] = round(pearson_corr, 4)
                pearson_matrix[asset_b][asset_a] = round(pearson_corr, 4)
                spearman_matrix[asset_a][asset_b] = round(spearman_corr, 4)
                spearman_matrix[asset_b][asset_a] = round(spearman_corr, 4)
        
        return pearson_matrix, spearman_matrix
    
    def _calculate_pair_metrics(self) -> Dict[str, CorrelationPair]:
        """Calculate detailed metrics for each asset pair"""
        pair_metrics: Dict[str, CorrelationPair] = {}
        now = datetime.now()
        
        for i, asset_a in enumerate(self.tracked_assets):
            for asset_b in self.tracked_assets[i + 1:]:
                pair_key = self._get_pair_key(asset_a, asset_b)
                corr_history = list(self._correlation_history.get(pair_key, []))
                
                if len(corr_history) < 2:
                    continue
                
                corr_array = np.array(corr_history)
                current_corr = corr_array[-1]
                historical_mean = np.mean(corr_array[:-1])
                historical_std = np.std(corr_array[:-1])
                
                if historical_std < 0.01:
                    historical_std = 0.01
                
                z_score = (current_corr - historical_mean) / historical_std
                
                returns_a = list(self._return_history.get(asset_a, []))
                returns_b = list(self._return_history.get(asset_b, []))
                min_len = min(len(returns_a), len(returns_b))
                
                try:
                    spearman_corr, _ = stats.spearmanr(
                        returns_a[-min_len:], 
                        returns_b[-min_len:]
                    ) if min_len >= 5 else (0.0, 1.0)
                    if np.isnan(spearman_corr):
                        spearman_corr = 0.0
                except Exception:
                    spearman_corr = 0.0
                
                pair_metrics[pair_key] = CorrelationPair(
                    asset_a=asset_a,
                    asset_b=asset_b,
                    pearson_correlation=round(float(current_corr), 4),
                    spearman_correlation=round(float(spearman_corr), 4),
                    sample_count=min_len,
                    historical_mean=round(float(historical_mean), 4),
                    historical_std=round(float(historical_std), 4),
                    z_score=round(float(z_score), 4),
                    last_updated=now
                )
        
        return pair_metrics
    
    def _calculate_contagion_risk(self) -> ContagionRisk:
        """Calculate aggregate contagion risk index"""
        now = datetime.now()
        active_breakdowns = [b for b in self._active_breakdowns.values() if b.is_active]
        
        weighted_severity = 0.0
        affected_pairs = []
        primary_driver = None
        max_severity = 0.0
        
        for breakdown in active_breakdowns:
            weight = self.PAIR_WEIGHTS.get(breakdown.pair_key, 1.0)
            weighted_severity += breakdown.severity_score * weight
            affected_pairs.append(breakdown.pair_key)
            
            if breakdown.severity_score > max_severity:
                max_severity = breakdown.severity_score
                primary_driver = breakdown.pair_key
        
        if active_breakdowns:
            weighted_severity /= len(active_breakdowns)
        
        volume_spillover = self._calculate_volume_spillover()
        
        cross_stress = self._calculate_cross_correlation_stress()
        
        risk_score = (
            weighted_severity * 0.40 +
            volume_spillover * 0.30 +
            cross_stress * 100 * 0.30
        )
        risk_score = float(np.clip(risk_score, 0, 100))
        
        if risk_score >= 70:
            level = ContagionLevel.EXTREME
            recommendation = "Immediate risk reduction. Consider full hedging or position exit."
        elif risk_score >= 50:
            level = ContagionLevel.HIGH
            recommendation = "Reduce exposure significantly. Implement defensive positioning."
        elif risk_score >= 30:
            level = ContagionLevel.ELEVATED
            recommendation = "Increase monitoring frequency. Tighten stop-losses."
        else:
            level = ContagionLevel.LOW
            recommendation = "Normal conditions. Continue standard operations."
        
        return ContagionRisk(
            timestamp=now,
            risk_score=risk_score,
            level=level,
            active_breakdowns=len(active_breakdowns),
            weighted_severity=weighted_severity,
            volume_spillover_score=volume_spillover,
            cross_correlation_stress=cross_stress,
            affected_pairs=affected_pairs,
            primary_driver=primary_driver,
            recommendation=recommendation
        )
    
    def _calculate_volume_spillover(self) -> float:
        """
        Calculate volume spillover score.
        
        Measures abnormal volume clustering across assets indicating
        potential contagion or systemic stress.
        """
        if len(self._total_market_volume) < 10:
            return 0.0
        
        volume_array = np.array(list(self._total_market_volume))
        current_volume = volume_array[-1]
        historical_mean = np.mean(volume_array[:-1])
        historical_std = np.std(volume_array[:-1])
        
        if historical_std < 1e-10:
            return 0.0
        
        volume_z = (current_volume - historical_mean) / historical_std
        
        spillover_score = min(100, max(0, (abs(volume_z) - 1) * 25))
        
        return float(spillover_score)
    
    def _calculate_cross_correlation_stress(self) -> float:
        """
        Calculate cross-correlation stress metric.
        
        Measures aggregate deviation from normal correlation structure.
        High values indicate correlation regime breakdown.
        """
        z_scores = []
        
        for pair_key, corr_history in self._correlation_history.items():
            if len(corr_history) < 10:
                continue
            
            corr_array = np.array(list(corr_history))
            current = corr_array[-1]
            mean = np.mean(corr_array[:-1])
            std = np.std(corr_array[:-1])
            
            if std > 0.01:
                z = abs((current - mean) / std)
                z_scores.append(z)
        
        if not z_scores:
            return 0.0
        
        mean_z = np.mean(z_scores)
        stress = (mean_z - 1) / 3
        
        return float(np.clip(stress, 0, 1))
    
    def _calculate_safe_haven_flow(self) -> SafeHavenFlow:
        """
        Calculate safe-haven flow analysis.
        
        Detects capital movement from risk assets to safe havens
        including stablecoins and BTC dominance shifts.
        """
        now = datetime.now()
        
        btc_dom_delta = 0.0
        if len(self._btc_dominance_history) >= 10:
            dom_array = np.array(list(self._btc_dominance_history))
            btc_dom_delta = dom_array[-1] - np.mean(dom_array[-10:-1])
        
        stablecoin_inflow = 0.0
        if len(self._stablecoin_volume_history) >= 10:
            stable_array = np.array(list(self._stablecoin_volume_history))
            stable_mean = np.mean(stable_array[:-1])
            if stable_mean > 0:
                stablecoin_inflow = (stable_array[-1] - stable_mean) / stable_mean
        
        risk_outflow = 0.0
        risk_assets = ['ETH', 'SOL', 'BNB', 'ADA', 'AVAX']
        for asset in risk_assets:
            vol_history = list(self._volume_history.get(asset, []))
            if len(vol_history) >= 10:
                vol_array = np.array(vol_history)
                vol_mean = np.mean(vol_array[:-1])
                if vol_mean > 0:
                    risk_outflow += (vol_mean - vol_array[-1]) / vol_mean
        risk_outflow /= len(risk_assets) if risk_assets else 1
        
        alt_to_btc = 0.0
        btc_vol = list(self._volume_history.get('BTC', []))
        if len(btc_vol) >= 10:
            btc_vol_array = np.array(btc_vol)
            btc_mean = np.mean(btc_vol_array[:-1])
            if btc_mean > 0:
                btc_change = (btc_vol_array[-1] - btc_mean) / btc_mean
                alt_to_btc = btc_change - risk_outflow
        
        flight_score = (
            btc_dom_delta * 100 * 0.30 +
            stablecoin_inflow * 100 * 0.35 +
            risk_outflow * 100 * 0.20 +
            alt_to_btc * 100 * 0.15
        )
        flight_score = float(np.clip(flight_score, -100, 100))
        
        flow_intensity = abs(flight_score) / 100
        
        if flight_score >= 50:
            flow_direction = FlowDirection.FLIGHT_TO_QUALITY
        elif flight_score >= 20:
            flow_direction = FlowDirection.RISK_OFF
        elif flight_score <= -20:
            flow_direction = FlowDirection.RISK_ON
        else:
            flow_direction = FlowDirection.NEUTRAL
        
        return SafeHavenFlow(
            timestamp=now,
            flow_direction=flow_direction,
            flow_intensity=flow_intensity,
            btc_dominance_delta=btc_dom_delta,
            stablecoin_inflow_ratio=stablecoin_inflow,
            risk_asset_outflow_ratio=risk_outflow,
            flight_to_quality_score=max(0, flight_score),
            alt_to_btc_flow=alt_to_btc,
            indicators={
                'btc_dominance_weight': 0.30,
                'stablecoin_weight': 0.35,
                'risk_outflow_weight': 0.20,
                'alt_btc_weight': 0.15
            }
        )
    
    def get_correlation_state(self) -> CorrelationState:
        """
        Get complete correlation engine state.
        
        Returns:
            CorrelationState containing matrix, breakdowns, and risk metrics
        """
        with self._lock:
            pearson_matrix, spearman_matrix = self._calculate_correlation_matrix()
            pair_metrics = self._calculate_pair_metrics()
            active_breakdowns = [b for b in self._active_breakdowns.values() if b.is_active]
            contagion_risk = self._calculate_contagion_risk()
            safe_haven_flow = self._calculate_safe_haven_flow()
            
            sample_counts = [len(h) for h in self._return_history.values() if h]
            avg_samples = int(np.mean(sample_counts)) if sample_counts else 0
            
            return CorrelationState(
                timestamp=datetime.now(),
                correlation_matrix=pearson_matrix,
                spearman_matrix=spearman_matrix,
                pair_metrics=pair_metrics,
                active_breakdowns=active_breakdowns,
                contagion_risk=contagion_risk,
                safe_haven_flow=safe_haven_flow,
                sample_count=avg_samples,
                tracked_assets=self.tracked_assets.copy(),
                window_samples=self.window_samples
            )
    
    def detect_breakdown(self) -> List[CorrelationBreakdown]:
        """
        Get list of active correlation breakdowns.
        
        Returns:
            List of active CorrelationBreakdown events
        """
        with self._lock:
            return [b for b in self._active_breakdowns.values() if b.is_active]
    
    def get_contagion_risk(self) -> ContagionRisk:
        """
        Get current contagion risk assessment.
        
        Returns:
            ContagionRisk with aggregate risk metrics
        """
        with self._lock:
            return self._calculate_contagion_risk()
    
    def get_safe_haven_flow(self) -> SafeHavenFlow:
        """
        Get current safe-haven flow analysis.
        
        Returns:
            SafeHavenFlow with flight-to-quality metrics
        """
        with self._lock:
            return self._calculate_safe_haven_flow()
    
    def get_pair_correlation(
        self,
        asset_a: str,
        asset_b: str
    ) -> Optional[CorrelationPair]:
        """
        Get correlation metrics for a specific pair.
        
        Args:
            asset_a: First asset symbol
            asset_b: Second asset symbol
            
        Returns:
            CorrelationPair or None if insufficient data
        """
        pair_key = self._get_pair_key(asset_a, asset_b)
        metrics = self._calculate_pair_metrics()
        return metrics.get(pair_key)
    
    def get_correlation_matrix_as_numpy(self) -> Tuple[np.ndarray, List[str]]:
        """
        Get correlation matrix as numpy array.
        
        Returns:
            Tuple of (correlation matrix, list of asset labels)
        """
        with self._lock:
            pearson_matrix, _ = self._calculate_correlation_matrix()
            assets = self.tracked_assets.copy()
            n = len(assets)
            matrix = np.zeros((n, n))
            
            for i, asset_a in enumerate(assets):
                for j, asset_b in enumerate(assets):
                    matrix[i, j] = pearson_matrix.get(asset_a, {}).get(asset_b, 0.0)
            
            return matrix, assets
    
    def reset(self) -> None:
        """Reset all engine state"""
        with self._lock:
            self._price_history.clear()
            self._return_history.clear()
            self._volume_history.clear()
            self._correlation_history.clear()
            self._active_breakdowns.clear()
            self._breakdown_timestamps.clear()
            self._last_prices.clear()
            self._last_volumes.clear()
            self._total_market_volume.clear()
            self._btc_dominance_history.clear()
            self._stablecoin_volume_history.clear()
            
            self._init_data_structures()
            
            logger.info("CrossAssetCorrelationEngine state reset")
    
    def get_state(self) -> CorrelationState:
        """Alias for get_correlation_state() for API consistency"""
        return self.get_correlation_state()
