-- ==========================================
-- OMNIX V5.1 - DATABASE OPTIMIZATION
-- Indexes para escalar a 100K+ usuarios
-- ==========================================

-- PROBLEMA: Queries lentos con muchos usuarios
-- SOLUCIÓN: Indexes estratégicos en columnas más consultadas

-- ==========================================
-- 1. USERS TABLE - Consultas por user_id frecuentes
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(subscription_tier) WHERE subscription_tier IS NOT NULL;

-- ==========================================
-- 2. TRADES TABLE - Histórico de trades
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trades_pair ON trades(pair);
CREATE INDEX IF NOT EXISTS idx_trades_user_pair ON trades(user_id, pair, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trades_pnl ON trades(profit_loss) WHERE profit_loss IS NOT NULL;

-- ==========================================
-- 3. BALANCE_HISTORY TABLE - Tracking de balance
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_balance_user_id ON balance_history(user_id);
CREATE INDEX IF NOT EXISTS idx_balance_timestamp ON balance_history(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_balance_user_time ON balance_history(user_id, timestamp DESC);

-- ==========================================
-- 4. CONVERSATIONS TABLE - Chat history
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp DESC);

-- ==========================================
-- 5. ANALYSIS TABLE - Análisis técnico
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_analysis_user_id ON analysis(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_pair ON analysis(pair);
CREATE INDEX IF NOT EXISTS idx_analysis_timestamp ON analysis(timestamp DESC);

-- ==========================================
-- 6. PAPER_TRADING_TRADES TABLE - Paper trading
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_paper_trades_user_id ON paper_trading_trades(user_id);
CREATE INDEX IF NOT EXISTS idx_paper_trades_timestamp ON paper_trading_trades(timestamp DESC);

-- ==========================================
-- 7. PERFORMANCE OPTIMIZATION
-- ==========================================

-- Vacuuming para reclamar espacio
VACUUM ANALYZE users;
VACUUM ANALYZE trades;
VACUUM ANALYZE balance_history;
VACUUM ANALYZE conversations;

-- ==========================================
-- VERIFICACIÓN DE INDEXES
-- ==========================================

-- Ver todos los indexes creados
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Ver tamaño de tablas e indexes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
