-- AI RISK GUARDIAN V5.4 - Tabla de Eventos de Riesgo
-- ====================================================

CREATE TABLE IF NOT EXISTS risk_guardian_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    risk_type VARCHAR(50) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    action_taken TEXT NOT NULL,
    metadata JSONB,
    user_id BIGINT
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_risk_events_timestamp 
ON risk_guardian_events(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_risk_events_type 
ON risk_guardian_events(risk_type);

CREATE INDEX IF NOT EXISTS idx_risk_events_level 
ON risk_guardian_events(risk_level);

-- Comentarios
COMMENT ON TABLE risk_guardian_events IS 'Eventos de riesgo detectados por AI Risk Guardian';
COMMENT ON COLUMN risk_guardian_events.risk_type IS 'OVERTRADING, DRAWDOWN, REVENGE_TRADING, CAPITAL_RISK';
COMMENT ON COLUMN risk_guardian_events.risk_level IS 'LOW, MEDIUM, HIGH, CRITICAL';
COMMENT ON COLUMN risk_guardian_events.metadata IS 'Datos adicionales del evento en formato JSON';
