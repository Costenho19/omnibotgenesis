# OMNIX Trading Profiles - V6.5.4c Reference

> **Version Control**: Current system version is defined in `omnix_config/settings.py`.

**Document Version:** 1.0  
**Created:** December 10, 2025  
**Status:** CURRENT - Production Reference

---

## Overview

Trading profiles control risk parameters, strategy activation, and trading behavior. Each profile is designed for a specific use case.

**Configuration File:** `omnix_core/config/trading_profiles.py`

---

## Active Profile: PRODUCTION_STABLE (V6.5.4c)

This is the current production profile for track record generation.

### Core Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `name` | PRODUCTION_STABLE | Profile identifier |
| `description` | V6.5.4c PRODUCTION STABLE | Proven strategies + ARES experimental |
| `is_paper_mode` | True | Paper trading only |
| `max_position_size_pct` | 2.5% | Max single position |
| `max_open_positions` | 8 | Concurrent positions limit |
| `base_trade_size` | $25,000 | Default trade size |

### Risk Limits (V6.5.4c)

| Parameter | Value | Notes |
|-----------|-------|-------|
| `max_daily_drawdown_pct` | **15%** | Increased from 10% (Dec 10) |
| `max_daily_loss_pct` | 2% | Daily loss circuit breaker |
| `max_weekly_loss_pct` | 5% | Weekly loss limit |
| `risk_guardian_size_reduction` | 12% | Reduce position at this drawdown |

### ARES Configuration (V6.5.4c - ACTIVE)

| Parameter | Value | Description |
|-----------|-------|-------------|
| `ares_enabled` | True | ARES system active |
| `ares_v1_enabled` | True | Swing trading (15m-4h) |
| `ares_v2_enabled` | True | Scalping (1m-5m) |
| `ares_v1_min_confidence` | 70% | Minimum for V1 execution |
| `ares_v2_min_confidence` | 75% | Minimum for V2 execution |
| `ares_max_daily_trades` | 3 | Shared limit V1+V2 |
| `ares_require_trend` | False | Allows lateral markets |
| `ares_stop_loss` | 1.2% (normal), 1.8% (volatile) | Volatility-based |
| `ares_take_profit` | 3.5% (normal), 5.0% (volatile) | Volatility-based |

> **Note:** ARES remains classified as `strategies_experimental` even when active. Production metrics only include the 10 core strategies.

### Production Strategies (10 Active)

1. QuantumMomentum
2. Monte Carlo Simulation
3. Kelly Criterion
4. Black Swan Detection
5. HMM Regime Detection
6. Kalman Filter
7. Non-Markovian Kernel
8. Coherence Engine
9. Risk Guardian
10. Sentiment Analysis

### Coherence Engine Settings

| Parameter | Value |
|-----------|-------|
| `coherence_veto_critical` | 25% |
| `score_momentum` | 15 |
| `score_trend` | 8 |
| `score_reversal` | 4 |

---

## Other Profiles

### INSTITUTIONAL

Conservative profile for real money trading.

| Parameter | Value |
|-----------|-------|
| `is_paper_mode` | False |
| `max_daily_drawdown_pct` | 10% |
| `ares_enabled` | False |
| `max_position_size_pct` | 2% |

### PAPER_AGGRESSIVE

Aggressive testing profile.

| Parameter | Value |
|-----------|-------|
| `is_paper_mode` | True |
| `max_daily_drawdown_pct` | 15% |
| `ares_enabled` | True |
| `buy_bias_multiplier` | 1.3x |

### BALANCED

Mixed conservative/aggressive profile.

| Parameter | Value |
|-----------|-------|
| `is_paper_mode` | True |
| `max_daily_drawdown_pct` | 10% |
| `ares_enabled` | False |

---

## Configuration Priority

1. **Environment Variable** `TRADING_PROFILE` (Railway/production)
2. **Code Default** in `trading_profiles.py`

**Railway Setting:** `TRADING_PROFILE=PRODUCTION_STABLE`

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| Dec 10, 2025 | 6.5.4c | ARES V1+V2 activated, drawdown 10%→15%, require_trend=False |
| Dec 9, 2025 | 6.5.4b | Hexagonal ports Phase 1 completed |
| Dec 8, 2025 | 6.5.4a | AI truthfulness fix with PaperTradingRepository |
