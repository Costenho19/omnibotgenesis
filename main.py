# ==============================================================================
# === OMNIX V3.8 PRO SHIELDED - RAILWAY PRODUCTION (main.py) ===
# ==============================================================================
# Arquitectura Webhook-First, modular y optimizada para producción.

# --- SECCIÓN 1: IMPORTACIONES ---
import logging
import asyncio
import os
import threading
import nest_asyncio
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes 

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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Aplicación Web Flask (Panel de Estado) ---
app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    """Endpoint principal para verificar que el servidor está vivo."""
    return '🧠 OMNIX V3.8 PRO SHIELDED - Quantum Ready & Actively Running'

def run_flask_in_thread():
    """Ejecuta la aplicación Flask en un hilo separado para no bloquear el bot."""
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=port)

# --- SECCIÓN 3: HANDLERS DE COMANDOS DE TELEGRAM ---
# Cada función maneja un comando específico del bot.

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bienvenido a OMNIX.\n\nEstoy operativo con IA cuántica, voz humana y seguridad post-cuántica.")

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await generar_analisis_completo(update, context)

async def trading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ejecutar_trade(update, context)

async def voz_firma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await procesar_firma_biometrica(update, context)

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🟢 OMNIX está activo y funcionando al 100%")

async def quantum_predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await montecarlo_predict(update, context)

async def quantum_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await quantum_portfolio_analysis(update, context)

async def sharia_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await validar_sharia(update, context)

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = await consultar_wallet() # Asumiendo que es una función asíncrona
    await update.message.reply_text(resultado, parse_mode="Markdown")

async def sugerencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = " ".join(context.args)
    if texto:
        # Asumiendo que guardar_sugerencia es una función síncrona
        await asyncio.to_thread(guardar_sugerencia, update.effective_user.id, texto)
        await update.message.reply_text("💡 ¡Gracias por tu sugerencia! Ha sido registrada.")
    else:
        await update.message.reply_text("Por favor, escribe tu sugerencia después del comando. Ejemplo: /sugerencia mejorar el análisis")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para mensajes de texto que no son comandos."""
    await generate_response(update, context)

# --- SECCIÓN 4: FUNCIÓN PRINCIPAL DE ARRANQUE ---

async def main():
    """Configura y arranca el bot de Telegram en modo Webhook."""
    # Verificación crítica de las variables de entorno.
    if not BOT_TOKEN or not WEBHOOK_URL:
        logger.critical("❌ FATAL: BOT_TOKEN o WEBHOOK_URL no están configurados en el entorno.")
        # Usamos os._exit(1) para terminar el proceso de forma segura en un entorno asíncrono.
        os._exit(1)
        
    # Inicia el servidor Flask en un hilo separado.
    flask_thread = threading.Thread(target=run_flask_in_thread, daemon=True)

    flask_thread.start()
    logger.info("🌐 Servidor web Flask iniciado en un hilo paralelo.")
    
    # Construimos la aplicación del bot.
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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # --- Configuración del Webhook ---
    # Esta es la configuración estándar y más robusta para producción.
    # El 'url_path' se usa para que el webhook sea más difícil de encontrar por bots maliciosos.
    # El puerto lo toma de la variable de entorno 'PORT' que asigna Railway.
    port = int(os.environ.get("PORT", 8443))
    logger.info(f"Iniciando Webhook en el puerto {port}...")
    await application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )
    logger.info("✅ OMNIX V3.8 PRO SHIELDED está en línea y escuchando peticiones.")

# === SECCIÓN 5: PUNTO DE ENTRADA DEL PROGRAMA ===
if __name__ == "__main__":
    import nest_asyncio
    import asyncio

    logger.info("🚀 Iniciando OMNIX...")

   try:
        nest_asyncio.apply()
        app = Application.builder().token(BOT_TOKEN).build()

        # --- Comando de prueba (/start) ---
        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text("✅ OMNIX está en línea y responde correctamente.")

        app.add_handler(CommandHandler("start", start))

        # --- Activar la respuesta de IA conversacional ---
        from conversational_ai import generate_response

        async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
            text = update.message.text
            respuesta = generate_response(update.effective_user.id, text)
            await update.message.reply_text(respuesta)

        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))

        # --- Ejecutar Webhook ---
                app.run_webhook(
                    listen="0.0.0.0",
                    port=8445,
        webhook_url=WEBHOOK_URL,
                )

    except Exception as e:
        logger.critical(f"❌ Error al iniciar OMNIX:\n{e}")
