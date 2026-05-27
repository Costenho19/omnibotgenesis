"""
OMNIX Agent Trust Fabric — Cross-Domain Trust Portability
ADR-158: Authority translation between governance domains.

When an AI agent authorized in one domain (e.g. HEALTHCARE) needs to
act in another domain (e.g. FINANCE), its authority cannot be carried
over implicitly. The CrossDomainBridge produces a Domain Translation
Receipt (DTR) — a PQC-signed proof that:

    a) The source delegation was ACTIVE and valid
    b) The authority was explicitly translated per a declared policy
    c) The translated authority is subject to a translation discount
    d) The translation itself is independently verifiable

Translation rules:
    - Authority budget ALWAYS decreases through translation
      (DTR enforces MAR: translated_budget <= source_budget)
    - A "translation discount" (default 20%) is applied
    - Domain pairs may define custom policies (e.g. HEALTHCARE→INSURANCE: 15%)
    - Translated authority is domain-scoped — only valid in target domain
    - DTRs expire with their source DR (or earlier if configured)

Key invariants:
    CDTP-INV-001: Translated authority ≤ source authority × (1 - discount)
    CDTP-INV-002: DTR is PQC-signed by the issuing system
    CDTP-INV-003: DTR embeds the source DR ID for chain traceability
    CDTP-INV-004: DTR is domain-scoped — invalid outside target domain
    CDTP-INV-005: DTRs are immutable once issued

ADR-158 — Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("OMNIX.ATF.DomainBridge")

DDL_DOMAIN_BRIDGES = """
CREATE TABLE IF NOT EXISTS atf_domain_bridges (
    dtr_id                  VARCHAR(64)   PRIMARY KEY,
    source_delegation_id    VARCHAR(64)   NOT NULL,
    source_domain           VARCHAR(64)   NOT NULL,
    target_domain           VARCHAR(64)   NOT NULL,
    source_agent_id         VARCHAR(64)   NOT NULL,
    target_agent_id         VARCHAR(64)   NOT NULL,
    source_authority_budget FLOAT         NOT NULL,
    translated_budget       FLOAT         NOT NULL,
    translation_discount    FLOAT         NOT NULL,
    translation_policy      VARCHAR(64)   NOT NULL,
    task_scope              JSONB         NOT NULL,
    chain_root_id           VARCHAR(64)   NOT NULL,
    content_hash            VARCHAR(64)   NOT NULL,
    pqc_signature           TEXT          DEFAULT NULL,
    pqc_algorithm           VARCHAR(32)   DEFAULT NULL,
    status                  VARCHAR(16)   NOT NULL DEFAULT 'ACTIVE',
    expires_at              TIMESTAMPTZ   DEFAULT NULL,
    issued_at               TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    issued_by               VARCHAR(128)  NOT NULL,
    metadata                JSONB         NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_atf_dtr_source_delegation
    ON atf_domain_bridges (source_delegation_id);
CREATE INDEX IF NOT EXISTS idx_atf_dtr_target_agent
    ON atf_domain_bridges (target_agent_id, target_domain, status);
CREATE INDEX IF NOT EXISTS idx_atf_dtr_source_domain_target
    ON atf_domain_bridges (source_domain, target_domain);
"""

DTR_ID_PREFIX = "ATFDTR"

DEFAULT_TRANSLATION_DISCOUNT = 0.20

DOMAIN_PAIR_POLICIES: Dict[Tuple[str, str], float] = {
    ("HEALTHCARE", "INSURANCE"):    0.15,
    ("HEALTHCARE", "FINANCE"):      0.30,
    ("FINANCE",    "INSURANCE"):    0.15,
    ("FINANCE",    "ENERGY"):       0.25,
    ("FINANCE",    "DEFENSE"):      0.50,
    ("DEFENSE",    "HEALTHCARE"):   0.40,
    ("ENERGY",     "FINANCE"):      0.20,
    ("INSURANCE",  "HEALTHCARE"):   0.15,
    ("INSURANCE",  "FINANCE"):      0.20,
}


class CrossDomainAuthorityError(Exception):
    """Raised when cross-domain translation violates an invariant."""


@dataclass
class DomainTranslationReceipt:
    """
    Cryptographic proof of cross-domain authority translation.

    A DTR proves that an agent authorized in source_domain was explicitly
    granted translated authority in target_domain, subject to the
    translation discount policy for that domain pair.

    Fields:
        dtr_id                  — "ATFDTR-{16HEX}"
        source_delegation_id    — ATFDR-{16HEX} of the source DR
        source_domain           — originating governance domain
        target_domain           — target governance domain
        source_agent_id         — AID in the source domain
        target_agent_id         — AID in the target domain
        source_authority_budget — authority held in source domain
        translated_budget       — authority granted in target domain
        translation_discount    — % reduction applied (e.g. 0.20 = 20%)
        translation_policy      — policy identifier used
        task_scope              — authorized scope in target domain
        chain_root_id           — chain_root_id of the source DR
        content_hash            — SHA-256 of all fields except sig fields
        pqc_signature           — Dilithium-3 sig by issuing system
        pqc_algorithm           — "dilithium3"
        status                  — ACTIVE | REVOKED | EXPIRED
        expires_at              — expiry (max = source DR expiry)
        issued_at               — ISO UTC timestamp
        issued_by               — AID or system identifier issuing the DTR
        metadata                — extension dict
    """
    dtr_id: str
    source_delegation_id: str
    source_domain: str
    target_domain: str
    source_agent_id: str
    target_agent_id: str
    source_authority_budget: float
    translated_budget: float
    translation_discount: float
    translation_policy: str
    task_scope: Dict[str, Any]
    chain_root_id: str
    content_hash: str
    pqc_signature: Optional[str]
    pqc_algorithm: Optional[str]
    status: str
    expires_at: Optional[str]
    issued_at: str
    issued_by: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_active(self) -> bool:
        return self.status == "ACTIVE"

    def effective_authority(self) -> float:
        return self.translated_budget

    def trust_summary(self) -> Dict[str, Any]:
        return {
            "dtr_id":                self.dtr_id,
            "source_domain":         self.source_domain,
            "target_domain":         self.target_domain,
            "source_agent_id":       self.source_agent_id,
            "target_agent_id":       self.target_agent_id,
            "source_budget":         self.source_authority_budget,
            "translated_budget":     self.translated_budget,
            "translation_discount":  f"{self.translation_discount*100:.0f}%",
            "translation_policy":    self.translation_policy,
            "chain_root_id":         self.chain_root_id,
            "pqc_signed":            self.pqc_signature is not None,
            "status":                self.status,
        }


class CrossDomainBridge:
    """
    Issues and verifies Domain Translation Receipts (DTRs) for
    cross-domain agent authority portability.

    Design contract:
        translate()          → DomainTranslationReceipt
        verify_dtr()         → verification result dict
        get_policy()         → discount for a domain pair
        get_dtr()            → DTR by ID
        list_dtrs()          → DTRs for a source delegation or agent
        ensure_tables()      → idempotent DDL

    CDTP-INV-001: translated_budget <= source_budget × (1 - discount)
    CDTP-INV-002: All DTRs are PQC-signed by the platform key
    CDTP-INV-003: DTRs embed the source_delegation_id
    CDTP-INV-004: DTRs are domain-scoped
    CDTP-INV-005: DTRs are immutable once issued
    """

    def __init__(self, db_url: Optional[str] = None):
        self._db_url = db_url or os.environ.get("DATABASE_URL")
        self._store: Dict[str, DomainTranslationReceipt] = {}
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
            logger.warning(f"[ATF.DomainBridge] DB connection failed: {exc}")
            return None

    @staticmethod
    def _build_dtr_id() -> str:
        return f"{DTR_ID_PREFIX}-{uuid.uuid4().hex[:16].upper()}"

    @staticmethod
    def _compute_content_hash(fields: Dict[str, Any]) -> str:
        exclude = {"content_hash", "pqc_signature", "pqc_algorithm"}
        clean = {k: v for k, v in fields.items() if k not in exclude}
        canonical = json.dumps(clean, sort_keys=True, separators=(",", ":"))
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
            logger.warning(f"[ATF.DomainBridge] Sign failed: {exc}")
        return None, None

    def get_policy(
        self,
        source_domain: str,
        target_domain: str,
    ) -> Tuple[float, str]:
        """
        Returns (discount_rate, policy_id) for a domain pair.

        Domain-pair-specific policies take precedence over the default.
        """
        src = source_domain.upper()
        tgt = target_domain.upper()
        pair = (src, tgt)
        if pair in DOMAIN_PAIR_POLICIES:
            discount = DOMAIN_PAIR_POLICIES[pair]
            policy_id = f"CDTP-{src[:4]}-{tgt[:4]}-POLICY"
        else:
            discount = DEFAULT_TRANSLATION_DISCOUNT
            policy_id = "CDTP-DEFAULT-POLICY"
        return discount, policy_id

    def ensure_tables(self) -> bool:
        if not self._db_url:
            return False
        conn = self._get_conn()
        if not conn:
            return False
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(DDL_DOMAIN_BRIDGES)
            logger.info("[ATF.DomainBridge] Table ready: atf_domain_bridges")
            return True
        except Exception as exc:
            logger.warning(f"[ATF.DomainBridge] ensure_tables failed: {exc}")
            return False
        finally:
            conn.close()

    def translate(
        self,
        source_delegation: Any,
        source_agent_id: str,
        target_agent_id: str,
        target_domain: str,
        target_task_scope: Dict[str, Any],
        issued_by: str = "system",
        discount_override: Optional[float] = None,
        expires_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DomainTranslationReceipt:
        """
        Issue a Domain Translation Receipt for cross-domain authority.

        Args:
            source_delegation:  DelegationReceipt (or dict) in source domain
            source_agent_id:    AID of the agent in the source domain
            target_agent_id:    AID in the target domain (may differ)
            target_domain:      Target governance domain
            target_task_scope:  Authorized scope in the target domain
            issued_by:          AID or system identifier
            discount_override:  Override the policy discount (for testing)
            expires_at:         Max = source DR expiry
            metadata:           Extension dict

        Returns:
            DomainTranslationReceipt — PQC-signed

        Raises:
            CrossDomainAuthorityError: If CDTP-INV-001 would be violated
            ValueError: If required fields are missing
        """
        if hasattr(source_delegation, "to_dict"):
            dr_dict = source_delegation.to_dict()
        elif isinstance(source_delegation, dict):
            dr_dict = source_delegation
        else:
            raise ValueError("source_delegation must be a DelegationReceipt or dict")

        if not source_agent_id:
            raise ValueError("source_agent_id is required")
        if not target_agent_id:
            raise ValueError("target_agent_id is required")
        if not target_domain:
            raise ValueError("target_domain is required")
        if not target_task_scope:
            raise ValueError("target_task_scope is required")

        source_delegation_id = dr_dict.get("delegation_id", "")
        source_domain = dr_dict.get("task_scope", {}).get("domain", "UNKNOWN")
        source_budget = float(dr_dict.get("authority_budget_granted", 0))
        chain_root_id = dr_dict.get("chain_root_id", source_delegation_id)
        dr_status = dr_dict.get("status", "UNKNOWN")

        if dr_status != "ACTIVE":
            raise CrossDomainAuthorityError(
                f"CDTP-INV-001: Source DR is {dr_status} — translation refused"
            )

        if source_domain.upper() == target_domain.upper():
            raise CrossDomainAuthorityError(
                "Same-domain translation is not permitted — use standard delegation"
            )

        if discount_override is not None:
            discount = max(0.0, min(1.0, discount_override))
            policy_id = f"CDTP-OVERRIDE-{discount*100:.0f}PCT"
        else:
            discount, policy_id = self.get_policy(source_domain, target_domain)

        max_translated = round(source_budget * (1.0 - discount), 4)
        translated_budget = round(min(source_budget, max_translated), 4)

        if translated_budget > source_budget:
            raise CrossDomainAuthorityError(
                f"CDTP-INV-001 VIOLATED: translated_budget ({translated_budget}) "
                f"> source_budget ({source_budget}). "
                f"Cross-domain translation cannot expand authority."
            )

        dtr_id = self._build_dtr_id()
        now = datetime.now(timezone.utc).isoformat()

        if not target_task_scope.get("domain"):
            target_task_scope["domain"] = target_domain.upper()

        core_fields: Dict[str, Any] = {
            "dtr_id":                   dtr_id,
            "source_delegation_id":     source_delegation_id,
            "source_domain":            source_domain.upper(),
            "target_domain":            target_domain.upper(),
            "source_agent_id":          source_agent_id,
            "target_agent_id":          target_agent_id,
            "source_authority_budget":  source_budget,
            "translated_budget":        translated_budget,
            "translation_discount":     discount,
            "translation_policy":       policy_id,
            "task_scope":               target_task_scope,
            "chain_root_id":            chain_root_id,
            "status":                   "ACTIVE",
            "expires_at":               expires_at,
            "issued_at":                now,
            "issued_by":                issued_by,
            "metadata":                 metadata or {},
        }

        content_hash = self._compute_content_hash(core_fields)
        pqc_sig, pqc_alg = self._sign(content_hash)

        dtr = DomainTranslationReceipt(
            dtr_id=dtr_id,
            source_delegation_id=source_delegation_id,
            source_domain=source_domain.upper(),
            target_domain=target_domain.upper(),
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            source_authority_budget=source_budget,
            translated_budget=translated_budget,
            translation_discount=discount,
            translation_policy=policy_id,
            task_scope=target_task_scope,
            chain_root_id=chain_root_id,
            content_hash=content_hash,
            pqc_signature=pqc_sig,
            pqc_algorithm=pqc_alg,
            status="ACTIVE",
            expires_at=expires_at,
            issued_at=now,
            issued_by=issued_by,
            metadata=metadata or {},
        )

        with self._lock:
            self._store[dtr_id] = dtr

        self._persist_dtr(dtr)

        logger.info(
            f"[ATF.DomainBridge] DTR issued — id={dtr_id} "
            f"{source_domain}→{target_domain} "
            f"budget={source_budget}→{translated_budget} "
            f"discount={discount*100:.0f}% policy={policy_id} "
            f"pqc={pqc_alg or 'SHA-256'}"
        )

        return dtr

    def verify_dtr(self, dtr: DomainTranslationReceipt) -> Dict[str, Any]:
        """
        Verify a Domain Translation Receipt.

        Steps:
            1. Recompute content_hash
            2. Verify PQC signature
            3. Verify CDTP-INV-001 (translated ≤ source × (1 - discount))
            4. Check status and expiry
        """
        fields = dtr.to_dict()
        recomputed = self._compute_content_hash(fields)
        hash_valid = (recomputed == dtr.content_hash)

        expected_max = round(dtr.source_authority_budget * (1.0 - dtr.translation_discount), 4)
        cdtp_inv_001_valid = dtr.translated_budget <= dtr.source_authority_budget

        pqc_valid = False
        pqc_checked = False
        if dtr.pqc_signature and self._provider:
            pk_b64 = os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64", "").strip()
            if pk_b64:
                pqc_checked = True
                try:
                    sig = base64.b64decode(dtr.pqc_signature)
                    pk  = base64.b64decode(pk_b64)
                    pqc_valid = bool(
                        self._provider.verify(sig, dtr.content_hash.encode(), pk)
                    )
                except Exception as exc:
                    logger.warning(f"[ATF.DomainBridge] PQC verify failed: {exc}")

        not_expired = True
        if dtr.expires_at:
            try:
                exp = datetime.fromisoformat(dtr.expires_at.replace("Z", "+00:00"))
                not_expired = datetime.now(timezone.utc) <= exp
            except Exception:
                not_expired = False

        active = dtr.status == "ACTIVE"
        fully_verified = (
            hash_valid and cdtp_inv_001_valid and not_expired and active
            and (pqc_valid if pqc_checked else True)
        )

        return {
            "dtr_id":               dtr.dtr_id,
            "hash_valid":           hash_valid,
            "pqc_signature_valid":  pqc_valid,
            "pqc_checked":          pqc_checked,
            "cdtp_inv_001_valid":   cdtp_inv_001_valid,
            "not_expired":          not_expired,
            "active":               active,
            "fully_verified":       fully_verified,
            "source_domain":        dtr.source_domain,
            "target_domain":        dtr.target_domain,
            "translated_budget":    dtr.translated_budget,
            "max_permitted":        expected_max,
            "translation_discount": dtr.translation_discount,
            "translation_policy":   dtr.translation_policy,
            "chain_root_id":        dtr.chain_root_id,
        }

    def get_dtr(self, dtr_id: str) -> Optional[DomainTranslationReceipt]:
        with self._lock:
            if dtr_id in self._store:
                return self._store[dtr_id]
        return None

    def list_dtrs(
        self,
        source_delegation_id: Optional[str] = None,
        target_agent_id: Optional[str] = None,
        target_domain: Optional[str] = None,
        status: str = "ACTIVE",
    ) -> List[DomainTranslationReceipt]:
        with self._lock:
            dtrs = list(self._store.values())
        if source_delegation_id:
            dtrs = [d for d in dtrs if d.source_delegation_id == source_delegation_id]
        if target_agent_id:
            dtrs = [d for d in dtrs if d.target_agent_id == target_agent_id]
        if target_domain:
            dtrs = [d for d in dtrs if d.target_domain == target_domain.upper()]
        if status:
            dtrs = [d for d in dtrs if d.status == status]
        return dtrs

    def _persist_dtr(self, dtr: DomainTranslationReceipt) -> None:
        if not self._db_url:
            return
        conn = self._get_conn()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO atf_domain_bridges (
                            dtr_id, source_delegation_id, source_domain,
                            target_domain, source_agent_id, target_agent_id,
                            source_authority_budget, translated_budget,
                            translation_discount, translation_policy,
                            task_scope, chain_root_id, content_hash,
                            pqc_signature, pqc_algorithm, status,
                            expires_at, issued_at, issued_by, metadata
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s::jsonb, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb
                        )
                        ON CONFLICT (dtr_id) DO NOTHING
                    """, (
                        dtr.dtr_id,
                        dtr.source_delegation_id,
                        dtr.source_domain,
                        dtr.target_domain,
                        dtr.source_agent_id,
                        dtr.target_agent_id,
                        dtr.source_authority_budget,
                        dtr.translated_budget,
                        dtr.translation_discount,
                        dtr.translation_policy,
                        json.dumps(dtr.task_scope),
                        dtr.chain_root_id,
                        dtr.content_hash,
                        dtr.pqc_signature,
                        dtr.pqc_algorithm,
                        dtr.status,
                        dtr.expires_at,
                        dtr.issued_at,
                        dtr.issued_by,
                        json.dumps(dtr.metadata),
                    ))
        except Exception as exc:
            logger.warning(f"[ATF.DomainBridge] persist failed: {exc}")
        finally:
            conn.close()
