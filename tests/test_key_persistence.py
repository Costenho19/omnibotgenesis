"""
Tests for ADR-078: Signing Key Persistence

Tests that DecisionReceiptEngine correctly loads keys from environment variables,
runs self-tests, generates ephemeral keys, and respects OMNIX_KEY_MODE.

Harold Nunes — OMNIX QUANTUM LTD
"""
import base64
import hashlib
import os
import sys
import unittest
from unittest.mock import patch, MagicMock


# ── Skip if PQC library unavailable ───────────────────────────────────────────

try:
    from pqc.sign import dilithium3 as _d3
    PQC_AVAILABLE = True
except ImportError:
    PQC_AVAILABLE = False


def _generate_test_keypair():
    """Generate a real Dilithium-3 keypair for test fixtures via the active provider."""
    from omnix_core.security.crypto_providers import get_active_provider
    provider = get_active_provider()
    kp = provider.generate_keypair()
    if kp is None:
        raise RuntimeError("Provider.generate_keypair() returned None")
    return kp[0], kp[1]  # (public_key, secret_key)


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


def _fresh_engine(env_overrides: dict):
    """Instantiate a DecisionReceiptEngine with clean env overrides."""
    import importlib
    import omnix_core.evidence.decision_receipt as dr_mod
    importlib.reload(dr_mod)
    from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
    with patch.dict(os.environ, env_overrides, clear=False):
        engine = DecisionReceiptEngine()
    return engine


# ── T002-K1: Ephemeral mode (default) ─────────────────────────────────────────

@unittest.skipUnless(PQC_AVAILABLE, "pqc library not installed")
class TestEphemeralMode(unittest.TestCase):

    def _make_engine_ephemeral(self):
        env = {
            "OMNIX_KEY_MODE": "ephemeral_dev",
        }
        # Remove persisted key env vars if present
        env["OMNIX_SIGNING_SECRET_KEY_B64"] = ""
        env["OMNIX_SIGNING_PUBLIC_KEY_B64"] = ""
        return _fresh_engine(env)

    def test_K1_ephemeral_mode_generates_keys(self):
        engine = self._make_engine_ephemeral()
        self.assertIsNotNone(engine._signing_keys)

    def test_K2_key_mode_is_ephemeral_dev(self):
        engine = self._make_engine_ephemeral()
        # ADR-085: process-scoped stable key may exist when module already loaded;
        # both "ephemeral_dev" (first init) and "stable_process" (reuse) are valid
        # ephemeral (non-persisted) modes.
        self.assertIn(engine.key_mode, ("ephemeral_dev", "stable_process"))

    def test_K3_active_since_is_set(self):
        engine = self._make_engine_ephemeral()
        self.assertIsNotNone(engine.active_since)

    def test_K4_key_id_is_16_hex_chars(self):
        engine = self._make_engine_ephemeral()
        kid = engine.key_id
        self.assertIsNotNone(kid)
        self.assertEqual(len(kid), 16)
        int(kid, 16)  # must be valid hex

    def test_K5_public_key_b64_is_non_empty(self):
        engine = self._make_engine_ephemeral()
        pk = engine.public_key_b64
        self.assertIsNotNone(pk)
        self.assertGreater(len(pk), 100)

    def test_K6_key_id_is_sha256_of_public_key(self):
        engine = self._make_engine_ephemeral()
        pk_bytes = engine._signing_keys[0]
        expected = hashlib.sha256(pk_bytes).hexdigest()[:16]
        self.assertEqual(engine.key_id, expected)

    def test_K7_can_sign_and_verify_with_ephemeral_keys(self):
        engine = self._make_engine_ephemeral()
        msg = b"test-governance-payload"
        pk, sk = engine._signing_keys
        provider = engine._provider
        sig = provider.sign(msg, sk)
        self.assertIsNotNone(sig)
        self.assertTrue(provider.verify(sig, msg, pk))


# ── T002-K2: Persisted mode (from env vars) ───────────────────────────────────

