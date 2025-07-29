# voice_engine.py
# ==========================================
# Módulo de generación de voz para OMNIX
# Usa gTTS para generar archivos de audio MP3
# Compatible con múltiples idiomas
# ==========================================

from gtts import gTTS
import uuid
import os
import logging

logger = logging.getLogger(__name__)

def generar_audio(text: str, lang: str = 'es') -> str:
    """
    Genera un archivo de audio MP3 desde texto usando gTTS.
    
    Parámetros:
        text (str): Texto a convertir en voz.
        lang (str): Idioma de la voz (es, en, ar, zh-cn...).

    Retorna:
        str: Nombre del archivo de audio generado.
    """
    try:
        # Crea archivo de voz con nombre único
        tts = gTTS(text=text, lang=lang)
        file_name = f"voz_{uuid.uuid4()}.mp3"
        tts.save(file_name)
        logger.info(f"✅ Voz generada correctamente: {file_name}")
        return file_name
    except Exception as e:
        logger.error(f"❌ Error generando voz: {e}")
        return None
