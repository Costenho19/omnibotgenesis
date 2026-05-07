"""
OMNIX — Commit-Time Admissibility Gate (CTAG)
ADR-140 — MOD-016

Re-evaluates whether the operational conditions that originally justified an
APPROVED governance decision still hold at the moment the irreversible
consequence is about to be committed.

Architecture position:
    Layer 5 — Commit-Time Admissibility Gate          ← THIS MODULE
    Layer 0   SAE  — Structural Admissibility Engine   (ADR-092)
    Layer 0b  SPG  — State Provenance Guard            (ADR-133)
    Layer 0c  CBG  — Conditional Bind Gate [opt-in]    (ADR-135)
    Layer 1-2 CP   — 11-Checkpoint Pipeline + TIE      (ADR-028/053)
    Layer 3   PQC  — Cryptographic Receipt             (ADR-096)
    Layer 4   SBE  — Standing Boundary Engine          (ADR-139)
    Layer 5   CTAG — Commit-Time Admissibility Gate    ← HERE

Problem addressed (Akhilesh Warik's execution-boundary question):
    A PQC receipt is cryptographically valid at the moment it is issued.
    But in persistent orchestration contexts, conditions drift between
    decision-time and execution-time. The receipt remains valid; the
    operational assumptions may not.

    CTAG closes this gap by re-evaluating admissibility at commit time
    using the current standing margin, comparing it to the margin
    captured at decision time, and determining whether the original
    authorization still holds or must be revoked.

Verdicts:
    VALID       — conditions still hold; commit is authorized
    DRIFTED     — conditions changed but within tolerance; commit with caveat
    REVOKED     — conditions degraded beyond tolerance; commit refused
    INDETERMINATE — comparison not possible (missing baseline); advisory pass

Design invariants:
    1. Fail-closed for REVOKED: caller must not commit if CTAG returns REVOKED.
    2. Fail-open for INDETERMINATE: caller may proceed but receipt flags the gap.
    3. CTAG does not re-run the full pipeline — it uses the current SBE vector
       and compares it to the baseline margin from the original ControlReceipt.
    4. Drift is measured as: drift_delta = current_margin − original_margin.
    5. If drift_delta < −REVOCATION_DRIFT_THRESHOLD → REVOKED.
    6. If −REVOCATION_DRIFT_THRESHOLD ≤ drift_delta < −CAUTION_DRIFT_THRESHOLD → DRIFTED.
    7. Drift_delta ≥ −CAUTION_DRIFT_THRESHOLD → VALID.
    8. CTAG is opt-in — callers must pass ctag_enabled=true.

Drift thresholds:
    REVOCATION_DRIFT_THRESHOLD = 0.15  (15-point drop → revocation)
    CAUTION_DRIFT_THRESHOLD    = 0.05  (5-point drop → caution/DRIFTED)

Implemented: May 2026
ADR-140
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger("OMNIX.CTAG")


# ── Drift thresholds ──────────────────────────────────────────────────────────

REVOCATION_DRIFT_THRESHOLD = 0.15
CAUTION_DRIFT_THRESHOLD    = 0.05


# ── Commit verdict ────────────────────────────────────────────────────────────

class CommitVerdict(str, Enum):
    VALID         = "VALID"
    DRIFTED       = "DRIFTED"
    REVOKED       = "REVOKED"
    INDETERMINATE = "INDETERMINATE"


# ── CTAG result ───────────────────────────────────────────────────────────────

@dataclass
class CTAGResult:
    """Result of a Commit-Time Admissibility Gate evaluation."""
    ctag_id:           str
    verdict:           CommitVerdict
    commit_authorized: bool
    original_margin:   Optional[float]
    current_margin:    float
    drift_delta:       Optional[float]          # current − original; negative = degraded
    original_decision: str                       # decision on the original receipt
    original_control_id: Optional[str]
    elapsed_seconds:   float                    # seconds since original evaluation
    resolution_note:   str
    latency_ms:        float = 0.0
    adr:               str   = "ADR-140"

    def to_dict(self) -> dict:
        return {
            "ctag_id":             self.ctag_id,
            "verdict":             self.verdict.value,
            "commit_authorized":   self.commit_authorized,
            "original_margin":     round(self.original_margin, 4) if self.original_margin is not None else None,
            "current_margin":      round(self.current_margin, 4),
            "drift_delta":         round(self.drift_delta, 4) if self.drift_delta is not None else None,
            "original_decision":   self.original_decision,
            "original_control_id": self.original_control_id,
            "elapsed_seconds":     round(self.elapsed_seconds, 2),
            "resolution_note":     self.resolution_note,
            "latency_ms":          round(self.latency_ms, 2),
            "adr":                 self.adr,
        }


# ── Main gate ─────────────────────────────────────────────────────────────────

class CommitTimeAdmissibilityGate:
    """
    MOD-016 — Commit-Time Admissibility Gate.

    Answers Akhilesh Warik's execution-boundary question directly:
        OMNIX treats admissibility as BOTH:
          (a) a point-in-time cryptographic receipt (issued by PQC layer), AND
          (b) a continuously re-evaluable execution condition (via AVM + CTAG).

    The CTAG is the formal gate at (b) — it is evaluated at the moment an
    orchestration system is about to commit an irreversible consequence, and
    it determines whether the original approval still holds.

    Usage:
        ctag = CommitTimeAdmissibilityGate()
        result = ctag.evaluate(
            current_margin    = sbe_result.standing_margin,
            original_control  = {   # from original ControlReceipt.to_dict()
                "control_id":      "UDCL-...",
                "decision":        "APPROVED",
                "standing_margin": 0.18,         # set by SBE at decision time
                "issued_at":       1746617000.0,  # unix timestamp
            },
        )
    """

    VERSION = "1.0.0"
    ADR     = "ADR-140"

    @staticmethod
    def _new_ctag_id() -> str:
        return "CTAG-" + secrets.token_hex(6).upper()

    def evaluate(
        self,
        current_margin:   float,
        original_control: Optional[dict] = None,
    ) -> CTAGResult:
        """
        Re-evaluate admissibility at commit time.

        Args:
            current_margin:   Standing margin computed NOW (from SBE).
            original_control: Dict with keys: control_id, decision,
                              standing_margin, issued_at (unix timestamp).
                              If None → INDETERMINATE.
        """
        t0      = time.perf_counter()
        ctag_id = self._new_ctag_id()
        now     = time.time()

        try:
            if not original_control:
                return CTAGResult(
                    ctag_id             = ctag_id,
                    verdict             = CommitVerdict.INDETERMINATE,
                    commit_authorized   = True,
                    original_margin     = None,
                    current_margin      = current_margin,
                    drift_delta         = None,
                    original_decision   = "UNKNOWN",
                    original_control_id = None,
                    elapsed_seconds     = 0.0,
                    resolution_note     = (
                        "No original control receipt provided. CTAG cannot compare baselines. "
                        "Commit authorized with advisory flag — original conditions unverified."
                    ),
                    latency_ms = (time.perf_counter() - t0) * 1000,
                )

            original_margin    = float(original_control.get("standing_margin", 0.0))
            original_decision  = str(original_control.get("decision", "UNKNOWN"))
            original_ctrl_id   = str(original_control.get("control_id", "UNKNOWN"))
            issued_at          = float(original_control.get("issued_at", now))
            elapsed_seconds    = now - issued_at
            drift_delta        = current_margin - original_margin

            logger.info(
                "[CTAG] ctrl=%s original_margin=%.4f current_margin=%.4f "
                "drift=%.4f elapsed_s=%.1f",
                original_ctrl_id, original_margin, current_margin,
                drift_delta, elapsed_seconds,
            )

            # ── Drift verdict ─────────────────────────────────────────────────

            if drift_delta < -REVOCATION_DRIFT_THRESHOLD:
                return CTAGResult(
                    ctag_id             = ctag_id,
                    verdict             = CommitVerdict.REVOKED,
                    commit_authorized   = False,
                    original_margin     = original_margin,
                    current_margin      = current_margin,
                    drift_delta         = drift_delta,
                    original_decision   = original_decision,
                    original_control_id = original_ctrl_id,
                    elapsed_seconds     = elapsed_seconds,
                    resolution_note     = (
                        f"Admissibility REVOKED. Drift delta {drift_delta:+.4f} exceeds revocation "
                        f"threshold −{REVOCATION_DRIFT_THRESHOLD}. Original approval [{original_ctrl_id}] "
                        "is no longer valid. Commit must not proceed."
                    ),
                    latency_ms = (time.perf_counter() - t0) * 1000,
                )

            if drift_delta < -CAUTION_DRIFT_THRESHOLD:
                return CTAGResult(
                    ctag_id             = ctag_id,
                    verdict             = CommitVerdict.DRIFTED,
                    commit_authorized   = True,
                    original_margin     = original_margin,
                    current_margin      = current_margin,
                    drift_delta         = drift_delta,
                    original_decision   = original_decision,
                    original_control_id = original_ctrl_id,
                    elapsed_seconds     = elapsed_seconds,
                    resolution_note     = (
                        f"Admissibility DRIFTED. Drift delta {drift_delta:+.4f} exceeds caution "
                        f"threshold −{CAUTION_DRIFT_THRESHOLD} but is within revocation tolerance. "
                        "Commit authorized with monitoring caveat. Consider re-evaluation."
                    ),
                    latency_ms = (time.perf_counter() - t0) * 1000,
                )

            # Drift within acceptable range
            return CTAGResult(
                ctag_id             = ctag_id,
                verdict             = CommitVerdict.VALID,
                commit_authorized   = True,
                original_margin     = original_margin,
                current_margin      = current_margin,
                drift_delta         = drift_delta,
                original_decision   = original_decision,
                original_control_id = original_ctrl_id,
                elapsed_seconds     = elapsed_seconds,
                resolution_note     = (
                    f"Admissibility VALID. Drift delta {drift_delta:+.4f} within tolerance. "
                    f"Original approval [{original_ctrl_id}] still holds. Commit authorized."
                ),
                latency_ms = (time.perf_counter() - t0) * 1000,
            )

        except Exception as exc:
            logger.error("[CTAG] evaluation exception: %s", exc)
            return CTAGResult(
                ctag_id             = ctag_id,
                verdict             = CommitVerdict.REVOKED,
                commit_authorized   = False,
                original_margin     = None,
                current_margin      = current_margin,
                drift_delta         = None,
                original_decision   = "UNKNOWN",
                original_control_id = None,
                elapsed_seconds     = 0.0,
                resolution_note     = f"CTAG evaluation failed (fail-closed): {str(exc)[:120]}",
                latency_ms          = (time.perf_counter() - t0) * 1000,
            )

    @classmethod
    def get_schema(cls) -> dict:
        return {
            "module":  "MOD-016",
            "adr":     cls.ADR,
            "version": cls.VERSION,
            "description": (
                "Commit-Time Admissibility Gate — re-evaluates whether conditions that "
                "justified the original approval still hold at execution moment. "
                "Closes the gap between point-in-time receipt validity and runtime drift."
            ),
            "verdicts": {
                "VALID":         "Conditions hold — commit authorized.",
                "DRIFTED":       "Conditions changed within tolerance — commit authorized with caveat.",
                "REVOKED":       "Conditions degraded beyond tolerance — commit refused.",
                "INDETERMINATE": "Baseline unavailable — advisory pass.",
            },
            "drift_thresholds": {
                "revocation": REVOCATION_DRIFT_THRESHOLD,
                "caution":    CAUTION_DRIFT_THRESHOLD,
            },
            "design_note": (
                "OMNIX treats admissibility as both: "
                "(a) a point-in-time PQC receipt (Layer 3), and "
                "(b) a continuously re-evaluable execution condition (Layer 4 SBE + Layer 5 CTAG). "
                "CTAG is the formal gate at (b)."
            ),
        }
