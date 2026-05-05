"""
OMNIX Key Generation Utility — ADR-078

Management command that generates a Dilithium-3 keypair and prints the
base64-encoded keys for use as environment variables.

Usage:
    python -m omnix_core.tools.key_gen

Output (safe to copy to .env / Railway):
    OMNIX_SIGNING_SECRET_KEY_B64=<base64>
    OMNIX_SIGNING_PUBLIC_KEY_B64=<base64>

Security:
    Secret key material is printed ONLY to stdout — not logged.
    Redirect stdout to a secure location; never commit output to source control.

Harold Nunes — OMNIX QUANTUM LTD
ADR-078 — April 2026
"""
from __future__ import annotations

import base64
import hashlib
import sys


def generate_and_print() -> None:
    """Generate Dilithium-3 keypair and print env var assignments to stdout."""
    try:
        from omnix_core.security.crypto_providers import get_active_provider
        provider = get_active_provider()
    except Exception as exc:
        print(f"ERROR: Cannot load crypto provider: {exc}", file=sys.stderr)
        sys.exit(1)

    kp = provider.generate_keypair()
    if kp is None:
        print("ERROR: generate_keypair() returned None — PQC library not available.", file=sys.stderr)
        sys.exit(1)

    pk_bytes, sk_bytes = kp[0], kp[1]

    # Self-test
    test_msg = b"OMNIX-KEY-SELFTEST"
    sig = provider.sign(test_msg, sk_bytes)
    if sig is None or not provider.verify(sig, test_msg, pk_bytes):
        print("ERROR: Key self-test failed — keypair is invalid.", file=sys.stderr)
        sys.exit(1)

    sk_b64 = base64.b64encode(sk_bytes).decode()
    pk_b64 = provider.serialize_public_key(pk_bytes)
    key_id  = hashlib.sha256(pk_bytes).hexdigest()[:16]

    sep = "─" * 72
    print(sep)
    print(f"OMNIX Signing Keypair — {provider.algorithm_name()}")
    print(f"key_id (public fingerprint): {key_id}")
    print(sep)
    print()
    print("# Copy both variables to your environment (Railway / .env):")
    print()
    print(f"OMNIX_SIGNING_SECRET_KEY_B64={sk_b64}")
    print()
    print(f"OMNIX_SIGNING_PUBLIC_KEY_B64={pk_b64}")
    print()
    print(sep)
    print("WARNING: Keep OMNIX_SIGNING_SECRET_KEY_B64 secret at all times.")
    print("OMNIX_SIGNING_PUBLIC_KEY_B64 is safe to distribute to verifiers.")
    print(f"Self-test: PASSED — {provider.algorithm_name()}")
    print(sep)


if __name__ == "__main__":
    generate_and_print()
