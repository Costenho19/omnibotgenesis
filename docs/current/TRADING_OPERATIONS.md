# OMNIX V6.5.4e Trading Operations

**Version:** 6.5.4e INSTITUTIONAL+ PREMIUM  
**Last Updated:** January 14, 2026  
**Active Profile:** PRODUCTION_STABLE  
**Latest Change:** ADR-007 Coherence Threshold Calibration

---

## Table of Contents

1. [Trading Flow Architecture](#1-trading-flow-architecture)
2. [Trading Profiles](#2-trading-profiles)
3. [Risk Management](#3-risk-management)
4. [Operational Procedures](#4-operational-procedures)
5. [Troubleshooting](#5-troubleshooting)

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

Step 3: Coherence Validation (6-Tier Veto System) - V6.5.4e ADR-007
├── Tier 1: Contradiction check (5+ vs 3+)
├── Tier 2: Black Swan risk level
├── Tier 3: Coherence score threshold (Adaptive Gate V6.5.4e)
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
├── **V6.5.4d: FINAL_SYMBOL_FILTER_VETO** (última línea de defensa)
├── Order placement (market/limit)
├── TP/SL setting (volatility-based)
└── Decision logging (audit trail)
```

> **V6.5.4d Security:** Added `FINAL_SYMBOL_FILTER_VETO` as last line of defense before trade execution. This redundant check blocks BUY orders on excluded symbols (e.g., ADA/USD) even if earlier filters fail. Uses `analysis.get('symbol')` as primary source.

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

### 2.1 Active Profile: PRODUCTION_STABLE V6.5.4d

**Source of Truth:** `omnix_core/config/trading_profiles.py`

| Parameter | Value | Description |
|-----------|-------|-------------|
| `min_trade_size` | $100 | Minimum trade size |
| `max_trade_size` | $3,000 | Maximum trade size |
| `base_trade_size` | $500 | Default trade size |
| `max_daily_trades` | 10 | Daily trade limit |
| `max_daily_loss_pct` | 15% | Drawdown halt trigger |
| `coherence_threshold` | 30-60% | Adaptive threshold (ADR-007 Phase 1) |
| `min_signal_strength` | 60% | Signal threshold |
| `sl_pct_high_vol` | 2.5% | Stop loss (high volatility) |
| `sl_pct_normal_vol` | 1.5% | Stop loss (normal volatility) |
| `tp_pct_high_vol` | 4.5% | Take profit (high volatility) |
| `tp_pct_normal_vol` | 3.0% | Take profit (normal volatility) |
| `emergency_sl_pct` | 2.0% | **V6.5.4d:** Max absolute loss per position |
| `score_moderate` | 12 | **V6.5.4d:** Same as score_strong (MODERATE disabled) |

### 2.2 V6.5.4d Changes (December 11, 2025)

| Change | From | To | Reason |
|--------|------|-----|--------|
| Emergency SL | N/A | 2% max | Prevent excessive per-trade losses |
| Entry thresholds | score_moderate=9 | score_moderate=12 | Only STRONG/VERY_STRONG signals |
| ADA/USD | Allowed | Blocked | 0% win rate over 12 trades |
| Macro trend veto | N/A | Kalman/HMM | Block trades in bearish trends |

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

### 2.5 PAPER_OPTIMIZED Hardening (December 13, 2025)

**V6.5.4d Update:** PAPER_OPTIMIZED profile was hardened to match PRODUCTION_STABLE safety requirements:

| Parameter | Before | After | Reason |
|-----------|--------|-------|--------|
| `score_very_strong` | 28 | 20 | Align with production |
| `score_strong` | 18 | 12 | Align with production |
| `score_moderate` | 10 | 12 | Disable MODERATE signals |
| `allowed_symbols` | All | BTC/USD, XRP/USD, LINK/USD | Focus on proven pairs |
| `excluded_symbols` | None | SOL, ETH, DOT, AVAX, ATOM, POL, LTC, ADA | Block underperforming pairs |

**Configuration in code:**
```python
PAPER_OPTIMIZED_PROFILE.extra_params = {
    'allowed_symbols': ['BTC/USD', 'XRP/USD', 'LINK/USD'],
    'excluded_symbols': ['SOL/USD', 'ETH/USD', 'DOT/USD', 'AVAX/USD', 
                         'ATOM/USD', 'POL/USD', 'LTC/USD', 'ADA/USD'],
    'use_pair_calibration': True
}
```

---

## 3. Risk Management

### 3.1 Risk Guardian V5.4 Protections

| Protection | Threshold | Action |
|------------|-----------|--------|
| Daily drawdown | 15% | Halt all trading |
| Overtrading | 50 trades/day | Block new trades |
| Revenge trading | 3 consecutive losses | 30-min cooldown |
| Position concentration | 15% per asset | Block additional buys |
| Trade size cap | $20,000 | Hard reject |

### 3.2 Stop Loss / Take Profit by Volatility

| Pair Type | Examples | SL | TP | R:R |
|-----------|----------|-----|-----|-----|
| High Volatility | DOT, AVAX, SOL, LINK | 2.5% | 4.5% | 1:1.8 |
| Normal Volatility | BTC, ETH, XRP, LTC | 1.5% | 3.0% | 1:2.0 |

### 3.3 Circuit Breakers

| Trigger | Action | Reset |
|---------|--------|-------|
| 5% daily loss | Reduce sizes 50% | Next trading day |
| 8% daily loss | Halt all trades | Manual review |
| 3 consecutive losses | 30-min cooldown | Automatic |
| Regime change | 15-min pause | After stability |

### 3.4 Emergency Stop

**Code Location:** `auto_trading_bot.py` → `_check_emergency_stop()`

```python
if current_drawdown > max_daily_loss_pct:
    emergency_stop = True  # Blocks ALL new trades
```

---

## 4. Operational Procedures

### 4.1 Daily Checklist

| Time | Task | Tool |
|------|------|------|
| 00:00 UTC | Check overnight trades | Dashboard |
| 06:00 UTC | Review drawdown status | `/balance` |
| 12:00 UTC | Midday performance check | Dashboard |
| 18:00 UTC | Pre-close review | `/status` |

### 4.2 Monitoring Commands (Telegram)

| Command | Purpose |
|---------|---------|
| `/autotrading status` | Bot status and metrics |
| `/balance` | Current balances |
| `/trades` | Recent trade list |
| `/performance` | Win rate and P&L |
| `/risk` | Risk Guardian status |

### 4.3 Dashboard Access

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| Flask API | `:5000/api/metrics` | Raw data |
| Streamlit | `:8080` | Visual charts |
| Health | `:5000/api/health` | System status |

### 4.4 Railway Deployment

```
GitHub (main) → Auto-deploy → Railway

DO NOT run bot on Replit and Railway simultaneously.
Telegram allows only ONE active connection per token.
```

### 4.5 Control Commands (V6.5.4d)

| Command | Acción | Efecto Inmediato |
|---------|--------|------------------|
| `/pausar` | Detener trading | Loop termina en <5s, DB is_paused=true |
| `/reanudar` | Reanudar trading | Loop reinicia inmediatamente, DB is_paused=false |
| `/status` | Ver estado | Muestra running, trades, win rate |

**Comportamiento V6.5.4d (Event Bridge):**

```
/pausar ejecuta:
1. UserSettingsService.pause_trading() → DB: is_paused = true
2. AutoTradingBot.stop() → Thread.join(timeout=5s)
3. Mensaje: "🛑 Trading pausado"

/reanudar ejecuta:
1. UserSettingsService.resume_trading() → DB: is_paused = false
2. AutoTradingBot.start() → Nuevo Thread con _trading_loop()
3. Mensaje: "🚀 Trading reanudado"
```

> **IMPORTANTE V6.5.4d:** Los comandos ahora reinician el trading loop SIN necesidad de redeploy de Railway.

### 4.6 Thread Safety

Para prevenir race conditions si el usuario ejecuta `/pausar` y `/reanudar` rápidamente:

| Protección | Mecanismo | Resultado |
|------------|-----------|-----------|
| Lock exclusivo | `_start_stop_lock` | Solo un start/stop a la vez |
| Verificación thread | `_thread.is_alive()` | No crear loops duplicados |
| Join con timeout | `join(timeout=5s)` | Espera ordenada del loop anterior |

### 4.7 Heartbeat Monitoring

El trading loop escribe un heartbeat cada ~5 minutos:

| Redis Key | TTL | Contenido |
|-----------|-----|-----------|
| `omnix:heartbeat:trading_loop` | 10 min | cycle, running, total_trades, paper_mode |

**Cómo verificar liveness:**
```bash
redis-cli GET omnix:heartbeat:trading_loop
```

Si la clave no existe o expiró → el loop está muerto → reiniciar con `/reanudar`.

---

## 5. Troubleshooting

### 5.1 No Trades Executing

| Check | Solution |
|-------|----------|
| Profile verification | `echo $TRADING_PROFILE` |
| Drawdown status | Check if < 15% |
| Market conditions | May be waiting for signals |
| Coherence thresholds | ADR-007 calibration applied |

### 5.2 Win Rate Below 55%

| Cause | Action |
|-------|--------|
| Adverse market | Wait for regime change |
| Strategy calibration | Adaptive engine auto-adjusts |
| Profile mismatch | Consider PAPER_OPTIMIZED |

### 5.3 Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| `COHERENCE_BLOCK` | Strategies disagree | Normal - wait for alignment |
| `RISK_GUARDIAN_VETO` | Risk limit triggered | Check drawdown, cooldown |
| `POSITION_LIMIT_REACHED` | Max positions open | Wait for closes |
| `EMERGENCY_STOP` | Drawdown exceeded | Manual review needed |

### 5.4 Log Locations

| Log Type | Location |
|----------|----------|
| Trading | Railway logs |
| Decisions | `decision_logs` table |
| Risk events | `risk_guardian_events` table |
| Dashboard | Flask console |

### 5.5 Veto Calibration (Shadow Portfolio)

El sistema captura todos los trades bloqueados y los analiza después de 24+ horas para determinar si el veto fue correcto.

**Dashboard:** Streamlit → "Shadow Portfolio" tab

**Cron Job:** Corre diariamente a las 05:00 UTC

**Tablas involucradas:**
- `shadow_trade_events` - Trades bloqueados con contexto
- `shadow_trade_outcomes` - Análisis contrafactual
- `filter_calibration_metrics` - Recomendaciones de calibración

**Runbook:** [shadow_portfolio_runner.md](../operations/runbooks/shadow_portfolio_runner.md)

---

## Appendix: Track Record Progress

| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| Trades | 119 | 500+ | 8-9 weeks |
| Win Rate | TBD | 55%+ | Ongoing |
| Active Days | ~5 | 30-60 | Ongoing |

**Goal:** Investor-grade track record for $1M seed funding at $11.5M pre-money valuation.
