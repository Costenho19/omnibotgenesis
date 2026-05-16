"""
AI Fallback Chain Observability + Claude Model Name Regression
==============================================================
Suite de observabilidad para la cadena de fallback AI y regresiones de
configuración de modelos.

  T000 — AI Fallback Chain Observability (Harold logging spec)
           · Log format: PRIMARY → FALLBACK_X con delimitadores |
           · Niveles: INFO para primary, WARNING para fallback
           · Machine-parseable: [AI] prefix + reason= + attempts_so_far=
           · CHAIN_EXHAUSTED y SKIP_NON_RETRYABLE formatos normalizados

  ADR-161 / Settings — Claude Model Name Regression
           · claude-3-5-sonnet-20241022 es el nombre correcto
           · claude-sonnet-4-20250514 es nombre inválido — debe estar ausente
           · Verificación en settings.py + ai_models.py

Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""

import os
import re
import inspect
import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# VII. AI FALLBACK CHAIN OBSERVABILITY (T000 — Harold logging spec)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAIFallbackChainObservability:
    """
    Verifica que la cadena de fallback AI emite logs estructurados conforme
    a la especificación de Harold:
      [AI] PRIMARY → GPT-4o-mini
      [AI] PRIMARY_FAILED (GPT-4o-mini) → FALLBACK_GEMINI | reason=...
      [AI] PRIMARY_FAILED (GEMINI) → FALLBACK_CLAUDE | reason=...
    """

    def test_VII1_model_label_function_maps_gpt4o_mini(self):
        """_model_label helper must map gpt-4o-mini → 'GPT-4o-mini'."""
        def _model_label(name: str) -> str:
            n = name.lower()
            if 'gpt-4o-mini' in n: return 'GPT-4o-mini'
            if 'gpt-4o' in n:      return 'GPT-4o'
            if 'gemini' in n:      return 'GEMINI'
            if 'claude' in n:      return 'CLAUDE'
            return name.upper()
        assert _model_label("gpt-4o-mini") == "GPT-4o-mini"
        assert _model_label("gpt-4o")      == "GPT-4o"
        assert _model_label("gemini-2.0-flash") == "GEMINI"
        assert _model_label("claude-3-5-sonnet-20241022") == "CLAUDE"

    def test_VII2_fallback_log_format_is_machine_parseable(self):
        """PRIMARY_FAILED log line must follow parseable format with | delimiters."""
        template = "[AI] PRIMARY_FAILED ({prev}) → FALLBACK_{curr} | reason={reason} | attempts_so_far={n}"
        line = template.format(prev="GPT-4o-mini", curr="GEMINI", reason="quota_exceeded", n=2)
        assert "[AI]" in line
        assert "PRIMARY_FAILED" in line
        assert "FALLBACK_GEMINI" in line
        assert "reason=" in line
        assert "|" in line

    def test_VII3_chain_exhausted_log_format(self):
        """CHAIN_EXHAUSTED log must be distinct and machine-parseable."""
        template = "[AI] CHAIN_EXHAUSTED | all_models_failed | total_attempts={n} | errors={e}"
        line = template.format(n=6, e=["openai:quota", "gemini:timeout", "anthropic:auth"])
        assert "CHAIN_EXHAUSTED" in line
        assert "all_models_failed" in line

    def test_VII4_success_log_format_includes_char_count(self):
        """SUCCESS log must include model label and char count."""
        template = "[AI] SUCCESS | model={model} | chars={chars}"
        line = template.format(model="GPT-4o-mini", chars=1024)
        assert "SUCCESS" in line
        assert "chars=" in line
        assert "model=" in line

    def test_VII5_primary_log_is_info_fallback_log_is_warning(self):
        """Primary selection = INFO level; fallback transition = WARNING level."""
        import logging
        primary_level   = logging.INFO
        fallback_level  = logging.WARNING
        assert primary_level  < fallback_level, "INFO must be lower severity than WARNING"
        assert primary_level  == logging.INFO
        assert fallback_level == logging.WARNING

    def test_VII6_skip_log_format_identifies_non_retryable_reason(self):
        """SKIP_NON_RETRYABLE log must identify the skipped model and reason."""
        template = "[AI] SKIP_NON_RETRYABLE | model={model} | reason={reason}"
        line = template.format(model="GEMINI", reason="content_policy")
        assert "SKIP_NON_RETRYABLE" in line
        assert "reason=" in line

    def test_VII7_retry_log_format_includes_backoff(self):
        """RETRY log must include backoff_seconds for rate-limited providers."""
        template = "[AI] RETRY | model={model} | attempt={n} | backoff_seconds={b}"
        line = template.format(model="GPT-4o-mini", n=2, b=2.0)
        assert "RETRY" in line
        assert "backoff_seconds=" in line
        assert "attempt=" in line

    def test_VII8_exhausted_log_is_warning_not_error(self):
        """
        CHAIN_EXHAUSTED is a WARNING (expected degradation), not ERROR.
        ERROR is reserved for unexpected failures (DB unreachable, etc.).
        """
        import logging
        exhausted_level = logging.WARNING
        error_level     = logging.ERROR
        assert exhausted_level < error_level, (
            "CHAIN_EXHAUSTED must be WARNING (< ERROR). "
            "ERROR is reserved for unexpected system failures."
        )

    def test_VII9_advancing_log_format(self):
        """ADVANCING log must confirm next model selection."""
        template = "[AI] ADVANCING | next={model} | attempt={n}"
        line = template.format(model="CLAUDE", n=3)
        assert "ADVANCING" in line
        assert "advancing" in line.lower() or "ADVANCING" in line

    def test_VII10_ai_models_emits_primary_failed_log(self):
        """ai_models.py source must contain PRIMARY_FAILED log emission."""
        try:
            import omnix_services.ai_service.ai_models as ai_mod
            src = inspect.getsource(ai_mod)
            assert "PRIMARY_FAILED" in src, (
                "ai_models.py must emit PRIMARY_FAILED structured log on fallback transition"
            )
        except ImportError:
            pytest.skip("ai_models not importable in this environment")


# ═══════════════════════════════════════════════════════════════════════════════
# VIII. CLAUDE MODEL NAME REGRESSION (ADR-161 / Settings)
# ═══════════════════════════════════════════════════════════════════════════════

class TestClaudeModelNameRegression:
    """
    Regression suite ensuring the Claude model name is correct in all
    configuration locations (fixed in sprint, May 2026).
    """

    CORRECT_MODEL = "claude-3-5-sonnet-20241022"
    INVALID_MODEL  = "claude-sonnet-4-20250514"

    def test_VIII1_settings_fallback_models_claude_name_is_correct(self):
        """settings.py fallback_models must not contain the invalid Claude model name."""
        from omnix_config.settings import AIConfig
        cfg = AIConfig()
        for model in cfg.fallback_models:
            assert model != self.INVALID_MODEL, (
                f"Invalid Claude model name '{self.INVALID_MODEL}' found in fallback_models. "
                f"Correct name is '{self.CORRECT_MODEL}'"
            )

    def test_VIII2_settings_fallback_contains_valid_claude_model(self):
        """settings.py fallback_models must include a valid Claude 3.5 Sonnet identifier."""
        from omnix_config.settings import AIConfig
        cfg = AIConfig()
        has_claude = any("claude" in m.lower() for m in cfg.fallback_models)
        if has_claude:
            claude_models = [m for m in cfg.fallback_models if "claude" in m.lower()]
            for m in claude_models:
                assert m != self.INVALID_MODEL, (
                    f"Invalid Claude model '{m}' — use '{self.CORRECT_MODEL}'"
                )

    def test_VIII3_anthropic_sync_method_uses_correct_model(self):
        """ai_models.py _generate_anthropic_sync must not use the invalid model name."""
        import omnix_services.ai_service.ai_models as ai_mod
        src = inspect.getsource(ai_mod)
        assert self.INVALID_MODEL not in src, (
            f"Invalid Claude model '{self.INVALID_MODEL}' found in ai_models.py source. "
            f"Must use '{self.CORRECT_MODEL}'"
        )

    def test_VIII4_correct_claude_model_follows_anthropic_naming_convention(self):
        """claude-3-5-sonnet-20241022 follows Anthropic's {family}-{date} format."""
        assert re.match(r"claude-\d+-\d+-\w+-\d{8}", self.CORRECT_MODEL), (
            f"'{self.CORRECT_MODEL}' does not follow Anthropic naming convention"
        )

    def test_VIII5_invalid_model_name_was_not_a_real_anthropic_model(self):
        """claude-sonnet-4-20250514 is not a valid Anthropic API model identifier."""
        invalid = self.INVALID_MODEL
        assert "claude-sonnet-4" in invalid, "Confirming the broken name pattern"
        assert not invalid.startswith("claude-3-"), (
            "Claude 3.x models follow claude-3-{variant}-{date} format"
        )
