"""
OMNIX V7.0 Infrastructure Adapters
===================================
Adapters implementing application ports by wrapping legacy services.

Available Adapters:
- TradingServiceAdapter: Wraps TradingService for ITradingService port
- RiskGuardianAdapter: Wraps RiskGuardian for IRiskPort

Migration Status: Wave 3 - COMPLETE
"""

from src.omnix.infrastructure.adapters.trading_adapter import TradingServiceAdapter
from src.omnix.infrastructure.adapters.risk_adapter import RiskGuardianAdapter

__all__ = [
    "TradingServiceAdapter",
    "RiskGuardianAdapter",
]
