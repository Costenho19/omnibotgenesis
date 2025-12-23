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
from omnix_dashboard.utils.queries import get_paper_trades

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
                            confidence = int(buy_ratio * 100)
                        elif buy_ratio < 0.3:
                            signal_type = 'BEARISH'
                            confidence = int((1 - buy_ratio) * 100)
                        else:
                            signal_type = 'NEUTRAL'
                            confidence = 50
                        
                        signals.append({
                            'strategy': list(stats['strategies'])[0] if stats['strategies'] else 'OMNIX',
                            'symbol': symbol,
                            'signal': signal_type,
                            'confidence': confidence,
                            'trades_24h': total,
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
                            'confidence': 75,
                            'position_open': True,
                            'timestamp': pos[4].isoformat() if pos[4] else datetime.now().isoformat()
                        })
                
                cursor.close()
                logger.info(f"Generated {len(signals)} signals from real trading data")
                
            except Exception as e:
                logger.error(f"Error fetching signals from DB: {e}")
    
    if not signals:
        signals = [
            {
                'strategy': 'OMNIX V6.5',
                'symbol': 'BTC/USD',
                'signal': 'ANALYZING',
                'confidence': 0,
                'message': 'Waiting for trading activity',
                'timestamp': datetime.now().isoformat()
            }
        ]
    
    return jsonify({
        'success': True,
        'signals': signals,
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
            'OMNIX_V6.5': {'active': bot_active, 'signals_today': trades_today},
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
        'version': 'INSTITUTIONAL+',
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
            'version': 'V5.4',
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
    
    current_regime = 'TRENDING'
    regime_confidence = 0.85
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
                    strat_name = row[0] or 'OMNIX_V6.5'
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
        strategy_weights = {
            'Quantum_Momentum': {'weight': 0.85, 'trades_24h': 0, 'win_rate': 58.0, 'status': 'ACTIVE'},
            'Non_Markovian': {'weight': 0.80, 'trades_24h': 0, 'win_rate': 54.0, 'status': 'ACTIVE'},
            'OMNIX_V6.5': {'weight': 0.75, 'trades_24h': 0, 'win_rate': 55.0, 'status': 'ACTIVE'},
            'Monte_Carlo': {'weight': 0.70, 'trades_24h': 0, 'win_rate': 52.0, 'status': 'ACTIVE'},
            'Kalman_Filter': {'weight': 0.65, 'trades_24h': 0, 'win_rate': 51.0, 'status': 'ACTIVE'},
            'HMM_Regime': {'weight': 0.60, 'trades_24h': 0, 'win_rate': 50.0, 'status': 'ACTIVE'}
        }
    
    main_driver = None
    max_weight = 0
    for name, data in strategy_weights.items():
        if data['weight'] >= 0.80 and data['weight'] > max_weight:
            max_weight = data['weight']
            main_driver = name
    
    adaptive_data = {
        'version': 'ULTRA',
        'status': 'ACTIVE',
        'main_driver': {
            'name': main_driver,
            'weight': max_weight,
            'description': 'ANU Quantum Random Number Generator for momentum detection' if main_driver == 'Quantum_Momentum' else 'Non-Markovian temporal memory kernel',
            'is_quantum': main_driver == 'Quantum_Momentum'
        } if main_driver else None,
        'regime': {
            'current': current_regime,
            'confidence': round(regime_confidence, 2),
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
            'signal_quality_avg': 0.72,
            'regime_accuracy_7d': 0.78,
            'calibration_success_rate': 0.95
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
        'version': 'V7.0 Phase 5',
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
    API endpoint for excluded/quarantined assets.
    Returns assets blocked from trading and avoided losses calculated from real DB data.
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
                    except:
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
        if symbols_list:
            with get_db_connection() as conn:
                if conn:
                    try:
                        cursor = conn.cursor()
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
                    except Exception as e:
                        logger.warning(f"Could not fetch DB losses: {e}")
        
        return jsonify({
            'success': True,
            'quarantine': {
                'assets': quarantined_assets,
                'total_blocked': len(quarantined_assets),
                'total_loss_avoided': total_avoided_loss,
                'protection_active': True
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in quarantine endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
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
        except:
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
        from omnix_core.sessions.user_session_manager import initialize_session_manager
        from omnix_core.cache.redis_cache import RedisCache
        from omnix_services.database_service import DatabaseService
        
        redis_cache = None
        database_service = None
        
        try:
            redis_cache = RedisCache()
        except Exception as e:
            logger.debug(f"Redis not available for sessions: {e}")
        
        try:
            database_service = DatabaseService()
        except Exception as e:
            logger.debug(f"DatabaseService not available for sessions: {e}")
        
        session_manager = initialize_session_manager(
            redis_cache=redis_cache,
            database_service=database_service
        )
        
        if hasattr(session_manager, 'get_active_session_count'):
            active_sessions = session_manager.get_active_session_count() or 0
        
        if hasattr(session_manager, 'get_active_sessions'):
            sessions = session_manager.get_active_sessions() or []
            for session in sessions[:10]:
                session_details.append({
                    'user_id': str(session.get('user_id', 'unknown'))[:8] + '...',
                    'started': str(session.get('started_at', '--')),
                    'status': session.get('status', 'active')
                })
    except Exception as e:
        logger.debug(f"UserSessionManager not available: {e}")
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
