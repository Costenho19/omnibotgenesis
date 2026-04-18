"""
OMNIX Governance Risk Map API — Module 1 Blueprint.

GET  /api/governance/risk-map             — List client's risk maps
GET  /api/governance/risk-map/<use_case>  — Get specific risk map
POST /api/governance/risk-map             — Create/update risk map (admin)
POST /api/governance/risk-map/classify    — Classify signals in real-time

NIST AI RMF: MAP | ISO 42001: §6.1 | ADR-029
"""

import logging
import os
import sys

from flask import Blueprint, jsonify, request

from .auth_rbac import authenticate_client, update_last_seen

logger = logging.getLogger(__name__)

governance_risk_bp = Blueprint("governance_risk", __name__)

_ENGINE = None


def _load_engine():
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE
    try:
        import importlib.util
        _root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(_root, "omnix_core", "governance", "risk_mapping.py")
        spec = importlib.util.spec_from_file_location("_omnix_risk_mapping", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_omnix_risk_mapping"] = mod
        spec.loader.exec_module(mod)
        _ENGINE = mod.RiskMappingEngine
        return _ENGINE
    except Exception as e:
        logger.error(f"Failed to load RiskMappingEngine: {e}")
        return None


def _require_auth(require_admin: bool = False):
    api_key = request.headers.get("X-API-Key", "")
    client = authenticate_client(api_key)
    if client is None:
        return None, (jsonify({"error": "Unauthorized — provide a valid X-API-Key", "status": 401}), 401)
    if require_admin and client.get("role") != "admin":
        return None, (jsonify({"error": "Forbidden — admin role required", "status": 403}), 403)
    return client, None


@governance_risk_bp.route("/api/governance/risk-map", methods=["GET"])
def list_risk_maps():
    """List all risk maps for the authenticated client."""
    client, err = _require_auth()
    if err:
        return err
    RiskMappingEngine = _load_engine()
    if not RiskMappingEngine:
        return jsonify({"error": "Risk mapping engine unavailable", "status": 503}), 503
    try:
        engine = RiskMappingEngine()
        maps = engine.get_risk_map(client["client_id"])
        update_last_seen(client["client_id"])
        return jsonify({
            "client_id": client["client_id"],
            "total": len(maps),
            "risk_maps": maps,
            "framework": "NIST AI RMF MAP — ISO 42001 §6.1",
        }), 200
    except Exception as e:
        logger.error(f"list_risk_maps error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500


@governance_risk_bp.route("/api/governance/risk-map/<string:use_case>", methods=["GET"])
def get_risk_map(use_case: str):
    """Get a specific risk map by use_case."""
    client, err = _require_auth()
    if err:
        return err
    RiskMappingEngine = _load_engine()
    if not RiskMappingEngine:
        return jsonify({"error": "Risk mapping engine unavailable", "status": 503}), 503
    try:
        engine = RiskMappingEngine()
        maps = engine.get_risk_map(client["client_id"], use_case=use_case)
        if not maps:
            return jsonify({"error": f"No risk map found for use_case='{use_case}'", "status": 404}), 404
        return jsonify({"risk_map": maps[0]}), 200
    except Exception as e:
        logger.error(f"get_risk_map error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500


@governance_risk_bp.route("/api/governance/risk-map", methods=["POST"])
def upsert_risk_map():
    """Create or update a risk map entry. Admin only."""
    client, err = _require_auth(require_admin=True)
    if err:
        return err
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json", "status": 400}), 400
    body = request.get_json(force=True) or {}
    use_case = str(body.get("use_case", "")).strip()[:128]
    classification = str(body.get("classification", "")).upper()
    if not use_case:
        return jsonify({"error": "'use_case' is required", "status": 400}), 400
    if classification not in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        return jsonify({"error": "classification must be CRITICAL, HIGH, MEDIUM, or LOW", "status": 400}), 400
    RiskMappingEngine = _load_engine()
    if not RiskMappingEngine:
        return jsonify({"error": "Risk mapping engine unavailable", "status": 503}), 503
    try:
        engine = RiskMappingEngine()
        result = engine.upsert_risk_map(
            client_id=client["client_id"],
            use_case=use_case,
            classification=classification,
            impact_financial=int(body.get("impact_financial", 50)),
            impact_operational=int(body.get("impact_operational", 50)),
            impact_regulatory=int(body.get("impact_regulatory", 50)),
            stakeholders=body.get("stakeholders", []),
            thresholds=body.get("thresholds", {}),
        )
        update_last_seen(client["client_id"])
        return jsonify({"risk_map": result, "action": "created_or_updated"}), 200
    except ValueError as e:
        return jsonify({"error": str(e), "status": 400}), 400
    except Exception as e:
        logger.error(f"upsert_risk_map error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500


@governance_risk_bp.route("/api/governance/risk-map/classify", methods=["POST"])
def classify_risk():
    """Classify normalized signals into a risk tier in real-time."""
    client, err = _require_auth()
    if err:
        return err
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json", "status": 400}), 400
    body = request.get_json(force=True) or {}
    signals = body.get("signals", {})
    if not signals:
        return jsonify({"error": "'signals' object is required", "status": 400}), 400
    RiskMappingEngine = _load_engine()
    if not RiskMappingEngine:
        return jsonify({"error": "Risk mapping engine unavailable", "status": 503}), 503
    try:
        engine = RiskMappingEngine()
        result = engine.classify_risk(signals)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"classify_risk error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500
