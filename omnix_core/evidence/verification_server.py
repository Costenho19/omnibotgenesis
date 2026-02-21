import os
import json
import hashlib
import base64
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from aiohttp import web

logger = logging.getLogger("OMNIX.VerificationServer")

try:
    from pqc.sign import dilithium3
    PQC_AVAILABLE = True
except ImportError:
    PQC_AVAILABLE = False
    dilithium3 = None

_signing_keys = None
_public_key_b64 = None

_rate_limit_store = defaultdict(list)
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 30


def _init_signing_keys():
    global _signing_keys, _public_key_b64
    if _signing_keys is not None:
        return
    if not PQC_AVAILABLE:
        logger.warning("PQC not available for verification server")
        return
    try:
        _signing_keys = dilithium3.keypair()
        _public_key_b64 = base64.b64encode(_signing_keys[0]).decode('utf-8')
        logger.info("Verification server signing keys generated (Dilithium-3)")
    except Exception as e:
        logger.error(f"Failed to generate signing keys: {e}")


def _get_db_connection():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        return None
    try:
        import psycopg2
        return psycopg2.connect(db_url)
    except ImportError:
        try:
            import psycopg
            return psycopg.connect(db_url, autocommit=True)
        except Exception as e:
            logger.error(f"DB connection failed (psycopg3): {e}")
            return None
    except Exception as e:
        logger.error(f"DB connection failed: {e}")
        return None


