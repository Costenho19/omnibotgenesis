"""
🧠 COMMUNITY FEEDBACK MANAGER - Sistema de Memoria Colectiva OMNIX V6.0
Gestiona todo el feedback de la comunidad para mejorar continuamente

CARACTERÍSTICAS:
- Almacena feedback positivo/negativo de señales
- Registra condiciones de mercado al momento del feedback
- Tracking de usuarios que dan feedback útil
- Base para análisis de patrones con AI
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
    logger.warning("psycopg2 no disponible para Community Feedback")


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
    """
    
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        self.connected = False
        
        if self.db_url and PSYCOPG2_AVAILABLE:
            try:
                self._init_tables()
                self.connected = True
                logger.info("✅ CommunityFeedbackManager conectado")
            except Exception as e:
                logger.error(f"❌ Error inicializando feedback tables: {e}")
        else:
            logger.warning("⚠️ Database no disponible para Community Feedback")
    
    def _get_connection(self):
        """Obtener conexión PostgreSQL"""
        if not self.db_url or not PSYCOPG2_AVAILABLE:
            return None
        return psycopg2.connect(self.db_url)
    
    def _init_tables(self):
        """Crear tablas de feedback comunitario"""
        conn = self._get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS community_feedback (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    username TEXT,
                    feedback_type TEXT NOT NULL,
                    signal_type TEXT,
                    strategy TEXT,
                    symbol TEXT,
                    result TEXT NOT NULL,
                    market_condition TEXT,
                    btc_price REAL,
                    volatility TEXT,
                    timeframe TEXT,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_verified BOOLEAN DEFAULT false,
                    helpful_votes INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategy_votes (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    vote INTEGER NOT NULL,
                    reason TEXT,
                    market_condition TEXT,
                    vote_date DATE DEFAULT CURRENT_DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, strategy, vote_date)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS improvement_proposals (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    username TEXT,
                    proposal_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    affected_strategy TEXT,
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    ai_analysis TEXT,
                    community_votes INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP,
                    implemented_at TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_contributions (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    total_feedback INTEGER DEFAULT 0,
                    helpful_feedback INTEGER DEFAULT 0,
                    total_votes INTEGER DEFAULT 0,
                    proposals_submitted INTEGER DEFAULT 0,
                    proposals_accepted INTEGER DEFAULT 0,
                    contribution_points INTEGER DEFAULT 0,
                    contribution_level TEXT DEFAULT 'Novato',
                    badges TEXT DEFAULT '[]',
                    first_contribution TIMESTAMP,
                    last_contribution TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detected_patterns (
                    id SERIAL PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    affected_strategy TEXT,
                    market_condition TEXT,
                    confidence REAL NOT NULL,
                    sample_size INTEGER NOT NULL,
                    success_rate REAL,
                    failure_rate REAL,
                    suggestion TEXT,
                    status TEXT DEFAULT 'detected',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    approved_at TIMESTAMP,
                    implemented_at TIMESTAMP
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_user ON community_feedback(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_strategy ON community_feedback(strategy)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_result ON community_feedback(result)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_votes_strategy ON strategy_votes(strategy)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_patterns_status ON detected_patterns(status)')
            
            conn.commit()
            logger.info("✅ Community Intelligence tables created")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error creating community tables: {e}")
            raise
        finally:
            conn.close()
    
    def submit_feedback(self, user_id: str, username: str, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registrar feedback de un usuario sobre una señal/estrategia
        
        Args:
            user_id: ID del usuario de Telegram
            username: Nombre de usuario
            feedback_data: {
                'feedback_type': 'signal' | 'strategy' | 'arbitrage',
                'signal_type': 'BUY' | 'SELL' | None,
                'strategy': 'ARES_V1' | 'ARES_V2' | etc,
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
        conn = self._get_connection()
        if not conn:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO community_feedback 
                (user_id, username, feedback_type, signal_type, strategy, symbol, 
                 result, market_condition, btc_price, volatility, timeframe, comment)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                user_id,
                username,
                feedback_data.get('feedback_type', 'signal'),
                feedback_data.get('signal_type'),
                feedback_data.get('strategy'),
                feedback_data.get('symbol'),
                feedback_data.get('result', 'unknown'),
                feedback_data.get('market_condition'),
                feedback_data.get('btc_price'),
                feedback_data.get('volatility'),
                feedback_data.get('timeframe'),
                feedback_data.get('comment')
            ))
            
            feedback_id = cursor.fetchone()[0]
            
            points_earned = self._update_user_contributions(cursor, user_id, username, 'feedback')
            
            conn.commit()
            
            return {
                'success': True,
                'feedback_id': feedback_id,
                'points_earned': points_earned,
                'message': f'Feedback registrado exitosamente (+{points_earned} puntos)'
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error submitting feedback: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def vote_strategy(self, user_id: str, strategy: str, vote: int, reason: str = None, 
                     market_condition: str = None) -> Dict[str, Any]:
        """
        Votar por una estrategia (1-5 estrellas)
        
        Args:
            user_id: ID del usuario
            strategy: Nombre de la estrategia (ARES_V1, ARES_V2, etc.)
            vote: Puntuación 1-5
            reason: Razón del voto (opcional)
            market_condition: Condición del mercado (opcional)
        """
        if vote < 1 or vote > 5:
            return {'success': False, 'error': 'Vote must be between 1 and 5'}
        
        conn = self._get_connection()
        if not conn:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO strategy_votes (user_id, strategy, vote, reason, market_condition, vote_date)
                VALUES (%s, %s, %s, %s, %s, CURRENT_DATE)
                ON CONFLICT (user_id, strategy, vote_date) 
                DO UPDATE SET vote = EXCLUDED.vote, reason = EXCLUDED.reason
                RETURNING id
            ''', (user_id, strategy, vote, reason, market_condition))
            
            vote_id = cursor.fetchone()[0]
            points_earned = self._update_user_contributions(cursor, user_id, None, 'vote')
            
            conn.commit()
            
            return {
                'success': True,
                'vote_id': vote_id,
                'points_earned': points_earned,
                'message': f'Voto registrado: {strategy} = {vote}⭐ (+{points_earned} puntos)'
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error voting strategy: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
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
        conn = self._get_connection()
        if not conn:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO improvement_proposals 
                (user_id, username, proposal_type, title, description, affected_strategy, priority)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                user_id,
                username,
                proposal_data.get('proposal_type', 'improvement'),
                proposal_data.get('title'),
                proposal_data.get('description'),
                proposal_data.get('affected_strategy'),
                proposal_data.get('priority', 'medium')
            ))
            
            proposal_id = cursor.fetchone()[0]
            points_earned = self._update_user_contributions(cursor, user_id, username, 'proposal')
            
            conn.commit()
            
            return {
                'success': True,
                'proposal_id': proposal_id,
                'points_earned': points_earned,
                'message': f'Propuesta #{proposal_id} enviada (+{points_earned} puntos)'
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error submitting proposal: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
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
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
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
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
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
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
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
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
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
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
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
