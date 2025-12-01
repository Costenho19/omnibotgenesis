"""
📊 OMNIX DAILY SUMMARY SERVICE V6.4 PREMIUM
Resúmenes diarios automáticos con métricas institucionales

CARACTERÍSTICAS PREMIUM:
- Resumen automático a hora configurable
- Métricas institucionales (Win Rate, P&L, Sharpe)
- Comparativa vs Bitcoin HODL
- Mejor/peor trade del día
- Formato premium para inversores
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import threading
import time

logger = logging.getLogger(__name__)


class DailySummaryService:
    """
    Servicio de Resúmenes Diarios V6.4 PREMIUM
    
    Genera y envía resúmenes automáticos con métricas
    institucionales y comparativa vs benchmark.
    """
    
    def __init__(self, telegram_bot=None, database_service=None, trading_service=None):
        self.telegram_bot = telegram_bot
        self.database_service = database_service
        self.trading_service = trading_service
        self.admin_chat_ids = []
        self.summary_hour = 20
        self.summary_minute = 0
        self.timezone_offset = -8
        self._scheduler_thread = None
        self._running = False
        self._load_admin_users()
        logger.info(f"📊 DailySummaryService V6.4 PREMIUM inicializado - Resumen a las {self.summary_hour}:00")
    
    def _load_admin_users(self):
        """Cargar lista de usuarios admin"""
        try:
            if self.database_service and hasattr(self.database_service, 'execute_query'):
                result = self.database_service.execute_query(
                    "SELECT user_id FROM users WHERE is_admin = TRUE"
                )
                if result:
                    self.admin_chat_ids = [str(row[0]) for row in result]
        except Exception as e:
            logger.warning(f"No se pudieron cargar admins: {e}")
    
    def set_admin_chat_id(self, chat_id: str):
        """Configurar chat_id de admin"""
        if chat_id not in self.admin_chat_ids:
            self.admin_chat_ids.append(str(chat_id))
    
    def set_summary_time(self, hour: int, minute: int = 0):
        """Configurar hora de resumen diario"""
        self.summary_hour = hour
        self.summary_minute = minute
        logger.info(f"📊 Resumen diario configurado para las {hour}:{minute:02d}")
    
    def start_scheduler(self):
        """Iniciar scheduler de resúmenes"""
        if self._running:
            return
        
        self._running = True
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True
        )
        self._scheduler_thread.start()
        logger.info("📊 Scheduler de resúmenes diarios iniciado")
    
    def stop_scheduler(self):
        """Detener scheduler"""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        logger.info("📊 Scheduler de resúmenes detenido")
    
    def _scheduler_loop(self):
        """Loop del scheduler - Ejecuta resumen a hora configurada"""
        last_summary_date = None
        
        while self._running:
            try:
                now = datetime.utcnow()
                current_hour = now.hour
                current_minute = now.minute
                current_date = now.date()
                
                should_send = (
                    current_hour == self.summary_hour and
                    current_minute >= self.summary_minute and
                    current_minute < self.summary_minute + 5 and
                    last_summary_date != current_date
                )
                
                if should_send:
                    logger.info(f"📊 Ejecutando resumen diario programado ({self.summary_hour}:{self.summary_minute:02d} UTC)")
                    try:
                        self.send_daily_summary_sync()
                    except Exception as send_err:
                        logger.error(f"Error enviando resumen: {send_err}")
                    last_summary_date = current_date
                
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error en scheduler loop: {e}")
                time.sleep(60)
    
    async def send_daily_summary(self, chat_id: str = None) -> bool:
        """
        Generar y enviar resumen diario
        """
        try:
            summary = self._generate_summary()
            if not summary:
                logger.warning("No hay datos para resumen diario")
                return False
            
            message = self._format_summary_message(summary)
            return await self._send_message(message, chat_id)
            
        except Exception as e:
            logger.error(f"Error enviando resumen diario: {e}")
            return False
    
    def send_daily_summary_sync(self, chat_id: str = None) -> bool:
        """Versión síncrona del resumen diario"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.send_daily_summary(chat_id))
                return True
            else:
                return loop.run_until_complete(self.send_daily_summary(chat_id))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.send_daily_summary(chat_id))
            finally:
                loop.close()
    
    def _generate_summary(self) -> Optional[Dict]:
        """Generar datos del resumen"""
        try:
            if not self.database_service:
                return None
            
            today = datetime.utcnow().date().isoformat()
            
            trades_query = """
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN profit_loss <= 0 THEN 1 ELSE 0 END) as losses,
                    COALESCE(SUM(profit_loss), 0) as total_pnl,
                    MAX(profit_loss) as best_trade,
                    MIN(profit_loss) as worst_trade,
                    AVG(profit_loss) as avg_pnl
                FROM paper_trading_trades
                WHERE status = 'closed'
                AND DATE(closed_at) = %s
            """
            
            result = self.database_service.execute_query(trades_query, (today,))
            
            if not result or len(result) == 0:
                return None
            
            row = result[0]
            total_trades = int(row[0] or 0)
            wins = int(row[1] or 0)
            losses = int(row[2] or 0)
            total_pnl = float(row[3] or 0)
            best_trade = float(row[4] or 0)
            worst_trade = float(row[5] or 0)
            avg_pnl = float(row[6] or 0)
            
            if total_trades == 0:
                return None
            
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
            
            balance_query = """
                SELECT balance_usd, total_realized_pnl_usd
                FROM paper_trading_balances
                LIMIT 1
            """
            balance_result = self.database_service.execute_query(balance_query)
            current_balance = 1_000_000.0
            total_realized_pnl = 0.0
            
            if balance_result and len(balance_result) > 0:
                current_balance = float(balance_result[0][0] or 1_000_000)
                total_realized_pnl = float(balance_result[0][1] or 0)
            
            benchmark = self._calculate_benchmark_comparison()
            
            return {
                'date': today,
                'total_trades': total_trades,
                'wins': wins,
                'losses': losses,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'best_trade': best_trade,
                'worst_trade': worst_trade,
                'avg_pnl': avg_pnl,
                'current_balance': current_balance,
                'total_realized_pnl': total_realized_pnl,
                'benchmark': benchmark
            }
            
        except Exception as e:
            logger.error(f"Error generando summary: {e}")
            return None
    
    def _calculate_benchmark_comparison(self) -> Dict:
        """Calcular comparativa vs Bitcoin HODL"""
        try:
            if not self.database_service:
                return {'available': False}
            
            first_trade_query = """
                SELECT MIN(opened_at), entry_price, symbol
                FROM paper_trading_trades
                WHERE symbol LIKE '%BTC%'
                GROUP BY entry_price, symbol
                ORDER BY MIN(opened_at) ASC
                LIMIT 1
            """
            result = self.database_service.execute_query(first_trade_query)
            
            if not result or len(result) == 0:
                return {'available': False}
            
            first_date, first_btc_price, _ = result[0]
            
            current_btc_price = self._get_current_btc_price()
            if not current_btc_price:
                return {'available': False}
            
            btc_hodl_return = ((current_btc_price / float(first_btc_price)) - 1) * 100
            
            balance_query = """
                SELECT total_realized_pnl_usd FROM paper_trading_balances LIMIT 1
            """
            balance_result = self.database_service.execute_query(balance_query)
            omnix_pnl = 0
            if balance_result and len(balance_result) > 0:
                omnix_pnl = float(balance_result[0][0] or 0)
            
            omnix_return = (omnix_pnl / 1_000_000) * 100
            alpha = omnix_return - btc_hodl_return
            
            return {
                'available': True,
                'btc_hodl_return': btc_hodl_return,
                'omnix_return': omnix_return,
                'alpha': alpha,
                'first_btc_price': float(first_btc_price),
                'current_btc_price': current_btc_price
            }
            
        except Exception as e:
            logger.warning(f"Error calculando benchmark: {e}")
            return {'available': False}
    
    def _get_current_btc_price(self) -> Optional[float]:
        """Obtener precio actual de BTC"""
        try:
            if self.trading_service and hasattr(self.trading_service, 'get_ticker'):
                ticker = self.trading_service.get_ticker('BTC/USD')
                if ticker and 'last' in ticker:
                    return float(ticker['last'])
            
            import requests
            response = requests.get(
                'https://api.kraken.com/0/public/Ticker?pair=XBTUSD',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if 'result' in data:
                    for key in data['result']:
                        return float(data['result'][key]['c'][0])
                        
        except Exception as e:
            logger.warning(f"Error obteniendo precio BTC: {e}")
        return None
    
    def _format_summary_message(self, summary: Dict) -> str:
        """Formatear mensaje de resumen premium"""
        try:
            pnl = summary['total_pnl']
            pnl_emoji = "🟢" if pnl >= 0 else "🔴"
            pnl_text = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
            
            best = summary['best_trade']
            worst = summary['worst_trade']
            best_text = f"+${best:,.2f}" if best >= 0 else f"-${abs(best):,.2f}"
            worst_text = f"+${worst:,.2f}" if worst >= 0 else f"-${abs(worst):,.2f}"
            
            balance_pct = ((summary['current_balance'] / 1_000_000) - 1) * 100
            balance_emoji = "📈" if balance_pct >= 0 else "📉"
            
            message = f"""
📊 *RESUMEN DIARIO OMNIX*
━━━━━━━━━━━━━━━━━━━━━
📅 {summary['date']}

🎯 *TRADES DEL DÍA*
├ Total: `{summary['total_trades']}`
├ Ganados: `{summary['wins']}` ✅
├ Perdidos: `{summary['losses']}` ❌
└ Win Rate: `{summary['win_rate']:.1f}%`

{pnl_emoji} *P&L DEL DÍA: {pnl_text}*
├ Mejor trade: `{best_text}`
├ Peor trade: `{worst_text}`
└ Promedio: `${summary['avg_pnl']:,.2f}`

{balance_emoji} *BALANCE TOTAL*
├ Actual: `${summary['current_balance']:,.2f}`
├ P&L Total: `${summary['total_realized_pnl']:,.2f}`
└ Retorno: `{balance_pct:+.2f}%`
"""
            
            benchmark = summary.get('benchmark', {})
            if benchmark.get('available'):
                alpha = benchmark['alpha']
                alpha_emoji = "🏆" if alpha > 0 else "📉"
                alpha_text = f"+{alpha:.2f}%" if alpha >= 0 else f"{alpha:.2f}%"
                
                message += f"""
{alpha_emoji} *VS BITCOIN HODL*
├ OMNIX: `{benchmark['omnix_return']:+.2f}%`
├ BTC HODL: `{benchmark['btc_hodl_return']:+.2f}%`
└ *Alpha: {alpha_text}*
"""
            
            message += f"""
━━━━━━━━━━━━━━━━━━━━━
🤖 _OMNIX V6.4 INSTITUTIONAL+_
"""
            
            return message
            
        except Exception as e:
            logger.error(f"Error formateando mensaje: {e}")
            return "📊 Error generando resumen"
    
    async def _send_message(self, message: str, chat_id: str = None) -> bool:
        """Enviar mensaje a Telegram"""
        try:
            if not self.telegram_bot:
                logger.warning("📊 Telegram bot no configurado")
                return False
            
            chat_ids = [chat_id] if chat_id else self.admin_chat_ids
            
            if not chat_ids:
                logger.warning("📊 No hay chat_ids configurados")
                return False
            
            success_count = 0
            for cid in chat_ids:
                try:
                    if hasattr(self.telegram_bot, 'send_message'):
                        await self.telegram_bot.send_message(
                            chat_id=int(cid),
                            text=message,
                            parse_mode='Markdown'
                        )
                        success_count += 1
                    elif hasattr(self.telegram_bot, 'bot'):
                        await self.telegram_bot.bot.send_message(
                            chat_id=int(cid),
                            text=message,
                            parse_mode='Markdown'
                        )
                        success_count += 1
                except Exception as send_err:
                    logger.warning(f"Error enviando a {cid}: {send_err}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
            return False
    
    def get_summary_now(self) -> Dict:
        """Obtener resumen sin enviar (para testing)"""
        return self._generate_summary()
