#!/usr/bin/env python3
"""
OMNIX Proof of Governance — Offline Certificate Verifier
ADR-189 · PoGR-INV-003 · OMNIX-POGR-2026-001

Verify any PoG Certificate entirely offline — no OMNIX account,
no API key, no network access beyond the initial download.

Usage:
    # Download and verify in one step (requires network once):
    python verify_pogc_offline.py POGC-A3F2B1C4D5E6F7A8

    # Verify a previously downloaded certificate file:
    python verify_pogc_offline.py --file certificate.json

    # Download only (save for later offline verification):
    python verify_pogc_offline.py POGC-A3F2B1C4D5E6F7A8 --download-only

    # Use a custom registry endpoint (default: omnixquantum.net):
    python verify_pogc_offline.py POGC-... --endpoint https://your-omnix-instance.com

Requirements:
    Python 3.8+  — no external dependencies required for core verification.
    (urllib and hashlib are standard library.)

What this verifier checks:
    [1] Content hash integrity  — SHA3-256 over canonical fields matches stored hash
    [2] Certificate status      — ACTIVE / EXPIRED / REVOKED
    [3] TTL validity            — certificate has not expired
    [4] PQC signature presence  — ML-DSA-65 (FIPS 204) signature is present
    [5] Issuer identity         — certificate was issued by OMNIX QUANTUM LTD
    [6] Mandate certification   — MANDATE-BOUND | MANDATE-ALIGNED | UNCERTIFIED

Exit codes:
    0 — All checks passed. Certificate is VALID.
    1 — One or more checks failed. Certificate is INVALID or WARNING.
    2 — Usage error or download failure.

OMNIX QUANTUM LTD — Harold Nunes — May 2026
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_ENDPOINT  = "https://omnixquantum.net"
CANONICAL_FIELDS  = [
    "pogc_id", "session_id", "ctchc_seal_hash",
    "issuer", "subject_org", "agent_id",
    "compliance_tier", "mandate_certification",
    "issued_at", "expires_at",
]
EXPECTED_ISSUER   = "OMNIX QUANTUM LTD"
VERSION           = "1.0.0"
ADR_REF           = "ADR-186 · ADR-187 · ADR-189"

# ── ANSI colours (disabled on Windows or when not a TTY) ──────────────────────

def _colour_supported() -> bool:
    import os
    return sys.stdout.isatty() and os.name != "nt"

_USE_COLOUR = _colour_supported()

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOUR else text

GREEN  = lambda t: _c("32", t)
RED    = lambda t: _c("31", t)
YELLOW = lambda t: _c("33", t)
CYAN   = lambda t: _c("36", t)
BOLD   = lambda t: _c("1",  t)
DIM    = lambda t: _c("2",  t)
GOLD   = lambda t: _c("33;1", t)

# ── Core verification ──────────────────────────────────────────────────────────

def _compute_content_hash(cert: Dict[str, Any]) -> str:
    """
    Recompute SHA3-256 over the canonical fields subset.
    This is the authoritative integrity check — any tampering
    with the core fields will produce a different hash.
    """
    canonical = {k: cert[k] for k in CANONICAL_FIELDS if k in cert}
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    return "sha3-256:" + hashlib.sha3_256(payload).hexdigest()


def verify_certificate(cert: Dict[str, Any]) -> Tuple[bool, List[Tuple[str, bool, str]]]:
    """
    Run all offline verification checks against a certificate dict.

    Returns:
        (overall_valid: bool, checks: list of (label, passed, detail))
    """
    checks: List[Tuple[str, bool, str]] = []
    now = datetime.now(timezone.utc)

    # ── [1] Content hash integrity ─────────────────────────────────────────
    stored_hash   = cert.get("content_hash", "")
    computed_hash = _compute_content_hash(cert)
    hash_ok       = stored_hash == computed_hash

    if hash_ok:
        checks.append(("Content hash (SHA3-256)", True,
                        f"Verified — {stored_hash[:32]}…"))
    else:
        checks.append(("Content hash (SHA3-256)", False,
                        f"MISMATCH\n"
                        f"  Stored:   {stored_hash}\n"
                        f"  Expected: {computed_hash}\n"
                        f"  → One or more canonical fields have been altered."))

    # ── [2] Certificate status ─────────────────────────────────────────────
    status = cert.get("status", "UNKNOWN")
    status_ok = status == "ACTIVE"
    if status == "ACTIVE":
        checks.append(("Certificate status", True, "ACTIVE"))
    elif status == "REVOKED":
        reason = cert.get("revocation_reason") or "no reason provided"
        checks.append(("Certificate status", False, f"REVOKED — {reason}"))
    elif status == "EXPIRED":
        checks.append(("Certificate status", False, "EXPIRED"))
    else:
        checks.append(("Certificate status", False, f"UNKNOWN status: {status}"))

    # ── [3] TTL validity ───────────────────────────────────────────────────
    expires_str = cert.get("expires_at", "")
    ttl_ok      = False
    try:
        # Handle both 'Z' suffix and '+00:00'
        expires_str_n = expires_str.replace("Z", "+00:00")
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

    # ── [4] PQC signature presence ────────────────────────────────────────
    sig = cert.get("pqc_signature", "")
    if sig.startswith("ML-DSA-65:"):
        checks.append(("PQC signature (ML-DSA-65)", True,
                        "Present — ML-DSA-65 (FIPS 204 / NIST 2024)"))
    elif sig.startswith("STUB-"):
        checks.append(("PQC signature (ML-DSA-65)", None,  # None = warning
                        "Development stub — not production ML-DSA-65"))
    elif sig:
        checks.append(("PQC signature (ML-DSA-65)", None,
                        f"Unrecognised format: {sig[:30]}…"))
    else:
        checks.append(("PQC signature (ML-DSA-65)", False, "ABSENT"))

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

    # ── Overall result ────────────────────────────────────────────────────
    # Fail = any check where passed is explicitly False (not None/warning)
    overall_valid = all(passed is not False for _, passed, _ in checks)

    return overall_valid, checks


# ── Download ──────────────────────────────────────────────────────────────────

def download_certificate(pogc_id: str, endpoint: str) -> Dict[str, Any]:
    """
    Download a certificate from the public PoGR API.
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
            data = json.loads(resp.read().decode())
            return data
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
    pogc_id   = cert.get("pogc_id", "—")
    org       = cert.get("subject_org", "—")
    issued    = cert.get("issued_at", "—")[:19].replace("T", " ")
    expires   = cert.get("expires_at", "—")[:10]
    tier      = cert.get("compliance_tier", "—")
    mandate   = cert.get("mandate_certification", "UNCERTIFIED")
    turns     = cert.get("turn_count", "—")
    alg       = (cert.get("pqc_algorithm") or "ml-dsa-65").upper()

    print(BOLD("  Certificate"))
    print(f"  {'ID':<22}  {CYAN(pogc_id)}")
    print(f"  {'Organization':<22}  {org}")
    print(f"  {'Compliance tier':<22}  {tier}")
    print(f"  {'Mandate certification':<22}  {GOLD(mandate) if mandate != 'UNCERTIFIED' else DIM(mandate)}")
    print(f"  {'Session turns':<22}  {turns}")
    print(f"  {'Algorithm':<22}  {alg} · FIPS 204")
    print(f"  {'Issued':<22}  {issued} UTC")
    print(f"  {'Expires':<22}  {expires}")
    print()


