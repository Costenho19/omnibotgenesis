"""
OMNIX V7.0 - DerivativesPort Protocol
======================================
Port for derivatives and hedging operations.

Wraps legacy services:
- derivatives_manager.py
- kraken_futures_client.py
- hedging_service.py
- options_pricer.py

Feature flag: USE_DERIVATIVES_PORT
"""

from typing import Protocol, Optional, List, Dict, Any, runtime_checkable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ContractType(Enum):
    """Derivatives contract types."""
    PERPETUAL = "perpetual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    OPTION_CALL = "option_call"
    OPTION_PUT = "option_put"


class HedgeType(Enum):
    """Types of hedging strategies."""
    DELTA_NEUTRAL = "delta_neutral"
    PROTECTIVE_PUT = "protective_put"
    COVERED_CALL = "covered_call"
    COLLAR = "collar"
    INVERSE = "inverse"


class MarginType(Enum):
    """Margin types."""
    ISOLATED = "isolated"
    CROSS = "cross"


class PositionMode(Enum):
    """Position modes."""
    ONE_WAY = "one_way"
    HEDGE = "hedge"


@dataclass
class FuturesContract:
    """Futures contract information."""
    symbol: str
    contract_type: ContractType
    underlying: str
    expiry: Optional[datetime] = None
    mark_price: float = 0.0
    index_price: float = 0.0
    funding_rate: float = 0.0
    next_funding_time: Optional[datetime] = None
    open_interest: float = 0.0
    volume_24h: float = 0.0
    
    @property
    def is_perpetual(self) -> bool:
        """Check if perpetual contract."""
        return self.contract_type == ContractType.PERPETUAL
    
    @property
    def premium_pct(self) -> float:
        """Calculate premium/discount vs index."""
        if self.index_price > 0:
            return ((self.mark_price / self.index_price) - 1) * 100
        return 0.0


@dataclass
class DerivativesPosition:
    """Derivatives position."""
    symbol: str
    contract_type: ContractType
    side: str  # 'long' or 'short'
    size: float
    size_usd: float
    entry_price: float
    mark_price: float
    liquidation_price: Optional[float] = None
    margin_used: float = 0.0
    margin_type: MarginType = MarginType.CROSS
    leverage: float = 1.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    funding_payment_accumulated: float = 0.0
    
    @property
    def is_profitable(self) -> bool:
        """Check if position is in profit."""
        return self.unrealized_pnl > 0


@dataclass
class MarginStatus:
    """Margin account status."""
    total_collateral_usd: float
    available_margin_usd: float
    used_margin_usd: float
    maintenance_margin_usd: float
    margin_ratio: float  # 0-100%
    account_leverage: float
    liquidation_risk: float  # 0-100%
    margin_type: MarginType = MarginType.CROSS
    
    @property
    def is_safe(self) -> bool:
        """Check if margin is safe (ratio > 50%)."""
        return self.margin_ratio > 50.0
    
    @property
    def is_critical(self) -> bool:
        """Check if margin is critical (ratio < 20%)."""
        return self.margin_ratio < 20.0


@dataclass
class HedgeOrder:
    """Hedge order details."""
    hedge_id: str
    hedge_type: HedgeType
    spot_symbol: str
    hedge_symbol: str
    spot_size_usd: float
    hedge_size_usd: float
    hedge_ratio: float
    entry_price: float
    target_delta: float = 0.0
    current_delta: float = 0.0
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def is_balanced(self) -> bool:
        """Check if hedge is balanced (delta near target)."""
        return abs(self.current_delta - self.target_delta) < 0.1


@dataclass
class HedgeRecommendation:
    """Recommendation for hedging."""
    should_hedge: bool
    hedge_type: HedgeType
    recommended_size_usd: float
    recommended_instrument: str
    reason: str
    urgency: str = "normal"
    estimated_cost_usd: float = 0.0


@dataclass
class FundingAnalysis:
    """Analysis of funding rates."""
    symbol: str
    current_rate: float
    predicted_rate_8h: float
    rate_trend: str  # 'rising', 'falling', 'stable'
    annualized_rate: float
    is_favorable_long: bool
    is_favorable_short: bool
    recommendation: str


