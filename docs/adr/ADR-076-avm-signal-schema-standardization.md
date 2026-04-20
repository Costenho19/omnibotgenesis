# ADR-076: AVM Signal Schema Standardization

**Status:** Accepted  
**Date:** 2026-04-20  
**Author:** Harold Alberto Nunes Rodelo — OMNIX QUANTUM LTD  
**Supersedes:** None  
**Related:** ADR-064 (AVM), ADR-075 (Non-Finite Signal Guard)

---

## Context

The Assumption Validity Monitor (AVM) computes drift between calibrated baseline signals and live governance signals using `SIGNAL_WEIGHTS` — a fixed dictionary of 6 canonical keys with assigned drift weights.

During a production audit on 2026-04-20, a systematic bug was discovered: all 9 domain calibration snapshots used domain-specific signal names (e.g., `momentum_score`, `fraud_probability`, `safety_score`) that did not match the 6 canonical keys in `SIGNAL_WEIGHTS`. This caused two failure modes:

- **Real Estate**: 1 key in common (`risk_exposure`) → `_compute_drift` amplified drift by `(1 / total_weight) = 5x` → drift always 100 → all decisions BLOCKED.
- **Other 7 domains**: 0 keys in common → `total_weight = 0` → `drift = 0` → AVM always PASSED without validating anything.

Neither failure mode produced an error or warning. Both were silent.

---

## Decision

### 1. Single Source of Truth — `SIGNAL_SCHEMA`

All AVM signal key names are derived from a single constant in `assumption_validity_monitor.py`:

```python
SIGNAL_WEIGHTS: dict[str, float] = {
    "probability_score":  0.25,
    "signal_coherence":   0.25,
    "risk_exposure":      0.20,
    "stress_resilience":  0.15,
    "trend_persistence":  0.10,
    "logic_consistency":  0.05,
}

SIGNAL_SCHEMA: list[str] = list(SIGNAL_WEIGHTS.keys())
_SIGNAL_SCHEMA_SET: frozenset[str] = frozenset(SIGNAL_SCHEMA)
```

**Rule:** Any file that references AVM signal key names MUST import `SIGNAL_SCHEMA` from `assumption_validity_monitor.py`. Never hardcode the list.

### 2. Fail-Fast Validation in `save_calibration_snapshot`

```python
if frozenset(baseline_signals.keys()) != _SIGNAL_SCHEMA_SET:
    raise ValueError("[AVM] SCHEMA_VIOLATION — ...")
```

This prevents writing a snapshot with wrong keys. The error is raised at calibration time, not at evaluation time — hours or days later.

### 3. Schema Match Logging in `evaluate`

Every call to `avm.evaluate()` now logs:

```
[AVM] AVM_SCHEMA_MATCH=FULL | domain=real_estate | snapshot=AVM-EFCB730444 | age=0.0h
```

Possible values:
| Value | Meaning |
|---|---|
| `FULL` | All 6 SIGNAL_SCHEMA keys matched — drift detection fully operational |
| `PARTIAL(n/6)` | Some keys matched — drift score may be amplified or unreliable |
| `NONE` | Zero keys matched — drift detection silently disabled |

`PARTIAL` and `NONE` also log `SCHEMA_ANOMALY` at WARNING/ERROR level respectively.

### 4. Drift Anomaly Detection

If `drift_score >= 99.9` AND `schema_match != FULL`, a `DRIFT_ANOMALY` error is logged — distinguishing a genuine 100% drift from a schema mismatch bug.

### 5. Startup Guard in `initialize_avm_baselines`

`_validate_domain_baselines()` runs at import time and raises `ValueError` if any entry in `DOMAIN_BASELINES` uses keys that don't match `SIGNAL_SCHEMA`. This blocks deployment with wrong configuration.

---

## Canonical Signal Keys

| Key | Weight | Semantic |
|---|---|---|
| `probability_score` | 0.25 | Likelihood of a valid/safe outcome |
| `signal_coherence` | 0.25 | Internal consistency across signal inputs |
| `risk_exposure` | 0.20 | Aggregate risk level (inverted: higher = more drift) |
| `stress_resilience` | 0.15 | Ability to absorb adverse conditions |
| `trend_persistence` | 0.10 | Stability and directionality of the signal trend |
| `logic_consistency` | 0.05 | Logical alignment of the governance chain |

All domain simulators, DB tables, and external evaluators normalize their domain-specific signals into these 6 canonical dimensions before reaching the AVM.

---

## Recalibration After This ADR

All 9 domain snapshots were recalibrated on 2026-04-20 with values derived from real decision averages in PostgreSQL:

| Domain | Snapshot | Source Decisions |
|---|---|---|
| insurance | AVM-2B57256FDE | 40,307 claims |
| medical_ai | AVM-D7955570CB | 21,683 decisions |
| energy_governance | AVM-E97EC817A0 | 26,125 decisions |
| robotics | AVM-337323464D | 59,348 actions |
| autonomous_agent | AVM-9D32AF4C5D | 20,549 decisions |
| stablecoin | AVM-58B855C1B0 | 1,385 decisions |
| real_estate | AVM-EFCB730444 | 13,245 decisions |
| trading | AVM-EEEDB2BF18 | representative |
| islamic_credit | AVM-39FFC6F4D7 | representative |

---

## Consequences

### Positive
- Any future schema mismatch is caught at write time (ValueError) and at evaluation time (SCHEMA_ANOMALY log)
- `AVM_SCHEMA_MATCH=FULL/PARTIAL/NONE` gives instant visibility in production logs
- Single source of truth eliminates the class of bug entirely
- Startup guard prevents deploying with misconfigured DOMAIN_BASELINES

### Negative
- Adding a new signal key requires coordinated update of: `SIGNAL_WEIGHTS`, all snapshot files, all `save_calibration_snapshot` call sites, and DB column definitions
- Existing snapshots loaded from disk or DB are NOT validated against SIGNAL_SCHEMA at load time — only at evaluation time via logging

### Risks Accepted
- `trading` and `islamic_credit` baselines use representative values, not DB-derived averages, because their decision tables do not store the canonical signal columns. These should be updated when real averages become available.

---

## Enforcement

1. `save_calibration_snapshot()` → raises `ValueError` on wrong keys
2. `initialize_avm_baselines.py` → raises `ValueError` at import if `DOMAIN_BASELINES` violates schema
3. `evaluate()` → logs `AVM_SCHEMA_MATCH` on every call; logs `SCHEMA_ANOMALY` on NONE/PARTIAL
4. Code review: any PR touching `SIGNAL_WEIGHTS` or `SIGNAL_SCHEMA` requires explicit sign-off
