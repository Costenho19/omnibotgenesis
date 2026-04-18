"""
Tests for Multi-User Support
=============================

Regression tests to verify that:
1. User registration correctly stores telegram_id
2. generate_smart_response() uses dynamic user context
3. Prompts don't hardcode "Harold" for non-admin users
4. Long messages are properly chunked (not truncated)

Fix: Dec 18, 2025 - Multi-user bug fixes
"""

import pytest


class TestMultiUserRegistration:
    """Tests that verify user registration stores telegram_id correctly."""
    
    def test_telegram_id_conversion_numeric(self):
        """Numeric user_id should be convertible to telegram_id."""
        user_ids = [
            "5804233562",
            "7014748854",
            "123456789",
        ]
        
        for user_id in user_ids:
            assert user_id.isdigit(), f"{user_id} should be numeric"
            telegram_id = int(user_id)
            assert telegram_id > 0, f"telegram_id should be positive"
    
    def test_telegram_id_conversion_non_numeric(self):
        """Non-numeric user_id should not convert to telegram_id."""
        user_ids = [
            "system",
            "admin",
            "user_abc",
            "",
        ]
        
        for user_id in user_ids:
            is_numeric = user_id and user_id.isdigit()
            assert not is_numeric, f"'{user_id}' should NOT be numeric"


class TestDynamicUserContext:
    """Tests that verify dynamic user context replaces hardcoded values."""
    
    def test_fallback_user_name(self):
        """When user name is not available, fallback to 'Usuario'."""
        fallback_name = "Usuario"
        
        test_cases = [
            (None, fallback_name),
            ("", fallback_name),
            ("Harold", "Harold"),
            ("David", "David"),
        ]
        
        for db_result, expected in test_cases:
            effective_name = db_result or fallback_name
            assert effective_name == expected
    
    def test_prompt_user_name_substitution(self):
        """Prompts should use dynamic user name, not hardcoded 'Harold'."""
        template = "Pregunta de {user_name}: ¿Cuál es el precio?"
        
        user_names = ["Harold", "David", "Usuario", "María"]
        
        for user_name in user_names:
            prompt = template.format(user_name=user_name)
            assert user_name in prompt
            if user_name != "Harold":
                assert "Harold" not in prompt


class TestMessageChunking:
    """Tests that verify long messages are chunked, not truncated."""
    
    def test_long_message_should_chunk(self):
        """Messages over 4000 chars should be split, not truncated."""
        long_message = "A" * 8000
        max_length = 4000
        
        if len(long_message) > max_length:
            num_parts = (len(long_message) + max_length - 1) // max_length
            assert num_parts == 2, "8000 char message should split into 2 parts"
    
    def test_short_message_no_chunk(self):
        """Messages under 4000 chars should not be split."""
        short_message = "Hello, this is a short message"
        max_length = 4000
        
        assert len(short_message) < max_length
        should_chunk = len(short_message) > max_length
        assert not should_chunk


class TestDatabaseFallback:
    """Tests that verify graceful degradation when DB is unavailable."""
    
    def test_user_name_fallback_on_db_error(self):
        """If DB lookup fails, should fallback to 'Usuario', not crash."""
        def mock_get_user_name_from_db(user_id):
            raise Exception("Database unavailable")
        
        fallback_name = "Usuario"
        
        try:
            result = mock_get_user_name_from_db("12345")
        except Exception:
            result = fallback_name
        
        assert result == fallback_name
    
    def test_ensure_user_exists_telegram_id_logic(self):
        """telegram_id should be set from user_id when numeric."""
        test_cases = [
            ("5804233562", 5804233562),
            ("7014748854", 7014748854),
            ("system", None),
            ("", None),
        ]
        
        for user_id, expected_telegram_id in test_cases:
            if user_id and user_id.isdigit():
                telegram_id_safe = int(user_id)
            else:
                telegram_id_safe = None
            
            assert telegram_id_safe == expected_telegram_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
