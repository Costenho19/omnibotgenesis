import psycopg2
import logging
import json
from quantum_security import encrypt_message, decrypt_message

from config import DATABASE_URL

logger = logging.getLogger(__name__)

def get_db_connection():
    """Establece una conexión con la base de datos PostgreSQL en Neon."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"FATAL: No se pudo conectar a la base de datos: {e}")
        return None

def setup_premium_database():
    """Configura las tablas en la base de datos PostgreSQL si no existen."""
    conn = get_db_connection()
    if not conn: return

    try:
        with conn.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS premium_assets (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT UNIQUE NOT NULL, name TEXT, type TEXT, market TEXT,
                    sector TEXT, country TEXT, currency TEXT, market_cap BIGINT,
                    premium_tier INTEGER DEFAULT 1,
                    added_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_analysis (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    current_price REAL, ai_prediction_1h REAL, ai_prediction_24h REAL,
                    ai_prediction_7d REAL, confidence_score REAL, volatility_forecast REAL,
                    momentum_score REAL, risk_score REAL, support_levels TEXT,
                    resistance_levels TEXT, news_sentiment REAL,
                    social_sentiment REAL, recommendation TEXT
                );
            ''')
        conn.commit()
        logger.info("Base de datos y tablas verificadas/creadas correctamente.")
    except Exception as e:
        logger.error(f"Error al configurar la base de datos: {e}")
    finally:
        if conn: conn.close()

def add_premium_assets(premium_assets: list):
    """Agrega una lista de activos premium a la base de datos."""
    conn = get_db_connection()
    if not conn: return
    
    sql = '''
        INSERT INTO premium_assets (symbol, name, type, market, sector, country, currency, market_cap, premium_tier)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (symbol) DO NOTHING;
    '''
    
    try:
        with conn.cursor() as cursor:
            cursor.executemany(sql, premium_assets)
        conn.commit()
        logger.info(f"{cursor.rowcount} nuevos activos premium fueron insertados.")
    except Exception as e:
        logger.error(f"Error agregando activos premium: {e}")
        conn.rollback()
    finally:
        if conn: conn.close()

def save_analysis_to_db(result):
    """Guarda un resultado de análisis en la base de datos."""
   def save_analysis_to_db(user_id, asset, analysis_text, result_dict):
    from datetime import datetime

    # 🔐 Ciframos los datos con seguridad cuántica
    encrypted_analysis = encrypt_message(analysis_text)
    encrypted_result = encrypt_message(json.dumps(result_dict))

    try:
        conn = get_db_connection()
        if not conn:
            return
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO ai_analysis (user_id, asset, analysis, result, timestamp)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, asset, encrypted_analysis, encrypted_result, datetime.utcnow())
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"❌ Error al guardar análisis cifrado: {e}")

    def crear_tabla_voice_signatures():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voice_signatures (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                texto_transcrito TEXT NOT NULL,
                firma_dilithium TEXT NOT NULL,
                hash_vocal TEXT NOT NULL,
                biometria_valida BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Tabla 'voice_signatures' creada correctamente.")
    except Exception as e:
        print(f"❌ Error al crear la tabla 'voice_signatures': {e}")
    # Crear tabla para guardar firmas de voz
def setup_voice_signature_table():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS voice_signatures (
        user_id TEXT PRIMARY KEY,
        voice_signature TEXT,
        dilithium_signature TEXT
    );
''')

    conn.commit()
    cur.close()
    conn.close()

# 🧠 Memoria contextual por usuario (IA)
def create_user_memory_table():
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_memory (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    user_input TEXT,
                    ai_response TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            logger.info("Tabla user_memory creada correctamente.")
    except Exception as e:
        logger.error(f"❌ Error al crear la tabla de memoria contextual: {e}")
    finally:
        conn.close()
# L140 - Manejo de memoria contextual del usuario

async def save_user_memory(user_id: str, memory: str):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        INSERT INTO user_memory (user_id, memory)
        VALUES ($1, $2)
        ON CONFLICT (user_id) DO UPDATE SET memory = EXCLUDED.memory
    """, user_id, memory)
    await conn.close()

