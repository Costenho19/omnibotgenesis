# OMNIX Phase 0 — Retrospective Governance Backtest

**Status**: INTERNAL DUE DILIGENCE 
**Date**: 2026-03-01 
**Author**: Harold Nunes 
**Period Analyzed**: July 6 – August 18, 2025 (Phase 0, Real Kraken Capital) 
**Method**: Retrospective signal estimation from real trade price history 

---

## Purpose

Answer a specific, verifiable question:

> If the OMNIX 6-checkpoint governance engine had been active during Phase 0, what proportion of the 1,115 real trades would have been blocked? And what does that imply for the -$1,167 / -28.6% loss in that period?

This document serves as internal due diligence. Results are stored in PostgreSQL for auditability.

---

## Background: Phase 0 Real Capital Activity

| Metric | Value | Source |
|--------|-------|--------|
| Period | Jul 6 – Aug 18, 2025 | Kraken ledger |
| Capital deployed | $4,076.66 | 6 BTC deposits, verified |
| Trades executed | 1,115 real Kraken trades | Ledger imported to `kraken_real_trades` |
| Assets traded | BTC, SOL, ETH, AVAX | Kraken spot exchange |
| P&L | -$1,167 (-28.6%) | End portfolio value vs. deposits |
| Fees paid | $168.84 | Kraken commissions |
| Money type | **REAL** — actual Kraken exchange capital | Never simulated/paper |
| Governance engine | **NOT active** | 6-checkpoint system built Nov 2025 |

---

## Methodology

### Data Sources
- **Price data**: Derived from `kraken_real_trades.amount_usd / amount` — exact prices at the moment of each real Kraken trade. No external OHLCV required.
- **Evaluation granularity**: Asset × hour buckets (e.g., "BTC at 2025-07-08 17:00")
- **Strict no-look-ahead**: Signals for each evaluation point computed using only price history from trades **prior** to that hour

### Signal Computation (per evaluation point)

For each (asset, hour) with ≥ 20 prior price data points, the following signals were computed using real OMNIX modules:

| Governance Signal | Computation Method |
|---|---|
| `probability_score` | EMA confidence × HMM bullish/ranging confidence |
| `risk_exposure` | ATR-based volatility percentile (inverted: high vol = high risk) |
| `signal_coherence` | Agreement between EMA direction and HMM regime |
| `trend_persistence` | Autocorrelation of directional moves in last 12 data points |
| `stress_resilience` | Monte Carlo win rate (2,000 simulations, GBM model) |
| `logic_consistency` | 100 - normalized variance across the 5 signals above |

### Governance Engine
The **exact** `GovernanceEvaluationEngine` from `omnix_core/governance/external_evaluator.py` was used, with unchanged thresholds:

| Checkpoint | Signal | Threshold |
|---|---|---|
| CP-1 Probability | `probability_score` | ≥ 50 |
| CP-2 Risk Limits | `risk_exposure` | ≤ 65 |
| CP-3 Signal Coherence | `signal_coherence` | ≥ 55 |
| CP-4 Trend Persistence | `trend_persistence` | ≥ 50 |
| CP-5 Stress Resilience | `stress_resilience` | ≥ 35 |
| CP-6 Logic Consistency | `logic_consistency` | ≥ 40 |

---

## Results

### Evaluation Coverage

| Metric | Value |
|--------|-------|
| Total (asset × hour) evaluation points | 258 |
| Points with sufficient data (≥ 20 prior trades) | 225 |
| Points with insufficient data | 33 |

### Governance Decisions

| Decision | Count | Percentage |
|---------|-------|-----------|
| **BLOCKED** | **215** | **95.6%** |
| **APPROVED** | **10** | **4.4%** |

### Most Triggered Checkpoints (in BLOCKED decisions)

| Checkpoint | Times Triggered |
|---|---|
| CP-1: Probability Check | 166 |
| CP-3: Signal Coherence | 159 |
| CP-4: Trend Persistence | 156 |
| CP-2: Risk Limits | 18 |

### Interpretation

**95.6% of evaluation points fail the governance checkpoints.** This is the primary finding.

The engine consistently detected:
- Low probability of positive outcomes (CP-1 failing 74% of BLOCKED cases)
- Weak signal agreement between EMA and HMM models (CP-3)
- Lack of trend persistence — the market was oscillating without directional conviction (CP-4)