@dataclass
class DerivativesSummary:
    """Summary of derivatives positions and metrics."""
    total_positions: int
    total_notional_usd: float
    total_unrealized_pnl: float
    net_delta: float
    total_funding_paid_24h: float
    margin_utilization_pct: float
    largest_position_pct: float
    positions: List[DerivativesPosition] = field(default_factory=list)


@runtime_checkable
class DerivativesPort(Protocol):
    """
    Port for derivatives trading and hedging.
    
    Provides:
    - Futures contract information
    - Position management
    - Margin monitoring
    - Hedging strategies
    - Funding rate analysis
    """
    
    def get_futures_contracts(
        self,
        underlying: Optional[str] = None
    ) -> List[FuturesContract]:
        """
        Get available futures contracts.
        
        Args:
            underlying: Filter by underlying asset
            
        Returns:
            List of futures contracts
        """
        ...
    
    def get_contract_info(
        self,
        symbol: str
    ) -> Optional[FuturesContract]:
        """
        Get info for a specific contract.
        
        Args:
            symbol: Contract symbol
            
        Returns:
            Contract info or None if not found
        """
        ...
    
    def get_derivatives_positions(
        self,
        symbols: Optional[List[str]] = None
    ) -> List[DerivativesPosition]:
        """
        Get current derivatives positions.
        
        Args:
            symbols: Filter by symbols
            
        Returns:
            List of derivatives positions
        """
        ...
    
    def get_margin_status(self) -> MarginStatus:
        """
        Get margin account status.
        
        Returns:
            Margin status
        """
        ...
    
    def calculate_hedge_requirement(
        self,
        spot_symbol: str,
        spot_size_usd: float,
        target_delta: float = 0.0
    ) -> HedgeRecommendation:
        """
        Calculate hedging requirement for a spot position.
        
        Args:
            spot_symbol: Spot asset symbol
            spot_size_usd: Spot position size
            target_delta: Target delta exposure
            
        Returns:
            Hedge recommendation
        """
        ...
    
    def execute_hedge(
        self,
        recommendation: HedgeRecommendation
    ) -> HedgeOrder:
        """
        Execute a hedge based on recommendation.
        
        Args:
            recommendation: Hedge recommendation
            
        Returns:
            Created hedge order
        """
        ...
    
    def get_active_hedges(self) -> List[HedgeOrder]:
        """
        Get active hedge orders.
        
        Returns:
            List of active hedges
        """
        ...
    
    def rebalance_hedge(
        self,
        hedge_id: str
    ) -> HedgeOrder:
        """
        Rebalance an existing hedge.
        
        Args:
            hedge_id: Hedge to rebalance
            
        Returns:
            Updated hedge order
        """
        ...
    
    def analyze_funding_rates(
        self,
        symbols: Optional[List[str]] = None
    ) -> List[FundingAnalysis]:
        """
        Analyze funding rates for opportunities.
        
        Args:
            symbols: Symbols to analyze
            
        Returns:
            Funding analysis for each symbol
        """
        ...
    
    def get_derivatives_summary(self) -> DerivativesSummary:
        """
        Get summary of derivatives exposure.
        
        Returns:
            Derivatives summary
        """
        ...
    
    def set_leverage(
        self,
        symbol: str,
        leverage: float
    ) -> bool:
        """
        Set leverage for a symbol.
        
        Args:
            symbol: Contract symbol
            leverage: Target leverage
            
        Returns:
            True if successfully set
        """
        ...
    
    def set_margin_type(
        self,
        symbol: str,
        margin_type: MarginType
    ) -> bool:
        """
        Set margin type for a symbol.
        
        Args:
            symbol: Contract symbol
            margin_type: Isolated or Cross
            
        Returns:
            True if successfully set
        """
        ...
    
    def is_derivatives_available(self) -> tuple[bool, str]:
        """
        Check if derivatives trading is available.
        
        Returns:
            (is_available, reason if not)
        """
        ...
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of derivatives services.
        
        Returns:
            Health status dictionary
        """
        ...
