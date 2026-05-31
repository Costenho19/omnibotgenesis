# POGR Remediation Plan — Audit V2

**System:** OMNIX Proof of Governance Registry (PoGR)  
**Version:** 2.0 — Post-Adversarial Audit  
**Date:** 2026-05-30  
**Source audit:** `POGR_ADVERSARIAL_AUDIT_V2.md`

---

## Remediation Priority Order

| Priority | Finding | File | Effort | Blocks Production? |
|---|---|---|---|---|
| 🔴 P0 | X01 — admin_resign derivable token | `pogr_blueprint.py` | 15 min | YES |
| 🔴 P1 | X02 — API PQC soft-fail | `pogr_blueprint.py` | 20 min | YES |
| 🔴 P2 | X03 — Offline sim-forgery | `verify_pogc_offline.py` | 30 min | YES |
| 🟡 P3 | A08 / H1 — POGC-GENESIS v1 | Re-issuance | 20 min | YES (trust) |
| 🟡 P4 | X04 — revocation_proof unverified | `pogr_blueprint.py` | 45 min | Partial |
| 🟢 P5 | M1 — POGC ID entropy | `pogr_blueprint.py` | 5 min | No |
| 🟢 P6 | M2 — Rate limiting | `pogr_blueprint.py` | 30 min | No |

---

## R-C1 — Fix admin_resign Authentication (P0 — CRITICAL)

**Finding:** X01  
**File:** `omnix_web/api/pogr_blueprint.py`, line 1427–1434  

### Root Cause

```python
# CURRENT (INSECURE):
expected_token = hashlib.sha3_256(
    f"POGR-RESIGN:{pogc_id}".encode()
).hexdigest()
```

The token has zero secret component. It is derivable by any party with access to
the source code (publicly auditable). The formula `sha3_256("POGR-RESIGN:" + pogc_id)`
is computable offline for any certificate ID.

### Remediation

Replace derivable hash with HMAC using a server-side secret:

```python
# FIXED:
import hmac as _hmac

RESIGN_SECRET = os.environ.get("POGR_ADMIN_RESIGN_SECRET", "")
if not RESIGN_SECRET:
    return _err(
        "POGR_ADMIN_RESIGN_SECRET not configured — admin operations unavailable",
        503
    )

expected_token = _hmac.new(
    RESIGN_SECRET.encode(),
    f"POGR-RESIGN:{pogc_id}".encode(),
    hashlib.sha3_256
).hexdigest()

provided_token = request.headers.get("X-Admin-Resign-Token", "").strip()
if not provided_token or not _hmac.compare_digest(expected_token, provided_token):
    logger.warning(f"[PoGR] admin_resign: invalid token for {pogc_id}")
    return _err("Invalid or missing X-Admin-Resign-Token", 403)
```

**Note:** Use `hmac.compare_digest()` to prevent timing side-channel attacks.

### Environment variable required

Add to Railway:

```
POGR_ADMIN_RESIGN_SECRET = <strong random secret — min 32 bytes>
```

Generate with: `python3 -c "import secrets; print(secrets.token_hex(32))"`

### Acceptance criteria

- `POST /v1/pogr/admin/resign/<pogc_id>` returns 503 if secret not configured
- Token computed without `POGR_ADMIN_RESIGN_SECRET` is rejected with 403
- Token computed with correct secret is accepted
- `hmac.compare_digest` used (no timing oracle)

---

## R-H2 — Fix API PQC Soft-Fail (P1 — HIGH)

**Finding:** X02  
**File:** `omnix_web/api/pogr_blueprint.py`, function `_verify_pqc_signature()`, line 222–226

### Root Cause

```python
# CURRENT (UNSAFE):
pk_b64 = os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64")
if not pk_b64:
    return (None,
            "⚠ Platform public key not configured ...")
    # ↑ None does NOT trigger valid=False in _verify_certificate_core()
    # The certificate is returned as valid=True with only a warning.
```

### Remediation

Add a fail-closed mode controlled by `OMNIX_PQC_VERIFY_FAIL_CLOSED` env var.
In Railway production, this variable must be set to `"true"`.

