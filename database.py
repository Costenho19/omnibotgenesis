import psycopg2
import json
import logging
from datetime import datetime

# --- Importaciones de Módulos Internos ---
# Hacemos una importación segura para evitar que el programa se caiga si los otros archivos aún no están listos.
try:
    import os
from pqc_encryption import encrypt_message
DATABASE_URL = os.environ.get("DATABASE_URL")

except ImportError as e:
    print(f"ADVERTENCIA en database.py: No se pudieron importar módulos. {e}")
    # Definimos variables falsas para que el resto del archivo no de error al cargar.
    DATABASE_URL = None
    def encrypt_message(msg): return msg

logger = logging.getLogger(__name__)

# --- FUNCIÓN PRINCIPAL DE CONEXIÓN ---

def get_db_connection():
    """
    Establece y devuelve una conexión con la base de datos PostgreSQL.
    Maneja los errores de conexión de forma segura.
    """
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL no está configurada. No se puede conectar a la base de datos.")
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"❌ Error crítico al conectar con la base de datos: {e}")
        return None

# --- SECCIÓN DE CREACIÓN Y CONFIGURACIÓN DE TABLAS (SETUP) ---

def setup_premium_database():
    """
    Crea todas las tablas necesarias si no existen.
    Esta función actúa como el punto de entrada para inicializar la BD.
    """
    _crear_tabla_premium_assets()
    _crear_tabla_voice_signatures()
    _crear_tabla_ai_analysis()
    # Aquí puedes añadir llamadas a otras funciones para crear más tablas en el futuro.

def _crear_tabla_premium_assets():
    """Crea la tabla 'premium_assets' para almacenar la lista de activos."""
    conn = get_db_connection()
    if not conn: return
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS premium_assets (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT UNIQUE NOT NULL,
                    name TEXT,
                    sector TEXT,
                    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            logger.info("✅ Tabla 'premium_assets' verificada/creada correctamente.")
    except Exception as e:
        logger.error(f"❌ Error al crear la tabla 'premium_assets': {e}")
        conn.rollback()
    finally:
        if conn: conn.close()

def _crear_tabla_voice_signatures():
    """Crea la tabla 'voice_signatures' para las firmas biométricas."""
    conn = get_db_connection()
    if not conn: return
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS voice_signatures (
                    user_id TEXT PRIMARY KEY,
                    signature BYTEA NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            logger.info("✅ Tabla 'voice_signatures' verificada/creada correctamente.")
    except Exception as e:
        logger.error(f"❌ Error al crear la tabla 'voice_signatures': {e}")
        conn.rollback()
    finally:
        if conn: conn.close()
        
def _crear_tabla_ai_analysis():
    """Crea la tabla 'ai_analysis' para guardar los análisis generados."""
    conn = get_db_connection()
    if not conn: return

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_analysis (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    analysis BYTEA,
                    result BYTEA,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            logger.info("✅ Tabla 'ai_analysis' verificada/creada correctamente.")
    except Exception as e:
        logger.error(f"❌ Error al crear la tabla 'ai_analysis': {e}")
        conn.rollback()
    finally:
        if conn: conn.close()


# --- SECCIÓN DE INSERCIÓN Y ACTUALIZACIÓN DE DATOS (OPERACIONES) ---

def add_premium_assets(premium_assets_list):
    """Inserta la lista de activos premium en la base de datos, ignorando duplicados."""
    conn = get_db_connection()
    if not conn: return

    # Preparamos los datos para la inserción.
    assets_to_insert = [(asset['symbol'], asset['name'], asset['sector']) for asset in premium_assets_list]
    
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO premium_assets (symbol, name, sector)
                VALUES (%s, %s, %s)
                ON CONFLICT (symbol) DO NOTHING;
            """
            cursor.executemany(sql, assets_to_insert)
            conn.commit()
            logger.info(f"✅ {cursor.rowcount or 0} nuevos activos premium insertados en la BD.")
    except Exception as e:
        logger.error(f"❌ Error agregando activos premium a la BD: {e}")
        conn.rollback()
    finally:
        if conn: conn.close()

def save_analysis_to_db(user_id, asset, analysis_text, result_dict):
    """
    Guarda un resultado de análisis en la base de datos con cifrado post-cuántico.
    """
    try:
        # Ciframos los datos antes de guardarlos.
        encrypted_analysis = encrypt_message(analysis_text)
        encrypted_result = encrypt_message(json.dumps(result_dict))

        conn = get_db_connection()
        if not conn: return
        
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO ai_analysis (user_id, asset, analysis, result, timestamp)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (str(user_id), asset, encrypted_analysis, encrypted_result, datetime.utcnow())
            )
            conn.commit()
    except Exception as e:
        logger.error(f"❌ Error guardando análisis cifrado en la BD: {e}")

# Aquí puedes añadir más funciones para interactuar con la base de datos en el futuro,
# como 'save_dilithium_signature', 'guardar_usuario_premium', 'es_usuario_premium', etc.
# database.py

def get_user_memory(user_id: str) -> str:
    # Aquí va la lógica real para obtener memoria del usuario desde PostgreSQL o lo que uses
    # Ejemplo básico para evitar que el bot falle:
    return ""
# ============================================================
# === FUNCIÓN PARA GUARDAR SUGERENCIAS DE LOS USUARIOS ======
# ============================================================

import datetime

async def guardar_sugerencia(user_id: int, sugerencia: str, db_pool=None):
    try:
        if db_pool is None:
            from .config import DATABASE_URL
            import asyncpg
            db_pool = await asyncpg.create_pool(DATABASE_URL)

        async with db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sugerencias (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    sugerencia TEXT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await conn.execute("""
                INSERT INTO sugerencias (user_id, sugerencia, fecha)
                VALUES ($1, $2, $3);
            """, user_id, sugerencia, datetime.datetime.utcnow())
    except Exception as e:
        print(f"[ERROR] guardando sugerencia: {e}")
