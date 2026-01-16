# OMNIX V6.5.4e Technical Debt Registry

**Created:** December 11, 2025  
**Updated:** January 16, 2026  
**Status:** Active - Deferred until 500-trade milestone  
**Priority:** Track record generation > Code refactoring

---

## ADR-009 Conversational Tone Update (Jan 16, 2026)

**Status:** ✅ COMPLETED

**Problema:** Respuestas del bot eran demasiado cortantes y frías. Límites de 30-50 palabras no permitían interacción amena.

**Cambios Implementados:**

| Tipo | Antes | Después | Razón |
|------|-------|---------|-------|
| Simple yes/no | 30 | 80 | Espacio para respuesta amigable |
| Operacional | 50 | 120 | Conversación natural |
| Técnico | 100 | 180 | Explicaciones con personalidad |
| Métricas | 150 | 200 | Contexto honesto completo |
| Due Diligence | 300 | 350 | Respuestas completas para inversores |
| AudienceContext default | 100 | 150 | Nuevo baseline conversacional |

**Archivos Modificados:**
- `docs/reference/adr/ADR-009-brevity-first-policy.md` - Nuevos límites documentados
- `omnix_services/ai_service/investor_responses.py` - `get_response_word_limit()` y `AudienceContext`
- `omnix_services/ai_service/ai_prompts.py` - `MASTER_SYSTEM_PROMPT` con tono ameno

**Principio Mantenido:** Respuesta directa primero, sin "Caballero Harold", sin rollos filosóficos.

---

## AI Brevity Detection Fix (Jan 16, 2026)

**Status:** ✅ COMPLETED

**Problema:** Bot truncaba respuestas cuando usuario pedía listas o enumeraciones (ej: "dime 10 cosas", "cuales son las capas", "enumeralas todas"). Mostraba "[Más detalles disponibles]" en lugar de dar la lista completa.

**Causa Raíz:** ADR-009 Brevity Policy solo detectaba frases como "explícame" pero no peticiones de listas/enumeraciones.

**Fix:** Expandir `explanation_indicators` en `get_response_word_limit()`:
- Agregado: enumera, enumeralas, cuales son, cuantas son, dime todas, lista todas, etc.
- Agregado: regex para detectar "dime N cosas", "give me N reasons" (peticiones numéricas)

**Archivo:** `omnix_services/ai_service/investor_responses.py` (líneas 145-175)

---

## Railway Production Hotfixes (Jan 16, 2026)

**Status:** ✅ COMPLETED

**Problema:** 3 errores en Railway production logs impidiendo operación correcta del bot.

### Fix 1: CacheAdapter.increment() Missing

**Error:** `'CacheAdapter' object has no attribute 'increment'`

**Causa Raíz:** V7.0 hexagonal `CacheAdapter` (activado con `USE_CACHE_PORT=true`) no implementaba método `increment()` requerido por `RateLimiter`. Legacy `RedisCache` sí lo tiene.

**Fix:** Agregar métodos `increment()` y `get_ttl()` a CacheAdapter que delegan a RedisCache.

**Archivo:** `src/omnix/infrastructure/adapters/cache_adapter.py`

### Fix 2: KrakenAPIClient.client.fetch_ticker() Missing

**Error:** `'KrakenAPIClient' object has no attribute 'client'`

**Causa Raíz:** `real_data_provider.py` llamaba `.client.fetch_ticker('BTC/USD')` asumiendo interfaz CCXT, pero `KrakenAPIClient` es implementación custom con `requests`.

**Fix:** Modificar `real_data_provider.py` para usar `kraken_client.get_ticker('XBTUSD')` directamente con parsing de formato Kraken nativo:
- `'c'[0]` = last price
- `'h'[1]` = 24h high
- `'l'[1]` = 24h low
- `'v'[1]` = 24h volume

**Archivo:** `omnix_core/context/real_data_provider.py` (líneas 114-131)

### Fix 3: PostgreSQL GROUP BY Alias Error

**Error:** `column "coherence_level" does not exist`

**Causa Raíz:** Query SQL usaba `GROUP BY coherence_level` pero `coherence_level` es un alias CASE, no columna. PostgreSQL no permite alias en GROUP BY.

**Fix:** Cambiar `GROUP BY coherence_level` → `GROUP BY 1` (referencia por posición). También corregido ORDER BY para usar CASE numérico.

**Archivo:** `omnix_core/context/real_data_provider.py` (líneas 354-363)

---

## Telegram Voice Service Fix (Dec 31, 2025)

**Status:** ✅ COMPLETED

**Problema:** `UnboundLocalError: cannot access local variable 'asyncio'` al generar respuestas de voz.

