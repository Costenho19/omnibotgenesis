# ADR-199 — Psycopg v3 Regression Guard (PRG)

**Status:** Accepted  
**Author:** Harold Nunes  
**Date:** 2026-05-27  
**Related:** ADR-196 (SVP), ADR-197 (SRP), ADR-198 (GOL)  
**Implements:** `tests/test_regression_psycopg.py`

---

## Context

On 2026-05-27, OMNIX migrated 93 files from `psycopg2` to `psycopg` (v3). The
migration was completed in a single session and is production-deployed. The risk
of behavioral regression is material:

### Why psycopg v3 Breaks psycopg2 Code Silently

| Behavior | psycopg2 | psycopg v3 | Risk if wrong |
|---|---|---|---|
| Row type | `tuple` (default) | `tuple` (default) | Low |
| Dict rows | `RealDictCursor` | `row_factory=dict_row` | **HIGH** — silent KeyError |
| UUID registration | `register_uuid()` required | Native, automatic | Low — was removed |
| Exception base class | `psycopg2.Error` | `psycopg.Error` | **HIGH** — wrong catch |
| FK violation class | `psycopg2.errors.ForeignKeyViolation` | `psycopg.errors.ForeignKeyViolation` | **HIGH** |
| Pool timeout | `pool.PoolTimeout` | `psycopg_pool.errors.PoolTimeout` | **HIGH** |
| Cursor context manager | Closes cursor | Closes cursor | Low |
| Connection autocommit | `False` (default) | `False` (default) | Low |
| `extras.execute_values` | Available | Not available — use `executemany` | Medium |

**The three highest-risk behaviors:**

1. **dict_row contract.** 34 files in `omnix_core/` were migrated from
   `cursor_factory=RealDictCursor` to `row_factory=dict_row`. A row returned from
   a `dict_row` cursor responds to string key access (`row["session_id"]`). If any
   migrated call site accidentally uses tuple index access (`row[0]`), it silently
   returns the wrong value. This is the most dangerous silent regression class.

2. **Exception class hierarchy.** 22 files have `except psycopg.OperationalError`
   blocks. If any catch block was missed or uses the wrong class (e.g., `except
   psycopg2.OperationalError` or bare `except Exception`), FK violations or
   reconnect failures will be swallowed silently instead of surfacing.

3. **FK violation handling.** `database_service.py` was specifically hardened to
   catch `psycopg.errors.ForeignKeyViolation` and auto-create the missing user row.
   This path must never regress — a FK violation that is not caught means a silent
   failure to save a conversation record in Railway production.

**What unit tests cannot catch:**

- Whether `row_factory=dict_row` is set on the *connection* or only on a *cursor*
  (the scope matters)
- Whether `psycopg.errors.ForeignKeyViolation` is a subclass of `psycopg.Error`
  in the installed version of psycopg
- Whether the pool raises `psycopg_pool.errors.PoolTimeout` vs
  `psycopg.OperationalError` for different exhaustion conditions
- Whether all 93 migrated files import `psycopg` and not `psycopg2` at runtime

---

## Decision

Introduce the **Psycopg v3 Regression Guard (PRG)** — a dedicated regression test
suite that permanently locks the behavioral contracts established by the migration.

Every test in this suite corresponds to a known failure mode. If psycopg is
downgraded, a dependency is corrupted, or a future migration re-introduces psycopg2
code, these tests fail loudly before Railway deployment.

### Test Suite Architecture

```
tests/test_regression_psycopg.py
│
├── TestPsycopgImportContracts       — no psycopg2 in production code
│     ├── test_no_psycopg2_in_omnix_core()
│     ├── test_no_psycopg2_in_omnix_services()
│     └── test_psycopg_v3_importable()
│
├── TestDictRowContract              — dict_row behavioral guarantees
│     ├── test_dict_row_string_key_access()
│     ├── test_dict_row_not_tuple()
│     ├── test_dict_row_on_connection_scope()
│     └── test_dict_row_missing_key_raises_keyerror()
│
├── TestExceptionHierarchy           — psycopg v3 exception class contracts
│     ├── test_operational_error_is_psycopg_error()
│     ├── test_integrity_error_is_psycopg_error()
│     ├── test_foreign_key_violation_is_integrity_error()
│     ├── test_unique_violation_is_integrity_error()
│     └── test_no_psycopg2_exception_classes_caught()
│
├── TestFKViolationHandling          — FK auto-recovery path (database_service.py)
│     ├── test_fk_violation_is_caught_not_swallowed()
│     ├── test_save_conversation_retries_on_fk_violation()
│     └── test_ensure_user_exists_retry_logic()
│
├── TestRowFactoryScope              — row_factory set at connection level
│     ├── test_row_factory_on_connection_propagates_to_cursor()
│     └── test_row_factory_override_on_cursor()
│
└── TestPoolTimeout                  — pool exhaustion behavior
      ├── test_pool_timeout_is_detectable()
      └── test_no_silent_hang_on_exhaustion()
```

