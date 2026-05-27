"""
OMNIX V6.5.4d - Shadow Portfolio Repository

Tracks all vetoed trades for counterfactual analysis and filter calibration.
Enables the Learning Engine to determine which filters block good opportunities
vs which correctly protect capital.

Created: Jan 9, 2026
Purpose: Shadow Portfolio + Learning Engine (Phase 1 data collection)

USAGE:
- Call log_shadow_event() when a trade is vetoed to capture full context
- Use get_pending_outcomes() to find events needing counterfactual calculation
- Use update_outcome() to record what would have happened
- Use get_calibration_metrics() for filter tuning recommendations
"""

import logging
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal
from contextlib import contextmanager
from dataclasses import dataclass, asdict

logger = logging.getLogger("OMNIX.ShadowPortfolio")


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
            logger.warning("DATABASE_URL not set - shadow portfolio disabled")
            yield None
            return
        
        try:
            import psycopg
            conn = psycopg.connect(database_url)
        except ImportError:
            logger.warning("psycopg (v3) not available - shadow portfolio disabled")
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


@dataclass
class ShadowTradeEvent:
    """
    Data class representing a vetoed trade captured for counterfactual analysis.
    
    Contains all context needed to later determine if the veto was correct.
    """
    symbol: str
    intended_action: str
    veto_type: str
    
    market: str = "crypto"
    intended_quantity: Optional[float] = None
    intended_entry_price: Optional[float] = None
    intended_position_size_usd: Optional[float] = None
    
    veto_reason: Optional[str] = None
    blocked_capital: float = 0.0
    
    ema_score: Optional[float] = None
    ema_signal: Optional[str] = None
    hmm_regime: Optional[str] = None
    coherence_score: Optional[float] = None
    monte_carlo_er: Optional[float] = None
    black_swan_prob: Optional[float] = None
    kelly_fraction: Optional[float] = None
    strategy_confidence: Optional[float] = None
    
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    spread_bps: Optional[float] = None
    atr_14: Optional[float] = None
    volume_24h: Optional[float] = None
    volatility_1h: Optional[float] = None
    
    intended_stop_loss: Optional[float] = None
    intended_take_profit: Optional[float] = None
    intended_holding_period_hours: int = 24
    
    decision_trace: Optional[Dict] = None
    metadata: Optional[Dict] = None


