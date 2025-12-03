"""
OMNIX Dashboard V6.5.2 - Audited Snapshots Blueprint
Provides cryptographically verified snapshots for investor auditing
"""

import hashlib
import json
from datetime import datetime, date
from typing import Optional
from flask import Blueprint, jsonify, request

from omnix_dashboard.utils.database import get_db_connection, is_db_available

snapshots_bp = Blueprint('snapshots', __name__)


def normalize_data(data) -> dict:
    """Normalize data_json from database - handles both string and dict formats"""
    if isinstance(data, str):
        return json.loads(data)
    return data


def calculate_checksum(data) -> str:
    """Calculate SHA-256 checksum for data integrity verification"""
    normalized = normalize_data(data)
    json_str = json.dumps(normalized, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode()).hexdigest()


def get_latest_checksum() -> Optional[str]:
    """Get the checksum of the most recent snapshot for chain verification"""
    if not is_db_available():
        return None
    
    with get_db_connection() as conn:
        if not conn:
            return None
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT checksum_sha256 FROM audited_snapshots 
                    ORDER BY created_at DESC LIMIT 1
                """)
                row = cur.fetchone()
                return row[0] if row else None
        except Exception:
            return None


@snapshots_bp.route('/api/snapshots')
def list_snapshots():
    """List all audited snapshots with verification status"""
    if not is_db_available():
        return jsonify({
            'success': False,
            'error': 'Database not available',
            'snapshots': []
        })
    
    with get_db_connection() as conn:
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed',
                'snapshots': []
            })
        
        try:
            limit = min(int(request.args.get('limit', 30)), 100)
            
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, snapshot_type, snapshot_date, total_equity, total_pnl,
                           open_positions_count, closed_trades_count, win_rate,
                           sharpe_ratio, max_drawdown, checksum_sha256, previous_checksum,
                           created_at, verified_at, verification_status
                    FROM audited_snapshots
                    ORDER BY snapshot_date DESC, created_at DESC
                    LIMIT %s
                """, (limit,))
                
                rows = cur.fetchall()
                snapshots = []
                
                for row in rows:
                    snapshots.append({
                        'id': row[0],
                        'type': row[1],
                        'date': row[2].isoformat() if row[2] else None,
                        'total_equity': float(row[3]) if row[3] else 0,
                        'total_pnl': float(row[4]) if row[4] else 0,
                        'open_positions': row[5] or 0,
                        'closed_trades': row[6] or 0,
                        'win_rate': float(row[7]) if row[7] else 0,
                        'sharpe_ratio': float(row[8]) if row[8] else 0,
                        'max_drawdown': float(row[9]) if row[9] else 0,
                        'checksum': row[10][:16] + '...' if row[10] else None,
                        'has_chain': row[11] is not None,
                        'created_at': row[12].isoformat() if row[12] else None,
                        'verified_at': row[13].isoformat() if row[13] else None,
                        'status': row[14] or 'pending'
                    })
                
                return jsonify({
                    'success': True,
                    'snapshots': snapshots,
                    'count': len(snapshots),
                    'db_connected': True
                })
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'snapshots': []
            })


