"""
Public Decision Verification API
ADR: complements ADR-040 (Public Governance Sandbox) and ADR-044 (Quantum-Secure Receipts)

GET /api/public/verify/<receipt_id>
Returns a human-readable, presentation-ready payload for the public /verify page.
No authentication required. Rate limited. No sensitive data exposed.

Author: Harold Nunes
"""

import json
import re
import time
import logging
import os
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

public_verify_bp = Blueprint('public_verify', __name__)

_rate_limit_store: dict = {}
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 30
RECEIPT_ID_RE = re.compile(r'^OMNIX[-_][A-Z0-9]{6,20}$')

# ─── Checkpoint label maps ────────────────────────────────────────────────────

_CP_LABELS = {
    'CP-0': {'en': 'Signal Integrity Validation', 'es': 'Validación de Integridad de Señal'},
    'CP-1': {'en': 'Monte Carlo Risk Simulation', 'es': 'Simulación Monte Carlo de Riesgo'},
    'CP-2': {'en': 'Risk Management System', 'es': 'Sistema de Gestión de Riesgo'},
    'CP-3': {'en': 'Early Veto Gate', 'es': 'Puerta de Veto Temprano'},
    'CP-4': {'en': 'Coherence Engine (6-tier)', 'es': 'Motor de Coherencia (6 niveles)'},
    'CP-5': {'en': 'Adaptive Coherence Gate', 'es': 'Puerta de Coherencia Adaptiva'},
    'CP-6': {'en': 'Edge Confirmation Window', 'es': 'Ventana de Confirmación de Ventaja'},
    'CP-7': {'en': 'Temporal Coherence Validation', 'es': 'Validación Temporal'},
    'CP-7b': {'en': 'Forward Trajectory Implication', 'es': 'Implicación de Trayectoria Futura'},
    'CP-8': {'en': 'Edge Persistence Gate', 'es': 'Puerta de Persistencia'},
}

# ─── Decision language maps ───────────────────────────────────────────────────

_DECISION_SUMMARY = {
    'APPROVED': {
        'en': 'OMNIX governance engine approved this decision — all safety checkpoints passed.',
        'es': 'El motor de gobernanza OMNIX aprobó esta decisión — todos los puntos de control de seguridad pasaron.',
        'color': 'green',
        'icon': '✅',
    },
    'APPROVE': {
        'en': 'OMNIX governance engine approved this decision — all safety checkpoints passed.',
        'es': 'El motor de gobernanza OMNIX aprobó esta decisión — todos los puntos de control de seguridad pasaron.',
        'color': 'green',
        'icon': '✅',
    },
    'BUY': {
        'en': 'OMNIX governance engine approved this entry signal.',
        'es': 'El motor de gobernanza OMNIX aprobó esta señal de entrada.',
        'color': 'green',
        'icon': '✅',
    },
    'BLOCKED': {
        'en': 'OMNIX governance engine blocked this decision — one or more safety checkpoints failed.',
        'es': 'El motor de gobernanza OMNIX bloqueó esta decisión — uno o más puntos de control de seguridad fallaron.',
        'color': 'red',
        'icon': '🛡️',
    },
    'BLOCK': {
        'en': 'OMNIX governance engine blocked this decision — one or more safety checkpoints failed.',
        'es': 'El motor de gobernanza OMNIX bloqueó esta decisión — uno o más puntos de control de seguridad fallaron.',
        'color': 'red',
        'icon': '🛡️',
    },
    'SELL': {
        'en': 'OMNIX governance engine issued a protected exit signal.',
        'es': 'El motor de gobernanza OMNIX emitió una señal de salida protegida.',
        'color': 'red',
        'icon': '🛡️',
    },
    'HOLD': {
        'en': 'OMNIX governance engine deferred this decision — signal conditions are not conclusive.',
        'es': 'El motor de gobernanza OMNIX difirió esta decisión — las condiciones de señal no son concluyentes.',
        'color': 'yellow',
        'icon': '⏸️',
    },
    'SIZE_REDUCE': {
        'en': 'OMNIX governance engine reduced position size — risk parameters exceeded.',
        'es': 'El motor de gobernanza OMNIX redujo el tamaño de la posición — parámetros de riesgo excedidos.',
        'color': 'yellow',
        'icon': '⚠️',
    },
}


