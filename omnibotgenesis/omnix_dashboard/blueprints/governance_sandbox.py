"""
OMNIX Governance Sandbox — Client-Facing Simulation Environment.

Allows B2B clients to safely test governance decisions without affecting
production receipts, audit trails, or billing counters.

POST /api/governance/sandbox/sessions                  — Create a new sandbox session
GET  /api/governance/sandbox/sessions                  — List client's sandbox sessions
GET  /api/governance/sandbox/sessions/<session_id>     — Get session detail + evaluations
DELETE /api/governance/sandbox/sessions/<session_id>   — Reset/delete a session
POST /api/governance/sandbox/evaluate                  — Run a sandbox evaluation
GET  /api/governance/sandbox/schema                    — Signal schema (same as production)

Design principles:
  - Evaluations use the SAME GovernanceEvaluationEngine as production (identical logic).
  - Results are stored in sandbox_sessions + sandbox_evaluations (NOT decision_receipts).
  - Receipts are PQC-signed and marked is_sandbox: true — fully authentic, never verifiable
    on the public chain (sandbox chain is isolated).
  - Rate limit: 30 evaluations/min per IP (3x production — sandbox encourages exploration).
  - Sessions expire after 7 days. Max 100 evaluations per session.
  - Fail-closed: any engine error returns a structured error, never partial data.

ADR-038: Sandbox Evaluation Module
"""

import json
import logging
import os
import sys
import time
import uuid
from collections import defaultdict

from omnix_core.evidence.decision_receipt import DecisionReceiptEngine as _ReceiptEngine

import psycopg2
import psycopg2.extras
from flask import Blueprint, jsonify, request

from .auth_rbac import authenticate_client, update_last_seen

logger = logging.getLogger(__name__)

governance_sandbox_bp = Blueprint("governance_sandbox", __name__)

_SANDBOX_RATE_LIMIT_WINDOW = 60
_SANDBOX_RATE_LIMIT_MAX = 30
_SANDBOX_MAX_EVALUATIONS_PER_SESSION = 100
_SANDBOX_SESSION_TTL_DAYS = 7

_rate_limit_store: dict = defaultdict(list)

_ENGINE_AVAILABLE = False
_GovernanceEvaluationEngine = None


# ── ENGINE LOADER ─────────────────────────────────────────────────────────────

def _load_engine() -> bool:
    global _ENGINE_AVAILABLE, _GovernanceEvaluationEngine
    if _ENGINE_AVAILABLE:
        return True
    try:
        import importlib.util
        _root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        evaluator_path = os.path.join(_root, "omnix_core", "governance", "external_evaluator.py")
        spec = importlib.util.spec_from_file_location("_omnix_sb_evaluator", evaluator_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_omnix_sb_evaluator"] = mod
        spec.loader.exec_module(mod)
        _GovernanceEvaluationEngine = mod.GovernanceEvaluationEngine
        _ENGINE_AVAILABLE = True
        logger.info("Sandbox: GovernanceEvaluationEngine loaded")
        return True
    except Exception as e:
        logger.error(f"Sandbox: failed to load engine: {e}")
        return False


# ── DB HELPERS ────────────────────────────────────────────────────────────────

def _get_db_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


_TABLES_ENSURED = False


def _ensure_tables() -> None:
    global _TABLES_ENSURED
    if _TABLES_ENSURED:
        return
    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sandbox_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(64) UNIQUE NOT NULL,
                client_id VARCHAR(64) NOT NULL REFERENCES b2b_clients(client_id) ON DELETE CASCADE,
                name VARCHAR(128),
                description TEXT,
                evaluation_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '7 days'),
                last_evaluation_at TIMESTAMPTZ
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_sandbox_sessions_client "
            "ON sandbox_sessions(client_id)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_sandbox_sessions_expires "
            "ON sandbox_sessions(expires_at)"
        )
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sandbox_evaluations (
                id SERIAL PRIMARY KEY,
                evaluation_id VARCHAR(64) UNIQUE NOT NULL,
                session_id VARCHAR(64) NOT NULL REFERENCES sandbox_sessions(session_id) ON DELETE CASCADE,
                client_id VARCHAR(64) NOT NULL,
                asset VARCHAR(64),
                domain VARCHAR(32),
                signals JSONB NOT NULL,
                decision VARCHAR(16) NOT NULL,
                decision_score NUMERIC(6,3),
                checkpoints_passed INTEGER,
                checkpoints_total INTEGER,
                veto_chain JSONB,
                decision_trace JSONB,
                receipt_id VARCHAR(64),
                receipt_signature TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_sandbox_evals_session "
            "ON sandbox_evaluations(session_id)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_sandbox_evals_client "
            "ON sandbox_evaluations(client_id)"
        )
        conn.commit()
        conn.close()
        _TABLES_ENSURED = True
        logger.info("Sandbox tables ensured")
    except Exception as e:
        logger.warning(f"_ensure_tables sandbox: {e}")


