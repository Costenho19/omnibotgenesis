"""
📊 Stock Trading Telegram Commands Handler
All commands for stock market trading
"""

import logging
import os
from typing import Optional
from .alpaca_service import AlpacaService
from .market_hours import MarketHoursManager
from .stock_analyzer import StockAnalyzer
from .fundamental_analyzer import FundamentalAnalyzer

logger = logging.getLogger(__name__)

# Feature flag check
STOCK_TRADING_ENABLED = os.getenv('STOCK_TRADING_ENABLED', 'false').lower() == 'true'


class StockCommandsHandler:
    """
    Handles all stock-related Telegram commands
    Only active if STOCK_TRADING_ENABLED=true
    """
    
    def __init__(self):
        if not STOCK_TRADING_ENABLED:
            logger.info("📊 Stock Trading Module: DORMIDO (use STOCK_TRADING_ENABLED=true para activar)")
            self.enabled = False
            return
        
        logger.info("📊 Inicializando Stock Trading Module...")
        
        # Initialize services
        self.alpaca = AlpacaService(paper_trading=True)
        self.market_hours = MarketHoursManager()
        self.stock_analyzer = StockAnalyzer()
        self.fundamental_analyzer = FundamentalAnalyzer()
        
        self.enabled = STOCK_TRADING_ENABLED and self.alpaca.connected
        
        if self.enabled:
            logger.info("✅ Stock Trading Module ACTIVADO - Alpaca conectado")
        else:
            logger.warning("⚠️ Stock Trading Module configurado pero Alpaca no conectado")
    
    async def handle_balance_stocks(self, update, context) -> str:
        """Handle /balance_bolsa command"""
        if not STOCK_TRADING_ENABLED:
            return "📊 El módulo de bolsa no está activado.\n\nContacta al administrador para activarlo."
        
        if not self.alpaca.connected:
            return "❌ No conectado a Alpaca. Verifica las credenciales API."
        
        try:
            balance = self.alpaca.fetch_balance()
            positions = self.alpaca.fetch_positions()
            
            if not balance:
                return "❌ Error obteniendo balance"
            
            response = "📊 **BALANCE BOLSA DE VALORES**\n\n"
            response += f"💵 Efectivo disponible: ${balance['cash']:,.2f}\n"
            response += f"⚡ Poder de compra: ${balance['buying_power']:,.2f}\n"
            response += f"💼 Valor del portafolio: ${balance['portfolio_value']:,.2f}\n"
            response += f"📈 Capital total: ${balance['equity']:,.2f}\n\n"
            
            if positions:
                response += "**POSICIONES ACTIVAS:**\n\n"
                total_pl = 0
                
                for pos in positions:
                    pl_pct = pos['unrealized_plpc'] * 100
                    emoji = "🟢" if pl_pct > 0 else "🔴" if pl_pct < 0 else "⚪"
                    
                    response += f"{emoji} **{pos['symbol']}**\n"
                    response += f"   Cantidad: {pos['qty']:.2f} acciones\n"
                    response += f"   Precio entrada: ${pos['avg_entry_price']:.2f}\n"
                    response += f"   Precio actual: ${pos['current_price']:.2f}\n"
                    response += f"   Valor: ${pos['market_value']:,.2f}\n"
                    response += f"   P&L: ${pos['unrealized_pl']:,.2f} ({pl_pct:+.2f}%)\n\n"
                    
                    total_pl += pos['unrealized_pl']
                
                pl_emoji = "🟢" if total_pl > 0 else "🔴" if total_pl < 0 else "⚪"
                response += f"{pl_emoji} **Total P&L: ${total_pl:+,.2f}**\n"
            else:
                response += "📭 No hay posiciones abiertas\n"
            
            return response
        
        except Exception as e:
            logger.error(f"Error en balance_stocks: {e}")
            return f"❌ Error: {str(e)}"
    
    async def handle_market_status(self, update, context) -> str:
        """Handle /mercado command"""
        if not STOCK_TRADING_ENABLED:
            return "📊 Módulo de bolsa no activado"
        
        try:
            status = self.market_hours.get_market_status()
            
            response = "🏦 **ESTADO DEL MERCADO**\n\n"
            response += f"{status['status_text']}\n\n"
            
            if status['is_open']:
                response += "✅ Puedes ejecutar órdenes ahora\n"
            elif status['is_extended_hours']:
                response += "🟡 Horario extendido (pre-market/after-hours)\n"
                response += "⚠️ Liquidez limitada\n"
            else:
                response += "🔴 Mercado cerrado\n"
                response += "⏰ Espera hasta la apertura\n"
            
            return response
        
        except Exception as e:
            logger.error(f"Error en market_status: {e}")
            return f"❌ Error: {str(e)}"
    
    async def handle_analyze_stock(self, update, context, symbol: str) -> str:
        """Handle /analizar [SYMBOL] command"""
        if not STOCK_TRADING_ENABLED:
            return "📊 Módulo de bolsa no activado"
        
        if not symbol:
            return "⚠️ Uso: /analizar AAPL"
        
        symbol = symbol.upper().strip()
        
        try:
            response = f"📊 **ANÁLISIS DE {symbol}**\n\n"
            
            # Technical analysis
            response += "🔍 **Análisis Técnico:**\n"
            tech_analysis = self.stock_analyzer.analyze_stock(symbol)
            
            if tech_analysis:
                signal_emoji = "🟢" if tech_analysis['signal'] == 'BUY' else "🔴" if tech_analysis['signal'] == 'SELL' else "🟡"
                
                response += f"{signal_emoji} Señal: **{tech_analysis['signal']}**\n"
                response += f"💯 Confianza: {tech_analysis['confidence']:.1f}%\n"
                response += f"💵 Precio actual: ${tech_analysis['current_price']:.2f}\n\n"
                response += f"📊 RSI: {tech_analysis['rsi']:.2f}\n"
                response += f"📈 MACD: {tech_analysis['macd']['macd']:.4f}\n"
                response += f"📉 EMA(9): ${tech_analysis['ema_9']:.2f}\n"
                response += f"📉 EMA(21): ${tech_analysis['ema_21']:.2f}\n"
                response += f"📉 EMA(50): ${tech_analysis['ema_50']:.2f}\n\n"
            else:
                response += "❌ No se pudo obtener análisis técnico\n\n"
            
            # Fundamental analysis
            response += "📈 **Análisis Fundamental:**\n"
            fund_analysis = self.fundamental_analyzer.analyze_fundamentals(symbol)
            
            if fund_analysis:
                response += f"{fund_analysis['emoji']} Score: {fund_analysis['score']:.1f}/100\n"
                response += f"🎯 Recomendación: **{fund_analysis['recommendation']}**\n\n"
                response += f"🏢 {fund_analysis['name']}\n"
                response += f"🏭 Sector: {fund_analysis['sector']}\n\n"
                
                response += "**Métricas clave:**\n"
                for reason in fund_analysis['reasons']:
                    response += f"{reason}\n"
            else:
                response += "❌ No se pudo obtener análisis fundamental\n"
            
            # Market status
            response += f"\n{self.market_hours.get_market_status()['status_text']}"
            
            return response
        
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return f"❌ Error analizando {symbol}: {str(e)}"
    
    async def handle_buy_stock(self, update, context, symbol: str, amount: Optional[float] = None) -> str:
        """Handle /comprar_bolsa [SYMBOL] [AMOUNT] command"""
        if not STOCK_TRADING_ENABLED:
            return "📊 Módulo de bolsa no activado"
        
        if not self.alpaca.connected:
            return "❌ No conectado a Alpaca"
        
        if not symbol:
            return "⚠️ Uso: /comprar_bolsa AAPL 1000  (compra $1000 de AAPL)"
        
        symbol = symbol.upper().strip()
        amount = amount or 100.0  # Default $100
        
        try:
            # Check market status
            if not self.market_hours.is_market_open():
                return f"🔴 Mercado cerrado\n{self.market_hours.get_market_status()['status_text']}"
            
            # Get current price
            price = self.alpaca.fetch_ticker_price(symbol)
            if not price:
                return f"❌ No se pudo obtener precio de {symbol}"
            
            # Create order (fractional shares with notional amount)
            order = self.alpaca.create_order(
                symbol=symbol,
                notional=amount,
                side='buy',
                order_type='market',
                time_in_force='day'
            )
            
            if order:
                response = f"✅ **ORDEN EJECUTADA**\n\n"
                response += f"🎯 Acción: {symbol}\n"
                response += f"💵 Monto: ${amount:.2f}\n"
                response += f"📊 Precio: ~${price:.2f}\n"
                response += f"📋 ID: {order['id'][:8]}...\n"
                response += f"✔️ Estado: {order['status']}\n\n"
                response += "⚠️ Modo Paper Trading (simulado)"
                return response
            else:
                return f"❌ Error ejecutando orden de compra"
        
        except Exception as e:
            logger.error(f"Error buying {symbol}: {e}")
            return f"❌ Error: {str(e)}"
    
    async def handle_sell_stock(self, update, context, symbol: str) -> str:
        """Handle /vender_bolsa [SYMBOL] command"""
        if not STOCK_TRADING_ENABLED:
            return "📊 Módulo de bolsa no activado"
        
        if not self.alpaca.connected:
            return "❌ No conectado a Alpaca"
        
        if not symbol:
            return "⚠️ Uso: /vender_bolsa AAPL"
        
        symbol = symbol.upper().strip()
        
        try:
            # Check market status
            if not self.market_hours.is_market_open():
                return f"🔴 Mercado cerrado\n{self.market_hours.get_market_status()['status_text']}"
            
            # Close position
            success = self.alpaca.close_position(symbol)
            
            if success:
                return f"✅ Posición en {symbol} cerrada exitosamente"
            else:
                return f"❌ Error cerrando posición en {symbol}\n(¿Tienes acciones de {symbol}?)"
        
        except Exception as e:
            logger.error(f"Error selling {symbol}: {e}")
            return f"❌ Error: {str(e)}"


# Global instance (only created if enabled)
stock_handler = StockCommandsHandler() if STOCK_TRADING_ENABLED else None
