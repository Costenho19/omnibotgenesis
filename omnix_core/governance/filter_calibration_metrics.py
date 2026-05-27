"""
ADR-127 — Phase 3: Filter Calibration Metrics

Async-buffered, zero-latency metrics collection for every governance gate.
Writes are enqueued in memory and flushed to PostgreSQL by a background
thread — the decision path never waits for a DB write.

Usage
─────
    from omnix_core.governance.filter_calibration_metrics import (
        FilterCalibrationMetricsService,
        FilterCalibrationEvent,
        extract_event_from_result,
        OUTCOME_PASS, OUTCOME_BLOCK, OUTCOME_HOLD, OUTCOME_SKIP,
    )

    svc = FilterCalibrationMetricsService()
    svc.ensure_schema()

    event = extract_event_from_result(result, domain="trading", asset="BTC")
    svc.record(event)                     # non-blocking — returns immediately

    stats = svc.query_gate_stats("coherence", window="1d")
    summary = svc.query_summary(window="1w")
"""

import json
import logging
import os
import queue
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("OMNIX.FilterCalibration")

# ── Gate outcome constants ─────────────────────────────────────────────────────
OUTCOME_PASS  =  0
OUTCOME_BLOCK =  1
OUTCOME_HOLD  =  2
OUTCOME_SKIP  = -1   # gate was not reached / not applicable

_OUTCOME_LABELS: Dict[int, str] = {
    OUTCOME_PASS:  "PASS",
    OUTCOME_BLOCK: "BLOCK",
    OUTCOME_HOLD:  "HOLD",
    OUTCOME_SKIP:  "SKIP",
}

# ── Gate column names (order matters for queries) ──────────────────────────────
GATES: Tuple[str, ...] = (
    "layer0",
    "cag",
    "coherence",
    "mc",
    "black_swan",
    "ecw",
    "sharia",
    "aml",
    "fraud",
    "jurisdiction",
)

# ── Window → PostgreSQL INTERVAL ───────────────────────────────────────────────
_WINDOW_INTERVALS: Dict[str, str] = {
    "1h": "1 hour",
    "1d": "1 day",
    "1w": "7 days",
}

_TABLE = "filter_calibration_events"

# Black swan level constants
BS_NONE = "NONE"
BS_LOW  = "LOW"
BS_HIGH = "HIGH"


# ── Event dataclass ────────────────────────────────────────────────────────────

@dataclass
class FilterCalibrationEvent:
    """
    One record per governance evaluation decision.

    All gate_* fields use the OUTCOME_* constants.
    OUTCOME_SKIP (-1) means the gate was not executed for this decision.
    """
    domain:               str            = "trading"
    asset:                Optional[str]  = None
    client_id:            Optional[str]  = None
    final_decision:       str            = "BLOCKED"
    processing_time_ms:   Optional[int]  = None

    # Per-gate outcomes
    gate_layer0:          int = OUTCOME_SKIP
    gate_cag:             int = OUTCOME_SKIP
    gate_coherence:       int = OUTCOME_SKIP
    gate_mc:              int = OUTCOME_SKIP
    gate_black_swan:      int = OUTCOME_SKIP
    gate_ecw:             int = OUTCOME_SKIP
    gate_sharia:          int = OUTCOME_SKIP
    gate_aml:             int = OUTCOME_SKIP
    gate_fraud:           int = OUTCOME_SKIP
    gate_jurisdiction:    int = OUTCOME_SKIP

    # Decision metrics
    dci_score:            Optional[float] = None   # 0–100: ALIGNED<35, TENSIONED<70, CONTRADICTORY
    coherence_score:      Optional[float] = None   # 0–100: internal signal agreement
    black_swan_level:     Optional[str]   = None   # "NONE" | "LOW" | "HIGH"
    escalation_triggered: bool            = False  # ADR-119: BS_HIGH → raised coherence thresholds

    # Optional override — if None, the DB column uses NOW()
    event_ts:             Optional[str]   = None


# ── Extraction helper ──────────────────────────────────────────────────────────

def _outcome_from_result_str(result_str: str) -> int:
    """Convert a gate result string to an OUTCOME_* constant."""
    s = (result_str or "").upper()
    if s in ("PASS", "PASSED", "OK", "APPROVED", "ADMISSIBLE"):
        return OUTCOME_PASS
    if s in ("BLOCKED", "BLOCK", "VETO", "REJECTED", "FAILED",
             "INADMISSIBLE", "AML_INTERNAL_ERROR", "FRAUD_INTERNAL_ERROR"):
        return OUTCOME_BLOCK
    if s in ("HOLD",):
        return OUTCOME_HOLD
    return OUTCOME_SKIP


def _scan_gate_results(gate_results: List[Dict], signal_keywords: Tuple[str, ...]) -> int:
    """
    Search gate_results for a gate whose signal or name matches any of the
    given keywords and return the corresponding OUTCOME_* constant.
    """
    for gr in gate_results:
        sig  = (gr.get("signal", "") or "").lower()
        name = (gr.get("name", "")   or "").lower()
        cpid = (gr.get("checkpoint", "") or "").lower()
        if any(kw in sig or kw in name or kw in cpid for kw in signal_keywords):
            return _outcome_from_result_str(gr.get("result", ""))
    return OUTCOME_SKIP


