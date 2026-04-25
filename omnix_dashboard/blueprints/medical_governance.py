"""
OMNIX Medical AI Governance API Blueprint
ADR-MED-001: Medical AI Governance Vertical

REST endpoints for the Medical AI Governance vertical.

Routes:
  GET  /api/medical/metrics        — Summary KPIs
  GET  /api/medical/decisions      — Recent decisions with outcomes
  GET  /api/medical/by-type        — Breakdown by decision type
  GET  /api/medical/by-device      — Breakdown by device type
  GET  /api/medical/by-jurisdiction — Breakdown by jurisdiction
  GET  /api/medical/timeline       — Decision trend over time
  GET  /api/medical/live-feed      — Last 10 decisions for live feed
  POST /api/medical/evaluate       — Manual decision evaluation
  GET  /api/medical/health         — Engine health check
"""

from __future__ import annotations

import logging
import os
import uuid

from flask import Blueprint, jsonify, request, g

logger = logging.getLogger("OMNIX.Medical.API")

medical_bp = Blueprint("medical", __name__, url_prefix="/api/medical")


def _get_db():
    import psycopg2
    if "db" not in g:
        g.db = psycopg2.connect(os.environ["DATABASE_URL"])
    return g.db


def _query(sql: str, params=None) -> list[dict]:
    conn = _get_db()
    from psycopg2.extras import RealDictCursor
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def _queryOne(sql: str, params=None) -> dict | None:
    rows = _query(sql, params)
    return rows[0] if rows else None


