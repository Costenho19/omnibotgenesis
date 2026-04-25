# ADR-122 — Audit Suite v4: Exit Governance + Human Oversight + Execution Boundary Hardening

**Status:** Accepted — Implemented 25 Apr 2026
**Author:** Harold Alberto Nunes Rodelo
**Scope:** Exit Governance Layer, Human Oversight Engine, Execution Protocol
**Triggered by:** OMNIX Audit Suite v4 — systematic gap scan of modules not covered by Audit Suites v2.0 (ADR-116–ADR-120) and v3 (ADR-121)

---

## 1. Context

Following Audit Suite v3 (ADR-121), a second gap scan identified three modules that had been imported as passing by the audit runner but never subjected to deep inspection of their fail-safe posture, exception handling, and canonical interface consistency:

| Module | Gap Identified |
|---|---|
| `omnix_core/governance/exit_governance.py` | `ExitGovernanceResult` fields `should_exit`, `reason`, `confidence` had no default values — uninitialized result could not be constructed without explicit args; bare `except: pass` in `_get_conn()`; no canonical alias |
| `omnix_core/governance/human_oversight.py` | `_get_conn()` used `os.environ["DATABASE_URL"]` — raises unhandled `KeyError` if env var not set; no fallback to `OMNIX_DB_URL` |
| `omnix_services/execution_service/execution_protocol.py` | No canonical alias for audit tooling (`ExecutionProtocolEngine`); confirmed no bare `except:pass` — architecture sound |

---

## 2. Decisions

### 2.1 ExitGovernanceResult — Fail-Safe Defaults

**Problem:** `ExitGovernanceResult` was a `@dataclass` with three required positional fields (`should_exit: bool`, `reason: str`, `confidence: float`). Any code path that instantiated the dataclass without these values would raise `TypeError` rather than returning a safe default.

**Decision:**

```python
@dataclass
class ExitGovernanceResult:
    # ADR-122 Fail-Safe Default Policy:
    # should_exit=False means HOLD — the safe direction on uninitialized result.
    # This default is only reached if ExitGovernanceEngine crashes before returning;
    # normal paths always set this field explicitly.
    # NOTE: EGL uses fail-THROUGH (not fail-closed) on error — see pass_through flag.
    should_exit: bool = False
    reason: str = "EGL_UNINITIALIZED"
    confidence: float = 0.0
```

**Rationale:** For exit decisions, `should_exit=False` means HOLD — the more conservative direction. If a position is held when it should have been exited, capital is preserved (not destroyed). This is the correct fail-safe direction for exit governance.

**Important distinction:**

| Error mode | Behavior | Trigger |
|---|---|---|
| `ExitGovernanceEngine` internal error | **FAIL-THROUGH** — uses `pass_through=naive_exit` (ADR-036) | Runtime exception during gate evaluation |
| `ExitGovernanceResult` constructed without args | **FAIL-SAFE** — `should_exit=False` (hold) | Uninitialized result (edge case, audit tooling) |

The `pass_through` flag in the result dataclass documents which mode is active. `pass_through=True` means the naive price-comparison result was used; `pass_through=False` means the 3-gate pipeline ran to completion.

### 2.2 ExitGovernanceResult — `_get_conn()` Exception Logging

**Problem:** Two bare exception handlers in `_get_conn()` silenced errors without logging:

```python
except ImportError:
    pass   # ← swallowed silently
...
except Exception:
    return None   # ← swallowed silently
```

**Decision:**

```python
except ImportError:
    logger.debug("[EGL] psycopg2 not available — trying psycopg3")
...
except Exception as exc:
    logger.warning("[EGL] psycopg3 connection failed: %s", exc)
    return None
```

**Rationale:** DB connection failures during exit receipt storage are non-critical (storage is best-effort) but must be visible in logs for operational debugging. The debug level for ImportError is appropriate since psycopg2/psycopg3 availability depends on the deployment environment and is not an error condition.

### 2.3 ExitGateResult — Canonical Alias

```python
# ── Canonical alias (ADR-122) ──────────────────────────────────────────────────
# ExitGateResult is the preferred name in audit scripts and external tooling.
# ExitGovernanceResult remains the primary class name for backward compatibility.
ExitGateResult = ExitGovernanceResult
```

Follows the alias convention established in ADR-121 for all governance gate result types.

### 2.4 HumanOversightEngine — _get_conn() Environment Variable Safety

**Problem:**

```python
def _get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])
```

Two failure modes:
1. `os.environ["DATABASE_URL"]` raises `KeyError` if the variable is not set — unhandled, propagates to caller
2. No fallback to `OMNIX_DB_URL` (the canonical OMNIX database secret)

**Decision:**

```python
def _get_conn():
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("OMNIX_DB_URL")
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL not configured — HumanOversightEngine requires database access. "
            "Set DATABASE_URL environment variable."
        )
    return psycopg2.connect(db_url)
```

**Rationale:**
- `os.environ.get()` returns `None` instead of raising — prevents silent crashes
- `OMNIX_DB_URL` fallback aligns with the canonical secret name used across all OMNIX services
- `RuntimeError` with descriptive message replaces opaque `KeyError` — operators get actionable error information
- `HumanOversightEngine` legitimately requires database access (EU AI Act Art. 14 audit trail) — failing loudly with a clear message is correct behavior

