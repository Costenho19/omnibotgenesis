#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNIX V5.3 ULTRA - Coherence Engine Integration Example
Ejemplo de cómo integrar el Coherence Engine con el sistema de trading
Desarrollado por Harold Nunes - Noviembre 2025
"""

from typing import Dict, Any
from omnix_services.coherence_service import (
    CoherenceEngine,
    StrategySignal,
    Signal
)


class OmnixCoherenceIntegration:
    """
    Integración del Coherence Engine con el sistema OMNIX de trading
    """
    
    def __init__(self):
        self.coherence_engine = CoherenceEngine()
    
    def analyze_trading_decision(self, trading_signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza una decisión de trading usando el Coherence Engine
        
        Args:
            trading_signals: Diccionario con señales de todas las estrategias
                {
                    'quantum_momentum': {'signal': 'BUY', 'confidence': 0.85, 'strength': 8.5},
                    'kalman_filter': {'signal': 'BUY', 'confidence': 0.78, 'strength': 0.87},
                    ...
                }
        
        Returns:
            Diccionario con análisis de coherencia y recomendación
        """
        
        # Convertir señales a formato StrategySignal
        strategy_signals = []
        
        for strategy_name, signal_data in trading_signals.items():
            # Convertir string a Signal enum
            signal_str = signal_data.get('signal', 'HOLD').upper()
            signal_enum = self._convert_to_signal_enum(signal_str)
            
            strategy_signal = StrategySignal(
                name=strategy_name,
                signal=signal_enum,
                confidence=signal_data.get('confidence', 0.5),
                strength=signal_data.get('strength', 0.0),
                reasoning=signal_data.get('reasoning', 'No reasoning provided')
            )
            strategy_signals.append(strategy_signal)
        
        # Analizar coherencia
        coherence_report = self.coherence_engine.analyze_coherence(strategy_signals)
        
        # Convertir a diccionario para uso en el bot
        return {
            'coherence_score': coherence_report.coherence_score,
            'coherence_level': coherence_report.coherence_level.value,
            'consensus_signal': coherence_report.consensus_signal.name,
            'consensus_confidence': coherence_report.consensus_confidence,
            'recommendation': coherence_report.decision_recommendation,
            'contradictions': coherence_report.contradictions,
            'bullish_count': coherence_report.bullish_count,
            'bearish_count': coherence_report.bearish_count,
            'neutral_count': coherence_report.neutral_count,
            'should_trade': coherence_report.coherence_score >= 50,  # Umbral de coherencia mínima
            'formatted_report': self.coherence_engine.format_report(coherence_report),
            'emoji': self.coherence_engine.get_coherence_emoji(coherence_report.coherence_score)
        }
    
    def _convert_to_signal_enum(self, signal_str: str) -> Signal:
        """Convierte string a Signal enum"""
        signal_map = {
            'STRONG_BUY': Signal.STRONG_BUY,
            'BUY': Signal.BUY,
            'HOLD': Signal.HOLD,
            'SELL': Signal.SELL,
            'STRONG_SELL': Signal.STRONG_SELL
        }
        return signal_map.get(signal_str, Signal.HOLD)


# Ejemplo de uso en el bot de trading
def example_trading_integration():
    """
    Ejemplo de cómo usar el Coherence Engine en el flujo de trading
    """
    
    # Inicializar integración
    coherence_integration = OmnixCoherenceIntegration()
    
    # Supongamos que tienes estas señales del sistema de trading
    trading_signals = {
        'quantum_momentum': {
            'signal': 'BUY',
            'confidence': 0.85,
            'strength': 8.5,
            'reasoning': 'EMA, RSI, MACD, Volume alcistas'
        },
        'kalman_filter': {
            'signal': 'BUY',
            'confidence': 0.78,
            'strength': 0.87,
            'reasoning': 'Tendencia alcista confirmada'
        },
        'monte_carlo': {
            'signal': 'BUY',
            'confidence': 0.82,
            'strength': 78.0,
            'reasoning': '78% win probability en 10K simulaciones'
        },
        'hmm_regime': {
            'signal': 'BUY',
            'confidence': 0.75,
            'strength': 1.0,
            'reasoning': 'Régimen TRENDING detectado'
        },
        'kelly_criterion': {
            'signal': 'BUY',
            'confidence': 0.70,
            'strength': 0.25,
            'reasoning': 'Kelly sugiere 25% de balance'
        },
        'black_swan': {
            'signal': 'HOLD',
            'confidence': 0.65,
            'strength': 0.0,
            'reasoning': 'Riesgo bajo, proceder con precaución'
        },
        'order_book': {
            'signal': 'BUY',
            'confidence': 0.72,
            'strength': 1.0,
            'reasoning': 'Whale accumulation detectado'
        },
        'sentiment': {
            'signal': 'SELL',
            'confidence': 0.60,
            'strength': -0.5,
            'reasoning': 'Sentimiento bajista en redes sociales'
        },
        'sharia_compliance': {
            'signal': 'BUY',
            'confidence': 1.0,
            'strength': 1.0,
            'reasoning': 'Asset halal confirmado'
        }
    }
    
    # Analizar coherencia
    coherence_analysis = coherence_integration.analyze_trading_decision(trading_signals)
    
    # Mostrar resultados
    print("=" * 60)
    print("🧠 ANÁLISIS DE COHERENCIA ANTES DE OPERAR")
    print("=" * 60)
    print(f"📊 Score de Coherencia: {coherence_analysis['coherence_score']:.1f}%")
    print(f"🎯 Nivel: {coherence_analysis['coherence_level']}")
    print(f"💪 Señal de Consenso: {coherence_analysis['consensus_signal']}")
    print(f"✅ Confianza: {coherence_analysis['consensus_confidence']*100:.1f}%")
    print(f"🚦 ¿Operar?: {'SÍ' if coherence_analysis['should_trade'] else 'NO'}")
    print(f"\n⚡ RECOMENDACIÓN:")
    print(f"   {coherence_analysis['recommendation']}")
    
    if coherence_analysis['contradictions']:
        print(f"\n⚠️ CONTRADICCIONES:")
        for i, contradiction in enumerate(coherence_analysis['contradictions'], 1):
            print(f"   {i}. {contradiction}")
    
    print("\n" + coherence_analysis['formatted_report'])
    
    # Decisión de trading basada en coherencia
    if coherence_analysis['should_trade'] and coherence_analysis['coherence_score'] >= 70:
        print(f"\n✅ {coherence_analysis['emoji']} PROCEDER CON TRADE - ALTA COHERENCIA")
    elif coherence_analysis['should_trade']:
        print(f"\n⚠️ {coherence_analysis['emoji']} PROCEDER CON PRECAUCIÓN - COHERENCIA MODERADA")
    else:
        print(f"\n🚫 {coherence_analysis['emoji']} NO OPERAR - COHERENCIA BAJA")
    
    return coherence_analysis


if __name__ == "__main__":
    # Ejecutar ejemplo
    result = example_trading_integration()
    
    print("\n" + "=" * 60)
    print("📦 Resultado retornado (JSON-like):")
    print("=" * 60)
    import json
    print(json.dumps({k: v for k, v in result.items() if k != 'formatted_report'}, indent=2))
