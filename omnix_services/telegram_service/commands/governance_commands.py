"""
OMNIX Governance Commands — ADR-058
Bot Telegram: comandos de gobernanza institucional.

Comandos implementados:
  /evaluar [escenario]  — Ejecuta el pipeline de 11 checkpoints y devuelve BLOCKED/APPROVED + receipt ID
  /evaluate             — Alias inglés
  /gobernanza           — Dashboard de estado del sistema de gobernanza
  /governance           — Alias inglés
  /velos                — Log de pushes al gateway Velos (solo admin) — ADR-052
  /recibo [n]           — Últimos N recibos PQC de gobernanza (solo admin) — ADR-028
  /receipt [n]          — Alias inglés

Arquitectura:
  - /evaluar usa HTTP POST a OMNIX_WEB_URL (env var, default localhost:5000)
    Razón: bot y web server son servicios Railway separados (recomendación arquitecto ADR-058)
  - /velos y /recibo consultan PostgreSQL directamente (DATABASE_URL) — acceso trusted
  - /gobernanza hace un health ping al sandbox + muestra estado del Critical Override Layer
  - Rate limit interno por user_id aplicado en /evaluar (max 5 eval/hora por usuario)
  - Los errores internos nunca se exponen al usuario (solo mensajes amigables)

ADR-028: External Signal Evaluation API
ADR-052: Velos Gateway Push + API Key Expiry
ADR-057: Critical Override Hybrid Expansion (Grupos 1-7)
ADR-058: Bot Governance Integration
"""

import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timezone

import requests

from omnix_config.settings import settings

logger = logging.getLogger(__name__)


def _is_admin(user_id: str) -> bool:
    """
    Verifica si un user_id de Telegram es el administrador del sistema.
    Replica la lógica de enterprise_bot._check_admin_permission para evitar
    import circular (enterprise_bot ← governance_commands ← enterprise_bot).
    ADR-058.
    """
    try:
        return int(user_id) == int(settings.TELEGRAM_ADMIN_ID)
    except (ValueError, TypeError):
        return False

# ── Rate limit por user_id para /evaluar ──────────────────────────────────────
_EVAL_RATE_LIMIT: dict = defaultdict(list)
_EVAL_RATE_MAX   = 5      # máximo 5 evaluaciones por usuario
_EVAL_RATE_WIN   = 3600   # ventana de 1 hora (segundos)


def _is_eval_rate_limited(user_id: str) -> bool:
    now   = time.time()
    start = now - _EVAL_RATE_WIN
    _EVAL_RATE_LIMIT[user_id] = [t for t in _EVAL_RATE_LIMIT[user_id] if t > start]
    if len(_EVAL_RATE_LIMIT[user_id]) >= _EVAL_RATE_MAX:
        return True
    _EVAL_RATE_LIMIT[user_id].append(now)
    return False


def _sandbox_url() -> str:
    return os.environ.get("OMNIX_WEB_URL", "http://localhost:5000")


def _db_connect():
    """Abre una conexión PostgreSQL usando DATABASE_URL. Lanza si no está configurado."""
    import psycopg2
    import psycopg2.extras
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL no configurado")
    return psycopg2.connect(db_url), psycopg2.extras


# ── /evaluar ─────────────────────────────────────────────────────────────────

