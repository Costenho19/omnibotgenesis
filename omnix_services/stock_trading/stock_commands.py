"""
📊 Stock Trading Telegram Commands Handler V6.2 PREMIUM
All commands for stock market trading with institutional features
"""

import logging
import os
from typing import Optional
from .alpaca_service import AlpacaService
from .market_hours import MarketHoursManager
from .stock_analyzer import StockAnalyzer
from .fundamental_analyzer import FundamentalAnalyzer

logger = logging.getLogger(__name__)

STOCK_TRADING_ENABLED = os.getenv('STOCK_TRADING_ENABLED', 'false').lower() == 'true'


class StockCommandsHandler:
    """
    Handles all stock-related Telegram commands V6.2 PREMIUM
    Includes institutional-grade analysis with:
    - Monte Carlo Simulations
    - Kalman Filter
    - HMM Regime Detection
    - ARES-STOCK strategies
    - Non-Markovian Memory
    - Coherence Engine
    - Risk Guardian
    """
    
    def __init__(self):
        if not STOCK_TRADING_ENABLED:
            logger.info("📊 Stock Trading Module: DORMIDO (use STOCK_TRADING_ENABLED=true para activar)")
            self.enabled = False
            return
        
        logger.info("📊 Inicializando Stock Trading Module V6.2 PREMIUM...")
        
        self.alpaca = AlpacaService(paper_trading=True)
        self.market_hours = MarketHoursManager()
        self.stock_analyzer = StockAnalyzer()
        self.fundamental_analyzer = FundamentalAnalyzer()
        
        self.premium_engine = None
        self.coherence_adapter = None
        self.risk_bridge = None
        self.auto_optimizer = None
        self._init_premium_features()
        
        self.enabled = STOCK_TRADING_ENABLED and self.alpaca.connected
        
        if self.enabled:
            logger.info("✅ Stock Trading Module V6.2 PREMIUM ACTIVADO")
            logger.info(f"   🏦 Alpaca: {'✅' if self.alpaca.connected else '❌'}")
            logger.info(f"   🚀 Premium Engine: {'✅' if self.premium_engine else '❌'}")
            logger.info(f"   🔗 Coherence: {'✅' if self.coherence_adapter else '❌'}")
            logger.info(f"   🛡️ Risk Guardian: {'✅' if self.risk_bridge else '❌'}")
        else:
            logger.warning("⚠️ Stock Trading Module configurado pero Alpaca no conectado")
    
    def _init_premium_features(self):
        """Initialize premium trading features"""
        try:
            from .premium import StockStrategyEngine
            self.premium_engine = StockStrategyEngine(
                stock_analyzer=self.stock_analyzer,
                fundamental_analyzer=self.fundamental_analyzer,
                market_hours=self.market_hours
            )
            logger.info("   ✅ Stock Strategy Engine Premium inicializado")
        except Exception as e:
            logger.warning(f"   ⚠️ Premium Engine no disponible: {e}")
        
        try:
            from .premium.integration import StockCoherenceAdapter
            self.coherence_adapter = StockCoherenceAdapter()
            logger.info("   ✅ Coherence Adapter inicializado")
        except Exception as e:
            logger.warning(f"   ⚠️ Coherence Adapter no disponible: {e}")
        
        try:
            from .premium.integration import StockRiskGuardianBridge
            self.risk_bridge = StockRiskGuardianBridge()
            logger.info("   ✅ Risk Guardian Bridge inicializado")
        except Exception as e:
            logger.warning(f"   ⚠️ Risk Guardian Bridge no disponible: {e}")
        
        try:
            from .premium.stock_auto_optimizer import StockAutoOptimizer
            self.auto_optimizer = StockAutoOptimizer()
            logger.info("   ✅ Auto-Optimizer inicializado")
        except Exception as e:
            logger.warning(f"   ⚠️ Auto-Optimizer no disponible: {e}")
    
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
    
    async def handle_premium_analysis(self, update, context, symbol: str) -> str:
        """Handle /analizar_premium [SYMBOL] - Análisis institucional completo"""
        if not STOCK_TRADING_ENABLED:
            return "📊 Módulo de bolsa no activado"
        
        if not symbol:
            return "⚠️ Uso: /analizar_premium AAPL"
        
        symbol = symbol.upper().strip()
        
        if not self.premium_engine:
            return await self.handle_analyze_stock(update, context, symbol)
        
        try:
            response = f"🚀 **ANÁLISIS PREMIUM: {symbol}**\n"
            response += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            signal = self.premium_engine.analyze(symbol, include_fundamental=True)
            
            if not signal:
                response += "❌ No se pudo completar análisis premium\n"
                response += "Intentando análisis básico...\n\n"
                return await self.handle_analyze_stock(update, context, symbol)
            
            signal_emojis = {
                'strong_buy': '🟢🟢',
                'buy': '🟢',
                'hold': '🟡',
                'sell': '🔴',
                'strong_sell': '🔴🔴'
            }
            
            regime_emojis = {
                'bull': '📈 Bull',
                'bear': '📉 Bear',
                'sideways': '➡️ Lateral',
                'crisis': '🚨 Crisis',
                'unknown': '❓ Desconocido'
            }
            
            signal_emoji = signal_emojis.get(signal.signal_type.value, '❓')
            regime_text = regime_emojis.get(signal.regime.value, '❓')
            
            response += f"{signal_emoji} **Señal: {signal.signal_type.value.upper()}**\n"
            response += f"💯 Confianza: {signal.confidence:.0%}\n"
            response += f"🎯 Régimen: {regime_text}\n\n"
            
            response += "**📊 Scores:**\n"
            response += f"   🔧 Técnico: {signal.technical_score:.2f}\n"
            response += f"   📈 Fundamental: {signal.fundamental_score:.2f}\n"
            response += f"   🧠 Coherencia: {signal.memory_coherence:.2f}\n\n"
            
            if signal.sources:
                response += "**🎲 Señales por Estrategia:**\n"
                for source, value in signal.sources.items():
                    emoji = "🟢" if value > 0.2 else "🔴" if value < -0.2 else "🟡"
                    response += f"   {emoji} {source}: {value:+.2f}\n"
                response += "\n"
            
            if signal.protection_warnings:
                response += "**🛡️ Protecciones Activas:**\n"
                for warning in signal.protection_warnings[:3]:
                    response += f"   • {warning}\n"
                if signal.position_multiplier < 1.0:
                    response += f"   📊 Sizing ajustado: {signal.position_multiplier:.0%}\n"
                response += "\n"
            
            if signal.risk_approved:
                response += "✅ **Aprobado por Risk Guardian**\n"
            else:
                response += "⚠️ **Vetos activos:**\n"
                for reason in signal.veto_reasons[:3]:
                    response += f"   • {reason}\n"
            
            response += f"\n🛡️ Gap Protection: {'✅' if signal.gap_protected else '❌'}"
            response += f" | Earnings Protection: {'✅' if signal.earnings_protected else '❌'}"
            response += f"\n🕐 {signal.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            
            return response
            
        except Exception as e:
            logger.error(f"Error in premium analysis {symbol}: {e}")
            return f"❌ Error en análisis premium: {str(e)}"
    
    async def handle_stock_status(self, update, context) -> str:
        """Handle /stock_status - Estado del sistema premium"""
        if not STOCK_TRADING_ENABLED:
            return "📊 Módulo de bolsa no activado"
        
        response = "🚀 **STOCK TRADING V6.3 ULTRA**\n"
        response += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        response += f"🏦 Alpaca: {'✅ Conectado' if self.alpaca.connected else '❌ Desconectado'}\n"
        response += f"⏰ Mercado: {self.market_hours.get_market_status()['status_text']}\n\n"
        
        response += "**Módulos Premium:**\n"
        response += f"   🚀 Strategy Engine: {'✅' if self.premium_engine else '❌'}\n"
        response += f"   🔗 Coherence Adapter: {'✅' if self.coherence_adapter else '❌'}\n"
        response += f"   🛡️ Risk Guardian: {'✅' if self.risk_bridge else '❌'}\n"
        response += f"   🔧 Auto-Optimizer: {'✅' if self.auto_optimizer else '❌'}\n\n"
        
        if self.premium_engine:
            status = self.premium_engine.get_status()
            modules = status.get('modules', {})
            active = sum(1 for v in modules.values() if v)
            total = len(modules)
            response += f"**Engine Status ({active}/{total}):**\n"
            response += f"   🎯 Monte Carlo: {'✅' if modules.get('monte_carlo') else '❌'}\n"
            response += f"   📈 Kalman Filter: {'✅' if modules.get('kalman_filter') else '❌'}\n"
            response += f"   🎲 HMM Regime: {'✅' if modules.get('hmm_detector') else '❌'}\n"
            response += f"   🧬 ARES-STOCK: {'✅' if modules.get('ares_stock') else '❌'}\n"
            response += f"   🧠 Memory Kernel: {'✅' if modules.get('memory_kernel') else '❌'}\n\n"
            
            response += "**Protección Institucional:**\n"
            response += f"   🛡️ Gap Protection: {'✅' if modules.get('gap_protection') else '❌'}\n"
            response += f"   📅 Earnings Protector: {'✅' if modules.get('earnings_protector') else '❌'}\n"
        
        return response
    
    async def handle_risk_dashboard(self, update, context) -> str:
        """Handle /risk_dashboard - Dashboard de riesgo institucional"""
        if not STOCK_TRADING_ENABLED:
            return "📊 Módulo de bolsa no activado"
        
        response = "🛡️ **RISK DASHBOARD INSTITUCIONAL**\n"
        response += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if not self.premium_engine:
            response += "❌ Motor premium no inicializado\n"
            return response
        
        try:
            dashboard = self.premium_engine.get_risk_dashboard()
            
            mode_emojis = {
                'NORMAL': '✅',
                'AWARE': '🟡',
                'CAUTIOUS': '🟠',
                'DEFENSIVE': '🔴'
            }
            
            mode = dashboard.get('market_mode', 'NORMAL')
            mode_emoji = mode_emojis.get(mode, '❓')
            
            response += f"**Estado del Mercado:**\n"
            response += f"   {mode_emoji} Modo: **{mode}**\n"
            response += f"   📊 Sizing multiplier: {dashboard.get('sizing_multiplier', 1.0):.0%}\n\n"
            
            protection = dashboard.get('protection_status', {})
            response += f"**Protecciones Activas:**\n"
            response += f"   🛡️ Gap Protection: {protection.get('gap_protection', 'INACTIVE')}\n"
            response += f"   📅 Earnings Protection: {protection.get('earnings_protection', 'INACTIVE')}\n"
            response += f"   🔗 Coherence Engine: {protection.get('coherence_engine', 'INACTIVE')}\n"
            response += f"   🛡️ Risk Guardian: {protection.get('risk_guardian', 'INACTIVE')}\n\n"
            
            trading_window = dashboard.get('trading_window', {})
            if trading_window:
                can_trade = "✅ SÍ" if trading_window.get('can_trade') else "🔴 NO"
                response += f"**Ventana de Trading:**\n"
                response += f"   🕐 Hora ET: {trading_window.get('current_time_et', 'N/A')}\n"
                response += f"   📊 Puede operar: {can_trade}\n"
                if trading_window.get('time_to_close'):
                    response += f"   ⏰ Tiempo al cierre: {trading_window.get('time_to_close')}\n"
                response += "\n"
            
            blocked = dashboard.get('blocked_symbols', [])
            if blocked:
                response += f"**🚫 Símbolos Bloqueados ({len(blocked)}):**\n"
                response += f"   {', '.join(blocked[:10])}\n\n"
            
            high_risk = dashboard.get('high_risk_earnings', [])
            if high_risk:
                response += f"**⚠️ Earnings próximos (alto riesgo):**\n"
                response += f"   {', '.join(high_risk[:10])}\n\n"
            
            response += f"🔧 Sistema: {dashboard.get('system_health', 'N/A')}\n"
            
            return response
            
        except Exception as e:
            logger.error(f"Error in risk dashboard: {e}")
            return f"❌ Error obteniendo dashboard: {str(e)}"
    
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
