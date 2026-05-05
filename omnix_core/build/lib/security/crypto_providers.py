"""
OMNIX — Crypto-Agility Provider Layer
ADR-043: Crypto-Agility Layer

Abstracts signing algorithms behind a CryptoProvider interface.
Swapping algorithms = change ACTIVE_SIGNING_PROVIDER env var.
No code changes needed. No architectural rewrite.

Provider registry:
  "dilithium3" → Dilithium-3 (ML-DSA-65, FIPS 204) — enterprise baseline
  "dilithium5" → Dilithium-5 (ML-DSA-87, FIPS 204) — high-assurance
  "ed25519"    → Ed25519 (classical fallback, dev/test environments)

Default: resolves from PQC_SIGNING_LEVEL for backward compatibility.

Backward compatibility:
  Old receipts signed with dilithium3 can still be verified via the registry.
  Algorithm ID is embedded in receipt metadata → verification dispatches correctly.

Security: provider_id is bound into the signed payload to prevent
algorithm confusion / downgrade attacks.

Author: Harold Nunes
Operational since: March 2026
ADR: ADR-043
"""

import os
import base64
import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger("OMNIX.Security.CryptoAgility")


class CryptoProvider(ABC):
    """Abstract interface every signing provider must implement."""

    @abstractmethod
    def provider_id(self) -> str:
        """Unique, stable identifier (used in signed payloads)."""

    @abstractmethod
    def algorithm_name(self) -> str:
        """Human-readable name for institutional disclosure."""

    @abstractmethod
    def generate_keypair(self) -> Optional[Tuple[bytes, bytes]]:
        """Returns (public_key, secret_key) or None on failure."""

    @abstractmethod
    def sign(self, message: bytes, secret_key: bytes) -> Optional[bytes]:
        """Sign message. Returns raw signature bytes or None."""

    @abstractmethod
    def verify(self, signature: bytes, message: bytes, public_key: bytes) -> bool:
        """Returns True if signature is valid."""

    def serialize_public_key(self, public_key: bytes) -> str:
        return base64.b64encode(public_key).decode("utf-8")

    def deserialize_public_key(self, data: str) -> bytes:
        return base64.b64decode(data)

    def get_info(self) -> Dict[str, Any]:
        return {
            "provider_id":    self.provider_id(),
            "algorithm_name": self.algorithm_name(),
            "available":      self._is_available(),
        }

    def _is_available(self) -> bool:
        try:
            kp = self.generate_keypair()
            return kp is not None
        except Exception:
            return False


# ─── Dilithium-3 Provider ────────────────────────────────────────────────────

class Dilithium3Provider(CryptoProvider):
    """Dilithium-3 (ML-DSA-65) — enterprise baseline, FIPS 204."""

    def provider_id(self) -> str:
        return "dilithium3"

    def algorithm_name(self) -> str:
        return "Dilithium-3 (ML-DSA-65)"

    def generate_keypair(self) -> Optional[Tuple[bytes, bytes]]:
        try:
            from pqc.sign import dilithium3
            return dilithium3.keypair()
        except Exception as e:
            logger.error(f"[Dilithium3] keypair generation failed: {e}")
            return None

    def sign(self, message: bytes, secret_key: bytes) -> Optional[bytes]:
        try:
            from pqc.sign import dilithium3
            return dilithium3.sign(message, secret_key)
        except Exception as e:
            logger.error(f"[Dilithium3] sign failed: {e}")
            return None

    def verify(self, signature: bytes, message: bytes, public_key: bytes) -> bool:
        try:
            from pqc.sign import dilithium3
            dilithium3.verify(signature, message, public_key)
            return True
        except Exception:
            return False


# ─── Dilithium-5 Provider ────────────────────────────────────────────────────