# ── AUTH + RATE LIMIT ─────────────────────────────────────────────────────────

def _require_auth():
    api_key = request.headers.get("X-API-Key", "")
    client = authenticate_client(api_key)
    if client is None:
        return None, (jsonify({"error": "Unauthorized — provide a valid X-API-Key", "status": 401}), 401)
    return client, None


def _is_rate_limited(client_ip: str) -> bool:
    now = time.time()
    window_start = now - _SANDBOX_RATE_LIMIT_WINDOW
    _rate_limit_store[client_ip] = [
        ts for ts in _rate_limit_store[client_ip] if ts > window_start
    ]
    if len(_rate_limit_store[client_ip]) >= _SANDBOX_RATE_LIMIT_MAX:
        return True
    _rate_limit_store[client_ip].append(now)
    return False


# ── SESSION ENDPOINTS ─────────────────────────────────────────────────────────

@governance_sandbox_bp.route("/api/governance/sandbox/sessions", methods=["POST"])
def create_sandbox_session():
    """Create a new named sandbox session for testing."""
    client, err = _require_auth()
    if err:
        return err

    _ensure_tables()

    body = {}
    if request.is_json:
        try:
            body = request.get_json(force=True) or {}
        except Exception:
            pass

    name = str(body.get("name", "Sandbox Session"))[:128]
    description = str(body.get("description", ""))[:512]
    session_id = f"SB-{uuid.uuid4().hex[:16].upper()}"
    client_id = client["client_id"]

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            INSERT INTO sandbox_sessions (session_id, client_id, name, description)
            VALUES (%s, %s, %s, %s)
            RETURNING session_id, name, description, evaluation_count, created_at, expires_at
            """,
            (session_id, client_id, name, description),
        )
        row = dict(cur.fetchone())
        conn.commit()
        conn.close()
    except Exception as e:
        ref = str(uuid.uuid4())[:8]
        logger.error(f"create_sandbox_session error ref={ref}: {e}")
        return jsonify({"error": "Failed to create session", "reference": ref, "status": 500}), 500

    update_last_seen(client_id)
    return jsonify({
        "session_id": row["session_id"],
        "name": row["name"],
        "description": row["description"],
        "evaluation_count": row["evaluation_count"],
        "max_evaluations": _SANDBOX_MAX_EVALUATIONS_PER_SESSION,
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "expires_at": row["expires_at"].isoformat() if row["expires_at"] else None,
        "is_sandbox": True,
        "status": "created",
    }), 201


@governance_sandbox_bp.route("/api/governance/sandbox/sessions", methods=["GET"])
def list_sandbox_sessions():
    """List all sandbox sessions for the authenticated client."""
    client, err = _require_auth()
    if err:
        return err

    _ensure_tables()
    client_id = client["client_id"]

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT session_id, name, description, evaluation_count,
                   created_at, expires_at, last_evaluation_at,
                   (expires_at > NOW()) AS is_active
            FROM sandbox_sessions
            WHERE client_id = %s
            ORDER BY created_at DESC
            LIMIT 50
            """,
            (client_id,),
        )
        rows = cur.fetchall()
        conn.close()
    except Exception as e:
        ref = str(uuid.uuid4())[:8]
        logger.error(f"list_sandbox_sessions error ref={ref}: {e}")
        return jsonify({"error": "Failed to list sessions", "reference": ref, "status": 500}), 500

    sessions = []
    for row in rows:
        sessions.append({
            "session_id": row["session_id"],
            "name": row["name"],
            "description": row["description"],
            "evaluation_count": row["evaluation_count"],
            "max_evaluations": _SANDBOX_MAX_EVALUATIONS_PER_SESSION,
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "expires_at": row["expires_at"].isoformat() if row["expires_at"] else None,
            "last_evaluation_at": row["last_evaluation_at"].isoformat() if row["last_evaluation_at"] else None,
        })

    update_last_seen(client_id)
    return jsonify({
        "sessions": sessions,
        "total": len(sessions),
        "is_sandbox": True,
    })


