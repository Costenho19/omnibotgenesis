# OMNIX QUANTUM — 40-Invariant Test Coverage Matrix
**Document ID:** OMNIX-COMPLIANCE-INV-MATRIX-2026-05  
**Date:** May 2026  
**Standard:** RFC-ATF-1 · RFC-ATF-2 · RFC-ATF-3 · ADR-161 through ADR-167  
**Total Invariants:** 40 across 8 families  
**Coverage:** 34/40 direct test (85.0%) · 6/40 structural only (15.0%) · 0/40 untested  

> This matrix is the authoritative traceability document between the 40 formal invariants published in RFC-ATF-1, RFC-ATF-2, RFC-ATF-3, and the test suite. It is referenced by the Technical Whitepaper (Section 13) and the Institutional Audit Report (OMNIX-AUDIT-ATF-EAP-OEP-2026-05).

---

## Family 1 — ATF Invariants (RFC-ATF-1 · ADR-156/157/158)

| ID | Formal Statement | Implementation | Test File | Test ID / Count | Status |
|---|---|---|---|---|---|
| ATF-INV-001 | `DR.budget_granted ≤ DR.budget_delegator` for all DRs (Monotonic Authority Reduction) | `delegation_receipt.py` — enforced at `issue()` + `translate()` | `test_atf_receipts.py` | `test_mar_invariant` | ✅ Direct |
| ATF-INV-002 | Trust lattice is a DAG — no delegation cycle exists (Acyclicity) | `trust_lattice.py` — DAG structure enforced | `test_agent_trust_fabric.py` | Structural path only | ⚠️ Structural |
| ATF-INV-003 | All DRs in a chain share the same `chain_root_id` (Chain Root Consistency) | `trust_lattice.py` — `verify_chain()` checks root | `test_atf_receipts.py` | `test_chain_root_consistency` | ✅ Direct |
| ATF-INV-004 | DR fields are immutable post-issuance (Content Hash Immutability) | `delegation_receipt.py` — SHA-256 over sorted canonical JSON | `test_atf_receipts.py` | `test_content_hash_immutability` | ✅ Direct |
| ATF-INV-005 | `TAR.execution_ns ≤ current_time` at verification (Temporal Non-Future-Dating) | `temporal_authority.py` — `execution_ns = time.time_ns()` captured first | `test_atf_receipts.py` | `test_tar_temporal_validity` | ✅ Direct |
| ATF-INV-006 | Full chain verifiable offline using only receipts and root public key | All ATF modules — embedded `delegator_public_key` in every receipt | `test_conformance_vectors.py` | 43/43 conformance vectors | ✅ Direct |

---

## Family 2 — RGC Invariants (RFC-ATF-2 · ADR-159/160)

| ID | Formal Statement | Implementation | Test File | Test ID / Count | Status |
|---|---|---|---|---|---|
| RGC-INV-001 | Every RCR anchored to a valid TAR | `runtime_continuity.py` — `tar_id` required in RCR | `test_runtime_governance_continuity.py` | `test_rcr_tar_anchoring` | ✅ Direct |
| RGC-INV-002 | CES computed from real-time values only (`T×0.30 + B×0.30 + D×0.20 + I×0.20`) | `runtime_continuity.py` — `_compute_ces()` formula hard-coded | `test_runtime_governance_continuity.py` + `test_atf_receipts.py` | CES formula: 94.39 verified | ✅ Direct |
| RGC-INV-003 | HALT terminates execution and revokes sub-tasks | `runtime_continuity.py` — HALT path triggers cascade revocation | `test_runtime_governance_continuity.py` | `test_halt_terminates_execution` | ✅ Direct |
| RGC-INV-004 | Aggregate budget never exceeds AFG limit (default 0.90, hard max 0.95) | `runtime_continuity.py` — `_check_afg()` enforced before RCR emission | `test_runtime_governance_continuity.py` | `test_afg_fragmentation_guard` | ✅ Direct |
| RGC-INV-005 | All RCRs PQC-signed and immutable | `runtime_continuity.py` — ML-DSA-65 signature on every RCR | `test_runtime_governance_continuity.py` | `test_rcr_pqc_signature` | ✅ Direct |
| RGC-INV-006 | Continuity chain is acyclic and monotonic | `runtime_continuity.py` — `previous_rcr_id` chain enforces forward-only | `test_runtime_governance_continuity.py` | `test_continuity_chain_monotonic` | ✅ Direct |
| RGC-INV-007 | CES inputs must meet freshness requirements | `rcr_performance.py` — EventDrivenSampler `notify()` pattern | No dedicated freshness rejection test | ⚠️ Structural |
| RGC-INV-008 | RC TTL enforced — auto-HALT on expiry | `runtime_continuity.py` — RC TTL checked in `_check_rc_expiry()` | `test_runtime_governance_continuity.py` | `test_rc_ttl_enforcement` | ✅ Direct |

