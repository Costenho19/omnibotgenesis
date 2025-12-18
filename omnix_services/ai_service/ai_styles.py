"""
OMNIX V5.1 ENTERPRISE - Visual Styles System
Ultra Premium Visual Response Formatting
Solicitado por Harold - Sistema de emojis y formato avanzado

FIX Dec 13, 2025: Pipeline idempotente que aplica exactamente UN badge por palabra.
Evita transformaciones en cascada que rompían el texto.
"""

import re
from datetime import datetime
from typing import Dict, List, Set
from omnix_core.utils.logger import get_logger

logger = get_logger(__name__)

EMOJI_CHARS = set('🚀✅💪🔥⭐🎯💎🏆💰📈📊💹🔄⚡📉🧠🔍📋🔬🚨⚠️🔔💡📢🚦₿🪙🌟😊😍🤩🎉🥳😎🤖🟢🔴🟡🟦🟤🟣🟠🔺🔻🔸🔹🔷🔶⟠🛡️🌊💧😴✨🚫💚❌💥➡️⬆️⬇️❄️')


class VisualStylesManager:
    """Premium Visual Formatting System"""
    
    def __init__(self):
        """Initialize visual styles configuration"""
        
        self.emoji_sets = {
            'success': ['🚀', '✅', '💪', '🔥', '⭐', '🎯', '💎', '🏆'],
            'trading': ['💰', '📈', '📊', '💹', '🔄', '⚡', '🎯', '📉'],
            'analysis': ['🧠', '📊', '🔍', '📈', '⚡', '🎯', '📋', '🔬'],
            'alerts': ['🚨', '⚠️', '🔔', '💡', '⭐', '🎯', '📢', '🚦'],
            'crypto': ['₿', '🪙', '💎', '🌟', '⚡', '🔥', '🚀', '💰'],
            'emotions': ['😊', '😍', '🤩', '🎉', '💪', '🥳', '😎', '🤖']
        }
        
        self.color_headers = {
            'crypto': '🟦 CRYPTO INTELLIGENCE',
            'trading': '🟩 TRADING SIGNALS', 
            'analysis': '🟪 MARKET ANALYSIS',
            'success': '🟨 SUCCESS METRICS',
            'alerts': '🟥 CRITICAL ALERTS',
            'money': '🟫 FINANCIAL DATA',
            'general': '⬜ OMNIX INSIGHTS'
        }
        
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
        
        self.visual_indicators = {
            'high': '🔺⬆️ HIGH',
            'medium': '🔸➡️ MEDIUM', 
            'low': '🔻⬇️ LOW',
            'very_high': '🚀🔥 VERY HIGH',
            'very_low': '📉❄️ VERY LOW'
        }
        
        self.premium_transformations = {
            'bitcoin': '₿🔥 Bitcoin',
            'btc': '₿💎 BTC',
            'ethereum': '⟠🚀 Ethereum', 
            'eth': '⟠⚡ ETH',
            'trading': '💹 Trading',
            'análisis': '📊 Análisis',
            'analysis': '📊 Analysis',
            'precio': '💰 Precio',
            'price': '💰 Price',
            'comprar': '🟢 COMPRAR',
            'buy': '🟢 BUY',
            'vender': '🔴 VENDER',
            'sell': '🔴 SELL',
            'bullish': '🟢📈 BULLISH',
            'bearish': '🔴📉 BEARISH',
            'profit': '🟢💎 PROFIT',
            'loss': '🔴⚠️ LOSS',
            'market': '🏛️ Market',
            'mercado': '🏛️ Mercado',
            'signal': '📡 Signal',
            'señal': '📡 Señal',
            'strategy': '🧠 Strategy',
            'estrategia': '🧠 Estrategia',
            'opportunity': '🎯 Opportunity',
            'oportunidad': '🎯 Oportunidad',
            'risk': '⚠️ Risk',
            'riesgo': '⚠️ Riesgo',
            'volatility': '⚡ Volatility',
            'volatilidad': '⚡ Volatilidad'
        }
        
        self.premium_separators = {
            'section': '━━━━━━━━━━━━',
            'subsection': '▔▔▔▔▔▔▔▔▔▔',
            'bullet_fancy': ['🔸', '🔹', '🔷', '🔶'],
            'dividers': ['*', '-', '+', 'o']
        }
    
    def _has_emoji_nearby(self, text: str, pos: int, window: int = 3) -> bool:
        """
        Detectar si hay un emoji cerca de la posición dada.
        Evita transformar palabras que ya tienen badges.
        """
        start = max(0, pos - window)
        end = min(len(text), pos + window)
        segment = text[start:end]
        return any(char in EMOJI_CHARS for char in segment)
    
    def _apply_keyword_enhancements(self, text: str, processed_words: Set[str]) -> str:
        """
        Aplicar transformaciones premium con word boundaries.
        Solo transforma cada palabra UNA vez.
        
        Args:
            text: Texto a procesar
            processed_words: Set de palabras ya procesadas (se actualiza in-place)
        
        Returns:
            Texto con badges aplicados
        """
        result = text
        
        for word, premium_word in self.premium_transformations.items():
            if word in processed_words:
                continue
            
            pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
            
            match = pattern.search(result)
            if match:
                if self._has_emoji_nearby(result, match.start()):
                    processed_words.add(word)
                    continue
                
                result = pattern.sub(premium_word, result, count=1)
                processed_words.add(word)
        
        return result
    
    def _has_omnix_header(self, text: str) -> bool:
        """
        Detect if text already has an OMNIX header to avoid duplication.
        FIX Dec 14, 2025: Gemini learns header pattern from conversation history.
        """
        header_patterns = [
            'OMNIX INSIGHTS',
            'CRYPTO INTELLIGENCE',
            'TRADING SIGNALS',
            'MARKET ANALYSIS',
            'SUCCESS METRICS',
            'CRITICAL ALERTS',
            'FINANCIAL DATA',
        ]
        first_lines = text[:200] if len(text) > 200 else text
        return any(pattern in first_lines for pattern in header_patterns)
    
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
            processed_words: Set[str] = set()
            
            processed_text = self._apply_keyword_enhancements(processed_text, processed_words)
            
            if '\n-' in processed_text or '\n•' in processed_text:
                fancy_bullet = self.premium_separators['bullet_fancy'][0]
                processed_text = processed_text.replace('\n-', f'\n{fancy_bullet}')
                processed_text = processed_text.replace('\n•', f'\n{fancy_bullet}')
            
            # FIX Dec 14, 2025: Skip header if already present (Gemini learned pattern from history)
            already_has_header = self._has_omnix_header(response_text)
            
            current_time = datetime.now().strftime('%H:%M')
            price_display = f"${current_price:,.2f}" if current_price > 0 else "$0.00"
            
            if already_has_header:
                # Only return processed text without footer duplication
                logger.debug("Header already detected in AI response, skipping header addition")
                final_response = processed_text
            else:
                # Return processed text only (clean, professional)
                final_response = processed_text
            
            return final_response
            
        except Exception as e:
            logger.error(f"Error applying visual style: {e}")
            return response_text
    
    def apply_visual_enhancements(self, text: str) -> str:
        """
        Método público para aplicar mejoras visuales (usado por OmnixStyleRenderer).
        Pipeline simplificado que solo aplica transformaciones premium.
        """
        processed_words: Set[str] = set()
        return self._apply_keyword_enhancements(text, processed_words)
    
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
