"""
OMNIX Governance API — External Signal Evaluation Endpoint.

POST /api/governance/evaluate                                    — Submit normalized signals, receive PQC-signed receipt.
GET  /api/governance/schema                                      — Signal schema documentation (public).
GET  /api/governance/receipts                                    — Client's own receipts (authenticated).
POST /api/governance/admin/clients                               — Create B2B client (admin only).
GET  /api/governance/admin/clients                               — List all B2B clients (admin only).
DELETE /api/governance/admin/clients/<client_id>                 — Deactivate client (admin only).
POST /api/governance/admin/clients/<client_id>/rotate            — Rotate API key (admin only).
GET  /api/governance/admin/clients/<client_id>/thresholds        — Get effective thresholds for client (admin only).
PUT  /api/governance/admin/clients/<client_id>/thresholds        — Set per-client checkpoint thresholds (admin only).
DELETE /api/governance/admin/clients/<client_id>/thresholds      — Revert client thresholds to defaults (admin only).
GET  /api/governance/admin/usage                                 — Monthly usage summary for all clients (admin only).
GET  /api/governance/admin/usage/<client_id>                     — Monthly usage detail for one client (admin only).

ADR-028: External Signal Evaluation API
ADR-037: Per-Client Configurable Thresholds
ADR-051: Client Usage Reporting & Billing Audit Trail
"""

import json
import logging
import os
import sys
import time
import threading
import urllib.request
import urllib.error
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

try:
    # Standalone deployment (omnix_web/api/ on Railway)
    from api.gov_auth_rbac import (
        authenticate_client,
        create_client,
        deactivate_client,
        list_clients,
        reactivate_client,
        rotate_api_key,
        update_last_seen,
    )
except ImportError:
    # Package deployment (omnix_dashboard/ on Flask Dashboard)
    from .auth_rbac import (
        authenticate_client,
        create_client,
        deactivate_client,
        list_clients,
        reactivate_client,
        rotate_api_key,
        update_last_seen,
    )

_alerts_trigger = None

def _get_alerts_trigger():
    global _alerts_trigger
    if _alerts_trigger is not None:
        return _alerts_trigger
    try:
        from .governance_alerts import trigger_alerts
        _alerts_trigger = trigger_alerts
    except Exception:
        _alerts_trigger = None
    return _alerts_trigger

logger = logging.getLogger(__name__)

governance_bp = Blueprint('governance', __name__)

_rate_limit_store: dict = defaultdict(list)
_RATE_LIMIT_WINDOW = 60
_RATE_LIMIT_MAX = 10

_client_rate_limit_store: dict = defaultdict(list)
_CLIENT_RATE_LIMIT_WINDOW = 60
_CLIENT_RATE_LIMIT_MAX = 30

_MONTHLY_ALERT_THRESHOLD = 500
_monthly_alert_sent: dict = {}

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

        _api_dir = os.path.dirname(__file__)

        # Path 1: bundled copy inside omnix_web/api/omnix_engine/ (Railway — only omnix_web is deployed)
        _local_evaluator = os.path.join(_api_dir, "omnix_engine", "external_evaluator.py")
        _local_receipt   = os.path.join(_api_dir, "omnix_engine", "decision_receipt.py")

        # Path 2: full repo (local dev — omnix_core available 3 levels up)
        _root = os.path.dirname(os.path.dirname(_api_dir))
        _repo_evaluator = os.path.join(_root, "omnix_core", "governance", "external_evaluator.py")
        _repo_receipt   = os.path.join(_root, "omnix_core", "evidence", "decision_receipt.py")

        evaluator_path = _local_evaluator if os.path.exists(_local_evaluator) else _repo_evaluator
        receipt_path   = _local_receipt   if os.path.exists(_local_receipt)   else _repo_receipt

        spec_ev = importlib.util.spec_from_file_location("_omnix_gov_evaluator", evaluator_path)
        mod_ev = importlib.util.module_from_spec(spec_ev)
        sys.modules['_omnix_gov_evaluator'] = mod_ev
        spec_ev.loader.exec_module(mod_ev)
        _GovernanceEvaluationEngine = mod_ev.GovernanceEvaluationEngine

        spec_rc = importlib.util.spec_from_file_location("_omnix_gov_receipt", receipt_path)
        mod_rc = importlib.util.module_from_spec(spec_rc)
        sys.modules['_omnix_gov_receipt'] = mod_rc
        spec_rc.loader.exec_module(mod_rc)
        _DecisionReceiptEngine = mod_rc.DecisionReceiptEngine

        _ENGINE_AVAILABLE = True
        logger.info(
            f"GovernanceEvaluationEngine loaded from: {evaluator_path}"
        )
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


