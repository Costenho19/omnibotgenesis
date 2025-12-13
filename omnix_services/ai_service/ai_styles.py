"""
OMNIX V5.1 ENTERPRISE - Visual Styles System
Ultra Premium Visual Response Formatting
Solicitado por Harold - Sistema de emojis y formato avanzado
"""

import re
from datetime import datetime
from typing import Dict, List
from omnix_core.utils.logger import get_logger

logger = get_logger(__name__)


class VisualStylesManager:
    """Premium Visual Formatting System"""
    
    def __init__(self):
        """Initialize visual styles configuration"""
        
        # 🎨 EMOJIS PREMIUM POR CATEGORÍA
        self.emoji_sets = {
            'success': ['🚀', '✅', '💪', '🔥', '⭐', '🎯', '💎', '🏆'],
            'trading': ['💰', '📈', '📊', '💹', '🔄', '⚡', '🎯', '📉'],
            'analysis': ['🧠', '📊', '🔍', '📈', '⚡', '🎯', '📋', '🔬'],
            'alerts': ['🚨', '⚠️', '🔔', '💡', '⭐', '🎯', '📢', '🚦'],
            'crypto': ['₿', '🪙', '💎', '🌟', '⚡', '🔥', '🚀', '💰'],
            'emotions': ['😊', '😍', '🤩', '🎉', '💪', '🥳', '😎', '🤖']
        }
        
        # 🎨 HEADERS COLORIDOS POR CONTEXTO
        self.color_headers = {
            'crypto': '🟦 CRYPTO INTELLIGENCE',
            'trading': '🟩 TRADING SIGNALS', 
            'analysis': '🟪 MARKET ANALYSIS',
            'success': '🟨 SUCCESS METRICS',
            'alerts': '🟥 CRITICAL ALERTS',
            'money': '🟫 FINANCIAL DATA',
            'general': '⬜ OMNIX INSIGHTS'
        }
        
        # 🎯 SUBTÍTULOS CON COLORES
        self.colored_subtitles = {
            'bullish': '🟢 BULLISH SIGNAL',
            'bearish': '🔴 BEARISH SIGNAL', 
            'neutral': '🟡 NEUTRAL ZONE',
            'strong': '🟦 STRONG MOMENTUM',
            'weak': '🟤 WEAK MOMENTUM',
            'opportunity': '🟣 OPPORTUNITY DETECTED',
            'risk': '🟠 RISK MANAGEMENT',
            'profit': '🟢 PROFIT TARGET',
            'loss': '🔴 STOP LOSS'
        }
        
        # 📊 INDICADORES VISUALES
        self.visual_indicators = {
            'high': '🔺⬆️ HIGH',
            'medium': '🔸➡️ MEDIUM', 
            'low': '🔻⬇️ LOW',
            'very_high': '🚀🔥 VERY HIGH',
            'very_low': '📉❄️ VERY LOW'
        }
        
        # 🔥 TRANSFORMACIONES PREMIUM DE PALABRAS
        self.premium_transformations = {
            'bitcoin': '₿🔥 Bitcoin',
            'btc': '₿💎 BTC',
            'ethereum': '⟠🚀 Ethereum', 
            'eth': '⟠⚡ ETH',
            'trading': '💹🎯 Trading',
            'análisis': '📊🧠 Análisis',
            'analysis': '📊🔍 Analysis',
            'precio': '💰📈 Precio',
            'price': '💰🎯 Price',
            'comprar': '🟢💎 COMPRAR',
            'buy': '🟢🚀 BUY',
            'vender': '🔴💰 VENDER',
            'sell': '🔴📉 SELL',
            'bullish': '🟢🚀📈 BULLISH',
            'bearish': '🔴📉⬇️ BEARISH',
            'profit': '🟢💎✨ PROFIT',
            'loss': '🔴⚠️📉 LOSS',
            'high': '🔺⬆️🔥 HIGH',
            'low': '🔻⬇️❄️ LOW',
            'strong': '💪🔥⚡ STRONG',
            'weak': '📉💧😴 WEAK',
            'market': '🏛️📊 Market',
            'mercado': '🏛️📊 Mercado',
            'signal': '📡🎯 Signal',
            'señal': '📡⚡ Señal',
            'strategy': '🧠⚡ Strategy',
            'estrategia': '🧠🎯 Estrategia',
            'opportunity': '🎯💎 Opportunity',
            'oportunidad': '🎯✨ Oportunidad',
            'risk': '⚠️🛡️ Risk',
            'riesgo': '⚠️🔥 Riesgo',
            'volatility': '⚡🌊 Volatility',
            'volatilidad': '⚡📊 Volatilidad'
        }
        
        # 🎨 SEPARADORES VISUALES PREMIUM
        self.premium_separators = {
            'section': '━━━━━━━━━━━━',
            'subsection': '▔▔▔▔▔▔▔▔▔▔',
            'bullet_fancy': ['🔸', '🔹', '🔷', '🔶'],
            'dividers': ['*', '-', '+', 'o']
        }
        
        # 📊 PATRONES DE SUBTÍTULOS PARA DETECCIÓN
        self.subtitle_patterns = {
            r'(análisis|analysis)': lambda m: f"🟪 📊🧠 {m.group(1).upper()} AVANZADO ⚡",
            r'(trading|💹 trading)': lambda m: f"🟩 💹🎯 TRADING SEÑALES 🚀",
            r'(precio|💰 precio|price)': lambda m: f"🟨 💰📈 PRECIO ACTUAL 🔥",
            r'(recomendación|recommendation)': lambda m: f"🟦 🎯💎 RECOMENDACIÓN EXPERTA ⭐",
            r'(riesgo|🔥 riesgo|risk)': lambda m: f"🟠 ⚠️🛡️ GESTIÓN DE RIESGO 📊",
            r'(oportunidad|🎯 oportunidad|opportunity)': lambda m: f"🟣 💎✨ OPORTUNIDAD DETECTADA 🚀",
            r'(estrategia|🧠 estrategia|strategy)': lambda m: f"🟪 🧠⚡ ESTRATEGIA INTELIGENTE 🎯",
            r'(mercado|market)': lambda m: f"🟦 🏛️📊 ANÁLISIS DE MERCADO 🌐",
            r'(señal|signal)': lambda m: f"🟩 📡⚡ SEÑAL DETECTADA 🎯",
            r'(tendencia|trend)': lambda m: f"🟨 📈🔮 TENDENCIA IDENTIFICADA ⚡",
            r'(volatilidad|volatility)': lambda m: f"🟠 ⚡🌊 VOLATILIDAD MEDIDA 📊",
            r'(soporte|support)': lambda m: f"🟢 🛡️💪 SOPORTE TÉCNICO 📈",
            r'(resistencia|resistance)': lambda m: f"🔴 🚫⬆️ RESISTENCIA TÉCNICA 📊",
            r'(momento|momentum)': lambda m: f"🟦 🚀⚡ MOMENTUM ACTUAL 💪"
        }
    
    def apply_ultra_visual_style(
        self, 
        response_text: str, 
        intent: str = 'general',
        current_price: float = 0.0
    ) -> str:
        """
        Aplicar estilo visual premium ultra avanzado
        
        Args:
            response_text: Texto de respuesta a formatear
            intent: Tipo de intención (crypto, trading, analysis, etc)
            current_price: Precio actual para footer dinámico
            
        Returns:
            Texto formateado con estilo premium
        """
        try:
            processed_text = response_text
            
            # FIX Dec 13, 2025: DESHABILITADO subtitle_patterns y premium_transformations
            # Causaban transformaciones en cascada que rompían el texto:
            # Ejemplo: "PAPER TRADING" → "PAPER 🟩 💹🎯 💹🎯 TRADING 🟩 📡⚡ SEÑAL..."
            # El AI de Gemini ya genera texto legible, no necesita transformación agresiva.
            #
            # Si se quiere re-habilitar en el futuro, usar una lista de "palabras ya procesadas"
            # para evitar transformaciones múltiples en la misma palabra.
            
            # 3️⃣ AÑADIR BULLETS FANCY
            if '\n-' in processed_text or '\n•' in processed_text:
                fancy_bullet = self.premium_separators['bullet_fancy'][0]
                processed_text = processed_text.replace('\n-', f'\n{fancy_bullet}')
                processed_text = processed_text.replace('\n•', f'\n{fancy_bullet}')
            
            # 4️⃣ SELECCIONAR EMOJIS Y HEADER POR CONTEXTO
            selected_emojis = self.emoji_sets.get(intent, self.emoji_sets['crypto'])
            header_emoji = selected_emojis[0] if selected_emojis else '🤖'
            color_header = self.color_headers.get(intent, self.color_headers['general'])
            
            # 5️⃣ CONSTRUCCIÓN FINAL CON FORMATO ULTRA PREMIUM
            current_time = datetime.now().strftime('%H:%M')
            price_display = f"${current_price:,.2f}" if current_price > 0 else "$0.00"
            
            final_response = f"""{header_emoji} {color_header} {header_emoji}
{self.premium_separators['section']}

{processed_text}

{self.premium_separators['subsection']}
🤖💎 OMNIX V5.1 • 🚀 • ENTERPRISE ⚡

📊 Live: {price_display} USD • 💹 Kraken • 🧠 Gemini AI
🚀 Trading 24/7 • ⏰ {current_time} • 🌐 Global

🔵 PO 🔴 YT 🔵 TG • 💚 37 🔥 1 👁️ 1232"""
            
            return final_response
            
        except Exception as e:
            logger.error(f"Error applying visual style: {e}")
            return response_text
    
    def get_emoji_by_sentiment(self, sentiment: str) -> str:
        """Get emoji based on sentiment"""
        sentiment_emojis = {
            'very_positive': '🚀💎✨',
            'positive': '✅💚📈',
            'neutral': '⚪️➡️',
            'negative': '⚠️📉',
            'very_negative': '🔴❌💥'
        }
        return sentiment_emojis.get(sentiment, '🤖')
    
    def format_percentage(self, value: float) -> str:
        """Format percentage with visual indicators"""
        if value > 5:
            return f"🔺⬆️ +{value:.2f}%"
        elif value > 0:
            return f"🟢 +{value:.2f}%"
        elif value == 0:
            return f"⚪️ {value:.2f}%"
        elif value > -5:
            return f"🔴 {value:.2f}%"
        else:
            return f"🔻⬇️ {value:.2f}%"
    
    def format_price(self, price: float, change: float = 0) -> str:
        """Format price with visual styling"""
        price_str = f"${price:,.2f}"
        
        if change > 0:
            return f"💰📈 {price_str} 🟢"
        elif change < 0:
            return f"💰📉 {price_str} 🔴"
        else:
            return f"💰 {price_str}"
