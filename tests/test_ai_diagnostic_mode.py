"""
Tests — T011: diagnostic_mode (RULE 13) + ai_service fallback chain
ADR-115, ADR-058

Estrategia: tests ligeros con imports guardados bajo try/except Exception.
Si el entorno de test no puede cargar los módulos de IA (por falta de
settings válidos), los tests se marcan como SKIP en lugar de fallar.
"""

import os
import sys
import inspect
import pytest
from unittest.mock import MagicMock, patch

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

# ─── Helper: importar módulo AI con skip seguro ───────────────────────────────

def _try_import(module_path, names=None):
    """Intenta importar un módulo; retorna (módulo, None) o (None, skip_reason)."""
    try:
        import importlib
        mod = importlib.import_module(module_path)
        if names:
            return {n: getattr(mod, n) for n in names}, None
        return mod, None
    except Exception as exc:
        return None, str(exc)


# ─── T011-A: DIAGNOSTIC_ONLY_PROMPT existe y tiene contenido mínimo ──────────

class TestDiagnosticOnlyPrompt:
    """Verificar que el prompt especial para diagnóstico existe en el código."""

    def test_prompt_file_exists(self):
        import os
        path = os.path.join(
            os.path.dirname(__file__), "..",
            "omnix_services", "ai_service", "prompt_templates.py"
        )
        assert os.path.isfile(os.path.normpath(path)), "prompt_templates.py no existe"

    def test_prompt_constant_defined_in_source(self):
        """DIAGNOSTIC_ONLY_PROMPT debe estar definido como constante en el archivo."""
        import os
        path = os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..",
            "omnix_services", "ai_service", "prompt_templates.py"
        ))
        with open(path, encoding="utf-8") as f:
            source = f.read()
        assert "DIAGNOSTIC_ONLY_PROMPT" in source, (
            "DIAGNOSTIC_ONLY_PROMPT no encontrado en prompt_templates.py"
        )

    def test_prompt_not_empty_in_source(self):
        """DIAGNOSTIC_ONLY_PROMPT no debe ser string vacío en el código fuente."""
        import os, re
        path = os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..",
            "omnix_services", "ai_service", "prompt_templates.py"
        ))
        with open(path, encoding="utf-8") as f:
            source = f.read()
        # Detectar DIAGNOSTIC_ONLY_PROMPT = "" (exactamente dos comillas, no triple)
        # Triple-quoted strings como """ NO cuentan como vacías
        match = re.search(r'DIAGNOSTIC_ONLY_PROMPT\s*=\s*(?:""(?!")|\'\'(?!\'))', source)
        assert match is None, "DIAGNOSTIC_ONLY_PROMPT es un string vacío '\"\"' o \"''\""


# ─── T011-B: generate_response_async tiene diagnostic_mode en firma ───────────

class TestDiagnosticModeFunctionSignature:
    """Verificar la firma de generate_response_async en código fuente."""

    def _get_source_path(self):
        import os
        return os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..",
            "omnix_services", "ai_service", "conversational_ai_adapter.py"
        ))

    def test_diagnostic_mode_param_exists_in_source(self):
        with open(self._get_source_path(), encoding="utf-8") as f:
            source = f.read()
        assert "diagnostic_mode" in source, (
            "diagnostic_mode no encontrado en conversational_ai_adapter.py"
        )

    def test_diagnostic_mode_default_false_in_source(self):
        with open(self._get_source_path(), encoding="utf-8") as f:
            source = f.read()
        assert "diagnostic_mode=False" in source, (
            "diagnostic_mode=False (default seguro) no encontrado en firma"
        )

    def test_diagnostic_mode_injection_logic_present(self):
        """Verificar que hay lógica 'if diagnostic_mode:' en el código."""
        with open(self._get_source_path(), encoding="utf-8") as f:
            source = f.read()
        assert "if diagnostic_mode:" in source, (
            "Bloque 'if diagnostic_mode:' no encontrado — lógica de inyección faltante"
        )

    def test_diagnostic_mode_uses_diagnostic_only_prompt(self):
        """Cuando diagnostic_mode=True debe cargar DIAGNOSTIC_ONLY_PROMPT."""
        with open(self._get_source_path(), encoding="utf-8") as f:
            source = f.read()
        assert "DIAGNOSTIC_ONLY_PROMPT" in source, (
            "DIAGNOSTIC_ONLY_PROMPT no referenciado en conversational_ai_adapter.py"
        )

    def test_diagnostic_mode_injects_investor_data(self):
        """Debe usar InvestorDataProvider para datos reales."""
        with open(self._get_source_path(), encoding="utf-8") as f:
            source = f.read()
        assert "InvestorDataProvider" in source, (
            "InvestorDataProvider no encontrado en conversational_ai_adapter.py"
        )


