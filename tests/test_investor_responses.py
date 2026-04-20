"""
Test suite for Investor Response Engine
Created: Dec 31, 2025

Verifies that the system gives coherent, institutional-grade responses
to critical investor questions without common pitch errors.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from omnix_services.ai_service.investor_responses import (
    InvestorResponseEngine,
    InvestorQueryType,
    INVESTOR_RESPONSES
)


class TestInvestorResponseEngine:
    """Tests for InvestorResponseEngine detection and responses"""
    
    @pytest.fixture
    def engine(self):
        return InvestorResponseEngine()
    
    def test_all_query_types_have_responses(self):
        """Every InvestorQueryType must have a corresponding response"""
        for query_type in InvestorQueryType:
            assert query_type in INVESTOR_RESPONSES, f"Missing response for {query_type}"
    
    def test_detect_system_inactivity_spanish(self, engine):
        """Detect questions about system inactivity in Spanish"""
        test_messages = [
            "El sistema casi nunca opera, ¿por qué?",
            "¿Por qué hay tan pocas operaciones?",
            "El bot está inactivo",
            "Casi no opera nunca",
        ]
        for msg in test_messages:
            result = engine.detect_query_type(msg)
            assert result == InvestorQueryType.SYSTEM_INACTIVITY, f"Failed for: {msg}"
    
    def test_detect_system_inactivity_english(self, engine):
        """Detect questions about system inactivity in English"""
        test_messages = [
            "The system rarely trades",
            "Why so few trades?",
            "System seems inactive",
        ]
        for msg in test_messages:
            result = engine.detect_query_type(msg)
            assert result == InvestorQueryType.SYSTEM_INACTIVITY, f"Failed for: {msg}"
    
    def test_detect_over_filtering_spanish(self, engine):
        """Detect questions about over-filtering in Spanish"""
        test_messages = [
            "El sistema filtra demasiado",
            "Bloquea todo con los vetos",
            "Es demasiado conservador",
        ]
        for msg in test_messages:
            result = engine.detect_query_type(msg)
            assert result == InvestorQueryType.OVER_FILTERING, f"Failed for: {msg}"
    
    def test_detect_why_not_buy_btc(self, engine):
        """Detect 'why not just buy BTC' questions"""
        test_messages = [
            "¿Por qué no simplemente comprar BTC y holdear?",
            "why not buy bitcoin",   # "buy and hold" triggers ADR-024 → None; use direct phrase
            "Better to just hodl",
        ]
        for msg in test_messages:
            result = engine.detect_query_type(msg)
            assert result == InvestorQueryType.WHY_NOT_BUY_BTC, f"Failed for: {msg}"
    
    def test_response_contains_no_blacklisted_phrases(self):
        """Verify responses don't contain blacklisted phrases"""
        blacklisted = [
            "refinando", "ajustando parámetros", "aprendiendo",
            "refining", "adjusting parameters", "learning phase",
            "problema", "problem", "error", "failure",
            "underperforming", "suboptimal", "poor performance",
        ]
        
        for query_type, response in INVESTOR_RESPONSES.items():
            full_response = response.format().lower()
            for phrase in blacklisted:
                assert phrase not in full_response, \
                    f"Blacklisted phrase '{phrase}' found in {query_type} response"
    
    def test_system_inactivity_response_has_killer_phrase(self):
        """Verify SYSTEM_INACTIVITY response contains the killer phrase"""
        response = INVESTOR_RESPONSES[InvestorQueryType.SYSTEM_INACTIVITY]
        full_text = response.format().lower()
        
        killer_phrases = [
            "few high-quality windows",
            "concentration",
            "discipline",
        ]
        
        found = any(phrase in full_text for phrase in killer_phrases)
        assert found, "SYSTEM_INACTIVITY response missing killer phrase about concentration/discipline"
    
    def test_over_filtering_response_frames_as_feature(self):
        """Verify OVER_FILTERING response frames filtering as a feature"""
        response = INVESTOR_RESPONSES[InvestorQueryType.OVER_FILTERING]
        full_text = response.format().lower()
        
        assert "feature" in full_text, "Response should frame filtering as a feature"
        assert "type ii error" in full_text or "missed opportunities" in full_text, \
            "Response should mention preferring missed opportunities over losses"
    
    def test_why_not_btc_response_addresses_risk(self):
        """Verify WHY_NOT_BUY_BTC response addresses downside risk without blacklisted terms"""
        response = INVESTOR_RESPONSES[InvestorQueryType.WHY_NOT_BUY_BTC]
        full_text = response.format().lower()
        
        assert "drawdown" not in full_text, "Response should NOT contain blacklisted word 'drawdown'"
        
        assert "77%" in full_text or "peak-to-trough" in full_text, \
            "Response should reference BTC's historical decline"
        assert "capital protection" in full_text or "risk management" in full_text, \
            "Response should mention capital protection"
    
    def test_investor_score_calculation(self, engine):
        """Test investor context scoring"""
        test_cases = [
            ("Quiero invertir en el proyecto", True),  # Should activate
            ("¿Cómo funciona el trading?", False),  # Too generic
            ("Due diligence para inversión institucional", True),  # Clear investor context
        ]
        
        for message, should_activate in test_cases:
            score, words = engine.calculate_investor_score(message)
            info = engine.get_investor_context_info(message)
            assert info["activates_institutional"] == should_activate, \
                f"Expected {should_activate} for: {message}"
    
    def test_all_responses_have_evidence_section(self):
        """Every response must have concrete evidence"""
        for query_type, response in INVESTOR_RESPONSES.items():
            assert len(response.evidence) > 50, \
                f"{query_type} response has insufficient evidence"
    
    def test_all_responses_have_closing_statement(self):
        """Every response must have a closing statement"""
        for query_type, response in INVESTOR_RESPONSES.items():
            assert len(response.closing) > 20, \
                f"{query_type} response has insufficient closing"


