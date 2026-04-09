# ADR-073: Forensic Audit — 7 Silent Governance Bugs (073A–073G)

**Status:** ACCEPTED  
**Date:** April 9, 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Build:** 6.5.6 | Post-ADR-072 Forensic Audit

---

## Context

Following the completion of ADR-069/070/071/072, a secondary forensic audit of the governance
pipeline was conducted to identify any remaining silent data-quality issues. Seven bugs were
found, two of which were classified as CRITICAL — affecting the semantic correctness of the
CP-6 Sharia Gate for Islamic finance clients, and the API contract of the Context Admission Gate.

---

## Bugs Resolved

### BUG-073A — CRITICAL: Gharar Semantic Mismatch

**File:** `omnix_core/bot/auto_trading_bot.py`  
**Severity:** CRITICAL  
**Domain affected:** Islamic finance (UAE/GCC clients)

**Problem:**  
The bot was using `decision_contradiction_index` (DCI) as the `gharar_score` parameter for
the CP-6 Sharia Gate:

```python
# BEFORE (wrong):
_gharar_score = decision.get('decision_contradiction_index', 0.0)
```

These are semantically distinct concepts:
- **DCI** — measures whether RSI/MACD/Bollinger signals agree with each other internally
- **Gharar** (AAOIFI SS-59) — Islamic law concept: uncertainty, ambiguity, or speculative
  risk in a transaction (e.g., maysir, excessive speculation)

A BUY signal on a speculative meme token could have DCI=5 (perfect signal agreement)
but gharar=95 (extremely speculative under Islamic finance principles). The check would
never fire.

**Fix:**  
Introduced `_get_sharia_gharar_score(decision)` helper with priority waterfall:
1. `v52_analysis.gharar_score` → source="EXPLICIT" (semantically correct)
2. `v52_analysis.black_swan_prob × 100` → source="BLACK_SWAN_PROXY" (best available)
3. `decision_contradiction_index` → source="DCI_PROXY" (last resort, flagged in trace)
4. `0.0` → source="PROXY_ZERO" (no signal, flagged as underestimation risk)

Each non-EXPLICIT source emits a `SHARIA_GHARAR_*` trace entry explaining the limitation.

---

### BUG-073D — ALTO: Sharia `debt_ratio` Permanently 0.0

**File:** `omnix_core/bot/auto_trading_bot.py`  
**Severity:** HIGH (companion to 073A)

**Problem:**  
The Sharia Gate's `debt_ratio` parameter was never passed by the bot. The `evaluate()` 
signature's `debt_ratio=0.0` default meant the AAOIFI debt-ratio check (Check 4: 
`if debt_ratio > debt_ratio_max`) could never fire for any trading decision.

**Fix:**  
Introduced `_get_sharia_debt_ratio(decision)` helper:
- Checks `v52_analysis.debt_ratio` first (future integration point)
- Returns `(0.0, "PROXY_ZERO")` in spot crypto context — accurate because crypto
  protocols don't have conventional debt-to-assets balance sheets
- Emits `SHARIA_DEBT_RATIO_PROXY_ZERO` trace noting the AAOIFI check is architectural
  for Islamic equity/sukuk instruments, not spot trading

The `debt_ratio` parameter is now always passed to `gate.evaluate()` from the real value.

---

### BUG-073B — CRITICAL: CAG API Signature `liquidity_score=100.0`

**File:** `omnix_core/governance/context_admission_gate.py`  
**Severity:** CRITICAL  
**Affects:** All callers of `ContextAdmissionGate.evaluate()` and `evaluate_session()`

**Problem:**  
Both public methods had `liquidity_score: float = 100.0` as their default parameter.
ADR-072 fixed the call sites in `external_evaluator.py`, but the API contract itself
remained broken. Any new code calling `gate.evaluate(vol=50, corr=30, macro=20)` without
specifying `liquidity_score` would silently receive fabricated perfect liquidity.

**Fix:**  
```python
# BEFORE:
def evaluate(self, ..., liquidity_score: float = 100.0, ...):
def evaluate_session(..., liquidity_score: float = 100.0, ...):

# AFTER (ADR-073B):
def evaluate(self, ..., liquidity_score: float = 0.0, ...):
def evaluate_session(..., liquidity_score: float = 0.0, ...):
```

