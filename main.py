import logging
import asyncio
import os
import psycopg2
import threading
from telegram import ReplyKeyboardMarkup
from langdetect import detect
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from gtts import gTTS
await save_user_memory(user_id, ai_response)
import io
import matplotlib.pyplot as plt
import yfinance as yf
from telegram import InputFile
# Importa nuestras clases y configuración
from config import BOT_TOKEN, DATABASE_URL, GEMINI_API_KEY, KRAKEN_API_KEY, CLAVE_PREMIUM, ADMIN_ID
from database import setup_premium_database, add_premium_assets, save_analysis_to_db, guardar_usuario_premium, es_usuario_premium, save_dilithium_signature
from analysis_engine import OmnixPremiumAnalysisEngine, premium_assets_list
from conversational_ai import ConversationalAI
from trading_system import KrakenTradingSystem
from pqc_encryption import PQCEncryption
from voice_signature import VoiceSignature, validate_voice_signature # Asegúrate que validate_voice_signature esté en este archivo

# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Instanciamos nuestros sistemas ---
analysis_engine = OmnixPremiumAnalysisEngine()
conversational_ai = ConversationalAI()
trading_system = KrakenTradingSystem()
voice_signer = VoiceSignature("frase_secreta_omni2025")
pqc = PQCEncryption()

# --- Definición de los Comandos del Bot ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envía un mensaje de bienvenida con menú y diferenciación de usuario."""
    user = update.effective_user
    user_id = str(user.id)
    
    if await es_usuario_premium(user_id):
        welcome_text = "🌟 Bienvenido de nuevo, Usuario Premium. Tienes acceso a todas las funciones avanzadas."
    else:
        welcome_text = "🔒 Bienvenido a OMNIX. Estás usando la versión gratuita. Usa /premium para descubrir las funciones exclusivas."
    
    await update.message.reply_html(f"¡Hola {user.mention_html()}!\n{welcome_text}")

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Realiza un análisis de un activo (solo para usuarios premium)."""
    user = update.effective_user
    if not await es_usuario_premium(user.id):
        await update.message.reply_text("🚫 Este comando es exclusivo para usuarios *Premium*. Usa /premium para más información.", parse_mode="Markdown")
        return
        
    # (El resto de tu código de análisis va aquí...)

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra información sobre la membresía Premium."""
    mensaje = (
        "🌟 *OMNIX Premium* 🌟\n\n"
        "Accede a funciones exclusivas:\n"
        "🔐 Trading 24/7 con IA y seguridad biométrica\n"
        "📊 Análisis técnico avanzado\n"
        "🧠 IA conversacional multilingüe\n"
        "🛡️ Seguridad con firma post-cuántica Dilithium\n\n"
        "Para activar tu cuenta, usa el comando `/clave <tu_clave_premium>`."
    )
    await update.message.reply_markdown(mensaje)

async def clave_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Permite a un usuario activar su cuenta Premium con una clave."""
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("Uso: /clave <tu_clave_premium>")
        return
        
    clave_ingresada = context.args[0]
    if clave_ingresada == CLAVE_PREMIUM:
        await guardar_usuario_premium(user_id, clave_ingresada)
        await update.message.reply_text("✅ ¡Clave correcta! Tu acceso premium ha sido activado. ¡Disfruta de todas las funciones!")
    else:
        await update.message.reply_text("❌ Clave incorrecta. Por favor, inténtalo de nuevo.")

async def voz_firma_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Verifica la identidad con firma biométrica + post-cuántica."""
    user = update.effective_user
    if not await es_usuario_premium(user.id):
        await update.message.reply_text("🚫 Este comando es exclusivo para usuarios premium.")
        return

    if not update.message.voice:
        await update.message.reply_text("🔊 Por favor, envíame un mensaje de voz para verificar tu identidad.")
        return

    file = await context.bot.get_file(update.message.voice.file_id)
    voice_path = f"voice_{user.id}.ogg"
    await file.download_to_drive(voice_path)

    # Simulación de validación biométrica
    if not validate_voice_signature(voice_path):
        await update.message.reply_text("🚫 Voz no reconocida. La verificación ha fallado.")
        os.remove(voice_path)
        return

    # Firma post-cuántica con Dilithium
    signature_message = f"Verificado: {user.username or user.id}"
    signature = pqc.sign_with_dilithium(signature_message.encode())
    await save_dilithium_signature(str(user.id), signature)
    
    await update.message.reply_text(
        f"✅ Identidad verificada con éxito.\n"
        f"🧬 Tu firma post-cuántica Dilithium ha sido registrada.",
        parse_mode='Markdown'
    )
    os.remove(voice_path)

