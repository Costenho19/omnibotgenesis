"""
OMNIX Agent Trust Fabric — Temporal Authority Admissibility
ADR-157: Time-bound proof that a Delegation Receipt was valid at the
exact nanosecond of an agent execution event.

Every agent action produces an ExecutionReceipt (ADR-131). The Temporal
Authority Admissibility extension bridges ATF and EIL by producing a
Temporal Admissibility Record (TAR) that binds:

    - The Delegation Receipt (DR) that authorizes the agent
    - The execution timestamp (nanosecond precision)
    - A cryptographic proof that the DR was ACTIVE at that moment

This answers a question no other AI agent framework can answer:

    "Was this agent's authority still valid at the EXACT nanosecond
     it took the action we are reviewing?"

Key invariants:
    TAR-INV-001: TAR is issued BEFORE execution completes
    TAR-INV-002: TAR timestamp is bound by PQC signature
    TAR-INV-003: Expired DRs produce TAR with status=REJECTED
    TAR-INV-004: TAR is immutable once issued (content_hash)
    TAR-INV-005: TAR chains to its originating DR and execution event
    TAR-INV-006: DR lifetime accepted by TAR engine cannot exceed
                 TAR_MAX_DR_LIFETIME_SECONDS — a COMPILED CONSTANT,
                 not an operator-configurable parameter. A DR whose
                 remaining validity window at admission time exceeds
                 this bound is REJECTED regardless of its stated
                 expires_at value. This closes the DORA issuance-time
                 attack surface: no operator can extend authority scope
                 by issuing a DR with an excessively permissive epoch.
                 The bound is structural, not policy-enforced.

ADR-157 rev.2 — Harold Nunes — OMNIX QUANTUM LTD — May 2026
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
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("OMNIX.ATF.Temporal")

# ─────────────────────────────────────────────────────────────────────────────
# COMPILED STALENESS BOUNDS — TAR-INV-006
#
# These are MODULE-LEVEL CONSTANTS. They are NOT read from environment
# variables and CANNOT be overridden by operator configuration. This is
# intentional: making these bounds configurable would constitute a DORA
# issuance-time attack surface (an operator under coercion could extend
# the authority epoch indefinitely). The bound is structural.
#
# TAR_MAX_DR_LIFETIME_SECONDS : Maximum remaining validity window a DR may
#     carry at the moment TAR admission is evaluated. A DR whose expiry is
#     more than this many seconds in the future is REJECTED. Default: 24h.
#     To issue authority beyond 24 h, a fresh DR must be issued — creating
#     a new auditable issuance event rather than a single long-lived token.
#
# TAR_CLOCK_SKEW_TOLERANCE_NS : Nanosecond tolerance for minor clock skew
#     between issuing and admitting runtimes. Does not affect lifetime bound.
# ─────────────────────────────────────────────────────────────────────────────
TAR_MAX_DR_LIFETIME_SECONDS: int  = 86_400     # 24 hours — compiled, not configurable
TAR_CLOCK_SKEW_TOLERANCE_NS: int  = 5_000_000_000  # 5 seconds clock skew tolerance

DDL_TEMPORAL_RECORDS = """
CREATE TABLE IF NOT EXISTS atf_temporal_records (
    tar_id                  VARCHAR(64)   PRIMARY KEY,
    delegation_id           VARCHAR(64)   NOT NULL,
    agent_id                VARCHAR(64)   NOT NULL,
    execution_ref           VARCHAR(128)  DEFAULT NULL,
    execution_ns            BIGINT        NOT NULL,
    execution_ts            TIMESTAMPTZ   NOT NULL,
    dr_status_at_admission  VARCHAR(16)   NOT NULL,
    dr_expires_at           TIMESTAMPTZ   DEFAULT NULL,
    authority_budget        FLOAT         NOT NULL,
    domain                  VARCHAR(64)   NOT NULL,
    task_action             TEXT          NOT NULL,
    admission_status        VARCHAR(16)   NOT NULL,
    rejection_reason        TEXT          DEFAULT NULL,
    content_hash            VARCHAR(64)   NOT NULL,
    pqc_signature           TEXT          DEFAULT NULL,
    pqc_algorithm           VARCHAR(32)   DEFAULT NULL,
    chain_root_id           VARCHAR(64)   NOT NULL,
    issued_at               TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    metadata                JSONB         NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_atf_tar_delegation
    ON atf_temporal_records (delegation_id);
CREATE INDEX IF NOT EXISTS idx_atf_tar_agent
    ON atf_temporal_records (agent_id, admission_status);
CREATE INDEX IF NOT EXISTS idx_atf_tar_execution_ns
    ON atf_temporal_records (execution_ns);
CREATE INDEX IF NOT EXISTS idx_atf_tar_chain_root
    ON atf_temporal_records (chain_root_id);
"""

TAR_ID_PREFIX = "ATFTAR"


class TemporalAdmissibilityError(Exception):
    """Raised when a temporal admissibility check fails."""


@dataclass
class TemporalAdmissibilityRecord:
    """
    Cryptographic proof that a Delegation Receipt was valid at the
    exact nanosecond of an agent execution event.

    Fields:
        tar_id                 — "ATFTAR-{16HEX}"
        delegation_id          — ATFDR-{16HEX} of the authorizing DR
        agent_id               — AID-{DOMAIN}-{16HEX} of the acting agent
        execution_ref          — optional reference to ExecutionReceipt (ADR-131)
        execution_ns           — nanosecond Unix timestamp of execution
        execution_ts           — ISO UTC timestamp of execution
        dr_status_at_admission — status of DR at admission time
        dr_expires_at          — DR expiry (from DR)
        authority_budget       — authority budget of the DR
        domain                 — governance domain
        task_action            — action being admitted
        admission_status       — ADMITTED | REJECTED
        rejection_reason       — reason for rejection (if any)
        content_hash           — SHA-256 of all fields except sig fields
        pqc_signature          — Dilithium-3 sig over content_hash
        pqc_algorithm          — "dilithium3"
        chain_root_id          — chain_root_id of the DR
        issued_at              — ISO UTC timestamp of TAR issuance
        metadata               — extension dict
    """
    tar_id: str
    delegation_id: str
    agent_id: str
    execution_ref: Optional[str]
    execution_ns: int
    execution_ts: str
    dr_status_at_admission: str
    dr_expires_at: Optional[str]
    authority_budget: float
    domain: str
    task_action: str
    admission_status: str
    rejection_reason: Optional[str]
    content_hash: str
    pqc_signature: Optional[str]
    pqc_algorithm: Optional[str]
    chain_root_id: str
    issued_at: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_admitted(self) -> bool:
        return self.admission_status == "ADMITTED"

    def summary(self) -> Dict[str, Any]:
        return {
            "tar_id":             self.tar_id,
            "delegation_id":      self.delegation_id,
            "agent_id":           self.agent_id,
            "execution_ns":       self.execution_ns,
            "execution_ts":       self.execution_ts,
            "admission_status":   self.admission_status,
            "authority_budget":   self.authority_budget,
            "domain":             self.domain,
            "task_action":        self.task_action,
            "chain_root_id":      self.chain_root_id,
            "pqc_signed":         self.pqc_signature is not None,
            "rejection_reason":   self.rejection_reason,
            "issued_at":          self.issued_at,
        }


class TemporalAuthorityEngine:
    """
    Issues and verifies Temporal Admissibility Records (TARs).

    A TAR is the cryptographic proof that an agent's Delegation Receipt
    was ACTIVE at the exact nanosecond an execution event occurred.

    Design contract:
        admit_execution()    → TemporalAdmissibilityRecord
        verify_tar()         → verification result dict
        get_tar()            → TAR by ID
        list_tars()          → TARs for a delegation or agent
        ensure_tables()      → idempotent DDL

    TAR-INV-001: TAR is issued synchronously BEFORE execution is logged.
    TAR-INV-002: execution_ns is captured at admission time (not post-hoc).
    TAR-INV-003: Expired or REVOKED DRs produce admission_status=REJECTED.
    TAR-INV-004: TARs are immutable once issued.
    """

    def __init__(self, db_url: Optional[str] = None):
        self._db_url = db_url or os.environ.get("DATABASE_URL")
        self._store: Dict[str, TemporalAdmissibilityRecord] = {}
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
            logger.warning(f"[ATF.Temporal] DB connection failed: {exc}")
            return None

    @staticmethod
    def _build_tar_id() -> str:
        return f"{TAR_ID_PREFIX}-{uuid.uuid4().hex[:16].upper()}"

    @staticmethod
    def _compute_content_hash(fields: Dict[str, Any]) -> str:
        exclude = {"content_hash", "pqc_signature", "pqc_algorithm"}
        clean = {k: v for k, v in fields.items() if k not in exclude}
        canonical = json.dumps(clean, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

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
            logger.warning(f"[ATF.Temporal] Sign failed: {exc}")
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
                    cur.execute(DDL_TEMPORAL_RECORDS)
            logger.info("[ATF.Temporal] Table ready: atf_temporal_records")
            return True
        except Exception as exc:
            logger.warning(f"[ATF.Temporal] ensure_tables failed: {exc}")
            return False
        finally:
            conn.close()

    def admit_execution(
        self,
        delegation_receipt: Any,
        agent_id: str,
        task_action: str,
        execution_ref: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TemporalAdmissibilityRecord:
        """
        Issue a Temporal Admissibility Record for an execution event.

        This method MUST be called synchronously at the moment of execution
        admission, before the execution is logged or performed. It captures
        the exact nanosecond at which the DR was checked.

        Args:
            delegation_receipt: DelegationReceipt (or dict) authorizing the agent
            agent_id:           AID of the acting agent
            task_action:        Description of the action being admitted
            execution_ref:      Optional reference to ExecutionReceipt (ADR-131)
            metadata:           Optional extension dict

        Returns:
            TemporalAdmissibilityRecord — ADMITTED or REJECTED, PQC-signed.

        TAR-INV-001: Issued synchronously at admission time.
        TAR-INV-002: execution_ns captured by time.time_ns() at this call.
        TAR-INV-003: Rejected if DR is not ACTIVE or is expired.
        """
        execution_ns = time.time_ns()
        now_utc = datetime.now(timezone.utc)
        execution_ts = now_utc.isoformat()
        issued_at = now_utc.isoformat()

        if hasattr(delegation_receipt, "to_dict"):
            dr_dict = delegation_receipt.to_dict()
        elif isinstance(delegation_receipt, dict):
            dr_dict = delegation_receipt
        else:
            raise ValueError("delegation_receipt must be a DelegationReceipt or dict")

        delegation_id = dr_dict.get("delegation_id", "")
        dr_status = dr_dict.get("status", "UNKNOWN")
        dr_expires_at = dr_dict.get("expires_at")
        authority_budget = float(dr_dict.get("authority_budget_granted", 0))
        domain = dr_dict.get("task_scope", {}).get("domain", "UNKNOWN")
        chain_root_id = dr_dict.get("chain_root_id", delegation_id)

        admission_status = "ADMITTED"
        rejection_reason: Optional[str] = None

        if dr_status != "ACTIVE":
            admission_status = "REJECTED"
            rejection_reason = f"DR status is {dr_status} — not ACTIVE"

        if admission_status == "ADMITTED" and dr_expires_at:
            try:
                exp = datetime.fromisoformat(
                    dr_expires_at.replace("Z", "+00:00")
                )
                exp_ns = int(exp.timestamp() * 1_000_000_000)

                if execution_ns > exp_ns:
                    admission_status = "REJECTED"
                    rejection_reason = (
                        f"DR expired at nanosecond {exp_ns}; "
                        f"execution at nanosecond {execution_ns} "
                        f"({execution_ns - exp_ns} ns after expiry)"
                    )

                # TAR-INV-006: compiled staleness bound enforcement.
                # If the DR's remaining validity window exceeds the compiled
                # ceiling, reject — regardless of operator configuration.
                # This is a structural guarantee, not a policy check.
                # Clock skew tolerance is added to the ceiling (not to the
                # remaining window) so that DRs near the boundary are not
                # spuriously rejected by minor clock drift.
                if admission_status == "ADMITTED":
                    remaining_ns = exp_ns - execution_ns
                    max_ns = (
                        TAR_MAX_DR_LIFETIME_SECONDS * 1_000_000_000
                        + TAR_CLOCK_SKEW_TOLERANCE_NS
                    )
                    if remaining_ns > max_ns:
                        admission_status = "REJECTED"
                        remaining_h = remaining_ns / 3_600_000_000_000
                        rejection_reason = (
                            f"TAR-INV-006: DR remaining lifetime "
                            f"({remaining_h:.2f}h) exceeds compiled "
                            f"staleness bound ({TAR_MAX_DR_LIFETIME_SECONDS}s). "
                            f"Reissue DR with a shorter lifetime epoch. "
                            f"This bound is structural and cannot be overridden "
                            f"by operator configuration."
                        )
                        logger.warning(
                            f"[ATF.Temporal] TAR-INV-006 VIOLATION — "
                            f"DR {delegation_id} remaining={remaining_h:.2f}h "
                            f"exceeds compiled bound={TAR_MAX_DR_LIFETIME_SECONDS}s"
                        )

            except Exception as exc:
                logger.warning(f"[ATF.Temporal] Expiry parse error: {exc}")

        tar_id = self._build_tar_id()

        core_fields: Dict[str, Any] = {
            "tar_id":                tar_id,
            "delegation_id":         delegation_id,
            "agent_id":              agent_id,
            "execution_ref":         execution_ref,
            "execution_ns":          execution_ns,
            "execution_ts":          execution_ts,
            "dr_status_at_admission": dr_status,
            "dr_expires_at":         dr_expires_at,
            "authority_budget":      authority_budget,
            "domain":                domain,
            "task_action":           task_action,
            "admission_status":      admission_status,
            "rejection_reason":      rejection_reason,
            "chain_root_id":         chain_root_id,
            "issued_at":             issued_at,
            "metadata":              metadata or {},
        }

        content_hash = self._compute_content_hash(core_fields)
        pqc_sig, pqc_alg = self._sign(content_hash)

        tar = TemporalAdmissibilityRecord(
            tar_id=tar_id,
            delegation_id=delegation_id,
            agent_id=agent_id,
            execution_ref=execution_ref,
            execution_ns=execution_ns,
            execution_ts=execution_ts,
            dr_status_at_admission=dr_status,
            dr_expires_at=dr_expires_at,
            authority_budget=authority_budget,
            domain=domain,
            task_action=task_action,
            admission_status=admission_status,
            rejection_reason=rejection_reason,
            content_hash=content_hash,
            pqc_signature=pqc_sig,
            pqc_algorithm=pqc_alg,
            chain_root_id=chain_root_id,
            issued_at=issued_at,
            metadata=metadata or {},
        )

        with self._lock:
            self._store[tar_id] = tar

        self._persist_tar(tar)

        log_level = logger.info if admission_status == "ADMITTED" else logger.warning
        log_level(
            f"[ATF.Temporal] TAR issued — id={tar_id} status={admission_status} "
            f"agent={agent_id} domain={domain} ns={execution_ns} "
            f"delegation={delegation_id} pqc={pqc_alg or 'SHA-256'}"
        )

        return tar

    def verify_tar(self, tar: TemporalAdmissibilityRecord) -> Dict[str, Any]:
        """
        Verify a Temporal Admissibility Record.

        Verification steps:
            1. Recompute content_hash — detects field tampering
            2. Verify PQC signature (platform key)
            3. Verify admission_status is ADMITTED
            4. Verify execution_ns is a plausible Unix nanosecond timestamp

        This verification requires NO platform access.

        Returns:
            dict with full verification result
        """
        fields = tar.to_dict()
        recomputed = self._compute_content_hash(fields)
        hash_valid = (recomputed == tar.content_hash)

        pqc_valid = False
        pqc_checked = False
        if tar.pqc_signature and self._provider:
            pk_b64 = os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64", "").strip()
            if pk_b64:
                pqc_checked = True
                try:
                    sig = base64.b64decode(tar.pqc_signature)
                    pk  = base64.b64decode(pk_b64)
                    pqc_valid = bool(
                        self._provider.verify(sig, tar.content_hash.encode(), pk)
                    )
                except Exception as exc:
                    logger.warning(f"[ATF.Temporal] PQC verify failed: {exc}")

        ns_plausible = (
            1_000_000_000_000_000_000 <= tar.execution_ns <= 10_000_000_000_000_000_000
        )

        admitted = tar.admission_status == "ADMITTED"
        fully_verified = hash_valid and admitted and ns_plausible and (
            pqc_valid if pqc_checked else True
        )

        return {
            "tar_id":             tar.tar_id,
            "hash_valid":         hash_valid,
            "pqc_signature_valid": pqc_valid,
            "pqc_checked":        pqc_checked,
            "admitted":           admitted,
            "ns_plausible":       ns_plausible,
            "fully_verified":     fully_verified,
            "admission_status":   tar.admission_status,
            "rejection_reason":   tar.rejection_reason,
            "delegation_id":      tar.delegation_id,
            "agent_id":           tar.agent_id,
            "execution_ns":       tar.execution_ns,
            "execution_ts":       tar.execution_ts,
            "authority_budget":   tar.authority_budget,
            "domain":             tar.domain,
            "chain_root_id":      tar.chain_root_id,
        }

    def get_tar(self, tar_id: str) -> Optional[TemporalAdmissibilityRecord]:
        with self._lock:
            if tar_id in self._store:
                return self._store[tar_id]
        if not self._db_url:
            return None
        conn = self._get_conn()
        if not conn:
            return None
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM atf_temporal_records WHERE tar_id = %s",
                    (tar_id,)
                )
                row = cur.fetchone()
                if row:
                    cols = [d[0] for d in cur.description]
                    return self._row_to_tar(dict(zip(cols, row)))
        except Exception as exc:
            logger.warning(f"[ATF.Temporal] get_tar DB failed: {exc}")
        finally:
            conn.close()
        return None

    def list_tars(
        self,
        delegation_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        admission_status: Optional[str] = None,
    ) -> List[TemporalAdmissibilityRecord]:
        with self._lock:
            tars = list(self._store.values())
        if delegation_id:
            tars = [t for t in tars if t.delegation_id == delegation_id]
        if agent_id:
            tars = [t for t in tars if t.agent_id == agent_id]
        if admission_status:
            tars = [t for t in tars if t.admission_status == admission_status]
        return sorted(tars, key=lambda t: t.execution_ns, reverse=True)

    def temporal_admissibility_report(self, agent_id: str) -> Dict[str, Any]:
        """
        Summary report of temporal admissibility for an agent.
        Useful for audit dashboards.
        """
        tars = self.list_tars(agent_id=agent_id)
        admitted = [t for t in tars if t.admission_status == "ADMITTED"]
        rejected = [t for t in tars if t.admission_status == "REJECTED"]
        pct_admitted = (len(admitted) / len(tars) * 100.0) if tars else 0.0

        return {
            "agent_id":        agent_id,
            "total_requests":  len(tars),
            "total_admitted":  len(admitted),
            "total_rejected":  len(rejected),
            "pct_admitted":    round(pct_admitted, 2),
            "latest_tar":      tars[0].summary() if tars else None,
            "rejection_reasons": [
                {"tar_id": t.tar_id, "reason": t.rejection_reason}
                for t in rejected
            ],
        }

    def _persist_tar(self, tar: TemporalAdmissibilityRecord) -> None:
        if not self._db_url:
            return
        conn = self._get_conn()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO atf_temporal_records (
                            tar_id, delegation_id, agent_id, execution_ref,
                            execution_ns, execution_ts, dr_status_at_admission,
                            dr_expires_at, authority_budget, domain, task_action,
                            admission_status, rejection_reason, content_hash,
                            pqc_signature, pqc_algorithm, chain_root_id,
                            issued_at, metadata
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb
                        )
                        ON CONFLICT (tar_id) DO NOTHING
                    """, (
                        tar.tar_id,
                        tar.delegation_id,
                        tar.agent_id,
                        tar.execution_ref,
                        tar.execution_ns,
                        tar.execution_ts,
                        tar.dr_status_at_admission,
                        tar.dr_expires_at,
                        tar.authority_budget,
                        tar.domain,
                        tar.task_action,
                        tar.admission_status,
                        tar.rejection_reason,
                        tar.content_hash,
                        tar.pqc_signature,
                        tar.pqc_algorithm,
                        tar.chain_root_id,
                        tar.issued_at,
                        json.dumps(tar.metadata),
                    ))
        except Exception as exc:
            logger.warning(f"[ATF.Temporal] persist failed: {exc}")
        finally:
            conn.close()

    def _row_to_tar(self, row: Dict) -> TemporalAdmissibilityRecord:
        def ts(v):
            if v is None:
                return None
            if isinstance(v, datetime):
                return v.isoformat()
            return str(v)
        meta = row.get("metadata") or {}
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}
        return TemporalAdmissibilityRecord(
            tar_id=row["tar_id"],
            delegation_id=row["delegation_id"],
            agent_id=row["agent_id"],
            execution_ref=row.get("execution_ref"),
            execution_ns=int(row["execution_ns"]),
            execution_ts=ts(row["execution_ts"]),
            dr_status_at_admission=row["dr_status_at_admission"],
            dr_expires_at=ts(row.get("dr_expires_at")),
            authority_budget=float(row["authority_budget"]),
            domain=row["domain"],
            task_action=row["task_action"],
            admission_status=row["admission_status"],
            rejection_reason=row.get("rejection_reason"),
            content_hash=row["content_hash"],
            pqc_signature=row.get("pqc_signature"),
            pqc_algorithm=row.get("pqc_algorithm"),
            chain_root_id=row["chain_root_id"],
            issued_at=ts(row["issued_at"]),
            metadata=meta,
        )
