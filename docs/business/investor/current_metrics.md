# OMNIX V6.5.4e INSTITUTIONAL+ - Current System Metrics
## Real-Time Transparency Report

**Last Updated:** January 14, 2026  
**Data Source:** Production Database (Railway)  
**Latest Change:** ADR-007 Coherence Threshold Calibration

---

## TRADING METRICS (Live Data)

### Paper Trading Performance

| Metric | Value | Notes |
|--------|-------|-------|
| **Total Trades** | 119 | Paper trading calibration phase |
| **Winning Trades** | 24 | Based on profit_loss > 0 (USD) |
| **Losing Trades** | 95 | |
| **Win Rate** | 20.17% | Learning phase - filters being calibrated |
| **Total P&L** | -$15,198.73 | Sum of all 119 trades |
| **Shadow Events** | 360 | Vetoed trades tracked for analysis |
| **Open Positions** | 0 | All positions closed |

### Account Status

| Metric | Value |
|--------|-------|
| **Starting Balance** | $1,000,000 (Paper Trading) |
| **Current Balance** | $984,801.27 |
| **Capital Preserved** | 98.5% |
| **Total P&L** | -$15,198.73 |
| **Total Return** | -1.52% |

---

## CONTEXT & EXPLANATION

### Why These Results?

The system is in **calibration phase**. Early trades used the PAPER_AGGRESSIVE profile with lower thresholds (30% coherence), which allowed lower-quality signals through. Key learnings:

1. **SL/TP Ratio was suboptimal** - Original 1.5%/2.5% didn't give trades enough room
2. **Coherence threshold too low** - 30% allowed weak consensus trades
3. **Market conditions challenging** - Sideways markets generate weak signals

### What We've Fixed (V6.5.4)

| Issue | Solution |
|-------|----------|
| Trades closed too early | New SL 1.5%/TP 3.0% ratio (2:1 R:R) |
| Weak signal entries | Coherence threshold raised to 60% |
| No audit trail | InstitutionalDecisionLogger with 11 events |
| Fixed SL/TP for all pairs | Volatility-based classification (high vs normal vol) |

### Current Profile: PAPER_OPTIMIZED

| Parameter | Value |
|-----------|-------|
| Coherence Veto Critical | 45% |
| Coherence Veto Normal | 60% |
| Stop Loss (Normal Vol) | 1.5% |
| Stop Loss (High Vol) | 2.5% |
| Take Profit (Normal Vol) | 3.0% |
| Take Profit (High Vol) | 4.5% |
| Min Confidence | 22% |
| Max Position | 8% of portfolio |
| Max Daily Loss | 4% |

---

## SYSTEM STATUS

### Core Engines (V6.5.4e INSTITUTIONAL+ PREMIUM)

| Engine | Status | Version |
|--------|--------|---------|
| AutoTradingBot | Active | V6.5.4e INSTITUTIONAL+ |
| Non-Markovian Kernel | Active | V6.5 |
| Coherence Engine | Active | V6.5 ULTRA (ADR-007 calibrated) |
| CAES (Adaptive Entry) | Active | V6.5.4 |
| Quantum Momentum | Active | V6.5.4 |
| Kelly Criterion | Active | V6.5.4 |
| AI Risk Guardian | Active | V5.4 |
| Monte Carlo | Active | Quantum-Enhanced |
| Kalman Filter | Active | V6.5.4e Optimized |
| HMM Regime Detector | Active | Standard |
| Portfolio Manager | Active | V6.4 INSTITUTIONAL+ |
| **InstitutionalDecisionLogger** | **Active** | **V6.5.4** |
| **Execution Protocol** | **Active** | **V6.5.4 PREMIUM** |
| **Position Manager** | **Active** | **V6.5.4 PREMIUM** |

### New V6.5.4e Features (Jan 2026)

| Feature | Description |
|---------|-------------|
| **ADR-007 Coherence Calibration** | Phase 1: 5-point threshold reduction (LOW 30%, MEDIUM 40%, HIGH 50%, EXTREME 60%) |
| **InstitutionalDecisionLogger** | 11 lifecycle events per trade decision with unique decision_id |
| **Volatility-Based SL/TP** | Automatic classification of pairs by volatility |
| **Execution Protocol PREMIUM** | Citadel-level TWAP/VWAP/ICEBERG execution |
| **Trading Profiles System** | 5 profiles: INSTITUTIONAL, PAPER_AGGRESSIVE, BALANCED, PAPER_OPTIMIZED, WIN_RATE_OPTIMIZED |
| **Audit Trail Events** | TRADE_CANDIDATE, VETO_COHERENCE, VETO_CONSENSUS, VETO_DRAWDOWN, VETO_RISK_GUARDIAN, VETO_HMM_REGIME, VETO_POSITION_LIMIT, TRADE_VALIDATED, TRADE_EXECUTED, TRADE_REJECTED, AI_NARRATIVE |
| **Shadow Portfolio System** | Counterfactual analysis of vetoed trades for filter calibration |
| **Veto Tracking System** | Real-time capital protection tracking with PostgreSQL persistence |
| **Adaptive Coherence Gate** | Dynamic thresholds based on EMA score + Black Swan severity |
| **Kalman Filter Optimization** | Log suppression + per-pair caching for reduced system overhead |

