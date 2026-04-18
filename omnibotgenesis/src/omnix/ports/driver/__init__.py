"""
OMNIX Driver Ports - Input Interfaces

These ports define contracts for how external actors (users, other systems)
interact with the application (REST API, Telegram bot, CLI, etc.).

All driver ports are defined as typing.Protocol for structural subtyping.
"""

from src.omnix.ports.driver.rest_api_port import RestApiPort
from src.omnix.ports.driver.telegram_port import TelegramPort
from src.omnix.ports.driver.intent_classification_port import (
    IntentClassificationPort,
    IntentClassificationPortABC,
    ClassificationRequest,
    ClassificationResponse,
)

__all__ = [
    "RestApiPort",
    "TelegramPort",
    "IntentClassificationPort",
    "IntentClassificationPortABC",
    "ClassificationRequest",
    "ClassificationResponse",
]
