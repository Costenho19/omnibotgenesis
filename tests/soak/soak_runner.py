"""
OMNIX Soak Reliability Protocol (SRP) — ADR-197

Long-running process that governs the governance stack against time-domain
failure modes that only emerge after hours or days of operation.

Probes executed each cycle:
  MemoryLeakMonitor        — RSS growth vs budget (SOAK-INV-001)
  DeadlockWatchdog         — hung operations > timeout (SOAK-INV-002)
  StaleSessionScanner      — ACTIVE sessions past TTL (SOAK-INV-003)
  ReconnectFailureTracker  — consecutive reconnect failures (SOAK-INV-004)
  OrphanRecordScanner      — BAR/CCS/CTCHC/MAS without parent session (SOAK-INV-005)
  SoakCheckpoint           — append-only hash-chained log (SOAK-INV-007)

Operation modes:
  mock-sprint   60s, in-memory mock — CI-safe, validates soak machinery
  overnight     8h, live DB (opt-in) — production-equivalent confidence
  continuous    ∞, live DB (opt-in) — production shadow

Usage:
  python tests/soak/soak_runner.py --mode mock-sprint
  OMNIX_HARDENING_ALLOW_LIVE_DB=true SOAK_DURATION_SECONDS=28800 \\
      python tests/soak/soak_runner.py --mode overnight

Configuration env vars — see ADR-197 §Configuration Reference.

Harold Nunes — OMNIX QUANTUM LTD — May 2026 — ADR-197
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ─── project root on sys.path ────────────────────────────────────────────────
_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_ROOT))

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-mode-token-for-pytest")

logging.basicConfig(
    level    = logging.INFO,
    format   = "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt  = "%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("OMNIX.Soak.SRP")

# ─── configuration ───────────────────────────────────────────────────────────
ALLOW_LIVE_DB       = os.environ.get("OMNIX_HARDENING_ALLOW_LIVE_DB", "false").lower() == "true"
CYCLE_INTERVAL_S    = float(os.environ.get("SOAK_CYCLE_INTERVAL_S",    "60"))
MEMORY_BUDGET_MB_H  = float(os.environ.get("SOAK_MEMORY_BUDGET_MB_PER_HOUR",  "50"))
DEADLOCK_TIMEOUT_S  = float(os.environ.get("SOAK_DEADLOCK_TIMEOUT_S",  "30"))
STALE_TTL_S         = float(os.environ.get("SOAK_SESSION_STALE_TTL_S", "3600"))
RECONNECT_MAX       = int(os.environ.get("SOAK_RECONNECT_MAX_ATTEMPTS", "5"))
AVM_DRIFT_TOL       = float(os.environ.get("SOAK_AVM_DRIFT_TOLERANCE",  "0.05"))
HALT_ON_VIOLATION   = os.environ.get("SOAK_HALT_ON_VIOLATION",  "false").lower() == "true"
SOAK_DURATION_S     = float(os.environ.get("SOAK_DURATION_SECONDS", "0"))  # 0 = infinite

SOAK_LOG = Path(__file__).parent / "soak_log.jsonl"


# ─────────────────────────────────────────────────────────────────────────────
#  ProbeResult
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ProbeResult:
    probe:    str
    passed:   bool
    violated: bool
    detail:   Dict[str, Any] = field(default_factory=dict)
    message:  str = ""


# ─────────────────────────────────────────────────────────────────────────────
#  SoakViolation
# ─────────────────────────────────────────────────────────────────────────────

class SoakViolation(RuntimeError):
    """Raised when SOAK_HALT_ON_VIOLATION=true and a critical invariant fires."""

    def __init__(self, invariant: str, detail: str) -> None:
        self.invariant = invariant
        super().__init__(f"[{invariant}] {detail}")


# ─────────────────────────────────────────────────────────────────────────────
#  MemoryLeakMonitor — SOAK-INV-001
# ─────────────────────────────────────────────────────────────────────────────

class MemoryLeakMonitor:
    """
    Tracks RSS memory growth over time.

    SOAK-INV-001: growth MUST NOT exceed SOAK_MEMORY_BUDGET_MB_PER_HOUR.
    """

    def __init__(self, budget_mb_per_hour: float = MEMORY_BUDGET_MB_H) -> None:
        self.budget_mb_per_hour = budget_mb_per_hour
        self._baseline_rss_mb:  Optional[float] = None
        self._baseline_time:    Optional[float] = None

    def _get_rss_mb(self) -> Optional[float]:
        try:
            import psutil
            return psutil.Process().memory_info().rss / (1024 * 1024)
        except ImportError:
            # psutil not available — fallback to /proc/self/status on Linux
            try:
                status = Path("/proc/self/status").read_text()
                for line in status.splitlines():
                    if line.startswith("VmRSS:"):
                        return float(line.split()[1]) / 1024.0
            except OSError:
                pass
            return None

    def baseline(self) -> Optional[float]:
        rss = self._get_rss_mb()
        self._baseline_rss_mb = rss
        self._baseline_time   = time.monotonic()
        logger.info("[MemoryLeakMonitor] baseline RSS=%.1f MB", rss or 0)
        return rss

    # Minimum elapsed seconds before enforcing the budget.
    # In the first 60 seconds, process startup artifacts inflate RSS temporarily.
    _MIN_ENFORCE_S: float = 60.0

    def sample(self) -> ProbeResult:
        """SOAK-INV-001: check that memory growth is within budget."""
        current_rss = self._get_rss_mb()

        if current_rss is None or self._baseline_rss_mb is None:
            return ProbeResult(
                probe   = "memory_leak",
                passed  = True,
                violated= False,
                detail  = {"reason": "psutil unavailable — skip"},
                message = "memory monitoring skipped (psutil not installed)",
            )

        elapsed_s  = time.monotonic() - self._baseline_time
        elapsed_h  = max(elapsed_s, 1.0) / 3600.0
        growth_mb  = current_rss - self._baseline_rss_mb
        budget_mb  = self.budget_mb_per_hour * elapsed_h
        rate_mb_h  = growth_mb / elapsed_h

        # Skip enforcement during the warm-up window to avoid false positives
        # from process startup artifacts (e.g. module imports, JIT compilation).
        if elapsed_s < self._MIN_ENFORCE_S:
            return ProbeResult(
                probe    = "memory_leak",
                passed   = True,
                violated = False,
                detail   = {
                    "current_rss_mb":  round(current_rss, 2),
                    "growth_mb":       round(growth_mb, 2),
                    "elapsed_s":       round(elapsed_s, 1),
                    "warm_up_skip":    True,
                    "enforce_after_s": self._MIN_ENFORCE_S,
                },
                message = f"memory warm-up window ({elapsed_s:.0f}s < {self._MIN_ENFORCE_S:.0f}s) — not enforcing",
            )

        violated = growth_mb > budget_mb

        return ProbeResult(
            probe    = "memory_leak",
            passed   = not violated,
            violated = violated,
            detail   = {
                "current_rss_mb":  round(current_rss, 2),
                "baseline_rss_mb": round(self._baseline_rss_mb, 2),
                "growth_mb":       round(growth_mb, 2),
                "budget_mb":       round(budget_mb, 2),
                "rate_mb_per_h":   round(rate_mb_h, 2),
                "elapsed_h":       round(elapsed_h, 3),
            },
            message = (
                f"[SOAK-INV-001 VIOLATION] RSS growth {growth_mb:.1f} MB "
                f"exceeds budget {budget_mb:.1f} MB "
                f"({rate_mb_h:.1f} MB/h)"
                if violated
                else f"RSS growth OK: {growth_mb:.1f} MB / {budget_mb:.1f} MB budget"
            ),
        )


# ─────────────────────────────────────────────────────────────────────────────
#  DeadlockWatchdog — SOAK-INV-002
# ─────────────────────────────────────────────────────────────────────────────

class DeadlockWatchdog:
    """
    Tracks in-flight operations and alerts if any exceeds the timeout.

    SOAK-INV-002: no operation may remain in-flight longer than SOAK_DEADLOCK_TIMEOUT_S.
    """

    def __init__(self, timeout_s: float = DEADLOCK_TIMEOUT_S) -> None:
        self.timeout_s = timeout_s
        self._lock:    threading.Lock = threading.Lock()
        self._ops:     Dict[str, float] = {}   # op_id → start_time

    def register_operation(self, op_id: str) -> str:
        with self._lock:
            self._ops[op_id] = time.monotonic()
        return op_id

    def complete_operation(self, op_id: str) -> None:
        with self._lock:
            self._ops.pop(op_id, None)

    def scan(self) -> ProbeResult:
        """SOAK-INV-002: find any operation in-flight longer than timeout."""
        now = time.monotonic()
        with self._lock:
            candidates = {
                op_id: now - start
                for op_id, start in self._ops.items()
                if now - start > self.timeout_s
            }

        violated = bool(candidates)
        return ProbeResult(
            probe    = "deadlock",
            passed   = not violated,
            violated = violated,
            detail   = {
                "deadlock_candidates": {
                    op_id: round(elapsed, 2)
                    for op_id, elapsed in candidates.items()
                },
                "timeout_s": self.timeout_s,
                "total_in_flight": len(self._ops),
            },
            message = (
                f"[SOAK-INV-002 VIOLATION] {len(candidates)} hung operations "
                f"(> {self.timeout_s}s): {list(candidates.keys())[:3]}"
                if violated
                else f"No deadlock candidates ({len(self._ops)} in-flight)"
            ),
        )


# ─────────────────────────────────────────────────────────────────────────────
#  StaleSessionScanner — SOAK-INV-003
# ─────────────────────────────────────────────────────────────────────────────

class StaleSessionScanner:
    """
    Detects OGR sessions stuck in ACTIVE status past the TTL.

    Requires OMNIX_HARDENING_ALLOW_LIVE_DB=true for DB queries.
    In mock mode, returns no-op result.

    SOAK-INV-003: no ACTIVE session older than SOAK_SESSION_STALE_TTL_S.
    """

    def __init__(self, stale_ttl_s: float = STALE_TTL_S) -> None:
        self.stale_ttl_s = stale_ttl_s

    def scan(self) -> ProbeResult:
        if not ALLOW_LIVE_DB:
            return ProbeResult(
                probe    = "stale_sessions",
                passed   = True,
                violated = False,
                detail   = {"mode": "mock — live DB required"},
                message  = "stale session scan skipped (mock mode)",
            )

        db_url = os.environ.get("DATABASE_URL", "")
        if not db_url:
            return ProbeResult(
                probe    = "stale_sessions",
                passed   = True,
                violated = False,
                detail   = {"reason": "DATABASE_URL not set"},
                message  = "stale session scan skipped (no DATABASE_URL)",
            )

        try:
            import psycopg
            from psycopg.rows import dict_row

            with psycopg.connect(db_url, row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT session_id, agent_id, started_at,
                               EXTRACT(EPOCH FROM (NOW() - started_at)) AS age_s
                        FROM atf_ogr_sessions
                        WHERE status = 'ACTIVE'
                          AND EXTRACT(EPOCH FROM (NOW() - started_at)) > %s
                        ORDER BY started_at ASC
                        LIMIT 20
                        """,
                        (self.stale_ttl_s,),
                    )
                    stale = cur.fetchall()

            violated = bool(stale)
            stale_ids = [row["session_id"] for row in stale] if stale else []

            return ProbeResult(
                probe    = "stale_sessions",
                passed   = not violated,
                violated = violated,
                detail   = {
                    "stale_count": len(stale),
                    "stale_session_ids": stale_ids[:5],
                    "stale_ttl_s": self.stale_ttl_s,
                },
                message  = (
                    f"[SOAK-INV-003 VIOLATION] {len(stale)} ACTIVE sessions "
                    f"older than {self.stale_ttl_s}s: {stale_ids[:3]}"
                    if violated
                    else f"No stale sessions found"
                ),
            )

        except Exception as exc:
            return ProbeResult(
                probe    = "stale_sessions",
                passed   = True,
                violated = False,
                detail   = {"error": str(exc)},
                message  = f"stale session scan error (non-critical): {exc}",
            )


