"""
OMNIX Incident Management API — Module 4 Blueprint.

POST /api/governance/incidents                      — Report new incident
GET  /api/governance/incidents                      — List incidents (with filters)
GET  /api/governance/incidents/<incident_id>        — Incident detail + reviews
POST /api/governance/incidents/<incident_id>/review — Add review (admin)
POST /api/governance/incidents/<incident_id>/resolve — Resolve incident (admin)

EU AI Act: Art. 9 + Art. 62 | NIST AI RMF: MANAGE | ADR-029
"""

import logging
import os
import sys

from flask import Blueprint, jsonify, request

from .auth_rbac import authenticate_client, update_last_seen

logger = logging.getLogger(__name__)

governance_incidents_bp = Blueprint("governance_incidents", __name__)

_ENGINE = None


def _load_engine():
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE
    try:
        import importlib.util
        _root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(_root, "omnix_core", "governance", "incident_management.py")
        spec = importlib.util.spec_from_file_location("_omnix_incident_mgmt", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_omnix_incident_mgmt"] = mod
        spec.loader.exec_module(mod)
        _ENGINE = mod.IncidentManagementEngine
        return _ENGINE
    except Exception as e:
        logger.error(f"Failed to load IncidentManagementEngine: {e}")
        return None


def _require_auth(require_admin: bool = False):
    api_key = request.headers.get("X-API-Key", "")
    client = authenticate_client(api_key)
    if client is None:
        return None, (jsonify({"error": "Unauthorized — provide a valid X-API-Key", "status": 401}), 401)
    if require_admin and client.get("role") != "admin":
        return None, (jsonify({"error": "Forbidden — admin role required", "status": 403}), 403)
    return client, None


@governance_incidents_bp.route("/api/governance/incidents", methods=["POST"])
def report_incident():
    """Report a new governance incident."""
    client, err = _require_auth()
    if err:
        return err
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json", "status": 400}), 400
    body = request.get_json(force=True) or {}
    title = str(body.get("title", "")).strip()
    severity = str(body.get("severity", "")).upper()
    if not title:
        return jsonify({"error": "'title' is required", "status": 400}), 400
    if severity not in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"):
        return jsonify({"error": "severity must be CRITICAL, HIGH, MEDIUM, LOW, or INFORMATIONAL", "status": 400}), 400

    IncidentManagementEngine = _load_engine()
    if not IncidentManagementEngine:
        return jsonify({"error": "Incident management engine unavailable", "status": 503}), 503

    try:
        engine = IncidentManagementEngine()
        incident = engine.report_incident(
            client_id=client["client_id"],
            title=title[:256],
            description=str(body.get("description", "")),
            severity=severity,
            related_receipt_id=str(body["related_receipt_id"])[:128] if body.get("related_receipt_id") else None,
            reported_by=client["client_id"],
        )
        update_last_seen(client["client_id"])
        return jsonify(incident), 201
    except ValueError as e:
        return jsonify({"error": str(e), "status": 400}), 400
    except Exception as e:
        logger.error(f"report_incident error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500


@governance_incidents_bp.route("/api/governance/incidents", methods=["GET"])
def list_incidents():
    """List incidents with optional filters by status and severity."""
    client, err = _require_auth()
    if err:
        return err
    status = request.args.get("status")
    severity = request.args.get("severity")
    try:
        limit = min(int(request.args.get("limit", 50)), 200)
        offset = max(int(request.args.get("offset", 0)), 0)
    except ValueError:
        return jsonify({"error": "limit and offset must be integers", "status": 400}), 400

    IncidentManagementEngine = _load_engine()
    if not IncidentManagementEngine:
        return jsonify({"error": "Incident management engine unavailable", "status": 503}), 503

    try:
        engine = IncidentManagementEngine()
        incidents = engine.list_incidents(
            client["client_id"],
            status=status,
            severity=severity,
            limit=limit,
            offset=offset,
        )
        return jsonify({
            "client_id": client["client_id"],
            "total_returned": len(incidents),
            "filters": {"status": status, "severity": severity},
            "incidents": incidents,
            "framework": "EU AI Act Art. 9 + Art. 62 — Incident management",
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e), "status": 400}), 400
    except Exception as e:
        logger.error(f"list_incidents error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500


@governance_incidents_bp.route("/api/governance/incidents/<string:incident_id>", methods=["GET"])
def get_incident(incident_id: str):
    """Get incident detail including all reviews."""
    client, err = _require_auth()
    if err:
        return err
    IncidentManagementEngine = _load_engine()
    if not IncidentManagementEngine:
        return jsonify({"error": "Incident management engine unavailable", "status": 503}), 503
    try:
        engine = IncidentManagementEngine()
        incident = engine.get_incident(incident_id, client["client_id"])
        if not incident:
            return jsonify({"error": f"Incident '{incident_id}' not found", "status": 404}), 404
        return jsonify(incident), 200
    except Exception as e:
        logger.error(f"get_incident error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500


@governance_incidents_bp.route("/api/governance/incidents/<string:incident_id>/review", methods=["POST"])
def add_review(incident_id: str):
    """Add a review to an incident. Admin only."""
    client, err = _require_auth(require_admin=True)
    if err:
        return err
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json", "status": 400}), 400
    body = request.get_json(force=True) or {}
    findings = str(body.get("findings", "")).strip()
    if not findings:
        return jsonify({"error": "'findings' is required", "status": 400}), 400

    IncidentManagementEngine = _load_engine()
    if not IncidentManagementEngine:
        return jsonify({"error": "Incident management engine unavailable", "status": 503}), 503

    try:
        engine = IncidentManagementEngine()
        review = engine.add_review(
            incident_id=incident_id,
            reviewer=client["client_id"],
            findings=findings,
            corrective_actions=body.get("corrective_actions", []),
        )
        return jsonify(review), 201
    except ValueError as e:
        return jsonify({"error": str(e), "status": 404}), 404
    except Exception as e:
        logger.error(f"add_review error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500


@governance_incidents_bp.route("/api/governance/incidents/<string:incident_id>/resolve", methods=["POST"])
def resolve_incident(incident_id: str):
    """Mark an incident as resolved. Admin only."""
    client, err = _require_auth(require_admin=True)
    if err:
        return err
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json", "status": 400}), 400
    body = request.get_json(force=True) or {}
    resolution_note = str(body.get("resolution_note", "")).strip()
    if not resolution_note:
        return jsonify({"error": "'resolution_note' is required", "status": 400}), 400

    IncidentManagementEngine = _load_engine()
    if not IncidentManagementEngine:
        return jsonify({"error": "Incident management engine unavailable", "status": 503}), 503

    try:
        engine = IncidentManagementEngine()
        result = engine.resolve_incident(
            incident_id=incident_id,
            resolved_by=client["client_id"],
            resolution_note=resolution_note,
        )
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e), "status": 400}), 400
    except Exception as e:
        logger.error(f"resolve_incident error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500