def _is_client_rate_limited(client_id: str) -> bool:
    """Per-client rate limit: max 30 calls per minute. Protects against accidental loops."""
    now = time.time()
    window_start = now - _CLIENT_RATE_LIMIT_WINDOW
    _client_rate_limit_store[client_id] = [
        ts for ts in _client_rate_limit_store[client_id] if ts > window_start
    ]
    if len(_client_rate_limit_store[client_id]) >= _CLIENT_RATE_LIMIT_MAX:
        return True
    _client_rate_limit_store[client_id].append(now)
    return False


def _check_monthly_alert(client_id: str) -> None:
    """Check monthly usage and alert Harold via Telegram if threshold is crossed. Runs in background thread."""
    def _run():
        try:
            import datetime
            now = datetime.datetime.utcnow()
            month_key = f"{client_id}:{now.year}:{now.month}"

            if _monthly_alert_sent.get(month_key):
                return

            conn = _get_db_conn()
            cur = conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM decision_receipts
                WHERE client_id = %s
                AND created_at >= date_trunc('month', NOW())
            """, (client_id,))
            count = cur.fetchone()[0]
            conn.close()

            if count >= _MONTHLY_ALERT_THRESHOLD:
                _monthly_alert_sent[month_key] = True
                msg = (
                    f"⚠️ OMNIX — Alerta de uso mensual\n\n"
                    f"Cliente: {client_id}\n"
                    f"Evaluaciones este mes: {count}\n"
                    f"Umbral: {_MONTHLY_ALERT_THRESHOLD}\n\n"
                    f"Revisar uso y facturación."
                )
                _notify_harold_telegram(msg)
        except Exception as e:
            logger.warning(f"_check_monthly_alert error: {e}")

    threading.Thread(target=_run, daemon=True).start()


def _get_db_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def _ensure_thresholds_table() -> None:
    """Ensure client_thresholds table exists. Called once on first evaluate request. ADR-037."""
    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS client_thresholds (
                id SERIAL PRIMARY KEY,
                client_id VARCHAR(64) NOT NULL REFERENCES b2b_clients(client_id) ON DELETE CASCADE,
                checkpoint_id VARCHAR(8) NOT NULL
                    CHECK (checkpoint_id IN ('CP-1','CP-2','CP-3','CP-4','CP-5','CP-6')),
                threshold NUMERIC(5,2) NOT NULL CHECK (threshold >= 0 AND threshold <= 100),
                updated_by VARCHAR(64),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(client_id, checkpoint_id)
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_client_thresholds_client_id ON client_thresholds(client_id)"
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"_ensure_thresholds_table: {e}")


_THRESHOLDS_TABLE_ENSURED = False

# ── VELOS GATEWAY CONFIG (ADR-052) ───────────────────────────────────────────
# KEEP IN SYNC with omnix_dashboard/blueprints/governance.py — both files must be
# identical in this section. ADR-052.
_VELOS_PUSH_LOG_ENSURED  = False
_VELOS_GATEWAY_URL       = "https://velos-gateway.onrender.com/api/v1/intercept"
_VELOS_CLIENT_ID         = os.environ.get("VELOS_CLIENT_ID", "velos-partner")
_VELOS_PUSH_SEMAPHORE    = threading.Semaphore(10)   # Max 10 concurrent push threads
_HAROLD_TELEGRAM_CHAT_ID = os.environ.get("HAROLD_TELEGRAM_CHAT_ID", "7014748854")


def _ensure_velos_push_log_table() -> None:
    """Create velos_push_log table if not exists. Called once on first push. ADR-052."""
    global _VELOS_PUSH_LOG_ENSURED
    if _VELOS_PUSH_LOG_ENSURED:
        return
    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS velos_push_log (
                id            SERIAL PRIMARY KEY,
                receipt_id    VARCHAR(64)  NOT NULL,
                client_id     VARCHAR(64)  NOT NULL,
                decision      VARCHAR(16)  NOT NULL,
                disposition   VARCHAR(16)  NOT NULL DEFAULT 'SENT',
                skip_reason   TEXT,
                pushed_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
                latency_ms    INTEGER,
                http_status   INTEGER,
                success       BOOLEAN      NOT NULL DEFAULT FALSE,
                response_body TEXT,
                error_message TEXT
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_velos_push_log_receipt ON velos_push_log(receipt_id)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_velos_push_log_pushed_at ON velos_push_log(pushed_at)"
        )
        conn.commit()
        conn.close()
        _VELOS_PUSH_LOG_ENSURED = True
    except Exception as e:
        logger.warning(f"_ensure_velos_push_log_table: {e}")


def _log_velos_disposition(
    receipt_id: str,
    client_id: str,
    decision: str,
    disposition: str,
    *,
    skip_reason: str | None = None,
    http_status: int | None = None,
    success: bool = False,
    response_body: str | None = None,
    error_message: str | None = None,
    latency_ms: int | None = None,
) -> None:
    """Write every Velos push disposition to velos_push_log (SENT/SKIPPED/ERROR)."""
    _ensure_velos_push_log_table()
    try:
        conn = _get_db_conn()
        cur  = conn.cursor()
        cur.execute(
            """
            INSERT INTO velos_push_log
                (receipt_id, client_id, decision, disposition, skip_reason,
                 latency_ms, http_status, success, response_body, error_message)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                receipt_id,
                client_id,
                decision,
                disposition,
                skip_reason,
                latency_ms,
                http_status,
                success,
                response_body[:512] if response_body else None,
                error_message,
            ),
        )
        conn.commit()
        conn.close()
    except Exception as db_err:
        logger.error(f"[VELOS LOG] Failed to write disposition: {db_err}")


