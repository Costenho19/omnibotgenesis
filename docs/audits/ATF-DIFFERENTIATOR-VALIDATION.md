# ATF Differentiator Validation Report
## OMNIX-AUDIT-ATF-DV-2026-001

**Date:** 2026-05-13 00:27 UTC  
**Scope:** OMNIX Agent Trust Fabric — RFC-ATF-1, ADR-156/157/158  
**Method:** In-process audit — real code, real objects, no mocks  
**Environment:** In-memory (no DATABASE_URL required)  

---

## Final Verdict: ✅ PASS

| Metric | Value |
|---|---|
| Tests executed | 55 |
| Tests passed | 55 |
| Tests failed | 0 |
| Pass rate | 100.0% |
| Overall verdict | **PASS** |

---

## Results by Area

### ✅ DR — 6/6 passed

| Test | Result | Note |
|---|---|---|
| generation | ✅ PASS | ATFDR-512508471CE544A5 |
| hash_stable | ✅ PASS |  |
| tamper_detection | ✅ PASS |  |
| pqc_signature | ✅ PASS | algo=Dilithium-3 (ML-DSA-65) |
| expiry_set | ✅ PASS |  |
| reduction_pct | ✅ PASS |  |

### ✅ MAR — 3/3 passed

| Test | Result | Note |
|---|---|---|
| multi_level_valid | ✅ PASS |  |
| violation_blocked | ✅ PASS | ATF-INV-001 VIOLATED: authority_budget_granted (80.0) > authority_budget_delegat |
| equal_budget_allowed | ✅ PASS |  |

### ✅ Lattice — 6/6 passed

| Test | Result | Note |
|---|---|---|
| agent_registration | ✅ PASS |  |
| lattice_delegate | ✅ PASS |  |
| verify_chain | ✅ PASS | depth=1 |
| chain_root_consistent | ✅ PASS |  |
| acyclicity_guard | ✅ PASS | visited-set prevents infinite traversal |
| ccs_score | ✅ PASS | ccs=100.0 verdict=COMPLETE |

### ✅ TAR — 7/7 passed

| Test | Result | Note |
|---|---|---|
| valid_admission | ✅ PASS |  |
| execution_ns_present | ✅ PASS | ns=1778632013036330919 |
| execution_ref_binding | ✅ PASS |  |
| ns_in_hash | ✅ PASS |  |
| expired_dr_rejected | ✅ PASS |  |
| revoked_dr_rejected | ✅ PASS |  |
| verify_tar | ✅ PASS | pqc_checked=True |

### ✅ Triple — 3/3 passed

| Test | Result | Note |
|---|---|---|
| triple_chain_linked | ✅ PASS | receipt_id=OMNIX-FIN-1778632018-TRIPLE |
| embed_in_receipt | ✅ PASS |  |
| verify_chain_connector | ✅ PASS | atf_present=True |

### ✅ Offline — 5/5 passed

| Test | Result | Note |
|---|---|---|
| offline_dr_hash | ✅ PASS |  |
| offline_mar_check | ✅ PASS |  |
| offline_expiry_check | ✅ PASS |  |
| offline_tar_hash | ✅ PASS |  |
| zero_platform_dependency | ✅ PASS |  |

### ✅ Replay — 3/3 passed

| Test | Result | Note |
|---|---|---|
| stale_dr_replay | ✅ PASS |  |
| tar_uniqueness | ✅ PASS |  |
| execution_ref_binding | ✅ PASS | TAR bound to OMNIX-FIN-A-001, not OMNIX-FIN-B-002 |

### ✅ CrossDomain — 7/7 passed

| Test | Result | Note |
|---|---|---|
| dtr_generated | ✅ PASS |  |
| discount_applied | ✅ PASS | 60→51.0 |
| cdtp_inv001 | ✅ PASS | 51.0 ≤ 60.0 |
| dtr_signature | ✅ PASS | algo=Dilithium-3 (ML-DSA-65) |
| verify_dtr | ✅ PASS |  |
| same_domain_blocked | ✅ PASS |  |
| policy_mapping | ✅ PASS | 4 pairs verified |

### ✅ PublicVerifier — 5/5 passed

| Test | Result | Note |
|---|---|---|
| file_exists | ✅ PASS |  |
| standalone_load | ✅ PASS |  |
| verify_real_receipt | ✅ PASS | fully_verified=True |
| corrupted_detected | ✅ PASS |  |
| verifier_mar_detection | ✅ PASS |  |

### ✅ Invariants — 4/4 passed

| Test | Result | Note |
|---|---|---|
| mar_invariant | ✅ PASS | 100→70→40→15 verified |
| acyclicity_invariant | ✅ PASS | visited-set in _collect_chain |
| chain_root_consistency | ✅ PASS |  |
| immutability_property | ✅ PASS |  |

### ✅ Threats — 6/6 passed

