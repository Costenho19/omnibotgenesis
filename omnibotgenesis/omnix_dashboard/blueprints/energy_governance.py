"""
OMNIX Energy Governance API Blueprint
ADR-ENG-001: Energy Governance Vertical (INTERNAL — restricted access)

REST endpoints for the Energy Governance vertical.
All routes require internal deployment — not exposed in public nav.

Routes:
  GET  /api/energy/metrics     — Summary KPIs (MW, CO2, stability, block rates)
  GET  /api/energy/decisions   — Recent energy governance decisions
  GET  /api/energy/by-type     — Breakdown by decision type
  GET  /api/energy/by-source   — Breakdown by energy source
  GET  /api/energy/by-region   — Breakdown by grid region
  GET  /api/energy/timeline    — Decision + MW trend over last 48h
  GET  /api/energy/live-feed   — Last 12 decisions for live SCADA feed
  POST /api/energy/evaluate    — Manual decision evaluation (what-if)
  GET  /api/energy/health      — Engine health check
"""

from __future__ import annotations

import logging
import os

from flask import Blueprint, jsonify, request, g

logger = logging.getLogger("OMNIX.Energy.API")

energy_bp = Blueprint("energy", __name__, url_prefix="/api/energy")


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


@energy_bp.route("/metrics")
@energy_bp.route("/metrics.json")
def get_metrics():
    try:
        totals = _queryOne("""
            SELECT
                COUNT(*)                                                     AS total_decisions,
                COUNT(*) FILTER (WHERE decision='APPROVED')                  AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')                   AS blocked,
                COUNT(*) FILTER (WHERE decision='HOLD')                      AS held,
                COALESCE(SUM(contracted_mw), 0)                              AS total_mw_governed,
                COALESCE(SUM(contracted_mw) FILTER (WHERE decision='APPROVED'), 0) AS approved_mw,
                COALESCE(SUM(contracted_mw) FILTER (WHERE decision='BLOCKED'), 0)  AS blocked_mw,
                COALESCE(SUM(carbon_avoided_tco2e), 0)                       AS total_carbon_avoided,
                COALESCE(AVG(decision_score), 0)                             AS avg_decision_score,
                COALESCE(AVG(capacity_margin_pct), 0)                        AS avg_capacity_margin,
                COALESCE(AVG(frequency_deviation_hz), 0)                     AS avg_frequency_deviation,
                COALESCE(AVG(settlement_risk_usd), 0)                        AS avg_settlement_risk,
                COALESCE(AVG(lmp_forecast_confidence), 0)                    AS avg_lmp_confidence,
                COALESCE(AVG(renewable_intermittency_buffer), 0)             AS avg_renewable_buffer,
                COUNT(*) FILTER (WHERE hard_block_reason IS NOT NULL)        AS hard_blocks,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') AS decisions_24h,
                COUNT(DISTINCT energy_source)                                AS sources_active,
                COUNT(DISTINCT grid_region)                                  AS regions_active
            FROM energy_decisions
        """)

        cycles = _queryOne("SELECT COUNT(*) AS total_cycles FROM energy_cycle_metrics")
        carbon_sum = _queryOne("""
            SELECT COALESCE(SUM(carbon_avoided_tco2e), 0) AS total
            FROM energy_cycle_metrics
        """)

        if not totals:
            return jsonify({"success": False, "error": "No data yet"}), 404

        total    = int(totals.get("total_decisions", 0)) or 1
        approved = int(totals.get("approved", 0))
        blocked  = int(totals.get("blocked", 0))

        return jsonify({
            "success": True,
            "metrics": {
                "total_decisions":       total,
                "decisions_approved":    approved,
                "decisions_blocked":     blocked,
                "decisions_held":        int(totals.get("held", 0)),
                "approval_rate":         round(approved / total, 4),
                "block_rate":            round(blocked / total, 4),
                "total_mw_governed":     round(float(totals.get("total_mw_governed", 0)), 1),
                "approved_mw":           round(float(totals.get("approved_mw", 0)), 1),
                "blocked_mw":            round(float(totals.get("blocked_mw", 0)), 1),
                "total_carbon_avoided":  round(float(totals.get("total_carbon_avoided", 0)), 2),
                "avg_decision_score":    round(float(totals.get("avg_decision_score", 0)), 2),
                "avg_capacity_margin":   round(float(totals.get("avg_capacity_margin", 0)), 2),
                "avg_frequency_deviation": round(float(totals.get("avg_frequency_deviation", 0)), 4),
                "avg_settlement_risk":   round(float(totals.get("avg_settlement_risk", 0)), 2),
                "avg_lmp_confidence":    round(float(totals.get("avg_lmp_confidence", 0)), 2),
                "avg_renewable_buffer":  round(float(totals.get("avg_renewable_buffer", 0)), 2),
                "hard_blocks":           int(totals.get("hard_blocks", 0)),
                "decisions_last_24h":    int(totals.get("decisions_24h", 0)),
                "sources_active":        int(totals.get("sources_active", 0)),
                "regions_active":        int(totals.get("regions_active", 0)),
                "simulation_cycles":     int((cycles or {}).get("total_cycles", 0)),
            }
        })
    except Exception as e:
        logger.error(f"get_metrics error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@energy_bp.route("/decisions")
def get_decisions():
    try:
        limit = min(int(request.args.get("limit", 50)), 200)
        rows = _query("""
            SELECT
                decision_id, decision_type, energy_source, grid_region,
                contracted_mw, settlement_price_mwh, contract_term_years,
                decision, decision_score, block_reason, hard_block_reason,
                probability_score, risk_exposure, signal_coherence,
                trend_persistence, stress_resilience, logic_consistency,
                trajectory_score, capacity_margin_pct, frequency_deviation_hz,
                carbon_avoided_tco2e, settlement_risk_usd,
                lmp_forecast_confidence, renewable_intermittency_buffer,
                receipt_id, domain, created_at
            FROM energy_decisions
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


@energy_bp.route("/live-feed")
def get_live_feed():
    try:
        rows = _query("""
            SELECT
                decision_id, decision_type, energy_source, grid_region,
                contracted_mw, settlement_price_mwh,
                decision, decision_score, block_reason, hard_block_reason,
                carbon_avoided_tco2e, settlement_risk_usd,
                frequency_deviation_hz, capacity_margin_pct,
                receipt_id, created_at
            FROM energy_decisions
            ORDER BY created_at DESC
            LIMIT 12
        """)
        for r in rows:
            if r.get("created_at"):
                r["created_at"] = r["created_at"].isoformat()
        return jsonify({"success": True, "decisions": rows})
    except Exception as e:
        logger.error(f"get_live_feed error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@energy_bp.route("/by-type")
def get_by_type():
    try:
        rows = _query("""
            SELECT
                decision_type,
                COUNT(*)                                                       AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED')                    AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')                     AS blocked,
                ROUND(SUM(contracted_mw)::numeric, 1)                         AS total_mw,
                ROUND(AVG(decision_score)::numeric, 2)                        AS avg_score,
                ROUND(AVG(carbon_avoided_tco2e)::numeric, 3)                  AS avg_carbon_avoided,
                ROUND(
                    COUNT(*) FILTER (WHERE decision='APPROVED')::numeric
                    / NULLIF(COUNT(*), 0), 4
                )                                                              AS approval_rate
            FROM energy_decisions
            GROUP BY decision_type
            ORDER BY total DESC
        """)
        return jsonify({"success": True, "by_type": rows})
    except Exception as e:
        logger.error(f"get_by_type error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@energy_bp.route("/by-source")
def get_by_source():
    try:
        rows = _query("""
            SELECT
                energy_source,
                COUNT(*)                                                       AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED')                    AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')                     AS blocked,
                ROUND(SUM(contracted_mw)::numeric, 1)                         AS total_mw,
                ROUND(AVG(lmp_forecast_confidence)::numeric, 2)               AS avg_lmp_confidence,
                ROUND(SUM(carbon_avoided_tco2e)::numeric, 2)                  AS total_carbon_avoided,
                ROUND(AVG(settlement_risk_usd)::numeric, 2)                   AS avg_settlement_risk,
                ROUND(
                    COUNT(*) FILTER (WHERE decision='APPROVED')::numeric
                    / NULLIF(COUNT(*), 0), 4
                )                                                              AS approval_rate
            FROM energy_decisions
            GROUP BY energy_source
            ORDER BY total_mw DESC
        """)
        return jsonify({"success": True, "by_source": rows})
    except Exception as e:
        logger.error(f"get_by_source error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@energy_bp.route("/by-region")
def get_by_region():
    try:
        rows = _query("""
            SELECT
                grid_region,
                COUNT(*)                                                       AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED')                    AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')                     AS blocked,
                ROUND(SUM(contracted_mw)::numeric, 1)                         AS total_mw,
                ROUND(AVG(capacity_margin_pct)::numeric, 2)                   AS avg_capacity_margin,
                ROUND(AVG(frequency_deviation_hz)::numeric, 4)                AS avg_freq_deviation,
                ROUND(SUM(carbon_avoided_tco2e)::numeric, 2)                  AS total_carbon_avoided,
                ROUND(
                    COUNT(*) FILTER (WHERE decision='APPROVED')::numeric
                    / NULLIF(COUNT(*), 0), 4
                )                                                              AS approval_rate
            FROM energy_decisions
            GROUP BY grid_region
            ORDER BY total_mw DESC
        """)
        return jsonify({"success": True, "by_region": rows})
    except Exception as e:
        logger.error(f"get_by_region error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@energy_bp.route("/timeline")
def get_timeline():
    try:
        rows = _query("""
            SELECT
                DATE_TRUNC('hour', created_at)                            AS hour,
                COUNT(*)                                                   AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED')               AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')                AS blocked,
                ROUND(SUM(contracted_mw)::numeric, 1)                     AS total_mw,
                ROUND(AVG(decision_score)::numeric, 2)                    AS avg_score,
                ROUND(SUM(carbon_avoided_tco2e)::numeric, 3)              AS carbon_avoided
            FROM energy_decisions
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


