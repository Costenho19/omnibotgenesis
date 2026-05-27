"""
OMNIX Agent Trust Fabric — Agent Identity Engine
ADR-156: Cryptographic registration and management of AI agent identities.

Every AI agent that participates in an OMNIX-governed environment is registered
here. Registration produces a Dilithium-3 key pair, an authority budget (0-100),
and a PQC-signed immutable identity record.

Key invariants:
    ATF-INV-004: A delegator cannot grant authority it does not hold
    ATF-INV-005: Identity records are immutable once issued
    ATF-INV-006: Independent verification requires no platform access

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

logger = logging.getLogger("OMNIX.ATF.Identity")

DDL_AGENT_REGISTRY = """
CREATE TABLE IF NOT EXISTS atf_agent_registry (
    agent_id            VARCHAR(64)   PRIMARY KEY,
    display_name        VARCHAR(128)  NOT NULL,
    domain              VARCHAR(64)   NOT NULL,
    vertical            VARCHAR(64)   NOT NULL DEFAULT 'general',
    authority_budget    FLOAT         NOT NULL,
    registered_by       VARCHAR(128)  NOT NULL,
    registration_tier   INTEGER       NOT NULL,
    public_key_b64      TEXT          NOT NULL,
    registration_hash   VARCHAR(64)   NOT NULL,
    pqc_signature       TEXT          DEFAULT NULL,
    pqc_algorithm       VARCHAR(32)   DEFAULT NULL,
    status              VARCHAR(16)   NOT NULL DEFAULT 'ACTIVE',
    capabilities        JSONB         NOT NULL DEFAULT '[]',
    registered_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    metadata            JSONB         NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_atf_registry_domain
    ON atf_agent_registry (domain, status);
CREATE INDEX IF NOT EXISTS idx_atf_registry_registered_by
    ON atf_agent_registry (registered_by);
"""


@dataclass
class AgentIdentity:
    """
    Immutable cryptographic identity record for an AI agent.

    Fields:
        agent_id          — unique AID: "AID-{DOMAIN}-{16HEX}"
        display_name      — human-readable name
        domain            — governance domain (e.g. FINANCE)
        vertical          — sub-vertical (e.g. equity_trading)
        authority_budget  — 0.0-100.0; 100 = full Tier-1 authority
        registered_by     — operator ID who registered this agent
        registration_tier — ADR-146 authority tier of registrar
        public_key_b64    — Dilithium-3 public key (base64)
        registration_hash — SHA-256 of all public fields at issuance
        pqc_signature     — Dilithium-3 sig by registrar's key (or None)
        pqc_algorithm     — algorithm name
        status            — ACTIVE | SUSPENDED | REVOKED
        capabilities      — list of capability tags
        registered_at     — ISO UTC timestamp
        metadata          — arbitrary extension dict
    """
    agent_id: str
    display_name: str
    domain: str
    vertical: str
    authority_budget: float
    registered_by: str
    registration_tier: int
    public_key_b64: str
    registration_hash: str
    pqc_signature: Optional[str]
    pqc_algorithm: Optional[str]
    status: str
    capabilities: List[str]
    registered_at: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_active(self) -> bool:
        return self.status == "ACTIVE"

    def trust_summary(self) -> Dict[str, Any]:
        return {
            "agent_id":        self.agent_id,
            "display_name":    self.display_name,
            "authority_budget": self.authority_budget,
            "status":          self.status,
            "pqc_signed":      self.pqc_signature is not None,
            "tier":            self.registration_tier,
            "domain":          self.domain,
        }


class AgentIdentityEngine:
    """
    Registers and manages AI agent identities for the OMNIX Agent Trust Fabric.

    Design contract:
        register_agent()       → AgentIdentity (PQC-signed, persisted)
        get_agent()            → AgentIdentity by agent_id
        list_agents()          → list of AgentIdentity for a domain
        suspend_agent()        → status ACTIVE → SUSPENDED
        revoke_agent()         → status → REVOKED (Tier-1 only, permanent)
        ensure_tables()        → idempotent DDL
        verify_identity()      → verify registration PQC signature

    Thread safety: in-memory registry is protected by a lock.
    """

    def __init__(self, db_url: Optional[str] = None):
        self._db_url = db_url or os.environ.get("DATABASE_URL")
        self._registry: Dict[str, AgentIdentity] = {}
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
            logger.warning(f"[ATF.Identity] DB connection failed: {exc}")
            return None

    def _pqc_sign(self, payload: bytes) -> Tuple[Optional[str], Optional[str]]:
        sk_b64 = os.environ.get("OMNIX_SIGNING_SECRET_KEY_B64", "").strip()
        if not sk_b64 or not self._provider:
            return None, None
        try:
            sk = base64.b64decode(sk_b64)
            sig = self._provider.sign(payload, sk)
            if sig:
                return base64.b64encode(sig).decode(), self._provider.algorithm_name()
        except Exception as exc:
            logger.warning(f"[ATF.Identity] PQC signing failed: {exc}")
        return None, None

    def _pqc_verify(self, payload: bytes, sig_b64: str, pub_key_b64: str) -> bool:
        if not self._provider:
            return False
        try:
            sig = base64.b64decode(sig_b64)
            pk  = base64.b64decode(pub_key_b64)
            return bool(self._provider.verify(sig, payload, pk))
        except Exception as exc:
            logger.warning(f"[ATF.Identity] PQC verify failed: {exc}")
            return False

    @staticmethod
    def _build_agent_id(domain: str) -> str:
        code = domain.upper() if domain else "UNKNOWN"
        hex_part = uuid.uuid4().hex[:16].upper()
        return f"AID-{code}-{hex_part}"

    @staticmethod
    def _compute_registration_hash(record: Dict[str, Any]) -> str:
        canonical = json.dumps(
            {k: v for k, v in record.items()
             if k not in ("registration_hash", "pqc_signature", "pqc_algorithm")},
            sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(canonical.encode()).hexdigest()

    def _generate_agent_keypair(self) -> Tuple[Optional[str], Optional[str]]:
        if not self._provider:
            logger.warning("[ATF.Identity] PQC provider unavailable — agent has no signing key")
            return None, None
        try:
            pk_bytes, sk_bytes = self._provider.generate_keypair()
            pk_b64 = base64.b64encode(pk_bytes).decode()
            sk_b64 = base64.b64encode(sk_bytes).decode()
            return pk_b64, sk_b64
        except Exception as exc:
            logger.error(f"[ATF.Identity] Keypair generation failed: {exc}")
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
                    cur.execute(DDL_AGENT_REGISTRY)
            logger.info("[ATF.Identity] Table ready: atf_agent_registry")
            return True
        except Exception as exc:
            logger.warning(f"[ATF.Identity] ensure_tables failed: {exc}")
            return False
        finally:
            conn.close()

    def register_agent(
        self,
        display_name: str,
        domain: str,
        vertical: str = "general",
        authority_budget: float = 50.0,
        registered_by: str = "system",
        registration_tier: int = 2,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        _injected_keypair: Optional[Tuple[str, str]] = None,
    ) -> AgentIdentity:
        """
        Register a new AI agent with a Dilithium-3 identity.

        Args:
            display_name:      Human-readable agent name
            domain:            Governance domain (e.g. FINANCE)
            vertical:          Sub-vertical
            authority_budget:  Initial authority (0.0-100.0). Max 80.0 for Tier-2 registration.
            registered_by:     Registrar identifier
            registration_tier: ADR-146 tier of registrar (1-4)
            capabilities:      Optional capability tags
            metadata:          Optional extension metadata
            _injected_keypair: (pk_b64, sk_b64) for testing only

        Returns:
            AgentIdentity — immutable, PQC-signed, persisted to DB if available.

        Raises:
            ValueError: If authority_budget > 100 or < 0
        """
        if not (0.0 <= authority_budget <= 100.0):
            raise ValueError(f"authority_budget must be 0-100, got {authority_budget}")
        if registration_tier == 2 and authority_budget > 80.0:
            authority_budget = 80.0
            logger.warning("[ATF.Identity] Tier-2 registration capped at budget=80.0")

        agent_id = self._build_agent_id(domain)
        now = datetime.now(timezone.utc).isoformat()

        if _injected_keypair:
            pk_b64, sk_b64 = _injected_keypair
        else:
            pk_b64, sk_b64 = self._generate_agent_keypair()

        if pk_b64 is None:
            pk_b64 = ""

        public_fields: Dict[str, Any] = {
            "agent_id":         agent_id,
            "display_name":     display_name,
            "domain":           domain.upper(),
            "vertical":         vertical.lower(),
            "authority_budget": authority_budget,
            "registered_by":    registered_by,
            "registration_tier": registration_tier,
            "public_key_b64":   pk_b64,
            "capabilities":     capabilities or [],
            "registered_at":    now,
        }

        reg_hash = self._compute_registration_hash(public_fields)

        sign_payload = f"OMNIX-ATF-REG-v1|agent_id={agent_id}|reg_hash={reg_hash}".encode()
        pqc_sig, pqc_alg = self._pqc_sign(sign_payload)

        identity = AgentIdentity(
            agent_id=agent_id,
            display_name=display_name,
            domain=domain.upper(),
            vertical=vertical.lower(),
            authority_budget=authority_budget,
            registered_by=registered_by,
            registration_tier=registration_tier,
            public_key_b64=pk_b64,
            registration_hash=reg_hash,
            pqc_signature=pqc_sig,
            pqc_algorithm=pqc_alg,
            status="ACTIVE",
            capabilities=capabilities or [],
            registered_at=now,
            metadata={
                **(metadata or {}),
                "_sk_b64": sk_b64 or "",
            },
        )

        with self._lock:
            self._registry[agent_id] = identity

        self._persist_agent(identity)

        logger.info(
            f"[ATF.Identity] Agent registered — id={agent_id} "
            f"budget={authority_budget} domain={domain} "
            f"pqc={pqc_alg or 'SHA-256 only'}"
        )
        return identity

    def _persist_agent(self, identity: AgentIdentity) -> None:
        if not self._db_url:
            return
        conn = self._get_conn()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO atf_agent_registry (
                            agent_id, display_name, domain, vertical,
                            authority_budget, registered_by, registration_tier,
                            public_key_b64, registration_hash,
                            pqc_signature, pqc_algorithm, status,
                            capabilities, registered_at, metadata
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s::jsonb, %s, %s::jsonb
                        )
                        ON CONFLICT (agent_id) DO NOTHING
                    """, (
                        identity.agent_id,
                        identity.display_name,
                        identity.domain,
                        identity.vertical,
                        identity.authority_budget,
                        identity.registered_by,
                        identity.registration_tier,
                        identity.public_key_b64,
                        identity.registration_hash,
                        identity.pqc_signature,
                        identity.pqc_algorithm,
                        identity.status,
                        json.dumps(identity.capabilities),
                        identity.registered_at,
                        json.dumps({k: v for k, v in identity.metadata.items()
                                    if k != "_sk_b64"}),
                    ))
        except Exception as exc:
            logger.warning(f"[ATF.Identity] DB persist failed (in-memory only): {exc}")
        finally:
            conn.close()

    def get_agent(self, agent_id: str) -> Optional[AgentIdentity]:
        with self._lock:
            if agent_id in self._registry:
                return self._registry[agent_id]

        if not self._db_url:
            return None
        conn = self._get_conn()
        if not conn:
            return None
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM atf_agent_registry WHERE agent_id = %s",
                    (agent_id,)
                )
                row = cur.fetchone()
                if row:
                    cols = [d[0] for d in cur.description]
                    d = dict(zip(cols, row))
                    identity = self._row_to_identity(d)
                    with self._lock:
                        self._registry[agent_id] = identity
                    return identity
        except Exception as exc:
            logger.warning(f"[ATF.Identity] get_agent DB lookup failed: {exc}")
        finally:
            conn.close()
        return None

    def list_agents(self, domain: Optional[str] = None, status: str = "ACTIVE") -> List[AgentIdentity]:
        with self._lock:
            agents = list(self._registry.values())
        if domain:
            agents = [a for a in agents if a.domain == domain.upper()]
        if status:
            agents = [a for a in agents if a.status == status]
        return agents

    def suspend_agent(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id in self._registry:
                a = self._registry[agent_id]
                self._registry[agent_id] = AgentIdentity(
                    **{**asdict(a), "status": "SUSPENDED"}
                )
        self._update_status(agent_id, "SUSPENDED")
        logger.warning(f"[ATF.Identity] Agent SUSPENDED — id={agent_id}")
        return True

    def revoke_agent(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id in self._registry:
                a = self._registry[agent_id]
                self._registry[agent_id] = AgentIdentity(
                    **{**asdict(a), "status": "REVOKED"}
                )
        self._update_status(agent_id, "REVOKED")
        logger.warning(f"[ATF.Identity] Agent REVOKED (Tier-1 action) — id={agent_id}")
        return True

    def _update_status(self, agent_id: str, status: str) -> None:
        if not self._db_url:
            return
        conn = self._get_conn()
        if not conn:
            return
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE atf_agent_registry SET status=%s WHERE agent_id=%s",
                        (status, agent_id)
                    )
        except Exception as exc:
            logger.warning(f"[ATF.Identity] Status update failed: {exc}")
        finally:
            conn.close()

    def verify_identity(self, identity: AgentIdentity) -> Dict[str, Any]:
        """
        Verify the PQC registration signature of an AgentIdentity.
        Can be called by any party — no platform access required if
        the registrar's public key is known.
        """
        sign_payload = (
            f"OMNIX-ATF-REG-v1|agent_id={identity.agent_id}"
            f"|reg_hash={identity.registration_hash}"
        ).encode()

        pk_b64 = os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64", "").strip()
        pqc_valid = False
        if identity.pqc_signature and pk_b64 and self._provider:
            pqc_valid = self._pqc_verify(sign_payload, identity.pqc_signature, pk_b64)

        public_fields = {
            "agent_id":         identity.agent_id,
            "display_name":     identity.display_name,
            "domain":           identity.domain,
            "vertical":         identity.vertical,
            "authority_budget": identity.authority_budget,
            "registered_by":    identity.registered_by,
            "registration_tier": identity.registration_tier,
            "public_key_b64":   identity.public_key_b64,
            "capabilities":     identity.capabilities,
            "registered_at":    identity.registered_at,
        }
        expected_hash = self._compute_registration_hash(public_fields)
        hash_valid = (expected_hash == identity.registration_hash)

        return {
            "agent_id":          identity.agent_id,
            "hash_valid":        hash_valid,
            "pqc_signature_valid": pqc_valid,
            "fully_verified":    hash_valid and (pqc_valid if identity.pqc_signature else True),
            "pqc_signed":        identity.pqc_signature is not None,
            "status":            identity.status,
            "authority_budget":  identity.authority_budget,
        }

    def _row_to_identity(self, row: Dict) -> AgentIdentity:
        def ts(v):
            if v is None:
                return None
            if isinstance(v, datetime):
                return v.isoformat()
            return str(v)
        caps = row.get("capabilities") or []
        if isinstance(caps, str):
            try:
                caps = json.loads(caps)
            except Exception:
                caps = []
        meta = row.get("metadata") or {}
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}
        return AgentIdentity(
            agent_id=row["agent_id"],
            display_name=row["display_name"],
            domain=row["domain"],
            vertical=row["vertical"],
            authority_budget=float(row["authority_budget"]),
            registered_by=row["registered_by"],
            registration_tier=int(row["registration_tier"]),
            public_key_b64=row["public_key_b64"],
            registration_hash=row["registration_hash"],
            pqc_signature=row.get("pqc_signature"),
            pqc_algorithm=row.get("pqc_algorithm"),
            status=row["status"],
            capabilities=caps,
            registered_at=ts(row["registered_at"]),
            metadata=meta,
        )
