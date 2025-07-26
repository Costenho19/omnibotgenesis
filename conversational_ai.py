# conversational_ai.py

from googletrans import Translator
from gtts import gTTS
import tempfile
import os
from openai import OpenAI
from config import OPENAI_API_KEY

translator = Translator()
openai = OpenAI(api_key=OPENAI_API_KEY)

# Memoria simple por usuario
user_memory = {}

class ConversationalAI:
    def __init__(self):
        self.default_lang = "es"

    def detect_language(self, message: str) -> str:
        try:
            lang = translator.detect(message).lang
            return lang if lang in ['es', 'en', 'ar', 'zh-cn'] else self.default_lang
        except:
            return self.default_lang

    def translate_input(self, message: str, target_lang: str = "en") -> str:
        try:
            return translator.translate(message, dest=target_lang).text
        except:
            return message

    def translate_output(self, message: str, target_lang: str) -> str:
        try:
            return translator.translate(message, dest=target_lang).text
        except:
            return message

 # Guardar la memoria del usuario (IA contextual)
async def save_user_memory(user_id: str, memory: str):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        INSERT INTO user_memory (user_id, ai_response)
        VALUES ($1, $2)
        ON CONFLICT (user_id) DO UPDATE SET ai_response = EXCLUDED.ai_response
    """, user_id, memory)
    await conn.close()

# Recuperar la memoria previa del usuario
async def generate_response_with_memory(user_id: str, user_input: str, language: str) -> str:
    # Obtener memoria previa
    memory = await get_user_memory(user_id)

    # Preparar contexto para GPT-4
    context = f"""Eres OMNIX, un asistente inteligente. Este es el historial del usuario:
{memory}

Ahora el usuario dice: {user_input}
Responde de forma útil, clara y profesional."""

    # Generar respuesta con OpenAI GPT-4
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un asistente profesional con memoria contextual."},
                {"role": "user", "content": context}
            ],
            temperature=0.7,
            max_tokens=300
        )
        ai_response = response.choices[0].message.content.strip()
    except Exception as e:
        ai_response = "⚠️ Ocurrió un error al generar la respuesta con memoria."
async def generate_response_with_memory(user_id: str, user_input: str, language: str) -> str:
    # Obtener memoria previa
    memory = await get_user_memory(user_id)

    # Preparar contexto para GPT-4
    context = f"""Eres OMNIX, un asistente inteligente. Este es el historial del usuario:
{memory}

Ahora el usuario dice: {user_input}
Responde de forma útil, clara y profesional."""

    # Generar respuesta con OpenAI GPT-4
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un asistente profesional con memoria contextual."},
                {"role": "user", "content": context}
            ],
            temperature=0.7,
            max_tokens=300
        )
        ai_response = response.choices[0].message.content.strip()
   await save_user_memory(user_id, ai_response)

    except Exception as e:
        ai_response = "⚠️ Ocurrió un error al generar la respuesta con memoria."

    # Guardar la nueva interacción en memoria
    new_memory = memory + f"\nUsuario: {user_input}\nOMNIX: {ai_response}"
    await save_user_memory(user_id, new_memory)

    return ai_response

    # Guardar la nueva interacción en memoria
    new_memory = memory + f"\nUsuario: {user_input}\nOMNIX: {ai_response}"
    await save_user_memory(user_id, new_memory)

    return ai_response

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
# LÍNEA 121
from googletrans import Translator
from langdetect import detect

# LÍNEA 124
translator = Translator()

# LÍNEA 126
def traducir_mensaje(texto: str, idioma_destino: str) -> str:
    try:
        return translator.translate(texto, dest=idioma_destino).text
    except:
        return texto  # Si falla, devuelve el original

