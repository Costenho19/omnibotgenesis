"""
OMNIX V7.0 - RiskControlPort Protocol
======================================
Port for risk management and control operations.

Wraps legacy services:
- circuit_breaker_manager.py
- limits_engine.py
- position_monitor.py
- alert_dispatcher.py

Feature flag: USE_RISK_CONTROL_PORT
"""

from typing import Protocol, Optional, List, Dict, Any, runtime_checkable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class RiskLevel(Enum):
    """Risk severity classification."""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    EXTREME = "extreme"


class CircuitBreakerState(Enum):
    """Circuit breaker state."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class AlertPriority(Enum):
    """Alert priority levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LimitType(Enum):
    """Types of trading limits."""
    POSITION_SIZE = "position_size"
    DAILY_LOSS = "daily_loss"
    DRAWDOWN = "drawdown"
    LEVERAGE = "leverage"
    CONCENTRATION = "concentration"
    CORRELATION = "correlation"


@dataclass
class RiskAssessmentRequest:
    """Request for risk assessment."""
    symbol: str
    side: str  # 'buy' or 'sell'
    size_usd: float
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    urgency: str = "normal"
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskDecision:
    """Risk assessment decision."""
    approved: bool
    risk_level: RiskLevel
    score: float  # 0-100, lower is safer
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    adjustments: Dict[str, Any] = field(default_factory=dict)
    max_allowed_size: Optional[float] = None
    recommended_stop_loss: Optional[float] = None
    veto_source: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_blocked(self) -> bool:
        """Check if trade is blocked (not approved)."""
        return not self.approved
    
    @property
    def is_high_risk(self) -> bool:
        """Check if risk level is high or above."""
        return self.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.EXTREME]


@dataclass
class CircuitBreakEvent:
    """Circuit breaker event."""
    breaker_id: str
    state: CircuitBreakerState
    trigger_reason: str
    triggered_at: datetime
    auto_recovery_at: Optional[datetime] = None
    affected_symbols: List[str] = field(default_factory=list)
    metrics_at_trigger: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_active(self) -> bool:
        """Check if circuit breaker is currently blocking."""
        return self.state == CircuitBreakerState.OPEN


@dataclass
class LimitStatus:
    """Status of a trading limit."""
    limit_type: LimitType
    limit_value: float
    current_value: float
    utilization_pct: float
    is_breached: bool
    headroom: float
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def is_near_limit(self) -> bool:
        """Check if near the limit (>80% utilized)."""
        return self.utilization_pct > 80.0


@dataclass
class PositionRisk:
    """Risk metrics for a single position."""
    symbol: str
    side: str
    size_usd: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    risk_score: float
    distance_to_stop_pct: Optional[float] = None
    time_in_position_hours: float = 0.0
    correlation_risk: float = 0.0
    liquidity_risk: float = 0.0


@dataclass
class PortfolioRiskSummary:
    """Portfolio-level risk summary."""
    total_exposure_usd: float
    net_exposure_usd: float
    gross_exposure_usd: float
    position_count: int
    long_count: int
    short_count: int
    total_unrealized_pnl: float
    max_single_position_pct: float
    concentration_score: float  # 0-100, higher is more concentrated
    correlation_risk_score: float  # 0-100
    overall_risk_level: RiskLevel
    warnings: List[str] = field(default_factory=list)


@dataclass
class Alert:
    """Risk alert."""
    alert_id: str
    priority: AlertPriority
    category: str
    title: str
    message: str
    created_at: datetime
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    related_symbol: Optional[str] = None
    action_required: bool = False
    suggested_action: Optional[str] = None


@runtime_checkable
class RiskControlPort(Protocol):
    """
    Port for risk management and control.
    
    Provides:
    - Trade risk assessment and approval
    - Circuit breaker management
    - Position monitoring
    - Limit enforcement
    - Alert dispatching
    """
    
    def assess_trade_risk(
        self,
        request: RiskAssessmentRequest
    ) -> RiskDecision:
        """
        Assess risk for a proposed trade.
        
        Args:
            request: Trade details to assess
            
        Returns:
            RiskDecision with approval status and details
        """
        ...
    
    def get_circuit_breaker_status(
        self,
        breaker_id: Optional[str] = None
    ) -> List[CircuitBreakEvent]:
        """
        Get circuit breaker status.
        
        Args:
            breaker_id: Specific breaker ID or None for all
            
        Returns:
            List of circuit breaker events
        """
        ...
    
    def trip_circuit_breaker(
        self,
        breaker_id: str,
        reason: str,
        duration_minutes: int = 60
    ) -> CircuitBreakEvent:
        """
        Manually trip a circuit breaker.
        
        Args:
            breaker_id: Breaker to trip
            reason: Reason for tripping
            duration_minutes: How long to keep open
            
        Returns:
            The created circuit break event
        """
        ...
    
    def reset_circuit_breaker(
        self,
        breaker_id: str
    ) -> bool:
        """
        Reset a circuit breaker to closed state.
        
        Args:
            breaker_id: Breaker to reset
            
        Returns:
            True if successfully reset
        """
        ...
    
    def get_limit_status(
        self,
        limit_type: Optional[LimitType] = None
    ) -> List[LimitStatus]:
        """
        Get current status of trading limits.
        
        Args:
            limit_type: Specific limit or None for all
            
        Returns:
            List of limit statuses
        """
        ...
    
    def check_limits(
        self,
        symbol: str,
        side: str,
        size_usd: float
    ) -> tuple[bool, List[str]]:
        """
        Check if a trade would breach any limits.
        
        Args:
            symbol: Asset symbol
            side: 'buy' or 'sell'
            size_usd: Position size in USD
            
        Returns:
            (is_within_limits, list of breached limit descriptions)
        """
        ...
    
    def get_position_risks(
        self,
        symbols: Optional[List[str]] = None
    ) -> List[PositionRisk]:
        """
        Get risk metrics for open positions.
        
        Args:
            symbols: Filter by symbols or None for all
            
        Returns:
            List of position risk metrics
        """
        ...
    
    def get_portfolio_risk_summary(self) -> PortfolioRiskSummary:
        """
        Get portfolio-level risk summary.
        
        Returns:
            Portfolio risk summary
        """
        ...
    
    def dispatch_alert(
        self,
        priority: AlertPriority,
        category: str,
        title: str,
        message: str,
        symbol: Optional[str] = None,
        action_required: bool = False
    ) -> Alert:
        """
        Dispatch a risk alert.
        
        Args:
            priority: Alert priority
            category: Alert category
            title: Short title
            message: Full message
            symbol: Related symbol if applicable
            action_required: If user action is needed
            
        Returns:
            The created alert
        """
        ...
    
    def get_recent_alerts(
        self,
        hours: int = 24,
        priority: Optional[AlertPriority] = None
    ) -> List[Alert]:
        """
        Get recent alerts.
        
        Args:
            hours: How far back to look
            priority: Filter by priority
            
        Returns:
            List of alerts
        """
        ...
    
    def acknowledge_alert(
        self,
        alert_id: str
    ) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert to acknowledge
            
        Returns:
            True if successfully acknowledged
        """
        ...
    
    def is_trading_allowed(self) -> tuple[bool, str]:
        """
        Check if trading is currently allowed.
        
        Returns:
            (is_allowed, reason if not allowed)
        """
        ...
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of risk control components.
        
        Returns:
            Health status dictionary
        """
        ...
