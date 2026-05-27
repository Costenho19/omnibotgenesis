# ADR-197 — Soak Reliability Protocol (SRP)

**Status:** Accepted  
**Author:** Harold Nunes  
**Date:** 2026-05-27  
**Related:** ADR-196 (SVP), ADR-198 (GOL), ADR-184 (OGR), ADR-181/182/183 (BEV), ADR-194 (MIVP)  
**Implements:** `tests/soak/soak_runner.py` — `SoakRunner`

---

## Context

Infrastructure hardness is not proven by a passing CI suite. The failure modes that
matter in production emerge over time — not in milliseconds:

| Failure mode | Time horizon | Detectable by unit test? |
|---|---|---|
| Memory leak in governance cache | Hours | No |
| psycopg connection pool exhaustion | Hours–days | No |
| Stale OGR sessions (ACTIVE, never closed) | Hours | No |
| Orphan BEV records (BAR/CCS/CTCHC without parent session) | Days | No |
| Deadlock in concurrent governance + AVM recalibration | Minutes–hours | Rarely |
| DB reconnect failure after Railway dyno restart | Seconds | No |
| AVM calibration cache drift from PostgreSQL baseline | Days | No |

After the psycopg v3 migration, all of these paths changed at the driver level.
The `OperationalError` class hierarchy, the connection pool eviction policy, and
cursor lifecycle semantics are different in v3. A system that passes all 245+ tests
on startup may still leak or deadlock after six hours.

**Problem:** OMNIX has no long-running reliability validation capability. There is no
mechanism to leave the governance stack running for hours and automatically detect
the failure modes listed above.

**Competing approaches:**

- **Chaos Monkey / Gremlin**: infrastructure-level fault injection. No governance
  semantics, no OGR session lifecycle awareness.
- **Production monitoring (Railway logs)**: reactive, not proactive. Detects
  failures after they impact users.
- **Load testing (k6)**: measures throughput, not long-term stability. Terminates
  after the test window.

---

## Decision

Introduce the **OMNIX Soak Reliability Protocol (SRP)** — a long-running process
that governs the governance stack against time-domain failure modes.

### Architecture

```
tests/soak/soak_runner.py
│
├── SoakRunner                       — main orchestrator, runs indefinitely
│     ├── run()                      — main loop: one cycle = all probes
│     ├── _checkpoint()              — appends snapshot to soak_log.jsonl
│     └── _handle_violation()        — logs, alerts, optionally halts
│
├── MemoryLeakMonitor                — RSS growth tracker
│     ├── baseline()                 — captures initial RSS via tracemalloc + psutil
│     ├── sample()                   — captures current RSS
│     └── assert_within_budget()     — SOAK-INV-001: growth ≤ budget/hour
│
├── DeadlockWatchdog                 — detects hung threads / connections
│     ├── register_operation()       — marks an operation as in-flight
│     ├── complete_operation()       — marks completion
│     └── scan()                     — SOAK-INV-002: any in-flight > timeout → alert
│
├── StaleSessionScanner              — detects ACTIVE sessions past TTL
│     ├── scan()                     — queries atf_ogr_sessions WHERE status=ACTIVE
│     └── assert_none_stale()        — SOAK-INV-003: age > TTL → violation
│
├── ReconnectFailureTracker          — tracks consecutive reconnect failures
│     ├── record_attempt()           — +1 attempt, updates last_success_at
│     └── assert_converges()         — SOAK-INV-004: consecutive < max_attempts
│
├── OrphanRecordScanner              — BEV/MIVP referential integrity
│     ├── scan_bar_orphans()         — BAR without parent OGR session
│     ├── scan_ccs_orphans()         — CCS without parent OGR session
│     ├── scan_ctchc_orphans()       — CTCHC chain without parent OGR session
│     ├── scan_mas_orphans()         — MAS records without parent MBR
│     └── assert_no_orphans()        — SOAK-INV-005: zero orphans
│
└── SoakCheckpoint                   — append-only evidence record
      ├── to_dict()                  — serializes all probe results
      └── write()                    — appends to tests/soak/soak_log.jsonl
```

### Operation Modes

| Mode | Duration | DB | Interval |
|---|---|---|---|
| **Mock sprint** | 60 seconds | In-memory | 5s |
| **Overnight** | 8 hours | Live (opt-in) | 60s |
| **Production shadow** | Continuous | Live | 300s |

Default is mock sprint — executes in CI to prove the soak machinery itself works.
Live modes require `OMNIX_HARDENING_ALLOW_LIVE_DB=true`.

### SoakRunner Main Loop

```python
while not self._stop_event.is_set():
    cycle_start = time.monotonic()
    results = self._run_probe_cycle()
    checkpoint = SoakCheckpoint(
        cycle_number=self._cycle,
        elapsed_seconds=time.monotonic() - self._start_time,
        results=results,
        violations=[v for v in results.values() if v.violated],
    )
    checkpoint.write(self._log_path)
    if checkpoint.has_critical_violation():
        self._handle_critical(checkpoint)
    self._sleep_until_next_cycle(cycle_start)
```

---

## Invariants

### SOAK-INV-001 — Memory Growth Budget
*RSS memory growth MUST NOT exceed `SOAK_MEMORY_BUDGET_MB_PER_HOUR` (default: 50 MB/hour)
over the soak window. Measured via `psutil.Process.memory_info().rss`.*

**Violation action:** Log `[SOAK][VIOLATION] SOAK-INV-001`, append to checkpoint,
raise `SoakViolation` if `SOAK_HALT_ON_VIOLATION=true`.

