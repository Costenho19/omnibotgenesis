# OMNIX V6.5.4d Technical Debt Registry

**Created:** December 11, 2025  
**Status:** Active - Deferred until 500-trade milestone  
**Priority:** Track record generation > Code refactoring

---

## Executive Summary

This document registers known technical debt in OMNIX V6.5.4d. All items are **intentionally deferred** to prioritize track record generation for investor presentations. Refactoring is planned for V7.0 after achieving the 500-trade milestone.

---

## 1. Architecture Debt

### 1.1 Hexagonal Ports Not Integrated (PARTIALLY RESOLVED)

**Status:** Partially resolved (Dec 12, 2025) - 3 of 8 ports integrated

| Issue | Description |
|-------|-------------|
| Ports Defined | 8 protocol interfaces in `src/omnix/ports/` |
| Adapters Exist | KrakenClient, DatabaseGateway, RedisCache, etc. |
| Problem | ~~Adapters don't implement ports~~ **3 adapters now implement ports** |
| Impact | Remaining 5 ports still use direct imports |

**Phase 3 Progress (Dec 12, 2025):**
| Port | Adapter | Status |
|------|---------|--------|
| TradingPort | KrakenAdapter | ✅ Integrated via container.py |
| MarketDataPort | KrakenAdapter | ✅ Integrated via container.py |
| AIInferencePort | GeminiAdapter | ✅ Integrated via container.py |
| DatabasePort | DatabaseGateway | ⬜ Deferred V7.0 |
| CachePort | RedisCache | ⬜ Deferred V7.0 |
| NotificationPort | TelegramUtils | ⬜ Deferred V7.0 |

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

### 1.4 Community Intelligence Interface Mismatch (RESOLVED)

**Status:** ✅ Resolved (Dec 13, 2025)

**Issue 1: Missing `connected` property in DatabaseGateway**

| Issue | Description |
|-------|-------------|
| Problem | All 5 community_intelligence modules checked `db.connected` |
| Root Cause | DatabaseGateway only had `is_connected()` method, no `connected` property |
| Impact | Modules reported "❌ Disconnected" despite database being healthy |

**Resolution:**
Added `@property connected` to `DatabaseGateway` that delegates to internal state:
```python
@property
def connected(self) -> bool:
    return self._connected and self._pool is not None
```

**Issue 2: Early-binding connection check at `__init__` time**

| Issue | Description |
|-------|-------------|
| Problem | Modules set `self.connected = self.db is not None and self.db.connected` once in `__init__` |
| Root Cause | If `db_manager` is None at bot startup, modules stay permanently "Disconnected" |
| Impact | On Railway where DB initializes after bot, modules never see the connection |

**Resolution:**
Changed from early-binding variable to lazy `@property` evaluation in all 5 modules:
```python
# BEFORE (early-binding - problem)
def __init__(self, database_service=None):
    self.db = database_service
    self.connected = self.db is not None and self.db.connected  # Set once!

# AFTER (lazy evaluation - fix)
def __init__(self, database_service=None):
    self.db = database_service

@property
def connected(self):
    """Lazy connection check - evaluates each time for late-binding db_manager."""
    return self.db is not None and self.db.connected
```

**Files affected:**
- `omnix_services/database_service/database_gateway.py` - Added `@property connected`
- `omnix_services/community_intelligence/feedback_manager.py` - Changed to `@property`
- `omnix_services/community_intelligence/reward_system.py` - Changed to `@property`
- `omnix_services/community_intelligence/signal_contribution.py` - Changed to `@property`
- `omnix_services/community_intelligence/community_dashboard.py` - Changed to `@property`
- `omnix_services/community_intelligence/community_analyzer.py` - Changed to `@property`

**Verification:** All 5 Community Intelligence modules now dynamically check connection status

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

## 3.5 Phase 4: Version Normalization (COMPLETE - Dec 13, 2025)

**Issue:** ~30+ files had hardcoded version strings instead of using centralized `VERSION_BANNER` from `omnix_config/settings.py`.

**Root Cause:** Organic growth without enforcement of single source of truth for version.

**Solution Implemented:**

| Action | Files Modified |
|--------|----------------|
| Updated VERSION to 6.5.4d | `omnix_config/settings.py` |
| Import VERSION_BANNER | `omnix_dashboard/streamlit_app.py` |
| Import VERSION_BANNER | `omnix_services/ai_service/video/analyzer.py` |
| Import VERSION_BANNER | `omnix_services/ai_service/video/integration.py` |
| Import VERSION_BANNER | `omnix_services/ai_service/providers/omnix_style_renderer.py` |
| Import VERSION_BANNER | `omnix_services/ai_service/providers/omnix_prompt_builder.py` |
| Created version checker | `scripts/verify_version_consistency.py` |

