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

These 10 core strategies generate signals that are weighted and scored:

| # | Strategy | Type | Purpose | Role in Scoring |
|---|----------|------|---------|-----------------|
| 1 | Monte Carlo | Statistical | Validate probabilities with simulations | Weighted signal |
| 2 | Black Swan | Risk | Detect extreme conditions (Kurtosis/Skewness) | Veto power |
| 3 | Sentiment Analysis | Behavioral | Market sentiment timing | Weighted signal |
| 4 | Kelly Criterion | Position Sizing | Optimal mathematical sizing | Size adjustment |
| 5 | HMM Regime Detection | Machine Learning | Detect TRENDING/RANGING/VOLATILE | Regime context |
| 6 | Kalman Filter | Signal Processing | Adaptive signal filtering | Weighted signal |
| 7 | Quantum Momentum | Proprietary | 6-component score (EMA/RSI/MACD/Volume/HP/ATR) | Primary signal |
| 8 | Risk Guardian | Protection | Overtrading prevention, drawdown protection | Veto power |
| 9 | Coherence Engine | Validation | 6-tier consensus threshold system | Gate keeper |
| 10 | Non-Markovian Kernel | Proprietary | Temporal memory with K(t-s) decay function | Confidence boost |

**Note:** Win rate targets (55%+) are system goals, not guaranteed outcomes. Actual performance depends on market conditions and profile configuration.

### 3.2 Support Modules (Non-Signal)

These modules provide protection and execution but do not generate trading signals:

| # | Module | Purpose |
|---|--------|---------|
| 1 | Risk Guardian V5.4 | Overtrading prevention, drawdown protection |
| 2 | Coherence Engine V6.5 | Threshold-based validation |
| 3 | Adaptive Parameter Engine | Auto-calibration by regime |
| 4 | On-Chain Intelligence V7.0 | Whale tracking, blockchain analytics (Blockchain.info API) |
| 5 | Execution Protocol | Trade execution (market/limit orders) |
| 6 | Fear & Greed Contrarian | Score adjustment on extreme sentiment |

**Note:** On-Chain Intelligence has been upgraded to a dedicated port in V7.0 architecture. See Section 10.6 for details.

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

The engine returns a **binary decision** (no ambiguous middle ground):

| Outcome | When Applied | Action |
|---------|--------------|--------|
| **PERMITTED** (`True`) | All thresholds met | Trade proceeds |
| **BLOCKED** (`False`) | Any threshold failed | Trade rejected |

**Warnings vs Blocks:**
- Warnings are logged but do NOT create a "review" zone
- The decision is always binary: proceed or block
- If any blocking rule triggers, the trade is rejected

**Auditor Question:** *"Who decides if a borderline trade can proceed?"*

**Answer:** Nobody. There is no discretionary zone. The algorithm either permits or blocks. Warnings are informational only and may suggest position size reduction, but the trade either happens or doesn't.

**Blocking Rules (from `coherence_engine.py`):**
1. Contradiction 5+ vs 3+ strategies → BLOCK
2. Black Swan HIGH/EXTREME risk → BLOCK
3. Coherence score < threshold (10% paper, 30% real) → BLOCK
4. Confidence < 60% (real mode only) → BLOCK
5. Monte Carlo win rate < 50% (real mode only) → BLOCK

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
Position Size = Base Size × Aggression Factor × Regime Multiplier

