# OMNIX V6.5.4d Module Catalog

**Version:** 6.5.4d INSTITUTIONAL+  
**Generated:** December 11, 2025  
**Phase:** 0.5 Foundation

---

## Overview

This catalog documents all modules in OMNIX V6.5.4d with their purpose, dependencies, and migration status.

---

## 1. Core Packages

### 1.1 omnix/ (Hexagonal Ports)

**Purpose:** Protocol interfaces for hexagonal architecture  
**Migration Status:** Defined, not integrated  
**Files:** 10

| Module | Purpose | Protocol Count |
|--------|---------|----------------|
| `ports/driven/ai_inference_port.py` | AI model interface | 1 |
| `ports/driven/cache_port.py` | Cache interface | 1 |
| `ports/driven/database_port.py` | Database interface | 3 |
| `ports/driven/market_data_port.py` | Market data interface | 2 |
| `ports/driven/notification_port.py` | Notification interface | 1 |
| `ports/driven/trading_port.py` | Trading interface | 1 |
| `ports/driver/rest_api_port.py` | REST API interface | 1 |
| `ports/driver/telegram_port.py` | Telegram interface | 1 |

**Migration Action:** Create adapters that implement these protocols in Phase 2.

---

### 1.2 omnix_config/

**Purpose:** Environment and configuration management  
**Migration Status:** Migrate to `src/omnix/config/`  
**Files:** 5

| Module | Purpose | Imports From |
|--------|---------|--------------|
| `settings.py` | Environment variables | - |
| `env_manager.py` | Environment config | - |
| `__init__.py` | VERSION_BANNER | - |

**Migration Action:** Consolidate into Pydantic Settings in Phase 1.

---

### 1.3 omnix_core/

**Purpose:** Bot, cache, strategies, sessions  
**Migration Status:** Split to domain/infrastructure  
**Files:** 30

| Subpackage | Purpose | Key Modules | Target Layer |
|------------|---------|-------------|--------------|
| `bot/` | Trading bot logic | `auto_trading_bot.py` (4,564 lines) | Application |
| `cache/` | Redis caching | `redis_cache.py`, `redis_state.py` | Infrastructure |
| `config/` | Trading profiles | `trading_profiles.py` | Config |
| `context/` | Real data provider | `real_data_provider.py` | Infrastructure |
| `quantum/` | Physics validation | `physics_validator.py` (4,459 lines) | Domain |
| `risk/` | Rollback protocol | `rollback_protocol.py` | Domain |
| `security/` | Post-quantum crypto | `pqc_security.py` | Infrastructure |
| `sessions/` | User sessions | `user_session_manager.py` | Application |
| `strategies/` | ARES, CAES, Non-Markovian | Multiple | Domain |
| `utils/` | Logger, rate limiter | `logger.py`, `rate_limiter.py` | Infrastructure |

**Migration Priority:** High (widely imported)

---

### 1.4 omnix_services/

**Purpose:** 24 service subpackages  
**Migration Status:** Split to application/infrastructure  
**Files:** 90+

| Subpackage | Purpose | Lines | Target Layer |
|------------|---------|-------|--------------|
| `ai_service/` | AI integration (SOLID model) | ~2,500 | Application |
| `coherence_service/` | 6-Tier Veto System | ~1,500 | Domain |
| `database_service/` | PostgreSQL gateway | ~4,900 | Infrastructure |
| `execution_service/` | Trade execution | ~2,000 | Application |
| `monitoring/` | Risk Guardian | ~1,800 | Domain |
| `telegram_service/` | Bot commands | ~7,812 | Interface |
| `trading_service/` | Kraken client | ~3,500 | Infrastructure |
| `risk_management/` | Risk models | ~2,000 | Domain |
| `adaptive_engine/` | Parameter calibration | ~1,200 | Application |
| `on_chain_service/` | Blockchain analytics | ~1,800 | Infrastructure |
| `web_search_service/` | Tavily search | ~600 | Infrastructure |
| `analytics/` | Metrics, charts | ~1,500 | Application |
| `market_data/` | Price feeds | ~1,200 | Infrastructure |
| `market_intelligence/` | Finnhub, Alpha Vantage | ~1,000 | Infrastructure |
| `notifications/` | Trade alerts | ~800 | Infrastructure |

**Reference Model:** `ai_service/` already implements SOLID+DI correctly.

---

### 1.5 omnix_dashboard/

**Purpose:** Flask + Streamlit dashboards  
**Migration Status:** Move to `src/omnix/interfaces/`  
**Files:** 25

| Module | Purpose | Port |
|--------|---------|------|
| `app.py` | Flask factory | 5000 |
| `streamlit_app.py` | Investor dashboard | 8080 |
| `blueprints/` | REST API routes | - |
| `utils/` | Database helpers | - |

**Migration Action:** Flask app factory pattern in Phase 3.

---

### 1.6 omnix_risk/

**Purpose:** Portfolio summary, cascade protection  
**Migration Status:** Consolidate with `omnix_services/risk_management/`  
**Files:** 5

**Migration Action:** Merge into `src/omnix/domain/risk/` in Phase 2.

---

### 1.7 omnix_testing/

**Purpose:** Backtesting framework  
**Migration Status:** Keep as separate package  
**Files:** 15