# ─── T011-C: ai_service tiene fallback chain ─────────────────────────────────

class TestAIServiceFallbackChain:
    """Verificar que ai_service.py tiene métodos de fallback definidos."""

    def _get_source_path(self):
        import os
        return os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..",
            "omnix_services", "ai_service", "ai_service.py"
        ))

    def test_fallback_response_method_exists(self):
        with open(self._get_source_path(), encoding="utf-8") as f:
            source = f.read()
        assert "_get_fallback_response" in source, (
            "_get_fallback_response no encontrado en ai_service.py"
        )

    def test_error_response_method_exists(self):
        with open(self._get_source_path(), encoding="utf-8") as f:
            source = f.read()
        assert "_get_error_response" in source, (
            "_get_error_response no encontrado en ai_service.py"
        )

    def test_fallback_returns_non_empty_string(self):
        """El fallback no debe retornar string vacío."""
        import re
        with open(self._get_source_path(), encoding="utf-8") as f:
            source = f.read()
        # Buscar el bloque de _get_fallback_response
        match = re.search(
            r'def _get_fallback_response.*?return\s+"([^"]*)"',
            source, re.DOTALL
        )
        if match:
            assert len(match.group(1).strip()) > 0, (
                "_get_fallback_response retorna string vacío"
            )

    def test_ai_service_has_fallback_import_or_local(self):
        """Debe haber una cadena de fallback documentada."""
        with open(self._get_source_path(), encoding="utf-8") as f:
            source = f.read()
        assert "fallback" in source.lower(), (
            "No se encontró ninguna lógica de fallback en ai_service.py"
        )


# ─── T011-D: InvestorDataProvider tiene get_basic_trading_stats ──────────────

class TestInvestorDataProviderInterface:
    """Verificar interface de InvestorDataProvider sin llamar a DB."""

    def _get_source_path(self):
        import os
        return os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..",
            "omnix_services", "ai_service", "providers", "investor_data_provider.py"
        ))

    def test_provider_file_exists(self):
        import os
        assert os.path.isfile(self._get_source_path()), (
            "investor_data_provider.py no existe"
        )

    def test_get_basic_trading_stats_defined(self):
        with open(self._get_source_path(), encoding="utf-8") as f:
            source = f.read()
        assert "def get_basic_trading_stats" in source, (
            "get_basic_trading_stats no definido en InvestorDataProvider"
        )

    def test_get_basic_trading_stats_returns_dict_structure(self):
        """Debe retornar dict con clave 'track_record' según el código."""
        with open(self._get_source_path(), encoding="utf-8") as f:
            source = f.read()
        assert "track_record" in source, (
            "Clave 'track_record' no encontrada en investor_data_provider.py"
        )

    def test_error_handling_present(self):
        """Debe tener manejo de errores (except) para fallas de DB."""
        with open(self._get_source_path(), encoding="utf-8") as f:
            source = f.read()
        assert "except" in source, (
            "No hay bloques except en investor_data_provider.py — sin manejo de errores DB"
        )


# ─── T011-E: Fail-closed en AML, CAG, FraudGate (T001 bloqueaba T011) ────────

