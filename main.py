# === OMNIX V3.8 PRO SHIELDED - RAILWAY PRODUCTION (main.py) ===

import logging
import asyncio
import os
import sys
import threading
import nest_asyncio
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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

# === LOGGING ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === FLASK APP ===
app_flask = Flask(__name__)
@app_flask.route("/")
def home():
    return '🧠 OMNIX V3.8 PRO SHIELDED - Running'

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=port)

# === HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bienvenido a OMNIX Quantum Assistant.")

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    respuesta, audio_path = await generate_response(texto)
    await update.message.reply_text(respuesta)
    await update.message.reply_voice(voice=open(audio_path, 'rb'))

# === FUNCIÓN PRINCIPAL ===
async def main():
    if not BOT_TOKEN or not WEBHOOK_URL:
        logger.critical("❌ BOT_TOKEN o WEBHOOK_URL no configurados.")
        os._exit(1)

    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("🌐 Servidor Flask iniciado.")

    application = Application.builder().token(BOT_TOKEN).build()

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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

  # === SECCIÓN FINAL - FUNCIONES Y HANDLERS ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = "🚀 Bienvenido a OMNIX Quantum Assistant.\n\nEstoy listo para ayudarte con trading automático, análisis de mercado y más."
    await update.message.reply_text(mensaje)

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    respuesta, audio_path = await generate_response(texto)
    await update.message.reply_text(respuesta)
    await update.message.reply_voice(voice=open(audio_path, 'rb'))

async def main():
    logging.basicConfig(level=logging.INFO)
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    await application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        webhook_url=WEBHOOK_URL,
    )

# === PUNTO DE ENTRADA ===

if __name__ == "__main__":
    print("🚀 Iniciando OMNIX Quantum Assistant...")

   # === SECCIÓN FINAL - FUNCIONES Y HANDLERS ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = "🚀 Bienvenido a OMNIX Quantum Assistant.\n\nEstoy listo para ayudarte con trading automático, análisis de mercado y más."
    await update.message.reply_text(mensaje)

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    respuesta, audio_path = await generate_response(texto)
    await update.message.reply_text(respuesta)
    await update.message.reply_voice(voice=open(audio_path, 'rb'))

if __name__ == "__main__":
    print("🚀 Iniciando OMNIX Quantum Assistant...")

    try:
        import nest_asyncio
        nest_asyncio.apply()

        from telegram.ext import ApplicationBuilder
        application = ApplicationBuilder().token(BOT_TOKEN).build()

        webhook_url = WEBHOOK_URL
        application.run_webhook(
            listen="0.0.0.0",
            port=8445,
            webhook_url=webhook_url,
        )

    except Exception as e:
        print("❌ Error inesperado en el arranque:", e)
        import sys
        sys.exit(1)
