"""
🔗 OMNIX INSTITUTIONAL+ - VIDEO LEARNING INTEGRATION
Integración entre VideoAnalyzerUltra y AutoLearningSystem

FUNCIONALIDAD:
- Conecta análisis ultra de videos con sistema de auto-aprendizaje
- Extrae parámetros desde análisis visual + transcripción + sentimiento
- Valida seguridad de parámetros sugeridos
- Aplica cambios automáticamente (si enabled) o propone (si disabled)
- Mantiene historial completo de aprendizajes

Desarrollado por Harold Nunes - OMNIX INSTITUTIONAL+
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from omnix_config import VERSION_BANNER
except ImportError:
    VERSION_BANNER = "V6.5.4 INSTITUTIONAL+"


@dataclass
class LearningProposal:
    """Propuesta de aprendizaje desde análisis de video"""
    source: str  # 'video_ultra', 'video_basic'
    video_url: str
    timestamp: str
    confidence: float
    proposed_changes: Dict[str, float]
    reasoning: List[str]
    status: str  # 'proposed', 'applied', 'rejected'


class VideoLearningIntegration:
    """
    Integración entre VideoAnalyzerUltra y AutoLearningSystem
    
    Traduce análisis de videos (visual + transcripción + sentimiento)
    en cambios concretos de parámetros de trading
    """
    
    def __init__(self, auto_learning_system, video_analyzer_ultra=None):
        """
        Inicializar integración
        
        Args:
            auto_learning_system: Instancia de AutoLearningSystem
            video_analyzer_ultra: Instancia de VideoAnalyzerUltra (opcional)
        """
        self.auto_learning = auto_learning_system
        self.video_analyzer = video_analyzer_ultra
        self.learning_proposals = []
        
        # Mapeo de análisis de video a parámetros de trading
        self.parameter_mappings = {
            # RSI thresholds
            'rsi_oversold': 'rsi_threshold_oversold',
            'rsi_overbought': 'rsi_threshold_overbought',
            
            # EMA periods
            'ema_fast': 'ema_fast_period',
            'ema_medium': 'ema_medium_period',
            'ema_slow': 'ema_slow_period',
            
            # MACD
            'macd_fast': 'macd_fast_period',
            'macd_slow': 'macd_slow_period',
            'macd_signal': 'macd_signal_period',
            
            # Advanced
            'adaptive_gamma': 'adaptive_gamma',
            'kelly_fraction': 'kelly_fraction',
            'hmm_window': 'hmm_window',
            'kalman_q': 'kalman_process_noise',
            'kalman_r': 'kalman_measurement_noise'
        }
        
        logger.info("🔗 Video Learning Integration inicializada")
    
    def process_video_analysis(self, video_url: str, extract_frames: bool = True) -> Dict[str, Any]:
        """
        Procesar análisis completo de video y generar propuestas de parámetros
        
        Args:
            video_url: URL del video de YouTube
            extract_frames: Si True, analiza frames visuales
            
        Returns:
            Dict con propuestas de aprendizaje
        """
        logger.info(f"🎥 [{VERSION_BANNER}] Procesando video para aprendizaje: {video_url}")
        
        result: Dict[str, Any] = {
            'video_url': video_url,
            'timestamp': datetime.now().isoformat(),
            'status': 'processing'
        }
        
        try:
            # 1. Analizar video con VideoAnalyzerUltra
            if not self.video_analyzer:
                logger.error("❌ VideoAnalyzerUltra no disponible")
                result['status'] = 'error'
                result['error'] = 'VideoAnalyzerUltra no inicializado'
                return result
            
            logger.info("🎬 Analizando video con capacidades ultra...")
            analysis = self.video_analyzer.analyze_video_complete(
                video_url, extract_frames=extract_frames
            )
            
            if analysis.get('status') != 'success':
                result['status'] = 'error'
                result['error'] = 'Video analysis falló'
                return result
            
            # 2. Extraer propuestas de parámetros desde análisis
            logger.info("🧠 Extrayendo propuestas de parámetros...")
            proposals = self._extract_parameter_proposals(analysis)
            
            if not proposals:
                logger.warning("⚠️ No se encontraron propuestas de parámetros válidas")
                result['status'] = 'no_proposals'
                return result
            
            # 3. Validar seguridad de propuestas
            logger.info("🔐 Validando seguridad de propuestas...")
            safe_proposals = self._validate_safety(proposals)
            
            # 4. Aplicar o proponer cambios según estado del auto-learning
            if self.auto_learning.enabled:
                logger.info("✅ Auto-learning activo - Aplicando cambios automáticamente...")
                apply_result = self._apply_proposals(safe_proposals, analysis)
                result['status'] = 'applied'
                result['applied_changes'] = apply_result
            else:
                logger.info("⏸️ Auto-learning pausado - Generando propuestas...")
                result['status'] = 'proposed'
                result['proposals'] = safe_proposals
            
            # 5. Guardar propuesta en historial
            proposal = LearningProposal(
                source='video_ultra',
                video_url=video_url,
                timestamp=datetime.now().isoformat(),
                confidence=analysis.get('confidence_score', 0.0),
                proposed_changes=safe_proposals,
                reasoning=self._generate_reasoning(analysis, safe_proposals),
                status=result['status']
            )
            self.learning_proposals.append(proposal)
            
            result['analysis_summary'] = {
                'sources_used': analysis.get('sources', []),
                'confidence': analysis.get('confidence_score', 0.0),
                'integrated_recommendation': analysis.get('integrated_recommendations', {})
            }
            
            logger.info(f"✅ Video procesado - {len(safe_proposals)} propuestas generadas")
            
        except Exception as e:
            logger.error(f"❌ Error procesando video: {e}")
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def _extract_parameter_proposals(self, analysis: Dict) -> Dict[str, float]:
        """
        Extraer propuestas de parámetros desde análisis de video
        
        Combina información de todas las fuentes:
        - Transcripción (parámetros mencionados explícitamente)
        - Visual (patrones detectados sugieren ajustes)
        - Sentimiento (agresividad/conservadurismo sugiere Kelly fraction)
        """
        proposals = {}
        
        try:
            # FUENTE 1: TRANSCRIPCIÓN - Parámetros mencionados explícitamente
            if 'transcript_analysis' in analysis:
                transcript = analysis['transcript_analysis']
                params = transcript.get('technical_parameters', {})
                
                for param_name, value in params.items():
                    # Mapear nombre de parámetro a nombre interno
                    internal_name = self.parameter_mappings.get(param_name.lower())
                    if internal_name and isinstance(value, (int, float)):
                        proposals[internal_name] = float(value)
                        logger.info(f"   📝 Transcripción sugiere {internal_name}: {value}")
            
            # FUENTE 2: VISUAL - Ajustes basados en patrones detectados
            if 'visual_analysis' in analysis:
                visual = analysis['visual_analysis']
                patterns = visual.get('patterns_detected', [])
                
                # Si se detectan muchos patrones de reversión → aumentar sensibilidad RSI
                reversal_patterns = [p for p in patterns if 'head' in p or 'double' in p]
                if len(reversal_patterns) >= 2:
                    # Hacer RSI más sensible
                    proposals['rsi_threshold_oversold'] = 20.0  # Más conservador
                    proposals['rsi_threshold_overbought'] = 80.0
                    logger.info("   🎬 Patrones de reversión detectados - Ajustando RSI")
                
                # Si hay muchos soportes/resistencias → usar EMA más lento
                sr_levels = visual.get('support_resistance_levels', [])
                if len(sr_levels) >= 5:
                    proposals['ema_slow_period'] = 60.0  # Más suave
                    logger.info("   📊 Múltiples niveles S/R - EMA más lento")
            
            # FUENTE 3: SENTIMIENTO - Ajustar agresividad (Kelly fraction)
            if 'sentiment_analysis' in analysis:
                sentiment = analysis['sentiment_analysis']
                risk_appetite = sentiment.get('risk_appetite', 'moderate')
                
                if risk_appetite == 'aggressive':
                    proposals['kelly_fraction'] = 0.35  # Más agresivo
                    logger.info("   💭 Sentimiento agresivo - Kelly fraction aumentado")
                elif risk_appetite == 'conservative':
                    proposals['kelly_fraction'] = 0.15  # Más conservador
                    logger.info("   💭 Sentimiento conservador - Kelly fraction reducido")
            
            # FUENTE 4: RECOMENDACIONES INTEGRADAS
            if 'integrated_recommendations' in analysis:
                recommendations = analysis['integrated_recommendations']
                suggested_params = recommendations.get('suggested_parameters', {})
                
                for param_name, value in suggested_params.items():
                    internal_name = self.parameter_mappings.get(param_name.lower())
                    if internal_name and isinstance(value, (int, float)):
                        # Sobrescribir solo si no existe o tiene mayor confianza
                        if internal_name not in proposals:
                            proposals[internal_name] = float(value)
                            logger.info(f"   🧠 Recomendación integrada {internal_name}: {value}")
            
        except Exception as e:
            logger.error(f"Error extrayendo propuestas: {e}")
        
        return proposals
    
    def _validate_safety(self, proposals: Dict[str, float]) -> Dict[str, float]:
        """
        Validar que las propuestas están dentro de límites seguros
        
        Filtra cualquier propuesta que esté fuera de rangos permitidos
        """
        safe_proposals = {}
        
        for param_name, proposed_value in proposals.items():
            # Verificar que el parámetro es ajustable
            if param_name not in self.auto_learning.adjustable_params:
                logger.warning(f"⚠️ Parámetro '{param_name}' no es ajustable - ignorado")
                continue
            
            # Obtener límites
            limits = self.auto_learning.adjustable_params[param_name]
            
            # Validar rango
            if limits.min_value <= proposed_value <= limits.max_value:
                safe_proposals[param_name] = proposed_value
                logger.info(f"✅ {param_name}: {proposed_value} (dentro de límites)")
            else:
                # Clamp a límites seguros
                clamped_value = max(limits.min_value, min(proposed_value, limits.max_value))
                safe_proposals[param_name] = clamped_value
                logger.warning(f"⚠️ {param_name}: {proposed_value} → {clamped_value} (clamped)")
        
        return safe_proposals
    
    def _apply_proposals(self, proposals: Dict[str, float], analysis: Dict) -> Dict:
        """
        Aplicar propuestas de parámetros a través del AutoLearningSystem
        
        Returns:
            Dict con resultados de aplicación
        """
        applied = []
        failed = []
        
        for param_name, value in proposals.items():
            try:
                # Aplicar cambio a través de AutoLearningSystem
                result = self.auto_learning.apply_parameter_change(
                    parameter_name=param_name,
                    new_value=value,
                    source='video_ultra',
                    confidence=analysis.get('confidence_score', 0.7)
                )
                
                if result.get('status') == 'success':
                    applied.append({
                        'parameter': param_name,
                        'old_value': result.get('old_value'),
                        'new_value': value,
                        'timestamp': result.get('timestamp')
                    })
                    logger.info(f"✅ Aplicado: {param_name} = {value}")
                else:
                    failed.append({
                        'parameter': param_name,
                        'value': value,
                        'reason': result.get('message', 'Unknown error')
                    })
                    logger.error(f"❌ Falló: {param_name} - {result.get('message')}")
                    
            except Exception as e:
                logger.error(f"❌ Error aplicando {param_name}: {e}")
                failed.append({
                    'parameter': param_name,
                    'value': value,
                    'reason': str(e)
                })
        
        return {
            'applied_count': len(applied),
            'failed_count': len(failed),
            'applied_changes': applied,
            'failed_changes': failed
        }
    
    def _generate_reasoning(self, analysis: Dict, proposals: Dict) -> List[str]:
        """Generar explicaciones para las propuestas"""
        reasoning = []
        
        # Fuentes utilizadas
        sources = analysis.get('sources', [])
        if sources:
            reasoning.append(f"Análisis basado en {len(sources)} fuentes: {', '.join(sources)}")
        
        # Confianza general
        confidence = analysis.get('confidence_score', 0.0)
        reasoning.append(f"Confianza general del análisis: {confidence:.1%}")
        
        # Cantidad de cambios propuestos
        if proposals:
            reasoning.append(f"{len(proposals)} parámetros ajustados")
        
        # Sentimiento detectado
        if 'sentiment_analysis' in analysis:
            sentiment = analysis['sentiment_analysis'].get('sentiment', 'neutral')
            reasoning.append(f"Sentimiento del trader: {sentiment}")
        
        # Patrones visuales
        if 'visual_analysis' in analysis:
            patterns = analysis['visual_analysis'].get('patterns_detected', [])
            if patterns:
                reasoning.append(f"{len(patterns)} patrones gráficos detectados")
        
        return reasoning
    
    def get_learning_history(self, limit: int = 10) -> List[LearningProposal]:
        """
        Obtener historial de aprendizajes
        
        Args:
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de LearningProposal (más recientes primero)
        """
        return list(reversed(self.learning_proposals[-limit:]))
    
    def get_statistics(self) -> Dict:
        """Obtener estadísticas de aprendizaje"""
        total = len(self.learning_proposals)
        applied = sum(1 for p in self.learning_proposals if p.status == 'applied')
        proposed = sum(1 for p in self.learning_proposals if p.status == 'proposed')
        rejected = sum(1 for p in self.learning_proposals if p.status == 'rejected')
        
        avg_confidence = 0.0
        if self.learning_proposals:
            avg_confidence = sum(p.confidence for p in self.learning_proposals) / total
        
        # Parámetros más frecuentemente ajustados
        param_counts = {}
        for proposal in self.learning_proposals:
            for param in proposal.proposed_changes.keys():
                param_counts[param] = param_counts.get(param, 0) + 1
        
        most_common = sorted(param_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_videos_analyzed': total,
            'changes_applied': applied,
            'changes_proposed': proposed,
            'changes_rejected': rejected,
            'avg_confidence': avg_confidence,
            'most_adjusted_parameters': dict(most_common)
        }


# Helper function
def learn_from_video(video_url: str, 
                    auto_learning_system, 
                    video_analyzer_ultra,
                    extract_frames: bool = True) -> Dict:
    """
    Función helper para aprender de un video de YouTube
    
    Args:
        video_url: URL del video
        auto_learning_system: Instancia de AutoLearningSystem
        video_analyzer_ultra: Instancia de VideoAnalyzerUltra
        extract_frames: Si True, analiza frames visuales
        
    Returns:
        Dict con resultado del aprendizaje
    """
    integration = VideoLearningIntegration(auto_learning_system, video_analyzer_ultra)
    return integration.process_video_analysis(video_url, extract_frames)
