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
    from pqc.sign import dilithium3
    PQC_AVAILABLE = True
except ImportError:
    PQC_AVAILABLE = False
    dilithium3 = None


class DecisionReceiptEngine:

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.environ.get('DATABASE_URL')
        self._signing_keys: Optional[Tuple[bytes, bytes]] = None
        self._init_keys()

    def _init_keys(self):
        if not PQC_AVAILABLE:
            logger.warning("PQC not available - receipts will use SHA-256 only")
            return
        try:
            self._signing_keys = dilithium3.keypair()
            logger.info("Receipt signing keys generated (Dilithium-3)")
        except Exception as e:
            logger.error(f"Failed to generate signing keys: {e}")

    @property
    def public_key_b64(self) -> Optional[str]:
        if self._signing_keys:
            return base64.b64encode(self._signing_keys[0]).decode('utf-8')
        return None

    def generate_receipt(self, decision: Dict[str, Any], prev_hash: str = "") -> Dict[str, Any]:
        receipt_id = f"OMNIX-{uuid.uuid4().hex[:12].upper()}"
        timestamp = datetime.now(timezone.utc).isoformat()

        public_payload = {
            'receipt_id': receipt_id,
            'timestamp': timestamp,
            'asset': decision.get('symbol', decision.get('asset', 'UNKNOWN')),
            'decision': decision.get('decision', 'UNKNOWN').upper(),
            'veto_chain': self._extract_veto_chain(decision),
            'policy_version': decision.get('policy_version', os.environ.get('OMNIX_VERSION', '6.5.4e')),
            'engine_version': os.environ.get('OMNIX_VERSION', '6.5.4e'),
            'prev_hash': prev_hash,
        }

        content_hash = self._compute_hash(public_payload)
        public_payload['content_hash'] = content_hash

        signature_b64 = None
        if self._signing_keys and PQC_AVAILABLE:
            try:
                message = content_hash.encode('utf-8')
                raw_sig = dilithium3.sign(message, self._signing_keys[1])
                signature_b64 = base64.b64encode(raw_sig).decode('utf-8')
            except Exception as e:
                logger.error(f"Failed to sign receipt: {e}")

        public_payload['signature'] = signature_b64
        public_payload['signature_algorithm'] = 'Dilithium-3 (ML-DSA-65)' if signature_b64 else 'NONE'
        public_payload['public_key'] = self.public_key_b64

        return public_payload

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
        try:
            import psycopg2
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO decision_receipts 
                (receipt_id, timestamp_utc, asset, decision, veto_chain, 
                 policy_version, engine_version, prev_hash, content_hash,
                 signature, signature_algorithm, public_key)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                receipt['public_key']
            ))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Failed to store receipt: {e}")
            return False

    def get_last_hash(self) -> str:
        if not self.db_url:
            return ""
        try:
            import psycopg2
            conn = psycopg2.connect(self.db_url)
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
            return ""


class ReceiptVerifier:

    @staticmethod
    def verify_receipt(receipt: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            'receipt_id': receipt.get('receipt_id', 'UNKNOWN'),
            'hash_valid': False,
            'signature_valid': False,
            'chain_valid': None,
            'verification_timestamp': datetime.now(timezone.utc).isoformat(),
        }

        payload_for_hash = {
            'receipt_id': receipt.get('receipt_id'),
            'timestamp': receipt.get('timestamp'),
            'asset': receipt.get('asset'),
            'decision': receipt.get('decision'),
            'veto_chain': receipt.get('veto_chain'),
            'policy_version': receipt.get('policy_version'),
            'engine_version': receipt.get('engine_version'),
            'prev_hash': receipt.get('prev_hash'),
        }

        canonical = json.dumps(payload_for_hash, sort_keys=True, ensure_ascii=True)
        computed_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
        result['hash_valid'] = (computed_hash == receipt.get('content_hash'))
        result['computed_hash'] = computed_hash
        result['stored_hash'] = receipt.get('content_hash')

        sig_b64 = receipt.get('signature')
        pub_key_b64 = receipt.get('public_key')

        if sig_b64 and pub_key_b64 and PQC_AVAILABLE:
            try:
                signature = base64.b64decode(sig_b64)
                public_key = base64.b64decode(pub_key_b64)
                message = receipt['content_hash'].encode('utf-8')
                dilithium3.verify(signature, message, public_key)
                result['signature_valid'] = True
            except Exception:
                result['signature_valid'] = False
        elif not PQC_AVAILABLE:
            result['signature_valid'] = None
            result['signature_note'] = 'PQC library not available for verification'
        elif not sig_b64:
            result['signature_valid'] = None
            result['signature_note'] = 'Receipt was not signed'

        result['overall_valid'] = result['hash_valid'] and (result['signature_valid'] is not False)
        result['algorithm'] = receipt.get('signature_algorithm', 'UNKNOWN')

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
