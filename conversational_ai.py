import logging
from typing import Dict, List
from langdetect import detect
from gtts import gTTS
import openai
import tempfile
import os

# --- Configuración Segura ---
try:
    from config import OPENAI_API_KEY
except ImportError:
    OPENAI_API_KEY = None

openai.api_key = OPENAI_API_KEY
logger = logging.getLogger(__name__)

class ConversationalAI:
    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self.user_memory: Dict[str, List[Dict[str, str]]] = {}
        if not OPENAI_API_KEY:
            logger.warning("🔒 OPENAI_API_KEY no encontrada. El módulo conversacional estará inactivo.")
            self.client = None
        else:
            self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
            logger.info("🤖 Módulo Conversacional OMNIX activo con modelo: " + model)

    def _get_chat_history(self, user_id: str) -> List[Dict[str, str]]:
        return self.user_memory.get(user_id, [])

    def _update_chat_history(self, user_id: str, role: str, content: str):
        if user_id not in self.user_memory:
            self.user_memory[user_id] = [
                {"role": "system", "content": "Eres OMNIX, un asistente de trading profesional, empático y preciso. Responde con claridad, educación y seguridad, adaptando tu lenguaje al idioma y emociones del usuario."}
            ]
        self.user_memory[user_id].append({"role": role, "content": content})
        self.user_memory[user_id] = self.user_memory[user_id][-11:]

    def detect_language(self, text: str) -> str:
        try:
            lang = detect(text)
            return lang if lang in ['es', 'en', 'ar', 'zh-cn'] else 'en'
        except Exception:
            return 'en'

    def generate_response(self, user_id: str, message: str) -> str:
        if not self.client:
            return "La función de IA está inactiva por falta de clave."
        try:
            self._update_chat_history(user_id, "user", message)
            messages = self._get_chat_history(user_id)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=200
            )
            reply = response.choices[0].message.content.strip()
            self._update_chat_history(user_id, "assistant", reply)
            return reply
        except Exception as e:
            logger.error(f"❌ Error al generar respuesta: {e}")
            return "Ocurrió un error al procesar tu mensaje. Intenta de nuevo."

    def generate_emotional_response(self, text: str, user_id: str = "default") -> str:
        if not self.client:
            return "La IA emocional está inactiva por falta de clave."
        try:
            prompt = (
                f"Responde con empatía, calidez y un toque humano al siguiente mensaje del usuario:\n"
                f"{text}\n\n"
                f"Tu rol: Asistente de IA empático especializado en trading, emociones humanas y ayuda positiva.\n"
                f"Responde de forma cercana, clara y emocionalmente adaptada al tono del mensaje original."
            )
            self._update_chat_history(user_id, "user", prompt)
            messages = self._get_chat_history(user_id)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.85,
                max_tokens=250
            )
            reply = response.choices[0].message.content.strip()
            self._update_chat_history(user_id, "assistant", reply)
            return reply
        except Exception as e:
            logger.error(f"💬 Error en respuesta emocional: {e}")
            return "Estoy aquí para ayudarte con lo que necesites, aunque hubo un pequeño error procesando tu mensaje."

    def generate_voice_response(self, text: str, lang: str = "es") -> str:
        try:
            tts = gTTS(text=text, lang=lang)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                tts.save(f.name)
                return f.name
        except Exception as e:
            logger.error(f"🎙 Error generando voz: {e}")
            return None

    def full_response(self, user_id: str, message: str) -> Dict[str, str]:
        lang = self.detect_language(message)
        text = self.generate_response(user_id, message)
        audio_path = self.generate_voice_response(text, lang)
        return {
            "text": text,
            "voice": audio_path,
            "lang": lang
        }
# === WRAPPER GLOBAL PARA IMPORTAR GENERATE_RESPONSE ===
from conversational_ai import ConversationalAI

ai = ConversationalAI()

def generate_response(user_id: str, message: str) -> str:
    return ai.generate_response(user_id, message)
