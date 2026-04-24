# ADR-117: Meta-Coherence Monitor — Second-Order Governance Perception Stability

**Status:** ACCEPTED — v1.1 Extended 24 April 2026 (DEFERRAL_TRAJECTORY signal added)  
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

### 3.2 Four Detection Mechanisms (v1.1)

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

#### DEFERRAL_TRAJECTORY (MCM v1.1)

Time-series analysis of the HOLD (deferral) rate across rolling weekly windows.
Computes velocity (Δhold_rate/period), acceleration (Δvelocity/period), and
volatility (standard deviation) to detect degradation trajectories **before**
cross-window drift detection (VERDICT_DISTRIBUTION_DRIFT) fires.

Inspired by Amanulla Khan (24 Apr 2026):

> *"Instability may first redistribute itself into latency, hesitation, or
> compensatory buffering dynamics before manifesting as overt failure.
> Longitudinal changes in absorption patterns may reveal degradation
> trajectories earlier than direct outcome analysis alone."*

**Computed metrics per domain:**

| Metric | Formula | Unit |
|---|---|---|
| `hold_rate` | HOLD / total × 100 | % per period |
| `velocity` | Δhold_rate / period | pp/week |
| `acceleration` | Δvelocity / period | pp/week² |
| `hold_rate_std` | σ(hold_rates) | pp |
| `sustained_increasing_periods` | max consecutive positive-velocity periods | N |

**Thresholds:**

| Threshold | Value | Meaning |
|---|---|---|
| `DEFERRAL_VELOCITY_WARNING` | 1.5 pp/week | Sustained growth requiring monitoring |
| `DEFERRAL_VELOCITY_CRITICAL` | 4.0 pp/week | Rapid deferral accumulation |
| `DEFERRAL_ACCELERATION_WARNING` | 0.5 pp/week² | Velocity itself increasing |
| `DEFERRAL_VOLATILITY_HIGH` | 12.0 pp σ | Oscillation signature (unstable regime) |
| `DEFERRAL_SUSTAINED_WARNING` | 3 periods | Early trend forming |
| `DEFERRAL_SUSTAINED_CRITICAL` | 5 periods | Structural deferral trajectory |

**First detection result — trading domain (24 Apr 2026):**

```
DEFERRAL_TRAJECTORY | CRITICAL | Score 74.3/100
periods=7 (weekly, 56-day lookback)
mean_hold = 89.1%
velocity  = +4.85 pp/week  [CRITICAL — above 4.0 threshold]
accel     = +0.83 pp/week² [WARNING — above 0.5 threshold]
std       = 12.0 pp        [WARNING — at volatility boundary]

[CRITICAL] DEFERRAL_VELOCITY_HIGH
  HOLD rate growing at +4.85 pp/week — predates output distribution change

[WARNING]  DEFERRAL_ACCELERATION
  Velocity itself accelerating at +0.83 pp/week² — progressive frame shift

[WARNING]  DEFERRAL_OSCILLATION
  std=12.0 pp — high inter-period oscillation, not a stable deferral state
```

### 3.3 Transition Signatures (Pre-Divergence Early Warning)

Unlike the AVM which fires on threshold breach, the MCM surfaces signatures
**before** divergence becomes explicit:

| Signal ID | Source | Severity | Description |
|---|---|---|---|
| `BLOCK_RATE_COLLAPSE` | VDD | CRITICAL | BLOCK rate < 25% of reference (>4x drop) |
| `BLOCK_RATE_DECLINE` | VDD | WARNING | BLOCK rate < 50% of reference |
| `HOLD_ABSORPTION` | VDD | WARNING | HOLD rising while BLOCK falling (deferral pattern) |
| `GATE_SILENCE:<gate>` | VPA | WARNING | Gate frequency < 15% of reference rate |
| `GATE_AMPLIFICATION:<gate>` | VPA | INFO | Gate frequency > 2× reference rate |
| `REFERENCE_AGE_WARNING` | RL | WARNING | Calibration > 75% through validity window |
| `REFERENCE_AGE_EXCEEDED` | RL | CRITICAL | Calibration past validity window |
| `RECALIBRATION_ANCHORING_RISK` | RL | CRITICAL | Last recal during BLOCK rate < 3% |
| `DEFERRAL_VELOCITY_HIGH` | DT | CRITICAL | HOLD rate growing > 4.0 pp/week (v1.1) |
| `DEFERRAL_VELOCITY_RISING` | DT | WARNING | HOLD rate growing > 1.5 pp/week (v1.1) |
| `DEFERRAL_ACCELERATION` | DT | WARNING | Velocity itself increasing > 0.5 pp/week² (v1.1) |
| `SUSTAINED_DEFERRAL_TREND` | DT | WARNING/CRITICAL | N consecutive periods of rising HOLD (v1.1) |
| `DEFERRAL_OSCILLATION` | DT | WARNING | Std dev > 12 pp — unstable oscillation regime (v1.1) |

*Sources: VDD=Verdict Distribution Drift, VPA=Veto Pattern Asymmetry, RL=Reference Legitimacy, DT=Deferral Trajectory*

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

## 8. Implementation Status

| Feature | Status |
|---|---|
| VERDICT_DISTRIBUTION_DRIFT (3 signals) | ✅ v1.0 — live |
| VETO_PATTERN_ASYMMETRY | ✅ v1.0 — live |
| REFERENCE_LEGITIMACY | ✅ v1.0 — live |
| DEFERRAL_TRAJECTORY (4 signals) | ✅ v1.1 — live |
| REST endpoints (`/api/governance/meta-coherence[/<domain>]`) | ✅ v1.1 — live |
| Tests (`tests/test_meta_coherence_monitor.py`) | ✅ 45 passing |
| DB persistence (`governance_drift_log`) | ✅ 4 rows per trading run |

## 9. Next Steps (ADR-118)

1. **Proxy mode gate disambiguation:** Filter `_PROXY_MODE` gate entries from asymmetry
   analysis or classify them separately in the veto_chain format
2. **Auto-remediation (ADR-118):** When MCM alert_level = CRITICAL, automatically
   suspend recalibration and escalate to operator — requires governance authority decision
3. **Scheduled sweep:** Run `monitor.run_all_domains()` on a cron schedule (daily)
   and persist comparative cross-domain reports for trend tracking
4. **Deferral window calibration:** Optimize `_TRAJECTORY_GRANULARITY_DAYS` per domain
   (trading may require 3-day windows; insurance may work on 14-day windows)

---

*"The system no longer asks only whether outputs are valid. It now asks whether the
frame evaluating validity is itself valid. That is the institutional governance standard."*

— Harold Nunes, OMNIX QUANTUM LTD, 24 April 2026
