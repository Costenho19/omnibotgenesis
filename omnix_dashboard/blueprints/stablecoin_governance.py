"""
OMNIX Stablecoin Reserve Governance API Blueprint
ADR-SRG-001: Stablecoin & Tokenization Governance Vertical (INTERNAL)

REST endpoints for the Stablecoin Reserve Governance vertical.
All routes require internal deployment — not exposed in public nav.

Routes:
  GET  /api/stablecoin/metrics      — Summary KPIs (volume, coverage, peg health, block rates)
  GET  /api/stablecoin/decisions    — Recent reserve governance decisions
  GET  /api/stablecoin/by-type      — Breakdown by decision type
  GET  /api/stablecoin/by-asset     — Breakdown by reserve asset
  GET  /api/stablecoin/by-jurisdiction — Breakdown by jurisdiction
  GET  /api/stablecoin/timeline     — Decision + volume trend over last 48h
  GET  /api/stablecoin/live-feed    — Last 12 decisions for live feed
  POST /api/stablecoin/evaluate     — Manual decision evaluation (what-if)
  GET  /api/stablecoin/health       — Engine health check
"""

from __future__ import annotations

import logging
import os

from flask import Blueprint, jsonify, request, g

logger = logging.getLogger("OMNIX.Stablecoin.API")

stablecoin_bp = Blueprint("stablecoin", __name__, url_prefix="/api/stablecoin")


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


