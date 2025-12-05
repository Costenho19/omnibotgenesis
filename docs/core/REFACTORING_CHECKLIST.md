# OMNIX V6.5.2 - Refactoring Checklist

> **Documento:** Lista de verificación para refactorización  
> **Ubicación:** `docs/core/REFACTORING_CHECKLIST.md`  
> **Creado:** 5 de Diciembre, 2025  
> **Estado:** En progreso  
> **Propósito:** Guía temporal para resolver discrepancias entre documentación y código. Eliminar al completar.

---

## Resumen Ejecutivo

Este documento lista todas las discrepancias encontradas entre la documentación técnica (`docs/core/*.md`) y el código actual. Cada issue tiene un checkbox para marcar cuando se complete.

**Prioridades:**
- 🔴 HIGH = Afecta funcionamiento o seguridad
- 🟡 MED = Afecta precisión de documentación
- 🟢 LOW = Mejoras opcionales

---

## 1. Dependencias y Paquetes

### 1.1 google-generativeai (DEPRECATED)
- **Prioridad:** 🔴 HIGH
- **Estado:** [x] ✅ COMPLETADO (Dec 5, 2025)
- **Problema:** Paquete `google-generativeai==0.8.5` está deprecado desde Agosto 2025
- **Solución:** Migrar a `google-genai` (nuevo SDK oficial)

**Solución implementada (V6.5.2):**
- [x] `requirements.txt` - Agregado `google-genai>=1.0.0`, documentado conflicto websockets
- [x] `omnix_services/ai_service/ai_models.py` - Import dual con fallback, GEMINI_SDK_VERSION
- [x] `omnix_services/ai_service/conversational_ai_adapter.py` - Import dual con fallback
- [x] `omnix_services/ai_service/video/analyzer.py` - Inicialización con _gemini_sdk tracking
- [x] `omnix_services/telegram_service/enterprise_bot.py` - Migrado a gemini_client con SDK version
- [x] `omnix_services/community_intelligence/community_analyzer.py` - Soporta nuevo y legacy SDK
- [x] `main.py` - Ya tenía código dual (nuevo SDK primero)

**Nota:** Conflicto de websockets (alpaca-trade-api <11 vs google-genai >=13). Usando versión para alpaca-trade-api, google-genai funciona con warning.

### 1.2 anthropic - Error en Documentación
- **Prioridad:** 🟢 LOW
- **Estado:** [ ] Pendiente
- **Problema:** `Omnix_TECHNICAL_REFERENCE.md` dice "(missing) - needs to be added" pero SÍ existe
- **Realidad:** `anthropic==0.75.0` está en requirements.txt y se importa correctamente
- **Solución:** Actualizar documentación
- **Archivos a corregir:**
  - [ ] `docs/core/Omnix_TECHNICAL_REFERENCE.md` línea ~464

---

## 2. Phase 4: Database Service Unification

### 2.1 DatabaseGateway no migrado a servicios Enterprise
- **Prioridad:** 🔴 HIGH
- **Estado:** [ ] Pendiente
- **Problema:** `DatabaseGateway` solo se usa en Dashboard, no en servicios principales
- **Ubicación actual de DatabaseGateway:**
  - ✅ `omnix_dashboard/gunicorn.conf.py`
  - ✅ `omnix_dashboard/utils/database.py`
  - ❌ `omnix_services/trading_service/*` - NO MIGRADO
  - ❌ `omnix_services/telegram_service/*` - NO MIGRADO
  - ❌ `main.py` - NO MIGRADO

### 2.2 Tareas Phase 4 Pendientes (de DATABASE_AUDIT_REPORT.md)
- [ ] **4.1** Trading Manager Adapter - Migrar `paper_trading_manager.py`
- [ ] **4.2** Bot Migration - Migrar `enterprise_bot.py` y `main.py`
- [ ] **4.3** Legacy Deprecation Warnings - Agregar warnings a código viejo
- [ ] **4.4** Documentation Update - Actualizar docs cuando complete

---

## 3. Endpoints API

### 3.1 Endpoints No Documentados
- **Prioridad:** 🟡 MED
- **Estado:** [ ] Pendiente
- **Problema:** 2 endpoints existen en código pero no en documentación

| Endpoint | Archivo | Línea | Doc Status |
|----------|---------|-------|------------|
| `/api/db-diagnostics` | system.py | 438 | ❌ No documentado |
| `/api/benchmarks` | market.py | 369 | ❌ No documentado |

- **Solución:** Agregar a `DASHBOARD_TECHNICAL_REFERENCE.md`
- [ ] Documentar `/api/db-diagnostics`
- [ ] Documentar `/api/benchmarks`

### 3.2 Endpoints Sin Consumidor Frontend
- **Prioridad:** 🟢 LOW
- **Estado:** [ ] Pendiente
- **Problema:** Endpoints backend existen pero ningún JS los consume

| Endpoint | Backend | JS Consumer |
|----------|---------|-------------|
| `/api/portfolio` | core.py:270 | ❌ No existe |
| `/api/market/stocks` | market.py:81 | ❌ No existe |
| `/api/intelligence/summary` | intelligence.py:268 | ❌ No existe |
| `/api/intelligence/alpha-vantage/*` | intelligence.py:233 | ❌ No existe |
| `/api/intelligence/finnhub/sentiment/*` | intelligence.py:198 | ❌ No existe |

- **Opciones:**
  - [ ] Crear componentes JS para consumir estos endpoints
  - [ ] O marcar como "API-only" en documentación

