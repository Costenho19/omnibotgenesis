"""
OMNIX V7.0 Execution Port
=========================
Protocol definition for institutional-grade trade execution analysis.

Wraps legacy services:
- ExecutionProtocol (main orchestrator)
- LiquidityAnalyzer (orderbook analysis, TBLR)
- CorrelationEngine (cross-asset correlation)
- MicroVolatilityEngine (regime detection)

Migration Status: Phase 5 - New Ports Implementation
Feature Flag: USE_EXECUTION_PORT
"""

from typing import Protocol, Optional, List, Dict, Any, runtime_checkable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ExecutionStyle(Enum):
    """Execution algorithm selection."""
    MARKET = "market"
    LIMIT = "limit"
    TWAP = "twap"
    VWAP = "vwap"
    ICEBERG = "iceberg"
    POV = "pov"
    IMPLEMENTATION_SHORTFALL = "is"


class ExecutionUrgency(Enum):
    """Trade urgency classification."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    PASSIVE = "passive"


class MarketCondition(Enum):
    """Current market condition assessment."""
    FAVORABLE = "favorable"
    NEUTRAL = "neutral"
    ADVERSE = "adverse"
    CRISIS = "crisis"


class VolatilityRegime(Enum):
    """Market volatility regime."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXTREME = "extreme"


