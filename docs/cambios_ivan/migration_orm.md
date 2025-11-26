# PLAN DE MIGRACIÓN: SQL Puro → SQLModel + Alembic + Flask API

**Proyecto**: OMNIX V6.0 ULTRA  
**Fecha Inicio**: 26 de Noviembre de 2025  
**Objetivo**: Migrar de psycopg2 (SQL puro) a SQLModel + Alembic con capa Flask API REST  
**Prioridad**: **ZERO DOWNTIME** - Sistema debe seguir funcionando en todo momento  

---

## 📋 ÍNDICE

1. [Visión General](#visión-general)
2. [Arquitectura Objetivo](#arquitectura-objetivo)
3. [FASE 0: Baseline Alembic](#fase-0-baseline-alembic)
4. [FASE 1: SQLModel Models](#fase-1-sqlmodel-models)
5. [FASE 2: Repository Layer](#fase-2-repository-layer)
6. [FASE 3: Adapter Pattern (Dual-Run)](#fase-3-adapter-pattern-dual-run)
7. [FASE 4: Flask API Layer](#fase-4-flask-api-layer)
8. [FASE 5: Migración Secuencial por Módulos](#fase-5-migración-secuencial-por-módulos)
9. [FASE 6: Production Validation](#fase-6-production-validation)
10. [FASE 7: Cleanup & Deprecation](#fase-7-cleanup--deprecation)
11. [Estrategia de Rollback](#estrategia-de-rollback)
12. [Testing Strategy](#testing-strategy)
13. [Checklist Final](#checklist-final)

---

## 📦 CHANGELOG DE VERSIONES 2025

**Última Actualización**: 26 de Noviembre de 2025  
**Todas las versiones han sido actualizadas a las releases más recientes de 2025**

### Tabla Comparativa de Versiones

| Paquete | Versión Original | Versión 2025 | Cambio | Notas Importantes |
|---------|-----------------|--------------|--------|-------------------|
| **sqlmodel** | 0.0.22 | **0.0.27** | ⬆️ +0.0.5 | ✨ Soporte UUID nativo, cascade delete relationships, SQLAlchemy ≥2.0.14 |
| **alembic** | 1.14.0 | **1.17.2** | ⬆️ +0.3.2 | ✨ PEP 621 (pyproject.toml), 🔴 **Python ≥3.10 requerido** |
| **asyncpg** | 0.29.0 | **0.30.0** | ⬆️ +0.1.0 | ✨ Soporte PostgreSQL 17, Python ≥3.8 |
| **pydantic** | 2.10.0 | **2.12.4** | ⬆️ +0.2.4 | ✨ Versión estable más reciente, Python ≥3.9, 360M+ downloads/mes |
| **pydantic-settings** | 2.6.0 | **2.12.0** | ⬆️ +0.6.0 | ✨ Integración AWS/Azure/GCP secrets, 🔴 **Python ≥3.10 requerido** |
| **greenlet** | 3.0.0 | **3.2.4** | ⬆️ +0.2.4 | ✨ Fixes Python 3.12+, soporte Musllinux wheels |
| **flask-limiter** | 3.8.0 | **4.0.0** | ⬆️ +0.2.0 | 🔴 **Breaking: Python ≥3.10 requerido**, dropped 3.8/3.9 support |
| **flask-cors** | 5.0.0 | **6.0.1** | ⬆️ +1.0.1 | 🔒 **Security fixes** (CVE-2024-6839, CVE-2024-6844, CVE-2024-6866) |
| **pyjwt** | 2.8.0 | **2.10.1** | ⬆️ +0.2.1 | 🔒 Mejoras de seguridad (CVE-2025-45768), Python ≥3.9 |
| **pytest-asyncio** | 0.23.0 | **1.3.0** | ⬆️ +1.0.7 | 🔴 **Breaking: Python ≥3.10, depreca `event_loop` fixture** |

### ⚠️ Breaking Changes Críticos

**Requisito de Python actualizado a ≥3.10**:
- ❌ **Python 3.8 y 3.9 ya NO son compatibles** con:
  - Flask-Limiter 4.0.0 (requiere Python ≥3.10)
  - pytest-asyncio 1.3.0 (requiere Python ≥3.10)
  - Alembic 1.17.2 (requiere Python ≥3.10)
  - pydantic-settings 2.12.0 (requiere Python ≥3.10)

**Cambios en APIs**:
- `pytest-asyncio 1.3.0`: Eliminó fixture `event_loop` (usar `event_loop_policy` o scoped loops)
- `SQLModel 0.0.27`: Cambios en cascade delete syntax (ver docs)

### ✅ Beneficios de las Actualizaciones 2025

#### SQLModel 0.0.27
- ✨ **UUID support nativo** con SQLAlchemy 2.0 types
- ✨ **Cascade delete relationships**: `cascade_delete`, `ondelete`, `passive_deletes`
- ✨ Fix para `EmailStr` y `max_length` con Pydantic v2
- ✨ Mínimo SQLAlchemy 2.0.14 (mejoras de performance)

#### Alembic 1.17.2
- ✨ **PEP 621 support**: Configuración en `pyproject.toml` en lugar de `alembic.ini`
- ✨ **Custom commands API**: `CommandLine.register_command()` para CLI custom
- ✨ Fix rendering de foreign keys en autogenerate
- ✨ Deprecado `utcnow()` reemplazado con `now(UTC)`

#### Flask-CORS 6.0.1
- 🔒 **Security patches críticos**:
  - CVE-2024-6839: CORS bypass vulnerability
  - CVE-2024-6844: Improper header validation
  - CVE-2024-6866: Cross-origin resource sharing bypass
- **IMPORTANTE**: Actualización obligatoria para producción

#### Pydantic-Settings 2.12.0
- ✨ **Cloud secrets integration**: AWS Secrets Manager, Azure Key Vault, GCP Secret Manager
- ✨ Soporte para TOML y YAML configs
- ✨ Mejor validación de environment variables

#### PyJWT 2.10.1
- 🔒 **Security improvements**: Validación de minimum key length (CVE-2025-45768)
- ✨ Mejor soporte para JWS detached payloads
- ✨ `PyJWKSet` con `__getitem__` support

#### pytest-asyncio 1.3.0
- ✨ **Scoped loops**: Loops creados una vez por scope (más rápido)
- ✨ **Auto mode**: `asyncio_mode = auto` en pytest.ini (no más decorators)
- ✨ Runtime dependency en `backports.asyncio.runner` para Python ≤3.10

### 📋 Requisitos Mínimos del Sistema

| Componente | Versión Mínima | Recomendada |
|-----------|---------------|-------------|
| **Python** | 3.10 | 3.12+ |
| **PostgreSQL** | 12.0 | 15.0+ |
| **Redis** | 6.0 | 7.0+ |
| **pip** | 21.0+ | 24.0+ |

---

## 🎯 VISIÓN GENERAL

### Estado Actual (Baseline)
```
omnix_services/database_service/
└── database_service.py (2,360 líneas)
    ├── SQL puro con psycopg2
    ├── 23 tablas manuales
    ├── 22 métodos DAL
    ├── 3 migraciones manuales idempotentes
    └── Sistema TTL cleanup automático
```

**Problemas Identificados**:
- ❌ No hay ORM (type safety débil, riesgo de errores)
- ❌ Migraciones manuales (error-prone, no versionadas)
- ❌ SQL concatenado (riesgo potencial de injection)
- ❌ No hay API REST (inversores no pueden consultar datos)
- ❌ Testing difícil (no hay mocks, tests acoplados a DB)
- ❌ No async-ready (limitado para escalar)

### Arquitectura Objetivo

**Stack Tecnológico Final** (Versiones 2025):
- **ORM**: SQLModel 0.0.27 (Pydantic + SQLAlchemy ≥2.0.14)
- **Migrations**: Alembic 1.17.2 (auto-generated, versionadas con PEP 621)
- **Database Driver**: asyncpg 0.30.0 (async PostgreSQL, soporte PG 17)
- **API**: Flask 3.0.0+ (REST API para inversores)
- **Auth**: PyJWT 2.10.1 (JWT authentication con security fixes)
- **Validation**: Pydantic 2.12.4 (schemas I/O, 360M+ downloads/mes)
- **Rate Limiting**: Flask-Limiter 4.0.0 (Redis-backed, Python ≥3.10)
- **CORS**: Flask-CORS 6.0.1 (security patches CVE-2024-*)
- **Settings**: pydantic-settings 2.12.0 (cloud secrets support)
- **Async Runtime**: greenlet 3.2.4 (Python 3.12+ compatible)
- **Testing**: pytest-asyncio 1.3.0 (auto mode, scoped loops)

**Estructura de Archivos Objetivo**:
```
omnix_services/database_service/
│
├── core/
│   ├── config.py              # Pydantic Settings (DATABASE_URL, etc)
│   ├── database.py            # Async engine + session factory
│   └── base.py                # Base models (UUIDModel, TimestampModel)
│
├── models/                    # SQLModel models (23 tablas)
│   ├── __init__.py
│   ├── user.py                # users, user_contacts
│   ├── trading.py             # trades, analysis, balance_history
│   ├── paper_trading.py       # paper_trading_balances, paper_trading_trades
│   ├── conversation.py        # conversations, trade_reasonings, etc
│   ├── community.py           # community_feedback, strategy_votes, etc
│   ├── signal.py              # community_signals, signal_executions, etc
│   └── risk_guardian.py       # risk_guardian_events
│
├── repositories/              # Data Access Layer (reemplaza DAL actual)
│   ├── base_repo.py           # Generic CRUD (create, get, update, delete)
│   ├── user_repo.py
│   ├── trade_repo.py
│   ├── community_repo.py
│   ├── signal_repo.py
│   └── ...
│
├── schemas/                   # Pydantic schemas (API I/O validation)
│   ├── user_schema.py
│   ├── trade_schema.py
│   └── ...
│
├── api/                       # Flask REST API (NUEVO)
│   ├── __init__.py
│   ├── v1/
│   │   ├── users.py           # GET /api/v1/users/{user_id}
│   │   ├── trades.py          # GET /api/v1/trades/recent
│   │   ├── signals.py         # GET /api/v1/signals/leaderboard
│   │   └── stats.py           # GET /api/v1/stats/performance
│   ├── auth.py                # JWT authentication
│   ├── middleware.py          # Rate limiting, CORS
│   └── docs.py                # OpenAPI/Swagger
│
├── migrations/                # Alembic (auto-generadas)
│   ├── versions/
│   │   └── 001_baseline.py
│   ├── env.py
│   └── script.py.mako
│
├── tests/                     # Testing completo
│   ├── test_schema_parity.py
│   ├── test_repositories.py
│   ├── test_api_endpoints.py
│   └── fixtures.py
│
├── database_service.py        # 🔌 ADAPTER (API pública backward compatible)
├── alembic.ini
└── README.md
```

**Beneficios Esperados**:
- ✅ Type safety completo (Pydantic + SQLAlchemy)
- ✅ Migraciones automáticas versionadas (Alembic)
- ✅ Testing 10x más fácil (mocks de repositories)
- ✅ API REST para inversores/dashboard
- ✅ Async ready (escalable a 1000+ req/s)
- ✅ Menos bugs (validación automática en models + schemas)
- ✅ Mejor mantenibilidad (separation of concerns)

---

## 🏗️ ARQUITECTURA OBJETIVO DETALLADA

### Flujo de Datos

```
┌─────────────────┐
│  Telegram Bot   │ (interfaz principal)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   database_service.py (Adapter)    │
│   - Dual-run: psycopg2 + SQLModel  │ (FASE 3-5)
│   - Feature flags por módulo       │
│   - Logging de discrepancias        │
└────────┬─────────────┬──────────────┘
         │             │
         ▼             ▼
┌────────────┐  ┌──────────────┐
│ psycopg2   │  │ SQLModel     │
│ (Legacy)   │  │ Repositories │
│ TEMPORAL   │  │ (Nuevo)      │
└────────────┘  └──────┬───────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Flask API REST │ (FASE 4)
              │  /api/v1/*      │
              └─────────────────┘
                       │
                       ▼
                ┌──────────────┐
                │  Inversores  │
                │  (Dashboard) │
                └──────────────┘
```

### Dependencias Nuevas a Instalar

```bash
# requirements.txt (agregar estas líneas - VERSIONES 2025)
# IMPORTANTE: Requiere Python >=3.10

# Core ORM & Migrations
sqlmodel==0.0.27          # UUID support, cascade delete, SQLAlchemy 2.0.14+
alembic==1.17.2           # PEP 621 (pyproject.toml), Python >=3.10
asyncpg==0.30.0           # PostgreSQL 17 support

# Validation & Settings
pydantic==2.12.4          # Latest stable, 360M+ downloads/month
pydantic-settings==2.12.0 # AWS/Azure/GCP secrets, Python >=3.10

# Flask API & Security
flask-limiter==4.0.0      # Rate limiting, Python >=3.10 REQUIRED
flask-cors==6.0.1         # SECURITY FIXES (CVE-2024-6839, 6844, 6866)
pyjwt==2.10.1             # JWT auth, security improvements

# Async Runtime & Testing
greenlet==3.2.4           # Python 3.12+ fixes
pytest-asyncio==1.3.0     # Auto mode, scoped loops, Python >=3.10
```

---

## 📦 FASE 0: BASELINE ALEMBIC

**Objetivo**: Crear baseline migration desde schema actual sin modificar nada  
**Duración Estimada**: 1 día  
**Criterio de Éxito**: Alembic detecta 23 tablas, diff = 0 cambios  
**Riesgo**: Bajo  

### PASO 0.1: Instalación de Dependencias

#### Pre-requisito: Verificar Python ≥3.10
```bash
python --version
# DEBE mostrar Python 3.10.x o superior
# Si es Python 3.8 o 3.9, ACTUALIZAR primero
```

#### Acción
```bash
# VERSIONES 2025 - Requiere Python >=3.10
# Instalar paquetes core ORM
pip install sqlmodel==0.0.27 alembic==1.17.2 asyncpg==0.30.0 pydantic==2.12.4 pydantic-settings==2.12.0 greenlet==3.2.4

# Instalar Flask API + Security (con security fixes)
pip install flask-limiter==4.0.0 flask-cors==6.0.1 pyjwt==2.10.1

# Instalar testing (async)
pip install pytest-asyncio==1.3.0

# Verificar instalación y versiones
python -c "import sqlmodel; print(f'✅ SQLModel {sqlmodel.__version__}')"
python -c "import alembic; print(f'✅ Alembic {alembic.__version__}')"
python -c "import asyncpg; print(f'✅ asyncpg {asyncpg.__version__}')"
python -c "import pydantic; print(f'✅ Pydantic {pydantic.__version__}')"
python -c "import flask_cors; print(f'✅ Flask-CORS {flask_cors.__version__}')"
```

#### Comprobaciones Redundantes
- ✅ **CHECK 1**: Verificar Python ≥3.10 (obligatorio para Flask-Limiter 4.0.0)
- ✅ **CHECK 2**: Verificar que `sqlmodel` se importa sin errores
- ✅ **CHECK 3**: Verificar que `alembic` se importa sin errores
- ✅ **CHECK 4**: Verificar versiones exactas (SQLModel 0.0.27, Alembic 1.17.2, Flask-CORS 6.0.1)
- ✅ **CHECK 5**: Ejecutar `python main.py` y confirmar que el bot sigue funcionando
- ✅ **CHECK 6**: Revisar logs del workflow para confirmar 0 errores de import
- ✅ **CHECK 7**: Confirmar Flask-CORS 6.0.1 (security fixes CVE-2024-*)

#### Criterio de Aprobación
- Bot funciona normalmente ✅
- No hay errores en logs ✅
- Versiones correctas instaladas ✅

#### Rollback
Si algo falla:
```bash
pip uninstall sqlmodel alembic asyncpg -y
# Sistema sigue funcionando con psycopg2
```

---

### PASO 0.2: Inicializar Alembic

#### Acción
```bash
cd omnix_services/database_service/
alembic init -t async migrations
```

Esto crea:
```
migrations/
├── versions/        # Migraciones auto-generadas
├── env.py          # Config de Alembic
└── script.py.mako  # Template para migraciones
```

#### Comprobaciones Redundantes
- ✅ **CHECK 1**: Verificar que carpeta `migrations/` existe
- ✅ **CHECK 2**: Verificar que `migrations/env.py` existe
- ✅ **CHECK 3**: Verificar que `alembic.ini` fue creado
- ✅ **CHECK 4**: Ejecutar `alembic --help` sin errores

#### Rollback
Si algo falla:
```bash
rm -rf migrations/ alembic.ini
# Sistema sigue funcionando con psycopg2
```

---

### PASO 0.3: Configurar Alembic para PostgreSQL

#### Acción: Editar `alembic.ini`

**Cambio**:
```ini
# ANTES
sqlalchemy.url = driver://user:pass@localhost/dbname

# DESPUÉS (comentar línea, usar env var)
# sqlalchemy.url = driver://user:pass@localhost/dbname
```

#### Acción: Editar `migrations/env.py`

Ver archivo completo de referencia en sección "Apéndice A: migrations/env.py template"

**Cambios clave**:
1. Importar `DATABASE_URL` desde env
2. Configurar `async_engine_from_config`
3. Preparar `target_metadata` (será `SQLModel.metadata` en FASE 1)

#### Comprobaciones Redundantes
- ✅ **CHECK 1**: Verificar que `DATABASE_URL` se lee correctamente
  ```python
  python -c "import os; print(os.environ.get('DATABASE_URL')[:30])"
  ```
- ✅ **CHECK 2**: Ejecutar `alembic current` sin errores
  ```bash
  cd omnix_services/database_service/
  alembic current
  # Esperado: "(head)" o mensaje que no hay migraciones aún
  ```

#### Rollback
```bash
git checkout migrations/env.py alembic.ini
```

---

### PASO 0.4: Crear Baseline Migration (NO ejecutar)

**CRÍTICO**: Esta migration NO se ejecuta, solo se genera para verificar que Alembic detecta el schema actual.

#### Acción
```bash
cd omnix_services/database_service/
alembic revision --autogenerate -m "baseline_schema_actual"
```

Esto crea: `migrations/versions/001_baseline_schema_actual.py`

#### Comprobaciones Redundantes CRÍTICAS

**CHECK 1: Contar tablas detectadas**
```bash
grep "CREATE TABLE" migrations/versions/001_*.py | wc -l
# Esperado: 23 (número de tablas en database_service.py)
```

**CHECK 2: Verificar tablas críticas**
```bash
grep -E "(users|trades|community_signals|risk_guardian_events)" migrations/versions/001_*.py
# Esperado: deben aparecer las 4 tablas críticas
```

**CHECK 3: Verificar Foreign Keys**
```bash
grep "ForeignKeyConstraint" migrations/versions/001_*.py | wc -l
# Esperado: 13 (número de FKs documentadas)
```

**CHECK 4: Verificar CHECK Constraints**
```bash
grep "CheckConstraint" migrations/versions/001_*.py | wc -l
# Esperado: 6-7 (algunos pueden fallar en detección)
```

**CHECK 5: Verificar Índices**
```bash
grep "CREATE INDEX" migrations/versions/001_*.py | wc -l
# Esperado: ~43 (número de índices reales)
```

**CHECK FINAL: Validación Manual de Schema**

Crear checklist (ver sección "Apéndice B: Baseline Validation Checklist")

#### Criterio de Cancelación
Si Alembic detecta < 20 tablas o hay > 10 discrepancias en columnas/constraints:
- **STOP** ⛔
- Revisar configuración de `migrations/env.py`
- Verificar que `DATABASE_URL` apunta a BD correcta
- No proceder a FASE 1 hasta resolver

#### Rollback
```bash
# NO ejecutar la migration
rm migrations/versions/001_*.py
```

---

### Criterios de Aprobación FASE 0

| Criterio | Esperado | Estado |
|---------|----------|--------|
| Tablas detectadas | 23 | ✅ / ❌ |
| FK constraints | 13 | ✅ / ❌ |
| CHECK constraints | 6-7 | ✅ / ❌ |
| Índices | ≥43 | ✅ / ❌ |
| Bot funcionando | Sin errores | ✅ / ❌ |
| Alembic configurado | `alembic current` OK | ✅ / ❌ |

**SI TODOS LOS CHECKS PASAN** → Proceder a FASE 1  
**SI ALGÚN CHECK FALLA** → Rollback y revisar configuración

---

## 🏗️ FASE 1: SQLMODEL MODELS

**Objetivo**: Crear 23 SQLModel models replicando schema exacto  
**Duración Estimada**: 3-4 días  
**Criterio de Éxito**: `alembic revision --autogenerate` genera diff VACÍO (0 cambios)  
**Riesgo**: Medio  

### Visión General

Esta fase crea models SQLModel que replican EXACTAMENTE el schema actual de PostgreSQL. La validación crítica es que al final, Alembic NO detecte cambios (diff = 0).

### PASO 1.1: Crear Estructura Base

```bash
cd omnix_services/database_service/
mkdir -p core models schemas
touch core/__init__.py core/config.py core/database.py core/base.py
touch models/__init__.py
```

---

### PASO 1.2: Crear `core/config.py`

Ver sección "Apéndice C: core/config.py template"

**Comprobaciones**:
- ✅ Verficar que `DATABASE_URL` se carga correctamente
- ✅ Verificar validación Pydantic funciona

---

### PASO 1.3: Crear `core/database.py`

Ver sección "Apéndice D: core/database.py template"

**Comprobaciones**:
- ✅ Verificar que engine se crea sin errores
- ✅ Verificar URL transformation (postgresql:// → postgresql+asyncpg://)

---

### PASO 1.4: Crear `core/base.py`

Ver sección "Apéndice E: core/base.py template"

---

### PASO 1.5-1.11: Crear Models (23 tablas)

**Orden de creación recomendado**:

1. **PASO 1.5**: `models/user.py` (2 tablas: users, user_contacts)
2. **PASO 1.6**: `models/trading.py` (3 tablas: trades, analysis, balance_history)
3. **PASO 1.7**: `models/conversation.py` (3 tablas: conversations, whatsapp_messages, sharia_validations)
4. **PASO 1.8**: `models/paper_trading.py` (2 tablas: paper_trading_balances, paper_trading_trades)
5. **PASO 1.9**: `models/conversational_brain.py` (3 tablas: trade_reasonings, trade_evaluations, pending_evaluations)
6. **PASO 1.10**: `models/community.py` (5 tablas: community_feedback, strategy_votes, improvement_proposals, user_contributions, detected_patterns)
7. **PASO 1.11**: `models/signal.py` (4 tablas: community_signals, signal_executions, signal_votes, alpha_leaderboard)
8. **PASO 1.12**: `models/risk_guardian.py` (1 tabla: risk_guardian_events)

**Para CADA modelo, seguir este checklist**:

#### Checklist por Modelo

1. ✅ Comparar columnas línea por línea con `database_service.py`
2. ✅ Replicar tipos de datos exactos (TEXT, NUMERIC(18,8), TIMESTAMP, etc)
3. ✅ Replicar defaults (DEFAULT 0, DEFAULT true, DEFAULT CURRENT_TIMESTAMP)
4. ✅ Replicar CHECK constraints
5. ✅ Replicar índices (simples + compuestos)
6. ✅ Replicar Foreign Keys
7. ✅ Generar migration parcial: `alembic revision --autogenerate -m "add [tabla] model"`
8. ✅ Verificar que migration es VACÍA (no modifica BD)

**Ejemplo: User Model**

Ver sección "Apéndice F: models/user.py template"

---

### PASO 1.13: Crear `models/__init__.py`

Ver sección "Apéndice G: models/__init__.py template"

**Comprobaciones**:
- ✅ Verificar que todos los models se importan sin errores
- ✅ Contar models: debe haber 23

---

### PASO 1.14: Actualizar `migrations/env.py` con Metadata

```python
# migrations/env.py (agregar después de imports)

from omnix_services.database_service.models import *  # Importar todos los models
from sqlmodel import SQLModel

# Cambiar esto:
# target_metadata = None

# Por esto:
target_metadata = SQLModel.metadata
```

**Comprobaciones**:
- ✅ Verificar que metadata se carga: `python -c "from sqlmodel import SQLModel; print(len(SQLModel.metadata.tables))"`
  - Esperado: 23

---

### PASO 1.15: Generar Migration Completa y Validar Diff VACÍO

**CRÍTICO**: Este es el paso más importante de FASE 1

```bash
alembic revision --autogenerate -m "add all sqlmodel models"
```

**Comprobaciones Redundantes FINALES**:

**CHECK FINAL 1: Migration debe estar VACÍA**

Abrir `migrations/versions/00X_add_all_sqlmodel_models.py`:

```python
def upgrade() -> None:
    # Esperado: VACÍO o solo comentarios
    pass

def downgrade() -> None:
    # Esperado: VACÍO o solo comentarios
    pass
```

**Si hay contenido en `upgrade()`**, significa que SQLModel models difieren del schema PostgreSQL actual. Esto es **CRÍTICO**.

**CHECK FINAL 2: Schema Comparison Script**

```python
# scripts/compare_schemas.py
# Ver sección "Apéndice H: Schema Comparison Script"
```

```bash
python scripts/compare_schemas.py
# Esperado: "✅ Schema parity PERFECTO - 23 tablas coinciden"
```

**CHECK FINAL 3: Unit Tests de Models**

```bash
pytest tests/test_models.py -v
# Esperado: 100% pass
```

---

### Criterios de Aprobación FASE 1

| Criterio | Esperado | Estado |
|---------|----------|--------|
| Models creados | 23 | ✅ / ❌ |
| Alembic diff | VACÍO (0 cambios) | ✅ / ❌ |
| Schema comparison | 0 diferencias | ✅ / ❌ |
| Unit tests | 100% pass | ✅ / ❌ |
| Bot funcionando | Sin errores | ✅ / ❌ |

**SI TODOS LOS CHECKS PASAN** → Proceder a FASE 2  
**SI ALEMBIC DIFF NO ES VACÍO** → Revisar models hasta encontrar discrepancia exacta

---

## 🗂️ FASE 2: REPOSITORY LAYER

**Objetivo**: Crear repositories que repliquen EXACTAMENTE los 22 métodos DAL actuales  
**Duración Estimada**: 3-4 días  
**Criterio de Éxito**: Parity tests pasan 100% (psycopg2 DAL vs SQLModel Repository devuelven lo mismo)  
**Riesgo**: Medio-Alto  

### Visión General

Esta fase implementa el **Repository Pattern**, creando una capa de abstracción sobre SQLModel que replica la API actual de `database_service.py`.

**Objetivo clave**: Cada método DAL debe tener un método Repository equivalente que devuelva EXACTAMENTE los mismos datos.

### PASO 2.1: Crear BaseRepository

Ver sección "Apéndice I: repositories/base_repo.py template"

---

### PASO 2.2-2.7: Crear Repositories Específicos

**Orden recomendado**:

1. **PASO 2.2**: `repositories/user_repo.py` (UserRepository)
2. **PASO 2.3**: `repositories/trade_repo.py` (TradeRepository)
3. **PASO 2.4**: `repositories/community_repo.py` (CommunityRepository)
4. **PASO 2.5**: `repositories/signal_repo.py` (SignalRepository)
5. **PASO 2.6**: `repositories/paper_trading_repo.py` (PaperTradingRepository)
6. **PASO 2.7**: `repositories/conversation_repo.py` (ConversationRepository)
7. **PASO 2.8**: `repositories/risk_guardian_repo.py` (RiskGuardianRepository)

**Para CADA repository**:

#### Checklist por Repository

1. ✅ Listar TODOS los métodos DAL del dominio (ej: User tiene ~4 métodos)
2. ✅ Implementar método equivalente en Repository
3. ✅ Crear parity test por cada método
4. ✅ Verificar que parity test pasa (psycopg2 == SQLModel)
5. ✅ Benchmark performance (< +10% latency)

**Ejemplo: UserRepository**

Ver sección "Apéndice J: repositories/user_repo.py template"

---

### PASO 2.9: Parity Testing Exhaustivo

**Objetivo**: Verificar que CADA método DAL devuelve EXACTAMENTE lo mismo que su Repository equivalente.

**Matriz de Parity Tests** (ejemplo):

| Método DAL | Línea DB Service | Repository Método | Parity Test | Estado |
|-----------|-----------------|------------------|-------------|--------|
| get_or_create_user | ~1600 | UserRepository.get_or_create_user | test_get_or_create_user_parity | ✅ / ❌ |
| update_user_profit | ~1650 | UserRepository.update_user_profit | test_update_user_profit_parity | ✅ / ❌ |
| add_user_contact | ~290 | UserRepository.add_user_contact | test_add_user_contact_parity | ✅ / ❌ |
| ... (22 métodos totales) | | | | |

**Template de Parity Test**:

```python
# tests/test_user_repo_parity.py
@pytest.mark.asyncio
async def test_get_or_create_user_parity():
    """Verificar que psycopg2 y SQLModel devuelven lo mismo"""
    
    test_user_id = f"parity_test_{uuid.uuid4()}"
    
    # 1. Resultado psycopg2 DAL
    db_service = DatabaseServiceEnterprise()
    dal_result = db_service.get_or_create_user(
        user_id=test_user_id,
        username="test_user"
    )
    
    # 2. Resultado SQLModel Repository
    async with get_session() as session:
        repo = UserRepository(session)
        repo_result = await repo.get_or_create_user(
            user_id=test_user_id,
            username="test_user"
        )
    
    # 3. Comparar resultados campo por campo
    assert dal_result['user_id'] == repo_result['user_id']
    assert dal_result['username'] == repo_result['username']
    assert dal_result['total_trades'] == repo_result['total_trades']
    
    # Cleanup
    # ...
```

**Ejecutar todos los parity tests**:
```bash
pytest tests/test_*_repo_parity.py -v --tb=short
# Esperado: 22/22 passed (100%)
```

---

### PASO 2.10: Performance Benchmarking

```python
# tests/test_performance_parity.py
def test_performance_comparison():
    """Comparar latencia psycopg2 vs SQLModel"""
    
    # Benchmark psycopg2
    start = time.time()
    for i in range(1000):
        db.get_or_create_user(user_id=f"perf_{i}")
    psycopg2_time = time.time() - start
    
    # Benchmark SQLModel
    start = time.time()
    for i in range(1000):
        asyncio.run(repo.get_or_create_user(user_id=f"perf_{i}"))
    sqlmodel_time = time.time() - start
    
    diff_pct = ((sqlmodel_time - psycopg2_time) / psycopg2_time) * 100
    
    print(f"psycopg2: {psycopg2_time:.2f}s")
    print(f"SQLModel: {sqlmodel_time:.2f}s")
    print(f"Diff: {diff_pct:+.1f}%")
    
    # Tolerar hasta +10% overhead
    assert diff_pct < 10
```

---

### Criterios de Aprobación FASE 2

| Criterio | Esperado | Estado |
|---------|----------|--------|
| Repositories creados | 7 dominios | ✅ / ❌ |
| Métodos replicados | 22/22 | ✅ / ❌ |
| Parity tests | 100% pass | ✅ / ❌ |
| Performance diff | < +10% | ✅ / ❌ |
| Bot funcionando | Sin errores | ✅ / ❌ |

**SI TODOS LOS CHECKS PASAN** → Proceder a FASE 3  
**SI PARITY TESTS FALLAN** → Debuggear hasta que DAL y Repository devuelvan exactamente lo mismo

---

## 🔌 FASE 3: ADAPTER PATTERN (DUAL-RUN)

**Objetivo**: Modificar `database_service.py` para dual-run (psycopg2 + SQLModel simultáneo)  
**Duración Estimada**: 2 días  
**Criterio de Éxito**: Feature flags funcionan, dual-run logging captura discrepancias  
**Riesgo**: Alto (puede romper API existente)  

### Visión General

Esta fase es **crítica** porque transforma `database_service.py` en un **adapter** que puede usar psycopg2 O SQLModel según feature flags.

**Concepto clave**: Durante transición, ejecuta AMBOS (psycopg2 + SQLModel) y compara resultados en logs.

### PASO 3.1: Mover Código Actual a Legacy

```bash
# Crear carpeta legacy
mkdir -p omnix_services/database_service/legacy

# Copiar código actual
cp omnix_services/database_service/database_service.py \
   omnix_services/database_service/legacy/psycopg2_dal.py
```

**Editar `legacy/psycopg2_dal.py`**:
- Cambiar clase `DatabaseServiceEnterprise` → `LegacyPsycopg2DAL`
- Agregar docstring: "⚠️ DEPRECATED - Solo para migración"

**Comprobaciones**:
- ✅ `LegacyPsycopg2DAL` se puede importar sin errores
- ✅ Bot sigue funcionando con legacy

---

### PASO 3.2: Crear Adapter en `database_service.py`

Ver sección "Apéndice K: database_service.py adapter template"

**Concepto del Adapter**:

```python
class DatabaseServiceEnterprise:
    def get_or_create_user(self, user_id, ...):
        if self.use_sqlmodel:
            # Usar SQLModel Repository
            result = self._async_wrapper(
                self._get_or_create_user_sqlmodel(user_id, ...)
            )
            
            # Dual-run: comparar con legacy
            if self.dual_run:
                legacy_result = self.legacy_dal.get_or_create_user(user_id, ...)
                self._compare_results("get_or_create_user", legacy_result, result)
            
            return result
        else:
            # Usar legacy psycopg2
            return self.legacy_dal.get_or_create_user(user_id, ...)
```

**Comprobaciones CRÍTICAS**:

**CHECK 1: Feature Flag Switching**
```python
os.environ['USE_SQLMODEL'] = 'false'
db = DatabaseServiceEnterprise()
# Debe usar psycopg2

os.environ['USE_SQLMODEL'] = 'true'
db2 = DatabaseServiceEnterprise()
# Debe usar SQLModel
```

**CHECK 2: Dual-Run Logging**
```python
os.environ['USE_SQLMODEL'] = 'true'
os.environ['DUAL_RUN_LOGGING'] = 'true'

db = DatabaseServiceEnterprise()
result = db.get_or_create_user(user_id="dual_test")

# Revisar logs - debe aparecer:
# ✅ get_or_create_user: Results match
# O:
# ⚠️ get_or_create_user: Results DIFFER
```

**CHECK 3: Backward Compatibility**
```python
# Verificar que API pública no cambió
db = DatabaseServiceEnterprise()

assert hasattr(db, 'get_or_create_user')
assert hasattr(db, 'submit_trade')
assert hasattr(db, 'submit_community_feedback')
# ... (22 métodos totales)
```

**CHECK 4: Integration con Community Intelligence**
```python
# Verificar que módulos existentes siguen funcionando
from omnix_services.community_intelligence.feedback_manager import FeedbackManager

manager = FeedbackManager()
result = manager.submit_feedback(
    user_id="integration_test",
    strategy="ARES_V1",
    result="success"
)

assert result is not None
```

---

### Criterios de Aprobación FASE 3

| Criterio | Esperado | Estado |
|---------|----------|--------|
| Adapter creado | ✅ | ✅ / ❌ |
| Feature flags funcionan | Switch sin errores | ✅ / ❌ |
| Dual-run logging | Captura discrepancias | ✅ / ❌ |
| Backward compatibility | 100% API igual | ✅ / ❌ |
| Community modules | 6/6 funcionan | ✅ / ❌ |
| Bot funcionando | Sin errores | ✅ / ❌ |

**SI TODOS LOS CHECKS PASAN** → Proceder a FASE 4  
**SI ADAPTER ROMPE API** → Revisar signatures de métodos públicos

---

## 🌐 FASE 4: FLASK API LAYER

**Objetivo**: Crear REST API con Flask para exponer datos a inversores  
**Duración Estimada**: 4-5 días  
**Criterio de Éxito**: 10 endpoints funcionando, auth JWT, OpenAPI docs  
**Riesgo**: Bajo (no afecta bot existente)  

### Visión General

Esta fase agrega una **capa REST API** completamente nueva que NO afecta el bot de Telegram existente.

**Uso**: Dashboard para inversores, consultas de stats, visualización de trades.

#### 🔒 Nota de Seguridad Importante (2025)

**Flask-CORS 6.0.1 incluye parches de seguridad CRÍTICOS**:
- ✅ **CVE-2024-6839**: CORS bypass vulnerability (CRITICAL)
- ✅ **CVE-2024-6844**: Improper header validation (HIGH)
- ✅ **CVE-2024-6866**: Cross-origin resource sharing bypass (HIGH)

**OBLIGATORIO**: Usar Flask-CORS 6.0.1 o superior para producción. Versiones anteriores (≤5.0.0) tienen vulnerabilidades de seguridad críticas.

**Verificación**:
```bash
pip show flask-cors
# Version: 6.0.1 o superior REQUERIDO
```

### API Contract

**Base URL**: `/api/v1/`

| Endpoint | Método | Auth | Descripción | Rate Limit |
|---------|--------|------|------------|------------|
| `/health` | GET | No | Health check | 10/min |
| `/auth/login` | POST | No | Obtener JWT | 5/min |
| `/users/{user_id}` | GET | JWT | Datos usuario | 100/hour |
| `/users/{user_id}/stats` | GET | JWT | Stats trading | 100/hour |
| `/trades/recent` | GET | JWT | Últimos trades | 100/hour |
| `/trades/{trade_id}` | GET | JWT | Detalle trade | 100/hour |
| `/signals/leaderboard` | GET | JWT | Alpha leaderboard | 50/hour |
| `/signals/active` | GET | JWT | Señales activas | 50/hour |
| `/stats/performance` | GET | JWT | Performance global | 50/hour |
| `/stats/risk` | GET | JWT | Risk metrics | 50/hour |

**Autenticación**: JWT Bearer Token  
**Rate Limiting**: Redis-backed (Flask-Limiter)

---

### PASO 4.1: Estructura Flask

```bash
mkdir -p omnix_services/database_service/api/v1
touch omnix_services/database_service/api/__init__.py
touch omnix_services/database_service/api/v1/{__init__,users,trades,signals,stats}.py
touch omnix_services/database_service/api/{auth,middleware}.py
```

---

### PASO 4.2: Crear Flask App

Ver sección "Apéndice L: api/__init__.py template"

---

### PASO 4.3: Implementar JWT Auth

Ver sección "Apéndice M: api/auth.py template"

---

### PASO 4.4: Crear Pydantic Schemas

Ver sección "Apéndice N: schemas/user_schema.py template"

---

### PASO 4.5: Implementar Endpoints

Ver sección "Apéndice O: api/v1/users.py template"

---

### PASO 4.6: Testing de API

```python
# tests/test_api_endpoints.py
def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'ok'

def test_get_user_with_valid_token(client):
    token = generate_token(user_id="test_123", role="user")
    
    response = client.get(
        '/api/v1/users/test_123',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    assert response.json['user_id'] == 'test_123'

def test_unauthorized_access(client):
    """User A no puede ver datos de User B"""
    token = generate_token(user_id="user_A", role="user")
    
    response = client.get(
        '/api/v1/users/user_B',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 403
```

```bash
pytest tests/test_api_endpoints.py -v
# Esperado: 100% pass
```

---

### PASO 4.7: Configurar Workflow Flask

```python
# api_server.py (archivo nuevo en root)
from omnix_services.database_service.api import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
```

**Configurar en Replit**:
- Workflow name: "OMNIX API"
- Command: `python api_server.py`
- Port: 8000
- Output type: console

---

### PASO 4.8: OpenAPI Docs

Acceso: `https://your-replit-url.repl.co/api/docs`

---

### Criterios de Aprobación FASE 4

| Criterio | Esperado | Estado |
|---------|----------|--------|
| Flask app creada | ✅ | ✅ / ❌ |
| Endpoints funcionando | 10/10 | ✅ / ❌ |
| Auth JWT | Válido requerido | ✅ / ❌ |
| Rate limiting | Límites OK | ✅ / ❌ |
| API tests | 100% pass | ✅ / ❌ |
| Swagger docs | Accesible | ✅ / ❌ |

**SI TODOS LOS CHECKS PASAN** → Proceder a FASE 5  
**SI ALGÚN TEST FALLA** → Debuggear endpoint específico

---

## 🔄 FASE 5: MIGRACIÓN SECUENCIAL POR MÓDULOS

**Objetivo**: Migrar gradualmente de psycopg2 a SQLModel usando feature flags  
**Duración Estimada**: 2-3 semanas  
**Criterio de Éxito**: Cada módulo migrado pasa regression + load tests + 7 días monitoring  
**Riesgo**: Alto (puede causar bugs en producción)  

### Orden de Migración (Menor a Mayor Riesgo)

1. ✅ **community_feedback** (Bajo riesgo - logging simple)
2. ✅ **risk_guardian** (Bajo riesgo - eventos aislados)
3. ✅ **signal_contribution** (Medio riesgo - 4 tablas)
4. ⚠️ **conversation** (Medio riesgo - logging de trades)
5. ⚠️ **paper_trading** (Medio-Alto riesgo - tracking de balance)
6. ⚠️ **trades** (CRÍTICO - core del bot)
7. ❌ **users** (ÚLTIMO - afecta TODO el sistema)

---

### Template: Migración de un Módulo

**Ejemplo: community_feedback**

#### PASO 5.X.1: Activar Feature Flag
```python
# .env
USE_SQLMODEL_COMMUNITY_FEEDBACK=true
```

#### PASO 5.X.2: Modificar Adapter
```python
# database_service.py
def submit_community_feedback(self, user_id, strategy, result, confidence):
    use_sqlmodel_module = os.getenv('USE_SQLMODEL_COMMUNITY_FEEDBACK', 'false') == 'true'
    
    if use_sqlmodel_module:
        # SQLModel
        result = self._async_wrapper(...)
        
        # Dual-run
        if self.dual_run:
            legacy_result = self.legacy_dal.submit_community_feedback(...)
            self._compare_results("submit_community_feedback", legacy_result, result)
        
        return result
    else:
        # Legacy
        return self.legacy_dal.submit_community_feedback(...)
```

#### PASO 5.X.3: Regression Tests
```python
def test_module_psycopg2():
    os.environ['USE_SQLMODEL_COMMUNITY_FEEDBACK'] = 'false'
    # Test con psycopg2

def test_module_sqlmodel():
    os.environ['USE_SQLMODEL_COMMUNITY_FEEDBACK'] = 'true'
    # Test con SQLModel (MISMAS assertions)

def test_module_dual_run():
    # Ejecutar 100 veces, verificar 0 discrepancias
```

#### PASO 5.X.4: Load Testing
```python
def test_module_load():
    # Benchmark 1000 ops
    # Tolerancia: < +10% latency
```

#### PASO 5.X.5: Activar en Producción con Dual-Run
```python
# .env producción
USE_SQLMODEL_COMMUNITY_FEEDBACK=true
DUAL_RUN_LOGGING=true  # Mantener por 7 días
```

**Monitorear 7 días**:
- ✅ 0 discrepancias en logs
- ✅ Latency p95 < baseline +5%
- ✅ 0 errores SQLAlchemy
- ✅ Memory usage estable

#### PASO 5.X.6: Deprecar Legacy

Después de 7 días sin problemas:
```python
# .env
USE_SQLMODEL_COMMUNITY_FEEDBACK=true
DUAL_RUN_LOGGING=false  # Desactivar dual-run

# Comentar código legacy en adapter
```

---

### REPETIR PARA CADA MÓDULO

**Total**: 7 módulos × 7 días monitoring = ~7-8 semanas de migración gradual

---

### Criterios de Aprobación FASE 5

| Criterio | Esperado | Estado |
|---------|----------|--------|
| Módulos migrados | 7/7 | ✅ / ❌ |
| Regression tests | 100% pass (todos) | ✅ / ❌ |
| Load tests | < +10% latency | ✅ / ❌ |
| Dual-run monitoring | 0 discrepancias | ✅ / ❌ |
| Production stability | 7 días × 7 módulos | ✅ / ❌ |

**SI TODOS PASAN** → Proceder a FASE 6  
**SI ALGÚN MÓDULO FALLA** → Rollback inmediato

---

## ✅ FASE 6: PRODUCTION VALIDATION

**Objetivo**: Validar sistema 100% SQLModel en producción  
**Duración**: 1-2 semanas  
**Criterio de Éxito**: 99.9% uptime, 0 errores críticos  
**Riesgo**: Medio  

### PASO 6.1: Load Testing

```python
def test_concurrent_users():
    """100 usuarios concurrentes"""
    # Debe completar en < 30s
```

### PASO 6.2: Monitoring Setup

- Configurar Sentry
- Métricas: error rate, latency, memory, DB connections

### PASO 6.3: TTL Cleanup Validation

Verificar que cleanup automático funciona con SQLModel.

---

### Criterios de Aprobación FASE 6

| Criterio | Esperado | Estado |
|---------|----------|--------|
| Load test | 100 concurrent OK | ✅ / ❌ |
| Uptime | 99.9% (2 semanas) | ✅ / ❌ |
| Error rate | < 0.1% | ✅ / ❌ |
| Latency p95 | < baseline +5% | ✅ / ❌ |

**SI TODOS PASAN** → Proceder a FASE 7  

---

## 🗑️ FASE 7: CLEANUP & DEPRECATION

**Objetivo**: Eliminar código psycopg2 completamente  
**Duración**: 1 día  
**Criterio de Éxito**: 100% SQLModel, 0% legacy  
**Riesgo**: Bajo  

### PASO 7.1: Eliminar Legacy

```bash
rm -rf omnix_services/database_service/legacy/
```

### PASO 7.2: Limpiar Feature Flags

Remover todos los `if use_sqlmodel:` del adapter.

### PASO 7.3: Actualizar Documentación

```markdown
# database.md
✅ SQLModel 0.0.27+ (UUID support, cascade delete, SQLAlchemy 2.0.14+)
✅ Alembic 1.17.2+ (PEP 621, auto-migrations, Python ≥3.10)
✅ Flask-CORS 6.0.1+ (Security fixes CVE-2024-*)
❌ psycopg2 (DEPRECATED Nov 2025 - Migrado a SQLModel)
```

---

### Criterios de Aprobación FASE 7

| Criterio | Esperado | Estado |
|---------|----------|--------|
| Legacy eliminado | 0 archivos | ✅ / ❌ |
| Feature flags eliminados | 100% SQLModel | ✅ / ❌ |
| Docs actualizadas | ✅ | ✅ / ❌ |

**SI TODOS PASAN** → **MIGRACIÓN COMPLETADA** 🎉

---

## 🔄 ESTRATEGIA DE ROLLBACK

| Fase | Rollback | Tiempo |
|------|----------|--------|
| FASE 0 | `rm -rf migrations/` | 5 min |
| FASE 1 | No ejecutar migrations | 0 min |
| FASE 2 | `rm -rf repositories/` | 10 min |
| FASE 3 | `git checkout database_service.py` | 30 min |
| FASE 4 | `rm -rf api/` | 5 min |
| FASE 5 | Feature flag `=false` | Instantáneo |
| FASE 6-7 | Restaurar legacy/ | 1-2 horas |

---

## 🧪 TESTING STRATEGY

### Niveles de Testing

1. **Unit Tests**: Models, Repositories, Endpoints (100% coverage)
2. **Integration Tests**: DB + Repos, API + DB
3. **Parity Tests**: psycopg2 vs SQLModel (byte-a-byte)
4. **Load Tests**: 100+ concurrent, 1000+ sequential
5. **E2E Tests**: Bot completo, API completa

### Coverage Targets

| Componente | Coverage |
|-----------|----------|
| Models | 100% |
| Repositories | 95% |
| API | 90% |
| Adapter | 85% |

---

## ✅ CHECKLIST FINAL

### Pre-Migration
- [ ] Backup PostgreSQL completo
- [ ] Git tag: `v6.0-pre-orm-migration`
- [ ] Documentar schema actual (database.md actualizado)

### FASE 0
- [ ] SQLModel instalado
- [ ] Alembic configurado
- [ ] Baseline migration generada (23 tablas)

### FASE 1
- [ ] 23 models creados
- [ ] Alembic diff = 0

### FASE 2
- [ ] 22 métodos DAL replicados
- [ ] Parity tests 100%

### FASE 3
- [ ] Adapter funcionando
- [ ] Dual-run logging OK

### FASE 4
- [ ] 10 endpoints implementados
- [ ] Auth JWT OK

### FASE 5
- [ ] 7 módulos migrados
- [ ] 49 días monitoring (7×7)

### FASE 6
- [ ] Load test OK
- [ ] 99.9% uptime

### FASE 7
- [ ] Legacy eliminado
- [ ] 100% SQLModel

---

## 📚 RECURSOS

- [SQLModel Docs](https://sqlmodel.tiangolo.com/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Flask Docs](https://flask.palletsprojects.com/)
- [Pydantic V2](https://docs.pydantic.dev/latest/)

---

## 🎯 RESUMEN EJECUTIVO

**Tiempo Total**: 8-10 semanas  
**Beneficios**:
- ✅ Type safety (Pydantic + SQLAlchemy)
- ✅ Migraciones automáticas
- ✅ Testing 10x más fácil
- ✅ API REST para inversores
- ✅ Async ready

**Riesgos Mitigados**:
- ⚠️ Zero downtime (dual-run)
- ⚠️ Rollback rápido (< 30 min)
- ⚠️ Validación exhaustiva (parity tests)

---

**FIN DEL PLAN - Ready for Implementation**

**Versión**: 1.0  
**Fecha**: 26 de Noviembre de 2025  
**Estado**: Aprobado por Architect