def _scan_trace(decision_trace: List[str], pass_keywords: Tuple[str, ...],
                block_keywords: Tuple[str, ...]) -> int:
    """
    Scan decision_trace strings for pass/block patterns.
    Block keywords take precedence over pass keywords.
    """
    found_pass  = False
    found_block = False
    for entry in decision_trace:
        e = (entry or "").upper()
        if any(kw.upper() in e for kw in block_keywords):
            found_block = True
        if any(kw.upper() in e for kw in pass_keywords):
            found_pass = True
    if found_block:
        return OUTCOME_BLOCK
    if found_pass:
        return OUTCOME_PASS
    return OUTCOME_SKIP


DECISION_TRACE_FORMAT_VERSION = "v1"
"""
Expected version tag in result dicts produced by GovernanceEvaluationEngine.
Set result['_trace_version'] = DECISION_TRACE_FORMAT_VERSION in the engine.
If absent or mismatched, extract_event_from_result logs a warning so format
drift is detectable immediately rather than silently falling to OUTCOME_SKIP.
"""


def extract_event_from_result(
    result:             Dict[str, Any],
    domain:             str            = "trading",
    asset:              Optional[str]  = None,
    client_id:          Optional[str]  = None,
    processing_time_ms: Optional[int]  = None,
) -> FilterCalibrationEvent:
    """
    Build a FilterCalibrationEvent from a GovernanceEvaluationEngine.evaluate()
    result dict.

    This function is best-effort — it never raises. If a gate's outcome cannot
    be determined, OUTCOME_SKIP is used. The call is O(N) over gate_results and
    decision_trace, which are small lists (< 20 entries each).

    I-4 guard: validates '_trace_version' field to detect format drift early.
    If the field is absent or mismatched, a WARNING is logged. Behavior is
    unchanged — extraction continues best-effort with OUTCOME_SKIP fallback.
    """
    try:
        trace_version = result.get("_trace_version")
        if trace_version is None:
            logger.debug(
                "[FCM] result dict has no '_trace_version' field. "
                "Add result['_trace_version'] = '%s' in GovernanceEvaluationEngine "
                "to enable format-drift detection (I-4).",
                DECISION_TRACE_FORMAT_VERSION,
            )
        elif trace_version != DECISION_TRACE_FORMAT_VERSION:
            logger.warning(
                "[FCM] decision_trace format version mismatch: expected '%s', "
                "got '%s'. Gate extraction may produce unexpected OUTCOME_SKIP values. "
                "Update DECISION_TRACE_FORMAT_VERSION or the engine output format.",
                DECISION_TRACE_FORMAT_VERSION,
                trace_version,
            )

        gate_results   = result.get("gate_results",   []) or []
        decision_trace = result.get("decision_trace", []) or []
        veto_chain     = result.get("veto_chain",     []) or []
        scores         = result.get("scores",         {}) or {}
        final_decision = (result.get("decision", "BLOCKED") or "BLOCKED").upper()

        # ── Layer 0 ────────────────────────────────────────────────────────────
        layer0_result = result.get("layer", "") or ""
        if "LAYER_0" in layer0_result.upper():
            gate_layer0 = OUTCOME_BLOCK
        elif result.get("layer_0"):
            admis = (result["layer_0"].get("admissibility", "") or "").upper()
            gate_layer0 = OUTCOME_BLOCK if admis == "INADMISSIBLE" else OUTCOME_PASS
        else:
            gate_layer0 = _scan_trace(
                decision_trace,
                pass_keywords=("LAYER_0 PASS", "LAYER0 PASS", "SAE PASS"),
                block_keywords=("LAYER_0 INADMISSIBLE", "LAYER0 BLOCKED"),
            )
            if gate_layer0 == OUTCOME_SKIP and result.get("checkpoints_total", 0) > 0:
                gate_layer0 = OUTCOME_PASS   # layer0 ran and passed if we got to checkpoints

        # ── CAG ────────────────────────────────────────────────────────────────
        gate_cag = _scan_trace(
            decision_trace,
            pass_keywords=("CAG_PASS", "CAG PASS", "CAG_APPROVED", "CAG SESSION_PASS"),
            block_keywords=("CAG SESSION_BLOCKED", "CAG_BLOCKED", "CAG BLOCKED"),
        )
        if gate_cag == OUTCOME_SKIP:
            gate_cag = _scan_gate_results(gate_results, ("cag", "context_admission"))

        # ── Coherence ──────────────────────────────────────────────────────────
        gate_coherence = _scan_gate_results(
            gate_results, ("coherence", "signal_coherence", "temporal_coherence")
        )
        if gate_coherence == OUTCOME_SKIP:
            gate_coherence = _scan_trace(
                decision_trace,
                pass_keywords=("COHERENCE.*PASS", "COHERENCE_PASS"),
                block_keywords=("COHERENCE.*BLOCK", "COHERENCE_BLOCK", "COHERENCE.*VETO"),
            )

        # ── Monte Carlo ────────────────────────────────────────────────────────
        gate_mc = _scan_gate_results(
            gate_results, ("logic_consistency", "mc", "monte_carlo", "montecarlo")
        )
        if gate_mc == OUTCOME_SKIP:
            gate_mc = _scan_trace(
                decision_trace,
                pass_keywords=("MC_PASS", "MONTE_CARLO_PASS", "MC PASS"),
                block_keywords=("MC_NEG_ER", "MC_BLOCK", "MC BLOCK", "MONTE_CARLO.*VETO"),
            )

        # ── Black Swan ─────────────────────────────────────────────────────────
        gate_black_swan = _scan_gate_results(
            gate_results, ("black_swan", "blackswan", "bs_")
        )
        if gate_black_swan == OUTCOME_SKIP:
            gate_black_swan = _scan_trace(
                decision_trace,
                pass_keywords=("BS_PASS", "BS PASS", "BLACK_SWAN PASS"),
                block_keywords=("BS_BLOCK", "BS BLOCK", "BS_VETO", "BLACK_SWAN.*BLOCK"),
            )

        # ── ECW ────────────────────────────────────────────────────────────────
        gate_ecw = _scan_gate_results(gate_results, ("ecw", "edge_confirmation"))
        if gate_ecw == OUTCOME_SKIP:
            gate_ecw = _scan_trace(
                decision_trace,
                pass_keywords=("ECW_PASS", "ECW PASS", "EDGE_CONFIRMED"),
                block_keywords=("ECW_BLOCK", "ECW BLOCK", "EDGE_UNCONFIRMED"),
            )

        # ── Sharia ─────────────────────────────────────────────────────────────
        gate_sharia = _scan_gate_results(gate_results, ("sharia", "cp-6", "gharar"))
        if gate_sharia == OUTCOME_SKIP:
            gate_sharia = _scan_trace(
                decision_trace,
                pass_keywords=("CP-6 SHARIA_PASS", "SHARIA_PASS", "SHARIA PASS"),
                block_keywords=("CP-6 SHARIA_VETO", "SHARIA_VETO", "SHARIA_BLOCKED"),
            )
        # Also check compliance_blocks
        sharia_block = result.get("compliance_blocks", {}).get("sharia_compliance", {})
        if gate_sharia == OUTCOME_SKIP and sharia_block:
            r = (sharia_block.get("result", "") or "").lower()
            if r == "passed":
                gate_sharia = OUTCOME_PASS
            elif r in ("failed", "blocked"):
                gate_sharia = OUTCOME_BLOCK

        # ── AML ────────────────────────────────────────────────────────────────
        gate_aml = _scan_gate_results(gate_results, ("aml", "cp-9", "anti_money"))
        if gate_aml == OUTCOME_SKIP:
            gate_aml = _scan_trace(
                decision_trace,
                pass_keywords=("CP-9 AML_PASS", "AML_PASS", "AML PASS"),
                block_keywords=("CP-9 AML_VETO", "AML_VETO", "AML_ERROR_BLOCKED", "AML BLOCK"),
            )
        aml_block = result.get("compliance_blocks", {}).get("aml_compliance", {})
        if gate_aml == OUTCOME_SKIP and aml_block:
            r = (aml_block.get("result", "") or "").lower()
            if r == "passed":
                gate_aml = OUTCOME_PASS
            elif r in ("failed", "blocked"):
                gate_aml = OUTCOME_BLOCK

        # ── Fraud ──────────────────────────────────────────────────────────────
        gate_fraud = _scan_gate_results(gate_results, ("fraud", "cp-10"))
        if gate_fraud == OUTCOME_SKIP:
            gate_fraud = _scan_trace(
                decision_trace,
                pass_keywords=("CP-10 FRAUD_PASS", "FRAUD_PASS", "FRAUD PASS"),
                block_keywords=("CP-10 FRAUD_VETO", "FRAUD_VETO", "FRAUD_ERROR_BLOCKED"),
            )
        fraud_block = result.get("compliance_blocks", {}).get("fraud_compliance", {})
        if gate_fraud == OUTCOME_SKIP and fraud_block:
            r = (fraud_block.get("result", "") or "").lower()
            if r == "passed":
                gate_fraud = OUTCOME_PASS
            elif r in ("failed", "blocked"):
                gate_fraud = OUTCOME_BLOCK

        # ── Jurisdiction ───────────────────────────────────────────────────────
        gate_jurisdiction = _scan_gate_results(gate_results, ("jurisdiction", "cp-11", "juris"))
        if gate_jurisdiction == OUTCOME_SKIP:
            gate_jurisdiction = _scan_trace(
                decision_trace,
                pass_keywords=("CP-11 JURISDICTION_PASS", "JURISDICTION_PASS"),
                block_keywords=("CP-11 JURISDICTION_VETO", "JURISDICTION_VETO", "JURISDICTION_BLOCKED"),
            )
        juris_block = result.get("compliance_blocks", {}).get("jurisdiction_compliance", {})
        if gate_jurisdiction == OUTCOME_SKIP and juris_block:
            r = (juris_block.get("result", "") or "").lower()
            if r == "passed":
                gate_jurisdiction = OUTCOME_PASS
            elif r in ("failed", "blocked"):
                gate_jurisdiction = OUTCOME_BLOCK

        # ── DCI score ──────────────────────────────────────────────────────────
        # logic_consistency signal is the source of DCI in the evaluation engine.
        # DCI = 100 - logic_consistency (high contradiction = low consistency).
        raw_lc = scores.get("logic_consistency")
        if raw_lc is not None:
            try:
                dci_score = round(max(0.0, min(100.0, 100.0 - float(raw_lc))), 2)
            except (TypeError, ValueError):
                dci_score = None
        else:
            dci_score = None

        # ── Coherence score ────────────────────────────────────────────────────
        raw_coh = scores.get("signal_coherence")
        if raw_coh is None:
            raw_coh = scores.get("temporal_coherence")
        try:
            coherence_score = round(float(raw_coh), 2) if raw_coh is not None else None
        except (TypeError, ValueError):
            coherence_score = None

        # ── Black Swan level ───────────────────────────────────────────────────
        black_swan_level = _extract_black_swan_level(decision_trace, gate_results, scores)

        # ── ADR-119 escalation ─────────────────────────────────────────────────
        escalation_triggered = any(
            "BS_HIGH_COHERENCE_ESCALATION" in (t or "").upper()
            for t in decision_trace
        )

        return FilterCalibrationEvent(
            domain               = domain or "trading",
            asset                = asset,
            client_id            = client_id,
            final_decision       = final_decision,
            processing_time_ms   = processing_time_ms,
            gate_layer0          = gate_layer0,
            gate_cag             = gate_cag,
            gate_coherence       = gate_coherence,
            gate_mc              = gate_mc,
            gate_black_swan      = gate_black_swan,
            gate_ecw             = gate_ecw,
            gate_sharia          = gate_sharia,
            gate_aml             = gate_aml,
            gate_fraud           = gate_fraud,
            gate_jurisdiction    = gate_jurisdiction,
            dci_score            = dci_score,
            coherence_score      = coherence_score,
            black_swan_level     = black_swan_level,
            escalation_triggered = escalation_triggered,
        )

    except Exception as exc:
        logger.error("[FCM] extract_event_from_result failed (returning empty event): %s", exc)
        return FilterCalibrationEvent(
            domain         = domain or "trading",
            asset          = asset,
            final_decision = (result.get("decision", "BLOCKED") or "BLOCKED").upper(),
        )


