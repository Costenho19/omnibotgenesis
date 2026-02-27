"""
OMNIX Governance API — External Signal Evaluation Endpoint.

POST /api/governance/evaluate  — Submit normalized signals, receive PQC-signed receipt.
GET  /api/governance/schema    — Signal schema documentation (public).

ADR-028: External Signal Evaluation API
"""

import json
import logging
import os
import sys
import time
import uuid
from collections import defaultdict
from flask import Blueprint, jsonify, request

try:
    from cryptography.fernet import Fernet
    _FERNET_AVAILABLE = True
except ImportError:
    _FERNET_AVAILABLE = False


def _encrypt_payload(data: str) -> str | None:
    """Encrypt a string payload using Fernet (AES-128-CBC + HMAC-SHA256).
    Returns base64-encoded ciphertext or None if key not configured."""
    key = os.environ.get("PAYLOAD_ENCRYPTION_KEY")
    if not key or not _FERNET_AVAILABLE:
        return None
    try:
        f = Fernet(key.encode() if isinstance(key, str) else key)
        return f.encrypt(data.encode()).decode()
    except Exception as e:
        logger_ref = logging.getLogger(__name__)
        logger_ref.warning(f"Payload encryption failed: {e}")
        return None


logger = logging.getLogger(__name__)

governance_bp = Blueprint('governance', __name__)

_rate_limit_store: dict = defaultdict(list)
_RATE_LIMIT_WINDOW = 60
_RATE_LIMIT_MAX = 10

_ENGINE_AVAILABLE = False
_GovernanceEvaluationEngine = None
_DecisionReceiptEngine = None


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
    _rate_limit_store[client_ip] = [
        ts for ts in _rate_limit_store[client_ip] if ts > window_start
    ]
    if len(_rate_limit_store[client_ip]) >= _RATE_LIMIT_MAX:
        return True
    _rate_limit_store[client_ip].append(now)
    return False


@governance_bp.route('/api/governance/schema', methods=['GET'])
def api_governance_schema():
    """Public endpoint — returns signal schema and checkpoint documentation."""
    if not _load_engine():
        return jsonify({
            'error': 'Governance engine not available',
            'status': 503,
            'reference': str(uuid.uuid4())[:8]
        }), 503

    schema = _GovernanceEvaluationEngine.get_signal_schema()
    return jsonify({
        'schema': schema,
        'endpoint': 'POST /api/governance/evaluate',
        'auth': 'X-API-Key header required (when B2B_API_KEY is configured in environment)',
        'rate_limit': f'{_RATE_LIMIT_MAX} requests per {_RATE_LIMIT_WINDOW}s per IP',
        'documentation': 'docs/reference/adr/ADR-028-external-signal-evaluation-api.md',
        'verifiable_at': 'https://omnibotgenesis-production.up.railway.app/verify',
    })


@governance_bp.route('/api/governance/evaluate', methods=['POST'])
def api_governance_evaluate():
    """
    Evaluate external signals through OMNIX 6-checkpoint governance pipeline.
    Returns a PQC-signed governance receipt.
    """
    b2b_key = os.environ.get("B2B_API_KEY")
    if b2b_key:
        provided = request.headers.get("X-API-Key")
        if provided != b2b_key:
            logger.warning(f"Unauthorized governance/evaluate attempt from {request.remote_addr or 'unknown'}")
            return jsonify({"error": "Unauthorized", "status": 401}), 401

    client_id = str(request.headers.get("X-Client-ID", "anonymous"))[:64]
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown').split(',')[0].strip()

    if _is_rate_limited(client_ip):
        ref_id = str(uuid.uuid4())[:8]
        logger.warning(f"Rate limit hit: governance/evaluate from {client_ip} ref={ref_id}")
        return jsonify({
            'error': 'Rate limit exceeded — governance evaluation is limited to '
                     f'{_RATE_LIMIT_MAX} requests per minute',
            'status': 429,
            'reference': ref_id,
            'retry_after_seconds': _RATE_LIMIT_WINDOW
        }), 429

    if not request.is_json:
        return jsonify({
            'error': 'Request must be Content-Type: application/json',
            'status': 400,
            'reference': str(uuid.uuid4())[:8]
        }), 400

    try:
        body = request.get_json(force=True)
    except Exception:
        return jsonify({
            'error': 'Invalid JSON body',
            'status': 400,
            'reference': str(uuid.uuid4())[:8]
        }), 400

    if not body or 'signals' not in body:
        return jsonify({
            'error': "Request body must include a 'signals' object. "
                     "See GET /api/governance/schema for the required format.",
            'status': 400,
            'reference': str(uuid.uuid4())[:8]
        }), 400

    if not _load_engine():
        ref_id = str(uuid.uuid4())[:8]
        return jsonify({
            'error': 'Governance engine temporarily unavailable',
            'status': 503,
            'reference': ref_id
        }), 503

    signals = body.get('signals', {})
    is_valid, error_msg = _GovernanceEvaluationEngine.validate_signals(signals)
    if not is_valid:
        return jsonify({
            'error': f'Invalid signals: {error_msg}',
            'status': 400,
            'reference': str(uuid.uuid4())[:8],
            'hint': 'See GET /api/governance/schema for required fields and value ranges.'
        }), 400

    asset = str(body.get('asset', 'UNKNOWN'))[:64]
    domain = str(body.get('domain', 'generic'))[:32]
    metadata = body.get('metadata', {})
    if not isinstance(metadata, dict):
        metadata = {}

    try:
        engine = _GovernanceEvaluationEngine()
        evaluation = engine.evaluate(
            signals=signals,
            asset=asset,
            domain=domain,
            metadata=metadata,
        )
    except Exception as e:
        ref_id = str(uuid.uuid4())[:8]
        logger.error(f"Governance evaluation error ref={ref_id}: {e}")
        return jsonify({
            'error': 'Internal evaluation error',
            'status': 500,
            'reference': ref_id
        }), 500

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
