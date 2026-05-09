"""
ETA-001 Trust Anchor Adversarial Tests
=======================================
Tests the OMNIX trust-anchor validation layer.
Covers all five trust status codes and adversarial scenarios:
  - Forged receipt signed with attacker keypair
  - Altered receipt (hash mismatch)
  - Unknown key (no public key in receipt)
  - Valid OMNIX key (env anchor present, fingerprint matches)
  - SHA-only downgrade (no PQC signature)

ADR-085 / ETA-001 (External Trust and Defensibility Stage 4)
"""
import base64
import hashlib
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from omnix_core.evidence.trust_anchor import (
    compute_key_fingerprint,
    classify_receipt,
    build_trust_anchor_block,
    load_trusted_omnix_fingerprint,
    TRUST_STATUS_VALID_OMNIX_ISSUED,
    TRUST_STATUS_VALID_UNTRUSTED_ISSUER,
    TRUST_STATUS_INVALID_SIGNATURE,
    TRUST_STATUS_UNKNOWN_KEY,
    TRUST_STATUS_DOWNGRADED_SHA_ONLY,
)

try:
    from pqc.sign import dilithium3
    PQC_AVAILABLE = True
except ImportError:
    PQC_AVAILABLE = False

SKIP_PQC = unittest.skipUnless(PQC_AVAILABLE, "pqcrypto not installed")


def _gen_keypair():
    """Generate a fresh Dilithium-3 keypair. Returns (public_key_b64, secret_key_b64)."""
    pk, sk = dilithium3.keypair()
    return base64.b64encode(pk).decode(), base64.b64encode(sk).decode()


def _sign(content_hash: str, sk_b64: str) -> str:
    """Sign a content hash with a Dilithium-3 secret key. Returns b64 signature."""
    sk = base64.b64decode(sk_b64)
    msg = content_hash.encode("utf-8")
    sig = dilithium3.sign(msg, sk)
    return base64.b64encode(sig).decode()


class TestComputeKeyFingerprint(unittest.TestCase):
    """Basic fingerprint computation."""

    def test_deterministic(self):
        raw = b"\x01" * 1952
        b64 = base64.b64encode(raw).decode()
        fp1 = compute_key_fingerprint(b64)
        fp2 = compute_key_fingerprint(b64)
        self.assertEqual(fp1, fp2)
        self.assertEqual(len(fp1), 64)

    def test_different_keys_different_fingerprints(self):
        raw1 = b"\x01" * 1952
        raw2 = b"\x02" * 1952
        fp1 = compute_key_fingerprint(base64.b64encode(raw1).decode())
        fp2 = compute_key_fingerprint(base64.b64encode(raw2).decode())
        self.assertNotEqual(fp1, fp2)

    def test_fingerprint_is_sha256_of_raw_bytes(self):
        raw = b"\xAB\xCD" * 976
        b64 = base64.b64encode(raw).decode()
        expected = hashlib.sha256(raw).hexdigest()
        self.assertEqual(compute_key_fingerprint(b64), expected)


class TestClassifyReceiptSHAOnly(unittest.TestCase):
    """DOWNGRADED_SHA_ONLY — no PQC signature present."""

    def test_sha_only_hash_valid(self):
        status, trusted, fp = classify_receipt(
            hash_valid=True,
            signature_valid=None,
            sig_b64=None,
            pub_key_b64=None,
            sig_algo="SHA-256",
            allow_well_known=False,
        )
        self.assertEqual(status, TRUST_STATUS_DOWNGRADED_SHA_ONLY)
        self.assertFalse(trusted)
        self.assertIsNone(fp)

    def test_sha_only_hash_invalid_becomes_invalid_sig(self):
        status, trusted, fp = classify_receipt(
            hash_valid=False,
            signature_valid=None,
            sig_b64=None,
            pub_key_b64=None,
            sig_algo="SHA-256",
        )
        self.assertEqual(status, TRUST_STATUS_INVALID_SIGNATURE)
        self.assertFalse(trusted)

    def test_no_sig_field_no_algo(self):
        status, trusted, fp = classify_receipt(
            hash_valid=True,
            signature_valid=None,
            sig_b64=None,
            pub_key_b64=None,
            sig_algo=None,
        )
        self.assertEqual(status, TRUST_STATUS_DOWNGRADED_SHA_ONLY)
        self.assertFalse(trusted)


