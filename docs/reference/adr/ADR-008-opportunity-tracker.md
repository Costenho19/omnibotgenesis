# ADR-008: Opportunity Tracker (Day 30 Review Framework)

**Date:** January 14, 2026  
**Status:** Adopted  
**Decision Makers:** Harold (Founder), OMNIX Agent  
**Context:** Data-driven validation of threshold calibration without immediate changes

## Problem Statement

OMNIX ADR-007 implemented a conservative 5-point threshold reduction. The system now observes scenarios where:

1. **BTC has near-optimal conditions** but doesn't trade:
   - Coherence: 54% (MODERATE) ✅
   - Regime: RANGING (28.7% vol) ✅
   - MC Win Rate: 49.8% ⚠️
   - Non-Markovian: 85% BUY ✅
   - Black Swan: MEDIUM ✅
   - **EMA: NONE @ 31.7%** ❌ (threshold ~40%)

2. **Some assets are consistently blocked** (correctly):
   - AVAX: Coherence 26-33%, VOLATILE 61%, HIGH Black Swan
   - XRP: MC declining from 49.8% → 48.7%

### Key Question

**Are we missing profitable opportunities, or is the system correctly protecting capital?**

We cannot answer this without 30 days of tracked data.

## Decision

Create an **Opportunity Tracker** framework to document and validate potential threshold adjustments **without changing any thresholds now**.

### Two-Sided Accounting

| Category | Description | Data Source |
|----------|-------------|-------------|
| **Missed Opportunities** | Trades blocked with good conditions | Shadow Portfolio + price follow-up |
| **Losses Avoided** | Trades correctly blocked | Shadow Portfolio + simulated P&L |
| **Net Opportunity** | Missed - Avoided | Calculated daily |

### Metrics to Track

```python
opportunity_tracker_metrics = {
    "missed_opportunities": {
        "description": "Trades blocked when conditions were favorable",
        "criteria": {
            "coherence": ">= 50%",
            "regime": "RANGING",
            "black_swan": "<= MEDIUM",
            "ema_confidence": ">= 30% but < 40% (current threshold)"
        },
        "follow_up": "Track BTC price 24h after block"
    },
    "losses_avoided": {
        "description": "Trades correctly blocked",
        "criteria": {
            "coherence": "< 30%",
            "regime": "VOLATILE",
            "black_swan": "HIGH or EXTREME",
            "mc_win_rate": "< 48%"
        },
        "simulation": "Calculate hypothetical loss if executed"
    },
    "net_opportunity": {
        "description": "Daily balance of missed vs avoided",
        "calculation": "sum(missed_pnl) - sum(avoided_loss)",
        "interpretation": {
            "positive": "Thresholds may be too strict",
            "negative": "Thresholds are correctly calibrated",
            "neutral": "System is balanced"
        }
    }
}
```

### Day 30 Review Decision Criteria

```python
day_30_decision_criteria = {
    "test_lower_threshold": {
        "conditions": [
            "missed_opportunities > 20",
            "estimated_missed_profit > $3,000",
            "estimated_avoided_loss > $5,000",  # Still protecting well
            "current_win_rate > 30%",
            "max_drawdown < 3%"
        ],
        "action": "Test EMA threshold 40% → 35% with $500 real capital"
    },
    "keep_conservative": {
        "conditions": [
            "missed_opportunities < 10",
            "OR estimated_missed_profit < $1,000",
            "OR avoided_losses significantly exceed missed opportunities"
        ],
        "action": "Maintain current thresholds, continue monitoring"
    },
    "tighten_thresholds": {
        "conditions": [
            "net_opportunity consistently negative",
            "system taking bad trades",
            "win_rate declining"
        ],
        "action": "Increase thresholds (reverse of ADR-007)"
    }
}
```

## Implementation

### FEAT-011 Evolution: Learning Engine → Opportunity Tracker

The existing `/api/learning/insights` endpoint will be enhanced:

| Component | Current | Enhanced |
|-----------|---------|----------|
| Veto effectiveness | ✅ | ✅ |
| Calibration recommendations | ✅ | ✅ (30-day review only) |
| **Missed opportunities** | ❌ | ✅ NEW |
| **Losses avoided** | ❌ | ✅ NEW |
| **Net opportunity** | ❌ | ✅ NEW |
| **Day 30 summary** | ❌ | ✅ NEW |

### Data Source

**Primary:** `shadow_trade_events` table (48K+ events)

```sql
-- Missed Opportunity Example (BTC with good conditions)
SELECT COUNT(*) as missed_count,
       AVG(estimated_position) as avg_position,
       AVG(CASE WHEN price_24h_later > entry_price THEN 1 ELSE 0 END) as would_have_won
FROM shadow_trade_events
WHERE veto_type = 'COHERENCE_GATE'
  AND coherence_score >= 50
  AND regime = 'RANGING'
  AND black_swan_severity IN ('LOW', 'MEDIUM')
  AND ema_score >= 30 AND ema_score < 40
  AND created_at > NOW() - INTERVAL '30 days';
```

### Dashboard Widget Update

FEAT-011 widget will show:

```
🧠 OPPORTUNITY TRACKER (Day X/30)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Missed Opportunities: 12
   Est. Profit if executed: +$1,850
   Avg conditions: Coh 52%, RANGING

✅ Losses Avoided: 8
   Est. Loss prevented: -$2,400
   Avg conditions: Coh 28%, VOLATILE

📈 Net Opportunity: -$550 (Conservative ✅)

🎯 Day 30 Status: TRACKING
   Review Date: Feb 13, 2026
   Current Recommendation: KEEP_CONSERVATIVE
```

## Rationale

1. **Data-driven decisions:** No threshold changes without 30 days of evidence
2. **Two-sided accounting:** Captures both upside (missed) and downside (avoided)
3. **Clear criteria:** Objective decision rules for Day 30 review
4. **Investor transparency:** Shows system is self-evaluating honestly
5. **Aligned with ADR-002:** Honest framing, not hiding opportunities or risks

## Guardrails

1. **NO threshold changes** until Day 30 review
2. **Automated tracking** via existing Shadow Portfolio infrastructure
3. **Daily aggregation** for trend analysis
4. **Clear documentation** of what constitutes "good conditions"

## Expected Outcome

After 30 days, we will have:

| Deliverable | Purpose |
|-------------|---------|
| Missed opportunity count | Quantify blocked trades with good conditions |
| Estimated missed P&L | Financial impact of conservative approach |
| Loss avoidance count | Quantify correctly blocked trades |
| Estimated avoided loss | Financial impact of protection |
| Net recommendation | Data-driven threshold decision |

## Timeline

| Day | Action |
|-----|--------|
| Day 0 (Jan 14) | ADR-008 adopted, tracking begins |
| Day 1-29 | Accumulate data, no changes |
| Day 30 (Feb 13) | Review data, make threshold decision |
| Day 31+ | Implement decision (if any) |

## Alternatives Considered

1. **Immediate threshold change:** Rejected - No data to support specific values
2. **No tracking:** Rejected - Would make decisions based on assumptions
3. **Complex ML optimization:** Deferred - Overkill for current scale

## References

- ADR-007: Coherence Threshold Calibration (triggered this analysis)
- ADR-002: Honest Framing Over Censorship
- FEAT-011: Learning Engine Insights (base implementation)
- Shadow Portfolio: `/api/learning/insights`, `shadow_trade_events` table
