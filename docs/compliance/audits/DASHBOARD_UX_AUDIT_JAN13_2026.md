# Dashboard UX Audit - January 13, 2026

**Audit Type:** External Analysis Review  
**Auditor:** AI Analysis + Harold Review  
**Date:** January 13, 2026  
**Dashboard Version:** V6.5.4d INSTITUTIONAL+

## Executive Summary

External analysis identified 3 critical bugs and 12 improvement opportunities. Current dashboard score: 7.5/10. Target after fixes: 9.5/10.

## Critical Findings

### CRITICAL-001: Win Rate Inconsistency

**Severity:** Critical  
**Impact:** Investor credibility

**Finding:**
- Header displays: `37.8% Precision` (correct)
- Trade History displays: `WR Dir: 0.0%` (WRONG)

**Root Cause:** Trade History widget calculates metrics locally with different logic than the header API.

**Recommendation:** Unify all win rate calculations through `omnix_dashboard/utils/queries.py` using ADR-005 logic.

### CRITICAL-002: Misleading "Protected" Metric

**Severity:** Critical  
**Impact:** Investor trust

**Finding:**
```
$31.4M Total Protected
```
This implies $31.4M was at risk when actual capital is $1M.

**Root Cause:** Displaying notional blocked value without context.

**Recommendation:** Rename to "Notional Blocked" and add context:
- Number of trades prevented
- Average position size blocked

### CRITICAL-003: Negative Metrics Too Prominent

**Severity:** High  
**Impact:** First impression

**Finding:**
```
-5.82 Sharpe
-6.03 Sortino
0.13 Profit Factor
```

**Root Cause:** Raw metrics displayed without calibration phase context.

**Recommendation:** Add "CALIBRATION PHASE" label and target values.

## UX Findings

### UX-001: Missing System Health Indicator

**Severity:** Medium  
**Impact:** User confidence

**Finding:** No at-a-glance indicator of overall system health.

**Recommendation:** Add System Health Score widget (0-100).

### UX-002: No Live Status Section

**Severity:** Medium  
**Impact:** User understanding

**Finding:** Users can't see what the system is doing RIGHT NOW.

**Recommendation:** Add "Live Status" section showing current action and reasoning.

### UX-003: Missing Calibration Progress

**Severity:** Medium  
**Impact:** Expectation management

**Finding:** No indication of progress toward optimization.

**Recommendation:** Add calibration progress bar with phases.

### UX-004: No Actionable Insights

**Severity:** Medium  
**Impact:** Decision support

**Finding:** Users must manually analyze data to extract insights.

**Recommendation:** Add auto-generated "Quick Insights" section.

## Positive Findings

1. Real-time data updates working correctly (14/14 widgets)
2. Latency monitoring accurate (~128ms)
3. Fear & Greed Index integration working
4. Candlestick chart functional
5. Dual win rate framework (ADR-005) correctly implemented in header

## Action Items

| Priority | Action | Owner | ETA |
|----------|--------|-------|-----|
| P0 | Fix WR Dir 0.0% bug | Dev | Today |
| P0 | Fix Fee Eroded 0 bug | Dev | Today |
| P0 | Rename "Protected" | Dev | Today |
| P1 | Add System Health Score | Dev | This Week |
| P1 | Add Live Status section | Dev | This Week |
| P1 | Add Quick Insights | Dev | This Week |

## References

- ADR-002: Honest Framing Over Censorship
- ADR-005: Dual Win Rate Framework
- ADR-006: Dashboard Improvement Proposals (new)
- docs/DASHBOARD_IMPROVEMENT_BACKLOG.md (new)
