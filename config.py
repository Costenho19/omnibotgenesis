# ==============================================================================
# === CONFIGURACIÓN GLOBAL DE OMNIX (config.py) ===
# ==============================================================================
# Lee de forma segura las claves desde .env o desde el entorno del servidor.
# Compatible con Railway, Render, Vercel y ejecución local.
# ==============================================================================

from decouple import config

# --- Claves del Bot Telegram y APIs Externas ---
BOT_TOKEN           = config('BOT_TOKEN', default=None)
GEMINI_API_KEY      = config('GEMINI_API_KEY', default=None)
OPENAI_API_KEY      = config('OPENAI_API_KEY', default=None)
KRAKEN_API_KEY      = config('KRAKEN_API_KEY', default=None)
KRAKEN_SECRET_KEY   = config('KRAKEN_SECRET_KEY', default=None)

# --- Base de Datos PostgreSQL ---
DATABASE_URL        = config('DATABASE_URL', default=None)
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- Seguridad y Control ---
CLAVE_PREMIUM       = config('CLAVE_PREMIUM', default="omnix2025premium")
SECRET_KEY          = config('SECRET_KEY', default="clave_super_segura")
SECRET_PHRASE       = config('SECRET_PHRASE', default="frase_de_respaldo")

# --- Administración ---
ADMIN_ID            = config('ADMIN_ID', cast=int, default=0)
