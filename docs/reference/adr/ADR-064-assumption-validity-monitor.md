# ADR-064: Assumption Validity Monitor (AVM)

**Status**: Accepted — Implemented  
**Date**: April 9, 2026  
**Authors**: Harold Nunes, OMNIX Core  
**Internal Build Reference**: 6.5.5  
**Responds to**: Ioana V. (PhD Decision Architect) | Jennifer (Knightian uncertainty critique) | Naimat Khan (VELOS integration pre-requisite)

---

## Context

### The Problem OMNIX Already Solved

OMNIX's 11-checkpoint fail-closed pipeline validates every decision before execution. Temporal Coherence (CP-7, ADR-032) validates backward trajectory consistency. Trajectory Invariant Enforcement (TIE, ADR-053) validates that approved decisions don't push the system toward globally inadmissible regions.

### The Problem OMNIX Had Not Solved

All of the above assume that the **parameters** governing the checkpoints are still calibrated to conditions that reflect reality.

The critical question raised by Ioana V. (PhD Decision Architect):

> *"Who detects when the underlying conditions change? A system can certify under inherited confidence — confidence that was valid when earned but is no longer valid under current conditions."*

And by Jennifer (Knightian uncertainty critique):

> *"What happens when OMNIX certifies something under assumptions that are no longer valid, but the system doesn't detect it? VELOS will faithfully enforce a decision based on obsolete assumptions."*

These critiques point to the same gap: **assumption drift** — the divergence between the conditions at parameter calibration time and the conditions at evaluation time.

### Terra/LUNA as the Archetype

In the Terra/LUNA forensic reconstruction (documented in InstitutionalPage), OMNIX's Temporal Coherence gate caught "inherited confidence" — confidence that existed at T-72h but had been structurally invalidated by T-24h. The system correctly blocked it.

However, that reconstruction was applied to a known historical event. In live operation, the question is: **does OMNIX detect in real-time when its own calibration parameters have become structurally invalid?**

Without AVM, the answer was: **no**. The pipeline could certify with high confidence under assumptions calibrated for one regime while operating in a completely different one.

---

## Decision

Implement the **Assumption Validity Monitor (AVM)** as a pre-pipeline gate that:

1. Runs **before** every governance evaluation cycle — before CAG, before checkpoints
2. Compares current normalized signals against a calibration baseline snapshot
3. Computes a **drift score** (0–100) representing how far current conditions have moved from calibration conditions
4. **Blocks the pipeline** (fail-closed) if drift exceeds the configured threshold
5. Embeds `snapshot_id`, `parameter_version`, and `avm_drift_score` in every governance receipt
6. Provides a **parameter versioning system** so any receipt can be traced back to the exact calibration state that produced it

### Architecture Position

```
Signals → AVM (ADR-064) → CAG (ADR-050) → 11 Checkpoints → TIE (ADR-053) → Final Decision
          [STALE_BLOCK]   [SESSION_BLOCK]   [CHECKPOINT_VETO]  [HOLD]
          
AVM runs first. If assumptions are stale, no evaluation occurs.
The pipeline never certifies under conditions it was not calibrated for.
```

---

## Design

### CalibrationSnapshot

A snapshot captures:
- `snapshot_id`: Unique identifier (AVM-XXXXXXXXXX)
- `parameter_version`: Semantic version linked to this calibration
- `domain`: Which domain this snapshot covers (trading, credit, insurance, robotics)
- `calibrated_at`: ISO 8601 UTC timestamp
- `baseline_signals`: The normalized governance signals (0–100) at calibration time
- `checkpoint_thresholds`: The checkpoint threshold values at calibration time
- `drift_threshold`: The max allowed drift for this snapshot

Every governance **receipt** issued while this snapshot is active carries the `snapshot_id` and `parameter_version`. If the snapshot is later invalidated, all receipts issued under it can be traced and flagged.

### Drift Computation

Drift is computed as a **weighted L1 distance** across governance signals:

```
drift_score = Σ(weight_i × |current_signal_i - baseline_signal_i|) / Σ(weight_i)
```

Signal weights (must sum to 1.0):

| Signal | Weight | Rationale |
|--------|--------|-----------|
| probability_score | 0.25 | Primary outcome confidence |
| signal_coherence | 0.25 | Internal agreement stability |
| risk_exposure | 0.20 | Capital risk level (amplified if increasing) |
| stress_resilience | 0.15 | Tail risk robustness |
| trend_persistence | 0.10 | Market structure stability |
| logic_consistency | 0.05 | Internal contradiction level |

**Risk exposure amplification**: If `risk_exposure` has increased beyond the baseline value, the raw drift is multiplied by 1.4. This reflects that rising risk is directionally more dangerous than falling risk of the same magnitude.

### Thresholds and Age Handling

| Condition | Action |
|-----------|--------|
| drift_score ≤ threshold AND age ≤ max_age_hours | VALID — pipeline proceeds |
| drift_score > threshold | DRIFT_BLOCK — pipeline blocked |
| age > max_age_hours | Warning issued, effective threshold tightened by up to 30% |
| age > critical_age_hours (720h = 30 days) | CRITICAL_STALE — unconditional block |

