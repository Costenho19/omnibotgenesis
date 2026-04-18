-- =============================================
-- OMNIX V5.3 ULTRA - AUTO-OPTIMIZATION TABLES
-- Tablas para tracking de optimizaciones genéticas
-- y A/B testing de estrategias
-- =============================================

-- Tabla: optimization_runs
-- Guarda historial de ejecuciones del algoritmo genético
CREATE TABLE IF NOT EXISTS optimization_runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) UNIQUE NOT NULL,
    start_time TIMESTAMP NOT NULL DEFAULT NOW(),
    end_time TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'RUNNING', -- RUNNING, COMPLETED, FAILED, PAUSED
    population_size INTEGER NOT NULL,
    generations INTEGER NOT NULL,
    mutation_rate FLOAT NOT NULL,
    best_fitness FLOAT DEFAULT 0.0,
    best_parameters JSONB, -- Mejor set de parámetros encontrado
    generation_history JSONB, -- Historia de generaciones
    total_individuals_evaluated INTEGER DEFAULT 0,
    notes TEXT,
    created_by VARCHAR(50) DEFAULT 'system'
);

-- Tabla: genetic_individuals
-- Almacena cada individuo evaluado
CREATE TABLE IF NOT EXISTS genetic_individuals (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) REFERENCES optimization_runs(run_id) ON DELETE CASCADE,
    generation INTEGER NOT NULL,
    individual_id VARCHAR(100) NOT NULL,
    parameters JSONB NOT NULL, -- StrategyParameters completos
    fitness FLOAT DEFAULT 0.0,
    trades_count INTEGER DEFAULT 0,
    win_rate FLOAT DEFAULT 0.0,
    profit_usd FLOAT DEFAULT 0.0,
    sharpe_ratio FLOAT DEFAULT 0.0,
    max_drawdown FLOAT DEFAULT 0.0,
    evaluated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(run_id, individual_id)
);

-- Tabla: ab_tests
-- Configuración de tests A/B
CREATE TABLE IF NOT EXISTS ab_tests (
    id SERIAL PRIMARY KEY,
    test_id VARCHAR(100) UNIQUE NOT NULL,
    test_name VARCHAR(200) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING', -- PENDING, RUNNING, COMPLETED, CANCELLED
    duration_hours INTEGER NOT NULL,
    min_samples INTEGER NOT NULL,
    control_params JSONB NOT NULL,
    variant_a_params JSONB NOT NULL,
    variant_b_params JSONB, -- Opcional
    winner_variant VARCHAR(20), -- CONTROL, VARIANT_A, VARIANT_B
    test_results JSONB, -- Resultados completos del análisis
    notes TEXT,
    created_by VARCHAR(50) DEFAULT 'harold'
);

-- Tabla: ab_test_trades
-- Trades ejecutados durante A/B tests
CREATE TABLE IF NOT EXISTS ab_test_trades (
    id SERIAL PRIMARY KEY,
    test_id VARCHAR(100) REFERENCES ab_tests(test_id) ON DELETE CASCADE,
    variant VARCHAR(20) NOT NULL, -- CONTROL, VARIANT_A, VARIANT_B
    trade_id VARCHAR(100),
    executed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    action VARCHAR(10) NOT NULL, -- BUY, SELL
    amount_usd FLOAT NOT NULL,
    price FLOAT NOT NULL,
    profit_usd FLOAT DEFAULT 0.0,
    is_win BOOLEAN DEFAULT FALSE,
    confidence FLOAT,
    strategy_signals JSONB, -- Señales de estrategias usadas
    closed_at TIMESTAMP,
    notes TEXT
);

-- Tabla: auto_adjustments
-- Historial de ajustes automáticos
CREATE TABLE IF NOT EXISTS auto_adjustments (
    id SERIAL PRIMARY KEY,
    adjustment_id VARCHAR(100) UNIQUE NOT NULL,
    triggered_at TIMESTAMP NOT NULL DEFAULT NOW(),
    applied_at TIMESTAMP,
    trigger_reason TEXT NOT NULL, -- Por qué se activó el ajuste
    previous_params JSONB NOT NULL,
    new_params JSONB NOT NULL,
    performance_metrics JSONB NOT NULL, -- Métricas que dispararon el ajuste
    lookback_trades INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'APPLIED', -- APPLIED, REVERTED
    reverted_at TIMESTAMP,
    revert_reason TEXT,
    created_by VARCHAR(50) DEFAULT 'auto_adjustment_engine'
);

