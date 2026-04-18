"""OMNIX Configuration Module"""

from .trading_profiles import (
    TradingProfile,
    TRADING_PROFILES,
    get_active_profile,
    get_profile_by_name
)

__all__ = [
    'TradingProfile',
    'TRADING_PROFILES',
    'get_active_profile',
    'get_profile_by_name'
]
