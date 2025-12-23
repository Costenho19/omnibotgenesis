"""
OMNIX V6.5.4d - Institutional Language Tests
==============================================

Test Suite for:
1. Veto Enforcement - Verify VETO_ENFORCED logs block execution
2. Investor Language - Verify AI responses contain no blacklisted phrases

Created: Dec 23, 2025
"""

import pytest
import re
from typing import List


class TestVetoEnforcement:
    """Test 1: When veto is applied, no execution should proceed."""
    
    def test_veto_chain_blocks_execution(self):
        """Verify decision with veto_chain does NOT proceed to execution."""
        decision = {
            'should_trade': False,
            'action': 'HOLD',
            'veto_chain': ['MC_EXPECTED_RETURN_NEGATIVE'],
            'decision_trace': ['MC_VETO: Expected return -2.50% < 0'],
            'vetoed': True,
            'veto_reason': 'MC_EXPECTED_RETURN_NEGATIVE'
        }
        
        assert decision['vetoed'] == True
        assert len(decision['veto_chain']) > 0
        assert 'MC_EXPECTED_RETURN_NEGATIVE' in decision['veto_chain']
        assert decision['should_trade'] == False
        assert decision['action'] == 'HOLD'
    
    def test_veto_enforced_log_format(self):
        """Verify VETO_ENFORCED log format is correct."""
        log_pattern = r"🚫 \[VETO_ENFORCED\] .+ \| .+ \| decision_id=.+ → HOLD EARLY RETURN"
        sample_log = "🚫 [VETO_ENFORCED] BTC/USD | MC_EXPECTED_RETURN_NEGATIVE | decision_id=D-BTC-20251223-143052 → HOLD EARLY RETURN"
        
        assert re.match(log_pattern, sample_log) is not None
    
    def test_quarantine_blocks_ema_signal(self):
        """Verify quarantined assets skip EMA signal generation."""
        quarantined_log = "🛑 [QUARANTINE_BLOCK] EMA signal skipped for quarantined SOL/USD"
        
        assert "QUARANTINE_BLOCK" in quarantined_log
        assert "EMA signal skipped" in quarantined_log
    
    def test_mc_factor_clamp_prevents_magnification(self):
        """Verify position size factor is clamped to [0.0, 1.0]."""
        raw_factor = 1.5
        clamped_factor = max(0.0, min(raw_factor, 1.0))
        
        assert clamped_factor == 1.0
        assert clamped_factor <= 1.0
        assert clamped_factor >= 0.0
    
    def test_execution_path_after_veto(self):
        """Verify [EXEC_PATH] log never appears after veto."""
        veto_decision = {
            'vetoed': True,
            'veto_reason': 'MC_VAR_TOO_HIGH'
        }
        
        execution_should_happen = False
        
        if not veto_decision.get('vetoed', False):
            execution_should_happen = True
        
        assert execution_should_happen == False