---

## 4. Conteo de Líneas Desactualizado

### 4.1 Archivos con más líneas que documentación
- **Prioridad:** 🟡 MED
- **Estado:** [ ] Pendiente

| Archivo | Doc | Real | Delta |
|---------|-----|------|-------|
| `omnix_core/trading_system.py` | 5,486 | 5,576 | +90 |
| `omnix_core/bot/auto_trading_bot.py` | ~3,400 | 3,532 | +132 |
| `omnix_services/trading_service/paper_trading_manager.py` | 961 | 1,023 | +62 |
| `omnix_dashboard/static/js/components/tradehistory.js` | ~130 | 177 | +47 |
| `omnix_dashboard/static/js/components/snapshots.js` | 150 | 307 | +157 |
| `omnix_dashboard/blueprints/core.py` | ~470 | 552 | +82 |
| `omnix_dashboard/blueprints/system.py` | 435 | 491 | +56 |

- **Solución:** Actualizar line counts en:
  - [ ] `docs/core/Omnix_TECHNICAL_REFERENCE.md`
  - [ ] `docs/core/DASHBOARD_TECHNICAL_REFERENCE.md`

### 4.2 Conteo Total de Paquetes
- **Documentación dice:**
  - omnix_services: 62,613 líneas
  - omnix_core: 20,131 líneas
- **Código real:**
  - omnix_services: ~52,093 líneas
  - omnix_core: ~15,801 líneas
- **Nota:** Diferencia significativa, verificar si se eliminó código o si conteo incluye comentarios/blanks

---

## 5. Issues de Trading Logic

### 5.1 Volumes = None bloquea estrategias
- **Prioridad:** 🔴 HIGH
- **Estado:** [x] ✅ COMPLETADO (Dec 5, 2025)
- **Problema:** Cuando `_get_volume_history()` retorna None, bloquea quantum y HMM
- **Ubicación:** `omnix_core/bot/auto_trading_bot.py`

**Solución implementada (V6.5.2):**
- [x] HMM Regime: Cambiada condición de `prices and volumes` a solo `prices`
- [x] Quantum Momentum: Usa `analyze()` con OHLC completo via nuevo `_get_ohlc_history()`
- [x] Nuevo método `_get_ohlc_history()`: Devuelve OHLC con volumes sintéticos si faltan
- [x] Nuevo método `_generate_synthetic_volumes()`: Genera volumes basados en price changes
- [x] Logging cuando se usan volumes sintéticos
- [x] Protección contra ZeroDivision y length mismatch

### 5.2 VETO Scoring Desbalanceado
- **Prioridad:** 🟡 MED
- **Estado:** [ ] Pendiente (documentado en replit.md)
- **Problema:** VETOs restan más puntos de los que max_score permite
- **Valores actuales:**
  - Black Swan HIGH: -30 puntos (pero max_score solo suma 15)
  - HMM VOLATILE: -15 puntos
  - Regime Change: -20 puntos
- **Impacto:** Sesgo hacia SELL cuando hay pocos datos
- **Solución propuesta:**
  - [ ] Normalizar VETOs proporcionales a max_score
  - [ ] O cap máximo de penalización = max_score actual

---

## 6. LSP Diagnostics

### 6.1 auto_trading_bot.py tiene 129 diagnostics
- **Prioridad:** 🟡 MED
- **Estado:** [ ] Pendiente
- **Archivo:** `omnix_core/bot/auto_trading_bot.py`
- **Acción:** Revisar con `get_latest_lsp_diagnostics` y corregir

---

## 7. Documentación Faltante

### 7.1 Información no sincronizada con replit.md
- **Prioridad:** 🟢 LOW
- **Estado:** [ ] Pendiente
- **Problema:** `replit.md` tiene secciones que no están en docs/core:
  - Current Performance (Dec 5, 2025)
  - Known Issues (Under Investigation)
  - DatabaseManager.log_risk_event fix
- **Solución:**
  - [ ] Sincronizar información relevante a Omnix_TECHNICAL_REFERENCE.md

---

## Orden de Ejecución Recomendado

1. **Fase A - Críticos (afectan funcionamiento):**
   - [x] 5.1 Volumes = None fix ✅
   - [x] 1.1 Migrar google-generativeai ✅ (Dec 5, 2025)

2. **Fase B - Arquitectura (mejora rendimiento):**
   - [ ] 2.1-2.2 Phase 4 Database Unification

3. **Fase C - Documentación (precisión):**
   - [ ] 1.2 Corregir error anthropic
   - [ ] 3.1 Documentar endpoints faltantes
   - [ ] 4.1-4.2 Actualizar line counts

4. **Fase D - Mejoras (opcional):**
   - [ ] 3.2 Consumir endpoints huérfanos
   - [ ] 5.2 Rebalancear VETOs
   - [ ] 6.1 Corregir LSP diagnostics

---

## Progreso

| Fase | Items | Completados | % |
|------|-------|-------------|---|
| A - Críticos | 2 | 2 | 100% |
| B - Arquitectura | 4 | 0 | 0% |
| C - Documentación | 4 | 0 | 0% |
| D - Mejoras | 3 | 0 | 0% |
| **TOTAL** | **13** | **2** | **15%** |

---

## Notas

- Este documento se elimina cuando todos los items estén marcados ✅
- Actualizar el % de progreso al completar cada item
- Commits relacionados deben referenciar este documento

---

*Última actualización: 5 de Diciembre, 2025*