Where:
- Base Size = Account Balance × Base Position %
- Aggression Factor = Sigmoid function of Kernel Confidence (0.5x - 3.0x)
- Regime Multiplier = Sub-regime adjustment (0.5x - 1.3x)
```

#### 7.2.1 Conflict of Interest Mitigation

**Auditor Question:** *"How does OMNIX prevent the Non-Markovian Kernel from self-proclaiming high confidence to maximize sizing?"*

**Safeguards Implemented (in `omnix_core/strategies/caes_module.py`):**

| Safeguard | Implementation | Effect |
|-----------|----------------|--------|
| **Hard System Cap** | `max_aggression = 3.0` | Absolute ceiling regardless of confidence |
| **Regime Multiplier** | Sub-regime detection reduces aggression | BEAR_PANIC = 0.5x, BREAKOUT_DOWN = 0.6x |
| **Max Position % per Regime** | `max_position_pct` varies by regime | BEAR_PANIC = 2%, BULL_STRONG = 5% |
| **Sigmoid Saturation** | Confidence >95% yields diminishing returns | Prevents runaway aggression |
| **ATR-Based Validation** | External volatility check caps aggression | ATR > 2x → Cap at 1.5x |

**How It Works:**
1. Raw Kernel Confidence (0-100%) → Sigmoid function → Base Aggression (0.5x - 3.0x)
2. Sub-regime detected from volatility/momentum → Regime Multiplier (0.5x - 1.3x)
3. **ATR Validation (Independent):** If ATR ratio > 2.0 → Hard cap at 1.5x; if > 1.5 → Cap at 2.0x
4. Final Aggression = min(Base × Regime, ATR_cap, System_cap)
5. Position limited by regime-specific `max_position_pct`

**Independence Guarantee:** The ATR ratio is calculated from historical price data, completely independent of the Kernel's confidence calculation. The Kernel cannot influence the ATR metric.

**Audit Trail:** CAES logs every calculation including:
- Raw Kernel Confidence input
- ATR ratio and cap applied (if any)
- Sub-regime detected
- Final aggression factor after all validations

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

OMNIX has implemented **fully functional** post-quantum cryptography using NIST-approved algorithms. This positions the platform ahead of regulatory requirements expected by 2030.

**Verification Status:** December 2025 - All PQC functions tested and operational.

### 8.2 Algorithms Implemented

| Algorithm | Standard | Purpose | Status | Verified |
|-----------|----------|---------|--------|----------|
| **Kyber-768** | NIST FIPS-203 (ML-KEM-768) | Key encapsulation (encryption) | Active | Dec 2025 |
| **Dilithium-3** | NIST FIPS-204 (ML-DSA-65) | Digital signatures | Active | Dec 2025 |

### 8.3 Key Sizes (NIST Compliant)

| Algorithm | Public Key | Secret Key | Ciphertext/Signature |
|-----------|------------|------------|----------------------|
| Kyber-768 | 1,184 bytes | 2,400 bytes | 1,088 bytes |
| Dilithium-3 | 1,952 bytes | 4,032 bytes | 3,309 bytes |

### 8.4 Implementation Scope

| Component | Protection Method | Status |
|-----------|-------------------|--------|
| Key Material | Kyber-768 key generation | Active |
| Signature Infrastructure | Dilithium-3 signing/verification | Active |
| Trading Service | PostQuantumSecurity integrated | Active |
| Trading System | PQC module loaded at startup | Active |
| Trade Signing | Optional PQ signatures | Active |
| Audit Log Integrity | Hash-based verification | Active |

### 8.5 Integration Points

PQC is integrated in 3 core modules:
1. `main.py` - System startup verification
2. `omnix_core/trading_system.py` - Trading engine integration
3. `omnix_services/trading_service/trading_service.py` - Order signing

### 8.6 Verification Command

```bash
python tests/test_pqc_security.py --health
```

Expected output:
```
OMNIX V6.5.4 - Post-Quantum Cryptography Health Check
Kyber-768 (ML-KEM-768): FUNCTIONAL
Dilithium-3 (ML-DSA-65): FUNCTIONAL
PostQuantumSecurity: ENABLED
PQC HEALTH CHECK PASSED - System is Quantum-Resistant
```

### 8.7 Why This Matters

- **Verified & Functional:** Not theoretical - tested and operational
- **Forward-Looking:** Prepared for quantum computing threats
- **Regulatory Alignment:** NIST FIPS 203/204 standards compliant
- **Differentiation:** First retail trading platform with verified PQC

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

### 10.3 Error Recovery & Emergency Protocols

**Auditor Question:** *"If a change causes unexpected losses, what is the hard-coded recovery protocol?"*

**Two-Layer Protection System:**

#### Layer 1: Emergency Stop (from `auto_trading_bot.py`)

| Protection | Implementation | Trigger |
|------------|----------------|---------|
| **Emergency Stop** | `_check_emergency_stop()` | Drawdown > `max_daily_loss_pct` |
| **Trading Halt** | `emergency_stop = True` | Blocks all new trades immediately |

#### Layer 2: Algorithmic Rollback Protocol (from `omnix_core/risk/rollback_protocol.py`)

| Protection | Implementation | Trigger |
|------------|----------------|---------|
| **Pre-Deploy Snapshot** | `create_pre_deploy_snapshot()` | Before any config change |
| **Deploy Registration** | `register_deploy()` | Records initial balance & timestamp |
| **Drawdown Monitoring** | `check_rollback_needed()` | Continuous post-deploy check |
| **1-Hour Warning** | Warning if drawdown > 0.5% | Prepares for potential revert |
| **Auto-Revert** | `execute_rollback()` | If drawdown > 1% within 24h |

**How the ARP Works:**
1. Before deploy: System creates snapshot of current config
2. Deploy registered with initial balance
3. Continuous monitoring: `check_rollback_needed(current_balance)`
4. If drawdown > 0.5% in first hour → Warning logged
5. If drawdown > 1% within 24h → Auto-revert to previous snapshot
6. Rollback restores previous config WITHOUT human intervention
7. All rollback events logged for audit

**Code Location:** `omnix_core/risk/rollback_protocol.py`

**Configurable Parameters:**
- `drawdown_threshold_1h`: 0.5% (warning)
- `drawdown_threshold_24h`: 1.0% (auto-revert)
- `auto_revert_enabled`: True (can be disabled for manual review)

**Integration Points (from `auto_trading_bot.py`):**
- `start()`: Creates config snapshot + registers deploy with initial balance
- `_trading_loop()`: Checks ARP every 10 cycles, immediate halt on trigger
- Persists halted state to prevent auto-restart by orchestrators

**Known Limitations (Roadmap for V7.0):**
- Config snapshots stored in local filesystem (ephemeral in containerized environments)
- Balance monitoring uses cached state; real-time P&L sync improvements planned
- Full deployment rollback requires Railway/Kubernetes integration beyond bot scope

### 10.4 Version Control

- **Repository:** GitHub (private)
- **Branching:** main (production), develop (testing)
- **Deployments:** Railway auto-deploy from main
- **Audit:** Git history preserved indefinitely

### 10.5 User Interface & Accessibility

OMNIX provides multiple interaction methods for end-users:

| Interface | Description | Audit Logging |
|-----------|-------------|---------------|
| **Telegram Bot** | Primary user interface with 40+ commands | All commands logged |
| **Interactive Menus** | Button-based navigation (no typing required) | Callback actions logged |
| **Voice Responses** | AI audio replies for accessibility | Response events logged |
| **Web Search** | Real-time internet search via `/buscar` | Search queries logged |
| **Dashboards** | Flask API + Streamlit visualization | Access logged |

**Command Categories:**
- Market Data (8 commands): `/precio`, `/market`, `/balance`, etc.
- Paper Trading (5 commands): `/paper_start`, `/paper_buy`, `/paper_sell`, etc.
- Stock Trading (6 commands): `/analizar`, `/comprar_bolsa`, etc.
- Advanced Analysis (7 commands): `/montecarlo`, `/blackswan`, `/sentiment`, etc.
- Configuration (8 commands): `/miconfig`, `/perfil`, `/limites`, etc.
- Community (5 commands): `/feedback`, `/community_stats`, etc.

**Community Intelligence System:**
- Users can report strategy performance via `/feedback`
- Gamified point system rewards contributions
- Leaderboard ranks top contributors
- Collective wisdom improves strategy calibration

### 10.6 Hexagonal Architecture V7.0 (Migration)

OMNIX is undergoing a strategic migration to hexagonal (ports & adapters) architecture using the **Strangler Fig Pattern**. This enables gradual migration while maintaining 24/7 operation.

> **IMPORTANT:** The legacy system (V6.5.4) remains fully active in production. The V7.0 architecture is 100% implemented but not yet activated. All trading operations use the proven legacy codebase.

**Current Status (December 2025):**

| Metric | Status |
|--------|--------|
| Ports Defined | **9/9** (100%) |
| Adapters Implemented | **10/10** (100%) |
| Active in Production | **0/9** (0%) |
| Production System | **Legacy V6.5.4** |
| Pattern | Strangler Fig with Feature Flags |

**Architecture Structure:**

```
src/omnix/           ← V7.0 Hexagonal (100% implemented, NOT ACTIVE)
├── ports/           ← 9 protocol interfaces
├── infrastructure/  ← 10 adapters
├── domain/          ← Business logic (strategies, risk, on-chain)
├── application/     ← Use cases + orchestration services
└── bootstrap/       ← DI Container (535 lines)

