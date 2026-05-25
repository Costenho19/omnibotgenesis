# OMNIX QUANTUM — 47-Invariant Test Coverage Matrix
**Document ID:** OMNIX-COMPLIANCE-INV-MATRIX-2026-05  
**Date:** May 2026 (rev.3 — May 17, 2026)  
**Standard:** RFC-ATF-1 · RFC-ATF-2 · RFC-ATF-3 · ADR-157 rev.2 · ADR-161 through ADR-167 · ADR-170  
**Total Invariants:** 47 across 9 families (GECR-INV-001–006 added in ADR-170)  
**Coverage:** 36/47 direct test (76.6%) · 11/47 structural only (23.4%) · 0/47 untested  

> This matrix is the authoritative traceability document between the 47 formal invariants published in RFC-ATF-1, RFC-ATF-2, RFC-ATF-3, ADR-157 rev.2, ADR-170, and the test suite. It is referenced by the Technical Whitepaper (Section 13) and the Institutional Audit Report (OMNIX-AUDIT-ATF-EAP-OEP-2026-05).
>
> **rev.2 changes:** TAR-INV-006 (Compiled Staleness Bound) added to Family 1. RGC-INV-007 gap closed — `RCR_CES_STALENESS_BOUND_SECONDS=300` compiled constant.
> **rev.3 changes:** GECR-INV-001–006 (Governance Execution Context Router) added in ADR-170. Total raised to 47.

---

## Family 1 — ATF Invariants (RFC-ATF-1 · ADR-156/157/158)

| ID | Formal Statement | Implementation | Test File | Test ID / Count | Status |
|---|---|---|---|---|---|
| ATF-INV-001 | `DR.budget_granted ≤ DR.budget_delegator` for all DRs (Monotonic Authority Reduction) | `delegation_receipt.py` — enforced at `issue()` + `translate()` | `test_atf_receipts.py` | `test_mar_invariant` | ✅ Direct |
| ATF-INV-002 | Trust lattice is a DAG — no delegation cycle exists (Acyclicity) | `trust_lattice.py` — DAG structure enforced | `test_agent_trust_fabric.py` | Structural path only | ⚠️ Structural |
| ATF-INV-003 | All DRs in a chain share the same `chain_root_id` (Chain Root Consistency) | `trust_lattice.py` — `verify_chain()` checks root | `test_atf_receipts.py` | `test_chain_root_consistency` | ✅ Direct |
| ATF-INV-004 | DR fields are immutable post-issuance (Content Hash Immutability) | `delegation_receipt.py` — SHA-256 over sorted canonical JSON | `test_atf_receipts.py` | `test_content_hash_immutability` | ✅ Direct |
| ATF-INV-005 | `TAR.execution_ns ≤ current_time` at verification (Temporal Non-Future-Dating) | `temporal_authority.py` — `execution_ns = time.time_ns()` captured first | `test_atf_receipts.py` | `test_tar_temporal_validity` | ✅ Direct |
| ATF-INV-006 | Full chain verifiable offline using only receipts and root public key; canonical JSON serialization reproducible cross-language | All ATF modules — embedded `delegator_public_key` in every receipt; `canonical_json()` spec in `sdk/conformance_vectors.json` | `test_conformance_vectors.py` | 10/10 canonical JSON vectors (Python) + 10/10 Node.js (conformance_check.ts) | ✅ Direct cross-language |
| TAR-INV-006 | DR remaining validity window at admission must not exceed 86400s (24h) — compiled constant, non-overridable by operator or env var (ADR-157 rev.2) | `temporal_authority.py` — `TAR_MAX_DR_LIFETIME_SECONDS=86400` + `TAR_CLOCK_SKEW_TOLERANCE_NS=5_000_000_000` compiled in module body; `runtime_continuity.py` — `RCR_CES_STALENESS_BOUND_SECONDS=300` | `test_tar_inv006_staleness_bound.py` | 23/23 — includes env-monkeypatch immutability verification | ✅ Direct |

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
| RGC-INV-007 | CES inputs must meet freshness requirements | `runtime_continuity.py` — `RCR_CES_STALENESS_BOUND_SECONDS=300` compiled constant (non-env-var); `rcr_performance.py` — EventDrivenSampler `notify()` pattern | `test_tar_inv006_staleness_bound.py` | Compiled constant immutability verified (env-monkeypatch tests) | ✅ Direct |
| RGC-INV-008 | RC TTL enforced — auto-HALT on expiry | `runtime_continuity.py` — RC TTL checked in `_check_rc_expiry()` | `test_runtime_governance_continuity.py` | `test_rc_ttl_enforcement` | ✅ Direct |