@stablecoin_bp.route("/metrics")
@stablecoin_bp.route("/metrics.json")
def get_metrics():
    try:
        totals = _queryOne("""
            SELECT
                COUNT(*)                                                         AS total_decisions,
                COUNT(*) FILTER (WHERE decision='APPROVED')                      AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')                       AS blocked,
                COUNT(*) FILTER (WHERE decision='HOLD')                          AS held,
                COALESCE(SUM(transaction_amount_usd), 0)                         AS total_volume_usd,
                COALESCE(SUM(transaction_amount_usd) FILTER (WHERE decision='APPROVED'), 0) AS approved_volume_usd,
                COALESCE(SUM(transaction_amount_usd) FILTER (WHERE decision='BLOCKED'), 0)  AS blocked_volume_usd,
                COALESCE(AVG(peg_deviation_pct), 0)                              AS avg_peg_deviation,
                COALESCE(AVG(reserve_coverage_ratio), 0)                         AS avg_reserve_coverage,
                COALESCE(AVG(liquid_reserve_ratio), 0)                           AS avg_liquid_ratio,
                COALESCE(AVG(crypto_exposure_pct), 0)                            AS avg_crypto_exposure,
                COALESCE(AVG(decision_score), 0)                                 AS avg_decision_score,
                COALESCE(AVG(transaction_risk_usd), 0)                           AS avg_transaction_risk,
                COUNT(*) FILTER (WHERE hard_block_reason IS NOT NULL)            AS hard_blocks,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') AS decisions_24h,
                COUNT(DISTINCT reserve_asset)                                    AS assets_active,
                COUNT(DISTINCT jurisdiction)                                     AS jurisdictions_active
            FROM stablecoin_decisions
        """)

        cycles = _queryOne("SELECT COUNT(*) AS total_cycles FROM stablecoin_cycle_metrics")

        if not totals:
            return jsonify({"success": False, "error": "No data yet"}), 404

        total    = int(totals.get("total_decisions", 0)) or 1
        approved = int(totals.get("approved", 0))
        blocked  = int(totals.get("blocked", 0))

        return jsonify({
            "success": True,
            "metrics": {
                "total_decisions":         total,
                "decisions_approved":      approved,
                "decisions_blocked":       blocked,
                "decisions_held":          int(totals.get("held", 0)),
                "approval_rate":           round(approved / total, 4),
                "block_rate":              round(blocked / total, 4),
                "total_volume_usd":        round(float(totals.get("total_volume_usd", 0)), 2),
                "approved_volume_usd":     round(float(totals.get("approved_volume_usd", 0)), 2),
                "blocked_volume_usd":      round(float(totals.get("blocked_volume_usd", 0)), 2),
                "avg_peg_deviation":       round(float(totals.get("avg_peg_deviation", 0)), 4),
                "avg_reserve_coverage":    round(float(totals.get("avg_reserve_coverage", 0)), 2),
                "avg_liquid_ratio":        round(float(totals.get("avg_liquid_ratio", 0)), 2),
                "avg_crypto_exposure":     round(float(totals.get("avg_crypto_exposure", 0)), 2),
                "avg_decision_score":      round(float(totals.get("avg_decision_score", 0)), 2),
                "avg_transaction_risk":    round(float(totals.get("avg_transaction_risk", 0)), 2),
                "hard_blocks":             int(totals.get("hard_blocks", 0)),
                "decisions_last_24h":      int(totals.get("decisions_24h", 0)),
                "assets_active":           int(totals.get("assets_active", 0)),
                "jurisdictions_active":    int(totals.get("jurisdictions_active", 0)),
                "simulation_cycles":       int((cycles or {}).get("total_cycles", 0)),
            }
        })
    except Exception as e:
        logger.error(f"get_metrics error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@stablecoin_bp.route("/decisions")
def get_decisions():
    try:
        limit = min(int(request.args.get("limit", 50)), 200)
        rows = _query("""
            SELECT
                decision_id, decision_type, reserve_asset, jurisdiction,
                transaction_amount_usd, total_supply_usd,
                peg_deviation_pct, reserve_coverage_ratio, liquid_reserve_ratio,
                crypto_exposure_pct,
                decision, decision_score, block_reason, hard_block_reason,
                probability_score, risk_exposure, signal_coherence,
                trend_persistence, stress_resilience, logic_consistency,
                trajectory_score, transaction_risk_usd,
                receipt_id, domain, created_at
            FROM stablecoin_decisions
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


@stablecoin_bp.route("/live-feed")
def get_live_feed():
    try:
        rows = _query("""
            SELECT
                decision_id, decision_type, reserve_asset, jurisdiction,
                transaction_amount_usd, peg_deviation_pct,
                reserve_coverage_ratio, liquid_reserve_ratio,
                decision, decision_score, block_reason, hard_block_reason,
                transaction_risk_usd, receipt_id, created_at
            FROM stablecoin_decisions
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


@stablecoin_bp.route("/by-type")
def get_by_type():
    try:
        rows = _query("""
            SELECT
                decision_type,
                COUNT(*)                                                           AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED')                        AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')                         AS blocked,
                ROUND(SUM(transaction_amount_usd)::numeric, 2)                    AS total_volume_usd,
                ROUND(AVG(decision_score)::numeric, 2)                            AS avg_score,
                ROUND(AVG(peg_deviation_pct)::numeric, 4)                         AS avg_peg_deviation,
                ROUND(
                    COUNT(*) FILTER (WHERE decision='APPROVED')::numeric
                    / NULLIF(COUNT(*), 0), 4
                )                                                                  AS approval_rate
            FROM stablecoin_decisions
            GROUP BY decision_type
            ORDER BY total DESC
        """)
        return jsonify({"success": True, "by_type": rows})
    except Exception as e:
        logger.error(f"get_by_type error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@stablecoin_bp.route("/by-asset")
def get_by_asset():
    try:
        rows = _query("""
            SELECT
                reserve_asset,
                COUNT(*)                                                           AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED')                        AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')                         AS blocked,
                ROUND(SUM(transaction_amount_usd)::numeric, 2)                    AS total_volume_usd,
                ROUND(AVG(reserve_coverage_ratio)::numeric, 2)                    AS avg_coverage,
                ROUND(AVG(liquid_reserve_ratio)::numeric, 2)                      AS avg_liquid_ratio,
                ROUND(AVG(crypto_exposure_pct)::numeric, 2)                       AS avg_crypto_exposure,
                ROUND(
                    COUNT(*) FILTER (WHERE decision='APPROVED')::numeric
                    / NULLIF(COUNT(*), 0), 4
                )                                                                  AS approval_rate
            FROM stablecoin_decisions
            GROUP BY reserve_asset
            ORDER BY total_volume_usd DESC
        """)
        return jsonify({"success": True, "by_asset": rows})
    except Exception as e:
        logger.error(f"get_by_asset error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@stablecoin_bp.route("/by-jurisdiction")
def get_by_jurisdiction():
    try:
        rows = _query("""
            SELECT
                jurisdiction,
                COUNT(*)                                                           AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED')                        AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')                         AS blocked,
                ROUND(SUM(transaction_amount_usd)::numeric, 2)                    AS total_volume_usd,
                ROUND(AVG(reserve_coverage_ratio)::numeric, 2)                    AS avg_coverage,
                ROUND(AVG(peg_deviation_pct)::numeric, 4)                         AS avg_peg_deviation,
                ROUND(
                    COUNT(*) FILTER (WHERE decision='APPROVED')::numeric
                    / NULLIF(COUNT(*), 0), 4
                )                                                                  AS approval_rate
            FROM stablecoin_decisions
            GROUP BY jurisdiction
            ORDER BY total_volume_usd DESC
        """)
        return jsonify({"success": True, "by_jurisdiction": rows})
    except Exception as e:
        logger.error(f"get_by_jurisdiction error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@stablecoin_bp.route("/timeline")
def get_timeline():
    try:
        rows = _query("""
            SELECT
                DATE_TRUNC('hour', created_at)                            AS hour,
                COUNT(*)                                                   AS total,
                COUNT(*) FILTER (WHERE decision='APPROVED')               AS approved,
                COUNT(*) FILTER (WHERE decision='BLOCKED')                AS blocked,
                ROUND(SUM(transaction_amount_usd)::numeric, 2)           AS total_volume_usd,
                ROUND(AVG(decision_score)::numeric, 2)                   AS avg_score,
                ROUND(AVG(peg_deviation_pct)::numeric, 4)                AS avg_peg_deviation
            FROM stablecoin_decisions
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


@stablecoin_bp.route("/evaluate", methods=["POST"])
def manual_evaluate():
    try:
        from omnix_core.stablecoin.stablecoin_signal_adapter import (
            StablecoinDecisionInput,
            StablecoinSignalAdapter,
        )
        data = request.get_json(force=True)

        decision_input = StablecoinDecisionInput(
            decision_type=data.get("decision_type", "reserve_rebalancing"),
            reserve_asset=data.get("reserve_asset", "US_Treasury_Bills"),
            jurisdiction=data.get("jurisdiction", "EU_MiCA"),
            peg_deviation_pct=float(data.get("peg_deviation_pct", 0.05)),
            reserve_coverage_ratio=float(data.get("reserve_coverage_ratio", 105.0)),
            liquid_reserve_ratio=float(data.get("liquid_reserve_ratio", 78.0)),
            crypto_exposure_pct=float(data.get("crypto_exposure_pct", 5.0)),
            concentration_risk=float(data.get("concentration_risk", 25.0)),
            counterparty_credit_risk=float(data.get("counterparty_credit_risk", 15.0)),
            reserve_duration_days=float(data.get("reserve_duration_days", 30.0)),
            on_chain_off_chain_alignment=float(data.get("on_chain_off_chain_alignment", 92.0)),
            cross_exchange_consistency=float(data.get("cross_exchange_consistency", 88.0)),
            oracle_confidence=float(data.get("oracle_confidence", 85.0)),
            reserve_flow_stability=float(data.get("reserve_flow_stability", 72.0)),
            tvl_trend_7d=float(data.get("tvl_trend_7d", 58.0)),
            redemption_pattern_stability=float(data.get("redemption_pattern_stability", 68.0)),
            instant_liquidity_coverage=float(data.get("instant_liquidity_coverage", 70.0)),
            emergency_reserve_buffer=float(data.get("emergency_reserve_buffer", 55.0)),
            credit_facility_available=float(data.get("credit_facility_available", 60.0)),
            mica_compliance_score=float(data.get("mica_compliance_score", 78.0)),
            aml_screening_completeness=float(data.get("aml_screening_completeness", 85.0)),
            audit_completeness=float(data.get("audit_completeness", 80.0)),
            aml_flag=bool(data.get("aml_flag", False)),
            sanctions_flag=bool(data.get("sanctions_flag", False)),
            counterparty_credit_default=bool(data.get("counterparty_credit_default", False)),
            transaction_amount_usd=float(data.get("transaction_amount_usd", 1_000_000.0)),
            total_supply_usd=float(data.get("total_supply_usd", 100_000_000.0)),
        )

        adapter = StablecoinSignalAdapter()
        signals = adapter.adapt(decision_input)

        return jsonify({
            "success":               True,
            "signals":               signals.to_omnix_dict(),
            "recommendation":        signals.recommendation,
            "peg_deviation_pct":     signals.peg_deviation_pct,
            "reserve_coverage_ratio": signals.reserve_coverage_ratio,
            "liquid_reserve_ratio":  signals.liquid_reserve_ratio,
            "crypto_exposure_pct":   signals.crypto_exposure_pct,
            "transaction_risk_usd":  signals.transaction_risk_usd,
            "hard_block_reason":     signals.hard_block_reason,
        })
    except Exception as e:
        logger.error(f"manual_evaluate error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@stablecoin_bp.route("/health")
def health():
    try:
        count  = _queryOne("SELECT COUNT(*) AS cnt FROM stablecoin_decisions")
        cycles = _queryOne("SELECT COUNT(*) AS cnt FROM stablecoin_cycle_metrics")
        return jsonify({
            "success":          True,
            "status":           "operational",
            "total_decisions":  int((count  or {}).get("cnt", 0)),
            "total_cycles":     int((cycles or {}).get("cnt", 0)),
            "domain":           "stablecoin",
            "receipt_prefix":   "OMNIX-SRG",
            "adr":              "ADR-SRG-001",
        })
    except Exception as e:
        return jsonify({"success": False, "status": "degraded", "error": str(e)}), 500
