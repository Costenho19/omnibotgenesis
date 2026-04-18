"""
OMNIX INSTITUTIONAL+ - AI Service Adapters

Adapters for backward compatibility and external integrations.
"""

from .legacy_adapter import (
    get_ai_service,
    get_ai_gateway,
    LegacyAIServiceAdapter,
)

__all__ = [
    "get_ai_service",
    "get_ai_gateway",
    "LegacyAIServiceAdapter",
]
