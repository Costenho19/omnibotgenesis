# Multi-User Phase 2 - Data Access Audit

**Fecha**: 22 de Diciembre 2025  
**Estado**: ⚠️ 9/11 ISSUES CORREGIDOS (Revisión Final - Architect Dec 22, 2025)  
**Propósito**: Catalogar todos los touchpoints SQL/Redis que requieren user_id scoping

---

## 0. Resumen Ejecutivo

| Área | Touchpoints | Críticos | Estado |
|------|-------------|----------|--------|
| Hardcoded user_id | 8 | 4 (AutoTradingBot) | ✅ CORREGIDO (Paso 2 - Dec 22) |
| Database Services con user_id='harold' default | 3 | 0 | ✅ CORREGIDO - user_id obligatorio (Paso 7 - Dec 22) |
| PaperTradingRepository user_id=None | 4 | 0 | ✅ CORREGIDO - user_id obligatorio (Paso 6 - Dec 22) |
| Tablas sin RLS | 11+ | 3 (paper_trading_*, user_settings) | ✅ RLS habilitado (Paso 3 - Dec 22) |
| Funciones YA con user_id obligatorio | 40+ | 0 | ✅ Listas |
| Redis keys | 6 callers | 0 (todos verificados OK) | ✅ Verificados |
| **Entry points sin user_id** | 3+ | 2 | ⚠️ **PENDIENTE** - REST/Dashboard/Scheduler |
| **Hard-checks "7014748854"** | 4 | 2 | ⚠️ **PENDIENTE** - TradingSystem guards |

### Estado Operacional

| Modo | Estado | Notas |
|------|--------|-------|
| Single-User (Harold) | ✅ **SEGURO** | Fallback a LEGACY_USER_ID funciona |
| Multi-Usuario | ❌ **BLOQUEADO** | 2 issues restantes impiden activación |

### Blockers Restantes (2)

1. **Entry Points sin user_id**: Telegram command handlers, REST blueprints, dashboard routes invocan trading sin pasar user_id explícito → caen en fallback a LEGACY_USER_ID
2. **Hard-checks de Harold en Guards**: `trading_system.py` (líneas ~865, ~1093), `performance_optimizer.py`, `conversational_ai_adapter.py` verifican `if str(user_id) == "7014748854"` y rechazan otros usuarios

### Plan de Remediación (Fase 3)

| Paso | Descripción | Prioridad |
|------|-------------|-----------|
| 3.1 | Modificar entry points para pasar user_id autenticado | ALTA |
| 3.2 | Cambiar `_get_effective_user_id()` para raise en lugar de fallback | MEDIA |
| 3.3 | Eliminar/feature-flag hard-checks de "7014748854" | ALTA |
| 3.4 | Tests de integración end-to-end multi-usuario | ALTA |

---

## 1. Hardcoded user_id (CRÍTICO)

### 1.1 AutoTradingBot - harold_user_id Hardcodes

**ESTADO**: ✅ **CORREGIDO** (Paso 2 - Dec 22, 2025)

| Archivo | Línea | Función | Estado |
|---------|-------|---------|--------|
| `omnix_core/bot/auto_trading_bot.py` | 1349 | `_check_open_positions_tp_sl()` | ✅ Usa `_get_effective_user_id()` |
| `omnix_core/bot/auto_trading_bot.py` | 2677 | `_execute_smart_trade()` | ✅ Usa `_get_effective_user_id()` |
| `omnix_core/bot/auto_trading_bot.py` | 3199 | position check para SELL | ✅ Usa user_id de `_execute_smart_trade` |
| `omnix_core/bot/auto_trading_bot.py` | 4248 | `_check_position_limit_early()` | ✅ Usa `_get_effective_user_id()` |

**Solución implementada:**
- Nuevo método `_get_effective_user_id(passed_user_id, caller)` (línea 726)
- Prioridad: explicit > config['user_id'] > LEGACY_USER_ID env var
- NO hay hardcoded values en código - `LEGACY_USER_ID` desde env var
- Warning logs cuando usa fallback (ayuda debugging de migración)
- Raises ValueError si no hay user_id disponible

### 1.2 TradingSystem - user_id Check

| Archivo | Línea | Propósito |
|---------|-------|-----------|
| `omnix_core/trading_system.py` | 865 | `if str(user_id) != "7014748854"` - Restricción de usuario |
| `omnix_core/trading_system.py` | 1093 | `if str(user_id) != "7014748854"` - Restricción de usuario |

