"""
OMNIX — Receipt Write-Ahead Log (WAL)
ISR-012 Remediation: Orphan-Decision Prevention

Problem (ISR-012):
  store_receipt() has no WAL or buffer. If PostgreSQL fails AFTER the
  governance engine evaluates and returns APPROVED/BLOCKED, but BEFORE
  the receipt is persisted, the decision exists in the world but is
  forensically invisible — no audit trail entry, no receipt in DB.

Solution:
  A lightweight, file-backed WAL that:
    1. Receives a receipt BEFORE the DB write attempt.
    2. If DB write succeeds → WAL entry is deleted (committed).
    3. If DB write fails → entry stays in WAL.
    4. On startup and periodically → reconcile_wal(store_fn) drains
       the WAL into the DB, guaranteeing eventual persistence.

WAL format: JSON Lines (one receipt dict per line).
Default path: $OMNIX_WAL_PATH or /tmp/omnix_receipt_wal.jsonl

Thread safety: ReceiptWAL uses a threading.Lock for all file operations.

ISR-012 | ADR-148 | Author: Harold Nunes — OMNIX QUANTUM LTD
"""

from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("OMNIX.Evidence.ReceiptWAL")

_DEFAULT_WAL_PATH = "/tmp/omnix_receipt_wal.jsonl"
_WAL_MAX_ENTRIES  = 10_000   # safety ceiling — prevents unbounded growth


