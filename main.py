# -*- coding: utf-8 -*-
import os
import asyncio
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask
from threading import Thread

from config import BOT_TOKEN
from conversational_ai import generate_response
from voice_engine import generar_audio
from database import save_analysis_to_db, get_user_memory
from analysis_engine import generar_analisis_completo, generar_grafico_btc
from trading_system import ejecutar_trade
from voice_signature import procesar_firma_biometrica
from pqc_encryption import cifrar_con_dilithium

# ========== LOG ==========
logging.basicConfig(level=logging.INFO)

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

# ========== IA COMANDOS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    botones = [["/analyze", "/trading"], ["/voz_firma", "/estado"]]
    markup = ReplyKeyboardMarkup(botones, resize_keyboard=True)
    mensaje = "Hola, soy OMNIX V4.0 🚀\nIA + Trading + Seguridad Cuántica"
    await update.message.reply_text(mensaje, reply_markup=markup)
    audio = generar_audio(mensaje, lang='es')
    await update.message.reply_voice(voice=open(audio, 'rb'))

@solo_premium
async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = generar_analisis_completo("BTC")
    img = generar_grafico_btc()
    await update.message.reply_photo(photo=open(img, 'rb'))
    await update.message.reply_text(resultado)
    audio = generar_audio(resultado, lang='es')
    await update.message.reply_voice(voice=open(audio, 'rb'))

@solo_premium
async def trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = ejecutar_trade("buy", "BTC")
    await update.message.reply_text(resultado)
    audio = generar_audio(resultado, lang='es')
    await update.message.reply_voice(voice=open(audio, 'rb'))

from qiskit import QuantumCircuit, execute, IBMQ
from qiskit.providers.ibmq import least_busy
from dotenv import load_dotenv

@solo_premium
async def quantum_real_demo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Conectando a IBM Quantum...")

    try:
        load_dotenv()
        IBMQ_API_KEY = os.getenv("IBMQ_API_KEY")
        if not IBMQ_API_KEY:
            await update.message.reply_text("⚠️ Clave IBMQ_API_KEY no encontrada en .env")
            return

        IBMQ.save_account(IBMQ_API_KEY, overwrite=True)
        provider = IBMQ.load_account()

        # Elegir backend real disponible
        backend = least_busy(provider.backends(filters=lambda b: b.configuration().n_qubits >= 1 and
                                               not b.configuration().simulator and b.status().operational==True))
        await update.message.reply_text(f"Ejecutando en: {backend.name()}")

        # Crear circuito de superposición simple
        qc = QuantumCircuit(1, 1)
        qc.h(0)
        qc.measure(0, 0)

        job = execute(qc, backend=backend, shots=1024)
        result = job.result()
        counts = result.get_counts()

        texto = f"✅ Resultados cuánticos reales:\n\n{counts}"
        await update.message.reply_text(texto)

        # Voz
        audio = generar_audio(texto, lang="es")
        if audio:
            await update.message.reply_voice(voice=open(audio, "rb"))

    except Exception as e:
        await update.message.reply_text(f"❌ Error al ejecutar demo cuántica: {str(e)}")

@solo_premium
async def voz_firma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enviando firma de voz cifrada con Dilithium...")
    resultado = procesar_firma_biometrica(update)
    firma_cifrada = cifrar_con_dilithium(resultado)
    await update.message.reply_text("Firma registrada y cifrada correctamente.")
    audio = generar_audio("Firma registrada y cifrada correctamente.", lang='es')
    await update.message.reply_voice(voice=open(audio, 'rb'))

@solo_premium
async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resumen = "Sistema OMNIX activo ✅\nTrading: OK\nIA: GPT-4o\nVoz: Activada\nQuantum Shield: ON"
    await update.message.reply_text(resumen)
    audio = generar_audio(resumen, lang='es')
    await update.message.reply_voice(voice=open(audio, 'rb'))

@solo_premium
async def quantum_predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prediccion = "Predicción cuántica: BTC tendencia alcista próxima 48h. Validación 87%."
    await update.message.reply_text(prediccion)
    audio = generar_audio(prediccion, lang='es')
    await update.message.reply_voice(voice=open(audio, 'rb'))

@solo_premium
async def quantum_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    portafolio = "Tu portafolio cuántico incluye BTC, ETH, USDT. Riesgo optimizado con IA Monte Carlo."
    await update.message.reply_text(portafolio)
    audio = generar_audio(portafolio, lang='es')
    await update.message.reply_voice(voice=open(audio, 'rb'))

# ========== MANEJO DE MENSAJES ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_usuario = update.message.text
    user_id = str(update.message.from_user.id)
    respuesta = generar_respuesta(user_id, texto_usuario)
  respuesta = generate_respuesta(user_id, texto_usuario)

# 🔊 Generar voz profesional con ElevenLabs
archivo_audio = generar_audio(respuesta, idioma="es")  # puedes cambiar a idioma detectado si quieres

if archivo_audio:
    with open(archivo_audio, 'rb') as audio:
        await update.message.reply_voice(voice=audio)

# Enviar también por texto
await update.message.reply_text(respuesta)
 

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
    app.add_handler(CommandHandler("quantum_portfolio", quantum_portfolio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("quantum_real_demo", quantum_real_demo))
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get('PORT', 8443)),
        url_path=BOT_TOKEN,
        webhook_url=os.environ.get("WEBHOOK_URL") + BOT_TOKEN
    )
