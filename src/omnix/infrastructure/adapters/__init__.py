"""
OMNIX V7.0 Infrastructure Adapters
===================================
Adapters implementing application ports by wrapping legacy services.

Available Adapters:
- TradingServiceAdapter: Wraps TradingService for ITradingService port
- RiskGuardianAdapter: Wraps RiskGuardian for IRiskPort
- CoherenceEngineAdapter: Wraps CoherenceEngine for ICoherenceEnginePort
- KrakenAdapter: Implements TradingPort + MarketDataPort for Kraken exchange
- GeminiAdapter: Implements AIInferencePort for AI inference (Gemini/OpenAI/Anthropic)

Migration Status: Phase 3 - INFRASTRUCTURE ADAPTERS COMPLETE
"""

from src.omnix.infrastructure.adapters.trading_adapter import TradingServiceAdapter
from src.omnix.infrastructure.adapters.risk_adapter import RiskGuardianAdapter
from src.omnix.infrastructure.adapters.coherence_adapter import CoherenceEngineAdapter
from src.omnix.infrastructure.adapters.kraken_adapter import KrakenAdapter
from src.omnix.infrastructure.adapters.gemini_adapter import GeminiAdapter

__all__ = [
    "TradingServiceAdapter",
    "RiskGuardianAdapter",
    "CoherenceEngineAdapter",
    "KrakenAdapter",
    "GeminiAdapter",
]
