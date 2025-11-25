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

logger = logging.getLogger(__name__)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
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
    
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        self.connected = PSYCOPG2_AVAILABLE and bool(self.db_url)
        
        if GEMINI_AVAILABLE:
            api_key = os.environ.get('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                self.ai_available = True
                logger.info("✅ CommunityAnalyzer con Gemini AI activado")
            else:
                self.ai_available = False
                logger.warning("⚠️ GEMINI_API_KEY no configurado")
        else:
            self.ai_available = False
    
    def _get_connection(self):
        """Obtener conexión PostgreSQL"""
        if not self.db_url or not PSYCOPG2_AVAILABLE:
            return None
        return psycopg2.connect(self.db_url)
    
    def analyze_feedback_patterns(self, days: int = 30, min_samples: int = 5) -> Dict[str, Any]:
        """
        Analizar patrones en el feedback de la comunidad
        
        Returns:
            Dict con patrones detectados y sugerencias
        """
        conn = self._get_connection()
        if not conn:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            since_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT 
                    strategy,
                    market_condition,
                    volatility,
                    result,
                    COUNT(*) as count
                FROM community_feedback
                WHERE created_at >= %s
                GROUP BY strategy, market_condition, volatility, result
                HAVING COUNT(*) >= %s
                ORDER BY strategy, count DESC
            ''', (since_date, min_samples))
            
            raw_patterns = cursor.fetchall()
            
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
                        'suggestion': f"Revisar {pattern['strategy']} en condiciones de mercado {pattern['condition']}"
                    }
                    detected_patterns.append(detected)
                    self._save_detected_pattern(cursor, detected)
            
            conn.commit()
            
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
            conn.rollback()
            logger.error(f"❌ Error analyzing patterns: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
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
        """Obtener análisis AI de los patrones detectados"""
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
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"❌ Error getting AI analysis: {e}")
            return None
    
    def _save_detected_pattern(self, cursor, pattern: Dict):
        """Guardar patrón detectado en la base de datos (con deduplicación)"""
        try:
            cursor.execute('''
                SELECT id FROM detected_patterns 
                WHERE affected_strategy = %s 
                AND market_condition = %s 
                AND pattern_type = %s
                AND status = 'detected'
                AND created_at >= NOW() - INTERVAL '7 days'
                LIMIT 1
            ''', (
                pattern['affected_strategy'],
                pattern['market_condition'],
                pattern['pattern_type']
            ))
            
            existing = cursor.fetchone()
            if existing:
                cursor.execute('''
                    UPDATE detected_patterns 
                    SET confidence = %s, sample_size = %s, failure_rate = %s, 
                        suggestion = %s, created_at = NOW()
                    WHERE id = %s
                ''', (
                    pattern['confidence'],
                    pattern['sample_size'],
                    pattern['failure_rate'],
                    pattern['suggestion'],
                    existing[0]
                ))
                logger.info(f"📝 Pattern updated: {pattern['pattern_type']} for {pattern['affected_strategy']}")
            else:
                cursor.execute('''
                    INSERT INTO detected_patterns 
                    (pattern_type, description, affected_strategy, market_condition, 
                     confidence, sample_size, failure_rate, suggestion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    pattern['pattern_type'],
                    pattern['description'],
                    pattern['affected_strategy'],
                    pattern['market_condition'],
                    pattern['confidence'],
                    pattern['sample_size'],
                    pattern['failure_rate'],
                    pattern['suggestion']
                ))
                logger.info(f"✅ Pattern saved: {pattern['pattern_type']} for {pattern['affected_strategy']}")
        except Exception as e:
            logger.error(f"❌ Error saving pattern: {e}")
    
    def get_strategy_health_report(self, strategy: str) -> Dict[str, Any]:
        """
        Generar reporte de salud de una estrategia basado en feedback comunitario
        
        Args:
            strategy: Nombre de la estrategia (ARES_V1, ARES_V2, etc.)
        """
        conn = self._get_connection()
        if not conn:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
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
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
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
        conn = self._get_connection()
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
        Generar insights generales de la comunidad
        """
        conn = self._get_connection()
        if not conn:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_feedback,
                    COUNT(DISTINCT user_id) as active_users,
                    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as feedback_7d,
                    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '1 day' THEN 1 END) as feedback_24h
                FROM community_feedback
            ''')
            feedback_overview = cursor.fetchone()
            
            cursor.execute('''
                SELECT 
                    strategy,
                    COUNT(*) as feedback_count,
                    ROUND(AVG(CASE WHEN result = 'success' THEN 100 ELSE 0 END)::numeric, 1) as success_rate
                FROM community_feedback
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY strategy
                ORDER BY feedback_count DESC
            ''')
            strategy_performance = cursor.fetchall()
            
            cursor.execute('SELECT COUNT(*) as count FROM improvement_proposals WHERE status = %s', ('pending',))
            pending_proposals = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM detected_patterns WHERE status = %s', ('detected',))
            pending_patterns = cursor.fetchone()['count']
            
            return {
                'success': True,
                'overview': {
                    'total_feedback': feedback_overview['total_feedback'],
                    'active_contributors': feedback_overview['active_users'],
                    'feedback_last_7d': feedback_overview['feedback_7d'],
                    'feedback_last_24h': feedback_overview['feedback_24h']
                },
                'strategy_performance': [dict(s) for s in strategy_performance],
                'pending_actions': {
                    'proposals': pending_proposals,
                    'patterns': pending_patterns
                },
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating insights: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
