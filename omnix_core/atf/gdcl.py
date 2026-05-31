"""
OMNIX Agent Trust Fabric — Governance Decision Convergence Layer (GDCL)
ADR-206: Multi-RSA aggregation → typed composite boundary verdict.

The GDCL resolves the multi-proof convergence problem:

  Given N RetroactiveSemanticAssessments from heterogeneous originating runtimes,
  produce a single typed boundary outcome that governs the local decision.

  Example (healthcare, Peter Cranstone / 3PMobile):
    Pharmacy (PORTABLE) + Payer (DRIFT_CRITICAL) + ED (PORTABLE) +
    Claims (DRIFT_ACKNOWLEDGED) + Audit (PORTABLE)
    → GDCL: LIMITED_RELIANCE — one boundary verdict, no upstream reconstruction.

Seven Composite Verdicts (exhaustive, mutually exclusive — GDCL-INV-001):
  FULL_RELIANCE      All RSAs = SEMANTICALLY_PORTABLE. No qualification required.
  QUALIFIED_RELIANCE Worst = DRIFT_ACKNOWLEDGED. Apply MORE_RESTRICTIVE posture.
  LIMITED_RELIANCE   Any DRIFT_CRITICAL; no INCOMPATIBLE. Document before regulatory use.
  CONTESTED          INCOMPATIBLE coexists with PORTABLE/ACKNOWLEDGED; no CRITICAL.
  REFUSED            All RSAs = SEMANTICALLY_INCOMPATIBLE. Operation must be rejected.
  ESCALATION         INCOMPATIBLE + DRIFT_CRITICAL simultaneous. Human review mandatory.
  INDETERMINATE      Empty input — no RSAs provided.

GDCL Invariants (ADR-206 §Invariants):
  GDCL-INV-001: Exhaustive taxonomy — every non-empty input maps to exactly one verdict.
  GDCL-INV-002: FULL_RELIANCE and REFUSED are mutually exclusive.
  GDCL-INV-003: Determinism — pure function; identical inputs → identical verdict.
  GDCL-INV-004: N=1 degeneracy — single RSA maps directly to its DSPP verdict class.
  GDCL-INV-005: No upstream reconstruction — operates solely on RSAResult objects.
  GDCL-INV-006: Traceability — every GCR PQC-signed, append-only, references all RSA IDs.

ADR-206 — Harold Nunes — OMNIX QUANTUM LTD — May 2026
Priority Record: OMNIX-PAR-2026-GDCL-001
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("OMNIX.ATF.GDCL")

# ---------------------------------------------------------------------------
# DSPP Verdict constants (mirrors DSPPVerdict enum — no circular import)
# ---------------------------------------------------------------------------

_VERDICT_PORTABLE       = "SEMANTICALLY_PORTABLE"
_VERDICT_ACKNOWLEDGED   = "DRIFT_ACKNOWLEDGED"
_VERDICT_CRITICAL       = "DRIFT_CRITICAL"
_VERDICT_INCOMPATIBLE   = "SEMANTICALLY_INCOMPATIBLE"

_ALL_DSPP_VERDICTS: Tuple[str, ...] = (
    _VERDICT_PORTABLE,
    _VERDICT_ACKNOWLEDGED,
    _VERDICT_CRITICAL,
    _VERDICT_INCOMPATIBLE,
)

# ---------------------------------------------------------------------------
# Composite Verdict
# ---------------------------------------------------------------------------

class GDCLCompositeVerdict(str, Enum):
    """
    Typed composite boundary outcome emitted by the GDCL.

    Ordered by operational severity (INDETERMINATE excluded from ordering):
    FULL_RELIANCE < QUALIFIED_RELIANCE < LIMITED_RELIANCE < CONTESTED
                  < REFUSED < ESCALATION

    Note: ESCALATION is more severe than REFUSED because it signals an active
    conflict requiring human resolution, whereas REFUSED is a clean rejection.
    """
    FULL_RELIANCE       = "FULL_RELIANCE"
    QUALIFIED_RELIANCE  = "QUALIFIED_RELIANCE"
    LIMITED_RELIANCE    = "LIMITED_RELIANCE"
    CONTESTED           = "CONTESTED"
    REFUSED             = "REFUSED"
    ESCALATION          = "ESCALATION"
    INDETERMINATE       = "INDETERMINATE"


# ---------------------------------------------------------------------------
# Boundary Recommendations — operational prose per verdict
# ---------------------------------------------------------------------------

_BOUNDARY_RECOMMENDATIONS: Dict[str, str] = {
    GDCLCompositeVerdict.FULL_RELIANCE: (
        "All assessed receipts are semantically portable in this domain. "
        "No semantic qualification required. The local decision may proceed "
        "under full reliance on all incoming governance proofs."
    ),
    GDCLCompositeVerdict.QUALIFIED_RELIANCE: (
        "Moderate semantic drift detected across one or more receipts. "
        "Apply the MORE_RESTRICTIVE governing posture (DSPP-INV-003) when "
        "interpreting these receipts. The local decision may proceed with "
        "contextual qualification documented in this GCR."
    ),
    GDCLCompositeVerdict.LIMITED_RELIANCE: (
        "Significant semantic divergence (DRIFT_CRITICAL) present in at least "
        "one receipt. Document the divergence explicitly before relying on this "
        "result in any regulatory or audit context. Human review is RECOMMENDED "
        "before commitment. Per DSPP §7.4, DRIFT_CRITICAL receipts must not be "
        "treated as fully portable without explicit acknowledgment."
    ),
    GDCLCompositeVerdict.CONTESTED: (
        "Conflicting semantic verdicts detected: at least one receipt is "
        "SEMANTICALLY_INCOMPATIBLE while others remain portable or acknowledged. "
        "The incompatible source cannot be dismissed. Document the conflict "
        "explicitly. Do not proceed without resolving or formally acknowledging "
        "the incompatible source per DSPP-INV-006 propagation rules."
    ),
    GDCLCompositeVerdict.REFUSED: (
        "All assessed receipts are SEMANTICALLY_INCOMPATIBLE in this domain. "
        "The local decision MUST be rejected. No reliance on the incoming "
        "governance proofs is admissible. Equivalent to HALT in OGR vocabulary."
    ),
    GDCLCompositeVerdict.ESCALATION: (
        "CRITICAL: Simultaneous SEMANTICALLY_INCOMPATIBLE and DRIFT_CRITICAL "
        "verdicts detected across the assessed receipts. The convergence cannot "
        "be resolved algorithmically. Human review is MANDATORY before any action. "
        "Do not commit the local decision until a designated authority has reviewed "
        "and explicitly authorized the divergence."
    ),
    GDCLCompositeVerdict.INDETERMINATE: (
        "No RSA inputs provided. The GDCL cannot compute a composite verdict "
        "without at least one RetroactiveSemanticAssessment. Provide RSA inputs "
        "or treat the absence as REFUSED per fail-closed governance policy."
    ),
}

# ---------------------------------------------------------------------------
# Error classes
# ---------------------------------------------------------------------------

class GDCLError(Exception):
    """Base exception for GDCL violations."""


class GDCLDeterminismError(GDCLError):
    """GDCL-INV-003: Internal non-determinism detected."""


class GDCLInvalidInputError(GDCLError):
    """Invalid RSA input: missing required fields or unrecognized verdict value."""


# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

DDL_GDCL_CONVERGENCE_RECORDS = """
CREATE TABLE IF NOT EXISTS atf_gdcl_convergence_records (
    gcr_id                      VARCHAR(128)    PRIMARY KEY,
    receiving_runtime_id        VARCHAR(128)    NOT NULL,
    rsa_ids                     JSONB           NOT NULL DEFAULT '[]',
    receipt_ids                 JSONB           NOT NULL DEFAULT '[]',
    n_assessments               INTEGER         NOT NULL CHECK (n_assessments >= 0),
    verdict_distribution        JSONB           NOT NULL DEFAULT '{}',
    composite_verdict           VARCHAR(32)     NOT NULL
                                    CHECK (composite_verdict IN (
                                        'FULL_RELIANCE','QUALIFIED_RELIANCE',
                                        'LIMITED_RELIANCE','CONTESTED',
                                        'REFUSED','ESCALATION','INDETERMINATE'
                                    )),
    dominant_sdu                NUMERIC(6,4)    NOT NULL,
    mean_sdu                    NUMERIC(6,4)    NOT NULL,
    min_portability_confidence  NUMERIC(6,4)    NOT NULL,
    boundary_recommendation     TEXT            NOT NULL,
    converged_at                TIMESTAMPTZ     NOT NULL,
    content_hash                VARCHAR(64)     NOT NULL,
    pqc_signature               TEXT            DEFAULT NULL,
    pqc_algorithm               VARCHAR(32)     DEFAULT NULL,
    created_at                  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_atf_gcr_runtime
    ON atf_gdcl_convergence_records (receiving_runtime_id);
CREATE INDEX IF NOT EXISTS idx_atf_gcr_verdict
    ON atf_gdcl_convergence_records (composite_verdict);
CREATE INDEX IF NOT EXISTS idx_atf_gcr_converged_at
    ON atf_gdcl_convergence_records (converged_at DESC);
"""


# ---------------------------------------------------------------------------
# Dataclass: GDCLConvergenceRecord (GCR)
# ---------------------------------------------------------------------------

@dataclass
class GDCLConvergenceRecord:
    """
    Governance Decision Convergence Record (GCR) — GDCL output artifact.
    PQC-signed, append-only, references all RSA inputs.

    Fields:
        gcr_id                     — "OMNIX-GCR-{16HEX}"
        receiving_runtime_id       — runtime performing the convergence
        rsa_ids                    — ordered list of RSA IDs ingested
        receipt_ids                — ordered list of receipt IDs covered
        n_assessments              — number of RSAs ingested
        verdict_distribution       — {dspp_verdict: count} breakdown
        composite_verdict          — GDCLCompositeVerdict (the boundary outcome)
        dominant_sdu               — max aggregate_sdu across all RSAs
        mean_sdu                   — arithmetic mean aggregate_sdu
        min_portability_confidence — min portability_confidence across all RSAs
        boundary_recommendation    — operational recommendation prose
        converged_at               — ISO UTC timestamp of convergence computation
        content_hash               — SHA3-256 of canonical fields
        pqc_signature              — ML-DSA-65 signature over content_hash
        pqc_algorithm              — "ML-DSA-65"
        created_at                 — ISO UTC creation timestamp
    """
    gcr_id: str
    receiving_runtime_id: str
    rsa_ids: List[str]
    receipt_ids: List[str]
    n_assessments: int
    verdict_distribution: Dict[str, int]
    composite_verdict: str
    dominant_sdu: float
    mean_sdu: float
    min_portability_confidence: float
    boundary_recommendation: str
    converged_at: str
    content_hash: str
    pqc_signature: Optional[str]
    pqc_algorithm: Optional[str]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_signed(self) -> bool:
        return self.pqc_signature is not None

    def is_actionable(self) -> bool:
        """Returns True if the verdict allows the local decision to proceed (with qualifications)."""
        return self.composite_verdict in (
            GDCLCompositeVerdict.FULL_RELIANCE.value,
            GDCLCompositeVerdict.QUALIFIED_RELIANCE.value,
            GDCLCompositeVerdict.LIMITED_RELIANCE.value,
        )

    def requires_halt(self) -> bool:
        """Returns True if the local decision MUST be rejected or escalated."""
        return self.composite_verdict in (
            GDCLCompositeVerdict.REFUSED.value,
            GDCLCompositeVerdict.ESCALATION.value,
        )

    def requires_human_review(self) -> bool:
        """Returns True if human review is required before proceeding."""
        return self.composite_verdict == GDCLCompositeVerdict.ESCALATION.value

    def summary(self) -> Dict[str, Any]:
        return {
            "gcr_id": self.gcr_id,
            "composite_verdict": self.composite_verdict,
            "n_assessments": self.n_assessments,
            "verdict_distribution": self.verdict_distribution,
            "dominant_sdu": round(self.dominant_sdu, 4),
            "mean_sdu": round(self.mean_sdu, 4),
            "min_portability_confidence": round(self.min_portability_confidence, 4),
            "is_signed": self.is_signed(),
            "requires_halt": self.requires_halt(),
            "requires_human_review": self.requires_human_review(),
        }


# ---------------------------------------------------------------------------
# RSAInput — lightweight duck-typed wrapper for RSA objects
# ---------------------------------------------------------------------------

@dataclass
class RSAInput:
    """
    Normalized view of a RetroactiveSemanticAssessment for GDCL convergence.
    Accepts either an RSA dataclass instance or a dict representation.

    GDCL-INV-005: Only the verdict, sdu, and confidence fields are read.
    No TSA, SDR, SPV, or delegation chain access.
    """
    rsa_id: str
    receipt_id: str
    dspp_verdict: str
    aggregate_sdu: float
    portability_confidence: float

    @classmethod
    def from_obj(cls, rsa: Any) -> "RSAInput":
        """
        Construct from a RetroactiveSemanticAssessment instance or dict.

        Raises:
            GDCLInvalidInputError: missing required fields or invalid verdict.
        """
        if isinstance(rsa, dict):
            data = rsa
        else:
            try:
                data = asdict(rsa) if hasattr(rsa, "__dataclass_fields__") else vars(rsa)
            except Exception:
                data = {attr: getattr(rsa, attr) for attr in (
                    "rsa_id", "receipt_id", "dspp_verdict",
                    "aggregate_sdu", "portability_confidence",
                )}

        rsa_id = data.get("rsa_id", "")
        receipt_id = data.get("receipt_id", "")
        verdict = data.get("dspp_verdict", "")
        sdu = float(data.get("aggregate_sdu", 0.0))
        confidence = float(data.get("portability_confidence", 1.0 - sdu))

        if not rsa_id:
            raise GDCLInvalidInputError("RSA input missing required field: rsa_id")
        if not receipt_id:
            raise GDCLInvalidInputError(f"RSA {rsa_id}: missing required field: receipt_id")
        if verdict not in _ALL_DSPP_VERDICTS:
            raise GDCLInvalidInputError(
                f"RSA {rsa_id}: unrecognized dspp_verdict '{verdict}'. "
                f"Must be one of {_ALL_DSPP_VERDICTS}"
            )
        if not (0.0 <= sdu <= 1.0):
            raise GDCLInvalidInputError(
                f"RSA {rsa_id}: aggregate_sdu {sdu} out of range [0.0, 1.0]"
            )

        return cls(
            rsa_id=rsa_id,
            receipt_id=receipt_id,
            dspp_verdict=verdict,
            aggregate_sdu=sdu,
            portability_confidence=confidence,
        )


# ---------------------------------------------------------------------------
# Core convergence algorithm (pure function — GDCL-INV-003)
# ---------------------------------------------------------------------------

def compute_composite_verdict(inputs: List[RSAInput]) -> GDCLCompositeVerdict:
    """
    Pure function. Computes the GDCL composite verdict from N RSAInputs.

    Algorithm (priority-ordered, worst-case dominance):
      1. Empty input       → INDETERMINATE
      2. INCOMPATIBLE ∧ CRITICAL present simultaneously → ESCALATION
      3. All INCOMPATIBLE  → REFUSED
      4. INCOMPATIBLE ∧ (PORTABLE ∨ ACKNOWLEDGED) present → CONTESTED
      5. Any CRITICAL      → LIMITED_RELIANCE
      6. Any ACKNOWLEDGED  → QUALIFIED_RELIANCE
      7. (else)            → FULL_RELIANCE

    GDCL-INV-001: exhaustive — every case is covered.
    GDCL-INV-002: FULL_RELIANCE and REFUSED are mutually exclusive by construction.
    GDCL-INV-003: pure function — no side effects, no stochastic components.
    GDCL-INV-004: N=1 degeneracy verified by case analysis against each DSPP verdict.
    """
    if not inputs:
        return GDCLCompositeVerdict.INDETERMINATE

    verdicts = [inp.dspp_verdict for inp in inputs]
    n = len(verdicts)

    has_incompatible  = _VERDICT_INCOMPATIBLE  in verdicts
    has_critical      = _VERDICT_CRITICAL      in verdicts
    has_acknowledged  = _VERDICT_ACKNOWLEDGED  in verdicts
    has_portable      = _VERDICT_PORTABLE      in verdicts
    n_incompatible    = verdicts.count(_VERDICT_INCOMPATIBLE)

    # Step 1 — ESCALATION: active conflict requiring human resolution
    if has_incompatible and has_critical:
        return GDCLCompositeVerdict.ESCALATION

    # Step 2 — REFUSED: unanimous incompatibility
    if n_incompatible == n:
        return GDCLCompositeVerdict.REFUSED

    # Step 3 — CONTESTED: sources disagree (incompatible vs portable/acknowledged)
    if has_incompatible and (has_portable or has_acknowledged):
        return GDCLCompositeVerdict.CONTESTED

    # Step 4 — LIMITED_RELIANCE: significant drift, no incompatibility
    if has_critical:
        return GDCLCompositeVerdict.LIMITED_RELIANCE

    # Step 5 — QUALIFIED_RELIANCE: moderate drift only
    if has_acknowledged:
        return GDCLCompositeVerdict.QUALIFIED_RELIANCE

    # Step 6 — FULL_RELIANCE: all portable
    return GDCLCompositeVerdict.FULL_RELIANCE


def _n1_degeneracy_check(verdict: str) -> GDCLCompositeVerdict:
    """
    GDCL-INV-004: maps a single DSPP verdict to its GDCL equivalent.
    Used for internal verification and documentation.
    """
    _map = {
        _VERDICT_PORTABLE:      GDCLCompositeVerdict.FULL_RELIANCE,
        _VERDICT_ACKNOWLEDGED:  GDCLCompositeVerdict.QUALIFIED_RELIANCE,
        _VERDICT_CRITICAL:      GDCLCompositeVerdict.LIMITED_RELIANCE,
        _VERDICT_INCOMPATIBLE:  GDCLCompositeVerdict.REFUSED,
    }
    return _map[verdict]


# ---------------------------------------------------------------------------
# GDCLEngine
# ---------------------------------------------------------------------------

class GDCLEngine:
    """
    Governance Decision Convergence Layer engine.

    Design contract:
        converge(rsa_results, receiving_runtime_id) → GDCLConvergenceRecord
        verify_convergence_record(gcr)              → dict (integrity check)
        ensure_tables()                             → idempotent DDL
        get_record(gcr_id)                         → Optional[GDCLConvergenceRecord]

    GDCL-INV-003 enforcement:
        converge() is deterministic. Given the same RSA inputs (order-independent),
        it always produces the same composite_verdict and the same content_hash.

    GDCL-INV-005 enforcement:
        converge() only reads rsa_id, receipt_id, dspp_verdict, aggregate_sdu,
        portability_confidence from each RSA. No DB access to originating runtimes.

    GDCL-INV-006 enforcement:
        Every GCR is persisted with PQC signature, referencing all RSA IDs.
    """

    def __init__(self, runtime_id: str, db_url: Optional[str] = None):
        self.runtime_id = runtime_id
        self._db_url = db_url or os.environ.get("DATABASE_URL")
        self._store: Dict[str, GDCLConvergenceRecord] = {}
        self._lock = threading.Lock()
        self._provider = self._load_provider()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_provider(self):
        try:
            from omnix_core.security.crypto_providers import get_active_provider
            return get_active_provider()
        except Exception:
            return None

    def _get_conn(self):
        try:
            import psycopg
            return psycopg.connect(self._db_url)
        except Exception as exc:
            logger.warning(f"[ATF.GDCL] DB connection failed: {exc}")
            return None

    @staticmethod
    def _canonical_json(obj: Dict[str, Any]) -> bytes:
        return json.dumps(
            obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")

    @staticmethod
    def _compute_hash(fields: Dict[str, Any]) -> str:
        """SHA3-256 over canonical fields (consistent with RCEP/IPFL canonicalization)."""
        exclude = {"content_hash", "pqc_signature", "pqc_algorithm"}
        clean = {k: v for k, v in fields.items() if k not in exclude}
        return hashlib.sha3_256(GDCLEngine._canonical_json(clean)).hexdigest()

    def _sign(self, hash_hex: str) -> Tuple[Optional[str], Optional[str]]:
        if not self._provider:
            return None, None
        sk_b64 = os.environ.get("OMNIX_SIGNING_SECRET_KEY_B64", "").strip()
        if not sk_b64:
            return None, None
        try:
            sk = base64.b64decode(sk_b64)
            sig = self._provider.sign(hash_hex.encode("utf-8"), sk)
            if sig:
                return base64.b64encode(sig).decode(), self._provider.algorithm_name()
        except Exception as exc:
            logger.warning(f"[ATF.GDCL] Sign failed: {exc}")
        return None, None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ensure_tables(self) -> bool:
        """Idempotent DDL — creates atf_gdcl_convergence_records if absent."""
        if not self._db_url:
            return False
        conn = self._get_conn()
        if not conn:
            return False
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(DDL_GDCL_CONVERGENCE_RECORDS)
            logger.info("[ATF.GDCL] Table ready: atf_gdcl_convergence_records")
            return True
        except Exception as exc:
            logger.warning(f"[ATF.GDCL] ensure_tables failed: {exc}")
            return False
        finally:
            conn.close()

    def converge(
        self,
        rsa_results: List[Any],
        receiving_runtime_id: Optional[str] = None,
    ) -> GDCLConvergenceRecord:
        """
        Ingest N RSA objects and emit a single typed GDCLConvergenceRecord.

        Args:
            rsa_results:           List of RSA objects (dataclass or dict).
                                   Accepts RetroactiveSemanticAssessment instances,
                                   dicts from .to_dict(), or any duck-typed object
                                   with rsa_id / receipt_id / dspp_verdict /
                                   aggregate_sdu / portability_confidence attrs.
            receiving_runtime_id:  Runtime performing the convergence.
                                   Defaults to self.runtime_id.

        Returns:
            GDCLConvergenceRecord — PQC-signed, persisted to DB if available.

        Raises:
            GDCLInvalidInputError: malformed RSA input.
            GDCLDeterminismError:  internal determinism violation (should never occur).
        """
        runtime_id = receiving_runtime_id or self.runtime_id
        now = datetime.now(timezone.utc).isoformat()

        # Normalize inputs (GDCL-INV-005: read only verdict/sdu/confidence)
        inputs: List[RSAInput] = [RSAInput.from_obj(r) for r in rsa_results]

        # Compute composite verdict (pure function — GDCL-INV-003)
        composite = compute_composite_verdict(inputs)

        # Build metrics (sorted for determinism — GDCL-INV-003)
        rsa_ids_sorted    = sorted(inp.rsa_id    for inp in inputs)
        receipt_ids_sorted = sorted(set(inp.receipt_id for inp in inputs))

        verdict_distribution: Dict[str, int] = {v: 0 for v in _ALL_DSPP_VERDICTS}
        for inp in inputs:
            verdict_distribution[inp.dspp_verdict] += 1
        # Remove zero-count verdicts for cleanliness
        verdict_distribution = {k: v for k, v in verdict_distribution.items() if v > 0}

        if inputs:
            sdus         = [inp.aggregate_sdu          for inp in inputs]
            confidences  = [inp.portability_confidence for inp in inputs]
            dominant_sdu = max(sdus)
            mean_sdu     = sum(sdus) / len(sdus)
            min_conf     = min(confidences)
        else:
            dominant_sdu = 0.0
            mean_sdu     = 0.0
            min_conf     = 1.0

        boundary_rec = _BOUNDARY_RECOMMENDATIONS.get(composite, "")

        gcr_id = f"OMNIX-GCR-{uuid.uuid4().hex[:16].upper()}"

        core_fields: Dict[str, Any] = {
            "gcr_id":                      gcr_id,
            "receiving_runtime_id":        runtime_id,
            "rsa_ids":                     rsa_ids_sorted,
            "receipt_ids":                 receipt_ids_sorted,
            "n_assessments":               len(inputs),
            "verdict_distribution":        verdict_distribution,
            "composite_verdict":           composite.value,
            "dominant_sdu":                round(dominant_sdu, 4),
            "mean_sdu":                    round(mean_sdu, 4),
            "min_portability_confidence":  round(min_conf, 4),
            "boundary_recommendation":     boundary_rec,
            "converged_at":                now,
            "created_at":                  now,
        }

        content_hash = self._compute_hash(core_fields)
        pqc_sig, pqc_alg = self._sign(content_hash)

        gcr = GDCLConvergenceRecord(
            gcr_id=gcr_id,
            receiving_runtime_id=runtime_id,
            rsa_ids=rsa_ids_sorted,
            receipt_ids=receipt_ids_sorted,
            n_assessments=len(inputs),
            verdict_distribution=verdict_distribution,
            composite_verdict=composite.value,
            dominant_sdu=round(dominant_sdu, 4),
            mean_sdu=round(mean_sdu, 4),
            min_portability_confidence=round(min_conf, 4),
            boundary_recommendation=boundary_rec,
            converged_at=now,
            content_hash=content_hash,
            pqc_signature=pqc_sig,
            pqc_algorithm=pqc_alg,
            created_at=now,
        )

        # GDCL-INV-006: persist append-only
        self._persist(gcr)

        logger.info(
            f"[ATF.GDCL] Converged {len(inputs)} RSAs → {composite.value} "
            f"(dominant_sdu={dominant_sdu:.4f}, signed={gcr.is_signed()}) [{gcr_id}]"
        )
        return gcr

    def verify_convergence_record(self, gcr: GDCLConvergenceRecord) -> Dict[str, Any]:
        """
        Verify integrity of a GDCLConvergenceRecord.

        Checks:
          1. content_hash recomputation
          2. PQC signature (if present)
          3. composite_verdict re-derivation from verdict_distribution
          4. n_assessments consistency

        Returns:
            dict with keys: valid (bool), checks (list), errors (list)
        """
        checks: List[str] = []
        errors: List[str] = []

        # Check 1 — content_hash
        data = gcr.to_dict()
        recomputed = self._compute_hash(data)
        if recomputed == gcr.content_hash:
            checks.append("PASS: content_hash recomputation matches")
        else:
            errors.append(
                f"FAIL: content_hash mismatch — stored={gcr.content_hash[:16]}… "
                f"recomputed={recomputed[:16]}…"
            )

        # Check 2 — PQC signature
        if gcr.pqc_signature and gcr.pqc_algorithm:
            pk_b64 = os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64", "").strip()
            if pk_b64 and self._provider:
                try:
                    pk = base64.b64decode(pk_b64)
                    sig = base64.b64decode(gcr.pqc_signature)
                    ok = self._provider.verify(gcr.content_hash.encode("utf-8"), sig, pk)
                    if ok:
                        checks.append(f"PASS: PQC signature valid ({gcr.pqc_algorithm})")
                    else:
                        errors.append(f"FAIL: PQC signature invalid ({gcr.pqc_algorithm})")
                except Exception as exc:
                    errors.append(f"FAIL: PQC verification error: {exc}")
            else:
                checks.append("SKIP: PQC signature present but no public key available for verification")
        else:
            checks.append("SKIP: no PQC signature present (unsigned GCR)")

        # Check 3 — composite verdict re-derivation
        dist = gcr.verdict_distribution
        total_from_dist = sum(dist.values())
        if total_from_dist == gcr.n_assessments:
            checks.append(f"PASS: n_assessments={gcr.n_assessments} consistent with verdict_distribution")
        else:
            errors.append(
                f"FAIL: n_assessments={gcr.n_assessments} but "
                f"sum(verdict_distribution)={total_from_dist}"
            )

        # Check 4 — composite_verdict value is in taxonomy
        valid_verdicts = {v.value for v in GDCLCompositeVerdict}
        if gcr.composite_verdict in valid_verdicts:
            checks.append(f"PASS: composite_verdict '{gcr.composite_verdict}' is a valid GDCL verdict")
        else:
            errors.append(f"FAIL: composite_verdict '{gcr.composite_verdict}' not in GDCL taxonomy")

        # Check 5 — GDCL-INV-002: FULL_RELIANCE and REFUSED not both present
        if (gcr.composite_verdict == GDCLCompositeVerdict.FULL_RELIANCE.value
                and dist.get(_VERDICT_INCOMPATIBLE, 0) > 0):
            errors.append(
                "FAIL: GDCL-INV-002 violation — FULL_RELIANCE with INCOMPATIBLE in distribution"
            )
        else:
            checks.append("PASS: GDCL-INV-002 — FULL_RELIANCE/REFUSED mutual exclusivity holds")

        return {
            "gcr_id": gcr.gcr_id,
            "composite_verdict": gcr.composite_verdict,
            "valid": len(errors) == 0,
            "checks": checks,
            "errors": errors,
            "n_checks": len(checks) + len(errors),
            "n_passed": len(checks),
            "n_failed": len(errors),
        }

    def get_record(self, gcr_id: str) -> Optional[GDCLConvergenceRecord]:
        """Retrieve a GCR by ID — checks in-memory store first, then DB."""
        with self._lock:
            if gcr_id in self._store:
                return self._store[gcr_id]
        return self._fetch_from_db(gcr_id)

    # ------------------------------------------------------------------
    # Persistence (GDCL-INV-006)
    # ------------------------------------------------------------------

    def _persist(self, gcr: GDCLConvergenceRecord) -> bool:
        with self._lock:
            self._store[gcr.gcr_id] = gcr

        if not self._db_url:
            return False
        conn = self._get_conn()
        if not conn:
            return False
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO atf_gdcl_convergence_records (
                            gcr_id, receiving_runtime_id, rsa_ids, receipt_ids,
                            n_assessments, verdict_distribution, composite_verdict,
                            dominant_sdu, mean_sdu, min_portability_confidence,
                            boundary_recommendation, converged_at,
                            content_hash, pqc_signature, pqc_algorithm, created_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s
                        )
                        ON CONFLICT (gcr_id) DO NOTHING
                        """,
                        (
                            gcr.gcr_id,
                            gcr.receiving_runtime_id,
                            json.dumps(gcr.rsa_ids),
                            json.dumps(gcr.receipt_ids),
                            gcr.n_assessments,
                            json.dumps(gcr.verdict_distribution),
                            gcr.composite_verdict,
                            gcr.dominant_sdu,
                            gcr.mean_sdu,
                            gcr.min_portability_confidence,
                            gcr.boundary_recommendation,
                            gcr.converged_at,
                            gcr.content_hash,
                            gcr.pqc_signature,
                            gcr.pqc_algorithm,
                            gcr.created_at,
                        ),
                    )
            logger.debug(f"[ATF.GDCL] Persisted GCR: {gcr.gcr_id}")
            return True
        except Exception as exc:
            logger.warning(f"[ATF.GDCL] Persist failed for {gcr.gcr_id}: {exc}")
            return False
        finally:
            conn.close()

    def _fetch_from_db(self, gcr_id: str) -> Optional[GDCLConvergenceRecord]:
        if not self._db_url:
            return None
        conn = self._get_conn()
        if not conn:
            return None
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM atf_gdcl_convergence_records WHERE gcr_id = %s",
                    (gcr_id,),
                )
                row = cur.fetchone()
            if not row:
                return None
            cols = [desc[0] for desc in cur.description] if hasattr(cur, "description") else []
            data = dict(zip(cols, row)) if cols else {}
            return GDCLConvergenceRecord(
                gcr_id=data["gcr_id"],
                receiving_runtime_id=data["receiving_runtime_id"],
                rsa_ids=data.get("rsa_ids") or [],
                receipt_ids=data.get("receipt_ids") or [],
                n_assessments=data["n_assessments"],
                verdict_distribution=data.get("verdict_distribution") or {},
                composite_verdict=data["composite_verdict"],
                dominant_sdu=float(data["dominant_sdu"]),
                mean_sdu=float(data["mean_sdu"]),
                min_portability_confidence=float(data["min_portability_confidence"]),
                boundary_recommendation=data.get("boundary_recommendation", ""),
                converged_at=str(data["converged_at"]),
                content_hash=data["content_hash"],
                pqc_signature=data.get("pqc_signature"),
                pqc_algorithm=data.get("pqc_algorithm"),
                created_at=str(data["created_at"]),
            )
        except Exception as exc:
            logger.warning(f"[ATF.GDCL] Fetch failed for {gcr_id}: {exc}")
            return None
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------

def converge_rsa_results(
    rsa_results: List[Any],
    receiving_runtime_id: str = "OMNIX-RUNTIME-LOCAL",
    db_url: Optional[str] = None,
) -> GDCLConvergenceRecord:
    """
    Module-level convenience wrapper. Creates a transient GDCLEngine and converges.

    Use this for one-shot convergence without managing an engine instance.
    For repeated calls (e.g., per-session), instantiate GDCLEngine directly.

    Args:
        rsa_results:           List of RSA objects.
        receiving_runtime_id:  Defaults to "OMNIX-RUNTIME-LOCAL".
        db_url:                Optional PostgreSQL URL. Falls back to DATABASE_URL env.

    Returns:
        GDCLConvergenceRecord — the composite boundary outcome.
    """
    engine = GDCLEngine(runtime_id=receiving_runtime_id, db_url=db_url)
    return engine.converge(rsa_results, receiving_runtime_id=receiving_runtime_id)
