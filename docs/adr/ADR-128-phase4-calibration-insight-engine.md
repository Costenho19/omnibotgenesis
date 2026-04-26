# ADR-128 — Phase 4: Calibration Insight Engine

**Status:** ACCEPTED  
**Date:** 2026-04-25  
**Author:** OMNIX Engineering  
**Scope:** `omnix_core/governance/calibration_insight.py`, `tests/test_phase4_calibration_insight.py`

---

## Context

Phase 3 (ADR-127) established `FilterCalibrationMetricsService` — a zero-latency event collector that stores per-gate outcomes, DCI scores, coherence scores, Black Swan levels, and ADR-119 escalation flags into `filter_calibration_events`.

Phase 3 answered **"can we collect?"**  
Phase 4 answers **"can we reason over what we collected?"**

Without an analysis layer, the stored metrics are inert. Institutional clients, auditors, and internal governance operators need:
- Time-series trend visibility across windows (1h → 1d → 1w)
- Anomaly detection with actionable severity classification
- Cross-domain comparison for governance posture benchmarking
- Coherence score distribution (internal signal agreement bands)

### Problem
- Raw query results from ADR-127 require manual comparison across windows to detect drift.
- No automated mechanism existed to flag a sudden block rate drop (filter weakening signal).
- HOLD spikes (decision paralysis) were invisible without per-window aggregation.
- Per-domain comparison required multiple separate query calls with no unified interface.

### Requirements
1. Internal analysis only — no new public endpoints, no UI changes, no core impact.
2. Build on top of `FilterCalibrationMetricsService` (dependency injection pattern).
3. Detect 6 anomaly types: BLOCK_RATE_DROP, HOLD_SPIKE, DCI_SURGE, COHERENCE_DRIFT, BS_HIGH_SURGE, ESCALATION_SURGE.
4. Classify anomaly severity: CRITICAL, HIGH, MEDIUM (with co-occurrence upgrade).
5. Graceful degradation when DB is unavailable (`available: False` in output).
6. 100% mockable — no real DB required for tests.
7. Thread-safe: read-only engine with no shared mutable state.

---

## Decision

Introduce `CalibrationInsightEngine` in `omnix_core/governance/calibration_insight.py`.

The engine:
- Accepts a `FilterCalibrationMetricsService` via constructor injection (or auto-constructs one from `OMNIX_DB_URL`).
- Exposes 6 public methods: `snapshot()`, `dci_trend()`, `coherence_distribution()`, `bs_trend()`, `detect_anomalies()`, `domain_comparison()`, and `full_report()`.
- Adds one internal SQL query (`_query_coherence_distribution`) that `FilterCalibrationMetricsService` does not provide.
- Never modifies any database table — purely read-only.

### Anomaly Detection Design

Anomalies are detected by comparing **1h (current)** against **1d (baseline)**:

| Anomaly Type | Signal | Threshold | Rationale |
|---|---|---|---|
| `BLOCK_RATE_DROP` | Coherence gate block_rate | ≥ 15pp drop | Coherence is the most sensitive filter; sudden drop may indicate weakening |
| `HOLD_SPIKE` | Avg hold_rate across all gates | ≥ 10pp rise | Decision paralysis or manual-review queue saturation |
| `DCI_SURGE` | Avg DCI score | ≥ 10pts rise | Increasing contradiction in governance signals |
| `COHERENCE_DRIFT` | Avg coherence_score (abs) | ≥ 10pts | Bidirectional — both drop and spike are anomalous |
| `BS_HIGH_SURGE` | BS_HIGH event rate | ≥ 5pp rise | Systemic risk elevation in current hour |
| `ESCALATION_SURGE` | ADR-119 escalation_rate | ≥ 5pp rise | Concentrated BS_HIGH_COHERENCE_ESCALATION events |

### Severity Classification

```
deviation >= threshold × 2.5  →  CRITICAL
deviation >= threshold × 2.0  →  HIGH
deviation >= threshold        →  MEDIUM
```

**Co-occurrence upgrade:** When 3+ anomalies fire simultaneously, MEDIUM and HIGH severities are bumped one level upward, reflecting systemic stress.

