from flask import Flask
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp

app = Flask(__name__)
app.secret_key = 'clave_super_segura'  # Reemplázalo luego con variable .env

# Registra las rutas
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)

if __name__ == "__main__":
    app.run(debug=True)
