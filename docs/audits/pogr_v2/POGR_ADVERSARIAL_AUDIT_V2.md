# POGR Adversarial Audit V2 — Institutional Security Review

**System:** OMNIX Proof of Governance Registry (PoGR)  
**Audit Version:** 2.0 — Full Adversarial  
**Date:** 2026-05-30  
**ADR References:** ADR-186 · ADR-187 · ADR-189 · ADR-205  
**Auditor Roles Assumed:** Hostile Protocol Reviewer · Cryptography Auditor ·
EU AI Act Assessor · Enterprise Security Reviewer · Skeptical External Verifier

---

## Scope and Objective

This audit assumes the adversarial posture of a hostile external party attempting to:

1. Forge a valid-looking PoG Certificate
2. Bypass revocation status of a revoked certificate
3. Exploit inconsistencies between verification channels
4. Undermine the trust assumptions that OMNIX publishes to regulators and enterprises

**Attack surface targeted:**

| Target | Implementation |
|---|---|
| Web verification page | `GET /pogr/verify/<pogc_id>` (Jinja2 HTML) |
| JSON API verification | `GET /v1/pogr/verify/<pogc_id>` (Flask JSON) |
| Certificate export | `GET /v1/pogr/certificate/<pogc_id>/export` |
| Offline standalone verifier | `scripts/verify_pogc_offline.py` v2.0 |
| Admin re-sign endpoint | `POST /v1/pogr/admin/resign/<pogc_id>` |

**Mandate:** Do not validate. Attempt to break.

---

## Attack Matrix — 15 Specified + 4 Additional

| ID | Attack | Target | Verdict | Severity |
|---|---|---|---|---|
| A01 | Modify `content_hash` field | Offline JSON | **DETECTED** | HIGH |
| A02 | Modify `issuer` field | Offline / API | **DETECTED** | HIGH |
| A03 | Modify `mandate_certification` | Offline / API | **DETECTED** | CRITICAL |
| A04 | Modify `compliance_tier` | Offline / API | **DETECTED** | CRITICAL |
| A05 | Modify `expires_at` to future | Offline / API | **DETECTED** | CRITICAL |
| A06 | Replace `pqc_signature` | Offline / API | **DETECTED** | CRITICAL |
| A07 | Replay expired certificate | Offline / API | **DETECTED** | MEDIUM |
| A08 | Replay revoked cert (v1 schema) | Offline (v1 only) | **BYPASSED** | MEDIUM |
| A09 | Export JSON tampering + offline verify | Offline | **DETECTED** | CRITICAL |
| A10 | API vs Web display inconsistency | API · Web | **DETECTED** | LOW |
| A11 | API vs Offline inconsistency | API · Offline | **DETECTED** | LOW |
| A12 | Web vs Offline inconsistency | Web · Offline | **DETECTED** | LOW |
| A13 | Missing mandatory fields | Offline / API | **DETECTED** | HIGH |
| A14 | Extra malicious injected fields | Offline / API | **DETECTED** | LOW |
| A15 | POGC ID collision attempt | API | **DETECTED** | MEDIUM |
| **X01** | **admin_resign unauthenticated** | Admin endpoint | **BYPASSED** | **CRITICAL** |
| **X02** | **API PQC soft-fail (no key)** | API verify | **BYPASSED** | **HIGH** |
| **X03** | **Offline sim-forgery path** | Offline verifier | **BYPASSED** | **HIGH** |
| **X04** | **revocation_proof not verified** | Revoke endpoint | **BYPASSED** | **MEDIUM** |

---

## Detailed Attack Analysis

---

### A01 — Modify `content_hash` Field

**Threat model:** Attacker downloads exported JSON, replaces `content_hash` with a value
matching tampered canonical fields.

**Attack vector:**
```python
cert["mandate_certification"] = "MANDATE-BOUND"
cert["content_hash"] = "sha3-256:" + sha3_256(json.dumps({...new fields...})).hexdigest()
# Leave pqc_signature unchanged (was signed over original fields)
```

**Code path analyzed:**
- `verify_pogc_offline.py` L250: `computed_hash = _compute_content_hash(cert, canon_version)`
- L251: `hash_ok = stored_hash == computed_hash`

**Result:** DETECTED. The verifier recomputes the hash independently from canonical fields.
The new `content_hash` matches the tampered fields, but the `pqc_signature` was signed over
the *original* canonical payload. PQC check (Check 4) fails:
- With `oqs` + platform key → `ML-DSA-65.verify()` raises → HARD FAIL
- Without `oqs`, real sig format → Path C → `PQC signature UNVERIFIABLE` → HARD FAIL

