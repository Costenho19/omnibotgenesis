"""
OMNIX — Payload Key Manager (ISR-021)
ISR-2026-Q2-001 · Payload Encryption Key Survivability

Problem:
  A single PAYLOAD_ENCRYPTION_KEY with no versioning means a key loss makes
  all historical encrypted_payload fields in decision_receipts permanently
  irrecoverable. MiFID II requires signal-level explainability.

Solution:
  Versioned key registry. Every encrypted payload is prefixed with
  "omnix-pek-v{N}:" to identify which key version was used. Decryption
  tries the version from the prefix, then falls back through all
  registered versions.

Environment variables:
  PAYLOAD_ENCRYPTION_KEY           → mapped to version "v1" (legacy compat)
  PAYLOAD_ENCRYPTION_KEY_v2        → version "v2"
  PAYLOAD_ENCRYPTION_KEY_CURRENT   → active version id, e.g. "v2" (default: "v1")

Key rotation procedure (zero-downtime):
  1. Generate new Fernet key: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  2. Set PAYLOAD_ENCRYPTION_KEY_v2 = <new_key> in Railway + escrow backup
  3. Set PAYLOAD_ENCRYPTION_KEY_CURRENT = "v2" in Railway
  4. Old PAYLOAD_ENCRYPTION_KEY (v1) remains set — needed to decrypt historical receipts
  5. All new receipts use v2; old receipts decrypt with v1 via prefix routing

ADR: ISR-021 remediation
"""
from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger("OMNIX.Evidence.PayloadKeyManager")

VERSION_PREFIX = "omnix-pek-"
LEGACY_KEY_ENV = "PAYLOAD_ENCRYPTION_KEY"
CURRENT_VERSION_ENV = "PAYLOAD_ENCRYPTION_KEY_CURRENT"
DEFAULT_VERSION = "v1"


def _load_key(version: str) -> Optional[bytes]:
    """Load Fernet key bytes for the given version."""
    if version == "v1":
        raw = os.environ.get(LEGACY_KEY_ENV, "")
    else:
        raw = os.environ.get(f"PAYLOAD_ENCRYPTION_KEY_{version}", "")
    if not raw:
        return None
    return raw.encode() if isinstance(raw, str) else raw


def _all_known_versions() -> list[str]:
    """Return all version ids for which an env var exists, ordered v1 first."""
    versions: list[str] = []
    if os.environ.get(LEGACY_KEY_ENV):
        versions.append("v1")
    n = 2
    while True:
        if os.environ.get(f"PAYLOAD_ENCRYPTION_KEY_v{n}"):
            versions.append(f"v{n}")
            n += 1
        else:
            break
    return versions or ["v1"]


class PayloadKeyManager:
    """
    Versioned Fernet key manager for decision_receipt encrypted payloads.

    Usage:
        mgr = PayloadKeyManager()
        token = mgr.encrypt(json_string)  # returns "omnix-pek-v1:<fernet_token>"
        plain = mgr.decrypt(token)        # auto-selects key by prefix
    """

    def __init__(self) -> None:
        try:
            from cryptography.fernet import Fernet
            self._Fernet = Fernet
            self._available = True
        except ImportError:
            self._Fernet = None
            self._available = False
            logger.warning("[PayloadKeyManager] cryptography not available — encryption disabled")

    @property
    def current_version(self) -> str:
        return os.environ.get(CURRENT_VERSION_ENV, DEFAULT_VERSION).strip()

    @property
    def is_available(self) -> bool:
        return self._available and bool(_load_key(self.current_version))

    def encrypt(self, plaintext: str) -> Optional[str]:
        """
        Encrypt plaintext and return a versioned token.
        Returns None if key is unavailable (governance continues without encryption).
        """
        if not self._available:
            return None
        version = self.current_version
        key = _load_key(version)
        if not key:
            logger.warning(
                f"[PayloadKeyManager][ISR-021] Encryption key '{version}' not found in env — "
                f"payload will not be encrypted. Set {LEGACY_KEY_ENV} or "
                f"PAYLOAD_ENCRYPTION_KEY_{version}."
            )
            return None
        try:
            f = self._Fernet(key)
            token = f.encrypt(plaintext.encode()).decode()
            return f"{VERSION_PREFIX}{version}:{token}"
        except Exception as exc:
            logger.warning(f"[PayloadKeyManager] Encryption failed: {exc}")
            return None

    def decrypt(self, versioned_token: str) -> Optional[str]:
        """
        Decrypt a versioned token. Auto-selects key based on prefix.
        Falls back through all known key versions on prefix mismatch.
        Returns None if decryption fails with all available keys.
        """
        if not self._available or not versioned_token:
            return None
        try:
            version, raw_token = _parse_version(versioned_token)
            key = _load_key(version)
            if key:
                try:
                    f = self._Fernet(key)
                    return f.decrypt(raw_token.encode()).decode()
                except Exception:
                    pass
            for fallback_version in _all_known_versions():
                if fallback_version == version:
                    continue
                fkey = _load_key(fallback_version)
                if not fkey:
                    continue
                try:
                    f = self._Fernet(fkey)
                    result = f.decrypt(raw_token.encode()).decode()
                    logger.info(
                        f"[PayloadKeyManager] Decrypted with fallback version '{fallback_version}' "
                        f"(token version was '{version}')"
                    )
                    return result
                except Exception:
                    continue
            logger.error(
                f"[PayloadKeyManager][ISR-021] Decryption failed with all available key versions. "
                f"Token version='{version}'. Available versions: {_all_known_versions()}. "
                f"If this is a historical receipt, ensure the correct key version is set in env."
            )
            return None
        except Exception as exc:
            logger.error(f"[PayloadKeyManager] Decrypt error: {exc}")
            return None

    def active_version_id(self) -> str:
        return self.current_version

    def list_available_versions(self) -> list[str]:
        return _all_known_versions()


def _parse_version(versioned_token: str) -> tuple[str, str]:
    """
    Parse "omnix-pek-v1:<fernet_token>" → ("v1", "<fernet_token>")
    For legacy tokens without prefix, assume "v1".
    """
    if versioned_token.startswith(VERSION_PREFIX):
        rest = versioned_token[len(VERSION_PREFIX):]
        colon_idx = rest.index(":")
        version = rest[:colon_idx]
        token = rest[colon_idx + 1:]
        return version, token
    return "v1", versioned_token


_default_manager: Optional[PayloadKeyManager] = None


def get_payload_key_manager() -> PayloadKeyManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = PayloadKeyManager()
    return _default_manager
