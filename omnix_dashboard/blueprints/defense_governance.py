"""
OMNIX Autonomous Defense Governance API Blueprint
ADR-DEF-001: Autonomous Defense Governance Vertical (INTERNAL)

REST endpoints for the Autonomous Defense Governance vertical.

Routes:
  GET  /api/defense/metrics       — Summary KPIs (decisions, approval, blocks, hard-blocks)
  GET  /api/defense/decisions     — Recent defense governance decisions
  GET  /api/defense/live-feed     — Last 12 decisions for live command feed
  GET  /api/defense/by-type       — Breakdown by decision type
  GET  /api/defense/by-platform   — Breakdown by platform type
  GET  /api/defense/by-theater    — Breakdown by operational theater
  GET  /api/defense/timeline      — Decision trend over last 48h
  POST /api/defense/evaluate      — Manual decision evaluation (what-if)
  GET  /api/defense/health        — Engine health check
"""

from __future__ import annotations

import logging
import os

from flask import Blueprint, jsonify, request, g

logger = logging.getLogger("OMNIX.Defense.API")

defense_bp = Blueprint("defense", __name__, url_prefix="/api/defense")


def _get_db():
    import psycopg2
    if "db" not in g:
        db_url = os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
        g.db = psycopg2.connect(db_url)
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


