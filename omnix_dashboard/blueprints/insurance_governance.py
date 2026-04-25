"""
OMNIX Insurance Governance API Blueprint
ADR-054: Insurance Governance Vertical

REST endpoints for the Insurance Governance vertical.

Routes:
  GET  /api/insurance/metrics       — Summary KPIs
  GET  /api/insurance/claims        — Recent claims with decisions
  GET  /api/insurance/by-type       — Breakdown by insurance type
  GET  /api/insurance/by-region     — Breakdown by region
  GET  /api/insurance/timeline      — Approval/block trend over time
  POST /api/insurance/evaluate      — Manual claim evaluation
  GET  /api/insurance/health        — Engine health check
"""

from __future__ import annotations

import logging
import os
import time
import uuid

from flask import Blueprint, jsonify, request, g

logger = logging.getLogger("OMNIX.Insurance.API")

insurance_bp = Blueprint("insurance", __name__, url_prefix="/api/insurance")


def _get_db():
    import psycopg2
    import psycopg2.extras
    if "db" not in g:
        g.db = psycopg2.connect(os.environ.get("OMNIX_DB_URL") or os.environ["DATABASE_URL"])
    return g.db


def _query(sql: str, params=None) -> list[dict]:
    conn = _get_db()
    with conn.cursor(cursor_factory=__import__("psycopg2.extras", fromlist=["RealDictCursor"]).RealDictCursor) as cur:
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def _queryOne(sql: str, params=None) -> dict | None:
    rows = _query(sql, params)
    return rows[0] if rows else None


