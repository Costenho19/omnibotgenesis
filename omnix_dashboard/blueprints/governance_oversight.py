"""
OMNIX Human Oversight API — Module 3 Blueprint.

POST /api/governance/overrides                — Create PQC-signed override (admin)
GET  /api/governance/overrides                — List overrides with pagination
GET  /api/governance/overrides/<override_id>  — Override detail + signature verification

EU AI Act: Art. 14 | NIST AI RMF: MANAGE | ADR-029
"""

import logging
import os
import sys

from flask import Blueprint, jsonify, request

from .auth_rbac import authenticate_client, update_last_seen

logger = logging.getLogger(__name__)

governance_oversight_bp = Blueprint("governance_oversight", __name__)

_ENGINE = None


def _load_engine():
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE
    try:
        import importlib.util
        _root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(_root, "omnix_core", "governance", "human_oversight.py")
        spec = importlib.util.spec_from_file_location("_omnix_human_oversight", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_omnix_human_oversight"] = mod
        spec.loader.exec_module(mod)
        _ENGINE = mod.HumanOversightEngine
        return _ENGINE
    except Exception as e:
        logger.error(f"Failed to load HumanOversightEngine: {e}")
        return None


def _require_auth(require_admin: bool = False):
    api_key = request.headers.get("X-API-Key", "")
    client = authenticate_client(api_key)
    if client is None:
        return None, (jsonify({"error": "Unauthorized — provide a valid X-API-Key", "status": 401}), 401)
    if require_admin and client.get("role") != "admin":
        return None, (jsonify({"error": "Forbidden — admin role required", "status": 403}), 403)
    return client, None


@governance_oversight_bp.route("/api/governance/overrides", methods=["POST"])
def create_override():
    """
    Create a PQC-signed human oversight override record.
    Admin only. Justification must be at least 50 characters.
    The original decision receipt remains immutable in the PQC hash chain.
    """
    client, err = _require_auth(require_admin=True)
    if err:
        return err
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json", "status": 400}), 400
    body = request.get_json(force=True) or {}
    required = ["receipt_id", "decision_before", "decision_after", "justification"]
    missing = [f for f in required if not body.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}", "status": 400}), 400

    HumanOversightEngine = _load_engine()
    if not HumanOversightEngine:
        return jsonify({"error": "Human oversight engine unavailable", "status": 503}), 503

    try:
        engine = HumanOversightEngine()
        result = engine.create_override(
            client_id=client["client_id"],
            receipt_id=str(body["receipt_id"])[:128],
            decision_before=str(body["decision_before"])[:32].upper(),
            decision_after=str(body["decision_after"])[:32].upper(),
            justification=str(body["justification"]),
            overridden_by=client["client_id"],
            role=client.get("role", "admin"),
        )
        update_last_seen(client["client_id"])
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e), "status": 400}), 400
    except Exception as e:
        logger.error(f"create_override error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500


@governance_oversight_bp.route("/api/governance/overrides", methods=["GET"])
def list_overrides():
    """List override records for the authenticated client with pagination."""
    client, err = _require_auth()
    if err:
        return err
    try:
        limit = min(int(request.args.get("limit", 20)), 100)
        offset = max(int(request.args.get("offset", 0)), 0)
    except ValueError:
        return jsonify({"error": "limit and offset must be integers", "status": 400}), 400

    HumanOversightEngine = _load_engine()
    if not HumanOversightEngine:
        return jsonify({"error": "Human oversight engine unavailable", "status": 503}), 503

    try:
        engine = HumanOversightEngine()
        overrides = engine.list_overrides(client["client_id"], limit=limit, offset=offset)
        return jsonify({
            "client_id": client["client_id"],
            "total_returned": len(overrides),
            "limit": limit,
            "offset": offset,
            "overrides": overrides,
            "framework": "EU AI Act Art. 14 — Human oversight audit trail",
        }), 200
    except Exception as e:
        logger.error(f"list_overrides error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500


@governance_oversight_bp.route("/api/governance/overrides/<string:override_id>", methods=["GET"])
def get_override(override_id: str):
    """Get full override detail with content hash verification."""
    client, err = _require_auth()
    if err:
        return err

    HumanOversightEngine = _load_engine()
    if not HumanOversightEngine:
        return jsonify({"error": "Human oversight engine unavailable", "status": 503}), 503

    try:
        engine = HumanOversightEngine()
        override = engine.get_override(override_id, client["client_id"])
        if not override:
            return jsonify({"error": f"Override '{override_id}' not found", "status": 404}), 404

        verification = engine.verify_override(override_id)
        override["integrity_check"] = verification
        return jsonify(override), 200
    except Exception as e:
        logger.error(f"get_override error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500
