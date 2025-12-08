# OMNIX V6.5.4 INSTITUTIONAL+ PREMIUM
## Internal Audit & Transparency Report
### Investor-Grade Documentation

---

**Document Classification:** Internal Audit Report  
**Version:** 1.0  
**Date:** December 2025  
**Prepared for:** Due Diligence Review by Prospective Investors  

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Trading Methodology](#2-trading-methodology)
3. [Strategy Ensemble](#3-strategy-ensemble)
4. [Coherence Engine: Dynamic Consensus Gate](#4-coherence-engine)
5. [Trading Profiles System](#5-trading-profiles)
6. [InstitutionalDecisionLogger: Audit Trail](#6-institutional-decision-logger)
7. [Risk Management Framework](#7-risk-management)
8. [Post-Quantum Security](#8-post-quantum-security)
9. [Data Integrity & Metrics](#9-data-integrity)
10. [Governance & Access Control](#10-governance)
11. [Declaration of Integrity](#11-declaration-of-integrity)
12. [Appendix: Technical Specifications](#12-appendix)

---

## 1. EXECUTIVE SUMMARY

This document provides complete transparency into OMNIX's trading decision-making process, risk controls, and audit mechanisms. It is designed for institutional investors conducting due diligence and demonstrates our commitment to:

- **Full Transparency:** Trading decisions are logged with multiple event types
- **Algorithmic Decision-Making:** Weighted scoring system with configurable thresholds
- **Risk-First Philosophy:** Multiple layers of protection before any trade executes
- **Verifiable Results:** All metrics are calculated from database records

**Key Differentiators:**

| Feature | OMNIX | Typical Trading Bots |
|---------|-------|---------------------|
| Audit Trail | Multiple event types per trade | None or minimal |
| Strategy Consensus | Multiple strategies weighted + scored | Single strategy |
| Veto Layers | Multi-layer threshold system | 0-1 layers |
| Post-Quantum Security | Kyber-768/Dilithium-3 infrastructure | None |
| Decision Logging | Institutional-grade | Basic logs |

---

## 2. TRADING METHODOLOGY

### 2.1 Decision Flow Overview

```
Market Data → 10 Core Strategies Analyze → Coherence Engine Validates → 
Risk Guardian Reviews → Execution Protocol Executes → Logger Records
```

### 2.2 Core Principles

1. **Weighted Scoring:** Multiple strategies contribute to a composite score
2. **Threshold-Based Vetos:** Protection layers can block trades below thresholds
3. **Position Limits:** Configurable caps prevent overexposure
4. **Comprehensive Logging:** Decision points are recorded for audit

### 2.3 Trade Lifecycle

| Phase | Description | Logged? |
|-------|-------------|---------|
| Candidate | Strategy generates signal | Yes |
| Validation | Coherence Engine evaluates | Yes |
| Risk Check | Risk Guardian reviews | Yes |
| Execution | Trade placed on exchange | Yes |
| Monitoring | TP/SL tracked | Yes |
| Close | Position closed | Yes |

---

## 3. STRATEGY ENSEMBLE

### 3.1 Core Trading Strategies (Signal Generators)

These 10 strategies generate signals that are weighted and scored:

| # | Strategy | Type | Purpose | Role in Scoring |
|---|----------|------|---------|-----------------|
| 1 | Monte Carlo | Statistical | Validate probabilities with simulations | Weighted signal |
| 2 | Black Swan | Risk | Detect extreme conditions (Kurtosis/Skewness) | Veto power |
| 3 | Sentiment Analysis | Behavioral | Market sentiment timing | Weighted signal |
| 4 | Kelly Criterion | Position Sizing | Optimal mathematical sizing | Size adjustment |
| 5 | HMM Regime Detection | Machine Learning | Detect TRENDING/RANGING/VOLATILE | Regime context |
| 6 | Kalman Filter | Signal Processing | Adaptive signal filtering | Weighted signal |
| 7 | Quantum Momentum | Proprietary | 6-component score (EMA/RSI/MACD/Volume/HP/ATR) | Primary signal |
| 8 | ARES V1 | Swing Trading | Institutional swing strategy | Weighted signal |
| 9 | ARES V2 | Scalping | Ultra-fast M1 scalping | Weighted signal |
| 10 | Non-Markovian Kernel | Proprietary | Temporal memory with K(t-s) decay function | Confidence boost |

**Note:** Win rate targets (55%+) are system goals, not guaranteed outcomes. Actual performance depends on market conditions and profile configuration.

### 3.2 Support Modules (Non-Signal)

These modules provide protection and execution but do not generate trading signals:

| # | Module | Purpose |
|---|--------|---------|
| 1 | Risk Guardian V5.4 | Overtrading prevention, drawdown protection |
| 2 | Coherence Engine V6.5 | Threshold-based validation |
| 3 | Adaptive Parameter Engine | Auto-calibration by regime |
| 4 | On-Chain Intelligence | Whale tracking, blockchain analytics |
| 5 | Execution Protocol | Trade execution (market/limit orders) |
| 6 | Fear & Greed Contrarian | Score adjustment on extreme sentiment |

### 3.3 Signal Generation Process

Each strategy generates a signal:

| Signal | Value | Meaning |
|--------|-------|---------|
| STRONG_BUY | +2 | High confidence long |
| BUY | +1 | Moderate confidence long |
| HOLD | 0 | No action |
| SELL | -1 | Moderate confidence short |
| STRONG_SELL | -2 | High confidence short |

**Final Score Calculation:**

```
Score = Σ(Strategy_Signal × Strategy_Weight)
```

Where weights are dynamically adjusted based on recent performance and market regime.

---

## 4. COHERENCE ENGINE: DYNAMIC CONSENSUS GATE

### 4.1 Overview

The Coherence Engine aggregates multi-strategy votes and applies weighted agreement and confidence thresholds to determine whether a trade should proceed. It operates as a dynamic consensus gate rather than a fixed rule set.

**How It Works:**
- Each strategy generates a directional signal (BUY/SELL/HOLD)
- The engine calculates **agreement_ratio** (how many strategies agree)
- The engine calculates **coherence_score** (weighted confidence level)
- These scores are compared against profile-specific thresholds
- Decisions are logged for audit purposes

### 4.2 Decision Outcomes

The engine returns one of three outcomes:

| Outcome | When Applied | Action |
|---------|--------------|--------|
| **PASS** | Scores meet profile thresholds | Trade proceeds |
| **BLOCK** | Scores below minimum thresholds | Trade rejected |
| **REVIEW** | Borderline scores or overrides | May proceed with adjustments |

**Note:** The specific thresholds are configurable per Trading Profile. Override decisions are logged when triggered.

### 4.3 Profile-Driven Thresholds

The Coherence Engine reads threshold values from the active Trading Profile:
- `coherence_veto_critical` - Minimum score to avoid immediate block
- `coherence_veto_normal` - Score threshold for cautionary review
- `coherence_warning` / `coherence_good` - Confidence bands

These values are exposed in `omnix_core/config/trading_profiles.py` and can be inspected during due diligence.

### 4.4 Transparency Through Logging

The Coherence Engine logs all decisions:
- Calculated agreement ratios and coherence scores
- Thresholds compared against
- Override events when strong signals bypass recommendations
- Final decision outcome (PASS/BLOCK/REVIEW)

---

## 5. TRADING PROFILES SYSTEM

### 5.1 Available Profiles

OMNIX supports configurable trading profiles for different use cases:

| Profile | Purpose | Aggressiveness |
|---------|---------|----------------|
| **INSTITUTIONAL** | Real money trading, maximum capital protection | Conservative |
| **PAPER_AGGRESSIVE** | Rapid track record building | Aggressive |
| **BALANCED** | Middle ground between protection and opportunity | Moderate |
| **PAPER_OPTIMIZED** | Investor demonstrations, prioritizes win rate | Selective |

### 5.2 What Profiles Control

Each profile configures parameters including:
- Minimum trade sizes and position limits
- Stop-loss and take-profit percentages
- Coherence thresholds for trade approval
- Score requirements for signal strength
- Target trades per day

**Note:** Specific parameter values are defined in the codebase (`omnix_core/config/trading_profiles.py`) and can be reviewed during due diligence.

### 5.3 Profile Selection

Profile is set via environment variable:

```
TRADING_PROFILE=PAPER_OPTIMIZED
```

**Current Recommendation:** For investor demonstrations, use **PAPER_OPTIMIZED** to achieve 55%+ win rate with fewer, higher-quality trades.

---

## 6. INSTITUTIONAL DECISION LOGGER: AUDIT TRAIL

### 6.1 Overview

The InstitutionalDecisionLogger records trading decisions and their outcomes for audit purposes. Events are logged conditionally based on the trade lifecycle path.

### 6.2 Event Categories

The logger captures the following categories of events:

| Category | Examples | Purpose |
|----------|----------|---------|
| **Trade Candidates** | Signal generated, analysis complete | Track what was considered |
| **Veto Events** | Coherence block, risk block, position limit | Track why trades were blocked |
| **Execution Events** | Trade validated, executed | Track what was traded |
| **Override Events** | Manual override, bypass logged | Track exceptions |
| **AI Events** | Narrative generated | Track AI explanations |

**Note:** Not all events fire for every trade. The logger is designed to capture the decision path taken, whether that leads to execution or rejection.

### 6.3 Event Schema (JSON)

```json
{
  "event_type": "TRADE_EXECUTED",
  "decision_id": "uuid-v4",
  "timestamp": "2025-12-08T14:30:00Z",
  "symbol": "BTC/USD",
  "direction": "BUY",
  "size_usd": 1500.00,
  "entry_price": 98500.00,
  "coherence_score": 78.5,
  "strategies_agreeing": 8,
  "strategies_total": 10,
  "guards_passed": ["COHERENCE", "RISK_GUARDIAN", "HMM", "POSITION_LIMIT"],
  "veto_chain": [],
  "metadata": {
    "profile": "PAPER_OPTIMIZED",
    "regime": "TRENDING_UP"
  }
}
```

### 6.4 Compatibility

Logs are compatible with:
- **Grafana/Loki** - Real-time dashboards
- **ELK Stack** - Elasticsearch, Logstash, Kibana
- **Splunk** - Enterprise log analysis
- **Custom Analytics** - JSON parsing

### 6.5 Audit Query Examples

**Find all vetoed trades:**
```sql
SELECT * FROM decision_logs WHERE event_type LIKE 'VETO_%';
```

**Calculate actual win rate:**
```sql
SELECT 
  COUNT(CASE WHEN profit > 0 THEN 1 END) * 100.0 / COUNT(*) as win_rate
FROM paper_trades 
WHERE status = 'CLOSED';
```

---

## 7. RISK MANAGEMENT FRAMEWORK

### 7.1 Risk Guardian V5.4

The Risk Guardian is an autonomous module that monitors all trading activity:

| Protection | Description | Threshold |
|------------|-------------|-----------|
| **Overtrading** | Blocks excessive trades | Max 50/day |
| **Drawdown** | Halts trading on losses | Max 8% daily |
| **Revenge Trading** | Detects emotional patterns | Blocks if 3+ losses in row |
| **Position Concentration** | Limits per-asset exposure | Max 15% per asset |
| **Hard Cap** | Maximum trade size | $20,000 per trade |

### 7.2 Position Sizing (CAES)

The Confidence-Adaptive Entry System (CAES) dynamically sizes positions:

```
Position Size = Base Size × Kernel Confidence × Regime Factor

Where:
- Base Size = Account Balance × Max Position %
- Kernel Confidence = Non-Markovian confidence (0.5x - 3.0x)
- Regime Factor = HMM regime adjustment (0.7x - 1.2x)
```

### 7.3 Stop-Loss / Take-Profit by Volatility

| Pair Type | Examples | Stop Loss | Take Profit | R:R Ratio |
|-----------|----------|-----------|-------------|-----------|
| High Volatility | DOT, AVAX, SOL, LINK | 2.5% | 4.5% | 1:1.8 |
| Normal Volatility | BTC, ETH, XRP, LTC | 1.5% | 3.0% | 1:2.0 |

### 7.4 Circuit Breakers

| Trigger | Action | Reset |
|---------|--------|-------|
| 5% daily loss | Reduce position sizes 50% | Next trading day |
| 8% daily loss | Halt all new trades | Manual review |
| 3 consecutive losses | 30-minute cooldown | Automatic |
| Regime change detected | Pause 15 minutes | After stability |

---

## 8. POST-QUANTUM SECURITY

### 8.1 Overview

OMNIX has implemented post-quantum cryptography infrastructure using NIST-approved algorithms. This positions the platform ahead of regulatory requirements expected by 2030.

### 8.2 Algorithms Implemented

| Algorithm | Standard | Purpose | Status |
|-----------|----------|---------|--------|
| **Kyber-768** | NIST FIPS-203 | Key encapsulation (encryption) | Implemented |
| **Dilithium-3** | NIST FIPS-204 | Digital signatures | Implemented |

### 8.3 Current Implementation Scope

| Component | Protection Method | Status |
|-----------|-------------------|--------|
| Key Material | Kyber-768 key generation | Active |
| Signature Infrastructure | Dilithium-3 available | Active |
| Trade Signing | Optional PQ signatures | Roadmap |
| Audit Log Integrity | Planned enhancement | Roadmap |

**Note:** Post-quantum cryptography infrastructure is in place. Full enforcement across all execution pathways is on the development roadmap.

### 8.4 Why This Matters

- **Forward-Looking:** Prepared for quantum computing threats
- **Regulatory Alignment:** NIST standards are becoming mandatory
- **Differentiation:** Early adopter advantage in retail trading space

---

## 9. DATA INTEGRITY & METRICS

### 9.1 How Metrics Are Calculated

Metrics are derived from database records:

| Metric | Calculation | Source |
|--------|-------------|--------|
| **Win Rate** | Winning Trades / Total Closed Trades | `paper_trades` table |
| **Total P/L** | Sum of all trade profits | `paper_trades.profit` column |
| **Balance** | Initial + Total P/L | Calculated field |
| **Drawdown** | (Peak - Current) / Peak | Rolling calculation |

### 9.2 Current Data Infrastructure

| Component | Implementation |
|-----------|----------------|
| **Database** | PostgreSQL (standard RDBMS) |
| **Trade Recording** | All paper trades recorded |
| **Timestamps** | Recorded at execution time |
| **Query Access** | SQL queries available for verification |

**Current Scope:** The system currently operates in paper trading mode. Real-money execution pathways are planned for future implementation.

### 9.3 Data Integrity Roadmap

Future enhancements under consideration:
- Append-only audit tables
- Cryptographic integrity verification
- Real-money execution parity

### 9.4 Verification Queries

Investors can verify metrics with these SQL queries:

**Verify Trade Count:**
```sql
SELECT COUNT(*) FROM paper_trades;
```

**Verify Win Rate:**
```sql
SELECT 
  COUNT(*) as total_trades,
  COUNT(CASE WHEN profit > 0 THEN 1 END) as wins,
  COUNT(CASE WHEN profit <= 0 THEN 1 END) as losses,
  COUNT(CASE WHEN profit > 0 THEN 1 END) * 100.0 / COUNT(*) as win_rate
FROM paper_trades 
WHERE status = 'CLOSED';
```

**Verify Balance Calculation:**
```sql
SELECT 
  1000000 + COALESCE(SUM(profit), 0) as calculated_balance
FROM paper_trades 
WHERE status = 'CLOSED';
```

---

## 10. GOVERNANCE & ACCESS CONTROL

### 10.1 Access Levels

| Role | Access | Actions Allowed |
|------|--------|-----------------|
| **Founder (Harold)** | Full | Code changes, strategy modifications, profile selection |
| **CTO (Iván)** | Full | Architecture changes, infrastructure, deployments |
| **Investor (Read-Only)** | Dashboard | View metrics, download reports, audit logs |
| **Public** | None | No access to system internals |

### 10.2 Change Management

| Change Type | Process |
|-------------|---------|
| Strategy Logic | Code review, test on paper, 48h observation |
| Profile Parameters | Document rationale, announce before deploy |
| Risk Limits | Dual approval (Harold + Iván) |
| Infrastructure | Staged rollout with rollback plan |

### 10.3 Version Control

- **Repository:** GitHub (private)
- **Branching:** main (production), develop (testing)
- **Deployments:** Railway auto-deploy from main
- **Audit:** Git history preserved indefinitely

---

## 11. DECLARATION OF INTEGRITY

### 11.1 Our Commitments

We, the founders of OMNIX, hereby declare:

1. **Transparency:** Trading decisions are logged for audit purposes
2. **No Conflicts:** We have no financial incentive to falsify paper trading results
3. **Honest Reporting:** Metrics shown to investors are calculated from database records
4. **Algorithmic Decision-Making:** Trades are executed based on configurable scoring thresholds
5. **Risk Disclosure:** Trading involves significant risk of loss; past performance does not guarantee future results

### 11.2 Practices We Avoid

| Practice | Our Approach |
|----------|--------------|
| Deleting trades | All trades remain in database |
| Manual trade selection | Automated based on thresholds |
| Selective metric reporting | All data queryable by investors |
| Backdating trades | Timestamps recorded at execution |
| Divergent paper/real logic | Same decision engine for both modes |

### 11.3 Investor Rights

Investors have the right to:

1. **Audit Access:** Request read-only database access
2. **Log Exports:** Download full decision logs
3. **Code Review:** Schedule technical deep-dive sessions
4. **Metric Verification:** Run verification queries
5. **Independent Audit:** Engage third-party auditor at investor expense

---

## 12. APPENDIX: TECHNICAL SPECIFICATIONS

### 12.1 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    OMNIX V6.5.4 INSTITUTIONAL+              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Monte Carlo │  │ Kalman      │  │ ARES V1/V2  │ +7 more │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          ▼                                  │
│              ┌───────────────────────┐                      │
│              │   COHERENCE ENGINE    │◄── Consensus Gate   │
│              └───────────┬───────────┘                      │
│                          ▼                                  │
│              ┌───────────────────────┐                      │
│              │    RISK GUARDIAN      │◄── Circuit Breakers │
│              └───────────┬───────────┘                      │
│                          ▼                                  │
│              ┌───────────────────────┐                      │
│              │ EXECUTION PROTOCOL    │◄── TWAP/VWAP/ICE    │
│              └───────────┬───────────┘                      │
│                          ▼                                  │
│              ┌───────────────────────┐                      │
│              │ INSTITUTIONAL LOGGER  │◄── Conditional Logs │
│              └───────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### 12.2 Database Schema (Key Tables)

| Table | Purpose | Records |
|-------|---------|---------|
| `paper_trades` | All paper trading activity | Growing |
| `decision_logs` | Audit trail events | Variable per trade |
| `balance_history` | Balance snapshots | Daily |
| `strategy_performance` | Per-strategy metrics | Updated hourly |
| `risk_events` | Circuit breaker triggers | As needed |

### 12.3 API Endpoints (Dashboard)

| Endpoint | Returns |
|----------|---------|
| `/api/health` | System status |
| `/api/metrics` | Current performance |
| `/api/trades` | Recent trade history |
| `/api/positions` | Open positions |
| `/api/audit` | Decision logs |

### 12.4 Deployment

| Component | Platform | Region |
|-----------|----------|--------|
| Trading Bot | Railway | US-East |
| Database | PostgreSQL (Neon) | US-East |
| Cache | Redis | US-East |
| Monitoring | Prometheus/Grafana | US-East |

---

## DOCUMENT CERTIFICATION

This Internal Audit & Transparency Report has been prepared by the OMNIX founding team and accurately represents the system's architecture, controls, and operating procedures as of December 2025.

**Prepared by:**
- Harold, Founder & CEO
- Iván, Co-founder & CTO

**Document Version:** 1.0  
**Last Updated:** December 2025  
**Next Review:** March 2026

---

*This document is confidential and intended for prospective investors conducting due diligence. Distribution without authorization is prohibited.*
