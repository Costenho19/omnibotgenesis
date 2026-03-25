#!/usr/bin/env python3
"""
Test Railway Startup Simulation
Simula el comportamiento exacto de Railway para validar el deployment.
Ejecutar directamente: python tests/integration/test_railway_startup.py
"""

import os
import sys
import subprocess
import time


def run_railway_startup_simulation():
    print("=" * 80)
    print("RAILWAY STARTUP SIMULATION TEST")
    print("=" * 80)
    print()

    print("Configurando variables de entorno Railway...")
    env_vars = {
        'PORT': '8080',
        'RAILWAY_ENVIRONMENT': 'production',
        'PYTHONUNBUFFERED': '1',
        'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', ''),
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', ''),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY', ''),
        'DATABASE_URL': os.getenv('DATABASE_URL', ''),
    }

    print("\nVerificando variables de entorno criticas:")
    critical_vars = ['TELEGRAM_BOT_TOKEN', 'DATABASE_URL']
    missing_vars = []
    for var in critical_vars:
        if env_vars[var]:
            print(f"   OK  {var}: CONFIGURADA")
        else:
            print(f"   WARN {var}: FALTANTE")
            missing_vars.append(var)

    if missing_vars:
        print(f"\nADVERTENCIA: Variables faltantes: {', '.join(missing_vars)}")

    print("\n" + "=" * 80)
    print("SIMULANDO RAILWAY START COMMAND: python -u main.py")
    print("=" * 80)
    print()

    test_env = os.environ.copy()
    test_env.update(env_vars)

    print("Ejecutando main.py por 30 segundos para validar startup...")

    try:
        process = subprocess.Popen(
            [sys.executable, '-u', 'main.py'],
            env=test_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        start_time = time.time()
        validation_checks = {
            'cache_cleanup': False,
            'modules_loaded': False,
            'bot_initialized': False,
            'telegram_running': False,
            'services_ready': False
        }

        output_lines = []
        print("VALIDANDO STARTUP SEQUENCE:\n")

        try:
            while time.time() - start_time < 30:
                try:
                    line = process.stdout.readline()
                    if not line:
                        if process.poll() is not None:
                            break
                        time.sleep(0.1)
                        continue

                    output_lines.append(line)
                    print(line, end='')

                    if 'Cache limpiado' in line or '__pycache__' in line:
                        validation_checks['cache_cleanup'] = True
                    if 'Servicios modulares cargados' in line or 'MODULOS BASICOS ACTIVADOS' in line:
                        validation_checks['modules_loaded'] = True
                    if 'EnterpriseTelegramBot instanciado' in line:
                        validation_checks['bot_initialized'] = True
                    if 'BOT TELEGRAM OPERATIVO' in line or 'Bot Telegram iniciado' in line:
                        validation_checks['telegram_running'] = True
                    if ('Gemini' in line and 'configurad' in line) or 'GEMINI' in line:
                        validation_checks['services_ready'] = True

                except Exception as e:
                    print(f"\nError leyendo output: {e}")
                    break
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except Exception:
                    process.kill()

        print("\n" + "=" * 80)
        print("RESULTADO DE VALIDACION:")
        print("=" * 80)

        all_passed = True
        for check, status in validation_checks.items():
            symbol = "OK" if status else "FAIL"
            print(f"{symbol} {check.replace('_', ' ').title()}: {'PASS' if status else 'FAIL'}")
            if not status:
                all_passed = False

        print("\n" + "=" * 80)
        if all_passed:
            print("VALIDACION COMPLETA: TODOS LOS CHECKS PASARON")
        else:
            print("VALIDACION INCOMPLETA: Algunos checks fallaron")
        print("=" * 80)

        return all_passed

    except KeyboardInterrupt:
        print("\nTest interrumpido por usuario")
        return False
    except Exception as e:
        print(f"\nERROR durante test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_railway_startup_simulation()
    sys.exit(0 if success else 1)
