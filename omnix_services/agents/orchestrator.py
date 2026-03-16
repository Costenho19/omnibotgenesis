"""
OMNIX Multi-Agent System — Agent Orchestrator
ADR-041: Multi-Agent Decision Governance

Runs all 3 agents in parallel (asyncio.gather), aggregates results into
a weighted consensus, and produces an OrchestratorResult ready for
injection into the governance pipeline.

Weights (from ADR-041):
  SignalAgent:    0.45  (dominant — direct technical evidence)
  RiskAgent:      0.30  (modulates conviction based on portfolio state)
  SentimentAgent: 0.25  (contextual confirmation)

Consensus thresholds:
  score > +0.20  → BUY
  score < -0.20  → SELL
  else           → HOLD

Disagreement rule:
  If all 3 agents produce different signals → HOLD,
  confidence capped at 35, requires_stronger_core_signal=True
"""
import logging
import asyncio
import time
from typing import Dict, Optional

from omnix_services.agents.base_agent import BaseAgent
from omnix_services.agents.models import (
    AgentResult, OrchestratorResult, SignalType, AgentStatus
)
from omnix_services.agents.signal_agent    import SignalAgent
from omnix_services.agents.sentiment_agent import SentimentAgent
from omnix_services.agents.risk_agent      import RiskAgent

logger = logging.getLogger(__name__)

AGENT_WEIGHTS: Dict[str, float] = {
    "SignalAgent":    0.45,
    "RiskAgent":      0.30,
    "SentimentAgent": 0.25,
}


class AgentOrchestrator:
    """
    Coordinates all OMNIX governance agents and produces a consensus signal.

    Usage:
        orchestrator = AgentOrchestrator()
        result = await orchestrator.run(symbol="BTC", timeframe="1h")
        # result.consensus_signal, result.consensus_score, result.to_dict()
    """

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {
            "SignalAgent":    SignalAgent(),
            "SentimentAgent": SentimentAgent(),
            "RiskAgent":      RiskAgent(),
        }

    async def run(self, symbol: str, timeframe: str = "1h") -> OrchestratorResult:
        """
        Run all agents in parallel and return a weighted consensus.
        Never raises — returns degraded result on complete failure.
        """
        start = time.monotonic()

        tasks = {
            name: agent.run(symbol, timeframe)
            for name, agent in self.agents.items()
        }

        results_list = await asyncio.gather(*tasks.values(), return_exceptions=True)
        component_results: Dict[str, AgentResult] = {}
        degraded_flags:    Dict[str, bool]         = {}

        for name, result in zip(tasks.keys(), results_list):
            if isinstance(result, Exception):
                logger.error(f"[Orchestrator] Agent {name} raised exception: {result}")
                agent = self.agents[name]
                result = agent._fallback(symbol, reason=str(result))
            component_results[name] = result
            degraded_flags[name] = result.status != AgentStatus.OK

        consensus = self._compute_consensus(component_results)
        latency_ms = (time.monotonic() - start) * 1000

        orchestrator_result = OrchestratorResult(
            symbol=symbol,
            timeframe=timeframe,
            consensus_signal=consensus["signal"],
            consensus_score=consensus["score"],
            consensus_confidence=consensus["confidence"],
            component_results=component_results,
            degraded_flags=degraded_flags,
            latency_ms=latency_ms,
            requires_stronger_core_signal=consensus["requires_stronger_core_signal"],
        )

        logger.info(
            f"[Orchestrator] {symbol} → {consensus['signal'].value} "
            f"(score={consensus['score']:.3f}, conf={consensus['confidence']:.1f}%, "
            f"latency={latency_ms:.0f}ms, degraded={any(degraded_flags.values())})"
        )
        return orchestrator_result

    def _compute_consensus(self, results: Dict[str, AgentResult]) -> Dict:
        weighted_score = 0.0
        total_weight   = 0.0
        weighted_conf  = 0.0
        signals_seen   = set()

        for name, result in results.items():
            weight = AGENT_WEIGHTS.get(name, 0.0)
            if result.confidence > 0 and result.signal != SignalType.UNKNOWN:
                contribution = weight * result.signal_value * result.confidence_norm
                weighted_score += contribution
                weighted_conf  += weight * result.confidence_norm
                total_weight   += weight
                signals_seen.add(result.signal)

        if total_weight == 0:
            return {
                "signal": SignalType.HOLD,
                "score": 0.0,
                "confidence": 0.0,
                "requires_stronger_core_signal": True,
            }

        norm_score = weighted_score / total_weight if total_weight > 0 else 0.0
        avg_conf   = (weighted_conf / total_weight) * 100 if total_weight > 0 else 0.0

        all_signals = [r.signal for r in results.values() if r.signal != SignalType.UNKNOWN]
        unique_signals = set(all_signals)

        # Requires stronger core signal when BUY and SELL are simultaneously present
        # (fundamental disagreement regardless of HOLD presence)
        hard_disagreement = (SignalType.BUY in unique_signals and SignalType.SELL in unique_signals)

        if hard_disagreement and len(unique_signals) == 3:
            return {
                "signal": SignalType.HOLD,
                "score": norm_score,
                "confidence": min(avg_conf, 35.0),
                "requires_stronger_core_signal": True,
            }

        requires_stronger = hard_disagreement

        if norm_score > OrchestratorResult.BUY_THRESHOLD:
            signal = SignalType.BUY
        elif norm_score < OrchestratorResult.SELL_THRESHOLD:
            signal = SignalType.SELL
        else:
            signal = SignalType.HOLD
            avg_conf *= 0.7

        return {
            "signal": signal,
            "score": round(norm_score, 4),
            "confidence": round(min(avg_conf, 95.0), 2),
            "requires_stronger_core_signal": requires_stronger,
        }

    def get_health(self) -> Dict:
        return {
            "orchestrator": "AgentOrchestrator",
            "agents": {name: agent.get_health() for name, agent in self.agents.items()},
            "weights": AGENT_WEIGHTS,
            "thresholds": {
                "buy":  OrchestratorResult.BUY_THRESHOLD,
                "sell": OrchestratorResult.SELL_THRESHOLD,
            },
        }
