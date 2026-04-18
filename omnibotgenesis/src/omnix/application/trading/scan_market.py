"""
OMNIX V7.0 Scan Market Use Case
=================================
Application service for scanning markets and generating signals.

This use case orchestrates the signal generation pipeline:
1. Fetch market data for all pairs
2. Run each strategy analyzer
3. Aggregate votes into coherence scoring
4. Filter actionable signals
"""

from dataclasses import dataclass, field
from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime

from src.omnix.domain.trading.entities import Signal, SignalStrength, TradeDirection
from src.omnix.domain.support.market import MarketSnapshot, StrategyVote, CoherenceResult


class IMarketDataPort(Protocol):
    """Port for market data access."""
    async def get_snapshot(self, pair: str) -> MarketSnapshot:
        ...
    
    async def get_tradable_pairs(self) -> List[str]:
        ...


class IStrategyPort(Protocol):
    """Port for strategy analysis."""
    async def analyze(self, pair: str, snapshot: MarketSnapshot) -> StrategyVote:
        ...


class ICoherencePort(Protocol):
    """Port for coherence evaluation."""
    async def evaluate(self, pair: str, votes: List[StrategyVote]) -> CoherenceResult:
        ...


class ISignalRepositoryPort(Protocol):
    """Port for signal persistence."""
    async def save(self, signal: Signal) -> None:
        ...


@dataclass
class ScanMarketRequest:
    """Request to scan markets."""
    pairs: Optional[List[str]] = None
    min_strength: SignalStrength = SignalStrength.STRONG
    max_signals: int = 5


@dataclass
class ScanMarketResponse:
    """Response from market scan."""
    signals: List[Signal] = field(default_factory=list)
    scanned_pairs: int = 0
    scan_duration_ms: float = 0.0
    errors: List[str] = field(default_factory=list)


class ScanMarketUseCase:
    """
    Use case for scanning markets and generating trading signals.
    
    Coordinates market data, strategy analysis, and coherence evaluation.
    """
    
    def __init__(
        self,
        market_data: IMarketDataPort,
        strategies: List[IStrategyPort],
        coherence: ICoherencePort,
        signal_repository: Optional[ISignalRepositoryPort] = None,
    ):
        self._market_data = market_data
        self._strategies = strategies
        self._coherence = coherence
        self._signal_repository = signal_repository
    
    async def execute(self, request: ScanMarketRequest) -> ScanMarketResponse:
        """
        Scan markets and generate signals.
        
        Args:
            request: Scan parameters
            
        Returns:
            ScanMarketResponse with generated signals
        """
        start_time = datetime.utcnow()
        response = ScanMarketResponse()
        
        try:
            if request.pairs:
                pairs = request.pairs
            else:
                pairs = await self._market_data.get_tradable_pairs()
            
            response.scanned_pairs = len(pairs)
            
            for pair in pairs:
                try:
                    signal = await self._analyze_pair(pair, request.min_strength)
                    if signal and signal.is_actionable():
                        response.signals.append(signal)
                        
                        if self._signal_repository:
                            await self._signal_repository.save(signal)
                        
                        if len(response.signals) >= request.max_signals:
                            break
                            
                except Exception as e:
                    response.errors.append(f"{pair}: {str(e)}")
            
            response.signals.sort(key=lambda s: s.score, reverse=True)
            
        except Exception as e:
            response.errors.append(f"Scan failed: {str(e)}")
        
        end_time = datetime.utcnow()
        response.scan_duration_ms = (end_time - start_time).total_seconds() * 1000
        
        return response
    
    async def _analyze_pair(
        self,
        pair: str,
        min_strength: SignalStrength,
    ) -> Optional[Signal]:
        """Analyze a single pair through the strategy pipeline."""
        snapshot = await self._market_data.get_snapshot(pair)
        
        votes: List[StrategyVote] = []
        for strategy in self._strategies:
            try:
                vote = await strategy.analyze(pair, snapshot)
                votes.append(vote)
            except Exception:
                pass
        
        if not votes:
            return None
        
        coherence_result = await self._coherence.evaluate(pair, votes)
        
        if not coherence_result.passed:
            return None
        
        direction = self._determine_direction(votes)
        score = coherence_result.final_score
        strength = SignalStrength.from_score(score)
        
        if strength.min_score < min_strength.min_score:
            return None
        
        signal = Signal(
            pair=pair,
            direction=direction,
            strength=strength,
            score=score,
            confidence=coherence_result.consensus_ratio,
            strategy="coherence_ensemble",
            strategy_votes={v.strategy_name: v.score for v in votes},
            entry_price=snapshot.price,
            regime=snapshot.regime.regime.value,
            volatility=snapshot.volatility,
            coherence_passed=True,
            coherence_score=coherence_result.final_score,
        )
        
        return signal
    
    def _determine_direction(self, votes: List[StrategyVote]) -> TradeDirection:
        """Determine overall direction from strategy votes."""
        bullish_score = sum(v.weighted_score for v in votes if v.is_bullish)
        bearish_score = sum(v.weighted_score for v in votes if v.is_bearish)
        
        return TradeDirection.BUY if bullish_score >= bearish_score else TradeDirection.SELL