### 2.5 ExecutionProtocolEngine — Canonical Alias

```python
# ── Canonical alias (ADR-122) ──────────────────────────────────────────────────
# ExecutionProtocolEngine is the preferred name in audit scripts and tooling.
# ExecutionProtocol remains the primary class name for backward compatibility.
ExecutionProtocolEngine = ExecutionProtocol
```

**Architecture confirmed:** `ExecutionProtocol` already implements a correct fail-safe posture:
- `_get_fallback_decision()` — always returns conservative `LIMIT` order on exception
- `data_integrity_block` — blocks execution if both liquidity and correlation data missing
- Crisis avoidance — execution denied if `MarketCondition.CRISIS` or `contagion_risk > 80`
- Component resilience — each sub-engine (`LiquidityAnalyzer`, `MicroVolatilityEngine`, `CrossAssetCorrelationEngine`) fails independently without crashing the orchestrator

No structural changes required. Alias added for audit interface consistency.

---

## 3. Fail-Safe + Fail-Through Policy — Complete Gate Reference

### 3.1 Entry Gates (all fail-closed)

| Gate | Result Class | Alias | Default | Error behavior |
|---|---|---|---|---|
| AML Gate | `AMLVetoResult` | — | `admissible=False` | BLOCKED |
| Fraud Gate | `FraudVetoResult` | — | `admissible=False` | BLOCKED |
| Context Admission Gate | `CAGResult` | — | `admitted=False` | BLOCKED |
| Sharia Gate | `ShariaVetoResult` | `ShariaGateResult` | `admissible=False` | BLOCKED |
| Jurisdiction Gate | `JurisdictionVetoResult` | `JurisdictionGateResult` | `admissible=False` | BLOCKED |
| SAE (Layer 0) | `EvaluationRequest` | — | evaluated inline | BLOCKED |

### 3.2 Exit Gates (fail-through by design — ADR-036)

| Gate | Result Class | Alias | Default | Error behavior |
|---|---|---|---|---|
| Exit Governance Layer | `ExitGovernanceResult` | `ExitGateResult` | `should_exit=False` (HOLD) | FAIL-THROUGH: `pass_through=naive_exit` |

**Design rationale for FAIL-THROUGH on exit:** Trapping capital in a position indefinitely (fail-closed would mean "don't exit") would expose OMNIX to unlimited loss on volatile positions. A software error in the EGL must not prevent legitimate exits triggered by Stop Loss. Therefore: on EGL failure, the naive price-comparison result is used and the `pass_through=True` flag is set in the receipt. This is logged and auditable.

### 3.3 Execution Boundary

| Component | Class | Alias | Error behavior |
|---|---|---|---|
| Execution Protocol | `ExecutionProtocol` | `ExecutionProtocolEngine` | `_get_fallback_decision()` → conservative LIMIT |

### 3.4 Human Oversight

| Component | Class | DB Requirement | Error behavior |
|---|---|---|---|
| Human Oversight Engine | `HumanOversightEngine` | Mandatory | `RuntimeError` with descriptive message |

---

## 4. Audit Suite v4 Fixes Summary

| File | Fix | Category |
|---|---|---|
| `exit_governance.py` | `should_exit: bool = False`, `reason: str = "EGL_UNINITIALIZED"`, `confidence: float = 0.0` | Fail-safe default |
| `exit_governance.py` | `except ImportError: pass` → `logger.debug(...)` | Bare pass elimination |
| `exit_governance.py` | `except Exception: return None` → `logger.warning(...); return None` | Exception visibility |
| `exit_governance.py` | `ExitGateResult = ExitGovernanceResult` | Canonical alias |
| `human_oversight.py` | `_get_conn()` → `os.environ.get("DATABASE_URL") or os.environ.get("OMNIX_DB_URL")` | Env var safety |
| `human_oversight.py` | Missing env var → explicit `RuntimeError` with message | Error clarity |
| `execution_protocol.py` | `ExecutionProtocolEngine = ExecutionProtocol` | Canonical alias |

---

## 5. Test Results

| Suite | Tests | Status |
|---|---|---|
| Code Verification | 7 | ✔ 7 passed |
| Critical Audit | 17 | ✔ 17 passed |
| Total (both suites) | 24 | ✔ 24 passed |

Syntax validation (AST parse) confirmed clean for all 3 modified files before test run.

---

## 6. Consequences

- `ExitGovernanceResult` can now be instantiated without arguments — returns a safe HOLD default
- `_get_conn()` in `HumanOversightEngine` now checks `OMNIX_DB_URL` as fallback and raises `RuntimeError` (not `KeyError`) with an actionable message
- All bare `except:pass` patterns in exit governance are eliminated — DB connection failures are now logged
- Canonical audit aliases complete for all 3 remaining unaliased modules
- Full governance gate reference table established (ADR-122 Section 3) covering entry gates, exit gates, execution boundary, and human oversight in one canonical location