**Causa Raíz:** Python interpreta `import asyncio` dentro de bloques condicionales como declaración de variable local para todo el scope de la función. Cuando el bloque no se ejecuta, la "variable local" no existe y falla al usar `asyncio.to_thread()`.

**Fix Implementado:**

| Línea | Contexto | Acción |
|-------|----------|--------|
| 3545 | `if i < total_parts - 1:` | Eliminado `import asyncio` redundante |
| 4835 | `if hasattr(self.ai, 'generate_response'):` | Eliminado `import asyncio` redundante |
| 6489 | Antes de `await arbitrage` | Eliminado `import asyncio` redundante |

**Regla:** Solo un `import asyncio` global (línea 10) - nunca imports condicionales.

**Archivos Modificados:**
- `omnix_services/telegram_service/enterprise_bot.py` - 3 imports eliminados

**Commit:** `6f77f8d`

---

## Type Safety Hotfix - SCOPE EXPANDIDO (Dec 30, 2025)

**Status:** ✅ COMPLETED (Fase 1: Coherence Engine) | ✅ COMPLETED (Fase 2: AutoTradingBot)

### Fase 1: Coherence Engine (completada anteriormente)

**Problema:** TypeError `'>=' not supported between instances of 'str' and 'int'` en Coherence Gate cuando `StrategySignal.signal` llegaba como string en lugar de Enum.

**Fixes Implementados:**

| Issue | Fix | Test |
|-------|-----|------|
| Signal como string | `normalize_signal()` convierte "BUY"/"SELL" a Enum Signal | `test_normalize_string_buy` |
| StrategySignal con tipos mixtos | `normalize_strategy_signal()` normaliza signal, confidence, strength | `test_normalize_with_string_signal` |
| Comparaciones >= sin blindaje | `safe_float()` en _classify_coherence_level, get_coherence_emoji | `test_classify_coherence_level_with_string_score` |
| safe_float no removía '%' | Ahora strip().replace('%', '') antes de parsear | `test_safe_float_removes_percent` |

**Tests:** 16/16 pasando en `tests/test_coherence_type_safety.py`

### Fase 2: AutoTradingBot _build_strategy_signals (Dec 30, 2025)

**Root Cause:** El error persistía porque `_build_strategy_signals()` extraía valores de diccionarios con `.get()` y los comparaba directamente sin normalización.

**Fixes Implementados:**

| Estrategia | Campo(s) | Fix Aplicado |
|------------|----------|--------------|
| quantum_momentum | signal, confidence | `safe_float(quantum.get('signal', 0), ...)` |
| kalman_filter | strength, confidence | `safe_float(kalman.get('strength', 0.5), ...)` |
| monte_carlo | win_rate | `safe_float(monte_carlo.get('win_rate', 0.5), ...)` |
| kelly_criterion | optimal_fraction | `safe_float(kelly.get('optimal_fraction', 0), ...)` |
| black_swan | crash_probability | `safe_float(black_swan.get('crash_probability', 0), ...)` |
| sentiment | overall_score | `safe_float(sentiment.get('overall_score', 50), ...)` |
| non_markovian | confidence, bullish_score, bearish_score | `safe_float()` aplicado a los 3 campos |

**Mejora a safe_float:**
```python
if isinstance(value, str):
    value = value.strip().replace('%', '')
```

**Tests:** 12 tests directos + 28 tests en `tests/test_auto_trading_bot_type_safety.py`

**Archivos Modificados:**
- `omnix_core/bot/auto_trading_bot.py` - safe_float mejorado + aplicado en _build_strategy_signals (9 estrategias) + 2 funciones adicionales
- `omnix_services/coherence_service/coherence_engine.py` - Funciones normalize_* (fase 1)
- `tests/test_auto_trading_bot_type_safety.py` - 28 tests nuevos

---

## Critical Audit Fixes (Dec 30, 2025)

**Status:** ✅ COMPLETED

**Fixes Implementados:**

| Issue | Fix | Test |
|-------|-----|------|
| Coherence Gate skip on exception | FAIL-CLOSED: exception → BLOCKED + return | `test_coherence_exception_returns_blocked_in_source` |
| MC Veto ambiguo | ER<0% → BLOCKED (MC_NEG_ER), WR<50% → SIZE_REDUCE | `test_mc_neg_er_veto_reason_in_source` |
| DecisionPayload incompleto | +action, +vetoed, +size_multiplier, +execution_path | `test_payload_has_audit_fields` |
| TRACK_RECORD_MODE hardcoded | Controlado por ENV (default=false) | N/A (config change) |

**Tests:** 27/27 pasando (17 nuevos de auditoría crítica)

