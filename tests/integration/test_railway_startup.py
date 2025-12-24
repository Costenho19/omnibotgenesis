#!/usr/bin/env python3
"""
Test Railway Startup Simulation
Simula el comportamiento exacto de Railway para validar el deployment
"""

import os
import sys
import subprocess
import time

print("=" * 80)
print("🧪 RAILWAY STARTUP SIMULATION TEST")
print("=" * 80)
print()

# Configurar variables de entorno de producción Railway
print("📋 Configurando variables de entorno Railway...")
env_vars = {
    'PORT': '8080',
    'RAILWAY_ENVIRONMENT': 'production',
    'PYTHONUNBUFFERED': '1',
    # Mantener las actuales del sistema
    'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', ''),
    'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', ''),
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
    'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY', ''),
    'DATABASE_URL': os.getenv('DATABASE_URL', ''),
}

# Verificar variables críticas
print("\n🔍 Verificando variables de entorno críticas:")
critical_vars = ['TELEGRAM_BOT_TOKEN', 'DATABASE_URL']
missing_vars = []
for var in critical_vars:
    if env_vars[var]:
        print(f"   ✅ {var}: CONFIGURADA")
    else:
        print(f"   ⚠️ {var}: FALTANTE")
        missing_vars.append(var)

if missing_vars:
    print(f"\n⚠️ ADVERTENCIA: Variables faltantes: {', '.join(missing_vars)}")
    print("   El test continuará pero algunas funcionalidades pueden fallar")

# Simular el comando de Railway
print("\n" + "=" * 80)
print("🚀 SIMULANDO RAILWAY START COMMAND:")
print("   Comando: python -u main.py")
print("=" * 80)
print()

# Preparar entorno
test_env = os.environ.copy()
test_env.update(env_vars)

# Ejecutar main.py en modo test (primeros 30 segundos)
print("⏱️ Ejecutando main.py por 30 segundos para validar startup...")
print()

try:
    # Iniciar proceso
    process = subprocess.Popen(
        [sys.executable, '-u', 'main.py'],
        env=test_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Capturar output por 30 segundos
    start_time = time.time()
    validation_checks = {
        'cache_cleanup': False,
        'modules_loaded': False,
        'bot_initialized': False,
        'telegram_running': False,
        'services_ready': False
    }
    
    output_lines = []
    print("📊 VALIDANDO STARTUP SEQUENCE:\n")
    
    try:
        while time.time() - start_time < 30:
            try:
                line = process.stdout.readline()
                if not line:
                    # El proceso terminó antes de 30 segundos
                    if process.poll() is not None:
                        break
                    time.sleep(0.1)
                    continue
                    
                # Guardar y mostrar output
                output_lines.append(line)
                print(line, end='')
                
                # Validar checkpoints
                if 'Cache limpiado' in line or '__pycache__' in line:
                    validation_checks['cache_cleanup'] = True
                if 'Servicios modulares cargados' in line or 'MÓDULOS BÁSICOS ACTIVADOS' in line:
                    validation_checks['modules_loaded'] = True
                if 'EnterpriseTelegramBot instanciado' in line:
                    validation_checks['bot_initialized'] = True
                if 'BOT TELEGRAM OPERATIVO' in line or 'Bot Telegram iniciado' in line:
                    validation_checks['telegram_running'] = True
                if ('Gemini' in line and 'configurad' in line) or 'GEMINI' in line:
                    validation_checks['services_ready'] = True
                    
            except Exception as e:
                print(f"\n⚠️ Error leyendo output: {e}")
                break
    finally:
        # Asegurar terminación del proceso
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except:
                process.kill()
    
    # Reporte de validación
    print("\n" + "=" * 80)
    print("📊 RESULTADO DE VALIDACIÓN:")
    print("=" * 80)
    
    all_passed = True
    for check, status in validation_checks.items():
        symbol = "✅" if status else "❌"
        print(f"{symbol} {check.replace('_', ' ').title()}: {'PASS' if status else 'FAIL'}")
        if not status:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 VALIDACIÓN COMPLETA: TODOS LOS CHECKS PASARON")
        print("✅ Railway deployment está LISTO para producción")
    else:
        print("⚠️ VALIDACIÓN INCOMPLETA: Algunos checks fallaron")
        print("🔧 Revisar logs arriba para identificar problemas")
    print("=" * 80)
    
    sys.exit(0 if all_passed else 1)
    
except KeyboardInterrupt:
    print("\n\n⚠️ Test interrumpido por usuario")
    process.terminate()
    sys.exit(1)
except Exception as e:
    print(f"\n\n❌ ERROR durante test: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
