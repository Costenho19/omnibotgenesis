"""
🧠 COMMUNITY ANALYZER - Análisis Inteligente de Feedback OMNIX V6.0
Utiliza AI (Gemini/GPT-4) para detectar patrones en feedback comunitario

CARACTERÍSTICAS:
- Detecta patrones de fallos en estrategias
- Identifica condiciones de mercado problemáticas
- Genera sugerencias de mejora basadas en datos
- NO modifica ARES automáticamente - solo sugiere
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import json
try:
    from psycopg.rows import dict_row as _dict_row
except ImportError:
    _dict_row = None

logger = logging.getLogger(__name__)


try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
    GEMINI_SDK_VERSION = 'new'
except ImportError:
    try:
        import google.generativeai as genai
        from google.generativeai import types
        GEMINI_AVAILABLE = True
        GEMINI_SDK_VERSION = 'legacy'
    except ImportError:
        GEMINI_AVAILABLE = False
        GEMINI_SDK_VERSION = None
        logger.warning("Gemini no disponible para análisis comunitario")


class CommunityAnalyzer:
    """
    🧠 ANALIZADOR DE INTELIGENCIA COLECTIVA
    
    Procesa feedback de la comunidad con AI para:
    - Detectar patrones de éxito/fallo
    - Identificar condiciones problemáticas
    - Generar recomendaciones de mejora
    
    IMPORTANTE: NO modifica estrategias automáticamente
    Solo genera sugerencias para aprobación humana
    """
    
    def __init__(self, database_service=None):
        """
        Inicializa CommunityAnalyzer con database_service centralizado
        
        Args:
            database_service: DatabaseManager o DatabaseServiceEnterprise instance
        """
        self.db = database_service
        
        if GEMINI_AVAILABLE:
            api_key = os.environ.get('GEMINI_API_KEY')
            if api_key:
                if GEMINI_SDK_VERSION == 'new':
                    self.gemini_client = genai.Client(api_key=api_key)
                    self.model = None
                    self.ai_available = True
                    logger.info("✅ CommunityAnalyzer con Gemini AI activado (NUEVO SDK)")
                else:
                    genai.configure(api_key=api_key)
                    self.model = genai.GenerativeModel('gemini-2.5-flash')
                    self.gemini_client = None
                    self.ai_available = True
                    logger.info("✅ CommunityAnalyzer con Gemini AI activado (LEGACY SDK)")
            else:
                self.ai_available = False
                logger.warning("⚠️ GEMINI_API_KEY no configurado")
        else:
            self.ai_available = False
    
    @property
    def connected(self):
        """Lazy connection check - evaluates each time for late-binding db_manager."""
        return self.db is not None and self.db.connected
    
    def _get_connection_DEPRECATED(self):
        """DEPRECATED: Ahora usa database_service centralizado"""
        pass
    
    def analyze_feedback_patterns(self, days: int = 30, min_samples: int = 5) -> Dict[str, Any]:
        """
        Analizar patrones en el feedback de la comunidad usando DatabaseService
        
        Returns:
            Dict con patrones detectados y sugerencias
        """
        if not self.connected:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            # Usar DAL centralizado
            since_date = datetime.now() - timedelta(days=days)
            raw_patterns = self.db.fetch_feedback_patterns(since_date, min_samples)
            
            patterns = self._process_raw_patterns(raw_patterns)
            
            if self.ai_available and patterns:
                ai_analysis = self._get_ai_analysis(patterns)
            else:
                ai_analysis = None
            
            detected_patterns = []
            for pattern in patterns:
                if pattern.get('failure_rate', 0) > 40:
                    detected = {
                        'pattern_type': 'high_failure',
                        'description': f"Alta tasa de fallos ({pattern['failure_rate']:.1f}%) para {pattern['strategy']} en mercado {pattern['condition']}",
                        'affected_strategy': pattern['strategy'],
                        'market_condition': pattern['condition'],
                        'confidence': min(pattern['sample_size'] / 20, 1.0),
                        'sample_size': pattern['sample_size'],
                        'failure_rate': pattern['failure_rate'],
                        'suggestion': f"Revisar {pattern['strategy']} en condiciones de mercado {pattern['condition']}",
                        'metadata': {
                            'volatility': pattern.get('volatility'),
                            'success_count': pattern.get('success', 0),
                            'failure_count': pattern.get('failure', 0)
                        }
                    }
                    detected_patterns.append(detected)
                    # Usar DAL para guardar patrón
                    self.db.upsert_detected_pattern(detected)
            
            return {
                'success': True,
                'patterns_analyzed': len(raw_patterns),
                'patterns_detected': len(detected_patterns),
                'patterns': detected_patterns,
                'ai_analysis': ai_analysis,
                'period_days': days,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing patterns: {e}")
            return {'success': False, 'error': str(e)}
    
    def _process_raw_patterns(self, raw_data: List[Dict]) -> List[Dict]:
        """Procesar datos crudos en patrones estructurados"""
        strategy_conditions = {}
        
        for row in raw_data:
            key = f"{row['strategy']}|{row['market_condition']}|{row['volatility']}"
            
            if key not in strategy_conditions:
                strategy_conditions[key] = {
                    'strategy': row['strategy'],
                    'condition': row['market_condition'],
                    'volatility': row['volatility'],
                    'success': 0,
                    'failure': 0,
                    'partial': 0,
                    'total': 0
                }
            
            sc = strategy_conditions[key]
            count = row['count']
            sc['total'] += count
            
            if row['result'] == 'success':
                sc['success'] += count
            elif row['result'] == 'failure':
                sc['failure'] += count
            else:
                sc['partial'] += count
        
        patterns = []
        for key, data in strategy_conditions.items():
            if data['total'] >= 3:
                data['success_rate'] = (data['success'] / data['total']) * 100
                data['failure_rate'] = (data['failure'] / data['total']) * 100
                data['sample_size'] = data['total']
                patterns.append(data)
        
        return sorted(patterns, key=lambda x: x['failure_rate'], reverse=True)
    
    def _get_ai_analysis(self, patterns: List[Dict]) -> str:
        """Obtener análisis AI de los patrones detectados - Soporta nuevo y legacy SDK"""
        if not self.ai_available:
            return None
        
        try:
            prompt = f"""
