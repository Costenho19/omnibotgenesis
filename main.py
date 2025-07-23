# L01 ---------------- IMPORTS ----------------
import logging
import asyncio
import os
import psycopg2  # test rápido de DB
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    MessageHandler, filters
)

# L12 --------------- ENV VARS ----------------
from config import BOT_TOKEN, DATABASE_URL

# L15 --------------- LOGGING -----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# L22 --------------- HELPER DB ---------------
def check_db():
    """Devuelve (ok: bool, msg: str) sobre el estado de la DB."""
    if not DATABASE_URL:
        return False, "DATABASE_URL no está definida."
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=5)
        conn.close()
        return True, "Conexión OK ✅"
    except Exception as e:
        return False, f"Error al conectar: {e}"

# L33 --------------- HANDLERS ----------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"/start de {user.name}")
    await update.message.reply_html(
        f"¡Hola {user.mention_html()}! OMNIX está vivo (modo diagnóstico). Usa /estado."
    )

async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db_ok, db_msg = check_db()
    msg = (
        "🟢 Bot activo (polling)\n"
        f"🔐 BOT_TOKEN cargado: {'Sí' if BOT_TOKEN else 'No'}\n"
        f"🗄️ DB: {db_msg}\n"
        "Comandos activos: /start, /estado\n"
        "Próximos: /analyze, /trading, botones, voz..."
    )
    await update.message.reply_text(msg)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    txt = update.message.text
    logger.info(f"Echo de {update.effective_user.name}: {txt}")
    await update.message.reply_text("Recibido ✅ (modo diagnóstico). Usa /estado o /start.")

# L55 ----------------- MAIN -------------------
async def main() -> None:
    logger.info("🚀 Iniciando OMNIX Bot (Diagnóstico V2)...")

    if not BOT_TOKEN:
        logger.critical("FATAL: BOT_TOKEN no encontrado.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers básicos
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("estado", estado_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Limpia webhook por si acaso
    await application.bot.delete_webhook()
    await application.initialize()
[L71] logger.info("🔄 Iniciando POLLING...")
[L72] await application.run_polling()

  

# L78 ----------------- RUN --------------------
if __name__ == "__main__":
    asyncio.run(main())
