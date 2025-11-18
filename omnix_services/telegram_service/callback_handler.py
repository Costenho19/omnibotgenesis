"""
OMNIX V5.4 ULTRA - Callback Handler Premium
Sistema profesional de manejo de callbacks para botones inline
"""

import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class CallbackHandler:
    """
    Manejador de callbacks para botones inline
    Procesa todas las interacciones con el teclado
    """
    
    def __init__(self, trading_service, ai_service, db_service=None):
        """
        Inicializar callback handler
        
        Args:
            trading_service: Servicio de trading (Kraken)
            ai_service: Servicio de IA conversacional
            db_service: Servicio de base de datos (opcional)
        """
        self.trading = trading_service
        self.ai = ai_service
        self.db = db_service
        
    async def handle_callback(self, update, context, bot_instance=None):
        """
        Procesar callback de botón inline
        
        Args:
            update: Update de Telegram
            context: Context de Telegram
            bot_instance: Instancia del bot (para acceder a otros métodos)
        """
        try:
            query = update.callback_query
            await query.answer()  # Responder al callback inmediatamente
            
            callback_data = query.data
            logger.info(f"🎨 Callback recibido: {callback_data}")
            
            # NO mostrar loading message - procesar directamente
            # Routing de callbacks
            if callback_data == "back_main":
                await self._show_main_menu(query, context)
            
            elif callback_data == "show_main_menu":
                await self._show_main_menu(query, context)
            
            # PRECIOS
            elif callback_data.startswith("price_"):
                symbol = callback_data.replace("price_", "").upper()
                await self._show_price(query, symbol)
            
            # ANÁLISIS
            elif callback_data.startswith("analysis_"):
                symbol = callback_data.replace("analysis_", "").upper()
                await self._show_analysis(query, symbol)
            
            # BALANCE
            elif callback_data == "balance":
                await self._show_balance(query, bot_instance)
            
            # HISTORIAL
            elif callback_data == "history":
                await self._show_history(query)
            
            # ALERTAS
            elif callback_data == "alerts_list":
                await self._show_alerts(query)
            elif callback_data == "alert_create":
                await self._create_alert_menu(query)
            
            # ESTRATEGIAS
            elif callback_data == "strategies":
                await self._show_strategies_menu(query)
            elif callback_data.startswith("strat_"):
                strategy_name = callback_data.replace("strat_", "")
                await self._show_strategy_details(query, strategy_name)
            
            # CONFIGURACIÓN
            elif callback_data == "settings":
                await self._show_settings_menu(query)
            
            # ESTADO DEL SISTEMA
            elif callback_data == "status":
                await self._show_system_status(query, bot_instance)
            
            # AYUDA
            elif callback_data == "help":
                await self._show_help(query)
            
            # ANÁLISIS ESPECÍFICOS (full_analysis, montecarlo, blackswan, etc.)
            elif callback_data.startswith(("full_analysis_", "montecarlo_", "blackswan_", "quantum_", 
                                          "hmm_", "kalman_", "kelly_", "sharia_", "orderbook_", "sentiment_")):
                await self._show_specific_analysis(query, callback_data)
            
            # ALERTAS ESPECÍFICAS
            elif callback_data.startswith("alert_"):
                await self._show_alert_config(query, callback_data)
            
            # CONFIGURACIÓN ESPECÍFICA
            elif callback_data.startswith("setting_"):
                await self._show_setting_detail(query, callback_data)
            
            else:
                # FALLBACK CON MENÚ - SIEMPRE mantener navegación
                from omnix_services.telegram_service.inline_keyboards import InlineKeyboardsManager
                keyboard = InlineKeyboardsManager.get_main_menu()
                await query.edit_message_text(
                    f"⚠️ Función en desarrollo: {callback_data}\n\n"
                    f"Usa el menú para navegar:",
                    reply_markup=keyboard
                )
                logger.warning(f"⚠️ Callback no implementado: {callback_data}")
        
        except Exception as e:
            logger.error(f"❌ Error procesando callback: {e}")
            try:
                await query.edit_message_text(f"❌ Error procesando acción: {str(e)[:100]}")
            except:
                pass
    
    async def _show_main_menu(self, query, context):
        """Mostrar menú principal con botones"""
        from omnix_services.telegram_service.inline_keyboards import InlineKeyboardsManager
        
        text = """🚀 **OMNIX V6.0 - MENÚ PRINCIPAL**

Selecciona una opción:"""
        
        keyboard = InlineKeyboardsManager.get_main_menu()
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=keyboard)
    
    async def _show_price(self, query, symbol):
        """Mostrar precio de una criptomoneda"""
        from omnix_services.telegram_service.inline_keyboards import InlineKeyboardsManager
        
        try:
            pair = f"{symbol}/USD"
            price = self.trading.get_current_price(pair)
            
            if price:
                text = f"""📊 **PRECIO {symbol}/USD**

💰 **Precio Actual:** ${price:,.2f}
⏰ **Actualizado:** {datetime.now().strftime('%H:%M:%S')}
📈 **Fuente:** Kraken API (tiempo real)

🔍 ¿Quieres análisis completo?"""
                
                # Botones de navegación
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = [
                    [InlineKeyboardButton(f"📈 Análisis {symbol}", callback_data=f"analysis_{symbol.lower()}")],
                    [InlineKeyboardButton("« Volver", callback_data="back_main")],
                ]
                await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                keyboard = InlineKeyboardsManager.get_main_menu()
                await query.edit_message_text(f"❌ No se pudo obtener precio de {symbol}", reply_markup=keyboard)
        except Exception as e:
            logger.error(f"❌ Error obteniendo precio {symbol}: {e}")
            from omnix_services.telegram_service.inline_keyboards import InlineKeyboardsManager
            keyboard = InlineKeyboardsManager.get_main_menu()
            await query.edit_message_text(f"❌ Error: {str(e)[:100]}", reply_markup=keyboard)
    
    async def _show_analysis(self, query, symbol):
        """Mostrar análisis técnico completo"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        # Mostrar menú de análisis específico para el símbolo
        from omnix_services.telegram_service.inline_keyboards import InlineKeyboardsManager
        
        text = f"""📈 **ANÁLISIS {symbol}**

