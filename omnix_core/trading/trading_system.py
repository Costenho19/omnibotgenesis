"""
omnix_core.trading.trading_system — Compatibility shim (ADR-121).

Canonical location: omnix_core.trading_system
This file re-exports TradingSystem to support the dotted import path:

    from omnix_core.trading.trading_system import TradingSystem
"""
from omnix_core.trading_system import TradingSystem

__all__ = ["TradingSystem"]
