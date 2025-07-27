import openai
from config import OPENAI_API_KEY
import logging

# Activamos la clave de OpenAI
openai.api_key = OPENAI_API_KEY

# Clase para gestionar IA conversacional ChatGPT
class ChatGPTConversationalAI:
    def __init__(self):
        self.user_memory = {}  # Memoria por usuario
        self.model = "gpt-4"   # Puedes cambiar a "gpt-3.5-turbo" si quieres

    def get_chat_history(self, user_id):
        return self.user_memory.get(user_id, [])

    def update_chat_history(self, user_id, role, content):
        if user_id not in self.user_memory:
            self.user_memory[user_id] = []
        self.user_memory[user_id].append({"role": role, "content": content})
        # Limitamos la memoria a los últimos 10 mensajes
        self.user_memory[user_id] = self.user_memory[user_id][-10:]

    def generate_response(self, user_id, message):
        try:
            self.update_chat_history(user_id, "user", message)
            messages = self.get_chat_history(user_id)

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=0.7
            )

            reply = response["choices"][0]["message"]["content"]
            self.update_chat_history(user_id, "assistant", reply)
            return reply

        except Exception as e:
            logging.error(f"Error al generar respuesta de ChatGPT: {e}")
            return "Lo siento, hubo un error al gener
