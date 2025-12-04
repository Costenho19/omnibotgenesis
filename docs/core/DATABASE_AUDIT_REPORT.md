# OMNIX V6.5.2 Database - Audit Report

> **Document:** Database Audit & Defect Analysis Report  
> **Location:** `docs/core/DATABASE_AUDIT_REPORT.md`  
> **Last Updated:** December 2025  
> **Status:** Analysis Complete  
> **Purpose:** Comprehensive database audit for institutional investors and technical debt reduction

---

## Document Scope

This audit report provides exhaustive analysis of the OMNIX database system including:

- **Schema Inventory**: 45 tables in production vs 44 documented
- **Integrity Analysis**: Foreign keys, constraints, and orphan tables
- **Redundancy Detection**: Duplicate tables, overlapping functionality
- **Service Duplication**: Multiple DB access patterns causing inconsistencies
- **Query Analysis**: Duplicate queries across endpoints
- **Remediation Plan**: Prioritized fixes with impact assessment

---

## 1. Executive Summary

### 1.1 Key Findings

| Category | Finding | Severity | Impact |
|----------|---------|----------|--------|
| Schema Drift | 45 tables exist vs 44 documented | 🟠 HIGH | Documentation out of sync |
| Undocumented Tables | 14 tables not in DATABASE.md | 🔴 CRITICAL | Audit trail incomplete |
| Missing Tables | 5 documented tables don't exist | 🟡 MEDIUM | Documentation inaccurate |
| Foreign Keys | Only 8 of 45 tables have FKs | 🔴 CRITICAL | Data integrity at risk |
| Duplicate Tables | 3 pairs of redundant tables | 🟠 HIGH | Confusion and waste |
| Service Duplication | 2 parallel DB services | 🔴 CRITICAL | Connection pool conflicts |
| Query Duplication | Same metrics calculated 3+ ways | 🟠 HIGH | Inconsistent data |

### 1.2 Statistics

| Metric | Value |
|--------|-------|
| Total Tables | 45 |
| Documented Tables | 44 |
| Foreign Keys | 8 |
| Indexes | 59 |
| Tables with user_id | 42 |
| Tables with FK to users | 8 (19%) |

---

## 2. Schema Inventory

### 2.1 Tables by Category (Actual Production)

| Category | Count | Tables |
|----------|-------|--------|
| Core Trading | 5 | trades, paper_trading_trades, paper_trading_balances, trading_history, balance_history |
| User Management | 4 | users, user_settings, user_contacts, user_contributions |
| AI & Conversations | 3 | ai_interactions, conversations, conversation_memory |
| Risk Management | 9 | risk_alerts, risk_events, risk_limits, risk_limit_breaches, risk_guardian_events, risk_guardian_logs, risk_metrics_snapshots, limit_checks, memory_risk_patterns |
| Derivatives | 6 | derivatives_orders, perpetual_positions, funding_payments, funding_arbitrage, hedge_positions, margin_calls |
| Community | 5 | community_feedback, community_signals, strategy_votes, improvement_proposals, user_rewards |
| Arbitrage | 1 | arbitrage_opportunities |
| Circuit Breakers | 2 | circuit_breaker_states, circuit_breaker_status |
| Snapshots | 3 | audited_snapshots, position_snapshots, risk_metrics_snapshots |
| Patterns | 2 | detected_patterns, pending_evaluations |
| Trade Analysis | 2 | trade_evaluations, trade_reasonings |
| System | 3 | schema_migrations, system_config, whatsapp_messages |
| **TOTAL** | **45** | |

### 2.2 Documentation Gap Analysis

#### Tables NOT Documented (14)

| Table | Columns | Purpose (Inferred) | Priority |
|-------|---------|-------------------|----------|
| `ai_interactions` | 9 | AI model usage tracking | 🟠 HIGH |
| `arbitrage_opportunities` | 13 | Cross-exchange arbitrage | 🟡 MEDIUM |
| `circuit_breaker_states` | 8 | Circuit breaker state machine | 🔴 CRITICAL |
| `funding_arbitrage` | 11 | Funding rate arbitrage | 🟡 MEDIUM |
| `funding_payments` | 7 | Funding rate payments log | 🟡 MEDIUM |
| `hedge_positions` | 10 | Spot-perp hedging | 🟡 MEDIUM |
| `limit_checks` | 8 | Risk limit validation log | 🟠 HIGH |
| `margin_calls` | 9 | Margin call events | 🔴 CRITICAL |
| `memory_risk_patterns` | 7 | Non-Markovian risk patterns | 🟠 HIGH |
| `risk_events` | 9 | General risk events | 🟠 HIGH |
| `risk_guardian_logs` | 6 | Risk guardian action log | 🟠 HIGH |
| `risk_metrics_snapshots` | 10 | Risk metrics over time | 🟠 HIGH |
| `system_config` | 5 | System configuration | 🟡 MEDIUM |
| `user_rewards` | 7 | User reward tracking | 🟡 MEDIUM |

#### Documented but Missing (5)

| Table | Documented In | Reality |
|-------|---------------|---------|
| `analysis` | DATABASE.md | Does not exist |
| `sharia_validations` | DATABASE.md | Does not exist |
| `video_transcript_cache` | DATABASE.md | Does not exist |
| `alpha_leaderboard` | DATABASE.md | Does not exist |
| `signal_executions` | DATABASE.md | Does not exist |

---

## 3. Schema Details (All 45 Tables)

### 3.1 Core Trading Tables

#### `paper_trading_trades` (13 columns) - PRIMARY
```
id (integer) PRIMARY KEY
user_id (varchar) 
symbol (varchar) NOT NULL
side (varchar) NOT NULL
quantity (numeric) NOT NULL
entry_price (numeric) NOT NULL
exit_price (numeric)
profit_loss (numeric)
profit_pct (numeric)
strategy (varchar)
status (varchar) DEFAULT 'open'
opened_at (timestamp)
closed_at (timestamp)
```
**Issue**: No FK to users despite `user_id` column

#### `paper_trading_balances` (15 columns)
```
id (integer) PRIMARY KEY
user_id (text) NOT NULL UNIQUE
balance_usd (numeric) DEFAULT 1000000.00
btc_balance (numeric) DEFAULT 0
eth_balance (numeric) DEFAULT 0
total_trades (integer) DEFAULT 0
winning_trades (integer) DEFAULT 0
losing_trades (integer) DEFAULT 0
total_realized_pnl_usd (numeric) DEFAULT 0
total_unrealized_pnl_usd (numeric) DEFAULT 0
available_margin_usd (numeric) DEFAULT 1000000.00
max_drawdown_pct (numeric) DEFAULT 0
sharpe_ratio (numeric) DEFAULT 0
created_at (timestamptz)
updated_at (timestamptz)
```
**Issue**: Uses `text` for user_id while others use `varchar`

#### `trading_history` (15 columns) - REDUNDANT WITH paper_trading_trades
```
id (integer) PRIMARY KEY
user_id (varchar) FK → users
trade_type (varchar)
symbol (varchar) NOT NULL
entry_price (numeric)
exit_price (numeric)
quantity (numeric)
profit_loss (numeric)
profit_percentage (numeric)
strategy (varchar)
notes (text)
status (varchar)
opened_at (timestamp)
closed_at (timestamp)
created_at (timestamp)
```
**Issue**: Nearly identical to `paper_trading_trades` - redundant

#### `trades` (12 columns) - EXCHANGE TRADES
```
id (integer) PRIMARY KEY
user_id (varchar)
symbol (varchar) NOT NULL
side (varchar) NOT NULL
quantity (numeric) NOT NULL
price (numeric) NOT NULL
total (numeric)
fee (numeric)
order_id (varchar)
exchange (varchar)
status (varchar)
executed_at (timestamp)
```
**Purpose**: Real exchange order tracking (different from paper trades)

#### `balance_history` (6 columns)
```
id (integer) PRIMARY KEY
user_id (varchar) FK → users
balance (numeric) NOT NULL
change_amount (numeric)
change_reason (varchar)
recorded_at (timestamp)
```

### 3.2 User Tables

#### `users` (18 columns) - MASTER TABLE
```
user_id (varchar) PRIMARY KEY
telegram_id (bigint) UNIQUE
username (varchar)
first_name (varchar)
last_name (varchar)
language_code (varchar)
is_premium (boolean)
is_admin (boolean)
is_active (boolean)
total_profit (numeric)
total_trades (integer)
win_rate (numeric)
subscription_tier (varchar)
subscription_expires_at (timestamp)
preferences (jsonb)
created_at (timestamp)
updated_at (timestamp)
last_active_at (timestamp)
```

#### `user_settings` (25 columns) - EXTENSIVE CONFIG
```
user_id (text) PRIMARY KEY
username (text)
risk_profile (text)
trading_limits (jsonb)
protection_settings (jsonb)
notification_preferences (jsonb)
allowed_cryptos (jsonb)
allowed_stocks (jsonb)
active_strategies (jsonb)
trading_enabled (boolean)
auto_trading (boolean)
paper_trading_mode (boolean)
is_paused (boolean)
pause_reason (text)
pause_until (timestamptz)
onboarding_completed (boolean)
terms_accepted (boolean)
risk_disclosure_accepted (boolean)
daily_pnl_usd (numeric)
daily_trades_count (integer)
daily_traded_usd (numeric)
daily_stats_date (date)
weekly_pnl_usd (numeric)
created_at (timestamptz)
updated_at (timestamptz)
```
**Note**: 25 columns - largest table, stores all user preferences

### 3.3 Risk Management Tables

#### `circuit_breaker_states` vs `circuit_breaker_status` - REDUNDANT PAIR

