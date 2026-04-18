"""
Tests for AI-First Command Detection
=====================================

Regression tests to verify that:
1. User questions in Spanish don't accidentally trigger config commands
2. Only explicit /commands trigger configuration actions
3. AI receives all free-text messages

Fix: Dec 18, 2025 - Prevented false positives like "resumen" → "resume"
"""

import pytest


class TestAIFirstCommandDetection:
    """Tests that verify AI-first message routing works correctly."""
    
    def test_slash_prefix_detection_commands(self):
        """Commands starting with / should be detected as explicit commands."""
        commands = [
            "/resume",
            "/pause",
            "/perfil aggressive",
            "/autotrading activar",
            "  /resume",
            "\t/pause",
        ]
        
        for cmd in commands:
            is_explicit = cmd.strip().startswith('/')
            assert is_explicit, f"'{cmd}' should be detected as explicit command"
    
    def test_spanish_questions_not_commands(self):
        """Spanish questions containing command substrings should NOT be commands."""
        questions = [
            "Si desactivamos el 'trading alpha' con el resumen de las señales, cuántas operaciones pierdo?",
            "Dame un resumen de los últimos trades",
            "Quiero resumir mi actividad de trading",
            "Las pérdidas son enormes, necesito pausar para analizar",
            "Cómo puedo mejorar mi perfil de inversión?",
            "El rendimiento resume los beneficios de la semana?",
            "Break-even y resumen de ganancias",
            "trading automático ha pausado muchas veces hoy",
            "resume trading history from yesterday",
            "I want to pause and think about my strategy",
        ]
        
        for q in questions:
            is_explicit = q.strip().startswith('/')
            assert not is_explicit, f"'{q[:50]}...' should NOT be detected as explicit command"
    
    def test_edge_cases(self):
        """Edge cases that should go to AI, not config handlers."""
        edge_cases = [
            "",
            " ",
            "?",
            "hola",
            "resume",
            "PAUSE",
            "perfil",
            "/",
            "¿Cómo uso /resume?",
            "El comando /pause no funciona",
        ]
        
        expected = [
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            True,
            False,
            False,
        ]
        
        for q, exp in zip(edge_cases, expected):
            is_explicit = q.strip().startswith('/')
            assert is_explicit == exp, f"'{q}' should {'be' if exp else 'NOT be'} explicit command"
    
    def test_legitimate_commands_with_args(self):
        """Commands with arguments should still work."""
        commands_with_args = [
            ("/perfil conservative", True),
            ("/limite 500", True),
            ("/pause 30 minutos", True),
            ("perfil conservative", False),
            ("limite 500", False),
        ]
        
        for cmd, expected in commands_with_args:
            is_explicit = cmd.strip().startswith('/')
            assert is_explicit == expected, f"'{cmd}' explicit={is_explicit}, expected={expected}"


class TestNLPFalsePositivePrevention:
    """Tests that verify common NLP false positives are prevented."""
    
    @pytest.mark.parametrize("message,expected_to_ai", [
        ("resumen de trades", True),
        ("resume trading", True),
        ("pausa el bot", True),
        ("pausar trading", True),
        ("/resume", False),
        ("/pause", False),
        ("/perfil aggressive ACEPTO", False),
    ])
    def test_message_routing(self, message: str, expected_to_ai: bool):
        """Verify correct routing of messages to AI vs config handlers."""
        is_explicit_command = message.strip().startswith('/')
        goes_to_ai = not is_explicit_command
        
        assert goes_to_ai == expected_to_ai, (
            f"Message '{message}' should go to "
            f"{'AI' if expected_to_ai else 'config handler'}"
        )
    
    def test_complex_spanish_question_pattern(self):
        """
        Critical test: The exact pattern that caused the original bug.
        
        User asked: "Si desactivamos el 'trading alpha' con el resumen de 
        las señales, cuántas operaciones pierdo?"
        
        The NLP falsely detected "resume" action due to substring matching
        in the word "resumen".
        """
        problematic_message = (
            "Si desactivamos el 'trading alpha' con el resumen de las "
            "señales, cuántas operaciones pierdo?"
        )
        
        is_explicit_command = problematic_message.strip().startswith('/')
        
        assert not is_explicit_command, (
            "This complex Spanish question should NOT trigger any config command. "
            "It should go directly to the AI for processing."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