class ContagionLevel(Enum):
    """Contagion risk level classification."""
    LOW = "low"
    ELEVATED = "elevated"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class LiquidityReport:
    """Liquidity analysis for a trading pair."""
    symbol: str
    liquidity_score: float
    bid_depth_usd: float
    ask_depth_usd: float
    spread_bps: float
    depth_imbalance: float
    hidden_liquidity_detected: bool
    hidden_liquidity_confidence: float
    tblr_ratio: float
    optimal_order_size_usd: float
    impact_estimates: Dict[float, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_liquid(self) -> bool:
        return self.liquidity_score > 0.6


@dataclass
class VolatilityMetrics:
    """Micro-volatility regime metrics."""
    symbol: str
    regime: VolatilityRegime
    current_volatility: float
    volatility_percentile: float
    asymmetric_response: float
    regime_duration_hours: float
    stability_score: float
    predicted_direction: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CorrelationMatrix:
    """Cross-asset correlation analysis."""
    pairs: List[str]
    correlation_matrix: Dict[str, Dict[str, float]]
    breakdown_detected: bool
    breakdown_pairs: List[tuple]
    contagion_level: ContagionLevel
    contagion_index: float
    safe_haven_flow: str
    btc_dominance_trend: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SlippagePrediction:
    """Slippage estimation for trade execution."""
    expected_slippage_bps: float
    worst_case_slippage_bps: float
    best_case_slippage_bps: float
    confidence: float
    impact_by_size: Dict[float, float] = field(default_factory=dict)
    factors: Dict[str, float] = field(default_factory=dict)
    
    @property
    def expected_slippage_pct(self) -> float:
        return self.expected_slippage_bps / 100.0
    
    @property
    def is_acceptable(self) -> bool:
        return self.expected_slippage_bps < 50


@dataclass
class ExecutionTiming:
    """Optimal execution timing recommendation."""
    execute_now: bool
    delay_seconds: int
    reason: str
    optimal_window_start: Optional[datetime] = None
    optimal_window_end: Optional[datetime] = None
    avoid_periods: List[str] = field(default_factory=list)
    confidence: float = 0.5


@dataclass
class ExecutionOrder:
    """Order request for execution analysis."""
    symbol: str
    side: str
    size_usd: float
    urgency: ExecutionUrgency = ExecutionUrgency.NORMAL
    max_slippage_bps: float = 50.0
    prefer_passive: bool = False
    split_allowed: bool = True
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Complete execution recommendation."""
    order: ExecutionOrder
    recommended_style: ExecutionStyle
    market_condition: MarketCondition
    liquidity: LiquidityReport
    volatility: VolatilityMetrics
    slippage: SlippagePrediction
    timing: ExecutionTiming
    correlation_risk: float
    contagion_risk: float
    proceed_recommended: bool
    warnings: List[str] = field(default_factory=list)
    suggested_splits: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)


@runtime_checkable
class ExecutionPort(Protocol):
    """
    Protocol for institutional-grade trade execution analysis.
    
    Provides:
    - Execution Decision Matrix (TWAP/VWAP/ICEBERG/MARKET)
    - Slippage prediction model
    - Optimal execution timing
    - Pre-trade analytics
    
    SOLID Principles:
    - SRP: Only execution analysis and routing
    - ISP: Focused interface for execution operations
    - DIP: High-level code depends on this abstraction
    
    Feature Flag: USE_EXECUTION_PORT
    Fallback: Direct calls to legacy ExecutionProtocol
    """
    
    def evaluate_liquidity(
        self,
        symbol: str,
        order_size_usd: Optional[float] = None
    ) -> LiquidityReport:
        """
        Analyze liquidity for a trading pair.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            order_size_usd: Optional order size for impact estimation
            
        Returns:
            LiquidityReport with depth, spread, and hidden liquidity analysis
        """
        ...
    
    def assess_correlation(
        self,
        pairs: List[str],
        window_hours: int = 24
    ) -> CorrelationMatrix:
        """
        Analyze cross-asset correlations and contagion risk.
        
        Args:
            pairs: List of trading pairs to analyze
            window_hours: Lookback window for correlation
            
        Returns:
            CorrelationMatrix with breakdown detection and contagion index
        """
        ...
    
    def compute_micro_volatility(
        self,
        symbol: str,
        window_minutes: int = 60
    ) -> VolatilityMetrics:
        """
        Compute micro-volatility regime metrics.
        
        Args:
            symbol: Trading pair
            window_minutes: Analysis window
            
        Returns:
            VolatilityMetrics with regime and asymmetric response
        """
        ...
    
    def predict_slippage(
        self,
        symbol: str,
        side: str,
        size_usd: float
    ) -> SlippagePrediction:
        """
        Predict slippage for a potential trade.
        
        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            size_usd: Order size in USD
            
        Returns:
            SlippagePrediction with expected, worst, best case
        """
        ...
    
    def get_optimal_timing(
        self,
        symbol: str,
        urgency: ExecutionUrgency = ExecutionUrgency.NORMAL
    ) -> ExecutionTiming:
        """
        Get optimal execution timing recommendation.
        
        Args:
            symbol: Trading pair
            urgency: How urgent is execution
            
        Returns:
            ExecutionTiming with recommendation and windows
        """
        ...
    
    def route_execution(
        self,
        order: ExecutionOrder
    ) -> ExecutionResult:
        """
        Full execution analysis and routing recommendation.
        
        Args:
            order: ExecutionOrder with all parameters
            
        Returns:
            ExecutionResult with complete recommendation
        """
        ...
    
    def get_market_condition(
        self,
        symbol: str
    ) -> MarketCondition:
        """
        Get current market condition assessment.
        
        Args:
            symbol: Trading pair
            
        Returns:
            MarketCondition enum value
        """
        ...
    
    def get_execution_summary(
        self,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Get quick execution summary for a symbol.
        
        Args:
            symbol: Trading pair
            
        Returns:
            Dict with key execution metrics
        """
        ...
    
    def is_execution_safe(
        self,
        symbol: str,
        size_usd: float
    ) -> tuple:
        """
        Quick safety check for execution.
        
        Args:
            symbol: Trading pair
            size_usd: Order size
            
        Returns:
            Tuple of (is_safe: bool, reason: str)
        """
        ...
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of execution services.
        
        Returns:
            Dict with:
            - healthy: bool
            - components: Dict[str, bool] (liquidity, correlation, volatility)
            - symbols_tracked: int
            - last_update: datetime
        """
        ...