async def evaluar_command(self, update, context):
    """
    /evaluar [escenario] — Pipeline de gobernanza OMNIX 11 checkpoints.
    Llama al sandbox API via HTTP. Timeout 60s. Rate limit: 5/hora por usuario.
    ADR-028, ADR-057, ADR-058.
    """
    user    = update.effective_user
    user_id = str(user.id)

    scenario = " ".join(context.args).strip() if context.args else ""

    if not scenario:
        await update.message.reply_text(
            "🏛️ *OMNIX Governance Evaluator*\n\n"
            "Envía cualquier escenario de decisión de alto impacto:\n\n"
            "`/evaluar [descripción del escenario]`\n\n"
            "*Ejemplo:*\n"
            "`/evaluar Meridian Capital $180M Murabaha, beneficial owner no divulgado,"
            " no AML officer, subsidiaria en lista de control de exportaciones de la UE.`\n\n"
            "El pipeline de 11 checkpoints evalúa: integridad de señal, riesgo,"
            " ética, AML, fraude y cumplimiento jurisdiccional.\n\n"
            "_OMNIX Decision Governance — Harold Nunes, Dubai 2026_",
            parse_mode="Markdown",
        )
        return

    if _is_eval_rate_limited(user_id):
        await update.message.reply_text(
            "⏳ Límite de evaluaciones alcanzado (5/hora). Intenta en unos minutos."
        )
        return

    processing_msg = await update.message.reply_text(
        "🔍 *Procesando en la red de gobernanza...*\n"
        "_Pipeline de 11 checkpoints activo. Puede tomar hasta 60 segundos._",
        parse_mode="Markdown",
    )

    try:
        endpoint = f"{_sandbox_url()}/api/public/sandbox/evaluate"
        resp = requests.post(
            endpoint,
            json={
                "scenario":     scenario,
                "entity_name":  "Telegram Evaluation",
                "language":     "auto",
            },
            timeout=60,
        )

        if resp.status_code != 200:
            logger.warning(f"[EVALUAR] HTTP {resp.status_code} from sandbox")
            await processing_msg.edit_text(
                f"⚠️ El evaluador devolvió un error (HTTP {resp.status_code}).\n"
                "Intenta de nuevo en unos instantes."
            )
            return

        data       = resp.json()
        decision   = data.get("decision", "UNKNOWN")
        cp_passed  = data.get("checkpoints_passed",  0)
        cp_total   = data.get("checkpoints_total",  11)
        cp_blocked = data.get("checkpoints_blocked",  0)
        receipt_id = data.get("receipt_id", "")
        explanation = (data.get("explanation") or "")[:500]

        icon    = "🔴" if decision == "BLOCKED" else "🟢"
        bar_ok  = "✅" * min(cp_passed,  11)
        bar_bad = "❌" * min(cp_blocked, 11)

        receipt_line = (
            f"\n📋 *Receipt ID:* `{receipt_id}`\n"
            f"🔗 Verifica en: omnixquantum.net"
            if receipt_id else ""
        )

        msg = (
            f"{icon} *OMNIX GOVERNANCE — {decision}*\n\n"
            f"📊 *Pipeline 11 Checkpoints:*\n"
            f"{bar_ok}{bar_bad}\n"
            f"✅ Pasados: {cp_passed} · ❌ Bloqueados: {cp_blocked} · Total: {cp_total}\n"
            f"{receipt_line}\n\n"
            f"📝 *Evaluación:*\n{explanation}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🧪 *Modo Demo — Análisis real, firma pendiente*\n"
            f"_Este análisis ha sido ejecutado por el pipeline real de OMNIX con sus 11 checkpoints activos — no es simulado ni ficticio. Sin embargo, al ser una demostración pública, el recibo no lleva firma criptográfica institucional ni tiene validez legal o contractual. Para evaluaciones con plena validez institucional, firma PQC y soporte regulatorio, contacta a OMNIX._\n\n"
            f"_OMNIX Decision Governance · Harold Nunes · Dubai 2026_"
        )

        await processing_msg.edit_text(msg, parse_mode="Markdown")

    except requests.Timeout:
        logger.warning("[EVALUAR] Timeout 60s")
        await processing_msg.edit_text(
            "⏱️ El evaluador tardó más de 60 segundos. "
            "Prueba con un escenario más breve o intenta de nuevo."
        )
    except Exception as exc:
        logger.error(f"[EVALUAR] Error: {exc}")
        await processing_msg.edit_text(
            "⚠️ Error en la red de gobernanza. Intenta de nuevo en unos instantes."
        )


# ── /gobernanza ───────────────────────────────────────────────────────────────

async def gobernanza_command(self, update, context):
    """
    /gobernanza — Estado del sistema de gobernanza OMNIX.
    Health ping al sandbox + resumen del Critical Override Layer (ADR-057).
    ADR-058.
    """
    from omnix_config import VERSION_BANNER

    health_ok = False
    try:
        r = requests.get(
            f"{_sandbox_url()}/api/public/sandbox/schema",
            timeout=5,
        )
        health_ok = r.status_code == 200
    except Exception:
        pass

    status_icon   = "🟢" if health_ok else "🟡"
    pipeline_text = "Operativo" if health_ok else "Sin conexión local (verificar OMNIX_WEB_URL)"

    msg = (
        f"🏛️ *OMNIX Decision Governance — Estado del Sistema*\n\n"
        f"{status_icon} *Pipeline 11-Checkpoint:* {pipeline_text}\n\n"
        f"🛡️ *Critical Override Layer (ADR-057) — 7 Grupos:*\n"
        f"✅ G1 — Lethal Decision Guard\n"
        f"✅ G2 — Signal Corruption / Governance Fraud\n"
        f"✅ G3 — Critical Violations (Islamic Finance · Export Control)\n"
        f"✅ G4 — Financial Crime Complex (AML · Sanctions · DeFi)\n"
        f"✅ G5 — No Human Oversight *(sin AML officer · automated approval)*\n"
        f"✅ G6 — Systemic Financial Risk (Flash Crash · Banco Central)\n"
        f"✅ G7 — PEP / Politically Exposed Persons\n\n"
        f"🌐 *Jurisdicciones activas:* 13\n"
        f"🤝 *Partner:* Velos — Naimat Khan · 10% mutual referral\n"
        f"🏆 *Posición:* Eureka GCC Dubai 2026 — Semifinalista\n"
        f"💰 *Pre-seed:* $500K @ $3M valuation\n\n"
        f"📌 *Versión:* {VERSION_BANNER}\n"
        f"🔗 omnixquantum.net\n\n"
        f"_Harold Nunes · OMNIX QUANTUM_"
    )

    await update.message.reply_text(msg, parse_mode="Markdown")