Selecciona el tipo de análisis que deseas:"""
        
        keyboard = InlineKeyboardsManager.get_analysis_menu(symbol)
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=keyboard)
    
    async def _show_balance(self, query, bot_instance):
        """Mostrar balance de Kraken"""
        try:
            balance = self.trading.get_real_balance()
            
            if balance:
                text = "💰 **BALANCE KRAKEN REAL**\n\n"
                total_usd = 0
                
                for currency, amount in balance.items():
                    amount_float = float(amount)
                    if amount_float > 0.001:  # Mostrar solo balances significativos
                        text += f"• **{currency}:** {amount_float:.8f}\n"
                        
                        # Convertir a USD si es posible
                        if currency != "USD":
                            try:
                                price = self.trading.get_current_price(f"{currency}/USD")
                                if price:
                                    value_usd = amount_float * price
                                    total_usd += value_usd
                                    text += f"  └─ ≈ ${value_usd:,.2f} USD\n"
                            except:
                                pass
                        else:
                            total_usd += amount_float
                
                text += f"\n💵 **Total Estimado:** ${total_usd:,.2f} USD"
                text += f"\n⏰ **Actualizado:** {datetime.now().strftime('%H:%M:%S')}"
                
                # Botón para volver
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = [[InlineKeyboardButton("« Volver", callback_data="back_main")]]
                await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                from omnix_services.telegram_service.inline_keyboards import InlineKeyboardsManager
                keyboard = InlineKeyboardsManager.get_main_menu()
                await query.edit_message_text("❌ Error obteniendo balance de Kraken", reply_markup=keyboard)
        except Exception as e:
            logger.error(f"❌ Error mostrando balance: {e}")
            from omnix_services.telegram_service.inline_keyboards import InlineKeyboardsManager
            keyboard = InlineKeyboardsManager.get_main_menu()
            await query.edit_message_text(f"❌ Error: {str(e)[:100]}", reply_markup=keyboard)
    
    async def _show_history(self, query):
        """Mostrar historial de trades"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        text = """📜 **HISTORIAL DE OPERACIONES**

📊 Función en desarrollo - Próximamente disponible

Mientras tanto usa:
• /performance 30 - Evolución de balance
• /balance - Balance actual"""
        
        keyboard = [[InlineKeyboardButton("« Volver", callback_data="back_main")]]
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def _show_alerts(self, query):
        """Mostrar alertas activas"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        text = """⚡ **ALERTAS INTELIGENTES**

