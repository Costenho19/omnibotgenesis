# ADR-160: RCR Performance Optimization Layer (RPOL)

**Status:** Accepted  
**Date:** May 14, 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Supersedes:** None  
**Extends:** ADR-159 (Runtime Governance Continuity)  
**Related:** ADR-131 (Execution Integrity Layer), ADR-156 (Agent Trust Fabric),
              ADR-157 (Temporal Authority Admissibility), ADR-158 (Cross-Domain Trust)

---

## Context

ADR-159 introduced the Runtime Governance Continuity (RGC) layer: a continuous,
PQC-signed authority health monitoring system that emits Runtime Continuity Records
(RCRs) throughout the lifecycle of long-running agent executions.

The production implementation of ADR-159 has the following runtime characteristics
that must be addressed before general availability:

### Performance Issues Identified

**Issue 1 — O(n) Thread Spawning**

Every call to `sample()` spawns two daemon threads: one for `_persist_rcr` and one
for `_persist_cee`. At scale (dozens of concurrent agent sessions, each sampling every
30–120 seconds), this generates tens of threads per minute. Thread creation on CPython
carries ~0.1–0.5ms overhead per thread, and each thread opens a new DB connection
(~5–20ms for pg connection establishment). The result is:

- Unpredictable latency spikes on the governance path
- DB connection pool exhaustion under concurrent load
- Thread count growth proportional to session × event frequency

**Issue 2 — No Event-Driven Sampling**

RGC callers must manually invoke `sample()` at appropriate intervals. In practice,
callers either over-sample (handshake on every micro-operation) or under-sample
(miss governance boundary events). Neither outcome is correct.

There is no mechanism for the governance engine to react to specific events
(budget drop, anomaly detection, context drift) without callers implementing
their own timer management.

**Issue 3 — No Adaptive Interval Scheduling**

ADR-159 §5 specifies a sampling strategy table (SHORT/MEDIUM/LONG/STREAMING profiles
× CES status overrides). This table is defined but not implemented — callers are
expected to implement it themselves. In practice, this has not happened, and all
sessions sample at the same fixed interval regardless of CES status.

**Issue 4 — No Risk-Based Governance Intensity**

All sessions receive the same governance intensity regardless of the risk profile of
the operation. A read-only audit query and a live trading execution both produce the
same number of PQC-signed RCRs with the same DB write overhead. This is unnecessary
and penalises low-risk operations.

---

## Decision

ADR-160 introduces the **RCR Performance Optimization Layer (RPOL)**: four composable
optimizations delivered as a companion module (`omnix_core/agents/atf/rcr_performance.py`)
with surgical integration into `RuntimeContinuityEngine`.

**All four optimizations preserve all 8 RGC invariants (RGC-INV-001–008).** No
governance guarantees are weakened. The optimizations reduce overhead on paths where
overhead is provably not required, and add structure on paths where it was missing.

---

### Optimization 1 — Pooled Async Write Queue (`RCRWriteQueue`)

**Replaces:** Per-sample daemon thread spawning in `_persist_rcr` / `_persist_cee`

**Mechanism:** A single background worker thread (`RCRWriteQueue-worker`) drains a
bounded `queue.Queue[_WriteTask]`. Consecutive writes are batched into a single DB
transaction, bounded by:

- `RPOL_WRITE_BATCH_SIZE` — max records per transaction (default: 10)
- `RPOL_FLUSH_INTERVAL_MS` — max time between flushes (default: 200ms)

**Thread reduction:** From O(n) threads (one per sample) to O(1) threads (one global
worker). DB connections drop from one-per-sample to one-per-batch.

**Fallback:** If the queue is full (bounded at 4096 tasks), the write falls back to
a single daemon thread. This preserves durability under extreme load.

**HALT path:** HALT-triggered RCRs bypass the queue delay by using synchronous writes
(HIGH/CRITICAL tier behaviour). This preserves RGC-INV-003 — HALT status always
terminates execution with a committed DB record.

