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

## Follow-up Items (Not In Scope — ADR-124)

1. **Flask Dashboard other blueprints** — `str(e)` patterns in  
   `governance.py`, `market.py`, `verification.py`, etc. (lower priority:  
   all protected by `@require_api_key`).
2. **Rate limiter storage** — `storage_uri="memory://"` does not share  
   state across Railway worker processes. Upgrade to Redis-backed storage  
   for production-grade rate limiting under load.
3. **Silent `except Exception: pass`** in vertical metrics aggregation  
   (lines 778–941 `server.py`) — best-effort aggregation; should emit  
   `logger.debug()` for observability.

---

## Security Classification

- **Category:** External API Hardening  
- **OWASP Top 10 addressed:** A05 (Security Misconfiguration), A09 (Logging Failures)  
- **Governance layer:** Layer 0 (Infrastructure Security)  
- **Railway production impact:** ✅ Safe — no schema changes, no breaking API changes  
