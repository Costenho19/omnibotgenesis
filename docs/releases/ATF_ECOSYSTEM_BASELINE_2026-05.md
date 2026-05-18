# ATF Ecosystem Baseline 2026.05
## OMNIX QUANTUM LTD — Institutional Governance Architecture Snapshot

**Document ID:** OMNIX-ATF-BASELINE-2026-05  
**Classification:** PUBLIC — Institutional Reference  
**Date:** May 18, 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Registered:** England & Wales · 71-75 Shelton Street, Covent Garden, London WC2H 9JQ  
**Operational HQ:** Abu Dhabi, UAE  
**Canonical URL:** omnixquantum.net  
**Status:** FROZEN — Institutional Baseline Snapshot

---

> This document is a point-in-time snapshot of the OMNIX Agent Trust Fabric ecosystem as of May 18, 2026.
> It is intended for institutional review, regulatory reference, investor due diligence, and academic citation.
> All counts, DOIs, hashes, and version identifiers in this document are authoritative for this date.

---

## 1. Ecosystem Identity

| Field | Value |
|---|---|
| Ecosystem Name | OMNIX Agent Trust Fabric (ATF) |
| Baseline Identifier | OMNIX-ATF-BASELINE-2026-05 |
| Governance Baseline Cross-Reference | GOVERNANCE_BASELINE-2026-Q2-001 |
| Organization | OMNIX QUANTUM LTD |
| Founder / Chief Architect | Harold Nunes |
| Jurisdiction | England & Wales (registered) · Abu Dhabi UAE (operations) |
| Snapshot Date | May 18, 2026 |
| Architecture Freeze Status | ACTIVE — Frozen as of May 9, 2026 |

---

## 2. RFC Stack — Canonical Publication Record

