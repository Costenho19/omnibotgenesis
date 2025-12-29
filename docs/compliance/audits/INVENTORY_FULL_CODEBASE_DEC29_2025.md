# OMNIX Codebase Inventory Audit
**Date:** December 29, 2025  
**Auditor:** AI Senior Fullstack Engineer  
**Status:** PHASE 1 - INVENTORY COMPLETE (REVISED)

---

## Executive Summary

| Category | Files | Status |
|----------|-------|--------|
| **Python (.py)** | 415 | Pending audit |
| **SQL (.sql)** | 3 | Pending audit |
| **Markdown (.md)** | 69 | Pending audit |
| **Total Project Files** | 487 | Pending consolidation |

---

## 1. Python Files Inventory by Tier

### Tier 1: CRITICAL RUNTIME (218 files)

#### omnix_core/ (29 files)
Core business logic - HIGHEST PRIORITY

| Directory | Files | Purpose |
|-----------|-------|---------|
| `bot/` | 3 | Auto trading bot, paper trading |
| `cache/` | 3 | Redis cache, state management |
| `config/` | 2 | Trading profiles |
| `context/` | 2 | Real data provider |
| `quantum/` | 5 | D-Wave QAOA, physics validation |
| `risk/` | 1 | Rollback protocol |
| `security/` | 2 | Post-quantum cryptography |
| `sessions/` | 2 | User session management |
| `strategies/` | 4 | CAES, EMA, Non-Markovian kernel |
| `utils/` | 3 | Logger, rate limiter |
| Root | 2 | trading_system.py, __init__.py |

#### omnix_services/ (189 files)
Service layer - HIGH PRIORITY

| Subdirectory | Files | Purpose |
|--------------|-------|---------|
| `ai_service/` | 35 | AI providers, prompts, conversational brain |
| `trading_service/` | 19 | Kraken, Monte Carlo, Kalman, HMM, Kelly |
| `stock_trading/` | 19 | Alpaca integration, stock trading |
| `market_data/` | 17 | Market data feeds |
| `derivatives/` | 8 | Futures, hedging, margin |
| `database_service/` | 8 | Database manager, migrations |
| `portfolio_management/` | 8 | Institutional portfolio optimizer |
| `risk_management/` | 8 | Risk management services |
| `analytics/` | 7 | Analytics engine |
| `optimization/` | 7 | Performance optimizer |
| `community_intelligence/` | 6 | Community intelligence |
| `monitoring/` | 6 | Analytics, latency, health checks |
| `telegram_service/` | 6 | Enterprise bot, callbacks |
| `execution_service/` | 5 | Execution protocol, liquidity |
| `concurrency/` | 4 | Concurrency management |
| `market_intelligence/` | 4 | Fear/Greed, Finnhub, Alpha Vantage |
| `notifications/` | 4 | Trade notifications, daily summary |
| `web_search_service/` | 4 | Tavily search integration |
| `coherence_service/` | 3 | Coherence engine V5.4 |
| `user_settings/` | 3 | User preferences |
| `voice_service/` | 3 | TTS/STT services |
| `adaptive_engine/` | 2 | Adaptive parameter engine |
| Root | 3 | Module init, symbol classifier, news scraper |

### Tier 2: HEXAGONAL ARCHITECTURE V7 (99 files)

#### src/omnix/ (99 files)
New architecture - MEDIUM-HIGH PRIORITY

| Directory | Files | Purpose | Status |
|-----------|-------|---------|--------|
| `infrastructure/` | 26 | Adapters (DB, API, external services) | Partially active |
| `ports/` | 25 | Port interfaces (contracts) | Planned |
| `domain/` | 22 | Entities, value objects, services | Planned |
| `application/` | 16 | Use cases, DTOs, orchestration | Planned |
| `bootstrap/` | 5 | DI container, entry points | Active |
| `config/` | 2 | Configuration modules | Active |
| `interfaces/` | 2 | Interface definitions | Planned |
| Root | 1 | __init__.py | - |

### Tier 3: CONFIGURATION (3 Python + 2 JSON files)

#### omnix_config/ (3 Python files)
System configuration - HIGH PRIORITY

| File | Purpose | Status |
|------|---------|--------|
| `settings.py` | Environment settings | KEEP |
| `env_manager.py` | Environment variable manager | KEEP |
| `__init__.py` | Module init | KEEP |

**Additional Config Files (non-Python):**
| File | Purpose | Status |
|------|---------|--------|
| `system_state_manifest.json` | AI self-knowledge | KEEP |
| `grafana/omnix_dashboard.json` | Grafana dashboard config | REVIEW |

### Tier 4: DASHBOARDS & API (22 files)