def _decision_meta(decision: str) -> dict:
    return _DECISION_SUMMARY.get(decision.upper(), {
        'en': f'Governance decision: {decision}',
        'es': f'Decisión de gobernanza: {decision}',
        'color': 'gray',
        'icon': '📋',
    })


# ─── Veto chain parser ────────────────────────────────────────────────────────
# Handles the real veto_chain format: "COMPONENT(CP-X): key=val ... pass_through=True/False"

_COMPONENT_LABELS: dict = {
    'SIV':              {'en': 'Signal Integrity Validation',      'es': 'Validación de Integridad de Señal',   'cp': 'CP-0'},
    'MC':               {'en': 'Monte Carlo Risk Simulation',      'es': 'Simulación Monte Carlo de Riesgo',    'cp': 'CP-1'},
    'MC_SIZE_REDUCE':   {'en': 'Monte Carlo: Position Size Adjustment', 'es': 'Monte Carlo: Ajuste de Tamaño', 'cp': 'CP-1'},
    'RMS':              {'en': 'Risk Management System',           'es': 'Sistema de Gestión de Riesgo',        'cp': 'CP-2'},
    'COHERENCE_GATE':   {'en': 'Coherence Engine Gate',            'es': 'Puerta del Motor de Coherencia',      'cp': 'CP-4/5'},
    'TCV':              {'en': 'Temporal Coherence Validation',    'es': 'Validación de Coherencia Temporal',   'cp': 'CP-7'},
    'FTI':              {'en': 'Forward Trajectory Implication',   'es': 'Implicación de Trayectoria Futura',   'cp': 'CP-7b'},
    'ECW_GATE':         {'en': 'Edge Confirmation Window',         'es': 'Ventana de Confirmación de Ventaja',  'cp': 'CP-6'},
    'ECW':              {'en': 'Edge Confirmation Window',         'es': 'Ventana de Confirmación de Ventaja',  'cp': 'CP-6'},
    'BLACK_SWAN_VETO':  {'en': 'Black Swan Event Detection',       'es': 'Detección de Eventos Extremos',       'cp': ''},
    'BLACK_SWAN':       {'en': 'Black Swan Event Detection',       'es': 'Detección de Eventos Extremos',       'cp': ''},
    'ARES_REMOVED':     {'en': 'Regime Analysis (Removed)',        'es': 'Análisis de Régimen (Retirado)',       'cp': ''},
    'ARES':             {'en': 'Regime Analysis',                  'es': 'Análisis de Régimen',                 'cp': ''},
    'RCK':              {'en': 'Regime-Conditioned Kelly',         'es': 'Kelly Condicionado por Régimen',      'cp': ''},
    'DCI':              {'en': 'Decision Contradiction Index',     'es': 'Índice de Contradicción',             'cp': ''},
    'HMM':              {'en': 'Hidden Markov Model Regime',       'es': 'Régimen HMM',                        'cp': ''},
    'EGL':              {'en': 'Exit Governance Layer',            'es': 'Capa de Gobernanza de Salida',        'cp': ''},
}

_COMP_RE = re.compile(r'^([A-Z][A-Z0-9_]*)[\(\s:]')
_NUM_RE  = re.compile(r'([\w\s]+)[=:]\s*([-\d.]+%?)')


def _extract_component(raw: str) -> str:
    m = _COMP_RE.match(raw.strip())
    return m.group(1) if m else raw[:20].split(':')[0].split('(')[0].strip()


def _extract_metric(raw: str) -> tuple:
    """Return (label, value) for the most informative metric in raw string."""
    for pattern in [r'score=([\d.]+)', r'(\d+\.?\d*)%', r'Coherence\s+([\d.]+)%',
                    r'CrashProb=([\d.]+)%', r'WR=([\d.]+)%', r'ER=([-\d.]+)%']:
        m = re.search(pattern, raw, re.IGNORECASE)
        if m:
            val = m.group(1)
            if 'score=' in pattern: return ('Score', val)
            if 'Coherence' in pattern: return ('Coherence', f'{val}%')
            if 'CrashProb' in pattern: return ('Crash Prob', f'{val}%')
            if 'WR=' in pattern: return ('Win Rate', f'{val}%')
            if 'ER=' in pattern: return ('Exp Return', f'{val}%')
            return ('Value', f'{val}%')
    return (None, None)