### 1.3 Otros Servicios con Harold Priority

| Archivo | Línea | Impacto |
|---------|-------|---------|
| `omnix_services/optimization/performance_optimizer.py` | 70 | `if str(user_id) == "7014748854"` - Prioridad Harold |
| `omnix_services/ai_service/conversational_ai_adapter.py` | 517 | `if str(user_id) == "7014748854"` - Consulta Kraken |

---

## 2. SQL Queries - Tablas que Requieren RLS

### 2.1 paper_trading_trades

| Archivo | Línea | Operación | user_id Presente |
|---------|-------|-----------|------------------|
| `omnix_core/bot/paper_trading.py` | 396 | INSERT | ✅ Sí |
| `omnix_core/bot/paper_trading.py` | 444 | INSERT | ✅ Sí |
| `omnix_core/bot/auto_trading_bot.py` | 3352 | SELECT COUNT | ⚠️ Verificar |
| `omnix_services/trading_service/paper_trading_manager.py` | 623 | INSERT | ✅ Sí |

### 2.2 paper_trading_balances

| Archivo | Línea | Operación | user_id Presente |
|---------|-------|-----------|------------------|
| `omnix_core/bot/paper_trading.py` | 306 | INSERT/UPSERT | ✅ Sí |
| `omnix_services/trading_service/paper_trading_manager.py` | 509 | INSERT/UPSERT | ✅ Sí |

### 2.3 user_settings

| Archivo | Línea | Operación | user_id Presente |
|---------|-------|-----------|------------------|
| `omnix_core/bot/auto_trading_bot.py` | 1085 | INSERT | ✅ Sí |
| `omnix_core/bot/auto_trading_bot.py` | 1094 | SELECT | ✅ Sí |
| `omnix_core/bot/auto_trading_bot.py` | 1110 | INSERT | ✅ Sí |

---

## 3. Redis Keys - Requieren user_id Scoping

### 3.1 Session Keys (YA con user_id)

| Patrón | Archivo | Estado |
|--------|---------|--------|
| `omnix:session:{user_id}` | `omnix_core/sessions/user_session_manager.py:136` | ✅ OK |

### 3.2 Redis Cache Infrastructure (omnix_core/cache/redis_cache.py)

**Arquitectura del Cache:**
- `RedisCache` (líneas 23-214): Clase de bajo nivel con métodos get/set/delete
- `cache_result` decorator (líneas 245-267): Genera keys automáticamente con `func_name + args + kwargs`
- `_normalize_cache_key()` (líneas 217-241): Hashea argumentos de función para generar key única

**Comportamiento de `cache_result` decorator:**
```
Key = "{prefix}:{func_name}:{hash_de_args_y_kwargs}"
```
- Si la función tiene `user_id` como argumento → key INCLUYE user_id automáticamente ✅
- Si la función NO tiene `user_id` → datos COMPARTIDOS (por diseño para market data)

**Callers de redis_cache.py:**

| Caller | Archivo | Tipo de Uso | Multi-User Safe |
|--------|---------|-------------|-----------------|
| rate_limiter | `omnix_core/utils/rate_limiter.py` | Rate limiting | ✅ Key=`{prefix}:{identifier}` donde identifier=user_id |
| redis_state | `omnix_core/cache/redis_state.py` | Conversación | ✅ Usa chat_id |
| trading_service | `omnix_services/trading_service/trading_service.py` | Market data decorator | ✅ Compartido OK |
| kraken_client | `omnix_services/trading_service/kraken_client.py` | Market data decorator | ✅ Compartido OK |
| ai_service | `omnix_services/ai_service/ai_service.py` | AI responses | ✅ No usa cache directamente |
| search_manager | `omnix_services/web_search_service/search_manager.py` | Web search | ✅ Compartido OK |

### 3.2.1 Cache Keys Específicas (Verificadas)

| Archivo | Línea | Key | Requiere user_id | Estado |
|---------|-------|-----|------------------|--------|
| `auto_trading_bot.py` | 1146-1150 | `omnix:heartbeat:trading_loop` | ❌ Sistema global | ✅ OK - Monitoreo singleton |
| `user_session_manager.py` | 252 | `omnix:session:{user_id}` | ✅ Tiene user_id | ✅ OK |

