# L01 ---------------- IMPORTS ----------------
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)
from config import BOT_TOKEN
from conversational_ai import ConversationalAI
from analysis_engine import OmnixPremiumAnalysisEngine
from trading_system import KrakenTradingSystem
from database import setup_premium_database

# L15 --------------- INSTANCIAS ---------------
ai_engine = ConversationalAI()
analysis_engine = OmnixPremiumAnalysisEngine()
trading_engine = KrakenTradingSystem()

# L20 ---------------- LOGGING -----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# L27 --------------- COMANDOS -----------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🤖 OMNIX está activo. Usa /estado para más detalles.")

async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("✅ Bot activo y escuchando. Todo en orden.")

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await update.message.reply_text("📊 Analizando mercado...")
    result = await analysis_engine.analyze_assets()
    await msg.edit_text(f"✅ Análisis completado:\n{result}")

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = update.message.text.replace("/ask", "").strip()
    if not user_input:
        await update.message.reply_text("❗ Por favor escribe una pregunta después de /ask.")
        return
    reply_text, voice_path = await ai_engine.get_response(user_input, update.effective_user.id)
    await update.message.reply_text(reply_text)
    if voice_path:
        await update.message.reply_voice(voice=open(voice_path, "rb"))

async def trading_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("💸 Ejecutando estrategia de trading...")
    result = trading_engine.execute_strategy()
    await update.message.reply_text(f"✅ Resultado:\n{result}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🔄 Usa comandos como /analyze o /trading.")

# L70 ---------------- MAIN --------------------

async def main():
    logger.info("Iniciando OMNIX Bot...")
    setup_premium_database()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("estado", estado_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(CommandHandler("ask", ask_command))
    application.add_handler(CommandHandler("trading", trading_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    logger.info("Bot escuchando...")
    await application.run_polling()

# L85 ---------------- RUN ---------------------
if __name__ == "__main__":
    asyncio.run(main())
