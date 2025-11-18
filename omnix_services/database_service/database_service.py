"""
🗄️ OMNIX DATABASE SERVICE ENTERPRISE
Gestión profesional de PostgreSQL con todas las tablas del sistema

CARACTERÍSTICAS:
- PostgreSQL nativo (Neon)
- 8 tablas profesionales
- Balance tracking automático
- Performance metrics institucionales
- Sharia compliance database
"""

import os
import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    import psycopg2
    from psycopg2 import sql
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2 no disponible - Database desactivado")


class DatabaseServiceEnterprise:
    """
    🗄️ SERVICIO ENTERPRISE DE BASE DE DATOS OMNIX
    
    Arquitectura profesional PostgreSQL para:
    - User management
    - Trading history
    - Balance tracking
    - Performance metrics
    - Sharia compliance
    """
    
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        self.connected = False
        
        if not PSYCOPG2_AVAILABLE:
            logger.error("psycopg2 no disponible")
            return
        
        if not self.db_url:
            logger.warning("DATABASE_URL no configurada")
            return
        
        try:
            self._init_tables()
            self.connected = True
            logger.info("🗄️ DatabaseServiceEnterprise conectado a PostgreSQL")
        except Exception as e:
            logger.error(f"Error conectando a DB: {e}")
    
    def health_check(self) -> Dict[str, bool]:
        """Health check del servicio"""
        return {
            'psycopg2_available': PSYCOPG2_AVAILABLE,
            'database_connected': self.connected,
            'database_url_configured': bool(self.db_url)
        }
    
    def _get_connection(self):
        """Obtener conexión a PostgreSQL"""
        if not self.db_url or not PSYCOPG2_AVAILABLE:
            return None
        return psycopg2.connect(self.db_url)
    
    def _init_tables(self):
        """Inicializar todas las tablas del sistema"""
        if not self.db_url or not PSYCOPG2_AVAILABLE:
            return
        
        conn = self._get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            
            # Tabla de usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    language_code TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_trades INTEGER DEFAULT 0,
                    total_profit REAL DEFAULT 0,
                    risk_tolerance TEXT DEFAULT 'medium',
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    whatsapp_number TEXT,
                    notifications_enabled BOOLEAN DEFAULT true
                )
            ''')
            
            # Tabla de precios históricos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prices (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT,
                    price REAL,
                    volume REAL,
                    change_24h REAL,
                    exchange TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de trades ejecutados
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    symbol TEXT,
                    side TEXT,
                    amount REAL,
                    price REAL,
                    total_cost REAL,
                    status TEXT,
                    order_id TEXT,
                    exchange TEXT,
                    profit_loss REAL DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de análisis
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    symbol TEXT,
                    analysis_type TEXT,
                    result TEXT,
                    confidence REAL,
                    recommendation TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de conversaciones IA
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    user_message TEXT,
                    ai_response TEXT,
                    language TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de notificaciones WhatsApp
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS whatsapp_messages (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    recipient TEXT,
                    message TEXT,
                    status TEXT,
                    message_sid TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de validaciones Sharia
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sharia_validations (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT,
                    status TEXT,
                    reasoning TEXT,
                    scholar_consensus INTEGER,
                    uae_approval BOOLEAN,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de balance histórico
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS balance_history (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    exchange TEXT DEFAULT 'kraken',
                    total_usd REAL,
                    btc_balance REAL DEFAULT 0,
                    eth_balance REAL DEFAULT 0,
                    usdt_balance REAL DEFAULT 0,
                    other_balance REAL DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ==========================================
            # PAPER TRADING TABLES - INSTITUTIONAL GRADE
            # ==========================================
            
            # Tabla de balances de paper trading (1 row por usuario)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS paper_trading_balances (
                    user_id TEXT PRIMARY KEY,
                    balance_usd NUMERIC(18,8) DEFAULT 1000000.00,
                    btc_balance NUMERIC(20,10) DEFAULT 0,
                    eth_balance NUMERIC(20,10) DEFAULT 0,
                    available_margin_usd NUMERIC(18,8) DEFAULT 1000000.00,
                    total_trades INTEGER DEFAULT 0,
                    winning_trades INTEGER DEFAULT 0,
                    losing_trades INTEGER DEFAULT 0,
                    total_realized_pnl_usd NUMERIC(18,8) DEFAULT 0,
                    total_unrealized_pnl_usd NUMERIC(18,8) DEFAULT 0,
                    max_drawdown_pct NUMERIC(6,4) DEFAULT 0,
                    sharpe_ratio NUMERIC(8,4) DEFAULT 0,
                    last_mark_to_market_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Índices para paper_trading_balances
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_paper_balances_total_pnl 
                ON paper_trading_balances(total_realized_pnl_usd DESC)
            ''')
            
            # Tabla de trades de paper trading (granular ledger)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS paper_trading_trades (
                    id BIGSERIAL PRIMARY KEY,
                    trade_uuid UUID UNIQUE DEFAULT gen_random_uuid(),
                    user_id TEXT NOT NULL,
                    position_id UUID,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
                    order_type TEXT DEFAULT 'market',
                    status TEXT DEFAULT 'filled',
                    entry_price NUMERIC(18,8) NOT NULL,
                    exit_price NUMERIC(18,8),
                    base_quantity NUMERIC(20,10) NOT NULL,
                    quote_notional_usd NUMERIC(18,8) NOT NULL,
                    fee_bps NUMERIC(6,4) DEFAULT 26.0,
                    fee_usd NUMERIC(18,8) NOT NULL,
                    gross_pnl_usd NUMERIC(18,8) DEFAULT 0,
                    net_realized_pnl_usd NUMERIC(18,8),
                    unrealized_pnl_usd NUMERIC(18,8),
                    opened_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP WITH TIME ZONE,
                    duration_seconds INTEGER,
                    source_strategy TEXT DEFAULT 'auto_trading_bot',
                    notes JSONB,
                    is_paper_trade BOOLEAN DEFAULT TRUE,
                    CONSTRAINT check_exit_price_on_close CHECK (
                        (closed_at IS NULL AND exit_price IS NULL) OR
                        (closed_at IS NOT NULL AND exit_price IS NOT NULL)
                    )
                )
            ''')
            
            # Índices para paper_trading_trades
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_paper_trades_user_opened 
                ON paper_trading_trades(user_id, opened_at DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_paper_trades_open_positions 
                ON paper_trading_trades(user_id, closed_at) WHERE closed_at IS NULL
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_paper_trades_symbol 
                ON paper_trading_trades(symbol)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_paper_trades_opened_at 
                ON paper_trading_trades USING BRIN (opened_at)
            ''')
            
            # ==========================================
            # CONVERSATIONAL BRAIN TABLES - ÚNICO EN EL MUNDO
            # ==========================================
            
            # Tabla de razonamientos pre-trade (el bot explica por qué decide)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trade_reasonings (
                    id BIGSERIAL PRIMARY KEY,
                    trade_uuid UUID UNIQUE DEFAULT gen_random_uuid(),
                    user_id TEXT,
                    trade_id TEXT,
                    order_id TEXT,
                    action TEXT NOT NULL CHECK (action IN ('BUY', 'SELL')),
                    pair TEXT NOT NULL,
                    amount_usd NUMERIC(18,8) NOT NULL,
                    confidence NUMERIC(5,4) NOT NULL,
                    signals JSONB NOT NULL,
                    reasons JSONB NOT NULL,
                    summary TEXT,
                    full_explanation TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_trade_reasonings_user_created 
                ON trade_reasonings(user_id, created_at DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_trade_reasonings_pair 
                ON trade_reasonings(pair)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_trade_reasonings_trade_id 
                ON trade_reasonings(trade_id, created_at DESC)
            ''')
            
            # Tabla de auto-evaluaciones post-trade (el bot se pregunta si fue buena decisión)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trade_evaluations (
                    id BIGSERIAL PRIMARY KEY,
                    evaluation_uuid UUID UNIQUE DEFAULT gen_random_uuid(),
                    trade_id TEXT NOT NULL,
                    trade_reasoning_uuid UUID REFERENCES trade_reasonings(trade_uuid),
                    user_id TEXT,
                    elapsed_minutes INTEGER,
                    original_action TEXT,
                    original_confidence NUMERIC(5,4),
                    result JSONB NOT NULL,
                    was_correct BOOLEAN NOT NULL,
                    learning_points JSONB,
                    adjustments_suggested JSONB,
                    full_review TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_trade_evaluations_user_created 
                ON trade_evaluations(user_id, created_at DESC)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_trade_evaluations_correctness 
                ON trade_evaluations(was_correct)
            ''')
            
            # Tabla de evaluaciones pendientes (sistema robusto sin threads)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pending_evaluations (
                    id BIGSERIAL PRIMARY KEY,
                    trade_id TEXT NOT NULL,
                    trade_reasoning_uuid UUID,
                    user_id TEXT,
                    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed')),
                    result JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP WITH TIME ZONE
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_pending_evaluations_scheduled 
                ON pending_evaluations(scheduled_at) WHERE status = 'pending'
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_pending_evaluations_trade 
                ON pending_evaluations(trade_id, status)
            ''')
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("✅ PostgreSQL: 13 tablas inicializadas (incluye Cerebro Conversacional ÚNICO)")
            
        except Exception as e:
            logger.error(f"Error inicializando tablas: {e}")
            if conn:
                conn.close()
    
    def save_balance_snapshot(self, user_id: str, balance_data: Dict) -> bool:
        """
        Guardar snapshot del balance
        
        Args:
            user_id: ID del usuario
            balance_data: Dict con total_usd, btc_balance, etc.
            
        Returns:
            True si exitoso, False si falla
        """
        if not self.connected:
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO balance_history (user_id, exchange, total_usd, btc_balance, eth_balance, usdt_balance, other_balance)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (
                user_id,
                balance_data.get('exchange', 'kraken'),
                balance_data.get('total_usd', 0),
                balance_data.get('btc_balance', 0),
                balance_data.get('eth_balance', 0),
                balance_data.get('usdt_balance', 0),
                balance_data.get('other_balance', 0)
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"✅ Balance snapshot guardado: ${balance_data.get('total_usd', 0):,.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando balance: {e}")
            return False
    
    def get_balance_history(self, user_id: str, days: int = 30) -> List[Dict]:
        """
        Obtener historial de balance
        
        Args:
            user_id: ID del usuario
            days: Días a consultar
            
        Returns:
            Lista de balances históricos
        """
        if not self.connected:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT total_usd, btc_balance, eth_balance, usdt_balance, other_balance, timestamp
                FROM balance_history
                WHERE user_id = %s AND timestamp >= NOW() - INTERVAL '1 day' * %s
                ORDER BY timestamp ASC
            ''', (user_id, days))
            
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            history = []
            for row in rows:
                history.append({
                    'total_usd': float(row[0]) if row[0] else 0,
                    'btc_balance': float(row[1]) if row[1] else 0,
                    'eth_balance': float(row[2]) if row[2] else 0,
                    'usdt_balance': float(row[3]) if row[3] else 0,
                    'other_balance': float(row[4]) if row[4] else 0,
                    'timestamp': row[5].isoformat() if row[5] else None
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error obteniendo history: {e}")
            return []
    
    def calculate_performance_metrics(self, history: List[Dict]) -> Optional[Dict]:
        """
        Calcular métricas de performance institucionales
        
        Args:
            history: Lista de balance histórico
            
        Returns:
            Dict con ROI, CAGR, Max Drawdown, etc.
        """
        if not history or len(history) < 2:
            return None
        
        try:
            initial_balance = history[0]['total_usd']
            current_balance = history[-1]['total_usd']
            
            # ROI
            roi_percent = ((current_balance - initial_balance) / initial_balance) * 100 if initial_balance > 0 else 0
            
            # Profit/Loss
            profit_loss = current_balance - initial_balance
            
            # Max Drawdown (peak-to-valley)
            peak = history[0]['total_usd']
            max_drawdown = 0
            
            for entry in history:
                balance = entry['total_usd']
                if balance > peak:
                    peak = balance
                if peak > 0:
                    current_drawdown = ((peak - balance) / peak) * 100
                    if current_drawdown > max_drawdown:
                        max_drawdown = current_drawdown
            
            # Max balance
            max_balance = max([h['total_usd'] for h in history])
            
            # Días tracking
            start_date = datetime.fromisoformat(history[0]['timestamp'])
            end_date = datetime.fromisoformat(history[-1]['timestamp'])
            days_tracked = (end_date - start_date).days
            
            # CAGR anualizado
            if days_tracked > 0:
                years = days_tracked / 365.25
                cagr = ((current_balance / initial_balance) ** (1/years) - 1) * 100 if years > 0 and initial_balance > 0 else 0
            else:
                cagr = 0
            
            return {
                'initial_balance': initial_balance,
                'current_balance': current_balance,
                'roi_percent': roi_percent,
                'profit_loss': profit_loss,
                'max_balance': max_balance,
                'max_drawdown_percent': max_drawdown,
                'days_tracked': days_tracked,
                'cagr_annual': cagr
            }
            
        except Exception as e:
            logger.error(f"Error calculando métricas: {e}")
            return None
    
    def save_trade(self, trade_data: Dict) -> bool:
        """Guardar trade ejecutado"""
        if not self.connected:
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO trades (user_id, symbol, side, amount, price, total_cost, status, order_id, exchange, profit_loss)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                trade_data.get('user_id'),
                trade_data.get('symbol'),
                trade_data.get('side'),
                trade_data.get('amount'),
                trade_data.get('price'),
                trade_data.get('total_cost'),
                trade_data.get('status'),
                trade_data.get('order_id'),
                trade_data.get('exchange', 'kraken'),
                trade_data.get('profit_loss', 0)
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"✅ Trade guardado: {trade_data.get('symbol')} {trade_data.get('side')}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando trade: {e}")
            return False
    
    def save_conversation(self, user_id: str, user_message: str, ai_response: str, language: str = 'es') -> bool:
        """Guardar conversación IA"""
        if not self.connected:
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversations (user_id, user_message, ai_response, language)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, user_message, ai_response, language))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error guardando conversación: {e}")
            return False
    
    def save_trade_reasoning(self, reasoning: Dict) -> Optional[str]:
        """
        Guardar razonamiento pre-trade del Cerebro Conversacional
        
        Args:
            reasoning: Dict con razonamiento completo
            
        Returns:
            UUID del razonamiento guardado, None si falla
        """
        if not self.connected:
            return None
        
        try:
            import json
            conn = self._get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO trade_reasonings (
                    user_id, action, pair, amount_usd, confidence,
                    signals, reasons, summary, full_explanation
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING trade_uuid
            ''', (
                reasoning.get('user_id', 'harold'),
                reasoning.get('action', 'BUY'),
                reasoning.get('pair', 'BTC/USD'),
                reasoning.get('amount_usd', 0),
                reasoning.get('confidence', 0),
                json.dumps(reasoning.get('signals', {})),
                json.dumps(reasoning.get('reasons', [])),
                reasoning.get('summary', ''),
                reasoning.get('full_explanation', '')
            ))
            
            trade_uuid = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.debug(f"🧠 Razonamiento guardado: {trade_uuid}")
            return str(trade_uuid)
            
        except Exception as e:
            logger.error(f"Error guardando razonamiento: {e}")
            return None
    
    def save_trade_evaluation(self, evaluation: Dict) -> Optional[str]:
        """
        Guardar auto-evaluación post-trade del Cerebro Conversacional
        
        Args:
            evaluation: Dict con evaluación completa
            
        Returns:
            UUID de la evaluación guardada, None si falla
        """
        if not self.connected:
            return None
        
        try:
            import json
            conn = self._get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO trade_evaluations (
                    trade_id, user_id, elapsed_minutes, original_action,
                    original_confidence, result, was_correct,
                    learning_points, adjustments_suggested, full_review
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING evaluation_uuid
            ''', (
                evaluation.get('trade_id', ''),
                evaluation.get('user_id', 'harold'),
                evaluation.get('elapsed_minutes', 30),
                evaluation.get('original_action', 'BUY'),
                evaluation.get('original_confidence', 0),
                json.dumps(evaluation.get('result', {})),
                evaluation.get('was_correct', False),
                json.dumps(evaluation.get('learning_points', [])),
                json.dumps(evaluation.get('adjustments_suggested', [])),
                evaluation.get('full_review', '')
            ))
            
            evaluation_uuid = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.debug(f"🔍 Evaluación guardada: {evaluation_uuid}")
            return str(evaluation_uuid)
            
        except Exception as e:
            logger.error(f"Error guardando evaluación: {e}")
            return None
    
    def get_recent_reasonings(self, user_id: str = 'harold', limit: int = 10) -> List[Dict]:
        """
        Obtener razonamientos recientes
        
        Args:
            user_id: ID del usuario
            limit: Número de razonamientos a obtener
            
        Returns:
            Lista de razonamientos
        """
        if not self.connected:
            return []
        
        try:
            import json
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    trade_uuid, action, pair, amount_usd, confidence,
                    signals, reasons, summary, full_explanation, created_at
                FROM trade_reasonings
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            ''', (user_id, limit))
            
            rows = cursor.fetchall()
            
            reasonings = []
            for row in rows:
                reasonings.append({
                    'trade_uuid': str(row[0]),
                    'action': row[1],
                    'pair': row[2],
                    'amount_usd': float(row[3]),
                    'confidence': float(row[4]),
                    'signals': json.loads(row[5]) if row[5] else {},
                    'reasons': json.loads(row[6]) if row[6] else [],
                    'summary': row[7],
                    'full_explanation': row[8],
                    'created_at': row[9].isoformat() if row[9] else None
                })
            
            cursor.close()
            conn.close()
            return reasonings
            
        except Exception as e:
            logger.error(f"Error obteniendo razonamientos: {e}")
            return []
    
    def get_learning_summary(self, user_id: str = 'harold') -> Dict:
        """
        Obtener resumen de aprendizajes del Cerebro Conversacional
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict con estadísticas de aprendizaje
        """
        if not self.connected:
            return {}
        
        try:
            conn = self._get_connection()
            if not conn:
                return {}
            
            cursor = conn.cursor()
            
            # Total evaluaciones
            cursor.execute('''
                SELECT COUNT(*) FROM trade_evaluations WHERE user_id = %s
            ''', (user_id,))
            total = cursor.fetchone()[0] or 0
            
            # Trades correctos
            cursor.execute('''
                SELECT COUNT(*) FROM trade_evaluations WHERE user_id = %s AND was_correct = TRUE
            ''', (user_id,))
            correct = cursor.fetchone()[0] or 0
            
            # Success rate
            success_rate = (correct / total * 100) if total > 0 else 0
            
            cursor.close()
            conn.close()
            
            return {
                'total_evaluations': total,
                'correct_trades': correct,
                'incorrect_trades': total - correct,
                'success_rate': success_rate,
                'performance': 'EXCELENTE' if success_rate > 70 else 'BUENO' if success_rate > 50 else 'MEJORABLE'
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo learning summary: {e}")
            return {}
    
    def schedule_trade_evaluation(self, trade_id: str, reasoning_uuid: Optional[str], user_id: str = 'harold', minutes_delay: int = 30) -> bool:
        """
        Programar evaluación post-trade (sistema robusto sin threads)
        
        Args:
            trade_id: ID del trade a evaluar
            reasoning_uuid: UUID del razonamiento original
            user_id: ID del usuario
            minutes_delay: Minutos para esperar antes de evaluar
            
        Returns:
            True si se programó correctamente
        """
        if not self.connected:
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Calcular scheduled_at
            scheduled_at = datetime.now() + timedelta(minutes=minutes_delay)
            
            cursor.execute('''
                INSERT INTO pending_evaluations (trade_id, trade_reasoning_uuid, user_id, scheduled_at)
                VALUES (%s, %s, %s, %s)
            ''', (trade_id, reasoning_uuid, user_id, scheduled_at))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"⏰ Evaluación programada para trade {trade_id} en {minutes_delay} minutos")
            return True
            
        except Exception as e:
            logger.error(f"Error programando evaluación: {e}")
            return False
    
    def get_due_evaluations(self) -> List[Dict]:
        """
        Obtener evaluaciones que ya es hora de procesar
        
        Returns:
            Lista de evaluaciones pendientes
        """
        if not self.connected:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, trade_id, trade_reasoning_uuid, user_id, scheduled_at
                FROM pending_evaluations
                WHERE status = 'pending' AND scheduled_at <= CURRENT_TIMESTAMP
                ORDER BY scheduled_at ASC
                LIMIT 10
            ''')
            
            rows = cursor.fetchall()
            
            evaluations = []
            for row in rows:
                evaluations.append({
                    'id': row[0],
                    'trade_id': row[1],
                    'reasoning_uuid': str(row[2]) if row[2] else None,
                    'user_id': row[3],
                    'scheduled_at': row[4].isoformat() if row[4] else None
                })
            
            cursor.close()
            conn.close()
            return evaluations
            
        except Exception as e:
            logger.error(f"Error obteniendo evaluaciones pendientes: {e}")
            return []
    
    def mark_evaluation_completed(self, evaluation_id: int, result: Dict) -> bool:
        """
        Marcar evaluación como completada
        
        Args:
            evaluation_id: ID de la evaluación pendiente
            result: Resultado de la evaluación
            
        Returns:
            True si se marcó correctamente
        """
        if not self.connected:
            return False
        
        try:
            import json
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE pending_evaluations
                SET status = 'completed', result = %s, processed_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (json.dumps(result), evaluation_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error marcando evaluación como completada: {e}")
            return False