**Gap note — RGC-INV-007:** EventDrivenSampler validates sampling intervals but does not reject stale CES inputs when `notify()` has not been called within `RGC_FRESHNESS_MAX_AGE_SECONDS`. A test that advances time past the freshness window and asserts CES recomputation refusal is needed.

---

## Family 3 — GPIL Invariants (ADR-161 · RFC-ATF-3 Part I)

| ID | Formal Statement | Implementation | Test File | Test ID / Count | Status |
|---|---|---|---|---|---|
| GPIL-INV-001 | Protocol-Bounded parameters are fixed across all runtimes (CES formula, thresholds, hash algorithm) | Protocol spec (ADR-161 §3) | `test_gpil_audit.py` | I11, I12 (policy bounds) | ✅ Direct |
| GPIL-INV-002 | Sovereign parameters are configurable within stated bounds only | Protocol spec (ADR-161 §2) | `test_gpil_audit.py` | I2 (AFG bounds), I3 (RC TTL bounds) | ✅ Direct |
| GPIL-INV-003 | CRGC is immutable once both parties have signed | Protocol spec (ADR-161 §4) | `test_gpil_audit.py` | I12 (hash determinism) | ✅ Direct |

**Gap note:** All three GPIL invariants are tested at the protocol/data-structure level. No runtime module exists (`gpil.py`) that actually issues, stores, or verifies CRGC objects in a live environment. Tests validate the specification; they do not validate a running implementation.

---

## Family 4 — ELR Invariants (ADR-162)

| ID | Formal Statement | Implementation | Test File | Test ID / Count | Status |
|---|---|---|---|---|---|
| ELR-INV-001 | Evidence class is assigned at creation and never changes | `cold_block_sealer.py` — `evidence_class` set at artifact creation | `test_eap_audit.py` | HOT→COLD transition tests | ✅ Direct |
| ELR-INV-002 | HOT artifacts transition to WARM or COLD, never backwards | `cold_block_sealer.py` — pipeline is unidirectional | `test_eap_audit.py` | Transition ordering tests | ✅ Direct |
| ELR-INV-003 | Evidence class cannot be reclassified across tier transitions | `cold_block_sealer.py` — `evidence_class` field in WARM manifest preserved | No dedicated reclassification rejection test | ⚠️ Structural |
| ELR-INV-004 | LEGAL/PQC/CONTRACT/EXCEPTION artifacts are never compressed or field-stripped | `cold_block_sealer.py` — immutable class permanence check | No dedicated compression-rejection test for immutable classes | ⚠️ Structural |

**Gap note — ELR-INV-003/004:** Tests verify correct transitions but do not explicitly attempt reclassification or stripping of immutable-class artifacts and assert rejection. These should be added to `test_eap_audit.py`.

---

## Family 5 — EAP Invariants (ADR-163/167)

