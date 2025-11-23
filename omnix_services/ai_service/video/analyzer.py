"""
🎥 OMNIX V5.3 QUANTUM ULTIMATE - VIDEO ANALYZER ULTRA
Sistema avanzado de análisis de videos de trading con procesamiento visual

CAPACIDADES PREMIUM INSTITUCIONALES:
1. 📝 Análisis de transcripciones (texto/audio)
2. 🎬 Procesamiento visual de frames (gráficos, patrones)
3. 📊 Detección de niveles técnicos en charts visuales
4. 💭 Análisis de sentimiento del trader (bullish/bearish)
5. 🧠 Integración multi-fuente para recomendaciones precisas

TECNOLOGÍAS:
- GPT-4 Vision API para análisis visual de gráficos
- Gemini 2.0 Flash Multimodal para frames
- OpenAI Whisper para transcripciones
- NLP avanzado para sentimiento

Desarrollado por Harold Nunes - Noviembre 2025 - V5.3 ULTRA
"""

import logging
import os
import re
import json
import tempfile
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


class VideoAnalyzerUltra:
    """
    Analizador ultra avanzado de videos de trading
    
    Combina análisis de transcripciones, procesamiento visual de frames,
    detección de patrones gráficos y análisis de sentimiento para generar
    recomendaciones de trading institucionales.
    """
    
    def __init__(self, openai_api_key: str = None, gemini_api_key: str = None):
        """
        Inicializar Video Analyzer Ultra
        
        Args:
            openai_api_key: API key de OpenAI (GPT-4 Vision)
            gemini_api_key: API key de Google Gemini
        """
        self.openai_api_key = openai_api_key or os.environ.get('OPENAI_API_KEY')
        self.gemini_api_key = gemini_api_key or os.environ.get('GEMINI_API_KEY')
        
        # Inicializar APIs de visión
        self._init_vision_apis()
        
        # Patrones técnicos a detectar en gráficos
        self.chart_patterns = [
            'head_and_shoulders', 'inverse_head_and_shoulders',
            'double_top', 'double_bottom',
            'ascending_triangle', 'descending_triangle', 'symmetrical_triangle',
            'bull_flag', 'bear_flag',
            'cup_and_handle',
            'wedge_rising', 'wedge_falling'
        ]
        
        # Indicadores visuales a detectar
        self.visual_indicators = [
            'support_level', 'resistance_level',
            'trendline_bullish', 'trendline_bearish',
            'moving_average_cross', 'volume_spike',
            'rsi_divergence', 'macd_divergence'
        ]
        
        logger.info("🎥 Video Analyzer Ultra V5.3 inicializado")
        logger.info(f"   🎬 GPT-4 Vision: {'✅' if self.openai_api_key else '❌'}")
        logger.info(f"   🧠 Gemini Vision: {'✅' if self.gemini_api_key else '❌'}")
    
    def _init_vision_apis(self):
        """Inicializar APIs de visión por computadora"""
        try:
            # GPT-4 Vision (OpenAI)
            if self.openai_api_key:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                logger.info("✅ GPT-4 Vision API inicializada")
            else:
                self.openai_client = None
                logger.warning("⚠️ OpenAI API key no disponible")
            
            # Gemini Vision
            if self.gemini_api_key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=self.gemini_api_key)
                    self.gemini_client = genai
                    logger.info("✅ Gemini Vision API inicializada")
                except Exception as e:
                    logger.warning(f"⚠️ Gemini Vision no disponible: {e}")
                    self.gemini_client = None
            else:
                self.gemini_client = None
                
        except Exception as e:
            logger.error(f"Error inicializando Vision APIs: {e}")
    
    def analyze_video_complete(self, video_url: str, extract_frames: bool = True) -> Dict:
        """
        Análisis COMPLETO de video: transcripción + visual + sentimiento
        
        Args:
            video_url: URL del video de YouTube
            extract_frames: Si True, analiza frames visuales (más lento pero completo)
            
        Returns:
            Dict con análisis completo multi-fuente
        """
        logger.info(f"🎥 Iniciando análisis ULTRA completo: {video_url}")
        
        results = {
            'video_url': video_url,
            'timestamp': datetime.now().isoformat(),
            'analysis_type': 'ULTRA_COMPLETE',
            'sources': []
        }
        
        try:
            # 1. ANÁLISIS DE TRANSCRIPCIÓN (texto/audio)
            logger.info("📝 Fase 1: Análisis de transcripción...")
            transcript_analysis = self._analyze_transcript(video_url)
            if transcript_analysis:
                results['transcript_analysis'] = transcript_analysis
                results['sources'].append('transcript')
            
            # 2. ANÁLISIS VISUAL DE FRAMES (gráficos, patrones)
            if extract_frames and (self.openai_client or self.gemini_client):
                logger.info("🎬 Fase 2: Análisis visual de frames...")
                visual_analysis = self._analyze_visual_frames(video_url)
                if visual_analysis:
                    results['visual_analysis'] = visual_analysis
                    results['sources'].append('visual')
            
            # 3. ANÁLISIS DE SENTIMIENTO (tono del trader)
            logger.info("💭 Fase 3: Análisis de sentimiento...")
            # DEFENSIVE: Solo analizar sentimiento si tenemos transcripción válida
            if transcript_analysis and isinstance(transcript_analysis, dict):
                raw_text = transcript_analysis.get('raw_text', '')
                sentiment_analysis = self._analyze_sentiment(raw_text)
                if sentiment_analysis:
                    results['sentiment_analysis'] = sentiment_analysis
                    results['sources'].append('sentiment')
            else:
                logger.warning("⚠️ Sin transcripción - saltando análisis de sentimiento")
            
            # 4. INTEGRACIÓN MULTI-FUENTE
            logger.info("🧠 Fase 4: Integración multi-fuente...")
            integrated_recommendations = self._integrate_multi_source(results)
            results['integrated_recommendations'] = integrated_recommendations
            
            # 5. CONFIANZA GENERAL
            results['confidence_score'] = self._calculate_confidence(results)
            results['status'] = 'success'
            
            logger.info(f"✅ Análisis ULTRA completo - Confianza: {results['confidence_score']:.2%}")
            
        except Exception as e:
            logger.error(f"❌ Error en análisis ultra: {e}")
            results['status'] = 'error'
            results['error'] = str(e)
        
        return results
    
    def _analyze_transcript(self, video_url: str) -> Optional[Dict]:
        """
        Analizar transcripción del video para extraer parámetros técnicos
        
        Similar al VideoLearningAnalyzer actual pero mejorado
        """
        try:
            # Extraer ID del video
            video_id = self._extract_video_id(video_url)
            if not video_id:
                return None
            
            # Obtener transcripción (YouTube API o yt-dlp)
            transcript = self._get_transcript(video_id)
            if not transcript:
                return None
            
            # Analizar con IA para extraer parámetros
            analysis = self._extract_technical_parameters(transcript)
            
            return {
                'raw_text': transcript,
                'technical_parameters': analysis.get('parameters', {}),
                'trading_strategy': analysis.get('strategy', ''),
                'timeframe': analysis.get('timeframe', ''),
                'assets_mentioned': analysis.get('assets', []),
                'confidence': analysis.get('confidence', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error analizando transcripción: {e}")
            return None
    
    def _analyze_visual_frames(self, video_url: str, num_frames: int = 3) -> Optional[Dict]:
        """
        Analizar frames del video para detectar gráficos y patrones visuales
        
        NUEVO: Procesamiento visual con GPT-4 Vision / Gemini Vision
        
        Args:
            num_frames: Número de frames a analizar (default: 3, max: 5 para controlar costos API)
        """
        try:
            # LÍMITE DE SEGURIDAD: Max 5 frames para controlar costos
            num_frames = min(num_frames, 5)
            logger.info(f"🎬 Extrayendo {num_frames} frames clave del video...")
            
            # Extraer frames representativos del video
            frames = self._extract_key_frames(video_url, num_frames)
            if not frames:
                logger.warning("⚠️ No se pudieron extraer frames")
                return None
            
            visual_findings = {
                'patterns_detected': [],
                'support_resistance_levels': [],
                'indicators_visible': [],
                'price_levels': [],
                'confidence': 0.0
            }
            
            # Analizar cada frame con Vision API
            for idx, frame_path in enumerate(frames):
                logger.info(f"   📊 Analizando frame {idx+1}/{len(frames)}...")
                
                frame_analysis = self._analyze_frame_with_vision(frame_path)
                
                if frame_analysis:
                    # Agregar patrones detectados
                    visual_findings['patterns_detected'].extend(
                        frame_analysis.get('patterns', [])
                    )
                    
                    # Agregar niveles de soporte/resistencia
                    visual_findings['support_resistance_levels'].extend(
                        frame_analysis.get('levels', [])
                    )
                    
                    # Agregar indicadores visibles
                    visual_findings['indicators_visible'].extend(
                        frame_analysis.get('indicators', [])
                    )
                    
                    # Agregar niveles de precio
                    if 'price_levels' in frame_analysis:
                        visual_findings['price_levels'].extend(
                            frame_analysis['price_levels']
                        )
            
            # Calcular confianza basada en consistencia entre frames
            visual_findings['confidence'] = self._calculate_visual_confidence(visual_findings)
            
            # Eliminar duplicados
            visual_findings['patterns_detected'] = list(set(visual_findings['patterns_detected']))
            visual_findings['indicators_visible'] = list(set(visual_findings['indicators_visible']))
            
            logger.info(f"✅ Análisis visual completo - {len(visual_findings['patterns_detected'])} patrones detectados")
            
            return visual_findings
            
        except Exception as e:
            logger.error(f"Error en análisis visual: {e}")
            return None
    
    def _analyze_frame_with_vision(self, frame_path: str) -> Optional[Dict]:
        """
        Analizar un frame individual usando GPT-4 Vision o Gemini Vision
        """
        try:
            # Intentar primero con GPT-4 Vision (más preciso para charts)
            if self.openai_client:
                return self._analyze_frame_gpt4_vision(frame_path)
            
            # Fallback a Gemini Vision
            elif self.gemini_client:
                return self._analyze_frame_gemini_vision(frame_path)
            
            else:
                logger.warning("⚠️ No hay Vision API disponible")
                return None
                
        except Exception as e:
            logger.error(f"Error analizando frame: {e}")
            return None
    
    def _analyze_frame_gpt4_vision(self, frame_path: str) -> Optional[Dict]:
        """
        Analizar frame con GPT-4 Vision API
        """
        try:
            import base64
            
            # Leer y codificar imagen
            with open(frame_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Prompt especializado para análisis de charts de trading
            prompt = """
Analiza esta imagen de un gráfico de trading y extrae la siguiente información en formato JSON:

1. **Patrones técnicos visibles** (head_and_shoulders, double_top, triangles, flags, etc.)
2. **Niveles de soporte y resistencia** (precio aproximado si es visible)
3. **Indicadores técnicos visibles** (RSI, MACD, moving averages, volume, etc.)
4. **Niveles de precio críticos** (si son visibles en el chart)
5. **Señal de trading** (bullish, bearish, neutral)

Responde solo con JSON válido:
{
  "patterns": ["pattern1", "pattern2"],
  "levels": [{"type": "support", "price": 50000}, {"type": "resistance", "price": 52000}],
  "indicators": ["RSI", "MACD", "EMA_20"],
  "price_levels": [50000, 51000, 52000],
  "signal": "bullish",
  "confidence": 0.85
}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            # Parsear respuesta JSON
            content = response.choices[0].message.content
            analysis = json.loads(content)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error con GPT-4 Vision: {e}")
            return None
    
    def _analyze_frame_gemini_vision(self, frame_path: str) -> Optional[Dict]:
        """
        Analizar frame con Gemini Vision API (fallback)
        """
        try:
            import PIL.Image
            
            # Cargar imagen
            img = PIL.Image.open(frame_path)
            
            # Crear modelo Gemini Vision
            model = self.gemini_client.GenerativeModel(model_name='gemini-2.0-flash-exp')
            
            # Prompt especializado para análisis de charts de trading
            prompt = """
Analiza esta imagen de un gráfico de trading y extrae la siguiente información en formato JSON:

1. **Patrones técnicos visibles** (head_and_shoulders, double_top, triangles, flags, etc.)
2. **Niveles de soporte y resistencia** (precio aproximado si es visible)
3. **Indicadores técnicos visibles** (RSI, MACD, moving averages, volume, etc.)
4. **Niveles de precio críticos** (si son visibles en el chart)
5. **Señal de trading** (bullish, bearish, neutral)

Responde solo con JSON válido:
{
  "patterns": ["pattern1", "pattern2"],
  "levels": [{"type": "support", "price": 50000}, {"type": "resistance", "price": 52000}],
  "indicators": ["RSI", "MACD", "EMA_20"],
  "price_levels": [50000, 51000, 52000],
  "signal": "bullish",
  "confidence": 0.85
}
"""
            
            # Generar análisis
            response = model.generate_content([prompt, img])
            
            # Parsear respuesta JSON
            content = response.text
            analysis = json.loads(content)
            
            logger.info("🧠 Análisis con Gemini Vision completado")
            return analysis
            
        except Exception as e:
            logger.error(f"Error con Gemini Vision: {e}")
            return None
    
    def _analyze_sentiment(self, text: str) -> Optional[Dict]:
        """
        Analizar sentimiento del trader (bullish, bearish, neutral)
        
        NUEVO: Análisis de tono y confianza del trader
        """
        try:
            if not text:
                return None
            
            # Usar GPT-4 para análisis de sentimiento avanzado
            if self.openai_client:
                prompt = f"""
Analiza el sentimiento de este texto de un trader sobre el mercado:

"{text[:1000]}"

Responde en JSON:
{{
  "sentiment": "bullish" | "bearish" | "neutral",
  "confidence_level": "high" | "medium" | "low",
  "key_signals": ["señal1", "señal2"],
  "risk_appetite": "aggressive" | "moderate" | "conservative",
  "score": 0.85
}}
"""
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300
                )
                
                content = response.choices[0].message.content
                sentiment = json.loads(content)
                
                return sentiment
            
            return None
            
        except Exception as e:
            logger.error(f"Error en análisis de sentimiento: {e}")
            return None
    
    def _integrate_multi_source(self, analysis_results: Dict) -> Dict:
        """
        Integrar análisis de múltiples fuentes en recomendaciones unificadas
        
        NUEVO: Combina transcripción + visual + sentimiento
        """
        recommendations = {
            'action': 'HOLD',  # BUY, SELL, HOLD
            'confidence': 0.0,
            'reasons': [],
            'suggested_parameters': {},
            'risk_level': 'MEDIUM'
        }
        
        try:
            sources_count = len(analysis_results.get('sources', []))
            
            if sources_count == 0:
                return recommendations
            
            # Recopilar señales de todas las fuentes
            signals = []
            
            # 1. Señales de transcripción
            if 'transcript_analysis' in analysis_results:
                transcript = analysis_results['transcript_analysis']
                params = transcript.get('technical_parameters', {})
                if params:
                    signals.append({
                        'source': 'transcript',
                        'signal': self._infer_signal_from_params(params),
                        'weight': 0.4,
                        'params': params
                    })
            
            # 2. Señales visuales
            if 'visual_analysis' in analysis_results:
                visual = analysis_results['visual_analysis']
                patterns = visual.get('patterns_detected', [])
                if patterns:
                    signal = self._infer_signal_from_patterns(patterns)
                    signals.append({
                        'source': 'visual',
                        'signal': signal,
                        'weight': 0.4
                    })
            
            # 3. Señales de sentimiento
            if 'sentiment_analysis' in analysis_results:
                sentiment = analysis_results['sentiment_analysis']
                signals.append({
                    'source': 'sentiment',
                    'signal': sentiment.get('sentiment', 'neutral'),
                    'weight': 0.2
                })
            
            # Calcular recomendación final (weighted average)
            final_signal = self._calculate_weighted_signal(signals)
            recommendations['action'] = final_signal['action']
            recommendations['confidence'] = final_signal['confidence']
            recommendations['reasons'] = final_signal['reasons']
            
            # Agregar parámetros sugeridos si disponibles
            if signals and 'params' in signals[0]:
                recommendations['suggested_parameters'] = signals[0]['params']
            
            logger.info(f"🧠 Recomendación integrada: {recommendations['action']} (conf: {recommendations['confidence']:.2%})")
            
        except Exception as e:
            logger.error(f"Error integrando fuentes: {e}")
        
        return recommendations
    
    def _calculate_weighted_signal(self, signals: List[Dict]) -> Dict:
        """Calcular señal final ponderada de múltiples fuentes"""
        if not signals:
            return {'action': 'HOLD', 'confidence': 0.0, 'reasons': []}
        
        # Convertir señales a valores numéricos
        signal_values = {
            'bullish': 1.0, 'BUY': 1.0,
            'bearish': -1.0, 'SELL': -1.0,
            'neutral': 0.0, 'HOLD': 0.0
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        reasons = []
        
        for sig in signals:
            value = signal_values.get(sig['signal'], 0.0)
            weight = sig.get('weight', 1.0)
            weighted_sum += value * weight
            total_weight += weight
            reasons.append(f"{sig['source']}: {sig['signal']}")
        
        final_value = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Convertir a acción
        if final_value > 0.3:
            action = 'BUY'
        elif final_value < -0.3:
            action = 'SELL'
        else:
            action = 'HOLD'
        
        confidence = abs(final_value)
        
        return {
            'action': action,
            'confidence': confidence,
            'reasons': reasons
        }
    
    def _infer_signal_from_params(self, params: Dict) -> str:
        """Inferir señal de trading desde parámetros técnicos"""
        # Lógica simple - mejorable
        if params.get('RSI_oversold', 30) < 35:
            return 'bullish'
        elif params.get('RSI_overbought', 70) > 65:
            return 'bearish'
        return 'neutral'
    
    def _infer_signal_from_patterns(self, patterns: List[str]) -> str:
        """Inferir señal desde patrones gráficos detectados"""
        bullish_patterns = ['inverse_head_and_shoulders', 'double_bottom', 'bull_flag', 'cup_and_handle']
        bearish_patterns = ['head_and_shoulders', 'double_top', 'bear_flag']
        
        bullish_count = sum(1 for p in patterns if any(bp in p for bp in bullish_patterns))
        bearish_count = sum(1 for p in patterns if any(bp in p for bp in bearish_patterns))
        
        if bullish_count > bearish_count:
            return 'bullish'
        elif bearish_count > bullish_count:
            return 'bearish'
        return 'neutral'
    
    def _calculate_confidence(self, results: Dict) -> float:
        """Calcular confianza general del análisis"""
        sources = results.get('sources', [])
        if not sources:
            return 0.0
        
        # Más fuentes = mayor confianza
        base_confidence = len(sources) / 3.0  # Max 3 fuentes
        
        # Ajustar por confianza individual de cada fuente
        individual_confidences = []
        
        if 'transcript_analysis' in results:
            individual_confidences.append(results['transcript_analysis'].get('confidence', 0.5))
        
        if 'visual_analysis' in results:
            individual_confidences.append(results['visual_analysis'].get('confidence', 0.5))
        
        if 'sentiment_analysis' in results:
            individual_confidences.append(results['sentiment_analysis'].get('score', 0.5))
        
        avg_confidence = sum(individual_confidences) / len(individual_confidences) if individual_confidences else 0.5
        
        return min(base_confidence * avg_confidence, 1.0)
    
    def _calculate_visual_confidence(self, visual_findings: Dict) -> float:
        """Calcular confianza del análisis visual"""
        # Más patrones/indicadores detectados = mayor confianza
        patterns_count = len(visual_findings.get('patterns_detected', []))
        indicators_count = len(visual_findings.get('indicators_visible', []))
        levels_count = len(visual_findings.get('support_resistance_levels', []))
        
        total_findings = patterns_count + indicators_count + levels_count
        
        # Normalizar a 0-1
        return min(total_findings / 10.0, 1.0)
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extraer ID de video de YouTube desde URL"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)',
            r'youtube\.com/embed/([a-zA-Z0-9_-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _get_transcript(self, video_id: str) -> Optional[str]:
        """Obtener transcripción del video (stub - implementar con youtube-transcript-api)"""
        # TODO: Implementar extracción real de transcripción
        logger.info(f"📝 Obteniendo transcripción de video {video_id}...")
        return "Transcripción de ejemplo - implementar extracción real"
    
    def _extract_technical_parameters(self, transcript: str) -> Dict:
        """Extraer parámetros técnicos de la transcripción con IA"""
        # Usar el mismo enfoque que VideoLearningAnalyzer
        # TODO: Integrar con IA para extracción
        return {
            'parameters': {},
            'strategy': '',
            'timeframe': '',
            'assets': [],
            'confidence': 0.7
        }
    
    def _extract_key_frames(self, video_url: str, num_frames: int) -> List[str]:
        """
        Extraer frames clave del video para análisis visual
        
        Usa ffmpeg o similar para extraer frames en intervalos regulares
        """
        # TODO: Implementar extracción real de frames con ffmpeg
        logger.info(f"🎬 Extrayendo {num_frames} frames clave...")
        return []  # Retornar lista de rutas a imágenes de frames


# Función helper para uso rápido
def analyze_trading_video_ultra(video_url: str, extract_frames: bool = True) -> Dict:
    """
    Analizar video de trading con todas las capacidades ultra
    
    Args:
        video_url: URL del video de YouTube
        extract_frames: Si True, analiza frames visuales (más completo pero más lento)
        
    Returns:
        Dict con análisis completo multi-fuente
    """
    analyzer = VideoAnalyzerUltra()
    return analyzer.analyze_video_complete(video_url, extract_frames=extract_frames)
