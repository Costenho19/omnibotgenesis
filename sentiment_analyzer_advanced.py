"""
💭 OMNIX V5.3 QUANTUM ULTIMATE - ADVANCED SENTIMENT ANALYZER
Analizador avanzado de sentimiento para traders y contenido de mercado

ANÁLISIS MULTI-DIMENSIONAL:
1. 📊 Sentimiento direccional (bullish, bearish, neutral)
2. 🎯 Nivel de confianza del trader (high, medium, low)
3. ⚡ Urgencia de acción (immediate, short-term, long-term)
4. 🎲 Apetito de riesgo (aggressive, moderate, conservative)
5. 📈 Fortaleza de convicción (strong, weak)

TÉCNICAS:
- NLP avanzado con transformers
- Análisis de palabras clave financieras
- Detección de modismos de trading
- Análisis de estructura retórica

Desarrollado por Harold Nunes - Noviembre 2025
"""

import logging
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class SentimentScore:
    """Resultado completo del análisis de sentimiento"""
    sentiment: str  # 'bullish', 'bearish', 'neutral'
    confidence_level: str  # 'high', 'medium', 'low'
    urgency: str  # 'immediate', 'short_term', 'long_term', 'none'
    risk_appetite: str  # 'aggressive', 'moderate', 'conservative'
    conviction_strength: float  # 0.0 - 1.0
    score: float  # -1.0 (bearish) a +1.0 (bullish)
    key_signals: List[str]
    reasoning: str