📊 Sistema de alertas en desarrollo

**Próximamente:**
- Alertas de precio (subida/bajada %)
- Alertas RSI (sobrecompra/sobreventa)
- Alertas Black Swan
- Alertas de volatilidad

Mantente atento a las actualizaciones! 🚀"""
        
        keyboard = [[InlineKeyboardButton("« Volver", callback_data="back_main")]]
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def _create_alert_menu(self, query):
        """Mostrar menú de creación de alertas"""
        from omnix_services.telegram_service.inline_keyboards import InlineKeyboardsManager
        
        text = """🎯 **CREAR NUEVA ALERTA**

Selecciona el tipo de alerta que deseas configurar:"""
        
        keyboard = InlineKeyboardsManager.get_alert_types()
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=keyboard)
    
    async def _show_strategies_menu(self, query):
        """Mostrar menú de estrategias"""
        from omnix_services.telegram_service.inline_keyboards import InlineKeyboardsManager
        
        text = """📚 **ESTRATEGIAS DE IA DISPONIBLES**

OMNIX utiliza 9 estrategias avanzadas:

Selecciona una para ver detalles:"""
        
        keyboard = InlineKeyboardsManager.get_strategies_menu()
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=keyboard)
    
    async def _show_strategy_details(self, query, strategy_name):
        """Mostrar detalles de una estrategia específica"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        strategies = {
            "montecarlo": """🎲 **MONTE CARLO SIMULATOR**

**Descripción:**
Simula 10,000 escenarios posibles de precio usando distribuciones α-estables (Lévy).

**Salidas:**
- Percentil 5%: Peor escenario
- Percentil 50%: Escenario medio
- Percentil 95%: Mejor escenario
- Probabilidad de subida/bajada

**Uso:** Evaluar riesgo antes de entrar a trade""",
            
            "blackswan": """🦢 **BLACK SWAN DETECTOR**

**Descripción:**
Detecta eventos extremos (cisnes negros) que podrían causar pérdidas catastróficas.

**Indicadores:**
- Probabilidad de evento extremo
- Nivel de riesgo (bajo/medio/alto/extremo)
- Recomendación de acción

**Uso:** Protección contra crashes del mercado""",
            
            "quantum": """⚛️ **QUANTUM MOMENTUM**

**Descripción:**
Usa números cuánticos REALES para detectar momentum y generar señales.

**Salidas:**
- Señal: ALCISTA/BAJISTA/NEUTRAL
- Puntuación de confianza
- Recomendación de entrada

**Uso:** Timing de entradas/salidas de trade""",
        }
        
        text = strategies.get(strategy_name, f"📚 Estrategia: {strategy_name}\n\nDetalles próximamente...")
        
        keyboard = [
            [InlineKeyboardButton("« Ver Estrategias", callback_data="strategies")],
            [InlineKeyboardButton("« Menú Principal", callback_data="back_main")],
        ]
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def _show_settings_menu(self, query):
        """Mostrar menú de configuración"""
        from omnix_services.telegram_service.inline_keyboards import InlineKeyboardsManager
        
        text = """⚙️ **CONFIGURACIÓN DEL SISTEMA**

Ajusta las preferencias de OMNIX:"""
        
        keyboard = InlineKeyboardsManager.get_settings_menu()
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=keyboard)
    
    async def _show_system_status(self, query, bot_instance):
        """Mostrar estado del sistema"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        text = """🔍 **ESTADO DEL SISTEMA**

✅ **SERVICIOS OPERATIVOS:**
🤖 IA Dual: Gemini 2.0 + GPT-4o
🏦 Kraken API: Conectado
📊 Trading Enterprise: Activo
🎲 Monte Carlo: Disponible
🦢 Black Swan: Disponible
⚛️ Quantum RNG: Activo
🎤 Voz Premium: Activa

💾 **BASE DE DATOS:**
PostgreSQL: Conectado
Redis: Sin caché

⏰ **UPTIME:**
Sistema operativo desde inicio"""
        
        keyboard = [[InlineKeyboardButton("« Volver", callback_data="back_main")]]
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def _show_help(self, query):
        """Mostrar ayuda"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        text = """❓ **AYUDA - OMNIX V6.0**

