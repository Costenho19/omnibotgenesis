# ADR-144 — Auto-Modification Guard: Meta-Governance Layer Over Adaptive Governance

| Field | Value |
|---|---|
| **Status** | Accepted — Implemented May 2026 |
| **Date** | 2026-05-08 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_core/governance/auto_modification_guard.py` (new) · `omnix_core/governance/assumption_validity_monitor.py` · `omnix_core/governance/meta_coherence_monitor.py` · `omnix_web/api/server.py` |
| **Extends** | ADR-118 (MCM Auto-Remediation) · ADR-120 (AVM Auto-Recalibration) |
| **Replaces** | — |

---

## 1. Problem Statement

ADR-118 and ADR-120 introduced automated remediation capability: the system can now recalibrate itself, tighten thresholds, and respond to CRITICAL governance alerts without human intervention.

This raises a foundational risk that Harold Nunes articulated on May 8, 2026:

> *"The most dangerous systems are those that self-govern without sufficient traceability. If the system can recalibrate itself, tighten its own checkpoints, and then trigger its own MCM analysis — which then re-triggers recalibration — we have a closed loop with no external brake. OMNIX is designed to solve this problem, not to become an instance of it."*

### Three specific failure modes this ADR addresses

#### 1.1 — Cumulative silent drift
Each auto-recalibration cycle is individually within permitted bounds (+20% per cycle). But compounding over 10 cycles produces a 500%+ deviation from the genesis baseline, with every individual step looking "small". No single alarm fires, but the system has fundamentally changed its own behavior.

#### 1.2 — Self-reinforcing conservatism (feedback loop)
MCM detects BLOCK_RATE_COLLAPSE → auto-tighten thresholds → more blocks → MCM detects BLOCK_RATE_COLLAPSE again (next cycle) → auto-tighten again → over-blocking. The MCM triggered the very degradation it was designed to detect.

#### 1.3 — Silent institutional confidence degradation
Counterparties and auditors receive governance receipts without knowing the thresholds used to produce them were automatically changed by an adaptive algorithm. A receipt issued under auto-modified thresholds must be distinguishable from one issued under human-reviewed baselines.

---

## 2. Decision

Implement an **Auto-Modification Guard (AMG)** as a mandatory governance layer that wraps *every* automated modification to AVM thresholds. The AMG is not optional and cannot be bypassed by internal code paths.

The AMG enforces six invariants:

| # | Invariant | Description |
|---|---|---|
| 1 | **Cumulative drift cap** | Total threshold change from the genesis baseline never exceeds `AVM_MAX_CUMULATIVE_DRIFT_PCT` (default: 30%) |
| 2 | **Automatic rollback** | If post-deployment performance check (24h window) shows degradation, the previous snapshot is automatically restored |
| 3 | **Signed diff proof** | Every modification produces a cryptographic proof of the exact before/after delta, signed with the process signing key (Dilithium-3 when available, SHA-256 otherwise) |
| 4 | **Approval gate** | Any single threshold change > `AVM_APPROVAL_THRESHOLD_PCT` (default: 10%) is HELD pending human approval via Telegram; `AVM_AUTO_APPROVE=true` bypasses this for dev environments only |
| 5 | **AUTO_MODIFIED trust flag** | All governance receipts issued under auto-modified snapshots carry a `trust_flags.auto_modified_snapshot=true` field, visible to counterparties and auditors |
| 6 | **Anti-loop guard** | MCM cannot trigger a recalibration that would feed back into its own CRITICAL detection within 24 hours. Loop detection escalates to human review instead |

---

## 3. Architecture

```
                      ┌─────────────────────────────────────┐
                      │    AUTO-MODIFICATION GUARD (AMG)     │
                      │         ADR-144                      │
                      ├─────────────────────────────────────┤
                      │                                      │
  AVM Phase 3/4   ──► │  1. compute_cumulative_drift()      │
  MCM auto-tighten    │     vs genesis baseline              │
                      │                                      │
                      │  2. build_signed_diff_proof()        │
                      │     SHA-256 + optional Dilithium-3   │
                      │                                      │
                      │  3. check_approval_gate()            │
                      │     > 10% single delta → HOLD        │
                      │                                      │
                      │  4. record_modification()            │
                      │     → avm_modification_registry     │
                      │                                      │
                      │  5. check_rollback_needed()          │
                      │     24h performance evaluation       │
                      │                                      │
                      │  6. is_auto_loop()                   │
                      │     MCM→MCM chain detection          │
                      │                                      │
                      └──────────────┬──────────────────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  AVM Snapshot Store  │
                          │  (JSON + PostgreSQL) │
                          └─────────────────────┘