class ShadowPortfolioRepository:
    """
    Repository for shadow portfolio events and counterfactual analysis.
    
    Provides methods to:
    - Log shadow trade events when trades are vetoed
    - Calculate and store counterfactual outcomes
    - Generate filter calibration metrics
    - Query shadow portfolio for dashboard
    
    Follows same patterns as VetoRepository for consistency.
    """
    
    def __init__(self, db_connection_func):
        """
        Initialize with a database connection factory.
        
        Args:
            db_connection_func: Callable that returns a DB connection context manager
        """
        self._get_connection = db_connection_func
    
    def log_shadow_event(self, event: ShadowTradeEvent) -> Optional[int]:
        """
        Log a shadow trade event when a trade is vetoed.
        
        Captures full market context for later counterfactual analysis.
        
        Args:
            event: ShadowTradeEvent with all trade and market context
            
        Returns:
            Event ID if logged successfully, None otherwise
        """
        try:
            with self._get_connection() as conn:
                if not conn:
                    logger.warning("No DB connection - shadow event not logged")
                    return None
                
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO shadow_trade_events (
                        symbol, market, intended_action, intended_quantity,
                        intended_entry_price, intended_position_size_usd,
                        veto_type, veto_reason, blocked_capital,
                        ema_score, ema_signal, hmm_regime, coherence_score,
                        monte_carlo_er, black_swan_prob, kelly_fraction, strategy_confidence,
                        bid_price, ask_price, spread_bps, atr_14, volume_24h, volatility_1h,
                        intended_stop_loss, intended_take_profit, intended_holding_period_hours,
                        decision_trace, metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING id
                """, (
                    event.symbol,
                    event.market,
                    event.intended_action,
                    event.intended_quantity,
                    event.intended_entry_price,
                    event.intended_position_size_usd,
                    event.veto_type,
                    event.veto_reason,
                    event.blocked_capital,
                    event.ema_score,
                    event.ema_signal,
                    event.hmm_regime,
                    event.coherence_score,
                    event.monte_carlo_er,
                    event.black_swan_prob,
                    event.kelly_fraction,
                    event.strategy_confidence,
                    event.bid_price,
                    event.ask_price,
                    event.spread_bps,
                    event.atr_14,
                    event.volume_24h,
                    event.volatility_1h,
                    event.intended_stop_loss,
                    event.intended_take_profit,
                    event.intended_holding_period_hours,
                    json.dumps(event.decision_trace or {}),
                    json.dumps(event.metadata or {})
                ))
                
                result = cursor.fetchone()
                event_id = result[0] if result else None
                conn.commit()
                cursor.close()
                
                logger.info(f"📝 [SHADOW_EVENT] {event.veto_type} | {event.symbol} | ${event.blocked_capital:,.2f} | ID={event_id}")
                return event_id
                
        except Exception as e:
            logger.error(f"Failed to log shadow event: {e}")
            return None
    
    def get_pending_outcomes(self, min_age_hours: int = 24, limit: int = 100) -> List[Dict]:
        """
        Get shadow events that need counterfactual outcome calculation.
        
        Returns events older than min_age_hours that haven't been analyzed yet.
        
        Args:
            min_age_hours: Minimum age of events to analyze (default 24h)
            limit: Maximum events to return
            
        Returns:
            List of event dictionaries needing analysis
        """
        try:
            with self._get_connection() as conn:
                if not conn:
                    return []
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, created_at, symbol, market, intended_action,
                           intended_entry_price, intended_stop_loss, intended_take_profit,
                           veto_type, intended_holding_period_hours
                    FROM shadow_trade_events
                    WHERE outcome_calculated = FALSE
                    AND created_at < NOW() - INTERVAL '%s hours'
                    ORDER BY created_at ASC
                    LIMIT %s
                """, (min_age_hours, limit))
                
                rows = cursor.fetchall()
                cursor.close()
                
                return [
                    {
                        'id': row[0],
                        'created_at': row[1],
                        'symbol': row[2],
                        'market': row[3],
                        'intended_action': row[4],
                        'intended_entry_price': float(row[5]) if row[5] else None,
                        'intended_stop_loss': float(row[6]) if row[6] else None,
                        'intended_take_profit': float(row[7]) if row[7] else None,
                        'veto_type': row[8],
                        'holding_period_hours': row[9] or 24
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Failed to get pending outcomes: {e}")
            return []
    
    def update_outcome(
        self,
        event_id: int,
        price_at_veto: float,
        prices: Dict[str, float],
        would_have_won: bool,
        counterfactual_pnl: Dict[str, float],
        max_drawdown_pct: float,
        max_favorable_pct: float,
        veto_was_correct: bool,
        verdict_reason: str
    ) -> bool:
        """
        Record the counterfactual outcome for a shadow event.
        
        Args:
            event_id: Shadow event ID
            price_at_veto: Price when trade was vetoed
            prices: Dict with price_after_1h, price_after_4h, etc.
            would_have_won: Whether trade would have been profitable
            counterfactual_pnl: Dict with pnl_1h, pnl_4h, etc.
            max_drawdown_pct: Maximum adverse movement
            max_favorable_pct: Maximum favorable movement
            veto_was_correct: Final verdict on whether veto was right
            verdict_reason: Explanation of verdict
            
        Returns:
            True if updated successfully
        """
        try:
            with self._get_connection() as conn:
                if not conn:
                    return False
                
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO shadow_trade_outcomes (
                        shadow_event_id,
                        price_at_veto,
                        price_after_1h, price_after_4h, price_after_24h,
                        price_after_7d, price_after_30d,
                        would_have_won,
                        counterfactual_pnl_1h, counterfactual_pnl_4h,
                        counterfactual_pnl_24h, counterfactual_pnl_7d, counterfactual_pnl_30d,
                        max_drawdown_pct, max_favorable_pct,
                        veto_was_correct, verdict_reason
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (shadow_event_id) DO UPDATE SET
                        calculated_at = NOW(),
                        price_at_veto = EXCLUDED.price_at_veto,
                        price_after_1h = EXCLUDED.price_after_1h,
                        price_after_4h = EXCLUDED.price_after_4h,
                        price_after_24h = EXCLUDED.price_after_24h,
                        price_after_7d = EXCLUDED.price_after_7d,
                        price_after_30d = EXCLUDED.price_after_30d,
                        would_have_won = EXCLUDED.would_have_won,
                        counterfactual_pnl_1h = EXCLUDED.counterfactual_pnl_1h,
                        counterfactual_pnl_4h = EXCLUDED.counterfactual_pnl_4h,
                        counterfactual_pnl_24h = EXCLUDED.counterfactual_pnl_24h,
                        counterfactual_pnl_7d = EXCLUDED.counterfactual_pnl_7d,
                        counterfactual_pnl_30d = EXCLUDED.counterfactual_pnl_30d,
                        max_drawdown_pct = EXCLUDED.max_drawdown_pct,
                        max_favorable_pct = EXCLUDED.max_favorable_pct,
                        veto_was_correct = EXCLUDED.veto_was_correct,
                        verdict_reason = EXCLUDED.verdict_reason
                """, (
                    event_id,
                    price_at_veto,
                    prices.get('1h'),
                    prices.get('4h'),
                    prices.get('24h'),
                    prices.get('7d'),
                    prices.get('30d'),
                    would_have_won,
                    counterfactual_pnl.get('1h'),
                    counterfactual_pnl.get('4h'),
                    counterfactual_pnl.get('24h'),
                    counterfactual_pnl.get('7d'),
                    counterfactual_pnl.get('30d'),
                    max_drawdown_pct,
                    max_favorable_pct,
                    veto_was_correct,
                    verdict_reason
                ))
                
                cursor.execute("""
                    UPDATE shadow_trade_events
                    SET outcome_calculated = TRUE,
                        outcome_calculated_at = NOW()
                    WHERE id = %s
                """, (event_id,))
                
                conn.commit()
                cursor.close()
                
                logger.info(f"📊 [SHADOW_OUTCOME] Event {event_id} | Veto correct: {veto_was_correct}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update outcome for event {event_id}: {e}")
            return False
    
    def get_calibration_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get filter calibration summary for the last N days.
        
        Shows which filters are accurate vs which need adjustment.
        
        Args:
            days: Look-back period
            
        Returns:
            Dict with calibration metrics per veto type
        """
        try:
            with self._get_connection() as conn:
                if not conn:
                    return self._empty_calibration()
                
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        e.veto_type,
                        COUNT(*) as total_vetoes,
                        COUNT(o.id) as vetoes_with_outcomes,
                        SUM(CASE WHEN o.veto_was_correct THEN 1 ELSE 0 END) as correct_vetoes,
                        SUM(CASE WHEN o.veto_was_correct = FALSE THEN 1 ELSE 0 END) as incorrect_vetoes,
                        AVG(o.counterfactual_pnl_24h) as avg_pnl_24h,
                        SUM(CASE WHEN o.would_have_won THEN 1 ELSE 0 END) as would_have_won_count,
                        SUM(e.blocked_capital) as total_blocked_capital
                    FROM shadow_trade_events e
                    LEFT JOIN shadow_trade_outcomes o ON e.id = o.shadow_event_id
                    WHERE e.created_at >= NOW() - INTERVAL '%s days'
                    GROUP BY e.veto_type
                    ORDER BY total_vetoes DESC
                """, (days,))
                
                rows = cursor.fetchall()
                cursor.close()
                
                summary = {
                    'period_days': days,
                    'by_veto_type': {},
                    'total_vetoes': 0,
                    'total_analyzed': 0,
                    'overall_accuracy': None
                }
                
                total_correct = 0
                total_analyzed = 0
                
                for row in rows:
                    veto_type = row[0]
                    total = row[1]
                    analyzed = row[2] or 0
                    correct = row[3] or 0
                    incorrect = row[4] or 0
                    avg_pnl = float(row[5]) if row[5] else None
                    won_count = row[6] or 0
                    blocked = float(row[7]) if row[7] else 0
                    
                    accuracy = (correct / analyzed * 100) if analyzed > 0 else None
                    win_rate_if_executed = (won_count / analyzed * 100) if analyzed > 0 else None
                    
                    summary['by_veto_type'][veto_type] = {
                        'total_vetoes': total,
                        'analyzed': analyzed,
                        'correct_vetoes': correct,
                        'incorrect_vetoes': incorrect,
                        'accuracy_pct': round(accuracy, 1) if accuracy else None,
                        'avg_counterfactual_pnl_24h': round(avg_pnl, 4) if avg_pnl else None,
                        'win_rate_if_executed': round(win_rate_if_executed, 1) if win_rate_if_executed else None,
                        'blocked_capital': blocked,
                        'recommendation': self._get_recommendation(accuracy, avg_pnl, win_rate_if_executed)
                    }
                    
                    summary['total_vetoes'] += total
                    total_analyzed += analyzed
                    total_correct += correct
                
                summary['total_analyzed'] = total_analyzed
                summary['overall_accuracy'] = round(total_correct / total_analyzed * 100, 1) if total_analyzed > 0 else None
                
                return summary
                
        except Exception as e:
            logger.error(f"Failed to get calibration summary: {e}")
            return self._empty_calibration()
    
    def _get_recommendation(
        self, 
        accuracy: Optional[float], 
        avg_pnl: Optional[float],
        win_rate: Optional[float]
    ) -> str:
        """Generate recommendation based on filter performance."""
        if accuracy is None:
            return "INSUFFICIENT_DATA"
        
        if accuracy >= 70:
            return "KEEP_CURRENT_THRESHOLD"
        elif accuracy >= 50:
            if avg_pnl and avg_pnl > 0:
                return "CONSIDER_LOOSENING"
            return "MONITOR"
        else:
            if win_rate and win_rate > 55:
                return "LOOSEN_THRESHOLD"
            return "REVIEW_FILTER_LOGIC"
    
    def _empty_calibration(self) -> Dict[str, Any]:
        """Return empty calibration structure."""
        return {
            'period_days': 0,
            'by_veto_type': {},
            'total_vetoes': 0,
            'total_analyzed': 0,
            'overall_accuracy': None
        }
    
    def get_recent_shadows(self, limit: int = 20) -> List[Dict]:
        """Get recent shadow events for dashboard display."""
        try:
            with self._get_connection() as conn:
                if not conn:
                    return []
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        e.id, e.created_at, e.symbol, e.veto_type,
                        e.intended_action, e.blocked_capital,
                        e.ema_score, e.coherence_score, e.hmm_regime,
                        o.veto_was_correct, o.counterfactual_pnl_24h
                    FROM shadow_trade_events e
                    LEFT JOIN shadow_trade_outcomes o ON e.id = o.shadow_event_id
                    ORDER BY e.created_at DESC
                    LIMIT %s
                """, (limit,))
                
                rows = cursor.fetchall()
                cursor.close()
                
                return [
                    {
                        'id': row[0],
                        'created_at': row[1].isoformat() if row[1] else None,
                        'symbol': row[2],
                        'veto_type': row[3],
                        'intended_action': row[4],
                        'blocked_capital': float(row[5]) if row[5] else 0,
                        'ema_score': float(row[6]) if row[6] else None,
                        'coherence_score': float(row[7]) if row[7] else None,
                        'hmm_regime': row[8],
                        'outcome_analyzed': row[9] is not None,
                        'veto_was_correct': row[9],
                        'counterfactual_pnl_24h': float(row[10]) if row[10] else None
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"Failed to get recent shadows: {e}")
            return []


_shadow_portfolio_instance: Optional[ShadowPortfolioRepository] = None


def get_shadow_portfolio_repository() -> Optional[ShadowPortfolioRepository]:
    """
    Get singleton ShadowPortfolioRepository instance.
    
    Uses standalone DATABASE_URL connection - works in both:
    - Bot context (Railway)
    - Dashboard context (Replit)
    
    Returns:
        ShadowPortfolioRepository instance or None if DB not available
    """
    global _shadow_portfolio_instance
    
    if _shadow_portfolio_instance is None:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.warning("DATABASE_URL not set - ShadowPortfolioRepository unavailable")
            return None
        
        _shadow_portfolio_instance = ShadowPortfolioRepository(_standalone_db_connection)
        logger.info("ShadowPortfolioRepository initialized with standalone DATABASE_URL connection")
    
    return _shadow_portfolio_instance