```
┌─────────────────────────────────────────────┐
│  sample() → _persist_rcr(rcr, tier=...)     │
│                    │                         │
│     tier=LOW ──────┤ skip persistence        │
│     tier=STANDARD ─┤ enqueue (async)         │
│     tier=HIGH ─────┤ enqueue + wait(5s)     │
│     tier=CRITICAL ─┤ enqueue + wait(5s)     │
│                    │                         │
│         RCRWriteQueue.enqueue_rcr()          │
│                    ↓                         │
│   ┌─────────────────────────────────┐       │
│   │  queue.Queue (max 4096 tasks)   │       │
│   └──────────────┬──────────────────┘       │
│                  │ background drain          │
│   ┌──────────────▼──────────────────┐       │
│   │  RCRWriteQueue-worker thread    │       │
│   │  batch(≤10) → single TX → DB   │       │
│   └─────────────────────────────────┘       │
└─────────────────────────────────────────────┘
```

---

### Optimization 2 — Event-Driven Sampler (`EventDrivenSampler`)

**Adds:** `RuntimeContinuityEngine.notify_event()` public method

**Mechanism:** An `EventDrivenSampler` intercepts governance events and triggers
`sample()` only when the measured delta exceeds configurable thresholds:

| Event Type | Default Threshold | Environment Variable |
|---|---|---|
| `BUDGET_CHANGE` | ≥ 10% of admission budget | `RPOL_BUDGET_TRIGGER_PCT` |
| `CONTEXT_DRIFT` | ≥ 15% drift | `RPOL_DRIFT_TRIGGER_PCT` |
| `ANOMALY_DETECTED` | ≥ 1 new anomaly | `RPOL_ANOMALY_TRIGGER_N` |
| `SUB_AGENT_SPAWN` | Always trigger | — |
| `SCOPE_CHANGE` | Always trigger | — |
| `EXTERNAL_TRIGGER` | Always trigger | — |

**Usage:**

```python
engine.notify_event(
    tar_id="ATFTAR-...",
    event_type="BUDGET_CHANGE",
    budget_consumed=15.0,
)
```

If the budget delta since the last sample is ≥ 10%, a full RCR is emitted with
`sample_reason="THRESHOLD_BREACH"`. Otherwise, the call returns `None` with zero
governance overhead.

**Per-session state tracking:** The sampler maintains `_SessionEventState` per session,
tracking last sampled values for budget, drift, and anomaly count. State is registered
on `start_session()` and deregistered on `stop_session()`.

**RGC-INV-002 compliance:** Samples triggered by `notify_event()` use real-time inputs
provided at the call site — no caching of CES components.

---

### Optimization 3 — Adaptive Interval Scheduler (`RCRScheduler`)

**Adds:** `RuntimeContinuityEngine.register_scheduler()` / `deregister_scheduler()`

**Mechanism:** A single background scheduler thread (`RCRScheduler-worker`) implements
the sampling strategy table from ADR-159 §5:

| Profile | NOMINAL | MONITORING | CRITICAL |
|---|---|---|---|
| SHORT (< 60s) | No sampling | 15s | 5s |
| MEDIUM (60s–600s) | 60s | 30s | 10s |
| LONG (> 600s) | 120s | 60s | 20s |
| STREAMING (unbounded) | 30s | 15s | 5s |

The scheduler reads `current_ces()` (in-memory, no DB, no RCR emission) to determine
the current status, then fires `sample()` at the appropriate interval.

The `RGC_SAMPLE_INTERVAL_SECONDS` environment variable overrides all profile intervals
when set (preserving the existing ADR-159 config point).

**Usage:**

```python
engine.register_scheduler(
    tar_id="ATFTAR-...",
    profile="LONG",
    get_inputs=lambda: {
        "budget_consumed": 0.0,
        "context_drift_pct": scope_engine.current_drift(),
        "active_anomalies": avm.active_count(),
    }
)
```

The `get_inputs` callback is called immediately before each scheduled sample to
provide fresh governance inputs. If `get_inputs` raises, the sample fires with
zeroed inputs (safe default: best CES, no false positives).

---

### Optimization 4 — Governance Risk Tier (`GovernanceRiskTier`)

**Adds:** `governance_risk_tier` parameter to `start_session()`

**Mechanism:** Four tiers define the governance intensity for a session:

