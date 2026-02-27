"""
OMNIX Governance API — External Signal Evaluation Endpoint.

POST /api/governance/evaluate         — Submit normalized signals, receive PQC-signed receipt.
GET  /api/governance/schema           — Signal schema documentation (public).
GET  /api/governance/receipts         — Client's own receipts (authenticated).
POST /api/governance/admin/clients    — Create B2B client (admin only).
GET  /api/governance/admin/clients    — List all B2B clients (admin only).
DELETE /api/governance/admin/clients/<client_id> — Deactivate client (admin only).
POST /api/governance/admin/clients/<client_id>/rotate — Rotate API key (admin only).

ADR-028: External Signal Evaluation API
"""

import json
import logging
import os
import sys
import time
import uuid
from collections import defaultdict

import psycopg2
import psycopg2.extras
from flask import Blueprint, jsonify, request

try:
    from cryptography.fernet import Fernet
    _FERNET_AVAILABLE = True
except ImportError:
    _FERNET_AVAILABLE = False

from .auth_rbac import (
    authenticate_client,
    create_client,
    deactivate_client,
    list_clients,
    reactivate_client,
    rotate_api_key,
    update_last_seen,
)

logger = logging.getLogger(__name__)

governance_bp = Blueprint('governance', __name__)

_rate_limit_store: dict = defaultdict(list)
_RATE_LIMIT_WINDOW = 60
_RATE_LIMIT_MAX = 10

_ENGINE_AVAILABLE = False
_GovernanceEvaluationEngine = None
_DecisionReceiptEngine = None


# ── HELPERS ──────────────────────────────────────────────────────────────────

def _encrypt_payload(data: str) -> str | None:
    """Encrypt string payload using Fernet (AES-128-CBC + HMAC-SHA256)."""
    key = os.environ.get("PAYLOAD_ENCRYPTION_KEY")
    if not key or not _FERNET_AVAILABLE:
        return None
    try:
        f = Fernet(key.encode() if isinstance(key, str) else key)
        return f.encrypt(data.encode()).decode()
    except Exception as e:
        logger.warning(f"Payload encryption failed: {e}")
        return None


def _load_engine():
    global _ENGINE_AVAILABLE, _GovernanceEvaluationEngine, _DecisionReceiptEngine
    if _ENGINE_AVAILABLE:
        return True
    try:
        import importlib.util
        _root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        evaluator_path = os.path.join(_root, "omnix_core", "governance", "external_evaluator.py")
        spec_ev = importlib.util.spec_from_file_location("_omnix_gov_evaluator", evaluator_path)
        mod_ev = importlib.util.module_from_spec(spec_ev)
        sys.modules['_omnix_gov_evaluator'] = mod_ev
        spec_ev.loader.exec_module(mod_ev)
        _GovernanceEvaluationEngine = mod_ev.GovernanceEvaluationEngine

        receipt_path = os.path.join(_root, "omnix_core", "evidence", "decision_receipt.py")
        spec_rc = importlib.util.spec_from_file_location("_omnix_gov_receipt", receipt_path)
        mod_rc = importlib.util.module_from_spec(spec_rc)
        sys.modules['_omnix_gov_receipt'] = mod_rc
        spec_rc.loader.exec_module(mod_rc)
        _DecisionReceiptEngine = mod_rc.DecisionReceiptEngine

        _ENGINE_AVAILABLE = True
        logger.info("GovernanceEvaluationEngine + DecisionReceiptEngine loaded via importlib")
        return True
    except Exception as e:
        logger.error(f"Failed to load governance engine: {e}")
        return False


def _is_rate_limited(client_ip: str) -> bool:
    now = time.time()
    window_start = now - _RATE_LIMIT_WINDOW
    _rate_limit_store[client_ip] = [ts for ts in _rate_limit_store[client_ip] if ts > window_start]
    if len(_rate_limit_store[client_ip]) >= _RATE_LIMIT_MAX:
        return True
    _rate_limit_store[client_ip].append(now)
    return False


