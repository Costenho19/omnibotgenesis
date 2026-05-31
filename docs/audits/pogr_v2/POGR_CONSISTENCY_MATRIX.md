# POGR Consistency Matrix — Web = API = Offline

**System:** OMNIX Proof of Governance Registry (PoGR)  
**Version:** 2.0 — Adversarial Audit  
**Date:** 2026-05-30  
**ADR Reference:** ADR-205 — "identical logic, identical verdict, across all three channels"

---

## Purpose

This matrix exhaustively compares the verdict produced by all three verification channels
for every meaningful certificate state and environmental condition. A discrepancy in any
cell represents a channel inconsistency — a violation of ADR-205's core guarantee.

---

## Legend

| Symbol | Meaning |
|---|---|
| ✅ | Channel returns VALID / verdict matches |
| ❌ | Channel returns INVALID / mismatched |
| ⚠ | Channel returns WARNING (valid=True with warning) |
| — | Not applicable for this channel |
| 🔴 | Inconsistency detected between channels |
| 🟢 | All channels consistent |

---

## Matrix Part 1 — Standard Certificate States

| Scenario | JSON API | HTML Web | Offline (oqs) | Offline (no oqs) | Consistent? |
|---|---|---|---|---|---|
| Valid active v2 cert, key configured | ✅ VALID | ✅ VALID | ✅ VALID | ⚠ VALID+warn | 🟢 |
| Revoked v2 cert (status in DB) | ❌ INVALID | ❌ INVALID | ❌ INVALID | ❌ INVALID | 🟢 |
| Revoked v2 cert, stale offline export | — | — | ❌ INVALID | ❌ INVALID | 🟢 (v2 bound) |
| Expired cert | ❌ INVALID | ❌ INVALID | ❌ INVALID | ❌ INVALID | 🟢 |
| STUB-signed cert (dev env) | ⚠ VALID+warn | ⚠ VALID+warn | ⚠ VALID+warn | ⚠ VALID+warn | 🟢 |
| Cert not found in registry | ❌ 404 | ❌ not found | — | — | 🟢 |

---

## Matrix Part 2 — Canonical Version Edge Cases

| Scenario | JSON API | HTML Web | Offline (oqs) | Offline (no oqs) | Consistent? |
|---|---|---|---|---|---|
| **v1 cert, ACTIVE** | ✅ VALID+warn | ✅ VALID+warn | ✅ VALID+warn | ⚠ VALID+warn | 🟢 |
| **v1 cert, revoked in DB** (server) | ❌ INVALID | ❌ INVALID | — | — | 🟢 |
| **v1 cert, revoked, stale offline export** | — | — | ⚠ **VALID+warn** | ⚠ **VALID+warn** | 🔴 A08 BYPASS |
| v2 cert, revoked, stale offline export | — | — | ❌ INVALID | ❌ INVALID | 🟢 |

**Key finding — A08:**
For v1 certificates, the API and Web (which read from DB) correctly report REVOKED.
But the offline verifier reading a pre-revocation export file reports VALID (with v1 warning).
This is an **offline-only channel inconsistency** for v1 certificates.

---

## Matrix Part 3 — Environmental Conditions

| Condition | JSON API | HTML Web | Offline (oqs) | Offline (no oqs) | Consistent? |
|---|---|---|---|---|---|
| Public key configured | ✅ Full PQC | ✅ Full PQC | ✅ Full PQC | — | 🟢 |
| Public key absent | ⚠ Hash-only | ⚠ Hash-only | ✅ Full PQC | ⚠ Sim/UNVERIFIABLE | 🔴 **X02** |
| oqs-python not installed | — | — | — | ⚠ Sim path | 🟢 (N/A) |
| Network unavailable | ❌ N/A | ❌ N/A | ✅ (from file) | ✅ (from file) | — |
| DB unavailable | ❌ 503 | ❌ 503 | ✅ (from file) | ✅ (from file) | — |

**Key finding — X02:**
When `OMNIX_SIGNING_PUBLIC_KEY_B64` is absent:
- API/Web: `valid = True` (PQC check returns Warning, not Fail)
- Offline with oqs: full ML-DSA-65 → fails if sig is invalid → `valid = False`
- **INCONSISTENCY: API says VALID, Offline (oqs) says INVALID for same cert with invalid sig**

---

## Matrix Part 4 — Tampered Certificate Fields

