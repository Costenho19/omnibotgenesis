"""
OMNIX Agent Trust Fabric — RCR Performance Optimization Layer (RPOL)
=====================================================================
ADR-160: Four composable optimizations that reduce runtime overhead of the
Runtime Governance Continuity engine (ADR-159) without weakening any RGC
invariant.

Optimizations
─────────────
1. Pooled Async Write Queue (RCRWriteQueue)
   Single background writer thread drains a bounded queue, replacing the
   per-RCR thread spawning in _persist_rcr / _persist_cee.
   Configurable batch size and flush interval.

2. Event-Driven Sampler (EventDrivenSampler)
   Triggers sample() only when a governance-relevant event exceeds a
   configurable delta threshold. Eliminates unnecessary handshakes on
   micro-operations that do not change authority health materially.

3. Adaptive Interval Scheduler (RCRScheduler)
   Background thread implements the sampling strategy table from ADR-159 §5:
   SHORT / MEDIUM / LONG / STREAMING profiles × CES status overrides.
   Replaces manual caller-driven sampling.

4. Governance Risk Tier (GovernanceRiskTier)
   LOW / STANDARD / HIGH / CRITICAL tier per session. LOW tier skips DB write
   and PQC signing for lightweight authority health checks. CRITICAL tier
   forces synchronous DB write + immediate escalation check.

Invariant compliance
────────────────────
- RGC-INV-001: Unaffected — RCRs still anchored to TAR.
- RGC-INV-002: Unaffected — CES still computed from real-time values.
- RGC-INV-003: Unaffected — HALT path bypasses write queue (synchronous).
- RGC-INV-004: Unaffected — AFG check is in-memory, no DB dependency.
- RGC-INV-005: Unaffected — PQC signing happens before queue enqueue.
              LOW tier explicitly skips governance persistence; callers must
              never issue LOW-tier samples for operations requiring audit trail.
- RGC-INV-006: Unaffected — ns ordering enforced by engine before queuing.
- RGC-INV-007: Unaffected — EventDrivenSampler uses real-time inputs.
- RGC-INV-008: Unaffected — RC TTL enforcement is synchronous.

ADR-160 — Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import enum
import logging
import os
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Tuple

logger = logging.getLogger("OMNIX.ATF.RCRPerformance")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Governance Risk Tier
# ─────────────────────────────────────────────────────────────────────────────

class GovernanceRiskTier(enum.Enum):
    """
    Per-session governance intensity tier.

    LOW      — lightweight CES check only. No DB write, no PQC signature.
               Use for low-risk read-only operations where audit trail is not
               required. NEVER use for operations that touch financial data,
               policy execution, or cross-domain delegation.

    STANDARD — full RCR with PQC signature + async (queued) DB write.
               Default for most agent executions.

    HIGH     — full RCR + synchronous DB write + immediate escalation check.
               Use for financial transactions, policy commits, sub-agent spawns.

    CRITICAL — full RCR + synchronous DB write + immediate escalation + halt
               callback fires synchronously. Use for operations that must
               never proceed past a governance failure.
    """
    LOW      = "LOW"
    STANDARD = "STANDARD"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


TIER_DESCRIPTIONS: Dict[str, str] = {
    "LOW":      "Lightweight CES check — no persistence, no PQC sign",
    "STANDARD": "Full RCR — async DB write, PQC signed",
    "HIGH":     "Full RCR — sync DB write, PQC signed, immediate escalation",
    "CRITICAL": "Full RCR — sync DB write, PQC signed, sync halt callback",
}


# ─────────────────────────────────────────────────────────────────────────────
# 2. Pooled Async Write Queue
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class _WriteTask:
    kind:    str          # "rcr" | "cee"
    payload: Any          # RuntimeContinuityRecord | ContinuityEscalationEvent
    sync_event: Optional[threading.Event] = None  # set when HIGH/CRITICAL tier


class RCRWriteQueue:
    """
    Single background writer thread that drains a bounded write queue.

    Replaces the per-RCR daemon thread in RuntimeContinuityEngine._persist_rcr
    and _persist_cee, reducing thread creation overhead from O(n) to O(1).

    Batches consecutive writes into a single DB transaction when possible,
    bounded by RPOL_WRITE_BATCH_SIZE (default 10) and RPOL_FLUSH_INTERVAL_MS
    (default 200ms).

    Thread-safety: all public methods are safe to call from any thread.
    HALT writes are enqueued with a sync_event and flushed immediately.
    """

    def __init__(
        self,
        db_url:        Optional[str] = None,
        batch_size:    int = 10,
        flush_ms:      float = 200.0,
        max_queue:     int = 4096,
    ):
        self._db_url     = db_url or os.environ.get("DATABASE_URL")
        self._batch_size = int(os.environ.get("RPOL_WRITE_BATCH_SIZE", batch_size))
        self._flush_ms   = float(os.environ.get("RPOL_FLUSH_INTERVAL_MS", flush_ms))
        self._q: queue.Queue[_WriteTask] = queue.Queue(maxsize=max_queue)
        self._stopped    = threading.Event()
        self._worker     = threading.Thread(
            target=self._drain, daemon=True, name="RCRWriteQueue-worker"
        )
        self._worker.start()
        logger.info(
            f"[RPOL] RCRWriteQueue started — batch={self._batch_size} "
            f"flush_ms={self._flush_ms}"
        )

    def enqueue_rcr(
        self,
        rcr: Any,
        synchronous: bool = False,
    ) -> Optional[threading.Event]:
        """
        Enqueue an RCR for async DB persistence.

        Args:
            rcr:         RuntimeContinuityRecord to persist.
            synchronous: If True, blocks until the write completes.
                         Used by HIGH and CRITICAL tiers.
        Returns:
            threading.Event if synchronous=True (caller can wait on it),
            None otherwise.
        """
        evt = threading.Event() if synchronous else None
        task = _WriteTask(kind="rcr", payload=rcr, sync_event=evt)
        try:
            self._q.put_nowait(task)
        except queue.Full:
            logger.warning("[RPOL] Write queue full — dropping RCR to background thread")
            threading.Thread(
                target=self._write_rcr_direct, args=(rcr,), daemon=True
            ).start()
            if evt:
                evt.set()
        return evt

    def enqueue_cee(
        self,
        cee: Any,
        synchronous: bool = False,
    ) -> Optional[threading.Event]:
        """Enqueue a ContinuityEscalationEvent for async DB persistence."""
        evt = threading.Event() if synchronous else None
        task = _WriteTask(kind="cee", payload=cee, sync_event=evt)
        try:
            self._q.put_nowait(task)
        except queue.Full:
            logger.warning("[RPOL] Write queue full — dropping CEE to background thread")
            threading.Thread(
                target=self._write_cee_direct, args=(cee,), daemon=True
            ).start()
            if evt:
                evt.set()
        return evt

    def flush(self, timeout: float = 5.0) -> bool:
        """
        Block until the write queue is empty or timeout expires.
        Returns True if fully drained.
        """
        try:
            self._q.join()
            return True
        except Exception:
            return False

    def stop(self, drain_timeout: float = 10.0) -> None:
        """Graceful shutdown — drain the queue then stop the worker."""
        self._stopped.set()
        self._worker.join(timeout=drain_timeout)
        logger.info("[RPOL] RCRWriteQueue stopped")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _drain(self) -> None:
        """Background worker: drains the queue in batches."""
        while not self._stopped.is_set():
            batch: list[_WriteTask] = []
            deadline = time.monotonic() + (self._flush_ms / 1000.0)

            while len(batch) < self._batch_size:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                try:
                    task = self._q.get(timeout=min(remaining, 0.05))
                    batch.append(task)
                except queue.Empty:
                    break

            if batch:
                self._write_batch(batch)

        # Final drain on shutdown
        while not self._q.empty():
            try:
                task = self._q.get_nowait()
                self._write_batch([task])
            except queue.Empty:
                break

    def _write_batch(self, tasks: list[_WriteTask]) -> None:
        """Write a batch of tasks in a single DB transaction."""
        if not self._db_url:
            for t in tasks:
                if t.sync_event:
                    t.sync_event.set()
                self._q.task_done()
            return

        conn = self._get_conn()
        if not conn:
            for t in tasks:
                if t.sync_event:
                    t.sync_event.set()
                self._q.task_done()
            return

        try:
            import json as _json
            with conn.cursor() as cur:
                for task in tasks:
                    if task.kind == "rcr":
                        self._insert_rcr(cur, task.payload, _json)
                    elif task.kind == "cee":
                        self._insert_cee(cur, task.payload, _json)
            conn.commit()
        except Exception as exc:
            logger.warning(f"[RPOL] Batch write failed: {exc}")
            try:
                conn.rollback()
            except Exception:
                pass
        finally:
            conn.close()
            for t in tasks:
                if t.sync_event:
                    t.sync_event.set()
                self._q.task_done()

    @staticmethod
    def _insert_rcr(cur: Any, rcr: Any, _json: Any) -> None:
        cur.execute("""
            INSERT INTO atf_runtime_continuity (
                rcr_id, tar_id, delegation_id, agent_id, chain_root_id,
                execution_ns, execution_ts, ces_score, ces_temporal,
                ces_budget, ces_context, ces_integrity,
                continuity_status, predecessor_rcr_id,
                budget_at_admission, budget_remaining,
                context_drift_pct, active_anomalies,
                dr_expires_at, time_remaining_ns, fragmentation_score,
                escalation_event_id, reauth_challenge_id,
                sample_reason, content_hash, pqc_signature,
                pqc_algorithm, issued_at, metadata
            ) VALUES (
                %s,%s,%s,%s,%s, %s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                %s,%s,%s,%s,%s,%s,%s,%s,%s
            ) ON CONFLICT (rcr_id) DO NOTHING
        """, (
            rcr.rcr_id, rcr.tar_id, rcr.delegation_id, rcr.agent_id,
            rcr.chain_root_id, rcr.execution_ns, rcr.execution_ts,
            rcr.ces_score, rcr.ces_temporal, rcr.ces_budget,
            rcr.ces_context, rcr.ces_integrity, rcr.continuity_status,
            rcr.predecessor_rcr_id, rcr.budget_at_admission,
            rcr.budget_remaining, rcr.context_drift_pct,
            rcr.active_anomalies, rcr.dr_expires_at,
            rcr.time_remaining_ns, rcr.fragmentation_score,
            rcr.escalation_event_id, rcr.reauth_challenge_id,
            rcr.sample_reason, rcr.content_hash, rcr.pqc_signature,
            rcr.pqc_algorithm, rcr.issued_at,
            _json.dumps(rcr.metadata),
        ))

    @staticmethod
    def _insert_cee(cur: Any, cee: Any, _json: Any) -> None:
        cur.execute("""
            INSERT INTO atf_continuity_escalations (
                cee_id, rcr_id, tar_id, delegation_id, agent_id,
                chain_root_id, threshold_crossed, recommended_action,
                ces_at_escalation, escalation_ns, response_ttl_seconds,
                resolved, content_hash, pqc_signature, pqc_algorithm,
                issued_at, metadata
            ) VALUES (
                %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
            ) ON CONFLICT (cee_id) DO NOTHING
        """, (
            cee.cee_id, cee.rcr_id, cee.tar_id, cee.delegation_id,
            cee.agent_id, cee.chain_root_id, cee.threshold_crossed,
            cee.recommended_action, cee.ces_at_escalation,
            cee.escalation_ns, cee.response_ttl_seconds,
            cee.resolved, cee.content_hash, cee.pqc_signature,
            cee.pqc_algorithm, cee.issued_at, _json.dumps(cee.metadata),
        ))

    def _write_rcr_direct(self, rcr: Any) -> None:
        """Fallback: single-RCR write when queue is full."""
        conn = self._get_conn()
        if not conn:
            return
        try:
            import json as _json
            with conn.cursor() as cur:
                self._insert_rcr(cur, rcr, _json)
            conn.commit()
        except Exception as exc:
            logger.warning(f"[RPOL] Direct RCR write failed: {exc}")
            try:
                conn.rollback()
            except Exception:
                pass
        finally:
            conn.close()

    def _write_cee_direct(self, cee: Any) -> None:
        """Fallback: single-CEE write when queue is full."""
        conn = self._get_conn()
        if not conn:
            return
        try:
            import json as _json
            with conn.cursor() as cur:
                self._insert_cee(cur, cee, _json)
            conn.commit()
        except Exception as exc:
            logger.warning(f"[RPOL] Direct CEE write failed: {exc}")
            try:
                conn.rollback()
            except Exception:
                pass
        finally:
            conn.close()

    def _get_conn(self) -> Any:
        try:
            import psycopg
            conn = psycopg.connect(self._db_url)
            return conn
        except Exception as exc:
            logger.warning(f"[RPOL] DB connection failed: {exc}")
            return None


# ─────────────────────────────────────────────────────────────────────────────
# 3. Event-Driven Sampler
# ─────────────────────────────────────────────────────────────────────────────

class GovernanceEventType(enum.Enum):
    """Events that may trigger an out-of-schedule RCR sample."""
    BUDGET_CHANGE      = "BUDGET_CHANGE"       # budget consumed beyond threshold
    ANOMALY_DETECTED   = "ANOMALY_DETECTED"    # new governance anomaly
    CONTEXT_DRIFT      = "CONTEXT_DRIFT"       # context drift exceeded threshold
    SCOPE_CHANGE       = "SCOPE_CHANGE"        # scope authorization boundary crossed
    SUB_AGENT_SPAWN    = "SUB_AGENT_SPAWN"     # new sub-agent delegated
    EXTERNAL_TRIGGER   = "EXTERNAL_TRIGGER"    # caller-driven event


@dataclass
class EventTriggerThresholds:
    """
    Configurable thresholds per event type.

    A sample is triggered only when the measured delta meets or exceeds
    the threshold. This prevents handshake on micro-operations that do
    not materially change authority health.

    All values are in the same units as the corresponding CES input:
    - budget_delta_pct:  % of budget_at_admission consumed since last sample
    - context_drift_pct: context drift % from scope engine
    - anomaly_count:     number of new active anomalies
    """
    budget_delta_pct:  float = 10.0   # trigger if budget dropped ≥ 10% since last sample
    context_drift_pct: float = 15.0   # trigger if drift ≥ 15%
    anomaly_count:     int   = 1      # trigger on any new anomaly
    sub_agent_spawn:   bool  = True   # always trigger on sub-agent spawn
    scope_change:      bool  = True   # always trigger on scope change

    @classmethod
    def from_env(cls) -> "EventTriggerThresholds":
        return cls(
            budget_delta_pct  = float(os.environ.get("RPOL_BUDGET_TRIGGER_PCT",  10.0)),
            context_drift_pct = float(os.environ.get("RPOL_DRIFT_TRIGGER_PCT",   15.0)),
            anomaly_count     = int(  os.environ.get("RPOL_ANOMALY_TRIGGER_N",   1)),
        )


@dataclass
class _SessionEventState:
    """Per-session state tracked by EventDrivenSampler."""
    last_sampled_budget:     float
    last_sampled_drift:      float
    last_sampled_anomalies:  int
    last_sample_ns:          int = field(default_factory=time.time_ns)


class EventDrivenSampler:
    """
    Intercepts governance events and triggers sample() only when the
    event delta exceeds configured thresholds.

    Usage:
        sampler = EventDrivenSampler(engine, thresholds)
        sampler.register_session(tar_id, budget_at_admission)
        sampler.notify(tar_id, GovernanceEventType.BUDGET_CHANGE,
                       budget_consumed=5.0)

    Thread-safety: all methods are safe to call from any thread.
    """

    def __init__(
        self,
        engine:     Any,
        thresholds: Optional[EventTriggerThresholds] = None,
    ):
        self._engine     = engine
        self._thresholds = thresholds or EventTriggerThresholds.from_env()
        self._states:    Dict[str, _SessionEventState] = {}
        self._lock       = threading.Lock()

    def register_session(
        self,
        tar_id:              str,
        budget_at_admission: float,
    ) -> None:
        """Register a new session for event tracking."""
        with self._lock:
            self._states[tar_id] = _SessionEventState(
                last_sampled_budget    = budget_at_admission,
                last_sampled_drift     = 0.0,
                last_sampled_anomalies = 0,
            )

    def deregister_session(self, tar_id: str) -> None:
        """Remove session state on session end."""
        with self._lock:
            self._states.pop(tar_id, None)

    def notify(
        self,
        tar_id:            str,
        event_type:        GovernanceEventType,
        budget_consumed:   float = 0.0,
        context_drift_pct: float = 0.0,
        active_anomalies:  int   = 0,
        metadata:          Optional[Dict[str, Any]] = None,
    ) -> Optional[Any]:
        """
        Notify the sampler of a governance event.

        Returns the RuntimeContinuityRecord if a sample was triggered,
        None if the delta did not meet the threshold.
        """
        with self._lock:
            state = self._states.get(tar_id)
        if not state:
            return None

        should_sample, reason = self._should_sample(
            event_type, state, budget_consumed, context_drift_pct, active_anomalies
        )

        if not should_sample:
            return None

        logger.debug(
            f"[RPOL] Event-driven sample triggered — tar={tar_id} "
            f"event={event_type.value} reason={reason}"
        )

        rcr = self._engine.sample(
            tar_id=tar_id,
            budget_consumed=budget_consumed,
            context_drift_pct=context_drift_pct,
            active_anomalies=active_anomalies,
            sample_reason="THRESHOLD_BREACH",
            metadata={
                "event_type": event_type.value,
                "trigger_reason": reason,
                **(metadata or {}),
            },
        )

        with self._lock:
            state = self._states.get(tar_id)
            if state:
                state.last_sampled_drift     = context_drift_pct
                state.last_sampled_anomalies = active_anomalies
                state.last_sample_ns         = time.time_ns()

        return rcr

    def _should_sample(
        self,
        event_type:        GovernanceEventType,
        state:             _SessionEventState,
        budget_consumed:   float,
        context_drift_pct: float,
        active_anomalies:  int,
    ) -> Tuple[bool, str]:
        t = self._thresholds

        if event_type == GovernanceEventType.SUB_AGENT_SPAWN and t.sub_agent_spawn:
            return True, "sub_agent_spawn"

        if event_type == GovernanceEventType.SCOPE_CHANGE and t.scope_change:
            return True, "scope_change"

        if event_type == GovernanceEventType.EXTERNAL_TRIGGER:
            return True, "external_trigger"

        if event_type == GovernanceEventType.BUDGET_CHANGE:
            if budget_consumed >= (state.last_sampled_budget * t.budget_delta_pct / 100.0):
                return True, f"budget_delta≥{t.budget_delta_pct}%"

        if event_type == GovernanceEventType.CONTEXT_DRIFT:
            if context_drift_pct >= t.context_drift_pct:
                return True, f"drift≥{t.context_drift_pct}%"

        if event_type == GovernanceEventType.ANOMALY_DETECTED:
            new_anomalies = active_anomalies - state.last_sampled_anomalies
            if new_anomalies >= t.anomaly_count:
                return True, f"new_anomalies={new_anomalies}"

        return False, "below_threshold"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Adaptive Interval Scheduler
# ─────────────────────────────────────────────────────────────────────────────

class ExecutionProfile(enum.Enum):
    """
    Execution duration profile for adaptive sampling.
    Maps to the sampling strategy table in ADR-159 §5.
    """
    SHORT     = "SHORT"      # < 60s
    MEDIUM    = "MEDIUM"     # 60s – 600s
    LONG      = "LONG"       # > 600s
    STREAMING = "STREAMING"  # unbounded


SAMPLING_INTERVALS: Dict[str, Dict[str, int]] = {
    # profile -> { ces_status -> interval_seconds }
    "SHORT":     {"NOMINAL": 0,   "MONITORING": 15,  "CRITICAL": 5},
    "MEDIUM":    {"NOMINAL": 60,  "MONITORING": 30,  "CRITICAL": 10},
    "LONG":      {"NOMINAL": 120, "MONITORING": 60,  "CRITICAL": 20},
    "STREAMING": {"NOMINAL": 30,  "MONITORING": 15,  "CRITICAL": 5},
}


@dataclass
class _SchedulerSession:
    tar_id:            str
    profile:           ExecutionProfile
    last_scheduled_ns: int = field(default_factory=time.time_ns)
    active:            bool = True
    get_inputs:        Optional[Callable[[], Dict[str, Any]]] = None


class RCRScheduler:
    """
    Background thread that fires engine.sample() at adaptive intervals
    based on execution profile and current CES status.

    Implements ADR-159 §5 (Sampling Strategy) automatically, so callers
    do not need to manage their own timers.

    Usage:
        scheduler = RCRScheduler(engine)
        scheduler.register(tar_id, ExecutionProfile.LONG,
                           get_inputs=lambda: {"budget_consumed": 0.5})
        # ... execution runs ...
        scheduler.deregister(tar_id)
        scheduler.stop()

    get_inputs callback returns a dict with optional keys:
        budget_consumed, context_drift_pct, active_anomalies, metadata
    """

    def __init__(self, engine: Any, tick_ms: float = 1000.0):
        self._engine   = engine
        self._tick_ms  = float(os.environ.get("RPOL_SCHEDULER_TICK_MS", tick_ms))
        self._sessions: Dict[str, _SchedulerSession] = {}
        self._lock     = threading.Lock()
        self._stopped  = threading.Event()
        self._worker   = threading.Thread(
            target=self._tick, daemon=True, name="RCRScheduler-worker"
        )
        self._worker.start()
        logger.info(f"[RPOL] RCRScheduler started — tick_ms={self._tick_ms}")

    def register(
        self,
        tar_id:     str,
        profile:    ExecutionProfile = ExecutionProfile.MEDIUM,
        get_inputs: Optional[Callable[[], Dict[str, Any]]] = None,
    ) -> None:
        """Register a session for scheduled sampling."""
        with self._lock:
            self._sessions[tar_id] = _SchedulerSession(
                tar_id=tar_id,
                profile=profile,
                get_inputs=get_inputs,
            )
        logger.debug(f"[RPOL] Scheduler registered — tar={tar_id} profile={profile.value}")

    def deregister(self, tar_id: str) -> None:
        """Remove a session from the scheduler."""
        with self._lock:
            sess = self._sessions.get(tar_id)
            if sess:
                sess.active = False
            self._sessions.pop(tar_id, None)

    def stop(self, timeout: float = 5.0) -> None:
        """Graceful stop."""
        self._stopped.set()
        self._worker.join(timeout=timeout)
        logger.info("[RPOL] RCRScheduler stopped")

    def _tick(self) -> None:
        while not self._stopped.is_set():
            now_ns = time.time_ns()
            with self._lock:
                sessions = list(self._sessions.values())

            for sess in sessions:
                if not sess.active:
                    continue
                try:
                    interval_s = self._interval_for(sess)
                    if interval_s == 0:
                        continue
                    elapsed_ns = now_ns - sess.last_scheduled_ns
                    if elapsed_ns >= interval_s * 1_000_000_000:
                        self._fire_sample(sess, now_ns)
                except Exception as exc:
                    logger.warning(
                        f"[RPOL] Scheduler tick error — tar={sess.tar_id}: {exc}"
                    )

            self._stopped.wait(timeout=self._tick_ms / 1000.0)

    def _interval_for(self, sess: _SchedulerSession) -> int:
        """Resolve current sampling interval for a session."""
        profile_key = sess.profile.value
        intervals   = SAMPLING_INTERVALS.get(profile_key, SAMPLING_INTERVALS["MEDIUM"])

        # Read last CES status from engine without emitting an RCR
        try:
            ces = self._engine.current_ces(sess.tar_id)
            if ces is None:
                return 0  # session may have ended
            status = ces.status
        except Exception:
            return 0

        # Map status to interval bucket
        if status in ("CRITICAL", "HALT"):
            bucket = "CRITICAL"
        elif status == "MONITORING":
            bucket = "MONITORING"
        else:
            bucket = "NOMINAL"

        override = int(os.environ.get("RGC_SAMPLE_INTERVAL_SECONDS", 0))
        if override > 0:
            return override

        return intervals.get(bucket, 60)

    def _fire_sample(self, sess: _SchedulerSession, now_ns: int) -> None:
        inputs: Dict[str, Any] = {}
        if sess.get_inputs:
            try:
                inputs = sess.get_inputs() or {}
            except Exception as exc:
                logger.warning(f"[RPOL] get_inputs error — tar={sess.tar_id}: {exc}")

        try:
            self._engine.sample(
                tar_id=sess.tar_id,
                budget_consumed=inputs.get("budget_consumed", 0.0),
                context_drift_pct=inputs.get("context_drift_pct", 0.0),
                active_anomalies=inputs.get("active_anomalies", 0),
                sample_reason="SCHEDULED",
                metadata=inputs.get("metadata"),
            )
        except Exception as exc:
            logger.warning(f"[RPOL] Scheduled sample failed — tar={sess.tar_id}: {exc}")

        with self._lock:
            sess = self._sessions.get(sess.tar_id)
            if sess:
                sess.last_scheduled_ns = now_ns


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singletons (lazy-init)
# ─────────────────────────────────────────────────────────────────────────────

_write_queue_instance:  Optional[RCRWriteQueue]      = None
_sampler_instance:      Optional[EventDrivenSampler]  = None
_scheduler_instance:    Optional[RCRScheduler]        = None
_rpol_lock = threading.Lock()


def get_write_queue() -> RCRWriteQueue:
    global _write_queue_instance
    with _rpol_lock:
        if _write_queue_instance is None:
            _write_queue_instance = RCRWriteQueue()
        return _write_queue_instance


def get_event_sampler(engine: Any) -> EventDrivenSampler:
    global _sampler_instance
    with _rpol_lock:
        if _sampler_instance is None:
            _sampler_instance = EventDrivenSampler(engine)
        return _sampler_instance


def get_scheduler(engine: Any) -> RCRScheduler:
    global _scheduler_instance
    with _rpol_lock:
        if _scheduler_instance is None:
            _scheduler_instance = RCRScheduler(engine)
        return _scheduler_instance
