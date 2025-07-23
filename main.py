import os
from gtts import gTTS
from google.generativeai import configure, GenerativeModel
from config import GEMINI_API_KEY

# Configuración de la API de Gemini
configure(api_key=GEMINI_API_KEY)

# Lista de idiomas soportados para TTS
VOICE_LANGUAGES = {
    'es': 'es',
    'en': 'en',
    'ar': 'ar',
    'zh': 'zh'
}

class ConversationalAI:
    def __init__(self):
        self.model = GenerativeModel("gemini-pro")
        self.memory = {}  # Memoria por usuario

    def get_response(self, user_id, message, language='es'):
        try:
            # Crear historial si no existe
            if user_id not in self.memory:
                self.memory[user_id] = []

            # Añadir nuevo mensaje del usuario al historial
            self.memory[user_id].append({"role": "user", "parts": [message]})

            # Obtener respuesta del modelo
            response = self.model.generate_content(self.memory[user_id])

            # Extraer texto de la respuesta
            response_text = response.text

            # Añadir respuesta del bot al historial
            self.memory[user_id].append({"role": "model", "parts": [response_text]})

            # Generar archivo de audio con gTTS
            tts_lang = VOICE_LANGUAGES.get(language, 'es')
            tts = gTTS(text=response_text, lang=tts_lang)
            audio_path = f"response_{user_id}.mp3"
            tts.save(audio_path)

            return response_text, audio_path

        except Exception as e:
            print(f"[ConversationalAI] Error: {e}")
            return "Lo siento, ocurrió un error al procesar tu mensaje.", None


        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response_text
        )

        if audio_file:
            with open(audio_file, 'rb') as audio:
                await context.bot.send_voice(
                    chat_id=update.effective_chat.id,
                    voice=audio
                )
    except Exception as e:
    
# Configuración de la API de Gemini
configure(api_key=GEMINI_API_KEY)

# Lista de idiomas soportados para TTS
VOICE_LANGUAGES = {
    'es': 'es',
    'en': 'en',
    'ar': 'ar',
    'zh': 'zh'
}

class ConversationalAI:
    def __init__(self):
        self.model = GenerativeModel("gemini-pro")
        self.memory = {}  # Memoria por usuario

    def get_response(self, user_id, message, language='es'):
        try:
            # Crear historial si no existe
            if user_id not in self.memory:
                self.memory[user_id] = []

            # Añadir nuevo mensaje del usuario al historial
            self.memory[user_id].append({"role": "user", "parts": [message]})

            # Obtener respuesta del modelo
            response = self.model.generate_content(self.memory[user_id])

            # Extraer texto de la respuesta
            response_text = response.text

            # Añadir respuesta del bot al historial
            self.memory[user_id].append({"role": "model", "parts": [response_text]})

            # Generar archivo de audio con gTTS
            tts_lang = VOICE_LANGUAGES.get(language, 'es')
            tts = gTTS(text=response_text, lang=tts_lang)
            audio_path = f"response_{user_id}.mp3"
            tts.save(audio_path)

            return response_text, audio_path

        except Exception as e:
            print(f"[ConversationalAI] Error: {e}")
            return "Lo siento, ocurrió un error al procesar tu mensaje.", None

        

# ------------------ MAIN ------------------

# ------------------- MAIN -------------------
async def main():
    logger.info("Iniciando OMNIX Bot...")

    if not BOT_TOKEN:
        logger.critical("FATAL: BOT_TOKEN no encontrado.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("estado", estado_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("trading", trading_command))
    application.add_handler(CommandHandler("ask", ask_command))

    # Texto libre (IA y voz)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    logger.info("✅ OMNIX activo 🔥")
    await application.run_polling()


# ------------------ RUN ------------------

if __name__ == "__main__":
    import nest_asyncio
    import asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())