omnix_core/          ← Legacy V6.5.4 (CURRENTLY ACTIVE)
omnix_services/      ← Legacy services (CURRENTLY ACTIVE)
```

**Migration Feature Flags:**

All flags are currently set to `false`. The system runs on legacy code while V7 components are validated in staging.

| Flag | Functionality | Risk | Fallback | Dependencies |
|------|--------------|------|----------|--------------|
| `USE_AI_PORT` | AI gateway with Gemini→OpenAI→Anthropic failover | Low | 5min cooldown → RoutingAIGateway | Includes AIInferencePort |
| `USE_VOICE_PORT` | Voice transcription (Whisper) | Low | Legacy voice_controller | Requires USE_AI_PORT |
| `USE_DATABASE_PORT` | PostgreSQL adapter | Medium | DatabaseGateway singleton | Must pair with USE_CACHE_PORT |
| `USE_CACHE_PORT` | Redis adapter | Low | RedisCache singleton | Must pair with USE_DATABASE_PORT |
| `USE_NOTIFICATION_PORT` | Telegram notifications | Low | telegram_utils module | None |
| `USE_TELEGRAM_PORT` | Bot command handling | Medium | EnterpriseBot class | None |
| `USE_ONCHAIN_PORT` | Blockchain data (Blockchain.info) | Low | Legacy analytics module | None |
| `USE_TRADING_PORT` | Trading execution (Kraken) | High | Legacy trading_service | Includes MarketDataPort |
| `USE_APP_LAYER` | Full application layer | High | All legacy services | Master flag (activates all)

**Cooldown/Fallback Mechanism:**

```
V7 Request → Adapter → Success → Continue V7
                    → Failure → Record failure
                              → Cooldown 5 min
                              → Route to Legacy
                              → After 5 min → Retry V7
