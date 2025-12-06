# OMNIX INSTITUTIONAL+ Database - Audit Report

> **Version Control**: Current system version is defined in `omnix_config/settings.py`. 
> See VERSION_BANNER for the authoritative version string.

> **Document:** Database Audit & Remediation Guide  
> **Location:** `docs/core/DATABASE_AUDIT_REPORT.md`  
> **Version:** 3.2  
> **Last Updated:** December 6, 2025  
> **Status:** Phase 4.1 Complete (execute_query migration)
>
> **Related:** [Omnix_TECHNICAL_REFERENCE.md](Omnix_TECHNICAL_REFERENCE.md) | [OMNIX_MODULE_CATALOG.md](OMNIX_MODULE_CATALOG.md)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current Status Dashboard](#2-current-status-dashboard)
3. [Integrity Risks & Gaps](#3-integrity-risks--gaps)
4. [Remediation Roadmap](#4-remediation-roadmap)
5. [Execution Playbooks](#5-execution-playbooks)
6. [Appendix A: Schema Reference](#appendix-a-schema-reference)
7. [Appendix B: SQL Templates](#appendix-b-sql-templates)
8. [Revision History](#revision-history)

---

## 1. Executive Summary

### 1.1 Key Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Total Tables | 42 | 42 | ✅ Consolidated |
| Foreign Keys | 38 (90%) | 18+ (40%) | ✅ EXCEEDED |
| Tables with user_id + FK | 38 of 42 | 20+ | ✅ Complete |
| Redundant Table Pairs | 0 | 0 | ✅ RESOLVED |
| Database Services | 2 (dual) | 1 (unified) | 🟡 Canary Active |

### 1.2 Critical Findings

| # | Finding | Severity | Phase to Fix |
|---|---------|----------|--------------|
| 1 | 34 tables have user_id without FK constraint | ✅ RESOLVED | Phase 3 ✅ |
| 2 | Dual database services competing for connections | 🔴 CRITICAL | Phase 2 ✅ (canary) |
| 3 | 3 pairs of redundant tables causing confusion | ✅ RESOLVED | Phase 3.6 ✅ |
| 4 | 14 tables undocumented in DATABASE.md | ✅ RESOLVED | Done |
| 5 | Query duplication across endpoints | 🟡 MEDIUM | Phase 4 |

### 1.3 System Contract

> **All database consumers must use tuple-based row access `row[n]` (psycopg3 default), NOT dict access `row['key']`.**

---

## 2. Current Status Dashboard

### 2.1 Quick Status (December 4, 2025)

```
╔══════════════════════════════════════════════════════════════════╗
║                    OMNIX DATABASE STATUS                          ║
╠══════════════════════════════════════════════════════════════════╣
║  🟢 Gateway Canary: ACTIVE (USE_UNIFIED_GATEWAY=true)            ║
║  🟢 Auto-Migrations: DISABLED (DISABLE_AUTO_MIGRATIONS=true)     ║
║  🟢 Trading: No interruptions                                     ║
║  🟢 FK Coverage: 38/42 tables (90%) ← EXCEEDED TARGET            ║
║  🟢 Orphan Scan: Complete - 34/34 tables clean                   ║
║  🟢 System User: Created (user_id='system')                      ║
║  🟢 Table Consolidation: 3 redundant tables removed              ║
╚══════════════════════════════════════════════════════════════════╝
```

### 2.2 Phase Progress

| Phase | Name | Status | Started | Completed |
|-------|------|--------|---------|-----------|
| 1 | Discovery & Freeze | ✅ Complete | Dec 3, 2025 | Dec 3, 2025 |
| 2 | Build Unified Gateway | 🟡 80% | Dec 3, 2025 | - |
| 3 | Data Integrity Hardening | ✅ Complete | Dec 4, 2025 | Dec 4, 2025 |
| 4 | Service Unification | 🟡 50% | Dec 5, 2025 | - |

### 2.3 Outstanding Blockers

| Blocker | Impact | Owner | ETA |
|---------|--------|-------|-----|
| 48h canary validation needed | Phase 2 still in progress | System | Dec 6, 2025 |
| Enterprise consumers not migrated | Old service still active | Agent | Phase 4 |

### 2.4 Feature Flags (Railway)

| Flag | Value | Purpose |
|------|-------|---------|
| `USE_UNIFIED_GATEWAY` | `true` | Route queries through DatabaseGateway |
| `DISABLE_AUTO_MIGRATIONS` | `true` | Skip 8 auto-migration routines |
| `DB_POOL_MIN` | `2` | Minimum pool connections |
| `DB_POOL_MAX` | `15` | Maximum pool connections |

---

## 3. Integrity Risks & Gaps

### 3.1 Missing Foreign Keys (34 Tables)

Tables with `user_id` column but no FK to `users` table:

#### 3.1.1 Complete Table List by Batch

| Batch | Priority | Tables | Count | Phase |
|-------|----------|--------|-------|-------|
| **Batch 1: Analytics** | 🟢 LOW | community_feedback, community_signals, strategy_votes, improvement_proposals, user_rewards | 5 | 3.3 |
| **Batch 2: Risk** | 🟠 MEDIUM | risk_alerts, risk_events, risk_limits, risk_limit_breaches, risk_guardian_events | 5 | 3.4 |
| **Batch 3: Trading** | 🔴 HIGH | paper_trading_trades, paper_trading_balances, trades, perpetual_positions, derivatives_orders | 5 | 3.5 |

#### 3.1.2 Additional Tables (19) - By Category

| Category | Tables | Priority | Phase |
|----------|--------|----------|-------|
| Risk Logs | risk_guardian_logs, memory_risk_patterns, limit_checks | 🟡 MEDIUM | 3.4 |
| Derivatives | funding_arbitrage, funding_payments, hedge_positions, margin_calls | 🟡 MEDIUM | 3.5 |
| Patterns | detected_patterns, pending_evaluations, trade_evaluations, trade_reasonings | 🟢 LOW | 3.3 |
| Snapshots | position_snapshots, audited_snapshots | 🟢 LOW | 3.3 |
| Circuit Breaker | circuit_breaker_states, circuit_breaker_status | 🟢 LOW | 3.3 |
| Other | conversations, user_settings, user_contributions, arbitrage_opportunities | 🟡 MEDIUM | 3.4 |

#### 3.1.3 Full Reference List (for Orphan Scan)

All 34 tables requiring FK addition:
```
 1. arbitrage_opportunities     18. memory_risk_patterns
 2. audited_snapshots           19. paper_trading_balances
 3. circuit_breaker_states      20. paper_trading_trades
 4. circuit_breaker_status      21. pending_evaluations
 5. community_feedback          22. perpetual_positions
 6. community_signals           23. position_snapshots
 7. conversations               24. risk_alerts
 8. derivatives_orders          25. risk_events
 9. detected_patterns           26. risk_guardian_events
10. funding_arbitrage           27. risk_guardian_logs
11. funding_payments            28. risk_limit_breaches
12. hedge_positions             29. risk_limits
13. improvement_proposals       30. strategy_votes
14. limit_checks                31. trade_evaluations
15. margin_calls                32. trade_reasonings
16. trades                      33. user_contributions
17. user_rewards                34. user_settings
```

**Impact**: Without FKs, orphan records can exist → breaks audits and data integrity.

### 3.2 Redundant Tables ✅ CONSOLIDATED

| Kept | Dropped | Overlap | Status |
|------|---------|---------|--------|
| `circuit_breaker_status` | `circuit_breaker_states` | 70% | ✅ DROPPED Dec 4 |
| `risk_guardian_events` | `risk_guardian_logs` | 60% | ✅ DROPPED Dec 4 |
| `paper_trading_trades` | `trading_history` | 80% | ✅ DROPPED Dec 4 |

**Consolidation Summary (Dec 4, 2025):**
- 3 redundant tables dropped: `circuit_breaker_states`, `risk_guardian_logs`, `trading_history`
- All had 0 rows and 0 code references (verified via grep)
- Total tables: 45 → 42
- FK count adjusted: 41 → 38 (3 FKs on dropped tables removed)

### 3.3 Service Duplication (Resolved by Phase 2)

| Service | Location | Status |
|---------|----------|--------|
| Dashboard Pool | `omnix_dashboard/utils/database.py` | 🟡 Routed via Gateway |
| Enterprise Service | `omnix_services/database_service/database_service.py` | ⬜ Pending migration |
| **Unified Gateway** | `omnix_services/database_service/database_gateway.py` | 🟢 Active (canary) |

### 3.4 Existing Foreign Keys (8 total)

| Table | Column | References |
|-------|--------|------------|
| ai_interactions | user_id | users.user_id |
| audited_snapshots | risk_snapshot_id | risk_metrics_snapshots.id |
| balance_history | user_id | users.user_id |
| conversation_memory | user_id | users.user_id |
| performance_metrics | user_id | users.user_id |
| trading_history | user_id | users.user_id |
| user_contacts | user_id | users.user_id |
| whatsapp_messages | user_id | users.user_id |

---

## 4. Remediation Roadmap

### Phase 1: Discovery & Freeze ✅ COMPLETE

| Task | Status | Date |
|------|--------|------|
| 1.1 Document all call sites | ✅ Done | Dec 3 |
| 1.2 Create DISABLE_AUTO_MIGRATIONS flag | ✅ Done | Dec 3 |
| 1.3 Add pool telemetry logging | ✅ Done | Dec 3 |
| 1.4 Create /api/db-diagnostics endpoint | ✅ Done | Dec 3 |
| 1.5 Document consumer migration order | ✅ Done | Dec 3 |

---

### Phase 2: Build Unified Gateway 🟡 80% COMPLETE

**Goal**: Single connection pool for all consumers

| Task | Status | Date | Notes |
|------|--------|------|-------|
| 2.1 Create DatabaseGateway class | ✅ Done | Dec 3 | Fork-safe singleton |
| 2.2 Fix auto_trading_bot.py dict access | ✅ Done | Dec 3 | Lines 787, 839, 908, 2050 |
| 2.3 Configure Gunicorn post_fork hook | ✅ Done | Dec 3 | gunicorn.conf.py |
| 2.4 Migrate Dashboard consumers | ✅ Done | Dec 3 | Via get_db_connection() |
| 2.5 Canary deployment (1h test) | ✅ Done | Dec 4 | 7 trades, 11/11 widgets OK |
| 2.6 24h canary validation | 🟡 Active | Dec 4-6 | In progress |
| 2.7 Migrate Enterprise consumers | ⬜ Pending | - | Phase 4 |
| 2.8 Deprecate old pool code | ⬜ Pending | - | Phase 4 |

**Architecture**:
```
ALL Consumers → DatabaseGateway → Single Pool → PostgreSQL
```

---

### Phase 3: Data Integrity Hardening ✅ COMPLETE

**Goal**: Add FKs, clean orphans, consolidate tables  
**Completed**: Dec 4, 2025

| Task | Description | Risk | Status | Date |
|------|-------------|------|--------|------|
| 3.1 | Orphan Scan - detect orphan user_ids | 🟢 LOW | ✅ Done | Dec 4 |
| 3.2 | Data Cleanup - created 'system' user | 🟡 MEDIUM | ✅ Done | Dec 4 |
| 3.3 | FK Batch 1 - 5 analytics tables | 🟢 LOW | ✅ Done | Dec 4 |
| 3.4 | FK Batch 2 - 8 risk tables | 🟡 MEDIUM | ✅ Done | Dec 4 |
| 3.5 | FK Batch 3 - 9 trading tables | 🔴 HIGH | ✅ Done | Dec 4 |
| 3.6 | FK Remaining - 12 pattern/snapshot/other | 🟢 LOW | ✅ Done | Dec 4 |
| 3.7 | Table Consolidation - Drop 3 redundant tables | 🟡 MEDIUM | ✅ Done | Dec 4 |

**Results**:
- Orphan scan: 34/34 tables clean (1 orphan resolved by creating system user)
- FKs added: 34 new constraints (total: 38 FKs, 90% coverage after consolidation)
- Table consolidation: 3 redundant tables dropped (45 → 42 tables)
- Dashboard verified: 11/11 widgets OK, 7 real trades

---

### Phase 4: Service Unification 🟡 IN PROGRESS

**Goal**: Complete migration, deprecate legacy  
**Pre-requisite**: Phase 3 FKs stable  
**Started**: December 5, 2025

| Task | Description | Risk | Status | Date |
|------|-------------|------|--------|------|
| 4.1 | execute_query() Gateway Integration | 🔴 HIGH | ✅ Done | Dec 5 |
| 4.2 | Bot Migration (enterprise_bot.py, main.py) | 🔴 HIGH | ✅ Implicit | Dec 5 |
| 4.3 | Legacy Deprecation Warnings | 🟡 MEDIUM | ✅ Done | Dec 5 |
| 4.4 | Documentation Update | 🟢 LOW | ✅ Done | Dec 5 |

**Implementation Notes (Dec 5, 2025)**:
- Modified `DatabaseServiceEnterprise.execute_query()` to route through `DatabaseGateway` when `USE_UNIFIED_GATEWAY=true`
- Added lazy-loaded `_get_gateway()` helper to avoid circular imports
- Added deprecation warning for `_get_connection()` legacy usage
- All consumers using `execute_query()` automatically benefit from unified pool
- Fallback to legacy connections preserved for robustness

---

### Phase 4.5: Defensive Migrations ✅ COMPLETE

**Goal**: Eliminate startup warnings from schema mismatches  
**Completed**: December 6, 2025

| Task | Description | Risk | Status | Date |
|------|-------------|------|--------|------|
| 4.5.1 | FK Migrations - verify column exists before ADD CONSTRAINT | 🟢 LOW | ✅ Done | Dec 6 |
| 4.5.2 | CHECK Migrations - verify column exists before ADD CONSTRAINT | 🟢 LOW | ✅ Done | Dec 6 |
| 4.5.3 | Cleanup TTL - verify timestamp column exists before DELETE | 🟢 LOW | ✅ Done | Dec 6 |

**Problem Resolved**:
Startup warnings caused by migrations attempting to add constraints to columns that don't exist in Railway database:
- `fk_signals_contributor` → column `contributor_id` doesn't exist in `community_signals`
- `chk_feedback_result` → column `result` doesn't exist in `community_feedback`  
- Cleanup TTL → column `timestamp` doesn't exist in some tables (uses `created_at`)

**Solution Applied**:
Added `column_exists()` helper functions to verify column presence before:
1. Adding FK constraints (`_add_foreign_key_constraints()`)
2. Adding CHECK constraints (`_add_check_constraints()`)
3. Executing cleanup DELETEs (`_cleanup_old_data()`)

**Result**: Clean startup with no warnings - migrations are now fully defensive and idempotent.

---

## 5. Execution Playbooks

### 5.1 Playbook: Orphan Scan (Phase 3.1)

**Purpose**: Detect user_ids that don't exist in `users` table

```sql
-- Run for each table with user_id column
SELECT 
    '[TABLE_NAME]' as table_name,
    COUNT(*) as orphan_count,
    ARRAY_AGG(DISTINCT user_id) as sample_ids
FROM [TABLE_NAME] t
WHERE t.user_id IS NOT NULL 
  AND NOT EXISTS (SELECT 1 FROM users u WHERE u.user_id = t.user_id);
```

**Tables to scan** (34): See Section 3.1.3 for complete list

---

### 5.2 Playbook: Data Cleanup (Phase 3.2)

| Strategy | When to Use | SQL Pattern |
|----------|-------------|-------------|
| DELETE | Old/irrelevant records | `DELETE FROM t WHERE user_id NOT IN (SELECT user_id FROM users) AND created_at < NOW() - '90 days'` |
| SET NULL | Keep record, user optional | `UPDATE t SET user_id = NULL WHERE ...` |
| REASSIGN | Migrate to system user | `UPDATE t SET user_id = 'SYSTEM' WHERE ...` |
| CREATE | User should exist | `INSERT INTO users (user_id) SELECT DISTINCT user_id FROM t WHERE ...` |

---

### 5.3 Playbook: Add FK Constraints (Phase 3.3-3.5)

**Pattern** (use for each table):

```sql
-- Set timeout to avoid long locks
SET lock_timeout = '5s';

-- Add FK with DEFERRABLE for safety
ALTER TABLE [table_name] 
  ADD CONSTRAINT fk_[table_name]_user 
  FOREIGN KEY (user_id) REFERENCES users(user_id) 
  DEFERRABLE INITIALLY DEFERRED;
```

**Rollback**:
```sql
ALTER TABLE [table_name] DROP CONSTRAINT IF EXISTS fk_[table_name]_user;
```

---

### 5.4 Playbook: Table Consolidation (Phase 3.6)

```
=== CONSOLIDATION: [SOURCE] → [TARGET] ===

1. ANALYSIS
   - Compare columns: SELECT column_name FROM information_schema.columns WHERE table_name = '[name]'
   - Count rows: SELECT COUNT(*) FROM [table]
   - Map columns: source_col → target_col

2. PREPARATION
   - Add missing columns to target
   - Create backup: CREATE TABLE [source]_backup AS SELECT * FROM [source]

3. MIGRATION
   - INSERT INTO [target] SELECT ... FROM [source] WHERE NOT EXISTS (...)
   - Verify counts match

4. CUTOVER
   - Update code: grep -r "[source]" omnix_*
   - Rename: ALTER TABLE [source] RENAME TO [source]_deprecated
   - Monitor 7 days

5. CLEANUP
   - DROP TABLE [source]_deprecated
```

---

### 5.5 Playbook: Enterprise Migration (Phase 4.1-4.2)

**Pattern for each file**:

```python
# At top of file
import os
USE_UNIFIED_GATEWAY = os.environ.get('USE_UNIFIED_GATEWAY', 'false').lower() == 'true'

def _get_db():
    if USE_UNIFIED_GATEWAY:
        from omnix_services.database_service.database_gateway import DatabaseGateway
        return DatabaseGateway()
    else:
        return db_service  # Legacy

# Replace each db call:
# Before: db_service.execute_query(...)
# After:  _get_db().execute_query(...)
```

**Files to migrate**:
1. `omnix_services/trading_service/paper_trading_manager.py`
2. `omnix_services/telegram_service/enterprise_bot.py`
3. `main.py`

---

## Appendix A: Schema Reference

### A.1 All Tables Summary (45 total)

| # | Table | Cols | FK | user_id | Category |
|---|-------|------|-----|---------|----------|
| 1 | users | 18 | - | ✅ | Core |
| 2 | user_settings | 25 | ❌ | ✅ | Core |
| 3 | user_contacts | 7 | ✅ | ✅ | Core |
| 4 | user_contributions | 7 | ❌ | ✅ | Core |
| 5 | paper_trading_trades | 13 | ❌ | ✅ | Trading |
| 6 | paper_trading_balances | 15 | ❌ | ✅ | Trading |
| 7 | trades | 12 | ❌ | ✅ | Trading |
| 8 | trading_history | 15 | ✅ | ✅ | Trading |
| 9 | balance_history | 6 | ✅ | ✅ | Trading |
| 10 | ai_interactions | 9 | ✅ | ✅ | AI |
| 11 | conversations | 6 | ❌ | ✅ | AI |
| 12 | conversation_memory | 6 | ✅ | ✅ | AI |
| 13-21 | *Risk tables (9)* | 6-10 | ❌ | ✅ | Risk |
| 22-27 | *Derivatives tables (6)* | 7-13 | ❌ | ✅ | Derivatives |
| 28-32 | *Community tables (5)* | 6-11 | ❌ | ✅ | Community |
| 33-37 | *Snapshots & Patterns (5)* | 7-19 | ✅/❌ | ✅ | Analytics |
| 38-45 | *System & Other (8)* | 5-9 | ❌ | ❌/✅ | System |

### A.2 Tables by Category

#### Core User Tables
- `users` (18 cols) - Master user table, PRIMARY KEY user_id
- `user_settings` (25 cols) - User preferences and trading config
- `user_contacts` (7 cols) - Contact info, FK to users
- `user_contributions` (7 cols) - User contributions tracking

#### Trading Tables
- `paper_trading_trades` (13 cols) - Paper trades, NEEDS FK
- `paper_trading_balances` (15 cols) - User balances, NEEDS FK
- `trades` (12 cols) - Exchange trades, NEEDS FK
- `trading_history` (15 cols) - Historical trades, HAS FK
- `balance_history` (6 cols) - Balance changes, HAS FK

#### Risk Management Tables
- `risk_alerts` (8 cols) - User alerts
- `risk_events` (9 cols) - Risk events log
- `risk_limits` (8 cols) - User limits
- `risk_limit_breaches` (8 cols) - Breach log
- `risk_guardian_events` (8 cols) - Guardian events
- `risk_guardian_logs` (6 cols) - REDUNDANT with events
- `risk_metrics_snapshots` (10 cols) - Risk metrics
- `limit_checks` (8 cols) - Limit validation
- `memory_risk_patterns` (7 cols) - Non-Markovian patterns

#### Derivatives Tables
- `derivatives_orders` (12 cols) - Derivative orders
- `perpetual_positions` (13 cols) - Perp positions
- `funding_payments` (7 cols) - Funding rate payments
- `funding_arbitrage` (11 cols) - Arbitrage opportunities
- `hedge_positions` (10 cols) - Spot-perp hedges
- `margin_calls` (9 cols) - Margin call events

#### Community Tables
- `community_feedback` (7 cols)
- `community_signals` (11 cols)
- `strategy_votes` (6 cols)
- `improvement_proposals` (10 cols)
- `user_rewards` (7 cols)

#### Circuit Breaker Tables
- `circuit_breaker_states` (8 cols) - REDUNDANT
- `circuit_breaker_status` (9 cols) - Keep this one

#### Snapshots & Analysis Tables
- `audited_snapshots` (19 cols) - Audited snapshots, HAS FK
- `position_snapshots` (10 cols) - Position snapshots
- `detected_patterns` (9 cols) - Pattern detection
- `pending_evaluations` (13 cols) - Pending evals (updated Dec 4)
- `trade_evaluations` (8 cols) - Trade evaluations
- `trade_reasonings` (7 cols) - Trade reasoning

#### System Tables
- `schema_migrations` (5 cols) - Migration tracking
- `system_config` (5 cols) - System configuration
- `whatsapp_messages` (8 cols) - WhatsApp integration, HAS FK
- `performance_metrics` (7 cols) - Performance tracking, HAS FK
- `arbitrage_opportunities` (13 cols) - Arbitrage detection

### A.3 Index Summary

| Type | Count | Examples |
|------|-------|----------|
| Primary Key | 45 | `*_pkey` on all tables |
| Unique | 7 | `users_telegram_id`, `schema_migrations_migration_name` |
| User ID | 8 | `idx_conversations_user_id`, `idx_detected_patterns_user_id` |
| Composite | 2 | `audited_snapshots(snapshot_type, snapshot_date)` |
| Partial | 2 | `idx_user_settings_paused WHERE is_paused = true` |
| Status | 1 | `idx_pending_evaluations_status_due_time` (added Dec 4) |

---

## Appendix B: SQL Templates

### B.1 FK Batch 1 - Analytics Tables

```sql
-- Phase 3.3: FK Batch 1 - Analytics Tables
-- Risk: LOW | Execution: Any time

SET lock_timeout = '5s';

ALTER TABLE community_feedback 
  ADD CONSTRAINT fk_community_feedback_user 
  FOREIGN KEY (user_id) REFERENCES users(user_id) 
  DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE community_signals 
  ADD CONSTRAINT fk_community_signals_user 
  FOREIGN KEY (user_id) REFERENCES users(user_id) 
  DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE strategy_votes 
  ADD CONSTRAINT fk_strategy_votes_user 
  FOREIGN KEY (user_id) REFERENCES users(user_id) 
  DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE improvement_proposals 
  ADD CONSTRAINT fk_improvement_proposals_user 
  FOREIGN KEY (user_id) REFERENCES users(user_id) 
  DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE user_rewards 
  ADD CONSTRAINT fk_user_rewards_user 
  FOREIGN KEY (user_id) REFERENCES users(user_id) 
  DEFERRABLE INITIALLY DEFERRED;
```

### B.2 FK Batch 2 - Risk Tables

```sql
-- Phase 3.4: FK Batch 2 - Risk Management Tables
-- Risk: MEDIUM | Execution: Low-activity window

SET lock_timeout = '5s';

ALTER TABLE risk_alerts 
  ADD CONSTRAINT fk_risk_alerts_user 
  FOREIGN KEY (user_id) REFERENCES users(user_id) 
  DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE risk_events 
  ADD CONSTRAINT fk_risk_events_user 
  FOREIGN KEY (user_id) REFERENCES users(user_id) 
  DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE risk_limits 
  ADD CONSTRAINT fk_risk_limits_user 
  FOREIGN KEY (user_id) REFERENCES users(user_id) 
  DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE risk_limit_breaches 
  ADD CONSTRAINT fk_risk_limit_breaches_user 
  FOREIGN KEY (user_id) REFERENCES users(user_id) 
  DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE risk_guardian_events 
  ADD CONSTRAINT fk_risk_guardian_events_user 
  FOREIGN KEY (user_id) REFERENCES users(user_id) 
  DEFERRABLE INITIALLY DEFERRED;
```

### B.3 FK Batch 3 - Trading Tables

```sql
-- Phase 3.5: FK Batch 3 - Trading Core Tables
-- Risk: HIGH | Execution: MAINTENANCE WINDOW ONLY

SET lock_timeout = '3s';

-- Fix type mismatch first
ALTER TABLE paper_trading_balances 
  ALTER COLUMN user_id TYPE VARCHAR USING user_id::VARCHAR;

-- Add FKs
ALTER TABLE paper_trading_trades 
  ADD CONSTRAINT fk_paper_trading_trades_user 
  FOREIGN KEY (user_id) REFERENCES users(user_id) 
  DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE paper_trading_balances 
  ADD CONSTRAINT fk_paper_trading_balances_user 
  FOREIGN KEY (user_id) REFERENCES users(user_id) 
  DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE trades 
  ADD CONSTRAINT fk_trades_user 
  FOREIGN KEY (user_id) REFERENCES users(user_id) 
  DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE perpetual_positions 
  ADD CONSTRAINT fk_perpetual_positions_user 
  FOREIGN KEY (user_id) REFERENCES users(user_id) 
  DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE derivatives_orders 
  ADD CONSTRAINT fk_derivatives_orders_user 
  FOREIGN KEY (user_id) REFERENCES users(user_id) 
  DEFERRABLE INITIALLY DEFERRED;
```

### B.4 Rollback Scripts

```sql
-- Rollback Batch 1
ALTER TABLE community_feedback DROP CONSTRAINT IF EXISTS fk_community_feedback_user;
ALTER TABLE community_signals DROP CONSTRAINT IF EXISTS fk_community_signals_user;
ALTER TABLE strategy_votes DROP CONSTRAINT IF EXISTS fk_strategy_votes_user;
ALTER TABLE improvement_proposals DROP CONSTRAINT IF EXISTS fk_improvement_proposals_user;
ALTER TABLE user_rewards DROP CONSTRAINT IF EXISTS fk_user_rewards_user;

-- Rollback Batch 2
ALTER TABLE risk_alerts DROP CONSTRAINT IF EXISTS fk_risk_alerts_user;
ALTER TABLE risk_events DROP CONSTRAINT IF EXISTS fk_risk_events_user;
ALTER TABLE risk_limits DROP CONSTRAINT IF EXISTS fk_risk_limits_user;
ALTER TABLE risk_limit_breaches DROP CONSTRAINT IF EXISTS fk_risk_limit_breaches_user;
ALTER TABLE risk_guardian_events DROP CONSTRAINT IF EXISTS fk_risk_guardian_events_user;

-- Rollback Batch 3
ALTER TABLE paper_trading_trades DROP CONSTRAINT IF EXISTS fk_paper_trading_trades_user;
ALTER TABLE paper_trading_balances DROP CONSTRAINT IF EXISTS fk_paper_trading_balances_user;
ALTER TABLE trades DROP CONSTRAINT IF EXISTS fk_trades_user;
ALTER TABLE perpetual_positions DROP CONSTRAINT IF EXISTS fk_perpetual_positions_user;
ALTER TABLE derivatives_orders DROP CONSTRAINT IF EXISTS fk_derivatives_orders_user;
```

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 3.2 | Dec 5, 2025 | **Phase 4.1 Complete**: `execute_query()` migrated to use DatabaseGateway when `USE_UNIFIED_GATEWAY=true`. All enterprise consumers automatically use unified pool. Deprecation warnings added. |
| 3.1 | Dec 4, 2025 | **Table Consolidation Complete**: Dropped 3 redundant tables (circuit_breaker_states, risk_guardian_logs, trading_history). Total: 45→42 tables, 41→38 FKs |
| 3.0 | Dec 4, 2025 | **Major reorganization**: Consolidated from 2699 to ~600 lines. Added Status Dashboard, consolidated schema refs to appendix, organized phases as tables. |
| 2.4 | Dec 4, 2025 | Added Phase 3-4 detailed implementation plan |
| 2.3 | Dec 4, 2025 | Updated Phase 2 canary status, pending_evaluations schema fix |
| 2.2 | Dec 3, 2025 | Phase 2 implementation started, Gateway created |
| 2.1 | Dec 3, 2025 | Phase 1 complete, call sites documented |
| 2.0 | Dec 3, 2025 | Added Phase 1-2 implementation plans |
| 1.0 | Dec 2, 2025 | Initial audit report |

---

## Success Criteria

### Phase 2 Complete When:
- [x] DatabaseGateway created with fork-safe singleton
- [x] Dashboard consumers migrated
- [x] Canary deployment active (validated Dec 4-5, 2025)
- [x] Enterprise consumers migrated (via execute_query() routing - Dec 5, 2025)
- [x] Old pool code deprecated (warnings added to _get_connection())

### Phase 3 Complete When: ✅ COMPLETED Dec 4, 2025
- [x] Orphan scan executed on all 34 tables (33/34 clean, 1 resolved)
- [x] Orphan records cleaned/reassigned (created 'system' user)
- [x] FK Batch 1-3 added (34 FKs total - EXCEEDED target of 15)
- [x] Table consolidation executed (3 redundant tables dropped)

**Verification Evidence (pg_constraint)**:
- 34 FKs added: All confirmed DEFERRABLE=YES, INITIALLY_DEFERRED=YES
- 7 original FKs (*_user_id_fkey pattern) already existed
- System user: `user_id='system'`, created `2025-12-04 07:21:39`
- Total FK coverage: 38 FKs to users table (90% - adjusted after consolidation)
- Tables consolidated: 45 → 42 (dropped circuit_breaker_states, risk_guardian_logs, trading_history)

### Phase 4 Complete When:
- [x] All Enterprise consumers using DatabaseGateway (via execute_query migration)
- [x] Deprecation warnings added to _get_connection()
- [x] FK count increased to 18+ (from 8) - NOW 38 (EXCEEDED, adjusted after consolidation)

---

**Document Version:** 3.1  
**OMNIX INSTITUTIONAL+**  
**Audit Date:** December 2025  
**Contact:** Development Team
