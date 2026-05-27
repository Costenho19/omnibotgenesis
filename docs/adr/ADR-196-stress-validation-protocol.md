# ADR-196 — Stress Validation Protocol (SVP)

**Status:** Accepted  
**Author:** Harold Nunes  
**Date:** 2026-05-27  
**Related:** ADR-184 (OGR), ADR-194 (MIVP), ADR-181/182/183 (BEV), ADR-198 (GOL), ADR-199 (PRG)  
**Implements:** `tests/test_stress.py` — `GovernanceStressHarness`

---

## Context

On 2026-05-27, OMNIX completed a production-critical migration of 93 files from
`psycopg2` to `psycopg` (v3). This was the largest single-session infrastructure
change in the platform's history and touched every layer of the stack:

- `omnix_core/agents/atf/` — all 9 ATF modules  
- `omnix_core/bev/` — BAR, CCS, CTCHC  
- `omnix_core/governance/` — 22 governance modules  
- `omnix_core/govern/` — OGR orchestrator  
- `omnix_services/` — Telegram bot, database service, community intelligence  

**The risk surface is substantial:**

1. **Concurrency semantics changed.** `psycopg` v3 uses asyncio-native connection
   handling. Incorrect migration (mixing sync/async, leaking cursors, ignoring
   `row_factory`) causes silent data corruption or runtime crashes under load.

2. **Telegram burst patterns are untested.** Railway production sees spike patterns
   of 10–50 concurrent `/govern` and `/evaluate` commands when advisories are issued.
   None of these have been validated against the new driver.

3. **DB reconnection paths are new.** psycopg v3 raises `psycopg.OperationalError`
   on connection failure with different subclass hierarchy than psycopg2. Reconnect
   logic in `_get_conn()` across 31 files must be verified to catch the right class.

4. **Governance throughput has no established SLO.** `GovernanceRuntime.start_session /
   record_turn / close_session` spans 6 ATF layers and is the hot path. Without a
   measured baseline, regressions will go undetected.

5. **Session restoration correctness is unverified.** After a crash or Railway
   restart, in-progress OGR sessions must be detectable (status=ACTIVE, age > TTL)
   and not silently orphaned.

**Competing approaches examined:**

- **locust.io / k6**: generic HTTP load generators. No governance semantics, no
  OGR session lifecycle awareness, no ATF invariant checking.
- **pytest-benchmark**: micro-benchmark only. No concurrency model, no fault injection.
- **Hypothesis / property testing**: excellent for unit contracts, not for end-to-end
  governance throughput or Telegram spike simulation.

None of the above understand:
  1. What a `chain_tip_hash` is or why it must be monotonically updated.
  2. That `HALT` is a terminal state that must survive concurrent turns.
  3. That `row_factory=dict_row` changes the contract between DB and governance logic.

---

## Decision

Introduce the **OMNIX Stress Validation Protocol (SVP)** — a governance-aware
stress test suite that validates system behavior under the concurrency, fault, and
throughput conditions that matter for OMNIX production.

### Architecture

```
tests/test_stress.py
│
├── GovernanceStressHarness          — drives concurrent OGR sessions
│     ├── _run_session_worker()      — start + N turns + close (one coroutine)
│     ├── run_concurrent_sessions()  — asyncio.gather over N workers
│     └── assert_invariants()        — checks STRESS-INV-001..008 post-run
│
├── TelegramSpikeSimulator           — simulates burst of concurrent bot commands
│     ├── simulate_spike()           — N handlers dispatched simultaneously
│     └── assert_no_session_loss()   — verifies all sessions reached terminal state
│
├── ReconnectFaultInjector           — injects transient DB failures
│     ├── inject_failure()           — replaces _get_conn() with failing stub
│     ├── restore()                  — restores original connector
│     └── assert_typed_error()       — verifies psycopg.OperationalError raised
│
├── SessionRestorationProbe          — verifies stale session detection
│     └── assert_stale_detectable()  — ACTIVE sessions older than TTL are findable
│
└── GovernanceThroughputBenchmark    — measures OGR hot-path latency
      ├── run_benchmark()            — N sequential sessions, measures each phase
      └── assert_slo()               — checks STRESS-INV-005 (≥ 50 sessions/min)
```

### Dual-Mode Operation

All tests run in two modes, selected automatically:

| Mode | Condition | DB | Behavior |
|---|---|---|---|
| **Mock** | `TESTING=true` (default) | In-memory MagicMock | Full governance logic, no Railway needed |
| **Live** | `OMNIX_HARDENING_ALLOW_LIVE_DB=true` | Real PostgreSQL | End-to-end validation |

Live mode is **opt-in** and **never runs in CI** unless explicitly set. This prevents
Railway production from being hit by stress traffic during automated test runs.

### GovernanceStressHarness

