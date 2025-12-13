"""
OMNIX V6.5.4d - Code Verification Tests

Validates Python syntax and critical imports without starting the Telegram bot.
These tests ensure code is ready for push to GitHub → Railway deploy.

Migrated from: scripts/verify_code.py
"""
import ast
import pytest
from pathlib import Path


class TestCriticalImports:
    """Test that critical OMNIX modules can be imported."""

    def test_physics_validator_import(self):
        """Verify quantum physics validator is importable."""
        from omnix_core.quantum.physics_validator import QuantumPhysicsValidator
        pv = QuantumPhysicsValidator()
        assert pv is not None

    def test_physics_validator_formulas_exist(self):
        """Verify all V5.0 and V6.0 formulas exist in physics_validator."""
        from omnix_core.quantum.physics_validator import QuantumPhysicsValidator
        pv = QuantumPhysicsValidator()
        
        required_formulas = [
            'quantum_channel_capacity',
            'private_capacity_thermal',
            'quantum_sharpe_ratio',
            'quantum_criticality',
            'pqc_decoherence_security',
            'vqe_bures_fisher',
            'side_channel_criticality'
        ]
        
        for formula_key in required_formulas:
            assert formula_key in pv.verified_formulas, f"Formula {formula_key} not found"

    def test_ai_prompts_import(self):
        """Verify AI prompts context manager is importable."""
        from omnix_services.ai_service.ai_prompts import PromptsContextManager
        pm = PromptsContextManager()
        assert pm is not None

    def test_conversational_brain_import(self):
        """Verify conversational brain is importable."""
        from omnix_services.ai_service.conversational_brain import ConversationalBrain
        assert ConversationalBrain is not None

    def test_database_service_import(self):
        """Verify database service is importable."""
        from omnix_services.database_service.database_service import DatabaseServiceEnterprise
        assert DatabaseServiceEnterprise is not None

    def test_version_banner_import(self):
        """Verify VERSION_BANNER is accessible from omnix_config."""
        from omnix_config import VERSION_BANNER
        assert VERSION_BANNER is not None
        assert "V6.5" in VERSION_BANNER


class TestMainSyntax:
    """Test main.py syntax validity."""

    def test_main_py_valid_syntax(self):
        """Verify main.py has valid Python syntax."""
        main_path = Path(__file__).parent.parent / "main.py"
        
        if not main_path.exists():
            pytest.skip("main.py not found")
        
        with open(main_path, 'r') as f:
            source = f.read()
        
        try:
            ast.parse(source)
        except SyntaxError as e:
            pytest.fail(f"main.py has syntax error: {e}")