| Tampered Field | Canonical? | JSON API | HTML Web | Offline (oqs) | Offline (no oqs) | Consistent? |
|---|---|---|---|---|---|---|
| `pogc_id` | ✅ v1+v2 | ❌ hash fail | ❌ hash fail | ❌ hash fail | ❌ hash fail | 🟢 |
| `session_id` | ✅ v1+v2 | ❌ hash fail | ❌ hash fail | ❌ hash fail | ❌ hash fail | 🟢 |
| `ctchc_seal_hash` | ✅ v1+v2 | ❌ hash fail | ❌ hash fail | ❌ hash fail | ❌ hash fail | 🟢 |
| `issuer` | ✅ v1+v2 | ❌ hash+issuer fail | ❌ hash fail | ❌ hash+issuer fail | ❌ hash+issuer fail | 🟢 |
| `subject_org` | ✅ v1+v2 | ❌ hash fail | ❌ hash fail | ❌ hash fail | ❌ hash fail | 🟢 |
| `agent_id` | ✅ v1+v2 | ❌ hash fail | ❌ hash fail | ❌ hash fail | ❌ hash fail | 🟢 |
| `compliance_tier` | ✅ v1+v2 | ❌ hash fail | ❌ hash fail | ❌ hash fail | ❌ hash fail | 🟢 |
| `mandate_certification` | ✅ v1+v2 | ❌ hash fail | ❌ hash fail | ❌ hash fail | ❌ hash fail | 🟢 |
| `issued_at` | ✅ v1+v2 | ❌ hash fail | ❌ hash fail | ❌ hash fail | ❌ hash fail | 🟢 |
| `expires_at` | ✅ v1+v2 | ❌ hash fail | ❌ hash fail | ❌ hash fail | ❌ hash fail | 🟢 |
| `status` | ✅ **v2 only** | ❌ hash fail | ❌ hash fail | ❌ hash fail | ❌ hash fail | 🟢 v2 |
| `status` (v1) | ❌ **NOT canonical** | N/A (from DB) | N/A (from DB) | ⚠ not checked | ⚠ not checked | 🔴 **A08** |
| `revoked_at` | ✅ **v2 only** | ❌ hash fail | ❌ hash fail | ❌ hash fail | ❌ hash fail | 🟢 v2 |
| `content_hash` only | — | ❌ hash fail | ❌ hash fail | ❌ hash fail | ❌ hash fail | 🟢 |
| `content_hash` + fields | — | ❌ PQC fail | ❌ PQC fail | ❌ PQC fail | ❌ PQC/UNVER | 🟢 |
| Non-canonical: `subject_org_id` | — | ✅ (not canonical) | ✅ (not canonical) | ✅ (not canonical) | ✅ (not canonical) | 🟢 |
| Non-canonical: `turn_count` | — | ✅ (not canonical) | ✅ (not canonical) | ✅ (not canonical) | ✅ (not canonical) | 🟢 |
| Non-canonical: `avg_conformance` | — | ✅ (not canonical) | ✅ (not canonical) | ✅ (not canonical) | ✅ (not canonical) | 🟢 |
| Extra injected fields | — | ✅ (ignored) | ✅ (ignored) | ✅ (ignored) | ✅ (ignored) | 🟢 |

---

## Matrix Part 5 — Forged Certificates

| Forgery Type | JSON API | HTML Web | Offline (oqs) | Offline (no oqs) | Consistent? |
|---|---|---|---|---|---|
| Full fabrication (random sig) | ❌ INVALID | ❌ INVALID | ❌ INVALID | ❌ UNVERIFIABLE | 🟢 |
| Full fabrication + sim sig (X03) | ❌ (not in DB) | ❌ (not in DB) | ❌ (not in DB) | ⚠ **VALID+warn** | 🔴 **X03** |
| Transplanted sig from other cert | ❌ hash fail | ❌ hash fail | ❌ PQC fail | ❌ UNVERIFIABLE | 🟢 |

**Key finding — X03:**
A fully fabricated certificate with a sim-format signature is:
- Rejected by API/Web (certificate not in DB — 404)
- Rejected by offline verifier with oqs (ML-DSA-65 verify fails)
- **Accepted by offline verifier without oqs (sim path matches, VALID+warn)**

This inconsistency means a party who only has access to the offline verifier
in a no-oqs environment cannot distinguish a real cert from a well-crafted forgery.

---

## Matrix Part 6 — The ADR-205 Kernel Guarantee

ADR-205 mandates: "identical logic, identical verdict, across all three channels."

| Check | API uses same kernel as Web? | Offline uses same logic? |
|---|---|---|
| Content hash (SHA3-256) | ✅ `_verify_certificate_core()` | ✅ `_compute_content_hash()` — identical formula |
| Status check | ✅ Same code path | ✅ `cert.get("status")` |
| TTL check | ✅ Same code path | ✅ `now < expires_at` |
| PQC signature | ✅ `_verify_pqc_signature()` | ✅ `_verify_pqc_signature()` — mirrored |
| Issuer identity | ✅ In `notes` (via hash) | ✅ Explicit check + in hash |
| Mandate certification | ✅ In `notes` | ✅ Explicit check |
| Canonical version | ✅ Same field set selection | ✅ Same field set selection |

**The kernel guarantee holds under normal conditions.**
It breaks under the two environmental conditions: A08 (v1 offline) and X02 (no key).

---

## Inconsistencies Summary

| Finding | Channels Affected | Root Cause |
|---|---|---|
| **A08** | API vs Offline (v1) | v1 status not in canonical set |
| **X02** | API/Web vs Offline+oqs | API: None≠False; Offline: False on UNVERIFIABLE |
| **X03** | Offline+oqs vs Offline-nooqs | Sim path returns None (warning, not fail) |

---

## Path to Full Consistency

After applying all remediations in `POGR_REMEDIATION_PLAN.md`:

1. **R-H2** (X02): API fails closed when public key absent → API = Offline+oqs = Offline-nooqs
2. **R-H3** (X03): Sim path removed from default → Offline-nooqs = Offline+oqs
3. **R-H1** (A08): POGC-GENESIS re-issued as v2 → no v1 certs remain in registry

After R-H1 + R-H2 + R-H3:

> **Web = API = Offline (oqs) = Offline (no oqs)**  
> For all certificate states, under all environmental conditions.