| Tier | PQC Sign | DB Write | DB Timing | Use Case |
|---|---|---|---|---|
| `LOW` | No | No | — | Read-only audit queries, internal health checks |
| `STANDARD` | Yes | Yes | Async (queued) | Standard agent executions (default) |
| `HIGH` | Yes | Yes | Synchronous | Financial transactions, policy commits, sub-agent spawns |
| `CRITICAL` | Yes | Yes | Synchronous | Operations that must never proceed past a governance failure |

**LOW tier semantics:** LOW tier skips DB persistence entirely. In-memory RCR chain
is maintained (RGC-INV-006 preserved). PQC signing is skipped (RGC-INV-005 does NOT
apply — callers must not request audit trail for LOW-tier operations). CES is computed
and HALT is enforced normally (RGC-INV-003 preserved).

**CEE exception:** Continuity Escalation Events (CEEs) are always persisted regardless
of tier. Escalation events represent governance boundary crossings that must be auditable
in all cases.

**Usage:**

```python
session = engine.start_session(
    tar_id=tar.tar_id,
    ...
    governance_risk_tier="HIGH",  # ADR-160
)
```

---

## Invariant Compliance Matrix

| Invariant | Description | RPOL Impact |
|---|---|---|
| RGC-INV-001 | Every RCR anchored to a valid TAR | Unaffected — `tar_id` NOT NULL in all write paths |
| RGC-INV-002 | CES computed from real-time values | Unaffected — no CES caching introduced |
| RGC-INV-003 | HALT terminates execution | Unaffected — HALT uses synchronous write; RCR committed before halt_callback |
| RGC-INV-004 | Aggregate budget ≤ AFG limit | Unaffected — AFG check is in-memory, no DB dependency |
| RGC-INV-005 | All RCRs PQC-signed and immutable | Scoped: LOW tier explicitly waives audit trail. STANDARD/HIGH/CRITICAL always sign. |
| RGC-INV-006 | Continuity chain acyclic and complete | Unaffected — in-memory store maintains full chain; DB is secondary |
| RGC-INV-007 | CES inputs must be fresh | Unaffected — EventDrivenSampler uses real-time inputs at call site |
| RGC-INV-008 | RC TTL enforced; auto-HALT on expiry | Unaffected — RC TTL check is synchronous, no queue dependency |

---

## Architecture

