# OMNIX QUANTUM — Governance Baseline
## Línea Base Institucional · Governance Architecture Freeze

**Document ID:** OMNIX-BASELINE-2026-Q2-001  
**Classification:** INTERNAL — Architecture Reference  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Status:** ACTIVE — Updated May 22, 2026 (ADR-178/179/180 + RFC-ATF-5 CGL extension)  
**Review Cycle:** Quarterly or upon any proposed core module change

---

> **Purpose:** This document declares the architectural baseline of OMNIX QUANTUM as of May 2026.  
> Any change to a `core-frozen` module requires an Architecture Decision Record (ADR) filed before implementation.  
> Any change to a governance invariant requires a Migration Plan filed before implementation.  
> This document is the source of truth for what OMNIX **is** — not what it may become.

---

## 1. Core Module Inventory

### 1.1 CORE-FROZEN Modules

These modules implement governance invariants. They **may not be modified** without a filed ADR, a peer review, and a test coverage report showing no regression.

| Module | Responsibility | Governing ADR(s) | Invariant |
|---|---|---|---|
| `omnix_core/governance/external_evaluator.py` | 11-checkpoint governance pipeline | ADR-028, ADR-040 | Every evaluation produces a deterministic decision |
| `omnix_core/evidence/decision_receipt.py` | PQC-signed receipt generation + Genealogy Chain | ADR-078, ADR-085, ADR-097, **ADR-154** | Every decision has exactly one receipt; every receipt is tamper-evident; sequential decisions for the same asset are cryptographically linked |
| `omnix_core/evidence/transparency_chain.py` | Append-only audit log + Chain Completeness Score | ADR-044, **ADR-155** | Every receipt entry is chained; chain tampering is detectable on read; every integrity report carries a 0–100 completeness score |
| `omnix_core/security/pqc_security.py` | Post-quantum cryptography | ADR-060 | Dilithium-3 (ML-DSA-65) is the signing algorithm; never downgraded silently |
| `omnix_core/governance/assumption_validity_monitor.py` | AVM per-tenant baselines + Threshold Probe Detection | ADR-074, ADR-120, ISR-001, **ADR-152** | Tenant calibrations are isolated; no cross-tenant contamination; systematic threshold probing is detected and recorded |
| `omnix_core/governance/semantic_version_registry.py` | Engine version semantics | ISR-008 | Every engine version maps to an explicit checkpoint contract |
| `omnix_core/governance/auto_modification_guard.py` | AMG — threshold change control | ADR-144 | AVM thresholds cannot change by more than 10%/event or 30% cumulative without approval |
| `omnix_core/governance/scope_authorization_engine.py` | Scope authorization records | ADR-147 | Every governance scope is PQC-signed at issuance |
| `omnix_core/governance/memory_context_auditor.py` | Decision-time context governance & Memory Attestation Records | ADR-151 | Every governance evaluation has a PQC-signed attestation of its full context window |
| `omnix_core/evidence/receipt_wal.py` | Write-Ahead Log for receipts | ISR-012 | Every governance decision has at least one durable copy before DB write |

### 1.2 GOVERNANCE-CRITICAL Modules

These modules implement governance-adjacent logic. Changes require a pull request review and test coverage. No ADR required unless the change touches an invariant.

| Module | Responsibility |
|---|---|
| `omnix_core/governance/avm_db_bridge.py` | AVM DB persistence |
| `omnix_core/governance/context_admission_gate.py` | Market condition admission |
| `omnix_core/governance/llm_isolation_boundary.py` | LLM↔governance structural separation + **Numeric Uniformity Anomaly detection (ADR-153)** |
| `omnix_core/evidence/payload_key_manager.py` | Payload encryption key versioning |
| `omnix_core/evidence/anti_replay.py` | Receipt replay prevention |
| `omnix_services/ai_service/input_sanitizer.py` | LLM input sanitization |
| `omnix_core/simulation/governance_replay.py` | Historical crisis replay engine |

### 1.3 OPERATIONAL Modules

Changes may be made with standard engineering practices. Test coverage expected.

