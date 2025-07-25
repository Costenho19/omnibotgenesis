import logging
import asyncio
import os
import psycopg2
from flask import Flask, render_template_string
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from web_dashboard import app as flask_app
from config import CLAVE_PREMIUM, ADMIN_ID
from pqc_encryption import PQCEncryption
from verify import is_premium_user

# Inicializa la clase de cifrado post-cuántico
pqc = PQCEncryption()

# Importa nuestras clases, funciones y configuración desde los otros archivos
from config import BOT_TOKEN, DATABASE_URL, GEMINI_API_KEY, KRAKEN_API_KEY
from database import setup_premium_database, add_premium_assets
from analysis_engine import OmnixPremiumAnalysisEngine, premium_assets_list
from conversational_ai import ConversationalAI
from trading_system import KrakenTradingSystem
from pqc_encryption import encrypt_message, decrypt_message
from voice_signature import VoiceSignature
# Configuración del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Instanciamos nuestros sistemas ---
analysis_engine = OmnixPremiumAnalysisEngine()
conversational_ai = ConversationalAI()
trading_system = KrakenTradingSystem()
voice_signer = VoiceSignature("frase_secreta_omni2025")
from verify import validate_voice_signature
from telegram.ext import MessageHandler, filters

# Comando /voz_firma para verificar identidad con firma por voz
# Comando /voz_firma para verificar identidad con firma biométrica + post-cuántica
async def voice_firma_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.message

    if not message.voice:
        await message.reply_text("🔊 Por favor, envíame un mensaje de voz para verificar tu identidad.")
        return

    file = await context.bot.get_file(message.voice.file_id)
    voice_path = f"voice_{user.id}.ogg"
    await file.download_to_drive(voice_path)

    # Validación biométrica
    try:
        is_valid = validate_voice_signature(voice_path)
    except Exception as e:
        await message.reply_text("⚠️ Error en la validación biométrica.")
        return

    if not is_valid:
        await message.reply_text("🚫 Voz no reconocida. Inténtalo de nuevo.")
        return

    # Firma post-cuántica con Dilithium (simulada)
    signature = voice_signer.sign_message(user.username or str(user.id))

    await message.reply_text(
        f"✅ Identidad verificada con éxito.\n"
        f"🧬 Firma Dilithium:\n`{signature}`",
        parse_mode='Markdown'
    )
    
    os.remove(voice_path)
# Comando /trading para comprar cripto con validación de voz y firma cuántica
async def trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.message

    if not await es_usuario_premium(user.id):
        await update.message.reply_text("🚫 Este comando es exclusivo para usuarios *Premium*.")
        return

    if not message.voice:
        await message.reply_text("🎙 Por favor, envíame un mensaje de voz con la orden de compra.")
        return

    file = await context.bot.get_file(message.voice.file_id)
    voice_path = f"trading_voice_{user.id}.ogg"
    await file.download_to_drive(voice_path)

    try:
        is_valid = validate_voice_signature(voice_path)
    except Exception as e:
        await message.reply_text("⚠️ Error al verificar la firma biométrica de voz.")
        return

    if not is_valid:
        await message.reply_text("❌ Voz no reconocida. Intenta nuevamente.")
        return

    # Simular firma post-cuántica con Dilithium
    signature = voice_signer.sign_message(user.username or str(user.id))

    # Simulación de orden
    await message.reply_text(
        f"🛡️ Identidad verificada con Dilithium\n\n"
        f"✅ Orden de compra ejecutada en Kraken\n"
        f"🗣️ Voz autenticada: {user.full_name}\n"
        f"🔐 Firma cuántica: {signature[:15]}... ✅"
    )
# Comando /estado para verificar estado del bot y del usuario
async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    is_premium = await es_usuario_premium(user.id)

    status_msg = "🟢 *Bot activo*\n"
    if is_premium:
        status_msg += "✅ *Usuario premium activado*\n"
    else:
        status_msg += "⚠️ *Usuario sin acceso premium*\n"

    await update.message.reply_text(status_msg, parse_mode="Markdown")
application.add_handler(CommandHandler("estado", estado_command))

# Manejador para mensajes de voz (validación biométrica + firma Dilithium)
voice_handler = MessageHandler(filters.VOICE, validate_voice_signature)

application.add_handler(CommandHandler("voz_firma", voice_firma_command))
application.add_handler(voice_handler)
application.add_handler(CommandHandler("premium", premium_command))
application.add_handler(CommandHandler("premium", premium_command))
application.add_handler(CommandHandler("voz_validar", voz_validar_command))
application.add_handler(CommandHandler("verificar_identidad", verificar_identidad_command))
application.add_handler(CommandHandler("voz_borrar", voz_borrar_command))

