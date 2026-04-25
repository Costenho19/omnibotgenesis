"""
OMNIX Anti-Replay Guard — Phase 2
ADR-076 (Phase 1) + ADR-077 (Phase 2): Redis-backed nonce store with in-memory fallback.

Guarantees: a governance receipt (identified by receipt_id) cannot be submitted
for execution more than once within its TTL window.

Backend selection (automatic at import time):
    1. If REDIS_URL is set and Redis connects → Redis backend (cross-process, restart-safe)
    2. Otherwise → In-memory backend (single-process, ADR-076 Phase 1 semantics)

Runtime mode (OMNIX_ANTI_REPLAY_MODE env var):
    best_effort (default): Redis fail → in-memory fallback + WARNING
    strict:                 Redis fail → ReplayDetected raised (fail-closed)

Redis key design:
    omnix:ar:{receipt_id}  → value "1", TTL = max(ttl_ms, MIN_WINDOW_MS) ms

Public interface (unchanged from Phase 1 — ADR-076 guarantee):
    check_and_register(receipt_id, ttl_ms)   → None | raises ReplayDetected
    is_replay(receipt_id)                    → bool
    get_store()                              → AntiReplayStore

Harold Nunes — OMNIX QUANTUM LTD
ADR-076 (Phase 1) | ADR-077 (Phase 2) | April 2026
"""
from __future__ import annotations

import os
import threading
import time
import hashlib
import logging
from typing import Optional

logger = logging.getLogger("OMNIX.Evidence.AntiReplay")

MIN_WINDOW_MS: int = 30_000     # minimum replay window: 30s (ADR-076)
MAX_STORE_SIZE: int = 100_000   # safety cap — in-memory only

_REDIS_KEY_PREFIX = "omnix:ar:"
_MODE = os.environ.get("OMNIX_ANTI_REPLAY_MODE", "best_effort").lower().strip()
_STRICT_MODE: bool = _MODE == "strict"


class ReplayDetected(Exception):
    """Raised when a receipt_id has already been registered within its TTL window."""


# ── Redis client (lazy, optional) ─────────────────────────────────────────────

def _get_redis():
    """
    Return a raw Redis client if REDIS_URL is set and reachable.
    Returns None silently if Redis is not configured or unavailable.
    Does NOT import the cache module unconditionally — avoids circular imports.
    """
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        return None
    try:
        import redis as _redis_lib
        client = _redis_lib.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        logger.info("OMNIX.AntiReplay — Redis backend active (Phase 2)")
        return client
    except Exception as exc:
        logger.warning(
            f"OMNIX.AntiReplay — Redis unavailable ({exc}); "
            f"mode={_MODE}. {'Fail-closed active.' if _STRICT_MODE else 'Falling back to in-memory.'}"
        )
        return None


# ── In-memory store ───────────────────────────────────────────────────────────

