"""
Telegram Commands for Derivatives Module - OMNIX Premium
=========================================================

Comandos de Telegram para el módulo de derivados:
- /derivatives - Estado del módulo y posiciones
- /deriv_open - Abrir posición en perpetuos
- /deriv_close - Cerrar posición
- /hedge_now - Crear hedge para posición spot
- /funding_status - Ver oportunidades de funding
- /deriv_stats - Estadísticas de trading

Integración con EnterpriseTelegramBot.
"""

import logging
from typing import Optional
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from .derivatives_manager import DerivativesManager, DerivativesConfig, TradingMode
from .hedging_service import HedgingService
from .funding_arbitrage import FundingArbitrageAnalyzer

logger = logging.getLogger(__name__)


class DerivativesTelegramCommands:
    """
    Comandos de Telegram para Derivados OMNIX
    
    Proporciona interfaz de usuario para:
    - Ver estado y posiciones
    - Abrir/cerrar trades
    - Gestionar hedges
    - Monitorear funding rates
    """
    
    def __init__(self, derivatives_manager: Optional[DerivativesManager] = None):
        """
        Inicializar comandos
        
        Args:
            derivatives_manager: DerivativesManager configurado
        """
        if derivatives_manager:
            self.manager = derivatives_manager
        else:
            config = DerivativesConfig(
                trading_mode=TradingMode.PAPER,
                initial_capital=100_000.0,
                max_leverage=3.0
            )
            self.manager = DerivativesManager(config)
        
        self.hedging = HedgingService(derivatives_manager=self.manager)
        self.funding = FundingArbitrageAnalyzer(
            futures_client=self.manager.futures_client,
            derivatives_manager=self.manager
        )
        
        logger.info("📱 DerivativesTelegramCommands inicializado")
    
    async def derivatives_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /derivatives - Estado del módulo de derivados
        """
        try:
            status = self.manager.get_status()
            summary = self.manager.get_portfolio_summary()
            positions = self.manager.get_positions()
            
            mode_emoji = "📊" if status["mode"] == "PAPER" else "🔴"
            halt_status = "🛑 DETENIDO" if status["is_halted"] else "✅ ACTIVO"
            
            msg = f"""
{mode_emoji} **OMNIX DERIVATIVES** {mode_emoji}

**Estado:** {halt_status}
**Modo:** {status['mode']} TRADING
**Leverage máximo:** {status['config']['max_leverage']}x

💰 **Portfolio:**
• Balance: ${summary['portfolio'].get('balance', 0):,.2f}
• PnL total: ${summary['portfolio'].get('total_pnl', 0):+,.2f}
• Win rate: {summary['portfolio'].get('win_rate', 0):.1%}

📊 **Margin:**
• Disponible: ${summary['margin']['available']:,.2f}
• Usado: ${summary['margin']['used']:,.2f}
• Nivel: {summary['margin']['level'].upper()}
• Leverage actual: {summary['margin']['leverage']:.2f}x

