# Session Log: January 29, 2026 - ECW Threshold Calibration

## Summary
Reduced ECW MC_WR_MIN threshold from 52% to 50% to allow more trades during Track Record validation phase.

## Problem Statement
After 14 days of Track Record (Jan 15-28, 2026):
- **Trades executed**: 0
- **Primary blocker**: ECW gate requiring MC_WR >= 52%
- **Observed MC_WR**: Typically 49-50% (edge marginal but below threshold)
- **Other signals**: Positive (Kernel 67%, CAES 1.27x, EMA SHORT 38-43%)

The system was operating in "ultra-conservative institutional mode" which prioritizes capital preservation over activity. While correct for large funds, this prevented track record validation.

## Solution

### Threshold Adjustment
| Parameter | Before | After |
|-----------|--------|-------|
| `mc_wr_min` | 52% | **50%** |
| `mc_er_min` | > 0% | > 0% (unchanged) |
| `consecutive_required` | 3 | 3 (unchanged) |

### ENV Configuration Added
All ECW parameters are now ENV-configurable:
- `ECW_MC_WR_MIN` (default: 50)
- `ECW_MC_ER_MIN` (default: 0)
- `ECW_CYCLES_REQUIRED` (default: 3)

### Rollback Procedure
```bash
# Railway: Set in Variables
ECW_MC_WR_MIN=52
# Restart service - no redeploy needed
```

## Guardrails Maintained
- Kelly max 2% / $20K cap (ADR-004)
- Only BTC/USD and XRP/USD allowed
- Black Swan ≤ MEDIUM required
- ER > 0% required
- 3 consecutive cycles confirmation

## Track Record Integrity
- Pre-v1.1 data (Jan 15-28): Unchanged, config epoch v1.0
- Post-v1.1 data (Jan 29+): Logged with `ecw_config_version: 1.1`
- No retroactive impact on historical decisions

## Files Modified
- `omnix_core/bot/auto_trading_bot.py`:
  - ECW config now ENV-controlled (lines 2956-2964)
  - Added `ecw_config_version` and `ecw_thresholds` to decision payload (lines 3077-3085)
  - Added startup logging for ECW thresholds (lines 126-131)
- `docs/reference/adr/ADR-019-edge-confirmation-window.md` - Added Revision v1.1
- `replit.md` - Updated ECW configuration section

## Success Criteria (Day 30 Review - Feb 13, 2026)
- At least 5-10 trades executed
- Win rate ≥ 45%
- No drawdown > 3%

## Architect Review
Validated by architect agent:
- Change is moderately safe with maintained guardrails
- ENV configuration enables immediate rollback
- Track record integrity preserved through config epochs
- Documentation updates ADR-019 with revision history
