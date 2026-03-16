"""
Tests for ADR-042/043/044 PQC Enhancements:
  ADR-042: Hybrid Cryptography (HybridKEM)
  ADR-043: Crypto-Agility Layer (CryptoProvider registry)
  ADR-044: Quantum-Secure Decision Receipts (TransparencyChain, InternalTimestamp)
"""

import json
import hashlib
import os
import base64
import pytest

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("DATABASE_URL", "")


# ──────────────────────────────────────────────────────────────────────────────
# ADR-042: Hybrid Cryptography
# ──────────────────────────────────────────────────────────────────────────────

class TestHybridKEM:

    def test_get_capabilities_returns_dict(self):
        from omnix_core.security.hybrid_crypto import HybridKEM
        caps = HybridKEM.get_capabilities()
        assert isinstance(caps, dict)
        assert "kyber768_available" in caps
        assert "x25519_available" in caps
        assert "hybrid_available" in caps
        assert caps["adr"] == "ADR-042"

    def test_generate_keypair_returns_bundle(self):
        from omnix_core.security.hybrid_crypto import HybridKEM
        kp = HybridKEM.generate_keypair()
        assert kp is not None
        assert "private" in kp
        assert "public" in kp
        assert "mode" in kp
        assert kp["mode"] in ("hybrid", "kyber768_only", "x25519_only")

    def test_encapsulate_returns_bundle(self):
        from omnix_core.security.hybrid_crypto import HybridKEM
        kp = HybridKEM.generate_keypair()
        assert kp is not None
        enc = HybridKEM.encapsulate(kp["public"])
        assert enc is not None
        assert "combined_secret" in enc
        assert "ciphertext_bundle" in enc
        assert "mode" in enc
        assert len(enc["combined_secret"]) == 32

    def test_encapsulate_decapsulate_produces_same_secret(self):
        from omnix_core.security.hybrid_crypto import HybridKEM
        kp = HybridKEM.generate_keypair()
        assert kp is not None
        enc = HybridKEM.encapsulate(kp["public"])
        assert enc is not None
        dec = HybridKEM.decapsulate(enc["ciphertext_bundle"], kp["private"])
        assert dec is not None
        assert dec["combined_secret"] == enc["combined_secret"]
        assert len(dec["combined_secret"]) == 32

    def test_different_keypairs_produce_different_secrets(self):
        from omnix_core.security.hybrid_crypto import HybridKEM
        kp1 = HybridKEM.generate_keypair()
        kp2 = HybridKEM.generate_keypair()
        assert kp1 is not None and kp2 is not None
        enc1 = HybridKEM.encapsulate(kp1["public"])
        enc2 = HybridKEM.encapsulate(kp2["public"])
        assert enc1 is not None and enc2 is not None
        assert enc1["combined_secret"] != enc2["combined_secret"]

    def test_hkdf_label_correct(self):
        from omnix_core.security.hybrid_crypto import HKDF_INFO_LABEL
        assert HKDF_INFO_LABEL == b"OMNIX-ADR042-HybridKEM-v1"

    def test_algorithm_description(self):
        from omnix_core.security.hybrid_crypto import HybridKEM
        kp = HybridKEM.generate_keypair()
        enc = HybridKEM.encapsulate(kp["public"])
        assert "HKDF" in enc["algorithm"]

    def test_wrong_private_key_decapsulation_fails_or_differs(self):
        from omnix_core.security.hybrid_crypto import HybridKEM
        kp1 = HybridKEM.generate_keypair()
        kp2 = HybridKEM.generate_keypair()
        enc = HybridKEM.encapsulate(kp1["public"])
        dec_wrong = HybridKEM.decapsulate(enc["ciphertext_bundle"], kp2["private"])
        if dec_wrong is not None:
            assert dec_wrong["combined_secret"] != enc["combined_secret"]


# ──────────────────────────────────────────────────────────────────────────────
# ADR-043: Crypto-Agility Provider Layer
# ──────────────────────────────────────────────────────────────────────────────

