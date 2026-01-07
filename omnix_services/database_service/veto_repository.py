"""
OMNIX V6.5.4d - Veto Repository

Handles persistence and retrieval of trading veto events.
Enables real-time capital protection tracking for dashboard.

Created: Jan 7, 2026
Purpose: Sync dashboard with OMNIX bot veto reports
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal

logger = logging.getLogger("OMNIX.VetoRepository")


class VetoType:
    COHERENCE_GATE = "COHERENCE_GATE"
    BLACK_SWAN = "BLACK_SWAN"
    MONTE_CARLO = "MONTE_CARLO"
    RMS = "RMS"
    QUARANTINE = "QUARANTINE"


class VetoRepository:
    """
    Repository for trading veto events.
    
    Provides methods to:
    - Log veto events when trades are blocked
    - Fetch aggregated veto data for dashboard
    - Query recent vetoes by type/symbol/time range
    """
    
    def __init__(self, db_connection_func):
        """
        Initialize with a database connection factory.
        
        Args:
            db_connection_func: Callable that returns a DB connection context manager
        """
        self._get_connection = db_connection_func
    
    def log_veto(
        self,
        veto_type: str,
        symbol: str,
        blocked_capital: float,
        reason: str = None,
        user_id: int = None,
        trade_id: int = None,
        engine_stage: str = None,
        market: str = "crypto",
        confidence: float = None,
        severity: str = "MEDIUM",
        metadata: dict = None
    ) -> bool:
        """
        Log a veto event to the database.
        
        Args:
            veto_type: Type of veto (COHERENCE_GATE, BLACK_SWAN, etc.)
            symbol: Trading pair (e.g., BTC/USD)
            blocked_capital: USD amount that was blocked
            reason: Human-readable reason for veto
            user_id: User who triggered the trade attempt
            trade_id: Related trade ID if any
            engine_stage: Which engine stage vetoed
            market: Market type (crypto/stock)
            confidence: Confidence score 0-100
            severity: Severity level (LOW/MEDIUM/HIGH/CRITICAL)
            metadata: Additional JSONB metadata
            
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            with self._get_connection() as conn:
                if not conn:
                    logger.warning("No DB connection - veto not logged (fail-open for logging)")
                    return False
                
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO trading_veto_log 
                    (veto_type, symbol, blocked_capital, reason, user_id, trade_id,
                     engine_stage, market, confidence, severity, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    veto_type,
                    symbol,
                    blocked_capital,
                    reason,
                    user_id,
                    trade_id,
                    engine_stage,
                    market,
                    confidence,
                    severity,
                    metadata or {}
                ))
                conn.commit()
                cursor.close()
                
                logger.info(f"Veto logged: {veto_type} | {symbol} | ${blocked_capital:,.2f}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to log veto: {e}")
            return False
    
    def get_veto_summary(self, hours: int = 48) -> Dict[str, Any]:
        """
        Get aggregated veto summary for dashboard.
        
        Args:
            hours: Look-back period in hours (default 48h)
            
        Returns:
            Dict with totals by veto type and overall
        """
        try:
            with self._get_connection() as conn:
                if not conn:
                    return self._empty_summary()
                
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        veto_type,
                        COUNT(*) as veto_count,
                        COALESCE(SUM(blocked_capital), 0) as total_blocked
                    FROM trading_veto_log
                    WHERE created_at >= NOW() - INTERVAL '%s hours'
                    GROUP BY veto_type
                    ORDER BY total_blocked DESC
                """, (hours,))
                
                rows = cursor.fetchall()
                cursor.close()
                
                summary = {
                    'period_hours': hours,
                    'by_type': {},
                    'total_blocked': 0,
                    'total_count': 0
                }
                
                for row in rows:
                    veto_type = row[0]
                    count = row[1]
                    blocked = float(row[2])
                    
                    summary['by_type'][veto_type] = {
                        'count': count,
                        'blocked_capital': blocked
                    }
                    summary['total_blocked'] += blocked
                    summary['total_count'] += count
                
                return summary
                
        except Exception as e:
            logger.error(f"Failed to get veto summary: {e}")
            return self._empty_summary()
    
    def get_recent_vetoes(
        self,
        limit: int = 20,
        veto_type: str = None,
        symbol: str = None,
        hours: int = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent veto events with optional filters.
        
        Args:
            limit: Maximum number of records
            veto_type: Filter by type
            symbol: Filter by symbol
            hours: Filter by time range
            
        Returns:
            List of veto records
        """
        try:
            with self._get_connection() as conn:
                if not conn:
                    return []
                
                cursor = conn.cursor()
                
                query = """
                    SELECT id, created_at, veto_type, symbol, blocked_capital, 
                           reason, severity, engine_stage
                    FROM trading_veto_log
                    WHERE 1=1
                """
                params = []
                
                if veto_type:
                    query += " AND veto_type = %s"
                    params.append(veto_type)
                
                if symbol:
                    query += " AND symbol = %s"
                    params.append(symbol)
                
                if hours:
                    query += " AND created_at >= NOW() - INTERVAL '%s hours'"
                    params.append(hours)
                
                query += " ORDER BY created_at DESC LIMIT %s"
                params.append(limit)
                
                cursor.execute(query, tuple(params))
                rows = cursor.fetchall()
                cursor.close()
                
                return [
                    {
                        'id': row[0],
                        'created_at': row[1].isoformat() if row[1] else None,
                        'veto_type': row[2],
                        'symbol': row[3],
                        'blocked_capital': float(row[4]) if row[4] else 0,
                        'reason': row[5],
                        'severity': row[6],
                        'engine_stage': row[7]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Failed to get recent vetoes: {e}")
            return []
    
    def get_all_time_total(self) -> float:
        """Get all-time total blocked capital."""
        try:
            with self._get_connection() as conn:
                if not conn:
                    return 0.0
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COALESCE(SUM(blocked_capital), 0) 
                    FROM trading_veto_log
                """)
                result = cursor.fetchone()
                cursor.close()
                
                return float(result[0]) if result else 0.0
                
        except Exception as e:
            logger.error(f"Failed to get all-time total: {e}")
            return 0.0
    
    def _empty_summary(self) -> Dict[str, Any]:
        """Return empty summary structure."""
        return {
            'period_hours': 0,
            'by_type': {},
            'total_blocked': 0,
            'total_count': 0
        }


_veto_repository_instance: Optional[VetoRepository] = None


def get_veto_repository() -> Optional[VetoRepository]:
    """
    Get singleton VetoRepository instance.
    
    Returns:
        VetoRepository instance or None if DB not available
    """
    global _veto_repository_instance
    
    if _veto_repository_instance is None:
        try:
            from omnix_dashboard.utils.database import get_db_connection
            _veto_repository_instance = VetoRepository(get_db_connection)
        except Exception as e:
            logger.warning(f"Could not initialize VetoRepository: {e}")
            return None
    
    return _veto_repository_instance