| ID | Formal Statement | Implementation | Test File | Test ID / Count | Status |
|---|---|---|---|---|---|
| EAP-INV-001 | Original `content_hash` recorded in transition manifest before any transformation | `cold_block_sealer.py` — `warm_archive_manifest` entry written first | `test_cold_block_archive.py` | 109/109 | ✅ Direct |
| EAP-INV-002 | PQC signature array preserved in COLD storage unchanged | `cold_block_sealer.py` — `pqc_signature` in block header untouched | `test_cold_block_archive.py` | PQC integrity tests | ✅ Direct |
| EAP-INV-003 | `predecessor_block_hash` chain across all COLD blocks must be unbroken | `cold_block_sealer.py` — chain linkage enforced in `seal_block()` | `test_cold_block_archive.py` | Chain integrity tests | ✅ Direct |
| EAP-INV-004 | LEGAL/PQC/CONTRACT/EXCEPTION sealed in complete canonical form | `cold_block_sealer.py` — immutable class permanence enforced | `test_cold_block_archive.py` | Immutable class tests | ✅ Direct |
| EAP-INV-005 | Offline reconstructability from block file + public key only | `omnix_atf_verify.py` v1.1.0 — standalone verifier, zero external deps | `test_cold_block_archive.py` | Offline verification tests | ✅ Direct |
| EAP-INV-006 | Every HOT→WARM and WARM→COLD transition creates a manifest entry | `cold_block_sealer.py` — manifest completeness enforced | `test_cold_block_archive.py` | Manifest completeness tests | ✅ Direct |
| EAP-INV-007 | Block IDs globally unique across platform lifetime (Redis INCR in prod) | `cold_block_sealer.py` L286–301 — Redis primary, local fallback | `test_cold_block_archive.py` | Redis path mocked only | ⚠️ Structural |

**Gap note — EAP-INV-007:** Production uniqueness relies on Redis INCR. The fallback to process-local counters (L264) is documented as unsafe for multi-process deployments (ADR-167 §2.2). A test is needed that: (1) sets `REDIS_URL=` (absent), (2) verifies startup raises `WARNING`, and (3) verifies that a production-mode check (`OMNIX_ARCHIVE_REDIS_REQUIRED=true`) fails fast rather than silently falling back.

---

## Family 6 — OEP Invariants (ADR-165)

| ID | Formal Statement | Implementation | Test File | Test ID / Count | Status |
|---|---|---|---|---|---|
| OEP-INV-001 | All files required for offline verification are self-contained in the ZIP | `oep_generator.py` — all 8 required paths included in bundle | `test_oep_forensic_audit.py` | V3 | ✅ Direct |
| OEP-INV-002 | `MANIFEST_VERSION = "oep-1.0"` constant is immutable | `oep_generator.py` — constant at module level | `test_oep_forensic_audit.py` | V6 | ✅ Direct |
| OEP-INV-003 | Package signature covers canonical manifest hash (two-phase design) | `oep_generator.py` — sign-then-zip, not zip-then-sign | `test_oep_forensic_audit.py` | Signature integrity tests | ✅ Direct |
| OEP-INV-004 | All blocks referenced in chain_index are present in BLOCKS/ | `oep_generator.py` — chain completeness check before ZIP | `test_oep_forensic_audit.py` | V5 | ✅ Direct |
| OEP-INV-005 | Issuer public key embedded in KEYS/public_key.b64 | `oep_generator.py` — key embedding required | `test_oep_forensic_audit.py` | V4 | ✅ Direct |
| OEP-INV-006 | Schema version locked at `oep-1.0` | `oep_generator.py` — schema version in manifest | `test_oep_forensic_audit.py` + `test_eap_extended_audit.py` | V1, V2 | ✅ Direct |

---

## Family 7 — FEA Invariants (ADR-166)

| ID | Formal Statement | Implementation | Test File | Test ID / Count | Status |
|---|---|---|---|---|---|
| FEA-INV-001 | Platform private key never transmitted in HTTP request body in production | `forensic_blueprint.py` — server reads key from env, not caller body | `test_oep_forensic_audit.py` | IV8 (caller key blocked when env=false) | ⚠️ Structural |
| FEA-INV-002 | Every OEP export logged with `client_id`, `ip`, `key_source`, `package_id` | `forensic_blueprint.py` — audit log on every export call | `test_oep_forensic_audit.py` | Audit log field tests | ✅ Direct |
| FEA-INV-003 | `/export` returns 401 for missing/invalid/expired API key | `forensic_blueprint.py` — B2B RBAC gate | `test_eap_extended_audit.py` | IV1–IV8 (8 tests) | ✅ Direct |
| FEA-INV-004 | `/export` returns 503 (fail-closed) when no signing key available | `forensic_blueprint.py` — key resolution priority chain | `test_oep_forensic_audit.py` | Fail-closed key tests | ✅ Direct |
| FEA-INV-005 | `FORENSIC_EXPORT_ALLOW_CALLER_KEYS=true` forbidden in production | `forensic_blueprint.py` — env var gate | `test_oep_forensic_audit.py` | IV7, IV8 | ✅ Direct |