class ReceiptWAL:
    """
    Write-Ahead Log for governance decision receipts.

    Guarantees that every evaluated governance decision has at least
    one durable copy (WAL file) before the primary DB write is attempted.

    Usage in store_receipt():
        wal = get_receipt_wal()
        wal_id = wal.wal_append(receipt)      # Step 1: WAL first
        ok = db_write(receipt)                # Step 2: DB write
        if ok:
            wal.wal_commit(wal_id)            # Step 3: delete from WAL
        # If not ok → receipt survives in WAL for reconcile_wal()

    Recovery:
        wal.reconcile_wal(store_fn)           # drain WAL into DB
    """

    def __init__(self, wal_path: Optional[str] = None):
        self._path = Path(wal_path or os.environ.get("OMNIX_WAL_PATH", _DEFAULT_WAL_PATH))
        self._lock = threading.Lock()
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            logger.warning(f"[WAL] Could not ensure WAL directory: {exc}")

    # ── Write ──────────────────────────────────────────────────────────────

    def wal_append(self, receipt: Dict[str, Any]) -> str:
        """
        Append a receipt to the WAL before attempting DB write.

        Returns a wal_id (UUID) that can be used to commit (delete)
        the entry once the primary DB write succeeds.

        Never raises — if WAL write fails, logs an error and returns
        an empty string (caller should proceed with DB write anyway).
        """
        wal_id = f"WAL-{uuid.uuid4().hex[:16].upper()}"
        entry = {
            "_wal_id":    wal_id,
            "_wal_ts":    datetime.now(timezone.utc).isoformat(),
            "_committed": False,
            **receipt,
        }
        try:
            with self._lock:
                size = self.wal_size()
                if size >= _WAL_MAX_ENTRIES:
                    logger.error(
                        f"[WAL][ISR-012] WAL ceiling reached ({size} entries). "
                        f"DB connectivity lost? Run reconcile_wal() urgently. "
                        f"Skipping WAL append for receipt={receipt.get('receipt_id', '?')}"
                    )
                    return ""
                with self._path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, default=str) + "\n")
            logger.debug(
                f"[WAL][ISR-012] Appended receipt={receipt.get('receipt_id','?')} "
                f"wal_id={wal_id}"
            )
            return wal_id
        except Exception as exc:
            logger.error(f"[WAL][ISR-012] wal_append failed: {exc}")
            return ""

    def wal_commit(self, wal_id: str) -> bool:
        """
        Mark a WAL entry as committed (DB write succeeded).

        Rewrites the WAL file excluding the committed entry.
        Returns True if the entry was found and removed.
        """
        if not wal_id:
            return False
        try:
            with self._lock:
                if not self._path.exists():
                    return False
                lines = self._path.read_text(encoding="utf-8").splitlines()
                new_lines = []
                found = False
                for line in lines:
                    try:
                        entry = json.loads(line)
                        if entry.get("_wal_id") == wal_id:
                            found = True
                            continue
                        new_lines.append(line)
                    except Exception:
                        new_lines.append(line)
                if found:
                    self._path.write_text("\n".join(new_lines) + ("\n" if new_lines else ""), encoding="utf-8")
                    logger.debug(f"[WAL][ISR-012] Committed wal_id={wal_id}")
                return found
        except Exception as exc:
            logger.error(f"[WAL][ISR-012] wal_commit failed: {exc}")
            return False

    # ── Read ───────────────────────────────────────────────────────────────

    def wal_size(self) -> int:
        """Return number of uncommitted entries in the WAL."""
        try:
            if not self._path.exists():
                return 0
            count = 0
            with self._path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        count += 1
            return count
        except Exception:
            return 0

    def wal_entries(self) -> List[Dict[str, Any]]:
        """Return all uncommitted WAL entries (oldest first)."""
        try:
            if not self._path.exists():
                return []
            entries = []
            with self._path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entries.append(json.loads(line))
                    except Exception as exc:
                        logger.warning(f"[WAL] Corrupt WAL line skipped: {exc}")
            return entries
        except Exception as exc:
            logger.error(f"[WAL] wal_entries read failed: {exc}")
            return []

    # ── Recovery ───────────────────────────────────────────────────────────

    def reconcile_wal(self, store_fn: Callable[[Dict[str, Any]], bool]) -> int:
        """
        Drain WAL into the primary DB by calling store_fn for each entry.

        store_fn should accept a receipt dict and return True on success.
        Successfully committed entries are removed from the WAL.

        Returns number of entries successfully reconciled.

        Call on startup and periodically (e.g. every 5 minutes) to ensure
        no receipts are permanently lost after DB outages.
        """
        entries = self.wal_entries()
        if not entries:
            return 0

        logger.info(f"[WAL][ISR-012] Reconciling {len(entries)} pending WAL entries...")
        reconciled = 0

        for entry in entries:
            wal_id = entry.get("_wal_id", "")
            receipt = {k: v for k, v in entry.items() if not k.startswith("_")}

            try:
                ok = store_fn(receipt)
                if ok:
                    self.wal_commit(wal_id)
                    reconciled += 1
                    logger.info(
                        f"[WAL][ISR-012] Reconciled receipt={receipt.get('receipt_id','?')} "
                        f"wal_id={wal_id}"
                    )
                else:
                    logger.warning(
                        f"[WAL][ISR-012] store_fn returned False for "
                        f"receipt={receipt.get('receipt_id','?')} — keeping in WAL"
                    )
            except Exception as exc:
                logger.error(
                    f"[WAL][ISR-012] store_fn raised for "
                    f"receipt={receipt.get('receipt_id','?')}: {exc}"
                )

        if reconciled:
            logger.info(f"[WAL][ISR-012] Reconciliation complete: {reconciled}/{len(entries)} entries committed.")

        return reconciled

    @property
    def wal_path(self) -> str:
        return str(self._path)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE-LEVEL SINGLETON
# ─────────────────────────────────────────────────────────────────────────────

_wal_instance: Optional[ReceiptWAL] = None
_wal_init_lock = threading.Lock()


def get_receipt_wal() -> ReceiptWAL:
    """
    Return the process-level ReceiptWAL singleton.
    Thread-safe double-checked locking.
    """
    global _wal_instance
    if _wal_instance is None:
        with _wal_init_lock:
            if _wal_instance is None:
                _wal_instance = ReceiptWAL()
                logger.info(
                    f"[WAL][ISR-012] ReceiptWAL initialized — path={_wal_instance.wal_path} "
                    f"pending={_wal_instance.wal_size()}"
                )
    return _wal_instance