### Coherence Distribution Bands

| Band | Range | Meaning |
|---|---|---|
| HIGH | coherence_score ≥ 70 | Strong signal agreement |
| MEDIUM | 40 ≤ coherence_score < 70 | Moderate agreement |
| LOW | coherence_score < 40 | Fragmented/weak signals |

### DCI Trend Direction

| Delta 1h vs 1d | Threshold | Label |
|---|---|---|
| +5pts or more | 5.0 | RISING |
| -5pts or less | 5.0 | FALLING |
| within ±5pts | — | STABLE |
| data absent | — | UNKNOWN |

---

## Module Structure

```
omnix_core/governance/calibration_insight.py
│
├── CalibrationAnomaly              — dataclass, one anomaly instance
├── CalibrationInsightEngine        — main analysis class
│   ├── snapshot()                  — gate outcome distribution + decision summary
│   ├── dci_trend()                 — DCI across 1h/1d/1w with directional delta
│   ├── coherence_distribution()    — coherence score bands (HIGH/MEDIUM/LOW)
│   ├── bs_trend()                  — BS_HIGH frequency trend across windows
│   ├── detect_anomalies()          — 6-signal anomaly detection with severity
│   ├── domain_comparison()         — side-by-side multi-domain metrics
│   ├── full_report()               — all of the above in one structured call
│   ├── _query_coherence_distribution()   — internal SQL (not in base service)
│   └── _query_decision_summary()         — internal SQL for final_decision counts
│
├── get_insight_engine()            — convenience factory
└── helpers: _avg_hold_rate, _avg_pass_rate, _avg_block_rate,
             _classify_trend, _upgrade_severity, _build_summary,
             _overall_severity
```

---

## Consequences

### Positive
- Governance operators can now detect filter drift in near-real-time (1h window).
- `detect_anomalies()` provides a single-call health check suitable for monitoring agents.
- Zero core impact: no changes to the decision path, no new tables, no new endpoints.
- Fully testable without a database (mock service pattern, 65 tests, all green).
- `domain_comparison()` enables cross-vertical governance posture benchmarking.

### Negative / Accepted Trade-offs
- `_query_coherence_distribution` duplicates the DB access pattern of the base service rather than extending it — accepted to preserve ADR-127's zero-change constraint.
- Anomaly detection uses fixed thresholds (not adaptive). Adaptive thresholds are a Phase 5+ concern.
- 1h window requires sufficient event volume for reliable rate calculations. Low-traffic domains may produce noisy anomaly signals.

### Neutral
- `full_report()` makes 8+ DB queries (one per method, one per window). For high-frequency polling, callers should use individual methods with shared connections.

---

## Test Coverage

| Test Class | Count | Coverage |
|---|---|---|
| `TestCalibrationAnomaly` | 2 | CalibrationAnomaly.to_dict() |
| `TestThresholdConstants` | 6 | All 6 threshold values |
| `TestHelpers` | 13 | All pure helper functions |
| `TestEngineConstruction` | 3 | Init patterns |
| `TestSnapshot` | 6 | snapshot() including error path |
| `TestDciTrend` | 6 | RISING/FALLING/STABLE + error |
| `TestCoherenceDistribution` | 2 | bands + error fallback |
| `TestBsTrend` | 4 | RISING + error + windows |
| `TestDetectAnomalies` | 11 | All 6 anomaly types + structure + error |
| `TestDomainComparison` | 5 | Multi-domain + error + window |
| `TestFullReport` | 4 | Keys + domain/window forwarding |
| **Total** | **65** | **65/65 PASSED** |

---

## References

- ADR-018: Decision Contradiction Index (DCI) bands (ALIGNED / TENSIONED / CONTRADICTORY)
- ADR-119: Governance Hardening — BS_HIGH coherence escalation
- ADR-125: Phase 1 Critical Core Tests
- ADR-126: Phase 2 Receipt Archival HOT/WARM/COLD
- ADR-127: Phase 3 Filter Calibration Metrics (base module for Phase 4)
