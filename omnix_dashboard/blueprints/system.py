"""
OMNIX Dashboard - System Blueprint
System API routes (/api/system/status, /api/debug, /api/signals/active)
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Blueprint, jsonify

from omnix_dashboard.utils.database import (
    get_db_connection, get_database_url, init_database,
    get_pool_stats, DB_AVAILABLE, DB_ERROR_MESSAGE
)
from omnix_dashboard.utils.decorators import require_api_key
from omnix_dashboard.utils.queries import get_paper_trades, consolidated_trade_metrics

logger = logging.getLogger(__name__)

system_bp = Blueprint('system', __name__)


@system_bp.route('/api/signals/active')
@require_api_key
def api_active_signals():
    """API endpoint for active trading signals - connected to real DB"""
    signals = []
    
    with get_db_connection() as conn:
        if conn:
            try:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT symbol, side, strategy, status, opened_at, entry_price
                    FROM paper_trading_trades
                    WHERE opened_at >= NOW() - INTERVAL '24 hours'
                    ORDER BY opened_at DESC
                    LIMIT 10
                ''')
                
                recent_trades = cursor.fetchall()
                
                symbol_stats = {}
                for trade in recent_trades:
                    symbol = trade[0]
                    side = trade[1]
                    strategy = trade[2] or 'OMNIX'
                    
                    if symbol not in symbol_stats:
                        symbol_stats[symbol] = {'buys': 0, 'sells': 0, 'strategies': set()}
                    
                    if side == 'buy':
                        symbol_stats[symbol]['buys'] += 1
                    else:
                        symbol_stats[symbol]['sells'] += 1
                    symbol_stats[symbol]['strategies'].add(strategy)
                
                for symbol, stats in symbol_stats.items():
                    total = stats['buys'] + stats['sells']
                    if total > 0:
                        buy_ratio = stats['buys'] / total
                        
                        if buy_ratio > 0.7:
                            signal_type = 'BULLISH'
                        elif buy_ratio < 0.3:
                            signal_type = 'BEARISH'
                        else:
                            signal_type = 'NEUTRAL'
                        
                        signals.append({
                            'strategy': list(stats['strategies'])[0] if stats['strategies'] else 'OMNIX',
                            'symbol': symbol,
                            'signal': signal_type,
                            'buy_ratio': round(buy_ratio, 2),
                            'trades_24h': total,
                            'source': 'paper_trading_trades',
                            'timestamp': datetime.now().isoformat()
                        })
                
                cursor.execute('''
                    SELECT symbol, side, strategy, entry_price, opened_at
                    FROM paper_trading_trades
                    WHERE status = 'open'
                    ORDER BY opened_at DESC
                ''')
                
                open_positions = cursor.fetchall()
                for pos in open_positions:
                    existing = next((s for s in signals if s['symbol'] == pos[0]), None)
                    if not existing:
                        signals.append({
                            'strategy': pos[2] or 'OMNIX',
                            'symbol': pos[0],
                            'signal': 'LONG' if pos[1] == 'buy' else 'SHORT',
                            'position_open': True,
                            'entry_price': float(pos[3]) if pos[3] else None,
                            'source': 'paper_trading_trades',
                            'timestamp': pos[4].isoformat() if pos[4] else datetime.now().isoformat()
                        })
                
                cursor.close()
                logger.info(f"Generated {len(signals)} signals from real trading data")
                
            except Exception as e:
                logger.error(f"Error fetching signals from DB: {e}")
    
    return jsonify({
        'success': True,
        'signals': signals,
        'count': len(signals),
        'message': 'No active signals — no trading activity in last 24h' if not signals else None,
        'source': 'PostgreSQL',
        'timestamp': datetime.now().isoformat()
    })


@system_bp.route('/api/system/status')
def api_system_status():
    """API endpoint for OMNIX system status - connected to real DB"""
    from omnix_dashboard.utils.database import DB_AVAILABLE
    
    trades = get_paper_trades(1)
    open_positions = len([t for t in trades if t.get('status') == 'open'])
    trades_today = len(trades)
    
    bot_active = False
    trading_enabled = False
    daily_pnl = 0.0
    user_settings_data = {}
    strategy_counts = {}
    
    with get_db_connection() as conn:
        if conn:
            try:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT auto_trading, trading_enabled, daily_pnl_usd, 
                           allowed_cryptos, protection_settings,
                           risk_profile, updated_at
                    FROM user_settings
                    ORDER BY updated_at DESC
                    LIMIT 1
                ''')
                
                settings_row = cursor.fetchone()
                if settings_row:
                    bot_active = bool(settings_row[0])
                    trading_enabled = bool(settings_row[1])
                    daily_pnl = float(settings_row[2]) if settings_row[2] else 0.0
                    allowed_cryptos = settings_row[3] if settings_row[3] else ['BTC/USD', 'ETH/USD']
                    protection = settings_row[4] if settings_row[4] else {}
                    user_settings_data = {
                        'active_cryptos': allowed_cryptos,
                        'stop_loss_pct': protection.get('stop_loss_pct', 3.0),
                        'take_profit_pct': protection.get('take_profit_pct', 5.0),
                        'risk_profile': settings_row[5] or 'moderado',
                        'last_updated': settings_row[6].isoformat() if settings_row[6] else None
                    }
                
                cursor.execute('''
                    SELECT strategy, COUNT(*) as cnt
                    FROM paper_trading_trades
                    WHERE opened_at >= NOW() - INTERVAL '24 hours'
                    GROUP BY strategy
                ''')
                
                strategy_counts = {row[0]: row[1] for row in cursor.fetchall()}
                cursor.close()
                
            except Exception as e:
                logger.error(f"Error reading user_settings: {e}")
    
    strategies = {}
    if strategy_counts:
        for strat_name, signal_count in strategy_counts.items():
            strategies[strat_name] = {'active': True, 'signals_today': signal_count}
    
    if not strategies:
        strategies = {
            'OMNIX_Core': {'active': bot_active, 'signals_today': trades_today},
            'Auto_Trading_Bot': {'active': bot_active, 'signals_today': open_positions}
        }
    
    drawdown_tier = 'NORMAL'
    risk_level = 'LOW'
    if daily_pnl < -500:
        drawdown_tier = 'CRITICAL'
        risk_level = 'CRITICAL'
    elif daily_pnl < -200:
        drawdown_tier = 'WARNING'
        risk_level = 'HIGH'
    elif daily_pnl < 0:
        drawdown_tier = 'CAUTION'
        risk_level = 'MEDIUM'
    
    status = {
        'bot_active': bot_active,
        'trading_enabled': trading_enabled,
        'version': 'DGI',
        'uptime': '24/7 Railway',
        'last_activity': datetime.now().isoformat(),
        'database_connected': DB_AVAILABLE,
        'daily_pnl_usd': round(daily_pnl, 2),
        'strategies': strategies,
        'protection': {
            'drawdown_tier': drawdown_tier,
            'ramp_up_pct': 100 if drawdown_tier == 'NORMAL' else (75 if drawdown_tier == 'CAUTION' else 50),
            'daily_loss_limit': user_settings_data.get('stop_loss_pct', 3.0) * 100,
            'position_size_factor': 1.0 if drawdown_tier == 'NORMAL' else (0.75 if drawdown_tier == 'CAUTION' else 0.5)
        },
        'risk_guardian': {
            'status': 'ACTIVE',
            'module': 'risk_guardian',
            'risk_level': risk_level,
            'circuit_breaker': {
                'active': drawdown_tier == 'CRITICAL',
                'trigger_reason': 'Daily loss limit exceeded' if drawdown_tier == 'CRITICAL' else None,
                'cooldown_remaining': 0
            },
            'overtrading_protection': {
                'enabled': True,
                'max_trades_per_day': 20,
                'max_trades_per_hour': 10,
                'trades_today': trades_today,
                'blocked': trades_today >= 20
            },
            'revenge_trading': {
                'enabled': True,
                'consecutive_losses_trigger': 3,
                'blocked': False,
                'cooldown_remaining': 0
            },
            'capital_protection': {
                'enabled': True,
                'max_risk_per_trade_pct': 2.0,
                'max_daily_loss_pct': 5.0,
                'current_daily_loss_pct': abs(min(daily_pnl, 0)) / 10000 * 100 if daily_pnl < 0 else 0
            },
            'limits': {
                'drawdown_10pct': {'action': 'reduce_size', 'triggered': False},
                'drawdown_20pct': {'action': 'stop_trading', 'triggered': drawdown_tier == 'CRITICAL'}
            }
        },
        'trading': {
            'open_positions': open_positions,
            'trades_today': trades_today,
            'pairs_active': user_settings_data.get('active_cryptos', ['BTC/USD', 'ETH/USD', 'SOL/USD'])
        },
        'user_settings': user_settings_data,
        'source': 'PostgreSQL',
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify({
        'success': True,
        'status': status
    })


@system_bp.route('/api/system/adaptive')
@require_api_key
def api_system_adaptive():
    """API endpoint for Adaptive Parameter Engine ULTRA telemetry"""
    from omnix_dashboard.utils.database import DB_AVAILABLE
    
    current_regime = None
    regime_confidence = None
    strategy_weights = {}
    calibration_history = []
    
    with get_db_connection() as conn:
        if conn:
            try:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT strategy, COUNT(*) as cnt,
                           AVG(CASE WHEN profit_loss > 0 THEN 1.0 ELSE 0.0 END) as win_rate
                    FROM paper_trading_trades
                    WHERE opened_at >= NOW() - INTERVAL '24 hours'
                    GROUP BY strategy
                ''')
                
                for row in cursor.fetchall():
                    strat_name = row[0] or 'OMNIX_Core'
                    trade_count = row[1]
                    win_rate = float(row[2]) if row[2] else 0.5
                    
                    weight = min(1.0, 0.4 + win_rate * 0.6)
                    strategy_weights[strat_name] = {
                        'weight': round(weight, 3),
                        'trades_24h': trade_count,
                        'win_rate': round(win_rate * 100, 1),
                        'status': 'ACTIVE' if weight > 0.5 else 'REDUCED'
                    }
                
                cursor.execute('''
                    SELECT strategy, 
                           SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins,
                           SUM(CASE WHEN profit_loss <= 0 THEN 1 ELSE 0 END) as losses,
                           AVG(profit_loss) as avg_pnl
                    FROM paper_trading_trades
                    WHERE closed_at >= NOW() - INTERVAL '7 days'
                    GROUP BY strategy
                ''')
                
                rows = cursor.fetchall()
                if rows:
                    total_wins = sum(r[1] or 0 for r in rows)
                    total_losses = sum(r[2] or 0 for r in rows)
                    total_trades = total_wins + total_losses
                    
                    if total_trades > 0:
                        overall_win_rate = total_wins / total_trades
                        if overall_win_rate > 0.6:
                            current_regime = 'TRENDING'
                            regime_confidence = min(0.95, 0.7 + overall_win_rate * 0.3)
                        elif overall_win_rate < 0.4:
                            current_regime = 'VOLATILE'
                            regime_confidence = 0.7
                        else:
                            current_regime = 'RANGING'
                            regime_confidence = 0.6
                
                cursor.close()
                
            except Exception as e:
                logger.error(f"Error reading adaptive engine data: {e}")
    
    if not strategy_weights:
        strategy_weights = {}
    
    main_driver = None
    max_weight = 0
    for name, data in strategy_weights.items():
        if data['weight'] >= 0.80 and data['weight'] > max_weight:
            max_weight = data['weight']
            main_driver = name
    
    adaptive_data = {
        'engine': 'adaptive',
        'status': 'ACTIVE',
        'main_driver': {
            'name': main_driver,
            'weight': max_weight,
            'description': 'ANU Quantum Random Number Generator for momentum detection' if main_driver == 'Quantum_Momentum' else 'Non-Markovian temporal memory kernel',
            'is_quantum': main_driver == 'Quantum_Momentum'
        } if main_driver else None,
        'regime': {
            'current': current_regime,
            'confidence': round(regime_confidence, 2) if regime_confidence is not None else None,
            'detected_at': datetime.now().isoformat(),
            'history': [
                {'regime': current_regime, 'duration_hours': 4, 'confidence': regime_confidence}
            ]
        },
        'calibration': {
            'last_run': datetime.now().isoformat(),
            'next_scheduled': (datetime.now() + timedelta(hours=1)).isoformat(),
            'strategies_calibrated': len(strategy_weights),
            'auto_calibration': True
        },
        'strategy_weights': strategy_weights,
        'kernel_params': {
            'tau': 12.0,
            'epsilon': 0.35,
            'omega': 0.523,
            'memory_window': 168,
            'description': 'Non-Markovian Memory Kernel parameters'
        },
        'performance_metrics': {
            'status': 'insufficient_data',
            'message': 'Requires real-time calibration telemetry (not available in demo)',
            'source': None
        },
        'source': 'PostgreSQL' if DB_AVAILABLE else 'defaults',
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify({
        'success': True,
        'adaptive': adaptive_data
    })


@system_bp.route('/api/debug')
@require_api_key
def api_debug():
    """Debug endpoint to diagnose connection issues (no secrets exposed)"""
    from omnix_dashboard.utils.database import DB_AVAILABLE, DB_ERROR_MESSAGE
    
    env_vars_status = {
        'DATABASE_URL': 'SET' if os.environ.get('DATABASE_URL') else 'NOT SET',
        'POSTGRES_URL': 'SET' if os.environ.get('POSTGRES_URL') else 'NOT SET',
        'DATABASE_PUBLIC_URL': 'SET' if os.environ.get('DATABASE_PUBLIC_URL') else 'NOT SET',
    }
    
    database_url = get_database_url()
    url_info = None
    if database_url:
        if '@' in database_url:
            host_part = database_url.split('@')[-1].split('/')[0] if '@' in database_url else 'unknown'
            url_info = f"Host: {host_part[:50]}..."
        else:
            url_info = "URL format: invalid (no @ symbol)"
    
    init_database()
    
    psycopg_installed = False
    try:
        import psycopg
        psycopg_installed = True
        psycopg_version = getattr(psycopg, '__version__', 'unknown')
    except ImportError:
        psycopg_version = 'NOT INSTALLED'
    
    return jsonify({
        'status': 'debug_info',
        'environment_variables': env_vars_status,
        'database_url_detected': database_url is not None,
        'database_url_info': url_info,
        'psycopg_installed': psycopg_installed,
        'psycopg_version': psycopg_version,
        'db_connected': DB_AVAILABLE,
        'db_error': DB_ERROR_MESSAGE,
        'python_version': os.popen('python --version').read().strip(),
        'timestamp': datetime.now().isoformat()
    })


@system_bp.route('/api/db-diagnostics')
@require_api_key
def api_db_diagnostics():
    """
    Phase 1 Database Diagnostics Endpoint (Dec 2025)
    
    Returns real-time pool statistics and Enterprise Service health.
    Used for monitoring connection pool contention before service unification.
    """
    warnings = []
    enterprise_health = {
        'connected': False,
        'using_enterprise': False,
        'auto_migrations_enabled': True,
        'last_connection_latency_ms': None
    }
    
    pool_stats = get_pool_stats()
    
    try:
        from omnix_services.database_service import db_service
        if db_service:
            health = db_service.health_check()
            enterprise_health = {
                'connected': health.get('database_connected', False),
                'using_enterprise': getattr(db_service, 'using_enterprise', False),
                'auto_migrations_enabled': health.get('auto_migrations_enabled', True),
                'psycopg_available': health.get('psycopg_available', False)
            }
    except ImportError:
        enterprise_health['error'] = 'Enterprise service not available'
    except Exception as e:
        enterprise_health['error'] = str(e)[:100]
    
    if pool_stats.get('status') == 'active' and enterprise_health.get('connected'):
        warnings.append("Two parallel DB services detected - consolidation recommended (see DATABASE_AUDIT_REPORT.md)")
    
    if pool_stats.get('requests_waiting', 0) > 0:
        warnings.append(f"Pool contention detected: {pool_stats.get('requests_waiting')} requests waiting")
    
    pool_available = pool_stats.get('pool_available', 0)
    pool_size = pool_stats.get('pool_size', 1)
    if pool_size > 0 and pool_available / pool_size < 0.2:
        warnings.append(f"Pool utilization high: only {pool_available}/{pool_size} connections available")
    
    return jsonify({
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'dashboard_pool': pool_stats,
        'enterprise_service': enterprise_health,
        'warnings': warnings,
        'phase': 'Phase 1: Discovery & Freeze',
        'documentation': 'docs/core/DATABASE_AUDIT_REPORT.md (Section 14)'
    })


@system_bp.route('/api/health/bootstrap')
def api_health_bootstrap():
    """
    Phase 5: DI Container and Adapter Health Telemetry
    
    Returns initialization status for all V7.0 hexagonal architecture components:
    - Database and Cache connectivity
    - Phase 2 adapters (Trading, Risk, Coherence)
    - Phase 3 adapters (Kraken, Gemini, Telegram)
    - Application layer feature flag status
    """
    container_health = {
        'available': False,
        'database': False,
        'cache': False,
        'settings': False,
        'use_app_layer': False,
        'adapters': {
            'trading': False,
            'risk': False,
            'coherence': False,
            'kraken': {'available': False, 'connected': False},
            'gemini': {'available': False, 'provider': 'none'},
            'telegram': {'available': False, 'running': False}
        },
        'database_manager': False
    }
    
    try:
        from src.omnix.bootstrap.container import get_container
        container = get_container()
        container_health['available'] = True
        
        health = container.health_check()
        container_health['database'] = health.get('database', False)
        container_health['cache'] = health.get('cache', False)
        container_health['settings'] = health.get('settings', False)
        container_health['use_app_layer'] = health.get('use_app_layer', False)
        container_health['database_manager'] = health.get('database_manager', False)
        
        container_health['adapters']['trading'] = health.get('trading_adapter', False)
        container_health['adapters']['risk'] = health.get('risk_adapter', False)
        container_health['adapters']['coherence'] = health.get('coherence_adapter', False)
        
        container_health['adapters']['kraken'] = {
            'available': health.get('kraken_adapter', False),
            'connected': health.get('kraken_connected', False)
        }
        container_health['adapters']['gemini'] = {
            'available': health.get('gemini_adapter', False),
            'provider': health.get('gemini_provider', 'none')
        }
        container_health['adapters']['telegram'] = {
            'available': health.get('telegram_adapter', False),
            'running': health.get('telegram_running', False)
        }
        
    except ImportError as e:
        container_health['error'] = f'Container not available: {str(e)}'
    except Exception as e:
        container_health['error'] = f'Health check failed: {str(e)}'
    
    overall_healthy = (
        container_health['available'] and
        container_health['database'] and
        container_health['settings']
    )
    
    return jsonify({
        'success': True,
        'healthy': overall_healthy,
        'container': container_health,
        'architecture': 'hexagonal',
        'timestamp': datetime.now().isoformat()
    })


@system_bp.route('/api/system/latency')
def api_system_latency():
    """
    API endpoint for real system latency measurement.
    Measures actual response times from database and cache.
    """
    import time
    
    measurements = {}
    
    start = time.perf_counter()
    with get_db_connection() as conn:
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                cursor.fetchone()
                measurements['database_ms'] = round((time.perf_counter() - start) * 1000, 2)
            except Exception:
                measurements['database_ms'] = None
        else:
            measurements['database_ms'] = None
    
    try:
        from omnix_core.cache.redis_cache import get_redis_client
        redis = get_redis_client()
        if redis:
            start = time.perf_counter()
            redis.ping()
            measurements['cache_ms'] = round((time.perf_counter() - start) * 1000, 2)
        else:
            measurements['cache_ms'] = None
    except Exception:
        measurements['cache_ms'] = None
    
    avg_latency = None
    valid_measurements = [v for v in measurements.values() if v is not None]
    if valid_measurements:
        avg_latency = round(sum(valid_measurements) / len(valid_measurements), 2)
    
    return jsonify({
        'success': True,
        'latency': {
            'database_ms': measurements.get('database_ms'),
            'cache_ms': measurements.get('cache_ms'),
            'avg_ms': avg_latency,
            'status': 'optimal' if avg_latency and avg_latency < 10 else 'normal'
        },
        'timestamp': datetime.now().isoformat()
    })


@system_bp.route('/api/system/quarantine')
def api_asset_quarantine():
    """
    API endpoint for excluded/quarantined assets and real-time veto tracking.
    Returns permanently blocked assets + dynamic vetoes from trading decisions.
    Jan 7, 2026: Enhanced with VetoRepository for real-time capital protection tracking.
    """
    try:
        from omnix_core.config.trading_profiles import PAIR_CALIBRATIONS, CalibrationTier
        
        quarantined_assets = []
        total_avoided_loss = 0.0
        
        for symbol, calibration in PAIR_CALIBRATIONS.items():
            if calibration.tier == CalibrationTier.EXCLUDED:
                loss_amount = 0.0
                notes = calibration.notes or ""
                
                if "-$" in notes:
                    try:
                        import re
                        match = re.search(r'-\$?([\d,]+)', notes)
                        if match:
                            loss_amount = float(match.group(1).replace(',', ''))
                    except Exception:
                        pass
                
                quarantined_assets.append({
                    'symbol': symbol,
                    'reason': notes.split(':')[0] if ':' in notes else notes,
                    'loss_avoided': loss_amount,
                    'tier': 'EXCLUDED',
                    'blocked_since': 'Dec 2025'
                })
                total_avoided_loss += loss_amount
        
        symbols_list = [a['symbol'] for a in quarantined_assets]
        veto_stats = {'48h': {}, '7d': {}, 'total': {}}
        
        with get_db_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    
                    if symbols_list:
                        cursor.execute('''
                            SELECT symbol, COUNT(*) as trade_count, SUM(profit_loss) as total_pnl
                            FROM paper_trading_trades
                            WHERE status = 'closed' AND profit_loss < 0
                            AND symbol = ANY(%s)
                            GROUP BY symbol
                        ''', (symbols_list,))
                        
                        db_losses = {row[0]: {'trades': row[1], 'pnl': float(row[2] or 0)} for row in cursor.fetchall()}
                        
                        for asset in quarantined_assets:
                            if asset['symbol'] in db_losses:
                                db_data = db_losses[asset['symbol']]
                                asset['db_trades'] = db_data['trades']
                                asset['db_loss'] = abs(db_data['pnl'])
                                if asset['loss_avoided'] == 0:
                                    asset['loss_avoided'] = abs(db_data['pnl'])
                                    total_avoided_loss += abs(db_data['pnl'])
                    
                    cursor.execute('''
                        SELECT veto_type, COUNT(*) as cnt, COALESCE(SUM(blocked_capital), 0) as capital
                        FROM trading_veto_log
                        WHERE created_at >= NOW() - INTERVAL '48 hours'
                        GROUP BY veto_type
                    ''')
                    veto_stats['48h'] = {row[0]: {'count': row[1], 'blocked': float(row[2])} for row in cursor.fetchall()}
                    
                    cursor.execute('''
                        SELECT veto_type, COUNT(*) as cnt, COALESCE(SUM(blocked_capital), 0) as capital
                        FROM trading_veto_log
                        WHERE created_at >= NOW() - INTERVAL '7 days'
                        GROUP BY veto_type
                    ''')
                    veto_stats['7d'] = {row[0]: {'count': row[1], 'blocked': float(row[2])} for row in cursor.fetchall()}
                    
                    cursor.execute('''
                        SELECT veto_type, COUNT(*) as cnt, COALESCE(SUM(blocked_capital), 0) as capital
                        FROM trading_veto_log
                        GROUP BY veto_type
                    ''')
                    veto_stats['total'] = {row[0]: {'count': row[1], 'blocked': float(row[2])} for row in cursor.fetchall()}
                    
                    cursor.close()
                except Exception as e:
                    logger.warning(f"Could not fetch veto stats: {e}")
        
        veto_48h_total = sum(v['blocked'] for v in veto_stats['48h'].values())
        veto_7d_total = sum(v['blocked'] for v in veto_stats['7d'].values())
        veto_all_total = sum(v['blocked'] for v in veto_stats['total'].values())
        
        return jsonify({
            'success': True,
            'quarantine': {
                'assets': quarantined_assets,
                'total_blocked': len(quarantined_assets),
                'total_loss_avoided': total_avoided_loss,
                'protection_active': True
            },
            'vetoes': {
                '48h': {
                    'by_type': veto_stats['48h'],
                    'total_blocked': veto_48h_total,
                    'total_count': sum(v['count'] for v in veto_stats['48h'].values())
                },
                '7d': {
                    'by_type': veto_stats['7d'],
                    'total_blocked': veto_7d_total,
                    'total_count': sum(v['count'] for v in veto_stats['7d'].values())
                },
                'all_time': {
                    'by_type': veto_stats['total'],
                    'total_blocked': veto_all_total,
                    'total_count': sum(v['count'] for v in veto_stats['total'].values())
                }
            },
            'capital_protected': {
                'permanent': total_avoided_loss,
                'dynamic_48h': veto_48h_total,
                'dynamic_7d': veto_7d_total,
                'grand_total': total_avoided_loss + veto_all_total
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except (ImportError, ValueError, RuntimeError) as e:
        logger.warning(f"Quarantine endpoint: dependency not available ({type(e).__name__})")
        return jsonify({
            'success': False,
            'error': 'Feature unavailable',
            'reason': 'Required service not configured'
        }), 503
    except Exception as e:
        logger.error(f"Error in quarantine endpoint: {type(e).__name__}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@system_bp.route('/api/system/equity')
@require_api_key
def api_system_equity():
    """
    API endpoint for equity curve with BTC benchmark comparison.
    Returns OMNIX performance vs BTC hold strategy with alpha calculation.
    """
    try:
        from omnix_dashboard.utils.queries import get_paper_trades
        
        all_trades = get_paper_trades(days=30)
        trades = [t for t in all_trades if t.get('status') == 'closed']
        
        omnix_curve = []
        btc_curve = []
        cumulative_pnl = 0.0
        initial_balance = 10000.0
        
        if trades:
            sorted_trades = sorted(trades, key=lambda x: x.get('closed_at') or x.get('opened_at', ''))
            
            for trade in sorted_trades:
                pnl = trade.get('pnl', 0) or 0
                cumulative_pnl += pnl
                trade_date = trade.get('closed_at') or trade.get('opened_at')
                
                if trade_date:
                    date_str = trade_date.strftime('%Y-%m-%d') if hasattr(trade_date, 'strftime') else str(trade_date)[:10]
                    pct_return = (cumulative_pnl / initial_balance) * 100
                    
                    omnix_curve.append({
                        'date': date_str,
                        'value': initial_balance + cumulative_pnl,
                        'pnl': cumulative_pnl,
                        'pct_change': round(pct_return, 2)
                    })
        
        btc_start_price = 95000.0
        btc_current_price = 88000.0
        btc_pct_change = ((btc_current_price - btc_start_price) / btc_start_price) * 100
        
        try:
            from omnix_services.market_data.kraken_data import KrakenDataService
            kraken = KrakenDataService()
            btc_price_data = kraken.get_price_data("BTC/USD")
            if btc_price_data and 'price' in btc_price_data:
                btc_current_price = btc_price_data['price']
                btc_pct_change = ((btc_current_price - btc_start_price) / btc_start_price) * 100
        except Exception:
            pass
        
        if omnix_curve:
            for i, point in enumerate(omnix_curve):
                progress = (i + 1) / len(omnix_curve)
                interpolated_btc_pct = btc_pct_change * progress
                btc_curve.append({
                    'date': point['date'],
                    'pct_change': round(interpolated_btc_pct, 2)
                })
        
        omnix_final_pct = omnix_curve[-1]['pct_change'] if omnix_curve else 0
        btc_final_pct = btc_pct_change
        alpha = omnix_final_pct - btc_final_pct
        
        return jsonify({
            'success': True,
            'equity': {
                'omnix': omnix_curve,
                'btc': btc_curve,
                'comparison': {
                    'omnix_return': round(omnix_final_pct, 2),
                    'btc_return': round(btc_final_pct, 2),
                    'alpha': round(alpha, 2),
                    'outperforming': alpha > 0
                },
                'initial_balance': initial_balance,
                'current_balance': initial_balance + cumulative_pnl,
                'total_pnl': round(cumulative_pnl, 2)
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in equity endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@system_bp.route('/api/system/sessions')
@require_api_key
def api_system_sessions():
    """
    API endpoint for live PostgreSQL sessions.
    Shows active user sessions for SaaS scalability demonstration.
    """
    active_sessions = 0
    session_details = []
    
    try:
        from omnix_dashboard.utils.database import get_db_connection
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM user_settings
                WHERE auto_trading = true 
                AND trading_enabled = true 
                AND (is_paused = false OR is_paused IS NULL)
            ''')
            count_row = cursor.fetchone()
            if count_row:
                active_sessions = count_row[0] or 0
            
            cursor.execute('''
                SELECT user_id, updated_at,
                       CASE WHEN is_paused THEN 'paused' ELSE 'active' END as status
                FROM user_settings
                WHERE auto_trading = true 
                AND trading_enabled = true 
                AND (is_paused = false OR is_paused IS NULL)
                ORDER BY updated_at DESC
                LIMIT 10
            ''')
            rows = cursor.fetchall()
            
            for row in rows:
                session_details.append({
                    'user_id': str(row[0])[:8] + '...',
                    'started': str(row[1]) if row[1] else '--',
                    'status': row[2] if len(row) > 2 else 'active'
                })
            
            cursor.close()
                
    except Exception as e:
        logger.warning(f"Sessions query failed: {e}")
        active_sessions = 0
    
    return jsonify({
        'success': True,
        'sessions': {
            'active_count': active_sessions,
            'details': session_details,
            'capacity': '100,000+',
            'database': 'PostgreSQL',
            'architecture': 'Multi-User SaaS Ready'
        },
        'timestamp': datetime.now().isoformat()
    })


@system_bp.route('/api/paper_tracker')
@require_api_key
def api_paper_tracker():
    """
    FASE 4 Tracker API: Consolidated metrics for BTC/USD and XRP/USD paper trades.
    Returns trade count, P/L, win rate, and progress toward 50-100 trade target.
    """
    metrics = consolidated_trade_metrics(days=10, symbols=["BTC/USD", "XRP/USD"])
    
    return jsonify({
        'success': metrics.get('success', False),
        'fase4': {
            'symbols': metrics.get('symbols', []),
            'days_tracked': metrics.get('days_tracked', 10),
            'trade_count': metrics.get('trade_count', 0),
            'win_count': metrics.get('win_count', 0),
            'loss_count': metrics.get('loss_count', 0),
            'gross_pnl': metrics.get('gross_pnl', 0),
            'win_rate': metrics.get('win_rate', 0),
            'avg_win': metrics.get('avg_win', 0),
            'avg_loss': metrics.get('avg_loss', 0),
            'max_drawdown': metrics.get('max_drawdown', 0),
            'target_trades': metrics.get('target_trades', 50),
            'target_win_rate': metrics.get('target_win_rate', 45.0),
            'trade_progress_pct': metrics.get('trade_progress_pct', 0),
            'win_rate_progress_pct': metrics.get('win_rate_progress_pct', 0),
            'on_track': metrics.get('on_track', False)
        },
        'timestamp': datetime.now().isoformat()
    })


@system_bp.route('/api/system/shadow-portfolio')
@require_api_key
def api_shadow_portfolio():
    """
    Shadow Portfolio API: Counterfactual analysis of vetoed trades.
    Returns veto accuracy by type, missed opportunities, and calibration recommendations.
    """
    veto_accuracy = []
    missed_opportunities = []
    calibration_recommendations = []
    summary = {
        'total_analyzed': 0,
        'correct_vetos': 0,
        'incorrect_vetos': 0,
        'accuracy_pct': 0.0,
        'potential_profit_missed': 0.0
    }
    
    try:
        with get_db_connection() as conn:
            if not conn:
                return jsonify({
                    'success': False,
                    'error': 'Database connection unavailable'
                }), 503
            
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    veto_type,
                    COUNT(*) as total,
                    SUM(CASE WHEN veto_was_correct THEN 1 ELSE 0 END) as correct,
                    ROUND(100.0 * SUM(CASE WHEN veto_was_correct THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 1) as accuracy
                FROM shadow_trade_outcomes
                GROUP BY veto_type
                ORDER BY total DESC
            ''')
            
            rows = cursor.fetchall()
            for row in rows:
                veto_accuracy.append({
                    'veto_type': row[0],
                    'total': row[1],
                    'correct': row[2],
                    'accuracy_pct': float(row[3]) if row[3] else 0.0
                })
                summary['total_analyzed'] += row[1]
                summary['correct_vetos'] += row[2]
            
            summary['incorrect_vetos'] = summary['total_analyzed'] - summary['correct_vetos']
            if summary['total_analyzed'] > 0:
                summary['accuracy_pct'] = round(100.0 * summary['correct_vetos'] / summary['total_analyzed'], 1)
            
            cursor.execute('''
                SELECT 
                    e.symbol,
                    e.intended_action,
                    e.entry_price,
                    o.counterfactual_pnl_24h,
                    o.max_favorable_pct,
                    o.verdict_reason,
                    e.veto_type,
                    o.analyzed_at
                FROM shadow_trade_outcomes o
                JOIN shadow_trade_events e ON o.event_id = e.id
                WHERE o.veto_was_correct = false
                AND o.counterfactual_pnl_24h > 1.5
                ORDER BY o.counterfactual_pnl_24h DESC
                LIMIT 10
            ''')
            
            missed_rows = cursor.fetchall()
            for row in missed_rows:
                missed_opportunities.append({
                    'symbol': row[0],
                    'action': row[1],
                    'entry_price': float(row[2]) if row[2] else 0,
                    'would_have_gained_pct': float(row[3]) if row[3] else 0,
                    'max_favorable_pct': float(row[4]) if row[4] else 0,
                    'reason': row[5],
                    'blocked_by': row[6],
                    'analyzed_at': row[7].isoformat() if row[7] else None
                })
                if row[3]:
                    summary['potential_profit_missed'] += float(row[3])
            
            cursor.execute('''
                SELECT 
                    filter_name,
                    current_threshold,
                    recommended_threshold,
                    recommended_action,
                    trades_analyzed,
                    accuracy_pct,
                    would_have_won_pct,
                    updated_at
                FROM filter_calibration_metrics
                ORDER BY updated_at DESC
                LIMIT 10
            ''')
            
            cal_rows = cursor.fetchall()
            for row in cal_rows:
                calibration_recommendations.append({
                    'filter': row[0],
                    'current': float(row[1]) if row[1] else None,
                    'recommended': float(row[2]) if row[2] else None,
                    'action': row[3],
                    'trades_analyzed': row[4],
                    'accuracy_pct': float(row[5]) if row[5] else 0,
                    'would_have_won_pct': float(row[6]) if row[6] else 0,
                    'updated_at': row[7].isoformat() if row[7] else None
                })
            
            cursor.close()
    
    except Exception as e:
        logger.error(f"Shadow portfolio query failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'note': 'Tables may not exist yet - run migration V007',
            'shadow_portfolio': None,
            'timestamp': datetime.now().isoformat()
        })
    
    return jsonify({
        'success': True,
        'shadow_portfolio': {
            'summary': summary,
            'veto_accuracy': veto_accuracy,
            'missed_opportunities': missed_opportunities,
            'calibration_recommendations': calibration_recommendations
        },
        'timestamp': datetime.now().isoformat()
    })


@system_bp.route('/api/governance/avm-status')
@require_api_key
def api_avm_status():
    """
    AVM Governance Status — live baseline integrity + drift per domain.

    Returns per-domain:
    - integrity_status: OK | TAMPERED | LEGACY_NO_HASH
    - baseline_hash (first 12 chars)
    - drift_status: STABLE | DRIFTING | STALE
    - is_valid
    - last_calibrated
    - version + is_active (if versioning enabled)
    - decisions_blocked (from DB if available)
    """
    try:
        from omnix_core.governance.avm_db_bridge import AVMDatabaseBridge
        from omnix_core.governance.assumption_validity_monitor import AssumptionValidityMonitor

        bridge = AVMDatabaseBridge()
        avm = AssumptionValidityMonitor()

        snapshots = bridge.load_all_snapshots() if bridge.is_available() else {}

        DOMAIN_ORDER = ["trading", "islamic_credit", "insurance", "robotics"]
        DOMAIN_LABELS = {
            "trading":        "Trading",
            "islamic_credit": "Islamic Credit",
            "insurance":      "Insurance",
            "robotics":       "Robotics",
        }

        domains = []
        decisions_blocked_total = 0

        with get_db_connection() as conn:
            blocked_by_domain = {}
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT domain, COUNT(*) as blocked
                        FROM avm_baseline_change_log
                        WHERE action = 'STALE_BLOCK'
                          AND logged_at > NOW() - INTERVAL '24 hours'
                        GROUP BY domain
                    """)
                    for row in cursor.fetchall():
                        blocked_by_domain[row[0]] = row[1]
                    cursor.close()
                except Exception:
                    pass

        for domain in DOMAIN_ORDER:
            snap_db = snapshots.get(domain, {})
            snap_local = avm.load_snapshot(domain)

            integrity = snap_db.get("integrity_status", "NO_SNAPSHOT")
            raw_hash = snap_db.get("baseline_hash", "")
            short_hash = raw_hash[:12] + "..." if raw_hash else "—"

            drift_score = None
            drift_status = "UNKNOWN"
            is_valid = False

            if snap_local:
                try:
                    age_h = snap_local.age_hours()
                    if integrity == "TAMPERED":
                        drift_status = "STALE"
                        is_valid = False
                    elif age_h > snap_local.max_age_hours:
                        drift_status = "STALE"
                        drift_score = 100.0
                        is_valid = False
                    else:
                        drift_status = "STABLE"
                        # drift_threshold is on 0-100 scale; show age as % of threshold
                        pct = (age_h / max(snap_local.max_age_hours, 1)) * snap_local.drift_threshold
                        drift_score = round(pct, 1)
                        is_valid = True
                except Exception as _exc:
                    logger.debug(f"AVM drift calc error for {domain}: {_exc}")
                    drift_status = "UNKNOWN"

            version = snap_db.get("version", 1)
            is_active = snap_db.get("is_active", True)
            calibrated_at = snap_db.get("calibrated_at", "—")
            if calibrated_at and calibrated_at != "—":
                try:
                    dt = datetime.fromisoformat(calibrated_at.replace("Z", "+00:00"))
                    calibrated_at = dt.strftime("%Y-%m-%d %H:%M UTC")
                except Exception:
                    pass

            blocked_24h = blocked_by_domain.get(domain, 0)
            decisions_blocked_total += blocked_24h

            domains.append({
                "domain":          domain,
                "label":           DOMAIN_LABELS[domain],
                "integrity":       integrity,
                "hash":            short_hash,
                "drift_score":     drift_score,
                "drift_status":    drift_status,
                "is_valid":        is_valid,
                "is_active":       is_active,
                "version":         version,
                "calibrated_at":   calibrated_at,
                "blocked_24h":     blocked_24h,
            })

        db_available = bridge.is_available()
        degraded = not db_available or any(
            d["integrity"] == "TAMPERED" for d in domains
        )

        # Fail-closed mode status
        import os as _os
        fail_closed = _os.environ.get("AVM_FAIL_CLOSED", "false").lower() == "true"

        # Last blocked decision — pull from credit_applications or shadow_trade_events
        last_decision = None
        with get_db_connection() as conn:
            if conn:
                try:
                    cursor = conn.cursor()
                    # Try credit applications first (most recent blocked)
                    cursor.execute("""
                        SELECT application_id, decision, sector, applicant_type,
                               requested_amount, submitted_at,
                               block_reason, blocked_at_checkpoint
                        FROM credit_applications
                        WHERE decision = 'BLOCKED'
                        ORDER BY submitted_at DESC
                        LIMIT 1
                    """)
                    row = cursor.fetchone()
                    if row:
                        amount_fmt = f"AED {row[4]:,.0f}" if row[4] else "—"
                        ts = row[5].strftime("%H:%M UTC") if row[5] else "—"
                        reason = row[6] or (f"Failed at checkpoint {row[7]}" if row[7] else "Governance threshold exceeded")
                        last_decision = {
                            "domain":  "Islamic Credit",
                            "input":   f"{(row[2] or '').replace('_', ' ').title()} · {row[3] or '—'}",
                            "result":  "BLOCKED",
                            "reason":  reason[:60] if reason else "Governance threshold exceeded",
                            "amount":  amount_fmt,
                            "ref":     (row[0] or "")[:20] or "—",
                            "time":    ts,
                        }
                    else:
                        # Fall back to shadow_trade_events
                        cursor.execute("""
                            SELECT symbol, veto_type, blocked_capital, created_at
                            FROM shadow_trade_events
                            WHERE veto_type IS NOT NULL
                            ORDER BY created_at DESC
                            LIMIT 1
                        """)
                        row = cursor.fetchone()
                        if row:
                            cap = f"${row[2]:,.0f}" if row[2] else "—"
                            ts = row[3].strftime("%H:%M UTC") if row[3] else "—"
                            last_decision = {
                                "domain":  "Trading",
                                "input":   row[0] or "—",
                                "result":  "BLOCKED",
                                "reason":  (row[1] or "VETO").replace("_", " "),
                                "amount":  cap,
                                "ref":     "SHADOW",
                                "time":    ts,
                            }
                    cursor.close()
                except Exception:
                    pass

        return jsonify({
            "success":                  True,
            "db_available":             db_available,
            "degraded_mode":            degraded,
            "fail_closed":              fail_closed,
            "domains":                  domains,
            "decisions_blocked_total":  decisions_blocked_total,
            "last_decision":            last_decision,
            "timestamp":                datetime.now().isoformat(),
        })

    except Exception as e:
        logger.error(f"AVM status error: {e}")
        return jsonify({
            "success":       False,
            "error":         str(e),
            "domains":       [],
            "degraded_mode": True,
            "timestamp":     datetime.now().isoformat(),
        })


