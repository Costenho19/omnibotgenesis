from flask import Flask, render_template_string
import psycopg2
import os
from config import DATABASE_URL

app = Flask(__name__)

@app.route("/")
def dashboard():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT user_id, symbol, analysis_text, timestamp FROM ai_analysis ORDER BY timestamp DESC LIMIT 50")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        html = "<h2>📊 Historial de Análisis OMNIX</h2><ul>"
        for row in rows:
            html += f"<li><b>{row[1]}</b> - {row[2]}<br><small>Usuario: {row[0]} | Fecha: {row[3]}</small></li><br>"
        html += "</ul>"
        return render_template_string(html)
    except Exception as e:
        return f"<h3>❌ Error al acceder a la base de datos: {e}</h3>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
