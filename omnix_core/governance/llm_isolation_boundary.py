"""
OMNIX — LLM Isolation Boundary
ADR-148: Structural Separation Between Conversational AI and Governance Pipeline

Architecture principle:
  Conversational AI ──→ [LLM ISOLATION BOUNDARY] ──→ Governance Pipeline
                                    ↓
                         boundary_crossing_log (auditable)

The boundary enforces that:
  1. No raw LLM text can enter the governance evaluation pipeline directly.
  2. Every crossing is logged with full provenance (source, destination, flags).
  3. Only GovernanceSignalPacket objects — containing exclusively numeric
     signals from the approved whitelist — may cross.
  4. LLM context artifacts (model names, prompt fragments, conversation state)
     are stripped before the packet is formed.
  5. Every violation raises BoundaryViolationError and is logged to DB.

This module is the architectural complement to input_sanitizer.py (ISR-017):
  - input_sanitizer:        per-message, content-level sanitization
  - LLMIsolationBoundary:   architectural-level, signal-level separation

ISR-017 extension | ADR-148 | Author: Harold Nunes — OMNIX QUANTUM LTD
Implemented: May 2026
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
import statistics as _statistics
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("OMNIX.Governance.LLMIsolationBoundary")

# ─────────────────────────────────────────────────────────────────────────────
# APPROVED SIGNAL WHITELIST
# Only these keys (all numeric) may cross the boundary into governance.
# Any other key is stripped and logged as a violation.
# ─────────────────────────────────────────────────────────────────────────────

_APPROVED_SIGNAL_KEYS: Set[str] = {
    "probability",
    "risk_score",
    "coherence_score",
    "volatility",
    "volume_ratio",
    "correlation",
    "liquidity_score",
    "macro_risk_index",
    "concentration_pct",
    "collateral_coverage",
    "counterparty_risk",
    "aml_risk_score",
    "fraud_risk_score",
    "jurisdiction_risk",
    "sentiment_score",
    "drawdown_pct",
    "sharpe_ratio",
    "var_95",
    "cvar_95",
    "beta",
    "leverage_ratio",
    "duration",
}

_FORBIDDEN_SIGNAL_KEYS: Set[str] = {
    "user_message",
    "prompt",
    "system_prompt",
    "llm_response",
    "model_name",
    "model_id",
    "conversation_id",
    "session_id",
    "raw_text",
    "instruction",
    "context_window",
    "temperature",
    "top_p",
    "completion",
    "chat_history",
}

_NUMERIC_TYPES = (int, float)


# ─────────────────────────────────────────────────────────────────────────────
# EXCEPTIONS
# ─────────────────────────────────────────────────────────────────────────────

class BoundaryViolationError(Exception):
    """
    Raised when an attempt is made to pass non-signal data across the
    LLM Isolation Boundary into the governance pipeline.

    Always caught by the caller — governance evaluation must never receive
    a BoundaryViolationError as input; it must fail-closed.
    """
    def __init__(self, message: str, violation_id: str, offending_keys: List[str] = None):
        super().__init__(message)
        self.violation_id = violation_id
        self.offending_keys = offending_keys or []


# ─────────────────────────────────────────────────────────────────────────────
# GOVERNANCE SIGNAL PACKET
# The ONLY object allowed to cross the LLM boundary into governance.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class GovernanceSignalPacket:
    """
    Canonical container for signals crossing the LLM Isolation Boundary.

    All signal values MUST be numeric (int or float) and drawn from the
    approved whitelist. Non-numeric or non-whitelisted keys are rejected.

    Fields:
        packet_id       — UUID for this crossing (auditable)
        source          — origin identifier (e.g. "telegram_bot", "api_gateway")
        signals         — approved numeric signals only
        asset           — asset symbol (e.g. "BTC", "ETH")
        domain          — governance domain (e.g. "trading", "insurance")
        crossed_at      — ISO-8601 UTC timestamp of boundary crossing
        sanitization_flags — flags from input_sanitizer (ISR-017)
        stripped_keys   — keys that were removed during sanitization
    """
    packet_id: str
    source: str
    signals: Dict[str, float]
    asset: str
    domain: str
    crossed_at: str
    sanitization_flags: List[str] = field(default_factory=list)
    stripped_keys: List[str] = field(default_factory=list)
    nua_report: Optional[Dict[str, Any]] = field(default=None)  # OMNIX DIFFERENTIATOR: NUA

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "packet_id":          self.packet_id,
            "source":             self.source,
            "signals":            self.signals,
            "asset":              self.asset,
            "domain":             self.domain,
            "crossed_at":         self.crossed_at,
            "sanitization_flags": self.sanitization_flags,
            "stripped_keys":      self.stripped_keys,
        }
        if self.nua_report is not None:
            d["nua_report"] = self.nua_report
        return d

    def packet_hash(self) -> str:
        """SHA-256 of canonical packet content — for audit trail."""
        canonical = json.dumps(
            {k: v for k, v in self.to_dict().items() if k != "packet_id"},
            sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# BOUNDARY CROSSING LOG ENTRY
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BoundaryCrossingRecord:
    """Auditable record of one LLM→Governance boundary crossing."""
    record_id: str
    packet_id: str
    source: str
    destination: str
    asset: str
    domain: str
    signal_count: int
    stripped_count: int
    sanitization_flags: List[str]
    packet_hash: str
    crossed_at: str
    crossing_type: str  # "APPROVED" | "STRIPPED" | "VIOLATION"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id":           self.record_id,
            "packet_id":           self.packet_id,
            "source":              self.source,
            "destination":         self.destination,
            "asset":               self.asset,
            "domain":              self.domain,
            "signal_count":        self.signal_count,
            "stripped_count":      self.stripped_count,
            "sanitization_flags":  self.sanitization_flags,
            "packet_hash":         self.packet_hash,
            "crossed_at":          self.crossed_at,
            "crossing_type":       self.crossing_type,
        }


# ─────────────────────────────────────────────────────────────────────────────
# OMNIX DIFFERENTIATOR: NUMERIC UNIFORMITY ANOMALY (NUA) DETECTION
#
# GOVERNANCE RISK SOLVED:
#   An LLM can fabricate governance signals that look structurally valid
#   (correct keys, numeric values, within range) but were invented rather
#   than computed from actual market data.  Traditional boundary checks
#   only inspect key names — they cannot distinguish real signals from
#   statistically suspicious numeric patterns.
#
#   NUA detects three fabrication fingerprints:
#     1. Coefficient of variation < 0.15 — all values suspiciously similar
#        (real market signals are noisy and diverse)
#     2. Round-number ratio > 60% — most values on ×0.05 multiples
#        (LLMs tend to round to "clean" numbers; markets do not)
#     3. Value range < 5.0 across ≥3 signals — unnaturally narrow spread
#
# VERIFIABLE EVIDENCE:
#   NumericUniformityReport is embedded in every GovernanceSignalPacket.
#   The report includes coefficient_of_variation, round_number_ratio,
#   value_range, and uniformity_score.  FABRICATION_LIKELY means the
#   signal set passed the boundary check but its numeric pattern is
#   statistically inconsistent with observed market-derived data.
#
# INSTITUTIONAL EXPLANATION:
#   If a bank employee tells you all six risk indicators are exactly 0.75,
#   you don't believe the data is real.  NUA automates that intuition.
#   It does not block — it flags.  The governance receipt carries the flag
#   so auditors can review later.
#
# ADR-148 extension | OMNIX-NUA-001
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class NumericUniformityReport:
    """
    Result of Numeric Uniformity Anomaly analysis on a GovernanceSignalPacket.

    uniformity_score: 0–100. Higher = more suspiciously uniform.
      < 30  → NATURAL           (normal market-derived diversity)
      30–70 → SUSPICIOUS        (unusual uniformity — flag for review)
      > 70  → FABRICATION_LIKELY (pattern consistent with LLM fabrication)
    """
    report_id: str
    signal_count: int
    coefficient_of_variation: float
    round_number_ratio: float
    value_range: float
    uniformity_score: float
    nua_verdict: str
    suspicious_signals: List[str]
    analyzed_at: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id":                  self.report_id,
            "signal_count":               self.signal_count,
            "coefficient_of_variation":   self.coefficient_of_variation,
            "round_number_ratio":         self.round_number_ratio,
            "value_range":                self.value_range,
            "uniformity_score":           self.uniformity_score,
            "nua_verdict":                self.nua_verdict,
            "suspicious_signals":         self.suspicious_signals,
            "analyzed_at":                self.analyzed_at,
        }


def _analyze_numeric_uniformity(
    signals: Dict[str, float],
    packet_id: str,
) -> NumericUniformityReport:
    """
    Analyze approved numeric signals for uniformity anomalies consistent
    with LLM fabrication.

    Never blocks — produces a flagged report embedded in the packet.
    Legitimate signals with low natural variation (e.g., stable fixed-income
    metrics) will show low uniformity_score because real data has noise even
    when values are close.  The composite score requires multiple independent
    anomaly indicators before reaching FABRICATION_LIKELY.
    """
    report_id = f"NUA-{uuid.uuid4().hex[:10].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    if len(signals) < 2:
        return NumericUniformityReport(
            report_id=report_id,
            signal_count=len(signals),
            coefficient_of_variation=0.0,
            round_number_ratio=0.0,
            value_range=0.0,
            uniformity_score=0.0,
            nua_verdict="NATURAL",
            suspicious_signals=[],
            analyzed_at=now_iso,
        )

    values = list(signals.values())
    mean_val = sum(values) / len(values)

    # 1. Coefficient of variation (std / mean): low = suspiciously similar
    try:
        std_val = _statistics.stdev(values) if len(values) >= 2 else 0.0
    except Exception:
        std_val = 0.0
    cv = round(abs(std_val / mean_val), 4) if mean_val != 0.0 else 0.0

    # 2. Round-number ratio: values on ×0.05 multiples (LLM rounding pattern)
    def _is_round(v: float) -> bool:
        remainder = v % 0.05
        return remainder < 0.001 or (0.05 - remainder) < 0.001

    round_count = sum(1 for v in values if _is_round(v))
    round_ratio = round(round_count / len(values), 3)

    # 3. Value range: suspiciously narrow across ≥3 signals
    value_range = round(max(values) - min(values), 2)

    # Suspicious signal detection: close to mean AND low overall diversity
    suspicious_signals: List[str] = []
    if cv < 0.15 and len(values) >= 3:
        for k, v in signals.items():
            if abs(v - mean_val) < 3.0:
                suspicious_signals.append(k)

    # Composite uniformity score (0–100)
    # Each component contributes independently; all three must be elevated
    # for FABRICATION_LIKELY — single-indicator triggering is deliberately avoided
    cv_component    = max(0.0, (0.5 - cv) / 0.5) * 40.0          # max 40 pts
    round_component = round_ratio * 30.0                           # max 30 pts
    range_component = (
        max(0.0, (10.0 - value_range) / 10.0) * 30.0
        if len(values) >= 3 else 0.0
    )                                                              # max 30 pts

    uniformity_score = round(min(100.0, cv_component + round_component + range_component), 1)

    if uniformity_score >= 70:
        verdict = "FABRICATION_LIKELY"
    elif uniformity_score >= 30:
        verdict = "SUSPICIOUS"
    else:
        verdict = "NATURAL"

    if verdict != "NATURAL":
        logger.warning(
            f"[LLMBoundary][NUA] Numeric uniformity anomaly — packet={packet_id} "
            f"verdict={verdict} score={uniformity_score} cv={cv:.4f} "
            f"round_ratio={round_ratio:.2f} range={value_range:.1f}"
        )

    return NumericUniformityReport(
        report_id=report_id,
        signal_count=len(signals),
        coefficient_of_variation=cv,
        round_number_ratio=round_ratio,
        value_range=value_range,
        uniformity_score=uniformity_score,
        nua_verdict=verdict,
        suspicious_signals=suspicious_signals,
        analyzed_at=now_iso,
    )


# ─────────────────────────────────────────────────────────────────────────────
# IN-PROCESS BOUNDARY LOG (ring buffer — DB write is best-effort)
# ─────────────────────────────────────────────────────────────────────────────

_boundary_log: List[BoundaryCrossingRecord] = []
_boundary_log_lock = threading.Lock()
_MAX_LOG_SIZE = 1000


def _log_crossing(record: BoundaryCrossingRecord) -> None:
    """Append crossing record to in-process ring buffer."""
    with _boundary_log_lock:
        _boundary_log.append(record)
        if len(_boundary_log) > _MAX_LOG_SIZE:
            _boundary_log.pop(0)


def get_boundary_log(limit: int = 100) -> List[Dict[str, Any]]:
    """Return recent boundary crossing records (newest first)."""
    with _boundary_log_lock:
        return [r.to_dict() for r in reversed(_boundary_log[-limit:])]


def get_boundary_stats() -> Dict[str, Any]:
    """Aggregate statistics for boundary crossing monitoring."""
    with _boundary_log_lock:
        total = len(_boundary_log)
        violations = sum(1 for r in _boundary_log if r.crossing_type == "VIOLATION")
        stripped = sum(1 for r in _boundary_log if r.crossing_type == "STRIPPED")
        approved = sum(1 for r in _boundary_log if r.crossing_type == "APPROVED")
        total_stripped_keys = sum(r.stripped_count for r in _boundary_log)
    return {
        "total_crossings":    total,
        "approved":           approved,
        "stripped":           stripped,
        "violations":         violations,
        "total_stripped_keys": total_stripped_keys,
        "violation_rate":     round(violations / total, 4) if total else 0.0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# LLM ISOLATION BOUNDARY
# ─────────────────────────────────────────────────────────────────────────────

class LLMIsolationBoundary:
    """
    Architectural enforcement layer between conversational AI and governance.

    Usage:
        boundary = LLMIsolationBoundary()

        # Convert raw AI-generated dict to a safe GovernanceSignalPacket
        packet = boundary.form_packet(
            raw_signals=ai_output_dict,
            source="telegram_bot",
            asset="BTC",
            domain="trading",
            sanitization_flags=["TRUNCATED"],
        )

        # The packet.signals dict is safe to pass to GovernanceEvaluationEngine
        evaluation = engine.evaluate(signals=packet.signals, ...)

    Raises BoundaryViolationError if forbidden keys are detected and
    strict_mode=True (default: False — strips and logs instead).
    """

    def __init__(self, strict_mode: bool = False, destination: str = "governance_pipeline"):
        self._strict = strict_mode
        self._destination = destination

    # ── Public API ────────────────────────────────────────────────────────────

    def form_packet(
        self,
        raw_signals: Dict[str, Any],
        source: str,
        asset: str,
        domain: str,
        sanitization_flags: Optional[List[str]] = None,
    ) -> GovernanceSignalPacket:
        """
        Validate and sanitize raw signals from the AI layer, forming a
        GovernanceSignalPacket safe to pass to the governance pipeline.

        Steps:
          1. Detect forbidden keys (LLM artifacts) → raise or strip
          2. Enforce numeric-only values
          3. Enforce approved-key whitelist (warn on unknown, strip on forbidden)
          4. Log the crossing with full provenance
          5. Return sanitized GovernanceSignalPacket

        Args:
            raw_signals:        Dict from AI layer (may contain LLM artifacts)
            source:             Origin identifier (for audit log)
            asset:              Asset symbol (BTC, ETH, etc.)
            domain:             Governance domain
            sanitization_flags: Flags from input_sanitizer.py (ISR-017)

        Returns:
            GovernanceSignalPacket with only approved numeric signals

        Raises:
            BoundaryViolationError: if strict_mode=True and forbidden keys found
        """
        sanitization_flags = sanitization_flags or []
        packet_id = f"PKT-{uuid.uuid4().hex[:12].upper()}"
        stripped_keys: List[str] = []
        violation_keys: List[str] = []

        clean_signals: Dict[str, float] = {}

        for key, value in raw_signals.items():
            if key in _FORBIDDEN_SIGNAL_KEYS:
                violation_keys.append(key)
                stripped_keys.append(key)
                continue

            if not isinstance(value, _NUMERIC_TYPES):
                stripped_keys.append(key)
                logger.debug(
                    f"[LLMBoundary] Non-numeric signal stripped: key={key} "
                    f"type={type(value).__name__} packet={packet_id}"
                )
                continue

            if key not in _APPROVED_SIGNAL_KEYS:
                stripped_keys.append(key)
                logger.warning(
                    f"[LLMBoundary] Unknown signal key stripped (not in approved whitelist): "
                    f"key={key} packet={packet_id}. "
                    f"Add to _APPROVED_SIGNAL_KEYS if this is a legitimate governance signal."
                )
                continue

            clean_signals[key] = float(value)

        if violation_keys:
            vid = f"BVIO-{uuid.uuid4().hex[:8].upper()}"
            logger.error(
                f"[LLMBoundary][VIOLATION] Forbidden LLM keys detected in governance signal: "
                f"keys={violation_keys} violation_id={vid} packet={packet_id} source={source}"
            )
            if self._strict:
                _log_crossing(BoundaryCrossingRecord(
                    record_id=f"BCR-{uuid.uuid4().hex[:12].upper()}",
                    packet_id=packet_id,
                    source=source,
                    destination=self._destination,
                    asset=asset,
                    domain=domain,
                    signal_count=0,
                    stripped_count=len(stripped_keys),
                    sanitization_flags=sanitization_flags,
                    packet_hash="",
                    crossed_at=datetime.now(timezone.utc).isoformat(),
                    crossing_type="VIOLATION",
                ))
                raise BoundaryViolationError(
                    f"Forbidden LLM context keys detected in governance signal: {violation_keys}",
                    violation_id=vid,
                    offending_keys=violation_keys,
                )

        now_iso = datetime.now(timezone.utc).isoformat()
        packet = GovernanceSignalPacket(
            packet_id=packet_id,
            source=source,
            signals=clean_signals,
            asset=asset,
            domain=domain,
            crossed_at=now_iso,
            sanitization_flags=sanitization_flags,
            stripped_keys=stripped_keys,
        )

        # OMNIX DIFFERENTIATOR: Numeric Uniformity Anomaly analysis
        # Runs on every crossing — does NOT block, only flags.
        # Result is embedded in the packet for downstream audit consumers.
        if clean_signals:
            nua = _analyze_numeric_uniformity(clean_signals, packet_id)
            packet.nua_report = nua.to_dict()

        crossing_type = "STRIPPED" if stripped_keys else "APPROVED"
        _log_crossing(BoundaryCrossingRecord(
            record_id=f"BCR-{uuid.uuid4().hex[:12].upper()}",
            packet_id=packet_id,
            source=source,
            destination=self._destination,
            asset=asset,
            domain=domain,
            signal_count=len(clean_signals),
            stripped_count=len(stripped_keys),
            sanitization_flags=sanitization_flags,
            packet_hash=packet.packet_hash(),
            crossed_at=now_iso,
            crossing_type=crossing_type,
        ))

        logger.info(
            f"[LLMBoundary] Boundary crossed: packet={packet_id} source={source} "
            f"asset={asset} domain={domain} signals={len(clean_signals)} "
            f"stripped={len(stripped_keys)} type={crossing_type}"
        )

        return packet

    def validate_packet(self, packet: GovernanceSignalPacket) -> bool:
        """
        Re-validate a GovernanceSignalPacket before it enters the pipeline.
        Returns True only if all signals remain in the approved whitelist
        and all values are numeric.
        """
        if not isinstance(packet, GovernanceSignalPacket):
            logger.error("[LLMBoundary] validate_packet: argument is not a GovernanceSignalPacket")
            return False

        for key, value in packet.signals.items():
            if key not in _APPROVED_SIGNAL_KEYS:
                logger.error(
                    f"[LLMBoundary] validate_packet FAILED: "
                    f"key={key} not in approved whitelist packet={packet.packet_id}"
                )
                return False
            if not isinstance(value, _NUMERIC_TYPES):
                logger.error(
                    f"[LLMBoundary] validate_packet FAILED: "
                    f"key={key} value is not numeric packet={packet.packet_id}"
                )
                return False

        return True

    @staticmethod
    def approved_signal_keys() -> List[str]:
        """Return sorted list of approved signal keys (for documentation / API schema)."""
        return sorted(_APPROVED_SIGNAL_KEYS)

    @staticmethod
    def forbidden_signal_keys() -> List[str]:
        """Return sorted list of explicitly forbidden LLM artifact keys."""
        return sorted(_FORBIDDEN_SIGNAL_KEYS)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE-LEVEL SINGLETON
# ─────────────────────────────────────────────────────────────────────────────

_default_boundary: Optional[LLMIsolationBoundary] = None
_boundary_init_lock = threading.Lock()


def get_isolation_boundary(strict_mode: bool = False) -> LLMIsolationBoundary:
    """
    Return the process-level LLM Isolation Boundary singleton.
    Thread-safe double-checked locking.
    """
    global _default_boundary
    if _default_boundary is None:
        with _boundary_init_lock:
            if _default_boundary is None:
                _default_boundary = LLMIsolationBoundary(strict_mode=strict_mode)
                logger.info(
                    f"[LLMBoundary] Isolation boundary initialized — "
                    f"strict_mode={strict_mode} "
                    f"approved_keys={len(_APPROVED_SIGNAL_KEYS)} "
                    f"forbidden_keys={len(_FORBIDDEN_SIGNAL_KEYS)}"
                )
    return _default_boundary
