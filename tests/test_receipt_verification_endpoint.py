"""
Tests for ADR-079: PKI Verification Endpoints

Tests the Flask blueprint:
    GET  /api/receipts/public-key
    POST /api/receipts/verify

Harold Nunes — OMNIX QUANTUM LTD
"""
import base64
import hashlib
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch


# ── Skip guard ────────────────────────────────────────────────────────────────

try:
    from pqc.sign import dilithium3 as _d3
    PQC_AVAILABLE = True
except ImportError:
    PQC_AVAILABLE = False


def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode()


# ── Fixture: Flask test client ────────────────────────────────────────────────

def _make_test_app(engine_mock=None):
    """Create a minimal Flask app with the receipt_pki blueprint."""
    from flask import Flask
    import importlib

    import omnix_dashboard.blueprints.receipt_verification as bp_mod
    importlib.reload(bp_mod)

    if engine_mock is not None:
        bp_mod._get_engine._instance = engine_mock
    elif hasattr(bp_mod._get_engine, "_instance"):
        del bp_mod._get_engine._instance

    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(bp_mod.receipt_pki_bp)
    return app.test_client()


def _make_engine_mock(pk_b64="pk_b64_placeholder", key_id="deadbeef12345678",
                       key_mode="ephemeral_dev", active_since="2026-04-09T00:00:00+00:00",
                       provider=None, signing_keys=None):
    eng = MagicMock()
    eng.public_key_b64 = pk_b64
    eng.key_id = key_id
    eng.key_mode = key_mode
    eng.active_since = active_since
    eng._provider = provider
    eng._signing_keys = signing_keys
    return eng


# ── T003-E1: GET /api/receipts/public-key ─────────────────────────────────────

class TestGetPublicKey(unittest.TestCase):

    def setUp(self):
        prov = MagicMock()
        prov.algorithm_name.return_value = "Dilithium-3 (ML-DSA-65)"
        prov.provider_id.return_value = "dilithium3"
        self.engine = _make_engine_mock(
            pk_b64="dGVzdHB1YmxpY2tleQ==",
            provider=prov,
            signing_keys=(b"\x00" * 1952, b"\x00" * 4000),
        )
        self.client = _make_test_app(engine_mock=self.engine)

    def test_E1_returns_200(self):
        r = self.client.get("/api/receipts/public-key")
        self.assertEqual(r.status_code, 200)

    def test_E2_response_contains_public_key_b64(self):
        r = self.client.get("/api/receipts/public-key")
        data = json.loads(r.data)
        self.assertIn("public_key_b64", data)
        self.assertEqual(data["public_key_b64"], "dGVzdHB1YmxpY2tleQ==")

    def test_E3_response_contains_algorithm(self):
        r = self.client.get("/api/receipts/public-key")
        data = json.loads(r.data)
        self.assertIn("algorithm", data)
        self.assertIn("Dilithium", data["algorithm"])

    def test_E4_response_contains_key_id(self):
        r = self.client.get("/api/receipts/public-key")
        data = json.loads(r.data)
        self.assertIn("key_id", data)
        self.assertEqual(data["key_id"], "deadbeef12345678")

    def test_E5_response_contains_active_since(self):
        r = self.client.get("/api/receipts/public-key")
        data = json.loads(r.data)
        self.assertIn("active_since", data)

    def test_E6_ephemeral_mode_includes_warning(self):
        r = self.client.get("/api/receipts/public-key")
        data = json.loads(r.data)
        self.assertIsNotNone(data.get("warning"))

    def test_E7_persisted_mode_warning_is_null(self):
        self.engine.key_mode = "persisted"
        r = self.client.get("/api/receipts/public-key")
        data = json.loads(r.data)
        self.assertIsNone(data.get("warning"))

    def test_E8_no_engine_returns_503(self):
        client = _make_test_app(engine_mock=None)
        import omnix_dashboard.blueprints.receipt_verification as bp_mod
        if hasattr(bp_mod._get_engine, "_instance"):
            del bp_mod._get_engine._instance
        with patch.object(bp_mod, "_get_engine", return_value=None):
            r = client.get("/api/receipts/public-key")
        self.assertEqual(r.status_code, 503)


# ── T003-E2: POST /api/receipts/verify — input validation ─────────────────────

