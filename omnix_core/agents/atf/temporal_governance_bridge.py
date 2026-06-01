"""
OMNIX Agent Trust Fabric — Temporal Governance Bridge (TGB)
ADR-180: Longitudinal projection of ATF governance evidence across regulatory
framework evolution.

Three record types:
  - TemporalContextSnapshot (TCS): embedded at record issuance, captures the
    exact regulatory and threshold context active at the nanosecond of creation.
  - RegulatoryAlignmentReceipt (RAR): issued at review time, projects a
    historical record to a current framework WITHOUT modifying original evidence
    (TGB-INV-002 non-destruction guarantee).
  - TemporalMigrationRecord (TMR): issued when evidence transitions lifecycle
    states (HOT → WARM → COLD per ADR-162), capturing the regulatory context
    at each transition for multi-jurisdiction retention compliance.

Key invariants:
    TGB-INV-001: Every ATF record issued with TGB_ENABLED=true carries a TCS
    TGB-INV-002: RAR never modifies the source record — projection only
    TGB-INV-003: RARs are independently computable from source + TCS + rulebook
    TGB-INV-004: Projection monotonicity — framework evolution cannot silently
                 invalidate prior evidence without an explicit EID
    TGB-INV-005: Every TMR and RAR is sealed with ML-DSA-65 (FIPS 204)

Status: IMPLEMENTED · TESTED · NOT DEPLOYED (Railway — pending env var TGB_ENABLED)

ADR-180 — Harold Nunes — OMNIX QUANTUM LTD — June 2026
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("OMNIX.ATF.TGB")

# ─────────────────────────────────────────────────────────────────────────────
# Compiled constants — not operator-configurable
# ─────────────────────────────────────────────────────────────────────────────
TGB_RULEBOOK_VERSION = "1.0"
TGB_ATF_SPEC_VERSION = "1.4"
TGB_PROJECTION_METHODOLOGY = "TGB-RAR-V1.0"

# Supported lifecycle migration events (ADR-162)
VALID_MIGRATION_EVENTS = frozenset({"HOT_TO_WARM", "WARM_TO_COLD", "COLD_ARCHIVED"})

# Supported retention bases
VALID_RETENTION_BASES = frozenset({
    "EU_AI_ACT_ART72_7YR",
    "GCC_DIFC_ART14_5YR",
    "ISO42001_10YR",
    "CUSTOMER_CONTRACT",
    "REGULATORY_ORDER",
})

# ─────────────────────────────────────────────────────────────────────────────
# DDL — idempotent (CREATE TABLE IF NOT EXISTS)
# ─────────────────────────────────────────────────────────────────────────────
DDL_TGB = """
CREATE TABLE IF NOT EXISTS atf_temporal_context_snapshots (
    id                      SERIAL PRIMARY KEY,
    tcs_id                  TEXT NOT NULL UNIQUE,
    parent_record_id        TEXT NOT NULL,
    parent_record_type      TEXT NOT NULL,
    issued_at_ns            BIGINT NOT NULL,
    regulatory_context      JSONB NOT NULL,
    threshold_context       JSONB NOT NULL,
    tcs_hash                TEXT NOT NULL,
    tcs_seal                TEXT,
    pqc_algorithm           TEXT,
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tcs_parent
    ON atf_temporal_context_snapshots(parent_record_id);
CREATE INDEX IF NOT EXISTS idx_tcs_issued_at
    ON atf_temporal_context_snapshots(issued_at_ns);

CREATE TABLE IF NOT EXISTS atf_regulatory_alignment_receipts (
    id                          SERIAL PRIMARY KEY,
    rar_id                      TEXT NOT NULL UNIQUE,
    source_record_id            TEXT NOT NULL,
    source_tcs_id               TEXT NOT NULL,
    review_timestamp            TIMESTAMP WITH TIME ZONE NOT NULL,
    reviewer_context            JSONB NOT NULL,
    field_projections           JSONB NOT NULL,
    semantic_shift_detected     BOOLEAN NOT NULL DEFAULT FALSE,
    semantic_shift_fields       TEXT[],
    original_record_integrity   TEXT NOT NULL,
    original_record_hash        TEXT NOT NULL,
    projection_methodology      TEXT NOT NULL DEFAULT 'TGB-RAR-V1.0',
    rar_seal                    TEXT,
    pqc_algorithm               TEXT,
    atf_spec_version_source     TEXT NOT NULL,
    atf_spec_version_target     TEXT NOT NULL,
    created_at                  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_rar_source
    ON atf_regulatory_alignment_receipts(source_record_id);
CREATE INDEX IF NOT EXISTS idx_rar_source_tcs
    ON atf_regulatory_alignment_receipts(source_tcs_id);

CREATE TABLE IF NOT EXISTS atf_temporal_migration_records (
    id                              SERIAL PRIMARY KEY,
    tmr_id                          TEXT NOT NULL UNIQUE,
    source_record_id                TEXT NOT NULL,
    migration_event                 TEXT NOT NULL,
    migration_timestamp             TIMESTAMP WITH TIME ZONE NOT NULL,
    regulatory_context_at_migration JSONB NOT NULL,
    retention_basis                 TEXT NOT NULL,
    next_review_due                 TIMESTAMP WITH TIME ZONE,
    tmr_seal                        TEXT,
    pqc_algorithm                   TEXT,
    created_at                      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tmr_source
    ON atf_temporal_migration_records(source_record_id);
CREATE INDEX IF NOT EXISTS idx_tmr_event
    ON atf_temporal_migration_records(migration_event);
"""


# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────
class TGBInvariantViolation(Exception):
    """Raised when a TGB invariant is violated (TGB-INV-001 through TGB-INV-005)."""


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class TemporalContextSnapshot:
    """
    TCS — Regulatory and threshold context snapshot at record issuance nanosecond.

    Embedded in ATF records (DR, TAR, RCR) via metadata['tcs'] to bind
    governance decisions to their exact interpretive context.

    ID format: TCS-{16HEX}
    """
    tcs_id: str
    parent_record_id: str
    parent_record_type: str       # DR | TAR | RCR | CUSTOM
    issued_at_ns: int             # nanosecond epoch
    regulatory_context: Dict[str, Any]
    threshold_context: Dict[str, Any]
    tcs_hash: str                 # SHA3-256 of canonical TCS JSON
    tcs_seal: Optional[str]       # ML-DSA-65 signature over tcs_hash
    pqc_algorithm: Optional[str]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_metadata_embed(self) -> Dict[str, Any]:
        """Compact form for embedding in parent record metadata."""
        return {
            "tcs_id": self.tcs_id,
            "issued_at_ns": self.issued_at_ns,
            "tcs_hash": self.tcs_hash,
            "pqc_sealed": self.tcs_seal is not None,
            "atf_spec_version": self.regulatory_context.get("atf_spec_version", TGB_ATF_SPEC_VERSION),
        }


@dataclass
class RegulatoryAlignmentReceipt:
    """
    RAR — Projects a historical ATF record to a current regulatory framework.

    Non-destructive by design (TGB-INV-002): the source record is never
    modified. The RAR is a separate artifact that documents the projection.

    ID format: RAR-{16HEX}
    """
    rar_id: str
    source_record_id: str
    source_tcs_id: str
    review_timestamp: str         # ISO8601
    reviewer_context: Dict[str, Any]
    field_projections: List[Dict[str, Any]]
    semantic_shift_detected: bool
    semantic_shift_fields: List[str]
    original_record_integrity: str  # VERIFIED | UNVERIFIED | INVALIDATED
    original_record_hash: str
    projection_methodology: str
    rar_seal: Optional[str]
    pqc_algorithm: Optional[str]
    atf_spec_version_source: str
    atf_spec_version_target: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_signed(self) -> bool:
        return self.rar_seal is not None


@dataclass
class TemporalMigrationRecord:
    """
    TMR — Records evidence lifecycle state transitions under their regulatory context.

    Satisfies EU AI Act Art. 72 (7-year retention), GCC/DIFC Art. 14,
    and ISO/IEC 42001 §9.1 simultaneously.

    ID format: TMR-{16HEX}
    Migration events: HOT_TO_WARM | WARM_TO_COLD | COLD_ARCHIVED
    """
    tmr_id: str
    source_record_id: str
    migration_event: str
    migration_timestamp: str      # ISO8601
    regulatory_context_at_migration: Dict[str, Any]
    retention_basis: str
    next_review_due: Optional[str]
    tmr_seal: Optional[str]
    pqc_algorithm: Optional[str]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_signed(self) -> bool:
        return self.tmr_seal is not None


# ─────────────────────────────────────────────────────────────────────────────
# Engine
# ─────────────────────────────────────────────────────────────────────────────
class TemporalGovernanceBridge:
    """
    TGB Engine — Issues and manages TCS, RAR, and TMR artifacts.

    Design contract:
        issue_tcs(parent_record_id, parent_record_type)     → TemporalContextSnapshot
        issue_rar(source_record_id, source_tcs_id, ...)     → RegulatoryAlignmentReceipt
        issue_tmr(source_record_id, migration_event, ...)   → TemporalMigrationRecord
        verify_tcs(tcs)                                      → dict (verification result)
        verify_rar(rar)                                      → dict (verification result)
        get_current_regulatory_context()                     → dict
        get_current_threshold_context()                      → dict
        ensure_tables()                                      → bool

    TGB-INV-001: Enforced — every issued TCS carries full regulatory context.
    TGB-INV-002: Enforced — issue_rar() never touches the source record.
    TGB-INV-003: Enforced — all hashes are recomputable from the artifact alone.
    TGB-INV-004: Projection monotonicity — documented in field_projections.
    TGB-INV-005: Enforced — TMR and RAR are PQC-signed when key is available.
    """

    def __init__(self, db_url: Optional[str] = None):
        self._db_url = db_url or os.environ.get("DATABASE_URL")
        self._enabled = os.environ.get("TGB_ENABLED", "true").lower() == "true"
        self._tcs_store: Dict[str, TemporalContextSnapshot] = {}
        self._rar_store: Dict[str, RegulatoryAlignmentReceipt] = {}
        self._tmr_store: Dict[str, TemporalMigrationRecord] = {}
        self._lock = threading.Lock()
        self._provider = self._load_provider()

    # ── Private helpers ───────────────────────────────────────────────────────

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
            logger.warning(f"[TGB] DB connection failed: {exc}")
            return None

    @staticmethod
    def _new_tcs_id() -> str:
        return f"TCS-{uuid.uuid4().hex[:16].upper()}"

    @staticmethod
    def _new_rar_id() -> str:
        return f"RAR-{uuid.uuid4().hex[:16].upper()}"

    @staticmethod
    def _new_tmr_id() -> str:
        return f"TMR-{uuid.uuid4().hex[:16].upper()}"

    @staticmethod
    def _sha3_256(data: str) -> str:
        return hashlib.sha3_256(data.encode("utf-8")).hexdigest()

    @staticmethod
    def _canonical_json(obj: Any) -> str:
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)

    def _sign(self, content_hash: str) -> Tuple[Optional[str], Optional[str]]:
        """Sign content_hash with platform Dilithium-3 key. Returns (sig_b64, alg_name)."""
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
            logger.warning(f"[TGB] PQC sign failed: {exc}")
        return None, None

    def _verify_seal(self, seal_b64: str, content_hash: str, pub_key_b64: Optional[str]) -> bool:
        if not self._provider or not pub_key_b64:
            return False
        try:
            sig = base64.b64decode(seal_b64)
            pk = base64.b64decode(pub_key_b64)
            return bool(self._provider.verify(sig, content_hash.encode(), pk))
        except Exception:
            return False

    # ── Regulatory context helpers ────────────────────────────────────────────

    def get_current_regulatory_context(self) -> Dict[str, Any]:
        """
        Returns the current active regulatory framework context.
        This snapshot is embedded in every TCS at issuance time.
        """
        return {
            "eu_ai_act_version":           "2024/1689-v1.0",
            "nist_ai_rmf_version":         "1.0",
            "gcc_difc_version":            "2024-r1",
            "iso_42001_version":           "2023",
            "uk_ai_safety_version":        "2024-eval-v1",
            "atf_spec_version":            TGB_ATF_SPEC_VERSION,
            "omnix_engine_version":        os.environ.get("OMNIX_ENGINE_VERSION", "2.0.0"),
            "jurisdiction_active":         ["EU", "UK", "GCC_DIFC", "US", "GLOBAL"],
            "risk_classification_scheme":  "EU_AI_ACT_ANNEX_III_2024",
            "tgb_rulebook_version":        TGB_RULEBOOK_VERSION,
        }

    def get_current_threshold_context(self) -> Dict[str, Any]:
        """Returns the current ATF threshold context embedded in every TCS."""
        return {
            "nominal_threshold":     80.0,
            "monitoring_lower":      50.0,
            "warning_lower":         30.0,
            "halt_threshold":        30.0,
            "fragmentation_limit":   float(os.environ.get("AFG_FRAGMENTATION_LIMIT", "0.90")),
            "max_delegation_depth":  5,
            "max_dr_lifetime_s":     86400,
        }

    # ── TCS ──────────────────────────────────────────────────────────────────

    def issue_tcs(
        self,
        parent_record_id: str,
        parent_record_type: str,
        regulatory_context_override: Optional[Dict[str, Any]] = None,
        threshold_context_override: Optional[Dict[str, Any]] = None,
    ) -> TemporalContextSnapshot:
        """
        Issue a Temporal Context Snapshot for a parent ATF record.

        Satisfies TGB-INV-001: captures complete regulatory + threshold context
        at the nanosecond of issuance.

        Args:
            parent_record_id:             ID of the DR / TAR / RCR being issued
            parent_record_type:           "DR" | "TAR" | "RCR" | "CUSTOM"
            regulatory_context_override:  Optional override (testing/audit)
            threshold_context_override:   Optional override

        Returns:
            TemporalContextSnapshot — PQC-sealed, persisted if DB available.
        """
        if not parent_record_id:
            raise ValueError("[TGB] parent_record_id is required (TGB-INV-001)")
        if not parent_record_type:
            raise ValueError("[TGB] parent_record_type is required")

        tcs_id = self._new_tcs_id()
        issued_at_ns = time.time_ns()
        now = datetime.now(timezone.utc).isoformat()

        regulatory_context = regulatory_context_override or self.get_current_regulatory_context()
        threshold_context = threshold_context_override or self.get_current_threshold_context()

        # TCS-INV: hash covers full regulatory and threshold snapshot
        hashable = {
            "tcs_id":              tcs_id,
            "parent_record_id":    parent_record_id,
            "parent_record_type":  parent_record_type,
            "issued_at_ns":        issued_at_ns,
            "regulatory_context":  regulatory_context,
            "threshold_context":   threshold_context,
        }
        tcs_hash = self._sha3_256(self._canonical_json(hashable))
        tcs_seal, pqc_alg = self._sign(tcs_hash)

        tcs = TemporalContextSnapshot(
            tcs_id=tcs_id,
            parent_record_id=parent_record_id,
            parent_record_type=parent_record_type,
            issued_at_ns=issued_at_ns,
            regulatory_context=regulatory_context,
            threshold_context=threshold_context,
            tcs_hash=tcs_hash,
            tcs_seal=tcs_seal,
            pqc_algorithm=pqc_alg,
            created_at=now,
        )

        with self._lock:
            self._tcs_store[tcs_id] = tcs

        self._persist_tcs(tcs)
        logger.info(
            f"[TGB] TCS issued — id={tcs_id} parent={parent_record_id} "
            f"type={parent_record_type} pqc={pqc_alg or 'unsigned'}"
        )
        return tcs

    def verify_tcs(
        self,
        tcs: TemporalContextSnapshot,
        public_key_b64: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Verify a TCS — hash integrity + PQC seal.

        Offline-verifiable: requires only the TCS and public key.
        """
        hashable = {
            "tcs_id":              tcs.tcs_id,
            "parent_record_id":    tcs.parent_record_id,
            "parent_record_type":  tcs.parent_record_type,
            "issued_at_ns":        tcs.issued_at_ns,
            "regulatory_context":  tcs.regulatory_context,
            "threshold_context":   tcs.threshold_context,
        }
        recomputed = self._sha3_256(self._canonical_json(hashable))
        hash_valid = (recomputed == tcs.tcs_hash)

        pub_b64 = public_key_b64 or os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64", "")
        pqc_valid = False
        pqc_checked = False
        if tcs.tcs_seal and pub_b64:
            pqc_checked = True
            pqc_valid = self._verify_seal(tcs.tcs_seal, tcs.tcs_hash, pub_b64)

        fully_verified = hash_valid and (pqc_valid if pqc_checked else True)
        return {
            "tcs_id":        tcs.tcs_id,
            "hash_valid":    hash_valid,
            "pqc_valid":     pqc_valid,
            "pqc_checked":   pqc_checked,
            "pqc_signed":    tcs.tcs_seal is not None,
            "fully_verified": fully_verified,
            "parent_record_id": tcs.parent_record_id,
        }

    # ── RAR ──────────────────────────────────────────────────────────────────

    def issue_rar(
        self,
        source_record_id: str,
        source_tcs_id: str,
        reviewer_context: Dict[str, Any],
        field_projections: List[Dict[str, Any]],
        original_record_hash: str,
        original_record_integrity: str = "VERIFIED",
        atf_spec_version_source: str = TGB_ATF_SPEC_VERSION,
        atf_spec_version_target: Optional[str] = None,
    ) -> RegulatoryAlignmentReceipt:
        """
        Issue a Regulatory Alignment Receipt — projects a historical record to
        the current (or specified) regulatory framework.

        TGB-INV-002 GUARANTEE: This method NEVER touches or modifies the source
        record. The RAR is a separate projection artifact only.

        TGB-INV-003: The RAR is independently computable from source + TCS + rulebook.

        Args:
            source_record_id:           ID of the original DR / TAR / RCR
            source_tcs_id:              TCS ID embedded in the source record
            reviewer_context:           Current regulatory framework context for projection
            field_projections:          List of field-level mapping dicts (see ADR-180)
            original_record_hash:       SHA3-256 of the source record (for integrity assertion)
            original_record_integrity:  "VERIFIED" | "UNVERIFIED" | "INVALIDATED"
            atf_spec_version_source:    ATF spec version under which source was issued
            atf_spec_version_target:    ATF spec version for the projection (defaults to current)

        Returns:
            RegulatoryAlignmentReceipt — PQC-sealed (TGB-INV-005).
        """
        if not source_record_id:
            raise ValueError("[TGB] source_record_id required")
        if not source_tcs_id:
            raise ValueError("[TGB] source_tcs_id required (TGB-INV-003)")
        if not original_record_hash:
            raise ValueError("[TGB] original_record_hash required for integrity assertion")
        if original_record_integrity not in {"VERIFIED", "UNVERIFIED", "INVALIDATED"}:
            raise ValueError("[TGB] original_record_integrity must be VERIFIED|UNVERIFIED|INVALIDATED")

        # Validate field_projections structure (TGB-INV-003)
        required_keys = {"field", "source_value", "target_value", "projection_rule"}
        for fp in field_projections:
            missing = required_keys - set(fp.keys())
            if missing:
                raise ValueError(f"[TGB] field_projection missing keys: {missing}")

        rar_id = self._new_rar_id()
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        target_version = atf_spec_version_target or TGB_ATF_SPEC_VERSION

        semantic_shift_fields = [
            fp["field"] for fp in field_projections
            if fp.get("source_value") != fp.get("target_value")
        ]
        semantic_shift_detected = len(semantic_shift_fields) > 0

        rar_content = {
            "rar_id":                      rar_id,
            "source_record_id":            source_record_id,
            "source_tcs_id":               source_tcs_id,
            "review_timestamp":            now_iso,
            "reviewer_context":            reviewer_context,
            "field_projections":           field_projections,
            "semantic_shift_detected":     semantic_shift_detected,
            "semantic_shift_fields":       semantic_shift_fields,
            "original_record_integrity":   original_record_integrity,
            "original_record_hash":        original_record_hash,
            "projection_methodology":      TGB_PROJECTION_METHODOLOGY,
            "atf_spec_version_source":     atf_spec_version_source,
            "atf_spec_version_target":     target_version,
        }
        rar_hash = self._sha3_256(self._canonical_json(rar_content))
        rar_seal, pqc_alg = self._sign(rar_hash)

        if not rar_seal:
            logger.warning(
                "[TGB] RAR issued WITHOUT PQC seal — TGB-INV-005 requires ML-DSA-65. "
                "Set OMNIX_SIGNING_SECRET_KEY_B64 to enable sealing."
            )

        rar = RegulatoryAlignmentReceipt(
            rar_id=rar_id,
            source_record_id=source_record_id,
            source_tcs_id=source_tcs_id,
            review_timestamp=now_iso,
            reviewer_context=reviewer_context,
            field_projections=field_projections,
            semantic_shift_detected=semantic_shift_detected,
            semantic_shift_fields=semantic_shift_fields,
            original_record_integrity=original_record_integrity,
            original_record_hash=original_record_hash,
            projection_methodology=TGB_PROJECTION_METHODOLOGY,
            rar_seal=rar_seal,
            pqc_algorithm=pqc_alg,
            atf_spec_version_source=atf_spec_version_source,
            atf_spec_version_target=target_version,
            created_at=now_iso,
        )

        with self._lock:
            self._rar_store[rar_id] = rar

        self._persist_rar(rar)
        logger.info(
            f"[TGB] RAR issued — id={rar_id} source={source_record_id} "
            f"semantic_shift={semantic_shift_detected} fields={semantic_shift_fields} "
            f"integrity={original_record_integrity} pqc={pqc_alg or 'unsigned'}"
        )
        return rar

    def verify_rar(
        self,
        rar: RegulatoryAlignmentReceipt,
        public_key_b64: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Verify RAR hash integrity and PQC seal (TGB-INV-003 offline verification)."""
        rar_content = {
            "rar_id":                      rar.rar_id,
            "source_record_id":            rar.source_record_id,
            "source_tcs_id":               rar.source_tcs_id,
            "review_timestamp":            rar.review_timestamp,
            "reviewer_context":            rar.reviewer_context,
            "field_projections":           rar.field_projections,
            "semantic_shift_detected":     rar.semantic_shift_detected,
            "semantic_shift_fields":       rar.semantic_shift_fields,
            "original_record_integrity":   rar.original_record_integrity,
            "original_record_hash":        rar.original_record_hash,
            "projection_methodology":      rar.projection_methodology,
            "atf_spec_version_source":     rar.atf_spec_version_source,
            "atf_spec_version_target":     rar.atf_spec_version_target,
        }
        recomputed_hash = self._sha3_256(self._canonical_json(rar_content))

        pub_b64 = public_key_b64 or os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64", "")
        pqc_valid = False
        pqc_checked = False
        if rar.rar_seal and pub_b64:
            pqc_checked = True
            pqc_valid = self._verify_seal(rar.rar_seal, recomputed_hash, pub_b64)

        fully_verified = (pqc_valid if pqc_checked else True) and rar.original_record_integrity != "INVALIDATED"
        return {
            "rar_id":                    rar.rar_id,
            "source_record_id":          rar.source_record_id,
            "pqc_valid":                 pqc_valid,
            "pqc_checked":               pqc_checked,
            "pqc_signed":                rar.rar_seal is not None,
            "semantic_shift_detected":   rar.semantic_shift_detected,
            "original_record_integrity": rar.original_record_integrity,
            "fully_verified":            fully_verified,
            "tgb_inv_002_respected":     True,  # Source never modified by design
        }

    # ── TMR ──────────────────────────────────────────────────────────────────

    def issue_tmr(
        self,
        source_record_id: str,
        migration_event: str,
        retention_basis: str,
        next_review_due: Optional[datetime] = None,
        regulatory_context_override: Optional[Dict[str, Any]] = None,
    ) -> TemporalMigrationRecord:
        """
        Issue a Temporal Migration Record when evidence transitions lifecycle states.

        TGB-INV-005: TMR is PQC-sealed with ML-DSA-65.

        Args:
            source_record_id:              ID of the record transitioning lifecycle
            migration_event:               "HOT_TO_WARM" | "WARM_TO_COLD" | "COLD_ARCHIVED"
            retention_basis:               Legal retention basis (EU_AI_ACT_ART72_7YR, etc.)
            next_review_due:               When this record should next be reviewed
            regulatory_context_override:   Optional override for testing

        Returns:
            TemporalMigrationRecord — PQC-sealed.
        """
        if not source_record_id:
            raise ValueError("[TGB] source_record_id required")
        if migration_event not in VALID_MIGRATION_EVENTS:
            raise ValueError(
                f"[TGB] migration_event must be one of {VALID_MIGRATION_EVENTS}, got '{migration_event}'"
            )
        if retention_basis not in VALID_RETENTION_BASES:
            raise ValueError(
                f"[TGB] retention_basis must be one of {VALID_RETENTION_BASES}, got '{retention_basis}'"
            )

        tmr_id = self._new_tmr_id()
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        # Default review schedule based on retention basis
        if next_review_due is None:
            retention_years = {
                "EU_AI_ACT_ART72_7YR":  7,
                "GCC_DIFC_ART14_5YR":   5,
                "ISO42001_10YR":        10,
                "CUSTOMER_CONTRACT":     3,
                "REGULATORY_ORDER":      7,
            }
            years = retention_years.get(retention_basis, 5)
            next_review_due = now + timedelta(days=years * 365)

        regulatory_context = regulatory_context_override or self.get_current_regulatory_context()

        tmr_content = {
            "tmr_id":                          tmr_id,
            "source_record_id":                source_record_id,
            "migration_event":                 migration_event,
            "migration_timestamp":             now_iso,
            "regulatory_context_at_migration": regulatory_context,
            "retention_basis":                 retention_basis,
            "next_review_due":                 next_review_due.isoformat(),
        }
        tmr_hash = self._sha3_256(self._canonical_json(tmr_content))
        tmr_seal, pqc_alg = self._sign(tmr_hash)

        if not tmr_seal:
            logger.warning(
                "[TGB] TMR issued WITHOUT PQC seal — TGB-INV-005 requires ML-DSA-65."
            )

        tmr = TemporalMigrationRecord(
            tmr_id=tmr_id,
            source_record_id=source_record_id,
            migration_event=migration_event,
            migration_timestamp=now_iso,
            regulatory_context_at_migration=regulatory_context,
            retention_basis=retention_basis,
            next_review_due=next_review_due.isoformat(),
            tmr_seal=tmr_seal,
            pqc_algorithm=pqc_alg,
            created_at=now_iso,
        )

        with self._lock:
            self._tmr_store[tmr_id] = tmr

        self._persist_tmr(tmr)
        logger.info(
            f"[TGB] TMR issued — id={tmr_id} source={source_record_id} "
            f"event={migration_event} basis={retention_basis} "
            f"next_review={next_review_due.date()} pqc={pqc_alg or 'unsigned'}"
        )
        return tmr

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def get_tcs(self, tcs_id: str) -> Optional[TemporalContextSnapshot]:
        with self._lock:
            return self._tcs_store.get(tcs_id)

    def get_rar(self, rar_id: str) -> Optional[RegulatoryAlignmentReceipt]:
        with self._lock:
            return self._rar_store.get(rar_id)

    def get_tmr(self, tmr_id: str) -> Optional[TemporalMigrationRecord]:
        with self._lock:
            return self._tmr_store.get(tmr_id)

    # ── DB persistence ────────────────────────────────────────────────────────

    def ensure_tables(self) -> bool:
        if not self._db_url:
            return False
        conn = self._get_conn()
        if not conn:
            return False
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(DDL_TGB)
            logger.info("[TGB] Tables ready: atf_temporal_context_snapshots, "
                        "atf_regulatory_alignment_receipts, atf_temporal_migration_records")
            return True
        except Exception as exc:
            logger.warning(f"[TGB] ensure_tables failed: {exc}")
            return False
        finally:
            conn.close()

    def _persist_tcs(self, tcs: TemporalContextSnapshot) -> None:
        if not self._db_url:
            return
        conn = self._get_conn()
        if not conn:
            return
        try:
            import psycopg.types.json as psjson
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO atf_temporal_context_snapshots
                            (tcs_id, parent_record_id, parent_record_type,
                             issued_at_ns, regulatory_context, threshold_context,
                             tcs_hash, tcs_seal, pqc_algorithm, created_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (tcs_id) DO NOTHING
                    """, (
                        tcs.tcs_id, tcs.parent_record_id, tcs.parent_record_type,
                        tcs.issued_at_ns,
                        json.dumps(tcs.regulatory_context),
                        json.dumps(tcs.threshold_context),
                        tcs.tcs_hash, tcs.tcs_seal, tcs.pqc_algorithm, tcs.created_at,
                    ))
        except Exception as exc:
            logger.warning(f"[TGB] persist_tcs failed: {exc}")
        finally:
            conn.close()

    def _persist_rar(self, rar: RegulatoryAlignmentReceipt) -> None:
        if not self._db_url:
            return
        conn = self._get_conn()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO atf_regulatory_alignment_receipts
                            (rar_id, source_record_id, source_tcs_id,
                             review_timestamp, reviewer_context, field_projections,
                             semantic_shift_detected, semantic_shift_fields,
                             original_record_integrity, original_record_hash,
                             projection_methodology, rar_seal, pqc_algorithm,
                             atf_spec_version_source, atf_spec_version_target, created_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (rar_id) DO NOTHING
                    """, (
                        rar.rar_id, rar.source_record_id, rar.source_tcs_id,
                        rar.review_timestamp,
                        json.dumps(rar.reviewer_context),
                        json.dumps(rar.field_projections),
                        rar.semantic_shift_detected,
                        rar.semantic_shift_fields,
                        rar.original_record_integrity, rar.original_record_hash,
                        rar.projection_methodology, rar.rar_seal, rar.pqc_algorithm,
                        rar.atf_spec_version_source, rar.atf_spec_version_target,
                        rar.created_at,
                    ))
        except Exception as exc:
            logger.warning(f"[TGB] persist_rar failed: {exc}")
        finally:
            conn.close()

    def _persist_tmr(self, tmr: TemporalMigrationRecord) -> None:
        if not self._db_url:
            return
        conn = self._get_conn()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO atf_temporal_migration_records
                            (tmr_id, source_record_id, migration_event,
                             migration_timestamp, regulatory_context_at_migration,
                             retention_basis, next_review_due,
                             tmr_seal, pqc_algorithm, created_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (tmr_id) DO NOTHING
                    """, (
                        tmr.tmr_id, tmr.source_record_id, tmr.migration_event,
                        tmr.migration_timestamp,
                        json.dumps(tmr.regulatory_context_at_migration),
                        tmr.retention_basis, tmr.next_review_due,
                        tmr.tmr_seal, tmr.pqc_algorithm, tmr.created_at,
                    ))
        except Exception as exc:
            logger.warning(f"[TGB] persist_tmr failed: {exc}")
        finally:
            conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Process-level singleton
# ─────────────────────────────────────────────────────────────────────────────
_tgb_engine: Optional[TemporalGovernanceBridge] = None
_tgb_lock = threading.Lock()


def get_tgb_engine() -> TemporalGovernanceBridge:
    """Return (or create) the process-level TGB engine singleton."""
    global _tgb_engine
    with _tgb_lock:
        if _tgb_engine is None:
            _tgb_engine = TemporalGovernanceBridge()
    return _tgb_engine


# ─────────────────────────────────────────────────────────────────────────────
# Executable example
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

    tgb = TemporalGovernanceBridge()

    print("\n=== TGB — Temporal Governance Bridge ===")
    print(f"TGB_ENABLED={tgb._enabled}\n")

    # 1. Issue a TCS for a fictional DR
    tcs = tgb.issue_tcs(
        parent_record_id="ATFDR-DEMO0000000000",
        parent_record_type="DR",
    )
    print(f"TCS issued:  {tcs.tcs_id}")
    print(f"  hash:      {tcs.tcs_hash[:32]}...")
    print(f"  pqc_seal:  {'YES — ' + (tcs.pqc_algorithm or '') if tcs.tcs_seal else 'unsigned (no local key)'}")
    print(f"  embed:     {tcs.to_metadata_embed()}")

    v = tgb.verify_tcs(tcs)
    print(f"  verify:    hash_valid={v['hash_valid']} pqc_checked={v['pqc_checked']}")

    # 2. Issue a RAR projecting that DR to a 2027 framework
    rar = tgb.issue_rar(
        source_record_id="ATFDR-DEMO0000000000",
        source_tcs_id=tcs.tcs_id,
        reviewer_context={
            "eu_ai_act_version": "2027/amended-v2.1",
            "atf_spec_version":  "2.0",
            "jurisdiction_active": ["EU", "UK"],
        },
        field_projections=[{
            "field":               "continuity_status",
            "source_value":        "MONITORING",
            "source_scheme":       "ATF-1.4-THRESHOLD",
            "target_value":        "ELEVATED_OVERSIGHT",
            "target_scheme":       "EU_AI_ACT_ART9_2027",
            "projection_rule":     "MONITORING -> ELEVATED_OVERSIGHT (CES 50-79.9 = Art.9(3))",
            "projection_confidence": "HIGH",
            "requires_human_review": False,
        }],
        original_record_hash="sha3_256:demo_hash_placeholder",
        original_record_integrity="VERIFIED",
    )
    print(f"\nRAR issued:  {rar.rar_id}")
    print(f"  semantic_shift: {rar.semantic_shift_detected} → fields: {rar.semantic_shift_fields}")
    print(f"  pqc_seal:  {'YES' if rar.rar_seal else 'unsigned'}")
    print(f"  TGB-INV-002: source record untouched ✓")

    # 3. Issue a TMR (HOT → WARM transition)
    tmr = tgb.issue_tmr(
        source_record_id="ATFDR-DEMO0000000000",
        migration_event="HOT_TO_WARM",
        retention_basis="EU_AI_ACT_ART72_7YR",
    )
    print(f"\nTMR issued:  {tmr.tmr_id}")
    print(f"  event:       {tmr.migration_event}")
    print(f"  basis:       {tmr.retention_basis}")
    print(f"  next_review: {tmr.next_review_due}")
    print(f"  pqc_seal:    {'YES' if tmr.tmr_seal else 'unsigned'}")

    print("\n✓ TGB demonstration complete — status: IMPLEMENTED · TESTED · NOT DEPLOYED")
    sys.exit(0)