| Aspect | `circuit_breaker_states` | `circuit_breaker_status` |
|--------|-------------------------|--------------------------|
| Columns | 8 | 9 |
| user_id | varchar | varchar |
| State | `state` varchar | `state` varchar |
| Trigger | `trigger_reason` text | `trigger_count` integer |
| Timestamps | triggered_at, reset_at | last_triggered_at, cooldown_until, updated_at |
| **Recommendation** | MERGE | Keep (more complete) |

#### `risk_guardian_events` vs `risk_guardian_logs` - REDUNDANT PAIR

| Aspect | `risk_guardian_events` | `risk_guardian_logs` |
|--------|------------------------|----------------------|
| Columns | 8 | 6 |
| Purpose | Events with severity | Action log |
| Fields | event_type, severity, description, action_taken | action_type, action_details, result |
| **Recommendation** | Keep (events) | MERGE into events |

### 3.4 Derivatives Tables

#### `derivatives_orders` (12 columns)
```
id, user_id, symbol, order_type, side, size, price, leverage, 
status, exchange_order_id, created_at, filled_at
```

#### `perpetual_positions` (13 columns)
```
id, user_id, symbol, side, size, entry_price, leverage, 
liquidation_price, margin, unrealized_pnl, status, opened_at, closed_at
```

#### `margin_calls` (9 columns) - NOT DOCUMENTED
```
id, user_id, position_id, margin_level, required_margin, 
current_margin, action_taken, created_at, resolved_at
```

---

## 4. Foreign Key Analysis

### 4.1 Existing Foreign Keys (8 total)

| Table | Column | References | On Delete |
|-------|--------|------------|-----------|
| `ai_interactions` | user_id | users.user_id | - |
| `audited_snapshots` | risk_snapshot_id | risk_metrics_snapshots.id | - |
| `balance_history` | user_id | users.user_id | - |
| `conversation_memory` | user_id | users.user_id | - |
| `performance_metrics` | user_id | users.user_id | - |
| `trading_history` | user_id | users.user_id | - |
| `user_contacts` | user_id | users.user_id | - |
| `whatsapp_messages` | user_id | users.user_id | - |

### 4.2 Missing Foreign Keys (CRITICAL)

| Table | Column | Should Reference | Priority |
|-------|--------|-----------------|----------|
| `paper_trading_trades` | user_id | users.user_id | 🔴 CRITICAL |
| `paper_trading_balances` | user_id | users.user_id | 🔴 CRITICAL |
| `trades` | user_id | users.user_id | 🔴 CRITICAL |
| `risk_alerts` | user_id | users.user_id | 🟠 HIGH |
| `risk_events` | user_id | users.user_id | 🟠 HIGH |
| `risk_limits` | user_id | users.user_id | 🟠 HIGH |
| `risk_guardian_events` | user_id | users.user_id | 🟠 HIGH |
| `perpetual_positions` | user_id | users.user_id | 🟠 HIGH |
| `derivatives_orders` | user_id | users.user_id | 🟠 HIGH |
| `community_signals` | user_id | users.user_id | 🟡 MEDIUM |
| `community_feedback` | user_id | users.user_id | 🟡 MEDIUM |
| `conversations` | user_id | users.user_id | 🟡 MEDIUM |
| `user_settings` | user_id | users.user_id | 🟡 MEDIUM |

**Impact**: Without FKs, orphan records can exist, breaking audits

---

## 5. Service Layer Duplication

### 5.1 Two Parallel Database Services

| Service | Location | Library | Purpose |
|---------|----------|---------|---------|
| Dashboard Pool | `omnix_dashboard/utils/database.py` | psycopg_pool | Dashboard API only |
| Enterprise Service | `omnix_services/database_service/database_service.py` | psycopg3 direct | Bot and core services |

**Risks**:
1. Connection pool exhaustion (both compete for connections)
2. Different failover logic
3. No transaction coordination
4. Credential handling inconsistency

### 5.2 Query Duplication Map

| Query | Location 1 | Location 2 | Location 3 |
|-------|-----------|-----------|-----------|
| Get paper trades | `queries.py:get_paper_trades()` | `core.py:api_trades()` | `snapshots.py:create_snapshot()` |
| Calculate win rate | `queries.py:calculate_metrics()` | `core.py:api_portfolio()` | `database_service.py` |
| Get balance | `queries.py:get_balance_history()` | `core.py:api_portfolio()` | `paper_trading_manager.py` |
| Count open positions | `core.py:api_metrics()` | `core.py:api_portfolio()` | `snapshots.py` |

**Issues**:
1. Different LIMIT values (500 vs unbounded)
2. Different column selections
3. Inconsistent PnL calculations
4. Different date range handling

---

## 6. Endpoint Data Overlap

### 6.1 Endpoints Returning Similar Data

| Endpoint | Data Source | Calculates | Overlap With |
|----------|-------------|------------|--------------|
| `/api/metrics` | paper_trading_trades | win_rate, sharpe, total_pnl | /api/portfolio |
| `/api/portfolio` | paper_trading_balances + trades | win_rate, sharpe, total_pnl | /api/metrics |
| `/api/trades` | paper_trading_trades | trade list | /api/positions |
| `/api/positions` | paper_trading_trades WHERE open | open trades | /api/trades |

### 6.2 Calculation Inconsistencies

| Metric | `/api/metrics` | `/api/portfolio` | Difference |
|--------|---------------|------------------|------------|
| Win Rate | From closed trades list | From paper_trading_balances.winning_trades | May differ if cache stale |
| Sharpe Ratio | Calculated from PnL array | From paper_trading_balances.sharpe_ratio | Stored vs calculated |
| Total PnL | SUM of trade.pnl | paper_trading_balances.total_realized_pnl_usd | Aggregation timing |

---

## 7. Redundant Table Analysis

### 7.1 Confirmed Redundant Pairs

| Pair | Recommendation | Migration Path |
|------|----------------|----------------|
| `circuit_breaker_states` ↔ `circuit_breaker_status` | MERGE to `circuit_breaker_status` | Copy historical states, drop _states |
| `risk_guardian_events` ↔ `risk_guardian_logs` | MERGE to `risk_guardian_events` | Add action_type column, migrate logs |
| `trading_history` ↔ `paper_trading_trades` | CONSOLIDATE | trading_history has FK, paper_trading_trades is primary |

### 7.2 Overlap Analysis

| Table A | Table B | Overlap % | Notes |
|---------|---------|-----------|-------|
| trading_history | paper_trading_trades | 80% | Same fields, different FKs |
| circuit_breaker_states | circuit_breaker_status | 70% | States is simpler |
| risk_guardian_events | risk_guardian_logs | 60% | Logs lacks severity |

---

## 8. Index Analysis

### 8.1 Existing Indexes (59 total)

| Type | Count | Examples |
|------|-------|----------|
| Primary Key | 45 | *_pkey on all tables |
| Unique | 7 | users_telegram_id, schema_migrations_migration_name |
| User ID | 8 | idx_conversations_user_id, idx_arbitrage_opportunities_user_id |
| Composite | 2 | audited_snapshots(snapshot_type, snapshot_date) |
| Partial | 2 | idx_user_settings_paused WHERE is_paused = true |

### 8.2 Missing Indexes (Recommended)

| Table | Column | Reason |
|-------|--------|--------|
| `paper_trading_trades` | user_id | High-frequency queries |
| `paper_trading_trades` | status | Filter open/closed |
| `paper_trading_trades` | opened_at | Date range queries |
| `risk_alerts` | user_id, acknowledged | Alert filtering |
| `perpetual_positions` | user_id, status | Position queries |

---

## 9. Remediation Plan

### 9.1 Phase 1: Documentation (Week 1) - LOW RISK

| Task | Priority | Effort |
|------|----------|--------|
| Document 14 undocumented tables | 🔴 CRITICAL | 4h |
| Remove 5 non-existent tables from docs | 🟠 HIGH | 1h |
| Update column types (user_id text→varchar) | 🟡 MEDIUM | 2h |
| Add index documentation | 🟡 MEDIUM | 2h |

### 9.2 Phase 2: Integrity (Week 2-3) - MEDIUM RISK

| Task | Priority | Effort | Migration Required |
|------|----------|--------|-------------------|
| Add FK: paper_trading_trades → users | 🔴 CRITICAL | 2h | Yes |
| Add FK: paper_trading_balances → users | 🔴 CRITICAL | 2h | Yes |
| Add FK: trades → users | 🔴 CRITICAL | 2h | Yes |
| Add 10 secondary FKs | 🟠 HIGH | 4h | Yes |
| Add missing indexes | 🟡 MEDIUM | 2h | Yes |

### 9.3 Phase 3: Consolidation (Week 4) - HIGH RISK

| Task | Priority | Effort | Breaking Change |
|------|----------|--------|-----------------|
| Merge circuit_breaker tables | 🟠 HIGH | 4h | Yes - update all references |
| Merge risk_guardian tables | 🟠 HIGH | 4h | Yes - update all references |
| Consolidate trading_history | 🟡 MEDIUM | 8h | Yes - update bot code |

### 9.4 Phase 4: Service Unification (Week 5-6) - HIGH RISK

| Task | Priority | Effort | Impact |
|------|----------|--------|--------|
| Create unified MetricsRepository | 🔴 CRITICAL | 8h | All endpoints |
| Migrate dashboard to enterprise service | 🔴 CRITICAL | 8h | Dashboard |
| Centralize query functions | 🟠 HIGH | 4h | Consistency |
| Add transaction support | 🟡 MEDIUM | 4h | Data integrity |

---

## 10. Appendix: Complete Table Schema

### A. All Tables with Column Counts

