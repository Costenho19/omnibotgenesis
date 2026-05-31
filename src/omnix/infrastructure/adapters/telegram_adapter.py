"""
OMNIX V7.0 Telegram Bot Adapter
================================
Phase 4D: Infrastructure adapter wrapping EnterpriseTelegramBot.
Enhanced with state isolation, async handlers, and telemetry.

This adapter implements ITelegramBot port, providing the bridge
between the hexagonal application layer and the legacy Telegram bot.

Migration Status: Phase 4D - USER INTERFACES MIGRATION
"""

import logging
import asyncio
import time
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, Callable, Awaitable, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """Finite state machine states for multi-step conversations."""
    IDLE = "idle"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    AWAITING_INPUT = "awaiting_input"
    AWAITING_SYMBOL = "awaiting_symbol"
    AWAITING_AMOUNT = "awaiting_amount"
    PROCESSING = "processing"


@dataclass
class UserSession:
    """Per-user session state for conversation tracking."""
    user_id: int
    chat_id: int
    state: ConversationState = ConversationState.IDLE
    context_data: Dict[str, Any] = field(default_factory=dict)
    last_activity: Optional[datetime] = None
    pending_action: Optional[str] = None
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def set_state(self, state: ConversationState, context: Optional[Dict] = None) -> None:
        """Transition to new state with optional context."""
        self.state = state
        if context:
            self.context_data.update(context)
        self.update_activity()
    
    def reset(self) -> None:
        """Reset to idle state."""
        self.state = ConversationState.IDLE
        self.context_data = {}
        self.pending_action = None
        self.update_activity()


class UserSessionManager:
    """
    Redis-backed per-user session manager for state isolation.
    
    Provides thread-safe session management with automatic expiry.
    Falls back to in-memory storage if Redis unavailable.
    """
    
    SESSION_TTL_SECONDS = 3600
    SESSION_KEY_PREFIX = "omnix:telegram:session:"
    
    def __init__(self, cache_adapter: Optional[Any] = None):
        """
        Initialize session manager.
        
        Args:
            cache_adapter: CacheAdapter instance for Redis storage (lazy-loaded if None)
        """
        self._cache_adapter = cache_adapter
        self._local_sessions: Dict[int, UserSession] = {}
    
    def _get_cache(self) -> Optional[Any]:
        """Lazy-load CacheAdapter."""
        if self._cache_adapter is not None:
            return self._cache_adapter
        
        try:
            from src.omnix.infrastructure.adapters.cache_adapter import CacheAdapter
            self._cache_adapter = CacheAdapter()
            return self._cache_adapter
        except ImportError:
            return None
    
    def _session_key(self, user_id: int) -> str:
        """Generate Redis key for user session."""
        return f"{self.SESSION_KEY_PREFIX}{user_id}"
    
    def get_session(self, user_id: int, chat_id: int) -> UserSession:
        """
        Get or create user session.
        
        First tries Redis, falls back to local memory.
        """
        cache = self._get_cache()
        
        if cache and cache.is_connected():
            try:
                data = cache.get_json(self._session_key(user_id))
                if data:
                    session = UserSession(
                        user_id=data['user_id'],
                        chat_id=data['chat_id'],
                        state=ConversationState(data.get('state', 'idle')),
                        context_data=data.get('context_data', {}),
                        last_activity=datetime.fromisoformat(data['last_activity']) if data.get('last_activity') else None,
                        pending_action=data.get('pending_action'),
                    )
                    return session
            except Exception as e:
                logger.warning(f"UserSessionManager: Redis read error: {e}")
        
        if user_id in self._local_sessions:
            return self._local_sessions[user_id]
        
        session = UserSession(user_id=user_id, chat_id=chat_id)
        session.update_activity()
        self._local_sessions[user_id] = session
        return session
    
    def save_session(self, session: UserSession) -> bool:
        """
        Persist user session.
        
        Saves to Redis if available, always updates local cache.
        """
        self._local_sessions[session.user_id] = session
        
        cache = self._get_cache()
        if cache and cache.is_connected():
            try:
                data = {
                    'user_id': session.user_id,
                    'chat_id': session.chat_id,
                    'state': session.state.value,
                    'context_data': session.context_data,
                    'last_activity': session.last_activity.isoformat() if session.last_activity else None,
                    'pending_action': session.pending_action,
                }
                return cache.set_json(
                    self._session_key(session.user_id),
                    data,
                    ttl_seconds=self.SESSION_TTL_SECONDS
                )
            except Exception as e:
                logger.warning(f"UserSessionManager: Redis write error: {e}")
        
        return True
    
    def delete_session(self, user_id: int) -> bool:
        """Delete user session from both stores."""
        self._local_sessions.pop(user_id, None)
        
        cache = self._get_cache()
        if cache and cache.is_connected():
            try:
                return cache.delete(self._session_key(user_id))
            except Exception:
                pass
        
        return True
    
    def get_active_sessions_count(self) -> int:
        """Get count of active local sessions."""
        return len(self._local_sessions)