**Gap closed — RGC-INV-007 (ADR-157 rev.2, May 17 2026):** `RCR_CES_STALENESS_BOUND_SECONDS=300` compiled constant added to `runtime_continuity.py`. Constant is non-overridable by env var — verified by env-monkeypatch tests in `test_tar_inv006_staleness_bound.py`. Promoted to ✅ Direct.

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
| FVP-INV-007 | Every `/verify` response includes `key_identity` object; `platform_fingerprint` populated if platform key configured; fingerprint algorithm deterministic cross-language (May 17 2026) | `forensic_blueprint.py` — `key_identity` computed in every response; `sdk/conformance_vectors.json` — 7 KFP vectors + algorithm spec; `sdk/node/src/fingerprint.ts` — Node.js reference implementation | `test_eap_extended_audit.py` (III6, III7) + `test_conformance_vectors.py` (7 KFP vectors) + `sdk/node/conformance_check.ts` (7 KFP vectors, Node.js) | 17 cross-language checks pass (Python + Node.js) | ✅ Direct cross-language |

---

## Family 9 — GECR Invariants (ADR-170)

| ID | Formal Statement | Implementation | Test File | Test ID / Count | Status |
|---|---|---|---|---|---|
| GECR-INV-001 | Every GECR orchestration decision is atomic with its governance receipt — no controlled action proceeds without a receipt being issued first (Control-Receipt Atomicity) | UDCL Layer 3 PQC receipt mandatory; CTAG verdict embedded in ControlReceipt before commit; RCR issued before CES-driven HALT/RC | Structural — enforced by UDCL mandatory pillar architecture | Layer 3 is non-optional in UDCL; no code path permits commit without ControlReceipt | ⚠️ Structural |
| GECR-INV-002 | Context drift between approval and commit is bounded: drift_delta < −0.05 → DRIFTED receipt; drift_delta < −0.15 → REVOKED, commit refused (Bounded Context Drift) | `commit_time_gate.py` — `REVOCATION_DRIFT_THRESHOLD=0.15`, `CAUTION_DRIFT_THRESHOLD=0.05` | `test_governance_integrity.py` | CTAG drift threshold tests | ✅ Direct |
| GECR-INV-003 | Cross-agent authority aggregate at `chain_root_id` level never exceeds AFG fragmentation limit (default 0.90, hard cap 0.95, values > 1.0 rejected) | `runtime_continuity.py` AFG enforcement — aggregate MAR at chain root level | `test_governance_integrity.py` | AFG fragmentation limit tests | ✅ Direct |
| GECR-INV-004 | HALT propagates atomically to ALL sibling sessions sharing the same `chain_root_id` — partial HALT is not a valid GECR state | `runtime_continuity.py` HALT propagation via chain_root_id | `test_governance_integrity.py` | HALT propagation tests | ✅ Direct |
| GECR-INV-005 | Cross-runtime agent operations require a bilaterally Dilithium-3 signed CRGC between runtimes prior to first cross-runtime admission; undeclared parameters default to the more restrictive runtime's value | ADR-161 CRGC issuance and validation; ATF-GPI-Aligned status required | `test_gpil_audit.py` | CRGC bilateral signing tests | ✅ Direct |
| GECR-INV-006 | Reauthorization Challenges auto-HALT on TTL expiry — TTL is bounded and non-extensible; no mechanism permits TTL extension | `runtime_continuity.py` RC TTL enforcement (restates RGC-INV-008 at GECR tier with explicit non-extension property) | `test_governance_integrity.py` | RC TTL enforcement tests | ✅ Direct |

---

## Family 10 — SGIP Invariants (ADR-171) — PROPOSED

> **Status: PROPOSED** — Formally defined in ADR-171. Pending activation in next baseline revision. These invariants govern the Semantic Governance Interoperability Protocol (Layer 4). Implementation module: `omnix_core/agents/atf/semantic_governance.py` (pending).

