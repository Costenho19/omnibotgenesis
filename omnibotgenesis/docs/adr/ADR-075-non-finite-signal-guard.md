# ADR-075: Non-Finite Signal Guard — Fail-Closed under NaN/Inf inputs

**Status:** ACCEPTED  
**Date:** 2026-04-09  
**Author:** Harold Nunes, OMNIX QUANTUM LTD  
**Audit trigger:** Forensic Audit Ronda 3 — Bloque H (Fail-closed under real exceptions)

---

## Context

During Forensic Audit Ronda 3 (2026-04-09), a critical bypass was confirmed in the
Assumption Validity Monitor (`_compute_drift`):

```python
# BEFORE FIX (vulnerable)
raw_drift = abs(current_val - baseline_val)
# If current_val = NaN: abs(NaN - 70.0) = NaN
# components[signal] = min(NaN, 100.0) = NaN
# weighted_drift += 0.25 * NaN = NaN
# ...
# drift_score = NaN
# if NaN > 35.0: → False (Python NaN comparison)
#   → BLOCK  ← never reached
# → PASS (CRITICAL: governance approved under undefined input)
```

**Severity:** CRITICAL  
**Impact:** Any NaN or Inf value in a governance signal caused the AVM to silently
approve decisions that should have been blocked. This bypassed the core
fail-closed guarantee of the pipeline.

**Reproduction:**
```python
avm = AssumptionValidityMonitor()
avm.save_calibration_snapshot("trading", {"probability_score": 70.0, ...})
result = avm.evaluate({"probability_score": float('nan'), ...}, domain="trading")
assert result.is_valid  # True — CRITICAL BYPASS
```

---

## Decision

Implement a two-layer non-finite signal guard in `AssumptionValidityMonitor`:

### Layer 1 — evaluate() first-line guard (primary)

Before calling `_compute_drift`, validate all input signals:

```python
non_finite_signals = [
    f"{k}={v}"
    for k, v in signals.items()
    if isinstance(v, (int, float)) and not math.isfinite(v)
]
if non_finite_signals:
    return AVMResult(
        is_valid=False,
        drift_score=100.0,
        block_reason=f"NON_FINITE_SIGNAL — {non_finite_signals[:4]}",
        pass_through=False,
    )
```

### Layer 2 — _compute_drift() defensive clamp (backup)

If non-finite values reach `_compute_drift` (e.g. from baseline, or direct calls):

```python
if not math.isfinite(baseline_val) or not math.isfinite(current_val):
    components[signal] = 100.0   # maximum drift → ensures BLOCK
    weighted_drift += weight * 100.0
    continue
```

---

## Blocking Policy (precedence order, strictest wins)

| Priority | Condition | Result |
|----------|-----------|--------|
| 1 | Any signal is NaN or Inf | `NON_FINITE_BLOCK`, `is_valid=False` |
| 2 | Snapshot age > `critical_age_hours` | `CRITICAL_STALE`, `is_valid=False` |
| 3 | Weighted drift > `effective_threshold` | `DRIFT_BLOCK`, `is_valid=False` |
| 4 | All checks pass | `PASS`, `is_valid=True`, `pass_through=False` |

---

## pass_through=True Semantics (contract clarification)

`pass_through=True` means the AVM had **no baseline to compare against**.  
It does **NOT** mean the decision is certified.

**Downstream integrators MUST treat `pass_through=True` as `NON_CERTIFIED`.**

| `is_valid` | `pass_through` | Meaning |
|------------|----------------|---------|
| `True` | `False` | **CERTIFIED** — AVM verified, drift acceptable |
| `False` | `False` | **BLOCKED** — STALE, DRIFT, or NON_FINITE |
| `True` | `True` | **NON_CERTIFIED** — no baseline (AVM disabled or no snapshot) |

---

## Fail-safe policy (§4.4)

Internal AVM exceptions propagate to the caller.  
The pipeline-level exception handler **must** treat any AVM exception as **BLOCK**,  
never as PASS. This is contrary to the pre-ADR-075 docstring which said  
"AVM exceptions → pass-through".

**The correct policy is: when in doubt, block.**

---

## Consequences

- **Positive:** NaN/Inf signals are now an explicit, auditable governance event.
  Every non-finite block produces a `block_reason` with the offending signal values.
- **Positive:** Dual-layer defense (evaluate + _compute_drift) ensures no single
  point of failure can produce a silent PASS.
- **Positive:** `pass_through` semantics are now formally documented.
- **Neutral:** Signals outside [0, 100] (e.g. -10, 999) are still accepted but
  drift is clamped to 100.0. This is by design — clipping is safer than blocking
  on range, which would require domain-specific range policies.
- **Risk:** If upstream code generates NaN from a bug, the AVM block will surface
  the issue as a governance event rather than hiding it. This is the desired behavior.

---

## Tests

- `tests/test_forensic_audit_ronda3.py::TestFailClosedUnderException::test_H1_nan_in_single_signal_blocks_evaluation`
- `tests/test_forensic_audit_ronda3.py::TestFailClosedUnderException::test_H2_positive_infinity_blocks_evaluation`
- `tests/test_forensic_audit_ronda3.py::TestFailClosedUnderException::test_H3_negative_infinity_blocks_evaluation`
- `tests/test_forensic_audit_ronda3.py::TestFailClosedUnderException::test_H4_all_nan_signals_blocks`
- `tests/test_forensic_audit_ronda3.py::TestFailClosedUnderException::test_H6_compute_drift_with_nan_clamps_not_passes`
- `tests/test_forensic_audit_ronda3.py::TestHostileInputFuzzing::test_C4_nan_in_single_of_six_signals_blocks`

---

## References

- ADR-064: Assumption Validity Monitor — original specification
- ADR-074: Enterprise Governance Baseline (SHA-256, versioning, fail-closed)
- Forensic Audit Ronda 3 — OMNIX QUANTUM LTD, 2026-04-09
- Python docs: IEEE 754 float, `math.isfinite()`, NaN comparison semantics