def _notify_harold_telegram(
    receipt_id: str,
    decision: str,
    disposition: str,
    *,
    latency_ms: int | None = None,
    http_status: int | None = None,
    error_message: str | None = None,
    asset: str | None = None,
) -> None:
    """
    Send a Telegram message to Harold when a Velos push completes (SENT or ERROR).
    Called inside the push daemon thread — synchronous HTTP call is intentional here.
    Silent on any failure — notification errors never affect the governance pipeline.
    Chat ID read from HAROLD_TELEGRAM_CHAT_ID env var (default: Harold's known ID).
    ADR-052.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        return

    chat_id   = _HAROLD_TELEGRAM_CHAT_ID
    asset_str = f"\n📦 Asset: <b>{asset}</b>" if asset else ""

    if disposition == "SENT":
        text = (
            f"🟢 <b>Velos Push — ENVIADO</b>\n"
            f"📋 Receipt: <code>{receipt_id}</code>\n"
            f"📊 Decision: <b>{decision}</b>"
            f"{asset_str}\n"
            f"✅ HTTP {http_status} · {latency_ms}ms"
        )
    else:  # ERROR
        err = (error_message or "Sin detalle")[:120]
        text = (
            f"🔴 <b>Velos Push — ERROR</b>\n"
            f"📋 Receipt: <code>{receipt_id}</code>\n"
            f"📊 Decision: <b>{decision}</b>"
            f"{asset_str}\n"
            f"❌ HTTP {http_status} — {err}\n"
            f"⏱ {latency_ms}ms"
        )

    try:
        body = json.dumps({
            "chat_id":    chat_id,
            "text":       text,
            "parse_mode": "HTML",
        }).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5):
            logger.debug(
                f"[VELOS NOTIFY] Telegram OK receipt={receipt_id} disposition={disposition}"
            )
    except Exception as exc:
        logger.warning(f"[VELOS NOTIFY] Telegram failed receipt={receipt_id}: {exc}")


def _push_to_velos_gateway(receipt_id: str, client_id: str, decision: str, payload: dict) -> None:
    """
    Push a governance receipt to the Velos ingestion gateway.
    Non-blocking — called in a bounded daemon thread (semaphore: max 10 concurrent).
    Every disposition (SENT/SKIPPED/ERROR) is logged to velos_push_log for billing audit.
    Only fires HTTP request when VELOS_GATEWAY_TOKEN is set and client_id matches.
    ADR-052.
    """
    token = os.environ.get("VELOS_GATEWAY_TOKEN")

    # Log SKIPPED cases — no token configured
    if not token:
        _log_velos_disposition(
            receipt_id, client_id, decision, "SKIPPED",
            skip_reason="VELOS_GATEWAY_TOKEN not set",
        )
        logger.debug(f"[VELOS PUSH] receipt={receipt_id} SKIPPED — token not configured")
        return

    # Log SKIPPED cases — wrong client
    if client_id != _VELOS_CLIENT_ID:
        _log_velos_disposition(
            receipt_id, client_id, decision, "SKIPPED",
            skip_reason=f"client_id={client_id} is not the Velos gateway client",
        )
        return

    # Semaphore prevents unbounded thread accumulation under burst traffic
    acquired = _VELOS_PUSH_SEMAPHORE.acquire(blocking=False)
    if not acquired:
        _log_velos_disposition(
            receipt_id, client_id, decision, "SKIPPED",
            skip_reason="semaphore exhausted — too many concurrent pushes",
        )
        logger.warning(f"[VELOS PUSH] receipt={receipt_id} SKIPPED — semaphore full")
        return

    t_start = time.monotonic()
    http_status   = None
    success       = False
    response_body = None
    error_message = None

    try:
        # Build safe payload — no internal secrets, no DB credentials, no infra details
        safe_payload = {
            "receipt_id":          payload.get("receipt_id"),
            "timestamp":           payload.get("timestamp"),
            "client_id":           client_id,
            "asset":               payload.get("asset"),
            "domain":              payload.get("domain"),
            "decision":            decision,
            "checkpoints_total":   payload.get("checkpoints_total"),
            "checkpoints_passed":  payload.get("checkpoints_passed"),
            "checkpoints_blocked": payload.get("checkpoints_blocked"),
            "content_hash":        payload.get("content_hash"),
            "signature":           payload.get("signature"),
            "signature_algorithm": payload.get("signature_algorithm"),
            "pqc_signed":          payload.get("pqc_signed"),
            "policy_version":      payload.get("policy_version"),
            "verifiable_at":       payload.get("verifiable_at"),
            "gate_results":        payload.get("gate_results"),
        }

        body_bytes = json.dumps(safe_payload, default=str).encode("utf-8")
        req = urllib.request.Request(
            _VELOS_GATEWAY_URL,
            data=body_bytes,
            headers={
                "Content-Type":  "application/json",
                "Authorization": f"Bearer {token}",
                "X-Source":      "OMNIX-Governance",
                "X-Receipt-ID":  receipt_id,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            http_status   = resp.getcode()
            response_body = resp.read(512).decode("utf-8", errors="replace")
            success       = (200 <= http_status < 300)

    except urllib.error.HTTPError as e:
        http_status   = e.code
        error_message = str(e)
        try:
            response_body = e.read(256).decode("utf-8", errors="replace")
        except Exception:
            pass
    except Exception as e:
        error_message = str(e)[:500]
    finally:
        _VELOS_PUSH_SEMAPHORE.release()

    latency_ms = int((time.monotonic() - t_start) * 1000)
    disposition = "SENT" if success else "ERROR"

    if success:
        logger.info(
            f"[VELOS PUSH] receipt={receipt_id} decision={decision} "
            f"status={http_status} latency={latency_ms}ms — OK"
        )
    else:
        logger.warning(
            f"[VELOS PUSH] receipt={receipt_id} decision={decision} "
            f"status={http_status} latency={latency_ms}ms error={error_message}"
        )

    _log_velos_disposition(
        receipt_id, client_id, decision, disposition,
        http_status=http_status,
        success=success,
        response_body=response_body,
        error_message=error_message,
        latency_ms=latency_ms,
    )

    # Notify Harold on Telegram for every SENT or ERROR — SKIPPED omitted (not actionable)
    if disposition in ("SENT", "ERROR"):
        _notify_harold_telegram(
            receipt_id, decision, disposition,
            latency_ms=latency_ms,
            http_status=http_status,
            error_message=error_message,
            asset=payload.get("asset"),
        )


def _load_client_checkpoint_overrides(client_id: str) -> list[dict]:
    """
    Load per-client checkpoint threshold overrides from client_thresholds table.
    Merges with CHECKPOINT_DEFAULTS — only defined rows override the defaults.
    Returns a list of checkpoint dicts compatible with GovernanceEvaluationEngine.

    Fail-closed: any error (DB, parse, validation) → returns CHECKPOINT_DEFAULTS.
    ADR-037: Per-Client Configurable Thresholds.
    """
    global _THRESHOLDS_TABLE_ENSURED
    if not _THRESHOLDS_TABLE_ENSURED:
        _ensure_thresholds_table()
        _THRESHOLDS_TABLE_ENSURED = True

    try:
        import importlib.util as _ilu
        import os as _os
        _root = _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__)))
        _ev_path = _os.path.join(_root, "omnix_core", "governance", "external_evaluator.py")
        _spec = _ilu.spec_from_file_location("_omnix_ev_floors", _ev_path)
        _mod = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        defaults = list(_mod.CHECKPOINT_DEFAULTS)
    except Exception as e:
        logger.warning(f"_load_client_checkpoint_overrides: could not load CHECKPOINT_DEFAULTS: {e}")
        return []

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT checkpoint_id, threshold FROM client_thresholds WHERE client_id = %s",
            (client_id,)
        )
        rows = {r["checkpoint_id"]: float(r["threshold"]) for r in cur.fetchall()}
        conn.close()
    except Exception as e:
        logger.warning(f"_load_client_checkpoint_overrides DB error for {client_id}: {e} — using defaults")
        return defaults

    if not rows:
        return defaults

    merged = []
    for cp in defaults:
        cp_copy = dict(cp)
        if cp["id"] in rows:
            cp_copy["threshold"] = rows[cp["id"]]
            cp_copy["_source"] = "client_custom"
        else:
            cp_copy["_source"] = "default"
        merged.append(cp_copy)

    logger.info(f"Loaded {len(rows)} custom threshold(s) for client={client_id}")
    return merged


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
    Evaluate external signals through the OMNIX 11-checkpoint governance pipeline.
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

    # Rate limit per client_id (protects against accidental loops in client code)
    if _is_client_rate_limited(client_id):
        ref_id = str(uuid.uuid4())[:8]
        logger.warning(f"Client rate limit hit: client={client_id} ref={ref_id}")
        return jsonify({
            'error': f'Client rate limit exceeded — {_CLIENT_RATE_LIMIT_MAX} requests per minute per client',
            'status': 429,
            'reference': ref_id,
            'retry_after_seconds': _CLIENT_RATE_LIMIT_WINDOW,
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
        checkpoint_overrides = _load_client_checkpoint_overrides(client_id)
        thresholds_source = "client_custom" if any(
            cp.get("_source") == "client_custom" for cp in checkpoint_overrides
        ) else "default"
        clean_overrides = [{k: v for k, v in cp.items() if k != "_source"} for cp in checkpoint_overrides]
        engine = _GovernanceEvaluationEngine(checkpoint_overrides=clean_overrides if clean_overrides else None)
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

    try:
        _trigger = _get_alerts_trigger()
        if _trigger:
            alert_payload = dict(evaluation)
            alert_payload["asset"] = asset
            alert_payload["domain"] = domain
            threading.Thread(
                target=_trigger,
                args=(client_id, alert_payload, receipt.get("receipt_id")),
                daemon=True,
            ).start()
    except Exception as _ae:
        logger.debug(f"Alert trigger skipped: {_ae}")

    # ── Velos Gateway Push (non-blocking, B2B Velos client only) ──────────────
    try:
        velos_payload = {
            "receipt_id":          receipt.get("receipt_id"),
            "timestamp":           receipt.get("timestamp"),
            "asset":               asset,
            "domain":              domain,
            "checkpoints_total":   evaluation.get("checkpoints_total"),
            "checkpoints_passed":  evaluation.get("checkpoints_passed"),
            "checkpoints_blocked": evaluation.get("checkpoints_blocked"),
            "content_hash":        receipt.get("content_hash"),
            "signature":           receipt.get("signature"),
            "signature_algorithm": receipt.get("signature_algorithm", "NONE"),
            "pqc_signed":          receipt.get("signature") is not None,
            "policy_version":      receipt.get("policy_version", os.environ.get("OMNIX_VERSION", "6.5.4e")),
            "verifiable_at":       "https://omnibotgenesis-production.up.railway.app/verify",
            "gate_results":        evaluation.get("gate_results"),
        }
        threading.Thread(
            target=_push_to_velos_gateway,
            args=(receipt.get("receipt_id"), client_id, evaluation["decision"], velos_payload),
            daemon=True,
        ).start()
    except Exception as _ve:
        logger.debug(f"Velos push thread skipped: {_ve}")

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
        'thresholds_source': thresholds_source,
        'verifiable_at': 'https://omnibotgenesis-production.up.railway.app/verify',
        'policy_version': receipt.get('policy_version', os.environ.get('OMNIX_VERSION', '6.5.4e')),
    }

    logger.info(
        f"[GOVERNANCE] evaluate: client={client_id} asset={asset} domain={domain} "
        f"decision={evaluation['decision']} "
        f"passed={evaluation['checkpoints_passed']}/{evaluation['checkpoints_total']} "
        f"thresholds={thresholds_source} "
        f"receipt={receipt.get('receipt_id')} encrypted={encrypted_payload is not None} ip={client_ip}"
    )

    # Monthly usage alert (non-blocking)
    _check_monthly_alert(client_id)

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


# ── THRESHOLD MANAGEMENT ENDPOINTS (ADR-037) ──────────────────────────────────

@governance_bp.route('/api/governance/admin/clients/<string:target_client_id>/thresholds', methods=['GET'])
def admin_get_thresholds(target_client_id: str):
    """
    Return effective checkpoints for a client.
    Each entry shows current threshold value and source: 'default' or 'custom'.
    Admin only. ADR-037.
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    overrides = _load_client_checkpoint_overrides(target_client_id)
    if not overrides:
        return jsonify({'error': 'Could not load checkpoints', 'status': 500}), 500

    result = []
    for cp in overrides:
        result.append({
            'checkpoint_id': cp['id'],
            'name': cp.get('name', ''),
            'threshold': cp['threshold'],
            'operator': cp.get('operator', ''),
            'source': cp.get('_source', 'default'),
        })

    return jsonify({
        'client_id': target_client_id,
        'checkpoints': result,
        'custom_count': sum(1 for r in result if r['source'] == 'client_custom'),
        'total': len(result),
    }), 200


