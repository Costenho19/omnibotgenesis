"""
OMNIX V7.0 Interfaces Layer
============================
Phase 3b: Driver adapters for external interfaces (Flask, Telegram, CLI).

This package contains the interface layer of the hexagonal architecture,
providing adapters for external systems that drive the application.
"""

from src.omnix.interfaces.flask_app import create_app, get_app

__all__ = [
    'create_app',
    'get_app',
]