### REG-INV-006 — No Railway Required

All tests in this suite run with `TESTING=true` and no `DATABASE_URL`. The psycopg
import and exception hierarchy are verified by import inspection and in-memory
mocking. No network connection is required.

---

## Invariants

### REG-INV-001 — Row Shape Contract Stability
*Any row returned from a cursor configured with `row_factory=dict_row` MUST respond
to string key access (`row["column_name"]`) and MUST NOT require integer index
access. This contract is permanent and applies to all 34 migrated call sites.*

**Verification test:** `test_dict_row_string_key_access()` — creates an in-memory
psycopg mock that simulates dict_row behavior and asserts `row["session_id"]`
returns the expected value while `row[0]` raises `TypeError`.

### REG-INV-002 — FK Violation Surfaces
*`psycopg.errors.ForeignKeyViolation` MUST NOT be caught by a bare
`except Exception` block in `omnix_services/database_service/database_service.py`.
It MUST be caught explicitly as `psycopg.errors.ForeignKeyViolation` (or its parent
`psycopg.errors.IntegrityError`) and trigger the auto-user-creation retry path.*

**Verification test:** `test_fk_violation_is_caught_not_swallowed()` — patches
`psycopg.connect` to raise `psycopg.errors.ForeignKeyViolation` on first call,
then verifies `save_conversation` calls `ensure_user_exists` and retries.

### REG-INV-003 — Typed Exception Hierarchy
*`psycopg.errors.ForeignKeyViolation` is a subclass of `psycopg.errors.IntegrityError`,
which is a subclass of `psycopg.Error`. This MUST hold in the installed version.
No production code catches `psycopg2.Error` or any psycopg2 exception class.*

**Verification test:** `test_foreign_key_violation_is_integrity_error()` and
`test_no_psycopg2_exception_classes_caught()` — static AST scan of all
`omnix_core/` and `omnix_services/` Python files.

### REG-INV-004 — Pool Exhaustion is Detectable
*When the psycopg connection pool is exhausted, the timeout MUST be detectable via
`psycopg_pool.errors.PoolTimeout` (or `psycopg.OperationalError` in connection-mode).
It MUST NOT cause a silent hang or a bare `Exception` with no actionable type.*

**Verification test:** `test_pool_timeout_is_detectable()` — mocks `pool.getconn()`
to raise `PoolTimeout`. Verifies the caller catches it as a typed exception.

### REG-INV-005 — No Implicit Tuple Access
*No production file in `omnix_core/` or `omnix_services/` accesses database rows
by integer index (`row[0]`, `row[1]`) when the connection uses `row_factory=dict_row`.
All access is via string key (`row["column_name"]`).*

**Verification test:** `test_dict_row_not_tuple()` — static grep for patterns
`row[0]`, `rows[0][0]`, `result[0][0]` in files that also contain
`row_factory=dict_row`.

### REG-INV-006 — TESTING Mode Sufficiency
*The entire regression suite MUST pass with `TESTING=true` and no `DATABASE_URL`
set. No test in this suite requires a Railway connection, a running PostgreSQL
instance, or any external service.*

**Verification:** CI runs `test_regression_psycopg.py` before any Railway deploy.
If `DATABASE_URL` is present, the test logs it but does not use it.

---

## Consequences

**Positive:**
- Any future migration (psycopg → psycopg 4, or any other DB driver) will be
  blocked from reaching Railway if it breaks these contracts
- The static AST scan (REG-INV-003, REG-INV-005) catches entire categories of
  bugs that no runtime test can find
- The FK violation path (REG-INV-002) protects the most user-visible production
  bug fixed in this migration

**Negative:**
- Static scans are brittle against code refactors — the grep patterns must be
  updated if the codebase structure changes significantly
- Mock-based tests (REG-INV-001, REG-INV-004) cannot verify the exact behavior
  of the installed psycopg version — only that exception classes exist

**Mitigation:**
- Static scan patterns are version-controlled in the test file itself and
  reviewed in every PR that touches `omnix_core/` or `omnix_services/`
- A separate integration test (in `tests/integration/`) handles live psycopg
  behavior — this suite handles the contracts only

---

## Related Records

| Record | Type | Description |
|---|---|---|
| `tests/test_regression_psycopg.py` | Implementation | PRG test suite |
| ADR-196 (SVP) | Sibling | Stress validation |
| ADR-197 (SRP) | Sibling | Soak reliability |
| ADR-198 (GOL) | Sibling | Observability layer |
