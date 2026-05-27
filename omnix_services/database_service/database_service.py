"""
🗄️ OMNIX DATABASE SERVICE ENTERPRISE
Gestión profesional de PostgreSQL con todas las tablas del sistema

CARACTERÍSTICAS:
- PostgreSQL nativo (Neon)
- 8 tablas profesionales
- Balance tracking automático
- Performance metrics institucionales
- Sharia compliance database
"""

import os
import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    import psycopg
    from psycopg import sql
    PSYCOPG_AVAILABLE = True
    logger.info("✅ psycopg3 cargado correctamente - Soporte nativo de URLs")
except ImportError:
    PSYCOPG_AVAILABLE = False
    logger.warning("psycopg3 no disponible - Database desactivado")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis no disponible - Cleanup se ejecutará siempre")

USE_UNIFIED_GATEWAY = os.environ.get('USE_UNIFIED_GATEWAY', 'false').lower() == 'true'
USE_DATABASE_PORT = os.environ.get('USE_DATABASE_PORT', 'false').lower() == 'true'
_gateway_instance = None

def _get_gateway():
    """Lazy-load database gateway with V7.0 port switching.
    
    V7.0 Migration: When USE_DATABASE_PORT=true, uses DatabaseAdapter (hexagonal).
    Otherwise, uses legacy DatabaseGateway directly.
    """
    global _gateway_instance
    if _gateway_instance is None:
        if USE_DATABASE_PORT:
            try:
                from src.omnix.infrastructure.adapters.database_adapter import DatabaseAdapter
                adapter = DatabaseAdapter()
                if adapter.is_connected():
                    logger.info("✅ USE_DATABASE_PORT=true - Using DatabaseAdapter (V7.0 hexagonal)")
                    _gateway_instance = adapter
                    return _gateway_instance
                else:
                    logger.warning("⚠️ DatabaseAdapter not connected, falling back to DatabaseGateway")
            except ImportError as e:
                logger.warning(f"⚠️ DatabaseAdapter import failed: {e}, using DatabaseGateway")
            except Exception as e:
                logger.error(f"❌ DatabaseAdapter creation failed: {e}, using DatabaseGateway")
        
        try:
            from omnix_services.database_service.database_gateway import DatabaseGateway
            _gateway_instance = DatabaseGateway.get_instance()
        except ImportError as e:
            logger.warning(f"⚠️ DatabaseGateway not available: {e}")
    return _gateway_instance