> **Verificación completada**: La key `omnix:heartbeat:trading_loop` es para monitoreo del sistema (singleton), no datos de usuario. No requiere user_id.

### 3.3 Redis Usage en Otros Servicios

| Servicio | Archivo | Tipo de Cache | Requiere user_id | Estado |
|----------|---------|---------------|------------------|--------|
| Web Search | `web_search_service/search_manager.py` | Resultados de búsqueda | ❌ Compartido | OK |
| Alpha Vantage | `market_intelligence/alpha_vantage_service.py` | Market data | ❌ Compartido | OK |
| Fear & Greed | `market_intelligence/fear_greed_service.py` | Indicadores | ❌ Compartido | OK |
| Finnhub | `market_intelligence/finnhub_service.py` | News cache | ❌ Compartido | OK |
| Language Detection | `ai_service/prompt_templates.py:323` | Idioma por chat_id | ✅ Ya usa chat_id | OK |
| RedisContextProvider | `ai_service/providers/redis_context_provider.py` | Conversation history | ✅ Ya usa user_id | OK |

### 3.4 Cache In-Memory (NO Redis - Sin Persistencia)

| Servicio | Archivo | Tipo | Keying | Riesgo Multi-User |
|----------|---------|------|--------|-------------------|
| IntelligentCacheSystem | `concurrency/cache_system.py` | Python dict | Global | ❌ Ninguno (proceso local) |
| User Settings Cache | `user_settings/user_settings_service.py` | Python dict | `[user_id]` | ✅ Aislado por user_id |
| Daily Stats Cache | `user_settings/user_settings_service.py` | Python dict | `[user_id]` | ✅ Aislado por user_id |

**Verificación user_settings_service.py (líneas 52, 121-132, 499-562)**:
- `self._settings_cache[user_id]` - ✅ Keys por user_id
- `self._daily_stats_cache[user_id]` - ✅ Keys por user_id
- No hay riesgo de cross-user leakage

> **Nota sobre IntelligentCacheSystem**: Usa diccionarios Python (`self.cache = {}`) NO Redis. Es local al proceso, no persiste entre reinicios, y cada proceso tiene su propia instancia. No representa riesgo de cross-user leakage.

> **Nota sobre market data caches**: Datos de mercado (precios, indicadores, noticias) son PÚBLICOS y COMPARTIDOS entre usuarios por diseño. No requieren aislamiento.

---

## 3b. Database Services - user_id OPCIONAL (RIESGO)

> **RIESGO**: Funciones con `user_id: Optional[str] = None` pueden retornar TODOS los datos si no se pasa user_id.

### 3b.1 PaperTradingRepository (omnix_services/database_service/)

**ESTADO**: ✅ **CORREGIDO** (Paso 6 - Dec 22, 2025)

| Función | Línea | user_id Param | Estado |
|---------|-------|---------------|--------|
| `get_trade_statistics(user_id: str)` | 40 | ✅ Obligatorio | Filtrado por usuario |
| `get_recent_trades(user_id: str, limit)` | 136 | ✅ Obligatorio | Filtrado por usuario |
| `get_paper_balance(user_id: str)` | 231 | ✅ Obligatorio | Filtrado por usuario |
| `get_full_performance_context(user_id: str)` | 342 | ✅ Obligatorio | Filtrado por usuario |

**Cambio realizado**: Parámetro `user_id` ahora es `str` obligatorio en lugar de `Optional[str] = None`. Las queries SQL siempre incluyen `WHERE user_id = %s`.

### 3b.2 DatabaseManager (omnix_services/database_service/)

| Función | Línea | user_id Param | Estado |
|---------|-------|---------------|--------|
| `save_balance_snapshot(user_id, ...)` | 55 | ✅ Requerido | OK |
| `get_balance_history(user_id, days)` | 60 | ✅ Requerido | OK |
| `ensure_user_exists(user_id, ...)` | 87 | ✅ Requerido | OK |
| `save_conversation(user_id, ...)` | 99 | ✅ Requerido | OK |
| `get_paper_trading_balance(user_id)` | 137 | ✅ Requerido | OK |
| `get_risk_limits(user_id)` | 146 | ✅ Requerido | OK |
| `get_circuit_breaker_status(user_id)` | 155 | ✅ Requerido | OK |
| `get_daily_trading_stats(user_id)` | 164 | ✅ Requerido | OK |
| `get_open_positions(user_id)` | 173 | ✅ Requerido | OK |

