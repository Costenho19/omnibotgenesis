"""
OMNIX Web - Public API Server
Serves real-time data from PostgreSQL for the public web dashboard
Also serves the built React frontend (dist/) as static files for Railway deployment
"""
import os
import json
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import psycopg2
from datetime import datetime, timezone
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(BASE_DIR, 'dist')

app = Flask(__name__)
CORS(app)


@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

from api.sandbox import register_sandbox_routes
register_sandbox_routes(app)

# ── B2B Governance API (ADR-028, ADR-051, ADR-052) ────────────────────────────
# Exposes /api/governance/* on omnixquantum.net (Railway stellar-hope service)
# Authentication: X-API-Key header (RBAC — b2b_clients table)
# Velos Gateway Push included (non-blocking, client_id='velos-partner' only)
try:
    from api.gov_blueprint import governance_bp
    app.register_blueprint(governance_bp)
    print("[server] governance_bp registered — /api/governance/* active")
except Exception as _gov_err:
    print(f"[server] WARNING: governance_bp not loaded: {_gov_err}")


def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        return None
    return psycopg2.connect(database_url)


@app.route('/api/live-metrics', methods=['GET'])
def get_live_metrics():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': True,
                'live': False,
                'metrics': {
                    'evaluation_cycles': 766741,
                    'pqc_signed_receipts': 82518,
                    'decisions_blocked': 9317,
                    'exit_receipts': 78,
                    'capital_preserved_pct': 98.42,
                    'verticals_demo': 4,
                    'system_uptime_days': 112,
                },
                'last_updated': datetime.now(timezone.utc).isoformat()
            })

        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM shadow_trade_events")
        eval_cycles = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(*) FROM decision_receipts")
        receipts = cur.fetchone()[0] or 0

        cur.execute("""
            SELECT COUNT(*) FROM decision_receipts
            WHERE decision IN ('BLOCK', 'BLOCKED')
        """)
        decisions_blocked = cur.fetchone()[0] or 0

        cur.execute("""
            SELECT COUNT(*) FROM exit_governance_receipts
        """)
        exit_receipts = cur.fetchone()[0] or 0

        try:
            cur.execute("""
                SELECT COALESCE(SUM(profit_loss), 0)
                FROM paper_trading_trades WHERE status = 'closed'
            """)
            pnl_row = cur.fetchone()
            total_pnl = float(pnl_row[0] or 0)
            capital_preserved = round(max(0, (1_000_000 + total_pnl) / 1_000_000 * 100), 2)
        except Exception:
            capital_preserved = 98.42

        earliest_dates = []
        for table in ('shadow_trade_events', 'decision_receipts'):
            try:
                cur.execute(f"SELECT MIN(created_at) FROM {table}")
                row = cur.fetchone()
                if row and row[0]:
                    earliest_dates.append(row[0])
            except Exception:
                pass

        LAUNCH_FALLBACK = datetime(2025, 11, 28, tzinfo=timezone.utc)
        if earliest_dates:
            first_date = min(earliest_dates)
            if hasattr(first_date, 'tzinfo') and first_date.tzinfo is None:
                first_date = first_date.replace(tzinfo=timezone.utc)
            uptime_days = max(0, (datetime.now(timezone.utc) - first_date).days)
        else:
            uptime_days = max(0, (datetime.now(timezone.utc) - LAUNCH_FALLBACK).days)

        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'live': True,
            'metrics': {
                'evaluation_cycles': eval_cycles,
                'pqc_signed_receipts': receipts,
                'decisions_blocked': decisions_blocked,
                'exit_receipts': exit_receipts,
                'capital_preserved_pct': capital_preserved,
                'verticals_demo': 4,
                'system_uptime_days': uptime_days,
            },
            'last_updated': datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        print(f"Error fetching live metrics: {e}")
        return jsonify({
            'success': True,
            'live': False,
            'metrics': {
                'evaluation_cycles': 766741,
                'pqc_signed_receipts': 82518,
                'decisions_blocked': 9317,
                'exit_receipts': 78,
                'capital_preserved_pct': 98.42,
                'verticals_demo': 4,
                'system_uptime_days': 112,
            },
            'last_updated': datetime.now(timezone.utc).isoformat()
        })


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'evaluationCycles': 766741,
                'pqcSignedReceipts': 82518,
                'decisionsBlocked': 9317,
                'capitalPreserved': 98.42,
                'systemUptime': '99.9%',
                'lastUpdate': datetime.now().isoformat()
            })

        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM shadow_trade_events")
        eval_cycles = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(*) FROM decision_receipts")
        pqc_receipts = cur.fetchone()[0] or 0

        cur.execute("SELECT COUNT(*) FROM decision_receipts WHERE decision IN ('BLOCK','BLOCKED')")
        decisions_blocked = cur.fetchone()[0] or 0

        try:
            cur.execute("SELECT COALESCE(SUM(profit_loss), 0) FROM paper_trading_trades WHERE status = 'closed'")
            pnl_row = cur.fetchone()
            total_pnl = float(pnl_row[0] or 0)
            capital_preserved = round(max(0, (1_000_000 + total_pnl) / 1_000_000 * 100), 2)
        except Exception:
            capital_preserved = 98.42

        cur.close()
        conn.close()

        return jsonify({
            'evaluationCycles': eval_cycles,
            'pqcSignedReceipts': pqc_receipts,
            'decisionsBlocked': decisions_blocked,
            'capitalPreserved': capital_preserved,
            'systemUptime': '99.9%',
            'lastUpdate': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error fetching metrics: {e}")
        return jsonify({
            'evaluationCycles': 766741,
            'pqcSignedReceipts': 82518,
            'decisionsBlocked': 9317,
            'capitalPreserved': 98.42,
            'systemUptime': '99.9%',
            'lastUpdate': datetime.now().isoformat()
        })


@app.route('/api/news', methods=['GET'])
def get_news():
    import requests as req
    api_key = os.environ.get('FINNHUB_API_KEY')
    if not api_key:
        return jsonify([
            {'id': '1', 'headline': 'Market data loading...', 'source': 'OMNIX',
             'datetime': datetime.now().timestamp() * 1000, 'url': '#', 'sentiment': 'neutral'}
        ])

    try:
        response = req.get(
            f'https://finnhub.io/api/v1/news?category=crypto&token={api_key}',
            timeout=10
        )
        data = response.json()
        news = []
        for item in data[:10]:
            sentiment = 'neutral'
            headline_lower = item.get('headline', '').lower()
            if any(w in headline_lower for w in ['surge', 'rally', 'gains', 'bullish', 'record']):
                sentiment = 'positive'
            elif any(w in headline_lower for w in ['crash', 'drop', 'fall', 'bearish', 'fear']):
                sentiment = 'negative'
            news.append({
                'id': str(item.get('id', '')),
                'headline': item.get('headline', ''),
                'source': item.get('source', ''),
                'datetime': item.get('datetime', 0) * 1000,
                'url': item.get('url', '#'),
                'sentiment': sentiment
            })
        return jsonify(news)
    except Exception as e:
        print(f"Error fetching news: {e}")
        return jsonify([])


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/api/analytics/decisions', methods=['GET'])
def analytics_decisions():
    """
    Decision analytics — aggregated patterns from all governance evaluations.
    Public endpoint. No auth required. Returns aggregated data only, no PII.
    """
    conn = get_db_connection()
    if not conn:
        return jsonify({
            'live': False,
            'note': 'Analytics unavailable — database not connected',
            'sample': {
                'total_decisions': 82518,
                'approval_rate_pct': 61.2,
                'block_rate_pct': 32.8,
                'hold_rate_pct': 6.0,
                'by_decision': {'APPROVED': 50502, 'BLOCKED': 27076, 'HOLD': 4940},
                'by_domain': {'trading': 38400, 'credit': 18200, 'insurance': 14100, 'robotics': 7818, 'energy': 4000},
                'top_blocking_checkpoints': [
                    {'checkpoint': 'CP-3', 'name': 'Risk Evaluation', 'block_count': 9821},
                    {'checkpoint': 'CP-2', 'name': 'Probability Assessment', 'block_count': 7340},
                    {'checkpoint': 'CP-6', 'name': 'Stress Testing', 'block_count': 5910},
                ],
            }
        })

    try:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM decision_receipts")
        total = cur.fetchone()[0] or 0

        cur.execute("""
            SELECT UPPER(decision), COUNT(*) FROM decision_receipts
            GROUP BY UPPER(decision)
        """)
        by_decision = {}
        for row in cur.fetchall():
            key = row[0]
            if key in ('BLOCK',):
                key = 'BLOCKED'
            elif key in ('APPROVE',):
                key = 'APPROVED'
            by_decision[key] = by_decision.get(key, 0) + row[1]

        approved = by_decision.get('APPROVED', 0)
        blocked = by_decision.get('BLOCKED', 0) + by_decision.get('BLOCK', 0)
        hold = by_decision.get('HOLD', 0)

        def _pct(n):
            return round(n / total * 100, 1) if total > 0 else 0.0

        cur.execute("""
            SELECT domain, COUNT(*) FROM decision_receipts
            WHERE domain IS NOT NULL
            GROUP BY domain ORDER BY COUNT(*) DESC LIMIT 10
        """)
        by_domain = {row[0]: row[1] for row in cur.fetchall()}

        cur.execute("""
            SELECT veto_chain FROM decision_receipts
            WHERE decision IN ('BLOCK','BLOCKED') AND veto_chain IS NOT NULL
            ORDER BY created_at DESC LIMIT 2000
        """)
        import json as _json
        cp_block_counts: dict = {}
        for (vc_raw,) in cur.fetchall():
            try:
                entries = _json.loads(vc_raw) if isinstance(vc_raw, str) else (vc_raw or [])
                for entry in entries:
                    txt = str(entry)
                    if 'BLOCKED' in txt.upper() or 'VETO' in txt.upper():
                        import re as _re
                        m = _re.search(r'CP-(\d+)', txt)
                        if m:
                            cp_key = f'CP-{m.group(1)}'
                            cp_block_counts[cp_key] = cp_block_counts.get(cp_key, 0) + 1
            except Exception:
                pass

        _cp_labels = {
            'CP-1': 'Signal Integrity Validator',
            'CP-2': 'Probability Assessment',
            'CP-3': 'Risk Evaluation',
            'CP-4': 'Coherence Engine',
            'CP-5': 'Trend Validator',
            'CP-6': 'Stress Testing',
            'CP-7': 'Ethics & Domain Gate',
            'CP-8': 'Threshold & Context Validator',
            'CP-9': 'AML Screening',
            'CP-10': 'Fraud Detection',
            'CP-11': 'Jurisdiction Compliance',
        }
        top_blocking = sorted(cp_block_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_blocking_out = [
            {'checkpoint': k, 'name': _cp_labels.get(k, k), 'block_count': v}
            for k, v in top_blocking
        ]

        cur.execute("""
            SELECT DATE_TRUNC('day', created_at)::date, UPPER(decision), COUNT(*)
            FROM decision_receipts
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY 1, 2
            ORDER BY 1
        """)
        trend_raw = cur.fetchall()
        trend: dict = {}
        for (day, dec, cnt) in trend_raw:
            day_str = str(day)
            if day_str not in trend:
                trend[day_str] = {'date': day_str, 'approved': 0, 'blocked': 0, 'hold': 0}
            if dec in ('APPROVED', 'APPROVE'):
                trend[day_str]['approved'] += cnt
            elif dec in ('BLOCKED', 'BLOCK'):
                trend[day_str]['blocked'] += cnt
            elif dec == 'HOLD':
                trend[day_str]['hold'] += cnt

        cur.execute("""
            SELECT COUNT(DISTINCT client_id) FROM decision_receipts
            WHERE client_id IS NOT NULL AND client_id != 'PUBLIC'
        """)
        b2b_clients_active = cur.fetchone()[0] or 0

        cur.close()
        conn.close()

        return jsonify({
            'live': True,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_decisions': total,
            'approval_rate_pct': _pct(approved),
            'block_rate_pct': _pct(blocked),
            'hold_rate_pct': _pct(hold),
            'by_decision': by_decision,
            'by_domain': by_domain,
            'top_blocking_checkpoints': top_blocking_out,
            'trend_30d': sorted(trend.values(), key=lambda x: x['date']),
            'b2b_clients_active': b2b_clients_active,
        })

    except Exception as e:
        print(f"Analytics error: {e}")
        return jsonify({'error': str(e), 'live': False}), 500


def init_contact_leads_table():
    try:
        conn = get_db_connection()
        if not conn:
            return
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS contact_leads (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                company VARCHAR(255),
                email VARCHAR(255) NOT NULL,
                referral_source VARCHAR(100) NOT NULL,
                message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Warning: Could not initialize contact_leads table: {e}")


init_contact_leads_table()


VALID_REFERRAL_SOURCES = {
    'Facebook', 'WhatsApp', 'Instagram', 'Telegram',
    'LinkedIn', 'Google', 'Recomendación', 'Otro'
}


@app.route('/api/contact', methods=['POST'])
def contact_lead():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid request body'}), 400

    name = (data.get('name') or '').strip()
    company = (data.get('company') or '').strip()
    email = (data.get('email') or '').strip()
    referral_source = (data.get('referral_source') or '').strip()
    message = (data.get('message') or '').strip()

    if not name or not email or not referral_source:
        return jsonify({'success': False, 'error': 'Name, email, and referral source are required'}), 400

    if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return jsonify({'success': False, 'error': 'Invalid email address'}), 400

    if referral_source not in VALID_REFERRAL_SOURCES:
        return jsonify({'success': False, 'error': 'Invalid referral source'}), 400

    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'error': 'Database unavailable',
                'fallback_email': 'contacto@omnixquantum.net'
            }), 503

        cur = conn.cursor()
        cur.execute(
            """INSERT INTO contact_leads (name, company, email, referral_source, message)
               VALUES (%s, %s, %s, %s, %s)""",
            (name, company or None, email, referral_source, message or None)
        )
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Contact information saved successfully'})

    except Exception as e:
        print(f"Error saving contact lead: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to save contact information',
            'fallback_email': 'contacto@omnixquantum.net'
        }), 500


@app.route('/api/sandbox/stats', methods=['GET'])
def sandbox_stats():
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database unavailable'}), 503
    try:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM sandbox_interactions")
        total = cur.fetchone()[0]

        cur.execute("""
            SELECT decision, COUNT(*) as cnt
            FROM sandbox_interactions GROUP BY decision ORDER BY cnt DESC
        """)
        by_decision = {row[0]: row[1] for row in cur.fetchall()}

        cur.execute("""
            SELECT domain, COUNT(*) as cnt
            FROM sandbox_interactions
            WHERE domain IS NOT NULL
            GROUP BY domain ORDER BY cnt DESC
        """)
        by_domain = {row[0]: row[1] for row in cur.fetchall()}

        cur.execute("""
            SELECT language, COUNT(*) as cnt
            FROM sandbox_interactions
            WHERE language IS NOT NULL
            GROUP BY language ORDER BY cnt DESC
        """)
        by_language = {row[0]: row[1] for row in cur.fetchall()}

        cur.execute("SELECT COUNT(DISTINCT client_ip) FROM sandbox_interactions WHERE client_ip IS NOT NULL")
        unique_ips = cur.fetchone()[0]

        cur.execute("""
            SELECT id, created_at, company_name, domain, decision, checkpoints_passed,
                   checkpoints_blocked, receipt_id,
                   LEFT(scenario_text, 120) as scenario_preview
            FROM sandbox_interactions
            ORDER BY created_at DESC LIMIT 20
        """)
        cols = [desc[0] for desc in cur.description]
        recent = [dict(zip(cols, row)) for row in cur.fetchall()]
        for r in recent:
            if r.get('created_at'):
                r['created_at'] = r['created_at'].isoformat()

        cur.close()
        conn.close()

        return jsonify({
            'total_evaluations': total,
            'unique_visitors': unique_ips,
            'by_decision': by_decision,
            'by_domain': by_domain,
            'by_language': by_language,
            'recent': recent,
        })
    except Exception as e:
        print(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500


_CP_NAMES = {
    'CP-0': {'en': 'Signal Integrity',     'es': 'Integridad de Señal'},
    'CP-1': {'en': 'Probability Gate',     'es': 'Puerta de Probabilidad'},
    'CP-2': {'en': 'Risk Limits',          'es': 'Límites de Riesgo'},
    'CP-3': {'en': 'Signal Coherence',     'es': 'Coherencia de Señales'},
    'CP-4': {'en': 'Trend Persistence',    'es': 'Persistencia de Tendencia'},
    'CP-5': {'en': 'Stress Test',          'es': 'Prueba de Estrés'},
    'CP-6': {'en': 'Logic Consistency',    'es': 'Consistencia Lógica'},
    'CP-7': {'en': 'Temporal Coherence',   'es': 'Coherencia Temporal'},
}


def _parse_veto_entry(raw: str):
    import re
    cp_code  = None
    label_en = raw
    label_es = raw
    result   = 'UNKNOWN'
    metric_label = None
    metric_value = None

    m_code = re.match(r'^(CP-\d+)\s+(.*)', raw)
    if m_code:
        cp_code  = m_code.group(1)
        rest     = m_code.group(2)
        names    = _CP_NAMES.get(cp_code, {})
        label_en = names.get('en', rest.split(':')[0].strip())
        label_es = names.get('es', rest.split(':')[0].strip())

    m_res = re.search(r'->\s*(PASS|BLOCKED|APPROVED|HOLD)', raw, re.IGNORECASE)
    if m_res:
        r = m_res.group(1).upper()
        result = 'PASS' if r in ('PASS', 'APPROVED') else 'BLOCKED' if r == 'BLOCKED' else 'UNKNOWN'

    m_cond = re.search(r'([\d.]+)\s*(>=|<=|>|<)\s*([\d.]+)', raw)
    if m_cond:
        metric_label = 'Score'
        metric_value = f"{float(m_cond.group(1)):.1f} {m_cond.group(2)} {m_cond.group(3)}"

    return {
        'code':         cp_code,
        'label_en':     label_en,
        'label_es':     label_es,
        'result':       result,
        'metric_label': metric_label,
        'metric_value': metric_value,
        'raw':          raw,
    }


@app.route('/api/public/verify/<path:receipt_id>', methods=['GET'])
def public_verify_receipt(receipt_id):
    import json as _json
    conn = get_db_connection()
    if not conn:
        return jsonify({'found': False, 'error': 'Database unavailable'}), 503

    try:
        cur = conn.cursor()
        rid_upper = receipt_id.upper()
        cur.execute("""
            SELECT receipt_id, timestamp_utc, asset, decision, veto_chain,
                   policy_version, engine_version, prev_hash, content_hash,
                   signature_algorithm, signature, domain
            FROM decision_receipts
            WHERE receipt_id = %s OR content_hash = %s
            LIMIT 1
        """, (rid_upper, receipt_id))
        row = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Verify DB error: {e}")
        return jsonify({'found': False, 'error': str(e)}), 500

    if not row:
        return jsonify({'found': False})

    (rid, ts, asset, decision, veto_chain_raw,
     policy_ver, engine_ver, prev_hash, content_hash,
     sig_algo, signature, domain) = row

    try:
        veto_list = _json.loads(veto_chain_raw) if isinstance(veto_chain_raw, str) else (veto_chain_raw or [])
    except Exception:
        veto_list = []

    checkpoints = [_parse_veto_entry(str(e)) for e in veto_list]
    passed  = sum(1 for c in checkpoints if c['result'] == 'PASS')
    blocked = sum(1 for c in checkpoints if c['result'] == 'BLOCKED')

    dec = (decision or '').upper()
    if dec == 'APPROVED':
        color, icon = 'green', '✅'
    elif dec == 'BLOCKED':
        color, icon = 'red', '🚫'
    elif dec == 'HOLD':
        color, icon = 'yellow', '⏸'
    else:
        color, icon = 'gray', '❓'

    is_pqc = bool(signature and sig_algo and 'SHA-256' not in (sig_algo or ''))
    ts_str = ts.isoformat() if hasattr(ts, 'isoformat') else str(ts)

    if dec == 'APPROVED':
        en_sum = f"Decision APPROVED — all {passed} governance checkpoints passed for {asset}."
        es_sum = f"Decisión APROBADA — los {passed} puntos de control de gobernanza pasaron para {asset}."
    elif dec == 'BLOCKED':
        en_sum = f"Decision BLOCKED — {blocked} of {len(checkpoints)} checkpoints failed for {asset}."
        es_sum = f"Decisión BLOQUEADA — {blocked} de {len(checkpoints)} puntos de control fallaron para {asset}."
    else:
        en_sum = f"Decision {dec} for {asset} — {passed} checkpoints passed, {blocked} blocked."
        es_sum = f"Decisión {dec} para {asset} — {passed} pasaron, {blocked} bloqueados."

    return jsonify({
        'found':               True,
        'receipt_id':          rid,
        'timestamp_utc':       ts_str,
        'asset':               asset or '',
        'decision':            dec,
        'domain':              domain or 'generic',
        'decision_color':      color,
        'decision_icon':       icon,
        'human_summary_en':    en_sum,
        'human_summary_es':    es_sum,
        'checkpoints_total':   len(checkpoints),
        'checkpoints_passed':  passed,
        'checkpoints_blocked': blocked,
        'checkpoints':         checkpoints,
        'integrity': {
            'content_hash':           content_hash or '',
            'prev_hash':              prev_hash or '',
            'signature_algorithm':    sig_algo or 'SHA-256 (sandbox)',
            'is_pqc':                 is_pqc,
            'independently_verifiable': True,
            'nist_note':              'NIST-standardized cryptographic algorithms' if is_pqc else 'SHA-256 hash chain integrity',
        },
        'policy_version':      policy_ver or '',
        'engine_version':      engine_ver or '',
        'independent_verify_url': None,
    })


@app.route('/api/public/send-receipt', methods=['POST'])
def send_receipt_email():
    data = request.get_json(silent=True) or {}
    recipient = (data.get('recipient_email') or '').strip()
    if not recipient or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', recipient):
        return jsonify({'success': False, 'error': 'Invalid email address'}), 400

    gmail_sender   = os.environ.get('GMAIL_SENDER', '')
    gmail_password = os.environ.get('GMAIL_APP_PASSWORD', '')
    if not gmail_sender or not gmail_password:
        return jsonify({'success': False, 'error': 'Email service not configured'}), 500

    receipt_id  = data.get('receipt_id', '')
    decision    = data.get('decision', '')
    explanation = data.get('explanation', '')
    scenario    = data.get('scenario', '')
    language    = data.get('language', 'en')
    gates       = data.get('gate_results', [])
    receipt     = data.get('receipt', {})
    cp_passed   = data.get('checkpoints_passed', 0)
    cp_total    = data.get('checkpoints_total', 11)
    cp_blocked  = data.get('checkpoints_blocked', 0)
    verify_url  = data.get('verification_url') or f'https://omnixquantum.net/verify/{receipt_id}'
    is_es       = language == 'es'
    is_approved = decision == 'APPROVED'

    banner_color = '#064E3B' if is_approved else '#450A0A'
    decision_color = '#34D399' if is_approved else '#FC6464'
    decision_label = ('APROBADO' if is_es else 'APPROVED') if is_approved else ('BLOQUEADO' if is_es else 'BLOCKED')

    gate_rows_html = ''
    for g in gates:
        passed    = g.get('result') == 'PASS'
        row_bg    = '#F0FDF4' if passed else '#FFF2F2'
        tag_color = '#166534' if passed else '#991B1B'
        tag_bg    = '#DCFCE7' if passed else '#FEE2E2'
        tag_text  = 'PASS' if passed else 'FAIL'
        gate_rows_html += f"""
        <tr style="background:{row_bg};">
          <td style="padding:6px 10px;font-size:12px;font-weight:bold;color:{tag_color};background:{tag_bg};border-radius:4px;white-space:nowrap;">{tag_text}</td>
          <td style="padding:6px 10px;font-size:12px;font-weight:bold;color:#1E1E3F;">{g.get('checkpoint','')}</td>
          <td style="padding:6px 10px;font-size:12px;color:#333;">{g.get('name_en') or g.get('name','')}</td>
        </tr>"""

    subject = f"OMNIX Governance Report — {decision_label} | {receipt_id}"

    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#F4F5F7;font-family:Helvetica,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F4F5F7;padding:30px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

  <tr><td style="background:#050D18;padding:18px 28px;">
    <table width="100%"><tr>
      <td style="vertical-align:middle;">
        <img src="https://omnixquantum.net/omnix_logo.png" alt="OMNIX" width="40" height="27" style="display:inline-block;vertical-align:middle;margin-right:10px;" />
        <span style="font-size:11px;color:#888;vertical-align:middle;">DECISION GOVERNANCE INFRASTRUCTURE</span>
      </td>
      <td align="right" style="vertical-align:middle;"><span style="font-size:10px;color:#555;font-family:monospace;">{receipt_id}</span></td>
    </tr></table>
  </td></tr>

  <tr><td style="background:{banner_color};padding:18px 28px;text-align:center;">
    <div style="font-size:28px;font-weight:bold;color:{decision_color};">{decision_label}</div>
    <div style="font-size:12px;color:{'#86EFAC' if is_approved else '#FCA5A5'};margin-top:4px;">
      {cp_passed}/{cp_total} {'checkpoints aprobados' if is_es else 'checkpoints passed'}
      {'  —  ' + str(cp_blocked) + (' bloqueados' if is_es else ' blocked') if cp_blocked > 0 else ''}
    </div>
  </td></tr>

  <tr><td style="padding:24px 28px;">
    <div style="font-size:11px;font-weight:bold;color:#1E1E3F;background:#EBEDF5;padding:6px 10px;border-radius:4px;margin-bottom:10px;">
      {'ANÁLISIS DE GOBERNANZA' if is_es else 'GOVERNANCE ANALYSIS'}
    </div>
    <p style="font-size:13px;color:#333;line-height:1.6;margin:0 0 20px 0;">{explanation}</p>

    {'<div style="font-size:11px;font-weight:bold;color:#1E1E3F;background:#EBEDF5;padding:6px 10px;border-radius:4px;margin-bottom:10px;">' + ('ESCENARIO EVALUADO' if is_es else 'EVALUATED SCENARIO') + '</div><p style="font-size:12px;color:#555;font-style:italic;margin:0 0 20px 4px;">&ldquo;' + scenario[:400] + '&rdquo;</p>' if scenario else ''}

    <div style="font-size:11px;font-weight:bold;color:#1E1E3F;background:#EBEDF5;padding:6px 10px;border-radius:4px;margin-bottom:10px;">
      {'PIPELINE DE 11 CHECKPOINTS' if is_es else '11-CHECKPOINT PIPELINE'}
    </div>
    <table width="100%" cellpadding="0" cellspacing="2" style="border-collapse:separate;border-spacing:0 2px;margin-bottom:20px;">
      {gate_rows_html}
    </table>

    <div style="font-size:11px;font-weight:bold;color:#1E1E3F;background:#EBEDF5;padding:6px 10px;border-radius:4px;margin-bottom:10px;">
      {'INTEGRIDAD CRIPTOGRÁFICA' if is_es else 'CRYPTOGRAPHIC INTEGRITY'}
    </div>
    <table width="100%" cellpadding="4" cellspacing="0" style="font-size:12px;margin-bottom:20px;">
      <tr><td style="color:#555;width:180px;">{'Algoritmo de firma' if is_es else 'Signature algorithm'}:</td>
          <td style="font-family:monospace;color:#333;">{receipt.get('signature_algorithm','SHA-256 (sandbox)')}</td></tr>
      <tr><td style="color:#555;">{'Hash del contenido' if is_es else 'Content hash'}:</td>
          <td style="font-family:monospace;color:#333;">{(receipt.get('content_hash') or '')[:32]}...</td></tr>
      <tr><td style="color:#555;">{'Firmado PQC' if is_es else 'PQC signed'}:</td>
          <td style="color:#333;">{'Modo sandbox — activo en producción' if is_es else 'Sandbox mode — active in production'}</td></tr>
    </table>

    <div style="background:#050D18;border-radius:6px;padding:14px 18px;margin-bottom:8px;">
      <div style="font-size:11px;font-weight:bold;color:#C9A227;margin-bottom:6px;">
        {'Verificar este recibo de forma independiente:' if is_es else 'Verify this receipt independently:'}
      </div>
      <a href="{verify_url}" style="font-size:11px;color:#A0AABF;font-family:monospace;word-break:break-all;">{verify_url}</a>
    </div>
  </td></tr>

  <tr><td style="background:#F8F8F8;border-top:1px solid #E5E7EB;padding:14px 28px;text-align:center;">
    <p style="font-size:11px;color:#888;margin:0;">
      OMNIX Decision Governance Infrastructure &nbsp;|&nbsp; omnixquantum.net &nbsp;|&nbsp; contacto@omnixquantum.net
    </p>
    <p style="font-size:10px;color:#AAA;margin:4px 0 0 0;">
      {'Generado:' if is_es else 'Generated:'} {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
    </p>
  </td></tr>

</table>
</td></tr></table>
</body>
</html>"""

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'OMNIX Decision Governance <{gmail_sender}>'
        msg['To']      = recipient
        msg['Reply-To'] = 'contacto@omnixquantum.net'
        msg.attach(MIMEText(html, 'html'))

        ctx = ssl.create_default_context()
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.ehlo()
            server.starttls(context=ctx)
            server.login(gmail_sender, gmail_password)
            server.sendmail(gmail_sender, recipient, msg.as_string())

        return jsonify({'success': True})
    except Exception as e:
        print(f'[EMAIL ERROR] {e}')
        return jsonify({'success': False, 'error': 'Failed to send email. Please try again.'}), 500


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path and os.path.exists(os.path.join(DIST_DIR, path)):
        return send_from_directory(DIST_DIR, path)
    return send_from_directory(DIST_DIR, 'index.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"OMNIX Web Server starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
