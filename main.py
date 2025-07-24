import logging
import asyncio
import os
import psycopg2
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Importa nuestras clases, funciones y configuración desde los otros archivos
from config import BOT_TOKEN, DATABASE_URL, GEMINI_API_KEY, KRAKEN_API_KEY
from database import setup_premium_database, add_premium_assets
from analysis_engine import OmnixPremiumAnalysisEngine, premium_assets_list
from conversational_ai import ConversationalAI
from trading_system import KrakenTradingSystem

# Configuración del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Instanciamos nuestros sistemas ---
analysis_engine = OmnixPremiumAnalysisEngine()
conversational_ai = ConversationalAI()
trading_system = KrakenTradingSystem()

# --- Definición de los Comandos del Bot ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envía un mensaje de bienvenida."""
    user = update.effective_user
    await update.message.reply_html(
        f"¡Hola {user.mention_html()}! Soy OMNIX, tu asistente de trading. Usa /analyze <SÍMBOLO> para empezar.",
    )

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Realiza un análisis de un activo."""
    if not context.args:
        await update.message.reply_text("Uso: /analyze <SÍMBOLO>")
        return

    symbol = context.args[0].upper()
    await update.message.reply_text(f"Analizando {symbol}, por favor espera...")
    loop = asyncio.get_running_loop()
    try:
        analysis_result = await loop.run_in_executor(
            None, analysis_engine.analyze_with_ai, symbol
        )
        if analysis_result:
            message = f"""
📈 *Análisis para {analysis_result.symbol}*

*Precio Actual:* ${analysis_result.current_price:,.2f}
*Recomendación:* *{analysis_result.recommendation}*
*Confianza:* {analysis_result.confidence:.0%}
*Riesgo:* {analysis_result.risk_score:.0%}

*Predicciones (Simuladas):*
  - 1h: ${analysis_result.prediction_1h:,.2f}
  - 24h: ${analysis_result.prediction_24h:,.2f}
  - 7d: ${analysis_result.prediction_7d:,.2f}
            """
            await update.message.reply_markdown(message)
        else:
            await update.message.reply_text(f"Lo siento, no pude obtener datos para {symbol}.")
    except Exception as e:
        logger.error(f"Error durante el análisis para {symbol}: {e}")
        await update.message.reply_text("Ocurrió un error inesperado durante el análisis.")

voice_fp = self.text_to_speech(ai_text, lang='es')  # puedes usar lang='en' si prefieres
return {"text": ai_text, "voice": voice_fp}

async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra el estado actual del sistema."""
    ia_ok = "✅" if analysis_engine else "❌"
    gemini_ok = "✅" if GEMINI_API_KEY else "❌"
    kraken_ok = "✅" if KRAKEN_API_KEY else "❌"
    
    conn_ok = "❌"
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn_ok = "✅"
        conn.close()
    except Exception as e:
        logger.error(f"Error de conexión a la BD para /estado: {e}")

    msg = (
        "*📡 Estado del Sistema OMNIX:*\n\n"
        f"*🧠 IA:* {ia_ok}\n"
        f"*🗄️ Base de Datos:* {conn_ok}\n"
        f"*🔐 API Gemini:* {gemini_ok}\n"
        f"*🔐 API Kraken:* {kraken_ok}"
    )
    await update.message.reply_markdown(msg)

async def trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ejecuta una orden de trading con validación mejorada."""
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Uso: /trading <BUY/SELL> <cantidad>")
            return
  
        side = args[0].upper()
        # MEJORA 1: Validación de entrada explícita
        if side not in ["BUY", "SELL"]:
            await update.message.reply_text("Orden inválida. El primer argumento debe ser BUY o SELL.")
            return

        amount = float(args[1])
        
        result = trading_system.place_market_order(pair="XXBTZUSD", order_type=side.lower(), volume=amount)

        # MEJORA 2: Control de errores mejorado
        if not result or result.get("error"):
            error_message = result.get('error', 'Respuesta desconocida del exchange.') if result else 'No se recibió respuesta del exchange.'
            await update.message.reply_text(f"Error al ejecutar orden: {error_message}")
        else:
            await update.message.reply_text(f"✅ Orden ejecutada:\n{result}")
    except ValueError:
        await update.message.reply_text("❌ Error: La cantidad debe ser un número.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error inesperado en el comando: {str(e)}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:



async def main() -> None:
    """Función principal que arranca todo."""
    logger.info("🚀 Iniciando OMNIX Bot...")
    
    if not BOT_TOKEN or not DATABASE_URL:
        logger.critical("FATAL: Faltan BOT_TOKEN o DATABASE_URL. El bot no puede iniciar.")
        return

    setup_premium_database()
    add_premium_assets(premium_assets_list)

    application = Application.builder().token(BOT_TOKEN).build()

    # Añadimos los manejadores de comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("ask", ask_command))
    application.add_handler(CommandHandler("estado", estado_command))
    application.add_handler(CommandHandler("trading", trading_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    logger.info("Limpiando cualquier sesión antigua de Telegram...")
    

    logger.info("Inicializando la aplicación...")
    await application.initialize()
    logger.info("✅ Bot listo, iniciando la escucha de peticiones...")
    await application.run_polling()

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_message = " ".join(context.args)

    if not user_message:
        await update.message.reply_text("❗️Por favor, escribe tu pregunta después del comando /ask.")
        return

    try:
        result = ai.generate_response(user_id, user_message)
        ai_text = result.get("text")
        voice_fp = result.get("voice")

        await update.message.reply_text(f"🤖 OMNIX:\n{ai_text}")

        if voice_fp:
            voice_fp.seek(0)
            await update.message.reply_voice(voice=voice_fp)
    except Exception as e:
        logger.error(f"Error en /ask: {e}")
        await update.message.reply_text("⚠️ Ocurrió un error al procesar tu pregunta.")
 if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

 



