"""
OMNIX Governance Observability Layer (GOL) — ADR-198

The first governance-native observability layer for AI agent decision systems.

Unlike generic APM tools (Datadog, Prometheus, OpenTelemetry), GOL metrics are:

  • Governance-aware  — every metric is bound to session_id + governing_receipt_id
  • Phase-granular    — separate latency histograms per ATF layer phase
  • Trust-tagged      — MANDATE-BOUND / MANDATE-ALIGNED / UNCERTIFIED on close
  • Audit-ready       — snapshot serializes to deterministic JSON (offline-verifiable)
  • Zero-dependency   — stdlib only; runs in Railway, offline, and TESTING=true mode

Invariants enforced here (ADR-198):
  OBS-INV-001  Every OGR lifecycle event emits a metric
  OBS-INV-002  Latency captured per phase: BAR, CCS, CTCHC, MIVP, DB_WRITE, TOTAL
  OBS-INV-003  DB pool stats captured without modification
  OBS-INV-004  All psycopg errors classified into typed buckets
  OBS-INV-005  No PII / keys / payload in labels
  OBS-INV-006  Snapshot deterministic, JSON-serializable, carries snapshot_id

Harold Nunes — OMNIX QUANTUM LTD — May 2026 — ADR-198
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Optional

logger = logging.getLogger("OMNIX.Observability.GOL")

# ─────────────────────────────────────────────────────────────────────────────
#  Phase constants — OBS-INV-002
# ─────────────────────────────────────────────────────────────────────────────
PHASE_SESSION_START  = "SESSION_START"
PHASE_TURN_RECORD    = "TURN_RECORD"
PHASE_SESSION_CLOSE  = "SESSION_CLOSE"
PHASE_SESSION_HALT   = "SESSION_HALT"
PHASE_CTCHC_HASH     = "CTCHC_HASH"       # BEV — cross-turn coherence hash (ADR-183)
PHASE_BAR_SIGN       = "BAR_SIGN"         # BEV — behavioral anchor signing (ADR-181)
PHASE_CCS_COMPUTE    = "CCS_COMPUTE"      # BEV — constraint conformance signal (ADR-182)
PHASE_MIVP_MAS       = "MIVP_MAS"         # MIVP — mandate alignment score (ADR-194)
PHASE_DB_WRITE       = "DB_WRITE"         # any DB persistence call

_ALL_PHASES = (
    PHASE_SESSION_START, PHASE_TURN_RECORD, PHASE_SESSION_CLOSE,
    PHASE_SESSION_HALT, PHASE_CTCHC_HASH, PHASE_BAR_SIGN,
    PHASE_CCS_COMPUTE, PHASE_MIVP_MAS, PHASE_DB_WRITE,
)

# Mandate tiers (mirror ADR-194)
MANDATE_BOUND   = "MANDATE-BOUND"
MANDATE_ALIGNED = "MANDATE-ALIGNED"
UNCERTIFIED     = "UNCERTIFIED"

# psycopg error bucket labels — OBS-INV-004
_ERROR_BUCKETS = (
    "OperationalError",
    "IntegrityError",
    "ForeignKeyViolation",
    "UniqueViolation",
    "PoolTimeout",
    "Other",
)

# Histogram window size (number of samples kept per phase)
_HISTOGRAM_WINDOW = int(os.environ.get("OMNIX_OBS_HISTOGRAM_WINDOW", "1000"))


# ─────────────────────────────────────────────────────────────────────────────
#  LatencyHistogram
# ─────────────────────────────────────────────────────────────────────────────

class LatencyHistogram:
    """
    Rolling-window latency histogram with p50 / p95 / p99 / min / max / mean.

    Thread-safe. Window size is configurable via OMNIX_OBS_HISTOGRAM_WINDOW.
    All values stored in milliseconds.
    """

    __slots__ = ("_phase", "_window", "_lock", "_samples", "_total", "_count")

    def __init__(self, phase: str, window: int = _HISTOGRAM_WINDOW) -> None:
        self._phase   = phase
        self._window  = window
        self._lock    = threading.Lock()
        self._samples: deque[float] = deque(maxlen=window)
        self._total   = 0.0
        self._count   = 0

    def record(self, elapsed_ms: float) -> None:
        with self._lock:
            self._samples.append(elapsed_ms)
            self._total += elapsed_ms
            self._count += 1

    def percentile(self, p: float) -> Optional[float]:
        with self._lock:
            if not self._samples:
                return None
            sorted_samples = sorted(self._samples)
            idx = int(len(sorted_samples) * p / 100.0)
            idx = min(idx, len(sorted_samples) - 1)
            return round(sorted_samples[idx], 3)

    def mean(self) -> Optional[float]:
        with self._lock:
            if not self._count:
                return None
            return round(self._total / self._count, 3)

    def minimum(self) -> Optional[float]:
        with self._lock:
            return round(min(self._samples), 3) if self._samples else None

    def maximum(self) -> Optional[float]:
        with self._lock:
            return round(max(self._samples), 3) if self._samples else None

    def sample_count(self) -> int:
        with self._lock:
            return self._count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase":   self._phase,
            "count":   self.sample_count(),
            "p50_ms":  self.percentile(50),
            "p95_ms":  self.percentile(95),
            "p99_ms":  self.percentile(99),
            "min_ms":  self.minimum(),
            "max_ms":  self.maximum(),
            "mean_ms": self.mean(),
        }


# ─────────────────────────────────────────────────────────────────────────────
#  ErrorCounter
# ─────────────────────────────────────────────────────────────────────────────

class ErrorCounter:
    """
    Typed psycopg error counter — OBS-INV-004.

    Classifies exceptions by psycopg v3 class name into one of the canonical
    buckets. Unknown classes fall into 'Other'. Thread-safe.
    """

    def __init__(self) -> None:
        self._lock    = threading.Lock()
        self._counts  = {bucket: 0 for bucket in _ERROR_BUCKETS}

    def record(self, exc: BaseException) -> str:
        bucket = self._classify(exc)
        with self._lock:
            self._counts[bucket] += 1
        return bucket

    @staticmethod
    def _classify(exc: BaseException) -> str:
        cls_name = type(exc).__name__
        for bucket in _ERROR_BUCKETS[:-1]:   # all except "Other"
            if cls_name == bucket or any(
                b.__name__ == bucket for b in type(exc).__mro__
            ):
                return bucket
        return "Other"

    def to_dict(self) -> Dict[str, int]:
        with self._lock:
            return dict(self._counts)

    def total(self) -> int:
        with self._lock:
            return sum(self._counts.values())


# ─────────────────────────────────────────────────────────────────────────────
#  GovernanceSessionMetric
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class GovernanceSessionMetric:
    """
    Per-session lifecycle record.

    Collected by GovernanceMetricsRegistry and exported in MetricsSnapshot.
    OBS-INV-005: no payload, no keys, no PII stored here.
    """
    session_id:            str
    domain:                str
    started_at:            str               # ISO-8601 UTC
    closed_at:             Optional[str]     # None if still active / halted
    halted_at:             Optional[str]
    turn_count:            int
    mandate_tier:          str               # MANDATE-BOUND / MANDATE-ALIGNED / UNCERTIFIED
    compliance_tier:       str               # ATF compliance tier
    phase_latencies_ms:    Dict[str, float]  # phase → last measured latency
    status:                str               # ACTIVE / CLOSED / HALTED


# ─────────────────────────────────────────────────────────────────────────────
#  GovernancePhaseTimer — context manager
# ─────────────────────────────────────────────────────────────────────────────

class GovernancePhaseTimer:
    """
    Context manager that times a governance phase and records it in the registry.

    Usage:
        with registry.phase_timer(session_id, PHASE_CTCHC_HASH) as t:
            chain = ctchc.add_link(...)
        # t.elapsed_ms is available after the with block
    """

    __slots__ = ("_registry", "_session_id", "_phase", "_start", "elapsed_ms")

    def __init__(
        self,
        registry: "GovernanceMetricsRegistry",
        session_id: str,
        phase: str,
    ) -> None:
        self._registry   = registry
        self._session_id = session_id
        self._phase      = phase
        self._start      = 0.0
        self.elapsed_ms  = 0.0

    def __enter__(self) -> "GovernancePhaseTimer":
        self._start = time.monotonic()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.elapsed_ms = (time.monotonic() - self._start) * 1000.0
        self._registry._record_phase_latency(
            self._session_id, self._phase, self.elapsed_ms
        )
        return False   # never suppress exceptions


# ─────────────────────────────────────────────────────────────────────────────
#  DBPoolStatsSnapshot
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DBPoolStatsSnapshot:
    """Point-in-time snapshot of the psycopg connection pool — OBS-INV-003."""
    captured_at:       str
    status:            str
    pool_size:         int
    pool_available:    int
    requests_waiting:  int
    avg_query_time_ms: float
    total_requests:    int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────────────
#  MetricsSnapshot — the exported artifact
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MetricsSnapshot:
    """
    Point-in-time export of the GovernanceMetricsRegistry.

    JSON-serializable and deterministic for the same input window.
    Carries snapshot_id + captured_at for offline traceability (OBS-INV-006).
    """
    snapshot_id:           str
    captured_at:           str               # ISO-8601 UTC
    window_seconds:        float
    sessions_started:      int
    sessions_closed:       int
    sessions_halted:       int
    sessions_active:       int
    mandate_tiers:         Dict[str, int]    # tier → count
    phase_latencies:       Dict[str, Any]    # phase → histogram dict
    db_pool:               Optional[Dict[str, Any]]
    errors:                Dict[str, int]
    turns_total:           int
    throughput_sessions_per_min: float
    throughput_turns_per_min:    float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MetricsSnapshot):
            return False
        a = self.to_dict()
        b = other.to_dict()
        for key in a:
            if key in ("snapshot_id", "captured_at"):
                continue
            if a[key] != b[key]:
                return False
        return True


# ─────────────────────────────────────────────────────────────────────────────
#  GovernanceMetricsRegistry — singleton
# ─────────────────────────────────────────────────────────────────────────────

class GovernanceMetricsRegistry:
    """
    Thread-safe singleton registry for OMNIX governance observability (ADR-198).

    Lifecycle hooks:
        registry.on_session_start(session)
        with registry.phase_timer(session_id, PHASE_CTCHC_HASH): ...
        registry.on_turn_end(session_id, turn_count)
        registry.on_session_close(session, mandate_tier)
        registry.on_session_halt(session, reason)
        registry.on_db_error(exc)
        registry.observe_pool_stats()          # call periodically
        snapshot = registry.export_snapshot()  # export at any time

    OBS-INV-001 — All lifecycle events emit metrics here.
    OBS-INV-005 — No PII stored. agent_id and session payload are NOT recorded.
    """

    _instance: Optional["GovernanceMetricsRegistry"] = None
    _lock:     threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self._registry_lock = threading.Lock()
        self._started_at    = time.monotonic()
        self._wall_start    = datetime.now(timezone.utc).isoformat()

        # Counters
        self._sessions_started  = 0
        self._sessions_closed   = 0
        self._sessions_halted   = 0
        self._turns_total       = 0

        # Mandate tier distribution — OBS-INV-001
        self._mandate_tiers: Dict[str, int] = {
            MANDATE_BOUND:   0,
            MANDATE_ALIGNED: 0,
            UNCERTIFIED:     0,
        }

        # Active sessions: session_id → GovernanceSessionMetric
        self._active_sessions: Dict[str, GovernanceSessionMetric] = {}

        # Phase latency histograms — OBS-INV-002
        self._histograms: Dict[str, LatencyHistogram] = {
            phase: LatencyHistogram(phase) for phase in _ALL_PHASES
        }

        # Per-session last latency (for snapshot)
        self._session_phase_latencies: Dict[str, Dict[str, float]] = defaultdict(dict)

        # Error counters — OBS-INV-004
        self._error_counter = ErrorCounter()

        # DB pool snapshots — OBS-INV-003
        self._latest_pool_snapshot: Optional[DBPoolStatsSnapshot] = None

        logger.info("[GOL] GovernanceMetricsRegistry initialised (ADR-198)")

    # ── Singleton ─────────────────────────────────────────────────────────────

    @classmethod
    def get_instance(cls) -> "GovernanceMetricsRegistry":
        """Return the process-global singleton registry."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_for_testing(cls) -> "GovernanceMetricsRegistry":
        """Reset the singleton — test isolation only. NOT for production."""
        with cls._lock:
            cls._instance = cls()
        return cls._instance

    # ── Lifecycle hooks — OBS-INV-001 ─────────────────────────────────────────

    def on_session_start(self, session: Any) -> None:
        """
        Record a new governance session opening.

        Parameters
        ----------
        session : OGRSession (or any object with session_id, domain,
                  started_at, compliance_tier attributes)
        """
        session_id = getattr(session, "session_id", str(session))
        domain     = getattr(session, "domain", "unknown")
        started_at = getattr(session, "started_at", datetime.now(timezone.utc).isoformat())
        tier       = getattr(session, "compliance_tier", "unknown")

        with self._registry_lock:
            self._sessions_started += 1
            self._active_sessions[session_id] = GovernanceSessionMetric(
                session_id          = session_id,
                domain              = domain,
                started_at          = started_at,
                closed_at           = None,
                halted_at           = None,
                turn_count          = 0,
                mandate_tier        = UNCERTIFIED,
                compliance_tier     = tier,
                phase_latencies_ms  = {},
                status              = "ACTIVE",
            )
        logger.debug("[GOL] on_session_start session=%s domain=%s", session_id, domain)

    def on_turn_end(self, session_id: str, turn_count: int) -> None:
        """Record that a turn completed. OBS-INV-001."""
        with self._registry_lock:
            self._turns_total += 1
            if session_id in self._active_sessions:
                self._active_sessions[session_id].turn_count = turn_count

    def on_session_close(
        self,
        session: Any,
        mandate_tier: str = UNCERTIFIED,
    ) -> None:
        """
        Record a governance session closing normally.

        Parameters
        ----------
        session      : OGRSession
        mandate_tier : MANDATE-BOUND / MANDATE-ALIGNED / UNCERTIFIED
        """
        session_id = getattr(session, "session_id", str(session))
        closed_at  = datetime.now(timezone.utc).isoformat()

        with self._registry_lock:
            self._sessions_closed += 1
            tier = mandate_tier if mandate_tier in self._mandate_tiers else UNCERTIFIED
            self._mandate_tiers[tier] += 1
            if session_id in self._active_sessions:
                m = self._active_sessions[session_id]
                self._active_sessions[session_id] = GovernanceSessionMetric(
                    session_id         = m.session_id,
                    domain             = m.domain,
                    started_at         = m.started_at,
                    closed_at          = closed_at,
                    halted_at          = None,
                    turn_count         = m.turn_count,
                    mandate_tier       = tier,
                    compliance_tier    = m.compliance_tier,
                    phase_latencies_ms = m.phase_latencies_ms,
                    status             = "CLOSED",
                )
        logger.debug("[GOL] on_session_close session=%s tier=%s", session_id, tier)

    def on_session_halt(self, session: Any, reason: str = "") -> None:
        """Record a governance session halting (HALT state). OBS-INV-001."""
        session_id = getattr(session, "session_id", str(session))
        halted_at  = datetime.now(timezone.utc).isoformat()

        with self._registry_lock:
            self._sessions_halted += 1
            self._mandate_tiers[UNCERTIFIED] += 1
            if session_id in self._active_sessions:
                m = self._active_sessions[session_id]
                self._active_sessions[session_id] = GovernanceSessionMetric(
                    session_id         = m.session_id,
                    domain             = m.domain,
                    started_at         = m.started_at,
                    closed_at          = None,
                    halted_at          = halted_at,
                    turn_count         = m.turn_count,
                    mandate_tier       = UNCERTIFIED,
                    compliance_tier    = m.compliance_tier,
                    phase_latencies_ms = m.phase_latencies_ms,
                    status             = "HALTED",
                )
        logger.warning("[GOL] on_session_halt session=%s reason=%s", session_id, reason)

    # ── Phase timing — OBS-INV-002 ────────────────────────────────────────────

    @contextmanager
    def phase_timer(
        self, session_id: str, phase: str
    ) -> Generator[GovernancePhaseTimer, None, None]:
        """
        Context manager for timing a governance phase.

        Usage:
            with registry.phase_timer(session_id, PHASE_CTCHC_HASH) as t:
                result = ctchc.add_link(...)
            # t.elapsed_ms available after block
        """
        timer = GovernancePhaseTimer(self, session_id, phase)
        timer.__enter__()
        try:
            yield timer
        finally:
            timer.__exit__(None, None, None)

    def _record_phase_latency(
        self, session_id: str, phase: str, elapsed_ms: float
    ) -> None:
        """Internal: record phase latency in histogram and per-session map."""
        if phase in self._histograms:
            self._histograms[phase].record(elapsed_ms)
        with self._registry_lock:
            self._session_phase_latencies[session_id][phase] = elapsed_ms
            if session_id in self._active_sessions:
                self._active_sessions[session_id].phase_latencies_ms[phase] = elapsed_ms

    # ── DB error recording — OBS-INV-004 ──────────────────────────────────────

    def on_db_error(self, exc: BaseException) -> str:
        """
        Record a database error. Returns the classified bucket label.

        Call this from any except block that catches psycopg exceptions.
        OBS-INV-004: errors are classified, never silently discarded.
        """
        bucket = self._error_counter.record(exc)
        logger.warning("[GOL] db_error bucket=%s type=%s", bucket, type(exc).__name__)
        return bucket

    # ── DB pool stats — OBS-INV-003 ───────────────────────────────────────────

    def observe_pool_stats(self) -> Optional[DBPoolStatsSnapshot]:
        """
        Pull current pool stats from DatabaseGateway and store them.
        Returns the snapshot, or None if DatabaseGateway is unavailable.

        OBS-INV-003: values are stored verbatim, not interpolated.
        """
        try:
            from omnix_services.database_service.database_gateway import DatabaseGateway
            raw = DatabaseGateway.get_pool_stats()
        except Exception as exc:
            logger.debug("[GOL] observe_pool_stats unavailable: %s", exc)
            return None

        snapshot = DBPoolStatsSnapshot(
            captured_at       = datetime.now(timezone.utc).isoformat(),
            status            = raw.get("status", "unknown"),
            pool_size         = int(raw.get("pool_size", 0)),
            pool_available    = int(raw.get("pool_available", 0)),
            requests_waiting  = int(raw.get("requests_waiting", 0)),
            avg_query_time_ms = float(raw.get("avg_query_time_ms", 0.0)),
            total_requests    = int(raw.get("total_requests", 0)),
        )
        with self._registry_lock:
            self._latest_pool_snapshot = snapshot
        return snapshot

    # ── Export — OBS-INV-006 ──────────────────────────────────────────────────

    def export_snapshot(self) -> MetricsSnapshot:
        """
        Export a point-in-time MetricsSnapshot.

        Deterministic for the same input window.
        OBS-INV-006: carries snapshot_id + captured_at.
        OBS-INV-005: no PII, no payload, no keys in output.
        """
        now         = time.monotonic()
        elapsed_s   = now - self._started_at
        captured_at = datetime.now(timezone.utc).isoformat()

        with self._registry_lock:
            sessions_started = self._sessions_started
            sessions_closed  = self._sessions_closed
            sessions_halted  = self._sessions_halted
            sessions_active  = sum(
                1 for m in self._active_sessions.values()
                if m.status == "ACTIVE"
            )
            mandate_tiers = dict(self._mandate_tiers)
            turns_total   = self._turns_total
            pool_snap     = self._latest_pool_snapshot

        phase_latencies = {
            phase: hist.to_dict()
            for phase, hist in self._histograms.items()
        }

        minutes = elapsed_s / 60.0 if elapsed_s > 0 else 1.0
        throughput_sessions = round(sessions_closed / minutes, 2)
        throughput_turns    = round(turns_total / minutes, 2)

        return MetricsSnapshot(
            snapshot_id                 = f"SNAP-{uuid.uuid4().hex[:16].upper()}",
            captured_at                 = captured_at,
            window_seconds              = round(elapsed_s, 1),
            sessions_started            = sessions_started,
            sessions_closed             = sessions_closed,
            sessions_halted             = sessions_halted,
            sessions_active             = sessions_active,
            mandate_tiers               = mandate_tiers,
            phase_latencies             = phase_latencies,
            db_pool                     = pool_snap.to_dict() if pool_snap else None,
            errors                      = self._error_counter.to_dict(),
            turns_total                 = turns_total,
            throughput_sessions_per_min = throughput_sessions,
            throughput_turns_per_min    = throughput_turns,
        )

    # ── Convenience: active session count ─────────────────────────────────────

    @property
    def active_session_count(self) -> int:
        with self._registry_lock:
            return sum(
                1 for m in self._active_sessions.values()
                if m.status == "ACTIVE"
            )

    def __repr__(self) -> str:
        return (
            f"GovernanceMetricsRegistry("
            f"started={self._sessions_started}, "
            f"closed={self._sessions_closed}, "
            f"active={self.active_session_count})"
        )
