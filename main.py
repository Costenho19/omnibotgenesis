
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

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Realiza un análisis de texto de un activo (solo premium)."""
    user = update.effective_user
    if not await es_usuario_premium(user.id):
        await update.message.reply_text("🚫 Este comando es exclusivo para usuarios Premium.", parse_mode="Markdown")
        return
        
    if not context.args:
        await update.message.reply_text("Uso: /analyze <SÍMBOLO>")
        return
    
    symbol = context.args[0].upper()
    await update.message.reply_text(f"Análisis de texto para {symbol} en desarrollo.")
    # (Aquí iría tu lógica de análisis de texto)

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

async def trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ejecuta una orden de trading."""
    user = update.effective_user
    if not await es_usuario_premium(user.id):
        await update.message.reply_text("🚫 Este comando es exclusivo para usuarios Premium.")
        return
    
    # (Tu lógica de trading aquí)
    await update.message.reply_text("Función de trading en desarrollo.")

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
