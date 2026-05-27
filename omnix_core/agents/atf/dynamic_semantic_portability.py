"""
OMNIX Agent Trust Fabric — Dynamic Semantic Portability Protocol (DSPP)
ADR-173: Layer 5 dynamic semantic portability for cross-runtime ATF deployments.

Three artifact types:

  Temporal Semantic Anchor (TSA)
    Embedded in or attached to any ATF receipt at creation time.
    Records the originating runtime's exact semantic posture (SPV hash + version +
    generated_at) at the moment of issuance. Enables any receiving domain to
    reconstruct the exact semantic context without contacting the originating runtime.

  Semantic Drift Record (SDR)
    Published whenever a runtime's semantic posture evolves (new regulations, policy
    updates, jurisdictional changes). Append-only, PQC-signed. Documents what changed,
    why, and the quantified Semantic Distance Unit (SDU) delta per ATF Core Term.

  Retroactive Semantic Assessment (RSA)
    Computed locally by a receiving domain — offline, without bilateral negotiation,
    without originating runtime dependency. Answers: is this receipt still semantically
    portable in this domain? Produces a deterministic DSPP verdict.

Semantic Distance Unit (SDU) — [0.0, 1.0]:
    0.00–0.09 → SEMANTICALLY_PORTABLE    (no material drift)
    0.10–0.39 → DRIFT_ACKNOWLEDGED       (drift resolvable under MORE_RESTRICTIVE)
    0.40–0.69 → DRIFT_CRITICAL           (requires explicit acknowledgment)
    0.70–1.00 → SEMANTICALLY_INCOMPATIBLE (receipt cannot be portably interpreted)

DSPP Invariants (ADR-173 §Invariants):
    DSPP-INV-001: TSA anchored_at ≤ receipt created_at — no retroactive anchoring
    DSPP-INV-002: SDRs are append-only — drift cannot be erased from the record
    DSPP-INV-003: Drift toward permissiveness does not grant permissive interpretation
    DSPP-INV-004: TSA content_hash covers spv_hash + spv_version + spv_generated_at
    DSPP-INV-005: RSA verdict is deterministic — pure function of public inputs
    DSPP-INV-006: SEMANTICALLY_INCOMPATIBLE propagates upward through delegation chain
    DSPP-INV-007: SDU thresholds (0.10, 0.40, 0.70) are structural constants

ADR-173 — Harold Nunes — OMNIX QUANTUM LTD — May 2026
Priority Record: OMNIX-PAR-2026-DSPP-001
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

logger = logging.getLogger("OMNIX.ATF.DSPP")

ATF_CORE_TERM_SET: Tuple[str, ...] = (
    "AUTHORITY",
    "ADMISSIBILITY",
    "TRUST",
    "SOVEREIGNTY",
    "RISK",
    "ESCALATION",
    "REVOCATION",
    "LEGITIMACY",
)

SDU_PORTABLE_THRESHOLD = 0.10
SDU_ACKNOWLEDGED_THRESHOLD = 0.40
SDU_CRITICAL_THRESHOLD = 0.70

SDU_WEIGHT_BOUNDARY = 0.40
SDU_WEIGHT_SCOPE = 0.35
SDU_WEIGHT_REGULATORY = 0.25

VALID_DRIFT_CATEGORIES = (
    "REGULATORY_UPDATE",
    "POLICY_EVOLUTION",
    "JURISDICTIONAL",
    "OPERATIONAL",
    "CORRECTION",
)

VALID_DRIFT_DIRECTIONS = ("MORE_RESTRICTIVE", "LESS_RESTRICTIVE", "LATERAL")

VALID_RECEIPT_TYPES = ("DR", "TAR", "DTR", "RCR", "SAC")


class DSPPVerdict(str, Enum):
    SEMANTICALLY_PORTABLE = "SEMANTICALLY_PORTABLE"
    DRIFT_ACKNOWLEDGED = "DRIFT_ACKNOWLEDGED"
    DRIFT_CRITICAL = "DRIFT_CRITICAL"
    SEMANTICALLY_INCOMPATIBLE = "SEMANTICALLY_INCOMPATIBLE"


class DSPPError(Exception):
    """Base exception for DSPP violations."""


class TSARetroactiveViolation(DSPPError):
    """DSPP-INV-001: TSA anchored_at > receipt created_at."""


class SDRImmutabilityViolation(DSPPError):
    """DSPP-INV-002: Attempt to publish duplicate SDR for same previous_spv_hash."""


class DSPPNonDeterminismError(DSPPError):
    """DSPP-INV-005: RSA computation produced non-deterministic result (internal error)."""


DDL_TEMPORAL_SEMANTIC_ANCHORS = """
CREATE TABLE IF NOT EXISTS atf_temporal_semantic_anchors (
    tsa_id              VARCHAR(128)  PRIMARY KEY,
    receipt_id          VARCHAR(128)  NOT NULL,
    receipt_type        VARCHAR(16)   NOT NULL
                            CHECK (receipt_type IN ('DR','TAR','DTR','RCR','SAC')),
    runtime_id          VARCHAR(128)  NOT NULL,
    spv_id              VARCHAR(128)  NOT NULL,
    spv_hash            VARCHAR(64)   NOT NULL,
    spv_version         VARCHAR(16)   NOT NULL DEFAULT '1.0',
    spv_generated_at    TIMESTAMPTZ   NOT NULL,
    anchored_at         TIMESTAMPTZ   NOT NULL,
    term_hashes         JSONB         NOT NULL DEFAULT '{}',
    content_hash        VARCHAR(64)   NOT NULL,
    pqc_signature       TEXT          DEFAULT NULL,
    pqc_algorithm       VARCHAR(32)   DEFAULT NULL,
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_atf_tsa_receipt
    ON atf_temporal_semantic_anchors (receipt_id);
CREATE INDEX IF NOT EXISTS idx_atf_tsa_spv_hash
    ON atf_temporal_semantic_anchors (spv_hash);
CREATE INDEX IF NOT EXISTS idx_atf_tsa_runtime
    ON atf_temporal_semantic_anchors (runtime_id);
"""

DDL_SEMANTIC_DRIFT_RECORDS = """
CREATE TABLE IF NOT EXISTS atf_semantic_drift_records (
    sdr_id              VARCHAR(128)  PRIMARY KEY,
    runtime_id          VARCHAR(128)  NOT NULL,
    previous_spv_id     VARCHAR(128)  NOT NULL,
    previous_spv_hash   VARCHAR(64)   NOT NULL,
    new_spv_id          VARCHAR(128)  NOT NULL,
    new_spv_hash        VARCHAR(64)   NOT NULL,
    effective_from      TIMESTAMPTZ   NOT NULL,
    drift_reason        TEXT          NOT NULL,
    drift_category      VARCHAR(32)   NOT NULL
                            CHECK (drift_category IN (
                                'REGULATORY_UPDATE','POLICY_EVOLUTION',
                                'JURISDICTIONAL','OPERATIONAL','CORRECTION'
                            )),
    term_drift_map      JSONB         NOT NULL DEFAULT '{}',
    governance_impact   VARCHAR(32)   NOT NULL DEFAULT 'PORTABLE',
    regulatory_anchors  JSONB         NOT NULL DEFAULT '[]',
    content_hash        VARCHAR(64)   NOT NULL,
    pqc_signature       TEXT          DEFAULT NULL,
    pqc_algorithm       VARCHAR(32)   DEFAULT NULL,
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_atf_sdr_prev_spv_hash
    ON atf_semantic_drift_records (runtime_id, previous_spv_hash);
CREATE INDEX IF NOT EXISTS idx_atf_sdr_runtime
    ON atf_semantic_drift_records (runtime_id);
CREATE INDEX IF NOT EXISTS idx_atf_sdr_new_spv_hash
    ON atf_semantic_drift_records (new_spv_hash);
"""

DDL_RETROACTIVE_SEMANTIC_ASSESSMENTS = """
CREATE TABLE IF NOT EXISTS atf_retroactive_semantic_assessments (
    rsa_id                  VARCHAR(128)  PRIMARY KEY,
    tsa_id                  VARCHAR(128)  NOT NULL,
    receipt_id              VARCHAR(128)  NOT NULL,
    originating_runtime_id  VARCHAR(128)  NOT NULL,
    receiving_runtime_id    VARCHAR(128)  NOT NULL,
    originating_spv_hash    VARCHAR(64)   NOT NULL,
    receiving_spv_hash      VARCHAR(64)   NOT NULL,
    assessed_at             TIMESTAMPTZ   NOT NULL,
    sdr_chain_traversed     JSONB         NOT NULL DEFAULT '[]',
    term_assessment         JSONB         NOT NULL DEFAULT '{}',
    aggregate_sdu           NUMERIC(6,4)  NOT NULL,
    dspp_verdict            VARCHAR(32)   NOT NULL,
    portability_confidence  NUMERIC(6,4)  NOT NULL,
    governing_posture       VARCHAR(32)   NOT NULL DEFAULT 'MORE_RESTRICTIVE',
    content_hash            VARCHAR(64)   NOT NULL,
    pqc_signature           TEXT          DEFAULT NULL,
    pqc_algorithm           VARCHAR(32)   DEFAULT NULL,
    created_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_atf_rsa_tsa
    ON atf_retroactive_semantic_assessments (tsa_id);
CREATE INDEX IF NOT EXISTS idx_atf_rsa_receipt
    ON atf_retroactive_semantic_assessments (receipt_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_atf_rsa_tsa_receiving
    ON atf_retroactive_semantic_assessments (tsa_id, receiving_runtime_id, receiving_spv_hash);
"""


@dataclass
class TemporalSemanticAnchor:
    """
    Temporal Semantic Anchor (TSA) — DSPP Layer 5 artifact.
    Binds a receipt to the exact semantic posture of its originating runtime at creation time.

    Fields:
        tsa_id          — "OMNIX-TSA-{16HEX}"
        receipt_id      — ATF receipt this TSA anchors
        receipt_type    — DR | TAR | DTR | RCR | SAC
        runtime_id      — originating runtime identifier
        spv_id          — SPV ID at time of receipt creation
        spv_hash        — SHA-256 of the originating SPV (the semantic anchor)
        spv_version     — semantic version of the originating SPV
        spv_generated_at — when the originating SPV was generated
        anchored_at     — when this TSA was created (≤ receipt timestamp)
        term_hashes     — per-term content_hash from the originating SPV
        content_hash    — SHA-256 of canonical TSA fields (DSPP-INV-004)
        pqc_signature   — ML-DSA-65 signature over content_hash
        pqc_algorithm   — "ML-DSA-65"
        created_at      — creation timestamp
    """
    tsa_id: str
    receipt_id: str
    receipt_type: str
    runtime_id: str
    spv_id: str
    spv_hash: str
    spv_version: str
    spv_generated_at: str
    anchored_at: str
    term_hashes: Dict[str, str]
    content_hash: str
    pqc_signature: Optional[str]
    pqc_algorithm: Optional[str]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_signed(self) -> bool:
        return self.pqc_signature is not None


@dataclass
class SemanticDriftRecord:
    """
    Semantic Drift Record (SDR) — DSPP Layer 5 artifact.
    Published when a runtime's semantic posture evolves. Append-only. PQC-signed.

    Fields:
        sdr_id              — "OMNIX-SDR-{runtime_id}-{16HEX}"
        runtime_id          — runtime publishing the drift record
        previous_spv_id     — SPV being superseded
        previous_spv_hash   — hash of the superseded SPV
        new_spv_id          — new SPV taking effect
        new_spv_hash        — hash of the new SPV
        effective_from      — when the new SPV takes effect
        drift_reason        — human-readable reason
        drift_category      — REGULATORY_UPDATE | POLICY_EVOLUTION | JURISDICTIONAL | OPERATIONAL | CORRECTION
        term_drift_map      — {term_id: {sdu, drift_direction, boundary_delta, scope_delta, regulatory_delta}}
        governance_impact   — PORTABLE | ACKNOWLEDGED | CRITICAL | INCOMPATIBLE
        regulatory_anchors  — legal/regulatory references
        content_hash        — SHA-256 of canonical SDR fields
        pqc_signature       — ML-DSA-65 signature
        pqc_algorithm       — "ML-DSA-65"
        created_at          — creation timestamp
    """
    sdr_id: str
    runtime_id: str
    previous_spv_id: str
    previous_spv_hash: str
    new_spv_id: str
    new_spv_hash: str
    effective_from: str
    drift_reason: str
    drift_category: str
    term_drift_map: Dict[str, Any]
    governance_impact: str
    regulatory_anchors: List[str]
    content_hash: str
    pqc_signature: Optional[str]
    pqc_algorithm: Optional[str]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_signed(self) -> bool:
        return self.pqc_signature is not None

    def max_sdu(self) -> float:
        if not self.term_drift_map:
            return 0.0
        return max(v.get("sdu", 0.0) for v in self.term_drift_map.values())

    def affected_terms(self) -> List[str]:
        return [t for t, v in self.term_drift_map.items() if v.get("sdu", 0.0) > 0.0]


@dataclass
class TermAssessment:
    """
    Per-term assessment result within an RSA.

    Fields:
        term_id                 — ATF Core Term identifier
        sdu                     — Semantic Distance Unit [0.0, 1.0]
        drift_direction         — MORE_RESTRICTIVE | LESS_RESTRICTIVE | LATERAL | NONE
        status                  — PORTABLE | ACKNOWLEDGED | CRITICAL | INCOMPATIBLE
        originating_hash        — STR content_hash from originating SPV
        receiving_hash          — STR content_hash from receiving SPV
        governing_interpretation — which interpretation governs (MORE_RESTRICTIVE)
        sdr_ids_applied         — SDR IDs that contributed to this term's drift
    """
    term_id: str
    sdu: float
    drift_direction: str
    status: str
    originating_hash: Optional[str]
    receiving_hash: Optional[str]
    governing_interpretation: str
    sdr_ids_applied: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RetroactiveSemanticAssessment:
    """
    Retroactive Semantic Assessment (RSA) — DSPP Layer 5 artifact.
    Computed locally, offline, without bilateral negotiation or originating runtime.

    Fields:
        rsa_id                  — "OMNIX-RSA-{16HEX}"
        tsa_id                  — TSA being assessed
        receipt_id              — receipt being assessed
        originating_runtime_id  — runtime that issued the receipt
        receiving_runtime_id    — domain performing the assessment
        originating_spv_hash    — SPV hash from the TSA
        receiving_spv_hash      — current SPV hash of the receiving domain
        assessed_at             — when the RSA was computed
        sdr_chain_traversed     — SDR IDs consulted during assessment
        term_assessment         — {term_id: TermAssessment}
        aggregate_sdu           — weighted mean SDU across all 8 terms
        dspp_verdict            — DSPPVerdict enum value
        portability_confidence  — 1.0 − aggregate_sdu
        governing_posture       — MORE_RESTRICTIVE (default)
        content_hash            — SHA-256 of canonical RSA fields
        pqc_signature           — ML-DSA-65 signature by receiving runtime
        pqc_algorithm           — "ML-DSA-65"
        created_at              — creation timestamp
    """
    rsa_id: str
    tsa_id: str
    receipt_id: str
    originating_runtime_id: str
    receiving_runtime_id: str
    originating_spv_hash: str
    receiving_spv_hash: str
    assessed_at: str
    sdr_chain_traversed: List[str]
    term_assessment: Dict[str, Any]
    aggregate_sdu: float
    dspp_verdict: str
    portability_confidence: float
    governing_posture: str
    content_hash: str
    pqc_signature: Optional[str]
    pqc_algorithm: Optional[str]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    def is_portable(self) -> bool:
        return self.dspp_verdict == DSPPVerdict.SEMANTICALLY_PORTABLE.value

    def is_incompatible(self) -> bool:
        return self.dspp_verdict == DSPPVerdict.SEMANTICALLY_INCOMPATIBLE.value

    def summary(self) -> Dict[str, Any]:
        return {
            "rsa_id": self.rsa_id,
            "receipt_id": self.receipt_id,
            "dspp_verdict": self.dspp_verdict,
            "aggregate_sdu": round(self.aggregate_sdu, 4),
            "portability_confidence": round(self.portability_confidence, 4),
            "affected_terms": [
                t for t, v in self.term_assessment.items()
                if isinstance(v, dict) and v.get("sdu", 0.0) > 0.0
            ],
        }


class DSPPEngine:
    """
    Dynamic Semantic Portability Protocol engine.
    Issues and manages TSA, SDR, and RSA artifacts.

    Design contract:
        create_tsa()         → TemporalSemanticAnchor (PQC-signed, persisted)
        publish_sdr()        → SemanticDriftRecord (append-only, PQC-signed, persisted)
        assess_portability() → RetroactiveSemanticAssessment (deterministic, PQC-signed)
        assess_chain_portability() → Dict[receipt_id, RSA] (DSPP-INV-006 chain propagation)
        compute_sdu()        → float (SDU per term pair)
        verify_tsa()         → dict (integrity check result)
        verify_sdr()         → dict (integrity check result)
        ensure_tables()      → idempotent DDL

    DSPP-INV-001 enforcement:
        create_tsa() raises TSARetroactiveViolation if anchored_at > receipt_created_at.

    DSPP-INV-002 enforcement:
        publish_sdr() raises SDRImmutabilityViolation if a SDR for the same
        (runtime_id, previous_spv_hash) already exists.

    DSPP-INV-005 enforcement:
        assess_portability() is a pure function — identical inputs always produce
        identical outputs. No random state in assessment logic.

    DSPP-INV-007 enforcement:
        SDU thresholds are module-level constants and are not configurable.
    """

    def __init__(self, runtime_id: str, db_url: Optional[str] = None):
        self.runtime_id = runtime_id
        self._db_url = db_url or os.environ.get("DATABASE_URL")
        self._tsa_store: Dict[str, TemporalSemanticAnchor] = {}
        self._sdr_store: Dict[str, SemanticDriftRecord] = {}
        self._rsa_store: Dict[str, RetroactiveSemanticAssessment] = {}
        self._sdr_by_prev_hash: Dict[str, str] = {}
        self._lock = threading.Lock()
        self._provider = self._load_provider()

    def _load_provider(self):
        try:
            from omnix_core.security.crypto_providers import get_active_provider
            return get_active_provider()
        except Exception:
            return None

    def _get_conn(self):
        try:
            import psycopg
            conn = psycopg.connect(self._db_url)
            return conn
        except Exception as exc:
            logger.warning(f"[ATF.DSPP] DB connection failed: {exc}")
            return None

    @staticmethod
    def _canonical_json(obj: Dict[str, Any]) -> bytes:
        return json.dumps(
            obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")

    @staticmethod
    def _compute_hash(fields: Dict[str, Any]) -> str:
        exclude = {
            "content_hash", "pqc_signature", "pqc_algorithm",
            "pqc_signature_a", "pqc_signature_b",
        }
        clean = {k: v for k, v in fields.items() if k not in exclude}
        return hashlib.sha256(DSPPEngine._canonical_json(clean)).hexdigest()

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
            logger.warning(f"[ATF.DSPP] Sign failed: {exc}")
        return None, None

    def ensure_tables(self) -> bool:
        if not self._db_url:
            return False
        conn = self._get_conn()
        if not conn:
            return False
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(DDL_TEMPORAL_SEMANTIC_ANCHORS)
                    cur.execute(DDL_SEMANTIC_DRIFT_RECORDS)
                    cur.execute(DDL_RETROACTIVE_SEMANTIC_ASSESSMENTS)
            logger.info("[ATF.DSPP] Tables ready: TSA + SDR + RSA")
            return True
        except Exception as exc:
            logger.warning(f"[ATF.DSPP] ensure_tables failed: {exc}")
            return False
        finally:
            conn.close()

    def create_tsa(
        self,
        receipt_id: str,
        receipt_type: str,
        spv: Any,
        receipt_created_at: Optional[str] = None,
        anchored_at: Optional[str] = None,
    ) -> TemporalSemanticAnchor:
        """
        Create a Temporal Semantic Anchor binding a receipt to its originating SPV.

        DSPP-INV-001: anchored_at must be ≤ receipt_created_at.
        DSPP-INV-004: content_hash covers spv_hash + spv_version + spv_generated_at.

        Args:
            receipt_id          — ATF receipt identifier
            receipt_type        — DR | TAR | DTR | RCR | SAC
            spv                 — SemanticPolicyVector (or dict) at receipt creation time
            receipt_created_at  — receipt timestamp (ISO UTC); defaults to now
            anchored_at         — TSA creation timestamp (ISO UTC); defaults to now

        Returns:
            TemporalSemanticAnchor — PQC-signed, persisted.

        Raises:
            TSARetroactiveViolation: anchored_at > receipt_created_at (DSPP-INV-001)
            ValueError: invalid receipt_type
        """
        if receipt_type not in VALID_RECEIPT_TYPES:
            raise ValueError(
                f"receipt_type '{receipt_type}' invalid. Must be one of {VALID_RECEIPT_TYPES}"
            )

        now = datetime.now(timezone.utc).isoformat()
        anchored_ts = anchored_at or now
        receipt_ts = receipt_created_at or now

        if anchored_ts > receipt_ts:
            raise TSARetroactiveViolation(
                f"DSPP-INV-001: TSA anchored_at ({anchored_ts}) > receipt_created_at ({receipt_ts}). "
                "A TSA cannot be added retroactively to an existing receipt."
            )

        spv_dict = spv if isinstance(spv, dict) else spv.to_dict()
        spv_id = spv_dict.get("spv_id", "")
        spv_hash = spv_dict.get("spv_hash", "")
        spv_generated_at = spv_dict.get("generated_at", now)

        spv_version = self._extract_spv_version(spv_dict)

        term_hashes: Dict[str, str] = {}
        core_term_set = spv_dict.get("atf_core_term_set", {})
        for term_id, term_data in core_term_set.items():
            if isinstance(term_data, dict):
                term_hashes[term_id] = term_data.get("content_hash", "")

        tsa_id = f"OMNIX-TSA-{uuid.uuid4().hex[:16].upper()}"

        core_fields: Dict[str, Any] = {
            "tsa_id": tsa_id,
            "receipt_id": receipt_id,
            "receipt_type": receipt_type,
            "runtime_id": self.runtime_id,
            "spv_id": spv_id,
            "spv_hash": spv_hash,
            "spv_version": spv_version,
            "spv_generated_at": spv_generated_at,
            "anchored_at": anchored_ts,
            "term_hashes": term_hashes,
            "created_at": now,
        }

        content_hash = self._compute_hash(core_fields)
        pqc_sig, pqc_alg = self._sign(content_hash)

        tsa = TemporalSemanticAnchor(
            tsa_id=tsa_id,
            receipt_id=receipt_id,
            receipt_type=receipt_type,
            runtime_id=self.runtime_id,
            spv_id=spv_id,
            spv_hash=spv_hash,
            spv_version=spv_version,
            spv_generated_at=spv_generated_at,
            anchored_at=anchored_ts,
            term_hashes=term_hashes,
            content_hash=content_hash,
            pqc_signature=pqc_sig,
            pqc_algorithm=pqc_alg,
            created_at=now,
        )

        with self._lock:
            self._tsa_store[tsa_id] = tsa

        self._persist_tsa(tsa)
        logger.info(
            f"[ATF.DSPP] TSA created — id={tsa_id} receipt={receipt_id} "
            f"type={receipt_type} spv_hash={spv_hash[:16]}... signed={pqc_sig is not None}"
        )
        return tsa

    def _extract_spv_version(self, spv_dict: Dict[str, Any]) -> str:
        term_set = spv_dict.get("atf_core_term_set", {})
        versions = []
        for term_data in term_set.values():
            if isinstance(term_data, dict) and "term_version" in term_data:
                versions.append(term_data["term_version"])
        if versions:
            return max(versions)
        return "1.0"

    def publish_sdr(
        self,
        previous_spv: Any,
        new_spv: Any,
        drift_reason: str,
        drift_category: str,
        regulatory_anchors: Optional[List[str]] = None,
        effective_from: Optional[str] = None,
    ) -> SemanticDriftRecord:
        """
        Publish a Semantic Drift Record documenting a transition between two SPV versions.

        DSPP-INV-002: One SDR per (runtime_id, previous_spv_hash). Cannot be re-published.
        The SDR chain is append-only — regulatory drift cannot be erased.

        Args:
            previous_spv        — SemanticPolicyVector (or dict) being superseded
            new_spv             — SemanticPolicyVector (or dict) taking effect
            drift_reason        — human-readable explanation of the semantic change
            drift_category      — REGULATORY_UPDATE | POLICY_EVOLUTION | JURISDICTIONAL |
                                  OPERATIONAL | CORRECTION
            regulatory_anchors  — list of legal/regulatory document references
            effective_from      — ISO UTC timestamp when new SPV takes effect (default: now)

        Returns:
            SemanticDriftRecord — PQC-signed, persisted.

        Raises:
            SDRImmutabilityViolation: duplicate (runtime_id, previous_spv_hash) (DSPP-INV-002)
            ValueError: invalid drift_category
        """
        if drift_category not in VALID_DRIFT_CATEGORIES:
            raise ValueError(
                f"drift_category '{drift_category}' invalid. "
                f"Must be one of {VALID_DRIFT_CATEGORIES}"
            )

        prev_dict = previous_spv if isinstance(previous_spv, dict) else previous_spv.to_dict()
        new_dict = new_spv if isinstance(new_spv, dict) else new_spv.to_dict()

        prev_spv_hash = prev_dict.get("spv_hash", "")
        new_spv_hash = new_dict.get("spv_hash", "")
        prev_spv_id = prev_dict.get("spv_id", "")
        new_spv_id = new_dict.get("spv_id", "")

        with self._lock:
            existing_key = f"{self.runtime_id}::{prev_spv_hash}"
            if existing_key in self._sdr_by_prev_hash:
                raise SDRImmutabilityViolation(
                    f"DSPP-INV-002: SDR already exists for runtime={self.runtime_id} "
                    f"previous_spv_hash={prev_spv_hash[:16]}... "
                    "Regulatory drift cannot be erased or re-published."
                )

        term_drift_map = self._compute_term_drift_map(prev_dict, new_dict)
        governance_impact = self._compute_governance_impact(term_drift_map)
        now = datetime.now(timezone.utc).isoformat()
        sdr_id = f"OMNIX-SDR-{self.runtime_id}-{uuid.uuid4().hex[:16].upper()}"

        core_fields: Dict[str, Any] = {
            "sdr_id": sdr_id,
            "runtime_id": self.runtime_id,
            "previous_spv_id": prev_spv_id,
            "previous_spv_hash": prev_spv_hash,
            "new_spv_id": new_spv_id,
            "new_spv_hash": new_spv_hash,
            "effective_from": effective_from or now,
            "drift_reason": drift_reason,
            "drift_category": drift_category,
            "term_drift_map": term_drift_map,
            "governance_impact": governance_impact,
            "regulatory_anchors": regulatory_anchors or [],
            "created_at": now,
        }

        content_hash = self._compute_hash(core_fields)
        pqc_sig, pqc_alg = self._sign(content_hash)

        sdr = SemanticDriftRecord(
            sdr_id=sdr_id,
            runtime_id=self.runtime_id,
            previous_spv_id=prev_spv_id,
            previous_spv_hash=prev_spv_hash,
            new_spv_id=new_spv_id,
            new_spv_hash=new_spv_hash,
            effective_from=effective_from or now,
            drift_reason=drift_reason,
            drift_category=drift_category,
            term_drift_map=term_drift_map,
            governance_impact=governance_impact,
            regulatory_anchors=regulatory_anchors or [],
            content_hash=content_hash,
            pqc_signature=pqc_sig,
            pqc_algorithm=pqc_alg,
            created_at=now,
        )

        with self._lock:
            self._sdr_store[sdr_id] = sdr
            self._sdr_by_prev_hash[f"{self.runtime_id}::{prev_spv_hash}"] = sdr_id

        self._persist_sdr(sdr)
        logger.info(
            f"[ATF.DSPP] SDR published — id={sdr_id} category={drift_category} "
            f"impact={governance_impact} max_sdu={sdr.max_sdu():.4f} "
            f"affected_terms={sdr.affected_terms()} signed={pqc_sig is not None}"
        )
        return sdr

    def assess_portability(
        self,
        tsa: TemporalSemanticAnchor,
        receiving_spv: Any,
        sdr_chain: Optional[List[SemanticDriftRecord]] = None,
        originating_str_entries: Optional[Dict[str, Any]] = None,
        receiving_str_entries: Optional[Dict[str, Any]] = None,
    ) -> RetroactiveSemanticAssessment:
        """
        Compute a Retroactive Semantic Assessment for a receipt in a receiving domain.

        DSPP-INV-005: This is a pure function. Identical inputs always produce identical output.
        No bilateral negotiation. No originating runtime required.

        The assessment compares:
        - The originating SPV captured in the TSA (what was meant at issuance)
        - The receiving domain's current SPV (what the domain means now)
        - The SDR chain from the originating runtime (how originating semantics evolved)

        Args:
            tsa                     — Temporal Semantic Anchor of the receipt being assessed
            receiving_spv           — current SPV of the receiving domain
            sdr_chain               — SDR chain from the originating runtime (may be empty)
            originating_str_entries — {term_id: definition_dict} at originating anchor time
            receiving_str_entries   — {term_id: definition_dict} for receiving domain now

        Returns:
            RetroactiveSemanticAssessment — deterministic, PQC-signed by receiving runtime.
        """
        recv_dict = receiving_spv if isinstance(receiving_spv, dict) else receiving_spv.to_dict()
        receiving_spv_hash = recv_dict.get("spv_hash", "")
        recv_term_set = recv_dict.get("atf_core_term_set", {})

        sdr_chain = sdr_chain or []
        sdr_ids_traversed = [s.sdr_id if hasattr(s, "sdr_id") else s.get("sdr_id", "")
                             for s in sdr_chain]

        term_assessment: Dict[str, Any] = {}
        for term_id in ATF_CORE_TERM_SET:
            orig_hash = tsa.term_hashes.get(term_id, "")
            recv_entry = recv_term_set.get(term_id, {})
            recv_hash = (recv_entry.get("content_hash", "") if isinstance(recv_entry, dict)
                         else "")

            sdu = self._compute_sdu_from_hashes(
                term_id=term_id,
                orig_hash=orig_hash,
                recv_hash=recv_hash,
                orig_entries=originating_str_entries or {},
                recv_entries=receiving_str_entries or {},
            )

            sdu_from_sdr = self._sdu_from_sdr_chain(term_id, sdr_chain)
            final_sdu = min(1.0, max(sdu, sdu_from_sdr))

            drift_direction = self._infer_drift_direction(
                term_id, sdr_chain, orig_hash, recv_hash
            )

            status = self._sdu_to_status(final_sdu)

            governing = self._governing_interpretation(
                drift_direction, tsa.runtime_id, recv_dict.get("runtime_id", "")
            )

            sdr_ids_for_term = [
                s.sdr_id if hasattr(s, "sdr_id") else s.get("sdr_id", "")
                for s in sdr_chain
                if term_id in (s.term_drift_map if hasattr(s, "term_drift_map")
                               else s.get("term_drift_map", {}))
            ]

            term_assessment[term_id] = TermAssessment(
                term_id=term_id,
                sdu=round(final_sdu, 4),
                drift_direction=drift_direction,
                status=status,
                originating_hash=orig_hash or None,
                receiving_hash=recv_hash or None,
                governing_interpretation=governing,
                sdr_ids_applied=sdr_ids_for_term,
            ).to_dict()

        all_sdus = [v["sdu"] for v in term_assessment.values()]
        aggregate_sdu = round(sum(all_sdus) / len(all_sdus), 4) if all_sdus else 0.0
        verdict = self._sdu_to_verdict(aggregate_sdu)
        confidence = round(max(0.0, 1.0 - aggregate_sdu), 4)

        now = datetime.now(timezone.utc).isoformat()
        rsa_id = f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}"

        core_fields: Dict[str, Any] = {
            "rsa_id": rsa_id,
            "tsa_id": tsa.tsa_id,
            "receipt_id": tsa.receipt_id,
            "originating_runtime_id": tsa.runtime_id,
            "receiving_runtime_id": self.runtime_id,
            "originating_spv_hash": tsa.spv_hash,
            "receiving_spv_hash": receiving_spv_hash,
            "assessed_at": now,
            "sdr_chain_traversed": sdr_ids_traversed,
            "term_assessment": term_assessment,
            "aggregate_sdu": aggregate_sdu,
            "dspp_verdict": verdict.value,
            "portability_confidence": confidence,
            "governing_posture": "MORE_RESTRICTIVE",
            "created_at": now,
        }

        content_hash = self._compute_hash(core_fields)
        pqc_sig, pqc_alg = self._sign(content_hash)

        rsa = RetroactiveSemanticAssessment(
            rsa_id=rsa_id,
            tsa_id=tsa.tsa_id,
            receipt_id=tsa.receipt_id,
            originating_runtime_id=tsa.runtime_id,
            receiving_runtime_id=self.runtime_id,
            originating_spv_hash=tsa.spv_hash,
            receiving_spv_hash=receiving_spv_hash,
            assessed_at=now,
            sdr_chain_traversed=sdr_ids_traversed,
            term_assessment=term_assessment,
            aggregate_sdu=aggregate_sdu,
            dspp_verdict=verdict.value,
            portability_confidence=confidence,
            governing_posture="MORE_RESTRICTIVE",
            content_hash=content_hash,
            pqc_signature=pqc_sig,
            pqc_algorithm=pqc_alg,
            created_at=now,
        )

        with self._lock:
            self._rsa_store[rsa_id] = rsa

        self._persist_rsa(rsa)
        logger.info(
            f"[ATF.DSPP] RSA computed — id={rsa_id} receipt={tsa.receipt_id} "
            f"verdict={verdict.value} sdu={aggregate_sdu:.4f} "
            f"confidence={confidence:.4f} signed={pqc_sig is not None}"
        )
        return rsa

    def assess_chain_portability(
        self,
        tsa_chain: List[TemporalSemanticAnchor],
        receiving_spv: Any,
        sdr_chain: Optional[List[SemanticDriftRecord]] = None,
    ) -> Dict[str, RetroactiveSemanticAssessment]:
        """
        Assess portability for an ordered chain of delegation receipts.

        DSPP-INV-006: If any receipt in the chain receives SEMANTICALLY_INCOMPATIBLE,
        all subsequent receipts in the chain are also marked SEMANTICALLY_INCOMPATIBLE
        without further computation.

        Args:
            tsa_chain       — ordered list of TSAs (parent first, leaf last)
            receiving_spv   — current SPV of the receiving domain
            sdr_chain       — SDR chain from originating runtime

        Returns:
            Dict[receipt_id, RetroactiveSemanticAssessment]
        """
        results: Dict[str, RetroactiveSemanticAssessment] = {}
        incompatible_from: Optional[int] = None

        for idx, tsa in enumerate(tsa_chain):
            if incompatible_from is not None:
                propagated = self._propagate_incompatible(tsa, receiving_spv, results)
                results[tsa.receipt_id] = propagated
                logger.info(
                    f"[ATF.DSPP] DSPP-INV-006: INCOMPATIBLE propagated to "
                    f"receipt={tsa.receipt_id} (chain position {idx})"
                )
                continue

            rsa = self.assess_portability(tsa, receiving_spv, sdr_chain)
            results[tsa.receipt_id] = rsa

            if rsa.is_incompatible():
                incompatible_from = idx
                logger.warning(
                    f"[ATF.DSPP] DSPP-INV-006: INCOMPATIBLE at chain position {idx} "
                    f"receipt={tsa.receipt_id} — propagating to all descendants"
                )

        return results

    def compute_sdu(
        self,
        term_a_entry: Dict[str, Any],
        term_b_entry: Dict[str, Any],
    ) -> Dict[str, float]:
        """
        Compute the Semantic Distance Unit (SDU) between two STR entries for the same term.

        Returns:
            Dict with keys: sdu, boundary_distance, scope_distance, regulatory_distance

        Algorithm (ADR-173 §SDU):
            boundary_distance  (weight 0.40): fraction of boundary_conditions that differ
            scope_distance     (weight 0.35): Jaccard distance of operational_scope sets
            regulatory_distance (weight 0.25): fraction of regulatory_anchors that differ

        DSPP-INV-007: Threshold constants are structural. Computation is deterministic.
        """
        if not term_a_entry and not term_b_entry:
            return {"sdu": 0.0, "boundary_distance": 0.0, "scope_distance": 0.0, "regulatory_distance": 0.0}

        if term_a_entry.get("content_hash") and term_b_entry.get("content_hash"):
            if term_a_entry["content_hash"] == term_b_entry["content_hash"]:
                return {"sdu": 0.0, "boundary_distance": 0.0, "scope_distance": 0.0, "regulatory_distance": 0.0}

        if not term_a_entry:
            return {"sdu": 1.0, "boundary_distance": 1.0, "scope_distance": 1.0, "regulatory_distance": 1.0}
        if not term_b_entry:
            return {"sdu": 1.0, "boundary_distance": 1.0, "scope_distance": 1.0, "regulatory_distance": 1.0}

        def_a = term_a_entry.get("definition", term_a_entry)
        def_b = term_b_entry.get("definition", term_b_entry)

        boundary_dist = self._boundary_distance(
            def_a.get("boundary_conditions", []),
            def_b.get("boundary_conditions", []),
        )

        scope_dist = self._scope_distance(
            term_a_entry.get("operational_scope", {}),
            term_b_entry.get("operational_scope", {}),
        )

        reg_dist = self._regulatory_distance(
            def_a.get("regulatory_anchors", []),
            def_b.get("regulatory_anchors", []),
        )

        sdu = round(
            boundary_dist * SDU_WEIGHT_BOUNDARY
            + scope_dist * SDU_WEIGHT_SCOPE
            + reg_dist * SDU_WEIGHT_REGULATORY,
            4,
        )

        return {
            "sdu": sdu,
            "boundary_distance": round(boundary_dist, 4),
            "scope_distance": round(scope_dist, 4),
            "regulatory_distance": round(reg_dist, 4),
        }

    def _boundary_distance(self, bc_a: List[str], bc_b: List[str]) -> float:
        if not bc_a and not bc_b:
            return 0.0
        if not bc_a or not bc_b:
            return 1.0
        a_set = {self._normalize_condition(c) for c in bc_a}
        b_set = {self._normalize_condition(c) for c in bc_b}
        intersection = len(a_set & b_set)
        union = len(a_set | b_set)
        return 1.0 - (intersection / union) if union > 0 else 0.0

    def _scope_distance(self, scope_a: Dict, scope_b: Dict) -> float:
        if not scope_a and not scope_b:
            return 0.0
        a_domains = set(scope_a.get("domains", []))
        b_domains = set(scope_b.get("domains", []))
        a_jurisdictions = set(scope_a.get("jurisdictions", []))
        b_jurisdictions = set(scope_b.get("jurisdictions", []))

        a_set = a_domains | a_jurisdictions
        b_set = b_domains | b_jurisdictions

        if not a_set and not b_set:
            return 0.0
        if not a_set or not b_set:
            return 0.5

        intersection = len(a_set & b_set)
        union = len(a_set | b_set)
        return 1.0 - (intersection / union) if union > 0 else 0.0

    def _regulatory_distance(self, reg_a: List[str], reg_b: List[str]) -> float:
        if not reg_a and not reg_b:
            return 0.0
        if not reg_a or not reg_b:
            return 0.5
        a_set = {r.strip().upper() for r in reg_a}
        b_set = {r.strip().upper() for r in reg_b}
        intersection = len(a_set & b_set)
        union = len(a_set | b_set)
        return 1.0 - (intersection / union) if union > 0 else 0.0

    def _normalize_condition(self, condition: str) -> str:
        import re
        return re.sub(r"\s+", " ", condition.strip().lower())

    def _compute_term_drift_map(
        self,
        prev_spv: Dict[str, Any],
        new_spv: Dict[str, Any],
    ) -> Dict[str, Any]:
        prev_terms = prev_spv.get("atf_core_term_set", {})
        new_terms = new_spv.get("atf_core_term_set", {})
        drift_map: Dict[str, Any] = {}

        for term_id in ATF_CORE_TERM_SET:
            prev_entry = prev_terms.get(term_id, {})
            new_entry = new_terms.get(term_id, {})
            sdu_result = self.compute_sdu(prev_entry, new_entry)
            drift_direction = self._infer_drift_direction_from_entries(prev_entry, new_entry)
            drift_map[term_id] = {
                "sdu": sdu_result["sdu"],
                "drift_direction": drift_direction,
                "boundary_delta": sdu_result["boundary_distance"],
                "scope_delta": sdu_result["scope_distance"],
                "regulatory_delta": sdu_result["regulatory_distance"],
            }

        return drift_map

    def _compute_governance_impact(self, term_drift_map: Dict[str, Any]) -> str:
        if not term_drift_map:
            return "PORTABLE"
        max_sdu = max(v.get("sdu", 0.0) for v in term_drift_map.values())
        return self._sdu_to_verdict_str(max_sdu)

    def _sdu_to_verdict(self, sdu: float) -> DSPPVerdict:
        if sdu < SDU_PORTABLE_THRESHOLD:
            return DSPPVerdict.SEMANTICALLY_PORTABLE
        if sdu < SDU_ACKNOWLEDGED_THRESHOLD:
            return DSPPVerdict.DRIFT_ACKNOWLEDGED
        if sdu < SDU_CRITICAL_THRESHOLD:
            return DSPPVerdict.DRIFT_CRITICAL
        return DSPPVerdict.SEMANTICALLY_INCOMPATIBLE

    def _sdu_to_verdict_str(self, sdu: float) -> str:
        return self._sdu_to_verdict(sdu).value.replace("SEMANTICALLY_", "").replace("DRIFT_", "")

    def _sdu_to_status(self, sdu: float) -> str:
        v = self._sdu_to_verdict(sdu)
        mapping = {
            DSPPVerdict.SEMANTICALLY_PORTABLE: "PORTABLE",
            DSPPVerdict.DRIFT_ACKNOWLEDGED: "ACKNOWLEDGED",
            DSPPVerdict.DRIFT_CRITICAL: "CRITICAL",
            DSPPVerdict.SEMANTICALLY_INCOMPATIBLE: "INCOMPATIBLE",
        }
        return mapping[v]

    def _infer_drift_direction(
        self,
        term_id: str,
        sdr_chain: List[Any],
        orig_hash: str,
        recv_hash: str,
    ) -> str:
        if orig_hash == recv_hash:
            return "NONE"
        for sdr in sdr_chain:
            tdm = sdr.term_drift_map if hasattr(sdr, "term_drift_map") else sdr.get("term_drift_map", {})
            if term_id in tdm:
                return tdm[term_id].get("drift_direction", "LATERAL")
        return "LATERAL"

    def _infer_drift_direction_from_entries(
        self, prev_entry: Dict, new_entry: Dict
    ) -> str:
        if not prev_entry and not new_entry:
            return "NONE"
        if not prev_entry:
            return "LATERAL"
        if not new_entry:
            return "LATERAL"
        prev_bc = set(prev_entry.get("definition", prev_entry).get("boundary_conditions", []))
        new_bc = set(new_entry.get("definition", new_entry).get("boundary_conditions", []))
        if new_bc > prev_bc:
            return "MORE_RESTRICTIVE"
        if prev_bc > new_bc:
            return "LESS_RESTRICTIVE"
        return "LATERAL"

    def _governing_interpretation(
        self, drift_direction: str, orig_runtime: str, recv_runtime: str
    ) -> str:
        if drift_direction == "LESS_RESTRICTIVE":
            return f"RECEIVING_RUNTIME:{recv_runtime} (MORE_RESTRICTIVE default — DSPP-INV-003)"
        return f"ORIGINATING_RUNTIME:{orig_runtime}"

    def _compute_sdu_from_hashes(
        self,
        term_id: str,
        orig_hash: str,
        recv_hash: str,
        orig_entries: Dict[str, Any],
        recv_entries: Dict[str, Any],
    ) -> float:
        if orig_hash and recv_hash and orig_hash == recv_hash:
            return 0.0
        orig_entry = orig_entries.get(term_id, {})
        recv_entry = recv_entries.get(term_id, {})
        if orig_entry or recv_entry:
            return self.compute_sdu(orig_entry, recv_entry)["sdu"]
        if orig_hash and recv_hash and orig_hash != recv_hash:
            return 0.20
        if orig_hash and not recv_hash:
            return 0.50
        if not orig_hash and recv_hash:
            return 0.50
        return 0.0

    def _sdu_from_sdr_chain(self, term_id: str, sdr_chain: List[Any]) -> float:
        max_sdu = 0.0
        for sdr in sdr_chain:
            tdm = sdr.term_drift_map if hasattr(sdr, "term_drift_map") else sdr.get("term_drift_map", {})
            if term_id in tdm:
                max_sdu = max(max_sdu, tdm[term_id].get("sdu", 0.0))
        return max_sdu

    def _propagate_incompatible(
        self,
        tsa: TemporalSemanticAnchor,
        receiving_spv: Any,
        existing_results: Dict[str, RetroactiveSemanticAssessment],
    ) -> RetroactiveSemanticAssessment:
        recv_dict = receiving_spv if isinstance(receiving_spv, dict) else receiving_spv.to_dict()
        receiving_spv_hash = recv_dict.get("spv_hash", "")
        now = datetime.now(timezone.utc).isoformat()
        rsa_id = f"OMNIX-RSA-{uuid.uuid4().hex[:16].upper()}"

        term_assessment = {}
        for term_id in ATF_CORE_TERM_SET:
            term_assessment[term_id] = TermAssessment(
                term_id=term_id,
                sdu=1.0,
                drift_direction="LATERAL",
                status="INCOMPATIBLE",
                originating_hash=tsa.term_hashes.get(term_id),
                receiving_hash=None,
                governing_interpretation="PROPAGATED_FROM_ANCESTOR:DSPP-INV-006",
                sdr_ids_applied=[],
            ).to_dict()

        core_fields: Dict[str, Any] = {
            "rsa_id": rsa_id,
            "tsa_id": tsa.tsa_id,
            "receipt_id": tsa.receipt_id,
            "originating_runtime_id": tsa.runtime_id,
            "receiving_runtime_id": self.runtime_id,
            "originating_spv_hash": tsa.spv_hash,
            "receiving_spv_hash": receiving_spv_hash,
            "assessed_at": now,
            "sdr_chain_traversed": ["PROPAGATED_DSPP_INV_006"],
            "term_assessment": term_assessment,
            "aggregate_sdu": 1.0,
            "dspp_verdict": DSPPVerdict.SEMANTICALLY_INCOMPATIBLE.value,
            "portability_confidence": 0.0,
            "governing_posture": "MORE_RESTRICTIVE",
            "created_at": now,
        }

        content_hash = self._compute_hash(core_fields)
        pqc_sig, pqc_alg = self._sign(content_hash)

        return RetroactiveSemanticAssessment(
            rsa_id=rsa_id,
            tsa_id=tsa.tsa_id,
            receipt_id=tsa.receipt_id,
            originating_runtime_id=tsa.runtime_id,
            receiving_runtime_id=self.runtime_id,
            originating_spv_hash=tsa.spv_hash,
            receiving_spv_hash=receiving_spv_hash,
            assessed_at=now,
            sdr_chain_traversed=["PROPAGATED_DSPP_INV_006"],
            term_assessment=term_assessment,
            aggregate_sdu=1.0,
            dspp_verdict=DSPPVerdict.SEMANTICALLY_INCOMPATIBLE.value,
            portability_confidence=0.0,
            governing_posture="MORE_RESTRICTIVE",
            content_hash=content_hash,
            pqc_signature=pqc_sig,
            pqc_algorithm=pqc_alg,
            created_at=now,
        )

    def verify_tsa(self, tsa: TemporalSemanticAnchor) -> Dict[str, Any]:
        core_fields = {k: v for k, v in tsa.to_dict().items()
                       if k not in {"content_hash", "pqc_signature", "pqc_algorithm"}}
        expected = self._compute_hash(core_fields)
        hash_valid = tsa.content_hash == expected

        inv001 = tsa.anchored_at <= tsa.created_at
        inv004 = all(
            k in core_fields for k in ["spv_hash", "spv_version", "spv_generated_at"]
        )

        return {
            "tsa_id": tsa.tsa_id,
            "hash_valid": hash_valid,
            "DSPP-INV-001": inv001,
            "DSPP-INV-004": inv004,
            "is_signed": tsa.is_signed(),
            "verified": hash_valid and inv001 and inv004,
        }

    def verify_sdr(self, sdr: SemanticDriftRecord) -> Dict[str, Any]:
        core_fields = {k: v for k, v in sdr.to_dict().items()
                       if k not in {"content_hash", "pqc_signature", "pqc_algorithm"}}
        expected = self._compute_hash(core_fields)
        hash_valid = sdr.content_hash == expected

        inv002 = sdr.previous_spv_hash != sdr.new_spv_hash
        max_sdu = sdr.max_sdu()

        return {
            "sdr_id": sdr.sdr_id,
            "hash_valid": hash_valid,
            "DSPP-INV-002": inv002,
            "is_signed": sdr.is_signed(),
            "max_sdu": max_sdu,
            "governance_impact": sdr.governance_impact,
            "verified": hash_valid and inv002,
        }

    def get_sdr_chain(
        self, origin_spv_hash: str, max_depth: int = 20
    ) -> List[SemanticDriftRecord]:
        chain = []
        current_hash = origin_spv_hash
        visited = set()
        depth = 0

        with self._lock:
            while depth < max_depth:
                key = f"{self.runtime_id}::{current_hash}"
                sdr_id = self._sdr_by_prev_hash.get(key)
                if not sdr_id or sdr_id in visited:
                    break
                sdr = self._sdr_store.get(sdr_id)
                if not sdr:
                    break
                chain.append(sdr)
                visited.add(sdr_id)
                current_hash = sdr.new_spv_hash
                depth += 1

        return chain

    def _persist_tsa(self, tsa: TemporalSemanticAnchor) -> None:
        if not self._db_url:
            return
        conn = self._get_conn()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO atf_temporal_semantic_anchors
                        (tsa_id, receipt_id, receipt_type, runtime_id, spv_id, spv_hash,
                         spv_version, spv_generated_at, anchored_at, term_hashes,
                         content_hash, pqc_signature, pqc_algorithm, created_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (tsa_id) DO NOTHING
                        """,
                        (
                            tsa.tsa_id, tsa.receipt_id, tsa.receipt_type, tsa.runtime_id,
                            tsa.spv_id, tsa.spv_hash, tsa.spv_version, tsa.spv_generated_at,
                            tsa.anchored_at, json.dumps(tsa.term_hashes),
                            tsa.content_hash, tsa.pqc_signature, tsa.pqc_algorithm, tsa.created_at,
                        ),
                    )
        except Exception as exc:
            logger.warning(f"[ATF.DSPP] persist_tsa failed: {exc}")
        finally:
            conn.close()

    def _persist_sdr(self, sdr: SemanticDriftRecord) -> None:
        if not self._db_url:
            return
        conn = self._get_conn()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO atf_semantic_drift_records
                        (sdr_id, runtime_id, previous_spv_id, previous_spv_hash, new_spv_id,
                         new_spv_hash, effective_from, drift_reason, drift_category,
                         term_drift_map, governance_impact, regulatory_anchors,
                         content_hash, pqc_signature, pqc_algorithm, created_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (sdr_id) DO NOTHING
                        """,
                        (
                            sdr.sdr_id, sdr.runtime_id, sdr.previous_spv_id, sdr.previous_spv_hash,
                            sdr.new_spv_id, sdr.new_spv_hash, sdr.effective_from, sdr.drift_reason,
                            sdr.drift_category, json.dumps(sdr.term_drift_map), sdr.governance_impact,
                            json.dumps(sdr.regulatory_anchors), sdr.content_hash,
                            sdr.pqc_signature, sdr.pqc_algorithm, sdr.created_at,
                        ),
                    )
        except Exception as exc:
            logger.warning(f"[ATF.DSPP] persist_sdr failed: {exc}")
        finally:
            conn.close()

    def _persist_rsa(self, rsa: RetroactiveSemanticAssessment) -> None:
        if not self._db_url:
            return
        conn = self._get_conn()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO atf_retroactive_semantic_assessments
                        (rsa_id, tsa_id, receipt_id, originating_runtime_id,
                         receiving_runtime_id, originating_spv_hash, receiving_spv_hash,
                         assessed_at, sdr_chain_traversed, term_assessment, aggregate_sdu,
                         dspp_verdict, portability_confidence, governing_posture,
                         content_hash, pqc_signature, pqc_algorithm, created_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (tsa_id, receiving_runtime_id, receiving_spv_hash) DO NOTHING
                        """,
                        (
                            rsa.rsa_id, rsa.tsa_id, rsa.receipt_id,
                            rsa.originating_runtime_id, rsa.receiving_runtime_id,
                            rsa.originating_spv_hash, rsa.receiving_spv_hash,
                            rsa.assessed_at, json.dumps(rsa.sdr_chain_traversed),
                            json.dumps(rsa.term_assessment), rsa.aggregate_sdu,
                            rsa.dspp_verdict, rsa.portability_confidence,
                            rsa.governing_posture, rsa.content_hash,
                            rsa.pqc_signature, rsa.pqc_algorithm, rsa.created_at,
                        ),
                    )
        except Exception as exc:
            logger.warning(f"[ATF.DSPP] persist_rsa failed: {exc}")
        finally:
            conn.close()
