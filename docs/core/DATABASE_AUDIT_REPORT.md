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

**Document Version:** 1.0  
**OMNIX V6.5.2 INSTITUTIONAL+**  
**Audit Date:** December 2025