Eres un analista experto de trading algorítmico. Analiza estos patrones de feedback comunitario
sobre las estrategias ARES de OMNIX y proporciona recomendaciones:

PATRONES DETECTADOS:
{json.dumps(patterns[:10], indent=2)}

Por favor proporciona:
1. RESUMEN: Un párrafo resumiendo los hallazgos principales
2. PROBLEMAS: Lista de problemas identificados
3. RECOMENDACIONES: Sugerencias específicas de mejora (sin modificar código automáticamente)
4. PRIORIDAD: Cuáles problemas son más urgentes

Responde en español, de forma concisa y profesional.
IMPORTANTE: Las recomendaciones son SOLO sugerencias, no se implementarán automáticamente.
"""
            
            if GEMINI_SDK_VERSION == 'new' and self.gemini_client:
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                if response:
                    if hasattr(response, 'text') and response.text:
                        return response.text
                    elif hasattr(response, 'candidates') and response.candidates:
                        try:
                            return response.candidates[0].content.parts[0].text
                        except (IndexError, AttributeError):
                            pass
            elif self.model:
                response = self.model.generate_content(prompt)
                if response and hasattr(response, 'text') and response.text:
                    return response.text
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting AI analysis: {e}")
            return None
    
    def _save_detected_pattern_DEPRECATED(self, cursor, pattern: Dict):
        """DEPRECATED: Ahora usa db.upsert_detected_pattern()"""
        pass
    
    def get_strategy_health_report(self, strategy: str) -> Dict[str, Any]:
        """
        Generar reporte de salud de una estrategia basado en feedback comunitario
        
        Args:
            strategy: Strategy name (EMA_REGIME, HMM_REGIME, KALMAN_FILTER, etc.)
        """
        if not self.connected:
            return {'success': False, 'error': 'Database not available'}
        
        conn = self.db._get_connection()
        if not conn:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            cursor = conn.cursor(row_factory=_dict_row) if _dict_row else conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_feedback,
                    COUNT(CASE WHEN result = 'success' THEN 1 END) as success_count,
                    COUNT(CASE WHEN result = 'failure' THEN 1 END) as failure_count,
                    COUNT(DISTINCT user_id) as unique_reporters
                FROM community_feedback 
                WHERE strategy = %s AND created_at >= NOW() - INTERVAL '30 days'
            ''', (strategy,))
            
            feedback_stats = cursor.fetchone()
            
            cursor.execute('''
                SELECT 
                    ROUND(AVG(vote)::numeric, 2) as avg_rating,
                    COUNT(*) as total_votes
                FROM strategy_votes
                WHERE strategy = %s AND created_at >= NOW() - INTERVAL '30 days'
            ''', (strategy,))
            
            vote_stats = cursor.fetchone()
            
            cursor.execute('''
                SELECT market_condition, result, COUNT(*) as count
                FROM community_feedback
                WHERE strategy = %s AND created_at >= NOW() - INTERVAL '30 days'
                GROUP BY market_condition, result
                ORDER BY count DESC
            ''', (strategy,))
            
            condition_breakdown = cursor.fetchall()
            
            total = feedback_stats['total_feedback'] or 1
            health_score = (
                (feedback_stats['success_count'] or 0) / total * 50 +
                ((vote_stats['avg_rating'] or 3) / 5) * 50
            )
            
            if health_score >= 80:
                health_status = '🟢 Excelente'
            elif health_score >= 60:
                health_status = '🟡 Bueno'
            elif health_score >= 40:
                health_status = '🟠 Regular'
            else:
                health_status = '🔴 Necesita atención'
            
            return {
                'success': True,
                'strategy': strategy,
                'health_score': round(health_score, 1),
                'health_status': health_status,
                'feedback': {
                    'total': feedback_stats['total_feedback'] or 0,
                    'success': feedback_stats['success_count'] or 0,
                    'failure': feedback_stats['failure_count'] or 0,
                    'success_rate': round(((feedback_stats['success_count'] or 0) / total) * 100, 1)
                },
                'ratings': {
                    'average': float(vote_stats['avg_rating'] or 0),
                    'total_votes': vote_stats['total_votes'] or 0
                },
                'condition_analysis': [dict(c) for c in condition_breakdown],
                'unique_reporters': feedback_stats['unique_reporters'] or 0,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating health report: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def get_pending_patterns(self) -> List[Dict[str, Any]]:
        """Obtener patrones detectados pendientes de revisión"""
        if not self.connected:
            return []
        
        conn = self.db._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(row_factory=_dict_row) if _dict_row else conn.cursor()
            
            cursor.execute('''
                SELECT * FROM detected_patterns 
                WHERE status = 'detected'
                ORDER BY confidence DESC, created_at DESC
                LIMIT 20
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"❌ Error getting pending patterns: {e}")
            return []
        finally:
            conn.close()
    
    def approve_pattern(self, pattern_id: int, approved: bool = True) -> Dict[str, Any]:
        """
        Aprobar o rechazar un patrón detectado
        SOLO Harold puede aprobar patrones
        """
        if not self.connected:
            return {'success': False, 'error': 'Database not available'}
        
        conn = self.db._get_connection()
        if not conn:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            cursor = conn.cursor()
            
            new_status = 'approved' if approved else 'rejected'
            
            cursor.execute('''
                UPDATE detected_patterns 
                SET status = %s, approved_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id
            ''', (new_status, pattern_id))
            
            result = cursor.fetchone()
            
            if result:
                conn.commit()
                return {
                    'success': True,
                    'pattern_id': pattern_id,
                    'new_status': new_status,
                    'message': f'Patrón #{pattern_id} {"aprobado" if approved else "rechazado"}'
                }
            else:
                return {'success': False, 'error': 'Pattern not found'}
                
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error approving pattern: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def generate_community_insights(self) -> Dict[str, Any]:
        """
        Generar insights generales de la comunidad usando DatabaseService
        """
        if not self.connected:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            # Usar DAL para stats básicas
            stats = self.db.get_community_stats()
            
            # Obtener top contributors y proposals usando DAL
            top_contributors = self.db.get_top_contributors(limit=5, days=30)
            proposals = self.db.get_improvement_proposals(status='pending', limit=5)
            
            return {
                'success': True,
                'overview': {
                    'total_feedback': stats.get('total_feedback', 0),
                    'active_contributors': stats.get('total_contributors', 0),
                    'pending_proposals': stats.get('pending_proposals', 0),
                    'active_patterns': stats.get('active_patterns', 0)
                },
                'top_contributors': top_contributors,
                'recent_proposals': proposals,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating insights: {e}")
            return {'success': False, 'error': str(e)}
