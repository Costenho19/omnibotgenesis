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

    def update_memory(self, user_id: int, message: str):
        if user_id not in user_memory:
            user_memory[user_id] = []
        user_memory[user_id].append(message)
        if len(user_memory[user_id]) > 5:
            user_memory[user_id] = user_memory[user_id][-5:]

    def get_memory(self, user_id: int) -> str:
        if user_id in user_memory:
            return "\n".join(user_memory[user_id])
        return ""

    def generate_response(self, user_id: int, message: str, lang: str) -> str:
        self.update_memory(user_id, message)
        history = self.get_memory(user_id)

        prompt = f"Historial:\n{history}\nUsuario: {message}\nAsistente:"
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un asistente útil y multilingüe."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            reply = response.choices[0].message.content.strip()
        except Exception as e:
            reply = "Lo siento, hubo un problema al generar la respuesta."

        translated_reply = self.translate_output(reply, target_lang=lang)
        return translated_reply

    def generate_voice(self, message: str, lang: str) -> str:
        try:
            tts = gTTS(text=message, lang=lang if lang != "zh-cn" else "zh")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                tts.save(f.name)
                return f.name
        except Exception as e:
            return None
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

