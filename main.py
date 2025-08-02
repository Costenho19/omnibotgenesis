# ==============================================================================
# === OMNIX V3.8 PRO SHIELDED - RAILWAY PRODUCTION (main.py) ===
# ==============================================================================
# Arquitectura Webhook-First, modular y optimizada para producción.

# --- SECCIÓN 1: IMPORTACIONES ---
import logging
import asyncio
import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Módulos Internos del Proyecto ---
# Se asume que estos módulos y funciones existen en sus respectivos archivos.
from config import BOT_TOKEN, WEBHOOK_URL
from conversational_ai import generate_response
from voice_engine import generar_audio
from database import save_analysis_to_db, guardar_sugerencia
from analysis_engine import generar_analisis_completo, generar_grafico_btc
from trading_system import ejecutar_trade, consultar_wallet
from voice_signature import procesar_firma_biometrica
from pqc_encryption import cifrar_con_dilithium
from sharia_validator import validar_sharia
from quantum_engine import montecarlo_predict, quantum_portfolio_analysis

# --- SECCIÓN 2: CONFIGURACIÓN INICIAL ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Aplicación Web Flask (Panel de Estado) ---
app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return '🧠 OMNIX V3.8 PRO SHIELDED - Quantum Ready & Actively Running'

def run_flask_in_thread():
    """Ejecuta la aplicación Flask en un hilo separado para no bloquear el bot."""
    port = int(os.environ.get("PORT", 8080))
    # Usamos 'werkzeug' para un servidor de producción más estable que el de desarrollo de Flask
    from werkzeug.serving import run_simple
    run_simple(hostname="0.0.0.0", port=port, application=app_flask)

# --- SECCIÓN 3: HANDLERS DE COMANDOS DE TELEGRAM ---
# Cada función maneja un comando específico del bot.

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = "🚀 Bienvenido a OMNIX Quantum Assistant.\n\nEstoy listo para ayudarte con trading automático, análisis de mercado y más."
    await update.message.reply_text(mensaje)

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await generar_analisis_completo(update, context)

async def trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ejecutar_trade(update, context)

async def voz_firma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await procesar_firma_biometrica(update, context)

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🟢 OMNIX está activo y funcionando.")

async def quantum_predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await montecarlo_predict(update, context)

async def quantum_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await quantum_portfolio_analysis(update, context)

async def sharia_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await validar_sharia(update, context)

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = await consultar_wallet()
    await update.message.reply_text(resultado, parse_mode="Markdown")

async def sugerencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = " ".join(context.args)
    if texto:
        await asyncio.to_thread(guardar_sugerencia, update.effective_user.id, texto)
        await update.message.reply_text("💡 Sugerencia recibida.")
    else:
        await update.message.reply_text("✍️ Escribe algo después del comando.")

# --- SECCIÓN 4: MANEJADOR GENERAL DE MENSAJES ---
async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    texto = update.message.text
    user_id = str(update.effective_user.id)
    
    try:
        respuesta = await asyncio.to_thread(generate_response, user_id, texto)
        await update.message.reply_text(respuesta)

        audio_path = await asyncio.to_thread(generar_audio, respuesta)
        if audio_path and os.path.exists(audio_path):
            try:
                with open(audio_path, 'rb') as audio_file:
                    await update.message.reply_voice(voice=audio_file)
            finally:
                os.remove(audio_path) # Aseguramos que el archivo se borre
        
    except Exception as e:
        logger.error(f"Error en manejar_mensaje: {e}")
        await update.message.reply_text("⚠️ Ocurrió un error al procesar tu mensaje.")

# --- SECCIÓN 5: FUNCIÓN PRINCIPAL DE ARRANQUE ---
async def main():
    """Configura y arranca el bot de Telegram en modo Webhook."""
    if not BOT_TOKEN or not WEBHOOK_URL:
        logger.critical("❌ FATAL: BOT_TOKEN o WEBHOOK_URL no están configurados en el entorno.")
        return # Usamos return para salir limpiamente
        
    application = Application.builder().token(BOT_TOKEN).build()

    # --- Registro de Handlers ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("analyze", analyze))
    application.add_handler(CommandHandler("trading", trading))
    application.add_handler(CommandHandler("voz_firma", voz_firma))
    application.add_handler(CommandHandler("estado", estado))
    application.add_handler(CommandHandler("quantum_predict", quantum_predict))
    application.add_handler(CommandHandler("quantum_portfolio", quantum_portfolio))
    application.add_handler(CommandHandler("sharia_check", sharia_check))
    application.add_handler(CommandHandler("wallet", wallet))
    application.add_handler(CommandHandler("sugerencia", sugerencia))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    port = int(os.environ.get("PORT", 8443))
    logger.info(f"Iniciando Webhook en el puerto {port}...")
    
    # run_webhook es una función que bloquea, por lo que debe ser la última llamada en main()
    await application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=BOT_TOKEN, # Usar el token como path añade una capa de seguridad
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )

# --- SECCIÓN 6: PUNTO DE ENTRADA DEL PROGRAMA ---
if __name__ == "__main__":
    logger.info("Iniciando OMNIX V3.8 PRO SHIELDED...")
    
    # 1. Inicia el servidor Flask en un hilo separado ANTES de iniciar el bot.
    flask_thread = threading.Thread(target=run_flask_in_thread, daemon=True)
    flask_thread.start()
    logger.info("🌐 Servidor web Flask iniciado en un hilo paralelo.")
    
    # 2. Inicia el bot de Telegram.
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"!!!!!!!!!! ERROR FATAL AL ARRANCAR EL BOT !!!!!!!!!!!\n{e}")
