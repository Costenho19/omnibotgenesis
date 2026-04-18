# ADR-069: Fraud Gate CP-10 — Epistemic Transparency (score=0 on disabled/failsafe)

**Status:** Accepted  
**Date:** 2026-04-09  
**Author:** Harold Nunes  
**Scope:** `omnix_core/governance/fraud_gate.py`, `omnix_core/bot/auto_trading_bot.py`

---

## Context

During a post-ADR-068 forensic audit, CP-10 (Fraud Detection Gate) was found to exhibit two critical epistemic violations:

1. **`FraudVetoResult.integrity_score` defaulted to `100.0`** — meaning when the gate was disabled or raised an exception, the PQC-signed receipt recorded `integrity_score=100.0`, fabricating fraud-free confidence without any evaluation having occurred.

2. **`recent_reversals=0` was hardcoded** at the call site in `auto_trading_bot.py` (line 4188), making the reversal detection check permanently blind regardless of actual trade history. This is a silent proxy that never fires the rapid-reversal manipulation pattern check.

These violations are category-1 epistemic fabrication: a signed, immutable PQC receipt claiming fraud-free status (`integrity=100`) when the gate never ran.

---

## Decision

### 1. `FraudVetoResult` dataclass

- `integrity_score: float = 0.0` (was `100.0`) — absence of fraud evaluation ≠ fraud-free
- Added `evaluation_state: str = ""` field — distinguishes DISABLED / FAILSAFE / EVALUATED
- Added `reason: str = ""` field — explicit human-readable reason for pass-through

### 2. Disabled path

```python
return FraudVetoResult(
    admitted=True, pass_through=True,
    integrity_score=0.0,
    evaluation_state="DISABLED",
    reason="FRAUD_DISABLED: score=0 reflects absence of evaluation..."
)
```

### 3. Failsafe path (exception)

```python
return FraudVetoResult(
    admitted=True, pass_through=True,
    integrity_score=0.0,
    evaluation_state="FAILSAFE",
    reason=f"FRAUD_FAILSAFE: score=0 reflects module error — {exc}..."
)
```

### 4. All `_run_checks` paths

Every return in `_run_checks` now includes `evaluation_state="EVALUATED"`.

### 5. Bot: `_get_recent_reversals()` helper

New method on `AutoTradingBot`:
- Reads from in-memory `_recent_actions_cache` (populated by `_track_recent_action()`)
- Falls back to `database_service.get_recent_trades()` if cache empty
- Returns `(0, "PROXY")` if both unavailable

### 6. Bot: `_track_recent_action()` helper

Called after each finalized decision to maintain rolling action history (max 6 entries per symbol).

### 7. Bot: Proxy mode traces

When `_rev_source == "PROXY"`:
```
FRAUD_REVERSAL_PROXY_MODE: no action history for symbol; recent_reversals=0 (undercount possible)...
```

When `v52_analysis` absent:
```
FRAUD_SENTIMENT_PROXY_MODE: v52_analysis absent; sentiment_score=50.0 (neutral stub)...
```

### 8. Bot: `fraud_evaluation_state` stored in decision dict

```python
decision['fraud_evaluation_state'] = getattr(_fraud_result, 'evaluation_state', '')
```

---

## Consequences

- PQC receipts now record `integrity_score=0.0` (not 100.0) when gate is disabled/failed
- `evaluation_state` field in receipt distinguishes not-evaluated from evaluated-clean
- Reversal detection is now connected to real action history when available
- Proxy modes are explicitly documented in decision trace for audit dashboards
- All 7 new tests pass (TestFraudGateADR069, TestProxyModesADR072 partial)

---

## Regulatory Alignment

- **EU AI Act Art. 6**: High-risk AI systems must maintain audit trails — fabricated scores violate this
- **MiFID II**: Market manipulation detection must be operational, not silently bypassed
- **NIST AI RMF GOVERN-1.2**: Epistemic honesty — documented uncertainty is required

---

## Tests Added

`tests/test_compliance_gates.py::TestFraudGateADR069` (7 tests):
- `test_disabled_gate_score_is_zero`
- `test_disabled_gate_evaluation_state_is_disabled`
- `test_evaluated_path_has_evaluation_state_evaluated`
- `test_evaluated_gate_score_nonzero_on_clean_input`
- `test_failsafe_returns_zero_score`
- `test_reversal_detection_with_zero_reversals_passes`
- `test_high_reversal_count_triggers_violation`