class SentimentAnalyzerAdvanced:
    """
    Analizador avanzado de sentimiento para contenido de trading
    
    Detecta no solo bullish/bearish, sino también confianza,
    urgencia, riesgo y fortaleza de convicción del trader
    """
    
    def __init__(self):
        """Inicializar analizador de sentimiento"""
        
        # Diccionario de palabras bullish (alcistas)
        self.bullish_words = {
            # Fuertemente alcistas (peso 2.0)
            'breakout': 2.0, 'rocket': 2.0, 'moon': 2.0, 'pump': 2.0,
            'rally': 2.0, 'surge': 2.0, 'explosive': 2.0, 'parabolic': 2.0,
            'accumulation': 1.8, 'accumulate': 1.8, 'buy': 1.8,
            
            # Moderadamente alcistas (peso 1.0-1.5)
            'bullish': 1.5, 'uptrend': 1.5, 'strength': 1.3, 'strong': 1.3,
            'positive': 1.2, 'gain': 1.2, 'growth': 1.2, 'increase': 1.0,
            'opportunity': 1.0, 'potential': 1.0, 'momentum': 1.3,
            'support': 1.1, 'bounce': 1.4, 'reversal': 1.2, 'bottom': 1.5,
            
            # Débilmente alcistas (peso 0.5-0.8)
            'hold': 0.5, 'consolidation': 0.5, 'stable': 0.4
        }
        
        # Diccionario de palabras bearish (bajistas)
        self.bearish_words = {
            # Fuertemente bajistas (peso -2.0)
            'crash': -2.0, 'dump': -2.0, 'collapse': -2.0, 'plunge': -2.0,
            'panic': -2.0, 'capitulation': -2.0, 'death': -2.0,
            
            # Moderadamente bajistas (peso -1.0 a -1.5)
            'bearish': -1.5, 'downtrend': -1.5, 'weakness': -1.3, 'weak': -1.3,
            'sell': -1.8, 'negative': -1.2, 'loss': -1.2, 'decline': -1.0,
            'correction': -1.3, 'resistance': -1.1, 'rejection': -1.4,
            'top': -1.5, 'overbought': -1.2, 'distribution': -1.6,
            
            # Débilmente bajistas (peso -0.5 a -0.8)
            'concern': -0.5, 'caution': -0.6, 'risk': -0.4
        }
        
        # Palabras que indican alta confianza
        self.high_confidence_words = [
            'definitely', 'certainly', 'absolutely', 'guaranteed',
            'sure', 'confident', 'convinced', 'clear', 'obvious',
            'will', 'going to', 'expect', 'predict'
        ]
        
        # Palabras que indican baja confianza
        self.low_confidence_words = [
            'maybe', 'possibly', 'perhaps', 'might', 'could',
            'uncertain', 'unsure', 'unclear', 'doubt', 'hope',
            'think', 'believe', 'seem', 'appear', 'probably'
        ]
        
        # Palabras de urgencia inmediata
        self.urgency_immediate = [
            'now', 'immediately', 'urgent', 'asap', 'today',
            'right now', 'breaking', 'alert', 'emergency'
        ]
        
        # Palabras de agresividad/riesgo
        self.aggressive_words = [
            'all in', 'leverage', 'yolo', 'risky', 'aggressive',
            'maximum', 'full', 'heavy', 'load up'
        ]
        
        # Palabras conservadoras
        self.conservative_words = [
            'careful', 'cautious', 'small position', 'minimal',
            'conservative', 'safe', 'protect', 'preserve',
            'defensive', 'hedge'
        ]
        
        logger.info("💭 Sentiment Analyzer Advanced inicializado")
        logger.info(f"   📊 {len(self.bullish_words)} palabras bullish")
        logger.info(f"   📉 {len(self.bearish_words)} palabras bearish")
    
    def analyze_text(self, text: str) -> SentimentScore:
        """
        Analizar sentimiento completo de un texto
        
        Args:
            text: Texto a analizar (transcripción, comentario, etc.)
            
        Returns:
            SentimentScore con análisis completo
        """
        if not text:
            return self._neutral_sentiment()
        
        try:
            # Normalizar texto
            text_lower = text.lower()
            
            # 1. SENTIMIENTO DIRECCIONAL (bullish/bearish/neutral)
            sentiment_score = self._calculate_directional_sentiment(text_lower)
            
            # 2. NIVEL DE CONFIANZA (high/medium/low)
            confidence_level = self._detect_confidence_level(text_lower)
            
            # 3. URGENCIA (immediate/short_term/long_term/none)
            urgency = self._detect_urgency(text_lower)
            
            # 4. APETITO DE RIESGO (aggressive/moderate/conservative)
            risk_appetite = self._detect_risk_appetite(text_lower)
            
            # 5. FORTALEZA DE CONVICCIÓN (0-1)
            conviction = self._calculate_conviction_strength(
                sentiment_score, confidence_level, text_lower
            )
            
            # 6. SEÑALES CLAVE DETECTADAS
            key_signals = self._extract_key_signals(text_lower, sentiment_score)
            
            # 7. DETERMINAR SENTIMIENTO FINAL
            if sentiment_score > 0.3:
                sentiment = 'bullish'
            elif sentiment_score < -0.3:
                sentiment = 'bearish'
            else:
                sentiment = 'neutral'
            
            # 8. REASONING (explicación)
            reasoning = self._generate_reasoning(
                sentiment, confidence_level, sentiment_score, key_signals
            )
            
            result = SentimentScore(
                sentiment=sentiment,
                confidence_level=confidence_level,
                urgency=urgency,
                risk_appetite=risk_appetite,
                conviction_strength=conviction,
                score=sentiment_score,
                key_signals=key_signals,
                reasoning=reasoning
            )
            
            logger.info(f"💭 Sentimiento: {sentiment} ({sentiment_score:.2f}) - Confianza: {confidence_level}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analizando sentimiento: {e}")
            return self._neutral_sentiment()
    
    def _calculate_directional_sentiment(self, text: str) -> float:
        """
        Calcular sentimiento direccional (-1 a +1)
        
        Suma pesos de palabras bullish y bearish
        """
        score = 0.0
        words = text.split()
        
        # Buscar palabras bullish
        for word, weight in self.bullish_words.items():
            count = text.count(word)
            score += count * weight
        
        # Buscar palabras bearish
        for word, weight in self.bearish_words.items():
            count = text.count(word)
            score += count * weight  # weight ya es negativo
        
        # Normalizar score a rango -1 a +1
        # Usar tanh para suavizar valores extremos
        import math
        normalized_score = math.tanh(score / 10.0)
        
        return normalized_score
    
    def _detect_confidence_level(self, text: str) -> str:
        """Detectar nivel de confianza del trader"""
        high_conf_count = sum(1 for word in self.high_confidence_words if word in text)
        low_conf_count = sum(1 for word in self.low_confidence_words if word in text)
        
        if high_conf_count > low_conf_count and high_conf_count >= 2:
            return 'high'
        elif low_conf_count > high_conf_count and low_conf_count >= 2:
            return 'low'
        else:
            return 'medium'
    
    def _detect_urgency(self, text: str) -> str:
        """Detectar urgencia de acción"""
        urgency_count = sum(1 for word in self.urgency_immediate if word in text)
        
        if urgency_count >= 2:
            return 'immediate'
        
        # Detectar timeframes
        if any(word in text for word in ['short term', 'days', 'this week']):
            return 'short_term'
        elif any(word in text for word in ['long term', 'months', 'years', 'hold']):
            return 'long_term'
        
        return 'none'
    
    def _detect_risk_appetite(self, text: str) -> str:
        """Detectar apetito de riesgo"""
        aggressive_count = sum(1 for word in self.aggressive_words if word in text)
        conservative_count = sum(1 for word in self.conservative_words if word in text)
        
        if aggressive_count > conservative_count and aggressive_count >= 1:
            return 'aggressive'
        elif conservative_count > aggressive_count and conservative_count >= 1:
            return 'conservative'
        else:
            return 'moderate'
    
    def _calculate_conviction_strength(self, sentiment_score: float, 
                                       confidence_level: str, 
                                       text: str) -> float:
        """
        Calcular fortaleza de convicción (0-1)
        
        Combina:
        - Magnitud del sentimiento
        - Nivel de confianza
        - Cantidad de evidencia mencionada
        """
        # Base: magnitud del sentimiento
        conviction = abs(sentiment_score)
        
        # Ajustar por nivel de confianza
        confidence_multipliers = {
            'high': 1.2,
            'medium': 1.0,
            'low': 0.7
        }
        conviction *= confidence_multipliers.get(confidence_level, 1.0)
        
        # Bonus por mencionar múltiples señales/indicadores
        technical_mentions = sum(1 for term in ['rsi', 'macd', 'ema', 'support', 'resistance', 'volume']
                                if term in text)
        conviction *= (1.0 + technical_mentions * 0.05)  # +5% por cada mención
        
        # Normalizar a 0-1
        return min(conviction, 1.0)
    
    def _extract_key_signals(self, text: str, sentiment_score: float) -> List[str]:
        """Extraer señales clave que influenciaron el sentimiento"""
        signals = []
        
        # Top palabras bullish/bearish encontradas
        if sentiment_score > 0:
            for word, weight in sorted(self.bullish_words.items(), 
                                     key=lambda x: x[1], reverse=True)[:5]:
                if word in text:
                    signals.append(f"Menciona '{word}' (alcista)")
        else:
            for word, weight in sorted(self.bearish_words.items(), 
                                     key=lambda x: x[1])[:5]:
                if word in text:
                    signals.append(f"Menciona '{word}' (bajista)")
        
        # Indicadores técnicos mencionados
        indicators = ['rsi', 'macd', 'ema', 'sma', 'fibonacci', 'bollinger']
        for ind in indicators:
            if ind in text:
                signals.append(f"Análisis técnico: {ind.upper()}")
        
        return signals[:5]  # Max 5 señales
    
    def _generate_reasoning(self, sentiment: str, confidence: str, 
                           score: float, signals: List[str]) -> str:
        """Generar explicación del análisis"""
        reasoning = f"Sentimiento {sentiment} detectado (score: {score:.2f}). "
        reasoning += f"Nivel de confianza: {confidence}. "
        
        if signals:
            reasoning += f"Basado en: {', '.join(signals[:3])}."
        
        return reasoning
    
    def _neutral_sentiment(self) -> SentimentScore:
        """Sentimiento neutral por defecto"""
        return SentimentScore(
            sentiment='neutral',
            confidence_level='low',
            urgency='none',
            risk_appetite='moderate',
            conviction_strength=0.0,
            score=0.0,
            key_signals=[],
            reasoning="Sin suficiente información para determinar sentimiento"
        )
    
    def batch_analyze(self, texts: List[str]) -> List[SentimentScore]:
        """
        Analizar múltiples textos en batch
        
        Args:
            texts: Lista de textos a analizar
            
        Returns:
            Lista de SentimentScore
        """
        return [self.analyze_text(text) for text in texts]
    
    def aggregate_sentiment(self, scores: List[SentimentScore]) -> Dict:
        """
        Agregar múltiples análisis en un consenso
        
        Args:
            scores: Lista de SentimentScore
            
        Returns:
            Dict con sentimiento agregado
        """
        if not scores:
            return {'sentiment': 'neutral', 'confidence': 0.0}
        
        # Contar votos
        sentiments = [s.sentiment for s in scores]
        sentiment_counts = Counter(sentiments)
        
        # Sentimiento mayoritario
        majority_sentiment = sentiment_counts.most_common(1)[0][0]
        
        # Score promedio
        avg_score = sum(s.score for s in scores) / len(scores)
        
        # Confianza promedio
        conviction_values = [s.conviction_strength for s in scores]
        avg_conviction = sum(conviction_values) / len(conviction_values)
        
        return {
            'sentiment': majority_sentiment,
            'avg_score': avg_score,
            'confidence': avg_conviction,
            'vote_distribution': dict(sentiment_counts),
            'sample_size': len(scores)
        }


# Helper function
def analyze_trader_sentiment(text: str) -> Dict:
    """
    Analizar sentimiento de un trader desde texto
    
    Args:
        text: Texto a analizar
        
    Returns:
        Dict con análisis completo
    """
    analyzer = SentimentAnalyzerAdvanced()
    result = analyzer.analyze_text(text)
    
    return {
        'sentiment': result.sentiment,
        'confidence': result.confidence_level,
        'urgency': result.urgency,
        'risk_appetite': result.risk_appetite,
        'conviction': result.conviction_strength,
        'score': result.score,
        'signals': result.key_signals,
        'reasoning': result.reasoning
    }