| Module | Responsibility |
|---|---|
| `omnix_web/api/gov_blueprint.py` | B2B Governance API endpoints |
| `omnix_web/api/server.py` | Flask application server |
| `omnix_dashboard/app.py` | Operations dashboard |
| `omnix_services/telegram_service/enterprise_bot.py` | Telegram bot interface |
| `omnix_services/ai_service/conversational_ai_adapter.py` | AI response generation |

---

## 2. Governance Invariants

These are the non-negotiable behavioral properties of OMNIX QUANTUM. **No release may violate these.**

### INV-001 — Fail-Closed Pipeline

Every governance checkpoint must fail-closed. If a checkpoint cannot evaluate (exception, timeout, missing data), the result is `BLOCKED` — never `APPROVED`.

**Enforced by:** `external_evaluator.py` — every checkpoint wrapped in `try/except → BLOCKED`  
**Test:** `tests/test_governance_integrity.py` — 124 tests

### INV-002 — Receipt for Every Decision

Every governance evaluation that completes (APPROVED, BLOCKED, or HOLD) must produce exactly one PQC-signed receipt with a globally unique `receipt_id`.

**Enforced by:** `decision_receipt.py::generate_receipt()` — always returns a receipt  
**Durability:** `receipt_wal.py` (ISR-012) — WAL before DB write  
**Test:** `tests/test_isr_remediation.py` — ISR-012 tests

### INV-003 — Hash Version in Every Receipt

Every receipt must include `hash_version` identifying the canonical hash algorithm. Changing the hash algorithm requires bumping `CANONICAL_HASH_VERSION` in `decision_receipt.py`.

**Enforced by:** `CANONICAL_HASH_VERSION = "sha256-v1"` — injected into every receipt payload  
**Governing:** ISR-010  
**Test:** `tests/test_governance_hardening.py` — hash version tests

### INV-004 — Tenant Isolation in AVM

AVM calibration state is partitioned by `tenant_id`. No client's calibration signals may affect another client's AVM baseline.

**Enforced by:** `get_avm_instance(tenant_id)` — per-tenant registry  
**Governing:** ISR-001  
**Test:** `tests/test_isr_remediation.py` — ISR-001 tests

### INV-011 — Context Window Attested at Every Evaluation

Every governance evaluation must produce a `MemoryAttestationRecord` (MAR) attesting the complete AI context window — signals, data sources, history depth, signal freshness, and scope — at the exact moment of evaluation. Critical context contamination blocks the evaluation (fail-closed). The MAR ID is embedded in the Decision Receipt as `memory_attestation_id`.

**Enforced by:** `memory_context_auditor.py::generate_mar()` — fail_closed_on_critical=True by default  
**Governing:** ADR-151  
**Test:** `tests/test_memory_context_governance.py` — 60+ tests

### INV-005 — LLM Content Never Enters Governance Directly

No raw LLM-generated text or non-numeric LLM artifact key may reach the governance evaluation engine. All AI-originated signals must pass through `LLMIsolationBoundary.form_packet()`.

**Enforced by:** `llm_isolation_boundary.py` — whitelist of 22 approved numeric signal keys  
**Governing:** ADR-148, ISR-017  
**Test:** `tests/test_governance_hardening.py` — LLM isolation tests

### INV-006 — Transparency Chain Read-Path Verification

Every call to `TransparencyChain.get_chain()` verifies chain integrity on the fetched entries. Breaks are logged at WARNING level; a break never silently passes.

**Enforced by:** `transparency_chain.py::get_chain()` — calls `verify_chain_integrity()` internally  
**Governing:** ISR-022  
**Test:** `tests/test_governance_hardening.py` — chain verification tests

### INV-007 — Replay Fidelity Classification

Every replay receipt must carry an explicit `fidelity_classification` field. The claim "OMNIX would have blocked [event]" is never made without declaring the fidelity class.

**Enforced by:** `SignedReplayReceipt.fidelity_classification` — default `FORENSIC_SIMULATION`  
**Governing:** ADR-149  
**Test:** `tests/test_governance_hardening.py` — replay fidelity tests

