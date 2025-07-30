# ================= OMNIX MAIN ====================
import os
import asyncio
import logging
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import BOT_TOKEN, WEBHOOK_URL
from conversational_ai import generate_response
from voice_engine import generar_audio
from database import save_analysis_to_db
from analysis_engine import generar_analisis_completo, generar_grafico_btc
from trading_system import ejecutar_trade
from voice_signature import procesar_firma_biometrica
from pqc_encryption import cifrar_con_dilithium
from sharia_validator import validar_sharia
from quantum_engine import montecarlo_predict, quantum_portfolio_analysis

# ========== LOG ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== FLASK PANEL ==========
app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return '🧠 OMNIX Running - Quantum Secure'

def run_flask():
    app_flask.run(host="0.0.0.0", port=8080)

# ========== HANDLERS ==========
async def start(update: Update, context): await update.message.reply_text("🤖 Bienvenido a OMNIX.")
async def analyze(update: Update, context): await generar_analisis_completo(update, context)
async def trading(update: Update, context): await ejecutar_trade(update, context)
async def voz_firma(update: Update, context): await procesar_firma_biometrica(update, context)
async def estado(update: Update, context): await update.message.reply_text("🟢 OMNIX está activo.")
async def quantum_predict(update: Update, context): await montecarlo_predict(update, context)
async def sharia_check(update: Update, context): await validar_sharia(update, context)
async def quantum_portfolio(update: Update, context): await quantum_portfolio_analysis(update, context)
async def bolsa(update: Update, context): await update.message.reply_text("📈 Bolsa de valores.")
async def finanzas_globales(update: Update, context): await update.message.reply_text("🌍 Finanzas globales.")
async def handle_message(update: Update, context): await generate_response(update, context)

# ========== MAIN ==========
async def main():
    Thread(target=run_flask).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("trading", trading))
    app.add_handler(CommandHandler("voz_firma", voz_firma))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(CommandHandler("quantum_predict", quantum_predict))
    app.add_handler(CommandHandler("sharia_check", sharia_check))
    app.add_handler(CommandHandler("quantum_portfolio", quantum_portfolio))
    app.add_handler(CommandHandler("bolsa", bolsa))
    app.add_handler(CommandHandler("finanzas_globales", finanzas_globales))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    if WEBHOOK_URL is None or BOT_TOKEN is None:
        raise ValueError("❌ WEBHOOK_URL o BOT_TOKEN no están definidos.")

   

# ========== EJECUCIÓN ==========
if __name__ == "__main__":
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8445)),
        url_path=BOT_TOKEN,
        webhook_url=WEBHOOK_URL + BOT_TOKEN,
    )


      
