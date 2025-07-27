# ==============================================================================
# === OMNIX GLOBAL BOT V2.0 - ARCHIVO PRINCIPAL (main.py) ===
# ==============================================================================
# Arquitectura refactorizada para simplicidad, potencia y escalabilidad.

# --- SECCIÓN 1: IMPORTACIONES ---
import logging
import asyncio
import os
import io
import tempfile
import matplotlib.pyplot as plt
import yfinance as yf
from gtts import gTTS
from langdetect import detect
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# --- Módulos Internos del Proyecto ---
# Se asume que estos archivos existen en el repositorio con las clases/funciones correspondientes.
from config import BOT_TOKEN
from conversational_ai import ConversationalAI
ai = ConversationalAI()

from analysis_engine import OmnixPremiumAnalysisEngine
from database import setup_premium_database
from quantum_engine import QuantumEngine
from pqc_encryption import generate_dilithium_signature
from voice_signature import validate_voice_biometrics

# --- SECCIÓN 2: CONFIGURACIÓN INICIAL ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Instancias Globales de los Motores del Bot ---
# Se inicializan una sola vez al arrancar el bot para máxima eficiencia.
engine = OmnixPremiumAnalysisEngine()
qe = QuantumEngine()

# --- SECCIÓN 3: FUNCIONES AUXILIARES (HERRAMIENTAS) ---

def reply_with_voice(text: str, lang: str = "es") -> io.BytesIO:
    """
    Convierte un texto a voz y lo devuelve como un objeto en memoria.
    Esto evita crear y borrar archivos constantemente en el servidor.
    """
    try:
        tts = gTTS(text, lang=lang)
        voice_buffer = io.BytesIO()
        tts.write_to_fp(voice_buffer)
        voice_buffer.seek(0) # Rebobinamos el buffer para que pueda ser leído.
        return voice_buffer
    except Exception as e:
        logging.error(f"Error al generar voz para el texto '{text}': {e}")
        return None # Devolvemos None si falla la generación de voz.

def detect_lang(text: str) -> str:
    """Detecta el idioma de un texto, con 'es' como opción segura por defecto."""
    try:
        # Añadimos una comprobación para evitar errores con textos muy cortos o sin caracteres alfabéticos.
        if not text or not any(c.isalpha() for c in text):
            return "es"
        return detect(text)
    except:
        return "es"

# --- SECCIÓN 4: HANDLERS DE COMANDOS (/start, /analyze, etc.) ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para el comando /start. Envía un saludo y una respuesta de voz."""
    lang = detect_lang(update.message.text or "")
    text = "¡Hola! Soy OMNIX, tu asistente de trading con inteligencia cuántica. ¿En qué puedo ayudarte hoy?"
    
    # Usamos nuestra herramienta para generar la voz.
    voice_buffer = reply_with_voice(text, lang)
    if voice_buffer:
        await update.message.reply_voice(voice_buffer, caption=text)
    else:
        await update.message.reply_text(text)

async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para el comando /estado."""
    lang = detect_lang(update.message.text or "")
    text = "✅ OMNIX está operativo con funciones premium activas: análisis, trading, voz, y seguridad cuántica."
    
    voice_buffer = reply_with_voice(text, lang)
    if voice_buffer:
        await update.message.reply_voice(voice_buffer, caption=text)
    else:
        await update.message.reply_text(text)

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para el comando /analyze [SYMBOL]."""
    try:
        symbol = context.args[0].upper() if context.args else "BTC-USD"
        # La lógica de análisis ahora está encapsulada en la clase del motor.
        result = await engine.analyze_asset(symbol)
        
        text = (
            f"📊 Análisis de {symbol}\n"
            f"Precio actual: ${result['price']:.2f}\n"
            f"Tendencia: {result['trend']}\n"
            f"Recomendación: {result['recommendation']}"
        )
        voice_buffer = reply_with_voice(text)
        if voice_buffer:
            await update.message.reply_voice(voice_buffer, caption=text)
        else:
            await update.message.reply_text(text)
            
    except IndexError:
        await update.message.reply_text("Por favor, proporciona un símbolo. Uso: /analyze <SÍMBOLO>")
    except Exception as e:
        logging.error(f"Error en /analyze: {e}")
        await update.message.reply_text(f"❌ Error en el análisis: {e}")

