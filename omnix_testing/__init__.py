"""
OMNIX V6.0 ULTRA - Professional Testing & Validation System
Sistema institucional de backtesting y paper trading para demostrar win rates a inversionistas
Desarrollado por Harold Nunes - Noviembre 2025
"""

__version__ = "1.0.0"
__author__ = "Harold Nunes"

from omnix_testing.backtesting.backtesting_engine import BacktestingEngine
from omnix_testing.backtesting.kraken_data_downloader import KrakenDataDownloader
from omnix_testing.backtesting.metrics_calculator import MetricsCalculator

__all__ = [
    'BacktestingEngine',
    'KrakenDataDownloader', 
    'MetricsCalculator'
]