# ── Layer 0 Metrics — executive / investor view (ADR-092) ─────────────────────

try:
    from omnix_core.governance.structural_admissibility_engine import (
        get_layer0_metrics          as _get_layer0_metrics,
        get_layer0_snapshot_history  as _get_layer0_snapshot_history,
        get_sae_override             as _get_sae_override,
        _LAYER0_DEMO_TAGLINE,
        _snapshot_interval_minutes   as _SNAPSHOT_INTERVAL_MIN,
        _SNAPSHOT_MAX_ENTRIES,
    )
    _SAE_METRICS_AVAILABLE = True
except ImportError:
    _SAE_METRICS_AVAILABLE = False
    _LAYER0_DEMO_TAGLINE   = ""
    _SNAPSHOT_INTERVAL_MIN = 5
    _SNAPSHOT_MAX_ENTRIES  = 288
    def _get_layer0_metrics():
        class _Stub:
            def snapshot(self): return {}
        return _Stub()
    def _get_layer0_snapshot_history(last_n=None): return []
    def _get_sae_override():
        return None


@system_bp.route('/api/system/layer0-metrics')
@require_api_key
def api_layer0_metrics():
    """
    GET /api/system/layer0-metrics
    Real-time Layer 0 (Structural Admissibility Engine) admission metrics.
    Executive / investor observability view.  ADR-092.

    Returns:
      global  — total/admitted/blocked/block_rate_pct + top_constraint_classes
      domains — per-domain breakdown sorted by blocked count (descending)
    """
    try:
        snapshot = _get_layer0_metrics().snapshot()
        override  = _get_sae_override()

        domains = []
        global_total    = 0
        global_admitted = 0
        global_blocked  = 0
        global_by_class: dict = {}

        for domain, stat in snapshot.items():
            domains.append({
                "domain":           domain,
                "total":            stat["total"],
                "admitted":         stat["admitted"],
                "blocked":          stat["blocked"],
                "block_rate_pct":   round(stat["block_rate_pct"], 2),
                "blocked_by_class": stat["blocked_by_class"],
            })
            global_total    += stat["total"]
            global_admitted += stat["admitted"]
            global_blocked  += stat["blocked"]
            for cls, cnt in stat["blocked_by_class"].items():
                global_by_class[cls] = global_by_class.get(cls, 0) + cnt

        domains.sort(key=lambda d: d["blocked"], reverse=True)

        top_constraint_classes = sorted(
            [{"class": k, "count": v} for k, v in global_by_class.items()],
            key=lambda x: x["count"],
            reverse=True,
        )

        global_block_rate = round(
            (global_blocked / global_total * 100) if global_total else 0.0,
            2,
        )

        snapshot_history = _get_layer0_snapshot_history(last_n=12)

        return jsonify({
            "success":              True,
            "sae_module_available": _SAE_METRICS_AVAILABLE,
            "operator_override":    (override.value if override is not None else "UNSET"),
            "demo_tagline":         _LAYER0_DEMO_TAGLINE,
            "global": {
                "total":                  global_total,
                "admitted":               global_admitted,
                "blocked":                global_blocked,
                "block_rate_pct":         global_block_rate,
                "top_constraint_classes": top_constraint_classes,
            },
            "domains":          domains,
            "snapshot_history": snapshot_history,
            "snapshot_config": {
                "interval_minutes": _SNAPSHOT_INTERVAL_MIN,
                "max_entries":      _SNAPSHOT_MAX_ENTRIES,
                "stored":           len(snapshot_history),
            },
            "timestamp": datetime.now().isoformat(),
            "note": (
                "Metrics accumulate from process start (in-memory, thread-safe). "
                "Snapshots every 5 min — ready for charts and pitch decks. "
                "ADR-092."
            ),
        })

    except Exception as exc:
        logger.exception("api_layer0_metrics error: %s", exc)
        return jsonify({
            "success":   False,
            "error":     str(exc),
            "timestamp": datetime.now().isoformat(),
        }), 500
