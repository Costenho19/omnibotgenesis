"""
OMNIX V6.5.4d - Veto Repository

Handles persistence and retrieval of trading veto events.
Enables real-time capital protection tracking for dashboard.

Created: Jan 7, 2026
Updated: Jan 8, 2026 - Deduplication cache (15 min window per symbol+veto_type)
Purpose: Sync dashboard with OMNIX bot veto reports

DEDUPLICATION LOGIC:
- Each (veto_type, symbol) combination is cached for 15 minutes
- Repeated vetoes within window are skipped to prevent inflated numbers
- Audit trail maintained via get_recent_vetoes() showing all actual decisions
- Dashboard shows realistic capital protection for investors
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal
from contextlib import contextmanager
import threading

logger = logging.getLogger("OMNIX.VetoRepository")

DEDUPE_WINDOW_SECONDS = 900


@contextmanager
def _standalone_db_connection():
    """
    Standalone database connection using DATABASE_URL.
    Works in both bot (Railway) and dashboard contexts.
    
    Supports both psycopg v3 (preferred) and psycopg2 (fallback).
    """
    conn = None
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.warning("DATABASE_URL not set - veto logging disabled")
            yield None
            return
        
        try:
            import psycopg
            conn = psycopg.connect(database_url)
        except ImportError:
            logger.warning("psycopg (v3) not available - veto logging disabled")
            yield None
            return
        
        yield conn
        
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        yield None
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


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
    - Log veto events when trades are blocked (with deduplication)
    - Fetch aggregated veto data for dashboard
    - Query recent vetoes by type/symbol/time range
    
    DEDUPLICATION (Jan 8, 2026):
    - Vetoes are cached by (veto_type, symbol) for 15 minutes
    - Prevents inflated capital protection numbers for investor dashboards
    - Maintains full audit trail in database
    """
    
    _dedupe_cache: Dict[Tuple[str, str], float] = {}
    _cache_lock = threading.Lock()
    
    def __init__(self, db_connection_func):
        """
        Initialize with a database connection factory.
        
        Args:
            db_connection_func: Callable that returns a DB connection context manager
        """
        self._get_connection = db_connection_func
    
    def _is_duplicate(self, veto_type: str, symbol: str) -> bool:
        """
        Check if this veto was logged recently (within DEDUPE_WINDOW_SECONDS).
        Thread-safe implementation using class-level cache.
        
        NOTE: Does NOT update cache - caller must call _mark_logged() on success.
        
        Returns:
            True if duplicate (should skip), False if new (should log)
        """
        cache_key = (veto_type, symbol)
        current_time = time.time()
        
        with self._cache_lock:
            self._cleanup_expired_cache(current_time)
            
            if cache_key in self._dedupe_cache:
                last_logged = self._dedupe_cache[cache_key]
                if current_time - last_logged < DEDUPE_WINDOW_SECONDS:
                    return True
            
            return False
    
    def _mark_logged(self, veto_type: str, symbol: str):
        """Mark a veto as logged in the cache (call AFTER successful DB insert)."""
        cache_key = (veto_type, symbol)
        with self._cache_lock:
            self._dedupe_cache[cache_key] = time.time()
    
    def _cleanup_expired_cache(self, current_time: float):
        """Remove expired entries from cache (called inside lock)."""
        expired_keys = [
            key for key, timestamp in self._dedupe_cache.items()
            if current_time - timestamp >= DEDUPE_WINDOW_SECONDS
        ]
        for key in expired_keys:
            del self._dedupe_cache[key]
    
    def log_veto(
        self,
        veto_type: str,
        symbol: str,
        blocked_capital: float,
        reason: Optional[str] = None,
        user_id: Optional[int] = None,
        trade_id: Optional[int] = None,
        engine_stage: Optional[str] = None,
        market: str = "crypto",
        confidence: Optional[float] = None,
        severity: str = "MEDIUM",
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Log a veto event to the database with deduplication.
        
        DEDUPLICATION: Same (veto_type, symbol) logged within 15 minutes is skipped.
        This prevents inflated capital protection numbers while maintaining audit trail.
        
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
            True if logged successfully, False if duplicate/skipped/error
        """
        if self._is_duplicate(veto_type, symbol):
            logger.debug(f"⏭️ [VETO_SKIPPED] {veto_type} | {symbol} | Duplicate within {DEDUPE_WINDOW_SECONDS}s window")
            return False
        
        try:
            import json
            
            with self._get_connection() as conn:
                if not conn:
                    logger.warning("No DB connection - veto not logged (fail-open for logging)")
                    return False
                
                metadata_json = json.dumps(metadata or {})
                
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
                    metadata_json
                ))
                conn.commit()
                cursor.close()
                
                self._mark_logged(veto_type, symbol)
                
                logger.warning(f"📝 [VETO_LOGGED] {veto_type} | {symbol} | ${blocked_capital:,.2f} | DB_INSERT_SUCCESS")
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
        veto_type: Optional[str] = None,
        symbol: Optional[str] = None,
        hours: Optional[int] = None
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
    
    def get_vetoes_by_timerange(
        self, 
        start_date: str, 
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get veto summary for a specific date range.
        Used by AI to provide accurate audit reports without fabricating data.
        
        Args:
            start_date: ISO format date string (e.g., "2026-01-05")
            end_date: ISO format date string (e.g., "2026-01-06")
            
        Returns:
            Dict with summary by veto type and total for the period
        """
        try:
            with self._get_connection() as conn:
                if not conn:
                    return {
                        'has_data': False,
                        'error': 'Database not available',
                        'period': {'start': start_date, 'end': end_date},
                        'by_type': {},
                        'total_blocked': 0,
                        'total_count': 0
                    }
                
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        veto_type,
                        COUNT(*) as veto_count,
                        COALESCE(SUM(blocked_capital), 0) as total_blocked,
                        MIN(created_at) as first_veto,
                        MAX(created_at) as last_veto
                    FROM trading_veto_log
                    WHERE DATE(created_at) >= %s AND DATE(created_at) <= %s
                    GROUP BY veto_type
                    ORDER BY total_blocked DESC
                """, (start_date, end_date))
                
                rows = cursor.fetchall()
                cursor.close()
                
                if not rows:
                    return {
                        'has_data': False,
                        'error': None,
                        'period': {'start': start_date, 'end': end_date},
                        'by_type': {},
                        'total_blocked': 0,
                        'total_count': 0,
                        'message': f'No veto records found for period {start_date} to {end_date}'
                    }
                
                summary = {
                    'has_data': True,
                    'error': None,
                    'period': {'start': start_date, 'end': end_date},
                    'by_type': {},
                    'total_blocked': 0,
                    'total_count': 0
                }
                
                for row in rows:
                    veto_type = row[0]
                    count = row[1]
                    blocked = float(row[2])
                    first = row[3].isoformat() if row[3] else None
                    last = row[4].isoformat() if row[4] else None
                    
                    summary['by_type'][veto_type] = {
                        'count': count,
                        'blocked_capital': blocked,
                        'first_veto': first,
                        'last_veto': last
                    }
                    summary['total_blocked'] += blocked
                    summary['total_count'] += count
                
                logger.info(f"📊 Veto timerange query: {start_date} to {end_date} = {summary['total_count']} vetoes, ${summary['total_blocked']:,.2f}")
                return summary
                
        except Exception as e:
            logger.error(f"Failed to get vetoes by timerange: {e}")
            return {
                'has_data': False,
                'error': str(e),
                'period': {'start': start_date, 'end': end_date},
                'by_type': {},
                'total_blocked': 0,
                'total_count': 0
            }
    
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
    
    Uses standalone DATABASE_URL connection - works in both:
    - Bot context (Railway)
    - Dashboard context (Replit)
    
    Returns:
        VetoRepository instance or None if DB not available
    """
    global _veto_repository_instance
    
    if _veto_repository_instance is None:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.warning("DATABASE_URL not set - VetoRepository unavailable")
            return None
        
        _veto_repository_instance = VetoRepository(_standalone_db_connection)
        logger.info("VetoRepository initialized with standalone DATABASE_URL connection")
    
    return _veto_repository_instance