| ID | Formal Statement | Implementation | Test File | Test ID / Count | Status |
|---|---|---|---|---|---|
| SGIP-INV-001 | An STR entry, once published with a valid ML-DSA-65 signature, has an immutable `content_hash` — no UPDATE path exists on `str_entry_id`; any modification attempt MUST raise `STR_IMMUTABILITY_VIOLATION` | `atf_semantic_term_registry` table — append-only; no UPDATE permitted on content-bearing columns | `tests/test_sgip_audit.py` (pending) | STR immutability tests | ❌ Pending implementation |
| SGIP-INV-002 | A Semantic Alignment Certificate MUST NOT be issued unless both parties have valid, signed STR entries for all 8 ATF Core Term Set terms — incomplete SPV raises `SAC_INCOMPLETE_SPV` at construction time | SAC constructor validates both SPVs for completeness before computing `sac_content_hash` | `tests/test_sgip_audit.py` (pending) | SAC completeness tests | ❌ Pending implementation |
| SGIP-INV-003 | For any cross-runtime operation touching a concept with `UNRESOLVED` status in the governing SAC: apply the more restrictive available definition; if neither runtime has defined the term, the operation is BLOCKED unconditionally | GECR CRPR-SGIP gate — checks SAC `semantic_alignment_map` before evaluating cross-runtime admission | `tests/test_sgip_audit.py` (pending) | Unresolved term BLOCK tests | ❌ Pending implementation |
| SGIP-INV-004 | The `sac_content_hash` MUST cover both parties' `spv_hash` values at issuance time — post-issuance SPV updates do not retroactively modify the SAC; a verifier recomputing from embedded values produces the identical hash | SAC construction embeds `spv_hash` values at issuance; no mutable reference to live SPV | `tests/test_sgip_audit.py` (pending) | SAC hash integrity tests | ❌ Pending implementation |

**Gap note — SGIP Family:** All four invariants are pending implementation of `omnix_core/agents/atf/semantic_governance.py`. Priority: RFC-ATF-4 sprint. The invariants are formally specified and their enforcement architecture is defined in ADR-171. Test file `tests/test_sgip_audit.py` to be created alongside the module.

---

## Family 11 — MIVP Invariants (ADR-194)

| ID | Formal Statement | Implementation | Test File | Test ID / Count | Status |
|---|---|---|---|---|---|
| MIVP-INV-001 | MBR MUST be issued and PQC-signed BEFORE the first agent turn when `mandate_binding` is present in governing receipt | `mandate_integrity_verification.py` — `create_mbr()` called in `GovernanceRuntime.start_session()` before session cache write | `tests/test_mivp.py` (pending) | Pre-turn MBR creation test | ⚠️ Structural |
| MIVP-INV-002 | `mandate_objective_hash` MUST be SHA-256 of `mandate_objective` at session start and MUST NOT change during the session | `MandateBindingRecord.compute_content_hash()` — hash computed at `create_mbr()` and embedded in PQC-signed `content_hash` | `tests/test_mivp.py` (pending) | Hash immutability test | ⚠️ Structural |
| MIVP-INV-003 | Every turn in an MBR-bound session MUST produce a MAS before output delivery | `mandate_integrity_verification.py` — `compute_mas()` called in `record_turn()` Step 4, before OGR verdict determination | `tests/test_mivp.py` (pending) | Per-turn MAS creation test | ⚠️ Structural |
| MIVP-INV-004 | MAS MUST be in [0.0, 1.0]; out-of-range MUST produce HALT verdict | `compute_mas()` — `max(0.0, min(1.0, 1.0 - weighted_sum))` clamp enforced + out-of-range treated as HALT | `tests/test_mivp.py` (pending) | Boundary clamp test | ⚠️ Structural |
| MIVP-INV-005 | When MAS < `mas_halt_threshold`, runtime MUST issue HALT verdict before next turn proceeds | `compute_mas()` — `verdict = "HALT"` when `alignment_score < mbr.mas_halt_threshold`; `record_turn()` checks `mas.verdict == "HALT"` | `tests/test_mivp.py` (pending) | Mandate HALT enforcement test | ⚠️ Structural |
| MIVP-INV-006 | MAS history MUST be append-only and linked to CTCHC turn hash | `compute_mas()` — `ctchc_link_hash` parameter from `link.chain_link_hash`; appended to in-memory list + DB | `tests/test_mivp.py` (pending) | Append-only chain linkage test | ⚠️ Structural |
| MIVP-INV-007 | At session close, MBR Seal MUST be issued covering all turns | `seal_mbr()` called in `GovernanceRuntime.close_session()` when `session.mbr_id` present | `tests/test_mivp.py` (pending) | Seal completeness test | ⚠️ Structural |
| MIVP-INV-008 | MANDATE-BOUND PoGC tag MUST only be issued when MBR present, seal complete, `turns_in_violation = 0` | `seal_mbr()` — `mandate_bound_eligible = (turns_in_violation == 0 and mbr is not None)`; `close_session()` appends `MANDATE-BOUND` to `pogc_tags` only when `mandate_bound = True` | `tests/test_mivp.py` (pending) | MANDATE-BOUND eligibility test | ⚠️ Structural |

