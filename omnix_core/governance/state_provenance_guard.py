"""
OMNIX State Provenance Guard (SPG) — ADR-133

Answers Eduardo Monteiro's pre-bind formation question:
    "Can this state be explained by more than one plausible lineage
     before consequence is bound to it?"

Architecture position:
    Layer 0  — Structural Admissibility Engine  (SAE)
    Layer 0b — State Provenance Guard           ← THIS MODULE
    Layer 1  — OMNIX Runtime Pipeline (CP-0 … CP-11 + TIE)
    Layer 2  — Trajectory Invariant Engine
    Layer 3  — PQC Evidence & Receipt Layer

Core guarantee:
    Any state that enters the OMNIX pipeline and passes Layer 0 structural
    checks may still carry lineage ambiguity — multiple causal hypotheses
    that equally explain the inputs. The SPG surfaces this ambiguity at the
    only moment it is still actionable: before the decision is formed and
    bound to a consequence.

    A compliant, internally consistent, fully traceable state can still be
    AMBIGUOUS in provenance. The SPG does not re-evaluate content —
    it evaluates FORMATION.

Modes:
    ADVISORY (default): SPG result embeds in receipt; pipeline continues.
    BLOCKING: AMBIGUOUS verdict blocks the evaluation (fail-closed).

Design principles:
    • Fail-closed: any exception → INDETERMINATE (advisory) or BLOCKED
    • Non-blocking by default — preserves backward compatibility
    • Full audit trail: verdict, score, hypothesis fits, contradictions
    • Thread-safe: stateless evaluation (no shared mutable state)
    • TESTING mode: no background threads

ADR Reference: ADR-133
Regulatory alignment:
    • EU AI Act Art. 9 — Risk management, traceability of AI state
    • MiFID II — Pre-trade formation audit
    • NIST AI RMF — Provenance and lineage accountability
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
from enum import Enum
from typing import Any

logger = logging.getLogger("OMNIX.SPG")


# ── Enums ────────────────────────────────────────────────────────────────────────

class ProvenanceVerdict(str, Enum):
    SINGULAR      = "SINGULAR"       # State resolves to one unique causal origin
    AMBIGUOUS     = "AMBIGUOUS"      # State compatible with multiple causal hypotheses
    INDETERMINATE = "INDETERMINATE"  # Insufficient signal to determine provenance


class SPGMode(str, Enum):
    ADVISORY = "ADVISORY"  # Result embeds in receipt; pipeline continues regardless
    BLOCKING = "BLOCKING"  # AMBIGUOUS verdict blocks the evaluation (fail-closed)


# ── Market Hypothesis Definitions ────────────────────────────────────────────────
#
# Each hypothesis represents a distinct causal state of the market that could
# generate a specific pattern of governance signals. A signal state is SINGULAR
# when it is compatible with exactly one hypothesis. AMBIGUOUS when multiple
# incompatible hypotheses explain it equally well.
#
# Hypothesis format:
#   {
#     "name":       str,
#     "conditions": list[dict]  — each condition has: signal, operator, threshold
#     "fit_floor":  float       — minimum proportion of conditions that must be met
#   }

_HYPOTHESES: list[dict] = [
    {
        "name": "BULLISH",
        "description": "Strong positive directional state with controlled risk",
        "conditions": [
            {"signal": "probability_score",  "op": "gte", "threshold": 62.0},
            {"signal": "risk_exposure",      "op": "lte", "threshold": 48.0},
            {"signal": "trend_persistence",  "op": "gte", "threshold": 56.0},
            {"signal": "signal_coherence",   "op": "gte", "threshold": 58.0},
        ],
        "fit_floor": 0.70,
    },
    {
        "name": "BEARISH",
        "description": "Negative directional state with elevated risk signals",
        "conditions": [
            {"signal": "probability_score",  "op": "lte", "threshold": 44.0},
            {"signal": "risk_exposure",      "op": "gte", "threshold": 56.0},
            {"signal": "trend_persistence",  "op": "lte", "threshold": 44.0},
            {"signal": "stress_resilience",  "op": "lte", "threshold": 50.0},
        ],
        "fit_floor": 0.70,
    },
    {
        "name": "RANGING",
        "description": "Neutral, range-bound state — no dominant directional pressure",
        "conditions": [
            {"signal": "probability_score",  "op": "range", "low": 44.0, "high": 62.0},
            {"signal": "risk_exposure",      "op": "range", "low": 38.0, "high": 62.0},
            {"signal": "trend_persistence",  "op": "range", "low": 38.0, "high": 62.0},
        ],
        "fit_floor": 0.65,
    },
    {
        "name": "HIGH_VOLATILITY",
        "description": "Elevated risk and stress with degraded resilience",
        "conditions": [
            {"signal": "risk_exposure",      "op": "gte", "threshold": 68.0},
            {"signal": "stress_resilience",  "op": "lte", "threshold": 42.0},
            {"signal": "signal_coherence",   "op": "lte", "threshold": 52.0},
        ],
        "fit_floor": 0.65,
    },
    {
        "name": "STABLE_LOW_RISK",
        "description": "Low risk, high resilience, stable formation",
        "conditions": [
            {"signal": "risk_exposure",      "op": "lte", "threshold": 34.0},
            {"signal": "stress_resilience",  "op": "gte", "threshold": 66.0},
            {"signal": "logic_consistency",  "op": "gte", "threshold": 64.0},
        ],
        "fit_floor": 0.65,
    },
]


# ── Internal contradiction pairs ─────────────────────────────────────────────────
#
# Pairs of signals that should have an expected directional relationship.
# When they violate that relationship significantly, it is evidence of
# multi-lineage formation — different sub-states producing contradictory signals.
#
# Format: (signal_a, signal_b, expected_relationship, tolerance)
#   expected_relationship: "inverse" | "direct"
#   If "inverse": high(a) should pair with low(b). Contradiction = high+high or low+low.
#   If "direct":  high(a) should pair with high(b). Contradiction = high+low.
#   tolerance: how many points apart they can be before we flag a contradiction.

_CONTRADICTION_PAIRS: list[dict] = [
    {
        "signal_a":    "probability_score",
        "signal_b":    "risk_exposure",
        "relationship": "inverse",
        "tolerance":   24.0,
        "description": "High probability with high risk — contradictory formation signal",
        "severity":    "HIGH",
    },
    {
        "signal_a":    "stress_resilience",
        "signal_b":    "risk_exposure",
        "relationship": "inverse",
        "tolerance":   26.0,
        "description": "High resilience with high risk — internally inconsistent state",
        "severity":    "HIGH",
    },
    {
        "signal_a":    "signal_coherence",
        "signal_b":    "logic_consistency",
        "relationship": "direct",
        "tolerance":   22.0,
        "description": "Coherent signals with inconsistent logic — multi-source artefact",
        "severity":    "MEDIUM",
    },
    {
        "signal_a":    "trend_persistence",
        "signal_b":    "probability_score",
        "relationship": "direct",
        "tolerance":   28.0,
        "description": "High trend persistence with low probability — contradictory directional state",
        "severity":    "MEDIUM",
    },
]


# ── Result dataclass ──────────────────────────────────────────────────────────────

@dataclass
class SPGResult:
    """
    Full state provenance evaluation result.

    Embeds in every decision receipt as `state_provenance` block.
    All fields are audit-ready and machine-readable.

    Fields:
        verdict:               SINGULAR | AMBIGUOUS | INDETERMINATE
        lineage_singularity:   0–100 score (100 = fully singular origin)
        dominant_hypothesis:   name of the hypothesis with highest fit
        hypothesis_fits:       fit score per hypothesis (0–1)
        contradictions:        list of internal signal contradictions detected
        contradiction_count:   total contradictions found
        evaluation_mode:       ADVISORY | BLOCKING
        blocked:               True only when mode=BLOCKING and verdict=AMBIGUOUS
        spg_id:                unique evaluation identifier
        evaluated_at:          ISO-8601 UTC timestamp
        elapsed_ms:            evaluation latency in milliseconds
        signal_count:          number of signals evaluated
        adr_reference:         "ADR-133"
        provenance_hash:       SHA-256 of (spg_id + verdict + lineage_singularity)
    """
    verdict:              ProvenanceVerdict
    lineage_singularity:  float
    dominant_hypothesis:  str | None
    hypothesis_fits:      dict[str, float]
    contradictions:       list[dict]
    contradiction_count:  int
    evaluation_mode:      SPGMode
    blocked:              bool
    spg_id:               str
    evaluated_at:         str
    elapsed_ms:           float
    signal_count:         int
    adr_reference:        str = "ADR-133"
    provenance_hash:      str = ""

    def to_dict(self) -> dict:
        return {
            "verdict":              self.verdict.value,
            "lineage_singularity":  round(self.lineage_singularity, 2),
            "dominant_hypothesis":  self.dominant_hypothesis,
            "hypothesis_fits":      {k: round(v, 4) for k, v in self.hypothesis_fits.items()},
            "contradictions":       self.contradictions,
            "contradiction_count":  self.contradiction_count,
            "evaluation_mode":      self.evaluation_mode.value,
            "blocked":              self.blocked,
            "spg_id":               self.spg_id,
            "evaluated_at":         self.evaluated_at,
            "elapsed_ms":           round(self.elapsed_ms, 3),
            "signal_count":         self.signal_count,
            "adr_reference":        self.adr_reference,
            "provenance_hash":      self.provenance_hash,
        }


# ── Core evaluation functions ─────────────────────────────────────────────────────

def _check_condition(value: float, condition: dict) -> bool:
    """Evaluate a single hypothesis condition against a signal value."""
    op = condition["op"]
    if op == "gte":
        return value >= condition["threshold"]
    if op == "lte":
        return value <= condition["threshold"]
    if op == "range":
        return condition["low"] <= value <= condition["high"]
    return False


def _evaluate_hypothesis(signals: dict[str, float], hyp: dict) -> float:
    """
    Compute the fit score (0–1) of a hypothesis against a signal set.

    Fit = proportion of conditions satisfied.
    Returns 0.0 if the hypothesis fit_floor is not reached.
    """
    conditions = hyp["conditions"]
    if not conditions:
        return 0.0
    satisfied = 0
    for cond in conditions:
        sig_name = cond["signal"]
        if sig_name not in signals:
            continue
        if _check_condition(signals[sig_name], cond):
            satisfied += 1
    raw_fit = satisfied / len(conditions)
    return raw_fit if raw_fit >= hyp.get("fit_floor", 0.0) else 0.0


def _detect_contradictions(signals: dict[str, float]) -> list[dict]:
    """
    Detect internal signal contradictions — evidence of multi-lineage formation.

    Returns a list of contradiction records, each containing:
        signal_a, signal_b, relationship, value_a, value_b,
        deviation, severity, description
    """
    found = []
    for pair in _CONTRADICTION_PAIRS:
        sig_a = pair["signal_a"]
        sig_b = pair["signal_b"]
        if sig_a not in signals or sig_b not in signals:
            continue

        val_a = signals[sig_a]
        val_b = signals[sig_b]
        tol   = pair["tolerance"]
        rel   = pair["relationship"]

        contradiction = False
        deviation     = 0.0

        if rel == "inverse":
            # Expected: when a is high, b should be low
            # Contradiction: both high (val_a + val_b > 100 + tolerance)
            # or both low (val_a + val_b < 100 - tolerance)
            combined = val_a + val_b
            mid = 100.0
            if combined > mid + tol:
                contradiction = True
                deviation = combined - mid - tol
            elif combined < mid - tol:
                contradiction = True
                deviation = mid - tol - combined

        elif rel == "direct":
            # Expected: a and b should be close
            # Contradiction: large divergence
            diff = abs(val_a - val_b)
            if diff > tol:
                contradiction = True
                deviation = diff - tol

        if contradiction:
            found.append({
                "signal_a":     sig_a,
                "signal_b":     sig_b,
                "relationship":  rel,
                "value_a":      round(val_a, 2),
                "value_b":      round(val_b, 2),
                "deviation":    round(deviation, 2),
                "tolerance":    tol,
                "severity":     pair["severity"],
                "description":  pair["description"],
            })

    return found


def _compute_lineage_singularity(
    hypothesis_fits: dict[str, float],
    contradictions:  list[dict],
    active_count:    int,
) -> float:
    """
    Compute the lineage singularity score (0–100).

    Logic:
        Start at 100.
        - Deduct for each additional hypothesis that is active (fits > 0).
          Each extra hypothesis represents an alternative causal explanation.
        - Deduct for each internal contradiction detected.
          Contradictions indicate multi-source signal formation.

    Score bands:
        80–100 : SINGULAR  — one causal origin dominates unambiguously
        50–79  : boundary  — borderline, ambiguity possible
        0–49   : AMBIGUOUS — multiple origins plausible
    """
    score = 100.0

    # Penalty per extra hypothesis (beyond the dominant one)
    extra = max(0, active_count - 1)
    score -= extra * 18.0

    # Penalty per contradiction — weighted by severity
    severity_weight = {"HIGH": 14.0, "MEDIUM": 8.0, "LOW": 4.0}
    for c in contradictions:
        score -= severity_weight.get(c.get("severity", "MEDIUM"), 8.0)

    return max(0.0, min(100.0, score))


def _compute_provenance_hash(spg_id: str, verdict: str, score: float) -> str:
    """Tamper-evident hash of the provenance evaluation outcome."""
    payload = json.dumps(
        {"spg_id": spg_id, "verdict": verdict, "lineage_singularity": round(score, 6)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ── Main class ────────────────────────────────────────────────────────────────────

class StateProvenanceGuard:
    """
    OMNIX State Provenance Guard — ADR-133.

    Evaluates whether an incoming signal state has a singular causal origin
    before it is bound to a governance decision.

    Usage (advisory, default):
        spg  = StateProvenanceGuard()
        spgr = spg.evaluate(signals)
        # spgr.verdict in {SINGULAR, AMBIGUOUS, INDETERMINATE}
        # spgr.blocked is always False in ADVISORY mode

    Usage (blocking):
        spg  = StateProvenanceGuard(mode=SPGMode.BLOCKING)
        spgr = spg.evaluate(signals)
        if spgr.blocked:
            return BLOCKED_response

    Thread safety: stateless — safe for concurrent use without locking.
    """

    _SINGULAR_FLOOR:   float = 80.0   # lineage_singularity >= this → SINGULAR
    _AMBIGUOUS_CEIL:   float = 50.0   # lineage_singularity <  this → AMBIGUOUS
    _HYP_ACTIVE_MIN:   float = 0.0001 # minimum fit to count a hypothesis as active

    def __init__(self, mode: SPGMode = SPGMode.ADVISORY) -> None:
        self.mode = mode

    def evaluate(
        self,
        signals:   dict[str, Any],
        domain:    str = "trading",
        asset:     str = "",
        client_id: str = "UNKNOWN",
    ) -> SPGResult:
        """
        Evaluate state provenance for a signal set.

        Args:
            signals:   Normalized governance signals (0–100 float values).
                       At minimum: probability_score, risk_exposure, signal_coherence,
                       trend_persistence, stress_resilience, logic_consistency.
            domain:    Governance domain (for logging only).
            asset:     Asset identifier (for logging only).
            client_id: Client identifier (for logging only).

        Returns:
            SPGResult — full provenance evaluation. Never raises.
        """
        t0         = time.time()
        spg_id     = f"SPG-{uuid.uuid4().hex[:12].upper()}"
        ts         = datetime.now(timezone.utc).isoformat()

        try:
            return self._run(signals, domain, asset, client_id, spg_id, ts, t0)
        except Exception as exc:
            logger.error(
                "[SPG] Evaluation exception — %s | domain=%s asset=%s: %s",
                spg_id, domain, asset, exc,
            )
            elapsed = (time.time() - t0) * 1000
            verdict = ProvenanceVerdict.INDETERMINATE
            return SPGResult(
                verdict             = verdict,
                lineage_singularity = 0.0,
                dominant_hypothesis = None,
                hypothesis_fits     = {},
                contradictions      = [],
                contradiction_count = 0,
                evaluation_mode     = self.mode,
                blocked             = False,   # fail-safe: never block on SPG exception
                spg_id              = spg_id,
                evaluated_at        = ts,
                elapsed_ms          = round(elapsed, 3),
                signal_count        = 0,
                provenance_hash     = _compute_provenance_hash(spg_id, verdict.value, 0.0),
            )

    def _run(
        self,
        signals:   dict[str, Any],
        domain:    str,
        asset:     str,
        client_id: str,
        spg_id:    str,
        ts:        str,
        t0:        float,
    ) -> SPGResult:
        # ── 1. Normalise signals ────────────────────────────────────────────────
        float_signals: dict[str, float] = {}
        for k, v in signals.items():
            try:
                float_signals[k] = float(v)
            except (TypeError, ValueError):
                pass

        signal_count = len(float_signals)

        if signal_count < 3:
            # Not enough signals to form a provenance opinion
            elapsed = (time.time() - t0) * 1000
            verdict = ProvenanceVerdict.INDETERMINATE
            score   = 0.0
            return SPGResult(
                verdict             = verdict,
                lineage_singularity = score,
                dominant_hypothesis = None,
                hypothesis_fits     = {},
                contradictions      = [],
                contradiction_count = 0,
                evaluation_mode     = self.mode,
                blocked             = False,
                spg_id              = spg_id,
                evaluated_at        = ts,
                elapsed_ms          = round(elapsed, 3),
                signal_count        = signal_count,
                provenance_hash     = _compute_provenance_hash(spg_id, verdict.value, score),
            )

        # ── 2. Hypothesis evaluation ────────────────────────────────────────────
        hypothesis_fits: dict[str, float] = {}
        for hyp in _HYPOTHESES:
            fit = _evaluate_hypothesis(float_signals, hyp)
            hypothesis_fits[hyp["name"]] = fit

        active_hyps = {
            name: fit
            for name, fit in hypothesis_fits.items()
            if fit > self._HYP_ACTIVE_MIN
        }
        active_count = len(active_hyps)

        dominant_hypothesis: str | None = None
        if active_hyps:
            dominant_hypothesis = max(active_hyps, key=lambda n: active_hyps[n])

        # ── 3. Contradiction detection ──────────────────────────────────────────
        contradictions = _detect_contradictions(float_signals)

        # ── 4. Lineage singularity score ────────────────────────────────────────
        score = _compute_lineage_singularity(hypothesis_fits, contradictions, active_count)

        # ── 5. Verdict ──────────────────────────────────────────────────────────
        if score >= self._SINGULAR_FLOOR:
            verdict = ProvenanceVerdict.SINGULAR
        elif score < self._AMBIGUOUS_CEIL or len(contradictions) >= 2:
            verdict = ProvenanceVerdict.AMBIGUOUS
        else:
            verdict = ProvenanceVerdict.INDETERMINATE

        blocked = (self.mode == SPGMode.BLOCKING and verdict == ProvenanceVerdict.AMBIGUOUS)

        # ── 6. Logging ──────────────────────────────────────────────────────────
        elapsed = (time.time() - t0) * 1000
        ph      = _compute_provenance_hash(spg_id, verdict.value, score)

        if verdict == ProvenanceVerdict.SINGULAR:
            logger.info(
                "✅ [SPG] SINGULAR_PROVENANCE | %s | domain=%s asset=%s "
                "score=%.1f dominant=%s contradictions=%d | elapsed=%.2fms",
                spg_id, domain, asset, score, dominant_hypothesis,
                len(contradictions), elapsed,
            )
        elif verdict == ProvenanceVerdict.AMBIGUOUS:
            level = logger.warning if not blocked else logger.error
            level(
                "%s [SPG] AMBIGUOUS_PROVENANCE | %s | domain=%s asset=%s "
                "score=%.1f active_hypotheses=%d contradictions=%d blocked=%s | elapsed=%.2fms",
                "🚨" if blocked else "⚠️",
                spg_id, domain, asset, score, active_count,
                len(contradictions), blocked, elapsed,
            )
        else:
            logger.debug(
                "[SPG] INDETERMINATE_PROVENANCE | %s | domain=%s asset=%s "
                "score=%.1f signals=%d | elapsed=%.2fms",
                spg_id, domain, asset, score, signal_count, elapsed,
            )

        return SPGResult(
            verdict             = verdict,
            lineage_singularity = score,
            dominant_hypothesis = dominant_hypothesis,
            hypothesis_fits     = hypothesis_fits,
            contradictions      = contradictions,
            contradiction_count = len(contradictions),
            evaluation_mode     = self.mode,
            blocked             = blocked,
            spg_id              = spg_id,
            evaluated_at        = ts,
            elapsed_ms          = round(elapsed, 3),
            signal_count        = signal_count,
            provenance_hash     = ph,
        )


# ── Module-level singleton ────────────────────────────────────────────────────────

_spg_instance: StateProvenanceGuard | None = None
_spg_lock = threading.Lock()


def get_global_spg(mode: SPGMode = SPGMode.ADVISORY) -> StateProvenanceGuard:
    """
    Return the module-level singleton StateProvenanceGuard.

    Lazy-initialised on first call. Thread-safe.
    Mode is set on first initialisation — subsequent calls with different
    mode are ignored (use StateProvenanceGuard() directly if you need a
    different mode per call).
    """
    global _spg_instance
    if _spg_instance is None:
        with _spg_lock:
            if _spg_instance is None:
                _spg_instance = StateProvenanceGuard(mode=mode)
    return _spg_instance


def evaluate_provenance(
    signals:   dict[str, Any],
    domain:    str = "trading",
    asset:     str = "",
    client_id: str = "UNKNOWN",
    mode:      SPGMode = SPGMode.ADVISORY,
) -> SPGResult:
    """
    Convenience function — evaluate state provenance with the global SPG instance.

    Never raises. Returns an SPGResult with INDETERMINATE verdict on any error.

    Args:
        signals:   Normalized governance signals (0–100 float values).
        domain:    Governance domain label.
        asset:     Asset identifier.
        client_id: Client identifier.
        mode:      ADVISORY (default) or BLOCKING.

    Returns:
        SPGResult — full provenance evaluation.
    """
    try:
        spg = get_global_spg(mode=mode)
        return spg.evaluate(signals=signals, domain=domain, asset=asset, client_id=client_id)
    except Exception as exc:
        logger.error("[SPG] evaluate_provenance outer exception: %s", exc)
        spg_id  = f"SPG-FALLBACK-{uuid.uuid4().hex[:8].upper()}"
        verdict = ProvenanceVerdict.INDETERMINATE
        return SPGResult(
            verdict             = verdict,
            lineage_singularity = 0.0,
            dominant_hypothesis = None,
            hypothesis_fits     = {},
            contradictions      = [],
            contradiction_count = 0,
            evaluation_mode     = mode,
            blocked             = False,
            spg_id              = spg_id,
            evaluated_at        = datetime.now(timezone.utc).isoformat(),
            elapsed_ms          = 0.0,
            signal_count        = 0,
            provenance_hash     = _compute_provenance_hash(spg_id, verdict.value, 0.0),
        )
