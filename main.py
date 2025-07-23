import logging
import nest_asyncio
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from conversational_ai import ConversationalAI
from analysis_engine import OmnixPremiumAnalysisEngine
from trading_system import KrakenTradingSystem
from database import save_analysis_to_db

from config import BOT_TOKEN

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------ COMANDOS ------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hola, soy OMNIX 🤖. Tu asistente de trading inteligente.")

async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("✅ OMNIX está operativo y listo para ayudarte.")

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    engine = OmnixPremiumAnalysisEngine()
    result = engine.run_full_analysis("BTC-USD")
    await update.message.reply_text(f"📊 Análisis completo:\n\n{result.summary}")
    save_analysis_to_db("BTC-USD", result)

async def trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    trader = KrakenTradingSystem()
    buy_price = trader.get_price("XBTUSD")
    trader.place_order("XBTUSD", "buy", 0.001)
    await update.message.reply_text(f"🛒 Compra ejecutada de 0.001 BTC a precio {buy_price}")

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    user_id = update.effective_user.id
    ai = ConversationalAI()
    response_text, audio_file = ai.get_response(user_id, user_message)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response_text)
    if audio_file:
        with open(audio_file, 'rb') as audio:
            await context.bot.send_voice(chat_id=update.effective_chat.id, voice=audio)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user_message = update.message.text
        user_id = update.effective_user.id

        ai = ConversationalAI()
        response_text, audio_file = ai.get_response(user_id, user_message)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response_text
        )

        if audio_file:
            with open(audio_file, 'rb') as audio:
                await context.bot.send_voice(
                    chat_id=update.effective_chat.id,
                    voice=audio
                )
    except Exception as e:
        logger.error(f"Error en echo(): {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ Ocurrió un error al procesar tu mensaje."
        )

# ------------------ MAIN ------------------

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

# ------------------ RUN ------------------

if __name__ == "__main__":
    import nest_asyncio
    import asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())

