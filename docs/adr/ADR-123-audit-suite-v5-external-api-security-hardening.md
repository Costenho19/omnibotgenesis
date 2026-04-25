# ADR-123 — Audit Suite v5: External API Security Hardening (omnix_web + Flask Dashboard)

**Status:** ACCEPTED  
**Date:** 2025-04-25  
**Author:** OMNIX Quantum Ltd — Harold Alberto Nunes Rodelo  
**Scope:** `omnix_web/api/server.py` · `omnix_dashboard/blueprints/core.py`

---

## Context

Audit Suite v5 targets the external-facing API layer deployed on Railway
(`omnixquantum.net`). The public server (`server.py`, 3 380 lines) and the
internal Flask Dashboard (`core.py`, 2 714 lines) were audited for:

- Error detail leakage to clients (exception messages in JSON responses)
- Absent structured logging (`print()` used in route handlers)
- Overly permissive rate-limiting configuration
- Missing request body size enforcement
- Input validation gaps in high-traffic email endpoint
- Silent exception swallowing without observability

---

## Issues Identified and Fixed

### 1 — No structured logging in `server.py`  
**Risk:** MEDIUM — `print()` in route handlers bypasses the Python logging  
infrastructure; in Railway/Railway deployments log aggregation targets  
`stderr` via the logging framework, not stdout `print`.

**Fix:** Added `import logging` + `logger = logging.getLogger(__name__)`  
at module level. All route-handler `print()` calls replaced with  
`logger.error()` / `logger.warning()`.

Files affected:
- `omnix_web/api/server.py` — lines 85, 91, 709, 1159, 1238, 1283, 1797,  
  1853, 2001, 2040

---

### 2 — Error detail leakage to external clients (`str(e)` in responses)  
**Risk:** HIGH — Exception messages can expose internal DB table names,  
column names, module import paths, and configuration details to any  
unauthenticated caller.

**Occurrences fixed:**

| File | Pattern | Endpoints affected |
|---|---|---|
| `server.py` | `"error": str(e)` | 12 vertical governance endpoints |
| `server.py` | `"message": str(e)` | 6 domain stats endpoints |
| `server.py` | `f'Verifier unavailable: {e}'` | `/api/trust/verify` |
| `server.py` | `f'Trust registry unavailable: {e}'` | `/api/trust/registry` |
| `server.py` | `f'Framework catalog unavailable: {e}'` | `/api/trust/frameworks` |
| `server.py` | `'detail': str(e)` | `/api/trust/health` |
| `server.py` | `{'error': str(e), 'live': False}` | `/api/analytics/decisions` |
| `server.py` | `{'error': str(e)}` | `/api/sandbox/stats` |
| `core.py` | `'error': str(e)` | 17 dashboard endpoints |

**Fix:** Added `_api_error(exc, ctx)` helper that:
1. Logs the full exception internally (`logger.error`)  
2. Returns a **generic** message to the client: `"Internal server error"`

All `str(e)` patterns in API responses replaced; no exception detail  
ever crosses the API boundary.

---

### 3 — No default rate limit on the Limiter  
**Risk:** HIGH — `default_limits=[]` means every endpoint without an  
explicit `@limiter.limit()` decorator is entirely unlimited. This exposes  
unauthenticated read endpoints to trivial DoS scraping.

**Fix:**
```python
# Before
default_limits=[]

# After — ADR-123
default_limits=["200 per minute"]
```

Endpoints with explicit decorators (`/api/contact`: 5/min 20/hr;  
`/api/trust/verify`: 60/min; `/api/public/send-receipt`: 3/min 10/hr)  
are unaffected — explicit limits take precedence over defaults.

---

### 4 — No request body size limit  
**Risk:** MEDIUM — Unlimited POST body size allows memory-exhaustion  
attacks on endpoints such as `/api/trust/verify` which accept arbitrary  
JSON payloads.

**Fix:**
```python
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1 MB hard cap
```

Flask returns HTTP 413 automatically when the limit is exceeded.

---

### 5 — `int()` without error handling in `/api/public/send-receipt`  
**Risk:** HIGH — Three consecutive bare `int(data.get(...))` calls on  
unvalidated user input. Any non-integer value (string, float-string,  
`null`) raises `ValueError`, which propagates as an unhandled 500.

**Fix:**
```python
# Before (raises ValueError on bad input)
cp_passed  = int(data.get('checkpoints_passed', 0))
cp_total   = int(data.get('checkpoints_total', 11))
cp_blocked = int(data.get('checkpoints_blocked', 0))

# After — ADR-123
try:
    cp_passed  = int(data.get('checkpoints_passed', 0))
    cp_total   = int(data.get('checkpoints_total', 11))
    cp_blocked = int(data.get('checkpoints_blocked', 0))
except (ValueError, TypeError):
    cp_passed, cp_total, cp_blocked = 0, 11, 0
```

---

### 6 — No type validation for `gate_results` and `receipt` fields  
**Risk:** MEDIUM — `data.get('gate_results', [])` returns whatever the  
client sends; a non-list value (e.g. `"gates"` or `123`) causes  
`for g in gates:` to iterate over characters or raise `TypeError`.