@insurance_bp.route("/metrics")
@insurance_bp.route("/metrics.json")
def get_metrics():
    try:
        totals = _queryOne("""
            SELECT
                COUNT(*) AS total_claims,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED') AS blocked,
                COUNT(*) FILTER (WHERE decision='HOLD') AS held,
                COALESCE(SUM(claim_amount_usd) FILTER (WHERE decision='APPROVED'), 0) AS total_approved_usd,
                COALESCE(SUM(claim_amount_usd) FILTER (WHERE decision='BLOCKED'), 0) AS total_blocked_usd,
                COALESCE(AVG(fraud_indicators), 0) AS avg_fraud_score,
                COALESCE(AVG(decision_score), 0) AS avg_decision_score,
                COALESCE(AVG(trajectory_score), 0) AS avg_trajectory_score,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') AS claims_24h,
                COUNT(*) FILTER (WHERE decision='BLOCKED' AND fraud_indicators > 60) AS high_fraud_blocked
            FROM insurance_claims
        """)
        cycles = _queryOne("""
            SELECT COUNT(*) AS total_cycles,
                   COALESCE(MAX(cycle_number), 0) AS last_cycle
            FROM insurance_cycle_metrics
        """)
        total = totals.get("total_claims", 0) or 1
        return jsonify({
            "success": True,
            "metrics": {
                "total_claims": int(totals.get("total_claims", 0)),
                "claims_approved": int(totals.get("approved", 0)),
                "claims_blocked": int(totals.get("blocked", 0)),
                "claims_held": int(totals.get("held", 0)),
                "approval_rate": round(int(totals.get("approved", 0)) / total, 4),
                "total_approved_usd": float(totals.get("total_approved_usd", 0)),
                "total_blocked_usd": float(totals.get("total_blocked_usd", 0)),
                "avg_fraud_score": round(float(totals.get("avg_fraud_score", 0)), 2),
                "avg_decision_score": round(float(totals.get("avg_decision_score", 0)), 2),
                "avg_trajectory_score": round(float(totals.get("avg_trajectory_score", 0)), 2),
                "claims_last_24h": int(totals.get("claims_24h", 0)),
                "high_fraud_blocked": int(totals.get("high_fraud_blocked", 0)),
                "simulation_cycles": int(cycles.get("total_cycles", 0)),
                "loss_avoided_usd": float(totals.get("total_blocked_usd", 0)),
            }
        })
    except Exception as e:
        logger.error(f"Insurance metrics error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@insurance_bp.route("/claims")
def get_claims():
    limit = min(int(request.args.get("limit", 50)), 200)
    offset = int(request.args.get("offset", 0))
    insurance_type = request.args.get("type")
    decision_filter = request.args.get("decision")

    conditions = []
    params: list = []
    if insurance_type:
        conditions.append("insurance_type = %s")
        params.append(insurance_type)
    if decision_filter:
        conditions.append("decision = %s")
        params.append(decision_filter.upper())

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    params += [limit, offset]

    try:
        rows = _query(f"""
            SELECT claim_id, claimant_type, insurance_type, region,
                   claim_amount_usd, policy_limit_usd, coverage_ratio,
                   fraud_indicators, evidence_completeness,
                   decision, decision_score, block_reason, receipt_id,
                   probability_score, risk_exposure, signal_coherence,
                   trend_persistence, stress_resilience, logic_consistency,
                   trajectory_score, created_at
            FROM insurance_claims
            {where}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, params)

        count = _queryOne(f"SELECT COUNT(*) AS n FROM insurance_claims {where}",
                          params[:-2] if params[:-2] else None)

        return jsonify({
            "success": True,
            "claims": rows,
            "total": int(count.get("n", 0)) if count else 0,
            "limit": limit,
            "offset": offset,
        })
    except Exception as e:
        logger.error(f"Insurance claims error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@insurance_bp.route("/by-type")
def get_by_type():
    try:
        rows = _query("""
            SELECT insurance_type,
                   COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                   COUNT(*) FILTER (WHERE decision='BLOCKED') AS blocked,
                   COALESCE(AVG(claim_amount_usd), 0) AS avg_claim_usd,
                   COALESCE(SUM(claim_amount_usd) FILTER (WHERE decision='BLOCKED'), 0) AS blocked_usd,
                   COALESCE(AVG(fraud_indicators), 0) AS avg_fraud
            FROM insurance_claims
            GROUP BY insurance_type
            ORDER BY total DESC
        """)
        for r in rows:
            r["approval_rate"] = round(r["approved"] / max(r["total"], 1), 4)
            r["avg_fraud"] = round(float(r["avg_fraud"]), 2)
            r["avg_claim_usd"] = round(float(r["avg_claim_usd"]), 2)
            r["blocked_usd"] = float(r["blocked_usd"])
        return jsonify({"success": True, "by_type": rows})
    except Exception as e:
        logger.error(f"Insurance by-type error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@insurance_bp.route("/by-region")
def get_by_region():
    try:
        rows = _query("""
            SELECT region,
                   COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                   COUNT(*) FILTER (WHERE decision='BLOCKED') AS blocked,
                   COALESCE(SUM(claim_amount_usd) FILTER (WHERE decision='APPROVED'), 0) AS approved_usd,
                   COALESCE(SUM(claim_amount_usd) FILTER (WHERE decision='BLOCKED'), 0) AS blocked_usd,
                   COALESCE(AVG(fraud_indicators), 0) AS avg_fraud
            FROM insurance_claims
            GROUP BY region
            ORDER BY total DESC
        """)
        for r in rows:
            r["approval_rate"] = round(r["approved"] / max(r["total"], 1), 4)
        return jsonify({"success": True, "by_region": rows})
    except Exception as e:
        logger.error(f"Insurance by-region error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@insurance_bp.route("/timeline")
def get_timeline():
    hours = int(request.args.get("hours", 24))
    try:
        rows = _query("""
            SELECT
                DATE_TRUNC('hour', created_at) AS hour,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED') AS blocked,
                COALESCE(SUM(claim_amount_usd) FILTER (WHERE decision='APPROVED'), 0) AS approved_usd
            FROM insurance_claims
            WHERE created_at > NOW() - INTERVAL '1 hour' * %s
            GROUP BY hour
            ORDER BY hour ASC
        """, [hours])
        return jsonify({"success": True, "timeline": rows})
    except Exception as e:
        logger.error(f"Insurance timeline error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@insurance_bp.route("/evaluate", methods=["POST"])
def manual_evaluate():
    """Manually evaluate a single insurance claim through the full pipeline."""
    data = request.get_json(silent=True) or {}
    try:
        from omnix_core.insurance.insurance_signal_adapter import (
            InsuranceClaimInput, InsuranceSignalAdapter
        )
        from omnix_core.insurance.insurance_simulator import _generate_claim, _evaluate_claim

        if not data:
            claim_data = _generate_claim()
        else:
            claim_data = {
                "claim_id": f"MANUAL-{uuid.uuid4().hex[:8].upper()}",
                "claimant_type": data.get("claimant_type", "Individual"),
                "insurance_type": data.get("insurance_type", "Property"),
                "region": data.get("region", "NA"),
                "claim_amount_usd": float(data.get("claim_amount_usd", 50000)),
                "policy_limit_usd": float(data.get("policy_limit_usd", 200000)),
                "coverage_ratio": float(data.get("claim_amount_usd", 50000)) / max(float(data.get("policy_limit_usd", 200000)), 1),
                "claimant_history_score": float(data.get("claimant_history_score", 75)),
                "fraud_indicators": float(data.get("fraud_indicators", 15)),
                "evidence_completeness": float(data.get("evidence_completeness", 80)),
                "loss_ratio_trend": float(data.get("loss_ratio_trend", 65)),
                "reserve_adequacy": float(data.get("reserve_adequacy", 75)),
                "policy_claim_alignment": float(data.get("policy_claim_alignment", 85)),
                "incident_days_ago": int(data.get("incident_days_ago", 30)),
                "prior_claims_count": int(data.get("prior_claims_count", 0)),
                "is_catastrophe_event": bool(data.get("is_catastrophe_event", False)),
            }

        result = _evaluate_claim(claim_data)
        return jsonify({"success": True, "evaluation": result})
    except Exception as e:
        logger.error(f"Insurance manual evaluate error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@insurance_bp.route("/health")
def health():
    try:
        last = _queryOne("""
            SELECT created_at, cycle_number
            FROM insurance_cycle_metrics
            ORDER BY created_at DESC LIMIT 1
        """)
        total = _queryOne("SELECT COUNT(*) AS n FROM insurance_claims")
        return jsonify({
            "success": True,
            "status": "operational",
            "total_claims": int(total.get("n", 0)) if total else 0,
            "last_cycle": last.get("cycle_number") if last else 0,
            "last_cycle_at": last.get("created_at").isoformat() if last and last.get("created_at") else None,
        })
    except Exception as e:
        return jsonify({"success": False, "status": "error", "error": "Internal server error"}), 500
