# ADR-033: Signal Integrity Validator (SIV) — Checkpoint 0

**Status**: ACCEPTED  
**Date**: March 2026  
**Author**: Harold Nunes  
**Category**: Architecture — Data Integrity  
**Follows**: ADR-032 (TCV — Checkpoint 7)

---

## Context

OMNIX operates a 7-checkpoint governance pipeline that validates whether a proposed
trading decision is statistically justified. Every checkpoint — Monte Carlo VETO,
Coherence Gate, TCV, ECW — operates on the same foundational assumption: that the
market data feeding the pipeline is accurate, fresh, and complete.

This assumption was never validated explicitly.

**The identified gap**: If Kraken returns a stale or corrupted price, if OHLC data
is missing, if a secondary data source shows a dramatically different price — the
entire 7-checkpoint pipeline processes bad data with institutional rigor, producing
outputs that are precisely wrong.

A concrete example of the failure mode:
- Kraken API timeout → last known price cached from 8 minutes ago
- BTC has moved 3% since the cached price
- Monte Carlo runs 10,000 simulations on the stale price
- 7 checkpoints pass on data that doesn't reflect current market reality
- A trade executes at a price that no longer exists

**Why the existing MarketDataValidator is insufficient:**
The existing `validate_price_freshness` (added Dec 2025, `omnix_services/market_data/validators.py`)
checks only whether the price fetch is recent — a single timestamp comparison, applied at
execution time (in `_execute_smart_trade`), after all analysis has already run.

SIV addresses four categories of data integrity failure, applied at the START of the
pipeline, before any analysis runs.

---

## Distinction from Existing Price Freshness Check

| Aspect | Existing `validate_price_freshness` | SIV (ADR-033) |
|--------|-------------------------------------|---------------|
| Position in pipeline | At execution (`_execute_smart_trade`) | At start (`_make_v52_decision`) |
| Scope | Single source, price only | All data sources, 4 categories |
| Validation depth | Timestamp comparison | Freshness + completeness + anomaly + cross-source |
| Output | Block/allow execution | Scored result with violation breakdown |
| Observability | Log only | `siv_score`, `siv_violations` in decision_trace |

The two components are complementary, not redundant. SIV gates the analysis phase.
The existing freshness check gates the execution phase. Both should pass for a trade.

---

## Decision

Add Signal Integrity Validator as **Checkpoint 0** — the pre-pipeline data quality
gate that runs before `_analyze_market()` results are used in governance scoring.

Position in the governance pipeline:
```
[0] SIV  ← Signal Integrity Validator (ADR-033) — NEW
[1] Monte Carlo VETO
[2] RMS VETO
[3] VETO Early Return
[4] Coherence Gate (6-tier)
[5] TCV — Temporal Coherence Validation (ADR-032)
[6] Edge Confirmation Window (ECW) Gate (ADR-019)
[7] Scoring
[8] Final Decision
```

---

## Validation Categories (4)

### 1. Data Freshness (Severity: CRITICAL / HIGH / LOW)

Validates when each data source was last successfully fetched.

| Source | Max Age | Violation | Severity |
|--------|---------|-----------|----------|
| Kraken price | 300s (5 min) | `PRICE_DATA_STALE` | CRITICAL |
| OHLC candles | 900s (15 min) | `OHLC_DATA_STALE` | HIGH |
| Sentiment/news | 1800s (30 min) | `SENTIMENT_DATA_STALE` | LOW |

Configurable via `SIV_PRICE_STALE_SECS`, `SIV_OHLC_STALE_SECS` env vars.

### 2. Completeness (Severity: CRITICAL / MEDIUM)

Validates that required fields are present and valid.

| Field | Missing Violation | Severity |
|-------|------------------|----------|
| Current price | `MISSING_PRICE` | CRITICAL |
| Price type | `INVALID_PRICE_TYPE` | CRITICAL |
| Price value | `NON_POSITIVE_PRICE` | CRITICAL |
| 24h Volume | `MISSING_VOLUME` | MEDIUM |
| OHLC data | `MISSING_OHLC` | MEDIUM |

### 3. Anomaly Detection (Severity: CRITICAL / HIGH / MEDIUM)

Detects statistically implausible price values.

| Check | Violation | Severity |
|-------|-----------|----------|
| Price change > 20% vs last cycle | `PRICE_SPIKE_ANOMALY` | HIGH |
| Bid/ask spread > 5% | `SPREAD_ANOMALY` | MEDIUM |
| Bid ≥ Ask (inverted market) | `INVERTED_SPREAD` | CRITICAL |

Configurable via `SIV_ANOMALY_THRESHOLD`, `SIV_SPREAD_THRESHOLD` env vars.
The price history window is maintained in-memory (last 20 prices per symbol).

### 4. Cross-Source Consistency (Severity: HIGH / MEDIUM)

When secondary price sources are available (CoinGecko, etc.), validates agreement.

| Discrepancy | Violation | Severity |
|-------------|-----------|----------|
| > 6% (3× tolerance) | `SOURCE_PRICE_DISCREPANCY` | HIGH |
| > 2% (tolerance) | `SOURCE_PRICE_DISCREPANCY` | MEDIUM |

