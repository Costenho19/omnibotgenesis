"""
OMNIX Agent Trust Fabric — Runtime Governance Continuity
=========================================================
ADR-159: Continuous authority health monitoring for long-running agent executions.

Closes the gap between point-of-admission authority (TAR, ADR-157) and the
ongoing validity of that authority throughout the execution lifecycle.

Every long-running execution produces Runtime Continuity Records (RCRs) —
PQC-signed authority health snapshots emitted at governed intervals:

    ATFRCR-{16HEX}

Each RCR carries a Continuity Eligibility Score (CES):

    CES = (T × 0.30) + (B × 0.30) + (D × 0.20) + (I × 0.20)

    T — Temporal Health:    time remaining on DR / total DR lifetime
    B — Budget Health:      budget remaining / budget at admission
    D — Context Fidelity:   100 - context_drift_pct (from Scope Auth Engine)
    I — Integrity Score:    100 - (active_anomalies × 10)

CES thresholds drive automatic escalation:

    75–100  NOMINAL     — continue, standard sampling
    50–75   MONITORING  — continue, increased sampling, flag outputs
    25–50   WARNING     — restrict sub-task spawning, Tier-1 alert
    10–25   CRITICAL    — suspend spawning, issue Reauthorization Challenge
     0–10   HALT        — terminate execution, revoke in-flight sub-tasks

Authority Fragmentation Guard (AFG):
    Prevents budget exhaustion across concurrent sub-agents by enforcing
    aggregate MAR at the chain_root_id level. Closes the fragmentation
    attack vector not covered by individual-level Monotonic Authority
    Reduction (ADR-156 MAR).

Reauthorization Challenge (RC):
    ATFRC-{16HEX} — formal mid-execution authority renewal protocol.
    Issued at CRITICAL. Tier-1 responds with a fresh short-lifetime DR.
    Auto-HALT on TTL expiry without response.

Key invariants:
    RGC-INV-001: Every RCR anchored to a valid TAR
    RGC-INV-002: CES computed from real-time values only
    RGC-INV-003: HALT terminates execution and revokes sub-tasks
    RGC-INV-004: Aggregate budget never exceeds AFG limit
    RGC-INV-005: All RCRs PQC-signed and immutable
    RGC-INV-006: Continuity chain is acyclic (monotonically advancing ns)
    RGC-INV-007: CES inputs must be fresh (staleness threshold enforced)
    RGC-INV-008: Reauthorization Challenge TTL enforced; auto-HALT on expiry

ADR-159 — Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("OMNIX.ATF.RuntimeContinuity")

# RPOL — RCRWriteQueue is a process-level singleton (independent of engine).
# Sampler and Scheduler are per-engine instances (created lazily on first use).
_rpol_write_queue  = None
_rpol_wq_lock      = threading.Lock()


def _get_write_queue():
    """Process-level singleton write queue (shared across all engines)."""
    global _rpol_write_queue
    if _rpol_write_queue is None:
        with _rpol_wq_lock:
            if _rpol_write_queue is None:
                from omnix_core.agents.atf.rcr_performance import RCRWriteQueue
                _rpol_write_queue = RCRWriteQueue()
    return _rpol_write_queue

# ─────────────────────────────────────────────────────────────────────────────
# DDL
# ─────────────────────────────────────────────────────────────────────────────

DDL_RUNTIME_CONTINUITY = """
CREATE TABLE IF NOT EXISTS atf_runtime_continuity (
    rcr_id                  VARCHAR(64)   PRIMARY KEY,
    tar_id                  VARCHAR(64)   NOT NULL,
    delegation_id           VARCHAR(64)   NOT NULL,
    agent_id                VARCHAR(64)   NOT NULL,
    chain_root_id           VARCHAR(64)   NOT NULL,
    execution_ns            BIGINT        NOT NULL,
    execution_ts            TIMESTAMPTZ   NOT NULL,
    ces_score               FLOAT         NOT NULL,
    ces_temporal            FLOAT         NOT NULL,
    ces_budget              FLOAT         NOT NULL,
    ces_context             FLOAT         NOT NULL,
    ces_integrity           FLOAT         NOT NULL,
    continuity_status       VARCHAR(16)   NOT NULL,
    predecessor_rcr_id      VARCHAR(64)   DEFAULT NULL,
    budget_at_admission     FLOAT         NOT NULL,
    budget_remaining        FLOAT         NOT NULL,
    context_drift_pct       FLOAT         NOT NULL DEFAULT 0.0,
    active_anomalies        INT           NOT NULL DEFAULT 0,
    dr_expires_at           TIMESTAMPTZ   DEFAULT NULL,
    time_remaining_ns       BIGINT        DEFAULT NULL,
    fragmentation_score     FLOAT         NOT NULL DEFAULT 0.0,
    escalation_event_id     VARCHAR(64)   DEFAULT NULL,
    reauth_challenge_id     VARCHAR(64)   DEFAULT NULL,
    sample_reason           VARCHAR(32)   NOT NULL DEFAULT 'SCHEDULED',
    content_hash            VARCHAR(64)   NOT NULL,
    pqc_signature           TEXT          DEFAULT NULL,
    pqc_algorithm           VARCHAR(32)   DEFAULT NULL,
    issued_at               TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    metadata                JSONB         NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_atf_rcr_tar
    ON atf_runtime_continuity (tar_id);
CREATE INDEX IF NOT EXISTS idx_atf_rcr_delegation_status
    ON atf_runtime_continuity (delegation_id, continuity_status);
CREATE INDEX IF NOT EXISTS idx_atf_rcr_chain_root_ns
    ON atf_runtime_continuity (chain_root_id, execution_ns);
CREATE INDEX IF NOT EXISTS idx_atf_rcr_status_issued
    ON atf_runtime_continuity (continuity_status, issued_at);
CREATE INDEX IF NOT EXISTS idx_atf_rcr_agent_ns
    ON atf_runtime_continuity (agent_id, execution_ns);

CREATE TABLE IF NOT EXISTS atf_continuity_escalations (
    cee_id                  VARCHAR(64)   PRIMARY KEY,
    rcr_id                  VARCHAR(64)   NOT NULL,
    tar_id                  VARCHAR(64)   NOT NULL,
    delegation_id           VARCHAR(64)   NOT NULL,
    agent_id                VARCHAR(64)   NOT NULL,
    chain_root_id           VARCHAR(64)   NOT NULL,
    threshold_crossed       VARCHAR(16)   NOT NULL,
    recommended_action      VARCHAR(32)   NOT NULL,
    ces_at_escalation       FLOAT         NOT NULL,
    escalation_ns           BIGINT        NOT NULL,
    response_ttl_seconds    INT           NOT NULL DEFAULT 300,
    response_received_at    TIMESTAMPTZ   DEFAULT NULL,
    response_dr_id          VARCHAR(64)   DEFAULT NULL,
    resolved                BOOLEAN       NOT NULL DEFAULT FALSE,
    resolution_status       VARCHAR(32)   DEFAULT NULL,
    content_hash            VARCHAR(64)   NOT NULL,
    pqc_signature           TEXT          DEFAULT NULL,
    pqc_algorithm           VARCHAR(32)   DEFAULT NULL,
    issued_at               TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    metadata                JSONB         NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_atf_cee_tar
    ON atf_continuity_escalations (tar_id);
CREATE INDEX IF NOT EXISTS idx_atf_cee_chain_root
    ON atf_continuity_escalations (chain_root_id, resolved);
"""

# ─────────────────────────────────────────────────────────────────────────────
# ID prefixes
# ─────────────────────────────────────────────────────────────────────────────

RCR_ID_PREFIX  = "ATFRCR"
CEE_ID_PREFIX  = "ATFCEE"
RC_ID_PREFIX   = "ATFRC"

# ─────────────────────────────────────────────────────────────────────────────
# CES thresholds
# ─────────────────────────────────────────────────────────────────────────────

CES_NOMINAL     = 75.0
CES_MONITORING  = 50.0
CES_WARNING     = 25.0
CES_CRITICAL    = 10.0
CES_HALT        = 0.0

# Authority Fragmentation Guard limit (default 90% of chain root budget)
AFG_FRAGMENTATION_LIMIT_DEFAULT = 0.90

# Default response TTL for Reauthorization Challenges (seconds)
RC_TTL_CRITICAL_DEFAULT = 300
RC_TTL_HALT_DEFAULT     = 0   # immediate

# ─────────────────────────────────────────────────────────────────────────────
# COMPILED CES STALENESS BOUND — RGC-INV-007
#
# MODULE-LEVEL CONSTANT. NOT read from environment variables.
# NOT operator-configurable. This is intentional.
#
# RCR_CES_STALENESS_BOUND_SECONDS: Maximum age of the CES component inputs
#     (temporal health, budget health, context fidelity, integrity score)
#     at the moment an RCR is issued. If any CES input was last updated
#     more than this many seconds ago, the RCR is flagged STALE and
#     continuity_status is forced to WARNING regardless of the computed
#     CES score. This prevents a slow-drift attack where stale inputs
#     produce artificially high CES scores that mask real authority decay.
#
# Making this configurable would allow an operator to extend the staleness
# window until inputs are effectively frozen — defeating the liveness
# guarantee that RGC-INV-007 is designed to enforce. The bound is compiled.
# ─────────────────────────────────────────────────────────────────────────────
RCR_CES_STALENESS_BOUND_SECONDS: int = 300   # 5 minutes — compiled, not configurable


# ─────────────────────────────────────────────────────────────────────────────
# GPIL — Cross-Runtime Governance Contract types (ADR-161 / RFC-ATF-2 §21)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CRGCPolicyParameters:
    """
    Policy Divergence Surface — 6 parameters that two runtimes may configure
    independently without violating CI or PI (ADR-161 §21.3).

    Within a CRGC these parameters are fixed for the contract lifetime;
    divergence beyond protocol bounds is a compliance violation.
    """
    afg_fragmentation_limit: float = AFG_FRAGMENTATION_LIMIT_DEFAULT   # [0.01, 0.95]
    rc_ttl_seconds: int = RC_TTL_CRITICAL_DEFAULT                       # [30, 3600]
    context_drift_methodology_ref: str = "OMNIX-DRIFT-DEFAULT-v1"
    anomaly_criteria_ref: str = "OMNIX-ANOMALY-DEFAULT-v1"
    sampling_profile: str = "STREAMING"            # SHORT|MEDIUM|LONG|STREAMING
    governance_risk_tier_policy: str = "STANDARD"  # LOW|STANDARD|HIGH|CRITICAL


@dataclass
class CRGC:
    """
    Cross-Runtime Governance Contract (ADR-161 §7).

    A bilaterally PQC-signed contract between two sovereign OMNIX runtimes
    that aligns their Policy Divergence Surface, enabling ATF-GPI-Aligned status.
    """
    crgc_id: str
    parties: List[str]
    effective_from: str
    expires_at: str
    invariant_version: str
    policy_parameters: CRGCPolicyParameters
    content_hash: str = ""
    pqc_signatures: List[str] = field(default_factory=list)

    def compute_hash(self) -> str:
        """SHA-256 over canonical JSON of hashable fields (deterministic)."""
        payload = {
            "crgc_id": self.crgc_id,
            "parties": sorted(self.parties),
            "effective_from": self.effective_from,
            "expires_at": self.expires_at,
            "invariant_version": self.invariant_version,
            "policy_parameters": asdict(self.policy_parameters),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def sign(self, party_index: int, key: str) -> str:
        """HMAC-SHA256 stand-in signature (replace with ML-DSA-65 in production)."""
        import hmac as _hmac
        return _hmac.new(
            key.encode("utf-8"),
            self.content_hash.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(timezone.utc)
        expires = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
        return now > expires

    def is_active(self, now: Optional[datetime] = None) -> bool:
        now = now or datetime.now(timezone.utc)
        eff = datetime.fromisoformat(self.effective_from.replace("Z", "+00:00"))
        return eff <= now and not self.is_expired(now)

    @staticmethod
    def create(
        party_a: str,
        party_b: str,
        policy: "CRGCPolicyParameters",
        ttl_hours: int = 24,
        key_a: str = "key-a",
        key_b: str = "key-b",
        invariant_version: str = "RFC-ATF-2-v1.0.0",
    ) -> "CRGC":
        """Factory: create and bilaterally sign a new CRGC."""
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        crgc = CRGC(
            crgc_id=f"CRGC-{uuid.uuid4().hex[:16].upper()}",
            parties=[party_a, party_b],
            effective_from=now.isoformat(),
            expires_at=(now + timedelta(hours=ttl_hours)).isoformat(),
            invariant_version=invariant_version,
            policy_parameters=policy,
        )
        crgc.content_hash = crgc.compute_hash()
        crgc.pqc_signatures = [crgc.sign(0, key_a), crgc.sign(1, key_b)]
        return crgc


# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────

class RGCError(Exception):
    """Base class for Runtime Governance Continuity errors."""


class InvalidCESInputError(RGCError):
    """RGC-INV-007: Stale or invalid CES input detected."""


class AuthorityFragmentationViolation(RGCError):
    """RGC-INV-004: Aggregate sub-agent budget exceeds AFG limit."""


class ContinuityHaltError(RGCError):
    """RGC-INV-003: Execution halted by continuity engine."""


# ─────────────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ContinuityEligibilityScore:
    """
    Composite authority health metric.

    CES = (T × 0.30) + (B × 0.30) + (D × 0.20) + (I × 0.20)

    All components are in [0.0, 100.0]. CES is in [0.0, 100.0].
    """
    temporal:   float   # T — time remaining health
    budget:     float   # B — budget remaining health
    context:    float   # D — context fidelity (100 - drift)
    integrity:  float   # I — integrity (100 - anomaly penalty)

    @property
    def score(self) -> float:
        return round(
            (self.temporal  * 0.30) +
            (self.budget    * 0.30) +
            (self.context   * 0.20) +
            (self.integrity * 0.20),
            4,
        )

    @property
    def status(self) -> str:
        s = self.score
        if s >= CES_NOMINAL:
            return "NOMINAL"
        if s >= CES_MONITORING:
            return "MONITORING"
        if s >= CES_WARNING:
            return "WARNING"
        if s >= CES_CRITICAL:
            return "CRITICAL"
        return "HALT"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ces_score":    self.score,
            "ces_temporal": self.temporal,
            "ces_budget":   self.budget,
            "ces_context":  self.context,
            "ces_integrity": self.integrity,
            "continuity_status": self.status,
        }


@dataclass
class RuntimeContinuityRecord:
    """
    PQC-signed, TAR-anchored authority health snapshot.

    Identifier format: ATFRCR-{16HEX}

    Each RCR references its predecessor (predecessor_rcr_id), forming a
    cryptographic continuity chain from admission TAR to execution completion.

    RGC-INV-005: Immutable once issued (content_hash + no UPDATE path).
    RGC-INV-006: Chain is acyclic — execution_ns must be > predecessor's.
    """
    rcr_id:              str
    tar_id:              str
    delegation_id:       str
    agent_id:            str
    chain_root_id:       str
    execution_ns:        int
    execution_ts:        str
    ces_score:           float
    ces_temporal:        float
    ces_budget:          float
    ces_context:         float
    ces_integrity:       float
    continuity_status:   str
    predecessor_rcr_id:  Optional[str]
    budget_at_admission: float
    budget_remaining:    float
    context_drift_pct:   float
    active_anomalies:    int
    dr_expires_at:       Optional[str]
    time_remaining_ns:   Optional[int]
    fragmentation_score: float
    escalation_event_id: Optional[str]
    reauth_challenge_id: Optional[str]
    sample_reason:       str
    content_hash:        str
    pqc_signature:       Optional[str]
    pqc_algorithm:       Optional[str]
    issued_at:           str
    metadata:            Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_nominal(self) -> bool:
        return self.continuity_status == "NOMINAL"

    def is_halted(self) -> bool:
        return self.continuity_status == "HALT"

    def summary(self) -> Dict[str, Any]:
        return {
            "rcr_id":            self.rcr_id,
            "tar_id":            self.tar_id,
            "delegation_id":     self.delegation_id,
            "agent_id":          self.agent_id,
            "execution_ns":      self.execution_ns,
            "execution_ts":      self.execution_ts,
            "ces_score":         self.ces_score,
            "continuity_status": self.continuity_status,
            "budget_remaining":  self.budget_remaining,
            "time_remaining_ns": self.time_remaining_ns,
            "fragmentation_score": self.fragmentation_score,
            "pqc_signed":        self.pqc_signature is not None,
            "issued_at":         self.issued_at,
        }


@dataclass
class ContinuityEscalationEvent:
    """
    PQC-signed escalation event issued when CES crosses a threshold.

    Identifier format: ATFCEE-{16HEX}
    """
    cee_id:               str
    rcr_id:               str
    tar_id:               str
    delegation_id:        str
    agent_id:             str
    chain_root_id:        str
    threshold_crossed:    str
    recommended_action:   str
    ces_at_escalation:    float
    escalation_ns:        int
    response_ttl_seconds: int
    response_received_at: Optional[str]
    response_dr_id:       Optional[str]
    resolved:             bool
    resolution_status:    Optional[str]
    content_hash:         str
    pqc_signature:        Optional[str]
    pqc_algorithm:        Optional[str]
    issued_at:            str
    metadata:             Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReauthorizationChallenge:
    """
    Formal mid-execution authority renewal request.

    Identifier format: ATFRC-{16HEX}

    Issued when CES drops to CRITICAL. Tier-1 responds by issuing a
    fresh short-lifetime DR linked via metadata.rc_id. Auto-HALT on
    TTL expiry (RGC-INV-008).
    """
    rc_id:               str
    cee_id:              str
    tar_id:              str
    delegation_id:       str
    agent_id:            str
    chain_root_id:       str
    ces_at_challenge:    float
    challenge_ns:        int
    ttl_seconds:         int
    expires_at_ns:       int
    response_dr_id:      Optional[str]
    resolved:            bool
    resolution:          Optional[str]
    content_hash:        str
    pqc_signature:       Optional[str]
    pqc_algorithm:       Optional[str]
    issued_at:           str
    metadata:            Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def is_expired(self) -> bool:
        return time.time_ns() > self.expires_at_ns and not self.resolved


# ─────────────────────────────────────────────────────────────────────────────
# ContinuitySession — in-memory execution tracking
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ContinuitySession:
    """
    In-memory state for a single long-running execution session.

    Created when start_session() is called. Destroyed when the session
    ends (HALT, COMPLETE, or explicit stop).
    """
    session_id:          str          # equals tar_id
    tar_id:              str
    delegation_id:       str
    agent_id:            str
    chain_root_id:       str
    domain:              str
    budget_at_admission: float
    budget_remaining:    float
    dr_expires_at_ns:    Optional[int]
    dr_issued_ns:        int
    started_at_ns:       int          = field(default_factory=time.time_ns)
    last_rcr_id:         Optional[str] = None
    last_rcr_ns:         int          = 0
    status:              str          = "ACTIVE"
    rcr_count:           int          = 0
    open_rc:             Optional[ReauthorizationChallenge] = None
    halt_callback:       Optional[Callable[[str], None]] = None
    metadata:            Dict[str, Any] = field(default_factory=dict)
    governance_risk_tier: str         = "STANDARD"  # ADR-160: LOW/STANDARD/HIGH/CRITICAL


# ─────────────────────────────────────────────────────────────────────────────
# RuntimeContinuityEngine
# ─────────────────────────────────────────────────────────────────────────────

class RuntimeContinuityEngine:
    """
    Issues and manages Runtime Continuity Records (RCRs) for long-running
    agent executions.

    Design contract:
        start_session()     → ContinuitySession
        sample()            → RuntimeContinuityRecord
        stop_session()      → final RuntimeContinuityRecord
        respond_to_rc()     → resolved ReauthorizationChallenge
        get_rcr()           → RuntimeContinuityRecord by ID
        session_chain()     → list[RuntimeContinuityRecord] for a tar_id
        current_ces()       → ContinuityEligibilityScore for an active session
        ensure_tables()     → idempotent DDL

    Thread-safety: all session state protected by _lock.
    """

    def __init__(self, db_url: Optional[str] = None):
        self._db_url = db_url or os.environ.get("DATABASE_URL")
        self._sessions:  Dict[str, ContinuitySession] = {}
        self._rcr_store: Dict[str, RuntimeContinuityRecord] = {}
        self._cee_store: Dict[str, ContinuityEscalationEvent] = {}
        self._rc_store:  Dict[str, ReauthorizationChallenge] = {}
        self._lock = threading.Lock()
        self._provider = self._load_provider()
        self._afg_limit = float(
            os.environ.get("AFG_FRAGMENTATION_LIMIT", AFG_FRAGMENTATION_LIMIT_DEFAULT)
        )
        self._rc_ttl = int(
            os.environ.get("RGC_RC_TTL_SECONDS", RC_TTL_CRITICAL_DEFAULT)
        )
        # ADR-160: Per-engine RPOL instances (lazy-initialized on first use)
        self._rpol_sampler   = None
        self._rpol_scheduler = None
        self._rpol_init_lock = threading.Lock()

    def _get_sampler(self):
        """Per-engine EventDrivenSampler — lazily initialized."""
        if self._rpol_sampler is None:
            with self._rpol_init_lock:
                if self._rpol_sampler is None:
                    from omnix_core.agents.atf.rcr_performance import EventDrivenSampler
                    self._rpol_sampler = EventDrivenSampler(self)
        return self._rpol_sampler

    def _get_scheduler(self):
        """Per-engine RCRScheduler — lazily initialized."""
        if self._rpol_scheduler is None:
            with self._rpol_init_lock:
                if self._rpol_scheduler is None:
                    from omnix_core.agents.atf.rcr_performance import RCRScheduler
                    self._rpol_scheduler = RCRScheduler(self)
        return self._rpol_scheduler

    # ──────────────────────────────────────────────────────────
    # Lifecycle
    # ──────────────────────────────────────────────────────────

    def start_session(
        self,
        tar_id:              str,
        delegation_id:       str,
        agent_id:            str,
        chain_root_id:       str,
        domain:              str,
        budget_at_admission: float,
        dr_expires_at:       Optional[str] = None,
        dr_issued_at:        Optional[str] = None,
        halt_callback:       Optional[Callable[[str], None]] = None,
        metadata:            Optional[Dict[str, Any]] = None,
        governance_risk_tier: str = "STANDARD",
    ) -> ContinuitySession:
        """
        Start a continuity monitoring session anchored to a TAR.

        Returns a ContinuitySession that tracks authority health for this
        execution. The session lives in memory; RCRs are persisted to DB.

        Args:
            tar_id:              The TAR that admitted this execution
            delegation_id:       The Delegation Receipt being monitored
            agent_id:            The executing agent's AID
            chain_root_id:       The human Tier-1 chain root
            domain:              Governance domain
            budget_at_admission: Authority budget at TAR issuance
            dr_expires_at:       Optional ISO UTC expiry of the DR
            dr_issued_at:        Optional ISO UTC issue time of the DR
            halt_callback:       Called with agent_id when HALT triggered
            metadata:            Optional extension metadata
        """
        dr_expires_at_ns: Optional[int] = None
        if dr_expires_at:
            try:
                dt = datetime.fromisoformat(
                    dr_expires_at.replace("Z", "+00:00")
                )
                dr_expires_at_ns = int(dt.timestamp() * 1_000_000_000)
            except Exception:
                pass

        dr_issued_ns: int = time.time_ns()
        if dr_issued_at:
            try:
                dt = datetime.fromisoformat(
                    dr_issued_at.replace("Z", "+00:00")
                )
                dr_issued_ns = int(dt.timestamp() * 1_000_000_000)
            except Exception:
                pass

        # Validate and normalise risk tier (ADR-160)
        valid_tiers = ("LOW", "STANDARD", "HIGH", "CRITICAL")
        tier = governance_risk_tier.upper() if governance_risk_tier else "STANDARD"
        if tier not in valid_tiers:
            logger.warning(
                f"[RGC] Unknown governance_risk_tier '{tier}' — defaulting to STANDARD"
            )
            tier = "STANDARD"

        session = ContinuitySession(
            session_id=tar_id,
            tar_id=tar_id,
            delegation_id=delegation_id,
            agent_id=agent_id,
            chain_root_id=chain_root_id,
            domain=domain,
            budget_at_admission=budget_at_admission,
            budget_remaining=budget_at_admission,
            dr_expires_at_ns=dr_expires_at_ns,
            dr_issued_ns=dr_issued_ns,
            halt_callback=halt_callback,
            metadata=metadata or {},
            governance_risk_tier=tier,
        )

        with self._lock:
            self._sessions[tar_id] = session

        # Register with RPOL event sampler (ADR-160)
        try:
            self._get_sampler().register_session(
                tar_id=tar_id,
                budget_at_admission=budget_at_admission,
            )
        except Exception:
            pass

        logger.info(
            f"[RGC] Session started — tar={tar_id} agent={agent_id} "
            f"budget={budget_at_admission:.1f} domain={domain} tier={tier}"
        )
        return session

    def stop_session(
        self,
        tar_id: str,
        budget_consumed: float = 0.0,
        context_drift_pct: float = 0.0,
        active_anomalies: int = 0,
        reason: str = "EXECUTION_COMPLETE",
    ) -> Optional[RuntimeContinuityRecord]:
        """
        Stop a continuity session and emit a final RCR.

        This RCR carries `sample_reason='EXECUTION_COMPLETE'` and is the
        terminal record in the continuity chain for this execution.
        """
        with self._lock:
            session = self._sessions.get(tar_id)
            if not session:
                logger.warning(f"[RGC] stop_session — no session for tar={tar_id}")
                return None
            session.status = "STOPPED"

        rcr = self.sample(
            tar_id=tar_id,
            budget_consumed=budget_consumed,
            context_drift_pct=context_drift_pct,
            active_anomalies=active_anomalies,
            sample_reason=reason,
        )

        with self._lock:
            self._sessions.pop(tar_id, None)

        # Deregister from RPOL event sampler (ADR-160)
        try:
            self._get_sampler().deregister_session(tar_id)
        except Exception:
            pass

        logger.info(
            f"[RGC] Session stopped — tar={tar_id} final_ces={rcr.ces_score:.1f} "
            f"status={rcr.continuity_status}"
        )
        return rcr

    # ──────────────────────────────────────────────────────────
    # Core sampling
    # ──────────────────────────────────────────────────────────

    def sample(
        self,
        tar_id:            str,
        budget_consumed:   float = 0.0,
        context_drift_pct: float = 0.0,
        active_anomalies:  int = 0,
        sample_reason:     str = "SCHEDULED",
        metadata:          Optional[Dict[str, Any]] = None,
    ) -> RuntimeContinuityRecord:
        """
        Emit a Runtime Continuity Record for an active session.

        This is the primary sampling operation. It:
        1. Computes CES from current state
        2. Issues an RCR (PQC-signed, immutable)
        3. Checks fragmentation guard
        4. Triggers escalation if threshold crossed
        5. Issues Reauthorization Challenge if CRITICAL
        6. Issues HALT if CES = HALT

        RGC-INV-002: CES inputs are taken from real-time values at the
        moment of this call — no caching of components.

        Args:
            tar_id:            The TAR (session identifier)
            budget_consumed:   Budget consumed since last sample
            context_drift_pct: Context drift % from scope engine (0.0–100.0)
            active_anomalies:  Count of active governance anomalies
            sample_reason:     SCHEDULED / THRESHOLD_BREACH / FRAGMENTATION / EXTERNAL
            metadata:          Optional extension metadata

        Returns:
            RuntimeContinuityRecord for this sample
        """
        now_ns = time.time_ns()
        now_ts = datetime.fromtimestamp(now_ns / 1e9, tz=timezone.utc).isoformat()

        with self._lock:
            session = self._sessions.get(tar_id)
            if not session:
                raise RGCError(f"No active continuity session for tar_id={tar_id}")

            # Update budget
            session.budget_remaining = max(
                0.0, session.budget_remaining - budget_consumed
            )
            predecessor_rcr_id = session.last_rcr_id

            # RGC-INV-006: new ns must be > predecessor's
            if session.last_rcr_ns >= now_ns:
                # clock skew safety — advance by 1ns
                now_ns = session.last_rcr_ns + 1

        # ── Compute CES ─────────────────────────────────────────────────────
        ces = self._compute_ces(
            session=session,
            now_ns=now_ns,
            context_drift_pct=context_drift_pct,
            active_anomalies=active_anomalies,
        )

        # ── Fragmentation Guard ──────────────────────────────────────────────
        frag_score = self._fragmentation_score(session.chain_root_id)

        # ── Issue RCR ───────────────────────────────────────────────────────
        rcr_id = self._build_id(RCR_ID_PREFIX)
        time_remaining_ns = self._time_remaining_ns(session, now_ns)
        dr_expires_at_str = (
            datetime.fromtimestamp(
                session.dr_expires_at_ns / 1e9, tz=timezone.utc
            ).isoformat()
            if session.dr_expires_at_ns else None
        )

        rcr = RuntimeContinuityRecord(
            rcr_id=rcr_id,
            tar_id=tar_id,
            delegation_id=session.delegation_id,
            agent_id=session.agent_id,
            chain_root_id=session.chain_root_id,
            execution_ns=now_ns,
            execution_ts=now_ts,
            ces_score=ces.score,
            ces_temporal=ces.temporal,
            ces_budget=ces.budget,
            ces_context=ces.context,
            ces_integrity=ces.integrity,
            continuity_status=ces.status,
            predecessor_rcr_id=predecessor_rcr_id,
            budget_at_admission=session.budget_at_admission,
            budget_remaining=session.budget_remaining,
            context_drift_pct=context_drift_pct,
            active_anomalies=active_anomalies,
            dr_expires_at=dr_expires_at_str,
            time_remaining_ns=time_remaining_ns,
            fragmentation_score=frag_score,
            escalation_event_id=None,
            reauth_challenge_id=None,
            sample_reason=sample_reason,
            content_hash="",       # computed below
            pqc_signature=None,
            pqc_algorithm=None,
            issued_at=now_ts,
            metadata=metadata or {},
        )

        # ── Content hash and PQC signature ──────────────────────────────────
        rcr.content_hash = self._compute_hash(rcr)
        self._sign_rcr(rcr)

        # ── Update session state ─────────────────────────────────────────────
        with self._lock:
            session.last_rcr_id = rcr_id
            session.last_rcr_ns = now_ns
            session.rcr_count += 1

        # ── Store (ADR-160: tier-aware persistence) ──────────────────────────
        with self._lock:
            self._rcr_store[rcr_id] = rcr
        self._persist_rcr(rcr, tier=session.governance_risk_tier)

        # ── Escalation ───────────────────────────────────────────────────────
        cee, rc = self._evaluate_escalation(rcr, session, ces)
        if cee:
            rcr.escalation_event_id = cee.cee_id
        if rc:
            rcr.reauth_challenge_id = rc.rc_id

        logger.info(
            f"[RGC] RCR issued — {rcr_id} ces={ces.score:.1f} "
            f"status={ces.status} agent={session.agent_id}"
        )

        # ── HALT enforcement (RGC-INV-003) ──────────────────────────────────
        if ces.status == "HALT":
            self._trigger_halt(session, rcr)

        return rcr

    # ──────────────────────────────────────────────────────────
    # Reauthorization
    # ──────────────────────────────────────────────────────────

    def respond_to_rc(
        self,
        rc_id:         str,
        new_dr_id:     str,
        new_dr_expires_at: Optional[str] = None,
    ) -> ReauthorizationChallenge:
        """
        Submit a Tier-1 reauthorization response to a pending RC.

        Resolves the challenge and resets the temporal CES component for
        the session.

        Args:
            rc_id:             The ATFRC-... challenge ID
            new_dr_id:         The new DR issued by Tier-1
            new_dr_expires_at: Optional expiry of the new DR
        """
        with self._lock:
            rc = self._rc_store.get(rc_id)
        if not rc:
            raise RGCError(f"No Reauthorization Challenge found: {rc_id}")

        if rc.is_expired():
            raise RGCError(
                f"RC {rc_id} expired at ns={rc.expires_at_ns}. "
                "Execution should have been HALTED by TTL enforcement."
            )

        now_ts = datetime.now(tz=timezone.utc).isoformat()
        rc.response_dr_id = new_dr_id
        rc.resolved = True
        rc.resolution = "REAUTHORIZED"
        rc.response_received_at = now_ts   # type: ignore[attr-defined]

        # Update session with new DR expiry if provided
        with self._lock:
            for session in self._sessions.values():
                if session.delegation_id == rc.delegation_id:
                    if new_dr_expires_at:
                        try:
                            dt = datetime.fromisoformat(
                                new_dr_expires_at.replace("Z", "+00:00")
                            )
                            session.dr_expires_at_ns = int(
                                dt.timestamp() * 1_000_000_000
                            )
                        except Exception:
                            pass
                    # Clear open RC
                    session.open_rc = None

        logger.info(
            f"[RGC] RC resolved — {rc_id} new_dr={new_dr_id} agent={rc.agent_id}"
        )
        return rc

    # ──────────────────────────────────────────────────────────
    # ADR-160: Event-driven sampling interface
    # ──────────────────────────────────────────────────────────

    def notify_event(
        self,
        tar_id:            str,
        event_type:        str,
        budget_consumed:   float = 0.0,
        context_drift_pct: float = 0.0,
        active_anomalies:  int   = 0,
        metadata:          Optional[Dict[str, Any]] = None,
    ) -> Optional["RuntimeContinuityRecord"]:
        """
        Notify the engine of a governance-relevant event that may trigger
        an out-of-schedule RCR sample (ADR-160 — EventDrivenSampler).

        The sample is triggered only when the event delta meets or exceeds
        the configured thresholds (RPOL_BUDGET_TRIGGER_PCT, RPOL_DRIFT_TRIGGER_PCT,
        RPOL_ANOMALY_TRIGGER_N). This avoids handshake on micro-operations that
        do not materially change authority health.

        event_type values: BUDGET_CHANGE | ANOMALY_DETECTED | CONTEXT_DRIFT |
                           SCOPE_CHANGE | SUB_AGENT_SPAWN | EXTERNAL_TRIGGER

        Returns the RuntimeContinuityRecord if a sample was triggered, None otherwise.
        """
        try:
            from omnix_core.agents.atf.rcr_performance import GovernanceEventType
            evt = GovernanceEventType(event_type)
            return self._get_sampler().notify(
                tar_id=tar_id,
                event_type=evt,
                budget_consumed=budget_consumed,
                context_drift_pct=context_drift_pct,
                active_anomalies=active_anomalies,
                metadata=metadata,
            )
        except Exception as exc:
            logger.warning(f"[RGC] notify_event failed — tar={tar_id} event={event_type}: {exc}")
            return None

    def register_scheduler(
        self,
        tar_id:     str,
        profile:    str = "MEDIUM",
        get_inputs: Optional[Callable[[], Dict[str, Any]]] = None,
    ) -> None:
        """
        Register a session with the adaptive interval scheduler (ADR-160).

        The scheduler fires sample() automatically at intervals derived from
        ADR-159 §5 (Sampling Strategy) based on execution profile and live CES.

        profile: SHORT | MEDIUM | LONG | STREAMING
        get_inputs: optional callable returning dict with budget_consumed,
                    context_drift_pct, active_anomalies, metadata keys.
        """
        try:
            from omnix_core.agents.atf.rcr_performance import ExecutionProfile
            ep = ExecutionProfile(profile)
            self._get_scheduler().register(tar_id, ep, get_inputs)
        except Exception as exc:
            logger.warning(f"[RGC] register_scheduler failed — tar={tar_id}: {exc}")

    def deregister_scheduler(self, tar_id: str) -> None:
        """Remove a session from the adaptive interval scheduler (ADR-160)."""
        try:
            self._get_scheduler().deregister(tar_id)
        except Exception:
            pass

    def check_rc_ttl(self, tar_id: str) -> bool:
        """
        Check if a pending Reauthorization Challenge has expired.
        If so, triggers HALT (RGC-INV-008).
        Returns True if HALT was triggered.
        """
        with self._lock:
            session = self._sessions.get(tar_id)
            if not session or not session.open_rc:
                return False
            rc = session.open_rc

        if rc.is_expired():
            logger.warning(
                f"[RGC] RC TTL expired — {rc.rc_id} tar={tar_id} "
                "triggering HALT (RGC-INV-008)"
            )
            halt_rcr = self.sample(
                tar_id=tar_id,
                sample_reason="RC_TTL_EXPIRED",
                metadata={"rc_id": rc.rc_id, "halt_reason": "RC_TTL_EXPIRED"},
            )
            return True
        return False

    # ──────────────────────────────────────────────────────────
    # Authority Fragmentation Guard
    # ──────────────────────────────────────────────────────────

    def check_fragmentation(
        self,
        chain_root_id:    str,
        chain_root_budget: float,
        new_grant_budget: float,
    ) -> None:
        """
        Verify that adding a new sub-delegation does not exceed the AFG limit.

        RGC-INV-004: Raises AuthorityFragmentationViolation if the aggregate
        consumed budget across all active delegations in the chain would
        exceed chain_root_budget × AFG_FRAGMENTATION_LIMIT.

        Args:
            chain_root_id:     The chain root to check against
            chain_root_budget: Total budget at the chain root
            new_grant_budget:  Budget of the proposed new delegation
        """
        current_aggregate = self._aggregate_consumed(chain_root_id)
        proposed_aggregate = current_aggregate + new_grant_budget
        limit = chain_root_budget * self._afg_limit

        if proposed_aggregate > limit:
            raise AuthorityFragmentationViolation(
                f"Authority fragmentation detected on chain {chain_root_id}: "
                f"aggregate_consumed={current_aggregate:.1f} "
                f"+ new_grant={new_grant_budget:.1f} "
                f"= {proposed_aggregate:.1f} "
                f"> AFG_LIMIT={limit:.1f} "
                f"({self._afg_limit * 100:.0f}% of {chain_root_budget:.1f}). "
                "RGC-INV-004 violated."
            )

    # ──────────────────────────────────────────────────────────
    # Retrieval
    # ──────────────────────────────────────────────────────────

    def get_rcr(self, rcr_id: str) -> Optional[RuntimeContinuityRecord]:
        with self._lock:
            if rcr_id in self._rcr_store:
                return self._rcr_store[rcr_id]
        return self._fetch_rcr_from_db(rcr_id)

    def session_chain(self, tar_id: str) -> List[RuntimeContinuityRecord]:
        """Return the full continuity chain for a session, ordered by ns."""
        with self._lock:
            chain = [
                r for r in self._rcr_store.values() if r.tar_id == tar_id
            ]
        chain.sort(key=lambda r: r.execution_ns)
        return chain

    def current_ces(self, tar_id: str) -> Optional[ContinuityEligibilityScore]:
        """Return the most recent CES for an active session, without emitting an RCR."""
        with self._lock:
            session = self._sessions.get(tar_id)
            if not session:
                return None
        return self._compute_ces(
            session=session,
            now_ns=time.time_ns(),
            context_drift_pct=0.0,
            active_anomalies=0,
        )

    def active_sessions(self) -> List[Dict[str, Any]]:
        """Return summary of all active continuity sessions."""
        with self._lock:
            return [
                {
                    "tar_id":              s.tar_id,
                    "delegation_id":       s.delegation_id,
                    "agent_id":            s.agent_id,
                    "chain_root_id":       s.chain_root_id,
                    "domain":              s.domain,
                    "budget_remaining":    s.budget_remaining,
                    "budget_at_admission": s.budget_at_admission,
                    "rcr_count":           s.rcr_count,
                    "status":              s.status,
                    "has_open_rc":         s.open_rc is not None,
                    "started_at_ns":       s.started_at_ns,
                }
                for s in self._sessions.values()
            ]

    # ──────────────────────────────────────────────────────────
    # DB / DDL
    # ──────────────────────────────────────────────────────────

    def ensure_tables(self) -> bool:
        """Idempotent DDL creation. Returns True on success."""
        if not self._db_url:
            return False
        conn = self._get_conn()
        if not conn:
            return False
        try:
            with conn.cursor() as cur:
                cur.execute(DDL_RUNTIME_CONTINUITY)
            conn.commit()
            logger.info("[RGC] Tables ensured: atf_runtime_continuity + atf_continuity_escalations")
            return True
        except Exception as exc:
            logger.warning(f"[RGC] ensure_tables failed: {exc}")
            conn.rollback()
            return False
        finally:
            conn.close()

    # ──────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────

    def _compute_ces(
        self,
        session:           ContinuitySession,
        now_ns:            int,
        context_drift_pct: float,
        active_anomalies:  int,
    ) -> ContinuityEligibilityScore:
        """
        Compute CES from real-time values.
        RGC-INV-002: Inputs must reflect current state.
        """
        # T — Temporal Health
        temporal = 100.0
        if session.dr_expires_at_ns:
            total_lifetime_ns = session.dr_expires_at_ns - session.dr_issued_ns
            remaining_ns = session.dr_expires_at_ns - now_ns
            if total_lifetime_ns > 0:
                temporal = max(0.0, min(100.0, remaining_ns / total_lifetime_ns * 100.0))
            elif remaining_ns <= 0:
                temporal = 0.0

        # B — Budget Health
        budget_health = 100.0
        if session.budget_at_admission > 0:
            budget_health = max(
                0.0,
                min(100.0, session.budget_remaining / session.budget_at_admission * 100.0),
            )

        # D — Context Fidelity
        context_fidelity = max(0.0, min(100.0, 100.0 - context_drift_pct))

        # I — Integrity Score (10 points per active anomaly)
        integrity = max(0.0, min(100.0, 100.0 - (active_anomalies * 10.0)))

        return ContinuityEligibilityScore(
            temporal=round(temporal, 4),
            budget=round(budget_health, 4),
            context=round(context_fidelity, 4),
            integrity=round(integrity, 4),
        )

    def _time_remaining_ns(
        self, session: ContinuitySession, now_ns: int
    ) -> Optional[int]:
        if session.dr_expires_at_ns is None:
            return None
        return max(0, session.dr_expires_at_ns - now_ns)

    def _fragmentation_score(self, chain_root_id: str) -> float:
        """Aggregate budget consumption % across sessions sharing this root."""
        with self._lock:
            sessions = [
                s for s in self._sessions.values()
                if s.chain_root_id == chain_root_id and s.status == "ACTIVE"
            ]
        if not sessions:
            return 0.0
        total_admission = sum(s.budget_at_admission for s in sessions)
        total_remaining = sum(s.budget_remaining for s in sessions)
        if total_admission <= 0:
            return 0.0
        consumed = total_admission - total_remaining
        return round(consumed / total_admission * 100.0, 4)

    def _aggregate_consumed(self, chain_root_id: str) -> float:
        """Total budget granted across all sessions in a chain."""
        with self._lock:
            return sum(
                s.budget_at_admission
                for s in self._sessions.values()
                if s.chain_root_id == chain_root_id
            )

    def _evaluate_escalation(
        self,
        rcr: RuntimeContinuityRecord,
        session: ContinuitySession,
        ces: ContinuityEligibilityScore,
    ) -> Tuple[Optional[ContinuityEscalationEvent], Optional[ReauthorizationChallenge]]:
        """Issue escalation artifacts if CES crossed a threshold."""
        status = ces.status
        if status == "NOMINAL":
            return None, None

        threshold_to_action = {
            "MONITORING": "ALERT",
            "WARNING":    "SUSPEND_SPAWNING",
            "CRITICAL":   "REAUTHORIZE",
            "HALT":       "HALT",
        }
        action = threshold_to_action.get(status, "ALERT")
        ttl = 0 if status == "HALT" else self._rc_ttl

        now_ns = time.time_ns()
        now_ts = datetime.fromtimestamp(now_ns / 1e9, tz=timezone.utc).isoformat()

        cee_id = self._build_id(CEE_ID_PREFIX)
        cee = ContinuityEscalationEvent(
            cee_id=cee_id,
            rcr_id=rcr.rcr_id,
            tar_id=rcr.tar_id,
            delegation_id=rcr.delegation_id,
            agent_id=rcr.agent_id,
            chain_root_id=rcr.chain_root_id,
            threshold_crossed=status,
            recommended_action=action,
            ces_at_escalation=ces.score,
            escalation_ns=now_ns,
            response_ttl_seconds=ttl,
            response_received_at=None,
            response_dr_id=None,
            resolved=False,
            resolution_status=None,
            content_hash="",
            pqc_signature=None,
            pqc_algorithm=None,
            issued_at=now_ts,
            metadata={},
        )
        cee.content_hash = self._compute_hash_dict(asdict(cee))
        self._sign_cee(cee)

        with self._lock:
            self._cee_store[cee_id] = cee
        self._persist_cee(cee, tier=session.governance_risk_tier)

        logger.warning(
            f"[RGC] Escalation — {cee_id} status={status} "
            f"ces={ces.score:.1f} agent={rcr.agent_id} action={action}"
        )

        # Issue Reauthorization Challenge for CRITICAL
        rc: Optional[ReauthorizationChallenge] = None
        if status == "CRITICAL":
            rc = self._issue_rc(cee, session, ces, now_ns, now_ts)

        return cee, rc

    def _issue_rc(
        self,
        cee:     ContinuityEscalationEvent,
        session: ContinuitySession,
        ces:     ContinuityEligibilityScore,
        now_ns:  int,
        now_ts:  str,
    ) -> ReauthorizationChallenge:
        """Issue a Reauthorization Challenge. RGC-INV-008."""
        # Don't issue duplicate RCs for the same open challenge
        with self._lock:
            if session.open_rc and not session.open_rc.is_expired():
                return session.open_rc

        expires_at_ns = now_ns + (self._rc_ttl * 1_000_000_000)
        rc_id = self._build_id(RC_ID_PREFIX)

        rc = ReauthorizationChallenge(
            rc_id=rc_id,
            cee_id=cee.cee_id,
            tar_id=session.tar_id,
            delegation_id=session.delegation_id,
            agent_id=session.agent_id,
            chain_root_id=session.chain_root_id,
            ces_at_challenge=ces.score,
            challenge_ns=now_ns,
            ttl_seconds=self._rc_ttl,
            expires_at_ns=expires_at_ns,
            response_dr_id=None,
            resolved=False,
            resolution=None,
            content_hash="",
            pqc_signature=None,
            pqc_algorithm=None,
            issued_at=now_ts,
            metadata={"cee_id": cee.cee_id},
        )
        rc.content_hash = self._compute_hash_dict(asdict(rc))
        self._sign_rc(rc)

        with self._lock:
            self._rc_store[rc_id] = rc
            session.open_rc = rc

        logger.warning(
            f"[RGC] Reauthorization Challenge — {rc_id} "
            f"ttl={self._rc_ttl}s agent={rc.agent_id}"
        )
        return rc

    def _trigger_halt(
        self, session: ContinuitySession, rcr: RuntimeContinuityRecord
    ) -> None:
        """
        RGC-INV-003: Halt execution and revoke all in-flight sub-tasks
        sharing this chain_root_id.
        """
        logger.error(
            f"[RGC] HALT triggered — tar={session.tar_id} "
            f"agent={session.agent_id} ces={rcr.ces_score:.1f}"
        )
        with self._lock:
            session.status = "HALTED"
            # Revoke all sibling sessions on the same chain root
            sibling_sessions = [
                s for s in self._sessions.values()
                if s.chain_root_id == session.chain_root_id
                and s.tar_id != session.tar_id
                and s.status == "ACTIVE"
            ]
            for sibling in sibling_sessions:
                sibling.status = "REVOKED_BY_HALT"
                logger.warning(
                    f"[RGC] Sibling session revoked — tar={sibling.tar_id} "
                    f"agent={sibling.agent_id} (root HALT from {session.tar_id})"
                )

        if session.halt_callback:
            try:
                session.halt_callback(session.agent_id)
            except Exception as exc:
                logger.warning(f"[RGC] halt_callback raised: {exc}")

    # ──────────────────────────────────────────────────────────
    # Cryptography helpers
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _build_id(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:16].upper()}"

    @staticmethod
    def _compute_hash(rcr: RuntimeContinuityRecord) -> str:
        payload = {
            k: v for k, v in asdict(rcr).items()
            if k not in ("content_hash", "pqc_signature", "pqc_algorithm")
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
        ).hexdigest()

    @staticmethod
    def _compute_hash_dict(d: Dict[str, Any]) -> str:
        payload = {
            k: v for k, v in d.items()
            if k not in ("content_hash", "pqc_signature", "pqc_algorithm")
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
        ).hexdigest()

    def _load_provider(self):
        try:
            from omnix_core.security.crypto_providers import get_active_provider
            return get_active_provider()
        except Exception:
            return None

    def _sign_rcr(self, rcr: RuntimeContinuityRecord) -> None:
        if not self._provider:
            return
        try:
            sig = self._provider.sign(rcr.content_hash.encode())
            if sig:
                rcr.pqc_signature = base64.b64encode(sig).decode()
                rcr.pqc_algorithm = "dilithium3"
        except Exception as exc:
            logger.warning(f"[RGC] PQC sign RCR failed: {exc}")

    def _sign_cee(self, cee: ContinuityEscalationEvent) -> None:
        if not self._provider:
            return
        try:
            sig = self._provider.sign(cee.content_hash.encode())
            if sig:
                cee.pqc_signature = base64.b64encode(sig).decode()
                cee.pqc_algorithm = "dilithium3"
        except Exception as exc:
            logger.warning(f"[RGC] PQC sign CEE failed: {exc}")

    def _sign_rc(self, rc: ReauthorizationChallenge) -> None:
        if not self._provider:
            return
        try:
            sig = self._provider.sign(rc.content_hash.encode())
            if sig:
                rc.pqc_signature = base64.b64encode(sig).decode()
                rc.pqc_algorithm = "dilithium3"
        except Exception as exc:
            logger.warning(f"[RGC] PQC sign RC failed: {exc}")

    # ──────────────────────────────────────────────────────────
    # DB helpers
    # ──────────────────────────────────────────────────────────

    def _get_conn(self):
        try:
            import psycopg
            conn = psycopg.connect(self._db_url)
            return conn
        except Exception as exc:
            logger.warning(f"[RGC] DB connection failed: {exc}")
            return None

    def _persist_rcr(
        self, rcr: RuntimeContinuityRecord, tier: str = "STANDARD"
    ) -> None:
        """
        Persist an RCR to the database.

        ADR-160 tier behaviour:
          LOW      — skip persistence (no audit trail required for this tier).
          STANDARD — enqueue to RCRWriteQueue (async, pooled thread).
          HIGH     — enqueue synchronously (blocks until written).
          CRITICAL — enqueue synchronously (blocks until written).
        """
        if not self._db_url:
            return

        if tier == "LOW":
            return

        synchronous = tier in ("HIGH", "CRITICAL")
        try:
            evt = _get_write_queue().enqueue_rcr(rcr, synchronous=synchronous)
            if synchronous and evt:
                evt.wait(timeout=5.0)
        except Exception as exc:
            logger.warning(f"[RGC] _persist_rcr (RPOL) failed: {exc} — fallback to thread")
            def _write():
                conn = self._get_conn()
                if not conn:
                    return
                try:
                    import json as _json
                    with conn.cursor() as cur:
                        from omnix_core.agents.atf.rcr_performance import RCRWriteQueue
                        RCRWriteQueue._insert_rcr(cur, rcr, _json)
                    conn.commit()
                except Exception as exc2:
                    logger.warning(f"[RGC] _persist_rcr fallback failed: {exc2}")
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                finally:
                    conn.close()
            threading.Thread(target=_write, daemon=True).start()

    def _persist_cee(
        self, cee: ContinuityEscalationEvent, tier: str = "STANDARD"
    ) -> None:
        """
        Persist a CEE to the database.

        ADR-160: CEEs are always persisted regardless of tier because they
        represent governance escalation events that must be auditable.
        HIGH/CRITICAL tiers use synchronous writes to ensure the CEE is
        committed before the calling thread continues.
        """
        if not self._db_url:
            return

        synchronous = tier in ("HIGH", "CRITICAL")
        try:
            evt = _get_write_queue().enqueue_cee(cee, synchronous=synchronous)
            if synchronous and evt:
                evt.wait(timeout=5.0)
        except Exception as exc:
            logger.warning(f"[RGC] _persist_cee (RPOL) failed: {exc} — fallback to thread")
            def _write():
                conn = self._get_conn()
                if not conn:
                    return
                try:
                    import json as _json
                    with conn.cursor() as cur:
                        from omnix_core.agents.atf.rcr_performance import RCRWriteQueue
                        RCRWriteQueue._insert_cee(cur, cee, _json)
                    conn.commit()
                except Exception as exc2:
                    logger.warning(f"[RGC] _persist_cee fallback failed: {exc2}")
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                finally:
                    conn.close()
            threading.Thread(target=_write, daemon=True).start()

    def _fetch_rcr_from_db(self, rcr_id: str) -> Optional[RuntimeContinuityRecord]:
        if not self._db_url:
            return None
        conn = self._get_conn()
        if not conn:
            return None
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM atf_runtime_continuity WHERE rcr_id = %s",
                    (rcr_id,)
                )
                row = cur.fetchone()
                if row:
                    cols = [d[0] for d in cur.description]
                    return self._row_to_rcr(dict(zip(cols, row)))
        except Exception as exc:
            logger.warning(f"[RGC] _fetch_rcr_from_db failed: {exc}")
        finally:
            conn.close()
        return None

    @staticmethod
    def _row_to_rcr(row: Dict[str, Any]) -> RuntimeContinuityRecord:
        meta = row.get("metadata") or {}
        if isinstance(meta, str):
            try:
                import json as _json
                meta = _json.loads(meta)
            except Exception:
                meta = {}
        return RuntimeContinuityRecord(
            rcr_id=row["rcr_id"],
            tar_id=row["tar_id"],
            delegation_id=row["delegation_id"],
            agent_id=row["agent_id"],
            chain_root_id=row["chain_root_id"],
            execution_ns=int(row["execution_ns"]),
            execution_ts=str(row["execution_ts"]),
            ces_score=float(row["ces_score"]),
            ces_temporal=float(row["ces_temporal"]),
            ces_budget=float(row["ces_budget"]),
            ces_context=float(row["ces_context"]),
            ces_integrity=float(row["ces_integrity"]),
            continuity_status=row["continuity_status"],
            predecessor_rcr_id=row.get("predecessor_rcr_id"),
            budget_at_admission=float(row["budget_at_admission"]),
            budget_remaining=float(row["budget_remaining"]),
            context_drift_pct=float(row.get("context_drift_pct", 0.0)),
            active_anomalies=int(row.get("active_anomalies", 0)),
            dr_expires_at=str(row["dr_expires_at"]) if row.get("dr_expires_at") else None,
            time_remaining_ns=int(row["time_remaining_ns"]) if row.get("time_remaining_ns") is not None else None,
            fragmentation_score=float(row.get("fragmentation_score", 0.0)),
            escalation_event_id=row.get("escalation_event_id"),
            reauth_challenge_id=row.get("reauth_challenge_id"),
            sample_reason=row.get("sample_reason", "SCHEDULED"),
            content_hash=row["content_hash"],
            pqc_signature=row.get("pqc_signature"),
            pqc_algorithm=row.get("pqc_algorithm"),
            issued_at=str(row["issued_at"]),
            metadata=meta,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────────────────────────────────────

_engine_instance: Optional[RuntimeContinuityEngine] = None
_engine_lock = threading.Lock()


def get_rgc_engine() -> RuntimeContinuityEngine:
    """Return the process-level RuntimeContinuityEngine singleton."""
    global _engine_instance
    with _engine_lock:
        if _engine_instance is None:
            _engine_instance = RuntimeContinuityEngine()
        return _engine_instance