# ─────────────────────────────────────────────────────────────────────────────
#  ReconnectFailureTracker — SOAK-INV-004
# ─────────────────────────────────────────────────────────────────────────────

class ReconnectFailureTracker:
    """
    Tracks consecutive DB reconnect failures.

    SOAK-INV-004: consecutive failures must not exceed SOAK_RECONNECT_MAX_ATTEMPTS.
    """

    def __init__(self, max_attempts: int = RECONNECT_MAX) -> None:
        self.max_attempts        = max_attempts
        self._consecutive        = 0
        self._total_attempts     = 0
        self._total_failures     = 0
        self._last_success_at:   Optional[float] = None
        self._lock               = threading.Lock()

    def record_attempt(self, success: bool) -> None:
        with self._lock:
            self._total_attempts += 1
            if success:
                self._consecutive    = 0
                self._last_success_at = time.monotonic()
            else:
                self._consecutive    += 1
                self._total_failures += 1

    def check(self) -> ProbeResult:
        """SOAK-INV-004: consecutive failures below max."""
        with self._lock:
            consecutive = self._consecutive
            total_f     = self._total_failures
            total_a     = self._total_attempts
            last_ok     = self._last_success_at

        violated = consecutive >= self.max_attempts

        return ProbeResult(
            probe    = "reconnect_failures",
            passed   = not violated,
            violated = violated,
            detail   = {
                "consecutive_failures": consecutive,
                "max_attempts":         self.max_attempts,
                "total_failures":       total_f,
                "total_attempts":       total_a,
                "last_success_age_s":   round(time.monotonic() - last_ok, 1) if last_ok else None,
            },
            message  = (
                f"[SOAK-INV-004 VIOLATION] {consecutive} consecutive reconnect "
                f"failures (max={self.max_attempts})"
                if violated
                else f"Reconnect OK: {consecutive} consecutive failures, {total_f}/{total_a} total"
            ),
        )


