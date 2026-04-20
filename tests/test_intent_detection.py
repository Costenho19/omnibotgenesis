"""
OMNIX V5.4 ULTRA - Sistema de Testing Premium
Testing del Detector de Intent y Calidad de Respuestas
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from omnix_services.ai_service.ai_prompts import PromptsContextManager

def test_intent_detection():
    """
    Testing exhaustivo del detector de intent
    Verifica que preguntas técnicas complejas sean clasificadas correctamente
    """
    
    prompts_manager = PromptsContextManager()
    
    # Test Cases: (mensaje, intent_esperado, descripción)
    test_cases = [
        # SALUDOS SIMPLES - greeting (sub-intent more precise than general_conversation)
        ("hola", "greeting", "Saludo básico"),
        ("gracias", "general_conversation", "Agradecimiento"),
        ("ok", "general_conversation", "Confirmación corta"),
        
        # PREGUNTAS TÉCNICAS - market_analysis
        ("¿Cómo OMNIX vence la EMH Fuerte?", "market_analysis", "Pregunta técnica con puntuación"),
        ("Explica Video Learning", "market_analysis", "Palabra clave: explica"),
        ("Por qué Alpha supera mercado", "market_analysis", "Palabra clave: por qué"),
        ("EMH?", "market_analysis", "Keyword técnico corto"),
        ("Diferencia entre Kalman y Monte Carlo", "market_analysis", "Comparación técnica"),
        ("Cómo funciona Black Swan detector", "performance_risk_discussion", "Pregunta de riesgo/Black Swan"),
        ("Ventaja de Quantum Momentum", "market_analysis", "Keyword: ventaja"),
        ("¿Qué es Machine Learning?", "market_analysis", "Keyword: machine learning"),
        
        # MENSAJES LARGOS - market_analysis
        ("Me gustaría entender mejor cómo el sistema maneja riesgos en condiciones de alta volatilidad", "market_analysis", "Mensaje largo >10 palabras"),
        
        # TRADING ACTIONS
        ("comprar BTC", "trading_action", "Acción de compra"),
        ("vender ETH", "trading_action", "Acción de venta"),
        
        # PRICE INQUIRY
        ("precio BTC", "price_inquiry", "Consulta de precio"),
        ("cuánto cuesta ETH", "price_inquiry", "Consulta de valor"),
        
        # BALANCE
        ("saldo", "balance_inquiry", "Consulta de balance"),
        ("cuánto tengo", "balance_inquiry", "Consulta de fondos"),
    ]
    
    print("=" * 80)
    print("🧪 TESTING DETECTOR DE INTENT - OMNIX V5.4 ULTRA")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for mensaje, expected_intent, descripcion in test_cases:
        detected_intent = prompts_manager.analyze_intent(mensaje)
        
        if detected_intent == expected_intent:
            print(f"✅ PASS: {descripcion}")
            print(f"   Mensaje: '{mensaje}'")
            print(f"   Intent: {detected_intent}")
            passed += 1
        else:
            print(f"❌ FAIL: {descripcion}")
            print(f"   Mensaje: '{mensaje}'")
            print(f"   Esperado: {expected_intent}")
            print(f"   Detectado: {detected_intent}")
            failed += 1
        print()
    
    print("=" * 80)
    print(f"RESULTADOS: {passed}/{len(test_cases)} tests pasados")
    print(f"✅ PASS: {passed}")
    print(f"❌ FAIL: {failed}")
    print("=" * 80)

    assert failed == 0, (
        f"Intent detection failures: {failed}/{len(test_cases)} cases wrong"
    )

def test_prompt_generation():
    """
    Verificar que los prompts generados tengan las instrucciones correctas
    """
    
    prompts_manager = PromptsContextManager()
    
    print("\n" + "=" * 80)
    print("🧪 TESTING GENERACIÓN DE PROMPTS")
    print("=" * 80)
    print()
    
    # Test market_analysis prompt
    prompt = prompts_manager.build_system_prompt(
        intent='market_analysis',
        user_name='Harold'
    )
    
    # Verificar elementos clave
    checks = [
        ("DEPTH" in prompt or "profundidad" in prompt.lower(), "Instrucción de profundidad en prompt"),
        ("9 estrategias" in prompt or "Monte Carlo" in prompt, "Mención de estrategias técnicas"),
        ("Harold" in prompt, "Personalización con nombre de usuario"),
        ("market_analysis" in prompt or "Análisis de Mercado" in prompt, "Tipo de intent correcto"),
    ]
    
    passed = 0
    for check, descripcion in checks:
        if check:
            print(f"✅ PASS: {descripcion}")
            passed += 1
        else:
            print(f"❌ FAIL: {descripcion}")
    
    print()
    print(f"RESULTADOS: {passed}/{len(checks)} checks pasados")
    print("=" * 80)

    assert passed == len(checks), (
        f"Prompt generation checks failed: {passed}/{len(checks)} passed"
    )

def test_normalization():
    """
    Testing de normalización de mensajes
    """
    
    prompts_manager = PromptsContextManager()
    
    print("\n" + "=" * 80)
    print("🧪 TESTING NORMALIZACIÓN DE MENSAJES")
    print("=" * 80)
    print()
    
    test_cases = [
        ("¿Cómo?", "como", "Normalización de puntuación y acentos"),
        ("EMH???", "emh", "Múltiples signos de puntuación"),
        ("POR QUÉ", "por que", "Mayúsculas y espacios"),
    ]
    
    passed = 0
    
    for mensaje, _, descripcion in test_cases:
        # Verificar que se detecta como market_analysis gracias a normalización
        intent = prompts_manager.analyze_intent(mensaje)
        if intent == "market_analysis":
            print(f"✅ PASS: {descripcion}")
            print(f"   Mensaje: '{mensaje}' → Intent: {intent}")
            passed += 1
        else:
            print(f"❌ FAIL: {descripcion}")
            print(f"   Mensaje: '{mensaje}' → Intent: {intent} (esperado: market_analysis)")
        print()
    
    print(f"RESULTADOS: {passed}/{len(test_cases)} tests pasados")
    print("=" * 80)

    assert passed == len(test_cases), (
        f"Normalization failures: {passed}/{len(test_cases)} cases correct"
    )

if __name__ == "__main__":
    print("\n🚀 OMNIX V5.4 ULTRA - SUITE DE TESTING PREMIUM\n")
    
    results = []
    
    # Test 1: Intent Detection
    results.append(("Intent Detection", test_intent_detection()))
    
    # Test 2: Prompt Generation
    results.append(("Prompt Generation", test_prompt_generation()))
    
    # Test 3: Normalization
    results.append(("Message Normalization", test_normalization()))
    
    # Resumen final
    print("\n" + "=" * 80)
    print("📊 RESUMEN FINAL")
    print("=" * 80)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 80)
    
    if all_passed:
        print("\n🎉 TODOS LOS TESTS PASADOS - Sistema listo para producción")
        sys.exit(0)
    else:
        print("\n⚠️ ALGUNOS TESTS FALLARON - Revisar implementación")
        sys.exit(1)
