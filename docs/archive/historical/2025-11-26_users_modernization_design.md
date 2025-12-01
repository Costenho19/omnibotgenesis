# Modernización de Tablas de Usuario - Diseño
**Fecha**: Nov 26, 2025  
**Autor**: Iván (con asistencia de Architect Agent)  
**Objetivo**: Mejorar consistencia y normalización de tablas relacionadas con usuarios

## 🎯 Problema Identificado

### Tabla `users` (Actual)
```sql
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,              -- ❌ TEXT no es ideal para PK
    username TEXT,
    first_name TEXT,
    language_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_trades INTEGER DEFAULT 0,
    total_profit REAL DEFAULT 0,           -- ❌ REAL pierde precisión
    risk_tolerance TEXT DEFAULT 'medium',  -- ❌ Sin CHECK constraint
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    whatsapp_number TEXT,                  -- ⚠️ Debería estar normalizado
    notifications_enabled BOOLEAN DEFAULT true
);
```

**Problemas**:
- ❌ `user_id` como TEXT (debería ser UUID)
- ❌ `total_profit` como REAL (pérdida de precisión en finanzas)
- ❌ No hay `telegram_user_id` separado (inmutable)
- ❌ `risk_tolerance` sin CHECK constraint
- ❌ `whatsapp_number` mezclado con perfil (viola 3NF)
- ❌ Sin índice en `last_activity`
- ❌ Sin `updated_at` para auditoría
- ❌ Sin constraints NOT NULL en campos críticos

### Tabla `whatsapp_messages` (Actual)
```sql
CREATE TABLE IF NOT EXISTS whatsapp_messages (
    id SERIAL PRIMARY KEY,
    user_id TEXT,                          -- ❌ No hay FK enforced
    recipient TEXT,
    message TEXT,
    status TEXT,                           -- ❌ Sin CHECK constraint
    message_sid TEXT,                      -- ❌ No es UNIQUE
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Problemas**:
- ❌ No hay FK constraint a `users.user_id`
- ❌ `message_sid` no es UNIQUE (puede duplicar)
- ❌ `status` sin CHECK constraint
- ❌ Sin índice en `(user_id, timestamp)`

---

## ✅ Solución Propuesta (3NF Normalización)

### 1. Nueva Tabla `users` (Modernizada)

```sql
-- HABILITAR EXTENSIÓN UUID (si no existe)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    -- Identificadores
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),  -- ✅ UUID moderno
    telegram_user_id TEXT UNIQUE NOT NULL,           -- ✅ Inmutable, indexed
    username TEXT UNIQUE,                            -- ✅ UNIQUE constraint
    first_name TEXT,
    email TEXT UNIQUE,                               -- ✅ Nuevo campo
    
    -- Preferencias
    language_code TEXT DEFAULT 'es',
    risk_tolerance TEXT DEFAULT 'medium' 
        CHECK (risk_tolerance IN ('low', 'medium', 'high', 'aggressive')),  -- ✅ CHECK
    notifications_enabled BOOLEAN DEFAULT true,
    
    -- Stats de Trading
    total_trades INTEGER DEFAULT 0 CHECK (total_trades >= 0),
    total_profit NUMERIC(18,8) DEFAULT 0,            -- ✅ NUMERIC precisión
    
    -- Auditoría
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para Performance
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_users_last_activity ON users(last_activity DESC);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = true;

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**Mejoras**:
- ✅ `id` UUID como PK (estándar moderno)
- ✅ `telegram_user_id` separado e inmutable
- ✅ `total_profit` como NUMERIC(18,8) (precisión financiera)
- ✅ CHECK constraints en `risk_tolerance`
- ✅ `email` para futuros canales
- ✅ `updated_at` con trigger automático
- ✅ 4 índices estratégicos
- ✅ Constraints NOT NULL donde corresponde

---

### 2. Nueva Tabla `user_contacts` (Normalización 3NF)

