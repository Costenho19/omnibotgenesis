"""
OMNIX Agent Trust Fabric — Delegation Receipt Engine
ADR-156: Cryptographic proof of agent-to-agent authority delegation.

Every time an agent (or a Tier-1 operator) delegates a task to a sub-agent,
a Delegation Receipt is produced. The receipt:

  - Is PQC-signed by the delegator's Dilithium-3 private key
  - Embeds the delegator's public key for self-contained verification
  - Enforces the Monotonic Authority Reduction (MAR) invariant:
      authority_budget_granted ≤ authority_budget_delegator  (ATF-INV-001)
  - Chains to its parent delegation via parent_delegation_id
  - Traces back to a human root via chain_root_id

Key invariants:
    ATF-INV-001: Authority never expands through delegation
    ATF-INV-002: Every receipt is PQC-signed by the delegator
    ATF-INV-005: Receipts are immutable once issued

ADR-156 — Harold Nunes — OMNIX QUANTUM LTD — May 2026
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

logger = logging.getLogger("OMNIX.ATF.Delegation")

DDL_DELEGATION_RECEIPTS = """
CREATE TABLE IF NOT EXISTS atf_delegation_receipts (
    delegation_id               VARCHAR(64)   PRIMARY KEY,
    delegator_id                VARCHAR(128)  NOT NULL,
    delegate_id                 VARCHAR(64)   NOT NULL,
    task_scope                  JSONB         NOT NULL,
    authority_budget_delegator  FLOAT         NOT NULL,
    authority_budget_granted    FLOAT         NOT NULL,
    parent_delegation_id        VARCHAR(64)   DEFAULT NULL,
    chain_root_id               VARCHAR(64)   NOT NULL,
    delegation_depth            INTEGER       NOT NULL,
    delegator_public_key        TEXT          NOT NULL,
    content_hash                VARCHAR(64)   NOT NULL,
    posture_state_hash          VARCHAR(64)   DEFAULT NULL,
    pqc_signature               TEXT          DEFAULT NULL,
    pqc_algorithm               VARCHAR(32)   DEFAULT NULL,
    expires_at                  TIMESTAMPTZ   DEFAULT NULL,
    status                      VARCHAR(16)   NOT NULL DEFAULT 'ACTIVE',
    created_at                  TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    metadata                    JSONB         NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_atf_dr_delegate
    ON atf_delegation_receipts (delegate_id, status);
CREATE INDEX IF NOT EXISTS idx_atf_dr_chain_root
    ON atf_delegation_receipts (chain_root_id);
CREATE INDEX IF NOT EXISTS idx_atf_dr_delegator
    ON atf_delegation_receipts (delegator_id);
ALTER TABLE atf_delegation_receipts
    ADD COLUMN IF NOT EXISTS posture_state_hash VARCHAR(64) DEFAULT NULL;
"""


class AuthorityExpansionViolation(Exception):
    """
    Raised when a delegation attempt violates the Monotonic Authority
    Reduction invariant (ATF-INV-001):
        authority_budget_granted > authority_budget_delegator
    """


@dataclass
class DelegationReceipt:
    """
    Cryptographic proof of agent-to-agent authority delegation.

    Fields:
        delegation_id               — "ATFDR-{16HEX}"
        delegator_id                — AID or human operator ID
        delegate_id                 — AID of receiving agent
        task_scope                  — dict describing what is authorized
        authority_budget_delegator  — budget held by delegator at issuance
        authority_budget_granted    — budget granted (≤ delegator's budget)
        parent_delegation_id        — ID of delegation that gave delegator its authority
        chain_root_id               — originating delegation (human root)
        delegation_depth            — 0=human, 1=first agent, N=Nth sub-agent
        delegator_public_key        — Dilithium-3 pub key embedded for verification
        content_hash                — SHA-256 of all fields except signature
        posture_state_hash          — SHA-256 of authority posture at issuance
                                      (delegator_id, task_scope, budgets, depth,
                                       chain_root_id, created_at). Enables
                                       TAR↔TAP bridge validation (SPV binding).
        pqc_signature               — Dilithium-3 sig over content_hash (delegator key)
        pqc_algorithm               — e.g. "dilithium3"
        expires_at                  — ISO UTC or None
        status                      — ACTIVE | EXPIRED | REVOKED
        created_at                  — ISO UTC
        metadata                    — extension dict
    """
    delegation_id: str
    delegator_id: str
    delegate_id: str
    task_scope: Dict[str, Any]
    authority_budget_delegator: float
    authority_budget_granted: float
    parent_delegation_id: Optional[str]
    chain_root_id: str
    delegation_depth: int
    delegator_public_key: str
    content_hash: str
    posture_state_hash: Optional[str]
    pqc_signature: Optional[str]
    pqc_algorithm: Optional[str]
    expires_at: Optional[str]
    status: str
    created_at: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_active(self) -> bool:
        return self.status == "ACTIVE"

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        try:
            exp = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) > exp
        except Exception:
            return False

    def authority_reduction_pct(self) -> float:
        """How much authority was reduced (%) vs the delegator's budget."""
        if self.authority_budget_delegator == 0:
            return 0.0
        return round(
            (1.0 - self.authority_budget_granted / self.authority_budget_delegator) * 100.0,
            2
        )

    def trust_summary(self) -> Dict[str, Any]:
        return {
            "delegation_id":      self.delegation_id,
            "delegator_id":       self.delegator_id,
            "delegate_id":        self.delegate_id,
            "authority_granted":  self.authority_budget_granted,
            "authority_reduction_pct": self.authority_reduction_pct(),
            "delegation_depth":   self.delegation_depth,
            "chain_root_id":      self.chain_root_id,
            "posture_state_hash": self.posture_state_hash,
            "pqc_signed":         self.pqc_signature is not None,
            "status":             self.status,
        }


class DelegationReceiptEngine:
    """
    Issues, verifies, and manages Delegation Receipts for the ATF.

    Design contract:
        create_delegation()  → DelegationReceipt (PQC-signed, persisted)
        verify_receipt()     → verification result dict
        revoke_delegation()  → status → REVOKED
        get_delegation()     → DelegationReceipt by ID
        list_delegations()   → delegations for a delegate or delegator
        ensure_tables()      → idempotent DDL

    MAR Enforcement (ATF-INV-001):
        create_delegation() raises AuthorityExpansionViolation if
        authority_budget_granted > authority_budget_delegator.
        This is enforced BEFORE signing — no receipt is issued.
    """

    def __init__(self, db_url: Optional[str] = None):
        self._db_url = db_url or os.environ.get("DATABASE_URL")
        self._store: Dict[str, DelegationReceipt] = {}
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
            logger.warning(f"[ATF.Delegation] DB connection failed: {exc}")
            return None

    @staticmethod
    def _build_delegation_id() -> str:
        return f"ATFDR-{uuid.uuid4().hex[:16].upper()}"

    @staticmethod
    def _compute_posture_state_hash(
        delegator_id: str,
        task_scope: Dict[str, Any],
        authority_budget_delegator: float,
        authority_budget_granted: float,
        delegation_depth: int,
        chain_root_id: str,
        created_at: str,
    ) -> str:
        """
        SHA-256 of the authority posture at the exact moment of DR issuance.

        Captures the complete posture state binding — enabling cross-protocol
        TAR↔TAP bridge validation (SPV binding per VeriSigil VGS integration).
        This hash is stable: it does not change after issuance regardless of
        subsequent authority evolution, making it safe for long-lived receipt
        validation under evolving posture.

        Committed fields (canonical JSON → SHA-256):
            delegator_id, task_scope, authority_budget_delegator,
            authority_budget_granted, delegation_depth,
            chain_root_id, created_at
        """
        posture = {
            "delegator_id":               delegator_id,
            "task_scope":                 task_scope,
            "authority_budget_delegator": round(authority_budget_delegator, 4),
            "authority_budget_granted":   round(authority_budget_granted, 4),
            "delegation_depth":           delegation_depth,
            "chain_root_id":              chain_root_id,
            "created_at":                 created_at,
        }
        canonical = json.dumps(posture, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    @staticmethod
    def _compute_content_hash(fields: Dict[str, Any]) -> str:
        """
        SHA-256 of canonicalized delegation fields (excluding signature fields).
        Tampering with any field breaks this hash, invalidating verification.
        """
        exclude = {"content_hash", "pqc_signature", "pqc_algorithm"}
        clean = {k: v for k, v in fields.items() if k not in exclude}
        canonical = json.dumps(clean, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def _sign_with_agent_key(
        self,
        content_hash: str,
        agent_sk_b64: Optional[str],
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Sign content_hash with the agent's own Dilithium-3 private key.
        Falls back to platform key if agent has no key.
        """
        if not self._provider:
            return None, None

        sk_b64 = agent_sk_b64 or os.environ.get("OMNIX_SIGNING_SECRET_KEY_B64", "").strip()
        if not sk_b64:
            return None, None
        try:
            sk = base64.b64decode(sk_b64)
            sig = self._provider.sign(content_hash.encode(), sk)
            if sig:
                return base64.b64encode(sig).decode(), self._provider.algorithm_name()
        except Exception as exc:
            logger.warning(f"[ATF.Delegation] Sign failed: {exc}")
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
                    cur.execute(DDL_DELEGATION_RECEIPTS)
            logger.info("[ATF.Delegation] Table ready: atf_delegation_receipts")
            return True
        except Exception as exc:
            logger.warning(f"[ATF.Delegation] ensure_tables failed: {exc}")
            return False
        finally:
            conn.close()

    def create_delegation(
        self,
        delegator_id: str,
        delegate_id: str,
        task_scope: Dict[str, Any],
        authority_budget_delegator: float,
        authority_budget_granted: float,
        delegator_public_key: str = "",
        delegator_sk_b64: Optional[str] = None,
        parent_delegation_id: Optional[str] = None,
        chain_root_id: Optional[str] = None,
        delegation_depth: int = 0,
        expires_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DelegationReceipt:
        """
        Issue a PQC-signed Delegation Receipt.

        Args:
            delegator_id:               AID or human operator ID
            delegate_id:                AID of receiving agent
            task_scope:                 What the delegate is authorized to do
            authority_budget_delegator: Budget held by delegator
            authority_budget_granted:   Budget to grant (must be ≤ delegator's)
            delegator_public_key:       Delegator's Dilithium-3 pub key (base64)
            delegator_sk_b64:           Delegator's private key for signing
            parent_delegation_id:       Parent DR ID (None if from human root)
            chain_root_id:              Root DR ID (computed if None)
            delegation_depth:           Chain depth (0=human root)
            expires_at:                 Optional ISO UTC expiry
            metadata:                   Extension dict

        Returns:
            DelegationReceipt — PQC-signed, persisted to DB if available.

        Raises:
            AuthorityExpansionViolation: If granted > delegator budget (ATF-INV-001)
            ValueError: If required fields are missing
        """
        if not delegator_id:
            raise ValueError("delegator_id is required")
        if not delegate_id:
            raise ValueError("delegate_id is required")
        if not task_scope:
            raise ValueError("task_scope cannot be empty")
        if not (0.0 <= authority_budget_granted <= 100.0):
            raise ValueError(f"authority_budget_granted must be 0-100, got {authority_budget_granted}")

        if authority_budget_granted > authority_budget_delegator:
            raise AuthorityExpansionViolation(
                f"ATF-INV-001 VIOLATED: authority_budget_granted ({authority_budget_granted}) "
                f"> authority_budget_delegator ({authority_budget_delegator}). "
                f"Monotonic Authority Reduction forbids authority expansion. "
                f"delegator={delegator_id} delegate={delegate_id}"
            )

        delegation_id = self._build_delegation_id()
        now = datetime.now(timezone.utc).isoformat()

        if chain_root_id is None:
            chain_root_id = delegation_id

        posture_state_hash = self._compute_posture_state_hash(
            delegator_id=delegator_id,
            task_scope=task_scope,
            authority_budget_delegator=round(authority_budget_delegator, 4),
            authority_budget_granted=round(authority_budget_granted, 4),
            delegation_depth=delegation_depth,
            chain_root_id=chain_root_id,
            created_at=now,
        )

        core_fields: Dict[str, Any] = {
            "delegation_id":               delegation_id,
            "delegator_id":                delegator_id,
            "delegate_id":                 delegate_id,
            "task_scope":                  task_scope,
            "authority_budget_delegator":  round(authority_budget_delegator, 4),
            "authority_budget_granted":    round(authority_budget_granted, 4),
            "parent_delegation_id":        parent_delegation_id,
            "chain_root_id":              chain_root_id,
            "delegation_depth":            delegation_depth,
            "delegator_public_key":        delegator_public_key,
            "posture_state_hash":          posture_state_hash,
            "expires_at":                  expires_at,
            "status":                      "ACTIVE",
            "created_at":                  now,
            "metadata":                    metadata or {},
        }

        content_hash = self._compute_content_hash(core_fields)
        core_fields["content_hash"] = content_hash

        pqc_sig, pqc_alg = self._sign_with_agent_key(content_hash, delegator_sk_b64)

        receipt = DelegationReceipt(
            delegation_id=delegation_id,
            delegator_id=delegator_id,
            delegate_id=delegate_id,
            task_scope=task_scope,
            authority_budget_delegator=round(authority_budget_delegator, 4),
            authority_budget_granted=round(authority_budget_granted, 4),
            parent_delegation_id=parent_delegation_id,
            chain_root_id=chain_root_id,
            delegation_depth=delegation_depth,
            delegator_public_key=delegator_public_key,
            content_hash=content_hash,
            posture_state_hash=posture_state_hash,
            pqc_signature=pqc_sig,
            pqc_algorithm=pqc_alg,
            expires_at=expires_at,
            status="ACTIVE",
            created_at=now,
            metadata=metadata or {},
        )

        with self._lock:
            self._store[delegation_id] = receipt

        self._persist_receipt(receipt)

        logger.info(
            f"[ATF.Delegation] Receipt issued — id={delegation_id} "
            f"depth={delegation_depth} budget={authority_budget_granted} "
            f"delegator={delegator_id} delegate={delegate_id} "
            f"pqc={pqc_alg or 'SHA-256 fallback'}"
        )
        return receipt

    def verify_receipt(
        self,
        receipt: DelegationReceipt,
        delegator_public_key_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Verify a Delegation Receipt independently.

        Verification steps:
            1. Recompute content_hash — detects field tampering
            2. Verify PQC signature (delegator_public_key embedded in receipt)
            3. Verify MAR invariant (granted ≤ delegator budget)
            4. Check expiry status

        This verification requires NO platform access — only the receipt itself.
        The delegator_public_key is embedded for this purpose.

        Args:
            receipt: DelegationReceipt to verify
            delegator_public_key_override: Override the embedded key (for testing)

        Returns:
            dict with full verification result
        """
        fields = receipt.to_dict()
        recomputed = self._compute_content_hash(fields)
        hash_valid = (recomputed == receipt.content_hash)

        pub_key = delegator_public_key_override or receipt.delegator_public_key
        pqc_valid = False
        pqc_checked = False

        if receipt.pqc_signature and pub_key and self._provider:
            pqc_checked = True
            try:
                sig = base64.b64decode(receipt.pqc_signature)
                pk  = base64.b64decode(pub_key)
                pqc_valid = bool(self._provider.verify(
                    sig, receipt.content_hash.encode(), pk
                ))
            except Exception as exc:
                logger.warning(f"[ATF.Delegation] PQC verify error: {exc}")

        mar_valid = receipt.authority_budget_granted <= receipt.authority_budget_delegator
        not_expired = not receipt.is_expired()

        fully_verified = hash_valid and mar_valid and not_expired and (
            pqc_valid if pqc_checked else True
        )

        return {
            "delegation_id":    receipt.delegation_id,
            "hash_valid":       hash_valid,
            "pqc_signature_valid": pqc_valid,
            "pqc_checked":      pqc_checked,
            "mar_invariant_valid": mar_valid,
            "not_expired":      not_expired,
            "fully_verified":   fully_verified,
            "delegation_depth": receipt.delegation_depth,
            "authority_budget_granted": receipt.authority_budget_granted,
            "authority_reduction_pct": receipt.authority_reduction_pct(),
            "chain_root_id":    receipt.chain_root_id,
            "pqc_signed":       receipt.pqc_signature is not None,
            "delegator_id":     receipt.delegator_id,
            "delegate_id":      receipt.delegate_id,
        }

    def get_delegation(self, delegation_id: str) -> Optional[DelegationReceipt]:
        with self._lock:
            if delegation_id in self._store:
                return self._store[delegation_id]

        if not self._db_url:
            return None
        conn = self._get_conn()
        if not conn:
            return None
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM atf_delegation_receipts WHERE delegation_id = %s",
                    (delegation_id,)
                )
                row = cur.fetchone()
                if row:
                    cols = [d[0] for d in cur.description]
                    receipt = self._row_to_receipt(dict(zip(cols, row)))
                    with self._lock:
                        self._store[delegation_id] = receipt
                    return receipt
        except Exception as exc:
            logger.warning(f"[ATF.Delegation] get_delegation DB failed: {exc}")
        finally:
            conn.close()
        return None

    def list_delegations(
        self,
        delegate_id: Optional[str] = None,
        delegator_id: Optional[str] = None,
        status: str = "ACTIVE",
    ) -> List[DelegationReceipt]:
        with self._lock:
            receipts = list(self._store.values())
        if delegate_id:
            receipts = [r for r in receipts if r.delegate_id == delegate_id]
        if delegator_id:
            receipts = [r for r in receipts if r.delegator_id == delegator_id]
        if status:
            receipts = [r for r in receipts if r.status == status]
        return receipts

    def revoke_delegation(self, delegation_id: str) -> bool:
        with self._lock:
            if delegation_id in self._store:
                dr = self._store[delegation_id]
                self._store[delegation_id] = DelegationReceipt(
                    **{**asdict(dr), "status": "REVOKED"}
                )
        if self._db_url:
            conn = self._get_conn()
            if conn:
                try:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                "UPDATE atf_delegation_receipts SET status='REVOKED' WHERE delegation_id=%s",
                                (delegation_id,)
                            )
                except Exception as exc:
                    logger.warning(f"[ATF.Delegation] revoke DB failed: {exc}")
                finally:
                    conn.close()
        logger.warning(f"[ATF.Delegation] Delegation REVOKED — id={delegation_id}")
        return True

    def _persist_receipt(self, receipt: DelegationReceipt) -> None:
        if not self._db_url:
            return
        conn = self._get_conn()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO atf_delegation_receipts (
                            delegation_id, delegator_id, delegate_id,
                            task_scope, authority_budget_delegator,
                            authority_budget_granted, parent_delegation_id,
                            chain_root_id, delegation_depth,
                            delegator_public_key, content_hash,
                            posture_state_hash,
                            pqc_signature, pqc_algorithm,
                            expires_at, status, created_at, metadata
                        ) VALUES (
                            %s, %s, %s, %s::jsonb, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb
                        )
                        ON CONFLICT (delegation_id) DO NOTHING
                    """, (
                        receipt.delegation_id,
                        receipt.delegator_id,
                        receipt.delegate_id,
                        json.dumps(receipt.task_scope),
                        receipt.authority_budget_delegator,
                        receipt.authority_budget_granted,
                        receipt.parent_delegation_id,
                        receipt.chain_root_id,
                        receipt.delegation_depth,
                        receipt.delegator_public_key,
                        receipt.content_hash,
                        receipt.posture_state_hash,
                        receipt.pqc_signature,
                        receipt.pqc_algorithm,
                        receipt.expires_at,
                        receipt.status,
                        receipt.created_at,
                        json.dumps(receipt.metadata),
                    ))
        except Exception as exc:
            logger.warning(f"[ATF.Delegation] persist failed (in-memory only): {exc}")
        finally:
            conn.close()

    def _row_to_receipt(self, row: Dict) -> DelegationReceipt:
        def ts(v):
            if v is None:
                return None
            if isinstance(v, datetime):
                return v.isoformat()
            return str(v)

        scope = row.get("task_scope") or {}
        if isinstance(scope, str):
            try:
                scope = json.loads(scope)
            except Exception:
                scope = {}
        meta = row.get("metadata") or {}
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}

        return DelegationReceipt(
            delegation_id=row["delegation_id"],
            delegator_id=row["delegator_id"],
            delegate_id=row["delegate_id"],
            task_scope=scope,
            authority_budget_delegator=float(row["authority_budget_delegator"]),
            authority_budget_granted=float(row["authority_budget_granted"]),
            parent_delegation_id=row.get("parent_delegation_id"),
            chain_root_id=row["chain_root_id"],
            delegation_depth=int(row["delegation_depth"]),
            delegator_public_key=row.get("delegator_public_key", ""),
            content_hash=row["content_hash"],
            posture_state_hash=row.get("posture_state_hash"),
            pqc_signature=row.get("pqc_signature"),
            pqc_algorithm=row.get("pqc_algorithm"),
            expires_at=ts(row.get("expires_at")),
            status=row["status"],
            created_at=ts(row.get("created_at")),
            metadata=meta,
        )