@unittest.skipUnless(PQC_AVAILABLE, "pqc library not installed")
class TestPersistedMode(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pk, sk = _generate_test_keypair()
        cls.pk_bytes = pk
        cls.sk_bytes = sk
        cls.pk_b64 = _b64(pk)
        cls.sk_b64 = _b64(sk)

    def _make_engine_persisted(self):
        env = {
            "OMNIX_KEY_MODE":                 "ephemeral_dev",
            "OMNIX_SIGNING_SECRET_KEY_B64":   self.sk_b64,
            "OMNIX_SIGNING_PUBLIC_KEY_B64":   self.pk_b64,
        }
        return _fresh_engine(env)

    def test_K8_persisted_mode_loads_correct_keys(self):
        engine = self._make_engine_persisted()
        self.assertEqual(engine.key_mode, "persisted")
        self.assertIsNotNone(engine._signing_keys)

    def test_K9_loaded_public_key_matches_env_var(self):
        engine = self._make_engine_persisted()
        loaded_pk = engine._signing_keys[0]
        self.assertEqual(loaded_pk, self.pk_bytes)

    def test_K10_loaded_secret_key_matches_env_var(self):
        engine = self._make_engine_persisted()
        loaded_sk = engine._signing_keys[1]
        self.assertEqual(loaded_sk, self.sk_bytes)

    def test_K11_key_id_matches_expected_fingerprint(self):
        engine = self._make_engine_persisted()
        expected = hashlib.sha256(self.pk_bytes).hexdigest()[:16]
        self.assertEqual(engine.key_id, expected)

    def test_K12_active_since_is_set_on_persisted_load(self):
        engine = self._make_engine_persisted()
        self.assertIsNotNone(engine.active_since)

    def test_K13_persisted_keys_can_sign_and_verify(self):
        engine = self._make_engine_persisted()
        msg = b"test-governance-payload-persisted"
        pk, sk = engine._signing_keys
        provider = engine._provider
        sig = provider.sign(msg, sk)
        self.assertIsNotNone(sig)
        self.assertTrue(provider.verify(sig, msg, pk))


# ── T002-K3: Required mode ─────────────────────────────────────────────────────

@unittest.skipUnless(PQC_AVAILABLE, "pqc library not installed")
class TestRequiredMode(unittest.TestCase):

    def test_K14_required_mode_without_keys_leaves_signing_keys_none(self):
        env = {
            "OMNIX_KEY_MODE":               "required",
            "OMNIX_SIGNING_SECRET_KEY_B64": "",
            "OMNIX_SIGNING_PUBLIC_KEY_B64": "",
        }
        engine = _fresh_engine(env)
        # required mode without env vars → no signing keys
        self.assertIsNone(engine._signing_keys)
        self.assertEqual(engine.key_mode, "required_missing")

    def test_K15_required_mode_with_valid_keys_loads_them(self):
        pk, sk = _generate_test_keypair()
        env = {
            "OMNIX_KEY_MODE":               "required",
            "OMNIX_SIGNING_SECRET_KEY_B64": _b64(sk),
            "OMNIX_SIGNING_PUBLIC_KEY_B64": _b64(pk),
        }
        engine = _fresh_engine(env)
        self.assertEqual(engine.key_mode, "persisted")
        self.assertIsNotNone(engine._signing_keys)


# ── T002-K4: Self-test validation ─────────────────────────────────────────────

@unittest.skipUnless(PQC_AVAILABLE, "pqc library not installed")
class TestSelfTest(unittest.TestCase):

    def test_K16_mismatched_keypair_falls_through_to_ephemeral(self):
        """If env keypair fails self-test, engine falls back to ephemeral generation."""
        pk1, sk1 = _generate_test_keypair()
        pk2, sk2 = _generate_test_keypair()
        # Cross the keys: public from pair 1, secret from pair 2 — self-test will fail
        env = {
            "OMNIX_KEY_MODE":               "ephemeral_dev",
            "OMNIX_SIGNING_SECRET_KEY_B64": _b64(sk2),
            "OMNIX_SIGNING_PUBLIC_KEY_B64": _b64(pk1),
        }
        engine = _fresh_engine(env)
        # Should have fallen back to ephemeral generation.
        # ADR-085: process-scoped stable key may exist when module already loaded;
        # "stable_process" is also a valid non-persisted fallback mode.
        self.assertIsNotNone(engine._signing_keys)
        self.assertIn(engine.key_mode, ("ephemeral_dev", "stable_process"))


# ── T002-K5: Receipt includes signing_key_id ──────────────────────────────────

@unittest.skipUnless(PQC_AVAILABLE, "pqc library not installed")
class TestReceiptKeyId(unittest.TestCase):

    def test_K17_generate_receipt_includes_signing_key_id(self):
        env = {
            "OMNIX_KEY_MODE":               "ephemeral_dev",
            "OMNIX_SIGNING_SECRET_KEY_B64": "",
            "OMNIX_SIGNING_PUBLIC_KEY_B64": "",
        }
        engine = _fresh_engine(env)
        if engine._signing_keys is None:
            self.skipTest("Signing keys unavailable")

        decision = {"decision": "APPROVED", "domain": "trading", "symbol": "BTC/USDT"}
        receipt = engine.generate_receipt(decision)

        self.assertIn("signing_key_id", receipt)
        self.assertEqual(receipt["signing_key_id"], engine.key_id)

    def test_K18_key_id_compute_is_deterministic(self):
        pk = b"\x01\x02\x03" * 100
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        kid1 = DecisionReceiptEngine._compute_key_id(pk)
        kid2 = DecisionReceiptEngine._compute_key_id(pk)
        self.assertEqual(kid1, kid2)
        self.assertEqual(len(kid1), 16)


if __name__ == "__main__":
    unittest.main(verbosity=2)
