-- =============================================================================
-- OMNIX V7.0 Migration: Fix Schema Discrepancies
-- Date: December 16, 2025
-- Purpose: Resolve missing columns causing production errors on Railway
-- =============================================================================

-- Error 1: column "was_correct" does not exist in trade_evaluations
-- The table was created without this column but code expects it
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'trade_evaluations' AND column_name = 'was_correct'
    ) THEN
        ALTER TABLE trade_evaluations ADD COLUMN was_correct BOOLEAN NOT NULL DEFAULT false;
        RAISE NOTICE 'Added was_correct column to trade_evaluations';
    END IF;
END $$;

-- Recreate the index that was failing
CREATE INDEX IF NOT EXISTS idx_trade_evaluations_correctness 
ON trade_evaluations(was_correct);


-- Error 2: column "is_halted" does not exist in circuit_breaker_status
-- The table exists but was created with old schema
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    -- Add is_halted if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'circuit_breaker_status' AND column_name = 'is_halted'
    ) THEN
        ALTER TABLE circuit_breaker_status ADD COLUMN is_halted BOOLEAN DEFAULT false;
        RAISE NOTICE 'Added is_halted column to circuit_breaker_status';
    END IF;

    -- Add reason if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'circuit_breaker_status' AND column_name = 'reason'
    ) THEN
        ALTER TABLE circuit_breaker_status ADD COLUMN reason VARCHAR(50);
        RAISE NOTICE 'Added reason column to circuit_breaker_status';
    END IF;

    -- Add message if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'circuit_breaker_status' AND column_name = 'message'
    ) THEN
        ALTER TABLE circuit_breaker_status ADD COLUMN message TEXT;
        RAISE NOTICE 'Added message column to circuit_breaker_status';
    END IF;

    -- Add halted_at if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'circuit_breaker_status' AND column_name = 'halted_at'
    ) THEN
        ALTER TABLE circuit_breaker_status ADD COLUMN halted_at TIMESTAMP WITH TIME ZONE;
        RAISE NOTICE 'Added halted_at column to circuit_breaker_status';
    END IF;

    -- Add resume_at if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'circuit_breaker_status' AND column_name = 'resume_at'
    ) THEN
        ALTER TABLE circuit_breaker_status ADD COLUMN resume_at TIMESTAMP WITH TIME ZONE;
        RAISE NOTICE 'Added resume_at column to circuit_breaker_status';
    END IF;

    -- Add halted_by if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'circuit_breaker_status' AND column_name = 'halted_by'
    ) THEN
        ALTER TABLE circuit_breaker_status ADD COLUMN halted_by VARCHAR(100) DEFAULT 'system';
        RAISE NOTICE 'Added halted_by column to circuit_breaker_status';
    END IF;

    -- Add can_override if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'circuit_breaker_status' AND column_name = 'can_override'
    ) THEN
        ALTER TABLE circuit_breaker_status ADD COLUMN can_override BOOLEAN DEFAULT true;
        RAISE NOTICE 'Added can_override column to circuit_breaker_status';
    END IF;

    -- Add updated_at if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'circuit_breaker_status' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE circuit_breaker_status ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
        RAISE NOTICE 'Added updated_at column to circuit_breaker_status';
    END IF;
END $$;


-- Error 3: paper_trading_trades missing columns used by legacy queries
-- Some queries expect 'quantity' and 'profit_loss' columns
-- The actual columns are 'base_quantity' and 'net_realized_pnl_usd'
-- -----------------------------------------------------------------------------

-- Create VIEW as alias for backwards compatibility (non-destructive)
CREATE OR REPLACE VIEW paper_trades AS
SELECT 
    id,
    trade_uuid,
    user_id,
    position_id,
    symbol,
    side AS direction,  -- Alias: side -> direction for legacy code
    side,
    order_type,
    status,
    entry_price,
    exit_price,
    base_quantity AS quantity,  -- Alias: base_quantity -> quantity
    base_quantity,
    quote_notional_usd AS position_size_usd,  -- Alias for legacy
    quote_notional_usd,
    fee_bps,
    fee_usd,
    gross_pnl_usd,
    net_realized_pnl_usd AS profit_loss,  -- Alias: net_realized_pnl_usd -> profit_loss
    net_realized_pnl_usd AS profit,  -- Another alias
    net_realized_pnl_usd,
    unrealized_pnl_usd,
    opened_at AS timestamp,  -- Alias: opened_at -> timestamp
    opened_at,
    opened_at AS created_at,  -- Alias for legacy
    closed_at,
    duration_seconds,
    source_strategy AS strategy,  -- Alias: source_strategy -> strategy
    source_strategy,
    notes,
    is_paper_trade
FROM paper_trading_trades;

COMMENT ON VIEW paper_trades IS 'Backwards-compatible view for legacy queries expecting paper_trades table';


-- Add profit_pct column if missing (used by queries.py)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'paper_trading_trades' AND column_name = 'profit_pct'
    ) THEN
        ALTER TABLE paper_trading_trades ADD COLUMN profit_pct NUMERIC(10,4);
        RAISE NOTICE 'Added profit_pct column to paper_trading_trades';
    END IF;
END $$;


-- =============================================================================
-- VERIFICATION QUERIES (run after migration to confirm success)
-- =============================================================================
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'trade_evaluations';
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'circuit_breaker_status';
-- SELECT * FROM paper_trades LIMIT 1;
-- =============================================================================
