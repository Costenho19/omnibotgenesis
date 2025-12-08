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
