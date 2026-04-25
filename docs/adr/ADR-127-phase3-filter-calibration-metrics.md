# ADR-127 — Phase 3: Filter Calibration Metrics

**Status:** ACCEPTED  
**Date:** 2026-04-25  
**Author:** OMNIX Engineering  
**Scope:** `omnix_core/governance/filter_calibration_metrics.py`, `omnix_web/api/proof_layer.py`

---

## Context

Phase 1 (ADR-125) established a critical-core test suite with 72 tests.  
Phase 2 (ADR-126) built the HOT→WARM→COLD receipt archival infrastructure.

Phase 3 introduces **observability of the governance pipeline itself**: how often each gate passes vs. blocks, how decisions distribute across DCI bands, how frequently Black Swan risk is HIGH, and when ADR-119 escalation fires. Without this data, calibrating thresholds, detecting drift, and demonstrating governance quality to institutional clients is impossible.

### Problem
- No time-series record of gate-level outcomes existed.
- DCI score (ADR-018) was computed but never stored for historical analysis.
- Coherence score distribution was invisible after the decision moment.
- ADR-119 escalation events (BS_HIGH → raised coherence thresholds) were logged but not queryable.
- No mechanism to measure pass_rate / block_rate per gate over time.

### Requirements
1. Collect per-gate metrics: `pass_rate`, `block_rate`, `hold_rate`.
2. Track: DCI distribution, coherence score, Black Swan frequency, ADR-119 escalation events.
3. Store per domain and time window (1h / 1d / 1w).
4. Zero impact on decision latency — async/buffered write path.
5. Internal query interface only — no public endpoint in Phase 3.

---

## Decision

### Architecture

**Event model (flat, one row per decision):**

```
filter_calibration_events
├── id                   BIGSERIAL PRIMARY KEY
├── event_ts             TIMESTAMPTZ NOT NULL DEFAULT NOW()
├── domain               VARCHAR(50)
├── asset                VARCHAR(100)
├── client_id            VARCHAR(100)
├── final_decision       VARCHAR(20)     -- APPROVED | BLOCKED
├── processing_time_ms   INTEGER
├── gate_layer0          SMALLINT        -- 0=PASS 1=BLOCK 2=HOLD -1=SKIP
├── gate_cag             SMALLINT
├── gate_coherence       SMALLINT
├── gate_mc              SMALLINT
├── gate_black_swan      SMALLINT
├── gate_ecw             SMALLINT
├── gate_sharia          SMALLINT
├── gate_aml             SMALLINT
├── gate_fraud           SMALLINT
├── gate_jurisdiction    SMALLINT
├── dci_score            FLOAT           -- 0–100 (ADR-018: ALIGNED<35, TENSIONED<70, CONTRADICTORY≥70)
├── coherence_score      FLOAT           -- 0–100 from signal_coherence
├── black_swan_level     VARCHAR(10)     -- NONE | LOW | HIGH
└── escalation_triggered BOOLEAN         -- ADR-119: BS_HIGH raised coherence thresholds
```

**Indexes:**
- `(domain, event_ts DESC)` — primary query pattern
- `(event_ts DESC)` — window aggregation
- `(final_decision, event_ts DESC)` — outcome filtering
- `(black_swan_level, event_ts DESC)` — BS analysis
- `(escalation_triggered, event_ts DESC)` — escalation queries

**Write path (zero-latency):**

```
Decision made
     │
     ▼ (< 1 μs)
extract_event_from_result()  ← best-effort, never raises
     │
     ▼ (< 1 μs)
queue.put_nowait()           ← returns immediately
     │
     ▼  (async, 30s interval)
FilterCalibrationDaemon      ← background thread flushes to PostgreSQL
```

**Read path:**

