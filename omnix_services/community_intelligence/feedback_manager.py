"""
🧠 COMMUNITY FEEDBACK MANAGER - Sistema de Memoria Colectiva OMNIX V6.0
Gestiona todo el feedback de la comunidad para mejorar continuamente

CARACTERÍSTICAS:
- Almacena feedback positivo/negativo de señales
- Registra condiciones de mercado al momento del feedback
- Tracking de usuarios que dan feedback útil
- Base para análisis de patrones con AI

REFACTORIZADO: Ahora usa DatabaseService centralizado (no queries directas)
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import json
try:
    from psycopg.rows import dict_row as _dict_row
except ImportError:
    _dict_row = None

logger = logging.getLogger(__name__)


class CommunityFeedbackManager:
    """
    🧠 GESTOR DE FEEDBACK COMUNITARIO
    
    Sistema premium para capturar y almacenar feedback de usuarios
    sobre señales de trading, estrategias ARES, y oportunidades de arbitraje.
    
    FUNCIONALIDADES:
    - Registro de feedback con contexto de mercado
    - Votación de estrategias (ARES V1, V2, etc.)
    - Sugerencias de mejora de usuarios
    - Tracking de contribuciones por usuario
    
    REFACTORIZADO: Usa DatabaseService centralizado
    """
    
    def __init__(self, database_service=None):
        """
        Inicializar Community Feedback Manager
        
        Args:
            database_service: DatabaseManager o DatabaseServiceEnterprise instance
        """
        self.db = database_service
        
        if self.db is not None:
            logger.info("✅ CommunityFeedbackManager inicializado con DatabaseService")
        else:
            logger.warning("⚠️ Database no disponible para Community Feedback")
    
    @property
    def connected(self):
        """Lazy connection check - evaluates each time for late-binding db_manager."""
        return self.db is not None and self.db.connected
    
    def submit_feedback(self, user_id: str, username: str, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registrar feedback de un usuario sobre una señal/estrategia
        
        Args:
            user_id: ID del usuario de Telegram
            username: Nombre de usuario
            feedback_data: {
                'feedback_type': 'signal' | 'strategy' | 'arbitrage',
                'signal_type': 'BUY' | 'SELL' | None,
                'strategy': 'EMA_REGIME' | 'HMM_REGIME' | etc,
                'symbol': 'BTC/USD' | etc,
                'result': 'success' | 'failure' | 'partial',
                'market_condition': 'bullish' | 'bearish' | 'sideways',
                'btc_price': float,
                'volatility': 'low' | 'medium' | 'high',
                'timeframe': '1m' | '5m' | '1h' | etc,
                'comment': str optional
            }
        
        Returns:
            Dict with success status and points earned
        """
        if not self.connected:
            return {'success': False, 'error': 'Database not available'}
        
        # Usar DatabaseService centralizado
        result = self.db.submit_community_feedback(user_id, username, feedback_data)
        
        if result.get('success'):
            # Actualizar contribuciones del usuario (con tipo específico)
            points_earned = 10  # Puntos base por feedback
            self.db.update_user_contributions(user_id, username, points_earned, 'feedback')
            
            result['points_earned'] = points_earned
            result['message'] = f'Feedback registrado exitosamente (+{points_earned} puntos)'
        
        return result
    
    def vote_strategy(self, user_id: str, strategy: str, vote: int, reason: str = None, 
                     market_condition: str = None) -> Dict[str, Any]:
        """
        Votar por una estrategia (1-5 estrellas)
        
        Args:
            user_id: ID del usuario
            strategy: Strategy name (EMA_REGIME, HMM_REGIME, KALMAN_FILTER, etc.)
            vote: Puntuación 1-5
            reason: Razón del voto (opcional)
            market_condition: Condición del mercado (opcional)
        """
        if vote < 1 or vote > 5:
            return {'success': False, 'error': 'Vote must be between 1 and 5'}
        
        if not self.connected:
            return {'success': False, 'error': 'Database not available'}
        
        # Usar DatabaseService centralizado con market_condition
        result = self.db.vote_strategy(user_id, strategy, vote, reason, market_condition)
        
        if result.get('success'):
            # Actualizar contribuciones del usuario (con tipo específico)
            points_earned = 5  # Puntos por voto
            self.db.update_user_contributions(user_id, None, points_earned, 'vote')
            
            result['points_earned'] = points_earned
            result['message'] = f'Voto registrado: {strategy} = {vote}⭐ (+{points_earned} puntos)'
        
        return result
    
    def submit_proposal(self, user_id: str, username: str, proposal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enviar propuesta de mejora
        
        Args:
            user_id: ID del usuario
            username: Nombre de usuario
            proposal_data: {
                'proposal_type': 'feature' | 'bug' | 'improvement' | 'strategy',
                'title': str,
                'description': str,
                'affected_strategy': str optional,
                'priority': 'low' | 'medium' | 'high'
            }
        """
        if not self.connected:
            return {'success': False, 'error': 'Database not available'}
        
        # Usar DatabaseService centralizado
        result = self.db.submit_proposal(user_id, username, proposal_data)
        
        if result.get('success'):
            # Actualizar contribuciones del usuario (con tipo específico)
            points_earned = 25  # Puntos por propuesta
            self.db.update_user_contributions(user_id, username, points_earned, 'proposal')
            
            result['points_earned'] = points_earned
            result['message'] = f'Propuesta #{result["proposal_id"]} enviada (+{points_earned} puntos)'
        
        return result
    
    def _update_user_contributions(self, cursor, user_id: str, username: str = None, 
                                   contribution_type: str = 'feedback') -> int:
        """Actualizar contribuciones del usuario y calcular puntos"""
        
        points_map = {
            'feedback': 10,
            'vote': 5,
            'proposal': 25,
            'helpful_feedback': 15
        }
        points_earned = points_map.get(contribution_type, 5)
        
        cursor.execute('''
            INSERT INTO user_contributions (user_id, username, total_feedback, total_votes, 
                                           proposals_submitted, contribution_points, first_contribution)
            VALUES (%s, %s, 
                    CASE WHEN %s = 'feedback' THEN 1 ELSE 0 END,
                    CASE WHEN %s = 'vote' THEN 1 ELSE 0 END,
                    CASE WHEN %s = 'proposal' THEN 1 ELSE 0 END,
                    %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE SET
                username = COALESCE(EXCLUDED.username, user_contributions.username),
                total_feedback = user_contributions.total_feedback + 
                    CASE WHEN %s = 'feedback' THEN 1 ELSE 0 END,
                total_votes = user_contributions.total_votes + 
                    CASE WHEN %s = 'vote' THEN 1 ELSE 0 END,
                proposals_submitted = user_contributions.proposals_submitted + 
                    CASE WHEN %s = 'proposal' THEN 1 ELSE 0 END,
                contribution_points = user_contributions.contribution_points + %s,
                last_contribution = CURRENT_TIMESTAMP,
                contribution_level = CASE 
                    WHEN user_contributions.contribution_points + %s >= 1000 THEN 'Experto'
                    WHEN user_contributions.contribution_points + %s >= 500 THEN 'Avanzado'
                    WHEN user_contributions.contribution_points + %s >= 100 THEN 'Intermedio'
                    ELSE 'Novato'
                END
        ''', (user_id, username, contribution_type, contribution_type, contribution_type, 
              points_earned, contribution_type, contribution_type, contribution_type, 
              points_earned, points_earned, points_earned, points_earned))
        
        return points_earned
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Obtener estadísticas de contribución de un usuario"""
        conn = self._get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(row_factory=_dict_row) if _dict_row else conn.cursor()
            
            cursor.execute('''
                SELECT * FROM user_contributions WHERE user_id = %s
            ''', (user_id,))
            
            stats = cursor.fetchone()
            
            if stats:
                stats['badges'] = json.loads(stats.get('badges', '[]'))
                return dict(stats)
            
            return {
                'user_id': user_id,
                'total_feedback': 0,
                'total_votes': 0,
                'proposals_submitted': 0,
                'contribution_points': 0,
                'contribution_level': 'Nuevo',
                'badges': []
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user stats: {e}")
            return None
        finally:
            conn.close()
    
    def get_feedback_summary(self, strategy: str = None, days: int = 30) -> Dict[str, Any]:
        """Obtener resumen de feedback para una estrategia"""
        conn = self._get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(row_factory=_dict_row) if _dict_row else conn.cursor()
            
            since_date = datetime.now() - timedelta(days=days)
            
            if strategy:
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_feedback,
                        COUNT(CASE WHEN result = 'success' THEN 1 END) as success_count,
                        COUNT(CASE WHEN result = 'failure' THEN 1 END) as failure_count,
                        COUNT(CASE WHEN result = 'partial' THEN 1 END) as partial_count,
                        COUNT(DISTINCT user_id) as unique_users
                    FROM community_feedback 
                    WHERE strategy = %s AND created_at >= %s
                ''', (strategy, since_date))
            else:
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_feedback,
                        COUNT(CASE WHEN result = 'success' THEN 1 END) as success_count,
                        COUNT(CASE WHEN result = 'failure' THEN 1 END) as failure_count,
                        COUNT(CASE WHEN result = 'partial' THEN 1 END) as partial_count,
                        COUNT(DISTINCT user_id) as unique_users
                    FROM community_feedback 
                    WHERE created_at >= %s
                ''', (since_date,))
            
            summary = cursor.fetchone()
            
            if summary and summary['total_feedback'] > 0:
                summary['success_rate'] = round(
                    (summary['success_count'] / summary['total_feedback']) * 100, 1
                )
            else:
                summary = dict(summary) if summary else {}
                summary['success_rate'] = 0
            
            return dict(summary)
            
        except Exception as e:
            logger.error(f"❌ Error getting feedback summary: {e}")
            return None
        finally:
            conn.close()
    
    def get_strategy_ratings(self) -> List[Dict[str, Any]]:
        """Obtener ratings de todas las estrategias"""
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(row_factory=_dict_row) if _dict_row else conn.cursor()
            
            cursor.execute('''
                SELECT 
                    strategy,
                    ROUND(AVG(vote)::numeric, 2) as avg_rating,
                    COUNT(*) as total_votes,
                    COUNT(DISTINCT user_id) as unique_voters
                FROM strategy_votes
                GROUP BY strategy
                ORDER BY avg_rating DESC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"❌ Error getting strategy ratings: {e}")
            return []
        finally:
            conn.close()
    
    def get_top_contributors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtener los usuarios con más contribuciones"""
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(row_factory=_dict_row) if _dict_row else conn.cursor()
            
            cursor.execute('''
                SELECT 
                    user_id,
                    username,
                    contribution_points,
                    contribution_level,
                    total_feedback,
                    proposals_accepted
                FROM user_contributions
                ORDER BY contribution_points DESC
                LIMIT %s
            ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"❌ Error getting top contributors: {e}")
            return []
        finally:
            conn.close()
    
    def get_recent_feedback(self, limit: int = 20, strategy: str = None) -> List[Dict[str, Any]]:
        """Obtener feedback reciente"""
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(row_factory=_dict_row) if _dict_row else conn.cursor()
            
            if strategy:
                cursor.execute('''
                    SELECT * FROM community_feedback 
                    WHERE strategy = %s
                    ORDER BY created_at DESC 
                    LIMIT %s
                ''', (strategy, limit))
            else:
                cursor.execute('''
                    SELECT * FROM community_feedback 
                    ORDER BY created_at DESC 
                    LIMIT %s
                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"❌ Error getting recent feedback: {e}")
            return []
        finally:
            conn.close()
