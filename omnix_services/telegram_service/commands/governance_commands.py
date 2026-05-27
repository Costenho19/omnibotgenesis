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
    import psycopg
    from psycopg.rows import dict_row
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL no configurado")
    return psycopg.connect(db_url, row_factory=dict_row), None


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
            "_OMNIX Decision Governance — Harold Nunes · omnixquantum.net_",
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
            f"_OMNIX Decision Governance · Harold Nunes · omnixquantum.net_"
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
        conn, _ = _db_connect()
        cur = conn.cursor()
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
        conn, _ = _db_connect()
        cur = conn.cursor()
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


# ── /impact — Governance Impact Score ────────────────────────────────────────

_DOMAIN_LABELS = {
    "trading":            "Trading",
    "credit":             "Crédito",
    "insurance":          "Seguros",
    "robotics":           "Robótica",
    "medical_ai":         "Médico/AI",
    "energy_governance":  "Energía",
    "real_estate":        "Inmobiliario",
    "autonomous_agent":   "Agentes",
    "compliance":         "Compliance",
    "public_sandbox":     "Sandbox",
    "generic":            "Genérico",
}

_DOMAIN_ORDER = [
    "trading", "credit", "insurance", "robotics",
    "medical_ai", "energy_governance", "real_estate", "autonomous_agent",
    "compliance", "public_sandbox", "generic",
]


