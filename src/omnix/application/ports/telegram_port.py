"""
OMNIX V7.0 Telegram Port
=========================
Phase 3b: Protocol interface for Telegram bot operations.

This port defines the contract for Telegram bot adapters,
allowing the application layer to interact with Telegram
without depending on specific implementation details.
"""

from typing import Protocol, Optional, Dict, Any, List, Callable, Awaitable
from dataclasses import dataclass


@dataclass
class TelegramMessage:
    """Represents an incoming Telegram message."""
    chat_id: int
    user_id: int
    username: Optional[str]
    text: str
    message_id: int
    is_command: bool = False
    command: Optional[str] = None
    command_args: Optional[str] = None


@dataclass
class TelegramResponse:
    """Represents an outgoing Telegram response."""
    chat_id: int
    text: str
    parse_mode: str = "HTML"
    reply_to_message_id: Optional[int] = None
    reply_markup: Optional[Dict[str, Any]] = None


class ITelegramBot(Protocol):
    """
    Port for Telegram bot operations.
    
    Defines the contract that Telegram bot adapters must implement.
    """
    
    async def start(self) -> bool:
        """
        Start the Telegram bot.
        
        Returns:
            True if started successfully, False otherwise.
        """
        ...
    
    async def stop(self) -> bool:
        """
        Stop the Telegram bot gracefully.
        
        Returns:
            True if stopped successfully, False otherwise.
        """
        ...
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send a text message to a chat.
        
        Args:
            chat_id: Target chat ID
            text: Message text
            parse_mode: Message formatting mode
            reply_markup: Optional inline keyboard
        
        Returns:
            True if sent successfully
        """
        ...
    
    async def send_voice(
        self,
        chat_id: int,
        voice_data: bytes,
        caption: Optional[str] = None,
    ) -> bool:
        """
        Send a voice message to a chat.
        
        Args:
            chat_id: Target chat ID
            voice_data: Audio data bytes
            caption: Optional caption text
        
        Returns:
            True if sent successfully
        """
        ...
    
    def is_running(self) -> bool:
        """Check if bot is currently running."""
        ...
    
    def health_check(self) -> Dict[str, Any]:
        """
        Get bot health status.
        
        Returns:
            Dict with health status information
        """
        ...
    
    def register_command_handler(
        self,
        command: str,
        handler: Callable[[TelegramMessage], Awaitable[TelegramResponse]],
    ) -> None:
        """
        Register a command handler.
        
        Args:
            command: Command name (without /)
            handler: Async function to handle the command
        """
        ...
    
    def register_message_handler(
        self,
        handler: Callable[[TelegramMessage], Awaitable[TelegramResponse]],
    ) -> None:
        """
        Register a general message handler.
        
        Args:
            handler: Async function to handle messages
        """
        ...


class ITelegramNotifier(Protocol):
    """
    Port for sending notifications via Telegram.
    
    Simpler interface for components that only need to send messages.
    """
    
    async def notify(
        self,
        chat_id: int,
        message: str,
        priority: str = "normal",
    ) -> bool:
        """
        Send a notification message.
        
        Args:
            chat_id: Target chat ID
            message: Notification text
            priority: Message priority (normal, high, urgent)
        
        Returns:
            True if sent successfully
        """
        ...
    
    async def notify_admins(
        self,
        message: str,
        priority: str = "normal",
    ) -> int:
        """
        Send notification to all admin users.
        
        Args:
            message: Notification text
            priority: Message priority
        
        Returns:
            Number of admins notified
        """
        ...
