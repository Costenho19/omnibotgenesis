# ADR-005: Dual Win Rate Framework

**Status:** IMPLEMENTED  
**Date:** January 12, 2026  
**Authors:** OMNIX Team  
**Supersedes:** N/A

## Context

During the trade investigation of January 11-12, 2026, we discovered a critical insight: the single win rate metric (20.17%) was technically correct but incomplete. Analysis revealed that 21 trades (17.6%) won in direction but lost money due to Kraken exchange fees.

This created a communication problem:
- The 20.17% win rate understated the system's predictive capability
- Investors seeing only this number might undervalue the technical sophistication
- But hiding the net result would violate our Honest Framing policy (ADR-002)

## Decision

Implement a **Dual Win Rate Framework** that shows both metrics across all interfaces:

| Metric | Calculation | Meaning |
|--------|-------------|---------|
| **Precisión (Directional)** | `profit_pct > 0` | System correctly predicted price direction |
| **Rentable (Net)** | `profit_loss > 0` | Trade was profitable after fees |
| **Fee-Eroded** | `profit_pct > 0 AND profit_loss < 0` | Won direction but lost to fees |

### Display Locations

1. **Dashboard Header:** Shows both metrics prominently (37.8% Precisión, 20.2% Rentable)
2. **Telegram Bot Status:** `_get_dual_win_rates()` method queries DB for both metrics
3. **AI Context Provider:** `real_data_provider.py` includes both in system prompt

### Technical Implementation

```python
# Query pattern used in all sources (consistency critical)
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as net_wins,
    SUM(CASE WHEN profit_pct > 0 THEN 1 ELSE 0 END) as dir_wins,
    SUM(CASE WHEN profit_pct > 0 AND profit_loss < 0 THEN 1 ELSE 0 END) as fee_eroded
FROM paper_trading_trades
WHERE status = 'closed'
```

**Critical:** All sources must use `profit_loss < 0` (not `<= 0`) for fee-eroded calculation.

## Rationale

1. **Transparency:** Aligns with ADR-002 Honest Framing - show all data, add context
2. **Technical Credibility:** 37.82% directional accuracy demonstrates AI/ML capability
3. **Financial Reality:** 20.17% net shows actual P&L impact
4. **Root Cause Visibility:** Fee-eroded count identifies the specific problem (position sizing)
5. **Actionable Insight:** Led directly to ADR-004 position sizing hotfix

## Consequences

### Positive
- Investors see complete picture with proper context
- System's predictive capability is properly represented
- Clear path to improvement (reduce position sizes to improve net WR)
- Consistency across all communication channels

### Negative
- Slightly more complex messaging than single metric
- Requires explanation of difference to non-technical audiences

### Neutral
- Dashboard header now shows two metrics instead of one
- All win rate queries must be updated to dual format

## Files Modified

| File | Change |
|------|--------|
| `omnix_dashboard/utils/queries.py` | Added dual win rate query functions |
| `omnix_core/bot/auto_trading_bot.py` | Added `_get_dual_win_rates()` method |
| `omnix_core/context/real_data_provider.py` | Updated context format with both metrics |
| `omnix_dashboard/templates/index.html` | Dashboard header shows both metrics |

## Validation

- 27 tests passed after implementation
- Dashboard displays 37.8% Precisión, 20.2% Rentable
- Telegram bot includes both metrics in status messages
- AI context includes both metrics for honest investor responses

## Related ADRs

- **ADR-002:** Honest Framing Over Censorship (this implements that principle)
- **ADR-003:** Official Positioning (metrics support "risk control" narrative)
- **ADR-004:** Position Sizing Hotfix (direct result of this analysis)
