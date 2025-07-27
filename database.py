import psycopg2
import json
import logging
from datetime import datetime
from pqc_encryption import encrypt_message
from config import DATABASE_URL

logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"❌ Error al conectar con la base de datos: {e}")
        return None

def setup_premium_database(premium_assets):
    """
    Inserta los activos premium iniciales en la base de datos.
    """
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO premium_assets (symbol, name, sector, added_at)
            VALUES (%s, %s, %s, NOW())
            """
            cursor.executemany(sql, premium_assets)
            conn.commit()
            logger.info(f"{cursor.rowcount} nuevos activos premium fueron insertados.")
    except Exception as e:
       logger.error(f"❌ Error agregando activos premium: {e}")

        conn.rollback()
    finally:
        if conn:
            conn.close()

def crear_tabla_voice_signatures():
    try:
        conn = get_db_connection()
        if not conn:
            return

        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS voice_signatures (
                user_id TEXT PRIMARY KEY,
                signature BYTEA,
                created_at TIMESTAMP DEFAULT NOW()
            )
            """
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"❌ Error creando tabla de firmas de voz: {e}")

def save_analysis_to_db(user_id, asset, analysis_text, result_dict):
    """
    Guarda un resultado de análisis en la base de datos con cifrado post-cuántico.
    """
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
        logger.error(f"❌ Error guardando análisis cifrado: {e}")
