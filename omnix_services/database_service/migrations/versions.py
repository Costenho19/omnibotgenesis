"""
OMNIX V6.5.4 - Migration Versions

Contains all versioned migrations for the database.
Each migration is idempotent and non-destructive.
"""

import logging
from typing import Any
from .registry import Migration, MigrationRegistry

logger = logging.getLogger("OMNIX.Migrations")


def _check_column_exists(cursor, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        )
    """, (table_name, column_name))
    result = cursor.fetchone()
    return result[0] if result else False


def _check_table_exists(cursor, table_name: str) -> bool:
    """Check if a table exists"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = %s
        )
    """, (table_name,))
    result = cursor.fetchone()
    return result[0] if result else False


def v001_sync_trade_reasonings_pair(cursor: Any) -> bool:
    """
    V001: Ensure trade_reasonings table has 'pair' column
    
    The table definition has 'pair' but Railway may have an older schema.
    This migration adds the column if missing and copies from 'symbol' if it exists.
    
    NON-DESTRUCTIVE: Only adds column if not exists, copies data.
    """
    try:
        if not _check_table_exists(cursor, 'trade_reasonings'):
            logger.info("Table trade_reasonings does not exist - will be created on bot startup")
            return True
        
        if _check_column_exists(cursor, 'trade_reasonings', 'pair'):
            logger.info("Column 'pair' already exists in trade_reasonings - skipping")
            return True
        
        logger.info("Adding 'pair' column to trade_reasonings...")
        cursor.execute("""
            ALTER TABLE trade_reasonings 
            ADD COLUMN pair TEXT
        """)
        
        if _check_column_exists(cursor, 'trade_reasonings', 'symbol'):
            logger.info("Copying data from 'symbol' to 'pair'...")
            cursor.execute("""
                UPDATE trade_reasonings 
                SET pair = symbol 
                WHERE pair IS NULL AND symbol IS NOT NULL
            """)
        
        cursor.execute("DROP INDEX IF EXISTS idx_trade_reasonings_pair")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trade_reasonings_pair 
            ON trade_reasonings(pair)
        """)
        
        logger.info("Migration V001 applied successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration V001 failed: {e}")
        return False


def v002_sync_paper_trading_columns(cursor: Any) -> bool:
    """
    V002: Ensure paper_trading_trades has correct column names
    
    Fixes the 'profit' vs 'profit_loss' column naming issue.
    Also ensures 'profit_pct' column exists.
    
    NON-DESTRUCTIVE: Only renames if old column exists, adds new columns.
    """
    try:
        if not _check_table_exists(cursor, 'paper_trading_trades'):
            logger.info("Table paper_trading_trades does not exist - will be created on bot startup")
            return True
        
        has_profit = _check_column_exists(cursor, 'paper_trading_trades', 'profit')
        has_profit_loss = _check_column_exists(cursor, 'paper_trading_trades', 'profit_loss')
        
        if has_profit and not has_profit_loss:
            logger.info("Renaming 'profit' to 'profit_loss' in paper_trading_trades...")
            cursor.execute("""
                ALTER TABLE paper_trading_trades 
                RENAME COLUMN profit TO profit_loss
            """)
        elif not has_profit_loss:
            logger.info("Adding 'profit_loss' column to paper_trading_trades...")
            cursor.execute("""
                ALTER TABLE paper_trading_trades 
                ADD COLUMN profit_loss NUMERIC(18,8) DEFAULT 0
            """)
        else:
            logger.info("Column 'profit_loss' already exists - skipping")
        
        if not _check_column_exists(cursor, 'paper_trading_trades', 'profit_pct'):
            logger.info("Adding 'profit_pct' column to paper_trading_trades...")
            cursor.execute("""
                ALTER TABLE paper_trading_trades 
                ADD COLUMN profit_pct NUMERIC(10,4) DEFAULT 0
            """)
        else:
            logger.info("Column 'profit_pct' already exists - skipping")
        
        logger.info("Migration V002 applied successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration V002 failed: {e}")
        return False


def v003_ensure_symbol_column(cursor: Any) -> bool:
    """
    V003: Ensure paper_trading_trades has 'symbol' column
    
    Some older schemas may use 'pair' instead of 'symbol'.
    This migration ensures consistency.
    
    NON-DESTRUCTIVE: Only adds column if not exists.
    """
    try:
        if not _check_table_exists(cursor, 'paper_trading_trades'):
            logger.info("Table paper_trading_trades does not exist - will be created on bot startup")
            return True
        
        if _check_column_exists(cursor, 'paper_trading_trades', 'symbol'):
            logger.info("Column 'symbol' already exists in paper_trading_trades - skipping")
            return True
        
        if _check_column_exists(cursor, 'paper_trading_trades', 'pair'):
            logger.info("Renaming 'pair' to 'symbol' in paper_trading_trades...")
            cursor.execute("""
                ALTER TABLE paper_trading_trades 
                RENAME COLUMN pair TO symbol
            """)
        else:
            logger.info("Adding 'symbol' column to paper_trading_trades...")
            cursor.execute("""
                ALTER TABLE paper_trading_trades 
                ADD COLUMN symbol VARCHAR(50)
            """)
        
        logger.info("Migration V003 applied successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration V003 failed: {e}")
        return False