| # | Table | Columns | Has FK | Has user_id |
|---|-------|---------|--------|-------------|
| 1 | ai_interactions | 9 | ✅ | ✅ |
| 2 | arbitrage_opportunities | 13 | ❌ | ✅ |
| 3 | audited_snapshots | 19 | ✅ | ✅ |
| 4 | balance_history | 6 | ✅ | ✅ |
| 5 | circuit_breaker_states | 8 | ❌ | ✅ |
| 6 | circuit_breaker_status | 9 | ❌ | ✅ |
| 7 | community_feedback | 7 | ❌ | ✅ |
| 8 | community_signals | 11 | ❌ | ✅ |
| 9 | conversation_memory | 6 | ✅ | ✅ |
| 10 | conversations | 6 | ❌ | ✅ |
| 11 | derivatives_orders | 12 | ❌ | ✅ |
| 12 | detected_patterns | 9 | ❌ | ✅ |
| 13 | funding_arbitrage | 11 | ❌ | ✅ |
| 14 | funding_payments | 7 | ❌ | ✅ |
| 15 | hedge_positions | 10 | ❌ | ✅ |
| 16 | improvement_proposals | 10 | ❌ | ✅ |
| 17 | limit_checks | 8 | ❌ | ✅ |
| 18 | margin_calls | 9 | ❌ | ✅ |
| 19 | memory_risk_patterns | 7 | ❌ | ✅ |
| 20 | paper_trading_balances | 15 | ❌ | ✅ |
| 21 | paper_trading_trades | 13 | ❌ | ✅ |
| 22 | pending_evaluations | 13 | ❌ | ✅ |
| 23 | performance_metrics | 7 | ✅ | ✅ |
| 24 | perpetual_positions | 13 | ❌ | ✅ |
| 25 | position_snapshots | 10 | ❌ | ✅ |
| 26 | risk_alerts | 8 | ❌ | ✅ |
| 27 | risk_events | 9 | ❌ | ✅ |
| 28 | risk_guardian_events | 8 | ❌ | ✅ |
| 29 | risk_guardian_logs | 6 | ❌ | ✅ |
| 30 | risk_limit_breaches | 8 | ❌ | ✅ |
| 31 | risk_limits | 8 | ❌ | ✅ |
| 32 | risk_metrics_snapshots | 10 | ❌ | ✅ |
| 33 | schema_migrations | 5 | ❌ | ❌ |
| 34 | strategy_votes | 6 | ❌ | ✅ |
| 35 | system_config | 5 | ❌ | ❌ |
| 36 | trade_evaluations | 8 | ❌ | ✅ |
| 37 | trade_reasonings | 7 | ❌ | ✅ |
| 38 | trades | 12 | ❌ | ✅ |
| 39 | trading_history | 15 | ✅ | ✅ |
| 40 | user_contacts | 7 | ✅ | ✅ |
| 41 | user_contributions | 7 | ❌ | ✅ |
| 42 | user_rewards | 7 | ❌ | ✅ |
| 43 | user_settings | 25 | ❌ | ✅ |
| 44 | users | 18 | - | ✅ |
| 45 | whatsapp_messages | 8 | ✅ | ✅ |

### B. Foreign Key Summary

**Tables with FK**: 8 (18%)  
**Tables without FK**: 37 (82%)  
**Tables with user_id but no FK**: 34 (76%)

---

## 11. Complete SQL Schema Reference

This section contains all `CREATE TABLE` statements for database replication and development reference.

### 11.1 User Management Tables

#### users
```sql
CREATE TABLE users (
    user_id VARCHAR PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    username VARCHAR,
    first_name VARCHAR,
    last_name VARCHAR,
    language_code VARCHAR,
    is_premium BOOLEAN,
    is_admin BOOLEAN,
    is_active BOOLEAN,
    total_profit NUMERIC,
    total_trades INTEGER,
    win_rate NUMERIC,
    subscription_tier VARCHAR,
    subscription_expires_at TIMESTAMP,
    preferences JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_active_at TIMESTAMP
);
```

#### user_settings
```sql
CREATE TABLE user_settings (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    risk_profile TEXT,
    trading_limits JSONB,
    protection_settings JSONB,
    notification_preferences JSONB,
    allowed_cryptos JSONB,
    allowed_stocks JSONB,
    active_strategies JSONB,
    trading_enabled BOOLEAN,
    auto_trading BOOLEAN,
    paper_trading_mode BOOLEAN,
    is_paused BOOLEAN,
    pause_reason TEXT,
    pause_until TIMESTAMPTZ,
    onboarding_completed BOOLEAN,
    terms_accepted BOOLEAN,
    risk_disclosure_accepted BOOLEAN,
    daily_pnl_usd NUMERIC,
    daily_trades_count INTEGER,
    daily_traded_usd NUMERIC,
    daily_stats_date DATE,
    weekly_pnl_usd NUMERIC,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
```

#### user_contacts
```sql
CREATE TABLE user_contacts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR REFERENCES users(user_id),
    contact_type VARCHAR NOT NULL,
    contact_value VARCHAR NOT NULL,
    is_verified BOOLEAN,
    is_primary BOOLEAN,
    created_at TIMESTAMP,
    UNIQUE(user_id, contact_type, contact_value)
);
```

#### user_contributions
```sql
CREATE TABLE user_contributions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    contribution_type VARCHAR NOT NULL,
    content TEXT,
    value NUMERIC,
    metadata JSONB,
    created_at TIMESTAMP
);
```

### 11.2 Core Trading Tables

#### paper_trading_trades
```sql
CREATE TABLE paper_trading_trades (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR,
    symbol VARCHAR NOT NULL,
    side VARCHAR NOT NULL,
    quantity NUMERIC NOT NULL,
    entry_price NUMERIC NOT NULL,
    exit_price NUMERIC,
    profit_loss NUMERIC,
    profit_pct NUMERIC,
    strategy VARCHAR,
    status VARCHAR DEFAULT 'open',
    opened_at TIMESTAMP,
    closed_at TIMESTAMP
);
```

#### paper_trading_balances
```sql
CREATE TABLE paper_trading_balances (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    balance_usd NUMERIC DEFAULT 1000000.00,
    btc_balance NUMERIC DEFAULT 0,
    eth_balance NUMERIC DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    total_realized_pnl_usd NUMERIC DEFAULT 0,
    total_unrealized_pnl_usd NUMERIC DEFAULT 0,
    available_margin_usd NUMERIC DEFAULT 1000000.00,
    max_drawdown_pct NUMERIC DEFAULT 0,
    sharpe_ratio NUMERIC DEFAULT 0,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
```

#### trades
```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR,
    symbol VARCHAR NOT NULL,
    side VARCHAR NOT NULL,
    quantity NUMERIC NOT NULL,
    price NUMERIC NOT NULL,
    total NUMERIC,
    fee NUMERIC,
    order_id VARCHAR,
    exchange VARCHAR,
    status VARCHAR,
    executed_at TIMESTAMP
);
```

#### trading_history
```sql
CREATE TABLE trading_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR REFERENCES users(user_id),
    trade_type VARCHAR,
    symbol VARCHAR NOT NULL,
    entry_price NUMERIC,
    exit_price NUMERIC,
    quantity NUMERIC,
    profit_loss NUMERIC,
    profit_percentage NUMERIC,
    strategy VARCHAR,
    notes TEXT,
    status VARCHAR,
    opened_at TIMESTAMP,
    closed_at TIMESTAMP,
    created_at TIMESTAMP
);
```

#### balance_history
```sql
CREATE TABLE balance_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR REFERENCES users(user_id),
    balance NUMERIC NOT NULL,
    change_amount NUMERIC,
    change_reason VARCHAR,
    recorded_at TIMESTAMP
);
```

### 11.3 AI & Conversation Tables

#### ai_interactions
```sql
CREATE TABLE ai_interactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR REFERENCES users(user_id),
    interaction_type VARCHAR NOT NULL,
    prompt TEXT,
    response TEXT,
    model_used VARCHAR,
    tokens_used INTEGER,
    latency_ms INTEGER,
    created_at TIMESTAMP
);
```

#### conversations
```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    language VARCHAR,
    created_at TIMESTAMP
);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);
```

#### conversation_memory
```sql
CREATE TABLE conversation_memory (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR REFERENCES users(user_id),
    role VARCHAR NOT NULL,
    content TEXT NOT NULL,
    context JSONB,
    created_at TIMESTAMP
);
```

### 11.4 Risk Management Tables

#### risk_alerts
```sql
CREATE TABLE risk_alerts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    alert_type VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    message TEXT NOT NULL,
    acknowledged BOOLEAN,
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP
);
```

#### risk_events
```sql
CREATE TABLE risk_events (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    description TEXT,
    metadata JSONB,
    resolved BOOLEAN,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP
);
```