### INV-008 — PQC Signing is Non-Negotiable

Post-quantum signing (Dilithium-3 / ML-DSA-65) is never disabled in production. `OMNIX_KEY_MODE=required` is the production setting. SHA-256-only fallback is permitted only in development.

**Enforced by:** `pqc_security.py`, `decision_receipt.py::_init_keys()`  
**Governing:** ADR-060, ADR-078

### INV-009 — AVM Thresholds are Security Parameters

`AVM_MAX_CUMULATIVE_DRIFT_PCT` (max 50%) and `AVM_APPROVAL_THRESHOLD_PCT` (max 10% per event) are security parameters, not operational config. Setting them above 50% silently degrades the cumulative drift guard.

**Enforced by:** `auto_modification_guard.py` — AMG validates every threshold change  
**Governing:** ADR-144

### INV-010 — Semantic Version Contract

Every engine version maps to an explicit, immutable `SemanticEntry` in `SemanticVersionRegistry`. A receipt issued under version `X.Y.Z` is semantically transparent in perpetuity — a regulator can determine exactly what each checkpoint meant at that version.

**Enforced by:** `semantic_version_registry.py::assert_version_consistency()` — CI guard  
**Governing:** ISR-008  
**Test:** `tests/test_version_consistency.py`

---

## 3. Evolution Protocol

### When an ADR is Required

An Architecture Decision Record is **mandatory** before implementing:

- Any change to a `core-frozen` module
- Any new governance checkpoint (adds to the 11-checkpoint pipeline)
- Any change to the receipt schema (`public_payload` fields in `generate_receipt()`)
- Any change to the canonical hash algorithm (`CANONICAL_HASH_VERSION`)
- Any change to the AVM tenant isolation model
- Any new crossing type for the LLM Isolation Boundary
- Any change to the replay fidelity classification model

### When a Migration Plan is Required

A Migration Plan is required for:

- Adding a column to `decision_receipts` or `governance_transparency_log`
- Changing the `CANONICAL_HASH_VERSION` (requires re-verification strategy for historical receipts)
- Bumping `CURRENT_SCHEMA_VERSION` in `semantic_version_registry.py`
- Any DB schema change that could break the `reconcile_wal()` path
- Key rotation strategy changes (ADR-078, ADR-085)

### ADR Template

All ADRs live in `docs/adr/`. Filename: `ADR-{N}-{slug}.md`.

Required sections: **Context · Decision · Consequences · Implementation Notes**

---

## 4. Module → ADR → Invariant Map

| Module | ADRs | Invariants |
|---|---|---|
| `external_evaluator.py` | ADR-028, 040 | INV-001 |
| `decision_receipt.py` | ADR-078, 085, 097, ISR-010 | INV-002, INV-003, INV-008 |
| `transparency_chain.py` | ADR-044, ISR-013, ISR-022 | INV-006 |
| `pqc_security.py` | ADR-060 | INV-008 |
| `assumption_validity_monitor.py` | ADR-074, 120, ISR-001 | INV-004 |
| `semantic_version_registry.py` | ISR-008 | INV-010 |
| `auto_modification_guard.py` | ADR-144 | INV-009 |
| `scope_authorization_engine.py` | ADR-147 | — |
| `receipt_wal.py` | ISR-012 | INV-002 |
| `llm_isolation_boundary.py` | ADR-148, ISR-017 | INV-005 |
| `memory_context_auditor.py` | ADR-151 | INV-011 |
| `governance_replay.py` | ADR-145, ADR-149 | INV-007 |

---

## 5. What Requires External Validation Before Production

Status updated: May 10, 2026 — following Production Verification Report OMNIX-PVR-2026-001.

