---
name: Production Hardening Layer
description: ADR-196/197/198/199 post-psycopg v3 migration hardening — stress tests, soak runner, observability, regression guard. Critical API constraints.
---

## The Rule
GovernanceRuntime API:
- `start_session(...)` → returns `OGRSession` object
- `record_turn(session_id: str, output_text, turn_metadata)` — takes **str**, NOT the OGRSession object
- `close_session(session_id: str)` — takes **str**, returns dict
- `get_session(session_id: str)` → OGRSession | None
- Always use `session.session_id` (str) for all subsequent calls after `start_session`.

## CTCHC Seal in Mock Mode
`close_session` calls `ctchc_engine.seal_chain(session_id)` which reads the chain from DB.
In mock mode (psycopg.connect mocked), the chain was never persisted → `RuntimeError: No chain found for session`.
**Fix:** wrap `close_session(sid)` in `try/except RuntimeError: pass` in any test that mocks psycopg.

## MemoryLeakMonitor Warm-Up
`MemoryLeakMonitor._MIN_ENFORCE_S = 60.0` — budget enforcement skipped for the first 60s of a soak run.
Without this, process startup (module imports, JIT) inflates RSS and triggers false SOAK-INV-001 violations.

## Reconnect Tracker in Mock Mode
`ReconnectFailureTracker.record_attempt(success)` should only be called with `success=False` for actual `psycopg.Error` exceptions.
Non-DB errors (e.g. API misuse) that happen inside the exerciser should call `record_attempt(True)` to avoid false SOAK-INV-004 violations.

## Test Results (2026-05-27)
- `tests/test_stress.py` — 10 passed, 0 failed, 1 skipped
- `tests/test_regression_psycopg.py` — 26 passed, 1 xfailed (intentional: pool timeout silent hang)
- Combined: 36 passed, 1 xfailed
- `tests/soak/soak_runner.py` mock-sprint — 4/4 cycles ✅, 0 violations

## ADR Index
| ADR | Sistema | Invariantes |
|---|---|---|
| ADR-196 | SVP Stress Validation Protocol | STRESS-INV-001–008 |
| ADR-197 | SRP Soak Reliability Protocol | SOAK-INV-001–007 |
| ADR-198 | GOL Governance Observability Layer | OBS-INV-001–006 |
| ADR-199 | PRG Psycopg v3 Regression Guard | REG-INV-001–006 |

**Why:** psycopg v3 migration across 93 files required permanent guards to prevent regression to psycopg2 patterns (dict_row API, exception hierarchy, FK violation handling).
**How to apply:** run `pytest tests/test_stress.py tests/test_regression_psycopg.py` after any change to governance pipeline or DB layer.