class TestClassifyReceiptUnknownKey(unittest.TestCase):
    """UNKNOWN_KEY — signature present but no public key."""

    def test_sig_present_no_key(self):
        status, trusted, fp = classify_receipt(
            hash_valid=True,
            signature_valid=None,
            sig_b64="c2lnbmF0dXJlYmFzZTY0",
            pub_key_b64=None,
            sig_algo="dilithium3",
            allow_well_known=False,
        )
        self.assertEqual(status, TRUST_STATUS_UNKNOWN_KEY)
        self.assertFalse(trusted)
        self.assertIsNone(fp)

    def test_sig_present_pqc_unavailable(self):
        status, trusted, fp = classify_receipt(
            hash_valid=True,
            signature_valid=None,
            sig_b64="c2lnbmF0dXJlYmFzZTY0",
            pub_key_b64=None,
            sig_algo="ML-DSA-65",
            allow_well_known=False,
        )
        self.assertEqual(status, TRUST_STATUS_UNKNOWN_KEY)
        self.assertFalse(trusted)


class TestClassifyReceiptInvalidSignature(unittest.TestCase):
    """INVALID_SIGNATURE — PQC signature mathematically invalid."""

    def test_invalid_pqc_sig(self):
        raw = b"\x03" * 1952
        pub_b64 = base64.b64encode(raw).decode()
        status, trusted, fp = classify_receipt(
            hash_valid=True,
            signature_valid=False,
            sig_b64="dGhpc2lzYWZha2VzaWduYXR1cmU=",
            pub_key_b64=pub_b64,
            sig_algo="dilithium3",
            allow_well_known=False,
        )
        self.assertEqual(status, TRUST_STATUS_INVALID_SIGNATURE)
        self.assertFalse(trusted)
        self.assertIsNotNone(fp)

    def test_altered_receipt_becomes_invalid_sig(self):
        raw = b"\x04" * 1952
        pub_b64 = base64.b64encode(raw).decode()
        status, trusted, fp = classify_receipt(
            hash_valid=False,
            signature_valid=False,
            sig_b64="dGhpc2lzYWZha2VzaWduYXR1cmU=",
            pub_key_b64=pub_b64,
            sig_algo="dilithium3",
            allow_well_known=False,
        )
        self.assertEqual(status, TRUST_STATUS_INVALID_SIGNATURE)
        self.assertFalse(trusted)


@SKIP_PQC
class TestAdversarialAttackerKeypair(unittest.TestCase):
    """
    VALID_SIGNATURE_UNTRUSTED_ISSUER
    ── Attacker generates a valid Dilithium-3 keypair and signs a receipt.
    The PQC signature is mathematically valid, but the key fingerprint
    does NOT match the trusted OMNIX anchor → must be REJECTED.
    This is the classic attacker-keypair exploit that ETA-001 closes.
    """

    def setUp(self):
        self.omnix_pub_b64, self.omnix_sk_b64 = _gen_keypair()
        self.attacker_pub_b64, self.attacker_sk_b64 = _gen_keypair()
        self.content_hash = "a" * 64
        self.omnix_fp = compute_key_fingerprint(self.omnix_pub_b64)
        os.environ["OMNIX_TRUSTED_KEY_FINGERPRINT"] = self.omnix_fp

    def tearDown(self):
        os.environ.pop("OMNIX_TRUSTED_KEY_FINGERPRINT", None)

    def test_attacker_keypair_rejected_as_untrusted(self):
        """Forged receipt with attacker keypair — valid sig, wrong issuer."""
        attacker_sig = _sign(self.content_hash, self.attacker_sk_b64)

        pk = base64.b64decode(self.attacker_pub_b64)
        sig = base64.b64decode(attacker_sig)
        msg = self.content_hash.encode("utf-8")
        dilithium3.verify(sig, msg, pk)

        status, trusted, fp = classify_receipt(
            hash_valid=True,
            signature_valid=True,
            sig_b64=attacker_sig,
            pub_key_b64=self.attacker_pub_b64,
            sig_algo="dilithium3",
            allow_well_known=False,
        )
        self.assertEqual(status, TRUST_STATUS_VALID_UNTRUSTED_ISSUER)
        self.assertFalse(trusted)
        self.assertNotEqual(fp, self.omnix_fp)

    def test_omnix_keypair_accepted(self):
        """Receipt signed by the real OMNIX key → VALID_OMNIX_ISSUED."""
        omnix_sig = _sign(self.content_hash, self.omnix_sk_b64)
        status, trusted, fp = classify_receipt(
            hash_valid=True,
            signature_valid=True,
            sig_b64=omnix_sig,
            pub_key_b64=self.omnix_pub_b64,
            sig_algo="dilithium3",
            allow_well_known=False,
        )
        self.assertEqual(status, TRUST_STATUS_VALID_OMNIX_ISSUED)
        self.assertTrue(trusted)
        self.assertEqual(fp, self.omnix_fp)

    def test_attacker_sig_on_omnix_public_key_fails_pqc(self):
        """Attacker signature on OMNIX public key → INVALID_SIGNATURE (PQC check would fail)."""
        attacker_sig = _sign(self.content_hash, self.attacker_sk_b64)
        status, trusted, fp = classify_receipt(
            hash_valid=True,
            signature_valid=False,
            sig_b64=attacker_sig,
            pub_key_b64=self.omnix_pub_b64,
            sig_algo="dilithium3",
            allow_well_known=False,
        )
        self.assertEqual(status, TRUST_STATUS_INVALID_SIGNATURE)
        self.assertFalse(trusted)


