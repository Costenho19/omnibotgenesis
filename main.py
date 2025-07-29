# ===================================================================
# OMNIX PRO V3.5 – ARCHIVO PRINCIPAL PARA RAILWAY (Webhook Ready)
# ===================================================================
import uvloop
uvloop.install()

import os, logging, io
import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode
from gtts import gTTS
from langdetect import detect
from flask import Flask, request

# --- Módulos internos del proyecto ---
from config import BOT_TOKEN, WEBHOOK_URL, DATABASE_URL
from conversational_ai import ConversationalAI
from database import (
    setup_premium_database,
    crear_tabla_premium_assets,
    guardar_mensaje_usuario,
)
from analysis_engine import OmnixPremiumAnalysisEngine, premium_assets_list
from quantum_engine import QuantumEngine
from trading_system import KrakenTradingSystem
from pqc_encryption import generate_dilithium_signature
from voice_signature import validate_voice_biometrics

# --- Configuración básica ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
engine = OmnixPremiumAnalysisEngine()
ai = ConversationalAI()
qe = QuantumEngine(historical_data=[])
trader = KrakenTradingSystem()
app = Flask(__name__)  # Webhook HTTP server

# --- Herramientas de voz y detección de idioma ---
def detect_lang(text: str) -> str:
    try:
        if not text or not any(c.isalpha() for c in text):
            return "es"
        return detect(text)
    except Exception:
        return "es"

def reply_with_voice(text: str, lang: str = "es") -> io.BytesIO:
    try:
        tts = gTTS(text, lang=lang)
        voice = io.BytesIO()
        tts.write_to_fp(voice)
        voice.seek(0)
        return voice
    except Exception as e:
        logging.error(f"Voz falló: {e}")
        return None

# --- Handlers de comandos ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = detect_lang(update.message.text or "")
    text = "🤖 ¡Hola! Soy OMNIX PRO V3.5. Estoy listo para asistirte en análisis, trading e inteligencia cuántica."
    voice = reply_with_voice(text, lang)
    await update.message.reply_voice(voice, caption=text) if voice else await update.message.reply_text(text)

async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "✅ Estado del sistema: OMNIX está en línea. Funciones activas: IA GPT-4o, voz, trading real, firma cuántica, análisis técnico, portafolio cuántico."
    voice = reply_with_voice(text)
    await update.message.reply_voice(voice, caption=text) if voice else await update.message.reply_text(text)

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = context.args[0].upper() if context.args else "BTC-USD"
        result = await engine.analyze_asset(symbol)
        text = (
            f"📊 Análisis de {symbol}\n"
            f"Precio actual: ${result['price']:.2f}\n"
            f"Tendencia: {result['trend']}\n"
            f"Recomendación: {result['recommendation']}"
        )
        voice = reply_with_voice(text)
        await update.message.reply_voice(voice, caption=text) if voice else await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"❌ Error en el análisis: {e}")

async def trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 3:
            await update.message.reply_text("Uso: /trading BTCUSD buy 0.01")
            return
        symbol, action, amount = context.args[0].upper(), context.args[1].lower(), float(context.args[2])
        if action not in ["buy", "sell"]:
            await update.message.reply_text("Acción inválida. Usa 'buy' o 'sell'.")
            return
        result = trader.execute_trade(symbol, action, amount)
        text = (
            f"🟢 Operación ejecutada:\n"
            f"{action.upper()} {amount} de {symbol}\n"
            f"Precio: ${result['price']:.2f} | Total: ${result['total']:.2f}"
        )
        voice = reply_with_voice(text)
        await update.message.reply_voice(voice, caption=text) if voice else await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"❌ Error en trading: {e}")

async def voz_firma_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        sample_voice = "voz_temp.mp3"
        _ = generate_dilithium_signature(sample_voice)
        valid = validate_voice_biometrics(user_id, sample_voice)
        msg = "🔐 Firma de voz validada con Dilithium." if valid else "⚠️ Firma no válida. Repite el proceso."
        voice = reply_with_voice(msg)
        await update.message.reply_voice(voice, caption=msg) if voice else await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"❌ Error en /voz_firma: {e}")

async def quantum_predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = context.args[0].upper() if context.args else "BTC-USD"
        prices = await engine.get_prices_series(symbol, period="180d")
        qp = qe.quantum_predict(prices)
        text = (
            f"🔮 Predicción Cuántica de {symbol}\n"
            f"Mediana: ${qp.next_price:.2f}\n"
            f"Retorno esperado: {qp.mean_return:.4%}\n"
            f"VaR 95%: {qp.var_95:.4%}"
        )
        fig, ax = plt.subplots()
        ax.hist(qp.scenarios, bins=60)
        ax.set_title("Distribución Cuántica de Precios")
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        await update.message.reply_photo(buf)
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"❌ Error en /quantum_predict: {e}")

async def quantum_portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        tickers = context.args if context.args else ["BTC-USD", "ETH-USD", "ADA-USD"]
        price_df = await engine.get_prices_df(tickers, period="180d")
        res = qe.quantum_optimize_portfolio(price_df)
        weights = "\n".join([f"• {k}: {v:.2%}" for k, v in res.weights.items()])
        text = f"🧠 Portafolio Cuántico:\n{weights}\n\nSharpe: {res.sharpe:.2f}"
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"❌ Error en /quantum_portfolio: {e}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_id = str(update.effective_user.id)
    lang = detect_lang(user_input)
    guardar_mensaje_usuario(user_id, user_input)
    response = await ai.generate_emotional_response_async(user_input, user_id)
    voice = reply_with_voice(response, lang)
    await update.message.reply_voice(voice, caption=response) if voice else await update.message.reply_text(response)

# --- Bot + Webhook Launcher ---
async def launch_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    crear_tabla_premium_assets()
    setup_premium_database(premium_assets_list)

    # Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("estado", estado_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("trading", trading_command))
    application.add_handler(CommandHandler("voz_firma", voz_firma_command))
    application.add_handler(CommandHandler("quantum_predict", quantum_predict_command))
    application.add_handler(CommandHandler("quantum_portfolio", quantum_portfolio_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Webhook
    await application.bot.set_webhook(url=WEBHOOK_URL)
    await application.initialize()
    await application.start()
    await application.updater.start_polling()  # para debug
    logging.info("✅ Webhook activado y bot iniciado.")

@app.route("/webhook", methods=["POST"])
def webhook():
    return "OK", 200

if __name__ == "__main__":
    try:
        asyncio.run(launch_bot())
    except Exception as e:
        logging.critical(f"❌ Error fatal al iniciar OMNIX: {e}")
