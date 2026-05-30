# OMNIX Independent Verification Guide

**Product:** Proof of Governance Registry (PoGR)  
**ADR:** ADR-186 · ADR-187 · ADR-205  
**Invariant:** PoGR-INV-003 — zero-trust verification  
**Version:** 1.0 · May 2026

---

## What This Verifies

This guide allows any third party to independently verify an OMNIX **Proof of Governance Certificate (PoGC)** without requiring access to OMNIX systems, accounts, APIs, or internal infrastructure of any kind.

The verifier checks six properties of any PoGC certificate:

| # | Check | What It Proves |
|---|---|---|
| 1 | **Content hash integrity** | No field was altered after issuance (SHA3-256) |
| 2 | **Certificate status** | ACTIVE — not revoked or expired |
| 3 | **TTL validity** | Not past its expiration date |
| 4 | **Post-quantum signature** | ML-DSA-65 (FIPS 204) — mathematically unforgeable |
| 5 | **Issuer authenticity** | Issued by OMNIX QUANTUM LTD |
| 6 | **Mandate certification** | AI agent operated within its stated mandate |

---

## Requirements

- **Python 3.8 or later** — standard library only for checks 1–3, 5–6 (no install needed)
- **oqs-python** — required for check 4 (ML-DSA-65 post-quantum cryptographic verification):

```
pip install oqs-python
```

---

## Step 1 — Download the Certificate

Request the exported certificate JSON from the public PoGR API (no authentication required):

```
GET https://omnixquantum.net/v1/pogr/certificate/<POGC-ID>/export
```

Example:

```bash
curl https://omnixquantum.net/v1/pogr/certificate/POGC-GENESIS-E071CC96/export \
     -o certificate.json
```

The exported file is self-contained. It includes:
- All certificate fields
- The canonical field schema used at signing time
- The platform public key (embedded for PQC verification)

---

## Step 2 — Download the Verifier

```bash
curl https://raw.githubusercontent.com/omnixquantum/omnix/main/scripts/verify_pogc_offline.py \
     -o verify_pogc_offline.py
```

Or copy it directly from the OMNIX repository: `scripts/verify_pogc_offline.py`

---

## Step 3 — Run the Verification

```bash
python verify_pogc_offline.py --file certificate.json
```

**Expected output (valid certificate):**

```
  ⬡  OMNIX Proof of Governance — Offline Certificate Verifier
     ADR-186 · ADR-189 · ADR-205 · PoGR-INV-003 · v2.0.0

  Certificate
  ID                        POGC-GENESIS-E071CC96
  Organization              OMNIX QUANTUM LTD
  Compliance tier           ATF-BEV-Compliant
  Mandate certification     MANDATE-BOUND
  Algorithm                 ML-DSA-65 · FIPS 204
  Canonical version         v2 (status bound ✓)

  Verification Checks
  ✓  Content hash (SHA3-256)
       Verified — sha3-256:4f2a…
  ✓  Certificate status
       ACTIVE (canonical_version=2)
  ✓  TTL validity
       Not expired — 300 days remaining (expires 2027-05-26)
  ✓  PQC signature (ML-DSA-65)
       ML-DSA-65 signature cryptographically verified (FIPS 204 / NIST 2024)
  ✓  Issuer identity
       OMNIX QUANTUM LTD
  ✓  Mandate certification
       MANDATE-BOUND — pristine fidelity (MIVP-INV-008 · ADR-194)
  ✓  Canonical schema version
       v2 — status and revoked_at are cryptographically bound

  ──────────────────────────────────────────────────────────

  STATUS        :  VALID

  TOTAL CHECKS  :  7
  PASSED        :  7
  FAILED        :  0

  ✅  CERTIFICATE VALID
  This governance certificate passed all offline verification checks.
```

---

## Result Interpretation

| Result | Meaning |
|---|---|
| **VALID** | The certificate is authentic, unmodified, active, and within its TTL. The AI session it references was governed correctly. |
| **WARNING** | The certificate is authentic, but contains non-blocking conditions (e.g. development signature, schema v1, or UNCERTIFIED mandate tier). |
| **INVALID** | The certificate has been altered, corrupted, revoked, expired, or cannot be authenticated. Do not rely on it. |

**Exit codes:**  
`0` = VALID or WARNING · `1` = INVALID · `2` = usage error

---

## Additional Verification Modes

**Machine-readable JSON output** (for CI/CD pipelines, audit systems):
```bash
python verify_pogc_offline.py --file certificate.json --json
```

**With explicit public key** (alternative to embedded key):
```bash
python verify_pogc_offline.py --file certificate.json --platform-key <base64-public-key>
```

**Download and verify in one command** (requires network):
```bash
python verify_pogc_offline.py POGC-GENESIS-E071CC96
```

---

## Cross-Verification

The same certificate can be independently verified through three channels — all three must return the same result:

| Channel | URL |
|---|---|
| **Web interface** | `https://omnixquantum.net/pogr/verify/<POGC-ID>` |
| **REST API** | `GET https://omnixquantum.net/v1/pogr/verify/<POGC-ID>` |
| **Offline verifier** | `python verify_pogc_offline.py --file certificate.json` |

PoGR-INV-003 mandates identical verdicts across all three channels (ADR-205 §6).

---

## What You Are NOT Required to Trust

This verification is designed to be trustless:

- No OMNIX account or API key required
- No access to OMNIX internal systems or databases
- No execution of OMNIX code — only Python standard library + oqs-python
- The platform public key is embedded in the exported certificate itself
- The verifier script contains no network calls when used with `--file`

The only trust anchor is the ML-DSA-65 post-quantum public key embedded in the certificate export. This key's fingerprint can be independently confirmed against the public manifest at `GET /v1/pogr/manifest`.

---

## Verification Contact

**OMNIX QUANTUM LTD**  
Decision Governance Infrastructure  
support@omnixquantum.net  
omnixquantum.net