**Archivos Modificados:**
- `omnix_core/config/trading_profiles.py` - ENV control
- `omnix_core/bot/auto_trading_bot.py` - Audit fields + coherence FAIL-CLOSED
- `tests/test_critical_audit.py` - 17 tests nuevos

---

## Multi-User Architecture Progress (Updated Dec 22, 2025)

### Phase 3: AuthorizationService (COMPLETED)

**Status:** ✅ COMPLETED (Dec 22, 2025)

**Implementation:**
- Created `AuthorizationPort` (hexagonal port) at `src/omnix/ports/driven/authorization_port.py`
- Created `AuthorizationAdapter` at `src/omnix/infrastructure/adapters/authorization_adapter.py`
- Defined `UserRole` enum: FREE < BASIC < PRO < PREMIUM < OWNER
- Defined `Permission` enum with 15 granular permissions
- Implemented `ROLE_PERMISSIONS` mapping for B2C SaaS tiers
- PostgreSQL integration reads from existing `users.is_admin` and `users.subscription_tier`
- Redis cache with 5 min TTL for performance
- Fallback to `settings.TELEGRAM_ADMIN_ID` when adapter not available

**Hardcoded Checks Replaced (11 locations):**

| File | Guards Replaced |
|------|-----------------|
| `omnix_core/trading_system.py` | 2 (execute_real_trade, execute_auto_trade) |
| `omnix_services/telegram_service/enterprise_bot.py` | 7 (convert, auto-trading, auto-learning) |
| `omnix_services/optimization/performance_optimizer.py` | 1 (prioritize_request) |
| `omnix_services/ai_service/conversational_ai_adapter.py` | 1 (view_real_balance) |

**Tests:** 25/25 passing in `tests/test_authorization.py`

**Harold Updated in DB:**
```sql
UPDATE users SET is_admin = true, subscription_tier = 'owner' WHERE user_id = '7014748854';
```

### Phase 3b: AutoTradingBot Authorization Integration (COMPLETED)

**Status:** ✅ COMPLETED (Dec 22, 2025)

**Implementation:**
- Added `AUTHORIZATION_ADAPTER_AVAILABLE` import block in `auto_trading_bot.py`
- Created `_require_trading_permission()` helper method (lines 796-843)
- Integrated permission checks in 5 methods:
  - `start()` - checks `auto_trading` permission before activating
  - `stop()` - checks `auto_trading` permission before stopping
  - `_execute_smart_trade()` - checks `trading` permission before executing
  - `_check_open_positions_tp_sl()` - checks `view_positions` permission
  - `_check_position_limit_early()` - checks `view_positions` permission

**Permission Logic:**
- Paper mode: Uses `PAPER_TRADING` or `PAPER_AUTO_TRADING` for trading, `VIEW_BALANCE` for positions
- Real mode: Uses `REAL_TRADING` or `REAL_AUTO_TRADING` for trading, `VIEW_REAL_BALANCE` for positions
- Fallback: Uses `LEGACY_USER_ID` env var when adapter not available (strict match required)

**Security:**
- Fallback denies access if LEGACY_USER_ID is empty or user_id is None
- Fallback denies access if user_id doesn't match LEGACY_USER_ID exactly

**Tests:** 36/36 passing in `tests/test_authorization.py`

**Exception Handling:**
- Uses `AuthorizationError` (project-specific) instead of standard `PermissionError`
- All callers catch `AuthorizationError` specifically and abort operations
- No broad `except Exception` can swallow authorization failures

### Multi-User Architecture Status

**Status:** ✅ OPERATIONAL - Single-user SAFE, Multi-user READY

| Phase | Description | Status | Esfuerzo |
|-------|-------------|--------|----------|
| 1 | Eliminar hardcoded user_id | ✅ Done | 4h |
| 2 | INTEGRAR UserSessionManager existente | ✅ Done | 4h |
| 3 | Crear AuthorizationService | ✅ Done | 8h |
| 3b | Integrar en AutoTradingBot | ✅ Done | 4h |
| 4 | Implementar RLS en PostgreSQL | ✅ Done | 10h |
| 5 | Refactorizar trading loop | ✅ Done (uses UserSessionManager) | 8h |
| 6 | Tests de aislamiento | ✅ Done (32 tests) | 4h |
| 7 | PQC para auth (opcional) | ⏸️ Deferred | 8h |
| 8 | Documentación | ✅ Done | 4h |

**Activation Checklist:**
1. ✅ AuthorizationPort + AuthorizationAdapter implemented
2. ✅ 17 hardcoded checks replaced across 5 files
3. ✅ Harold has OWNER role in database
4. ✅ 32 tests passing
5. ⏸️ Feature flag `AUTHORIZATION_PORT_ENABLED` ready (currently false for Railway safety)

