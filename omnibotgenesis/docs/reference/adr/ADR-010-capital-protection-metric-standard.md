# ADR-010: Capital Protection Metric Standard

**Status**: Accepted  
**Date**: 2026-01-15  
**Author**: OMNIX Team  
**Relates To**: ADR-008 (Opportunity Tracker)

## Context

Multiple dashboard widgets display capital protection metrics using inconsistent terminology:
- "Capital Protected" (notional value)
- "$1.2B Protected" (raw blocked amounts)
- "Loss Avoided" (realistic estimates)

This inconsistency confuses investors who see dramatically different numbers ($1.2B vs $267K) representing the same concept.

## Problem

1. **Investor Confusion**: Seeing "$1.2B Protected" and "$267K Est. Loss Avoided" on the same dashboard creates credibility issues
2. **Misleading Metrics**: Notional blocked values suggest unrealistic protection amounts
3. **Terminology Inconsistency**: Different widgets use different labels for similar concepts

## Decision

Standardize all capital protection displays using a two-tier metric system:

### Primary Metric: Est. Loss Avoided
- **Label**: "Est. Loss Avoided*" 
- **Calculation**: `Notional × 0.6%` (conservative avg adverse move)
- **Purpose**: Realistic estimate of potential losses prevented
- **Display**: Emphasized, larger font, green color

### Secondary Metric: Notional Blocked
- **Label**: "Notional Blocked"
- **Calculation**: Sum of blocked trade position sizes
- **Purpose**: Raw data for transparency
- **Display**: De-emphasized, smaller font, gray color

### Required Elements
1. **Tooltip/Help Text**: "Based on ~0.6% avg adverse move × position size"
2. **Asterisk**: Primary metric must include "*" indicating methodology
3. **Consistent Terminology**: Never use "Protected" alone without context

## Methodology Rationale

The 0.6% multiplier is derived from:
- Average adverse price movement before stop-loss would trigger
- Conservative lower bound (actual losses could be higher)
- Same methodology used for both "Missed Opportunities" and "Losses Avoided" ensuring apples-to-apples comparison

## Data Types Distinction

The system has two types of capital protection data:

### 1. Quarantined Assets (Actual Losses)
- **Source**: `quarantine.total_loss_avoided`
- **Nature**: Real P&L losses from trades before assets were blocked
- **Display**: "Loss Avoided" (no asterisk, no estimation)
- **Applies to**: Streamlit Quarantine tab

### 2. Dynamic Veto Blocking (Estimated Losses)
- **Source**: `blocked_capital` from trading_veto_log
- **Nature**: Notional position sizes of blocked trades
- **Display**: "Est. Loss Avoided*" = Notional × 0.6%
- **Applies to**: Flask dashboard widgets (quarantine.js, learninginsights.js)

## Affected Components

| Component | File | Status |
|-----------|------|--------|
| Quarantine Widget | `omnix_dashboard/static/js/components/quarantine.js` | ✅ Updated |
| Learning Insights | `omnix_dashboard/static/js/components/learninginsights.js` | ✅ Updated |
| Regime Detection | `omnix_dashboard/static/js/components/regimedetection.js` | ✅ Updated |
| Streamlit Dashboard | `omnix_dashboard/streamlit_app.py` | ✅ Updated (uses actual loss, not estimate) |
| Risk Guardian Widget | `omnix_dashboard/static/js/components/riskguardian.js` | ✅ No changes needed |

## Implementation

### JavaScript Example
```javascript
// Primary metric
<span style="color: var(--accent-green);">${formatCapital(estLossAvoided)}</span>
<span>Est. Loss Avoided*</span>

// Secondary metric  
<span style="color: #6b7280; font-size: 0.85em;">${formatCapital(notionalBlocked)}</span>
<span>Notional Blocked</span>

// Tooltip
title="Est. based on ~0.6% avg adverse move × position size"
```

### Streamlit Example
```python
est_loss_avoided = notional_blocked * 0.006
st.metric(
    "Est. Loss Avoided*",
    f"${est_loss_avoided:,.2f}",
    delta=f"Notional: ${notional_blocked:,.0f}",
    help="*Based on ~0.6% avg adverse move × position size"
)
```

## Consequences

### Positive
- Consistent investor experience across all dashboard views
- Credible metrics that can be defended in due diligence
- Transparent methodology shown to users

### Negative
- Numbers appear smaller (which is honest but less impressive)
- Requires updating multiple components

## Related Documents
- ADR-008: Opportunity Tracker (uses same methodology for Missed vs Avoided)
- ARCHITECTURE.md: Dashboard Features section

## Compliance
This ADR supports the "Honest Framing" principle from ADR-002 and ensures investor-ready metrics.
