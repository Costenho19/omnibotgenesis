import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Importa nuestras clases, funciones y configuración desde los otros archivos
from config import BOT_TOKEN, DATABASE_URL
from database import setup_premium_database, add_premium_assets
from analysis_engine import OmnixPremiumAnalysisEngine, premium_assets_list

# Configuración del logging para ver qué hace el bot
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Instanciamos nuestro motor de análisis ---
# Creamos una instancia global para que no se reinicie con cada comando
analysis_engine = OmnixPremiumAnalysisEngine()

# --- Definición de los Comandos del Bot ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envía un mensaje de bienvenida cuando el comando /start es ejecutado."""
    user = update.effective_user
    await update.message.reply_html(
        rf"¡Hola {user.mention_html()}! Soy OMNIX, tu asistente de trading. Usa /analyze <SÍMBOLO> para empezar (ej: /analyze AAPL).",
    )

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Realiza un análisis de un activo solicitado por el usuario."""
    # Verificamos si el usuario ha escrito un símbolo después del comando
    if not context.args:
        await update.message.reply_text("Por favor, dame un símbolo para analizar. Uso: /analyze <SÍMBOLO>")
        return

    symbol = context.args[0].upper()
    await update.message.reply_text(f"Analizando {symbol}, un momento por favor...")

    # Ejecuta el análisis en un hilo separado para no bloquear el bot
    # Esto es crucial para que pueda atender a varios usuarios a la vez
    loop = asyncio.get_running_loop()
    try:
        # La función 'analysis_engine.analyze_with_ai' es la que tarda, por eso la separamos
        analysis_result = await loop.run_in_executor(
            None, analysis_engine.analyze_with_ai, symbol
        )

        if analysis_result:
            # Formateamos el mensaje de respuesta con los resultados
            message = f"""
📈 *Análisis para {analysis_result.symbol}* 📈

*Precio Actual:* ${analysis_result.current_price:,.2f}
*Recomendación:* *{analysis_result.recommendation}*
*Confianza:* {analysis_result.confidence:.0%}
*Riesgo:* {analysis_result.risk_score:.0%}

*Predicciones (Simuladas):*
  - 1h: ${analysis_result.prediction_1h:,.2f}
  - 24h: ${analysis_result.prediction_24h:,.2f}
  - 7d: ${analysis_result.prediction_7d:,.2f}
            """
            # Usamos reply_markdown para que los asteriscos (*) pongan el texto en negrita
            await update.message.reply_markdown(message)
        else:
            await update.message.reply_text(f"Lo siento, no pude obtener datos para {symbol}. Revisa si el ticker es correcto (ej. AAPL, BTC-USD).")

    except Exception as e:
        logger.error(f"Error durante el análisis para {symbol}: {e}")
        await update.message.reply_text("Ocurrió un error inesperado al procesar tu solicitud. Por favor, intenta de nuevo.")
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Esta función responde a cualquier mensaje que no sea un comando."""
    logger.info(f"RECIBIDO MENSAJE de {update.effective_user.name}: {update.message.text}")
    await update.message.reply_text("He recibido tu mensaje. El comando /start está en desarrollo.")
# --- Función Principal que Arranca Todo ---

async def main() -> None:
    """Inicia el bot y lo mantiene corriendo."""
    logger.info("🚀 Iniciando OMNIX Bot...")

    # Verificaciones críticas antes de arrancar
    if not BOT_TOKEN:
        logger.critical("FATAL: No se ha encontrado el BOT_TOKEN. El bot no puede iniciar.")
        return
    
    if not DATABASE_URL:
        logger.critical("FATAL: No se ha encontrado la DATABASE_URL. El bot no puede iniciar.")
        return

    # 1. Nos aseguramos de que las tablas de la base de datos existan
    setup_premium_database()
    # 2. Poblamos la base de datos con los activos iniciales de nuestra lista
    add_premium_assets(premium_assets_list)

    # Creamos la aplicación del bot
    application = Application.builder().token(BOT_TOKEN).build()
    await application.bot.delete_webhook()
    # Añadimos los manejadores de comandos (le decimos al bot qué hacer con cada comando)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    logger.info("✅ Bot listo y escuchando peticiones...")
    
    # Arrancamos el bot para que escuche mensajes de Telegram
    application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
