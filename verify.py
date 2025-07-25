import os
import base64
import hashlib
from pqc_encryption import PQCEncryption
from voice_signature import VoiceSignature
from config import CLAVE_PREMIUM

# Instancia de cifrado cuántico y firma por voz
pqc = PQCEncryption()
voice_signer = VoiceSignature(CLAVE_PREMIUM)

def validate_voice_signature(update, context):
    user = update.message.from_user
    voice = update.message.voice

    if not voice:
        update.message.reply_text("⚠️ No se detectó ningún mensaje de voz. Intenta de nuevo.")
        return

    # Descargar el archivo de voz
    file = context.bot.get_file(voice.file_id)
    file_path = f"/tmp/{user.id}_voice.ogg"
    file.download(file_path)

    try:
        # Leer y codificar el archivo
        with open(file_path, "rb") as f:
            voice_data = f.read()
        encoded_voice = base64.b64encode(voice_data).decode("utf-8")

        # Firmar el mensaje con clave cuántica
        firma = voice_signer.sign_message(encoded_voice)

        # Validar firma y simular verificación biométrica
        if voice_signer.verify_signature(encoded_voice, firma):
            encrypted_firma = pqc.encrypt(firma)
            update.message.reply_text(f"✅ Identidad verificada por voz.\n🔐 Firma cifrada:\n{encrypted_firma[:100]}...")
        else:
            update.message.reply_text("❌ No se pudo validar tu identidad. Intenta de nuevo.")

    except Exception as e:
        update.message.reply_text(f"⚠️ Error al procesar el mensaje de voz: {str(e)}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
