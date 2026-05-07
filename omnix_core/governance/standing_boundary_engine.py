"""
OMNIX — Standing Boundary Engine (SBE)
ADR-139 — MOD-015

Computes a numeric Standing Margin from an 8-dimension Standing Vector and
maps it to one of six extended OMNIX decision classes:

    APPROVED   — positive margin, full execution authorized
    NARROW     — marginal positive; scope reduction applied before bind
    QUARANTINE — signal integrity compromised; payload isolated, bind suspended
    REBOUND    — margin negative; returns execution to last admissible posture
    HOLD       — margin indeterminate; supervisor escalation required
    BLOCKED    — hard refusal; margin below absolute floor

Architecture position:
    Layer 4 — Standing Boundary Engine             ← THIS MODULE
    Layer 0   SAE  — Structural Admissibility Engine   (ADR-092)
    Layer 0b  SPG  — State Provenance Guard            (ADR-133)
    Layer 0c  CBG  — Conditional Bind Gate [opt-in]    (ADR-135)
    Layer 1-2 CP   — 11-Checkpoint Pipeline + TIE      (ADR-028/053)
    Layer 3   PQC  — Cryptographic Receipt             (ADR-096)
    Layer 4   SBE  — Standing Boundary Engine          ← HERE

Design invariants:
    1. Fail-closed: any exception → BLOCKED with standing_margin = None.
    2. standing_margin is always included in ControlReceipt.
    3. SBE never overrides a prior BLOCKED or HOLD — it only refines APPROVED.
    4. All 8 standing dimensions are returned for full audit transparency.
    5. standing_margin range: [-1.0, +1.0]. Positive = admitted. Negative = refused.
    6. NARROW is the only class that permits a consequential action at reduced scope.
    7. QUARANTINE does not destroy the payload — it isolates it for later review.
    8. REBOUND references the prior admissible control_id (if known).

Standing Vector Dimensions (OMNIX-native adaptation):
    1. authority_score       — domain authorization level (0–1)
    2. policy_compliance     — compliance gate pass rate (0–1)
    3. signal_integrity      — provenance quality from SPG (0–1)
    4. capacity_margin       — exposure headroom vs. limits (0–1)
    5. coherence_score       — internal signal consistency (0–1)
    6. trajectory_stability  — TIE momentum alignment (0–1)
    7. execution_readiness   — readiness for irreversible consequence (0–1)
    8. debt_load_inverted    — 1 − accumulated risk load (0–1)

Implemented: May 2026
ADR-139
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Optional

logger = logging.getLogger("OMNIX.SBE")


# ── Decision classes ──────────────────────────────────────────────────────────

class ExtendedDecision(str, Enum):
    APPROVED   = "APPROVED"
    NARROW     = "NARROW"
    QUARANTINE = "QUARANTINE"
    REBOUND    = "REBOUND"
    HOLD       = "HOLD"
    BLOCKED    = "BLOCKED"


# ── Standing vector ───────────────────────────────────────────────────────────

@dataclass
class StandingVector:
    """
    8-dimension standing vector. Each dimension: float in [0, 1].
    Zero means completely degraded; one means fully nominal.
    """
    authority_score:      float = 1.0
    policy_compliance:    float = 1.0
    signal_integrity:     float = 1.0
    capacity_margin:      float = 1.0
    coherence_score:      float = 1.0
    trajectory_stability: float = 1.0
    execution_readiness:  float = 1.0
    debt_load_inverted:   float = 1.0

    # Dimension weights — must sum to 1.0
    # ClassVar: not part of __init__, not overridable by positional args
    _WEIGHTS: ClassVar[dict] = {
        "authority_score":      0.18,
        "policy_compliance":    0.18,
        "signal_integrity":     0.16,
        "capacity_margin":      0.14,
        "coherence_score":      0.12,
        "trajectory_stability": 0.10,
        "execution_readiness":  0.07,
        "debt_load_inverted":   0.05,
    }

    # Minimum per-dimension thresholds — falling below triggers dimension failure
    # ClassVar: not part of __init__, not overridable by positional args
    _MIN_THRESHOLDS: ClassVar[dict] = {
        "authority_score":      0.50,
        "policy_compliance":    0.60,
        "signal_integrity":     0.40,
        "capacity_margin":      0.20,
        "coherence_score":      0.30,
        "trajectory_stability": 0.20,
        "execution_readiness":  0.30,
        "debt_load_inverted":   0.10,
    }

    def weighted_score(self) -> float:
        """Weighted sum of all standing dimensions. Range [0, 1]."""
        w = self._WEIGHTS
        return (
            self.authority_score      * w["authority_score"]      +
            self.policy_compliance    * w["policy_compliance"]     +
            self.signal_integrity     * w["signal_integrity"]      +
            self.capacity_margin      * w["capacity_margin"]       +
            self.coherence_score      * w["coherence_score"]       +
            self.trajectory_stability * w["trajectory_stability"]  +
            self.execution_readiness  * w["execution_readiness"]   +
            self.debt_load_inverted   * w["debt_load_inverted"]
        )

    def failed_dimensions(self) -> list[str]:
        """Returns list of dimension names that fell below their minimum threshold."""
        mins = self._MIN_THRESHOLDS
        failed = []
        for dim, threshold in mins.items():
            val = getattr(self, dim, 1.0)
            if val < threshold:
                failed.append(dim)
        return failed

    def to_dict(self) -> dict:
        return {
            "authority_score":      round(self.authority_score, 4),
            "policy_compliance":    round(self.policy_compliance, 4),
            "signal_integrity":     round(self.signal_integrity, 4),
            "capacity_margin":      round(self.capacity_margin, 4),
            "coherence_score":      round(self.coherence_score, 4),
            "trajectory_stability": round(self.trajectory_stability, 4),
            "execution_readiness":  round(self.execution_readiness, 4),
            "debt_load_inverted":   round(self.debt_load_inverted, 4),
        }


# ── SBE result ────────────────────────────────────────────────────────────────

@dataclass
class SBEResult:
    """Result of a Standing Boundary Engine evaluation."""
    sbe_id:            str
    decision:          ExtendedDecision
    standing_margin:   float                    # range [-1.0, +1.0]
    standing_vector:   StandingVector
    failed_dimensions: list[str]
    narrowed_scope:    Optional[dict]           # populated for NARROW decisions
    quarantine_token:  Optional[str]            # populated for QUARANTINE
    rebound_target_id: Optional[str]            # prior admissible control_id
    resolution_note:   str
    latency_ms:        float = 0.0
    adr:               str   = "ADR-139"

    def to_dict(self) -> dict:
        return {
            "sbe_id":            self.sbe_id,
            "decision":          self.decision.value,
            "standing_margin":   round(self.standing_margin, 4),
            "standing_vector":   self.standing_vector.to_dict(),
            "failed_dimensions": self.failed_dimensions,
            "narrowed_scope":    self.narrowed_scope,
            "quarantine_token":  self.quarantine_token,
            "rebound_target_id": self.rebound_target_id,
            "resolution_note":   self.resolution_note,
            "latency_ms":        round(self.latency_ms, 2),
            "adr":               self.adr,
        }


# ── Standing margin decision bands ───────────────────────────────────────────
#
#  standing_margin = weighted_score − EXECUTION_FLOOR
#  EXECUTION_FLOOR = 0.65 (the minimum weighted score for full approval)
#
#   > +0.20        → APPROVED      (clear headroom)
#    +0.05 to +0.20 → APPROVED      (narrow headroom — flagged in receipt)
#    +0.01 to +0.05 → NARROW        (scope reduction applied before bind)
#    -0.05 to +0.01 → QUARANTINE    (marginal; isolate payload, suspend bind)
#    -0.15 to -0.05 → REBOUND       (below floor; return to last admissible)
#    < -0.15        → BLOCKED       (hard refusal)
#
# Additionally, if signal_integrity < 0.40 AND weighted_score is positive:
#    → QUARANTINE (integrity failure overrides margin)
#
# If trajectory_stability is critically degraded (<0.10):
#    → REBOUND (execution posture must return to last stable state)

EXECUTION_FLOOR    = 0.65   # minimum weighted score for full approval
NARROW_FLOOR       = 0.66   # 0.65 + 0.01
QUARANTINE_FLOOR   = 0.60   # 0.65 - 0.05
REBOUND_FLOOR      = 0.50   # 0.65 - 0.15

SIGNAL_INTEGRITY_QUARANTINE_THRESHOLD   = 0.40
TRAJECTORY_STABILITY_REBOUND_THRESHOLD  = 0.10


# ── Main engine ───────────────────────────────────────────────────────────────

class StandingBoundaryEngine:
    """
    MOD-015 — Standing Boundary Engine.

    Computes a numeric Standing Margin from an 8-dimension Standing Vector
    and resolves the appropriate extended decision class.

    Usage:
        sbe = StandingBoundaryEngine()
        vector = StandingBoundaryEngine.vector_from_pillar_results(pillar_results, evaluation)
        result = sbe.evaluate(vector, asset=asset, domain=domain)
    """

    VERSION = "1.0.0"
    ADR     = "ADR-139"

    @staticmethod
    def _new_sbe_id() -> str:
        import secrets
        return "SBE-" + secrets.token_hex(6).upper()

    @staticmethod
    def _quarantine_token(sbe_id: str, asset: str, domain: str) -> str:
        payload = f"{sbe_id}:{asset}:{domain}:{time.time()}"
        return "QT-" + hashlib.sha256(payload.encode()).hexdigest()[:16].upper()

    @classmethod
    def vector_from_pillar_results(
        cls,
        pillar_results: list,
        evaluation:     dict,
        prior_decision: str = "APPROVED",
    ) -> StandingVector:
        """
        Derives a StandingVector from existing UDCL pillar results and
        the raw checkpoint pipeline evaluation dict.

        This avoids re-running evaluations — it composes the vector from
        data already collected by the UDCL pipeline.
        """
        raw_score        = evaluation.get("score")
        score            = float(raw_score) if raw_score is not None else 75.0
        score_normalized = min(max(score / 100.0, 0.0), 1.0) if score > 1.0 else score

        # -- authority_score: from SAE admission status
        sae_detail = next(
            (r.detail for r in pillar_results if r.pillar == "sae"), {}
        )
        authority_score = (
            1.0 if sae_detail.get("admission_status") == "admitted" else
            0.5 if sae_detail.get("admission_status") == "unavailable" else
            0.0
        )

        # -- policy_compliance: derived from checkpoint pass rate
        cp_detail = next(
            (r.detail for r in pillar_results if r.pillar == "checkpoint_pipeline"), {}
        )
        total_cps  = cp_detail.get("checkpoints_total", 1) or 1
        passed_cps = cp_detail.get("checkpoints_passed", 1)
        policy_compliance = round(passed_cps / total_cps, 4)

        # -- signal_integrity: from SPG lineage_singularity
        spg_detail = next(
            (r.detail for r in pillar_results if r.pillar == "spg"), {}
        )
        spg_verdict   = spg_detail.get("verdict", "SINGULAR")
        raw_lineage   = float(spg_detail.get("lineage_singularity", 100.0))
        lineage_norm  = min(max(raw_lineage / 100.0, 0.0), 1.0) if raw_lineage > 1.0 else raw_lineage
        signal_integrity = (
            lineage_norm if spg_verdict == "SINGULAR"   else
            lineage_norm * 0.6 if spg_verdict == "AMBIGUOUS" else
            0.0
        )

        # -- capacity_margin: score-derived; approximates exposure headroom
        capacity_margin = min(score_normalized * 1.1, 1.0)

        # -- coherence_score: from evaluation veto_chain (fewer vetos = more coherent)
        veto_chain   = evaluation.get("veto_chain", [])
        coherence_score = max(1.0 - (len(veto_chain) * 0.15), 0.0)

        # -- trajectory_stability: from TIE results if present; else score-derived
        gate_results       = evaluation.get("gate_results", {})
        tie_result         = gate_results.get("tie") or gate_results.get("trajectory_invariant")
        trajectory_stability = (
            float(tie_result.get("stability_score", score_normalized))
            if isinstance(tie_result, dict)
            else score_normalized
        )

        # -- execution_readiness: composite of CBG pass + no blocked checkpoints
        cbg_detail = next(
            (r.detail for r in pillar_results if r.pillar == "cbg"), {}
        )
        cbg_ok = cbg_detail.get("bind_allowed", True)
        blocked_cps = cp_detail.get("checkpoints_blocked", 0)
        execution_readiness = (
            1.0 if (cbg_ok and blocked_cps == 0) else
            0.7 if cbg_ok else
            0.3
        )

        # -- debt_load_inverted: 1 − (blocked_cps / total_cps) — lower block rate = less debt
        debt_load_inverted = 1.0 - round(
            min(blocked_cps / total_cps, 1.0), 4
        )

        return StandingVector(
            authority_score      = round(authority_score, 4),
            policy_compliance    = round(policy_compliance, 4),
            signal_integrity     = round(signal_integrity, 4),
            capacity_margin      = round(capacity_margin, 4),
            coherence_score      = round(coherence_score, 4),
            trajectory_stability = round(trajectory_stability, 4),
            execution_readiness  = round(execution_readiness, 4),
            debt_load_inverted   = round(debt_load_inverted, 4),
        )

    def evaluate(
        self,
        vector:            StandingVector,
        asset:             str,
        domain:            str,
        prior_decision:    str = "APPROVED",
        rebound_target_id: Optional[str] = None,
        original_scope:    Optional[dict] = None,
    ) -> SBEResult:
        """
        Evaluate standing vector and return SBEResult with extended decision class.

        Only refines an existing APPROVED decision.
        If prior_decision is BLOCKED or HOLD, returns it unchanged.

        Args:
            vector:            StandingVector from vector_from_pillar_results().
            asset:             Instrument or entity identifier.
            domain:            Governance vertical.
            prior_decision:    Decision from 11-Checkpoint Pipeline.
            rebound_target_id: Control ID of prior admissible evaluation (for REBOUND).
            original_scope:    Original requested scope dict (for NARROW scope reduction).
        """
        t0     = time.perf_counter()
        sbe_id = self._new_sbe_id()

        try:
            # SBE only refines APPROVED — honor prior blocks/holds
            if prior_decision in ("BLOCKED", "HOLD"):
                return SBEResult(
                    sbe_id            = sbe_id,
                    decision          = ExtendedDecision(prior_decision),
                    standing_margin   = 0.0,
                    standing_vector   = vector,
                    failed_dimensions = [],
                    narrowed_scope    = None,
                    quarantine_token  = None,
                    rebound_target_id = None,
                    resolution_note   = f"Prior decision {prior_decision} honored — SBE does not override.",
                    latency_ms        = (time.perf_counter() - t0) * 1000,
                )

            weighted = vector.weighted_score()
            margin   = round(weighted - EXECUTION_FLOOR, 4)
            failed   = vector.failed_dimensions()

            logger.info(
                "[SBE] domain=%s asset=%s weighted=%.4f margin=%.4f failed_dims=%s",
                domain, asset, weighted, margin, failed,
            )

            # ── Resolution logic ──────────────────────────────────────────────

            # QUARANTINE override: signal integrity failure regardless of margin
            if vector.signal_integrity < SIGNAL_INTEGRITY_QUARANTINE_THRESHOLD:
                qt = self._quarantine_token(sbe_id, asset, domain)
                return SBEResult(
                    sbe_id            = sbe_id,
                    decision          = ExtendedDecision.QUARANTINE,
                    standing_margin   = margin,
                    standing_vector   = vector,
                    failed_dimensions = failed,
                    narrowed_scope    = None,
                    quarantine_token  = qt,
                    rebound_target_id = None,
                    resolution_note   = (
                        f"Signal integrity {vector.signal_integrity:.2f} below quarantine "
                        f"threshold {SIGNAL_INTEGRITY_QUARANTINE_THRESHOLD}. "
                        "Payload isolated — bind suspended pending integrity restoration."
                    ),
                    latency_ms = (time.perf_counter() - t0) * 1000,
                )

            # REBOUND override: trajectory critically degraded
            if vector.trajectory_stability < TRAJECTORY_STABILITY_REBOUND_THRESHOLD:
                return SBEResult(
                    sbe_id            = sbe_id,
                    decision          = ExtendedDecision.REBOUND,
                    standing_margin   = margin,
                    standing_vector   = vector,
                    failed_dimensions = failed,
                    narrowed_scope    = None,
                    quarantine_token  = None,
                    rebound_target_id = rebound_target_id,
                    resolution_note   = (
                        f"Trajectory stability {vector.trajectory_stability:.2f} critically degraded "
                        f"(threshold {TRAJECTORY_STABILITY_REBOUND_THRESHOLD}). "
                        "Execution must return to last admissible posture."
                    ),
                    latency_ms = (time.perf_counter() - t0) * 1000,
                )

            # Margin-band decision
            if margin > 0.20:
                decision       = ExtendedDecision.APPROVED
                note           = f"Standing margin {margin:+.4f} — clear headroom. Full execution authorized."
                narrowed_scope = None
                qt             = None
                rebound_id     = None

            elif margin >= 0.05:
                decision       = ExtendedDecision.APPROVED
                note           = f"Standing margin {margin:+.4f} — narrow headroom. Full execution authorized with monitoring."
                narrowed_scope = None
                qt             = None
                rebound_id     = None

            elif margin >= 0.01:
                decision       = ExtendedDecision.NARROW
                narrowed_scope = self._compute_narrow_scope(original_scope, margin, asset)
                note           = (
                    f"Standing margin {margin:+.4f} — marginal. Scope reduced to {narrowed_scope}. "
                    "Execution permitted at reduced scope only."
                )
                qt         = None
                rebound_id = None

            elif margin >= -0.05:
                qt         = self._quarantine_token(sbe_id, asset, domain)
                decision   = ExtendedDecision.QUARANTINE
                note       = (
                    f"Standing margin {margin:+.4f} — below execution floor. "
                    f"Payload quarantined [{qt}]. Bind suspended."
                )
                narrowed_scope = None
                rebound_id     = None

            elif margin >= -0.15:
                decision       = ExtendedDecision.REBOUND
                note           = (
                    f"Standing margin {margin:+.4f} — below quarantine floor. "
                    "Execution returns to last admissible posture."
                )
                narrowed_scope = None
                qt             = None
                rebound_id     = rebound_target_id

            else:
                decision       = ExtendedDecision.BLOCKED
                note           = (
                    f"Standing margin {margin:+.4f} — below absolute floor. "
                    f"Hard refusal. Failed dimensions: {failed}."
                )
                narrowed_scope = None
                qt             = None
                rebound_id     = None

            return SBEResult(
                sbe_id            = sbe_id,
                decision          = decision,
                standing_margin   = margin,
                standing_vector   = vector,
                failed_dimensions = failed,
                narrowed_scope    = narrowed_scope,
                quarantine_token  = qt,
                rebound_target_id = rebound_id,
                resolution_note   = note,
                latency_ms        = (time.perf_counter() - t0) * 1000,
            )

        except Exception as exc:
            logger.error("[SBE] evaluation exception: %s", exc)
            safe_vector = vector if isinstance(vector, StandingVector) else StandingVector()
            return SBEResult(
                sbe_id            = sbe_id,
                decision          = ExtendedDecision.BLOCKED,
                standing_margin   = -1.0,
                standing_vector   = safe_vector,
                failed_dimensions = ["system_error"],
                narrowed_scope    = None,
                quarantine_token  = None,
                rebound_target_id = None,
                resolution_note   = f"SBE evaluation failed (fail-closed): {str(exc)[:120]}",
                latency_ms        = (time.perf_counter() - t0) * 1000,
            )

    @staticmethod
    def _compute_narrow_scope(
        original_scope: Optional[dict],
        margin:         float,
        asset:          str,
    ) -> dict:
        """
        Compute a reduced scope for a NARROW decision.

        Reduction factor is derived from how close margin is to the NARROW_FLOOR:
            reduction = 1 − (margin / 0.05) * 0.5
            → margin=0.01 → 90% reduction
            → margin=0.04 → 60% reduction
        """
        if not original_scope:
            return {
                "asset":          asset,
                "scope_reduction": "50%",
                "note":           "No original scope provided — default 50% reduction applied.",
                "adr":            "ADR-139",
            }

        reduction_factor = 1.0 - (min(margin, 0.05) / 0.05) * 0.5
        reduced_scope    = {}
        for key, val in original_scope.items():
            if isinstance(val, (int, float)) and val > 0:
                reduced_scope[key] = round(val * (1.0 - reduction_factor), 4)
            else:
                reduced_scope[key] = val

        return {
            **reduced_scope,
            "scope_reduction": f"{round(reduction_factor * 100, 1)}%",
            "original_scope":  original_scope,
            "adr":             "ADR-139",
        }