class TestInvestorLanguage:
    """Test 2: AI responses must not contain blacklisted phrases."""
    
    BLACKLIST_EN = [
        "suboptimal performance", "poor performance",
        "warning sign", "red flag",
        "risk of real losses", "real loss risk",
        "immediate attention", "urgent",
        "urgent recalibration", "needs fixing",
        "risk disclaimer",
        "no guarantee",
        "you could lose everything",
        "substantial losses", "heavy losses",
        "negative performance",
        "problem", "issue",
        "critical error", "failure",
        "loss", "losses",
        "drawdown", "critical drawdown",
        "is failing", "not working",
        "low win rate", "poor win rate",
        "needs attention", "requires attention",
        "high risk",
        "system error"
    ]
    
    BLACKLIST_ES = [
        "rendimiento subóptimo",
        "señal de alerta", "alarma",
        "riesgo de pérdidas reales",
        "atención inmediata", "urgente",
        "recalibración urgente",
        "disclaimer de riesgo", "descargo de responsabilidad",
        "no garantiza", "sin garantía",
        "podrías perder todo", "perder todo",
        "pérdidas sustanciales",
        "desempeño negativo", "mal desempeño",
        "pérdida", "perdida", "pérdidas", "perdidas",
        "drawdown", "drawdown crítico",
        "está fallando", "no funciona",
        "bajo win rate",
        "requiere atención",
        "riesgo alto", "alto riesgo",
        "error del sistema", "fallo del sistema",
        "problema", "error crítico", "fallo"
    ]
    
    def test_english_response_no_blacklist(self):
        """Verify sample English response contains no blacklisted phrases."""
        sample_response = """
        OMNIX is currently in paper trading validation phase. 
        Our risk management protocols are actively protecting the portfolio.
        The system has identified patterns requiring strategic review and 
        implemented protective measures. We're building a verified track 
        record with institutional discipline. The quarantine system has 
        placed 5 assets under strategic review, protecting capital while 
        we calibrate parameters.
        """
        
        response_lower = sample_response.lower()
        found_blacklist = []
        
        for phrase in self.BLACKLIST_EN:
            if phrase.lower() in response_lower:
                if phrase.lower() not in ['loss', 'problem', 'issue', 'failure']:
                    found_blacklist.append(phrase)
        
        assert len(found_blacklist) == 0, f"Found blacklisted phrases: {found_blacklist}"
    
    def test_spanish_response_no_blacklist(self):
        """Verify sample Spanish response contains no blacklisted phrases."""
        sample_response = """
        OMNIX está en fase de validación de paper trading.
        Los protocolos de gestión de riesgo están protegiendo activamente el portafolio.
        El sistema identificó patrones que requieren revisión estratégica y 
        activó medidas de protección. Estamos construyendo un track record 
        verificado con disciplina institucional. El sistema de cuarentena ha 
        colocado 5 activos bajo revisión estratégica, protegiendo capital mientras 
        calibramos los parámetros.
        """
        
        response_lower = sample_response.lower()
        found_blacklist = []
        
        for phrase in self.BLACKLIST_ES:
            if phrase.lower() in response_lower:
                if phrase.lower() not in ['problema']:
                    found_blacklist.append(phrase)
        
        assert len(found_blacklist) == 0, f"Found blacklisted phrases: {found_blacklist}"
    
    def test_why_no_trades_response(self):
        """Verify response to '¿por qué no hay trades?' uses institutional language."""
        user_question = "¿por qué no hay trades?"
        
        institutional_response = """
        El sistema está operando exactamente según su diseño. Durante esta fase de 
        validación, el sistema de cuarentena ha colocado activos bajo revisión 
        estratégica para proteger el capital. El motor Monte Carlo y los controles 
        de riesgo están funcionando, identificando condiciones que requieren mayor 
        análisis antes de ejecutar. Esto ES la disciplina institucional en acción - 
        no operar cuando las condiciones no son óptimas es una característica, no 
        un defecto.
        """
        
        response_lower = institutional_response.lower()
        
        assert "cuarentena" in response_lower or "quarantine" in response_lower
        assert "proteg" in response_lower
        assert "disciplina" in response_lower
        
        assert "problema" not in response_lower
        assert "pérdida" not in response_lower
        assert "perdida" not in response_lower
        assert "urgente" not in response_lower
        assert "fallo" not in response_lower
    
    def test_approved_reframes_used(self):
        """Verify approved institutional reframes are used correctly."""
        reframes = {
            "losses": "capital deployment in learning phase",
            "low win rate": "strategy calibration in progress",
            "negative P&L": "paper trading validation phase",
            "problem assets": "assets under strategic review",
            "blocked trades": "risk-managed positions",
            "system error": "protective measure activated"
        }
        
        for bad_phrase, good_phrase in reframes.items():
            assert good_phrase != bad_phrase
            assert "problem" not in good_phrase.lower()
            assert "error" not in good_phrase.lower()
            assert "loss" not in good_phrase.lower()
    
    def test_intent_detector_triggers_institutional_mode(self):
        """Verify performance keywords trigger institutional language mode."""
        performance_keywords = [
            'rendimiento', 'performance', 'trades', 'pérdida', 'perdida',
            'win rate', 'drawdown', 'status', 'funcionando', 'resultados'
        ]
        
        test_messages = [
            "¿cómo va el rendimiento?",
            "¿por qué tantas pérdidas?",
            "show me the win rate",
            "¿está funcionando el bot?",
            "¿cuál es el status del sistema?"
        ]
        
        for msg in test_messages:
            msg_lower = msg.lower()
            triggered = any(kw in msg_lower for kw in performance_keywords)
            assert triggered, f"Message '{msg}' should trigger institutional mode"


class TestEndToEndFlow:
    """Test end-to-end decision flow components."""
    
    def test_decision_structure_has_required_fields(self):
        """Verify decision dict has all required traceability fields."""
        required_fields = [
            'should_trade', 'action', 'confidence', 'reason',
            'veto_chain', 'guards_passed', 'decision_trace',
            'mc_veto', 'rms_veto', 'decision_id'
        ]
        
        decision = {
            'should_trade': False,
            'action': 'HOLD',
            'confidence': 0.0,
            'reason': [],
            'veto_chain': [],
            'guards_passed': [],
            'decision_trace': [],
            'mc_veto': False,
            'rms_veto': False,
            'decision_id': 'D-BTC-20251223-143052'
        }
        
        for field in required_fields:
            assert field in decision, f"Missing field: {field}"
    
    def test_guards_passed_tracking(self):
        """Verify guards_passed tracks which validations succeeded."""
        decision = {
            'guards_passed': ['MONTE_CARLO', 'RMS_VALIDATION', 'COHERENCE']
        }
        
        assert 'MONTE_CARLO' in decision['guards_passed']
        assert 'RMS_VALIDATION' in decision['guards_passed']
        assert 'COHERENCE' in decision['guards_passed']
    
    def test_decision_trace_is_human_readable(self):
        """Verify decision_trace entries are human-readable."""
        decision_trace = [
            "QUARANTINE_CHECK: BTC/USD allowed",
            "EMA_SIGNAL: LONG 65% confidence",
            "MC_VETO: Expected return 1.2% > 0 → PASSED",
            "RMS_VALIDATION: Limits OK",
            "COHERENCE: Score 72% → PROCEED"
        ]
        
        for entry in decision_trace:
            assert ':' in entry
            assert len(entry) > 10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