### 3b.3 DatabaseGateway - Análisis de Queries

| Archivo | Línea | Query | Contexto | Riesgo |
|---------|-------|-------|----------|--------|
| `database_gateway.py` | 17 | `SELECT * FROM trades` | **DOCSTRING** (ejemplo de uso) | ❌ Ninguno |
| `database_gateway.py` | 20 | `SELECT * FROM trades WHERE id = %s` | **DOCSTRING** (ejemplo de uso) | ❌ Ninguno |
| `database_gateway.py` | 282 | `SELECT * FROM trades WHERE id = %s` | Código real | ⚠️ Filtra por trade_id |

> **ACLARACIÓN IMPORTANTE**: Las queries en líneas 17 y 20 son **EJEMPLOS EN DOCSTRINGS**, NO código ejecutable. DatabaseGateway es un **connection pool singleton** - NO ejecuta queries por sí mismo. Las queries reales vienen de callers (DatabaseManager, DatabaseService, etc.) que YA incluyen user_id.

**Métodos reales de DatabaseGateway:**
- `get_pool()` - Retorna connection pool
- `execute_query()` - Ejecuta query genérica
- `get_instance()` - Singleton pattern

> **Conclusión DatabaseGateway**: No representa riesgo multi-user. Es infraestructura de bajo nivel. El filtrado de user_id ocurre en capas superiores (DatabaseManager, DatabaseService).

**Call Sites de DatabaseGateway**:
| Caller | Archivo | Línea | Contexto |
|--------|---------|-------|----------|
| `_execute_query()` wrapper | `database_service.py` | 291 | Wrapper seguro, queries vienen de funciones que YA filtran por user_id |
| Ejemplos docstring | `database_gateway.py` | 15, 20 | NO ejecutables |
| `get_trade_by_id()` | `database_gateway.py` | 282 | Busca por trade_id | ⚠️ Ver análisis abajo |

**Análisis `get_trade_by_id()` (línea 282)**:
- Query: `SELECT * FROM trades WHERE id = %s`
- Filtra por trade_id, NO por user_id

**Caller Trace (definitivo)**:
```
get_trade_by_id() [database_gateway.py:282]
  └── DatabasePort.get_trade_by_id() [database_port.py:79]
       └── (V7.0 hexagonal ports - feature flags ALL FALSE)
            └── SIN USO EN PRODUCCIÓN - código inactivo
```

**Verificación de feature flags** (src/omnix/config/settings.py):
- `USE_DATABASE_PORT = false` (default)
- `USE_CACHE_PORT = false` (default)
- Todos los flags V7.0 = false

**Conclusión**: 
- **Riesgo actual**: NULO - La función existe pero NO se ejecuta en producción (Railway usa legacy code 100%)
- **Riesgo futuro (cuando V7.0 se active)**: RLS en tabla `trades` filtrará automáticamente por user_id

> **Nota**: El único uso real de `execute_query()` es dentro de `database_service._execute_query()` que es llamado por funciones que YA requieren user_id.

### 3b.4 PaperTradingRepository - Callers

| Caller | Archivo | Línea | Pasa user_id? |
|--------|---------|-------|---------------|
| `get_real_trading_context()` | `conversational_ai_adapter.py` | 469-472 | ⚠️ Depende del caller |

> **Solo 1 caller**: `conversational_ai_adapter.py` es el único que importa y usa `PaperTradingRepository`. Se debe verificar que pase user_id.

### 3b.5 DatabaseService (omnix_services/database_service/)

**Archivo**: `database_service.py` (~4900 líneas)

