#!/usr/bin/env python3
"""
OMNIX PoGR — Re-issuance Script: POGC-GENESIS-E071CC96 → v2
ADR-205 §6.1 · POGR-SEC-014 · A08 Operational Closure

Purpose:
    POGC-GENESIS-E071CC96 was issued as canonical_version=1 before ADR-205 introduced
    canonical_version=2 (status + revoked_at cryptographically bound to hash + ML-DSA-65 sig).
    This is the only v1 cert ever issued. This script:

        1. Signs a valid revocation_proof for POGC-GENESIS-E071CC96 (ML-DSA-65, Phase 2 payload).
        2. Revokes POGC-GENESIS-E071CC96 via POST /v1/pogr/revoke/<id>.
        3. Issues a new canonical_version=2 cert for the GENESIS session.
        4. Verifies the new cert offline (content_hash + status binding).
        5. Writes a signed execution trace to evidence_packages/ (JSON).

Usage:
    # Dry-run (no network calls — shows what would happen):
    python scripts/reissue_pogc_genesis_v2.py --dry-run

    # Production execution (requires Railway API + env vars):
    OMNIX_WEB_URL=https://omnixquantum.net \\
    OMNIX_API_KEY=<your_b2b_api_key> \\
    OMNIX_SIGNING_SECRET_KEY_B64=<base64_sk> \\
    python scripts/reissue_pogc_genesis_v2.py

    # Custom endpoint (staging):
    python scripts/reissue_pogc_genesis_v2.py --endpoint https://staging.omnixquantum.net

    # Non-interactive (CI / ops automation):
    python scripts/reissue_pogc_genesis_v2.py --yes

Prerequisites:
    pip install oqs-python requests
    (oqs-python: https://github.com/open-quantum-safe/liboqs-python)

Environment variables (required unless --dry-run):
    OMNIX_WEB_URL              — Production API base URL
    OMNIX_API_KEY              — B2B API key with revoke + certify permissions
    OMNIX_SIGNING_SECRET_KEY_B64 — ML-DSA-65 private key (base64) for signing revocation_proof
    GENESIS_SESSION_ID         — OGR session ID for the new v2 cert (default: SESSION-GENESIS)

ADR-205 §6.1 — A08 Operational Closure
OMNIX QUANTUM LTD — Harold Nunes — 2026-05-31
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

# ── ANSI colours ──────────────────────────────────────────────────────────────

_TTY = sys.stdout.isatty()

def _c(code: str, t: str) -> str:
    return f"\033[{code}m{t}\033[0m" if _TTY else t

GREEN   = lambda t: _c("92",   t)
RED     = lambda t: _c("91",   t)
YELLOW  = lambda t: _c("93",   t)
CYAN    = lambda t: _c("96",   t)
BOLD    = lambda t: _c("1",    t)
DIM     = lambda t: _c("2",    t)
GOLD    = lambda t: _c("33;1", t)
MAGENTA = lambda t: _c("95",   t)

# ── Constants ─────────────────────────────────────────────────────────────────

GENESIS_POGC_ID  = "POGC-GENESIS-E071CC96"
GENESIS_SESSION  = os.environ.get("GENESIS_SESSION_ID", "SESSION-GENESIS")
DEFAULT_ENDPOINT = "https://omnixquantum.net"
SCRIPT_VERSION   = "1.0.0"
ADR_REF          = "ADR-205 §6.1 · POGR-SEC-014"
EVIDENCE_DIR     = os.path.join(os.path.dirname(__file__), "..", "evidence_packages")

# ── Banner ────────────────────────────────────────────────────────────────────

def _banner():
    print()
    print(GOLD("  ⬡  OMNIX PoGR — GENESIS Re-issuance (v1 → v2)"))
    print(DIM(f"     {ADR_REF} · A08 Operational Closure · v{SCRIPT_VERSION}"))
    print()


def _section(title: str):
    print()
    print(BOLD(f"── {title} " + "─" * max(0, 60 - len(title))))


def _ok(msg: str):
    print(f"  {GREEN('✓')} {msg}")


def _fail(msg: str):
    print(f"  {RED('✗')} {msg}")


def _warn(msg: str):
    print(f"  {YELLOW('⚠')} {msg}")


def _info(msg: str):
    print(f"  {CYAN('→')} {msg}")


def _step(n: int, total: int, msg: str):
    print()
    print(BOLD(f"  Step {n}/{total}: {msg}"))

# ── Phase 2 revocation_proof generation ───────────────────────────────────────

def _build_revocation_payload(pogc_id: str, reason: str, cert_issued_at: str) -> bytes:
    """
    Build the canonical payload for ML-DSA-65 revocation_proof signing.
    ADR-205 §6.2 — must match _verify_revocation_proof_phase2() in pogr_blueprint.py.

    Payload: {"action":"REVOKE","issued_at":<cert_issued_at>,"pogc_id":<id>,"revocation_reason":<reason>}
    (sort_keys=True, separators=(',',':'), UTF-8)
    """
    return json.dumps(
        {
            "action":             "REVOKE",
            "issued_at":          cert_issued_at,
            "pogc_id":            pogc_id,
            "revocation_reason":  reason,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def _sign_revocation_proof(
    pogc_id: str,
    reason: str,
    cert_issued_at: str,
    sk_b64: str,
    dry_run: bool = False,
) -> Tuple[Optional[str], str]:
    """
    Sign the revocation payload with ML-DSA-65 private key.

    Returns:
        (proof_str, description)
        proof_str: "ML-DSA-65:<hex_signature>" or None on failure
    """
    payload = _build_revocation_payload(pogc_id, reason, cert_issued_at)

    if dry_run:
        # Deterministic stub for dry-run (never accepted by Phase 2 verification)
        stub_hex = hashlib.sha3_256(b"DRY-RUN-PROOF:" + payload).hexdigest() * 4
        return (
            f"ML-DSA-65:{stub_hex}",
            "DRY-RUN stub (SHA3-256 · not a real ML-DSA-65 signature)",
        )

    try:
        from oqs import Signature as OQSSig
        sk = base64.b64decode(sk_b64)
        signer = OQSSig("ML-DSA-65", sk)
        sig_bytes = signer.sign(payload)
        proof = "ML-DSA-65:" + sig_bytes.hex()
        return proof, f"ML-DSA-65 signature ({len(sig_bytes)} bytes · FIPS 204 · NIST 2024)"
    except ImportError:
        return None, "oqs-python not installed — cannot sign ML-DSA-65 proof. pip install oqs-python"
    except Exception as exc:
        return None, f"Signing failed: {exc}"


# ── API helpers ───────────────────────────────────────────────────────────────

def _api(
    method: str,
    endpoint: str,
    path: str,
    api_key: str,
    body: Optional[Dict] = None,
    dry_run: bool = False,
) -> Tuple[int, Dict]:
    """Make an authenticated API call. In dry-run mode, return mocked responses."""
    url = f"{endpoint.rstrip('/')}{path}"

    if dry_run:
        _info(f"[DRY-RUN] {method.upper()} {url}")
        if body:
            _info(f"  Body: {json.dumps(body, indent=2)[:300]}")
        # Simulate plausible responses
        if "revoke" in path:
            return 200, {
                "status": "revoked",
                "pogc_id": GENESIS_POGC_ID,
                "revoked_at": datetime.now(timezone.utc).isoformat(),
                "reason": body.get("revocation_reason", "—") if body else "—",
                "_dry_run": True,
            }
        if "certify" in path:
            return 201, {
                "status": "issued",
                "certificate": {
                    "pogc_id":           "POGC-GENESIS-V2-DRYRUN",
                    "canonical_version": 2,
                    "status":            "ACTIVE",
                    "issued_at":         datetime.now(timezone.utc).isoformat(),
                    "mandate_certification": "MANDATE-BOUND",
                    "_dry_run":          True,
                },
                "_dry_run": True,
            }
        return 200, {"_dry_run": True}

    try:
        import urllib.request
        import urllib.error

        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "X-API-Key":     api_key,
                "Content-Type":  "application/json",
                "User-Agent":    f"OMNIX-GenesisReissue/{SCRIPT_VERSION}",
                "Accept":        "application/json",
            },
            method=method.upper(),
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except Exception as exc:
        # Try to extract body from HTTPError
        if hasattr(exc, "read"):
            try:
                body_bytes = exc.read()
                return getattr(exc, "code", 500), json.loads(body_bytes.decode())
            except Exception:
                pass
        return 0, {"error": str(exc)}


# ── Offline verification helper ────────────────────────────────────────────────

def _verify_cert_offline_quick(cert: Dict[str, Any]) -> Tuple[bool, str]:
    """Quick offline check: content_hash + status for the new v2 cert."""
    canon_version = int(cert.get("canonical_version") or 1)
    if canon_version < 2:
        return False, f"canonical_version={canon_version} — expected 2"

    canonical_v2_fields = [
        "pogc_id", "session_id", "ctchc_seal_hash",
        "issuer", "subject_org", "agent_id",
        "compliance_tier", "mandate_certification",
        "issued_at", "expires_at", "status", "revoked_at",
    ]
    canonical = {k: cert.get(k) for k in canonical_v2_fields}
    payload   = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    computed  = "sha3-256:" + hashlib.sha3_256(payload).hexdigest()
    stored    = cert.get("content_hash", "")

    if computed != stored:
        return False, f"content_hash mismatch\n  computed: {computed}\n  stored:   {stored}"

    status = cert.get("status", "UNKNOWN")
    if status != "ACTIVE":
        return False, f"status={status} — expected ACTIVE"

    return True, f"canonical_version=2 · content_hash ✓ · status=ACTIVE ✓"


# ── Evidence trace ─────────────────────────────────────────────────────────────

def _write_evidence_trace(trace: Dict[str, Any], dry_run: bool) -> str:
    """Write the execution trace to evidence_packages/ as JSON."""
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    suffix = "_dryrun" if dry_run else ""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"pogc_genesis_reissue_trace{suffix}_{ts}.json"
    path = os.path.join(EVIDENCE_DIR, filename)
    # Compute trace hash for integrity
    trace_bytes = json.dumps(trace, sort_keys=True, separators=(",", ":")).encode()
    trace["trace_hash"] = "sha3-256:" + hashlib.sha3_256(trace_bytes).hexdigest()
    with open(path, "w") as f:
        json.dump(trace, f, indent=2, default=str)
    return path


# ── Confirmation prompt ────────────────────────────────────────────────────────

def _confirm(msg: str, yes: bool) -> bool:
    if yes:
        _warn(f"--yes flag set: auto-confirming '{msg}'")
        return True
    print()
    print(YELLOW(f"  ? {msg}"))
    print(DIM("    Type 'yes' to proceed, anything else to abort: "), end="", flush=True)
    try:
        answer = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer == "yes"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="OMNIX PoGR — Re-issue POGC-GENESIS-E071CC96 as canonical_version=2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("OMNIX_WEB_URL", DEFAULT_ENDPOINT),
        help=f"API base URL (default: {DEFAULT_ENDPOINT})",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OMNIX_API_KEY", ""),
        help="B2B API key (or set OMNIX_API_KEY env var)",
    )
    parser.add_argument(
        "--sk-b64",
        default=os.environ.get("OMNIX_SIGNING_SECRET_KEY_B64", ""),
        help="ML-DSA-65 private key base64 (or set OMNIX_SIGNING_SECRET_KEY_B64)",
    )
    parser.add_argument(
        "--session-id",
        default=os.environ.get("GENESIS_SESSION_ID", GENESIS_SESSION),
        help=f"OGR session ID for new v2 cert (default: {GENESIS_SESSION})",
    )
    parser.add_argument(
        "--revocation-reason",
        default="Re-issued as canonical_version=2 per ADR-205 §6.1 A08 operational closure",
        help="Revocation reason for POGC-GENESIS-E071CC96",
    )
    parser.add_argument(
        "--regulatory-tags",
        default="EU-AI-ACT,MICA-TITLE-VI,DORA-ART-11",
        help="Comma-separated regulatory tags for new cert",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making API calls",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip all confirmation prompts (for CI / ops automation)",
    )
    args = parser.parse_args()

    _banner()

    TOTAL_STEPS = 5

    # ── Pre-flight checks ─────────────────────────────────────────────────────
    _section("Pre-flight Checks")

    issues = []
    if not args.dry_run:
        if not args.api_key:
            issues.append("OMNIX_API_KEY not set (--api-key)")
        if not args.sk_b64:
            issues.append("OMNIX_SIGNING_SECRET_KEY_B64 not set (--sk-b64)")
        if not args.endpoint or args.endpoint == DEFAULT_ENDPOINT:
            _warn(f"Endpoint: {args.endpoint} (production — double-check before proceeding)")
        else:
            _ok(f"Endpoint: {args.endpoint}")

    if issues:
        for issue in issues:
            _fail(issue)
        print()
        print(RED("  Aborting — missing required configuration."))
        print(DIM("  Use --dry-run to simulate without API calls."))
        print()
        sys.exit(1)

    if args.dry_run:
        _warn("DRY-RUN mode — no API calls will be made. Responses are simulated.")
    else:
        _ok(f"Endpoint:  {args.endpoint}")
        _ok(f"API key:   {'*' * 8}{args.api_key[-4:] if len(args.api_key) >= 4 else '****'}")
        _ok(f"SK loaded: {'yes' if args.sk_b64 else 'NO'}")

    _ok(f"Target:    {GENESIS_POGC_ID} (canonical_version=1 → 2)")
    _ok(f"Session:   {args.session_id}")
    _ok(f"Reason:    {args.revocation_reason}")
    _ok(f"Reg tags:  {args.regulatory_tags}")

    trace: Dict[str, Any] = {
        "script":            f"reissue_pogc_genesis_v2.py v{SCRIPT_VERSION}",
        "adr":               ADR_REF,
        "dry_run":           args.dry_run,
        "started_at":        datetime.now(timezone.utc).isoformat(),
        "operator_endpoint": args.endpoint,
        "old_pogc_id":       GENESIS_POGC_ID,
        "session_id":        args.session_id,
        "revocation_reason": args.revocation_reason,
        "steps":             {},
    }

    if not _confirm(
        f"Proceed with re-issuance of {GENESIS_POGC_ID}?",
        args.yes or args.dry_run,
    ):
        print(RED("\n  Aborted by operator.\n"))
        sys.exit(0)

    # ── Step 1: Fetch current cert from API ───────────────────────────────────
    _step(1, TOTAL_STEPS, f"Fetch current cert — {GENESIS_POGC_ID}")

    status_code, cert_resp = _api(
        "GET", args.endpoint, f"/v1/pogr/certificate/{GENESIS_POGC_ID}",
        args.api_key, dry_run=args.dry_run,
    )

    cert_issued_at = cert_resp.get("issued_at", "")
    cert_canon_version = cert_resp.get("canonical_version", "—")
    cert_status = cert_resp.get("status", "UNKNOWN")

    if args.dry_run:
        # Simulate v1 cert
        cert_issued_at = "2026-05-26T00:00:00+00:00"
        cert_canon_version = 1
        cert_status = "ACTIVE"

    trace["steps"]["1_fetch"] = {
        "status_code":       status_code,
        "cert_issued_at":    cert_issued_at,
        "canonical_version": cert_canon_version,
        "cert_status":       cert_status,
    }

    if not args.dry_run and status_code not in (200, 201):
        _fail(f"GET /v1/pogr/certificate/{GENESIS_POGC_ID} → HTTP {status_code}")
        _fail(f"Response: {cert_resp}")
        sys.exit(1)

    _ok(f"Fetched: canonical_version={cert_canon_version} · status={cert_status} · issued_at={cert_issued_at}")

    if str(cert_canon_version) == "2":
        _warn("Certificate is already canonical_version=2. Nothing to do.")
        _warn("If a fresh v2 cert is desired regardless, edit GENESIS_POGC_ID and re-run.")
        sys.exit(0)

    # ── Step 2: Generate ML-DSA-65 revocation_proof ───────────────────────────
    _step(2, TOTAL_STEPS, "Generate ML-DSA-65 revocation_proof (Phase 2)")

    proof, proof_desc = _sign_revocation_proof(
        pogc_id       = GENESIS_POGC_ID,
        reason        = args.revocation_reason,
        cert_issued_at= cert_issued_at,
        sk_b64        = args.sk_b64,
        dry_run       = args.dry_run,
    )

    trace["steps"]["2_proof"] = {
        "description":    proof_desc,
        "proof_prefix":   (proof[:40] + "…") if proof else None,
        "payload_fields": ["action", "issued_at", "pogc_id", "revocation_reason"],
    }

    if proof is None:
        _fail(proof_desc)
        sys.exit(1)

    _ok(f"Proof generated: {proof_desc}")
    _info(f"Proof prefix:    {proof[:50]}…")

    # ── Step 3: Revoke POGC-GENESIS-E071CC96 ─────────────────────────────────
    _step(3, TOTAL_STEPS, f"Revoke {GENESIS_POGC_ID}")

    if not _confirm(
        f"Send POST /v1/pogr/revoke/{GENESIS_POGC_ID} — this is IRREVERSIBLE on the live registry.",
        args.yes or args.dry_run,
    ):
        print(RED("\n  Aborted by operator.\n"))
        sys.exit(0)

    revoke_body = {
        "revocation_reason": args.revocation_reason,
        "revocation_proof":  proof,
    }

    t0 = time.monotonic()
    rev_code, rev_resp = _api(
        "POST", args.endpoint, f"/v1/pogr/revoke/{GENESIS_POGC_ID}",
        args.api_key, body=revoke_body, dry_run=args.dry_run,
    )
    rev_latency_ms = round((time.monotonic() - t0) * 1000)

    trace["steps"]["3_revoke"] = {
        "status_code": rev_code,
        "response":    rev_resp,
        "latency_ms":  rev_latency_ms,
    }

    if rev_code not in (200, 201):
        _fail(f"POST /v1/pogr/revoke/{GENESIS_POGC_ID} → HTTP {rev_code}")
        _fail(f"Response: {json.dumps(rev_resp, indent=2)}")
        print()
        print(RED("  Revocation failed. New cert NOT issued. Registry unchanged."))
        _write_evidence_trace(trace, args.dry_run)
        sys.exit(1)

    revoked_at = rev_resp.get("revoked_at", datetime.now(timezone.utc).isoformat())
    _ok(f"Revoked: {GENESIS_POGC_ID} · revoked_at={revoked_at} · latency={rev_latency_ms}ms")

    # ── Step 4: Issue new canonical_version=2 cert ────────────────────────────
    _step(4, TOTAL_STEPS, f"Issue new v2 cert for session {args.session_id}")

    reg_tags = [t.strip() for t in args.regulatory_tags.split(",") if t.strip()]

    certify_body = {
        "session_id":      args.session_id,
        "regulatory_tags": reg_tags,
        "subject_org":     "OMNIX QUANTUM LTD",
    }

    t1 = time.monotonic()
    cert_code, cert_resp2 = _api(
        "POST", args.endpoint, "/v1/pogr/certify",
        args.api_key, body=certify_body, dry_run=args.dry_run,
    )
    cert_latency_ms = round((time.monotonic() - t1) * 1000)

    new_cert = cert_resp2.get("certificate") or cert_resp2
    new_pogc_id = new_cert.get("pogc_id", "UNKNOWN")

    trace["steps"]["4_certify"] = {
        "status_code":   cert_code,
        "new_pogc_id":   new_pogc_id,
        "latency_ms":    cert_latency_ms,
        "response_keys": list(cert_resp2.keys()),
    }

    if cert_code not in (200, 201):
        _fail(f"POST /v1/pogr/certify → HTTP {cert_code}")
        _fail(f"Response: {json.dumps(cert_resp2, indent=2)[:500]}")
        print()
        _warn(f"WARNING: {GENESIS_POGC_ID} was REVOKED but new cert issuance FAILED.")
        _warn("Manual intervention required — re-run certify step independently.")
        _write_evidence_trace(trace, args.dry_run)
        sys.exit(1)

    new_canon_v = new_cert.get("canonical_version", "?")
    new_status  = new_cert.get("status", "?")
    new_mandate = new_cert.get("mandate_certification", "?")

    _ok(f"New cert: {new_pogc_id}")
    _ok(f"  canonical_version = {new_canon_v}")
    _ok(f"  status            = {new_status}")
    _ok(f"  mandate           = {new_mandate}")
    _ok(f"  latency           = {cert_latency_ms}ms")

    # ── Step 5: Offline verification of new cert ──────────────────────────────
    _step(5, TOTAL_STEPS, "Offline verification — new v2 cert")

    offline_ok, offline_detail = _verify_cert_offline_quick(new_cert)

    trace["steps"]["5_offline_verify"] = {
        "passed":  offline_ok,
        "detail":  offline_detail,
    }
    trace["new_pogc_id"]    = new_pogc_id
    trace["completed_at"]   = datetime.now(timezone.utc).isoformat()
    trace["outcome"]        = "SUCCESS" if offline_ok else "PARTIAL_FAILURE"

    if offline_ok:
        _ok(f"Offline verification: {offline_detail}")
    else:
        _warn(f"Offline verification: {offline_detail}")
        _warn("The cert was issued but offline hash check has warnings — inspect manually.")

    # ── Write evidence trace ──────────────────────────────────────────────────
    _section("Evidence Trace")

    trace_path = _write_evidence_trace(trace, args.dry_run)
    _ok(f"Trace written: {os.path.relpath(trace_path)}")

    # ── Summary ───────────────────────────────────────────────────────────────
    _section("Summary")

    print()
    print(BOLD("  Re-issuance Result"))
    print(f"  {'Old cert':<28} {DIM(GENESIS_POGC_ID)} → REVOKED ✓")
    print(f"  {'New cert':<28} {CYAN(new_pogc_id)} · v{new_canon_v} · {new_status}")
    print(f"  {'Mandate':<28} {GOLD(new_mandate)}")
    print(f"  {'Offline verify':<28} {'✓ PASS' if offline_ok else '⚠ WARNING'}")
    print(f"  {'Evidence trace':<28} {os.path.relpath(trace_path)}")
    print()

    if offline_ok:
        print(BOLD(GREEN("  ✓ A08 CLOSED — POGC-GENESIS re-issued as canonical_version=2")))
        print(DIM("    Status and revocation are now cryptographically bound to hash + ML-DSA-65 sig."))
        print(DIM(f"    Verify the new cert: python scripts/verify_pogc_offline.py {new_pogc_id}"))
    else:
        print(BOLD(YELLOW("  ⚠ Re-issuance completed with warnings — manual inspection recommended")))

    print()


if __name__ == "__main__":
    main()
