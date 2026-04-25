"""
OMNIX Oversight Surface API — ADR-124.

Provides endpoints to govern the *quality* of human oversight moments.

POST   /api/oversight/sessions                      — Create oversight session
GET    /api/oversight/sessions                      — List sessions (filtered)
GET    /api/oversight/sessions/<session_id>         — Get session details
POST   /api/oversight/sessions/<session_id>/open    — Mark session as presented (starts timer)
POST   /api/oversight/sessions/<session_id>/submit  — Submit human review
GET    /api/oversight/sessions/<session_id>/eqs     — Get Epistemic Quality Score detail
POST   /api/oversight/sessions/expire               — Mark stale sessions EXPIRED (admin)

Authentication: X-API-Key header — same B2B RBAC as governance endpoints.
"""

import logging
import os
import sys

from flask import Blueprint, jsonify, request

logger = logging.getLogger("OMNIX.API.OversightBP")

oversight_bp = Blueprint("oversight_bp", __name__)


def _load_ose():
    try:
        _root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        sys.path.insert(0, _root)
        from omnix_core.governance.oversight_surface import OversightSurfaceEngine
        return OversightSurfaceEngine()
    except Exception as e:
        logger.error("[oversight_bp] OversightSurfaceEngine load error: %s: %s", type(e).__name__, e)
        return None


def _require_auth(require_admin: bool = False):
    """
    Authenticate via X-API-Key using the governance RBAC layer.
    Returns (client_dict, None) on success or (None, error_response) on failure.
    """
    try:
        try:
            from api.gov_blueprint import _require_auth as _gov_auth
        except ImportError:
            from omnix_web.api.gov_blueprint import _require_auth as _gov_auth
        return _gov_auth(require_admin=require_admin)
    except Exception as e:
        logger.error("[oversight_bp] auth import error: %s: %s", type(e).__name__, e)
        return None, (jsonify({"error": "Authentication service unavailable", "status": 503}), 503)


def _safe_int(val, default: int, min_val: int = 1, max_val: int = 200) -> int:
    try:
        return max(min_val, min(max_val, int(val)))
    except (TypeError, ValueError):
        return default


@oversight_bp.route("/api/oversight/sessions", methods=["POST"])
def create_oversight_session():
    """
    Create a new oversight session for a decision requiring human review.

    Body (JSON):
        decision_id         str  required  — receipt ID or decision identifier
        domain              str  required  — governance domain
        original_decision   str  required  — APPROVED | BLOCKED | HOLD
        decision_snapshot   dict optional  — full decision payload for framing
        reviewer_id         str  optional  — pre-assign reviewer
        metadata            dict optional  — extra context

    Returns session_id, framing_score, framing_missing fields.
    """
    client, err = _require_auth()
    if err:
        return err

    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json", "status": 400}), 400

    body = request.get_json(force=True) or {}
    decision_id = str(body.get("decision_id", "")).strip()
    domain = str(body.get("domain", "")).strip()
    original_decision = str(body.get("original_decision", "")).strip().upper()

    if not decision_id:
        return jsonify({"error": "'decision_id' is required", "status": 400}), 400
    if not domain:
        return jsonify({"error": "'domain' is required", "status": 400}), 400
    if not original_decision:
        return jsonify({"error": "'original_decision' is required", "status": 400}), 400

    decision_snapshot = body.get("decision_snapshot")
    if decision_snapshot is not None and not isinstance(decision_snapshot, dict):
        return jsonify({"error": "'decision_snapshot' must be a JSON object", "status": 400}), 400

    metadata = body.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        return jsonify({"error": "'metadata' must be a JSON object", "status": 400}), 400

    ose = _load_ose()
    if not ose:
        return jsonify({"error": "Oversight Surface Engine unavailable", "status": 503}), 503

    try:
        session = ose.create_session(
            decision_id=decision_id,
            domain=domain,
            original_decision=original_decision,
            decision_snapshot=decision_snapshot,
            reviewer_id=body.get("reviewer_id") or client.get("client_id"),
            metadata=metadata,
        )
        return jsonify({"success": True, "session": session}), 201
    except ValueError as e:
        return jsonify({"error": str(e), "status": 400}), 400
    except Exception as e:
        logger.error("[oversight_bp] create_session: %s: %s", type(e).__name__, e)
        return jsonify({"error": "Internal server error", "status": 500}), 500