```sql
CREATE TABLE IF NOT EXISTS user_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- ✅ FK enforced
    
    -- Tipo de contacto
    contact_type TEXT NOT NULL 
        CHECK (contact_type IN ('whatsapp', 'telegram', 'email', 'phone', 'sms')),
    contact_value TEXT NOT NULL,                    -- Número, email, username, etc.
    
    -- Verificación y prioridad
    is_verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMP WITH TIME ZONE,
    is_primary BOOLEAN DEFAULT false,               -- Contacto principal para ese tipo
    
    -- Metadatos
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Un usuario no puede tener el mismo contacto duplicado
    UNIQUE(user_id, contact_type, contact_value)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_user_contacts_user ON user_contacts(user_id);
CREATE INDEX IF NOT EXISTS idx_user_contacts_type ON user_contacts(contact_type, is_verified);
CREATE INDEX IF NOT EXISTS idx_user_contacts_primary ON user_contacts(user_id, is_primary) 
    WHERE is_primary = true;

-- Trigger para updated_at
CREATE TRIGGER update_user_contacts_updated_at
    BEFORE UPDATE ON user_contacts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

**Beneficios**:
- ✅ Normalización correcta (1:N relación)
- ✅ Soporte multi-canal (WhatsApp, email, Telegram, etc.)
- ✅ Verificación por canal
- ✅ FK enforced con CASCADE
- ✅ Permite múltiples WhatsApp, emails, etc.

---

### 3. Tabla `whatsapp_messages` (Mejorada)

```sql
CREATE TABLE IF NOT EXISTS whatsapp_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relación con usuario (FK enforced)
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,  -- ✅ FK enforced
    
    -- Mensaje
    recipient TEXT NOT NULL,
    message TEXT NOT NULL,
    
    -- Status con constraint
    status TEXT NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'sent', 'delivered', 'failed', 'read')),  -- ✅ CHECK
    
    -- Twilio tracking
    message_sid TEXT UNIQUE,                        -- ✅ UNIQUE constraint
    error_message TEXT,
    
    -- Timestamps
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para queries frecuentes
CREATE INDEX IF NOT EXISTS idx_whatsapp_user_time ON whatsapp_messages(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_whatsapp_status ON whatsapp_messages(status) WHERE status != 'delivered';
CREATE INDEX IF NOT EXISTS idx_whatsapp_sid ON whatsapp_messages(message_sid) WHERE message_sid IS NOT NULL;
```

**Mejoras**:
- ✅ FK enforced a users(id) con CASCADE
- ✅ UNIQUE en `message_sid`
- ✅ CHECK constraint en `status`
- ✅ Índice compuesto `(user_id, created_at DESC)`
- ✅ Timestamps granulares

---

## 📊 Migración de Datos

### Estrategia
1. **Crear tablas nuevas** (`users_v2`, `user_contacts`, `whatsapp_messages_v2`)
2. **Backfill datos existentes**:
   - `users` → `users_v2` (generar UUID, preservar telegram_user_id)
   - Extraer `whatsapp_number` → `user_contacts`
   - `whatsapp_messages` → `whatsapp_messages_v2` (linkear vía UUID)
3. **Validar integridad** (conteo, FK, constraints)
4. **Swap tablas** (DROP old, RENAME new)

### Script de Migración (Transaccional)

```sql
BEGIN;

-- 1. Habilitar UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Crear tabla users_v2
-- (DDL completo de arriba)

-- 3. Migrar datos de users → users_v2
INSERT INTO users_v2 (
    id, telegram_user_id, username, first_name, language_code,
    total_trades, total_profit, risk_tolerance, notifications_enabled,
    created_at, last_activity, is_active
)
SELECT 
    uuid_generate_v4() as id,
    user_id as telegram_user_id,
    username,
    first_name,
    language_code,
    total_trades,
    total_profit::NUMERIC(18,8),
    COALESCE(risk_tolerance, 'medium'),
    COALESCE(notifications_enabled, true),
    created_at,
    last_activity,
    true as is_active
FROM users;

-- 4. Crear tabla user_contacts
-- (DDL completo de arriba)

-- 5. Migrar whatsapp_number → user_contacts
INSERT INTO user_contacts (user_id, contact_type, contact_value, is_verified, is_primary)
SELECT 
    u2.id,
    'whatsapp' as contact_type,
    u.whatsapp_number as contact_value,
    false as is_verified,
    true as is_primary
FROM users u
JOIN users_v2 u2 ON u.user_id = u2.telegram_user_id
WHERE u.whatsapp_number IS NOT NULL AND u.whatsapp_number != '';

-- 6. Crear whatsapp_messages_v2
-- (DDL completo de arriba)

-- 7. Migrar whatsapp_messages → whatsapp_messages_v2
INSERT INTO whatsapp_messages_v2 (user_id, recipient, message, status, message_sid, created_at)
SELECT 
    u2.id,
    wm.recipient,
    wm.message,
    COALESCE(wm.status, 'sent'),
    wm.message_sid,
    wm.timestamp
FROM whatsapp_messages wm
LEFT JOIN users u ON wm.user_id = u.user_id
LEFT JOIN users_v2 u2 ON u.user_id = u2.telegram_user_id
WHERE u2.id IS NOT NULL;

-- 8. Validaciones
DO $$
DECLARE
    old_count INTEGER;
    new_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO old_count FROM users;
    SELECT COUNT(*) INTO new_count FROM users_v2;
    
    IF old_count != new_count THEN
        RAISE EXCEPTION 'Migration failed: user count mismatch (% vs %)', old_count, new_count;
    END IF;
    
    RAISE NOTICE 'Validation passed: % users migrated successfully', new_count;
END $$;

-- 9. Swap tablas (CUIDADO)
DROP TABLE IF EXISTS users CASCADE;
ALTER TABLE users_v2 RENAME TO users;

DROP TABLE IF EXISTS whatsapp_messages CASCADE;
ALTER TABLE whatsapp_messages_v2 RENAME TO whatsapp_messages;

COMMIT;
```

---

## 📈 Resultados Esperados

### Antes
- 2 tablas con problemas de normalización
- Sin FK constraints enforced
- REAL en datos financieros (pérdida precisión)
- Sin índices estratégicos
- Sin auditoría (updated_at)

### Después
- 3 tablas 100% normalizadas (3NF)
- FK constraints enforced con CASCADE
- NUMERIC en datos financieros
- 10+ índices estratégicos
- Auditoría completa (created_at, updated_at)
- Soporte multi-canal (WhatsApp, email, Telegram, etc.)

---

## 🔧 Próximos Pasos

1. ✅ Implementar DDL en `database_service.py`
2. ⏳ Crear métodos DAL para `user_contacts`
3. ⏳ Actualizar métodos DAL existentes
4. ⏳ Ejecutar migración
5. ⏳ Validar integridad de datos
6. ⏳ Actualizar documentación
