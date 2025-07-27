# ==============================================================================
# === OMNIX GLOBAL BOT - PANEL WEB (web_dashboard.py) ===
# ==============================================================================
# Este es el punto de entrada principal para la aplicación web Flask.

from flask import Flask

# --- Importación de los Blueprints ---
# Un Blueprint en Flask es como un "módulo" o "sección" de nuestra página web.
# Esto nos permite organizar nuestras rutas (URLs) de forma muy limpia.
# Se asume que tienes una carpeta 'routes' con los archivos 'auth.py' y 'dashboard.py'.
try:
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
except ImportError as e:
    # Si las rutas no se encuentran, creamos Blueprints falsos para que la app no se caiga.
    # Esto facilita la depuración si la estructura de carpetas no es correcta.
    print(f"ADVERTENCIA: No se pudieron importar las rutas del dashboard: {e}")
    from flask import Blueprint
    auth_bp = Blueprint('auth_bp', __name__)
    dashboard_bp = Blueprint('dashboard_bp', __name__)

# --- Creación de la Aplicación Flask ---
# Esta es la línea que crea nuestra aplicación web.
app = Flask(__name__)

# --- Configuración de la Clave Secreta ---
# IMPORTANTE: La 'secret_key' es crucial para la seguridad de las sesiones de usuario.
# En producción, NUNCA debe estar escrita directamente en el código.
# La leeremos de las variables de entorno, igual que el BOT_TOKEN.
# Asegúrate de añadir una variable FLASK_SECRET_KEY en Railway.
from config import FLASK_SECRET_KEY
app.secret_key = FLASK_SECRET_KEY or 'clave_de_desarrollo_insegura'


# --- Registro de los Blueprints ---
# Aquí le decimos a nuestra aplicación principal que "active" las secciones
# que hemos definido en los otros archivos.
app.register_blueprint(auth_bp, url_prefix='/auth') # Todas las rutas de autenticación empezarán con /auth
app.register_blueprint(dashboard_bp, url_prefix='/') # El dashboard será la página principal

# --- Punto de Entrada para Ejecución Directa ---
# Este bloque solo se ejecuta si corremos este archivo directamente (ej. `python web_dashboard.py`).
# En nuestro caso, el bot de Telegram (`main.py`) se encargará de iniciarlo.
if __name__ == "__main__":
    # El modo debug=True es muy útil para el desarrollo, pero NUNCA debe usarse en producción.
    # El puerto 5000 es un estándar para desarrollo con Flask.
    app.run(host="0.0.0.0", port=5000, debug=True)
