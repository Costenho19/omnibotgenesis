import os
import time

print("--- INICIANDO PRUEBA DE VERIFICACIÓN ---")

# Leemos la variable BOT_TOKEN
bot_token = os.environ.get('BOT_TOKEN')

if bot_token:
    print("✅ ÉXITO: La variable BOT_TOKEN fue encontrada.")
    # Imprimimos solo los primeros 5 caracteres por seguridad
    print(f"   -> El token empieza con: {bot_token[:5]}")
else:
    print("❌ ERROR: La variable BOT_TOKEN NO fue encontrada.")

print("--- PRUEBA DE VERIFICACIÓN TERMINADA ---")

# Dejamos el script durmiendo para que los logs no se cierren de inmediato
time.sleep(300)