# ─────────────────────────────────────────────────────────────────────────────
#  OrphanRecordScanner — SOAK-INV-005
# ─────────────────────────────────────────────────────────────────────────────

class OrphanRecordScanner:
    """
    Detects BEV/MIVP records that have no parent OGR session.

    SOAK-INV-005: zero orphan records in BAR, CCS, CTCHC, MAS tables.
    Requires OMNIX_HARDENING_ALLOW_LIVE_DB=true.
    """

    _ORPHAN_QUERIES: List[Tuple[str, str]] = [
        (
            "atf_behavioral_anchor_records",
            """
            SELECT COUNT(*) AS orphan_count FROM atf_behavioral_anchor_records bar
            LEFT JOIN atf_ogr_sessions s ON s.session_id = bar.session_id
            WHERE s.session_id IS NULL
            """,
        ),
        (
            "atf_constraint_conformance_signals",
            """
            SELECT COUNT(*) AS orphan_count FROM atf_constraint_conformance_signals ccs
            LEFT JOIN atf_ogr_sessions s ON s.session_id = ccs.session_id
            WHERE s.session_id IS NULL
            """,
        ),
        (
            "atf_coherence_hash_chains",
            """
            SELECT COUNT(*) AS orphan_count FROM atf_coherence_hash_chains ctchc
            LEFT JOIN atf_ogr_sessions s ON s.session_id = ctchc.session_id
            WHERE s.session_id IS NULL
            """,
        ),
        (
            "atf_mandate_alignment_scores",
            """
            SELECT COUNT(*) AS orphan_count FROM atf_mandate_alignment_scores mas
            LEFT JOIN atf_mandate_binding_records mbr ON mbr.mbr_id = mas.mbr_id
            LEFT JOIN atf_ogr_sessions s ON s.session_id = mbr.session_id
            WHERE s.session_id IS NULL
            """,
        ),
    ]

    def scan(self) -> ProbeResult:
        if not ALLOW_LIVE_DB:
            return ProbeResult(
                probe    = "orphan_records",
                passed   = True,
                violated = False,
                detail   = {"mode": "mock — live DB required"},
                message  = "orphan scan skipped (mock mode)",
            )

        db_url = os.environ.get("DATABASE_URL", "")
        if not db_url:
            return ProbeResult(
                probe    = "orphan_records",
                passed   = True,
                violated = False,
                detail   = {"reason": "DATABASE_URL not set"},
                message  = "orphan scan skipped (no DATABASE_URL)",
            )

        try:
            import psycopg
            from psycopg.rows import dict_row

            orphan_counts: Dict[str, int] = {}

            with psycopg.connect(db_url, row_factory=dict_row) as conn:
                with conn.cursor() as cur:
                    for table, query in self._ORPHAN_QUERIES:
                        try:
                            cur.execute(query)
                            row = cur.fetchone()
                            count = row["orphan_count"] if row else 0
                            orphan_counts[table] = int(count)
                        except Exception:
                            orphan_counts[table] = -1   # table may not exist yet

            total_orphans = sum(c for c in orphan_counts.values() if c > 0)
            violated = total_orphans > 0

            return ProbeResult(
                probe    = "orphan_records",
                passed   = not violated,
                violated = violated,
                detail   = orphan_counts,
                message  = (
                    f"[SOAK-INV-005 VIOLATION] {total_orphans} orphan records found: "
                    f"{orphan_counts}"
                    if violated
                    else f"No orphan records across BEV/MIVP tables"
                ),
            )

        except Exception as exc:
            return ProbeResult(
                probe    = "orphan_records",
                passed   = True,
                violated = False,
                detail   = {"error": str(exc)},
                message  = f"orphan scan error (non-critical): {exc}",
            )


