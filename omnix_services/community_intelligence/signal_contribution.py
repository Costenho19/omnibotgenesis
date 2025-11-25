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
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import json
import hashlib

logger = logging.getLogger(__name__)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


class SignalContributionManager:
    """
    🚀 GESTOR DE SEÑALES COMUNITARIAS
    
    Sistema premium para crowdsourcing de alpha:
    - Usuarios comparten señales de trading
    - Sistema trackea performance de cada señal
    - Royalties automáticos para contribuidores exitosos
    - Ranking de mejores "alpha hunters"
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
    
    def __init__(self, reward_system=None):
        self.db_url = os.environ.get('DATABASE_URL')
        self.connected = False
        self.reward_system = reward_system
        
        if self.db_url and PSYCOPG2_AVAILABLE:
            try:
                self._init_tables()
                self.connected = True
                logger.info("✅ SignalContributionManager conectado")
            except Exception as e:
                logger.error(f"❌ Error inicializando signal tables: {e}")
        else:
            logger.warning("⚠️ Database no disponible para Signal Contribution")
    
    def _get_connection(self):
        """Obtener conexión PostgreSQL"""
        if not self.db_url or not PSYCOPG2_AVAILABLE:
            return None
        return psycopg2.connect(self.db_url)
    
    def _init_tables(self):
        """Crear tablas para señales comunitarias"""
        conn = self._get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS community_signals (
                    id SERIAL PRIMARY KEY,
                    signal_id TEXT UNIQUE NOT NULL,
                    contributor_id TEXT NOT NULL,
                    contributor_name TEXT,
                    
                    -- Señal
                    symbol TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    entry_price REAL,
                    target_price REAL,
                    stop_loss REAL,
                    timeframe TEXT DEFAULT '1h',
                    confidence INTEGER DEFAULT 50,
                    
                    -- Análisis
                    reasoning TEXT,
                    indicators_used TEXT,
                    market_condition TEXT,
                    
                    -- Tracking
                    status TEXT DEFAULT 'active',
                    executions_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    
                    -- Votos
                    upvotes INTEGER DEFAULT 0,
                    downvotes INTEGER DEFAULT 0,
                    
                    -- Resultado final
                    final_result TEXT,
                    actual_return REAL,
                    closed_at TIMESTAMP,
                    
                    -- Royalties
                    royalties_earned INTEGER DEFAULT 0,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signal_executions (
                    id SERIAL PRIMARY KEY,
                    signal_id TEXT NOT NULL,
                    executor_id TEXT NOT NULL,
                    executor_name TEXT,
                    
                    entry_price REAL,
                    exit_price REAL,
                    result TEXT,
                    profit_pct REAL,
                    
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    
                    feedback TEXT,
                    rating INTEGER
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signal_votes (
                    id SERIAL PRIMARY KEY,
                    signal_id TEXT NOT NULL,
                    voter_id TEXT NOT NULL,
                    vote_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(signal_id, voter_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alpha_leaderboard (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT UNIQUE NOT NULL,
                    username TEXT,
                    
                    -- Stats
                    signals_shared INTEGER DEFAULT 0,
                    signals_successful INTEGER DEFAULT 0,
                    total_executions INTEGER DEFAULT 0,
                    win_rate REAL DEFAULT 0,
                    avg_return REAL DEFAULT 0,
                    
                    -- Puntos
                    royalty_points INTEGER DEFAULT 0,
                    reputation_score REAL DEFAULT 50,
                    
                    -- Ranking
                    rank_position INTEGER,
                    rank_tier TEXT DEFAULT 'Bronze',
                    
                    last_signal_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("✅ Signal Contribution tables created")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error creating signal tables: {e}")
            raise
        finally:
            conn.close()
    
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
        conn = self._get_connection()
        if not conn:
            return {'success': False, 'error': 'Database no disponible'}
        
        try:
            cursor = conn.cursor()
            
            signal_id = self._generate_signal_id(user_id, signal_data)
            
            symbol = signal_data.get('symbol', 'BTC').upper()
            signal_type = signal_data.get('signal_type', 'LONG').upper()
            
            if signal_type not in self.SIGNAL_TYPES:
                return {'success': False, 'error': f'Tipo inválido. Usa: {self.SIGNAL_TYPES}'}
            
            expires_hours = 24 if signal_data.get('timeframe', '1h') in ['1m', '5m', '15m'] else 72
            expires_at = datetime.now() + timedelta(hours=expires_hours)
            
            cursor.execute('''
                INSERT INTO community_signals 
                (signal_id, contributor_id, contributor_name, symbol, signal_type,
                 entry_price, target_price, stop_loss, timeframe, confidence,
                 reasoning, indicators_used, market_condition, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                signal_id, user_id, username, symbol, signal_type,
                signal_data.get('entry_price'),
                signal_data.get('target_price'),
                signal_data.get('stop_loss'),
                signal_data.get('timeframe', '1h'),
                signal_data.get('confidence', 50),
                signal_data.get('reasoning'),
                signal_data.get('indicators'),
                signal_data.get('market_condition'),
                expires_at
            ))
            
            self._update_leaderboard(cursor, user_id, username, 'signal_shared')
            
            conn.commit()
            
            points = self.ROYALTY_POINTS['signal_shared']
            if self.reward_system:
                self.reward_system.award_points(user_id, points, 'signal_shared')
            
            logger.info(f"✅ Señal compartida: {signal_id} por {username}")
            
            return {
                'success': True,
                'signal_id': signal_id,
                'symbol': symbol,
                'signal_type': signal_type,
                'expires_at': expires_at.isoformat(),
                'points_earned': points
            }
            
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            return {'success': False, 'error': 'Ya compartiste una señal similar recientemente'}
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Error sharing signal: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()
    
    def get_community_signals(self, limit: int = 10, symbol: str = None) -> List[Dict]:
        """
        📊 Obtener señales activas de la comunidad
        """
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = '''
                SELECT 
                    signal_id, contributor_name, symbol, signal_type,
                    entry_price, target_price, stop_loss, timeframe,
                    confidence, reasoning, upvotes, downvotes,
                    executions_count, created_at, expires_at,
                    CASE 
                        WHEN executions_count > 0 THEN 
                            ROUND(success_count::numeric / executions_count * 100, 1)
                        ELSE 0 
                    END as success_rate
                FROM community_signals
                WHERE status = 'active' 
                  AND expires_at > NOW()
            '''
            
            params = []
            if symbol:
                query += ' AND symbol = %s'
                params.append(symbol.upper())
            
            query += ' ORDER BY upvotes DESC, created_at DESC LIMIT %s'
            params.append(limit)
            
            cursor.execute(query, params)
            signals = cursor.fetchall()
            
            return [dict(s) for s in signals]
            
        except Exception as e:
            logger.error(f"❌ Error getting community signals: {e}")
            return []
        finally:
            conn.close()
    
    def vote_signal(self, signal_id: str, voter_id: str, vote_type: str) -> Dict:
        """
        👍/👎 Votar una señal
        """
        conn = self._get_connection()
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
        conn = self._get_connection()
        if not conn:
            return {'success': False, 'error': 'Database no disponible'}
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
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
        conn = self._get_connection()
        if not conn:
            return {'success': False, 'error': 'Database no disponible'}
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
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
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
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
        conn = self._get_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
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
