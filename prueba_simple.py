import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("!!! COMANDO /start RECIBIDO !!!")
    await update.message.reply_text("¡Funciona! El bot de prueba está vivo.")

print("--- SCRIPT DE PRUEBA INICIANDO ---")

TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    print("--- ERROR FATAL: No se encontró el BOT_TOKEN. ---")
else:
    print(f"--- Token encontrado, empieza con: {TOKEN[:5]} ---")
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    print("--- Lanzando el bot en modo polling... ---")
    application.run_polling()