class TestCryptoProviders:

    def test_list_providers_returns_all_three(self):
        from omnix_core.security.crypto_providers import list_providers
        providers = list_providers()
        assert "dilithium3" in providers
        assert "dilithium5" in providers
        assert "ed25519"    in providers

    def test_get_active_provider_returns_provider(self):
        from omnix_core.security.crypto_providers import get_active_provider
        p = get_active_provider()
        assert p is not None
        assert p.provider_id() in ("dilithium3", "dilithium5", "ed25519")
        assert isinstance(p.algorithm_name(), str)

    def test_provider_ids_are_stable(self):
        from omnix_core.security.crypto_providers import _REGISTRY
        assert _REGISTRY["dilithium3"].provider_id() == "dilithium3"
        assert _REGISTRY["dilithium5"].provider_id() == "dilithium5"
        assert _REGISTRY["ed25519"].provider_id()    == "ed25519"

    def test_dilithium3_sign_verify_roundtrip(self):
        from omnix_core.security.crypto_providers import _REGISTRY
        p = _REGISTRY["dilithium3"]
        kp = p.generate_keypair()
        assert kp is not None
        pub, sec = kp
        msg = b"OMNIX governance test message"
        sig = p.sign(msg, sec)
        assert sig is not None
        assert p.verify(sig, msg, pub)

    def test_dilithium3_verify_fails_wrong_message(self):
        from omnix_core.security.crypto_providers import _REGISTRY
        p = _REGISTRY["dilithium3"]
        kp = p.generate_keypair()
        assert kp is not None
        pub, sec = kp
        sig = p.sign(b"original message", sec)
        assert not p.verify(sig, b"tampered message", pub)

    def test_dilithium3_serialize_deserialize_public_key(self):
        from omnix_core.security.crypto_providers import _REGISTRY
        p = _REGISTRY["dilithium3"]
        kp = p.generate_keypair()
        assert kp is not None
        pub, _ = kp
        serialized   = p.serialize_public_key(pub)
        deserialized = p.deserialize_public_key(serialized)
        assert deserialized == pub

    def test_ed25519_sign_verify_roundtrip(self):
        from omnix_core.security.crypto_providers import _REGISTRY
        p = _REGISTRY["ed25519"]
        kp = p.generate_keypair()
        assert kp is not None
        pub, sec = kp
        msg = b"OMNIX ed25519 test"
        sig = p.sign(msg, sec)
        assert sig is not None
        assert p.verify(sig, msg, pub)

    def test_get_provider_by_id(self):
        from omnix_core.security.crypto_providers import get_provider
        p3 = get_provider("dilithium3")
        assert p3 is not None
        assert p3.provider_id() == "dilithium3"
        p_none = get_provider("nonexistent")
        assert p_none is None

    def test_active_provider_respects_env_var(self):
        import importlib
        original = os.environ.pop("ACTIVE_SIGNING_PROVIDER", None)
        try:
            os.environ["ACTIVE_SIGNING_PROVIDER"] = "ed25519"
            from omnix_core.security import crypto_providers
            importlib.reload(crypto_providers)
            p = crypto_providers.get_active_provider()
            assert p.provider_id() == "ed25519"
        finally:
            if original:
                os.environ["ACTIVE_SIGNING_PROVIDER"] = original
            else:
                os.environ.pop("ACTIVE_SIGNING_PROVIDER", None)

    def test_get_agility_status_structure(self):
        from omnix_core.security.crypto_providers import get_agility_status
        status = get_agility_status()
        assert "active_provider" in status
        assert "available_providers" in status
        assert "swap_requires_rewrite" in status
        assert status["swap_requires_rewrite"] is False
        assert status["adr"] == "ADR-043"


# ──────────────────────────────────────────────────────────────────────────────
# ADR-044: Transparency Chain & Internal Timestamp
# ──────────────────────────────────────────────────────────────────────────────

