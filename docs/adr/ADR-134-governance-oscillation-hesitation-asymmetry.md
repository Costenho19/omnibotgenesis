# ADR-134 — Governance Oscillation & Hesitation Asymmetry Engine

**Status:** Active  
**Date:** 2026-04-28  
**Author:** Harold Alberto Nunes Rodelo, OMNIX QUANTUM LTD  
**Builds on:** ADR-127 (FCM), ADR-128 (Calibration Insight), ADR-129 (Anomaly Response)

---

## 1. Context

ADR-128 (CalibrationInsightEngine) detects **snapshot anomalies** — single-window
deviations from a defined baseline within a short time horizon (1h/1d/1w).

It does not detect **temporal patterns** — whether the governance frame is cycling,
whether regime-change boundaries exist in the longitudinal record, whether
processing latency reveals deferral shortcuts under evaluative load, or whether
oscillation amplitude is decreasing as a pre-capture signal.

The gap was identified through extended exchange with Dr.(H.C.) Amanulla Khan
(Founder, Skilligen™ HDI, Dubai, 2026-04-28):

> *"Oscillation itself becomes a transition signature: the system still detects
> mismatch strongly enough to resist full normalization, but no longer possesses
> a stable evaluative frame capable of resolving the tension coherently."*

> *"Whether prolonged deferral preference under oscillatory conditions gradually
> conditions the system toward normalization capture by reducing repeated exposure
> to unresolved evaluative tension over time."*

> *"Instability may first redistribute itself into latency, hesitation, or
> compensatory buffering dynamics before manifesting as overt failure."*

This ADR creates the module that converts those theoretical observations into
directly measurable signals from the permanent decision record.

---

## 2. Decision

Create `omnix_core/governance/oscillation_insight.py` — a read-only analysis
engine providing four complementary longitudinal detection methods:

1. **Oscillation Profile** — HOLD rate standard deviation across rolling weekly windows
2. **Phase-Segmented Analysis** — Regime-change boundary detection
3. **Hesitation Asymmetry** — Processing latency by decision type
4. **Dampening Curve** — Oscillation amplitude trend over time

Expose via `GET /api/analytics/oscillation` with `view` parameter.

---

## 3. Four Analysis Methods

### 3.1 Oscillation Profile (`oscillation_profile`)

Queries `filter_calibration_events` for HOLD/BLOCK/APPROVED counts across N
rolling 7-day windows (default: 8 weeks).

Computes standard deviation, amplitude (max − min hold_rate), and classifies
the oscillation pattern:

| Pattern | Condition | Interpretation |
|---|---|---|
| `CYCLING` | std-dev ≥ 8pp | Evaluative frame cycling without resolution. Residual recognition capacity present. |
| `DRIFTING` | std-dev < 8pp, monotonic increase | Slow accumulation toward deferral equilibrium. |
| `SETTLING` | std-dev < 8pp, monotonic decrease | Resolving — toward enforcement (healthy) or captured equilibrium. Cross-reference dampening curve. |
| `STABLE` | std-dev < 8pp, no trend | No significant oscillation or directional signal. |
| `INSUFFICIENT_DATA` | < 4 valid windows | Too few data points for reliable classification. |

**Design principle:** A captured system wouldn't cycle — it would settle. Continued
alternation means the evaluative frame still detects tension. That tension is doing
work, even if it cannot resolve.

### 3.2 Phase-Segmented Analysis (`phase_segmented_analysis`)

Detects weeks where HOLD rate shifts > 20pp week-over-week. These are treated
as **phase boundaries** — structural regime-change events, not noise.

**Why this matters:** Continuity-based regression averaging pre-boundary and
post-boundary observations in the same model dampens the transition signal at
exactly the moment the signal matters most. The March 16 trading week (HOLD
rate collapse from 92% → 53% in one period) is the canonical example.

Each segment receives:
- Independent average HOLD and BLOCK rates
- OLS slope (pp per week within segment)
- Phase label: `PRE_BOUNDARY` | `POST_BOUNDARY_N` | `BASELINE`

A `continuity_warning=True` flag is set when ≥1 boundary is detected, indicating
that continuity-based analysis is structurally invalid across the full period.

### 3.3 Hesitation Asymmetry (`hesitation_asymmetry`)

Compares `avg/p50/p90 processing_time_ms` by decision type (APPROVED / BLOCKED /
HOLD) within the configured window.

**Asymmetry coefficient** = `avg_HOLD_ms / avg_BLOCK_ms`

| Coefficient | Interpretation |
|---|---|
| < 0.85 | **Asymmetry present.** HOLD decisions resolve significantly faster than BLOCK. The evaluative frame is defaulting to deferral under load — routing tension into postponement rather than resolution. |
| 0.85 – 1.0 | Marginal. Below detection threshold. |
| ≥ 1.0 | No asymmetry. HOLD processes at or slower than BLOCK — effort proportional to decision type. |

**Signal significance:** If deferral states begin resolving faster than enforcement
states during oscillation periods, the system may be preferentially conserving
evaluative load by routing tension into postponement rather than resolution
(Amanulla, 2026-04-28).

### 3.4 Dampening Curve (`dampening_curve`)

Splits the observed period (N weeks) into two equal halves. Compares oscillation
amplitude (max − min hold_rate) between the older half and the recent half.

