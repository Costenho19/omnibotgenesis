"""
OMNIX Human Oversight API — Module 3 Blueprint.

POST /api/governance/overrides                — Create PQC-signed override (admin)
GET  /api/governance/overrides                — List overrides with pagination
GET  /api/governance/overrides/<override_id>  — Override detail + signature verification

GET  /api/governance/meta-coherence           — MCM: second-order frame stability audit (ADR-117)
GET  /api/governance/meta-coherence/<domain>  — MCM analysis for a specific domain

EU AI Act: Art. 14 | NIST AI RMF: MANAGE | ADR-029 | ADR-117
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


# ── Meta-Coherence Monitor endpoints (ADR-117) ─────────────────────────────────

def _load_mcm():
    """Lazy-load MetaCoherenceMonitor to avoid import cost on every request."""
    try:
        from omnix_core.governance.meta_coherence_monitor import MetaCoherenceMonitor
        return MetaCoherenceMonitor
    except ImportError as exc:
        logger.warning(f"MetaCoherenceMonitor unavailable: {exc}")
        return None


def _report_to_dict(report) -> dict:
    """Serialize a MetaCoherenceReport to a JSON-safe dict."""
    def _vd(vd):
        if not vd:
            return None
        return {
            "sufficient_data":    vd.sufficient_data,
            "error":              vd.error,
            "ref_blocked_pct":    vd.ref_blocked_pct,
            "cur_blocked_pct":    vd.cur_blocked_pct,
            "ref_held_pct":       vd.ref_held_pct,
            "cur_held_pct":       vd.cur_held_pct,
            "composite_drift":    round(vd.composite_drift, 2),
            "alert_level":        vd.alert_level,
            "reference_total":    vd.reference_total,
            "current_total":      vd.current_total,
        }

    def _vp(vp):
        if not vp:
            return None
        return {
            "error":           vp.error,
            "asymmetry_score": round(vp.asymmetry_score, 2),
            "silenced_gates":  vp.silenced_gates,
            "amplified_gates": vp.amplified_gates,
            "alert_level":     vp.alert_level,
        }

    def _rl(rl):
        if not rl:
            return None
        return {
            "error":                       rl.error,
            "calibration_age_hours":       round(rl.calibration_age_hours, 1),
            "max_age_hours":               rl.max_age_hours,
            "age_fraction":                round(rl.age_fraction, 3),
            "recalibration_anchoring_risk": rl.recalibration_anchoring_risk,
            "alert_level":                 rl.alert_level,
            "snapshot_id":                 rl.snapshot_id,
        }

    def _sig(s):
        return {
            "signal_id":   s.signal_id,
            "severity":    s.severity,
            "description": s.description,
            "evidence":    s.evidence,
        }

    return {
        "report_id":              report.report_id,
        "domain":                 report.domain,
        "generated_at":           report.generated_at,
        "mcm_version":            report.mcm_version,
        "alert_level":            report.alert_level,
        "composite_score":        round(report.composite_score, 2),
        "evaluation_frame_stable": report.evaluation_frame_stable,
        "executive_summary":      report.executive_summary,
        "verdict_distribution":   _vd(report.verdict_distribution),
        "veto_pattern":           _vp(report.veto_pattern),
        "reference_legitimacy":   _rl(report.reference_legitimacy),
        "transition_signatures":  [_sig(s) for s in (report.transition_signatures or [])],
        "adr": "ADR-117",
    }


@governance_oversight_bp.route("/api/governance/meta-coherence", methods=["GET"])
def meta_coherence_all():
    """
    GET /api/governance/meta-coherence

    Run Meta-Coherence Monitor across all active domains and return
    a summary report + per-domain detail.

    ADR-117 | Second-order governance perception stability audit.
    """
    client, err = _require_auth()
    if err:
        return err

    MCM = _load_mcm()
    if not MCM:
        return jsonify({"error": "MetaCoherenceMonitor unavailable", "status": 503}), 503

    try:
        monitor = MCM()
        domains = monitor._get_active_domains()

        reference_days = int(request.args.get("reference_days", 30))
        current_days   = int(request.args.get("current_days",   14))
        persist        = request.args.get("persist", "false").lower() == "true"

        domain_reports = []
        worst_alert    = "OK"
        _order         = {"OK": 0, "WARNING": 1, "CRITICAL": 2, "UNKNOWN": -1}

        for domain in domains:
            report = monitor.run_full_analysis(
                domain,
                reference_days=reference_days,
                current_days=current_days,
            )
            if persist:
                monitor.persist_to_db(report)

            domain_reports.append(_report_to_dict(report))
            if _order.get(report.alert_level, -1) > _order.get(worst_alert, 0):
                worst_alert = report.alert_level

        return jsonify({
            "status":          "ok",
            "overall_alert":   worst_alert,
            "domains_scanned": len(domain_reports),
            "reference_days":  reference_days,
            "current_days":    current_days,
            "persisted":       persist,
            "reports":         domain_reports,
            "adr":             "ADR-117",
        }), 200

    except Exception as exc:
        logger.error(f"meta_coherence_all error: {exc}")
        return jsonify({"error": "Internal error", "status": 500}), 500


@governance_oversight_bp.route("/api/governance/meta-coherence/<string:domain>", methods=["GET"])
def meta_coherence_domain(domain: str):
    """
    GET /api/governance/meta-coherence/<domain>

    Run Meta-Coherence Monitor for a single domain.
    Optional query params: reference_days (default 30), current_days (default 14), persist (false).

    ADR-117 | Second-order governance perception stability audit.
    """
    client, err = _require_auth()
    if err:
        return err

    MCM = _load_mcm()
    if not MCM:
        return jsonify({"error": "MetaCoherenceMonitor unavailable", "status": 503}), 503

    try:
        monitor = MCM()
        reference_days = int(request.args.get("reference_days", 30))
        current_days   = int(request.args.get("current_days",   14))
        persist        = request.args.get("persist", "false").lower() == "true"

        report = monitor.run_full_analysis(
            domain,
            reference_days=reference_days,
            current_days=current_days,
        )

        if persist:
            monitor.persist_to_db(report)

        return jsonify(_report_to_dict(report)), 200

    except Exception as exc:
        logger.error(f"meta_coherence_domain({domain}) error: {exc}")
        return jsonify({"error": "Internal error", "status": 500}), 500
