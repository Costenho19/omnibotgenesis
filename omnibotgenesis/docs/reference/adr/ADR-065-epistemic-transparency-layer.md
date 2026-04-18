# ADR-065: Epistemic Transparency Layer — Correcting Manufactured Confidence

**Date:** 2026-04-09
**Status:** Accepted
**Author:** Harold Nunes, OMNIX QUANTUM LTD
**Triggered by:** Internal governance audit (post Dr. Ioana challenge, April 2026)

---

## Context

During a governance review session, a systematic pattern was identified across multiple OMNIX
subsystems: **manufactured confidence in the absence of evidence**.

This is a first-order epistemic failure — not a technical bug, but a design assumption that
conflates "no data" with "good conditions". The pattern was named after the first public challenge
that exposed it: a governance expert (Dr. Ioana) demonstrated that a system can issue confident
decisions even when its foundational assumptions have never been validated.

OMNIX ADR-064 (Assumption Validity Monitor) resolved the first instance of this pattern for
calibration drift. ADR-065 resolves four additional instances discovered in the subsequent audit.

---

## The Pattern: Manufactured Confidence

**Correct behaviour**: Absence of evidence → explicit declaration of uncertainty (score=0,
warning in trace, `pass_through=True`)

**Incorrect behaviour (pre-ADR-065)**: Absence of evidence → high confidence score assumed,
pipeline proceeds as if conditions are normal

This pattern is identical to what caused Terra/LUNA's collapse: the system continued operating
with inherited confidence while the foundations eroded beneath it.

---

## Four Instances Found and Fixed

### Instance 1 — TCV: Perfect Score Without Trajectory History

**File**: `omnix_core/temporal/coherence_validator.py`

**Before**: When `len(events) < min_events` (insufficient trajectory history), the system returned
`trajectory_score=100.0` with `pass_through=True`. A brand-new system with zero history received
the maximum possible trajectory coherence score — the opposite of honest uncertainty.

The same problem occurred in the module failsafe (exception path): `trajectory_score=100.0`.

Sub-scores also inflated without evidence:
- `_score_direction_coherence`: returned 75.0 when < 2 data points
- `_score_signal_stability`: returned 80.0 when < 2 direction samples

**After**:
- All pass-through paths return `trajectory_score=0.0`
- Reason string explicitly documents: `"score=0 reflects absence of evidence, not trajectory failure"`
- Sub-scores return 0.0 when insufficient data
- `pass_through=True` remains the decision mechanism — a 0 score does not block the pipeline,
  it honestly communicates that no trajectory assessment was possible

**Downstream safety**: `auto_trading_bot.py` uses `admissible` (not score) for veto decisions.
Score change from 100→0 is safe. Bot stores score for telemetry only.

---

### Instance 2 — OPTIONAL_SIGNAL_DEFAULTS: Automatic Approval Without Data

**File**: `omnix_core/governance/external_evaluator.py`

**Before**: When callers omit `signal_integrity` or `temporal_coherence`, the system substituted
defaults that automatically pass their respective checkpoints:
- `signal_integrity=75.0` → passes CP-0 (threshold=60) and CP-10 (threshold=50)
- `temporal_coherence=65.0` → passes CP-7 (threshold=45)

No record was kept that a default was used. A regulator reading the decision receipt could not
distinguish between "caller provided signal_integrity=75" and "system assumed 75 because no data".

**After**:
- Default values are unchanged (backward-compatible with existing clients)
- Every default substitution is tracked in `applied_defaults` dict
- A `SIGNAL_DEFAULT_APPLIED` entry is written to `decision_trace` for each defaulted signal,
  naming the affected checkpoints
- `applied_signal_defaults` dict is included in the evaluation result
- Downstream audit can always distinguish real data from assumed defaults

**Design rationale for keeping default values**: Changing defaults to below-threshold values would
break existing clients. The transparency fix (documenting when defaults are used) achieves the
regulatory objective without backward-incompatible behavior. A future ADR should propose migrating
to "borderline defaults" (value = threshold) via versioned API contract.

---

### Instance 3 — CAG: Optimistic Market Assumption Without Data

**File**: `omnix_core/governance/external_evaluator.py`

**Before**: When the Context Admission Gate (CAG) is enabled but no real market data is provided
by the caller, it evaluates against defaults:
- `global_volatility=0.0` (perfectly calm — below the 80.0 threshold)
- `cross_pair_correlation=0.0` (perfectly uncorrelated — below the 90.0 threshold)
- `liquidity_score=100.0` (perfect liquidity — above the 20.0 minimum)
- `macro_risk=0.0` (no macro risk — below the 85.0 ceiling)