**Amplitude delta** = `second_half_amplitude − first_half_amplitude`

| Direction | Condition | Interpretation |
|---|---|---|
| `DAMPENING` | delta < −4pp | Oscillation amplitude falling. Residual recognition capacity attenuating. **Pre-capture signal:** the transition from resistance to absorption may be underway. |
| `AMPLIFYING` | delta > +4pp | Oscillation amplitude rising. Evaluative conflict intensifying — escalation may follow before capture or enforcement stabilisation. |
| `STABLE` | \|delta\| ≤ 4pp | No directional trend. Evaluative conflict holding steady. |

**Theoretical basis:** If oscillation persists as long as the system detects
mismatch, but each deferral cycle reduces detection sensitivity, oscillation
amplitude should decrease before the system settles into captured equilibrium.
That dampening curve — if measurable — is the advance indicator of the transition
from resistance to absorption.

---

## 4. Executive Summary

`oscillation_report()` combines all four methods and produces an `executive_summary`
with a risk level (`LOW / MEDIUM / HIGH / CRITICAL`) and a prioritised signal list.

**CRITICAL** is triggered when dampening + hesitation asymmetry are simultaneously
present — the combination indicates pre-capture across multiple dimensions.

Recommendation at `CRITICAL`:
> "Immediate governance review required. Pre-capture signals present across multiple
> dimensions. External legitimacy anchoring recommended. Engage HDI layer for
> independent evaluative validation."

---

## 5. API Endpoint

```
GET /api/analytics/oscillation
```

**Query parameters:**

| Parameter | Type | Default | Values |
|---|---|---|---|
| `domain` | string | all | trading, credit, insurance, … |
| `num_weeks` | int | 8 | 1–26 |
| `view` | string | full | full \| profile \| phases \| asymmetry \| dampening |

**Authentication:** Public — aggregated metrics only, no PII.

**Headers returned:**
- `X-OMNIX-ADR: ADR-134`
- `Cache-Control: no-cache, no-store, must-revalidate`

---

## 6. Data Source

All queries read from `filter_calibration_events` (ADR-127):

| Column | Used by |
|---|---|
| `final_decision` | All methods |
| `event_ts` | All methods (window filtering) |
| `processing_time_ms` | Hesitation asymmetry |
| `domain` | All methods (optional filter) |

**Zero write path.** This module never modifies the DB.

---

## 7. Thresholds

| Threshold | Value | Rationale |
|---|---|---|
| `OSCILLATION_STD_THRESHOLD` | 8pp | From trading data: 14pp std-dev observed. 8pp is conservative lower bound. |
| `PHASE_BOUNDARY_THRESHOLD` | 20pp | Observed 39pp shift (92%→53%) in March trading week. 20pp catches meaningful transitions. |
| `LATENCY_ASYMMETRY_THRESHOLD` | 0.85 | 15% faster HOLD vs BLOCK = significant deferral shortcut. |
| `DAMPENING_AMPLITUDE_DELTA` | 4pp | Minimum detectable amplitude change within noise. |
| `MIN_WINDOWS_FOR_OSCILLATION` | 4 | Below 4 windows, pattern classification is unreliable. |
| `MIN_DECISIONS_PER_WINDOW` | 10 | Sparse windows excluded from statistics. |

---

## 8. Architectural Position

```
filter_calibration_events (ADR-127)
         ↓
CalibrationInsightEngine (ADR-128) — snapshot anomalies, 1h/1d/1w
         ↓
OscillationInsightEngine (ADR-134) — temporal patterns, 4–26 weeks
         ↓
AnomalyResponseEngine    (ADR-129) — governance recommendations
         ↓
External legitimacy validation (HDI — Amanulla framework)
```

---

## 9. Relationship to ADR-130 (VC Revocation)

When `oscillation_report()` returns `risk_level=CRITICAL`, the recommended
response includes external legitimacy anchoring. In OMNIX's trust architecture,
this is implemented by:

1. Flagging affected domain calibration snapshots for external review
2. Triggering `fire_avm_domain_suspension()` (ADR-130 v2) for VCs issued
   during the degraded period
3. Engaging the oversight session layer (ADR-124) for human attestation
   before any recalibration

---

## 10. Fail-Safe Guarantees

- All four methods return `{"available": False}` on DB unavailability
- No exceptions propagate to the caller
- No shared mutable state — thread-safe
- Zero impact on the live governance evaluation pipeline

---

## 11. Test Coverage

`tests/test_oscillation_insight.py` — target: 35 tests

| Group | Tests | Coverage |
|---|---|---|
| T01–T05 | Import, instantiation, helpers | Module structure |
| T06–T10 | `oscillation_profile` patterns | CYCLING/DRIFTING/SETTLING/STABLE/INSUFFICIENT_DATA |
| T11–T15 | `phase_segmented_analysis` | Boundary detection, segment building, continuity warning |
| T16–T20 | `hesitation_asymmetry` | Coefficient calculation, threshold detection, interpretation |
| T21–T25 | `dampening_curve` | DAMPENING/AMPLIFYING/STABLE/INSUFFICIENT_DATA |
| T26–T30 | `oscillation_report` full | Executive summary, risk levels |
| T31–T35 | Edge cases | Empty data, DB error fail-safe, sparse windows |

---

## 12. Changelog

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-04-28 | Initial implementation — 4 methods, API endpoint, ADR-134 |