### V6.5.4 PREMIUM Panel Features (Dec 8, 2025)

| Feature | Description |
|---------|-------------|
| **InstitutionalMetricsCalculator** | Sharpe, Sortino, Calmar ratios per-pair and portfolio-wide |
| **PDF Report Generator** | 989-line institutional PDF with Monte Carlo projections |
| **Monte Carlo Real Simulation** | 10,000 numpy iterations per horizon (30/90/180 days) |
| **Streamlit Dashboard** | Interactive investor visualization with Plotly charts |
| **OmnixAPIClient** | Service separation - Streamlit consumes Flask API exclusively |
| **Centralized Finnhub Service** | Real-time news via centralized service (no 422/429 errors) |
| **Dual Dashboard Architecture** | Flask (port 5000) + Streamlit (port 8080) |

### Infrastructure

| Component | Status | Details |
|-----------|--------|---------|
| Railway Deployment | Online | 24/7 |
| PostgreSQL Database | Connected | 42+ tables |
| Redis Cache | Connected | Fast state management |
| Telegram Bot | Active | User interface |
| Dashboard | Active | 12/12 widgets OK |

### Security

| Feature | Status |
|---------|--------|
| Post-Quantum Encryption | Active (Kyber-768) |
| Digital Signatures | Active (Dilithium-3) |
| Session Management | Secure |
| API Rate Limiting | Active |

---

## SUPPORTED MARKETS

### Cryptocurrencies (Kraken)

| Pair | Volatility Class | SL/TP |
|------|------------------|-------|
| BTC/USD | Normal | 1.5%/3.0% |
| ETH/USD | Normal | 1.5%/3.0% |
| LTC/USD | Normal | 1.5%/3.0% |
| XRP/USD | Normal | 1.5%/3.0% |
| ADA/USD | Normal | 1.5%/3.0% |
| SOL/USD | **High** | 2.5%/4.5% |
| DOT/USD | **High** | 2.5%/4.5% |
| LINK/USD | **High** | 2.5%/4.5% |
| AVAX/USD | **High** | 2.5%/4.5% |
| ATOM/USD | **High** | 2.5%/4.5% |
| POL/USD | **High** | 2.5%/4.5% |

### Stocks (Alpaca)

| Category | Status |
|----------|--------|
| US Equities | Active |
| ETFs | Active |
| Fractional Shares | Supported |

---

## INSTITUTIONAL DECISION LOGGER

### Event Types

```
TRADE_CANDIDATE    → Signal generated, entering decision flow
VETO_COHERENCE     → Blocked by coherence score threshold
VETO_CONSENSUS     → Blocked by strategy disagreement
VETO_DRAWDOWN      → Blocked by daily loss limit
VETO_RISK_GUARDIAN → Blocked by AI risk monitor
VETO_HMM_REGIME    → Blocked by unfavorable market regime
VETO_POSITION_LIMIT → Blocked by max open positions
TRADE_VALIDATED    → All guards passed, ready to execute
TRADE_EXECUTED     → Order placed successfully
TRADE_REJECTED     → Final rejection with veto_chain
AI_NARRATIVE       → Post-decision explanation (non-decisional)
```

### Sample Log Output

```json
{
  "decision_id": "DEC-20251208002232-5355493B",
  "event_type": "TRADE_VALIDATED",
  "timestamp": "2025-12-08T00:22:32.923936Z",
  "symbol": "ADA/USD",
  "direction": "BUY",
  "position_size_usd": 42393.75,
  "guards_passed": ["CONSENSUS", "COHERENCE"]
}
```

### Compatibility

- **Grafana + Loki** - Direct JSON ingestion
- **ELK Stack** - Elasticsearch/Logstash/Kibana ready
- **BigQuery/Snowflake** - Structured for data warehouses
- **Datadog** - Log management integration

---

## DATA FRESHNESS COMMITMENT

This document will be updated:
- Automatically after every 50 trades
- Weekly during active trading
- On request for investor updates

All metrics are pulled directly from the production database with no manual adjustments.

---

*For historical data access or custom reports, contact the OMNIX team.*

---

## SHADOW PORTFOLIO SYSTEM (January 2026)

### What It Does

Every blocked trade is tracked and analyzed 24-30 hours later to determine if the veto was correct:

| Metric | Description |
|--------|-------------|
| **Shadow Events Captured** | 360 trades blocked and tracked |
| **Veto Types Tracked** | COHERENCE_GATE, MONTE_CARLO, BLACK_SWAN, RMS |
| **Analysis Window** | 24-720 hours post-veto |
| **Output** | Veto accuracy %, missed opportunities, filter recommendations |

### Investor Value

> "OMNIX implements institutional-grade counterfactual analysis. Every blocked trade is tracked and analyzed to determine filter accuracy. This data-driven approach ensures our risk filters are neither too conservative (blocking profitable opportunities) nor too loose (allowing losing trades). The system learns from its own decisions."

### Dashboard Access

- **Streamlit Dashboard** → "Shadow Portfolio" tab
- Shows: Accuracy by veto type, top missed opportunities, calibration recommendations

---

**Document Version:** V6.5.4e  
**Last Updated:** January 14, 2026
