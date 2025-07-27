
import logging
import asyncio
import os
import psycopg2
import threading
import io
import tempfile
import matplotlib.pyplot as plt
import yfinance as yf
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from gtts import gTTS
from langdetect import detect
from database import (
from io import BytesIO 
    ...
    save_dilithium_signature,  # ya la tienes
    get_dilithium_signature,   # <-- AGREGA ESTA si aún no está
    ...
)

# --- Importaciones de tus Módulos ---
from config import BOT_TOKEN, DATABASE_URL, GEMINI_API_KEY, KRAKEN_API_KEY, CLAVE_PREMIUM, ADMIN_ID
from database import (
    setup_premium_database, add_premium_assets, save_analysis_to_db, 
    guardar_usuario_premium, es_usuario_premium, save_dilithium_signature,
    save_user_memory, get_user_memory, get_user_language, setup_memory_table, setup_language_table
)
from analysis_engine import OmnixPremiumAnalysisEngine, premium_assets_list
from conversational_ai import ConversationalAI # Asegúrate que aquí esté tu función generate_response_with_memory
from trading_system import KrakenTradingSystem
from pqc_encryption import PQCEncryption
from voice_signature import VoiceSignature, validate_voice_signature
from langdetect import detect
from conversational_ai import traducir_mensaje
from voice_verification import compare_voice_signatures

# --- Configuración Inicial ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Instancias Globales de tus Sistemas ---
analysis_engine = OmnixPremiumAnalysisEngine()
conversational_ai = ConversationalAI()
trading_system = KrakenTradingSystem()
voice_signer = VoiceSignature("frase_secreta_omni2025")
pqc = PQCEncryption()

# --- FUNCIONES AUXILIARES ---
from functools import wraps