async def trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para el comando /trading [SYMBOL] [ACTION] [AMOUNT]."""
    try:
        if len(context.args) < 3:
            await update.message.reply_text("Uso: /trading <SÍMBOLO> <buy/sell> <CANTIDAD>")
            return
            
        symbol, action, amount = context.args[0].upper(), context.args[1].lower(), float(context.args[2])
        
        if action not in ['buy', 'sell']:
            await update.message.reply_text("La acción debe ser 'buy' o 'sell'.")
            return
            
        result = engine.execute_trade(symbol, action, amount)
        
        text = (
            f"🟢 Operación realizada:\n"
            f"{action.upper()} {amount} de {symbol}\n"
            f"Precio de ejecución: ${result['price']:.2f}\n"
            f"Total: ${result['total']:.2f}"
        )
        voice_buffer = reply_with_voice(text)
        if voice_buffer:
            await update.message.reply_voice(voice_buffer, caption=text)
        else:
            await update.message.reply_text(text)
            
    except (IndexError, ValueError):
        await update.message.reply_text("Formato incorrecto. Uso: /trading <SÍMBOLO> <buy/sell> <CANTIDAD>")
    except Exception as e:
        logging.error(f"Error en /trading: {e}")
        await update.message.reply_text(f"❌ Error en la operación de trading: {e}")

async def voz_firma_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para el comando /voz_firma."""
    try:
        user_id = update.effective_user.id
        # NOTA: La lógica real necesitaría recibir un archivo de voz del usuario.
        # Esto es una simulación conceptual como estaba en tu código.
        sample_voice = "voz_referencia.mp3" 
        signature = generate_dilithium_signature(sample_voice)
        is_valid = validate_voice_biometrics(user_id, sample_voice)

        if is_valid:
            msg = "🔐 Identidad verificada y firma cuántica generada correctamente."
        else:
            msg = "⚠️ Firma de voz no válida. Intenta de nuevo."

        voice_buffer = reply_with_voice(msg)
        if voice_buffer:
            await update.message.reply_voice(voice_buffer, caption=msg)
        else:
            await update.message.reply_text(msg)
            
    except Exception as e:
        logging.error(f"Error en /voz_firma: {e}")
        await update.message.reply_text(f"❌ Error en la firma por voz: {e}")

async def quantum_predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para el comando /quantum_predict [SYMBOL]."""
    try:
        symbol = context.args[0].upper() if context.args else "BTC-USD"
        prices = await engine.get_prices_series(symbol, period="180d")
        qp = qe.quantum_predict(prices)

        text = (
            f"🔮 Predicción Cuántica — {symbol}\n"
            f"Próximo precio (mediana): ${qp.next_price:.2f}\n"
            f"Retorno esperado: {qp.mean_return:.4%}\n"
            f"VaR 95%: {qp.var_95:.4%}"
        )
        voice_buffer = reply_with_voice(text)
        if voice_buffer:
            await update.message.reply_voice(voice_buffer, caption=text)
        else:
            await update.message.reply_text(text)

        # Generación del gráfico de distribución
        fig, ax = plt.subplots(); ax.hist(qp.scenarios, bins=60)
        ax.set_title(f"Distribución de precios simulados — {symbol}")
        buf = io.BytesIO(); plt.savefig(buf, format="png", dpi=160); buf.seek(0)
        await update.message.reply_photo(buf); plt.close(fig)

    except Exception as e:
        logging.error(f"Error en /quantum_predict: {e}")
        await update.message.reply_text(f"❌ Error en la predicción cuántica: {e}")

async def quantum_portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para el comando /quantum_portfolio [SYMBOLS...]."""
    try:
        tickers = context.args if context.args else ["BTC-USD", "ETH-USD", "SOL-USD"]
        price_df = await engine.get_prices_df(tickers, period="180d")
        res = qe.quantum_optimize_portfolio(price_df)

        weights_txt = "\n".join([f"- {k}: {v:.2%}" for k, v in res.weights.items()])
        text = (
            f"🧠 Optimizador Cuántico de Portafolio\n\n"
            f"{weights_txt}\n\n"
            f"Retorno Esperado: {res.exp_return:.2%} | Riesgo: {res.exp_risk:.2%} | Sharpe: {res.sharpe:.2f}"
        )
        voice_buffer = reply_with_voice(text)
        if voice_buffer:
            await update.message.reply_voice(voice_buffer, caption=text)
        else:
            await update.message.reply_text(text)

    except Exception as e:
        logging.error(f"Error en /quantum_portfolio: {e}")
        await update.message.reply_text(f"❌ Error en la optimización cuántica: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para cualquier mensaje de texto que no sea un comando."""
    user_input = update.message.text
    lang = detect_lang(user_input)
    
    # La lógica de IA conversacional ahora está encapsulada en su propia clase/función.
    response = generate_response(user_input)
    
    voice_buffer = reply_with_voice(response, lang)
    if voice_buffer:
        await update.message.reply_voice(voice_buffer, caption=response)
    else:
        await update.message.reply_text(response)

# --- SECCIÓN 5: FUNCIÓN PRINCIPAL DE ARRANQUE ---

async def main() -> None:
    """Función principal que configura y arranca el bot."""
    # Verificación crítica del BOT_TOKEN antes de hacer nada más.
    if not BOT_TOKEN:
        logging.critical("FATAL: BOT_TOKEN no encontrado en las variables de entorno. El bot no puede arrancar.")
        return

    # Inicializamos la base de datos una sola vez.
    setup_premium_database()

    # Creamos la aplicación del bot.
    application = Application.builder().token(BOT_TOKEN).build()

    # --- Registro de Handlers ---
    # Asociamos cada comando a su función correspondiente.
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("estado", estado_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("trading", trading_command))
    application.add_handler(CommandHandler("voz_firma", voz_firma_command))
    application.add_handler(CommandHandler("quantum_predict", quantum_predict_command))
    application.add_handler(CommandHandler("quantum_portfolio", quantum_portfolio_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logging.info("🚀 Iniciando OMNIX Bot V2.0...")
    # Usamos run_polling() que es un "todo en uno" que maneja el ciclo de vida por nosotros.
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logging.critical(f"!!!!!!!!!! ERROR FATAL AL INICIAR EL BOT !!!!!!!!!!!\n{e}")