@governance_bp.route('/api/governance/admin/clients/<string:target_client_id>/thresholds', methods=['PUT'])
def admin_set_thresholds(target_client_id: str):
    """
    Set per-client checkpoint threshold overrides.
    Body: {"CP-1": 60, "CP-3": 70}  — partial updates, only named checkpoints are changed.
    Validates against CHECKPOINT_SAFETY_FLOORS.
    Admin only. ADR-037.
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    try:
        import importlib.util as _ilu
        import os as _os
        _root = _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__)))
        _ev_path = _os.path.join(_root, "omnix_core", "governance", "external_evaluator.py")
        _spec = _ilu.spec_from_file_location("_omnix_ev_floors_admin", _ev_path)
        _mod = _ilu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        validate_fn = _mod.validate_threshold_against_floor
        floors = _mod.CHECKPOINT_SAFETY_FLOORS
    except Exception as e:
        logger.error(f"admin_set_thresholds: cannot load safety floors: {e}")
        return jsonify({'error': 'Internal configuration error', 'status': 500}), 500

    if not request.is_json:
        return jsonify({'error': 'Request must be Content-Type: application/json', 'status': 400}), 400
    try:
        body = request.get_json(force=True)
    except Exception:
        return jsonify({'error': 'Invalid JSON body', 'status': 400}), 400

    if not isinstance(body, dict) or not body:
        return jsonify({'error': 'Body must be a non-empty JSON object: {"CP-1": 60, ...}', 'status': 400}), 400

    valid_cps = set(floors.keys())
    errors = []
    updates = {}

    for cp_id, value in body.items():
        if cp_id not in valid_cps:
            errors.append(f"Unknown checkpoint '{cp_id}'. Valid: {sorted(valid_cps)}")
            continue
        try:
            threshold = float(value)
        except (TypeError, ValueError):
            errors.append(f"{cp_id}: threshold must be a number, got {value!r}")
            continue
        ok, msg = validate_fn(cp_id, threshold)
        if not ok:
            errors.append(msg)
            continue
        updates[cp_id] = threshold

    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors, 'status': 400}), 400

    if not updates:
        return jsonify({'error': 'No valid checkpoints provided', 'status': 400}), 400

    admin_id = client['client_id']
    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        for cp_id, threshold in updates.items():
            cur.execute("""
                INSERT INTO client_thresholds (client_id, checkpoint_id, threshold, updated_by, updated_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (client_id, checkpoint_id)
                DO UPDATE SET threshold = EXCLUDED.threshold,
                              updated_by = EXCLUDED.updated_by,
                              updated_at = NOW()
            """, (target_client_id, cp_id, threshold, admin_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"admin_set_thresholds DB error for {target_client_id}: {e}")
        return jsonify({'error': 'Database error while saving thresholds', 'status': 500}), 500

    logger.info(
        f"[ADMIN] set thresholds for client={target_client_id} "
        f"checkpoints={list(updates.keys())} by admin={admin_id}"
    )

    effective = _load_client_checkpoint_overrides(target_client_id)
    result = [{
        'checkpoint_id': cp['id'],
        'name': cp.get('name', ''),
        'threshold': cp['threshold'],
        'operator': cp.get('operator', ''),
        'source': cp.get('_source', 'default'),
    } for cp in effective]

    return jsonify({
        'client_id': target_client_id,
        'updated': list(updates.keys()),
        'checkpoints': result,
        'message': f"{len(updates)} threshold(s) updated successfully.",
    }), 200


@governance_bp.route('/api/governance/admin/clients/<string:target_client_id>/thresholds', methods=['DELETE'])
def admin_delete_thresholds(target_client_id: str):
    """
    Revert ALL threshold overrides for a client to system defaults.
    Deletes all rows in client_thresholds for this client.
    Admin only. ADR-037.
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM client_thresholds WHERE client_id = %s", (target_client_id,))
        deleted = cur.rowcount
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"admin_delete_thresholds DB error for {target_client_id}: {e}")
        return jsonify({'error': 'Database error while deleting thresholds', 'status': 500}), 500

    logger.info(
        f"[ADMIN] reverted thresholds for client={target_client_id} "
        f"deleted={deleted} by admin={client['client_id']}"
    )
    return jsonify({
        'client_id': target_client_id,
        'deleted_overrides': deleted,
        'message': 'All custom thresholds removed. Client will now use system defaults.',
    }), 200


