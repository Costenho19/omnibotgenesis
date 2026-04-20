"""
AVM Real Alerts — ADR-076 extension

Sends real-time notifications when the AVM detects critical schema or drift anomalies.
Alerts go to Telegram. Falls back silently if not configured — governance is never
blocked by a missing alert channel.

Environment variables required:
    TELEGRAM_BOT_TOKEN    — bot token (already present in OMNIX)
    OMNIX_ADMIN_CHAT_ID   — numeric chat ID of the admin who receives alerts

Set OMNIX_ADMIN_CHAT_ID to your personal Telegram chat ID or a monitoring group ID.
"""
from __future__ import annotations

import logging
import os
import threading
import urllib.request
import urllib.parse
import json
from datetime import datetime, timezone

logger = logging.getLogger("OMNIX.AVM.Alerts")

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

_ALERT_ICONS = {
    "SCHEMA_ANOMALY_NONE":    "🚨",
    "SCHEMA_ANOMALY_PARTIAL": "⚠️",
    "DRIFT_ANOMALY":          "💥",
    "SCHEMA_MISMATCH_DB":     "🛑",
}


def _send_telegram(token: str, chat_id: str, text: str) -> None:
    url = _TELEGRAM_API.format(token=token)
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        resp.read()


def fire_avm_alert(
    event_type: str,
    domain: str,
    detail: str,
    snapshot_id: str = "UNKNOWN",
) -> None:
    """
    Send a real Telegram alert for a critical AVM anomaly.

    Args:
        event_type:  One of SCHEMA_ANOMALY_NONE, SCHEMA_ANOMALY_PARTIAL,
                     DRIFT_ANOMALY, SCHEMA_MISMATCH_DB
        domain:      AVM domain name (e.g. 'real_estate')
        detail:      Human-readable description of the anomaly
        snapshot_id: Snapshot identifier (for traceability)

    Runs in a daemon thread so it never blocks the governance pipeline.
    Falls back silently if env vars are not configured.
    """
    if os.environ.get("TESTING", "").lower() == "true":
        logger.debug(f"[AVM.Alerts] TESTING mode — alert suppressed: {event_type} domain={domain}")
        return

    token   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("OMNIX_ADMIN_CHAT_ID", "")

    if not token or not chat_id:
        logger.warning(
            f"[AVM.Alerts] Alert NOT sent — TELEGRAM_BOT_TOKEN or OMNIX_ADMIN_CHAT_ID "
            f"not set. event={event_type} domain={domain}"
        )
        return

    icon = _ALERT_ICONS.get(event_type, "⚠️")
    now  = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    text = (
        f"{icon} <b>OMNIX AVM ALERT</b>\n"
        f"Event: <code>{event_type}</code>\n"
        f"Domain: <code>{domain}</code>\n"
        f"Snapshot: <code>{snapshot_id}</code>\n"
        f"Time: {now}\n\n"
        f"{detail}"
    )

    def _send() -> None:
        try:
            _send_telegram(token, chat_id, text)
            logger.info(f"[AVM.Alerts] Alert sent — event={event_type} domain={domain}")
        except Exception as exc:
            logger.warning(
                f"[AVM.Alerts] Failed to send Telegram alert: {exc} "
                f"— event={event_type} domain={domain}"
            )

    t = threading.Thread(target=_send, daemon=True, name=f"avm-alert-{domain}")
    t.start()
