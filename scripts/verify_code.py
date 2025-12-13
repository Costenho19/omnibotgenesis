#!/usr/bin/env python3
"""
Simple code verification script for Replit development.
This validates Python syntax and imports without starting the Telegram bot.
Use this to verify code changes before pushing to GitHub → Railway.
"""
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def verify_imports():
    """Verify critical imports without starting services"""
    try:
        from omnix_config import VERSION_BANNER
        version_str = VERSION_BANNER
    except ImportError:
        version_str = "V6.5.4d INSTITUTIONAL+"
    
    print("=" * 60)
    print(f"OMNIX {version_str} - Code Verification")
    print("=" * 60)
    print()
    
    errors = []
    warnings = []
    
    # Test 1: Core quantum physics validator
    print("[1/5] Verificando physics_validator...")
    try:
        from omnix_core.quantum.physics_validator import QuantumPhysicsValidator
        pv = QuantumPhysicsValidator()
        
        # Verify all V5.0 and V6.0 formulas exist
        new_formulas = [
            'quantum_channel_capacity',
            'private_capacity_thermal',
            'quantum_sharpe_ratio',
            'quantum_criticality',
            # V6.0 PREMIUM - PQC Criticalidad
            'pqc_decoherence_security',
            'vqe_bures_fisher',
            'side_channel_criticality'
        ]
        
        for formula_key in new_formulas:
            if formula_key in pv.verified_formulas:
                formula = pv.verified_formulas[formula_key]
                kw_count = len(pv.detection_keywords.get(formula_key, []))
                print(f"  ✓ {formula.name}")
                print(f"    Keywords: {kw_count} términos")
            else:
                errors.append(f"{formula_key} NOT found in verified_formulas")
        
        print(f"  ✓ Total fórmulas verificadas: {len(pv.verified_formulas)}")
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