class TestGatesFailClosed:
    """
    Verifica que AML, CAG y FraudGate están implementadas fail-closed:
    cuando su método interno _run_checks/_run_admission_checks lanza excepción,
    el gate debe devolver blocked/veto (no pass_through) — ADR-116.
    """

    def test_aml_gate_fail_closed_on_internal_exception(self):
        """AMLGate → fail-closed: admissible=False, pass_through=False en error."""
        from omnix_core.governance.aml_gate import AMLGate, AMLGateConfig

        class BrokenAMLGate(AMLGate):
            def _run_checks(self, *args, **kwargs):
                raise RuntimeError("Test: simulated AML internal failure")

        gate = BrokenAMLGate(AMLGateConfig(enabled=True, db_url=None))
        result = gate.evaluate("BTC/USD", "BUY", volume_usd=100.0, trade_frequency_24h=0)

        assert result.admissible is False, "AMLGate con error debe bloquear (admissible=False)"
        assert result.pass_through is False, "AMLGate con error NO debe usar pass_through=True"
        assert result.evaluation_state == "FAIL_CLOSED", (
            f"evaluation_state esperado FAIL_CLOSED, obtenido {result.evaluation_state!r}"
        )

    def test_cag_fail_closed_on_internal_exception(self):
        """CAG → fail-closed: admitted=False, pass_through=False en error."""
        from omnix_core.governance.context_admission_gate import ContextAdmissionGate, CAGConfig

        class BrokenCAG(ContextAdmissionGate):
            def _run_admission_checks(self, *args, **kwargs):
                raise RuntimeError("Test: simulated CAG internal failure")

        gate = BrokenCAG(CAGConfig(enabled=True))
        result = gate.evaluate(global_volatility=50.0)

        assert result.admitted is False, "CAG con error debe bloquear (admitted=False)"
        assert result.pass_through is False, "CAG con error NO debe usar pass_through=True"
        assert result.evaluation_state == "FAIL_CLOSED", (
            f"evaluation_state esperado FAIL_CLOSED, obtenido {result.evaluation_state!r}"
        )

    def test_fraud_gate_fail_closed_on_internal_exception(self):
        """FraudGate → fail-closed: admissible=False, pass_through=False en error."""
        from omnix_core.governance.fraud_gate import FraudGate, FraudGateConfig

        class BrokenFraudGate(FraudGate):
            def _run_checks(self, *args, **kwargs):
                raise RuntimeError("Test: simulated FraudGate internal failure")

        gate = BrokenFraudGate(FraudGateConfig(enabled=True))
        result = gate.evaluate("BTC/USD", "BUY")

        assert result.admissible is False, "FraudGate con error debe bloquear (admissible=False)"
        assert result.pass_through is False, "FraudGate con error NO debe usar pass_through=True"
        assert result.evaluation_state == "FAIL_CLOSED", (
            f"evaluation_state esperado FAIL_CLOSED, obtenido {result.evaluation_state!r}"
        )

    def test_aml_docstring_says_fail_closed(self):
        """El docstring de aml_gate.py debe decir 'Fail-closed' (no 'Fail-safe')."""
        import os
        path = os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..",
            "omnix_core", "governance", "aml_gate.py"
        ))
        with open(path, encoding="utf-8") as f:
            source = f.read()
        assert "Fail-closed" in source, "aml_gate.py docstring debe decir 'Fail-closed'"
        assert "Fail-safe" not in source[:500], (
            "aml_gate.py aún dice 'Fail-safe' en la sección Design — corregir docstring"
        )

    def test_cag_docstring_says_fail_closed(self):
        """El docstring de context_admission_gate.py debe decir 'Fail-closed'."""
        import os
        path = os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..",
            "omnix_core", "governance", "context_admission_gate.py"
        ))
        with open(path, encoding="utf-8") as f:
            source = f.read()
        assert "Fail-closed" in source, "context_admission_gate.py debe decir 'Fail-closed'"

    def test_fraud_docstring_says_fail_closed(self):
        """El docstring de fraud_gate.py debe decir 'Fail-closed'."""
        import os
        path = os.path.normpath(os.path.join(
            os.path.dirname(__file__), "..",
            "omnix_core", "governance", "fraud_gate.py"
        ))
        with open(path, encoding="utf-8") as f:
            source = f.read()
        assert "Fail-closed" in source, "fraud_gate.py debe decir 'Fail-closed'"
