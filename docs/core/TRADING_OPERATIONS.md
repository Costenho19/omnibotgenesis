# OMNIX V6.5.4c Trading Operations

**Version:** 6.5.4c INSTITUTIONAL+ PREMIUM  
**Last Updated:** December 10, 2025  
**Active Profile:** PRODUCTION_STABLE

---

## Table of Contents

1. [Trading Flow Architecture](#1-trading-flow-architecture)
2. [Trading Profiles](#2-trading-profiles)
3. [ARES Strategies (Active)](#3-ares-strategies)
4. [Risk Management](#4-risk-management)
5. [Operational Procedures](#5-operational-procedures)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Trading Flow Architecture

### 1.1 Signal Generation Pipeline

```
Market Data → Strategy Analysis → Coherence Validation → Risk Check → Execution

Step 1: Market Data Collection
├── Kraken API: Real-time prices, OHLCV
├── On-Chain: Whale movements, DeFi metrics
└── Sentiment: Fear & Greed Index, news

Step 2: Strategy Analysis (10 Core Strategies)
├── QuantumMomentum: Primary directional signal
├── Monte Carlo: Probability validation (10K iterations)
├── HMM Regime: Market state (TRENDING/RANGING/VOLATILE)
├── Kalman Filter: Signal noise reduction
├── Black Swan: Tail risk detection (VETO power)
├── Kelly Criterion: Optimal position sizing
├── Sentiment Analysis: Market mood
├── Non-Markovian Kernel: Temporal patterns
├── Coherence Engine: Consensus gate
└── Risk Guardian: Protection layer

Step 3: Coherence Validation (6-Tier Veto System)
├── Tier 1: Contradiction check (5+ vs 3+)
├── Tier 2: Black Swan risk level
├── Tier 3: Coherence score threshold
├── Tier 4: Confidence threshold (60%+)
├── Tier 5: Monte Carlo win rate (50%+)
└── Tier 6: Position limit check

Step 4: Risk Guardian Review
├── Overtrading check (max 50/day)
├── Drawdown check (max 15%)
├── Revenge trading detection
├── Position concentration (max 15% per asset)
└── Hard cap validation ($20K max trade)

Step 5: Execution
├── CAES position sizing
├── Order placement (market/limit)
├── TP/SL setting (volatility-based)
└── Decision logging (audit trail)
```

### 1.2 Trade Lifecycle

| Phase | Description | Logged Events |
|-------|-------------|---------------|
| Candidate | Strategy generates signal | TRADE_CANDIDATE |
| Validation | Coherence Engine evaluates | COHERENCE_RESULT |
| Risk Check | Risk Guardian reviews | RISK_CHECK |
| Execution | Trade placed | TRADE_EXECUTED |
| Monitoring | TP/SL tracked | POSITION_UPDATE |
| Close | Position closed | TRADE_CLOSED |

---

## 2. Trading Profiles

### 2.1 Active Profile: PRODUCTION_STABLE V6.5.4c

**Source of Truth:** `omnix_core/config/trading_profiles.py`

| Parameter | Value | Description |
|-----------|-------|-------------|
| `min_trade_size` | $100 | Minimum trade size |
| `max_trade_size` | $3,000 | Maximum trade size |
| `base_trade_size` | $500 | Default trade size |
| `max_daily_trades` | 10 | Daily trade limit |
| `max_daily_loss_pct` | 15% | Drawdown halt trigger |
| `coherence_threshold` | 55% | Minimum coherence score |
| `min_signal_strength` | 60% | Signal threshold |
| `sl_pct_high_vol` | 2.5% | Stop loss (high volatility) |
| `sl_pct_normal_vol` | 1.5% | Stop loss (normal volatility) |
| `tp_pct_high_vol` | 4.5% | Take profit (high volatility) |
| `tp_pct_normal_vol` | 3.0% | Take profit (normal volatility) |

### 2.2 V6.5.4c Changes (December 10, 2025)

| Change | From | To | Reason |
|--------|------|-----|--------|
| Drawdown limit | 10% | 15% | Allow trading during recovery |
| ARES V1 | Disabled | Active (70%) | Track record generation |
| ARES V2 | Disabled | Active (75%) | Track record generation |
| ARES daily limit | N/A | 3 trades | Controlled exposure |

### 2.3 Available Profiles

| Profile | Purpose | Aggressiveness |
|---------|---------|----------------|
| **PRODUCTION_STABLE** | Track record generation (ACTIVE) | Moderate |
| INSTITUTIONAL | Real money, maximum protection | Conservative |
| PAPER_AGGRESSIVE | Rapid testing, more trades | Aggressive |
| BALANCED | Middle ground | Moderate |
| PAPER_OPTIMIZED | Investor demos, win rate focus | Selective |
| WIN_RATE_OPTIMIZED | Maximum win rate | Very Selective |

### 2.4 Profile Selection

```bash
# Railway environment variable
TRADING_PROFILE=PRODUCTION_STABLE
```

**Note:** Profile changes take effect after bot restart.

---

## 3. ARES Strategies

### 3.1 ARES V1 (Swing Trading)

| Parameter | Value |
|-----------|-------|
| Timeframe | 4h - 1d |
| Min Confidence | 70% |
| Holding Period | 1-7 days |
| Target R:R | 1:2.5 |
| Lateral Markets | Allowed |

**Entry Conditions:**
- Trend alignment on 4h and 1d
- Volume confirmation
- Non-Markovian Kernel confidence ≥ 70%
- Coherence score ≥ 55%

### 3.2 ARES V2 (Scalping)

| Parameter | Value |
|-----------|-------|
| Timeframe | 15m - 1h |
| Min Confidence | 75% |
| Holding Period | 1h - 8h |
| Target R:R | 1:1.5 |
| Lateral Markets | Allowed |

**Entry Conditions:**
- Quick momentum setup
- Tight stop loss
- Higher confidence threshold
- Fast exit on target

### 3.3 Combined Limits

| Limit | Value | Scope |
|-------|-------|-------|
| Max trades/day | 3 | Shared between V1 + V2 |
| Max concurrent | 2 | ARES positions |
| Separate tracking | Yes | From production metrics |

---

## 4. Risk Management

### 4.1 Risk Guardian V5.4 Protections

| Protection | Threshold | Action |
|------------|-----------|--------|
| Daily drawdown | 15% | Halt all trading |
| Overtrading | 50 trades/day | Block new trades |
| Revenge trading | 3 consecutive losses | 30-min cooldown |
| Position concentration | 15% per asset | Block additional buys |
| Trade size cap | $20,000 | Hard reject |

### 4.2 Stop Loss / Take Profit by Volatility

| Pair Type | Examples | SL | TP | R:R |
|-----------|----------|-----|-----|-----|
| High Volatility | DOT, AVAX, SOL, LINK | 2.5% | 4.5% | 1:1.8 |
| Normal Volatility | BTC, ETH, XRP, LTC | 1.5% | 3.0% | 1:2.0 |

### 4.3 Circuit Breakers

| Trigger | Action | Reset |
|---------|--------|-------|
| 5% daily loss | Reduce sizes 50% | Next trading day |
| 8% daily loss | Halt all trades | Manual review |
| 3 consecutive losses | 30-min cooldown | Automatic |
| Regime change | 15-min pause | After stability |

### 4.4 Emergency Stop

**Code Location:** `auto_trading_bot.py` → `_check_emergency_stop()`

```python
if current_drawdown > max_daily_loss_pct:
    emergency_stop = True  # Blocks ALL new trades
```

---

## 5. Operational Procedures

### 5.1 Daily Checklist

| Time | Task | Tool |
|------|------|------|
| 00:00 UTC | Check overnight trades | Dashboard |
| 06:00 UTC | Review drawdown status | `/balance` |
| 12:00 UTC | Midday performance check | Dashboard |
| 18:00 UTC | Pre-close review | `/status` |

### 5.2 Monitoring Commands (Telegram)

| Command | Purpose |
|---------|---------|
| `/autotrading status` | Bot status and metrics |
| `/balance` | Current balances |
| `/trades` | Recent trade list |
| `/performance` | Win rate and P&L |
| `/risk` | Risk Guardian status |

### 5.3 Dashboard Access

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| Flask API | `:5000/api/metrics` | Raw data |
| Streamlit | `:8080` | Visual charts |
| Health | `:5000/api/health` | System status |

### 5.4 Railway Deployment

```
GitHub (main) → Auto-deploy → Railway

DO NOT run bot on Replit and Railway simultaneously.
Telegram allows only ONE active connection per token.
```

---

## 6. Troubleshooting

### 6.1 No Trades Executing

| Check | Solution |
|-------|----------|
| Profile verification | `echo $TRADING_PROFILE` |
| ARES activation | Verify V6.5.4c config |
| Drawdown status | Check if < 15% |
| Market conditions | May be waiting for signals |
| Coherence thresholds | May be too strict |

### 6.2 Win Rate Below 55%

| Cause | Action |
|-------|--------|
| Adverse market | Wait for regime change |
| Strategy calibration | Adaptive engine auto-adjusts |
| Profile mismatch | Consider PAPER_OPTIMIZED |

### 6.3 Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| `COHERENCE_BLOCK` | Strategies disagree | Normal - wait for alignment |
| `RISK_GUARDIAN_VETO` | Risk limit triggered | Check drawdown, cooldown |
| `POSITION_LIMIT_REACHED` | Max positions open | Wait for closes |
| `EMERGENCY_STOP` | Drawdown exceeded | Manual review needed |

### 6.4 Log Locations

| Log Type | Location |
|----------|----------|
| Trading | Railway logs |
| Decisions | `decision_logs` table |
| Risk events | `risk_guardian_events` table |
| Dashboard | Flask console |

---

## Appendix: Track Record Progress

| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| Trades | 27 | 500+ | 8-9 weeks |
| Win Rate | TBD | 55%+ | Ongoing |
| Active Days | ~5 | 30-60 | Ongoing |
| ARES Trades | TBD | Tracked separately | Ongoing |

**Goal:** Investor-grade track record for $1M seed funding at $11.5M pre-money valuation.