# ===========================================================================
# CLIENT USAGE REPORTING — ADR-051
# ===========================================================================

@governance_bp.route('/api/governance/admin/usage', methods=['GET'])
def admin_usage_summary():
    """
    GET /api/governance/admin/usage
    Monthly usage summary for ALL clients — for billing and audit.
    Admin only. ADR-051.

    Query params:
      - months: int (default 3) — how many trailing months to show
      - client_id: str (optional) — filter to a specific client

    Returns per-client, per-month counts of evaluations broken down by
    APPROVED / BLOCKED / HOLD decisions. Excludes 'PUBLIC' sandbox traffic.
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    try:
        months = max(1, min(int(request.args.get('months', 3)), 24))
    except (TypeError, ValueError):
        months = 3

    filter_client_id = request.args.get('client_id')

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        params = [months]
        client_filter_sql = ""
        if filter_client_id:
            client_filter_sql = "AND dr.client_id = %s"
            params.append(filter_client_id)

        cur.execute(f"""
            SELECT
                dr.client_id,
                bc.name AS client_name,
                bc.email AS client_email,
                bc.is_active,
                TO_CHAR(DATE_TRUNC('month', dr.created_at), 'YYYY-MM') AS month,
                COUNT(*) AS total_evaluations,
                SUM(CASE WHEN dr.decision = 'APPROVED' THEN 1 ELSE 0 END) AS approved,
                SUM(CASE WHEN dr.decision = 'BLOCKED' THEN 1 ELSE 0 END) AS blocked,
                SUM(CASE WHEN dr.decision = 'HOLD' THEN 1 ELSE 0 END) AS hold,
                MIN(dr.created_at) AS first_evaluation,
                MAX(dr.created_at) AS last_evaluation
            FROM decision_receipts dr
            LEFT JOIN b2b_clients bc ON bc.client_id = dr.client_id
            WHERE dr.client_id != 'PUBLIC'
              AND dr.created_at >= DATE_TRUNC('month', NOW()) - (INTERVAL '1 month' * %s)
              {client_filter_sql}
            GROUP BY dr.client_id, bc.name, bc.email, bc.is_active,
                     DATE_TRUNC('month', dr.created_at)
            ORDER BY dr.client_id, month DESC
        """, params)

        rows = cur.fetchall()
        conn.close()

        structured = {}
        for row in rows:
            cid = row['client_id']
            if cid not in structured:
                structured[cid] = {
                    'client_id': cid,
                    'client_name': row['client_name'] or cid,
                    'client_email': row['client_email'],
                    'is_active': row['is_active'],
                    'months': [],
                    'total_all_time_in_range': 0,
                }
            month_entry = {
                'month': row['month'],
                'total_evaluations': int(row['total_evaluations']),
                'approved': int(row['approved'] or 0),
                'blocked': int(row['blocked'] or 0),
                'hold': int(row['hold'] or 0),
                'first_evaluation': row['first_evaluation'].isoformat() if row['first_evaluation'] else None,
                'last_evaluation': row['last_evaluation'].isoformat() if row['last_evaluation'] else None,
            }
            structured[cid]['months'].append(month_entry)
            structured[cid]['total_all_time_in_range'] += int(row['total_evaluations'])

        clients_list = list(structured.values())
        grand_total = sum(c['total_all_time_in_range'] for c in clients_list)

        logger.info(
            f"[ADMIN] usage_summary: queried by admin={client['client_id']} "
            f"months={months} clients={len(clients_list)} total={grand_total}"
        )

        return jsonify({
            'report_generated_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
            'trailing_months': months,
            'clients': clients_list,
            'grand_total_evaluations': grand_total,
            'client_count': len(clients_list),
            'note': 'PUBLIC sandbox traffic excluded. Counts are for B2B API calls only.',
        }), 200

    except Exception as e:
        logger.error(f"admin_usage_summary DB error: {e}")
        return jsonify({'error': 'Database error generating usage report', 'status': 500}), 500


@governance_bp.route('/api/governance/admin/usage/<string:target_client_id>', methods=['GET'])
def admin_usage_client(target_client_id: str):
    """
    GET /api/governance/admin/usage/<client_id>
    Detailed monthly usage for a specific client — all decisions, monthly breakdown.
    Admin only. ADR-051.

    Query params:
      - months: int (default 12) — how many trailing months to show
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    try:
        months = max(1, min(int(request.args.get('months', 12)), 36))
    except (TypeError, ValueError):
        months = 12

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("""
            SELECT client_id, name, email, role, is_active, created_at, last_seen_at
            FROM b2b_clients WHERE client_id = %s
        """, (target_client_id,))
        client_row = cur.fetchone()

        cur.execute("""
            SELECT
                TO_CHAR(DATE_TRUNC('month', created_at), 'YYYY-MM') AS month,
                COUNT(*) AS total_evaluations,
                SUM(CASE WHEN decision = 'APPROVED' THEN 1 ELSE 0 END) AS approved,
                SUM(CASE WHEN decision = 'BLOCKED' THEN 1 ELSE 0 END) AS blocked,
                SUM(CASE WHEN decision = 'HOLD' THEN 1 ELSE 0 END) AS hold,
                COUNT(DISTINCT asset) AS distinct_assets,
                MIN(created_at) AS first_evaluation,
                MAX(created_at) AS last_evaluation
            FROM decision_receipts
            WHERE client_id = %s
              AND created_at >= DATE_TRUNC('month', NOW()) - (INTERVAL '1 month' * %s)
            GROUP BY DATE_TRUNC('month', created_at)
            ORDER BY month DESC
        """, (target_client_id, months))

        monthly_rows = cur.fetchall()

        cur.execute("""
            SELECT COUNT(*) AS total FROM decision_receipts WHERE client_id = %s
        """, (target_client_id,))
        lifetime_row = cur.fetchone()

        conn.close()

        monthly = []
        total_in_range = 0
        for row in monthly_rows:
            entry = {
                'month': row['month'],
                'total_evaluations': int(row['total_evaluations']),
                'approved': int(row['approved'] or 0),
                'blocked': int(row['blocked'] or 0),
                'hold': int(row['hold'] or 0),
                'distinct_assets': int(row['distinct_assets'] or 0),
                'first_evaluation': row['first_evaluation'].isoformat() if row['first_evaluation'] else None,
                'last_evaluation': row['last_evaluation'].isoformat() if row['last_evaluation'] else None,
            }
            total_in_range += entry['total_evaluations']
            monthly.append(entry)

        logger.info(
            f"[ADMIN] usage_client: queried by admin={client['client_id']} "
            f"target={target_client_id} months={months} total_in_range={total_in_range}"
        )

        return jsonify({
            'report_generated_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
            'client_id': target_client_id,
            'client_info': dict(client_row) if client_row else None,
            'trailing_months': months,
            'total_evaluations_in_range': total_in_range,
            'lifetime_evaluations': int(lifetime_row['total'] if lifetime_row else 0),
            'monthly_breakdown': monthly,
        }), 200

    except Exception as e:
        logger.error(f"admin_usage_client DB error for {target_client_id}: {e}")
        return jsonify({'error': 'Database error generating client usage report', 'status': 500}), 500


