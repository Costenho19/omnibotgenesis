# ARES V1/V2 - Experimental Trading Strategies
## Status: ACTIVE in Paper Trading (V6.5.4d)
### December 2025

> **UPDATE Dec 11, 2025:** ARES V1+V2 are now **ACTIVE** in PRODUCTION_STABLE profile for track record generation. They remain classified as experimental for investor metric separation. V6.5.4d adds macro trend veto (Kalman/HMM) to prevent trades in bearish trends.

---

## OVERVIEW

ARES (Advanced Regime-aware Entry System) is a set of experimental trading strategies currently under development and calibration. These modules are **not included in production trading metrics** until validation is complete.

---

## ARES V1 - Swing Trading Protocol

### Architecture (3-Layer System)

| Layer | Name | Function |
|-------|------|----------|
| 1 | ANF (Adaptive Noise Filtering) | Signal smoothing with HP Filter |
| 2 | ISA (Institutional Signal Aggregation) | Multi-indicator consensus |
| 3 | SXE (Signal eXecution Engine) | Entry/exit optimization |

### Indicators Used
- Triple EMA Crossover (8/21/55)
- RSI Adaptive (14-period with dynamic thresholds)
- MACD with signal confirmation
- Volume Confirmation (relative volume analysis)
- ATR for volatility sizing

### Target Metrics
- Win Rate: 55-65%
- Risk/Reward: 2:1 minimum
- Timeframe: 4H to 1D

### Current Status (V6.5.4d)
- Implementation: Complete
- Backtesting: Complete
- **Live Calibration: ACTIVE** (Dec 11, 2025)
- Minimum Confidence: 70%
- Max Daily Trades: 3 (shared with V2)
- Macro Trend Veto: Active (Kalman/HMM)

---

## ARES V2 - Scalping Protocol

### Design Philosophy
Fast scalping strategy for quick opportunities on short timeframes.

### Indicators
- EMA 5/13 crossover
- RSI 7-period fast
- Volume spike detection
- Micro-volatility analysis

### Target Metrics
- Win Rate: 60-70%
- Risk/Reward: 1.5:1
- Timeframe: 15m to 1h

### Current Status (V6.5.4d)
- Implementation: Complete
- Backtesting: Complete
- **Live Calibration: ACTIVE** (Dec 11, 2025)
- Minimum Confidence: 75%
- Max Daily Trades: 3 (shared with V1)
- Macro Trend Veto: Active (Kalman/HMM)

---

## V6.5.4d CONFIGURATION

```python
# PRODUCTION_STABLE Profile Settings
ares_enabled = True
ares_v1_enabled = True
ares_v2_enabled = True
ares_v1_min_confidence = 0.70
ares_v2_min_confidence = 0.75
ares_max_daily_trades = 3
ares_require_trend = False  # Allows lateral markets

# V6.5.4d Additions
score_moderate = 12  # Same as score_strong (MODERATE disabled)
emergency_sl_pct = 0.02  # 2% max absolute loss
macro_trend_veto = True  # Kalman/HMM bearish blocking
```

---

## KILL-SWITCH SYSTEM

ARES includes protective kill-switches that halt trading when:
- Balance drops below threshold
- Win rate falls below minimum
- Consecutive losses exceed limit
- Volatility exceeds safe parameters

---

## VALIDATION REQUIREMENTS

Before ARES moves to production:

1. **Backtesting Results**
   - 1000+ simulated trades
   - Win rate > 55% across all market conditions
   - Maximum drawdown < 15%

2. **Paper Trading Validation**
   - 200+ live paper trades
   - Consistent performance over 30 days
   - Risk metrics within targets

3. **Production Pilot**
   - Small position sizes (1% max)
   - Close monitoring for 2 weeks
   - Gradual position increase

---

## TIMELINE

| Phase | Duration | Status |
|-------|----------|--------|
| Development | Completed | Done |
| Backtesting | 2-4 weeks | In Progress |
| Paper Validation | 4-6 weeks | Pending |
| Production Pilot | 2 weeks | Pending |
| Full Production | TBD | Pending |

---

## NOTES

ARES is separate from the production trading system. The current production system uses:
- QuantumMomentum Strategy
- Monte Carlo Validation
- Kelly Criterion Position Sizing
- HMM Regime Detection
- Kalman Filter
- Non-Markovian Kernel
- Coherence Engine (6-tier)
- Risk Guardian

These production strategies have their own metrics that are presented to investors.

---

*Last Updated: December 2025*
*Document Location: docs/experimental/*
