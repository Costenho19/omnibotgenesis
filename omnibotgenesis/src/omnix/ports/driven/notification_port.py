"""
OMNIX Notification Port - Messaging Interface Contract

This Protocol defines the contract for sending notifications.
All methods are ASYNC for optimal Telegram API performance.

SOLID Principles:
- SRP: Only notification operations
- ISP: Minimal interface for messaging
- DIP: Depend on this abstraction, not TelegramBot directly
"""

from typing import Protocol, Optional, runtime_checkable


@runtime_checkable
class NotificationPort(Protocol):
    """
    Contract for sending notifications (Telegram).
    
    Implementation: omnix_core.bot.enterprise_bot.TelegramHandler
    """
    
    async def send_message(
        self,
        recipient_id: str,
        message: str,
        parse_mode: str = 'HTML'
    ) -> bool:
        """
        Send text message.
        
        Args:
            recipient_id: User/chat ID
            message: Message text
            parse_mode: 'HTML' or 'Markdown'
            
        Returns:
            True if sent successfully
        """
        ...
    
    async def send_trade_alert(
        self,
        recipient_id: str,
        trade_data: dict
    ) -> bool:
        """
        Send formatted trade alert.
        
        Args:
            recipient_id: User/chat ID
            trade_data: Trade details (symbol, side, amount, price, etc.)
            
        Returns:
            True if sent successfully
        """
        ...