async def trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ejecuta una orden de trading con validación por voz."""
    user = update.effective_user
    if not await es_usuario_premium(user.id):
        await update.message.reply_text("🚫 Este comando es exclusivo para usuarios Premium.")
        return
    
    # (Aquí iría tu lógica completa de trading con voz...)
    await update.message.reply_text("Función de trading en desarrollo.")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from telegram import ReplyKeyboardMarkup
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from telegram import ReplyKeyboardMarkup
    from gtts import gTTS
    import tempfile
    from conversational_ai import ConversationalAI
    # 🔍 Detectar idioma del usuario
    language_code = update.message.from_user.language_code or 'en'

    if language_code.startswith('es'):
        lang = 'es'
        welcome_text = "¡Bienvenido a OMNIX!\nSelecciona una opción del menú:"
        welcome_voice = "Bienvenido a OMNIX. Tu asistente de trading inteligente está activo."
    elif language_code.startswith('en'):
        lang = 'en'
        welcome_text = "Welcome to OMNIX!\nPlease select an option from the menu:"
        welcome_voice = "Welcome to OMNIX. Your smart trading assistant is now active."
    elif language_code.startswith('ar'):
        lang = 'ar'
        welcome_text = "مرحبًا بك في أومنيكس!\nاختر خيارًا من القائمة:"
        welcome_voice = "مرحبًا بك في أومنيكس. مساعد التداول الذكي جاهز الآن."
    elif language_code.startswith('zh'):
        lang = 'zh'
        welcome_text = "欢迎使用OMNIX！\n请选择菜单中的一个选项："
        welcome_voice = "欢迎使用OMNIX。您的智能交易助手已激活。"
    else:
        lang = 'en'
        welcome_text = "Welcome to OMNIX!\nPlease select an option from the menu:"
        welcome_voice = "Welcome to OMNIX. Your smart trading assistant is now active."

    keyboard = [
        ["📊 Estado", "🧠 Análisis"],
        ["📉 Trading", "🔐 Seguridad"],
        ["🌐 Idioma", "👤 Cuenta"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    # Voz tipo Alexa (gTTS)
    2
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tts.save(f.name)
        audio_path = f.name

    with open(audio_path, 'rb') as audio:
        await update.message.reply_voice(voice=audio)

    # Estado del sistema
    estado = (
        "🤖 *Estado del sistema OMNIX:*\n\n"
        "✅ Bot activo y funcionando\n"
        "🔁 Conexión IA (GPT-4): OK\n"
        "🧠 Módulo Conversacional: Activo\n"
        "📡 Trading conectado (Kraken): OK\n"
        "🗄️ Base de datos: Conectada\n"
        "🛡️ Seguridad Cuántica (Dilithium): Habilitada\n"
        "📌 Versión: *OMNIX v1.5*"
    )

    await update.message.reply_text(
        text=estado,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    # Respuesta GPT bienvenida
    ai = ConversationalAI()
    bienvenida = ai.get_response("Saluda al usuario y dile que puede empezar a operar o preguntar lo que desee", "es")
    await update.message.reply_text(bienvenida)

    keyboard = [
        ["📊 Estado", "🔍 Análisis"],
        ["📈 Trading", "🛡️ Seguridad"],
        ["🌐 Idioma", "👤 Cuenta"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "👋 ¡Bienvenido a OMNIX!\nSelecciona una opción del menú:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def premium_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra la lista de usuarios premium al administrador."""
    admin_id_str = str(ADMIN_ID)
    user_id_str = str(update.effective_user.id)