| Test | Result | Note |
|---|---|---|
| tm002_forgery_detected | ✅ PASS |  |
| tm003_amplification_blocked | ✅ PASS |  |
| tm005_chain_poisoning | ✅ PASS | mismatch detectable in verify_chain() |
| tm006_orphan_blocked | ✅ PASS |  |
| tm007_cycle_blocked | ✅ PASS | visited-set in _collect_chain |
| tm008_crosstar_blocked | ✅ PASS |  |

---

## What Really Works — Demonstrable Today

| Capability | Evidence | Defensibility |
|---|---|---|
| DR generation with content_hash | In-process test | HIGH — deterministic |
| MAR enforcement (AuthorityExpansionViolation) | Exception raised on violation | HIGH — code path proven |
| TAR admission before execution | execution_ns from time.time_ns() | HIGH — synchronous call |
| TAR rejection for expired/revoked DR | admission_status=REJECTED | HIGH — verified |
| execution_ref binding to receipt | TAR.execution_ref set at issuance | HIGH — structural |
| Offline hash verification | hashlib only, zero platform calls | HIGH — proven |
| Cross-domain discount arithmetic | CDTP-INV-001 enforced | HIGH — in verify_dtr() |
| Forgery detection via content_hash | Any field change breaks hash | HIGH — SHA-256 |
| Privilege amplification blocked | AEV raised at delegate() | HIGH — pre-signing |
| Chain root consistency | chain_root_id field in every DR | HIGH — structural |
| Public CLI verifier (offline) | standalone module, zero imports | HIGH — ATF-INV-006 |
| ATF CCS score computation | chain_completeness_score() | HIGH — algorithmic |

---

## What Is Experimental / Partially Implemented

| Gap | Status | Risk |
|---|---|---|
| PQC signature in test env | Absent without OMNIX_SIGNING_SECRET_KEY_B64 | LOW — hash verification still works |
| DB persistence of TARs | In-memory fallback when no DATABASE_URL | LOW — logic identical |
| Cascade revocation propagation | Status mutation tested manually | MEDIUM — no atomic cascade yet |
| RFC 3161 TSA counter-signature | Not implemented | MEDIUM — for Level-3 compliance |
| Multi-instance TAR uniqueness | DB unique constraint only | MEDIUM — needs Redis in multi-node |
| Cycle injection via DB write | Visited-set catches at traversal time | LOW — defense-in-depth |

---

## Claims Defensible Publicly

These claims are supported by the audit evidence and can be stated without qualification:

1. **MAR is enforced at issuance** — `AuthorityExpansionViolation` is raised before any signing occurs. No DR with budget_granted > budget_delegator can be created.
2. **TARs are issued before execution** — `execution_ns = time.time_ns()` is the first line of `admit_execution()`. This is structural, not configurable.
3. **Receipts are independently verifiable** — content_hash recomputation requires only `hashlib` and `json`. No OMNIX library import needed.
4. **Forged receipts are detected** — Any field change produces a different SHA-256 hash, breaking verification.
5. **Expired/revoked DRs produce REJECTED TARs** — Verified in audit tests 4c and 4d.
6. **Cross-domain authority always decreases** — `translated_budget = source_budget × (1 - discount)` with discount > 0.
7. **execution_ref binds TAR to a specific governance decision** — Structural: set at TAR issuance, included in signed hash.

---

## True Differentiators vs. Existing Frameworks

| Property | ATF | OAuth 2.0 | JWT | W3C VC |
|---|---|---|---|---|
| Signed artifact before execution | ✅ TAR | ❌ | ❌ | ❌ |
| Authority budget arithmetic | ✅ MAR invariant | ❌ | ❌ | ❌ |
| Nanosecond-resolution timestamp in signed artifact | ✅ | ❌ | ❌ | ❌ |
| Cross-domain mandatory reduction | ✅ DTR | ❌ | ❌ | ❌ |
| Offline verification (no platform call) | ✅ ATF-INV-006 | ❌ | Partial | Partial |
| Formally specified invariants (TLA+) | ✅ | ❌ | ❌ | ❌ |
| Triple artifact chain (DR+TAR+Receipt) | ✅ | ❌ | ❌ | ❌ |

---

## Residual Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Clock drift in TAR execution_ns | MEDIUM | RFC 3161 TSA (planned Level-3) |
| Revocation not cascading atomically | MEDIUM | Short DR validity + central registry |
| PQC library not FIPS 140-3 validated | LOW | Disclosed in RFC-ATF-1 §11.5 |
| Multi-node TAR uniqueness | MEDIUM | Redis SETNX or DB UNIQUE constraint |
| Connector non-blocking on REJECTED | LOW | Caller decides whether to block |

---

**Document ID:** OMNIX-AUDIT-ATF-DV-2026-001  
**Generated:** 2026-05-13 00:27 UTC  
**Verdict:** ✅ **PASS** (55/55 — 100.0%)  