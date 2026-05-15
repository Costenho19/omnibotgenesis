# OMNIX Platform Public Key Registry

**Document ID:** OMNIX-SEC-2026-001-A  
**Classification:** PUBLIC — distribute freely  
**Owner:** Harold Nunes — OMNIX QUANTUM LTD (UK)  
**Operative Headquarters:** UAE  
**Last Updated:** 2026-05-15  
**ADR Reference:** ADR-167  
**Status:** ACTIVE

---

## 1. Purpose

This document is the canonical institutional reference for the OMNIX platform public key fingerprint used to sign all COLD Evidence Archive blocks and OMNIX Evidence Package (OEP) files.

Its purpose is to allow any party — auditor, regulator, counterparty, or independent verifier — to confirm that an OEP or archive block they have received was genuinely signed by OMNIX QUANTUM LTD, and not by an unrelated party.

This is not a technical implementation guide. It is the institutional trust anchor record.

---

## 2. Platform Key Specification

| Property | Value |
|---|---|
| **Algorithm** | ML-DSA-65 (Module-Lattice Digital Signature Algorithm, Level 5) |
| **Standard** | FIPS 204 — Module-Lattice-Based Digital Signature Standard |
| **Public key size** | 1,952 bytes |
| **Security level** | NIST Level 3 (≥ 128-bit post-quantum security) |
| **Signature size** | 3,309 bytes |
| **Scheme family** | Dilithium (Crystals) — NIST PQC Round 3 winner |

### 2.1 Current Active Fingerprint

```
CURRENT_FINGERPRINT: <retrieve from /api/forensic/platform-key at first deployment>
```

> **Note for operators:** The fingerprint above is populated automatically by querying
> `GET https://omnixquantum.net/api/forensic/platform-key` and copying the `fingerprint` field.
> This must be done after the first Railway deployment with `OMNIX_SIGNING_PUBLIC_KEY_B64` set.
> Once established, commit the fingerprint here and do not change it until a formal key rotation.

**Fingerprint format:** `sha256:` followed by the lowercase hex SHA-256 digest of the raw public key bytes (after base64 decoding of `OMNIX_SIGNING_PUBLIC_KEY_B64`).

**Example format:** `sha256:a3f4b2c1d0e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3`

---

## 3. Verification Locations

The platform key fingerprint is verifiable through multiple independent channels. Auditors are encouraged to cross-check across at least two.

### 3.1 HTTP API (Primary — Machine-Readable)

```
GET https://omnixquantum.net/api/forensic/platform-key
```

Response (JSON):
```json
{
  "status": "active",
  "platform_name": "OMNIX QUANTUM LTD",
  "algorithm": "ML-DSA-65 (FIPS 204)",
  "fingerprint": "sha256:...",
  "fingerprint_short": "sha256:abcd1234…efgh5678",
  "canonical_verification_url": "https://omnixquantum.net/api/forensic/platform-key",
  "configured": true
}
```

No authentication required. The fingerprint is public information.

### 3.2 DNS TXT Record (Independent Channel — No HTTP Required)

```
Record name: _omnix-key.omnixquantum.net
Record type: TXT
Record value: omnix-key-fingerprint=sha256:<hex>
```

Query command:
```bash
dig TXT _omnix-key.omnixquantum.net +short
```

The DNS TXT record allows fingerprint verification entirely independent of the OMNIX platform HTTP infrastructure. A regulator or counterparty can verify the fingerprint even if omnixquantum.net is unreachable.

**DNS record update policy:** DNS TXT records are updated within 72 hours of any key rotation event. See section 7 of `KEY_ROTATION_RUNBOOK.md`.

### 3.3 Zenodo Permanent Archive

**DOI:** https://doi.org/10.5281/zenodo.20155016

The OMNIX ATF Research Package on Zenodo includes the platform public key file and its fingerprint as a time-stamped permanent record. Zenodo deposits are immutable — the fingerprint recorded there is forensically sound evidence of the key in use at submission time.

**Location in package:** `KEYS/platform_public_key.b64` + `KEYS/FINGERPRINT.txt`

### 3.4 Web Portal (Human-Readable)

```
https://omnixquantum.net/archive-verify
```

The Forensic Archive Verification Portal displays the current platform key fingerprint in a dedicated "Platform Trust Anchor" panel. When verifying an OEP, the portal automatically compares the embedded key against the live platform key and shows MATCH or MISMATCH.

---

## 4. OEP Package Fingerprint Verification