class _InMemoryStore:
    """Phase 1 thread-safe in-memory store (ADR-076)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: dict[str, int] = {}

    def check_and_register(self, receipt_id: str, ttl_ms: int) -> None:
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
                        f"expires_in={remaining_s:.1f}s [in-memory]"
                    )
                    logger.warning(msg)
                    raise ReplayDetected(msg)

            if len(self._store) >= MAX_STORE_SIZE:
                msg = f"STORE_CAPACITY_EXCEEDED — cannot register {receipt_id}"
                logger.error(f"AntiReplayStore at capacity ({MAX_STORE_SIZE}). {msg}")
                raise ReplayDetected(msg)

            self._store[receipt_id] = expiry_ms
            logger.debug(f"anti-replay [mem] registered {receipt_id} ttl={window_ms/1000:.0f}s")

    def is_replay(self, receipt_id: str) -> bool:
        now_ms = int(time.time() * 1000)
        with self._lock:
            expiry = self._store.get(receipt_id)
            return expiry is not None and expiry > now_ms

    def revoke(self, receipt_id: str) -> bool:
        with self._lock:
            return self._store.pop(receipt_id, None) is not None

    def stats(self) -> dict:
        now_ms = int(time.time() * 1000)
        with self._lock:
            active = sum(1 for exp in self._store.values() if exp > now_ms)
            return {
                "backend": "in_memory",
                "total_entries": len(self._store),
                "active_entries": active,
                "expired_entries": len(self._store) - active,
                "mode": _MODE,
            }

    def _purge_expired_locked(self, now_ms: int) -> int:
        expired = [k for k, exp in self._store.items() if exp <= now_ms]
        for k in expired:
            del self._store[k]
        if expired:
            logger.debug(f"anti-replay purged {len(expired)} expired entries")
        return len(expired)


# ── Redis-backed store ─────────────────────────────────────────────────────────

class _RedisStore:
    """
    Phase 2 Redis-backed anti-replay store (ADR-077).

    Uses SET NX PX for atomic check-and-register.
    Cross-process and restart-safe when Redis persists.
    """

    def __init__(self, client) -> None:
        self._client = client

    def _key(self, receipt_id: str) -> str:
        return f"{_REDIS_KEY_PREFIX}{receipt_id}"

    def check_and_register(self, receipt_id: str, ttl_ms: int) -> None:
        window_ms = max(ttl_ms, MIN_WINDOW_MS)
        key = self._key(receipt_id)

        registered = self._client.set(key, "1", px=window_ms, nx=True)
        if not registered:
            ttl_remaining = self._client.pttl(key)
            remaining_s = ttl_remaining / 1000 if ttl_remaining > 0 else 0
            msg = (
                f"REPLAY_DETECTED receipt_id={receipt_id} "
                f"expires_in={remaining_s:.1f}s [redis]"
            )
            logger.warning(msg)
            raise ReplayDetected(msg)

        logger.debug(f"anti-replay [redis] registered {receipt_id} ttl={window_ms/1000:.0f}s")

    def is_replay(self, receipt_id: str) -> bool:
        return self._client.exists(self._key(receipt_id)) > 0

    def revoke(self, receipt_id: str) -> bool:
        deleted = self._client.delete(self._key(receipt_id))
        return bool(deleted)

    def stats(self) -> dict:
        try:
            count = len(self._client.keys(f"{_REDIS_KEY_PREFIX}*"))
        except Exception:
            count = -1
        return {
            "backend": "redis",
            "active_entries": count,
            "mode": _MODE,
        }


# ── Unified AntiReplayStore ───────────────────────────────────────────────────

class AntiReplayStore:
    """
    Unified anti-replay store. Transparently selects Redis or in-memory backend.

    Redis backend is used when REDIS_URL is configured and reachable.
    Fallback to in-memory depends on OMNIX_ANTI_REPLAY_MODE:
        best_effort (default): in-memory fallback with warning
        strict: ReplayDetected raised if Redis fails

    Public interface is identical to Phase 1 (ADR-076).
    """

    def __init__(self) -> None:
        self._mem = _InMemoryStore()
        redis_client = _get_redis()
        self._redis: Optional[_RedisStore] = _RedisStore(redis_client) if redis_client else None
        if self._redis:
            logger.info(f"AntiReplayStore — backend=redis mode={_MODE}")
        else:
            logger.info(f"AntiReplayStore — backend=in_memory mode={_MODE}")

    def _backend_or_fallback(self, operation: str, receipt_id: str, ttl_ms: int = MIN_WINDOW_MS):
        """Execute operation on Redis; fall back to in-memory based on mode."""
        if self._redis:
            try:
                return getattr(self._redis, operation)(receipt_id, ttl_ms) if ttl_ms != MIN_WINDOW_MS \
                    else getattr(self._redis, operation)(receipt_id, ttl_ms)
            except ReplayDetected:
                raise
            except Exception as exc:
                logger.error(f"AntiReplayStore — Redis error during {operation}: {exc}")
                if _STRICT_MODE:
                    raise ReplayDetected(
                        f"ANTI_REPLAY_BACKEND_FAILURE — Redis unavailable in strict mode. "
                        f"receipt_id={receipt_id}"
                    ) from exc
                logger.warning(
                    f"AntiReplayStore — Redis down, degrading to in-memory (best_effort). "
                    f"receipt_id={receipt_id}"
                )
        return None

    def check_and_register(self, receipt_id: str, ttl_ms: int = MIN_WINDOW_MS) -> None:
        """
        Atomically check if receipt_id is a replay and register it if not.

        Args:
            receipt_id: Canonical OMNIX receipt ID (e.g. OMNIX-TRD-ABC123DEF456).
            ttl_ms: How long (ms) to consider this ID as "used". Floor: MIN_WINDOW_MS.

        Raises:
            ReplayDetected: If already registered within TTL, or Redis fails in strict mode.
            ValueError: If receipt_id is empty or ttl_ms <= 0.
        """
        if not receipt_id:
            raise ValueError("receipt_id cannot be empty")
        if ttl_ms <= 0:
            raise ValueError(f"ttl_ms must be positive, got {ttl_ms}")

        if self._redis:
            try:
                self._redis.check_and_register(receipt_id, ttl_ms)
                return
            except ReplayDetected:
                raise
            except Exception as exc:
                logger.error(f"AntiReplayStore — Redis check_and_register failed: {exc}")
                if _STRICT_MODE:
                    raise ReplayDetected(
                        f"ANTI_REPLAY_BACKEND_FAILURE — Redis unavailable in strict mode. "
                        f"receipt_id={receipt_id}"
                    ) from exc
                logger.warning(
                    f"AntiReplayStore — Redis down, degrading to in-memory (best_effort). "
                    f"receipt_id={receipt_id}"
                )

        self._mem.check_and_register(receipt_id, ttl_ms)

    def is_replay(self, receipt_id: str) -> bool:
        """
        Read-only check: True if receipt_id is currently registered.
        Does NOT register the receipt_id.
        """
        if self._redis:
            try:
                return self._redis.is_replay(receipt_id)
            except Exception as exc:
                logger.error(f"AntiReplayStore — Redis is_replay failed: {exc}")
        return self._mem.is_replay(receipt_id)

    def revoke(self, receipt_id: str) -> bool:
        """
        Remove a receipt_id from the store (admin override / test teardown).
        Returns True if it was present.
        """
        redis_result = False
        if self._redis:
            try:
                redis_result = self._redis.revoke(receipt_id)
            except Exception as exc:
                logger.error(f"AntiReplayStore — Redis revoke failed: {exc}")
        mem_result = self._mem.revoke(receipt_id)
        return redis_result or mem_result

    def stats(self) -> dict:
        """Return current store statistics."""
        if self._redis:
            try:
                s = self._redis.stats()
                s["mode"] = _MODE
                s["strict"] = _STRICT_MODE
                return s
            except Exception:
                pass
        s = self._mem.stats()
        s["strict"] = _STRICT_MODE
        return s

    @property
    def backend(self) -> str:
        return "redis" if self._redis else "in_memory"


# ── Process-level singleton ────────────────────────────────────────────────────
# Same interface as Phase 1 (ADR-076). Backend is selected at import time.

_default_store = AntiReplayStore()


def check_and_register(receipt_id: str, ttl_ms: int = MIN_WINDOW_MS) -> None:
    """Module-level convenience — uses the process singleton."""
    _default_store.check_and_register(receipt_id, ttl_ms)


def is_replay(receipt_id: str) -> bool:
    """Module-level convenience — uses the process singleton."""
    return _default_store.is_replay(receipt_id)


def get_store() -> AntiReplayStore:
    """Return the process-level singleton store (for stats, testing, etc.)."""
    return _default_store


# ── Canonical alias (ADR-121) ────────────────────────────────────────────────
# AntiReplayGuard is the preferred name in audit scripts and external tooling.
# AntiReplayStore remains the primary class name for backward compatibility.
AntiReplayGuard = AntiReplayStore
