"""
OMNIX V7.0 Notification Infrastructure Adapter
===============================================
Phase 4A: Implements NotificationPort by wrapping legacy telegram_utils
and TelegramBotAdapter. Strangler Fig pattern - zero modifications to legacy code.

Migration Status: Phase 4A - LOW-COUPLING SERVICES
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class NotificationAdapter:
    """
    Infrastructure adapter for notifications via Telegram.
    
    Implements NotificationPort:
    - send_message: Send text message to user
    - send_trade_alert: Send formatted trade alert
    
    Features:
    - Message splitting for Telegram 4096 char limit
    - Rate limiting awareness
    - Telemetry and request tracking
    - Graceful degradation if Telegram unavailable
    
    Strangler Fig: Wraps legacy telegram_utils without modification.
    """
    
    def __init__(
        self,
        telegram_adapter: Optional[Any] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize notification adapter.
        
        Args:
            telegram_adapter: TelegramBotAdapter instance (lazy-loaded if None)
            max_retries: Maximum retry attempts for failed sends
            retry_delay: Delay between retries in seconds
        """
        self._telegram_adapter = telegram_adapter
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        
        self._request_count = 0
        self._success_count = 0
        self._error_count = 0
        self._last_request: Optional[datetime] = None
        
        self._split_message = None
        self._truncate_message = None
        self._init_legacy_utils()
    
    def _init_legacy_utils(self):
        """Initialize legacy telegram_utils functions."""
        try:
            from omnix_services.notifications.telegram_utils import (
                split_message,
                truncate_message,
                SAFE_MAX_LENGTH
            )
            self._split_message = split_message
            self._truncate_message = truncate_message
            self._safe_max_length = SAFE_MAX_LENGTH
            logger.info("NotificationAdapter: Legacy telegram_utils loaded")
        except ImportError as e:
            logger.warning(f"NotificationAdapter: telegram_utils not available: {e}")
            self._safe_max_length = 4000
    
    def _get_telegram_adapter(self) -> Optional[Any]:
        """Lazy-load TelegramBotAdapter from container."""
        if self._telegram_adapter is not None:
            return self._telegram_adapter
        
        try:
            from src.omnix.bootstrap.container import get_container
            container = get_container()
            self._telegram_adapter = container.telegram_adapter
            return self._telegram_adapter
        except Exception as e:
            logger.error(f"NotificationAdapter: Failed to get telegram_adapter: {e}")
            return None
    
    async def send_message(
        self,
        recipient_id: str,
        message: str,
        parse_mode: str = 'HTML'
    ) -> bool:
        """
        Send text message to recipient.
        
        Implements NotificationPort.send_message.
        Handles message splitting for Telegram limits.
        
        Args:
            recipient_id: User or chat ID (string, converted to int for Telegram)
            message: Message text to send
            parse_mode: 'HTML' or 'Markdown'
            
        Returns:
            True if all message parts sent successfully
        """
        self._request_count += 1
        self._last_request = datetime.utcnow()
        
        if not message or not message.strip():
            logger.warning("NotificationAdapter: Empty message, skipping send")
            return True
        
        adapter = self._get_telegram_adapter()
        if adapter is None:
            logger.error("NotificationAdapter: No telegram adapter available")
            self._error_count += 1
            return False
        
        try:
            chat_id = int(recipient_id)
        except (ValueError, TypeError):
            logger.error(f"NotificationAdapter: Invalid recipient_id: {recipient_id}")
            self._error_count += 1
            return False
        
        if self._split_message:
            parts = self._split_message(message)
        else:
            parts = [message] if len(message) <= self._safe_max_length else [message[:self._safe_max_length]]
        
        all_sent = True
        for part in parts:
            try:
                success = await adapter.send_message(
                    chat_id=chat_id,
                    text=part,
                    parse_mode=parse_mode
                )
                if not success:
                    all_sent = False
                    self._error_count += 1
            except Exception as e:
                logger.error(f"NotificationAdapter: Failed to send message part: {e}")
                all_sent = False
                self._error_count += 1
        
        if all_sent:
            self._success_count += 1
        
        return all_sent
    
    async def send_trade_alert(
        self,
        recipient_id: str,
        trade_data: dict
    ) -> bool:
        """
        Send formatted trade alert to recipient.
        
        Implements NotificationPort.send_trade_alert.
        Formats trade data into a rich HTML message.
        
        Args:
            recipient_id: User or chat ID
            trade_data: Trade details dict with keys:
                - symbol: Trading pair (e.g., 'BTC/USD')
                - side: 'BUY' or 'SELL'
                - amount: Trade amount
                - price: Execution price
                - profit_loss: Optional P/L amount
                - profit_loss_pct: Optional P/L percentage
                - reason: Optional trade reason
                
        Returns:
            True if alert sent successfully
        """
        self._request_count += 1
        self._last_request = datetime.utcnow()
        
        message = self._format_trade_alert(trade_data)
        return await self.send_message(recipient_id, message, parse_mode='HTML')
    
    def _format_trade_alert(self, trade_data: dict) -> str:
        """Format trade data into HTML message."""
        symbol = trade_data.get('symbol', 'UNKNOWN')
        side = trade_data.get('side', 'UNKNOWN')
        amount = trade_data.get('amount', 0)
        price = trade_data.get('price', 0)
        
        side_emoji = "🟢" if side.upper() == "BUY" else "🔴"
        
        lines = [
            f"{side_emoji} <b>TRADE ALERT</b> {side_emoji}",
            "",
            f"<b>Pair:</b> {symbol}",
            f"<b>Side:</b> {side.upper()}",
            f"<b>Amount:</b> {amount:,.8f}",
            f"<b>Price:</b> ${price:,.2f}",
        ]
        
        if 'profit_loss' in trade_data:
            pl = trade_data['profit_loss']
            pl_pct = trade_data.get('profit_loss_pct', 0)
            pl_emoji = "📈" if pl >= 0 else "📉"
            lines.extend([
                "",
                f"{pl_emoji} <b>P/L:</b> ${pl:,.2f} ({pl_pct:+.2f}%)"
            ])
        
        if 'reason' in trade_data:
            lines.extend([
                "",
                f"<i>{trade_data['reason']}</i>"
            ])
        
        lines.extend([
            "",
            f"<code>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</code>"
        ])
        
        return "\n".join(lines)
    
    def health_check(self) -> Dict[str, Any]:
        """Get adapter health status and telemetry."""
        adapter = self._get_telegram_adapter()
        adapter_healthy = False
        
        if adapter is not None:
            if hasattr(adapter, 'health_check'):
                adapter_status = adapter.health_check()
                adapter_healthy = adapter_status.get('initialized', False)
            else:
                adapter_healthy = True
        
        success_rate = (
            self._success_count / self._request_count * 100
            if self._request_count > 0 else 100.0
        )
        
        return {
            'healthy': adapter_healthy,
            'telegram_adapter_available': adapter is not None,
            'legacy_utils_loaded': self._split_message is not None,
            'request_count': self._request_count,
            'success_count': self._success_count,
            'error_count': self._error_count,
            'success_rate_pct': round(success_rate, 2),
            'last_request': self._last_request.isoformat() if self._last_request else None,
        }
