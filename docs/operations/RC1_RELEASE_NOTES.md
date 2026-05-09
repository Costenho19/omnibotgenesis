# OMNIX QUANTUM — Release Candidate 1 (RC-1)
## Institutional Release Notes

**Release:** RC-1  
**Version:** 6.6.0  
**Release Date:** May 2026  
**Governance Baseline:** OMNIX-BASELINE-2026-Q2-001  
**ADR Count:** 150  
**Classification:** INSTITUTIONAL — Decision Governance Infrastructure

---

> **What RC-1 means:**  
> OMNIX QUANTUM RC-1 is the first frozen, documented, and independently verifiable release of the governance infrastructure.  
> All core modules are architecturally frozen. All invariants are tested. All hardening work is complete.  
> Changes after RC-1 require an ADR, a migration plan, and regression tests.

---

## What Is OMNIX QUANTUM?

OMNIX QUANTUM is **infrastructure that verifies and governs automated decisions before execution**.

Every automated action — a trade, a credit approval, an insurance claim, a medical protocol — passes through an 11-checkpoint governance pipeline. Every decision produces a Post-Quantum Cryptographic receipt (Dilithium-3 / ML-DSA-65 / NIST FIPS 204) that is independently verifiable without OMNIX infrastructure. Every receipt is permanent, tamper-evident, and auditable.

This is not a chatbot. This is not a dashboard. This is governance infrastructure.

---

## RC-1 Highlights

### 1. Governance Baseline Frozen (OMNIX-BASELINE-2026-Q2-001)

10 governance invariants codified and tested:

| Invariant | Description |
|---|---|
| INV-001 | Every checkpoint fails closed — exception = BLOCKED |
| INV-002 | Every decision has exactly one PQC-signed receipt |
| INV-003 | Every receipt carries `hash_version: sha256-v1` — algorithm explicit |
| INV-004 | AVM calibration state is per-tenant — zero cross-contamination |
| INV-005 | LLM content never reaches governance directly |
| INV-006 | Transparency chain integrity verified on every read |
| INV-007 | Every replay receipt declares its fidelity class explicitly |
| INV-008 | Dilithium-3 signing is non-negotiable in production |
| INV-009 | AVM thresholds are security parameters — capped at 50% |
| INV-010 | Every engine version maps to an immutable checkpoint contract |

### 2. ISR Remediations Complete (All 8)

| ISR | Module | Description |
|---|---|---|
| ISR-001 | `assumption_validity_monitor.py` | AVM per-tenant isolation — singleton replaced with registry |
| ISR-008 | `semantic_version_registry.py` | Semantic version → checkpoint contract mapping |
| ISR-010 | `decision_receipt.py` | `hash_version` committed inside every receipt hash |
| ISR-012 | `receipt_wal.py` | Write-Ahead Log — receipt durable before DB write |
| ISR-013 | `transparency_chain.py` | Chain resilience — retry + pending queue |
| ISR-017 | `input_sanitizer.py` | Prompt injection sanitizer for LLM inputs |
| ISR-021 | `payload_key_manager.py` | Payload encryption key versioning |
| ISR-022 | `transparency_chain.py` | Read-path chain integrity verification |

### 3. ADR-148 — LLM Isolation Boundary

Structural separation between AI and governance:
- `LLMIsolationBoundary.form_packet()` — 22-key whitelist, non-numeric stripping, forbidden key blocking
- `GovernanceSignalPacket` — the only container that may cross the boundary
- Crossing audit log with 500-entry ring buffer
- Strict mode with `BoundaryViolationError` for high-security deployments

### 4. ADR-149 — Replay Fidelity Classification

Transparent institutional claims from crisis replay:
- `ReplayFidelityClass` — `FORENSIC_SIMULATION`, `COMPUTATIONAL_REPLAY`, `PARTIAL_COMPUTATIONAL`
- Every `SignedReplayReceipt` carries `fidelity_classification`, `fidelity_note`, `admissible_claim`
- `verify_replay_chain()` — independent verification of all replay receipts, no OMNIX infra needed

### 5. ADR-150 — Operational Readiness Layer

Production-grade health monitoring:
- `GET /api/health` — 6-subsystem health report + Telegram alerts
- `GET /api/health/live` — liveness probe for Railway
- `GET /api/health/ready` — readiness probe for load balancers
- `POST /api/health/reconcile-wal` — WAL flush after DB recovery
- `alert_critical()`, `alert_warning()`, `alert_recovery()` — structured Telegram ops alerts