```

### 3.1 Data model — `avm_modification_registry`

```sql
CREATE TABLE IF NOT EXISTS avm_modification_registry (
    id                   SERIAL PRIMARY KEY,
    modification_id      TEXT        NOT NULL UNIQUE,
    domain               TEXT        NOT NULL,
    source               TEXT        NOT NULL,
    thresholds_before    JSONB       NOT NULL,
    thresholds_after     JSONB       NOT NULL,
    diff_proof           TEXT        NOT NULL,
    diff_proof_algorithm TEXT        NOT NULL DEFAULT 'SHA-256',
    cumulative_drift_pct FLOAT       NOT NULL DEFAULT 0.0,
    max_single_delta_pct FLOAT       NOT NULL DEFAULT 0.0,
    status               TEXT        NOT NULL DEFAULT 'DEPLOYED',
    approval_required    BOOLEAN     NOT NULL DEFAULT FALSE,
    approved_by          TEXT,
    approved_at          TIMESTAMPTZ,
    rollback_snapshot_id TEXT,
    performance_check_at TIMESTAMPTZ,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_amr_domain_status
    ON avm_modification_registry (domain, status, created_at DESC);
```

**`status` lifecycle:**

```
PENDING_APPROVAL ──► DEPLOYED ──► ROLLED_BACK
                  └──► REJECTED
```

### 3.2 Signed diff proof format

```
AMG-DIFF-v1:{base64(sha256(canonical_json))}:{algorithm}:{optional_pqc_sig_b64}
```

where `canonical_json = json.dumps({domain, before, after, actor, ts_utc}, sort_keys=True)`.

When Dilithium-3 is available, the SHA-256 hash bytes are additionally signed and appended. The diff proof is stored in `avm_modification_registry.diff_proof` and included in Telegram notifications.

### 3.3 Trust flag propagation

`AVMResult.to_dict()` includes:

```json
{
  "trust_flags": {
    "auto_modified_snapshot": true,
    "auto_modification_source": "PHASE3_OPT",
    "modification_id": "AMG-TRADING-4A7B3F"
  }
}
```

This field flows into every governance receipt's `avm_result` block, making the modification visible to the counterparty at verification time.

---

## 4. Environment variables

| Variable | Default | Description |
|---|---|---|
| `AVM_MAX_CUMULATIVE_DRIFT_PCT` | `30.0` | Hard cap on total threshold drift from genesis |
| `AVM_APPROVAL_THRESHOLD_PCT` | `10.0` | Single-threshold change requiring human approval |
| `AVM_AUTO_APPROVE` | `false` | Bypass approval gate (dev only, never in production) |
| `AVM_ROLLBACK_WINDOW_HOURS` | `24` | Hours after deployment before performance rollback check |
| `AVM_ANTI_LOOP_WINDOW_HOURS` | `24` | Hours within which MCM→MCM chain is detected as loop |

---

## 5. Anti-Loop Guard — formal definition

A **modification loop** is defined as:

> Two or more entries in `mcm_remediation_log` for the same domain, within `AVM_ANTI_LOOP_WINDOW_HOURS`, where both have `action_taken IN ('TIGHTEN_CHECKPOINT_THRESHOLDS', 'FORCE_AVM_RECALIBRATION')`.

When a loop is detected:
1. The pending remediation action is **escalated to human review** (not executed)
2. A `LOOP_DETECTED` entry is written to `mcm_remediation_log`
3. Telegram admin notification is sent with explicit loop context
4. The domain is flagged with `AVM_AUTO_LOOP_DETECTED` tag until human acknowledges

This prevents the most dangerous failure mode: the system tightening its own thresholds in response to alerts generated by its own previous tightening.

---

## 6. Rollback mechanism

Post-deployment performance check runs 24 hours after any `DEPLOYED` modification:

```
At T+24h for domain D:
  1. Re-run optimize_checkpoint_thresholds(domain, lookback_days=7)
  2. If returned optimized thresholds differ from DEPLOYED thresholds by > 15%
     in the same direction as the original modification:
       → Performance has degraded further, modification was ineffective
       → restore thresholds_before from avm_modification_registry
       → tag snapshot ROLLED_BACK
       → notify operator via Telegram
  3. If performance is within tolerance: mark status=VERIFIED_OK
```

The rollback is conservative: it only fires when the performance check indicates the modification made things *worse* in a measurable direction, not merely because the system has not yet converged.

---

## 7. Consequences

### Positive
- Every adaptive change is bounded, signed, auditable, and reversible
- Self-reinforcing feedback loops are structurally blocked, not just rate-limited
- Counterparties can inspect any governance receipt and see whether the threshold configuration was human-reviewed or auto-modified
- Cumulative drift cap means the system cannot silently evolve past its institutional calibration over time

### Negative / Trade-offs
- Approval gate adds latency to Phase 4 deployment (requires Telegram response from operator)
- Rollback check requires 24h of post-deployment data — fast-moving domains may not have stable signal in that window
- Anti-loop guard may escalate legitimate multi-CRITICAL events to human review unnecessarily during genuine market crises

### Invariants this ADR does NOT relax
- ADR-116: Fail-closed enforcement — auto-modification never changes the fail-closed behavior of any gate
- ADR-085: Signing key stability — auto-modification does not affect PQC key rotation
- Past receipts are immutable — no auto-modification affects receipts already issued
- Genesis snapshot is permanent — the genesis anchor for cumulative drift calculation is never overwritten

---

## 8. Related

- ADR-118: MCM Auto-Remediation — the consumer of AMG anti-loop guard
- ADR-120: AVM Auto-Recalibration — the consumer of AMG cumulative cap + diff proof
- ADR-116: Fail-Closed Enforcement Policy
- ADR-117: Meta-Coherence Monitor
- ADR-074: AVM Database Bridge
- ADR-085: Signing Key Persistence

---

## 9. Forensic Validation Findings (May 2026)

**Report reference**: `docs/FORENSIC_VALIDATION_REPORT.md` — FVR-AMG-2026-001

A formal 7-point production hardening audit was conducted after full implementation. All 7 points passed. The following findings are summarized here for in-document traceability.

### 9.1 — Three defects corrected during audit

| ID | Severity | Description | Fix |
|---|---|---|---|
| DEF-001 | HIGH | `AVM_AUTO_APPROVE` and all AMG env vars read at module import time — runtime overrides unreliable | Replaced all module-level constants with dynamic accessor functions `_auto_approve()`, `_approval_threshold_pct()`, etc. |
| DEF-002 | MEDIUM | `AMG_REGISTRY_DDL` in `server.py` contained two SQL statements in one `execute()` call — psycopg2 may drop the second | Split into `AMG_REGISTRY_DDL` (table) and `AMG_INDEX_DDL` (index) — two separate `cur.execute()` calls |
| DEF-003 | LOW | `auto_recalibrate_stale_domains()` had no documentation explaining why it bypasses AMG | Added comprehensive docstring section `AMG SCOPE BOUNDARY (ADR-144 §4)` |

### 9.2 — AMG scope boundary clarification

The audit identified a design boundary that requires explicit documentation:

**`auto_recalibrate_stale_domains()`** calls `save_calibration_snapshot()` directly without going through `run_guard()`. This is correct behavior. The function performs **baseline recalibration** — it re-anchors `baseline_signals` to current market state while `checkpoint_thresholds` are preserved unchanged. The AMG is designed to protect threshold modifications, not baseline signal re-anchoring. These carry different governance semantics:

- **Threshold modification** (AMG scope): changes what decisions get blocked
- **Baseline recalibration** (outside AMG scope): changes what counts as "normal" drift

This boundary is enforced by inspection: `auto_recalibrate_stale_domains()` always passes `checkpoint_thresholds=snapshot.checkpoint_thresholds` (the existing values, unchanged) to `save_calibration_snapshot()`.

### 9.3 — Rollback data sufficiency

The rollback check requires 24h of bidirectional decision data. For sparse domains (defense, energy), this may never accumulate sufficient data to fire. This is **conservative behavior** — the system does not roll back blindly on insufficient data. Operators on sparse domains should use manual review of modification registry records.

### 9.4 — Anti-loop guard simulation results

| Remediation count in 24h | Loop detected | Expected |
|---|---|---|
| 0 | False | False — PASS |
| 1 | False | False — PASS |
| 2 | True | True — PASS |
| 5 | True | True — PASS |

### 9.5 — Signed diff proof properties verified

- Format: `AMG-DIFF-v1:{sha256_64hex}:{algorithm}` ✅
- Non-repudiation: different inputs → different hashes ✅
- Domain isolation: same thresholds, different domain → different hash ✅
- Algorithm: `Dilithium-3 (ML-DSA-65)` when PQC keys available ✅

### 9.6 — Full invariant table

| Invariant | Implementation | Env var | Default | Test result |
|---|---|---|---|---|
| Cumulative drift cap | `compute_cumulative_drift()` vs genesis | `AVM_MAX_CUMULATIVE_DRIFT_PCT` | 30% | PASS |
| Automatic rollback | `check_rollback_needed()` at T+24h | `AVM_ROLLBACK_WINDOW_HOURS` | 24h | PASS (conservative) |
| Signed diff proof | `build_signed_diff_proof()` SHA-256 + Dilithium-3 | — | — | PASS |
| Approval gate | `check_approval_gate()` > 10% → HOLD | `AVM_APPROVAL_THRESHOLD_PCT` | 10% | PASS |
| Trust flag | `evaluate()` detects auto-modified tags | — | — | PASS |
| Anti-loop guard | `is_auto_loop()` ≥2 in window → block | `AVM_ANTI_LOOP_WINDOW_HOURS` | 24h | PASS |

**Status post-audit: Production-complete. All 7 audit points pass.**

---

*"The goal is not just to make OMNIX adaptive — it must remain auditable, bounded, reversible, and incapable of silently changing its own decision behavior beyond safe limits."*

— Harold Nunes, OMNIX QUANTUM LTD, May 8, 2026