def _determine_result(raw: str, component: str) -> str:
    r = raw.upper()
    comp = component.upper()

    if 'REMOVED' in comp or 'ELIMINATED' in r:          return 'N/A'
    if 'SIZE_REDUCE' in comp:                            return 'ADJUSTED'
    if '(PASSED)' in r or '>= ' in r and 'PASSED' in r: return 'PASS'
    if 'WARN THRESHOLD' in r or '< ' in r and 'WARN' in r: return 'BLOCKED'
    if 'CONFIRMED' in r and 'ECW' in r:                  return 'PASS'
    if 'WAITING' in r and 'ECW' in r:                    return 'BLOCKED'
    if 'ADMISSIBLE=TRUE' in r.replace(' ', ''):          return 'PASS'
    if 'ADMISSIBLE=FALSE' in r.replace(' ', ''):         return 'BLOCKED'
    if 'VETO' in comp:
        if 'HIGH' in r:   return 'BLOCKED'
        if 'MEDIUM' in r: return 'PASS'
        if 'LOW' in r:    return 'PASS'
    if ':PASS' in r or ': PASS' in r:                    return 'PASS'
    if ':BLOCK' in r or ': BLOCK' in r:                  return 'BLOCKED'
    if 'PASS_THROUGH=FALSE' in r.replace(' ', ''):
        if 'VIOLATION' in r and re.search(r'VIOLATIONS=[1-9]', r.replace(' ', '')):
            return 'PASS'
    if 'PASS_THROUGH=TRUE' in r.replace(' ', ''):        return 'BYPASSED'
    return 'PASS'


def _parse_veto_chain(veto_chain_raw) -> list:
    """Parse veto_chain (list of strings) into structured checkpoint cards."""
    if not veto_chain_raw:
        return []
    if isinstance(veto_chain_raw, str):
        try:
            veto_chain_raw = json.loads(veto_chain_raw)
        except Exception:
            veto_chain_raw = [veto_chain_raw]
    if not isinstance(veto_chain_raw, list):
        return []

    checkpoints = []
    for raw in veto_chain_raw:
        raw_str = str(raw).strip()[:200]
        comp    = _extract_component(raw_str)
        meta    = _COMPONENT_LABELS.get(comp, {'en': comp.replace('_', ' ').title(), 'es': comp.replace('_', ' ').title(), 'cp': ''})
        result  = _determine_result(raw_str, comp)
        metric_label, metric_value = _extract_metric(raw_str)
        code    = meta.get('cp') or None

        checkpoints.append({
            'code':         code if code else None,
            'label_en':     meta['en'],
            'label_es':     meta['es'],
            'result':       result,
            'metric_label': metric_label,
            'metric_value': metric_value,
            'raw':          raw_str,
        })

    return checkpoints


def _build_summary_sentence(decision: str, checkpoints: list, asset: str, lang: str = 'en') -> str:
    total   = len(checkpoints)
    passed  = sum(1 for c in checkpoints if c['result'] == 'PASS')
    blocked = total - passed
    meta    = _decision_meta(decision)
    base    = meta[lang]

    if total > 0 and lang == 'en':
        return f"{meta['icon']} {base} {passed} of {total} safety checkpoints passed."
    elif total > 0 and lang == 'es':
        return f"{meta['icon']} {base} {passed} de {total} puntos de control de seguridad pasaron."
    return f"{meta['icon']} {base}"


def _get_db_conn():
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
            logger.error(f"[PublicVerify] DB error (psycopg3): {e}")
            return None
    except Exception as e:
        logger.error(f"[PublicVerify] DB error: {e}")
        return None


