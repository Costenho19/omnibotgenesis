"""
User Settings Intent Value Objects
===================================

Value Objects for intent classification in the OMNIX trading bot.
These define the canonical list of configuration intents that require
explicit /command prefixes to prevent false positives.

Design Principle (AI-First):
- Only messages starting with "/" are considered configuration commands
- All other text goes directly to AI for natural conversation
- This prevents false positives like "resumen" → "resume"

Dec 18, 2025: Created as part of hexagonal architecture migration
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import re


class IntentType(Enum):
    """Types of user intents detected from messages."""
    
    CONFIGURATION = "configuration"
    QUERY = "query"
    CONVERSATION = "conversation"
    UNKNOWN = "unknown"


class ConfigurationIntent(Enum):
    """
    Configuration intents that modify user settings.
    
    These MUST be triggered by explicit /commands only.
    """
    
    PAUSE = "pause"
    RESUME = "resume"
    UPDATE_RISK = "update_risk"
    UPDATE_LIMIT = "update_limit"
    AUTO_TRADING = "auto_trading"
    SET_PROFILE = "set_profile"
    
    @classmethod
    def from_command(cls, command: str) -> Optional["ConfigurationIntent"]:
        """Map a command string to a ConfigurationIntent."""
        cmd = command.lower().strip().lstrip('/')
        
        if cmd in ('pause', 'pausar'):
            return cls.PAUSE
        elif cmd in ('resume', 'reanudar', 'continuar'):
            return cls.RESUME
        elif cmd.startswith('perfil'):
            return cls.SET_PROFILE
        elif cmd.startswith('limite'):
            return cls.UPDATE_LIMIT
        elif cmd.startswith('autotrading'):
            return cls.AUTO_TRADING
        elif cmd.startswith('riesgo'):
            return cls.UPDATE_RISK
        
        return None


@dataclass(frozen=True)
class Intent:
    """
    Immutable Value Object representing a detected user intent.
    
    Attributes:
        type: The type of intent (configuration, query, conversation, unknown)
        config_intent: If type is CONFIGURATION, the specific config action
        confidence: Confidence score (0.0 to 1.0)
        requires_confirmation: Whether action needs user confirmation
        raw_message: Original message that triggered this intent
    """
    
    type: IntentType
    config_intent: Optional[ConfigurationIntent] = None
    confidence: float = 1.0
    requires_confirmation: bool = False
    raw_message: str = ""
    
    def __post_init__(self):
        """Validate intent consistency."""
        if self.type == IntentType.CONFIGURATION and self.config_intent is None:
            raise ValueError("Configuration intent requires config_intent to be set")
        
        if self.type != IntentType.CONFIGURATION and self.config_intent is not None:
            raise ValueError("Non-configuration intent should not have config_intent")
    
    @property
    def is_explicit_command(self) -> bool:
        """Check if this intent came from an explicit /command."""
        return self.raw_message.strip().startswith('/')
    
    @classmethod
    def from_message(cls, message: str) -> "Intent":
        """
        Create an Intent from a user message.
        
        AI-First Rule: Only messages starting with "/" are considered commands.
        All other messages are treated as conversation for AI processing.
        """
        stripped = message.strip()
        
        if not stripped.startswith('/'):
            return cls(
                type=IntentType.CONVERSATION,
                raw_message=message,
                confidence=1.0
            )
        
        cmd_match = re.match(r'^/(\w+)', stripped)
        if not cmd_match:
            return cls(
                type=IntentType.UNKNOWN,
                raw_message=message,
                confidence=0.5
            )
        
        command = cmd_match.group(1).lower()
        config_intent = ConfigurationIntent.from_command(command)
        
        if config_intent:
            high_risk = config_intent in (
                ConfigurationIntent.UPDATE_RISK,
                ConfigurationIntent.AUTO_TRADING,
            )
            
            return cls(
                type=IntentType.CONFIGURATION,
                config_intent=config_intent,
                confidence=1.0,
                requires_confirmation=high_risk,
                raw_message=message
            )
        
        return cls(
            type=IntentType.QUERY,
            raw_message=message,
            confidence=1.0
        )


COMMAND_INTENTS: dict[str, ConfigurationIntent] = {
    "/pause": ConfigurationIntent.PAUSE,
    "/pausar": ConfigurationIntent.PAUSE,
    "/resume": ConfigurationIntent.RESUME,
    "/reanudar": ConfigurationIntent.RESUME,
    "/continuar": ConfigurationIntent.RESUME,
    "/perfil": ConfigurationIntent.SET_PROFILE,
    "/limite": ConfigurationIntent.UPDATE_LIMIT,
    "/autotrading": ConfigurationIntent.AUTO_TRADING,
    "/riesgo": ConfigurationIntent.UPDATE_RISK,
}