def _extract_black_swan_level(
    decision_trace: List[str],
    gate_results:   List[Dict],
    scores:         Dict[str, Any],
) -> Optional[str]:
    """Extract black swan risk level from any available source."""
    # 1. Try scores dict
    for key in ("black_swan", "black_swan_risk", "bs_level", "bs_risk"):
        v = scores.get(key)
        if v is not None:
            s = str(v).upper()
            if s in (BS_HIGH, BS_LOW, BS_NONE):
                return s

    # 2. Try gate_results
    for gr in gate_results:
        sig = (gr.get("signal", "") or "").lower()
        if "black_swan" in sig or "bs_" in sig:
            score = gr.get("score")
            if score is not None:
                try:
                    f = float(score)
                    if f >= 70:
                        return BS_HIGH
                    elif f >= 30:
                        return BS_LOW
                    else:
                        return BS_NONE
                except (TypeError, ValueError):
                    pass

    # 3. Try decision_trace patterns
    for t in decision_trace:
        u = (t or "").upper()
        if "BS HIGH" in u or "BLACK_SWAN HIGH" in u or "BS_HIGH" in u:
            return BS_HIGH
        if "BS LOW" in u or "BLACK_SWAN LOW" in u or "BS_LOW" in u:
            return BS_LOW
        if "BS NONE" in u or "BLACK_SWAN NONE" in u or "BS_NONE" in u:
            return BS_NONE

    return None


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _get_db_conn(db_url: str):
    import psycopg
    return psycopg.connect(db_url, connect_timeout=10)