#### omnix_dashboard/ (18 files)
| File | Purpose |
|------|---------|
| `app.py` | Flask dashboard |
| `streamlit_app.py` | Streamlit dashboard |
| `blueprints/` | Flask blueprints |
| `templates/` | HTML templates |
| `static/` | CSS, JS assets |
| `utils/` | Dashboard utilities |

#### omnix_api/ (4 files)
| File | Purpose |
|------|---------|
| `__init__.py` | API initialization |
| `routes/` | API endpoints |
| `payments/` | Payment processing |

### Tier 5: TESTING HARNESS (53 files)

#### tests/ (34 files)
| Directory | Files | Purpose |
|-----------|-------|---------|
| Root | 24 | Core tests, version tests, integration tests |
| `contracts/` | 5 | Contract tests (port contracts) |
| `application/` | 3 | Application layer tests |
| `integration/` | 2 | Integration tests |

#### omnix_testing/ (19 files)
Backtesting and validation framework - MEDIUM PRIORITY

| Directory | Files | Purpose |
|-----------|-------|---------|
| `backtesting/` | 6 | Backtesting engine, metrics |
| `utils/` | 2 | Testing utilities |
| Root | 11 | Validators, stress tests, TCA |

**Key Files:**
- `run_backtest.py` - Main backtest runner
- `professional_validator.py` - Strategy validation
- `institutional_stress_suite.py` - Stress testing
- `advanced_tca.py` - Transaction cost analysis
- `strategy_comparator.py` - Strategy comparison

### Tier 6: TOOLS & SCRIPTS (10 files)

#### tools/ (8 files)
Developer and operations tools

| Directory | Files | Purpose |
|-----------|-------|---------|
| `operations/` | 3 | Migration watchdog, investor reports |
| `telegram/` | 4 | Chat tools, ID lookup |
| Root | 1 | __init__.py |

#### scripts/ (2 files)
| File | Purpose |
|------|---------|
| `migration/activate_cache_port.py` | Cache port activation |
| `traceability/validate_traceability.py` | Traceability validation |

### Tier 7: SQL MIGRATIONS (3 files)

#### sql/ (3 SQL files)
Database schemas and migrations

| File | Purpose | Status |
|------|---------|--------|
| `migrations/V7_001_fix_schema_discrepancies.sql` | V7 schema fixes | REVIEW |
| `optimization_tables.sql` | Optimization tables | REVIEW |
| `risk_guardian_table.sql` | Risk guardian table | REVIEW |

### Tier 8: ARCHIVE/DEPRECATED (7 files)

#### archive/deprecated_ares/ (7 files)
Deprecated ARES strategies - CANDIDATE FOR DELETION

| Directory | Files | Purpose | Status |
|-----------|-------|---------|--------|
| `stock_trading/` | 1 | ares_stock.py | DELETE |
| `strategies/` | 4 | ares_v1.py, ares_v2.py, etc | DELETE |
| `testing/` | 2 | Validation scripts | DELETE |

### Tier 9: ROOT LEVEL (3 files)
| File | Purpose | Status |
|------|---------|--------|
| `main.py` | Entry point | KEEP |
| `wsgi.py` | WSGI entry | KEEP |
| `start_dashboard.py` | Dashboard starter | KEEP |

---

## 2. Markdown Files Inventory

### docs/ Structure (69 files total)

#### docs/current/ (9 files) - ACTIVE DOCUMENTATION
| File | Purpose | Status |
|------|---------|--------|
| `ARCHITECTURE.md` | System architecture | REVIEW |
| `HEXAGONAL_MIGRATION_STATUS.md` | V7 migration status | REVIEW |
| `TECHNICAL_DEBT.md` | Known technical debt | REVIEW |
| `COMPLETE_FUNCTIONALITY_MAP.md` | Feature map | REVIEW |
| `TRADING_OPERATIONS.md` | Trading operations | REVIEW |
| `MULTI_USER_ARCHITECTURE.md` | Multi-user design | REVIEW |
| `MULTIUSER_PHASE2_DATA_AUDIT.md` | Phase 2 audit | REVIEW |
| `DECISION_CONTRACT.md` | Decision contracts | REVIEW |
| `COMMAND_AUDIT_REPORT.md` | Command audit | REVIEW |

#### docs/compliance/ (7 files) - AUDIT REPORTS & EVIDENCE
| File | Purpose | Status |
|------|---------|--------|
| `audits/OMNIX_SYSTEM_AUDIT_DEC27_2025.md` | Latest audit | KEEP |
| `audits/SENIOR_AUDIT_REPORT_DEC_2025.md` | Senior review | KEEP |
| `audits/INDEPENDENT_TECHNICAL_AUDIT_DEC25_2025.md` | Independent audit | KEEP |
| `audits/DATABASE_AUDIT_REPORT.md` | DB audit | KEEP |
| `audits/INTERNAL_AUDIT_TRANSPARENCY.md` | Transparency report | REVIEW |
| `audits/CODEBASE_INVENTORY_AUDIT_DEC29_2025.md` | This inventory audit | CURRENT |
| `evidence/traceability_validation.md` | Traceability evidence | KEEP |