@energy_bp.route("/evaluate", methods=["POST"])
def manual_evaluate():
    try:
        from omnix_core.energy.energy_signal_adapter import (
            EnergyDecisionInput,
            EnergySignalAdapter,
        )
        data = request.get_json(force=True)

        decision_input = EnergyDecisionInput(
            decision_type=data.get("decision_type", "dispatch_order"),
            energy_source=data.get("energy_source", "Natural_Gas"),
            grid_region=data.get("grid_region", "PJM"),
            lmp_forecast_confidence=float(data.get("lmp_forecast_confidence", 72)),
            frequency_deviation_hz=float(data.get("frequency_deviation_hz", 0.05)),
            grid_congestion_index=float(data.get("grid_congestion_index", 30)),
            capacity_margin_pct=float(data.get("capacity_margin_pct", 18)),
            day_ahead_rt_spread=float(data.get("day_ahead_rt_spread", 15)),
            futures_spot_convergence=float(data.get("futures_spot_convergence", 65)),
            cross_border_price_alignment=float(data.get("cross_border_price_alignment", 60)),
            load_forecast_accuracy=float(data.get("load_forecast_accuracy", 74)),
            demand_growth_stability=float(data.get("demand_growth_stability", 68)),
            seasonality_alignment=float(data.get("seasonality_alignment", 70)),
            renewable_intermittency_buffer=float(data.get("renewable_intermittency_buffer", 60)),
            interconnect_capacity_utilization=float(data.get("interconnect_capacity_utilization", 55)),
            storage_readiness=float(data.get("storage_readiness", 60)),
            regulatory_violation_flag=bool(data.get("regulatory_violation_flag", False)),
            carbon_position_over_cap=bool(data.get("carbon_position_over_cap", False)),
            counterparty_credit_default=bool(data.get("counterparty_credit_default", False)),
            sanctions_flag=bool(data.get("sanctions_flag", False)),
            contracted_mw=float(data.get("contracted_mw", 200)),
            contract_term_years=float(data.get("contract_term_years", 1.0)),
            settlement_price_mwh=float(data.get("settlement_price_mwh", 55.0)),
            carbon_price_usd_tco2=float(data.get("carbon_price_usd_tco2", 25.0)),
        )

        adapter = EnergySignalAdapter()
        signals = adapter.adapt(decision_input)

        return jsonify({
            "success":          True,
            "signals":          signals.to_omnix_dict(),
            "recommendation":   signals.recommendation,
            "carbon_avoided_tco2e": signals.carbon_avoided_tco2e,
            "settlement_risk_usd":  signals.settlement_risk_usd,
            "hard_block_reason": signals.hard_block_reason,
        })
    except Exception as e:
        logger.error(f"manual_evaluate error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@energy_bp.route("/health")
def health():
    try:
        count = _queryOne("SELECT COUNT(*) AS cnt FROM energy_decisions")
        cycles = _queryOne("SELECT COUNT(*) AS cnt FROM energy_cycle_metrics")
        return jsonify({
            "success":        True,
            "status":         "operational",
            "total_decisions": int((count or {}).get("cnt", 0)),
            "total_cycles":   int((cycles or {}).get("cnt", 0)),
            "domain":         "energy_governance",
            "receipt_prefix": "OMNIX-EGV",
            "adr":            "ADR-ENG-001",
        })
    except Exception as e:
        return jsonify({"success": False, "status": "degraded", "error": str(e)}), 500