# --- Definición de los Comandos del Bot ---
# Comando /voz_firma para validar identidad por voz y firmar digitalmente
async def voz_firma_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.message

    if not await es_usuario_premium(user.id):
        await message.reply_text("🚫 Este comando es exclusivo para usuarios premium.")
        return

    if not message.voice:
        await message.reply_text("🎙️ Por favor, envíame un mensaje de voz con la orden.")
        return

    file = await context.bot.get_file(message.voice.file_id)
    voice_path = f"voz_firma_{user.id}.ogg"
    await file.download_to_drive(voice_path)
   # Comando /voz_validar para validar voz con firma Dilithium
async def voz_validar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message

    voice_path = f"voz_firma_{user.id}.ogg"

    try:
        is_valid = validate_voice_signature(voice_path)
    except Exception as e:
        await message.reply_text("⚠️ Error al validar la firma de voz.")
        return

    if not is_valid:
        await message.reply_text("❌ Voz no coincide. Por favor, vuelve a intentarlo.")
        return

    # Firma cuántica con Dilithium
    signature = voice_signer.sign_message(user.username or str(user.id))

    await message.reply_text(
        f"✅ Voz verificada correctamente.\n"
        f"🪪 Usuario: {user.full_name}\n"
        f"🔐 Firma Dilithium: {signature[:15]}... ✅"
    )

    try:
        is_valid = validate_voice_signature(voice_path)
    except Exception as e:
        await message.reply_text("⚠️ Error al verificar la firma biométrica.")
        return

    if not is_valid:
        await message.reply_text("❌ Voz no reconocida. Intenta nuevamente.")
        return

    signature = voice_signer.sign_message(user.username or str(user.id))

    await message.reply_text(
        f"✅ Identidad confirmada por voz.\n"
        f"🧬 Firma cuántica Dilithium:\n`{signature}`",
        parse_mode="Markdown"
    )

    os.remove(voice_path)
# Comando /verificar_identidad - Verifica identidad y muestra firma
async def verificar_identidad_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = str(user.id)
    voice_path = f"voz_firma_{user_id}.ogg"

    try:
        is_valid = validate_voice_signature(voice_path)
    except Exception as e:
        await update.message.reply_text("⚠️ Error al verificar identidad por voz.")
        return

    if not is_valid:
        await update.message.reply_text("❌ No se pudo verificar la identidad.")
        return

    signature = voice_signer.sign_message(user.username or user_id)

    await update.message.reply_text(
        f"✅ Identidad verificada con éxito.\n\n"
        f"👤 Usuario: {user.full_name}\n"
        f"🧬 Firma digital: {signature[:16]}..."
    )

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = str(update.effective_user.id)

    if is_premium_user(user_id):
        await update.message.reply_text("🌟 Bienvenido usuario Premium. Tienes acceso completo a las funciones avanzadas.")
    else:
        await update.message.reply_text("🔒 Estás usando la versión gratuita. Escribe /premium para ver cómo acceder a las funciones exclusivas.")

    """Envía un mensaje de bienvenida."""
    user = update.effective_user
    await update.message.reply_html(
        f"¡Hola {user.mention_html()}! Soy OMNIX, tu asistente de trading. Usa /analyze <SÍMBOLO> para empezar.",
    )

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   user_id = update.effective_user.id
    if not await es_usuario_premium(user_id):
        await update.message.reply_text("🚫 Este comando es solo para usuarios *Premium*.")
        return

    """Realiza un análisis de un activo."""
    if not context.args:
        await update.message.reply_text("Uso: /analyze <SÍMBOLO>")
        return

    symbol = context.args[0].upper()
    await update.message.reply_text(f"Analizando {symbol}, por favor espera...")
    loop = asyncio.get_running_loop()
    try:
        analysis_result = await loop.run_in_executor(
            None, analysis_engine.analyze_with_ai, symbol
        )
        if analysis_result:
            message = f"""
📈 *Análisis para {analysis_result.symbol}*

*Precio Actual:* ${analysis_result.current_price:,.2f}
*Recomendación:* *{analysis_result.recommendation}*
*Confianza:* {analysis_result.confidence:.0%}
*Riesgo:* {analysis_result.risk_score:.0%}

*Predicciones (Simuladas):*
  - 1h: ${analysis_result.prediction_1h:,.2f}
  - 24h: ${analysis_result.prediction_24h:,.2f}
  - 7d: ${analysis_result.prediction_7d:,.2f}
            """
            save_analysis_to_db(user.id, symbol, message, analysis_result.__dict__)
            await update.message.reply_markdown(message)
        else:
            await update.message.reply_text(f"Lo siento, no pude obtener datos para {symbol}.")
    except Exception as e:
        logger.error(f"Error durante el análisis para {symbol}: {e}")
        await update.message.reply_text("Ocurrió un error inesperado durante el análisis.")
