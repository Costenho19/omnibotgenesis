"""
OMNIX Multi-Agent System — Data Models
ADR-041: Multi-Agent Decision Governance

Defines shared data contracts for all agents and the orchestrator.
All models are JSON-serializable for DB storage and audit trails.
"""
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class SignalType(str, Enum):
    BUY  = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    UNKNOWN = "UNKNOWN"


class RiskLevel(str, Enum):
    LOW      = "LOW"
    MODERATE = "MODERATE"
    HIGH     = "HIGH"
    EXTREME  = "EXTREME"
    UNKNOWN  = "UNKNOWN"


class AgentStatus(str, Enum):
    OK       = "OK"
    DEGRADED = "DEGRADED"
    FAILED   = "FAILED"


@dataclass
class AgentResult:
    """
    Output contract for every agent.
    confidence: 0-100 (0 = no conviction, 100 = maximum conviction)
    signal_value: numeric mapping used by orchestrator (+1 BUY, 0 HOLD, -1 SELL)
    """
    agent_name:   str
    signal:       SignalType
    confidence:   float
    reasoning:    str
    status:       AgentStatus
    metadata:     Dict[str, Any] = field(default_factory=dict)
    timestamp:    str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def signal_value(self) -> float:
        mapping = {SignalType.BUY: 1.0, SignalType.HOLD: 0.0, SignalType.SELL: -1.0, SignalType.UNKNOWN: 0.0}
        return mapping[self.signal]

    @property
    def confidence_norm(self) -> float:
        return max(0.0, min(1.0, self.confidence / 100.0))

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["signal"] = self.signal.value
        d["status"] = self.status.value
        d["signal_value"] = self.signal_value
        d["confidence_norm"] = self.confidence_norm
        return d


@dataclass
class OrchestratorResult:
    """
    Consolidated output from the AgentOrchestrator.
    Injected into the governance pipeline as external_signal_weight.

    consensus_score: weighted sum in [-1, +1]
    Thresholds (from ADR-041): >+0.20 → BUY, <-0.20 → SELL, else HOLD
    """
    symbol:              str
    timeframe:           str
    consensus_signal:    SignalType
    consensus_score:     float
    consensus_confidence: float
    component_results:   Dict[str, AgentResult]
    degraded_flags:      Dict[str, bool]
    latency_ms:          float
    requires_stronger_core_signal: bool = False
    timestamp:           str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    BUY_THRESHOLD  = 0.20
    SELL_THRESHOLD = -0.20

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "consensus_signal": self.consensus_signal.value,
            "consensus_score": round(self.consensus_score, 4),
            "consensus_confidence": round(self.consensus_confidence, 2),
            "component_results": {k: v.to_dict() for k, v in self.component_results.items()},
            "degraded_flags": self.degraded_flags,
            "latency_ms": round(self.latency_ms, 2),
            "requires_stronger_core_signal": self.requires_stronger_core_signal,
            "timestamp": self.timestamp,
        }

    @property
    def is_degraded(self) -> bool:
        return any(self.degraded_flags.values())
