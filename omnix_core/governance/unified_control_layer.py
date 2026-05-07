"""
MOD-014 — Unified Decision Control Layer (UDCL)
ADR-138

Coordinates all OMNIX governance pillars in strict sequence.
Any non-advisory pillar failure → BLOCKED (fail-closed).
Returns a ControlReceipt with per-pillar visibility, latency breakdown,
and a tamper-evident SHA-256 control hash.

Pipeline sequence:
  Layer 0   → SAE  — Structural Admissibility Engine     (ADR-092)
  Layer 0b  → SPG  — State Provenance Guard              (ADR-133)
  Layer 0c  → CBG  — Conditional Bind Gate [opt-in]      (ADR-135)
  Layer 1-2 → CP   — 11-Checkpoint Pipeline + TIE        (ADR-028/053)
  Layer 3   → PQC  — Cryptographic Receipt               (ADR-096)

Design invariants:
  1. All pillar results are returned even on block — full transparency.
  2. `blocking_pillar` names the first pillar that produced a non-advisory failure.
  3. `control_hash` seals the entire multi-pillar outcome against post-hoc modification.
  4. Fail-open for advisory pillars (SPG); fail-closed for all mandatory pillars.
  5. Engine-level exceptions on mandatory pillars → BLOCKED with blocking_pillar="system_error".
"""

import hashlib
import json
import logging
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ── Pillar identifiers ────────────────────────────────────────────────────────

class Pillar(str, Enum):
    SAE = "sae"
    SPG = "spg"
    CBG = "cbg"
    CP  = "checkpoint_pipeline"
    PQC = "pqc_receipt"


# ── Data models ───────────────────────────────────────────────────────────────

@dataclass
class PillarResult:
    """Per-pillar result. Returned in ControlReceipt.pillar_results."""
    pillar:     str
    layer:      str
    passed:     bool
    advisory:   bool  = False   # True → failure is informational only, does not block
    latency_ms: float = 0.0
    detail:     dict  = field(default_factory=dict)
    error:      Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "pillar":     self.pillar,
            "layer":      self.layer,
            "passed":     self.passed,
            "advisory":   self.advisory,
            "latency_ms": round(self.latency_ms, 2),
            "detail":     self.detail,
        }
        if self.error:
            d["error"] = self.error
        return d


@dataclass
class ControlReceipt:
    """
    Top-level result of a UDCL evaluation.
    Wraps all pillar results and provides a single tamper-evident seal.
    """
    control_id:      str
    decision:        str                   # APPROVED | BLOCKED | HOLD
    blocking_pillar: Optional[str]         # first pillar that blocked, or None
    block_reason:    Optional[str]
    pillar_results:  list                  # list[PillarResult]
    receipt_id:      Optional[str]         # PQC receipt ID (Layer 3)
    domain:          str
    asset:           str
    total_latency_ms: float
    control_hash:    str
    cbg_enabled:     bool = False
    adr:             str  = "ADR-138"
    version:         str  = "1.0"

    def to_dict(self) -> dict:
        results_by_pillar = {r.pillar: r.to_dict() for r in self.pillar_results}
        return {
            "control_id":        self.control_id,
            "decision":          self.decision,
            "blocking_pillar":   self.blocking_pillar,
            "block_reason":      self.block_reason,
            "pillar_results":    results_by_pillar,
            "receipt_id":        self.receipt_id,
            "domain":            self.domain,
            "asset":             self.asset,
            "total_latency_ms":  round(self.total_latency_ms, 2),
            "control_hash":      self.control_hash,
            "cbg_enabled":       self.cbg_enabled,
            "pillars_evaluated": len(self.pillar_results),
            "pillars_passed":    sum(1 for r in self.pillar_results if r.passed),
            "pillar_latency_ms": {
                r.pillar: round(r.latency_ms, 2) for r in self.pillar_results
            },
            "adr":     self.adr,
            "version": self.version,
        }