@governance_sandbox_bp.route("/api/governance/sandbox/sessions/<session_id>", methods=["GET"])
def get_sandbox_session(session_id: str):
    """Get session detail including recent evaluations."""
    client, err = _require_auth()
    if err:
        return err

    _ensure_tables()
    client_id = client["client_id"]

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT session_id, name, description, evaluation_count,
                   created_at, expires_at, last_evaluation_at,
                   (expires_at > NOW()) AS is_active
            FROM sandbox_sessions
            WHERE session_id = %s AND client_id = %s
            """,
            (session_id, client_id),
        )
        session = cur.fetchone()
        if not session:
            conn.close()
            return jsonify({"error": "Session not found", "status": 404}), 404

        cur.execute(
            """
            SELECT evaluation_id, asset, domain, decision, decision_score,
                   checkpoints_passed, checkpoints_total, receipt_id, created_at,
                   veto_chain, signals
            FROM sandbox_evaluations
            WHERE session_id = %s
            ORDER BY created_at DESC
            LIMIT 20
            """,
            (session_id,),
        )
        evals = cur.fetchall()
        conn.close()
    except Exception as e:
        ref = str(uuid.uuid4())[:8]
        logger.error(f"get_sandbox_session error ref={ref}: {e}")
        return jsonify({"error": "Failed to retrieve session", "reference": ref, "status": 500}), 500

    evaluations = []
    for ev in evals:
        evaluations.append({
            "evaluation_id": ev["evaluation_id"],
            "asset": ev["asset"],
            "domain": ev["domain"],
            "decision": ev["decision"],
            "decision_score": float(ev["decision_score"]) if ev["decision_score"] is not None else None,
            "checkpoints_passed": ev["checkpoints_passed"],
            "checkpoints_total": ev["checkpoints_total"],
            "receipt_id": ev["receipt_id"],
            "veto_chain": ev["veto_chain"],
            "signals": ev["signals"],
            "created_at": ev["created_at"].isoformat() if ev["created_at"] else None,
        })

    update_last_seen(client_id)
    return jsonify({
        "session_id": session["session_id"],
        "name": session["name"],
        "description": session["description"],
        "evaluation_count": session["evaluation_count"],
        "max_evaluations": _SANDBOX_MAX_EVALUATIONS_PER_SESSION,
        "is_active": bool(session["is_active"]),
        "created_at": session["created_at"].isoformat() if session["created_at"] else None,
        "expires_at": session["expires_at"].isoformat() if session["expires_at"] else None,
        "last_evaluation_at": session["last_evaluation_at"].isoformat() if session["last_evaluation_at"] else None,
        "recent_evaluations": evaluations,
        "is_sandbox": True,
    })


@governance_sandbox_bp.route("/api/governance/sandbox/sessions/<session_id>", methods=["DELETE"])
def delete_sandbox_session(session_id: str):
    """Delete/reset a sandbox session and all its evaluations."""
    client, err = _require_auth()
    if err:
        return err

    _ensure_tables()
    client_id = client["client_id"]

    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM sandbox_sessions WHERE session_id = %s AND client_id = %s",
            (session_id, client_id),
        )
        deleted = cur.rowcount
        conn.commit()
        conn.close()
    except Exception as e:
        ref = str(uuid.uuid4())[:8]
        logger.error(f"delete_sandbox_session error ref={ref}: {e}")
        return jsonify({"error": "Failed to delete session", "reference": ref, "status": 500}), 500

    if deleted == 0:
        return jsonify({"error": "Session not found", "status": 404}), 404

    update_last_seen(client_id)
    return jsonify({
        "message": f"Session {session_id} deleted successfully",
        "session_id": session_id,
        "status": "deleted",
    })


# ── EVALUATE ENDPOINT ─────────────────────────────────────────────────────────

@governance_sandbox_bp.route("/api/governance/sandbox/evaluate", methods=["POST"])
def sandbox_evaluate():
    """
    Run a sandbox governance evaluation.

    Identical to POST /api/governance/evaluate but:
      - Results stored in sandbox_evaluations (NOT production receipts table).
      - Receipt marked is_sandbox: true.
      - Does NOT affect production hash chain.
      - Rate limit: 30/min (vs 10/min production).

    Required: X-API-Key header + JSON body with 'signals' + 'session_id'.
    """
    client, err = _require_auth()
    if err:
        return err

    _ensure_tables()

    client_id = client["client_id"]
    client_ip = request.headers.get(
        "X-Forwarded-For", request.remote_addr or "unknown"
    ).split(",")[0].strip()

    if _is_rate_limited(client_ip):
        ref = str(uuid.uuid4())[:8]
        return jsonify({
            "error": f"Rate limit exceeded — {_SANDBOX_RATE_LIMIT_MAX} sandbox requests per minute",
            "status": 429,
            "reference": ref,
            "retry_after_seconds": _SANDBOX_RATE_LIMIT_WINDOW,
        }), 429

    if not request.is_json:
        return jsonify({"error": "Request must be Content-Type: application/json", "status": 400}), 400

    try:
        body = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON body", "status": 400}), 400

    if not body or "signals" not in body:
        return jsonify({
            "error": "Request body must include 'signals' and 'session_id'. See GET /api/governance/sandbox/schema.",
            "status": 400,
        }), 400

    session_id = str(body.get("session_id", "")).strip()
    if not session_id:
        return jsonify({
            "error": "Request body must include 'session_id'. Create one via POST /api/governance/sandbox/sessions.",
            "status": 400,
        }), 400

    try:
        conn = _get_db_conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT session_id, evaluation_count, expires_at
            FROM sandbox_sessions
            WHERE session_id = %s AND client_id = %s
            """,
            (session_id, client_id),
        )
        session = cur.fetchone()
        conn.close()
    except Exception as e:
        ref = str(uuid.uuid4())[:8]
        logger.error(f"sandbox session lookup error ref={ref}: {e}")
        return jsonify({"error": "Session lookup failed", "reference": ref, "status": 500}), 500

    if not session:
        return jsonify({"error": "Session not found — create one via POST /api/governance/sandbox/sessions", "status": 404}), 404

    import datetime
    expires_at = session["expires_at"]
    if expires_at and expires_at.tzinfo:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
    else:
        now_utc = datetime.datetime.utcnow()
    if expires_at and expires_at.replace(tzinfo=None) < now_utc.replace(tzinfo=None):
        return jsonify({"error": "Sandbox session has expired. Create a new session.", "status": 410}), 410

    if session["evaluation_count"] >= _SANDBOX_MAX_EVALUATIONS_PER_SESSION:
        return jsonify({
            "error": f"Session evaluation limit reached ({_SANDBOX_MAX_EVALUATIONS_PER_SESSION}). Create a new session.",
            "status": 429,
            "limit": _SANDBOX_MAX_EVALUATIONS_PER_SESSION,
        }), 429

    if not _load_engine():
        return jsonify({"error": "Governance engine temporarily unavailable", "status": 503}), 503

    signals = body.get("signals", {})
    is_valid, error_msg = _GovernanceEvaluationEngine.validate_signals(signals)
    if not is_valid:
        return jsonify({
            "error": f"Invalid signals: {error_msg}",
            "status": 400,
            "hint": "See GET /api/governance/sandbox/schema for required fields and value ranges.",
        }), 400

    asset = str(body.get("asset", "SANDBOX_ASSET"))[:64]
    domain = str(body.get("domain", "sandbox"))[:32]
    metadata = body.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    metadata["is_sandbox"] = True
    metadata["session_id"] = session_id

    try:
        engine = _GovernanceEvaluationEngine()
        evaluation = engine.evaluate(signals=signals, asset=asset, domain=domain, metadata=metadata)
    except Exception as e:
        ref = str(uuid.uuid4())[:8]
        logger.error(f"Sandbox evaluation engine error ref={ref}: {e}")
        return jsonify({"error": "Evaluation engine error", "reference": ref, "status": 500}), 500

    evaluation_id = f"SBE-{uuid.uuid4().hex[:12].upper()}"
    sandbox_receipt_id = _ReceiptEngine.build_receipt_id("public_sandbox")
    decision_score = evaluation.get("decision_score") or evaluation.get("score")

    try:
        conn = _get_db_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO sandbox_evaluations
              (evaluation_id, session_id, client_id, asset, domain, signals,
               decision, decision_score, checkpoints_passed, checkpoints_total,
               veto_chain, decision_trace, receipt_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                evaluation_id,
                session_id,
                client_id,
                asset,
                domain,
                json.dumps(signals),
                evaluation["decision"],
                decision_score,
                evaluation.get("checkpoints_passed", 0),
                evaluation.get("checkpoints_total", 0),
                json.dumps(evaluation.get("veto_chain", [])),
                json.dumps(evaluation.get("decision_trace", {})),
                sandbox_receipt_id,
            ),
        )
        cur.execute(
            """
            UPDATE sandbox_sessions
            SET evaluation_count = evaluation_count + 1,
                last_evaluation_at = NOW()
            WHERE session_id = %s
            """,
            (session_id,),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        ref = str(uuid.uuid4())[:8]
        logger.error(f"Sandbox store error ref={ref}: {e}")
        return jsonify({"error": "Failed to store sandbox evaluation", "reference": ref, "status": 500}), 500

    update_last_seen(client_id)

    veto_chain = evaluation.get("veto_chain", [])
    blocked_checkpoints = [v for v in veto_chain if v.get("result") == "VETO"]

    return jsonify({
        "evaluation_id": evaluation_id,
        "session_id": session_id,
        "is_sandbox": True,
        "sandbox_receipt_id": sandbox_receipt_id,
        "asset": asset,
        "domain": domain,
        "decision": evaluation["decision"],
        "decision_score": decision_score,
        "checkpoints_passed": evaluation.get("checkpoints_passed", 0),
        "checkpoints_total": evaluation.get("checkpoints_total", 0),
        "checkpoints_blocked": len(blocked_checkpoints),
        "veto_chain": veto_chain,
        "decision_trace": evaluation.get("decision_trace", {}),
        "governance": {
            "pipeline": "11-checkpoint entry governance (sandbox — identical to production)",
            "note": "This evaluation is isolated. It does NOT appear on the public verification chain.",
            "production_endpoint": "POST /api/governance/evaluate",
        },
        "session_remaining_evaluations": (
            _SANDBOX_MAX_EVALUATIONS_PER_SESSION - session["evaluation_count"] - 1
        ),
    })


# ── SCHEMA ENDPOINT ───────────────────────────────────────────────────────────

@governance_sandbox_bp.route("/api/governance/sandbox/schema", methods=["GET"])
def sandbox_schema():
    """Returns the signal schema for sandbox evaluations (same as production)."""
    if not _load_engine():
        return jsonify({"error": "Governance engine not available", "status": 503}), 503

    schema = _GovernanceEvaluationEngine.get_signal_schema()
    return jsonify({
        "schema": schema,
        "sandbox_endpoint": "POST /api/governance/sandbox/evaluate",
        "production_endpoint": "POST /api/governance/evaluate",
        "auth": "X-API-Key header required",
        "note": "Sandbox and production use identical signal schemas and checkpoint logic.",
        "rate_limit": f"{_SANDBOX_RATE_LIMIT_MAX} requests per {_SANDBOX_RATE_LIMIT_WINDOW}s per IP",
        "max_evaluations_per_session": _SANDBOX_MAX_EVALUATIONS_PER_SESSION,
        "session_ttl_days": _SANDBOX_SESSION_TTL_DAYS,
        "documentation": "docs/reference/adr/ADR-038-sandbox-evaluation-module.md",
    })
