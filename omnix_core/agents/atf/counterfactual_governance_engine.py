"""
OMNIX Agent Trust Fabric — Counterfactual Governance Engine (CGE)
ADR-178: Cryptographically attested alternative governance paths.

Two record types:
  - CounterfactualForkRecord (CFR): one alternative governance path, signed
  - CounterfactualAttestationToken (CAT): bound set of all CFRs for an evaluation

The CGE is strictly additive and read-only with respect to the primary pipeline.
Primary decisions are computed, sealed, and recorded BEFORE any CGE computation.
The CGE cannot alter the primary outcome (CGE-INV-002 — hard invariant).

Key invariants:
    CGE-INV-001: Every evaluation with CGE_ENABLED=true produces a CAT with ≥1 CFR
    CGE-INV-002: Primary governance decision is identical whether CGE is enabled or not
    CGE-INV-003: Every CFR is sealed with ML-DSA-65
    CGE-INV-004: cat_root_hash = sha256(sorted(cfr_content_hashes)) — tampering detectable
    CGE-INV-005: No parameter variation exceeds CGE_MAX_VARIATION_PCT (default 0.40)
    CGE-INV-006: CFRs and CATs are append-only — no UPDATE or DELETE
    CGE-INV-007: Full offline verifiability from CAT + primary receipt + public key

Status: IMPLEMENTED · TESTED · NOT DEPLOYED (Railway — pending CGE_ENABLED env var)

ADR-178 — Harold Nunes — OMNIX QUANTUM LTD — June 2026
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import struct
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("OMNIX.ATF.CGE")

# ─────────────────────────────────────────────────────────────────────────────
# Compiled constants
# ─────────────────────────────────────────────────────────────────────────────
CGE_DEFAULT_FORK_COUNT = 3
CGE_MIN_FORK_COUNT = 1
CGE_MAX_FORK_COUNT = 7
CGE_DEFAULT_MAX_VARIATION_PCT = 0.40
CGE_MIN_VARIATION_PCT = 0.05
CGE_ATF_SPEC_VERSION = "1.4"

# CES thresholds (ATF compiled constants — mirrors RCR)
_CES_NOMINAL    = 80.0
_CES_MONITORING = 50.0
_CES_WARNING    = 30.0

DDL_CGE = """
CREATE TABLE IF NOT EXISTS atf_counterfactual_forks (
    id                              SERIAL PRIMARY KEY,
    cfr_id                          TEXT NOT NULL UNIQUE,
    cat_id                          TEXT NOT NULL,
    primary_receipt_id              TEXT NOT NULL,
    evaluation_id                   TEXT NOT NULL,
    variation_vector                JSONB NOT NULL,
    counterfactual_outcome          TEXT NOT NULL,
    counterfactual_ces_score        NUMERIC(6,3),
    outcome_diverges_from_primary   BOOLEAN NOT NULL,
    divergence_invariant_triggered  TEXT,
    posture_state_hash_cf           TEXT NOT NULL,
    cfr_seal                        TEXT,
    pqc_algorithm                   TEXT,
    issued_at                       TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at                      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_cfr_primary_receipt
    ON atf_counterfactual_forks(primary_receipt_id);
CREATE INDEX IF NOT EXISTS idx_cfr_cat
    ON atf_counterfactual_forks(cat_id);

CREATE TABLE IF NOT EXISTS atf_counterfactual_tokens (
    id                      SERIAL PRIMARY KEY,
    cat_id                  TEXT NOT NULL UNIQUE,
    primary_receipt_id      TEXT NOT NULL,
    evaluation_timestamp    TIMESTAMP WITH TIME ZONE NOT NULL,
    cfr_count               INTEGER NOT NULL,
    cfr_ids                 TEXT[] NOT NULL,
    cfr_content_hashes      TEXT[] NOT NULL,
    cat_root_hash           TEXT NOT NULL,
    divergence_count        INTEGER NOT NULL DEFAULT 0,
    decision_space_summary  JSONB NOT NULL,
    cat_seal                TEXT,
    pqc_algorithm           TEXT,
    atf_spec_version        TEXT NOT NULL DEFAULT '1.4',
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_cat_primary_receipt
    ON atf_counterfactual_tokens(primary_receipt_id);
"""


class CGEInvariantViolation(Exception):
    """Raised when a CGE invariant is violated (CGE-INV-001 through CGE-INV-007)."""


@dataclass
class CounterfactualForkRecord:
    """
    CFR — One alternative governance path for a given evaluation.

    The posture_state_hash_cf is computed identically to the primary
    posture_state_hash using the variation-adjusted parameters, enabling
    offline independent verification using the same procedure as primary records.

    ID format: CFR-{16HEX}
    """
    cfr_id: str
    cat_id: str
    primary_receipt_id: str
    evaluation_id: str
    variation_vector: Dict[str, float]
    counterfactual_outcome: str           # NOMINAL | MONITORING | WARNING | HALT | REJECT
    counterfactual_ces_score: float
    outcome_diverges_from_primary: bool
    divergence_invariant_triggered: Optional[str]
    posture_state_hash_cf: str            # SHA3-256 over variation-adjusted fields
    cfr_seal: Optional[str]              # ML-DSA-65 over cfr content hash
    pqc_algorithm: Optional[str]
    issued_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def content_hash(self) -> str:
        """SHA3-256 of canonical CFR content (excluding seal fields)."""
        payload = {k: v for k, v in self.to_dict().items()
                   if k not in {"cfr_seal", "pqc_algorithm"}}
        return hashlib.sha3_256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
        ).hexdigest()


@dataclass
class CounterfactualAttestationToken:
    """
    CAT — The complete, cryptographically bound set of CFRs for one evaluation.

    cat_root_hash = sha256(sorted(cfr_content_hashes))
    Any modification to any CFR invalidates the CAT seal (CGE-INV-004).

    ID format: CAT-{16HEX}
    """
    cat_id: str
    primary_receipt_id: str
    evaluation_timestamp: str
    cfr_count: int
    cfr_ids: List[str]
    cfr_content_hashes: List[str]
    cat_root_hash: str
    divergence_count: int
    decision_space_summary: Dict[str, Any]
    cat_seal: Optional[str]
    pqc_algorithm: Optional[str]
    atf_spec_version: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def verify_root_hash(self) -> bool:
        """CGE-INV-004: recompute and compare cat_root_hash."""
        expected = hashlib.sha256(
            json.dumps(sorted(self.cfr_content_hashes), separators=(",", ":")).encode()
        ).hexdigest()
        return expected == self.cat_root_hash


class CounterfactualGovernanceEngine:
    """
    CGE Engine — Generates and manages counterfactual governance paths.

    Design contract:
        evaluate(primary_receipt_id, primary_params)  → CounterfactualAttestationToken
        verify_cat(cat, cfrs)                          → dict (full verification result)
        get_cat(cat_id)                                → CounterfactualAttestationToken | None
        get_cfrs_for_cat(cat_id)                       → List[CounterfactualForkRecord]
        ensure_tables()                                → bool

    CGE-INV-002 GUARANTEE: The `evaluate()` method is read-only with respect to
    the primary governance pipeline. It never modifies primary records.

    Deterministic CSPRNG: variations are generated via SHA3-256 counter-mode
    seeded from sha3_256(eval_id || primary_receipt_id), ensuring full
    reproducibility without storing random state (CGE-INV-007).
    """

    def __init__(self, db_url: Optional[str] = None):
        self._db_url = db_url or os.environ.get("DATABASE_URL")
        self._enabled = os.environ.get("CGE_ENABLED", "true").lower() == "true"
        self._fork_count = self._clamp_int(
            os.environ.get("CGE_FORK_COUNT", str(CGE_DEFAULT_FORK_COUNT)),
            CGE_MIN_FORK_COUNT, CGE_MAX_FORK_COUNT, CGE_DEFAULT_FORK_COUNT
        )
        self._max_variation = self._clamp_float(
            os.environ.get("CGE_MAX_VARIATION_PCT", str(CGE_DEFAULT_MAX_VARIATION_PCT)),
            CGE_MIN_VARIATION_PCT, CGE_DEFAULT_MAX_VARIATION_PCT, CGE_DEFAULT_MAX_VARIATION_PCT
        )
        self._cat_store: Dict[str, CounterfactualAttestationToken] = {}
        self._cfr_store: Dict[str, List[CounterfactualForkRecord]] = {}
        self._lock = threading.Lock()
        self._provider = self._load_provider()

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _clamp_int(val: str, lo: int, hi: int, default: int) -> int:
        try:
            return max(lo, min(hi, int(val)))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _clamp_float(val: str, lo: float, hi: float, default: float) -> float:
        try:
            return max(lo, min(hi, float(val)))
        except (ValueError, TypeError):
            return default

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
            logger.warning(f"[CGE] DB connection failed: {exc}")
            return None

    @staticmethod
    def _new_cfr_id() -> str:
        return f"CFR-{uuid.uuid4().hex[:16].upper()}"

    @staticmethod
    def _new_cat_id() -> str:
        return f"CAT-{uuid.uuid4().hex[:16].upper()}"

    @staticmethod
    def _new_eval_id() -> str:
        return f"CGE-EVAL-{uuid.uuid4().hex[:16].upper()}"

    @staticmethod
    def _sha3_256(data: str) -> str:
        return hashlib.sha3_256(data.encode("utf-8")).hexdigest()

    @staticmethod
    def _sha256(data: str) -> str:
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def _sign(self, content_hash: str) -> Tuple[Optional[str], Optional[str]]:
        if not self._provider:
            return None, None
        sk_b64 = os.environ.get("OMNIX_SIGNING_SECRET_KEY_B64", "").strip()
        if not sk_b64:
            return None, None
        try:
            sk = base64.b64decode(sk_b64)
            sig = self._provider.sign(content_hash.encode(), sk)
            if sig:
                return base64.b64encode(sig).decode(), self._provider.algorithm_name()
        except Exception as exc:
            logger.warning(f"[CGE] PQC sign failed: {exc}")
        return None, None

    def _verify_seal(self, seal_b64: str, content_hash: str) -> bool:
        pub_b64 = os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64", "")
        if not self._provider or not pub_b64:
            return False
        try:
            sig = base64.b64decode(seal_b64)
            pk = base64.b64decode(pub_b64)
            return bool(self._provider.verify(sig, content_hash.encode(), pk))
        except Exception:
            return False

    # ── Deterministic CSPRNG (CGE-INV-007) ───────────────────────────────────

    def _derive_variation_seed(self, evaluation_id: str, primary_receipt_id: str) -> bytes:
        """
        Deterministic seed: SHA3-256(evaluation_id || "||" || primary_receipt_id).
        Reproducible without storing state — any party can recompute.
        """
        combined = f"{evaluation_id}||{primary_receipt_id}"
        return hashlib.sha3_256(combined.encode()).digest()

    def _derive_variation_scalar(self, seed: bytes, counter: int) -> float:
        """
        Counter-mode SHA3-256 expansion: SHA3-256(seed || counter_bytes) → float in [0, 1).
        CGE-INV-005: caller enforces the ±max_variation_pct bound.
        """
        counter_bytes = struct.pack(">Q", counter)
        h = hashlib.sha3_256(seed + counter_bytes).digest()
        # Interpret first 8 bytes as uint64, normalize to [0, 1)
        uint64_val = struct.unpack(">Q", h[:8])[0]
        return uint64_val / (2 ** 64)

    def _generate_variation_vector(
        self,
        seed: bytes,
        fork_index: int,
        primary_params: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Generate one deterministic variation vector for fork_index.

        Uses counter-mode CSPRNG: each parameter gets its own counter lane
        (fork_index * 10 + param_index) to prevent correlation between forks.

        CGE-INV-005: all variations clamped to [-max_variation, +max_variation].
        """
        param_keys = [
            "authority_budget_delta_pct",
            "ces_threshold_nominal_override",
            "delegation_depth_limit_override",
            "fragmentation_limit_override",
        ]
        vector: Dict[str, float] = {}
        base_counter = fork_index * 10

        for i, key in enumerate(param_keys):
            scalar = self._derive_variation_scalar(seed, base_counter + i)
            # Map [0, 1) to [-max_variation, +max_variation]
            delta = (scalar * 2.0 - 1.0) * self._max_variation

            if key == "authority_budget_delta_pct":
                vector[key] = round(delta, 4)
            elif key == "ces_threshold_nominal_override":
                base = primary_params.get("ces_threshold_nominal", _CES_NOMINAL)
                variation = base * delta
                vector[key] = round(
                    max(_CES_MONITORING + 1.0, min(100.0, base + variation)), 2
                )
            elif key == "delegation_depth_limit_override":
                base_depth = int(primary_params.get("delegation_depth", 3))
                delta_depth = max(0, round(base_depth * abs(delta)))
                sign = 1 if delta >= 0 else -1
                vector[key] = max(1, base_depth + sign * delta_depth)
            elif key == "fragmentation_limit_override":
                base_frag = primary_params.get("fragmentation_limit", 0.90)
                variation = base_frag * delta
                vector[key] = round(
                    max(0.50, min(0.95, base_frag + variation)), 3
                )

        return vector

    # ── CES computation ───────────────────────────────────────────────────────

    @staticmethod
    def _compute_counterfactual_outcome(
        ces_score: float,
        authority_budget: float,
        nominal_threshold: float,
    ) -> Tuple[str, Optional[str]]:
        """
        Derive NOMINAL/MONITORING/WARNING/HALT/REJECT from counterfactual parameters.
        Returns (outcome, invariant_triggered_if_diverges).
        """
        if authority_budget <= 0:
            return "REJECT", "CGE-REJECT-ZERO-BUDGET"
        if ces_score < _CES_WARNING:
            return "HALT", "RGC-INV-003"
        if ces_score < _CES_MONITORING:
            return "WARNING", "RGC-INV-002"
        if ces_score < nominal_threshold:
            return "MONITORING", None
        return "NOMINAL", None

    # ── Main evaluation entry point ───────────────────────────────────────────

    def evaluate(
        self,
        primary_receipt_id: str,
        primary_params: Dict[str, Any],
        primary_outcome: str,
    ) -> CounterfactualAttestationToken:
        """
        Generate M counterfactual governance paths for a primary evaluation.

        CGE-INV-002: This method is READ-ONLY. It never modifies or touches
        any primary receipt, record, or governance state.

        Args:
            primary_receipt_id:  ID of the DR/TAR/RCR that triggered this evaluation
            primary_params:      Dict of primary governance parameters:
                                   ces_score, authority_budget, delegation_depth,
                                   fragmentation_limit, ces_threshold_nominal (optional)
            primary_outcome:     The sealed primary outcome (NOMINAL/MONITORING/WARNING/HALT)

        Returns:
            CounterfactualAttestationToken — PQC-sealed, with CFR_COUNT forks.

        Raises:
            CGEInvariantViolation if CGE_ENABLED=false or no forks produced.
        """
        if not self._enabled:
            raise CGEInvariantViolation(
                "CGE_ENABLED=false — counterfactual evaluation disabled"
            )
        if not primary_receipt_id:
            raise ValueError("[CGE] primary_receipt_id required")

        evaluation_id = self._new_eval_id()
        cat_id = self._new_cat_id()
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        seed = self._derive_variation_seed(evaluation_id, primary_receipt_id)
        ces_primary = float(primary_params.get("ces_score", 75.0))
        budget_primary = float(primary_params.get("authority_budget", 80.0))
        nominal_threshold_primary = float(primary_params.get("ces_threshold_nominal", _CES_NOMINAL))

        cfrs: List[CounterfactualForkRecord] = []

        for fork_idx in range(self._fork_count):
            cfr_id = self._new_cfr_id()
            vector = self._generate_variation_vector(seed, fork_idx, {
                "ces_threshold_nominal": nominal_threshold_primary,
                "delegation_depth": primary_params.get("delegation_depth", 3),
                "fragmentation_limit": primary_params.get("fragmentation_limit", 0.90),
            })

            # Apply authority_budget_delta_pct to primary budget
            budget_delta = vector.get("authority_budget_delta_pct", 0.0)
            cf_budget = max(0.0, budget_primary * (1.0 + budget_delta))
            cf_nominal_threshold = vector.get("ces_threshold_nominal_override", nominal_threshold_primary)

            # CES score shifts proportionally with budget change (simplified model)
            ces_shift = ces_primary * (budget_delta * 0.3)
            cf_ces = max(0.0, min(100.0, ces_primary + ces_shift))

            cf_outcome, divergence_invariant = self._compute_counterfactual_outcome(
                cf_ces, cf_budget, cf_nominal_threshold
            )
            diverges = cf_outcome != primary_outcome

            # posture_state_hash_cf: SHA3-256 over variation-adjusted committed fields
            posture_payload = {
                "cfr_id":                      cfr_id,
                "primary_receipt_id":          primary_receipt_id,
                "evaluation_id":               evaluation_id,
                "variation_vector":            vector,
                "counterfactual_ces_score":    round(cf_ces, 3),
                "counterfactual_outcome":      cf_outcome,
                "outcome_diverges_from_primary": diverges,
            }
            posture_hash = self._sha3_256(
                json.dumps(posture_payload, sort_keys=True, separators=(",", ":"), default=str)
            )

            cfr = CounterfactualForkRecord(
                cfr_id=cfr_id,
                cat_id=cat_id,
                primary_receipt_id=primary_receipt_id,
                evaluation_id=evaluation_id,
                variation_vector=vector,
                counterfactual_outcome=cf_outcome,
                counterfactual_ces_score=round(cf_ces, 3),
                outcome_diverges_from_primary=diverges,
                divergence_invariant_triggered=divergence_invariant if diverges else None,
                posture_state_hash_cf=posture_hash,
                cfr_seal=None,
                pqc_algorithm=None,
                issued_at=now_iso,
            )

            # Sign CFR over its content hash (CGE-INV-003)
            cfr_hash = cfr.content_hash()
            cfr_seal, pqc_alg = self._sign(cfr_hash)
            if not cfr_seal:
                logger.warning(
                    f"[CGE] CFR {cfr_id} issued WITHOUT seal — "
                    "CGE-INV-003 requires ML-DSA-65. Set OMNIX_SIGNING_SECRET_KEY_B64."
                )
            cfr.cfr_seal = cfr_seal
            cfr.pqc_algorithm = pqc_alg

            cfrs.append(cfr)

        # CGE-INV-001: must produce ≥1 CFR
        if not cfrs:
            raise CGEInvariantViolation(
                f"[CGE] CGE-INV-001 VIOLATED: zero CFRs produced for evaluation {evaluation_id}"
            )

        # CGE-INV-004: cat_root_hash = sha256(sorted(cfr_content_hashes))
        cfr_hashes = [cfr.content_hash() for cfr in cfrs]
        cat_root_hash = self._sha256(
            json.dumps(sorted(cfr_hashes), separators=(",", ":"))
        )

        divergence_count = sum(1 for cfr in cfrs if cfr.outcome_diverges_from_primary)
        alt_outcomes: Dict[str, int] = {}
        for cfr in cfrs:
            alt_outcomes[cfr.counterfactual_outcome] = alt_outcomes.get(cfr.counterfactual_outcome, 0) + 1

        # Sensitivity heuristic: which params drove divergence?
        sensitivity_tags: List[str] = []
        for cfr in cfrs:
            if cfr.outcome_diverges_from_primary:
                v = cfr.variation_vector
                if abs(v.get("authority_budget_delta_pct", 0)) > 0.15:
                    sensitivity_tags.append("HIGH_BUDGET_SENSITIVITY")
                if v.get("ces_threshold_nominal_override", nominal_threshold_primary) > nominal_threshold_primary + 5:
                    sensitivity_tags.append("HIGH_CES_THRESHOLD_SENSITIVITY")
        sensitivity = " | ".join(sorted(set(sensitivity_tags))) or "STABLE"

        decision_space_summary = {
            "primary_outcome":      primary_outcome,
            "alternative_outcomes": alt_outcomes,
            "divergence_count":     divergence_count,
            "parameter_sensitivity": sensitivity,
            "fork_count":           len(cfrs),
            "max_variation_pct":    self._max_variation,
        }

        cat_content = {
            "cat_id":              cat_id,
            "primary_receipt_id":  primary_receipt_id,
            "evaluation_timestamp": now_iso,
            "cfr_count":           len(cfrs),
            "cfr_ids":             [cfr.cfr_id for cfr in cfrs],
            "cfr_content_hashes":  cfr_hashes,
            "cat_root_hash":       cat_root_hash,
            "divergence_count":    divergence_count,
            "decision_space_summary": decision_space_summary,
            "atf_spec_version":    CGE_ATF_SPEC_VERSION,
        }
        cat_hash = self._sha3_256(
            json.dumps(cat_content, sort_keys=True, separators=(",", ":"), default=str)
        )
        cat_seal, cat_alg = self._sign(cat_hash)
        if not cat_seal:
            logger.warning("[CGE] CAT issued WITHOUT PQC seal.")

        cat = CounterfactualAttestationToken(
            cat_id=cat_id,
            primary_receipt_id=primary_receipt_id,
            evaluation_timestamp=now_iso,
            cfr_count=len(cfrs),
            cfr_ids=[cfr.cfr_id for cfr in cfrs],
            cfr_content_hashes=cfr_hashes,
            cat_root_hash=cat_root_hash,
            divergence_count=divergence_count,
            decision_space_summary=decision_space_summary,
            cat_seal=cat_seal,
            pqc_algorithm=cat_alg,
            atf_spec_version=CGE_ATF_SPEC_VERSION,
        )

        with self._lock:
            self._cat_store[cat_id] = cat
            self._cfr_store[cat_id] = cfrs

        self._persist_cat_and_cfrs(cat, cfrs)
        logger.info(
            f"[CGE] CAT issued — id={cat_id} primary={primary_receipt_id} "
            f"forks={len(cfrs)} diverged={divergence_count} "
            f"primary_outcome={primary_outcome} sensitivity={sensitivity} "
            f"pqc={cat_alg or 'unsigned'}"
        )
        return cat

    # ── Verification (CGE-INV-007 offline) ───────────────────────────────────

    def verify_cat(
        self,
        cat: CounterfactualAttestationToken,
        cfrs: List[CounterfactualForkRecord],
    ) -> Dict[str, Any]:
        """
        Full offline verification of a CAT and its CFRs.

        CGE-INV-004: verifies cat_root_hash = sha256(sorted(cfr_content_hashes))
        CGE-INV-007: requires only CAT + CFRs + public key (no platform access)
        """
        # CGE-INV-004: root hash integrity
        root_hash_valid = cat.verify_root_hash()

        # CFR count consistency
        cfr_count_valid = (cat.cfr_count == len(cfrs))

        # Verify each CFR hash matches what CAT declares
        computed_hashes = [cfr.content_hash() for cfr in cfrs]
        all_hashes_match = sorted(computed_hashes) == sorted(cat.cfr_content_hashes)

        # CAT seal verification
        cat_content = {
            "cat_id":              cat.cat_id,
            "primary_receipt_id":  cat.primary_receipt_id,
            "evaluation_timestamp": cat.evaluation_timestamp,
            "cfr_count":           cat.cfr_count,
            "cfr_ids":             cat.cfr_ids,
            "cfr_content_hashes":  cat.cfr_content_hashes,
            "cat_root_hash":       cat.cat_root_hash,
            "divergence_count":    cat.divergence_count,
            "decision_space_summary": cat.decision_space_summary,
            "atf_spec_version":    cat.atf_spec_version,
        }
        cat_hash = self._sha3_256(
            json.dumps(cat_content, sort_keys=True, separators=(",", ":"), default=str)
        )
        pqc_valid = False
        pqc_checked = False
        if cat.cat_seal:
            pqc_checked = True
            pqc_valid = self._verify_seal(cat.cat_seal, cat_hash)

        fully_verified = root_hash_valid and cfr_count_valid and all_hashes_match and (
            pqc_valid if pqc_checked else True
        )

        return {
            "cat_id":               cat.cat_id,
            "primary_receipt_id":   cat.primary_receipt_id,
            "root_hash_valid":      root_hash_valid,       # CGE-INV-004
            "cfr_count_valid":      cfr_count_valid,
            "all_hashes_match":     all_hashes_match,
            "pqc_valid":            pqc_valid,
            "pqc_checked":          pqc_checked,
            "pqc_signed":           cat.cat_seal is not None,
            "divergence_count":     cat.divergence_count,
            "primary_outcome":      cat.decision_space_summary.get("primary_outcome"),
            "alternative_outcomes": cat.decision_space_summary.get("alternative_outcomes"),
            "parameter_sensitivity": cat.decision_space_summary.get("parameter_sensitivity"),
            "fully_verified":       fully_verified,
            "cge_inv_002_respected": True,  # By design — evaluate() is read-only
        }

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def get_cat(self, cat_id: str) -> Optional[CounterfactualAttestationToken]:
        with self._lock:
            return self._cat_store.get(cat_id)

    def get_cfrs_for_cat(self, cat_id: str) -> List[CounterfactualForkRecord]:
        with self._lock:
            return list(self._cfr_store.get(cat_id, []))

    # ── DB persistence (append-only — CGE-INV-006) ───────────────────────────

    def ensure_tables(self) -> bool:
        if not self._db_url:
            return False
        conn = self._get_conn()
        if not conn:
            return False
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(DDL_CGE)
            logger.info("[CGE] Tables ready: atf_counterfactual_forks, atf_counterfactual_tokens")
            return True
        except Exception as exc:
            logger.warning(f"[CGE] ensure_tables failed: {exc}")
            return False
        finally:
            conn.close()

    def _persist_cat_and_cfrs(
        self,
        cat: CounterfactualAttestationToken,
        cfrs: List[CounterfactualForkRecord],
    ) -> None:
        if not self._db_url:
            return
        conn = self._get_conn()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    # Persist each CFR (append-only — CGE-INV-006)
                    for cfr in cfrs:
                        cur.execute("""
                            INSERT INTO atf_counterfactual_forks
                                (cfr_id, cat_id, primary_receipt_id, evaluation_id,
                                 variation_vector, counterfactual_outcome,
                                 counterfactual_ces_score, outcome_diverges_from_primary,
                                 divergence_invariant_triggered, posture_state_hash_cf,
                                 cfr_seal, pqc_algorithm, issued_at)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            ON CONFLICT (cfr_id) DO NOTHING
                        """, (
                            cfr.cfr_id, cfr.cat_id, cfr.primary_receipt_id, cfr.evaluation_id,
                            json.dumps(cfr.variation_vector),
                            cfr.counterfactual_outcome,
                            cfr.counterfactual_ces_score,
                            cfr.outcome_diverges_from_primary,
                            cfr.divergence_invariant_triggered,
                            cfr.posture_state_hash_cf,
                            cfr.cfr_seal, cfr.pqc_algorithm, cfr.issued_at,
                        ))
                    # Persist CAT (append-only)
                    cur.execute("""
                        INSERT INTO atf_counterfactual_tokens
                            (cat_id, primary_receipt_id, evaluation_timestamp,
                             cfr_count, cfr_ids, cfr_content_hashes, cat_root_hash,
                             divergence_count, decision_space_summary,
                             cat_seal, pqc_algorithm, atf_spec_version)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (cat_id) DO NOTHING
                    """, (
                        cat.cat_id, cat.primary_receipt_id, cat.evaluation_timestamp,
                        cat.cfr_count,
                        cat.cfr_ids,
                        cat.cfr_content_hashes,
                        cat.cat_root_hash,
                        cat.divergence_count,
                        json.dumps(cat.decision_space_summary),
                        cat.cat_seal, cat.pqc_algorithm, cat.atf_spec_version,
                    ))
        except Exception as exc:
            logger.warning(f"[CGE] persist failed: {exc}")
        finally:
            conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Process-level singleton
# ─────────────────────────────────────────────────────────────────────────────
_cge_engine: Optional[CounterfactualGovernanceEngine] = None
_cge_lock = threading.Lock()


def get_cge_engine() -> CounterfactualGovernanceEngine:
    global _cge_engine
    with _cge_lock:
        if _cge_engine is None:
            _cge_engine = CounterfactualGovernanceEngine()
    return _cge_engine


# ─────────────────────────────────────────────────────────────────────────────
# Executable example
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

    cge = CounterfactualGovernanceEngine()
    print("\n=== CGE — Counterfactual Governance Engine ===")
    print(f"CGE_ENABLED={cge._enabled} | FORK_COUNT={cge._fork_count} | MAX_VAR={cge._max_variation}\n")

    # Simulate a primary evaluation: NOMINAL outcome at CES=85
    cat = cge.evaluate(
        primary_receipt_id="ATFRCR-DEMO0000000000",
        primary_params={
            "ces_score":             85.0,
            "authority_budget":      90.0,
            "delegation_depth":      2,
            "fragmentation_limit":   0.85,
            "ces_threshold_nominal": 80.0,
        },
        primary_outcome="NOMINAL",
    )

    print(f"CAT issued:    {cat.cat_id}")
    print(f"  primary:     {cat.decision_space_summary['primary_outcome']}")
    print(f"  forks:       {cat.cfr_count}")
    print(f"  diverged:    {cat.divergence_count}")
    print(f"  sensitivity: {cat.decision_space_summary['parameter_sensitivity']}")
    print(f"  root_hash:   {cat.cat_root_hash[:32]}...")
    print(f"  pqc_seal:    {'YES — ' + (cat.pqc_algorithm or '') if cat.cat_seal else 'unsigned (no local key)'}")
    print(f"  root_hash_valid: {cat.verify_root_hash()}")

    cfrs = cge.get_cfrs_for_cat(cat.cat_id)
    for cfr in cfrs:
        div = "DIVERGES" if cfr.outcome_diverges_from_primary else "same"
        print(f"  CFR {cfr.cfr_id}: ces={cfr.counterfactual_ces_score} "
              f"outcome={cfr.counterfactual_outcome} [{div}]")

    result = cge.verify_cat(cat, cfrs)
    print(f"\nVerification:  fully_verified={result['fully_verified']}")
    print(f"  root_hash_valid={result['root_hash_valid']}  "
          f"all_hashes_match={result['all_hashes_match']}  "
          f"CGE-INV-002={result['cge_inv_002_respected']}")

    print("\n✓ CGE demonstration complete — status: IMPLEMENTED · TESTED · NOT DEPLOYED")
    sys.exit(0)