async def get_user_memory(user_id: str) -> str:
    conn = await asyncpg.connect(DATABASE_URL)
    row = await conn.fetchrow("SELECT memory FROM user_memory WHERE user_id = $1", user_id)
    await conn.close()
    return row["memory"] if row else ""

def save_user_memory(user_id, user_input, ai_response):
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_memory (user_id, user_input, ai_response)
                VALUES (%s, %s, %s);
            """, (user_id, user_input, ai_response))
            conn.commit()
    except Exception as e:
        logger.error(f"❌ Error al guardar memoria del usuario: {e}")
    finally:
        conn.close()

def get_user_memory(user_id, limit=5):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT user_input, ai_response
                FROM user_memory
                WHERE user_id = %s
                ORDER BY timestamp DESC
                LIMIT %s;
            """, (user_id, limit))
            rows = cursor.fetchall()
            return rows[::-1]  # orden cronológico
    except Exception as e:
        logger.error(f"❌ Error al obtener memoria del usuario: {e}")
        return []
    finally:
        conn.close()
import asyncpg

async def setup_memory_table():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_memory (
            user_id TEXT PRIMARY KEY,
            memory TEXT
        )
    """)
    await conn.close()
import psycopg2
from config import DATABASE_URL

def setup_memory_table():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_memory (
            user_id TEXT PRIMARY KEY,
            memory TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

async def save_user_memory(user_id: str, new_message: str):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT memory FROM user_memory WHERE user_id = %s;", (user_id,))
    result = cur.fetchone()

    if result:
        updated_memory = result[0] + "\n" + new_message
        cur.execute("UPDATE user_memory SET memory = %s WHERE user_id = %s;", (updated_memory, user_id))
    else:
        cur.execute("INSERT INTO user_memory (user_id, memory) VALUES (%s, %s);", (user_id, new_message))

    conn.commit()
    cur.close()
    conn.close()

async def get_user_memory(user_id: str) -> str:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT memory FROM user_memory WHERE user_id = %s;", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else ""
def setup_language_table():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_language (
            user_id TEXT PRIMARY KEY,
            language TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

async def set_user_language(user_id: str, language: str):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT language FROM user_language WHERE user_id = %s;", (user_id,))
    result = cur.fetchone()
    if result:
        cur.execute("UPDATE user_language SET language = %s WHERE user_id = %s;", (language, user_id))
    else:
        cur.execute("INSERT INTO user_language (user_id, language) VALUES (%s, %s);", (user_id, language))
    conn.commit()
    cur.close()
    conn.close()

async def get_user_language(user_id: str) -> str:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT language FROM user_language WHERE user_id = %s;", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else "es"
async def setup_language_table():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_language (
            user_id TEXT PRIMARY KEY,
            language TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

async def save_user_language(user_id: str, language: str):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT language FROM user_language WHERE user_id = %s;", (user_id,))
    result = cur.fetchone()
    if result:
        cur.execute("UPDATE user_language SET language = %s WHERE user_id = %s;", (language, user_id))
    else:
        cur.execute("INSERT INTO user_language (user_id, language) VALUES (%s, %s);", (user_id, language))
    conn.commit()
    cur.close()
    conn.close()

async def get_user_language(user_id: str) -> str:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT language FROM user_language WHERE user_id = %s;", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None

import psycopg2
from config import DATABASE_URL

def save_dilithium_signature(user_id: str, signature: str, timestamp: int):
    """Guarda la firma digital junto con el timestamp en la base de datos."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dilithium_signatures (
            id SERIAL PRIMARY KEY,
            user_id TEXT,
            signature TEXT,
            timestamp BIGINT
        )
    """)
    cur.execute("""
        INSERT INTO dilithium_signatures (user_id, signature, timestamp)
        VALUES (%s, %s, %s)
    """, (user_id, signature, timestamp))
    conn.commit()
    cur.close()
    conn.close()