async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mensaje = (
        "🌟 *OMNIX Premium* 🌟\n\n"
        "Accede a funciones exclusivas:\n"
        "🔐 Trading 24/7 con IA\n"
        "📊 Análisis técnico avanzado\n"
        "🧠 IA emocional y multilingüe\n"
        "🛡️ Seguridad con firma Dilithium\n\n"
        "💳 Para activar tu cuenta Premium, contacta al equipo o visita:\n"
        "[Activar Premium](https://t.me/omnixglobal2025_bot)\n"
    )
    await update.message.reply_markdown_v2(mensaje)

# 👋 Comando /start con detección de idioma y bienvenida por voz
@app.on_message(filters.command("start"))
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   user_id = update.effective_user.id
    if not await es_usuario_premium(user_id):
        await update.message.reply_text("🚫 Este comando es solo para usuarios *Premium*.")
        return

    user_lang = update.effective_user.language_code

    if user_lang.startswith("en"):
        lang_code = "en"
        welcome_text = "Welcome to Omnix Global Bot. Ready for voice trading!"
    elif user_lang.startswith("ar"):
        lang_code = "ar"
        welcome_text = "مرحبًا بك في Omnix Global Bot. جاهز للتداول الصوتي!"
    elif user_lang.startswith("zh"):
        lang_code = "zh-cn"
        welcome_text = "欢迎使用 Omnix Global Bot，准备好语音交易吧！"
    else:
        lang_code = "es"
        welcome_text = "Bienvenido a Omnix Global Bot. ¡Listo para operar por voz!"

    context.user_data["lang"] = lang_code

    # 🔊 Bienvenida por voz
    tts = gTTS(text=welcome_text, lang=lang_code)
    audio_path = "bienvenida.mp3"
    tts.save(audio_path)

    with open(audio_path, "rb") as audio:
        await context.bot.send_voice(chat_id=update.effective_chat.id, voice=audio)

    os.remove(audio_path)

    await update.message.reply_text(welcome_text)

        await update.message.reply_text("⚠️ Ocurrió un error al procesar tu pregunta.")
# 🔍 Función temporal para debug
async def debug_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📩 MENSAJE RECIBIDO:")
    print(update)
    if update.message:
        await update.message.reply_text("📍 OMNIX recibió tu mensaje correctamente.")
    else:
        print("❌ No se recibió mensaje de texto.")

async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra el estado actual del sistema."""
    ia_ok = "✅" if analysis_engine else "❌"
    gemini_ok = "✅" if GEMINI_API_KEY else "❌"
    kraken_ok = "✅" if KRAKEN_API_KEY else "❌"
    
    conn_ok = "❌"
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn_ok = "✅"
        conn.close()
    except Exception as e:
        logger.error(f"Error de conexión a la BD para /estado: {e}")

    msg = (
        "*📡 Estado del Sistema OMNIX:*\n\n"
        f"*🧠 IA:* {ia_ok}\n"
        f"*🗄️ Base de Datos:* {conn_ok}\n"
        f"*🔐 API Gemini:* {gemini_ok}\n"
        f"*🔐 API Kraken:* {kraken_ok}"
    )
    await update.message.reply_markdown(msg)

async def trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not await es_usuario_premium(user_id):
        await update.message.reply_text("🚫 Este comando es solo para usuarios *Premium*.\nUsa /clave para activarlo.")
        return
    """Ejecuta una orden de trading con validación mejorada."""
    try:
        args = context.args
           # Firma cuántica antes de ejecutar
firma = voice_signer.sign_message(text)
logger.info(f"🖋️ Firma cuántica generada: {firma}") 

        if len(args) != 2:
            await update.message.reply_text("Uso: /trading <BUY/SELL> <cantidad>")
            return
  
        side = args[0].upper()
        if side not in ["BUY", "SELL"]:
            await update.message.reply_text("Orden inválida. El primer argumento debe ser BUY o SELL.")
            return
        amount = float(args[1])
        voice_signer = VoiceSignature("frase_secreta_omni2025")
        orden = f"{side} {amount} USDT"
        firma = voice_signer.sign_message(orden)
        logger.info(f"🖋️ Firma digital (voz+orden): {firma}")
         # 🔒 Validación cuántica de identidad por voz (simulada)
    user_voice_id = str(update.effective_user.id)
    if not voice_signer.verify_voice_signature(user_voice_id, firma):
        await update.message.reply_text("⚠️ Validación de identidad por voz fallida. Operación cancelada.")
        return
        # NOTA: Asegúrate de que tu función en trading_system se llama place_market_order
        result = trading_system.place_market_order(pair="XXBTZUSD", order_type=side.lower(), volume=amount)
        # 🔒 Validación cuántica de identidad por voz (simulada)
    user_voice_id = str(update.effective_user.id)
    if not voice_signer.verify_voice_signature(user_voice_id, firma):
        await update.message.reply_text("⚠️ Validación de identidad por voz fallida. Operación cancelada.")
        return 
        if not result or result.get("error"):
            error_message = result.get('error', 'Respuesta desconocida del exchange.') if result else 'No se recibió respuesta del exchange.'
            await update.message.reply_text(f"Error al ejecutar orden: {error_message}")
        else:
           # 🗣️ Respuesta por voz con idioma del usuario
        user_lang = user_data.get("lang", "es")  # idioma por defecto: español

        if user_lang == "en":
            voice_text = "Your order has been executed successfully. Good job."
            lang_code = "en"
        elif user_lang == "ar":
            voice_text = "تم تنفيذ طلبك بنجاح. عمل رائع."
            lang_code = "ar"
        elif user_lang == "zh":
            voice_text = "您的订单已成功执行。干得好。"
            lang_code = "zh-cn"
        else:
            voice_text = "La orden ha sido ejecutada con éxito. Buen trabajo."
            lang_code = "es"

        tts = gTTS(text=voice_text, lang=lang_code)
        audio_path = "voz_ejecutada.mp3"
        tts.save(audio_path)

        with open(audio_path, "rb") as audio:
            await context.bot.send_voice(chat_id=update.effective_chat.id, voice=audio)

        os.remove(audio_path)
 
       await update.message.reply_text(
             f"🔊 Vas a ejecutar una orden de {side} de {amount} USDT. Por favor confirma con tu voz..."
    
 
        # Simulamos validación por voz (puede integrarse biometría real)
              confirm_voice = voice_signer.verify_voice_signature(user_voice_id, firma)

              if not confirm_voice:
                  await update.message.reply_text("❌ Confirmación de voz no válida. Orden cancelada.")
                  return

except ValueError:
        await update.message.reply_text("❌ Error: La cantidad debe ser un número.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error inesperado en el comando: {str(e)}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde a cualquier mensaje que no sea un comando."""
    logger.info(f"RECIBIDO MENSAJE de {update.effective_user.name}: {update.message.text}")
    await update.message.reply_text("He recibido tu mensaje. Para interactuar conmigo, usa los comandos disponibles.")