@oversight_bp.route("/api/oversight/sessions", methods=["GET"])
def list_oversight_sessions():
    """
    List oversight sessions with optional filters.

    Query params:
        status      PENDING | OPEN | SUBMITTED | EXPIRED
        domain      governance domain string
        reviewer_id reviewer identifier
        limit       1–200 (default 50)
    """
    client, err = _require_auth()
    if err:
        return err

    status = request.args.get("status", "").upper() or None
    domain = request.args.get("domain", "").strip() or None
    reviewer_id = request.args.get("reviewer_id", "").strip() or None
    limit = _safe_int(request.args.get("limit", 50), default=50)

    ose = _load_ose()
    if not ose:
        return jsonify({"error": "Oversight Surface Engine unavailable", "status": 503}), 503

    try:
        sessions = ose.list_sessions(
            status=status, domain=domain, reviewer_id=reviewer_id, limit=limit
        )
        return jsonify({
            "success": True,
            "sessions": sessions,
            "count": len(sessions),
        }), 200
    except Exception as e:
        logger.error("[oversight_bp] list_sessions: %s: %s", type(e).__name__, e)
        return jsonify({"error": "Internal server error", "status": 500}), 500


@oversight_bp.route("/api/oversight/sessions/<string:session_id>", methods=["GET"])
def get_oversight_session(session_id: str):
    """Return full session record including EQS and framing details."""
    client, err = _require_auth()
    if err:
        return err

    ose = _load_ose()
    if not ose:
        return jsonify({"error": "Oversight Surface Engine unavailable", "status": 503}), 503

    try:
        session = ose.get_session(session_id)
        return jsonify({"success": True, "session": session}), 200
    except ValueError as e:
        return jsonify({"error": str(e), "status": 404}), 404
    except Exception as e:
        logger.error("[oversight_bp] get_session: %s: %s", type(e).__name__, e)
        return jsonify({"error": "Internal server error", "status": 500}), 500


@oversight_bp.route("/api/oversight/sessions/<string:session_id>/open", methods=["POST"])
def open_oversight_session(session_id: str):
    """
    Mark session as OPEN — starts the deliberation timer.

    Call this endpoint when the oversight UI is actually displayed to the reviewer.
    The reviewer cannot submit until DELIBERATION_WINDOW_SECONDS have elapsed.
    """
    client, err = _require_auth()
    if err:
        return err

    ose = _load_ose()
    if not ose:
        return jsonify({"error": "Oversight Surface Engine unavailable", "status": 503}), 503

    try:
        result = ose.open_session(session_id)
        return jsonify({"success": True, **result}), 200
    except ValueError as e:
        return jsonify({"error": str(e), "status": 400}), 400
    except Exception as e:
        logger.error("[oversight_bp] open_session: %s: %s", type(e).__name__, e)
        return jsonify({"error": "Internal server error", "status": 500}), 500


@oversight_bp.route("/api/oversight/sessions/<string:session_id>/submit", methods=["POST"])
def submit_oversight_review(session_id: str):
    """
    Submit a human review decision.

    Body (JSON):
        action          str  required  — CONFIRMED | OVERRIDDEN | ESCALATED
        justification   str  required when action=OVERRIDDEN (min 50 chars)

    Enforces:
        - Deliberation window: must have been OPEN for ≥30 seconds
        - Override friction: OVERRIDDEN requires structured justification

    Returns eqs_score (Epistemic Quality Score) and audit_hash.
    """
    client, err = _require_auth()
    if err:
        return err

    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json", "status": 400}), 400

    body = request.get_json(force=True) or {}
    action = str(body.get("action", "")).strip().upper()
    justification = str(body.get("justification", "")).strip() or None

    if not action:
        return jsonify({"error": "'action' is required (CONFIRMED | OVERRIDDEN | ESCALATED)", "status": 400}), 400

    ose = _load_ose()
    if not ose:
        return jsonify({"error": "Oversight Surface Engine unavailable", "status": 503}), 503

    try:
        result = ose.submit_review(
            session_id=session_id,
            reviewer_id=client["client_id"],
            action=action,
            justification=justification,
        )
        return jsonify({"success": True, **result}), 200
    except ValueError as e:
        return jsonify({"error": str(e), "status": 400}), 400
    except Exception as e:
        logger.error("[oversight_bp] submit_review: %s: %s", type(e).__name__, e)
        return jsonify({"error": "Internal server error", "status": 500}), 500


