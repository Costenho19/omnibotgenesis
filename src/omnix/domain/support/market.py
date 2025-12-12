"""
OMNIX V7.0 Market Support Entities
===================================
Supporting entities for market data and strategy coordination.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List


class MarketRegime(Enum):
    """Market regime states detected by HMM."""
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"
    UNKNOWN = "unknown"
    
    @property
    def is_bullish(self) -> bool:
        """Check if regime favors long positions."""
        return self in (MarketRegime.TRENDING_BULL, MarketRegime.BREAKOUT)
    
    @property
    def is_bearish(self) -> bool:
        """Check if regime favors short positions."""
        return self in (MarketRegime.TRENDING_BEAR, MarketRegime.REVERSAL)
    
    @property
    def is_neutral(self) -> bool:
        """Check if regime is neutral."""
        return self in (MarketRegime.RANGING, MarketRegime.UNKNOWN)
    
    @property
    def allows_trading(self) -> bool:
        """Check if regime allows trading (not too volatile)."""
        return self != MarketRegime.HIGH_VOLATILITY


@dataclass
class RegimeState:
    """
    Current market regime state with confidence.
    
    Output from HMM Regime detector.
    """
    regime: MarketRegime = MarketRegime.UNKNOWN
    confidence: float = 0.0
    strength: float = 0.0
    
    transition_probability: float = 0.0
    previous_regime: Optional[MarketRegime] = None
    
    detected_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_confident(self, threshold: float = 0.6) -> bool:
        """Check if regime detection is confident enough."""
        return self.confidence >= threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "regime": self.regime.value,
            "confidence": self.confidence,
            "strength": self.strength,
            "transition_probability": self.transition_probability,
            "previous_regime": self.previous_regime.value if self.previous_regime else None,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
        }


@dataclass
class MarketSnapshot:
    """
    Point-in-time snapshot of market data.
    
    Used for strategy analysis and decision logging.
    """
    pair: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    price: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    spread: float = 0.0
    
    volume_24h: float = 0.0
    change_24h: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0
    
    volatility: float = 0.0
    atr: float = 0.0
    
    regime: RegimeState = field(default_factory=RegimeState)
    
    fear_greed_index: Optional[int] = None
    sentiment: Optional[str] = None
    
    orderbook_imbalance: float = 0.0
    liquidity_score: float = 1.0
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def spread_pct(self) -> float:
        """Calculate spread as percentage of price."""
        if self.price == 0:
            return 0.0
        return (self.spread / self.price) * 100
    
    @property
    def is_liquid(self) -> bool:
        """Check if market is sufficiently liquid."""
        return self.liquidity_score >= 0.5 and self.spread_pct < 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pair": self.pair,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "price": self.price,
            "bid": self.bid,
            "ask": self.ask,
            "spread": self.spread,
            "spread_pct": self.spread_pct,
            "volume_24h": self.volume_24h,
            "change_24h": self.change_24h,
            "volatility": self.volatility,
            "regime": self.regime.to_dict(),
            "fear_greed_index": self.fear_greed_index,
            "liquidity_score": self.liquidity_score,
        }


@dataclass
class StrategyVote:
    """
    Vote from a single strategy in the Coherence Engine.
    
    Represents one component of the 6-tier veto system.
    """
    strategy_name: str = ""
    direction: str = ""
    score: float = 0.0
    confidence: float = 0.0
    weight: float = 1.0
    
    tier: int = 1
    is_veto: bool = False
    veto_reason: Optional[str] = None
    
    signals: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def weighted_score(self) -> float:
        """Calculate weight-adjusted score."""
        return self.score * self.weight
    
    @property
    def is_bullish(self) -> bool:
        """Check if vote is bullish."""
        return self.direction.lower() in ("buy", "long", "bullish")
    
    @property
    def is_bearish(self) -> bool:
        """Check if vote is bearish."""
        return self.direction.lower() in ("sell", "short", "bearish")
    
    def agrees_with(self, other: "StrategyVote") -> bool:
        """Check if this vote agrees with another."""
        return self.is_bullish == other.is_bullish
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "strategy_name": self.strategy_name,
            "direction": self.direction,
            "score": self.score,
            "confidence": self.confidence,
            "weight": self.weight,
            "weighted_score": self.weighted_score,
            "tier": self.tier,
            "is_veto": self.is_veto,
            "veto_reason": self.veto_reason,
            "signals": self.signals,
        }


@dataclass
class CoherenceResult:
    """
    Result of Coherence Engine evaluation.
    
    Aggregates strategy votes and determines final decision.
    """
    pair: str = ""
    passed: bool = False
    final_score: float = 0.0
    
    votes: List[StrategyVote] = field(default_factory=list)
    consensus_ratio: float = 0.0
    
    veto_active: bool = False
    veto_strategy: Optional[str] = None
    veto_reason: Optional[str] = None
    
    tier_results: Dict[int, bool] = field(default_factory=dict)
    
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def vote_count(self) -> int:
        """Total number of votes."""
        return len(self.votes)
    
    @property
    def bullish_count(self) -> int:
        """Count of bullish votes."""
        return sum(1 for v in self.votes if v.is_bullish)
    
    @property
    def bearish_count(self) -> int:
        """Count of bearish votes."""
        return sum(1 for v in self.votes if v.is_bearish)
    
    def add_vote(self, vote: StrategyVote) -> None:
        """Add a strategy vote."""
        self.votes.append(vote)
        if vote.is_veto:
            self.veto_active = True
            self.veto_strategy = vote.strategy_name
            self.veto_reason = vote.veto_reason
    
    def calculate_consensus(self) -> float:
        """Calculate consensus ratio among votes."""
        if not self.votes:
            return 0.0
        
        bullish = self.bullish_count
        bearish = self.bearish_count
        total = len(self.votes)
        
        majority = max(bullish, bearish)
        self.consensus_ratio = majority / total if total > 0 else 0.0
        return self.consensus_ratio
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pair": self.pair,
            "passed": self.passed,
            "final_score": self.final_score,
            "consensus_ratio": self.consensus_ratio,
            "vote_count": self.vote_count,
            "bullish_count": self.bullish_count,
            "bearish_count": self.bearish_count,
            "veto_active": self.veto_active,
            "veto_strategy": self.veto_strategy,
            "veto_reason": self.veto_reason,
            "tier_results": self.tier_results,
            "votes": [v.to_dict() for v in self.votes],
        }
