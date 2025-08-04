import psycopg2
import json
import logging
from datetime import datetime

# --- Importaciones de Módulos Internos ---
try:
    import os
    from pqc_encryption import encrypt_message
    DATABASE_URL = os.environ.get("DATABASE_URL")
except ImportError as e:
    print(f"⚠️ ADVERTENCIA en database.py: No se pudieron importar módulos. {e}")
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
        logger.error(f"❌ Error al conectar a la base de datos: {e}")
        return None


