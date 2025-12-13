"""
OMNIX V7.0 Telegram Bot Adapter
================================
Phase 3b: Infrastructure adapter wrapping EnterpriseTelegramBot.

This adapter implements ITelegramBot port, providing the bridge
between the hexagonal application layer and the legacy Telegram bot.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, Callable, Awaitable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TelegramBotAdapter:
    """
    Adapter for Telegram bot operations.
    
    Wraps the legacy EnterpriseTelegramBot to implement ITelegramBot port.
    Provides telemetry, health checks, and graceful error handling.
    """
    
    _bot: Optional[Any] = field(default=None, repr=False)
    _is_initialized: bool = field(default=False, repr=False)
    _db_manager: Optional[Any] = field(default=None, repr=False)
    
    def __post_init__(self):
        self._initialize_bot()
    
    def _initialize_bot(self) -> None:
        """Initialize the legacy EnterpriseTelegramBot."""
        try:
            from omnix_services.telegram_service import EnterpriseTelegramBot
            self._bot = EnterpriseTelegramBot(db_manager=self._db_manager)
            self._is_initialized = True
            logger.info("TelegramBotAdapter: EnterpriseTelegramBot initialized")
        except ImportError as e:
            logger.warning(f"TelegramBotAdapter: EnterpriseTelegramBot not available: {e}")
            self._is_initialized = False
        except Exception as e:
            logger.error(f"TelegramBotAdapter: Failed to initialize: {e}")
            self._is_initialized = False
    
    async def start(self) -> bool:
        """Start the Telegram bot."""
        if not self._is_initialized or self._bot is None:
            logger.error("TelegramBotAdapter: Cannot start - bot not initialized")
            return False
        
        try:
            if hasattr(self._bot, 'run'):
                loop = asyncio.get_event_loop()
                loop.run_in_executor(None, self._bot.run)
                logger.info("TelegramBotAdapter: Bot started")
                return True
            elif hasattr(self._bot, 'start'):
                await self._bot.start()
                return True
        except Exception as e:
            logger.error(f"TelegramBotAdapter: Failed to start: {e}")
        return False
    
    async def stop(self) -> bool:
        """Stop the Telegram bot gracefully."""
        if not self._is_initialized or self._bot is None:
            return True
        
        try:
            if hasattr(self._bot, 'stop'):
                await self._bot.stop()
                logger.info("TelegramBotAdapter: Bot stopped")
                return True
        except Exception as e:
            logger.error(f"TelegramBotAdapter: Failed to stop: {e}")
        return False
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send a text message to a chat."""
        if not self._is_initialized or self._bot is None:
            logger.warning("TelegramBotAdapter: Cannot send message - bot not initialized")
            return False
        
        try:
            if hasattr(self._bot, 'application') and self._bot.application:
                await self._bot.application.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )
                return True
        except Exception as e:
            logger.error(f"TelegramBotAdapter: Failed to send message: {e}")
        return False
    
    async def send_voice(
        self,
        chat_id: int,
        voice_data: bytes,
        caption: Optional[str] = None,
    ) -> bool:
        """Send a voice message to a chat."""
        if not self._is_initialized or self._bot is None:
            return False
        
        try:
            if hasattr(self._bot, 'application') and self._bot.application:
                await self._bot.application.bot.send_voice(
                    chat_id=chat_id,
                    voice=voice_data,
                    caption=caption,
                )
                return True
        except Exception as e:
            logger.error(f"TelegramBotAdapter: Failed to send voice: {e}")
        return False
    
    def is_running(self) -> bool:
        """Check if bot is currently running."""
        if not self._is_initialized or self._bot is None:
            return False
        return getattr(self._bot, 'is_running', False)
    
    def health_check(self) -> Dict[str, Any]:
        """Get bot health status."""
        return {
            'initialized': self._is_initialized,
            'running': self.is_running(),
            'has_bot': self._bot is not None,
            'has_application': (
                self._bot is not None and 
                hasattr(self._bot, 'application') and 
                self._bot.application is not None
            ),
        }
    
    async def _send_response(self, update, response) -> None:
        """
        Send TelegramResponse honoring all protocol fields.
        
        Properly handles:
        - response.chat_id: If different from update, send to specified chat
        - response.reply_to_message_id: If set, reply to that message
        - response.reply_markup: Pass through to Telegram API
        """
        from src.omnix.application.ports.telegram_port import TelegramResponse
        
        if not isinstance(response, TelegramResponse):
            return
        
        target_chat_id = response.chat_id
        originating_chat_id = update.effective_chat.id if update.effective_chat else None
        
        if target_chat_id != originating_chat_id or response.reply_to_message_id:
            if self._bot and hasattr(self._bot, 'application') and self._bot.application:
                await self._bot.application.bot.send_message(
                    chat_id=target_chat_id,
                    text=response.text,
                    parse_mode=response.parse_mode,
                    reply_to_message_id=response.reply_to_message_id,
                    reply_markup=response.reply_markup,
                )
        else:
            await update.message.reply_text(
                response.text,
                parse_mode=response.parse_mode,
                reply_markup=response.reply_markup,
            )
    
    def register_command_handler(
        self,
        command: str,
        handler: Callable[[Any], Awaitable[Any]],
    ) -> None:
        """
        Register a command handler with protocol-compliant wrapper.
        
        Converts Update/Context to TelegramMessage and TelegramResponse back to Telegram API calls.
        """
        if self._bot is not None and hasattr(self._bot, 'application'):
            from telegram.ext import CommandHandler
            
            async def wrapped_handler(update, context):
                from src.omnix.application.ports.telegram_port import TelegramMessage, TelegramResponse
                
                msg = TelegramMessage(
                    chat_id=update.effective_chat.id,
                    user_id=update.effective_user.id,
                    username=update.effective_user.username,
                    text=update.message.text or "",
                    message_id=update.message.message_id,
                    is_command=True,
                    command=command,
                    command_args=update.message.text.split(maxsplit=1)[1] if ' ' in (update.message.text or "") else None,
                )
                
                try:
                    response = await handler(msg)
                    if isinstance(response, TelegramResponse):
                        await self._send_response(update, response)
                except Exception as e:
                    logger.error(f"TelegramBotAdapter: Handler error for /{command}: {e}")
            
            self._bot.application.add_handler(CommandHandler(command, wrapped_handler))
            logger.info(f"TelegramBotAdapter: Registered command handler for /{command}")
    
    def register_message_handler(
        self,
        handler: Callable[[Any], Awaitable[Any]],
    ) -> None:
        """
        Register a general message handler with protocol-compliant wrapper.
        
        Converts Update/Context to TelegramMessage and TelegramResponse back to Telegram API calls.
        """
        if self._bot is not None and hasattr(self._bot, 'application'):
            from telegram.ext import MessageHandler, filters
            
            async def wrapped_handler(update, context):
                from src.omnix.application.ports.telegram_port import TelegramMessage, TelegramResponse
                
                if not update.message or not update.message.text:
                    return
                
                msg = TelegramMessage(
                    chat_id=update.effective_chat.id,
                    user_id=update.effective_user.id,
                    username=update.effective_user.username,
                    text=update.message.text,
                    message_id=update.message.message_id,
                    is_command=False,
                )
                
                try:
                    response = await handler(msg)
                    if isinstance(response, TelegramResponse):
                        await self._send_response(update, response)
                except Exception as e:
                    logger.error(f"TelegramBotAdapter: Message handler error: {e}")
            
            self._bot.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wrapped_handler))
            logger.info("TelegramBotAdapter: Registered message handler")
    
    @property
    def bot(self) -> Optional[Any]:
        """Access underlying bot instance (for legacy compatibility)."""
        return self._bot
