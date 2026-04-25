"""
OMNIX Robotics Governance API Blueprint
ADR-055: Robotics & Autonomous Systems Governance Vertical

REST endpoints for the Robotics Governance vertical.

Routes:
  GET  /api/robotics/metrics        — Summary KPIs
  GET  /api/robotics/actions        — Recent robot actions with decisions
  GET  /api/robotics/by-industry    — Breakdown by industry
  GET  /api/robotics/by-robot       — Breakdown by robot type
  GET  /api/robotics/by-action      — Breakdown by action type
  GET  /api/robotics/fleet          — Active robot fleet status
  GET  /api/robotics/timeline       — Action trend over time
  POST /api/robotics/evaluate       — Manual action evaluation
  GET  /api/robotics/health         — Engine health check
"""

from __future__ import annotations

import logging
import os
import uuid

from flask import Blueprint, jsonify, request, g

logger = logging.getLogger("OMNIX.Robotics.API")

robotics_bp = Blueprint("robotics", __name__, url_prefix="/api/robotics")


def _get_db():
    import psycopg2
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


@robotics_bp.route("/metrics")
@robotics_bp.route("/metrics.json")
def get_metrics():
    try:
        totals = _queryOne("""
            SELECT
                COUNT(*) AS total_actions,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED') AS blocked,
                COUNT(*) FILTER (WHERE decision='HOLD') AS held,
                COALESCE(AVG(sensor_confidence), 0) AS avg_sensor_confidence,
                COALESCE(AVG(collision_risk), 0) AS avg_collision_risk,
                COALESCE(AVG(decision_score), 0) AS avg_decision_score,
                COALESCE(AVG(trajectory_score), 0) AS avg_trajectory_score,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') AS actions_24h,
                COUNT(DISTINCT robot_id) AS active_robots,
                COALESCE(SUM(safety_incidents_prevented_flag), 0) AS safety_prevented
            FROM (
                SELECT *, 
                    CASE WHEN decision='BLOCKED' AND collision_risk > 65 THEN 1 ELSE 0 END AS safety_incidents_prevented_flag
                FROM robot_actions
            ) t
        """)
        cycles = _queryOne("""
            SELECT COUNT(*) AS total_cycles,
                   COALESCE(SUM(safety_incidents_prevented), 0) AS total_safety_prevented
            FROM robotics_cycle_metrics
        """)

        total = int(totals.get("total_actions", 0)) or 1
        return jsonify({
            "success": True,
            "metrics": {
                "total_actions": int(totals.get("total_actions", 0)),
                "actions_approved": int(totals.get("approved", 0)),
                "actions_blocked": int(totals.get("blocked", 0)),
                "actions_held": int(totals.get("held", 0)),
                "approval_rate": round(int(totals.get("approved", 0)) / total, 4),
                "avg_sensor_confidence": round(float(totals.get("avg_sensor_confidence", 0)), 2),
                "avg_collision_risk": round(float(totals.get("avg_collision_risk", 0)), 2),
                "avg_decision_score": round(float(totals.get("avg_decision_score", 0)), 2),
                "avg_trajectory_score": round(float(totals.get("avg_trajectory_score", 0)), 2),
                "actions_last_24h": int(totals.get("actions_24h", 0)),
                "active_robots": int(totals.get("active_robots", 0)),
                "safety_incidents_prevented": int(cycles.get("total_safety_prevented", 0)) if cycles else 0,
                "simulation_cycles": int(_queryOne("SELECT COUNT(*) AS n FROM robotics_cycle_metrics").get("n", 0)),
            }
        })
    except Exception as e:
        logger.error(f"Robotics metrics error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@robotics_bp.route("/actions")
def get_actions():
    limit = min(int(request.args.get("limit", 50)), 200)
    offset = int(request.args.get("offset", 0))
    industry = request.args.get("industry")
    robot_type = request.args.get("robot_type")
    decision_filter = request.args.get("decision")

    conditions = []
    params: list = []
    if industry:
        conditions.append("industry = %s")
        params.append(industry)
    if robot_type:
        conditions.append("robot_type = %s")
        params.append(robot_type)
    if decision_filter:
        conditions.append("decision = %s")
        params.append(decision_filter.upper())

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    params += [limit, offset]

    try:
        rows = _query(f"""
            SELECT action_id, robot_id, robot_type, industry, action_type, environment,
                   sensor_confidence, collision_risk, sensor_fusion_agreement,
                   battery_pct, temperature_c, payload_kg, speed_ms, proximity_cm,
                   decision, decision_score, block_reason, receipt_id,
                   probability_score, risk_exposure, signal_coherence,
                   trend_persistence, stress_resilience, logic_consistency,
                   trajectory_score, created_at
            FROM robot_actions
            {where}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, params)

        count = _queryOne(f"SELECT COUNT(*) AS n FROM robot_actions {where}",
                          params[:-2] if params[:-2] else None)

        return jsonify({
            "success": True,
            "actions": rows,
            "total": int(count.get("n", 0)) if count else 0,
            "limit": limit,
            "offset": offset,
        })
    except Exception as e:
        logger.error(f"Robotics actions error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@robotics_bp.route("/by-industry")
def get_by_industry():
    try:
        rows = _query("""
            SELECT industry,
                   COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                   COUNT(*) FILTER (WHERE decision='BLOCKED') AS blocked,
                   COALESCE(AVG(sensor_confidence), 0) AS avg_sensor_confidence,
                   COALESCE(AVG(collision_risk), 0) AS avg_collision_risk,
                   COUNT(*) FILTER (WHERE decision='BLOCKED' AND collision_risk > 65) AS safety_prevented
            FROM robot_actions
            GROUP BY industry
            ORDER BY total DESC
        """)
        for r in rows:
            r["approval_rate"] = round(r["approved"] / max(r["total"], 1), 4)
            r["avg_sensor_confidence"] = round(float(r["avg_sensor_confidence"]), 2)
            r["avg_collision_risk"] = round(float(r["avg_collision_risk"]), 2)
        return jsonify({"success": True, "by_industry": rows})
    except Exception as e:
        logger.error(f"Robotics by-industry error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@robotics_bp.route("/by-robot")
def get_by_robot():
    try:
        rows = _query("""
            SELECT robot_type,
                   COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                   COUNT(*) FILTER (WHERE decision='BLOCKED') AS blocked,
                   COALESCE(AVG(sensor_confidence), 0) AS avg_sensor_confidence,
                   COALESCE(AVG(collision_risk), 0) AS avg_collision_risk,
                   COUNT(DISTINCT robot_id) AS robot_count
            FROM robot_actions
            GROUP BY robot_type
            ORDER BY total DESC
        """)
        for r in rows:
            r["approval_rate"] = round(r["approved"] / max(r["total"], 1), 4)
        return jsonify({"success": True, "by_robot": rows})
    except Exception as e:
        logger.error(f"Robotics by-robot error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@robotics_bp.route("/fleet")
def get_fleet():
    """Active fleet status — latest reading per robot."""
    try:
        rows = _query("""
            SELECT DISTINCT ON (robot_id)
                robot_id, robot_type, industry, action_type,
                sensor_confidence, collision_risk, battery_pct, temperature_c,
                decision, decision_score, created_at
            FROM robot_actions
            ORDER BY robot_id, created_at DESC
            LIMIT 100
        """)
        return jsonify({"success": True, "fleet": rows, "total_robots": len(rows)})
    except Exception as e:
        logger.error(f"Robotics fleet error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@robotics_bp.route("/timeline")
def get_timeline():
    hours = int(request.args.get("hours", 12))
    try:
        rows = _query("""
            SELECT
                DATE_TRUNC('hour', created_at) AS hour,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED') AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED') AS blocked,
                COALESCE(AVG(sensor_confidence), 0) AS avg_sensor_confidence,
                COUNT(*) FILTER (WHERE decision='BLOCKED' AND collision_risk > 65) AS safety_events
            FROM robot_actions
            WHERE created_at > NOW() - INTERVAL '1 hour' * %s
            GROUP BY hour
            ORDER BY hour ASC
        """, [hours])
        return jsonify({"success": True, "timeline": rows})
    except Exception as e:
        logger.error(f"Robotics timeline error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@robotics_bp.route("/evaluate", methods=["POST"])
def manual_evaluate():
    data = request.get_json(silent=True) or {}
    try:
        from omnix_core.robotics.robotics_simulator import _generate_action, _evaluate_action
        fleet: dict = {}
        if not data:
            action_data = _generate_action(fleet)
        else:
            action_data = {
                "action_id": f"MANUAL-{uuid.uuid4().hex[:8].upper()}",
                "robot_id": data.get("robot_id", f"RBT-MANUAL-{uuid.uuid4().hex[:6].upper()}"),
                "robot_type": data.get("robot_type", "Industrial_Arm"),
                "industry": data.get("industry", "Automotive"),
                "action_type": data.get("action_type", "assembly_critical"),
                "environment": data.get("environment", "structured"),
                "sensor_confidence": float(data.get("sensor_confidence", 85)),
                "lidar_agreement": float(data.get("lidar_agreement", 88)),
                "camera_confidence": float(data.get("camera_confidence", 82)),
                "imu_stability": float(data.get("imu_stability", 90)),
                "proximity_cm": float(data.get("proximity_cm", 150)),
                "payload_kg": float(data.get("payload_kg", 50)),
                "max_payload_kg": float(data.get("max_payload_kg", 250)),
                "speed_ms": float(data.get("speed_ms", 1.2)),
                "max_speed_ms": float(data.get("max_speed_ms", 2.5)),
                "battery_pct": float(data.get("battery_pct", 75)),
                "motor_temp_c": float(data.get("motor_temp_c", 55)),
                "joint_stress_pct": float(data.get("joint_stress_pct", 40)),
                "mission_logic_score": float(data.get("mission_logic_score", 88)),
                "environmental_stability": float(data.get("environmental_stability", 82)),
                "historical_success_rate": float(data.get("historical_success_rate", 92)),
            }
        result = _evaluate_action(action_data)
        return jsonify({"success": True, "evaluation": result})
    except Exception as e:
        logger.error(f"Robotics manual evaluate error: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@robotics_bp.route("/health")
def health():
    try:
        last = _queryOne("""
            SELECT created_at, cycle_number
            FROM robotics_cycle_metrics
            ORDER BY created_at DESC LIMIT 1
        """)
        total = _queryOne("SELECT COUNT(*) AS n FROM robot_actions")
        fleet = _queryOne("SELECT COUNT(DISTINCT robot_id) AS n FROM robot_actions")
        return jsonify({
            "success": True,
            "status": "operational",
            "total_actions": int(total.get("n", 0)) if total else 0,
            "active_robots": int(fleet.get("n", 0)) if fleet else 0,
            "last_cycle": last.get("cycle_number") if last else 0,
            "last_cycle_at": last.get("created_at").isoformat() if last and last.get("created_at") else None,
        })
    except Exception as e:
        return jsonify({"success": False, "status": "error", "error": "Internal server error"}), 500
