"""
📊 COMMUNITY DASHBOARD - Panel de Control Comunitario OMNIX V6.0
Visualizaciones y estadísticas de la inteligencia colectiva

CARACTERÍSTICAS:
- Estadísticas globales de la comunidad
- Performance de estrategias según usuarios
- Tendencias de feedback
- Reportes ejecutivos
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import json

logger = logging.getLogger(__name__)

try:
    from psycopg.rows import dict_row
    PSYCOPG_AVAILABLE = True
except ImportError:
    PSYCOPG_AVAILABLE = False
    dict_row = None


class CommunityDashboard:
    """
    📊 DASHBOARD DE INTELIGENCIA COLECTIVA
    
    Proporciona:
    - Estadísticas en tiempo real de la comunidad
    - Rankings de estrategias según feedback
    - Tendencias y patrones
    - Reportes para Harold
    """
    
    def __init__(self, database_service=None):
        self.db = database_service
        
        if self.db is not None:
            logger.info("✅ CommunityDashboard inicializado con database_service")
    
    @property
    def connected(self):
        """Lazy connection check - evaluates each time for late-binding db_manager."""
        return self.db is not None and self.db.connected
    
    def get_global_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas globales de la comunidad
        """
        if not self.connected:
            return self._get_empty_stats()
        
        conn = self.db._get_connection()
        if not conn:
            return self._get_empty_stats()
        
        try:
            cursor = conn.cursor(row_factory=dict_row)
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_feedback,
                    COUNT(DISTINCT user_id) as total_contributors,
                    COUNT(CASE WHEN result = 'success' THEN 1 END) as success_count,
                    COUNT(CASE WHEN result = 'failure' THEN 1 END) as failure_count,
                    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '24 hours' THEN 1 END) as feedback_24h,
                    COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as feedback_7d
                FROM community_feedback
            ''')
            feedback_stats = cursor.fetchone()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_votes,
                    ROUND(AVG(vote)::numeric, 2) as avg_vote
                FROM strategy_votes
            ''')
            vote_stats = cursor.fetchone()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_proposals,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved,
                    COUNT(CASE WHEN status = 'implemented' THEN 1 END) as implemented
                FROM improvement_proposals
            ''')
            proposal_stats = cursor.fetchone()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_patterns,
                    COUNT(CASE WHEN status = 'detected' THEN 1 END) as pending_review,
                    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved
                FROM detected_patterns
            ''')
            pattern_stats = cursor.fetchone()
            
            cursor.execute('''
                SELECT SUM(contribution_points) as total_points
                FROM user_contributions
            ''')
            points_stats = cursor.fetchone()
            
            total = feedback_stats['total_feedback'] or 1
            success_rate = ((feedback_stats['success_count'] or 0) / total) * 100
            
            return {
                'success': True,
                'feedback': {
                    'total': feedback_stats['total_feedback'] or 0,
                    'success': feedback_stats['success_count'] or 0,
                    'failure': feedback_stats['failure_count'] or 0,
                    'success_rate': round(success_rate, 1),
                    'last_24h': feedback_stats['feedback_24h'] or 0,
                    'last_7d': feedback_stats['feedback_7d'] or 0
                },
                'contributors': {
                    'total': feedback_stats['total_contributors'] or 0,
                    'total_points_distributed': points_stats['total_points'] or 0
                },
                'votes': {
                    'total': vote_stats['total_votes'] or 0,
                    'average_rating': float(vote_stats['avg_vote'] or 0)
                },
                'proposals': {
                    'total': proposal_stats['total_proposals'] or 0,
                    'pending': proposal_stats['pending'] or 0,
                    'approved': proposal_stats['approved'] or 0,
                    'implemented': proposal_stats['implemented'] or 0
                },
                'patterns': {
                    'total': pattern_stats['total_patterns'] or 0,
                    'pending_review': pattern_stats['pending_review'] or 0,
                    'approved': pattern_stats['approved'] or 0
                },
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting global stats: {e}")
            return self._get_empty_stats()
        finally:
            conn.close()
    
    def _get_empty_stats(self) -> Dict[str, Any]:
        """Estadísticas vacías cuando no hay datos"""
        return {
            'success': True,
            'feedback': {
                'total': 0, 'success': 0, 'failure': 0, 
                'success_rate': 0, 'last_24h': 0, 'last_7d': 0
            },
            'contributors': {'total': 0, 'total_points_distributed': 0},
            'votes': {'total': 0, 'average_rating': 0},
            'proposals': {'total': 0, 'pending': 0, 'approved': 0, 'implemented': 0},
            'patterns': {'total': 0, 'pending_review': 0, 'approved': 0},
            'generated_at': datetime.now().isoformat()
        }
    
    def get_strategy_rankings(self) -> List[Dict[str, Any]]:
        """
        Obtener ranking de estrategias basado en feedback y votos
        """
        if not self.connected:
            return []
        
        conn = self.db._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(row_factory=dict_row)
            
            cursor.execute('''
                WITH feedback_stats AS (
                    SELECT 
                        strategy,
                        COUNT(*) as feedback_count,
                        COUNT(CASE WHEN result = 'success' THEN 1 END) as success_count,
                        COUNT(CASE WHEN result = 'failure' THEN 1 END) as failure_count
                    FROM community_feedback
                    WHERE strategy IS NOT NULL
                    GROUP BY strategy
                ),
                vote_stats AS (
                    SELECT 
                        strategy,
                        ROUND(AVG(vote)::numeric, 2) as avg_rating,
                        COUNT(*) as vote_count
                    FROM strategy_votes
                    GROUP BY strategy
                )
                SELECT 
                    COALESCE(f.strategy, v.strategy) as strategy,
                    COALESCE(f.feedback_count, 0) as feedback_count,
                    COALESCE(f.success_count, 0) as success_count,
                    COALESCE(f.failure_count, 0) as failure_count,
                    COALESCE(v.avg_rating, 0) as avg_rating,
                    COALESCE(v.vote_count, 0) as vote_count,
                    CASE 
                        WHEN f.feedback_count > 0 
                        THEN ROUND((f.success_count::numeric / f.feedback_count) * 100, 1)
                        ELSE 0 
                    END as success_rate
                FROM feedback_stats f
                FULL OUTER JOIN vote_stats v ON f.strategy = v.strategy
                ORDER BY avg_rating DESC, success_rate DESC
            ''')
            
            rankings = []
            for i, row in enumerate(cursor.fetchall(), 1):
                combined_score = (
                    (float(row['avg_rating'] or 0) / 5) * 50 +
                    (float(row['success_rate'] or 0) / 100) * 50
                )
                
                if combined_score >= 80:
                    health = '🟢 Excelente'
                elif combined_score >= 60:
                    health = '🟡 Bueno'
                elif combined_score >= 40:
                    health = '🟠 Regular'
                else:
                    health = '🔴 Bajo'
                
                rankings.append({
                    'rank': i,
                    'strategy': row['strategy'],
                    'avg_rating': float(row['avg_rating'] or 0),
                    'vote_count': row['vote_count'] or 0,
                    'feedback_count': row['feedback_count'] or 0,
                    'success_rate': float(row['success_rate'] or 0),
                    'combined_score': round(combined_score, 1),
                    'health_status': health
                })
            
            return rankings
            
        except Exception as e:
            logger.error(f"❌ Error getting strategy rankings: {e}")
            return []
        finally:
            conn.close()
    
    def get_trending_insights(self, days: int = 7) -> Dict[str, Any]:
        """
        Obtener insights de tendencias recientes
        """
        if not self.connected:
            return {'success': False, 'trends': []}
        
        conn = self.db._get_connection()
        if not conn:
            return {'success': False, 'trends': []}
        
        try:
            cursor = conn.cursor(row_factory=dict_row)
            since_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as count,
                    COUNT(CASE WHEN result = 'success' THEN 1 END) as success,
                    COUNT(CASE WHEN result = 'failure' THEN 1 END) as failure
                FROM community_feedback
                WHERE created_at >= %s
                GROUP BY DATE(created_at)
                ORDER BY date
            ''', (since_date,))
            
            daily_trends = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute('''
                SELECT strategy, market_condition, result, COUNT(*) as count
                FROM community_feedback
                WHERE created_at >= %s AND result = 'failure'
                GROUP BY strategy, market_condition, result
                ORDER BY count DESC
                LIMIT 5
            ''', (since_date,))
            
            problem_areas = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute('''
                SELECT strategy, market_condition, COUNT(*) as count
                FROM community_feedback
                WHERE created_at >= %s AND result = 'success'
                GROUP BY strategy, market_condition
                ORDER BY count DESC
                LIMIT 5
            ''', (since_date,))
            
            success_areas = [dict(row) for row in cursor.fetchall()]
            
            return {
                'success': True,
                'period_days': days,
                'daily_trends': daily_trends,
                'problem_areas': problem_areas,
                'success_areas': success_areas,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting trends: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def generate_executive_report(self) -> Dict[str, Any]:
        """
        Generar reporte ejecutivo para Harold
        """
        stats = self.get_global_stats()
        rankings = self.get_strategy_rankings()
        trends = self.get_trending_insights(7)
        
        report = {
            'title': 'OMNIX Community Intelligence Report',
            'generated_at': datetime.now().isoformat(),
            'executive_summary': {
                'total_contributors': stats['contributors']['total'],
                'total_feedback': stats['feedback']['total'],
                'community_success_rate': stats['feedback']['success_rate'],
                'average_strategy_rating': stats['votes']['average_rating'],
                'pending_actions': stats['proposals']['pending'] + stats['patterns']['pending_review']
            },
            'top_strategies': rankings[:3] if rankings else [],
            'areas_needing_attention': [],
            'recent_activity': {
                'feedback_24h': stats['feedback']['last_24h'],
                'feedback_7d': stats['feedback']['last_7d']
            },
            'recommendations': []
        }
        
        if rankings:
            low_performers = [r for r in rankings if r['combined_score'] < 50]
            report['areas_needing_attention'] = low_performers
        
        if trends.get('problem_areas'):
            for problem in trends['problem_areas'][:3]:
                report['recommendations'].append({
                    'type': 'review',
                    'message': f"Revisar {problem['strategy']} en condición {problem['market_condition']} ({problem['count']} fallos reportados)"
                })
        
        if stats['proposals']['pending'] > 0:
            report['recommendations'].append({
                'type': 'proposals',
                'message': f"Hay {stats['proposals']['pending']} propuestas de mejora pendientes de revisión"
            })
        
        if stats['patterns']['pending_review'] > 0:
            report['recommendations'].append({
                'type': 'patterns',
                'message': f"Hay {stats['patterns']['pending_review']} patrones detectados por AI pendientes de aprobación"
            })
        
        return report
    
    def format_telegram_stats(self) -> str:
        """
        Formatear estadísticas para mostrar en Telegram
        """
        stats = self.get_global_stats()
        rankings = self.get_strategy_rankings()[:5]
        
        message = """
📊 **COMMUNITY INTELLIGENCE DASHBOARD**

🧠 **ESTADÍSTICAS GLOBALES**
   👥 Contribuidores: {contributors}
   📝 Total Feedback: {feedback}
   ✅ Tasa de éxito: {success_rate}%
   ⭐ Rating promedio: {avg_rating}/5

📈 **ACTIVIDAD RECIENTE**
   🕐 Últimas 24h: {last_24h} feedback
   📅 Últimos 7 días: {last_7d} feedback

🏆 **TOP ESTRATEGIAS (según comunidad)**
{rankings}

💡 **ACCIONES PENDIENTES**
   📋 Propuestas: {pending_proposals}
   🔍 Patrones AI: {pending_patterns}

💎 **PUNTOS DISTRIBUIDOS**
   Total: {total_points} puntos

*OMNIX V6.0 ULTRA - Community Intelligence*
""".format(
            contributors=stats['contributors']['total'],
            feedback=stats['feedback']['total'],
            success_rate=stats['feedback']['success_rate'],
            avg_rating=stats['votes']['average_rating'],
            last_24h=stats['feedback']['last_24h'],
            last_7d=stats['feedback']['last_7d'],
            rankings=self._format_rankings(rankings),
            pending_proposals=stats['proposals']['pending'],
            pending_patterns=stats['patterns']['pending_review'],
            total_points=stats['contributors']['total_points_distributed']
        )
        
        return message
    
    def _format_rankings(self, rankings: List[Dict]) -> str:
        """Formatear rankings para Telegram"""
        if not rankings:
            return "   Sin datos suficientes aún"
        
        lines = []
        medals = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣']
        
        for i, r in enumerate(rankings):
            medal = medals[i] if i < len(medals) else f'{i+1}.'
            lines.append(f"   {medal} {r['strategy']}: {r['combined_score']}pts ({r['health_status']})")
        
        return '\n'.join(lines)