### 6. Architecture Visualization (`/architecture`)

Six interactive diagrams:
- Governance Pipeline (11 checkpoints)
- Receipt Lifecycle (WAL → PQC → DB → chain)
- LLM Isolation Boundary (22 approved / 13 forbidden keys)
- Tenant Isolation (AVM per-tenant calibration)
- Trust Anchor Chain (Dilithium-3 verification flow)
- Runtime Authority Matrix (4-tier authority model)

---

## Test Coverage

| Suite | Tests | Status |
|---|---|---|
| `test_governance_integrity.py` | 124 | ✅ 124 passing |
| `test_isr_remediation.py` | 54 | ✅ 54 passing |
| `test_governance_hardening.py` | 55 | ✅ 55 passing |
| `test_version_consistency.py` | — | ✅ passing |
| `test_critical_audit.py` | — | ✅ passing |

---

## Breaking Changes from Pre-RC-1

| Change | Impact | Migration |
|---|---|---|
| `store_receipt()` now WAL-first | WAL file created at `/tmp/omnix_receipt_wal.jsonl` | None — WAL is additive and transparent |
| `get_chain()` now verifies integrity on read | WARNING logged if chain breaks detected | None — read behavior unchanged, verification is additive |
| `SignedReplayReceipt` has 3 new fields | `fidelity_classification`, `fidelity_note`, `admissible_claim` | `to_dict()` includes them — callers that expect exact keys may need update |
| `public_payload` includes `hash_version` | `hash_version` is now part of the committed hash | New receipts have different `content_hash` than pre-RC-1 receipts — expected |

---

## Known Limitations (Carry-Forward to RC-2)

| Item | Risk | Status |
|---|---|---|
| `pypqc 0.0.6.2` maintenance (ISR-009) | Deprecation risk for historical receipt verification | Monitor — pure-Python fallback verifier planned |
| Rate limit per-client in Redis (ISR-002) | Per-dyno limits only — global quota not enforced in multi-replica | Planned RC-2 |
| FRED_API_KEY hardcode (ISR-014) | API key in source code | Planned RC-2 |
| External validation (no pilot yet) | Internal assumptions unvalidated | Priority for RC-2 cycle |
| Multi-region / failover plan | No documented multi-region strategy | Planned — see HEALTH_MONITORING.md INC runbooks |

---

## Production Checklist (Before Institutional Demo)

- [ ] `OMNIX_SIGNING_SECRET_KEY_B64` set in Railway (PQC keys persistent)
- [ ] `OMNIX_SIGNING_PUBLIC_KEY_B64` set in Railway
- [ ] `OMNIX_ANTI_REPLAY_MODE=strict` set in Railway
- [ ] `TELEGRAM_ADMIN_USER_ID` set in Railway (operational alerts active)
- [ ] Railway health checks configured: `/api/health/live` + `/api/health/ready`
- [ ] UptimeRobot / Better Stack monitoring `/api/health/live` every 60s
- [ ] Manual `GET /api/health` run — all subsystems UP
- [ ] `pg_dump` baseline backup taken before first institutional demo

---

## Architecture Decision Records — RC-1 Index (Last 10)

| ADR | Title |
|---|---|
| ADR-141 | Module API Wiring — Oscillation/Anomaly/Execution/CAG |
| ADR-142 | Breach Containment Engine |
| ADR-143 | Multi-Domain Risk Governance |
| ADR-144 | Auto-Modification Guard (AMG) |
| ADR-145 | Governance Replay Engine |
| ADR-146 | Runtime Authority Matrix |
| ADR-147 | Scope Authorization Record |
| ADR-148 | LLM Isolation Boundary |
| ADR-149 | Replay Fidelity Classification |
| ADR-150 | Health Monitoring & Operational Readiness |

**Full index:** `docs/adr/` — 150 total ADRs.

---

## Signing This Release

OMNIX QUANTUM RC-1 is signed by Harold Nunes (Founder & Chief Architect) as the governance authority under the Runtime Authority Matrix (ADR-146, TIER-1).

Every architectural invariant in this release is frozen. Every ISR remediation is tested. Every operational gap identified in the Institutional Survivability Report (ISR-2026-Q2-001) has been addressed or formally carried forward to RC-2.

**This is the baseline from which OMNIX enters institutional validation.**

---

*OMNIX QUANTUM RC-1 · v6.6.0 · May 2026 · omnixquantum.net*  
*Governance Baseline: OMNIX-BASELINE-2026-Q2-001*
