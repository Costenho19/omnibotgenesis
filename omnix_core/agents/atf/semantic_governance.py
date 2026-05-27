"""
OMNIX Agent Trust Fabric — Semantic Governance Interoperability Protocol (SGIP)
ADR-171: Layer 4 semantic interoperability for cross-runtime ATF deployments.

Three artifact types:

  Semantic Term Registry (STR)
    Per-runtime, append-only store of formal operational definitions for the
    eight ATF Core Terms. Each entry is PQC-signed and carries a content_hash
    that is permanent from the moment of first valid signature (SGIP-INV-001).

  Semantic Policy Vector (SPV)
    Point-in-time snapshot of a runtime's STR entries for all eight core terms.
    The spv_hash is a single value representing the runtime's complete semantic
    posture. Two runtimes with identical spv_hash values are semantically
    equivalent.

  Semantic Alignment Certificate (SAC)
    Bilateral, PQC-signed map of semantic alignment between two runtimes.
    Extends the Cross-Runtime Governance Contract (CRGC, ADR-161) to Layer 4.
    Required for ATF-SGIP-Aligned compliance designation.

ATF Core Term Set (SGIP-INV-002):
    AUTHORITY · ADMISSIBILITY · TRUST · SOVEREIGNTY
    RISK · ESCALATION · REVOCATION · LEGITIMACY

Key invariants (ADR-171 §5):
    SGIP-INV-001: STR entries are immutable once signed
    SGIP-INV-002: SAC requires all 8 core terms in both SPVs
    SGIP-INV-003: Unresolved divergence defaults to more restrictive
    SGIP-INV-004: SAC content_hash covers both SPV hashes at issuance

ADR-171 — Harold Nunes — OMNIX QUANTUM LTD — May 2026
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
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("OMNIX.ATF.SemanticGovernance")

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

ALIGNMENT_STATUSES = ("ALIGNED", "ACKNOWLEDGED_DIVERGENCE", "UNRESOLVED")
DIVERGENCE_RESOLUTIONS = ("MORE_RESTRICTIVE", "RUNTIME_A", "RUNTIME_B", "BILATERAL_OVERRIDE")

DDL_SEMANTIC_TERM_REGISTRY = """
CREATE TABLE IF NOT EXISTS atf_semantic_term_registry (
    str_entry_id        VARCHAR(128)  PRIMARY KEY,
    runtime_id          VARCHAR(128)  NOT NULL,
    term_id             VARCHAR(64)   NOT NULL
                            CHECK (term_id IN (
                                'AUTHORITY','ADMISSIBILITY','TRUST','SOVEREIGNTY',
                                'RISK','ESCALATION','REVOCATION','LEGITIMACY'
                            )),
    term_version        VARCHAR(16)   NOT NULL DEFAULT '1.0',
    definition_json     JSONB         NOT NULL,
    operational_scope   JSONB         NOT NULL DEFAULT '{}',
    effective_from      TIMESTAMPTZ   NOT NULL,
    supersedes_id       VARCHAR(128)  DEFAULT NULL,
    content_hash        VARCHAR(64)   NOT NULL,
    pqc_signature       TEXT          DEFAULT NULL,
    pqc_algorithm       VARCHAR(32)   DEFAULT NULL,
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_atf_str_runtime_term
    ON atf_semantic_term_registry (runtime_id, term_id);
CREATE INDEX IF NOT EXISTS idx_atf_str_term_version
    ON atf_semantic_term_registry (term_id, term_version);
"""

DDL_SEMANTIC_POLICY_VECTORS = """
CREATE TABLE IF NOT EXISTS atf_semantic_policy_vectors (
    spv_id              VARCHAR(128)  PRIMARY KEY,
    runtime_id          VARCHAR(128)  NOT NULL,
    generated_at        TIMESTAMPTZ   NOT NULL,
    atf_core_term_set   JSONB         NOT NULL,
    extended_terms      JSONB         NOT NULL DEFAULT '{}',
    spv_hash            VARCHAR(64)   NOT NULL,
    pqc_signature       TEXT          DEFAULT NULL,
    pqc_algorithm       VARCHAR(32)   DEFAULT NULL,
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_atf_spv_runtime
    ON atf_semantic_policy_vectors (runtime_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_atf_spv_hash
    ON atf_semantic_policy_vectors (spv_hash);
"""

DDL_SEMANTIC_ALIGNMENT_CERTIFICATES = """
CREATE TABLE IF NOT EXISTS atf_semantic_alignment_certificates (
    sac_id                  VARCHAR(128)  PRIMARY KEY,
    crgc_id                 VARCHAR(128)  DEFAULT NULL,
    runtime_a_id            VARCHAR(128)  NOT NULL,
    runtime_a_spv_id        VARCHAR(128)  NOT NULL,
    runtime_a_spv_hash      VARCHAR(64)   NOT NULL,
    runtime_b_id            VARCHAR(128)  NOT NULL,
    runtime_b_spv_id        VARCHAR(128)  NOT NULL,
    runtime_b_spv_hash      VARCHAR(64)   NOT NULL,
    effective_from          TIMESTAMPTZ   NOT NULL,
    expires_at              TIMESTAMPTZ   DEFAULT NULL,
    semantic_alignment_map  JSONB         NOT NULL,
    unresolved_terms        JSONB         NOT NULL DEFAULT '[]',
    governing_posture       VARCHAR(32)   NOT NULL DEFAULT 'MORE_RESTRICTIVE',
    sac_content_hash        VARCHAR(64)   NOT NULL,
    pqc_signature_a         TEXT          DEFAULT NULL,
    pqc_signature_b         TEXT          DEFAULT NULL,
    pqc_algorithm           VARCHAR(32)   DEFAULT NULL,
    created_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_atf_sac_runtime_a
    ON atf_semantic_alignment_certificates (runtime_a_id);
CREATE INDEX IF NOT EXISTS idx_atf_sac_runtime_b
    ON atf_semantic_alignment_certificates (runtime_b_id);
CREATE INDEX IF NOT EXISTS idx_atf_sac_crgc
    ON atf_semantic_alignment_certificates (crgc_id);
"""


class SGIPError(Exception):
    """Base exception for SGIP violations."""


class STRImmutabilityViolation(SGIPError):
    """SGIP-INV-001: Attempt to modify an existing STR entry."""


class SAC_IncompleteSPV(SGIPError):
    """SGIP-INV-002: SAC construction attempted with incomplete SPV."""


class UnknownTermError(SGIPError):
    """Term ID not in ATF Core Term Set."""


@dataclass
class SemanticTermEntry:
    """
    A single STR entry — formal operational definition of one ATF core term.

    Fields:
        str_entry_id    — "STR-{runtime_id}-{term_id}-{16HEX}"
        runtime_id      — "RUNTIME-{jurisdiction}-{organization}-{date}"
        term_id         — one of the 8 ATF Core Terms
        term_version    — semantic version string (e.g. "1.0")
        definition      — formal definition dict (formal_statement, boundary_conditions,
                          regulatory_anchors, out_of_scope, examples)
        operational_scope — domains, jurisdictions, agent_tiers dict
        effective_from  — ISO UTC
        supersedes_id   — str_entry_id of the entry this supersedes (or None)
        content_hash    — SHA-256 of canonical JSON (excludes sig fields)
        pqc_signature   — ML-DSA-65 signature over content_hash
        pqc_algorithm   — "ML-DSA-65"
        created_at      — ISO UTC
    """
    str_entry_id: str
    runtime_id: str
    term_id: str
    term_version: str
    definition: Dict[str, Any]
    operational_scope: Dict[str, Any]
    effective_from: str
    supersedes_id: Optional[str]
    content_hash: str
    pqc_signature: Optional[str]
    pqc_algorithm: Optional[str]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_signed(self) -> bool:
        return self.pqc_signature is not None


@dataclass
class SemanticPolicyVector:
    """
    Point-in-time snapshot of a runtime's STR entries for all 8 core terms.

    The spv_hash is the single value representing the runtime's semantic posture.
    Two runtimes with identical spv_hash are semantically equivalent.

    Fields:
        spv_id              — "OMNIX-SPV-{runtime_id}-{date}-{16HEX}"
        runtime_id          — issuing runtime identifier
        generated_at        — ISO UTC timestamp of generation
        atf_core_term_set   — dict: {term_id: {str_entry_id, content_hash}}
        extended_terms      — additional runtime-specific terms
        spv_hash            — SHA-256 over canonical atf_core_term_set entries
        pqc_signature       — ML-DSA-65 signature over spv_hash
        pqc_algorithm       — "ML-DSA-65"
        created_at          — ISO UTC
    """
    spv_id: str
    runtime_id: str
    generated_at: str
    atf_core_term_set: Dict[str, Any]
    extended_terms: Dict[str, Any]
    spv_hash: str
    pqc_signature: Optional[str]
    pqc_algorithm: Optional[str]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_complete(self) -> bool:
        return all(t in self.atf_core_term_set for t in ATF_CORE_TERM_SET)

    def coverage_report(self) -> Dict[str, Any]:
        present = [t for t in ATF_CORE_TERM_SET if t in self.atf_core_term_set]
        missing = [t for t in ATF_CORE_TERM_SET if t not in self.atf_core_term_set]
        return {
            "complete": len(missing) == 0,
            "present_terms": present,
            "missing_terms": missing,
            "coverage_pct": round(len(present) / len(ATF_CORE_TERM_SET) * 100, 1),
        }


@dataclass
class SemanticAlignmentCertificate:
    """
    Bilateral PQC-signed alignment map between two runtimes.
    Layer 4 of the ATF interoperability stack (ADR-171).

    Fields:
        sac_id                  — "OMNIX-SAC-{16HEX}"
        crgc_id                 — linked CRGC (ADR-161) or None
        runtime_a               — {runtime_id, spv_id, spv_hash}
        runtime_b               — {runtime_id, spv_id, spv_hash}
        effective_from          — ISO UTC
        expires_at              — ISO UTC or None
        semantic_alignment_map  — {term_id: {status, runtime_a_hash, runtime_b_hash,
                                              divergence_resolution, divergence_note}}
        unresolved_terms        — list of term_ids with UNRESOLVED status
        governing_posture       — "MORE_RESTRICTIVE" (default) or declared override
        sac_content_hash        — SHA-256 over canonical (parties + alignment_map)
        pqc_signature_a         — ML-DSA-65 from runtime_a over sac_content_hash
        pqc_signature_b         — ML-DSA-65 from runtime_b over sac_content_hash
        pqc_algorithm           — "ML-DSA-65"
        created_at              — ISO UTC
    """
    sac_id: str
    crgc_id: Optional[str]
    runtime_a: Dict[str, Any]
    runtime_b: Dict[str, Any]
    effective_from: str
    expires_at: Optional[str]
    semantic_alignment_map: Dict[str, Any]
    unresolved_terms: List[str]
    governing_posture: str
    sac_content_hash: str
    pqc_signature_a: Optional[str]
    pqc_signature_b: Optional[str]
    pqc_algorithm: Optional[str]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def alignment_summary(self) -> Dict[str, Any]:
        aligned = [t for t, v in self.semantic_alignment_map.items()
                   if v.get("status") == "ALIGNED"]
        divergent = [t for t, v in self.semantic_alignment_map.items()
                     if v.get("status") == "ACKNOWLEDGED_DIVERGENCE"]
        unresolved = self.unresolved_terms
        return {
            "sac_id": self.sac_id,
            "aligned_terms": aligned,
            "divergent_terms": divergent,
            "unresolved_terms": unresolved,
            "sgip_designation": (
                "ATF-SGIP-Aligned" if not unresolved and len(aligned) + len(divergent) == 8
                else "ATF-GPI-Aligned"
            ),
            "both_signed": self.pqc_signature_a is not None and self.pqc_signature_b is not None,
        }

    def sgip_designation(self) -> str:
        summary = self.alignment_summary()
        return summary["sgip_designation"]


class SemanticGovernanceEngine:
    """
    Issues, verifies, and manages SGIP artifacts (STR, SPV, SAC).

    Design contract:
        publish_term()   → SemanticTermEntry (PQC-signed, append-only persisted)
        generate_spv()   → SemanticPolicyVector (snapshot of current STR state)
        create_sac()     → SemanticAlignmentCertificate (bilateral alignment)
        verify_sac()     → verification result dict
        verify_term()    → term entry integrity check
        ensure_tables()  → idempotent DDL

    SGIP-INV-001 enforcement:
        publish_term() raises STRImmutabilityViolation if str_entry_id already exists.
        A new term version must use a new str_entry_id with supersedes_id set.

    SGIP-INV-002 enforcement:
        create_sac() raises SAC_IncompleteSPV if either SPV is missing any core term.
    """

    def __init__(self, runtime_id: str, db_url: Optional[str] = None):
        self.runtime_id = runtime_id
        self._db_url = db_url or os.environ.get("DATABASE_URL")
        self._str_store: Dict[str, SemanticTermEntry] = {}
        self._spv_store: Dict[str, SemanticPolicyVector] = {}
        self._sac_store: Dict[str, SemanticAlignmentCertificate] = {}
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
            logger.warning(f"[ATF.SGIP] DB connection failed: {exc}")
            return None

    @staticmethod
    def _canonical_json(obj: Dict[str, Any]) -> bytes:
        return json.dumps(
            obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")

    @staticmethod
    def _compute_hash(fields: Dict[str, Any]) -> str:
        exclude = {"content_hash", "pqc_signature", "pqc_algorithm",
                   "pqc_signature_a", "pqc_signature_b", "sac_content_hash",
                   "spv_hash"}
        clean = {k: v for k, v in fields.items() if k not in exclude}
        return hashlib.sha256(SemanticGovernanceEngine._canonical_json(clean)).hexdigest()

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
            logger.warning(f"[ATF.SGIP] Sign failed: {exc}")
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
                    cur.execute(DDL_SEMANTIC_TERM_REGISTRY)
                    cur.execute(DDL_SEMANTIC_POLICY_VECTORS)
                    cur.execute(DDL_SEMANTIC_ALIGNMENT_CERTIFICATES)
            logger.info("[ATF.SGIP] Tables ready: STR + SPV + SAC")
            return True
        except Exception as exc:
            logger.warning(f"[ATF.SGIP] ensure_tables failed: {exc}")
            return False
        finally:
            conn.close()

    def publish_term(
        self,
        term_id: str,
        definition: Dict[str, Any],
        operational_scope: Optional[Dict[str, Any]] = None,
        term_version: str = "1.0",
        supersedes_id: Optional[str] = None,
        effective_from: Optional[str] = None,
    ) -> SemanticTermEntry:
        """
        Publish a new STR entry for a core term.

        SGIP-INV-001: Each str_entry_id is unique and append-only.
        To update a term, supply supersedes_id pointing to the previous entry.

        Args:
            term_id         — one of the 8 ATF Core Terms
            definition      — dict with formal_statement, boundary_conditions,
                              regulatory_anchors, out_of_scope, examples
            operational_scope — domains, jurisdictions, agent_tiers (optional)
            term_version    — semantic version (default "1.0")
            supersedes_id   — previous entry being superseded (optional)
            effective_from  — ISO UTC timestamp (default: now)

        Returns:
            SemanticTermEntry — PQC-signed, persisted.

        Raises:
            UnknownTermError: term_id not in ATF Core Term Set
            ValueError: definition missing required formal_statement
        """
        if term_id not in ATF_CORE_TERM_SET:
            raise UnknownTermError(
                f"'{term_id}' is not an ATF Core Term. Valid: {ATF_CORE_TERM_SET}"
            )
        if not definition.get("formal_statement"):
            raise ValueError("definition.formal_statement is required")

        now = datetime.now(timezone.utc).isoformat()
        str_entry_id = (
            f"STR-{self.runtime_id}-{term_id}-{uuid.uuid4().hex[:16].upper()}"
        )

        scope = operational_scope or {}
        core_fields: Dict[str, Any] = {
            "str_entry_id": str_entry_id,
            "runtime_id": self.runtime_id,
            "term_id": term_id,
            "term_version": term_version,
            "definition": definition,
            "operational_scope": scope,
            "effective_from": effective_from or now,
            "supersedes_id": supersedes_id,
            "created_at": now,
        }

        content_hash = self._compute_hash(core_fields)
        pqc_sig, pqc_alg = self._sign(content_hash)

        entry = SemanticTermEntry(
            str_entry_id=str_entry_id,
            runtime_id=self.runtime_id,
            term_id=term_id,
            term_version=term_version,
            definition=definition,
            operational_scope=scope,
            effective_from=effective_from or now,
            supersedes_id=supersedes_id,
            content_hash=content_hash,
            pqc_signature=pqc_sig,
            pqc_algorithm=pqc_alg,
            created_at=now,
        )

        with self._lock:
            self._str_store[str_entry_id] = entry

        self._persist_str_entry(entry)
        logger.info(
            f"[ATF.SGIP] STR entry published — id={str_entry_id} term={term_id} "
            f"version={term_version} signed={pqc_sig is not None}"
        )
        return entry

    def generate_spv(self, extended_terms: Optional[Dict[str, Any]] = None) -> SemanticPolicyVector:
        """
        Generate a Semantic Policy Vector from the current STR state.

        Uses the latest (most recently published) entry per core term.
        The spv_hash is the SHA-256 of the canonical atf_core_term_set dict.

        Returns:
            SemanticPolicyVector — PQC-signed snapshot.

        Note: A complete SPV requires all 8 core terms to be published.
        Partial SPVs are allowed but cannot be used in SAC construction (SGIP-INV-002).
        """
        now = datetime.now(timezone.utc).isoformat()

        latest: Dict[str, SemanticTermEntry] = {}
        with self._lock:
            for entry in self._str_store.values():
                existing = latest.get(entry.term_id)
                if existing is None or entry.created_at > existing.created_at:
                    latest[entry.term_id] = entry

        core_term_map: Dict[str, Any] = {}
        for term_id in ATF_CORE_TERM_SET:
            if term_id in latest:
                e = latest[term_id]
                core_term_map[term_id] = {
                    "str_entry_id": e.str_entry_id,
                    "content_hash": f"sha256:{e.content_hash}",
                    "term_version": e.term_version,
                }

        spv_hash_input = self._canonical_json(core_term_map)
        spv_hash = hashlib.sha256(spv_hash_input).hexdigest()

        spv_id = (
            f"OMNIX-SPV-{self.runtime_id}-"
            f"{datetime.now(timezone.utc).strftime('%Y%m%d')}-"
            f"{uuid.uuid4().hex[:16].upper()}"
        )

        pqc_sig, pqc_alg = self._sign(spv_hash)

        spv = SemanticPolicyVector(
            spv_id=spv_id,
            runtime_id=self.runtime_id,
            generated_at=now,
            atf_core_term_set=core_term_map,
            extended_terms=extended_terms or {},
            spv_hash=spv_hash,
            pqc_signature=pqc_sig,
            pqc_algorithm=pqc_alg,
            created_at=now,
        )

        with self._lock:
            self._spv_store[spv_id] = spv

        self._persist_spv(spv)
        coverage = spv.coverage_report()
        logger.info(
            f"[ATF.SGIP] SPV generated — id={spv_id} coverage={coverage['coverage_pct']}% "
            f"complete={coverage['complete']} hash={spv_hash[:12]}..."
        )
        return spv

    def create_sac(
        self,
        spv_a: SemanticPolicyVector,
        spv_b: SemanticPolicyVector,
        alignment_declarations: Dict[str, Dict[str, Any]],
        crgc_id: Optional[str] = None,
        governing_posture: str = "MORE_RESTRICTIVE",
        expires_at: Optional[str] = None,
        sk_a_b64: Optional[str] = None,
    ) -> SemanticAlignmentCertificate:
        """
        Construct a Semantic Alignment Certificate between two runtimes.

        SGIP-INV-002: Both SPVs must cover all 8 ATF Core Terms.
        SGIP-INV-004: sac_content_hash covers spv_hash values at issuance time.

        Args:
            spv_a                   — SPV of runtime A (this engine's runtime)
            spv_b                   — SPV of runtime B (counterparty)
            alignment_declarations  — per-term alignment map:
                                      {term_id: {status, divergence_resolution?,
                                                  divergence_note?}}
            crgc_id                 — linked CRGC ID (optional)
            governing_posture       — "MORE_RESTRICTIVE" (default)
            expires_at              — ISO UTC or None
            sk_a_b64                — private key for runtime A's signature

        Returns:
            SemanticAlignmentCertificate — content_hash computed, runtime A signed.
            Call add_counterparty_signature() to add runtime B's signature.

        Raises:
            SAC_IncompleteSPV: If either SPV is missing core terms (SGIP-INV-002)
            ValueError: Invalid alignment declaration
        """
        if not spv_a.is_complete():
            missing = spv_a.coverage_report()["missing_terms"]
            raise SAC_IncompleteSPV(
                f"SGIP-INV-002 VIOLATED: SPV-A missing core terms: {missing}"
            )
        if not spv_b.is_complete():
            missing = spv_b.coverage_report()["missing_terms"]
            raise SAC_IncompleteSPV(
                f"SGIP-INV-002 VIOLATED: SPV-B missing core terms: {missing}"
            )

        now = datetime.now(timezone.utc).isoformat()
        sac_id = f"OMNIX-SAC-{uuid.uuid4().hex[:16].upper()}"

        alignment_map: Dict[str, Any] = {}
        unresolved: List[str] = []

        for term_id in ATF_CORE_TERM_SET:
            decl = alignment_declarations.get(term_id, {})
            status = decl.get("status", "UNRESOLVED")
            if status not in ALIGNMENT_STATUSES:
                raise ValueError(
                    f"Invalid alignment status '{status}' for {term_id}. "
                    f"Valid: {ALIGNMENT_STATUSES}"
                )
            entry: Dict[str, Any] = {
                "status": status,
                "runtime_a_hash": spv_a.atf_core_term_set.get(term_id, {}).get("content_hash"),
                "runtime_b_hash": spv_b.atf_core_term_set.get(term_id, {}).get("content_hash"),
            }
            if status == "ACKNOWLEDGED_DIVERGENCE":
                resolution = decl.get("divergence_resolution", "MORE_RESTRICTIVE")
                if resolution not in DIVERGENCE_RESOLUTIONS:
                    raise ValueError(
                        f"Invalid divergence_resolution '{resolution}' for {term_id}."
                    )
                entry["divergence_resolution"] = resolution
                entry["divergence_note"] = decl.get("divergence_note", "")
            elif status == "UNRESOLVED":
                unresolved.append(term_id)
            alignment_map[term_id] = entry

        parties_and_map = {
            "parties": {
                "runtime_a": {
                    "runtime_id": spv_a.runtime_id,
                    "spv_id": spv_a.spv_id,
                    "spv_hash": spv_a.spv_hash,
                },
                "runtime_b": {
                    "runtime_id": spv_b.runtime_id,
                    "spv_id": spv_b.spv_id,
                    "spv_hash": spv_b.spv_hash,
                },
            },
            "semantic_alignment_map": alignment_map,
        }
        sac_content_hash = hashlib.sha256(
            self._canonical_json(parties_and_map)
        ).hexdigest()

        _sk = sk_a_b64 or os.environ.get("OMNIX_SIGNING_SECRET_KEY_B64", "").strip()
        pqc_sig_a, pqc_alg = self._sign(sac_content_hash)
        if sk_a_b64 and sk_a_b64 != os.environ.get("OMNIX_SIGNING_SECRET_KEY_B64", ""):
            try:
                if self._provider:
                    sk = base64.b64decode(sk_a_b64)
                    sig = self._provider.sign(sac_content_hash.encode("utf-8"), sk)
                    if sig:
                        pqc_sig_a = base64.b64encode(sig).decode()
                        pqc_alg = self._provider.algorithm_name()
            except Exception as exc:
                logger.warning(f"[ATF.SGIP] SAC sign-A failed: {exc}")

        sac = SemanticAlignmentCertificate(
            sac_id=sac_id,
            crgc_id=crgc_id,
            runtime_a={
                "runtime_id": spv_a.runtime_id,
                "spv_id": spv_a.spv_id,
                "spv_hash": spv_a.spv_hash,
            },
            runtime_b={
                "runtime_id": spv_b.runtime_id,
                "spv_id": spv_b.spv_id,
                "spv_hash": spv_b.spv_hash,
            },
            effective_from=now,
            expires_at=expires_at,
            semantic_alignment_map=alignment_map,
            unresolved_terms=unresolved,
            governing_posture=governing_posture,
            sac_content_hash=sac_content_hash,
            pqc_signature_a=pqc_sig_a,
            pqc_signature_b=None,
            pqc_algorithm=pqc_alg,
            created_at=now,
        )

        with self._lock:
            self._sac_store[sac_id] = sac

        self._persist_sac(sac)
        summary = sac.alignment_summary()
        logger.info(
            f"[ATF.SGIP] SAC created — id={sac_id} "
            f"aligned={len(summary['aligned_terms'])} "
            f"divergent={len(summary['divergent_terms'])} "
            f"unresolved={len(summary['unresolved_terms'])} "
            f"designation={summary['sgip_designation']}"
        )
        return sac

    def add_counterparty_signature(
        self,
        sac: SemanticAlignmentCertificate,
        sk_b_b64: str,
    ) -> SemanticAlignmentCertificate:
        """
        Add runtime B's PQC signature to a SAC issued by runtime A.

        Both parties must sign the same sac_content_hash (SGIP-INV-004).
        """
        if not self._provider:
            logger.warning("[ATF.SGIP] No PQC provider — counterparty signature skipped")
            return sac
        try:
            sk = base64.b64decode(sk_b_b64)
            sig = self._provider.sign(sac.sac_content_hash.encode("utf-8"), sk)
            if sig:
                sac.pqc_signature_b = base64.b64encode(sig).decode()
                logger.info(f"[ATF.SGIP] SAC counterparty signature added — id={sac.sac_id}")
        except Exception as exc:
            logger.warning(f"[ATF.SGIP] Counterparty sign failed: {exc}")
        return sac

    def verify_term(self, entry: SemanticTermEntry) -> Dict[str, Any]:
        """
        Verify the integrity of an STR entry.

        Checks:
          1. content_hash recomputation (field tampering detection)
          2. PQC signature verification (if signature + public key available)
        """
        fields = entry.to_dict()
        recomputed = self._compute_hash(fields)
        hash_valid = recomputed == entry.content_hash

        pqc_valid = False
        pqc_check = "SKIPPED — no signature"
        if entry.pqc_signature and self._provider:
            pub_key_b64 = os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64", "").strip()
            if pub_key_b64:
                try:
                    pub = base64.b64decode(pub_key_b64)
                    sig = base64.b64decode(entry.pqc_signature)
                    pqc_valid = self._provider.verify(
                        sig, entry.content_hash.encode("utf-8"), pub
                    )
                    pqc_check = "VALID" if pqc_valid else "INVALID"
                except Exception as exc:
                    pqc_check = f"ERROR: {exc}"
            else:
                pqc_check = "SKIPPED — no public key"

        return {
            "str_entry_id": entry.str_entry_id,
            "term_id": entry.term_id,
            "hash_valid": hash_valid,
            "recomputed_hash": recomputed,
            "stored_hash": entry.content_hash,
            "pqc_check": pqc_check,
            "pqc_valid": pqc_valid,
            "integrity_status": (
                "VERIFIED" if hash_valid and pqc_valid
                else "HASH_ONLY" if hash_valid and not pqc_valid
                else "TAMPERED"
            ),
        }

    def verify_sac(
        self,
        sac: SemanticAlignmentCertificate,
        spv_a: Optional[SemanticPolicyVector] = None,
        spv_b: Optional[SemanticPolicyVector] = None,
    ) -> Dict[str, Any]:
        """
        Verify a Semantic Alignment Certificate.

        Checks:
          1. sac_content_hash recomputation (SGIP-INV-004)
          2. PQC signature A (if available)
          3. PQC signature B (if available)
          4. SGIP-INV-002: both SPVs complete (if provided)
          5. Unresolved term analysis (SGIP-INV-003)
        """
        parties_and_map = {
            "parties": {
                "runtime_a": {
                    "runtime_id": sac.runtime_a["runtime_id"],
                    "spv_id": sac.runtime_a["spv_id"],
                    "spv_hash": sac.runtime_a["spv_hash"],
                },
                "runtime_b": {
                    "runtime_id": sac.runtime_b["runtime_id"],
                    "spv_id": sac.runtime_b["spv_id"],
                    "spv_hash": sac.runtime_b["spv_hash"],
                },
            },
            "semantic_alignment_map": sac.semantic_alignment_map,
        }
        recomputed = hashlib.sha256(self._canonical_json(parties_and_map)).hexdigest()
        hash_valid = recomputed == sac.sac_content_hash

        pub_key_b64 = os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64", "").strip()
        sig_a_valid = False
        sig_b_valid = False
        sig_check = "SKIPPED"

        if self._provider and pub_key_b64:
            try:
                pub = base64.b64decode(pub_key_b64)
                msg = sac.sac_content_hash.encode("utf-8")
                if sac.pqc_signature_a:
                    sig_a_valid = self._provider.verify(
                        base64.b64decode(sac.pqc_signature_a), msg, pub
                    )
                if sac.pqc_signature_b:
                    sig_b_valid = self._provider.verify(
                        base64.b64decode(sac.pqc_signature_b), msg, pub
                    )
                sig_check = "COMPLETED"
            except Exception as exc:
                sig_check = f"ERROR: {exc}"

        spv_coverage: Dict[str, Any] = {}
        if spv_a:
            spv_coverage["runtime_a"] = spv_a.coverage_report()
        if spv_b:
            spv_coverage["runtime_b"] = spv_b.coverage_report()

        return {
            "sac_id": sac.sac_id,
            "hash_valid": hash_valid,
            "recomputed_hash": recomputed,
            "stored_hash": sac.sac_content_hash,
            "sig_a_valid": sig_a_valid,
            "sig_b_valid": sig_b_valid,
            "sig_check": sig_check,
            "bilateral_signed": sig_a_valid and sig_b_valid,
            "unresolved_terms": sac.unresolved_terms,
            "sgip_designation": sac.sgip_designation(),
            "governing_posture": sac.governing_posture,
            "spv_coverage": spv_coverage,
            "fully_verified": hash_valid and sig_a_valid and sig_b_valid,
        }

    def get_term(self, term_id: str) -> Optional[SemanticTermEntry]:
        with self._lock:
            latest = None
            for entry in self._str_store.values():
                if entry.term_id == term_id:
                    if latest is None or entry.created_at > latest.created_at:
                        latest = entry
            return latest

    def list_terms(self) -> List[SemanticTermEntry]:
        with self._lock:
            return list(self._str_store.values())

    def _persist_str_entry(self, entry: SemanticTermEntry) -> bool:
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
                        INSERT INTO atf_semantic_term_registry
                            (str_entry_id, runtime_id, term_id, term_version,
                             definition_json, operational_scope, effective_from,
                             supersedes_id, content_hash, pqc_signature, pqc_algorithm,
                             created_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (str_entry_id) DO NOTHING
                        """,
                        (
                            entry.str_entry_id, entry.runtime_id, entry.term_id,
                            entry.term_version,
                            None.Json(entry.definition),
                            None.Json(entry.operational_scope),
                            entry.effective_from, entry.supersedes_id,
                            entry.content_hash, entry.pqc_signature, entry.pqc_algorithm,
                            entry.created_at,
                        ),
                    )
            return True
        except Exception as exc:
            logger.warning(f"[ATF.SGIP] persist_str_entry failed: {exc}")
            return False
        finally:
            conn.close()

    def _persist_spv(self, spv: SemanticPolicyVector) -> bool:
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
                        INSERT INTO atf_semantic_policy_vectors
                            (spv_id, runtime_id, generated_at, atf_core_term_set,
                             extended_terms, spv_hash, pqc_signature, pqc_algorithm,
                             created_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (spv_id) DO NOTHING
                        """,
                        (
                            spv.spv_id, spv.runtime_id, spv.generated_at,
                            None.Json(spv.atf_core_term_set),
                            None.Json(spv.extended_terms),
                            spv.spv_hash, spv.pqc_signature, spv.pqc_algorithm,
                            spv.created_at,
                        ),
                    )
            return True
        except Exception as exc:
            logger.warning(f"[ATF.SGIP] persist_spv failed: {exc}")
            return False
        finally:
            conn.close()

    def _persist_sac(self, sac: SemanticAlignmentCertificate) -> bool:
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
                        INSERT INTO atf_semantic_alignment_certificates
                            (sac_id, crgc_id, runtime_a_id, runtime_a_spv_id,
                             runtime_a_spv_hash, runtime_b_id, runtime_b_spv_id,
                             runtime_b_spv_hash, effective_from, expires_at,
                             semantic_alignment_map, unresolved_terms, governing_posture,
                             sac_content_hash, pqc_signature_a, pqc_signature_b,
                             pqc_algorithm, created_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (sac_id) DO NOTHING
                        """,
                        (
                            sac.sac_id, sac.crgc_id,
                            sac.runtime_a["runtime_id"], sac.runtime_a["spv_id"],
                            sac.runtime_a["spv_hash"],
                            sac.runtime_b["runtime_id"], sac.runtime_b["spv_id"],
                            sac.runtime_b["spv_hash"],
                            sac.effective_from, sac.expires_at,
                            None.Json(sac.semantic_alignment_map),
                            None.Json(sac.unresolved_terms),
                            sac.governing_posture, sac.sac_content_hash,
                            sac.pqc_signature_a, sac.pqc_signature_b,
                            sac.pqc_algorithm, sac.created_at,
                        ),
                    )
            return True
        except Exception as exc:
            logger.warning(f"[ATF.SGIP] persist_sac failed: {exc}")
            return False
        finally:
            conn.close()