| RFC | Title | Zenodo DOI | Figshare DOI | Status |
|---|---|---|---|---|
| RFC-ATF-1 | Agent Trust Fabric — Delegation Protocol with Post-Quantum Signatures (ML-DSA-65 / NIST FIPS 204) | [10.5281/zenodo.20155016](https://doi.org/10.5281/zenodo.20155016) | [10.6084/m9.figshare.32308077](https://doi.org/10.6084/m9.figshare.32308077) | ✅ Published |
| RFC-ATF-2 | Agent Trust Fabric — Runtime Governance Continuity | [10.5281/zenodo.20241344](https://doi.org/10.5281/zenodo.20241344) | [10.6084/m9.figshare.32308095](https://doi.org/10.6084/m9.figshare.32308095) | ✅ Published |
| RFC-ATF-3 | Agent Trust Fabric — Governance Policy Interoperability, Evidence Lifecycle & Forensic Verification Protocol | [10.5281/zenodo.20247342](https://doi.org/10.5281/zenodo.20247342) | [10.6084/m9.figshare.32308119](https://doi.org/10.6084/m9.figshare.32308119) | ✅ Published |
| RFC-ATF-4 | Semantic Governance Interoperability Protocol (SGIP) | — | — | 🔲 Proposed — ADR-171 |

All published RFCs are deposited under permanent DOIs and licensed CC BY 4.0.
Zenodo deposits are immutable. Figshare deposits are versioned.

---

## 3. Invariant Registry — May 18, 2026

**Total active invariants: 47**  
**Total proposed invariants: 4 (SGIP family — pending next baseline revision)**  
**Grand total specified: 51**

| Family | ID Range | Count | Governing Document | Status |
|---|---|---|---|---|
| ATF | ATF-INV-001–006 | 6 | RFC-ATF-1 · ADR-156 | ✅ Active |
| TAR | TAR-INV-006 | 1 | ADR-157 rev.2 | ✅ Active |
| RGC | RGC-INV-001–008 | 8 | RFC-ATF-2 · ADR-159 | ✅ Active |
| GPIL | GPIL-INV-001–003 | 3 | RFC-ATF-3 · ADR-161 | ✅ Active |
| ELR | ELR-INV-001–004 | 4 | RFC-ATF-3 · ADR-163 | ✅ Active |
| EAP | EAP-INV-001–007 | 7 | RFC-ATF-3 · ADR-163 | ✅ Active |
| OEP | OEP-INV-001–006 | 6 | RFC-ATF-3 · ADR-165 | ✅ Active |
| FEA | FEA-INV-001–005 | 5 | RFC-ATF-3 · ADR-166 | ✅ Active |
| FVP | FVP-INV-007 | 1 | RFC-ATF-3 · ADR-164/167 | ✅ Active |
| GECR | GECR-INV-001–006 | 6 | ADR-170 | ✅ Active |
| **TOTAL ACTIVE** | | **47** | | |
| SGIP | SGIP-INV-001–004 | 4 | ADR-171 | 🔲 Proposed |
| **GRAND TOTAL** | | **51** | | |

**Invariant coverage (active 47):**
- Direct test coverage: 41/47 (87.2%)
- Structural enforcement only: 6/47 (12.8%)
- Zero coverage: 0/47 (0.0%)

Full traceability: `docs/compliance/INVARIANT_TEST_MATRIX.md`

---

## 4. Architecture Decision Records

**Total ADRs as of this baseline: 171**

| Range | Scope | Notable |
|---|---|---|
| ADR-001–100 | Core governance pipeline, receipts, AVM, PQC infrastructure | ADR-028 (pipeline), ADR-060 (PQC), ADR-074/120 (AVM) |
| ADR-101–150 | Execution integrity, context governance, LLM isolation, scope authorization | ADR-144 (AMG), ADR-147 (SAR), ADR-151 (MCA) |
| ADR-151–160 | ATF stack foundation layers | ADR-154 (GCR), ADR-155 (TCC), ADR-156–159 (ATF L1–L3) |
| ADR-161–170 | Interoperability, evidence lifecycle, forensic verification, GECR | ADR-161 (GPIL), ADR-163 (EAP), ADR-165 (OEP), ADR-170 (GECR) |
| ADR-171 | Semantic Governance Interoperability Protocol (SGIP) — Layer 4 | ADR-171 |

Full index: `docs/ARCHITECTURE_INDEX.md`

---

## 5. Compliance Designation Stack

```
ATF-RGC-Compliant                    RFC-ATF-2 · 8 invariants satisfied
  └─ ATF-GPI-Aligned                 ADR-161 · valid CRGC established
       └─ ATF-SGIP-Aligned           ADR-171 · valid SAC + full Core Term Set
                                     [PROPOSED — pending RFC-ATF-4]
```

**Current highest production designation: ATF-GPI-Aligned**  
**ATF-SGIP-Aligned:** specified, not yet in conformance suite

---

## 6. Interoperability Stack

| Layer | Scope | Mechanism | Document |
|---|---|---|---|
| L1 — Cryptographic | ML-DSA-65 signature verification | Unconditional. Binary pass/fail. | RFC-ATF-1 §7.6 |
| L2 — Protocol | CES formula, invariant table, threshold definitions | Fixed. Zero variability. | RFC-ATF-2 §6 |
| L3 — Governance Policy | 6 parametric divergence surface dimensions | Bounded. CRGC coordinates alignment. | ADR-161 / RFC-ATF-3 §21 |
| L4 — Semantic | 8 ATF Core Term definitions | Sovereign + declared. SAC maps alignment. | ADR-171 [proposed] |

---

## 7. Cryptographic Infrastructure

| Property | Value |
|---|---|
| Signing algorithm | ML-DSA-65 (CRYSTALS-Dilithium, FIPS 204) |
| NIST standardization | August 2024 |
| Security level | AES-192 equivalent against quantum adversaries |
| Signature size | 3293 bytes |
| Public key size | 1312 bytes |
| Hash algorithm | SHA-256 with `sha256:` prefix over canonical JSON (sort_keys=True) |
| Key publication | `/api/forensic/platform-key` · `_omnix-key.omnixquantum.net` TXT · Zenodo DOI 10.5281/zenodo.20155016 |
| Key rotation policy | ADR-154 §5 — rotation produces new GCR; prior receipts remain verifiable |

---

## 8. Test Suite Summary

| Suite | Tests | Status | Governing |
|---|---|---|---|
| `test_governance_integrity.py` | 124 | ✅ PASS | INV-001–006 + pipeline |
| `test_code_verification.py` | 27 | ✅ PASS | Module imports + syntax |
| `test_critical_audit.py` | 16 | ✅ PASS | Safe-float, exception handling |
| `test_atf_receipts.py` | — | ✅ PASS | ATF-INV-001–006 |
| `test_conformance_vectors.py` | 37 | ✅ PASS | Cross-language canonical JSON |
| `test_eap_extended_audit.py` | 58 | ✅ PASS (4 skip) | EAP/OEP/FEA/FVP invariants |
| `test_tar_inv006_staleness_bound.py` | 23 | ✅ PASS | TAR-INV-006 |
| `test_response_validator.py` | 27 | ✅ PASS | Response validation |
| `test_systemic_router.py` | — | ✅ PASS | Systemic routing |
| **Total** | **245+** | **✅ ALL PASS** | |

**Pending:** `tests/test_sgip_audit.py` — not yet created (SGIP proposed)

---

## 9. Audit Trail

| Document | Date | Scope | Verdict |
|---|---|---|---|
| `ATF_EAP_OEP_INSTITUTIONAL_AUDIT_2026-05.md` | May 2026 | ATF/EAP/OEP full stack | PASS |
| `DAILY-ATF-OMNIX-AUDIT-2026-05-18.md` | May 18, 2026 | ADR-171, SGIP, count consistency | PASS WITH WARNINGS |
| `INVARIANT_TEST_MATRIX.md` (rev.3) | May 17, 2026 | 47-invariant coverage matrix | 87.2% direct |

---

## 10. Ecosystem Freeze Status

This baseline snapshot is frozen as of May 18, 2026. The following actions are in effect:

| Action | Status |
|---|---|
| New invariant families (active) | 🔒 FROZEN — next revision: baseline 2026-Q3 |
| New core RFC publication | 🔒 FROZEN — RFC-ATF-4 (SGIP) in specification phase |
| ADR filing | ✅ OPEN — new ADRs may be filed; no invariant changes |
| Frontend cosmetic updates | ✅ OPEN |
| Test coverage improvements | ✅ OPEN — priority: P1–P6 from invariant matrix |
| SGIP implementation | 🔲 PENDING — `omnix_core/agents/atf/semantic_governance.py` |

---

## 11. Priority Record

The OMNIX Agent Trust Fabric protocol stack — comprising RFC-ATF-1, RFC-ATF-2, RFC-ATF-3, ADR-156 through ADR-171, and the ATF-SGIP-Aligned designation — represents an original contribution to post-quantum governance infrastructure by Harold Nunes, OMNIX QUANTUM LTD, Abu Dhabi UAE / London UK.

First publication: RFC-ATF-1, Zenodo, DOI 10.5281/zenodo.20155016  
Ecosystem baseline snapshot: this document — OMNIX-ATF-BASELINE-2026-05  
Layer 4 specification (SGIP): ADR-171, May 18, 2026

---

*OMNIX QUANTUM LTD — Decision Governance Infrastructure*  
*Baseline: OMNIX-ATF-BASELINE-2026-05 · May 18, 2026 · omnixquantum.net*
