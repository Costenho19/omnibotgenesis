"""
OMNIX Derivatives Trading Module - Premium Institutional Grade
==============================================================

Sistema de trading de derivados (perpetuos/futuros) con enfoque institucional:
- Máximo 3x apalancamiento (conservador)
- Protección contra liquidación automática
- Hedging automático spot↔perpetuos
- Arbitraje de funding rates
- Integración completa con RMS

Componentes:
- KrakenFuturesClient: Cliente API para Kraken Futures
- MarginEngine: Gestión de margen y apalancamiento
- PaperDerivatives: Simulador paper trading
- DerivativesManager: Orquestador principal
- HedgingService: Hedging automático
- FundingArbitrageAnalyzer: Análisis de oportunidades funding

NOTA: Este módulo opera en modo PAPER TRADING por defecto.
Live trading requiere activación explícita y API keys de Kraken Futures.

Author: OMNIX Team
Version: 1.0.0
"""

from .kraken_futures_client import KrakenFuturesClient
from .margin_engine import MarginEngine
from .paper_derivatives import PaperDerivativesManager
from .derivatives_manager import DerivativesManager
from .hedging_service import HedgingService
from .funding_arbitrage import FundingArbitrageAnalyzer

__all__ = [
    'KrakenFuturesClient',
    'MarginEngine', 
    'PaperDerivativesManager',
    'DerivativesManager',
    'HedgingService',
    'FundingArbitrageAnalyzer'
]

__version__ = "1.0.0"