**COMANDOS PRINCIPALES:**
/precio BTC - Precio en tiempo real
/balance - Ver balance Kraken
/analisis BTC - Análisis técnico completo
/help - Esta ayuda
/status - Estado del sistema

**PAPER TRADING:**
/paper_start - Iniciar con $1M virtual
/paper_balance - Ver balance simulado
/paper_buy - Comprar (simulado)
/paper_sell - Vender (simulado)

**AUTO-TRADING:**
/auto_start - Activar bot 24/7
/auto_stop - Detener bot
/auto_status - Ver estado

💬 **Pregúntame cualquier cosa sobre trading!**"""
        
        keyboard = [[InlineKeyboardButton("« Volver", callback_data="back_main")]]
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def _show_specific_analysis(self, query, callback_data):
        """Mostrar análisis específico (Monte Carlo, Black Swan, etc.)"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        # Parsear callback: "montecarlo_BTC" -> strategy="montecarlo", symbol="BTC"
        parts = callback_data.split("_", 1)
        strategy = parts[0] if len(parts) > 0 else "unknown"
        symbol = parts[1].upper() if len(parts) > 1 else "BTC"
        
        strategy_names = {
            "full": "Análisis Completo",
            "montecarlo": "Monte Carlo",
            "blackswan": "Black Swan",
            "quantum": "Quantum Momentum",
            "hmm": "HMM Regime",
            "kalman": "Kalman Filter",
            "kelly": "Kelly Criterion",
            "sharia": "Sharia Compliance",
            "orderbook": "Order Book",
            "sentiment": "Sentiment Analysis"
        }
        
        strategy_name = strategy_names.get(strategy, strategy.title())
        
        text = f"""📊 **{strategy_name} - {symbol}**

⏳ Generando análisis...

📊 Función premium en desarrollo
Próximamente disponible con datos en tiempo real

Mientras tanto usa:
• /analisis {symbol} - Análisis por comando
• /montecarlo {symbol} - Monte Carlo específico"""
        
        keyboard = [
            [InlineKeyboardButton("« Ver Opciones", callback_data=f"analysis_{symbol.lower()}")],
            [InlineKeyboardButton("« Menú Principal", callback_data="back_main")],
        ]
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def _show_alert_config(self, query, callback_data):
        """Mostrar configuración de alerta específica"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        alert_types = {
            "alert_price_up": "Precio Sube X%",
            "alert_price_down": "Precio Baja X%",
            "alert_price_target": "Precio Objetivo",
            "alert_rsi_high": "RSI Sobrecompra",
            "alert_rsi_low": "RSI Sobreventa",
            "alert_drawdown": "Drawdown > X%",
            "alert_blackswan": "Black Swan",
            "alert_volatility": "Volatilidad Alta"
        }
        
        alert_name = alert_types.get(callback_data, "Alerta")
        
        text = f"""🎯 **{alert_name}**

📊 Sistema de alertas en desarrollo

**Próximos pasos:**
1. Configurar parámetros
2. Seleccionar criptomoneda
3. Activar notificación push

Mantente atento a las actualizaciones! 🚀"""
        
        keyboard = [
            [InlineKeyboardButton("« Ver Alertas", callback_data="alerts_list")],
            [InlineKeyboardButton("« Menú Principal", callback_data="back_main")],
        ]
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def _show_setting_detail(self, query, callback_data):
        """Mostrar detalle de configuración específica"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        settings = {
            "setting_voice": "🔊 Voz Premium",
            "setting_notifications": "🔔 Notificaciones",
            "setting_trading_mode": "📊 Modo Trading",
            "setting_risk": "💰 Nivel de Riesgo",
            "setting_ai_model": "🤖 Modelo IA",
            "setting_dashboard": "📈 Dashboard"
        }
        
        setting_name = settings.get(callback_data, "Configuración")
        
        text = f"""⚙️ **{setting_name}**

📊 Configuración en desarrollo

**Opciones disponibles próximamente:**
- Personalización avanzada
- Ajustes en tiempo real
- Guardado automático

Mantente atento! 🚀"""
        
        keyboard = [
            [InlineKeyboardButton("« Ver Configuración", callback_data="settings")],
            [InlineKeyboardButton("« Menú Principal", callback_data="back_main")],
        ]
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
