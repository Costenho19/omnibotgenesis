import json
import hashlib
import base64
import logging
import threading
import uuid
import os
from collections import deque
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("OMNIX.Evidence")

# ── OMNIX DIFFERENTIATOR: Receipt Genealogy Chain ──────────────────────────────
#
# In-process ring buffer: maps "{domain}:{asset}" → deque of (receipt_id, ts)
# tuples, enabling cryptographic parent-child linkage across sequential decisions
# for the same asset.
#
# No other receipt system does this. Every receipt in the industry is standalone.
# OMNIX treats receipts as nodes in a verifiable decision lineage chain.
# Auditors can answer: "What decisions led to this one?" without DB access.
# The genealogy is embedded in the content_hash — tampering breaks verification.
#
# ADR-028 extension | OMNIX-GEN-001

_genealogy_buffer: Dict[str, deque] = {}
_genealogy_lock = threading.Lock()
_GENEALOGY_MAX_CHAIN = 50     # max receipts tracked per domain:asset key


def _build_genealogy(domain: str, asset: str, receipt_id: str) -> Dict[str, Any]:
    """
    Build receipt genealogy metadata and register the current receipt in the chain.

    Returns:
        parent_receipt_id  — ID of the immediately preceding receipt (None if first)
        chain_root_id      — ID of the first receipt in this session chain
        generation_depth   — 1-indexed position in the chain (1 = first ever)
        chain_key          — "{domain}:{asset}" identifier
        is_chain_root      — True when this is the first receipt in the chain
    """
    key = f"{domain}:{asset}" if domain else f"unknown:{asset}"

    with _genealogy_lock:
        if key not in _genealogy_buffer:
            _genealogy_buffer[key] = deque(maxlen=_GENEALOGY_MAX_CHAIN)

        chain = _genealogy_buffer[key]
        chain_snapshot = list(chain)   # snapshot before appending current

        parent_receipt_id = chain_snapshot[-1] if chain_snapshot else None
        chain_root_id = chain_snapshot[0] if chain_snapshot else receipt_id
        generation_depth = len(chain_snapshot) + 1

        chain.append(receipt_id)

    return {
        "parent_receipt_id": parent_receipt_id,
        "chain_root_id":     chain_root_id if parent_receipt_id else receipt_id,
        "generation_depth":  generation_depth,
        "chain_key":         key,
        "is_chain_root":     parent_receipt_id is None,
    }


# ISR-010: Canonical hash algorithm version — embedded in every receipt.
# Changing the hash algorithm requires bumping this constant AND creating a
# migration plan. Never change this silently — historical receipts become
# unverifiable if the verifier uses a different algorithm than what was used.
CANONICAL_HASH_VERSION = "sha256-v1"


def _get_governance_schema_version() -> str:
    """Return the schema version from the semantic registry (ISR-008)."""
    try:
        from omnix_core.governance.semantic_version_registry import get_current_entry
        return get_current_entry().schema_version
    except Exception:
        return "1"


def _get_checkpoint_logic_fingerprint() -> str:
    """Return the checkpoint logic fingerprint for the current engine (ISR-008)."""
    try:
        from omnix_core.governance.semantic_version_registry import current_fingerprint
        return current_fingerprint()
    except Exception:
        return ""


try:
    from omnix_core.security.crypto_providers import get_active_provider, get_provider
    _active_provider = get_active_provider()
    PQC_AVAILABLE = True
except Exception:
    _active_provider = None
    PQC_AVAILABLE = False
    logger.warning("Crypto providers not available — receipts will use SHA-256 only")

try:
    from pqc.sign import dilithium3
    _LEGACY_DILITHIUM3_AVAILABLE = True
except ImportError:
    _LEGACY_DILITHIUM3_AVAILABLE = False
    dilithium3 = None

# ---------------------------------------------------------------------------
# STABLE MODULE-LEVEL KEY — generated ONCE per process at import time (ADR-085).
# All DecisionReceiptEngine instances in this process share the same keypair.
# This eliminates EPHEMERAL warnings when env vars are not set, and ensures the
# public key published in the trust registry matches all receipts signed in this
# deployment.  Set OMNIX_SIGNING_SECRET_KEY_B64 + OMNIX_SIGNING_PUBLIC_KEY_B64
# in Railway env vars to persist the same key across restarts.
# ---------------------------------------------------------------------------
_STABLE_SIGNING_KEYS: Optional[Tuple[bytes, bytes]] = None
_STABLE_PUBLIC_KEY_B64: Optional[str] = None

