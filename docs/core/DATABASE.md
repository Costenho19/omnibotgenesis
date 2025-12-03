# OMNIX V6.5.2 INSTITUTIONAL+ - Database Schema Documentation

**Version:** V6.5.2 INSTITUTIONAL+  
**Last Updated:** December 2025  
**Database:** PostgreSQL (Railway/Neon)  
**Total Tables:** 45  
**Audit Report:** See [DATABASE_AUDIT_REPORT.md](./DATABASE_AUDIT_REPORT.md)

---

## Overview

OMNIX uses PostgreSQL for all persistent data storage. The database supports multi-user trading (100,000+ users), paper trading simulation, risk management, AI interactions, and community intelligence.

---

## Schema Summary

| Category | Tables | Purpose |
|----------|--------|---------|
| Core Trading | 5 | trades, paper_trading_trades, paper_trading_balances, trading_history, balance_history |
| User Management | 4 | users, user_settings, user_contacts, user_contributions |
| AI & Conversations | 3 | ai_interactions, conversations, conversation_memory |
| Risk Management | 9 | risk_alerts, risk_events, risk_limits, risk_limit_breaches, risk_guardian_events, risk_guardian_logs, risk_metrics_snapshots, limit_checks, memory_risk_patterns |
| Derivatives | 6 | derivatives_orders, perpetual_positions, funding_payments, funding_arbitrage, hedge_positions, margin_calls |
| Community | 5 | community_feedback, community_signals, strategy_votes, improvement_proposals, user_rewards |
| Arbitrage | 1 | arbitrage_opportunities |
| Circuit Breakers | 2 | circuit_breaker_states, circuit_breaker_status |
| Snapshots & Analysis | 5 | audited_snapshots, position_snapshots, detected_patterns, pending_evaluations, trade_evaluations |
| Trade Analysis | 1 | trade_reasonings |
| System | 4 | schema_migrations, system_config, whatsapp_messages, performance_metrics |
| **TOTAL** | **45** | |

---

## 1. User Management Tables (4)

### users (18 columns) - MASTER TABLE
Primary user accounts table with Telegram integration.
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

### user_settings (25 columns)
Extensive user configuration and preferences.
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

### user_contacts (7 columns)
Multi-channel contact information.
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

### user_contributions (7 columns)
User contribution tracking for community features.
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

---

## 2. Core Trading Tables (5)

### paper_trading_trades (13 columns) - PRIMARY TRADING TABLE
Virtual trade executions for paper trading mode.
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
**Note**: No FK to users - recommended to add

### paper_trading_balances (15 columns)
Virtual portfolio balances with performance metrics.
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

### trades (12 columns)
Real exchange order tracking.
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

### trading_history (15 columns)
Historical trade records with FK to users.
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

### balance_history (6 columns)
Historical balance tracking.
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

---

## 3. AI & Conversation Tables (3)

### ai_interactions (9 columns)
AI model usage tracking.
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

### conversations (6 columns)
AI conversation history.
```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    language VARCHAR,
    created_at TIMESTAMP
);
```
**Indexes**: idx_conversations_user_id, idx_conversations_created_at

### conversation_memory (6 columns)
Long-term conversation context.
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

---

## 4. Risk Management Tables (9)

### risk_alerts (8 columns)
User risk notifications.
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

### risk_events (9 columns)
General risk events log.
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

### risk_limits (8 columns)
Configured risk limits per user.
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

### risk_limit_breaches (8 columns)
Risk limit violation log.
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

### risk_guardian_events (8 columns)
Risk guardian action events with severity.
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

### risk_guardian_logs (6 columns)
Risk guardian action log.
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

### risk_metrics_snapshots (10 columns)
Point-in-time risk metrics.
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

### limit_checks (8 columns)
Risk limit validation log.
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

### memory_risk_patterns (7 columns)
Non-Markovian risk pattern storage.
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
```
**Indexes**: idx_memory_risk_patterns_user_id

---

## 5. Derivatives Tables (6)

### derivatives_orders (12 columns)
Futures/perpetual orders.
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

### perpetual_positions (13 columns)
Open perpetual positions.
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

### funding_payments (7 columns)
Funding rate payment log.
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

### funding_arbitrage (11 columns)
Funding rate arbitrage opportunities.
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
```
**Indexes**: idx_funding_arbitrage_user_id

### hedge_positions (10 columns)
Spot-perpetual hedging positions.
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

### margin_calls (9 columns)
Margin call events.
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

---

## 6. Community Tables (5)

### community_feedback (7 columns)
User signal and strategy feedback.
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

### community_signals (11 columns)
Community-generated trading signals.
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

### strategy_votes (6 columns)
User strategy ratings.
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

### improvement_proposals (10 columns)
User improvement suggestions.
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

### user_rewards (7 columns)
User reward tracking.
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

---

## 7. Arbitrage Table (1)

### arbitrage_opportunities (13 columns)
Cross-exchange arbitrage opportunities.
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
```
**Indexes**: idx_arbitrage_opportunities_user_id

---

## 8. Circuit Breaker Tables (2)

### circuit_breaker_states (8 columns)
Circuit breaker state machine.
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

### circuit_breaker_status (9 columns)
Current circuit breaker status.
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

---

## 9. Snapshots & Analysis Tables (5)

### audited_snapshots (19 columns)
Cryptographically verified snapshots for investor auditing.
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
    position_snapshot_ids ARRAY,
    risk_snapshot_id INTEGER REFERENCES risk_metrics_snapshots(id),
    UNIQUE(snapshot_type, snapshot_date)
);
```

### position_snapshots (10 columns)
Point-in-time position state.
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

### detected_patterns (9 columns)
AI-detected trading patterns.
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
```
**Indexes**: idx_detected_patterns_user_id

### pending_evaluations (9 columns)
Queue for pending evaluations.
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
```
**Indexes**: idx_pending_evaluations_user_id

### trade_evaluations (8 columns)
Post-trade AI evaluations.
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

---

## 10. Trade Reasoning Table (1)

### trade_reasonings (7 columns)
AI reasoning for trade decisions.
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

---

## 11. System Tables (4)

### schema_migrations (5 columns)
Database migration tracking.
```sql
CREATE TABLE schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name TEXT UNIQUE NOT NULL,
    migration_hash TEXT,
    executed_at TIMESTAMPTZ,
    success BOOLEAN
);
```

### system_config (5 columns)
System configuration storage.
```sql
CREATE TABLE system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP
);
```

### whatsapp_messages (8 columns)
WhatsApp message log.
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

### performance_metrics (7 columns)
User performance metrics over time.
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

## Foreign Key Summary

| Tables with FK | Reference |
|----------------|-----------|
| ai_interactions | → users |
| audited_snapshots | → risk_metrics_snapshots |
| balance_history | → users |
| conversation_memory | → users |
| performance_metrics | → users |
| trading_history | → users |
| user_contacts | → users |
| whatsapp_messages | → users |

**Total with FK**: 8 of 45 (18%)  
**Recommended**: Add FK to paper_trading_trades, trades, and all tables with user_id

---

## Connection Configuration

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

## Related Documentation

- **Audit Report**: [DATABASE_AUDIT_REPORT.md](./DATABASE_AUDIT_REPORT.md) - Comprehensive defect analysis
- **Dashboard Reference**: [DASHBOARD_TECHNICAL_REFERENCE.md](./DASHBOARD_TECHNICAL_REFERENCE.md) - API endpoints and frontend

---

**Document Version:** 4.0  
**OMNIX V6.5.2 INSTITUTIONAL+**  
**Last Updated:** December 2025
