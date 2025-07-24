from flask import Flask, render_template_string
import psycopg2
import os
from config import DATABASE_URL

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>OMNIX Panel</title>
    <style>
        body { font-family: Arial; background-color: #0c0c0c; color: white; padding: 2rem; }
        h1 { color: #00ff99; }
        table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
        th, td { border: 1px solid #333; padding: 0.5rem; text-align: left; }
        th { background-color: #111; }
    </style>
</head>
<body>
    <h1>📊 Panel OMNIX - Análisis Recientes</h1>
    <table>
        <tr>
            <th>Usuario</th><th>Asset</th><th>Análisis</th><th>Fecha</th>
        </tr>
        {% for row in rows %}
        <tr>
            <td>{{ row[0] }}</td><td>{{ row[1] }}</td><td>{{ row[2] }}</td><td>{{ row[3] }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route("/")
def home():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, asset, ai_text, created_at FROM ai_analysis ORDER BY created_at DESC LIMIT 20")
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        rows = [(0, "ERROR", str(e), "-")]
    
    return render_template_string(HTML_TEMPLATE, rows=rows)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=False, host="0.0.0.0", port=port)