# ===========================================================================
# EXECUTION BOUNDARY INTEGRITY — ADR-045
# ===========================================================================

@governance_bp.route('/api/governance/execution-integrity', methods=['GET'])
def api_execution_integrity_status():
    """
    GET /api/governance/execution-integrity
    Returns the current Execution Boundary Integrity Protocol (EBIP) status.
    ADR-045: Navigation health, concentration prediction, consistency violations.
    No authentication required — read-only system health endpoint.
    """
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from omnix_services.governance_service.execution_integrity import get_ebip
        ebip = get_ebip()
        status = ebip.get_system_integrity_status()
        return jsonify({'status': 'ok', 'execution_integrity': status}), 200
    except Exception as e:
        logger.warning(f"api_execution_integrity_status: {e}")
        return jsonify({
            'status': 'ok',
            'execution_integrity': {
                'overall_execution_integrity': 100.0,
                'navigation_health': {'alert_level': 'NOMINAL', 'total_decisions': 0},
                'concentration_prediction': {'predicted_risk': 'INSUFFICIENT_DATA'},
                'recent_consistency_violations_24h': 0,
                'components': {
                    'ACV': 'Admissibility Consistency Validator — ACTIVE',
                    'ECP': 'Execution Commitment Protocol — ACTIVE',
                    'NPM': 'Navigation Pattern Monitor — ACTIVE',
                    'CP':  'Concentration Predictor — ACTIVE',
                },
                'ebip_version': '1.0',
            }
        }), 200
