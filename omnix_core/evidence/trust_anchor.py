"""
OMNIX Trust Anchor Registry — ETA-001
======================================
ADR-085 / ETA-001 (External Trust and Defensibility, Stage 4)

Provides the canonical trust-anchor validation layer for all OMNIX receipt
verifiers. A cryptographically valid signature is necessary but NOT sufficient
for trust — the signature must have been produced by a key whose fingerprint
is pinned in the OMNIX trust anchor.

Trust Status Codes
------------------
  VALID_OMNIX_ISSUED            — Hash valid, PQC sig valid, key fingerprint
                                   matches the trusted OMNIX anchor. This is
                                   the only status that proves OMNIX issuance.

  VALID_SIGNATURE_UNTRUSTED_ISSUER — Hash valid, PQC signature mathematically
                                   valid, but embedded key fingerprint does NOT
                                   match the trusted OMNIX anchor. Receipt may
                                   have been signed by an attacker keypair.

  INVALID_SIGNATURE             — PQC signature present but mathematically
                                   invalid. Receipt is forged or tampered.

  UNKNOWN_KEY                   — Signature present but no public key available
                                   for verification — cannot determine issuer.

  DOWNGRADED_SHA_ONLY           — No PQC signature. Hash chain integrity is
                                   verified, but issuer cannot be proven.

Trust Anchor Sources (priority order)
--------------------------------------
  1. OMNIX_TRUSTED_KEY_FINGERPRINT env var — SHA-256 hex fingerprint of the
     trusted public key bytes (64-char hex). Highest priority.
  2. OMNIX_SIGNING_PUBLIC_KEY_B64 env var — the full base64 public key; its
     SHA-256 fingerprint is computed on first call and cached.
  3. /.well-known/omnix-public-key.json — fetched from omnixquantum.net
     (online environments only; result cached for TTL_SECONDS).
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import threading
import time
import urllib.request
from typing import Optional, Tuple

logger = logging.getLogger("OMNIX.TrustAnchor")

OMNIX_PUBKEY_WELL_KNOWN = "https://omnixquantum.net/.well-known/omnix-public-key.json"

TRUST_STATUS_VALID_OMNIX_ISSUED            = "VALID_OMNIX_ISSUED"
TRUST_STATUS_VALID_UNTRUSTED_ISSUER        = "VALID_SIGNATURE_UNTRUSTED_ISSUER"
TRUST_STATUS_INVALID_SIGNATURE             = "INVALID_SIGNATURE"
TRUST_STATUS_UNKNOWN_KEY                   = "UNKNOWN_KEY"
TRUST_STATUS_DOWNGRADED_SHA_ONLY           = "DOWNGRADED_SHA_ONLY"

TRUST_STATUS_DESCRIPTIONS: dict[str, str] = {
    TRUST_STATUS_VALID_OMNIX_ISSUED: (
        "Hash valid, PQC signature valid, key fingerprint matches the trusted OMNIX anchor. "
        "Receipt is proven to be issued by OMNIX Quantum Ltd."
    ),
    TRUST_STATUS_VALID_UNTRUSTED_ISSUER: (
        "Hash valid, PQC signature mathematically valid, but the embedded public key "
        "fingerprint does NOT match the trusted OMNIX anchor. Receipt may have been "
        "signed by an attacker keypair. DO NOT treat as OMNIX-issued."
    ),
    TRUST_STATUS_INVALID_SIGNATURE: (
        "PQC signature is present but mathematically invalid. Receipt is forged or "
        "has been tampered with after signing."
    ),
    TRUST_STATUS_UNKNOWN_KEY: (
        "Signature is present but no public key is available for verification. "
        "Issuer cannot be determined."
    ),
    TRUST_STATUS_DOWNGRADED_SHA_ONLY: (
        "No PQC signature on this receipt — hash-chain integrity mode only. "
        "Payload has not been tampered with, but cryptographic issuer proof is absent."
    ),
}

_TTL_SECONDS      = 300
_cached_fp: Optional[str] = None
_cached_fp_at: float = 0.0
_cache_lock = threading.Lock()


# ── Key fingerprint ────────────────────────────────────────────────────────────

def compute_key_fingerprint(pub_key_b64: str) -> str:
    """
    Compute SHA-256 fingerprint (hex) of the raw Dilithium-3 public key bytes.
    This is the canonical identity of a public key for OMNIX trust comparison.
    """
    raw = base64.b64decode(pub_key_b64)
    return hashlib.sha256(raw).hexdigest()


# ── Trusted fingerprint loading ────────────────────────────────────────────────

def _fetch_well_known_fingerprint(timeout: int = 4) -> Optional[str]:
    """Fetch trusted public key fingerprint from omnixquantum.net well-known."""
    try:
        req = urllib.request.Request(
            OMNIX_PUBKEY_WELL_KNOWN,
            headers={"User-Agent": "OMNIX-TrustAnchor/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            import json as _json
            data = _json.loads(resp.read().decode("utf-8"))
            key_b64 = data.get("key", {}).get("public_key_b64")
            if key_b64:
                return compute_key_fingerprint(key_b64)
            fp = data.get("key", {}).get("fingerprint_sha256")
            if fp and len(fp) == 64:
                return fp
    except Exception as exc:
        logger.debug("[TrustAnchor] well-known fetch failed: %s", exc)
    return None


def load_trusted_omnix_fingerprint(allow_well_known: bool = True) -> Optional[str]:
    """
    Return the trusted OMNIX public key fingerprint (SHA-256 hex, 64 chars).

    Priority:
      1. OMNIX_TRUSTED_KEY_FINGERPRINT env var (pre-computed, fastest)
      2. OMNIX_SIGNING_PUBLIC_KEY_B64 env var (compute fingerprint from key)
      3. /.well-known/omnix-public-key.json (network fetch, TTL-cached)

    Returns None if no trusted anchor is configured.
    """
    global _cached_fp, _cached_fp_at

    pinned = os.environ.get("OMNIX_TRUSTED_KEY_FINGERPRINT", "").strip()
    if pinned and len(pinned) == 64:
        return pinned

    pub_b64 = os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64", "").strip()
    if pub_b64:
        try:
            return compute_key_fingerprint(pub_b64)
        except Exception as exc:
            logger.warning("[TrustAnchor] Could not compute fingerprint from env key: %s", exc)

    if not allow_well_known:
        return None

    with _cache_lock:
        now = time.monotonic()
        if _cached_fp and (now - _cached_fp_at) < _TTL_SECONDS:
            return _cached_fp

    fp = _fetch_well_known_fingerprint()
    with _cache_lock:
        _cached_fp    = fp
        _cached_fp_at = time.monotonic()
    return fp


# ── Trust classification ───────────────────────────────────────────────────────

def classify_receipt(
    hash_valid:      bool,
    signature_valid: Optional[bool],
    sig_b64:         Optional[str],
    pub_key_b64:     Optional[str],
    sig_algo:        Optional[str],
    allow_well_known: bool = True,
) -> Tuple[str, bool, Optional[str]]:
    """
    Classify the trust status of a receipt given its cryptographic check results.

    Parameters
    ----------
    hash_valid      : True if SHA-256 content hash verified
    signature_valid : True/False if PQC verification ran; None if not attempted
    sig_b64         : base64-encoded signature field (None if absent)
    pub_key_b64     : base64-encoded embedded public key (None if absent)
    sig_algo        : signature algorithm label from the receipt
    allow_well_known: whether to allow a network call to the OMNIX well-known

    Returns
    -------
    (trust_status, issuer_trusted, key_fingerprint)
      trust_status   : one of the TRUST_STATUS_* constants
      issuer_trusted : True only when trust_status == VALID_OMNIX_ISSUED
      key_fingerprint: SHA-256 hex of the embedded public key, or None
    """
    key_fingerprint: Optional[str] = None
    if pub_key_b64:
        try:
            key_fingerprint = compute_key_fingerprint(pub_key_b64)
        except Exception:
            pass

    algo_lower = (sig_algo or "").lower()
    is_sha_only_algo = "sha" in algo_lower and "dilithium" not in algo_lower and "ml-dsa" not in algo_lower

    # ── Case 1: SHA-256 only receipt (no PQC signature) ────────────────────
    if not sig_b64 or is_sha_only_algo:
        if hash_valid:
            return TRUST_STATUS_DOWNGRADED_SHA_ONLY, False, key_fingerprint
        return TRUST_STATUS_INVALID_SIGNATURE, False, key_fingerprint

    # ── Case 2: Signature present, no key to verify against ────────────────
    if sig_b64 and not pub_key_b64:
        return TRUST_STATUS_UNKNOWN_KEY, False, key_fingerprint

    # ── Case 3: Signature mathematically invalid ────────────────────────────
    if signature_valid is False:
        return TRUST_STATUS_INVALID_SIGNATURE, False, key_fingerprint

    # ── Case 4: PQC signature valid — compare key fingerprint to anchor ─────
    if signature_valid is True:
        if not key_fingerprint:
            return TRUST_STATUS_UNKNOWN_KEY, False, key_fingerprint

        trusted_fp = load_trusted_omnix_fingerprint(allow_well_known=allow_well_known)
        if trusted_fp:
            if key_fingerprint == trusted_fp:
                return TRUST_STATUS_VALID_OMNIX_ISSUED, True, key_fingerprint
            else:
                return TRUST_STATUS_VALID_UNTRUSTED_ISSUER, False, key_fingerprint
        else:
            logger.warning(
                "[TrustAnchor] No trusted anchor configured — cannot confirm OMNIX issuance. "
                "Set OMNIX_SIGNING_PUBLIC_KEY_B64 or OMNIX_TRUSTED_KEY_FINGERPRINT."
            )
            return TRUST_STATUS_VALID_UNTRUSTED_ISSUER, False, key_fingerprint

    # ── Case 5: PQC library unavailable or signature check not attempted ─────
    if sig_b64 and not pub_key_b64:
        return TRUST_STATUS_UNKNOWN_KEY, False, key_fingerprint

    return TRUST_STATUS_UNKNOWN_KEY, False, key_fingerprint


# ── Convenience helper ─────────────────────────────────────────────────────────

def build_trust_anchor_block(
    hash_valid:      bool,
    signature_valid: Optional[bool],
    sig_b64:         Optional[str],
    pub_key_b64:     Optional[str],
    sig_algo:        Optional[str],
    allow_well_known: bool = True,
) -> dict:
    """
    Return a serializable trust anchor block suitable for API responses.

    Includes: trust_status, issuer_trusted, key_fingerprint,
              trusted_anchor_fingerprint, trust_status_description.
    """
    trust_status, issuer_trusted, key_fp = classify_receipt(
        hash_valid=hash_valid,
        signature_valid=signature_valid,
        sig_b64=sig_b64,
        pub_key_b64=pub_key_b64,
        sig_algo=sig_algo,
        allow_well_known=allow_well_known,
    )
    trusted_fp = load_trusted_omnix_fingerprint(allow_well_known=allow_well_known)
    return {
        "trust_status":               trust_status,
        "issuer_trusted":             issuer_trusted,
        "key_fingerprint":            key_fp,
        "trusted_anchor_fingerprint": trusted_fp,
        "anchor_source":              _describe_anchor_source(),
        "trust_status_description":   TRUST_STATUS_DESCRIPTIONS.get(trust_status, ""),
    }


def _describe_anchor_source() -> str:
    if os.environ.get("OMNIX_TRUSTED_KEY_FINGERPRINT", "").strip():
        return "env:OMNIX_TRUSTED_KEY_FINGERPRINT"
    if os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64", "").strip():
        return "env:OMNIX_SIGNING_PUBLIC_KEY_B64 (computed)"
    return "/.well-known/omnix-public-key.json"