Default thresholds (configurable via env):
- `AVM_DRIFT_THRESHOLD`: 35.0
- `AVM_MAX_AGE_HOURS`: 168.0 (7 days)
- `AVM_CRITICAL_AGE_HOURS`: 720.0 (30 days)

### Pass-Through Behavior

AVM is **fail-safe**: exceptions → pass-through (pipeline availability preserved).

When no calibration snapshot exists for a domain, AVM logs a warning and passes through. This ensures backward compatibility — existing domains that have not yet been calibrated with AVM continue to function, but with a persistent warning that drift detection is inactive.

---

## Integration Points

### 1. GovernanceEvaluationEngine (external_evaluator.py)

AVM integrates as the first gate in `evaluate()`:

```python
# Before CAG, before checkpoints:
avm = get_avm_instance()
avm_result = avm.evaluate(signals=resolved_signals, domain=domain)
if not avm_result.is_valid and not avm_result.pass_through:
    return BLOCKED with avm_result details
```

### 2. DecisionReceiptEngine (decision_receipt.py)

Every receipt includes an `avm_result` block:

```json
{
  "receipt_id": "OMNIX-XXXXXXXXXXXX",
  "avm_result": {
    "is_valid": true,
    "snapshot_id": "AVM-XXXXXXXXXX",
    "parameter_version": "1.12345",
    "drift_score": 12.3,
    "age_hours": 24.5
  }
}
```

### 3. Rollback Protocol Integration

When AVM blocks with `DRIFT_BLOCK`, this is a signal that recalibration is needed. Operators should:
1. Investigate the drift source (which signals diverged most)
2. Determine whether a regime change occurred
3. Recalibrate by calling `save_calibration_snapshot()` with updated baseline

---

## Adversarial Test Coverage

The test suite (`tests/test_assumption_validity_monitor.py`) covers:

| Test Class | Scenarios |
|------------|-----------|
| TestAVMDisabled | Gate disabled via env var |
| TestAVMNoSnapshot | No baseline — pass-through + warning |
| TestAVMValidDrift | Signals within tolerance |
| TestAVMDriftBlock | Signals beyond drift threshold → BLOCKED |
| TestAVMCriticalAge | Snapshot older than critical_age_hours → unconditional BLOCKED |
| TestAVMStaleWarning | Snapshot older than max_age_hours → warning + tightened threshold |
| TestAVMRiskAmplification | Increasing risk exposure amplified correctly |
| TestAVMAdversarial | Terra/LUNA pattern, regime shift, gradual drift, boundary manipulation |
| TestAVMParameterVersioning | snapshot_id and parameter_version correctly embedded |
| TestAVMInvalidation | Snapshot invalidation + re-save |
| TestAVMMultiDomain | Independent snapshots per domain |
| TestAVMIntegration | Full pipeline integration via GovernanceEvaluationEngine |

---

## Consequences

### Positive

- **Closes the Knightian uncertainty gap**: OMNIX now detects when its own assumptions have become stale — not just when incoming signals fail checkpoints
- **Parameter provenance in every receipt**: Every governance receipt is now traceable to its exact calibration state
- **Institutional credibility**: Addresses the core critique from Ioana V. and Jennifer — the system now audits itself before auditing decisions
- **VELOS integration safety**: Naimat's concern that VELOS would enforce decisions based on stale OMNIX assumptions is structurally addressed

### Constraints

- **First calibration required per domain**: AVM passes through until a domain's first `save_calibration_snapshot()` call. Operators must calibrate before drift detection is armed.
- **Baseline quality matters**: AVM is only as good as the baseline snapshot. A snapshot taken during an abnormal period will produce false positives. Calibration should occur during stable, representative operating conditions.
- **Drift threshold tuning**: The default threshold (35.0) is conservative. Domain-specific tuning may be required — insurance and credit may tolerate less drift than trading.

---

## Files

| File | Role |
|------|------|
| `omnix_core/governance/assumption_validity_monitor.py` | Core AVM module |
| `tests/test_assumption_validity_monitor.py` | Full adversarial test suite |
| `avm_snapshots/` | Persisted calibration snapshots (one JSON per domain) |
| `omnix_core/governance/external_evaluator.py` | AVM integration (pre-pipeline gate) |
| `omnix_core/evidence/decision_receipt.py` | AVM result embedded in receipts |

---

## Related ADRs

| ADR | Relationship |
|-----|-------------|
| ADR-032 (Temporal Coherence, CP-7) | Detects incoherent decision sequences; AVM detects stale calibration |
| ADR-045 (EBIP) | Detects execution boundary anomalies; AVM detects assumption drift |
| ADR-050 (CAG) | Detects systemic market conditions; AVM detects parameter staleness |
| ADR-053 (TIE) | Detects inadmissible trajectories; AVM detects stale baselines |

AVM is the earliest gate in the pipeline. It answers: **"Are our assumptions about what signals mean still valid?"** All downstream gates assume the answer is yes — AVM verifies this.
