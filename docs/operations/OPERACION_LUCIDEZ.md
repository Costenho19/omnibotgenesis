# Operación Lucidez - Segmented Expectancy Analysis

**Date**: January 1, 2026
**Internal Build Reference**: 6.5.4d
**Status**: IMPLEMENTED

## Overview

"Operación Lucidez" transforms the trading system from one that "tries to win" to one that "knows WHERE it wins" through expectancy segmentation by market regime and signal coherence.

## Core Concept

Instead of analyzing overall win rate (which hides regime-specific performance), we segment trades by:

1. **HMM Regime**: BULLISH, BEARISH, RANGING, or UNKNOWN
2. **Coherence Bucket**: LOW (<40), MED (40-70), HIGH (70+)

This creates a matrix showing which combinations have positive expectancy (edge) vs negative expectancy (should be filtered out).

## Expectancy Formula

```
E = (Win% × AvgWin) - (Loss% × |AvgLoss|)
```

- **E > 0**: Positive edge - system is profitable in this segment
- **E < 0**: Negative edge - system loses money in this segment
- **E = 0**: Breakeven - no statistical edge

## Implementation

### Database Schema (Migration V005)

Added columns to `paper_trading_trades`:

| Column | Type | Purpose |
|--------|------|---------|
| `hmm_regime` | VARCHAR(20) | HMM regime at trade entry (BULLISH/BEARISH/RANGING) |
| `coherence_score` | NUMERIC(5,2) | Coherence score at trade entry (0-100) |
| `ema_regime_signal` | VARCHAR(10) | EMA signal that triggered the trade (BUY/SELL) |
| `strategy_confidence` | NUMERIC(5,2) | Overall strategy confidence (0-100) |

Indexes added for efficient querying:
- `idx_paper_trades_hmm_regime`
- `idx_paper_trades_coherence_score`

### Telemetry Capture Flow

```
AutoTradingBot.perform_analysis()
    ↓
Extract hmm_regime from analysis['hmm_regime']
Extract coherence_score from analysis['coherence_report']
    ↓
PaperTradingManager.execute_paper_trade(
    ...,
    hmm_regime=telemetry_hmm_regime,
    coherence_score=telemetry_coherence_score,
    ema_regime_signal=action,
    strategy_confidence=telemetry_confidence
)
    ↓
_open_position_v2() stores in paper_trading_trades
```

### API Endpoint

**GET /api/metrics/expectancy**

Returns:
```json
{
  "success": true,
  "days_analyzed": 90,
  "total_trades": 112,
  "segment_count": 8,
  "segments": [
    {
      "regime": "BULLISH",
      "coherence_bucket": "HIGH (70+)",
      "trade_count": 25,
      "wins": 18,
      "losses": 7,
      "win_rate": 72.0,
      "avg_win": 145.50,
      "avg_loss": 62.30,
      "expectancy": 87.29,
      "total_pnl": 2182.25,
      "is_profitable": true
    }
  ],
  "best_segment": "BULLISH + HIGH (70+)",
  "best_expectancy": 87.29,
  "overall_expectancy": 12.45,
  "profitable_segment_count": 3,
  "recommendation": "Focus on BULLISH + HIGH (70+)"
}
```

### Streamlit Dashboard Widget

Navigate to **Expectancy** in the sidebar to see:
- Summary metrics (total trades, overall expectancy, best segment)
- Segment table with all metrics
- Heatmap showing profitable vs losing segments
- Investor explanation

## Strategic Value

### For Investors
- Demonstrates quantitative understanding of WHERE the system has edge
- Shows systematic approach to performance optimization
- Provides falsifiable metrics (E per segment with 5+ trade minimum)

### For System Optimization
- Identifies regimes to AVOID (negative E)
- Identifies regimes to FOCUS (positive E)
- Enables regime-aware filtering to concentrate trading in profitable conditions

## Files Modified

| File | Changes |
|------|---------|
| `omnix_services/database_service/migrations/versions.py` | V005 migration adding telemetry columns |
| `omnix_core/bot/paper_trading.py` | execute_paper_trade() and _open_position_v2() accept telemetry |
| `omnix_core/bot/auto_trading_bot.py` | Extract and pass telemetry to paper trading |
| `omnix_dashboard/utils/queries.py` | get_segmented_expectancy() function |
| `omnix_dashboard/blueprints/core.py` | /api/metrics/expectancy endpoint |
| `omnix_dashboard/api_client.py` | get_segmented_expectancy() method |
| `omnix_dashboard/streamlit_app.py` | render_expectancy() widget |

## Future Enhancements

1. **Regime-Aware Trade Filtering**: Automatically skip trades in negative-E segments
2. **Dynamic Sizing**: Increase position size in high-E segments
3. **Real-Time E Monitoring**: Track E changes over time to detect edge decay
4. **Backtest Integration**: Calculate historical E for strategy optimization

## Related Documentation

- [MIGRATION_STATUS.md](../MIGRATION_STATUS.md) - V7 migration status
- [REAL_SYSTEM_STATUS.md](../REAL_SYSTEM_STATUS.md) - System capabilities
- [TECHNICAL_DEBT.md](../current/TECHNICAL_DEBT.md) - Known issues and improvements
