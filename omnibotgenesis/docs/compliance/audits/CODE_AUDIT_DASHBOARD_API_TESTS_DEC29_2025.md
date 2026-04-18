# CODE AUDIT: Dashboard, API, Tests & Scripts (61 files)
## OMNIX — Phase 2D
**Date**: December 29, 2025  
**Auditor**: AI Assistant (Senior FullStack Developer Review)  
**Scope**: Web interfaces, payments, tests, scripts, root files

---

## Complete File Inventory

| # | Directory | Files | Purpose |
|---|-----------|-------|---------|
| 1 | omnix_dashboard/ | 18 | Flask dashboard app |
| 2 | tests/ | 34 | Pytest test suite |
| 3 | omnix_api/ | 4 | Payment integrations |
| 4 | Root files | 3 | Entry points |
| 5 | scripts/ | 2 | Migration, traceability |
| **TOTAL** | | **61** | |

**Plus SQL Files**: 4 files (migrations, indexes, risk tables)

---

## Executive Summary

| Component | Status | Assessment |
|-----------|--------|------------|
| Dashboard | HEALTHY | Flask Blueprints, CORS, pooling |
| Tests | COMPREHENSIVE | 34 tests, contracts, integration |
| API/Payments | LEGACY WARNING | V5.1, unconfigured Price IDs |
| Scripts | ACTIVE | Migration, traceability |

---

## COMPONENT 1: OMNIX_DASHBOARD (18 files)

**Location**: `omnix_dashboard/`

**Structure**:
```
omnix_dashboard/
├── app.py                 # Flask app factory
├── run.py                 # Development runner
├── streamlit_app.py       # Streamlit dashboard
├── gunicorn.conf.py       # Production WSGI config
├── api_client.py          # API client utilities
├── blueprints/
│   ├── __init__.py        # Blueprint exports
│   ├── views.py           # View routes
│   ├── core.py            # Core API endpoints
│   ├── market.py          # Market data endpoints
│   ├── intelligence.py    # Intelligence endpoints
│   ├── system.py          # System status endpoints
│   └── snapshots.py       # Snapshot endpoints
└── utils/
    ├── __init__.py
    ├── database.py        # DB connection pooling
    ├── decorators.py      # Route decorators
    ├── external_apis.py   # External API clients
    └── queries.py         # SQL queries
```

**Architecture Assessment**:
| Pattern | Implementation | Score |
|---------|----------------|-------|
| Application Factory | `create_app()` | ★★★★★ |
| Blueprint Modularization | 6 blueprints | ★★★★★ |
| Connection Pooling | psycopg_pool | ★★★★★ |
| CORS Security | Railway + Replit | ★★★★☆ |
| Environment Detection | IS_RAILWAY | ★★★★★ |
| Graceful Shutdown | atexit.register() | ★★★★★ |

**Blueprints** (6):
| Blueprint | Prefix | Purpose |
|-----------|--------|---------|
| views_bp | / | HTML views |
| core_bp | /api | Core API |
| market_bp | /api/market | Market data |
| intelligence_bp | /api/intel | Intelligence data |
| system_bp | /api/system | System status |
| snapshots_bp | /api/snapshots | State snapshots |

**Security Features**:
| Feature | Status | Evidence |
|---------|--------|----------|
| SESSION_SECRET | REQUIRED (Railway) | Line 30-36 |
| DASHBOARD_API_KEY | OPTIONAL (warning) | Line 50-52 |
| CORS Origins | Configurable | Line 38-48 |
| Production Check | IS_RAILWAY | Line 23 |

**Database Connection**:
- Uses `get_database_url()` with 3-tier fallback
- Connection pooling via `psycopg_pool`
- Graceful shutdown via `shutdown_pool()`

---

## COMPONENT 2: TESTS (34 files)

**Location**: `tests/`

**Test Categories**:

### Contract Tests (4 files)
| Test | Scope | Lines |
|------|-------|-------|
| test_cache_port_contract.py | CachePort interface | 9,513 |
| test_database_port_contract.py | DatabasePort interface | 14,046 |
| test_notification_port_contract.py | NotificationPort interface | 11,060 |
| test_telegram_port_contract.py | TelegramPort interface | 25,283 |

### Integration Tests (2 files)
| Test | Purpose |
|------|---------|
| test_migration_win_rate.py | Win rate calculation verification |
| test_railway_startup.py | Railway deployment startup test |

### Application Tests (2 files)
| Test | Purpose |
|------|---------|
| test_ai_first_command_detection.py | AI command detection |
| test_multiuser_support.py | Multi-user isolation |

### Port Tests (9 files)
| Test | Port Tested |
|------|-------------|
| test_derivatives_port.py | DerivativesPort |
| test_execution_port.py | ExecutionPort |
| test_market_intel_port.py | MarketIntelPort |
| test_onchain_port.py | OnChainDataPort |
| test_optimization_port.py | OptimizationPort |
| test_portfolio_port.py | PortfolioPort |
| test_risk_control_port.py | RiskControlPort |
| test_cache_adapter_validation.py | CacheAdapter |
| test_parity_harness.py | Legacy parity |

### Core Tests (17 files)
| Test | Purpose |
|------|---------|
| test_authorization.py | Authorization system |
| test_code_verification.py | Code verification |
| test_domain_entities.py | Domain entity tests |
| test_institutional_language.py | AI language enforcement |
| test_integration_phase2.py | Phase 2 integration |
| test_intent_detection.py | Intent detection |
| test_multi_user_isolation.py | User isolation |
| test_phase1_bootstrap.py | Bootstrap tests |
| test_phase3b_integration.py | Phase 3b integration |
| test_pqc_security.py | Post-quantum crypto |
| test_price_stale_detection.py | Price stale detection |
| test_smoke.py | Smoke tests |
| test_v7_services_integration.py | V7 services |
| test_version_consistency.py | Version consistency |
| conftest.py | Pytest fixtures |

