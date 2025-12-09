"""
OMNIX Driver Ports - Input Interfaces

These ports define contracts for how external actors (users, other systems)
interact with the application (REST API, Telegram bot, CLI, etc.).

All driver ports are defined as typing.Protocol for structural subtyping.
"""

from omnix.ports.driver.rest_api_port import RestApiPort
from omnix.ports.driver.telegram_port import TelegramPort

__all__ = [
    "RestApiPort",
    "TelegramPort",
]
