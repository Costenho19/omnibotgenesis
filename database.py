1  import psycopg2
2  import json
3  import logging
4  from datetime import datetime
5  from pqc_encryption import encrypt_message
6  from config import DATABASE_URL
7
8  logger = logging.getLogger(__name__)
9
10 def get_db_connection():
11     try:
12         conn = psycopg2.connect(DATABASE_URL)
13         return conn
14     except Exception as e:
15         logger.error(f"❌ Error al conectar con la base de datos: {e}")
16         return None
17
18 def setup_premium_database(premium_assets):
19     """
20     Inserta los activos premium iniciales en la base de datos.
21     """
22     conn = get_db_connection()
23     if not conn:
24         return
25     try:
26         with conn.cursor() as cursor:
27             sql = """
28                 INSERT INTO premium_assets (symbol, name, sector, added_at)
29                 VALUES (%s, %s, %s, NOW())
30             """
31             cursor.executemany(sql, premium_assets)
32             conn.commit()
33             logger.info(f"{cursor.rowcount} activos premium insertados")
34     except Exception as e:
35         logger.error(f"❌ Error insertando activos premium: {e}")
36         conn.rollback()
37     finally:
38         conn.close()
39
40 def save_analysis_to_db(user_id, asset, analysis_text, result_dict):
41     """
42     Guarda un resultado de análisis en la base de datos con cifrado post-cuántico.
43     """
44     encrypted_analysis = encrypt_message(analysis_text)
45     encrypted_result = encrypt_message(json.dumps(result_dict))
46
47     try:
48         conn = get_db_connection()
49         if not conn:
50             return
51         cursor = conn.cursor()
52         cursor.execute(
53             """
54             INSERT INTO ai_analysis (user_id, asset, analysis, result, timestamp)
55             VALUES (%s, %s, %s, %s, %s)
56             """,
57             (user_id, asset, encrypted_analysis, encrypted_result, datetime.utcnow())
58         )
59         conn.commit()
60         cursor.close()
61         conn.close()
62     except Exception as e:
63         logger.error(f"❌ Error guardando análisis cifrado: {e}")
64
65 def crear_tabla_voice_signatures():
66     try:
67         conn = psycopg2.connect(DATABASE_URL)
68         cursor = conn.cursor()
69         cursor.execute(
70             '''
71             CREATE TABLE IF NOT EXISTS voice_signatures (
72                 id SERIAL PRIMARY KEY,
73                 user_id TEXT,
74                 signature TEXT,
75                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
76             )
77             '''
78         )
79         conn.commit()
80         cursor.close()
81         conn.close()
82     except Exception as e:
83         logger.error(f"❌ Error creando tabla de firmas de voz: {e}")
