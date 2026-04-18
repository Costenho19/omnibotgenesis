# ADR-035: Regime-Conditioned Kelly (RCK)

**Status**: ACCEPTED  
**Date**: March 2026  
**Author**: Harold Nunes  
**Category**: Architecture — Position Sizing  
**Follows**: ADR-034 (FTI), ADR-004 (Position Sizing)

---

## Context

The Kelly Criterion in OMNIX uses three inputs: `win_rate`, `avg_win`, `avg_loss`.

**The gap**: These inputs were hardcoded constants:
```python
kelly = kelly_optimizer.calculate_optimal_position(
    win_rate=0.55,  # Hardcoded
    avg_win=0.03,   # Hardcoded
    avg_loss=0.02,  # Hardcoded
    ...
)
```

**Why this is statistically wrong**: A global win_rate of 0.55 merges the system's
performance across ALL market regimes — TRENDING, RANGING, VOLATILE, BEARISH.

These regimes have fundamentally different win characteristics:
- TRENDING regime: edge from momentum persistence; historically higher WR
- VOLATILE regime: edge disrupted by noise; historically lower WR, wider swings
- BEARISH regime: directional bias against BUY entries; different avg_loss profile

Mixing these into a single WR produces an averaged number that is optimal for
NO specific regime. It over-sizes positions during adverse regimes (VOLATILE,
BEARISH) and under-sizes during favorable regimes (TRENDING).

---

## Decision

Add Regime-Conditioned Kelly as a data provider for Kelly inputs, replacing
hardcoded values with regime-specific historical statistics.

**Implementation**: New class `RegimeConditionedKelly` in
`omnix_core/sizing/regime_conditioned_kelly.py`.

---

## Algorithm

### Input Query

Query `paper_trading_trades` filtered by:
- Symbol (optional)
- Regime (from HMM, stored in decision_trace JSON)
- Last `RCK_LOOKBACK_DAYS` days (default: 90)

Extract: `profit_loss` per trade → compute `win_rate`, `avg_win`, `avg_loss`.

### Fallback Chain (3 levels)

```
Level 1: Regime-specific stats (≥ RCK_MIN_SAMPLES=10 trades in current regime)
         → confidence: HIGH (≥30) or MEDIUM (10-29)

Level 2: Global stats (any regime, ≥ RCK_MIN_GLOBAL=5 trades)
         → confidence: LOW (fallback used)

Level 3: Conservative defaults
         win_rate=0.50, avg_win=1%, avg_loss=1%
         → confidence: LOW (fallback used)
```

### Example Outcome (with sufficient history)

| Regime | win_rate | avg_win | avg_loss | Kelly% | vs. Hardcoded |
|--------|----------|---------|----------|--------|---------------|
| TRENDING | 0.62 | 2.8% | 1.5% | 18.7% | +8.7% |
| RANGING | 0.54 | 2.1% | 1.9% | 3.2% | -6.8% |
| VOLATILE | 0.44 | 3.5% | 2.8% | 0% (negative) | -10% |
| BEARISH | 0.38 | 1.9% | 2.5% | 0% (negative) | -10% |
| *Hardcoded* | *0.55* | *3.0%* | *2.0%* | *10.0%* | baseline |

This shows the hardcoded approach over-sizes in VOLATILE/BEARISH and under-sizes
in TRENDING. RCK corrects this dynamically.

---

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `RCK_MIN_SAMPLES` | 10 | Min regime-specific trades to use regime stats |
| `RCK_MIN_GLOBAL` | 5 | Min global trades to use global fallback |
| `RCK_LOOKBACK_DAYS` | 90 | Trade history window |

---

## Confidence Levels

| Level | Condition | Action |
|-------|-----------|--------|
| HIGH | ≥30 regime-specific samples | Use regime stats with confidence |
| MEDIUM | 10-29 regime-specific samples | Use regime stats, note lower confidence |
| LOW | <10 regime-specific, ≥5 global | Use global stats (fallback used=True) |
| LOW | <5 global | Use conservative defaults (fallback used=True) |

---

## Observability

Added to decision_trace when Kelly runs:

| Field | Description |
|-------|-------------|
| `kelly_regime_conditioned` | True if regime-specific stats were used |
| `kelly_regime` | Which regime stats were applied |
| `kelly_regime_samples` | Number of historical trades for this regime |
| `kelly_confidence` | "HIGH", "MEDIUM", or "LOW" |
| `kelly_fallback_level` | "REGIME", "GLOBAL", or "DEFAULTS" |

---

## Current State (Launch)

At system launch with the Track Record Oficial starting Jan 15, 2026, and 0 trades:
- All 3 levels of the fallback chain lead to **Level 3: Conservative defaults**
- This is equivalent to the previous hardcoded behavior
- As the system executes trades and accumulates regime-segmented history,
  RCK automatically activates higher-confidence levels

**This is the correct behavior**: RCK doesn't introduce risk on Day 1.
It improves position sizing progressively as evidence accumulates.

---

## Test Coverage

36 tests in `tests/test_regime_conditioned_kelly.py`:

| Test Class | Tests | Coverage Area |
|------------|-------|---------------|
| `TestRegimeKellyStats` | 5 | Dataclass + Kelly fraction computation |
| `TestFallbackChain` | 6 | 3-level fallback logic |
| `TestRegimeStatsQuery` | 8 | Win rate, avg_win, avg_loss computation |
| `TestConfidenceLevels` | 6 | HIGH/MEDIUM/LOW confidence logic |
| `TestCalcStats` | 5 | Statistical computation |
| `TestIntegrationWithKelly` | 6 | Compatibility with KellyCriterionOptimizer |

---

## Consequences

### Positive
- **Evidence-based sizing**: Kelly inputs reflect actual system performance by regime.
- **Progressive improvement**: confidence increases automatically as trades accumulate.
- **Conservative launch**: defaults on Day 1 are equivalent to previous hardcoded behavior.
- **Fail-safe**: any DB error → conservative defaults, never crashes the pipeline.

### Constraints
- **Minimum history requirement**: 10 samples per regime for regime-specific stats.
  In early operation, the system falls back to global or defaults.
- **Regime detection dependency**: requires HMM regime to be stored in decision_trace.
  If not stored (old trades), those trades are excluded from regime-specific query.

---

## Relationship to Prior ADRs

| ADR | Relationship |
|-----|-------------|
| ADR-004 | Position sizing limits (2% max) — RCK provides inputs, ADR-004 still applies |
| ADR-014 | HMM Regime Detection — provides current_regime for RCK query |
| ADR-016 | Kelly logging policy — RCK adds regime metadata to Kelly log |
| ADR-035 | This ADR |
