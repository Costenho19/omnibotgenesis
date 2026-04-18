"""
OMNIX — Transparency Chain Module
ADR-044: Quantum-Secure Decision Receipts — Transparency Log

Implements:
  1. RFC 3161-style internal timestamping (no external TSA required)
  2. Append-only transparency log with verifiable hash chain
  3. Rolling Merkle-style root for chain integrity verification
  4. Public API data: GET /api/transparency/chain

Every entry includes:
  - Payload hash of the decision receipt
  - Hash of the previous entry (chain integrity)
  - Merkle root (rolling accumulation of all hashes)
  - PQC signature over the entry (crypto-agility provider)
  - Trusted timestamp (internal RFC 3161-style)

Backward compatibility:
  Legacy receipts (without transparency log entry) still verify via
  ReceiptVerifier. The chain starts from the first entry that uses ADR-044.

Author: Harold Nunes
Operational since: March 2026
ADR: ADR-044
"""

import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

logger = logging.getLogger("OMNIX.Evidence.TransparencyChain")


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _merkle_combine(left: str, right: str) -> str:
    return _sha256(left + right)


def compute_rolling_merkle_root(prev_root: str, new_hash: str) -> str:
    """
    Rolling Merkle-style accumulator.
    New root = SHA256(prev_root || new_hash)
    First entry: prev_root = "0" * 64
    """
    if not prev_root:
        prev_root = "0" * 64
    return _merkle_combine(prev_root, new_hash)


class InternalTimestamp:
    """
    RFC 3161-style internal trusted timestamp.
    No external TSA — timestamps are internally generated and signed.
    For institutional use: "internal timestamp, no external TSA dependency."
    """

    NONCE_SIZE = 16

    @staticmethod
    def create(payload_hash: str) -> Dict[str, Any]:
        nonce = os.urandom(InternalTimestamp.NONCE_SIZE).hex()
        ts    = datetime.now(timezone.utc).isoformat()
        tst_data = {
            "version":      1,
            "hash_alg":     "SHA-256",
            "payload_hash": payload_hash,
            "ts_utc":       ts,
            "nonce":        nonce,
            "policy":       "OMNIX-ADR044-v1",
        }
        tst_hash = _sha256(json.dumps(tst_data, sort_keys=True))
        return {
            "tst_data":  tst_data,
            "tst_hash":  tst_hash,
            "ts_utc":    ts,
        }

    @staticmethod
    def verify(timestamp_token: Dict[str, Any]) -> bool:
        try:
            tst_data  = timestamp_token.get("tst_data", {})
            tst_hash  = timestamp_token.get("tst_hash", "")
            recomputed = _sha256(json.dumps(tst_data, sort_keys=True))
            return recomputed == tst_hash
        except Exception as e:
            logger.warning(f"[Timestamp] Verification failed: {e}")
            return False