---

## Resolved Items

### Language Detection AI-First Refactor (RESOLVED)
**Status:** ✅ Resolved (Dec 22, 2025)

**Issue:** Language detection used hardcoded dictionaries (poor quality), was slow, and inconsistent.

**Resolution:**
- **ELIMINADOS** diccionarios hardcodeados de detección de idioma (código basura)
- **INSTALADO** `fast-langdetect` (FastText-based, 80x más rápido que langdetect)
- **FLUJO AI-First**:
  - Textos largos (≥50 chars): fast-langdetect (FastText, muy preciso)
  - Textos cortos (<50 chars): Gemini AI (`gemini-2.0-flash-lite`, temp=0, max_tokens=5)
  - Fallback: fast-langdetect → langdetect → 'en'
- **OPTIMIZACIÓN**: Cliente Gemini singleton para reducir latencia
- **MAPEO gTTS**: ISO codes a códigos gTTS válidos (ej: zh → zh-CN)
- **RESULTADO**: 12/12 tests pasando
- **Ubicación**: `omnix_services/ai_service/prompt_templates.py`, `omnix_services/voice_service/voice_controller.py`

### Hardcoded Multilingual Messages (RESOLVED)
**Status:** ✅ Resolved (Dec 19, 2025)

**Issue:** Fallback/error messages were hardcoded in Spanish across multiple files, causing wrong-language responses.

**Resolution:** 
- Replaced with minimal English placeholders in `ai_service.py`, `conversational_ai_adapter.py`, `ai_error_handler.py`
- AI-first approach: Gemini generates all localized content

### Language Detection Concurrency (RESOLVED)
**Status:** ✅ Resolved (Dec 19, 2025)

**Issue:** `langdetect` uses non-thread-safe global state, causing language bleed between concurrent users.

**Resolution:**
- Added `threading.Lock` for sync paths
- Added `asyncio.to_thread()` for async paths
- Redis persistence per `chat_id` with 24h TTL

---

## Executive Summary

This document registers known technical debt in OMNIX V6.5.4e. All items are **intentionally deferred** to prioritize track record generation for investor presentations. Refactoring is planned for V7.0 after achieving the 500-trade milestone.

---

## 1. Architecture Debt

### 1.1 Hexagonal Ports Not Integrated (SUBSTANTIALLY RESOLVED)

**Status:** Substantially resolved (Dec 22, 2025) - 19 ports, 21 adapters implemented

| Issue | Description |
|-------|-------------|
| Ports Defined | **19** protocol interfaces in `src/omnix/ports/` (16 driven + 3 driver) |
| Adapters Exist | **21** adapters in `src/omnix/infrastructure/adapters/` |
| Problem | **Todos los adapters implementados**, pero NO activos (feature flags = false) |
| Impact | Sistema opera 100% legacy; arquitectura V7 lista para activación gradual |

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

**Status:** Updated to V6.5.4e January 14, 2026

---

## 3.5 Phase 4: Version Normalization (COMPLETE - Dec 13, 2025)

**Issue:** ~30+ files had hardcoded version strings instead of using centralized `VERSION_BANNER` from `omnix_config/settings.py`.

**Root Cause:** Organic growth without enforcement of single source of truth for version.

**Solution Implemented:**

| Action | Files Modified |
|--------|----------------|
| Updated VERSION to 6.5.4e | `omnix_config/settings.py` |
| Import VERSION_BANNER | `omnix_dashboard/streamlit_app.py` |
| Import VERSION_BANNER | `omnix_services/ai_service/video/analyzer.py` |
| Import VERSION_BANNER | `omnix_services/ai_service/video/integration.py` |
| Import VERSION_BANNER | `omnix_services/ai_service/providers/omnix_style_renderer.py` |
| Import VERSION_BANNER | `omnix_services/ai_service/providers/omnix_prompt_builder.py` |
| Created version checker | `scripts/verify_version_consistency.py` |

**Central Version Location:**
```python
# omnix_config/settings.py
VERSION = "6.5.4e"
VERSION_NAME = "INSTITUTIONAL+"
VERSION_BANNER = f"V{VERSION} {VERSION_NAME}"  # "V6.5.4e INSTITUTIONAL+"
```

**Usage Pattern:**
```python
from omnix_config import VERSION_BANNER
logger.info(f"OMNIX {VERSION_BANNER} started")
```

**Preserved Historical Comments:**
- Calibration comments in `trading_profiles.py` (V6.5.4b, V6.5.4c, V6.5.4d, V6.5.4e) remain as historical audit trail
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