```python
# FIXED:
pk_b64 = os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64")
if not pk_b64:
    fail_closed = os.environ.get("OMNIX_PQC_VERIFY_FAIL_CLOSED", "false").lower() == "true"
    if fail_closed:
        return (False,
                "✗ PQC verification FAILED — OMNIX_SIGNING_PUBLIC_KEY_B64 not configured "
                "and OMNIX_PQC_VERIFY_FAIL_CLOSED=true (production mode). "
                "Certificate cannot be cryptographically verified.")
    return (None,
            "⚠ Platform public key not configured (OMNIX_SIGNING_PUBLIC_KEY_B64) "
            "— PQC cryptographic verification skipped; hash integrity still enforced "
            "[WARN: set OMNIX_PQC_VERIFY_FAIL_CLOSED=true in production]")
```

Additionally, log a CRITICAL-level alert when the key is missing in production:

```python
if not pk_b64:
    import os as _os
    if _os.environ.get("RAILWAY_ENVIRONMENT") or _os.environ.get("RAILWAY_SERVICE_NAME"):
        logger.critical(
            "[PoGR] OMNIX_SIGNING_PUBLIC_KEY_B64 missing in production environment! "
            "PQC verification is running in hash-only mode. "
            "All PoGR certificates appear valid without cryptographic proof."
        )
```

### Environment variable required

Add to Railway:

```
OMNIX_PQC_VERIFY_FAIL_CLOSED = true
```

### Acceptance criteria

- With `OMNIX_PQC_VERIFY_FAIL_CLOSED=true` and missing key: `valid=False`, HTTP 200 with `{"valid": false}`
- With key configured: normal cryptographic verification (unchanged)
- Without `OMNIX_PQC_VERIFY_FAIL_CLOSED` set: current warning behavior (backward compat in dev)
- CRITICAL log emitted in Railway when key is absent

---

## R-H3 — Restrict Offline Sim-Forgery Path (P2 — HIGH)

**Finding:** X03  
**File:** `scripts/verify_pogc_offline.py`, function `_verify_pqc_signature()`, line 195–210

### Root Cause

The AUDIT-PQC-SIM-V2 path is default behavior when oqs is unavailable. It returns
`(None, ...)` which is treated as non-blocking by `overall_valid`. A forger who knows
the public formula can create a cert that passes with `overall_valid=True`.

### Remediation — Two-Part Fix

#### Part A: Make sim path explicit opt-in (`--allow-sim`)

```python
# New function signature:
def _verify_pqc_signature(
    cert, canonical, platform_key_b64, *, allow_sim: bool = False
) -> Tuple[Optional[bool], str]:
    ...
    # Path B: Audit-sim (only if explicitly opted in)
    if allow_sim:
        sig_hex      = sig_str.removeprefix("ML-DSA-65:")
        expected_sim = hashlib.sha3_256(b"AUDIT-PQC-SIM-V2:" + payload).hexdigest()
        if sig_hex == expected_sim:
            return (None, "SHA3-256 audit simulation verified ...")
    
    # Path C (formerly): Now the default when no key and no sim
    return (False,
            "PQC signature UNVERIFIABLE — cannot be trusted.\n"
            "  No platform key available for ML-DSA-65 verification.\n"
            "  Install oqs-python and provide the platform key:\n"
            "    pip install oqs-python\n"
            "    python verify_pogc_offline.py --file cert.json --platform-key <b64>")
```

#### Part B: Add `--allow-sim` CLI flag

```python
parser.add_argument(
    "--allow-sim",
    action="store_true",
    default=False,
    help=(
        "Accept AUDIT-PQC-SIM-V2 signatures as valid (WARNING). "
        "Use ONLY in test/development environments. "
        "Production certificates always carry real ML-DSA-65 signatures."
    ),
)
```

Pass `allow_sim=args.allow_sim` when calling `_verify_pqc_signature`.

#### Part C: Update `verify_certificate()` signature

```python
def verify_certificate(
    cert, platform_key_b64=None, *, allow_sim: bool = False
) -> Tuple[bool, List]:
    ...
    pqc_ok, pqc_msg = _verify_pqc_signature(cert, canonical, platform_key_b64,
                                              allow_sim=allow_sim)
```

### Acceptance criteria