def _window_clause(window: str) -> str:
    """Return a WHERE clause fragment for the given time window."""
    interval = _WINDOW_INTERVALS.get(window, "1 day")
    return f"event_ts >= NOW() - INTERVAL '{interval}'"


# ── Schema ─────────────────────────────────────────────────────────────────────

_CREATE_TABLE = f"""
CREATE TABLE IF NOT EXISTS {_TABLE} (
    id                   BIGSERIAL    PRIMARY KEY,
    event_ts             TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    domain               VARCHAR(50)  NOT NULL DEFAULT 'trading',
    asset                VARCHAR(100),
    client_id            VARCHAR(100),
    final_decision       VARCHAR(20)  NOT NULL DEFAULT 'BLOCKED',
    processing_time_ms   INTEGER,

    -- Gate outcomes: 0=PASS, 1=BLOCK, 2=HOLD, -1=SKIP
    gate_layer0          SMALLINT     NOT NULL DEFAULT -1,
    gate_cag             SMALLINT     NOT NULL DEFAULT -1,
    gate_coherence       SMALLINT     NOT NULL DEFAULT -1,
    gate_mc              SMALLINT     NOT NULL DEFAULT -1,
    gate_black_swan      SMALLINT     NOT NULL DEFAULT -1,
    gate_ecw             SMALLINT     NOT NULL DEFAULT -1,
    gate_sharia          SMALLINT     NOT NULL DEFAULT -1,
    gate_aml             SMALLINT     NOT NULL DEFAULT -1,
    gate_fraud           SMALLINT     NOT NULL DEFAULT -1,
    gate_jurisdiction    SMALLINT     NOT NULL DEFAULT -1,

    -- Decision metrics
    dci_score            FLOAT,
    coherence_score      FLOAT,
    black_swan_level     VARCHAR(10),
    escalation_triggered BOOLEAN      NOT NULL DEFAULT FALSE
)
"""

_CREATE_INDEXES = [
    f"CREATE INDEX IF NOT EXISTS idx_fcal_domain_ts   ON {_TABLE}(domain, event_ts DESC)",
    f"CREATE INDEX IF NOT EXISTS idx_fcal_ts           ON {_TABLE}(event_ts DESC)",
    f"CREATE INDEX IF NOT EXISTS idx_fcal_decision     ON {_TABLE}(final_decision, event_ts DESC)",
    f"CREATE INDEX IF NOT EXISTS idx_fcal_bs_level     ON {_TABLE}(black_swan_level, event_ts DESC)",
    f"CREATE INDEX IF NOT EXISTS idx_fcal_escalation   ON {_TABLE}(escalation_triggered, event_ts DESC)",
]


