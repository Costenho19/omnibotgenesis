"""
OMNIX V7.0 Generate Coherence Report Use Case
===============================================
Application service for generating coherence analysis reports.

This use case produces reports from the 6-Tier Coherence Engine:
1. Strategy votes aggregation
2. Consensus calculation
3. Veto analysis
4. Tier results summary
"""

from dataclasses import dataclass, field
from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime

from src.omnix.domain.support.market import (
    MarketSnapshot, StrategyVote, CoherenceResult, RegimeState,
)


class ICoherenceEnginePort(Protocol):
    """Port for coherence engine."""
    async def evaluate(self, pair: str, snapshot: MarketSnapshot) -> CoherenceResult:
        ...
    
    async def get_strategy_votes(self, pair: str, snapshot: MarketSnapshot) -> List[StrategyVote]:
        ...


class IMarketDataPort(Protocol):
    """Port for market data."""
    async def get_snapshot(self, pair: str) -> MarketSnapshot:
        ...


@dataclass
class CoherenceReportRequest:
    """Request for coherence report generation."""
    pair: str
    include_tier_details: bool = True
    include_vote_breakdown: bool = True


@dataclass
class TierResult:
    """Result from a single tier in the 6-tier system."""
    tier_number: int
    tier_name: str
    passed: bool
    score: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CoherenceReport:
    """Complete coherence analysis report."""
    pair: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    overall_passed: bool = False
    final_score: float = 0.0
    consensus_ratio: float = 0.0
    
    direction: str = ""
    recommended_action: str = "HOLD"
    
    bullish_votes: int = 0
    bearish_votes: int = 0
    neutral_votes: int = 0
    
    veto_active: bool = False
    veto_source: Optional[str] = None
    veto_reason: Optional[str] = None
    
    tier_results: List[TierResult] = field(default_factory=list)
    vote_breakdown: List[Dict[str, Any]] = field(default_factory=list)
    
    regime: Optional[str] = None
    volatility: float = 0.0
    liquidity_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pair": self.pair,
            "timestamp": self.timestamp.isoformat(),
            "overall_passed": self.overall_passed,
            "final_score": self.final_score,
            "consensus_ratio": self.consensus_ratio,
            "direction": self.direction,
            "recommended_action": self.recommended_action,
            "bullish_votes": self.bullish_votes,
            "bearish_votes": self.bearish_votes,
            "veto_active": self.veto_active,
            "veto_source": self.veto_source,
            "veto_reason": self.veto_reason,
            "tier_results": [
                {"tier": t.tier_number, "name": t.tier_name, "passed": t.passed, "score": t.score}
                for t in self.tier_results
            ],
            "regime": self.regime,
            "volatility": self.volatility,
        }


@dataclass
class GenerateCoherenceReportResponse:
    """Response from coherence report generation."""
    success: bool = True
    report: Optional[CoherenceReport] = None
    error: Optional[str] = None


class GenerateCoherenceReportUseCase:
    """
    Use case for generating coherence analysis reports.
    
    Produces detailed reports from the 6-Tier Coherence Engine.
    """
    
    TIER_NAMES = {
        1: "Technical Indicators",
        2: "Momentum Analysis",
        3: "Regime Detection",
        4: "Risk Assessment",
        5: "Non-Markovian Memory",
        6: "Final Consensus",
    }
    
    def __init__(
        self,
        coherence_engine: ICoherenceEnginePort,
        market_data: IMarketDataPort,
    ):
        self._coherence = coherence_engine
        self._market_data = market_data
    
    async def execute(self, request: CoherenceReportRequest) -> GenerateCoherenceReportResponse:
        """
        Generate a coherence analysis report for a trading pair.
        
        Args:
            request: Report parameters
            
        Returns:
            GenerateCoherenceReportResponse with the report
        """
        try:
            snapshot = await self._market_data.get_snapshot(request.pair)
            
            votes = await self._coherence.get_strategy_votes(request.pair, snapshot)
            
            coherence_result = await self._coherence.evaluate(request.pair, snapshot)
            
            report = self._build_report(
                pair=request.pair,
                snapshot=snapshot,
                votes=votes,
                coherence_result=coherence_result,
                include_tier_details=request.include_tier_details,
                include_vote_breakdown=request.include_vote_breakdown,
            )
            
            return GenerateCoherenceReportResponse(
                success=True,
                report=report,
            )
            
        except Exception as e:
            return GenerateCoherenceReportResponse(
                success=False,
                error=str(e),
            )
    
    def _build_report(
        self,
        pair: str,
        snapshot: MarketSnapshot,
        votes: List[StrategyVote],
        coherence_result: CoherenceResult,
        include_tier_details: bool,
        include_vote_breakdown: bool,
    ) -> CoherenceReport:
        """Build the coherence report from raw data."""
        bullish = sum(1 for v in votes if v.is_bullish)
        bearish = sum(1 for v in votes if v.is_bearish)
        neutral = len(votes) - bullish - bearish
        
        if bullish > bearish:
            direction = "BULLISH"
        elif bearish > bullish:
            direction = "BEARISH"
        else:
            direction = "NEUTRAL"
        
        if coherence_result.passed and coherence_result.final_score >= 12:
            if direction == "BULLISH":
                action = "BUY"
            elif direction == "BEARISH":
                action = "SELL"
            else:
                action = "HOLD"
        else:
            action = "HOLD"
        
        report = CoherenceReport(
            pair=pair,
            overall_passed=coherence_result.passed,
            final_score=coherence_result.final_score,
            consensus_ratio=coherence_result.consensus_ratio,
            direction=direction,
            recommended_action=action,
            bullish_votes=bullish,
            bearish_votes=bearish,
            neutral_votes=neutral,
            veto_active=coherence_result.veto_active,
            veto_source=coherence_result.veto_strategy,
            veto_reason=coherence_result.veto_reason,
            regime=snapshot.regime.regime.value if snapshot.regime else None,
            volatility=snapshot.volatility,
            liquidity_score=snapshot.liquidity_score,
        )
        
        if include_tier_details:
            for tier_num, passed in coherence_result.tier_results.items():
                tier_result = TierResult(
                    tier_number=tier_num,
                    tier_name=self.TIER_NAMES.get(tier_num, f"Tier {tier_num}"),
                    passed=passed,
                    score=0.0,
                )
                report.tier_results.append(tier_result)
        
        if include_vote_breakdown:
            for vote in votes:
                report.vote_breakdown.append({
                    "strategy": vote.strategy_name,
                    "direction": vote.direction,
                    "score": vote.score,
                    "confidence": vote.confidence,
                    "weight": vote.weight,
                    "weighted_score": vote.weighted_score,
                    "is_veto": vote.is_veto,
                })
        
        return report
