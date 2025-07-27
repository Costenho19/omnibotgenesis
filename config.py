from decouple import config

# decouple buscará las variables en Railway de forma más robusta.
# Si no las encuentra, el valor por defecto será None.
BOT_TOKEN = config('BOT_TOKEN', default=None)
DATABASE_URL = config('DATABASE_URL', default=None)
GEMINI_API_KEY = config('GEMINI_API_KEY', default=None)
OPENAI_API_KEY = config('OPENAI_API_KEY', default=None)
KRAKEN_API_KEY = config('KRAKEN_API_KEY', default=None)
KRAKEN_SECRET_KEY = config('KRAKEN_SECRET_KEY', default=None)
CLAVE_PREMIUM = config('CLAVE_PREMIUM', default=None)
ADMIN_ID = int(config('ADMIN_ID', default=0))
SECRET_PHRASE = os.getenv("SECRET_PHRASE")
SECRET_KEY = os.getenv("SECRET_KEY")
