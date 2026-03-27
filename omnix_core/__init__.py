"""
OMNIX Core Modules
Core trading system and bot functionality
"""

try:
    from .trading_system import TradingSystem
except (ImportError, Exception):
    TradingSystem = None

__all__ = [
    'TradingSystem'
]
