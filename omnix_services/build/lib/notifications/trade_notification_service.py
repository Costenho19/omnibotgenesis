"""
📢 OMNIX TRADE NOTIFICATION SERVICE V6.4 PREMIUM
Sistema de notificaciones en tiempo real para trades ejecutados

CARACTERÍSTICAS PREMIUM:
- Notificaciones instantáneas de BUY/SELL
- Detalles completos del trade (precio, cantidad, señal)
- P&L en tiempo real para trades cerrados
- Formato institucional con emojis premium
- Integración directa con Telegram
"""

import logging
from datetime import datetime
from typing import Dict, Optional, List
import asyncio

from .telegram_utils import split_message

logger = logging.getLogger(__name__)


class TradeNotificationService:
    """
    Servicio Premium de Notificaciones de Trading V6.4
    
    Envía alertas en tiempo real a Telegram cuando se ejecutan trades,
    con información detallada y formato institucional.
    """
    
    def __init__(self, telegram_bot=None, database_service=None):
        self.telegram_bot = telegram_bot
        self.database_service = database_service
        self.admin_chat_ids = []
        self._load_admin_users()
        logger.info("📢 TradeNotificationService V6.4 PREMIUM inicializado")
    
    def _load_admin_users(self):
        """Cargar lista de usuarios admin para notificaciones"""
        try:
            if self.database_service and hasattr(self.database_service, 'execute_query'):
                result = self.database_service.execute_query(
                    "SELECT user_id FROM users WHERE is_admin = TRUE"
                )
                if result:
                    self.admin_chat_ids = [str(row[0]) for row in result]
                    logger.info(f"📢 Admins cargados para notificaciones: {len(self.admin_chat_ids)}")
        except Exception as e:
            logger.warning(f"No se pudieron cargar admins: {e}")
    
    def set_admin_chat_id(self, chat_id: str):
        """Configurar chat_id de admin manualmente"""
        if chat_id not in self.admin_chat_ids:
            self.admin_chat_ids.append(str(chat_id))
            logger.info(f"📢 Admin chat_id agregado: {chat_id}")
    
    async def notify_trade_opened(self, trade_data: Dict, chat_id: str = None) -> bool:
        """
        Notificar apertura de posición (BUY)
        
        Args:
            trade_data: Datos del trade ejecutado
            chat_id: ID del chat a notificar (None = todos los admins)
        """
        try:
            symbol = trade_data.get('symbol', 'UNKNOWN')
            entry_price = trade_data.get('entry_price', 0)
            quantity = trade_data.get('quantity', 0)
            amount_usd = trade_data.get('amount_usd', 0)
            strategy = trade_data.get('strategy', 'auto')
            signal_strength = trade_data.get('signal_strength', 'MODERATE')
            confidence = trade_data.get('confidence', 0)
            
            emoji_strength = self._get_signal_emoji(signal_strength)
            
            message = f"""
🟢 *COMPRA EJECUTADA*

📊 *{symbol}*
━━━━━━━━━━━━━━━━━━
💰 Precio entrada: `${entry_price:,.2f}`
📦 Cantidad: `{quantity:.6f}`
💵 Monto USD: `${amount_usd:,.2f}`

{emoji_strength} Señal: *{signal_strength}*
🎯 Confianza: `{confidence:.1f}%`
🤖 Estrategia: `{strategy}`

⏰ {datetime.now().strftime('%H:%M:%S')} UTC
"""
            
            return await self._send_notification(message, chat_id)
            
        except Exception as e:
            logger.error(f"Error notificando trade abierto: {e}")
            return False
    
    async def notify_trade_closed(self, trade_data: Dict, chat_id: str = None) -> bool:
        """
        Notificar cierre de posición (SELL) con P&L
        
        Args:
            trade_data: Datos del trade cerrado incluyendo P&L
            chat_id: ID del chat a notificar
        """
        try:
            symbol = trade_data.get('symbol', 'UNKNOWN')
            entry_price = trade_data.get('entry_price', 0)
            exit_price = trade_data.get('exit_price', 0)
            quantity = trade_data.get('base_quantity', trade_data.get('quantity', 0))
            pnl = trade_data.get('net_realized_pnl_usd', 0)
            pnl_pct = trade_data.get('profit_pct', 0)
            duration = trade_data.get('duration_seconds', 0)
            is_winning = trade_data.get('is_winning_trade', pnl > 0)
            
            emoji_result = "🟢" if is_winning else "🔴"
            pnl_text = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
            pnl_pct_text = f"+{pnl_pct:.2f}%" if pnl_pct >= 0 else f"{pnl_pct:.2f}%"
            duration_text = self._format_duration(duration)
            
            message = f"""
{emoji_result} *VENTA EJECUTADA*

📊 *{symbol}*
━━━━━━━━━━━━━━━━━━
📥 Entrada: `${entry_price:,.2f}`
📤 Salida: `${exit_price:,.2f}`
📦 Cantidad: `{quantity:.6f}`

💰 *P&L: {pnl_text} ({pnl_pct_text})*
⏱️ Duración: `{duration_text}`

⏰ {datetime.now().strftime('%H:%M:%S')} UTC
"""
            
            return await self._send_notification(message, chat_id)
            
        except Exception as e:
            logger.error(f"Error notificando trade cerrado: {e}")
            return False
    
    async def notify_trade_executed(self, side: str, trade_data: Dict, chat_id: str = None) -> bool:
        """
        Notificación unificada para cualquier trade
        
        Args:
            side: 'buy' o 'sell'
            trade_data: Datos del trade
            chat_id: Chat destino
        """
        if side.lower() == 'buy':
            return await self.notify_trade_opened(trade_data, chat_id)
        else:
            return await self.notify_trade_closed(trade_data, chat_id)
    
    def notify_trade_sync(self, side: str, trade_data: Dict, chat_id: str = None) -> bool:
        """
        Versión síncrona para usar desde código no-async
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.notify_trade_executed(side, trade_data, chat_id))
                return True
            else:
                return loop.run_until_complete(
                    self.notify_trade_executed(side, trade_data, chat_id)
                )
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.notify_trade_executed(side, trade_data, chat_id)
                )
            finally:
                loop.close()
    
    async def _send_notification(self, message: str, chat_id: str = None) -> bool:
        """Enviar notificación a Telegram con soporte para mensajes largos"""
        try:
            if not self.telegram_bot:
                logger.warning("📢 Telegram bot no configurado para notificaciones")
                return False
            
            chat_ids = [chat_id] if chat_id else self.admin_chat_ids
            
            if not chat_ids:
                logger.warning("📢 No hay chat_ids configurados para notificaciones")
                return False
            
            message_parts = split_message(message)
            
            success_count = 0
            for cid in chat_ids:
                try:
                    for part in message_parts:
                        if hasattr(self.telegram_bot, 'send_message'):
                            await self.telegram_bot.send_message(
                                chat_id=int(cid),
                                text=part,
                                parse_mode='Markdown'
                            )
                        elif hasattr(self.telegram_bot, 'bot') and hasattr(self.telegram_bot.bot, 'send_message'):
                            await self.telegram_bot.bot.send_message(
                                chat_id=int(cid),
                                text=part,
                                parse_mode='Markdown'
                            )
                    success_count += 1
                except Exception as send_err:
                    logger.warning(f"Error enviando a {cid}: {send_err}")
            
            if success_count > 0:
                logger.info(f"📢 Notificación enviada a {success_count} chats ({len(message_parts)} partes)")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error enviando notificación: {e}")
            return False
    
    def _get_signal_emoji(self, strength: str) -> str:
        """Obtener emoji según fuerza de señal"""
        emojis = {
            'VERY_STRONG': '🔥',
            'STRONG': '💪',
            'MODERATE': '📊',
            'WEAK': '📉'
        }
        return emojis.get(strength.upper(), '📊')
    
    def _format_duration(self, seconds: int) -> str:
        """Formatear duración de trade"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
