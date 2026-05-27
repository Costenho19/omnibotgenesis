"""
🎥 OMNIX INSTITUTIONAL+ - VIDEO ANALYZER ULTRA
Sistema avanzado de análisis de videos de trading con procesamiento visual

CAPACIDADES PREMIUM INSTITUCIONALES:
1. 📝 Análisis de transcripciones (texto/audio)
2. 🎬 Procesamiento visual de frames (gráficos, patrones)
3. 📊 Detección de niveles técnicos en charts visuales
4. 💭 Análisis de sentimiento del trader (bullish/bearish)
5. 🧠 Integración multi-fuente para recomendaciones precisas

TECNOLOGÍAS:
- GPT-4 Vision API para análisis visual de gráficos
- Gemini 2.0 Flash Multimodal para frames (NUEVO SDK google-genai)
- OpenAI Whisper para transcripciones
- NLP avanzado para sentimiento

Desarrollado por Harold Nunes - OMNIX INSTITUTIONAL+
"""

import logging
import os
import re
import json
import tempfile
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

logger = logging.getLogger(__name__)


def parse_vision_json(content: Optional[str], source: str = "AI") -> Optional[Dict[str, Any]]:
    """
    Parse JSON response from Vision APIs, handling markdown code blocks.
    
    Args:
        content: Raw response content from AI model
        source: Name of the source for logging (e.g., "GPT-4", "Gemini")
        
    Returns:
        Parsed dict or None if parsing fails
    """
    if not content:
        return None
    
    try:
        clean_content = content.strip()
        if clean_content.startswith('```json'):
            clean_content = clean_content[7:]
        if clean_content.startswith('```'):
            clean_content = clean_content[3:]
        if clean_content.endswith('```'):
            clean_content = clean_content[:-3]
        
        return json.loads(clean_content.strip())
    except json.JSONDecodeError as je:
        logger.warning(f"⚠️ Error parseando JSON de {source}: {je}")
        return None


