# -*- coding: utf-8 -*-
import os
import asyncio
import logging
import json
import tempfile
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask
from threading import Thread
from functools import partial

from config import BOT_TOKEN
from conversational_ai import generate_response
from voice_engine import generar_audio
from database import save_analysis_to_db, get_user_memory
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
app = Flask(__name__)

@app.route('/')
def home():
    return 'OMNIX Running - Quantum Secure'

@app.route('/premium_panel')
def panel():
    return 'Panel Premium OK ✅'

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# ========== PERSISTENCIA PREMIUM ==========
PREMIUM_FILE = "premium_users.json"

if os.path.exists(PREMIUM_FILE):
    with open(PREMIUM_FILE, 'r') as f:
        premium_users = set(json.load(f))
else:
    premium_users = set()

def guardar_premium():
    with open(PREMIUM_FILE, 'w') as f:
        json.dump(list(premium_users), f)

def solo_premium(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.message.from_user.id)
        if user_id not in premium_users:
            await update.message.reply_text("⚠️ Esta función es solo para usuarios premium. Contacta al soporte para más información.")
            return
        return await func(update, context)
    return wrapper

# ========== IA COMANDOS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    botones = [["/analyze BTC", "/trading BTC"], ["/voz_firma", "/estado"], ["/sharia_check BTC", "/quantum_predict"]]
    markup = ReplyKeyboardMarkup(botones, resize_keyboard=True)
    mensaje = "Hola, soy OMNIX V4.0 \U0001F680\nIA + Trading + Seguridad Cuántica"
    await update.message.reply_text(mensaje, reply_markup=markup)
    audio = generar_audio(mensaje, lang='es', voice_id='elevenlabs_male')
    if audio:
        await update.message.reply_voice(voice=open(audio, 'rb'))
        os.remove(audio)

@solo_premium
async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    crypto = context.args[0].upper() if context.args else "BTC"
    try:
        loop = asyncio.get_running_loop()
        resultado = await loop.run_in_executor(None, partial(generar_analisis_completo, crypto))
        img = generar_grafico_btc()
        await update.message.reply_photo(photo=open(img, 'rb'))
        os.remove(img)
        await update.message.reply_text(resultado)
        audio = generar_audio(resultado, lang='es', voice_id='elevenlabs_male')
        if audio:
            await update.message.reply_voice(voice=open(audio, 'rb'))
            os.remove(audio)
    except Exception as e:
        logger.error(f"Error en analyze: {e}")
        await update.message.reply_text("❌ Error al generar análisis. Intenta de nuevo más tarde.")

@solo_premium
async def trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    crypto = context.args[0].upper() if context.args else "BTC"
    try:
        loop = asyncio.get_running_loop()
        resultado = await loop.run_in_executor(None, partial(ejecutar_trade, "buy", crypto))
        await update.message.reply_text(resultado)
        audio = generar_audio(resultado, lang='es', voice_id='elevenlabs_male')
        if audio:
            await update.message.reply_voice(voice=open(audio, 'rb'))
            os.remove(audio)
    except Exception as e:
        logger.error(f"Error en trading: {e}")
        await update.message.reply_text("❌ Error al ejecutar operación de trading.")

@solo_premium
async def voz_firma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Procesando firma de voz cuántica...")
    try:
        resultado = procesar_firma_biometrica(update)
        firma_cifrada = cifrar_con_dilithium(resultado)
        mensaje = "Firma registrada y cifrada correctamente."
        await update.message.reply_text(mensaje)
        audio = generar_audio(mensaje, lang='es', voice_id='elevenlabs_male')
        if audio:
            await update.message.reply_voice(voice=open(audio, 'rb'))
            os.remove(audio)
    except Exception as e:
        logger.error(f"Error en voz_firma: {e}")
        await update.message.reply_text("❌ Error al procesar firma biométrica.")

@solo_premium
async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resumen = "Sistema OMNIX activo ✅\nTrading: OK\nIA: GPT-4o\nVoz: ElevenLabs\nQuantum Shield: ON"
    await update.message.reply_text(resumen)
    audio = generar_audio(resumen, lang='es', voice_id='elevenlabs_male')
    if audio:
        await update.message.reply_voice(voice=open(audio, 'rb'))
        os.remove(audio)

@solo_premium
async def quantum_predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pred = montecarlo_predict("BTC")
        await update.message.reply_text(pred)
        audio = generar_audio(pred, lang='es', voice_id='elevenlabs_male')
        if audio:
            await update.message.reply_voice(voice=open(audio, 'rb'))
            os.remove(audio)
    except Exception as e:
        logger.error(f"Error en quantum_predict: {e}")
        await update.message.reply_text("❌ Error en predicción cuántica.")

@solo_premium
async def sharia_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    crypto = context.args[0].upper() if context.args else "BTC"
    try:
        resultado = validar_sharia(crypto)
        await update.message.reply_text(resultado)
        audio = generar_audio(resultado, lang='es', voice_id='elevenlabs_male')
        if audio:
            await update.message.reply_voice(voice=open(audio, 'rb'))
            os.remove(audio)
    except Exception as e:
        logger.error(f"Error en sharia_check: {e}")
        await update.message.reply_text("❌ Error en validación halal.")

@solo_premium
async def quantum_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        resultado = quantum_portfolio_analysis()
        await update.message.reply_text(resultado)
        audio = generar_audio(resultado, lang='es', voice_id='elevenlabs_male')
        if audio:
            await update.message.reply_voice(voice=open(audio, 'rb'))
            os.remove(audio)
    except Exception as e:
        logger.error(f"Error en quantum_portfolio: {e}")
        await update.message.reply_text("❌ Error al generar portafolio cuántico.")

# ========== MANEJO DE MENSAJES ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    texto_usuario = update.message.text
    try:
        respuesta = generate_response(user_id, texto_usuario)
        await update.message.reply_text(respuesta)
        audio = generar_audio(respuesta, lang='es', voice_id='elevenlabs_male')
        if audio:
            await update.message.reply_voice(voice=open(audio, 'rb'))
            os.remove(audio)
    except Exception as e:
        logger.error(f"Error en handle_message: {e}")
        await update.message.reply_text("❌ Error al procesar tu mensaje.")

# ========== MAIN ==========
if __name__ == '__main__':
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("trading", trading))
    app.add_handler(CommandHandler("voz_firma", voz_firma))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(CommandHandler("quantum_predict", quantum_predict))
    app.add_handler(CommandHandler("sharia_check", sharia_check))
    app.add_handler(CommandHandler("quantum_portfolio", quantum_portfolio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get('PORT', 8443)),
        url_path=BOT_TOKEN,
        webhook_url=os.environ.get("WEBHOOK_URL") + BOT_TOKEN
    )
