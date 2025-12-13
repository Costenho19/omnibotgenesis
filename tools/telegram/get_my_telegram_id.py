#!/usr/bin/env python3
"""
Script simple para obtener tu Telegram User ID.
Ejecuta esto y luego envía cualquier mensaje al bot (@YourBotUsername).
"""

import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def get_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Captura y muestra el User ID del usuario."""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Sin username"
    first_name = update.effective_user.first_name or "Sin nombre"
    
    print("\n" + "="*60)
    print("✅ TELEGRAM USER ID DETECTADO")
    print("="*60)
    print(f"👤 Nombre: {first_name}")
    print(f"📱 Username: @{username}")
    print(f"🆔 User ID: {user_id}")
    print("="*60)
    print("\n💾 Guarda este User ID para enviar mensajes programáticos\n")
    
    await update.message.reply_text(
        f"✅ Perfecto Harold!\n\n"
        f"🆔 Tu User ID es: `{user_id}`\n"
        f"👤 Nombre: {first_name}\n"
        f"📱 Username: @{username}\n\n"
        f"Este script se detendrá en 10 segundos..."
    )
    
    await asyncio.sleep(10)
    print("\n🛑 Script finalizado. Usa el User ID mostrado arriba.\n")
    os._exit(0)

async def main():
    print("\n" + "="*60)
    print("🔍 ESPERANDO MENSAJE DE TELEGRAM...")
    print("="*60)
    print("📱 Envía cualquier mensaje a tu bot de Telegram")
    print("🤖 El bot responderá con tu User ID")
    print("="*60 + "\n")
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, get_user_id))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
