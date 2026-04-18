# Decision Contradiction Index (DCI) - Retroactive Analysis

**Created:** January 21, 2026  
**Purpose:** SQL queries and analysis methodology for validating DCI as a predictor of trade outcomes  
**Reference:** ADR-018-decision-contradiction-index.md

## Overview

This document provides SQL queries to compute DCI retroactively for historical trades and validate whether high DCI scores correlate with poor trade outcomes.

## DCI Formula Recap

```
DCI = local_strength + global_edge_penalty + regime_penalty + risk_penalty

Components:
- Local strength (0-40): avg(NM%, EMA%) × 0.4
- Global edge penalty (0-30): 30 - edge_score
- Regime penalty (0-15): VOLATILE=15, RANGING=10, BEARISH/UNKNOWN=5, BULLISH=0
- Risk penalty (0-15): based on Black Swan severity
```

## Query 1: Compute DCI for Closed Trades

```sql
-- Retroactive DCI computation for paper_trading_trades
WITH trade_metrics AS (
  SELECT 
    id,
    symbol,
    action,
    entry_price,
    exit_price,
    profit_loss,
    profit_pct,
    coherence_score,
    CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END as is_win,
    -- Extract regime from hmm_regime JSON or use as string
    CASE 
      WHEN hmm_regime IS NULL THEN 'UNKNOWN'
      WHEN hmm_regime::text LIKE '{%' THEN 
        COALESCE((hmm_regime::json->>'regime')::text, 'UNKNOWN')
      ELSE hmm_regime::text
    END as regime,
    -- Extract volatility
    CASE 
      WHEN hmm_regime IS NULL THEN 0.2
      WHEN hmm_regime::text LIKE '{%' THEN 
        COALESCE((hmm_regime::json->>'volatility')::float, 0.2)
      ELSE 0.2
    END as volatility,
    telemetry_source,
    created_at
  FROM paper_trading_trades
  WHERE status = 'closed'
),
dci_computed AS (
  SELECT 
    *,
    -- Simplified DCI: use coherence as proxy for local strength
    -- (NM and EMA not directly stored, but coherence correlates)
    (COALESCE(coherence_score, 30) * 0.4) as local_strength,
    -- Edge penalty: assume neutral for legacy trades
    20 as global_edge_penalty,
    -- Regime penalty
    CASE 
      WHEN regime = 'VOLATILE' OR volatility > 0.25 THEN 15
      WHEN regime = 'RANGING' THEN 10
      WHEN regime IN ('BEARISH', 'UNKNOWN') THEN 5
      ELSE 0
    END as regime_penalty,
    -- Risk penalty: estimate from regime volatility
    CASE 
      WHEN volatility > 0.35 THEN 12
      WHEN volatility > 0.25 THEN 7
      ELSE 3
    END as risk_penalty
  FROM trade_metrics
)
SELECT 
  id,
  symbol,
  profit_loss,
  profit_pct,
  is_win,
  regime,
  volatility,
  coherence_score,
  local_strength + global_edge_penalty + regime_penalty + risk_penalty as dci_score,
  CASE 
    WHEN (local_strength + global_edge_penalty + regime_penalty + risk_penalty) < 35 THEN 'ALIGNED'
    WHEN (local_strength + global_edge_penalty + regime_penalty + risk_penalty) < 70 THEN 'TENSIONED'
    ELSE 'CONTRADICTORY'
  END as dci_level,
  telemetry_source,
  created_at
FROM dci_computed
ORDER BY created_at DESC;
```

## Query 2: DCI vs Win Rate Cohort Analysis

```sql
-- Compare win rates across DCI levels
WITH dci_trades AS (
  SELECT 
    id,
    profit_loss,
    CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END as is_win,
    COALESCE(coherence_score, 30) as coherence,
    CASE 
      WHEN hmm_regime IS NULL THEN 'UNKNOWN'
      WHEN hmm_regime::text LIKE '{%' THEN 
        COALESCE((hmm_regime::json->>'regime')::text, 'UNKNOWN')
      ELSE hmm_regime::text
    END as regime,
    CASE 
      WHEN hmm_regime IS NULL THEN 0.2
      WHEN hmm_regime::text LIKE '{%' THEN 
        COALESCE((hmm_regime::json->>'volatility')::float, 0.2)
      ELSE 0.2
    END as volatility
  FROM paper_trading_trades
  WHERE status = 'closed'
),
dci_scores AS (
  SELECT 
    *,
    -- Calculate DCI
    (coherence * 0.4) + 20 +
    CASE 
      WHEN regime = 'VOLATILE' OR volatility > 0.25 THEN 15
      WHEN regime = 'RANGING' THEN 10
      WHEN regime IN ('BEARISH', 'UNKNOWN') THEN 5
      ELSE 0
    END +
    CASE 
      WHEN volatility > 0.35 THEN 12
      WHEN volatility > 0.25 THEN 7
      ELSE 3
    END as dci_score
  FROM dci_trades
)
SELECT 
  CASE 
    WHEN dci_score < 35 THEN 'ALIGNED (0-34)'
    WHEN dci_score < 70 THEN 'TENSIONED (35-69)'
    ELSE 'CONTRADICTORY (70-100)'
  END as dci_level,
  COUNT(*) as trades,
  ROUND(AVG(CASE WHEN is_win = 1 THEN 100.0 ELSE 0 END), 1) as win_rate_pct,
  ROUND(AVG(profit_loss)::numeric, 2) as avg_pnl,
  ROUND(SUM(profit_loss)::numeric, 2) as total_pnl
FROM dci_scores
GROUP BY 1
ORDER BY 1;
```