#### Funciones CON user_id OBLIGATORIO (✅ OK)
| Función | Línea | user_id Param |
|---------|-------|---------------|
| `save_balance_snapshot(user_id, ...)` | 2574 | ✅ Requerido |
| `get_balance_history(user_id, days)` | 2617 | ✅ Requerido |
| `ensure_user_exists(user_id, ...)` | 2768 | ✅ Requerido |
| `save_conversation(user_id, ...)` | 2856 | ✅ Requerido |
| `submit_community_feedback(user_id, ...)` | 3273 | ✅ Requerido |
| `vote_strategy(user_id, ...)` | 3351 | ✅ Requerido |
| `update_user_contributions(user_id, ...)` | 3380 | ✅ Requerido |
| `submit_proposal(user_id, ...)` | 3461 | ✅ Requerido |
| `add_user_contact(user_id, ...)` | 3960 | ✅ Requerido |
| `get_user_contacts(user_id, ...)` | 4011 | ✅ Requerido |
| `verify_user_contact(user_id, ...)` | 4070 | ✅ Requerido |
| `set_primary_contact(user_id, ...)` | 4113 | ✅ Requerido |
| `get_risk_limits(user_id)` | 4168 | ✅ Requerido |
| `save_risk_breach(user_id, ...)` | 4276 | ✅ Requerido |
| `get_risk_breaches(user_id, days)` | 4325 | ✅ Requerido |
| `save_risk_metrics_snapshot(user_id, ...)` | 4376 | ✅ Requerido |
| `get_risk_metrics_history(user_id, days)` | 4454 | ✅ Requerido |
| `get_circuit_breaker_status(user_id)` | 4508 | ✅ Requerido |
| `save_circuit_breaker_status(user_id, ...)` | 4555 | ✅ Requerido |
| `save_risk_alert(user_id, ...)` | 4612 | ✅ Requerido |
| `get_daily_trading_stats(user_id)` | 4638 | ✅ Requerido |
| `get_open_positions(user_id)` | 4687 | ✅ Requerido |
| `get_paper_trading_balance(user_id)` | 4735 | ✅ Requerido |
| `get_recent_trades(user_id, limit)` | 4813 | ✅ Requerido |

#### Funciones CON user_id='harold' POR DEFECTO - ✅ CORREGIDAS (Paso 7 - Dec 22)

**ESTADO**: ✅ **CORREGIDO** - Todas las funciones ahora requieren user_id obligatorio

| Función | Línea | Estado |
|---------|-------|--------|
| `get_recent_reasonings(user_id: str)` | 3045 | ✅ Obligatorio |
| `get_learning_summary(user_id: str)` | 3101 | ✅ Obligatorio |
| `schedule_trade_evaluation(..., user_id: str)` | 3151 | ✅ Obligatorio |

**Callers actualizados:**
- `trading_system.py:2940` - Ahora usa `user_id` del mensaje Telegram
- `trading_system.py:2969` - Ahora usa `user_id` del mensaje Telegram  
- `auto_trading_bot.py:3460` - Ahora usa `_get_effective_user_id()`

#### Queries de Schema/Metadata (Sin filtro user_id - OK)
Todas las queries a `information_schema.*` son para verificación de estructura, no datos de usuario.

| Tipo | Ejemplos | Riesgo |
|------|----------|--------|
| Schema checks | `SELECT FROM information_schema.tables` | ❌ Ninguno |
| Migrations | `SELECT executed_at FROM schema_migrations` | ❌ Ninguno |
| Counts globales | `SELECT COUNT(*) FROM users` | ⚠️ Solo admin |

#### Queries Community/Analytics (Datos públicos compartidos)
| Tabla | Tipo | Riesgo Multi-User |
|-------|------|-------------------|
| `community_feedback` | Público por diseño | ❌ Compartido OK |
| `improvement_proposals` | Público por diseño | ❌ Compartido OK |
| `detected_patterns` | Público por diseño | ❌ Compartido OK |
| `video_transcript_cache` | Público | ❌ Compartido OK |

> **Conclusión DatabaseService**: 24+ funciones YA requieren user_id obligatorio. Solo 3 funciones tienen 'harold' hardcoded como default. Las queries de schema y community son seguras.

---

#### Legacy reference (para compatibilidad)

| Función | Línea | user_id Param | Estado |
|---------|-------|---------------|--------|
| `save_balance_snapshot(user_id, ...)` | 2574 | ✅ Requerido | OK |
| `get_balance_history(user_id, days)` | 2617 | ✅ Requerido | OK |
| `ensure_user_exists(user_id, ...)` | 2768 | ✅ Requerido | OK |
| `add_user_contact(user_id, ...)` | 3960 | ✅ Requerido | OK |
| `get_user_contacts(user_id, ...)` | 4011 | ✅ Requerido | OK |
| `get_risk_limits(user_id)` | 4168 | ✅ Requerido | OK |
| `save_risk_breach(user_id, ...)` | 4276 | ✅ Requerido | OK |
| `get_risk_breaches(user_id, days)` | 4325 | ✅ Requerido | OK |
| `get_circuit_breaker_status(user_id)` | 4508 | ✅ Requerido | OK |
| `save_circuit_breaker_status(user_id, ...)` | 4555 | ✅ Requerido | OK |

