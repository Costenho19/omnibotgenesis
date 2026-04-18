"""
Tests for ADR-077: Redis Anti-Replay Guard Phase 2

Tests the Redis backend, mode switching, and fallback behaviour.
Redis is mocked throughout — no real Redis connection required.

Harold Nunes — OMNIX QUANTUM LTD
"""
import os
import threading
import time
import unittest
from unittest.mock import MagicMock, patch


# ── Helpers ────────────────────────────────────────────────────────────────────

def _fresh_store(**env_overrides):
    """Create a fresh AntiReplayStore with optional env var overrides and mocked Redis."""
    with patch.dict(os.environ, env_overrides, clear=False):
        import importlib
        import omnix_core.evidence.anti_replay as ar_mod
        importlib.reload(ar_mod)
        store = ar_mod.AntiReplayStore()
    return store, ar_mod


# ── T001-R1: In-memory store when REDIS_URL is absent ─────────────────────────

class TestInMemoryFallback(unittest.TestCase):

    def setUp(self):
        env = {"OMNIX_ANTI_REPLAY_MODE": "best_effort"}
        env.pop("REDIS_URL", None)
        with patch.dict(os.environ, env, clear=False):
            if "REDIS_URL" in os.environ:
                del os.environ["REDIS_URL"]
            import importlib
            import omnix_core.evidence.anti_replay as ar_mod
            importlib.reload(ar_mod)
            self.ar = ar_mod
            self.store = ar_mod.AntiReplayStore()

    def test_R1_backend_is_in_memory_without_redis_url(self):
        self.assertEqual(self.store.backend, "in_memory")

    def test_R2_check_and_register_accepts_new_id(self):
        self.store.check_and_register("OMNIX-TRD-AA0011223344", ttl_ms=30_000)

    def test_R3_replay_detected_on_duplicate(self):
        rid = "OMNIX-TRD-BB1122334455"
        self.store.check_and_register(rid, ttl_ms=30_000)
        with self.assertRaises(self.ar.ReplayDetected):
            self.store.check_and_register(rid, ttl_ms=30_000)

    def test_R4_is_replay_true_after_registration(self):
        rid = "OMNIX-TRD-CC2233445566"
        self.store.check_and_register(rid, ttl_ms=30_000)
        self.assertTrue(self.store.is_replay(rid))

    def test_R5_is_replay_false_before_registration(self):
        self.assertFalse(self.store.is_replay("OMNIX-TRD-NEVER000000"))

    def test_R6_revoke_removes_id(self):
        rid = "OMNIX-TRD-DD3344556677"
        self.store.check_and_register(rid, ttl_ms=30_000)
        self.assertTrue(self.store.revoke(rid))
        # Now should be registrable again
        self.store.check_and_register(rid, ttl_ms=30_000)

    def test_R7_stats_returns_dict_with_backend(self):
        s = self.store.stats()
        self.assertIn("backend", s)
        self.assertEqual(s["backend"], "in_memory")

    def test_R8_empty_receipt_id_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.store.check_and_register("", ttl_ms=30_000)

    def test_R9_negative_ttl_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.store.check_and_register("OMNIX-TRD-EE4455667788", ttl_ms=-1)

    def test_R10_module_functions_match_store_behaviour(self):
        """Module-level check_and_register / is_replay work identically."""
        with patch.dict(os.environ, {"OMNIX_ANTI_REPLAY_MODE": "best_effort"}, clear=False):
            import importlib
            import omnix_core.evidence.anti_replay as mod
            importlib.reload(mod)
            rid = "OMNIX-TRD-FF5566778899"
            mod.check_and_register(rid, ttl_ms=30_000)
            self.assertTrue(mod.is_replay(rid))


# ── T001-R2: Redis backend (mocked) ───────────────────────────────────────────

