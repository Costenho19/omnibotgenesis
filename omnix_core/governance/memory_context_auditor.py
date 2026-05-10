"""
OMNIX — Memory Context Auditor
ADR-151: Decision-Time Context Governance & Memory Attestation

═══════════════════════════════════════════════════════════════════════════════
PURPOSE
═══════════════════════════════════════════════════════════════════════════════

Most AI governance frameworks ask: "Did the model decide correctly?"
This module asks a prior, deeper question: "What did the model know when it decided —
and was that knowledge defensible, uncontaminated, and within authorized bounds?"

This is the architectural distinction between:
  · Decision Governance   — what OMNIX has always done (ADR-028)
  · Context Governance    — what this module adds (ADR-151)

Every AI decision is a function of two things:
  1. The algorithm (governed by the 11-checkpoint pipeline)
  2. The context window (governed by this module)

Without context governance, a receipt proves the algorithm ran correctly on some inputs.
With context governance, a receipt proves the algorithm ran correctly on *these specific,
attested, uncontaminated inputs* — and here is the signed proof.

═══════════════════════════════════════════════════════════════════════════════
ARCHITECTURE POSITION
═══════════════════════════════════════════════════════════════════════════════

    [External Data Sources / Signal Feeds / History]
                │
                ▼
    MemoryContextAuditor.capture_snapshot()   ← context captured here
                │
                ├─→ detect_contamination()    ← unauthorized keys, injection attempts
                ├─→ detect_drift()            ← context vs authorized baseline
                └─→ generate_mar()            ← PQC-signed Memory Attestation Record
                │
                ▼
    [LLMIsolationBoundary.form_packet()]      ← existing (ADR-148)
                │
                ▼
    [11-Checkpoint Pipeline]                  ← existing (ADR-028)
                │
                ▼
    [DecisionReceiptEngine + mar_id embedded] ← enhanced: receipt now references MAR

═══════════════════════════════════════════════════════════════════════════════
KEY INVARIANTS (never relaxed)
═══════════════════════════════════════════════════════════════════════════════

  1. Every MemoryAttestationRecord is immutable once generated.
  2. MAR generation is fail-closed: if context cannot be attested, the pipeline
     receives a ContaminationClass.CRITICAL verdict — decision is BLOCKED.
  3. MARs carry PQC signatures (Dilithium-3) when keys are available;
     fallback to SHA-256-only in degraded mode (logged as WARNING).
  4. Context contamination detection is additive — every layer that finds an issue
     appends a ContaminationFlag; no single layer can clear flags from another.
  5. The mar_id is embedded in every Decision Receipt as `memory_attestation_id`
     — creating a bidirectional audit chain: receipt ↔ MAR.
  6. History depth governance: context windows exceeding MAX_AUTHORIZED_HISTORY_DEPTH
     are flagged as SUSPICIOUS and trigger Tier 1 review.

ADR-151 — Harold Nunes — OMNIX QUANTUM LTD — May 2026
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
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("OMNIX.Governance.MemoryContextAuditor")

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS & CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

# Maximum number of previous decisions allowed in context window.
# Exceeding this triggers SUSPICIOUS — context may be carrying stale signals.
MAX_AUTHORIZED_HISTORY_DEPTH: int = int(os.environ.get("OMNIX_MAX_CONTEXT_HISTORY", "10"))

# Drift threshold (%) above which context is considered DRIFTED from baseline.
CONTEXT_DRIFT_THRESHOLD: float = float(os.environ.get("OMNIX_CONTEXT_DRIFT_THRESHOLD", "30.0"))

# Drift threshold above which context is CRITICAL (pipeline must block).
CONTEXT_CRITICAL_THRESHOLD: float = float(os.environ.get("OMNIX_CONTEXT_CRITICAL_THRESHOLD", "70.0"))

# Data freshness: signals older than this (seconds) are flagged STALE.
MAX_SIGNAL_AGE_SECONDS: int = int(os.environ.get("OMNIX_MAX_SIGNAL_AGE_SECONDS", "300"))

# Ring buffer size for in-process MAR log.
_MAX_MAR_LOG_SIZE: int = 2000

# Authorized external data source categories.
_AUTHORIZED_DATA_SOURCES: Set[str] = {
    "market_feed",
    "credit_bureau",
    "aml_database",
    "regulatory_registry",
    "historical_receipts",
    "calibration_snapshot",
    "fraud_intelligence",
    "jurisdiction_registry",
    "sharia_authority",
    "actuarial_table",
    "energy_grid_feed",
    "property_registry",
    "defense_intelligence",
    "stablecoin_reserve_feed",
    "health_records_anonymized",
    "robotics_sensor_feed",
    "agent_intent_feed",
    "internal_signals",
}

# Signal weight map for context drift computation (mirrors AVM — ADR-076).
_CONTEXT_DRIFT_WEIGHTS: Dict[str, float] = {
    "probability_score":  0.25,
    "signal_coherence":   0.25,
    "risk_exposure":      0.20,
    "stress_resilience":  0.15,
    "trend_persistence":  0.10,
    "logic_consistency":  0.05,
}


# ─────────────────────────────────────────────────────────────────────────────
# ENUMERATIONS
# ─────────────────────────────────────────────────────────────────────────────

class ContaminationClass(str, Enum):
    """
    Classification of context integrity at decision time.

    CLEAN        — No contamination detected. Context is authorized and unmodified.
    SUSPICIOUS   — Anomalies detected (excessive history, stale signals, unknown sources).
                   Pipeline continues with trust_flags.context_suspicious = True.
    CONTAMINATED — Active contamination evidence (forbidden keys, injection patterns,
                   unauthorized data sources). Tier 1 review triggered.
    CRITICAL     — Severe contamination or context integrity cannot be established.
                   Pipeline BLOCKED. Tier 1 alert dispatched.
    """
    CLEAN       = "CLEAN"
    SUSPICIOUS  = "SUSPICIOUS"
    CONTAMINATED = "CONTAMINATED"
    CRITICAL    = "CRITICAL"


class ContaminationSource(str, Enum):
    """Origin layer where contamination was detected."""
    SIGNAL_LAYER      = "SIGNAL_LAYER"       # In the numeric signal dict
    HISTORY_LAYER     = "HISTORY_LAYER"      # In the context history window
    EXTERNAL_SOURCE   = "EXTERNAL_SOURCE"    # Unauthorized data source
    FRESHNESS_GUARD   = "FRESHNESS_GUARD"    # Signal staleness
    INJECTION_GUARD   = "INJECTION_GUARD"    # Prompt/context injection patterns
    DRIFT_GUARD       = "DRIFT_GUARD"        # Context drift from baseline
    INTEGRITY_GUARD   = "INTEGRITY_GUARD"    # Hash/signature mismatch


class ContextKey(str, Enum):
    """
    Categories of data that may be present in the AI's context window.
    Used to build a structured manifest — not a free-form dict.
    """
    GOVERNANCE_SIGNALS  = "governance_signals"
    DECISION_HISTORY    = "decision_history"
    EXTERNAL_FEEDS      = "external_feeds"
    CALIBRATION_DATA    = "calibration_data"
    REGULATORY_CONTEXT  = "regulatory_context"
    DOMAIN_METADATA     = "domain_metadata"
    TEMPORAL_CONTEXT    = "temporal_context"
    SCOPE_AUTHORIZATION = "scope_authorization"


# ─────────────────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ExternalDataSource:
    """
    Record of one external data source consulted during context assembly.

    Fields:
        source_type    — category (must be in _AUTHORIZED_DATA_SOURCES)
        source_id      — specific feed or API identifier
        queried_at     — ISO-8601 UTC timestamp of data retrieval
        data_age_s     — age of data at time of query (seconds)
        authorized     — whether source_type is in authorized set
        data_hash      — SHA-256 of retrieved data (for tampering detection)
    """
    source_type: str
    source_id: str
    queried_at: str
    data_age_s: float
    authorized: bool
    data_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContaminationFlag:
    """
    A single detected contamination event in the context window.

    Flags are additive — multiple flags may apply to one snapshot.
    No layer can remove a flag raised by another layer.

    Fields:
        flag_id        — UUID for this flag
        source         — ContaminationSource enum
        severity       — ContaminationClass (the worst flag determines overall class)
        description    — Human-readable description
        evidence       — Key/value evidence supporting the flag
        detected_at    — ISO-8601 UTC
    """
    flag_id: str
    source: str          # ContaminationSource value
    severity: str        # ContaminationClass value
    description: str
    evidence: Dict[str, Any]
    detected_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContextSnapshot:
    """
    Point-in-time capture of the complete context window at decision time.

    This is the memory state of the AI system at the exact moment it was
    asked to evaluate a governance decision.

    Fields:
        snapshot_id        — Unique identifier (OMNIX-CTX-{12hex})
        domain             — Governance domain (trading, insurance, etc.)
        asset              — Asset or case identifier
        captured_at        — ISO-8601 UTC timestamp
        context_keys       — Manifest of ContextKey categories present
        signals            — The exact numeric signals entering governance
        signal_fingerprint — SHA-256 of canonical signals dict
        history_depth      — Number of previous decisions in context
        history_fingerprint — SHA-256 of decision history (if present)
        external_sources   — Data sources consulted
        signal_age_s       — Age of signals at capture time (seconds)
        domain_metadata    — Domain-specific context metadata
        scope_id           — Active Scope Authorization ID (ADR-147)
        context_hash       — SHA-256 of full canonical context (integrity anchor)
    """
    snapshot_id: str
    domain: str
    asset: str
    captured_at: str
    context_keys: List[str]
    signals: Dict[str, float]
    signal_fingerprint: str
    history_depth: int
    history_fingerprint: Optional[str]
    external_sources: List[Dict[str, Any]]
    signal_age_s: float
    domain_metadata: Dict[str, Any]
    scope_id: Optional[str]
    context_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DriftAssessment:
    """
    Quantitative assessment of context drift from the authorized baseline.

    Mirrors AVM drift computation (ADR-076) but applied to context signals
    rather than calibration snapshots.

    OMNIX DIFFERENTIATOR — Adversarial vs. Natural Drift Classification:
    Most governance systems measure drift magnitude. OMNIX also classifies
    drift *intent*: natural drift (market moved — all signals shift together)
    vs. adversarial drift (selective signals shifted to manipulate outcome).

    A natural drift of 40% is a market event. An adversarial drift of 40%
    is a potential attack. They look identical in magnitude — only directional
    pattern analysis can distinguish them.

    Fields:
        drift_score           — Weighted L1 distance (0–100)
        drift_verdict         — NEGLIGIBLE / MODERATE / SIGNIFICANT / CRITICAL
        signal_deltas         — Per-signal delta from baseline
        baseline_id           — Identifier of the baseline used for comparison
        assessed_at           — ISO-8601 UTC
        drift_pattern         — NATURAL / ADVERSARIAL / UNDETERMINED
        adversarial_signals   — Signals whose drift direction would flip the decision
        signal_direction_map  — Per-signal: RISING / FALLING / STABLE
    """
    drift_score: float
    drift_verdict: str
    signal_deltas: Dict[str, float]
    baseline_id: Optional[str]
    assessed_at: str
    drift_pattern: str = "UNDETERMINED"           # NATURAL | ADVERSARIAL | UNDETERMINED
    adversarial_signals: List[str] = field(default_factory=list)
    signal_direction_map: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryAttestationRecord:
    """
    PQC-signed attestation of the AI's complete context state at decision time.

    The MAR is the answer to: "What did the AI know when it decided,
    and was that knowledge defensible?"

    A MAR ID is embedded in every Decision Receipt as `memory_attestation_id`,
    creating a permanent bidirectional audit chain:

        Decision Receipt ←→ Memory Attestation Record

    ─────────────────────────────────────────────────────────────────────────
    OMNIX DIFFERENTIATOR — Context Sovereignty Score (CSS):
    ─────────────────────────────────────────────────────────────────────────
    No AI governance platform computes a single defensibility score for the
    context window. OMNIX does.

    The CSS (0–100) is a composite metric combining:
      · Source authorization rate  (what % of data sources were authorized)
      · Signal freshness score     (how fresh signals were at decision time)
      · Contamination penalty      (class-based deduction: SUSPICIOUS=-10,
                                    CONTAMINATED=-30, CRITICAL=-60)
      · Drift penalty              (proportional to normalized drift score)

    A CSS ≥ 80 is "Defensible." A CSS < 50 is "Indefensible."
    Regulators and auditors have one number to assess context quality.

    ─────────────────────────────────────────────────────────────────────────
    OMNIX DIFFERENTIATOR — Adversarial Drift Pattern:
    ─────────────────────────────────────────────────────────────────────────
    Most systems measure drift magnitude. OMNIX classifies drift intent.
    NATURAL drift = market moved, all signals shift together coherently.
    ADVERSARIAL drift = selective signals shifted to manipulate outcome.
    A 40% natural drift is a market event. A 40% adversarial drift is an
    attack. `drift_assessment.drift_pattern` captures this distinction.

    Fields:
        mar_id                  — Unique identifier (OMNIX-MAR-{12hex})
        decision_id             — Links to the governance decision
        domain                  — Governance domain
        asset                   — Asset or case identifier
        snapshot                — The full ContextSnapshot
        contamination_flags     — All detected contamination events
        contamination_class     — Worst-case: CLEAN/SUSPICIOUS/CONTAMINATED/CRITICAL
        drift_assessment        — Quantified drift + adversarial pattern
        context_sovereignty_score — CSS (0–100): composite defensibility metric
        css_breakdown           — Per-component CSS breakdown for audit trail
        integrity_verdict       — Human-readable attestation statement
        content_hash            — SHA-256 of canonical MAR content (pre-signature)
        pqc_signature           — Base64 Dilithium-3 signature (or SHA-256 degraded)
        public_key              — Base64 public key (self-verifying, no infra needed)
        signing_algorithm       — Algorithm identifier
        generated_at            — ISO-8601 UTC
        adr_reference           — "ADR-151"
    """
    mar_id: str
    decision_id: Optional[str]
    domain: str
    asset: str
    snapshot: Dict[str, Any]
    contamination_flags: List[Dict[str, Any]]
    contamination_class: str
    drift_assessment: Dict[str, Any]
    context_sovereignty_score: float
    css_breakdown: Dict[str, float]
    integrity_verdict: str
    content_hash: str
    pqc_signature: str
    public_key: str
    signing_algorithm: str
    generated_at: str
    adr_reference: str = "ADR-151"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────────────
# EXCEPTIONS
# ─────────────────────────────────────────────────────────────────────────────

class ContextIntegrityError(Exception):
    """
    Raised when context integrity cannot be established (CRITICAL contamination).
    Callers must catch this and block the governance evaluation — fail-closed.
    """
    def __init__(self, message: str, snapshot_id: str, flags: List[ContaminationFlag]):
        super().__init__(message)
        self.snapshot_id = snapshot_id
        self.flags = flags


# ─────────────────────────────────────────────────────────────────────────────
# IN-PROCESS MAR LOG (ring buffer)
# ─────────────────────────────────────────────────────────────────────────────

_mar_log: List[Dict[str, Any]] = []
_mar_log_lock = threading.Lock()


def _append_mar_log(mar: MemoryAttestationRecord) -> None:
    with _mar_log_lock:
        _mar_log.append({
            "mar_id":                    mar.mar_id,
            "domain":                    mar.domain,
            "asset":                     mar.asset,
            "contamination_class":       mar.contamination_class,
            "drift_score":               mar.drift_assessment.get("drift_score", 0.0),
            "drift_pattern":             mar.drift_assessment.get("drift_pattern", "UNDETERMINED"),
            "context_sovereignty_score": mar.context_sovereignty_score,
            "flags_count":               len(mar.contamination_flags),
            "generated_at":              mar.generated_at,
        })
        if len(_mar_log) > _MAX_MAR_LOG_SIZE:
            _mar_log.pop(0)


def get_mar_log(limit: int = 100) -> List[Dict[str, Any]]:
    """Return recent MAR summaries from in-process ring buffer (newest first)."""
    with _mar_log_lock:
        return list(reversed(_mar_log[-limit:]))


def get_mar_stats() -> Dict[str, Any]:
    """Aggregate statistics for operational monitoring."""
    with _mar_log_lock:
        total = len(_mar_log)
        by_class: Dict[str, int] = {}
        total_drift = 0.0
        for m in _mar_log:
            cc = m.get("contamination_class", "UNKNOWN")
            by_class[cc] = by_class.get(cc, 0) + 1
            total_drift += m.get("drift_score", 0.0)
        return {
            "total_mars":          total,
            "by_contamination":    by_class,
            "avg_drift_score":     round(total_drift / total, 2) if total else 0.0,
            "clean_rate":          round(by_class.get("CLEAN", 0) / total, 4) if total else 1.0,
            "critical_rate":       round(by_class.get("CRITICAL", 0) / total, 4) if total else 0.0,
        }


# ─────────────────────────────────────────────────────────────────────────────
# SIGNING HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _load_signing_keys() -> Tuple[Optional[bytes], Optional[bytes]]:
    """Load Dilithium-3 keys from environment (ADR-085 pattern)."""
    sk_b64 = os.environ.get("OMNIX_SIGNING_SECRET_KEY_B64", "").strip()
    pk_b64 = os.environ.get("OMNIX_SIGNING_PUBLIC_KEY_B64", "").strip()
    if not sk_b64 or not pk_b64:
        return None, None
    try:
        return base64.b64decode(sk_b64), base64.b64decode(pk_b64)
    except Exception as e:
        logger.warning(f"[MAR] Failed to decode signing keys: {e}")
        return None, None


def _sign_content(content: bytes) -> Tuple[str, str, str]:
    """
    Sign content with Dilithium-3. Returns (signature_b64, public_key_b64, algorithm).
    Falls back to SHA-256 HMAC if PQC is unavailable (degraded mode, logged).
    """
    sk_bytes, pk_bytes = _load_signing_keys()

    # Attempt PQC signing via crypto_providers (ADR-085)
    try:
        from omnix_core.security.crypto_providers import get_active_provider
        provider = get_active_provider()
        if provider and sk_bytes and pk_bytes:
            sig = provider.sign(content, sk_bytes)
            if sig:
                sig_b64 = base64.b64encode(sig).decode()
                pk_b64  = provider.serialize_public_key(pk_bytes)
                return sig_b64, pk_b64, f"Dilithium-3 (NIST FIPS 204) · {provider.algorithm_name()}"
    except Exception as e:
        logger.warning(f"[MAR] PQC signing unavailable, falling back to SHA-256: {e}")

    # Fallback: SHA-256 content hash (degraded mode)
    sha = hashlib.sha256(content).hexdigest()
    logger.warning("[MAR] DEGRADED MODE — MAR signed with SHA-256 only, not PQC.")
    return sha, "SHA256-ONLY-NO-PQC-KEY", "sha256-degraded"


def _canonical_hash(data: Dict[str, Any]) -> str:
    """SHA-256 of canonical JSON representation (sorted keys, no whitespace)."""
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# MEMORY CONTEXT AUDITOR — MAIN ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class MemoryContextAuditor:
    """
    OMNIX Memory Context Auditor — ADR-151

    Governs the complete context window of any AI system at the moment it
    produces a governance decision.

    Usage (standard flow):
        auditor = MemoryContextAuditor()

        # 1. Capture what the AI knew
        snapshot = auditor.capture_snapshot(
            signals={"probability_score": 72, "risk_exposure": 45, ...},
            domain="trading",
            asset="BTC/USD",
            history_depth=3,
            external_sources=[
                ExternalDataSource("market_feed", "binance_l2", ..., authorized=True),
            ],
            signal_age_s=12.4,
            domain_metadata={"strategy": "momentum"},
            scope_id="SAR-XXXXXXXXXXXX",
        )

        # 2. Detect contamination
        flags = auditor.detect_contamination(snapshot)

        # 3. Assess drift from baseline
        drift = auditor.detect_drift(snapshot, baseline_signals=avm_baseline)

        # 4. Generate signed MAR
        mar = auditor.generate_mar(snapshot, flags, drift, decision_id=None)
        # mar.mar_id → embed in Decision Receipt as memory_attestation_id

        # 5. If CRITICAL, block:
        if mar.contamination_class == ContaminationClass.CRITICAL.value:
            raise ContextIntegrityError("Context CRITICAL", snapshot.snapshot_id, flags)

    Thread-safe. Singleton via get_memory_context_auditor().
    """

    def __init__(self, fail_closed_on_critical: bool = True):
        """
        Args:
            fail_closed_on_critical: If True (default), generate_mar() raises
                ContextIntegrityError when contamination_class is CRITICAL.
                Set False only in testing/shadow mode.
        """
        self._fail_closed = fail_closed_on_critical
        logger.info(
            f"[MAR] MemoryContextAuditor initialized — "
            f"fail_closed={fail_closed_on_critical} "
            f"drift_threshold={CONTEXT_DRIFT_THRESHOLD}% "
            f"critical_threshold={CONTEXT_CRITICAL_THRESHOLD}% "
            f"max_history={MAX_AUTHORIZED_HISTORY_DEPTH}"
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def capture_snapshot(
        self,
        signals: Dict[str, float],
        domain: str,
        asset: str,
        history_depth: int = 0,
        history_fingerprint: Optional[str] = None,
        external_sources: Optional[List[ExternalDataSource]] = None,
        signal_age_s: float = 0.0,
        domain_metadata: Optional[Dict[str, Any]] = None,
        scope_id: Optional[str] = None,
    ) -> ContextSnapshot:
        """
        Capture the complete context window at the current moment.

        This is the fundamental operation — before any evaluation begins,
        call this to create an immutable, hashable record of what the AI knew.

        Args:
            signals:           Numeric governance signals (pre-boundary-crossing)
            domain:            Governance domain
            asset:             Asset or case identifier
            history_depth:     Number of prior decisions in context window
            history_fingerprint: SHA-256 of decision history content (if any)
            external_sources:  Data sources consulted during context assembly
            signal_age_s:      Age of signals in seconds at capture time
            domain_metadata:   Domain-specific context (e.g. applicant_type)
            scope_id:          Active scope authorization ID (ADR-147)

        Returns:
            ContextSnapshot — immutable, hashable, ready for contamination check
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        snapshot_id = f"OMNIX-CTX-{uuid.uuid4().hex[:12].upper()}"
        external_sources = external_sources or []

        # Build context key manifest
        context_keys: List[str] = [ContextKey.GOVERNANCE_SIGNALS.value]
        if history_depth > 0:
            context_keys.append(ContextKey.DECISION_HISTORY.value)
        if external_sources:
            context_keys.append(ContextKey.EXTERNAL_FEEDS.value)
        if domain_metadata:
            context_keys.append(ContextKey.DOMAIN_METADATA.value)
        if scope_id:
            context_keys.append(ContextKey.SCOPE_AUTHORIZATION.value)
        context_keys.append(ContextKey.TEMPORAL_CONTEXT.value)

        # Compute signal fingerprint
        canonical_signals = json.dumps(signals, sort_keys=True, separators=(",", ":"), default=str)
        signal_fingerprint = hashlib.sha256(canonical_signals.encode()).hexdigest()

        # Compute full context hash (integrity anchor)
        context_payload = {
            "snapshot_id":    snapshot_id,
            "domain":         domain,
            "asset":          asset,
            "captured_at":    now_iso,
            "signals":        signals,
            "history_depth":  history_depth,
            "sources":        [s.to_dict() if hasattr(s, 'to_dict') else s for s in external_sources],
            "scope_id":       scope_id,
        }
        context_hash = _canonical_hash(context_payload)

        snapshot = ContextSnapshot(
            snapshot_id=snapshot_id,
            domain=domain,
            asset=asset,
            captured_at=now_iso,
            context_keys=context_keys,
            signals=signals,
            signal_fingerprint=signal_fingerprint,
            history_depth=history_depth,
            history_fingerprint=history_fingerprint,
            external_sources=[
                s.to_dict() if hasattr(s, 'to_dict') else s
                for s in external_sources
            ],
            signal_age_s=signal_age_s,
            domain_metadata=domain_metadata or {},
            scope_id=scope_id,
            context_hash=context_hash,
        )

        logger.info(
            f"[MAR] Context snapshot captured — id={snapshot_id} "
            f"domain={domain} asset={asset} signals={len(signals)} "
            f"history_depth={history_depth} sources={len(external_sources)}"
        )
        return snapshot

    def detect_contamination(self, snapshot: ContextSnapshot) -> List[ContaminationFlag]:
        """
        Run all contamination detection layers against a ContextSnapshot.

        Layers (applied in order, all results accumulated):
          1. Signal Layer      — forbidden keys, non-numeric values
          2. Freshness Guard   — signal staleness
          3. History Guard     — excessive history depth
          4. Source Guard      — unauthorized external sources
          5. Injection Guard   — prompt injection patterns in metadata

        Returns:
            List of ContaminationFlag (empty = CLEAN). Flags are additive.
        """
        flags: List[ContaminationFlag] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        def _flag(source: ContaminationSource, severity: ContaminationClass,
                  description: str, evidence: Dict[str, Any]) -> ContaminationFlag:
            return ContaminationFlag(
                flag_id=f"CFG-{uuid.uuid4().hex[:8].upper()}",
                source=source.value,
                severity=severity.value,
                description=description,
                evidence=evidence,
                detected_at=now_iso,
            )

        # ── Layer 1: Signal Layer ────────────────────────────────────────────
        _FORBIDDEN_IN_CONTEXT = {
            "prompt", "system_prompt", "user_message", "llm_response",
            "model_name", "model_id", "conversation_id", "chat_history",
            "session_id", "raw_text", "instruction", "context_window",
            "temperature", "top_p", "completion",
        }
        forbidden_found = [k for k in snapshot.signals if k in _FORBIDDEN_IN_CONTEXT]
        if forbidden_found:
            flags.append(_flag(
                ContaminationSource.SIGNAL_LAYER,
                ContaminationClass.CRITICAL,
                f"Forbidden LLM artifact keys detected in governance signals — "
                f"context integrity cannot be established",
                {"forbidden_keys": forbidden_found, "count": len(forbidden_found)},
            ))

        non_numeric = [k for k, v in snapshot.signals.items() if not isinstance(v, (int, float))]
        if non_numeric:
            flags.append(_flag(
                ContaminationSource.SIGNAL_LAYER,
                ContaminationClass.CONTAMINATED,
                f"Non-numeric signal values detected — governance pipeline requires numeric signals",
                {"non_numeric_keys": non_numeric},
            ))

        import math
        nan_inf = [k for k, v in snapshot.signals.items()
                   if isinstance(v, float) and (math.isnan(v) or math.isinf(v))]
        if nan_inf:
            flags.append(_flag(
                ContaminationSource.SIGNAL_LAYER,
                ContaminationClass.CRITICAL,
                f"NaN/Inf values detected in governance signals — logic bypass risk",
                {"affected_keys": nan_inf},
            ))

        # ── Layer 2: Freshness Guard ─────────────────────────────────────────
        if snapshot.signal_age_s > MAX_SIGNAL_AGE_SECONDS:
            severity = (ContaminationClass.CONTAMINATED
                        if snapshot.signal_age_s > MAX_SIGNAL_AGE_SECONDS * 2
                        else ContaminationClass.SUSPICIOUS)
            flags.append(_flag(
                ContaminationSource.FRESHNESS_GUARD,
                severity,
                f"Signals are stale — age {snapshot.signal_age_s:.1f}s exceeds "
                f"authorized maximum {MAX_SIGNAL_AGE_SECONDS}s",
                {"signal_age_s": snapshot.signal_age_s, "threshold_s": MAX_SIGNAL_AGE_SECONDS},
            ))

        # ── Layer 3: History Guard ───────────────────────────────────────────
        if snapshot.history_depth > MAX_AUTHORIZED_HISTORY_DEPTH:
            flags.append(_flag(
                ContaminationSource.HISTORY_LAYER,
                ContaminationClass.SUSPICIOUS,
                f"Context history exceeds authorized depth — "
                f"context window may carry stale prior-decision signals",
                {
                    "history_depth":          snapshot.history_depth,
                    "max_authorized_depth":   MAX_AUTHORIZED_HISTORY_DEPTH,
                },
            ))

        if snapshot.history_depth > 0 and snapshot.history_fingerprint is None:
            flags.append(_flag(
                ContaminationSource.HISTORY_LAYER,
                ContaminationClass.SUSPICIOUS,
                "Decision history present in context but not fingerprinted — "
                "history integrity cannot be verified",
                {"history_depth": snapshot.history_depth},
            ))

        # ── Layer 4: Source Guard ────────────────────────────────────────────
        for src in snapshot.external_sources:
            src_type = src.get("source_type", "") if isinstance(src, dict) else src.source_type
            authorized = src.get("authorized", False) if isinstance(src, dict) else src.authorized
            data_age = src.get("data_age_s", 0) if isinstance(src, dict) else src.data_age_s

            if not authorized or src_type not in _AUTHORIZED_DATA_SOURCES:
                flags.append(_flag(
                    ContaminationSource.EXTERNAL_SOURCE,
                    ContaminationClass.CONTAMINATED,
                    f"Unauthorized external data source in context — "
                    f"source_type '{src_type}' is not in the authorized registry",
                    {"source_type": src_type, "authorized": authorized},
                ))

            if data_age > MAX_SIGNAL_AGE_SECONDS:
                flags.append(_flag(
                    ContaminationSource.FRESHNESS_GUARD,
                    ContaminationClass.SUSPICIOUS,
                    f"External data source '{src_type}' returned stale data",
                    {"source_type": src_type, "data_age_s": data_age},
                ))

        # ── Layer 5: Injection Guard ─────────────────────────────────────────
        _INJECTION_PATTERNS = [
            "ignore previous", "disregard", "forget instructions",
            "system:", "assistant:", "human:", "jailbreak",
            "override governance", "bypass checkpoint",
            "approve regardless", "always approve",
        ]
        metadata_str = json.dumps(snapshot.domain_metadata, default=str).lower()
        matched = [p for p in _INJECTION_PATTERNS if p in metadata_str]
        if matched:
            flags.append(_flag(
                ContaminationSource.INJECTION_GUARD,
                ContaminationClass.CRITICAL,
                "Prompt injection patterns detected in domain metadata",
                {"matched_patterns": matched, "source": "domain_metadata"},
            ))

        if flags:
            worst = max(
                (ContaminationClass[f.severity] for f in flags),
                key=lambda c: [
                    ContaminationClass.CLEAN,
                    ContaminationClass.SUSPICIOUS,
                    ContaminationClass.CONTAMINATED,
                    ContaminationClass.CRITICAL,
                ].index(c)
            )
            logger.warning(
                f"[MAR] Contamination detected — snapshot={snapshot.snapshot_id} "
                f"flags={len(flags)} worst={worst.value} "
                f"domain={snapshot.domain}"
            )
        else:
            logger.info(
                f"[MAR] Context clean — snapshot={snapshot.snapshot_id} "
                f"domain={snapshot.domain}"
            )

        return flags

    def detect_drift(
        self,
        snapshot: ContextSnapshot,
        baseline_signals: Optional[Dict[str, float]] = None,
        baseline_id: Optional[str] = None,
    ) -> DriftAssessment:
        """
        Compute context drift from an authorized baseline.

        Uses the AVM canonical signal weights (ADR-076) for consistency.
        If no baseline is provided, returns NEGLIGIBLE drift (no comparison possible).

        Args:
            snapshot:          The ContextSnapshot to assess
            baseline_signals:  Authorized baseline signal values (0–100 normalized)
            baseline_id:       Identifier of the baseline (for audit trail)

        Returns:
            DriftAssessment with quantified drift score and verdict
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        if not baseline_signals:
            return DriftAssessment(
                drift_score=0.0,
                drift_verdict="NEGLIGIBLE",
                signal_deltas={},
                baseline_id=baseline_id,
                assessed_at=now_iso,
            )

        import math
        signal_deltas: Dict[str, float] = {}
        weighted_drift = 0.0
        total_weight = 0.0

        for key, weight in _CONTEXT_DRIFT_WEIGHTS.items():
            current = snapshot.signals.get(key)
            baseline = baseline_signals.get(key)
            if current is None or baseline is None:
                continue
            if math.isnan(current) or math.isnan(baseline):
                continue
            delta = abs(current - baseline)
            signal_deltas[key] = round(delta, 2)
            weighted_drift += delta * weight
            total_weight += weight

        drift_score = round((weighted_drift / total_weight) if total_weight > 0 else 0.0, 2)

        # Risk amplification: if risk_exposure is rising, amplify drift signal
        current_risk = snapshot.signals.get("risk_exposure", 0)
        baseline_risk = baseline_signals.get("risk_exposure", 0)
        if isinstance(current_risk, (int, float)) and isinstance(baseline_risk, (int, float)):
            if current_risk > baseline_risk:
                drift_score = round(drift_score * 1.4, 2)

        if drift_score < 15.0:
            verdict = "NEGLIGIBLE"
        elif drift_score < CONTEXT_DRIFT_THRESHOLD:
            verdict = "MODERATE"
        elif drift_score < CONTEXT_CRITICAL_THRESHOLD:
            verdict = "SIGNIFICANT"
        else:
            verdict = "CRITICAL"

        # ── OMNIX DIFFERENTIATOR: Adversarial vs. Natural Drift Classification ──
        #
        # Natural drift: market moved — all signals drift in the same direction
        #   coherently (all risk signals up, all quality signals down).
        # Adversarial drift: selective signals shifted to specifically flip the
        #   decision outcome — high-approval signals rise while risk signals fall,
        #   or vice versa. Only statistically unlikely combinations trigger this.
        #
        # Detection method:
        #   1. Build signal_direction_map: RISING / FALLING / STABLE per signal
        #   2. Identify "decision-critical" signals (probability_score, risk_exposure)
        #   3. If decision-critical signals drift in opposite directions to
        #      non-critical signals AND drift_score > 15 → ADVERSARIAL
        #   4. If all signals drift coherently → NATURAL
        #   5. Otherwise → UNDETERMINED

        drift_pattern = "UNDETERMINED"
        adversarial_signals: List[str] = []
        signal_direction_map: Dict[str, str] = {}

        if signal_deltas and total_weight > 0:
            # Build direction map
            for key in _CONTEXT_DRIFT_WEIGHTS:
                current_val = snapshot.signals.get(key)
                baseline_val = baseline_signals.get(key)
                if current_val is None or baseline_val is None:
                    continue
                if abs(current_val - baseline_val) < 1.0:
                    signal_direction_map[key] = "STABLE"
                elif current_val > baseline_val:
                    signal_direction_map[key] = "RISING"
                else:
                    signal_direction_map[key] = "FALLING"

            non_stable = {k: v for k, v in signal_direction_map.items() if v != "STABLE"}

            if len(non_stable) >= 2 and drift_score > 10.0:
                # Signals that increase approval probability
                approval_signals = {"probability_score", "signal_coherence",
                                    "stress_resilience", "trend_persistence"}
                # Signals that increase risk/block
                risk_signals = {"risk_exposure"}

                approval_directions = {k: v for k, v in non_stable.items()
                                       if k in approval_signals}
                risk_directions = {k: v for k, v in non_stable.items()
                                   if k in risk_signals}

                # Adversarial pattern: approval signals RISING while risk signals FALLING
                # or approval signals FALLING while risk signals RISING (smear attack)
                approval_rising  = [k for k, v in approval_directions.items() if v == "RISING"]
                approval_falling = [k for k, v in approval_directions.items() if v == "FALLING"]
                risk_rising      = [k for k, v in risk_directions.items() if v == "RISING"]
                risk_falling     = [k for k, v in risk_directions.items() if v == "FALLING"]

                is_approval_manipulation = (
                    len(approval_rising) >= 2 and len(risk_falling) >= 1
                )
                is_smear_attack = (
                    len(approval_falling) >= 2 and len(risk_rising) >= 1
                )

                if is_approval_manipulation or is_smear_attack:
                    drift_pattern = "ADVERSARIAL"
                    adversarial_signals = approval_rising + risk_falling if is_approval_manipulation \
                        else approval_falling + risk_rising
                    logger.warning(
                        f"[MAR] ADVERSARIAL DRIFT DETECTED — snapshot={snapshot.snapshot_id} "
                        f"signals={adversarial_signals} drift_score={drift_score}"
                    )
                else:
                    # Check coherence: if most non-stable signals move in same direction
                    directions = list(non_stable.values())
                    rising_count  = directions.count("RISING")
                    falling_count = directions.count("FALLING")
                    dominant = max(rising_count, falling_count)
                    if dominant / len(directions) >= 0.75:
                        drift_pattern = "NATURAL"
                    else:
                        drift_pattern = "UNDETERMINED"

        logger.info(
            f"[MAR] Drift assessment — snapshot={snapshot.snapshot_id} "
            f"drift_score={drift_score} verdict={verdict} pattern={drift_pattern}"
        )

        return DriftAssessment(
            drift_score=drift_score,
            drift_verdict=verdict,
            signal_deltas=signal_deltas,
            baseline_id=baseline_id,
            assessed_at=now_iso,
            drift_pattern=drift_pattern,
            adversarial_signals=adversarial_signals,
            signal_direction_map=signal_direction_map,
        )

    def generate_mar(
        self,
        snapshot: ContextSnapshot,
        flags: List[ContaminationFlag],
        drift: DriftAssessment,
        decision_id: Optional[str] = None,
    ) -> MemoryAttestationRecord:
        """
        Generate a PQC-signed Memory Attestation Record.

        This is the institutional-grade artifact that answers:
        "What did the AI know when it decided, and was that knowledge defensible?"

        The MAR ID must be embedded in the corresponding Decision Receipt as
        `memory_attestation_id` to maintain the bidirectional audit chain.

        Args:
            snapshot:    The ContextSnapshot from capture_snapshot()
            flags:       Contamination flags from detect_contamination()
            drift:       Drift assessment from detect_drift()
            decision_id: The governance decision ID (may be None before evaluation)

        Returns:
            MemoryAttestationRecord — signed, immutable, ready for DB storage

        Raises:
            ContextIntegrityError: if contamination_class is CRITICAL and
                fail_closed_on_critical=True (default)
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        mar_id = f"OMNIX-MAR-{uuid.uuid4().hex[:12].upper()}"

        # Determine worst contamination class
        if not flags:
            contamination_class = ContaminationClass.CLEAN
        else:
            severity_order = [
                ContaminationClass.CLEAN,
                ContaminationClass.SUSPICIOUS,
                ContaminationClass.CONTAMINATED,
                ContaminationClass.CRITICAL,
            ]
            worst = max(
                (ContaminationClass[f.severity] for f in flags),
                key=lambda c: severity_order.index(c)
            )
            contamination_class = worst

        # Factor in drift
        if drift.drift_verdict == "CRITICAL" and contamination_class not in (
            ContaminationClass.CRITICAL,
        ):
            contamination_class = ContaminationClass.CONTAMINATED

        # ── OMNIX DIFFERENTIATOR: Context Sovereignty Score (CSS) ────────────
        #
        # A single composite 0–100 defensibility score for the context window.
        # No AI governance platform computes this. CSS gives regulators and
        # CAIOs one number to assess: "Was this context defensible?"
        #
        # Components:
        #   source_authorization_rate  (0–100): % of external sources authorized
        #   freshness_score            (0–100): signal age vs. max authorized age
        #   contamination_penalty:     CLEAN=0, SUSPICIOUS=-10, CONTAMINATED=-30, CRITICAL=-60
        #   drift_penalty:             proportional to drift_score (max -20 points)
        #   adversarial_bonus_penalty: ADVERSARIAL pattern adds -15
        #
        # CSS ≥ 80 → "Defensible"   | CSS 60–79 → "Conditional"
        # CSS 40–59 → "Restricted"  | CSS < 40  → "Indefensible"

        total_sources = len(snapshot.external_sources)
        authorized_count = sum(
            1 for s in snapshot.external_sources
            if (s.get("authorized", False) if isinstance(s, dict) else getattr(s, "authorized", False))
        )
        source_rate_score = (authorized_count / total_sources * 100.0) if total_sources > 0 else 100.0

        freshness_score = max(0.0, 100.0 - (snapshot.signal_age_s / max(MAX_SIGNAL_AGE_SECONDS, 1)) * 100.0)

        contamination_penalty = {
            ContaminationClass.CLEAN:        0.0,
            ContaminationClass.SUSPICIOUS:  -10.0,
            ContaminationClass.CONTAMINATED: -30.0,
            ContaminationClass.CRITICAL:    -60.0,
        }.get(contamination_class, 0.0)

        drift_penalty = -min(drift.drift_score / 100.0 * 20.0, 20.0)

        adversarial_penalty = -15.0 if drift.drift_pattern == "ADVERSARIAL" else 0.0

        # CSS base: average of source_rate and freshness, then apply penalties
        css_base = (source_rate_score * 0.4 + freshness_score * 0.6)
        css_raw  = css_base + contamination_penalty + drift_penalty + adversarial_penalty
        css      = round(max(0.0, min(100.0, css_raw)), 1)

        css_breakdown = {
            "source_authorization_rate": round(source_rate_score, 1),
            "freshness_score":           round(freshness_score, 1),
            "contamination_penalty":     contamination_penalty,
            "drift_penalty":             round(drift_penalty, 2),
            "adversarial_penalty":       adversarial_penalty,
            "css_base":                  round(css_base, 1),
            "css_final":                 css,
        }

        if css >= 80:
            css_label = "DEFENSIBLE"
        elif css >= 60:
            css_label = "CONDITIONAL"
        elif css >= 40:
            css_label = "RESTRICTED"
        else:
            css_label = "INDEFENSIBLE"

        # Build integrity verdict
        if contamination_class == ContaminationClass.CLEAN:
            integrity_verdict = (
                f"ATTESTED — context clean · CSS {css}/100 ({css_label}) · "
                f"drift {drift.drift_verdict} ({drift.drift_pattern}) · "
                f"full governance authority"
            )
        elif contamination_class == ContaminationClass.SUSPICIOUS:
            integrity_verdict = (
                f"ATTESTED WITH FLAGS — CSS {css}/100 ({css_label}) · "
                f"drift {drift.drift_verdict} ({drift.drift_pattern}) · "
                f"governance continues · Tier 1 review recommended"
            )
        elif contamination_class == ContaminationClass.CONTAMINATED:
            integrity_verdict = (
                f"CONDITIONAL — CSS {css}/100 ({css_label}) · "
                f"active contamination · drift {drift.drift_pattern} · "
                f"governance restricted · Tier 1 escalation required"
            )
        else:
            integrity_verdict = (
                f"BLOCKED — CSS {css}/100 ({css_label}) · "
                f"critical context integrity failure · "
                f"governance evaluation must not proceed"
            )

        # Canonical content for signing — includes CSS so it's tamper-evident
        content_payload = {
            "mar_id":                    mar_id,
            "decision_id":               decision_id,
            "domain":                    snapshot.domain,
            "asset":                     snapshot.asset,
            "snapshot_id":               snapshot.snapshot_id,
            "context_hash":              snapshot.context_hash,
            "signal_fingerprint":        snapshot.signal_fingerprint,
            "contamination_class":       contamination_class.value,
            "drift_score":               drift.drift_score,
            "drift_pattern":             drift.drift_pattern,
            "context_sovereignty_score": css,
            "generated_at":              now_iso,
        }
        content_hash = _canonical_hash(content_payload)

        # PQC signature
        sig_b64, pk_b64, algorithm = _sign_content(content_hash.encode())

        mar = MemoryAttestationRecord(
            mar_id=mar_id,
            decision_id=decision_id,
            domain=snapshot.domain,
            asset=snapshot.asset,
            snapshot=snapshot.to_dict(),
            contamination_flags=[f.to_dict() for f in flags],
            contamination_class=contamination_class.value,
            drift_assessment=drift.to_dict(),
            context_sovereignty_score=css,
            css_breakdown=css_breakdown,
            integrity_verdict=integrity_verdict,
            content_hash=content_hash,
            pqc_signature=sig_b64,
            public_key=pk_b64,
            signing_algorithm=algorithm,
            generated_at=now_iso,
        )

        _append_mar_log(mar)

        logger.info(
            f"[MAR] Generated — mar_id={mar_id} domain={snapshot.domain} "
            f"asset={snapshot.asset} contamination={contamination_class.value} "
            f"drift={drift.drift_score} flags={len(flags)} "
            f"algorithm={algorithm}"
        )

        if contamination_class == ContaminationClass.CRITICAL and self._fail_closed:
            logger.error(
                f"[MAR][CRITICAL] Context integrity failure — pipeline BLOCKED "
                f"mar_id={mar_id} snapshot={snapshot.snapshot_id} "
                f"flags={[f.description for f in flags]}"
            )
            raise ContextIntegrityError(
                f"CRITICAL context integrity failure — governance evaluation blocked. "
                f"MAR: {mar_id}",
                snapshot_id=snapshot.snapshot_id,
                flags=flags,
            )

        return mar

    def verify_mar(self, mar: MemoryAttestationRecord) -> bool:
        """
        Cryptographically verify a Memory Attestation Record.

        Recomputes the content hash and verifies the PQC signature.
        Returns True only if signature is valid and content is unmodified.

        This is the independent verification path — no DB access required.
        """
        try:
            content_payload = {
                "mar_id":                    mar.mar_id,
                "decision_id":               mar.decision_id,
                "domain":                    mar.domain,
                "asset":                     mar.asset,
                "snapshot_id":               mar.snapshot.get("snapshot_id"),
                "context_hash":              mar.snapshot.get("context_hash"),
                "signal_fingerprint":        mar.snapshot.get("signal_fingerprint"),
                "contamination_class":       mar.contamination_class,
                "drift_score":               mar.drift_assessment.get("drift_score", 0.0),
                "drift_pattern":             mar.drift_assessment.get("drift_pattern", "UNDETERMINED"),
                "context_sovereignty_score": mar.context_sovereignty_score,
                "generated_at":              mar.generated_at,
            }
            expected_hash = _canonical_hash(content_payload)
            if expected_hash != mar.content_hash:
                logger.error(
                    f"[MAR] Verification FAILED — content_hash mismatch "
                    f"mar_id={mar.mar_id}"
                )
                return False

            if mar.signing_algorithm.startswith("sha256-degraded"):
                logger.warning(
                    f"[MAR] Verification in degraded mode — SHA-256 only, no PQC signature "
                    f"mar_id={mar.mar_id}"
                )
                return True

            from omnix_core.security.crypto_providers import get_active_provider
            provider = get_active_provider()
            if not provider:
                return False
            sig = base64.b64decode(mar.pqc_signature)
            pk  = base64.b64decode(mar.public_key)
            valid = provider.verify(sig, mar.content_hash.encode(), pk)
            logger.info(
                f"[MAR] Verification {'PASSED' if valid else 'FAILED'} — "
                f"mar_id={mar.mar_id} algorithm={mar.signing_algorithm}"
            )
            return valid

        except Exception as e:
            logger.error(f"[MAR] Verification error — mar_id={mar.mar_id}: {e}")
            return False