def _check_policy_exists(cursor, table_name: str, policy_name: str) -> bool:
    """Check if a RLS policy exists on a table"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM pg_policies 
            WHERE tablename = %s AND policyname = %s
        )
    """, (table_name, policy_name))
    result = cursor.fetchone()
    return result[0] if result else False


def v004_enable_row_level_security(cursor: Any) -> bool:
    """
    V004: Enable Row-Level Security (RLS) on multi-user tables
    
    Enables RLS on:
    - paper_trading_trades: Trading history per user
    - paper_trading_balances: Balance snapshots per user
    - user_settings: User configuration
    
    Policy Logic:
    - If app.current_user_id is NOT set (NULL or '') → see ALL rows (legacy mode)
    - If app.current_user_id IS set → see ONLY rows for that user
    
    FORCE ROW LEVEL SECURITY is enabled so RLS applies even to table owners.
    NOTE: Superusers (like 'postgres') ALWAYS bypass RLS - this is PostgreSQL design.
    Production should use a non-superuser application role.
    
    NON-DESTRUCTIVE: Only enables RLS and creates policies if not exist.
    BACKWARD COMPATIBLE: Legacy queries without app.current_user_id see all rows.
    """
    try:
        tables_config = [
            ('paper_trading_trades', 'user_id'),
            ('paper_trading_balances', 'user_id'),
            ('user_settings', 'user_id'),
        ]
        
        for table_name, user_column in tables_config:
            if not _check_table_exists(cursor, table_name):
                logger.info(f"Table {table_name} does not exist - skipping RLS")
                continue
            
            logger.info(f"Enabling RLS on {table_name}...")
            cursor.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY")
            cursor.execute(f"ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY")
            
            policy_name = f"{table_name}_user_isolation"
            
            if _check_policy_exists(cursor, table_name, policy_name):
                cursor.execute(f"DROP POLICY {policy_name} ON {table_name}")
                logger.info(f"Dropped existing policy {policy_name} for update")
            
            cursor.execute(f"""
                CREATE POLICY {policy_name} ON {table_name}
                FOR ALL
                USING (
                    NULLIF(current_setting('app.current_user_id', true), '') IS NULL 
                    OR {user_column}::text = current_setting('app.current_user_id', true)
                )
                WITH CHECK (
                    NULLIF(current_setting('app.current_user_id', true), '') IS NULL 
                    OR {user_column}::text = current_setting('app.current_user_id', true)
                )
            """)
            
            logger.info(f"Created RLS policy {policy_name} on {table_name}")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_paper_trading_trades_user_id 
            ON paper_trading_trades(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_paper_trading_balances_user_id 
            ON paper_trading_balances(user_id)
        """)
        
        logger.info("Migration V004 applied successfully - RLS enabled on multi-user tables")
        logger.info("NOTE: Superusers bypass RLS by design. Use non-superuser role in production.")
        return True
        
    except Exception as e:
        logger.error(f"Migration V004 failed: {e}")
        return False


def v005_add_telemetry_columns_operacion_lucidez(cursor: Any) -> bool:
    """
    V005: Operación Lucidez - Add telemetry columns for trade segmentation
    
    Adds columns to track market regime and coherence at trade execution time:
    - hmm_regime: Market regime (BULLISH/BEARISH/RANGING)
    - coherence_score: Coherence percentage (0-100)
    - ema_regime_signal: EMA signal at trade time (BUY/SELL/HOLD)
    - strategy_confidence: Overall strategy confidence (0-100)
    
    These enable "Expectancy by Segment" analysis to discover WHERE the system wins.
    
    NON-DESTRUCTIVE: Only adds columns if not exists.
    """
    try:
        if not _check_table_exists(cursor, 'paper_trading_trades'):
            logger.info("Table paper_trading_trades does not exist - will be created on bot startup")
            return True
        
        columns_to_add = [
            ('hmm_regime', 'VARCHAR(20)', "Market regime at trade time"),
            ('coherence_score', 'NUMERIC(5,2)', "Coherence percentage 0-100"),
            ('ema_regime_signal', 'VARCHAR(10)', "EMA signal BUY/SELL/HOLD"),
            ('strategy_confidence', 'NUMERIC(5,2)', "Strategy confidence 0-100"),
        ]
        
        for col_name, col_type, col_desc in columns_to_add:
            if _check_column_exists(cursor, 'paper_trading_trades', col_name):
                logger.info(f"Column '{col_name}' already exists - skipping")
            else:
                logger.info(f"Adding '{col_name}' ({col_desc}) to paper_trading_trades...")
                cursor.execute(f"""
                    ALTER TABLE paper_trading_trades 
                    ADD COLUMN {col_name} {col_type}
                """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_paper_trades_hmm_regime 
            ON paper_trading_trades(hmm_regime)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_paper_trades_coherence_bucket 
            ON paper_trading_trades((
                CASE WHEN coherence_score >= 70 THEN 'HIGH'
                     WHEN coherence_score >= 50 THEN 'MED'
                     ELSE 'LOW' END
            ))
        """)
        
        logger.info("Migration V005 (Operación Lucidez) applied successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration V005 failed: {e}")
        return False


