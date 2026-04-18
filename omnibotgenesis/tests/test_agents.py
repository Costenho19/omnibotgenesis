"""
Tests — OMNIX Multi-Agent System
ADR-041: Multi-Agent Decision Governance

Covers:
  - AgentResult / OrchestratorResult serialization
  - BaseAgent fallback on timeout and exceptions
  - Orchestrator consensus logic (normal, degraded, full-disagreement)
  - Each agent graceful degradation when APIs are unavailable
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from omnix_services.agents.models import (
    AgentResult, OrchestratorResult, SignalType, RiskLevel, AgentStatus
)
from omnix_services.agents.base_agent import BaseAgent
from omnix_services.agents.orchestrator import AgentOrchestrator, AGENT_WEIGHTS


# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_agent_result(signal=SignalType.BUY, confidence=70.0, name="TestAgent",
                      status=AgentStatus.OK) -> AgentResult:
    return AgentResult(
        agent_name=name,
        signal=signal,
        confidence=confidence,
        reasoning="Test reasoning",
        status=status,
        metadata={},
    )


# ─── Model Tests ──────────────────────────────────────────────────────────────

class TestAgentResult:
    def test_signal_value_buy(self):
        r = make_agent_result(signal=SignalType.BUY)
        assert r.signal_value == 1.0

    def test_signal_value_sell(self):
        r = make_agent_result(signal=SignalType.SELL)
        assert r.signal_value == -1.0

    def test_signal_value_hold(self):
        r = make_agent_result(signal=SignalType.HOLD)
        assert r.signal_value == 0.0

    def test_confidence_norm_clamped(self):
        r = make_agent_result(confidence=150.0)
        assert r.confidence_norm == 1.0
        r2 = make_agent_result(confidence=-10.0)
        assert r2.confidence_norm == 0.0

    def test_to_dict_serializable(self):
        r = make_agent_result()
        d = r.to_dict()
        json_str = json.dumps(d)
        assert "BUY" in json_str
        assert "signal_value" in d
        assert d["signal_value"] == 1.0

    def test_timestamp_is_iso(self):
        r = make_agent_result()
        datetime.fromisoformat(r.timestamp)


class TestOrchestratorResult:
    def _make_result(self) -> OrchestratorResult:
        comp = {
            "SignalAgent":    make_agent_result(SignalType.BUY, 70, "SignalAgent"),
            "RiskAgent":      make_agent_result(SignalType.HOLD, 50, "RiskAgent"),
            "SentimentAgent": make_agent_result(SignalType.BUY, 60, "SentimentAgent"),
        }
        return OrchestratorResult(
            symbol="BTC",
            timeframe="1h",
            consensus_signal=SignalType.BUY,
            consensus_score=0.35,
            consensus_confidence=65.0,
            component_results=comp,
            degraded_flags={"SignalAgent": False, "RiskAgent": False, "SentimentAgent": False},
            latency_ms=250.0,
        )

    def test_to_dict_serializable(self):
        r = self._make_result()
        d = r.to_dict()
        json.dumps(d)

    def test_is_degraded_false(self):
        r = self._make_result()
        assert r.is_degraded is False

    def test_is_degraded_true(self):
        r = self._make_result()
        r.degraded_flags["SignalAgent"] = True
        assert r.is_degraded is True


# ─── BaseAgent Fallback Tests ─────────────────────────────────────────────────

class ConcreteAgent(BaseAgent):
    name = "ConcreteAgent"
    timeout = 5.0

    def __init__(self, data=None, raise_exc=None, delay=0.0):
        self._data = data or {}
        self._raise = raise_exc
        self._delay = delay

    async def _fetch_data(self, symbol, timeframe):
        if self._delay:
            await asyncio.sleep(self._delay)
        if self._raise:
            raise self._raise
        return self._data

    async def _compute_signal(self, symbol, timeframe, raw_data):
        return self._make_result(SignalType.BUY, 80.0, "Test BUY signal")


class TestBaseAgentFallback:
    def test_fallback_on_exception(self):
        agent = ConcreteAgent(raise_exc=ValueError("API error"))
        result = asyncio.run(agent.run("BTC"))
        assert result.signal == SignalType.HOLD
        assert result.confidence == 0.0
        assert result.status == AgentStatus.FAILED

    def test_fallback_on_timeout(self):
        agent = ConcreteAgent(delay=20.0)
        agent.timeout = 0.1
        result = asyncio.run(agent.run("BTC"))
        assert result.signal == SignalType.HOLD
        assert result.status == AgentStatus.FAILED
        assert "Timeout" in result.reasoning

    def test_normal_result(self):
        agent = ConcreteAgent()
        result = asyncio.run(agent.run("BTC"))
        assert result.signal == SignalType.BUY
        assert result.confidence == 80.0
        assert result.status == AgentStatus.OK


# ─── Orchestrator Consensus Tests ─────────────────────────────────────────────

class TestOrchestratorConsensus:
    def _make_orchestrator_with_mocks(self, signal_res, sentiment_res, risk_res):
        orch = AgentOrchestrator.__new__(AgentOrchestrator)
        mock_signal    = MagicMock()
        mock_sentiment = MagicMock()
        mock_risk      = MagicMock()
        mock_signal.run    = AsyncMock(return_value=signal_res)
        mock_sentiment.run = AsyncMock(return_value=sentiment_res)
        mock_risk.run      = AsyncMock(return_value=risk_res)
        mock_signal._fallback    = lambda s, reason="": make_agent_result(SignalType.HOLD, 0, "SignalAgent", AgentStatus.FAILED)
        mock_sentiment._fallback = lambda s, reason="": make_agent_result(SignalType.HOLD, 0, "SentimentAgent", AgentStatus.FAILED)
        mock_risk._fallback      = lambda s, reason="": make_agent_result(SignalType.HOLD, 0, "RiskAgent", AgentStatus.FAILED)
        orch.agents = {
            "SignalAgent":    mock_signal,
            "SentimentAgent": mock_sentiment,
            "RiskAgent":      mock_risk,
        }
        return orch

    def test_all_buy_produces_buy(self):
        orch = self._make_orchestrator_with_mocks(
            make_agent_result(SignalType.BUY, 80, "SignalAgent"),
            make_agent_result(SignalType.BUY, 70, "SentimentAgent"),
            make_agent_result(SignalType.BUY, 60, "RiskAgent"),
        )
        result = asyncio.run(orch.run("BTC"))
        assert result.consensus_signal == SignalType.BUY
        assert result.consensus_score > 0.20

    def test_all_sell_produces_sell(self):
        orch = self._make_orchestrator_with_mocks(
            make_agent_result(SignalType.SELL, 80, "SignalAgent"),
            make_agent_result(SignalType.SELL, 70, "SentimentAgent"),
            make_agent_result(SignalType.SELL, 60, "RiskAgent"),
        )
        result = asyncio.run(orch.run("BTC"))
        assert result.consensus_signal == SignalType.SELL
        assert result.consensus_score < -0.20

    def test_mixed_signals_produce_hold(self):
        orch = self._make_orchestrator_with_mocks(
            make_agent_result(SignalType.BUY,  50, "SignalAgent"),
            make_agent_result(SignalType.HOLD, 50, "SentimentAgent"),
            make_agent_result(SignalType.SELL, 50, "RiskAgent"),
        )
        result = asyncio.run(orch.run("BTC"))
        assert result.consensus_signal == SignalType.HOLD
        assert result.requires_stronger_core_signal is True
        assert result.consensus_confidence <= 35.0

    def test_degraded_agents_return_hold(self):
        orch = self._make_orchestrator_with_mocks(
            make_agent_result(SignalType.HOLD, 0, "SignalAgent", AgentStatus.FAILED),
            make_agent_result(SignalType.HOLD, 0, "SentimentAgent", AgentStatus.FAILED),
            make_agent_result(SignalType.HOLD, 0, "RiskAgent", AgentStatus.FAILED),
        )
        result = asyncio.run(orch.run("BTC"))
        assert result.consensus_signal == SignalType.HOLD
        assert result.consensus_confidence == 0.0

    def test_latency_is_recorded(self):
        orch = self._make_orchestrator_with_mocks(
            make_agent_result(SignalType.BUY, 80, "SignalAgent"),
            make_agent_result(SignalType.BUY, 70, "SentimentAgent"),
            make_agent_result(SignalType.BUY, 60, "RiskAgent"),
        )
        result = asyncio.run(orch.run("BTC"))
        assert result.latency_ms >= 0

    def test_weights_sum_to_one(self):
        total = sum(AGENT_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_result_is_serializable(self):
        orch = self._make_orchestrator_with_mocks(
            make_agent_result(SignalType.BUY, 80, "SignalAgent"),
            make_agent_result(SignalType.HOLD, 50, "SentimentAgent"),
            make_agent_result(SignalType.BUY, 65, "RiskAgent"),
        )
        result = asyncio.run(orch.run("BTC"))
        d = result.to_dict()
        json.dumps(d)
