# OMNIX Decision Governance
## Complete Feature Catalog
### End-User Functionality Reference

---

**Document Classification:** Feature Documentation  
**Version:** 1.1  
**Date:** January 2026  
**Purpose:** Comprehensive catalog of all user-facing features for investor due diligence

---

## TABLE OF CONTENTS

1. [Trading Capabilities](#1-trading-capabilities)
2. [AI & Intelligence Features](#2-ai--intelligence-features)
3. [Risk Management & Capital Protection](#3-risk-management--capital-protection)
4. [Portfolio Management](#4-portfolio-management)
5. [Analytics & Investor Reporting](#5-analytics--investor-reporting)
6. [User Interface & Interaction](#6-user-interface--interaction)
7. [Community Intelligence](#7-community-intelligence)
8. [Security Features](#8-security-features)
9. [Feature Verification Matrix](#9-feature-verification-matrix)

---

## 1. TRADING CAPABILITIES

### 1.1 Paper Trading System

| Feature | Description | User Benefit |
|---------|-------------|--------------|
| **$1M Virtual Capital** | Start with $1,000,000 simulated funds | Risk-free strategy testing |
| **Real Market Prices** | Uses live Kraken prices for all trades | Realistic performance metrics |
| **Instant Execution** | `/paper_buy BTC 10000` executes immediately | No slippage in testing |
| **Position Tracking** | Full portfolio view with unrealized P&L | Real-time performance monitoring |
| **Trade History** | Complete record of all paper trades | Track record for investors |

### 1.2 Automated Trading (24/7)

| Feature | Description | User Benefit |
|---------|-------------|--------------|
| **Auto-Trading Bot** | Autonomous trade execution based on AI signals | Generates trades while you sleep |
| **Multi-Crypto Scanner** | Scans 11 cryptocurrency pairs simultaneously | Finds best opportunities across markets |
| **Tiered Signal Strength** | Trades classified by confidence (Tier 1-6) | Only highest quality trades execute |
| **Ramp-Up System** | Gradually increases position sizes on success | Protects capital early, maximizes later |
| **Profile-Based Execution** | 5 trading profiles for different strategies | Customizable risk/reward approach |

### 1.3 Supported Markets

| Market | Exchange | Pairs/Assets | Status |
|--------|----------|--------------|--------|
| **Cryptocurrency** | Kraken | 11 pairs (BTC, ETH, SOL, DOT, etc.) | Active |
| **US Stocks** | Alpaca | NYSE/NASDAQ equities | Active |
| **ETFs** | Alpaca | All major ETFs | Active |
| **Fractional Shares** | Alpaca | Any stock amount | Supported |

### 1.4 Trade Execution

| Feature | Description | User Benefit |
|---------|-------------|--------------|
| **TWAP Execution** | Time-Weighted Average Price | Reduces market impact |
| **VWAP Execution** | Volume-Weighted Average Price | Better fill prices |
| **ICEBERG Orders** | Large orders split into smaller chunks | Hides order size from market |
| **Liquidity Analysis** | Pre-trade liquidity assessment | Avoids thin markets |

---

## 2. AI & INTELLIGENCE FEATURES

### 2.1 Core AI Strategies (Signal Generators)

| # | Strategy | Type | What It Does |
|---|----------|------|--------------|
| 1 | **Monte Carlo** | Statistical | Simulates 10,000 future scenarios |
| 2 | **Black Swan Detection** | Risk | Identifies extreme market conditions |
| 3 | **Sentiment Analysis** | Behavioral | Measures market mood (Fear & Greed) |
| 4 | **Kelly Criterion** | Sizing | Calculates optimal bet size |
| 5 | **HMM Regime Detection** | Machine Learning | Detects TRENDING/RANGING/VOLATILE |
| 6 | **Kalman Filter** | Signal Processing | Filters noise from price signals (optimized with log suppression + per-pair caching) |
| 7 | **Quantum Momentum** | Proprietary | 6-component technical score (EMA/RSI/MACD/Volume/HP/ATR) |
| 8 | **Risk Guardian** | Protection | Overtrading prevention, drawdown protection |
| 9 | **Coherence Engine** | Validation | 6-tier consensus threshold system |
| 10 | **Non-Markovian Kernel** | Proprietary | Temporal memory with decay function |

### 2.2 Support Modules (Protection & Execution)

| # | Module | Purpose |
|---|--------|---------|
| 1 | **Risk Guardian V5.4** | Overtrading prevention, drawdown protection |
| 2 | **Coherence Engine V6.5** | 6-tier threshold-based validation |
| 3 | **Adaptive Coherence Gate V010** | Dynamic thresholds based on market severity |
| 4 | **Adaptive Parameter Engine** | Auto-calibration by market regime |
| 5 | **Market Intelligence** | Fear & Greed Index, Finnhub News, Alpha Vantage (NOT on-chain - roadmap) |
| 6 | **Execution Protocol** | TWAP/VWAP/ICEBERG execution |
| 7 | **Fear & Greed Contrarian** | Score adjustment on extreme sentiment |

### 2.3 Conversational AI

| Feature | Description | User Benefit |
|---------|-------------|--------------|
| **Natural Language Q&A** | Ask anything about crypto in plain language | No technical knowledge required |
| **Multi-Provider AI** | Gemini 2.0 Flash + OpenAI GPT-4o fallback | High availability |
| **Context Awareness** | Remembers conversation history | Coherent multi-turn dialogue |
| **Voice Responses** | Audio replies via Whisper TTS | Hands-free interaction |

### 2.4 Real-Time Web Search

| Feature | Description | User Benefit |
|---------|-------------|--------------|
| **Tavily Integration** | Real-time internet search | Latest news and information |
| **Redis Caching** | Cached results for speed | Instant repeated queries |
| **Natural Language** | "busca noticias bitcoin hoy" | Intuitive search commands |
| **Source Attribution** | Links to original sources | Verifiable information |

---

## 3. RISK MANAGEMENT & CAPITAL PROTECTION

### 3.1 Circuit Breaker System

| Protection | Trigger | Action |
|------------|---------|--------|
| **Daily Loss Limit** | Exceeds configured % | Halts all trading |
| **Drawdown Limit** | Max drawdown exceeded | Reduces position sizes |
| **Consecutive Losses** | 3+ losses in a row | 30-minute cooldown |
| **Volatility Spike** | Extreme market movement | Pauses new entries |
| **Regime Change** | Market structure shift | 15-minute observation |

### 3.2 Position Limits

| Limit Type | Default | Purpose |
|------------|---------|---------|
| **Per-Trade Maximum** | 8% of portfolio | Single trade can't destroy account |
| **Daily Trade Count** | 50 max | Prevents overtrading |
| **Open Positions** | Configurable | Limits total exposure |
| **Concentration** | 15% per asset | Forces diversification |
| **Hard Cap** | $20,000 per trade | Absolute maximum |

### 3.3 Volatility-Adaptive Stop Loss / Take Profit

| Pair Type | Examples | Stop Loss | Take Profit | R:R |
|-----------|----------|-----------|-------------|-----|
| **High Volatility** | DOT, AVAX, SOL, LINK | 2.5% | 4.5% | 1:1.8 |
| **Normal Volatility** | BTC, ETH, XRP, LTC | 1.5% | 3.0% | 1:2.0 |

### 3.4 Algorithmic Rollback Protocol (ARP)

| Phase | Threshold | Action |
|-------|-----------|--------|
| **Warning** | 0.5% drawdown in 1 hour | Log warning, prepare revert |
| **Auto-Revert** | 1% drawdown in 24 hours | Automatic config rollback |
| **Emergency Stop** | Critical breach | Halt all trading immediately |

### 3.5 Adaptive Coherence Gate (Jan 2026) - ADR-007

| EMA Signal | Black Swan Severity | Coherence Threshold | Benefit |
|------------|---------------------|---------------------|---------|
| **Strong (≥20 pts)** | LOW | 30% | Maximum opportunity capture |
| **Strong (≥20 pts)** | MEDIUM | 40% | Balanced filtering |
| **Strong (≥20 pts)** | HIGH | 50% | Strict protection |
| **Strong (≥20 pts)** | EXTREME | 60% | Maximum protection |
| **Weak (<20 pts)** | Any | 10%/30% (paper/real) | Default protection |

> **ADR-007 Phase 1 (Jan 14, 2026):** 5-point threshold reduction based on Shadow Portfolio analysis showing 48,937 vetos blocking $978.7M in 7 days.

**Investor Value Proposition:**
> "OMNIX dynamically calibrates coherence filters based on market regime severity, maximizing opportunity capture in favorable conditions while maintaining institutional discipline during high-risk periods."

**Technical Implementation:**
- Centralized architecture in CoherenceEngine (domain service pattern)
- AdaptiveGateDecision DTO for transparent decision tracking
- Real-time Railway logging: `ADAPTIVE_GATE_DECISION` events
- Fail-closed safety: Any exception blocks trade (capital protection priority)

### 3.6 Shadow Portfolio System (Jan 2026)

| Feature | Description | User Benefit |
|---------|-------------|--------------|
| **Counterfactual Analysis** | Tracks every blocked trade | Learn if vetos were correct |
| **24-720h Analysis Window** | Analyzes price movement after veto | Data-driven filter calibration |
| **Veto Accuracy Metrics** | Accuracy % by veto type | Identify overprotective filters |
| **Missed Opportunity Detection** | Finds profitable blocked trades | Optimize filter thresholds |
| **Calibration Recommendations** | Automatic threshold suggestions | Continuous improvement |

**Investor Value Proposition:**
> "OMNIX implements institutional-grade counterfactual analysis. Every blocked trade is tracked and analyzed 24-30 hours later to determine filter accuracy. This data-driven approach ensures our risk filters learn from their own decisions."

**Technical Implementation:**
- Tables: `shadow_trade_events`, `shadow_trade_outcomes`, `filter_calibration_metrics`
- Daily cron job: 05:00 UTC via Railway
- Dashboard: Streamlit "Shadow Portfolio" tab
- Thresholds: >1% gain = incorrect veto, <1% marginal = correct veto

### 3.7 Veto Tracking System (Jan 2026)

| Feature | Description | User Benefit |
|---------|-------------|--------------|
| **Real-time Logging** | Every veto persisted to PostgreSQL | Complete audit trail |
| **Capital Protection Metrics** | Tracks potential losses avoided | Investor reporting |
| **Deduplication** | Prevents inflated reporting | Accurate metrics |
| **Dashboard Integration** | Veto stats in main dashboard | Transparency |

**Investor Value Proposition:**
> "OMNIX tracks every blocked trade with the capital at risk, providing verifiable metrics on how much potential loss the system prevented."

---

## 4. PORTFOLIO MANAGEMENT

### 4.1 Optimization Models

| Model | Description | User Benefit |
|-------|-------------|--------------|
| **Markowitz Mean-Variance** | Classic portfolio optimization | Optimal risk-adjusted allocation |
| **Black-Litterman** | Incorporates user views | Personalized optimization |

### 4.2 Position Sizing (CAES)

| Factor | Calculation | Effect |
|--------|-------------|--------|
| **Base Size** | Account Balance x Base % | Starting position |
| **Aggression Factor** | Sigmoid of Kernel Confidence | 0.5x - 3.0x multiplier |
| **Regime Multiplier** | Market condition adjustment | 0.5x - 1.3x |
| **ATR Validation** | External volatility check | Hard caps on aggression |

### 4.3 Risk Profiles

| Profile | Max Per Trade | Daily Loss Limit | Best For |
|---------|---------------|------------------|----------|
| **Ultraconservador** | 2% | 5% | Maximum protection |
| **Conservador** | 5% | 10% | Stable growth |
| **Moderado** | 10% | 15% | Balanced approach |
| **Agresivo** | 15% | 25% | Higher risk/reward |
| **Institucional** | 8% | 12% | Goldman-Sachs parameters |

---

## 5. ANALYTICS & INVESTOR REPORTING

### 5.1 Institutional Metrics

| Metric | Description | Industry Standard |
|--------|-------------|-------------------|
| **Sharpe Ratio** | Return / Total Volatility | Used by Citadel, Millennium |
| **Sortino Ratio** | Return / Downside Risk Only | Preferred by Point72 |
| **Calmar Ratio** | Annual Return / Max Drawdown | Used by Two Sigma |
| **Profit Factor** | Gross Profit / Gross Loss | Standard hedge fund metric |

### 5.2 PDF Report Generator

| Section | Content |
|---------|---------|
| **Executive Summary** | Performance overview, key metrics |
| **Risk Analysis** | Sharpe, Sortino, Calmar with interpretations |
| **Per-Pair Breakdown** | Individual crypto/stock performance |
| **Monte Carlo Projections** | 10,000 scenario simulation (30/90/180 days) |
| **Drawdown Analysis** | Historical drawdown chart |

### 5.3 Advanced Analysis Tools

| Tool | Command | Output |
|------|---------|--------|
| **Volume Profile** | Automatic | Detects whale trading zones |
| **Fibonacci Levels** | Automatic | Support/resistance levels |
| **Monte Carlo** | `/montecarlo BTC` | Probability distributions |
| **Black Swan** | `/blackswan BTC` | Extreme risk assessment |
| **Order Book** | `/orderbook BTC` | Liquidity analysis |

### 5.4 Dashboards

| Dashboard | Port | Purpose |
|-----------|------|---------|
| **Flask API** | 5000 | Backend API, web terminal |
| **Streamlit** | 8080 | Interactive investor visualization |

---

## 6. USER INTERFACE & INTERACTION

### 6.1 Telegram Bot Interface

| Feature | Description | User Benefit |
|---------|-------------|--------------|
| **Interactive Menu** | Inline button navigation | Click instead of typing |
| **40+ Commands** | Complete functionality access | Everything in one place |
| **Voice Responses** | Audio message replies | Hands-free usage |
| **Multi-Language** | English, Spanish, Arabic docs | Global accessibility |

### 6.2 Main Menu Structure

```
[Price BTC] [Analysis BTC]
[Price ETH] [Analysis ETH]
[Kraken Balance] [History]
[Active Alerts] [New Alert]
[AI Strategies] [Settings]
[System Status] [Help]
```

### 6.3 Command Categories

| Category | Example Commands | Count |
|----------|-----------------|-------|
| **Market Data** | `/precio`, `/market`, `/balance` | 8 |
| **Paper Trading** | `/paper_start`, `/paper_buy`, `/paper_sell` | 5 |
| **Stock Trading** | `/balance_bolsa`, `/analizar`, `/comprar_bolsa` | 6 |
| **Auto-Trading** | `/auto_start`, `/auto_stop`, `/auto_status` | 3 |
| **Advanced Analysis** | `/montecarlo`, `/blackswan`, `/sentiment` | 7 |
| **Web Search** | `/buscar` | 1 |
| **Configuration** | `/miconfig`, `/perfil`, `/limites` | 8 |
| **Community** | `/feedback`, `/community_stats`, `/top_strategies` | 5 |
| **Education** | `/educacion`, `/legal` | 2 |

### 6.4 Alert System

| Feature | Description | User Benefit |
|---------|-------------|--------------|
| **Price Alerts** | Notify when price reaches target | Never miss opportunity |
| **Configurable** | Set any price level | Customized monitoring |
| **Multi-Asset** | Alerts for any supported pair | Comprehensive coverage |

### 6.5 User Configuration

| Setting | Command | Options |
|---------|---------|---------|
| **Risk Profile** | `/perfil` | 5 preset profiles |
| **Trading Limits** | `/limites` | Custom thresholds |
| **Protection** | `/proteccion` | Auto-protection settings |
| **Strategies** | `/estrategias` | Enable/disable strategies |
| **Allowed Cryptos** | `/cryptos` | Whitelist pairs |
| **Auto-Trading** | `/autotrading` | Toggle on/off |

---

## 7. COMMUNITY INTELLIGENCE

### 7.1 Feedback System

| Feature | Description | User Benefit |
|---------|-------------|--------------|
| **Strategy Feedback** | Report if strategy worked | Collective learning |
| **Point System** | Earn points for contributions | Gamified engagement |
| **Leaderboard** | Top contributors ranking | Recognition |

### 7.2 Community Features

| Command | Purpose |
|---------|---------|
| `/feedback` | Report strategy performance |
| `/community_stats` | View community statistics |
| `/top_strategies` | See best performing strategies |
| `/my_signals` | Your personal signal history |
| `/vote_strategy` | Vote on strategy effectiveness |

---

## 8. SECURITY FEATURES

### 8.1 Post-Quantum Cryptography

| Algorithm | Standard | Purpose | Status |
|-----------|----------|---------|--------|
| **Kyber-768** | NIST-standardized | Key encapsulation | Active |
| **Dilithium-3** | NIST-standardized | Digital signatures | Active |

### 8.2 Data Protection

| Feature | Implementation |
|---------|----------------|
| **Cache Key Hashing** | SHA256 normalized keys |
| **Session Isolation** | Per-user trading sessions |
| **Redis Encryption** | Secure state management |
| **API Rate Limiting** | Production-grade protection |

### 8.3 Audit Trail

| Event Type | Logged Data |
|------------|-------------|
| **Trade Candidates** | Signal generated, analysis |
| **Veto Events** | Why trades were blocked |
| **Execution Events** | Trade placed, filled |
| **Override Events** | Manual interventions |

### 8.4 Sharia Compliance

| Feature | Command | Purpose |
|---------|---------|---------|
| **Sharia Check** | `/sharia [crypto]` | Verify Islamic finance compliance |
| **Screening** | Automatic | Filter non-compliant assets |

---

## 9. FEATURE VERIFICATION MATRIX

### 9.1 Code Location Reference

| Feature | Primary File | Verified |
|---------|--------------|----------|
| Paper Trading | `omnix_services/telegram_service/enterprise_bot.py` | Yes |
| Monte Carlo | `omnix_core/strategies/monte_carlo.py` | Yes |
| Coherence Engine | `omnix_core/engines/coherence_engine.py` | Yes |
| Risk Guardian | `omnix_core/risk/ai_risk_guardian.py` | Yes |
| Circuit Breaker | `omnix_services/risk_management/circuit_breaker.py` | Yes |
| Institutional Metrics | `omnix_services/analytics/institutional_metrics.py` | Yes |
| PDF Reports | `omnix_services/analytics/institutional_report.py` | Yes |
| Volume Profile | `omnix_services/analytics/volume_profile.py` | Yes |
| Fibonacci Analyzer | `omnix_services/analytics/fibonacci_analyzer.py` | Yes |
| Web Search | `omnix_services/web_search_service/search_manager.py` | Yes |
| Redis Cache | `omnix_core/cache/redis_cache.py` | Yes |
| CAES Sizing | `omnix_core/strategies/caes_module.py` | Yes |
| ARP Rollback | `omnix_core/risk/rollback_protocol.py` | Yes |

### 9.2 Verification Queries

Investors can verify feature implementation:

```sql
-- Verify paper trades exist
SELECT COUNT(*) FROM paper_trades;

-- Verify decision logging
SELECT DISTINCT event_type FROM decision_logs;

-- Verify user settings
SELECT COUNT(*) FROM user_settings;
```

---

## DOCUMENT MAINTENANCE

| Update Trigger | Action |
|----------------|--------|
| New feature added | Add to relevant category |
| Feature modified | Update description |
| Feature removed | Move to deprecated section |
| Code location change | Update verification matrix |

---

*This document is automatically updated with each major release.*

**Document Version:** 1.1  
**Last Updated:** January 9, 2026  
**Next Review:** February 2026
