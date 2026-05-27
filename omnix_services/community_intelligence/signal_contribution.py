"""
🚀 SIGNAL CONTRIBUTION MANAGER - Crowdsourcing de Alpha OMNIX V6.0
Sistema donde usuarios comparten señales y ganan royalties cuando funcionan

DIFERENCIADOR COMPETITIVO:
- Usuario A comparte señal "BTC LONG en $95K"
- Si otros usuarios la ejecutan y gana → Usuario A recibe royalties
- Sistema de reputación basado en señales exitosas
- Los mejores contribuidores = más influencia en el sistema

FLUJO:
1. Usuario comparte señal con /share_signal
2. Señal aparece en /community_signals para todos
3. Otros usuarios pueden ejecutarla o votar
4. Si señal es exitosa → contribuidor gana puntos royalty
5. Top contribuidores aparecen en /signal_leaderboard

REFACTORIZADO (Nov 26, 2025):
- Usa DatabaseService centralizado (no queries directas)
- Tablas definidas en database_service.py (única fuente de verdad)
- Métodos DAL: save_community_signal(), get_community_signals()
- 120 líneas de código duplicado eliminadas
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import json
import hashlib
try:
    from psycopg.rows import dict_row as _dict_row
except ImportError:
    _dict_row = None

logger = logging.getLogger(__name__)



class SignalContributionManager:
    """
    🚀 GESTOR DE SEÑALES COMUNITARIAS
    
    Sistema premium para crowdsourcing de alpha:
    - Usuarios comparten señales de trading
    - Sistema trackea performance de cada señal
    - Royalties automáticos para contribuidores exitosos
    - Ranking de mejores "alpha hunters"
    
    REFACTORIZADO: Usa DatabaseService centralizado (Nov 26, 2025)
    - Tablas: community_signals, signal_executions, signal_votes, alpha_leaderboard
    - Definidas en: omnix_services/database_service/database_service.py
    """
    
    SIGNAL_TYPES = ['LONG', 'SHORT', 'NEUTRAL']
    TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d', '1w']
    
    ROYALTY_POINTS = {
        'signal_shared': 10,
        'signal_voted': 2,
        'signal_executed_by_others': 5,
        'signal_success': 50,
        'signal_partial': 25,
        'signal_failure': -10,
        'top_contributor_bonus': 100
    }
    
    def __init__(self, database_service=None, reward_system=None):
        """
        Inicializar Signal Contribution Manager
        
        Args:
            database_service: DatabaseManager o DatabaseServiceEnterprise instance
            reward_system: RewardSystem instance (opcional)
        """
        self.db = database_service
        self.reward_system = reward_system
        
        if self.db is not None:
            logger.info("✅ SignalContributionManager inicializado con DatabaseService")
        else:
            logger.warning("⚠️ Database no disponible para Signal Contribution")
    
    @property
    def connected(self):
        """Lazy connection check - evaluates each time for late-binding db_manager."""
        return self.db is not None and self.db.connected
    
    def share_signal(self, user_id: str, username: str, signal_data: Dict) -> Dict:
        """
        🚀 Compartir una señal con la comunidad
        
        Args:
            user_id: ID del contribuidor
            username: Nombre del contribuidor
            signal_data: {
                'symbol': 'BTC',
                'signal_type': 'LONG',
                'entry_price': 95000,
                'target_price': 100000,
                'stop_loss': 92000,
                'timeframe': '4h',
                'confidence': 75,
                'reasoning': 'RSI oversold + support level'
            }
        
        Returns:
            {'success': True, 'signal_id': 'xxx', 'points_earned': 10}
        """
        if not self.connected:
            return {'success': False, 'error': 'Database no disponible'}
        
        # Validación de signal_type
        signal_type = signal_data.get('signal_type', 'LONG').upper()
        if signal_type not in self.SIGNAL_TYPES:
            return {'success': False, 'error': f'Tipo inválido. Usa: {self.SIGNAL_TYPES}'}
        
        # Preparar datos completos para la señal
        signal_id = self._generate_signal_id(user_id, signal_data)
        symbol = signal_data.get('symbol', 'BTC').upper()
        
        full_signal_data = {
            'signal_id': signal_id,
            'contributor_id': user_id,
            'contributor_name': username,
            'symbol': symbol,
            'signal_type': signal_type,
            'entry_price': signal_data.get('entry_price'),
            'target_price': signal_data.get('target_price'),
            'stop_loss': signal_data.get('stop_loss'),
            'timeframe': signal_data.get('timeframe', '1h'),
            'confidence': signal_data.get('confidence', 50),
            'reasoning': signal_data.get('reasoning'),
            'indicators_used': signal_data.get('indicators'),
            'market_condition': signal_data.get('market_condition')
        }
        
        # Usar DatabaseService centralizado
        result = self.db.save_community_signal(full_signal_data)
        
        if result.get('success'):
            # Premiar puntos
            points = self.ROYALTY_POINTS['signal_shared']
            if self.reward_system:
                self.reward_system.award_points(user_id, points, 'signal_shared')
            
            logger.info(f"✅ Señal compartida: {signal_id} por {username}")
            
            result['signal_id'] = signal_id
            result['symbol'] = symbol
            result['signal_type'] = signal_type
            result['points_earned'] = points
        
        return result
    
    def get_community_signals(self, limit: int = 10, symbol: str = None) -> List[Dict]:
        """
        📊 Obtener señales activas de la comunidad
        """
        if not self.connected:
            return []
        
        # Usar DatabaseService centralizado
        signals = self.db.get_community_signals(status='active', limit=limit)
        return signals if signals else []
    
    def vote_signal(self, signal_id: str, voter_id: str, vote_type: str) -> Dict:
        """
        👍/👎 Votar una señal
        """
        conn = self.db._get_connection() if self.connected else None
        if not conn:
            return {'success': False, 'error': 'Database no disponible'}
        
        try:
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT contributor_id FROM community_signals WHERE signal_id = %s',
                (signal_id,)
            )
            row = cursor.fetchone()
            if not row:
                return {'success': False, 'error': 'Señal no encontrada'}
            
            if row[0] == voter_id:
                return {'success': False, 'error': 'No puedes votar tu propia señal'}
            
            cursor.execute('''
                INSERT INTO signal_votes (signal_id, voter_id, vote_type)
                VALUES (%s, %s, %s)
                ON CONFLICT (signal_id, voter_id) 
                DO UPDATE SET vote_type = EXCLUDED.vote_type
            ''', (signal_id, voter_id, vote_type))
            
            if vote_type == 'up':
                cursor.execute(
                    'UPDATE community_signals SET upvotes = upvotes + 1 WHERE signal_id = %s',
                    (signal_id,)
                )
            else:
                cursor.execute(
                    'UPDATE community_signals SET downvotes = downvotes + 1 WHERE signal_id = %s',
                    (signal_id,)
                )
            
            conn.commit()
            
            return {'success': True, 'vote': vote_type}
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error voting signal: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def execute_signal(self, signal_id: str, executor_id: str, executor_name: str,
                       entry_price: float = None) -> Dict:
        """
        ▶️ Registrar que un usuario ejecutó una señal
        """
        conn = self.db._get_connection() if self.connected else None
        if not conn:
            return {'success': False, 'error': 'Database no disponible'}
        
        try:
            cursor = conn.cursor(row_factory=_dict_row) if _dict_row else conn.cursor()
            
            cursor.execute(
                'SELECT * FROM community_signals WHERE signal_id = %s AND status = %s',
                (signal_id, 'active')
            )
            signal = cursor.fetchone()
            if not signal:
                return {'success': False, 'error': 'Señal no encontrada o expirada'}
            
            if signal['contributor_id'] == executor_id:
                return {'success': False, 'error': 'No puedes ejecutar tu propia señal'}
            
            cursor.execute('''
                INSERT INTO signal_executions 
                (signal_id, executor_id, executor_name, entry_price)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            ''', (signal_id, executor_id, executor_name, entry_price or signal['entry_price']))
            
            cursor.execute('''
                UPDATE community_signals 
                SET executions_count = executions_count + 1
                WHERE signal_id = %s
            ''', (signal_id,))
            
            self._update_leaderboard(cursor, signal['contributor_id'], 
                                    signal['contributor_name'], 'signal_executed')
            
            conn.commit()
            
            points = self.ROYALTY_POINTS['signal_executed_by_others']
            if self.reward_system:
                self.reward_system.award_points(
                    signal['contributor_id'], 
                    points, 
                    f'signal_executed:{signal_id}'
                )
            
            return {
                'success': True,
                'signal': dict(signal),
                'message': f"Ejecutando señal de {signal['contributor_name']}"
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error executing signal: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def report_signal_result(self, signal_id: str, executor_id: str, 
                            result: str, profit_pct: float = None) -> Dict:
        """
        📊 Reportar resultado de una señal ejecutada
        """
        conn = self.db._get_connection() if self.connected else None
        if not conn:
            return {'success': False, 'error': 'Database no disponible'}
        
        try:
            cursor = conn.cursor(row_factory=_dict_row) if _dict_row else conn.cursor()
            
            cursor.execute('''
                UPDATE signal_executions 
                SET result = %s, profit_pct = %s, closed_at = NOW()
                WHERE signal_id = %s AND executor_id = %s AND result IS NULL
                RETURNING id
            ''', (result, profit_pct, signal_id, executor_id))
            
            if cursor.rowcount == 0:
                return {'success': False, 'error': 'Ejecución no encontrada'}
            
            cursor.execute(
                'SELECT contributor_id, contributor_name FROM community_signals WHERE signal_id = %s',
                (signal_id,)
            )
            signal = cursor.fetchone()
            
            if result == 'success':
                cursor.execute('''
                    UPDATE community_signals 
                    SET success_count = success_count + 1
                    WHERE signal_id = %s
                ''', (signal_id,))
                royalty_points = self.ROYALTY_POINTS['signal_success']
            elif result == 'partial':
                royalty_points = self.ROYALTY_POINTS['signal_partial']
            else:
                cursor.execute('''
                    UPDATE community_signals 
                    SET failure_count = failure_count + 1
                    WHERE signal_id = %s
                ''', (signal_id,))
                royalty_points = self.ROYALTY_POINTS['signal_failure']
            
            cursor.execute('''
                UPDATE community_signals 
                SET royalties_earned = royalties_earned + %s
                WHERE signal_id = %s
            ''', (max(0, royalty_points), signal_id))
            
            self._update_leaderboard(cursor, signal['contributor_id'],
                                    signal['contributor_name'], 
                                    f'signal_{result}')
            
            conn.commit()
            
            if self.reward_system and royalty_points > 0:
                self.reward_system.award_points(
                    signal['contributor_id'],
                    royalty_points,
                    f'royalty:{signal_id}:{result}'
                )
            
            return {
                'success': True,
                'result': result,
                'royalty_points': royalty_points,
                'contributor': signal['contributor_name']
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error reporting signal result: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def get_alpha_leaderboard(self, limit: int = 10) -> List[Dict]:
        """
        🏆 Obtener ranking de mejores contribuidores de señales
        """
        conn = self.db._get_connection() if self.connected else None
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(row_factory=_dict_row) if _dict_row else conn.cursor()
            
            cursor.execute('''
                SELECT 
                    username, signals_shared, signals_successful,
                    total_executions, win_rate, royalty_points,
                    reputation_score, rank_tier
                FROM alpha_leaderboard
                WHERE signals_shared > 0
                ORDER BY royalty_points DESC, win_rate DESC
                LIMIT %s
            ''', (limit,))
            
            leaders = cursor.fetchall()
            
            result = []
            for i, leader in enumerate(leaders, 1):
                leader_dict = dict(leader)
                leader_dict['position'] = i
                result.append(leader_dict)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting leaderboard: {e}")
            return []
        finally:
            conn.close()
    
    def get_user_signals(self, user_id: str) -> Dict:
        """
        📊 Obtener estadísticas de señales de un usuario
        """
        conn = self.db._get_connection() if self.connected else None
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor(row_factory=_dict_row) if _dict_row else conn.cursor()
            
            cursor.execute('''
                SELECT * FROM alpha_leaderboard WHERE user_id = %s
            ''', (user_id,))
            stats = cursor.fetchone()
            
            cursor.execute('''
                SELECT signal_id, symbol, signal_type, confidence,
                       upvotes, downvotes, executions_count, 
                       success_count, failure_count, royalties_earned,
                       status, created_at
                FROM community_signals
                WHERE contributor_id = %s
                ORDER BY created_at DESC
                LIMIT 20
            ''', (user_id,))
            signals = cursor.fetchall()
            
            return {
                'stats': dict(stats) if stats else {},
                'signals': [dict(s) for s in signals]
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user signals: {e}")
            return {}
        finally:
            conn.close()
    
    def _update_leaderboard(self, cursor, user_id: str, username: str, action: str):
        """Actualizar leaderboard del usuario"""
        try:
            cursor.execute('''
                INSERT INTO alpha_leaderboard (user_id, username)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE SET username = EXCLUDED.username
            ''', (user_id, username))
            
            if action == 'signal_shared':
                cursor.execute('''
                    UPDATE alpha_leaderboard 
                    SET signals_shared = signals_shared + 1,
                        last_signal_at = NOW(),
                        updated_at = NOW()
                    WHERE user_id = %s
                ''', (user_id,))
            
            elif action == 'signal_executed':
                cursor.execute('''
                    UPDATE alpha_leaderboard 
                    SET total_executions = total_executions + 1,
                        updated_at = NOW()
                    WHERE user_id = %s
                ''', (user_id,))
            
            elif action == 'signal_success':
                cursor.execute('''
                    UPDATE alpha_leaderboard 
                    SET signals_successful = signals_successful + 1,
                        royalty_points = royalty_points + %s,
                        reputation_score = LEAST(100, reputation_score + 2),
                        updated_at = NOW()
                    WHERE user_id = %s
                ''', (self.ROYALTY_POINTS['signal_success'], user_id))
            
            elif action == 'signal_failure':
                cursor.execute('''
                    UPDATE alpha_leaderboard 
                    SET reputation_score = GREATEST(0, reputation_score - 1),
                        updated_at = NOW()
                    WHERE user_id = %s
                ''', (user_id,))
            
            cursor.execute('''
                UPDATE alpha_leaderboard 
                SET win_rate = CASE 
                    WHEN signals_shared > 0 THEN 
                        ROUND(signals_successful::numeric / signals_shared * 100, 1)
                    ELSE 0 
                END,
                rank_tier = CASE
                    WHEN royalty_points >= 1000 THEN 'Diamond'
                    WHEN royalty_points >= 500 THEN 'Platinum'
                    WHEN royalty_points >= 200 THEN 'Gold'
                    WHEN royalty_points >= 50 THEN 'Silver'
                    ELSE 'Bronze'
                END
                WHERE user_id = %s
            ''', (user_id,))
            
        except Exception as e:
            logger.error(f"Error updating leaderboard: {e}")
    
    def _generate_signal_id(self, user_id: str, signal_data: Dict) -> str:
        """Generar ID único para señal"""
        content = f"{user_id}:{signal_data.get('symbol')}:{signal_data.get('signal_type')}:{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
