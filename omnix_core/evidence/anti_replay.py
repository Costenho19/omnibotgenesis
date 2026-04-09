"""
OMNIX Anti-Replay Guard
ADR-075 §5: Nonce-based receipt replay prevention within TTL windows.

Guarantees: a governance receipt (identified by receipt_id) cannot be
submitted for execution more than once within its TTL window.

Design:
    - Thread-safe in-process store (threading.Lock + dict).
    - Each entry expires automatically after max(ttl_ms, MIN_WINDOW_MS).
    - `check_and_register()` is atomic: check + register in one locked operation.
    - Expired entries are purged lazily on every call (amortised O(n) worst case,
      typically O(1) because entries expire in FIFO order).

Limitations:
    - In-process only: does NOT protect across multiple worker processes or
      across restarts. For multi-process / persistent anti-replay, wire
      check_and_register() to a Redis SET with EX (see ADR-076 roadmap).
    - Suitable for single-instance deployment (Railway, Render, Fly.io single dyno).

Usage:
    from omnix_core.evidence.anti_replay import AntiReplayStore

    store = AntiReplayStore()   # one instance per process (singleton below)

    try:
        store.check_and_register(receipt_id, ttl_ms=30_000)
    except ReplayDetected as e:
        return 409_CONFLICT, str(e)

Harold Nunes — OMNIX QUANTUM LTD
ADR-075 §5 | April 2026
"""
from __future__ import annotations

import threading
import time
import logging

logger = logging.getLogger("OMNIX.Evidence.AntiReplay")

MIN_WINDOW_MS: int = 30_000     # minimum replay window: 30s
MAX_STORE_SIZE: int = 100_000   # safety cap to prevent unbounded memory growth


class ReplayDetected(Exception):
    """Raised when a receipt_id has already been registered within its TTL window."""


class AntiReplayStore:
    """
    Thread-safe in-memory anti-replay store.

    Entries: { receipt_id: expiry_epoch_ms }
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: dict[str, int] = {}   # receipt_id → expiry_epoch_ms

    def check_and_register(self, receipt_id: str, ttl_ms: int = MIN_WINDOW_MS) -> None:
        """
        Atomically check if receipt_id is a replay and register it if not.

        Args:
            receipt_id: The canonical OMNIX receipt ID (e.g. OMNIX-TRD-ABC123DEF456).
            ttl_ms: How long (ms) to consider this ID as "used". Defaults to MIN_WINDOW_MS.

        Raises:
            ReplayDetected: If this receipt_id was already registered and has not expired.
            ValueError: If receipt_id is empty or ttl_ms <= 0.
        """
        if not receipt_id:
            raise ValueError("receipt_id cannot be empty")
        if ttl_ms <= 0:
            raise ValueError(f"ttl_ms must be positive, got {ttl_ms}")

        window_ms = max(ttl_ms, MIN_WINDOW_MS)
        now_ms = int(time.time() * 1000)
        expiry_ms = now_ms + window_ms

        with self._lock:
            self._purge_expired_locked(now_ms)

            if receipt_id in self._store:
                existing_expiry = self._store[receipt_id]
                if existing_expiry > now_ms:
                    remaining_s = (existing_expiry - now_ms) / 1000
                    msg = (
                        f"REPLAY_DETECTED receipt_id={receipt_id} "
                        f"expires_in={remaining_s:.1f}s"
                    )
                    logger.warning(msg)
                    raise ReplayDetected(msg)

            if len(self._store) >= MAX_STORE_SIZE:
                logger.error(
                    f"AntiReplayStore at capacity ({MAX_STORE_SIZE}). "
                    f"Possible memory leak or DDoS. Rejecting new registration."
                )
                raise ReplayDetected(
                    f"STORE_CAPACITY_EXCEEDED — cannot register {receipt_id}"
                )

            self._store[receipt_id] = expiry_ms
            logger.debug(f"anti-replay registered {receipt_id} expires_in={window_ms/1000:.0f}s")

    def is_replay(self, receipt_id: str) -> bool:
        """
        Read-only check: returns True if the receipt_id is currently registered
        (i.e. would be rejected by check_and_register).
        Does NOT register the receipt_id.
        """
        now_ms = int(time.time() * 1000)
        with self._lock:
            expiry = self._store.get(receipt_id)
            return expiry is not None and expiry > now_ms

    def revoke(self, receipt_id: str) -> bool:
        """
        Manually remove a receipt_id from the store (e.g. for test teardown
        or administrative override). Returns True if it was present.
        """
        with self._lock:
            return self._store.pop(receipt_id, None) is not None

    def stats(self) -> dict:
        """Return current store statistics (non-blocking snapshot)."""
        now_ms = int(time.time() * 1000)
        with self._lock:
            active = sum(1 for exp in self._store.values() if exp > now_ms)
            return {
                "total_entries": len(self._store),
                "active_entries": active,
                "expired_entries": len(self._store) - active,
            }

    def _purge_expired_locked(self, now_ms: int) -> int:
        """
        Remove all expired entries. Must be called with self._lock held.
        Returns the number of entries removed.
        """
        expired = [k for k, exp in self._store.items() if exp <= now_ms]
        for k in expired:
            del self._store[k]
        if expired:
            logger.debug(f"anti-replay purged {len(expired)} expired entries")
        return len(expired)


# ── Process-level singleton ──────────────────────────────────────────────────
# Import this and use it directly — no need to instantiate per request.
# In multi-process deploys, each worker has its own instance (acceptable for
# single-dyno Railway/Render deployments). For multi-worker, use Redis backend.

_default_store = AntiReplayStore()


def check_and_register(receipt_id: str, ttl_ms: int = MIN_WINDOW_MS) -> None:
    """Module-level convenience function using the process singleton."""
    _default_store.check_and_register(receipt_id, ttl_ms)


def is_replay(receipt_id: str) -> bool:
    """Module-level convenience function using the process singleton."""
    return _default_store.is_replay(receipt_id)


def get_store() -> AntiReplayStore:
    """Return the process-level singleton store (for stats, testing, etc.)."""
    return _default_store