**Verdict:** DETECTED (both paths catch this).

---

### A02 — Modify `issuer` Field

**Threat model:** Attacker substitutes the issuer to impersonate a different authority.

**Attack vector:**
```json
{ "issuer": "Acme Governance Corp" }
```

**Code paths:**
1. `verify_pogc_offline.py` L311: explicit `cert.get("issuer") == "OMNIX QUANTUM LTD"` check
2. `issuer` is in `_CANONICAL_V1` (L70–76) → hash mismatch if changed

**Result:** DETECTED via two independent mechanisms: issuer identity check AND hash integrity.

---

### A03 — Modify `mandate_certification`

**Threat model:** Attacker upgrades `UNCERTIFIED` → `MANDATE-BOUND` to misrepresent
the MIVP compliance tier to a regulator.

**`mandate_certification` is in `_CANONICAL_V1` (field 8 of 10).**
Any modification invalidates the SHA3-256 content hash, which in turn invalidates the ML-DSA-65 signature.

**Verdict:** DETECTED — hash mismatch on Check 1, PQC fail on Check 4.  
**Severity: CRITICAL** — this field carries regulatory weight under EU AI Act Art. 9.

---

### A04 — Modify `compliance_tier`

**Same binding as A03.** `compliance_tier` is canonical field 7.  
Modifying it produces both a hash mismatch and a signature failure.

**Verdict:** DETECTED.  
**Severity: CRITICAL** — tier drives procurement decisions and regulatory alignment claims.

---

### A05 — Modify `expires_at` to Future Date

**Threat model:** Attacker extends an expiring certificate by modifying `expires_at`.

**`expires_at` is canonical field 10 (present in both v1 and v2 schema).**
Modification breaks the SHA3-256 hash → Check 1 fails.

**Code path:** `_compute_content_hash()` → `json.dumps(canonical, sort_keys=True)` includes `expires_at`.

**Verdict:** DETECTED — hash mismatch immediately catches the tampered TTL.  
**Severity: CRITICAL** — a successful bypass would grant perpetual certificate validity.

---

### A06 — Replace `pqc_signature`

**Threat model:** Attacker replaces the signature with a forged value to re-anchor a tampered certificate.

**Attack vectors tested:**
- Replace with random hex: `ML-DSA-65:deadbeef0000...`
- Replace with valid ML-DSA-65 sig over different data
- Replace with valid STUB: `STUB-SHA3-256:<hash>`

**Code path (`_verify_pqc_signature` in pogr_blueprint.py):**
```python
# Line 219: format check
if not sig_str.startswith("ML-DSA-65:"):
    return (None, "⚠ Signature format unrecognised")  # STUB → None, not False

# Lines 233-237: cryptographic verification
verifier.verify(payload, sig_bytes, pk_bytes)
# → raises ValueError if invalid → returns (False, "✗ ML-DSA-65 signature INVALID")
```

**Verdict:** DETECTED — any replacement that is not a valid ML-DSA-65 signature over the
*original canonical payload* using OMNIX's private key will fail verification.

**Caveat (links to X02):** If `OMNIX_SIGNING_PUBLIC_KEY_B64` is absent from the environment,
the API returns `(None, "⚠ key not configured")` → valid stays True. This is a separate
finding (X02).

---

### A07 — Replay Expired Certificate

**Threat model:** Attacker presents a certificate that has passed its `expires_at` date.

**All three channels enforce TTL independently:**
- API: `_verify_certificate_core()` L307–311 compares `now > expires_at`
- Web: same kernel via `_verify_certificate_core()`
- Offline: `verify_pogc_offline.py` L289–297 computes `now < expires_at`

Importantly, `expires_at` is a **canonical field** — an attacker cannot modify it
without breaking the hash/sig. The verifier checks *both* the cryptographic binding
and the TTL independently.

**Verdict:** DETECTED on all three channels.

---

### A08 — Replay Revoked Certificate (v1 Schema) ← BYPASSED

**Threat model:** Certificate was issued as canonical_version=1, then revoked.
Attacker uses a pre-revocation export (JSON file where `status=ACTIVE`).

**Root cause:**

`_CANONICAL_V1` (10 fields) does NOT include `status` or `revoked_at`:
```python
_CANONICAL_V1 = [
    "pogc_id", "session_id", "ctchc_seal_hash",
    "issuer", "subject_org", "agent_id",
    "compliance_tier", "mandate_certification",
    "issued_at", "expires_at",
]
```