@medical_bp.route("/metrics")
@medical_bp.route("/metrics.json")
def get_metrics():
    try:
        totals = _queryOne("""
            SELECT
                COUNT(*) AS total_decisions,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED') AS blocked,
                COUNT(*) FILTER (WHERE decision='HOLD') AS held,
                COALESCE(AVG(diagnostic_confidence), 0) AS avg_diagnostic_confidence,
                COALESCE(AVG(patient_risk_score), 0) AS avg_patient_risk,
                COALESCE(AVG(decision_score), 0) AS avg_decision_score,
                COALESCE(AVG(trajectory_score), 0) AS avg_trajectory_score,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') AS decisions_24h,
                COUNT(DISTINCT device_id) AS active_devices,
                COUNT(*) FILTER (WHERE decision='BLOCKED' AND (ethics_flag=TRUE OR consent_verified=FALSE)) AS safety_blocks
            FROM medical_decisions
        """)

        cycles = _queryOne("""
            SELECT COUNT(*) AS total_cycles
            FROM medical_cycle_metrics
        """)

        if not totals:
            return jsonify({"success": False, "error": "No data yet"}), 404

        total = int(totals.get("total_decisions", 0)) or 1
        approved = int(totals.get("approved", 0))
        blocked = int(totals.get("blocked", 0))

        return jsonify({
            "success": True,
            "metrics": {
                "total_decisions": total,
                "decisions_approved": approved,
                "decisions_blocked": blocked,
                "decisions_held": int(totals.get("held", 0)),
                "approval_rate": round(approved / total, 4),
                "block_rate": round(blocked / total, 4),
                "avg_diagnostic_confidence": round(float(totals.get("avg_diagnostic_confidence", 0)), 2),
                "avg_patient_risk": round(float(totals.get("avg_patient_risk", 0)), 2),
                "avg_decision_score": round(float(totals.get("avg_decision_score", 0)), 2),
                "avg_trajectory_score": round(float(totals.get("avg_trajectory_score", 0)), 2),
                "decisions_last_24h": int(totals.get("decisions_24h", 0)),
                "active_devices": int(totals.get("active_devices", 0)),
                "safety_blocks": int(totals.get("safety_blocks", 0)),
                "simulation_cycles": int((cycles or {}).get("total_cycles", 0)),
            }
        })
    except Exception as e:
        logger.error(f"get_metrics error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@medical_bp.route("/decisions")
def get_decisions():
    try:
        limit = min(int(request.args.get("limit", 30)), 100)
        rows = _query("""
            SELECT decision_id, device_id, device_type, decision_type,
                   patient_profile, jurisdiction,
                   sensor_confidence, diagnostic_confidence,
                   patient_risk_score, contraindication_score,
                   evidence_completeness, care_plan_alignment,
                   recovery_trend, comorbidity_index,
                   ethics_flag, consent_verified, off_label_use,
                   decision, decision_score, block_reason, receipt_id,
                   probability_score, risk_exposure, signal_coherence,
                   trend_persistence, stress_resilience, logic_consistency,
                   trajectory_score, created_at
            FROM medical_decisions
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        for r in rows:
            if r.get("created_at"):
                r["created_at"] = r["created_at"].isoformat()
        return jsonify({"success": True, "decisions": rows})
    except Exception as e:
        logger.error(f"get_decisions error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@medical_bp.route("/live-feed")
def get_live_feed():
    try:
        rows = _query("""
            SELECT decision_id, device_type, decision_type, patient_profile,
                   jurisdiction, diagnostic_confidence, patient_risk_score,
                   decision, decision_score, block_reason, receipt_id,
                   trajectory_score, created_at
            FROM medical_decisions
            ORDER BY created_at DESC
            LIMIT 10
        """)
        for r in rows:
            if r.get("created_at"):
                r["created_at"] = r["created_at"].isoformat()
        return jsonify({"success": True, "decisions": rows})
    except Exception as e:
        logger.error(f"get_live_feed error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@medical_bp.route("/by-type")
def get_by_type():
    try:
        rows = _query("""
            SELECT
                decision_type,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED') AS blocked,
                ROUND(AVG(diagnostic_confidence)::numeric, 2) AS avg_confidence,
                ROUND(AVG(patient_risk_score)::numeric, 2) AS avg_risk,
                ROUND(COUNT(*) FILTER (WHERE decision='APPROVED')::numeric / NULLIF(COUNT(*),0), 4) AS approval_rate
            FROM medical_decisions
            GROUP BY decision_type
            ORDER BY total DESC
        """)
        return jsonify({"success": True, "by_type": rows})
    except Exception as e:
        logger.error(f"get_by_type error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@medical_bp.route("/by-device")
def get_by_device():
    try:
        rows = _query("""
            SELECT
                device_type,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED') AS blocked,
                ROUND(AVG(sensor_confidence)::numeric, 2) AS avg_sensor_confidence,
                ROUND(AVG(decision_score)::numeric, 2) AS avg_decision_score,
                COUNT(DISTINCT device_id) AS device_count,
                ROUND(COUNT(*) FILTER (WHERE decision='APPROVED')::numeric / NULLIF(COUNT(*),0), 4) AS approval_rate
            FROM medical_decisions
            GROUP BY device_type
            ORDER BY total DESC
        """)
        return jsonify({"success": True, "by_device": rows})
    except Exception as e:
        logger.error(f"get_by_device error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@medical_bp.route("/by-jurisdiction")
def get_by_jurisdiction():
    try:
        rows = _query("""
            SELECT
                jurisdiction,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED') AS blocked,
                ROUND(AVG(decision_score)::numeric, 2) AS avg_score,
                ROUND(COUNT(*) FILTER (WHERE decision='APPROVED')::numeric / NULLIF(COUNT(*),0), 4) AS approval_rate
            FROM medical_decisions
            GROUP BY jurisdiction
            ORDER BY total DESC
        """)
        return jsonify({"success": True, "by_jurisdiction": rows})
    except Exception as e:
        logger.error(f"get_by_jurisdiction error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@medical_bp.route("/timeline")
def get_timeline():
    try:
        rows = _query("""
            SELECT
                DATE_TRUNC('hour', created_at) AS hour,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED') AS blocked,
                ROUND(AVG(decision_score)::numeric, 2) AS avg_score
            FROM medical_decisions
            WHERE created_at > NOW() - INTERVAL '48 hours'
            GROUP BY DATE_TRUNC('hour', created_at)
            ORDER BY hour ASC
        """)
        for r in rows:
            if r.get("hour"):
                r["hour"] = r["hour"].isoformat()
        return jsonify({"success": True, "timeline": rows})
    except Exception as e:
        logger.error(f"get_timeline error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@medical_bp.route("/evaluate", methods=["POST"])
def manual_evaluate():
    try:
        from omnix_core.medical.medical_signal_adapter import (
            MedicalDecisionInput, MedicalSignalAdapter
        )
        data = request.get_json(force=True)
        decision_input = MedicalDecisionInput(
            device_type=data.get("device_type", "Clinical_AI"),
            decision_type=data.get("decision_type", "diagnostic_alert"),
            patient_profile=data.get("patient_profile", "chronic_condition"),
            jurisdiction=data.get("jurisdiction", "UAE"),
            sensor_confidence=float(data.get("sensor_confidence", 80)),
            diagnostic_confidence=float(data.get("diagnostic_confidence", 80)),
            patient_risk_score=float(data.get("patient_risk_score", 40)),
            contraindication_score=float(data.get("contraindication_score", 10)),
            evidence_completeness=float(data.get("evidence_completeness", 80)),
            care_plan_alignment=float(data.get("care_plan_alignment", 80)),
            recovery_trend=float(data.get("recovery_trend", 65)),
            comorbidity_index=float(data.get("comorbidity_index", 30)),
            ethics_flag=bool(data.get("ethics_flag", False)),
            consent_verified=bool(data.get("consent_verified", True)),
            off_label_use=bool(data.get("off_label_use", False)),
            days_since_calibration=int(data.get("days_since_calibration", 1)),
            prior_adverse_events=int(data.get("prior_adverse_events", 0)),
        )
        adapter = MedicalSignalAdapter()
        signals = adapter.adapt(decision_input)
        return jsonify({"success": True, "signals": signals.to_omnix_dict(),
                        "recommendation": signals.recommendation})
    except Exception as e:
        logger.error(f"manual_evaluate error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@medical_bp.route("/health")
def health():
    try:
        count = _queryOne("SELECT COUNT(*) AS cnt FROM medical_decisions")
        return jsonify({
            "success": True,
            "status": "operational",
            "total_decisions": int((count or {}).get("cnt", 0)),
            "domain": "medical_ai",
            "receipt_prefix": "OMNIX-MED"
        })
    except Exception as e:
        return jsonify({"success": False, "status": "degraded", "error": "Internal server error"}), 500