---

## 4. Funciones que YA Aceptan user_id

### 4.1 PaperTradingManager (omnix_services/trading_service/)

| Función | Línea | Acepta user_id |
|---------|-------|----------------|
| `initialize_user(user_id)` | 81 | ✅ |
| `execute_paper_trade(user_id, ...)` | 141 | ✅ |
| `get_paper_balance(user_id)` | 414 | ✅ |
| `get_open_positions(user_id)` | 917 | ✅ |
| `has_open_position_for_symbol(user_id, symbol)` | 963 | ✅ |
| `_close_position_fifo_v2(user_id, ...)` | 678 | ✅ |
| `get_trade_pnl_report(user_id)` | 830 | ✅ |

### 4.2 PositionManager

| Función | Línea | Acepta user_id |
|---------|-------|----------------|
| `manage_all_positions(user_id, paper_mode)` | 549 | ✅ |
| `_close_position(user_id, position, ...)` | 708 | ✅ |

---

## 5. Tablas PostgreSQL - RLS Requerido

### 5.1 Tablas Críticas (Trading Data)

| Tabla | Columna user_id | RLS Activo | Prioridad |
|-------|-----------------|------------|-----------|
| `paper_trading_trades` | ✅ Existe | ❌ No | 🔴 ALTA |
| `paper_trading_balances` | ✅ Existe | ❌ No | 🔴 ALTA |
| `trades` | ✅ Existe | ❌ No | 🔴 ALTA |

### 5.2 Tablas de Usuario

| Tabla | Columna user_id | RLS Activo | Prioridad |
|-------|-----------------|------------|-----------|
| `user_settings` | ✅ PK | ❌ No | MEDIA |
| `user_contacts` | ✅ Existe | ❌ No | MEDIA |
| `user_contributions` | ✅ Existe | ❌ No | BAJA |

### 5.3 Tablas de Análisis y Logs

| Tabla | Columna user_id | RLS Activo | Prioridad |
|-------|-----------------|------------|-----------|
| `conversation_history` | ⚠️ Verificar | ❌ No | BAJA |
| `risk_limit_breaches` | ✅ Existe | ❌ No | MEDIA |
| `risk_metrics_snapshots` | ✅ Existe | ❌ No | MEDIA |
| `circuit_breaker_status` | ✅ Existe | ❌ No | MEDIA |
| `balance_history` | ✅ Existe | ❌ No | MEDIA |

### 5.4 Tablas Comunitarias (sin RLS por diseño)

| Tabla | Razón sin RLS |
|-------|---------------|
| `community_feedback` | Datos compartidos entre usuarios |
| `strategy_votes` | Datos públicos de votación |
| `improvement_proposals` | Propuestas compartidas |

---

## 6. Plan de Acción (Actualizado)

### Paso 1 (Propagar User Context)
- [ ] enterprise_bot.py: Extraer user_id de `update.effective_user.id` en cada handler
- [ ] Pasar user_id a todas las llamadas de AutoTradingBot

### Paso 2 (Activar UserSessionManager) - ✅ COMPLETADO (Dec 22)
- [x] USER_SESSION_MANAGER_AVAILABLE ya es True cuando el import funciona
- [x] start()/stop() integrados con UserSessionManager
- [x] Callers en trading_system.py actualizados para pasar user_id

### Paso 3 (UserConfigPort)
- [ ] Crear nuevo port y adapter para configuración por usuario
- [ ] Cache Redis con TTL

### Paso 4 (Refactorizar AutoTradingBot)
- [ ] Eliminar 4 hardcodes de `harold_user_id` en auto_trading_bot.py
- [ ] Eliminar 2 checks en trading_system.py
- [ ] Cambiar a recibir user_id como parámetro

### Paso 5 (PostgreSQL RLS)
- [ ] Migración: ALTER TABLE ENABLE RLS en 3 tablas críticas
- [ ] Crear políticas: tenant_isolation_*
- [ ] Modificar DatabaseManager para SET app.current_user_id
- [ ] Políticas permisivas para dashboards/analytics

### Paso 6 (PaperTradingRepository)
- [ ] Cambiar `user_id=None` a `user_id: str` (obligatorio) en 4 funciones
- [ ] O asegurar que siempre se pase user_id desde callers