Every OMNIX Evidence Package (OEP, `.oep` extension) contains the signing public key at `KEYS/public_key.b64`. To verify that a package was signed by the OMNIX platform key:

### Step 1 — Compute the package key fingerprint

```python
import hashlib, base64

pk_b64 = open("KEYS/public_key.b64").read().strip()
pk_bytes = base64.b64decode(pk_b64)
pkg_fingerprint = "sha256:" + hashlib.sha256(pk_bytes).hexdigest()
print(f"Package key fingerprint: {pkg_fingerprint}")
```

### Step 2 — Retrieve the platform fingerprint

```bash
curl -s https://omnixquantum.net/api/forensic/platform-key | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('Platform fingerprint:', data['fingerprint'])
"
```

Or from DNS:
```bash
dig TXT _omnix-key.omnixquantum.net +short
```

### Step 3 — Compare

```python
platform_fingerprint = "<value from step 2>"

if pkg_fingerprint == platform_fingerprint:
    print("TRUST LEVEL: OMNIX PLATFORM KEY — block signed by OMNIX QUANTUM LTD")
else:
    print("TRUST LEVEL: EXTERNAL KEY — block NOT signed by the OMNIX platform key")
    print("The PASS verdict covers cryptographic validity only, not platform endorsement")
```

---

## 5. Trust Level Classification

| Condition | Trust Level | Meaning |
|---|---|---|
| Package key fingerprint matches platform fingerprint | `OMNIX_PLATFORM` | Signed by OMNIX QUANTUM LTD. Highest institutional trust. |
| Package key fingerprint does not match | `EXTERNAL` | Signed by a non-platform key. Cryptographic PASS is valid but not a platform endorsement. |
| Platform fingerprint unavailable (server not configured) | `UNVERIFIABLE` | Cannot determine trust level. Contact OMNIX QUANTUM LTD. |

**Critical distinction:** The OMNIX verification portal (`/api/forensic/verify`) verifies _cryptographic validity_ for any presented key. A `PASS` verdict against an external key means "the signature is mathematically valid for this key" — it does NOT mean "OMNIX QUANTUM LTD endorses this block." Only `key_identity.matches_platform === true` indicates genuine platform endorsement.

---

## 6. Embedding in OEP Packages

Every OEP generated by the platform includes the following fingerprint information:

**In `META/manifest.json`:**
```json
{
  "package_id": "OEP-...",
  "platform_key_fingerprint": "sha256:...",
  "platform_key_registry_url": "https://omnixquantum.net/api/forensic/platform-key",
  "key_trust_level": "OMNIX_PLATFORM"
}
```

**In `README.txt`:**
A "PLATFORM KEY VERIFICATION" section with the fingerprint, registry URL, and verification instructions.

**In `KEYS/public_key.b64`:**
The raw public key (base64 encoded) from which the fingerprint is derived.

---

## 7. Key Fingerprint History

| Version | Fingerprint | Valid From | Valid Until | Status |
|---|---|---|---|---|
| v1.0 | _\<populate at first deployment\>_ | 2026-05-15 | Active | ACTIVE |

**Policy:** Historical fingerprints are maintained in this table permanently. Evidence blocks verified against a superseded key retain their PASS status — see `KEY_ROTATION_RUNBOOK.md §8 (Backward Verification Policy)`.

---

## 8. Contact and Reporting

- **Platform owner:** Harold Nunes — OMNIX QUANTUM LTD
- **Web:** https://omnixquantum.net
- **Key compromise reporting:** Contact immediately via official channels. See `KEY_ROTATION_RUNBOOK.md §4`.
- **Fingerprint discrepancy reporting:** If the fingerprint in an OEP you hold does not match the current platform fingerprint and you believe your OEP is legitimate, contact OMNIX QUANTUM LTD with the package ID and signing date for investigation.

---

## 9. References

- ADR-167 — Forensic Hardening: Key Identity Registry, Distributed Block Sequencing & Verifier Determinism
- ADR-165 — OMNIX Evidence Package (OEP) Format  
- ADR-164 — Forensic Archive Verification Portal
- ADR-163 — Immutable Evidence Archive Pipeline
- RFC-ATF-1 — Agent Trust Fabric Formal Specification (Zenodo DOI: 10.5281/zenodo.20155016)
- `docs/security/KEY_ROTATION_RUNBOOK.md` — Key Rotation and Compromise Response Runbook
- FIPS 204 — NIST Module-Lattice-Based Digital Signature Standard