@defense_bp.route("/metrics")
@defense_bp.route("/metrics.json")
def get_metrics():
    try:
        totals = _queryOne("""
            SELECT
                COUNT(*)                                                          AS total_decisions,
                COUNT(*) FILTER (WHERE decision='APPROVED')                       AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')                        AS blocked,
                COUNT(*) FILTER (WHERE decision='HOLD')                           AS held,
                COUNT(*) FILTER (WHERE hard_block_reason IS NOT NULL)             AS hard_blocks,
                COUNT(*) FILTER (WHERE civilian_proximity_flag = TRUE)            AS civilian_proximity_events,
                COUNT(*) FILTER (WHERE roe_violation_flag = TRUE)                 AS roe_violations,
                COUNT(*) FILTER (WHERE friendly_fire_risk_flag = TRUE)            AS friendly_fire_prevented,
                COUNT(*) FILTER (WHERE cyber_intrusion_flag = TRUE)               AS cyber_intrusions,
                COALESCE(AVG(target_confidence), 0)                               AS avg_target_confidence,
                COALESCE(AVG(target_discrimination), 0)                           AS avg_target_discrimination,
                COALESCE(AVG(collateral_damage_estimate), 0)                      AS avg_collateral_estimate,
                COALESCE(AVG(roe_compliance_score), 0)                            AS avg_roe_compliance,
                COALESCE(AVG(comms_integrity), 0)                                 AS avg_comms_integrity,
                COALESCE(AVG(legal_authorization_score), 0)                       AS avg_legal_score,
                COALESCE(AVG(human_oversight_available), 0)                       AS avg_human_oversight,
                COALESCE(AVG(engagement_risk_index), 0)                           AS avg_engagement_risk,
                COALESCE(AVG(decision_score), 0)                                  AS avg_decision_score,
                COALESCE(AVG(trajectory_score), 0)                                AS avg_trajectory_score,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') AS decisions_24h,
                COUNT(DISTINCT platform_type)                                     AS platforms_active,
                COUNT(DISTINCT operational_theater)                               AS theaters_active
            FROM defense_decisions
        """)

        cycles = _queryOne("SELECT COUNT(*) AS total_cycles FROM defense_cycle_metrics")
        cycle_stats = _queryOne("""
            SELECT
                COALESCE(SUM(missions_authorized), 0)  AS total_missions_authorized,
                COALESCE(SUM(targets_validated), 0)    AS total_targets_validated,
                COALESCE(SUM(hard_blocks), 0)          AS total_hard_blocks
            FROM defense_cycle_metrics
        """)

        if not totals:
            return jsonify({"success": False, "error": "No data yet"}), 404

        total    = int(totals.get("total_decisions", 0)) or 1
        approved = int(totals.get("approved", 0))
        blocked  = int(totals.get("blocked", 0))

        return jsonify({
            "success": True,
            "metrics": {
                "total_decisions":             total,
                "decisions_approved":          approved,
                "decisions_blocked":           blocked,
                "decisions_held":              int(totals.get("held", 0)),
                "approval_rate":               round(approved / total, 4),
                "block_rate":                  round(blocked / total, 4),
                "hard_blocks":                 int(totals.get("hard_blocks", 0)),
                "civilian_proximity_events":   int(totals.get("civilian_proximity_events", 0)),
                "roe_violations_detected":     int(totals.get("roe_violations", 0)),
                "friendly_fire_prevented":     int(totals.get("friendly_fire_prevented", 0)),
                "cyber_intrusions_detected":   int(totals.get("cyber_intrusions", 0)),
                "avg_target_confidence":       round(float(totals.get("avg_target_confidence", 0)), 2),
                "avg_target_discrimination":   round(float(totals.get("avg_target_discrimination", 0)), 2),
                "avg_collateral_estimate":     round(float(totals.get("avg_collateral_estimate", 0)), 2),
                "avg_roe_compliance":          round(float(totals.get("avg_roe_compliance", 0)), 2),
                "avg_comms_integrity":         round(float(totals.get("avg_comms_integrity", 0)), 2),
                "avg_legal_score":             round(float(totals.get("avg_legal_score", 0)), 2),
                "avg_human_oversight":         round(float(totals.get("avg_human_oversight", 0)), 2),
                "avg_engagement_risk":         round(float(totals.get("avg_engagement_risk", 0)), 2),
                "avg_decision_score":          round(float(totals.get("avg_decision_score", 0)), 2),
                "avg_trajectory_score":        round(float(totals.get("avg_trajectory_score", 0)), 2),
                "decisions_last_24h":          int(totals.get("decisions_24h", 0)),
                "platforms_active":            int(totals.get("platforms_active", 0)),
                "theaters_active":             int(totals.get("theaters_active", 0)),
                "simulation_cycles":           int((cycles or {}).get("total_cycles", 0)),
                "total_missions_authorized":   int((cycle_stats or {}).get("total_missions_authorized", 0)),
                "total_targets_validated":     int((cycle_stats or {}).get("total_targets_validated", 0)),
            }
        })
    except Exception as e:
        logger.error(f"get_metrics error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@defense_bp.route("/decisions")
def get_decisions():
    try:
        limit = min(int(request.args.get("limit", 50)), 200)
        rows = _query("""
            SELECT
                decision_id, decision_type, platform_type, operational_theater,
                engagement_range_km, mission_duration_hrs,
                target_confidence, target_discrimination, collateral_damage_estimate,
                roe_compliance_score, comms_integrity, cyber_vulnerability_score,
                mission_necessity_score, human_oversight_available, legal_authorization_score,
                iff_confidence, engagement_risk_index,
                civilian_proximity_flag, roe_violation_flag, cyber_intrusion_flag,
                friendly_fire_risk_flag, chain_of_command_break,
                decision, decision_score, block_reason, hard_block_reason,
                probability_score, risk_exposure, signal_coherence,
                trend_persistence, stress_resilience, logic_consistency,
                trajectory_score, receipt_id, domain, created_at
            FROM defense_decisions
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


@defense_bp.route("/live-feed")
def get_live_feed():
    try:
        rows = _query("""
            SELECT
                decision_id, decision_type, platform_type, operational_theater,
                target_confidence, collateral_damage_estimate, roe_compliance_score,
                engagement_range_km, iff_confidence, engagement_risk_index,
                decision, decision_score, block_reason, hard_block_reason,
                civilian_proximity_flag, roe_violation_flag, friendly_fire_risk_flag,
                receipt_id, created_at
            FROM defense_decisions
            ORDER BY created_at DESC
            LIMIT 12
        """)
        for r in rows:
            if r.get("created_at"):
                r["created_at"] = r["created_at"].isoformat()
        return jsonify({"success": True, "decisions": rows})
    except Exception as e:
        logger.error(f"get_live_feed error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@defense_bp.route("/by-type")
def get_by_type():
    try:
        rows = _query("""
            SELECT
                decision_type,
                COUNT(*)                                                          AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED')                       AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')                        AS blocked,
                ROUND(AVG(decision_score)::numeric, 2)                            AS avg_score,
                ROUND(AVG(target_confidence)::numeric, 2)                         AS avg_target_confidence,
                ROUND(AVG(collateral_damage_estimate)::numeric, 2)                AS avg_collateral,
                ROUND(
                    COUNT(*) FILTER (WHERE decision='APPROVED')::numeric
                    / NULLIF(COUNT(*), 0), 4
                )                                                                 AS approval_rate
            FROM defense_decisions
            GROUP BY decision_type
            ORDER BY total DESC
        """)
        return jsonify({"success": True, "by_type": rows})
    except Exception as e:
        logger.error(f"get_by_type error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@defense_bp.route("/by-platform")
def get_by_platform():
    try:
        rows = _query("""
            SELECT
                platform_type,
                COUNT(*)                                                          AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED')                       AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')                        AS blocked,
                COUNT(*) FILTER (WHERE hard_block_reason IS NOT NULL)             AS hard_blocks,
                ROUND(AVG(engagement_risk_index)::numeric, 2)                     AS avg_engagement_risk,
                ROUND(AVG(target_confidence)::numeric, 2)                         AS avg_target_confidence,
                ROUND(AVG(comms_integrity)::numeric, 2)                           AS avg_comms_integrity,
                ROUND(
                    COUNT(*) FILTER (WHERE decision='APPROVED')::numeric
                    / NULLIF(COUNT(*), 0), 4
                )                                                                 AS approval_rate
            FROM defense_decisions
            GROUP BY platform_type
            ORDER BY total DESC
        """)
        return jsonify({"success": True, "by_platform": rows})
    except Exception as e:
        logger.error(f"get_by_platform error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@defense_bp.route("/by-theater")
def get_by_theater():
    try:
        rows = _query("""
            SELECT
                operational_theater,
                COUNT(*)                                                          AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED')                       AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')                        AS blocked,
                COUNT(*) FILTER (WHERE civilian_proximity_flag = TRUE)            AS civilian_events,
                COUNT(*) FILTER (WHERE friendly_fire_risk_flag = TRUE)            AS ff_events,
                ROUND(AVG(roe_compliance_score)::numeric, 2)                      AS avg_roe_compliance,
                ROUND(AVG(collateral_damage_estimate)::numeric, 2)                AS avg_collateral,
                ROUND(
                    COUNT(*) FILTER (WHERE decision='APPROVED')::numeric
                    / NULLIF(COUNT(*), 0), 4
                )                                                                 AS approval_rate
            FROM defense_decisions
            GROUP BY operational_theater
            ORDER BY total DESC
        """)
        return jsonify({"success": True, "by_theater": rows})
    except Exception as e:
        logger.error(f"get_by_theater error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@defense_bp.route("/timeline")
def get_timeline():
    try:
        rows = _query("""
            SELECT
                DATE_TRUNC('hour', created_at)                            AS hour,
                COUNT(*)                                                   AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED')               AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')                AS blocked,
                COUNT(*) FILTER (WHERE hard_block_reason IS NOT NULL)     AS hard_blocks,
                ROUND(AVG(decision_score)::numeric, 2)                    AS avg_score,
                ROUND(AVG(engagement_risk_index)::numeric, 2)             AS avg_engagement_risk
            FROM defense_decisions
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


