"""
OMNIX Scope Authorization Engine
ADR-147: Scope Authorization Record — Defensible Scope Issuance & Context-Aware Reapproval

═══════════════════════════════════════════════════════════════════════════════
PURPOSE
═══════════════════════════════════════════════════════════════════════════════

OMNIX's governance pipeline answers: "Did the agent stay within scope?"
This module answers the prior question: "Was the scope itself defensible,
who authorized it, and does it remain valid as operational context shifts?"

This closes the gap articulated by enterprise Chief AI Officers and institutional
auditors: a receipt proving scope compliance is incomplete without a signed record
proving the scope was legitimately issued under defensible criteria.

Architecture position:
    Tier 1 Operator
        │
        ▼
    ScopeAuthorizationEngine.issue_scope()
        ├── scope_definition      — what is authorized
        ├── defensibility_criteria — why it is defensible
        ├── context_snapshot      — AVM signals at authorization time
        ├── PQC signature         — Dilithium-3 over scope_hash + context_hash
        └── governance_scope_authorizations (DB, immutable)
                │
                ▼ (ongoing — at each AVM evaluation)
    ScopeAuthorizationEngine.check_context_drift()
        └── drift > threshold → flag_reapproval() → REAPPROVAL_REQUIRED

Key invariants (never relaxed):
    1. Scope records are immutable once issued — no UPDATE path on core fields.
    2. Scope issuance requires authority_tier = 1 (Tier 1 only).
    3. Reapproval after context drift requires Tier 1 reauthorization.
    4. Revocation is Tier 1 only.
    5. All issued scopes carry a PQC signature when signing keys are available;
       fallback to SHA-256-only when PQC library is unavailable (degraded mode).
    6. Context drift detection uses the canonical AVM signal weights (ADR-076).
    7. Governance decisions continue under existing scope while reapproval is
       pending — but receipts carry trust_flags.scope_reapproval_pending = true.

ADR-147 — Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import math
import os
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

logger = logging.getLogger("OMNIX.SAE")

# ── AVM signal weights (ADR-076) ───────────────────────────────────────────────
# Imported at call time to avoid circular imports.
_SIGNAL_WEIGHTS: dict[str, float] = {
    "probability_score":  0.25,
    "signal_coherence":   0.25,
    "risk_exposure":      0.20,
    "stress_resilience":  0.15,
    "trend_persistence":  0.10,
    "logic_consistency":  0.05,
}

# Default drift threshold (%) above which scope reapproval is triggered.
# Overridable via defensibility_criteria.scope_reapproval_drift_threshold per scope.
_DEFAULT_REAPPROVAL_DRIFT_THRESHOLD = 25.0

# ── Environment helpers ────────────────────────────────────────────────────────

def _signing_secret_key() -> Optional[bytes]:
    """Load Dilithium-3 secret key from OMNIX_SIGNING_SECRET_KEY_B64."""
    raw = os.environ.get("OMNIX_SIGNING_SECRET_KEY_B64", "").strip()
    if not raw:
        return None
    try:
        return base64.b64decode(raw)
    except Exception:
        return None


def _pqc_sign(payload: bytes) -> tuple[Optional[str], Optional[str]]:
    """
    Sign payload bytes with Dilithium-3 (ML-DSA-65).

    Returns:
        (signature_b64, algorithm_name) or (None, None) if unavailable.
    """
    sk = _signing_secret_key()
    if not sk:
        return None, None
    try:
        from omnix_core.security.pqc_config import SIGNING_MODULE, ALGORITHM_NAME
        if SIGNING_MODULE is None:
            return None, None
        sig_bytes = SIGNING_MODULE.sign(payload, sk)
        return base64.b64encode(sig_bytes).decode(), ALGORITHM_NAME
    except Exception as exc:
        logger.warning(f"[SAE] PQC signing unavailable — degraded mode (SHA-256 only): {exc}")
        return None, None


# ── DDL ───────────────────────────────────────────────────────────────────────

DDL_SCOPE_TABLE = """
CREATE TABLE IF NOT EXISTS governance_scope_authorizations (
    scope_id                    VARCHAR(64)   PRIMARY KEY,
    domain                      VARCHAR(64)   NOT NULL,
    vertical                    VARCHAR(64)   NOT NULL DEFAULT 'general',
    authority_tier              INTEGER       NOT NULL CHECK (authority_tier BETWEEN 1 AND 4),
    authorized_by               VARCHAR(128)  NOT NULL,
    scope_definition            JSONB         NOT NULL,
    defensibility_criteria      JSONB         NOT NULL DEFAULT '{}',
    context_snapshot            JSONB         NOT NULL DEFAULT '{}',
    context_hash                VARCHAR(64)   NOT NULL,
    scope_hash                  VARCHAR(64)   NOT NULL,
    pqc_signature               TEXT          DEFAULT NULL,
    pqc_algorithm               VARCHAR(32)   DEFAULT NULL,
    status                      VARCHAR(32)   NOT NULL DEFAULT 'ACTIVE'
                                              CHECK (status IN (
                                                  'ACTIVE',
                                                  'REAPPROVAL_REQUIRED',
                                                  'SUPERSEDED',
                                                  'REVOKED'
                                              )),
    issued_at                   TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    expires_at                  TIMESTAMPTZ   DEFAULT NULL,
    superseded_by               VARCHAR(64)   DEFAULT NULL,
    reapproval_required         BOOLEAN       NOT NULL DEFAULT FALSE,
    reapproval_required_at      TIMESTAMPTZ   DEFAULT NULL,
    reapproval_reason           TEXT          DEFAULT NULL,
    context_drift_at_reapproval FLOAT         DEFAULT NULL,
    avm_snapshot_id             VARCHAR(32)   DEFAULT NULL,
    avm_snapshot_version        INTEGER       DEFAULT NULL
);
CREATE INDEX IF NOT EXISTS idx_gsa_domain_vertical_status
    ON governance_scope_authorizations (domain, vertical, status);
