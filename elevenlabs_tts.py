# elevenlabs_tts.py
import os
from elevenlabs import generate, play, save
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("ELEVENLABS_API_KEY")

def generar_audio(texto, idioma='es', nombre_archivo='voz_omni.mp3'):
    try:
        voice = "Antoni" if idioma == "es" else "Rachel" if idioma == "en" else "Adam"
        audio = generate(
            text=texto,
            voice=voice,
            model="eleven_multilingual_v2",
            api_key=api_key
        )
        save(audio, nombre_archivo)
        return nombre_archivo
    except Exception as e:
        print(f"Error generando voz ElevenLabs: {e}")
        return None
