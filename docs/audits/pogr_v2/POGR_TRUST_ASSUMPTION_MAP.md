# POGR Trust Assumption Map

**System:** OMNIX Proof of Governance Registry (PoGR)  
**Version:** 2.0 — Adversarial Audit  
**Date:** 2026-05-30  
**ADR References:** ADR-186 · ADR-205 · PoGR-INV-001–006

---

## Purpose

This document maps every trust assumption made by each verification channel of the
PoGR system. A trust assumption is an implicit belief that, if violated, produces
a security failure. Mapping these assumptions allows regulators, enterprise buyers,
and independent auditors to evaluate the system's security model precisely — without
relying on OMNIX's own assertions.

---

## Trust Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     TRUST HIERARCHY                                     │
│                                                                         │
│   Level 0 — Root Trust: OMNIX ML-DSA-65 Private Key                    │
│             (never leaves Railway; HSM recommended)                     │
│                                                                         │
│   Level 1 — Platform Trust: OMNIX_SIGNING_PUBLIC_KEY_B64                │
│             (published via HTTP manifest, DNS TXT, Zenodo DOI)          │
│             PoGR-INV-005: 3-channel redundancy                          │
│                                                                         │
│   Level 2 — Registry Trust: PostgreSQL append-only ledger               │
│             PoGR-INV-002: no DELETE, no UPDATE on core fields           │
│             (except revocation and admin_resign — see gaps)             │
│                                                                         │
│   Level 3 — Certificate Trust: content_hash + pqc_signature             │
│             Canonical fields cryptographically anchored                 │
│                                                                         │
│   Level 4 — Verification Trust: _verify_certificate_core()              │
│             Single shared kernel — API + HTML + offline                 │
│             ADR-205                                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Channel-by-Channel Trust Analysis

### Channel 1: JSON API — `GET /v1/pogr/verify/<pogc_id>`

| Assumption ID | Trust Assumption | Enforced? | Gap if Violated |
|---|---|---|---|
| T-API-01 | PostgreSQL DB is uncompromised | ✓ Railway managed | DB breach → all certs invalid |
| T-API-02 | `OMNIX_SIGNING_PUBLIC_KEY_B64` is correctly set | ⚠ No fail-closed | Key absent → PQC check becomes WARNING, valid=True |
| T-API-03 | `_verify_certificate_core()` is called for every response | ✓ ADR-205 | Verified in code |
| T-API-04 | Redis anti-replay is live | ⚠ Best-effort mode | Replay under dyno split-brain |
| T-API-05 | `canonical_version` field in DB is accurate | ✓ Enforced on INSERT | Tampered version → wrong field set used |
| T-API-06 | `status` field in DB reflects true revocation state | ✓ DB constraint | DB corruption only |
| T-API-07 | `admin_resign` endpoint is protected by a secret | ❌ **VIOLATED** | Derivable token (X01) |

**Implicit trust chain for API verification:**
```
Caller → OMNIX API → PostgreSQL (T-API-01)
                    → OMNIX_SIGNING_PUBLIC_KEY_B64 (T-API-02) — PARTIAL TRUST
                    → _verify_certificate_core() (T-API-03)
```

**Trust boundary violations detected:** T-API-02 (soft-fail), T-API-07 (derivable admin token)

---

### Channel 2: HTML Web Page — `GET /pogr/verify/<pogc_id>`

| Assumption ID | Trust Assumption | Enforced? | Gap if Violated |
|---|---|---|---|
| T-WEB-01 | Same PostgreSQL source as JSON API | ✓ Same `_get_db()` | N/A |
| T-WEB-02 | `_verify_certificate_core()` called (not a separate logic) | ✓ ADR-205 line 1101 | N/A |
| T-WEB-03 | HTML rendering does not silently drop failing checks | ✓ Jinja2 renders `notes` | Verified in code |
| T-WEB-04 | TLS termination is trusted (HTTPS) | ✓ Railway / Replit | MitM if TLS fails |
| T-WEB-05 | No client-side verification bypass via JavaScript | ✓ Jinja2 is server-side | N/A |
| T-WEB-06 | v1 warning displayed for legacy certs | ✓ line 324–330 in kernel | v1 warning shown to user |

**Trust boundary violations detected:** None. Web channel is the strongest channel.

---

### Channel 3: Offline Verifier — `scripts/verify_pogc_offline.py`

| Assumption ID | Trust Assumption | Enforced? | Gap if Violated |
|---|---|---|---|
| T-OFF-01 | `oqs-python` is installed | ⚠ Optional | No oqs → falls to sim path |
| T-OFF-02 | `platform_public_key_b64` is embedded in export or provided via `--platform-key` | ⚠ Optional | No key → sim path or UNVERIFIABLE |
| T-OFF-03 | AUDIT-PQC-SIM-V2 formula is not known to attacker | ❌ **VIOLATED** | Formula is in public source (X03) |
| T-OFF-04 | `status` field in exported JSON is current (v2 only) | ✓ v2 status bound | v1: status not bound (A08) |
| T-OFF-05 | `canonical_version` field in file is accurate | ⚠ Attacker-controlled | Downgrade from v2→v1 attack |
| T-OFF-06 | `overall_valid = all(passed is not False ...)` treats None as non-blocking | ⚠ Design choice | Warnings pass overall check |
| T-OFF-07 | Verifier binary/source is authentic (not tampered) | ⚠ SHA256 of verifier not published | Supply chain: attacker replaces verifier |

