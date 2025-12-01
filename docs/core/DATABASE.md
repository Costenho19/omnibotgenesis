# OMNIX V6.5 INSTITUTIONAL+ - Database Schema Documentation

**Version:** V6.5 INSTITUTIONAL+  
**Last Updated:** December 2024  
**Database:** PostgreSQL (Railway/Neon)  
**Total Tables:** 44

---

## Overview

OMNIX uses PostgreSQL for all persistent data storage. The database is organized into logical groups supporting trading, analytics, community intelligence, risk management, and the adaptive parameter engine.

---

## Schema Summary

| Category | Tables | Purpose |
|----------|--------|---------|
| Core Trading | 9 | Users, trades, analysis, balances |
| Paper Trading | 2 | Virtual trading simulation |
| Conversational Brain | 3 | Trade reasoning and evaluations |
| Community Intelligence | 9 | Feedback, voting, contributions |
| Risk Management | 4 | Risk guardian, circuit breakers |
| Derivatives | 6 | Futures, hedging, funding |
| Adaptive Engine V6.5 | 3 | Parameter calibration |
| System | 4 | Migrations, cache, settings |
| On-Chain Intelligence | 4 | Whale tracking, exchange flows |
| **TOTAL** | **44** | |

---

## Core Trading Tables (9)

### users
Primary user accounts table.
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id TEXT UNIQUE NOT NULL,
    username TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    subscription_tier TEXT DEFAULT 'free'
);
```

### user_contacts
Multi-channel contact information.
```sql
CREATE TABLE user_contacts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    contact_type TEXT NOT NULL,  -- 'telegram', 'whatsapp', 'email'
    contact_value TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### trades