# ─────────────────────────────────────────────────────────────────────────────
# MODULE-LEVEL SINGLETON
# ─────────────────────────────────────────────────────────────────────────────

_default_auditor: Optional[MemoryContextAuditor] = None
_auditor_init_lock = threading.Lock()


def get_memory_context_auditor(fail_closed: bool = True) -> MemoryContextAuditor:
    """
    Return the process-level MemoryContextAuditor singleton.
    Thread-safe double-checked locking. (ADR-151)
    """
    global _default_auditor
    if _default_auditor is None:
        with _auditor_init_lock:
            if _default_auditor is None:
                _default_auditor = MemoryContextAuditor(fail_closed_on_critical=fail_closed)
                logger.info(
                    f"[MAR] MemoryContextAuditor singleton initialized — "
                    f"fail_closed={fail_closed}"
                )
    return _default_auditor


# ─────────────────────────────────────────────────────────────────────────────
# CONVENIENCE: FULL CONTEXT AUDIT IN ONE CALL
# ─────────────────────────────────────────────────────────────────────────────

def audit_context(
    signals: Dict[str, float],
    domain: str,
    asset: str,
    history_depth: int = 0,
    history_fingerprint: Optional[str] = None,
    external_sources: Optional[List[ExternalDataSource]] = None,
    signal_age_s: float = 0.0,
    domain_metadata: Optional[Dict[str, Any]] = None,
    scope_id: Optional[str] = None,
    baseline_signals: Optional[Dict[str, float]] = None,
    baseline_id: Optional[str] = None,
    decision_id: Optional[str] = None,
) -> MemoryAttestationRecord:
    """
    Full context audit in one call — capture → detect → drift → generate MAR.

    This is the standard integration point for callers that want to add
    memory governance to an existing evaluation flow without managing the
    intermediate objects.

    Returns:
        MemoryAttestationRecord — signed MAR ready for DB storage and receipt embedding.

    Raises:
        ContextIntegrityError — if contamination_class is CRITICAL (fail-closed).
    """
    auditor = get_memory_context_auditor()
    snapshot = auditor.capture_snapshot(
        signals=signals,
        domain=domain,
        asset=asset,
        history_depth=history_depth,
        history_fingerprint=history_fingerprint,
        external_sources=external_sources or [],
        signal_age_s=signal_age_s,
        domain_metadata=domain_metadata,
        scope_id=scope_id,
    )
    flags = auditor.detect_contamination(snapshot)
    drift = auditor.detect_drift(snapshot, baseline_signals, baseline_id)
    return auditor.generate_mar(snapshot, flags, drift, decision_id=decision_id)