#### docs/business/ (9 files) - BUSINESS & INVESTOR MATERIALS
| File | Purpose | Status |
|------|---------|--------|
| `B2C_SAAS_PLAN.md` | B2C SaaS business plan | REVIEW |
| `investor/one_pager.md` | One-pager | KEEP |
| `investor/financial_projections.md` | Financials | KEEP |
| `investor/founding_team.md` | Team info | KEEP |
| `investor/current_metrics.md` | Current metrics | UPDATE |
| `investor/feature_catalog.md` | Features | REVIEW |
| `investor/accelerator_application.md` | Accelerator app | KEEP |
| `investor/arabic_executive_summary.md` | Arabic summary | KEEP |
| `investor/gcc_market_readiness.md` | GCC readiness | KEEP |

#### docs/operations/ (12 files) - RUNBOOKS
| File | Purpose | Status |
|------|---------|--------|
| `DEPLOYMENT.md` | Deployment guide | REVIEW |
| `FEATURE_FLAG_ACTIVATION.md` | Feature flags | REVIEW |
| `CONFIGURACION_OPTIMIZADA.md` | Config optimization | REVIEW |
| `RUNBOOK_AI_PORT_ACTIVATION.md` | AI port runbook | REVIEW |
| `RUNBOOK_DERIVATIVES_PORT_ACTIVATION.md` | Derivatives runbook | REVIEW |
| `RUNBOOK_EXECUTION_PORT_ACTIVATION.md` | Execution runbook | REVIEW |
| `RUNBOOK_MARKET_INTEL_PORT_ACTIVATION.md` | Market intel runbook | REVIEW |
| `RUNBOOK_ONCHAIN_PORT_ACTIVATION.md` | On-chain runbook | REVIEW |
| `RUNBOOK_OPTIMIZATION_PORT_ACTIVATION.md` | Optimization runbook | REVIEW |
| `RUNBOOK_PORTFOLIO_PORT_ACTIVATION.md` | Portfolio runbook | REVIEW |
| `RUNBOOK_RISK_CONTROL_PORT_ACTIVATION.md` | Risk control runbook | REVIEW |
| `experimental/quantum_roadmap.md` | Quantum roadmap | REVIEW |

#### docs/history/ (23 files) - HISTORICAL DOCS

##### docs/history/2025-12/ (13 files)
| File | Purpose | Status |
|------|---------|--------|
| `MIGRATION_PLAN.md` | Migration plan | ARCHIVE |
| `PHASE2_PLAN.md` | Phase 2 plan | ARCHIVE |
| `PHASE4_MIGRATION_PLAN.md` | Phase 4 plan | ARCHIVE |
| `REWRITE_PLAN_V7.md` | V7 rewrite plan | ARCHIVE |
| `CODEBASE_AUDIT_REPORT_FULL.md` | Full audit | ARCHIVE |
| `CODEBASE_AUDIT_REPORT_20251215.md` | Dec 15 audit | ARCHIVE |
| `AUDIT_REPORT_20251208_SUPERSEDED.md` | Superseded | DELETE |
| `ARCHITECTURE_AUDIT.md` | Architecture audit | ARCHIVE |
| `FOLDER_AUDIT_PHASE6.md` | Folder audit | ARCHIVE |
| `IMPORT_AUDIT.md` | Import audit | ARCHIVE |
| `RAILWAY_DEPLOYMENT.md` | Railway deploy | KEEP |
| `RAILWAY_DASHBOARD_SETUP.md` | Railway dashboard | KEEP |
| `ares_development_DEPRECATED.md` | Deprecated | DELETE |

##### docs/history/2025-11/ (10 files)
| File | Purpose | Status |
|------|---------|--------|
| `2025-11-26_*.md` (5 files) | November decisions | ARCHIVE |
| `2025-11-27_anu_qrng_activation.md` | QRNG activation | ARCHIVE |
| `arbitrage_system_documentation.md` | Arbitrage docs | ARCHIVE |
| `community_intelligence_documentation.md` | Community intel | ARCHIVE |
| `market_dashboard_documentation.md` | Dashboard docs | ARCHIVE |
| `migration_orm.md` | ORM migration | ARCHIVE |

#### docs/reference/ (2 files)
| File | Purpose | Status |
|------|---------|--------|
| `TRACEABILITY_MATRIX.md` | Traceability | KEEP |
| `adr/ADR-001-hexagonal.md` | ADR hexagonal | KEEP |