class TestVerifyInputValidation(unittest.TestCase):

    def _make_client_with_noop_engine(self):
        """Engine that always says 'not ready' — for input validation tests only."""
        prov = MagicMock()
        prov.verify.return_value = True
        prov.algorithm_name.return_value = "Dilithium-3 (ML-DSA-65)"
        pk = b"\x01" * 1952
        sk = b"\x02" * 4000
        engine = _make_engine_mock(
            pk_b64=_b64(pk), provider=prov, signing_keys=(pk, sk),
        )
        return _make_test_app(engine_mock=engine)

    def _valid_body(self):
        return {
            "receipt_id":   "OMNIX-TRD-A0B1C2D3E4F5",
            "content_hash": "a" * 64,
            "signature_b64": _b64(b"\x01" * 100),
        }

    def test_E9_missing_receipt_id_returns_400(self):
        client = self._make_client_with_noop_engine()
        body = self._valid_body()
        del body["receipt_id"]
        r = client.post("/api/receipts/verify", json=body)
        self.assertEqual(r.status_code, 400)
        self.assertIn("MALFORMED_INPUT", r.data.decode())

    def test_E10_invalid_receipt_id_format_returns_400(self):
        client = self._make_client_with_noop_engine()
        body = self._valid_body()
        body["receipt_id"] = "INVALID-FORMAT"
        r = client.post("/api/receipts/verify", json=body)
        self.assertEqual(r.status_code, 400)

    def test_E11_receipt_id_with_domain_code_accepted(self):
        client = self._make_client_with_noop_engine()
        body = self._valid_body()
        body["receipt_id"] = "OMNIX-TRD-A0B1C2D3E4F5"
        with patch("omnix_dashboard.blueprints.receipt_verification._db_lookup", return_value=None):
            r = client.post("/api/receipts/verify", json=body)
        self.assertNotEqual(r.status_code, 400)

    def test_E12_short_content_hash_returns_400(self):
        client = self._make_client_with_noop_engine()
        body = self._valid_body()
        body["content_hash"] = "abc123"
        r = client.post("/api/receipts/verify", json=body)
        self.assertEqual(r.status_code, 400)

    def test_E13_non_hex_content_hash_returns_400(self):
        client = self._make_client_with_noop_engine()
        body = self._valid_body()
        body["content_hash"] = "g" * 64  # 'g' is not hex
        r = client.post("/api/receipts/verify", json=body)
        self.assertEqual(r.status_code, 400)

    def test_E14_oversized_signature_returns_400(self):
        client = self._make_client_with_noop_engine()
        body = self._valid_body()
        body["signature_b64"] = _b64(b"\xff" * 9000)  # > 8192 bytes decoded
        r = client.post("/api/receipts/verify", json=body)
        self.assertEqual(r.status_code, 400)

    def test_E15_invalid_base64_signature_returns_400(self):
        client = self._make_client_with_noop_engine()
        body = self._valid_body()
        body["signature_b64"] = "!!!not-base64!!!"
        r = client.post("/api/receipts/verify", json=body)
        self.assertEqual(r.status_code, 400)


# ── T003-E3: POST /api/receipts/verify — crypto verification ─────────────────