**Fix:**
```python
raw_gates = data.get('gate_results', [])
gates     = raw_gates if isinstance(raw_gates, list) else []
receipt   = data.get('receipt', {}) if isinstance(data.get('receipt', {}), dict) else {}
```

---

### 7 — Unvalidated `language` field in send-receipt  
**Risk:** LOW — `language` was accepted as any string; only `'en'` and  
`'es'` are valid values used in template conditionals.

**Fix:**
```python
language = data.get('language', 'en') if data.get('language') in ('en', 'es') else 'en'
```

---

### 8 — `print()` in global error handlers (lines 85, 91)  
**Risk:** LOW — Error handlers used `print()` instead of `logger.error()`,  
bypassing log aggregation.

**Fix:** Both handlers now call `logger.error("[OMNIX.API] ...")`.

---

## Test Validation

All existing tests pass after changes:

| Suite | Result |
|---|---|
| Code Verification | 7/7 ✅ |
| Critical Audit | 17/17 ✅ |
| Response Validator | 16/16 ✅ |
| Systemic Router | 27/27 ✅ |
| **Total** | **67/67** ✅ |

---

## Follow-up Items (Resolved In Appendix Below)

All three follow-up items from the original ADR-123 have been completed in the
same session — see Appendix A.

---

## Appendix A — Full Codebase Consistency Pass (Post ADR-123)

**Scope:** all governance blueprints + `system.py` + `governance_reports.py`  
**Date completed:** 2026-04-25  
**Tests after pass:** 27/27 + 16/16 + 27/27 = **70/70 ✅**

### A.1 — Vertical Governance Blueprints (`str(e)` → generic)

Pattern fixed in every blueprint below using `replace_all`:

| File | Pattern replaced | Count |
|---|---|---|
| `medical_governance.py` | `{"success":False,"error":str(e)},500` | all |
| `agents_governance.py` | same | all |
| `real_estate_governance.py` | same | all |
| `energy_governance.py` | same | all |
| `robotics_governance.py` | same + `"status":"error"` variant | all |
| `stablecoin_governance.py` | same | all |
| `insurance_governance.py` | same + degraded-mode `str(e)` | all |
| `credit_governance.py` | `{"status":"error","message":str(e)},500` | all |
| `snapshots.py` | `'error':str(e)` | all |
| `intelligence.py` | `'error':str(e)` | all |

### A.2 — ADR-122 Modules Verified Clean

`exit_governance.py`, `human_oversight.py`, `execution_protocol.py` —
audited, zero `str(e)` in API responses, zero silent `except:pass`.

### A.3 — `system.py` (7 patterns)

| Line (approx) | Pattern | Fix |
|---|---|---|
| 465 | `enterprise_health['error'] = str(e)[:100]` | `"Component unavailable"` + `logger.error()` |
| 547 | `f'Container not available: {str(e)}'` | `"Container unavailable"` + `logger.warning()` |
| 549 | `f'Health check failed: {str(e)}'` | `"Health check failed"` + `logger.error()` |
| 848 | `'error': str(e)` in equity endpoint | `"Internal server error"` |
| 1069 | `'error': str(e)` in shadow portfolio | `"Internal server error"` |
| 1279 | `"error": str(e)` in AVM status | `"Internal server error"` |
| 1395 | `"error": str(exc)` in layer0 metrics | `"Internal server error"` |

All `logger.error()` calls retained / added with structured `type(e).__name__` format.

### A.4 — `governance_reports.py`

Line 629: `"detail": str(e)` removed from PDF error response.
`logger.error()` already present — no information lost for operators.

### A.5 — `server.py` — Remaining `print()` and Silent `except`

- Line 2330: `print(f'[EMAIL ERROR] {e}')` → `logger.error("[OMNIX.API] [send_receipt_email] %s: %s", ...)`
- 15 silent `except Exception: pass` blocks (vertical stats aggregation, DID patching,
  ADR count fallback, trust verifier, CP analytics) — all replaced with:
  ```python
  except Exception as e:
      logger.debug("[OMNIX.API] best-effort skipped: %s: %s", type(e).__name__, e)
  ```
  Behavior unchanged; full observability added.

### A.6 — Decisions: Acceptable Patterns (No Change)

| Pattern | Reason |
|---|---|
| `ValueError → 400` in `governance_incidents/risk/metrics` | Controlled validation messages from internal engine; all routes require `_require_auth()` |
| `return False, str(e)` in `governance_alerts._deliver_*()` | Internal delivery helper; result stored in DB + logged, never returned to API client directly |

---

## Security Classification

- **Category:** External API Hardening + Full Codebase Hardening  
- **OWASP Top 10 addressed:** A05 (Security Misconfiguration), A09 (Logging Failures)  
- **Governance layer:** Layer 0 (Infrastructure Security)  
- **Railway production impact:** ✅ Safe — no schema changes, no breaking API changes  