**Gap note — FEA-INV-001:** Test IV8 verifies caller key injection is blocked when `FORENSIC_EXPORT_ALLOW_CALLER_KEYS=false`. A complementary test is needed to verify that the env var **defaults to false** when absent (i.e., `os.environ.get("FORENSIC_EXPORT_ALLOW_CALLER_KEYS", "false") != "true"` is the correct check, not `== "false"`). This prevents a misconfiguration where the var is unset and evaluated as truthy.

---

## Family 8 — FVP Invariants (ADR-167)

| ID | Formal Statement | Implementation | Test File | Test ID / Count | Status |
|---|---|---|---|---|---|
| FVP-INV-007 | Every `/verify` response includes `key_identity` object; `platform_fingerprint` populated if platform key configured | `forensic_blueprint.py` — `key_identity` computed in every response | `test_eap_extended_audit.py` | III6, III7 (FVP-INV-006/007 documented in blueprint source) | ✅ Direct |

---

## Coverage Summary

```
Family          Invariants    Direct ✅    Structural ⚠️    None ❌
ATF-INV         6             5            1               0
RGC-INV         8             7            1               0
GPIL-INV        3             3            0               0
ELR-INV         4             2            2               0
EAP-INV         7             6            1               0
OEP-INV         6             6            0               0
FEA-INV         5             4            1               0
FVP-INV         1             1            0               0
─────────────────────────────────────────────────────────
TOTAL           40            34           7               0

Direct coverage:      34/40 = 85.0%
Structural only:       7/40 = 17.5%  ← target for next sprint
Zero coverage:         0/40 = 0.0%
```

---

## Priority Remediation Plan

| Priority | Invariant | Action | File | Sprint |
|---|---|---|---|---|
| 1 | ATF-INV-002 | Add cycle injection test: create circular DR chain, assert `VerificationResult.is_valid = False` | `tests/test_agent_trust_fabric.py` | Next |
| 2 | RGC-INV-007 | Add CES freshness rejection test: advance time past `RGC_FRESHNESS_MAX_AGE_SECONDS`, assert CES recomputation refused | `tests/test_runtime_governance_continuity.py` | Next |
| 3 | ELR-INV-003 | Add reclassification rejection test: attempt to change `evidence_class` on transition, assert immutability error | `tests/test_eap_audit.py` | Next |
| 4 | ELR-INV-004 | Add compression rejection test: attempt to strip `LEGAL`-class artifact fields, assert rejection | `tests/test_eap_audit.py` | Next |
| 5 | EAP-INV-007 | Add production-mode Redis probe test: `OMNIX_ARCHIVE_REDIS_REQUIRED=true` + absent REDIS_URL = hard fail | `tests/test_cold_block_archive.py` | Next |
| 6 | FEA-INV-001 | Add env var default test: absent `FORENSIC_EXPORT_ALLOW_CALLER_KEYS` behaves as `false` | `tests/test_oep_forensic_audit.py` | Next |
| 7 | ELR-INV-003 (GPIL) | Implement `omnix_core/governance/gpil.py` runtime module — CRGC issuance, signing, storage | `omnix_core/governance/gpil.py` | Future |

---

*This matrix supersedes all previous invariant coverage references. Update this document whenever a new invariant is added or a new test closes a structural-only gap.*  
*Cross-referenced by: `docs/whitepaper/OMNIX_TECHNICAL_WHITEPAPER.md` §13 · `docs/audits/ATF_EAP_OEP_INSTITUTIONAL_AUDIT_2026-05.md` §B*
