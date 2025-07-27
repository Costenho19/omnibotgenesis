# ==============================================================================
# === OMNIX GLOBAL BOT - ARCHIVO PRINCIPAL (main.py) ===
# ==============================================================================

# --- SECCIÓN 1: IMPORTACIONES ---
import logging
import asyncio
import os
import psycopg2
import threading
import io
import tempfile
import uuid
import datetime
import matplotlib.pyplot as plt
import yfinance as yf
from functools import wraps
from gtts import gTTS
from langdetect import detect
import openai

from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# --- MÓDULOS INTERNOS ---
from config import BOT_TOKEN
from conversational_ai import generate_response
from analysis_engine import OmnixPremiumAnalysisEngine
from database import setup_premium_database, save_analysis_to_db
from quantum_engine import QuantumEngine
from pqc_encryption import generate_dilithium_signature
from voice_signature import validate_voice_biometrics

# --- INICIALIZACIÓN PRINCIPAL ---
application = Application.builder().token(BOT_TOKEN).build()
engine = OmnixPremiumAnalysisEngine()
qe = QuantumEngine()
setup_premium_database()

# --- FUNCIONES AUXILIARES ---
def reply_with_voice(text: str, lang: str = "es") -> InputFile:
    tts = gTTS(text, lang=lang)
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp.name)
    return InputFile(open(temp.name, "rb"), filename="omni_voice.mp3")

def detect_lang(text: str) -> str:
    try:
        return detect(text)
    except:
        return "es"

# --- HANDLER: /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = detect_lang(update.message.text or "")
    text = "¡Hola! Soy OMNIX, tu asistente de trading con inteligencia cuántica. ¿En qué puedo ayudarte hoy?"
    voice = reply_with_voice(text, lang)
    await update.message.reply_voice(voice, caption=text)

# --- HANDLER: /estado ---
async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = detect_lang(update.message.text or "")
    text = "✅ OMNIX está operativo con funciones premium activas: análisis, trading, voz, y seguridad cuántica."
    voice = reply_with_voice(text, lang)
    await update.message.reply_voice(voice, caption=text)

# --- HANDLER: /analyze [SYMBOL] ---
async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = context.args[0] if context.args else "BTC-USD"
        result = await engine.analyze_asset(symbol)
        text = (
            f"📊 Análisis de {symbol}\n"
            f"Precio actual: ${result['price']:.2f}\n"
            f"Tendencia: {result['trend']}\n"
            f"Recomendación: {result['recommendation']}"
        )
        lang = detect_lang(text)
        voice = reply_with_voice(text, lang)
        await update.message.reply_voice(voice, caption=text)
    except Exception as e:
        await update.message.reply_text(f"❌ Error en análisis: {e}")

# --- HANDLER: /trading [SYMBOL] [ACTION] [AMOUNT] ---
async def trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 3:
            await update.message.reply_text("Uso: /trading SYMBOL buy/sell AMOUNT")
            return
        symbol, action, amount = args[0], args[1].lower(), float(args[2])
        result = engine.execute_trade(symbol, action, amount)
        text = (
            f"🟢 Operación realizada:\n"
            f"{action.upper()} {amount} de {symbol}\n"
            f"Precio de ejecución: ${result['price']:.2f}\n"
            f"Total: ${result['total']:.2f}"
        )
        voice = reply_with_voice(text)
        await update.message.reply_voice(voice, caption=text)
    except Exception as e:
        await update.message.reply_text(f"❌ Error en trading: {e}")
# --- HANDLER: /voz_firma ---
async def voz_firma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        sample_voice = "voz_referencia.mp3"
        signature = generate_dilithium_signature(sample_voice)
        is_valid = validate_voice_biometrics(user_id, sample_voice)

        if is_valid:
            msg = "🔐 Identidad verificada y firma cuántica generada correctamente."
        else:
            msg = "⚠️ Firma de voz no válida. Intenta de nuevo."

        voice = reply_with_voice(msg)
        await update.message.reply_voice(voice, caption=msg)
    except Exception as e:
        await update.message.reply_text(f"❌ Error en voz_firma: {e}")

# --- HANDLER: /quantum_predict [SYMBOL] ---
async def quantum_predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = context.args[0] if context.args else "BTC-USD"
        prices = await engine.get_prices_series(symbol, period="180d")
        qp = qe.quantum_predict(prices)

        text = (
            f"🔮 Quantum Predict — {symbol}\n"
            f"Next price (median): ${qp.next_price:.2f}\n"
            f"Mean return: {qp.mean_return:.4%}\n"
            f"P50: {qp.p50:.4%} | P90: {qp.p90:.4%}\n"
            f"VaR 95%: {qp.var_95:.4%}"
        )
        voice = reply_with_voice(text)
        await update.message.reply_voice(voice, caption=text)

        fig, ax = plt.subplots()
        ax.hist(qp.scenarios, bins=60)
        ax.set_title(f"Distribución de precios simulados — {symbol}")
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=160)
        buf.seek(0)
        await update.message.reply_photo(buf)
        plt.close(fig)

    except Exception as e:
        await update.message.reply_text(f"❌ Error en quantum_predict: {e}")

# --- HANDLER: /quantum_portfolio SYMBOL1 SYMBOL2 ... ---
async def quantum_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        tickers = context.args if context.args else ["BTC-USD", "ETH-USD", "SOL-USD"]
        price_df = await engine.get_prices_df(tickers, period="180d")
        res = qe.quantum_optimize_portfolio(price_df)

        weights_txt = "\n".join([f"- {k}: {v:.2%}" for k, v in res.weights.items()])
        text = (
            f"🧠 Quantum Portfolio Optimizer\n"
            f"{weights_txt}\n\n"
            f"Exp Return: {res.exp_return:.2%} | Risk: {res.exp_risk:.2%} | Sharpe: {res.sharpe:.2f}"
        )
        voice = reply_with_voice(text)
        await update.message.reply_voice(voice, caption=text)

    except Exception as e:
        await update.message.reply_text(f"❌ Error en quantum_portfolio: {e}")

# --- HANDLER: Mensajes normales (GPT) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    lang = detect_lang(user_input)
    response = generate_response(user_input)
    voice = reply_with_voice(response, lang)
    await update.message.reply_voice(voice, caption=response)

# --- REGISTRO DE HANDLERS ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("estado", estado))
application.add_handler(CommandHandler("analyze", analyze))
application.add_handler(CommandHandler("trading", trading))
application.add_handler(CommandHandler("voz_firma", voz_firma))
application.add_handler(CommandHandler("quantum_predict", quantum_predict))
application.add_handler(CommandHandler("quantum_portfolio", quantum_portfolio))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- EJECUCIÓN ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    application.run_polling()