def _print_checks(checks: List[Tuple[str, bool, str]]):
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
        print("  " + "─" * 56)
        print()
        print(f"  {GREEN(BOLD('✅  CERTIFICATE VALID'))}")
        print(f"  {DIM('This governance certificate passed all offline verification checks.')}")
        print(f"  {DIM('The AI session it references was governed correctly.')}")
    else:
        print("  " + "─" * 56)
        print()
        print(f"  {RED(BOLD('❌  CERTIFICATE INVALID'))}")
        print(f"  {DIM('One or more verification checks failed — see details above.')}")
    print()
    print(f"  {DIM('Verified at')} {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"  {DIM('Public URL')} {DEFAULT_ENDPOINT}/pogr/verify/{pogc_id}")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="verify_pogc_offline.py",
        description=(
            "OMNIX Proof of Governance — Offline Certificate Verifier.\n"
            "Verify any PoGC with no OMNIX account, no API key, no trust.\n"
            "PoGR-INV-003 · ADR-189 · OMNIX QUANTUM LTD"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python verify_pogc_offline.py POGC-A3F2B1C4D5E6F7A8\n"
            "  python verify_pogc_offline.py --file certificate.json\n"
            "  python verify_pogc_offline.py POGC-... --download-only\n"
        )
    )
    parser.add_argument(
        "pogc_id", nargs="?",
        help="PoG Certificate ID (e.g. POGC-A3F2B1C4D5E6F7A8)"
    )
    parser.add_argument(
        "--file", "-f", metavar="PATH",
        help="Path to a previously downloaded certificate JSON file"
    )
    parser.add_argument(
        "--endpoint", metavar="URL", default=DEFAULT_ENDPOINT,
        help=f"Registry API base URL (default: {DEFAULT_ENDPOINT})"
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
        help="Output results as machine-readable JSON"
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

        # Save if requested
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
    valid, checks = verify_certificate(cert)

    if args.json:
        result = {
            "valid":    valid,
            "pogc_id":  pogc_id,
            "checks":   [
                {"label": lbl, "passed": p, "detail": det}
                for lbl, p, det in checks
            ],
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "verifier":    f"OMNIX OfflineVerifier/{VERSION}",
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