All executed trades (paper + real).
```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,  -- 'buy' or 'sell'
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    fee REAL DEFAULT 0,
    pnl REAL,
    strategy TEXT,
    signal_strength TEXT,  -- 'STRONG', 'MEDIUM', 'WEAK'
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### analysis
AI analysis records.
```sql
CREATE TABLE analysis (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    analysis_type TEXT NOT NULL,
    result JSONB,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### conversations
AI conversation history.
```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    message TEXT NOT NULL,
    response TEXT,
    ai_model TEXT,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### balance_history
Historical balance tracking.
```sql
CREATE TABLE balance_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    balance REAL NOT NULL,
    currency TEXT DEFAULT 'USD',
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### sharia_validations
Islamic finance compliance checks.
```sql
CREATE TABLE sharia_validations (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    is_compliant BOOLEAN,
    reason TEXT,
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### video_transcript_cache
AI video analysis cache.
```sql
CREATE TABLE video_transcript_cache (
    id SERIAL PRIMARY KEY,
    video_url TEXT UNIQUE NOT NULL,
    transcript TEXT,
    analysis JSONB,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### user_settings
User preferences and configuration.
```sql
CREATE TABLE user_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    setting_key TEXT NOT NULL,
    setting_value JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, setting_key)
);
```

---

## Paper Trading Tables (2)

### paper_trading_balances
Virtual portfolio balances.
```sql
CREATE TABLE paper_trading_balances (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    currency TEXT DEFAULT 'USD',
    balance REAL DEFAULT 1000000.0,  -- $1M starting capital
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### paper_trading_trades
Virtual trade executions.
```sql
CREATE TABLE paper_trading_trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity REAL NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL,
    pnl REAL,
    status TEXT DEFAULT 'open',  -- 'open', 'closed'
    strategy TEXT,
    signal_strength TEXT,
    entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exit_time TIMESTAMP
);
```

---

## Conversational Brain Tables (3)

### trade_reasonings
AI reasoning for trade decisions.
```sql
CREATE TABLE trade_reasonings (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER REFERENCES trades(id),
    reasoning TEXT NOT NULL,
    ai_model TEXT,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### trade_evaluations
Post-trade AI evaluations.
```sql
CREATE TABLE trade_evaluations (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER REFERENCES trades(id),
    evaluation TEXT,
    lessons_learned TEXT,
    score REAL,
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### pending_evaluations
Queue for pending trade evaluations.
```sql
CREATE TABLE pending_evaluations (
    id SERIAL PRIMARY KEY,
    trade_id INTEGER REFERENCES trades(id),
    scheduled_for TIMESTAMP,
    status TEXT DEFAULT 'pending'
);
```

---

## Community Intelligence Tables (9)

### community_feedback
User signal feedback.
```sql
CREATE TABLE community_feedback (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    feedback_type TEXT NOT NULL,  -- 'signal', 'strategy', 'arbitrage'
    strategy TEXT,
    symbol TEXT,
    result TEXT NOT NULL,  -- 'success', 'failure', 'partial'
    market_condition TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### strategy_votes
User strategy ratings.
```sql
CREATE TABLE strategy_votes (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    strategy TEXT NOT NULL,
    vote INTEGER NOT NULL,  -- 1-5 stars
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### user_contributions
Contributor profiles.
```sql
CREATE TABLE user_contributions (
    user_id TEXT PRIMARY KEY,
    total_feedback INTEGER DEFAULT 0,
    contribution_points INTEGER DEFAULT 0,
    contribution_level TEXT DEFAULT 'Novato',
    badges JSONB DEFAULT '[]'
);
```

### detected_patterns
AI-detected trading patterns.
```sql
CREATE TABLE detected_patterns (
    id SERIAL PRIMARY KEY,
    pattern_type TEXT NOT NULL,
    description TEXT,
    affected_strategy TEXT,
    confidence REAL,
    status TEXT DEFAULT 'detected'
);
```

### improvement_proposals
User improvement suggestions.
```sql
CREATE TABLE improvement_proposals (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    proposal_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending'
);
```

### community_signals
Community-generated signals.
```sql
CREATE TABLE community_signals (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### signal_executions
Tracked signal executions.
```sql
CREATE TABLE signal_executions (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER REFERENCES community_signals(id),
    result TEXT,
    pnl REAL,
    executed_at TIMESTAMP
);
```

### signal_votes
Signal reliability votes.
```sql
CREATE TABLE signal_votes (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER REFERENCES community_signals(id),
    user_id TEXT NOT NULL,
    vote INTEGER  -- 1 or -1
);
```

### alpha_leaderboard
Top contributor rankings.
```sql
CREATE TABLE alpha_leaderboard (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    score REAL DEFAULT 0,
    rank INTEGER,
    period TEXT,  -- 'weekly', 'monthly', 'all_time'
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Risk Management Tables (4)

### risk_guardian_events
Risk guardian actions.
```sql
CREATE TABLE risk_guardian_events (
    id SERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,  -- 'drawdown_alert', 'position_limit', 'revenge_trade'
    severity TEXT,
    action_taken TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### risk_limits
Configured risk limits.
```sql
CREATE TABLE risk_limits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    limit_type TEXT NOT NULL,
    limit_value REAL,
    is_active BOOLEAN DEFAULT true
);
```

### risk_limit_breaches
Risk limit violation log.
```sql
CREATE TABLE risk_limit_breaches (
    id SERIAL PRIMARY KEY,
    limit_id INTEGER REFERENCES risk_limits(id),
    breach_value REAL,
    action_taken TEXT,
    breached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### circuit_breaker_status
Trading circuit breaker state.
```sql
CREATE TABLE circuit_breaker_status (
    id SERIAL PRIMARY KEY,
    is_active BOOLEAN DEFAULT false,
    reason TEXT,
    activated_at TIMESTAMP,
    deactivated_at TIMESTAMP
);
```

---

## Derivatives Tables (6)

### derivatives_balances
Margin account balances.
```sql
CREATE TABLE derivatives_balances (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    balance REAL,
    margin_used REAL,
    margin_available REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### derivatives_trades
Futures/options trades.
```sql
CREATE TABLE derivatives_trades (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    symbol TEXT NOT NULL,
    contract_type TEXT,  -- 'futures', 'perpetual'
    side TEXT NOT NULL,
    quantity REAL,
    price REAL,
    leverage REAL,
    pnl REAL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### derivatives_positions
Open derivative positions.
```sql
CREATE TABLE derivatives_positions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    symbol TEXT NOT NULL,
    side TEXT,
    quantity REAL,
    entry_price REAL,
    liquidation_price REAL,
    unrealized_pnl REAL
);
```

### derivatives_funding_log
Funding rate payments.
```sql
CREATE TABLE derivatives_funding_log (
    id SERIAL PRIMARY KEY,
    position_id INTEGER,
    funding_rate REAL,
    payment REAL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### derivatives_hedges
Active hedging strategies.
```sql
CREATE TABLE derivatives_hedges (
    id SERIAL PRIMARY KEY,
    spot_position_id INTEGER,
    hedge_position_id INTEGER,
    hedge_ratio REAL,
    status TEXT DEFAULT 'active'
);
```

### derivatives_funding_opportunities
Funding rate arbitrage opportunities.
```sql
CREATE TABLE derivatives_funding_opportunities (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    long_exchange TEXT,
    short_exchange TEXT,
    spread REAL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Adaptive Engine V6.5 Tables (3)

### adaptive_parameters
Current adaptive parameters.
```sql
CREATE TABLE adaptive_parameters (
    id SERIAL PRIMARY KEY,
    strategy TEXT NOT NULL,
    symbol TEXT NOT NULL,
    regime TEXT,  -- 'bullish', 'bearish', 'sideways'
    stop_loss REAL,
    take_profit REAL,
    position_size_pct REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### calibration_events
Parameter calibration history.
```sql
CREATE TABLE calibration_events (
    id SERIAL PRIMARY KEY,
    strategy TEXT NOT NULL,
    old_params JSONB,
    new_params JSONB,
    trigger_reason TEXT,
    calibrated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### calibration_metrics
Calibration performance metrics.
```sql
CREATE TABLE calibration_metrics (
    id SERIAL PRIMARY KEY,
    calibration_id INTEGER REFERENCES calibration_events(id),
    win_rate_before REAL,
    win_rate_after REAL,
    sharpe_before REAL,
    sharpe_after REAL,
    measured_at TIMESTAMP
);
```

---

## System Tables (4)

### schema_migrations
Database migration tracking.
```sql
CREATE TABLE schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name TEXT UNIQUE NOT NULL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT true
);
```

---

## On-Chain Intelligence Tables (4)

### whale_transactions
Large transaction tracking.
```sql
CREATE TABLE whale_transactions (
    id SERIAL PRIMARY KEY,
    tx_hash TEXT UNIQUE,
    from_address TEXT,
    to_address TEXT,
    amount REAL,
    token TEXT,
    usd_value REAL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### exchange_flows
Exchange inflow/outflow tracking.
```sql
CREATE TABLE exchange_flows (
    id SERIAL PRIMARY KEY,
    exchange TEXT NOT NULL,
    token TEXT NOT NULL,
    flow_type TEXT,  -- 'inflow', 'outflow'
    amount REAL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### smart_money_signals
Aggregated smart money indicators.
```sql
CREATE TABLE smart_money_signals (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    signal_type TEXT,
    score REAL,
    sources JSONB,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### network_metrics
Blockchain network health metrics.
```sql
CREATE TABLE network_metrics (
    id SERIAL PRIMARY KEY,
    network TEXT NOT NULL,  -- 'bitcoin', 'ethereum'
    metric_type TEXT,
    metric_value REAL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Connection Configuration

### Environment Variables
```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

### Railway Reference
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

### Connection Pool Settings
- Max connections: 20
- Min connections: 5
- Connection timeout: 30s
- Idle timeout: 600s

---

## Backup & Recovery

### Railway Automatic Backups
- Daily automatic backups
- 7-day retention
- Point-in-time recovery available

### Manual Backup
```bash
pg_dump $DATABASE_URL > omnix_backup_$(date +%Y%m%d).sql
```

### Restore
```bash
psql $DATABASE_URL < omnix_backup_20241201.sql
```

---

**Document Version:** 3.0  
**OMNIX V6.5 INSTITUTIONAL+**  
**Last Updated:** December 2024