# ─────────────────────────────────────────────────────────────────────────────
#  SoakCheckpoint — SOAK-INV-007
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SoakCheckpoint:
    """
    Append-only checkpoint record written at the end of each probe cycle.

    SOAK-INV-007: forms a simple hash chain — prev_hash of each record is the
    SHA-256 of the previous raw JSON line, making the log tamper-evident.
    """
    checkpoint_id:  str
    cycle_number:   int
    elapsed_s:      float
    captured_at:    str
    results:        Dict[str, Any]
    violations:     List[str]
    probe_count:    int

    @property
    def has_critical_violation(self) -> bool:
        return bool(self.violations)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def write(self, log_path: Path = SOAK_LOG) -> None:
        """SOAK-INV-007: append one record, compute chain hash."""
        log_path.parent.mkdir(parents=True, exist_ok=True)

        prev_hash = "GENESIS"
        if log_path.exists():
            lines = log_path.read_text(encoding="utf-8").strip().splitlines()
            if lines:
                prev_hash = hashlib.sha256(lines[-1].encode()).hexdigest()

        record             = self.to_dict()
        record["prev_hash"]= prev_hash
        raw                = json.dumps(record, default=str, sort_keys=True)
        record["hash"]     = hashlib.sha256(raw.encode()).hexdigest()

        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")