@snapshots_bp.route('/api/snapshots/create', methods=['POST'])
def create_snapshot():
    """Create a new audited snapshot with cryptographic verification"""
    if not is_db_available():
        return jsonify({
            'success': False,
            'error': 'Database not available'
        })
    
    with get_db_connection() as conn:
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            })
        
        try:
            data = request.get_json() or {}
            snapshot_type = data.get('type', 'daily')
            snapshot_date = data.get('date', date.today().isoformat())
            
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as wins,
                           SUM(profit_loss) as total_pnl
                    FROM paper_trading_trades
                    WHERE DATE(closed_at) <= %s AND closed_at IS NOT NULL
                """, (snapshot_date,))
                
                trade_stats = cur.fetchone()
                total_trades = trade_stats[0] or 0
                wins = trade_stats[1] or 0
                total_pnl = float(trade_stats[2]) if trade_stats[2] else 0
                
                cur.execute("""
                    SELECT COUNT(*) FROM paper_trading_trades
                    WHERE closed_at IS NULL
                """)
                open_positions = cur.fetchone()[0] or 0
                
                cur.execute("""
                    SELECT balance_usd, sharpe_ratio, max_drawdown_pct, 
                           total_trades, winning_trades, total_realized_pnl_usd
                    FROM paper_trading_balances
                    ORDER BY updated_at DESC LIMIT 1
                """)
                balance_row = cur.fetchone()
                if balance_row:
                    total_equity = float(balance_row[0]) if balance_row[0] else 10000.0
                    sharpe_ratio = float(balance_row[1]) if balance_row[1] else 0
                    max_drawdown = float(balance_row[2]) if balance_row[2] else 0
                    db_total_trades = balance_row[3] or 0
                    db_wins = balance_row[4] or 0
                    realized_pnl = float(balance_row[5]) if balance_row[5] else 0
                    if db_total_trades > 0:
                        total_trades = db_total_trades
                        wins = db_wins
                        total_pnl = realized_pnl
                else:
                    total_equity = 10000.0
                    sharpe_ratio = 0
                    max_drawdown = 0
                
                win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
                
                snapshot_data = {
                    'snapshot_type': snapshot_type,
                    'snapshot_date': snapshot_date,
                    'total_equity': total_equity,
                    'total_pnl': total_pnl,
                    'open_positions_count': open_positions,
                    'closed_trades_count': total_trades,
                    'win_rate': win_rate,
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_drawdown,
                    'generated_at': datetime.now().isoformat()
                }
                
                checksum = calculate_checksum(snapshot_data)
                previous_checksum = get_latest_checksum()
                
                cur.execute("""
                    INSERT INTO audited_snapshots (
                        snapshot_type, snapshot_date, total_equity, total_pnl,
                        open_positions_count, closed_trades_count, win_rate,
                        sharpe_ratio, max_drawdown, data_json, checksum_sha256,
                        previous_checksum, verification_status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                    ON CONFLICT (snapshot_type, snapshot_date) 
                    DO UPDATE SET
                        total_equity = EXCLUDED.total_equity,
                        total_pnl = EXCLUDED.total_pnl,
                        open_positions_count = EXCLUDED.open_positions_count,
                        closed_trades_count = EXCLUDED.closed_trades_count,
                        win_rate = EXCLUDED.win_rate,
                        data_json = EXCLUDED.data_json,
                        checksum_sha256 = EXCLUDED.checksum_sha256,
                        previous_checksum = EXCLUDED.previous_checksum,
                        created_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (
                    snapshot_type, snapshot_date, total_equity, total_pnl,
                    open_positions, total_trades, win_rate,
                    sharpe_ratio, max_drawdown, json.dumps(snapshot_data), checksum, previous_checksum
                ))
                
                snapshot_id = cur.fetchone()[0]
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'snapshot_id': snapshot_id,
                    'checksum': checksum,
                    'chained': previous_checksum is not None,
                    'message': f'Snapshot created for {snapshot_date}'
                })
                
        except Exception as e:
            conn.rollback()
            return jsonify({
                'success': False,
                'error': str(e)
            })


@snapshots_bp.route('/api/snapshots/<int:snapshot_id>/verify')
def verify_snapshot(snapshot_id):
    """Verify the integrity of a specific snapshot"""
    if not is_db_available():
        return jsonify({
            'success': False,
            'error': 'Database not available'
        })
    
    with get_db_connection() as conn:
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            })
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, data_json, checksum_sha256, previous_checksum,
                           verification_status
                    FROM audited_snapshots WHERE id = %s
                """, (snapshot_id,))
                
                row = cur.fetchone()
                if not row:
                    return jsonify({
                        'success': False,
                        'error': 'Snapshot not found'
                    })
                
                stored_data = row[1]
                stored_checksum = row[2]
                previous_checksum = row[3]
                
                calculated_checksum = calculate_checksum(stored_data)
                checksum_valid = calculated_checksum == stored_checksum
                
                chain_valid = True
                if previous_checksum:
                    cur.execute("""
                        SELECT checksum_sha256 FROM audited_snapshots
                        WHERE checksum_sha256 = %s
                    """, (previous_checksum,))
                    chain_valid = cur.fetchone() is not None
                
                new_status = 'verified' if (checksum_valid and chain_valid) else 'failed'
                
                cur.execute("""
                    UPDATE audited_snapshots 
                    SET verified_at = CURRENT_TIMESTAMP,
                        verification_status = %s
                    WHERE id = %s
                """, (new_status, snapshot_id))
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'snapshot_id': snapshot_id,
                    'checksum_valid': checksum_valid,
                    'chain_valid': chain_valid,
                    'verification_status': new_status,
                    'stored_checksum': stored_checksum[:16] + '...',
                    'calculated_checksum': calculated_checksum[:16] + '...',
                    'verified_at': datetime.now().isoformat()
                })
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })


@snapshots_bp.route('/api/snapshots/chain/verify')
def verify_chain():
    """Verify the entire chain of snapshots with full integrity checks"""
    if not is_db_available():
        return jsonify({
            'success': False,
            'error': 'Database not available'
        })
    
    with get_db_connection() as conn:
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            })
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, checksum_sha256, previous_checksum, data_json
                    FROM audited_snapshots
                    ORDER BY created_at ASC
                """)
                
                rows = cur.fetchall()
                if not rows:
                    return jsonify({
                        'success': True,
                        'chain_valid': True,
                        'total_snapshots': 0,
                        'verified_count': 0,
                        'message': 'No snapshots to verify'
                    })
                
                checksums = {row[1]: row[0] for row in rows}
                verified_count = 0
                broken_links = []
                verified_ids = []
                failed_ids = []
                
                for row in rows:
                    snapshot_id, stored_checksum, prev_checksum, data = row
                    is_valid = True
                    issue = None
                    
                    calc_checksum = calculate_checksum(data)
                    if calc_checksum != stored_checksum:
                        is_valid = False
                        issue = 'checksum_mismatch'
                        broken_links.append({
                            'id': snapshot_id,
                            'issue': issue,
                            'stored': stored_checksum[:16] + '...',
                            'calculated': calc_checksum[:16] + '...'
                        })
                    elif prev_checksum and prev_checksum not in checksums:
                        is_valid = False
                        issue = 'broken_chain'
                        broken_links.append({
                            'id': snapshot_id,
                            'issue': issue,
                            'missing_checksum': prev_checksum[:16] + '...'
                        })
                    
                    if is_valid:
                        verified_count += 1
                        verified_ids.append(snapshot_id)
                    else:
                        failed_ids.append(snapshot_id)
                
                if verified_ids:
                    cur.execute("""
                        UPDATE audited_snapshots 
                        SET verified_at = CURRENT_TIMESTAMP,
                            verification_status = 'verified'
                        WHERE id = ANY(%s)
                    """, (verified_ids,))
                
                if failed_ids:
                    cur.execute("""
                        UPDATE audited_snapshots 
                        SET verified_at = CURRENT_TIMESTAMP,
                            verification_status = 'failed'
                        WHERE id = ANY(%s)
                    """, (failed_ids,))
                
                conn.commit()
                
                chain_valid = len(broken_links) == 0
                
                return jsonify({
                    'success': True,
                    'chain_valid': chain_valid,
                    'total_snapshots': len(rows),
                    'verified_count': verified_count,
                    'failed_count': len(failed_ids),
                    'broken_links': broken_links if not chain_valid else [],
                    'verified_at': datetime.now().isoformat()
                })
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })


