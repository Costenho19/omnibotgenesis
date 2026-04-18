"""
OMNIX — Seed Script: Vertical Governance Tables
================================================
Popula medical_decisions, energy_decisions, property_decisions y agent_decisions
en la base de datos de Railway usando los motores de gobernanza reales de OMNIX.

Uso:
    python scripts/seed_vertical_tables.py

Requiere: OMNIX_DB_URL o DATABASE_URL en el entorno.
"""
import os
import sys
import random
import logging

logging.basicConfig(level=logging.INFO, format="%(name)s — %(message)s")
logger = logging.getLogger("OMNIX.Seed")

# ── Resolver URL de base de datos ──────────────────────────────────────────────
db_url = (
    os.environ.get("DATABASE_URL") or
    os.environ.get("OMNIX_DB_URL") or
    os.environ.get("POSTGRES_URL")
)
if not db_url:
    logger.error("No database URL. Configura DATABASE_URL u OMNIX_DB_URL.")
    sys.exit(1)

# Los simuladores leen DATABASE_URL directamente
os.environ["DATABASE_URL"] = db_url
logger.info("Conectando a Railway PostgreSQL...")

import psycopg2

CYCLES = 15          # ciclos por dominio
BATCH_MIN = 4        # mínimo decisiones por ciclo
BATCH_MAX = 7        # máximo decisiones por ciclo


def _run_domain(name: str, create_fn, generate_fn, evaluate_fn, persist_fn) -> int:
    """Ejecuta CYCLES ciclos de gobernanza y persiste los resultados."""
    logger.info("=" * 60)
    logger.info(f"DOMINIO: {name}")
    logger.info("=" * 60)
    conn = psycopg2.connect(db_url)
    try:
        create_fn(conn)
        total = 0
        for cycle in range(1, CYCLES + 1):
            batch_size = random.randint(BATCH_MIN, BATCH_MAX)
            decisions = [generate_fn() for _ in range(batch_size)]
            results   = [evaluate_fn(d) for d in decisions]
            saved = 0
            for r in results:
                try:
                    persist_fn(r, conn)
                    saved += 1
                    total += 1
                except Exception as e:
                    conn.rollback()
            approved = sum(1 for r in results if r.get("decision") == "APPROVED")
            blocked  = sum(1 for r in results if r.get("decision") == "BLOCKED")
            logger.info(
                f"  Ciclo {cycle:02d}: {saved}/{batch_size} guardados "
                f"— APPROVED={approved} BLOCKED={blocked}"
            )
        return total
    except Exception as e:
        logger.error(f"Error en {name}: {e}")
        return 0
    finally:
        conn.close()


# ── 1. Medical AI ──────────────────────────────────────────────────────────────
try:
    from omnix_core.medical.medical_simulator import (
        _create_medical_decisions_table,
        _generate_decision     as _med_gen,
        _evaluate_decision     as _med_eval,
        _persist_decision      as _med_persist,
    )
    total_med = _run_domain(
        "Medical AI Governance",
        _create_medical_decisions_table,
        _med_gen, _med_eval, _med_persist,
    )
    logger.info(f"✅ Medical AI: {total_med} decisiones insertadas")
except Exception as e:
    logger.error(f"❌ Medical AI import falló: {e}")

# ── 2. Energy Governance ───────────────────────────────────────────────────────
logger.info("=" * 60)
logger.info("DOMINIO: Energy Governance")
logger.info("=" * 60)
try:
    from omnix_core.energy.energy_simulator import (
        _create_energy_tables,
        _run_cycle as _energy_run_cycle,
    )
    conn = psycopg2.connect(db_url)
    _create_energy_tables(conn)
    for cycle in range(1, CYCLES + 1):
        try:
            _energy_run_cycle(conn, cycle)
            logger.info(f"  Ciclo {cycle:02d}: OK")
        except Exception as e:
            logger.warning(f"  Ciclo {cycle:02d} error: {e}")
            conn.rollback()
    conn.close()
    conn2 = psycopg2.connect(db_url)
    cur = conn2.cursor()
    cur.execute("SELECT COUNT(*) FROM energy_decisions")
    total_egy = cur.fetchone()[0]
    conn2.close()
    logger.info(f"✅ Energy Governance: {total_egy} decisiones en tabla")
except Exception as e:
    logger.error(f"❌ Energy Governance falló: {e}")

# ── 3. Real Estate ─────────────────────────────────────────────────────────────
try:
    from omnix_core.real_estate.real_estate_simulator import (
        _create_property_decisions_table,
        _generate_decision   as _res_gen,
        _evaluate_decision   as _res_eval,
        _persist_decision    as _res_persist,
    )
    total_res = _run_domain(
        "Real Estate Governance",
        _create_property_decisions_table,
        _res_gen, _res_eval, _res_persist,
    )
    logger.info(f"✅ Real Estate: {total_res} decisiones insertadas")
except Exception as e:
    logger.error(f"❌ Real Estate import falló: {e}")

# ── 4. Autonomous Agents ───────────────────────────────────────────────────────
try:
    from omnix_core.agents.agents_simulator import (
        _create_agent_decisions_table,
        _generate_decision   as _agt_gen,
        _evaluate_decision   as _agt_eval,
        _persist_decision    as _agt_persist,
    )
    total_agt = _run_domain(
        "Autonomous Agents Governance",
        _create_agent_decisions_table,
        _agt_gen, _agt_eval, _agt_persist,
    )
    logger.info(f"✅ Autonomous Agents: {total_agt} decisiones insertadas")
except Exception as e:
    logger.error(f"❌ Autonomous Agents import falló: {e}")

# ── Verificación final ─────────────────────────────────────────────────────────
logger.info("=" * 60)
logger.info("VERIFICACIÓN FINAL — Todas las tablas verticales")
logger.info("=" * 60)
try:
    conn = psycopg2.connect(db_url)
    cur  = conn.cursor()
    tables = [
        ("decision_receipts",  "trading"),
        ("credit_applications", "islamic_credit"),
        ("insurance_claims",   "insurance"),
        ("robot_actions",      "robotics"),
        ("medical_decisions",  "medical_ai"),
        ("energy_decisions",   "energy_governance"),
        ("property_decisions", "real_estate"),
        ("agent_decisions",    "autonomous_agents"),
    ]
    for table, domain in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count  = cur.fetchone()[0]
            status = "✅" if count > 0 else "⚠️  VACÍA"
            logger.info(f"  {status}  {domain:25s} → {table}: {count} registros")
        except Exception as e:
            logger.warning(f"  ❌  {domain:25s} → {table}: error — {e}")
            conn.rollback()
    conn.close()
except Exception as e:
    logger.error(f"Error en verificación: {e}")

logger.info("=" * 60)
logger.info("Seed completado.")