MIGRATIONS = MigrationRegistry()

MIGRATIONS.register(Migration(
    version="V001",
    description="Sync trade_reasonings table - add pair column",
    apply_func=v001_sync_trade_reasonings_pair
))

MIGRATIONS.register(Migration(
    version="V002", 
    description="Sync paper_trading_trades - rename profit to profit_loss",
    apply_func=v002_sync_paper_trading_columns
))

MIGRATIONS.register(Migration(
    version="V003",
    description="Ensure paper_trading_trades has symbol column",
    apply_func=v003_ensure_symbol_column
))

MIGRATIONS.register(Migration(
    version="V004",
    description="Enable Row-Level Security on multi-user tables",
    apply_func=v004_enable_row_level_security
))

MIGRATIONS.register(Migration(
    version="V005",
    description="Operación Lucidez - Add telemetry columns for trade segmentation",
    apply_func=v005_add_telemetry_columns_operacion_lucidez
))


def v006_create_trading_veto_log(cursor: Any) -> bool:
    """
    V006: Create trading_veto_log table for real-time veto tracking
    
    Tracks all veto decisions (Coherence Gate, Black Swan, Monte Carlo, RMS)
    with blocked capital amounts for accurate dashboard reporting.
    
    This enables:
    - Real-time "capital protected" metrics matching OMNIX bot reports
    - Audit trail of all blocked trades with reasons
    - Dashboard widget showing vetoes by type (last 48h, 7d, total)
    
    NON-DESTRUCTIVE: Only creates table if not exists.
    """
    try:
        if _check_table_exists(cursor, 'trading_veto_log'):
            logger.info("Table trading_veto_log already exists - skipping creation")
            return True
        
        logger.info("Creating trading_veto_log table...")
        cursor.execute("""
            CREATE TABLE trading_veto_log (
                id BIGSERIAL PRIMARY KEY,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                veto_type VARCHAR(30) NOT NULL,
                engine_stage VARCHAR(50),
                symbol VARCHAR(20) NOT NULL,
                market VARCHAR(10) DEFAULT 'crypto',
                user_id BIGINT,
                trade_id BIGINT,
                blocked_capital NUMERIC(18,2) NOT NULL DEFAULT 0,
                currency VARCHAR(10) DEFAULT 'USD',
                confidence NUMERIC(5,2),
                severity VARCHAR(20) DEFAULT 'MEDIUM',
                reason TEXT,
                metadata JSONB DEFAULT '{}'::jsonb
            )
        """)
        
        cursor.execute("""
            CREATE INDEX idx_veto_log_created_at 
            ON trading_veto_log(created_at DESC)
        """)
        cursor.execute("""
            CREATE INDEX idx_veto_log_type_created 
            ON trading_veto_log(veto_type, created_at DESC)
        """)
        cursor.execute("""
            CREATE INDEX idx_veto_log_symbol_created 
            ON trading_veto_log(symbol, created_at DESC)
        """)
        
        cursor.execute("""
            COMMENT ON TABLE trading_veto_log IS 'Real-time veto tracking for dashboard capital protection metrics'
        """)
        cursor.execute("""
            COMMENT ON COLUMN trading_veto_log.veto_type IS 'COHERENCE_GATE, BLACK_SWAN, MONTE_CARLO, RMS, QUARANTINE'
        """)
        cursor.execute("""
            COMMENT ON COLUMN trading_veto_log.blocked_capital IS 'USD amount that would have been deployed if trade executed'
        """)
        
        logger.info("Migration V006 (trading_veto_log) applied successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration V006 failed: {e}")
        return False


MIGRATIONS.register(Migration(
    version="V006",
    description="Create trading_veto_log table for real-time veto tracking",
    apply_func=v006_create_trading_veto_log
))