# ── /velos (admin-only) ───────────────────────────────────────────────────────

async def velos_command(self, update, context):
    """
    /velos — Últimos pushes al gateway Velos. Solo admin. ADR-052.
    Query directo a velos_push_log (acceso trusted desde el bot).
    """
    user = update.effective_user
    if not _is_admin(str(user.id)):
        await update.message.reply_text("🔒 Acceso restringido — solo administrador.")
        return

    try:
        conn, extras = _db_connect()
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        cur.execute(
            """
            SELECT receipt_id, client_id, decision, disposition,
                   http_status, latency_ms, pushed_at, skip_reason, error_message
            FROM   velos_push_log
            ORDER  BY pushed_at DESC
            LIMIT  5
            """
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            await update.message.reply_text(
                "📭 No hay eventos Velos registrados aún.\n"
                "_El gateway push se activa cuando VELOS_GATEWAY_TOKEN está configurado._",
                parse_mode="Markdown",
            )
            return

        lines = ["🔗 *VELOS GATEWAY — Últimos 5 eventos (ADR-052)*\n"]
        for r in rows:
            disp = r["disposition"]
            icon = "✅" if disp == "SENT" else ("⏭️" if disp == "SKIPPED" else "❌")
            ts   = (
                r["pushed_at"].strftime("%Y-%m-%d %H:%M UTC")
                if r["pushed_at"] else "N/A"
            )
            rid = (r["receipt_id"] or "")[:20]
            lines.append(
                f"{icon} `{rid}…`\n"
                f"   {r['decision']} · {disp} · "
                f"HTTP {r['http_status'] or '—'} · {r['latency_ms'] or '—'}ms\n"
                f"   {ts}"
            )
            if disp == "SKIPPED" and r.get("skip_reason"):
                lines.append(f"   ℹ️ {r['skip_reason'][:80]}")
            if disp == "ERROR" and r.get("error_message"):
                lines.append(f"   ⚠️ {r['error_message'][:80]}")

        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")

    except RuntimeError as exc:
        await update.message.reply_text(f"⚠️ {exc}")
    except Exception as exc:
        logger.error(f"[VELOS] Error: {exc}")
        await update.message.reply_text(
            "⚠️ Error consultando el log de Velos. Verifica DATABASE_URL."
        )


# ── /recibo (admin-only) ──────────────────────────────────────────────────────

async def recibo_command(self, update, context):
    """
    /recibo [n] — Últimos N recibos PQC de gobernanza. Solo admin. ADR-028.
    Query directo a decision_receipts.
    n = 1-10 (default 3).
    """
    user = update.effective_user
    if not _is_admin(str(user.id)):
        await update.message.reply_text("🔒 Acceso restringido — solo administrador.")
        return

    limit = 3
    if context.args:
        try:
            limit = max(1, min(int(context.args[0]), 10))
        except ValueError:
            pass

    try:
        conn, extras = _db_connect()
        cur = conn.cursor(cursor_factory=extras.RealDictCursor)
        cur.execute(
            """
            SELECT receipt_id, asset, decision, timestamp_utc, created_at
            FROM   decision_receipts
            ORDER  BY created_at DESC
            LIMIT  %s
            """,
            (limit,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            await update.message.reply_text(
                "📭 No hay recibos de gobernanza registrados aún.\n"
                "_Los recibos se generan después de cada evaluación via /api/governance/evaluate._",
                parse_mode="Markdown",
            )
            return

        lines = [f"📋 *GOVERNANCE RECEIPTS — Últimos {len(rows)} (ADR-028)*\n"]
        for r in rows:
            icon = "🟢" if r["decision"] == "APPROVED" else "🔴"
            ts   = (
                r["created_at"].strftime("%Y-%m-%d %H:%M UTC")
                if r["created_at"] else "N/A"
            )
            asset = (r["asset"] or "N/A")[:30]
            lines.append(
                f"{icon} `{r['receipt_id']}`\n"
                f"   {asset} · *{r['decision']}* · {ts}"
            )

        lines.append("\n🔗 Verifica en: omnixquantum.net")
        await update.message.reply_text("\n\n".join(lines), parse_mode="Markdown")

    except RuntimeError as exc:
        await update.message.reply_text(f"⚠️ {exc}")
    except Exception as exc:
        logger.error(f"[RECIBO] Error: {exc}")
        await update.message.reply_text(
            "⚠️ Error consultando recibos. Verifica DATABASE_URL."
        )