class DatabaseServiceEnterprise:
    """
    🗄️ SERVICIO ENTERPRISE DE BASE DE DATOS OMNIX
    
    Arquitectura profesional PostgreSQL para:
    - User management
    - Trading history
    - Balance tracking
    - Performance metrics
    - Sharia compliance
    """
    
    def __init__(self):
        self.db_url = None
        self.connected = False
        self.redis_client = None
        db_url_source = None
        
        # 🔧 FIX Nov 29, 2025: Múltiples fuentes para DATABASE_URL
        # Prioridad: os.environ > env_manager > settings
        # Esto soluciona el problema de orden de carga en Railway
        
        # 1. Intentar os.environ primero (Railway/Replit inyectan aquí)
        self.db_url = os.environ.get('DATABASE_URL')
        if self.db_url:
            db_url_source = "os.environ"
        
        # 2. Si no está en os.environ, intentar env_manager
        if not self.db_url:
            try:
                from omnix_config.env_manager import env_config
                self.db_url = env_config.get('DATABASE_URL')
                if self.db_url:
                    db_url_source = "env_manager"
                    # También inyectar a os.environ para otros módulos
                    os.environ['DATABASE_URL'] = self.db_url
                    logger.info("🔄 DATABASE_URL cargada desde env_manager → inyectada a os.environ")
            except Exception as e:
                logger.warning(f"⚠️ env_manager no disponible: {e}")
        
        # 3. Si aún no está, intentar settings
        if not self.db_url:
            try:
                from omnix_config.settings import settings
                if hasattr(settings, 'database') and hasattr(settings.database, 'url'):
                    self.db_url = settings.database.url
                    if self.db_url:
                        db_url_source = "settings"
                        os.environ['DATABASE_URL'] = self.db_url
                        logger.info("🔄 DATABASE_URL cargada desde settings → inyectada a os.environ")
            except Exception as e:
                logger.warning(f"⚠️ settings no disponible: {e}")
        
        # 🔧 FIX Nov 29, 2025 #2: Detectar si el VALUE incluye la KEY como prefijo
        # Esto ocurre cuando Railway tiene: Key=DATABASE_URL, Value=DATABASE_URL=postgresql://...
        if self.db_url:
            # Detectar patrones incorrectos: DATABASE_URL=... o DATABASE_URL:...
            if self.db_url.startswith('DATABASE_URL='):
                self.db_url = self.db_url[len('DATABASE_URL='):]
                # Propagar la corrección a os.environ para otros módulos
                os.environ['DATABASE_URL'] = self.db_url
                logger.warning("🔧 FIX APLICADO: Removido prefijo 'DATABASE_URL=' → propagado a os.environ")
            elif self.db_url.startswith('DATABASE_URL:'):
                self.db_url = self.db_url[len('DATABASE_URL:'):]
                os.environ['DATABASE_URL'] = self.db_url
                logger.warning("🔧 FIX APLICADO: Removido prefijo 'DATABASE_URL:' → propagado a os.environ")
            elif self.db_url == 'DATABASE_URL':
                # El valor ES literalmente la key (error de configuración)
                logger.error("❌ DATABASE_URL contiene 'DATABASE_URL' literal - Error de configuración en Railway")
                logger.error("   Revisa que el VALUE sea la URL real, no el nombre de la variable")
                self.db_url = None
        
        # 🔧 FIX: Railway usa postgres:// pero psycopg necesita postgresql://
        if self.db_url and self.db_url.startswith('postgres://'):
            self.db_url = self.db_url.replace('postgres://', 'postgresql://', 1)
            logger.info("🔄 DATABASE_URL convertida: postgres:// → postgresql://")
        
        # Intentar conectar a Redis para tracking de cleanup
        if REDIS_AVAILABLE:
            try:
                redis_url = os.environ.get('REDIS_URL')
                if not redis_url:
                    try:
                        from omnix_config.env_manager import env_config
                        redis_url = env_config.get('REDIS_URL', 'redis://localhost:6379')
                    except Exception:
                        redis_url = os.environ.get('REDIS_URL', 'redis://shinkansen.proxy.rlwy.net:32595')
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
            except Exception as e:
                logger.warning(f"Redis no disponible para cleanup tracking: {e}")
        
        # 🔍 DEBUG LOGGING MEJORADO PARA RAILWAY
        logger.info("=" * 70)
        logger.info("🚀 INICIANDO DatabaseServiceEnterprise V6.3 (psycopg3)")
        logger.info(f"📊 PSYCOPG_AVAILABLE: {PSYCOPG_AVAILABLE}")
        
        if self.db_url:
            # Mostrar primeros 30 caracteres para confirmar presencia (sin exponer credenciales)
            db_url_preview = self.db_url[:30] + "..." if len(self.db_url) > 30 else self.db_url
            logger.info(f"✅ DATABASE_URL detectada: {db_url_preview}")
            logger.info(f"📏 DATABASE_URL length: {len(self.db_url)} caracteres")
            logger.info(f"📦 DATABASE_URL source: {db_url_source}")
        else:
            logger.error("❌ DATABASE_URL NO ENCONTRADA en ninguna fuente:")
            logger.error("   - os.environ: No")
            logger.error("   - env_manager: No")
            logger.error("   - settings: No")
            logger.info(f"🔑 Variables en os.environ: {', '.join(sorted([k for k in os.environ.keys() if 'DATABASE' in k.upper() or 'PG' in k.upper()])[:10])}")
            logger.info("=" * 70)
            return
        
        if not PSYCOPG_AVAILABLE:
            logger.error("❌ psycopg3 NO DISPONIBLE - No se puede conectar a PostgreSQL")
            logger.info("=" * 70)
            return
        
        try:
            logger.info("🔌 Intentando conectar a PostgreSQL...")
            
            # 🚦 FEATURE FLAG: DISABLE_AUTO_MIGRATIONS (Phase 1 - Dec 2025)
            # Set DISABLE_AUTO_MIGRATIONS=true in Railway to skip all DDL operations
            # This allows telemetry collection without schema changes
            auto_migrations_disabled = os.environ.get('DISABLE_AUTO_MIGRATIONS', 'false').lower() == 'true'
            self.auto_migrations_enabled = not auto_migrations_disabled
            
            if auto_migrations_disabled:
                logger.warning("=" * 70)
                logger.warning("⚠️ AUTO-MIGRATIONS DISABLED via DISABLE_AUTO_MIGRATIONS=true")
                logger.warning("   - Schema migrations: SKIPPED")
                logger.warning("   - Table cleanup: SKIPPED")
                logger.warning("   - Connection validation: RUNNING")
                logger.warning("=" * 70)
                
                # Validate connection even when migrations are disabled
                # This ensures self.connected is accurate and queries can execute
                test_conn = self._get_connection()
                if test_conn:
                    try:
                        cursor = test_conn.cursor()
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
                        cursor.close()
                        logger.info("✅ Connection validated (migrations disabled)")
                    finally:
                        test_conn.close()
                else:
                    raise Exception("Failed to establish database connection")
            else:
                # 🔄 EJECUTAR MIGRACIONES (si es necesario)
                self._migrate_users_to_v2()
                self._drop_prices_table()
                self._fix_risk_guardian_user_id_type()
                self._add_foreign_key_constraints()
                self._add_check_constraints()
                
                # 🧹 MIGRACIÓN AGRESIVA: Limpieza de tablas legacy (Nov 28, 2025)
                # EJECUTAR ANTES de _init_tables() para evitar recrear tablas legacy
                self._run_aggressive_cleanup()
                
                self._init_tables()
                
                # 🗑️ Ejecutar cleanup automático (1x por día)
                self._run_daily_cleanup()
            
            self.connected = True
            self.using_enterprise = True  # 🔧 FIX Nov 30, 2025: Flag para PaperTradingManager use PostgreSQL
            logger.info("✅ PostgreSQL: 33 tablas activas (8 core + 6 risk + 6 derivatives + 7 community + 6 signals)")
            logger.info("🗄️ DatabaseServiceEnterprise conectado exitosamente")
            logger.info("🏢 using_enterprise = True → Paper Trading usará PostgreSQL")
            logger.info("=" * 70)
        except Exception as e:
            logger.error("=" * 70)
            logger.error(f"❌ ERROR CONECTANDO A POSTGRESQL:")
            logger.error(f"   Tipo: {type(e).__name__}")
            logger.error(f"   Mensaje: {str(e)}")
            import traceback
            logger.error(f"   Traceback completo:\n{traceback.format_exc()}")
            logger.error("=" * 70)
    
    def health_check(self) -> Dict[str, bool]:
        """Health check del servicio"""
        return {
            'psycopg_available': PSYCOPG_AVAILABLE,
            'database_connected': self.connected,
            'database_url_configured': bool(self.db_url),
            'auto_migrations_enabled': getattr(self, 'auto_migrations_enabled', True)
        }
    
    def execute_query(self, sql: str, params: tuple = None, fetch: bool = None):
        """
        Ejecutar query SQL genérica
        
        🚀 Phase 4 Database Unification (Dec 2025):
        - If USE_UNIFIED_GATEWAY=true, uses DatabaseGateway connection pool
        - Otherwise, uses legacy direct connections
        
        Args:
            sql: Query SQL a ejecutar
            params: Parámetros para la query (tuple)
            fetch: Si True, retorna resultados (SELECT/RETURNING). 
                   Si False, solo ejecuta (INSERT/UPDATE sin RETURNING).
                   Si None (default), auto-detecta basado en el SQL.
            
        Returns:
            Lista de tuplas con resultados si es SELECT o RETURNING, None si es INSERT/UPDATE sin fetch
        """
        if not self.connected:
            logger.error("❌ execute_query: Database no conectada")
            return None
        
        sql_upper = sql.strip().upper()
        should_fetch = fetch if fetch is not None else (
            sql_upper.startswith('SELECT') or 'RETURNING' in sql_upper
        )
        
        if USE_UNIFIED_GATEWAY:
            gateway = _get_gateway()
            if gateway and gateway._pool:
                try:
                    from omnix_services.database_service.database_gateway import DatabaseGateway
                    return DatabaseGateway.execute_query(sql, params, fetch=should_fetch)
                except Exception as e:
                    logger.warning(f"⚠️ Gateway execute_query failed, falling back: {e}")
        
        conn = None
        try:
            conn = self._get_connection()
            if not conn:
                logger.error("❌ execute_query: No se pudo obtener conexión")
                return None
                
            cursor = conn.cursor()
            
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            if should_fetch:
                result = cursor.fetchall()
                conn.commit()
                return result
            else:
                conn.commit()
                return None
                
        except Exception as e:
            logger.error(f"❌ execute_query error: {e}")
            logger.error(f"   SQL: {sql[:100]}...")
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    logger.debug("Rollback failed during error handling")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    logger.debug("Connection close failed")
    
    def _get_connection(self):
        """
        Obtener conexión a PostgreSQL
        
        🚀 Phase 4 Database Unification (Dec 2025):
        - Uses legacy direct connection (deprecated)
        - For new code, prefer execute_query() which uses DatabaseGateway
        
        ⚠️ DEPRECATED: This method creates a new connection each time.
        Use execute_query() instead for automatic connection pooling.
        """
        if not self.db_url or not PSYCOPG_AVAILABLE:
            return None
        
        if not USE_UNIFIED_GATEWAY:
            import warnings
            warnings.warn(
                "DatabaseServiceEnterprise._get_connection() creates unpooled connections. "
                "Set USE_UNIFIED_GATEWAY=true to use the unified connection pool via execute_query().",
                DeprecationWarning,
                stacklevel=2
            )
        
        try:
            conn_string = self.db_url
            if '?' not in conn_string:
                conn_string += '?sslmode=require'
            elif 'sslmode' not in conn_string:
                conn_string += '&sslmode=require'
            
            return psycopg.connect(conn_string, connect_timeout=10)
        except Exception as e:
            logger.error(f"❌ Error conectando a PostgreSQL: {e}")
            raise
    
    def _migrate_users_to_v2(self):
        """
        🔄 MIGRACIÓN CONSERVADORA: Modernización progresiva sin romper compatibilidad
        
        Estrategia:
        - Agregar columnas nuevas a users SIN eliminar user_id (backward compatible)
        - Crear tabla user_contacts para normalización
        - Mejorar whatsapp_messages progresivamente
        - Mantener 100% compatibilidad con código existente
        
        FECHA: Nov 26, 2025
        """
        if not self.db_url or not PSYCOPG_AVAILABLE:
            return
        
        conn = self._get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            # ✅ Verificar si la tabla users existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'users' 
                    AND table_schema = 'public'
                )
            """)
            users_exists = cursor.fetchone()[0]
            
            if not users_exists:
                logger.info("✅ Fresh deployment: users table no existe, saltando migración")
                logger.info("   _init_tables() creará el schema correcto")
                conn.close()
                return
            
            # Verificar si la migración ya se ejecutó
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'total_profit'
            """)
            profit_column = cursor.fetchone()
            
            # Si total_profit ya es NUMERIC, la migración ya se ejecutó
            if profit_column and 'numeric' in profit_column[1]:
                logger.info("✅ Migración ya completada (total_profit es NUMERIC)")
                conn.close()
                return
            
            logger.info("🔄 Iniciando MIGRACIÓN FASE 1: Mejoras ADD-ONLY (backward compatible)")
            logger.info("   Detectada tabla users existente, aplicando ALTER TABLE...")
            
            # Habilitar extensión UUID
            cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            
            # ========================================
            # FASE 1: AGREGAR COLUMNAS NUEVAS A USERS
            # (Mantener user_id TEXT como PK - NO romper nada)
            # ========================================
            
            # Agregar columna email
            cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS email TEXT UNIQUE
            ''')
            
            # Agregar columna is_active
            cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true
            ''')
            
            # Agregar columna updated_at
            cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            ''')
            
            # Cambiar total_profit de REAL a NUMERIC (con validación)
            logger.info("  Migrando total_profit: REAL → NUMERIC(18,8)...")
            cursor.execute('''
                ALTER TABLE users 
                ALTER COLUMN total_profit TYPE NUMERIC(18,8) 
                USING COALESCE(total_profit::NUMERIC(18,8), 0)
            ''')
            
            # Agregar CHECK constraint en risk_tolerance (si no existe)
            cursor.execute('''
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint 
                        WHERE conname = 'check_risk_tolerance'
                    ) THEN
                        ALTER TABLE users ADD CONSTRAINT check_risk_tolerance 
                        CHECK (risk_tolerance IN ('low', 'medium', 'high', 'aggressive'));
                    END IF;
                END $$
            ''')
            
            # Agregar CHECK constraint en total_trades
            cursor.execute('''
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint 
                        WHERE conname = 'check_total_trades'
                    ) THEN
                        ALTER TABLE users ADD CONSTRAINT check_total_trades 
                        CHECK (total_trades >= 0);
                    END IF;
                END $$
            ''')
            
            # Crear índices nuevos
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_last_activity ON users(last_activity DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = true')
            
            logger.info("✅ Columnas nuevas agregadas a users")
            
            # ========================================
            # CREAR TABLA user_contacts (NORMALIZACIÓN 3NF)
            # FK a users.user_id TEXT (no UUID todavía)
            # ========================================
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_contacts (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    contact_type TEXT NOT NULL 
                        CHECK (contact_type IN ('whatsapp', 'telegram', 'email', 'phone', 'sms')),
                    contact_value TEXT NOT NULL,
                    is_verified BOOLEAN DEFAULT false,
                    verified_at TIMESTAMP WITH TIME ZONE,
                    is_primary BOOLEAN DEFAULT false,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, contact_type, contact_value)
                )
            ''')
            
            # Índices para user_contacts
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_contacts_user ON user_contacts(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_contacts_type ON user_contacts(contact_type, is_verified)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_contacts_primary ON user_contacts(user_id, is_primary) WHERE is_primary = true')
            
            logger.info("✅ Tabla user_contacts creada")
            
            # Migrar whatsapp_number → user_contacts
            cursor.execute('''
                INSERT INTO user_contacts (user_id, contact_type, contact_value, is_verified, is_primary)
                SELECT 
                    user_id,
                    'whatsapp' as contact_type,
                    whatsapp_number as contact_value,
                    false as is_verified,
                    true as is_primary
                FROM users
                WHERE whatsapp_number IS NOT NULL AND whatsapp_number != ''
                ON CONFLICT (user_id, contact_type, contact_value) DO NOTHING
            ''')
            
            migrated_contacts = cursor.rowcount
            logger.info(f"✅ Migrados {migrated_contacts} contactos WhatsApp a user_contacts")
            
            # Commit
            conn.commit()
            logger.info("🎉 MIGRACIÓN FASE 1 COMPLETADA EXITOSAMENTE")
            logger.info("   - users mejorada (email, is_active, updated_at, NUMERIC)")
            logger.info("   - CHECK constraints agregados")
            logger.info("   - user_contacts creada (3NF normalización)")
            logger.info(f"   - {migrated_contacts} contactos normalizados")
            logger.info("   - ✅ 100% BACKWARD COMPATIBLE (user_id TEXT preservado)")
            
        except Exception as e:
            logger.error(f"❌ ERROR EN MIGRACIÓN: {e}")
            import traceback
            logger.error(traceback.format_exc())
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _drop_prices_table(self):
        """
        🗑️ MIGRACIÓN: Eliminar tabla prices huérfana (Nov 26, 2025)
        
        Razón: La tabla prices nunca se usa (0 INSERT, 0 SELECT).
        Todos los módulos consultan precios directamente vía API Kraken.
        
        Esta migración es idempotente y segura.
        """
        if not self.db_url or not PSYCOPG_AVAILABLE:
            return
        
        conn = self._get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            # Verificar si la tabla existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'prices' 
                    AND table_schema = 'public'
                )
            """)
            prices_exists = cursor.fetchone()[0]
            
            if not prices_exists:
                logger.info("✅ Tabla prices ya no existe (skip migration)")
                conn.close()
                return
            
            logger.info("🗑️ Eliminando tabla prices (huérfana, 0 usos)")
            
            # DROP TABLE (seguro con IF EXISTS)
            cursor.execute('DROP TABLE IF EXISTS prices')
            
            conn.commit()
            logger.info("✅ Tabla prices eliminada exitosamente")
            logger.info("   Razón: Todos los módulos usan API Kraken directamente")
            
        except Exception as e:
            logger.error(f"❌ Error eliminando tabla prices: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _fix_risk_guardian_user_id_type(self):
        """
        🔧 MIGRACIÓN: Corregir tipo incompatible en risk_guardian_events (Nov 26, 2025)
        
        Problema: risk_guardian_events.user_id es BIGINT pero users.user_id es TEXT (Telegram ID)
        Solución: ALTER COLUMN user_id de BIGINT → TEXT
        
        Esta migración es idempotente y segura.
        """
        if not self.db_url or not PSYCOPG_AVAILABLE:
            return
        
        conn = self._get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            # Verificar si la tabla existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'risk_guardian_events' 
                    AND table_schema = 'public'
                )
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                logger.info("✅ Tabla risk_guardian_events no existe aún (skip migration)")
                conn.close()
                return
            
            # Verificar tipo actual
            cursor.execute("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'risk_guardian_events' 
                AND column_name = 'user_id'
            """)
            current_type = cursor.fetchone()
            
            if not current_type:
                logger.info("✅ Columna user_id no existe en risk_guardian_events (skip migration)")
                conn.close()
                return
            
            if current_type[0] == 'text':
                logger.info("✅ risk_guardian_events.user_id ya es TEXT (skip migration)")
                conn.close()
                return
            
            logger.info("🔧 Corrigiendo tipo incompatible: risk_guardian_events.user_id BIGINT → TEXT")
            
            # ALTER COLUMN (seguro - convierte int a string)
            cursor.execute("""
                ALTER TABLE risk_guardian_events 
                ALTER COLUMN user_id TYPE TEXT 
                USING user_id::TEXT
            """)
            
            conn.commit()
            logger.info("✅ Tipo corregido exitosamente: risk_guardian_events.user_id ahora es TEXT")
            logger.info("   Razón: users.user_id es TEXT (Telegram ID), necesita consistencia")
            
        except Exception as e:
            logger.error(f"❌ Error corrigiendo tipo user_id: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _add_foreign_key_constraints(self):
        """
        🔗 MIGRACIÓN: Agregar Foreign Key Constraints (Nov 26, 2025)
        
        Garantiza integridad referencial con ON DELETE CASCADE para:
        - trades, analysis, conversations, balance_history (datos del usuario)
        - paper_trading_trades, trade_reasonings, trade_evaluations (datos derivados)
        - community_signals, signal_executions, signal_votes (Community Intelligence)
        - alpha_leaderboard, risk_guardian_events (tracking)
        
        Estrategia: CASCADE - Si eliminas usuario, eliminas todos sus datos relacionados
        
        Esta migración es idempotente (verifica FK antes de agregar).
        """
        if not self.db_url or not PSYCOPG_AVAILABLE:
            return
        
        conn = self._get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            logger.info("🔗 Agregando Foreign Key Constraints con ON DELETE CASCADE...")
            
            # Función helper para verificar si FK existe
            def fk_exists(table_name, constraint_name):
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE table_name = %s 
                        AND constraint_name = %s 
                        AND constraint_type = 'FOREIGN KEY'
                    )
                """, (table_name, constraint_name))
                return cursor.fetchone()[0]
            
            # Función helper para verificar si columna existe (ADDED Dec 6, 2025)
            def column_exists(table_name, column_name):
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = %s 
                        AND column_name = %s
                    )
                """, (table_name, column_name))
                return cursor.fetchone()[0]
            
            # Lista de FKs a agregar (tabla, columna_fk, constraint_name)
            foreign_keys = [
                ('trades', 'user_id', 'fk_trades_user'),
                ('analysis', 'user_id', 'fk_analysis_user'),
                ('conversations', 'user_id', 'fk_conversations_user'),
                ('whatsapp_messages', 'user_id', 'fk_whatsapp_user'),
                ('balance_history', 'user_id', 'fk_balance_history_user'),
                ('paper_trading_trades', 'user_id', 'fk_paper_trades_user'),
                ('trade_reasonings', 'user_id', 'fk_trade_reasonings_user'),
                ('trade_evaluations', 'user_id', 'fk_trade_evaluations_user'),
                ('community_signals', 'contributor_id', 'fk_signals_contributor'),
                ('signal_executions', 'executor_id', 'fk_executions_executor'),
                ('signal_votes', 'voter_id', 'fk_votes_voter'),
                ('alpha_leaderboard', 'user_id', 'fk_leaderboard_user'),
                ('risk_guardian_events', 'user_id', 'fk_risk_events_user'),
            ]
            
            added_count = 0
            skipped_count = 0
            
            for table, column, constraint in foreign_keys:
                # Verificar si la tabla existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s AND table_schema = 'public'
                    )
                """, (table,))
                
                if not cursor.fetchone()[0]:
                    logger.info(f"   ⏭️  Tabla {table} no existe (skip)")
                    skipped_count += 1
                    continue
                
                # Verificar si la columna existe (ADDED Dec 6, 2025 - defensive migration)
                if not column_exists(table, column):
                    logger.info(f"   ⏭️  Columna {column} no existe en {table} (skip)")
                    skipped_count += 1
                    continue
                
                # Verificar si FK ya existe
                if fk_exists(table, constraint):
                    logger.info(f"   ✅ {constraint} ya existe en {table}")
                    skipped_count += 1
                    continue
                
                # Agregar FK
                try:
                    cursor.execute(f"""
                        ALTER TABLE {table} 
                        ADD CONSTRAINT {constraint} 
                        FOREIGN KEY ({column}) 
                        REFERENCES users(user_id) 
                        ON DELETE CASCADE
                    """)
                    logger.info(f"   ✅ Agregado {constraint} en {table}.{column}")
                    added_count += 1
                except Exception as e:
                    logger.warning(f"   ⚠️  Error agregando {constraint}: {e}")
            
            conn.commit()
            
            if added_count > 0:
                logger.info(f"✅ Foreign Keys agregadas: {added_count} nuevas, {skipped_count} ya existían")
                logger.info("   Estrategia: ON DELETE CASCADE (eliminar usuario elimina datos relacionados)")
            else:
                logger.info(f"✅ Todas las Foreign Keys ya estaban configuradas ({skipped_count} FKs)")
            
        except Exception as e:
            logger.error(f"❌ Error agregando Foreign Keys: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _add_check_constraints(self):
        """
        ✅ MIGRACIÓN: Agregar CHECK Constraints para validación de datos (Nov 26, 2025)
        
        Garantiza valores válidos en columnas enum y rangos numéricos:
        - trades.status: valores permitidos
        - community_signals.signal_type y status
        - signal_votes.vote_type
        - pending_evaluations.status
        - community_feedback.result
        
        Estrategia: Constraints a nivel DB previenen datos inválidos
        
        Esta migración es idempotente (verifica constraints antes de agregar).
        """
        if not self.db_url or not PSYCOPG_AVAILABLE:
            return
        
        conn = self._get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            logger.info("✅ Agregando CHECK Constraints para validación de datos...")
            
            # Función helper para verificar si constraint existe
            def check_exists(table_name, constraint_name):
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE table_name = %s 
                        AND constraint_name = %s 
                        AND constraint_type = 'CHECK'
                    )
                """, (table_name, constraint_name))
                return cursor.fetchone()[0]
            
            # Función helper para verificar si columna existe (ADDED Dec 6, 2025)
            def column_exists_check(table_name, column_name):
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = %s 
                        AND column_name = %s
                    )
                """, (table_name, column_name))
                return cursor.fetchone()[0]
            
            # Función helper para extraer nombre de columna de condición CHECK
            def extract_column_from_condition(condition):
                """Extrae el nombre de columna de una condición como 'status IN (...)'"""
                import re
                match = re.match(r'^(\w+)\s+IN\s+', condition)
                return match.group(1) if match else None
            
            # Lista de CHECK constraints a agregar
            # (tabla, constraint_name, condición)
            check_constraints = [
                ('trades', 'chk_trades_status', 
                 "status IN ('filled', 'cancelled', 'pending', 'open', 'closed')"),
                
                ('community_signals', 'chk_signals_type', 
                 "signal_type IN ('BUY', 'SELL')"),
                
                ('community_signals', 'chk_signals_status', 
                 "status IN ('active', 'expired', 'closed')"),
                
                ('signal_votes', 'chk_votes_type', 
                 "vote_type IN ('upvote', 'downvote')"),
                
                ('pending_evaluations', 'chk_evaluations_status', 
                 "status IN ('pending', 'completed', 'failed')"),
                
                ('community_feedback', 'chk_feedback_result', 
                 "result IN ('success', 'fail', 'neutral', 'mixed')"),
                
                ('strategy_votes', 'chk_strategy_vote', 
                 "vote IN ('approve', 'reject', 'neutral')"),
            ]
            
            added_count = 0
            skipped_count = 0
            
            for table, constraint, condition in check_constraints:
                # Verificar si la tabla existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s AND table_schema = 'public'
                    )
                """, (table,))
                
                if not cursor.fetchone()[0]:
                    logger.info(f"   ⏭️  Tabla {table} no existe (skip)")
                    skipped_count += 1
                    continue
                
                # Verificar si la columna referenciada en la condición existe (ADDED Dec 6, 2025)
                column_name = extract_column_from_condition(condition)
                if column_name and not column_exists_check(table, column_name):
                    logger.info(f"   ⏭️  Columna {column_name} no existe en {table} (skip)")
                    skipped_count += 1
                    continue
                
                # Verificar si constraint ya existe
                if check_exists(table, constraint):
                    logger.info(f"   ✅ {constraint} ya existe en {table}")
                    skipped_count += 1
                    continue
                
                # Agregar CHECK constraint
                try:
                    cursor.execute(f"""
                        ALTER TABLE {table} 
                        ADD CONSTRAINT {constraint} 
                        CHECK ({condition})
                    """)
                    logger.info(f"   ✅ Agregado {constraint} en {table}")
                    added_count += 1
                except Exception as e:
                    logger.warning(f"   ⚠️  Error agregando {constraint}: {e}")
            
            conn.commit()
            
            if added_count > 0:
                logger.info(f"✅ CHECK Constraints agregados: {added_count} nuevos, {skipped_count} ya existían")
                logger.info("   Beneficio: Validación automática de datos a nivel DB")
            else:
                logger.info(f"✅ Todos los CHECK Constraints ya estaban configurados ({skipped_count} constraints)")
            
        except Exception as e:
            logger.error(f"❌ Error agregando CHECK Constraints: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _run_aggressive_cleanup(self):
        """
        🧹 MIGRACIÓN AGRESIVA: Limpieza de tablas legacy y normalización (Nov 28, 2025)
        
        Opción B (Agresiva): Eliminación de tablas sin uso activo
        
        ESTRATEGIA:
        1. Advisory lock para prevenir ejecuciones concurrentes
        2. Transacción única con rollback automático si falla algo
        3. Migrar users.whatsapp_number → user_contacts (ON CONFLICT para idempotencia)
        4. Crear backups: omnix_backup.<tabla>_YYYYMMDD
        5. DROP TABLE IF EXISTS para 5 tablas legacy:
           - whatsapp_messages (sin uso activo)
           - detected_patterns (sin uso activo)
           - improvement_proposals (sin uso activo)
           - monitoring_metrics (sin uso activo)
           - ai_alerts (sin uso activo)
        6. Tabla schema_migrations para tracking one-time execution
        
        GARANTÍAS DE SEGURIDAD:
        - Idempotente (ejecutable múltiples veces sin error)
        - Transaccional (rollback automático si falla)
        - Backups automáticos antes de DROP
        - Advisory lock previene race conditions
        
        RESULTADO: 33 tablas (8 core + 6 risk/monitoring + 6 derivatives + 7 community + 6 signals)
        """
        if not self.db_url or not PSYCOPG_AVAILABLE:
            return
        
        conn = self._get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            # ================================================
            # PASO 0: Verificar si migración ya se ejecutó
            # ================================================
            logger.info("🔍 Verificando si migración agresiva ya se ejecutó...")
            
            # Crear tabla schema_migrations si no existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    migration_name TEXT UNIQUE NOT NULL,
                    migration_hash TEXT,
                    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN DEFAULT true
                )
            """)
            conn.commit()
            
            # Verificar si esta migración ya corrió
            migration_name = 'aggressive_cleanup_nov28_2025'
            migration_hash = 'drop_5_legacy_tables_normalize_contacts'
            
            cursor.execute("""
                SELECT executed_at, success FROM schema_migrations 
                WHERE migration_name = %s AND success = true
            """, (migration_name,))
            
            existing_migration = cursor.fetchone()
            
            if existing_migration:
                logger.info(f"✅ Migración agresiva ya ejecutada el {existing_migration[0]}")
                logger.info("   ⏭️  Saltando ejecución (idempotencia)")
                conn.close()
                return
            
            logger.info("🚀 Iniciando MIGRACIÓN AGRESIVA - Limpieza de base de datos...")
            logger.info("=" * 80)
            
            # ================================================
            # PASO 1: Advisory Lock para prevenir concurrencia
            # ================================================
            logger.info("🔒 Adquiriendo advisory lock (ID: 999888777)...")
            cursor.execute("SELECT pg_advisory_lock(999888777)")
            logger.info("✅ Lock adquirido")
            
            # ================================================
            # PASO 2: Iniciar transacción principal
            # ================================================
            logger.info("📦 Iniciando transacción principal...")
            
            # ================================================
            # PASO 3: Migrar users.whatsapp_number → user_contacts
            # ================================================
            logger.info("📱 PASO 1/4: Migrando users.whatsapp_number → user_contacts...")
            
            # Verificar si columna existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name = 'whatsapp_number'
                )
            """)
            
            if cursor.fetchone()[0]:
                # Migrar datos
                cursor.execute("""
                    INSERT INTO user_contacts (user_id, contact_type, contact_value, is_primary)
                    SELECT user_id, 'whatsapp', whatsapp_number, true
                    FROM users
                    WHERE whatsapp_number IS NOT NULL
                    AND whatsapp_number != ''
                    ON CONFLICT (user_id, contact_type, contact_value) 
                    DO UPDATE SET is_primary = EXCLUDED.is_primary
                """)
                
                migrated_count = cursor.rowcount
                logger.info(f"   ✅ Migrados {migrated_count} números WhatsApp a user_contacts")
                
                # Verificar que todos fueron migrados
                cursor.execute("""
                    SELECT COUNT(*) FROM users 
                    WHERE whatsapp_number IS NOT NULL AND whatsapp_number != ''
                """)
                total_whatsapp = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM user_contacts 
                    WHERE contact_type = 'whatsapp'
                """)
                migrated_in_contacts = cursor.fetchone()[0]
                
                logger.info(f"   🔍 Verificación: {total_whatsapp} en users → {migrated_in_contacts} en user_contacts")
                
                # Eliminar columna whatsapp_number
                logger.info("   🗑️  Eliminando columna users.whatsapp_number...")
                cursor.execute("ALTER TABLE users DROP COLUMN IF EXISTS whatsapp_number")
                logger.info("   ✅ Columna eliminada")
            else:
                logger.info("   ⏭️  Columna whatsapp_number ya eliminada - saltando migración")
            
            # ================================================
            # PASO 4: Crear backups de tablas legacy
            # ================================================
            logger.info("💾 PASO 2/4: Creando backups de tablas legacy...")
            
            backup_date = datetime.now().strftime('%Y%m%d')
            legacy_tables = [
                'whatsapp_messages',
                'detected_patterns', 
                'improvement_proposals',
                'monitoring_metrics',
                'ai_alerts'
            ]
            
            backed_up_count = 0
            for table_name in legacy_tables:
                # Verificar si tabla existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s AND table_schema = 'public'
                    )
                """, (table_name,))
                
                if cursor.fetchone()[0]:
                    # Contar registros
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    
                    backup_table = f"omnix_backup_{table_name}_{backup_date}"
                    
                    # Crear backup
                    cursor.execute(f"""
                        CREATE TABLE IF NOT EXISTS {backup_table} AS 
                        SELECT * FROM {table_name}
                    """)
                    
                    logger.info(f"   ✅ Backup creado: {backup_table} ({row_count} registros)")
                    backed_up_count += 1
                else:
                    logger.info(f"   ⏭️  Tabla {table_name} no existe - saltando backup")
            
            logger.info(f"   📊 Total backups creados: {backed_up_count}/{len(legacy_tables)}")
            
            # ================================================
            # PASO 5: DROP TABLE IF EXISTS para tablas legacy
            # ================================================
            logger.info("🗑️  PASO 3/4: Eliminando tablas legacy...")
            
            dropped_count = 0
            for table_name in legacy_tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                logger.info(f"   ✅ Eliminada: {table_name}")
                dropped_count += 1
            
            logger.info(f"   📊 Total tablas eliminadas: {dropped_count}/{len(legacy_tables)}")
            
            # ================================================
            # PASO 6: Registrar migración exitosa
            # ================================================
            logger.info("📝 PASO 4/4: Registrando migración en schema_migrations...")
            
            cursor.execute("""
                INSERT INTO schema_migrations (migration_name, migration_hash, success)
                VALUES (%s, %s, true)
                ON CONFLICT (migration_name) 
                DO UPDATE SET executed_at = CURRENT_TIMESTAMP, success = true
            """, (migration_name, migration_hash))
            
            logger.info("   ✅ Migración registrada")
            
            # ================================================
            # PASO 7: COMMIT - Aplicar todos los cambios
            # ================================================
            logger.info("💾 Aplicando cambios (COMMIT)...")
            conn.commit()
            logger.info("✅ COMMIT exitoso")
            
            # ================================================
            # PASO 8: Liberar advisory lock
            # ================================================
            logger.info("🔓 Liberando advisory lock...")
            cursor.execute("SELECT pg_advisory_unlock(999888777)")
            logger.info("✅ Lock liberado")
            
            # ================================================
            # RESUMEN FINAL
            # ================================================
            logger.info("=" * 80)
            logger.info("🎉 MIGRACIÓN AGRESIVA COMPLETADA EXITOSAMENTE")
            logger.info("📊 Resultado:")
            logger.info(f"   - Tablas eliminadas: {dropped_count}")
            logger.info(f"   - Backups creados: {backed_up_count}")
            logger.info(f"   - WhatsApp contacts migrados: {migrated_count if 'migrated_count' in locals() else 0}")
            logger.info(f"   - Schema esperado: 33 tablas (8 core + 6 risk + 6 derivatives + 7 community + 6 signals)")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error("=" * 80)
            logger.error("❌ ERROR EN MIGRACIÓN AGRESIVA")
            logger.error(f"   Tipo: {type(e).__name__}")
            logger.error(f"   Mensaje: {str(e)}")
            import traceback
            logger.error(f"   Traceback:\n{traceback.format_exc()}")
            logger.error("=" * 80)
            logger.error("🔄 ROLLBACK automático - ningún cambio fue aplicado")
            
            # Registrar migración fallida
            try:
                cursor.execute("""
                    INSERT INTO schema_migrations (migration_name, migration_hash, success)
                    VALUES (%s, %s, false)
                    ON CONFLICT (migration_name) DO NOTHING
                """, (migration_name, migration_hash))
                conn.commit()
            except Exception:
                logger.debug("Failed to log migration failure")
            
            conn.rollback()
            
            try:
                cursor.execute("SELECT pg_advisory_unlock(999888777)")
            except Exception:
                logger.debug("Failed to release advisory lock")
        
        finally:
            conn.close()
    
    def verify_schema_integrity(self) -> Dict[str, any]:
        """
        🔍 VALIDACIÓN POST-MIGRACIÓN: Verificar integridad del schema (Nov 28, 2025)
        
        VALIDACIONES:
        1. Contar tablas activas (esperado: 28)
        2. Verificar user_contacts tiene datos migrados
        3. Confirmar Foreign Keys intactos
        4. Smoke queries en tablas críticas
        5. Validar que tablas legacy fueron eliminadas
        
        Returns:
            Dict con resultados de validación
        """
        if not self.db_url or not PSYCOPG_AVAILABLE:
            return {'success': False, 'error': 'Database not available'}
        
        conn = self._get_connection()
        if not conn:
            return {'success': False, 'error': 'Connection failed'}
        
        results = {
            'success': True,
            'validations': [],
            'errors': [],
            'warnings': []
        }
        
        try:
            cursor = conn.cursor()
            
            logger.info("🔍 INICIANDO VALIDACIÓN DE INTEGRIDAD DE SCHEMA...")
            logger.info("=" * 80)
            
            # ================================================
            # VALIDACIÓN 1: Contar tablas activas
            # ================================================
            logger.info("📊 VALIDACIÓN 1/5: Contando tablas activas...")
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                AND table_name NOT LIKE 'omnix_backup_%'
            """)
            
            total_tables = cursor.fetchone()[0]
            expected_tables = 29  # 28 + schema_migrations
            
            if total_tables == expected_tables:
                logger.info(f"   ✅ Total tablas: {total_tables} (esperado: {expected_tables})")
                results['validations'].append({'check': 'table_count', 'status': 'passed', 'value': total_tables})
            else:
                logger.warning(f"   ⚠️  Total tablas: {total_tables} (esperado: {expected_tables})")
                results['warnings'].append(f"Table count mismatch: {total_tables} vs {expected_tables}")
                results['validations'].append({'check': 'table_count', 'status': 'warning', 'value': total_tables})
            
            # ================================================
            # VALIDACIÓN 2: Verificar tablas legacy eliminadas
            # ================================================
            logger.info("🗑️  VALIDACIÓN 2/5: Verificando tablas legacy eliminadas...")
            
            legacy_tables = [
                'whatsapp_messages',
                'detected_patterns',
                'improvement_proposals',
                'monitoring_metrics',
                'ai_alerts'
            ]
            
            legacy_still_present = []
            for table_name in legacy_tables:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s AND table_schema = 'public'
                    )
                """, (table_name,))
                
                if cursor.fetchone()[0]:
                    legacy_still_present.append(table_name)
            
            if not legacy_still_present:
                logger.info(f"   ✅ Todas las tablas legacy eliminadas ({len(legacy_tables)})")
                results['validations'].append({'check': 'legacy_tables_removed', 'status': 'passed'})
            else:
                logger.warning(f"   ⚠️  Tablas legacy aún presentes: {legacy_still_present}")
                results['warnings'].append(f"Legacy tables not removed: {legacy_still_present}")
                results['validations'].append({'check': 'legacy_tables_removed', 'status': 'warning', 'remaining': legacy_still_present})
            
            # ================================================
            # VALIDACIÓN 3: Verificar user_contacts tiene datos
            # ================================================
            logger.info("📱 VALIDACIÓN 3/5: Verificando migración de contactos...")
            
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'whatsapp_number'
                )
            """)
            whatsapp_column_exists = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM user_contacts WHERE contact_type = 'whatsapp'")
            whatsapp_contacts_count = cursor.fetchone()[0]
            
            if not whatsapp_column_exists:
                logger.info(f"   ✅ Columna users.whatsapp_number eliminada")
                logger.info(f"   ✅ user_contacts tiene {whatsapp_contacts_count} contactos WhatsApp")
                results['validations'].append({
                    'check': 'whatsapp_migration', 
                    'status': 'passed', 
                    'migrated_contacts': whatsapp_contacts_count
                })
            else:
                logger.warning(f"   ⚠️  Columna users.whatsapp_number aún existe")
                results['warnings'].append("users.whatsapp_number column not removed")
                results['validations'].append({'check': 'whatsapp_migration', 'status': 'warning'})
            
            # ================================================
            # VALIDACIÓN 4: Verificar Foreign Keys críticos
            # ================================================
            logger.info("🔗 VALIDACIÓN 4/5: Verificando Foreign Keys...")
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.table_constraints 
                WHERE constraint_type = 'FOREIGN KEY' 
                AND table_schema = 'public'
            """)
            
            fk_count = cursor.fetchone()[0]
            
            if fk_count > 0:
                logger.info(f"   ✅ Foreign Keys activos: {fk_count}")
                results['validations'].append({'check': 'foreign_keys', 'status': 'passed', 'count': fk_count})
            else:
                logger.error(f"   ❌ No se encontraron Foreign Keys")
                results['errors'].append("No foreign keys found")
                results['validations'].append({'check': 'foreign_keys', 'status': 'failed'})
                results['success'] = False
            
            # ================================================
            # VALIDACIÓN 5: Smoke queries en tablas críticas
            # ================================================
            logger.info("🔥 VALIDACIÓN 5/5: Smoke queries en tablas críticas...")
            
            critical_tables = [
                'users',
                'trades',
                'risk_guardian_events',
                'derivatives_balances',
                'paper_trading_balances',
                'user_contacts',
                'schema_migrations'
            ]
            
            smoke_test_passed = 0
            for table_name in critical_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    logger.info(f"   ✅ {table_name}: {row_count} registros")
                    smoke_test_passed += 1
                except Exception as e:
                    logger.error(f"   ❌ {table_name}: Error - {e}")
                    results['errors'].append(f"Smoke test failed for {table_name}: {e}")
                    results['success'] = False
            
            results['validations'].append({
                'check': 'smoke_tests', 
                'status': 'passed' if smoke_test_passed == len(critical_tables) else 'failed',
                'passed': smoke_test_passed,
                'total': len(critical_tables)
            })
            
            # ================================================
            # RESUMEN FINAL
            # ================================================
            logger.info("=" * 80)
            if results['success']:
                logger.info("✅ VALIDACIÓN DE INTEGRIDAD: EXITOSA")
            else:
                logger.error("❌ VALIDACIÓN DE INTEGRIDAD: FALLÓ")
            
            logger.info(f"📊 Validaciones pasadas: {len([v for v in results['validations'] if v.get('status') == 'passed'])}/{len(results['validations'])}")
            
            if results['warnings']:
                logger.warning(f"⚠️  Advertencias: {len(results['warnings'])}")
                for warning in results['warnings']:
                    logger.warning(f"   - {warning}")
            
            if results['errors']:
                logger.error(f"❌ Errores: {len(results['errors'])}")
                for error in results['errors']:
                    logger.error(f"   - {error}")
            
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Error durante validación de integridad: {e}")
            results['success'] = False
            results['errors'].append(str(e))
        
        finally:
            conn.close()
        
        return results
    
    def _run_daily_cleanup(self):
        """
        🕐 CONTROL DE FRECUENCIA: Ejecutar cleanup 1x por día (Nov 26, 2025)
        
        Usa Redis para trackear última ejecución. Si Redis no está disponible,
        ejecuta cleanup de todos modos (fail-safe para prevenir crecimiento infinito).
        
        Key: db:last_cleanup_date
        Valor: ISO timestamp de última ejecución
        """
        try:
            should_cleanup = False
            
            if self.redis_client:
                try:
                    # Verificar última ejecución
                    last_cleanup = self.redis_client.get('db:last_cleanup_date')
                    
                    if not last_cleanup:
                        logger.info("🗑️ Primera ejecución de cleanup - ejecutando...")
                        should_cleanup = True
                    else:
                        # Parsear fecha y verificar si han pasado >24 horas
                        last_cleanup_dt = datetime.fromisoformat(last_cleanup)
                        hours_since_cleanup = (datetime.now() - last_cleanup_dt).total_seconds() / 3600
                        
                        if hours_since_cleanup >= 24:
                            logger.info(f"🗑️ Último cleanup hace {hours_since_cleanup:.1f}h - ejecutando...")
                            should_cleanup = True
                        else:
                            logger.info(f"✅ Cleanup reciente ({hours_since_cleanup:.1f}h atrás) - skip")
                            should_cleanup = False
                    
                except Exception as e:
                    logger.warning(f"⚠️  Error verificando Redis cleanup flag: {e}")
                    should_cleanup = True
            else:
                # Sin Redis, ejecutar cleanup siempre (fail-safe)
                logger.info("⚠️  Redis no disponible - ejecutando cleanup (fail-safe)")
                should_cleanup = True
            
            if should_cleanup:
                self._cleanup_old_data()
                
                # Actualizar timestamp en Redis
                if self.redis_client:
                    try:
                        self.redis_client.set('db:last_cleanup_date', datetime.now().isoformat())
                        logger.info("✅ Timestamp de cleanup actualizado en Redis")
                    except Exception as e:
                        logger.warning(f"⚠️  Error guardando timestamp en Redis: {e}")
        
        except Exception as e:
            logger.error(f"❌ Error en control de cleanup diario: {e}")
    
    def _cleanup_old_data(self):
        """
        🗑️ CLEANUP AUTOMÁTICO: Eliminar datos antiguos según TTL configurado (Nov 26, 2025)
        
        TTL Policy (Time To Live):
        - conversations, trades, risk_guardian_events: 30 días (datos operacionales)
        - trade_reasonings, trade_evaluations, balance_history: 90 días (datos de entrenamiento ML)
        - signal_executions, signal_votes: 60 días (datos de comunidad)
        - pending_evaluations (completed/failed): 7 días (limpieza de cola)
        
        Estrategia: DELETE directo basado en timestamp
        Ejecución: 1x por día (verificado con Redis flag)
        
        Beneficio: Previene crecimiento infinito (~95% reducción de espacio en 1 año)
        """
        if not self.db_url or not PSYCOPG_AVAILABLE:
            return
        
        conn = self._get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            logger.info("🗑️ Ejecutando cleanup automático de datos antiguos (TTL)...")
            
            # Configuración de TTL por tabla (días)
            # tabla: (días_ttl, columna_timestamp, condición_adicional)
            # FIXED Nov 26, 2025: Corregidos nombres de columnas (created_at vs timestamp)
            cleanup_config = {
                'conversations': (30, 'created_at', None),  # FIXED Nov 29: era 'timestamp'
                'trades': (30, 'timestamp', None),
                'risk_guardian_events': (30, 'created_at', None),  # FIXED Dec 5: era 'timestamp'
                'trade_reasonings': (90, 'created_at', None),  # FIXED: era 'timestamp'
                'trade_evaluations': (90, 'created_at', None),  # FIXED: era 'timestamp'
                'balance_history': (90, 'timestamp', None),
                'signal_executions': (60, 'executed_at', None),
                'signal_votes': (60, 'created_at', None),
                'whatsapp_messages': (30, 'timestamp', None),
                'analysis': (30, 'timestamp', None),
                
                # Cleanup especial para pending_evaluations
                'pending_evaluations': (7, 'created_at', "status IN ('completed', 'failed')"),  # FIXED: era 'timestamp'
            }
            
            total_deleted = 0
            tables_cleaned = 0
            
            for table_name, (ttl_days, timestamp_col, extra_condition) in cleanup_config.items():
                try:
                    # Verificar si tabla existe
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = %s AND table_schema = 'public'
                        )
                    """, (table_name,))
                    
                    if not cursor.fetchone()[0]:
                        continue
                    
                    # Verificar si columna timestamp existe (ADDED Dec 6, 2025 - defensive cleanup)
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name = %s AND column_name = %s
                        )
                    """, (table_name, timestamp_col))
                    
                    if not cursor.fetchone()[0]:
                        logger.debug(f"   ⏭️  Columna {timestamp_col} no existe en {table_name} (skip cleanup)")
                        continue
                    
                    # Construir query DELETE
                    delete_query = f"""
                        DELETE FROM {table_name}
                        WHERE {timestamp_col} < NOW() - INTERVAL '{ttl_days} days'
                    """
                    
                    if extra_condition:
                        delete_query += f" AND {extra_condition}"
                    
                    # Ejecutar DELETE y obtener count
                    cursor.execute(delete_query)
                    deleted_rows = cursor.rowcount
                    
                    if deleted_rows > 0:
                        logger.info(f"   ✅ {table_name}: {deleted_rows} registros eliminados (TTL: {ttl_days} días)")
                        total_deleted += deleted_rows
                        tables_cleaned += 1
                    
                except Exception as e:
                    logger.warning(f"   ⚠️  Error limpiando {table_name}: {e}")
                    continue
            
            conn.commit()
            
            if total_deleted > 0:
                logger.info(f"✅ Cleanup completado: {total_deleted} registros eliminados de {tables_cleaned} tablas")
                logger.info(f"   Espacio liberado estimado: ~{total_deleted * 2}KB")
            else:
                logger.info("✅ Cleanup ejecutado: No hay datos antiguos para eliminar")
            
        except Exception as e:
            logger.error(f"❌ Error en cleanup automático: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _init_tables(self):
        """Inicializar todas las tablas del sistema"""
        if not self.db_url or not PSYCOPG_AVAILABLE:
            return
        
        conn = self._get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            # Habilitar extensión UUID (si no existe)
            cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            
            # Tabla de usuarios (MEJORADA FASE 1 - Nov 26, 2025)
            # Mantiene user_id TEXT como PK para backward compatibility
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    language_code TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_trades INTEGER DEFAULT 0 CHECK (total_trades >= 0),
                    total_profit NUMERIC(18,8) DEFAULT 0,
                    risk_tolerance TEXT DEFAULT 'medium' 
                        CHECK (risk_tolerance IN ('low', 'medium', 'high', 'aggressive')),
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    whatsapp_number TEXT,
                    notifications_enabled BOOLEAN DEFAULT true,
                    email TEXT UNIQUE,
                    is_active BOOLEAN DEFAULT true,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # MIGRACIÓN: Agregar columnas faltantes a tabla users existente (Nov 29, 2025)
            # Esto es necesario porque CREATE TABLE IF NOT EXISTS no modifica tablas existentes
            migration_columns = [
                ("last_activity", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                ("whatsapp_number", "TEXT"),
                ("notifications_enabled", "BOOLEAN DEFAULT true"),
                ("email", "TEXT"),
                ("is_active", "BOOLEAN DEFAULT true"),
                ("updated_at", "TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"),
                ("total_trades", "INTEGER DEFAULT 0"),
                ("total_profit", "NUMERIC(18,8) DEFAULT 0"),
                ("risk_tolerance", "TEXT DEFAULT 'medium'")
            ]
            
            for col_name, col_def in migration_columns:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_def}")
                except Exception as col_err:
                    pass  # Silently ignore if column exists or can't be added
            
            # Índices estratégicos para users
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_last_activity ON users(last_activity DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = true')
            
            # Tabla de contactos de usuario (NUEVA - Nov 26, 2025)
            # FK a users.user_id TEXT (backward compatible)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_contacts (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    contact_type TEXT NOT NULL 
                        CHECK (contact_type IN ('whatsapp', 'telegram', 'email', 'phone', 'sms')),
                    contact_value TEXT NOT NULL,
                    is_verified BOOLEAN DEFAULT false,
                    verified_at TIMESTAMP WITH TIME ZONE,
                    is_primary BOOLEAN DEFAULT false,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, contact_type, contact_value)
                )
            ''')
            
            # Índices para user_contacts
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_contacts_user ON user_contacts(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_contacts_type ON user_contacts(contact_type, is_verified)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_contacts_primary ON user_contacts(user_id, is_primary) WHERE is_primary = true')
            
            # Tabla de trades ejecutados
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    symbol TEXT,
                    side TEXT,
                    amount REAL,
                    price REAL,
                    total_cost REAL,
                    status TEXT,
                    order_id TEXT,
                    exchange TEXT,
                    profit_loss REAL DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de análisis
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    symbol TEXT,
                    analysis_type TEXT,
                    result TEXT,
                    confidence REAL,
                    recommendation TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de conversaciones IA
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    user_message TEXT,
                    ai_response TEXT,
                    language TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de contactos de usuario (NUEVA - Nov 26, 2025 + Migración Agresiva Nov 28, 2025)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_contacts (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    contact_type TEXT NOT NULL 
                        CHECK (contact_type IN ('whatsapp', 'telegram', 'email', 'phone', 'sms')),
                    contact_value TEXT NOT NULL,
                    is_verified BOOLEAN DEFAULT false,
                    verified_at TIMESTAMP WITH TIME ZONE,
                    is_primary BOOLEAN DEFAULT false,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, contact_type, contact_value)
                )
            ''')
            
            # Índices para user_contacts
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_contacts_user ON user_contacts(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_contacts_type ON user_contacts(contact_type, is_verified)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_contacts_primary ON user_contacts(user_id, is_primary) WHERE is_primary = true')
            
            # Tabla de validaciones Sharia
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sharia_validations (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT,
                    status TEXT,
                    reasoning TEXT,
                    scholar_consensus INTEGER,
                    uae_approval BOOLEAN,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de balance histórico
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS balance_history (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    exchange TEXT DEFAULT 'kraken',
                    total_usd REAL,
                    btc_balance REAL DEFAULT 0,
                    eth_balance REAL DEFAULT 0,
                    usdt_balance REAL DEFAULT 0,
                    other_balance REAL DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ==========================================
            # PAPER TRADING TABLES - INSTITUTIONAL GRADE
            # ==========================================
            
            # Tabla de balances de paper trading (1 row por usuario)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS paper_trading_balances (
                    user_id TEXT PRIMARY KEY,
                    balance_usd NUMERIC(18,8) DEFAULT 1000000.00,
                    btc_balance NUMERIC(20,10) DEFAULT 0,
                    eth_balance NUMERIC(20,10) DEFAULT 0,
                    available_margin_usd NUMERIC(18,8) DEFAULT 1000000.00,
                    total_trades INTEGER DEFAULT 0,
                    winning_trades INTEGER DEFAULT 0,
                    losing_trades INTEGER DEFAULT 0,
                    total_realized_pnl_usd NUMERIC(18,8) DEFAULT 0,
                    total_unrealized_pnl_usd NUMERIC(18,8) DEFAULT 0,
                    max_drawdown_pct NUMERIC(6,4) DEFAULT 0,
                    sharpe_ratio NUMERIC(8,4) DEFAULT 0,
                    last_mark_to_market_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Índices para paper_trading_balances
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_paper_balances_total_pnl 
                ON paper_trading_balances(total_realized_pnl_usd DESC)
            ''')
            
            # Tabla de trades de paper trading (granular ledger)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS paper_trading_trades (
                    id BIGSERIAL PRIMARY KEY,
                    trade_uuid UUID UNIQUE DEFAULT gen_random_uuid(),
                    user_id TEXT NOT NULL,
                    position_id UUID,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
                    order_type TEXT DEFAULT 'market',
                    status TEXT DEFAULT 'filled',
                    entry_price NUMERIC(18,8) NOT NULL,
                    exit_price NUMERIC(18,8),
                    base_quantity NUMERIC(20,10) NOT NULL,
                    quote_notional_usd NUMERIC(18,8) NOT NULL,
                    fee_bps NUMERIC(6,4) DEFAULT 26.0,
                    fee_usd NUMERIC(18,8) NOT NULL,
                    gross_pnl_usd NUMERIC(18,8) DEFAULT 0,
                    net_realized_pnl_usd NUMERIC(18,8),
                    unrealized_pnl_usd NUMERIC(18,8),
                    opened_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP WITH TIME ZONE,
                    duration_seconds INTEGER,
                    source_strategy TEXT DEFAULT 'auto_trading_bot',
                    notes JSONB,
                    is_paper_trade BOOLEAN DEFAULT TRUE,
                    CONSTRAINT check_exit_price_on_close CHECK (
                        (closed_at IS NULL AND exit_price IS NULL) OR
                        (closed_at IS NOT NULL AND exit_price IS NOT NULL)
                    )
                )
            ''')
            
            # Índices para paper_trading_trades
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_paper_trades_user_opened 
                ON paper_trading_trades(user_id, opened_at DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_paper_trades_open_positions 
                ON paper_trading_trades(user_id, closed_at) WHERE closed_at IS NULL
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_paper_trades_symbol 
                ON paper_trading_trades(symbol)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_paper_trades_opened_at 
                ON paper_trading_trades USING BRIN (opened_at)
            ''')
            
            # ==========================================
            # CONVERSATIONAL BRAIN TABLES - ÚNICO EN EL MUNDO
            # ==========================================
            
            # Tabla de razonamientos pre-trade (el bot explica por qué decide)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trade_reasonings (
                    id BIGSERIAL PRIMARY KEY,
                    trade_uuid UUID UNIQUE DEFAULT gen_random_uuid(),
                    user_id TEXT,
                    trade_id TEXT,
                    order_id TEXT,
                    action TEXT NOT NULL CHECK (action IN ('BUY', 'SELL')),
                    pair TEXT NOT NULL,
                    amount_usd NUMERIC(18,8) NOT NULL,
                    confidence NUMERIC(5,4) NOT NULL,
                    signals JSONB NOT NULL,
                    reasons JSONB NOT NULL,
                    summary TEXT,
                    full_explanation TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_trade_reasonings_user_created 
                ON trade_reasonings(user_id, created_at DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_trade_reasonings_pair 
                ON trade_reasonings(pair)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_trade_reasonings_trade_id 
                ON trade_reasonings(trade_id, created_at DESC)
            ''')
            
            # Tabla de auto-evaluaciones post-trade (el bot se pregunta si fue buena decisión)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trade_evaluations (
                    id BIGSERIAL PRIMARY KEY,
                    evaluation_uuid UUID UNIQUE DEFAULT gen_random_uuid(),
                    trade_id TEXT NOT NULL,
                    trade_reasoning_uuid UUID REFERENCES trade_reasonings(trade_uuid),
                    user_id TEXT,
                    elapsed_minutes INTEGER,
                    original_action TEXT,
                    original_confidence NUMERIC(5,4),
                    result JSONB NOT NULL,
                    was_correct BOOLEAN NOT NULL,
                    learning_points JSONB,
                    adjustments_suggested JSONB,
                    full_review TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Migration: add was_correct column BEFORE creating indexes that reference it
            cursor.execute("""
                ALTER TABLE trade_evaluations
                ADD COLUMN IF NOT EXISTS was_correct BOOLEAN NOT NULL DEFAULT FALSE
            """)
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_trade_evaluations_user_created 
                ON trade_evaluations(user_id, created_at DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_trade_evaluations_correctness 
                ON trade_evaluations(was_correct)
            ''')
            
            # Tabla de evaluaciones pendientes (sistema robusto sin threads)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pending_evaluations (
                    id BIGSERIAL PRIMARY KEY,
                    trade_id TEXT NOT NULL,
                    trade_reasoning_uuid UUID,
                    user_id TEXT,
                    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
                    result JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP WITH TIME ZONE
                )
            ''')

            # Migration: add scheduled_at column BEFORE creating indexes that reference it
            cursor.execute("""
                ALTER TABLE pending_evaluations
                ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            """)

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_pending_evaluations_scheduled 
                ON pending_evaluations(scheduled_at) WHERE status = 'pending'
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_pending_evaluations_trade 
                ON pending_evaluations(trade_id, status)
            ''')
            
            # ==========================================
            # COMMUNITY INTELLIGENCE TABLES - CROWDSOURCING
            # ==========================================
            
            # Tabla de feedback comunitario
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS community_feedback (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    username TEXT,
                    feedback_type TEXT NOT NULL,
                    signal_type TEXT,
                    strategy TEXT,
                    symbol TEXT,
                    result TEXT NOT NULL,
                    market_condition TEXT,
                    btc_price REAL,
                    volatility TEXT,
                    timeframe TEXT,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_verified BOOLEAN DEFAULT false,
                    helpful_votes INTEGER DEFAULT 0
                )
            ''')
            
            # Tabla de votos de estrategias
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategy_votes (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    vote INTEGER NOT NULL,
                    reason TEXT,
                    market_condition TEXT,
                    vote_date DATE DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, strategy, vote_date)
                )
            ''')
            
            # Tabla de contribuciones de usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_contributions (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    total_feedback INTEGER DEFAULT 0,
                    helpful_feedback INTEGER DEFAULT 0,
                    total_votes INTEGER DEFAULT 0,
                    proposals_submitted INTEGER DEFAULT 0,
                    proposals_accepted INTEGER DEFAULT 0,
                    contribution_points INTEGER DEFAULT 0,
                    contribution_level TEXT DEFAULT 'Novato',
                    badges TEXT DEFAULT '[]',
                    first_contribution TIMESTAMP,
                    last_contribution TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de patrones detectados por AI
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detected_patterns (
                    id SERIAL PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    symbol TEXT,
                    pattern_data JSONB NOT NULL,
                    confidence REAL,
                    timeframe TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            ''')
            
            # Tabla de propuestas de mejora
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS improvement_proposals (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    proposal_type TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    expected_impact TEXT,
                    status TEXT DEFAULT 'pending',
                    votes INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP
                )
            ''')
            
            # Migration: add strategy column BEFORE creating indexes that reference it
            cursor.execute("""
                ALTER TABLE community_feedback
                ADD COLUMN IF NOT EXISTS strategy TEXT
            """)
            cursor.execute("""
                ALTER TABLE strategy_votes
                ADD COLUMN IF NOT EXISTS strategy TEXT NOT NULL DEFAULT ''
            """)

            # Índices para Community Intelligence
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_user ON community_feedback(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_strategy ON community_feedback(strategy)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_result ON community_feedback(result)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_votes_strategy ON strategy_votes(strategy)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_detected_patterns_type ON detected_patterns(pattern_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_improvement_proposals_user ON improvement_proposals(user_id)')
            
            # ==========================================
            # SIGNAL CONTRIBUTION TABLES - CROWDSOURCING ALPHA
            # ==========================================
            
            # Tabla de señales compartidas por usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS community_signals (
                    id SERIAL PRIMARY KEY,
                    signal_id TEXT UNIQUE NOT NULL,
                    contributor_id TEXT NOT NULL,
                    contributor_name TEXT,
                    
                    -- Señal
                    symbol TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    entry_price REAL,
                    target_price REAL,
                    stop_loss REAL,
                    timeframe TEXT DEFAULT '1h',
                    confidence INTEGER DEFAULT 50,
                    
                    -- Análisis
                    reasoning TEXT,
                    indicators_used TEXT,
                    market_condition TEXT,
                    
                    -- Tracking
                    status TEXT DEFAULT 'active',
                    executions_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    
                    -- Votos
                    upvotes INTEGER DEFAULT 0,
                    downvotes INTEGER DEFAULT 0,
                    
                    -- Resultado final
                    final_result TEXT,
                    actual_return REAL,
                    closed_at TIMESTAMP,
                    
                    -- Royalties
                    royalties_earned INTEGER DEFAULT 0,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            ''')
            
            # Tabla de ejecuciones de señales
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signal_executions (
                    id SERIAL PRIMARY KEY,
                    signal_id TEXT NOT NULL,
                    executor_id TEXT NOT NULL,
                    executor_name TEXT,
                    
                    entry_price REAL,
                    exit_price REAL,
                    result TEXT,
                    profit_pct REAL,
                    
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    
                    feedback TEXT,
                    rating INTEGER
                )
            ''')
            
            # Tabla de votos de señales
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signal_votes (
                    id SERIAL PRIMARY KEY,
                    signal_id TEXT NOT NULL,
                    voter_id TEXT NOT NULL,
                    vote_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(signal_id, voter_id)
                )
            ''')
            
            # Tabla de leaderboard de alpha
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alpha_leaderboard (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT UNIQUE NOT NULL,
                    username TEXT,
                    
                    -- Stats
                    signals_shared INTEGER DEFAULT 0,
                    signals_successful INTEGER DEFAULT 0,
                    total_executions INTEGER DEFAULT 0,
                    win_rate REAL DEFAULT 0,
                    avg_return REAL DEFAULT 0,
                    
                    -- Puntos
                    royalty_points INTEGER DEFAULT 0,
                    reputation_score REAL DEFAULT 50,
                    
                    -- Ranking
                    rank_position INTEGER,
                    rank_tier TEXT DEFAULT 'Bronze',
                    
                    last_signal_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ==========================================
            # AI RISK GUARDIAN TABLE - MONITORING
            # ==========================================
            
            # Tabla de eventos del AI Risk Guardian
            # Note: Uses event_type/severity columns (not risk_type/risk_level)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_guardian_events (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    event_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    description TEXT NOT NULL,
                    action_taken VARCHAR(100) NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
            ''')
            
            # Índices para risk_guardian_events
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_events_created ON risk_guardian_events(created_at DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_events_event_type ON risk_guardian_events(event_type)')
            
            # ==========================================
            # RISK MANAGEMENT SYSTEM (RMS) TABLES
            # Nov 27, 2025 - Institutional Risk Control
            # ==========================================
            
            # Tabla de configuración de límites de riesgo por usuario
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_limits (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    limit_type VARCHAR(50) NOT NULL,
                    threshold_value NUMERIC(18,8) NOT NULL,
                    threshold_unit VARCHAR(20) NOT NULL DEFAULT 'PERCENT',
                    warning_threshold_pct NUMERIC(8,4) DEFAULT 80.0,
                    is_active BOOLEAN DEFAULT true,
                    cooldown_minutes INTEGER DEFAULT 60,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, limit_type)
                )
            ''')
            
            # Tabla de violaciones de límites
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_limit_breaches (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    limit_id INTEGER REFERENCES risk_limits(id) ON DELETE SET NULL,
                    limit_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) NOT NULL,
                    current_value NUMERIC(18,8),
                    threshold_value NUMERIC(18,8),
                    percentage_used NUMERIC(8,4),
                    action_taken VARCHAR(100),
                    description TEXT,
                    metadata JSONB,
                    resolved_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de snapshots de métricas de riesgo
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_metrics_snapshots (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    snapshot_date DATE NOT NULL,
                    total_balance_usd NUMERIC(18,8),
                    total_exposure_usd NUMERIC(18,8),
                    available_balance_usd NUMERIC(18,8),
                    daily_pnl_usd NUMERIC(18,8),
                    daily_pnl_pct NUMERIC(8,4),
                    max_drawdown_usd NUMERIC(18,8),
                    max_drawdown_pct NUMERIC(8,4),
                    current_drawdown_pct NUMERIC(8,4),
                    max_single_position_pct NUMERIC(8,4),
                    open_positions INTEGER DEFAULT 0,
                    daily_trades_count INTEGER DEFAULT 0,
                    volatility_index NUMERIC(8,4),
                    risk_score INTEGER DEFAULT 0,
                    positions_breakdown JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, snapshot_date)
                )
            ''')
            
            # Tabla de estado del circuit breaker
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS circuit_breaker_status (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL UNIQUE,
                    is_halted BOOLEAN DEFAULT false,
                    reason VARCHAR(50),
                    message TEXT,
                    halted_at TIMESTAMP WITH TIME ZONE,
                    resume_at TIMESTAMP WITH TIME ZONE,
                    halted_by VARCHAR(100) DEFAULT 'system',
                    can_override BOOLEAN DEFAULT true,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Índices para RMS Tables
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_limits_user ON risk_limits(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_breaches_user ON risk_limit_breaches(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_breaches_created ON risk_limit_breaches(created_at DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_breaches_severity ON risk_limit_breaches(severity)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_snapshots_user_date ON risk_metrics_snapshots(user_id, snapshot_date DESC)')
            
            logger.info("✅ RMS Tables creadas (risk_limits, risk_limit_breaches, risk_metrics_snapshots, circuit_breaker_status)")
            
            # ==========================================
            # ÍNDICES PARA FOREIGN KEYS (Performance)
            # Nov 26, 2025 - Optimize JOINs and FK lookups
            # ==========================================
            logger.info("🔍 Creando índices en columnas FK para optimizar performance...")
            
            # Core System Tables
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_user_id ON analysis(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_whatsapp_user_id ON whatsapp_messages(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_balance_history_user_id ON balance_history(user_id)')
            
            # Paper Trading Tables (user_id ya indexado en paper_trading_trades)
            # paper_trading_trades ya tiene idx_paper_trades_user_opened
            
            # Conversational Brain Tables
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trade_reasonings_user_id ON trade_reasonings(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trade_evaluations_user_id ON trade_evaluations(user_id)')
            
            # Community Intelligence Tables
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_community_feedback_user_id ON community_feedback(user_id)')
            
            # Signal Contribution Tables
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_community_signals_contributor ON community_signals(contributor_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_signal_executions_executor ON signal_executions(executor_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_signal_executions_signal ON signal_executions(signal_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_signal_votes_voter ON signal_votes(voter_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_signal_votes_signal ON signal_votes(signal_id)')
            
            # Risk Guardian Table
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_events_user_id ON risk_guardian_events(user_id)')
            
            # alpha_leaderboard.user_id ya tiene UNIQUE constraint (no necesita índice adicional)
            
            logger.info("✅ Índices FK creados (mejora 10x en queries con JOIN)")
            
            # ==========================================
            # ÍNDICES COMPUESTOS (user_id + timestamp)
            # Nov 26, 2025 - Optimize historical queries
            # ==========================================
            logger.info("🔍 Creando índices compuestos para queries de historial...")
            
            # Optimizar queries tipo: "Dame trades del usuario X ordenados por fecha"
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_trades_user_timestamp 
                ON trades(user_id, timestamp DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_conversations_user_created 
                ON conversations(user_id, created_at DESC)
            ''')  # FIXED Nov 29: era 'timestamp' pero tabla usa 'created_at'
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_balance_history_user_timestamp 
                ON balance_history(user_id, timestamp DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_trade_reasonings_user_created 
                ON trade_reasonings(user_id, created_at DESC)
            ''')  # FIXED Nov 26, 2025: era 'timestamp' pero tabla usa 'created_at'
            
            # Índice en users.last_activity para queries de "usuarios activos"
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_last_activity 
                ON users(last_activity DESC)
            ''')
            
            logger.info("✅ Índices compuestos creados (optimiza queries con filtro + ordenamiento)")
            
            # ==========================================
            # DERIVATIVES TRADING TABLES - INSTITUTIONAL
            # Nov 28, 2025 - Perpetuals & Futures Module
            # ==========================================
            
            # Tabla de balances de derivados (paper trading perpetuos)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS derivatives_balances (
                    user_id TEXT PRIMARY KEY,
                    balance_usd NUMERIC(18,8) DEFAULT 100000.00,
                    margin_used NUMERIC(18,8) DEFAULT 0,
                    available_margin NUMERIC(18,8) DEFAULT 100000.00,
                    unrealized_pnl NUMERIC(18,8) DEFAULT 0,
                    total_realized_pnl NUMERIC(18,8) DEFAULT 0,
                    total_funding_paid NUMERIC(18,8) DEFAULT 0,
                    total_fees_paid NUMERIC(18,8) DEFAULT 0,
                    max_leverage NUMERIC(4,2) DEFAULT 3.00,
                    total_trades INTEGER DEFAULT 0,
                    winning_trades INTEGER DEFAULT 0,
                    losing_trades INTEGER DEFAULT 0,
                    max_drawdown_pct NUMERIC(8,4) DEFAULT 0,
                    peak_balance NUMERIC(18,8) DEFAULT 100000.00,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de trades de derivados (perpetuos)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS derivatives_trades (
                    id BIGSERIAL PRIMARY KEY,
                    trade_id TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL CHECK (side IN ('long', 'short')),
                    size NUMERIC(20,10) NOT NULL,
                    entry_price NUMERIC(18,8) NOT NULL,
                    exit_price NUMERIC(18,8),
                    leverage NUMERIC(4,2) NOT NULL DEFAULT 1.00,
                    margin_used NUMERIC(18,8) NOT NULL,
                    liquidation_price NUMERIC(18,8),
                    order_type TEXT DEFAULT 'market',
                    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'closed', 'liquidated', 'cancelled')),
                    pnl NUMERIC(18,8) DEFAULT 0,
                    pnl_pct NUMERIC(10,6) DEFAULT 0,
                    funding_paid NUMERIC(18,8) DEFAULT 0,
                    fees_paid NUMERIC(18,8) DEFAULT 0,
                    close_reason TEXT,
                    opened_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Índices para derivatives_trades
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_deriv_trades_user ON derivatives_trades(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_deriv_trades_symbol ON derivatives_trades(symbol)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_deriv_trades_status ON derivatives_trades(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_deriv_trades_user_opened ON derivatives_trades(user_id, opened_at DESC)')
            
            # Tabla de posiciones abiertas de derivados
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS derivatives_positions (
                    position_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL CHECK (side IN ('long', 'short')),
                    size NUMERIC(20,10) NOT NULL,
                    entry_price NUMERIC(18,8) NOT NULL,
                    leverage NUMERIC(4,2) NOT NULL,
                    margin_used NUMERIC(18,8) NOT NULL,
                    liquidation_price NUMERIC(18,8),
                    unrealized_pnl NUMERIC(18,8) DEFAULT 0,
                    funding_accumulated NUMERIC(18,8) DEFAULT 0,
                    opened_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    last_update TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, symbol)
                )
            ''')
            
            # Índice para posiciones
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_deriv_positions_user ON derivatives_positions(user_id)')
            
            # Tabla de funding rates históricos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS derivatives_funding_log (
                    id BIGSERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    position_id TEXT,
                    symbol TEXT NOT NULL,
                    funding_rate NUMERIC(12,8) NOT NULL,
                    funding_amount NUMERIC(18,8) NOT NULL,
                    side TEXT,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Índice para funding log
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_funding_log_user ON derivatives_funding_log(user_id, timestamp DESC)')
            
            # Tabla de hedges activos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS derivatives_hedges (
                    hedge_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    spot_symbol TEXT NOT NULL,
                    spot_size NUMERIC(20,10) NOT NULL,
                    spot_value NUMERIC(18,8) NOT NULL,
                    hedge_symbol TEXT NOT NULL,
                    hedge_size NUMERIC(20,10) NOT NULL,
                    hedge_entry_price NUMERIC(18,8) NOT NULL,
                    coverage_ratio NUMERIC(6,4) NOT NULL,
                    hedge_type TEXT DEFAULT 'partial',
                    delta NUMERIC(18,8) DEFAULT 0,
                    pnl NUMERIC(18,8) DEFAULT 0,
                    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'closed', 'rebalancing')),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    last_rebalance TIMESTAMP WITH TIME ZONE,
                    closed_at TIMESTAMP WITH TIME ZONE
                )
            ''')
            
            # Índice para hedges
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_hedges_user ON derivatives_hedges(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_hedges_status ON derivatives_hedges(status)')
            
            # Tabla de oportunidades de funding arbitrage
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS derivatives_funding_opportunities (
                    id BIGSERIAL PRIMARY KEY,
                    opportunity_id TEXT UNIQUE NOT NULL,
                    symbol TEXT NOT NULL,
                    funding_rate NUMERIC(12,8) NOT NULL,
                    funding_rate_annual NUMERIC(10,6) NOT NULL,
                    spot_price NUMERIC(18,8) NOT NULL,
                    perp_price NUMERIC(18,8) NOT NULL,
                    basis NUMERIC(10,6) NOT NULL,
                    expected_return_annual NUMERIC(10,6) NOT NULL,
                    risk_score NUMERIC(6,2) DEFAULT 0,
                    status TEXT DEFAULT 'detected' CHECK (status IN ('detected', 'executing', 'active', 'closed', 'missed')),
                    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP WITH TIME ZONE
                )
            ''')
            
            # Índice para oportunidades
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_funding_opp_status ON derivatives_funding_opportunities(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_funding_opp_symbol ON derivatives_funding_opportunities(symbol)')
            
            logger.info("✅ Derivatives Tables creadas (derivatives_balances, derivatives_trades, derivatives_positions, derivatives_funding_log, derivatives_hedges, derivatives_funding_opportunities)")
            
            # Tabla de caché de transcripciones de video
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS video_transcript_cache (
                    video_id TEXT PRIMARY KEY,
                    transcript TEXT NOT NULL,
                    source TEXT DEFAULT 'whisper',
                    duration_seconds INTEGER,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days')
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transcript_expires ON video_transcript_cache(expires_at)')
            
            logger.info("✅ Video Transcript Cache Table creada")
            
            # ========================================
            # ADAPTIVE PARAMETER ENGINE TABLES
            # Tablas para auto-calibración dinámica de estrategias ARES
            # ========================================
            
            # Tabla de perfiles de parámetros adaptativos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS adaptive_parameters (
                    id BIGSERIAL PRIMARY KEY,
                    strategy_name TEXT NOT NULL,
                    stop_loss_pct NUMERIC(8,5) NOT NULL DEFAULT -0.28,
                    take_profit_pct NUMERIC(8,5) NOT NULL DEFAULT 0.85,
                    position_size_factor NUMERIC(6,4) NOT NULL DEFAULT 1.0,
                    timeout_minutes INTEGER NOT NULL DEFAULT 60,
                    entry_threshold NUMERIC(6,4) NOT NULL DEFAULT 0.70,
                    sensitivity_coefficient NUMERIC(6,4) NOT NULL DEFAULT 1.0,
                    calibration_count INTEGER NOT NULL DEFAULT 0,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(strategy_name, is_active)
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_adaptive_params_strategy ON adaptive_parameters(strategy_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_adaptive_params_active ON adaptive_parameters(is_active)')
            
            # Tabla de eventos de calibración
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calibration_events (
                    id BIGSERIAL PRIMARY KEY,
                    event_id TEXT UNIQUE NOT NULL,
                    strategy TEXT NOT NULL,
                    regime TEXT NOT NULL,
                    regime_confidence NUMERIC(6,4) NOT NULL,
                    previous_params JSONB NOT NULL,
                    new_params JSONB NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('pending', 'applied', 'rejected_cooldown', 'rejected_risk', 'rejected_coherence', 'rolled_back')),
                    reason TEXT,
                    microstructure_context JSONB,
                    performance_window JSONB,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_calibration_strategy ON calibration_events(strategy, timestamp DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_calibration_status ON calibration_events(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_calibration_regime ON calibration_events(regime)')
            
            # Tabla de métricas de calibración (para machine learning)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calibration_metrics (
                    id BIGSERIAL PRIMARY KEY,
                    strategy TEXT NOT NULL,
                    regime TEXT NOT NULL,
                    calibration_event_id TEXT REFERENCES calibration_events(event_id),
                    trades_after INTEGER DEFAULT 0,
                    pnl_after NUMERIC(18,8) DEFAULT 0,
                    win_rate_after NUMERIC(6,4),
                    avg_trade_duration INTEGER,
                    parameter_effectiveness NUMERIC(6,4),
                    measured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cal_metrics_strategy ON calibration_metrics(strategy)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cal_metrics_regime ON calibration_metrics(regime)')
            
            logger.info("✅ Adaptive Parameter Engine Tables creadas (adaptive_parameters, calibration_events, calibration_metrics)")

            # ── ADR-050: Context Admission Gate — session_admission_events ──────
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_admission_events (
                    id BIGSERIAL PRIMARY KEY,
                    event_id TEXT UNIQUE NOT NULL,
                    session_id TEXT DEFAULT '',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    admitted BOOLEAN NOT NULL,
                    decision TEXT DEFAULT '',
                    admission_score NUMERIC(6,2) NOT NULL DEFAULT 100.0,
                    violation TEXT DEFAULT '',
                    reason_code TEXT DEFAULT '',
                    global_volatility NUMERIC(6,2) DEFAULT 0.0,
                    cross_pair_correlation NUMERIC(6,2) DEFAULT 0.0,
                    correlation_score NUMERIC(6,2) DEFAULT 0.0,
                    liquidity_score NUMERIC(6,2) DEFAULT 100.0,
                    macro_risk NUMERIC(6,2) DEFAULT 0.0,
                    macro_risk_score NUMERIC(6,2) DEFAULT 0.0,
                    parameters_snapshot JSONB DEFAULT '{}',
                    cag_config JSONB DEFAULT '{}',
                    gate_checks JSONB DEFAULT '[]',
                    receipt_id TEXT DEFAULT '',
                    user_id TEXT DEFAULT '',
                    symbol TEXT DEFAULT ''
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_admission_created ON session_admission_events(created_at DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_admission_admitted ON session_admission_events(admitted)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_admission_violation ON session_admission_events(violation) WHERE violation != \'\'')
            logger.info("✅ CAG Table creada: session_admission_events (ADR-050)")
            # ──────────────────────────────────────────────────────────────────
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("✅ PostgreSQL: 24 tablas inicializadas (Core + Paper Trading + Cerebro + Community Intelligence + Signal Contribution + Risk Guardian + CAG)")
            
        except Exception as e:
            logger.error(f"Error inicializando tablas: {e}")
            if conn:
                conn.close()
    
    def save_balance_snapshot(self, user_id: str, balance_data: Dict) -> bool:
        """
        Guardar snapshot del balance
        
        Args:
            user_id: ID del usuario
            balance_data: Dict con total_usd, btc_balance, etc.
            
        Returns:
            True si exitoso, False si falla
        """
        if not self.connected:
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO balance_history (user_id, exchange, total_usd, btc_balance, eth_balance, usdt_balance, other_balance)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (
                user_id,
                balance_data.get('exchange', 'kraken'),
                balance_data.get('total_usd', 0),
                balance_data.get('btc_balance', 0),
                balance_data.get('eth_balance', 0),
                balance_data.get('usdt_balance', 0),
                balance_data.get('other_balance', 0)
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"✅ Balance snapshot guardado: ${balance_data.get('total_usd', 0):,.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando balance: {e}")
            return False

    def log_session_admission_event(
        self,
        event_id: str,
        admitted: bool,
        admission_score: float,
        violation: str = "",
        global_volatility: float = 0.0,
        cross_pair_correlation: float = 0.0,
        liquidity_score: float = 100.0,
        macro_risk: float = 0.0,
        cag_config: dict = None,
        gate_checks: list = None,
        receipt_id: str = "",
        user_id: str = "",
        symbol: str = "",
        session_id: str = "",
    ) -> bool:
        """
        Persist a CAG session admission event to session_admission_events.
        ADR-050: Context Admission Gate — fail-safe, non-critical.

        Returns True if stored, False on error (pipeline continues regardless).
        """
        if not self.connected:
            return False

        import json

        decision_str = "ADMITTED" if admitted else "BLOCKED"
        reason_code = violation or ""
        parameters_snapshot = {
            "global_volatility": round(global_volatility, 2),
            "cross_pair_correlation": round(cross_pair_correlation, 2),
            "liquidity_score": round(liquidity_score, 2),
            "macro_risk": round(macro_risk, 2),
        }

        try:
            conn = self._get_connection()
            if not conn:
                return False

            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO session_admission_events
                    (event_id, session_id, admitted, decision, admission_score,
                     violation, reason_code,
                     global_volatility, cross_pair_correlation, correlation_score,
                     liquidity_score, macro_risk, macro_risk_score,
                     parameters_snapshot, cag_config, gate_checks,
                     receipt_id, user_id, symbol)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (event_id) DO NOTHING
                """,
                (
                    event_id,
                    session_id or event_id,
                    admitted,
                    decision_str,
                    round(admission_score, 2),
                    reason_code,
                    reason_code,
                    round(global_volatility, 2),
                    round(cross_pair_correlation, 2),
                    round(cross_pair_correlation, 2),
                    round(liquidity_score, 2),
                    round(macro_risk, 2),
                    round(macro_risk, 2),
                    json.dumps(parameters_snapshot),
                    json.dumps(cag_config or {}),
                    json.dumps(gate_checks or []),
                    receipt_id or "",
                    user_id or "",
                    symbol or "",
                ),
            )
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(
                f"🔒 [CAG] session_admission_events persisted: {event_id} | "
                f"{decision_str} | score={admission_score:.0f}/100"
            )
            return True

        except Exception as e:
            logger.warning(f"⚠️ [CAG] log_session_admission_event failed (non-critical): {e}")
            return False

    def get_balance_history(self, user_id: str, days: int = 30) -> List[Dict]:
        """
        Obtener historial de balance
        
        Args:
            user_id: ID del usuario
            days: Días a consultar
            
        Returns:
            Lista de balances históricos
        """
        if not self.connected:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT total_usd, btc_balance, eth_balance, usdt_balance, other_balance, timestamp
                FROM balance_history
                WHERE user_id = %s AND timestamp >= NOW() - INTERVAL '1 day' * %s
                ORDER BY timestamp ASC
            ''', (user_id, days))
            
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            history = []
            for row in rows:
                history.append({
                    'total_usd': float(row[0]) if row[0] else 0,
                    'btc_balance': float(row[1]) if row[1] else 0,
                    'eth_balance': float(row[2]) if row[2] else 0,
                    'usdt_balance': float(row[3]) if row[3] else 0,
                    'other_balance': float(row[4]) if row[4] else 0,
                    'timestamp': row[5].isoformat() if row[5] else None
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error obteniendo history: {e}")
            return []
    
    def calculate_performance_metrics(self, history: List[Dict]) -> Optional[Dict]:
        """
        Calcular métricas de performance institucionales
        
        Args:
            history: Lista de balance histórico
            
        Returns:
            Dict con ROI, CAGR, Max Drawdown, etc.
        """
        if not history or len(history) < 2:
            return None
        
        try:
            initial_balance = history[0]['total_usd']
            current_balance = history[-1]['total_usd']
            
            # ROI
            roi_percent = ((current_balance - initial_balance) / initial_balance) * 100 if initial_balance > 0 else 0
            
            # Profit/Loss
            profit_loss = current_balance - initial_balance
            
            # Max Drawdown (peak-to-valley)
            peak = history[0]['total_usd']
            max_drawdown = 0
            
            for entry in history:
                balance = entry['total_usd']
                if balance > peak:
                    peak = balance
                if peak > 0:
                    current_drawdown = ((peak - balance) / peak) * 100
                    if current_drawdown > max_drawdown:
                        max_drawdown = current_drawdown
            
            # Max balance
            max_balance = max([h['total_usd'] for h in history])
            
            # Días tracking
            start_date = datetime.fromisoformat(history[0]['timestamp'])
            end_date = datetime.fromisoformat(history[-1]['timestamp'])
            days_tracked = (end_date - start_date).days
            
            # CAGR anualizado
            if days_tracked > 0:
                years = days_tracked / 365.25
                cagr = ((current_balance / initial_balance) ** (1/years) - 1) * 100 if years > 0 and initial_balance > 0 else 0
            else:
                cagr = 0
            
            return {
                'initial_balance': initial_balance,
                'current_balance': current_balance,
                'roi_percent': roi_percent,
                'profit_loss': profit_loss,
                'max_balance': max_balance,
                'max_drawdown_percent': max_drawdown,
                'days_tracked': days_tracked,
                'cagr_annual': cagr
            }
            
        except Exception as e:
            logger.error(f"Error calculando métricas: {e}")
            return None
    
    def save_trade(self, trade_data: Dict) -> bool:
        """Guardar trade ejecutado"""
        if not self.connected:
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO trades (user_id, symbol, side, amount, price, total_cost, status, order_id, exchange, profit_loss)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                trade_data.get('user_id'),
                trade_data.get('symbol'),
                trade_data.get('side'),
                trade_data.get('amount'),
                trade_data.get('price'),
                trade_data.get('total_cost'),
                trade_data.get('status'),
                trade_data.get('order_id'),
                trade_data.get('exchange', 'kraken'),
                trade_data.get('profit_loss', 0)
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"✅ Trade guardado: {trade_data.get('symbol')} {trade_data.get('side')}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando trade: {e}")
            return False
    
    def ensure_user_exists(self, user_id: str, username: str = None, 
                           first_name: str = None, language_code: str = 'auto') -> bool:
        """
        Garantizar que el usuario existe en la tabla users.
        Si no existe, lo crea (INSERT). Si existe, actualiza last_activity (idempotente).
        
        Este método DEBE llamarse antes de cualquier operación que escriba a tablas
        con FK a users.user_id (conversations, trades, analysis, signals, etc.)
        
        Args:
            user_id: ID del usuario (Telegram user_id como string)
            username: Username de Telegram (opcional)
            first_name: Nombre del usuario (opcional)
            language_code: Código de idioma (default: 'auto' = AI auto-detection)
            
        Returns:
            True si el usuario existe o fue creado exitosamente, False si error
        """
        # LOGGING DETALLADO PARA DEBUG
        logger.info(f"🔍 ensure_user_exists called: user_id={user_id}, username={username}, first_name={first_name}")
        
        if not self.connected:
            logger.error(f"❌ ensure_user_exists FAILED: Database not connected (self.connected={self.connected})")
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                logger.error("❌ ensure_user_exists FAILED: _get_connection() returned None")
                return False
            
            cursor = conn.cursor()
            
            # Usar valores default si son None para evitar problemas
            username_safe = username or f"user_{user_id}"
            first_name_safe = first_name or "Usuario"
            
            logger.info(f"✅ Executing UPSERT for user {user_id} (username={username_safe}, first_name={first_name_safe})")
            
            # FIX Nov 29, 2025: Verificar si columna last_activity existe antes de usarla
            # Esto evita error si la migración no se ejecutó en Railway
            cursor.execute('''
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'last_activity'
            ''')
            has_last_activity = cursor.fetchone() is not None
            
            # FIX Dec 18, 2025: Convertir user_id a telegram_id (bigint) si es numérico
            telegram_id_safe = None
            if user_id and user_id.isdigit():
                telegram_id_safe = int(user_id)
            
            if has_last_activity:
                # UPSERT con last_activity y telegram_id
                cursor.execute('''
                    INSERT INTO users (user_id, telegram_id, username, first_name, language_code, created_at, last_activity)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id) DO UPDATE SET
                        last_activity = CURRENT_TIMESTAMP,
                        telegram_id = COALESCE(EXCLUDED.telegram_id, users.telegram_id),
                        username = COALESCE(EXCLUDED.username, users.username),
                        first_name = COALESCE(EXCLUDED.first_name, users.first_name),
                        language_code = COALESCE(EXCLUDED.language_code, users.language_code)
                ''', (user_id, telegram_id_safe, username_safe, first_name_safe, language_code))
            else:
                # UPSERT SIN last_activity (tabla legacy) pero con telegram_id
                logger.warning("⚠️ Columna last_activity no existe - usando UPSERT legacy")
                cursor.execute('''
                    INSERT INTO users (user_id, telegram_id, username, first_name, language_code, created_at)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id) DO UPDATE SET
                        telegram_id = COALESCE(EXCLUDED.telegram_id, users.telegram_id),
                        username = COALESCE(EXCLUDED.username, users.username),
                        first_name = COALESCE(EXCLUDED.first_name, users.first_name),
                        language_code = COALESCE(EXCLUDED.language_code, users.language_code)
                ''', (user_id, telegram_id_safe, username_safe, first_name_safe, language_code))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ ensure_user_exists SUCCESS: User {user_id} registered/updated")
            return True
            
        except Exception as e:
            logger.error(f"❌ ensure_user_exists EXCEPTION: {e}", exc_info=True)
            # Retry once after brief wait — handles Railway startup DB readiness timing
            import time
            time.sleep(1)
            try:
                conn2 = self._get_connection()
                if conn2:
                    cursor2 = conn2.cursor()
                    cursor2.execute('''
                        INSERT INTO users (user_id, username, first_name, language_code, created_at)
                        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (user_id) DO UPDATE SET
                            username = COALESCE(EXCLUDED.username, users.username),
                            first_name = COALESCE(EXCLUDED.first_name, users.first_name)
                    ''', (user_id, username or f"user_{user_id}", first_name or "Usuario", language_code))
                    conn2.commit()
                    cursor2.close()
                    conn2.close()
                    logger.info(f"✅ ensure_user_exists RETRY SUCCESS: User {user_id}")
                    return True
            except Exception as e2:
                logger.error(f"❌ ensure_user_exists RETRY FAILED: {e2}")
            return False

    def save_conversation(self, user_id: str, user_message: str, ai_response: str, language: str = 'es') -> bool:
        """Guardar conversación IA en PostgreSQL (persistente)"""
        if not self.connected:
            logger.warning(f"🧠 save_conversation: DB not connected for user {user_id}")
            return False
        
        try:
            logger.info(f"🧠 save_conversation: Guardando para user {user_id} (msg: {len(user_message)} chars, resp: {len(ai_response)} chars)")
            
            conn = self._get_connection()
            if not conn:
                logger.error(f"🧠 save_conversation: No connection for user {user_id}")
                return False
            
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO conversations (user_id, user_message, ai_response, language)
                    VALUES (%s, %s, %s, %s)
                ''', (user_id, user_message, ai_response, language))
                conn.commit()
            except Exception as insert_err:
                err_str = str(insert_err).lower()
                if 'foreign key' in err_str or 'violates' in err_str:
                    # User not in users table yet — create and retry
                    logger.warning(f"⚠️ save_conversation FK violation for {user_id} — creating user and retrying")
                    conn.rollback()
                    cursor.execute('''
                        INSERT INTO users (user_id, username, first_name, language_code, created_at)
                        VALUES (%s, %s, %s, 'es', CURRENT_TIMESTAMP)
                        ON CONFLICT (user_id) DO NOTHING
                    ''', (user_id, f"user_{user_id}", "Usuario"))
                    cursor.execute('''
                        INSERT INTO conversations (user_id, user_message, ai_response, language)
                        VALUES (%s, %s, %s, %s)
                    ''', (user_id, user_message, ai_response, language))
                    conn.commit()
                else:
                    raise
            cursor.close()
            conn.close()
            
            logger.info(f"✅ save_conversation: SUCCESS para user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ save_conversation ERROR para user {user_id}: {e}", exc_info=True)
            return False
    
    def get_conversation_history(self, chat_id: int, limit: int = 10) -> list:
        """
        Obtener historial de conversación desde PostgreSQL (PERSISTENTE)
        
        Args:
            chat_id: ID del chat
            limit: Número de pares de mensajes a retornar (default: 10)
            
        Returns:
            Lista de diccionarios con {'user': str, 'ai': str, 'timestamp': str}
        """
        if not self.connected:
            logger.warning(f"🧠 get_conversation_history: DB not connected for chat {chat_id}")
            return []
        
        try:
            logger.info(f"🧠 get_conversation_history: Cargando para chat {chat_id} (limit={limit})")
            
            conn = self._get_connection()
            if not conn:
                logger.error(f"🧠 get_conversation_history: No connection for chat {chat_id}")
                return []
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_message, ai_response, created_at 
                FROM conversations 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            ''', (str(chat_id), limit))
            
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            history = []
            for row in reversed(rows):
                history.append({
                    'user': row[0],
                    'ai': row[1],
                    'timestamp': row[2].isoformat() if row[2] else None
                })
            
            logger.info(f"✅ get_conversation_history: Loaded {len(history)} messages for chat {chat_id}")
            return history
            
        except Exception as e:
            logger.error(f"❌ get_conversation_history ERROR for chat {chat_id}: {e}", exc_info=True)
            return []
    
    def save_trade_reasoning(self, reasoning: Dict) -> Optional[str]:
        """
        Guardar razonamiento pre-trade del Cerebro Conversacional
        
        Args:
            reasoning: Dict con razonamiento completo
            
        Returns:
            UUID del razonamiento guardado, None si falla
        """
        if not self.connected:
            return None
        
        try:
            import json
            conn = self._get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO trade_reasonings (
                    user_id, action, pair, amount_usd, confidence,
                    signals, reasons, summary, full_explanation
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING trade_uuid
            ''', (
                reasoning.get('user_id', 'harold'),
                reasoning.get('action', 'BUY'),
                reasoning.get('pair', 'BTC/USD'),
                reasoning.get('amount_usd', 0),
                reasoning.get('confidence', 0),
                json.dumps(reasoning.get('signals', {})),
                json.dumps(reasoning.get('reasons', [])),
                reasoning.get('summary', ''),
                reasoning.get('full_explanation', '')
            ))
            
            trade_uuid = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.debug(f"🧠 Razonamiento guardado: {trade_uuid}")
            return str(trade_uuid)
            
        except Exception as e:
            logger.error(f"Error guardando razonamiento: {e}")
            return None
    
    def save_trade_evaluation(self, evaluation: Dict) -> Optional[str]:
        """
        Guardar auto-evaluación post-trade del Cerebro Conversacional
        
        Args:
            evaluation: Dict con evaluación completa
            
        Returns:
            UUID de la evaluación guardada, None si falla
        """
        if not self.connected:
            return None
        
        try:
            import json
            conn = self._get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO trade_evaluations (
                    trade_id, user_id, elapsed_minutes, original_action,
                    original_confidence, result, was_correct,
                    learning_points, adjustments_suggested, full_review
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING evaluation_uuid
            ''', (
                evaluation.get('trade_id', ''),
                evaluation.get('user_id', 'harold'),
                evaluation.get('elapsed_minutes', 30),
                evaluation.get('original_action', 'BUY'),
                evaluation.get('original_confidence', 0),
                json.dumps(evaluation.get('result', {})),
                evaluation.get('was_correct', False),
                json.dumps(evaluation.get('learning_points', [])),
                json.dumps(evaluation.get('adjustments_suggested', [])),
                evaluation.get('full_review', '')
            ))
            
            evaluation_uuid = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.debug(f"🔍 Evaluación guardada: {evaluation_uuid}")
            return str(evaluation_uuid)
            
        except Exception as e:
            logger.error(f"Error guardando evaluación: {e}")
            return None
    
    def get_trade_reasoning_by_uuid(self, reasoning_uuid: str) -> Optional[Dict]:
        """
        Recuperar razonamiento pre-trade completo por su UUID.

        Permite al motor de auto-evaluación reconstruir el contexto original
        de la decisión para compararlo con el resultado real del trade.

        Args:
            reasoning_uuid: UUID del razonamiento almacenado en trade_reasonings

        Returns:
            Dict con todos los campos del razonamiento, o None si no existe o hay error
        """
        if not self.connected or not reasoning_uuid:
            return None

        try:
            import json
            conn = self._get_connection()
            if not conn:
                return None

            cursor = conn.cursor()
            cursor.execute('''
                SELECT trade_uuid, user_id, action, pair, amount_usd, confidence,
                       signals, reasons, summary, full_explanation, created_at
                FROM trade_reasonings
                WHERE trade_uuid = %s::UUID
                LIMIT 1
            ''', (str(reasoning_uuid),))

            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if not row:
                logger.debug(f"[DB] Razonamiento no encontrado: {reasoning_uuid}")
                return None

            return {
                'trade_uuid':       str(row[0]),
                'user_id':          row[1],
                'action':           row[2],
                'pair':             row[3],
                'amount_usd':       float(row[4]) if row[4] else 0.0,
                'confidence':       float(row[5]) if row[5] else 0.0,
                'signals':          json.loads(row[6]) if row[6] else {},
                'reasons':          json.loads(row[7]) if row[7] else [],
                'summary':          row[8] or '',
                'full_explanation': row[9] or '',
                'created_at':       row[10].isoformat() if row[10] else None,
            }

        except Exception as e:
            logger.error(f"[DB] Error obteniendo razonamiento {reasoning_uuid}: {e}")
            return None

    def get_trade_by_id(self, trade_id: str) -> Optional[Dict]:
        """
        Recuperar trade de paper_trading_trades por UUID o ID numérico.

        Usado por el motor de evaluación post-trade para obtener el P/L real,
        precio de entrada, precio de salida y duración del trade cerrado.

        Args:
            trade_id: UUID del trade (str) o ID numérico (str).
                      Se intenta primero match por trade_uuid, luego por id.

        Returns:
            Dict con datos del trade incluyendo profit_loss neto, o None si
            el trade no existe, aún está abierto (sin exit_price), o hay error.
        """
        if not self.connected or not trade_id:
            return None

        try:
            conn = self._get_connection()
            if not conn:
                return None

            cursor = conn.cursor()
            cursor.execute('''
                SELECT trade_uuid, symbol, side, status,
                       entry_price, exit_price,
                       net_realized_pnl_usd, gross_pnl_usd,
                       base_quantity, quote_notional_usd,
                       opened_at, closed_at, duration_seconds
                FROM paper_trading_trades
                WHERE trade_uuid::TEXT = %s
                   OR id::TEXT = %s
                LIMIT 1
            ''', (trade_id, trade_id))

            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if not row:
                logger.debug(f"[DB] Trade no encontrado: {trade_id}")
                return None

            entry_price = float(row[4]) if row[4] else 0.0
            exit_price  = float(row[5]) if row[5] else 0.0
            net_pnl     = float(row[6]) if row[6] else 0.0
            gross_pnl   = float(row[7]) if row[7] else 0.0

            return {
                'trade_uuid':         str(row[0]),
                'symbol':             row[1],
                'side':               row[2],
                'status':             row[3],
                'entry_price':        entry_price,
                'exit_price':         exit_price,
                'profit_loss':        net_pnl,
                'gross_pnl_usd':      gross_pnl,
                'base_quantity':      float(row[8]) if row[8] else 0.0,
                'quote_notional_usd': float(row[9]) if row[9] else 0.0,
                'opened_at':          row[10].isoformat() if row[10] else None,
                'closed_at':          row[11].isoformat() if row[11] else None,
                'duration_seconds':   int(row[12]) if row[12] else 0,
            }

        except Exception as e:
            logger.error(f"[DB] Error obteniendo trade {trade_id}: {e}")
            return None

    def get_recent_reasonings(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Obtener razonamientos recientes
        
        Args:
            user_id: ID del usuario (OBLIGATORIO para aislamiento multi-usuario)
            limit: Número de razonamientos a obtener
            
        Returns:
            Lista de razonamientos
        """
        if not self.connected:
            return []
        
        try:
            import json
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    trade_uuid, action, pair, amount_usd, confidence,
                    signals, reasons, summary, full_explanation, created_at
                FROM trade_reasonings
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            ''', (user_id, limit))
            
            rows = cursor.fetchall()
            
            reasonings = []
            for row in rows:
                reasonings.append({
                    'trade_uuid': str(row[0]),
                    'action': row[1],
                    'pair': row[2],
                    'amount_usd': float(row[3]),
                    'confidence': float(row[4]),
                    'signals': json.loads(row[5]) if row[5] else {},
                    'reasons': json.loads(row[6]) if row[6] else [],
                    'summary': row[7],
                    'full_explanation': row[8],
                    'created_at': row[9].isoformat() if row[9] else None
                })
            
            cursor.close()
            conn.close()
            return reasonings
            
        except Exception as e:
            logger.error(f"Error obteniendo razonamientos: {e}")
            return []
    
    def get_learning_summary(self, user_id: str) -> Dict:
        """
        Obtener resumen de aprendizajes del Cerebro Conversacional
        
        Args:
            user_id: ID del usuario (OBLIGATORIO para aislamiento multi-usuario)
            
        Returns:
            Dict con estadísticas de aprendizaje
        """
        if not self.connected:
            return {}
        
        try:
            conn = self._get_connection()
            if not conn:
                return {}
            
            cursor = conn.cursor()
            
            # Total evaluaciones
            cursor.execute('''
                SELECT COUNT(*) FROM trade_evaluations WHERE user_id = %s
            ''', (user_id,))
            total = cursor.fetchone()[0] or 0
            
            # Trades correctos
            cursor.execute('''
                SELECT COUNT(*) FROM trade_evaluations WHERE user_id = %s AND was_correct = TRUE
            ''', (user_id,))
            correct = cursor.fetchone()[0] or 0
            
            # Success rate
            success_rate = (correct / total * 100) if total > 0 else 0
            
            cursor.close()
            conn.close()
            
            return {
                'total_evaluations': total,
                'correct_trades': correct,
                'incorrect_trades': total - correct,
                'success_rate': success_rate,
                'performance': 'EXCELENTE' if success_rate > 70 else 'BUENO' if success_rate > 50 else 'MEJORABLE'
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo learning summary: {e}")
            return {}
    
    def schedule_trade_evaluation(self, trade_id: str, reasoning_uuid: Optional[str], user_id: str, minutes_delay: int = 30) -> bool:
        """
        Programar evaluación post-trade (sistema robusto sin threads)
        
        Args:
            trade_id: ID del trade a evaluar
            reasoning_uuid: UUID del razonamiento original
            user_id: ID del usuario (OBLIGATORIO para aislamiento multi-usuario)
            minutes_delay: Minutos para esperar antes de evaluar
            
        Returns:
            True si se programó correctamente
        """
        if not self.connected:
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Calcular scheduled_at
            scheduled_at = datetime.now() + timedelta(minutes=minutes_delay)
            
            cursor.execute('''
                INSERT INTO pending_evaluations (trade_id, trade_reasoning_uuid, user_id, scheduled_at)
                VALUES (%s, %s, %s, %s)
            ''', (trade_id, reasoning_uuid, user_id, scheduled_at))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"⏰ Evaluación programada para trade {trade_id} en {minutes_delay} minutos")
            return True
            
        except Exception as e:
            logger.error(f"Error programando evaluación: {e}")
            return False
    
    def get_due_evaluations(self) -> List[Dict]:
        """
        Obtener evaluaciones que ya es hora de procesar
        
        Returns:
            Lista de evaluaciones pendientes
        """
        if not self.connected:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, trade_id, trade_reasoning_uuid, user_id, scheduled_at
                FROM pending_evaluations
                WHERE status = 'pending' AND scheduled_at <= CURRENT_TIMESTAMP
                ORDER BY scheduled_at ASC
                LIMIT 10
            ''')
            
            rows = cursor.fetchall()
            
            evaluations = []
            for row in rows:
                evaluations.append({
                    'id': row[0],
                    'trade_id': row[1],
                    'reasoning_uuid': str(row[2]) if row[2] else None,
                    'user_id': row[3],
                    'scheduled_at': row[4].isoformat() if row[4] else None
                })
            
            cursor.close()
            conn.close()
            return evaluations
            
        except Exception as e:
            logger.error(f"Error obteniendo evaluaciones pendientes: {e}")
            return []
    
    def mark_evaluation_completed(self, evaluation_id: int, result: Dict) -> bool:
        """
        Marcar evaluación como completada
        
        Args:
            evaluation_id: ID de la evaluación pendiente
            result: Resultado de la evaluación
            
        Returns:
            True si se marcó correctamente
        """
        if not self.connected:
            return False
        
        try:
            import json
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE pending_evaluations
                SET status = 'completed', result = %s, processed_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (json.dumps(result), evaluation_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error marcando evaluación como completada: {e}")
            return False
    
    # ==========================================
    # COMMUNITY INTELLIGENCE DATA ACCESS LAYER
    # ==========================================
    
    def submit_community_feedback(self, user_id: str, username: str, feedback_data: Dict) -> Dict:
        """Registrar feedback comunitario"""
        if not self.connected:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            conn = self._get_connection()
            if not conn:
                return {'success': False, 'error': 'Connection failed'}
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO community_feedback 
                (user_id, username, feedback_type, signal_type, strategy, symbol, 
                 result, market_condition, btc_price, volatility, timeframe, comment)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                user_id, username, feedback_data.get('feedback_type'), 
                feedback_data.get('signal_type'), feedback_data.get('strategy'),
                feedback_data.get('symbol'), feedback_data.get('result'),
                feedback_data.get('market_condition'), feedback_data.get('btc_price'),
                feedback_data.get('volatility'), feedback_data.get('timeframe'),
                feedback_data.get('comment')
            ))
            
            feedback_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            return {'success': True, 'feedback_id': feedback_id}
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_community_feedback(self, strategy: str = None, limit: int = 50) -> List[Dict]:
        """Obtener feedback comunitario"""
        if not self.connected:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            
            if strategy:
                cursor.execute('''
                    SELECT * FROM community_feedback 
                    WHERE strategy = %s 
                    ORDER BY created_at DESC LIMIT %s
                ''', (strategy, limit))
            else:
                cursor.execute('''
                    SELECT * FROM community_feedback 
                    ORDER BY created_at DESC LIMIT %s
                ''', (limit,))
            
            rows = cursor.fetchall()
            feedback_list = []
            
            for row in rows:
                feedback_list.append({
                    'id': row[0], 'user_id': row[1], 'username': row[2],
                    'feedback_type': row[3], 'strategy': row[5], 'result': row[7]
                })
            
            cursor.close()
            conn.close()
            return feedback_list
            
        except Exception as e:
            logger.error(f"Error getting feedback: {e}")
            return []
    
    def vote_strategy(self, user_id: str, strategy: str, vote: int, reason: str = None, market_condition: str = None) -> Dict:
        """Votar por una estrategia con condición de mercado"""
        if not self.connected:
            return {'success': False}
        
        try:
            conn = self._get_connection()
            if not conn:
                return {'success': False}
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO strategy_votes (user_id, strategy, vote, reason, market_condition, vote_date)
                VALUES (%s, %s, %s, %s, %s, CURRENT_DATE)
                ON CONFLICT (user_id, strategy, vote_date) 
                DO UPDATE SET vote = EXCLUDED.vote, reason = EXCLUDED.reason, market_condition = EXCLUDED.market_condition
                RETURNING id
            ''', (user_id, strategy, vote, reason, market_condition))
            
            vote_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            return {'success': True, 'vote_id': vote_id}
            
        except Exception as e:
            logger.error(f"Error voting strategy: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_user_contributions(self, user_id: str, username: str, points: int, contribution_type: str = 'generic') -> bool:
        """
        Actualizar contribuciones del usuario (puntos + contadores específicos)
        
        Args:
            user_id: ID del usuario
            username: Nombre del usuario
            points: Puntos a agregar
            contribution_type: 'feedback' | 'vote' | 'proposal' | 'helpful_feedback' | 'proposal_accepted' | 'generic'
        
        Counters updated based on contribution_type:
            - 'feedback' → total_feedback +1, points +10
            - 'vote' → total_votes +1, points +5
            - 'proposal' → proposals_submitted +1, points +25
            - 'helpful_feedback' → helpful_feedback +1, points +15
            - 'proposal_accepted' → proposals_accepted +1, points +50
        """
        if not self.connected:
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Actualizar TODOS los contadores según tipo de contribución
            cursor.execute('''
                INSERT INTO user_contributions (
                    user_id, username, 
                    total_feedback, helpful_feedback, total_votes, 
                    proposals_submitted, proposals_accepted,
                    contribution_points, first_contribution
                )
                VALUES (
                    %s, %s,
                    CASE WHEN %s = 'feedback' THEN 1 ELSE 0 END,
                    CASE WHEN %s = 'helpful_feedback' THEN 1 ELSE 0 END,
                    CASE WHEN %s = 'vote' THEN 1 ELSE 0 END,
                    CASE WHEN %s = 'proposal' THEN 1 ELSE 0 END,
                    CASE WHEN %s = 'proposal_accepted' THEN 1 ELSE 0 END,
                    %s, CURRENT_TIMESTAMP
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    username = COALESCE(EXCLUDED.username, user_contributions.username),
                    total_feedback = user_contributions.total_feedback + 
                        CASE WHEN %s = 'feedback' THEN 1 ELSE 0 END,
                    helpful_feedback = user_contributions.helpful_feedback + 
                        CASE WHEN %s = 'helpful_feedback' THEN 1 ELSE 0 END,
                    total_votes = user_contributions.total_votes + 
                        CASE WHEN %s = 'vote' THEN 1 ELSE 0 END,
                    proposals_submitted = user_contributions.proposals_submitted + 
                        CASE WHEN %s = 'proposal' THEN 1 ELSE 0 END,
                    proposals_accepted = user_contributions.proposals_accepted + 
                        CASE WHEN %s = 'proposal_accepted' THEN 1 ELSE 0 END,
                    contribution_points = user_contributions.contribution_points + %s,
                    last_contribution = CURRENT_TIMESTAMP,
                    contribution_level = CASE 
                        WHEN user_contributions.contribution_points + %s >= 1000 THEN 'Experto'
                        WHEN user_contributions.contribution_points + %s >= 500 THEN 'Avanzado'
                        WHEN user_contributions.contribution_points + %s >= 100 THEN 'Intermedio'
                        ELSE 'Novato'
                    END
            ''', (
                user_id, username,
                contribution_type, contribution_type, contribution_type, contribution_type, contribution_type,
                points,
                contribution_type, contribution_type, contribution_type, contribution_type, contribution_type,
                points, points, points, points
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating contributions: {e}")
            return False
    
    def submit_proposal(self, user_id: str, username: str, proposal_data: Dict) -> Dict:
        """Enviar propuesta de mejora"""
        if not self.connected:
            return {'success': False, 'error': 'Database not available'}
        
        # Validación de campos requeridos
        required_fields = ['proposal_type', 'title', 'description']
        for field in required_fields:
            if field not in proposal_data:
                return {'success': False, 'error': f'Missing required field: {field}'}
        
        try:
            conn = self._get_connection()
            if not conn:
                return {'success': False, 'error': 'Connection failed'}
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO improvement_proposals 
                (user_id, username, proposal_type, title, description, affected_strategy, priority)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                user_id,
                username,
                proposal_data.get('proposal_type', 'improvement'),
                proposal_data.get('title'),
                proposal_data.get('description'),
                proposal_data.get('affected_strategy'),
                proposal_data.get('priority', 'medium')
            ))
            
            proposal_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            return {'success': True, 'proposal_id': proposal_id}
            
        except Exception as e:
            logger.error(f"Error submitting proposal: {e}")
            return {'success': False, 'error': str(e)}
    
    # ==========================================
    # SIGNAL CONTRIBUTION DATA ACCESS LAYER
    # ==========================================
    
    def save_community_signal(self, signal_data: Dict) -> Dict:
        """Guardar señal compartida por usuario"""
        if not self.connected:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            conn = self._get_connection()
            if not conn:
                return {'success': False, 'error': 'Connection failed'}
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO community_signals 
                (signal_id, contributor_id, contributor_name, symbol, signal_type,
                 entry_price, target_price, stop_loss, timeframe, confidence,
                 reasoning, indicators_used, market_condition)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                signal_data.get('signal_id'), signal_data.get('contributor_id'),
                signal_data.get('contributor_name'), signal_data.get('symbol'),
                signal_data.get('signal_type'), signal_data.get('entry_price'),
                signal_data.get('target_price'), signal_data.get('stop_loss'),
                signal_data.get('timeframe'), signal_data.get('confidence'),
                signal_data.get('reasoning'), signal_data.get('indicators_used'),
                signal_data.get('market_condition')
            ))
            
            signal_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            return {'success': True, 'id': signal_id}
            
        except Exception as e:
            logger.error(f"Error saving signal: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_community_signals(self, status: str = 'active', limit: int = 20) -> List[Dict]:
        """Obtener señales comunitarias"""
        if not self.connected:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT signal_id, contributor_name, symbol, signal_type,
                       entry_price, target_price, confidence, upvotes, downvotes
                FROM community_signals 
                WHERE status = %s 
                ORDER BY created_at DESC LIMIT %s
            ''', (status, limit))
            
            rows = cursor.fetchall()
            signals = []
            
            for row in rows:
                signals.append({
                    'signal_id': row[0], 'contributor': row[1], 'symbol': row[2],
                    'type': row[3], 'entry': row[4], 'target': row[5],
                    'confidence': row[6], 'upvotes': row[7], 'downvotes': row[8]
                })
            
            cursor.close()
            conn.close()
            return signals
            
        except Exception as e:
            logger.error(f"Error getting signals: {e}")
            return []
    
    def update_signal_votes(self, signal_id: str, vote_type: str) -> bool:
        """Actualizar votos de una señal"""
        if not self.connected:
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            if vote_type == 'upvote':
                cursor.execute('''
                    UPDATE community_signals 
                    SET upvotes = upvotes + 1 
                    WHERE signal_id = %s
                ''', (signal_id,))
            else:
                cursor.execute('''
                    UPDATE community_signals 
                    SET downvotes = downvotes + 1 
                    WHERE signal_id = %s
                ''', (signal_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating signal votes: {e}")
            return False
    
    # ==========================================
    # RISK GUARDIAN DATA ACCESS LAYER
    # ==========================================
    
    def log_risk_event(self, risk_type: str, risk_level: str, description: str, 
                       action_taken: str, metadata: Dict = None, user_id: int = None) -> bool:
        """Registrar evento del AI Risk Guardian
        
        Note: Parameters use risk_type/risk_level for API compatibility,
        but map to event_type/severity columns in the database.
        """
        if not self.connected:
            return False
        
        try:
            import json
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO risk_guardian_events 
                (event_type, severity, description, action_taken, metadata, user_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (risk_type, risk_level, description, action_taken, 
                  json.dumps(metadata) if metadata else None, user_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error logging risk event: {e}")
            return False
    
    def get_risk_events(self, limit: int = 50, risk_type: str = None) -> List[Dict]:
        """Obtener eventos de riesgo
        
        Note: Returns risk_type/risk_level keys for API compatibility,
        but reads from event_type/severity columns in the database.
        """
        if not self.connected:
            return []
        
        try:
            import json
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            
            if risk_type:
                cursor.execute('''
                    SELECT created_at, event_type, severity, description, action_taken
                    FROM risk_guardian_events 
                    WHERE event_type = %s
                    ORDER BY created_at DESC LIMIT %s
                ''', (risk_type, limit))
            else:
                cursor.execute('''
                    SELECT created_at, event_type, severity, description, action_taken
                    FROM risk_guardian_events 
                    ORDER BY created_at DESC LIMIT %s
                ''', (limit,))
            
            rows = cursor.fetchall()
            events = []
            
            for row in rows:
                events.append({
                    'timestamp': row[0].isoformat() if row[0] else None,
                    'risk_type': row[1], 'risk_level': row[2],
                    'description': row[3], 'action_taken': row[4]
                })
            
            cursor.close()
            conn.close()
            return events
            
        except Exception as e:
            logger.error(f"Error getting risk events: {e}")
            return []
    
    # ==========================================
    # COMMUNITY ANALYZER DATA ACCESS LAYER
    # ==========================================
    
    def fetch_feedback_patterns(self, since_date, min_samples: int = 5) -> List[Dict]:
        """Obtener patrones agregados de feedback comunitario"""
        if not self.connected:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    strategy,
                    market_condition,
                    volatility,
                    result,
                    COUNT(*) as count
                FROM community_feedback
                WHERE created_at >= %s
                GROUP BY strategy, market_condition, volatility, result
                HAVING COUNT(*) >= %s
                ORDER BY strategy, count DESC
            ''', (since_date, min_samples))
            
            rows = cursor.fetchall()
            patterns = []
            
            for row in rows:
                patterns.append({
                    'strategy': row[0],
                    'market_condition': row[1],
                    'volatility': row[2],
                    'result': row[3],
                    'count': row[4]
                })
            
            cursor.close()
            conn.close()
            return patterns
            
        except Exception as e:
            logger.error(f"Error fetching feedback patterns: {e}")
            return []
    
    def upsert_detected_pattern(self, pattern: Dict) -> bool:
        """Guardar o actualizar patrón detectado"""
        if not self.connected:
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Verificar si ya existe
            cursor.execute('''
                SELECT pattern_id FROM detected_patterns 
                WHERE pattern_type = %s 
                AND affected_strategy = %s 
                AND market_condition = %s
                AND status = 'detected'
            ''', (pattern.get('pattern_type'), pattern.get('affected_strategy'), 
                  pattern.get('market_condition')))
            
            existing = cursor.fetchone()
            
            import json
            if existing:
                # Actualizar existente
                cursor.execute('''
                    UPDATE detected_patterns SET
                        confidence = %s,
                        sample_size = %s,
                        failure_rate = %s,
                        suggestion = %s,
                        metadata = %s,
                        updated_at = NOW()
                    WHERE pattern_id = %s
                ''', (pattern.get('confidence'), pattern.get('sample_size'),
                      pattern.get('failure_rate'), pattern.get('suggestion'),
                      json.dumps(pattern.get('metadata', {})), existing[0]))
            else:
                # Insertar nuevo
                cursor.execute('''
                    INSERT INTO detected_patterns 
                    (pattern_type, description, affected_strategy, market_condition,
                     confidence, sample_size, failure_rate, suggestion, metadata, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'detected')
                ''', (pattern.get('pattern_type'), pattern.get('description'),
                      pattern.get('affected_strategy'), pattern.get('market_condition'),
                      pattern.get('confidence'), pattern.get('sample_size'),
                      pattern.get('failure_rate'), pattern.get('suggestion'),
                      json.dumps(pattern.get('metadata', {}))))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error upserting detected pattern: {e}")
            return False
    
    def get_top_contributors(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """Obtener mejores contribuidores"""
        if not self.connected:
            return []
        
        try:
            from datetime import datetime, timedelta
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            since_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT 
                    user_id,
                    username,
                    contribution_points,
                    contribution_level,
                    total_feedback,
                    proposals_submitted,
                    proposals_accepted
                FROM user_contributions
                WHERE last_contribution >= %s
                ORDER BY contribution_points DESC
                LIMIT %s
            ''', (since_date, limit))
            
            rows = cursor.fetchall()
            contributors = []
            
            for row in rows:
                contributors.append({
                    'user_id': row[0],
                    'username': row[1],
                    'points': row[2],
                    'level': row[3],
                    'total_feedback': row[4],
                    'proposals_submitted': row[5],
                    'proposals_accepted': row[6]
                })
            
            cursor.close()
            conn.close()
            return contributors
            
        except Exception as e:
            logger.error(f"Error getting top contributors: {e}")
            return []
    
    def get_improvement_proposals(self, status: str = None, limit: int = 20) -> List[Dict]:
        """Obtener propuestas de mejora"""
        if not self.connected:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            
            if status:
                cursor.execute('''
                    SELECT proposal_id, user_id, title, description, category,
                           expected_improvement, status, votes, created_at
                    FROM improvement_proposals
                    WHERE status = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                ''', (status, limit))
            else:
                cursor.execute('''
                    SELECT proposal_id, user_id, title, description, category,
                           expected_improvement, status, votes, created_at
                    FROM improvement_proposals
                    ORDER BY created_at DESC
                    LIMIT %s
                ''', (limit,))
            
            rows = cursor.fetchall()
            proposals = []
            
            for row in rows:
                proposals.append({
                    'proposal_id': row[0],
                    'user_id': row[1],
                    'title': row[2],
                    'description': row[3],
                    'category': row[4],
                    'expected_improvement': row[5],
                    'status': row[6],
                    'votes': row[7],
                    'created_at': row[8].isoformat() if row[8] else None
                })
            
            cursor.close()
            conn.close()
            return proposals
            
        except Exception as e:
            logger.error(f"Error getting improvement proposals: {e}")
            return []
    
    def get_community_stats(self) -> Dict:
        """Obtener estadísticas comunitarias"""
        if not self.connected:
            return {}
        
        try:
            conn = self._get_connection()
            if not conn:
                return {}
            
            cursor = conn.cursor()
            stats = {}
            
            # Total contributors
            cursor.execute('SELECT COUNT(*) FROM user_contributions')
            stats['total_contributors'] = cursor.fetchone()[0]
            
            # Total feedback
            cursor.execute('SELECT COUNT(*) FROM community_feedback')
            stats['total_feedback'] = cursor.fetchone()[0]
            
            # Pending proposals
            cursor.execute('SELECT COUNT(*) FROM improvement_proposals WHERE status = %s', ('pending',))
            stats['pending_proposals'] = cursor.fetchone()[0]
            
            # Detected patterns
            cursor.execute('SELECT COUNT(*) FROM detected_patterns WHERE status = %s', ('detected',))
            stats['active_patterns'] = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"Error getting community stats: {e}")
            return {}
    
    # ==========================================
    # USER CONTACTS MANAGEMENT (NUEVA - Nov 26, 2025)
    # ==========================================
    
    def add_user_contact(self, user_id: str, contact_type: str, contact_value: str, 
                        is_primary: bool = False, is_verified: bool = False) -> Dict:
        """
        Agregar nuevo método de contacto para usuario
        
        Args:
            user_id: user_id del usuario (Telegram ID)
            contact_type: Tipo de contacto ('whatsapp', 'email', 'telegram', 'phone', 'sms')
            contact_value: Valor del contacto (número, email, etc.)
            is_primary: Si es el contacto principal para ese tipo
            is_verified: Si ya está verificado
        
        Returns:
            Dict con resultado de la operación
        """
        if not self.db_url or not PSYCOPG_AVAILABLE:
            return {'success': False, 'error': 'Database not available'}
        
        conn = self._get_connection()
        if not conn:
            return {'success': False, 'error': 'Connection failed'}
        
        try:
            cursor = conn.cursor()
            
            # Insertar contacto (user_id es TEXT, FK directo)
            cursor.execute('''
                INSERT INTO user_contacts (user_id, contact_type, contact_value, is_primary, is_verified)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id, contact_type, contact_value) 
                DO UPDATE SET is_primary = EXCLUDED.is_primary, is_verified = EXCLUDED.is_verified
                RETURNING id
            ''', (user_id, contact_type, contact_value, is_primary, is_verified))
            
            contact_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Contacto agregado: {contact_type} para user {user_id}")
            return {
                'success': True, 
                'contact_id': str(contact_id),
                'contact_type': contact_type,
                'contact_value': contact_value
            }
            
        except Exception as e:
            logger.error(f"Error adding user contact: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_user_contacts(self, user_id: str, contact_type: str = None) -> List[Dict]:
        """
        Obtener contactos de un usuario
        
        Args:
            user_id: user_id del usuario (Telegram ID)
            contact_type: Filtrar por tipo de contacto (opcional)
        
        Returns:
            Lista de contactos
        """
        if not self.db_url or not PSYCOPG_AVAILABLE:
            return []
        
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            # Obtener contactos (user_id es TEXT, FK directo)
            if contact_type:
                cursor.execute('''
                    SELECT id, contact_type, contact_value, is_verified, is_primary, 
                           verified_at, created_at
                    FROM user_contacts
                    WHERE user_id = %s AND contact_type = %s
                    ORDER BY is_primary DESC, created_at DESC
                ''', (user_id, contact_type))
            else:
                cursor.execute('''
                    SELECT id, contact_type, contact_value, is_verified, is_primary, 
                           verified_at, created_at
                    FROM user_contacts
                    WHERE user_id = %s
                    ORDER BY contact_type, is_primary DESC, created_at DESC
                ''', (user_id,))
            
            contacts = []
            for row in cursor.fetchall():
                contacts.append({
                    'id': str(row[0]),
                    'contact_type': row[1],
                    'contact_value': row[2],
                    'is_verified': row[3],
                    'is_primary': row[4],
                    'verified_at': row[5].isoformat() if row[5] else None,
                    'created_at': row[6].isoformat() if row[6] else None
                })
            
            cursor.close()
            conn.close()
            return contacts
            
        except Exception as e:
            logger.error(f"Error getting user contacts: {e}")
            return []
    
    def verify_user_contact(self, user_id: str, contact_type: str, contact_value: str) -> bool:
        """
        Marcar contacto como verificado
        
        Args:
            user_id: user_id del usuario (Telegram ID)
            contact_type: Tipo de contacto
            contact_value: Valor del contacto
        
        Returns:
            True si se verificó exitosamente
        """
        if not self.db_url or not PSYCOPG_AVAILABLE:
            return False
        
        conn = self._get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Marcar como verificado (user_id es TEXT, FK directo)
            cursor.execute('''
                UPDATE user_contacts
                SET is_verified = true, verified_at = CURRENT_TIMESTAMP
                WHERE user_id = %s AND contact_type = %s AND contact_value = %s
            ''', (user_id, contact_type, contact_value))
            
            conn.commit()
            success = cursor.rowcount > 0
            cursor.close()
            conn.close()
            
            if success:
                logger.info(f"✅ Contacto verificado: {contact_type} {contact_value} para user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error verifying contact: {e}")
            return False
    
    def set_primary_contact(self, user_id: str, contact_type: str, contact_value: str) -> bool:
        """
        Establecer un contacto como principal para su tipo
        
        Args:
            user_id: user_id del usuario (Telegram ID)
            contact_type: Tipo de contacto
            contact_value: Valor del contacto a marcar como principal
        
        Returns:
            True si se estableció exitosamente
        """
        if not self.db_url or not PSYCOPG_AVAILABLE:
            return False
        
        conn = self._get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Quitar is_primary de todos los contactos de ese tipo
            cursor.execute('''
                UPDATE user_contacts
                SET is_primary = false
                WHERE user_id = %s AND contact_type = %s
            ''', (user_id, contact_type))
            
            # Establecer el nuevo contacto principal
            cursor.execute('''
                UPDATE user_contacts
                SET is_primary = true
                WHERE user_id = %s AND contact_type = %s AND contact_value = %s
            ''', (user_id, contact_type, contact_value))
            
            conn.commit()
            success = cursor.rowcount > 0
            cursor.close()
            conn.close()
            
            if success:
                logger.info(f"✅ Contacto principal establecido: {contact_type} {contact_value} para user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error setting primary contact: {e}")
            return False
    
    # ==========================================
    # RISK MANAGEMENT SYSTEM (RMS) DAL METHODS
    # Nov 27, 2025 - Institutional Risk Control
    # ==========================================
    
    def get_risk_limits(self, user_id: str) -> List[Dict]:
        """
        Obtener límites de riesgo configurados para un usuario
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Lista de límites configurados
        """
        if not self.connected:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, limit_type, limit_value, current_value,
                       is_active, created_at, updated_at
                FROM risk_limits
                WHERE user_id = %s AND is_active = true
                ORDER BY limit_type
            ''', (user_id,))
            
            limits = []
            for row in cursor.fetchall():
                limits.append({
                    'id': row[0],
                    'user_id': row[1],
                    'limit_type': row[2],
                    'threshold_value': float(row[3]) if row[3] else 0,
                    'threshold_unit': 'PERCENT',
                    'warning_threshold_pct': 80.0,
                    'is_active': row[5],
                    'cooldown_minutes': 60,
                    'created_at': row[6],
                    'updated_at': row[7]
                })
            
            cursor.close()
            conn.close()
            return limits
            
        except Exception as e:
            logger.error(f"Error getting risk limits: {e}")
            return []
    
    def set_risk_limit(
        self, 
        user_id: str, 
        limit_type: str, 
        threshold_value: float,
        threshold_unit: str = 'PERCENT',
        warning_threshold_pct: float = 80.0,
        cooldown_minutes: int = 60
    ) -> bool:
        """
        Configurar o actualizar un límite de riesgo
        
        Args:
            user_id: ID del usuario
            limit_type: Tipo de límite
            threshold_value: Valor del umbral
            threshold_unit: Unidad (PERCENT, USD, COUNT)
            warning_threshold_pct: Porcentaje para warning
            cooldown_minutes: Minutos de cooldown
        
        Returns:
            True si se guardó exitosamente
        """
        if not self.connected:
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO risk_limits 
                    (user_id, limit_type, threshold_value, threshold_unit, 
                     warning_threshold_pct, cooldown_minutes, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, limit_type) 
                DO UPDATE SET 
                    threshold_value = EXCLUDED.threshold_value,
                    threshold_unit = EXCLUDED.threshold_unit,
                    warning_threshold_pct = EXCLUDED.warning_threshold_pct,
                    cooldown_minutes = EXCLUDED.cooldown_minutes,
                    updated_at = CURRENT_TIMESTAMP
            ''', (user_id, limit_type, threshold_value, threshold_unit, 
                  warning_threshold_pct, cooldown_minutes))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Risk limit set: {limit_type} = {threshold_value} {threshold_unit} for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting risk limit: {e}")
            return False
    
    def save_risk_breach(self, user_id: str, breach_data: Dict) -> bool:
        """
        Guardar una violación de límite
        
        Args:
            user_id: ID del usuario
            breach_data: Datos de la violación
        
        Returns:
            True si se guardó exitosamente
        """
        if not self.connected:
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO risk_limit_breaches 
                    (user_id, limit_id, limit_type, severity, current_value,
                     threshold_value, percentage_used, action_taken, description, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                user_id,
                breach_data.get('limit_id'),
                breach_data.get('limit_type'),
                breach_data.get('severity'),
                breach_data.get('current_value'),
                breach_data.get('threshold_value'),
                breach_data.get('percentage_used'),
                breach_data.get('action_taken'),
                breach_data.get('description'),
                breach_data.get('metadata')
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Risk breach saved: {breach_data.get('severity')} for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving risk breach: {e}")
            return False
    
    def get_risk_breaches(self, user_id: str, days: int = 30) -> List[Dict]:
        """
        Obtener historial de violaciones de límites
        
        Args:
            user_id: ID del usuario
            days: Días a consultar
        
        Returns:
            Lista de violaciones
        """
        if not self.connected:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, limit_type, severity, current_value, threshold_value,
                       percentage_used, action_taken, description, resolved_at, created_at
                FROM risk_limit_breaches
                WHERE user_id = %s AND created_at >= NOW() - INTERVAL '%s days'
                ORDER BY created_at DESC
            ''', (user_id, days))
            
            breaches = []
            for row in cursor.fetchall():
                breaches.append({
                    'id': row[0],
                    'limit_type': row[1],
                    'severity': row[2],
                    'current_value': float(row[3]) if row[3] else 0,
                    'threshold_value': float(row[4]) if row[4] else 0,
                    'percentage_used': float(row[5]) if row[5] else 0,
                    'action_taken': row[6],
                    'description': row[7],
                    'resolved_at': row[8].isoformat() if row[8] else None,
                    'created_at': row[9].isoformat() if row[9] else None
                })
            
            cursor.close()
            conn.close()
            return breaches
            
        except Exception as e:
            logger.error(f"Error getting risk breaches: {e}")
            return []
    
    def save_risk_metrics_snapshot(self, user_id: str, snapshot_date, metrics: Dict) -> bool:
        """
        Guardar snapshot de métricas de riesgo
        
        Args:
            user_id: ID del usuario
            snapshot_date: Fecha del snapshot
            metrics: Diccionario con métricas
        
        Returns:
            True si se guardó exitosamente
        """
        if not self.connected:
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            import json
            positions_json = json.dumps(metrics.get('positions_breakdown', {}))
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO risk_metrics_snapshots 
                    (user_id, snapshot_date, total_balance_usd, total_exposure_usd,
                     available_balance_usd, daily_pnl_usd, daily_pnl_pct, max_drawdown_usd,
                     max_drawdown_pct, current_drawdown_pct, max_single_position_pct,
                     open_positions, daily_trades_count, volatility_index, risk_score,
                     positions_breakdown)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, snapshot_date) 
                DO UPDATE SET 
                    total_balance_usd = EXCLUDED.total_balance_usd,
                    total_exposure_usd = EXCLUDED.total_exposure_usd,
                    available_balance_usd = EXCLUDED.available_balance_usd,
                    daily_pnl_usd = EXCLUDED.daily_pnl_usd,
                    daily_pnl_pct = EXCLUDED.daily_pnl_pct,
                    max_drawdown_usd = EXCLUDED.max_drawdown_usd,
                    max_drawdown_pct = EXCLUDED.max_drawdown_pct,
                    current_drawdown_pct = EXCLUDED.current_drawdown_pct,
                    max_single_position_pct = EXCLUDED.max_single_position_pct,
                    open_positions = EXCLUDED.open_positions,
                    daily_trades_count = EXCLUDED.daily_trades_count,
                    volatility_index = EXCLUDED.volatility_index,
                    risk_score = EXCLUDED.risk_score,
                    positions_breakdown = EXCLUDED.positions_breakdown
            ''', (
                user_id,
                snapshot_date,
                metrics.get('total_balance_usd', 0),
                metrics.get('total_exposure_usd', 0),
                metrics.get('available_balance_usd', 0),
                metrics.get('daily_pnl_usd', 0),
                metrics.get('daily_pnl_pct', 0),
                metrics.get('max_drawdown_usd', 0),
                metrics.get('max_drawdown_pct', 0),
                metrics.get('current_drawdown_pct', 0),
                metrics.get('max_single_position_pct', 0),
                metrics.get('open_positions', 0),
                metrics.get('daily_trades_count', 0),
                metrics.get('volatility_index', 0),
                metrics.get('risk_score', 0),
                positions_json
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Risk metrics snapshot saved for {user_id} on {snapshot_date}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving risk metrics snapshot: {e}")
            return False
    
    def get_risk_metrics_history(self, user_id: str, days: int = 30) -> List[Dict]:
        """
        Obtener historial de métricas de riesgo
        
        Args:
            user_id: ID del usuario
            days: Días a consultar
        
        Returns:
            Lista de snapshots
        """
        if not self.connected:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT snapshot_date, total_balance_usd, total_exposure_usd,
                       daily_pnl_usd, daily_pnl_pct, current_drawdown_pct,
                       max_single_position_pct, open_positions, daily_trades_count,
                       risk_score, positions_breakdown
                FROM risk_metrics_snapshots
                WHERE user_id = %s AND snapshot_date >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY snapshot_date DESC
            ''', (user_id, days))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'snapshot_date': row[0].isoformat() if row[0] else None,
                    'total_balance_usd': float(row[1]) if row[1] else 0,
                    'total_exposure_usd': float(row[2]) if row[2] else 0,
                    'daily_pnl_usd': float(row[3]) if row[3] else 0,
                    'daily_pnl_pct': float(row[4]) if row[4] else 0,
                    'current_drawdown_pct': float(row[5]) if row[5] else 0,
                    'max_single_position_pct': float(row[6]) if row[6] else 0,
                    'open_positions': row[7] or 0,
                    'daily_trades_count': row[8] or 0,
                    'risk_score': row[9] or 0,
                    'positions_breakdown': row[10] or {}
                })
            
            cursor.close()
            conn.close()
            return history
            
        except Exception as e:
            logger.error(f"Error getting risk metrics history: {e}")
            return []
    
    def get_circuit_breaker_status(self, user_id: str) -> Optional[Dict]:
        """
        Obtener estado del circuit breaker para un usuario
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Dict con estado o None
        """
        if not self.connected:
            return None
        
        try:
            conn = self._get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT is_halted, reason, message, halted_at, resume_at, 
                       halted_by, can_override, updated_at
                FROM circuit_breaker_status
                WHERE user_id = %s
            ''', (user_id,))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row:
                return {
                    'is_halted': row[0],
                    'reason': row[1],
                    'message': row[2],
                    'halted_at': row[3],
                    'resume_at': row[4],
                    'halted_by': row[5],
                    'can_override': row[6],
                    'updated_at': row[7]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting circuit breaker status: {e}")
            return None
    
    def save_circuit_breaker_status(self, user_id: str, status: Dict) -> bool:
        """
        Guardar estado del circuit breaker
        
        Args:
            user_id: ID del usuario
            status: Dict con estado
        
        Returns:
            True si se guardó exitosamente
        """
        if not self.connected:
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO circuit_breaker_status 
                    (user_id, is_halted, reason, message, halted_at, 
                     resume_at, halted_by, can_override, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    is_halted = EXCLUDED.is_halted,
                    reason = EXCLUDED.reason,
                    message = EXCLUDED.message,
                    halted_at = EXCLUDED.halted_at,
                    resume_at = EXCLUDED.resume_at,
                    halted_by = EXCLUDED.halted_by,
                    can_override = EXCLUDED.can_override,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                user_id,
                status.get('is_halted', False),
                status.get('reason'),
                status.get('message'),
                status.get('halted_at'),
                status.get('resume_at'),
                status.get('halted_by', 'system'),
                status.get('can_override', True)
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Circuit breaker status saved for {user_id}: halted={status.get('is_halted')}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving circuit breaker status: {e}")
            return False
    
    def save_risk_alert(self, user_id: str, alert_data: Dict) -> bool:
        """
        Guardar alerta de riesgo (reusa risk_limit_breaches con metadata)
        
        Args:
            user_id: ID del usuario
            alert_data: Datos de la alerta
        
        Returns:
            True si se guardó exitosamente
        """
        import json
        
        breach_data = {
            'limit_type': 'alert',
            'severity': alert_data.get('severity', 'info'),
            'description': f"{alert_data.get('title', '')}: {alert_data.get('message', '')}",
            'action_taken': 'alert_sent',
            'metadata': json.dumps({
                'channel': alert_data.get('channel'),
                'sent_at': alert_data.get('sent_at')
            })
        }
        
        return self.save_risk_breach(user_id, breach_data)
    
    def get_daily_trading_stats(self, user_id: str) -> Optional[Dict]:
        """
        Obtener estadísticas de trading del día actual
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Dict con estadísticas o None
        """
        if not self.connected:
            return None
        
        try:
            conn = self._get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as trades_count,
                    COALESCE(SUM(profit_loss), 0) as daily_pnl,
                    COALESCE(SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END), 0) as wins,
                    COALESCE(SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END), 0) as losses
                FROM paper_trading_trades
                WHERE user_id = %s::TEXT 
                AND DATE(opened_at) = CURRENT_DATE
                AND status = 'closed'
            ''', (user_id,))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row:
                return {
                    'trades_count': row[0] or 0,
                    'daily_pnl': float(row[1]) if row[1] else 0,
                    'wins': row[2] or 0,
                    'losses': row[3] or 0
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting daily trading stats: {e}")
            return None
    
    def get_open_positions(self, user_id: str) -> List[Dict]:
        """
        Obtener posiciones abiertas del usuario
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Lista de posiciones abiertas
        """
        if not self.connected:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT symbol, side, quantity, entry_price, opened_at
                FROM paper_trading_trades
                WHERE user_id = %s::TEXT AND status = 'open'
                ORDER BY opened_at DESC
            ''', (user_id,))
            
            positions = []
            for row in cursor.fetchall():
                entry_price = float(row[3]) if row[3] else 0
                size = float(row[2]) if row[2] else 0
                positions.append({
                    'symbol': row[0],
                    'side': row[1],
                    'quantity': size,
                    'entry_price': entry_price,
                    'current_price': entry_price,
                    'value_usd': size * entry_price,
                    'opened_at': row[4]
                })
            
            cursor.close()
            conn.close()
            return positions
            
        except Exception as e:
            logger.error(f"Error getting open positions: {e}")
            return []
    
    def get_paper_trading_balance(self, user_id: str) -> Optional[Dict]:
        """
        FIX Nov 30, 2025: Método requerido por RMS LimitsEngine
        Obtener balance de paper trading para cálculo de drawdown
        
        IMPORTANTE: Distinguir entre NULL (no existe) y 0 (balance agotado real)
        - NULL → usuario no inicializado → retorna balance inicial $1M
        - 0 → balance real agotado → preservar 0 para que RMS detecte drawdown
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Dict con balance y available, o balance inicial si no existe
        """
        INITIAL_BALANCE = 1000000.0
        
        if not self.connected:
            logger.warning(f"⚠️ get_paper_trading_balance: DB not connected, returning initial balance for {user_id}")
            return {
                'balance': INITIAL_BALANCE,
                'available': INITIAL_BALANCE,
                'total_pnl': 0
            }
        
        try:
            conn = self._get_connection()
            if not conn:
                logger.warning(f"⚠️ get_paper_trading_balance: No connection, returning initial balance for {user_id}")
                return {
                    'balance': INITIAL_BALANCE,
                    'available': INITIAL_BALANCE,
                    'total_pnl': 0
                }
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT balance_usd, available_margin_usd, total_realized_pnl_usd
                FROM paper_trading_balances
                WHERE user_id = %s
            ''', (user_id,))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row:
                # FIX: Usar is None para distinguir NULL de 0
                # Si el valor es 0, mantenerlo como 0 (balance agotado real)
                # Si es NULL, usar default (no debería pasar con schema correcto)
                balance = float(row[0]) if row[0] is not None else INITIAL_BALANCE
                available = float(row[1]) if row[1] is not None else balance
                total_pnl = float(row[2]) if row[2] is not None else 0
                
                return {
                    'balance': balance,
                    'available': available,
                    'total_pnl': total_pnl
                }
            
            # Usuario no existe en paper_trading_balances
            # Esto es normal para usuarios nuevos que aún no han hecho /paper_start
            logger.info(f"📊 get_paper_trading_balance: User {user_id} not initialized, returning initial balance")
            return {
                'balance': INITIAL_BALANCE,
                'available': INITIAL_BALANCE,
                'total_pnl': 0
            }
            
        except Exception as e:
            logger.error(f"Error getting paper trading balance: {e}")
            # En caso de error de DB, asumir usuario nuevo para no bloquear trading
            return {
                'balance': INITIAL_BALANCE,
                'available': INITIAL_BALANCE,
                'total_pnl': 0
            }
    
    def get_recent_trades(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Obtener trades recientes para detectar pérdidas consecutivas
        
        Args:
            user_id: ID del usuario
            limit: Número de trades a obtener
        
        Returns:
            Lista de trades recientes
        """
        if not self.connected:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT symbol, side, quantity, entry_price, exit_price, profit_loss, closed_at
                FROM paper_trading_trades
                WHERE user_id = %s::TEXT AND status = 'closed'
                ORDER BY closed_at DESC
                LIMIT %s
            ''', (user_id, limit))
            
            trades = []
            for row in cursor.fetchall():
                trades.append({
                    'symbol': row[0],
                    'side': row[1],
                    'size': float(row[2]) if row[2] else 0,
                    'entry_price': float(row[3]) if row[3] else 0,
                    'exit_price': float(row[4]) if row[4] else 0,
                    'profit': float(row[5]) if row[5] else 0,
                    'closed_at': row[6]
                })
            
            cursor.close()
            conn.close()
            return trades
            
        except Exception as e:
            logger.error(f"Error getting recent trades: {e}")
            return []
    
    def get_cached_transcript(self, video_id: str) -> Optional[str]:
        """
        Obtener transcripción cacheada de un video
        
        Args:
            video_id: ID del video de YouTube
            
        Returns:
            Transcripción si existe y no ha expirado, None si no existe
        """
        if not self.connected:
            return None
        
        try:
            conn = self._get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT transcript FROM video_transcript_cache
                WHERE video_id = %s AND expires_at > CURRENT_TIMESTAMP
            ''', (video_id,))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if row:
                logger.info(f"✅ Transcripción encontrada en caché para video {video_id}")
                return row[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached transcript: {e}")
            return None
    
    def save_transcript_cache(self, video_id: str, transcript: str, source: str = 'whisper', duration_seconds: int = None) -> bool:
        """
        Guardar transcripción en caché
        
        Args:
            video_id: ID del video de YouTube
            transcript: Texto de la transcripción
            source: Fuente de la transcripción (whisper, youtube, etc.)
            duration_seconds: Duración del video en segundos
            
        Returns:
            True si exitoso, False si falla
        """
        if not self.connected or not transcript:
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO video_transcript_cache (video_id, transcript, source, duration_seconds)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (video_id) DO UPDATE SET
                    transcript = EXCLUDED.transcript,
                    source = EXCLUDED.source,
                    duration_seconds = EXCLUDED.duration_seconds,
                    created_at = CURRENT_TIMESTAMP,
                    expires_at = CURRENT_TIMESTAMP + INTERVAL '30 days'
            ''', (video_id, transcript, source, duration_seconds))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"✅ Transcripción guardada en caché para video {video_id} ({len(transcript)} chars)")
            return True
            
        except Exception as e:
            logger.error(f"Error saving transcript cache: {e}")
            return False
