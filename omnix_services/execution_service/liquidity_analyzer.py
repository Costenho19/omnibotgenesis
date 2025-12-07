"""
OMNIX Execution Protocol V6.5.4 INSTITUTIONAL+ - Liquidity Analyzer
====================================================================
Institutional-grade liquidity analysis for optimal execution

Components:
- True Bid Liquidity Recovery (TBLR): Rolling imbalance recovery ratio
- Order Book Depth Analysis: Multi-level depth decay metrics
- Hidden Liquidity Detection: Iceberg order footprint heuristics

Author: OMNIX Team
"""

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np

try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    ccxt = None
    CCXT_AVAILABLE = False

from omnix_config import VERSION_BANNER

logger = logging.getLogger(__name__)


class DepthLevel(Enum):
    """Order book depth levels relative to mid price"""
    LEVEL_01 = (0.001, "0.1%")
    LEVEL_05 = (0.005, "0.5%")
    LEVEL_10 = (0.010, "1.0%")
    LEVEL_20 = (0.020, "2.0%")
    
    def __init__(self, pct: float, label: str):
        self.pct = pct
        self.label = label


class LiquidityConfidence(Enum):
    """Confidence levels for hidden liquidity detection"""
    HIGH = ("HIGH", 0.8, "Strong iceberg indicators")
    MEDIUM = ("MEDIUM", 0.5, "Possible hidden liquidity")
    LOW = ("LOW", 0.3, "Weak signals")
    NONE = ("NONE", 0.0, "No hidden liquidity detected")
    
    def __init__(self, level: str, threshold: float, description: str):
        self.level = level
        self.threshold = threshold
        self.description = description


@dataclass
class LiquiditySnapshot:
    """
    Point-in-time liquidity snapshot for TBLR calculation.
    
    Captures bid/ask depth at various levels for tracking recovery
    after large market orders.
    """
    timestamp: datetime
    symbol: str
    mid_price: float
    bid_depth_usd: float
    ask_depth_usd: float
    bid_levels: Dict[str, float] = field(default_factory=dict)
    ask_levels: Dict[str, float] = field(default_factory=dict)
    spread_bps: float = 0.0
    total_bids: int = 0
    total_asks: int = 0
    
    @property
    def depth_imbalance_ratio(self) -> float:
        """
        Calculate depth imbalance ratio.
        
        Formula: (bid_depth - ask_depth) / (bid_depth + ask_depth)
        Range: -1.0 (all asks) to +1.0 (all bids)
        """
        total = self.bid_depth_usd + self.ask_depth_usd
        if total == 0:
            return 0.0
        return (self.bid_depth_usd - self.ask_depth_usd) / total
    
    @property
    def total_depth_usd(self) -> float:
        """Total orderbook depth in USD"""
        return self.bid_depth_usd + self.ask_depth_usd


@dataclass
class DepthAnalysis:
    """
    Multi-level order book depth analysis.
    
    Provides decay metrics at 0.1%, 0.5%, 1%, 2% from mid price
    with weighted scoring for execution quality assessment.
    """
    timestamp: datetime
    symbol: str
    mid_price: float
    depth_by_level: Dict[str, Dict[str, float]] = field(default_factory=dict)
    decay_rates: Dict[str, float] = field(default_factory=dict)
    imbalance_ratio: float = 0.0
    weighted_depth_score: float = 0.0
    liquidity_grade: str = "C"
    
    def get_bid_depth_at_level(self, level: str) -> float:
        """Get bid depth at specified level"""
        return self.depth_by_level.get(level, {}).get('bid', 0.0)
    
    def get_ask_depth_at_level(self, level: str) -> float:
        """Get ask depth at specified level"""
        return self.depth_by_level.get(level, {}).get('ask', 0.0)
    
    @property
    def is_healthy(self) -> bool:
        """Check if liquidity is healthy for execution"""
        return self.weighted_depth_score >= 50.0 and abs(self.imbalance_ratio) < 0.5


@dataclass
class HiddenLiquiditySignal:
    """
    Hidden liquidity (iceberg order) detection signal.
    
    Detects presence of hidden liquidity based on:
    - Trade size vs visible depth anomalies
    - Repeated refreshing at same price level
    - Volume patterns inconsistent with visible book
    """
    timestamp: datetime
    symbol: str
    confidence: LiquidityConfidence
    confidence_score: float
    detected_side: str
    price_level: float
    estimated_hidden_size: float
    indicators: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_significant(self) -> bool:
        """Check if hidden liquidity signal is actionable"""
        return self.confidence_score >= 0.5 and self.estimated_hidden_size > 10000


