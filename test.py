import os
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- PASO 1: Configuración básica ---
# Esto nos permite ver los mensajes del bot en los logs de Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- PASO 2: Leemos el BOT_TOKEN de las variables de Railway ---
# Esta es la única "llave" que necesita este bot de prueba
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# --- PASO 3: Definimos el único comando que este bot entenderá ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Esta función se activa cuando alguien envía /start."""
    user_name = update.effective_user.name
    
    # Imprimimos un mensaje en los logs para saber que hemos recibido el comando
    logger.info(f"Comando /start RECIBIDO de: {user_name}")
    
    # Enviamos una respuesta al usuario en Telegram
    await update.message.reply_text(f"¡Hola {user_name}! El bot de prueba está funcionando correctamente.")

# --- PASO 4: La función principal que arranca el bot ---
async def main() -> None:
    """La función principal que configura y arranca este bot de prueba."""
    
    # Comprobamos si tenemos la llave de Telegram
    if not BOT_TOKEN:
        logger.critical("FATAL: No se ha encontrado el BOT_TOKEN en las variables de entorno.")
        return

    logger.info("Iniciando el bot de PRUEBA...")
    
    # Creamos la aplicación del bot
    application = Application.builder().token(BOT_TOKEN).build()

    # Le decimos al bot que cuando reciba el comando "start", active la función 'start'
    application.add_handler(CommandHandler("start", start))

    # --- Limpieza y Arranque Controlado (La parte importante) ---
    logger.info("Limpiando cualquier sesión antigua de Telegram...")
    await application.bot.delete_webhook()

    logger.info("Inicializando la aplicación...")
    await application.initialize()

    logger.info("✅ Bot de PRUEBA listo y escuchando peticiones...")
    await application.start()
    
    # Mantenemos el bot activo para siempre
    await asyncio.Event().wait()


# --- PASO 5: El punto de entrada que ejecuta todo ---
if __name__ == "__main__":
    asyncio.run(main())