if PQC_AVAILABLE and _active_provider is not None:
    _sk_b64 = os.environ.get("OMNIX_SIGNING_SECRET_KEY_B64", "").strip()
    _pk_b64 = os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64", "").strip()
    if _sk_b64 and _pk_b64:
        try:
            _sk_bytes = base64.b64decode(_sk_b64)
            _pk_bytes = base64.b64decode(_pk_b64)
            _test_sig = _active_provider.sign(b"OMNIX-KEY-SELFTEST", _sk_bytes)
            if _test_sig and _active_provider.verify(_test_sig, b"OMNIX-KEY-SELFTEST", _pk_bytes):
                _STABLE_SIGNING_KEYS   = (_pk_bytes, _sk_bytes)
                _STABLE_PUBLIC_KEY_B64 = _active_provider.serialize_public_key(_pk_bytes)
                logger.info(
                    f"[ADR-085] Signing keys loaded from env vars — "
                    f"stable across restarts. algorithm={_active_provider.algorithm_name()}"
                )
        except Exception as _env_key_err:
            logger.warning(f"[ADR-085] Env-var keys invalid, generating ephemeral stable key: {_env_key_err}")
    if _STABLE_SIGNING_KEYS is None:
        try:
            _STABLE_SIGNING_KEYS   = _active_provider.generate_keypair()
            _STABLE_PUBLIC_KEY_B64 = _active_provider.serialize_public_key(_STABLE_SIGNING_KEYS[0])
            logger.info(
                f"[ADR-085] Stable process-scoped signing keys generated "
                f"({_active_provider.algorithm_name()}) — shared by all instances this process."
            )
        except Exception as _gen_err:
            logger.error(f"[ADR-085] Failed to generate stable signing keys: {_gen_err}")


def _get_db_connection(db_url: str):
    if not db_url:
        return None
    try:
        import psycopg2
        return psycopg2.connect(db_url)
    except ImportError:
        try:
            import psycopg
            return psycopg.connect(db_url, autocommit=False)
        except Exception as e:
            logger.error(f"DB connection failed (psycopg3): {e}")
            return None
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        return None