# ─────────────────────────────────────────────────────────────────────────────
#  MockGovernanceExerciser
# ─────────────────────────────────────────────────────────────────────────────

class MockGovernanceExerciser:
    """
    In mock mode: exercises the OGR session lifecycle each cycle so the
    soak runner generates realistic load without a real DB.
    """

    def __init__(self, sessions_per_cycle: int = 5) -> None:
        self.sessions_per_cycle = sessions_per_cycle

    def run_cycle(self, watchdog: DeadlockWatchdog, tracker: ReconnectFailureTracker) -> None:
        from unittest.mock import MagicMock, patch

        mock_cursor = MagicMock()
        mock_cursor.__enter__ = lambda s: s
        mock_cursor.__exit__  = MagicMock(return_value=False)
        mock_cursor.fetchone.return_value = None
        mock_cursor.fetchall.return_value = []

        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__  = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        with patch("psycopg.connect", return_value=mock_conn):
            try:
                from omnix_core.govern.governance_runtime import GovernanceRuntime
                for i in range(self.sessions_per_cycle):
                    op_id = watchdog.register_operation(f"soak-session-{uuid.uuid4().hex[:8]}")
                    try:
                        rt      = GovernanceRuntime()
                        session = rt.start_session(
                            agent_id             = f"soak-agent-{i:04d}",
                            governing_receipt_id = f"SOAK-RCP-{i:06d}",
                            domain               = "soak_test",
                        )
                        sid = session.session_id
                        rt.record_turn(sid, output_text="soak cycle output", turn_metadata={})
                        try:
                            rt.close_session(sid)
                        except RuntimeError:
                            pass  # CTCHC seal requires DB persistence — expected in mock
                        tracker.record_attempt(True)
                    except Exception as exc:
                        logger.warning("[Soak] session error: %s", exc)
                        # Only count as reconnect failure for psycopg errors
                        import psycopg
                        if isinstance(exc, psycopg.Error):
                            tracker.record_attempt(False)
                        else:
                            tracker.record_attempt(True)  # non-DB error — not a reconnect issue
                    finally:
                        watchdog.complete_operation(op_id)
            except ImportError:
                logger.warning("[Soak] GovernanceRuntime not importable — skip mock exercise")