def _get_db_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def _require_auth(require_admin: bool = False):
    """
    Authenticate request via X-API-Key header.
    Returns (client_dict, None) on success or (None, error_response) on failure.
    """
    api_key = request.headers.get("X-API-Key", "")
    client = authenticate_client(api_key)
    if client is None:
        logger.warning(f"Unauthorized governance attempt from {request.remote_addr or 'unknown'}")
        return None, (jsonify({"error": "Unauthorized — provide a valid X-API-Key", "status": 401}), 401)
    if require_admin and client.get("role") != "admin":
        return None, (jsonify({"error": "Forbidden — admin role required", "status": 403}), 403)
    return client, None


# ── PUBLIC ENDPOINT ───────────────────────────────────────────────────────────

@governance_bp.route('/api/governance/schema', methods=['GET'])
def api_governance_schema():
    """Public endpoint — returns signal schema and checkpoint documentation."""
    if not _load_engine():
        return jsonify({'error': 'Governance engine not available', 'status': 503}), 503

    schema = _GovernanceEvaluationEngine.get_signal_schema()
    return jsonify({
        'schema': schema,
        'endpoint': 'POST /api/governance/evaluate',
        'auth': 'X-API-Key header required — contact OMNIX to obtain a client API key',
        'rate_limit': f'{_RATE_LIMIT_MAX} requests per {_RATE_LIMIT_WINDOW}s per IP',
        'documentation': 'docs/reference/adr/ADR-028-external-signal-evaluation-api.md',
        'verifiable_at': 'https://omnibotgenesis-production.up.railway.app/verify',
    })


# ── EVALUATE ENDPOINT ─────────────────────────────────────────────────────────

