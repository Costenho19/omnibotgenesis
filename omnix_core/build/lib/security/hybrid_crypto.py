"""
OMNIX — Hybrid Cryptography Module
ADR-042: Hybrid Classical + Post-Quantum Key Exchange

Combines X25519 (classical ECDH) with Kyber-768 (PQC KEM) via HKDF.
Combined shared secret = HKDF(kyber_secret || ecdh_secret, context)

Rationale (ADR-042):
  - If Kyber is broken by a future algorithm → X25519 still protects
  - If X25519 is broken by a quantum computer → Kyber-768 still protects
  - Industry standard for quantum transition (NIST recommends hybrid approach)

Fail-safe degradation:
  - Both available  → hybrid (strongest)
  - Only Kyber      → kyber_only
  - Only X25519     → ecdh_only
  - Neither         → None (logged as critical)

Operational since: March 2026
Author: Harold Nunes
"""

import hashlib
import logging
import os
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger("OMNIX.Security.Hybrid")

try:
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives.hashes import SHA256
    from cryptography.hazmat.primitives.serialization import (
        Encoding, PublicFormat, PrivateFormat, NoEncryption
    )
    ECDH_AVAILABLE = True
except ImportError:
    ECDH_AVAILABLE = False
    logger.warning("[Hybrid] X25519 (cryptography library) not available.")

try:
    from pqc.kem import kyber768
    KYBER_AVAILABLE = True
except ImportError:
    KYBER_AVAILABLE = False
    logger.warning("[Hybrid] Kyber-768 (pypqc) not available.")


HKDF_INFO_LABEL = b"OMNIX-ADR042-HybridKEM-v1"
HKDF_OUTPUT_LEN = 32


def _hkdf_combine(kyber_secret: Optional[bytes], ecdh_secret: Optional[bytes]) -> bytes:
    """
    Derive a single 32-byte combined secret using HKDF.
    Both inputs are concatenated as IKM. Missing components become empty bytes.
    """
    ikm = (kyber_secret or b"") + (ecdh_secret or b"")
    h = HKDF(
        algorithm=SHA256(),
        length=HKDF_OUTPUT_LEN,
        salt=None,
        info=HKDF_INFO_LABEL,
    )
    return h.derive(ikm)


