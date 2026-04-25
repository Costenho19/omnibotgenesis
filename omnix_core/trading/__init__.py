"""
omnix_core.trading — Compatibility shim (ADR-121).

The canonical trading system module is omnix_core.trading_system.
This package exists to satisfy import paths of the form:

    from omnix_core.trading.trading_system import TradingSystem

which are used by audit tooling and external scripts. All symbols
are re-exported from the canonical location — no duplication of logic.
"""
from omnix_core.trading_system import TradingSystem

__all__ = ["TradingSystem"]