- Without `--allow-sim`: real ML-DSA-65 cert with no oqs → UNVERIFIABLE (False) → INVALID
- Without `--allow-sim`: forged sim cert with no oqs → UNVERIFIABLE (False) → INVALID
- With `--allow-sim`: sim cert → WARNING → VALID+warn (dev env only)
- With `--allow-sim` + oqs + key: real cert → VALID (oqs takes precedence over sim)
- `--help` output clearly explains `--allow-sim` is dev-only

---

## R-H1 — Retire POGC-GENESIS v1 Certificate (P3 — HIGH)

**Finding:** A08  
**Issue:** POGC-GENESIS-E071CC96 was issued as `canonical_version=1`. If revoked,
the offline verifier cannot detect the revocation from an exported file.

### Remediation — Re-issuance

The only correct fix is to re-issue the genesis certificate as `canonical_version=2`.
A v1 cert cannot be upgraded in place — the cryptographic anchor changes.

#### Steps:

1. Revoke POGC-GENESIS-E071CC96 via `POST /v1/pogr/revoke/POGC-GENESIS-E071CC96`
   with `revocation_reason: "Superseded by v2 canonical schema (ADR-205)"`
   and a valid `revocation_proof` string.

2. Issue a new PoGC against the same session (or a new GENESIS session) with
   `canonical_version=2` (current default).

3. Update all references to POGC-GENESIS-E071CC96 in:
   - `replit.md`
   - `docs/ARCHITECTURE_INDEX.md`
   - `docs/INDEPENDENT_VERIFIER_GUIDE.md`
   - Any public-facing documentation or RFC appendices

#### Interim mitigation (before re-issuance):

Add to offline verifier: when `canon_version < 2` AND `status != "ACTIVE"` → **hard fail**:

```python
# In verify_certificate(), after Check 2 (status check):
if canon_version < 2 and status != "ACTIVE":
    # v1 cert showing non-ACTIVE: the status IS in the file even though not bound
    # to hash. A revoked/expired v1 cert offline should always be INVALID.
    checks.append(("v1 status hard-fail", False,
                   f"v1 canonical schema: status='{status}' detected. "
                   "Even without cryptographic binding, this status is authoritative. "
                   f"Verify live: {DEFAULT_ENDPOINT}/v1/pogr/verify/{cert.get('pogc_id','')}"))
```

This does not fix the full bypass (attacker can set `status=ACTIVE` in the file),
but it correctly handles the honest case of a legitimately revoked v1 cert.

### Acceptance criteria

- No v1 certificates remain ACTIVE in the registry after re-issuance
- All new certificates are `canonical_version=2` (already enforced by `CURRENT_CANONICAL_VERSION=2`)
- Updated genesis cert ID documented in all canonical locations

---

## R-M1 — revocation_proof Verification (P4 — MEDIUM)

**Finding:** X04  
**File:** `omnix_web/api/pogr_blueprint.py`, `revoke()` endpoint, line 935–941

### Root Cause

`revocation_proof` is stored as an opaque string, never verified against any
cryptographic standard. PoGR-INV-006 states: "Revocation requires PQC proof from
original issuer" — but the invariant is not machine-enforced.

### Remediation — Phase 1 (Structural)

Define a machine-verifiable revocation proof format:

```json
{
  "proof_type": "ML-DSA-65",
  "signed_payload": "REVOKE:<pogc_id>:<revocation_reason>:<iso_timestamp>",
  "signature_hex": "<ML-DSA-65 signature over signed_payload>",
  "algorithm": "ml-dsa-65-fips204"
}
```

Validate in `revoke()`:

```python
import json as _json

try:
    proof_obj = _json.loads(proof)
    assert proof_obj.get("proof_type") == "ML-DSA-65"
    # Verify signature against the org's registered public key
    # (requires org public key storage — Phase 2 DB schema addition)
except Exception:
    return _err(
        "revocation_proof must be a JSON object with proof_type=ML-DSA-65 "
        "and a valid ML-DSA-65 signature. See ADR-186 §6 for format spec.",
        400
    )
```

**Note:** Full implementation requires storing the issuing org's public key
at certification time. This is a Phase 2 schema addition (new column: `issuer_public_key`
in `pogr_certificates`).

### Phase 1 (Immediate — No DB change required)

Enforce minimum structural validity:

