"""
OMNIX PoGR — Import External Certificate to Production Registry
===============================================================

Registers POGC-EXT-A7F3C2B1D9E4F508 (VeriSigil AI) in the Railway production
database and immediately signs it with the real ML-DSA-65 key.

After running this script, anyone can verify the certificate at:
    https://omnixquantum.net/pogr/verify/POGC-EXT-A7F3C2B1D9E4F508

Usage (from workspace root):
    POGR_ADMIN_RESIGN_SECRET=<secret> python scripts/import_external_pogc_to_production.py

Or if the secret is already in the environment (Replit):
    python scripts/import_external_pogc_to_production.py

Harold Nunes — OMNIX QUANTUM LTD — 2026-05-31
"""

import hashlib
import hmac as _hmac
import json
import os
import sys
import urllib.request
import urllib.error

# ── Target ────────────────────────────────────────────────────────────────────
PRODUCTION_URL = "https://omnixquantum.net"
ENDPOINT       = f"{PRODUCTION_URL}/v1/pogr/admin/import-external"
POGC_ID        = "POGC-EXT-A7F3C2B1D9E4F508"

# ── Certificate data (from generate_verisigil_pogc.py + ADR-186/187) ─────────
CERT_PAYLOAD = {
    "pogc_id":               POGC_ID,
    "session_id":            "bundle-482df2c4f1d9",
    "ctchc_seal_hash":       "586b996f53da83652b2690b4117a4830d4bde3c22c7737085c40f5ee86a4ac3a",
    "issuer":                "OMNIX QUANTUM LTD",
    "subject_org":           "VeriSigil AI",
    "subject_org_id":        "verisigil-ai-001",
    "agent_id":              "financial-agent-1780111266",
    "compliance_tier":       "EXT-VGS-ELI-Compliant",
    "mandate_certification": "MANDATE-BOUND",
    "turn_count":            1,
    "avg_conformance":       1.0,
    "issued_at":             "2026-05-30T21:00:00+00:00",
    "expires_at":            "2027-05-30T21:00:00+00:00",
    "regulatory_tags":       ["EU-AI-ACT", "NIST-AU-2", "ISO-42001"],
}


def _compute_token(secret: str, pogc_id: str) -> str:
    """Compute the HMAC-SHA3-256 admin token for import-external."""
    return _hmac.new(
        secret.encode(),
        f"POGR-IMPORT-EXTERNAL:{pogc_id}".encode(),
        hashlib.sha3_256,
    ).hexdigest()


def _call(url: str, payload: dict, token: str) -> dict:
    """POST JSON to the endpoint with the admin token header."""
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type":       "application/json",
            "X-Admin-Import-Token": token,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode()
            return {"http_status": resp.status, "body": json.loads(body)}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return {"http_status": e.code, "body": json.loads(body)}
        except Exception:
            return {"http_status": e.code, "body": body}
    except Exception as exc:
        return {"http_status": 0, "body": str(exc)}


def main():
    print("=" * 68)
    print("  OMNIX PoGR — External Certificate Import")
    print(f"  Target : {PRODUCTION_URL}")
    print(f"  POGC ID: {POGC_ID}")
    print("=" * 68)

    # ── Resolve secret ────────────────────────────────────────────────────
    secret = (
        os.environ.get("POGR_RESIGN_TOKEN")
        or os.environ.get("POGR_ADMIN_RESIGN_SECRET", "")
    ).strip()

    if not secret:
        print("\n❌  POGR_ADMIN_RESIGN_SECRET not set.")
        print("    Run with: POGR_ADMIN_RESIGN_SECRET=<secret> python scripts/import_external_pogc_to_production.py")
        sys.exit(1)

    token = _compute_token(secret, POGC_ID)
    print(f"\n✅  Token computed (sha3-256, first 16 chars): {token[:16]}...")

    # ── Send request ──────────────────────────────────────────────────────
    print(f"\n📡  POST {ENDPOINT}")
    result = _call(ENDPOINT, CERT_PAYLOAD, token)

    http_status = result["http_status"]
    body        = result["body"]

    print(f"    HTTP {http_status}")

    if http_status in (200, 201):
        status = body.get("status", "?")
        if status == "already_registered":
            print("\n✅  Certificate already in production registry — no action needed.")
        elif status == "imported":
            print("\n✅  Certificate successfully imported and signed with ML-DSA-65!")
            print(f"   PQC algorithm : {body.get('pqc_algorithm', '?')}")
            print(f"   Content hash  : {body.get('content_hash', '?')[:40]}...")
        else:
            print(f"\n✅  Response: {status}")

        public_page = body.get("public_page", f"{PRODUCTION_URL}/pogr/verify/{POGC_ID}")
        verify_url  = body.get("verify_url",  f"{PRODUCTION_URL}/v1/pogr/verify/{POGC_ID}")
        print()
        print(f"   🔗 Public page  : {public_page}")
        print(f"   🔗 API verify   : {verify_url}")
        print()
        print("   Raheem can now go to:")
        print(f"   {public_page}")
        print("   and see the certificate with a green ✅ VÁLIDO.")

    elif http_status == 403:
        print("\n❌  Authentication failed — wrong POGR_ADMIN_RESIGN_SECRET.")
        print(f"    Server said: {body}")

    elif http_status == 503:
        print("\n❌  Server unavailable or ML-DSA-65 key not configured on Railway.")
        print(f"    Server said: {body}")

    else:
        print(f"\n❌  Unexpected response:")
        print(f"    {json.dumps(body, indent=2) if isinstance(body, dict) else body}")
        sys.exit(1)

    print("=" * 68)


if __name__ == "__main__":
    main()
