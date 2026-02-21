"""
OMNIX Dashboard Blueprints
Modular route organization for Flask application
"""

from .views import views_bp
from .core import core_bp
from .market import market_bp
from .intelligence import intelligence_bp
from .system import system_bp
from .snapshots import snapshots_bp
from .verification import verification_bp

__all__ = [
    'views_bp',
    'core_bp', 
    'market_bp',
    'intelligence_bp',
    'system_bp',
    'snapshots_bp',
    'verification_bp'
]