@snapshots_bp.route('/api/snapshots/<int:snapshot_id>/audit')
def get_snapshot_audit(snapshot_id):
    """Get full audit details for a snapshot including complete checksums for external verification"""
    if not is_db_available():
        return jsonify({
            'success': False,
            'error': 'Database not available'
        })
    
    with get_db_connection() as conn:
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            })
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, snapshot_type, snapshot_date, total_equity, total_pnl,
                           open_positions_count, closed_trades_count, win_rate,
                           sharpe_ratio, max_drawdown, checksum_sha256, previous_checksum,
                           data_json, created_at, verified_at, verification_status
                    FROM audited_snapshots WHERE id = %s
                """, (snapshot_id,))
                
                row = cur.fetchone()
                if not row:
                    return jsonify({
                        'success': False,
                        'error': 'Snapshot not found'
                    })
                
                recalculated = calculate_checksum(row[12])
                integrity_valid = recalculated == row[10]
                
                return jsonify({
                    'success': True,
                    'audit': {
                        'id': row[0],
                        'type': row[1],
                        'date': row[2].isoformat() if row[2] else None,
                        'metrics': {
                            'total_equity': float(row[3]) if row[3] else 0,
                            'total_pnl': float(row[4]) if row[4] else 0,
                            'open_positions': row[5] or 0,
                            'closed_trades': row[6] or 0,
                            'win_rate': float(row[7]) if row[7] else 0,
                            'sharpe_ratio': float(row[8]) if row[8] else 0,
                            'max_drawdown': float(row[9]) if row[9] else 0
                        },
                        'cryptography': {
                            'stored_checksum': row[10],
                            'recalculated_checksum': recalculated,
                            'previous_checksum': row[11],
                            'integrity_valid': integrity_valid,
                            'algorithm': 'SHA-256'
                        },
                        'raw_data': row[12],
                        'timestamps': {
                            'created_at': row[13].isoformat() if row[13] else None,
                            'verified_at': row[14].isoformat() if row[14] else None
                        },
                        'verification_status': row[15] or 'pending'
                    }
                })
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })


@snapshots_bp.route('/api/snapshots/latest')
def get_latest_snapshot():
    """Get the most recent snapshot with full details"""
    if not is_db_available():
        return jsonify({
            'success': False,
            'error': 'Database not available'
        })
    
    with get_db_connection() as conn:
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database connection failed'
            })
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, snapshot_type, snapshot_date, total_equity, total_pnl,
                           open_positions_count, closed_trades_count, win_rate,
                           sharpe_ratio, max_drawdown, checksum_sha256, data_json,
                           created_at, verified_at, verification_status
                    FROM audited_snapshots
                    ORDER BY snapshot_date DESC, created_at DESC
                    LIMIT 1
                """)
                
                row = cur.fetchone()
                if not row:
                    return jsonify({
                        'success': True,
                        'snapshot': None,
                        'message': 'No snapshots available'
                    })
                
                return jsonify({
                    'success': True,
                    'snapshot': {
                        'id': row[0],
                        'type': row[1],
                        'date': row[2].isoformat() if row[2] else None,
                        'total_equity': float(row[3]) if row[3] else 0,
                        'total_pnl': float(row[4]) if row[4] else 0,
                        'open_positions': row[5] or 0,
                        'closed_trades': row[6] or 0,
                        'win_rate': float(row[7]) if row[7] else 0,
                        'sharpe_ratio': float(row[8]) if row[8] else 0,
                        'max_drawdown': float(row[9]) if row[9] else 0,
                        'checksum': row[10],
                        'data': row[11],
                        'created_at': row[12].isoformat() if row[12] else None,
                        'verified_at': row[13].isoformat() if row[13] else None,
                        'status': row[14] or 'pending'
                    }
                })
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })
