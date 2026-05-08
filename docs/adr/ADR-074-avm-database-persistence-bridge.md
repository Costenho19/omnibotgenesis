# ADR-074 — AVM Database Persistence Bridge

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-10 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_core/governance/avm_db_bridge.py` |
| **Extends** | ADR-064 (Assumption Validity Monitor) |
| **Replaces** | — |

---

## Context

The Adaptive Veto Machine (AVM) maintained calibration snapshots in memory only. Each container restart (Railway deploy, crash recovery, scale-to-zero) erased all calibrated baselines, forcing a cold-start recalibration cycle that could last 30–60 minutes during which governance decisions used uncalibrated defaults.

Three additional enterprise concerns were identified:

1. **Tamper detection** — an in-memory snapshot could be silently overwritten by a bug or hostile module; no integrity proof existed.
2. **Audit trail for forced recalibrations** — regulatory auditors required evidence of *who* triggered a recalibration, *when*, and *why*.
3. **Fail-closed on DB errors** — if the database was reachable but returned corrupt data, the system must refuse to proceed rather than silently fall back to uncalibrated defaults.

## Decision

Implement a `AVMDatabaseBridge` class that persists every AVM snapshot to PostgreSQL with enterprise-grade integrity guarantees:

1. **SHA-256 hash stored with every snapshot.** On load, the hash is recomputed and compared. Any mismatch raises a `TAMPERED` flag and the snapshot is rejected.
2. **Change audit log.** Every `force=True` recalibration writes a record to `avm_calibration_log` with actor, reason, timestamp, and snapshot ID. A non-empty reason string is required.
3. **DB fail-closed mode.** If `AVM_FAIL_CLOSED=true` and the database returns a corrupt or tampered snapshot, governance halts with a `DEGRADED_MODE` signal rather than proceeding without validated baselines.
4. **Persist across container restarts.** Snapshots stored in Railway PostgreSQL survive deploys and scale-to-zero events.

```python
# Usage pattern (ADR-074)
bridge = AVMDatabaseBridge()
bridge.save_snapshot(domain="trading", snapshot=avm.export(), actor="auto_recalibration")
loaded = bridge.load_snapshot(domain="trading")   # raises TAMPERED if hash mismatch
```

## Schema

```sql
CREATE TABLE IF NOT EXISTS avm_calibration_snapshots (
    id           SERIAL PRIMARY KEY,
    domain       TEXT NOT NULL,
    snapshot_id  TEXT NOT NULL UNIQUE,
    payload      JSONB NOT NULL,
    sha256_hash  TEXT NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT now(),
    actor        TEXT,
    reason       TEXT
);

CREATE TABLE IF NOT EXISTS avm_calibration_log (
    id           SERIAL PRIMARY KEY,
    domain       TEXT NOT NULL,
    snapshot_id  TEXT NOT NULL,
    actor        TEXT NOT NULL,
    reason       TEXT NOT NULL,
    event_ts     TIMESTAMPTZ DEFAULT now()
);
```

## Consequences

**Positive:**
- AVM baselines survive container restarts — no cold-start degradation.
- Tamper detection provides cryptographic-grade assurance for institutional auditors.
- Audit log satisfies regulatory requirements for change management in automated governance systems.

**Negative:**
- DB round-trip on every snapshot load adds ~5–20ms startup latency.
- `AVM_FAIL_CLOSED=true` can halt the system if the DB is temporarily unavailable.

## Related

- ADR-064: Assumption Validity Monitor (AVM core design)
- ADR-075: Non-Finite Signal Guard (input validation into AVM)
- ADR-120: AVM Engine Auto-Recalibration (periodic recalibration scheduler)
