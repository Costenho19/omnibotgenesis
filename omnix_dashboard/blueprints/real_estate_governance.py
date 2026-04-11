"""
OMNIX Real Estate Governance API Blueprint
ADR-RES-001: Real Estate Governance Vertical

REST endpoints for the Real Estate Governance vertical.

Routes:
  GET  /api/real-estate/metrics        — Summary KPIs
  GET  /api/real-estate/decisions      — Recent property decisions with outcomes
  GET  /api/real-estate/by-type        — Breakdown by decision type
  GET  /api/real-estate/by-property    — Breakdown by property type
  GET  /api/real-estate/by-jurisdiction — Breakdown by jurisdiction
  GET  /api/real-estate/timeline       — Decision trend over time (48h)
  GET  /api/real-estate/live-feed      — Last 10 decisions for live feed
  POST /api/real-estate/evaluate       — Manual decision evaluation (what-if)
  GET  /api/real-estate/health         — Engine health check
"""

from __future__ import annotations

import logging
import os
import uuid

from flask import Blueprint, jsonify, request, g

logger = logging.getLogger("OMNIX.RealEstate.API")

real_estate_bp = Blueprint("real_estate", __name__, url_prefix="/api/real-estate")


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


@real_estate_bp.route("/metrics")
@real_estate_bp.route("/metrics.json")
def get_metrics():
    try:
        totals = _queryOne("""
            SELECT
                COUNT(*) AS total_decisions,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')  AS blocked,
                COUNT(*) FILTER (WHERE decision='HOLD')     AS held,
                COALESCE(AVG(model_accuracy), 0)     AS avg_avm_confidence,
                COALESCE(AVG(ltv_ratio), 0)          AS avg_ltv_ratio,
                COALESCE(AVG(decision_score), 0)     AS avg_decision_score,
                COALESCE(AVG(trajectory_score), 0)   AS avg_trajectory_score,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') AS decisions_24h,
                COUNT(DISTINCT property_type)        AS property_types_active,
                COUNT(*) FILTER (WHERE aml_flag = TRUE) AS aml_blocks,
                COUNT(*) FILTER (WHERE decision='BLOCKED'
                    AND (aml_flag=TRUE OR rera_compliant=FALSE
                         OR sharia_screening_passed=FALSE)) AS compliance_blocks
            FROM property_decisions
        """)

        cycles = _queryOne("SELECT COUNT(*) AS total_cycles FROM property_cycle_metrics")

        if not totals:
            return jsonify({"success": False, "error": "No data yet"}), 404

        total    = int(totals.get("total_decisions", 0)) or 1
        approved = int(totals.get("approved", 0))
        blocked  = int(totals.get("blocked", 0))

        return jsonify({
            "success": True,
            "metrics": {
                "total_decisions":        total,
                "decisions_approved":     approved,
                "decisions_blocked":      blocked,
                "decisions_held":         int(totals.get("held", 0)),
                "approval_rate":          round(approved / total, 4),
                "block_rate":             round(blocked / total, 4),
                "avg_avm_confidence":     round(float(totals.get("avg_avm_confidence", 0)), 2),
                "avg_ltv_ratio":          round(float(totals.get("avg_ltv_ratio", 0)), 2),
                "avg_decision_score":     round(float(totals.get("avg_decision_score", 0)), 2),
                "avg_trajectory_score":   round(float(totals.get("avg_trajectory_score", 0)), 2),
                "decisions_last_24h":     int(totals.get("decisions_24h", 0)),
                "property_types_active":  int(totals.get("property_types_active", 0)),
                "aml_blocks":             int(totals.get("aml_blocks", 0)),
                "compliance_blocks":      int(totals.get("compliance_blocks", 0)),
                "simulation_cycles":      int((cycles or {}).get("total_cycles", 0)),
            }
        })
    except Exception as e:
        logger.error(f"get_metrics error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@real_estate_bp.route("/decisions")
def get_decisions():
    try:
        limit = min(int(request.args.get("limit", 30)), 100)
        rows = _query("""
            SELECT
                decision_id, property_id, decision_type,
                property_type, market_segment, jurisdiction, financing_mode,
                comparable_quality, model_accuracy, data_freshness, market_depth,
                ltv_ratio, price_deviation, aml_risk_score, comparable_alignment,
                market_trend_score, demand_index, inventory_pressure,
                liquidity_score, rate_sensitivity, vacancy_risk,
                aml_flag, rera_compliant, sharia_screening_passed,
                beneficial_owner_verified, days_since_last_valuation, prior_aml_incidents,
                decision, decision_score, block_reason, receipt_id,
                probability_score, risk_exposure, signal_coherence,
                trend_persistence, stress_resilience, logic_consistency,
                trajectory_score, created_at
            FROM property_decisions
            ORDER BY created_at DESC
            LIMIT %s
        """, (limit,))
        for r in rows:
            if r.get("created_at"):
                r["created_at"] = r["created_at"].isoformat()
        return jsonify({"success": True, "decisions": rows})
    except Exception as e:
        logger.error(f"get_decisions error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@real_estate_bp.route("/live-feed")
def get_live_feed():
    try:
        rows = _query("""
            SELECT
                decision_id, property_id, decision_type, property_type,
                market_segment, jurisdiction, financing_mode,
                model_accuracy, ltv_ratio, aml_risk_score,
                aml_flag, decision, decision_score,
                block_reason, receipt_id, trajectory_score, created_at
            FROM property_decisions
            ORDER BY created_at DESC
            LIMIT 10
        """)
        for r in rows:
            if r.get("created_at"):
                r["created_at"] = r["created_at"].isoformat()
        return jsonify({"success": True, "decisions": rows})
    except Exception as e:
        logger.error(f"get_live_feed error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@real_estate_bp.route("/by-type")
def get_by_type():
    try:
        rows = _query("""
            SELECT
                decision_type,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')  AS blocked,
                ROUND(AVG(model_accuracy)::numeric, 2)      AS avg_avm_confidence,
                ROUND(AVG(decision_score)::numeric, 2)      AS avg_decision_score,
                ROUND(
                    COUNT(*) FILTER (WHERE decision='APPROVED')::numeric
                    / NULLIF(COUNT(*), 0), 4
                ) AS approval_rate
            FROM property_decisions
            GROUP BY decision_type
            ORDER BY total DESC
        """)
        return jsonify({"success": True, "by_type": rows})
    except Exception as e:
        logger.error(f"get_by_type error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@real_estate_bp.route("/by-property")
def get_by_property():
    try:
        rows = _query("""
            SELECT
                property_type,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')  AS blocked,
                ROUND(AVG(model_accuracy)::numeric, 2)      AS avg_avm_confidence,
                ROUND(AVG(ltv_ratio)::numeric, 2)           AS avg_ltv_ratio,
                ROUND(AVG(decision_score)::numeric, 2)      AS avg_decision_score,
                ROUND(
                    COUNT(*) FILTER (WHERE decision='APPROVED')::numeric
                    / NULLIF(COUNT(*), 0), 4
                ) AS approval_rate
            FROM property_decisions
            GROUP BY property_type
            ORDER BY total DESC
        """)
        return jsonify({"success": True, "by_property": rows})
    except Exception as e:
        logger.error(f"get_by_property error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@real_estate_bp.route("/by-jurisdiction")
def get_by_jurisdiction():
    try:
        rows = _query("""
            SELECT
                jurisdiction,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')  AS blocked,
                ROUND(AVG(aml_risk_score)::numeric, 2)      AS avg_aml_risk,
                ROUND(AVG(decision_score)::numeric, 2)      AS avg_score,
                ROUND(
                    COUNT(*) FILTER (WHERE decision='APPROVED')::numeric
                    / NULLIF(COUNT(*), 0), 4
                ) AS approval_rate
            FROM property_decisions
            GROUP BY jurisdiction
            ORDER BY CASE jurisdiction
                WHEN 'UAE' THEN 1 WHEN 'GCC' THEN 2
                WHEN 'UK'  THEN 3 WHEN 'EU'  THEN 4 ELSE 5
            END
        """)
        return jsonify({"success": True, "by_jurisdiction": rows})
    except Exception as e:
        logger.error(f"get_by_jurisdiction error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@real_estate_bp.route("/timeline")
def get_timeline():
    try:
        rows = _query("""
            SELECT
                DATE_TRUNC('hour', created_at) AS hour,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')  AS blocked,
                ROUND(AVG(decision_score)::numeric, 2)      AS avg_score
            FROM property_decisions
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
        return jsonify({"success": False, "error": str(e)}), 500


@real_estate_bp.route("/evaluate", methods=["POST"])
def manual_evaluate():
    try:
        from omnix_core.real_estate.real_estate_signal_adapter import (
            PropertyDecisionInput, RealEstateSignalAdapter
        )
        data = request.get_json(force=True)

        decision_input = PropertyDecisionInput(
            decision_type=data.get("decision_type", "property_valuation"),
            property_type=data.get("property_type", "Residential"),
            market_segment=data.get("market_segment", "Mid_Market"),
            jurisdiction=data.get("jurisdiction", "UAE"),
            financing_mode=data.get("financing_mode", "Conventional"),
            comparable_quality=float(data.get("comparable_quality", 75)),
            model_accuracy=float(data.get("model_accuracy", 80)),
            data_freshness=float(data.get("data_freshness", 85)),
            market_depth=float(data.get("market_depth", 70)),
            ltv_ratio=float(data.get("ltv_ratio", 75)),
            price_deviation=float(data.get("price_deviation", 10)),
            aml_risk_score=float(data.get("aml_risk_score", 15)),
            comparable_alignment=float(data.get("comparable_alignment", 78)),
            market_trend_score=float(data.get("market_trend_score", 68)),
            demand_index=float(data.get("demand_index", 65)),
            inventory_pressure=float(data.get("inventory_pressure", 45)),
            liquidity_score=float(data.get("liquidity_score", 72)),
            rate_sensitivity=float(data.get("rate_sensitivity", 48)),
            vacancy_risk=float(data.get("vacancy_risk", 25)),
            aml_flag=bool(data.get("aml_flag", False)),
            rera_compliant=bool(data.get("rera_compliant", True)),
            sharia_screening_passed=bool(data.get("sharia_screening_passed", True)),
            beneficial_owner_verified=bool(data.get("beneficial_owner_verified", True)),
            days_since_last_valuation=int(data.get("days_since_last_valuation", 0)),
            prior_aml_incidents=int(data.get("prior_aml_incidents", 0)),
        )

        adapter = RealEstateSignalAdapter()
        signals = adapter.adapt(decision_input)
        return jsonify({
            "success": True,
            "signals": signals.to_omnix_dict(),
            "recommendation": signals.recommendation,
            "ltv_hard_block": signals.ltv_hard_block,
            "aml_block": signals.aml_block,
        })
    except Exception as e:
        logger.error(f"manual_evaluate error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@real_estate_bp.route("/health")
def health():
    try:
        count = _queryOne("SELECT COUNT(*) AS cnt FROM property_decisions")
        return jsonify({
            "success": True,
            "status": "operational",
            "total_decisions": int((count or {}).get("cnt", 0)),
            "domain": "real_estate",
            "receipt_prefix": "OMNIX-REP",
        })
    except Exception as e:
        return jsonify({"success": False, "status": "degraded", "error": str(e)}), 500