class Dilithium5Provider(CryptoProvider):
    """Dilithium-5 (ML-DSA-87) — high-assurance, national-grade, FIPS 204."""

    def provider_id(self) -> str:
        return "dilithium5"

    def algorithm_name(self) -> str:
        return "Dilithium-5 (ML-DSA-87)"

    def generate_keypair(self) -> Optional[Tuple[bytes, bytes]]:
        try:
            from pqc.sign import dilithium5
            return dilithium5.keypair()
        except Exception as e:
            logger.error(f"[Dilithium5] keypair generation failed: {e}")
            return None

    def sign(self, message: bytes, secret_key: bytes) -> Optional[bytes]:
        try:
            from pqc.sign import dilithium5
            return dilithium5.sign(message, secret_key)
        except Exception as e:
            logger.error(f"[Dilithium5] sign failed: {e}")
            return None

    def verify(self, signature: bytes, message: bytes, public_key: bytes) -> bool:
        try:
            from pqc.sign import dilithium5
            dilithium5.verify(signature, message, public_key)
            return True
        except Exception:
            return False


# ─── Ed25519 Provider (Classical fallback) ───────────────────────────────────

class Ed25519Provider(CryptoProvider):
    """
    Ed25519 (classical ECDSA variant) — dev/test environments only.
    NOT quantum-resistant. Used only when PQC is unavailable.
    """

    def provider_id(self) -> str:
        return "ed25519"

    def algorithm_name(self) -> str:
        return "Ed25519 (classical — dev/test only)"

    def generate_keypair(self) -> Optional[Tuple[bytes, bytes]]:
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            from cryptography.hazmat.primitives.serialization import (
                Encoding, PublicFormat, PrivateFormat, NoEncryption
            )
            priv = Ed25519PrivateKey.generate()
            pub_bytes  = priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
            priv_bytes = priv.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
            return pub_bytes, priv_bytes
        except Exception as e:
            logger.error(f"[Ed25519] keypair generation failed: {e}")
            return None

    def sign(self, message: bytes, secret_key: bytes) -> Optional[bytes]:
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            priv = Ed25519PrivateKey.from_private_bytes(secret_key)
            return priv.sign(message)
        except Exception as e:
            logger.error(f"[Ed25519] sign failed: {e}")
            return None

    def verify(self, signature: bytes, message: bytes, public_key: bytes) -> bool:
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            pub = Ed25519PublicKey.from_public_bytes(public_key)
            pub.verify(signature, message)
            return True
        except Exception:
            return False


# ─── Provider Registry ───────────────────────────────────────────────────────

_REGISTRY: Dict[str, CryptoProvider] = {
    "dilithium3": Dilithium3Provider(),
    "dilithium5": Dilithium5Provider(),
    "ed25519":    Ed25519Provider(),
}


def _resolve_default_provider_id() -> str:
    """Backward-compatible: derive provider from PQC_SIGNING_LEVEL if ACTIVE_SIGNING_PROVIDER not set."""
    explicit = os.environ.get("ACTIVE_SIGNING_PROVIDER", "").strip().lower()
    if explicit and explicit in _REGISTRY:
        return explicit

    level = os.environ.get("PQC_SIGNING_LEVEL", "3").strip()
    if level == "5":
        return "dilithium5"
    return "dilithium3"


def get_active_provider() -> CryptoProvider:
    """Return the currently configured signing provider."""
    pid = _resolve_default_provider_id()
    provider = _REGISTRY.get(pid)
    if provider is None:
        logger.warning(f"[CryptoAgility] Unknown provider '{pid}', falling back to dilithium3.")
        return _REGISTRY["dilithium3"]
    logger.debug(f"[CryptoAgility] Active provider: {provider.algorithm_name()}")
    return provider


def get_provider(provider_id: str) -> Optional[CryptoProvider]:
    """Get a specific provider by ID — for verification of legacy receipts."""
    return _REGISTRY.get(provider_id)


def list_providers() -> Dict[str, Dict[str, Any]]:
    return {pid: p.get_info() for pid, p in _REGISTRY.items()}


def get_agility_status() -> Dict[str, Any]:
    active = get_active_provider()
    return {
        "active_provider":       active.provider_id(),
        "active_algorithm":      active.algorithm_name(),
        "env_var":               "ACTIVE_SIGNING_PROVIDER",
        "current_value":         os.environ.get("ACTIVE_SIGNING_PROVIDER", "(derived from PQC_SIGNING_LEVEL)"),
        "available_providers":   list(list_providers().keys()),
        "swap_requires_restart": True,
        "swap_requires_rewrite": False,
        "adr":                   "ADR-043",
        "note":                  "Change ACTIVE_SIGNING_PROVIDER env var to swap. No code changes needed.",
    }