CHART_ANALYSIS_PROMPT = """
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

from omnix_config import VERSION_BANNER


class VideoAnalyzerUltra:
    """
    Analizador ultra avanzado de videos de trading
    
    Combina análisis de transcripciones, procesamiento visual de frames,
    detección de patrones gráficos y análisis de sentimiento para generar
    recomendaciones de trading institucionales.
    """
    
    def __init__(
        self, 
        openai_api_key: Optional[str] = None, 
        gemini_api_key: Optional[str] = None, 
        database_service: Optional[Any] = None
    ):
        """
        Inicializar Video Analyzer Ultra
        
        Args:
            openai_api_key: API key de OpenAI (GPT-4 Vision)
            gemini_api_key: API key de Google Gemini
            database_service: Servicio de base de datos para caché de transcripciones
        """
        self.openai_api_key = openai_api_key or os.environ.get('OPENAI_API_KEY')
        self.gemini_api_key = gemini_api_key or os.environ.get('GEMINI_API_KEY')
        self.database_service = database_service
        
        self.openai_client: Optional[Any] = None
        self.gemini_client: Optional[Any] = None
        self._gemini_sdk: Optional[str] = None
        
        self._init_vision_apis()
        
        self.chart_patterns = [
            'head_and_shoulders', 'inverse_head_and_shoulders',
            'double_top', 'double_bottom',
            'ascending_triangle', 'descending_triangle', 'symmetrical_triangle',
            'bull_flag', 'bear_flag',
            'cup_and_handle',
            'wedge_rising', 'wedge_falling'
        ]
        
        self.visual_indicators = [
            'support_level', 'resistance_level',
            'trendline_bullish', 'trendline_bearish',
            'moving_average_cross', 'volume_spike',
            'rsi_divergence', 'macd_divergence'
        ]
        
        logger.info(f"🎥 [{VERSION_BANNER}] Video Analyzer Ultra inicializado")
        logger.info(f"   🎬 GPT-4 Vision: {'✅' if self.openai_client else '❌'}")
        logger.info(f"   🧠 Gemini Vision: {'✅' if self.gemini_client else '❌'}")
    
    def _init_vision_apis(self) -> None:
        """Inicializar APIs de visión por computadora"""
        try:
            if self.openai_api_key:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                logger.info("✅ GPT-4 Vision API inicializada")
            else:
                self.openai_client = None
                logger.warning("⚠️ OpenAI API key no disponible")
            
            if self.gemini_api_key:
                try:
                    from google import genai
                    self.gemini_client = genai.Client(api_key=self.gemini_api_key)
                    self._gemini_sdk = 'new'
                    logger.info("✅ Gemini Vision API inicializada (NUEVO SDK google-genai)")
                except ImportError:
                    try:
                        import google.generativeai as genai_legacy
                        genai_legacy.configure(api_key=self.gemini_api_key)  # type: ignore[attr-defined]
                        self.gemini_client = genai_legacy
                        self._gemini_sdk = 'legacy'
                        logger.info("✅ Gemini Vision API inicializada (SDK legacy)")
                    except Exception as legacy_err:
                        logger.warning(f"⚠️ Gemini Vision no disponible: {legacy_err}")
                        self.gemini_client = None
                        self._gemini_sdk = None
            else:
                self.gemini_client = None
                self._gemini_sdk = None
                
        except Exception as e:
            logger.error(f"Error inicializando Vision APIs: {e}")
    
    def analyze_video_complete(self, video_url: str, extract_frames: bool = True) -> Dict[str, Any]:
        """
        Análisis COMPLETO de video: transcripción + visual + sentimiento
        
        Args:
            video_url: URL del video de YouTube
            extract_frames: Si True, analiza frames visuales (más lento pero completo)
            
        Returns:
            Dict con análisis completo multi-fuente
        """
        logger.info(f"🎥 [{VERSION_BANNER}] Iniciando análisis ULTRA completo: {video_url}")
        
        results: Dict[str, Any] = {
            'video_url': video_url,
            'timestamp': datetime.now().isoformat(),
            'analysis_type': 'ULTRA_COMPLETE',
            'sources': []
        }
        
        try:
            logger.info("📝 Fase 1: Análisis de transcripción...")
            transcript_analysis = self._analyze_transcript(video_url)
            if transcript_analysis:
                results['transcript_analysis'] = transcript_analysis
                results['sources'].append('transcript')
            
            if extract_frames and (self.openai_client or self.gemini_client):
                logger.info("🎬 Fase 2: Análisis visual de frames...")
                visual_analysis = self._analyze_visual_frames(video_url)
                if visual_analysis:
                    results['visual_analysis'] = visual_analysis
                    results['sources'].append('visual')
            
            logger.info("💭 Fase 3: Análisis de sentimiento...")
            if transcript_analysis and isinstance(transcript_analysis, dict):
                raw_text = transcript_analysis.get('raw_text', '')
                if raw_text:
                    sentiment_analysis = self._analyze_sentiment(raw_text)
                    if sentiment_analysis:
                        results['sentiment_analysis'] = sentiment_analysis
                        results['sources'].append('sentiment')
            else:
                logger.warning("⚠️ Sin transcripción - saltando análisis de sentimiento")
            
            logger.info("🧠 Fase 4: Integración multi-fuente...")
            integrated_recommendations = self._integrate_multi_source(results)
            results['integrated_recommendations'] = integrated_recommendations
            
            results['confidence_score'] = self._calculate_confidence(results)
            results['status'] = 'success'
            
            logger.info(f"✅ Análisis ULTRA completo - Confianza: {results['confidence_score']:.2%}")
            
        except Exception as e:
            logger.error(f"❌ Error en análisis ultra: {e}")
            results['status'] = 'error'
            results['error'] = str(e)
        
        return results
    
    def _analyze_transcript(self, video_url: str) -> Optional[Dict[str, Any]]:
        """Analizar transcripción del video para extraer parámetros técnicos"""
        try:
            video_id = self._extract_video_id(video_url)
            if not video_id:
                return None
            
            transcript = self._get_transcript(video_id)
            if not transcript:
                return None
            
            analysis = self._extract_technical_parameters(transcript)
            
            return {
                'raw_text': transcript,
                'technical_parameters': analysis.get('indicators', {}),
                'trading_strategy': analysis.get('strategy', ''),
                'strategy': analysis.get('strategy', ''),
                'timeframe': analysis.get('timeframe', ''),
                'assets_mentioned': analysis.get('assets', []),
                'assets': analysis.get('assets', []),
                'indicators': analysis.get('indicators', {}),
                'levels': analysis.get('levels', {}),
                'entry_exit': analysis.get('entry_exit', {}),
                'risk_management': analysis.get('risk_management', {}),
                'key_insights': analysis.get('key_insights', []),
                'summary': analysis.get('summary', ''),
                'confidence': analysis.get('confidence', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error analizando transcripción: {e}")
            return None
    
    def _analyze_visual_frames(self, video_url: str, num_frames: int = 3) -> Optional[Dict[str, Any]]:
        """
        Analizar frames del video para detectar gráficos y patrones visuales
        
        Args:
            num_frames: Número de frames a analizar (default: 3, max: 5 para controlar costos API)
        """
        try:
            num_frames = min(num_frames, 5)
            logger.info(f"🎬 Extrayendo {num_frames} frames clave del video...")
            
            frames = self._extract_key_frames(video_url, num_frames)
            if not frames:
                logger.warning("⚠️ No se pudieron extraer frames")
                return None
            
            visual_findings: Dict[str, Any] = {
                'patterns_detected': [],
                'support_resistance_levels': [],
                'indicators_visible': [],
                'price_levels': [],
                'confidence': 0.0
            }
            
            for idx, frame_path in enumerate(frames):
                logger.info(f"   📊 Analizando frame {idx+1}/{len(frames)}...")
                
                frame_analysis = self._analyze_frame_with_vision(frame_path)
                
                if frame_analysis:
                    visual_findings['patterns_detected'].extend(
                        frame_analysis.get('patterns', [])
                    )
                    visual_findings['support_resistance_levels'].extend(
                        frame_analysis.get('levels', [])
                    )
                    visual_findings['indicators_visible'].extend(
                        frame_analysis.get('indicators', [])
                    )
                    if 'price_levels' in frame_analysis:
                        visual_findings['price_levels'].extend(
                            frame_analysis['price_levels']
                        )
            
            visual_findings['confidence'] = self._calculate_visual_confidence(visual_findings)
            visual_findings['patterns_detected'] = list(set(visual_findings['patterns_detected']))
            visual_findings['indicators_visible'] = list(set(visual_findings['indicators_visible']))
            
            logger.info(f"✅ Análisis visual completo - {len(visual_findings['patterns_detected'])} patrones detectados")
            
            return visual_findings
            
        except Exception as e:
            logger.error(f"Error en análisis visual: {e}")
            return None
    
    def _extract_key_frames(self, video_url: str, num_frames: int = 3) -> List[str]:
        """Extraer frames clave del video usando yt-dlp + ffmpeg"""
        try:
            import yt_dlp
            
            video_id = self._extract_video_id(video_url)
            if not video_id:
                return []
            
            with tempfile.TemporaryDirectory() as tmpdir:
                video_path = os.path.join(tmpdir, f"{video_id}.mp4")
                
                ydl_opts = {
                    'format': 'worst[ext=mp4]/worst',
                    'outtmpl': video_path,
                    'quiet': True,
                    'no_warnings': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])
                
                if not os.path.exists(video_path):
                    for f in os.listdir(tmpdir):
                        if f.endswith(('.mp4', '.webm', '.mkv')):
                            video_path = os.path.join(tmpdir, f)
                            break
                
                if not os.path.exists(video_path):
                    logger.warning("⚠️ No se pudo descargar el video")
                    return []
                
                import subprocess
                
                result = subprocess.run(
                    ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                     '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
                    capture_output=True, text=True
                )
                duration = float(result.stdout.strip()) if result.stdout.strip() else 60.0
                
                frames = []
                interval = duration / (num_frames + 1)
                
                for i in range(1, num_frames + 1):
                    timestamp = interval * i
                    frame_path = os.path.join(tmpdir, f"frame_{i}.jpg")
                    
                    subprocess.run([
                        'ffmpeg', '-ss', str(timestamp), '-i', video_path,
                        '-vframes', '1', '-q:v', '2', frame_path
                    ], capture_output=True)
                    
                    if os.path.exists(frame_path):
                        persistent_frame = os.path.join('/tmp', f"omnix_frame_{video_id}_{i}.jpg")
                        import shutil
                        shutil.copy(frame_path, persistent_frame)
                        frames.append(persistent_frame)
                
                return frames
                
        except ImportError:
            logger.warning("⚠️ yt-dlp o ffmpeg no disponible para extracción de frames")
            return []
        except Exception as e:
            logger.error(f"Error extrayendo frames: {e}")
            return []
    
    def _analyze_frame_with_vision(self, frame_path: str) -> Optional[Dict[str, Any]]:
        """Analizar un frame individual usando GPT-4 Vision o Gemini Vision"""
        try:
            if self.openai_client:
                return self._analyze_frame_gpt4_vision(frame_path)
            elif self.gemini_client:
                return self._analyze_frame_gemini_vision(frame_path)
            else:
                logger.warning("⚠️ No hay Vision API disponible")
                return None
        except Exception as e:
            logger.error(f"Error analizando frame: {e}")
            return None
    
    def _analyze_frame_gpt4_vision(self, frame_path: str) -> Optional[Dict[str, Any]]:
        """Analizar frame con GPT-4 Vision API"""
        if not self.openai_client:
            return None
            
        try:
            import base64
            
            with open(frame_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": CHART_ANALYSIS_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            return parse_vision_json(content, "GPT-4 Vision")
            
        except Exception as e:
            logger.error(f"Error con GPT-4 Vision: {e}")
            return None
    
    def _analyze_frame_gemini_vision(self, frame_path: str) -> Optional[Dict[str, Any]]:
        """Analizar frame con Gemini Vision API (NUEVO SDK google-genai)"""
        if not self.gemini_client:
            return None
            
        try:
            import PIL.Image
            
            img = PIL.Image.open(frame_path)
            
            if self._gemini_sdk == 'new':
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[CHART_ANALYSIS_PROMPT, img]
                )
                content = response.text if response else None
            else:
                model = self.gemini_client.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content([CHART_ANALYSIS_PROMPT, img])
                content = response.text if response else None
            
            analysis = parse_vision_json(content, "Gemini Vision")
            if analysis:
                logger.info("🧠 Análisis con Gemini Vision completado")
            return analysis
            
        except Exception as e:
            logger.error(f"Error con Gemini Vision: {e}")
            return None
    
    def _analyze_sentiment(self, text: str) -> Optional[Dict[str, Any]]:
        """Analizar sentimiento del trader (bullish, bearish, neutral)"""
        if not text:
            return None
            
        try:
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
                    max_tokens=1500
                )
                
                content = response.choices[0].message.content
                return parse_vision_json(content, "Sentiment Analysis")
            
            return None
            
        except Exception as e:
            logger.error(f"Error en análisis de sentimiento: {e}")
            return None
    
    def _integrate_multi_source(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Integrar análisis de múltiples fuentes en recomendaciones unificadas"""
        recommendations: Dict[str, Any] = {
            'action': 'HOLD',
            'confidence': 0.0,
            'reasons': [],
            'suggested_parameters': {},
            'risk_level': 'MEDIUM'
        }
        
        try:
            sources_count = len(analysis_results.get('sources', []))
            
            if sources_count == 0:
                return recommendations
            
            signals: List[Dict[str, Any]] = []
            
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
            
            if 'sentiment_analysis' in analysis_results:
                sentiment = analysis_results['sentiment_analysis']
                signals.append({
                    'source': 'sentiment',
                    'signal': sentiment.get('sentiment', 'neutral'),
                    'weight': 0.2
                })
            
            final_signal = self._calculate_weighted_signal(signals)
            recommendations['action'] = final_signal['action']
            recommendations['confidence'] = final_signal['confidence']
            recommendations['reasons'] = final_signal['reasons']
            
            if signals and 'params' in signals[0]:
                recommendations['suggested_parameters'] = signals[0]['params']
            
            logger.info(f"🧠 Recomendación integrada: {recommendations['action']} (conf: {recommendations['confidence']:.2%})")
            
        except Exception as e:
            logger.error(f"Error integrando fuentes: {e}")
        
        return recommendations
    
    def _calculate_weighted_signal(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcular señal final ponderada de múltiples fuentes"""
        if not signals:
            return {'action': 'HOLD', 'confidence': 0.0, 'reasons': []}
        
        signal_values: Dict[str, float] = {
            'bullish': 1.0, 'BUY': 1.0,
            'bearish': -1.0, 'SELL': -1.0,
            'neutral': 0.0, 'HOLD': 0.0
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        reasons: List[str] = []
        
        for sig in signals:
            value = signal_values.get(sig.get('signal', 'neutral'), 0.0)
            weight = sig.get('weight', 1.0)
            weighted_sum += value * weight
            total_weight += weight
            reasons.append(f"{sig.get('source', 'unknown')}: {sig.get('signal', 'neutral')}")
        
        final_value = weighted_sum / total_weight if total_weight > 0 else 0.0
        
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
    
    def _infer_signal_from_params(self, params: Dict[str, Any]) -> str:
        """Inferir señal de trading desde parámetros técnicos"""
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
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calcular confianza general del análisis"""
        sources = results.get('sources', [])
        if not sources:
            return 0.0
        
        base_confidence = len(sources) / 3.0
        
        individual_confidences: List[float] = []
        
        if 'transcript_analysis' in results:
            individual_confidences.append(results['transcript_analysis'].get('confidence', 0.5))
        
        if 'visual_analysis' in results:
            individual_confidences.append(results['visual_analysis'].get('confidence', 0.5))
        
        if 'sentiment_analysis' in results:
            individual_confidences.append(results['sentiment_analysis'].get('score', 0.5))
        
        avg_confidence = sum(individual_confidences) / len(individual_confidences) if individual_confidences else 0.5
        
        return min(base_confidence * avg_confidence, 1.0)
    
    def _calculate_visual_confidence(self, visual_findings: Dict[str, Any]) -> float:
        """Calcular confianza del análisis visual"""
        patterns_count = len(visual_findings.get('patterns_detected', []))
        indicators_count = len(visual_findings.get('indicators_visible', []))
        levels_count = len(visual_findings.get('support_resistance_levels', []))
        
        total_findings = patterns_count + indicators_count + levels_count
        
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
    
    def get_transcript_robust(self, video_url: str) -> Dict[str, Any]:
        """
        Método PÚBLICO y ROBUSTO para obtener transcripción de YouTube.
        Unifica todos los fallbacks en un solo punto de entrada.
        
        Args:
            video_url: URL completa del video de YouTube
            
        Returns:
            Dict con:
                - 'success': bool
                - 'transcript': str (si éxito)
                - 'method': str (método que funcionó)
                - 'error': str (si falló)
                - 'video_id': str
        """
        result: Dict[str, Any] = {
            'success': False,
            'transcript': None,
            'method': None,
            'error': None,
            'video_id': None,
            'attempts': []
        }
        
        video_id = self._extract_video_id(video_url)
        if not video_id:
            result['error'] = "No se pudo extraer el ID del video de la URL"
            logger.error(f"❌ {result['error']}: {video_url}")
            return result
        
        result['video_id'] = video_id
        logger.info(f"🎬 [{VERSION_BANNER}] Obteniendo transcripción robusta para video {video_id}...")
        
        if self.database_service:
            try:
                cached = self.database_service.get_cached_transcript(video_id)
                if cached and len(cached) > 50:
                    result['success'] = True
                    result['transcript'] = cached
                    result['method'] = 'cache'
                    logger.info(f"🚀 Transcripción obtenida de caché: {len(cached)} chars")
                    return result
            except Exception as cache_err:
                result['attempts'].append(f"cache: {str(cache_err)[:50]}")
        
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            
            try:
                transcript_data = YouTubeTranscriptApi.get_transcript(
                    video_id, 
                    languages=['es', 'en', 'es-419', 'es-ES', 'en-US', 'en-GB']
                )
                if transcript_data:
                    full_text = ' '.join([entry['text'] for entry in transcript_data])
                    if len(full_text) > 50:
                        result['success'] = True
                        result['transcript'] = full_text
                        result['method'] = 'youtube-transcript-api (direct)'
                        logger.info(f"✅ Transcripción directa: {len(full_text)} chars")
                        return result
            except Exception as direct_err:
                result['attempts'].append(f"yt-api-direct: {str(direct_err)[:50]}")
                logger.warning(f"⚠️ Método directo falló: {direct_err}")
            
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                for t in transcript_list:
                    try:
                        data = t.fetch()
                        full_text = ' '.join([entry['text'] for entry in data])
                        if len(full_text) > 50:
                            result['success'] = True
                            result['transcript'] = full_text
                            result['method'] = f'youtube-transcript-api (list - {t.language})'
                            logger.info(f"✅ Transcripción via list: {len(full_text)} chars")
                            return result
                    except Exception:
                        continue
            except Exception as list_err:
                result['attempts'].append(f"yt-api-list: {str(list_err)[:50]}")
                logger.warning(f"⚠️ list_transcripts falló: {list_err}")
                
        except ImportError:
            result['attempts'].append("youtube-transcript-api not installed")
        except Exception as api_err:
            result['attempts'].append(f"yt-api: {str(api_err)[:50]}")
        
        logger.info("🔧 Intentando yt-dlp como fallback...")
        ytdlp_transcript = self._get_transcript_ytdlp_only(video_id)
        if ytdlp_transcript and len(ytdlp_transcript) > 50:
            result['success'] = True
            result['transcript'] = ytdlp_transcript
            result['method'] = 'yt-dlp'
            logger.info(f"✅ Transcripción yt-dlp: {len(ytdlp_transcript)} chars")
            return result
        else:
            result['attempts'].append("yt-dlp: sin subtítulos")
        
        logger.info("🎤 Intentando Whisper como último recurso...")
        whisper_transcript = self._get_transcript_whisper(video_id)
        if whisper_transcript and len(whisper_transcript) > 50:
            result['success'] = True
            result['transcript'] = whisper_transcript
            result['method'] = 'whisper'
            logger.info(f"✅ Transcripción Whisper: {len(whisper_transcript)} chars")
            return result
        else:
            if self.openai_client:
                result['attempts'].append("whisper: descarga audio falló")
            else:
                result['attempts'].append("whisper: OpenAI no configurado")
        
        if not result['success']:
            all_attempts = ', '.join(result['attempts'])
            result['error'] = f"Todos los métodos fallaron: {all_attempts}"
            logger.warning(f"⚠️ {result['error']}")
        
        return result
    
    def _get_transcript(self, video_id: str) -> Optional[str]:
        """Obtener transcripción REAL del video usando youtube-transcript-api"""
        logger.info(f"📝 [{VERSION_BANNER}] Obteniendo transcripción de video {video_id}...")
        
        if self.database_service:
            try:
                cached = self.database_service.get_cached_transcript(video_id)
                if cached:
                    logger.info(f"🚀 Transcripción obtenida de caché: {len(cached)} chars")
                    return cached
            except Exception:
                pass
        
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
            
            try:
                try:
                    transcript_data = YouTubeTranscriptApi.get_transcript(
                        video_id, 
                        languages=['es', 'en', 'es-419', 'es-ES', 'en-US', 'en-GB']
                    )
                    if transcript_data:
                        full_text = ' '.join([entry['text'] for entry in transcript_data])
                        logger.info(f"✅ Transcripción obtenida (método directo): {len(full_text)} caracteres")
                        return full_text
                except Exception as direct_err:
                    logger.warning(f"⚠️ Método directo falló: {direct_err}, intentando list_transcripts...")
                
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                transcript = None
                for lang in ['es', 'en', 'es-419', 'es-ES', 'en-US', 'en-GB']:
                    try:
                        transcript = transcript_list.find_transcript([lang])
                        break
                    except Exception:
                        continue
                
                if not transcript:
                    try:
                        transcript = transcript_list.find_generated_transcript(['es', 'en'])
                    except Exception:
                        for t in transcript_list:
                            transcript = t
                            break
                
                if transcript:
                    transcript_data = transcript.fetch()
                    full_text = ' '.join([entry['text'] for entry in transcript_data])
                    logger.info(f"✅ Transcripción obtenida: {len(full_text)} caracteres, idioma: {transcript.language}")
                    return full_text
                else:
                    logger.warning(f"⚠️ No se encontró transcripción para video {video_id}")
                    return None
                    
            except TranscriptsDisabled:
                logger.warning(f"⚠️ Transcripciones deshabilitadas para video {video_id}")
                return self._get_transcript_ytdlp(video_id)
            except NoTranscriptFound:
                logger.warning(f"⚠️ No hay transcripción disponible para video {video_id}")
                return self._get_transcript_ytdlp(video_id)
            except VideoUnavailable:
                logger.warning(f"⚠️ Video {video_id} no disponible")
                return None
            except Exception as inner_err:
                logger.warning(f"⚠️ Error interno obteniendo transcripción: {inner_err}")
                logger.info("🔄 Intentando fallback con yt-dlp...")
                return self._get_transcript_ytdlp(video_id)
                
        except ImportError as ie:
            logger.error(f"❌ youtube-transcript-api no instalada: {ie}")
            logger.info("🔄 Intentando fallback con yt-dlp...")
            return self._get_transcript_ytdlp(video_id)
        except Exception as e:
            logger.error(f"❌ Error obteniendo transcripción: {e}")
            logger.info("🔄 Intentando fallback con yt-dlp...")
            return self._get_transcript_ytdlp(video_id)
    
    def _get_transcript_ytdlp_only(self, video_id: str, max_retries: int = 3) -> Optional[str]:
        """Obtener transcripción usando yt-dlp SOLO (sin llamar a Whisper)"""
        logger.info(f"🔧 [{VERSION_BANNER}] Intentando yt-dlp para video {video_id}...")
        
        try:
            import yt_dlp
            import time
            import random
        except ImportError:
            logger.warning("⚠️ yt-dlp no instalado")
            return None
        
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        for attempt in range(max_retries):
            if attempt > 0:
                delay = (2 ** attempt) + random.uniform(1, 3)
                logger.info(f"⏳ Esperando {delay:.1f}s antes de reintentar (intento {attempt + 1}/{max_retries})...")
                time.sleep(delay)
            
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    ydl_opts = {
                        'writesubtitles': True,
                        'writeautomaticsub': True,
                        'subtitleslangs': ['es', 'en', 'es-419', 'es-ES', 'en-US', 'en-GB'],
                        'subtitlesformat': 'vtt',
                        'skip_download': True,
                        'outtmpl': os.path.join(tmpdir, '%(id)s'),
                        'quiet': True,
                        'no_warnings': True,
                        'extract_flat': False,
                        'http_headers': {
                            'User-Agent': random.choice(user_agents),
                            'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
                        },
                        'socket_timeout': 30,
                        'retries': 3,
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(video_url, download=True)
                        
                        if info and 'subtitles' in info:
                            for lang in ['es', 'en', 'es-419', 'es-ES', 'en-US', 'en-GB']:
                                if lang in info['subtitles']:
                                    sub_file = os.path.join(tmpdir, f"{video_id}.{lang}.vtt")
                                    if os.path.exists(sub_file):
                                        with open(sub_file, 'r', encoding='utf-8') as f:
                                            vtt_content = f.read()
                                            text = self._parse_vtt(vtt_content)
                                            if text:
                                                logger.info(f"✅ Transcripción yt-dlp: {len(text)} chars (manual)")
                                                return text
                        
                        if info and 'automatic_captions' in info:
                            for lang in ['es', 'en', 'es-419', 'es-ES', 'en-US', 'en-GB']:
                                if lang in info['automatic_captions']:
                                    sub_file = os.path.join(tmpdir, f"{video_id}.{lang}.vtt")
                                    if os.path.exists(sub_file):
                                        with open(sub_file, 'r', encoding='utf-8') as f:
                                            vtt_content = f.read()
                                            text = self._parse_vtt(vtt_content)
                                            if text:
                                                logger.info(f"✅ Transcripción yt-dlp: {len(text)} chars (auto)")
                                                return text
                        
                        for filename in os.listdir(tmpdir):
                            if filename.endswith('.vtt'):
                                filepath = os.path.join(tmpdir, filename)
                                with open(filepath, 'r', encoding='utf-8') as f:
                                    vtt_content = f.read()
                                    text = self._parse_vtt(vtt_content)
                                    if text:
                                        logger.info(f"✅ Transcripción yt-dlp: {len(text)} chars")
                                        return text
                                        
            except Exception as ydl_err:
                error_str = str(ydl_err)
                if '429' in error_str or 'Too Many Requests' in error_str:
                    logger.warning(f"⚠️ Rate limit 429 (intento {attempt + 1}/{max_retries})")
                    continue
                else:
                    logger.warning(f"⚠️ yt-dlp error: {ydl_err}")
                    break
        
        logger.warning(f"⚠️ yt-dlp no encontró subtítulos para {video_id}")
        return None
    
    def _get_transcript_ytdlp(self, video_id: str, max_retries: int = 3) -> Optional[str]:
        """Obtener transcripción usando yt-dlp como fallback robusto con reintentos"""
        logger.info(f"🔧 [{VERSION_BANNER}] Intentando yt-dlp para video {video_id}...")
        
        try:
            import yt_dlp
            import time
            import random
        except ImportError:
            logger.warning("⚠️ yt-dlp no instalado")
            return None
        
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        last_error: Optional[Exception] = None
        
        for attempt in range(max_retries):
            if attempt > 0:
                delay = (2 ** attempt) + random.uniform(1, 3)
                logger.info(f"⏳ Esperando {delay:.1f}s antes de reintentar (intento {attempt + 1}/{max_retries})...")
                time.sleep(delay)
            
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    ydl_opts = {
                        'writesubtitles': True,
                        'writeautomaticsub': True,
                        'subtitleslangs': ['es', 'en', 'es-419', 'es-ES', 'en-US', 'en-GB'],
                        'subtitlesformat': 'vtt',
                        'skip_download': True,
                        'outtmpl': os.path.join(tmpdir, '%(id)s'),
                        'quiet': True,
                        'no_warnings': True,
                        'extract_flat': False,
                        'http_headers': {
                            'User-Agent': random.choice(user_agents),
                            'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
                        },
                        'socket_timeout': 30,
                        'retries': 3,
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(video_url, download=True)
                        
                        if info and 'subtitles' in info:
                            for lang in ['es', 'en', 'es-419', 'es-ES', 'en-US', 'en-GB']:
                                if lang in info['subtitles']:
                                    sub_file = os.path.join(tmpdir, f"{video_id}.{lang}.vtt")
                                    if os.path.exists(sub_file):
                                        with open(sub_file, 'r', encoding='utf-8') as f:
                                            vtt_content = f.read()
                                            text = self._parse_vtt(vtt_content)
                                            if text:
                                                logger.info(f"✅ Transcripción yt-dlp obtenida: {len(text)} chars (subtítulos manuales)")
                                                return text
                        
                        if info and 'automatic_captions' in info:
                            for lang in ['es', 'en', 'es-419', 'es-ES', 'en-US', 'en-GB']:
                                if lang in info['automatic_captions']:
                                    sub_file = os.path.join(tmpdir, f"{video_id}.{lang}.vtt")
                                    if os.path.exists(sub_file):
                                        with open(sub_file, 'r', encoding='utf-8') as f:
                                            vtt_content = f.read()
                                            text = self._parse_vtt(vtt_content)
                                            if text:
                                                logger.info(f"✅ Transcripción yt-dlp obtenida: {len(text)} chars (auto-generados)")
                                                return text
                        
                        for filename in os.listdir(tmpdir):
                            if filename.endswith('.vtt'):
                                filepath = os.path.join(tmpdir, filename)
                                with open(filepath, 'r', encoding='utf-8') as f:
                                    vtt_content = f.read()
                                    text = self._parse_vtt(vtt_content)
                                    if text:
                                        logger.info(f"✅ Transcripción yt-dlp obtenida: {len(text)} chars")
                                        return text
                                        
            except Exception as ydl_err:
                last_error = ydl_err
                error_str = str(ydl_err)
                if '429' in error_str or 'Too Many Requests' in error_str:
                    logger.warning(f"⚠️ Rate limit 429 (intento {attempt + 1}/{max_retries}): {ydl_err}")
                    continue
                else:
                    logger.warning(f"⚠️ yt-dlp extraction error: {ydl_err}")
                    break
        
        error_str = str(last_error) if last_error else "no subtitles found"
        logger.info(f"🎤 Subtítulos no disponibles ({error_str[:50]}...) - intentando transcripción de audio con Whisper...")
        whisper_result = self._get_transcript_whisper(video_id)
        if whisper_result:
            return whisper_result
        logger.warning(f"⚠️ Todos los métodos fallaron para video {video_id}")
        return None
    
    def _get_transcript_whisper(self, video_id: str, max_duration_seconds: int = 600) -> Optional[str]:
        """
        Fallback: Descargar audio del video y transcribir con OpenAI Whisper.
        Se usa cuando YouTube bloquea subtítulos con error 429.
        
        Args:
            video_id: ID del video de YouTube
            max_duration_seconds: Duración máxima en segundos (default: 10 minutos)
        """
        if not self.openai_client:
            logger.warning("⚠️ OpenAI client no disponible para Whisper")
            return None
        
        logger.info(f"🎤 [{VERSION_BANNER}] Iniciando transcripción Whisper para video {video_id}...")
        
        try:
            import yt_dlp
            
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            with tempfile.TemporaryDirectory() as tmpdir:
                audio_file = os.path.join(tmpdir, f"{video_id}.mp3")
                
                ydl_opts = {
                    'format': 'worstaudio[ext=m4a]/worstaudio/worst',
                    'outtmpl': os.path.join(tmpdir, f"{video_id}.%(ext)s"),
                    'quiet': True,
                    'no_warnings': True,
                    'max_downloads': 1,
                    'extract_audio': True,
                }
                
                logger.info("📥 Descargando audio del video...")
                
                info = None
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=True)
                    
                    if info:
                        duration = info.get('duration', 0)
                        if duration > max_duration_seconds:
                            logger.warning(f"⚠️ Video muy largo ({duration}s > {max_duration_seconds}s) - cancelando Whisper")
                            return None
                        logger.info(f"📊 Duración del video: {duration}s")
                
                actual_audio_file = audio_file
                for ext in ['.mp3', '.m4a', '.webm', '.opus']:
                    test_file = os.path.join(tmpdir, f"{video_id}{ext}")
                    if os.path.exists(test_file):
                        actual_audio_file = test_file
                        break
                
                if not os.path.exists(actual_audio_file):
                    for f in os.listdir(tmpdir):
                        if f.startswith(video_id):
                            actual_audio_file = os.path.join(tmpdir, f)
                            break
                
                if not os.path.exists(actual_audio_file):
                    logger.warning("⚠️ No se pudo descargar el audio")
                    return None
                
                file_size = os.path.getsize(actual_audio_file)
                logger.info(f"✅ Audio descargado: {file_size / 1024 / 1024:.2f} MB")
                
                if file_size > 25 * 1024 * 1024:
                    logger.warning(f"⚠️ Archivo de audio muy grande ({file_size / 1024 / 1024:.1f} MB > 25 MB)")
                    return None
                
                logger.info("🎤 Enviando a OpenAI Whisper para transcripción...")
                
                with open(actual_audio_file, 'rb') as audio:
                    transcript_response = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio,
                        language="es",
                        response_format="text"
                    )
                
                if transcript_response and len(str(transcript_response)) > 50:
                    result_text = str(transcript_response)
                    logger.info(f"✅ Transcripción Whisper exitosa: {len(result_text)} chars")
                    if self.database_service:
                        try:
                            duration = info.get('duration', 0) if info else None
                            self.database_service.save_transcript_cache(video_id, result_text, 'whisper', duration)
                        except Exception:
                            pass
                    return result_text
                else:
                    logger.warning("⚠️ Whisper retornó transcripción vacía o muy corta")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error en transcripción Whisper: {e}")
            return None
    
    def _parse_vtt(self, vtt_content: str) -> Optional[str]:
        """Parsear contenido VTT a texto plano"""
        try:
            lines = vtt_content.split('\n')
            text_lines: List[str] = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('WEBVTT'):
                    continue
                if line.startswith('Kind:') or line.startswith('Language:'):
                    continue
                if '-->' in line:
                    continue
                if line.isdigit():
                    continue
                line = re.sub(r'<[^>]+>', '', line)
                if line and (not text_lines or line not in text_lines[-3:]):
                    text_lines.append(line)
            
            full_text = ' '.join(text_lines)
            full_text = ' '.join(full_text.split())
            
            return full_text if len(full_text) > 50 else None
            
        except Exception as e:
            logger.warning(f"⚠️ Error parsing VTT: {e}")
            return None
    
    def _extract_technical_parameters(self, transcript: str) -> Dict[str, Any]:
        """Extraer parámetros técnicos de la transcripción con IA"""
        logger.info(f"🧠 [{VERSION_BANNER}] Analizando transcripción con IA ({len(transcript)} chars)...")
        
        try:
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": """Eres un experto en trading. Analiza la transcripción y extrae:
1. Estrategia principal mencionada
2. Timeframe recomendado (M1, M5, M15, H1, H4, D1, W1)
3. Activos/criptomonedas mencionados
4. Indicadores técnicos (RSI, MACD, EMA, etc.) con sus configuraciones
5. Niveles de soporte/resistencia si se mencionan
6. Puntos de entrada/salida recomendados
7. Gestión de riesgo (stop loss, take profit, ratio R:R)

Responde en JSON con esta estructura:
{
    "strategy": "nombre de la estrategia",
    "timeframe": "timeframe principal",
    "assets": ["lista", "de", "activos"],
    "indicators": {"RSI": "14", "EMA": "9,21"},
    "levels": {"support": [], "resistance": []},
    "entry_exit": {"entry": "descripción", "exit": "descripción"},
    "risk_management": {"stop_loss": "", "take_profit": "", "risk_reward": ""},
    "key_insights": ["punto clave 1", "punto clave 2"],
    "summary": "resumen ejecutivo del video en 2-3 oraciones"
}"""
                        },
                        {
                            "role": "user",
                            "content": f"Analiza esta transcripción de video de trading:\n\n{transcript[:8000]}"
                        }
                    ],
                    temperature=0.3,
                    max_tokens=1500
                )
                
                if not response or not response.choices or len(response.choices) == 0:
                    logger.warning("⚠️ OpenAI retornó respuesta vacía o sin choices")
                    return {
                        'strategy': 'Sin respuesta de OpenAI',
                        'summary': 'La API no retornó choices válidos',
                        'confidence': 0.0
                    }
                
                result_text = response.choices[0].message.content if response.choices[0].message else None
                
                if result_text:
                    try:
                        clean_text = result_text.strip()
                        if '```json' in clean_text:
                            clean_text = clean_text.split('```json')[1].split('```')[0]
                        elif '```' in clean_text:
                            clean_text = clean_text.split('```')[1].split('```')[0]
                        
                        analysis = json.loads(clean_text.strip())
                        if 'confidence' not in analysis:
                            analysis['confidence'] = None
                            analysis['confidence_note'] = 'AI model did not provide confidence score'
                        logger.info(f"✅ Análisis IA completado: estrategia={analysis.get('strategy', 'N/A')}")
                        return analysis
                    except json.JSONDecodeError:
                        logger.warning("⚠️ No se pudo parsear JSON, retornando texto raw")
                        return {
                            'raw_analysis': result_text,
                            'strategy': 'Ver análisis completo',
                            'summary': result_text[:500] if result_text else '',
                            'confidence': None,
                            'confidence_note': 'Could not parse structured response'
                        }
                else:
                    return {
                        'strategy': 'Sin respuesta de IA',
                        'summary': 'La IA no generó respuesta',
                        'confidence': 0.0
                    }
                        
            elif self.gemini_client:
                prompt = f"""Analiza esta transcripción de video de trading y extrae los puntos clave, estrategias, indicadores mencionados, y recomendaciones:

{transcript[:8000]}

Proporciona un análisis estructurado con:
1. Resumen ejecutivo
2. Estrategia principal
3. Indicadores y configuraciones
4. Puntos de entrada/salida
5. Gestión de riesgo"""
                
                if self._gemini_sdk == 'new':
                    response = self.gemini_client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt
                    )
                    content = response.text if response else ''
                else:
                    model = self.gemini_client.GenerativeModel('gemini-2.5-flash')
                    response = model.generate_content(prompt)
                    content = response.text if response else ''
                
                return {
                    'summary': content,
                    'strategy': 'Ver análisis completo',
                    'confidence': 0.75
                }
            else:
                return {
                    'raw_text': transcript[:2000],
                    'strategy': 'Análisis manual requerido',
                    'summary': f'Transcripción disponible ({len(transcript)} caracteres). Sin IA para análisis automático.',
                    'confidence': 0.5
                }
                
        except Exception as e:
            logger.error(f"❌ Error extrayendo parámetros técnicos: {e}")
            return {
                'strategy': 'Error en análisis',
                'summary': f'Error: {str(e)}',
                'confidence': 0.0
            }


def analyze_video_ultra(video_url: str, extract_frames: bool = True) -> Dict[str, Any]:
    """
    Función helper para análisis ultra de video
    
    Args:
        video_url: URL del video de YouTube
        extract_frames: Si True, analiza frames visuales
        
    Returns:
        Dict con análisis completo
    """
    analyzer = VideoAnalyzerUltra()
    return analyzer.analyze_video_complete(video_url, extract_frames=extract_frames)