#### Root docs/ (3 files)
| File | Purpose | Status |
|------|---------|--------|
| `README.md` | Documentation index | UPDATE |
| `MIGRATION_STATUS.md` | Migration status | UPDATE |
| `REAL_SYSTEM_STATUS.md` | Real system status | UPDATE |

### Other Markdown Files (4 files)
| File | Purpose | Status |
|------|---------|--------|
| `replit.md` | Replit config + memory | UPDATE |
| `CHANGELOG.md` | Change log | UPDATE |
| `tools/README.md` | Tools docs | REVIEW |
| `omnix_testing/README.md` | Testing framework docs | REVIEW |

---

## 3. Recommended Actions Summary

### Files to DELETE (9 files)

**Documentation (2 files):**
- `docs/history/2025-12/AUDIT_REPORT_20251208_SUPERSEDED.md`
- `docs/history/2025-12/ares_development_DEPRECATED.md`

**Code - Deprecated ARES (7 files):**
- `archive/deprecated_ares/stock_trading/ares_stock.py`
- `archive/deprecated_ares/strategies/ares_v1.py`
- `archive/deprecated_ares/strategies/ares_v1_v7.py`
- `archive/deprecated_ares/strategies/ares_v2.py`
- `archive/deprecated_ares/strategies/ares_v2_v7.py`
- `archive/deprecated_ares/testing/run_premium_validation.py`
- `archive/deprecated_ares/testing/validate_ares_strategies.py`

### Files to ARCHIVE (move to history) (~15 files)
- Various migration plans and old audits in `docs/history/`

### Files to UPDATE (10+ files)
- `replit.md` - Consolidate as single source of truth
- `docs/README.md` - Update index
- `docs/MIGRATION_STATUS.md` - Align with current state
- `docs/REAL_SYSTEM_STATUS.md` - Update metrics
- `docs/business/investor/current_metrics.md` - Latest metrics

### Files to REVIEW for potential consolidation
- All `docs/operations/RUNBOOK_*.md` files (8 files) - Consider consolidating into single runbook
- All `docs/current/` files (9 files) - Verify alignment with code
- SQL files in `sql/` - Verify against actual database schema

---

## 4. Next Steps

| Phase | Task | Estimated Effort |
|-------|------|------------------|
| 2A | Audit omnix_core/ (29 files) | 2-3 hours |
| 2B | Audit omnix_services/ (189 files) | 6-8 hours |
| 2C | Audit src/omnix/ (99 files) | 3-4 hours |
| 2D | Audit dashboards/tests (56 files) | 2-3 hours |
| 3 | Documentation audit & cleanup | 3-4 hours |
| 4 | Integration analysis | 2-3 hours |
| 5 | Final consolidation | 2-3 hours |

**Total Estimated Effort:** 20-28 hours

---

## Appendix: File Counts by Directory

```
=== PYTHON FILES ===
omnix_core/          29 files  (Tier 1 - Critical Runtime)
omnix_services/     189 files  (Tier 1 - Critical Runtime)
src/omnix/           99 files  (Tier 2 - Hexagonal V7)
omnix_config/         3 files  (Tier 3 - Configuration)
omnix_dashboard/     18 files  (Tier 4 - Dashboards)
omnix_api/            4 files  (Tier 4 - API)
tests/               34 files  (Tier 5 - Testing)
omnix_testing/       19 files  (Tier 5 - Testing)
tools/                8 files  (Tier 6 - Tools)
scripts/              2 files  (Tier 6 - Scripts)
archive/              7 files  (Tier 8 - Deprecated)
root/                 3 files  (Tier 9 - Root)
---------------------------------
TOTAL PYTHON:       415 files

=== SQL FILES ===
sql/                  3 files  (Tier 7 - Migrations)
---------------------------------
TOTAL SQL:            3 files

=== MARKDOWN FILES ===
docs/current/         9 files
docs/compliance/      7 files  (including this audit)
docs/business/        9 files  (1 root + 8 investor/)
docs/operations/     12 files  (11 root + 1 experimental/)
docs/history/        23 files  (13 in 2025-12/ + 10 in 2025-11/)
docs/reference/       2 files  (1 root + 1 adr/)
docs/ root            3 files  (README, MIGRATION_STATUS, REAL_SYSTEM_STATUS)
root/                 2 files  (replit.md, CHANGELOG.md)
tools/                1 file   (README.md)
omnix_testing/        1 file   (README.md)
---------------------------------
TOTAL MARKDOWN:      69 files

=== GRAND TOTAL ===
Python:             415 files
SQL:                  3 files
Markdown:            69 files
---------------------------------
TOTAL PROJECT:      487 files
```
