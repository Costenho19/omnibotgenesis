import logging
import asyncio
import os
import psycopg2
from flask import Flask, render_template_string
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from web_dashboard import app as flask_app

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

# --- Definición de los Comandos del Bot ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    # Comando para activar cuenta premium
async def clave_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    clave_ingresada = ' '.join(context.args)
    user_id = update.effective_user.id
    if clave_ingresada == "omni2025premium":
        await update.message.reply_text("✅ ¡Clave correcta! Acceso premium activado.")
        await guardar_usuario_premium(user_id)
    else:
        await update.message.reply_text("❌ Clave incorrecta. Intenta nuevamente.")
    logger.info("Limpiando cualquier sesión antigua de Telegram...")
    await application.bot.delete_webhook()
    # Iniciar Flask en hilo paralelo
    threading.Thread(target=flask_app.run, kwargs={"host": "0.0.0.0", "port": 5000}).start()

    await application.run_polling()

    logger.info("Inicializando la aplicación...")
    await application.initialize()

    logger.info("✅ Bot listo, iniciando la escucha de peticiones...")
    
    