| Item | Risk | Status |
|---|---|---|
| `OMNIX_SIGNING_SECRET_KEY_B64` in Railway | Ephemeral keys invalidate all receipts on restart | ✅ **RESOLVED** — `pqc_mode: dilithium3-persistent` confirmed in production |
| `OMNIX_SIGNING_PUBLIC_KEY_B64` in Railway | Verification endpoint non-functional without it | ✅ **RESOLVED** — verification endpoint operational |
| `OMNIX_ANTI_REPLAY_MODE=strict` in Railway | Cross-dyno replay in multi-instance deployments | ✅ **RESOLVED** — confirmed in bot startup logs May 10, 2026 |
| `pypqc 0.0.6.2` library maintenance (ISR-009) | Deprecation breaks historical receipt verification | ⚠️ Monitor — pure-Python fallback verifier planned (RC-2) |
| FRED_API_KEY hardcode (ISR-014) | API key in source code | ⚠️ Planned RC-2 |
| Rate limit per-client in Redis (ISR-002) | Multi-dyno per-dyno limits bypass global quota | ⚠️ Planned RC-2 — migrate `_client_rate_limit_store` to Redis |

---

## 6. Approved ADR Index (as of May 2026)

151 total ADRs. Last 6:

| ADR | Title | Status |
|---|---|---|
| ADR-146 | Runtime Authority Matrix | Accepted |
| ADR-147 | Scope Authorization Record | Accepted |
| ADR-148 | LLM Isolation Boundary | Accepted |
| ADR-149 | Replay Fidelity Classification | Accepted |
| ADR-150 | Health Monitoring & Operational Readiness | Accepted |
| ADR-151 | Memory Context Governance | Accepted |

---

## 7. Hardening Status (May 2026)

| Remediation | Module | Status |
|---|---|---|
| ISR-001 — AVM multi-tenant isolation | `assumption_validity_monitor.py` | ✅ Complete |
| ISR-008 — Semantic version registry | `semantic_version_registry.py` | ✅ Complete |
| ISR-010 — Hash version in receipts | `decision_receipt.py` | ✅ Complete |
| ISR-012 — WAL for store_receipt | `receipt_wal.py` | ✅ Complete |
| ISR-013 — Transparency chain resilience | `transparency_chain.py` | ✅ Complete |
| ISR-017 — Prompt injection sanitizer | `input_sanitizer.py` | ✅ Complete |
| ISR-021 — Payload key versioning | `payload_key_manager.py` | ✅ Complete |
| ISR-022 — Read-path chain verification | `transparency_chain.py` | ✅ Complete |
| ADR-148 — LLM isolation boundary | `llm_isolation_boundary.py` | ✅ Complete |
| ADR-149 — Replay fidelity classification | `governance_replay.py` | ✅ Complete |
| ADR-151 — Memory Context Governance | `memory_context_auditor.py` | ✅ Complete |

---

---

## Addendum — ADR-171: Semantic Governance Interoperability Protocol (SGIP)

**Filed:** May 2026 · **Status:** Accepted · **Extends:** ADR-161 (GPIL)

ADR-171 introduces Layer 4 — Semantic Interoperability — to the ATF compliance stack. It formalizes the **Semantic Term Registry (STR)**, **Semantic Policy Vector (SPV)**, and **Semantic Alignment Certificate (SAC)** as first-class protocol artifacts covering the eight concepts of the ATF Core Term Set: AUTHORITY, ADMISSIBILITY, TRUST, SOVEREIGNTY, RISK, ESCALATION, REVOCATION, LEGITIMACY.

This ADR does not modify any active invariant. It adds **4 PROPOSED invariants** (SGIP-INV-001–004) pending activation in the next baseline revision. The **ATF-SGIP-Aligned** compliance designation is the highest in the ATF stack — it is the first mechanism in any governance infrastructure to provide cryptographically committed, independently verifiable semantic declarations for cross-runtime governance operations.

**Impact on counts:**
- ADRs: 170 → **171**
- Active invariants: 47 (unchanged — SGIP family is PROPOSED)
- Proposed invariants: 0 → **4** (SGIP-INV-001–004)
- Implementation module pending: `omnix_core/agents/atf/semantic_governance.py`
- Test suite pending: `tests/test_sgip_audit.py`
- Future RFC: RFC-ATF-4

*OMNIX QUANTUM — Decision Governance Infrastructure*  
*Governance Baseline OMNIX-BASELINE-2026-Q2-001 · May 2026 · omnixquantum.net*
