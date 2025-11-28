#!/usr/bin/env python3
"""
Simple code verification script for Replit development.
This validates Python syntax and imports without starting the Telegram bot.
Use this to verify code changes before pushing to GitHub → Railway.
"""
import sys

def verify_imports():
    """Verify critical imports without starting services"""
    print("=" * 60)
    print("OMNIX V6.0 ULTRA - Code Verification")
    print("=" * 60)
    print()
    
    errors = []
    warnings = []
    
    # Test 1: Core quantum physics validator
    print("[1/5] Verificando physics_validator...")
    try:
        from omnix_core.quantum.physics_validator import QuantumPhysicsValidator
        pv = QuantumPhysicsValidator()
        
        # Verify the new quantum_channel_capacity formula exists
        if 'quantum_channel_capacity' in pv.verified_formulas:
            formula = pv.verified_formulas['quantum_channel_capacity']
            print(f"  ✓ Fórmula encontrada: {formula.name}")
            print(f"  ✓ Keywords: {len(pv.detection_keywords.get('quantum_channel_capacity', []))} términos")
        else:
            errors.append("quantum_channel_capacity formula NOT found in verified_formulas")
    except Exception as e:
        errors.append(f"physics_validator import failed: {e}")
    
    # Test 2: AI prompts
    print("[2/5] Verificando ai_prompts...")
    try:
        from omnix_services.ai_service.ai_prompts import PromptsContextManager
        pm = PromptsContextManager()
        print("  ✓ PromptsContextManager importado correctamente")
    except Exception as e:
        errors.append(f"ai_prompts import failed: {e}")
    
    # Test 3: Conversational brain
    print("[3/5] Verificando conversational_brain...")
    try:
        from omnix_services.ai_service.conversational_brain import ConversationalBrain
        print("  ✓ ConversationalBrain importado correctamente")
    except Exception as e:
        errors.append(f"conversational_brain import failed: {e}")
    
    # Test 4: Database service
    print("[4/5] Verificando database_service...")
    try:
        from omnix_services.database_service.database_service import DatabaseServiceEnterprise
        print("  ✓ DatabaseServiceEnterprise importado correctamente")
    except Exception as e:
        errors.append(f"database_service import failed: {e}")
    
    # Test 5: Main module (syntax only)
    print("[5/5] Verificando main.py sintaxis...")
    try:
        import ast
        with open('main.py', 'r') as f:
            ast.parse(f.read())
        print("  ✓ main.py sintaxis válida")
    except SyntaxError as e:
        errors.append(f"main.py syntax error: {e}")
    except Exception as e:
        warnings.append(f"main.py check: {e}")
    
    print()
    print("=" * 60)
    
    if errors:
        print("ERRORES ENCONTRADOS:")
        for err in errors:
            print(f"  ✗ {err}")
        sys.exit(1)
    else:
        print("✓ VERIFICACIÓN COMPLETADA - Código listo para push a GitHub")
        print()
        print("Próximos pasos:")
        print("  1. Usa el panel Git de Replit para hacer commit/push")
        print("  2. Railway detectará el push y hará deploy automático")
        print("  3. El bot en Railway usará el código actualizado")
        print()
        if warnings:
            print("Advertencias (no críticas):")
            for warn in warnings:
                print(f"  ! {warn}")
        sys.exit(0)

if __name__ == "__main__":
    verify_imports()