class TestRedisBackend(unittest.TestCase):

    def _make_store_with_redis(self, mock_redis):
        """Build store with a mocked Redis client."""
        import omnix_core.evidence.anti_replay as ar_mod
        store = ar_mod.AntiReplayStore.__new__(ar_mod.AntiReplayStore)
        store._mem = ar_mod._InMemoryStore()
        store._redis = ar_mod._RedisStore(mock_redis)
        return store, ar_mod

    def _mock_redis_client(self, set_return=True):
        client = MagicMock()
        client.set.return_value = set_return    # True → key registered; None → key existed
        client.pttl.return_value = 15_000
        client.exists.return_value = 1 if not set_return else 0
        client.delete.return_value = 1
        client.keys.return_value = []
        return client

    def test_R11_backend_is_redis_when_client_set(self):
        import omnix_core.evidence.anti_replay as ar_mod
        mock_client = self._mock_redis_client()
        store, _ = self._make_store_with_redis(mock_client)
        self.assertEqual(store.backend, "redis")

    def test_R12_redis_set_nx_px_called_on_register(self):
        import omnix_core.evidence.anti_replay as ar_mod
        mock_client = self._mock_redis_client(set_return=True)
        store, _ = self._make_store_with_redis(mock_client)
        store.check_and_register("OMNIX-TRD-A0A0A0A0A0A0", ttl_ms=30_000)
        mock_client.set.assert_called_once()
        call_kwargs = mock_client.set.call_args
        self.assertIn("nx", call_kwargs.kwargs)
        self.assertIn("px", call_kwargs.kwargs)
        self.assertTrue(call_kwargs.kwargs["nx"])

    def test_R13_replay_detected_when_redis_returns_none(self):
        import omnix_core.evidence.anti_replay as ar_mod
        mock_client = self._mock_redis_client(set_return=None)  # key exists
        store, _ = self._make_store_with_redis(mock_client)
        with self.assertRaises(ar_mod.ReplayDetected):
            store.check_and_register("OMNIX-TRD-B1B1B1B1B1B1", ttl_ms=30_000)

    def test_R14_is_replay_uses_redis_exists(self):
        import omnix_core.evidence.anti_replay as ar_mod
        mock_client = self._mock_redis_client()
        mock_client.exists.return_value = 1
        store, _ = self._make_store_with_redis(mock_client)
        self.assertTrue(store.is_replay("OMNIX-TRD-C2C2C2C2C2C2"))

    def test_R15_revoke_calls_redis_delete(self):
        import omnix_core.evidence.anti_replay as ar_mod
        mock_client = self._mock_redis_client()
        store, _ = self._make_store_with_redis(mock_client)
        result = store.revoke("OMNIX-TRD-D3D3D3D3D3D3")
        mock_client.delete.assert_called_once()
        self.assertTrue(result)

    def test_R16_stats_includes_redis_backend(self):
        import omnix_core.evidence.anti_replay as ar_mod
        mock_client = self._mock_redis_client()
        store, _ = self._make_store_with_redis(mock_client)
        s = store.stats()
        self.assertEqual(s["backend"], "redis")

    def test_R17_redis_key_uses_omnix_ar_prefix(self):
        import omnix_core.evidence.anti_replay as ar_mod
        mock_client = self._mock_redis_client()
        store, _ = self._make_store_with_redis(mock_client)
        rid = "OMNIX-TRD-E4E4E4E4E4E4"
        store.check_and_register(rid, ttl_ms=30_000)
        call_args = mock_client.set.call_args
        key_used = call_args.args[0] if call_args.args else call_args.kwargs.get("name", "")
        self.assertTrue(key_used.startswith("omnix:ar:"), f"Key should start with omnix:ar:, got: {key_used}")

    def test_R18_best_effort_falls_back_to_memory_on_redis_error(self):
        import omnix_core.evidence.anti_replay as ar_mod

        broken_client = MagicMock()
        broken_client.set.side_effect = ConnectionError("Redis down")

        store = ar_mod.AntiReplayStore.__new__(ar_mod.AntiReplayStore)
        store._mem = ar_mod._InMemoryStore()
        store._redis = ar_mod._RedisStore(broken_client)

        with patch.object(ar_mod, "_STRICT_MODE", False):
            rid = "OMNIX-TRD-F5F5F5F5F5F5"
            store.check_and_register(rid, ttl_ms=30_000)
            self.assertTrue(store._mem.is_replay(rid))

    def test_R19_strict_mode_raises_on_redis_error(self):
        import omnix_core.evidence.anti_replay as ar_mod

        broken_client = MagicMock()
        broken_client.set.side_effect = ConnectionError("Redis down")

        store = ar_mod.AntiReplayStore.__new__(ar_mod.AntiReplayStore)
        store._mem = ar_mod._InMemoryStore()
        store._redis = ar_mod._RedisStore(broken_client)

        with patch.object(ar_mod, "_STRICT_MODE", True):
            with self.assertRaises(ar_mod.ReplayDetected):
                store.check_and_register("OMNIX-TRD-G6G6G6G6G6G6", ttl_ms=30_000)

    def test_R20_ttl_floor_applied_on_redis_set(self):
        import omnix_core.evidence.anti_replay as ar_mod
        mock_client = self._mock_redis_client()
        store, _ = self._make_store_with_redis(mock_client)
        store.check_and_register("OMNIX-TRD-H7H7H7H7H7H7", ttl_ms=100)  # below MIN_WINDOW_MS
        call_kwargs = mock_client.set.call_args.kwargs
        self.assertGreaterEqual(call_kwargs["px"], ar_mod.MIN_WINDOW_MS)


# ── T001-R3: Thread safety (in-memory) ────────────────────────────────────────

class TestThreadSafety(unittest.TestCase):

    def test_R21_concurrent_registrations_exactly_one_winner(self):
        import omnix_core.evidence.anti_replay as ar_mod
        store = ar_mod._InMemoryStore()
        rid = "OMNIX-TRD-CONCURRENT0000"
        errors = []
        replay_count = []

        def attempt():
            try:
                store.check_and_register(rid, ttl_ms=30_000)
            except ar_mod.ReplayDetected:
                replay_count.append(1)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=attempt) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")
        # Exactly 1 winner, 19 replay detections
        self.assertEqual(len(replay_count), 19)


if __name__ == "__main__":
    unittest.main(verbosity=2)