@governance_bp.route('/api/governance/evaluate', methods=['POST'])
def api_governance_evaluate():
    """
    Evaluate external signals through OMNIX 6-checkpoint governance pipeline.
    Returns a PQC-signed governance receipt.
    Requires valid X-API-Key (RBAC authenticated).
    """
    client, err = _require_auth()
    if err:
        return err

    client_id = client["client_id"]
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown').split(',')[0].strip()

    # Rate limit per IP
    if _is_rate_limited(client_ip):
        ref_id = str(uuid.uuid4())[:8]
        logger.warning(f"Rate limit hit: governance/evaluate from {client_ip} client={client_id} ref={ref_id}")
        return jsonify({
            'error': f'Rate limit exceeded — {_RATE_LIMIT_MAX} requests per minute',
            'status': 429,
            'reference': ref_id,
            'retry_after_seconds': _RATE_LIMIT_WINDOW,
        }), 429

    if not request.is_json:
        return jsonify({'error': 'Request must be Content-Type: application/json', 'status': 400}), 400

    try:
        body = request.get_json(force=True)
    except Exception:
        return jsonify({'error': 'Invalid JSON body', 'status': 400}), 400

    if not body or 'signals' not in body:
        return jsonify({
            'error': "Request body must include a 'signals' object. See GET /api/governance/schema.",
            'status': 400,
        }), 400

    if not _load_engine():
        return jsonify({'error': 'Governance engine temporarily unavailable', 'status': 503}), 503

    signals = body.get('signals', {})
    is_valid, error_msg = _GovernanceEvaluationEngine.validate_signals(signals)
    if not is_valid:
        return jsonify({
            'error': f'Invalid signals: {error_msg}',
            'status': 400,
            'hint': 'See GET /api/governance/schema for required fields and value ranges.',
        }), 400

    asset = str(body.get('asset', 'UNKNOWN'))[:64]
    domain = str(body.get('domain', 'generic'))[:32]
    metadata = body.get('metadata', {})
    if not isinstance(metadata, dict):
        metadata = {}

    try:
        engine = _GovernanceEvaluationEngine()
        evaluation = engine.evaluate(signals=signals, asset=asset, domain=domain, metadata=metadata)
    except Exception as e:
        ref_id = str(uuid.uuid4())[:8]
        logger.error(f"Governance evaluation error ref={ref_id}: {e}")
        return jsonify({'error': 'Internal evaluation error', 'status': 500, 'reference': ref_id}), 500

    encrypted_payload = _encrypt_payload(json.dumps(signals, sort_keys=True))

    try:
        receipt_engine = _DecisionReceiptEngine()
        prev_hash = receipt_engine.get_last_hash()
        decision_payload = {
            'symbol': asset,
            'asset': asset,
            'decision': evaluation['decision'],
            'decision_trace': evaluation['decision_trace'],
            'veto_chain': evaluation['veto_chain'],
            'policy_version': os.environ.get('OMNIX_VERSION', '6.5.4e'),
            'domain': domain,
            'external_evaluation': True,
            'checkpoints_total': evaluation['checkpoints_total'],
            'checkpoints_passed': evaluation['checkpoints_passed'],
            'client_id': client_id,
            'encrypted_payload': encrypted_payload,
        }
        receipt = receipt_engine.generate_receipt(decision_payload, prev_hash=prev_hash)
        receipt['client_id'] = client_id
        receipt['encrypted_payload'] = encrypted_payload
        receipt_engine.store_receipt(receipt)
    except Exception as e:
        ref_id = str(uuid.uuid4())[:8]
        logger.error(f"Receipt generation error ref={ref_id}: {e}")
        receipt = {
            'receipt_id': f'OMNIX-ERR-{ref_id}',
            'signature': None,
            'signature_algorithm': 'NONE',
            'content_hash': None,
            'public_key': None,
            'timestamp': None,
            'prev_hash': '',
        }

    # Update last_seen (best-effort)
    update_last_seen(client_id)

    response = {
        'receipt_id': receipt.get('receipt_id'),
        'timestamp': receipt.get('timestamp'),
        'client_id': client_id,
        'asset': asset,
        'domain': domain,
        'decision': evaluation['decision'],
        'checkpoints_total': evaluation['checkpoints_total'],
        'checkpoints_passed': evaluation['checkpoints_passed'],
        'checkpoints_blocked': evaluation['checkpoints_blocked'],
        'gate_results': evaluation['gate_results'],
        'veto_chain': evaluation['veto_chain'],
        'decision_trace': evaluation['decision_trace'],
        'scores': evaluation['scores'],
        'content_hash': receipt.get('content_hash'),
        'signature': receipt.get('signature'),
        'signature_algorithm': receipt.get('signature_algorithm', 'NONE'),
        'pqc_signed': receipt.get('signature') is not None,
        'payload_encrypted': encrypted_payload is not None,
        'verifiable_at': 'https://omnibotgenesis-production.up.railway.app/verify',
        'policy_version': receipt.get('policy_version', os.environ.get('OMNIX_VERSION', '6.5.4e')),
    }

    logger.info(
        f"[GOVERNANCE] evaluate: client={client_id} asset={asset} domain={domain} "
        f"decision={evaluation['decision']} "
        f"passed={evaluation['checkpoints_passed']}/{evaluation['checkpoints_total']} "
        f"receipt={receipt.get('receipt_id')} encrypted={encrypted_payload is not None} ip={client_ip}"
    )
    return jsonify(response), 200


# ── CLIENT RECEIPTS ENDPOINT ──────────────────────────────────────────────────