@SKIP_PQC
class TestValidOmnixIssuance(unittest.TestCase):
    """Full end-to-end: valid OMNIX key in env, receipt signed with OMNIX key."""

    def setUp(self):
        self.omnix_pub_b64, self.omnix_sk_b64 = _gen_keypair()
        self.content_hash = hashlib.sha256(b"test payload").hexdigest()
        self.omnix_fp = compute_key_fingerprint(self.omnix_pub_b64)
        os.environ["OMNIX_SIGNING_PUBLIC_KEY_B64"] = self.omnix_pub_b64
        os.environ.pop("OMNIX_TRUSTED_KEY_FINGERPRINT", None)

    def tearDown(self):
        os.environ.pop("OMNIX_SIGNING_PUBLIC_KEY_B64", None)
        os.environ.pop("OMNIX_TRUSTED_KEY_FINGERPRINT", None)

    def test_valid_omnix_issued_e2e(self):
        omnix_sig = _sign(self.content_hash, self.omnix_sk_b64)
        status, trusted, fp = classify_receipt(
            hash_valid=True,
            signature_valid=True,
            sig_b64=omnix_sig,
            pub_key_b64=self.omnix_pub_b64,
            sig_algo="dilithium3",
            allow_well_known=False,
        )
        self.assertEqual(status, TRUST_STATUS_VALID_OMNIX_ISSUED)
        self.assertTrue(trusted)
        self.assertEqual(fp, self.omnix_fp)

    def test_trusted_fp_env_takes_priority(self):
        """OMNIX_TRUSTED_KEY_FINGERPRINT env var takes priority over public key env var."""
        attacker_pub, attacker_sk = _gen_keypair()
        attacker_fp = compute_key_fingerprint(attacker_pub)
        os.environ["OMNIX_TRUSTED_KEY_FINGERPRINT"] = attacker_fp

        omnix_sig = _sign(self.content_hash, self.omnix_sk_b64)
        status, trusted, fp = classify_receipt(
            hash_valid=True,
            signature_valid=True,
            sig_b64=omnix_sig,
            pub_key_b64=self.omnix_pub_b64,
            sig_algo="dilithium3",
            allow_well_known=False,
        )
        self.assertEqual(status, TRUST_STATUS_VALID_UNTRUSTED_ISSUER)
        self.assertFalse(trusted)

    def test_no_anchor_configured_returns_untrusted(self):
        """If no anchor is configured (no env vars, no well-known) → UNTRUSTED_ISSUER."""
        os.environ.pop("OMNIX_SIGNING_PUBLIC_KEY_B64", None)
        os.environ.pop("OMNIX_TRUSTED_KEY_FINGERPRINT", None)

        omnix_sig = _sign(self.content_hash, self.omnix_sk_b64)
        status, trusted, fp = classify_receipt(
            hash_valid=True,
            signature_valid=True,
            sig_b64=omnix_sig,
            pub_key_b64=self.omnix_pub_b64,
            sig_algo="dilithium3",
            allow_well_known=False,
        )
        self.assertEqual(status, TRUST_STATUS_VALID_UNTRUSTED_ISSUER)
        self.assertFalse(trusted)