class TestPromptTemplatesRules:
    """Tests for the new investor response rules in prompt_templates"""
    
    def test_prompt_templates_importable(self):
        """Verify prompt_templates module is importable"""
        from omnix_services.ai_service.prompt_templates import MASTER_SYSTEM_PROMPT
        assert "INVESTOR RESPONSE RULES" in MASTER_SYSTEM_PROMPT
    
    def test_prompt_has_rule_no_unverifiable_claims(self):
        """Verify Rule 1 exists in prompt"""
        from omnix_services.ai_service.prompt_templates import MASTER_SYSTEM_PROMPT
        assert "NO UNVERIFIABLE CLAIMS" in MASTER_SYSTEM_PROMPT
    
    def test_prompt_has_rule_no_percentage_without_source(self):
        """Verify Rule 2 exists in prompt"""
        from omnix_services.ai_service.prompt_templates import MASTER_SYSTEM_PROMPT
        assert "NO PERCENTAGE WITHOUT SOURCE" in MASTER_SYSTEM_PROMPT
    
    def test_prompt_has_rule_never_say_refinando(self):
        """Verify Rule 3 exists in prompt"""
        from omnix_services.ai_service.prompt_templates import MASTER_SYSTEM_PROMPT
        assert "NEVER SAY" in MASTER_SYSTEM_PROMPT
        assert "REFINANDO" in MASTER_SYSTEM_PROMPT
    
    def test_prompt_has_rule_close_inactivity_risk(self):
        """Verify Rule 4 exists in prompt"""
        from omnix_services.ai_service.prompt_templates import MASTER_SYSTEM_PROMPT
        assert "SYSTEM THAT NEVER TRADES" in MASTER_SYSTEM_PROMPT
    
    def test_prompt_has_killer_phrases(self):
        """Verify killer phrases are in prompt"""
        from omnix_services.ai_service.prompt_templates import MASTER_SYSTEM_PROMPT
        killer_phrases = [
            "pocas ventanas buenas",
            "concentración de payoff",
            "mercado habilita",
        ]
        for phrase in killer_phrases:
            assert phrase in MASTER_SYSTEM_PROMPT, f"Missing killer phrase: {phrase}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