async def impact_command(self, update, context):
    """
    /impact — Governance Impact Score en tiempo real.
    Muestra decisiones por dominio (últimos 7 días), tasa de contención
    de riesgo y capital bajo gobernanza.
    ADR-083 Addendum — Governance Impact Reporting.
    """
    processing = await update.message.reply_text(
        "🔄 _Calculando Governance Impact Score..._",
        parse_mode="Markdown",
    )

    try:
        conn, _ = _db_connect()
        cur = conn.cursor()

        # ── 1. Decisiones por dominio (últimos 7 días) ──────────────────────
        cur.execute(
            """
            SELECT
                domain,
                UPPER(decision) AS decision,
                COUNT(*) AS cnt
            FROM   decision_receipts
            WHERE  created_at >= NOW() - INTERVAL '7 days'
            GROUP  BY domain, UPPER(decision)
            ORDER  BY domain, UPPER(decision)
            """
        )
        rows_7d = cur.fetchall()

        # ── 2. Totales históricos ───────────────────────────────────────────
        cur.execute(
            """
            SELECT
                COUNT(*)                                                                     AS total,
                COUNT(*) FILTER (WHERE UPPER(decision) IN ('BLOCKED','BLOCK','HOLD','REJECT')) AS blocked,
                COUNT(*) FILTER (WHERE UPPER(decision) IN ('APPROVED','APPROVE','PASS'))       AS approved,
                COUNT(DISTINCT domain)                                                       AS domains_active
            FROM decision_receipts
            """
        )
        totals = cur.fetchone()

        # ── 3. Capital bajo gobernanza (paper trading) ──────────────────────
        balance_usd = None
        try:
            cur.execute(
                "SELECT balance_usd FROM paper_trading_balances LIMIT 1"
            )
            bal_row = cur.fetchone()
            if bal_row:
                balance_usd = float(bal_row["balance_usd"])
        except Exception:
            pass

        # ── 4. Señales vetadas (shadow_trade_events) ────────────────────────
        vetoed_signals = 0
        try:
            cur.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM   shadow_trade_events
                WHERE  action = 'VETOED'
                   AND timestamp >= NOW() - INTERVAL '7 days'
                """
            )
            vr = cur.fetchone()
            if vr:
                vetoed_signals = int(vr["cnt"])
        except Exception:
            pass

        cur.close()
        conn.close()

        # ── 5. Armar estadísticas por dominio ───────────────────────────────
        stats: dict = {}
        for row in rows_7d:
            dom = row["domain"] or "generic"
            if dom not in stats:
                stats[dom] = {"APPROVED": 0, "BLOCKED": 0}
            dec = (row["decision"] or "").upper()
            if dec in ("APPROVED", "APPROVE", "PASS"):
                stats[dom]["APPROVED"] += int(row["cnt"])
            elif dec in ("BLOCKED", "BLOCK", "HOLD", "REJECT"):
                stats[dom]["BLOCKED"] += int(row["cnt"])

        total_7d   = sum(v["APPROVED"] + v["BLOCKED"] for v in stats.values())
        blocked_7d = sum(v["BLOCKED"] for v in stats.values())
        approved_7d = total_7d - blocked_7d

        # ── 6. Governance Impact Score (GIS 0-100) ──────────────────────────
        total_all    = int(totals["total"] or 0)
        blocked_all  = int(totals["blocked"] or 0)
        domains_ever = int(totals["domains_active"] or 0)

        containment_rate = (blocked_all / total_all * 100) if total_all > 0 else 0
        gis = min(100, int(
            70                                          # pipeline operativo
            + min(15, containment_rate * 0.15)          # +15 si contención = 100%
            + min(10, domains_ever * 1.25)              # +10 si 8 dominios activos
            + (5 if balance_usd and balance_usd > 900_000 else 0)  # +5 capital preservado
        ))

        # ── 7. Barra GIS visual ─────────────────────────────────────────────
        filled   = gis // 10
        empty    = 10 - filled
        gis_bar  = "█" * filled + "░" * empty

        # ── 8. Tabla de dominios ────────────────────────────────────────────
        domain_lines = []
        active_domains = 0
        for dom in _DOMAIN_ORDER:
            if dom not in stats:
                continue
            label    = _DOMAIN_LABELS.get(dom, dom)
            approved = stats[dom]["APPROVED"]
            blocked  = stats[dom]["BLOCKED"]
            total_d  = approved + blocked
            block_pct = int(blocked / total_d * 100) if total_d > 0 else 0
            active_domains += 1
            domain_lines.append(
                f"  • {label:<14} {total_d:>4} eval │ "
                f"🔴 {blocked} ({block_pct}%) │ 🟢 {approved}"
            )

        if not domain_lines:
            domain_lines = ["  _Sin datos en los últimos 7 días. Usa /evaluar para generar decisiones._"]

        domains_block = "\n".join(domain_lines)

        # ── 9. Balance line ─────────────────────────────────────────────────
        balance_line = (
            f"💼 *Capital bajo gobernanza:* ${balance_usd:,.2f} USD "
            f"({balance_usd / 1_000_000 * 100:.1f}% de $1M preservado)\n"
            if balance_usd else ""
        )

        # ── 10. Signals line ────────────────────────────────────────────────
        signals_line = (
            f"⛔ *Señales vetadas (7d):* {vetoed_signals:,}\n"
            if vetoed_signals > 0 else ""
        )

        # ── 11. Mensaje final ───────────────────────────────────────────────
        msg = (
            f"🏛️ *OMNIX — GOVERNANCE IMPACT SCORE*\n\n"
            f"┌─ GIS: *{gis}/100* ─────────────────┐\n"
            f"│ {gis_bar} │\n"
            f"└──────────────────────────────────────┘\n\n"
            f"📊 *DECISIONES — Últimos 7 días*\n"
            f"{domains_block}\n\n"
            f"📈 *RESUMEN GLOBAL (histórico)*\n"
            f"  Evaluaciones totales:    {total_all:>6,}\n"
            f"  🔴 BLOCKED:              {blocked_all:>6,} ({containment_rate:.1f}% contención)\n"
            f"  🟢 APPROVED:             {total_all - blocked_all:>6,}\n"
            f"  Dominios activos:        {domains_ever:>6}/8\n\n"
            f"{balance_line}"
            f"{signals_line}"
            f"\n🔗 omnixquantum.net · _OMNIX Decision Governance_"
        )

        await processing.edit_text(msg, parse_mode="Markdown")

    except RuntimeError as exc:
        logger.warning(f"[IMPACT] DB no disponible: {exc}")
        await processing.edit_text(
            "⚠️ Base de datos no disponible. Verifica DATABASE_URL."
        )
    except Exception as exc:
        logger.error(f"[IMPACT] Error inesperado: {exc}")
        await processing.edit_text(
            "⚠️ No se pudo calcular el Governance Impact Score. Intenta de nuevo."
        )


# ── /clientes — Lista de clientes B2B (solo admin) ───────────────────────────

async def clientes_command(self, update, context):
    """
    /clientes — Muestra todos los clientes B2B activos con su uso.
    Solo admin (Harold). Consulta PostgreSQL directamente.
    """
    user = update.effective_user
    if not _is_admin(str(user.id)):
        await update.message.reply_text("⛔ Solo el administrador puede ver los clientes.")
        return

    processing = await update.message.reply_text("⏳ Consultando clientes B2B...")

    try:
        conn, _ = _db_connect()
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        b.client_id,
                        b.name,
                        b.email,
                        b.role,
                        b.is_active,
                        b.created_at,
                        b.last_seen_at,
                        b.key_expires_at,
                        COUNT(d.id) AS total_evals,
                        COUNT(CASE WHEN d.created_at > NOW() - INTERVAL '24 hours' THEN 1 END) AS evals_24h,
                        COUNT(CASE WHEN d.created_at > NOW() - INTERVAL '30 days' THEN 1 END) AS evals_30d
                    FROM b2b_clients b
                    LEFT JOIN decision_receipts d ON d.client_id = b.client_id
                    GROUP BY b.client_id, b.name, b.email, b.role,
                             b.is_active, b.created_at, b.last_seen_at, b.key_expires_at
                    ORDER BY b.created_at DESC
                    LIMIT 20
                """)
                clients = cur.fetchall()
        conn.close()

        if not clients:
            await processing.edit_text(
                "📋 *CLIENTES B2B OMNIX*\n\n"
                "_No hay clientes registrados todavía._\n\n"
                "Usa `/nuevo_cliente` para añadir el primero.",
                parse_mode="Markdown"
            )
            return

        lines = []
        now_ts = datetime.now(timezone.utc)
        for c in clients:
            status = "🟢" if c["is_active"] else "🔴"
            role_icon = "👑" if c["role"] == "admin" else "🏢"
            last_seen = "nunca"
            if c["last_seen_at"]:
                delta = now_ts - c["last_seen_at"].replace(tzinfo=timezone.utc)
                h = int(delta.total_seconds() // 3600)
                last_seen = f"hace {h}h" if h < 48 else f"hace {delta.days}d"

            expiry = ""
            if c["key_expires_at"]:
                exp_delta = c["key_expires_at"].replace(tzinfo=timezone.utc) - now_ts
                days_left = exp_delta.days
                expiry = f" · ⏳{days_left}d" if days_left <= 14 else ""

            lines.append(
                f"{status} {role_icon} *{c['client_id']}*{expiry}\n"
                f"   {c['name']}"
                + (f" · {c['email']}" if c['email'] else "")
                + f"\n"
                f"   📊 {c['total_evals']:,} total · {c['evals_30d']:,}/30d · {c['evals_24h']:,}/24h\n"
                f"   👁️ {last_seen}"
            )

        msg = (
            f"📋 *CLIENTES B2B OMNIX* ({len(clients)} registrados)\n\n"
            + "\n\n".join(lines)
            + "\n\n_Usa `/nuevo_cliente` para añadir un cliente._"
        )
        await processing.edit_text(msg, parse_mode="Markdown")

    except RuntimeError as exc:
        logger.warning(f"[CLIENTES] DB no disponible: {exc}")
        await processing.edit_text("⚠️ Base de datos no disponible.")
    except Exception as exc:
        logger.error(f"[CLIENTES] Error: {exc}")
        await processing.edit_text("⚠️ Error al consultar clientes.")


# ── /nuevo_cliente — Provisionar cliente B2B (solo admin) ────────────────────

async def nuevo_cliente_command(self, update, context):
    """
    /nuevo_cliente id_cliente|Nombre Empresa|email@empresa.com
    Provisiona un nuevo cliente B2B y muestra la API key (solo una vez).
    Solo admin (Harold).
    Ejemplo: /nuevo_cliente quant-alpha|Quant Alpha Capital|cto@quantalpha.com
    """
    user = update.effective_user
    if not _is_admin(str(user.id)):
        await update.message.reply_text("⛔ Solo el administrador puede crear clientes.")
        return

    args_str = " ".join(context.args).strip() if context.args else ""

    if not args_str or "|" not in args_str:
        await update.message.reply_text(
            "🏢 *Crear nuevo cliente B2B*\n\n"
            "Formato:\n"
            "`/nuevo_cliente id-cliente|Nombre Empresa|email@empresa.com`\n\n"
            "Ejemplo:\n"
            "`/nuevo_cliente quant-alpha|Quant Alpha Capital|cto@quantalpha.com`\n\n"
            "ℹ️ El id-cliente debe ser único, solo minúsculas y guiones.\n"
            "La API key se mostrará UNA SOLA VEZ — cópiala inmediatamente.",
            parse_mode="Markdown"
        )
        return

    parts = [p.strip() for p in args_str.split("|")]
    client_id = parts[0].lower().replace(" ", "-") if len(parts) > 0 else ""
    name      = parts[1] if len(parts) > 1 else client_id
    email     = parts[2] if len(parts) > 2 else None

    if not client_id or len(client_id) < 3:
        await update.message.reply_text("⚠️ El id-cliente debe tener al menos 3 caracteres.")
        return

    processing = await update.message.reply_text(f"⏳ Creando cliente `{client_id}`...", parse_mode="Markdown")

    try:
        import secrets as _secrets
        import hashlib
        import psycopg

        raw_key = "OMNIX-" + _secrets.token_hex(24).upper()
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(days=90)

        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise RuntimeError("DATABASE_URL no configurado")

        conn = psycopg.connect(db_url)
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO b2b_clients (client_id, name, email, role, is_active, api_key_hash, key_expires_at)
                    VALUES (%s, %s, %s, 'standard', TRUE, %s, %s)
                    ON CONFLICT (client_id) DO NOTHING
                    RETURNING client_id
                """, (client_id, name, email, key_hash, expires_at))
                result = cur.fetchone()

        conn.close()

        if not result:
            await processing.edit_text(
                f"⚠️ El cliente `{client_id}` ya existe. Usa `--rotate` en el script de Railway para rotar la key.",
                parse_mode="Markdown"
            )
            return

        logger.info(f"[NUEVO_CLIENTE] Cliente creado: {client_id} ({name})")

        key_preview = raw_key[:10] + "..." + raw_key[-6:]

        public_msg = (
            f"✅ *Cliente B2B creado exitosamente*\n\n"
            f"🏢 *Empresa:* {name}\n"
            f"🔑 *Client ID:* `{client_id}`\n"
            + (f"📧 *Email:* {email}\n" if email else "")
            + f"📅 *Expira:* {expires_at.strftime('%d %b %Y')}\n"
            f"🔐 *API Key:* `{key_preview}`\n\n"
            f"📖 Endpoint: `https://omnixquantum.net/api/governance/evaluate`\n"
            f"Portal cliente: `https://omnixquantum.net/client`"
        )
        await processing.edit_text(public_msg, parse_mode="Markdown")

        secret_msg = await update.message.reply_text(
            f"🔐 *API KEY COMPLETA — COPIA Y BORRA ESTE MENSAJE INMEDIATAMENTE*\n\n"
            f"`{raw_key}`\n\n"
            f"⚠️ _Este mensaje se eliminará automáticamente en 60 segundos._",
            parse_mode="Markdown"
        )

        import asyncio as _asyncio
        async def _delete_key_msg():
            await _asyncio.sleep(60)
            try:
                await secret_msg.delete()
                logger.info(f"[NUEVO_CLIENTE] API key message auto-deleted for {client_id}")
            except Exception:
                pass
        _asyncio.create_task(_delete_key_msg())

    except RuntimeError as exc:
        logger.warning(f"[NUEVO_CLIENTE] DB no disponible: {exc}")
        await processing.edit_text("⚠️ Base de datos no disponible. Verifica DATABASE_URL.")
    except Exception as exc:
        logger.error(f"[NUEVO_CLIENTE] Error: {exc}")
        await processing.edit_text(f"⚠️ Error al crear el cliente: {type(exc).__name__}")