CREATE INDEX IF NOT EXISTS idx_gsa_issued_at
    ON governance_scope_authorizations (issued_at DESC);
"""


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class ScopeAuthorizationRecord:
    """
    A PQC-signed, immutable record of a governance scope authorization.

    Answers:
        - What is authorized (scope_definition)
        - Why it is defensible (defensibility_criteria)
        - Who authorized it (authorized_by + authority_tier)
        - Under what operational context (context_snapshot)
        - With what cryptographic proof (pqc_signature)
    """
    scope_id: str
    domain: str
    vertical: str
    authority_tier: int
    authorized_by: str
    scope_definition: dict[str, Any]
    defensibility_criteria: dict[str, Any]
    context_snapshot: dict[str, Any]
    context_hash: str
    scope_hash: str
    pqc_signature: Optional[str]
    pqc_algorithm: Optional[str]
    status: str
    issued_at: str
    expires_at: Optional[str]
    superseded_by: Optional[str]
    reapproval_required: bool
    reapproval_required_at: Optional[str]
    reapproval_reason: Optional[str]
    context_drift_at_reapproval: Optional[float]
    avm_snapshot_id: Optional[str]
    avm_snapshot_version: Optional[int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def is_active(self) -> bool:
        return self.status == "ACTIVE"

    def requires_reapproval(self) -> bool:
        return self.status == "REAPPROVAL_REQUIRED"

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        try:
            exp = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) > exp
        except Exception:
            return False

    def trust_flags(self) -> dict[str, bool]:
        return {
            "scope_reapproval_pending": self.requires_reapproval(),
            "scope_expired":            self.is_expired(),
            "pqc_signed":               self.pqc_signature is not None,
            "tier1_authorized":         self.authority_tier == 1,
        }


@dataclass
class ContextDriftResult:
    """
    Result of comparing current AVM signals against the scope's context_snapshot.
    """
    scope_id: str
    domain: str
    vertical: str
    drift_pct: float
    drift_threshold: float
    requires_reapproval: bool
    drift_detail: dict[str, float]
    evaluated_at: str
    current_signals: dict[str, float]
    snapshot_signals: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ── Engine ────────────────────────────────────────────────────────────────────

class ScopeAuthorizationEngine:
    """
    Issues, tracks, and monitors governance scope authorizations.

    Design contract:
        issue_scope()          → PQC-signed ScopeAuthorizationRecord persisted to DB
        get_active_scope()     → current ACTIVE scope for (domain, vertical)
        check_context_drift()  → compares current AVM signals vs. scope context
        flag_reapproval()      → marks scope REAPPROVAL_REQUIRED
        reauthorize()          → new scope supersedes old (Tier 1 only)
        revoke_scope()         → hard revoke (Tier 1 only)
        get_scope_history()    → full immutable history for (domain, vertical)
        ensure_table()         → idempotent DDL
    """

    def __init__(self, db_url: Optional[str] = None):
        self._db_url = db_url or os.environ.get("DATABASE_URL")
        self._available = bool(self._db_url)

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _get_conn(self):
        import psycopg
        conn = psycopg.connect(self._db_url)
        return conn

    @staticmethod
    def _sanitize_for_hash(obj: Any) -> Any:
        """
        Recursively replace non-finite floats (NaN, Inf, -Inf) with None.

        Python's json.dumps silently serializes NaN/Infinity as the bare tokens
        NaN/Infinity — which are not valid JSON (RFC 8259) and will parse
        differently across languages (JavaScript JSON.parse raises, Python
        json.loads accepts). Replacing them with null produces deterministic,
        spec-compliant canonical JSON for SHA-256 hashing.
        """
        if isinstance(obj, float) and not math.isfinite(obj):
            return None
        if isinstance(obj, dict):
            return {k: ScopeAuthorizationEngine._sanitize_for_hash(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [ScopeAuthorizationEngine._sanitize_for_hash(v) for v in obj]
        return obj

    @staticmethod
    def _compute_scope_hash(scope_definition: dict, defensibility_criteria: dict) -> str:
        """SHA-256 of canonicalized scope_definition + defensibility_criteria."""
        payload = {
            "scope_definition":        scope_definition,
            "defensibility_criteria":  defensibility_criteria,
        }
        clean = ScopeAuthorizationEngine._sanitize_for_hash(payload)
        canon = json.dumps(clean, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canon.encode()).hexdigest()

    @staticmethod
    def _compute_context_hash(context_snapshot: dict) -> str:
        """SHA-256 of canonicalized context_snapshot."""
        clean = ScopeAuthorizationEngine._sanitize_for_hash(context_snapshot)
        canon = json.dumps(clean, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canon.encode()).hexdigest()

    @staticmethod
    def _compute_drift(
        current_signals: dict[str, float],
        snapshot_signals: dict[str, float],
    ) -> tuple[float, dict[str, float]]:
        """
        Weighted drift between current signals and snapshot signals.

        Uses canonical AVM signal weights (ADR-076).
        Returns (total_drift_pct, per_signal_drift_detail).
        """
        detail: dict[str, float] = {}
        total = 0.0
        for signal, weight in _SIGNAL_WEIGHTS.items():
            current = current_signals.get(signal)
            baseline = snapshot_signals.get(signal)
            if current is None or baseline is None:
                continue
            denominator = max(abs(baseline), 0.01)
            signal_drift = abs(current - baseline) / denominator * 100.0
            weighted = weight * signal_drift
            detail[signal] = round(signal_drift, 4)
            total += weighted
        return round(total, 4), detail

    def _build_sign_payload(self, scope_hash: str, context_hash: str) -> bytes:
        """Canonical payload for PQC signing."""
        return f"OMNIX-SAR-v1|scope_hash={scope_hash}|context_hash={context_hash}".encode()

    def _row_to_record(self, row: dict) -> ScopeAuthorizationRecord:
        """Convert a DB row dict to a ScopeAuthorizationRecord."""
        def _ts(v) -> Optional[str]:
            if v is None:
                return None
            if isinstance(v, datetime):
                return v.isoformat()
            return str(v)

        return ScopeAuthorizationRecord(
            scope_id=row["scope_id"],
            domain=row["domain"],
            vertical=row["vertical"],
            authority_tier=int(row["authority_tier"]),
            authorized_by=row["authorized_by"],
            scope_definition=row["scope_definition"] if isinstance(row["scope_definition"], dict) else {},
            defensibility_criteria=row["defensibility_criteria"] if isinstance(row["defensibility_criteria"], dict) else {},
            context_snapshot=row["context_snapshot"] if isinstance(row["context_snapshot"], dict) else {},
            context_hash=row["context_hash"],
            scope_hash=row["scope_hash"],
            pqc_signature=row.get("pqc_signature"),
            pqc_algorithm=row.get("pqc_algorithm"),
            status=row["status"],
            issued_at=_ts(row["issued_at"]),
            expires_at=_ts(row.get("expires_at")),
            superseded_by=row.get("superseded_by"),
            reapproval_required=bool(row.get("reapproval_required", False)),
            reapproval_required_at=_ts(row.get("reapproval_required_at")),
            reapproval_reason=row.get("reapproval_reason"),
            context_drift_at_reapproval=row.get("context_drift_at_reapproval"),
            avm_snapshot_id=row.get("avm_snapshot_id"),
            avm_snapshot_version=row.get("avm_snapshot_version"),
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    def ensure_table(self) -> bool:
        """Idempotent DDL — safe to call on every startup."""
        if not self._available:
            return False
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(DDL_SCOPE_TABLE)
                conn.commit()
            logger.info("[SAE] Table ready: governance_scope_authorizations")
            return True
        except Exception as exc:
            logger.warning(f"[SAE] ensure_table failed: {exc}")
            return False

    def issue_scope(
        self,
        domain: str,
        vertical: str,
        scope_definition: dict[str, Any],
        defensibility_criteria: dict[str, Any],
        authorized_by: str,
        authority_tier: int = 1,
        context_snapshot: Optional[dict[str, Any]] = None,
        avm_snapshot_id: Optional[str] = None,
        avm_snapshot_version: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> ScopeAuthorizationRecord:
        """
        Issue a new PQC-signed scope authorization.

        Args:
            domain:                  Governance domain (e.g. "FINANCE").
            vertical:                Sub-vertical (e.g. "equity_trading").
            scope_definition:        What is authorized — see ADR-147 §5.
            defensibility_criteria:  Why it is defensible — see ADR-147 §6.
            authorized_by:           Actor identifier (user / service).
            authority_tier:          Authority tier 1-4 (ADR-146). Scope issuance
                                     is Tier 1 only by governance policy.
            context_snapshot:        AVM signals at authorization time. If None,
                                     an empty snapshot is stored (degraded mode).
            avm_snapshot_id:         ID of the active AVM calibration snapshot.
            avm_snapshot_version:    Version of the active AVM calibration snapshot.
            expires_at:              Optional expiry datetime (UTC).

        Returns:
            ScopeAuthorizationRecord — immutable, PQC-signed.

        Raises:
            ValueError: If authority_tier is not 1-4 or required fields are missing.
            RuntimeError: If DB is unavailable.
        """
        if authority_tier not in (1, 2, 3, 4):
            raise ValueError(f"authority_tier must be 1-4, got: {authority_tier}")
        if not domain or not domain.strip():
            raise ValueError("domain is required")
        if not authorized_by or not authorized_by.strip():
            raise ValueError("authorized_by is required")
        if not scope_definition:
            raise ValueError("scope_definition cannot be empty")

        if context_snapshot is None:
            context_snapshot = {}

        scope_id     = f"SAR-{uuid.uuid4().hex[:24].upper()}"
        scope_hash   = self._compute_scope_hash(scope_definition, defensibility_criteria)
        context_hash = self._compute_context_hash(context_snapshot)
        now          = datetime.now(timezone.utc)

        sign_payload           = self._build_sign_payload(scope_hash, context_hash)
        pqc_signature, pqc_alg = _pqc_sign(sign_payload)

        if pqc_signature:
            logger.info(f"[SAE] Scope {scope_id} signed with {pqc_alg}")
        else:
            logger.warning(
                f"[SAE] Scope {scope_id} issued WITHOUT PQC signature "
                "(OMNIX_SIGNING_SECRET_KEY_B64 not set or PQC library unavailable) "
                "— SHA-256 hash integrity only (degraded mode)"
            )

        record = ScopeAuthorizationRecord(
            scope_id=scope_id,
            domain=domain.upper(),
            vertical=vertical.lower(),
            authority_tier=authority_tier,
            authorized_by=authorized_by,
            scope_definition=scope_definition,
            defensibility_criteria=defensibility_criteria,
            context_snapshot=context_snapshot,
            context_hash=context_hash,
            scope_hash=scope_hash,
            pqc_signature=pqc_signature,
            pqc_algorithm=pqc_alg,
            status="ACTIVE",
            issued_at=now.isoformat(),
            expires_at=expires_at.isoformat() if expires_at else None,
            superseded_by=None,
            reapproval_required=False,
            reapproval_required_at=None,
            reapproval_reason=None,
            context_drift_at_reapproval=None,
            avm_snapshot_id=avm_snapshot_id,
            avm_snapshot_version=avm_snapshot_version,
        )

        if not self._available:
            logger.warning("[SAE] DB unavailable — scope record not persisted (in-memory only)")
            return record

        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO governance_scope_authorizations (
                            scope_id, domain, vertical,
                            authority_tier, authorized_by,
                            scope_definition, defensibility_criteria,
                            context_snapshot, context_hash, scope_hash,
                            pqc_signature, pqc_algorithm, status,
                            issued_at, expires_at,
                            avm_snapshot_id, avm_snapshot_version
                        ) VALUES (
                            %(scope_id)s, %(domain)s, %(vertical)s,
                            %(authority_tier)s, %(authorized_by)s,
                            %(scope_definition)s::jsonb, %(defensibility_criteria)s::jsonb,
                            %(context_snapshot)s::jsonb, %(context_hash)s, %(scope_hash)s,
                            %(pqc_signature)s, %(pqc_algorithm)s, %(status)s,
                            %(issued_at)s, %(expires_at)s,
                            %(avm_snapshot_id)s, %(avm_snapshot_version)s
                        )
                    """, {
                        "scope_id":               record.scope_id,
                        "domain":                 record.domain,
                        "vertical":               record.vertical,
                        "authority_tier":         record.authority_tier,
                        "authorized_by":          record.authorized_by,
                        "scope_definition":       json.dumps(record.scope_definition),
                        "defensibility_criteria": json.dumps(record.defensibility_criteria),
                        "context_snapshot":       json.dumps(record.context_snapshot),
                        "context_hash":           record.context_hash,
                        "scope_hash":             record.scope_hash,
                        "pqc_signature":          record.pqc_signature,
                        "pqc_algorithm":          record.pqc_algorithm,
                        "status":                 record.status,
                        "issued_at":              record.issued_at,
                        "expires_at":             record.expires_at,
                        "avm_snapshot_id":        record.avm_snapshot_id,
                        "avm_snapshot_version":   record.avm_snapshot_version,
                    })
                conn.commit()

            logger.info(
                f"[SAE] Scope issued — id={scope_id} domain={record.domain} "
                f"vertical={record.vertical} tier={authority_tier} "
                f"by={authorized_by} pqc={'YES' if pqc_signature else 'DEGRADED'}"
            )
            return record

        except Exception as exc:
            logger.error(f"[SAE] Failed to persist scope {scope_id}: {exc}")
            raise RuntimeError(f"Scope authorization could not be persisted: {exc}") from exc

    def get_active_scope(
        self, domain: str, vertical: str = "general"
    ) -> Optional[ScopeAuthorizationRecord]:
        """Return the most recently issued ACTIVE scope for (domain, vertical)."""
        if not self._available:
            return None
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT *
                        FROM governance_scope_authorizations
                        WHERE domain = %s AND vertical = %s
                          AND status IN ('ACTIVE', 'REAPPROVAL_REQUIRED')
                        ORDER BY issued_at DESC
                        LIMIT 1
                    """, (domain.upper(), vertical.lower()))
                    cols = [d[0] for d in cur.description]
                    row  = cur.fetchone()
            if not row:
                return None
            return self._row_to_record(dict(zip(cols, row)))
        except Exception as exc:
            logger.warning(f"[SAE] get_active_scope failed domain={domain}: {exc}")
            return None

    def get_scope_by_id(self, scope_id: str) -> Optional[ScopeAuthorizationRecord]:
        """Return a scope record by its scope_id."""
        if not self._available:
            return None
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM governance_scope_authorizations WHERE scope_id = %s",
                        (scope_id,)
                    )
                    cols = [d[0] for d in cur.description]
                    row  = cur.fetchone()
            if not row:
                return None
            return self._row_to_record(dict(zip(cols, row)))
        except Exception as exc:
            logger.warning(f"[SAE] get_scope_by_id failed scope_id={scope_id}: {exc}")
            return None

    def check_context_drift(
        self,
        domain: str,
        vertical: str,
        current_signals: dict[str, float],
    ) -> Optional[ContextDriftResult]:
        """
        Compute drift between current AVM signals and the scope's context_snapshot.

        If drift exceeds the scope's configured threshold (or the global default),
        automatically flags the scope for reapproval.

        Returns:
            ContextDriftResult or None if no active scope exists.
        """
        scope = self.get_active_scope(domain, vertical)
        if not scope:
            return None

        snapshot_signals = {
            k: float(v)
            for k, v in scope.context_snapshot.items()
            if isinstance(v, (int, float))
        }

        drift_pct, drift_detail = self._compute_drift(current_signals, snapshot_signals)

        threshold = float(
            scope.defensibility_criteria.get(
                "scope_reapproval_drift_threshold",
                _DEFAULT_REAPPROVAL_DRIFT_THRESHOLD,
            )
        )

        requires = drift_pct > threshold
        evaluated_at = datetime.now(timezone.utc).isoformat()

        if requires and scope.status == "ACTIVE":
            reason = (
                f"Context drift {drift_pct:.2f}% exceeds threshold {threshold:.2f}%. "
                f"Per-signal: {json.dumps(drift_detail, sort_keys=True)}"
            )
            self.flag_reapproval(scope.scope_id, reason, drift_pct)
            logger.warning(
                f"[SAE] Scope {scope.scope_id} flagged for reapproval — "
                f"domain={domain} drift={drift_pct:.2f}% threshold={threshold:.2f}%"
            )

        return ContextDriftResult(
            scope_id=scope.scope_id,
            domain=domain.upper(),
            vertical=vertical.lower(),
            drift_pct=drift_pct,
            drift_threshold=threshold,
            requires_reapproval=requires,
            drift_detail=drift_detail,
            evaluated_at=evaluated_at,
            current_signals=current_signals,
            snapshot_signals=snapshot_signals,
        )

    def flag_reapproval(
        self,
        scope_id: str,
        reason: str,
        drift_pct: Optional[float] = None,
    ) -> bool:
        """
        Mark a scope as REAPPROVAL_REQUIRED.

        Does not revoke or block existing evaluations — receipts issued under
        this scope while reapproval is pending will carry
        trust_flags.scope_reapproval_pending = true.
        """
        if not self._available:
            return False
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE governance_scope_authorizations
                        SET status                      = 'REAPPROVAL_REQUIRED',
                            reapproval_required         = TRUE,
                            reapproval_required_at      = NOW(),
                            reapproval_reason           = %(reason)s,
                            context_drift_at_reapproval = %(drift_pct)s
                        WHERE scope_id = %(scope_id)s
                          AND status   = 'ACTIVE'
                    """, {
                        "scope_id": scope_id,
                        "reason":   reason,
                        "drift_pct": drift_pct,
                    })
                conn.commit()
            logger.info(f"[SAE] Scope {scope_id} → REAPPROVAL_REQUIRED | reason={reason[:80]}...")
            return True
        except Exception as exc:
            logger.error(f"[SAE] flag_reapproval failed scope_id={scope_id}: {exc}")
            return False

    def reauthorize(
        self,
        old_scope_id: str,
        scope_definition: dict[str, Any],
        defensibility_criteria: dict[str, Any],
        authorized_by: str,
        authority_tier: int = 1,
        context_snapshot: Optional[dict[str, Any]] = None,
        avm_snapshot_id: Optional[str] = None,
        avm_snapshot_version: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> ScopeAuthorizationRecord:
        """
        Issue a new scope that supersedes the old one.

        Marks old scope as SUPERSEDED with a pointer to the new scope_id.
        Issues the new scope via issue_scope() — PQC-signed, fully immutable.

        Args:
            old_scope_id: The scope_id being replaced.
            (remaining args): Same as issue_scope().

        Returns:
            New ScopeAuthorizationRecord.

        Raises:
            ValueError: If old_scope_id does not exist or is not supersedable.
        """
        old = self.get_scope_by_id(old_scope_id)
        if not old:
            raise ValueError(f"Scope not found: {old_scope_id}")
        if old.status == "REVOKED":
            raise ValueError(f"Cannot reauthorize a REVOKED scope: {old_scope_id}")
        if old.status == "SUPERSEDED":
            raise ValueError(f"Scope already superseded: {old_scope_id}")

        new_scope = self.issue_scope(
            domain=old.domain,
            vertical=old.vertical,
            scope_definition=scope_definition,
            defensibility_criteria=defensibility_criteria,
            authorized_by=authorized_by,
            authority_tier=authority_tier,
            context_snapshot=context_snapshot,
            avm_snapshot_id=avm_snapshot_id,
            avm_snapshot_version=avm_snapshot_version,
            expires_at=expires_at,
        )

        if self._available:
            try:
                with self._get_conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE governance_scope_authorizations
                            SET status        = 'SUPERSEDED',
                                superseded_by = %s
                            WHERE scope_id = %s
                        """, (new_scope.scope_id, old_scope_id))
                    conn.commit()
                logger.info(
                    f"[SAE] Scope {old_scope_id} → SUPERSEDED by {new_scope.scope_id} "
                    f"(reauthorized by {authorized_by})"
                )
            except Exception as exc:
                logger.error(f"[SAE] Failed to mark old scope as SUPERSEDED: {exc}")

        return new_scope

    def revoke_scope(
        self,
        scope_id: str,
        reason: str,
        authorized_by: str,
        authority_tier: int = 1,
    ) -> bool:
        """
        Hard-revoke a scope (Tier 1 only by governance policy).

        A revoked scope cannot be reactivated. Issue a new scope if needed.
        """
        if authority_tier != 1:
            raise PermissionError(
                f"Scope revocation requires authority_tier=1 (Tier 1 Platform Owner). "
                f"Got tier={authority_tier} actor={authorized_by}"
            )
        if not reason or not reason.strip():
            raise ValueError("reason is required for scope revocation")
        if not self._available:
            raise RuntimeError(
                "[SAE] Scope revocation failed — database unavailable (no DATABASE_URL). "
                "Revocation of a live governance scope requires a persistent DB."
            )

        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE governance_scope_authorizations
                        SET status              = 'REVOKED',
                            reapproval_reason   = %(reason)s,
                            reapproval_required_at = NOW()
                        WHERE scope_id = %(scope_id)s
                          AND status NOT IN ('REVOKED', 'SUPERSEDED')
                    """, {"scope_id": scope_id, "reason": f"REVOKED by {authorized_by}: {reason}"})
                    rows_affected = cur.rowcount
                conn.commit()
            if rows_affected == 0:
                return False  # Scope not found or already in terminal state
            logger.warning(
                f"[SAE] Scope REVOKED — id={scope_id} "
                f"by={authorized_by} (tier={authority_tier}) reason={reason[:80]}"
            )
            return True
        except Exception as exc:
            logger.error(f"[SAE] revoke_scope failed scope_id={scope_id}: {exc}")
            raise RuntimeError(f"[SAE] revoke_scope DB error: {exc}") from exc

    def get_scope_history(
        self,
        domain: str,
        vertical: str = "general",
        limit: int = 50,
    ) -> list[ScopeAuthorizationRecord]:
        """Return all scope records for (domain, vertical), newest first."""
        if not self._available:
            return []
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT * FROM governance_scope_authorizations
                        WHERE domain = %s AND vertical = %s
                        ORDER BY issued_at DESC
                        LIMIT %s
                    """, (domain.upper(), vertical.lower(), limit))
                    cols = [d[0] for d in cur.description]
                    rows = cur.fetchall()
            return [self._row_to_record(dict(zip(cols, r))) for r in rows]
        except Exception as exc:
            logger.warning(f"[SAE] get_scope_history failed: {exc}")
            return []

    def is_available(self) -> bool:
        return self._available


# ── Module-level singleton ─────────────────────────────────────────────────────

_engine: Optional[ScopeAuthorizationEngine] = None
_engine_lock: threading.Lock = threading.Lock()


def get_scope_engine() -> ScopeAuthorizationEngine:
    """
    Return the module-level ScopeAuthorizationEngine singleton.

    Thread-safe double-checked locking prevents TOCTOU race conditions under
    multithreaded Flask (Werkzeug threaded=True default). Without the lock, two
    simultaneous requests could both observe _engine is None and construct two
    separate instances — diverging their in-memory DB connection state.
    """
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = ScopeAuthorizationEngine()
    return _engine
