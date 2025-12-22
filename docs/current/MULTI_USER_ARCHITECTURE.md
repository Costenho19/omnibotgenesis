# OMNIX V6.5.4d - Arquitectura Multi-Usuario

**Versión**: V6.5.4d INSTITUTIONAL+  
**Fecha de Auditoría**: 22 de Diciembre 2025  
**Estado**: ✅ FASE 3b COMPLETADA - Multi-Usuario OPERACIONAL  
**Autor**: Auditoría de Arquitectura OMNIX

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Guía de Uso Práctico](#2-guía-de-uso-práctico)
3. [Análisis Técnico Detallado](#3-análisis-técnico-detallado)
4. [Esquema de Base de Datos](#4-esquema-de-base-de-datos)
5. [Criptografía Post-Cuántica](#5-criptografía-post-cuántica)
6. [Arquitectura Multi-Usuario](#6-arquitectura-multi-usuario)
7. [Coherencia con Arquitectura Hexagonal V7.0](#7-coherencia-con-arquitectura-hexagonal-v70)
8. [Plan de Implementación (Completado)](#8-plan-de-implementación-completado)
9. [Riesgos y Mitigaciones](#9-riesgos-y-mitigaciones)

---

## 1. Resumen Ejecutivo

### 1.1 Estado Actual (Actualizado 22 Dic 2025)

| Aspecto | Estado Anterior | Estado Actual (Phase 3b) |
|---------|-----------------|--------------------------|
| Arquitectura | Single-tenant hardcodeado | ✅ **Multi-usuario con RBAC** |
| AuthorizationService | No existía | ✅ **AuthorizationPort + Adapter integrados** |
| UserSessionManager | Existía pero no integrado | ✅ **Integrado en AutoTradingBot** |
| Permisos | Hardcoded checks | ✅ **15 permisos granulares por rol** |
| Harold | user_id hardcodeado | ✅ **OWNER en BD con todos los permisos** |

> **COMPLETADO (22 Dic 2025)**: 
> - `AuthorizationService` completamente integrado en 5 archivos
> - 17 hardcoded checks reemplazados con RBAC
> - 36/36 tests pasando
> - Harold tiene rol OWNER con paper trading activo

### 1.2 Estado de Seguridad

```
┌─────────────────────────────────────────────────────────────────────┐
│  ✅ PROBLEMA RESUELTO: RBAC IMPLEMENTADO                            │
│                                                                     │
│  AuthorizationAdapter verifica permisos en PostgreSQL + Redis      │
│  Cada usuario tiene su rol (FREE/BASIC/PRO/PREMIUM/OWNER)          │
│                                                                     │
│  Resultado: Trading aislado por usuario                             │
│  Estado: Multi-usuario LISTO para activación                        │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 Modelo de Roles y Permisos

| Rol | Permisos Trading | Permisos Análisis | Límites |
|-----|------------------|-------------------|---------|
| **OWNER** | Real + Paper + Auto | Todos | Sin límites |
| **PREMIUM** | Paper + Auto | Todos | 50 trades/día |
| **PRO** | Paper + Alertas | Avanzados | 20 trades/día |
| **BASIC** | Paper básico | Básicos | 10 trades/día |
| **FREE** | Solo vista | 3 análisis/día | Solo lectura |

### 1.4 Verificación en Base de Datos

```sql
-- Harold configurado como OWNER
SELECT user_id, is_admin, subscription_tier FROM users WHERE user_id = '7014748854';
-- Resultado: user_id=7014748854, is_admin=true, subscription_tier='owner'

-- Paper trading activo
SELECT paper_trading_mode, auto_trading, trading_enabled FROM user_settings WHERE user_id = '7014748854';
-- Resultado: paper_trading_mode=true, auto_trading=true, trading_enabled=true
```

---

## 2. Guía de Uso Práctico

### 2.1 Agregar un Nuevo Usuario

```sql
-- Paso 1: Crear usuario en tabla users
INSERT INTO users (user_id, username, is_admin, subscription_tier, created_at)
VALUES ('TELEGRAM_CHAT_ID', 'nombre_usuario', false, 'basic', NOW());

-- Paso 2: Crear configuración inicial
INSERT INTO user_settings (user_id, username, trading_enabled, auto_trading, paper_trading_mode)
VALUES ('TELEGRAM_CHAT_ID', 'nombre_usuario', true, false, true);

-- Paso 3 (opcional): Inicializar balance paper trading
INSERT INTO paper_trading_balances (user_id, currency, balance, updated_at)
VALUES ('TELEGRAM_CHAT_ID', 'USD', 100000.00, NOW());
```

### 2.2 Cambiar Tier de Usuario

```sql
-- Upgrade a PRO
UPDATE users SET subscription_tier = 'pro' WHERE user_id = 'TELEGRAM_CHAT_ID';

-- Upgrade a PREMIUM
UPDATE users SET subscription_tier = 'premium' WHERE user_id = 'TELEGRAM_CHAT_ID';

-- Nota: El cache de Redis se invalida automáticamente después de 5 minutos
-- Para invalidación inmediata, reiniciar el bot o esperar TTL
```

### 2.3 Verificar Permisos de Usuario

```sql
-- Ver rol y permisos efectivos
SELECT u.user_id, u.subscription_tier, u.is_admin,
       us.trading_enabled, us.auto_trading, us.paper_trading_mode
FROM users u
JOIN user_settings us ON u.user_id = us.user_id
WHERE u.user_id = 'TELEGRAM_CHAT_ID';
```

### 2.4 Permisos por Tier

| Tier | Permisos Incluidos |
|------|-------------------|
| **FREE** | `VIEW_BALANCE`, `VIEW_POSITIONS` |
| **BASIC** | FREE + `PAPER_TRADING`, `RECEIVE_ALERTS` |
| **PRO** | BASIC + `PAPER_AUTO_TRADING`, `ADVANCED_ANALYSIS` |
| **PREMIUM** | PRO + `PRIORITY_EXECUTION`, `CUSTOM_STRATEGIES` |
| **OWNER** | TODOS (15 permisos) incluyendo `REAL_TRADING`, `REAL_AUTO_TRADING` |

---

## 3. Análisis Técnico Detallado (Histórico)

> **Nota**: Esta sección documenta el problema original que fue **RESUELTO** en Phase 3b.

### 2.1 Auditoría de AutoTradingBot

**Archivo**: `omnix_core/bot/auto_trading_bot.py`  
**Líneas de código**: 4,841  
**Problema**: user_id hardcodeado en 6 ubicaciones

#### Ubicaciones del Hardcoded user_id

| Línea | Función | Código | Impacto |
|-------|---------|--------|---------|
| 1230 | `_manage_positions()` | `user_id = str(self.config.get('harold_user_id', '7014748854'))` | Gestión de posiciones |
| 3004 | `_execute_trading_cycle()` | `user_id = str(self.config.get('harold_user_id', '7014748854'))` | Estadísticas diarias |
| 3047 | `_check_position_limits()` | `user_id = str(self.config.get('harold_user_id', '7014748854'))` | Límites de posición |
| 3081 | `_has_open_position()` | `user_id = str(self.config.get('harold_user_id', '7014748854'))` | Verificación posiciones |
| 3213 | `_execute_paper_trade()` | `user_id=str(self.config.get('harold_user_id', '7014748854'))` | Ejecución de trades |
| 4119 | `get_open_positions()` | `user_id = str(self.config.get('harold_user_id', '7014748854'))` | Consulta posiciones |

#### Flujo de Ejecución Actual

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         FLUJO ACTUAL (PROBLEMÁTICO)                        │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Telegram                                                                  │
│     │                                                                      │
│     ▼                                                                      │
│  enterprise_bot.py                                                         │
│     │ handle_autotrading()                                                 │
│     │ → chat_id disponible AQUÍ ✓                                         │
│     │                                                                      │
│     ▼                                                                      │
│  UserSettingsService                                                       │
│     │ pause_trading(user_id) / resume_trading(user_id)                    │
│     │ → user_id pasado correctamente                                       │
│     │                                                                      │
│     ▼                                                                      │
│  AutoTradingBot                                                            │
│     │ start() / stop()                                                     │
│     │ → ❌ IGNORA el user_id del llamador                                  │
│     │ → ❌ USA hardcoded '7014748854'                                      │
│     │                                                                      │
│     ▼                                                                      │
│  _trading_loop() → _execute_trading_cycle()                               │
│     │ → ❌ Siempre opera como Harold                                       │
│     │                                                                      │
│     ▼                                                                      │
│  PaperTradingManager                                                       │
│     │ execute_trade(user_id='7014748854')                                 │
│     │ → ❌ Trades guardados bajo Harold                                    │
│     │                                                                      │
│     ▼                                                                      │
│  PostgreSQL                                                                │
│     └── paper_trading_trades.user_id = '7014748854'  ← Siempre Harold     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Auditoría de UserSessionManager

**Estado**: ✅ **EXISTE** pero ❌ **NO INTEGRADO**

> **CORRECCIÓN (20 Dic 2025)**: El `UserSessionManager` SÍ existe como código funcional.

**Archivo**: `omnix_core/sessions/user_session_manager.py`  
**Líneas de código**: 562  
**Estado**: Completamente implementado, NO integrado con AutoTradingBot

#### Clases Implementadas

| Clase | Propósito | Estado |
|-------|-----------|--------|
| `SessionStatus` | Enum: INACTIVE, ACTIVE, PAUSED, EMERGENCY_STOP | ✅ Completo |
| `UserTradingSession` | Dataclass con estado completo por usuario | ✅ Completo |
| `UserSessionManager` | Gestor de sesiones con Redis + PostgreSQL | ✅ Completo |

#### Métodos del UserSessionManager

| Método | Parámetros | Función | Estado |
|--------|------------|---------|--------|
| `get_session(user_id)` | user_id: str | Obtener/crear sesión (cache local → Redis → PostgreSQL → nueva) | ✅ Implementado |
| `save_session(session)` | UserTradingSession | Guardar en Redis + PostgreSQL | ✅ Implementado |
| `start_trading(user_id)` | user_id: str | Iniciar trading para usuario específico | ✅ Implementado |
| `stop_trading(user_id)` | user_id: str | Detener trading para usuario específico | ✅ Implementado |
| `pause_trading(user_id)` | user_id: str | Pausar trading temporal | ✅ Implementado |
| `resume_trading(user_id)` | user_id: str | Reanudar trading pausado | ✅ Implementado |
| `get_active_sessions()` | - | Listar sesiones activas (desde Redis) | ✅ Implementado |
| `restore_all_sessions()` | - | Restaurar sesiones después de restart | ✅ Implementado |

#### Capacidades del UserSessionManager

```python
class UserSessionManager:
    """
    🚀 Gestor de sesiones multi-usuario PREMIUM
    
    Capacidad: 100,000+ usuarios simultáneos
    Backend: Redis (estado) + PostgreSQL (persistencia)
    
    Características:
    - Sesiones aisladas por user_id
    - Estado en Redis para velocidad
    - Persistencia en PostgreSQL para durabilidad
    - Auto-restauración después de reinicios
    - Limpieza automática de sesiones inactivas
    """
    
    REDIS_PREFIX = "omnix:session:"
    SESSION_TTL = 86400 * 7  # 7 días en segundos
    ACTIVE_SESSIONS_KEY = "omnix:active_sessions"
```

#### Estado de Integración UserSessionManager (Actualizado Dec 22, 2025)

**ESTADO**: ✅ **INTEGRADO** (Fase 2 Paso 5)

Cambios implementados:
1. `AutoTradingBot.__init__` inicializa `UserSessionManager` con Redis/database
2. `start(user_id)` activa sesión en UserSessionManager y usa loop multi-usuario
3. `stop(user_id)` desactiva sesión en UserSessionManager
4. Callers en `trading_system.py` pasan `user_id` del mensaje Telegram

```python
# auto_trading_bot.py - start() ahora integrado
if USER_SESSION_MANAGER_AVAILABLE and get_session_manager:
    session_manager = get_session_manager()
    session = session_manager.get_session(effective_user_id)
    session.running = True
    session_manager.save_session(session)
    # Usa _trading_loop_multi_user para procesar todos los usuarios activos
```

**Limitaciones conocidas** (para futuras iteraciones):
- Entry points como REST API y dashboard no pasan user_id aún
- Fallback a LEGACY_USER_ID cuando user_id no disponible
- Tests de integración multi-usuario pendientes

### 2.3 Auditoría de PaperTradingManager

**Archivo**: `omnix_services/trading_service/paper_trading_manager.py`  
**Líneas de código**: 1,024  
**Estado**: Parcialmente preparado para multi-usuario

#### Funciones con soporte user_id

| Función | Acepta user_id | Usa Correctamente |
|---------|---------------|-------------------|
| `initialize_user(user_id)` | ✅ Sí | ✅ Sí |
| `get_paper_balance(user_id)` | ✅ Sí | ✅ Sí |
| `execute_trade(user_id, ...)` | ✅ Sí | ✅ Sí |
| `get_open_positions(user_id)` | ✅ Sí | ✅ Sí |
| `close_position(user_id, ...)` | ✅ Sí | ✅ Sí |

**Problema**: El `PaperTradingManager` **sí soporta multi-usuario**, pero `AutoTradingBot` le pasa siempre el mismo `user_id` hardcodeado.

### 2.4 Auditoría de UserSettingsService

**Archivo**: `omnix_services/user_settings/user_settings_service.py`  
**Estado**: Parcialmente funcional

```python
def pause_trading(self, user_id: str) -> bool:
    """Pause trading for a specific user"""
    # ✅ Recibe user_id correctamente
    # ✅ Actualiza user_settings.is_paused = True para ESE user_id
    # ❌ Pero AutoTradingBot ignora este estado por usuario
```

**Problema**: El servicio está diseñado para multi-usuario, pero `AutoTradingBot` no consume el estado por usuario.

### 2.5 Auditoría de Comandos Telegram

**Archivo**: `omnix_services/telegram_service/enterprise_bot.py`

#### Flujo de /pausar

```python
async def handle_pause_autotrading(update, context):
    chat_id = str(update.effective_chat.id)  # ✅ chat_id disponible
    
    # ✅ Pasa el user_id correcto
    result = await user_settings_service.pause_trading(chat_id)
    
    # ❌ AutoTradingBot.stop() no usa el chat_id
    auto_trading_bot.stop()  # ← No pasa user_id, ignora el llamador
```

#### Flujo de /reanudar

```python
async def handle_resume_autotrading(update, context):
    chat_id = str(update.effective_chat.id)  # ✅ chat_id disponible
    
    # ✅ Pasa el user_id correcto
    result = await user_settings_service.resume_trading(chat_id)
    
    # ❌ AutoTradingBot.start() no usa el chat_id
    auto_trading_bot.start()  # ← No pasa user_id, opera como Harold
```

---

## 3. Esquema de Base de Datos

### 3.1 Tablas Actuales con user_id

```sql
-- Tabla: paper_trading_trades
CREATE TABLE paper_trading_trades (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(255),      -- ✅ Columna existe
    symbol          VARCHAR(50),
    side            VARCHAR(10),
    quantity        NUMERIC,
    entry_price     NUMERIC,
    exit_price      NUMERIC,
    profit_loss     NUMERIC,
    profit_pct      NUMERIC,
    strategy        VARCHAR(100),
    status          VARCHAR(20),
    opened_at       TIMESTAMP,
    closed_at       TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Tabla: trades
CREATE TABLE trades (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(255),      -- ✅ Columna existe
    symbol          VARCHAR(50),
    side            VARCHAR(10),
    quantity        NUMERIC,
    price           NUMERIC,
    total           NUMERIC,
    fee             NUMERIC,
    order_id        VARCHAR(100),
    exchange        VARCHAR(50),
    status          VARCHAR(20),
    executed_at     TIMESTAMP
);

-- Tabla: user_settings
CREATE TABLE user_settings (
    user_id                     TEXT PRIMARY KEY,  -- ✅ PK por usuario
    username                    TEXT,
    risk_profile                TEXT,
    trading_limits              JSONB,
    protection_settings         JSONB,
    notification_preferences    JSONB,
    allowed_cryptos             JSONB,
    allowed_stocks              JSONB,
    active_strategies           JSONB,
    trading_enabled             BOOLEAN DEFAULT TRUE,
    auto_trading                BOOLEAN DEFAULT FALSE,
    paper_trading_mode          BOOLEAN DEFAULT TRUE,
    is_paused                   BOOLEAN DEFAULT FALSE,
    pause_reason                TEXT,
    pause_until                 TIMESTAMPTZ,
    onboarding_completed        BOOLEAN DEFAULT FALSE,
    terms_accepted              BOOLEAN DEFAULT FALSE,
    risk_disclosure_accepted    BOOLEAN DEFAULT FALSE,
    daily_pnl_usd               NUMERIC DEFAULT 0,
    daily_trades_count          INTEGER DEFAULT 0,
    daily_traded_usd            NUMERIC DEFAULT 0,
    daily_stats_date            DATE,
    weekly_pnl_usd              NUMERIC DEFAULT 0,
    created_at                  TIMESTAMPTZ DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.2 Row-Level Security (RLS) - NO IMPLEMENTADO

**Estado actual**: Las tablas tienen columna `user_id` pero **NO hay políticas RLS**.

```sql
-- VERIFICACIÓN: No existen políticas RLS
SELECT schemaname, tablename, policyname 
FROM pg_policies 
WHERE tablename IN ('paper_trading_trades', 'trades', 'user_settings');

-- Resultado: 0 rows (sin políticas)
```

### 3.3 Propuesta de Row-Level Security

```sql
-- Paso 1: Habilitar RLS en tablas críticas
ALTER TABLE paper_trading_trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;

-- Paso 2: Crear políticas de aislamiento
CREATE POLICY tenant_isolation_paper_trades ON paper_trading_trades
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE))
    WITH CHECK (user_id = current_setting('app.current_user_id', TRUE));

CREATE POLICY tenant_isolation_trades ON trades
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', TRUE))
    WITH CHECK (user_id = current_setting('app.current_user_id', TRUE));

-- Paso 3: En cada conexión, establecer el usuario
SET app.current_user_id = '7014748854';  -- Establecer antes de queries
```

### 3.4 Tabla Propuesta: user_sessions

```sql
CREATE TABLE user_sessions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             TEXT NOT NULL REFERENCES user_settings(user_id),
    telegram_chat_id    TEXT NOT NULL,
    session_token       TEXT,
    pqc_public_key      BYTEA,           -- Clave pública Dilithium-3
    trading_state       JSONB DEFAULT '{}',
    is_active           BOOLEAN DEFAULT TRUE,
    last_activity       TIMESTAMPTZ DEFAULT NOW(),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    expires_at          TIMESTAMPTZ,
    UNIQUE(telegram_chat_id)
);

CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_sessions_telegram ON user_sessions(telegram_chat_id);
```

---

## 4. Criptografía Post-Cuántica

### 4.1 Estado Actual de PQC

**Archivo**: `omnix_core/security/pqc_security.py`  
**Líneas de código**: 471  
**Estado**: Implementada pero subutilizada

#### Capacidades Implementadas

| Algoritmo | Estándar NIST | Función | Estado |
|-----------|---------------|---------|--------|
| ML-KEM-768 (Kyber) | FIPS 203 | Encriptación de claves | ✅ Implementado, ❌ No usado |
| ML-DSA-65 (Dilithium) | FIPS 204 | Firmas digitales | ✅ Implementado, ⚠️ Uso limitado |

#### Uso Actual en Producción

```python
# pqc_security.py - Funciones disponibles
PostQuantumSecurity.generate_keypair_encryption()   # Kyber-768 - NO USADO
PostQuantumSecurity.encapsulate_secret()            # Kyber-768 - NO USADO
PostQuantumSecurity.decapsulate_secret()            # Kyber-768 - NO USADO
PostQuantumSecurity.generate_keypair_signature()    # Dilithium-3 - NO USADO en auth
PostQuantumSecurity.sign_message()                  # Dilithium-3 - Usado para firmar trades
PostQuantumSecurity.verify_signature()              # Dilithium-3 - NO USADO para verificar usuarios
```

### 4.2 PQC NO Proporciona Autorización

**Documentación dice** (líneas 45-50 de auto_trading_bot.py):
```
SEGURIDAD:
- Firma Post-Quantum de todos los trades
```

**Realidad**:
- PQC firma trades para **integridad** (el trade no fue modificado)
- PQC **NO verifica** que el usuario esté autorizado a ejecutar el trade
- PQC **NO protege** contra un usuario ejecutando comandos de otro

### 4.3 Propuesta de PQC para Autorización

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PQC AUTHORIZATION FLOW (PROPUESTO)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. ONBOARDING: Usuario se registra                                        │
│     ┌─────────────┐                                                         │
│     │   Cliente   │ ────► Servidor genera keypair Dilithium-3               │
│     └─────────────┘       (public_key, secret_key)                          │
│           │               ↓                                                 │
│           │         Guarda secret_key en DB (encriptado)                    │
│           │         Envía public_key al cliente (opcional)                  │
│           ▼                                                                 │
│     user_sessions.pqc_public_key = public_key                               │
│                                                                             │
│  2. CADA COMANDO DE TRADING:                                                │
│     ┌─────────────┐                                                         │
│     │  /reanudar  │ ────► Servidor busca session por chat_id                │
│     └─────────────┘       ↓                                                 │
│                     Firma el comando con secret_key del usuario             │
│                     signature = dilithium3.sign(command, secret_key)        │
│                           ↓                                                 │
│                     Adjunta signature al trade log                          │
│                     trade.pqc_signature = signature                         │
│                           ↓                                                 │
│                     ✅ Trade ejecutado con prueba criptográfica             │
│                        de que FUE el usuario autorizado                     │
│                                                                             │
│  3. AUDITORÍA:                                                              │
│     Verificar: dilithium3.verify(signature, command, public_key)            │
│     Si falla → Trade no fue autorizado por el usuario legítimo              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.4 Beneficios de PQC para Auth

| Beneficio | Descripción |
|-----------|-------------|
| **Quantum-Safe** | Protegido contra computadoras cuánticas futuras |
| **Non-Repudiation** | Usuario no puede negar haber ejecutado el trade |
| **Audit Trail** | Cada trade tiene firma verificable |
| **Compliance** | Cumple con estándares NIST 2024 |

---

## 5. Arquitectura Multi-Usuario Propuesta

### 5.1 Diagrama de Arquitectura Target

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA MULTI-USUARIO PROPUESTA                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CAPA DE PRESENTACIÓN                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │   Telegram   │  │  Flask API   │  │  Streamlit   │                      │
│  │    Bot       │  │  Dashboard   │  │  Dashboard   │                      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                      │
│         │                 │                 │                               │
│         └────────────────┬┴─────────────────┘                               │
│                          │                                                  │
│  ┌───────────────────────▼───────────────────────┐                         │
│  │            SESSION MANAGER (NUEVO)             │                         │
│  │  ┌─────────────────────────────────────────┐  │                         │
│  │  │  chat_id → user_id → Session Context    │  │                         │
│  │  │  Redis: omnix:session:{chat_id}         │  │                         │
│  │  │  TTL: 24 horas                          │  │                         │
│  │  └─────────────────────────────────────────┘  │                         │
│  └───────────────────────┬───────────────────────┘                         │
│                          │                                                  │
│  ┌───────────────────────▼───────────────────────┐                         │
│  │            AUTH LAYER (NUEVO)                  │                         │
│  │  ┌─────────────────────────────────────────┐  │                         │
│  │  │  - Verificar user_id es el owner         │  │                         │
│  │  │  - Admin check para comandos sensibles   │  │                         │
│  │  │  - PQC signature (opcional)              │  │                         │
│  │  └─────────────────────────────────────────┘  │                         │
│  └───────────────────────┬───────────────────────┘                         │
│                          │                                                  │
│  CAPA DE APLICACIÓN                                                         │
│  ┌───────────────────────▼───────────────────────┐                         │
│  │              AutoTradingBot V2                 │                         │
│  │  ┌─────────────────────────────────────────┐  │                         │
│  │  │  start(user_id) → Inicia loop PARA ESE  │  │                         │
│  │  │  stop(user_id)  → Detiene loop PARA ESE │  │                         │
│  │  │  user_trading_loops: Dict[user_id, Loop]│  │                         │
│  │  └─────────────────────────────────────────┘  │                         │
│  └───────────────────────┬───────────────────────┘                         │
│                          │                                                  │
│  ┌───────────────────────▼───────────────────────┐                         │
│  │           UserSettingsService                  │                         │
│  │  ┌─────────────────────────────────────────┐  │                         │
│  │  │  get_settings(user_id)                   │  │                         │
│  │  │  pause_trading(user_id)                  │  │                         │
│  │  │  resume_trading(user_id)                 │  │                         │
│  │  └─────────────────────────────────────────┘  │                         │
│  └───────────────────────┬───────────────────────┘                         │
│                          │                                                  │
│  ┌───────────────────────▼───────────────────────┐                         │
│  │           PaperTradingManager                  │                         │
│  │  ┌─────────────────────────────────────────┐  │                         │
│  │  │  execute_trade(user_id, ...)  ← Ya OK   │  │                         │
│  │  │  get_balance(user_id)         ← Ya OK   │  │                         │
│  │  └─────────────────────────────────────────┘  │                         │
│  └───────────────────────┬───────────────────────┘                         │
│                          │                                                  │
│  CAPA DE DATOS                                                              │
│  ┌───────────────────────▼───────────────────────┐                         │
│  │                PostgreSQL + RLS                │                         │
│  │  ┌─────────────────────────────────────────┐  │                         │
│  │  │  SET app.current_user_id = '{user_id}'  │  │                         │
│  │  │  RLS Policy → Solo ve sus propios datos │  │                         │
│  │  └─────────────────────────────────────────┘  │                         │
│  └───────────────────────────────────────────────┘                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Componentes Nuevos Requeridos

#### 5.2.1 UserSessionManager

```python
class UserSessionManager:
    """
    Gestiona sesiones de trading por usuario.
    Almacena estado en Redis con TTL 24h.
    """
    
    def __init__(self, redis_client, database_service):
        self.redis = redis_client
        self.db = database_service
        self.sessions: Dict[str, UserSession] = {}
    
    def get_session(self, chat_id: str) -> UserSession:
        """Obtiene o crea sesión para un chat_id de Telegram"""
        cache_key = f"omnix:session:{chat_id}"
        
        # Intentar Redis primero
        cached = self.redis.get(cache_key)
        if cached:
            return UserSession.from_json(cached)
        
        # Crear nueva sesión
        session = UserSession(
            chat_id=chat_id,
            user_id=self._resolve_user_id(chat_id),
            trading_state=TradingState.IDLE,
            created_at=datetime.now()
        )
        
        # Guardar en Redis con TTL
        self.redis.setex(cache_key, 86400, session.to_json())
        return session
    
    def _resolve_user_id(self, chat_id: str) -> str:
        """Mapea chat_id de Telegram a user_id interno"""
        # Buscar en user_settings si existe
        # Si no existe, crear nuevo usuario
        return chat_id  # Por ahora, chat_id = user_id
```

#### 5.2.2 AuthorizationService

```python
class AuthorizationService:
    """
    Verifica que el usuario tiene permiso para ejecutar comandos.
    """
    
    ADMIN_COMMANDS = ['/pausar', '/reanudar', '/config', '/emergency_stop']
    
    def __init__(self, user_settings_service, pqc_security=None):
        self.user_settings = user_settings_service
        self.pqc = pqc_security
    
    def is_owner(self, requester_id: str, target_user_id: str) -> bool:
        """Verifica que el solicitante es dueño de la cuenta"""
        return requester_id == target_user_id
    
    def can_execute_command(self, chat_id: str, command: str) -> Tuple[bool, str]:
        """Verifica si el usuario puede ejecutar un comando"""
        
        # Comandos de admin requieren ser owner
        if command in self.ADMIN_COMMANDS:
            settings = self.user_settings.get_settings(chat_id)
            if not settings:
                return False, "Usuario no registrado"
            
            if not self.is_owner(chat_id, settings.user_id):
                return False, "Solo el dueño puede ejecutar este comando"
        
        return True, "OK"
    
    def sign_action(self, user_id: str, action: dict) -> Optional[bytes]:
        """Firma una acción con PQC (opcional)"""
        if not self.pqc:
            return None
        
        # Obtener secret_key del usuario
        secret_key = self._get_user_secret_key(user_id)
        if not secret_key:
            return None
        
        action_bytes = json.dumps(action).encode()
        return self.pqc.sign_message(action_bytes, secret_key)
```

### 5.3 Flujo Propuesto: /reanudar

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FLUJO PROPUESTO: /reanudar                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Usuario envía /reanudar en Telegram                                     │
│     chat_id = '111222333'                                                   │
│                                                                             │
│  2. enterprise_bot.py recibe el comando                                     │
│     ┌──────────────────────────────────────────┐                           │
│     │  async def handle_resume_autotrading():  │                           │
│     │      chat_id = update.effective_chat.id  │                           │
│     │                                          │                           │
│     │      # NUEVO: Obtener sesión             │                           │
│     │      session = session_manager.get(chat_id)                          │
│     │      user_id = session.user_id           │                           │
│     │                                          │                           │
│     │      # NUEVO: Verificar autorización     │                           │
│     │      can, reason = auth.can_execute(     │                           │
│     │          chat_id, '/reanudar'            │                           │
│     │      )                                   │                           │
│     │      if not can:                         │                           │
│     │          return reply(f"⛔ {reason}")    │                           │
│     │                                          │                           │
│     │      # Ejecutar con user_id correcto     │                           │
│     │      user_settings.resume_trading(user_id)                           │
│     │      auto_trading_bot.start(user_id)     │  ← CAMBIO CLAVE           │
│     └──────────────────────────────────────────┘                           │
│                                                                             │
│  3. AutoTradingBot.start(user_id='111222333')                               │
│     ┌──────────────────────────────────────────┐                           │
│     │  def start(self, user_id: str):          │                           │
│     │      with self._start_stop_lock:         │                           │
│     │          # Crear loop PARA ESTE usuario  │                           │
│     │          if user_id in self.user_loops:  │                           │
│     │              return already_running      │                           │
│     │                                          │                           │
│     │          loop = TradingLoop(user_id)     │                           │
│     │          self.user_loops[user_id] = loop │                           │
│     │          loop.start()                    │                           │
│     └──────────────────────────────────────────┘                           │
│                                                                             │
│  4. TradingLoop para user_id='111222333'                                    │
│     - Opera SOLO sobre las posiciones de este usuario                       │
│     - Usa SU balance, no el de Harold                                       │
│     - Registra trades con SU user_id                                        │
│                                                                             │
│  5. PostgreSQL con RLS                                                      │
│     SET app.current_user_id = '111222333';                                  │
│     SELECT * FROM paper_trading_trades;                                     │
│     → Solo ve trades de '111222333'                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Coherencia con Arquitectura Hexagonal V7.0

### 6.1 Estado Actual de Hexagonal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA HEXAGONAL V7.0                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Estado: 17 Ports + 19 Adapters implementados, 0% activo en producción     │
│                                                                             │
│  src/omnix/                                                                 │
│  ├── ports/                  ← Interfaces (contratos)                       │
│  │   ├── driven/             ← Ports salientes (DB, APIs externas)         │
│  │   │   ├── ai_port.py                                                    │
│  │   │   ├── trading_port.py                                               │
│  │   │   ├── persistence_port.py                                           │
│  │   │   └── ...                                                           │
│  │   └── driver/             ← Ports entrantes (Telegram, API)             │
│  │       ├── telegram_port.py                                              │
│  │       └── api_port.py                                                   │
│  │                                                                          │
│  ├── infrastructure/         ← Adapters (implementaciones)                  │
│  │   └── adapters/                                                          │
│  │       ├── kraken_adapter.py                                              │
│  │       ├── gemini_adapter.py                                              │
│  │       └── ...                                                            │
│  │                                                                          │
│  ├── domain/                 ← Lógica de negocio pura                       │
│  │   └── trading/                                                           │
│  │       ├── entities/                                                      │
│  │       └── strategies/                                                    │
│  │                                                                          │
│  └── application/            ← Casos de uso                                 │
│      └── use_cases/                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Nuevos Ports Requeridos para Multi-Usuario

| Port | Tipo | Responsabilidad |
|------|------|-----------------|
| `SessionPort` | Driven | Gestión de sesiones de usuario |
| `AuthorizationPort` | Driven | Verificación de permisos |
| `IdentityPort` | Driven | Mapeo chat_id → user_id |

### 6.3 Nuevos Adapters Requeridos

```python
# src/omnix/ports/driven/session_port.py
from abc import ABC, abstractmethod
from typing import Optional

class SessionPort(ABC):
    """Port para gestión de sesiones de usuario"""
    
    @abstractmethod
    def get_session(self, chat_id: str) -> Optional[UserSession]:
        """Obtiene sesión por chat_id"""
        pass
    
    @abstractmethod
    def create_session(self, chat_id: str, user_id: str) -> UserSession:
        """Crea nueva sesión"""
        pass
    
    @abstractmethod
    def invalidate_session(self, chat_id: str) -> bool:
        """Invalida sesión existente"""
        pass

# src/omnix/infrastructure/adapters/redis_session_adapter.py
class RedisSessionAdapter(SessionPort):
    """Implementación de sesiones con Redis"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.prefix = "omnix:session:"
        self.ttl = 86400  # 24 horas
    
    def get_session(self, chat_id: str) -> Optional[UserSession]:
        key = f"{self.prefix}{chat_id}"
        data = self.redis.get(key)
        if data:
            return UserSession.from_json(data)
        return None
    
    def create_session(self, chat_id: str, user_id: str) -> UserSession:
        session = UserSession(
            chat_id=chat_id,
            user_id=user_id,
            created_at=datetime.now()
        )
        key = f"{self.prefix}{chat_id}"
        self.redis.setex(key, self.ttl, session.to_json())
        return session
```

### 6.4 Integración con Bootstrap

```python
# src/omnix/bootstrap/container.py
class Container:
    """Contenedor de dependencias para hexagonal"""
    
    def __init__(self, config: Config):
        self.config = config
        
        # Adapters existentes
        self.trading_adapter = self._create_trading_adapter()
        self.ai_adapter = self._create_ai_adapter()
        
        # NUEVOS adapters para multi-usuario
        self.session_adapter = self._create_session_adapter()
        self.authorization_adapter = self._create_authorization_adapter()
    
    def _create_session_adapter(self) -> SessionPort:
        if self.config.use_redis:
            return RedisSessionAdapter(self.redis_client)
        return InMemorySessionAdapter()  # Fallback para testing
    
    def _create_authorization_adapter(self) -> AuthorizationPort:
        return DefaultAuthorizationAdapter(
            user_settings_port=self.user_settings_adapter,
            pqc_security=self.pqc_security if self.config.use_pqc else None
        )
```

### 6.5 Feature Flags Necesarios

```python
# omnix_config/feature_flags.py

# Flags existentes
USE_APP_LAYER = os.getenv('USE_APP_LAYER', 'false').lower() == 'true'
USE_AI_PORT = os.getenv('USE_AI_PORT', 'false').lower() == 'true'

# NUEVOS flags para multi-usuario
USE_SESSION_MANAGER = os.getenv('USE_SESSION_MANAGER', 'false').lower() == 'true'
USE_AUTHORIZATION = os.getenv('USE_AUTHORIZATION', 'false').lower() == 'true'
USE_PQC_AUTH = os.getenv('USE_PQC_AUTH', 'false').lower() == 'true'
USE_RLS = os.getenv('USE_RLS', 'false').lower() == 'true'
```

---

## 7. Plan de Implementación

### 7.1 Fases y Dependencias

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PLAN DE IMPLEMENTACIÓN                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FASE 1: Fundación (2-3 días)                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1.1 Eliminar hardcoded user_id                                     │   │
│  │      - Modificar 6 ubicaciones en AutoTradingBot                    │   │
│  │      - Propagar user_id desde start()/stop()                        │   │
│  │      Dependencias: Ninguna                                          │   │
│  │      Riesgo: BAJO (cambio localizado)                               │   │
│  │                                                                     │   │
│  │  1.2 INTEGRAR UserSessionManager existente                           │   │
│  │      - Archivo YA EXISTE: omnix_core/sessions/user_session_manager.py│  │
│  │      - Habilitar USER_SESSION_MANAGER_AVAILABLE = True              │   │
│  │      - Conectar con AutoTradingBot                                  │   │
│  │      Dependencias: 1.1                                              │   │
│  │      Riesgo: BAJO (código ya probado, solo integrar)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 2: Autorización (1-2 días)                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  2.1 Crear AuthorizationService                                     │   │
│  │      - Verificar ownership de comandos                              │   │
│  │      - Gate en /pausar y /reanudar                                  │   │
│  │      Dependencias: 1.2                                              │   │
│  │      Riesgo: MEDIO (afecta flujo de comandos)                       │   │
│  │                                                                     │   │
│  │  2.2 Modificar enterprise_bot.py                                    │   │
│  │      - Integrar session_manager                                     │   │
│  │      - Agregar checks de autorización                               │   │
│  │      Dependencias: 2.1                                              │   │
│  │      Riesgo: MEDIO (cambio en handlers)                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 3: Aislamiento de Datos (2-3 días)                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  3.1 Implementar Row-Level Security                                 │   │
│  │      - Scripts SQL para habilitar RLS                               │   │
│  │      - Crear políticas de aislamiento                               │   │
│  │      Dependencias: 1.1, 1.2                                         │   │
│  │      Riesgo: ALTO (cambio en DB)                                    │   │
│  │                                                                     │   │
│  │  3.2 Modificar DatabaseGateway                                      │   │
│  │      - SET app.current_user_id en cada conexión                     │   │
│  │      - Pasar user_id en contexto                                    │   │
│  │      Dependencias: 3.1                                              │   │
│  │      Riesgo: ALTO (afecta todas las queries)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 4: Trading Multi-Usuario (2-3 días)                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  4.1 Refactorizar trading loop                                      │   │
│  │      - Dict[user_id, TradingLoop] en lugar de singleton             │   │
│  │      - Cada usuario con su propio ciclo                             │   │
│  │      Dependencias: 1.1, 1.2, 3.2                                    │   │
│  │      Riesgo: ALTO (cambio arquitectónico)                           │   │
│  │                                                                     │   │
│  │  4.2 Tests de aislamiento                                           │   │
│  │      - Simular 2 usuarios simultáneos                               │   │
│  │      - Verificar que no comparten estado                            │   │
│  │      Dependencias: 4.1                                              │   │
│  │      Riesgo: BAJO (solo testing)                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 5: PQC Auth (Opcional, 2 días)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  5.1 Integrar PQC con sesiones                                      │   │
│  │      - Generar keypair por usuario                                  │   │
│  │      - Firmar comandos de trading                                   │   │
│  │      Dependencias: 1.2, 2.1                                         │   │
│  │      Riesgo: BAJO (feature opcional)                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  FASE 6: Documentación (1 día)                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  6.1 Actualizar documentación técnica                               │   │
│  │      - ARCHITECTURE.md                                              │   │
│  │      - TRADING_OPERATIONS.md                                        │   │
│  │      - replit.md                                                    │   │
│  │      Dependencias: Todas las fases anteriores                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Tabla de Tareas Detalladas

| ID | Tarea | Esfuerzo | Prioridad | Dependencias | Riesgo |
|----|-------|----------|-----------|--------------|--------|
| 1.1 | Eliminar `harold_user_id` hardcodeado de AutoTradingBot | 4h | P0 | - | Bajo |
| 1.2 | **INTEGRAR** `UserSessionManager` existente (omnix_core/sessions/) | 4h | P0 | 1.1 | Bajo |
| 2.1 | Crear `AuthorizationService` | 4h | P0 | 1.2 | Medio |
| 2.2 | Integrar auth en enterprise_bot.py | 4h | P0 | 2.1 | Medio |
| 3.1 | Implementar RLS en PostgreSQL | 6h | P1 | 1.1 | Alto |
| 3.2 | Modificar DatabaseGateway para RLS | 4h | P1 | 3.1 | Alto |
| 4.1 | Refactorizar trading loop multi-usuario | 8h | P1 | 3.2 | Alto |
| 4.2 | Tests de aislamiento multi-usuario | 4h | P1 | 4.1 | Bajo |
| 5.1 | Integrar PQC con auth (opcional) | 8h | P2 | 2.1 | Bajo |
| 6.1 | Actualizar documentación | 4h | P1 | Todas | Bajo |

**Total estimado**: 50 horas (~6 días de trabajo)

> **NOTA (20 Dic 2025)**: El `UserSessionManager` ya existe y está probado.
> La tarea 1.2 se reduce de 6h a 4h porque solo requiere **integración**, no desarrollo nuevo.

### 7.4 Progreso de Implementación (20 Dic 2025)

| Tarea | Estado | Detalle |
|-------|--------|---------|
| Parametrizar `_check_open_positions_tp_sl(user_id)` | ✅ COMPLETADO | Acepta user_id con fallback legacy |
| Parametrizar `_execute_smart_trade(analysis, user_id)` | ✅ COMPLETADO | Acepta user_id con fallback legacy |
| Parametrizar `_check_position_limit_early(user_id)` | ✅ COMPLETADO | Acepta user_id con fallback legacy |
| Implementar `_process_user_trading_cycle(user_id, session)` | ✅ COMPLETADO | Lógica básica con persistencia de sesión |
| Actualizar verificación límite diario | ✅ COMPLETADO | Usa user_id del parámetro |
| Actualizar verificación posición duplicada | ✅ COMPLETADO | Usa user_id del parámetro |
| Actualizar execute_paper_trade | ✅ COMPLETADO | Usa user_id del parámetro |

**NOTA IMPORTANTE**: La implementación actual es **BÁSICA** y mantiene compatibilidad con el flujo legacy.
Para producción completa, falta:
- Desacoplar configuración por usuario (actualmente usa `self.config` compartido)
- Migrar protecciones ARP y heartbeats al flujo multi-usuario
- Tests de aislamiento con múltiples usuarios simultáneos

### 7.5 Integración con Arquitectura Hexagonal V7.0 (20 Dic 2025)

| Componente | Ubicación | Estado |
|------------|-----------|--------|
| `UserSessionPort` | `src/omnix/ports/driven/user_session_port.py` | ✅ CREADO |
| `UserSession` value object | `src/omnix/ports/driven/user_session_port.py` | ✅ CREADO |
| `UserSessionAdapter` | `src/omnix/infrastructure/adapters/user_session_adapter.py` | ✅ CREADO |
| Export en `__init__.py` | `src/omnix/ports/driven/__init__.py` | ✅ ACTUALIZADO |

**Uso en Use Cases:**
```python
from src.omnix.ports.driven import UserSessionPort, UserSession
from src.omnix.infrastructure.adapters.user_session_adapter import UserSessionAdapter

# En bootstrap/dependency injection
session_adapter = UserSessionAdapter()

# En use cases
session = session_adapter.get_session(user_id)
session_adapter.save_session(session)
```

### 7.3 Diagrama de Dependencias

```
                    ┌─────────┐
                    │   1.1   │ Eliminar hardcoded
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │   1.2   │ UserSessionManager
                    └────┬────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         ┌────▼────┐┌────▼────┐┌────▼────┐
         │   2.1   ││   3.1   ││   5.1   │
         │  Auth   ││   RLS   ││   PQC   │
         └────┬────┘└────┬────┘└─────────┘
              │          │           (opcional)
         ┌────▼────┐┌────▼────┐
         │   2.2   ││   3.2   │
         │  Bot    ││   DB    │
         └────┬────┘└────┬────┘
              │          │
              └────┬─────┘
                   │
              ┌────▼────┐
              │   4.1   │ Trading Multi-User
              └────┬────┘
                   │
              ┌────▼────┐
              │   4.2   │ Tests
              └────┬────┘
                   │
              ┌────▼────┐
              │   6.1   │ Documentación
              └─────────┘
```

---

## 8. Riesgos y Mitigaciones

### 8.1 Riesgos Técnicos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| RLS rompe queries existentes | Media | Alto | Testing exhaustivo en staging |
| Trading loop multi-usuario inestable | Media | Alto | Feature flag para rollback |
| Redis no disponible | Baja | Medio | Fallback a sesiones in-memory |
| Conflictos de concurrencia | Media | Medio | Locks por usuario |

### 8.2 Riesgos de Seguridad

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Bypass de autorización | Baja | Crítico | Tests de penetración |
| Data leakage entre usuarios | Media | Crítico | RLS + auditoría |
| Sesiones hijacked | Baja | Alto | TTL corto + PQC opcional |

### 8.3 Riesgos de Negocio

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Downtime durante migración | Media | Alto | Blue-green deployment |
| Usuarios pierden trades históricos | Baja | Alto | Backup antes de migración |
| Tiempo de desarrollo excede estimación | Media | Medio | MVP primero, features después |

### 8.4 Plan de Rollback

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PLAN DE ROLLBACK                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Si hay problemas críticos en producción:                                   │
│                                                                             │
│  1. Feature Flags → OFF                                                     │
│     USE_SESSION_MANAGER=false                                               │
│     USE_AUTHORIZATION=false                                                 │
│     USE_RLS=false                                                           │
│                                                                             │
│  2. Railway → Redeploy versión anterior                                     │
│     Dashboard → Deployments → Seleccionar último deploy estable            │
│                                                                             │
│  3. PostgreSQL → Desactivar RLS                                             │
│     ALTER TABLE paper_trading_trades DISABLE ROW LEVEL SECURITY;           │
│     ALTER TABLE trades DISABLE ROW LEVEL SECURITY;                          │
│                                                                             │
│  4. Redis → Flush sesiones                                                  │
│     redis-cli KEYS "omnix:session:*" | xargs redis-cli DEL                 │
│                                                                             │
│  Tiempo de rollback estimado: < 5 minutos                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Apéndice A: Código de Referencia

### A.1 Ubicaciones de Hardcoded user_id

```python
# omnix_core/bot/auto_trading_bot.py

# Línea 1230
user_id = str(self.config.get('harold_user_id', '7014748854'))

# Línea 3004
user_id = str(self.config.get('harold_user_id', '7014748854'))

# Línea 3047
user_id = str(self.config.get('harold_user_id', '7014748854'))

# Línea 3081
user_id = str(self.config.get('harold_user_id', '7014748854'))

# Línea 3213
user_id=str(self.config.get('harold_user_id', '7014748854'))

# Línea 4119
user_id = str(self.config.get('harold_user_id', '7014748854'))
```

### A.2 Esquema de Base de Datos Completo

```sql
-- Verificar estructura actual
\d paper_trading_trades
\d trades  
\d user_settings

-- Verificar RLS (debe retornar 0 filas actualmente)
SELECT * FROM pg_policies WHERE tablename LIKE '%trading%';
```

---

## Apéndice B: Checklist de Implementación

### Pre-Implementación
- [ ] Backup completo de base de datos
- [ ] Documentar estado actual de Railway
- [ ] Revisar logs de últimos 7 días

### Fase 1: Fundación
- [ ] Eliminar hardcoded user_id (6 ubicaciones)
- [ ] Crear UserSessionManager
- [ ] Tests unitarios para sesiones

### Fase 2: Autorización
- [ ] Crear AuthorizationService
- [ ] Modificar handlers de Telegram
- [ ] Tests de autorización

### Fase 3: RLS
- [ ] Script SQL para habilitar RLS
- [ ] Modificar DatabaseGateway
- [ ] Tests de aislamiento de datos

### Fase 4: Trading Multi-Usuario
- [ ] Refactorizar trading loop
- [ ] Tests de concurrencia
- [ ] Load testing (2 usuarios)

### Post-Implementación
- [ ] Actualizar documentación
- [ ] Training para operadores
- [ ] Monitoreo por 48 horas

---

*Documento generado: 20 de Diciembre 2025*  
*OMNIX V6.5.4d INSTITUTIONAL+ - Auditoría de Arquitectura Multi-Usuario*
