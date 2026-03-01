"""
OMNIX Governance Reporting API — Module 5 Blueprint.

POST /api/governance/reports                               — Generate compliance report
GET  /api/governance/reports                               — List reports (metadata only)
GET  /api/governance/reports/<report_id>                   — Full report
GET  /api/governance/reports/<report_id>/export            — Export JSON or CSV
GET  /api/governance/reports/<report_id>/lineage/<receipt_id> — Decision lineage trace

NIST AI RMF: GOVERN | ISO 42001: §10 | EU AI Act: Art. 12 | ADR-029
"""

import logging
import os
import sys
from datetime import datetime, timezone

from flask import Blueprint, Response, jsonify, request

from .auth_rbac import authenticate_client, update_last_seen

logger = logging.getLogger(__name__)

governance_reports_bp = Blueprint("governance_reports", __name__)

_ENGINE = None


def _load_engine():
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE
    try:
        import importlib.util
        _root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(_root, "omnix_core", "governance", "reporting_engine.py")
        spec = importlib.util.spec_from_file_location("_omnix_reporting_engine", path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_omnix_reporting_engine"] = mod
        spec.loader.exec_module(mod)
        _ENGINE = mod.GovernanceReportingEngine
        return _ENGINE
    except Exception as e:
        logger.error(f"Failed to load GovernanceReportingEngine: {e}")
        return None


def _require_auth(require_admin: bool = False):
    api_key = request.headers.get("X-API-Key", "")
    client = authenticate_client(api_key)
    if client is None:
        return None, (jsonify({"error": "Unauthorized — provide a valid X-API-Key", "status": 401}), 401)
    if require_admin and client.get("role") != "admin":
        return None, (jsonify({"error": "Forbidden — admin role required", "status": 403}), 403)
    return client, None


@governance_reports_bp.route("/api/governance/reports", methods=["POST"])
def generate_report():
    """
    Generate a compliance report for a specified period.
    Body: { "period_start": ISO8601, "period_end": ISO8601, "type": "COMPLIANCE" }
    """
    client, err = _require_auth()
    if err:
        return err
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json", "status": 400}), 400
    body = request.get_json(force=True) or {}

    try:
        period_start_str = body.get("period_start") or body.get("from")
        period_end_str = body.get("period_end") or body.get("to")
        if not period_start_str or not period_end_str:
            return jsonify({"error": "'period_start' and 'period_end' are required (ISO 8601 format)", "status": 400}), 400
        period_start = datetime.fromisoformat(period_start_str.replace("Z", "+00:00"))
        period_end = datetime.fromisoformat(period_end_str.replace("Z", "+00:00"))
    except ValueError as e:
        return jsonify({"error": f"Invalid date format: {e}. Use ISO 8601 (e.g. 2026-01-01T00:00:00Z)", "status": 400}), 400

    if period_start >= period_end:
        return jsonify({"error": "period_start must be before period_end", "status": 400}), 400

    report_type = str(body.get("type", "COMPLIANCE")).upper()[:32]

    GovernanceReportingEngine = _load_engine()
    if not GovernanceReportingEngine:
        return jsonify({"error": "Reporting engine unavailable", "status": 503}), 503

    try:
        engine = GovernanceReportingEngine()
        report = engine.generate_report(
            client_id=client["client_id"],
            period_start=period_start,
            period_end=period_end,
            report_type=report_type,
            generated_by=client["client_id"],
        )
        update_last_seen(client["client_id"])
        return jsonify(report), 201
    except Exception as e:
        logger.error(f"generate_report error: {e}")
        return jsonify({"error": "Internal error generating report", "status": 500}), 500


@governance_reports_bp.route("/api/governance/reports", methods=["GET"])
def list_reports():
    """List compliance reports for the authenticated client (metadata only, no content)."""
    client, err = _require_auth()
    if err:
        return err
    GovernanceReportingEngine = _load_engine()
    if not GovernanceReportingEngine:
        return jsonify({"error": "Reporting engine unavailable", "status": 503}), 503
    try:
        engine = GovernanceReportingEngine()
        reports = engine.list_reports(client["client_id"])
        return jsonify({
            "client_id": client["client_id"],
            "total": len(reports),
            "reports": reports,
            "framework": "NIST AI RMF GOVERN | ISO 42001 §10 | EU AI Act Art. 12",
        }), 200
    except Exception as e:
        logger.error(f"list_reports error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500


@governance_reports_bp.route("/api/governance/reports/<string:report_id>", methods=["GET"])
def get_report(report_id: str):
    """Retrieve a full compliance report by ID."""
    client, err = _require_auth()
    if err:
        return err
    GovernanceReportingEngine = _load_engine()
    if not GovernanceReportingEngine:
        return jsonify({"error": "Reporting engine unavailable", "status": 503}), 503
    try:
        engine = GovernanceReportingEngine()
        report = engine.get_report(report_id, client["client_id"])
        if not report:
            return jsonify({"error": f"Report '{report_id}' not found", "status": 404}), 404
        return jsonify(report), 200
    except Exception as e:
        logger.error(f"get_report error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500


@governance_reports_bp.route("/api/governance/reports/<string:report_id>/export", methods=["GET"])
def export_report(report_id: str):
    """
    Export a report in JSON or CSV format.
    Query param: ?format=json (default) or ?format=csv
    CSV exports the decision lineage section only.
    """
    client, err = _require_auth()
    if err:
        return err
    fmt = request.args.get("format", "json").lower()
    GovernanceReportingEngine = _load_engine()
    if not GovernanceReportingEngine:
        return jsonify({"error": "Reporting engine unavailable", "status": 503}), 503
    try:
        engine = GovernanceReportingEngine()
        if fmt == "csv":
            csv_data = engine.export_csv(report_id, client["client_id"])
            if csv_data is None:
                return jsonify({"error": f"Report '{report_id}' not found", "status": 404}), 404
            return Response(
                csv_data,
                mimetype="text/csv",
                headers={"Content-Disposition": f"attachment; filename=omnix_governance_{report_id}.csv"},
            )
        else:
            report = engine.get_report(report_id, client["client_id"])
            if not report:
                return jsonify({"error": f"Report '{report_id}' not found", "status": 404}), 404
            import json
            json_str = json.dumps(report, default=str, indent=2)
            return Response(
                json_str,
                mimetype="application/json",
                headers={"Content-Disposition": f"attachment; filename=omnix_governance_{report_id}.json"},
            )
    except Exception as e:
        logger.error(f"export_report error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500


@governance_reports_bp.route("/api/governance/reports/<string:report_id>/lineage/<string:receipt_id>", methods=["GET"])
def get_lineage(report_id: str, receipt_id: str):
    """
    Build full decision lineage for a receipt:
    signal → checkpoints → veto_chain → decision → human override → verification URL
    EU AI Act Art. 12 — complete traceability record.
    """
    client, err = _require_auth()
    if err:
        return err
    GovernanceReportingEngine = _load_engine()
    if not GovernanceReportingEngine:
        return jsonify({"error": "Reporting engine unavailable", "status": 503}), 503
    try:
        engine = GovernanceReportingEngine()
        lineage = engine.build_lineage(receipt_id, client["client_id"])
        return jsonify(lineage), 200
    except Exception as e:
        logger.error(f"get_lineage error: {e}")
        return jsonify({"error": "Internal error", "status": 500}), 500