# ── Main service ───────────────────────────────────────────────────────────────

class FilterCalibrationMetricsService:
    """
    Zero-latency governance metrics collector.

    record() enqueues to an in-memory buffer and returns immediately.
    A background flush thread (or explicit flush() calls) drains the queue
    to PostgreSQL in batches.

    Thread-safe: record() and flush() can be called from any thread.
    """

    def __init__(
        self,
        db_url:          Optional[str] = None,
        flush_interval_s: float        = 30.0,
        max_queue_size:   int          = 2000,
    ):
        self.db_url          = db_url or os.environ.get("OMNIX_DB_URL") or os.environ.get("DATABASE_URL")
        self.flush_interval_s = flush_interval_s
        self._queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self._schema_ok          = False
        self._flush_lock         = threading.Lock()

    # ── Schema ─────────────────────────────────────────────────────────────────

    def ensure_schema(self, conn=None) -> bool:
        """Create table and indexes if they don't exist. Safe to call multiple times."""
        own_conn = conn is None
        if own_conn:
            if not self.db_url:
                logger.warning("[FCM] No DB URL — schema not created")
                return False
            try:
                conn = _get_db_conn(self.db_url)
            except Exception as exc:
                logger.error("[FCM] DB connection failed for schema: %s", exc)
                return False
        try:
            cur = conn.cursor()
            cur.execute(_CREATE_TABLE)
            for idx_sql in _CREATE_INDEXES:
                cur.execute(idx_sql)
            conn.commit()
            cur.close()
            self._schema_ok = True
            logger.info("[FCM] Schema OK — table=%s", _TABLE)
            return True
        except Exception as exc:
            logger.error("[FCM] Schema creation error: %s", exc)
            try:
                conn.rollback()
            except Exception:
                pass
            return False
        finally:
            if own_conn:
                try:
                    conn.close()
                except Exception:
                    pass

    # ── Write path ─────────────────────────────────────────────────────────────

    def record(self, event: FilterCalibrationEvent) -> None:
        """
        Enqueue a calibration event for async DB write.

        Returns immediately — never blocks the calling thread.
        If the queue is full, the event is dropped with a WARNING log.
        """
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            logger.warning(
                "[FCM] Queue full (%d items) — dropping event domain=%s decision=%s",
                self._queue.maxsize, event.domain, event.final_decision,
            )

    def flush(self, conn=None) -> int:
        """
        Drain the in-memory queue and write all pending events to the DB.

        Returns the number of events written.
        Thread-safe: concurrent flush() calls are serialized internally.
        """
        if self._queue.empty():
            return 0

        events: List[FilterCalibrationEvent] = []
        try:
            while True:
                events.append(self._queue.get_nowait())
        except queue.Empty:
            pass

        if not events:
            return 0

        with self._flush_lock:
            return self._write_batch(events, conn)

    def _write_batch(self, events: List[FilterCalibrationEvent], conn=None) -> int:
        own_conn = conn is None
        if own_conn:
            if not self.db_url:
                logger.warning("[FCM] No DB URL — %d events discarded", len(events))
                return 0
            try:
                conn = _get_db_conn(self.db_url)
            except Exception as exc:
                logger.error("[FCM] DB connection failed for flush: %s", exc)
                return 0

        written = 0
        try:
            cur = conn.cursor()
            for ev in events:
                try:
                    ts_clause = "" if ev.event_ts is None else "event_ts,"
                    ts_value  = () if ev.event_ts is None else (ev.event_ts,)
                    if ev.event_ts:
                        cur.execute(
                            f"""
                            INSERT INTO {_TABLE}
                                (event_ts, domain, asset, client_id, final_decision,
                                 processing_time_ms,
                                 gate_layer0, gate_cag, gate_coherence, gate_mc,
                                 gate_black_swan, gate_ecw, gate_sharia, gate_aml,
                                 gate_fraud, gate_jurisdiction,
                                 dci_score, coherence_score,
                                 black_swan_level, escalation_triggered)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            """,
                            (
                                ev.event_ts,
                                ev.domain, ev.asset, ev.client_id, ev.final_decision,
                                ev.processing_time_ms,
                                ev.gate_layer0, ev.gate_cag, ev.gate_coherence, ev.gate_mc,
                                ev.gate_black_swan, ev.gate_ecw, ev.gate_sharia, ev.gate_aml,
                                ev.gate_fraud, ev.gate_jurisdiction,
                                ev.dci_score, ev.coherence_score,
                                ev.black_swan_level, ev.escalation_triggered,
                            ),
                        )
                    else:
                        cur.execute(
                            f"""
                            INSERT INTO {_TABLE}
                                (domain, asset, client_id, final_decision,
                                 processing_time_ms,
                                 gate_layer0, gate_cag, gate_coherence, gate_mc,
                                 gate_black_swan, gate_ecw, gate_sharia, gate_aml,
                                 gate_fraud, gate_jurisdiction,
                                 dci_score, coherence_score,
                                 black_swan_level, escalation_triggered)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            """,
                            (
                                ev.domain, ev.asset, ev.client_id, ev.final_decision,
                                ev.processing_time_ms,
                                ev.gate_layer0, ev.gate_cag, ev.gate_coherence, ev.gate_mc,
                                ev.gate_black_swan, ev.gate_ecw, ev.gate_sharia, ev.gate_aml,
                                ev.gate_fraud, ev.gate_jurisdiction,
                                ev.dci_score, ev.coherence_score,
                                ev.black_swan_level, ev.escalation_triggered,
                            ),
                        )
                    written += 1
                except Exception as row_exc:
                    logger.error("[FCM] Row write error: %s", row_exc)
                    try:
                        conn.rollback()
                    except Exception:
                        pass
            conn.commit()
            cur.close()
            if written:
                logger.debug("[FCM] Flushed %d events to %s", written, _TABLE)
        except Exception as exc:
            logger.error("[FCM] Batch write error: %s", exc)
            try:
                conn.rollback()
            except Exception:
                pass
        finally:
            if own_conn:
                try:
                    conn.close()
                except Exception:
                    pass
        return written

    # ── Query interface ────────────────────────────────────────────────────────

    def query_gate_stats(
        self,
        gate:    str,
        *,
        domain:  Optional[str] = None,
        window:  str           = "1d",
        conn     = None,
    ) -> Dict[str, Any]:
        """
        Return pass/block/hold/skip rates for a single gate over a time window.

        Parameters
        ──────────
        gate   : one of GATES ("coherence", "mc", "aml", etc.)
        domain : filter by domain, or None for all domains
        window : "1h" | "1d" | "1w"

        Returns
        ───────
        {
            "gate":       str,
            "window":     str,
            "domain":     str | None,
            "total":      int,
            "pass_count":  int, "pass_rate":  float,
            "block_count": int, "block_rate": float,
            "hold_count":  int, "hold_rate":  float,
            "skip_count":  int,
        }
        """
        if gate not in GATES:
            raise ValueError(f"Unknown gate '{gate}'. Valid: {GATES}")

        col = f"gate_{gate}"
        domain_filter = "AND domain = %s" if domain else ""
        params: Tuple = (domain,) if domain else ()

        sql = f"""
            SELECT
                COUNT(*) FILTER (WHERE {col} = {OUTCOME_PASS})  AS pass_count,
                COUNT(*) FILTER (WHERE {col} = {OUTCOME_BLOCK}) AS block_count,
                COUNT(*) FILTER (WHERE {col} = {OUTCOME_HOLD})  AS hold_count,
                COUNT(*) FILTER (WHERE {col} = {OUTCOME_SKIP})  AS skip_count,
                COUNT(*)                                          AS total
            FROM {_TABLE}
            WHERE {_window_clause(window)} {domain_filter}
              AND {col} >= -1
        """

        own_conn, conn = self._maybe_connect(conn)
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()
            cur.close()
        finally:
            if own_conn:
                try:
                    conn.close()
                except Exception:
                    pass

        pass_count  = int(row[0] or 0)
        block_count = int(row[1] or 0)
        hold_count  = int(row[2] or 0)
        skip_count  = int(row[3] or 0)
        total       = int(row[4] or 0)
        eligible    = total - skip_count

        def rate(n: int) -> float:
            return round(n / eligible, 4) if eligible > 0 else 0.0

        return {
            "gate":        gate,
            "window":      window,
            "domain":      domain,
            "total":       total,
            "eligible":    eligible,
            "pass_count":  pass_count,  "pass_rate":  rate(pass_count),
            "block_count": block_count, "block_rate": rate(block_count),
            "hold_count":  hold_count,  "hold_rate":  rate(hold_count),
            "skip_count":  skip_count,
        }

    def query_all_gate_stats(
        self,
        *,
        domain: Optional[str] = None,
        window: str           = "1d",
        conn    = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Return gate stats for all gates in a single DB roundtrip.

        Returns dict keyed by gate name → same structure as query_gate_stats().
        """
        cols = " ".join(
            f"""
            COUNT(*) FILTER (WHERE gate_{g} = {OUTCOME_PASS})  AS {g}_pass,
            COUNT(*) FILTER (WHERE gate_{g} = {OUTCOME_BLOCK}) AS {g}_block,
            COUNT(*) FILTER (WHERE gate_{g} = {OUTCOME_HOLD})  AS {g}_hold,
            COUNT(*) FILTER (WHERE gate_{g} = {OUTCOME_SKIP})  AS {g}_skip,
            """
            for g in GATES
        )
        total_col = "COUNT(*) AS total"
        domain_filter = "AND domain = %s" if domain else ""
        params: Tuple = (domain,) if domain else ()

        sql = f"""
            SELECT {cols} {total_col}
            FROM {_TABLE}
            WHERE {_window_clause(window)} {domain_filter}
        """

        own_conn, conn = self._maybe_connect(conn)
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()
            cur.close()
        finally:
            if own_conn:
                try:
                    conn.close()
                except Exception:
                    pass

        if row is None:
            row = [0] * (len(GATES) * 4 + 1)

        results: Dict[str, Dict[str, Any]] = {}
        idx = 0
        total = int(row[-1] or 0)
        for g in GATES:
            pass_count  = int(row[idx]     or 0)
            block_count = int(row[idx + 1] or 0)
            hold_count  = int(row[idx + 2] or 0)
            skip_count  = int(row[idx + 3] or 0)
            idx += 4
            eligible = total - skip_count

            def rate(n: int, e: int = eligible) -> float:
                return round(n / e, 4) if e > 0 else 0.0

            results[g] = {
                "gate":        g,
                "window":      window,
                "domain":      domain,
                "total":       total,
                "eligible":    eligible,
                "pass_count":  pass_count,  "pass_rate":  rate(pass_count),
                "block_count": block_count, "block_rate": rate(block_count),
                "hold_count":  hold_count,  "hold_rate":  rate(hold_count),
                "skip_count":  skip_count,
            }

        return results

    def query_dci_distribution(
        self,
        *,
        domain: Optional[str] = None,
        window: str           = "1d",
        conn    = None,
    ) -> Dict[str, Any]:
        """
        DCI (Decision Contradiction Index) distribution and statistics.

        DCI bands (ADR-018):
            ALIGNED       0 – 34
            TENSIONED    35 – 69
            CONTRADICTORY 70 – 100

        Returns
        ───────
        {
            "window":  str,
            "domain":  str | None,
            "total_with_dci": int,
            "avg":  float, "min": float, "max": float, "p50": float, "p90": float,
            "aligned_count":       int, "aligned_rate":       float,
            "tensioned_count":     int, "tensioned_rate":     float,
            "contradictory_count": int, "contradictory_rate": float,
        }
        """
        domain_filter = "AND domain = %s" if domain else ""
        params: Tuple = (domain,) if domain else ()

        sql = f"""
            SELECT
                COUNT(dci_score)                                               AS total_with_dci,
                AVG(dci_score)                                                 AS avg_dci,
                MIN(dci_score)                                                 AS min_dci,
                MAX(dci_score)                                                 AS max_dci,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY dci_score)        AS p50,
                PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY dci_score)        AS p90,
                COUNT(*) FILTER (WHERE dci_score < 35)                        AS aligned_count,
                COUNT(*) FILTER (WHERE dci_score >= 35 AND dci_score < 70)    AS tensioned_count,
                COUNT(*) FILTER (WHERE dci_score >= 70)                       AS contradictory_count
            FROM {_TABLE}
            WHERE {_window_clause(window)} {domain_filter}
              AND dci_score IS NOT NULL
        """

        own_conn, conn = self._maybe_connect(conn)
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()
            cur.close()
        finally:
            if own_conn:
                try:
                    conn.close()
                except Exception:
                    pass

        if row is None:
            row = [0] * 9

        total     = int(row[0] or 0)
        aligned   = int(row[6] or 0)
        tensioned = int(row[7] or 0)
        contra    = int(row[8] or 0)

        def rate(n: int) -> float:
            return round(n / total, 4) if total > 0 else 0.0

        return {
            "window":              window,
            "domain":              domain,
            "total_with_dci":      total,
            "avg":                 round(float(row[1]), 2) if row[1] is not None else None,
            "min":                 round(float(row[2]), 2) if row[2] is not None else None,
            "max":                 round(float(row[3]), 2) if row[3] is not None else None,
            "p50":                 round(float(row[4]), 2) if row[4] is not None else None,
            "p90":                 round(float(row[5]), 2) if row[5] is not None else None,
            "aligned_count":       aligned,       "aligned_rate":       rate(aligned),
            "tensioned_count":     tensioned,     "tensioned_rate":     rate(tensioned),
            "contradictory_count": contra,        "contradictory_rate": rate(contra),
        }

    def query_black_swan_frequency(
        self,
        *,
        domain: Optional[str] = None,
        window: str           = "1d",
        conn    = None,
    ) -> Dict[str, Any]:
        """
        Black Swan event frequency over the given window.

        Returns
        ───────
        {
            "window":   str,
            "domain":   str | None,
            "total":    int,
            "none_count": int, "none_rate": float,
            "low_count":  int, "low_rate":  float,
            "high_count": int, "high_rate": float,
            "unknown_count": int,
        }
        """
        domain_filter = "AND domain = %s" if domain else ""
        params: Tuple = (domain,) if domain else ()

        sql = f"""
            SELECT
                COUNT(*)                                                    AS total,
                COUNT(*) FILTER (WHERE black_swan_level = 'NONE')          AS none_count,
                COUNT(*) FILTER (WHERE black_swan_level = 'LOW')           AS low_count,
                COUNT(*) FILTER (WHERE black_swan_level = 'HIGH')          AS high_count,
                COUNT(*) FILTER (WHERE black_swan_level IS NULL)           AS unknown_count
            FROM {_TABLE}
            WHERE {_window_clause(window)} {domain_filter}
        """

        own_conn, conn = self._maybe_connect(conn)
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()
            cur.close()
        finally:
            if own_conn:
                try:
                    conn.close()
                except Exception:
                    pass

        if row is None:
            row = [0] * 5

        total   = int(row[0] or 0)
        none_c  = int(row[1] or 0)
        low_c   = int(row[2] or 0)
        high_c  = int(row[3] or 0)
        unk_c   = int(row[4] or 0)

        def rate(n: int) -> float:
            return round(n / total, 4) if total > 0 else 0.0

        return {
            "window":        window,
            "domain":        domain,
            "total":         total,
            "none_count":    none_c,  "none_rate":  rate(none_c),
            "low_count":     low_c,   "low_rate":   rate(low_c),
            "high_count":    high_c,  "high_rate":  rate(high_c),
            "unknown_count": unk_c,
        }

    def query_escalation_events(
        self,
        *,
        domain: Optional[str] = None,
        window: str           = "1d",
        conn    = None,
    ) -> Dict[str, Any]:
        """
        ADR-119 escalation event frequency.

        An escalation occurs when Black Swan = HIGH forces the coherence
        gate threshold to be raised (BS_HIGH_COHERENCE_ESCALATION trace).

        Returns
        ───────
        {
            "window":             str,
            "domain":             str | None,
            "total":              int,
            "escalation_count":   int,
            "escalation_rate":    float,
            "escalation_blocked": int,   # escalation events that led to BLOCKED
            "escalation_approved": int,  # escalation events where decision was still APPROVED
        }
        """
        domain_filter = "AND domain = %s" if domain else ""
        params: Tuple = (domain,) if domain else ()

        sql = f"""
            SELECT
                COUNT(*)                                                                         AS total,
                COUNT(*) FILTER (WHERE escalation_triggered = TRUE)                              AS escalation_count,
                COUNT(*) FILTER (WHERE escalation_triggered = TRUE
                                   AND final_decision IN ('BLOCKED', 'BLOCK'))                   AS escalation_blocked,
                COUNT(*) FILTER (WHERE escalation_triggered = TRUE
                                   AND final_decision = 'APPROVED')                              AS escalation_approved
            FROM {_TABLE}
            WHERE {_window_clause(window)} {domain_filter}
        """

        own_conn, conn = self._maybe_connect(conn)
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            row = cur.fetchone()
            cur.close()
        finally:
            if own_conn:
                try:
                    conn.close()
                except Exception:
                    pass

        if row is None:
            row = [0, 0, 0, 0]

        total    = int(row[0] or 0)
        esc_c    = int(row[1] or 0)
        esc_blk  = int(row[2] or 0)
        esc_app  = int(row[3] or 0)

        return {
            "window":              window,
            "domain":              domain,
            "total":               total,
            "escalation_count":    esc_c,
            "escalation_rate":     round(esc_c / total, 4) if total > 0 else 0.0,
            "escalation_blocked":  esc_blk,
            "escalation_approved": esc_app,
        }

    def query_summary(
        self,
        *,
        domain: Optional[str] = None,
        window: str           = "1d",
        conn    = None,
    ) -> Dict[str, Any]:
        """
        Full calibration summary in a single call.

        Returns all gate stats, DCI distribution, Black Swan frequency,
        and escalation events — sharing a single DB connection.
        """
        own_conn, conn = self._maybe_connect(conn)
        try:
            gate_stats  = self.query_all_gate_stats(domain=domain, window=window, conn=conn)
            dci         = self.query_dci_distribution(domain=domain, window=window, conn=conn)
            bs          = self.query_black_swan_frequency(domain=domain, window=window, conn=conn)
            escalation  = self.query_escalation_events(domain=domain, window=window, conn=conn)
            queue_depth = self._queue.qsize()
        finally:
            if own_conn:
                try:
                    conn.close()
                except Exception:
                    pass

        return {
            "window":         window,
            "domain":         domain,
            "queue_depth":    queue_depth,
            "gate_stats":     gate_stats,
            "dci":            dci,
            "black_swan":     bs,
            "escalation":     escalation,
            "generated_at":   datetime.now(timezone.utc).isoformat(),
        }

    def pending_count(self) -> int:
        """Number of events waiting in the in-memory buffer."""
        return self._queue.qsize()

    # ── Internal ───────────────────────────────────────────────────────────────

    def _maybe_connect(self, conn):
        """Return (own_conn, conn). If conn is provided, reuse it."""
        if conn is not None:
            return False, conn
        if not self.db_url:
            raise RuntimeError("[FCM] No DB URL configured")
        return True, _get_db_conn(self.db_url)


# ── Background flush daemon ────────────────────────────────────────────────────

class FilterCalibrationDaemon:
    """
    Background thread that periodically flushes the in-memory event queue
    to PostgreSQL.

    Typical usage (called once at server startup):

        daemon = FilterCalibrationDaemon(svc)
        daemon.start()
    """

    def __init__(
        self,
        svc:              FilterCalibrationMetricsService,
        flush_interval_s: float = 30.0,
        warmup_s:         float = 15.0,
    ):
        self._svc             = svc
        self._flush_interval  = flush_interval_s
        self._warmup          = warmup_s
        self._thread: Optional[threading.Thread] = None
        self._stop_event      = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="FilterCalibrationFlush",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            "[FCM] Daemon started — warmup=%.0fs flush_interval=%.0fs",
            self._warmup, self._flush_interval,
        )

    def stop(self) -> None:
        self._stop_event.set()

    def _run(self) -> None:
        time.sleep(self._warmup)
        while not self._stop_event.is_set():
            try:
                written = self._svc.flush()
                if written:
                    logger.debug("[FCM] Daemon flushed %d events", written)
            except Exception as exc:
                logger.error("[FCM] Daemon flush error: %s", exc)
            self._stop_event.wait(timeout=self._flush_interval)
        # Final flush on shutdown
        try:
            self._svc.flush()
        except Exception:
            pass


# ── Module-level singleton (used by proof_layer.py integration) ───────────────

_svc_lock   = threading.Lock()
_global_svc: Optional[FilterCalibrationMetricsService] = None
_global_daemon: Optional[FilterCalibrationDaemon] = None


def get_global_service() -> FilterCalibrationMetricsService:
    """
    Return (or create) the module-level singleton service.
    The daemon is started automatically on first access.
    """
    global _global_svc, _global_daemon
    if _global_svc is not None:
        return _global_svc
    with _svc_lock:
        if _global_svc is not None:
            return _global_svc
        svc    = FilterCalibrationMetricsService()
        daemon = FilterCalibrationDaemon(svc)
        try:
            svc.ensure_schema()
        except Exception as exc:
            logger.warning("[FCM] Schema init deferred (no DB yet): %s", exc)
        daemon.start()
        _global_svc    = svc
        _global_daemon = daemon
        return _global_svc