@dataclass
class TelegramBotAdapter:
    """
    Infrastructure adapter for Telegram bot operations.
    
    Implements ITelegramBot port:
    - start/stop: Bot lifecycle management
    - send_message/send_voice: Message sending
    - register_command_handler: Command registration
    - register_message_handler: General message handling
    - register_callback_handler: Inline button callbacks
    
    Features:
    - Lazy loading of EnterpriseTelegramBot
    - Per-user state isolation via UserSessionManager
    - Conversation state machine for multi-step flows
    - Telemetry tracking (request_count, error_count, latency)
    - Graceful degradation if bot unavailable
    
    Strangler Fig: Wraps legacy EnterpriseTelegramBot without modification.
    """
    
    _bot: Optional[Any] = field(default=None, repr=False)
    _is_initialized: bool = field(default=False, repr=False)
    _is_running: bool = field(default=False, repr=False)
    _db_manager: Optional[Any] = field(default=None, repr=False)
    _session_manager: Optional[UserSessionManager] = field(default=None, repr=False)
    
    _request_count: int = field(default=0, repr=False)
    _message_count: int = field(default=0, repr=False)
    _command_count: int = field(default=0, repr=False)
    _callback_count: int = field(default=0, repr=False)
    _error_count: int = field(default=0, repr=False)
    _total_latency_ms: float = field(default=0.0, repr=False)
    _last_request: Optional[datetime] = field(default=None, repr=False)
    
    def __post_init__(self):
        self._session_manager = UserSessionManager()
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
    
    def _track_request(self, start_time: float, request_type: str = "general") -> None:
        """Track request telemetry."""
        self._request_count += 1
        self._last_request = datetime.utcnow()
        elapsed_ms = (time.time() - start_time) * 1000
        self._total_latency_ms += elapsed_ms
        
        if request_type == "message":
            self._message_count += 1
        elif request_type == "command":
            self._command_count += 1
        elif request_type == "callback":
            self._callback_count += 1
    
    def _track_error(self) -> None:
        """Track error occurrence."""
        self._error_count += 1
    
    async def start(self) -> bool:
        """
        Start the Telegram bot (initialization only).
        
        For PTB v20+, initializes and starts the Application but does NOT
        mark _is_running=True. That flag is controlled by run_polling().
        
        NOTE: This method prepares the bot but does NOT block.
        Call run_polling() after start() to enter the blocking loop.
        """
        start_time = time.time()
        
        if not self._is_initialized or self._bot is None:
            logger.error("TelegramBotAdapter: Cannot start - bot not initialized")
            self._track_error()
            return False
        
        try:
            if hasattr(self._bot, 'application') and self._bot.application:
                app = self._bot.application
                if not app.running:
                    await app.initialize()
                    await app.start()
                logger.info("TelegramBotAdapter: Bot started via Application")
                self._track_request(start_time)
                return True
            elif hasattr(self._bot, 'start'):
                await self._bot.start()
                self._track_request(start_time)
                return True
        except Exception as e:
            logger.error(f"TelegramBotAdapter: Failed to start: {e}")
            self._track_error()
        return False
    
    async def stop(self) -> bool:
        """
        Stop the Telegram bot gracefully.
        
        For PTB v20+, properly stops updater and application.
        """
        start_time = time.time()
        
        if not self._is_initialized or self._bot is None:
            return True
        
        try:
            if hasattr(self._bot, 'application') and self._bot.application:
                app = self._bot.application
                if hasattr(app, 'updater') and app.updater and app.updater.running:
                    await app.updater.stop()
                if app.running:
                    await app.stop()
                await app.shutdown()
                self._is_running = False
                logger.info("TelegramBotAdapter: Bot stopped via Application")
                self._track_request(start_time)
                return True
            elif hasattr(self._bot, 'stop'):
                await self._bot.stop()
                self._is_running = False
                logger.info("TelegramBotAdapter: Bot stopped")
                self._track_request(start_time)
                return True
            else:
                self._is_running = False
                return True
        except Exception as e:
            logger.error(f"TelegramBotAdapter: Failed to stop: {e}")
            self._track_error()
            return False
    
    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict[str, Any]] = None,
        reply_to_message_id: Optional[int] = None,
    ) -> bool:
        """Send a text message to a chat."""
        start_time = time.time()
        
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
                    reply_to_message_id=reply_to_message_id,
                )
                self._track_request(start_time, "message")
                return True
        except Exception as e:
            logger.error(f"TelegramBotAdapter: Failed to send message: {e}")
            self._track_error()
        return False
    
    async def send_voice(
        self,
        chat_id: int,
        voice_data: bytes,
        caption: Optional[str] = None,
    ) -> bool:
        """Send a voice message to a chat."""
        start_time = time.time()
        
        if not self._is_initialized or self._bot is None:
            return False
        
        try:
            if hasattr(self._bot, 'application') and self._bot.application:
                await self._bot.application.bot.send_voice(
                    chat_id=chat_id,
                    voice=voice_data,
                    caption=caption,
                )
                self._track_request(start_time, "message")
                return True
        except Exception as e:
            logger.error(f"TelegramBotAdapter: Failed to send voice: {e}")
            self._track_error()
        return False
    
    async def edit_message(
        self,
        chat_id: int,
        message_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Edit an existing message."""
        start_time = time.time()
        
        if not self._is_initialized or self._bot is None:
            return False
        
        try:
            if hasattr(self._bot, 'application') and self._bot.application:
                await self._bot.application.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )
                self._track_request(start_time, "message")
                return True
        except Exception as e:
            logger.error(f"TelegramBotAdapter: Failed to edit message: {e}")
            self._track_error()
        return False
    
    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False,
    ) -> bool:
        """Answer a callback query from inline button."""
        start_time = time.time()
        
        if not self._is_initialized or self._bot is None:
            return False
        
        try:
            if hasattr(self._bot, 'application') and self._bot.application:
                await self._bot.application.bot.answer_callback_query(
                    callback_query_id=callback_query_id,
                    text=text,
                    show_alert=show_alert,
                )
                self._track_request(start_time, "callback")
                return True
        except Exception as e:
            logger.error(f"TelegramBotAdapter: Failed to answer callback: {e}")
            self._track_error()
        return False
    
    def get_session(self, user_id: int, chat_id: int) -> UserSession:
        """Get user session for state isolation."""
        if self._session_manager is None:
            self._session_manager = UserSessionManager()
        return self._session_manager.get_session(user_id, chat_id)
    
    def save_session(self, session: UserSession) -> bool:
        """Save user session state."""
        if self._session_manager is None:
            return False
        return self._session_manager.save_session(session)
    
    def is_running(self) -> bool:
        """Check if bot is currently running."""
        return self._is_running
    
    async def run_polling(self) -> None:
        """
        Run the bot polling loop (blocking).
        
        PTB v21 pattern: Uses Application.updater.start_polling() + blocking loop.
        This method blocks until the bot is stopped or interrupted.
        
        Call start() first to initialize, then run_polling() to enter the loop.
        """
        if not self._is_initialized or self._bot is None:
            logger.error("TelegramBotAdapter: Cannot run_polling - bot not initialized")
            return
        
        if self._is_running:
            logger.warning("TelegramBotAdapter: run_polling already active, ignoring duplicate call")
            return
        
        app = None
        try:
            # FIX: Always use enterprise_bot.start_polling() so that all command
            # handlers are registered before polling starts. The previous path
            # called app.updater.start_polling() directly, bypassing handler
            # registration and leaving the bot unable to receive any commands.
            if hasattr(self._bot, 'start_polling'):
                start_polling = self._bot.start_polling
                logger.info("TelegramBotAdapter: Starting via enterprise_bot.start_polling() — handlers will be registered")
                self._is_running = True
                app = getattr(self._bot, 'application', None)

                if asyncio.iscoroutinefunction(start_polling):
                    await start_polling()
                else:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, start_polling)
            else:
                logger.error("TelegramBotAdapter: No polling method available")
                return
                
        except asyncio.CancelledError:
            logger.info("TelegramBotAdapter: Polling cancelled")
        except Exception as e:
            logger.error(f"TelegramBotAdapter: run_polling error: {e}")
            self._track_error()
            raise
        finally:
            self._is_running = False
            logger.info("TelegramBotAdapter: Cleaning up polling...")
            if app is not None:
                try:
                    if hasattr(app, 'updater') and app.updater and app.updater.running:
                        await app.updater.stop()
                    if app.running:
                        await app.stop()
                    await app.shutdown()
                    logger.info("TelegramBotAdapter: Application shutdown complete")
                except Exception as cleanup_error:
                    logger.warning(f"TelegramBotAdapter: cleanup error: {cleanup_error}")
    
    async def run_webhook(
        self,
        webhook_url: str,
        secret_token: str = "",
        port: int = 8080,
    ) -> None:
        """Run the bot in webhook mode — zero Conflict errors on Railway deploys.

        Delegates to enterprise_bot.start_webhook(), which registers the webhook
        with Telegram and binds an aiohttp server on 0.0.0.0:$PORT.

        Args:
            webhook_url:  Public HTTPS base URL, e.g. "https://omnix-bot.up.railway.app".
                          Set via TELEGRAM_WEBHOOK_URL env var.
            secret_token: 32+ char random string for Telegram → service auth.
                          Set via TELEGRAM_WEBHOOK_SECRET env var.
            port:         Port to listen on (matches Railway $PORT).
        """
        if not self._is_initialized or self._bot is None:
            logger.error("TelegramBotAdapter: Cannot run_webhook — bot not initialized")
            return

        if self._is_running:
            logger.warning("TelegramBotAdapter: run_webhook already active, ignoring duplicate call")
            return

        try:
            if hasattr(self._bot, 'start_webhook'):
                logger.info(
                    "TelegramBotAdapter: Starting via enterprise_bot.start_webhook() "
                    "— webhook mode, zero-conflict Railway deploys"
                )
                self._is_running = True
                await self._bot.start_webhook(
                    webhook_url=webhook_url,
                    secret_token=secret_token,
                    port=port,
                )
            else:
                logger.error("TelegramBotAdapter: start_webhook not available on bot instance")
        except asyncio.CancelledError:
            logger.info("TelegramBotAdapter: Webhook cancelled")
        except Exception as e:
            logger.error(f"TelegramBotAdapter: run_webhook error: {e}")
            self._track_error()
            raise
        finally:
            self._is_running = False
            logger.info("TelegramBotAdapter: Webhook stopped")

    def health_check(self) -> Dict[str, Any]:
        """
        Get bot health status and telemetry.
        
        Note: Does NOT inflate telemetry counters.
        """
        avg_latency = 0.0
        if self._request_count > 0:
            avg_latency = self._total_latency_ms / self._request_count
        
        error_rate = 0.0
        if self._request_count > 0:
            error_rate = self._error_count / self._request_count * 100
        
        active_sessions = 0
        if self._session_manager:
            active_sessions = self._session_manager.get_active_sessions_count()
        
        return {
            'healthy': self._is_initialized and self._bot is not None,
            'initialized': self._is_initialized,
            'running': self.is_running(),
            'has_bot': self._bot is not None,
            'has_application': (
                self._bot is not None and 
                hasattr(self._bot, 'application') and 
                self._bot.application is not None
            ),
            'request_count': self._request_count,
            'message_count': self._message_count,
            'command_count': self._command_count,
            'callback_count': self._callback_count,
            'error_count': self._error_count,
            'avg_latency_ms': round(avg_latency, 2),
            'error_rate_pct': round(error_rate, 2),
            'active_sessions': active_sessions,
            'last_request': self._last_request.isoformat() if self._last_request else None,
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
        Includes session injection for state isolation.
        """
        if self._bot is None or not hasattr(self._bot, 'application'):
            logger.warning(f"TelegramBotAdapter: Cannot register command /{command} - no application")
            return
        
        from telegram.ext import CommandHandler
        adapter = self
        
        async def wrapped_handler(update, context):
            start_time = time.time()
            from src.omnix.application.ports.telegram_port import TelegramMessage, TelegramResponse
            
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            session = adapter.get_session(user_id, chat_id)
            
            msg = TelegramMessage(
                chat_id=chat_id,
                user_id=user_id,
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
                    await adapter._send_response(update, response)
                session.update_activity()
                adapter.save_session(session)
                adapter._track_request(start_time, "command")
            except Exception as e:
                logger.error(f"TelegramBotAdapter: Handler error for /{command}: {e}")
                adapter._track_error()
        
        self._bot.application.add_handler(CommandHandler(command, wrapped_handler))
        logger.info(f"TelegramBotAdapter: Registered command handler for /{command}")
    
    def register_message_handler(
        self,
        handler: Callable[[Any], Awaitable[Any]],
    ) -> None:
        """
        Register a general message handler with protocol-compliant wrapper.
        
        Converts Update/Context to TelegramMessage and TelegramResponse back to Telegram API calls.
        Includes session injection for state isolation.
        """
        if self._bot is None or not hasattr(self._bot, 'application'):
            logger.warning("TelegramBotAdapter: Cannot register message handler - no application")
            return
        
        from telegram.ext import MessageHandler, filters
        adapter = self
        
        async def wrapped_handler(update, context):
            start_time = time.time()
            from src.omnix.application.ports.telegram_port import TelegramMessage, TelegramResponse
            
            if not update.message or not update.message.text:
                return
            
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            session = adapter.get_session(user_id, chat_id)
            
            msg = TelegramMessage(
                chat_id=chat_id,
                user_id=user_id,
                username=update.effective_user.username,
                text=update.message.text,
                message_id=update.message.message_id,
                is_command=False,
            )
            
            try:
                response = await handler(msg)
                if isinstance(response, TelegramResponse):
                    await adapter._send_response(update, response)
                session.update_activity()
                adapter.save_session(session)
                adapter._track_request(start_time, "message")
            except Exception as e:
                logger.error(f"TelegramBotAdapter: Message handler error: {e}")
                adapter._track_error()
        
        self._bot.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, wrapped_handler))
        logger.info("TelegramBotAdapter: Registered message handler")
    
    def register_callback_handler(
        self,
        pattern: Optional[str] = None,
        handler: Optional[Callable[[Any], Awaitable[Any]]] = None,
    ) -> None:
        """
        Register a callback query handler for inline buttons.
        
        Args:
            pattern: Regex pattern to match callback_data (None matches all)
            handler: Async function to handle the callback
        
        The handler receives a CallbackMessage dataclass with:
        - chat_id, user_id, username
        - callback_data: The data from the inline button
        - message_id: ID of the message with the button
        """
        if self._bot is None or not hasattr(self._bot, 'application'):
            logger.warning("TelegramBotAdapter: Cannot register callback handler - no application")
            return
        
        if handler is None:
            logger.warning("TelegramBotAdapter: No handler provided for callback")
            return
        
        from telegram.ext import CallbackQueryHandler
        adapter = self
        
        async def wrapped_handler(update, context):
            start_time = time.time()
            from src.omnix.application.ports.telegram_port import TelegramResponse
            
            query = update.callback_query
            if not query:
                return
            
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            session = adapter.get_session(user_id, chat_id)
            
            callback_msg = {
                'chat_id': chat_id,
                'user_id': user_id,
                'username': update.effective_user.username,
                'callback_data': query.data,
                'message_id': query.message.message_id if query.message else None,
                'callback_query_id': query.id,
            }
            
            try:
                await query.answer()
                
                response = await handler(callback_msg)
                if isinstance(response, TelegramResponse):
                    if query.message:
                        await adapter.edit_message(
                            chat_id=chat_id,
                            message_id=query.message.message_id,
                            text=response.text,
                            parse_mode=response.parse_mode,
                            reply_markup=response.reply_markup,
                        )
                    else:
                        await adapter.send_message(
                            chat_id=chat_id,
                            text=response.text,
                            parse_mode=response.parse_mode,
                            reply_markup=response.reply_markup,
                        )
                
                session.update_activity()
                adapter.save_session(session)
                adapter._track_request(start_time, "callback")
            except Exception as e:
                logger.error(f"TelegramBotAdapter: Callback handler error: {e}")
                adapter._track_error()
        
        self._bot.application.add_handler(CallbackQueryHandler(wrapped_handler, pattern=pattern))
        pattern_desc = pattern if pattern else "all"
        logger.info(f"TelegramBotAdapter: Registered callback handler for pattern: {pattern_desc}")
    
    @property
    def bot(self) -> Optional[Any]:
        """Access underlying bot instance (for legacy compatibility)."""
        return self._bot
    
    @property
    def session_manager(self) -> Optional[UserSessionManager]:
        """Access session manager for direct session operations."""
        return self._session_manager