@unittest.skipUnless(PQC_AVAILABLE, "pqc library not installed")
class TestCryptoVerification(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from omnix_core.security.crypto_providers import get_active_provider
        cls._provider = get_active_provider()
        kp = cls._provider.generate_keypair()
        cls.pk, cls.sk = kp[0], kp[1]
        cls.content_hash = "b" * 64
        cls.message = cls.content_hash.encode("utf-8")
        cls.signature = cls._provider.sign(cls.message, cls.sk)
        cls.sig_b64 = _b64(cls.signature)

    def _make_engine(self):
        from omnix_core.security.crypto_providers import get_active_provider
        provider = get_active_provider()
        engine = _make_engine_mock(
            pk_b64=_b64(self.pk),
            key_id=hashlib.sha256(self.pk).hexdigest()[:16],
            provider=provider,
            signing_keys=(self.pk, self.sk),
        )
        return engine

    def _make_client(self):
        return _make_test_app(engine_mock=self._make_engine())

    def test_E16_valid_signature_returns_valid_true(self):
        client = self._make_client()
        body = {
            "receipt_id":   "OMNIX-TRD-A0B1C2D3E4F5",
            "content_hash": self.content_hash,
            "signature_b64": self.sig_b64,
        }
        with patch("omnix_dashboard.blueprints.receipt_verification._db_lookup", return_value=None):
            r = client.post("/api/receipts/verify", json=body)
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertTrue(data["valid"])

    def test_E17_tampered_hash_returns_valid_false(self):
        client = self._make_client()
        body = {
            "receipt_id":    "OMNIX-TRD-A0B1C2D3E4F5",
            "content_hash":  "c" * 64,  # different hash — signature will not verify
            "signature_b64": self.sig_b64,
        }
        with patch("omnix_dashboard.blueprints.receipt_verification._db_lookup", return_value=None):
            r = client.post("/api/receipts/verify", json=body)
        data = json.loads(r.data)
        self.assertFalse(data["valid"])
        self.assertEqual(data.get("reason"), "SIGNATURE_INVALID")

    def test_E18_valid_sig_returns_algorithm_and_key_id(self):
        client = self._make_client()
        body = {
            "receipt_id":    "OMNIX-TRD-A0B1C2D3E4F5",
            "content_hash":  self.content_hash,
            "signature_b64": self.sig_b64,
        }
        with patch("omnix_dashboard.blueprints.receipt_verification._db_lookup", return_value=None):
            r = client.post("/api/receipts/verify", json=body)
        data = json.loads(r.data)
        self.assertIn("algorithm", data)
        self.assertIn("key_id", data)
        self.assertIn("verified_at", data)


# ── T003-E4: DB cross-reference ────────────────────────────────────────────────

@unittest.skipUnless(PQC_AVAILABLE, "pqc library not installed")
class TestDbCrossReference(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from omnix_core.security.crypto_providers import get_active_provider
        cls._provider = get_active_provider()
        kp = cls._provider.generate_keypair()
        cls.pk, cls.sk = kp[0], kp[1]
        cls.content_hash = "d" * 64
        cls.message = cls.content_hash.encode("utf-8")
        cls.signature = cls._provider.sign(cls.message, cls.sk)
        cls.sig_b64 = _b64(cls.signature)

    def _make_client(self):
        from omnix_core.security.crypto_providers import get_active_provider
        provider = get_active_provider()
        engine = _make_engine_mock(
            pk_b64=_b64(self.pk),
            key_id=hashlib.sha256(self.pk).hexdigest()[:16],
            provider=provider,
            signing_keys=(self.pk, self.sk),
        )
        return _make_test_app(engine_mock=engine)

    def test_E19_db_hash_mismatch_returns_valid_false(self):
        client = self._make_client()
        db_result = {
            "found": True,
            "content_hash": "e" * 64,  # different from submitted
            "signature": None,
            "decision": "APPROVED",
            "timestamp": "2026-04-09T00:00:00+00:00",
        }
        body = {
            "receipt_id":    "OMNIX-TRD-A0B1C2D3E4F5",
            "content_hash":  self.content_hash,
            "signature_b64": self.sig_b64,
        }
        with patch("omnix_dashboard.blueprints.receipt_verification._db_lookup", return_value=db_result):
            r = client.post("/api/receipts/verify", json=body)
        data = json.loads(r.data)
        self.assertFalse(data["valid"])
        self.assertEqual(data.get("reason"), "HASH_MISMATCH")

    def test_E20_db_match_proceeds_to_crypto_verify(self):
        client = self._make_client()
        db_result = {
            "found": True,
            "content_hash": self.content_hash,  # matches submitted
            "signature": None,
            "decision": "APPROVED",
            "timestamp": "2026-04-09T00:00:00+00:00",
        }
        body = {
            "receipt_id":    "OMNIX-TRD-A0B1C2D3E4F5",
            "content_hash":  self.content_hash,
            "signature_b64": self.sig_b64,
        }
        with patch("omnix_dashboard.blueprints.receipt_verification._db_lookup", return_value=db_result):
            r = client.post("/api/receipts/verify", json=body)
        data = json.loads(r.data)
        self.assertTrue(data["valid"])
        self.assertTrue(data["db_cross_reference"]["content_hash_match"])

    def test_E21_db_not_found_still_verifies_cryptographically(self):
        client = self._make_client()
        db_result = {"found": False}
        body = {
            "receipt_id":    "OMNIX-TRD-A0B1C2D3E4F5",
            "content_hash":  self.content_hash,
            "signature_b64": self.sig_b64,
        }
        with patch("omnix_dashboard.blueprints.receipt_verification._db_lookup", return_value=db_result):
            r = client.post("/api/receipts/verify", json=body)
        data = json.loads(r.data)
        self.assertTrue(data["valid"])
        self.assertFalse(data["db_cross_reference"]["found"])

    def test_E22_db_unavailable_still_verifies_cryptographically(self):
        client = self._make_client()
        body = {
            "receipt_id":    "OMNIX-TRD-A0B1C2D3E4F5",
            "content_hash":  self.content_hash,
            "signature_b64": self.sig_b64,
        }
        with patch("omnix_dashboard.blueprints.receipt_verification._db_lookup", return_value=None):
            r = client.post("/api/receipts/verify", json=body)
        data = json.loads(r.data)
        self.assertTrue(data["valid"])


# ── T003-E5: Rate limiting ────────────────────────────────────────────────────

class TestRateLimiting(unittest.TestCase):

    def test_E23_exceeding_rate_limit_returns_429(self):
        import omnix_dashboard.blueprints.receipt_verification as bp_mod
        import importlib
        importlib.reload(bp_mod)

        # Set rate limit to 1 for testing
        with patch.object(bp_mod, "_RL_MAX", 1):
            app = __import__("flask").Flask(__name__)
            app.config["TESTING"] = True
            app.register_blueprint(bp_mod.receipt_pki_bp)
            client = app.test_client()

            prov = MagicMock()
            prov.verify.return_value = True
            prov.algorithm_name.return_value = "Dilithium-3"
            pk = b"\x01" * 1952
            sk = b"\x02" * 4000
            bp_mod._get_engine._instance = _make_engine_mock(
                provider=prov, signing_keys=(pk, sk)
            )
            bp_mod._rl_store.clear()

            body = {
                "receipt_id":    "OMNIX-TRD-A0B1C2D3E4F5",
                "content_hash":  "a" * 64,
                "signature_b64": _b64(b"\x01" * 100),
            }

            with patch.object(bp_mod, "_db_lookup", return_value=None):
                r1 = client.post("/api/receipts/verify", json=body)
                r2 = client.post("/api/receipts/verify", json=body)

            self.assertNotEqual(r1.status_code, 429)
            self.assertEqual(r2.status_code, 429)


if __name__ == "__main__":
    unittest.main(verbosity=2)