class HybridKEM:
    """
    Hybrid Key Encapsulation: X25519 ECDH + Kyber-768 PQC.

    Usage (sender side):
        recipient_public = HybridRecipient.public_bundle()
        result = HybridKEM.encapsulate(recipient_public)
        shared_secret = result["combined_secret"]

    Usage (recipient side):
        shared_secret = HybridKEM.decapsulate(result["ciphertext_bundle"], recipient_private_bundle)
    """

    @staticmethod
    def generate_keypair() -> Optional[Dict[str, Any]]:
        """
        Generate a hybrid keypair bundle.
        Returns dict with 'private' and 'public' sub-bundles, and 'mode'.
        """
        private_bundle: Dict[str, Any] = {}
        public_bundle:  Dict[str, Any] = {}
        mode_parts = []

        if KYBER_AVAILABLE:
            try:
                kyber_pub, kyber_sec = kyber768.keypair()
                private_bundle["kyber_secret"] = kyber_sec
                public_bundle["kyber_public"]  = kyber_pub
                mode_parts.append("kyber768")
            except Exception as e:
                logger.error(f"[Hybrid] Kyber keypair generation failed: {e}")

        if ECDH_AVAILABLE:
            try:
                ecdh_priv = X25519PrivateKey.generate()
                ecdh_pub  = ecdh_priv.public_key()
                private_bundle["ecdh_private"] = ecdh_priv
                public_bundle["ecdh_public"]   = ecdh_pub
                mode_parts.append("x25519")
            except Exception as e:
                logger.error(f"[Hybrid] X25519 keypair generation failed: {e}")

        if not mode_parts:
            logger.critical("[Hybrid] No KEM algorithm available. Hybrid keypair generation failed.")
            return None

        mode = "hybrid" if len(mode_parts) == 2 else mode_parts[0] + "_only"
        logger.info(f"[Hybrid] Keypair generated — mode: {mode}")
        return {"private": private_bundle, "public": public_bundle, "mode": mode}

    @staticmethod
    def encapsulate(public_bundle: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Sender: encapsulate a shared secret against the recipient's public bundle.
        Returns ciphertext_bundle + combined_secret (32 bytes).
        """
        kyber_ct:     Optional[bytes] = None
        kyber_secret: Optional[bytes] = None
        ecdh_ct:      Optional[bytes] = None
        ecdh_secret:  Optional[bytes] = None
        mode_parts = []

        if KYBER_AVAILABLE and "kyber_public" in public_bundle:
            try:
                kyber_secret, kyber_ct = kyber768.encap(public_bundle["kyber_public"])
                mode_parts.append("kyber768")
            except Exception as e:
                logger.error(f"[Hybrid] Kyber encapsulation failed: {e}")

        if ECDH_AVAILABLE and "ecdh_public" in public_bundle:
            try:
                ephemeral_priv = X25519PrivateKey.generate()
                ecdh_secret    = ephemeral_priv.exchange(public_bundle["ecdh_public"])
                ecdh_ct        = ephemeral_priv.public_key().public_bytes(
                    Encoding.Raw, PublicFormat.Raw
                )
                mode_parts.append("x25519")
            except Exception as e:
                logger.error(f"[Hybrid] X25519 encapsulation failed: {e}")

        if not mode_parts:
            logger.critical("[Hybrid] Encapsulation failed — no algorithm available.")
            return None

        combined = _hkdf_combine(kyber_secret, ecdh_secret)
        mode = "hybrid" if len(mode_parts) == 2 else mode_parts[0] + "_only"

        return {
            "combined_secret":   combined,
            "ciphertext_bundle": {
                "kyber_ciphertext": kyber_ct,
                "ecdh_ephemeral_pub": ecdh_ct,
            },
            "mode": mode,
            "algorithm": "X25519+Kyber-768/HKDF-SHA256",
        }

    @staticmethod
    def decapsulate(
        ciphertext_bundle: Dict[str, Any],
        private_bundle: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Recipient: recover the shared secret from ciphertext_bundle.
        Returns combined_secret (32 bytes) and metadata.
        """
        kyber_secret: Optional[bytes] = None
        ecdh_secret:  Optional[bytes] = None
        mode_parts = []

        if KYBER_AVAILABLE and "kyber_ciphertext" in ciphertext_bundle and "kyber_secret" in private_bundle:
            try:
                kyber_secret = kyber768.decap(
                    ciphertext_bundle["kyber_ciphertext"],
                    private_bundle["kyber_secret"]
                )
                mode_parts.append("kyber768")
            except Exception as e:
                logger.error(f"[Hybrid] Kyber decapsulation failed: {e}")

        if ECDH_AVAILABLE and "ecdh_ephemeral_pub" in ciphertext_bundle and "ecdh_private" in private_bundle:
            try:
                ephem_pub_bytes = ciphertext_bundle["ecdh_ephemeral_pub"]
                ephem_pub = X25519PublicKey.from_public_bytes(ephem_pub_bytes)
                ecdh_secret = private_bundle["ecdh_private"].exchange(ephem_pub)
                mode_parts.append("x25519")
            except Exception as e:
                logger.error(f"[Hybrid] X25519 decapsulation failed: {e}")

        if not mode_parts:
            logger.critical("[Hybrid] Decapsulation failed — no algorithm recovered a secret.")
            return None

        combined = _hkdf_combine(kyber_secret, ecdh_secret)
        mode = "hybrid" if len(mode_parts) == 2 else mode_parts[0] + "_only"

        return {
            "combined_secret": combined,
            "mode": mode,
            "algorithm": "X25519+Kyber-768/HKDF-SHA256",
        }

    @staticmethod
    def get_capabilities() -> Dict[str, Any]:
        return {
            "kyber768_available": KYBER_AVAILABLE,
            "x25519_available":   ECDH_AVAILABLE,
            "hybrid_available":   KYBER_AVAILABLE and ECDH_AVAILABLE,
            "hkdf_label":         HKDF_INFO_LABEL.decode(),
            "output_length_bytes": HKDF_OUTPUT_LEN,
            "adr": "ADR-042",
        }