**Trust boundary violations detected:** T-OFF-03 (sim formula public), T-OFF-04 (v1 A08), T-OFF-05 (version downgrade).

#### T-OFF-05 — canonical_version Downgrade Attack (New Finding)

An attacker can modify `canonical_version: 2 → 1` in an exported JSON, then
modify `status` or `revoked_at` freely (those fields are not canonical in v1),
and recompute `content_hash` over v1 fields only. The sig check will then fail
(real ML-DSA-65 was over v2 fields), but in environments without `oqs`:
- Path B: sim check fails (sig was real ML-DSA-65, not sim)
- Path C: UNVERIFIABLE → HARD FAIL

**So T-OFF-05 does NOT produce a bypass today** — the PQC check still fails.
But it IS a trust assumption worth monitoring if the sim path is expanded.

---

### Channel 4: Export Endpoint — `GET /v1/pogr/certificate/<pogc_id>/export`

| Assumption ID | Trust Assumption | Enforced? | Gap if Violated |
|---|---|---|---|
| T-EXP-01 | Exported JSON is authentic at time of download | ✓ Served directly from DB | Transport-level only (HTTPS) |
| T-EXP-02 | `_export_metadata.status_warning` is read by verifier | ⚠ Warning only | Downstream tool ignores metadata |
| T-EXP-03 | Embedded `platform_public_key_b64` is the real platform key | ✓ Read from env at serve time | Env poisoning |
| T-EXP-04 | File is not modified after download | ⚠ No file hash published | File can be modified before offline verify |
| T-EXP-05 | `exported_at` timestamp is trusted | ⚠ No signature over metadata | Metadata fields are not in canonical set |

**Trust boundary violations detected:** T-EXP-04, T-EXP-05 — export metadata has no
cryptographic protection. An attacker can modify `_export_metadata` without affecting
the hash/sig of the certificate fields. The metadata fields are informational only.

---

### Channel 5: Revoke Endpoint — `POST /v1/pogr/revoke/<pogc_id>`

| Assumption ID | Trust Assumption | Enforced? | Gap if Violated |
|---|---|---|---|
| T-REV-01 | API key authenticates original issuing org | ✓ `subject_org_id == client["client_id"]` | Compromised API key |
| T-REV-02 | `revocation_proof` is a valid PQC-signed payload | ❌ **NOT VERIFIED** | Any non-empty string accepted (X04) |
| T-REV-03 | Revocation is permanent (append-only invariant) | ✓ PoGR-INV-002 status=REVOKED | DB breach |
| T-REV-04 | v2: content_hash re-signed after revocation | ✓ lines 975–997 of blueprint | Only if canon_version >= 2 |
| T-REV-05 | v1: content_hash NOT re-signed after revocation | ⚠ By design — creates A08 gap | See A08 |

---

## Trust Assumption Summary

| Gap | Channel | Trust Violated | Severity |
|---|---|---|---|
| X01 | Admin endpoint | T-API-07 | CRITICAL |
| X02 | JSON API | T-API-02 | HIGH |
| X03 | Offline verifier | T-OFF-03 | HIGH |
| A08 | Offline v1 | T-OFF-04 | MEDIUM |
| X04 | Revoke endpoint | T-REV-02 | MEDIUM |
| T-OFF-05 | Offline v2→v1 downgrade | T-OFF-05 | LOW (blocked by PQC) |
| T-EXP-04 | Export metadata | T-EXP-04 | LOW (metadata only) |

---

## Trust Assumptions That HOLD (Verified)

The following assumptions are **correctly enforced** and tested:

| Assumption | Mechanism |
|---|---|
| Canonical field tampering produces hash mismatch | `_compute_content_hash()` re-derives from fields |
| Hash + sig together cannot be forged without ML-DSA-65 private key | FIPS 204 EUF-CMA security |
| Web and API produce identical verdicts | Single `_verify_certificate_core()` kernel (ADR-205) |
| Registry is append-only (no silently deleted certs) | DB PRIMARY KEY + no DELETE path |
| TTL is cryptographically bound (expires_at in canonical set) | Field 10 of CANONICAL_V1/V2 |
| Revocation status is live on API (reads DB directly) | Server reads `status` from DB per request |
| DB-level schema constraints enforce valid enum values | `CHECK (status IN ('ACTIVE','EXPIRED','REVOKED'))` |

---

## Regulatory Trust Model (EU AI Act Art. 9 / SOC-2-AI)

For OMNIX's public claims that PoGR certificates are "verifiable by any third party without OMNIX access" to hold under regulatory scrutiny:

1. The platform public key must be available via at least 2 of the 3 declared channels (HTTP, DNS TXT, Zenodo) — **DNS and Zenodo channels are declared but not yet live**
2. The offline verifier must not produce `valid=True` for forged certificates — **violated by X03 in no-oqs environments**
3. Admin operations must be authenticated with a secret, not a derivable value — **violated by X01**
4. All PoGR invariants as published in RFC-ATF-1–6 must be machine-enforceable — **X04 violates PoGR-INV-006**

These gaps must be closed before presenting PoGR to regulators, enterprise security teams, or legal due-diligence processes.
