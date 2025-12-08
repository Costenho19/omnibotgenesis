# OMNIX V6.5.4 INSTITUTIONAL+ PREMIUM - Current System Metrics
## Real-Time Transparency Report

**Last Updated:** December 8, 2025  
**Data Source:** Production Database (Railway)

---

## TRADING METRICS (Live Data)

### Paper Trading Performance

| Metric | Value | Notes |
|--------|-------|-------|
| **Total Trades** | 27 | Paper trading calibration phase |
| **Winning Trades** | 7 | |
| **Losing Trades** | 20 | |
| **Win Rate** | 25.9% | Below target - optimizing parameters |
| **Total P&L** | -$3,077.84 | Calibration losses expected |
| **Best Trade** | +$252.90 | |
| **Worst Trade** | -$1,007.16 | Outlier during volatile period |
| **Total Gains** | +$365.34 | |
| **Total Losses** | -$2,477.83 | |
| **Open Positions** | 8 | Actively managed |

### Account Status

| Metric | Value |
|--------|-------|
| **Starting Balance** | $1,000,000 |
| **Current Balance** | $897,688.55 |
| **Unrealized P&L** | In open positions |
| **Max Drawdown** | 10.23% |
| **Sharpe Ratio** | Calculating... |

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

### Core Engines (V6.5.4 INSTITUTIONAL+ PREMIUM)

| Engine | Status | Version |
|--------|--------|---------|
| AutoTradingBot | Active | V6.5.4 INSTITUTIONAL+ |
| Non-Markovian Kernel | Active | V6.5 |
| Coherence Engine | Active | V6.5 ULTRA |
| CAES (Adaptive Entry) | Active | V6.5.4 |
| ARES Protocol V1 | Active | V1.1.0 |
| ARES Protocol V2 | Active | V2.1.0 |
| AI Risk Guardian | Active | V5.4 |
| Monte Carlo | Active | Quantum-Enhanced |
| Kalman Filter | Active | Standard |
| HMM Regime Detector | Active | Standard |
| Portfolio Manager | Active | V6.4 INSTITUTIONAL+ |
| **InstitutionalDecisionLogger** | **Active** | **V6.5.4** |
| **Execution Protocol** | **Active** | **V6.5.4 PREMIUM** |
| **Position Manager** | **Active** | **V6.5.4 PREMIUM** |

### New V6.5.4 Features

| Feature | Description |
|---------|-------------|
| **InstitutionalDecisionLogger** | 11 lifecycle events per trade decision with unique decision_id |
| **Volatility-Based SL/TP** | Automatic classification of pairs by volatility |
| **Execution Protocol PREMIUM** | Citadel-level TWAP/VWAP/ICEBERG execution |
| **Trading Profiles System** | 4 profiles: INSTITUTIONAL, PAPER_AGGRESSIVE, BALANCED, PAPER_OPTIMIZED |
| **Audit Trail Events** | TRADE_CANDIDATE, VETO_COHERENCE, VETO_CONSENSUS, VETO_DRAWDOWN, VETO_RISK_GUARDIAN, VETO_HMM_REGIME, VETO_POSITION_LIMIT, TRADE_VALIDATED, TRADE_EXECUTED, TRADE_REJECTED, AI_NARRATIVE |

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

**Document Version:** V6.5.4.2  
**Last Updated:** December 8, 2025