class TestInternalTimestamp:

    def test_create_returns_token(self):
        from omnix_core.evidence.transparency_chain import InternalTimestamp
        token = InternalTimestamp.create("a" * 64)
        assert "tst_data" in token
        assert "tst_hash" in token
        assert "ts_utc" in token

    def test_verify_valid_token(self):
        from omnix_core.evidence.transparency_chain import InternalTimestamp
        token = InternalTimestamp.create("b" * 64)
        assert InternalTimestamp.verify(token)

    def test_verify_fails_tampered_token(self):
        from omnix_core.evidence.transparency_chain import InternalTimestamp
        token = InternalTimestamp.create("c" * 64)
        token["tst_data"]["payload_hash"] = "tampered"
        assert not InternalTimestamp.verify(token)

    def test_nonce_is_different_each_call(self):
        from omnix_core.evidence.transparency_chain import InternalTimestamp
        t1 = InternalTimestamp.create("x" * 64)
        t2 = InternalTimestamp.create("x" * 64)
        assert t1["tst_data"]["nonce"] != t2["tst_data"]["nonce"]

    def test_policy_label_correct(self):
        from omnix_core.evidence.transparency_chain import InternalTimestamp
        token = InternalTimestamp.create("y" * 64)
        assert token["tst_data"]["policy"] == "OMNIX-ADR044-v1"


class TestRollingMerkleRoot:

    def test_first_entry_has_deterministic_start(self):
        from omnix_core.evidence.transparency_chain import compute_rolling_merkle_root
        root1 = compute_rolling_merkle_root("", "abc123")
        root2 = compute_rolling_merkle_root("", "abc123")
        assert root1 == root2

    def test_different_hashes_produce_different_roots(self):
        from omnix_core.evidence.transparency_chain import compute_rolling_merkle_root
        root1 = compute_rolling_merkle_root("", "hash_a")
        root2 = compute_rolling_merkle_root("", "hash_b")
        assert root1 != root2

    def test_chain_progression(self):
        from omnix_core.evidence.transparency_chain import compute_rolling_merkle_root
        hashes = ["hash_1", "hash_2", "hash_3"]
        root   = ""
        roots  = []
        for h in hashes:
            root = compute_rolling_merkle_root(root, h)
            roots.append(root)
        assert len(set(roots)) == 3

    def test_output_is_64_char_hex(self):
        from omnix_core.evidence.transparency_chain import compute_rolling_merkle_root
        root = compute_rolling_merkle_root("prev", "current")
        assert len(root) == 64
        assert all(c in "0123456789abcdef" for c in root)


