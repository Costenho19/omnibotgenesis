"""
OMNIX V6.5.4 - Railway Schema Synchronization Script

This script fixes the schema mismatch between Railway production database
and the current codebase. Run this ONCE on Railway to sync the schema.

Issues Fixed:
1. trade_reasonings table missing 'pair' column
2. paper_trades vs paper_trading_trades table confusion
3. profit vs profit_loss column naming

Usage on Railway:
    python scripts/railway_schema_sync.py
"""

import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Get PostgreSQL connection from environment"""
    try:
        import psycopg2
    except ImportError:
        logger.error("psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)
    
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        logger.info("Connected to Railway PostgreSQL")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        sys.exit(1)

def check_column_exists(cursor, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        )
    """, (table_name, column_name))
    return cursor.fetchone()[0]

def check_table_exists(cursor, table_name: str) -> bool:
    """Check if a table exists"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = %s
        )
    """, (table_name,))
    return cursor.fetchone()[0]

def run_migration(conn):
    """Execute the schema synchronization migration"""
    cursor = conn.cursor()
    changes_made = []
    
    try:
        logger.info("=" * 60)
        logger.info("OMNIX V6.5.4 Railway Schema Sync")
        logger.info("=" * 60)
        
        if check_table_exists(cursor, 'trade_reasonings'):
            logger.info("Table trade_reasonings exists")
            
            if not check_column_exists(cursor, 'trade_reasonings', 'pair'):
                logger.info("Adding 'pair' column to trade_reasonings...")
                cursor.execute("""
                    ALTER TABLE trade_reasonings 
                    ADD COLUMN IF NOT EXISTS pair TEXT
                """)
                changes_made.append("Added 'pair' column to trade_reasonings")
                
                if check_column_exists(cursor, 'trade_reasonings', 'symbol'):
                    logger.info("Copying data from 'symbol' to 'pair'...")
                    cursor.execute("""
                        UPDATE trade_reasonings 
                        SET pair = symbol 
                        WHERE pair IS NULL AND symbol IS NOT NULL
                    """)
                    changes_made.append("Copied symbol data to pair column")
            else:
                logger.info("Column 'pair' already exists in trade_reasonings")
            
            logger.info("Recreating index on trade_reasonings(pair)...")
            cursor.execute("""
                DROP INDEX IF EXISTS idx_trade_reasonings_pair
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trade_reasonings_pair 
                ON trade_reasonings(pair)
            """)
            changes_made.append("Recreated idx_trade_reasonings_pair index")
        else:
            logger.warning("Table trade_reasonings does not exist - will be created on next bot startup")
        
        if check_table_exists(cursor, 'paper_trading_trades'):
            logger.info("Table paper_trading_trades exists")
            
            if not check_column_exists(cursor, 'paper_trading_trades', 'profit_loss'):
                if check_column_exists(cursor, 'paper_trading_trades', 'profit'):
                    logger.info("Renaming 'profit' to 'profit_loss'...")
                    cursor.execute("""
                        ALTER TABLE paper_trading_trades 
                        RENAME COLUMN profit TO profit_loss
                    """)
                    changes_made.append("Renamed profit -> profit_loss in paper_trading_trades")
                else:
                    logger.info("Adding 'profit_loss' column...")
                    cursor.execute("""
                        ALTER TABLE paper_trading_trades 
                        ADD COLUMN IF NOT EXISTS profit_loss NUMERIC(18,8) DEFAULT 0
                    """)
                    changes_made.append("Added profit_loss column to paper_trading_trades")
            else:
                logger.info("Column 'profit_loss' already exists in paper_trading_trades")
            
            if not check_column_exists(cursor, 'paper_trading_trades', 'profit_pct'):
                logger.info("Adding 'profit_pct' column...")
                cursor.execute("""
                    ALTER TABLE paper_trading_trades 
                    ADD COLUMN IF NOT EXISTS profit_pct NUMERIC(10,4) DEFAULT 0
                """)
                changes_made.append("Added profit_pct column to paper_trading_trades")
            else:
                logger.info("Column 'profit_pct' already exists in paper_trading_trades")
        else:
            logger.warning("Table paper_trading_trades does not exist")
        
        if check_table_exists(cursor, 'paper_trades'):
            logger.info("Legacy table paper_trades exists (view or old table)")
        
        conn.commit()
        
        logger.info("=" * 60)
        logger.info("MIGRATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
        if changes_made:
            logger.info("Changes made:")
            for change in changes_made:
                logger.info(f"  - {change}")
        else:
            logger.info("No changes needed - schema is already up to date")
        
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        logger.error("Transaction rolled back - no changes made")
        return False
    finally:
        cursor.close()

def main():
    """Main entry point"""
    logger.info("Starting Railway Schema Sync...")
    
    conn = get_database_connection()
    
    try:
        success = run_migration(conn)
        if success:
            logger.info("Schema sync completed. Please restart the bot.")
            sys.exit(0)
        else:
            logger.error("Schema sync failed. Please check the errors above.")
            sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