def _check_rate_limit(ip: str) -> bool:
    now = time.time()
    _rate_limit_store[ip] = [t for t in _rate_limit_store[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limit_store[ip]) >= RATE_LIMIT_MAX:
        return False
    _rate_limit_store[ip].append(now)
    return True


VERIFY_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OMNIX Decision Governance | Receipt Verification</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0a0e17; color: #e5e7eb; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
        .verify-container { max-width: 760px; margin: 0 auto; padding: 2rem 1rem; }
        .receipt-field { display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
        .receipt-field .label { color: #9ca3af; font-size: 0.85rem; }
        .receipt-field .value { font-family: 'Courier New', monospace; font-size: 0.85rem; text-align: right; max-width: 60%; word-break: break-all; }
        .status-badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; font-family: 'Courier New', monospace; }
        .status-valid { background: rgba(34,197,94,0.15); color: #22c55e; border: 1px solid rgba(34,197,94,0.3); }
        .status-invalid { background: rgba(239,68,68,0.15); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }
        .status-pending { background: rgba(234,179,8,0.15); color: #eab308; border: 1px solid rgba(234,179,8,0.3); }
        .hash-display { font-family: 'Courier New', monospace; font-size: 0.75rem; color: #60a5fa; word-break: break-all; }
        #searchInput { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15); color: #fff; padding: 12px 16px; font-family: 'Courier New', monospace; font-size: 0.95rem; width: 100%; border-radius: 6px; }
        #searchInput:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.2); }
        #searchInput::placeholder { color: #6b7280; }
        a { color: #3b82f6; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
<div class="verify-container">
    <div style="text-align: center; margin-bottom: 2rem;">
        <div style="font-size: 0.75rem; color: #6b7280; letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 4px;">OMNIX Decision Governance</div>
        <h1 style="font-size: 1.5rem; font-weight: 700; margin: 0;">Receipt Verification</h1>
        <p style="color: #9ca3af; font-size: 0.85rem; margin-top: 6px;">Independently verify the authenticity of governance decisions</p>
    </div>

    <div style="margin-bottom: 2rem;">
        <div style="display: flex; gap: 8px;">
            <input type="text" id="searchInput" placeholder="Enter Receipt ID (e.g., OMNIX-A1B2C3D4E5F6)" autocomplete="off" spellcheck="false">
            <button onclick="verifyReceipt()" id="verifyBtn" style="background: #3b82f6; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-weight: 600; white-space: nowrap; font-size: 0.9rem;">Verify</button>
        </div>
    </div>

    <div id="result" style="display: none;"></div>

    <div id="recentSection" style="margin-top: 2rem;">
        <h3 style="font-size: 0.85rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1rem;">Recent Governance Receipts</h3>
        <div id="recentList" style="font-size: 0.85rem; color: #6b7280;">Loading...</div>
    </div>

    <div style="margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid rgba(255,255,255,0.06); text-align: center;">
        <div style="font-size: 0.75rem; color: #4b5563;">
            Signatures use NIST-standardized Dilithium-3 (ML-DSA-65) post-quantum cryptography.<br>
            Hash chain provides tamper-evident ledger integrity (SHA-256).<br>
            <a href="/api/public_key">View Public Key</a>
        </div>
    </div>
</div>

<script>
const searchInput = document.getElementById('searchInput');
searchInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') verifyReceipt();
});

async function verifyReceipt() {
    const receiptId = searchInput.value.trim();
    if (!receiptId) return;

    const btn = document.getElementById('verifyBtn');
    const resultDiv = document.getElementById('result');
    btn.disabled = true;
    btn.textContent = 'Verifying...';
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<div style="text-align:center; color:#6b7280; padding:2rem;">Verifying receipt...</div>';

    try {
        const res = await fetch('/api/verify/' + encodeURIComponent(receiptId));
        const data = await res.json();
        if (!data.found) {
            resultDiv.innerHTML = renderNotFound(receiptId);
        } else {
            resultDiv.innerHTML = renderVerification(data);
        }
    } catch(err) {
        resultDiv.innerHTML = '<div style="color:#ef4444; padding:1rem; background:rgba(239,68,68,0.1); border-radius:6px;">Verification service unavailable. Please try again.</div>';
    }

    btn.disabled = false;
    btn.textContent = 'Verify';
}

function renderNotFound(id) {
    return '<div style="padding:1.5rem; background:rgba(239,68,68,0.05); border:1px solid rgba(239,68,68,0.2); border-radius:8px;"><div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;"><span class="status-badge status-invalid">NOT FOUND</span></div><p style="color:#9ca3af; font-size:0.85rem; margin:0;">Receipt <code style="color:#ef4444;">' + id + '</code> does not exist in the governance ledger.</p></div>';
}

function renderVerification(data) {
    var r = data.receipt;
    var v = data.verification;
    var isValid = v.overall_valid;
    var statusClass = isValid ? 'status-valid' : (isValid === false ? 'status-invalid' : 'status-pending');
    var statusText = isValid ? 'VALID' : (isValid === false ? 'INVALID' : 'PENDING');

    var html = '<div style="padding:1.5rem; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:8px;">';
    html += '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem;"><span class="status-badge ' + statusClass + '">' + statusText + '</span><span style="font-family:monospace; font-size:0.8rem; color:#6b7280;">' + r.receipt_id + '</span></div>';
    html += '<div style="margin-bottom:1.5rem;">';
    html += '<div class="receipt-field"><span class="label">Timestamp</span><span class="value">' + r.timestamp + '</span></div>';
    html += '<div class="receipt-field"><span class="label">Asset</span><span class="value">' + r.asset + '</span></div>';
    html += '<div class="receipt-field"><span class="label">Decision</span><span class="value" style="color:' + (r.decision==='APPROVE'?'#22c55e':r.decision==='BLOCK'?'#ef4444':'#eab308') + '">' + r.decision + '</span></div>';
    html += '<div class="receipt-field"><span class="label">Signature Algorithm</span><span class="value">' + r.signature_algorithm + '</span></div>';
    html += '</div>';
    html += '<div style="margin-bottom:1.5rem;"><div style="font-size:0.8rem; color:#6b7280; margin-bottom:6px;">VERIFICATION CHECKS</div>';
    html += '<div class="receipt-field"><span class="label">Hash Integrity</span><span class="value">' + renderCheck(v.hash_valid) + '</span></div>';
    html += '<div class="receipt-field"><span class="label">Signature Valid</span><span class="value">' + renderCheck(v.signature_valid) + '</span></div>';
    html += '</div>';
    html += '<div style="margin-bottom:1rem;"><div style="font-size:0.8rem; color:#6b7280; margin-bottom:6px;">CONTENT HASH</div><div class="hash-display">' + r.content_hash + '</div></div>';
    html += '</div>';
    return html;
}

function renderCheck(val) {
    if (val === true) return '<span style="color:#22c55e;">PASS</span>';
    if (val === false) return '<span style="color:#ef4444;">FAIL</span>';
    return '<span style="color:#eab308;">N/A</span>';
}

async function loadRecent() {
    try {
        var res = await fetch('/api/verify/recent?limit=10');
        var data = await res.json();
        var list = document.getElementById('recentList');
        if (!data.receipts || data.receipts.length === 0) {
            list.innerHTML = '<div style="color:#4b5563; font-style:italic;">No receipts recorded yet. Receipts are generated as the governance engine processes evaluation cycles.</div>';
            return;
        }
        var html = '';
        data.receipts.forEach(function(r) {
            var decColor = r.decision==='APPROVE'?'#22c55e':r.decision==='BLOCK'?'#ef4444':'#eab308';
            html += '<div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid rgba(255,255,255,0.04); cursor:pointer;" onclick="searchInput.value=\\'' + r.receipt_id + '\\'; verifyReceipt();">';
            html += '<div><span style="font-family:monospace; font-size:0.8rem; color:#60a5fa;">' + r.receipt_id + '</span>';
            html += '<span style="margin-left:8px; font-size:0.8rem; color:' + decColor + ';">' + r.decision + '</span>';
            html += '<span style="margin-left:8px; font-size:0.78rem; color:#6b7280;">' + r.asset + '</span></div>';
            html += '<span style="font-size:0.75rem; color:#4b5563;">' + (r.signed ? 'PQC Signed' : 'Unsigned') + '</span></div>';
        });
        list.innerHTML = html;
    } catch(e) {
        document.getElementById('recentList').innerHTML = '<div style="color:#4b5563;">Unable to load recent receipts.</div>';
    }
}

loadRecent();
</script>
</body>
</html>"""


def _verify_receipt_crypto(receipt: dict) -> dict:
    result = {
        'receipt_id': receipt.get('receipt_id', 'UNKNOWN'),
        'hash_valid': False,
        'signature_valid': None,
        'verification_timestamp': datetime.now(timezone.utc).isoformat(),
    }

    payload_for_hash = {
        'receipt_id': receipt.get('receipt_id'),
        'timestamp': receipt.get('timestamp'),
        'asset': receipt.get('asset'),
        'decision': receipt.get('decision'),
        'veto_chain': receipt.get('veto_chain'),
        'policy_version': receipt.get('policy_version'),
        'engine_version': receipt.get('engine_version'),
        'prev_hash': receipt.get('prev_hash'),
    }

    canonical = json.dumps(payload_for_hash, sort_keys=True, ensure_ascii=True)
    computed_hash = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    result['hash_valid'] = (computed_hash == receipt.get('content_hash'))
    result['computed_hash'] = computed_hash
    result['stored_hash'] = receipt.get('content_hash')

    sig_b64 = receipt.get('signature')
    pub_key_b64 = receipt.get('public_key')

    if sig_b64 and pub_key_b64 and PQC_AVAILABLE:
        try:
            signature = base64.b64decode(sig_b64)
            public_key = base64.b64decode(pub_key_b64)
            message = receipt['content_hash'].encode('utf-8')
            dilithium3.verify(signature, message, public_key)
            result['signature_valid'] = True
        except Exception:
            result['signature_valid'] = False
    elif not PQC_AVAILABLE:
        result['signature_note'] = 'PQC library not available for verification'
    elif not sig_b64:
        result['signature_note'] = 'Receipt was not signed'

    result['overall_valid'] = result['hash_valid'] and (result['signature_valid'] is not False)
    result['algorithm'] = receipt.get('signature_algorithm', 'UNKNOWN')

    return result


async def handle_verify_page(request):
    return web.Response(text=VERIFY_HTML, content_type='text/html')


async def handle_health(request):
    return web.json_response({'status': 'ok', 'service': 'OMNIX Verification'})


async def handle_verify_receipt(request):
    receipt_id = request.match_info.get('receipt_id', '')
    ip = request.remote or '0.0.0.0'

    if not _check_rate_limit(ip):
        return web.json_response({'error': 'Rate limit exceeded. Max 30 requests per minute.'}, status=429)

    if not receipt_id or len(receipt_id) > 64:
        return web.json_response({'error': 'Invalid receipt ID'}, status=400)

    conn = _get_db_connection()
    if not conn:
        return web.json_response({'error': 'Database not available'}, status=503)

    try:
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
        conn.close()

        if not row:
            return web.json_response({
                'found': False,
                'receipt_id': receipt_id,
                'error': 'Receipt not found'
            }, status=404)

        veto_chain = row[4]
        if isinstance(veto_chain, str):
            try:
                veto_chain = json.loads(veto_chain)
            except json.JSONDecodeError:
                veto_chain = []

        receipt = {
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
        }

        verification = _verify_receipt_crypto(receipt)

        return web.json_response({
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
            },
            'verification': verification
        })
    except Exception as e:
        logger.error(f"Error verifying receipt: {e}")
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        return web.json_response({'error': 'Verification failed'}, status=500)


async def handle_public_key(request):
    _init_signing_keys()
    if _public_key_b64:
        return web.json_response({
            'public_key': _public_key_b64,
            'algorithm': 'Dilithium-3 (ML-DSA-65)',
            'standard': 'NIST-standardized post-quantum digital signature',
            'key_size': '1952 bytes',
            'security_level': 'NIST Level 3 (~192-bit classical equivalent)',
            'note': 'This key is generated per engine instance. Production keys are versioned and persistent.'
        })
    return web.json_response({
        'error': 'Public key not available',
        'reason': 'PQC engine not initialized'
    }, status=503)


async def handle_recent_receipts(request):
    limit = int(request.query.get('limit', '20'))
    limit = min(limit, 100)

    conn = _get_db_connection()
    if not conn:
        return web.json_response({'error': 'Database not available'}, status=503)

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT receipt_id, timestamp_utc, asset, decision,
                   signature_algorithm, content_hash
            FROM decision_receipts
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        receipts = [
            {
                'receipt_id': r[0],
                'timestamp': r[1],
                'asset': r[2],
                'decision': r[3],
                'signed': r[4] != 'NONE',
                'hash_prefix': r[5][:16] + '...'
            }
            for r in rows
        ]

        return web.json_response({'receipts': receipts, 'count': len(receipts)})
    except Exception as e:
        logger.error(f"Error fetching recent receipts: {e}")
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        return web.json_response({'error': 'Failed to fetch receipts'}, status=500)


async def handle_governance_metrics(request):
    conn = _get_db_connection()
    if not conn:
        return web.json_response({'error': 'Database not available'}, status=503)

    try:
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

        cur.close()
        conn.close()

        block_rate = 0
        if total_shadow > 0:
            block_rate = round((vetoed_count / total_shadow) * 100, 1)

        return web.json_response({
            'governance_summary': {
                'total_evaluation_cycles': total_shadow,
                'total_receipts': total_receipts,
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
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        return web.json_response({'error': 'Failed to compute metrics'}, status=500)


def create_verification_app() -> web.Application:
    app = web.Application()
    app.router.add_get('/', handle_health)
    app.router.add_get('/verify', handle_verify_page)
    app.router.add_get('/api/verify/recent', handle_recent_receipts)
    app.router.add_get('/api/verify/{receipt_id}', handle_verify_receipt)
    app.router.add_get('/api/public_key', handle_public_key)
    app.router.add_get('/api/governance/metrics', handle_governance_metrics)
    return app


async def start_verification_server(port: int = 8000):
    app = create_verification_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Verification server running on port {port}")
    return runner
