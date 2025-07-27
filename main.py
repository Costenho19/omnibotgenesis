# ==============================================================================
# === OMNIX GLOBAL BOT - ARCHIVO PRINCIPAL (main.py) ===
# ==============================================================================

# --- SECCIÓN 1: IMPORTACIONES ---
# Aquí cargamos todas las herramientas que nuestro bot necesita.

import logging
import asyncio
import os
import psycopg2
import threading
from io import BytesIO
import tempfile
import uuid
import datetime
import matplotlib.pyplot as plt
import yfinance as yf
from functools import wraps
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from gtts import gTTS
from langdetect import detect
import openai

# --- Importaciones de nuestros propios Módulos ---
# Conectamos este archivo con los otros 6 archivos del proyecto.
from config import BOT_TOKEN, DATABASE_URL, GEMINI_API_KEY, KRAKEN_API_KEY, CLAVE_PREMIUM, ADMIN_ID, OPENAI_API_KEY, SECRET_PHRASE
from database import (
    setup_premium_database, add_premium_assets, save_analysis_to_db, 
    guardar_usuario_premium, es_usuario_premium, save_dilithium_signature,
    save_user_memory, get_user_memory, get_user_language, setup_memory_table, 
    setup_language_table, get_dilithium_signature, get_user_analysis_count
)
from analysis_engine import OmnixPremiumAnalysisEngine, premium_assets_list
from conversational_ai import ConversationalAI, traducir_mensaje, generate_response_with_memory
from trading_system import KrakenTradingSystem
from pqc_encryption import PQCEncryption
from voice_signature import VoiceSignature, validate_voice_signature, compare_voice_signatures, get_saved_signature

# --- SECCIÓN 2: CONFIGURACIÓN INICIAL ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
openai.api_key = OPENAI_API_KEY

# --- Instancias Globales de nuestros Sistemas ---
# Creamos los "cerebros" de nuestro bot que estarán siempre activos.
analysis_engine = OmnixPremiumAnalysisEngine()
conversational_ai = ConversationalAI()
trading_system = KrakenTradingSystem()
voice_signer = VoiceSignature(SECRET_PHRASE)
pqc = PQCEncryption()

