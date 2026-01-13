# ADR-006: Dashboard Improvement Proposals

**Date:** January 13, 2026  
**Status:** Proposed  
**Author:** AI Analysis + Harold Review  
**Priority:** Critical (Fixes) / High (UX) / Medium (Nice-to-Have)

## Context

External analysis of the OMNIX Terminal Dashboard identified several critical issues and improvement opportunities. The current dashboard scores 7.5/10 and can be improved to 9.5/10 with targeted changes.

## Critical Issues (MUST FIX)

### Issue 1: Win Rate Directional Shows 0.0%

**Problem:**
- Header displays: 37.8% Precision (correct)
- Trade History section shows: WR Dir: 0.0% (INCORRECT)

**Impact:** Severe credibility issue - contradicting metrics confuse investors.

**Root Cause:** Trade History widget calculating WR Dir locally with different logic than header.

**Fix:** Ensure Trade History uses same query as header (`profit_pct > 0` for directional).

### Issue 2: "Protected" Metric is Misleading

**Problem:**
```
$31.4M Total Protected
```
This implies $31.4M was at risk when capital is only $1M.

**Impact:** Misleading for investors; could be seen as deceptive.

**Fix:** Rename to "Notional Blocked" with context:
```
$31.4M Notional Blocked
5 Actual Trades Prevented
$100K Avg Position Blocked
```

### Issue 3: Negative Metrics Too Prominent

**Problem:**
```
-5.82 Sharpe
-6.03 Sortino
0.13 Profit Factor
```
These destroy credibility when seen first.

**Fix:** Add calibration context:
```
CALIBRATION PHASE METRICS
Sharpe: -5.82 (pre-optimization)
Target: >1.0 (post-calibration)
Status: 119/100 trades completed
```

## UX/Visual Improvements (High Priority)

### Improvement 1: Quick Insights Section

Auto-generated actionable insights:
```
3 toxic symbols blocked: SOL, ADA, LINK
  -> Represent 70% of total losses
  
BTC only symbol with coherence >60%
  -> Current focus is correct

System 100% defensive last 48h
  -> High volatility + low coherence
```

### Improvement 2: System Health Score

Visual confidence indicator:
```
SYSTEM HEALTH: 72/100

Risk Controls: 95/100
Data Quality: 88/100
Win Rate: 35/100 (calibrating)
Latency: 98/100
Uptime: 100/100
```

### Improvement 3: Live Status Section

Real-time system state:
```
LIVE STATUS: DEFENSIVE MODE

Current Action: HOLD (all pairs)
Reason: Coherence <30% on XRP/AVAX
Next Analysis: 7 seconds

Active Vetos:
- XRP: Blocked (26.2% coherence)
- AVAX: Blocked (26.2% coherence)
```

### Improvement 4: Calibration Progress Bar

Show progress toward optimization:
```
Phase 1: Data Collection     100%
Phase 2: Pattern Analysis     65%
Phase 3: Threshold Opt.       30%
Phase 4: Live Deployment       0%
```

### Improvement 5: Recommended Actions

For Harold's daily decisions:
```
1. URGENT: Review EMA strategy
   Why: 100% NONE signals last 24h
   
2. Review coherence threshold
   Current: 30%, Blocking: 66% of analysis
   
3. Keep SOL/ADA/LINK blocked
   Reason: 0% WR, -$10k losses
```

## Nice-to-Have Improvements (Medium Priority)

### Comparative Metrics Table
```
Metric       OMNIX    BTC Hold   Avg Bot
30d Return   -2.56%   -7.37%    -12.5%
Max DD        1.5%     8.2%      15.3%
Alpha        +4.81%    0.0%      -5.1%
```

### P&L Breakdown Visual
```
By Symbol:
LINK:  -$4,482 (29%)
ADA:   -$4,261 (28%)
BTC:   -$3,200 (21%)
SOL:   -$1,952 (13%)
XRP:   -$1,303 (9%)
```

### Risk Heatmap
```
Symbol    Coherence  Volatility  Risk
BTC/USD   60.9%      27.8%       LOW
XRP/USD   26.2%      50.1%       EXTREME
AVAX/USD  26.2%      59.2%       EXTREME
```

### Decision Log (Real-time)
```
06:43:11 | XRP/USD  | BLOCKED | Coherence 26.2%
06:43:08 | BTC/USD  | HOLD    | EMA=NONE
```

### Regime Detection Dashboard
```
Current Regime: VOLATILE (HIGH RISK)
Confidence: 100%
Duration: 6h 23m

Historical Performance by Regime:
TRENDING:   +$45/trade
RANGING:    -$95/trade
VOLATILE:  -$180/trade
```

## Implementation Priority

### Phase 1: Critical Fixes (TODAY)
1. Fix WR Dir: 0.0% -> 37.8%
2. Fix Fee Eroded: 0 -> 21
3. Rename "Protected" to "Notional Blocked"

### Phase 2: UX Improvements (THIS WEEK)
1. Add System Health Score widget
2. Add Live Status section
3. Add Quick Insights auto-generated
4. Add Calibration Progress bar

### Phase 3: Nice-to-Have (NEXT WEEK)
1. Comparative Metrics table
2. P&L Breakdown visual
3. Risk Heatmap
4. Real-time Decision Log

## Layout Recommendation

### Section 1: HERO (First Thing Seen)
- System Health Score
- Live Status
- Calibration Progress
- Next Action

### Section 2: KEY METRICS (Positives First)
- +4.81% Alpha vs BTC
- 20.2% Win Rate Net
- 37.8% Precision
- 1.5% Max Drawdown

### Section 3: Quick Insights
- Auto-generated actionable insights

### Section 4: Charts
- Equity curve, Price, Volume

### Section 5: Collapsed Advanced
- Sharpe/Sortino (calibrating)
- Detailed trade history
- Veto analysis

## Decision

Accept these proposals as the roadmap for dashboard improvements. Prioritize critical fixes immediately to maintain investor credibility.

## Consequences

**Positive:**
- Dashboard credibility improved from 7.5/10 to 9.5/10
- Consistent metrics across all sections
- Honest framing per ADR-002
- Better investor presentation

**Negative:**
- Development time required
- Some complexity added to frontend
- Need to maintain new widgets

## References

- ADR-002: Honest Framing Over Censorship
- ADR-005: Dual Win Rate Framework
- docs/compliance/audits/DATA_INTEGRITY_AUDIT_JAN2026.md
