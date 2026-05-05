"""
OMNIX Investor Data Provider - ADR-013

Proporciona datos SQL reales para respuestas de due diligence a inversores.
Read-only, sin exponer queries SQL crudas al usuario final.

Métricas disponibles:
1. Segmented Expectancy (régimen + coherence)
2. Fee Breakdown (fees totales, promedio, break-even)
3. Pre vs Post-Hotfix Stats (ADR-007: Jan 14, 2026)
4. Trade Size Analysis (by bucket)

Creado: Jan 16, 2026
Referencia: docs/reference/adr/ADR-013-investor-data-provider.md
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os

logger = logging.getLogger(__name__)

HOTFIX_DATE = datetime(2026, 1, 14)
DAY_1_TRACK_RECORD = datetime(2026, 1, 15)


from contextlib import contextmanager

@contextmanager
def _get_db_connection():
    """Get database connection using dashboard's DatabaseGateway.
    
    Returns a context manager that yields connection or None.
    Always safe to use with `with` statement.
    """
    try:
        from omnix_dashboard.utils.database import get_db_connection
        with get_db_connection() as conn:
            yield conn
    except ImportError:
        logger.warning("Dashboard database module not available")
        yield None
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        yield None


class InvestorDataProvider:
    """
    Proveedor de datos SQL reales para respuestas a inversores.
    
    Usado por ConversationalAIAdapter cuando detecta investor intent.
    Devuelve datos formateados que el AI puede citar directamente.
    """
    
    def __init__(self):
        self.hotfix_date = HOTFIX_DATE
        self.day1_date = DAY_1_TRACK_RECORD
    
    def get_all_investor_metrics(self) -> Dict[str, Any]:
        """
        Obtiene TODAS las métricas relevantes para inversores.
        Llamado cuando se detecta investor due diligence context.
        
        Returns:
            Dict con todas las métricas estructuradas para prompt injection
        """
        try:
            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'segmented_expectancy': self.get_segmented_expectancy(),
                'fee_breakdown': self.get_fee_breakdown(),
                'pre_post_hotfix': self.get_pre_post_hotfix_stats(),
                'trade_size_analysis': self.get_trade_size_analysis(),
                'data_quality': self.get_data_quality_metrics(),
                'formatted_summary': self._format_for_ai_prompt()
            }
        except Exception as e:
            logger.error(f"Error getting investor metrics: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_segmented_expectancy(self, days: int = 90) -> Dict[str, Any]:
        """
        Expectancy segmentada por (hmm_regime, coherence_bucket)
        
        Fórmula: E = (Win% × AvgWin) - (Loss% × |AvgLoss|)
        
        Returns:
            Dict con segmentos, mejor segmento, y expectancy global
        """
        with _get_db_connection() as conn:
            if not conn:
                return {'success': False, 'error': 'No database connection', 'segments': []}
            
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    WITH coherence_buckets AS (
                        SELECT 
                            id,
                            hmm_regime,
                            coherence_score,
                            profit_loss,
                            CASE 
                                WHEN coherence_score IS NULL THEN 'NO_DATA'
                                WHEN coherence_score < 40 THEN 'LOW (<40%)'
                                WHEN coherence_score < 70 THEN 'MED (40-70%)'
                                ELSE 'HIGH (70%+)'
                            END AS coherence_bucket
                        FROM paper_trading_trades
                        WHERE status = 'closed'
                          AND opened_at >= NOW() - INTERVAL '1 day' * %s
                          AND profit_loss IS NOT NULL
                    )
                    SELECT 
                        COALESCE(hmm_regime, 'UNKNOWN') as regime,
                        coherence_bucket,
                        COUNT(*) as trade_count,
                        COUNT(*) FILTER (WHERE profit_loss > 0) as wins,
                        COUNT(*) FILTER (WHERE profit_loss <= 0) as losses,
                        COALESCE(AVG(profit_loss) FILTER (WHERE profit_loss > 0), 0) as avg_win,
                        COALESCE(AVG(ABS(profit_loss)) FILTER (WHERE profit_loss <= 0), 0) as avg_loss,
                        SUM(profit_loss) as total_pnl
                    FROM coherence_buckets
                    GROUP BY hmm_regime, coherence_bucket
                    ORDER BY 
                        CASE hmm_regime 
                            WHEN 'BULLISH' THEN 1 
                            WHEN 'BEARISH' THEN 2 
                            WHEN 'RANGING' THEN 3 
                            ELSE 4 
                        END,
                        coherence_bucket
                ''', (days,))
                
                rows = cursor.fetchall()
                cursor.close()
                
                segments = []
                best_segment = None
                best_expectancy = float('-inf')
                total_pnl = 0
                total_trades = 0
                
                for row in rows:
                    regime = row[0]
                    coherence_bucket = row[1]
                    trade_count = row[2]
                    wins = row[3]
                    losses = row[4]
                    avg_win = float(row[5]) if row[5] else 0
                    avg_loss = float(row[6]) if row[6] else 0
                    segment_pnl = float(row[7]) if row[7] else 0
                    
                    win_rate = (wins / trade_count * 100) if trade_count > 0 else 0
                    loss_rate = 100 - win_rate
                    
                    expectancy = (win_rate/100 * avg_win) - (loss_rate/100 * avg_loss)
                    
                    segment = {
                        'regime': regime,
                        'coherence_bucket': coherence_bucket,
                        'trade_count': trade_count,
                        'wins': wins,
                        'losses': losses,
                        'win_rate': round(win_rate, 2),
                        'avg_win': round(avg_win, 2),
                        'avg_loss': round(avg_loss, 2),
                        'expectancy': round(expectancy, 2),
                        'total_pnl': round(segment_pnl, 2),
                        'profitable': expectancy > 0
                    }
                    segments.append(segment)
                    
                    total_pnl += segment_pnl
                    total_trades += trade_count
                    
                    if expectancy > best_expectancy:
                        best_expectancy = expectancy
                        best_segment = f"{regime} + {coherence_bucket}"
                
                global_expectancy = (total_pnl / total_trades) if total_trades > 0 else 0
                
                return {
                    'success': True,
                    'segments': segments,
                    'best_segment': best_segment,
                    'best_expectancy': round(best_expectancy, 2),
                    'global_expectancy': round(global_expectancy, 2),
                    'total_trades': total_trades,
                    'total_pnl': round(total_pnl, 2),
                    'days_analyzed': days
                }
                
            except Exception as e:
                logger.error(f"Error getting segmented expectancy: {e}")
                return {'success': False, 'error': str(e), 'segments': []}
    
    def get_basic_trading_stats(self) -> Dict[str, Any]:
        """
        Estadísticas básicas de trading separadas en dos períodos:
        - Learning Baseline: Nov 2025 – 14 Ene 2026 (fase de calibración)
        - Track Record Oficial: 15 Ene 2026 – hoy (sistema recalibrado)

        Usado por el modo diagnóstico para mostrar datos reales al usuario.
        """
        with _get_db_connection() as conn:
            if not conn:
                return {'success': False, 'error': 'No database connection'}
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        period,
                        COUNT(*)                                                         AS total_trades,
                        COUNT(*) FILTER (WHERE profit_loss > 0)                         AS winners,
                        ROUND(100.0 * COUNT(*) FILTER (WHERE profit_loss > 0)
                              / NULLIF(COUNT(*), 0), 2)                                 AS win_rate,
                        ROUND(COALESCE(SUM(profit_loss), 0)::numeric, 2)               AS total_pnl,
                        ROUND(COALESCE(AVG(profit_loss), 0)::numeric, 2)               AS avg_pnl,
                        ROUND(COALESCE(MIN(profit_loss), 0)::numeric, 2)               AS worst_trade,
                        ROUND(COALESCE(MAX(profit_loss), 0)::numeric, 2)               AS best_trade
                    FROM (
                        SELECT
                            profit_loss,
                            CASE
                                WHEN opened_at >= '2026-01-15' THEN 'track_record'
                                ELSE 'baseline'
                            END AS period
                        FROM paper_trading_trades
                        WHERE status = 'closed'
                          AND profit_loss IS NOT NULL
                    ) sub
                    GROUP BY period
                """)
                rows = cursor.fetchall()
                cursor.close()

                result = {'success': True, 'baseline': None, 'track_record': None}
                for row in rows:
                    period, total, winners, wr, total_pnl, avg_pnl, worst, best = row
                    entry = {
                        'total_trades': int(total),
                        'winners':      int(winners),
                        'win_rate':     float(wr or 0),
                        'total_pnl':   float(total_pnl or 0),
                        'avg_pnl':     float(avg_pnl or 0),
                        'worst_trade': float(worst or 0),
                        'best_trade':  float(best or 0),
                    }
                    result[period] = entry

                return result
            except Exception as e:
                logger.error(f"Error in get_basic_trading_stats: {e}")
                return {'success': False, 'error': str(e)}

    def get_fee_breakdown(self, days: int = 90) -> Dict[str, Any]:
        """
        Análisis de fees y break-even calculation.
        
        Returns:
            Dict con fees totales, promedio por trade, break-even fee %
        """
        with _get_db_connection() as conn:
            if not conn:
                return {'success': False, 'error': 'No database connection'}
            
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(profit_loss) as gross_pnl,
                        AVG(ABS(profit_loss)) as avg_trade_size,
                        COUNT(*) FILTER (WHERE profit_pct > 0 AND profit_loss <= 0) as fee_eroded,
                        AVG(profit_pct) as avg_pnl_pct,
                        AVG(ABS(profit_pct)) FILTER (WHERE profit_loss > 0) as avg_win_pct,
                        AVG(ABS(profit_pct)) FILTER (WHERE profit_loss <= 0) as avg_loss_pct
                    FROM paper_trading_trades
                    WHERE status = 'closed'
                      AND opened_at >= NOW() - INTERVAL '1 day' * %s
                ''', (days,))
                
                row = cursor.fetchone()
                cursor.close()
                
                if not row:
                    return {'success': False, 'error': 'No trades found'}
                
                total_trades = row[0] or 0
                gross_pnl = float(row[1]) if row[1] else 0
                avg_trade_size = float(row[2]) if row[2] else 0
                fee_eroded = row[3] or 0
                avg_pnl_pct = float(row[4]) if row[4] else 0
                avg_win_pct = float(row[5]) if row[5] else 0
                avg_loss_pct = float(row[6]) if row[6] else 0
                
                kraken_fee = 0.26
                estimated_total_fees = total_trades * avg_trade_size * (kraken_fee / 100) * 2
                avg_fee_per_trade = (estimated_total_fees / total_trades) if total_trades > 0 else 0
                
                break_even_trades = 0
                if avg_win_pct > 0:
                    break_even_fee_pct = avg_pnl_pct + (kraken_fee * 2)
                else:
                    break_even_fee_pct = kraken_fee * 2
                
                return {
                    'success': True,
                    'total_trades': total_trades,
                    'gross_pnl': round(gross_pnl, 2),
                    'estimated_total_fees': round(estimated_total_fees, 2),
                    'avg_fee_per_trade': round(avg_fee_per_trade, 2),
                    'kraken_fee_pct': kraken_fee,
                    'fee_eroded_trades': fee_eroded,
                    'fee_erosion_rate': round((fee_eroded / total_trades * 100) if total_trades > 0 else 0, 2),
                    'avg_win_pct': round(avg_win_pct, 2),
                    'avg_loss_pct': round(avg_loss_pct, 2),
                    'break_even_move_pct': round(break_even_fee_pct, 2),
                    'analysis': f"Kraken fee {kraken_fee}% x2 (entry+exit) = {kraken_fee*2}%. Trade must move >{break_even_fee_pct:.2f}% to profit."
                }
                
            except Exception as e:
                logger.error(f"Error getting fee breakdown: {e}")
                return {'success': False, 'error': str(e)}
    
    def get_pre_post_hotfix_stats(self) -> Dict[str, Any]:
        """
        Comparación pre vs post-hotfix (ADR-007: Jan 14, 2026).
        
        Returns:
            Dict con métricas antes y después de la calibración
        """
        with _get_db_connection() as conn:
            if not conn:
                return {'success': False, 'error': 'No database connection'}
            
            try:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        CASE WHEN opened_at < %s THEN 'PRE_HOTFIX' ELSE 'POST_HOTFIX' END as period,
                        COUNT(*) as trades,
                        COUNT(*) FILTER (WHERE profit_loss > 0) as wins,
                        SUM(profit_loss) as pnl,
                        AVG(profit_loss) as avg_pnl,
                        AVG(coherence_score) as avg_coherence,
                        COALESCE(telemetry_source, 'LEGACY') as telemetry
                    FROM paper_trading_trades
                    WHERE status = 'closed'
                    GROUP BY 
                        CASE WHEN opened_at < %s THEN 'PRE_HOTFIX' ELSE 'POST_HOTFIX' END,
                        COALESCE(telemetry_source, 'LEGACY')
                    ORDER BY period, telemetry
                ''', (self.hotfix_date, self.hotfix_date))
                
                rows = cursor.fetchall()
                cursor.close()
                
                pre_hotfix = {'trades': 0, 'wins': 0, 'pnl': 0, 'avg_coherence': 0}
                post_hotfix = {'trades': 0, 'wins': 0, 'pnl': 0, 'avg_coherence': 0}
                
                for row in rows:
                    period = row[0]
                    trades = row[1]
                    wins = row[2]
                    pnl = float(row[3]) if row[3] else 0
                    avg_pnl = float(row[4]) if row[4] else 0
                    avg_coh = float(row[5]) if row[5] else 0
                    
                    if period == 'PRE_HOTFIX':
                        pre_hotfix['trades'] += trades
                        pre_hotfix['wins'] += wins
                        pre_hotfix['pnl'] += pnl
                        if avg_coh > 0:
                            pre_hotfix['avg_coherence'] = avg_coh
                    else:
                        post_hotfix['trades'] += trades
                        post_hotfix['wins'] += wins
                        post_hotfix['pnl'] += pnl
                        if avg_coh > 0:
                            post_hotfix['avg_coherence'] = avg_coh
                
                pre_wr = (pre_hotfix['wins'] / pre_hotfix['trades'] * 100) if pre_hotfix['trades'] > 0 else 0
                post_wr = (post_hotfix['wins'] / post_hotfix['trades'] * 100) if post_hotfix['trades'] > 0 else 0
                
                wr_improvement = post_wr - pre_wr
                pnl_improvement = post_hotfix['pnl'] - pre_hotfix['pnl']
                
                return {
                    'success': True,
                    'hotfix_date': self.hotfix_date.strftime('%Y-%m-%d'),
                    'hotfix_reference': 'ADR-007 Coherence Threshold Calibration',
                    'pre_hotfix': {
                        'trades': pre_hotfix['trades'],
                        'wins': pre_hotfix['wins'],
                        'win_rate': round(pre_wr, 2),
                        'pnl': round(pre_hotfix['pnl'], 2),
                        'avg_coherence': round(pre_hotfix['avg_coherence'], 2),
                        'telemetry': 'LEGACY_ESTIMATED (backfilled)'
                    },
                    'post_hotfix': {
                        'trades': post_hotfix['trades'],
                        'wins': post_hotfix['wins'],
                        'win_rate': round(post_wr, 2),
                        'pnl': round(post_hotfix['pnl'], 2),
                        'avg_coherence': round(post_hotfix['avg_coherence'], 2),
                        'telemetry': 'REAL'
                    },
                    'improvement': {
                        'win_rate_delta': round(wr_improvement, 2),
                        'pnl_delta': round(pnl_improvement, 2),
                        'statistically_significant': post_hotfix['trades'] >= 30
                    }
                }
                
            except Exception as e:
                logger.error(f"Error getting pre/post hotfix stats: {e}")
                return {'success': False, 'error': str(e)}
    
    def get_trade_size_analysis(self) -> Dict[str, Any]:
        """
        Análisis de rentabilidad por tamaño de trade.
        Basado en ADR-004 Position Sizing Hotfix.
        
        Returns:
            Dict con win rate por bucket de tamaño
        """
        with _get_db_connection() as conn:
            if not conn:
                return {'success': False, 'error': 'No database connection'}
            
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        CASE 
                            WHEN ABS(profit_loss) < 100 THEN 'MICRO (<$100)'
                            WHEN ABS(profit_loss) < 1000 THEN 'SMALL ($100-$1K)'
                            WHEN ABS(profit_loss) < 10000 THEN 'MEDIUM ($1K-$10K)'
                            ELSE 'LARGE ($10K+)'
                        END AS size_bucket,
                        COUNT(*) as trades,
                        COUNT(*) FILTER (WHERE profit_loss > 0) as wins,
                        SUM(profit_loss) as pnl,
                        AVG(profit_loss) as avg_pnl
                    FROM paper_trading_trades
                    WHERE status = 'closed'
                    GROUP BY 1
                    ORDER BY 
                        CASE 
                            WHEN ABS(profit_loss) < 100 THEN 1
                            WHEN ABS(profit_loss) < 1000 THEN 2
                            WHEN ABS(profit_loss) < 10000 THEN 3
                            ELSE 4
                        END
                ''')
                
                rows = cursor.fetchall()
                cursor.close()
                
                buckets = []
                for row in rows:
                    size_bucket = row[0]
                    trades = row[1]
                    wins = row[2]
                    pnl = float(row[3]) if row[3] else 0
                    avg_pnl = float(row[4]) if row[4] else 0
                    
                    win_rate = (wins / trades * 100) if trades > 0 else 0
                    
                    buckets.append({
                        'size_bucket': size_bucket,
                        'trades': trades,
                        'wins': wins,
                        'win_rate': round(win_rate, 2),
                        'pnl': round(pnl, 2),
                        'avg_pnl': round(avg_pnl, 2),
                        'profitable': pnl > 0
                    })
                
                best_bucket = max(buckets, key=lambda x: x['win_rate']) if buckets else None
                worst_bucket = min(buckets, key=lambda x: x['win_rate']) if buckets else None
                
                return {
                    'success': True,
                    'buckets': buckets,
                    'best_bucket': best_bucket['size_bucket'] if best_bucket else None,
                    'best_win_rate': best_bucket['win_rate'] if best_bucket else 0,
                    'worst_bucket': worst_bucket['size_bucket'] if worst_bucket else None,
                    'worst_win_rate': worst_bucket['win_rate'] if worst_bucket else 0,
                    'recommendation': f"Focus on {best_bucket['size_bucket'] if best_bucket else 'N/A'} trades (WR: {best_bucket['win_rate'] if best_bucket else 0}%)"
                }
                
            except Exception as e:
                logger.error(f"Error getting trade size analysis: {e}")
                return {'success': False, 'error': str(e)}
    
    def get_data_quality_metrics(self) -> Dict[str, Any]:
        """
        Métricas de calidad de datos para transparencia.
        
        Returns:
            Dict con % de trades con telemetría real vs estimada
        """
        with _get_db_connection() as conn:
            if not conn:
                return {'success': False, 'error': 'No database connection'}
            
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        COALESCE(telemetry_source, 'LEGACY') as source,
                        COUNT(*) as count
                    FROM paper_trading_trades
                    WHERE status = 'closed'
                    GROUP BY 1
                ''')
                
                rows = cursor.fetchall()
                cursor.close()
                
                sources = {}
                total = 0
                for row in rows:
                    source = row[0]
                    count = row[1]
                    sources[source] = count
                    total += count
                
                real_pct = (sources.get('REAL', 0) / total * 100) if total > 0 else 0
                legacy_pct = 100 - real_pct
                
                return {
                    'success': True,
                    'total_trades': total,
                    'real_telemetry': sources.get('REAL', 0),
                    'legacy_estimated': total - sources.get('REAL', 0),
                    'real_pct': round(real_pct, 1),
                    'legacy_pct': round(legacy_pct, 1),
                    'data_quality_score': round(real_pct, 0),
                    'note': 'REAL = post-Jan 15, 2026 with full telemetry. LEGACY_ESTIMATED = pre-Jan 15 with backfilled metrics.'
                }
                
            except Exception as e:
                logger.error(f"Error getting data quality metrics: {e}")
                return {'success': False, 'error': str(e)}
    
    def _format_for_ai_prompt(self) -> str:
        """
        Formatea todos los datos para inyección directa en prompt del AI.
        
        Returns:
            String formateado listo para incluir en respuesta
        """
        try:
            seg = self.get_segmented_expectancy(days=90)
            fees = self.get_fee_breakdown(days=90)
            hotfix = self.get_pre_post_hotfix_stats()
            sizes = self.get_trade_size_analysis()
            quality = self.get_data_quality_metrics()
            
            prompt = f"""
## INVESTOR DATA (Real PostgreSQL Queries - {datetime.now().strftime('%Y-%m-%d %H:%M')})

### Segmented Expectancy (Last 90 Days)
- **Best Segment**: {seg.get('best_segment', 'N/A')} → Expectancy: ${seg.get('best_expectancy', 0)}/trade
- **Global Expectancy**: ${seg.get('global_expectancy', 0)}/trade
- **Total Trades Analyzed**: {seg.get('total_trades', 0)}
- **Total P&L**: ${seg.get('total_pnl', 0):,.2f}

### Fee Analysis (Kraken {fees.get('kraken_fee_pct', 0.26)}% per side)
- **Fee-Eroded Trades**: {fees.get('fee_eroded_trades', 0)} ({fees.get('fee_erosion_rate', 0)}%)
- **Break-Even Move Required**: >{fees.get('break_even_move_pct', 0.52)}% to profit
- **Avg Fee Per Trade**: ${fees.get('avg_fee_per_trade', 0):.2f}

### Pre vs Post-Hotfix (ADR-007: {hotfix.get('hotfix_date', 'Jan 14, 2026')})
| Period | Trades | Win Rate | P&L |
|--------|--------|----------|-----|
| Pre-Hotfix | {hotfix.get('pre_hotfix', {}).get('trades', 0)} | {hotfix.get('pre_hotfix', {}).get('win_rate', 0)}% | ${hotfix.get('pre_hotfix', {}).get('pnl', 0):,.2f} |
| Post-Hotfix | {hotfix.get('post_hotfix', {}).get('trades', 0)} | {hotfix.get('post_hotfix', {}).get('win_rate', 0)}% | ${hotfix.get('post_hotfix', {}).get('pnl', 0):,.2f} |
| **Delta** | - | {hotfix.get('improvement', {}).get('win_rate_delta', 0):+.2f}% | ${hotfix.get('improvement', {}).get('pnl_delta', 0):+,.2f} |

### Trade Size Analysis (ADR-004 Insight)
- **Best Bucket**: {sizes.get('best_bucket', 'N/A')} → WR: {sizes.get('best_win_rate', 0)}%
- **Worst Bucket**: {sizes.get('worst_bucket', 'N/A')} → WR: {sizes.get('worst_win_rate', 0)}%

### Data Quality
- **Real Telemetry**: {quality.get('real_pct', 0)}% ({quality.get('real_telemetry', 0)} trades)
- **Legacy Estimated**: {quality.get('legacy_pct', 0)}% ({quality.get('legacy_estimated', 0)} trades)
"""
            return prompt.strip()
            
        except Exception as e:
            logger.error(f"Error formatting for AI prompt: {e}")
            return f"[Investor data unavailable: {str(e)}]"


investor_data_provider = InvestorDataProvider()


def get_investor_data_for_ai() -> Dict[str, Any]:
    """
    Función helper para obtener datos de inversor.
    Usada por ConversationalAIAdapter.
    """
    return investor_data_provider.get_all_investor_metrics()


def get_formatted_investor_data() -> str:
    """
    Obtiene datos formateados para inyección directa en prompt.
    """
    return investor_data_provider._format_for_ai_prompt()
