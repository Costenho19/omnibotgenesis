import json
import hashlib
import base64
import logging
import uuid
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("OMNIX.Evidence")

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
        self._init_keys()

    def _init_keys(self):
        if not PQC_AVAILABLE or self._provider is None:
            logger.warning("Crypto provider not available - receipts will use SHA-256 only")
            return
        try:
            self._signing_keys = self._provider.generate_keypair()
            logger.info(f"Receipt signing keys generated ({self._provider.algorithm_name()})")
        except Exception as e:
            logger.error(f"Failed to generate signing keys: {e}")

    @property
    def public_key_b64(self) -> Optional[str]:
        if self._signing_keys and self._provider:
            return self._provider.serialize_public_key(self._signing_keys[0])
        return None

    def generate_receipt(self, decision: Dict[str, Any], prev_hash: str = "") -> Dict[str, Any]:
        receipt_id = f"OMNIX-{uuid.uuid4().hex[:12].upper()}"
        timestamp = datetime.now(timezone.utc).isoformat()

        provider_id = self._provider.provider_id() if self._provider else "sha256"
        alg_name    = self._provider.algorithm_name() if self._provider else "SHA-256"

        public_payload = {
            'receipt_id':       receipt_id,
            'timestamp':        timestamp,
            'asset':            decision.get('symbol', decision.get('asset', 'UNKNOWN')),
            'decision':         decision.get('decision', 'UNKNOWN').upper(),
            'veto_chain':       self._extract_veto_chain(decision),
            'policy_version':   decision.get('policy_version', os.environ.get('OMNIX_VERSION', '6.5.4e')),
            'engine_version':   os.environ.get('OMNIX_VERSION', '6.5.4e'),
            'prev_hash':        prev_hash,
            'signing_provider': provider_id,
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

        content_hash = self._compute_hash(public_payload)
        public_payload['content_hash'] = content_hash

        signature_b64 = None
        if self._signing_keys and self._provider:
            try:
                message   = content_hash.encode('utf-8')
                raw_sig   = self._provider.sign(message, self._signing_keys[1])
                if raw_sig:
                    signature_b64 = base64.b64encode(raw_sig).decode('utf-8')
            except Exception as e:
                logger.error(f"Failed to sign receipt: {e}")

        if signature_b64 is None and not (self._signing_keys and self._provider):
            signature_b64 = hashlib.sha256(content_hash.encode('utf-8')).hexdigest()

        public_payload['signature']           = signature_b64
        public_payload['signature_algorithm'] = alg_name if signature_b64 else 'NONE'
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

            cur = conn.cursor()
            cur.execute("""
                INSERT INTO decision_receipts 
                (receipt_id, timestamp_utc, asset, decision, veto_chain, 
                 policy_version, engine_version, prev_hash, content_hash,
                 signature, signature_algorithm, public_key,
                 client_id, encrypted_payload, retention_until, domain)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            ))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to store receipt: {e}")
            try:
                conn.close()
            except Exception:
                pass
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
        result['algorithm']     = receipt.get('signature_algorithm', 'UNKNOWN')
        result['signing_provider'] = receipt.get('signing_provider', 'dilithium3')

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
