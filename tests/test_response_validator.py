"""
Tests for AI Response Validator

Validates detection of incomplete/corrupted AI responses.
"""

import pytest
from omnix_services.ai_service.response_validator import (
    is_response_incomplete,
    validate_and_log_response,
    sanitize_incomplete_response,
    create_retry_prompt,
)


class TestIsResponseIncomplete:
    """Test detection of incomplete responses."""
    
    def test_empty_response_is_incomplete(self):
        """Empty response should be flagged."""
        is_incomplete, reason = is_response_incomplete("")
        assert is_incomplete is True
        assert "EMPTY_RESPONSE" in reason
    
    def test_none_response_is_incomplete(self):
        """None response should be flagged."""
        is_incomplete, reason = is_response_incomplete(None)
        assert is_incomplete is True
    
    def test_too_short_response_is_incomplete(self):
        """Very short response should be flagged."""
        is_incomplete, reason = is_response_incomplete("Sí.")
        assert is_incomplete is True
        assert "TOO_SHORT" in reason or "TOO_FEW_WORDS" in reason
    
    def test_lo_mismo_pattern_is_incomplete(self):
        """Response ending with 'lo mismo' should be flagged."""
        response = "*1. Primer punto explicado con suficiente detalle para pasar el límite de caracteres mínimo. *2. lo mismo"
        is_incomplete, reason = is_response_incomplete(response)
        assert is_incomplete is True
        assert "TRUNCATION_PATTERN" in reason or "ENDS_WITH_LO_MISMO" in reason or "INCOMPLETE" in reason
    
    def test_numbered_item_cutoff_is_incomplete(self):
        """Response ending with just a number is incomplete."""
        response = "Aquí hay algunos puntos importantes sobre el tema. *1. Primer punto. *2."
        is_incomplete, reason = is_response_incomplete(response)
        assert is_incomplete is True
    
    def test_trailing_conjunction_is_incomplete(self):
        """Response ending with conjunction is incomplete."""
        response = "Este es un análisis muy completo del sistema OMNIX que incluye varios componentes importantes y"
        is_incomplete, reason = is_response_incomplete(response)
        assert is_incomplete is True
    
    def test_valid_response_passes(self):
        """A complete, valid response should pass."""
        response = """
        OMNIX es un sistema de trading algorítmico que utiliza múltiples capas de 
        validación para proteger el capital de los inversores. El sistema implementa
        vetos de Monte Carlo, análisis de Black Swan, y coherencia de señales.
        
        La arquitectura incluye:
        *1. Motor de decisiones cuantitativo
        *2. Sistema de gestión de riesgo
        *3. Validación de señales en tiempo real
        
        El objetivo es mantener el capital preservado mientras se buscan oportunidades
        de trading con expectativa positiva.
        """
        is_incomplete, reason = is_response_incomplete(response)
        assert is_incomplete is False
        assert reason == "OK"
    
    def test_real_truncation_case_lo_mismo(self):
        """Real case from user report: response ends with 'lo mismo'."""
        response = """Claro, Harold. Para responder a tu pregunta sobre cómo vamos a 
        "cambiar el mercado", es crucial entender que OMNIX no busca manipular o 
        influir en el mercado en sí. Nuestra misión es ofrecer una infraestructura 
        de control de riesgo robusta que permita a nuestros inversores navegar y 
        prosperar en las condiciones del mercado, sean cuales sean. 
        *1. Análisis Inmediato* Actualmente, el mercado de criptomonedas se 
        caracteriza por una alta volatilidad. *2. lo mismo"""
        
        is_incomplete, reason = is_response_incomplete(response)
        assert is_incomplete is True


class TestSanitizeIncompleteResponse:
    """Test sanitization of incomplete responses."""
    
    def test_removes_lo_mismo_ending(self):
        """Should remove 'lo mismo' pattern."""
        response = "Punto uno explicado. *2. lo mismo"
        sanitized = sanitize_incomplete_response(response)
        assert "lo mismo" not in sanitized
    
    def test_removes_trailing_number(self):
        """Should remove trailing numbered item."""
        response = "Información importante. *3."
        sanitized = sanitize_incomplete_response(response)
        assert not sanitized.endswith("*3.")
    
    def test_adds_truncation_notice(self):
        """Should add notice for truncated responses."""
        response = "Este es un análisis parcial del sistema con información útil para el usuario."
        sanitized = sanitize_incomplete_response(response)
        assert "resumida" in sanitized or sanitized.endswith(".")
    
    def test_empty_returns_fallback_message(self):
        """Empty input should return fallback message."""
        sanitized = sanitize_incomplete_response("")
        assert "reformular" in sanitized or len(sanitized) > 0


class TestCreateRetryPrompt:
    """Test retry prompt generation."""
    
    def test_includes_original_message(self):
        """Retry prompt should include original message."""
        original = "¿Cómo funciona OMNIX?"
        prompt = create_retry_prompt(original, "TRUNCATION")
        assert original in prompt
    
    def test_includes_critical_instructions(self):
        """Retry prompt should have instructions for complete response."""
        prompt = create_retry_prompt("pregunta", "INCOMPLETE")
        assert "COMPLETA" in prompt or "completa" in prompt.lower()


class TestValidateAndLogResponse:
    """Test validation with logging."""
    
    def test_valid_response_returns_true(self):
        """Valid response should return is_valid=True."""
        response = """Este es un análisis completo del sistema OMNIX que incluye 
        todas las funcionalidades principales y está bien estructurado con 
        información relevante para el usuario."""
        
        is_valid, reason, sanitized = validate_and_log_response(
            response, "test query", "gemini"
        )
        assert is_valid is True
        assert reason == "OK"
    
    def test_invalid_response_returns_false(self):
        """Invalid response should return is_valid=False."""
        response = "*1. punto *2."
        
        is_valid, reason, sanitized = validate_and_log_response(
            response, "test query", "gemini"
        )
        assert is_valid is False
        assert reason != "OK"
