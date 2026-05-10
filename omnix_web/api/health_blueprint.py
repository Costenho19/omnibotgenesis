"""
OMNIX — Health & Operational Readiness Blueprint  (ADR-150)

Endpoints:
  GET  /api/health             — full subsystem health report (JSON)
  GET  /api/health/live        — liveness probe (200) for Railway / load balancers
  GET  /api/health/ready       — readiness probe (200 / 503) — DB must be UP
  POST /api/health/reconcile-wal — trigger WAL reconciliation (admin only)
"""

import logging
import os
import sys
import time
from datetime import datetime, timezone
from functools import wraps

from flask import Blueprint, jsonify, request

# ── Path bootstrap — same logic as server.py so omnix_core is importable ──────
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
if _WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, _WORKSPACE_ROOT)

logger = logging.getLogger(__name__)

health_bp = Blueprint("health", __name__)

OMNIX_VERSION        = "6.6.0"
GOVERNANCE_BASELINE  = "OMNIX-BASELINE-2026-Q2-001"


# ── Minimal auth for reconcile-wal ────────────────────────────────────────────

def _admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        allowed_ips_raw = os.getenv("ADMIN_ALLOWED_IPS", "127.0.0.1")
        allowed_ips = [ip.strip() for ip in allowed_ips_raw.split(",") if ip.strip()]
        remote = request.remote_addr or ""
        admin_token = os.getenv("ADMIN_TOKEN", "")
        provided_token = request.headers.get("X-Admin-Token", "")
        if remote in allowed_ips:
            return f(*args, **kwargs)
        if admin_token and provided_token and provided_token == admin_token:
            return f(*args, **kwargs)
        return jsonify({"error": "Unauthorized"}), 403
    return decorated


# ── Direct DB probe (no omnix_core dependency) ────────────────────────────────

def _probe_db_direct(db_url):
    """Probe DB using psycopg2 directly — works even when omnix_core is absent."""
    if not db_url:
        return False, "DATABASE_URL not configured"
    try:
        import psycopg2  # noqa
        conn = psycopg2.connect(db_url, connect_timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return True, "OK"
    except ImportError:
        return False, "psycopg2 not installed"
    except Exception as e:
        return False, str(e)[:120]


# ── /api/health ───────────────────────────────────────────────────────────────

@health_bp.route("/api/health", methods=["GET"])
def health_full():
    send_alerts = request.args.get("alerts", "true").lower() != "false"
    ts = datetime.now(timezone.utc).isoformat()

    # Try full deep-probe report via omnix_core
    try:
        from omnix_core.ops.health_check import run_health_check
        from omnix_core.ops.operational_alerts import evaluate_health_and_alert

        report = run_health_check()

        if send_alerts and os.getenv("TESTING", "").lower() != "true":
            try:
                evaluate_health_and_alert(report)
            except Exception as ae:
                logger.warning(f"[health_bp] Alert dispatch failed: {ae}")

        status_code = 200 if report.status in ("UP", "DEGRADED") else 503
        return jsonify(report.to_dict()), status_code

    except Exception as e:
        logger.warning(f"[health_bp] Deep probe unavailable — using fallback: {e}")

    # Fallback — direct DB probe only
    db_ok, db_detail = _probe_db_direct(os.getenv("DATABASE_URL"))
    overall = "UP" if db_ok else "DEGRADED"
    return jsonify({
        "status":              overall,
        "timestamp_utc":       ts,
        "version":             OMNIX_VERSION,
        "governance_baseline": GOVERNANCE_BASELINE,
        "uptime_seconds":      None,
        "wal_pending":         0,
        "adr_count":           150,
        "pqc_mode":            "dilithium3-persistent" if os.getenv("OMNIX_SIGNING_SECRET_KEY_B64") else "sha256-only",
        "note":                "fallback mode — omnix_core not in path",
        "subsystems": [
            {"name": "database", "status": "UP" if db_ok else "DOWN",
             "latency_ms": None, "detail": db_detail, "critical": True},
        ],
    }), 200


# ── /api/health/live ──────────────────────────────────────────────────────────

@health_bp.route("/api/health/live", methods=["GET"])
def health_live():
    """Liveness probe — always 200 if the process is alive."""
    return jsonify({
        "alive":         True,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }), 200


# ── /api/health/ready ─────────────────────────────────────────────────────────

@health_bp.route("/api/health/ready", methods=["GET"])
def health_ready():
    """Readiness probe — 200 only when DB is reachable."""
    ts = datetime.now(timezone.utc).isoformat()

    # Try deep probe first
    try:
        from omnix_core.ops.health_check import _probe_database, _probe_governance_engine
        db_probe  = _probe_database(os.getenv("DATABASE_URL"))
        gov_probe = _probe_governance_engine()
        ready = db_probe.status == "UP" and gov_probe.status == "UP"
        return jsonify({
            "ready":             ready,
            "database":          db_probe.status,
            "governance_engine": gov_probe.status,
            "timestamp_utc":     ts,
        }), 200 if ready else 503

    except Exception:
        pass

    # Fallback — direct psycopg2 probe
    db_ok, db_detail = _probe_db_direct(os.getenv("DATABASE_URL"))
    return jsonify({
        "ready":         db_ok,
        "database":      "UP" if db_ok else "DOWN",
        "detail":        db_detail,
        "timestamp_utc": ts,
        "note":          "fallback mode",
    }), 200 if db_ok else 503


# ── /api/health/reconcile-wal ─────────────────────────────────────────────────

@health_bp.route("/api/health/reconcile-wal", methods=["POST"])
@_admin_required
def reconcile_wal():
    try:
        from omnix_core.evidence.receipt_wal import get_receipt_wal
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            return jsonify({"error": "DATABASE_URL not configured"}), 503

        engine = DecisionReceiptEngine(db_url=db_url)
        wal    = get_receipt_wal()

        pending_before = wal.wal_size()
        reconciled     = wal.reconcile_wal(lambda r: engine.store_receipt(r))

        return jsonify({
            "reconciled":     reconciled,
            "pending_before": pending_before,
            "pending_after":  wal.wal_size(),
        }), 200

    except Exception as e:
        logger.error(f"[health_bp] WAL reconciliation failed: {e}")
        return jsonify({"error": str(e)}), 500