**Test Fixtures** (conftest.py):
| Fixture | Purpose |
|---------|---------|
| mock_env | Mock environment variables |
| sample_trade_data | Sample trade data |
| sample_market_data | Sample market data |

**Test Coverage Assessment**:
| Area | Coverage | Status |
|------|----------|--------|
| Contract Tests | 4 ports | GOOD |
| Port Tests | 9 ports | EXCELLENT |
| Integration | 2 tests | ADEQUATE |
| Domain | 1 test | NEEDS MORE |

---

## COMPONENT 3: OMNIX_API (4 files)

**Location**: `omnix_api/`

**Structure**:
```
omnix_api/
├── __init__.py
├── payments/
│   ├── __init__.py
│   └── stripe_integration.py
└── routes/
    └── __init__.py
```

### Stripe Integration Analysis

**File**: `omnix_api/payments/stripe_integration.py`

**Version**: V5.1 (LEGACY - needs update)

**Features**:
| Feature | Implementation | Status |
|---------|----------------|--------|
| Checkout Session | stripe.checkout.Session.create() | IMPLEMENTED |
| Payment Verification | verify_payment() | IMPLEMENTED |
| Subscription Cancellation | cancel_subscription() | IMPLEMENTED |
| Customer Subscriptions | get_customer_subscriptions() | IMPLEMENTED |
| Webhook Handler | /webhook endpoint | PARTIAL (no signature verification) |

**Critical Issues**:
| ID | Issue | Severity | Line |
|----|-------|----------|------|
| C1 | Price IDs unconfigured ('price_XXXXX') | HIGH | 37-42 |
| C2 | Webhook signature not verified | HIGH | 205-216 |
| C3 | Embedded HTML in responses | MEDIUM | 164-203 |

**LSP Diagnostics**: 1 warning in stripe_integration.py

**Pricing Configuration Required**:
```python
PRICES = {
    'pro_monthly': 'price_XXXXX',       # TODO: Configure
    'enterprise_monthly': 'price_XXXXX', # TODO: Configure
    'pro_yearly': 'price_XXXXX',         # TODO: Configure
    'enterprise_yearly': 'price_XXXXX',  # TODO: Configure
}
```

**Recommendation**: 
1. Create Price IDs in Stripe Dashboard
2. Add webhook signature verification
3. Move HTML templates to Jinja2 files

---

## COMPONENT 4: ROOT FILES (3 files)

**Location**: Project root

| File | Purpose | Status |
|------|---------|--------|
| main.py | Main entry point | ACTIVE |
| start_dashboard.py | Dashboard launcher | ACTIVE |
| wsgi.py | WSGI entry point | ACTIVE |

---

## COMPONENT 5: SCRIPTS (2 files)

**Location**: `scripts/`

| File | Purpose |
|------|---------|
| migration/activate_cache_port.py | Cache port activation |
| traceability/validate_traceability.py | Traceability validation |

---

## COMPONENT 6: SQL FILES (4 files)

| File | Purpose |
|------|---------|
| omnix_services/database_service/optimize_indexes.sql | Index optimization |
| sql/migrations/V7_001_fix_schema_discrepancies.sql | V7 schema fixes |
| sql/optimization_tables.sql | Optimization tables |
| sql/risk_guardian_table.sql | Risk guardian table |

---

## Issues Summary

### Critical Issues

| ID | Component | Issue | Recommendation |
|----|-----------|-------|----------------|
| C1 | omnix_api | Stripe Price IDs unconfigured | Create in Stripe Dashboard |
| C2 | omnix_api | Webhook signature not verified | Add STRIPE_WEBHOOK_SECRET |

### Medium Priority Issues

| ID | Component | Issue | Recommendation |
|----|-----------|-------|----------------|
| M1 | omnix_api | Embedded HTML in Stripe routes | Move to Jinja2 templates |
| M2 | omnix_api | Version V5.1 outdated | Update to V6.5.4d |
| M3 | tests | Domain entity coverage low | Add more entity tests |

### Low Priority / Technical Debt

| ID | Component | Issue | Recommendation |
|----|-----------|-------|----------------|
| L1 | omnix_dashboard | 1 Streamlit app alongside Flask | Consider consolidation |
| L2 | scripts | Only 2 migration scripts | Document migration process |

---

## Security Assessment

| Component | Status | Evidence |
|-----------|--------|----------|
| Dashboard CORS | SECURE | Whitelist origins |
| Dashboard Session | SECURE | SESSION_SECRET required |
| Stripe API | SECURE | API key from env |
| Stripe Webhook | INSECURE | No signature verification |
| Database | SECURE | Connection pooling |

---

## Test Coverage Summary

| Category | Count | Coverage |
|----------|-------|----------|
| Contract Tests | 4 | Ports interface validation |
| Integration Tests | 2 | Deployment, migration |
| Application Tests | 2 | AI commands, multi-user |
| Port Tests | 9 | Port implementations |
| Core Tests | 17 | Various system tests |
| **TOTAL** | **34** | |

---

## Recommendations

### Immediate (Critical)
1. Configure Stripe Price IDs in production
2. Add webhook signature verification

### Short-term
1. Update stripe_integration.py to V6.5.4d
2. Move HTML templates to Jinja2
3. Add more domain entity tests

### Long-term
1. Consider Streamlit/Flask consolidation
2. Add E2E tests for payment flow
3. Document migration script usage

---

**Audit Completed**: December 29, 2025  
**Next Review**: After Phase 3A (Documentation Audit)  
**Approved By**: Pending Architect Review