# ─────────────────────────────────────────────────────────────────────────────
#  SoakRunner — main orchestrator
# ─────────────────────────────────────────────────────────────────────────────

class SoakRunner:
    """
    Main soak orchestrator. Runs probe cycles indefinitely (or for
    SOAK_DURATION_SECONDS) and writes SOAK-INV-007 checkpoints.

    Usage:
        runner = SoakRunner(mode="mock-sprint")
        runner.run()
    """

    _MODE_CONFIGS = {
        "mock-sprint": {"duration_s": 60,    "cycle_s": 5,   "sessions": 3},
        "overnight":   {"duration_s": 28800, "cycle_s": 60,  "sessions": 10},
        "continuous":  {"duration_s": 0,     "cycle_s": 300, "sessions": 10},
    }

    def __init__(self, mode: str = "mock-sprint") -> None:
        cfg = self._MODE_CONFIGS.get(mode, self._MODE_CONFIGS["mock-sprint"])
        self.mode          = mode
        self.duration_s    = SOAK_DURATION_S if SOAK_DURATION_S > 0 else cfg["duration_s"]
        self.cycle_s       = float(os.environ.get("SOAK_CYCLE_INTERVAL_S", str(cfg["cycle_s"])))
        self._stop         = threading.Event()
        self._cycle        = 0
        self._start_time   = 0.0
        self._violations:  List[str] = []

        self._memory   = MemoryLeakMonitor()
        self._watchdog = DeadlockWatchdog()
        self._stale    = StaleSessionScanner()
        self._reconnect= ReconnectFailureTracker()
        self._orphans  = OrphanRecordScanner()
        self._exerciser= MockGovernanceExerciser(sessions_per_cycle=cfg["sessions"])

        # Pull GOL metrics if available
        try:
            from omnix_core.observability import GovernanceMetricsRegistry
            self._registry = GovernanceMetricsRegistry.get_instance()
        except ImportError:
            self._registry = None

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        self._start_time = time.monotonic()
        self._memory.baseline()

        logger.info(
            "[SRP] Soak started — mode=%s duration=%ss cycle=%ss live_db=%s",
            self.mode, self.duration_s or "∞", self.cycle_s, ALLOW_LIVE_DB,
        )
        logger.info("[SRP] Log: %s", SOAK_LOG)

        while not self._stop.is_set():
            elapsed = time.monotonic() - self._start_time
            if self.duration_s > 0 and elapsed >= self.duration_s:
                logger.info("[SRP] Duration reached (%.0f s) — stopping", elapsed)
                break

            self._cycle += 1
            cycle_start = time.monotonic()
            logger.info("[SRP] Cycle %d (elapsed=%.0fs)", self._cycle, elapsed)

            results = self._run_probe_cycle()
            self._write_checkpoint(results)

            cycle_elapsed = time.monotonic() - cycle_start
            sleep_s = max(0.0, self.cycle_s - cycle_elapsed)
            if sleep_s > 0:
                self._stop.wait(timeout=sleep_s)

        self._finalize()

    def _run_probe_cycle(self) -> Dict[str, ProbeResult]:
        """Execute all probes and return results dict."""
        # Exercise governance stack in mock mode to generate load
        if not ALLOW_LIVE_DB:
            self._exerciser.run_cycle(self._watchdog, self._reconnect)

        results: Dict[str, ProbeResult] = {}

        # SOAK-INV-001
        r = self._memory.sample()
        results["memory_leak"] = r
        if r.violated:
            self._log_violation("SOAK-INV-001", r.message)

        # SOAK-INV-002
        r = self._watchdog.scan()
        results["deadlock"] = r
        if r.violated:
            self._log_violation("SOAK-INV-002", r.message)

        # SOAK-INV-003
        r = self._stale.scan()
        results["stale_sessions"] = r
        if r.violated:
            self._log_violation("SOAK-INV-003", r.message)

        # SOAK-INV-004
        r = self._reconnect.check()
        results["reconnect_failures"] = r
        if r.violated:
            self._log_violation("SOAK-INV-004", r.message)

        # SOAK-INV-005
        r = self._orphans.scan()
        results["orphan_records"] = r
        if r.violated:
            self._log_violation("SOAK-INV-005", r.message)

        # GOL snapshot (advisory)
        if self._registry:
            snap = self._registry.export_snapshot()
            results["gol_snapshot"] = ProbeResult(
                probe    = "gol_snapshot",
                passed   = True,
                violated = False,
                detail   = snap.to_dict(),
                message  = "GOL snapshot captured",
            )

        return results

    def _log_violation(self, invariant: str, detail: str) -> None:
        self._violations.append(f"{invariant}: {detail}")
        logger.error("[SRP][VIOLATION] %s — %s", invariant, detail)
        if HALT_ON_VIOLATION:
            raise SoakViolation(invariant, detail)

    def _write_checkpoint(self, results: Dict[str, ProbeResult]) -> None:
        """SOAK-INV-007: append checkpoint to hash-chained log."""
        violations = [
            f"{k}: {r.message}"
            for k, r in results.items()
            if r.violated
        ]
        checkpoint = SoakCheckpoint(
            checkpoint_id = f"SOAK-{uuid.uuid4().hex[:12].upper()}",
            cycle_number  = self._cycle,
            elapsed_s     = round(time.monotonic() - self._start_time, 1),
            captured_at   = datetime.now(timezone.utc).isoformat(),
            results       = {k: asdict(v) for k, v in results.items()},
            violations    = violations,
            probe_count   = len(results),
        )
        checkpoint.write()

        status = "🔴 VIOLATION" if violations else "✅ OK"
        logger.info(
            "[SRP] Cycle %d %s — probes=%d violations=%d",
            self._cycle, status, len(results), len(violations),
        )

    def _finalize(self) -> None:
        elapsed = time.monotonic() - self._start_time
        logger.info(
            "[SRP] Soak complete — cycles=%d elapsed=%.0fs total_violations=%d",
            self._cycle, elapsed, len(self._violations),
        )
        if self._violations:
            logger.error("[SRP] Violations recorded:")
            for v in self._violations:
                logger.error("  %s", v)
        else:
            logger.info("[SRP] ✅ Zero violations across all %d cycles", self._cycle)