@governance_bp.route('/api/governance/receipts', methods=['GET'])
def api_governance_receipts():
    """
    Returns the authenticated client's own governance receipts.
    Isolation guaranteed: WHERE client_id = authenticated client's ID.
    Query params: limit (default 20, max 100), offset (default 0), decision (optional filter).
    """
    client, err = _require_auth()
    if err:
        return err

    client_id = client["client_id"]
    try:
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = max(int(request.args.get('offset', 0)), 0)
    except ValueError:
        return jsonify({'error': 'limit and offset must be integers', 'status': 400}), 400

    decision_filter = request.args.get('decision')

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        where_clause = "WHERE client_id = %s"
        params = [client_id]

        if decision_filter:
            where_clause += " AND decision = %s"
            params.append(decision_filter.upper())

        cur.execute(
            f"""
            SELECT receipt_id, timestamp_utc, asset, decision, veto_chain, created_at
            FROM decision_receipts
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            params + [limit, offset],
        )
        receipts = [dict(r) for r in cur.fetchall()]

        cur.execute(f"SELECT COUNT(*) as cnt FROM decision_receipts {where_clause}", params)
        total = cur.fetchone()["cnt"]

        cur.close()
        conn.close()

        return jsonify({
            'client_id': client_id,
            'total': total,
            'limit': limit,
            'offset': offset,
            'receipts': receipts,
            'verifiable_at': 'https://omnibotgenesis-production.up.railway.app/verify',
        }), 200

    except Exception as e:
        logger.error(f"Error fetching receipts for client={client_id}: {e}")
        return jsonify({'error': 'Database error', 'status': 500}), 500


# ── ADMIN ENDPOINTS ───────────────────────────────────────────────────────────

@governance_bp.route('/api/governance/admin/clients', methods=['POST'])
def admin_create_client():
    """Create a new B2B client. Admin only. Returns plaintext API key — shown once."""
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    if not request.is_json:
        return jsonify({'error': 'Request must be JSON', 'status': 400}), 400

    body = request.get_json(force=True) or {}
    new_client_id = str(body.get('client_id', '')).strip()[:64]
    name = str(body.get('name', '')).strip()[:128]
    email = str(body.get('email', '')).strip()[:256] or None
    role = str(body.get('role', 'standard')).strip()

    if not new_client_id:
        return jsonify({'error': "'client_id' is required", 'status': 400}), 400
    if role not in ('standard', 'admin'):
        return jsonify({'error': "role must be 'standard' or 'admin'", 'status': 400}), 400

    try:
        api_key = create_client(client_id=new_client_id, name=name, email=email, role=role)
        logger.info(f"[ADMIN] created B2B client: {new_client_id} role={role} by admin={client['client_id']}")
        return jsonify({
            'client_id': new_client_id,
            'name': name,
            'role': role,
            'api_key': api_key,
            'message': 'Store this API key securely — it is shown only once and never stored in plaintext.',
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e), 'status': 409}), 409


@governance_bp.route('/api/governance/admin/clients', methods=['GET'])
def admin_list_clients():
    """List all B2B clients. Admin only. Never returns api_key_hash."""
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    try:
        clients = list_clients()
        # Convert datetime objects to ISO strings for JSON serialization
        for c in clients:
            for field in ('created_at', 'last_seen_at'):
                if c.get(field):
                    c[field] = c[field].isoformat()
        return jsonify({'clients': clients, 'total': len(clients)}), 200
    except Exception as e:
        logger.error(f"Admin list_clients error: {e}")
        return jsonify({'error': 'Database error', 'status': 500}), 500


@governance_bp.route('/api/governance/admin/clients/<string:target_client_id>', methods=['DELETE'])
def admin_deactivate_client(target_client_id: str):
    """Deactivate a B2B client (soft delete). Admin only."""
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    if target_client_id == client['client_id']:
        return jsonify({'error': 'Cannot deactivate your own client', 'status': 400}), 400

    found = deactivate_client(target_client_id)
    if not found:
        return jsonify({'error': f"client_id '{target_client_id}' not found", 'status': 404}), 404

    logger.info(f"[ADMIN] deactivated client: {target_client_id} by admin={client['client_id']}")
    return jsonify({'client_id': target_client_id, 'status': 'deactivated'}), 200


@governance_bp.route('/api/governance/admin/clients/<string:target_client_id>/reactivate', methods=['POST'])
def admin_reactivate_client(target_client_id: str):
    """Reactivate a deactivated B2B client. Admin only."""
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    found = reactivate_client(target_client_id)
    if not found:
        return jsonify({'error': f"client_id '{target_client_id}' not found", 'status': 404}), 404

    logger.info(f"[ADMIN] reactivated client: {target_client_id} by admin={client['client_id']}")
    return jsonify({'client_id': target_client_id, 'status': 'active'}), 200


@governance_bp.route('/api/governance/admin/clients/<string:target_client_id>/rotate', methods=['POST'])
def admin_rotate_key(target_client_id: str):
    """Rotate API key for a client. Admin only. Returns new key — shown once."""
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    try:
        new_key = rotate_api_key(target_client_id)
        logger.info(f"[ADMIN] rotated key for client: {target_client_id} by admin={client['client_id']}")
        return jsonify({
            'client_id': target_client_id,
            'api_key': new_key,
            'message': 'New API key generated. Previous key is now invalid. Store this key securely — shown once only.',
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e), 'status': 404}), 404