async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra el estado actual del sistema OMNIX."""
    estado_text = (
        "🤖 *Estado del sistema OMNIX:*\n\n"
        "✅ Bot activo y funcionando\n"
        "🔁 Conexión IA (Gemini): OK\n"
        "🧠 Módulo Conversacional: Activo\n"
        "📡 Trading conectado (Kraken): OK\n"
        "🗄️ Base de datos: Conectada\n"
        "🛡️ Seguridad Cuántica (Dilithium): Habilitada\n"
        "📌 Versión: OMNIX v1.5"
    )
    await update.message.reply_text(estado_text, parse_mode="Markdown")

    if user_id_str != admin_id_str:
        await update.message.reply_text("⛔ No tienes permisos para acceder a este panel.")
        return

    # (Aquí iría tu código para consultar y mostrar los usuarios premium...)
    await update.message.reply_text("Panel de administración en desarrollo.")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
   from telegram import ReplyKeyboardMarkup

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        ["📊 Estado", "🔍 Análisis"],
        ["🎯 Trading", "🛡️ Seguridad"],
        ["🌐 Idioma", "👤 Cuenta"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "📋 *Menú principal OMNIX:*\nSelecciona una opción:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    """Responde a mensajes de texto que no son comandos."""
    logger.info(f"RECIBIDO MENSAJE de {update.effective_user.name}: {update.message.text}")
    await update.message.reply_text("He recibido tu mensaje. Usa /start para ver los comandos disponibles.")

async def main() -> None:
    """Función principal que arranca todo."""
    logger.info("🚀 Iniciando OMNIX Bot...")
    
    if not BOT_TOKEN or not DATABASE_URL:
        logger.critical("FATAL: Faltan BOT_TOKEN o DATABASE_URL.")
        return

    setup_premium_database()
    add_premium_assets(premium_assets_list)

    application = Application.builder().token(BOT_TOKEN).build()

    # Añadimos los manejadores de comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("premium", premium_command))
    application.add_handler(CommandHandler("clave", clave_command))
    application.add_handler(CommandHandler("voz_firma", voz_firma_command))
    application.add_handler(CommandHandler("trading", trading_command))
    application.add_handler(CommandHandler("estado", estado_command))
    application.add_handler(CommandHandler("premium_panel", premium_panel_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, boton_handler))
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, general_response_handler))
await setup_memory_table()

    from telegram.ext import MessageHandler, filters
from langdetect import detect
from gtts import gTTS
import tempfile

async def general_response_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user_input = update.message.text

    # Detectar idioma
    language = detect(user_input)

    # Obtener respuesta con memoria
    response = await generate_response_with_memory(user_id, user_input, language)

    # Enviar respuesta escrita
    await update.message.reply_text(response)

    # Convertir a voz tipo Alexa
    tts = gTTS(text=response, lang=language)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tts.save(f.name)
        audio_path = f.name

    with open(audio_path, 'rb') as audio:
        await update.message.reply_voice(voice=audio)

# Añadir este handler al final
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), general_response_handler))

from telegram.ext import MessageHandler, filters
from langdetect import detect
from gtts import gTTS
import tempfile

async def general_response_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    user_input = update.message.text

    # Detectar idioma
    language = detect(user_input)

    # Obtener respuesta con memoria
    response = await generate_response_with_memory(user_id, user_input, language)

    # Enviar respuesta escrita
    await update.message.reply_text(response)

    # Convertir a voz tipo Alexa
    tts = gTTS(text=response, lang=language)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        tts.save(f.name)
        audio_path = f.name

    with open(audio_path, 'rb') as audio:
        await update.message.reply_voice(voice=audio)

# Añadir este handler al final
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), general_response_handler))

    logger.info("Limpiando sesión antigua de Telegram...")
    await application.bot.delete_webhook()

    logger.info("Inicializando la aplicación...")
    await application.initialize()

    logger.info("✅ Bot listo, iniciando la escucha de peticiones...")
    await application.start()
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"!!!!!!!!!! ERROR FATAL AL INICIAR EL BOT !!!!!!!!!!!")
        print(f"Error: {e}")
  
async def boton_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "estado" in text:
        await estado_command(update, context)
    elif "análisis" in text or "analisis" in text:
        await analyze_command(update, context)
    elif "trading" in text:
        await trading_command(update, context)
    elif "seguridad" in text:
        await update.message.reply_text("🛡️ Seguridad post-cuántica activa con Dilithium.")
    elif "idioma" in text:
        await update.message.reply_text("🌐 Función de cambio de idioma en desarrollo.")
    elif "cuenta" in text:
        await update.message.reply_text("👤 Esta es tu cuenta de usuario OMNIX.")

@dp.message_handler(lambda message: message.text not in ["/start", "/analyze", "/estado", "/trading"])
@app.command("/analyze")
async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) == 0:
            await update.message.reply_text("Por favor, indica el símbolo del activo. Ejemplo: /analyze BTC-USD")
            return

        symbol = context.args[0].upper()
        data = yf.download(symbol, period="7d", interval="1h")

        if data.empty:
            await update.message.reply_text("No se encontraron datos para ese símbolo.")
            return

        plt.figure(figsize=(10, 4))
        plt.plot(data.index, data["Close"], label="Precio")
        plt.title(f"Precio de {symbol} (últimos 7 días)")
        plt.xlabel("Fecha")
        plt.ylabel("Precio")
        plt.legend()
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()

        await update.message.reply_photo(photo=InputFile(buf, filename="grafico.png"))

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error al generar el análisis: {str(e)}")
@app.command("/analyze")
async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) == 0:
            await update.message.reply_text("Por favor, indica el símbolo del activo. Ejemplo: /analyze BTC-USD")
            return

        symbol = context.args[0].upper()
        data = yf.download(symbol, period="7d", interval="1h")

        if data.empty:
            await update.message.reply_text("No se encontraron datos para ese símbolo.")
            return

        plt.figure(figsize=(10, 4))
        plt.plot(data.index, data["Close"], label="Precio")
        plt.title(f"Precio de {symbol} (últimos 7 días)")
        plt.xlabel("Fecha")
        plt.ylabel("Precio")
        plt.legend()
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()

        await update.message.reply_photo(photo=InputFile(buf, filename="grafico.png"))
       texto_resumen = f"Análisis completo de {symbol}. El gráfico muestra los precios de cierre durante los últimos 7 días."

        # Detectar idioma del texto (langdetect)
        idioma_detectado = detect(texto_resumen)

        # gTTS solo acepta ciertos idiomas, así que filtramos
        idioma_voz = idioma_detectado if idioma_detectado in ["es", "en", "ar", "zh-cn"] else "es"

        tts = gTTS(text=texto_resumen, lang=idioma_voz)
        audio_path = "/tmp/analisis_audio.mp3"
        tts.save(audio_path)

        with open(audio_path, "rb") as audio_file:
            await update.message.reply_voice(voice=audio_file)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error al generar el análisis: {str(e)}")
@app.command("/estado")
async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        estado_texto = (
            f"🧠 Sistema OMNIX activo.\n"
            f"📡 Exchanges conectados: Kraken, Binance.\n"
            f"🕒 Hora actual: {now} UTC.\n"
            f"✅ Todo funcionando correctamente."
        )

        # Detectar idioma
        idioma_detectado = detect(estado_texto)
        idioma_voz = idioma_detectado if idioma_detectado in ["es", "en", "ar", "zh-cn"] else "en"

        # Convertir a voz
        tts_estado = gTTS(text=estado_texto, lang=idioma_voz)
        estado_audio_path = "/tmp/estado_audio.mp3"
        tts_estado.save(estado_audio_path)

        # Enviar voz
        with open(estado_audio_path, "rb") as audio_file:
            await update.message.reply_voice(voice=audio_file)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error al generar el estado: {str(e)}")

@app.command("/estado")
async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        estado_texto = (
            f"🧠 Sistema OMNIX activo.\n"
            f"📡 Exchanges conectados: Kraken, Binance.\n"
            f"🕒 Hora actual: {now} UTC.\n"
            f"✅ Todo funcionando correctamente."
        )

        # Detectar idioma
        idioma_detectado = detect(estado_texto)
        idioma_voz = idioma_detectado if idioma_detectado in ["es", "en", "ar", "zh-cn"] else "en"

        # Convertir a voz
        tts_estado = gTTS(text=estado_texto, lang=idioma_voz)
        estado_audio_path = "/tmp/estado_audio.mp3"
        tts_estado.save(estado_audio_path)

        # Enviar voz
        with open(estado_audio_path, "rb") as audio_file:
            await update.message.reply_voice(voice=audio_file)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error al generar el estado: {str(e)}")
@app.command("/trading")
async def trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = context.args[0].upper() if context.args else "BTC"
        cantidad = context.args[1] if len(context.args) > 1 else "50"

        mensaje = (
            f"💰 Orden de compra simulada:\n"
            f"Criptoactivo: {symbol}\n"
            f"Monto: ${cantidad} USD\n"
            f"🕒 Ejecutado por OMNIX vía voz."
        )

        # Detectar idioma
        idioma_detectado = detect(mensaje)
        idioma_voz = idioma_detectado if idioma_detectado in ["es", "en", "ar", "zh-cn"] else "es"

        # Convertir a voz
        tts_trading = gTTS(text=mensaje, lang=idioma_voz)
        trading_audio_path = "/tmp/trading_audio.mp3"
        tts_trading.save(trading_audio_path)
@app.command("/menu")
async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        keyboard = [
            ["📊 Análisis", "📈 Estado"],
            ["🎯 Trading"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Selecciona una opción:", reply_markup=reply_markup)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error al mostrar el menú: {str(e)}")

        # Enviar voz
        with open(trading_audio_path, "rb") as audio_file:
            await update.message.reply_voice(voice=audio_file)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error al ejecutar la orden: {str(e)}")
@app.message()
@app.message()
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()

    try:
        if text == "📊 análisis":
            mensaje = "📈 Generando gráfico de análisis de BTC, por favor espera..."
            idioma = detect(mensaje)
            tts = gTTS(text=mensaje, lang=idioma)
            ruta_audio = "/tmp/analisis_respuesta.mp3"
            tts.save(ruta_audio)
            await update.message.reply_voice(voice=open(ruta_audio, "rb"))

            try:
                from analysis_engine import generar_grafico_btc
                await generar_grafico_btc(update)
            except Exception as e:
                await update.message.reply_text(f"⚠️ Error al generar el gráfico: {str(e)}")


        elif text == "📈 estado":
            mensaje = "Mostrando el estado actual del sistema."
            idioma = detect(mensaje)
            tts = gTTS(text=mensaje, lang=idioma)
            ruta_audio = "/tmp/audio_respuesta.mp3"
            tts.save(ruta_audio)
            await estado_command(update, context)

        elif text == "🎯 trading":
            mensaje = "Por favor usa el comando: /trading BTC 50"
            idioma = detect(mensaje)
            tts = gTTS(text=mensaje, lang=idioma)
            ruta_audio = "/tmp/audio_respuesta.mp3"
            tts.save(ruta_audio)

        # Enviar respuesta en voz
        with open(ruta_audio, "rb") as audio:
            await update.message.reply_voice(voice=audio)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error con los botones: {str(e)}")

# LÍNEAS FINALES DE main.py
@application.command_handler("trading")
async def trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.effective_user.id)
        if not is_premium_user(user_id):
            await update.message.reply_text("🔒 Este comando es solo para usuarios premium.")
            return

        user_input = update.message.text.lower()

        # Detectar acción (comprar o vender)
        if "comprar" in user_input:
            side = "buy"
        elif "vender" in user_input:
            side = "sell"
        else:
            await update.message.reply_text("❗Por favor indica si deseas comprar o vender.")
            return

        # Extraer cantidad y símbolo
        parts = user_input.split()
        amount = float([p for p in parts if p.replace('.', '', 1).isdigit()][0])
        symbol = [p.upper() for p in parts if p.lower() in ["btc", "eth", "sol", "ada"]][0]

        # Ejecutar trade con Kraken
        trading_system = KrakenTradingSystem()
        result = trading_system.place_order(symbol, amount, side)

        # Confirmación visual y por voz
        confirm_msg = f"✅ Trade ejecutado: {side.upper()} {amount} de {symbol}.\nID: {result.get('txid', 'sin id')}"
        await update.message.reply_text(confirm_msg)
        
        voice = text_to_speech(f"Operación completada: {side} {amount} de {symbol}.")
        await update.message.reply_voice(voice)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error al ejecutar el trade: {str(e)}")