**Note:** All 8 MIVP invariants are enforced at the structural/implementation level. Dedicated test suite `tests/test_mivp.py` to be created. ProxyGuard keyword-density activation is a baseline implementation — production deployments should extend with domain-specific ML classifiers per ADR-194 §Consequential Risk.

---

## Coverage Summary

```
Family          Invariants    Direct ✅    Structural ⚠️    None ❌    Status
ATF-INV         6             5            1               0          Active
TAR-INV         1             1            0               0          Active ← ADR-157 rev.2
RGC-INV         8             8            0               0          Active ← RGC-INV-007 closed
GPIL-INV        3             3            0               0          Active
ELR-INV         4             2            2               0          Active
EAP-INV         7             6            1               0          Active
OEP-INV         6             6            0               0          Active
FEA-INV         5             4            1               0          Active
FVP-INV         1             1            0               0          Active
GECR-INV        6             5            1               0          Active ← ADR-170
MIVP-INV        8             0            8               0          Active ← ADR-194 (new)
─────────────────────────────────────────────────────────────────────────────
ACTIVE TOTAL    55            41           14              0
─────────────────────────────────────────────────────────────────────────────
SGIP-INV        4             0            0               4          PROPOSED ← ADR-171
─────────────────────────────────────────────────────────────────────────────
GRAND TOTAL     59            41           14              4

Active coverage (55 invariants):
  Direct:      41/55 = 74.5%
  Structural:  14/55 = 25.5%
  None:         0/55 =  0.0%

Proposed (SGIP, 4 invariants):
  All 4 pending implementation — RFC-ATF-4 sprint

MIVP-INV (8 invariants, all Structural — pending tests/test_mivp.py):
  Priority action: create test_mivp.py — target 8/8 Direct
```

---

## Priority Remediation Plan

| Priority | Invariant | Action | File | Sprint |
|---|---|---|---|---|
| 1 | ATF-INV-002 | Add cycle injection test: create circular DR chain, assert `VerificationResult.is_valid = False` | `tests/test_agent_trust_fabric.py` | Next |
| 2 | ELR-INV-003 | Add reclassification rejection test: attempt to change `evidence_class` on transition, assert immutability error | `tests/test_eap_audit.py` | Next |
| 3 | ELR-INV-004 | Add compression rejection test: attempt to strip `LEGAL`-class artifact fields, assert rejection | `tests/test_eap_audit.py` | Next |
| 4 | EAP-INV-007 | Add production-mode Redis probe test: `OMNIX_ARCHIVE_REDIS_REQUIRED=true` + absent REDIS_URL = hard fail | `tests/test_cold_block_archive.py` | Next |
| 5 | FEA-INV-001 | Add env var default test: absent `FORENSIC_EXPORT_ALLOW_CALLER_KEYS` behaves as `false` | `tests/test_oep_forensic_audit.py` | Next |
| 6 | ELR-INV-003 (GPIL) | Implement `omnix_core/governance/gpil.py` runtime module — CRGC issuance, signing, storage | `omnix_core/governance/gpil.py` | Future |
| 7 | SGIP-INV-001–004 | Implement `omnix_core/agents/atf/semantic_governance.py` — STR, SPV, SAC classes; create `tests/test_sgip_audit.py` | `semantic_governance.py` + test file | RFC-ATF-4 sprint |

> **Closed items:** RGC-INV-007 — removed from backlog May 17 2026 (ADR-157 rev.2). Structural gap closed via compiled constant `RCR_CES_STALENESS_BOUND_SECONDS=300` in `runtime_continuity.py`.

---

**Cross-language conformance infrastructure (May 17 2026):** `sdk/conformance_vectors.json` — 12 canonical vectors (7 KFP + 5 CJ) machine-generated from the Python reference implementation. `tests/test_conformance_vectors.py` — 37 Python tests. `sdk/node/conformance_check.ts` — 17 Node.js checks. Any future SDK (Go, Rust, Java) must pass against the same vector file.

*This matrix supersedes all previous invariant coverage references. Update this document whenever a new invariant is added or a new test closes a structural-only gap.*  
*Cross-referenced by: `docs/whitepaper/OMNIX_TECHNICAL_WHITEPAPER.md` §13 · `docs/audits/ATF_EAP_OEP_INSTITUTIONAL_AUDIT_2026-05.md` §B · ADR-171*
