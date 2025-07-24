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
        body { font-family: Arial; background-color: #0c0c0c; color: white; }
        h1 { color: #00ff99; }
        table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
        th, td { border: 1px solid #333; padding: 0.5rem; text-align: center; }
        th { background-color: #111; }
    </style>
</head>
<body>
    <h1>📊 Panel OMNIX - Análisis Recientes</h1>
    <table>
        <tr>
            <th>Usuario</th>
            <th>Asset</th>
            <th>Análisis</th>
            <th>Fecha</th>
        </tr>
        {% for row in rows %}
        <tr>
            <td>{{ row[0] }}</td>
            <td>{{ row[1] }}</td>
            <td>{{ row[2] }}</td>
            <td>{{ row[3] }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route("/")
def panel():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT usuario, asset, analisis, fecha FROM ai_analysis ORDER BY fecha DESC LIMIT 20")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template_string(HTML_TEMPLATE, rows=rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