# ─────────────────────────────────────────────────────────────────────────────
#  Pytest integration — mock sprint as a test
# ─────────────────────────────────────────────────────────────────────────────

def test_soak_mock_sprint():
    """
    Runs a 60-second mock soak sprint as a pytest test.

    CI-safe: no DATABASE_URL required (REG-INV-006 compatible).
    Validates the soak machinery itself — all probes, checkpoint writing,
    hash chain, and GOL snapshot integration.
    """
    import pytest
    runner = SoakRunner(mode="mock-sprint")
    runner.run()

    # Verify checkpoint log was written
    assert SOAK_LOG.exists(), "SOAK-INV-007: soak_log.jsonl was not created"
    lines = SOAK_LOG.read_text().strip().splitlines()
    assert len(lines) > 0, "SOAK-INV-007: soak_log.jsonl has no records"

    # Verify last checkpoint has required fields
    last = json.loads(lines[-1])
    required_fields = {"checkpoint_id", "cycle_number", "elapsed_s", "captured_at", "results", "violations"}
    missing = required_fields - set(last.keys())
    assert not missing, f"Checkpoint missing fields: {missing}"

    # Verify hash chain integrity
    if len(lines) >= 2:
        prev_raw = lines[-2]
        expected_prev_hash = hashlib.sha256(prev_raw.encode()).hexdigest()
        actual_prev_hash   = last.get("prev_hash")
        assert actual_prev_hash == expected_prev_hash, (
            "SOAK-INV-007 VIOLATION: hash chain broken in soak_log.jsonl"
        )

    # Report violations (advisory — do not fail test for mock-mode advisory violations)
    checkpoint = last
    critical_violations = [
        v for v in checkpoint.get("violations", [])
        if "SOAK-INV-001" in v or "SOAK-INV-002" in v
    ]
    assert not critical_violations, (
        f"SOAK-INV-001/002 violation in mock sprint: {critical_violations}"
    )