**Central Version Location:**
```python
# omnix_config/settings.py
VERSION = "6.5.4d"
VERSION_NAME = "INSTITUTIONAL+"
VERSION_BANNER = f"V{VERSION} {VERSION_NAME}"  # "V6.5.4d INSTITUTIONAL+"
```

**Usage Pattern:**
```python
from omnix_config import VERSION_BANNER
logger.info(f"OMNIX {VERSION_BANNER} started")
```

**Preserved Historical Comments:**
- Calibration comments in `trading_profiles.py` (V6.5.4b, V6.5.4c, V6.5.4d) remain as historical audit trail
- Docstrings in test files remain unchanged

**Prevention:**
- `scripts/verify_version_consistency.py` detects hardcoded versions in Python, JS, and HTML
- Run before major releases: `python scripts/verify_version_consistency.py`

**JavaScript Limitation:**
JavaScript cannot dynamically import Python constants. When updating VERSION:
1. Update `omnix_config/settings.py` (central source)
2. Manually update console.log statements in:
   - `omnix_dashboard/static/js/pages/terminal.js`
   - `omnix_dashboard/static/js/pages/dashboard.js`
3. Run `python scripts/verify_version_consistency.py` to verify

**Status:** ✅ COMPLETE

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

## 5. Legacy & Dormant Packages

Based on the comprehensive Functional Domain Map audit (December 12, 2025), the following packages have been identified as LEGACY, DORMANT, or requiring evaluation:

### 5.1 Confirmed DORMANT (No Active Imports)

| Package | Location | Reason | Recommendation | Phase |
|---------|----------|--------|----------------|-------|
| **alerts** | `omnix_services/alerts/` | `notifications/` service is used instead; no active imports in trading pipeline | Consolidate functionality into `notifications/` or deprecate | V7.0 Phase 4 |
| **on_chain_service** | `omnix_services/on_chain_service/` | No active imports in codebase; APIs (Arkham, Clank) not integrated | Activate with feature flag when APIs available | V7.0 Phase 3 |

### 5.1b ACTIVE but Candidate for Consolidation

| Package | Location | Reason | Recommendation | Phase |
|---------|----------|--------|----------------|-------|
| **concurrency** | `omnix_services/concurrency/` | Actively imported by `main.py` (IntelligentCacheSystem, OptimizedConcurrencyManager) | Evaluate consolidation with Redis cache system | V7.0 Phase 2 |

### 5.2 Confirmed LEGACY (Superseded by Newer Code)

| Package | Location | Superseded By | Recommendation | Phase |
|---------|----------|---------------|----------------|-------|
| **regime_switcher** | `omnix_strategies/regime_switcher.py` | `adaptive_engine/` provides dynamic regime adaptation | Archive and deprecate | V7.0 Phase 4 |

### 5.3 PARTIAL Integration (Requires Evaluation)

| Package | Location | Current Usage | Recommendation | Phase |
|---------|----------|---------------|----------------|-------|
| **community_intelligence** | `omnix_services/community_intelligence/` | Only imported by Telegram commands in `enterprise_bot.py`; not integrated into trading pipeline; database tables may be empty | Evaluate: (1) Integrate into trading signals, or (2) Archive as B2C feature for future SaaS | V7.0 Phase 2+ |
| **derivatives** | `omnix_services/derivatives/` | Conditional import in `main.py`; not in main execution loop | Keep as STRATEGIC capability; add feature flag before production activation | V7.0 Phase 3 |

### 5.4 Previously Undocumented (Now Documented)

| Package | Purpose | Status |
|---------|---------|--------|
| `omnix_reports/` | Pitch deck PDF generation | Now documented in Functional Domain Map |
| `omnix_api/` | Stripe integration (B2C prep) | Documented as STRATEGIC - future use |
| `omnix_risk/` | Additional risk utilities | Now documented in Domain 4: Risk & Protection |

### 5.5 Deprecation Checklist

Before deprecating any package:

1. **Verify no imports:**
   ```bash
   grep -r "from omnix_services.alerts" . --include="*.py"
   grep -r "from omnix_services.concurrency" . --include="*.py"
   grep -r "from omnix_strategies" . --include="*.py"
   ```

2. **Check database tables:** Ensure no active data would be orphaned

3. **Review Railway logs:** Confirm no runtime calls

4. **Create deprecation ADR:** Document decision in `docs/transformation/adr/`

5. **Move to archive:** Relocate to `docs/history/deprecated/` before deletion

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
*Last reviewed: December 12, 2025*
