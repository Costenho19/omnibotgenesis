"""
OMNIX — Operational Health Check Engine  (ADR-150)

Performs deep health probes of every critical subsystem and returns
a structured HealthReport consumable by the /api/health endpoint,
monitoring dashboards, and automated alerting.

Subsystems checked:
  DB          — PostgreSQL connectivity + decision_receipts table access
  Redis       — ping + SET/GET round-trip
  PQC         — Dilithium-3 key availability
  WAL         — pending entries count
  AVM         — assumption validity monitor reachable
  Governance  — external evaluator importable
  API         — always-UP from server perspective

ADR-150: Every subsystem has a status (UP / DEGRADED / DOWN) and a
latency_ms. The overall status is the worst-case of all subsystems.
Callers must not interpret partial degradation as a total outage.
"""

import hashlib
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

OMNIX_VERSION = "6.6.0"
GOVERNANCE_BASELINE = "OMNIX-BASELINE-2026-Q2-001"

STATUS_UP       = "UP"
STATUS_DEGRADED = "DEGRADED"
STATUS_DOWN     = "DOWN"

_STATUS_RANK = {STATUS_UP: 0, STATUS_DEGRADED: 1, STATUS_DOWN: 2}


@dataclass
class SubsystemHealth:
    name: str
    status: str                    # UP | DEGRADED | DOWN
    latency_ms: Optional[float]
    detail: str = ""
    critical: bool = True          # critical=True means DOWN → overall DOWN

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name":       self.name,
            "status":     self.status,
            "latency_ms": round(self.latency_ms, 2) if self.latency_ms is not None else None,
            "detail":     self.detail,
            "critical":   self.critical,
        }


@dataclass
class HealthReport:
    status: str                          # overall worst-case
    timestamp_utc: str
    version: str
    governance_baseline: str
    uptime_seconds: Optional[float]
    subsystems: List[SubsystemHealth] = field(default_factory=list)
    wal_pending: int = 0
    adr_count: int = 149
    pqc_mode: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status":               self.status,
            "timestamp_utc":        self.timestamp_utc,
            "version":              self.version,
            "governance_baseline":  self.governance_baseline,
            "uptime_seconds":       round(self.uptime_seconds, 1) if self.uptime_seconds else None,
            "wal_pending":          self.wal_pending,
            "adr_count":            self.adr_count,
            "pqc_mode":             self.pqc_mode,
            "subsystems":           [s.to_dict() for s in self.subsystems],
        }


# ── Module-level start time for uptime tracking ───────────────────────────────
_START_TIME = time.monotonic()