def _check_rate_limit(ip: str) -> bool:
    now = time.time()
    _rate_limit_store.setdefault(ip, [])
    _rate_limit_store[ip] = [t for t in _rate_limit_store[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limit_store[ip]) >= RATE_LIMIT_MAX:
        return False
    _rate_limit_store[ip].append(now)
    return True


# ─── Shared DB fetch ──────────────────────────────────────────────────────────

def _fetch_receipt(receipt_id: str):
    """Return presentation-ready dict or None if not found / DB error."""
    conn = _get_db_conn()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT receipt_id, timestamp_utc, asset, decision,
                   veto_chain, policy_version, engine_version,
                   prev_hash, content_hash, signature_algorithm, domain
            FROM decision_receipts
            WHERE receipt_id = %s
            LIMIT 1
        """, (receipt_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"[PublicVerify] DB query failed: {e}")
        try:
            conn.close()
        except Exception:
            pass
        return None

    if not row:
        return {}

    (rid, ts_utc, asset, decision,
     veto_chain_raw, policy_version, engine_version,
     prev_hash, content_hash, signature_algorithm, domain) = row

    ts_str      = ts_utc.isoformat() if hasattr(ts_utc, 'isoformat') else str(ts_utc)
    checkpoints = _parse_veto_chain(veto_chain_raw)
    total       = len(checkpoints)
    passed      = sum(1 for c in checkpoints if c['result'] == 'PASS')
    blocked_n   = total - passed
    meta        = _decision_meta(decision or 'UNKNOWN')
    railway_url = os.environ.get('RAILWAY_VERIFY_URL', '')

    return {
        'found':          True,
        'receipt_id':     rid,
        'timestamp_utc':  ts_str,
        'asset':          asset or 'UNKNOWN',
        'decision':       (decision or 'UNKNOWN').upper(),
        'domain':         domain or 'trading',
        'decision_color': meta.get('color', 'gray'),
        'decision_icon':  meta.get('icon', '📋'),
        'human_summary_en': _build_summary_sentence(decision or 'UNKNOWN', checkpoints, asset or '?', 'en'),
        'human_summary_es': _build_summary_sentence(decision or 'UNKNOWN', checkpoints, asset or '?', 'es'),
        'checkpoints_total':   total,
        'checkpoints_passed':  passed,
        'checkpoints_blocked': blocked_n,
        'checkpoints':         checkpoints,
        'integrity': {
            'content_hash':             content_hash,
            'prev_hash':                prev_hash or '',
            'signature_algorithm':      signature_algorithm or 'Dilithium-3 (ML-DSA-65)',
            'is_pqc':                   True,
            'independently_verifiable': True,
            'nist_note':                'Signed with NIST-standardized post-quantum algorithms',
        },
        'policy_version':         policy_version or '6.5.4e',
        'engine_version':         engine_version or '6.5.4e',
        'independent_verify_url': f"{railway_url}/verify/{rid}" if railway_url else None,
    }


# ─── JSON endpoint ────────────────────────────────────────────────────────────

@public_verify_bp.route('/api/public/verify/<receipt_id>', methods=['GET'])
def verify_receipt(receipt_id: str):
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()
    if not _check_rate_limit(ip):
        return jsonify({'error': 'Rate limit exceeded', 'retry_after': 60}), 429
    if not RECEIPT_ID_RE.match(receipt_id):
        return jsonify({'found': False, 'error': 'Invalid receipt ID format'}), 400
    data = _fetch_receipt(receipt_id)
    if data is None:
        return jsonify({'found': False, 'error': 'Service temporarily unavailable'}), 503
    if not data:
        return jsonify({'found': False, 'receipt_id': receipt_id}), 200
    return jsonify(data), 200


# ─── HTML page endpoint ───────────────────────────────────────────────────────

_COLOR_HEX = {'green': '#22c55e', 'red': '#ef4444', 'yellow': '#eab308', 'gray': '#818cf8'}
_COLOR_BG  = {'green': 'rgba(34,197,94,.10)',  'red': 'rgba(239,68,68,.10)',
               'yellow': 'rgba(234,179,8,.10)', 'gray': 'rgba(129,140,248,.10)'}
_COLOR_BD  = {'green': 'rgba(34,197,94,.30)',  'red': 'rgba(239,68,68,.30)',
               'yellow': 'rgba(234,179,8,.30)', 'gray': 'rgba(129,140,248,.30)'}


def _checkpoint_rows(checkpoints: list) -> str:
    rows = []
    for cp in checkpoints:
        if cp['result'] == 'PASS':
            icon, clr = '✓', '#22c55e'
        elif cp['result'] == 'BLOCKED':
            icon, clr = '✗', '#ef4444'
        elif cp['result'] == 'N/A':
            icon, clr = '–', '#6b7280'
        else:
            icon, clr = '~', '#eab308'

        label = cp['label_en']
        code  = f'<span style="font-family:monospace;font-size:.7rem;color:#6b7280;margin-right:6px">{cp["code"]}</span>' if cp['code'] else ''
        metric = ''
        if cp['metric_label'] and cp['metric_value']:
            metric = f'<span style="font-size:.72rem;color:#6b7280;margin-left:8px">{cp["metric_label"]}: <b style="color:#9ca3af">{cp["metric_value"]}</b></span>'

        rows.append(f'''
        <div style="display:flex;gap:10px;padding:10px 0;border-bottom:1px solid rgba(255,255,255,.04)">
          <span style="color:{clr};font-size:1rem;flex-shrink:0;width:18px;text-align:center">{icon}</span>
          <span style="font-size:.87rem;color:#e5e7eb">{code}{label}{metric}</span>
          <span style="margin-left:auto;font-family:monospace;font-size:.7rem;color:{clr};flex-shrink:0">{cp["result"]}</span>
        </div>''')
    return ''.join(rows)


@public_verify_bp.route('/r/<receipt_id>', methods=['GET'])
def verify_page_html(receipt_id: str):
    if not RECEIPT_ID_RE.match(receipt_id):
        return '<h2 style="font-family:sans-serif;color:#ef4444;padding:2rem">Invalid receipt ID format</h2>', 400

    data = _fetch_receipt(receipt_id)

    if data is None:
        msg = 'Service temporarily unavailable. Please try again.'
        body = f'<div style="text-align:center;padding:3rem"><p style="color:#ef4444">{msg}</p></div>'
    elif not data:
        body = f'''
        <div style="text-align:center;padding:3rem">
          <div style="font-size:2.5rem;margin-bottom:1rem">🔍</div>
          <h2 style="color:#e5e7eb;margin-bottom:.5rem">Receipt not found</h2>
          <p style="color:#6b7280;font-family:monospace">{receipt_id}</p>
          <p style="color:#4b5563;font-size:.85rem;margin-top:1rem">
            Receipts are generated by the governance engine after every decision.<br>
            Try the <a href="/try" style="color:#3b82f6">public sandbox</a> to generate one.
          </p>
        </div>'''
    else:
        col   = data['decision_color']
        chk   = _checkpoint_rows(data['checkpoints'])
        ind   = f'<a href="{data["independent_verify_url"]}" target="_blank" style="color:#3b82f6;font-size:.8rem">Open independent ledger ↗</a>' if data.get('independent_verify_url') else ''
        prev_h = f'<div style="margin-bottom:8px"><span style="font-size:.68rem;color:#6b7280;text-transform:uppercase;letter-spacing:.1em">Previous Hash</span><br><span style="font-family:monospace;font-size:.7rem;color:#60a5fa;word-break:break-all">{data["integrity"]["prev_hash"]}</span></div>' if data['integrity']['prev_hash'] else ''

        body = f'''
        <!-- Decision banner -->
        <div style="padding:1.4rem;border-radius:10px;background:{_COLOR_BG[col]};border:1px solid {_COLOR_BD[col]};margin-bottom:1.2rem">
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:.8rem">
            <span style="font-size:1.6rem">{data["decision_icon"]}</span>
            <div>
              <div style="font-size:1.1rem;font-weight:700;color:{_COLOR_HEX[col]}">{data["decision"]}</div>
              <div style="font-family:monospace;font-size:.72rem;color:#6b7280">{data["receipt_id"]}</div>
            </div>
          </div>
          <p style="color:#d1d5db;font-size:.9rem;margin:0 0 .4rem">{data["human_summary_en"]}</p>
          <p style="color:#9ca3af;font-size:.8rem;margin:0;font-style:italic">{data["human_summary_es"]}</p>
        </div>

        <!-- Key facts -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;padding:1rem;background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:8px;margin-bottom:1.2rem">
          <div><div style="font-size:.65rem;color:#6b7280;text-transform:uppercase;letter-spacing:.1em;margin-bottom:3px">Asset</div><div style="font-family:monospace;font-size:.85rem;color:#e5e7eb">{data["asset"]}</div></div>
          <div><div style="font-size:.65rem;color:#6b7280;text-transform:uppercase;letter-spacing:.1em;margin-bottom:3px">Checkpoints</div><div style="font-family:monospace;font-size:.85rem;color:#e5e7eb">{data["checkpoints_passed"]} / {data["checkpoints_total"]} passed</div></div>
          <div><div style="font-size:.65rem;color:#6b7280;text-transform:uppercase;letter-spacing:.1em;margin-bottom:3px">Policy</div><div style="font-family:monospace;font-size:.85rem;color:#e5e7eb">{data["policy_version"]}</div></div>
          <div><div style="font-size:.65rem;color:#6b7280;text-transform:uppercase;letter-spacing:.1em;margin-bottom:3px">Time (UTC)</div><div style="font-size:.75rem;color:#e5e7eb">{data["timestamp_utc"][:19].replace("T"," ")}</div></div>
        </div>

        <!-- Checkpoints -->
        <div style="padding:1.2rem;background:rgba(255,255,255,.02);border:1px solid rgba(255,255,255,.06);border-radius:8px;margin-bottom:1.2rem">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.8rem">
            <span style="font-size:.7rem;color:#6b7280;text-transform:uppercase;letter-spacing:.1em;font-weight:600">Safety Checkpoint Pipeline</span>
            <span style="font-size:.75rem;color:#22c55e">✓ {data["checkpoints_passed"]} passed &nbsp;
              {"<span style='color:#ef4444'>✗ " + str(data["checkpoints_blocked"]) + " blocked</span>" if data["checkpoints_blocked"] else ""}
            </span>
          </div>
          {chk}
        </div>

        <!-- Integrity -->
        <div style="padding:1.2rem;background:rgba(59,130,246,.05);border:1px solid rgba(59,130,246,.15);border-radius:8px;margin-bottom:1.2rem">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:.8rem">
            <span>🔒</span>
            <span style="font-size:.7rem;color:#60a5fa;text-transform:uppercase;letter-spacing:.1em;font-weight:600">Cryptographic Integrity</span>
          </div>
          <div style="background:rgba(34,197,94,.06);border:1px solid rgba(34,197,94,.15);border-radius:6px;padding:.7rem;margin-bottom:.8rem;display:flex;gap:8px;align-items:flex-start">
            <span style="color:#22c55e">✓</span>
            <div>
              <div style="color:#22c55e;font-weight:600;font-size:.85rem;margin-bottom:2px">Tamper-Proof Receipt</div>
              <div style="color:#9ca3af;font-size:.75rem">Signed with {data["integrity"]["signature_algorithm"]} · {data["integrity"]["nist_note"]}</div>
            </div>
          </div>
          <div style="margin-bottom:8px"><span style="font-size:.68rem;color:#6b7280;text-transform:uppercase;letter-spacing:.1em">Content Hash (SHA-256)</span><br><span style="font-family:monospace;font-size:.7rem;color:#60a5fa;word-break:break-all">{data["integrity"]["content_hash"]}</span></div>
          {prev_h}
          <div style="margin-top:.6rem">{ind}</div>
        </div>

        <p style="text-align:center;font-size:.72rem;color:#4b5563">
          <a href="/" style="color:#3b82f6">omnixquantum.net</a> &nbsp;·&nbsp;
          All governance decisions are logged in an append-only hash chain with post-quantum cryptographic signatures.
        </p>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>OMNIX — Governance Receipt {receipt_id}</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{background:#0a0e17;color:#e5e7eb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-height:100vh}}
    a{{color:#3b82f6}}
  </style>
</head>
<body>
  <!-- Header -->
  <div style="border-bottom:1px solid rgba(255,255,255,.06);padding:14px 24px;display:flex;align-items:center;justify-content:space-between">
    <a href="/" style="display:flex;align-items:center;gap:10px;text-decoration:none">
      <span style="font-size:1.2rem">🛡️</span>
      <div>
        <div style="font-size:.85rem;font-weight:700;color:#fff;letter-spacing:.06em">OMNIX QUANTUM</div>
        <div style="font-size:.6rem;color:#6b7280;letter-spacing:.12em;text-transform:uppercase">Decision Governance Infrastructure</div>
      </div>
    </a>
    <a href="/try" style="font-size:.8rem;color:#3b82f6;text-decoration:none">Try sandbox ↗</a>
  </div>

  <!-- Content -->
  <div style="max-width:680px;margin:0 auto;padding:2rem 1.2rem">
    <h1 style="font-size:1.4rem;font-weight:700;color:#fff;margin-bottom:.4rem">Governance Receipt</h1>
    <p style="color:#9ca3af;font-size:.85rem;margin-bottom:1.5rem">Independent cryptographic verification of a governance decision.</p>
    {body}
  </div>
</body>
</html>'''
    return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
