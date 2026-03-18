"""
Test: SHA-256 fallback when PQC provider is unavailable.
Ensures Signature NONE regression never occurs.
"""
import hashlib
import sys
import os
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestReceiptSHA256Fallback(unittest.TestCase):
    """Verify that receipts use SHA-256 when pypqc/PQC provider is absent."""

    def _make_engine_no_pqc(self):
        """Instantiate DecisionReceiptEngine with PQC forcibly disabled."""
        with patch.dict('sys.modules', {'omnix_core.security.crypto_providers': None}):
            import importlib
            import omnix_core.evidence.decision_receipt as mod
            importlib.reload(mod)
            engine = mod.DecisionReceiptEngine.__new__(mod.DecisionReceiptEngine)
            engine._provider = None
            engine._signing_keys = None
            engine.db_url = None
            return engine, mod

    def test_signature_algorithm_is_sha256_when_no_pqc(self):
        """signature_algorithm must be 'SHA-256', never 'NONE', when PQC unavailable."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        engine = DecisionReceiptEngine.__new__(DecisionReceiptEngine)
        engine._provider = None
        engine._signing_keys = None
        engine.db_url = None

        with patch.object(engine, '_append_to_transparency_chain', return_value=None), \
             patch.object(engine, '_extract_veto_chain', return_value=[]):
            receipt = engine.generate_receipt({'decision': 'BLOCKED', 'asset': 'BTC/USD'})

        self.assertEqual(
            receipt['signature_algorithm'], 'SHA-256',
            f"Expected 'SHA-256', got '{receipt['signature_algorithm']}'"
        )
        self.assertNotEqual(receipt['signature_algorithm'], 'NONE')

    def test_signature_is_not_none_when_no_pqc(self):
        """signature field must be a non-empty string, not None, when PQC unavailable."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        engine = DecisionReceiptEngine.__new__(DecisionReceiptEngine)
        engine._provider = None
        engine._signing_keys = None
        engine.db_url = None

        with patch.object(engine, '_append_to_transparency_chain', return_value=None), \
             patch.object(engine, '_extract_veto_chain', return_value=[]):
            receipt = engine.generate_receipt({'decision': 'APPROVED', 'asset': 'ETH/USD'})

        self.assertIsNotNone(receipt['signature'], "Signature must not be None")
        self.assertIsInstance(receipt['signature'], str)
        self.assertGreater(len(receipt['signature']), 0)

    def test_signature_matches_sha256_of_content_hash(self):
        """Fallback signature must be SHA-256 hexdigest of content_hash."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        engine = DecisionReceiptEngine.__new__(DecisionReceiptEngine)
        engine._provider = None
        engine._signing_keys = None
        engine.db_url = None

        with patch.object(engine, '_append_to_transparency_chain', return_value=None), \
             patch.object(engine, '_extract_veto_chain', return_value=[]):
            receipt = engine.generate_receipt({'decision': 'HOLD', 'asset': 'BTC/USD'})

        expected_sig = hashlib.sha256(receipt['content_hash'].encode('utf-8')).hexdigest()
        self.assertEqual(receipt['signature'], expected_sig)

    def test_signing_provider_is_sha256_when_no_pqc(self):
        """signing_provider must be 'sha256' (not 'none') when PQC unavailable."""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        engine = DecisionReceiptEngine.__new__(DecisionReceiptEngine)
        engine._provider = None
        engine._signing_keys = None
        engine.db_url = None

        with patch.object(engine, '_append_to_transparency_chain', return_value=None), \
             patch.object(engine, '_extract_veto_chain', return_value=[]):
            receipt = engine.generate_receipt({'decision': 'BLOCKED', 'asset': 'SOL/USD'})

        self.assertEqual(receipt['signing_provider'], 'sha256')
        self.assertNotEqual(receipt['signing_provider'], 'none')

    def test_pqc_path_unchanged(self):
        """When PQC provider IS available, it must still be used (no regression)."""
        import base64
        from unittest.mock import MagicMock
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine

        mock_provider = MagicMock()
        mock_provider.provider_id.return_value = 'dilithium3'
        mock_provider.algorithm_name.return_value = 'Dilithium-3'
        mock_provider.sign.return_value = b'fakesignature'
        mock_provider.serialize_public_key.return_value = 'pubkeyb64'

        engine = DecisionReceiptEngine.__new__(DecisionReceiptEngine)
        engine._provider = mock_provider
        engine._signing_keys = (b'pubkey', b'privkey')
        engine.db_url = None

        with patch.object(engine, '_append_to_transparency_chain', return_value=None), \
             patch.object(engine, '_extract_veto_chain', return_value=[]):
            receipt = engine.generate_receipt({'decision': 'APPROVED', 'asset': 'BTC/USD'})

        expected_sig_b64 = base64.b64encode(b'fakesignature').decode()
        self.assertEqual(receipt['signature_algorithm'], 'Dilithium-3')
        self.assertEqual(receipt['signing_provider'], 'dilithium3')
        self.assertEqual(receipt['signature'], expected_sig_b64)


if __name__ == '__main__':
    unittest.main()