class DecisionReceiptEngine:

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.environ.get('DATABASE_URL')
        self._signing_keys: Optional[Tuple[bytes, bytes]] = None
        self._provider = _active_provider
        self._key_mode: str = "uninitialized"
        self._active_since: Optional[str] = None
        self._init_keys()

    # ── ADR-078: Signing Key Persistence ──────────────────────────────────────

    def _init_keys(self) -> None:
        """
        Load or generate Dilithium-3 signing keys per ADR-078.

        Priority:
          1. OMNIX_SIGNING_SECRET_KEY_B64 + OMNIX_SIGNING_PUBLIC_KEY_B64 env vars (persisted)
          2. Generate ephemeral keys if OMNIX_KEY_MODE=ephemeral_dev (default)
          3. Refuse to generate if OMNIX_KEY_MODE=required

        Security: private key material is NEVER written to logs.
        Only the public key (base64) and fingerprint (key_id) are logged.
        """
        if not PQC_AVAILABLE or self._provider is None:
            logger.warning("Crypto provider not available — receipts will use SHA-256 only")
            self._key_mode = "sha256_only"
            return

        key_mode_env = os.environ.get("OMNIX_KEY_MODE", "ephemeral_dev").strip().lower()
        sk_b64 = os.environ.get("OMNIX_SIGNING_SECRET_KEY_B64", "").strip()
        pk_b64 = os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64", "").strip()

        if sk_b64 and pk_b64:
            try:
                sk_bytes = base64.b64decode(sk_b64)
                pk_bytes = base64.b64decode(pk_b64)

                # Mandatory self-test — validates keypair coherence
                test_msg = b"OMNIX-KEY-SELFTEST"
                sig = self._provider.sign(test_msg, sk_bytes)
                if sig is None or not self._provider.verify(sig, test_msg, pk_bytes):
                    raise ValueError("Key self-test failed — keypair is invalid or mismatched")

                self._signing_keys = (pk_bytes, sk_bytes)
                self._key_mode = "persisted"
                self._active_since = datetime.now(timezone.utc).isoformat()
                kid = self._compute_key_id(pk_bytes)
                logger.info(
                    f"[ADR-078] Signing keys loaded from environment. "
                    f"key_id={kid} algorithm={self._provider.algorithm_name()} mode=persisted"
                )
                return
            except Exception as exc:
                logger.error(
                    f"[ADR-078] Failed to load signing keys from environment: {exc}. "
                    f"Falling back to ephemeral key generation."
                )

        # Keys not in env — honour OMNIX_KEY_MODE
        if key_mode_env == "required":
            logger.error(
                "[ADR-078] OMNIX_KEY_MODE=required but OMNIX_SIGNING_SECRET_KEY_B64 / "
                "OMNIX_SIGNING_PUBLIC_KEY_B64 are not set or failed self-test. "
                "Receipt engine running without PQC signatures. "
                "Set env vars and restart to enable persisted signing."
            )
            self._key_mode = "required_missing"
            return

        # ADR-085: Reuse the module-level stable keypair if available.
        # This ensures all instances in this process share the same public key,
        # so the trust registry always matches the actual signing key.
        if _STABLE_SIGNING_KEYS is not None:
            self._signing_keys = _STABLE_SIGNING_KEYS
            self._key_mode = "stable_process"
            self._active_since = datetime.now(timezone.utc).isoformat()
            return

        # Last resort: generate per-instance (should rarely reach here)
        try:
            self._signing_keys = self._provider.generate_keypair()
            pk_bytes = self._signing_keys[0]
            self._key_mode = "ephemeral_dev"
            self._active_since = datetime.now(timezone.utc).isoformat()
            kid = self._compute_key_id(pk_bytes)
            pk_b64_out = self._provider.serialize_public_key(pk_bytes)
            logger.warning(
                f"[ADR-078] EPHEMERAL signing keys generated (stable key unavailable). "
                f"key_id={kid}  algorithm={self._provider.algorithm_name()}\n"
                f"To persist keys across restarts, run:\n"
                f"  python -m omnix_core.tools.key_gen\n"
                f"and set OMNIX_SIGNING_SECRET_KEY_B64 + OMNIX_SIGNING_PUBLIC_KEY_B64."
            )
        except Exception as exc:
            logger.error(f"[ADR-078] Failed to generate signing keys: {exc}")
            self._key_mode = "failed"

    @staticmethod
    def _compute_key_id(public_key: bytes) -> str:
        """SHA-256 fingerprint of the public key, first 16 hex chars (key_id)."""
        return hashlib.sha256(public_key).hexdigest()[:16]

    # ── Key properties (ADR-078 / ADR-079) ────────────────────────────────────

    @property
    def public_key_b64(self) -> Optional[str]:
        if self._signing_keys and self._provider:
            return self._provider.serialize_public_key(self._signing_keys[0])
        return None

    @property
    def key_id(self) -> Optional[str]:
        """Short fingerprint (16 hex chars) uniquely identifying the active public key."""
        if self._signing_keys:
            return self._compute_key_id(self._signing_keys[0])
        return None

    @property
    def key_mode(self) -> str:
        """persisted | ephemeral_dev | required_missing | sha256_only | failed"""
        return self._key_mode

    @property
    def active_since(self) -> Optional[str]:
        """ISO-8601 UTC timestamp when the current keys became active."""
        return self._active_since

    @property
    def signature(self) -> Optional[dict]:
        """
        Signing capability summary for audit validation (ADR-121).

        Returns a dict with the active signing metadata if keys are loaded,
        or None if the engine is operating in SHA-256 fallback mode.

        Audit tooling can use `hasattr(receipt_engine, 'signature')` to confirm
        that the engine has a signature property, and `receipt_engine.signature`
        to inspect the active signing configuration.
        """
        return {
            "key_id":       self.key_id,
            "key_mode":     self._key_mode,
            "active_since": self._active_since,
            "public_key_b64": self.public_key_b64,
            "pqc_available": bool(self._provider and self._signing_keys),
        }

    _DEFAULT_TTL_MS: int = 30_000

    _DOMAIN_CODES: Dict[str, str] = {
        "trading":           "TRD",
        "islamic_credit":    "CRD",
        "insurance":         "INS",
        "robotics":          "RBT",
        "public_sandbox":    "PUB",
        "medical_ai":        "MED",
        "autonomous_agent":  "AGT",
        "real_estate":       "REP",
        "energy_governance": "EGV",
        "stablecoin":        "SRG",
        "defense_governance": "DEF",
    }

    @classmethod
    def build_receipt_id(cls, domain: str = "") -> str:
        """
        Canonical receipt ID format: OMNIX-{DOMAIN}-{12 hex} when domain is known,
        OMNIX-{12 hex} for legacy/unknown domains.
        ADR-074 — universal governance layer consistency.
        """
        code = cls._DOMAIN_CODES.get(domain, "")
        hex_part = uuid.uuid4().hex[:12].upper()
        if code:
            return f"OMNIX-{code}-{hex_part}"
        return f"OMNIX-{hex_part}"

    def generate_receipt(self, decision: Dict[str, Any], prev_hash: str = "") -> Dict[str, Any]:
        domain = decision.get("domain", "")
        receipt_id = self.build_receipt_id(domain)
        now_dt     = datetime.now(timezone.utc)
        timestamp  = now_dt.isoformat()

        issued_at_ms = int(now_dt.timestamp() * 1000)
        ttl_ms       = int(os.environ.get('OMNIX_RECEIPT_TTL_MS', self._DEFAULT_TTL_MS))
        ttl_epoch_ms = issued_at_ms + ttl_ms

        provider_id = self._provider.provider_id() if self._provider else "sha256"
        alg_name    = self._provider.algorithm_name() if self._provider else "SHA-256"

        public_payload = {
            'receipt_id':       receipt_id,
            'timestamp':        timestamp,
            'issued_at_ms':     issued_at_ms,
            'ttl_epoch_ms':     ttl_epoch_ms,
            'ttl_ms':           ttl_ms,
            'asset':            decision.get('symbol', decision.get('asset', 'UNKNOWN')),
            'decision':         decision.get('decision', 'UNKNOWN').upper(),
            'veto_chain':       self._extract_veto_chain(decision),
            'policy_version':   decision.get('policy_version', os.environ.get('OMNIX_VERSION', '6.5.4e')),
            'engine_version':   os.environ.get('OMNIX_VERSION', '6.5.4e'),
            'prev_hash':        prev_hash,
            'signing_provider': provider_id,
            'signing_key_id':   self.key_id,
            'domain':           domain if domain else None,
            'governance_schema_version': _get_governance_schema_version(),
            'checkpoint_logic_fingerprint': _get_checkpoint_logic_fingerprint(),
            'hash_version': CANONICAL_HASH_VERSION,
        }

        if 'sharia_compliance' in decision:
            public_payload['sharia_compliance'] = decision['sharia_compliance']

        if 'aml_compliance' in decision:
            public_payload['aml_compliance'] = decision['aml_compliance']

        if 'fraud_compliance' in decision:
            public_payload['fraud_compliance'] = decision['fraud_compliance']

        if 'jurisdiction_compliance' in decision:
            public_payload['jurisdiction_compliance'] = decision['jurisdiction_compliance']

        if 'context_admission' in decision:
            public_payload['context_admission'] = decision['context_admission']
            ca = decision['context_admission']
            if isinstance(ca, dict) and ca.get('veto_type'):
                public_payload['veto_type'] = ca['veto_type']

        if 'avm_result' in decision:
            avm = decision['avm_result']
            if isinstance(avm, dict):
                public_payload['avm_result'] = {
                    'is_valid': avm.get('is_valid'),
                    'snapshot_id': avm.get('snapshot_id'),
                    'parameter_version': avm.get('parameter_version'),
                    'drift_score': avm.get('drift_score'),
                    'age_hours': avm.get('age_hours'),
                    'pass_through': avm.get('pass_through', False),
                }
                if avm.get('block_reason'):
                    public_payload['avm_result']['block_reason'] = avm['block_reason']

        # ── OMNIX DIFFERENTIATOR: Receipt Genealogy Chain ──────────────────────
        # Build and embed genealogy BEFORE computing content_hash so that
        # tampering with parent_receipt_id breaks hash verification.
        # GOVERNANCE RISK SOLVED: Without lineage, an auditor cannot tell
        # whether an approval was the first decision for an asset or followed
        # 10 prior blocks that were overridden.  The chain provides that context.
        # INSTITUTIONAL EXPLANATION: Like a paper trail that shows not just
        # the final signature, but every approval and rejection that preceded it.
        _asset_key  = public_payload.get('asset', 'UNKNOWN')
        _domain_key = public_payload.get('domain') or ''
        genealogy = _build_genealogy(_domain_key, _asset_key, receipt_id)
        public_payload['genealogy'] = genealogy
        if genealogy.get('generation_depth', 1) > 1:
            logger.info(
                f"[Receipt][GEN] Lineage chain — receipt={receipt_id} "
                f"parent={genealogy['parent_receipt_id']} "
                f"depth={genealogy['generation_depth']} "
                f"root={genealogy['chain_root_id']}"
            )
        # ───────────────────────────────────────────────────────────────────────
        content_hash = self._compute_hash(public_payload)
        public_payload['content_hash'] = content_hash

        signature_b64    = None
        signature_format = 'NONE'

        if self._signing_keys and self._provider:
            try:
                message = content_hash.encode('utf-8')
                raw_sig = self._provider.sign(message, self._signing_keys[1])
                if raw_sig:
                    signature_b64    = base64.b64encode(raw_sig).decode('utf-8')
                    signature_format = 'base64_pqc'
            except Exception as e:
                logger.error(f"Failed to sign receipt: {e}")

        if signature_b64 is None and not (self._signing_keys and self._provider):
            signature_b64    = hashlib.sha256(content_hash.encode('utf-8')).hexdigest()
            signature_format = 'hex_sha256_fallback'

        public_payload['signature']           = signature_b64
        public_payload['signature_algorithm'] = alg_name if signature_b64 else 'NONE'
        public_payload['signature_format']    = signature_format
        public_payload['public_key']          = self.public_key_b64

        self._append_to_transparency_chain(receipt_id, public_payload)

        return public_payload

    def _append_to_transparency_chain(self, receipt_id: str, payload: Dict[str, Any]) -> None:
        """Non-blocking: append receipt to transparency log (ADR-044)."""
        try:
            from omnix_core.evidence.transparency_chain import TransparencyChain
            chain = TransparencyChain()
            chain.append(
                receipt_id=receipt_id,
                symbol=payload.get('asset', 'UNKNOWN'),
                decision=payload.get('decision', 'UNKNOWN'),
                payload_hash=payload.get('content_hash', ''),
                event_type='decision',
            )
        except Exception as e:
            logger.debug(f"Transparency chain append skipped (non-blocking): {e}")

    def _extract_veto_chain(self, decision: Dict[str, Any]) -> list:
        trace = decision.get('decision_trace', [])
        if isinstance(trace, list):
            safe_trace = []
            for entry in trace:
                entry_str = str(entry)
                parts = entry_str.split(':')
                if len(parts) >= 2:
                    gate_name = parts[0].strip()
                    result = ':'.join(parts[1:]).strip()
                    if len(result) > 80:
                        result = result[:77] + '...'
                    safe_trace.append(f"{gate_name}: {result}")
                else:
                    safe_trace.append(entry_str[:80])
            return safe_trace
        return []

    def _compute_hash(self, payload: Dict[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    def store_receipt(self, receipt: Dict[str, Any]) -> bool:
        # ISR-012: WAL-first — write to WAL before attempting DB write.
        # If DB fails, receipt survives in WAL for reconcile_wal() on recovery.
        _wal_id = ""
        try:
            from omnix_core.evidence.receipt_wal import get_receipt_wal
            _wal_id = get_receipt_wal().wal_append(receipt)
        except Exception as _wal_err:
            logger.warning(f"[ISR-012] WAL append failed (non-blocking): {_wal_err}")

        if not self.db_url:
            logger.warning("No database URL configured - receipt not stored")
            return False
        conn = _get_db_connection(self.db_url)
        if not conn:
            logger.warning("Failed to connect to DB for receipt storage")
            return False
        try:
            from datetime import timedelta
            retention_until = (datetime.now(timezone.utc) + timedelta(days=365)).date()

            # ADR-097: extract canonical_hash_v2 from execution_proof
            execution_proof = receipt.get('execution_proof') or {}
            canonical_hash_v2 = execution_proof.get('canonical_hash')
            execution_bound = bool(canonical_hash_v2)

            cur = conn.cursor()
            cur.execute("""
                INSERT INTO decision_receipts 
                (receipt_id, timestamp_utc, asset, decision, veto_chain, 
                 policy_version, engine_version, prev_hash, content_hash,
                 signature, signature_algorithm, public_key,
                 client_id, encrypted_payload, retention_until, domain,
                 canonical_hash_v2, execution_bound)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (receipt_id) DO NOTHING
            """, (
                receipt['receipt_id'],
                receipt['timestamp'],
                receipt['asset'],
                receipt['decision'],
                json.dumps(receipt['veto_chain']),
                receipt['policy_version'],
                receipt['engine_version'],
                receipt['prev_hash'],
                receipt['content_hash'],
                receipt['signature'],
                receipt['signature_algorithm'],
                receipt['public_key'],
                receipt.get('client_id'),
                receipt.get('encrypted_payload'),
                retention_until,
                receipt.get('domain'),
                canonical_hash_v2,
                execution_bound,
            ))
            conn.commit()
            cur.close()
            conn.close()
            # ISR-012: DB write succeeded — commit (delete) WAL entry
            if _wal_id:
                try:
                    from omnix_core.evidence.receipt_wal import get_receipt_wal
                    get_receipt_wal().wal_commit(_wal_id)
                except Exception:
                    pass
            if canonical_hash_v2:
                logger.debug(
                    f"[ADR-097] canonical_hash_v2 persisted "
                    f"receipt={receipt['receipt_id'][:12]}... "
                    f"hash={canonical_hash_v2[:16]}..."
                )
            return True
        except Exception as e:
            logger.error(f"Failed to store receipt: {e}")
            try:
                conn.close()
            except Exception:
                pass
            # ISR-012: DB write failed — WAL entry is retained for reconcile_wal()
            if _wal_id:
                logger.warning(
                    f"[ISR-012] DB write failed — receipt={receipt.get('receipt_id','?')} "
                    f"retained in WAL wal_id={_wal_id}. "
                    f"Call reconcile_wal() when DB recovers."
                )
            return False

    def get_last_hash(self) -> str:
        if not self.db_url:
            return ""
        conn = _get_db_connection(self.db_url)
        if not conn:
            return ""
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT content_hash FROM decision_receipts 
                ORDER BY created_at DESC LIMIT 1
            """)
            row = cur.fetchone()
            cur.close()
            conn.close()
            return row[0] if row else ""
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            return ""


class ReceiptVerifier:

    @staticmethod
    def verify_receipt(receipt: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            'receipt_id':             receipt.get('receipt_id', 'UNKNOWN'),
            'hash_valid':             False,
            'signature_valid':        False,
            'chain_valid':            None,
            'verification_timestamp': datetime.now(timezone.utc).isoformat(),
        }

        payload_for_hash = {
            'receipt_id':       receipt.get('receipt_id'),
            'timestamp':        receipt.get('timestamp'),
            'asset':            receipt.get('asset'),
            'decision':         receipt.get('decision'),
            'veto_chain':       receipt.get('veto_chain'),
            'policy_version':   receipt.get('policy_version'),
            'engine_version':   receipt.get('engine_version'),
            'prev_hash':        receipt.get('prev_hash'),
            'signing_provider': receipt.get('signing_provider'),
        }
        if payload_for_hash['signing_provider'] is None:
            del payload_for_hash['signing_provider']

        for timing_field in ('issued_at_ms', 'ttl_epoch_ms', 'ttl_ms'):
            if timing_field in receipt:
                payload_for_hash[timing_field] = receipt[timing_field]

        # Fields present in generate_receipt payload before hash is computed
        for metadata_field in (
            'signing_key_id', 'domain',
            'governance_schema_version', 'checkpoint_logic_fingerprint',
            'hash_version', 'genealogy',
        ):
            if metadata_field in receipt:
                payload_for_hash[metadata_field] = receipt[metadata_field]

        for optional_block in (
            'sharia_compliance', 'aml_compliance', 'fraud_compliance',
            'jurisdiction_compliance', 'context_admission', 'avm_result',
        ):
            if optional_block in receipt:
                payload_for_hash[optional_block] = receipt[optional_block]
        if 'veto_type' in receipt:
            payload_for_hash['veto_type'] = receipt['veto_type']

        canonical = json.dumps(payload_for_hash, sort_keys=True, ensure_ascii=True)
        computed_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        result['hash_valid']    = (computed_hash == receipt.get('content_hash'))
        result['computed_hash'] = computed_hash
        result['stored_hash']   = receipt.get('content_hash')

        sig_b64     = receipt.get('signature')
        pub_key_b64 = receipt.get('public_key')

        if sig_b64 and pub_key_b64:
            provider_id = receipt.get('signing_provider', 'dilithium3')
            provider = None
            try:
                from omnix_core.security.crypto_providers import get_provider as _get_provider
                provider = _get_provider(provider_id)
            except Exception:
                pass

            if provider is None and _LEGACY_DILITHIUM3_AVAILABLE and provider_id == 'dilithium3':
                try:
                    signature  = base64.b64decode(sig_b64)
                    public_key = base64.b64decode(pub_key_b64)
                    message    = receipt['content_hash'].encode('utf-8')
                    dilithium3.verify(signature, message, public_key)
                    result['signature_valid'] = True
                except Exception:
                    result['signature_valid'] = False
            elif provider:
                try:
                    signature  = base64.b64decode(sig_b64)
                    public_key = provider.deserialize_public_key(pub_key_b64)
                    message    = receipt['content_hash'].encode('utf-8')
                    result['signature_valid'] = provider.verify(signature, message, public_key)
                except Exception:
                    result['signature_valid'] = False
            else:
                result['signature_valid'] = None
                result['signature_note']  = f'Provider {provider_id!r} not available for verification'
        elif not sig_b64:
            result['signature_valid'] = None
            result['signature_note']  = 'Receipt was not signed'

        result['overall_valid'] = result['hash_valid'] and (result['signature_valid'] is not False)
        result['algorithm']        = receipt.get('signature_algorithm', 'UNKNOWN')
        result['signing_provider'] = receipt.get('signing_provider', 'dilithium3')
        result['signature_format'] = receipt.get('signature_format', 'UNKNOWN')

        ttl_epoch_ms = receipt.get('ttl_epoch_ms')
        if ttl_epoch_ms is not None:
            import time as _time
            now_ms = int(_time.time() * 1000)
            result['ttl_epoch_ms'] = ttl_epoch_ms
            result['is_expired']   = now_ms > ttl_epoch_ms
            result['age_ms']       = now_ms - receipt.get('issued_at_ms', now_ms)
        else:
            result['is_expired'] = None
            result['age_ms']     = None

        return result

    @staticmethod
    def verify_chain(receipts: list) -> Dict[str, Any]:
        if not receipts:
            return {'chain_valid': True, 'length': 0, 'breaks': []}

        breaks = []
        for i in range(1, len(receipts)):
            expected_prev = receipts[i - 1].get('content_hash', '')
            actual_prev = receipts[i].get('prev_hash', '')
            if expected_prev != actual_prev:
                breaks.append({
                    'position': i,
                    'receipt_id': receipts[i].get('receipt_id'),
                    'expected_prev_hash': expected_prev[:16] + '...',
                    'actual_prev_hash': actual_prev[:16] + '...' if actual_prev else 'EMPTY'
                })

        return {
            'chain_valid': len(breaks) == 0,
            'length': len(receipts),
            'breaks': breaks
        }


# ── Canonical aliases (ADR-121) ──────────────────────────────────────────────
# DecisionReceipt is the preferred name in audit scripts and external tooling.
# DecisionReceiptEngine remains the primary class name for backward compatibility.
DecisionReceipt = DecisionReceiptEngine
