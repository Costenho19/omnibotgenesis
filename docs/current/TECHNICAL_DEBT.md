# OMNIX V6.5.4d Technical Debt Registry

**Created:** December 11, 2025  
**Status:** Active - Deferred until 500-trade milestone  
**Priority:** Track record generation > Code refactoring

---

## Executive Summary

This document registers known technical debt in OMNIX V6.5.4d. All items are **intentionally deferred** to prioritize track record generation for investor presentations. Refactoring is planned for V7.0 after achieving the 500-trade milestone.

---

## 1. Architecture Debt

### 1.1 Hexagonal Ports Not Integrated (CRITICAL)

**Status:** Deferred to V7.0

| Issue | Description |
|-------|-------------|
| Ports Defined | 8 protocol interfaces in `omnix/ports/` |
| Adapters Exist | KrakenClient, DatabaseGateway, RedisCache, etc. |
| Problem | Adapters don't implement ports; services import directly |
| Impact | No dependency inversion, testing requires full infrastructure |

**Current State:**
```python
# ACTUAL (direct import)
from omnix_services.database_service import database_gateway
result = database_gateway.execute(query)

# TARGET V7.0 (port injection)
def __init__(self, db: DatabasePort):
    self.db = db
```

**Resolution Plan:** V7.0 Strangler Fig migration per `MIGRATION_ROADMAP.md`

### 1.2 main.py Monolithic Bootstrap (HIGH)

**Status:** Deferred to V7.0

| Responsibility | Should Be |
|----------------|-----------|
| Redis cache cleanup | Infrastructure layer |
| Database migrations | Bootstrap/migrations |
| Bot initialization | Interface layer |
| Flask app creation | Interface layer |
| Trading loop | Application layer |

**Impact:** Single Responsibility Principle violated, testing difficult

**Resolution Plan:** Extract to `src/omnix/bootstrap/` with DI container

### 1.3 Cross-Package Coupling (HIGH)

**Status:** Deferred to V7.0

Dashboard blueprints import service singletons directly:
```python
# omnix_dashboard/blueprints/core.py
from omnix_services.database_service import database_gateway  # Direct coupling
```

**Resolution Plan:** Inject dependencies through Flask extensions

---

## 2. Code Quality Debt

### 2.1 Bare Except Clauses (MEDIUM)

**Count:** ~80 instances  
**Risk:** Silent failures, debugging difficulty

**Example:**
```python
# Current
try:
    result = risky_operation()
except:  # Bare except
    pass

# Target
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
```

**Files with highest density:**
- `main.py`
- `omnix_services/trading_service/` modules
- `omnix_dashboard/blueprints/`

### 2.2 Silenced Exceptions (HIGH)

**Count:** ~55 instances  
**Pattern:** `except: pass` or `except Exception: pass`

**Risk:** Critical errors may go unnoticed in production

**Resolution Plan:** Add structured logging for all exception handlers

### 2.3 TODO/FIXME Comments (LOW)

**Count:** 26 unresolved  
**Status:** Documented but not critical for track record

### 2.4 Large Files (MEDIUM)

| File | Lines | Recommendation |
|------|-------|----------------|
| `enterprise_bot.py` | 7,812 | Split into command handlers |
| `trading_system.py` | 5,576 | Extract execution logic |
| `database_service.py` | 4,912 | Split by domain |
| `auto_trading_bot.py` | 4,564 | Extract strategies |
| `physics_validator.py` | 4,459 | Modularize formulas |

---

## 3. Documentation Debt

### 3.1 Module Location Inconsistencies (RESOLVED)

**Status:** Fixed December 11, 2025

Previously documented paths did not match actual code locations. Updated in:
- `docs/core/ARCHITECTURE_REFERENCE.md`
- `docs/core/INDEX.md`

### 3.2 Version References (RESOLVED)

**Status:** Updated to V6.5.4d December 11, 2025

---

## 4. Testing Debt

### 4.1 Test Coverage (CRITICAL - Deferred)

**Current Coverage:** <1%  
**Target Coverage:** 60%+ for core trading logic

| Area | Current Tests | Target |
|------|---------------|--------|
| Domain/Strategies | 0 | 80% |
| Trading Execution | 0 | 70% |
| Risk Calculations | 0 | 90% |
| AI Service | 2 | 60% |
| Integration | 0 | 50% |

**Resolution Plan:** Add tests after 500-trade milestone using pytest + mocks

### 4.2 No Integration Tests

**Impact:** Changes may break production without detection

**Mitigation:** Manual testing + Railway deployment monitoring

---

## 5. Undocumented Packages

The following packages exist but were not in original documentation:

| Package | Purpose | Status |
|---------|---------|--------|
| `omnix_reports/` | Pitch deck PDF generation | Now documented |
| `omnix_strategies/` | Regime switcher (legacy) | Consider deprecation |
| `omnix_api/` | Stripe integration (B2C prep) | Future use |

---

## 6. Deferred Refactoring Items

### Priority Matrix

```
IMPACT ↑
         │  ┌─────────────────┐   ┌─────────────────┐
   HIGH  │  │ Ports           │   │ main.py         │
         │  │ Integration     │   │ Bootstrap       │
         │  └─────────────────┘   └─────────────────┘
         │  ┌─────────────────┐   ┌─────────────────┐
 MEDIUM  │  │ Bare excepts    │   │ enterprise_bot  │
         │  │ Add logging     │   │ Split file      │
         │  └─────────────────┘   └─────────────────┘
         │  ┌─────────────────┐   ┌─────────────────┐
   LOW   │  │ TODO comments   │   │ Type hints      │
         │  │ Cleanup         │   │ Add coverage    │
         │  └─────────────────┘   └─────────────────┘
         └────────────────────────────────────────────→ EFFORT
                 LOW              MEDIUM           HIGH
```

### Recommended Order (Post-500 Trades)

1. **Quick Wins** (1-2 days)
   - Add logging to silenced exceptions
   - Clean up bare except clauses
   - Resolve critical TODOs

2. **Bootstrap Refactor** (3-5 days)
   - Extract main.py to bootstrap module
   - Create DI container
   - Enable unit testing

3. **Hexagonal Integration** (1-2 weeks)
   - Connect ports to adapters
   - Inject dependencies
   - Add integration tests

4. **File Splitting** (1 week)
   - enterprise_bot.py → command modules
   - auto_trading_bot.py → strategy modules

---

## 7. Why Defer?

**Business Priority:** Generate 500+ verifiable trades for $1M seed funding at $11.5M pre-money valuation.

| Risk | Mitigation |
|------|------------|
| Production instability | Railway monitoring, manual testing |
| Silent failures | Daily log review, Telegram alerts |
| Code complexity | Documentation, institutional knowledge |

**Decision:** Technical debt is acceptable during track record generation. Full refactoring starts with V7.0 after investor milestone.

---

*Document maintained by: OMNIX Development Team*  
*Last reviewed: December 11, 2025*
