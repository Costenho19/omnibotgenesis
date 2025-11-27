"""
OMNIX V6.0 ULTRA - Professional Testing & Validation System
Sistema institucional de backtesting y paper trading para demostrar win rates a inversionistas
Desarrollado por Harold Nunes - Noviembre 2025

COMPONENTES:
- BacktestingEngine: Motor de backtesting con datos reales de Kraken
- ProfessionalValidator: Validación anti-overfitting (Walk-Forward + Monte Carlo)
- KrakenDataDownloader: Descarga de datos históricos
- MetricsCalculator: Cálculo de métricas institucionales
"""

__version__ = "1.1.0"
__author__ = "Harold Nunes"

from omnix_testing.backtesting.backtesting_engine import BacktestingEngine
from omnix_testing.backtesting.kraken_data_downloader import KrakenDataDownloader
from omnix_testing.backtesting.metrics_calculator import MetricsCalculator

from omnix_testing.professional_validator import (
    ProfessionalValidator,
    CostModel,
    MarketRegime,
    WalkForwardResult,
    ValidationReport
)

__all__ = [
    'BacktestingEngine',
    'KrakenDataDownloader', 
    'MetricsCalculator',
    'ProfessionalValidator',
    'CostModel',
    'MarketRegime',
    'WalkForwardResult',
    'ValidationReport'
]
