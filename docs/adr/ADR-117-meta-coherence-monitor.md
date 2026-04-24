# ADR-117: Meta-Coherence Monitor — Second-Order Governance Perception Stability

**Status:** ACCEPTED — Implemented 24 April 2026  
**Authors:** Harold Nunes, OMNIX QUANTUM LTD  
**Supersedes:** N/A  
**Related:** ADR-064 (AVM), ADR-075 (Non-Finite Signal Guard), ADR-116 (Fail-Closed Enforcement)

---

## 1. Context

The Assumption Validity Monitor (ADR-064) addresses first-order drift: it detects when
live conditions have diverged from the frozen calibration baseline. This is a necessary
but insufficient condition for governance integrity.

A deeper failure mode was identified through dialogue with Amanulla Khan (Honorary Doctorate)
on 24 April 2026:

> *"The critical problem is not only detecting divergence, but detecting when the interpretive
> logic evaluating divergence has itself begun adapting to the degraded state. That feels like
> the point where governance perception itself becomes structurally unstable."*

This failure mode — **compensatory normalization** — manifests when a governance system's
evaluation frame silently drifts toward accepting conditions it would previously have blocked.
The outputs appear stable because the measurement criteria moved with the environment.

**Observable evidence in OMNIX trading domain (24 Apr 2026):**

| Metric | Reference (30d ago) | Current (14d) | Drift |
|---|---|---|---|
| BLOCK rate | 13.7% | 0.4% | −13.3pp (−97%) |
| HOLD rate | 86.3% | 93.9% | +7.6pp |
| APPROVE rate | 0.0% | 5.7% | +5.7pp |

The AVM calibration snapshot (AVM-EEEDB2BF18) was recalibrated during a period when the
BLOCK rate was 0.46% — meaning the "frozen reference" itself encodes a potentially
degraded state. This is the **reference anchoring risk** Amanullah identifies as the
deepest form of reference obsolescence.

---

## 2. Decision

Implement the **Meta-Coherence Monitor (MCM)** as a second-order, independent governance
perception auditor that operates on the historical record — never on live pipeline state.

The MCM answers one question the AVM cannot ask from within:

> **Has the governance evaluation frame begun adapting to degraded conditions,
> independent of whether individual outputs pass first-order drift detection?**

---

## 3. Architecture

### 3.1 Independence Principle

The MCM MUST NOT share state with the pipeline it monitors. It reads exclusively from:
- `decision_receipts` — historical verdict record
- `avm_calibration_snapshots` — calibration baseline reference
- `avm_baseline_change_log` — recalibration history

It writes exclusively to:
- `governance_drift_log` — MCM findings, independently queryable

This isolation means the MCM's own evaluation frame cannot be contaminated by the
pipeline state it is auditing. It is the "external reference point not trained on
the same environment" that longitudinal observation requires.

### 3.2 Three Detection Mechanisms

#### VERDICT_DISTRIBUTION_DRIFT

Compares the BLOCKED / HELD / APPROVED ratio between two time windows:
- **Reference window:** N days ago (represents "normal operating conditions")
- **Current window:** Recent M days (represents current evaluation behavior)

Drift score formula (weighted, 0–100):

```
drift = |Δblocked| × 0.55 + |Δheld| × 0.25 + |Δapproved| × 0.20
```

BLOCKED is weighted highest (0.55) because BLOCK_RATE_COLLAPSE is the primary
compensatory normalization signature.

#### VETO_PATTERN_ASYMMETRY

Analyzes which governance gates appear in decision `veto_chain` records across both
windows. A gate that drops below 15% of its reference firing frequency without a
corresponding policy change is exhibiting silent normalization (GATE_SILENCE).

Detects:
- **Gate silence:** evaluator bypassing or no longer invoking a gate
- **Gate amplification:** one gate absorbing decisions that previously distributed
  across multiple gates (compensatory concentration)

#### REFERENCE_LEGITIMACY

Validates the AVM calibration baseline against two criteria:

1. **Calibration age:** Is the snapshot approaching its `max_age_hours` validity window?
   Warning threshold: 75% of max age. Critical: 100%.

2. **Anchoring risk:** Was the last recalibration performed during a period of anomalously
   low BLOCK rate (< 3%)? If so, the frozen reference may encode a degraded state,
   making it an unreliable validity anchor — the reference obsolescence problem.

### 3.3 Transition Signatures (Pre-Divergence Early Warning)

Unlike the AVM which fires on threshold breach, the MCM surfaces signatures
**before** divergence becomes explicit:

