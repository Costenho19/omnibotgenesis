"""
OMNIX — Post-Quantum Cryptography Module
==========================================
Cryptographic signing and key encapsulation using NIST-standardized algorithms.

Signing level is configurable via PQC_SIGNING_LEVEL environment variable.
See omnix_core/security/pqc_config.py for tier definitions.

ADR-022 — Post-Quantum Cryptography Implementation
ADR-031 — PQC Configurable Assurance Tiers

Operational since: November 2025
Author: Harold Nunes
"""

import json
import base64
import logging
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
import hashlib

try:
    from pqc.kem import kyber768
    KEM_AVAILABLE = True
except ImportError:
    KEM_AVAILABLE = False
    kyber768 = None  # type: ignore
    logging.warning("pypqc KEM (kyber768) not available.")

from omnix_core.security.pqc_config import (
    SIGNING_MODULE as _dilithium,
    ALGORITHM_NAME,
    ML_DSA_VARIANT,
    SECURITY_LEVEL_DESC,
    KEY_SIZES,
    SIGNING_LEVEL,
    AVAILABLE_TIERS,
)

PQC_AVAILABLE = _dilithium is not None and KEM_AVAILABLE


class PostQuantumSecurity:
    """
    Post-quantum cryptographic security for OMNIX governance infrastructure.

    Signing algorithm is selected by PQC_SIGNING_LEVEL environment variable:
      3 → Dilithium-3 (ML-DSA-65) — enterprise-grade baseline (default)
      5 → Dilithium-5 (ML-DSA-87) — high-assurance / national-grade
    """

    def __init__(self):
        self.logger = logging.getLogger("OMNIX.PQC")
        self.pqc_enabled = PQC_AVAILABLE
        self.version = "1.1.0"
        self.signing_level = SIGNING_LEVEL
        self.algorithm_name = ALGORITHM_NAME
        self.ml_dsa_variant = ML_DSA_VARIANT
        self.security_level_desc = SECURITY_LEVEL_DESC

        if self.pqc_enabled:
            self.logger.info(f"POST-QUANTUM CRYPTOGRAPHY ACTIVE — {self.algorithm_name}")
            self.logger.info(f"KEM: Kyber-768 (ML-KEM-768) | Signing: {self.algorithm_name}")
        else:
            self.logger.error("PQC NOT AVAILABLE — install pypqc: pip install pypqc")

    def generate_keypair_encryption(self) -> Optional[Tuple[bytes, bytes]]:
        """Generate Kyber-768 key pair for key encapsulation (not data encryption)."""
        if not KEM_AVAILABLE:
            self.logger.error("Kyber-768 not available.")
            return None
        try:
            public_key, secret_key = kyber768.keypair()
            self.logger.info(f"Kyber-768 keypair generated. PK: {len(public_key)}B SK: {len(secret_key)}B")
            return public_key, secret_key
        except Exception as e:
            self.logger.error(f"Kyber-768 keypair generation failed: {e}")
            return None

    def encapsulate_secret(self, public_key: bytes) -> Optional[Tuple[bytes, bytes]]:
        """Encapsulate a shared secret using Kyber-768 (key exchange, not data encryption)."""
        if not KEM_AVAILABLE:
            self.logger.error("Kyber-768 not available.")
            return None
        try:
            shared_secret, ciphertext = kyber768.encap(public_key)
            return shared_secret, ciphertext
        except Exception as e:
            self.logger.error(f"Kyber-768 encapsulation failed: {e}")
            return None

    def decapsulate_secret(self, ciphertext: bytes, secret_key: bytes) -> Optional[bytes]:
        """Recover a shared secret from Kyber-768 ciphertext."""
        if not KEM_AVAILABLE:
            self.logger.error("Kyber-768 not available.")
            return None
        try:
            return kyber768.decap(ciphertext, secret_key)
        except Exception as e:
            self.logger.error(f"Kyber-768 decapsulation failed: {e}")
            return None

    def generate_keypair_signature(self) -> Optional[Tuple[bytes, bytes]]:
        """Generate signing key pair using the configured Dilithium level."""
        if not self.pqc_enabled or _dilithium is None:
            self.logger.error("Signing module not available.")
            return None
        try:
            public_key, secret_key = _dilithium.keypair()
            self.logger.info(
                f"{self.algorithm_name} keypair generated. PK: {len(public_key)}B SK: {len(secret_key)}B"
            )
            return public_key, secret_key
        except Exception as e:
            self.logger.error(f"Keypair generation failed: {e}")
            return None

    def sign_message(self, message: bytes, secret_key: bytes) -> Optional[bytes]:
        """Sign an arbitrary message using the configured Dilithium level."""
        if not self.pqc_enabled or _dilithium is None:
            self.logger.error("Signing module not available.")
            return None
        try:
            signature = _dilithium.sign(message, secret_key)
            self.logger.info(f"Message signed with {self.algorithm_name}. Signature: {len(signature)}B")
            return signature
        except Exception as e:
            self.logger.error(f"Message signing failed: {e}")
            return None

    def verify_signature(self, signature: bytes, message: bytes, public_key: bytes) -> bool:
        """Verify a digital signature using the configured Dilithium level."""
        if not self.pqc_enabled or _dilithium is None:
            self.logger.error("Signing module not available.")
            return False
        try:
            _dilithium.verify(signature, message, public_key)
            return True
        except Exception as e:
            self.logger.error(f"Signature verification failed: {e}")
            return False

    def secure_api_key(self, api_key: str, public_key: bytes) -> Optional[Dict[str, str]]:
        """
        Protect an API key using Kyber-768 KEM for secure transmission.
        Note: Kyber-768 provides key encapsulation — actual key material is XOR'd
        with the derived shared secret. Not bulk data encryption.
        """
        if not KEM_AVAILABLE:
            self.logger.error("Kyber-768 not available.")
            return None
        try:
            result = self.encapsulate_secret(public_key)
            if not result:
                return None
            shared_secret, ciphertext = result
            key_hash = hashlib.sha256(shared_secret).digest()
            encrypted_key = bytes(a ^ b for a, b in zip(api_key.encode(), key_hash[:len(api_key)]))
            return {
                'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
                'encrypted_key': base64.b64encode(encrypted_key).decode('utf-8'),
                'timestamp': datetime.now().isoformat(),
                'algorithm': 'Kyber-768 (ML-KEM-768)',
            }
        except Exception as e:
            self.logger.error(f"API key protection failed: {e}")
            return None

    def sign_trading_order(self, order_data: Dict[str, Any], secret_key: bytes) -> Optional[str]:
        """Sign a trading order payload with the configured Dilithium level."""
        if not self.pqc_enabled or _dilithium is None:
            self.logger.error("Signing module not available.")
            return None
        try:
            order_json = json.dumps(order_data, sort_keys=True).encode('utf-8')
            signature = self.sign_message(order_json, secret_key)
            if signature:
                self.logger.info(f"Trading order signed: {order_data.get('symbol', 'N/A')}")
                return base64.b64encode(signature).decode('utf-8')
            return None
        except Exception as e:
            self.logger.error(f"Trading order signing failed: {e}")
            return None

    def verify_trading_order(
        self,
        order_data: Dict[str, Any],
        signature_b64: str,
        public_key: bytes,
    ) -> bool:
        """Verify a trading order signature."""
        if not self.pqc_enabled or _dilithium is None:
            self.logger.error("Signing module not available.")
            return False
        try:
            order_json = json.dumps(order_data, sort_keys=True).encode('utf-8')
            signature = base64.b64decode(signature_b64)
            return self.verify_signature(signature, order_json, public_key)
        except Exception as e:
            self.logger.error(f"Trading order verification failed: {e}")
            return False

    def get_security_info(self) -> Dict[str, Any]:
        """
        Return full cryptographic security posture for this instance.
        Includes active tier and all available tiers for institutional disclosure.
        """
        return {
            'pqc_enabled': self.pqc_enabled,
            'version': self.version,
            'active_tier': {
                'signing_level': self.signing_level,
                'algorithm_name': self.algorithm_name,
                'ml_dsa_variant': self.ml_dsa_variant,
                'security_level_desc': self.security_level_desc,
                'key_sizes': KEY_SIZES,
            },
            'kem': {
                'algorithm': 'Kyber-768 (ML-KEM-768)',
                'role': 'Key Encapsulation Mechanism — key exchange only, not data encryption',
                'available': KEM_AVAILABLE,
            },
            'available_tiers': AVAILABLE_TIERS,
            'deployment_note': (
                'Signing level is deployment-context configurable via PQC_SIGNING_LEVEL '
                'environment variable. No architectural rewrite required to change tiers. '
                'Level 3 = enterprise baseline. Level 5 = high-assurance / national-grade.'
            ),
            'quantum_resistant': True,
            'nist_approved': True,
            'production_ready': True,
            'operational_since': '2025-11',
        }