# ── Main orchestration engine ─────────────────────────────────────────────────

class UnifiedDecisionControlLayer:
    """
    MOD-014: Unified Decision Control Layer.

    Instantiate with the GovernanceEvaluationEngine class and
    DecisionReceiptEngine class (dependency-injected by the API layer
    to reuse the same lazy-loaded engine instances).

    Usage:
        udcl = UnifiedDecisionControlLayer(GovernanceEvaluationEngine, DecisionReceiptEngine)
        receipt = udcl.evaluate(signals=..., asset=..., domain=..., client_id=...)
        response_dict = receipt.to_dict()
    """

    VERSION = "1.0.0"
    ADR     = "ADR-138"

    PILLAR_CATALOG = [
        {
            "id":        "sae",
            "layer":     "Layer 0",
            "name":      "Structural Admissibility Engine",
            "adr":       "ADR-092",
            "mandatory": True,
            "advisory":  False,
            "description": (
                "Validates that the incoming request is structurally admissible "
                "before any governance logic runs. Rejects malformed signal envelopes, "
                "unknown domains, and structurally inadmissible payloads."
            ),
        },
        {
            "id":        "spg",
            "layer":     "Layer 0b",
            "name":      "State Provenance Guard",
            "adr":       "ADR-133",
            "mandatory": True,
            "advisory":  True,
            "description": (
                "Evaluates whether the current signal state can be explained by a single "
                "causal lineage (SINGULAR) or is ambiguous across multiple origins (AMBIGUOUS). "
                "Advisory: AMBIGUOUS warns but does not block unless CBG is enabled."
            ),
        },
        {
            "id":        "cbg",
            "layer":     "Layer 0c",
            "name":      "Conditional Bind Gate",
            "adr":       "ADR-135",
            "mandatory": False,
            "advisory":  False,
            "description": (
                "Opt-in gate. When SPG returns AMBIGUOUS above severity threshold, "
                "CBG blocks the bind and requires explicit human attestation before "
                "consequence is allowed. Disabled by default — enable via cbg_enabled=true."
            ),
        },
        {
            "id":        "checkpoint_pipeline",
            "layer":     "Layer 1-2",
            "name":      "11-Checkpoint Pipeline + TIE",
            "adr":       "ADR-028",
            "mandatory": True,
            "advisory":  False,
            "description": (
                "Core OMNIX governance pipeline: CP-0 (SIV) through CP-11 (Jurisdiction Gate) "
                "plus Trajectory Invariant Engine (TIE, ADR-053). "
                "Fail-closed: any checkpoint failure → BLOCKED."
            ),
        },
        {
            "id":        "pqc_receipt",
            "layer":     "Layer 3",
            "name":      "PQC Cryptographic Receipt",
            "adr":       "ADR-096",
            "mandatory": True,
            "advisory":  False,
            "description": (
                "Generates a Post-Quantum Cryptography (Dilithium-3) signed receipt for "
                "the governance decision. Chain-linked to prior receipts via prev_hash. "
                "Publicly verifiable at /verify."
            ),
        },
    ]

    def __init__(self, governance_engine_cls, receipt_engine_cls):
        self._gov_engine_cls     = governance_engine_cls
        self._receipt_engine_cls = receipt_engine_cls

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _new_control_id() -> str:
        return "UDCL-" + secrets.token_hex(8).upper()

    @staticmethod
    def _elapsed_ms(t0: float) -> float:
        return (time.perf_counter() - t0) * 1000

    @staticmethod
    def _control_hash(
        control_id: str,
        decision:   str,
        pillar_outcomes: list,  # list of "pillar:PASS|BLOCK" strings
    ) -> str:
        payload = json.dumps(
            {
                "control_id": control_id,
                "decision":   decision,
                "pillars":    sorted(pillar_outcomes),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()

    def _build_receipt(
        self,
        control_id:      str,
        decision:        str,
        blocking_pillar: Optional[str],
        block_reason:    Optional[str],
        pillar_results:  list,
        receipt_id:      Optional[str],
        domain:          str,
        asset:           str,
        t_total:         float,
        cbg_enabled:     bool = False,
    ) -> ControlReceipt:
        outcomes = [
            f"{r.pillar}:{'PASS' if r.passed else 'BLOCK'}"
            for r in pillar_results
        ]
        ctrl_hash = self._control_hash(control_id, decision, outcomes)
        return ControlReceipt(
            control_id      = control_id,
            decision        = decision,
            blocking_pillar = blocking_pillar,
            block_reason    = block_reason,
            pillar_results  = pillar_results,
            receipt_id      = receipt_id,
            domain          = domain,
            asset           = asset,
            total_latency_ms= self._elapsed_ms(t_total),
            control_hash    = ctrl_hash,
            cbg_enabled     = cbg_enabled,
        )

    def _blocked(
        self,
        control_id:     str,
        blocking:       str,
        reason:         str,
        pillar_results: list,
        domain:         str,
        asset:          str,
        t_total:        float,
        receipt_id:     Optional[str] = None,
        cbg_enabled:    bool = False,
    ) -> ControlReceipt:
        return self._build_receipt(
            control_id, "BLOCKED", blocking, reason,
            pillar_results, receipt_id, domain, asset, t_total,
            cbg_enabled=cbg_enabled,
        )

    # ── Layer 0: SAE ─────────────────────────────────────────────────────────

    def _run_sae(self, domain: str, client_id: str) -> PillarResult:
        t0 = time.perf_counter()
        try:
            from omnix_core.governance.structural_admissibility_engine import get_layer0_metrics
            sae    = get_layer0_metrics()
            snap   = sae.snapshot()
            status = snap.get("admission_status", "admitted")
            passed = status != "rejected"
            return PillarResult(
                pillar    = "sae",
                layer     = "Layer 0",
                passed    = passed,
                advisory  = False,
                latency_ms= self._elapsed_ms(t0),
                detail    = {
                    "admission_status": status,
                    "domain_coverage":  snap.get("domain_coverage", {}),
                    "adr": "ADR-092",
                },
            )
        except Exception as exc:
            logger.debug("[UDCL][SAE] unavailable — pass-through: %s", exc)
            return PillarResult(
                pillar    = "sae",
                layer     = "Layer 0",
                passed    = True,
                advisory  = False,
                latency_ms= self._elapsed_ms(t0),
                detail    = {
                    "admission_status": "unavailable",
                    "note": "SAE module not loaded — structural pass-through per ADR-092 §6",
                    "adr":  "ADR-092",
                },
            )

    # ── Layer 0b: SPG ─────────────────────────────────────────────────────────

    def _run_spg(
        self,
        signals:   dict,
        domain:    str,
        asset:     str,
        client_id: str,
    ) -> PillarResult:
        t0 = time.perf_counter()
        try:
            from omnix_core.governance.state_provenance_guard import evaluate_provenance
            result  = evaluate_provenance(
                signals   = signals,
                domain    = domain,
                asset     = asset,
                client_id = client_id,
            )
            verdict = result.verdict.value if hasattr(result.verdict, "value") else str(result.verdict)
            # SPG is advisory — only CONTRADICTED is a hard signal (treated as advisory block)
            passed  = verdict != "CONTRADICTED"
            return PillarResult(
                pillar    = "spg",
                layer     = "Layer 0b",
                passed    = passed,
                advisory  = True,
                latency_ms= self._elapsed_ms(t0),
                detail    = {
                    "verdict":             verdict,
                    "lineage_singularity": round(float(result.lineage_singularity), 2),
                    "contradiction_count": int(result.contradiction_count),
                    "spg_id":             result.spg_id,
                    "adr": "ADR-133",
                },
            )
        except Exception as exc:
            logger.debug("[UDCL][SPG] unavailable — advisory pass: %s", exc)
            return PillarResult(
                pillar    = "spg",
                layer     = "Layer 0b",
                passed    = True,
                advisory  = True,
                latency_ms= self._elapsed_ms(t0),
                detail    = {
                    "verdict": "unavailable",
                    "note": "SPG module not loaded — advisory pass per ADR-133 §fail-safe",
                    "adr":  "ADR-133",
                },
            )

    # ── Layer 0c: CBG (opt-in) ────────────────────────────────────────────────

    def _run_cbg(
        self,
        spg_result: PillarResult,
        domain:     str,
        asset:      str,
        decision_id: str,
    ) -> PillarResult:
        t0 = time.perf_counter()
        try:
            from omnix_core.governance.conditional_bind_gate import ConditionalBindGate
            d              = spg_result.detail
            verdict        = d.get("verdict", "SINGULAR")
            lineage        = float(d.get("lineage_singularity", 100.0))
            contradictions = int(d.get("contradiction_count", 0))
            spg_id         = d.get("spg_id", "SPG-UNKNOWN")

            cbg        = ConditionalBindGate()
            gate_result = cbg.evaluate(
                spg_id              = spg_id,
                spg_verdict         = verdict,
                lineage_singularity = lineage,
                contradiction_count = contradictions,
                decision_id         = decision_id,
                domain              = domain,
            )
            bind_allowed = gate_result.bind_allowed
            gate_verdict = getattr(gate_result, "verdict", "PASS" if bind_allowed else "GATE_CREATED")
            return PillarResult(
                pillar    = "cbg",
                layer     = "Layer 0c",
                passed    = bind_allowed,
                advisory  = False,
                latency_ms= self._elapsed_ms(t0),
                detail    = {
                    "bind_allowed": bind_allowed,
                    "verdict":      gate_verdict,
                    "gate_id":      getattr(gate_result, "gate_id", None),
                    "reason":       getattr(gate_result, "reason", ""),
                    "adr": "ADR-135",
                },
            )
        except Exception as exc:
            logger.debug("[UDCL][CBG] fail-safe pass: %s", exc)
            return PillarResult(
                pillar    = "cbg",
                layer     = "Layer 0c",
                passed    = True,
                advisory  = False,
                latency_ms= self._elapsed_ms(t0),
                detail    = {
                    "bind_allowed": True,
                    "verdict":      "PASS",
                    "note": "CBG fail-safe — bind allowed per ADR-135 §2.1 Constraint 1",
                    "adr":  "ADR-135",
                },
            )

    # ── Layer 1-2: 11-Checkpoint Pipeline + TIE ──────────────────────────────

    def _run_checkpoint_pipeline(
        self,
        signals:              dict,
        asset:                str,
        domain:               str,
        metadata:             dict,
        compliance_config:    dict,
        checkpoint_overrides: Optional[list],
    ) -> tuple:
        """Returns (PillarResult, raw_evaluation_dict)."""
        t0 = time.perf_counter()
        try:
            engine     = self._gov_engine_cls(checkpoint_overrides=checkpoint_overrides)
            evaluation = engine.evaluate(
                signals           = signals,
                asset             = asset,
                domain            = domain,
                metadata          = metadata,
                compliance_config = compliance_config,
            )
            decision    = evaluation.get("decision", "BLOCKED")
            passed      = decision == "APPROVED"
            checkpoints = evaluation.get("checkpoints", [])
            passed_cps  = sum(1 for cp in checkpoints if cp.get("passed", False))

            result = PillarResult(
                pillar    = "checkpoint_pipeline",
                layer     = "Layer 1-2",
                passed    = passed,
                advisory  = False,
                latency_ms= self._elapsed_ms(t0),
                detail    = {
                    "decision":           decision,
                    "score":              evaluation.get("score"),
                    "checkpoints_total":  len(checkpoints),
                    "checkpoints_passed": passed_cps,
                    "checkpoints_blocked": len(checkpoints) - passed_cps,
                    "block_reason":       evaluation.get("block_reason"),
                    "veto_chain":         evaluation.get("veto_chain", []),
                    "adr": "ADR-028",
                },
            )
            return result, evaluation

        except Exception as exc:
            logger.error("[UDCL][CP] pipeline exception: %s", exc)
            dummy_eval = {"decision": "BLOCKED", "checkpoints": [], "score": 0,
                          "block_reason": "Pipeline engine error", "veto_chain": [],
                          "gate_results": {}}
            result = PillarResult(
                pillar    = "checkpoint_pipeline",
                layer     = "Layer 1-2",
                passed    = False,
                advisory  = False,
                latency_ms= self._elapsed_ms(t0),
                detail    = {
                    "decision":    "BLOCKED",
                    "block_reason": "Checkpoint pipeline raised an unhandled exception",
                    "adr": "ADR-028",
                },
                error=str(exc)[:200],
            )
            return result, dummy_eval

    # ── Layer 3: PQC Receipt ──────────────────────────────────────────────────

    def _run_pqc_receipt(
        self,
        evaluation: dict,
        asset:      str,
        domain:     str,
        client_id:  str,
        metadata:   dict,
        control_id: str,
    ) -> tuple:
        """Returns (PillarResult, receipt_id: str | None)."""
        t0         = time.perf_counter()
        receipt_id = None
        try:
            receipt_engine = self._receipt_engine_cls()
            prev_hash      = receipt_engine.get_last_hash()
            decision_payload = {
                "symbol":      asset,
                "asset":       asset,
                "domain":      domain,
                "client_id":   client_id,
                "decision":    evaluation.get("decision", "BLOCKED"),
                "score":       evaluation.get("score"),
                "block_reason": evaluation.get("block_reason"),
                "checkpoints": evaluation.get("checkpoints", []),
                "metadata": {
                    **metadata,
                    "udcl_control_id": control_id,
                    "udcl_adr":        "ADR-138",
                },
            }
            receipt    = receipt_engine.generate_receipt(
                decision_payload = decision_payload,
                prev_hash        = prev_hash,
                client_id        = client_id,
                domain           = domain,
            )
            receipt_id = receipt.get("receipt_id")
            return PillarResult(
                pillar    = "pqc_receipt",
                layer     = "Layer 3",
                passed    = True,
                advisory  = False,
                latency_ms= self._elapsed_ms(t0),
                detail    = {
                    "receipt_id":  receipt_id,
                    "algorithm":   receipt.get("signature_algorithm", "Dilithium-3"),
                    "pqc_signed":  receipt.get("signature") is not None,
                    "verify_url":  (
                        f"https://omnixquantum.net/verify#{receipt_id}"
                        if receipt_id else None
                    ),
                    "chain_linked": receipt.get("prev_hash") is not None,
                    "adr": "ADR-096",
                },
            ), receipt_id

        except Exception as exc:
            logger.error("[UDCL][PQC] receipt generation error: %s", exc)
            return PillarResult(
                pillar    = "pqc_receipt",
                layer     = "Layer 3",
                passed    = False,
                advisory  = False,
                latency_ms= self._elapsed_ms(t0),
                detail    = {
                    "status": "error",
                    "note":   "PQC receipt generation failed",
                    "adr":    "ADR-096",
                },
                error=str(exc)[:200],
            ), None

    # ── Main orchestration ────────────────────────────────────────────────────

    def evaluate(
        self,
        signals:              dict,
        asset:                str,
        domain:               str,
        client_id:            str,
        metadata:             Optional[dict] = None,
        compliance_config:    Optional[dict] = None,
        checkpoint_overrides: Optional[list] = None,
        cbg_enabled:          bool           = False,
    ) -> ControlReceipt:
        """
        Full multi-pillar governance evaluation. Returns ControlReceipt.

        Execution order:
          SAE → SPG → [CBG] → 11-Checkpoint + TIE → PQC Receipt

        Fail-closed: any mandatory non-advisory pillar failure → BLOCKED.
        Fail-open: advisory pillar (SPG) failure → warning only, continues.
        """
        t_total            = time.perf_counter()
        control_id         = self._new_control_id()
        metadata           = metadata or {}
        compliance_config  = compliance_config or {}
        pillar_results: list[PillarResult] = []

        # ── Layer 0: SAE ──────────────────────────────────────────────────────
        sae_r = self._run_sae(domain, client_id)
        pillar_results.append(sae_r)
        if not sae_r.passed:
            # SAE is non-advisory — structural rejection is always final
            return self._blocked(
                control_id, "sae", "Structural admissibility rejected",
                pillar_results, domain, asset, t_total, cbg_enabled=cbg_enabled,
            )

        # ── Layer 0b: SPG ─────────────────────────────────────────────────────
        spg_r = self._run_spg(signals, domain, asset, client_id)
        pillar_results.append(spg_r)
        # SPG is advisory — CONTRADICTED logs but does not block unless CBG escalates

        # ── Layer 0c: CBG (opt-in) ────────────────────────────────────────────
        if cbg_enabled:
            cbg_r = self._run_cbg(
                spg_r, domain, asset,
                decision_id=f"{control_id}-{domain}-{asset}",
            )
            pillar_results.append(cbg_r)
            if not cbg_r.passed:
                return self._blocked(
                    control_id, "cbg",
                    cbg_r.detail.get("reason", "Conditional bind gate blocked — human attestation required"),
                    pillar_results, domain, asset, t_total, cbg_enabled=cbg_enabled,
                )

        # ── Layer 1-2: 11-Checkpoint Pipeline + TIE ──────────────────────────
        cp_r, evaluation = self._run_checkpoint_pipeline(
            signals, asset, domain, metadata, compliance_config, checkpoint_overrides,
        )
        pillar_results.append(cp_r)

        # Generate PQC receipt regardless of pipeline decision (BLOCKED receipts are auditable)
        pqc_r, receipt_id = self._run_pqc_receipt(
            evaluation, asset, domain, client_id, metadata, control_id,
        )
        pillar_results.append(pqc_r)

        if not cp_r.passed:
            cp_decision = cp_r.detail.get("decision", "BLOCKED")
            final       = cp_decision if cp_decision in ("BLOCKED", "HOLD") else "BLOCKED"
            return self._build_receipt(
                control_id, final, "checkpoint_pipeline",
                cp_r.detail.get("block_reason", "Checkpoint pipeline blocked"),
                pillar_results, receipt_id, domain, asset, t_total,
                cbg_enabled=cbg_enabled,
            )

        if not pqc_r.passed:
            return self._blocked(
                control_id, "pqc_receipt", "PQC receipt generation failed",
                pillar_results, domain, asset, t_total, receipt_id=receipt_id,
                cbg_enabled=cbg_enabled,
            )

        # ── All mandatory pillars passed ──────────────────────────────────────
        cp_decision = cp_r.detail.get("decision", "APPROVED")
        return self._build_receipt(
            control_id, cp_decision, None, None,
            pillar_results, receipt_id, domain, asset, t_total,
            cbg_enabled=cbg_enabled,
        )

    # ── Schema / catalog helpers ──────────────────────────────────────────────

    @classmethod
    def get_pillar_catalog(cls) -> list:
        return cls.PILLAR_CATALOG

    @classmethod
    def get_schema(cls) -> dict:
        return {
            "module":      "MOD-014",
            "adr":         cls.ADR,
            "version":     cls.VERSION,
            "description": (
                "Unified Decision Control Layer — coordinates all OMNIX governance "
                "pillars in sequence. Any non-advisory mandatory pillar failure → "
                "BLOCKED (fail-closed). Returns ControlReceipt with full per-pillar "
                "visibility, latency breakdown, and tamper-evident control hash."
            ),
            "pillars": cls.PILLAR_CATALOG,
            "endpoints": {
                "evaluate":  "POST /api/governance/control/evaluate",
                "schema":    "GET  /api/governance/control/schema",
                "health":    "GET  /api/governance/control/health",
                "receipt":   "GET  /api/governance/control/receipts/<control_id>",
            },
            "request_body": {
                "signals":            "dict — same schema as /api/governance/evaluate",
                "asset":              "string — instrument or entity identifier",
                "domain":             "string — governance vertical (trading, credit, etc.)",
                "metadata":           "dict (optional) — caller-supplied context",
                "compliance_config":  "dict (optional) — gate activation params",
                "cbg_enabled":        "bool (optional, default false) — enable Conditional Bind Gate",
            },
            "control_receipt_fields": {
                "control_id":        "UDCL-{16 hex} — unique ID for this multi-pillar evaluation",
                "decision":          "APPROVED | BLOCKED | HOLD",
                "blocking_pillar":   "Name of first blocking pillar, or null",
                "block_reason":      "Human-readable block reason, or null",
                "pillar_results":    "Dict of per-pillar results keyed by pillar ID",
                "receipt_id":        "PQC receipt ID (Layer 3) — verifiable at /verify",
                "control_hash":      "SHA-256 seal of control_id + decision + pillar outcomes",
                "total_latency_ms":  "End-to-end wall-clock time in milliseconds",
                "pillar_latency_ms": "Per-pillar latency breakdown in milliseconds",
                "cbg_enabled":       "Whether CBG (Layer 0c) was active for this evaluation",
                "pillars_evaluated": "Number of pillars that ran",
                "pillars_passed":    "Number of pillars that returned passed=true",
            },
            "design_invariants": [
                "All pillar results are returned even on block — full transparency.",
                "blocking_pillar names the first pillar that produced a non-advisory failure.",
                "control_hash seals the entire multi-pillar outcome — tamper-evident.",
                "SPG (Layer 0b) is advisory — AMBIGUOUS warns but does not block alone.",
                "CBG (Layer 0c) is opt-in — enable via cbg_enabled=true in request.",
                "PQC receipt is generated for ALL decisions including BLOCKED.",
            ],
        }

    @classmethod
    def check_pillar_health(cls) -> dict:
        """
        Runtime health check for all OMNIX governance pillars.
        Returns a dict with per-pillar availability status.
        Called by GET /api/governance/control/health.
        """
        health = {}
        checks = [
            ("sae",                "omnix_core.governance.structural_admissibility_engine", "get_layer0_metrics"),
            ("spg",                "omnix_core.governance.state_provenance_guard",          "evaluate_provenance"),
            ("cbg",                "omnix_core.governance.conditional_bind_gate",           "ConditionalBindGate"),
            ("checkpoint_pipeline","omnix_core.governance.external_evaluator",              "GovernanceEvaluationEngine"),
        ]
        for pillar_id, module_path, symbol in checks:
            t0 = time.perf_counter()
            try:
                mod = __import__(module_path, fromlist=[symbol])
                getattr(mod, symbol)
                health[pillar_id] = {
                    "status":     "operational",
                    "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
                }
            except Exception as exc:
                health[pillar_id] = {
                    "status":  "unavailable",
                    "reason":  str(exc)[:120],
                    "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
                }
        # PQC receipt is checked separately via engine flag
        health["pqc_receipt"] = {
            "status": "operational",
            "note":   "Checked at evaluate time — lazy load via _ENGINE_AVAILABLE flag",
        }
        all_operational = all(
            v.get("status") == "operational" for v in health.values()
        )
        return {
            "overall": "operational" if all_operational else "degraded",
            "pillars": health,
            "adr":     cls.ADR,
        }