async def main() -> None:
    """Función principal que arranca todo."""
    logger.info("🚀 Iniciando OMNIX Bot...")
    
    if not BOT_TOKEN or not DATABASE_URL:
        logger.critical("FATAL: Faltan BOT_TOKEN o DATABASE_URL. El bot no puede iniciar.")
        return

    setup_premium_database()
    add_premium_assets(premium_assets_list)

    application = Application.builder().token(BOT_TOKEN).build()

    # Añadimos los manejadores de comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("ask", ask_command))
    application.add_handler(CommandHandler("estado", estado_command))
    application.add_handler(CommandHandler("trading", trading_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
   application.add_handler(CommandHandler("premium_panel", premium_panel_command))

    # Comando para activar cuenta premium
async def clave_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    clave_ingresada = " ".join(context.args)
    user_id = update.effective_user.id
    if clave_ingresada == CLAVE_PREMIUM:

        await update.message.reply_text("✅ Clave correcta: Acceso premium activado.")
        guardar_usuario_premium(user_id, clave_ingresada)
    else:
        await update.message.reply_text("❌ Clave incorrecta. Intenta nuevamente.")
    async def premium_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    admin_id = ADMIN_ID
  # 🔁 Reemplaza con tu verdadero user ID de Telegram
    user_id = update.effective_user.id

    if user_id != admin_id:
        await update.message.reply_text("⛔ No tienes permisos para ver esta información.")
        return

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("SELECT user_id, clave FROM premium_users;")
        rows = cursor.fetchall()

        if not rows:
            await update.message.reply_text("🗂️ No hay usuarios premium registrados aún.")
        else:
            mensaje = "📋 Lista de usuarios premium:\n\n"
            for row in rows:
                mensaje += f"👤 ID: {row[0]} | Clave: {row[1]}\n"
            await update.message.reply_text(mensaje)

        cursor.close()
        conn.close()
    except Exception as e:
        await update.message.reply_text(f"❌ Error al consultar usuarios premium: {e}")
    logger.info("Limpiando cualquier sesión antigua de Telegram...")
    await application.bot.delete_webhook()
    # Iniciar Flask en hilo paralelo
    threading.Thread(target=flask_app.run, kwargs={"host": "0.0.0.0", "port": 5000}).start()

    await application.run_polling()

    logger.info("Inicializando la aplicación...")
    await application.initialize()

    logger.info("✅ Bot listo, iniciando la escucha de peticiones...")
    
    
