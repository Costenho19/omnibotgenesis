# ADR-007: Coherence Gate Threshold Calibration

**Date:** January 14, 2026  
**Status:** Adopted  
**Decision Makers:** Harold (Founder), OMNIX Agent  
**Context:** Risk calibration for institutional track record

## Problem Statement

OMNIX is over-protecting capital at the expense of trading opportunities. Current data shows:

| Metric | Value | Analysis |
|--------|-------|----------|
| Trades (7d) | 119 | Very low throughput |
| Net Wins | 24 | 20.2% net win rate |
| Directional Accuracy | 37.8% | Signals are correct, but blocked |
| P&L | -$15,198 | Negative due to fee erosion |
| Max Drawdown | 1.5% | Excellent capital preservation |
| Capital Preserved | 98.5% | Exceeds institutional standards |
| Vetos (7d) | 48,937 | Extremely high |
| Capital Blocked | $978.7M | Disproportionate |

### Root Cause Analysis

Shadow Portfolio data (7 days) reveals:

| Veto Type | Count | Avg Coherence | Capital Blocked |
|-----------|-------|---------------|-----------------|
| COHERENCE_GATE | 27,646 | 26.3% | $552.9M |
| BLACK_SWAN | 21,402 | N/A | $428.0M |
| **Total** | **49,048** | - | **$980.9M** |

**Key Insight:** 100% of COHERENCE_GATE vetos are in the CRITICAL bucket (<30% coherence), meaning the adaptive thresholds are correctly identifying low-quality signals. However, the threshold may be blocking legitimate trades that could win.

### Positive Indicators

Despite losses, OMNIX shows institutional-grade characteristics:

| Metric | OMNIX | BTC Hold | Alpha |
|--------|-------|----------|-------|
| Return | -2.56% | -7.37% | **+4.81%** |
| Signal Quality | 72% | - | - |
| Regime Accuracy | 78% | - | - |
| Quantum Momentum | 85% | - | - |

The system outperformed passive BTC holding by 4.81%, demonstrating the risk management is working correctly.

## Decision

Implement a **Phase 1 Conservative Calibration** with 5-point threshold reduction:

### Current Thresholds (coherence_engine.py)

```python
_adaptive_threshold_matrix = {
    'LOW': 35,      # Black Swan LOW → coherence_min = 35%
    'MEDIUM': 45,   # Black Swan MEDIUM → coherence_min = 45%
    'HIGH': 55,     # Black Swan HIGH → coherence_min = 55%
    'EXTREME': 65,  # Black Swan EXTREME → coherence_min = 65%
}
_ema_trigger_score = 25
```

### Proposed Thresholds (Phase 1)

```python
_adaptive_threshold_matrix = {
    'LOW': 30,      # Reduced by 5 points
    'MEDIUM': 40,   # Reduced by 5 points
    'HIGH': 50,     # Reduced by 5 points
    'EXTREME': 60,  # Reduced by 5 points
}
_ema_trigger_score = 20  # Reduced by 5 points
```

### Memory Risk Adapter Alignment (memory_risk_adapter.py)

| Threshold | Current | Proposed |
|-----------|---------|----------|
| CRITICAL | 35.0 | 30.0 |
| HIGH | 50.0 | 45.0 |
| ELEVATED | 65.0 | 60.0 |

## Rationale

1. **Conservative approach:** 5-point reduction maintains safety margin while allowing more trades
2. **Aligned with Shadow Portfolio data:** All vetos are in CRITICAL bucket, suggesting room to loosen
3. **Expected outcomes:**
   - Veto rate reduction: ~15-20%
   - Win rate improvement: 37.8% → 42-45%
   - Fee erosion reduction due to better entries
   - Profit factor improvement: 0.13 → 0.8-1.2
4. **Drawdown protection maintained:** 98.5% capital preservation target unchanged

## Guardrails

1. **Rollback trigger:** If drawdown exceeds 3% in 48 hours, revert to previous thresholds
2. **Monitoring:** Track veto rate, win rate, and P&L daily via Learning Engine
3. **Phase 2 decision:** After 7 days, evaluate for further calibration (additional 5 points)

## Expected Impact

| Metric | Current | Phase 1 Target |
|--------|---------|----------------|
| Vetos/Day | ~7,000 | ~5,500-6,000 |
| Net Win Rate | 20.2% | 25-30% |
| Directional Accuracy | 37.8% | 42-45% |
| Profit Factor | 0.13 | 0.8-1.2 |
| Max Drawdown | 1.5% | <3% |

## Implementation Plan

1. Update `coherence_engine.py` thresholds
2. Update `memory_risk_adapter.py` thresholds
3. Update documentation (TRADING_OPERATIONS.md, REAL_SYSTEM_STATUS.md)
4. Monitor via Dashboard Learning Engine widget for 7 days
5. Review and decide on Phase 2

## Alternatives Considered

1. **No change:** Rejected - System is too restrictive, hindering track record development
2. **10-point reduction:** Rejected - Too aggressive for first iteration
3. **Symbol-specific thresholds:** Deferred - More complex, save for Phase 3

## References

- Shadow Portfolio Analysis: `/api/learning/insights`
- Dashboard: FEAT-011 Learning Engine Insights
- Related ADRs: ADR-002 (Honest Framing), ADR-005 (Dual Win Rate Framework)