In the v1 schema, `status=ACTIVE` in the exported JSON is NOT bound to any
cryptographic proof. Revocation in the live DB updates `status=REVOKED` in the
DB row, but a previously exported JSON file still carries `status=ACTIVE`.

**Offline attack flow:**
1. Export cert before or during active period: `status=ACTIVE` in file
2. Cert is revoked in registry
3. Run offline verifier against stale file
4. Check 2 reads `cert.get("status")` = `ACTIVE` from file → PASSES
5. Check 1 recomputes hash over v1 fields (no status) → PASSES
6. PQC over v1 canonical (no status) → PASSES or WARNING
7. **Result: VALID verdict from offline verifier**

**Scope:** This bypass is **offline only**. Both the API (`/v1/pogr/verify`) and
the web page (`/pogr/verify`) read from the live DB — they always show the current
REVOKED status correctly.

**Mitigating controls already in place:**
- Export endpoint includes `status_warning` for v1 certs (pogr_blueprint.py L651–658)
- Offline verifier Check 7 emits a WARNING for v1 certs
- `CURRENT_CANONICAL_VERSION = 2` — new certs are v2; no new v1 certs can be issued
- POGC-GENESIS-E071CC96 is v1 (see Remediation Plan)

**Residual risk:** Any pre-existing v1 certificate can be presented as ACTIVE offline
after revocation, indefinitely, until the certificate expires via TTL (12 months).

---

### A09 — Export JSON Tampering + Offline Verify

**Threat model:** Attacker downloads the export JSON, modifies any field, and runs
the offline verifier against it.

**Attack flow for any canonical field (e.g., `mandate_certification`):**
```python
cert["mandate_certification"] = "MANDATE-BOUND"
# content_hash now MISMATCHES → Check 1 FAILS → overall_valid = False
```

**Attack flow with content_hash recomputed:**
```python
canonical = {k: cert.get(k) for k in CANONICAL_V2}
canonical["mandate_certification"] = "MANDATE-BOUND"
cert["mandate_certification"] = "MANDATE-BOUND"
cert["content_hash"] = "sha3-256:" + sha3_256(json.dumps(canonical, sort_keys=True, separators=(",",":")).encode()).hexdigest()
# pqc_signature still points to original payload → PQC Check 4 FAILS
```

**Verdict:** DETECTED — the attacker cannot forge a valid ML-DSA-65 signature without
OMNIX's private key. Hash alone is not sufficient. See X03 for the sim-forgery variant.

---

### A10, A11, A12 — Channel Consistency Attacks

**Threat model:** Web, API, and Offline produce different verdicts for the same certificate.

**Analysis:**
ADR-205 specifically addresses this by mandating a **single authoritative verification kernel**:
`_verify_certificate_core()` in `pogr_blueprint.py` is called by both the JSON API endpoint
(`/v1/pogr/verify`) and the HTML page (`/pogr/verify`).

The React `PoGRVerifyPage.tsx` fetches from `/v1/pogr/verify/<id>` — it calls the same
JSON API. There is no independent client-side verification logic in the React layer.

The offline verifier (`verify_pogc_offline.py`) uses identical canonical field definitions
(`CANONICAL_V1` / `CANONICAL_V2`), the same SHA3-256 formula, and the same ML-DSA-65
verification path.

**Verdict:** DETECTED — no inconsistency found across channels for standard verification.
See X02 for the API key-absent edge case.

---

### A13 — Missing Mandatory Fields

**Threat model:** Attacker crafts a certificate JSON with null or absent mandatory fields.

**Attack example:**
```json
{ "pogc_id": null, "issuer": null, "content_hash": null }
```

**Code path:** `_compute_content_hash()` calls `cert.get(k)` → returns `None` for missing fields.
This produces a different canonical payload from the original → hash mismatch → Check 1 FAILS.

Additionally, Check 5 (issuer identity) explicitly fails for null issuer.

**Verdict:** DETECTED — null/missing canonical fields produce hash mismatches. The canonical
field set acts as a structural schema enforcer.

---

### A14 — Extra Malicious Injected Fields

**Threat model:** Attacker injects extra fields in the JSON to influence downstream parsers
(JSON injection, prototype pollution, SSRF payloads).

**Code path:** `_canonical_fields()` uses an **explicit allowlist**:
```python
fields = _CANONICAL_V2 if version >= 2 else _CANONICAL_V1
for k in fields:
    result[k] = data.get(k)
```

Extra fields are never included in the canonical payload used for hashing or signing.
They are ignored completely during verification.

**Verdict:** DETECTED — allowlist canonicalization prevents shadow-field injection.
Extra fields pass through to the JSON response but carry no cryptographic weight.

