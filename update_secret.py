import os
import sys

# Leer el secret actual
current = os.getenv('DATABASE_URL', '')
print(f"Secret actual (primeros 60 chars): {current[:60]}...")

# La URL correcta de Harold
correct_url = "postgresql://postgres:uEyRpKDhlriSwqluZRnlQtXPbTXqxvVW@interchange.proxy.rlwy.net:22986/railway"

# Avisar al usuario que debe actualizar manualmente
print("\n" + "="*70)
print("⚠️  IMPORTANTE: Debes actualizar el secret DATABASE_URL manualmente")
print("="*70)
print("\n📋 Copia esta URL completa:\n")
print(correct_url)
print("\n🔧 Pasos:")
print("1. Replit → Tools (🔧) → Secrets")
print("2. Click DATABASE_URL → Edit (⋮)")
print("3. BORRA TODO y pega la URL de arriba")
print("4. Click Save")
print("\n✅ Luego OMNIX se conectará automáticamente")
