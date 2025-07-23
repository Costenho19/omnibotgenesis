# L01 ---------------- IMPORTS ----------------
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# OMNIX Módulos Propios
from config import BOT_TOKEN
from conversational_ai import ConversationalAI
from analysis_engine import OmnixPremiumAnalysisEngine
from trading_system import KrakenTradingSystem
from database import save_analysis_to_db

# L13 --------------- INSTANCIAS --------------
ai = ConversationalAI()
analyzer = OmnixPremiumAnalysisEngine()
trader = KrakenTradingSystem()

# L17 --------------- LOGGING -----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# L23 --------------- HANDLERS ----------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"/start de {user.name}")
    await update.message.reply_html(
        f"🤖 ¡Hola {user.mention_html()}! Soy OMNIX, tu asistente crypto cuadrilingüe. Usa /estado para diagnóstico o /trading para comenzar."
    )

async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = (
        "✅ OMNIX está operativo\n"
        f"• IA: Gemini ✅\n"
        f"• Kraken: activo ✅\n"
        f"• DB: conectada ✅\n"
        "Comandos: /start, /estado, /trading, /analyze\n"
        "💬 También puedes hablarme libremente."
    )
    await update.message.reply_text(msg)

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info("Análisis solicitado")
        result = analyzer.analyze_assets()
        await update.message.reply_text(result.summary)
        save_analysis_to_db(result)  # Guarda en la DB
    except Exception as e:
        logger.error(f"Error en /analyze: {e}")
        await update.message.reply_text("❌ Error al analizar el mercado.")

async def trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        logger.info("Trading solicitado")
        res = trader.execute_strategy()
        await update.message.reply_text(f"📈 {res}")
    except Exception as e:
        logger.error(f"Error en /trading: {e}")
        await update.message.reply_text("❌ No se pudo ejecutar trading.")

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = " ".join(context.args)
    if not user_input:
        await update.message.reply_text("Escribe algo después de /ask.")
        return
    logger.info(f"Pregunta: {user_input}")
    response_text, response_voice = ai.get_response(user_input)
    await update.message.reply_text(response_text)
    if response_voice:
        await update.message.reply_voice(voice=response_voice)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = update.message.text
    logger.info(f"Texto libre: {user_input}")
    response_text, response_voice = ai.get_response(user_input)
    await update.message.reply_text(response_text)
    if response_voice:
        await update.message.reply_voice(voice=response_voice)

# L84 ---------------- MAIN -------------------
async def main():
    logger.info("Iniciando OMNIX Bot...")
    if not BOT_TOKEN:
        logger.critical("FATAL: BOT_TOKEN no encontrado.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Comandos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("estado", estado_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("trading", trading_command))
    application.add_handler(CommandHandler("ask", ask_command))

    # Texto libre
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    logger.info("OMNIX activo 🚀")
    await application.run_polling()

#  ---------------- RUN -------------------
 if __name__ == "__main__":
     import nest_asyncio
     import asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())

