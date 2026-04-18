"""
⚡ OMNIX INSTITUTIONAL+ - VIDEO LEARNING ANALYZER
Sistema de análisis inteligente de videos de trading
Extrae insights técnicos y genera propuestas de ajuste automáticas
Desarrollado por Harold Nunes - OMNIX INSTITUTIONAL+
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class VideoLearningAnalyzer:
    """
    Analizador inteligente de videos de trading
    
    Extrae automáticamente:
    - Patrones de velas mencionados
    - Niveles de RSI recomendados
    - Configuraciones de EMA/SMA
    - Estrategias de entrada/salida
    - Configuraciones de MACD
    - Niveles de soporte/resistencia
    """
    
    def __init__(self, ai_service=None):
        self.ai_service = ai_service
        
        # Patrones de extracción de insights técnicos
        self.patterns = {
            'rsi': {
                'oversold': r'rsi\s*(?:below|bajo|menor|<)\s*(\d+)',
                'overbought': r'rsi\s*(?:above|sobre|mayor|>)\s*(\d+)',
                'general': r'rsi\s*(?:de|of|at|en)\s*(\d+)'
            },
            'ema': {
                'fast': r'ema\s*(?:rápido|fast|corto|short)\s*(?:de|of)?\s*(\d+)',
                'medium': r'ema\s*(?:medio|medium)\s*(?:de|of)?\s*(\d+)',
                'slow': r'ema\s*(?:lento|slow|largo|long)\s*(?:de|of)?\s*(\d+)',
                'general': r'ema\s*(\d+)'
            },
            'sma': {
                'general': r'sma\s*(\d+)',
                'moving_average': r'media\s*móvil\s*(?:de)?\s*(\d+)'
            },
            'macd': {
                'fast': r'macd\s*(?:rápido|fast)\s*(?:de|of)?\s*(\d+)',
                'slow': r'macd\s*(?:lento|slow)\s*(?:de|of)?\s*(\d+)',
                'signal': r'(?:señal|signal)\s*(?:de|of)?\s*(\d+)'
            }
        }
        
        # Keywords que indican insights importantes
        self.insight_keywords = [
            'mejor', 'mejor', 'recomiendo', 'funciona', 'efectivo',
            'óptimo', 'ideal', 'perfecto', 'usar', 'aplicar',
            'configurar', 'ajustar', 'cambiar', 'modificar',
            'works', 'better', 'recommend', 'optimal', 'ideal'
        ]
        
        logger.info("🎓 Video Learning Analyzer inicializado")
    
    def analyze_video(
        self,
        video_url: str,
        ai_response: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analizar video y extraer insights técnicos
        
        Args:
            video_url: URL del video de YouTube
            ai_response: Respuesta de la IA que ya analizó el video (opcional)
            
        Returns:
            Diccionario con insights y propuestas de ajuste
        """
        logger.info(f"🎬 Analizando video: {video_url}")
        
        insights = {
            'video_url': video_url,
            'timestamp': datetime.now().isoformat(),
            'raw_insights': [],
            'technical_parameters': {},
            'confidence_score': 0.0,
            'recommendations': []
        }
        
        # Si tenemos respuesta de IA, extraer insights
        if ai_response:
            insights = self._extract_insights_from_text(ai_response, insights)
        
        # Si no tenemos respuesta de IA, solicitarla
        elif self.ai_service:
            logger.info("🤖 Solicitando análisis de IA del video...")
            ai_analysis = self._request_ai_analysis(video_url)
            if ai_analysis:
                insights = self._extract_insights_from_text(ai_analysis, insights)
        
        # Generar propuestas de ajuste basadas en insights
        insights['adjustment_proposals'] = self._generate_adjustment_proposals(
            insights['technical_parameters']
        )
        
        logger.info(f"✅ Análisis completado: {len(insights['adjustment_proposals'])} propuestas")
        
        return insights
    
    def _extract_insights_from_text(
        self,
        text: str,
        insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extraer insights técnicos del texto de análisis"""
        text_lower = text.lower()
        
        # Extraer parámetros RSI
        rsi_insights = self._extract_rsi_parameters(text_lower)
        if rsi_insights:
            insights['technical_parameters']['rsi'] = rsi_insights
            insights['raw_insights'].append(f"RSI: {rsi_insights}")
        
        # Extraer parámetros EMA
        ema_insights = self._extract_ema_parameters(text_lower)
        if ema_insights:
            insights['technical_parameters']['ema'] = ema_insights
            insights['raw_insights'].append(f"EMA: {ema_insights}")
        
        # Extraer parámetros MACD
        macd_insights = self._extract_macd_parameters(text_lower)
        if macd_insights:
            insights['technical_parameters']['macd'] = macd_insights
            insights['raw_insights'].append(f"MACD: {macd_insights}")
        
        # Calcular confidence score basado en keywords
        confidence = self._calculate_confidence(text_lower)
        insights['confidence_score'] = confidence
        
        return insights
    
    def _extract_rsi_parameters(self, text: str) -> Optional[Dict[str, float]]:
        """Extraer parámetros de RSI del texto"""
        rsi_params = {}
        
        # Buscar RSI oversold
        oversold_match = re.search(self.patterns['rsi']['oversold'], text, re.IGNORECASE)
        if oversold_match:
            value = int(oversold_match.group(1))
            if 10 <= value <= 30:  # Validar rango
                rsi_params['oversold'] = float(value)
        
        # Buscar RSI overbought
        overbought_match = re.search(self.patterns['rsi']['overbought'], text, re.IGNORECASE)
        if overbought_match:
            value = int(overbought_match.group(1))
            if 70 <= value <= 90:  # Validar rango
                rsi_params['overbought'] = float(value)
        
        return rsi_params if rsi_params else None
    
    def _extract_ema_parameters(self, text: str) -> Optional[Dict[str, float]]:
        """Extraer parámetros de EMA del texto"""
        ema_params = {}
        
        # Buscar EMA rápido
        fast_match = re.search(self.patterns['ema']['fast'], text, re.IGNORECASE)
        if fast_match:
            value = int(fast_match.group(1))
            if 5 <= value <= 12:
                ema_params['fast'] = float(value)
        
        # Buscar EMA medio
        medium_match = re.search(self.patterns['ema']['medium'], text, re.IGNORECASE)
        if medium_match:
            value = int(medium_match.group(1))
            if 15 <= value <= 30:
                ema_params['medium'] = float(value)
        
        # Buscar EMA lento
        slow_match = re.search(self.patterns['ema']['slow'], text, re.IGNORECASE)
        if slow_match:
            value = int(slow_match.group(1))
            if 40 <= value <= 70:
                ema_params['slow'] = float(value)
        
        # Buscar menciones generales de EMA
        general_matches = re.findall(self.patterns['ema']['general'], text, re.IGNORECASE)
        if general_matches:
            for match in general_matches:
                value = int(match)
                # Clasificar según rango
                if 5 <= value <= 12 and 'fast' not in ema_params:
                    ema_params['fast'] = float(value)
                elif 15 <= value <= 30 and 'medium' not in ema_params:
                    ema_params['medium'] = float(value)
                elif 40 <= value <= 70 and 'slow' not in ema_params:
                    ema_params['slow'] = float(value)
        
        return ema_params if ema_params else None
    
    def _extract_macd_parameters(self, text: str) -> Optional[Dict[str, float]]:
        """Extraer parámetros de MACD del texto"""
        macd_params = {}
        
        # MACD típicamente es 12, 26, 9
        fast_match = re.search(self.patterns['macd']['fast'], text, re.IGNORECASE)
        if fast_match:
            value = int(fast_match.group(1))
            if 8 <= value <= 15:
                macd_params['fast'] = float(value)
        
        slow_match = re.search(self.patterns['macd']['slow'], text, re.IGNORECASE)
        if slow_match:
            value = int(slow_match.group(1))
            if 20 <= value <= 35:
                macd_params['slow'] = float(value)
        
        signal_match = re.search(self.patterns['macd']['signal'], text, re.IGNORECASE)
        if signal_match:
            value = int(signal_match.group(1))
            if 5 <= value <= 15:
                macd_params['signal'] = float(value)
        
        return macd_params if macd_params else None
    
    def _calculate_confidence(self, text: str) -> float:
        """Calcular confidence score basado en keywords"""
        keyword_count = 0
        for keyword in self.insight_keywords:
            keyword_count += text.count(keyword)
        
        # Normalizar entre 0 y 1
        confidence = min(1.0, keyword_count / 10.0)
        
        return round(confidence, 2)
    
    def _generate_adjustment_proposals(
        self,
        technical_params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generar propuestas de ajuste basadas en parámetros técnicos
        
        Args:
            technical_params: Parámetros técnicos extraídos del video
            
        Returns:
            Lista de propuestas de ajuste para auto_learning_system
        """
        proposals = []
        
        # Propuestas RSI
        if 'rsi' in technical_params:
            rsi = technical_params['rsi']
            
            if 'oversold' in rsi:
                proposals.append({
                    'param_name': 'rsi_threshold_oversold',
                    'new_value': rsi['oversold'],
                    'reason': f'Video recomienda RSI oversold en {rsi["oversold"]}',
                    'confidence': 0.8
                })
            
            if 'overbought' in rsi:
                proposals.append({
                    'param_name': 'rsi_threshold_overbought',
                    'new_value': rsi['overbought'],
                    'reason': f'Video recomienda RSI overbought en {rsi["overbought"]}',
                    'confidence': 0.8
                })
        
        # Propuestas EMA
        if 'ema' in technical_params:
            ema = technical_params['ema']
            
            if 'fast' in ema:
                proposals.append({
                    'param_name': 'ema_fast_period',
                    'new_value': ema['fast'],
                    'reason': f'Video sugiere EMA rápido de {int(ema["fast"])} períodos',
                    'confidence': 0.75
                })
            
            if 'medium' in ema:
                proposals.append({
                    'param_name': 'ema_medium_period',
                    'new_value': ema['medium'],
                    'reason': f'Video sugiere EMA medio de {int(ema["medium"])} períodos',
                    'confidence': 0.75
                })
            
            if 'slow' in ema:
                proposals.append({
                    'param_name': 'ema_slow_period',
                    'new_value': ema['slow'],
                    'reason': f'Video sugiere EMA lento de {int(ema["slow"])} períodos',
                    'confidence': 0.75
                })
        
        return proposals
    
    def _request_ai_analysis(self, video_url: str) -> Optional[str]:
        """Solicitar análisis del video a la IA"""
        # Aquí se conectaría con Gemini/GPT-4o
        # Por ahora es placeholder
        logger.warning("⚠️ AI service no configurado para análisis directo")
        return None


def get_video_learning_analyzer(ai_service=None) -> VideoLearningAnalyzer:
    """Factory para obtener instancia del analizador"""
    return VideoLearningAnalyzer(ai_service=ai_service)


if __name__ == "__main__":
    # Test básico
    logging.basicConfig(level=logging.INFO)
    
    analyzer = VideoLearningAnalyzer()
    
    # Simular respuesta de IA
    test_response = """
    En este video, el trader recomienda usar RSI con nivel de sobreventa 
    en 15 y sobrecompra en 85. También sugiere usar EMA rápido de 9 períodos,
    EMA medio de 21 períodos y EMA lento de 55 períodos para mejor detección
    de tendencias. El MACD funciona mejor con 12, 26, 9.
    """
    
    result = analyzer.analyze_video(
        "https://youtube.com/watch?v=test",
        ai_response=test_response
    )
    
    print("\n📊 RESULTADO DEL ANÁLISIS:")
    print(f"Insights extraídos: {result['raw_insights']}")
    print(f"Parámetros técnicos: {result['technical_parameters']}")
    print(f"Confidence: {result['confidence_score']}")
    print(f"\n💡 Propuestas ({len(result['adjustment_proposals'])}):")
    for proposal in result['adjustment_proposals']:
        print(f"  - {proposal['param_name']}: {proposal['new_value']}")
        print(f"    Razón: {proposal['reason']}")
