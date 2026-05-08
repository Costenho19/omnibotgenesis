import json
import logging
import os
import time
from collections import defaultdict
from flask import Blueprint, jsonify, request
from omnix_dashboard.utils.database import get_db_connection

logger = logging.getLogger(__name__)

verification_bp = Blueprint('verification', __name__)

VERIFIER_AVAILABLE = False
DecisionReceiptEngine = None
ReceiptVerifier = None

def _init_verifier():
    global VERIFIER_AVAILABLE, DecisionReceiptEngine, ReceiptVerifier
    if VERIFIER_AVAILABLE:
        return
    try:
        import importlib.util
        import sys
        spec = importlib.util.spec_from_file_location(
            "decision_receipt",
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                        "omnix_core", "evidence", "decision_receipt.py")
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules['_omnix_receipt'] = mod
        spec.loader.exec_module(mod)
        ReceiptVerifier = mod.ReceiptVerifier
        DecisionReceiptEngine = mod.DecisionReceiptEngine
        VERIFIER_AVAILABLE = True
    except Exception as e:
        logger.warning(f"Receipt verifier not available: {e}")

_rate_limit_store = defaultdict(list)
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 30


def _check_rate_limit(ip: str) -> bool:
    now = time.time()
    _rate_limit_store[ip] = [t for t in _rate_limit_store[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limit_store[ip]) >= RATE_LIMIT_MAX:
        return False
    _rate_limit_store[ip].append(now)
    return True


def _get_receipt_from_db(receipt_id: str) -> dict:
    try:
        with get_db_connection() as conn:
            if not conn:
                return None
            cur = conn.cursor()
            cur.execute("""
                SELECT receipt_id, timestamp_utc, asset, decision, veto_chain,
                       policy_version, engine_version, prev_hash, content_hash,
                       signature, signature_algorithm, public_key, created_at
                FROM decision_receipts
                WHERE receipt_id = %s
            """, (receipt_id,))
            row = cur.fetchone()
            cur.close()
            if not row:
                return None
            veto_chain = row[4]
            if isinstance(veto_chain, str):
                try:
                    veto_chain = json.loads(veto_chain)
                except json.JSONDecodeError:
                    veto_chain = []
            return {
                'receipt_id': row[0],
                'timestamp': row[1],
                'asset': row[2],
                'decision': row[3],
                'veto_chain': veto_chain,
                'policy_version': row[5],
                'engine_version': row[6],
                'prev_hash': row[7],
                'content_hash': row[8],
                'signature': row[9],
                'signature_algorithm': row[10],
                'public_key': row[11],
                'stored_at': row[12].isoformat() if row[12] else None
            }
    except Exception as e:
        logger.error(f"Error fetching receipt: {e}")
        return None


@verification_bp.route('/verify')
@verification_bp.route('/verify/<path:receipt_id>')
@verification_bp.route('/crisis-replay')
def verify_page(receipt_id=None):
    import os as _os
    from flask import send_from_directory as _sfd
    react_dist = _os.path.normpath(_os.path.join(_os.path.dirname(__file__), '..', '..', 'omnix_web', 'dist'))
    return _sfd(react_dist, 'index.html')


@verification_bp.route('/api/public_key')
def public_key():
    _init_verifier()
    if DecisionReceiptEngine:
        engine = DecisionReceiptEngine()
        pk = engine.public_key_b64
        if pk:
            return jsonify({
                'public_key': pk,
                'algorithm': 'Dilithium-3 (ML-DSA-65)',
                'standard': 'NIST-standardized post-quantum digital signature',
                'key_size': '1952 bytes',
                'security_level': 'Strong quantum resistance — NIST-standardized post-quantum algorithm',
                'note': 'This key is generated per engine instance. Production keys are versioned and persistent.'
            })
    return jsonify({
        'error': 'Public key not available',
        'reason': 'PQC engine not initialized'
    }), 503


@verification_bp.route('/api/verify/<receipt_id>')
def verify_receipt(receipt_id):
    if not _check_rate_limit(request.remote_addr or '0.0.0.0'):
        return jsonify({'error': 'Rate limit exceeded. Max 30 requests per minute.'}), 429

    if not receipt_id or len(receipt_id) > 64:
        return jsonify({'error': 'Invalid receipt ID'}), 400

    receipt = _get_receipt_from_db(receipt_id)
    if not receipt:
        return jsonify({
            'found': False,
            'receipt_id': receipt_id,
            'error': 'Receipt not found'
        }), 404

    _init_verifier()
    if VERIFIER_AVAILABLE:
        verification = ReceiptVerifier.verify_receipt(receipt)
    else:
        verification = {
            'receipt_id': receipt_id,
            'hash_valid': None,
            'signature_valid': None,
            'overall_valid': None,
            'note': 'Verification engine not available'
        }

    return jsonify({
        'found': True,
        'receipt': {
            'receipt_id': receipt['receipt_id'],
            'timestamp': receipt['timestamp'],
            'asset': receipt['asset'],
            'decision': receipt['decision'],
            'content_hash': receipt['content_hash'],
            'prev_hash': receipt['prev_hash'][:16] + '...' if receipt['prev_hash'] else '',
            'signature_algorithm': receipt['signature_algorithm'],
            'has_signature': bool(receipt.get('signature')),
            'policy_version': receipt.get('policy_version') or '—',
            'engine_version': receipt.get('engine_version') or '—',
            'veto_chain': receipt.get('veto_chain') or [],
        },
        'verification': verification
    })


@verification_bp.route('/api/verify/chain')
def verify_chain():
    limit = request.args.get('limit', 50, type=int)
    limit = min(limit, 200)

    try:
        with get_db_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database not available'}), 503
            cur = conn.cursor()
            cur.execute("""
                SELECT receipt_id, content_hash, prev_hash, timestamp_utc, asset, decision
                FROM decision_receipts
                ORDER BY created_at ASC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            cur.close()

        receipts = [
            {
                'receipt_id': r[0],
                'content_hash': r[1],
                'prev_hash': r[2],
                'timestamp': r[3],
                'asset': r[4],
                'decision': r[5]
            }
            for r in rows
        ]

        _init_verifier()
        if VERIFIER_AVAILABLE:
            chain_result = ReceiptVerifier.verify_chain(receipts)
        else:
            chain_result = {'chain_valid': None, 'length': len(receipts), 'note': 'Verifier not available'}

        return jsonify({
            'chain': chain_result,
            'total_receipts': len(receipts)
        })
    except Exception as e:
        logger.error(f"Error verifying chain: {e}")
        return jsonify({'error': 'Verification failed'}), 500


@verification_bp.route('/api/verify/recent')
def recent_receipts():
    """Return recently signed governance receipts for the public ledger view.

    Filters applied (ADR-063):
    - signature_algorithm must be present and not 'NONE' — unsigned/test receipts excluded.
    - asset must match the canonical trading-pair pattern ^[A-Z0-9]+/[A-Z]+$ — internal
      test assets (e.g. 'UNINTELLIGIBLE-SCENARIO') are excluded at the database layer.
    - NULL guards on both columns ensure deterministic predicate evaluation.

    These filters protect the public /verify page from displaying test data visible to
    investors and auditors. Individual receipt lookup (/api/verify/<id>) is unaffected.
    """
    limit = request.args.get('limit', 20, type=int)
    limit = min(limit, 100)

    try:
        with get_db_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database not available'}), 503
            cur = conn.cursor()
            cur.execute("""
                SELECT receipt_id, timestamp_utc, asset, decision,
                       signature_algorithm, content_hash
                FROM decision_receipts
                WHERE signature_algorithm IS NOT NULL
                  AND signature_algorithm <> 'NONE'
                  AND asset IS NOT NULL
                  AND asset ~ '^[A-Z0-9]+/[A-Z]+$'
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            cur.close()

        receipts = [
            {
                'receipt_id': r[0],
                'timestamp': r[1].isoformat() if hasattr(r[1], 'isoformat') else str(r[1]),
                'asset': r[2],
                'decision': r[3],
                'signed': True,
                'hash_prefix': (r[5] or '')[:16] + '...' if r[5] else ''
            }
            for r in rows
        ]

        return jsonify({'receipts': receipts, 'count': len(receipts)})
    except Exception as e:
        logger.error(f"Error fetching recent receipts: {e}")
        return jsonify({'error': 'Failed to fetch receipts'}), 500


@verification_bp.route('/api/governance/metrics')
def governance_metrics():
    try:
        with get_db_connection() as conn:
            if not conn:
                return jsonify({'error': 'Database not available'}), 503
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM decision_receipts")
            total_receipts = cur.fetchone()[0]

            cur.execute("SELECT decision, COUNT(*) FROM decision_receipts GROUP BY decision")
            decision_counts = {row[0]: row[1] for row in cur.fetchall()}

            cur.execute("SELECT COUNT(*) FROM shadow_trade_events")
            total_shadow = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(*) FROM shadow_trade_events 
                WHERE veto_reason IS NOT NULL AND veto_reason != ''
            """)
            vetoed_count = cur.fetchone()[0]

            cur.execute("""
                SELECT 
                    CASE 
                        WHEN veto_reason LIKE 'Risk level%%' THEN 'Risk Assessment Gate'
                        WHEN veto_reason LIKE 'ECW%%' THEN 'Edge Confirmation Window'
                        WHEN veto_reason LIKE 'Coherence%%' THEN 'Coherence Gate'
                        WHEN veto_reason LIKE 'Monte Carlo%%' THEN 'Monte Carlo Validation'
                        WHEN veto_reason LIKE 'RMS%%' THEN 'Risk Management System'
                        ELSE 'Other Governance Gate'
                    END as category,
                    COUNT(*) as cnt 
                FROM shadow_trade_events 
                WHERE veto_reason IS NOT NULL AND veto_reason != ''
                GROUP BY category 
                ORDER BY cnt DESC 
                LIMIT 10
            """)
            veto_reasons = [{'category': row[0], 'count': row[1]} for row in cur.fetchall()]

            cur.execute("""
                SELECT asset, COUNT(*) as cnt
                FROM decision_receipts
                GROUP BY asset
                ORDER BY cnt DESC
            """)
            asset_breakdown = [{'asset': row[0], 'count': row[1]} for row in cur.fetchall()]

            cur.execute("""
                SELECT COALESCE(SUM(realized_pnl), 0)
                FROM trades
                WHERE status = 'closed'
            """)
            row = cur.fetchone()
            total_pnl = float(row[0]) if row and row[0] is not None else 0.0
            capital_preserved_pct = round(max(0, (1_000_000 + total_pnl) / 1_000_000 * 100), 2)

            from datetime import datetime, timezone
            track_record_start = datetime(2026, 1, 15, tzinfo=timezone.utc)
            system_uptime_days = (datetime.now(timezone.utc) - track_record_start).days + 1

            cur.close()

        block_rate = 0
        if total_shadow > 0:
            block_rate = round((vetoed_count / total_shadow) * 100, 1)

        return jsonify({
            'governance_summary': {
                'total_evaluation_cycles': total_shadow,
                'total_receipts': total_receipts,
                'decisions_blocked': vetoed_count,
                'capital_preserved_pct': capital_preserved_pct,
                'verticals_demo': 8,
                'system_uptime_days': system_uptime_days,
                'decisions': decision_counts,
                'capital_exposure_block_rate': f"{block_rate}%",
                'governance_gates_activity': veto_reasons,
                'asset_breakdown': asset_breakdown,
            },
            'methodology': {
                'receipt_integrity': 'SHA-256 hash chain',
                'signature_algorithm': 'Dilithium-3 (ML-DSA-65, NIST-standardized)',
                'verification': 'Public endpoint available at /api/verify/<receipt_id>',
            },
            'disclaimer': 'Internal dataset, not externally audited. Evaluation cycles represent governance engine processing, not executed trades.'
        })
    except Exception as e:
        logger.error(f"Error computing governance metrics: {e}")
        return jsonify({'error': 'Failed to compute metrics'}), 500
