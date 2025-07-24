import logging
import gtts
import io

# Importamos las claves desde nuestro archivo de configuración central
from config import GEMINI_API_KEY
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Configuramos la API de Gemini si la clave existe
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Error al configurar la API de Gemini: {e}")

class ConversationalAI:
    """Sistema de IA conversacional cuadrilingüe"""
    
    def __init__(self):
        self.conversation_memory = {}
        self.supported_languages = ['es', 'en', 'ar', 'zh']
        # Inicializamos el modelo de Gemini aquí para poder reutilizarlo
        if GEMINI_API_KEY:
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
            logger.warning("Clave de API de Gemini no encontrada. La IA conversacional avanzada está deshabilitada.")
        
    def get_ai_response(self, text: str, user_id: str) -> str:
        """Generar respuesta de IA usando Gemini."""
        if not self.model:
            return "Lo siento, la función de chat no está disponible en este momento."

        # Mantenemos un historial simple de la conversación
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = []
        
        # Creamos el prompt para la IA
        prompt = f"""
        Eres OMNIX, un bot de trading experto y amigable. Un usuario te ha dicho: '{text}'.
        Tu historial de conversación reciente con este usuario es: {self.conversation_memory[user_id][-5:]}
        Responde de manera concisa, útil y amigable.
        """
        
               try:
            response = self.model.generate_content(prompt)
            ai_text = response.text

            # Actualizamos el historial
            self.conversation_memory[user_id].append(f"User: {text}\nAI: {ai_text}")

            voice_fp = self.text_to_speech(ai_text, lang='es')
            return {"text": ai_text, "voice": voice_fp}

        except Exception as e:
            logger.error(f"Error al generar respuesta de Gemini: {e}")
            return {"text": "Lo siento, tuve un problema al procesar tu pregunta.", "voice": None}


        except Exception as e:
            logger.error(f"Error al generar respuesta de Gemini: {e}")
            return "Lo siento, tuve un problema al procesar tu pregunta."

    def text_to_speech(self, text: str, lang: str = 'es') -> io.BytesIO:
        """Convierte texto a un archivo de audio en memoria."""
        if lang not in self.supported_languages:
            lang = 'es' # Usamos español por defecto
        
        try:
            # Creamos un objeto de audio en memoria
            audio_fp = io.BytesIO()
            tts = gtts.gTTS(text, lang=lang)
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0) # Rebobinamos el archivo para que pueda ser leído desde el principio
            return audio_fp
        except Exception as e:
            logger.error(f"Error al convertir texto a voz: {e}")
            return None