## Query 3: Correlation Analysis Prep

```sql
-- Export data for correlation analysis in Python/pandas
SELECT 
  id,
  symbol,
  profit_loss,
  profit_pct,
  CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END as is_win,
  COALESCE(coherence_score, 30) as coherence_score,
  CASE 
    WHEN hmm_regime IS NULL THEN 'UNKNOWN'
    WHEN hmm_regime::text LIKE '{%' THEN 
      COALESCE((hmm_regime::json->>'regime')::text, 'UNKNOWN')
    ELSE hmm_regime::text
  END as regime,
  CASE 
    WHEN hmm_regime IS NULL THEN 0.2
    WHEN hmm_regime::text LIKE '{%' THEN 
      COALESCE((hmm_regime::json->>'volatility')::float, 0.2)
    ELSE 0.2
  END as volatility,
  -- Compute DCI inline
  (COALESCE(coherence_score, 30) * 0.4) + 20 +
  CASE 
    WHEN hmm_regime IS NULL THEN 5
    WHEN (hmm_regime::text LIKE '{%' AND (hmm_regime::json->>'regime') = 'VOLATILE') 
         OR (COALESCE((hmm_regime::json->>'volatility')::float, 0.2) > 0.25) THEN 15
    WHEN (hmm_regime::text LIKE '{%' AND (hmm_regime::json->>'regime') = 'RANGING') THEN 10
    WHEN hmm_regime::text IN ('BEARISH', 'UNKNOWN') THEN 5
    ELSE 0
  END +
  CASE 
    WHEN hmm_regime IS NULL THEN 5
    WHEN hmm_regime::text LIKE '{%' AND COALESCE((hmm_regime::json->>'volatility')::float, 0.2) > 0.35 THEN 12
    WHEN hmm_regime::text LIKE '{%' AND COALESCE((hmm_regime::json->>'volatility')::float, 0.2) > 0.25 THEN 7
    ELSE 3
  END as dci_score,
  telemetry_source,
  created_at
FROM paper_trading_trades
WHERE status = 'closed'
ORDER BY created_at;
```

## Python Validation Script

```python
import pandas as pd
from scipy import stats
import psycopg2
import os

# Load data from database
conn = psycopg2.connect(os.environ['DATABASE_URL'])
df = pd.read_sql("""
    SELECT 
        profit_loss,
        profit_pct,
        CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END as is_win,
        (COALESCE(coherence_score, 30) * 0.4) + 20 + 10 as dci_score
    FROM paper_trading_trades
    WHERE status = 'closed'
""", conn)
conn.close()

# Calculate correlations
corr_pnl = stats.pearsonr(df['dci_score'], df['profit_loss'])
corr_win = stats.spearmanr(df['dci_score'], df['is_win'])

print(f"DCI vs P&L Correlation: r={corr_pnl[0]:.3f}, p={corr_pnl[1]:.4f}")
print(f"DCI vs Win Rate Correlation: rho={corr_win[0]:.3f}, p={corr_win[1]:.4f}")

# Cohort comparison (investor-friendly naming)
aligned_dci = df[df['dci_score'] < 35]
contradictory_dci = df[df['dci_score'] >= 70]

print(f"\nALIGNED (<35): {len(aligned_dci)} trades, WR={aligned_dci['is_win'].mean()*100:.1f}%")
print(f"CONTRADICTORY (>=70): {len(contradictory_dci)} trades, WR={contradictory_dci['is_win'].mean()*100:.1f}%")
```

## Validation Criteria (Day 9)

| Metric | Threshold | Action |
|--------|-----------|--------|
| |r| >= 0.6 | DCI is valid predictor | Promote to investor-facing |
| |r| <= 0.4 | DCI is vanity metric | Archive, don't use |
| 0.4 < |r| < 0.6 | Inconclusive | Refine after Day 30 |

## Expected Results

If DCI works correctly:
- CONTRADICTORY DCI trades should have **lower** win rates
- ALIGNED DCI trades should have **higher** win rates
- Negative correlation between DCI and profit_loss

This validates that DCI captures internal contradiction and justifies HOLD decisions.

## Level Naming (Investor-Friendly)

| Technical | Investor-Friendly | Interpretation |
|-----------|-------------------|----------------|
| LOW (0-34) | ALIGNED | All signals converging, high-confidence decision |
| MEDIUM (35-69) | TENSIONED | Mixed signals detected, exercising caution |
| HIGH (70-100) | CONTRADICTORY | Significant internal conflict - capital preservation mode |
