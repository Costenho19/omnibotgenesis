"""
🏆 REWARD SYSTEM - Sistema de Recompensas OMNIX V6.0
Sistema de puntos, niveles y badges para incentivar contribuciones

CARACTERÍSTICAS:
- Puntos por feedback útil
- Niveles de contribución (Novato → Experto)
- Badges especiales por logros
- Leaderboard comunitario
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



BADGES = {
    'first_feedback': {
        'name': '🎯 Primer Feedback',
        'description': 'Enviaste tu primer feedback',
        'points_required': 0,
        'condition': 'total_feedback >= 1'
    },
    'feedback_enthusiast': {
        'name': '📊 Entusiasta',
        'description': '10+ feedbacks enviados',
        'points_required': 0,
        'condition': 'total_feedback >= 10'
    },
    'feedback_master': {
        'name': '🎖️ Maestro del Feedback',
        'description': '50+ feedbacks enviados',
        'points_required': 0,
        'condition': 'total_feedback >= 50'
    },
    'helpful_contributor': {
        'name': '💎 Contribuidor Valioso',
        'description': '5+ feedbacks marcados como útiles',
        'points_required': 0,
        'condition': 'helpful_feedback >= 5'
    },
    'idea_maker': {
        'name': '💡 Generador de Ideas',
        'description': 'Enviaste una propuesta de mejora',
        'points_required': 0,
        'condition': 'proposals_submitted >= 1'
    },
    'innovator': {
        'name': '🚀 Innovador',
        'description': 'Una de tus propuestas fue implementada',
        'points_required': 0,
        'condition': 'proposals_accepted >= 1'
    },
    'rising_star': {
        'name': '⭐ Estrella Emergente',
        'description': '100+ puntos de contribución',
        'points_required': 100,
        'condition': 'contribution_points >= 100'
    },
    'community_leader': {
        'name': '👑 Líder Comunitario',
        'description': '500+ puntos de contribución',
        'points_required': 500,
        'condition': 'contribution_points >= 500'
    },
    'omnix_legend': {
        'name': '🏆 Leyenda OMNIX',
        'description': '1000+ puntos de contribución',
        'points_required': 1000,
        'condition': 'contribution_points >= 1000'
    }
}

LEVELS = {
    0: {'name': 'Nuevo', 'emoji': '🌱', 'min_points': 0},
    1: {'name': 'Novato', 'emoji': '🌿', 'min_points': 10},
    2: {'name': 'Aprendiz', 'emoji': '🌳', 'min_points': 50},
    3: {'name': 'Intermedio', 'emoji': '⭐', 'min_points': 100},
    4: {'name': 'Avanzado', 'emoji': '🌟', 'min_points': 300},
    5: {'name': 'Experto', 'emoji': '💫', 'min_points': 500},
    6: {'name': 'Maestro', 'emoji': '🏆', 'min_points': 1000},
    7: {'name': 'Leyenda', 'emoji': '👑', 'min_points': 2500}
}


class RewardSystem:
    """
    🏆 SISTEMA DE RECOMPENSAS COMUNITARIAS
    
    Gestiona:
    - Puntos por contribuciones
    - Niveles de usuario
    - Badges y logros
    - Leaderboard
    """
    
    def __init__(self, database_service=None):
        """
        Inicializa RewardSystem con database_service centralizado
        
        Args:
            database_service: DatabaseManager o DatabaseServiceEnterprise instance
        """
        self.db = database_service
        
        if self.db is not None:
            logger.info("✅ RewardSystem inicializado con DatabaseService")
    
    @property
    def connected(self):
        """Lazy connection check - evaluates each time for late-binding db_manager."""
        return self.db is not None and self.db.connected
    
    def _get_connection_DEPRECATED(self):
        """DEPRECATED: Ahora usa database_service centralizado"""
        pass
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Obtener perfil completo de un usuario con puntos, nivel y badges
        """
        if not self.connected:
            return self._get_default_profile(user_id)
        
        try:
            conn = self.db._get_connection()
            if not conn:
                return self._get_default_profile(user_id)
            
            cursor = conn.cursor(row_factory=_dict_row) if _dict_row else conn.cursor()
            
            cursor.execute('SELECT * FROM user_contributions WHERE user_id = %s', (user_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                return self._get_default_profile(user_id)
            
            points = user_data['contribution_points'] or 0
            level = self._calculate_level(points)
            
            badges_raw = user_data.get('badges')
            if not badges_raw or badges_raw == 'null':
                current_badges = []
            else:
                try:
                    current_badges = json.loads(badges_raw)
                    if not isinstance(current_badges, list):
                        current_badges = []
                except (json.JSONDecodeError, TypeError):
                    current_badges = []
            new_badges = self._check_new_badges(user_data, current_badges)
            
            if new_badges:
                all_badges = list(set(current_badges + new_badges))
                cursor.execute(
                    'UPDATE user_contributions SET badges = %s WHERE user_id = %s',
                    (json.dumps(all_badges), user_id)
                )
                conn.commit()
                current_badges = all_badges
            
            badge_details = [BADGES[b] for b in current_badges if b in BADGES]
            
            cursor.execute('''
                SELECT COUNT(*) + 1 as rank
                FROM user_contributions
                WHERE contribution_points > %s
            ''', (points,))
            rank_data = cursor.fetchone()
            
            profile_data = {
                'user_id': user_id,
                'username': user_data.get('username'),
                'points': points,
                'level': level,
                'level_info': LEVELS[level],
                'next_level': LEVELS.get(level + 1),
                'points_to_next': (LEVELS.get(level + 1, {}).get('min_points', points) - points) if level < 7 else 0,
                'badges': badge_details,
                'badge_count': len(current_badges),
                'stats': {
                    'total_feedback': user_data['total_feedback'] or 0,
                    'helpful_feedback': user_data['helpful_feedback'] or 0,
                    'proposals_submitted': user_data['proposals_submitted'] or 0,
                    'proposals_accepted': user_data['proposals_accepted'] or 0
                },
                'rank': rank_data['rank'],
                'new_badges_earned': new_badges,
                'member_since': user_data.get('first_contribution')
            }
            
            cursor.close()
            conn.close()
            return profile_data
            
        except Exception as e:
            logger.error(f"❌ Error getting user profile: {e}")
            if 'cursor' in locals() and cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
            if 'conn' in locals() and conn:
                try:
                    conn.close()
                except Exception:
                    pass
            return self._get_default_profile(user_id)
    
    def _get_default_profile(self, user_id: str) -> Dict[str, Any]:
        """Perfil por defecto para usuarios nuevos"""
        return {
            'user_id': user_id,
            'username': None,
            'points': 0,
            'level': 0,
            'level_info': LEVELS[0],
            'next_level': LEVELS[1],
            'points_to_next': 10,
            'badges': [],
            'badge_count': 0,
            'stats': {
                'total_feedback': 0,
                'helpful_feedback': 0,
                'proposals_submitted': 0,
                'proposals_accepted': 0
            },
            'rank': None,
            'new_badges_earned': [],
            'member_since': None
        }
    
    def _calculate_level(self, points: int) -> int:
        """Calcular nivel basado en puntos"""
        for level in sorted(LEVELS.keys(), reverse=True):
            if points >= LEVELS[level]['min_points']:
                return level
        return 0
    
    def _check_new_badges(self, user_data: Dict, current_badges: List[str]) -> List[str]:
        """Verificar qué badges nuevos ha ganado el usuario"""
        new_badges = []
        
        for badge_id, badge_info in BADGES.items():
            if badge_id in current_badges:
                continue
            
            condition = badge_info['condition']
            
            try:
                if eval(condition, {}, {
                    'total_feedback': user_data.get('total_feedback', 0) or 0,
                    'helpful_feedback': user_data.get('helpful_feedback', 0) or 0,
                    'proposals_submitted': user_data.get('proposals_submitted', 0) or 0,
                    'proposals_accepted': user_data.get('proposals_accepted', 0) or 0,
                    'contribution_points': user_data.get('contribution_points', 0) or 0,
                    'total_votes': user_data.get('total_votes', 0) or 0
                }):
                    new_badges.append(badge_id)
            except Exception as e:
                logger.warning(f"Error evaluating badge condition: {e}")
        
        return new_badges
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtener leaderboard de mejores contribuidores
        """
        if not self.connected:
            return []
        
        conn = self.db._get_connection()
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
                    helpful_feedback,
                    proposals_accepted,
                    badges
                FROM user_contributions
                WHERE contribution_points > 0
                ORDER BY contribution_points DESC
                LIMIT %s
            ''', (limit,))
            
            leaderboard = []
            for i, row in enumerate(cursor.fetchall(), 1):
                points = row['contribution_points'] or 0
                level = self._calculate_level(points)
                badges = json.loads(row.get('badges', '[]'))
                
                leaderboard.append({
                    'rank': i,
                    'user_id': row['user_id'],
                    'username': row['username'] or f"User #{row['user_id'][-4:]}",
                    'points': points,
                    'level': level,
                    'level_emoji': LEVELS[level]['emoji'],
                    'level_name': LEVELS[level]['name'],
                    'feedback_count': row['total_feedback'] or 0,
                    'badge_count': len(badges)
                })
            
            cursor.close()
            conn.close()
            return leaderboard
            
        except Exception as e:
            logger.error(f"❌ Error getting leaderboard: {e}")
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
            return []
    
    def award_bonus_points(self, user_id: str, points: int, reason: str) -> Dict[str, Any]:
        """
        Otorgar puntos bonus a un usuario (solo admin)
        """
        if not self.connected:
            return {'success': False, 'error': 'Database not available'}
        
        conn = self.db._get_connection()
        if not conn:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_contributions 
                SET contribution_points = contribution_points + %s,
                    last_contribution = CURRENT_TIMESTAMP
                WHERE user_id = %s
                RETURNING contribution_points
            ''', (points, user_id))
            
            result = cursor.fetchone()
            
            if result:
                conn.commit()
                return {
                    'success': True,
                    'user_id': user_id,
                    'points_awarded': points,
                    'new_total': result[0],
                    'reason': reason
                }
            else:
                return {'success': False, 'error': 'User not found'}
                
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error awarding points: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def get_available_badges(self) -> List[Dict[str, Any]]:
        """Obtener lista de todos los badges disponibles"""
        return [
            {
                'id': badge_id,
                'name': badge_info['name'],
                'description': badge_info['description'],
                'points_required': badge_info['points_required']
            }
            for badge_id, badge_info in BADGES.items()
        ]
    
    def mark_feedback_helpful(self, feedback_id: int, user_id: str) -> Dict[str, Any]:
        """
        Marcar un feedback como útil y otorgar puntos bonus al autor
        """
        if not self.connected:
            return {'success': False, 'error': 'Database not available'}
        
        conn = self.db._get_connection()
        if not conn:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            cursor = conn.cursor(row_factory=_dict_row) if _dict_row else conn.cursor()
            
            cursor.execute('''
                SELECT user_id, is_verified FROM community_feedback WHERE id = %s
            ''', (feedback_id,))
            
            feedback = cursor.fetchone()
            
            if not feedback:
                return {'success': False, 'error': 'Feedback not found'}
            
            if feedback['is_verified']:
                return {'success': False, 'error': 'Already marked as helpful'}
            
            cursor.execute('''
                UPDATE community_feedback 
                SET is_verified = true, helpful_votes = helpful_votes + 1
                WHERE id = %s
            ''', (feedback_id,))
            
            cursor.execute('''
                UPDATE user_contributions 
                SET helpful_feedback = helpful_feedback + 1,
                    contribution_points = contribution_points + 15
                WHERE user_id = %s
            ''', (feedback['user_id'],))
            
            conn.commit()
            
            return {
                'success': True,
                'feedback_id': feedback_id,
                'author_id': feedback['user_id'],
                'bonus_points': 15,
                'message': 'Feedback marcado como útil, autor recompensado'
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error marking feedback helpful: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