class TestTransparencyChainNoDB:
    """Tests that work without a real database (no-op when DB unavailable)."""

    def test_chain_get_chain_empty_without_db(self):
        from omnix_core.evidence.transparency_chain import TransparencyChain
        os.environ["DATABASE_URL"] = ""
        chain = TransparencyChain()
        entries = chain.get_chain(symbol="BTC", limit=5)
        assert isinstance(entries, list)

    def test_verify_chain_integrity_empty(self):
        from omnix_core.evidence.transparency_chain import TransparencyChain
        chain  = TransparencyChain()
        result = chain.verify_chain_integrity([])
        assert result["valid"] is True
        assert result["length"] == 0
        assert result["breaks"] == []

    def test_verify_chain_integrity_valid_sequence(self):
        from omnix_core.evidence.transparency_chain import TransparencyChain, compute_rolling_merkle_root
        chain = TransparencyChain()

        h1 = hashlib.sha256(b"receipt1").hexdigest()
        h2 = hashlib.sha256(b"receipt2").hexdigest()
        h3 = hashlib.sha256(b"receipt3").hexdigest()

        r1 = compute_rolling_merkle_root("", h1)
        r2 = compute_rolling_merkle_root(r1, h2)
        r3 = compute_rolling_merkle_root(r2, h3)

        entries = [
            {"payload_hash": h1, "prev_log_hash": None, "merkle_root": r1},
            {"payload_hash": h2, "prev_log_hash": h1,   "merkle_root": r2},
            {"payload_hash": h3, "prev_log_hash": h2,   "merkle_root": r3},
        ]
        result = chain.verify_chain_integrity(entries)
        assert result["valid"] is True
        assert result["length"] == 3
        assert result["breaks"] == []

    def test_verify_chain_integrity_detects_break(self):
        from omnix_core.evidence.transparency_chain import TransparencyChain, compute_rolling_merkle_root
        chain = TransparencyChain()

        h1 = hashlib.sha256(b"receipt1").hexdigest()
        h2 = hashlib.sha256(b"receipt2").hexdigest()

        r1 = compute_rolling_merkle_root("", h1)
        r2 = compute_rolling_merkle_root(r1, h2)

        entries = [
            {"payload_hash": h1, "prev_log_hash": None, "merkle_root": r1},
            {"payload_hash": h2, "prev_log_hash": "tampered_hash", "merkle_root": r2},
        ]
        result = chain.verify_chain_integrity(entries)
        assert result["valid"] is False
        assert len(result["breaks"]) > 0

    def test_append_graceful_without_db(self):
        from omnix_core.evidence.transparency_chain import TransparencyChain
        os.environ["DATABASE_URL"] = ""
        chain = TransparencyChain()
        result = chain.append(
            receipt_id="TEST-RECEIPT-001",
            symbol="BTC",
            decision="HOLD",
            payload_hash="a" * 64,
        )
        assert result is None


# ──────────────────────────────────────────────────────────────────────────────
# ADR-043 + ADR-044: Updated DecisionReceiptEngine
# ──────────────────────────────────────────────────────────────────────────────

class TestDecisionReceiptEngineWithProvider:

    def test_generate_receipt_includes_signing_provider(self):
        os.environ["DATABASE_URL"] = ""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        engine  = DecisionReceiptEngine()
        receipt = engine.generate_receipt({"symbol": "BTC", "decision": "HOLD"})
        assert "signing_provider" in receipt
        assert receipt["signing_provider"] in ("dilithium3", "dilithium5", "ed25519", "none")

    def test_generate_receipt_has_signature_algorithm(self):
        os.environ["DATABASE_URL"] = ""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine
        engine  = DecisionReceiptEngine()
        receipt = engine.generate_receipt({"symbol": "ETH", "decision": "BUY"})
        assert "signature_algorithm" in receipt

    def test_verify_receipt_new_format(self):
        os.environ["DATABASE_URL"] = ""
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine, ReceiptVerifier
        engine  = DecisionReceiptEngine()
        receipt = engine.generate_receipt({"symbol": "BTC", "decision": "HOLD"})
        result  = ReceiptVerifier.verify_receipt(receipt)
        assert result["hash_valid"] is True
        assert result["overall_valid"] is True

    def test_verify_receipt_backward_compat_no_signing_provider(self):
        """Legacy receipts without signing_provider field still verify (hash only path)."""
        from omnix_core.evidence.decision_receipt import ReceiptVerifier
        import uuid
        from datetime import datetime, timezone

        legacy = {
            "receipt_id":         f"OMNIX-{uuid.uuid4().hex[:12].upper()}",
            "timestamp":          datetime.now(timezone.utc).isoformat(),
            "asset":              "BTC",
            "decision":           "HOLD",
            "veto_chain":         [],
            "policy_version":     "6.5.4e",
            "engine_version":     "6.5.4e",
            "prev_hash":          "",
            "signature":          None,
            "signature_algorithm": "NONE",
            "public_key":         None,
        }
        payload = {k: legacy[k] for k in [
            "receipt_id", "timestamp", "asset", "decision", "veto_chain",
            "policy_version", "engine_version", "prev_hash",
        ]}
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        legacy["content_hash"] = hashlib.sha256(canonical.encode()).hexdigest()

        result = ReceiptVerifier.verify_receipt(legacy)
        assert result["hash_valid"] is True
        assert result["overall_valid"] is True