The default of `0.0` is the fail-safe direction: illiquid → blocks. Callers MUST supply
a real or proxy value. The docstring was updated with the rationale and a reference to
`_get_cag_market_params()` for the documented proxy mapping.

---

### BUG-073C — ALTO: Bot Paper Mode Liquidity Not in Decision Trace

**File:** `omnix_core/bot/auto_trading_bot.py` (`_get_cag_market_params`)  
**Severity:** HIGH

**Problem:**  
The paper mode liquidity proxy (`100.0`) was silently injected with no trace entry.
ADR-072 established the `CAG_LIQUIDITY_PROXY_MODE` pattern in `external_evaluator.py`,
but the bot's own CAG call never documented its liquidity source.

**Fix:**  
`_get_cag_market_params()` now tracks `_liquidity_source` with three explicit values:
- `"ENV_OVERRIDE"` — operator-injected via `CAG_LIQUIDITY_SCORE` env var
- `"PAPER_MODE_PROXY"` — paper mode, fills simulated at any size → 100.0
- `"LIVE_MODE_PROXY"` — live mode on Kraken major pairs → 85.0 (slight spread discount)

The source is:
1. Logged via `logger.info()` at every CAG session check
2. Included in the receipt `parameters` dict (embedded in `context_admission`)
3. Available for downstream trace inspection via the `_liquidity_source` key

---

### BUG-073E — SIGNIFICATIVO: HARAM_ASSET Return Missing `evaluation_state`

**File:** `omnix_core/governance/sharia_gate.py`  
**Severity:** SIGNIFICANT (consistency)

**Problem:**  
The early return for haram assets did not explicitly set `evaluation_state`:

```python
# BEFORE:
return ShariaVetoResult(
    admissible=False,
    violation="HARAM_ASSET",
    sharia_score=0.0,
    # evaluation_state relying on dataclass default "EVALUATED"
)
```

While the dataclass default of `"EVALUATED"` is technically correct, it was inconsistent
with ADR-066's principle of explicit state on all evaluation paths.

**Fix:**  
Added `evaluation_state="EVALUATED"` explicitly to the HARAM_ASSET return.

---

### BUG-073F — SIGNIFICATIVO: AVM NO_BASELINE Silent Pass-Through

**File:** `omnix_core/governance/external_evaluator.py`  
**Severity:** SIGNIFICANT

**Problem:**  
When AVM ran with no calibration snapshot (`snapshot_id="NO_BASELINE"`) or was disabled
(`snapshot_id="DISABLED"`), it silently passed through with no trace entry in the decision
record. Receipts were issued without any note that drift detection was inactive.

The existing code only added a trace for the `not pass_through` (valid) path:

```python
if not avm_result.pass_through:
    decision_trace.append("AVM VALID: drift=...")
# MISSING: what happens when pass_through=True?
```

**Fix:**  
Added explicit trace entries for all pass-through states:
- `snapshot_id="NO_BASELINE"` → emits `AVM_NO_BASELINE: Assumption Validity Monitor has no calibration snapshot...`
- `snapshot_id="DISABLED"` → emits `AVM_DISABLED: Assumption Validity Monitor disabled via AVM_ENABLED=false...`
- Other pass-through states → emits `AVM_PASS_THROUGH: snapshot={id} — running in pass-through mode`

Operators can now see in every receipt whether AVM was armed, disabled, or lacking a baseline.

---

### BUG-073G — SIGNIFICATIVO: TIE Signals 50.0 Without SIGNAL_DEFAULT_APPLIED

**File:** `omnix_core/governance/trajectory_invariant_engine.py`  
**Severity:** SIGNIFICANT

**Problem:**  
When signals were absent from `current_signals`, TIE silently defaulted all 6 signals to
`50.0`. This is neutral enough to never trigger any invariant threshold (all thresholds
are well above or below 50.0), but it silently biased trajectory history toward "healthy
neutral" without documentation. Operators couldn't distinguish "genuinely 50" from
"signal missing at evaluation time."

**Fix:**  
Added `signal_defaults: list[str]` field to `TIEResult` dataclass.  
In `_run_invariants()`, before building the window, tracks which of the 6 signals were
absent from `current`:

```python
signal_defaults = [
    f"TIE_SIGNAL_DEFAULT_APPLIED:{s}=50.0 (signal absent from caller)"
    for s in _TIE_SIGNALS
    if s not in current
]
```

Logged via `logger.debug()` and propagated to `TIEResult.signal_defaults`.

---

## Tests Added

**File:** `tests/test_compliance_gates.py`  
**New tests:** 27 (total: 112/112 passing, up from 85/85)

| Class | Count | Coverage |
|---|---|---|
| `TestGhararSemanticMismatchADR073A` | 11 | All 4 gharar proxy paths + debt_ratio + trace entries |
| `TestCAGSignatureADR073B` | 3 | inspect.signature defaults + zero-liquidity blocking |
| `TestPaperModeLiquidityTraceADR073C` | 3 | All 3 liquidity sources (ENV/PAPER/LIVE) |
| `TestHaramAssetEvaluationStateADR073E` | 3 | HARAM_ASSET / HALAL / DISABLED paths |
| `TestAVMNoBaselineTraceADR073F` | 3 | NO_BASELINE / DISABLED / VALID paths |
| `TestTIESignalDefaultsADR073G` | 4 | field exists + 0/3/6 signal default cases |

---

## Files Modified

| File | Change |
|---|---|
| `omnix_core/bot/auto_trading_bot.py` | Added `_get_sharia_gharar_score()`, `_get_sharia_debt_ratio()` helpers; updated Sharia gate call site; updated `_get_cag_market_params()` with `_liquidity_source` tracking |
| `omnix_core/governance/context_admission_gate.py` | `evaluate()` + `evaluate_session()`: `liquidity_score` default 100.0 → 0.0 |
| `omnix_core/governance/sharia_gate.py` | HARAM_ASSET return: added explicit `evaluation_state="EVALUATED"` |
| `omnix_core/governance/external_evaluator.py` | AVM pass-through paths documented in `decision_trace` |
| `omnix_core/governance/trajectory_invariant_engine.py` | `TIEResult.signal_defaults` field; `_run_invariants` tracks missing signals |
| `tests/test_compliance_gates.py` | +27 tests (073A–073G) |

---

## Proxy Mode Documentation Summary (cumulative ADR-069–073)

| Proxy | Source | Documentation |
|---|---|---|
| `AML_VOLUME` | cached transaction count | `AML_VOLUME_PROXY_MODE` in decision_trace |
| `FRAUD_SENTIMENT` | v52 absent → 50.0 | `FRAUD_SENTIMENT_PROXY_MODE` in decision_trace |
| `FRAUD_REVERSAL` | no history → 0 | `FRAUD_REVERSAL_PROXY_MODE` in decision_trace |
| `CAG_LIQUIDITY` (external) | 0.0 default | `CAG_LIQUIDITY_PROXY_MODE` in decision_trace |
| `CAG_LIQUIDITY` (bot) | paper=100 / live=85 | `_liquidity_source` in params + logger.info |
| `SHARIA_GHARAR` | DCI/BSP/PROXY_ZERO | `SHARIA_GHARAR_*` in decision_trace |
| `SHARIA_DEBT_RATIO` | 0.0 (crypto context) | `SHARIA_DEBT_RATIO_PROXY_ZERO` in decision_trace |
| `TIE_SIGNALS` | 50.0 neutral stubs | `signal_defaults` in TIEResult |
| `AVM_STATE` | NO_BASELINE / DISABLED | `AVM_NO_BASELINE` / `AVM_DISABLED` in decision_trace |

---

## Impact Assessment

No change in pipeline behavior for:
- Non-Islamic clients (Sharia Gate disabled by default)
- Clients with full signal data (gharar_score explicit in v52_analysis)
- Existing sessions passing through AVM (pass-through logic unchanged)

Breaking API change (additive, fail-safe direction):
- `CAGConfig.evaluate()` and `evaluate_session()` `liquidity_score` default: 100.0 → 0.0
- Any caller that omitted `liquidity_score` will now receive `0.0` instead of `100.0`
- This may cause more CAG blocks for callers without explicit liquidity — which is correct
  behavior (fail closed, not open)

---

*OMNIX QUANTUM LTD | Build 6.5.6 | ADR-073 | April 2026*