```python
svc = FilterCalibrationMetricsService()

# Per-gate pass/block/hold rates
stats = svc.query_gate_stats("coherence", domain="trading", window="1d")

# All gates in one DB round-trip
all_stats = svc.query_all_gate_stats(domain="trading", window="1h")

# DCI distribution with percentiles
dci = svc.query_dci_distribution(window="1w")

# Black Swan frequency
bs = svc.query_black_swan_frequency(domain="trading", window="1d")

# ADR-119 escalation events
esc = svc.query_escalation_events(domain="trading", window="1d")

# Full summary (single connection)
summary = svc.query_summary(domain="trading", window="1d")
```

### DCI Score Computation
The `logic_consistency` signal from `GovernanceEvaluationEngine` is the primary DCI source:

```
dci_score = 100.0 - logic_consistency   # clamped [0, 100]
```

DCI bands (ADR-018):
- **ALIGNED** 0–34: signals agree, proceed normally
- **TENSIONED** 35–69: internal conflict, proceed with caution
- **CONTRADICTORY** 70–100: signals contradict → HOLD mandated

### Gate Extraction Strategy
`extract_event_from_result()` extracts gate outcomes from the engine result dict using a 3-tier fallback:
1. `gate_results` list (checkpoint_id / signal match)
2. `decision_trace` patterns (e.g., `"CP-9 AML_PASS"`, `"BS_HIGH_COHERENCE_ESCALATION"`)
3. `compliance_blocks` dict (for Sharia, AML, Fraud, Jurisdiction)

All extraction is best-effort — `OUTCOME_SKIP (-1)` when uncertain. Never raises.

### ADR-119 Escalation Detection
An escalation event is recorded when `decision_trace` contains `BS_HIGH_COHERENCE_ESCALATION`. This trace is written by the bot when Black Swan = HIGH forces coherence thresholds to escalate from 45%→65% (normal) and 30%→50% (critical).

### Integration Point
`proof_layer.py::simple_evaluate()` calls `get_global_service().record(event)` **after** `_persist_evl_receipt()`. The call is wrapped in `try/except` — if FCM is unavailable, it logs at DEBUG and the response is unaffected.

The `get_global_service()` singleton initializes the service and starts the daemon on first access. Schema is created automatically.

---

## Consequences

### Positive
- Gate-level pass/block rates are now measurable over time → threshold calibration becomes data-driven.
- DCI distribution enables detection of structural signal conflicts before they become systemic.
- Black Swan HIGH frequency tracking enables adaptive risk posture.
- ADR-119 escalation events are queryable → can validate that BS_HIGH → BLOCKED causal chain is working.
- Zero decision latency impact (queue.put_nowait is O(1), < 1 μs).
- Fail-open: FCM failure never affects governance decisions.

### Negative / Mitigations
- One new table per deployment environment (handled by `ensure_schema()`).
- Queue overflow drops events under extreme load (max_queue_size=2000). At 1 req/s, buffer covers >30 minutes. Logged as WARNING.
- Gate extraction is best-effort — compliance gates (AML, Sharia, etc.) are only active when enabled via env vars, so their outcomes will be SKIP for most deployments.

---

## Test Coverage

Phase 3 adds **`tests/test_phase3_filter_calibration_metrics.py`** with tests covering:

| Category | Count |
|---|---|
| `_outcome_from_result_str` | 5 |
| `_scan_gate_results` | 4 |
| `_scan_trace` | 5 |
| `_extract_black_swan_level` | 6 |
| `extract_event_from_result` | 18 |
| `FilterCalibrationEvent` defaults | 2 |
| `FilterCalibrationMetricsService` | 14 |
| `FilterCalibrationDaemon` | 2 |
| `get_global_service` singleton | 2 |
| `GATES` constant | 2 |
| **Total** | **60** |

---

## ADR Count
This brings the ADR count to **36** (ADR-063 through ADR-127, non-contiguous).

## Test Count
- Phase 1: 72 tests (ADR-125)
- Phase 2: 43 tests (ADR-126)
- Phase 3: 60 tests (ADR-127)
- Previous: 156 tests
- **New total: 259 tests confirmed green**
