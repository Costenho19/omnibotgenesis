"""
OMNIX V7.0 Trading Use Cases
=============================
Application services for trading operations.

Use Cases:
- ExecuteTradeUseCase: Execute trades with risk checks
- ScanMarketUseCase: Scan markets for trading signals
- ManagePositionsUseCase: Manage open positions
- GenerateCoherenceReportUseCase: Generate coherence analysis reports

Migration Status: Wave 2 - COMPLETE
"""

from src.omnix.application.trading.execute_trade import (
    ExecuteTradeUseCase,
    ExecuteTradeRequest,
    ExecuteTradeResponse,
)
from src.omnix.application.trading.scan_market import (
    ScanMarketUseCase,
    ScanMarketRequest,
    ScanMarketResponse,
)
from src.omnix.application.trading.manage_positions import (
    ManagePositionsUseCase,
    ManagePositionsRequest,
    ManagePositionsResponse,
    PositionSummary,
)
from src.omnix.application.trading.coherence_report import (
    GenerateCoherenceReportUseCase,
    CoherenceReportRequest,
    GenerateCoherenceReportResponse,
    CoherenceReport,
    TierResult,
)

__all__ = [
    "ExecuteTradeUseCase",
    "ExecuteTradeRequest",
    "ExecuteTradeResponse",
    "ScanMarketUseCase",
    "ScanMarketRequest",
    "ScanMarketResponse",
    "ManagePositionsUseCase",
    "ManagePositionsRequest",
    "ManagePositionsResponse",
    "PositionSummary",
    "GenerateCoherenceReportUseCase",
    "CoherenceReportRequest",
    "GenerateCoherenceReportResponse",
    "CoherenceReport",
    "TierResult",
]