| Signal ID | Severity | Description |
|---|---|---|
| `BLOCK_RATE_COLLAPSE` | CRITICAL | BLOCK rate < 25% of reference (>4x drop) |
| `BLOCK_RATE_DECLINE` | WARNING | BLOCK rate < 50% of reference |
| `HOLD_ABSORPTION` | WARNING | HOLD rising while BLOCK falling (deferral pattern) |
| `GATE_SILENCE:<gate>` | WARNING | Gate frequency < 15% of reference rate |
| `GATE_AMPLIFICATION:<gate>` | INFO | Gate frequency > 2× reference rate |
| `REFERENCE_AGE_WARNING` | WARNING | Calibration > 75% through validity window |
| `REFERENCE_AGE_EXCEEDED` | CRITICAL | Calibration past validity window |
| `RECALIBRATION_ANCHORING_RISK` | CRITICAL | Last recal during BLOCK rate < 3% |

### 3.4 Alert Levels

| Score Range | Alert Level | Interpretation |
|---|---|---|
| 0–19 | OK | Evaluation frame stable, no normalization signatures |
| 20–44 | WARNING | Significant shift requiring monitoring |
| 45–100 | CRITICAL | Evaluator likely adapting to degraded conditions |

---

## 4. Implementation

**Module:** `omnix_core/governance/meta_coherence_monitor.py`  
**Key classes:** `MetaCoherenceMonitor`, `MetaCoherenceReport`  
**DB tables read:** `decision_receipts`, `avm_calibration_snapshots`  
**DB tables written:** `governance_drift_log`

**Usage:**
```python
from omnix_core.governance.meta_coherence_monitor import get_meta_coherence_monitor

monitor = get_meta_coherence_monitor()
report  = monitor.run_full_analysis("trading", reference_days=30, current_days=14)
monitor.persist_to_db(report)

print(report.alert_level)            # "CRITICAL"
print(report.evaluation_frame_stable) # False
print(report.executive_summary)
```

---

## 5. Fail-Closed Policy

If the MCM encounters a DB error or internal exception:
- Logs at WARNING level
- Returns `evaluation_frame_stable=None` (unknown, not True)
- Never returns `evaluation_frame_stable=True` under uncertainty
- Never raises exceptions to the caller

---

## 6. Consequences

### Positive

- **Closes the meta-governance gap:** OMNIX now detects both first-order (output) drift
  and second-order (evaluation frame) drift
- **Independent audit trail:** MCM findings persist to `governance_drift_log` independently
  of the pipeline, creating an externally verifiable record
- **Investor-grade transparency:** The MCM executive summary is designed for direct
  inclusion in governance reports, audit packages, and partner communications
- **Answers Amanullah's critique directly:** The system now distinguishes between
  "stable systems" and "stabilized degradation"

### Negative / Risks

- **MCM itself is subject to anchoring risk:** If the reference window is too short,
  the MCM's own baseline may encode a degraded period. Mitigation: use ≥ 30-day
  reference windows for trading domains.
- **Proxy mode gates inflate asymmetry scores:** When governance gates run in fallback
  mode (e.g., `AML_FREQUENCY_PROXY_MODE`), they appear in veto_chains at near-100%
  frequency, inflating asymmetry scores. Future work: distinguish proxy-mode entries
  from substantive gate decisions.

---

## 7. Live Detection — 24 April 2026

First MCM run on OMNIX trading domain identified:

```
MCM-5610F2DB56 | CRITICAL | Score 79.5/100
evaluation_frame_stable: False

[CRITICAL] BLOCK_RATE_COLLAPSE
  BLOCK rate: 13.7% → 0.4% (3% of reference)
  Evaluator normalizing conditions that previously triggered blocks

[CRITICAL] RECALIBRATION_ANCHORING_RISK
  Last recalibration BLOCK rate: 0.46% (below 3% threshold)
  Frozen reference may encode a degraded state

[WARNING] HOLD_ABSORPTION
  HOLD +7.7pp while BLOCK −13.3pp
  Decisions deferred rather than resolved
```

This is the first real-world confirmation of the compensatory normalization pattern
in OMNIX operational data.

---

## 8. Next Steps

1. **Proxy mode gate disambiguation:** Filter `_PROXY_MODE` gate entries from asymmetry
   analysis or classify them separately in the veto_chain format
2. **Recalibration trigger:** When MCM alert_level = CRITICAL, automatically open a
   recalibration review ticket
3. **MCM dashboard widget:** Expose MCM scores in the Flask Dashboard governance panel
4. **Multi-domain sweep:** Run `monitor.run_all_domains()` on a schedule and persist
   comparative reports

---

*"The system no longer asks only whether outputs are valid. It now asks whether the
frame evaluating validity is itself valid. That is the institutional governance standard."*

— Harold Nunes, OMNIX QUANTUM LTD, 24 April 2026
