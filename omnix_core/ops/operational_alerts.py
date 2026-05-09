"""
OMNIX — Operational Alert Dispatcher  (ADR-150)

Sends structured Telegram alerts for critical operational events.
Designed to be called from health checks, WAL reconciliation,
startup probes, and any module that detects a critical condition.

Alert levels:
  CRITICAL  — immediate action required (DB down, PQC keys missing, WAL overflow)
  WARNING   — degraded state (Redis unreachable, WAL pending, PQC fallback)
  INFO      — system events (startup, recovery, scheduled backup completed)

All alerts include:
  - timestamp UTC
  - OMNIX version
  - subsystem name
  - alert level badge
  - detail message
  - governance baseline reference

ADR-150: Operational alerts are non-blocking. A failure to send a
Telegram message must never cause a governance pipeline failure.
"""

import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

OMNIX_VERSION     = "6.6.0"
ALERT_COOLDOWN_S  = 300   # 5 min between identical alerts (same subsystem+level)

_alert_cooldowns: dict = {}   # {alert_key: last_sent_ts}

LEVEL_BADGES = {
    "CRITICAL": "🔴 CRITICAL",
    "WARNING":  "🟡 WARNING",
    "INFO":     "🟢 INFO",
    "RECOVERY": "✅ RECOVERY",
}


def _cooldown_key(subsystem: str, level: str) -> str:
    return f"{subsystem}:{level}"


def _is_cooled(subsystem: str, level: str) -> bool:
    key = _cooldown_key(subsystem, level)
    last = _alert_cooldowns.get(key, 0)
    return (time.monotonic() - last) < ALERT_COOLDOWN_S


def _mark_sent(subsystem: str, level: str) -> None:
    _alert_cooldowns[_cooldown_key(subsystem, level)] = time.monotonic()


def _build_message(
    level: str,
    subsystem: str,
    detail: str,
    extra: Optional[str] = None,
) -> str:
    badge = LEVEL_BADGES.get(level, f"[{level}]")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        f"{badge}",
        f"",
        f"📡 <b>OMNIX QUANTUM</b> — Operational Alert",
        f"🕐 {ts}",
        f"⚙️ Subsystem: <code>{subsystem}</code>",
        f"",
        f"{detail}",
    ]
    if extra:
        lines.append(f"")
        lines.append(f"ℹ️ {extra}")
    lines += [
        f"",
        f"<i>v{OMNIX_VERSION} · OMNIX-BASELINE-2026-Q2-001</i>",
    ]
    return "\n".join(lines)


def _send_telegram(message: str) -> bool:
    """Send a Telegram message to the admin. Non-blocking — never raises."""
    try:
        import requests
        token   = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_ADMIN_USER_ID", "")
        if not token or not chat_id:
            logger.debug("[OpsAlert] TELEGRAM_BOT_TOKEN or TELEGRAM_ADMIN_USER_ID not set — skipping")
            return False
        if os.getenv("TESTING", "").lower() == "true":
            logger.debug(f"[OpsAlert][TEST MODE] Would send: {message[:80]}…")
            return True
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id":    chat_id,
                "text":       message,
                "parse_mode": "HTML",
            },
            timeout=8,
        )
        if resp.status_code == 200:
            return True
        logger.warning(f"[OpsAlert] Telegram API returned {resp.status_code}: {resp.text[:200]}")
        return False
    except Exception as e:
        logger.warning(f"[OpsAlert] Failed to send alert: {e}")
        return False


# ── Public API ─────────────────────────────────────────────────────────────────