Configurable via `SIV_CROSS_SOURCE_TOLERANCE` env var (default 2%).

---

## Scoring

Each violation deducts from a starting score of 100:

| Severity | Deduction |
|----------|-----------|
| CRITICAL | −30 |
| HIGH | −20 |
| MEDIUM | −10 |
| LOW | −5 |

**Score range:** [0, 100]. Minimum 0 (no negative scores).  
**Threshold:** `SIV_THRESHOLD` env var (default 60). Score < threshold → FAIL → HOLD.

A single CRITICAL violation (−30) reduces score to 70, which still passes at the default
threshold of 60. Two CRITICAL violations (−60) would fail. This is intentional —
SIV is designed to catch severe data corruption, not to become a veto machine.

---

## Fail-Safe Design

On any SIV module error → `passed=True`, `pass_through=True`.

SIV never blocks the pipeline due to its own failure. This is consistent with the
fail-safe philosophy applied in TCV (ADR-032) and the Coherence Engine (ADR-017).
The decision trace records `siv_pass_through=True` for observability.

---

## Observability

Every evaluation adds to `decision_trace`:

| Field | Description |
|-------|-------------|
| `siv_score` | Composite integrity score [0-100] |
| `siv_passed` | Whether SIV threshold was met |
| `siv_violation_count` | Number of violations detected |
| `siv_violations` | List of violation codes |
| `siv_pass_through` | True if SIV returned passed due to module error |

Log format:
```
🔍 [SIV] BTC/USD | Score: 78/100 | 1 violation(s) | sources=3 → PASS
🔍 [SIV] BTC/USD | Score: 40/100 | 3 violation(s) | sources=3 → FAIL → HOLD
```

---

## Consequences

### Positive
- **Closes the data integrity gap**: governance decisions now explicitly validate
  the data they operate on, not just the decisions themselves.
- **Defense-in-depth**: adds a fourth layer before existing execution-time freshness check.
- **Audit trail**: SIV violations are captured in decision_trace and PQC-signed receipts.
- **Configurable thresholds**: all parameters are env vars — no code change needed to tune.
- **Investor narrative**: demonstrates OMNIX validates inputs, not just outputs.

### Constraints
- **In-memory price history**: anomaly detection requires at least one prior price per symbol.
  First evaluation after startup has no history → `PRICE_SPIKE_ANOMALY` cannot trigger.
- **Secondary source dependency**: cross-source check only activates when secondary prices
  are passed by the caller. If not provided, this category is skipped (not penalized).
- **Conservative threshold (60)**: designed to block only genuine data corruption events.
  Systems running without secondary price sources will not be penalized.

---

## Test Coverage

47 tests in `tests/test_signal_integrity_validator.py`:

| Test Class | Tests | Coverage Area |
|------------|-------|---------------|
| `TestSIVResult` | 4 | Dataclass structure and serialization |
| `TestSIVViolation` | 1 | Violation dataclass |
| `TestSIVFailSafe` | 5 | Fail-safe behavior |
| `TestSIVFreshness` | 6 | Freshness validation per source |
| `TestSIVCompleteness` | 7 | Field completeness and type validation |
| `TestSIVAnomalyDetection` | 8 | Spike, spread, inverted spread detection |
| `TestSIVCrossSource` | 5 | Multi-source consistency |
| `TestSIVScoring` | 6 | Score computation and threshold |
| `TestSIVSources` | 2 | sources_checked counter |
| `TestSIVPriceHistory` | 2 | In-memory history management |

---

## Implementation Files

```
omnix_core/data/__init__.py
omnix_core/data/signal_integrity_validator.py
omnix_core/bot/auto_trading_bot.py  (integration — Checkpoint 0)
tests/test_signal_integrity_validator.py
```

---

## Configuration Reference

| Env Var | Default | Description |
|---------|---------|-------------|
| `SIV_THRESHOLD` | 60 | Minimum score to pass |
| `SIV_PRICE_STALE_SECS` | 300 | Max price age (seconds) |
| `SIV_OHLC_STALE_SECS` | 900 | Max OHLC age (seconds) |
| `SIV_ANOMALY_THRESHOLD` | 0.20 | Max single-cycle price change |
| `SIV_SPREAD_THRESHOLD` | 0.05 | Max bid/ask spread |
| `SIV_CROSS_SOURCE_TOLERANCE` | 0.02 | Max cross-source price discrepancy |

---

## Relationship to Prior ADRs

| ADR | Relationship |
|-----|-------------|
| ADR-004 | Position sizing — SIV FAIL skips Kelly sizing entirely |
| ADR-017 | FINAL_DECISION_REASON — SIV_FAIL is a valid reason code |
| ADR-019 | ECW Gate — SIV FAIL resets ECW counter (bad data invalidates edge persistence) |
| ADR-028 | External Governance API — SIV applied to domain adapter inputs |
| ADR-032 | TCV — SIV is Checkpoint 0; TCV is Checkpoint 7. Symmetric fail-safe design. |