📈 **Posiciones abiertas:** {len(positions)}
"""
            
            if positions:
                msg += "\n**Posiciones:**\n"
                for pos in positions[:5]:
                    side_emoji = "🟢" if pos["side"] == "long" else "🔴"
                    pnl = pos.get("unrealized_pnl", 0)
                    pnl_str = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
                    msg += f"{side_emoji} {pos['symbol']} {pos['side'].upper()} {pos['size']:.4f} | PnL: {pnl_str}\n"
            
            msg += f"\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            keyboard = [
                [
                    InlineKeyboardButton("📊 Abrir Long", callback_data="deriv_open_long"),
                    InlineKeyboardButton("📉 Abrir Short", callback_data="deriv_open_short")
                ],
                [
                    InlineKeyboardButton("🛡️ Hedge Now", callback_data="hedge_now"),
                    InlineKeyboardButton("💰 Funding", callback_data="funding_status")
                ],
                [
                    InlineKeyboardButton("📈 Stats", callback_data="deriv_stats"),
                    InlineKeyboardButton("🔄 Refresh", callback_data="deriv_refresh")
                ]
            ]
            
            await update.message.reply_text(
                msg,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            logger.error(f"Error en /derivatives: {e}")
            await update.message.reply_text(f"❌ Error obteniendo estado: {str(e)}")
    
    async def open_position(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /deriv_open <symbol> <side> <size> [leverage]
        Ejemplo: /deriv_open BTC long 0.1 2
        """
        try:
            args = context.args
            
            if len(args) < 3:
                await update.message.reply_text(
                    "📋 **Uso:** /deriv_open <symbol> <side> <size> [leverage]\n\n"
                    "**Ejemplos:**\n"
                    "• `/deriv_open BTC long 0.1` - Long 0.1 BTC (1x)\n"
                    "• `/deriv_open ETH short 1.0 2` - Short 1 ETH (2x)\n\n"
                    "**Símbolos:** BTC, ETH, SOL, XRP\n"
                    "**Sides:** long, short\n"
                    "**Leverage máximo:** 3x",
                    parse_mode="Markdown"
                )
                return
            
            symbol = args[0].upper()
            side = args[1].lower()
            size = float(args[2])
            leverage = float(args[3]) if len(args) > 3 else 1.0
            
            if side not in ["long", "short"]:
                await update.message.reply_text("❌ Side debe ser 'long' o 'short'")
                return
            
            if symbol not in ["BTC", "ETH", "SOL", "XRP"]:
                await update.message.reply_text("❌ Símbolo no soportado. Usa: BTC, ETH, SOL, XRP")
                return
            
            if leverage > 3.0:
                await update.message.reply_text("⚠️ Leverage máximo es 3x. Usando 3x.")
                leverage = 3.0
            
            result = self.manager.open_position(
                symbol=symbol,
                side=side,
                size=size,
                leverage=leverage
            )
            
            if result["success"]:
                side_emoji = "🟢" if side == "long" else "🔴"
                msg = f"""
{side_emoji} **POSICIÓN ABIERTA**

**Símbolo:** {symbol}
**Side:** {side.upper()}
**Tamaño:** {size}
**Leverage:** {leverage}x
**Precio entrada:** ${result.get('entry_price', 0):,.2f}
**Margen usado:** ${result.get('margin_used', 0):,.2f}
**Modo:** {result.get('mode', 'PAPER')}

📋 Trade ID: `{result.get('trade_id', 'N/A')}`
"""
                await update.message.reply_text(msg, parse_mode="Markdown")
            else:
                await update.message.reply_text(f"❌ Error: {result.get('error', 'Unknown error')}")
                
        except ValueError as e:
            await update.message.reply_text(f"❌ Error en parámetros: {str(e)}")
        except Exception as e:
            logger.error(f"Error en /deriv_open: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def close_position(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /deriv_close <symbol>
        Ejemplo: /deriv_close BTC
        """
        try:
            args = context.args
            
            if not args:
                positions = self.manager.get_positions()
                if not positions:
                    await update.message.reply_text("📭 No hay posiciones abiertas para cerrar")
                    return
                
                msg = "📋 **Posiciones abiertas:**\n\n"
                for pos in positions:
                    side_emoji = "🟢" if pos["side"] == "long" else "🔴"
                    pnl = pos.get("unrealized_pnl", 0)
                    pnl_str = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
                    msg += f"{side_emoji} {pos['symbol']}: {pos['side'].upper()} {pos['size']:.4f} | PnL: {pnl_str}\n"
                
                msg += "\n**Uso:** `/deriv_close <symbol>`"
                await update.message.reply_text(msg, parse_mode="Markdown")
                return
            
            symbol = args[0].upper()
            
            result = self.manager.close_position(symbol=symbol, reason="manual_telegram")
            
            if result["success"]:
                pnl = result.get("pnl", 0)
                pnl_emoji = "✅" if pnl >= 0 else "❌"
                pnl_str = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
                
                msg = f"""
{pnl_emoji} **POSICIÓN CERRADA**

**Símbolo:** {symbol}
**PnL:** {pnl_str}
**PnL %:** {result.get('pnl_pct', 0):+.2%}
**Precio salida:** ${result.get('exit_price', 0):,.2f}

📋 Trade ID: `{result.get('trade_id', 'N/A')}`
"""
                await update.message.reply_text(msg, parse_mode="Markdown")
            else:
                await update.message.reply_text(f"❌ Error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error en /deriv_close: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def hedge_now(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /hedge_now <symbol> <spot_size> [coverage]
        Ejemplo: /hedge_now BTC 1.0 0.8
        """
        try:
            args = context.args
            
            if len(args) < 2:
                await update.message.reply_text(
                    "🛡️ **Hedging de Posiciones Spot**\n\n"
                    "**Uso:** `/hedge_now <symbol> <spot_size> [coverage]`\n\n"
                    "**Ejemplos:**\n"
                    "• `/hedge_now BTC 1.0` - Hedge 80% de 1 BTC\n"
                    "• `/hedge_now ETH 5.0 0.5` - Hedge 50% de 5 ETH\n\n"
                    "**Coverage:** 0.5 a 1.0 (default: 0.8)",
                    parse_mode="Markdown"
                )
                return
            
            symbol = args[0].upper()
            spot_size = float(args[1])
            coverage = float(args[2]) if len(args) > 2 else 0.8
            
            market = self.manager.get_market_data(symbol)
            if not market:
                await update.message.reply_text(f"❌ No se pudo obtener precio para {symbol}")
                return
            
            spot_price = market["mark_price"]
            
            hedge = self.hedging.create_hedge(
                spot_symbol=symbol,
                spot_size=spot_size,
                spot_price=spot_price,
                coverage_ratio=coverage
            )
            
            if hedge:
                msg = f"""
🛡️ **HEDGE CREADO**

**Spot:** {spot_size} {symbol} @ ${spot_price:,.2f}
**Valor protegido:** ${hedge.spot_value:,.2f}

**Hedge:** {hedge.hedge_size:.4f} SHORT {hedge.hedge_symbol}
**Cobertura:** {hedge.coverage_ratio:.0%}
**Precio liquidación:** ${hedge.liquidation_price if hasattr(hedge, 'liquidation_price') else 'N/A'}

📋 Hedge ID: `{hedge.hedge_id}`
"""
                await update.message.reply_text(msg, parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ No se pudo crear el hedge")
                
        except ValueError as e:
            await update.message.reply_text(f"❌ Error en parámetros: {str(e)}")
        except Exception as e:
            logger.error(f"Error en /hedge_now: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def funding_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /funding_status - Ver oportunidades de funding arbitrage
        """
        try:
            opportunities = self.funding.scan_opportunities()
            active_positions = self.funding.get_active_positions()
            stats = self.funding.get_stats()
            
            msg = """
💰 **FUNDING RATE ARBITRAGE**

"""
            
            if opportunities:
                msg += "**🔍 Oportunidades detectadas:**\n"
                for opp in opportunities[:5]:
                    risk_emoji = "🟢" if opp.risk_score < 30 else ("🟡" if opp.risk_score < 60 else "🔴")
                    msg += f"{risk_emoji} **{opp.symbol}**: {opp.funding_rate:.4%} (anual: {opp.expected_return_annual:.1%})\n"
            else:
                msg += "📭 No hay oportunidades rentables ahora\n"
            
            msg += f"\n**📊 Estadísticas:**\n"
            msg += f"• Oportunidades detectadas: {stats['opportunities_detected']}\n"
            msg += f"• Ejecutadas: {stats['opportunities_executed']}\n"
            msg += f"• Posiciones activas: {stats['current_positions']}\n"
            msg += f"• Funding ganado: ${stats['total_funding_earned']:,.2f}\n"
            msg += f"• PnL total: ${stats['total_pnl']:+,.2f}\n"
            
            if active_positions:
                msg += "\n**📈 Posiciones activas:**\n"
                for pos in active_positions[:3]:
                    msg += f"• {pos['symbol']}: ${pos['total_funding']:+,.2f} ({pos['payments']} pagos)\n"
            
            await update.message.reply_text(msg, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error en /funding_status: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def derivatives_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /deriv_stats - Estadísticas detalladas de derivados
        """
        try:
            summary = self.manager.get_portfolio_summary()
            portfolio = summary.get("portfolio", {})
            margin = summary.get("margin", {})
            
            total_trades = portfolio.get("total_trades", 0)
            winning = portfolio.get("winning_trades", 0)
            losing = portfolio.get("losing_trades", 0)
            win_rate = winning / total_trades if total_trades > 0 else 0
            
            msg = f"""
📊 **ESTADÍSTICAS DERIVADOS**

💰 **Rendimiento:**
• Balance inicial: $100,000.00
• Balance actual: ${portfolio.get('balance', 100000):,.2f}
• PnL total: ${portfolio.get('total_pnl', 0):+,.2f}
• Retorno: {portfolio.get('total_pnl_pct', 0):.2%}
• Max drawdown: {portfolio.get('max_drawdown', 0):.2%}

📈 **Trading:**
• Total trades: {total_trades}
• Ganadores: {winning} ({win_rate:.1%})
• Perdedores: {losing}
• Mejor trade: ${portfolio.get('largest_win', 0):,.2f}
• Peor trade: ${abs(portfolio.get('largest_loss', 0)):,.2f}

💰 **Costos:**
• Fees totales: ${portfolio.get('total_fees', 0):,.2f}
• Funding pagado: ${portfolio.get('total_funding', 0):,.2f}

📊 **Margin:**
• Equity: ${margin.get('equity', 0):,.2f}
• Disponible: ${margin.get('available', 0):,.2f}
• Leverage actual: {margin.get('leverage', 0):.2f}x

⚠️ *Paper trading - No dinero real*
"""
            
            await update.message.reply_text(msg, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error en /deriv_stats: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar callbacks de botones inline"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "deriv_refresh":
            self.manager.update_prices()
            await self.derivatives_status(update, context)
            
        elif data == "deriv_stats":
            await self.derivatives_stats(update, context)
            
        elif data == "funding_status":
            await self.funding_status(update, context)
            
        elif data == "hedge_now":
            await query.message.reply_text(
                "🛡️ Usa: `/hedge_now <symbol> <spot_size> [coverage]`",
                parse_mode="Markdown"
            )
            
        elif data == "deriv_open_long":
            await query.message.reply_text(
                "📈 Para abrir LONG:\n`/deriv_open <symbol> long <size> [leverage]`",
                parse_mode="Markdown"
            )
            
        elif data == "deriv_open_short":
            await query.message.reply_text(
                "📉 Para abrir SHORT:\n`/deriv_open <symbol> short <size> [leverage]`",
                parse_mode="Markdown"
            )


def register_derivatives_commands(application, derivatives_manager: Optional[DerivativesManager] = None):
    """
    Registrar comandos de derivados en la aplicación Telegram
    
    Args:
        application: Application de python-telegram-bot
        derivatives_manager: DerivativesManager opcional
    """
    from telegram.ext import CommandHandler, CallbackQueryHandler
    
    commands = DerivativesTelegramCommands(derivatives_manager)
    
    application.add_handler(CommandHandler("derivatives", commands.derivatives_status))
    application.add_handler(CommandHandler("deriv_open", commands.open_position))
    application.add_handler(CommandHandler("deriv_close", commands.close_position))
    application.add_handler(CommandHandler("hedge_now", commands.hedge_now))
    application.add_handler(CommandHandler("funding_status", commands.funding_status))
    application.add_handler(CommandHandler("deriv_stats", commands.derivatives_stats))
    
    application.add_handler(CallbackQueryHandler(
        commands.handle_callback, 
        pattern="^deriv_|^hedge_|^funding_"
    ))
    
    logger.info("📱 Derivatives commands registrados: /derivatives, /deriv_open, /deriv_close, /hedge_now, /funding_status, /deriv_stats")
    
    return commands
