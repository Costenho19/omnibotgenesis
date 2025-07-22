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


# Configuración del logging para ver qué hace el bot
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
    """Envía un mensaje de bienvenida cuando el comando /start es ejecutado."""
    user = update.effective_user
    await update.message.reply_html(
        f"¡Hola {user.mention_html()}! Soy OMNIX, tu asistente de trading. Usa /analyze <SÍMBOLO> para empezar.",
    )

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Realiza un análisis de un activo solicitado por el usuario."""
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

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja las preguntas de los usuarios a la IA conversacional."""
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("Uso: /ask <tu pregunta>")
        return

    question = ' '.join(context.args)
    logger.info(f"RECIBIDA PREGUNTA de {update.effective_user.name}: {question}")
    await update.message.reply_text("Pensando... 🤔", quote=True)

    loop = asyncio.get_running_loop()
    ai_response = await loop.run_in_executor(
        None, conversational_ai.get_ai_response, question, user_id
    )
    await update.message.reply_text(ai_response, quote=True)

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
    """Ejecuta una orden de trading."""
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Uso: /trading <BUY/SELL> <cantidad>")
            return
  
        side = args[0].upper()
        amount = float(args[1])
        
        result = trading_system.place_market_order(pair="XXBTZUSD", order_type=side.lower(), volume=amount)

        if result.get("error"):
            await update.message.reply_text(f"Error al ejecutar orden: {result['error']}")
        else:
            await update.message.reply_text(f"✅ Orden ejecutada:\n{result}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error en el comando: {str(e)}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responde a cualquier mensaje que no sea un comando."""
    logger.info(f"RECIBIDO MENSAJE de {update.effective_user.name}: {update.message.text}")
    await update.message.reply_text("He recibido tu mensaje. Para interactuar conmigo, usa los comandos: /start, /analyze, /ask, /estado, /trading.")

# L136
async def main() -> None:
    """Función principal que arranca todo."""
    # L139
    print(f"BOT_TOKEN: {BOT_TOKEN[:5]}...")
    print(f"DATABASE_URL: {DATABASE_URL}")

    # L143  (deja comentado este chequeo por ahora)
    # if not BOT_TOKEN or not DATABASE_URL:
    #     logger.critical("FATAL: Faltan BOT_TOKEN o DATABASE_URL. El bot no puede iniciar.")
    #     return

    # L148
    setup_premium_database()
    add_premium_assets(premium_assets_list)

    # L152
    application = Application.builder().token(BOT_TOKEN).build()

    # L155 – Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("ask", ask_command))
    application.add_handler(CommandHandler("estado", estado_command))
    application.add_handler(CommandHandler("trading", trading_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # L163
    logger.info("🧹 Limpiando cualquier sesión antigua de Telegram...")
    await application.bot.delete_webhook()

    # L166
    logger.info("⚙️ Inicializando la aplicación...")
    await application.initialize()

    # L169
    logger.info("✅ Bot listo, iniciando la escucha de peticiones...")
    await application.start()

    # L172
    await asyncio.Event().wait()

# L176
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
