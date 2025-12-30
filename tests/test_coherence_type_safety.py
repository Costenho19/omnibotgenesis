#!/usr/bin/env python3
"""
Test Type Safety for Coherence Engine
FIX Dec 30, 2025: Verifica que CoherenceEngine no lanza excepciones
por comparaciones str vs int.

Ejecutar: python -m pytest tests/test_coherence_type_safety.py -v
"""
import pytest
from omnix_services.coherence_service.coherence_engine import (
    CoherenceEngine,
    StrategySignal,
    Signal,
    normalize_signal,
    normalize_strategy_signal,
    safe_float,
)


class TestNormalizeSignal:
    """Tests para normalize_signal()"""
    
    def test_normalize_string_buy(self):
        """String 'BUY' debe convertir a Signal.BUY"""
        result = normalize_signal("BUY")
        assert result == Signal.BUY
        assert isinstance(result, Signal)
    
    def test_normalize_string_sell(self):
        """String 'SELL' debe convertir a Signal.SELL"""
        result = normalize_signal("SELL")
        assert result == Signal.SELL
    
    def test_normalize_string_hold(self):
        """String 'HOLD' debe convertir a Signal.HOLD"""
        result = normalize_signal("HOLD")
        assert result == Signal.HOLD
    
    def test_normalize_string_lowercase(self):
        """Strings en lowercase deben funcionar"""
        assert normalize_signal("buy") == Signal.BUY
        assert normalize_signal("sell") == Signal.SELL
    
    def test_normalize_enum_passthrough(self):
        """Enum Signal debe pasar sin cambio"""
        result = normalize_signal(Signal.STRONG_BUY)
        assert result == Signal.STRONG_BUY
    
    def test_normalize_int_value(self):
        """Int 1 debe convertir a Signal.BUY"""
        result = normalize_signal(1)
        assert result == Signal.BUY
    
    def test_normalize_none_to_hold(self):
        """None debe convertir a Signal.HOLD (fallback seguro)"""
        result = normalize_signal(None)
        assert result == Signal.HOLD
    
    def test_normalize_invalid_string_to_hold(self):
        """String inválido debe convertir a HOLD"""
        result = normalize_signal("INVALID_SIGNAL")
        assert result == Signal.HOLD


class TestNormalizeStrategySignal:
    """Tests para normalize_strategy_signal()"""
    
    def test_normalize_with_string_signal(self):
        """StrategySignal con signal string debe normalizarse"""
        original = StrategySignal(
            name="test_strategy",
            signal="BUY",  # String en lugar de Enum
            confidence=0.75,
            strength=1.0,
            reasoning="test"
        )
        result = normalize_strategy_signal(original)
        
        assert isinstance(result.signal, Signal)
        assert result.signal == Signal.BUY
        assert isinstance(result.confidence, float)
    
    def test_normalize_with_string_confidence(self):
        """StrategySignal con confidence string debe normalizarse"""
        original = StrategySignal(
            name="test_strategy",
            signal=Signal.BUY,
            confidence="0.73",  # String numérico
            strength="1.0",     # String numérico
            reasoning="test"
        )
        result = normalize_strategy_signal(original)
        
        assert isinstance(result.confidence, float)
        assert result.confidence == 0.73
        assert isinstance(result.strength, float)
        assert result.strength == 1.0


class TestCoherenceEngineTypeSafety:
    """Tests de seguridad de tipos para CoherenceEngine"""
    
    def test_analyze_coherence_with_string_signals(self):
        """analyze_coherence acepta signals con signal=string sin excepción"""
        engine = CoherenceEngine()
        signals = [
            StrategySignal(
                name="strategy1",
                signal="BUY",  # String - debería causar error sin fix
                confidence=0.75,
                strength=1.0,
                reasoning="test"
            ),
            StrategySignal(
                name="strategy2", 
                signal="SELL",  # String
                confidence=0.60,
                strength=-1.0,
                reasoning="test"
            ),
        ]
        
        report = engine.analyze_coherence(signals)
        
        assert isinstance(report.coherence_score, float)
        assert report.coherence_score >= 0
        assert report.coherence_score <= 100
    
    def test_analyze_coherence_with_string_confidence(self):
        """analyze_coherence acepta confidence y strength como strings numéricos"""
        engine = CoherenceEngine()
        signals = [
            StrategySignal(
                name="strategy1",
                signal=Signal.BUY,
                confidence="0.73",  # String numérico
                strength="1.0",     # String numérico
                reasoning="test"
            ),
        ]
        
        report = engine.analyze_coherence(signals)
        assert isinstance(report.coherence_score, float)
    
    def test_classify_coherence_level_with_string_score(self):
        """_classify_coherence_level maneja score como string"""
        engine = CoherenceEngine()
        
        from omnix_services.coherence_service.coherence_engine import CoherenceLevel
        result = engine._classify_coherence_level("75.5")
        assert result == CoherenceLevel.GOOD
    
    def test_get_coherence_emoji_with_string_score(self):
        """get_coherence_emoji maneja score como string"""
        engine = CoherenceEngine()
        
        result = engine.get_coherence_emoji("85")
        assert result == "🔵"  # Azul - Bueno


class TestSafeFloat:
    """Tests para safe_float()"""
    
    def test_safe_float_removes_percent(self):
        """safe_float remueve % y convierte"""
        result = safe_float("73.5%")
        assert result == 73.5
    
    def test_safe_float_with_spaces(self):
        """safe_float maneja espacios"""
        result = safe_float("  42.0  ")
        assert result == 42.0