#### risk_limits
```sql
CREATE TABLE risk_limits (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    limit_type VARCHAR NOT NULL,
    limit_value NUMERIC NOT NULL,
    current_value NUMERIC,
    is_active BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### risk_limit_breaches
```sql
CREATE TABLE risk_limit_breaches (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    limit_id INTEGER,
    limit_type VARCHAR,
    limit_value NUMERIC,
    breached_value NUMERIC,
    action_taken VARCHAR,
    created_at TIMESTAMP
);
```

#### risk_guardian_events
```sql
CREATE TABLE risk_guardian_events (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    event_type VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    description TEXT,
    action_taken VARCHAR,
    metadata JSONB,
    created_at TIMESTAMP
);
```

#### risk_guardian_logs
```sql
CREATE TABLE risk_guardian_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    action_type VARCHAR NOT NULL,
    action_details JSONB,
    result VARCHAR,
    created_at TIMESTAMP
);
```

#### risk_metrics_snapshots
```sql
CREATE TABLE risk_metrics_snapshots (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    var_daily NUMERIC,
    max_drawdown NUMERIC,
    sharpe_ratio NUMERIC,
    sortino_ratio NUMERIC,
    exposure NUMERIC,
    margin_used NUMERIC,
    metadata JSONB,
    snapshot_at TIMESTAMP
);
```

#### limit_checks
```sql
CREATE TABLE limit_checks (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    check_type VARCHAR NOT NULL,
    passed BOOLEAN NOT NULL,
    current_value NUMERIC,
    limit_value NUMERIC,
    metadata JSONB,
    checked_at TIMESTAMP
);
```

#### memory_risk_patterns
```sql
CREATE TABLE memory_risk_patterns (
    id SERIAL PRIMARY KEY,
    pattern_type VARCHAR NOT NULL,
    pattern_data JSONB NOT NULL,
    confidence NUMERIC NOT NULL,
    detected_at TIMESTAMP,
    expires_at TIMESTAMP,
    user_id VARCHAR
);
CREATE INDEX idx_memory_risk_patterns_user_id ON memory_risk_patterns(user_id);
```

### 11.5 Derivatives Tables

#### derivatives_orders
```sql
CREATE TABLE derivatives_orders (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    symbol VARCHAR NOT NULL,
    order_type VARCHAR NOT NULL,
    side VARCHAR NOT NULL,
    size NUMERIC NOT NULL,
    price NUMERIC,
    leverage NUMERIC,
    status VARCHAR,
    exchange_order_id VARCHAR,
    created_at TIMESTAMP,
    filled_at TIMESTAMP
);
```

#### perpetual_positions
```sql
CREATE TABLE perpetual_positions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    symbol VARCHAR NOT NULL,
    side VARCHAR NOT NULL,
    size NUMERIC NOT NULL,
    entry_price NUMERIC NOT NULL,
    leverage NUMERIC NOT NULL,
    liquidation_price NUMERIC,
    margin NUMERIC,
    unrealized_pnl NUMERIC,
    status VARCHAR,
    opened_at TIMESTAMP,
    closed_at TIMESTAMP
);
```

#### funding_payments
```sql
CREATE TABLE funding_payments (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    symbol VARCHAR NOT NULL,
    funding_rate NUMERIC,
    payment_amount NUMERIC,
    position_size NUMERIC,
    paid_at TIMESTAMP
);
```

#### funding_arbitrage
```sql
CREATE TABLE funding_arbitrage (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR NOT NULL,
    exchange_a VARCHAR NOT NULL,
    exchange_b VARCHAR,
    rate_a NUMERIC,
    rate_b NUMERIC,
    spread NUMERIC,
    opportunity_value NUMERIC,
    executed BOOLEAN,
    created_at TIMESTAMP,
    user_id VARCHAR
);
CREATE INDEX idx_funding_arbitrage_user_id ON funding_arbitrage(user_id);
```

#### hedge_positions
```sql
CREATE TABLE hedge_positions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    spot_symbol VARCHAR NOT NULL,
    perp_symbol VARCHAR NOT NULL,
    spot_size NUMERIC,
    perp_size NUMERIC,
    hedge_ratio NUMERIC,
    status VARCHAR,
    created_at TIMESTAMP,
    closed_at TIMESTAMP
);
```

#### margin_calls
```sql
CREATE TABLE margin_calls (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    position_id INTEGER,
    margin_level NUMERIC,
    required_margin NUMERIC,
    current_margin NUMERIC,
    action_taken VARCHAR,
    created_at TIMESTAMP,
    resolved_at TIMESTAMP
);
```

### 11.6 Community Tables

#### community_feedback
```sql
CREATE TABLE community_feedback (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    feedback_type VARCHAR NOT NULL,
    content TEXT,
    rating INTEGER,
    metadata JSONB,
    created_at TIMESTAMP
);
```

#### community_signals
```sql
CREATE TABLE community_signals (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    signal_type VARCHAR NOT NULL,
    symbol VARCHAR,
    direction VARCHAR,
    confidence NUMERIC,
    rationale TEXT,
    status VARCHAR,
    performance NUMERIC,
    created_at TIMESTAMP,
    expires_at TIMESTAMP
);
```

#### strategy_votes
```sql
CREATE TABLE strategy_votes (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    strategy_name VARCHAR NOT NULL,
    vote_type VARCHAR NOT NULL,
    comment TEXT,
    created_at TIMESTAMP
);
```

#### improvement_proposals
```sql
CREATE TABLE improvement_proposals (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    proposal_type VARCHAR,
    title VARCHAR,
    description TEXT,
    expected_impact TEXT,
    status VARCHAR,
    votes INTEGER,
    created_at TIMESTAMP,
    reviewed_at TIMESTAMP
);
```

#### user_rewards
```sql
CREATE TABLE user_rewards (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    reward_type VARCHAR NOT NULL,
    amount NUMERIC,
    reason TEXT,
    metadata JSONB,
    created_at TIMESTAMP
);
```

### 11.7 Arbitrage Table

#### arbitrage_opportunities
```sql
CREATE TABLE arbitrage_opportunities (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR NOT NULL,
    buy_exchange VARCHAR NOT NULL,
    sell_exchange VARCHAR,
    buy_price NUMERIC,
    sell_price NUMERIC,
    spread_pct NUMERIC,
    volume_available NUMERIC,
    executed BOOLEAN,
    profit NUMERIC,
    detected_at TIMESTAMP,
    executed_at TIMESTAMP,
    user_id VARCHAR
);
CREATE INDEX idx_arbitrage_opportunities_user_id ON arbitrage_opportunities(user_id);
```

### 11.8 Circuit Breaker Tables

#### circuit_breaker_states
```sql
CREATE TABLE circuit_breaker_states (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    breaker_type VARCHAR NOT NULL,
    state VARCHAR NOT NULL,
    trigger_reason TEXT,
    triggered_at TIMESTAMP,
    reset_at TIMESTAMP,
    metadata JSONB
);
```

#### circuit_breaker_status
```sql
CREATE TABLE circuit_breaker_status (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    breaker_name VARCHAR NOT NULL,
    state VARCHAR NOT NULL,
    trigger_count INTEGER,
    last_triggered_at TIMESTAMP,
    cooldown_until TIMESTAMP,
    metadata JSONB,
    updated_at TIMESTAMP
);
```

### 11.9 Snapshots & Analysis Tables

#### audited_snapshots
```sql
CREATE TABLE audited_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_type VARCHAR NOT NULL,
    snapshot_date DATE NOT NULL,
    total_equity NUMERIC NOT NULL,
    total_pnl NUMERIC NOT NULL,
    open_positions_count INTEGER,
    closed_trades_count INTEGER,
    win_rate NUMERIC,
    sharpe_ratio NUMERIC,
    max_drawdown NUMERIC,
    data_json JSONB NOT NULL,
    checksum_sha256 VARCHAR NOT NULL,
    previous_checksum VARCHAR,
    created_at TIMESTAMP,
    verified_at TIMESTAMP,
    verification_status VARCHAR,
    user_id VARCHAR,
    position_snapshot_ids INTEGER[],
    risk_snapshot_id INTEGER REFERENCES risk_metrics_snapshots(id),
    UNIQUE(snapshot_type, snapshot_date)
);
```

#### position_snapshots
```sql
CREATE TABLE position_snapshots (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    symbol VARCHAR NOT NULL,
    position_size NUMERIC,
    entry_price NUMERIC,
    current_price NUMERIC,
    unrealized_pnl NUMERIC,
    margin_used NUMERIC,
    leverage NUMERIC,
    snapshot_at TIMESTAMP
);
```

#### detected_patterns
```sql
CREATE TABLE detected_patterns (
    id SERIAL PRIMARY KEY,
    pattern_type VARCHAR NOT NULL,
    symbol VARCHAR NOT NULL,
    pattern_data JSONB NOT NULL,
    confidence NUMERIC,
    timeframe VARCHAR,
    detected_at TIMESTAMP,
    expires_at TIMESTAMP,
    user_id VARCHAR
);
CREATE INDEX idx_detected_patterns_user_id ON detected_patterns(user_id);
```

#### pending_evaluations
```sql
CREATE TABLE pending_evaluations (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR,
    entity_id INTEGER,
    evaluation_type VARCHAR,
    priority INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    user_id VARCHAR,
    -- Added Dec 4, 2025 (Schema Fix)
    trade_id INTEGER,
    due_time TIMESTAMP DEFAULT NOW(),
    conditions JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending'
);
CREATE INDEX idx_pending_evaluations_user_id ON pending_evaluations(user_id);
CREATE INDEX idx_pending_evaluations_status_due_time ON pending_evaluations(status, due_time);
```
**Note**: Schema updated Dec 4, 2025 to support `DatabaseManager.get_due_evaluations()` method.

#### trade_evaluations
```sql
CREATE TABLE trade_evaluations (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER,
    user_id VARCHAR,
    evaluation_type VARCHAR,
    score NUMERIC,
    feedback TEXT,
    metrics JSONB,
    created_at TIMESTAMP
);
```

### 11.10 Trade Reasoning Table

#### trade_reasonings
```sql
CREATE TABLE trade_reasonings (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER,
    user_id VARCHAR,
    reasoning_type VARCHAR,
    content TEXT,
    confidence NUMERIC,
    created_at TIMESTAMP
);
```

### 11.11 System Tables

#### schema_migrations
```sql
CREATE TABLE schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name TEXT UNIQUE NOT NULL,
    migration_hash TEXT,
    executed_at TIMESTAMPTZ,
    success BOOLEAN
);
```

#### system_config
```sql
CREATE TABLE system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP
);
```

#### whatsapp_messages
```sql
CREATE TABLE whatsapp_messages (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR REFERENCES users(user_id),
    message_type VARCHAR NOT NULL,
    content TEXT NOT NULL,
    media_url TEXT,
    direction VARCHAR NOT NULL,
    status VARCHAR,
    created_at TIMESTAMP
);
```

#### performance_metrics
```sql
CREATE TABLE performance_metrics (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR REFERENCES users(user_id),
    metric_type VARCHAR NOT NULL,
    metric_value NUMERIC NOT NULL,
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    recorded_at TIMESTAMP
);
```

---

## 12. Connection Configuration

### Environment Variables
```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

