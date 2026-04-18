"""
OMNIX Governance Metrics API — Module 2 Blueprint.

GET  /api/governance/metrics             — Performance metrics (last N days)
GET  /api/governance/metrics/live        — Live stats from decision_receipts
POST /api/governance/metrics             — Record manual metrics snapshot (admin)
POST /api/governance/drift/detect        — Run drift detection
GET  /api/governance/drift/logs          — Drift log history

NIST AI RMF: MEASURE | ISO 42001: §9.1 | ADR-029
"""

import logging
import os
import sys

from flask import Blueprint, jsonify, request

from .auth_rbac import authenticate_client, update_last_seen

logger = logging.getLogger(__name__)

governance_metrics_bp = Blueprint("governance_metrics", __name__)

_ENGINE = None


def _load_engine():
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE
    try:
        import importlib.util
        _root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(_root, "omnix_core", "governance", "measurement_monitoring.py")
        spec = importlib.util.spec_from_file_location("_omnix_measurement", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_omnix_measurement"] = mod
        spec.loader.exec_module(mod)
        _ENGINE = mod.MeasurementMonitoringEngine
        return _ENGINE
    except Exception as e:
        logger.error(f"Failed to load MeasurementMonitoringEngine: {e}")
        return None


def _require_auth(require_admin: bool = False):
    api_key = request.headers.get("X-API-Key", "")
    client = authenticate_client(api_key)
    if client is None:
        return None, (jsonify({"error": "Unauthorized — provide a valid X-API-Key", "status": 401}), 401)
    if require_admin and client.get("role") != "admin":
        return None, (jsonify({"error": "Forbidden — admin role required", "status": 403}), 403)
    return client, None


@governance_metrics_bp.route("/api/governance/metrics", methods=["GET"])
def get_metrics():
    """Return stored performance metrics grouped by checkpoint."""
    client, err = _require_auth()
    if err:
        return err
    try:
        days = min(int(request.args.get("days", 30)), 365)
    except ValueError:
        return jsonify({"error": "days must be an integer", "status": 400}), 400
    MeasurementMonitoringEngine = _load_engine()
    if not MeasurementMonitoringEngine:
        return jsonify({"error": "Metrics engine unavailable", "status": 503}), 503
    try:
        engine = MeasurementMonitoringEngine()
        metrics = engine.get_metrics(client["client_id"], days=days)
        update_last_seen(client["client_id"])
        return jsonify({
            "client_id": client["client_id"],
            "period_days": days,
            "checkpoints": metrics,
            "framework": "NIST AI RMF MEASURE — ISO 42001 §9.1",
        }), 200
    except Exception as e:
        logger.error(f"get_metrics error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500


@governance_metrics_bp.route("/api/governance/metrics/live", methods=["GET"])
def get_live_metrics():
    """Compute live approval/block stats directly from decision_receipts."""
    client, err = _require_auth()
    if err:
        return err
    try:
        days = min(int(request.args.get("days", 30)), 365)
    except ValueError:
        return jsonify({"error": "days must be an integer", "status": 400}), 400
    MeasurementMonitoringEngine = _load_engine()
    if not MeasurementMonitoringEngine:
        return jsonify({"error": "Metrics engine unavailable", "status": 503}), 503
    try:
        engine = MeasurementMonitoringEngine()
        stats = engine.compute_checkpoint_stats(client["client_id"], days=days)
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"get_live_metrics error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500


@governance_metrics_bp.route("/api/governance/metrics", methods=["POST"])
def record_metrics():
    """Record a manual performance metrics snapshot. Admin only."""
    client, err = _require_auth(require_admin=True)
    if err:
        return err
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json", "status": 400}), 400
    body = request.get_json(force=True) or {}
    required = ["checkpoint_id", "approval_rate", "block_rate", "avg_score", "window_start", "window_end"]
    missing = [f for f in required if f not in body]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}", "status": 400}), 400
    MeasurementMonitoringEngine = _load_engine()
    if not MeasurementMonitoringEngine:
        return jsonify({"error": "Metrics engine unavailable", "status": 503}), 503
    try:
        from datetime import datetime
        engine = MeasurementMonitoringEngine()
        result = engine.record_metrics(
            client_id=client["client_id"],
            checkpoint_id=str(body["checkpoint_id"])[:32],
            approval_rate=float(body["approval_rate"]),
            block_rate=float(body["block_rate"]),
            avg_score=float(body["avg_score"]),
            window_start=datetime.fromisoformat(body["window_start"]),
            window_end=datetime.fromisoformat(body["window_end"]),
        )
        update_last_seen(client["client_id"])
        return jsonify({"metric": result}), 201
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e), "status": 400}), 400
    except Exception as e:
        logger.error(f"record_metrics error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500


@governance_metrics_bp.route("/api/governance/drift/detect", methods=["POST"])
def detect_drift():
    """Run drift detection on a set of signal values vs baseline."""
    client, err = _require_auth()
    if err:
        return err
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json", "status": 400}), 400
    body = request.get_json(force=True) or {}
    signal_name = str(body.get("signal_name", "")).strip()
    current_values = body.get("current_values", [])
    if not signal_name:
        return jsonify({"error": "'signal_name' is required", "status": 400}), 400
    if not isinstance(current_values, list) or len(current_values) < 2:
        return jsonify({"error": "'current_values' must be a list with at least 2 values", "status": 400}), 400
    MeasurementMonitoringEngine = _load_engine()
    if not MeasurementMonitoringEngine:
        return jsonify({"error": "Metrics engine unavailable", "status": 503}), 503
    try:
        engine = MeasurementMonitoringEngine()
        result = engine.detect_drift(
            client_id=client["client_id"],
            signal_name=signal_name,
            current_values=[float(v) for v in current_values],
            baseline_mean=body.get("baseline_mean"),
            baseline_std=body.get("baseline_std"),
        )
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"detect_drift error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500


@governance_metrics_bp.route("/api/governance/drift/logs", methods=["GET"])
def get_drift_logs():
    """Return drift detection history, optionally filtered to alerts only."""
    client, err = _require_auth()
    if err:
        return err
    alert_only = request.args.get("alert_only", "false").lower() == "true"
    MeasurementMonitoringEngine = _load_engine()
    if not MeasurementMonitoringEngine:
        return jsonify({"error": "Metrics engine unavailable", "status": 503}), 503
    try:
        engine = MeasurementMonitoringEngine()
        logs = engine.get_drift_logs(client["client_id"], alert_only=alert_only)
        return jsonify({
            "client_id": client["client_id"],
            "alert_only": alert_only,
            "total": len(logs),
            "drift_logs": logs,
        }), 200
    except Exception as e:
        logger.error(f"get_drift_logs error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500