---

### A15 — POGC ID Collision Attempt

**Threat model:** Attacker predicts or brute-forces a future POGC ID to pre-register
a malicious certificate or cause a primary-key collision.

**Implementation:**
```python
def _pogc_id() -> str:
    return "POGC-" + secrets.token_hex(8).upper()
```

`secrets.token_hex(8)` = 8 bytes = 64 bits of CSPRNG entropy.

**Collision probability analysis:**
- Birthday bound: ~50% collision probability at 2^32 ≈ 4 billion certificates
- Prediction difficulty: `secrets` module uses OS entropy source (`/dev/urandom`)
- DB enforcement: `pogc_id TEXT PRIMARY KEY` — INSERT fails on duplicate

**Current risk at scale:** Negligible (registry currently holds O(1) certificates).
**Forward-looking risk:** Below NIST SP 800-90B recommendation of 128-bit entropy
for cryptographic identifiers.

**Verdict:** DETECTED at DB level. Severity MEDIUM for future scale.

---

### X01 — admin_resign Unauthenticated (Additional Finding) ← CRITICAL BYPASS

**Threat model:** Attacker calls the admin endpoint to re-sign any certificate.

**Endpoint:** `POST /v1/pogr/admin/resign/<pogc_id>`

**Authentication mechanism:**
```python
expected_token = hashlib.sha3_256(
    f"POGR-RESIGN:{pogc_id}".encode()
).hexdigest()
provided_token = request.headers.get("X-Admin-Resign-Token", "").strip()
if not provided_token or provided_token != expected_token:
    return _err("Invalid or missing X-Admin-Resign-Token", 403)
```

**Proof of derivability:**
```
pogc_id:   POGC-GENESIS-E071CC96
token:     sha3_256("POGR-RESIGN:POGC-GENESIS-E071CC96") = 40a08a86d53e9060687e...
```

The "secret" token has **zero secret component**. Any party with access to the source
code (publicly auditable) can compute the admin token for any certificate ID.

**Current impact:**
The endpoint re-signs using data from the DB (not from the request body), and
requires `OMNIX_SIGNING_SECRET_KEY_B64` to be present. Today, the attacker can
only trigger a re-sign of OMNIX's own data with OMNIX's own key — no data is
altered. The net effect is limited.

**Architectural impact (CRITICAL):**
1. There is no meaningful authentication on an admin endpoint
2. Any future modification to read fields from the request body → immediate full forgery
3. A regulatory auditor (EU AI Act Art. 9, SOC-2-AI) reviewing the source code
   will classify this as a CRITICAL finding without appeal
4. The endpoint is permanently discoverable via public source code

**Verdict:** CRITICAL — architectural failure. The token provides zero security benefit.

---

### X02 — API PQC Verification Soft-Fail When Key Absent ← HIGH BYPASS

**Code path:**
```python
# _verify_pqc_signature() in pogr_blueprint.py, line 222-226:
pk_b64 = os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64")
if not pk_b64:
    return (None,
            "⚠ Platform public key not configured (OMNIX_SIGNING_PUBLIC_KEY_B64) "
            "— PQC cryptographic verification skipped; hash integrity still enforced")
```

A return of `(None, ...)` does **not** set `valid = False` (line 320–321 of blueprint):
```python
if pqc_ok is False:  # ← only False triggers failure; None is a warning
    valid = False
```

**Impact:**
- If `OMNIX_SIGNING_PUBLIC_KEY_B64` is missing (misconfiguration, restart, env loss):
  The API returns `{"valid": true}` for any certificate that:
  (a) has a matching content hash, AND
  (b) carries an `ML-DSA-65:` prefixed signature (even a random one)
- The system silently degrades from **asymmetric cryptographic proof** to
  **symmetric hash integrity** without logging a CRITICAL alert

**Distinction from offline verifier:**
The offline verifier's Path C (no key, real sig format, no sim match) returns
`(False, "PQC signature UNVERIFIABLE")` — a HARD FAIL.
The API's equivalent path returns `(None, "⚠ key not configured")` — a WARNING.

**This creates a channel inconsistency under the key-absent condition.**

---

### X03 — Offline Sim-Forgery Path ← HIGH BYPASS

**The AUDIT-PQC-SIM-V2 formula is in public source code.**

```python
# verify_pogc_offline.py, line 200:
expected_sim = hashlib.sha3_256(b"AUDIT-PQC-SIM-V2:" + payload).hexdigest()
if sig_hex == expected_sim:
    return (None, "SHA3-256 audit simulation verified ...")
```

**Attack vector:**

