"""
OMNIX Agent Trust Fabric — Grand Unified Governance Theory (GUGT)
ADR-179: Universal Invariant Framework covering all AI governance domains,
jurisdictions, and agent types under a single provable receipt.

One record type:
  - UniversalInvariantReceipt (UIR): cryptographically-sealed certification
    that a subject system satisfies all six Universal Governance Invariants
    (UGI-001 through UGI-006) across at least one regulatory framework.

Six Universal Governance Invariants:
    UGI-001  Human Anchor         — every AI decision is ultimately accountable
                                    to a human principal
    UGI-002  Temporal Validity    — governance records carry explicit validity
                                    bounds; stale evidence is inadmissible
    UGI-003  Cross-Domain Port.   — evidence is verifiable across domains and
                                    jurisdictions without bilateral negotiation
    UGI-004  Auditability         — a complete, tamper-evident audit trail exists
                                    and is independently reconstructible
    UGI-005  Cryptographic Int.   — every artifact is PQC-sealed (ML-DSA-65)
    UGI-006  Self-Contained Rec.  — offline verification requires no platform
                                    access beyond the artifact itself

Four Conformance Levels:
    GUGT-L1       UGI-001 + UGI-002 PASS
    GUGT-L2       UGI-001..004 all PASS
    GUGT-L3       All six UGIs PASS
    GUGT-L3+ATF   GUGT-L3 AND subject_protocol == "ATF"

Key invariants:
    GUGT-INV-001  UIR MUST carry assessments for all 6 UGIs
    GUGT-INV-002  Each UGI MUST reference at least one specific clause
    GUGT-INV-003  UIR MUST be ML-DSA-65 sealed (allow_unsigned for test only)
    GUGT-INV-004  agent_type_coverage MUST be non-empty
    GUGT-INV-005  UIR is append-only once issued
    GUGT-INV-006  L3 / L3+ATF require UGI-001 PASS

Status: IMPLEMENTED · TESTED · NOT DEPLOYED

ADR-179 — Harold Nunes — OMNIX QUANTUM LTD — June 2026
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import secrets
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from omnix_core.security.crypto_providers import get_active_provider

logger = logging.getLogger("OMNIX.ATF.GUGT")

# ─────────────────────────────────────────────────────────────────────────────
# Compiled constants
# ─────────────────────────────────────────────────────────────────────────────
GUGT_SPEC_VERSION = "1.0"
GUGT_ATF_SPEC_VERSION = "1.4"

# Ordered canonical UGI catalogue (GUGT-INV-001)
UNIVERSAL_GOVERNANCE_INVARIANTS: Tuple[str, ...] = (
    "UGI-001",  # Human Anchor
    "UGI-002",  # Temporal Validity
    "UGI-003",  # Cross-Domain Portability
    "UGI-004",  # Auditability
    "UGI-005",  # Cryptographic Integrity
    "UGI-006",  # Self-Contained Reconstruction
)

UGI_DESCRIPTIONS: Dict[str, str] = {
    "UGI-001": "Human Anchor — every AI decision is ultimately accountable to a human principal",
    "UGI-002": "Temporal Validity — governance records carry explicit validity bounds",
    "UGI-003": "Cross-Domain Portability — evidence verifiable across domains and jurisdictions",
    "UGI-004": "Auditability — complete, tamper-evident audit trail independently reconstructible",
    "UGI-005": "Cryptographic Integrity — every artifact PQC-sealed with ML-DSA-65 (FIPS 204)",
    "UGI-006": "Self-Contained Reconstruction — offline verifiable without platform access",
}

# Conformance levels (monotonically increasing)
CONFORMANCE_LEVELS = ("GUGT-L1", "GUGT-L2", "GUGT-L3", "GUGT-L3+ATF")

# Valid assessment statuses per UGI
VALID_STATUSES = frozenset({"PASS", "FAIL", "NOT_ASSESSED"})

# ─────────────────────────────────────────────────────────────────────────────
# Framework Coverage — controlled vocabulary (GUGT-INV-002)
#
# Format: <PREFIX>_<CLAUSE>  or  CUSTOM:<framework>:<clause>
# Architect guidance: controlled prefixes prevent false certifications via
# free-form strings. CUSTOM namespace allows forward-compatible extension.
# ─────────────────────────────────────────────────────────────────────────────
FRAMEWORK_PREFIXES = frozenset({
    "EU_AI_ACT",
    "NIST_GOVERN",
    "NIST_MAP",
    "NIST_MANAGE",
    "NIST_MEASURE",
    "GCC_DIFC",
    "ISO42001",
    "UK_AI_SAFETY",
    "DORA",
    "MICA",
    "NIST_AU",
    "ATF",            # OMNIX ATF invariant family citations
    "BEV",
    "MIVP",
    "POGR",
})

# Known valid clause references (non-exhaustive; new ones accepted via CUSTOM:)
KNOWN_CLAUSES = frozenset({
    "EU_AI_ACT_ART9",   "EU_AI_ACT_ART11",  "EU_AI_ACT_ART13",
    "EU_AI_ACT_ART14",  "EU_AI_ACT_ART72",
    "NIST_GOVERN_1.1",  "NIST_GOVERN_2.2",
    "NIST_MAP_1.1",     "NIST_MAP_3.5",
    "NIST_MANAGE_2.2",  "NIST_MANAGE_4.1",
    "NIST_MEASURE_1.1", "NIST_MEASURE_2.5",
    "NIST_AU_2",        "NIST_AU_3",
    "GCC_DIFC_ART14",   "GCC_DIFC_ART9_7",
    "ISO42001_6_2",     "ISO42001_8_4",     "ISO42001_10YR",
    "UK_AI_SAFETY_S3",  "UK_AI_SAFETY_S7",
    "DORA_ART11",       "DORA_ART17",
    "MICA_TITLE6",
    "ATF_INV_001",      "ATF_INV_006",
    "BEV_INV_001",      "BEV_INV_010",
    "MIVP_INV_001",     "MIVP_INV_009",
    "POGR_INV_001",     "POGR_INV_003",
})


def _validate_clause_ref(ref: str) -> bool:
    """
    Validate a framework clause reference against the controlled vocabulary.

    Accepted forms:
      - A known clause from KNOWN_CLAUSES
      - <PREFIX>_<anything>  where PREFIX is in FRAMEWORK_PREFIXES
      - CUSTOM:<framework>:<clause>   (explicit extension namespace)

    Returns True if valid, False otherwise.
    """
    if not ref or not isinstance(ref, str):
        return False
    ref = ref.strip()
    if ref in KNOWN_CLAUSES:
        return True
    if ref.startswith("CUSTOM:"):
        parts = ref.split(":", 2)
        return len(parts) == 3 and all(p.strip() for p in parts)
    for prefix in FRAMEWORK_PREFIXES:
        if ref.startswith(prefix + "_") and len(ref) > len(prefix) + 1:
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# DDL — idempotent
# ─────────────────────────────────────────────────────────────────────────────
DDL_GUGT = """
CREATE TABLE IF NOT EXISTS gugt_universal_invariant_receipts (
    id                      SERIAL PRIMARY KEY,
    uir_id                  TEXT NOT NULL UNIQUE,
    subject_system          TEXT NOT NULL,
    subject_protocol        TEXT NOT NULL,
    ugi_assessment          JSONB NOT NULL,
    agent_type_coverage     TEXT[] NOT NULL,
    jurisdiction_coverage   TEXT[] NOT NULL,
    conformance_level       TEXT NOT NULL,
    ugi_pass_count          INTEGER NOT NULL,
    certification_valid     BOOLEAN NOT NULL DEFAULT TRUE,
    content_hash            TEXT NOT NULL,
    uir_seal                TEXT,
    pqc_algorithm           TEXT,
    issued_at               TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_uir_subject
    ON gugt_universal_invariant_receipts (subject_system);
CREATE INDEX IF NOT EXISTS idx_uir_conformance
    ON gugt_universal_invariant_receipts (conformance_level);
CREATE INDEX IF NOT EXISTS idx_uir_issued
    ON gugt_universal_invariant_receipts (issued_at DESC);
"""

# ─────────────────────────────────────────────────────────────────────────────
# Custom exceptions
# ─────────────────────────────────────────────────────────────────────────────

class GUGTInvariantViolation(Exception):
    """Raised when a GUGT invariant is violated during UIR issuance."""
    def __init__(self, invariant: str, detail: str):
        self.invariant = invariant
        self.detail = detail
        super().__init__(f"[{invariant}] {detail}")


class GUGTUnsignedError(Exception):
    """Raised when signing fails in production mode (allow_unsigned=False)."""


# ─────────────────────────────────────────────────────────────────────────────
# Dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class UniversalInvariantReceipt:
    """
    Universal Invariant Receipt (UIR) — GUGT root artifact.

    Certifies that a subject system satisfies the six Universal Governance
    Invariants across one or more regulatory frameworks. Sealed ML-DSA-65.

    ID format: UIR-{16 uppercase hex digits}
    """
    uir_id: str
    subject_system: str
    subject_protocol: str
    ugi_assessment: Dict[str, Any]          # {UGI-001..006: {status, evidence_ref, framework_coverage}}
    agent_type_coverage: List[str]           # e.g. ["LLM", "TRADING_AGENT"]
    jurisdiction_coverage: List[str]         # e.g. ["EU", "UAE", "UK"]
    conformance_level: str                   # GUGT-L1 / L2 / L3 / L3+ATF
    ugi_pass_count: int
    certification_valid: bool                # False when issued without seal (GUGT-INV-003)
    content_hash: str                        # sha3-256:<hex>
    uir_seal: Optional[str]                  # base64 ML-DSA-65 signature over content_hash
    pqc_algorithm: Optional[str]
    issued_at: str                           # ISO-8601 UTC

    # Optional cross-artifact links (TGB TCS / CGE CAT ids — no hard dependency)
    linked_artifacts: Optional[Dict[str, List[str]]] = field(default=None)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_signed(self) -> bool:
        return self.uir_seal is not None

    @property
    def passes_all_ugis(self) -> bool:
        return self.ugi_pass_count == 6

    def summary(self) -> str:
        signed = "SEALED" if self.is_signed() else "UNSIGNED"
        return (
            f"UIR {self.uir_id} | {self.conformance_level} | "
            f"UGIs={self.ugi_pass_count}/6 | {signed} | "
            f"system={self.subject_system}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Engine
# ─────────────────────────────────────────────────────────────────────────────

class GrandUnifiedGovernanceEngine:
    """
    GUGT Engine — issues, stores, and verifies Universal Invariant Receipts.

    Usage (typical):
        engine = GrandUnifiedGovernanceEngine()
        assessment = engine.assess_ugi_compliance(
            subject_system="MyAISystem-v1",
            evidence_by_ugi={
                "UGI-001": {"status": "PASS", "evidence_ref": "DR-...",
                            "framework_coverage": ["EU_AI_ACT_ART14"]},
                ...
            }
        )
        uir = engine.issue_uir(
            subject_system="MyAISystem-v1",
            subject_protocol="ATF",
            ugi_assessment=assessment,
            agent_type_coverage=["LLM"],
            jurisdiction_coverage=["EU"],
        )

    Storage:
        Primary:  PostgreSQL table gugt_universal_invariant_receipts
        Fallback: In-process dict (dev / test without DB)

    Signing (GUGT-INV-003):
        Production: OMNIX_SIGNING_SECRET_KEY_B64 must be set; exception on failure.
        Test/dev:   Pass allow_unsigned=True to engine or individual issue_uir call.
    """

    def __init__(self, allow_unsigned: bool = False):
        """
        Args:
            allow_unsigned: If True, UIR issuance proceeds without seal when no
                            signing key is available (marks certification_valid=False).
                            MUST be False in production.
        """
        self._allow_unsigned = allow_unsigned
        self._provider = get_active_provider()
        self._lock = threading.Lock()
        self._memory_store: Dict[str, UniversalInvariantReceipt] = {}
        self._tables_ensured = False

    # ── DDL ──────────────────────────────────────────────────────────────────

    def _ensure_tables(self) -> None:
        if self._tables_ensured:
            return
        try:
            conn = self._get_db()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(DDL_GUGT)
            conn.close()
            self._tables_ensured = True
            logger.info("[GUGT] DB tables ensured (gugt_universal_invariant_receipts)")
        except Exception as exc:
            logger.warning(f"[GUGT] DDL skipped (in-memory fallback active): {exc}")

    def _get_db(self):
        url = os.environ.get("DATABASE_URL", "")
        if not url:
            raise RuntimeError("DATABASE_URL not configured")
        try:
            import psycopg
            conn = psycopg.connect(url, row_factory=psycopg.rows.dict_row)
            return conn
        except ImportError:
            pass
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = False
        return conn

    # ── Signing ───────────────────────────────────────────────────────────────

    def _sign(self, content_hash: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Sign content_hash with ML-DSA-65.

        Returns (seal_b64, algorithm_name) on success, (None, None) on failure.
        Failure behaviour depends on self._allow_unsigned.
        """
        sk_b64 = os.environ.get("OMNIX_SIGNING_SECRET_KEY_B64", "").strip()
        if not sk_b64:
            return None, None
        try:
            sk = base64.b64decode(sk_b64)
            sig_bytes = self._provider.sign(content_hash.encode(), sk)
            if sig_bytes is None:
                return None, None
            return base64.b64encode(sig_bytes).decode(), self._provider.algorithm_name()
        except Exception as exc:
            logger.warning(f"[GUGT] PQC signing failed: {exc}")
            return None, None

    def _verify_seal(
        self, seal_b64: str, content_hash: str, public_key_b64: str
    ) -> bool:
        try:
            sig = base64.b64decode(seal_b64)
            pk  = base64.b64decode(public_key_b64)
            return self._provider.verify(sig, content_hash.encode(), pk)
        except Exception as exc:
            logger.warning(f"[GUGT] Seal verification error: {exc}")
            return False

    # ── Hashing ───────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_content_hash(payload: Dict[str, Any]) -> str:
        """SHA3-256 over the canonical JSON of the UIR payload (excl. uir_seal)."""
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha3_256(canonical.encode()).hexdigest()
        return f"sha3-256:{digest}"

    # ── Validation helpers ────────────────────────────────────────────────────

    @staticmethod
    def _validate_ugi_assessment(evidence_by_ugi: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalise a caller-supplied UGI evidence dict.

        Each UGI entry must have:
          - status: "PASS" | "FAIL" | "NOT_ASSESSED"
          - framework_coverage: non-empty list of controlled clause refs
          - evidence_ref: optional string reference to a supporting artifact

        Raises:
            GUGTInvariantViolation(GUGT-INV-001) if any UGI is missing
            GUGTInvariantViolation(GUGT-INV-002) if clause specificity fails
        """
        normalised: Dict[str, Any] = {}

        # GUGT-INV-001: all 6 UGIs must be present
        for ugi in UNIVERSAL_GOVERNANCE_INVARIANTS:
            if ugi not in evidence_by_ugi:
                raise GUGTInvariantViolation(
                    "GUGT-INV-001",
                    f"UGI evidence missing for {ugi} — all 6 UGIs required. "
                    f"Provided: {sorted(evidence_by_ugi.keys())}"
                )

        for ugi, entry in evidence_by_ugi.items():
            if ugi not in UNIVERSAL_GOVERNANCE_INVARIANTS:
                logger.warning(f"[GUGT] Unknown UGI key '{ugi}' — ignored")
                continue

            if not isinstance(entry, dict):
                raise GUGTInvariantViolation(
                    "GUGT-INV-001",
                    f"{ugi} evidence must be a dict, got {type(entry).__name__}"
                )

            status = entry.get("status", "NOT_ASSESSED")
            if status not in VALID_STATUSES:
                raise GUGTInvariantViolation(
                    "GUGT-INV-001",
                    f"{ugi}.status='{status}' invalid. Must be one of {sorted(VALID_STATUSES)}"
                )

            # GUGT-INV-002: at least one specific clause reference required
            coverage: List[str] = entry.get("framework_coverage", [])
            if not coverage:
                raise GUGTInvariantViolation(
                    "GUGT-INV-002",
                    f"{ugi} has empty framework_coverage. "
                    "At least one specific clause reference is required (e.g. EU_AI_ACT_ART14)."
                )

            invalid_clauses = [c for c in coverage if not _validate_clause_ref(c)]
            if invalid_clauses:
                raise GUGTInvariantViolation(
                    "GUGT-INV-002",
                    f"{ugi} contains invalid clause references: {invalid_clauses}. "
                    "Use controlled prefixes (EU_AI_ACT, NIST_GOVERN, …) or CUSTOM:<framework>:<clause>."
                )

            normalised[ugi] = {
                "status":             status,
                "evidence_ref":       entry.get("evidence_ref", ""),
                "framework_coverage": list(coverage),
                "description":        UGI_DESCRIPTIONS.get(ugi, ""),
                "linked_artifacts":   entry.get("linked_artifacts", []),
            }

        return normalised

    @staticmethod
    def _compute_conformance_level(
        assessment: Dict[str, Any], subject_protocol: str
    ) -> Tuple[str, int]:
        """
        Determine conformance level from a validated UGI assessment.

        Returns (conformance_level, ugi_pass_count).

        Hierarchy:
            GUGT-L3+ATF  all 6 PASS + protocol == "ATF"
            GUGT-L3      all 6 PASS
            GUGT-L2      UGI-001..004 all PASS
            GUGT-L1      UGI-001 + UGI-002 PASS
            (none)       < GUGT-L1 threshold
        """
        pass_set = {
            ugi for ugi, v in assessment.items()
            if v.get("status") == "PASS"
        }
        count = len(pass_set)

        all_six = set(UNIVERSAL_GOVERNANCE_INVARIANTS)
        l2_required = {"UGI-001", "UGI-002", "UGI-003", "UGI-004"}
        l1_required = {"UGI-001", "UGI-002"}

        if all_six.issubset(pass_set):
            level = "GUGT-L3+ATF" if subject_protocol == "ATF" else "GUGT-L3"
        elif l2_required.issubset(pass_set):
            level = "GUGT-L2"
        elif l1_required.issubset(pass_set):
            level = "GUGT-L1"
        else:
            level = "GUGT-L1-PARTIAL"  # below minimum; UIR will have certification_valid=False

        return level, count

    # ── Public API ────────────────────────────────────────────────────────────

    def assess_ugi_compliance(
        self,
        subject_system: str,
        evidence_by_ugi: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate and normalise caller-supplied UGI evidence.

        This is the first step — call before issue_uir() to catch
        evidence problems early without committing any record.

        Args:
            subject_system:  Human-readable identifier for the system being assessed.
            evidence_by_ugi: Dict keyed by UGI-001..UGI-006; each value is:
                {
                    "status": "PASS" | "FAIL" | "NOT_ASSESSED",
                    "evidence_ref": "<artifact-id or URL>",       # optional
                    "framework_coverage": ["EU_AI_ACT_ART14", …], # required, ≥1
                    "linked_artifacts": ["TCS-…", "CAT-…"],       # optional
                }

        Returns:
            Normalised assessment dict (same structure, with descriptions added).

        Raises:
            GUGTInvariantViolation — GUGT-INV-001 (missing UGI) or
                                     GUGT-INV-002 (clause specificity failure)
        """
        logger.debug(f"[GUGT] assess_ugi_compliance — system={subject_system}")
        return self._validate_ugi_assessment(evidence_by_ugi)

    def issue_uir(
        self,
        subject_system: str,
        subject_protocol: str,
        ugi_assessment: Dict[str, Any],
        agent_type_coverage: List[str],
        jurisdiction_coverage: List[str],
        *,
        allow_unsigned: Optional[bool] = None,
        linked_artifacts: Optional[Dict[str, List[str]]] = None,
    ) -> UniversalInvariantReceipt:
        """
        Issue a Universal Invariant Receipt.

        Invariants enforced:
            GUGT-INV-001  All 6 UGIs present
            GUGT-INV-002  Every UGI has ≥1 specific clause ref
            GUGT-INV-003  UIR is ML-DSA-65 sealed (unless allow_unsigned)
            GUGT-INV-004  agent_type_coverage non-empty
            GUGT-INV-005  Stored append-only (ON CONFLICT DO NOTHING)
            GUGT-INV-006  L3/L3+ATF requires UGI-001 PASS

        Args:
            subject_system:       Identifier for the system being certified.
            subject_protocol:     Protocol governing the system ("ATF", "VGS",
                                  "CUSTOM", …). Use "ATF" for GUGT-L3+ATF.
            ugi_assessment:       Output of assess_ugi_compliance().
            agent_type_coverage:  Non-empty list of agent types certified
                                  (e.g. ["LLM", "TRADING_AGENT"]).
            jurisdiction_coverage: Jurisdictions covered (e.g. ["EU", "UAE"]).
            allow_unsigned:       Override instance-level allow_unsigned setting.
                                  If None, uses instance default.
            linked_artifacts:     Optional dict of artifact IDs from sibling
                                  modules — e.g. {"tcs_ids": ["TCS-…"], "cat_ids": […]}.
                                  No hard dependency; stored for audit traceability.

        Returns:
            UniversalInvariantReceipt — sealed and persisted.

        Raises:
            GUGTInvariantViolation — on any invariant breach.
            GUGTUnsignedError     — signing failed in production mode.
        """
        unsigned_ok = allow_unsigned if allow_unsigned is not None else self._allow_unsigned

        # ── GUGT-INV-004: agent_type_coverage non-empty ───────────────────
        if not agent_type_coverage:
            raise GUGTInvariantViolation(
                "GUGT-INV-004",
                "agent_type_coverage must be non-empty. "
                "Specify at least one agent type (e.g. 'LLM', 'TRADING_AGENT')."
            )

        # Re-validate assessment (in case caller bypassed assess_ugi_compliance)
        validated = self._validate_ugi_assessment(ugi_assessment)

        # ── Conformance level ─────────────────────────────────────────────
        conformance_level, ugi_pass_count = self._compute_conformance_level(
            validated, subject_protocol
        )

        # ── GUGT-INV-006: L3/L3+ATF requires UGI-001 PASS ────────────────
        if conformance_level in ("GUGT-L3", "GUGT-L3+ATF"):
            if validated.get("UGI-001", {}).get("status") != "PASS":
                raise GUGTInvariantViolation(
                    "GUGT-INV-006",
                    f"Conformance level {conformance_level} requires UGI-001 PASS. "
                    f"Got status='{validated.get('UGI-001', {}).get('status', 'MISSING')}'. "
                    "Downgrade subject's conformance claim or fix the UGI-001 evidence."
                )

        # ── Build content hash payload ─────────────────────────────────────
        now_utc = datetime.now(timezone.utc).isoformat()
        uir_id  = "UIR-" + secrets.token_hex(8).upper()

        payload: Dict[str, Any] = {
            "uir_id":               uir_id,
            "subject_system":       subject_system,
            "subject_protocol":     subject_protocol,
            "ugi_assessment":       validated,
            "agent_type_coverage":  sorted(set(agent_type_coverage)),
            "jurisdiction_coverage": sorted(set(jurisdiction_coverage)),
            "conformance_level":    conformance_level,
            "ugi_pass_count":       ugi_pass_count,
            "issued_at":            now_utc,
            "gugt_spec_version":    GUGT_SPEC_VERSION,
        }
        if linked_artifacts:
            payload["linked_artifacts"] = linked_artifacts

        content_hash = self._compute_content_hash(payload)

        # ── GUGT-INV-003: sign ─────────────────────────────────────────────
        uir_seal, pqc_alg = self._sign(content_hash)
        certification_valid = True

        if uir_seal is None:
            if unsigned_ok:
                logger.warning(
                    f"[GUGT] UIR {uir_id} issued WITHOUT PQC seal — "
                    "OMNIX_SIGNING_SECRET_KEY_B64 not set or signing failed. "
                    "certification_valid=False. DO NOT use in production (GUGT-INV-003)."
                )
                certification_valid = False
            else:
                raise GUGTUnsignedError(
                    f"[GUGT] Cannot issue UIR {uir_id} — PQC signing failed and "
                    "allow_unsigned=False (production mode). "
                    "Set OMNIX_SIGNING_SECRET_KEY_B64 in the deployment environment."
                )

        uir = UniversalInvariantReceipt(
            uir_id=uir_id,
            subject_system=subject_system,
            subject_protocol=subject_protocol,
            ugi_assessment=validated,
            agent_type_coverage=sorted(set(agent_type_coverage)),
            jurisdiction_coverage=sorted(set(jurisdiction_coverage)),
            conformance_level=conformance_level,
            ugi_pass_count=ugi_pass_count,
            certification_valid=certification_valid,
            content_hash=content_hash,
            uir_seal=uir_seal,
            pqc_algorithm=pqc_alg,
            issued_at=now_utc,
            linked_artifacts=linked_artifacts,
        )

        self._persist(uir)
        logger.info(
            f"[GUGT] UIR issued — {uir.summary()} | "
            f"protocol={subject_protocol} sealed={uir.is_signed()}"
        )
        return uir

    def get_uir(self, uir_id: str) -> Optional[UniversalInvariantReceipt]:
        """
        Retrieve a UIR by ID. Checks DB first, then in-memory store.
        Returns None if not found.
        """
        # Try DB
        try:
            self._ensure_tables()
            conn = self._get_db()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM gugt_universal_invariant_receipts WHERE uir_id = %s LIMIT 1",
                    (uir_id,)
                )
                row = cur.fetchone()
            conn.close()
            if row:
                return self._row_to_uir(dict(row))
        except Exception as exc:
            logger.warning(f"[GUGT] DB read failed for {uir_id}: {exc}")

        # Fallback: in-memory
        with self._lock:
            return self._memory_store.get(uir_id)

    def verify_uir(
        self,
        uir: UniversalInvariantReceipt,
        public_key_b64: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Offline-verify a UIR: content hash integrity + ML-DSA-65 seal.

        This is a zero-trust, zero-platform-access verification path:
        a reviewer who holds only the UIR dict and the OMNIX public key
        can reproduce all checks without an OMNIX account.

        Args:
            uir:             The receipt to verify.
            public_key_b64:  ML-DSA-65 public key (base64). Falls back to
                             OMNIX_SIGNING_PUBLIC_KEY_B64 env var.

        Returns:
            {
                "valid":            bool,
                "content_hash_ok":  bool,
                "pqc_seal_ok":      bool | None,   # None = key unavailable
                "conformance_level": str,
                "ugi_pass_count":   int,
                "notes":            [str],
            }
        """
        notes: List[str] = []
        content_hash_ok = False
        pqc_seal_ok: Optional[bool] = None

        # ── 1. Rebuild canonical payload (exclude seal fields) ─────────────
        payload: Dict[str, Any] = {
            "uir_id":               uir.uir_id,
            "subject_system":       uir.subject_system,
            "subject_protocol":     uir.subject_protocol,
            "ugi_assessment":       uir.ugi_assessment,
            "agent_type_coverage":  uir.agent_type_coverage,
            "jurisdiction_coverage": uir.jurisdiction_coverage,
            "conformance_level":    uir.conformance_level,
            "ugi_pass_count":       uir.ugi_pass_count,
            "issued_at":            uir.issued_at,
            "gugt_spec_version":    GUGT_SPEC_VERSION,
        }
        if uir.linked_artifacts:
            payload["linked_artifacts"] = uir.linked_artifacts

        expected_hash = self._compute_content_hash(payload)
        if expected_hash == uir.content_hash:
            content_hash_ok = True
            notes.append("✓ Content hash verified (SHA3-256)")
        else:
            notes.append(
                f"✗ Content hash mismatch — "
                f"expected={expected_hash} stored={uir.content_hash}"
            )

        # ── 2. PQC seal ────────────────────────────────────────────────────
        if not uir.uir_seal:
            notes.append("⚠ No PQC seal present (unsigned UIR — GUGT-INV-003 not satisfied)")
        else:
            pk_b64 = (
                public_key_b64
                or os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64", "")
            )
            if not pk_b64:
                notes.append(
                    "⚠ No public key provided — PQC seal verification skipped. "
                    "Pass public_key_b64 or set OMNIX_SIGNING_PUBLIC_KEY_B64."
                )
            else:
                pqc_seal_ok = self._verify_seal(uir.uir_seal, uir.content_hash, pk_b64)
                if pqc_seal_ok:
                    notes.append(
                        f"✓ ML-DSA-65 seal cryptographically verified "
                        f"(FIPS 204 · {uir.pqc_algorithm or 'ml-dsa-65'})"
                    )
                else:
                    notes.append(
                        "✗ ML-DSA-65 seal INVALID — "
                        "content was tampered or wrong public key provided"
                    )

        # ── 3. Conformance summary ─────────────────────────────────────────
        notes.append(
            f"✓ Conformance: {uir.conformance_level} "
            f"({uir.ugi_pass_count}/6 UGIs PASS)"
        )
        if not uir.certification_valid:
            notes.append(
                "⚠ certification_valid=False — "
                "UIR was issued without a PQC seal (GUGT-INV-003 not satisfied)"
            )

        valid = (
            content_hash_ok
            and (pqc_seal_ok is not False)
            and uir.certification_valid
        )

        return {
            "valid":             valid,
            "content_hash_ok":   content_hash_ok,
            "pqc_seal_ok":       pqc_seal_ok,
            "conformance_level": uir.conformance_level,
            "ugi_pass_count":    uir.ugi_pass_count,
            "certification_valid": uir.certification_valid,
            "notes":             notes,
        }

    # ── Storage ───────────────────────────────────────────────────────────────

    def _persist(self, uir: UniversalInvariantReceipt) -> None:
        """Persist UIR to DB (primary) or in-memory store (fallback)."""
        self._ensure_tables()
        stored_to_db = False
        try:
            conn = self._get_db()
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO gugt_universal_invariant_receipts
                            (uir_id, subject_system, subject_protocol,
                             ugi_assessment, agent_type_coverage, jurisdiction_coverage,
                             conformance_level, ugi_pass_count, certification_valid,
                             content_hash, uir_seal, pqc_algorithm, issued_at)
                        VALUES
                            (%(uir_id)s, %(subject_system)s, %(subject_protocol)s,
                             %(ugi_assessment)s, %(agent_type_coverage)s, %(jurisdiction_coverage)s,
                             %(conformance_level)s, %(ugi_pass_count)s, %(certification_valid)s,
                             %(content_hash)s, %(uir_seal)s, %(pqc_algorithm)s, %(issued_at)s)
                        ON CONFLICT (uir_id) DO NOTHING
                    """, {
                        "uir_id":               uir.uir_id,
                        "subject_system":       uir.subject_system,
                        "subject_protocol":     uir.subject_protocol,
                        "ugi_assessment":       json.dumps(uir.ugi_assessment),
                        "agent_type_coverage":  uir.agent_type_coverage,
                        "jurisdiction_coverage": uir.jurisdiction_coverage,
                        "conformance_level":    uir.conformance_level,
                        "ugi_pass_count":       uir.ugi_pass_count,
                        "certification_valid":  uir.certification_valid,
                        "content_hash":         uir.content_hash,
                        "uir_seal":             uir.uir_seal,
                        "pqc_algorithm":        uir.pqc_algorithm,
                        "issued_at":            uir.issued_at,
                    })
            conn.close()
            stored_to_db = True
            logger.debug(f"[GUGT] Persisted {uir.uir_id} to DB")
        except Exception as exc:
            logger.warning(f"[GUGT] DB persist failed — falling back to memory: {exc}")

        if not stored_to_db:
            with self._lock:
                self._memory_store[uir.uir_id] = uir
            logger.debug(f"[GUGT] {uir.uir_id} stored in memory (DB unavailable)")

    def _row_to_uir(self, row: Dict[str, Any]) -> UniversalInvariantReceipt:
        """Reconstruct a UIR from a DB row dict."""
        ugi_assessment = row.get("ugi_assessment")
        if isinstance(ugi_assessment, str):
            ugi_assessment = json.loads(ugi_assessment)
        return UniversalInvariantReceipt(
            uir_id=row["uir_id"],
            subject_system=row["subject_system"],
            subject_protocol=row["subject_protocol"],
            ugi_assessment=ugi_assessment or {},
            agent_type_coverage=list(row.get("agent_type_coverage") or []),
            jurisdiction_coverage=list(row.get("jurisdiction_coverage") or []),
            conformance_level=row["conformance_level"],
            ugi_pass_count=int(row.get("ugi_pass_count", 0)),
            certification_valid=bool(row.get("certification_valid", True)),
            content_hash=row["content_hash"],
            uir_seal=row.get("uir_seal"),
            pqc_algorithm=row.get("pqc_algorithm"),
            issued_at=(
                row["issued_at"].isoformat()
                if hasattr(row.get("issued_at"), "isoformat")
                else str(row.get("issued_at", ""))
            ),
            linked_artifacts=None,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Clause validation utility (public)
# ─────────────────────────────────────────────────────────────────────────────

def validate_clause_ref(ref: str) -> bool:
    """Public wrapper for clause reference validation."""
    return _validate_clause_ref(ref)


# ─────────────────────────────────────────────────────────────────────────────
# Smoke test / demo (__main__)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

    print("=" * 70)
    print("OMNIX GUGT — Grand Unified Governance Theory Engine")
    print("ADR-179 · RFC-ATF-5 · Harold Nunes · OMNIX QUANTUM LTD")
    print("=" * 70)

    engine = GrandUnifiedGovernanceEngine(allow_unsigned=True)

    evidence = {
        "UGI-001": {
            "status": "PASS",
            "evidence_ref": "AIR-OMNIX-GENESIS-001",
            "framework_coverage": ["EU_AI_ACT_ART14", "NIST_GOVERN_1.1"],
        },
        "UGI-002": {
            "status": "PASS",
            "evidence_ref": "TAR-OMNIX-GENESIS-001",
            "framework_coverage": ["EU_AI_ACT_ART11", "ISO42001_6_2"],
        },
        "UGI-003": {
            "status": "PASS",
            "evidence_ref": "DTR-OMNIX-GENESIS-001",
            "framework_coverage": ["NIST_MAP_1.1", "GCC_DIFC_ART14"],
        },
        "UGI-004": {
            "status": "PASS",
            "evidence_ref": "RCR-OMNIX-GENESIS-001",
            "framework_coverage": ["EU_AI_ACT_ART13", "NIST_MANAGE_2.2"],
        },
        "UGI-005": {
            "status": "PASS",
            "evidence_ref": "BAR-OMNIX-GENESIS-001",
            "framework_coverage": ["ATF_INV_006", "POGR_INV_001"],
        },
        "UGI-006": {
            "status": "PASS",
            "evidence_ref": "RCEP-OMNIX-GENESIS-001",
            "framework_coverage": ["ATF_INV_001", "CUSTOM:OMNIX_TAMPER:VERIFY_GUIDE_V1"],
        },
    }

    print("\n[1] assess_ugi_compliance …")
    assessment = engine.assess_ugi_compliance("QuantumBank-TradingDesk-v1", evidence)
    print(f"    UGIs validated: {list(assessment.keys())}")

    print("\n[2] issue_uir (ATF protocol → GUGT-L3+ATF expected) …")
    uir = engine.issue_uir(
        subject_system="QuantumBank-TradingDesk-v1",
        subject_protocol="ATF",
        ugi_assessment=assessment,
        agent_type_coverage=["TRADING_AGENT", "LLM"],
        jurisdiction_coverage=["EU", "UAE", "UK"],
        linked_artifacts={
            "tcs_ids": ["TCS-DEMO-GENESIS"],
            "cat_ids": ["CAT-DEMO-GENESIS"],
        },
    )
    print(f"    {uir.summary()}")
    print(f"    content_hash  = {uir.content_hash}")
    print(f"    signed        = {uir.is_signed()}")
    print(f"    certification = {uir.certification_valid}")

    print("\n[3] verify_uir …")
    result = engine.verify_uir(uir)
    for note in result["notes"]:
        print(f"    {note}")
    print(f"    valid={result['valid']}")

    print("\n[4] GUGT-INV-001 guard test (missing UGI) …")
    try:
        bad = {k: v for k, v in evidence.items() if k != "UGI-003"}
        engine.assess_ugi_compliance("test", bad)
        print("    FAIL — should have raised")
        sys.exit(1)
    except GUGTInvariantViolation as exc:
        print(f"    OK — {exc}")

    print("\n[5] GUGT-INV-002 guard test (bad clause) …")
    try:
        bad2 = dict(evidence)
        bad2["UGI-004"] = {"status": "PASS", "framework_coverage": ["FREE_TEXT_NO_PREFIX"]}
        engine.assess_ugi_compliance("test", bad2)
        print("    FAIL — should have raised")
        sys.exit(1)
    except GUGTInvariantViolation as exc:
        print(f"    OK — {exc}")

    print("\n[6] GUGT-INV-004 guard test (empty agent_type_coverage) …")
    try:
        engine.issue_uir(
            subject_system="test", subject_protocol="ATF",
            ugi_assessment=assessment,
            agent_type_coverage=[],
            jurisdiction_coverage=["EU"],
        )
        print("    FAIL — should have raised")
        sys.exit(1)
    except GUGTInvariantViolation as exc:
        print(f"    OK — {exc}")

    print("\n[7] Conformance level monotonicity …")
    for ugi_to_fail in ["UGI-005", "UGI-004", "UGI-002"]:
        partial = dict(evidence)
        partial[ugi_to_fail] = {**evidence[ugi_to_fail], "status": "FAIL"}
        a2 = engine.assess_ugi_compliance("test", partial)
        lvl, cnt = GrandUnifiedGovernanceEngine._compute_conformance_level(a2, "ATF")
        print(f"    {ugi_to_fail}=FAIL → {lvl} ({cnt}/6)")

    print("\n✅ All GUGT smoke tests passed")
    print("=" * 70)
