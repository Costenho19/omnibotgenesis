"""
Tests for Systemic Framing Router (ADR-013)

Validates deterministic classification of systemic questions into 4 types:
- TYPE_A: Coordination / Synchronization
- TYPE_B: Software / Deployment
- TYPE_C: Dependencies / Providers
- TYPE_D: Governance / Compliance
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from omnix_services.ai_service.conversational_ai_adapter import (
    classify_systemic_question,
    detect_systemic_question,
    get_systemic_override_prompt,
    SYSTEMIC_TYPE_A_KEYWORDS,
    SYSTEMIC_TYPE_B_KEYWORDS,
    SYSTEMIC_TYPE_C_KEYWORDS,
    SYSTEMIC_TYPE_D_KEYWORDS,
    SYSTEMIC_OVERRIDE_COORDINATION,
    SYSTEMIC_OVERRIDE_SOFTWARE,
    SYSTEMIC_OVERRIDE_DEPENDENCIES,
    SYSTEMIC_OVERRIDE_GOVERNANCE,
)


class TestSystemicClassification:
    """Test classify_systemic_question() function."""
    
    def test_type_a_coordination_keywords(self):
        """Type A should detect coordination/synchronization questions."""
        questions = [
            "Si 10,000 usuarios reciben la misma señal de venta...",
            "¿Qué pasa si todos los usuarios vendieran simultáneamente?",
            "¿Cómo evitan el efecto manada?",
            "¿Existe riesgo sistémico si todos reciben la misma señal?",
            "¿OMNIX podría causar coordinación de mercado?",
            "¿Qué ocurre con una venta masiva?",
        ]
        for q in questions:
            result = classify_systemic_question(q)
            assert result == 'TYPE_A', f"Expected TYPE_A for: {q}, got {result}"
    
    def test_type_b_software_keywords(self):
        """Type B should detect software/deployment questions."""
        questions = [
            "¿Qué pasa si hay un defecto lógico en el código base?",
            "Si descubren un bug después del despliegue...",
            "¿Cómo manejan la versión del modelo?",
            "¿Qué ocurre si el mismo código afecta a miles de instancias?",
        ]
        for q in questions:
            result = classify_systemic_question(q)
            assert result == 'TYPE_B', f"Expected TYPE_B for: {q}, got {result}"
    
    def test_type_c_dependencies_keywords(self):
        """Type C should detect dependencies/providers questions."""
        questions = [
            "¿Cómo gestionan dependencia de proveedores externos?",
            "¿Qué pasa con un fallo silencioso de API?",
            "Si Kraken tiene datos inconsistentes...",
            "¿Cómo manejan la latencia del exchange?",
        ]
        for q in questions:
            result = classify_systemic_question(q)
            assert result == 'TYPE_C', f"Expected TYPE_C for: {q}, got {result}"
    
    def test_type_d_governance_keywords(self):
        """Type D should detect governance/compliance questions."""
        questions = [
            "¿Cómo se preparan para auditorías regulatorias?",
            "¿Tienen compliance con SEC?",
            "¿Cuál es la responsabilidad fiduciaria?",
            "¿Cómo manejan la gobernanza del sistema?",
        ]
        for q in questions:
            result = classify_systemic_question(q)
            assert result == 'TYPE_D', f"Expected TYPE_D for: {q}, got {result}"
    
    def test_non_systemic_questions(self):
        """Non-systemic questions should return None."""
        questions = [
            "¿Cuál es el win rate actual?",
            "¿Cómo funciona el motor de trading?",
            "¿Qué es OMNIX?",
            "Muéstrame el dashboard",
        ]
        for q in questions:
            result = classify_systemic_question(q)
            assert result is None, f"Expected None for: {q}, got {result}"


class TestPriorityOrder:
    """Test priority order: A > D > C > B."""
    
    def test_type_a_beats_type_b(self):
        """Type A (coordination) should have priority over Type B (software)."""
        q = "Si 10,000 usuarios descubren un bug y venden simultáneamente"
        result = classify_systemic_question(q)
        assert result == 'TYPE_A', f"Expected TYPE_A (priority), got {result}"
    
    def test_type_a_beats_type_c(self):
        """Type A (coordination) should have priority over Type C (dependencies)."""
        q = "Si una API falla y todos los usuarios reciben la misma señal de venta"
        result = classify_systemic_question(q)
        assert result == 'TYPE_A', f"Expected TYPE_A (priority), got {result}"
    
    def test_type_d_beats_type_c(self):
        """Type D (governance) should have priority over Type C (dependencies)."""
        q = "¿Cómo auditan los proveedores externos?"
        result = classify_systemic_question(q)
        assert result == 'TYPE_D', f"Expected TYPE_D (priority), got {result}"


class TestDetectSystemicQuestion:
    """Test detect_systemic_question() boolean function."""
    
    def test_detects_any_systemic_type(self):
        """Should return True for any systemic question type."""
        assert detect_systemic_question("10,000 usuarios vendiendo") is True
        assert detect_systemic_question("defecto lógico en código") is True
        assert detect_systemic_question("proveedores externos fallando") is True
        assert detect_systemic_question("auditoría regulatoria") is True
    
    def test_returns_false_for_non_systemic(self):
        """Should return False for non-systemic questions."""
        assert detect_systemic_question("¿Cuál es el balance?") is False
        assert detect_systemic_question("Hola OMNIX") is False


class TestGetSystemicOverridePrompt:
    """Test get_systemic_override_prompt() function."""
    
    def test_type_a_returns_coordination_prompt(self):
        """TYPE_A should return coordination override."""
        prompt = get_systemic_override_prompt('TYPE_A')
        assert prompt == SYSTEMIC_OVERRIDE_COORDINATION
        assert 'COORDINATION' in prompt
        assert 'no genera señales sincronizadas' in prompt
    
    def test_type_b_returns_software_prompt(self):
        """TYPE_B should return software override."""
        prompt = get_systemic_override_prompt('TYPE_B')
        assert prompt == SYSTEMIC_OVERRIDE_SOFTWARE
        assert 'SOFTWARE' in prompt
        assert 'múltiples capas de defensa' in prompt
    
    def test_type_c_returns_dependencies_prompt(self):
        """TYPE_C should return dependencies override."""
        prompt = get_systemic_override_prompt('TYPE_C')
        assert prompt == SYSTEMIC_OVERRIDE_DEPENDENCIES
        assert 'DEPENDENCIES' in prompt
        assert 'resiliencia' in prompt
    
    def test_type_d_returns_governance_prompt(self):
        """TYPE_D should return governance override."""
        prompt = get_systemic_override_prompt('TYPE_D')
        assert prompt == SYSTEMIC_OVERRIDE_GOVERNANCE
        assert 'GOVERNANCE' in prompt
        assert 'gobernanza' in prompt.lower()
    
    def test_none_returns_empty(self):
        """None should return empty string."""
        prompt = get_systemic_override_prompt(None)
        assert prompt == ""


class TestOverrideContent:
    """Test that each override contains required elements."""
    
    def test_all_overrides_forbid_numbered_sections(self):
        """All overrides should forbid numbered sections."""
        overrides = [
            SYSTEMIC_OVERRIDE_COORDINATION,
            SYSTEMIC_OVERRIDE_SOFTWARE,
            SYSTEMIC_OVERRIDE_DEPENDENCIES,
            SYSTEMIC_OVERRIDE_GOVERNANCE,
        ]
        for override in overrides:
            assert '*1.' in override or 'Numbered sections' in override
            assert 'FORBIDDEN' in override.upper()
    
    def test_coordination_override_has_mandatory_opening(self):
        """Coordination override must have specific opening phrase."""
        assert 'OMNIX no genera señales sincronizadas' in SYSTEMIC_OVERRIDE_COORDINATION
        assert 'MANDATORY OPENING' in SYSTEMIC_OVERRIDE_COORDINATION
    
    def test_software_override_has_different_opening(self):
        """Software override should NOT have coordination opening."""
        assert 'implementa múltiples capas de defensa' in SYSTEMIC_OVERRIDE_SOFTWARE
        assert 'DO NOT open with' in SYSTEMIC_OVERRIDE_SOFTWARE
    
    def test_dependencies_override_has_different_opening(self):
        """Dependencies override should NOT have coordination opening."""
        assert 'valida cada fuente de datos' in SYSTEMIC_OVERRIDE_DEPENDENCIES
        assert 'DO NOT open with' in SYSTEMIC_OVERRIDE_DEPENDENCIES
    
    def test_governance_override_has_different_opening(self):
        """Governance override should NOT have coordination opening."""
        assert 'perspectiva de gobernanza' in SYSTEMIC_OVERRIDE_GOVERNANCE
        assert 'DO NOT open with' in SYSTEMIC_OVERRIDE_GOVERNANCE


class TestRealWorldQuestions:
    """Test with actual investor questions from production."""
    
    def test_code_defect_question_is_type_b(self):
        """Investor's code defect question should be TYPE_B, not TYPE_A."""
        q = "Si OMNIX utiliza el mismo código base y versiones de modelo para miles de instancias aisladas, ¿cómo evita que un defecto lógico descubierto después del despliegue afecte simultáneamente a todos los clientes antes de ser detectado y neutralizado?"
        result = classify_systemic_question(q)
        assert result == 'TYPE_B', f"Expected TYPE_B for code defect question, got {result}"
    
    def test_provider_degradation_question_is_type_c(self):
        """Investor's provider question should be TYPE_C, not TYPE_A."""
        q = "¿Cómo gestiona OMNIX el riesgo de dependencia de proveedores externos (exchanges, APIs de datos, infraestructura cloud) y qué ocurre si una degradación parcial, fallo silencioso o comportamiento incorrecto de un proveedor externo introduce datos inconsistentes que podrían afectar las decisiones de miles de instancias sin que exista un 'hard failure' detectable?"
        result = classify_systemic_question(q)
        assert result == 'TYPE_C', f"Expected TYPE_C for provider question, got {result}"
    
    def test_mass_selling_question_is_type_a(self):
        """Mass selling question should remain TYPE_A."""
        q = "Si 10,000 usuarios recibieran simultáneamente una señal de venta, ¿cómo evitan el impacto en el mercado?"
        result = classify_systemic_question(q)
        assert result == 'TYPE_A', f"Expected TYPE_A for mass selling question, got {result}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
