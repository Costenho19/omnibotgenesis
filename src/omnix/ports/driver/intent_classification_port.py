"""
Intent Classification Port (Driver Port)
==========================================

This port defines how external systems (like Telegram bot) can classify
user intents before routing messages to AI or configuration handlers.

Design Principle (AI-First):
- Intent classification only examines messages that start with "/"
- All other messages are immediately routed to AI conversation
- This prevents false positives from NLP keyword matching

Protocol for TelegramPort Integration:
- handle_message() → IntentClassificationPort.classify() → AI if not command
- handle_command() → IntentClassificationPort.classify() → execute if valid

Dec 18, 2025: Created as part of hexagonal architecture migration
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Protocol

from src.omnix.domain.user_settings.intents import (
    Intent,
    IntentType,
    ConfigurationIntent,
)


@dataclass
class ClassificationRequest:
    """Request to classify a user message."""
    
    user_id: str
    message: str
    chat_id: Optional[str] = None
    context: Optional[dict] = None


@dataclass
class ClassificationResponse:
    """Result of intent classification."""
    
    intent: Intent
    should_route_to_ai: bool
    action_handler: Optional[str] = None
    action_params: Optional[dict] = None
    
    @property
    def is_configuration_command(self) -> bool:
        """Check if this is a configuration command."""
        return (
            self.intent.type == IntentType.CONFIGURATION 
            and not self.should_route_to_ai
        )


class IntentClassificationPort(Protocol):
    """
    Protocol for intent classification services.
    
    This is a Driver Port - it's called by external systems (Telegram, REST API)
    to determine how to route incoming messages.
    
    Implementation Notes:
    - The classify() method should be fast (< 10ms)
    - No network calls - uses local pattern matching
    - AI-First: returns should_route_to_ai=True for all non-/commands
    """
    
    def classify(self, request: ClassificationRequest) -> ClassificationResponse:
        """
        Classify a user message to determine routing.
        
        Args:
            request: The classification request with user message
            
        Returns:
            ClassificationResponse with routing decision
        """
        ...
    
    def get_command_help(self, command: str) -> Optional[str]:
        """
        Get help text for a specific command.
        
        Args:
            command: The command to get help for (e.g., "/pause")
            
        Returns:
            Help text or None if command not found
        """
        ...
    
    def list_available_commands(self) -> list[str]:
        """
        List all available configuration commands.
        
        Returns:
            List of command strings (e.g., ["/pause", "/resume", ...])
        """
        ...


class IntentClassificationPortABC(ABC):
    """
    Abstract base class for intent classification.
    
    Use this if you prefer ABC over Protocol.
    """
    
    @abstractmethod
    def classify(self, request: ClassificationRequest) -> ClassificationResponse:
        """Classify a user message to determine routing."""
        pass
    
    @abstractmethod
    def get_command_help(self, command: str) -> Optional[str]:
        """Get help text for a specific command."""
        pass
    
    @abstractmethod
    def list_available_commands(self) -> list[str]:
        """List all available configuration commands."""
        pass