```python
# Reject obviously invalid proofs (empty string already caught above)
if len(proof) < 64:
    return _err("revocation_proof is too short to be a valid cryptographic proof", 400)
if not (proof.startswith("ML-DSA-65:") or proof.startswith("{")):
    return _err(
        "revocation_proof must be either an ML-DSA-65 hex signature "
        "(prefix 'ML-DSA-65:') or a JSON proof object", 400
    )
```

### Acceptance criteria

- Phase 1: empty strings and trivially invalid proofs are rejected
- Phase 2: proof cryptographically verified against issuing org's public key
- PoGR-INV-006 emitted as satisfied only when proof is structurally valid

---

## R-M2 — POGC ID Entropy Upgrade (P5 — MEDIUM)

**Finding:** M1 — 64-bit entropy below NIST SP 800-90B 128-bit recommendation

### Remediation

```python
# CURRENT:
def _pogc_id() -> str:
    return "POGC-" + secrets.token_hex(8).upper()   # 64-bit

# FIXED:
def _pogc_id() -> str:
    return "POGC-" + secrets.token_hex(16).upper()  # 128-bit
```

128-bit entropy → birthday bound collision at ~2^64 certificates.
ID length increases from 16 to 32 hex characters.

**Migration:** Existing POGC IDs retain their original format. New IDs use 32-char format.
No DB schema change required (column is `TEXT`).

### Acceptance criteria

- New IDs: 32 hex characters (128-bit entropy)
- No existing IDs invalidated
- `_pogc_id()` test passes

---

## R-M3 — Rate Limiting on Public Endpoints (P6 — MEDIUM)

**Finding:** M2 — Unauthenticated /verify and /export endpoints have no rate limiting

### Remediation

Add Flask-Limiter with Redis backend (Railway Redis already configured):

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    storage_uri=os.environ.get("REDIS_URL"),
    default_limits=["200 per day", "50 per hour"]
)

# On the verify endpoint:
@pogr_bp.route("/v1/pogr/verify/<pogc_id>")
@limiter.limit("60 per minute")
def verify(pogc_id):
    ...

# On the export endpoint:
@pogr_bp.route("/v1/pogr/certificate/<pogc_id>/export")
@limiter.limit("20 per minute")
def export_certificate(pogc_id):
    ...
```

**Install:** `pip install flask-limiter[redis]`

### Acceptance criteria

- `/v1/pogr/verify` returns 429 after 60 req/min per IP
- `/v1/pogr/certificate/.../export` returns 429 after 20 req/min per IP
- Limits do not apply to authenticated API key requests

---

## Production-Ready Checklist

Complete the following before declaring PoGR production-ready:

```
[ ] R-C1 — admin_resign uses HMAC with POGR_ADMIN_RESIGN_SECRET (P0)
[ ] R-H2 — OMNIX_PQC_VERIFY_FAIL_CLOSED=true in Railway (P1)
[ ] R-H3 — --allow-sim flag in verify_pogc_offline.py v2.1 (P2)
[ ] R-H1 — POGC-GENESIS v1 revoked + new v2 cert issued (P3)
[ ] R-M1 — revocation_proof Phase 1 structural validation (P4)
[ ] DNS TXT channel for public key published (PoGR-INV-005)
[ ] Zenodo DOI snapshot for public key published (PoGR-INV-005)
[ ] Re-run adversarial audit (Audit V3) against all remediations
[ ] 0 CRITICAL, 0 HIGH confirmed in Audit V3
```

### Expected Audit V3 Results (after all remediations)

| Finding | Status After Remediation |
|---|---|
| X01 — admin_resign derivable token | ✅ CLOSED — HMAC with secret |
| X02 — API PQC soft-fail | ✅ CLOSED — fail-closed mode |
| X03 — Offline sim-forgery | ✅ CLOSED — sim path opt-in only |
| A08 — v1 offline bypass | ✅ CLOSED — v1 cert revoked, no new v1 |
| X04 — revocation_proof | ⚠ PARTIAL — Phase 1 only |
| M1 — ID entropy | ✅ CLOSED — 128-bit |
| M2 — rate limiting | ✅ CLOSED — Flask-Limiter |

**After all P0–P3 remediations:**
- 0 Critical
- 0 High
- Web = API = Offline (all conditions)
- No certificate forgery path without OMNIX private key

> PoGR is production-ready when all P0–P3 items are ✅.
