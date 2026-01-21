# ADR-018: DECISION_CONTRADICTION_INDEX (DCI)

**Date:** January 21, 2026  
**Status:** Accepted  
**Category:** Observability / Institutional Transparency / Shadow Metric

## Context

OMNIX frequently sees scenarios where:
- Non-Markovian memory shows BUY 70%+ confidence
- EMA signal is NONE
- Monte Carlo expected return is near zero
- Action taken: HOLD

This is **correct behavior** - the system refuses to trade when local signals contradict global edge. However, this leaves an important question unanswered for investors:

> "If there was a strong BUY signal... why didn't it enter?"

The answer exists implicitly in logs, but investors and risk committees need an **explicit, quantified** explanation.

## Decision

Implement **DECISION_CONTRADICTION_INDEX (DCI)** - a shadow observational metric that measures internal contradiction between signals.

### Key Properties

| Property | Value |
|----------|-------|
| **Mode** | Shadow / Observational only |
| **Affects Trading** | NO - purely diagnostic |
| **Output** | Score 0-100, Level: LOW / MEDIUM / HIGH |
| **Purpose** | Explain HOLDs with high local signals |

## Formula (v0.1)

DCI is computed from 4 components using data already available in the decision payload:

```python
DCI = local_strength + global_edge_penalty + regime_penalty + risk_penalty
```

### Components (0-100 total)

| Component | Max Points | Calculation |
|-----------|------------|-------------|
| **Local Signal Strength** | 40 | avg(NonMarkovian%, EMA%) normalized 0-40 |
| **Global Edge Penalty** | 30 | Inverse of edge quality: (30 - edge_score) |
| **Regime Misalignment** | 15 | VOLATILE/RANGING with high vol = 15, BULLISH/low vol = 0 |
| **Risk Overlay** | 15 | Black Swan severity: LOW=3, MEDIUM=7, HIGH=12, EXTREME=15 |

### Interpretation

| DCI Score | Level | Meaning |
|-----------|-------|---------|
| 0-34 | LOW | Signals aligned, decision clear |
| 35-69 | MEDIUM | Mixed signals, moderate uncertainty |
| 70-100 | HIGH | Strong contradiction - HOLD justified by conflict |

### Example Calculation

**Scenario: BTC/USD with strong local but weak global**

```
Inputs:
  Non-Markovian: BUY 71%
  EMA: NONE (0%)
  MC_ER: 0.0001
  MC_WR: 43%
  Regime: VOLATILE
  Black Swan: MEDIUM

Calculation:
  local_strength = avg(71, 0) * 0.4 = 14.2
  global_edge_penalty = 30 - clamp((43-50)*0.6 + 0.0001*1000, 0, 30) = 30 - 0 = 30
  regime_penalty = 12 (VOLATILE)
  risk_penalty = 7 (MEDIUM)

  DCI = 14.2 + 30 + 12 + 7 = 63.2 → MEDIUM

Interpretation: Moderate contradiction. Local signals mixed (one strong, one absent), 
global edge insufficient, regime unfavorable. HOLD is correct.
```

## Implementation

### Location

`omnix_core/bot/auto_trading_bot.py` - immediately after FINAL_DECISION_REASON block

### Log Format

```
📊 DECISION_CONTRADICTION_INDEX:
   - Score: 63
   - Level: MEDIUM
   - Local strength: 14.2 (NM=71%, EMA=0%)
   - Edge penalty: 30.0 (MC_ER=0.0001, WR=43%)
   - Regime penalty: 12 (VOLATILE)
   - Risk penalty: 7 (MEDIUM)
   → High internal contradiction between local signal and global edge
```

### Decision Payload

```python
decision['decision_contradiction_index'] = {
    'score': 63.2,
    'level': 'MEDIUM',
    'components': {
        'local_strength': 14.2,
        'global_edge_penalty': 30.0,
        'regime_penalty': 12,
        'risk_penalty': 7
    },
    'interpretation': 'High internal contradiction between local signal and global edge'
}
```

## Validation (Day 9 Analysis)

### Objective

Determine if DCI predicts trade outcomes better than random chance.

### Methodology

1. Compute DCI retroactively for Days 1-6 trades and vetoed decisions
2. Calculate correlations:
   - DCI vs win rate
   - DCI vs average drawdown
   - DCI vs profit_loss

### Success Criteria

| Metric | Threshold | Action |
|--------|-----------|--------|
| r ≥ 0.6 | DCI is valid predictor | Promote to investor-facing |
| r ≤ 0.4 | DCI is vanity metric | Archive, don't use |
| 0.4 < r < 0.6 | Inconclusive | Refine after Day 30 |

### SQL Query for Retroactive Analysis

```sql
WITH dci_trades AS (
  SELECT 
    id,
    symbol,
    profit_loss,
    profit_pct,
    coherence_score,
    hmm_regime,
    CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END as is_win,
    -- Compute DCI components from stored data
    COALESCE((hmm_regime::json->>'volatility')::float, 0.3) as volatility
  FROM paper_trading_trades
  WHERE status = 'closed'
    AND telemetry_source = 'REAL'
)
SELECT 
  symbol,
  COUNT(*) as trades,
  AVG(coherence_score) as avg_coherence,
  SUM(is_win)::float / COUNT(*) as win_rate,
  AVG(profit_loss) as avg_pnl
FROM dci_trades
GROUP BY symbol
ORDER BY avg_pnl;
```

## Benefits

### For Investors / Risk Committee

- Demonstrates OMNIX **knows when not to trust** a signal
- Converts HOLD from passive inaction to **active decision**
- Eliminates argument: "missed opportunities due to rigidity"

### For Architecture

- No feedback loops introduced
- No decision changes
- Observational only - safe for production

### For Audit

- Explicit documentation of internal contradiction
- Enables ex-post analysis of opportunity cost vs risk
- Full traceability in decision payload

## Pitch-Ready Language

> "OMNIX doesn't just block trades for risk; it explicitly measures internal contradiction between signals, refusing to act when the market sends inconsistent messages."

## Future Enhancements (Post-Validation)

1. **OPPORTUNITY_COST_LEDGER** - Track how much was left on table without hindsight bias
2. **GOVERNANCE_OVERRIDE_WINDOW** - When humans can intervene without breaking discipline
3. **DCI Dashboard Widget** - Visual display if validation passes

## Files Changed

- `omnix_core/bot/auto_trading_bot.py` - DCI computation and logging
- `docs/reference/adr/ADR-018-decision-contradiction-index.md` - This document
- `docs/README.md` - Reference added
- `docs/REAL_SYSTEM_STATUS.md` - Recent changes updated

## Consequences

- Slightly larger log output per cycle (~6 lines)
- `decision_contradiction_index` dict available in decision payload
- Enables retroactive analysis via SQL
- No impact on trading logic (shadow mode only)

## References

- ADR-017: FINAL_DECISION_REASON Summary Block
- ADR-007: Coherence Threshold Calibration
- ADR-008: Opportunity Tracker