### Redis Keys (Paso 8)
- [ ] Verificar que todas las keys de cache incluyan user_id si aplica
- [ ] Validar que no haya colisiones entre usuarios

---

## 7. Resumen de Hallazgos

### 7.1 Elementos que Requieren Cambios (ACCIÓN REQUERIDA)

**Fuente: Sección 1 de este documento (verificado)**

| Categoría | Total | Archivos/Líneas Verificadas | Severidad |
|-----------|-------|----------------------------|-----------|
| Hardcoded user_id=7014748854 | 4 | `auto_trading_bot.py` (1308, 2637, 3168, 4210) | 🔴 CRÍTICO |
| Restricción user_id en TradingSystem | 2 | `trading_system.py` (865, 1093) | 🔴 CRÍTICO |
| Prioridad Harold en Services | 2 | `performance_optimizer.py:70`, `conversational_ai_adapter.py:517` | 🟡 MEDIO |
| Funciones user_id='harold' default | 3 | `database_service.py` (3042, 3098, 3148) | 🟡 MEDIO |
| PaperTradingRepository user_id=None | 4 | `paper_trading_repository.py` (ver Sección 3b.1) | 🟡 MEDIO |
| Tablas sin RLS | 3 críticas | paper_trading_trades, paper_trading_balances, trades | 🔴 CRÍTICO |

### 7.1.1 Resumen Ejecutivo de Cambios Necesarios

| Acción | Esfuerzo | Riesgo |
|--------|----------|--------|
| Eliminar 8 user_id hardcoded | ~4h | Bajo (callers ya soportan user_id) |
| Cambiar 3 defaults 'harold' a obligatorio | ~1h | Bajo (son funciones internas) |
| Enforizar user_id en 4 PaperTradingRepo funcs | ~2h | Bajo (1 caller conocido) |
| Crear RLS policies en 3 tablas | ~4h | Medio (requiere testing exhaustivo) |
| **TOTAL** | **~11h** | **Bajo-Medio** |

### 7.2 Elementos YA Correctos (No requieren cambios)

| Categoría | Cantidad | Estado |
|-----------|----------|--------|
| DatabaseService funciones con user_id obligatorio | 24+ | ✅ OK |
| DatabaseManager funciones con user_id obligatorio | 7 | ✅ OK |
| PaperTradingManager funciones con user_id obligatorio | 9 | ✅ OK |
| Redis services con user_id/chat_id | 3 | ✅ OK |
| In-memory caches con user_id keying | 2 | ✅ OK |
| UserSessionManager | 1 | ✅ OK |
| RedisContextProvider | 1 | ✅ OK |

---

## 8. Conclusiones

1. **Problema Principal**: `AutoTradingBot` hardcodea user_id antes de llamar funciones que YA soportan multi-usuario.

2. **Solución**: Propagar user_id desde Telegram → AutoTradingBot → Services.

3. **Riesgo Adicional**: `PaperTradingRepository` tiene 4 funciones con `user_id=None` que pueden retornar datos de todos los usuarios si no se pasa el parámetro.

4. **RLS**: 11+ tablas necesitan políticas, pero solo 3 son críticas para trading data.

5. **Buena Noticia**: La mayoría de funciones en DatabaseManager, DatabaseService, y PaperTradingManager YA requieren user_id como parámetro obligatorio.

---

*Generado: 22 de Diciembre 2025 (Revisión 3 - Final)*

---

## 9. Apéndice: Cobertura de Auditoría

### Áreas Auditadas ✅
- `omnix_core/bot/` - AutoTradingBot, paper_trading
- `omnix_core/sessions/` - UserSessionManager
- `omnix_core/cache/` - Redis cache
- `omnix_core/trading_system.py` - Sistema de trading
- `omnix_services/database_service/` - DatabaseGateway, DatabaseManager, DatabaseService, PaperTradingRepository
- `omnix_services/trading_service/` - PaperTradingManager, PositionManager
- `omnix_services/market_intelligence/` - Cache de market data
- `omnix_services/ai_service/` - Conversational adapter, language detection
- `omnix_services/optimization/` - Performance optimizer

### Áreas Excluidas (No requieren user_id)
- Market data services (datos públicos compartidos)
- Web search cache (resultados compartidos)
- Community intelligence (datos públicos por diseño)
- Schema migrations