-- Tabla: parameter_evolution
-- Tracking de evolución de parámetros en el tiempo
CREATE TABLE IF NOT EXISTS parameter_evolution (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    source VARCHAR(50) NOT NULL, -- genetic, ab_test, auto_adjust, manual
    parameters JSONB NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    win_rate_24h FLOAT,
    sharpe_ratio_24h FLOAT,
    profit_24h FLOAT,
    trades_24h INTEGER,
    notes TEXT
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_optimization_runs_status ON optimization_runs(status);
CREATE INDEX IF NOT EXISTS idx_genetic_individuals_run_id ON genetic_individuals(run_id);
CREATE INDEX IF NOT EXISTS idx_genetic_individuals_fitness ON genetic_individuals(fitness DESC);
CREATE INDEX IF NOT EXISTS idx_ab_tests_status ON ab_tests(status);
CREATE INDEX IF NOT EXISTS idx_ab_test_trades_test_id ON ab_test_trades(test_id);
CREATE INDEX IF NOT EXISTS idx_ab_test_trades_variant ON ab_test_trades(variant);
CREATE INDEX IF NOT EXISTS idx_auto_adjustments_triggered_at ON auto_adjustments(triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_parameter_evolution_timestamp ON parameter_evolution(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_parameter_evolution_active ON parameter_evolution(active);

-- Función: get_best_parameters
-- Retorna los mejores parámetros históricos
CREATE OR REPLACE FUNCTION get_best_parameters(
    min_trades INTEGER DEFAULT 100,
    days_back INTEGER DEFAULT 7
)
RETURNS TABLE (
    parameters JSONB,
    fitness FLOAT,
    win_rate FLOAT,
    sharpe_ratio FLOAT,
    profit_usd FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        gi.parameters,
        gi.fitness,
        gi.win_rate,
        gi.sharpe_ratio,
        gi.profit_usd
    FROM genetic_individuals gi
    WHERE gi.trades_count >= min_trades
        AND gi.evaluated_at >= NOW() - (days_back || ' days')::INTERVAL
    ORDER BY gi.fitness DESC
    LIMIT 10;
END;
$$ LANGUAGE plpgsql;

-- Función: get_ab_test_summary
-- Resumen de un test A/B
CREATE OR REPLACE FUNCTION get_ab_test_summary(p_test_id VARCHAR)
RETURNS TABLE (
    variant VARCHAR,
    trades_count BIGINT,
    win_rate FLOAT,
    avg_profit FLOAT,
    total_profit FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        att.variant,
        COUNT(*)::BIGINT as trades_count,
        (SUM(CASE WHEN att.is_win THEN 1 ELSE 0 END)::FLOAT / COUNT(*))::FLOAT as win_rate,
        AVG(att.profit_usd)::FLOAT as avg_profit,
        SUM(att.profit_usd)::FLOAT as total_profit
    FROM ab_test_trades att
    WHERE att.test_id = p_test_id
    GROUP BY att.variant
    ORDER BY win_rate DESC, total_profit DESC;
END;
$$ LANGUAGE plpgsql;

-- Comentarios
COMMENT ON TABLE optimization_runs IS 'Ejecuciones del algoritmo genético de optimización';
COMMENT ON TABLE genetic_individuals IS 'Individuos evaluados durante optimización genética';
COMMENT ON TABLE ab_tests IS 'Configuración de tests A/B de estrategias';
COMMENT ON TABLE ab_test_trades IS 'Trades ejecutados durante A/B tests';
COMMENT ON TABLE auto_adjustments IS 'Ajustes automáticos de parámetros basados en performance';
COMMENT ON TABLE parameter_evolution IS 'Evolución histórica de parámetros del sistema';

-- Datos iniciales (parámetros baseline)
INSERT INTO parameter_evolution (source, parameters, active, notes)
VALUES (
    'manual',
    '{
        "quantum_threshold": 5.0,
        "quantum_weight": 0.20,
        "kalman_threshold": 0.3,
        "kalman_weight": 0.15,
        "monte_carlo_simulations": 10000,
        "monte_carlo_confidence": 0.60,
        "monte_carlo_weight": 0.15,
        "hmm_states": 3,
        "hmm_weight": 0.12,
        "kelly_fraction": 0.25,
        "kelly_weight": 0.10,
        "black_swan_kurtosis_threshold": 3.0,
        "black_swan_weight": 0.10,
        "order_book_depth": 10,
        "order_book_weight": 0.08,
        "sentiment_threshold": 60.0,
        "sentiment_weight": 0.06,
        "sharia_weight": 0.04,
        "min_confidence_threshold": 0.60,
        "max_position_size_usd": 1000.0,
        "stop_loss_percentage": 0.05,
        "take_profit_percentage": 0.10
    }'::JSONB,
    TRUE,
    'Parámetros baseline iniciales de OMNIX V5.3 ULTRA'
)
ON CONFLICT DO NOTHING;

SELECT 'Tablas de Auto-Optimization creadas exitosamente ✅' AS status;
