# ADR-070: Context Admission Gate CP-1 — Epistemic Transparency (score=0 on disabled/failsafe)

**Status:** Accepted  
**Date:** 2026-04-09  
**Author:** Harold Nunes  
**Scope:** `omnix_core/governance/context_admission_gate.py`

---

## Context

Post-ADR-068 forensic audit identified that CP-1 (Context Admission Gate, CAG) violated the same epistemic pattern as the compliance gates:

1. **Disabled path returned `admission_score=100.0`** — implying perfect global market conditions (vol=0, liq=100, macro=0) without any evaluation.
2. **`evaluate_session()` failsafe returned `admission_score=100.0`** — same fabrication on exception.
3. **No `evaluation_state` field** — no way to distinguish disabled/failsafe/evaluated in downstream audit or receipt.

The CAG gates the entire session before any checkpoint runs. A fabricated `admission_score=100` here propagates confidence through the entire 11-checkpoint pipeline and into PQC receipts.

---

## Decision

### 1. `CAGResult` dataclass

- `admission_score: float = 0.0` (was `100.0`)
- `liquidity_score: float = 0.0` (was `100.0` via comment)
- Added `evaluation_state: str = ""` field

### 2. Disabled path

```python
return CAGResult(
    admitted=True, pass_through=True,
    admission_score=0.0,
    evaluation_state="DISABLED",
    reason="CAG_DISABLED: score=0 reflects absence of evaluation, not perfect market conditions..."
)
```

### 3. `evaluate()` failsafe (exception)

```python
return CAGResult(
    admitted=True, pass_through=True,
    admission_score=0.0,
    evaluation_state="FAILSAFE",
    reason=f"CAG_FAILSAFE: score=0 reflects module error — {exc}..."
)
```

### 4. `evaluate_session()` failsafe (exception)

Same pattern: `admission_score=0.0`, `evaluation_state="FAILSAFE"`.

### 5. All `_run_admission_checks` return paths

Every return (blocked, admitted-with-warnings, fully-admitted) now includes `evaluation_state="EVALUATED"`.

---

## Consequences

- Downstream receipt builder and audit trail accurately reflect when session admission was not evaluated
- `evaluation_state` distinguishes three states for compliance dashboards
- Conservative failsafe: `admission_score=0` on error does not falsely signal perfect market conditions
- All 6 new tests pass (TestCAGADR070)

---

## Regulatory Alignment

- **EU AI Act Art. 9**: Risk management — session gates must not silently pass on error with fake confidence
- **MiFID II Circuit Breaker**: Session admission accuracy required
- **NIST AI RMF MAP-2.1**: Documented context gaps are required

---

## Tests Added

`tests/test_compliance_gates.py::TestCAGADR070` (6 tests):
- `test_disabled_gate_score_is_zero`
- `test_disabled_gate_evaluation_state_is_disabled`
- `test_evaluated_admitted_path_has_state_evaluated`
- `test_evaluated_blocked_path_has_state_evaluated`
- `test_failsafe_returns_zero_score`
- `test_disabled_gate_is_pass_through`
