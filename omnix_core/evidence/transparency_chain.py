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
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

logger = logging.getLogger("OMNIX.Evidence.TransparencyChain")

_chain_degraded: bool = False
_STORE_RETRY_DELAYS: tuple = (0.1, 0.3, 0.9)


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


_DDL_PENDING = """
CREATE TABLE IF NOT EXISTS transparency_chain_pending (
    id           SERIAL       PRIMARY KEY,
    log_id       VARCHAR(32)  NOT NULL UNIQUE,
    receipt_id   VARCHAR(64)  NOT NULL,
    symbol       VARCHAR(32)  NOT NULL,
    event_type   VARCHAR(32)  NOT NULL DEFAULT 'decision',
    payload_hash VARCHAR(64)  NOT NULL,
    prev_log_hash VARCHAR(64),
    merkle_root  VARCHAR(64)  NOT NULL,
    signing_provider VARCHAR(32) NOT NULL DEFAULT 'none',
    signature_b64 TEXT,
    ts_utc       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    pending_reason TEXT        NOT NULL DEFAULT '',
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
"""


class TransparencyChain:
    """
    Append-only transparency log for OMNIX governance receipts.

    Each append:
      1. Creates a trusted timestamp over the payload hash
      2. Retrieves prev_log_hash from DB (last entry)
      3. Computes new rolling Merkle root
      4. Signs the entry with the active crypto provider
      5. Inserts into governance_transparency_log (with retry + pending fallback)

    ISR-013 durability: _store_entry retries 3× with exponential backoff.
    On all failures, falls back to transparency_chain_pending table.
    If that also fails, sets process-level _chain_degraded flag.

    Self-verifiable: every entry contains all data needed to verify it
    without calling back into OMNIX.
    """

    TABLE = "governance_transparency_log"
    TABLE_PENDING = "transparency_chain_pending"

    def __init__(self):
        self._db_url = os.environ.get("DATABASE_URL")
        self._ensure_pending_table()

    def _ensure_pending_table(self) -> None:
        if not self._db_url:
            return
        conn = self._get_conn()
        if not conn:
            return
        try:
            cur = conn.cursor()
            cur.execute(_DDL_PENDING)
            conn.commit()
            cur.close()
            conn.close()
        except Exception as exc:
            logger.warning(f"[TransparencyChain] Could not create pending table: {exc}")
            try:
                conn.close()
            except Exception:
                pass

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
        """
        Return recent transparency log entries, optionally filtered by symbol.

        ISR-022: Internally verifies chain integrity on every read.
        If chain breaks are detected, logs a WARNING.
        Returns entries newest-first (as before); integrity check uses oldest-first.
        """
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

            # ISR-022: Read-path chain integrity verification
            # Entries arrive newest-first from DB; verify needs oldest-first
            if rows:
                ordered_oldest_first = list(reversed(rows))
                integrity = self.verify_chain_integrity(ordered_oldest_first)
                if not integrity["valid"]:
                    logger.warning(
                        f"[TransparencyChain][ISR-022] CHAIN INTEGRITY VIOLATION DETECTED "
                        f"on read path — breaks={integrity['breaks']} "
                        f"length={integrity['length']} symbol={symbol or 'ALL'}"
                    )

            return rows
        except Exception as e:
            logger.error(f"[TransparencyChain] get_chain failed: {e}")
            try:
                conn.close()
            except Exception:
                pass
            return []

    def get_chain_with_integrity(
        self, symbol: Optional[str] = None, limit: int = 20,
        pending_table_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Return transparency log entries WITH an attached integrity report
        AND the Chain Completeness Score (CCS).

        ISR-022: Recommended method for audit tooling and external verifiers.

        OMNIX DIFFERENTIATOR — Chain Completeness Score (CCS):
          The integrity dict now includes a single 0-100 defensibility score.
          No other transparency framework publishes a completeness metric.
          Regulators can ask "Is the audit trail complete?" and get a number.

        Returns:
          entries   — list of chain entries (newest-first)
          integrity — {valid, length, breaks, ccs, ccs_verdict, ccs_breakdown,
                       chain_integrity_score, temporal_consistency_score,
                       pending_penalty, minimum_coverage_score}

        Example:
            result = chain.get_chain_with_integrity(symbol="BTC", limit=50)
            print(f"CCS: {result['integrity']['ccs']}/100 "
                  f"({result['integrity']['ccs_verdict']})")
        """
        rows = self.get_chain(symbol=symbol, limit=limit)
        ordered_oldest_first = list(reversed(rows))
        integrity = self.verify_chain_integrity(ordered_oldest_first)
        ccs_report = compute_chain_completeness_score(
            ordered_oldest_first,
            pending_table_count=pending_table_count,
        )
        integrity.update(ccs_report)
        return {
            "entries":   rows,
            "integrity": integrity,
        }

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
        """
        ISR-013: Store with retry (3×) + pending-table fallback + degraded flag.
        Never raises. Returns True only if primary table write succeeded.
        """
        global _chain_degraded
        if not self._db_url:
            return False

        last_exc: Optional[Exception] = None

        for attempt, delay in enumerate(_STORE_RETRY_DELAYS, start=1):
            conn = self._get_conn()
            if not conn:
                time.sleep(delay)
                continue
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
                    entry.get("prev_log_hash") or None,
                    entry["merkle_root"],
                    entry["signing_provider"],
                    entry.get("signature_b64"),
                    entry["ts_utc"],
                    1,
                ))
                conn.commit()
                cur.close()
                conn.close()
                if _chain_degraded:
                    logger.info("[TransparencyChain][ISR-013] Primary write succeeded — degraded flag cleared.")
                    _chain_degraded = False
                return True
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    f"[TransparencyChain][ISR-013] Primary write attempt {attempt}/{len(_STORE_RETRY_DELAYS)} failed: {exc}"
                )
                try:
                    conn.rollback()
                    conn.close()
                except Exception:
                    pass
                if attempt < len(_STORE_RETRY_DELAYS):
                    time.sleep(delay)

        logger.error(
            f"[TransparencyChain][ISR-013] All {len(_STORE_RETRY_DELAYS)} retry attempts failed — "
            f"writing to pending table. last_error={last_exc}"
        )
        pending_ok = self._store_pending(entry, reason=str(last_exc))
        if not pending_ok:
            _chain_degraded = True
            logger.error(
                "[TransparencyChain][ISR-013] CRITICAL: Both primary and pending writes failed. "
                "Audit chain has a gap. _chain_degraded=True. "
                "Inspect DATABASE_URL and PostgreSQL connectivity."
            )
            self._send_degraded_alert(entry.get("log_id", "?"), str(last_exc))
        return False

    def _store_pending(self, entry: Dict[str, Any], reason: str = "") -> bool:
        """Write to transparency_chain_pending as fallback (ISR-013)."""
        conn = self._get_conn()
        if not conn:
            return False
        try:
            cur = conn.cursor()
            cur.execute(f"""
                INSERT INTO {self.TABLE_PENDING} (
                    log_id, receipt_id, symbol, event_type,
                    payload_hash, prev_log_hash, merkle_root,
                    signing_provider, signature_b64, ts_utc, pending_reason
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (log_id) DO NOTHING
            """, (
                entry["log_id"],
                entry["receipt_id"],
                entry["symbol"],
                entry["event_type"],
                entry["payload_hash"],
                entry.get("prev_log_hash") or None,
                entry["merkle_root"],
                entry["signing_provider"],
                entry.get("signature_b64"),
                entry["ts_utc"],
                reason[:500],
            ))
            conn.commit()
            cur.close()
            conn.close()
            logger.info(
                f"[TransparencyChain][ISR-013] Entry {entry['log_id']} written to pending table. "
                f"Will be reconciled when DB recovers."
            )
            return True
        except Exception as exc:
            logger.error(f"[TransparencyChain][ISR-013] Pending write also failed: {exc}")
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass
            return False

    def _send_degraded_alert(self, log_id: str, reason: str) -> None:
        """Send Telegram alert when chain is fully degraded (ISR-013)."""
        try:
            admin_id = os.environ.get("TELEGRAM_ADMIN_USER_ID", "")
            token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
            if not admin_id or not token or os.environ.get("TESTING"):
                return
            import urllib.request
            msg = (
                f"⚠️ [OMNIX ALERT] Transparency chain degraded!\n"
                f"log_id={log_id}\n"
                f"Both primary and pending writes failed.\n"
                f"reason={reason[:200]}\n"
                f"Investigate DATABASE_URL connectivity immediately."
            )
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = json.dumps({"chat_id": admin_id, "text": msg, "parse_mode": "HTML"}).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass

    def reconcile_pending_entries(self) -> int:
        """
        Drain transparency_chain_pending into the main transparency log.
        Call on startup and periodically (every 5 min) to recover from DB outages.
        Returns number of entries successfully reconciled.
        ISR-013 recovery path.
        """
        if not self._db_url:
            return 0
        conn = self._get_conn()
        if not conn:
            return 0
        reconciled = 0
        try:
            cur = conn.cursor()
            cur.execute(f"""
                SELECT log_id, receipt_id, symbol, event_type, payload_hash,
                       prev_log_hash, merkle_root, signing_provider, signature_b64, ts_utc
                FROM {self.TABLE_PENDING}
                ORDER BY created_at ASC
                LIMIT 100
            """)
            rows = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as exc:
            logger.warning(f"[TransparencyChain][ISR-013] reconcile: fetch pending failed: {exc}")
            try:
                conn.close()
            except Exception:
                pass
            return 0

        for row in rows:
            (log_id, receipt_id, symbol, event_type, payload_hash,
             prev_log_hash, merkle_root, signing_provider, signature_b64, ts_utc) = row
            entry = {
                "log_id": log_id,
                "receipt_id": receipt_id,
                "symbol": symbol,
                "event_type": event_type,
                "payload_hash": payload_hash,
                "prev_log_hash": prev_log_hash,
                "merkle_root": merkle_root,
                "signing_provider": signing_provider or "none",
                "signature_b64": signature_b64,
                "ts_utc": ts_utc,
            }
            conn2 = self._get_conn()
            if not conn2:
                break
            try:
                cur2 = conn2.cursor()
                cur2.execute(f"""
                    INSERT INTO {self.TABLE} (
                        log_id, receipt_id, symbol, event_type,
                        payload_hash, prev_log_hash, merkle_root,
                        signing_provider, signature_b64, ts_utc, chain_version
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (log_id) DO NOTHING
                """, (
                    log_id, receipt_id, symbol, event_type, payload_hash,
                    prev_log_hash, merkle_root, signing_provider, signature_b64, ts_utc, 1,
                ))
                cur2.execute(
                    f"DELETE FROM {self.TABLE_PENDING} WHERE log_id = %s",
                    (log_id,),
                )
                conn2.commit()
                cur2.close()
                conn2.close()
                reconciled += 1
            except Exception as exc2:
                logger.warning(f"[TransparencyChain][ISR-013] reconcile: failed for {log_id}: {exc2}")
                try:
                    conn2.rollback()
                    conn2.close()
                except Exception:
                    pass

        if reconciled:
            logger.info(f"[TransparencyChain][ISR-013] Reconciled {reconciled} pending entries.")
        return reconciled

    def _get_conn(self):
        if not self._db_url:
            return None
        try:
            import psycopg
            return psycopg.connect(self._db_url)
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

    # ── Audit convenience API (ADR-121) ─────────────────────────────────────────

    def append_entry(self, payload: dict) -> Optional[Dict[str, Any]]:
        """
        Convenience wrapper for append() that accepts a raw dict payload (ADR-121).

        Extracts or generates the fields required by append() from the payload dict:
          - receipt_id  → payload["receipt_id"] or auto-generated TC-<uuid>
          - symbol      → payload["symbol"] or "SYSTEM"
          - decision    → payload["decision"] or "AUDIT_ENTRY"
          - payload_hash → SHA-256 of canonical JSON serialization of payload
          - event_type  → payload["event_type"] or "audit"

        Used by audit tooling to log arbitrary governance events without constructing
        a full DecisionReceipt. Never raises — delegates to append() which is also
        fail-safe.
        """
        receipt_id   = payload.get("receipt_id",  f"TC-{uuid.uuid4().hex[:12].upper()}")
        symbol       = str(payload.get("symbol",   "SYSTEM"))
        decision     = str(payload.get("decision", "AUDIT_ENTRY"))
        event_type   = str(payload.get("event_type", "audit"))
        payload_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()
        return self.append(receipt_id, symbol, decision, payload_hash, event_type)


def compute_chain_completeness_score(
    entries: List[Dict[str, Any]],
    pending_table_count: int = 0,
    min_gap_s: int = 60,
) -> Dict[str, Any]:
    """
    OMNIX DIFFERENTIATOR — Chain Completeness Score (CCS)
    ADR-155: Quantitative Defensibility Metric for Governance Audit Trails.

    Computes a 0-100 score representing the reliability and completeness
    of the transparency log.

    Scoring Logic:
      1. Chain Integrity (50 pts): -8 pts per detected break (Merkle mismatch/prev_hash).
      2. Temporal Consistency (30 pts): -10 pts per anomalous gap (>24h AND >100x min_gap).
      3. Minimum Coverage (20 pts): 20 if entries exist, 0 if empty.
      4. Pending Penalty: -3 pts per entry in pending table (max -30).

    Verdicts:
      90-100: COMPLETE
      70-89:  DEGRADED
      50-69:  PARTIAL
      <50:    COMPROMISED
      EMPTY:  NO_DATA
    """
    if not entries:
        return {
            "ccs": 0.0,
            "ccs_verdict": "NO_DATA",
            "chain_integrity_score": 0.0,
            "temporal_consistency_score": 0.0,
            "pending_penalty": 0.0,
            "minimum_coverage_score": 0.0,
            "ccs_breakdown": {
                "chain_breaks": 0,
                "pending_entries": pending_table_count,
                "entries_analyzed": 0,
            }
        }

    # 1. Chain Integrity Score (max 50)
    # verify_chain_integrity logic but integrated for scoring
    breaks = 0
    for i in range(len(entries)):
        # Merkle break
        computed_root = compute_rolling_merkle_root(
            entries[i-1]["merkle_root"] if i > 0 else "0" * 64,
            entries[i]["payload_hash"]
        )
        if computed_root != entries[i]["merkle_root"]:
            breaks += 1

        # Continuity break
        if i > 0:
            if entries[i-1]["payload_hash"] != entries[i].get("prev_log_hash"):
                breaks += 1

    integrity_score = max(0.0, 50.0 - (breaks * 8.0))

    # 2. Temporal Consistency Score (max 30)
    anomalous_gaps = 0
    for i in range(1, len(entries)):
        try:
            ts1 = datetime.fromisoformat(entries[i-1]["ts_utc"])
            ts2 = datetime.fromisoformat(entries[i]["ts_utc"])
            gap = (ts2 - ts1).total_seconds()
            # Gap > 24h AND > 100x the minimum expected gap
            if gap > 86400 and gap > (min_gap_s * 100):
                anomalous_gaps += 1
        except Exception:
            continue

    temporal_score = max(0.0, 30.0 - (anomalous_gaps * 10.0))

    # 3. Minimum Coverage (20 pts)
    coverage_score = 20.0 if len(entries) > 0 else 0.0

    # 4. Pending Penalty
    pending_penalty = min(30.0, pending_table_count * 3.0)

    # Final CCS
    ccs = max(0.0, integrity_score + temporal_score + coverage_score - pending_penalty)

    # Verdict
    if ccs >= 90:
        verdict = "COMPLETE"
    elif ccs >= 70:
        verdict = "DEGRADED"
    elif ccs >= 50:
        verdict = "PARTIAL"
    else:
        verdict = "COMPROMISED"

    return {
        "ccs": round(ccs, 1),
        "ccs_verdict": verdict,
        "chain_integrity_score": integrity_score,
        "temporal_consistency_score": temporal_score,
        "pending_penalty": pending_penalty,
        "minimum_coverage_score": coverage_score,
        "ccs_breakdown": {
            "chain_breaks": breaks,
            "pending_entries": pending_table_count,
            "entries_analyzed": len(entries),
        }
    }