def alert_critical(
    subsystem: str,
    detail: str,
    extra: Optional[str] = None,
    force: bool = False,
) -> bool:
    """
    Send a CRITICAL operational alert.

    Args:
        subsystem: e.g. "database", "receipt_wal", "pqc_dilithium3"
        detail:    Human-readable description of the critical condition
        extra:     Optional remediation hint
        force:     Bypass cooldown (use for startup alerts)

    Returns:
        True if message was sent, False otherwise (alert still logged).
    """
    logger.error(f"[OpsAlert][CRITICAL] subsystem={subsystem} — {detail}")
    if not force and _is_cooled(subsystem, "CRITICAL"):
        logger.debug(f"[OpsAlert] Cooldown active for {subsystem}:CRITICAL — skipping Telegram")
        return False
    msg = _build_message("CRITICAL", subsystem, detail, extra)
    sent = _send_telegram(msg)
    if sent:
        _mark_sent(subsystem, "CRITICAL")
    return sent


def alert_warning(
    subsystem: str,
    detail: str,
    extra: Optional[str] = None,
) -> bool:
    """Send a WARNING operational alert (degraded but not down)."""
    logger.warning(f"[OpsAlert][WARNING] subsystem={subsystem} — {detail}")
    if _is_cooled(subsystem, "WARNING"):
        return False
    msg = _build_message("WARNING", subsystem, detail, extra)
    sent = _send_telegram(msg)
    if sent:
        _mark_sent(subsystem, "WARNING")
    return sent


def alert_info(subsystem: str, detail: str) -> bool:
    """Send an INFO operational alert (non-critical system event)."""
    logger.info(f"[OpsAlert][INFO] subsystem={subsystem} — {detail}")
    msg = _build_message("INFO", subsystem, detail)
    return _send_telegram(msg)


def alert_recovery(subsystem: str, detail: str) -> bool:
    """Send a RECOVERY alert when a previously degraded subsystem recovers."""
    logger.info(f"[OpsAlert][RECOVERY] subsystem={subsystem} — {detail}")
    # Clear cooldowns so future alerts go through immediately
    for level in ("CRITICAL", "WARNING"):
        _alert_cooldowns.pop(_cooldown_key(subsystem, level), None)
    msg = _build_message("RECOVERY", subsystem, detail)
    return _send_telegram(msg)


def alert_startup(version: str, pqc_mode: str, db_status: str) -> bool:
    """
    Send a startup confirmation alert.
    Called once when the API server finishes initializing.
    """
    detail = (
        f"🚀 OMNIX API Server started successfully.\n"
        f"   Version: <code>{version}</code>\n"
        f"   PQC mode: <code>{pqc_mode}</code>\n"
        f"   Database: <code>{db_status}</code>"
    )
    return alert_info("server_startup", detail)


def evaluate_health_and_alert(health_report) -> None:
    """
    Evaluate a HealthReport and dispatch alerts for any subsystem
    that is DOWN or DEGRADED.

    Called automatically by the /api/health endpoint and the
    health check background scheduler (when implemented).

    Args:
        health_report: HealthReport from omnix_core.ops.health_check.run_health_check()
    """
    for sub in health_report.subsystems:
        if sub.status == "DOWN" and sub.critical:
            alert_critical(
                subsystem=sub.name,
                detail=f"Subsystem <code>{sub.name}</code> is <b>DOWN</b>.\n{sub.detail}",
                extra="Check Railway logs and DATABASE_URL / REDIS_URL environment variables.",
            )
        elif sub.status == "DOWN":
            alert_warning(
                subsystem=sub.name,
                detail=f"Non-critical subsystem <code>{sub.name}</code> is DOWN.\n{sub.detail}",
            )
        elif sub.status == "DEGRADED":
            alert_warning(
                subsystem=sub.name,
                detail=f"Subsystem <code>{sub.name}</code> is DEGRADED.\n{sub.detail}",
            )

    if health_report.wal_pending >= 10:
        alert_critical(
            subsystem="receipt_wal",
            detail=(
                f"WAL has <b>{health_report.wal_pending} pending receipts</b>.\n"
                f"The database may be down. Governance decisions are durable in WAL "
                f"but will not be queryable until DB recovers and reconcile_wal() runs."
            ),
            extra="Call /api/health/reconcile-wal when DB is restored.",
        )
