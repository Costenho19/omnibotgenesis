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
        
        # 🔍 DEBUG LOGGING MEJORADO PARA RAILWAY
        logger.info("=" * 70)
        logger.info("🚀 INICIANDO DatabaseServiceEnterprise")
        logger.info(f"📊 PSYCOPG2_AVAILABLE: {PSYCOPG2_AVAILABLE}")
        
        if self.db_url:
            # Mostrar primeros 30 caracteres para confirmar presencia (sin exponer credenciales)
            db_url_preview = self.db_url[:30] + "..." if len(self.db_url) > 30 else self.db_url
            logger.info(f"✅ DATABASE_URL detectada: {db_url_preview}")
            logger.info(f"📏 DATABASE_URL length: {len(self.db_url)} caracteres")
        else:
            logger.error("❌ DATABASE_URL NO ENCONTRADA en os.environ")
            logger.info(f"🔑 Variables disponibles: {', '.join(sorted(os.environ.keys())[:10])}")
            logger.info("=" * 70)
            return
        
        if not PSYCOPG2_AVAILABLE:
            logger.error("❌ psycopg2 NO DISPONIBLE - No se puede conectar a PostgreSQL")
            logger.info("=" * 70)
            return
        
        try:
            logger.info("🔌 Intentando conectar a PostgreSQL...")
            self._init_tables()
            self.connected = True
            logger.info("✅ PostgreSQL: 13 tablas inicializadas")
            logger.info("🗄️ DatabaseServiceEnterprise conectado exitosamente")
            logger.info("=" * 70)
        except Exception as e:
            logger.error("=" * 70)
            logger.error(f"❌ ERROR CONECTANDO A POSTGRESQL:")
            logger.error(f"   Tipo: {type(e).__name__}")
            logger.error(f"   Mensaje: {str(e)}")
            import traceback
            logger.error(f"   Traceback completo:\n{traceback.format_exc()}")
            logger.error("=" * 70)
    
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
            
            # ==========================================
            # COMMUNITY INTELLIGENCE TABLES - CROWDSOURCING
            # ==========================================
            
            # Tabla de feedback comunitario
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
            
            # Tabla de votos de estrategias
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
            
            # Tabla de propuestas de mejora
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
            
            # Tabla de contribuciones de usuarios
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
            
            # Tabla de patrones detectados por AI
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
            
            # Índices para Community Intelligence
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_user ON community_feedback(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_strategy ON community_feedback(strategy)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_result ON community_feedback(result)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_votes_strategy ON strategy_votes(strategy)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_patterns_status ON detected_patterns(status)')
            
            # ==========================================
            # SIGNAL CONTRIBUTION TABLES - CROWDSOURCING ALPHA
            # ==========================================
            
            # Tabla de señales compartidas por usuarios
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
            
            # Tabla de ejecuciones de señales
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
            
            # Tabla de votos de señales
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
            
            # Tabla de leaderboard de alpha
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
            
            # ==========================================
            # AI RISK GUARDIAN TABLE - MONITORING
            # ==========================================
            
            # Tabla de eventos del AI Risk Guardian
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_guardian_events (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
                    risk_type VARCHAR(50) NOT NULL,
                    risk_level VARCHAR(20) NOT NULL,
                    description TEXT NOT NULL,
                    action_taken TEXT NOT NULL,
                    metadata JSONB,
                    user_id BIGINT
                )
            ''')
            
            # Índices para risk_guardian_events
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_events_timestamp ON risk_guardian_events(timestamp DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_risk_events_type ON risk_guardian_events(risk_type)')
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("✅ PostgreSQL: 23 tablas inicializadas (Core + Paper Trading + Cerebro + Community Intelligence + Signal Contribution + Risk Guardian)")
            
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
    
    def get_conversation_history(self, chat_id: int, limit: int = 10) -> list:
        """
        Obtener historial de conversación desde PostgreSQL (PERSISTENTE)
        
        Args:
            chat_id: ID del chat
            limit: Número de pares de mensajes a retornar (default: 10)
            
        Returns:
            Lista de diccionarios con {'user': str, 'ai': str, 'timestamp': str}
        """
        if not self.connected:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_message, ai_response, timestamp 
                FROM conversations 
                WHERE user_id = %s 
                ORDER BY timestamp DESC 
                LIMIT %s
            ''', (str(chat_id), limit))
            
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Convertir a formato esperado (más reciente primero, luego invertir)
            history = []
            for row in reversed(rows):  # Invertir para tener cronológico
                history.append({
                    'user': row[0],
                    'ai': row[1],
                    'timestamp': row[2].isoformat() if row[2] else None
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            return []
    
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
    
    # ==========================================
    # COMMUNITY INTELLIGENCE DATA ACCESS LAYER
    # ==========================================
    
    def submit_community_feedback(self, user_id: str, username: str, feedback_data: Dict) -> Dict:
        """Registrar feedback comunitario"""
        if not self.connected:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            conn = self._get_connection()
            if not conn:
                return {'success': False, 'error': 'Connection failed'}
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO community_feedback 
                (user_id, username, feedback_type, signal_type, strategy, symbol, 
                 result, market_condition, btc_price, volatility, timeframe, comment)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                user_id, username, feedback_data.get('feedback_type'), 
                feedback_data.get('signal_type'), feedback_data.get('strategy'),
                feedback_data.get('symbol'), feedback_data.get('result'),
                feedback_data.get('market_condition'), feedback_data.get('btc_price'),
                feedback_data.get('volatility'), feedback_data.get('timeframe'),
                feedback_data.get('comment')
            ))
            
            feedback_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            return {'success': True, 'feedback_id': feedback_id}
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_community_feedback(self, strategy: str = None, limit: int = 50) -> List[Dict]:
        """Obtener feedback comunitario"""
        if not self.connected:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            
            if strategy:
                cursor.execute('''
                    SELECT * FROM community_feedback 
                    WHERE strategy = %s 
                    ORDER BY created_at DESC LIMIT %s
                ''', (strategy, limit))
            else:
                cursor.execute('''
                    SELECT * FROM community_feedback 
                    ORDER BY created_at DESC LIMIT %s
                ''', (limit,))
            
            rows = cursor.fetchall()
            feedback_list = []
            
            for row in rows:
                feedback_list.append({
                    'id': row[0], 'user_id': row[1], 'username': row[2],
                    'feedback_type': row[3], 'strategy': row[5], 'result': row[7]
                })
            
            cursor.close()
            conn.close()
            return feedback_list
            
        except Exception as e:
            logger.error(f"Error getting feedback: {e}")
            return []
    
    def vote_strategy(self, user_id: str, strategy: str, vote: int, reason: str = None, market_condition: str = None) -> Dict:
        """Votar por una estrategia con condición de mercado"""
        if not self.connected:
            return {'success': False}
        
        try:
            conn = self._get_connection()
            if not conn:
                return {'success': False}
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO strategy_votes (user_id, strategy, vote, reason, market_condition, vote_date)
                VALUES (%s, %s, %s, %s, %s, CURRENT_DATE)
                ON CONFLICT (user_id, strategy, vote_date) 
                DO UPDATE SET vote = EXCLUDED.vote, reason = EXCLUDED.reason, market_condition = EXCLUDED.market_condition
                RETURNING id
            ''', (user_id, strategy, vote, reason, market_condition))
            
            vote_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            return {'success': True, 'vote_id': vote_id}
            
        except Exception as e:
            logger.error(f"Error voting strategy: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_user_contributions(self, user_id: str, username: str, points: int, contribution_type: str = 'generic') -> bool:
        """
        Actualizar contribuciones del usuario (puntos + contadores específicos)
        
        Args:
            user_id: ID del usuario
            username: Nombre del usuario
            points: Puntos a agregar
            contribution_type: 'feedback' | 'vote' | 'proposal' | 'helpful_feedback' | 'proposal_accepted' | 'generic'
        
        Counters updated based on contribution_type:
            - 'feedback' → total_feedback +1, points +10
            - 'vote' → total_votes +1, points +5
            - 'proposal' → proposals_submitted +1, points +25
            - 'helpful_feedback' → helpful_feedback +1, points +15
            - 'proposal_accepted' → proposals_accepted +1, points +50
        """
        if not self.connected:
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Actualizar TODOS los contadores según tipo de contribución
            cursor.execute('''
                INSERT INTO user_contributions (
                    user_id, username, 
                    total_feedback, helpful_feedback, total_votes, 
                    proposals_submitted, proposals_accepted,
                    contribution_points, first_contribution
                )
                VALUES (
                    %s, %s,
                    CASE WHEN %s = 'feedback' THEN 1 ELSE 0 END,
                    CASE WHEN %s = 'helpful_feedback' THEN 1 ELSE 0 END,
                    CASE WHEN %s = 'vote' THEN 1 ELSE 0 END,
                    CASE WHEN %s = 'proposal' THEN 1 ELSE 0 END,
                    CASE WHEN %s = 'proposal_accepted' THEN 1 ELSE 0 END,
                    %s, CURRENT_TIMESTAMP
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    username = COALESCE(EXCLUDED.username, user_contributions.username),
                    total_feedback = user_contributions.total_feedback + 
                        CASE WHEN %s = 'feedback' THEN 1 ELSE 0 END,
                    helpful_feedback = user_contributions.helpful_feedback + 
                        CASE WHEN %s = 'helpful_feedback' THEN 1 ELSE 0 END,
                    total_votes = user_contributions.total_votes + 
                        CASE WHEN %s = 'vote' THEN 1 ELSE 0 END,
                    proposals_submitted = user_contributions.proposals_submitted + 
                        CASE WHEN %s = 'proposal' THEN 1 ELSE 0 END,
                    proposals_accepted = user_contributions.proposals_accepted + 
                        CASE WHEN %s = 'proposal_accepted' THEN 1 ELSE 0 END,
                    contribution_points = user_contributions.contribution_points + %s,
                    last_contribution = CURRENT_TIMESTAMP,
                    contribution_level = CASE 
                        WHEN user_contributions.contribution_points + %s >= 1000 THEN 'Experto'
                        WHEN user_contributions.contribution_points + %s >= 500 THEN 'Avanzado'
                        WHEN user_contributions.contribution_points + %s >= 100 THEN 'Intermedio'
                        ELSE 'Novato'
                    END
            ''', (
                user_id, username,
                contribution_type, contribution_type, contribution_type, contribution_type, contribution_type,
                points,
                contribution_type, contribution_type, contribution_type, contribution_type, contribution_type,
                points, points, points, points
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating contributions: {e}")
            return False
    
    def submit_proposal(self, user_id: str, username: str, proposal_data: Dict) -> Dict:
        """Enviar propuesta de mejora"""
        if not self.connected:
            return {'success': False, 'error': 'Database not available'}
        
        # Validación de campos requeridos
        required_fields = ['proposal_type', 'title', 'description']
        for field in required_fields:
            if field not in proposal_data:
                return {'success': False, 'error': f'Missing required field: {field}'}
        
        try:
            conn = self._get_connection()
            if not conn:
                return {'success': False, 'error': 'Connection failed'}
            
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
            conn.commit()
            cursor.close()
            conn.close()
            
            return {'success': True, 'proposal_id': proposal_id}
            
        except Exception as e:
            logger.error(f"Error submitting proposal: {e}")
            return {'success': False, 'error': str(e)}
    
    # ==========================================
    # SIGNAL CONTRIBUTION DATA ACCESS LAYER
    # ==========================================
    
    def save_community_signal(self, signal_data: Dict) -> Dict:
        """Guardar señal compartida por usuario"""
        if not self.connected:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            conn = self._get_connection()
            if not conn:
                return {'success': False, 'error': 'Connection failed'}
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO community_signals 
                (signal_id, contributor_id, contributor_name, symbol, signal_type,
                 entry_price, target_price, stop_loss, timeframe, confidence,
                 reasoning, indicators_used, market_condition)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                signal_data.get('signal_id'), signal_data.get('contributor_id'),
                signal_data.get('contributor_name'), signal_data.get('symbol'),
                signal_data.get('signal_type'), signal_data.get('entry_price'),
                signal_data.get('target_price'), signal_data.get('stop_loss'),
                signal_data.get('timeframe'), signal_data.get('confidence'),
                signal_data.get('reasoning'), signal_data.get('indicators_used'),
                signal_data.get('market_condition')
            ))
            
            signal_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            return {'success': True, 'id': signal_id}
            
        except Exception as e:
            logger.error(f"Error saving signal: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_community_signals(self, status: str = 'active', limit: int = 20) -> List[Dict]:
        """Obtener señales comunitarias"""
        if not self.connected:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            cursor.execute('''
                SELECT signal_id, contributor_name, symbol, signal_type,
                       entry_price, target_price, confidence, upvotes, downvotes
                FROM community_signals 
                WHERE status = %s 
                ORDER BY created_at DESC LIMIT %s
            ''', (status, limit))
            
            rows = cursor.fetchall()
            signals = []
            
            for row in rows:
                signals.append({
                    'signal_id': row[0], 'contributor': row[1], 'symbol': row[2],
                    'type': row[3], 'entry': row[4], 'target': row[5],
                    'confidence': row[6], 'upvotes': row[7], 'downvotes': row[8]
                })
            
            cursor.close()
            conn.close()
            return signals
            
        except Exception as e:
            logger.error(f"Error getting signals: {e}")
            return []
    
    def update_signal_votes(self, signal_id: str, vote_type: str) -> bool:
        """Actualizar votos de una señal"""
        if not self.connected:
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            if vote_type == 'upvote':
                cursor.execute('''
                    UPDATE community_signals 
                    SET upvotes = upvotes + 1 
                    WHERE signal_id = %s
                ''', (signal_id,))
            else:
                cursor.execute('''
                    UPDATE community_signals 
                    SET downvotes = downvotes + 1 
                    WHERE signal_id = %s
                ''', (signal_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating signal votes: {e}")
            return False
    
    # ==========================================
    # RISK GUARDIAN DATA ACCESS LAYER
    # ==========================================
    
    def log_risk_event(self, risk_type: str, risk_level: str, description: str, 
                       action_taken: str, metadata: Dict = None, user_id: int = None) -> bool:
        """Registrar evento del AI Risk Guardian"""
        if not self.connected:
            return False
        
        try:
            import json
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO risk_guardian_events 
                (risk_type, risk_level, description, action_taken, metadata, user_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (risk_type, risk_level, description, action_taken, 
                  json.dumps(metadata) if metadata else None, user_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error logging risk event: {e}")
            return False
    
    def get_risk_events(self, limit: int = 50, risk_type: str = None) -> List[Dict]:
        """Obtener eventos de riesgo"""
        if not self.connected:
            return []
        
        try:
            import json
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            
            if risk_type:
                cursor.execute('''
                    SELECT timestamp, risk_type, risk_level, description, action_taken
                    FROM risk_guardian_events 
                    WHERE risk_type = %s
                    ORDER BY timestamp DESC LIMIT %s
                ''', (risk_type, limit))
            else:
                cursor.execute('''
                    SELECT timestamp, risk_type, risk_level, description, action_taken
                    FROM risk_guardian_events 
                    ORDER BY timestamp DESC LIMIT %s
                ''', (limit,))
            
            rows = cursor.fetchall()
            events = []
            
            for row in rows:
                events.append({
                    'timestamp': row[0].isoformat() if row[0] else None,
                    'risk_type': row[1], 'risk_level': row[2],
                    'description': row[3], 'action_taken': row[4]
                })
            
            cursor.close()
            conn.close()
            return events
            
        except Exception as e:
            logger.error(f"Error getting risk events: {e}")
            return []
    
    # ==========================================
    # COMMUNITY ANALYZER DATA ACCESS LAYER
    # ==========================================
    
    def fetch_feedback_patterns(self, since_date, min_samples: int = 5) -> List[Dict]:
        """Obtener patrones agregados de feedback comunitario"""
        if not self.connected:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
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
            
            rows = cursor.fetchall()
            patterns = []
            
            for row in rows:
                patterns.append({
                    'strategy': row[0],
                    'market_condition': row[1],
                    'volatility': row[2],
                    'result': row[3],
                    'count': row[4]
                })
            
            cursor.close()
            conn.close()
            return patterns
            
        except Exception as e:
            logger.error(f"Error fetching feedback patterns: {e}")
            return []
    
    def upsert_detected_pattern(self, pattern: Dict) -> bool:
        """Guardar o actualizar patrón detectado"""
        if not self.connected:
            return False
        
        try:
            conn = self._get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Verificar si ya existe
            cursor.execute('''
                SELECT pattern_id FROM detected_patterns 
                WHERE pattern_type = %s 
                AND affected_strategy = %s 
                AND market_condition = %s
                AND status = 'detected'
            ''', (pattern.get('pattern_type'), pattern.get('affected_strategy'), 
                  pattern.get('market_condition')))
            
            existing = cursor.fetchone()
            
            import json
            if existing:
                # Actualizar existente
                cursor.execute('''
                    UPDATE detected_patterns SET
                        confidence = %s,
                        sample_size = %s,
                        failure_rate = %s,
                        suggestion = %s,
                        metadata = %s,
                        updated_at = NOW()
                    WHERE pattern_id = %s
                ''', (pattern.get('confidence'), pattern.get('sample_size'),
                      pattern.get('failure_rate'), pattern.get('suggestion'),
                      json.dumps(pattern.get('metadata', {})), existing[0]))
            else:
                # Insertar nuevo
                cursor.execute('''
                    INSERT INTO detected_patterns 
                    (pattern_type, description, affected_strategy, market_condition,
                     confidence, sample_size, failure_rate, suggestion, metadata, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'detected')
                ''', (pattern.get('pattern_type'), pattern.get('description'),
                      pattern.get('affected_strategy'), pattern.get('market_condition'),
                      pattern.get('confidence'), pattern.get('sample_size'),
                      pattern.get('failure_rate'), pattern.get('suggestion'),
                      json.dumps(pattern.get('metadata', {}))))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error upserting detected pattern: {e}")
            return False
    
    def get_top_contributors(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """Obtener mejores contribuidores"""
        if not self.connected:
            return []
        
        try:
            from datetime import datetime, timedelta
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            since_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT 
                    user_id,
                    username,
                    contribution_points,
                    contribution_level,
                    total_feedback,
                    proposals_submitted,
                    proposals_accepted
                FROM user_contributions
                WHERE last_contribution >= %s
                ORDER BY contribution_points DESC
                LIMIT %s
            ''', (since_date, limit))
            
            rows = cursor.fetchall()
            contributors = []
            
            for row in rows:
                contributors.append({
                    'user_id': row[0],
                    'username': row[1],
                    'points': row[2],
                    'level': row[3],
                    'total_feedback': row[4],
                    'proposals_submitted': row[5],
                    'proposals_accepted': row[6]
                })
            
            cursor.close()
            conn.close()
            return contributors
            
        except Exception as e:
            logger.error(f"Error getting top contributors: {e}")
            return []
    
    def get_improvement_proposals(self, status: str = None, limit: int = 20) -> List[Dict]:
        """Obtener propuestas de mejora"""
        if not self.connected:
            return []
        
        try:
            conn = self._get_connection()
            if not conn:
                return []
            
            cursor = conn.cursor()
            
            if status:
                cursor.execute('''
                    SELECT proposal_id, user_id, title, description, category,
                           expected_improvement, status, votes, created_at
                    FROM improvement_proposals
                    WHERE status = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                ''', (status, limit))
            else:
                cursor.execute('''
                    SELECT proposal_id, user_id, title, description, category,
                           expected_improvement, status, votes, created_at
                    FROM improvement_proposals
                    ORDER BY created_at DESC
                    LIMIT %s
                ''', (limit,))
            
            rows = cursor.fetchall()
            proposals = []
            
            for row in rows:
                proposals.append({
                    'proposal_id': row[0],
                    'user_id': row[1],
                    'title': row[2],
                    'description': row[3],
                    'category': row[4],
                    'expected_improvement': row[5],
                    'status': row[6],
                    'votes': row[7],
                    'created_at': row[8].isoformat() if row[8] else None
                })
            
            cursor.close()
            conn.close()
            return proposals
            
        except Exception as e:
            logger.error(f"Error getting improvement proposals: {e}")
            return []
    
    def get_community_stats(self) -> Dict:
        """Obtener estadísticas comunitarias"""
        if not self.connected:
            return {}
        
        try:
            conn = self._get_connection()
            if not conn:
                return {}
            
            cursor = conn.cursor()
            stats = {}
            
            # Total contributors
            cursor.execute('SELECT COUNT(*) FROM user_contributions')
            stats['total_contributors'] = cursor.fetchone()[0]
            
            # Total feedback
            cursor.execute('SELECT COUNT(*) FROM community_feedback')
            stats['total_feedback'] = cursor.fetchone()[0]
            
            # Pending proposals
            cursor.execute('SELECT COUNT(*) FROM improvement_proposals WHERE status = %s', ('pending',))
            stats['pending_proposals'] = cursor.fetchone()[0]
            
            # Detected patterns
            cursor.execute('SELECT COUNT(*) FROM detected_patterns WHERE status = %s', ('detected',))
            stats['active_patterns'] = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"Error getting community stats: {e}")
            return {}
