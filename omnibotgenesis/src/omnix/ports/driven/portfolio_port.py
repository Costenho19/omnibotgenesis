"""
OMNIX V7.0 - PortfolioPort Protocol
====================================
Port for portfolio management and exposure control.

Wraps legacy services:
- portfolio_engine.py
- portfolio_optimizer.py
- exposure_manager.py
- rebalancer.py

Feature flag: USE_PORTFOLIO_PORT
"""

from typing import Protocol, Optional, List, Dict, Any, runtime_checkable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AssetClass(Enum):
    """Asset class types."""
    CRYPTO = "crypto"
    STOCKS = "stocks"
    FOREX = "forex"
    COMMODITIES = "commodities"
    DERIVATIVES = "derivatives"
    STABLECOINS = "stablecoins"


class RebalanceStrategy(Enum):
    """Portfolio rebalancing strategies."""
    THRESHOLD = "threshold"
    CALENDAR = "calendar"
    TACTICAL = "tactical"
    MOMENTUM = "momentum"
    RISK_PARITY = "risk_parity"


class ExposureType(Enum):
    """Types of portfolio exposure."""
    GROSS = "gross"
    NET = "net"
    LONG = "long"
    SHORT = "short"
    DELTA = "delta"


@dataclass
class PortfolioPosition:
    """Individual portfolio position."""
    symbol: str
    asset_class: AssetClass
    quantity: float
    avg_entry_price: float
    current_price: float
    market_value_usd: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    weight_pct: float
    target_weight_pct: Optional[float] = None
    deviation_pct: Optional[float] = None
    side: str = "long"
    
    @property
    def is_overweight(self) -> bool:
        """Check if position is overweight vs target."""
        if self.target_weight_pct is None:
            return False
        return self.weight_pct > self.target_weight_pct * 1.1
    
    @property
    def is_underweight(self) -> bool:
        """Check if position is underweight vs target."""
        if self.target_weight_pct is None:
            return False
        return self.weight_pct < self.target_weight_pct * 0.9


@dataclass
class PortfolioView:
    """Complete portfolio view."""
    total_value_usd: float
    cash_usd: float
    invested_usd: float
    positions: List[PortfolioPosition]
    position_count: int
    asset_allocation: Dict[str, float]
    unrealized_pnl: float
    unrealized_pnl_pct: float
    realized_pnl_today: float
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def cash_pct(self) -> float:
        """Cash percentage of portfolio."""
        if self.total_value_usd > 0:
            return (self.cash_usd / self.total_value_usd) * 100
        return 100.0


@dataclass
class ExposureReport:
    """Portfolio exposure report."""
    gross_exposure_usd: float
    net_exposure_usd: float
    long_exposure_usd: float
    short_exposure_usd: float
    leverage: float
    beta: float
    delta_exposure: float
    sector_exposure: Dict[str, float]
    asset_class_exposure: Dict[str, float]
    geographic_exposure: Dict[str, float]
    concentration_top5_pct: float
    correlation_with_market: float


@dataclass
class RebalanceOrder:
    """Individual rebalance order."""
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    current_weight_pct: float
    target_weight_pct: float
    estimated_value_usd: float
    priority: int = 0
    reason: str = ""


@dataclass
class RebalanceCommand:
    """Rebalancing command with orders."""
    command_id: str
    strategy: RebalanceStrategy
    orders: List[RebalanceOrder]
    total_buy_usd: float
    total_sell_usd: float
    net_flow_usd: float
    estimated_cost_usd: float
    drift_before_pct: float
    drift_after_pct: float
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def is_neutral(self) -> bool:
        """Check if rebalance is cash-neutral."""
        return abs(self.net_flow_usd) < 100


@dataclass
class TargetAllocation:
    """Target portfolio allocation."""
    symbol: str
    target_weight_pct: float
    min_weight_pct: float = 0.0
    max_weight_pct: float = 100.0
    asset_class: AssetClass = AssetClass.CRYPTO
    rebalance_threshold_pct: float = 5.0


@dataclass
class AllocationPlan:
    """Complete allocation plan."""
    plan_id: str
    name: str
    targets: List[TargetAllocation]
    rebalance_strategy: RebalanceStrategy
    rebalance_frequency_hours: int = 24
    last_rebalance: Optional[datetime] = None
    is_active: bool = True


@runtime_checkable
class PortfolioPort(Protocol):
    """
    Port for portfolio management.
    
    Provides:
    - Portfolio view and positions
    - Exposure management
    - Rebalancing
    - Allocation planning
    """
    
    def get_portfolio_view(
        self,
        include_derivatives: bool = False
    ) -> PortfolioView:
        """
        Get current portfolio view.
        
        Args:
            include_derivatives: Include derivatives positions
            
        Returns:
            Complete portfolio view
        """
        ...
    
    def get_positions(
        self,
        asset_class: Optional[AssetClass] = None,
        symbols: Optional[List[str]] = None
    ) -> List[PortfolioPosition]:
        """
        Get portfolio positions.
        
        Args:
            asset_class: Filter by asset class
            symbols: Filter by symbols
            
        Returns:
            List of positions
        """
        ...
    
    def get_exposure_report(self) -> ExposureReport:
        """
        Get portfolio exposure report.
        
        Returns:
            Exposure report
        """
        ...
    
    def calculate_rebalance(
        self,
        strategy: RebalanceStrategy = RebalanceStrategy.THRESHOLD,
        targets: Optional[List[TargetAllocation]] = None
    ) -> RebalanceCommand:
        """
        Calculate rebalancing orders.
        
        Args:
            strategy: Rebalancing strategy
            targets: Target allocations (or use active plan)
            
        Returns:
            Rebalance command with orders
        """
        ...
    
    def execute_rebalance(
        self,
        command: RebalanceCommand
    ) -> RebalanceCommand:
        """
        Execute a rebalance command.
        
        Args:
            command: Rebalance command to execute
            
        Returns:
            Updated command with execution status
        """
        ...
    
    def get_allocation_plan(
        self,
        plan_id: Optional[str] = None
    ) -> Optional[AllocationPlan]:
        """
        Get allocation plan.
        
        Args:
            plan_id: Specific plan ID or None for active plan
            
        Returns:
            Allocation plan
        """
        ...
    
    def set_allocation_plan(
        self,
        plan: AllocationPlan
    ) -> bool:
        """
        Set or update allocation plan.
        
        Args:
            plan: Allocation plan
            
        Returns:
            True if successfully set
        """
        ...
    
    def get_drift_analysis(self) -> Dict[str, Any]:
        """
        Get portfolio drift analysis.
        
        Returns:
            Drift analysis with deviations from targets
        """
        ...
    
    def get_performance_metrics(
        self,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get portfolio performance metrics.
        
        Args:
            period_days: Analysis period
            
        Returns:
            Performance metrics dict
        """
        ...
    
    def get_correlation_matrix(
        self,
        symbols: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Get correlation matrix for positions.
        
        Args:
            symbols: Specific symbols or all
            
        Returns:
            Correlation matrix
        """
        ...
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of portfolio services.
        
        Returns:
            Health status dictionary
        """
        ...
