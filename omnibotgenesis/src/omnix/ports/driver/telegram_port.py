"""
OMNIX Telegram Port - Bot Command Interface Contract

This Protocol defines the contract for Telegram bot command handlers.
Driver ports represent how external actors interact with the application.

SOLID Principles:
- SRP: Only Telegram command handling
- ISP: Minimal interface for bot operations
- DIP: Bot depends on this abstraction
"""

from typing import Protocol, Dict, Any, Optional, runtime_checkable


@runtime_checkable
class TelegramPort(Protocol):
    """
    Contract for Telegram bot command handlers.
    
    Implementation: omnix_core.bot.enterprise_bot.EnterpriseBot
    """
    
    async def handle_message(
        self,
        user_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Handle incoming text message.
        
        Args:
            user_id: Telegram user ID
            message: Message text
            context: Optional conversation context
            
        Returns:
            Response message to send
        """
        ...
    
    async def handle_command(
        self,
        user_id: str,
        command: str,
        args: Optional[str] = None
    ) -> str:
        """
        Handle bot command (e.g., /start, /status).
        
        Args:
            user_id: Telegram user ID
            command: Command name without /
            args: Optional command arguments
            
        Returns:
            Response message to send
        """
        ...
    
    async def handle_callback(
        self,
        user_id: str,
        callback_data: str
    ) -> Dict[str, Any]:
        """
        Handle inline keyboard callback.
        
        Args:
            user_id: Telegram user ID
            callback_data: Callback data string
            
        Returns:
            Dict with:
            - message: Optional response message
            - edit_message: Optional edited message
            - answer_callback: bool
        """
        ...
    
    def get_user_state(self, user_id: str) -> Dict[str, Any]:
        """
        Get current user conversation state.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Dict with user's current state and context
        """
        ...
