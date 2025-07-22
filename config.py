import os
from dotenv import load_dotenv

# Carga las variables de un archivo .env si existe (útil para pruebas locales)
load_dotenv()

BOT_TOKEN = os.environ.get('BOT_TOKEN')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
KRAKEN_API_KEY = os.environ.get('KRAKEN_API_KEY')
KRAKEN_SECRET_KEY = os.environ.get('KRAKEN_SECRET_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL') # Nuestra nueva URL de Neon
