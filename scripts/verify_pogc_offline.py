#!/usr/bin/env python3
"""
OMNIX Proof of Governance — Offline Certificate Verifier v2.0
ADR-186 · ADR-189 · ADR-205 · PoGR-INV-003 · OMNIX-POGR-2026-001

Verify any PoG Certificate entirely offline — no OMNIX account,
no API key, no network access beyond the initial download.

Usage:
    # Download and verify in one step (requires network once):
    python verify_pogc_offline.py POGC-A3F2B1C4D5E6F7A8

    # Verify a previously downloaded certificate file:
    python verify_pogc_offline.py --file certificate.json

    # Full PQC cryptographic verification (pass platform public key):
    python verify_pogc_offline.py --file cert.json --platform-key <base64>

    # Download only (save for later offline verification):
    python verify_pogc_offline.py POGC-A3F2B1C4D5E6F7A8 --download-only

    # Machine-readable JSON output:
    python verify_pogc_offline.py --file cert.json --json

Requirements:
    Python 3.8+  — no external dependencies for core verification (hash + status).
    oqs-python   — OPTIONAL, required for ML-DSA-65 PQC cryptographic verification:
                   pip install oqs-python

What this verifier checks:
    [1] Content hash integrity  — SHA3-256 over canonical fields matches stored hash
    [2] Certificate status      — ACTIVE / EXPIRED / REVOKED (v2: cryptographically bound)
    [3] TTL validity            — certificate has not expired
    [4] PQC signature           — ML-DSA-65 (FIPS 204) cryptographic verification
                                  (requires oqs-python + platform public key)
    [5] Issuer identity         — certificate was issued by OMNIX QUANTUM LTD
    [6] Mandate certification   — MANDATE-BOUND | MANDATE-ALIGNED | UNCERTIFIED
    [7] Canonical version       — v1 warning / v2 full status binding

ADR-205 — canonical_version 2: status + revoked_at are cryptographically bound.
           canonical_version 1: status is NOT bound — always verify live for revocation.

Exit codes:
    0 — All hard checks passed. Certificate is VALID (warnings possible).
    1 — One or more checks failed. Certificate is INVALID.
    2 — Usage error or download failure.

OMNIX QUANTUM LTD — Harold Nunes — May 2026
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_ENDPOINT  = "https://omnixquantum.net"
EXPECTED_ISSUER   = "OMNIX QUANTUM LTD"
VERSION           = "2.0.0"
ADR_REF           = "ADR-186 · ADR-189 · ADR-205"

# ADR-205: v1 legacy fields (10), v2 includes status + revoked_at (12)
CANONICAL_V1 = [
    "pogc_id", "session_id", "ctchc_seal_hash",
    "issuer", "subject_org", "agent_id",
    "compliance_tier", "mandate_certification",
    "issued_at", "expires_at",
]
CANONICAL_V2 = CANONICAL_V1 + ["status", "revoked_at"]

# ── ANSI colours (disabled on Windows or when not a TTY) ──────────────────────

def _colour_supported() -> bool:
    import os
    return sys.stdout.isatty() and os.name != "nt"

_USE_COLOUR = _colour_supported()

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOUR else text

GREEN  = lambda t: _c("32",   t)
RED    = lambda t: _c("31",   t)
YELLOW = lambda t: _c("33",   t)
CYAN   = lambda t: _c("36",   t)
BOLD   = lambda t: _c("1",    t)
DIM    = lambda t: _c("2",    t)
GOLD   = lambda t: _c("33;1", t)

# ── Core verification ──────────────────────────────────────────────────────────

def _detect_canonical_version(cert: Dict[str, Any]) -> int:
    """
    Detect canonical schema version from the certificate.
    ADR-205: canonical_version 2 includes status + revoked_at in the hash.
    """
    # Explicit field in cert (new certs from v1.1+ server)
    v = cert.get("canonical_version") or cert.get(
        "_offline_verification", {}).get("canonical_version")
    if v is not None:
        try:
            return int(v)
        except (TypeError, ValueError):
            pass
    return 1  # safe default: treat as legacy v1


def _compute_content_hash(cert: Dict[str, Any], version: int) -> str:
    """
    Recompute SHA3-256 over the canonical fields subset.
    Uses the correct field set for the given canonical_version.
    ADR-205.
    """
    fields = CANONICAL_V2 if version >= 2 else CANONICAL_V1
    canonical: Dict[str, Any] = {}
    for k in fields:
        val = cert.get(k)
        # Normalise: datetimes are already strings in exported JSON
        canonical[k] = val
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    return "sha3-256:" + hashlib.sha3_256(payload).hexdigest()


def _verify_pqc_signature(
    cert: Dict[str, Any],
    canonical: Dict[str, Any],
    platform_key_b64: Optional[str],
) -> Tuple[Optional[bool], str]:
    """
    Verify the ML-DSA-65 signature cryptographically.
    ADR-205 — POGR-SEC-001 fix.

    platform_key_b64 priority:
      1. --platform-key argument (explicit override)
      2. _offline_verification.platform_public_key_b64 (embedded in export)
      3. Not available → warning

    Returns:
        (True,  "✓ ML-DSA-65 signature cryptographically verified (FIPS 204)")
        (False, "✗ ML-DSA-65 signature INVALID — <reason>")
        (None,  "⚠ <warning>")  — warning, not a hard failure
    """
    sig_str = cert.get("pqc_signature", "")

    if not sig_str:
        return (False, "PQC signature absent")

    if sig_str.startswith("STUB-"):
        return (None,
                "Signature is a development stub — not production ML-DSA-65. "
                "Re-sign with OMNIX_SIGNING_SECRET_KEY_B64 in production.")

    if not sig_str.startswith("ML-DSA-65:"):
        return (None, f"Signature format unrecognised: {sig_str[:30]}…")

    # Resolve platform public key
    pk_b64 = platform_key_b64
    if not pk_b64:
        pk_b64 = (cert.get("_offline_verification") or {}).get("platform_public_key_b64")

    if not pk_b64:
        return (None,
                "Platform public key not provided — PQC cryptographic verification skipped.\n"
                "  Hash integrity is still enforced.\n"
                "  For full cryptographic verification:\n"
                "    python verify_pogc_offline.py --file cert.json --platform-key <base64>\n"
                "  Or use a cert exported from a production server (includes embedded key).")

    # Attempt oqs import
    try:
        from oqs import Signature as OQSSig  # type: ignore
    except ImportError:
        return (None,
                "oqs-python not installed — PQC cryptographic verification skipped.\n"
                "  Install: pip install oqs-python\n"
                "  Hash integrity is still enforced.")

    try:
        pk_bytes  = base64.b64decode(pk_b64)
        payload   = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
        sig_bytes = bytes.fromhex(sig_str.removeprefix("ML-DSA-65:"))
        verifier  = OQSSig("ML-DSA-65")
        verifier.verify(payload, sig_bytes, pk_bytes)
        return (True, "ML-DSA-65 signature cryptographically verified (FIPS 204 / NIST 2024)")
    except Exception as exc:
        return (False, f"ML-DSA-65 signature INVALID — {exc}")


def verify_certificate(
    cert: Dict[str, Any],
    platform_key_b64: Optional[str] = None,
) -> Tuple[bool, List[Tuple[str, Optional[bool], str]]]:
    """
    Run all offline verification checks against a certificate dict.
    ADR-205: canonical_version-aware, PQC cryptographic verification.

    Returns:
        (overall_valid: bool,
         checks: list of (label, passed, detail))
         passed: True = OK, False = FAIL, None = WARNING
    """
    checks: List[Tuple[str, Optional[bool], str]] = []
    now = datetime.now(timezone.utc)

    # Detect canonical schema version (ADR-205)
    canon_version = _detect_canonical_version(cert)

    # ── [1] Content hash integrity ─────────────────────────────────────────
    stored_hash   = cert.get("content_hash", "")
    computed_hash = _compute_content_hash(cert, canon_version)
    hash_ok       = stored_hash == computed_hash

    if hash_ok:
        checks.append(("Content hash (SHA3-256)", True,
                        f"Verified — {stored_hash[:32]}…"))
    else:
        checks.append(("Content hash (SHA3-256)", False,
                        f"MISMATCH\n"
                        f"  Stored:   {stored_hash}\n"
                        f"  Expected: {computed_hash}\n"
                        f"  → One or more canonical fields have been altered "
                        f"(canonical_version={canon_version})."))

    # ── [2] Certificate status ─────────────────────────────────────────────
    status    = cert.get("status", "UNKNOWN")
    status_ok = status == "ACTIVE"

    if status == "ACTIVE":
        checks.append(("Certificate status", True,
                        f"ACTIVE (canonical_version={canon_version})"))
    elif status == "REVOKED":
        reason = cert.get("revocation_reason") or "no reason provided"
        checks.append(("Certificate status", False,
                        f"REVOKED — {reason}"))
    elif status == "EXPIRED":
        checks.append(("Certificate status", False, "EXPIRED"))
    else:
        checks.append(("Certificate status", False,
                        f"UNKNOWN status: {status}"))

    # ── [3] TTL validity ───────────────────────────────────────────────────
    expires_str = cert.get("expires_at", "")
    ttl_ok      = False
    try:
        expires_str_n = str(expires_str).replace("Z", "+00:00")
        expires_at    = datetime.fromisoformat(expires_str_n)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now < expires_at:
            days_left = (expires_at - now).days
            ttl_ok    = True
            checks.append(("TTL validity", True,
                            f"Not expired — {days_left} days remaining "
                            f"(expires {expires_at.strftime('%Y-%m-%d')})"))
        else:
            checks.append(("TTL validity", False,
                            f"Expired on {expires_at.strftime('%Y-%m-%d %H:%M UTC')}"))
    except Exception as exc:
        checks.append(("TTL validity", False, f"Cannot parse expires_at: {exc}"))

    # ── [4] PQC signature (ML-DSA-65 cryptographic) ───────────────────────
    # Build canonical dict for signature verification (same as issuance)
    fields = CANONICAL_V2 if canon_version >= 2 else CANONICAL_V1
    canonical = {k: cert.get(k) for k in fields}

    pqc_ok, pqc_msg = _verify_pqc_signature(cert, canonical, platform_key_b64)
    checks.append(("PQC signature (ML-DSA-65)", pqc_ok, pqc_msg))

    # ── [5] Issuer identity ───────────────────────────────────────────────
    issuer    = cert.get("issuer", "")
    issuer_ok = issuer == EXPECTED_ISSUER
    checks.append(("Issuer identity", issuer_ok,
                    issuer if issuer_ok
                    else f"Expected '{EXPECTED_ISSUER}', got '{issuer}'"))

    # ── [6] Mandate certification ─────────────────────────────────────────
    mandate = cert.get("mandate_certification", "UNCERTIFIED")
    if mandate == "MANDATE-BOUND":
        checks.append(("Mandate certification", True,
                        "MANDATE-BOUND — pristine fidelity (MIVP-INV-008 · ADR-194)"))
    elif mandate == "MANDATE-ALIGNED":
        checks.append(("Mandate certification", True,
                        "MANDATE-ALIGNED — mission-aligned (MIVP-INV-009 · ADR-194)"))
    else:
        checks.append(("Mandate certification", None,
                        "UNCERTIFIED — mandate verification not performed"))

    # ── [7] Canonical version status binding (ADR-205) ────────────────────
    if canon_version >= 2:
        checks.append(("Canonical schema version", True,
                        "v2 — status and revoked_at are cryptographically bound "
                        "to the content_hash and ML-DSA-65 signature"))
    else:
        checks.append(("Canonical schema version", None,
                        f"v{canon_version} (legacy) — fields 'status' and 'revoked_at' are NOT "
                        f"cryptographically bound to this certificate's hash or signature.\n"
                        f"  SECURITY: A revoked certificate's exported file still shows ACTIVE.\n"
                        f"  Always verify revocation in real-time at:\n"
                        f"  {DEFAULT_ENDPOINT}/v1/pogr/verify/{cert.get('pogc_id', '<id>')}"))

    # ── Overall result ────────────────────────────────────────────────────
    # FAIL = any check with passed=False; warnings (None) are non-blocking.
    overall_valid = all(passed is not False for _, passed, _ in checks)

    return overall_valid, checks


# ── Download ──────────────────────────────────────────────────────────────────

def download_certificate(pogc_id: str, endpoint: str) -> Dict[str, Any]:
    """
    Download a certificate from the public PoGR API.
    Uses /v1/pogr/certificate/<id> (full JSON with export metadata).
    PoGR-INV-003: no authentication required.
    """
    url = f"{endpoint.rstrip('/')}/v1/pogr/certificate/{pogc_id}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"OMNIX-OfflineVerifier/{VERSION}",
            "Accept":     "application/json",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status != 200:
                raise SystemExit(
                    f"{RED('Error')}: Registry returned HTTP {resp.status} for {pogc_id}")
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise SystemExit(
                f"{RED('Not found')}: No certificate '{pogc_id}' in the registry.")
        raise SystemExit(f"{RED('HTTP error')}: {exc}")
    except urllib.error.URLError as exc:
        raise SystemExit(
            f"{RED('Network error')}: Cannot reach {endpoint}\n"
            f"  {exc.reason}\n"
            f"  Tip: Use --file with a previously downloaded certificate for offline verification.")


# ── Rendering ─────────────────────────────────────────────────────────────────

def _print_banner():
    print()
    print(GOLD("  ⬡  OMNIX Proof of Governance — Offline Certificate Verifier"))
    print(DIM(f"     {ADR_REF} · PoGR-INV-003 · v{VERSION}"))
    print()


def _print_cert_summary(cert: Dict[str, Any]):
    pogc_id       = cert.get("pogc_id", "—")
    org           = cert.get("subject_org", "—")
    issued        = str(cert.get("issued_at", "—"))[:19].replace("T", " ")
    expires       = str(cert.get("expires_at", "—"))[:10]
    tier          = cert.get("compliance_tier", "—")
    mandate       = cert.get("mandate_certification", "UNCERTIFIED")
    turns         = cert.get("turn_count", "—")
    alg           = (cert.get("pqc_algorithm") or "ml-dsa-65").upper()
    canon_version = _detect_canonical_version(cert)
    has_pk        = bool(
        (cert.get("_offline_verification") or {}).get("platform_public_key_b64"))

    print(BOLD("  Certificate"))
    print(f"  {'ID':<24}  {CYAN(pogc_id)}")
    print(f"  {'Organization':<24}  {org}")
    print(f"  {'Compliance tier':<24}  {tier}")
    print(f"  {'Mandate certification':<24}  "
          f"{GOLD(mandate) if mandate != 'UNCERTIFIED' else DIM(mandate)}")
    print(f"  {'Session turns':<24}  {turns}")
    print(f"  {'Algorithm':<24}  {alg} · FIPS 204")
    print(f"  {'Canonical version':<24}  "
          f"{'v' + str(canon_version) + ' (' + ('status bound ✓' if canon_version >= 2 else 'status NOT bound ⚠') + ')'}")
    print(f"  {'Platform key embedded':<24}  {'Yes ✓' if has_pk else 'No (pass --platform-key for PQC verify)'}")
    print(f"  {'Issued':<24}  {issued} UTC")
    print(f"  {'Expires':<24}  {expires}")
    print()


def _print_checks(checks: List[Tuple[str, Optional[bool], str]]):
    print(BOLD("  Verification Checks"))
    for label, passed, detail in checks:
        if passed is True:
            icon = GREEN("  ✓")
            clr  = GREEN
        elif passed is False:
            icon = RED("  ✗")
            clr  = RED
        else:
            icon = YELLOW("  ⚠")
            clr  = YELLOW

        print(f"{icon}  {clr(label)}")
        for line in detail.split("\n"):
            print(f"       {DIM(line)}")
    print()


def _print_verdict(valid: bool, pogc_id: str):
    if valid:
        print("  " + "─" * 58)
        print()
        print(f"  {GREEN(BOLD('✅  CERTIFICATE VALID'))}")
        print(f"  {DIM('This governance certificate passed all offline verification checks.')}")
        print(f"  {DIM('The AI session it references was governed correctly.')}")
    else:
        print("  " + "─" * 58)
        print()
        print(f"  {RED(BOLD('❌  CERTIFICATE INVALID'))}")
        print(f"  {DIM('One or more verification checks failed — see details above.')}")
    print()
    print(f"  {DIM('Verified at')}  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"  {DIM('Public URL')}   {DEFAULT_ENDPOINT}/pogr/verify/{pogc_id}")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="verify_pogc_offline.py",
        description=(
            "OMNIX Proof of Governance — Offline Certificate Verifier v2.0.\n"
            "Verify any PoGC with no OMNIX account, no API key, no trust.\n"
            "ADR-205: canonical_version 2 binds status+revoked_at to the signature.\n"
            "PoGR-INV-003 · ADR-186 · ADR-189 · ADR-205 · OMNIX QUANTUM LTD"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Download and verify (hash only):\n"
            "  python verify_pogc_offline.py POGC-A3F2B1C4D5E6F7A8\n\n"
            "  # Verify saved file with full PQC cryptographic check:\n"
            "  python verify_pogc_offline.py --file certificate.json --platform-key <base64>\n\n"
            "  # Export from server (includes embedded key) then verify:\n"
            "  curl https://omnixquantum.net/v1/pogr/certificate/POGC-.../export > cert.json\n"
            "  python verify_pogc_offline.py --file cert.json\n\n"
            "  # Machine-readable JSON output:\n"
            "  python verify_pogc_offline.py --file cert.json --json\n"
        )
    )
    parser.add_argument(
        "pogc_id", nargs="?",
        help="PoG Certificate ID (e.g. POGC-A3F2B1C4D5E6F7A8)"
    )
    parser.add_argument(
        "--file", "-f", metavar="PATH",
        help="Path to a previously downloaded / exported certificate JSON file"
    )
    parser.add_argument(
        "--endpoint", metavar="URL", default=DEFAULT_ENDPOINT,
        help=f"Registry API base URL (default: {DEFAULT_ENDPOINT})"
    )
    parser.add_argument(
        "--platform-key", metavar="BASE64",
        help=(
            "Base64-encoded ML-DSA-65 platform public key for PQC cryptographic verification. "
            "Obtain from: GET /v1/pogr/manifest (platform_key.configured field) or "
            "from the _offline_verification.platform_public_key_b64 field in an exported cert."
        )
    )
    parser.add_argument(
        "--download-only", action="store_true",
        help="Download the certificate JSON and save it, without verifying"
    )
    parser.add_argument(
        "--output", "-o", metavar="PATH",
        help="Save downloaded certificate JSON to this file"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output results as machine-readable JSON (exit 0=valid, 1=invalid)"
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {VERSION}"
    )

    args = parser.parse_args()

    if not args.pogc_id and not args.file:
        parser.error("Provide a POGC-ID or use --file PATH")

    # ── Load certificate ───────────────────────────────────────────────────
    if args.file:
        try:
            with open(args.file) as fh:
                cert = json.load(fh)
        except FileNotFoundError:
            print(f"{RED('Error')}: File not found: {args.file}", file=sys.stderr)
            sys.exit(2)
        except json.JSONDecodeError as exc:
            print(f"{RED('Error')}: Invalid JSON in {args.file}: {exc}", file=sys.stderr)
            sys.exit(2)
        pogc_id = cert.get("pogc_id", args.file)
    else:
        pogc_id = args.pogc_id
        cert    = download_certificate(pogc_id, args.endpoint)

        out_path = args.output or (f"{pogc_id}.json" if args.download_only else None)
        if out_path:
            with open(out_path, "w") as fh:
                json.dump(cert, fh, indent=2, default=str)
            print(f"{GREEN('Saved')}: {out_path}")

        if args.download_only:
            print(f"\nCertificate downloaded. To verify offline:\n"
                  f"  python verify_pogc_offline.py --file {out_path or pogc_id + '.json'}")
            sys.exit(0)

    # ── Verify ────────────────────────────────────────────────────────────
    platform_key_b64 = args.platform_key or None
    valid, checks = verify_certificate(cert, platform_key_b64=platform_key_b64)

    if args.json:
        result = {
            "valid":      valid,
            "pogc_id":    pogc_id,
            "canonical_version": _detect_canonical_version(cert),
            "checks":     [
                {"label": lbl, "passed": p, "detail": det}
                for lbl, p, det in checks
            ],
            "verified_at":   datetime.now(timezone.utc).isoformat(),
            "verifier":      f"OMNIX-OfflineVerifier/{VERSION}",
            "adr_ref":       ADR_REF,
        }
        print(json.dumps(result, indent=2))
    else:
        _print_banner()
        _print_cert_summary(cert)
        _print_checks(checks)
        _print_verdict(valid, pogc_id)

    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