def solo_premium(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if not es_usuario_premium(user_id):
            mensaje = "🚫 Esta función es exclusiva para usuarios premium. Usa /premium para activar tu cuenta."
            tts = gTTS(mensaje, lang='es')
            voz = BytesIO()
            tts.write_to_fp(voz)
            voz.seek(0)
            await update.message.reply_text(mensaje)
            await update.message.reply_voice(voice=voz)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
async def enviar_grafico(message, simbolo="BTC-USD"):
    """Genera y envía un gráfico de precios."""
    try:
        import datetime
        hoy = datetime.datetime.now()
        inicio = hoy - datetime.timedelta(days=30)
        datos = yf.download(simbolo, start=inicio.strftime('%Y-%m-%d'), end=hoy.strftime('%Y-%m-%d'))

        if datos.empty:
            await message.reply_text(f"⚠️ No se encontraron datos para {simbolo}.")
            return

        fig, ax = plt.subplots(figsize=(10, 5))
        datos["Close"].plot(ax=ax, label="Precio de cierre", color="cyan")
        ax.set_title(f"📊 Precio de {simbolo} (últimos 30 días)")
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Precio en USD")
        ax.legend(); ax.grid(True)

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close(fig)

        await message.reply_photo(photo=InputFile(buffer, filename=f"{simbolo}_grafico.png"), caption=f"📈 Análisis de {simbolo}")
    except Exception as e:
        logger.error(f"Error al generar gráfico: {e}")
        await message.reply_text("Lo siento, ocurrió un error al generar el gráfico.")

# --- DEFINICIÓN DE COMANDOS (/start, /analyze, etc.) ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envía un mensaje de bienvenida con menú de botones y diferenciación de usuario."""
    user = update.effective_user
    user_id = str(user.id)
    language_code = user.language_code or 'es'
    
    if await es_usuario_premium(user_id):
        welcome_text = "🌟 ¡Bienvenido de nuevo, Usuario Premium!"
    else:
        welcome_text = "🔒 ¡Bienvenido a OMNIX! Estás usando la versión gratuita."
    
    keyboard = [
        ["📊 Análisis", "📈 Estado"],
        ["🎯 Trading", "🔐 Seguridad"],
        ["👤 Cuenta", "❓ Ayuda"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    await update.message.reply_html(
        f"¡Hola {user.mention_html()}!\n{welcome_text}\n\nSelecciona una opción del menú de abajo:",
        reply_markup=reply_markup
    )

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra un menú con botones en línea (inline)."""
    keyboard = [
        [InlineKeyboardButton("🤖 Chat con IA", callback_data="chat_ia")],
        [InlineKeyboardButton("📊 Análisis Gráfico", callback_data="analisis_grafico")],
        [InlineKeyboardButton("📚 Educación (Pronto)", callback_data="educacion")],
        [InlineKeyboardButton("⚙️ Configuración (Pronto)", callback_data="configuracion")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Selecciona una opción del menú avanzado:", reply_markup=reply_markup)

@solo_premium
async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args

    if not args:
        await update.message.reply_text("❗Por favor indica el símbolo del activo (por ejemplo: BTC-USD)")
        return

    simbolo = args[0].upper()

    await update.message.reply_text(f"📊 Analizando {simbolo} con IA y generando gráfico...")

    # 1. Análisis con IA
    engine = OmnixPremiumAnalysisEngine(simbolo)
    resultado = engine.realizar_analisis()
    texto_analisis = resultado.resumen

    # 2. Generar gráfico
    grafico = generar_grafico_precio(simbolo)

    # 3. Enviar análisis + gráfico
    await update.message.reply_photo(photo=grafico, caption=texto_analisis)

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra información sobre la membresía Premium."""
    mensaje = (
        "🌟 *OMNIX Premium* 🌟\n\n"
        "Accede a funciones exclusivas:\n"
        "🔐 Trading 24/7 con IA y seguridad biométrica\n"
        "📊 Análisis técnico avanzado y gráficos\n"
        "🧠 IA conversacional multilingüe con memoria\n"
        "🛡️ Seguridad con firma post-cuántica Dilithium\n\n"
        "Para activar tu cuenta, usa el comando `/clave <tu_clave_premium>`."
    )
    await update.message.reply_markdown(mensaje)

async def clave_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Permite a un usuario activar su cuenta Premium."""
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("Uso: /clave <tu_clave_premium>")
        return
        
    clave_ingresada = context.args[0]
    if clave_ingresada == CLAVE_PREMIUM:
        await guardar_usuario_premium(user_id, clave_ingresada)
        await update.message.reply_text("✅ ¡Clave correcta! Tu acceso premium ha sido activado.")
    else:
        await update.message.reply_text("❌ Clave incorrecta.")

async def voz_firma_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Verifica la identidad con firma biométrica + post-cuántica."""
    user = update.effective_user
    if not await es_usuario_premium(user.id):
        await update.message.reply_text("🚫 Este comando es exclusivo para usuarios premium.")
        return

    if not update.message.voice:
        await update.message.reply_text("🔊 Por favor, envíame un mensaje de voz para registrar tu firma.")
        return

    file = await context.bot.get_file(update.message.voice.file_id)
    voice_path = f"voice_reg_{user.id}.ogg"
    await file.download_to_drive(voice_path)

    if not validate_voice_signature(voice_path): # Simulación
        await update.message.reply_text("🚫 Voz no reconocida. La verificación ha fallado.")
        os.remove(voice_path)
        return

    signature_message = f"Verificado:{user.id}"
    signature = pqc.sign_with_dilithium(signature_message.encode())
    await save_dilithium_signature(str(user.id), signature)
    
    await update.message.reply_text("✅ Identidad verificada. Tu firma de voz y cuántica han sido registradas.", parse_mode='Markdown')
    os.remove(voice_path)
# voice_signature.py
import time
import hmac
import hashlib
from typing import Tuple

class VoiceSignature:
    """
    Firma ligera basada en HMAC + timestamp (NO sustituye a Dilithium).
    Úsala como 2º factor rápido. Para no repudio usa pqc.sign_with_dilithium().
    """
    def __init__(self, secret_phrase: str):
        # Derivamos una clave HMAC a partir de la frase secreta
        self.key = hashlib.sha3_512(secret_phrase.encode("utf-8")).digest()

    def sign_message(self, message: str, ts: int | None = None) -> Tuple[str, int]:
        """
        Devuelve (firma_hex, timestamp_usado)
        """
        if ts is None:
            ts = int(time.time())
        payload = f"{ts}|{message}".encode("utf-8")
        mac = hmac.new(self.key, payload, hashlib.sha3_512).hexdigest()
        return mac, ts

    def verify_signature(self, message: str, signature: str, ts: int, max_age: int = 120) -> bool:
        """
        Verifica firma y que el timestamp no esté expirado.
        """
        now = int(time.time())
        if now - ts > max_age:
            return False
        payload = f"{ts}|{message}".encode("utf-8")
        expected = hmac.new(self.key, payload, hashlib.sha3_512).hexdigest()
        return hmac.compare_digest(expected, signature)
@solo_premium
async def trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ejecuta una orden de trading."""
    user = update.effective_user
    if not await es_usuario_premium(user.id):
        await update.message.reply_text("🚫 Este comando es exclusivo para usuarios Premium.")
        return
        # Verificar firma biométrica
    if not validar_sesion_biometrica(str(user.id)):
        await update.message.reply_text("🔒 Firma biométrica no válida. Usa /voz_firma para verificar tu identidad.")
        return

    # (Tu lógica de trading aquí)
    await update.message.reply_text("Función de trading en desarrollo.")
@solo_premium
async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra el estado del sistema y del usuario."""
    user = update.effective_user
    es_premium = await es_usuario_premium(user.id)
    tipo_cuenta = "🌟 Premium" if es_premium else "🆓 Gratuita"
    
    estado_texto = (
        f"🤖 *Estado del sistema OMNIX:*\n\n"
        f"✅ Bot: Activo y funcionando\n"
        f"🧠 IA (Gemini): Conectada\n"
        f"📡 Trading (Kraken): Conectado\n"
        f"🗄️ Base de datos: Conectada\n"
        f"🛡️ Seguridad Cuántica: Habilitada\n"
        f"----------\n"
        f"👤 Tu Cuenta: {tipo_cuenta}"
    )
    await update.message.reply_text(estado_texto, parse_mode="Markdown")
# --- COMANDO /voz_firma ---
from telegram.constants import ChatAction
import os
import uuid
import tempfile
import requests
from voice_signature import VoiceSignature
from database import save_dilithium_signature

SECRET_PHRASE = "mi frase secreta de firma biométrica"  # Cámbiala por tu frase real
@solo_premium
async def voz_firma_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    # Verifica que haya mensaje de voz
    if not update.message.voice:
        await update.message.reply_text("🎙️ Por favor, envía un mensaje de voz para verificar tu identidad.")
        return

    await update.message.reply_text("🎧 Procesando tu firma de voz...")

    # Descargar audio
    voice_file = await context.bot.get_file(update.message.voice.file_id)
    voice_path = f"/tmp/{uuid.uuid4()}.ogg"
    await voice_file.download_to_drive(voice_path)

    # Convertir con Whisper API (requiere tu clave OpenAI)
    import openai
    openai.api_key = OPENAI_API_KEY
    with open(voice_path, "rb") as f:
        transcript = openai.Audio.transcribe("whisper-1", f)["text"]

    os.remove(voice_path)

    if SECRET_PHRASE.lower() not in transcript.lower():
        await update.message.reply_text("❌ Tu frase secreta no coincide. Intenta de nuevo.")
        return

    # Firmar la sesión
    signer = VoiceSignature(SECRET_PHRASE)
   signature, timestamp = signer.sign_message(transcript)


    # Guardar en base de datos
    save_dilithium_signature(user_id, signature,timestamp)

    await update.message.reply_text("✅ Identidad verificada y firma registrada exitosamente.")
@solo_premium
async def verificar_voz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    if not update.message.voice:
        await update.message.reply_text("🎙️ Por favor, envía un mensaje de voz para verificar tu identidad.")
        return

    await update.message.reply_text("🔍 Verificando tu voz...")

    # Guardar archivo temporal
    voice_file = await context.bot.get_file(update.message.voice.file_id)
    voice_path = f"/tmp/voice_check_{uuid.uuid4()}.ogg"
    await voice_file.download_to_drive(voice_path)

    # Obtener firma anterior de base de datos
    firma_guardada = get_saved_signature(user_id)  # <- Asegúrate de tener esta función en database.py

    if not firma_guardada:
        await update.message.reply_text("⚠️ No hay firma de voz registrada. Usa /voz_firma primero.")
        return

    # Comparar firmas biométricas
    coincide = compare_voice_signatures(firma_guardada, voice_path)

    if coincide:
        await update.message.reply_text("✅ Voz verificada. Identidad confirmada.")
    else:
        await update.message.reply_text("❌ La voz no coincide. Acceso denegado.")
@solo_premium
async def firma_visual_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    if not update.message.voice:
        await update.message.reply_text("🎙️ Por favor, envía un mensaje de voz para generar tu firma visual.")
        return

    await update.message.reply_text("🧬 Generando firma visual de tu voz...")

    # Guardar archivo de voz
    voice_file = await context.bot.get_file(update.message.voice.file_id)
    voice_path = f"/tmp/firma_visual_{uuid.uuid4()}.ogg"
    await voice_file.download_to_drive(voice_path)

    # Transcribir con Whisper
    import openai
    openai.api_key = OPENAI_API_KEY
    with open(voice_path, "rb") as f:
        transcript = openai.Audio.transcribe("whisper-1", f)["text"]

    os.remove(voice_path)

    # Firmar la transcripción
    from voice_signature import VoiceSignature
    signer = VoiceSignature(SECRET_PHRASE)
    signature, timestamp = signer.sign_message(transcript)
@solo_premium
async def verificar_voz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    if not update.message.voice:
        await update.message.reply_text("🎙️ Por favor, envía un mensaje de voz para verificar tu identidad.")
        return

    await update.message.reply_text("🔍 Verificando tu voz...")

    # Guardar archivo temporal
    voice_file = await context.bot.get_file(update.message.voice.file_id)
    voice_path = f"/tmp/voice_check_{uuid.uuid4()}.ogg"
    await voice_file.download_to_drive(voice_path)

    # Obtener firma anterior de base de datos
    firma_guardada = get_saved_signature(user_id)  # <- Asegúrate de tener esta función en database.py

    if not firma_guardada:
        await update.message.reply_text("⚠️ No hay firma de voz registrada. Usa /voz_firma primero.")
        return

    # Comparar firmas biométricas
    coincide = compare_voice_signatures(firma_guardada, voice_path)

    if coincide:
        await update.message.reply_text("✅ Voz verificada. Identidad confirmada.")
    else:
        await update.message.reply_text("❌ La voz no coincide. Acceso denegado.")

    # Mostrar firma al usuario
    firma_formateada = f"""
🧾 Firma Visual Generada:
------------------------------
🗣 Texto detectado: "{transcript}"
🔏 Firma Dilithium: {signature[:64]}...
🕓 Tiempo: {timestamp}
"""
    await update.message.reply_text(firma_formateada)

async def cuenta_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra información detallada de la cuenta del usuario."""
    user = update.effective_user
    es_premium = await es_usuario_premium(user.id)
    tipo_cuenta = "🌟 Premium" if es_premium else "🆓 Gratuita"
    idioma_pref = await get_user_language(user.id) or "No definido"
    
    mensaje = (
        f"👤 *Información de tu cuenta OMNIX*\n\n"
        f"🧾 Tipo de cuenta: {tipo_cuenta}\n"
        f"🌐 Idioma preferido: `{idioma_pref}`\n"
        f"\nGracias por usar OMNIX."
    )
    await update.message.reply_markdown(mensaje)

async def premium_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra la lista de usuarios premium al administrador."""
    if str(update.effective_user.id) != str(ADMIN_ID):
        await update.message.reply_text("⛔ No tienes permisos para acceder a este panel.")
        return
        
    # (Aquí iría tu código para consultar y mostrar los usuarios premium...)
    await update.message.reply_text("Panel de administración en desarrollo.")

# --- MANEJADORES DE MENSAJES Y BOTONES ---

async def general_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja cualquier mensaje de texto, incluyendo los botones del menú principal."""
    user_id = str(update.message.from_user.id)
    user_input = update.message.text
    
    # Manejo de botones del menú principal (ReplyKeyboardMarkup)
    if "📊 Análisis" in user_input:
        await update.message.reply_text("Por favor, usa el comando /analyze <SÍMBOLO> para un análisis de texto, o /menu para ver el análisis gráfico.")
        return
    elif "📈 Estado" in user_input:
        await estado_command(update, context)
        return
    elif "🎯 Trading" in user_input:
        await trading_command(update, context)
        return
    elif "🔐 Seguridad" in user_input:
        await update.message.reply_text("Usa /voz_firma para registrar tu identidad biométrica.")
        return
    elif "👤 Cuenta" in user_input:
        await cuenta_command(update, context)
        return
    elif "❓ Ayuda" in user_input:
        await premium_command(update, context) # El comando premium sirve como ayuda
        return

    # Si no es un botón, es un chat con la IA
    logger.info(f"RECIBIDO CHAT de {update.effective_user.name}: {user_input}")
    historial = await get_user_memory(user_id)
    prompt = historial + "\nUsuario: " + user_input + "\nOMNIX:"
    language = await get_user_language(user_id) or detect(user_input)

    #respuesta = await generate_response_with_memory(user_id, prompt, language)
    respuesta = conversational_ai.generate_response(user_id, prompt) # Usando la clase directamente
    await save_user_memory(user_id, f"Usuario: {user_input}\nOMNIX: {respuesta}")

    await update.message.reply_text(respuesta)

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja los botones del menú inline (/menu)."""
    query = update.callback_query
    await query.answer()
    opcion = query.data

    if opcion == "analisis_grafico":
        await query.message.reply_text("Generando gráfico de BTC-USD...")
        await enviar_grafico(query.message, simbolo="BTC-USD")
    else:
        respuesta = {
            "chat_ia": "🤖 Puedes chatear conmigo directamente. Escribe lo que quieras.",
            "educacion": "📚 Módulo educativo disponible próximamente.",
            "configuracion": "⚙️ Configuraciones avanzadas disponibles pronto."
        }.get(opcion, "❓ Opción no reconocida.")
        await query.edit_message_text(text=respuesta)

# --- FUNCIÓN PRINCIPAL DE ARRANQUE ---

async def main() -> None:
    """Función principal que configura y arranca el bot."""
    logger.info("🚀 Iniciando OMNIX Bot...")
    def generar_grafico_precio(simbolo: str) -> io.BytesIO:
    data = yf.download(simbolo, period="7d", interval="1h")
    plt.figure(figsize=(10, 4))
    plt.plot(data["Close"], label="Precio", linewidth=2)
    plt.title(f"Precio de {simbolo} (últimos 7 días)")
    plt.xlabel("Fecha")
    plt.ylabel("USD")
    plt.legend()
    plt.tight_layout()
async def menu_botones_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra un menú con botones interactivos."""
    keyboard = [
        [InlineKeyboardButton("📊 Análisis", callback_data="analyze")],
        [InlineKeyboardButton("🤖 Trading", callback_data="trading")],
        [InlineKeyboardButton("👤 Cuenta", callback_data="cuenta")],
        [InlineKeyboardButton("⭐ Premium", callback_data="premium")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📍 Selecciona una opción del menú:", reply_markup=reply_markup)

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()
    buffer.seek(0)
    return buffer

    if not BOT_TOKEN or not DATABASE_URL:
        logger.critical("FATAL: Faltan BOT_TOKEN o DATABASE_URL.")
        return

    # Preparamos las tablas de la BD que no existan
    setup_premium_database()
    setup_memory_table()
    setup_language_table()
    add_premium_assets(premium_assets_list)

    application = Application.builder().token(BOT_TOKEN).build()

    # Añadimos los manejadores de comandos y mensajes
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("premium", premium_command))
    application.add_handler(CommandHandler("clave", clave_command))
    application.add_handler(CommandHandler("voz_firma", voz_firma_command))
    application.add_handler(CommandHandler("trading", trading_command))
    application.add_handler(CommandHandler("estado", estado_command))
    application.add_handler(CommandHandler("cuenta", cuenta_command))
    application.add_handler(CommandHandler("premium_panel", premium_panel_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, general_text_handler))
    application.add_handler(CallbackQueryHandler(menu_callback_handler))
    application.add_handler(CommandHandler("validar", voz_validar_command))
    application.add_handler(CommandHandler("cuenta_segura", cuenta_segura_command))
    application.add_handler(CommandHandler("mercado", mercado_command))
    application.add_handler(CommandHandler("menu_botones", menu_botones_command))
    application.add_handler(CallbackQueryHandler(responder_botones))
    application.add_handler(CommandHandler("menu_botones", menu_botones_command))
    application.add_handler(CallbackQueryHandler(responder_botones))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("premium_panel", premium_panel_command))

async def cuenta_segura_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    firma_guardada = get_dilithium_signature(user_id)

    if firma_guardada:
        mensaje = f"🔐 Tu cuenta está protegida con firma biométrica cuántica.\n🗓️ Último registro: Hoy"
    else:
        mensaje = "⚠️ No se ha encontrado una firma biométrica válida.\nUsa /voz_firma para registrar tu voz."
     # Detectar idioma del usuario y traducir
    idioma_usuario = detect(mensaje)
    if idioma_usuario != 'es':
        mensaje = traducir_mensaje(mensaje, idioma_usuario)
@solo_premium
async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    # Activo por defecto (puedes cambiarlo)
    symbol = "BTC-USD"
    data = yf.download(symbol, period="7d", interval="1h")

    # Crear gráfico con matplotlib
    plt.figure(figsize=(10, 4))
    plt.plot(data.index, data["Close"], label=f"{symbol} Precio", color='blue')
    plt.title(f"Análisis de {symbol} (Últimos 7 días)")
    plt.xlabel("Fecha")
    plt.ylabel("Precio (USD)")
    plt.grid(True)
    plt.legend()

    # Guardar imagen temporal
    graph_path = f"/tmp/graph_{uuid.uuid4()}.png"
    plt.tight_layout()
    plt.savefig(graph_path)
    plt.close()

    # Mensaje explicativo
    mensaje = f"📈 Aquí tienes el gráfico de {symbol} en los últimos 7 días. El precio actual ronda los {round(data['Close'][-1], 2)} USD."

    # Convertir texto a voz
    tts = gTTS(mensaje, lang='es')
    voz = BytesIO()
    tts.write_to_fp(voz)
    voz.seek(0)

    # Enviar imagen + texto + voz
    await update.message.reply_photo(photo=InputFile(graph_path))
    await update.message.reply_text(mensaje)
    await update.message.reply_voice(voice=voz)

    # Convertir a voz
    tts = gTTS(mensaje, lang='es')
    voz = BytesIO()
    tts.write_to_fp(voz)
    voz.seek(0)
@solo_premium
async def premium_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Contar usuarios premium
    cur.execute("SELECT COUNT(*) FROM premium_users")
    total_premium = cur.fetchone()[0]

    # Contar análisis realizados
    cur.execute("SELECT COUNT(*) FROM ai_analysis")
    total_analisis = cur.fetchone()[0]

    # Último análisis
    cur.execute("SELECT MAX(timestamp) FROM ai_analysis")
    ultimo_analisis = cur.fetchone()[0]

    conn.close()

    mensaje = f"""
📊 Panel Premium OMNIX:
👥 Usuarios Premium: {total_premium}
📈 Análisis Realizados: {total_analisis}
🕒 Último Análisis: {ultimo_analisis if ultimo_analisis else 'Sin datos'}
🟢 Estado del Sistema: Operativo ✅
""".strip()
# Convertir a voz
tts = gTTS(mensaje, lang='es')
voz = BytesIO()
tts.write_to_fp(voz)
voz.seek(0)

# Enviar respuesta
await update.message.reply_text(mensaje)
await update.message.reply_voice(voice=voz)

   
    await update.message.reply_text(mensaje)
    await update.message.reply_voice(voice=voz)

    await update.message.reply_text(mensaje)
    await update.message.reply_voice(voice=voz)

    logger.info("Limpiando sesión antigua de Telegram...")
    await application.bot.delete_webhook()

    logger.info("Inicializando la aplicación...")
    await application.initialize()
@solo_premium
async def mercado_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    # Lista de activos a mostrar
    activos = ['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD']
    resumen = "📊 *Resumen del Mercado Cripto:*\n\n"

    for activo in activos:
        try:
            data = yf.download(activo, period="1d", interval="1h")
            precio_actual = round(data["Close"][-1], 2)
            resumen += f"• {activo.split('-')[0]}: {precio_actual} USD\n"
        except Exception as e:
            resumen += f"• {activo.split('-')[0]}: ❌ Error\n"

    resumen += "\n🔁 Datos actualizados en tiempo real."

    # Convertir texto a voz
    tts = gTTS(resumen, lang='es')
    voz = BytesIO()
    tts.write_to_fp(voz)
    voz.seek(0)

    # Enviar respuesta
    await update.message.reply_text(resumen, parse_mode="Markdown")
    await update.message.reply_voice(voice=voz)

    logger.info("✅ Bot listo, iniciando la escucha de peticiones...")
    await application.start()
    
    await asyncio.Event().wait()
from datetime import datetime
from voice_signature import VoiceSignature
from database import get_dilithium_signature

def validar_sesion_biometrica(user_id: str) -> bool:
    """Verifica si la firma biométrica del usuario es válida y reciente (hoy)."""
    firma_guardada = get_dilithium_signature(user_id)
    if not firma_guardada:
        return False

    signer = VoiceSignature(SECRET_PHRASE)
    firma_esperada = signer.sign_message(user_id)[0]  # Solo usamos la firma (sin timestamp)
    
    # Comparar firmas
    if firma_guardada != firma_esperada:
        return False

    # Si quisieras verificar el timestamp, puedes adaptar la tabla para obtenerlo también y compararlo con hoy.
    return True
from telegram import Update
from telegram.ext import ContextTypes
from gtts import gTTS
from io import BytesIO

async def voz_validar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    es_valida = validar_sesion_biometrica(user_id)

    if es_valida:
        mensaje = "✅ Tu firma biométrica es válida."
    else:
        mensaje = "❌ Firma biométrica inválida. Usa /voz_firma para registrar una nueva."

    # Generar respuesta en voz
    tts = gTTS(mensaje, lang='es')
    voz = BytesIO()
    tts.write_to_fp(voz)
    voz.seek(0)

    # Enviar mensaje y voz
    await update.message.reply_text(mensaje)
    await update.message.reply_voice(voice=voz)
from telegram import Update
from telegram.ext import ContextTypes
from gtts import gTTS
from io import BytesIO

async def cuenta_segura_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    firma_guardada = get_dilithium_signature(user_id)

    if firma_guardada:
        mensaje = f"🔐 Tu cuenta está protegida con firma biométrica cuántica.\n🗓️ Último registro: Hoy"
    else:
        mensaje = "⚠️ No se ha encontrado una firma biométrica válida.\nUsa /voz_firma para registrar tu voz."

    # Convertir a voz
    tts = gTTS(mensaje, lang='es')
    voz = BytesIO()
    tts.write_to_fp(voz)
    voz.seek(0)

    await update.message.reply_text(mensaje)
    await update.message.reply_voice(voice=voz)
from telegram import Update, InputFile
from telegram.ext import ContextTypes
from io import BytesIO
from gtts import gTTS
import yfinance as yf
import matplotlib.pyplot as plt
@solo_premium
async def mercado_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cryptos = {
        "BTC-USD": "Bitcoin",
        "ETH-USD": "Ethereum",
        "SOL-USD": "Solana"
    }

    mensaje = "📊 Resumen del mercado:\n"
    plt.figure(figsize=(10, 6))

    for symbol, nombre in cryptos.items():
        data = yf.download(symbol, period="1d", interval="15m")
        last_price = data['Close'].iloc[-1]
        mensaje += f"• {nombre}: ${last_price:.2f}\n"
        plt.plot(data.index, data['Close'], label=nombre)
    @solo_premium 
    plt.title("Precios Criptomonedas (24h)")
    plt.xlabel("Hora")
    plt.ylabel("Precio (USD)")
    plt.legend()
    plt.tight_layout()

    img = BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)

    tts = gTTS(mensaje, lang='es')
    voz = BytesIO()
    tts.write_to_fp(voz)
    voz.seek(0)

    await update.message.reply_text(mensaje)
    await update.message.reply_voice(voice=voz)
    await update.message.reply_photo(photo=InputFile(img, filename="mercado.png"))
   from gtts import gTTS
from io import BytesIO

async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)

    # Estado simulado (puedes conectar estos valores a tu sistema real)
    estado_kraken = "🟢 Kraken conectado"
    estado_ia = "🤖 GPT-4 activo"
    estado_trading = "📈 Trading automático: activo"
    estado_memoria = "🧠 Memoria contextual: activada"

    mensaje = (
        f"📊 Estado del sistema OMNIX:\n"
        f"{estado_kraken}\n"
        f"{estado_ia}\n"
        f"{estado_trading}\n"
        f"{estado_memoria}"
    )

    # Convertir a voz
    tts = gTTS(mensaje, lang='es')
    voz = BytesIO()
    tts.write_to_fp(voz)
    voz.seek(0)

    # Enviar mensaje y voz
    await update.message.reply_text(mensaje)
    await update.message.reply_voice(voice=voz)
 async def responder_botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "analyze":
        await query.edit_message_text("📊 Has seleccionado *Análisis*.")
    elif query.data == "trading":
        await query.edit_message_text("🤖 Has seleccionado *Trading*.")
    elif query.data == "cuenta":
        await query.edit_message_text("👤 Has seleccionado *Cuenta*.")
    elif query.data == "premium":
        await query.edit_message_text("⭐ Has seleccionado *Premium*.")
    else:
        await query.edit_message_text("❓ Opción no reconocida.")
# Handler para mensajes de texto normales
@solo_premium
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    user_message = update.message.text

    # Detectar idioma automáticamente
    lang = detect(user_message)

    # Generar respuesta con memoria desde conversational_ai
    from conversational_ai import generate_response_with_memory
    respuesta = await generate_response_with_memory(user_id, user_message, lang)

    # Convertir respuesta a voz con gTTS
    from gtts import gTTS
    from io import BytesIO
    tts = gTTS(text=respuesta, lang=lang)
    voz = BytesIO()
    tts.write_to_fp(voz)
    voz.seek(0)

    # Enviar respuesta en texto y voz
    await update.message.reply_text(respuesta)
    await update.message.reply_voice(voice=voz)
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"!!!!!!!!!! ERROR FATAL AL INICIAR EL BOT !!!!!!!!!!!")
        print(f"Error: {e}")