### SOAK-INV-002 — Deadlock-Free Operations
*No governance operation (start_session, record_turn, close_session, AVM recalibration)
remains in-flight longer than `SOAK_DEADLOCK_TIMEOUT_S` (default: 30 seconds).*

**Violation action:** `DeadlockWatchdog.scan()` logs the hung operation ID, thread ID,
and elapsed time. Appended to checkpoint as `deadlock_candidate`.

### SOAK-INV-003 — No Stale Sessions
*No row in `atf_ogr_sessions` has `status = 'ACTIVE'` with
`created_at < NOW() - INTERVAL '{SOAK_SESSION_STALE_TTL_S} seconds'` (default: 3600s).*

**Violation action:** `StaleSessionScanner` logs session_id, age, agent_id. Stale
sessions are **not** automatically closed — violation is reported only (closing
requires human authorization per OGR-INV-001).

### SOAK-INV-004 — Reconnect Convergence
*After any `psycopg.OperationalError`, the connection is re-established within
`SOAK_RECONNECT_MAX_ATTEMPTS` (default: 5) consecutive attempts. If not, the
soak reports a `reconnect_failure` and increments the violation counter.*

**Violation action:** After `max_attempts` exceeded, `ReconnectFailureTracker`
appends `reconnect_exhausted=true` to checkpoint.

### SOAK-INV-005 — No BEV/MIVP Orphan Records
*Every row in `atf_behavioral_anchor_records`, `atf_constraint_conformance_signals`,
`atf_coherence_hash_chains`, and `atf_mandate_alignment_scores` MUST have a
corresponding row in `atf_ogr_sessions` (via `session_id` foreign key).*

**Verification query:**
```sql
SELECT COUNT(*) FROM atf_behavioral_anchor_records bar
LEFT JOIN atf_ogr_sessions s ON s.session_id = bar.session_id
WHERE s.session_id IS NULL;
```
*Expected: 0. Any non-zero result is a SOAK-INV-005 violation.*

### SOAK-INV-006 — AVM Cache Consistency
*The AVM in-memory calibration cache MUST NOT diverge from the `avm_calibration_snapshots`
table by more than `SOAK_AVM_DRIFT_TOLERANCE` (default: 0.05) on any domain.*

**Verification:** `SoakRunner` calls `/api/health/ready` and compares the AVM
domain scores reported there against the last `avm_calibration_snapshots` row.

### SOAK-INV-007 — Append-Only Checkpoint Log
*`tests/soak/soak_log.jsonl` grows by exactly one record per cycle. Records are
never modified or deleted. SHA-256 of each record is stored in the next record
to form a simple hash chain.*

**Verification:** `SoakCheckpoint.write()` computes `prev_hash` from the last
record before appending. Any tampering breaks the chain.

---

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `SOAK_CYCLE_INTERVAL_S` | `60` | Seconds between probe cycles |
| `SOAK_MEMORY_BUDGET_MB_PER_HOUR` | `50` | Max RSS growth (MB/hour) |
| `SOAK_DEADLOCK_TIMEOUT_S` | `30` | Hung-operation threshold (seconds) |
| `SOAK_SESSION_STALE_TTL_S` | `3600` | Max ACTIVE session age (seconds) |
| `SOAK_RECONNECT_MAX_ATTEMPTS` | `5` | Max consecutive reconnect attempts |
| `SOAK_AVM_DRIFT_TOLERANCE` | `0.05` | AVM cache/DB drift tolerance |
| `SOAK_HALT_ON_VIOLATION` | `false` | Exit process on any violation |
| `OMNIX_HARDENING_ALLOW_LIVE_DB` | `false` | Enable live DB probes |
| `SOAK_DURATION_SECONDS` | `0` (∞) | Run duration (0 = infinite) |

---

## Running the Soak

```bash
# Mock sprint (60s, CI-safe)
python tests/soak/soak_runner.py --mode mock-sprint

# Overnight live soak (8 hours, requires Railway DATABASE_URL)
OMNIX_HARDENING_ALLOW_LIVE_DB=true \
SOAK_DURATION_SECONDS=28800 \
python tests/soak/soak_runner.py --mode overnight

# Continuous (production shadow, runs until Ctrl+C)
OMNIX_HARDENING_ALLOW_LIVE_DB=true \
python tests/soak/soak_runner.py --mode continuous
```

---

## Consequences

**Positive:**
- Time-domain failure modes (leaks, orphans, stale sessions) are now detectable
  before they impact production users
- The checkpoint log is a governance artifact — auditors can verify the system
  ran reliably over N hours
- SOAK-INV-007 (hash chain) makes the log tamper-evident for compliance purposes

**Negative:**
- Live soak requires real DATABASE_URL — cannot fully validate memory/reconnect
  behavior in mock mode
- SOAK-INV-003 (stale sessions) requires human review before closing — the soak
  runner cannot take remediation action autonomously

**Mitigation:**
- Mock sprint validates the soak machinery itself and runs in CI
- Stale session alerts are forwarded to the Telegram admin channel via
  `TELEGRAM_ADMIN_USER_ID` if configured

---

## Related Records

| Record | Type | Description |
|---|---|---|
| `tests/soak/soak_log.jsonl` | Append-only evidence | One record per cycle |
| `tests/soak/stress_log.jsonl` | Append-only evidence | One record per stress run (SVP) |
| ADR-196 (SVP) | Stress protocol | Burst/concurrency validation |
| ADR-198 (GOL) | Observability layer | Metrics fed into soak checkpoints |