### Connection Pool Settings (psycopg_pool)
- Min connections: 5
- Max connections: 20
- Connection timeout: 30s
- Idle timeout: 600s

---

## 13. Service Unification Implementation Plan

> **PRIORITY #1**: Consolidate dual PostgreSQL service layers before attempting schema fixes.  
> **Reason**: Two independent database stacks compete for connections, run separate migrations, and create inconsistent transaction semantics.

### 13.1 Problem Statement

OMNIX currently has **two parallel database services** operating simultaneously:

| Service | Location | Library | Pool Size | Auto-Migrations |
|---------|----------|---------|-----------|-----------------|
| Dashboard Pool | `omnix_dashboard/utils/database.py` | psycopg_pool | 2-10 | No |
| Enterprise Service | `omnix_services/database_service/database_service.py` | psycopg3 direct | No pool | **Yes (5 routines)** |

**Risks**:
1. Connection pool exhaustion (both compete for Railway's limited connections)
2. Conflicting DDL (Enterprise auto-runs schema mutations on import)
3. Inconsistent transaction semantics across trading flows
4. Any FK rollout while dual services persist could be silently undone

---

### 13.2 Call Site Mapping

#### Dashboard Pool Consumers (psycopg_pool)

| File | Function | Usage Pattern |
|------|----------|---------------|
| `omnix_dashboard/app.py` | `create_app()` | Initializes pool at startup |
| `omnix_dashboard/run.py` | Startup | Imports database module |
| `omnix_dashboard/blueprints/core.py` | All `/api/*` endpoints | `get_db_connection()` |
| `omnix_dashboard/blueprints/views.py` | Template rendering | `get_db_connection()` |
| `omnix_dashboard/blueprints/snapshots.py` | Snapshot creation | `get_db_connection()` |
| `omnix_dashboard/blueprints/system.py` | Health checks | `get_db_connection()` |
| `omnix_dashboard/utils/queries.py` | Query functions | `get_db_connection()` |

**Total**: 7 files, ~50 call sites

#### Enterprise Service Consumers (psycopg3 direct)

| File | Class/Function | Usage Pattern |
|------|----------------|---------------|
| `main.py` | Bot startup | `DatabaseServiceEnterprise()` |
| `verify_code.py` | Validation | `DatabaseServiceEnterprise()` |
| `omnix_services/telegram_service/enterprise_bot.py` | Bot commands | `db_service` instance |
| `omnix_services/monitoring/risk_guardian.py` | Risk events | `db_service` instance |
| `omnix_services/ai_service/ai_service.py` | AI interactions | `db_service` instance |
| `omnix_services/community_intelligence/*.py` | 4 modules | `db_service` instance |
| `omnix_services/database_service/database_manager.py` | Manager wrapper | `DatabaseServiceEnterprise()` |

**Total**: 9 files, ~30 call sites

---

### 13.3 Auto-Migration Routines (CRITICAL)

The Enterprise Service runs these migrations **automatically on every import**:

| Migration | Method | Risk Level | Action |
|-----------|--------|------------|--------|
| Users V2 | `_migrate_users_to_v2()` | 🟠 HIGH | Alters users table, adds constraints |
| Drop Prices | `_drop_prices_table()` | 🟢 LOW | Drops orphan table |
| Fix Risk Guardian | `_fix_risk_guardian_user_id_type()` | 🟠 HIGH | Alters column type |
| Add FKs | `_add_foreign_key_constraints()` | 🔴 CRITICAL | Can break if tables not ready |
| Add CHECKs | `_add_check_constraints()` | 🟡 MEDIUM | Adds validation constraints |
| Aggressive Cleanup | `_run_aggressive_cleanup()` | 🔴 CRITICAL | Drops legacy tables |
| Init Tables | `_init_tables()` | 🔴 CRITICAL | Creates 33 tables |
| Daily Cleanup | `_run_daily_cleanup()` | 🟡 MEDIUM | Deletes old records |

**Total**: 8 automatic DDL routines running on every bot restart

---

## 14. Phase 1: Discovery & Freeze (Implementation)

> **Duration**: 48-72 hours  
> **Risk Level**: LOW (no schema changes, monitoring only)  
> **Goal**: Map all call sites, disable auto-migrations, establish baseline telemetry

### 14.1 Task Checklist

| # | Task | Status | Owner | Notes |
|---|------|--------|-------|-------|
| 1.1 | Document all Dashboard Pool call sites | ✅ Done | Agent | See 13.2 |
| 1.2 | Document all Enterprise Service call sites | ✅ Done | Agent | See 13.2 |
| 1.3 | Create `DISABLE_AUTO_MIGRATIONS` feature flag | ✅ Done | Agent | `database_service.py` |
| 1.4 | Add telemetry logging to Dashboard Pool | ✅ Done | Agent | `database.py` - 5min interval |
| 1.5 | Add telemetry logging to Enterprise Service | ⬜ Pending | Agent | Connection count per call |
| 1.6 | Create `/api/db-diagnostics` endpoint | ✅ Done | Agent | `system.py` - Real-time stats |
| 1.7 | Deploy to Railway staging (if available) | ⬜ Pending | User | Validate in staging first |
| 1.8 | Run 48-hour telemetry capture | ⬜ Pending | User | Collect pool contention data |
| 1.9 | Analyze telemetry and identify high-risk call sites | ⬜ Pending | Agent | Based on connection patterns |
| 1.10 | Document consumer migration order | ✅ Done | Agent | See 14.5 |

### 14.2 Feature Flag Implementation

**Environment Variable**: `DISABLE_AUTO_MIGRATIONS`

```python
# In DatabaseServiceEnterprise.__init__():
if os.environ.get('DISABLE_AUTO_MIGRATIONS', 'false').lower() == 'true':
    logger.warning("⚠️ AUTO-MIGRATIONS DISABLED via feature flag")
    # Skip all migration routines
else:
    # Run migrations as normal
    self._migrate_users_to_v2()
    self._drop_prices_table()
    # ... etc
```

**Deployment Note**: Set `DISABLE_AUTO_MIGRATIONS=true` in Railway ONLY after Phase 1 telemetry confirms no active schema changes are needed.

### 14.3 Telemetry Implementation

#### Dashboard Pool (every 5 minutes)

```python
import threading
import time

def _log_pool_stats_periodically():
    while True:
        stats = get_pool_stats()
        logger.info(f"📊 POOL TELEMETRY: size={stats.get('pool_size')}, "
                   f"available={stats.get('pool_available')}, "
                   f"waiting={stats.get('requests_waiting')}, "
                   f"total_requests={stats.get('requests_num')}")
        time.sleep(300)  # 5 minutes

# Start telemetry thread on pool init
telemetry_thread = threading.Thread(target=_log_pool_stats_periodically, daemon=True)
telemetry_thread.start()
```

#### Enterprise Service (per connection)

```python
def _get_connection(self):
    start_time = time.time()
    conn = psycopg.connect(conn_string, connect_timeout=10)
    elapsed = (time.time() - start_time) * 1000
    logger.info(f"📊 ENTERPRISE CONN: latency={elapsed:.1f}ms, caller={inspect.stack()[2].function}")
    return conn
```

### 14.4 Diagnostics Endpoint Specification

**Endpoint**: `GET /api/db-diagnostics`  
**Authentication**: Admin only (check is_admin flag)  
**Response**:

```json
{
  "timestamp": "2025-12-03T10:30:00Z",
  "dashboard_pool": {
    "status": "active",
    "pool_size": 5,
    "pool_available": 3,
    "requests_waiting": 0,
    "requests_num": 1542,
    "usage_ms": 45230,
    "pool_min": 2,
    "pool_max": 10
  },
  "enterprise_service": {
    "connected": true,
    "using_enterprise": true,
    "last_connection_latency_ms": 45.2,
    "auto_migrations_enabled": false
  },
  "warnings": [
    "Two parallel DB services detected - consolidation recommended"
  ]
}
```

### 14.5 Consumer Migration Order (Draft)

Based on risk and dependency analysis:

| Priority | Consumer | Reason | Complexity |
|----------|----------|--------|------------|
| 1 | `omnix_dashboard/utils/queries.py` | Isolated query functions | 🟢 LOW |
| 2 | `omnix_dashboard/blueprints/core.py` | Main API endpoints | 🟡 MEDIUM |
| 3 | `omnix_dashboard/blueprints/snapshots.py` | Snapshot creation | 🟢 LOW |
| 4 | `omnix_dashboard/blueprints/views.py` | Template rendering | 🟢 LOW |
| 5 | `omnix_dashboard/blueprints/system.py` | Health checks | 🟢 LOW |
| 6 | `omnix_services/ai_service/ai_service.py` | AI interactions | 🟡 MEDIUM |
| 7 | `omnix_services/community_intelligence/*.py` | 4 community modules | 🟡 MEDIUM |
| 8 | `omnix_services/monitoring/risk_guardian.py` | Risk events | 🟠 HIGH |
| 9 | `omnix_services/telegram_service/enterprise_bot.py` | Bot commands | 🔴 CRITICAL |
| 10 | `main.py` | Bot startup | 🔴 CRITICAL |

**Strategy**: Migrate dashboard consumers first (lower risk), then services, then bot core.

### 14.6 Rollback Strategy

If any Phase 1 change causes issues:

1. **Feature Flag**: Set `DISABLE_AUTO_MIGRATIONS=false` to restore original behavior
2. **Telemetry**: Comment out telemetry threads if causing performance issues
3. **Diagnostics Endpoint**: Remove route if exposing sensitive data
4. **Railway Rollback**: Use Railway's deployment history to revert to previous version

### 14.7 Success Criteria

Phase 1 is complete when:

- [x] All call sites documented in this report
- [x] Feature flag implemented and tested locally (Dec 3, 2025)
- [x] Telemetry logging active in Dashboard Pool (Dec 3, 2025)
- [x] `/api/db-diagnostics` endpoint functional (Dec 3, 2025)
- [ ] 48-hour telemetry data collected from production
- [ ] High-risk call sites identified
- [x] Consumer migration order finalized (See 14.5)

---

## 15. Phase 2: Build Unified Database Gateway

> **Duration**: 1 week  
> **Risk Level**: 🟡 MEDIUM  
> **Goal**: Create single connection pool serving all consumers, eliminate dual-service architecture

### 15.1 Current Problem Analysis

```
┌─────────────────────────────────────────────────────────────────┐
│                    CURRENT ARCHITECTURE (PROBLEMATIC)           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Dashboard Consumers          Enterprise Consumers             │
│   ┌────────────────┐          ┌────────────────┐               │
│   │ queries.py     │          │ paper_trading  │               │
│   │ core.py        │          │ manager.py     │               │
│   │ system.py      │          │ enterprise_    │               │
│   │ snapshots.py   │          │ bot.py         │               │
│   └───────┬────────┘          │ main.py        │               │
│           │                   └───────┬────────┘               │
│           ▼                           ▼                        │
│   ┌────────────────┐          ┌────────────────┐               │
│   │ psycopg_pool   │          │ psycopg.connect│               │
│   │ ConnectionPool │          │ (per-query)    │               │
│   │ min=2, max=10  │          │ NO POOLING     │               │
│   └───────┬────────┘          └───────┬────────┘               │
│           │                           │                        │
│           └─────────┬─────────────────┘                        │
│                     ▼                                          │
│            ┌────────────────┐                                  │
│            │   PostgreSQL   │  ← Connection Contention!        │
│            │    Railway     │                                  │
│            └────────────────┘                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Problems**:
1. Two separate connection strategies compete for connections
2. Enterprise service creates new connection per query (expensive)
3. No visibility into total connection usage
4. Railway Postgres limits connections (usually 100)
5. Auto-migrations run from Enterprise, not Dashboard

### 15.2 Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TARGET ARCHITECTURE (UNIFIED)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ALL Consumers (Dashboard + Enterprise)                        │
│   ┌────────────────────────────────────────────────────┐       │
│   │ queries.py | core.py | paper_trading_manager.py    │       │
│   │ system.py | snapshots.py | enterprise_bot.py       │       │
│   └────────────────────────┬───────────────────────────┘       │
│                            │                                    │
│                            ▼                                    │
│   ┌────────────────────────────────────────────────────┐       │
│   │              DatabaseGateway                        │       │
│   │  ┌──────────────────────────────────────────────┐  │       │
│   │  │ • Unified ConnectionPool (psycopg_pool)      │  │       │
│   │  │ • Feature flags for migration control        │  │       │
│   │  │ • Telemetry & health checks                  │  │       │
│   │  │ • Backward-compatible execute_query()        │  │       │
│   │  │ • Context manager get_connection()           │  │       │
│   │  └──────────────────────────────────────────────┘  │       │
│   └────────────────────────┬───────────────────────────┘       │
│                            │                                    │
│                            ▼                                    │
│            ┌────────────────┐                                  │
│            │   PostgreSQL   │  ← Single Pool!                  │
│            │    Railway     │                                  │
│            └────────────────┘                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 15.3 DatabaseGateway Design

**Location**: `omnix_services/database_service/database_gateway.py` (NEW FILE)

```python
"""
DatabaseGateway - Unified Database Access Layer
Phase 2 Implementation - December 2025

Provides single connection pool for all OMNIX consumers.
Backward compatible with existing DatabaseServiceEnterprise interface.
"""

from psycopg_pool import ConnectionPool
from contextlib import contextmanager
import os
import logging
import threading

logger = logging.getLogger(__name__)

class DatabaseGateway:
    """
    Unified database access layer replacing dual-service architecture.
    
    Features:
    - Single ConnectionPool (psycopg_pool) for all queries
    - Backward-compatible execute_query() for Enterprise consumers
    - Context manager get_connection() for Dashboard consumers
    - Built-in telemetry and health checks
    - Feature flag support for controlled rollout
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern - one gateway instance per process"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.db_url = os.environ.get('DATABASE_URL')
        self.pool = None
        self.connected = False
        self.auto_migrations_enabled = os.environ.get(
            'DISABLE_AUTO_MIGRATIONS', 'false'
        ).lower() != 'true'
        
        self._init_pool()
        self._initialized = True
    
    def _init_pool(self):
        """Initialize connection pool with production settings"""
        if not self.db_url:
            logger.error("DATABASE_URL not found")
            return
            
        try:
            min_size = int(os.environ.get('DB_POOL_MIN', '2'))
            max_size = int(os.environ.get('DB_POOL_MAX', '15'))  # Higher for unified
            
            self.pool = ConnectionPool(
                conninfo=self.db_url,
                min_size=min_size,
                max_size=max_size,
                timeout=30.0,
                max_lifetime=3600.0,
                max_idle=600.0,
                open=True,
                name="omnix_unified_pool"
            )
            self.connected = True
            logger.info(f"DatabaseGateway pool initialized: min={min_size}, max={max_size}")
            
        except Exception as e:
            logger.error(f"DatabaseGateway init failed: {e}")
            self.connected = False
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for Dashboard-style access.
        
        Usage:
            with gateway.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
        """
        if not self.pool:
            yield None
            return
            
        try:
            with self.pool.connection() as conn:
                yield conn
        except Exception as e:
            logger.error(f"Gateway connection error: {e}")
            yield None
    
    def execute_query(self, sql: str, params: tuple = None, fetch: bool = None):
        """
        Execute query - backward compatible with Enterprise interface.
        
        Usage:
            result = gateway.execute_query("SELECT * FROM users WHERE id = %s", (id,))
            gateway.execute_query("UPDATE users SET name = %s", (name,))
        """
        if not self.pool:
            logger.error("Gateway pool not available")
            return None
            
        try:
            with self.pool.connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                sql_upper = sql.strip().upper()
                should_fetch = fetch if fetch is not None else (
                    sql_upper.startswith('SELECT') or 'RETURNING' in sql_upper
                )
                
                if should_fetch:
                    result = cursor.fetchall()
                    conn.commit()
                    return result
                else:
                    conn.commit()
                    return None
                    
        except Exception as e:
            logger.error(f"Gateway query error: {e}")
            logger.error(f"   SQL: {sql[:100]}...")
            raise
    
    def get_pool_stats(self) -> dict:
        """Return pool statistics for monitoring"""
        if not self.pool:
            return {'status': 'unavailable'}
            
        try:
            stats = self.pool.get_stats()
            return {
                'status': 'active',
                'pool_size': stats.pool_size,
                'pool_available': stats.pool_available,
                'requests_waiting': stats.requests_waiting,
                'requests_num': stats.requests_num,
                'usage_ms': stats.usage_ms,
                'pool_name': 'omnix_unified_pool'
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def health_check(self) -> dict:
        """Health check for monitoring endpoints"""
        return {
            'connected': self.connected,
            'pool_available': self.pool is not None,
            'auto_migrations_enabled': self.auto_migrations_enabled,
            'stats': self.get_pool_stats()
        }


# Global instance for import convenience
_gateway = None

def get_gateway() -> DatabaseGateway:
    """Get or create the singleton gateway instance"""
    global _gateway
    if _gateway is None:
        _gateway = DatabaseGateway()
    return _gateway
```

### 15.4 Critical Implementation Details

#### 15.4.1 Gunicorn/Multi-Worker Lifecycle (CRITICAL)

**Problem**: When using Gunicorn with multiple workers (`-w 4`), the master process forks child workers. If the pool is initialized before fork, all workers share the same socket connections → corruption.

**Solution**: Lazy initialization + post-fork hook

```python
# In database_gateway.py - Updated Singleton

class DatabaseGateway:
    _instance = None
    _lock = threading.Lock()
    _pid = None  # Track process ID for fork detection
    
    def __new__(cls):
        current_pid = os.getpid()
        
        # If we're in a new process (post-fork), reset singleton
        if cls._instance is not None and cls._pid != current_pid:
            logger.warning(f"Fork detected (old_pid={cls._pid}, new_pid={current_pid}). Reinitializing pool.")
            cls._instance = None
        
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
                    cls._pid = current_pid
        return cls._instance
```

**Gunicorn Config** (`gunicorn.conf.py`):
```python
# Post-fork hook to ensure each worker gets fresh pool
def post_fork(server, worker):
    from omnix_services.database_service.database_gateway import DatabaseGateway
    DatabaseGateway._instance = None  # Force reinitialization in this worker
    logger.info(f"Worker {worker.pid} initialized fresh database pool")
```

**Railway Deployment**: Railway uses single-process mode by default, but this pattern ensures safety if scaled.

**Gunicorn Integration Steps** (for production):

1. **Create/Update gunicorn.conf.py**:
```python
# gunicorn.conf.py
import logging

bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
timeout = 120

def post_fork(server, worker):
    """Reset database pool after fork to prevent socket sharing"""
    try:
        from omnix_services.database_service.database_gateway import DatabaseGateway
        DatabaseGateway._instance = None
        logging.info(f"Worker {worker.pid}: Database pool reset for fresh connection")
    except ImportError:
        pass  # Gateway not yet created
```

2. **Verify hook is active** (add to startup log check):
```python
# In app.py or __init__.py
import os
logger.info(f"Process PID: {os.getpid()}, Pool initialized: {gateway.connected}")
```

3. **Railway Procfile** (if using Gunicorn):
```
web: gunicorn --config gunicorn.conf.py omnix_dashboard.app:app
```

4. **Validation command** (run locally with Gunicorn):
```bash
gunicorn -w 2 --config gunicorn.conf.py omnix_dashboard.app:app
# Check logs for: "Worker XXXXX: Database pool reset for fresh connection"
```

#### 15.4.2 execute_query() Semantic Compatibility (CRITICAL)

**Problem**: Enterprise code expects specific psycopg3 behaviors. Gateway must match exactly.

| Behavior | Current Enterprise | Gateway Must Match |
|----------|-------------------|-------------------|
| Cursor factory | Default (tuple rows) | Default (tuple rows) |
| Autocommit | False (explicit commit) | False (explicit commit) |
| Transaction | Per-connection | Per-connection via pool |
| Rollback on error | Manual in except block | Manual in except block |
| Connection close | Always in finally | Pool handles return |

**Row Access Pattern Analysis** (from code audit):

All Enterprise consumers access results via **tuple indexing** (`row[0]`, `row[1]`, etc.), NOT dict-style access. Examples from `paper_trading_manager.py`:

```python
# Line 481-497: _get_paper_balance()
row = result[0]
return {
    'user_id': row[0],          # Tuple index 0
    'balance_usd': float(row[1]), # Tuple index 1
    'btc_balance': float(row[2]), # etc.
    ...
}

# Line 634: _open_position_v2()
trade_id = result[0][0]  # First row, first column

# Line 865: get_trade_pnl_report()
trade_id, symbol, side, entry_price, ... = row  # Tuple unpacking
```

**Full Enterprise Audit Results** (all files checked):

| File | Access Pattern | Status |
|------|---------------|--------|
| `paper_trading_manager.py` | Tuple index (`row[0]`, `row[1]`) | ✅ Compatible |
| `daily_summary_service.py` | Tuple index (`row[0]`, `result[0][0]`) | ✅ Compatible |
| `trade_notification_service.py` | Tuple index (`row[0]`) | ✅ Compatible |
| `paper_trading.py` | Tuple index (`row[0]`, `result[0][0]`) | ✅ Compatible |
| `user_session_manager.py` | Tuple index (`row[0]`) | ✅ Compatible |
| `auto_trading_bot.py` | **MIXED** - some `.get('key')` calls | ⚠️ NEEDS FIX |

**CRITICAL FINDING - auto_trading_bot.py**:

Lines 787, 839, 908, 2050 use dict-style access (`.get('key')`) which is **INCOMPATIBLE** with psycopg3 default tuple rows. This is likely a latent bug OR unused code path.

```python
# Line 787 - PROBLEMATIC (dict access on tuple)
uid = result[0].get('user_id')  # Will fail if result[0] is tuple

# Line 839 - PROBLEMATIC
auto_trading = row.get('auto_trading', False)  # Will fail
```

**Resolution Options**:

1. **Option A (Preferred)**: Fix auto_trading_bot.py to use tuple indexing:
   ```python
   # Before (broken)
   uid = result[0].get('user_id')
   # After (fixed)
   uid = result[0][0]  # First column = user_id
   ```

2. **Option B**: Add row_factory to Gateway for dict returns:
   ```python
   from psycopg.rows import dict_row
   cursor = conn.cursor(row_factory=dict_row)
   ```
   **NOT RECOMMENDED** - Changes behavior for ALL consumers

**Conclusion**: Gateway returns `List[Tuple]` (psycopg3 default). Most consumers are compatible. **auto_trading_bot.py requires fixes** before Phase 2 migration - added to Task 2.4.1.

**Updated execute_query() with full compatibility**:

```python
def execute_query(self, sql: str, params: tuple = None, fetch: bool = None):
    """
    Execute query - DROP-IN replacement for Enterprise interface.
    
    Semantic guarantees:
    - Returns list of tuples (same as psycopg3 default cursor)
    - Commits on success, raises on error (caller handles rollback logic)
    - No autocommit - explicit transaction boundaries
    - Connection returned to pool (not closed)
    
    Return types:
    - SELECT/RETURNING: List[Tuple] (can be empty [])
    - INSERT/UPDATE/DELETE without RETURNING: None
    - Error: raises exception (caller must handle)
    """
    if not self.pool:
        logger.error("Gateway pool not available")
        return None
        
    conn = None
    try:
        with self.pool.connection() as conn:
            cursor = conn.cursor()  # Default tuple factory
            
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            # Auto-detect fetch based on SQL (same as Enterprise)
            sql_upper = sql.strip().upper()
            should_fetch = fetch if fetch is not None else (
                sql_upper.startswith('SELECT') or 'RETURNING' in sql_upper
            )
            
            if should_fetch:
                result = cursor.fetchall()  # List[Tuple]
                conn.commit()
                return result
            else:
                conn.commit()
                return None
                
    except Exception as e:
        # Note: Pool's context manager handles connection return
        # Caller is responsible for any application-level rollback logic
        logger.error(f"Gateway query error: {e}")
        logger.error(f"   SQL: {sql[:100]}...")
        raise  # Preserve exception for caller handling
```

#### 15.4.3 Import Strategy (No Circular Dependencies)

**Problem**: Dashboard (`omnix_dashboard`) importing from Enterprise (`omnix_services`) could create circular imports.

**Solution**: Gateway is standalone with no internal OMNIX imports

```
omnix_services/
└── database_service/
    ├── __init__.py          # Exports: get_gateway, DatabaseGateway
    ├── database_gateway.py  # NEW: Standalone, no omnix_* imports
    └── database_service.py  # LEGACY: Will be deprecated
```

**Gateway Dependencies** (external only):
```python
# database_gateway.py imports ONLY:
from psycopg_pool import ConnectionPool
from contextlib import contextmanager
import os
import logging
import threading
# NO imports from omnix_core, omnix_dashboard, etc.
```

**Safe Import Pattern** for consumers:
```python
# In omnix_dashboard/utils/queries.py
def get_paper_trades(days=30, return_dict=False):
    if USE_UNIFIED_GATEWAY:
        # Lazy import inside function - avoids module-level circular deps
        from omnix_services.database_service.database_gateway import get_gateway
        gateway = get_gateway()
        with gateway.get_connection() as conn:
            ...
```

**Validation Before Deploy**:

1. **Compile Check** (catches syntax errors):
```bash
python -m py_compile omnix_services/database_service/database_gateway.py
# No output = success
```

2. **Import Chain Validation** (catches circular imports):
```bash
# Test Gateway standalone (should have NO omnix_* deps)
python -c "from omnix_services.database_service.database_gateway import get_gateway; print('Gateway OK:', get_gateway())"

# Test Dashboard can import Gateway
python -c "from omnix_dashboard.utils.queries import get_paper_trades; print('Queries OK')"

# Full import test (simulates production startup)
python -c "
import sys
print('Testing import chain...')
from omnix_services.database_service.database_gateway import DatabaseGateway
print('  1. DatabaseGateway: OK')
from omnix_dashboard.utils.database import get_db_connection  
print('  2. Dashboard pool: OK')
from omnix_dashboard.utils.queries import get_paper_trades
print('  3. Queries module: OK')
print('All imports successful!')
"
```

3. **Railway PYTHONPATH** (already configured in Railway):
```
# Railway automatically adds project root to PYTHONPATH
# No changes needed for omnix_* imports
```

4. **Circular Dependency Detection** (optional but recommended):
```bash
# Install: pip install pydeps
pydeps omnix_services/database_service/database_gateway.py --no-show --max-bacon 2
# Should show ONLY external deps (psycopg_pool, logging, etc.)
```

**Module Ownership Summary**:
```
Package                          Owns                      Imports From Gateway
──────────────────────────────────────────────────────────────────────────────
omnix_services.database_service  database_gateway.py       (self - no imports)
omnix_dashboard.utils            queries.py, database.py   YES (lazy import)
omnix_dashboard.blueprints       core.py, system.py, etc   YES (lazy import)
omnix_services.trading_service   paper_trading_manager.py  YES (lazy import)
```

### 15.5 Migration Strategy: Canary Deployment

Phase 2 uses a **canary deployment** pattern to migrate consumers one-by-one without breaking 24/7 trading.

#### Stage 1: Feature Flag for Routing (Week 1, Days 1-2)

Add routing flag to each consumer file:

```python
# In omnix_dashboard/utils/queries.py
USE_UNIFIED_GATEWAY = os.environ.get('USE_UNIFIED_GATEWAY', 'false').lower() == 'true'

def get_paper_trades(days=30, return_dict=False):
    if USE_UNIFIED_GATEWAY:
        from omnix_services.database_service.database_gateway import get_gateway
        gateway = get_gateway()
        with gateway.get_connection() as conn:
            # Same logic, different pool
            ...
    else:
        # Original code path
        with get_db_connection() as conn:
            ...
```

#### Stage 2: Migrate Dashboard Consumers (Week 1, Days 3-4)

| Order | File | Functions | Risk |
|-------|------|-----------|------|
| 1 | `utils/queries.py` | `get_paper_trades()`, `get_balance_history()` | 🟢 LOW |
| 2 | `blueprints/system.py` | `/api/health`, `/api/db-diagnostics` | 🟢 LOW |
| 3 | `blueprints/core.py` | `/api/metrics`, `/api/trades`, `/api/positions` | 🟡 MEDIUM |
| 4 | `blueprints/snapshots.py` | 7 snapshot endpoints | 🟡 MEDIUM |

#### Stage 3: Migrate Enterprise Consumers (Week 1, Days 5-7)

| Order | File | Functions | Risk |
|-------|------|-----------|------|
| 5 | `notifications/daily_summary_service.py` | Summary queries | 🟢 LOW |
| 6 | `notifications/trade_notification_service.py` | Trade notifications | 🟢 LOW |
| 7 | `trading_service/paper_trading_manager.py` | All trading operations | 🔴 CRITICAL |
| 8 | `telegram_service/enterprise_bot.py` | Bot commands | 🔴 CRITICAL |
| 9 | `main.py` | Bot startup | 🔴 CRITICAL |

### 15.6 Task Checklist

| # | Task | Status | Owner | Risk |
|---|------|--------|-------|------|
| **Pre-Implementation** |
| 2.1 | Analyze Phase 1 telemetry logs (48h) | ⬜ Pending | Agent | - |
| 2.2 | Identify peak connection usage patterns | ⬜ Pending | Agent | - |
| **Pre-Requisite Fixes** |
| 2.3 | Fix auto_trading_bot.py dict-style access (lines 787,839,908,2050) | ✅ Done | Agent | 🟢 RESOLVED |
| **Gateway Creation** |
| 2.4 | Create `database_gateway.py` with fork-safe singleton | ✅ Done | Agent | 🟢 RESOLVED |
| 2.5 | Implement execute_query() with semantic compatibility | ✅ Done | Agent | 🟢 RESOLVED |
| 2.6 | Add Gunicorn post-fork hook (gunicorn.conf.py) | ✅ Done | Agent | 🟢 RESOLVED |
| 2.7 | Run import chain validation tests | ✅ Done | Agent | 🟢 RESOLVED |
| **Canary Rollout** |
| 2.8 | Add `USE_UNIFIED_GATEWAY` feature flag | ✅ Done | Agent | 🟢 RESOLVED |
| 2.9 | Migrate `queries.py` (first canary) | ✅ Done | Agent | 🟢 RESOLVED |
| 2.10 | Test with `USE_UNIFIED_GATEWAY=true` locally | ✅ Done | Agent | 🟢 RESOLVED |
| 2.11 | Deploy to Railway with flag ON | ✅ Done | User | 🟢 RESOLVED |
| 2.12 | Verify Gunicorn post_fork hook active in logs | ✅ Done | User | 🟢 RESOLVED |
| 2.13 | Enable flag for 1 hour, monitor | ✅ Done | User | 🟢 RESOLVED |
| **Full Migration** |
| 2.14 | Migrate remaining Dashboard consumers | ⬜ Pending | Agent | 🟡 MEDIUM |
| 2.15 | Migrate Enterprise consumers (critical) | ⬜ Pending | Agent | 🔴 CRITICAL |
| **Cleanup** |
| 2.16 | Deprecate old Dashboard pool with warnings | ⬜ Pending | Agent | 🟡 MEDIUM |
| 2.17 | Deprecate old Enterprise service with warnings | ⬜ Pending | Agent | 🔴 CRITICAL |
| 2.18 | Measure connection reduction (target: 50%+) | ⬜ Pending | Agent | - |

### 15.7 Telemetry Analysis Template

When you provide the 48-hour logs, I will analyze them using this template:

```
=== PHASE 1 TELEMETRY ANALYSIS ===

1. CONNECTION PATTERNS
   - Peak concurrent connections: ___
   - Average connections during trading hours: ___
   - Connection spikes (timestamp + count): ___

2. POOL UTILIZATION (Dashboard)
   - Pool size at peak: ___/10
   - Requests waiting (max): ___
   - Usage time (avg ms): ___

3. ENTERPRISE SERVICE USAGE
   - Queries per hour (avg): ___
   - Failed connection attempts: ___
   - Long-running queries (>5s): ___

4. RECOMMENDATIONS
   - Suggested unified pool size: min=___, max=___
   - High-risk migration targets: ___
   - Safe migration candidates: ___
```

### 15.8 Code Changes Summary

| File | Action | Lines Changed (Est.) |
|------|--------|---------------------|
| `omnix_services/database_service/database_gateway.py` | CREATE | ~200 |
| `omnix_dashboard/utils/queries.py` | MODIFY | ~20 |
| `omnix_dashboard/utils/database.py` | DEPRECATE | ~50 (add warnings) |
| `omnix_dashboard/blueprints/core.py` | MODIFY | ~15 |
| `omnix_dashboard/blueprints/system.py` | MODIFY | ~20 |
| `omnix_dashboard/blueprints/snapshots.py` | MODIFY | ~30 |
| `omnix_services/trading_service/paper_trading_manager.py` | MODIFY | ~40 |
| `omnix_services/database_service/database_service.py` | DEPRECATE | ~100 (add warnings) |

### 15.9 Railway Deployment Checklist

Status: **CANARY DEPLOYMENT ACTIVE** (Dec 4, 2025)

```
PRE-DEPLOYMENT
─────────────────────────────────────────────────────────────
[x] 1. Phase 1 telemetry logs analyzed (48h) - Dec 3, 2025
[x] 2. auto_trading_bot.py dict-access bugs fixed - Dec 3, 2025
[x] 3. database_gateway.py created and tested locally - Dec 3, 2025
[x] 4. Import chain validation passed (see 15.4.3) - Dec 3, 2025
[x] 5. Gunicorn post_fork hook added (if using Gunicorn) - Dec 3, 2025

RAILWAY DEPLOYMENT (flag OFF)
─────────────────────────────────────────────────────────────
[x] 6. Push code to GitHub main branch - Dec 3, 2025
[x] 7. Railway auto-deploys from main - Dec 3, 2025
[x] 8. Verify logs show "DatabaseGateway pool initialized" - Dec 3, 2025
[x] 9. If using Gunicorn, verify "Database pool reset for fresh connection" - Dec 3, 2025
[x] 10. Dashboard loads correctly (/terminal, /api/health) - Dec 3, 2025

CANARY TEST (flag ON for 1 hour)
─────────────────────────────────────────────────────────────
[x] 11. Set USE_UNIFIED_GATEWAY=true in Railway env vars - Dec 4, 2025
[x] 12. Railway restarts automatically - Dec 4, 2025
[x] 13. Monitor for 1 hour: - Dec 4, 2025
       - /api/health returns status=ok ✓
       - /api/db-diagnostics shows unified pool stats ✓
       - No "connection pool exhausted" errors ✓
       - Trading continues normally ✓
[x] 14. No issues found - Canary successful

FULL ROLLOUT
─────────────────────────────────────────────────────────────
[x] 15. Keep flag ON for 24 hours - IN PROGRESS (Dec 4, 2025)
[ ] 16. Migrate remaining consumers
[ ] 17. Deprecate old pool code
[ ] 18. Remove feature flag (make Gateway default)
```

### 15.10 Rollback Strategy

If any Phase 2 migration causes issues:

1. **Immediate**: Set `USE_UNIFIED_GATEWAY=false` → reverts to dual-service
2. **Per-consumer**: Each file can be individually reverted
3. **Full rollback**: Railway deployment history to Phase 1 version

### 15.11 Success Criteria

Phase 2 is complete when:

- [x] Telemetry analyzed and pool sizing determined (Dec 3, 2025)
- [x] auto_trading_bot.py dict-access bugs fixed (Dec 3, 2025)
- [x] `DatabaseGateway` created with fork-safe singleton (Dec 3, 2025)
- [x] Gunicorn post_fork hook configured and verified (Dec 3, 2025)
- [x] Import chain validation tests passed (Dec 3, 2025)
- [x] All Dashboard consumers migrated (via `get_db_connection()` abstraction) (Dec 3, 2025)
- [ ] All Enterprise consumers migrated
- [ ] Old pool code deprecated with warnings
- [x] Single unified pool serving all queries (USE_UNIFIED_GATEWAY=true active) (Dec 4, 2025)
- [ ] Connection count reduced by 50%+ (measured)
- [x] Zero trading interruptions during migration (Dec 4, 2025)

### 15.12 Dependencies

**Requires before starting**:
- Phase 1 complete ✅
- 48-hour telemetry logs from Railway production
- User approval to proceed with canary deployment

---

## 16. Phase 3-4 Overview (Future)

| Phase | Focus | Duration | Risk |
|-------|-------|----------|------|
| **Phase 3** | Add missing FKs, merge redundant tables | 1 week | 🟠 HIGH |
| **Phase 4** | Consolidate query functions, add transactions | 1 week | 🟠 HIGH |

**Detailed plans for Phases 3-4 will be added after Phase 2 completes successfully.**

---

**Document Version:** 2.3  
**OMNIX V6.5.2 INSTITUTIONAL+**  
**Audit Date:** December 2025  
**Phase 1 Plan Added:** December 3, 2025  
**Phase 2 Plan Added:** December 3, 2025  
**Phase 2 Status Updated:** December 4, 2025 (Canary deployment active, schema fixes applied)