@dataclass
class TBLRMetrics:
    """
    True Bid Liquidity Recovery metrics.
    
    Measures how quickly bid liquidity recovers after large sells.
    Formula: TBLR = (recovered_bid_depth / initial_impact) over rolling window
    """
    timestamp: datetime
    symbol: str
    tblr_ratio: float
    recovery_time_ms: float
    initial_impact_usd: float
    recovered_depth_usd: float
    window_seconds: int
    sample_count: int
    
    @property
    def recovery_quality(self) -> str:
        """Assess recovery quality"""
        if self.tblr_ratio >= 0.95:
            return "EXCELLENT"
        elif self.tblr_ratio >= 0.80:
            return "GOOD"
        elif self.tblr_ratio >= 0.60:
            return "MODERATE"
        elif self.tblr_ratio >= 0.40:
            return "POOR"
        return "CRITICAL"


class LiquidityAnalyzer:
    """
    OMNIX Liquidity Analyzer - Institutional Grade
    
    Provides comprehensive liquidity analysis including:
    - True Bid Liquidity Recovery (TBLR)
    - Order Book Depth Analysis
    - Hidden Liquidity Detection
    
    Thread-safe implementation with configurable rolling windows.
    """
    
    def __init__(
        self,
        rolling_window_seconds: int = 60,
        max_snapshots: int = 1000,
        kraken_config: Optional[Dict] = None
    ):
        """
        Initialize LiquidityAnalyzer.
        
        Args:
            rolling_window_seconds: Window size for rolling metrics (default 60s)
            max_snapshots: Maximum snapshots to retain (default 1000)
            kraken_config: Optional ccxt config for Kraken
        """
        self.rolling_window_seconds = rolling_window_seconds
        self.max_snapshots = max_snapshots
        
        self._lock = threading.RLock()
        self._snapshots: Dict[str, Deque[LiquiditySnapshot]] = {}
        self._trade_history: Dict[str, Deque[Dict]] = {}
        self._impact_events: Dict[str, Deque[Dict]] = {}
        
        self._depth_weights = {
            DepthLevel.LEVEL_01.label: 0.40,
            DepthLevel.LEVEL_05.label: 0.30,
            DepthLevel.LEVEL_10.label: 0.20,
            DepthLevel.LEVEL_20.label: 0.10,
        }
        
        self._exchange = None
        self._init_exchange(kraken_config)
        
        logger.info(f"LiquidityAnalyzer {VERSION_BANNER} initialized")
        logger.info(f"Rolling window: {rolling_window_seconds}s, Max snapshots: {max_snapshots}")
    
    def _init_exchange(self, config: Optional[Dict] = None) -> None:
        """Initialize ccxt exchange connection"""
        if not CCXT_AVAILABLE:
            logger.warning("ccxt not available - using fallback mode")
            return
        
        try:
            import os
            exchange_config = config or {
                'enableRateLimit': True,
                'timeout': 30000,
                'options': {'adjustForTimeDifference': True}
            }
            
            api_key = os.environ.get('KRAKEN_API_KEY', '')
            api_secret = os.environ.get('KRAKEN_API_SECRET', '')
            
            if api_key and api_secret:
                exchange_config['apiKey'] = api_key
                exchange_config['secret'] = api_secret
            
            self._exchange = ccxt.kraken(exchange_config)
            logger.info("Kraken exchange connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            self._exchange = None
    
    def fetch_order_book(
        self,
        symbol: str,
        limit: int = 100
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch order book from Kraken via ccxt.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            limit: Number of levels to fetch (default 100)
            
        Returns:
            Order book dict with bids, asks, timestamp or None on error
        """
        if not self._exchange:
            logger.warning("Exchange not initialized")
            return None
        
        try:
            orderbook = self._exchange.fetch_order_book(symbol, limit)
            return {
                'symbol': symbol,
                'bids': orderbook.get('bids', []),
                'asks': orderbook.get('asks', []),
                'timestamp': orderbook.get('timestamp') or int(time.time() * 1000),
                'datetime': orderbook.get('datetime') or datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            return None
    
    def _calculate_mid_price(self, bids: List, asks: List) -> float:
        """Calculate mid price from order book"""
        if not bids or not asks:
            return 0.0
        best_bid = bids[0][0] if bids else 0
        best_ask = asks[0][0] if asks else 0
        if best_bid and best_ask:
            return (best_bid + best_ask) / 2
        return best_bid or best_ask or 0.0
    
    def _calculate_spread_bps(self, bids: List, asks: List) -> float:
        """Calculate bid-ask spread in basis points"""
        if not bids or not asks:
            return 0.0
        best_bid = bids[0][0]
        best_ask = asks[0][0]
        mid = (best_bid + best_ask) / 2
        if mid == 0:
            return 0.0
        return ((best_ask - best_bid) / mid) * 10000
    
    def _calculate_depth_at_levels(
        self,
        bids: List,
        asks: List,
        mid_price: float
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate depth at multiple price levels.
        
        Returns depth in USD at 0.1%, 0.5%, 1%, 2% from mid price.
        """
        result = {}
        
        for level in DepthLevel:
            upper_bound = mid_price * (1 + level.pct)
            lower_bound = mid_price * (1 - level.pct)
            
            bid_depth = sum(
                price * amount
                for price, amount in bids
                if price >= lower_bound
            )
            
            ask_depth = sum(
                price * amount
                for price, amount in asks
                if price <= upper_bound
            )
            
            result[level.label] = {
                'bid': bid_depth,
                'ask': ask_depth,
                'total': bid_depth + ask_depth,
                'imbalance': (bid_depth - ask_depth) / (bid_depth + ask_depth + 1e-10)
            }
        
        return result
    
    def _calculate_decay_rates(
        self,
        depth_by_level: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """
        Calculate depth decay rates between levels.
        
        Measures how quickly depth decreases as we move away from mid.
        """
        levels = [DepthLevel.LEVEL_01.label, DepthLevel.LEVEL_05.label,
                  DepthLevel.LEVEL_10.label, DepthLevel.LEVEL_20.label]
        decay_rates = {}
        
        for i in range(len(levels) - 1):
            current_level = levels[i]
            next_level = levels[i + 1]
            
            current_depth = depth_by_level.get(current_level, {}).get('total', 0)
            next_depth = depth_by_level.get(next_level, {}).get('total', 0)
            
            if current_depth > 0:
                decay_rates[f"{current_level}_to_{next_level}"] = (
                    (next_depth - current_depth) / current_depth
                )
            else:
                decay_rates[f"{current_level}_to_{next_level}"] = 0.0
        
        return decay_rates
    
    def _calculate_weighted_depth_score(
        self,
        depth_by_level: Dict[str, Dict[str, float]],
        mid_price: float
    ) -> float:
        """
        Calculate weighted average depth score (0-100).
        
        Weights closer levels more heavily as they're more relevant
        for immediate execution quality.
        """
        total_score = 0.0
        benchmarks = {
            DepthLevel.LEVEL_01.label: 500_000,
            DepthLevel.LEVEL_05.label: 1_000_000,
            DepthLevel.LEVEL_10.label: 2_000_000,
            DepthLevel.LEVEL_20.label: 5_000_000,
        }
        
        for level_label, weight in self._depth_weights.items():
            depth = depth_by_level.get(level_label, {}).get('total', 0)
            benchmark = benchmarks.get(level_label, 1_000_000)
            level_score = min(100, (depth / benchmark) * 100)
            total_score += level_score * weight
        
        return round(total_score, 2)
    
    def _assign_liquidity_grade(self, score: float, imbalance: float) -> str:
        """Assign liquidity grade based on score and imbalance"""
        if abs(imbalance) > 0.7:
            return "D"
        
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C+"
        elif score >= 40:
            return "C"
        elif score >= 25:
            return "D"
        return "F"
    
    def _create_snapshot(
        self,
        orderbook: Dict[str, Any]
    ) -> LiquiditySnapshot:
        """Create liquidity snapshot from order book data"""
        bids = orderbook.get('bids', [])
        asks = orderbook.get('asks', [])
        symbol = orderbook.get('symbol', 'UNKNOWN')
        
        mid_price = self._calculate_mid_price(bids, asks)
        spread_bps = self._calculate_spread_bps(bids, asks)
        depth_by_level = self._calculate_depth_at_levels(bids, asks, mid_price)
        
        bid_depth_usd = sum(price * amount for price, amount in bids)
        ask_depth_usd = sum(price * amount for price, amount in asks)
        
        bid_levels = {
            level: depth_by_level.get(level, {}).get('bid', 0)
            for level in self._depth_weights.keys()
        }
        ask_levels = {
            level: depth_by_level.get(level, {}).get('ask', 0)
            for level in self._depth_weights.keys()
        }
        
        return LiquiditySnapshot(
            timestamp=datetime.now(),
            symbol=symbol,
            mid_price=mid_price,
            bid_depth_usd=bid_depth_usd,
            ask_depth_usd=ask_depth_usd,
            bid_levels=bid_levels,
            ask_levels=ask_levels,
            spread_bps=spread_bps,
            total_bids=len(bids),
            total_asks=len(asks)
        )
    
    def _store_snapshot(self, snapshot: LiquiditySnapshot) -> None:
        """Thread-safe snapshot storage"""
        with self._lock:
            symbol = snapshot.symbol
            if symbol not in self._snapshots:
                self._snapshots[symbol] = deque(maxlen=self.max_snapshots)
            self._snapshots[symbol].append(snapshot)
    
    def _get_recent_snapshots(
        self,
        symbol: str,
        window_seconds: Optional[int] = None
    ) -> List[LiquiditySnapshot]:
        """Get snapshots within rolling window"""
        window = window_seconds or self.rolling_window_seconds
        cutoff = datetime.now()
        
        with self._lock:
            if symbol not in self._snapshots:
                return []
            
            return [
                s for s in self._snapshots[symbol]
                if (cutoff - s.timestamp).total_seconds() <= window
            ]
    
    def analyze_depth(self, orderbook: Dict[str, Any]) -> DepthAnalysis:
        """
        Perform multi-level depth analysis.
        
        Calculates depth decay metrics, imbalance ratios, and
        weighted depth scores across 0.1%, 0.5%, 1%, 2% levels.
        
        Args:
            orderbook: Order book data with bids and asks
            
        Returns:
            DepthAnalysis with comprehensive depth metrics
        """
        bids = orderbook.get('bids', [])
        asks = orderbook.get('asks', [])
        symbol = orderbook.get('symbol', 'UNKNOWN')
        
        mid_price = self._calculate_mid_price(bids, asks)
        depth_by_level = self._calculate_depth_at_levels(bids, asks, mid_price)
        decay_rates = self._calculate_decay_rates(depth_by_level)
        
        total_bid = sum(depth_by_level.get(l, {}).get('bid', 0) for l in self._depth_weights)
        total_ask = sum(depth_by_level.get(l, {}).get('ask', 0) for l in self._depth_weights)
        imbalance = (total_bid - total_ask) / (total_bid + total_ask + 1e-10)
        
        weighted_score = self._calculate_weighted_depth_score(depth_by_level, mid_price)
        grade = self._assign_liquidity_grade(weighted_score, imbalance)
        
        return DepthAnalysis(
            timestamp=datetime.now(),
            symbol=symbol,
            mid_price=mid_price,
            depth_by_level=depth_by_level,
            decay_rates=decay_rates,
            imbalance_ratio=round(imbalance, 4),
            weighted_depth_score=weighted_score,
            liquidity_grade=grade
        )
    
    def calculate_tblr(
        self,
        symbol: str,
        window_seconds: Optional[int] = None
    ) -> Optional[TBLRMetrics]:
        """
        Calculate True Bid Liquidity Recovery (TBLR).
        
        Measures how quickly bid liquidity recovers after large sells.
        Formula: TBLR = (recovered_bid_depth / initial_impact) over rolling window
        
        Args:
            symbol: Trading pair
            window_seconds: Optional custom window (default uses class setting)
            
        Returns:
            TBLRMetrics or None if insufficient data
        """
        window = window_seconds or self.rolling_window_seconds
        snapshots = self._get_recent_snapshots(symbol, window)
        
        if len(snapshots) < 3:
            logger.debug(f"Insufficient snapshots for TBLR: {len(snapshots)}")
            return None
        
        bid_depths = np.array([s.bid_depth_usd for s in snapshots])
        
        mean_depth = np.mean(bid_depths)
        std_depth = np.std(bid_depths)
        
        if std_depth < 1e-6:
            return TBLRMetrics(
                timestamp=datetime.now(),
                symbol=symbol,
                tblr_ratio=1.0,
                recovery_time_ms=0,
                initial_impact_usd=0,
                recovered_depth_usd=mean_depth,
                window_seconds=window,
                sample_count=len(snapshots)
            )
        
        threshold = mean_depth - (2 * std_depth)
        impact_indices = np.where(bid_depths < threshold)[0]
        
        if len(impact_indices) == 0:
            return TBLRMetrics(
                timestamp=datetime.now(),
                symbol=symbol,
                tblr_ratio=1.0,
                recovery_time_ms=0,
                initial_impact_usd=0,
                recovered_depth_usd=mean_depth,
                window_seconds=window,
                sample_count=len(snapshots)
            )
        
        recovery_ratios = []
        recovery_times = []
        impacts = []
        
        for idx in impact_indices:
            if idx >= len(bid_depths) - 1:
                continue
            
            impact_depth = bid_depths[idx]
            initial_impact = mean_depth - impact_depth
            impacts.append(initial_impact)
            
            for recovery_idx in range(idx + 1, len(bid_depths)):
                if bid_depths[recovery_idx] >= mean_depth * 0.9:
                    recovered = bid_depths[recovery_idx] - impact_depth
                    ratio = min(1.0, recovered / (initial_impact + 1e-10))
                    recovery_ratios.append(ratio)
                    
                    time_diff = (
                        snapshots[recovery_idx].timestamp -
                        snapshots[idx].timestamp
                    ).total_seconds() * 1000
                    recovery_times.append(time_diff)
                    break
        
        if not recovery_ratios:
            tblr = bid_depths[-1] / mean_depth
            recovery_time = 0
            impact = 0
            recovered = bid_depths[-1]
        else:
            tblr = np.mean(recovery_ratios)
            recovery_time = np.mean(recovery_times)
            impact = np.mean(impacts)
            recovered = mean_depth * tblr
        
        return TBLRMetrics(
            timestamp=datetime.now(),
            symbol=symbol,
            tblr_ratio=round(float(tblr), 4),
            recovery_time_ms=round(float(recovery_time), 2),
            initial_impact_usd=round(float(impact), 2),
            recovered_depth_usd=round(float(recovered), 2),
            window_seconds=window,
            sample_count=len(snapshots)
        )
    
    def detect_hidden_liquidity(
        self,
        symbol: str,
        orderbook: Dict[str, Any],
        recent_trades: Optional[List[Dict]] = None
    ) -> HiddenLiquiditySignal:
        """
        Detect hidden liquidity (iceberg orders).
        
        Uses heuristics based on:
        - Large trade vs visible depth anomaly
        - Order refreshing patterns
        - Volume inconsistencies
        
        Args:
            symbol: Trading pair
            orderbook: Current order book
            recent_trades: Optional list of recent trades
            
        Returns:
            HiddenLiquiditySignal with confidence scoring
        """
        bids = orderbook.get('bids', [])
        asks = orderbook.get('asks', [])
        
        mid_price = self._calculate_mid_price(bids, asks)
        
        indicators = {
            'depth_anomaly': 0.0,
            'trade_size_ratio': 0.0,
            'refresh_pattern': 0.0,
            'volume_inconsistency': 0.0
        }
        
        detected_side = 'UNKNOWN'
        price_level = mid_price
        estimated_size = 0.0
        
        if recent_trades:
            trades = recent_trades[-100:]
            
            trade_sizes = [t.get('amount', 0) * t.get('price', 0) for t in trades]
            if trade_sizes:
                avg_trade_size = np.mean(trade_sizes)
                max_trade_size = np.max(trade_sizes)
                
                best_bid_depth = bids[0][0] * bids[0][1] if bids else 0
                best_ask_depth = asks[0][0] * asks[0][1] if asks else 0
                
                if max_trade_size > best_bid_depth * 1.5:
                    indicators['depth_anomaly'] = min(1.0, max_trade_size / (best_bid_depth + 1))
                    detected_side = 'BID'
                    price_level = bids[0][0] if bids else mid_price
                    estimated_size = max_trade_size - best_bid_depth
                    
                if max_trade_size > best_ask_depth * 1.5:
                    ask_anomaly = min(1.0, max_trade_size / (best_ask_depth + 1))
                    if ask_anomaly > indicators['depth_anomaly']:
                        indicators['depth_anomaly'] = ask_anomaly
                        detected_side = 'ASK'
                        price_level = asks[0][0] if asks else mid_price
                        estimated_size = max_trade_size - best_ask_depth
                
                indicators['trade_size_ratio'] = min(1.0, max_trade_size / (avg_trade_size + 1))
        
        snapshots = self._get_recent_snapshots(symbol, 30)
        if len(snapshots) >= 5:
            bid_changes = []
            for i in range(1, len(snapshots)):
                prev = snapshots[i-1].bid_depth_usd
                curr = snapshots[i].bid_depth_usd
                if prev > 0:
                    change = abs(curr - prev) / prev
                    bid_changes.append(change)
            
            if bid_changes:
                std_change = np.std(bid_changes)
                if std_change < 0.05 and len(bid_changes) > 3:
                    indicators['refresh_pattern'] = 0.3
                elif std_change < 0.02:
                    indicators['refresh_pattern'] = 0.6
        
        confidence_score = (
            indicators['depth_anomaly'] * 0.40 +
            indicators['trade_size_ratio'] * 0.25 +
            indicators['refresh_pattern'] * 0.20 +
            indicators['volume_inconsistency'] * 0.15
        )
        confidence_score = round(min(1.0, confidence_score), 4)
        
        if confidence_score >= LiquidityConfidence.HIGH.threshold:
            confidence = LiquidityConfidence.HIGH
        elif confidence_score >= LiquidityConfidence.MEDIUM.threshold:
            confidence = LiquidityConfidence.MEDIUM
        elif confidence_score >= LiquidityConfidence.LOW.threshold:
            confidence = LiquidityConfidence.LOW
        else:
            confidence = LiquidityConfidence.NONE
        
        return HiddenLiquiditySignal(
            timestamp=datetime.now(),
            symbol=symbol,
            confidence=confidence,
            confidence_score=confidence_score,
            detected_side=detected_side,
            price_level=price_level,
            estimated_hidden_size=max(0, estimated_size),
            indicators=indicators
        )
    
    def analyze_liquidity(
        self,
        symbol: str,
        include_tblr: bool = True,
        include_hidden: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive liquidity analysis for a symbol.
        
        Combines:
        - Order book depth analysis
        - True Bid Liquidity Recovery (TBLR)
        - Hidden liquidity detection
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            include_tblr: Include TBLR metrics (requires historical data)
            include_hidden: Include hidden liquidity detection
            
        Returns:
            Dict with complete liquidity analysis
        """
        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'version': VERSION_BANNER,
            'status': 'ERROR',
            'depth_analysis': None,
            'tblr_metrics': None,
            'hidden_liquidity': None,
            'snapshot': None,
            'summary': {}
        }
        
        try:
            orderbook = self.fetch_order_book(symbol)
            if not orderbook:
                result['error'] = 'Failed to fetch order book'
                return result
            
            snapshot = self._create_snapshot(orderbook)
            self._store_snapshot(snapshot)
            result['snapshot'] = {
                'mid_price': snapshot.mid_price,
                'bid_depth_usd': round(snapshot.bid_depth_usd, 2),
                'ask_depth_usd': round(snapshot.ask_depth_usd, 2),
                'spread_bps': round(snapshot.spread_bps, 2),
                'depth_imbalance': round(snapshot.depth_imbalance_ratio, 4)
            }
            
            depth = self.analyze_depth(orderbook)
            result['depth_analysis'] = {
                'mid_price': depth.mid_price,
                'imbalance_ratio': depth.imbalance_ratio,
                'weighted_depth_score': depth.weighted_depth_score,
                'liquidity_grade': depth.liquidity_grade,
                'depth_by_level': depth.depth_by_level,
                'decay_rates': depth.decay_rates,
                'is_healthy': depth.is_healthy
            }
            
            if include_tblr:
                tblr = self.calculate_tblr(symbol)
                if tblr:
                    result['tblr_metrics'] = {
                        'tblr_ratio': tblr.tblr_ratio,
                        'recovery_time_ms': tblr.recovery_time_ms,
                        'recovery_quality': tblr.recovery_quality,
                        'initial_impact_usd': tblr.initial_impact_usd,
                        'recovered_depth_usd': tblr.recovered_depth_usd,
                        'sample_count': tblr.sample_count
                    }
            
            if include_hidden:
                hidden = self.detect_hidden_liquidity(symbol, orderbook)
                result['hidden_liquidity'] = {
                    'confidence': hidden.confidence.level,
                    'confidence_score': hidden.confidence_score,
                    'detected_side': hidden.detected_side,
                    'price_level': hidden.price_level,
                    'estimated_hidden_size': round(hidden.estimated_hidden_size, 2),
                    'is_significant': hidden.is_significant,
                    'indicators': hidden.indicators
                }
            
            result['summary'] = self._generate_summary(result)
            result['status'] = 'OK'
            
            logger.info(
                f"Liquidity analysis complete for {symbol}: "
                f"Grade={depth.liquidity_grade}, Score={depth.weighted_depth_score}"
            )
            
        except Exception as e:
            logger.error(f"Error analyzing liquidity for {symbol}: {e}")
            result['error'] = str(e)
        
        return result
    
    def _generate_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary of liquidity analysis"""
        summary = {
            'execution_quality': 'UNKNOWN',
            'risk_level': 'UNKNOWN',
            'recommendations': []
        }
        
        depth = analysis.get('depth_analysis', {})
        tblr = analysis.get('tblr_metrics', {})
        hidden = analysis.get('hidden_liquidity', {})
        
        score = depth.get('weighted_depth_score', 0)
        imbalance = abs(depth.get('imbalance_ratio', 0))
        grade = depth.get('liquidity_grade', 'F')
        
        if score >= 70 and imbalance < 0.3:
            summary['execution_quality'] = 'EXCELLENT'
            summary['risk_level'] = 'LOW'
        elif score >= 50 and imbalance < 0.5:
            summary['execution_quality'] = 'GOOD'
            summary['risk_level'] = 'MODERATE'
        elif score >= 30:
            summary['execution_quality'] = 'FAIR'
            summary['risk_level'] = 'ELEVATED'
        else:
            summary['execution_quality'] = 'POOR'
            summary['risk_level'] = 'HIGH'
        
        if imbalance > 0.5:
            summary['recommendations'].append(
                f"High imbalance ({imbalance:.2%}) - consider order splitting"
            )
        
        if tblr and tblr.get('tblr_ratio', 1) < 0.6:
            summary['recommendations'].append(
                f"Slow recovery (TBLR={tblr['tblr_ratio']:.2%}) - use limit orders"
            )
        
        if hidden and hidden.get('is_significant'):
            summary['recommendations'].append(
                f"Hidden liquidity detected on {hidden['detected_side']} side"
            )
        
        if grade in ['D', 'F']:
            summary['recommendations'].append(
                "Poor liquidity - reduce position size or wait for improvement"
            )
        
        if not summary['recommendations']:
            summary['recommendations'].append("Conditions favorable for execution")
        
        return summary
    
    def get_metrics_summary(self, symbol: str) -> Dict[str, Any]:
        """Get quick metrics summary for a symbol"""
        snapshots = self._get_recent_snapshots(symbol)
        
        if not snapshots:
            return {'status': 'NO_DATA', 'symbol': symbol}
        
        latest = snapshots[-1]
        bid_depths = [s.bid_depth_usd for s in snapshots]
        ask_depths = [s.ask_depth_usd for s in snapshots]
        
        return {
            'status': 'OK',
            'symbol': symbol,
            'snapshot_count': len(snapshots),
            'latest_mid_price': latest.mid_price,
            'latest_spread_bps': round(latest.spread_bps, 2),
            'avg_bid_depth': round(np.mean(bid_depths), 2),
            'avg_ask_depth': round(np.mean(ask_depths), 2),
            'depth_volatility': round(np.std(bid_depths) / (np.mean(bid_depths) + 1), 4),
            'avg_imbalance': round(np.mean([s.depth_imbalance_ratio for s in snapshots]), 4)
        }
    
    def clear_history(self, symbol: Optional[str] = None) -> None:
        """Clear snapshot history"""
        with self._lock:
            if symbol:
                if symbol in self._snapshots:
                    self._snapshots[symbol].clear()
                    logger.info(f"Cleared history for {symbol}")
            else:
                self._snapshots.clear()
                logger.info("Cleared all snapshot history")
