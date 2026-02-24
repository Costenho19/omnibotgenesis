"""
OMNIX Coherence Engine Demo Script

Moved from coherence_engine.py __main__ block to keep demo/test code
outside of the production runtime.

Usage: python examples/coherence_engine_demo.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from omnix_services.coherence_service.coherence_engine import (
    CoherenceEngine, StrategySignal, Signal
)


def example_usage():
    engine = CoherenceEngine()

    signals = [
        StrategySignal(
            name="quantum_momentum",
            signal=Signal.BUY,
            confidence=0.85,
            strength=8.5,
            reasoning="6 componentes alcistas"
        ),
        StrategySignal(
            name="kalman_filter",
            signal=Signal.BUY,
            confidence=0.78,
            strength=0.87,
            reasoning="Tendencia alcista confirmada"
        ),
        StrategySignal(
            name="monte_carlo",
            signal=Signal.BUY,
            confidence=0.82,
            strength=78.0,
            reasoning="78% probabilidad de ganancia"
        ),
        StrategySignal(
            name="hmm_regime",
            signal=Signal.BUY,
            confidence=0.75,
            strength=1.0,
            reasoning="Régimen TRENDING alcista"
        ),
        StrategySignal(
            name="kelly_criterion",
            signal=Signal.BUY,
            confidence=0.70,
            strength=0.25,
            reasoning="25% tamaño óptimo"
        ),
        StrategySignal(
            name="black_swan",
            signal=Signal.HOLD,
            confidence=0.65,
            strength=0.0,
            reasoning="Riesgo bajo detectado"
        ),
        StrategySignal(
            name="order_book",
            signal=Signal.BUY,
            confidence=0.72,
            strength=1.0,
            reasoning="Flow institucional positivo"
        ),
        StrategySignal(
            name="sentiment",
            signal=Signal.SELL,
            confidence=0.60,
            strength=-0.5,
            reasoning="Sentiment bajista en redes"
        ),
        StrategySignal(
            name="sharia_compliance",
            signal=Signal.BUY,
            confidence=1.0,
            strength=1.0,
            reasoning="Asset halal confirmado"
        ),
    ]

    report = engine.analyze_coherence(signals)
    print(engine.format_report(report))

    emoji = engine.get_coherence_emoji(report.coherence_score)
    print(f"\n{emoji} Score Visual: {report.coherence_score:.1f}%")


if __name__ == "__main__":
    example_usage()