An attacker can craft a complete, forged certificate JSON that passes the offline
verifier with `overall_valid = True` in environments without `oqs-python`:

```python
import hashlib, json

forged = {
    "pogc_id": "POGC-XXXXXXXXXXXXXXXX",
    "session_id": "...",
    "ctchc_seal_hash": "...",
    "issuer": "OMNIX QUANTUM LTD",
    "subject_org": "Attacker Corp",
    "agent_id": "...",
    "compliance_tier": "ATF-BEV-Compliant",
    "mandate_certification": "MANDATE-BOUND",
    "issued_at": "2026-01-01T00:00:00+00:00",
    "expires_at": "2027-01-01T00:00:00+00:00",
    "status": "ACTIVE",
    "revoked_at": None,
    "canonical_version": 2,
    # ...
}
fields = ["pogc_id","session_id","ctchc_seal_hash","issuer","subject_org","agent_id",
          "compliance_tier","mandate_certification","issued_at","expires_at","status","revoked_at"]
canonical = {k: forged.get(k) for k in fields}
payload = json.dumps(canonical, sort_keys=True, separators=(",",":")).encode()
forged["content_hash"] = "sha3-256:" + hashlib.sha3_256(payload).hexdigest()
sim_sig = hashlib.sha3_256(b"AUDIT-PQC-SIM-V2:" + payload).hexdigest()
forged["pqc_signature"] = "ML-DSA-65:" + sim_sig  # passes Path B
```

**Offline verifier verdict against forged cert (without oqs):**
- Check 1 (hash): ✓ PASS — hash recomputed matches
- Check 2 (status): ✓ PASS — `ACTIVE`
- Check 3 (TTL): ✓ PASS — not expired
- Check 4 (PQC): ⚠ WARNING — sim path matched
- Check 5 (issuer): ✓ PASS
- Check 6 (mandate): ✓ PASS (`MANDATE-BOUND`)
- Check 7 (version): ✓ PASS (v2)
- `overall_valid = all(passed is not False for ...)` → **True** (None is not False)

**Verdict:** BYPASSED. A forged certificate shows as VALID with a WARNING in environments
without `oqs-python`. The warning text is explicit, but `overall_valid = True` and
the exit code is `0`.

**Mitigating factor:** Production certs exported from the API embed the real ML-DSA-65
public key in `_offline_verification.platform_public_key_b64`. Any verifier with
`oqs-python` installed and the embedded key will fail the forged cert via Path A.
The bypass only affects environments without `oqs-python`.

**Scope:** This finding explains why the sim path must be strictly opt-in, not default.

---

### X04 — revocation_proof Not Cryptographically Verified ← MEDIUM BYPASS

**Code path:**
```python
# pogr_blueprint.py, line 935-941:
proof = (body.get("revocation_proof") or "").strip()
if not proof:
    return _err("revocation_proof is required (PoGR-INV-006: PQC-signed revocation payload)")
```

The `revocation_proof` field is stored in the DB but **never verified**. Any non-empty
string is accepted as a valid proof. PoGR-INV-006 states:
> "Revocation requires PQC proof from original issuer"

The invariant is enforced at the identity level (API key must match `subject_org_id`)
but not at the cryptographic level. The "PQC-signed revocation payload" is a stub —
it is stored but not parsed, not verified against the platform key, and not cross-checked
against the original certificate.

**Impact:** The revocation audit trail contains unverified proof strings. A downstream
regulator or auditor who reads a revocation record cannot verify that the proof was
legitimate. Under EU AI Act Art. 17 (risk management system), this weakens the
non-repudiation guarantee of revocation events.

---

## Final Summary

| Metric | Count |
|---|---|
| **Total attacks executed** | 19 (15 specified + 4 additional) |
| **Detected** | 15 |
| **Bypassed** | 4 (A08 · X01 · X02 · X03) |
| **Critical** | 1 (X01) |
| **High** | 4 (A01 · A02 · X02 · X03) |
| **Medium** | 3 (A07 · A08 · X04) |
| **Low** | 3 (A10–A14) |

## Production-Ready Criteria

PoGR is **NOT YET** production-ready per the defined criteria:

| Criterion | Status |
|---|---|
| 0 Critical findings | ❌ 1 Critical (X01) |
| 0 High findings | ❌ 4 High (A01 variant, X02, X03) |
| Web = API = Offline | ⚠ Inconsistency under key-absent condition (X02) |
| No certificate forgery path | ❌ Forgery possible offline without oqs (X03) |

See `POGR_REMEDIATION_PLAN.md` for exact code changes required.
