"""
WSGI Entry Point para Railway
"""

import os
import sys
import logging
import threading

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

logger.info("=" * 70)
logger.info("🚀 WSGI: Iniciando Railway deployment")
logger.info("=" * 70)

try:
    # Importar Flask app SIN iniciar bot
    logger.info("📦 Importando create_flask_app...")
    from main import create_flask_app, start_telegram_bot_background
    
    logger.info("🔧 Creando Flask app...")
    app = create_flask_app()
    
    if app is None:
        logger.error("❌ create_flask_app() retornó None")
        raise Exception("create_flask_app() returned None")
    
    logger.info(f"✅ Flask app lista: {type(app)}")
    
    # Iniciar bot de Telegram en background DESPUÉS de tener la app
    logger.info("🤖 Iniciando bot de Telegram en background...")
    bot_thread = threading.Thread(target=start_telegram_bot_background, daemon=True)
    bot_thread.start()
    logger.info("✅ Bot thread iniciado")
    
    # Obtener puerto
    port = int(os.environ.get('PORT', 8080))
    host = '0.0.0.0'
    
    logger.info("=" * 70)
    logger.info(f"🌐 INICIANDO SERVIDOR WAITRESS")
    logger.info(f"   📍 Host: {host}")
    logger.info(f"   📍 Port: {port}")
    logger.info("=" * 70)
    
    # Usar Waitress
    from waitress import serve
    
    logger.info("🔥 Waitress escuchando peticiones...")
    serve(app, host=host, port=port, threads=4, channel_timeout=120)
    
except Exception as e:
    logger.error("=" * 70)
    logger.error(f"❌ ERROR FATAL: {e}")
    logger.error("=" * 70)
    import traceback
    logger.error(traceback.format_exc())
    raise