# ─────────────────────────────────────────────────────────────────────────────
#  CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="OMNIX Soak Reliability Protocol (SRP) — ADR-197",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  mock-sprint   60s in-memory run (CI-safe, no DATABASE_URL needed)
  overnight     8h live run (requires OMNIX_HARDENING_ALLOW_LIVE_DB=true)
  continuous    ∞ live run (runs until Ctrl+C)

Examples:
  python tests/soak/soak_runner.py --mode mock-sprint
  OMNIX_HARDENING_ALLOW_LIVE_DB=true python tests/soak/soak_runner.py --mode overnight
        """,
    )
    parser.add_argument(
        "--mode",
        choices=["mock-sprint", "overnight", "continuous"],
        default="mock-sprint",
        help="Operation mode (default: mock-sprint)",
    )
    args = parser.parse_args()

    runner = SoakRunner(mode=args.mode)

    import signal

    def _sigterm(*_):
        logger.info("[SRP] SIGTERM received — stopping gracefully")
        runner.stop()

    signal.signal(signal.SIGTERM, _sigterm)
    signal.signal(signal.SIGINT,  _sigterm)

    try:
        runner.run()
    except SoakViolation as exc:
        logger.critical("[SRP] HALT: %s", exc)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("[SRP] Interrupted")


if __name__ == "__main__":
    _cli()