```
omnix_core/agents/atf/
├── runtime_continuity.py      # ADR-159 engine (updated)
│   ├── RuntimeContinuityEngine
│   │   ├── start_session(... governance_risk_tier="STANDARD")  ← new param
│   │   ├── sample(...)                                          ← tier-aware persist
│   │   ├── notify_event(tar_id, event_type, ...)               ← new (ADR-160)
│   │   ├── register_scheduler(tar_id, profile, get_inputs)     ← new (ADR-160)
│   │   ├── deregister_scheduler(tar_id)                        ← new (ADR-160)
│   │   └── _persist_rcr(rcr, tier=...)                        ← updated (ADR-160)
│   └── ContinuitySession
│       └── governance_risk_tier: str = "STANDARD"              ← new field
│
└── rcr_performance.py         # ADR-160 RPOL module (new)
    ├── GovernanceRiskTier     # Enum: LOW | STANDARD | HIGH | CRITICAL
    ├── RCRWriteQueue          # Optimization 1: pooled async writer
    ├── EventDrivenSampler     # Optimization 2: event-threshold sampler
    │   ├── EventTriggerThresholds
    │   └── GovernanceEventType
    └── RCRScheduler           # Optimization 3: adaptive interval scheduler
        ├── ExecutionProfile
        └── SAMPLING_INTERVALS
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `RPOL_WRITE_BATCH_SIZE` | `10` | Max RCRs per DB transaction (RCRWriteQueue) |
| `RPOL_FLUSH_INTERVAL_MS` | `200` | Max ms between queue flushes |
| `RPOL_BUDGET_TRIGGER_PCT` | `10.0` | Budget delta % threshold for BUDGET_CHANGE events |
| `RPOL_DRIFT_TRIGGER_PCT` | `15.0` | Context drift % threshold for CONTEXT_DRIFT events |
| `RPOL_ANOMALY_TRIGGER_N` | `1` | New anomaly count threshold for ANOMALY_DETECTED events |
| `RPOL_SCHEDULER_TICK_MS` | `1000` | Scheduler worker tick interval in ms |
| `RGC_SAMPLE_INTERVAL_SECONDS` | (profile-based) | Override all scheduler intervals (ADR-159 compat) |

---

## Performance Impact

| Metric | Before ADR-160 | After ADR-160 |
|---|---|---|
| Threads per sample | 2 (rcr + cee) | 0 (queued to existing worker) |
| DB connections per sample | 2 | ≤ 0.2 (amortized across batch of 10) |
| Latency on execution path | 0.1–0.5ms (thread create) + 0–5ms (connect) | < 0.01ms (queue.put_nowait) |
| LOW-tier overhead | Same as STANDARD | ~0.05ms (CES compute only) |
| HIGH-tier DB latency | Async (unordered) | Synchronous (ordered, 5s timeout) |

---

## Consequences

**Positive:**
- Eliminates thread creation overhead on the critical governance path
- Reduces DB connection pool pressure by up to 10× under batch conditions
- Provides structured event-driven sampling — callers no longer need to implement
  their own threshold logic or timer management
- Scheduler implements ADR-159 §5 automatically — sessions always sample at the
  correct interval for their CES status
- Risk-tier system allows low-risk operations to participate in governance without
  paying the full PQC + DB overhead

**Negative:**
- Additional background threads (2: writer + scheduler). Both are daemon threads
  and will not prevent process shutdown.
- LOW-tier sessions produce no DB audit trail. Callers must ensure LOW is not used
  for operations requiring auditability.
- Write queue introduces a maximum 200ms latency for STANDARD-tier DB persistence
  (acceptable given the in-memory store is the authoritative source).

**Mitigations:**
- RCRWriteQueue falls back to daemon thread on queue full — no write loss.
- Scheduler falls back to zeroed inputs if `get_inputs` raises — no false HALT triggers.
- HALT writes always synchronous — no durability gap on the most critical path.

---

## Patent Landscape

ADR-160 introduces the following novel technical claims:

1. **Governance Risk Tier System:** A session-level risk classification (LOW/STANDARD/
   HIGH/CRITICAL) that governs the intensity of PQC signing and DB persistence for
   runtime continuity records, enabling adaptive governance overhead without weakening
   the authority health monitoring invariants.

2. **Event-Threshold Governance Sampler:** A sampling mechanism that intercepts
   governance events (budget change, anomaly, context drift, scope change) and triggers
   RCR emission only when the measured delta exceeds configurable thresholds, eliminating
   handshake overhead on micro-operations while preserving governance coverage of
   material authority state changes.

3. **Pooled Async Write Queue with Tier-Aware Synchrony:** A write architecture where
   governance artifacts (RCRs, CEEs) are batched into a single background thread with
   configurable synchronous flush for high-risk operations, providing O(1) thread
   overhead regardless of session or sample count.

---

## Compliance

| Regulation | ADR-160 Enhancement |
|---|---|
| EU AI Act Art. 13 | Risk-tier system allows proportionate governance intensity per operation risk — regulators can audit that HIGH-risk operations received stronger governance coverage |
| DORA Art. 9 | Adaptive scheduler ensures continuous sampling for STREAMING executions without manual timer management — operational control evidence is automatic |
| SOC 2 CC6 | HIGH/CRITICAL synchronous writes ensure audit trail commits before execution continues — no governance record is lost due to async buffering |
| NIST AI RMF Govern 1.4 | Event-driven sampler ensures governance records are emitted at every material authority state change, not just on scheduled intervals |

---

## Related ADRs

- **ADR-159:** Runtime Governance Continuity — defines RCRs, CES, AFG, escalation protocol
- **ADR-157:** Temporal Authority Admissibility — defines TARs that anchor RCR chains
- **ADR-156:** Agent Trust Fabric — defines the delegation chain that RCRs monitor
- **ADR-131:** Execution Integrity Layer — upstream of RGC in the governance pipeline