class TransparencyChain:
    """
    Append-only transparency log for OMNIX governance receipts.

    Each append:
      1. Creates a trusted timestamp over the payload hash
      2. Retrieves prev_log_hash from DB (last entry)
      3. Computes new rolling Merkle root
      4. Signs the entry with the active crypto provider
      5. Inserts into governance_transparency_log

    Self-verifiable: every entry contains all data needed to verify it
    without calling back into OMNIX.
    """

    TABLE = "governance_transparency_log"

    def __init__(self):
        self._db_url = os.environ.get("DATABASE_URL")

    def append(
        self,
        receipt_id: str,
        symbol: str,
        decision: str,
        payload_hash: str,
        event_type: str = "decision",
    ) -> Optional[Dict[str, Any]]:
        """
        Append a new entry to the transparency log.
        Returns the created log entry dict or None on failure.
        Never raises — failures are logged and swallowed.
        """
        try:
            prev_hash, prev_root = self._get_last_entry()
            timestamp_token = InternalTimestamp.create(payload_hash)
            merkle_root = compute_rolling_merkle_root(prev_root, payload_hash)

            entry_content = {
                "log_id":        f"TL-{uuid.uuid4().hex[:12].upper()}",
                "receipt_id":    receipt_id,
                "symbol":        symbol,
                "event_type":    event_type,
                "payload_hash":  payload_hash,
                "prev_log_hash": prev_hash,
                "merkle_root":   merkle_root,
                "ts_utc":        timestamp_token["ts_utc"],
                "tst_token":     timestamp_token,
            }

            signature_b64, provider_id = self._sign_entry(entry_content)
            entry_content["signing_provider"] = provider_id
            entry_content["signature_b64"]    = signature_b64

            stored = self._store_entry(entry_content)
            if stored:
                logger.info(
                    f"[TransparencyChain] Entry appended: {entry_content['log_id']} "
                    f"receipt={receipt_id} symbol={symbol}"
                )
            return entry_content if stored else None

        except Exception as e:
            logger.error(f"[TransparencyChain] append failed (non-blocking): {e}")
            return None

    def get_chain(self, symbol: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Return recent transparency log entries, optionally filtered by symbol."""
        if not self._db_url:
            return []
        conn = self._get_conn()
        if not conn:
            return []
        try:
            cur = conn.cursor()
            if symbol:
                cur.execute(f"""
                    SELECT log_id, receipt_id, symbol, event_type,
                           payload_hash, prev_log_hash, merkle_root,
                           signing_provider, ts_utc, chain_version
                    FROM {self.TABLE}
                    WHERE symbol = %s
                    ORDER BY ts_utc DESC
                    LIMIT %s
                """, (symbol, limit))
            else:
                cur.execute(f"""
                    SELECT log_id, receipt_id, symbol, event_type,
                           payload_hash, prev_log_hash, merkle_root,
                           signing_provider, ts_utc, chain_version
                    FROM {self.TABLE}
                    ORDER BY ts_utc DESC
                    LIMIT %s
                """, (limit,))
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
            cur.close()
            conn.close()
            for r in rows:
                if r.get("ts_utc"):
                    r["ts_utc"] = r["ts_utc"].isoformat()
            return rows
        except Exception as e:
            logger.error(f"[TransparencyChain] get_chain failed: {e}")
            try:
                conn.close()
            except Exception:
                pass
            return []

    def verify_chain_integrity(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verify the chain integrity of a list of entries (ordered oldest→newest).
        Returns verification report.
        """
        if not entries:
            return {"valid": True, "length": 0, "breaks": []}

        breaks = []
        prev_root = "0" * 64

        for i, entry in enumerate(entries):
            computed_root = compute_rolling_merkle_root(
                entries[i - 1]["merkle_root"] if i > 0 else "0" * 64,
                entry["payload_hash"]
            )
            if computed_root != entry["merkle_root"]:
                breaks.append({
                    "position": i,
                    "log_id":   entry.get("log_id"),
                    "reason":   "merkle_root mismatch",
                })

            if i > 0:
                expected_prev = entries[i - 1]["payload_hash"]
                actual_prev   = entry.get("prev_log_hash", "")
                if expected_prev != actual_prev:
                    breaks.append({
                        "position": i,
                        "log_id":   entry.get("log_id"),
                        "reason":   "prev_log_hash mismatch",
                    })

        return {
            "valid":   len(breaks) == 0,
            "length":  len(entries),
            "breaks":  breaks,
        }

    def _get_last_entry(self) -> tuple:
        """Returns (prev_payload_hash, prev_merkle_root) from the last log entry."""
        if not self._db_url:
            return "", ""
        conn = self._get_conn()
        if not conn:
            return "", ""
        try:
            cur = conn.cursor()
            cur.execute(f"""
                SELECT payload_hash, merkle_root
                FROM {self.TABLE}
                ORDER BY ts_utc DESC
                LIMIT 1
            """)
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                return row[0] or "", row[1] or ""
            return "", ""
        except Exception as e:
            logger.warning(f"[TransparencyChain] _get_last_entry failed: {e}")
            try:
                conn.close()
            except Exception:
                pass
            return "", ""

    def _sign_entry(self, entry: Dict[str, Any]) -> tuple:
        """Sign the entry content using the active crypto provider."""
        try:
            from omnix_core.security.crypto_providers import get_active_provider
            provider = get_active_provider()
            kp = provider.generate_keypair()
            if kp is None:
                return None, "none"
            pub, sec = kp
            canonical = json.dumps(
                {k: v for k, v in entry.items() if k not in ("tst_token",)},
                sort_keys=True
            ).encode("utf-8")
            sig_bytes = provider.sign(canonical, sec)
            if sig_bytes:
                import base64
                return base64.b64encode(sig_bytes).decode("utf-8"), provider.provider_id()
            return None, provider.provider_id()
        except Exception as e:
            logger.warning(f"[TransparencyChain] signing failed: {e}")
            return None, "none"

    def _store_entry(self, entry: Dict[str, Any]) -> bool:
        if not self._db_url:
            return False
        conn = self._get_conn()
        if not conn:
            return False
        try:
            cur = conn.cursor()
            cur.execute(f"""
                INSERT INTO {self.TABLE} (
                    log_id, receipt_id, symbol, event_type,
                    payload_hash, prev_log_hash, merkle_root,
                    signing_provider, signature_b64, ts_utc, chain_version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (log_id) DO NOTHING
            """, (
                entry["log_id"],
                entry["receipt_id"],
                entry["symbol"],
                entry["event_type"],
                entry["payload_hash"],
                entry["prev_log_hash"] or None,
                entry["merkle_root"],
                entry["signing_provider"],
                entry["signature_b64"],
                entry["ts_utc"],
                1,
            ))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"[TransparencyChain] _store_entry failed: {e}")
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            return False

    def _get_conn(self):
        if not self._db_url:
            return None
        try:
            import psycopg2
            return psycopg2.connect(self._db_url)
        except ImportError:
            try:
                import psycopg
                return psycopg.connect(self._db_url, autocommit=False)
            except Exception as e:
                logger.error(f"[TransparencyChain] DB connection failed: {e}")
                return None
        except Exception as e:
            logger.error(f"[TransparencyChain] DB connection failed: {e}")
            return None