def _probe_database(db_url: Optional[str]) -> SubsystemHealth:
    if not db_url:
        return SubsystemHealth("database", STATUS_DOWN, None,
                               "DATABASE_URL not configured", critical=True)
    t0 = time.monotonic()
    try:
        import psycopg
        conn = psycopg.connect(db_url, connect_timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM decision_receipts LIMIT 1")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        latency = (time.monotonic() - t0) * 1000
        return SubsystemHealth(
            "database", STATUS_UP, latency,
            f"decision_receipts accessible — {count:,} rows", critical=True
        )
    except ImportError:
        return SubsystemHealth("database", STATUS_DOWN, None,
                               "psycopg2 not installed", critical=True)
    except Exception as e:
        latency = (time.monotonic() - t0) * 1000
        return SubsystemHealth("database", STATUS_DOWN, latency,
                               f"connection failed: {str(e)[:120]}", critical=True)


def _probe_redis(redis_url: Optional[str]) -> SubsystemHealth:
    if not redis_url:
        return SubsystemHealth("redis", STATUS_DEGRADED, None,
                               "REDIS_URL not configured — anti-replay degraded", critical=False)
    t0 = time.monotonic()
    try:
        import redis
        r = redis.from_url(redis_url, socket_connect_timeout=3, socket_timeout=3)
        probe_key = "omnix:health:probe"
        probe_val = hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
        r.set(probe_key, probe_val, ex=10)
        returned = r.get(probe_key)
        latency = (time.monotonic() - t0) * 1000
        if returned and returned.decode() == probe_val:
            return SubsystemHealth("redis", STATUS_UP, latency,
                                   "SET/GET round-trip verified", critical=False)
        return SubsystemHealth("redis", STATUS_DEGRADED, latency,
                               "SET/GET round-trip mismatch", critical=False)
    except ImportError:
        return SubsystemHealth("redis", STATUS_DEGRADED, None,
                               "redis-py not installed", critical=False)
    except Exception as e:
        latency = (time.monotonic() - t0) * 1000
        return SubsystemHealth("redis", STATUS_DEGRADED, latency,
                               f"unreachable: {str(e)[:120]}", critical=False)


def _probe_pqc() -> SubsystemHealth:
    t0 = time.monotonic()
    try:
        from omnix_core.security.pqc_security import PostQuantumSecurity
        pqc = PostQuantumSecurity()
        keypair = pqc.generate_keypair_signature()
        if not keypair:
            raise RuntimeError("generate_keypair_signature returned None")
        pk, sk = keypair
        test_msg = b"omnix-health-probe"
        sig = pqc.sign_message(test_msg, sk)
        if not sig:
            raise RuntimeError("sign_message returned None")
        ok = pqc.verify_signature(sig, test_msg, pk)
        latency = (time.monotonic() - t0) * 1000
        if ok:
            return SubsystemHealth("pqc_dilithium3", STATUS_UP, latency,
                                   "Dilithium-3 sign/verify cycle passed", critical=False)
        return SubsystemHealth("pqc_dilithium3", STATUS_DEGRADED, latency,
                               "sign/verify returned False", critical=False)
    except Exception as e:
        latency = (time.monotonic() - t0) * 1000
        mode = os.getenv("OMNIX_KEY_MODE", "not_set")
        return SubsystemHealth(
            "pqc_dilithium3", STATUS_DEGRADED, latency,
            f"PQC unavailable — receipts SHA-256 only. mode={mode} err={str(e)[:80]}",
            critical=False
        )


def _probe_wal() -> SubsystemHealth:
    t0 = time.monotonic()
    try:
        from omnix_core.evidence.receipt_wal import get_receipt_wal
        wal = get_receipt_wal()
        pending = wal.wal_size()
        latency = (time.monotonic() - t0) * 1000
        if pending == 0:
            return SubsystemHealth("receipt_wal", STATUS_UP, latency,
                                   "WAL empty — all receipts committed to DB", critical=False)
        elif pending < 10:
            return SubsystemHealth("receipt_wal", STATUS_DEGRADED, latency,
                                   f"WAL has {pending} pending entries — DB write lagging",
                                   critical=False)
        else:
            return SubsystemHealth("receipt_wal", STATUS_DOWN, latency,
                                   f"WAL has {pending} pending entries — DB likely down",
                                   critical=False)
    except Exception as e:
        latency = (time.monotonic() - t0) * 1000
        return SubsystemHealth("receipt_wal", STATUS_DEGRADED, latency,
                               f"WAL probe failed: {str(e)[:80]}", critical=False)


def _probe_avm() -> SubsystemHealth:
    t0 = time.monotonic()
    try:
        from omnix_core.governance.assumption_validity_monitor import get_avm_instance
        avm = get_avm_instance("health-probe")
        assert callable(getattr(avm, "evaluate", None)), "evaluate() not found on AVM"
        latency = (time.monotonic() - t0) * 1000
        return SubsystemHealth("avm", STATUS_UP, latency,
                               "Assumption Validity Monitor operational", critical=False)
    except Exception as e:
        latency = (time.monotonic() - t0) * 1000
        return SubsystemHealth("avm", STATUS_DEGRADED, latency,
                               f"AVM probe failed: {str(e)[:80]}", critical=False)


def _probe_governance_engine() -> SubsystemHealth:
    t0 = time.monotonic()
    try:
        from omnix_core.governance.external_evaluator import GovernanceEvaluationEngine  # noqa: F401
        from omnix_core.evidence.decision_receipt import DecisionReceiptEngine  # noqa: F401
        latency = (time.monotonic() - t0) * 1000
        return SubsystemHealth("governance_engine", STATUS_UP, latency,
                               "11-checkpoint pipeline importable", critical=True)
    except Exception as e:
        latency = (time.monotonic() - t0) * 1000
        return SubsystemHealth("governance_engine", STATUS_DOWN, latency,
                               f"governance engine import failed: {str(e)[:80]}", critical=True)


def _pqc_mode_label() -> str:
    try:
        key_b64 = os.getenv("OMNIX_SIGNING_SECRET_KEY_B64", "")
        if key_b64:
            return "dilithium3-persistent"
        return "sha256-only"
    except Exception:
        return "unknown"


def _adr_count() -> int:
    try:
        import re
        adr_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "docs", "adr"
        )
        nums = [
            int(re.search(r"ADR-(\d+)", f).group(1))
            for f in os.listdir(adr_dir)
            if re.search(r"ADR-(\d+)", f)
        ]
        return max(nums) if nums else 149
    except Exception:
        return 149


def run_health_check(
    db_url: Optional[str] = None,
    redis_url: Optional[str] = None,
) -> HealthReport:
    """
    Run all health probes and return a HealthReport.

    Args:
        db_url:    PostgreSQL connection string (defaults to DATABASE_URL env var)
        redis_url: Redis connection string (defaults to REDIS_URL env var)

    Returns:
        HealthReport with overall status and per-subsystem details.
    """
    db_url    = db_url    or os.getenv("DATABASE_URL")
    redis_url = redis_url or os.getenv("REDIS_URL")

    probes = [
        _probe_database(db_url),
        _probe_redis(redis_url),
        _probe_pqc(),
        _probe_wal(),
        _probe_avm(),
        _probe_governance_engine(),
    ]

    # Overall status — worst-case of critical subsystems
    worst = STATUS_UP
    for p in probes:
        rank_candidate = _STATUS_RANK.get(p.status, 0)
        rank_current   = _STATUS_RANK.get(worst, 0)
        if p.critical and rank_candidate > rank_current:
            worst = p.status

    wal_pending = 0
    for p in probes:
        if p.name == "receipt_wal" and p.detail:
            try:
                import re
                m = re.search(r"(\d+) pending", p.detail)
                if m:
                    wal_pending = int(m.group(1))
            except Exception:
                pass

    return HealthReport(
        status=worst,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        version=OMNIX_VERSION,
        governance_baseline=GOVERNANCE_BASELINE,
        uptime_seconds=time.monotonic() - _START_TIME,
        subsystems=probes,
        wal_pending=wal_pending,
        adr_count=_adr_count(),
        pqc_mode=_pqc_mode_label(),
    )
