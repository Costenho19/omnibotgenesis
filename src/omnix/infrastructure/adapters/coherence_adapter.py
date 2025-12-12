"""
OMNIX V7.0 Coherence Engine Adapter
=====================================
Adapter wrapping legacy CoherenceEngine for new port interface.

This adapter delegates to the real legacy coherence engine to ensure
parity between old and new application layers.
"""

import asyncio
import logging
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor

from src.omnix.domain.support.market import (
    MarketSnapshot, StrategyVote, CoherenceResult,
)

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=4)


async def _run_sync(func, *args, **kwargs):
    """Run a synchronous function in executor for async context."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, lambda: func(*args, **kwargs))


class CoherenceEngineAdapter:
    """
    Adapter for legacy CoherenceEngine.
    
    Implements ICoherenceEnginePort by delegating to legacy coherence_service
    CoherenceEngine. This ensures full parity with legacy behavior including
    tier breakdown, veto propagation, and strategy weight calculations.
    """
    
    def __init__(self, legacy_engine=None):
        """Initialize adapter with optional legacy engine.
        
        Args:
            legacy_engine: Optional pre-initialized CoherenceEngine.
                          If None, will be lazy-loaded from legacy module.
        """
        self._legacy = legacy_engine
        self._lazy_loaded = False
    
    def _get_legacy(self):
        """Lazy load legacy coherence engine if not provided."""
        if self._legacy is None and not self._lazy_loaded:
            try:
                from omnix_services.coherence_service.coherence_engine import CoherenceEngine
                self._legacy = CoherenceEngine()
                logger.info("CoherenceEngineAdapter: Legacy engine loaded")
            except ImportError as e:
                logger.warning(f"CoherenceEngineAdapter: Legacy engine not available: {e}")
            self._lazy_loaded = True
        return self._legacy
    
    async def evaluate(self, pair: str, votes: List[StrategyVote]) -> CoherenceResult:
        """
        Evaluate coherence for a trading pair using legacy engine.
        
        Args:
            pair: Trading pair (e.g., "BTC/USD")
            votes: Strategy votes to evaluate
            
        Returns:
            CoherenceResult with evaluation outcome from legacy engine
        """
        legacy = self._get_legacy()
        if legacy is None:
            return CoherenceResult(
                pair=pair,
                passed=False,
                veto_active=True,
                veto_reason="Coherence engine not available",
            )
        
        try:
            legacy_signals = self._convert_votes_to_legacy_signals(votes)
            
            report = await _run_sync(legacy.analyze_coherence, legacy_signals)
            
            result = self._convert_legacy_report_to_result(pair, report, votes)
            
            return result
            
        except Exception as e:
            logger.error(f"CoherenceEngineAdapter.evaluate error: {e}")
            return CoherenceResult(
                pair=pair,
                passed=False,
                veto_active=True,
                veto_reason=f"Evaluation error: {str(e)}",
            )
    
    def _convert_votes_to_legacy_signals(self, votes: List[StrategyVote]) -> list:
        """Convert domain votes to legacy StrategySignal format."""
        try:
            from omnix_services.coherence_service.coherence_engine import (
                StrategySignal as LegacySignal,
                Signal as LegacySignalEnum,
            )
            
            legacy_signals = []
            for vote in votes:
                if vote.score >= 4:
                    signal = LegacySignalEnum.STRONG_BUY
                elif vote.score > 0:
                    signal = LegacySignalEnum.BUY
                elif vote.score <= -4:
                    signal = LegacySignalEnum.STRONG_SELL
                elif vote.score < 0:
                    signal = LegacySignalEnum.SELL
                else:
                    signal = LegacySignalEnum.HOLD
                
                legacy_signals.append(LegacySignal(
                    name=vote.strategy_name,
                    signal=signal,
                    confidence=vote.confidence,
                    strength=abs(vote.score),
                    reasoning=f"Tier {vote.tier} vote",
                ))
            
            return legacy_signals
            
        except ImportError:
            return []
    
    def _convert_legacy_report_to_result(
        self,
        pair: str,
        report,
        original_votes: List[StrategyVote],
    ) -> CoherenceResult:
        """Convert legacy CoherenceReport to domain CoherenceResult."""
        result = CoherenceResult(pair=pair)
        
        for vote in original_votes:
            result.add_vote(vote)
        
        result.final_score = report.coherence_score
        
        consensus_ratio = report.coherence_score / 100.0
        result.consensus_ratio = consensus_ratio
        
        if report.contradictions:
            result.veto_active = True
            result.veto_reason = "; ".join(report.contradictions[:3])
        
        from omnix_services.coherence_service.coherence_engine import CoherenceLevel
        result.passed = (
            report.coherence_level in [CoherenceLevel.EXCELLENT, CoherenceLevel.GOOD]
            and not result.veto_active
            and consensus_ratio >= 0.66
        )
        
        result.tier_breakdown = self._extract_tier_breakdown(original_votes)
        
        return result
    
    def _extract_tier_breakdown(self, votes: List[StrategyVote]) -> dict:
        """Extract tier breakdown from votes for institutional reporting."""
        breakdown = {}
        for vote in votes:
            tier_key = f"tier_{vote.tier}"
            if tier_key not in breakdown:
                breakdown[tier_key] = {
                    "votes": 0,
                    "bullish": 0,
                    "bearish": 0,
                    "neutral": 0,
                    "total_score": 0.0,
                }
            breakdown[tier_key]["votes"] += 1
            breakdown[tier_key]["total_score"] += vote.score
            
            if vote.is_bullish:
                breakdown[tier_key]["bullish"] += 1
            elif vote.is_bearish:
                breakdown[tier_key]["bearish"] += 1
            else:
                breakdown[tier_key]["neutral"] += 1
        
        return breakdown
    
    async def get_strategy_votes(
        self,
        pair: str,
        snapshot: MarketSnapshot,
    ) -> List[StrategyVote]:
        """
        Generate strategy votes from market snapshot.
        
        This method creates votes based on market data for cases where
        we need to generate votes internally (testing, simulation).
        
        Args:
            pair: Trading pair
            snapshot: Current market data
            
        Returns:
            List of strategy votes
        """
        votes: List[StrategyVote] = []
        
        try:
            votes.append(StrategyVote(
                strategy_name="quantum_momentum",
                direction="buy" if snapshot.change_24h > 0 else "sell",
                score=min(abs(snapshot.change_24h) * 2, 6.0),
                confidence=0.7,
                weight=0.20,
                tier=1,
            ))
            
            regime_bullish = snapshot.regime.regime.is_bullish
            votes.append(StrategyVote(
                strategy_name="hmm_regime",
                direction="buy" if regime_bullish else "sell",
                score=4.0 if regime_bullish else -4.0,
                confidence=snapshot.regime.confidence,
                weight=0.12,
                tier=3,
            ))
            
            volatility_ok = snapshot.volatility < 0.05
            votes.append(StrategyVote(
                strategy_name="kalman_filter",
                direction="neutral" if volatility_ok else "sell",
                score=2.0 if volatility_ok else -2.0,
                confidence=0.8,
                weight=0.15,
                tier=2,
            ))
            
            liquidity_ok = snapshot.liquidity_score > 0.6
            votes.append(StrategyVote(
                strategy_name="order_book",
                direction="buy" if liquidity_ok else "neutral",
                score=2.0 if liquidity_ok else 0.0,
                confidence=0.6,
                weight=0.08,
                tier=2,
            ))
            
        except Exception as e:
            logger.warning(f"CoherenceEngineAdapter.get_strategy_votes: {e}")
        
        return votes