| Module | Purpose |
|--------|---------|
| `backtesting/backtesting_engine.py` | Trade simulation |
| `professional_validator.py` | Strategy validation |
| `institutional_stress_suite.py` | Stress testing |

**Migration Action:** Low priority, keep for now.

---

### 1.8 omnix_reports/

**Purpose:** PDF pitch deck generation  
**Migration Status:** Move to `src/omnix/application/reports/`  
**Files:** 8

**Migration Action:** Phase 4 cleanup.

---

### 1.9 omnix_strategies/

**Purpose:** Legacy regime switcher  
**Migration Status:** Consider deprecation  
**Files:** 4

**Migration Action:** Evaluate if still used, may deprecate.

---

### 1.10 omnix_api/

**Purpose:** Stripe B2C integration  
**Migration Status:** Future use (B2C launch)  
**Files:** 6

**Migration Action:** Phase 4 or post-migration.

---

## 2. Key Files (>4,000 lines)

| File | Lines | Issue | Action |
|------|-------|-------|--------|
| `enterprise_bot.py` | 7,812 | Monolithic | Split to command handlers |
| `trading_system.py` | 5,576 | Mixed concerns | Extract execution logic |
| `database_service.py` | 4,912 | Large | Split by domain |
| `auto_trading_bot.py` | 4,564 | Strategies embedded | Extract to domain |
| `physics_validator.py` | 4,459 | Complex math | Modularize formulas |

---

## 3. Migration Layer Mapping

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TARGET ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  src/omnix/                                                              │
│  │                                                                       │
│  ├── domain/                     ← omnix_core/strategies/                │
│  │   ├── trading/                  omnix_core/risk/                      │
│  │   ├── risk/                     omnix_services/coherence_service/     │
│  │   └── strategies/               omnix_services/monitoring/ (domain)   │
│  │                                                                       │
│  ├── application/                ← omnix_core/bot/                       │
│  │   ├── trading/                  omnix_services/execution_service/     │
│  │   ├── analysis/                 omnix_services/ai_service/            │
│  │   └── reports/                  omnix_reports/                        │
│  │                                                                       │
│  ├── infrastructure/             ← omnix_core/cache/                     │
│  │   ├── persistence/              omnix_services/database_service/      │
│  │   ├── external/                 omnix_services/trading_service/       │
│  │   └── notifications/            omnix_services/market_data/           │
│  │                                                                       │
│  ├── interfaces/                 ← omnix_dashboard/                      │
│  │   ├── flask_app/                omnix_services/telegram_service/      │
│  │   └── telegram/                                                       │
│  │                                                                       │
│  ├── config/                     ← omnix_config/                         │
│  │   └── settings.py               omnix_core/config/                    │
│  │                                                                       │
│  └── bootstrap/                  ← main.py                               │
│      └── container.py                                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Root Files (Cleanup in Phase 4)

**Purpose:** Scripts, entrypoints, and utilities in project root  
**Migration Status:** Reorganize in Phase 4 (Cleanup)  
**Files:** 9

| File | Purpose | Target Location | Priority |
|------|---------|-----------------|----------|
| `main.py` | Bot entrypoint | `src/omnix/bootstrap/main.py` | P0 |
| `wsgi.py` | Production WSGI entry | `src/omnix/bootstrap/wsgi.py` | P0 |
| `start_dashboard.py` | Dashboard launcher | `scripts/start_dashboard.py` or DELETE if redundant | P1 |
| `chat_with_bot.py` | Testing utility | `scripts/chat_with_bot.py` | P2 |
| `generate_investor_report.py` | Investor reports | `scripts/generate_investor_report.py` | P1 |
| `send_telegram_message.py` | Telegram utility | `scripts/send_telegram_message.py` | P2 |
| `get_my_telegram_id.py` | Telegram ID helper | `scripts/get_my_telegram_id.py` | P2 |
| `test_railway_startup.py` | Deployment test | `tests/integration/test_railway_startup.py` | P1 |
| `verify_code.py` | Code verification | `scripts/verify_code.py` or `tests/` | P2 |

**Migration Action:** 
- Phase 4.1: Move `main.py` and `wsgi.py` to bootstrap
- Phase 4.2: Create `scripts/` directory and move utilities
- Phase 4.3: Move tests to `tests/integration/`
- Phase 4.4: Update Procfile and railway.json paths
- Phase 4.5: Evaluate `start_dashboard.py` redundancy

---

## 5. Dependency Injection Status

| Component | Current | Target |
|-----------|---------|--------|
| AI Service | DI Container | Keep (reference model) |
| Database | Singleton | Inject via port |
| Redis Cache | Singleton | Inject via port |
| Kraken Client | Direct import | Inject via port |
| Telegram Bot | Direct import | Inject via port |
| Risk Guardian | Direct import | Inject via port |

---

## 6. Type Coverage

| Package | Estimated Coverage | Target |
|---------|-------------------|--------|
| `omnix_core/` | ~15% | 60% |
| `omnix_services/ai_service/` | ~60% | 80% |
| `omnix_services/` (other) | ~10% | 60% |
| `omnix_dashboard/` | ~5% | 40% |

---

*Document maintained as part of Phase 0 Foundation*  
*Last updated: December 12, 2025*
