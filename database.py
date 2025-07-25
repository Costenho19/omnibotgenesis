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