All four checks pass. The session is admitted with score=100 on the assumption of ideal market
conditions — when in reality, conditions are simply unknown.

**After**:
- When all four CAG context parameters are absent from the caller's `compliance_config`,
  a `CAG_WARNING` is written to `decision_trace`
- The warning is also added to `context_admission_block["epistemic_warning"]` in the result
- CAG admission behavior is unchanged — the warning is informational, not blocking

**Detection logic**: Checks for absence of the four CAG keys in `cfg`. If none are present,
all parameters came from defaults. If any are present, the caller has provided real data.

---

### Instance 4 — Fraud Gate: Circular Validation

**File**: `omnix_core/governance/external_evaluator.py`

**Before**: CP-10 (Fraud Detection Gate) receives inputs derived entirely from signals that
already passed earlier checkpoints:
- `dci_score` ← derived from `logic_consistency` (CP-6 signal)
- `technical_score` ← `probability_score` (CP-1 signal)
- `sentiment_score` ← `signal_coherence` (CP-3 signal)

Signals coherent enough to pass CP-1, CP-3, and CP-6 are almost certainly coherent enough to
pass CP-10 as well. This is not independent fraud detection — it is re-validation of already
approved signals.

**After**:
- A `FRAUD_PROXY_MODE` entry is written to `decision_trace` before every CP-10 evaluation
- `compliance_blocks["fraud_compliance"]` includes `proxy_mode: True` and
  `proxy_source_signals` documenting the derivation chain
- Fraud gate behavior is unchanged — the limitation is documented, not circumvented

**Long-term resolution**: Independent fraud detection requires an independent data source
(microstructure data, external fraud signals, behavioral anomaly detection not derived from
the governance pipeline's own signals). This is a product roadmap item, not an immediate fix.

---

## What the Epistemic Transparency Layer Provides

Every evaluation result now includes:

```json
{
  "decision_trace": [
    "SIGNAL_DEFAULT_APPLIED: signal_integrity=75.0 — not provided by caller (affects: CP-0, CP-10)",
    "CAG_WARNING: all context parameters are defaults — no real market data provided...",
    "FRAUD_PROXY_MODE: CP-10 inputs derived from pipeline-approved signals..."
  ],
  "applied_signal_defaults": {
    "signal_integrity": 75.0,
    "temporal_coherence": 65.0
  }
}
```

And in TCV results:
```json
{
  "trajectory_score": 0.0,
  "pass_through": true,
  "reason": "INSUFFICIENT_TRAJECTORY_DATA: 1 events < 3 required — pass-through (score=0 reflects absence of evidence, not trajectory failure)"
}
```

---

## Files Modified

| File | Change |
|------|--------|
| `omnix_core/temporal/coherence_validator.py` | TCV pass-through score 100→0; sub-scores 75/80→0 without data |
| `omnix_core/governance/external_evaluator.py` | SIGNAL_DEFAULT_APPLIED trace; CAG_WARNING; FRAUD_PROXY_MODE; applied_signal_defaults in result |

---

## Regulatory Alignment

| Standard | Relevance |
|----------|-----------|
| EU AI Act Art. 13 | Transparency and provision of information — AI systems must be transparent and provide sufficient information to users |
| NIST AI RMF (MAP 2.3) | Risks from AI systems are documented and traceable |
| ISO 42001 §8.4 | AI system operations — uncertainty and limitations must be documented |
| Basel III (Model Risk) | Model outputs must distinguish "no data" from "good conditions" |
| MiFID II (audit trail) | All decision factors including data limitations must be in the audit trail |

---

## Decisions NOT Made

1. **Did not change default values** for `OPTIONAL_SIGNAL_DEFAULTS` — backward compatibility
   with existing B2B clients (Velos et al.). Future ADR to propose versioned migration.

2. **Did not fix the structural fraud gate limitation** — requires independent fraud data source
   which is a product roadmap item.

3. **Did not change `_score_regime_alignment` neutral returns** (65.0 when mixed/no regimes) —
   this is "ambiguous evidence", not "no evidence". A mixed regime is a valid signal of
   uncertainty, not a missing input. Kept at 65.0.

---

## Companion ADRs

- ADR-064: Assumption Validity Monitor (first instance of this pattern — calibration drift)
- ADR-032: Temporal Coherence Validation (TCV design)
- ADR-050: Context Admission Gate (CAG design)
- ADR-048: Fraud Detection Gate (CP-10 design)
- ADR-028: External Signal Evaluation API (pipeline design)