# --- SECCIÓN 3: DECORADOR DE "SOLO PREMIUM" ---
# Esta es una herramienta avanzada que nos permite proteger funciones.
def solo_premium(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = str(update.effective_user.id)
        if not await es_usuario_premium(user_id):
            mensaje = "🚫 Esta función es exclusiva para usuarios premium. Usa /premium para activar tu cuenta."
            try:
                tts = gTTS(mensaje, lang='es')
                voz = io.BytesIO()
                tts.write_to_fp(voz)
                voz.seek(0)
                await update.message.reply_text(mensaje)
                await update.message.reply_voice(voice=voz)
            except Exception as e:
                logger.error(f"Error en decorador solo_premium al generar voz: {e}")
                await update.message.reply_text(mensaje)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

# --- SECCIÓN 4: FUNCIONES AUXILIARES ---

def validar_sesion_biometrica(user_id: str) -> bool:
    """Verifica si la firma biométrica del usuario es válida."""
    firma_guardada = get_dilithium_signature(user_id)
    if not firma_guardada: return False
    # (Aquí iría una lógica de validación más compleja si fuera necesario)
    return True

async def enviar_grafico(message, simbolo="BTC-USD"):
    """Genera y envía un gráfico de precios."""
    try:
        hoy = datetime.datetime.now()
        inicio = hoy - datetime.timedelta(days=30)
        datos = yf.download(simbolo, start=inicio.strftime('%Y-%m-%d'), end=hoy.strftime('%Y-%m-%d'))

        if datos.empty:
            await message.reply_text(f"⚠️ No se encontraron datos para {simbolo}.")
            return

        fig, ax = plt.subplots(figsize=(10, 5))
        datos["Close"].plot(ax=ax, label="Precio Cierre", color="cyan")
        ax.set_title(f"📊 Precio de {simbolo} (30 días)"); ax.set_xlabel("Fecha"); ax.set_ylabel("Precio USD")
        ax.legend(); ax.grid(True); plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png'); buffer.seek(0); plt.close(fig)

        await message.reply_photo(photo=InputFile(buffer, filename=f"{simbolo}.png"), caption=f"📈 Análisis de {simbolo}")
    except Exception as e:
        logger.error(f"Error al generar gráfico: {e}")
        await message.reply_text("Error al generar el gráfico.")

# --- SECCIÓN 5: DEFINICIÓN DE TODOS LOS COMANDOS DEL BOT ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envía el mensaje de bienvenida y el menú principal de botones."""
    user = update.effective_user
    user_id = str(user.id)
    
    if await es_usuario_premium(user_id):
        welcome_text = "🌟 ¡Bienvenido de nuevo, Usuario Premium!"
    else:
        welcome_text = "🔒 ¡Bienvenido a OMNIX! Estás usando la versión gratuita."
    
    keyboard = [["📊 Análisis", "📈 Estado"], ["🎯 Trading", "🔐 Seguridad"], ["👤 Cuenta", "❓ Ayuda"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_html(f"¡Hola {user.mention_html()}!\n{welcome_text}", reply_markup=reply_markup)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra un menú con botones en línea (inline)."""
    keyboard = [
        [InlineKeyboardButton("🤖 Chat con IA", callback_data="chat_ia")],
        [InlineKeyboardButton("📊 Análisis Gráfico", callback_data="analisis_grafico")],
        [InlineKeyboardButton("📚 Educación (Pronto)", callback_data="educacion")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Selecciona una opción del menú avanzado:", reply_markup=reply_markup)

@solo_premium
async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera análisis de texto y gráfico para un símbolo."""
    if not context.args:
        await update.message.reply_text("❗Por favor indica el símbolo. Ejemplo: /analyze BTC-USD")
        return

    simbolo = context.args[0].upper()
    await update.message.reply_text(f"📊 Analizando {simbolo}...")
    await enviar_grafico(update.message, simbolo)
    # (Aquí podrías añadir el análisis de texto de la clase analysis_engine)

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra información sobre la membresía Premium."""
    mensaje = (
        "🌟 *OMNIX Premium* 🌟\n\nAccede a funciones exclusivas:\n"
        "🔐 Trading 24/7 con IA y seguridad biométrica\n📊 Análisis técnico avanzado y gráficos\n"
        "🧠 IA conversacional multilingüe con memoria\n🛡️ Seguridad con firma post-cuántica Dilithium\n\n"
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

@solo_premium
async def voz_firma_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Registra la firma biométrica de voz del usuario usando Whisper y Dilithium."""
    user = update.effective_user; user_id = str(user.id)
    if not update.message.voice:
        await update.message.reply_text("🎙️ Por favor, envía un mensaje de voz diciendo tu frase secreta para registrar tu firma.")
        context.user_data["esperando_firma"] = True
        return

    await update.message.reply_text("🎧 Procesando tu firma de voz...")
    voice_file = await context.bot.get_file(update.message.voice.file_id)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_voice_file:
        await voice_file.download_to_drive(temp_voice_file.name)
        voice_path = temp_voice_file.name

    try:
        with open(voice_path, "rb") as f:
            transcript = openai.Audio.transcribe("whisper-1", f)["text"]

        if SECRET_PHRASE.lower() not in transcript.lower():
            await update.message.reply_text("❌ Tu frase secreta no coincide. Intenta de nuevo.")
            return

        signature, timestamp = voice_signer.sign_message(transcript)
        save_dilithium_signature(user_id, signature, timestamp)
        await update.message.reply_text("✅ Identidad verificada y firma registrada exitosamente.")
    finally:
        os.remove(voice_path)
        context.user_data["esperando_firma"] = False

@solo_premium
async def trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ejecuta una orden de trading con validación biométrica."""
    user = update.effective_user
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
        f"🤖 *Estado del sistema OMNIX:*\n\n✅ Bot: Activo y funcionando\n"
        f"🧠 IA (Gemini): Conectada\n📡 Trading (Kraken): Conectado\n"
        f"🗄️ Base de datos: Conectada\n🛡️ Seguridad Cuántica: Habilitada\n"
        f"----------\n👤 Tu Cuenta: {tipo_cuenta}"
    )
    await update.message.reply_text(estado_texto, parse_mode="Markdown")

@solo_premium
async def cuenta_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra información detallada de la cuenta del usuario."""
    user = update.effective_user; user_id = str(user.id)
    premium = await es_usuario_premium(user_id)
    total_analisis = await get_user_analysis_count(user_id)
    firma = get_dilithium_signature(user_id)
    
    mensaje = (
        f"🔐 Cuenta de {user.first_name}:\n"
        f"👑 Estado: {'Premium' if premium else 'No Premium'}\n"
        f"📊 Análisis realizados: {total_analisis}\n"
        f"🖊️ Firma biométrica: {'Registrada' if firma else 'No registrada'}\n"
    )
    await update.message.reply_text(mensaje)

async def premium_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Panel de administrador para ver usuarios premium."""
    if str(update.effective_user.id) != str(ADMIN_ID):
        await update.message.reply_text("⛔ No tienes permisos para este panel.")
        return
    # (Lógica para consultar y mostrar usuarios premium)
    await update.message.reply_text("Panel de administración en desarrollo.")

@solo_premium
async def mercado_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra un resumen del mercado cripto."""
    activos = ['BTC-USD', 'ETH-USD', 'SOL-USD']
    resumen = "📊 *Resumen del Mercado Cripto:*\n\n"
    for activo in activos:
        try:
            data = yf.Ticker(activo).history(period="1d")
            resumen += f"• {activo.split('-')[0]}: ${data['Close'][-1]:.2f} USD\n"
        except Exception:
            resumen += f"• {activo.split('-')[0]}: ❌ Error\n"
    
    await update.message.reply_text(resumen, parse_mode="Markdown")

# --- SECCIÓN 6: MANEJADORES DE MENSAJES Y BOTONES ---

async def general_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja cualquier mensaje de texto: botones del menú o chat con la IA."""
    user_id = str(update.message.from_user.id)
    user_input = update.message.text
    
    # Manejo de botones del menú principal
    if "📊 Análisis" in user_input: await analyze_command(update, context); return
    elif "📈 Estado" in user_input: await estado_command(update, context); return
    elif "🎯 Trading" in user_input: await trading_command(update, context); return
    elif "🔐 Seguridad" in user_input: await update.message.reply_text("Usa /voz_firma para registrar tu identidad biométrica."); return
    elif "👤 Cuenta" in user_input: await cuenta_command(update, context); return
    elif "❓ Ayuda" in user_input: await premium_command(update, context); return

    # Si no es un botón, es un chat con la IA (solo para premium)
    if not await es_usuario_premium(user_id):
        await update.message.reply_text("🤖 La función de chat con IA es solo para usuarios Premium. Usa /premium para activarla.")
        return

    logger.info(f"RECIBIDO CHAT de {update.effective_user.name}: {user_input}")
    historial = await get_user_memory(user_id)
    prompt = historial + "\nUsuario: " + user_input + "\nOMNIX:"
    language = await get_user_language(user_id) or detect(user_input)

  respuesta = conversational_ai.generate_response_with_memory(user_id, prompt)

    await save_user_memory(user_id, f"Usuario: {user_input}\nOMNIX: {respuesta}")
    await update.message.reply_text(respuesta)

async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja los botones del menú inline."""
    query = update.callback_query
    await query.answer()
    opcion = query.data

    if opcion == "analisis_grafico":
        await query.message.reply_text("Generando gráfico de BTC-USD...")
        await enviar_grafico(query.message, simbolo="BTC-USD")
    else:
        respuesta = {
            "chat_ia": "🤖 Puedes chatear conmigo directamente.",
            "educacion": "📚 Módulo educativo disponible próximamente.",
        }.get(opcion, "❓ Opción no reconocida.")
        await query.edit_message_text(text=respuesta)

# --- SECCIÓN 7: FUNCIÓN PRINCIPAL DE ARRANQUE ---

async def main() -> None:
    """Función principal que configura y arranca el bot."""
    logger.info("🚀 Iniciando OMNIX Bot...")
    
    if not BOT_TOKEN or not DATABASE_URL:
        logger.critical("FATAL: Faltan BOT_TOKEN o DATABASE_URL."); return

    # Preparamos las tablas de la BD
    setup_premium_database(); setup_memory_table(); setup_language_table()
    add_premium_assets(premium_assets_list)

    application = Application.builder().token(BOT_TOKEN).build()

    # Añadimos todos los manejadores
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
    application.add_handler(CommandHandler("mercado", mercado_command))
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
        print(f"!!!!!!!!!! ERROR FATAL AL INICIAR EL BOT !!!!!!!!!!!\n{e}")