@oversight_bp.route("/api/oversight/sessions/<string:session_id>/eqs", methods=["GET"])
def get_session_eqs(session_id: str):
    """
    Return Epistemic Quality Score breakdown for a submitted session.

    EQS (0.0–1.0) measures whether the oversight moment was genuinely deliberative:
        40% — deliberation time (saturates at 2× the minimum window)
        40% — framing completeness (required fields present)
        20% — justification quality (matters only for OVERRIDDEN)

    Labels: HIGH ≥0.85 | MEDIUM ≥0.60 | LOW ≥0.35 | MINIMAL <0.35
    """
    client, err = _require_auth()
    if err:
        return err

    ose = _load_ose()
    if not ose:
        return jsonify({"error": "Oversight Surface Engine unavailable", "status": 503}), 503

    try:
        session = ose.get_session(session_id)
    except ValueError as e:
        return jsonify({"error": str(e), "status": 404}), 404
    except Exception as e:
        logger.error("[oversight_bp] get_session_eqs load: %s: %s", type(e).__name__, e)
        return jsonify({"error": "Internal server error", "status": 500}), 500

    if session.get("status") != "SUBMITTED":
        return jsonify({
            "error": f"EQS is only available for SUBMITTED sessions (current: {session.get('status')})",
            "status": 400,
        }), 400

    try:
        from omnix_core.governance.oversight_surface import (
            DELIBERATION_WINDOW_SECONDS,
            FRAMING_REQUIRED_FIELDS,
        )
    except ImportError:
        DELIBERATION_WINDOW_SECONDS = 30
        FRAMING_REQUIRED_FIELDS = ["risk_score", "domain", "original_decision", "block_reason"]

    eqs = session.get("eqs_score") or 0.0
    delib = session.get("deliberation_seconds") or 0.0
    framing = session.get("framing_score") or 0.0
    action = session.get("action", "")
    justification = session.get("justification") or ""

    target = DELIBERATION_WINDOW_SECONDS * 2
    time_score = min(1.0, delib / max(target, 1))
    just_score = min(1.0, len(justification) / 200) if action == "OVERRIDDEN" else 1.0

    return jsonify({
        "success": True,
        "session_id": session_id,
        "eqs_score": round(eqs, 4),
        "eqs_label": session.get("eqs_label", "UNKNOWN"),
        "breakdown": {
            "time_score": round(time_score, 4),
            "framing_score": round(framing, 4),
            "justification_score": round(just_score, 4),
            "weights": {"time": 0.40, "framing": 0.40, "justification": 0.20},
        },
        "deliberation_seconds": round(delib, 2),
        "deliberation_window_seconds": DELIBERATION_WINDOW_SECONDS,
        "framing_required_fields": FRAMING_REQUIRED_FIELDS,
        "framing_missing": session.get("framing_missing", []),
        "action": action,
        "submitted_at": session.get("submitted_at"),
        "reviewer_id": session.get("reviewer_id"),
    }), 200


@oversight_bp.route("/api/oversight/sessions/expire", methods=["POST"])
def expire_stale_sessions():
    """
    Mark all stale PENDING/OPEN sessions older than SESSION_EXPIRY_HOURS as EXPIRED.
    Admin only.
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err

    ose = _load_ose()
    if not ose:
        return jsonify({"error": "Oversight Surface Engine unavailable", "status": 503}), 503

    try:
        count = ose.expire_stale_sessions()
        return jsonify({"success": True, "expired_count": count}), 200
    except Exception as e:
        logger.error("[oversight_bp] expire_stale_sessions: %s: %s", type(e).__name__, e)
        return jsonify({"error": "Internal server error", "status": 500}), 500
