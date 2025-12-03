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
| 22 | pending_evaluations | 9 | ❌ | ✅ |
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
    priority INTEGER,
    metadata JSONB,
    created_at TIMESTAMP,
    processed_at TIMESTAMP,
    user_id VARCHAR
);
CREATE INDEX idx_pending_evaluations_user_id ON pending_evaluations(user_id);
```

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
| 1.1 | Document all Dashboard Pool call sites | ⬜ Pending | Agent | See 13.2 |
| 1.2 | Document all Enterprise Service call sites | ⬜ Pending | Agent | See 13.2 |
| 1.3 | Create `DISABLE_AUTO_MIGRATIONS` feature flag | ⬜ Pending | Agent | Environment variable |
| 1.4 | Add telemetry logging to Dashboard Pool | ⬜ Pending | Agent | Every 5 minutes |
| 1.5 | Add telemetry logging to Enterprise Service | ⬜ Pending | Agent | Connection count per call |
| 1.6 | Create `/api/db-diagnostics` endpoint | ⬜ Pending | Agent | Real-time pool stats |
| 1.7 | Deploy to Railway staging (if available) | ⬜ Pending | User | Validate in staging first |
| 1.8 | Run 48-hour telemetry capture | ⬜ Pending | User | Collect pool contention data |
| 1.9 | Analyze telemetry and identify high-risk call sites | ⬜ Pending | Agent | Based on connection patterns |
| 1.10 | Document consumer migration order | ⬜ Pending | Agent | Priority sequence |

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
- [ ] Feature flag implemented and tested locally
- [ ] Telemetry logging active in both services
- [ ] `/api/db-diagnostics` endpoint functional
- [ ] 48-hour telemetry data collected from production
- [ ] High-risk call sites identified
- [ ] Consumer migration order finalized

---

## 15. Phase 2-4 Overview (Future)

| Phase | Focus | Duration | Risk |
|-------|-------|----------|------|
| **Phase 2** | Build unified gateway, migrate dashboard | 1 week | 🟡 MEDIUM |
| **Phase 3** | Add missing FKs, merge redundant tables | 1 week | 🟠 HIGH |
| **Phase 4** | Consolidate query functions, add transactions | 1 week | 🟠 HIGH |

**Detailed plans for Phases 2-4 will be added after Phase 1 completes successfully.**

---

**Document Version:** 2.1  
**OMNIX V6.5.2 INSTITUTIONAL+**  
**Audit Date:** December 2025  
**Phase 1 Plan Added:** December 3, 2025
