import openai
import logging
from typing import Dict, List
from config import OPENAI_API_KEY

# Configuramos el cliente de OpenAI
openai.api_key = OPENAI_API_KEY
logger = logging.getLogger(__name__)

class ConversationalAI:
    """
    Clase para manejar la inteligencia artificial conversacional utilizando OpenAI (GPT-4 o 3.5).
    """

    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self.user_memory: Dict[str, List[Dict[str, str]]] = {}

    def _get_history(self, user_id: str) -> List[Dict[str, str]]:
        return self.user_memory.get(user_id, [])

    def _update_history(self, user_id: str, role: str, content: str):
        if user_id not in self.user_memory:
            self.user_memory[user_id] = [
                {"role": "system", "content": "Eres OMNIX, un asistente financiero inteligente y amigable. Responde con claridad y precisión."}
            ]
        self.user_memory[user_id].append({"role": role, "content": content})
        self.user_memory[user_id] = self.user_memory[user_id][-11:]  # Últimos 5 intercambios + system

    def generate_response(self, user_id: str, message: str) -> str:
        try:
            self._update_history(user_id, "user", message)
            messages = self._get_history(user_id)

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )

            reply = response["choices"][0]["message"]["content"].strip()
            self._update_history(user_id, "assistant", reply)
            return reply

        except Exception as e:
            logger.error(f"❌ Error al generar respuesta de OpenAI: {e}")
            return "Lo siento, hubo un problema al generar la respuesta con inteligencia artificial."

# --- Prueba local (opcional) ---
if __name__ == '__main__':
    if not OPENAI_API_KEY:
        print("⚠️ Falta la clave de OpenAI.")
    else:
        bot = ConversationalAI()
        uid = "test_user"
        print("[Usuario] Hola, ¿quién eres?")
        print("[OMNIX] ", bot.generate_response(uid, "Hola, ¿quién eres?"))