@defense_bp.route("/evaluate", methods=["POST"])
def manual_evaluate():
    try:
        from omnix_core.defense.defense_signal_adapter import (
            DefenseDecisionInput,
            DefenseSignalAdapter,
        )
        data = request.get_json(force=True)

        decision_input = DefenseDecisionInput(
            decision_type=data.get("decision_type", "mission_authorization"),
            platform_type=data.get("platform_type", "Autonomous_UAS"),
            operational_theater=data.get("operational_theater", "Contested_Airspace"),
            target_confidence=float(data.get("target_confidence", 72)),
            target_discrimination=float(data.get("target_discrimination", 70)),
            collateral_damage_estimate=float(data.get("collateral_damage_estimate", 78)),
            roe_compliance_score=float(data.get("roe_compliance_score", 76)),
            comms_integrity=float(data.get("comms_integrity", 75)),
            cyber_vulnerability_score=float(data.get("cyber_vulnerability_score", 70)),
            mission_necessity_score=float(data.get("mission_necessity_score", 72)),
            human_oversight_available=float(data.get("human_oversight_available", 68)),
            legal_authorization_score=float(data.get("legal_authorization_score", 74)),
            environmental_conditions=float(data.get("environmental_conditions", 70)),
            platform_readiness=float(data.get("platform_readiness", 80)),
            geofence_compliance=float(data.get("geofence_compliance", 85)),
            iff_confidence=float(data.get("iff_confidence", 74)),
            civilian_proximity_flag=bool(data.get("civilian_proximity_flag", False)),
            roe_violation_flag=bool(data.get("roe_violation_flag", False)),
            cyber_intrusion_flag=bool(data.get("cyber_intrusion_flag", False)),
            friendly_fire_risk_flag=bool(data.get("friendly_fire_risk_flag", False)),
            chain_of_command_break=bool(data.get("chain_of_command_break", False)),
            legal_prohibition_flag=bool(data.get("legal_prohibition_flag", False)),
            engagement_range_km=float(data.get("engagement_range_km", 10.0)),
            mission_duration_hrs=float(data.get("mission_duration_hrs", 2.0)),
        )

        adapter = DefenseSignalAdapter()
        signals = adapter.adapt(decision_input)

        return jsonify({
            "success":                 True,
            "signals":                 signals.to_omnix_dict(),
            "hard_block_reason":       signals.hard_block_reason,
            "engagement_risk_index":   signals.engagement_risk_index,
            "target_confidence":       signals.target_confidence,
            "collateral_damage_estimate": signals.collateral_damage_estimate,
            "roe_compliance_score":    signals.roe_compliance_score,
            "legal_authorization_score": signals.legal_authorization_score,
        })
    except Exception as e:
        logger.error(f"manual_evaluate error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@defense_bp.route("/health")
def health():
    try:
        count  = _queryOne("SELECT COUNT(*) AS cnt FROM defense_decisions")
        cycles = _queryOne("SELECT COUNT(*) AS cnt FROM defense_cycle_metrics")
        hard_b = _queryOne("SELECT COUNT(*) AS cnt FROM defense_decisions WHERE hard_block_reason IS NOT NULL")
        return jsonify({
            "success":         True,
            "status":          "operational",
            "total_decisions": int((count or {}).get("cnt", 0)),
            "total_cycles":    int((cycles or {}).get("cnt", 0)),
            "total_hard_blocks": int((hard_b or {}).get("cnt", 0)),
            "domain":          "defense_governance",
            "receipt_prefix":  "OMNIX-DEF",
            "adr":             "ADR-DEF-001",
        })
    except Exception as e:
        return jsonify({"success": False, "status": "degraded", "error": str(e)}), 500
