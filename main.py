import logging
import asyncio
import os
import psycopg2
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from gtts import gTTS

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


async def premium_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra la lista de usuarios premium al administrador."""
    admin_id_str = str(ADMIN_ID)
    user_id_str = str(update.effective_user.id)

    if user_id_str != admin_id_str:
        await update.message.reply_text("⛔ No tienes permisos para acceder a este panel.")
        return

    # (Aquí iría tu código para consultar y mostrar los usuarios premium...)
    await update.message.reply_text("Panel de administración en desarrollo.")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    
    
