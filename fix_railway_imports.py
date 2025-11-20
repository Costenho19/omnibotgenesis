"""
RAILWAY FIX - Forzar imports correctos
Ejecuta esto ANTES de main.py en Railway
"""

import sys
import os

# Asegurar que el directorio actual está en el path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print("✅ PYTHONPATH configurado correctamente")
print(f"   📂 Working Directory: {current_dir}")
print(f"   🐍 Python Path: {sys.path[:3]}")

# Verificar que omnix_config se puede importar
try:
    from omnix_config.settings import settings
    print("✅ omnix_config.settings importado correctamente")
except ImportError as e:
    print(f"❌ ERROR importando omnix_config.settings: {e}")
    sys.exit(1)

# Verificar ARES (sin bloqueo)
try:
    import ares_quantum_protocol
    import ares_scalping_v2
    print("✅ ARES Quantum Protocol files detectados")
except ImportError as e:
    print(f"⚠️ ARES files no disponibles: {e}")
except Exception as e:
    print(f"⚠️ ARES import error: {type(e).__name__}: {e}")