This is **exactly what we would expect** looking back at the Jul–Aug 2025 period:
- High-frequency short-term trades with no regime alignment
- BTC oscillating without sustained directional momentum
- Excessive trading frequency (1,115 trades in 44 days = ~25 trades/day)

**The governance engine's 95.6% block rate is consistent with the observed losses.** The system correctly identifies this as an unfavorable trading regime.

---

## What This Means for the Capital Preservation Narrative

### Honest Statement (Valid)
> "When we retroactively applied the 6-checkpoint governance engine to Phase 0 trade signals, 95.6% of evaluation points failed at least one checkpoint — primarily due to insufficient trend persistence and weak signal coherence. The engine identified this period as a high-uncertainty, low-probability-of-success regime. Not trading preserves capital. The system's design is consistent with this outcome."

### What We Cannot Claim (Per Architect Review)
- We **cannot** state an exact P&L improvement figure, because:
 - The signal computation is a reconstruction, not a live replay
 - The thresholds were calibrated in Nov 2025–Jan 2026, not in Jul–Aug 2025
 - Blocking trades in a short-term scalping regime doesn't simply "preserve" the spent USD — it changes the entire trading behavior
- The hourly grouping simplifies 1,115 individual trades into 225 evaluation points

---

## Documented Limitations (Mandatory Disclosure)

Per the Architect Review (2026-03-01), the following limitations MUST be disclosed to institutional investors:

1. **Retrospective reconstruction, not live replay**: Signals were computed from real trade price history after the fact. The live system in Jul–Aug 2025 did not have these signals.

2. **Calibration drift**: Current governance thresholds were calibrated using Nov 2025–Jan 2026 data. Applying them to Jul–Aug 2025 may reflect hindsight bias.

3. **Execution effects not modeled**: Slippage, partial fills, and latency are not simulated. "Blocked trade P&L = $0" is hypothetical.

4. **Signal approximation**: The mapping from price history to the 6 governance signals is a reasonable approximation of the live system logic — not the exact pipeline that would have run at the time.

5. **Hourly granularity**: 1,115 individual trades are grouped into 225 asset×hour evaluation points. Finer granularity would require tick-data not available from the public Kraken API for 2025.

---

## Database Records

| Table | Description |
|---|---|
| `kraken_real_trades` | 2,237 raw ledger entries from Kraken (Jul 6 – Aug 18, 2025). Real capital. |
| `backtest_phase0_signals` | 225 computed evaluation points (COMPUTED) + 33 (INSUFFICIENT_DATA) |
| `backtest_phase0_results` | 225 governance decisions with veto chains |

---

## Conclusion

The retrospective backtest shows the governance engine would have flagged 95.6% of Phase 0 trade groups as high-uncertainty / fail-closed. This is consistent with the actual -28.6% loss in that period.

**The story is not "the engine would have avoided the loss."**

**The story is: "The engine detects the type of market behavior that caused the loss — and its fail-closed design responds correctly: do not trade."**

This is a stronger and more credible claim than a specific P&L improvement figure, because it is grounded in what the system actually does rather than a simulated counterfactual.

The narrative for investors remains the three-phase arc:
- **Phase 0 (Real capital)**: $4,076 real money, 1,115 trades, -$1,167 loss. No governance.
- **Phase 1 (Paper, calibration)**: Built 6-checkpoint engine. 119 paper trades. Calibrated.
- **Phase 2 (Paper, track record)**: 98.5% capital preserved while BTC fell 7.37%.

The backtest provides internal evidence that the engine's conservative behavior in Phase 2 is **not arbitrary** — it reflects the same detection logic that would have signaled extreme caution in Phase 0.

**Recommendation**: Use the 95.6% block rate finding as internal due diligence evidence. Do not publish as a primary pitch metric without a full external audit. Use the qualitative narrative ("fail-closed detected high-uncertainty correctly") rather than a specific P&L improvement claim.

---

*See also: `docs/business/OMNIX_EUREKA_PITCH_FINAL.md` Slide 6 for investor-facing narrative.* 
*Scripts: `scripts/backtest/01_fetch_ohlcv.py`, `02_compute_signals.py`, `03_run_evaluation.py`*
