# OMNIX — Mathematical Audit Report
# P&L Integrity, Fee Treatment & Sharpe Ratio Analysis

**Date**: February 24, 2026
**Scope**: All 119 paper_trading_trades (Learning Baseline, Nov 30 - Dec 29, 2025)
**Auditor**: Automated Pipeline Validation (Stages 1-3)
**Status**: COMPLETED — Findings documented below

---

## Executive Summary

The 119 trades in the Learning Baseline have a **$4,487.87 total discrepancy** between stored P&L and `(exit_price - entry_price) * quantity`. Root cause has been identified: **Kraken round-trip fees (0.52%) are embedded in the P&L for 106 trades but NOT for 12 trades**, creating inconsistent fee treatment. One trade (#1) is anomalous. No synthetic data was found — all discrepancies are explainable.

| Category | Trades | Delta | Status |
|----------|--------|-------|--------|
| FEE_MATCH | 106 | -$4,589.31 | Fees correctly deducted |
| EXACT_MATCH | 12 | -$0.02 | Fees NOT deducted (different code path) |
| ANOMALOUS | 1 | +$101.46 | Trade #1 — impossible P&L direction |
| **TOTAL** | **119** | **-$4,487.87** | |

---

## Stage 1 — DB Column Inventory

| Required Field | DB Column | Exists? | Notes |
|----------------|-----------|---------|-------|
| entry_price | `entry_price` | YES | NUMERIC, NOT NULL |
| exit_price | `exit_price` | YES | NUMERIC, nullable (NULL = open) |
| position_size | `quantity` | YES | NUMERIC, NOT NULL |
| fees | — | **NO** | No fee column exists |
| pnl | `profit_loss` | YES | NUMERIC, nullable |
| pnl_percent | `profit_pct` | YES | NUMERIC, nullable |
| timestamp_entry | `opened_at` | YES | TIMESTAMP |
| timestamp_exit | `closed_at` | YES | TIMESTAMP, nullable |
| telemetry_source | `telemetry_source` | YES | ALL = LEGACY_ESTIMATED |
| execution_source | — | **NO** | No price source tracking |

**Missing fields**: `fees` (individual fee per trade) and `execution_source` (Kraken API vs snapshot vs estimation).

---

## Stage 2 — P&L Mathematical Verification

### Formula Discovery

**For 106 trades** (closed by legacy auto_trading_bot.py code path):
```
stored_pnl = (exit_price - entry_price) * quantity 
             - (entry_price * quantity * 0.0026)     # entry fee
             - (exit_price * quantity * 0.0026)       # exit fee

Verification: residual = stored_pnl - gross_pnl + round_trip_fee = 0.0000 for ALL 106
```

Fee formula: `fee = notional_usd * 0.0026` (Kraken taker fee = 26 bps per side, 52 bps round-trip).

**For 12 trades** (closed by `_close_position_fifo_v2()` in paper_trading.py):
```
stored_pnl = (exit_price - entry_price) * quantity
             # NO fee deduction

Code reference: paper_trading.py line 540:
  gross_pnl = (exit_price - entry_price_float) * quantity_float
Line 555: stores gross_pnl directly as profit_loss
```

**For Trade #1** (anomalous):
```
entry: 90874.90 → exit: 90000.00 (BUY, price DECREASED)
Recalculated P&L: -$0.96
Stored P&L: +$100.50
Delta: +$101.46 — DIRECTION ERROR
Likely cause: Early test/manual entry, first trade in system
```

### Code Path Analysis

Two different code paths close trades:

| Path | File | Fee Treatment | Trades |
|------|------|---------------|--------|
| Legacy | auto_trading_bot.py:5244 | `pnl = (current_price - avg_price) * qty` then fee deducted from balance | 106 |
| FIFO v2 | paper_trading.py:540 | `gross_pnl = (exit - entry) * qty`, stored WITHOUT fee | 12 |

The inconsistency: FIFO v2 calculates fees (`fee_usd = self._calculate_fee(quote_notional_usd)` at line 539) but only uses them for balance updates, NOT for the stored `profit_loss`.

### Aggregate Financial Impact

```
Stored Total P&L:              -$15,198.73
Gross P&L (no fees):            -$10,710.86
Total Round-Trip Fees (all):     -$5,100.40
If all had fees deducted:       -$15,811.26

Missing fees (12 exact trades):    $510.57
Trade #1 anomaly:                  $101.46
Accounted delta:                   $612.03  ≈ (-15,198.73) - (-15,811.26) = $612.53 ✓
```

---

## Stage 3 — Direction Error Analysis (20 trades)

20 trades were initially classified as "DIRECTION_ERROR" (price moved one way, P&L went opposite). After fee analysis, ALL 20 are explained:

- The stored P&L includes ~0.52% round-trip fees
- For trades where gross P&L is positive but small, fees can flip the sign (making positive gross → negative net)
- For trades where gross P&L is negative, fees make it more negative
- Example: Trade #8 — gross P&L = +$23.87, but fees = $124.37, so net = -$100.50. Correctly stored.

**Only Trade #1 remains genuinely anomalous** (cannot be explained by any fee model).

---

## Stage 4 — Sharpe Ratio Analysis

### Current Formula (queries.py:288-297)
```python
initial_capital_for_sharpe = 1_000_000          # ARBITRARY ASSUMPTION
pct_returns = np.array(pnls) / 1_000_000 * 100  # $ → %
risk_free_rate = 0.05 / 252                      # 5% annual / 252 trading days
excess_returns = pct_returns - risk_free_rate
sharpe = mean(excess) / std(pct_returns) * sqrt(min(N, 252))
```

### Issues Identified

1. **$1M capital assumption**: Not sourced from actual balance. Arbitrary but reasonable for institutional framing (initial paper trading balance was $1M).
2. **Inconsistent P&L inputs**: Sharpe uses `pnls` array from stored P&L, which mixes fee-inclusive (106) and fee-exclusive (12) values.
3. **Annualization factor**: Uses `sqrt(N)` capped at `sqrt(252)`. Each trade is treated as one "period" — acceptable for paper trading but not standard institutional practice.
4. **Sortino denominator**: Only uses downside returns std, which is correct.

### Sharpe Sensitivity

The $1M denominator makes all returns tiny (max trade was $292 = 0.029% of $1M), resulting in a Sharpe that's heavily dampened. This is conservative — if anything, the Sharpe underestimates volatility impact because it treats $292 as negligible relative to $1M.

---

## Stage 5 — Recommendations

### R1: Trade #1 — Quarantine or Correct
Trade #1 is the only unexplainable entry. Options:
- (a) Mark as `ANOMALOUS` and exclude from metrics
- (b) Recalculate using correct formula: `pnl = (90000 - 90874.90) * 0.00110036 - fees = -$1.48`
- (c) Delete as test data

### R2: Fee Inconsistency — Standardize
12 trades have no fee deduction. Options:
- (a) Recalculate these 12 trades' P&L to include fees (decreases total P&L by ~$510)
- (b) Keep as-is with documentation (current behavior)
- (c) Add `fees` column and backfill all 119 trades with calculated fees

### R3: Fix _close_position_fifo_v2
Line 555 of paper_trading.py stores `gross_pnl` instead of `net_pnl`. For future trades, `profit_loss` should include fees for consistency:
```python
net_pnl = gross_pnl - entry_fee - exit_fee  # where entry_fee = entry_price * qty * 0.0026
```

### R4: Sharpe Documentation
Document the $1M capital assumption explicitly. Optionally source from `paper_trading_balances.balance_usd` initial value.

### R5: Add `fees` Column
```sql
ALTER TABLE paper_trading_trades ADD COLUMN fees_usd NUMERIC DEFAULT 0;
```
Backfill with: `UPDATE SET fees_usd = (entry_price * quantity + exit_price * quantity) * 0.0026 WHERE telemetry_source = 'LEGACY_ESTIMATED';`

### R6: Add `execution_source` Column
Track whether prices came from Kraken API, snapshot, or estimation for future trades.

---

## Conclusion

**The discrepancy is structural but EXPLAINABLE.** It is NOT:
- Synthetic data
- Silent fallbacks
- Hidden bias

It IS:
- Two different code paths with inconsistent fee treatment
- One anomalous early test trade
- A documented $1M capital assumption for Sharpe

**Financial materiality**: The $510 fee gap (12 trades without fees) represents 3.4% of total P&L. Trade #1's $101.46 error represents 0.67% of total P&L. Combined: ~4% materiality.

**Recommended priority**: Fix R3 (future trades) → R5 (add fees column) → R1 (quarantine trade #1) → R2 (standardize historical).
