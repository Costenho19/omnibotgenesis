"""
OMNIX Trading Bot Core
Auto-trading bot y paper trading
"""

from .auto_trading_bot import AutoTradingBot
from .paper_trading import PaperTradingManager

__all__ = [
    'AutoTradingBot',
    'PaperTradingManager'
]
