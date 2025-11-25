"""
OMNIX V5.4 ULTRA - Inline Keyboards Premium
Sistema profesional de botones interactivos para Telegram
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class InlineKeyboardsManager:
    """
    Gestor de teclados inline profesionales para OMNIX
    Diseño institucional con categorías organizadas
    """
    
    @staticmethod
    def get_main_menu() -> InlineKeyboardMarkup:
        """
        Menú principal con todas las opciones organizadas
        Diseño premium con emojis estratégicos
        """
        keyboard = [
            # Fila 1: Análisis de mercado
            [
                InlineKeyboardButton("📊 Precio BTC", callback_data="price_btc"),
                InlineKeyboardButton("📈 Análisis BTC", callback_data="analysis_btc"),
            ],
            # Fila 2: Otras criptos
            [
                InlineKeyboardButton("💎 Precio ETH", callback_data="price_eth"),
                InlineKeyboardButton("📊 Análisis ETH", callback_data="analysis_eth"),
            ],
            # Fila 3: Cuenta y balance
            [
                InlineKeyboardButton("💰 Balance Kraken", callback_data="balance"),
                InlineKeyboardButton("📜 Historial", callback_data="history"),
            ],
            # Fila 4: Trading y alertas
            [
                InlineKeyboardButton("⚡ Alertas Activas", callback_data="alerts_list"),
                InlineKeyboardButton("🎯 Nueva Alerta", callback_data="alert_create"),
            ],
            # Fila 5: Configuración y ayuda
            [
                InlineKeyboardButton("📚 Estrategias IA", callback_data="strategies"),
                InlineKeyboardButton("⚙️ Configuración", callback_data="settings"),
            ],
            # Fila 6: Estado del sistema
            [
                InlineKeyboardButton("🔍 Estado Sistema", callback_data="status"),
                InlineKeyboardButton("❓ Ayuda", callback_data="help"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_crypto_selector() -> InlineKeyboardMarkup:
        """
        Selector de criptomonedas para análisis
        """
        keyboard = [
            [
                InlineKeyboardButton("₿ Bitcoin", callback_data="select_btc"),
                InlineKeyboardButton("💎 Ethereum", callback_data="select_eth"),
            ],
            [
                InlineKeyboardButton("🔷 Cardano", callback_data="select_ada"),
                InlineKeyboardButton("❄️ Avalanche", callback_data="select_avax"),
            ],
            [
                InlineKeyboardButton("🔺 Polygon", callback_data="select_matic"),
                InlineKeyboardButton("⚫ Polkadot", callback_data="select_dot"),
            ],
            [
                InlineKeyboardButton("🔗 Chainlink", callback_data="select_link"),
                InlineKeyboardButton("« Volver", callback_data="back_main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_analysis_menu(symbol: str = "BTC") -> InlineKeyboardMarkup:
        """
        Menú de opciones de análisis para una cripto específica
        """
        keyboard = [
            [
                InlineKeyboardButton("📊 Análisis Completo", callback_data=f"full_analysis_{symbol}"),
            ],
            [
                InlineKeyboardButton("🎲 Monte Carlo", callback_data=f"montecarlo_{symbol}"),
                InlineKeyboardButton("🦢 Black Swan", callback_data=f"blackswan_{symbol}"),
            ],
            [
                InlineKeyboardButton("⚛️ Quantum", callback_data=f"quantum_{symbol}"),
                InlineKeyboardButton("🔮 HMM Regime", callback_data=f"hmm_{symbol}"),
            ],
            [
                InlineKeyboardButton("📉 Kalman Filter", callback_data=f"kalman_{symbol}"),
                InlineKeyboardButton("💹 Kelly Criterion", callback_data=f"kelly_{symbol}"),
            ],
            [
                InlineKeyboardButton("☪️ Sharia Check", callback_data=f"sharia_{symbol}"),
                InlineKeyboardButton("📖 Order Book", callback_data=f"orderbook_{symbol}"),
            ],
            [
                InlineKeyboardButton("« Volver", callback_data="back_main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_alert_types() -> InlineKeyboardMarkup:
        """
        Tipos de alertas disponibles
        """
        keyboard = [
            [
                InlineKeyboardButton("📈 Precio Sube X%", callback_data="alert_price_up"),
                InlineKeyboardButton("📉 Precio Baja X%", callback_data="alert_price_down"),
            ],
            [
                InlineKeyboardButton("🎯 Precio Objetivo", callback_data="alert_price_target"),
                InlineKeyboardButton("⚠️ RSI Sobrecompra", callback_data="alert_rsi_high"),
            ],
            [
                InlineKeyboardButton("💰 RSI Sobreventa", callback_data="alert_rsi_low"),
                InlineKeyboardButton("🔴 Drawdown > X%", callback_data="alert_drawdown"),
            ],
            [
                InlineKeyboardButton("🦢 Black Swan", callback_data="alert_blackswan"),
                InlineKeyboardButton("🌊 Volatilidad Alta", callback_data="alert_volatility"),
            ],
            [
                InlineKeyboardButton("« Cancelar", callback_data="back_main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_trading_menu(symbol: str = "BTC") -> InlineKeyboardMarkup:
        """
        Menú de trading para ejecutar operaciones
        """
        keyboard = [
            [
                InlineKeyboardButton(f"🟢 COMPRAR {symbol}", callback_data=f"buy_{symbol}"),
                InlineKeyboardButton(f"🔴 VENDER {symbol}", callback_data=f"sell_{symbol}"),
            ],
            [
                InlineKeyboardButton("📊 Análisis Pre-Trade", callback_data=f"pretrade_{symbol}"),
            ],
            [
                InlineKeyboardButton("💰 Calcular Position Size", callback_data=f"position_{symbol}"),
            ],
            [
                InlineKeyboardButton("« Volver", callback_data="back_main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_strategies_menu() -> InlineKeyboardMarkup:
        """
        Menú de estrategias de IA disponibles
        """
        keyboard = [
            [
                InlineKeyboardButton("🎲 Monte Carlo Simulator", callback_data="strat_montecarlo"),
            ],
            [
                InlineKeyboardButton("🦢 Black Swan Detector", callback_data="strat_blackswan"),
            ],
            [
                InlineKeyboardButton("⚛️ Quantum Momentum", callback_data="strat_quantum"),
            ],
            [
                InlineKeyboardButton("🔮 HMM Regime Detection", callback_data="strat_hmm"),
            ],
            [
                InlineKeyboardButton("📉 Dual Kalman Filter", callback_data="strat_kalman"),
            ],
            [
                InlineKeyboardButton("💹 Kelly Criterion", callback_data="strat_kelly"),
            ],
            [
                InlineKeyboardButton("☪️ Sharia Compliance", callback_data="strat_sharia"),
            ],
            [
                InlineKeyboardButton("📖 Order Book Analysis", callback_data="strat_orderbook"),
            ],
            [
                InlineKeyboardButton("🎭 Sentiment Analysis", callback_data="strat_sentiment"),
            ],
            [
                InlineKeyboardButton("« Volver", callback_data="back_main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_confirmation(action: str, symbol: str = "") -> InlineKeyboardMarkup:
        """
        Teclado de confirmación para acciones críticas
        """
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirmar", callback_data=f"confirm_{action}_{symbol}"),
                InlineKeyboardButton("❌ Cancelar", callback_data="back_main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_settings_menu() -> InlineKeyboardMarkup:
        """
        Menú de configuración del sistema
        """
        keyboard = [
            [
                InlineKeyboardButton("🔊 Voz ON/OFF", callback_data="setting_voice"),
                InlineKeyboardButton("🔔 Notificaciones", callback_data="setting_notifications"),
            ],
            [
                InlineKeyboardButton("📊 Modo Trading", callback_data="setting_trading_mode"),
                InlineKeyboardButton("💰 Risk Level", callback_data="setting_risk"),
            ],
            [
                InlineKeyboardButton("🤖 Modelo IA", callback_data="setting_ai_model"),
                InlineKeyboardButton("📈 Dashboard", callback_data="setting_dashboard"),
            ],
            [
                InlineKeyboardButton("« Volver", callback_data="back_main"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_quick_actions() -> InlineKeyboardMarkup:
        """
        Acciones rápidas más usadas
        """
        keyboard = [
            [
                InlineKeyboardButton("⚡ Precio BTC", callback_data="price_btc"),
                InlineKeyboardButton("💰 Balance", callback_data="balance"),
            ],
            [
                InlineKeyboardButton("📊 Ver Más Opciones", callback_data="show_main_menu"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_trade_feedback_buttons(trade_id: str, strategy: str = "PAPER", 
                                   symbol: str = "BTC", signal_type: str = "BUY") -> InlineKeyboardMarkup:
        """
        Botones de feedback rápido para señales de trading
        
        Args:
            trade_id: ID único del trade para tracking
            strategy: Nombre de la estrategia (ARES_V1, ARES_V2, PAPER, etc.)
            symbol: Símbolo del par (BTC, ETH, etc.)
            signal_type: Tipo de señal (BUY, SELL)
        
        Returns:
            InlineKeyboardMarkup con botones de feedback
        """
        callback_base = f"feedback|{trade_id}|{strategy}|{symbol}|{signal_type}"
        
        keyboard = [
            [
                InlineKeyboardButton("👍 Buen Trade", callback_data=f"{callback_base}|success"),
                InlineKeyboardButton("👎 Mal Trade", callback_data=f"{callback_base}|failure"),
            ],
            [
                InlineKeyboardButton("💡 Sugerencia", callback_data=f"{callback_base}|suggest"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_signal_feedback_buttons(signal_id: str, strategy: str, 
                                    symbol: str, signal_type: str,
                                    market_condition: str = "unknown") -> InlineKeyboardMarkup:
        """
        Botones de feedback para señales ARES automáticas
        
        Args:
            signal_id: ID único de la señal
            strategy: ARES_V1, ARES_V2, etc.
            symbol: Par de trading
            signal_type: BUY/SELL
            market_condition: bullish/bearish/sideways
        
        Returns:
            InlineKeyboardMarkup con opciones de feedback detallado
        """
        callback_base = f"sigfb|{signal_id}|{strategy}|{symbol}|{signal_type}|{market_condition}"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Funcionó", callback_data=f"{callback_base}|success"),
                InlineKeyboardButton("❌ Falló", callback_data=f"{callback_base}|failure"),
                InlineKeyboardButton("⚖️ Parcial", callback_data=f"{callback_base}|partial"),
            ],
            [
                InlineKeyboardButton("⭐ Votar Estrategia", callback_data=f"vote|{strategy}"),
                InlineKeyboardButton("💡 Proponer Mejora", callback_data=f"propose|{strategy}|{symbol}"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