The harness drives real `GovernanceRuntime` sessions (not mocked at the OGR level)
so that actual ATF/BEV/MIVP logic executes and timing reflects production cost:

```python
async def _run_session_worker(self, worker_id: int) -> SessionResult:
    rt = GovernanceRuntime()
    session = rt.start_session(
        agent_id=f"stress-agent-{worker_id}",
        governing_receipt_id=f"STRESS-RCP-{worker_id:04d}",
        domain="stress_test",
    )
    for turn_idx in range(self.turns_per_session):
        rt.record_turn(session, f"stress output turn {turn_idx}", {})
    rt.close_session(session)
    return SessionResult(session=session, worker_id=worker_id)
```

The DB layer is patched at `psycopg.connect` — all SQL calls succeed instantly in
mock mode, but the governance chain computation (hashing, signing, invariant checks)
runs with full fidelity.

---

## Invariants

### STRESS-INV-001 — Session Integrity Under Concurrency
*No session loses data or produces a corrupted `chain_tip_hash` when N sessions run
concurrently. Each session's hash chain is independent and deterministic.*

**Verification:** After `run_concurrent_sessions(N=20)`, every `OGRSession.chain_tip_hash`
is non-null, non-duplicate across sessions, and matches the hash recomputed from
`session.chain_genesis_hash + turn_outputs`.

### STRESS-INV-002 — Monotonic Turn Index
*`turn_count` within a single session is monotonically increasing even when
multiple coroutines attempt concurrent turns on the same session object.*

**Verification:** `session.turn_count == turns_per_session` after all workers complete.

### STRESS-INV-003 — HALT State Persistence
*A session in `STATUS_HALTED` MUST NOT be overwritten to `STATUS_ACTIVE` or
`STATUS_CLOSED` by any concurrent governance operation.*

**Verification:** Inject a HALT on session `N//2`. Verify no subsequent turn
changes `session.session_status` away from `STATUS_HALTED`.

### STRESS-INV-004 — Typed Reconnect Errors
*DB reconnection failures surface as `psycopg.OperationalError` (not bare `Exception`,
not `psycopg2.OperationalError`). No silent fallback.*

**Verification:** `ReconnectFaultInjector` patches `psycopg.connect` to raise
`psycopg.OperationalError`. All callers must catch exactly this type.

### STRESS-INV-005 — Governance Throughput SLO
*The hot path (`start_session → 3 turns → close_session`) completes at ≥ 50
sessions/minute in mock mode and ≥ 10 sessions/minute in live mode.*

**Verification:** `GovernanceThroughputBenchmark.assert_slo()` fails the test if
throughput falls below threshold. Threshold is configurable via
`OMNIX_STRESS_THROUGHPUT_SLO_MIN` env var.

### STRESS-INV-006 — psycopg v3 Exception Typing
*All database errors in `omnix_core/` and `omnix_services/` are caught as
`psycopg.Error` subclasses, never as `psycopg2.Error` or bare `Exception`.*

**Verification:** Grep-based static assertion confirms no `psycopg2` exception
class is referenced in any non-build Python file.

### STRESS-INV-007 — Hash Chain Determinism
*`chain_genesis_hash` is identical across two `start_session` calls with identical
inputs. The CTCHC genesis computation is side-effect-free.*

**Verification:** Two sessions with identical `agent_id`, `governing_receipt_id`,
and `domain` produce the same `chain_genesis_hash` value.

### STRESS-INV-008 — Tamper-Evident Stress Report
*Each stress run appends a structured result record to `tests/soak/stress_log.jsonl`
with timestamp, concurrency level, throughput, pass/fail, and failing invariant(s).
The log is append-only.*

**Verification:** `stress_log.jsonl` grows by exactly one record per run. Existing
records are never modified.

---

## Consequences

**Positive:**
- Production-confidence after every future migration or major refactor
- Establishes governance throughput SLOs with measurable baseline
- Detects psycopg regression classes that unit tests cannot find
- The stress log becomes an audit trail of infrastructure confidence

**Negative:**
- Mock mode hides real DB latency — live mode required for full confidence
- Hash chain determinism test (STRESS-INV-007) may flag intentional nonce injection

**Mitigation:**
- Live mode gated by `OMNIX_HARDENING_ALLOW_LIVE_DB=true` — never in CI unless explicit
- STRESS-INV-007 includes a `nonce_free=True` flag for the determinism sub-test

---

## Related Records

| Record | Type | Created by |
|---|---|---|
| `tests/soak/stress_log.jsonl` | Append-only run log | `GovernanceStressHarness.write_report()` |
| ADR-197 (SRP) | Soak test protocol | Harold Nunes 2026-05-27 |
| ADR-198 (GOL) | Observability layer | Harold Nunes 2026-05-27 |
| ADR-199 (PRG) | Regression guard | Harold Nunes 2026-05-27 |
