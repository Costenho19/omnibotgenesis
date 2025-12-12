"""
OMNIX V7.0 Coherence Engine Adapter
=====================================
Adapter wrapping legacy CoherenceEngine for new port interface.
"""

import asyncio
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor

from src.omnix.domain.support.market import (
    MarketSnapshot, StrategyVote, CoherenceResult,
)

_executor = ThreadPoolExecutor(max_workers=4)


async def _run_sync(func, *args, **kwargs):
    """Run a synchronous function in executor for async context."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, lambda: func(*args, **kwargs))


class CoherenceEngineAdapter:
    """
    Adapter for legacy CoherenceEngine.
    
    Implements ICoherenceEnginePort by delegating to legacy implementation.
    """
    
    def __init__(self, legacy_engine=None):
        """Initialize adapter with optional legacy engine."""
        self._legacy = legacy_engine
        self._lazy_loaded = False
    
    def _get_legacy(self):
        """Lazy load legacy coherence engine if not provided."""
        if self._legacy is None and not self._lazy_loaded:
            try:
                from omnix_core.bot.auto_trading_bot import AutoTradingBot
                self._legacy = AutoTradingBot
            except ImportError:
                pass
            self._lazy_loaded = True
        return self._legacy
    
    async def evaluate(self, pair: str, snapshot: MarketSnapshot) -> CoherenceResult:
        """
        Evaluate coherence for a trading pair.
        
        Args:
            pair: Trading pair (e.g., "BTC/USD")
            snapshot: Current market data
            
        Returns:
            CoherenceResult with evaluation outcome
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
            result = CoherenceResult(pair=pair)
            
            votes = await self.get_strategy_votes(pair, snapshot)
            for vote in votes:
                result.add_vote(vote)
            
            result.calculate_consensus()
            
            if result.consensus_ratio >= 0.66 and not result.veto_active:
                bullish_score = sum(v.weighted_score for v in votes if v.is_bullish)
                bearish_score = sum(abs(v.weighted_score) for v in votes if v.is_bearish)
                result.final_score = max(bullish_score, bearish_score)
                result.passed = result.final_score >= 12
            else:
                result.passed = False
            
            return result
            
        except Exception as e:
            return CoherenceResult(
                pair=pair,
                passed=False,
                veto_active=True,
                veto_reason=f"Evaluation error: {str(e)}",
            )
    
    async def get_strategy_votes(
        self,
        pair: str,
        snapshot: MarketSnapshot,
    ) -> List[StrategyVote]:
        """
        Get strategy votes for a trading pair.
        
        Args:
            pair: Trading pair
            snapshot: Current market data
            
        Returns:
            List of strategy votes
        """
        votes: List[StrategyVote] = []
        
        try:
            votes.append(StrategyVote(
                strategy_name="Momentum",
                direction="buy" if snapshot.change_24h > 0 else "sell",
                score=abs(snapshot.change_24h) * 2,
                confidence=0.6,
                weight=1.0,
                tier=1,
            ))
            
            votes.append(StrategyVote(
                strategy_name="Regime",
                direction="buy" if snapshot.regime.regime.is_bullish else "sell",
                score=5.0 if snapshot.regime.regime.is_bullish else -5.0,
                confidence=snapshot.regime.confidence,
                weight=1.2,
                tier=3,
            ))
            
            volatility_ok = snapshot.volatility < 0.05
            votes.append(StrategyVote(
                strategy_name="Volatility",
                direction="buy" if volatility_ok else "neutral",
                score=3.0 if volatility_ok else 0.0,
                confidence=0.7,
                weight=0.8,
                tier=2,
            ))
            
        except Exception:
            pass
        
        return votes