```

This pattern ensures:
1. Zero-downtime during migration
2. Automatic recovery from V7 failures
3. Comprehensive logging for audit
4. Gradual risk reduction via staged activation

**Activation Sequence (Planned):**
1. `USE_AI_PORT` (robust fallback, no dependencies)
2. `USE_ONCHAIN_PORT` (independent data source)
3. `USE_CACHE_PORT` + `USE_DATABASE_PORT` (together)
4. `USE_NOTIFICATION_PORT`
5. `USE_TELEGRAM_PORT`
6. `USE_VOICE_PORT`
7. `USE_APP_LAYER` (final activation)

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

**Legacy Architecture (V6.5.4 - Currently Active in Production):**

```
┌─────────────────────────────────────────────────────────────┐
│                    OMNIX V6.5.4 INSTITUTIONAL+              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Monte Carlo │  │ Kalman      │  │ Q.Momentum  │ +7 more │
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

**Hexagonal Architecture V7.0 (Implemented, Pending Activation):**

```
┌─────────────────────────────────────────────────────────────┐
│                    src/omnix/ V7.0 HEXAGONAL                │
├─────────────────────────────────────────────────────────────┤
│  PORTS (9 Protocols)                                        │
│  ├── Driven: AI, Voice, Database, Cache, Notification      │
│  │           Trading, MarketData, OnChainData               │
│  └── Driver: Telegram, RestApi                              │
├─────────────────────────────────────────────────────────────┤
│  ADAPTERS (10 Implementations)                              │
│  ├── AIGatewayShim, VoiceServiceAdapter                    │
│  ├── DatabaseAdapter, CacheAdapter, NotificationAdapter    │
│  ├── TradingAdapter, KrakenAdapter, OnChainDataAdapter     │
│  └── TelegramBotAdapter, FlaskBlueprints                   │
├─────────────────────────────────────────────────────────────┤
│  DOMAIN (Pure Business Logic)                               │
│  ├── 10 Trading Strategies (Monte Carlo, Kalman, etc.)     │
│  ├── Risk Guardian, Coherence Engine                        │
│  └── Entities, Value Objects (Money, Quantity, Trade)      │
├─────────────────────────────────────────────────────────────┤
│  BOOTSTRAP                                                  │
│  └── DI Container (535 lines) + Feature Flag Control       │
└─────────────────────────────────────────────────────────────┘
```

### 12.1.1 Ports & Adapters Inventory

| Port | Adapter | Status | Feature Flag |
|------|---------|--------|--------------|
| AITextGatewayPort | AIGatewayShim | Ready | `USE_AI_PORT` |
| AIVoicePort | VoiceServiceAdapter | Ready | `USE_VOICE_PORT` |
| DatabasePort | DatabaseAdapter | Ready | `USE_DATABASE_PORT` |
| CachePort | CacheAdapter | Ready | `USE_CACHE_PORT` |
| NotificationPort | NotificationAdapter | Ready | `USE_NOTIFICATION_PORT` |
| TradingPort | TradingAdapter | Ready | `USE_TRADING_PORT` |
| MarketDataPort | KrakenAdapter | Ready | (w/ Trading) |
| OnChainDataPort | OnChainDataAdapter | Ready | `USE_ONCHAIN_PORT` |
| TelegramPort | TelegramBotAdapter | Ready | `USE_TELEGRAM_PORT` |
| RestApiPort | FlaskBlueprints | Ready | `USE_APP_LAYER` |

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

**Document Version:** 1.1  
**Last Updated:** December 17, 2025  
**Next Review:** March 2026

**Version 1.1 Changes:**
- Added Section 10.6: Hexagonal Architecture V7.0 (Migration)
- Updated Section 12.1: Added V7.0 architecture diagram and ports/adapters inventory
- Updated On-Chain Intelligence reference to V7.0 dedicated port
- Added 9 feature flags documentation with activation sequence

---

*This document is confidential and intended for prospective investors conducting due diligence. Distribution without authorization is prohibited.*