class TestBuildTrustAnchorBlock(unittest.TestCase):
    """build_trust_anchor_block() returns well-formed dict."""

    def test_sha_only_block_structure(self):
        block = build_trust_anchor_block(
            hash_valid=True,
            signature_valid=None,
            sig_b64=None,
            pub_key_b64=None,
            sig_algo="SHA-256",
            allow_well_known=False,
        )
        self.assertIn("trust_status", block)
        self.assertIn("issuer_trusted", block)
        self.assertIn("key_fingerprint", block)
        self.assertIn("trusted_anchor_fingerprint", block)
        self.assertIn("anchor_source", block)
        self.assertIn("trust_status_description", block)
        self.assertEqual(block["trust_status"], TRUST_STATUS_DOWNGRADED_SHA_ONLY)
        self.assertFalse(block["issuer_trusted"])
        self.assertIsInstance(block["trust_status_description"], str)
        self.assertGreater(len(block["trust_status_description"]), 10)

    def test_unknown_key_block(self):
        block = build_trust_anchor_block(
            hash_valid=True,
            signature_valid=None,
            sig_b64="c2ln",
            pub_key_b64=None,
            sig_algo="dilithium3",
            allow_well_known=False,
        )
        self.assertEqual(block["trust_status"], TRUST_STATUS_UNKNOWN_KEY)
        self.assertFalse(block["issuer_trusted"])


class TestUnknownFingerprintNoAnchor(unittest.TestCase):
    """No anchor configured → cannot confirm OMNIX issuance."""

    def setUp(self):
        os.environ.pop("OMNIX_TRUSTED_KEY_FINGERPRINT", None)
        os.environ.pop("OMNIX_SIGNING_PUBLIC_KEY_B64", None)

    def test_no_anchor_sig_valid_returns_untrusted(self):
        raw = b"\x10" * 1952
        pub_b64 = base64.b64encode(raw).decode()
        status, trusted, fp = classify_receipt(
            hash_valid=True,
            signature_valid=True,
            sig_b64="c2lnbmF0dXJl",
            pub_key_b64=pub_b64,
            sig_algo="dilithium3",
            allow_well_known=False,
        )
        self.assertEqual(status, TRUST_STATUS_VALID_UNTRUSTED_ISSUER)
        self.assertFalse(trusted)
        self.assertIsNotNone(fp)

    def test_no_anchor_sha_only_hash_valid(self):
        status, trusted, fp = classify_receipt(
            hash_valid=True,
            signature_valid=None,
            sig_b64=None,
            pub_key_b64=None,
            sig_algo="SHA-256",
            allow_well_known=False,
        )
        self.assertEqual(status, TRUST_STATUS_DOWNGRADED_SHA_ONLY)
        self.assertFalse(trusted)


class TestLoadTrustedFingerprint(unittest.TestCase):
    """load_trusted_omnix_fingerprint() priority chain."""

    def setUp(self):
        os.environ.pop("OMNIX_TRUSTED_KEY_FINGERPRINT", None)
        os.environ.pop("OMNIX_SIGNING_PUBLIC_KEY_B64", None)

    def tearDown(self):
        os.environ.pop("OMNIX_TRUSTED_KEY_FINGERPRINT", None)
        os.environ.pop("OMNIX_SIGNING_PUBLIC_KEY_B64", None)

    def test_pinned_fingerprint_has_highest_priority(self):
        fake_fp = "a" * 64
        os.environ["OMNIX_TRUSTED_KEY_FINGERPRINT"] = fake_fp
        raw = b"\x20" * 1952
        os.environ["OMNIX_SIGNING_PUBLIC_KEY_B64"] = base64.b64encode(raw).decode()
        result = load_trusted_omnix_fingerprint(allow_well_known=False)
        self.assertEqual(result, fake_fp)

    def test_pubkey_env_var_computed(self):
        raw = b"\x30" * 1952
        b64 = base64.b64encode(raw).decode()
        os.environ["OMNIX_SIGNING_PUBLIC_KEY_B64"] = b64
        expected = hashlib.sha256(raw).hexdigest()
        result = load_trusted_omnix_fingerprint(allow_well_known=False)
        self.assertEqual(result, expected)

    def test_no_anchor_returns_none(self):
        result = load_trusted_omnix_fingerprint(allow_well_known=False)
        self.assertIsNone(result)

    def test_invalid_pinned_fingerprint_ignored(self):
        os.environ["OMNIX_TRUSTED_KEY_FINGERPRINT"] = "tooshort"
        result = load_trusted_omnix_fingerprint(allow_well_known=False)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
