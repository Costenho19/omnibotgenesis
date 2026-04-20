"""
OMNIX Structural Admissibility Engine (SAE) — Layer 0

Patent Reference: OMNIX-PAT-2026-015
  "Structural Admissibility Engine for Automated Decision Governance Systems
   with Pre-Pipeline Schema Validation, Enumerated Constraint Encoding,
   and Zero-Bypass Boundary Enforcement"

Inventor: Harold Alberto Nunes Rodelo — OMNIX QUANTUM LTD, United Kingdom

Architecture position:
  Layer 0  — Structural Admissibility Engine  ← THIS MODULE
  Layer 1  — OMNIX Runtime Pipeline (CP-0 … CP-11 + TIE)
  Layer 2  — Trajectory Invariant Engine
  Layer 3  — PQC Evidence & Receipt Layer

Core guarantee (Zero-Bypass Boundary, §4.1 of patent):
  An EvaluationRequest object — the only valid input to Layer 1 — can ONLY
  be constructed by StructuralAdmissibilityValidator.validate_and_construct().
  No code path, configuration flag, or operational state can produce a valid
  EvaluationRequest without passing through the full SAV constraint evaluation.
  Inadmissible requests are unrepresentable as system objects, not merely
  intercepted at runtime.

Components implemented (per patent §II–§VI):
  A — Structural Constraint Schema (SCS): declarative constraint registry
  B — Structural Admissibility Validator (SAV): pre-construction evaluator
  C — Zero-Bypass Boundary Enforcement (ZBE): private constructor sentinel
  D — Structured Rejection with Constraint Provenance (SRCP): machine-readable rejection
  E — Composable Cross-Domain Constraint Architecture (CCCA): domain-agnostic registry

See also: docs/adr/ADR-092-structural-admissibility-engine.md
"""
from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger("OMNIX.SAE")


# ── Enums ───────────────────────────────────────────────────────────────────────

class ConstraintResult(str, Enum):
    PERMITTED   = "PERMITTED"
    PROHIBITED  = "PROHIBITED"
    CONDITIONAL = "CONDITIONAL"


class ConstraintClass(str, Enum):
    SANCTIONS             = "SANCTIONS"
    JURISDICTION_ASSET    = "JURISDICTION_ASSET"
    JURISDICTION_OPERATION = "JURISDICTION_OPERATION"
    ETHICAL_SHARIA        = "ETHICAL_SHARIA"
    ETHICAL_ESG           = "ETHICAL_ESG"
    CLIENT_SPECIFIC       = "CLIENT_SPECIFIC"


class EvaluationMode(str, Enum):
    FAST_FAIL  = "FAST_FAIL"
    FULL_AUDIT = "FULL_AUDIT"


class SAEOverride(str, Enum):
    """
    Internal-only feature flag for Layer 0.

    UNSET     — default: honour compliance_config.layer0_enabled / SAE_ENABLED env var
    FORCE_ON  — Layer 0 always active regardless of what any API caller passes
    FORCE_OFF — Layer 0 always inactive (emergency operator bypass)

    Only settable via set_sae_override() — not exposed through any API endpoint.
    """
    UNSET     = "UNSET"
    FORCE_ON  = "FORCE_ON"
    FORCE_OFF = "FORCE_OFF"


class Domain(str, Enum):
    FINANCIAL_TRADING = "FINANCIAL_TRADING"
    INSURANCE         = "INSURANCE"
    MEDICAL_AI        = "MEDICAL_AI"
    REAL_ESTATE       = "REAL_ESTATE"
    ENERGY            = "ENERGY"
    AUTONOMOUS_AGENT  = "AUTONOMOUS_AGENT"
    STABLECOIN        = "STABLECOIN"
    GENERIC           = "GENERIC"


# ── Layer 0 Business Metrics ────────────────────────────────────────────────────

class Layer0Metrics:
    """
    Thread-safe in-memory counters for Layer 0 business reporting.

    Tracks per-domain admission and block rates — the raw material for investor
    dashboards and regulatory audit arguments.

    Usage:
        from omnix_core.governance.structural_admissibility_engine import get_layer0_metrics
        m = get_layer0_metrics()
        report = m.snapshot()  → dict keyed by domain
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._total:   dict[str, int] = defaultdict(int)
        self._blocked: dict[str, int] = defaultdict(int)
        self._blocked_by_class: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

    def record_admitted(self, domain: str) -> None:
        domain = domain.upper()
        with self._lock:
            self._total[domain] += 1

    def record_blocked(self, domain: str, constraint_class: str) -> None:
        domain = domain.upper()
        with self._lock:
            self._total[domain] += 1
            self._blocked[domain] += 1
            self._blocked_by_class[domain][constraint_class] += 1

    def snapshot(self) -> dict[str, Any]:
        """Return a point-in-time copy of all metrics."""
        with self._lock:
            result: dict[str, Any] = {}
            for domain in sorted(self._total):
                total   = self._total[domain]
                blocked = self._blocked[domain]
                result[domain] = {
                    "total":            total,
                    "admitted":         total - blocked,
                    "blocked":          blocked,
                    "block_rate_pct":   round(100.0 * blocked / total, 2) if total else 0.0,
                    "blocked_by_class": dict(self._blocked_by_class[domain]),
                }
            return result

    def reset(self) -> None:
        """Reset all counters (e.g., between test runs or daily roll-overs)."""
        with self._lock:
            self._total.clear()
            self._blocked.clear()
            self._blocked_by_class.clear()


# ── Layer 0 Snapshot Store ───────────────────────────────────────────────────────

_LAYER0_DEMO_TAGLINE = (
    "Layer 0 doesn't block decisions — "
    "it prevents invalid decisions from ever existing."
)

_SNAPSHOT_MAX_ENTRIES = 288   # 24 h at 5-min intervals

class Layer0SnapshotStore:
    """
    Ring-buffer that records periodic Layer 0 metric snapshots.

    A background daemon thread (started at module import, disabled in TESTING mode)
    calls record() every `interval_minutes` and stores the result in a bounded deque.
    History is available via history() — ready for time-series charts, pitch decks,
    and regulatory audit packages.
    """

    def __init__(self, max_entries: int = _SNAPSHOT_MAX_ENTRIES) -> None:
        self._lock     = threading.Lock()
        self._entries: deque = deque(maxlen=max_entries)

    def record(self, metrics: Layer0Metrics) -> None:
        """Capture a timestamped snapshot and append to the ring buffer."""
        raw = metrics.snapshot()
        if not raw:
            return

        gt = 0; ga = 0; gb = 0; gbc: dict = {}
        for stat in raw.values():
            gt += stat["total"];  ga += stat["admitted"];  gb += stat["blocked"]
            for cls, cnt in stat["blocked_by_class"].items():
                gbc[cls] = gbc.get(cls, 0) + cnt

        entry = {
            "recorded_at":     datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "global": {
                "total":         gt,
                "admitted":      ga,
                "blocked":       gb,
                "block_rate_pct": round(100.0 * gb / gt, 2) if gt else 0.0,
                "blocked_by_class": dict(sorted(gbc.items(), key=lambda x: -x[1])),
            },
            "domains": {
                domain: {
                    "total":          stat["total"],
                    "admitted":       stat["admitted"],
                    "blocked":        stat["blocked"],
                    "block_rate_pct": stat["block_rate_pct"],
                }
                for domain, stat in raw.items()
            },
        }
        with self._lock:
            self._entries.append(entry)

    def history(self, last_n: int | None = None) -> list[dict]:
        """Return stored snapshots (oldest first).  Pass last_n to limit count."""
        with self._lock:
            entries = list(self._entries)
        return entries if last_n is None else entries[-last_n:]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


# Module-level singletons — access via get_layer0_metrics() / get/set_sae_override()
_layer0_metrics    = Layer0Metrics()
_layer0_snapshots  = Layer0SnapshotStore()
_sae_override      = SAEOverride.UNSET
_sae_override_lock = threading.Lock()
_snapshot_interval_minutes: int = 5


def get_layer0_metrics() -> Layer0Metrics:
    """Return the shared Layer 0 metrics instance."""
    return _layer0_metrics


def get_layer0_snapshot_history(last_n: int | None = None) -> list[dict]:
    """
    Return recorded Layer 0 metric snapshots, oldest first.

    Each entry: {recorded_at, global: {total, admitted, blocked, block_rate_pct,
    blocked_by_class}, domains: {DOMAIN: {...}}}

    Args:
        last_n: if given, return only the most recent N snapshots.
    """
    return _layer0_snapshots.history(last_n)


def _snapshot_scheduler(interval_minutes: int) -> None:
    """Daemon thread: records a Layer 0 snapshot every `interval_minutes`."""
    interval_secs = interval_minutes * 60
    while True:
        time.sleep(interval_secs)
        try:
            _layer0_snapshots.record(_layer0_metrics)
        except Exception:
            pass


def _start_snapshot_scheduler(interval_minutes: int = 5) -> None:
    """
    Start the background snapshot thread.

    Called once at module import.  Skipped in TESTING mode so pytest runs
    do not keep threads alive between test sessions.
    """
    import os as _os
    if _os.environ.get("TESTING", "").lower() in ("1", "true", "yes"):
        return
    t = threading.Thread(
        target=_snapshot_scheduler,
        args=(interval_minutes,),
        daemon=True,
        name="SAE-Layer0-SnapshotScheduler",
    )
    t.start()
    logger.info(
        f"[SAE] Layer0 snapshot scheduler started — interval={interval_minutes}min "
        f"max_entries={_SNAPSHOT_MAX_ENTRIES}"
    )


_start_snapshot_scheduler(_snapshot_interval_minutes)


def set_sae_override(override: SAEOverride) -> None:
    """
    Set the internal Layer 0 activation override.

    INTERNAL USE ONLY. Must never be called from an API handler —
    it is only for server initialisation and operator control.

    SAEOverride.FORCE_ON  → Layer 0 active for ALL requests, ignoring caller flags.
    SAEOverride.FORCE_OFF → Layer 0 inactive for ALL requests (emergency bypass).
    SAEOverride.UNSET     → restore normal behaviour (compliance_config / SAE_ENABLED env).
    """
    global _sae_override
    with _sae_override_lock:
        prev = _sae_override
        _sae_override = override
    logger.info(f"[SAE] Override changed: {prev.value} → {override.value}")


def get_sae_override() -> SAEOverride:
    """Return the current internal Layer 0 override state."""
    with _sae_override_lock:
        return _sae_override


# ── Exceptions ──────────────────────────────────────────────────────────────────

class StructuralAdmissibilityViolation(Exception):
    """
    Raised when code attempts to construct an EvaluationRequest directly,
    bypassing the StructuralAdmissibilityValidator (Zero-Bypass violation).

    This exception should NEVER be caught silently. It indicates a programming
    error — a code path that bypasses Layer 0 governance.
    """


# ── Data structures ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ConstraintViolation:
    """
    Component D — Structured Rejection with Constraint Provenance (SRCP).
    Machine-readable record of a single constraint violation, per patent §V.
    """
    constraint_id:      str
    constraint_class:   ConstraintClass
    description:        str
    regulatory_source:  str
    input_fields:       tuple[str, ...]
    input_values:       dict[str, Any]
    resolution:         str

    def to_dict(self) -> dict:
        return {
            "constraint_id":     self.constraint_id,
            "constraint_class":  self.constraint_class.value,
            "description":       self.description,
            "regulatory_source": self.regulatory_source,
            "input_fields":      list(self.input_fields),
            "input_values":      self.input_values,
            "resolution":        self.resolution,
        }


@dataclass
class StructuredRejectionRecord:
    """
    Component D — Full rejection record returned by SAV when a proposed
    request is structurally inadmissible. Machine-readable, audit-ready.
    """
    violations:               list[ConstraintViolation]
    layer_0_processing_ms:    float = 0.0
    admissibility:            str   = "INADMISSIBLE"
    rejected_at:              str   = "LAYER_0_STRUCTURAL_ADMISSIBILITY"
    pipeline_entry:           bool  = False
    audit_id:                 str   = field(default_factory=lambda: uuid.uuid4().hex[:12].upper())
    evaluated_at:             str   = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "admissibility":          self.admissibility,
            "rejected_at":            self.rejected_at,
            "pipeline_entry":         self.pipeline_entry,
            "audit_id":               self.audit_id,
            "evaluated_at":           self.evaluated_at,
            "layer_0_processing_ms":  round(self.layer_0_processing_ms, 3),
            "violations":             [v.to_dict() for v in self.violations],
        }

    @property
    def primary_violation(self) -> ConstraintViolation | None:
        return self.violations[0] if self.violations else None

    def __str__(self) -> str:
        if not self.violations:
            return "INADMISSIBLE (no violation detail)"
        v = self.violations[0]
        return (
            f"INADMISSIBLE [{v.constraint_class.value}] {v.constraint_id}: "
            f"{v.description}"
        )


@dataclass
class ProposedRequest:
    """
    An unvalidated decision request submitted by external code to the SAV.
    This object is NOT an EvaluationRequest — it has not passed Layer 0.

    Fields are domain-agnostic:
      subject     — the entity being acted upon (asset in trading, property in RE, etc.)
      operation   — the type of action being requested
      jurisdiction — the regulatory context
      domain      — which OMNIX vertical this request belongs to
      client_id   — client identifier for client-specific constraint lookup
      ethical_flags — ["SHARIA"] | ["ESG"] | [] — active ethical constraint sets
      metadata    — domain-specific additional fields (position_size, licenses, etc.)
    """
    subject:        str
    operation:      str
    jurisdiction:   str
    domain:         str  = Domain.GENERIC.value
    client_id:      str  = "GENERIC"
    ethical_flags:  list[str] = field(default_factory=list)
    metadata:       dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.subject    = self.subject.upper().strip()
        self.operation  = self.operation.upper().strip()
        self.jurisdiction = self.jurisdiction.upper().strip()
        self.domain     = self.domain.upper().strip()


# ── Component C: Zero-Bypass EvaluationRequest ─────────────────────────────────

class EvaluationRequest:
    """
    Structural admissibility-enforced evaluation request — Layer 0 output.

    CONSTRUCTION IS PRIVATE. This object can only be created by
    StructuralAdmissibilityValidator.validate_and_construct().

    Any attempt to construct an EvaluationRequest directly raises
    StructuralAdmissibilityViolation — a non-swallowable exception.

    This is the Zero-Bypass Boundary Enforcement (ZBE) mechanism described
    in patent §IV. The sentinel token is private to this class and
    StructuralAdmissibilityValidator — it is never exposed via public API.

    Once constructed, the request is immutable (frozen) — no field can be
    modified after Layer 0 has validated it.
    """
    # Private sentinel — accessible ONLY within this module.
    # StructuralAdmissibilityValidator holds a reference via the class.
    _SAV_TOKEN: object = object()

    def __init__(
        self,
        _token: object,
        proposed: ProposedRequest,
        validated_at: str,
    ) -> None:
        if _token is not EvaluationRequest._SAV_TOKEN:
            raise StructuralAdmissibilityViolation(
                "EvaluationRequest must be constructed via "
                "StructuralAdmissibilityValidator.validate_and_construct(). "
                "Direct instantiation is prohibited — Zero-Bypass Boundary "
                "Enforcement (OMNIX-PAT-2026-015 §4.1)."
            )
        object.__setattr__(self, "_frozen", False)
        object.__setattr__(self, "subject",       proposed.subject)
        object.__setattr__(self, "operation",     proposed.operation)
        object.__setattr__(self, "jurisdiction",  proposed.jurisdiction)
        object.__setattr__(self, "domain",        proposed.domain)
        object.__setattr__(self, "client_id",     proposed.client_id)
        object.__setattr__(self, "ethical_flags", tuple(proposed.ethical_flags))
        object.__setattr__(self, "metadata",      dict(proposed.metadata))
        object.__setattr__(self, "validated_at",  validated_at)
        object.__setattr__(self, "evaluation_id", f"SAE-{uuid.uuid4().hex[:10].upper()}")
        object.__setattr__(self, "_frozen", True)

    def __setattr__(self, key: str, value: Any) -> None:
        if getattr(self, "_frozen", False):
            raise AttributeError(
                f"EvaluationRequest is immutable after Layer 0 validation. "
                f"Cannot set '{key}' (OMNIX-PAT-2026-015 §4.2)."
            )
        object.__setattr__(self, key, value)

    def __repr__(self) -> str:
        return (
            f"EvaluationRequest(id={self.evaluation_id} "
            f"subject={self.subject} op={self.operation} "
            f"jur={self.jurisdiction} domain={self.domain})"
        )


# ── Component A: Structural Constraint Schema (SCS) ────────────────────────────
# Constraint data is loaded from existing authoritative sources (jurisdiction_gate,
# sharia_gate) and extended with the SAE-specific constraint format.

def _build_sanctions_constraints() -> list[dict]:
    """
    SANCTIONS class: highest priority, unconditional PROHIBITED.
    Loaded from jurisdiction_gate.OFAC_SANCTIONED_ASSETS (ADR-068).
    """
    try:
        from omnix_core.governance.jurisdiction_gate import OFAC_SANCTIONED_ASSETS
        sanctioned = frozenset(OFAC_SANCTIONED_ASSETS)
    except Exception:
        sanctioned = frozenset({
            "TORNADO", "TORNADO_CASH", "TORN", "SINBAD", "BLENDER",
            "CHIPMIXER", "RAILGUN", "RAIL", "AZTEC", "XMR_MIXER",
        })

    def _check(proposed: ProposedRequest) -> ConstraintViolation | None:
        asset = proposed.subject
        if asset in sanctioned or any(s in asset for s in ("MIXER", "TUMBLER")):
            return ConstraintViolation(
                constraint_id=f"SN-OFAC-{asset}-001",
                constraint_class=ConstraintClass.SANCTIONS,
                description=(
                    f"Asset {asset} appears on OFAC SDN / EU Consolidated / "
                    "UN Security Council sanctions list."
                ),
                regulatory_source=(
                    "OFAC SDN List (31 C.F.R. Parts 500-598); "
                    "EU Consolidated Sanctions List; "
                    "UN Security Council Consolidated List"
                ),
                input_fields=("subject",),
                input_values={"subject": asset},
                resolution=(
                    f"{asset} is unconditionally prohibited in all jurisdictions. "
                    "Select a non-sanctioned asset."
                ),
            )
        return None

    return [{"class": ConstraintClass.SANCTIONS, "fn": _check}]


def _build_jurisdiction_asset_constraints() -> list[dict]:
    """
    JURISDICTION_ASSET class: encoded per-jurisdiction asset prohibitions.
    Loaded from jurisdiction_gate.JURISDICTION_RULES.
    """
    try:
        from omnix_core.governance.jurisdiction_gate import JURISDICTION_RULES
        rules = JURISDICTION_RULES
    except Exception:
        rules = {}

    def _check(proposed: ProposedRequest) -> ConstraintViolation | None:
        jur   = proposed.jurisdiction
        asset = proposed.subject
        rule  = rules.get(jur)
        if rule is None:
            return None
        prohibited: set[str] = rule.get("prohibited_assets", set())
        if asset in prohibited:
            return ConstraintViolation(
                constraint_id=f"JA-{jur}-{asset}-001",
                constraint_class=ConstraintClass.JURISDICTION_ASSET,
                description=(
                    f"Asset {asset} is prohibited in {jur} jurisdiction "
                    f"({rule.get('description', '')})"
                ),
                regulatory_source=rule.get("description", f"{jur} regulatory framework"),
                input_fields=("subject", "jurisdiction"),
                input_values={"subject": asset, "jurisdiction": jur},
                resolution=(
                    f"{asset} is not permitted in {jur}. "
                    "Select a compliant asset for this jurisdiction."
                ),
            )
        return None

    return [{"class": ConstraintClass.JURISDICTION_ASSET, "fn": _check}]


def _build_jurisdiction_operation_constraints() -> list[dict]:
    """
    JURISDICTION_OPERATION class: encoded per-jurisdiction operation restrictions.
    Loaded from jurisdiction_gate.JURISDICTION_RULES.
    """
    try:
        from omnix_core.governance.jurisdiction_gate import JURISDICTION_RULES
        rules = JURISDICTION_RULES
    except Exception:
        rules = {}

    OPERATION_MAP = {
        "SPOT":        "allowed_spot",
        "LEVERAGED":   "allowed_leveraged",
        "LEVERAGE":    "allowed_leveraged",
        "DERIVATIVES": "allowed_derivatives",
        "DERIVATIVE":  "allowed_derivatives",
        "SHORT":       "allowed_spot",
        "STAKING":     "allowed_spot",
        "LENDING":     "allowed_spot",
    }

    OPERATION_REGULATORY_SOURCE = {
        "LEVERAGED": {
            "UAE": "UAE VARA Regulations 2023 — leveraged virtual asset products require Broker/Dealer category",
            "UK":  "FCA PS20/10 — leveraged crypto derivatives banned for retail clients",
            "US":  "FinCEN / CFTC — retail leverage on crypto requires CFTC authorization",
            "GCC": "GCC VARA-aligned framework — leveraged products restricted",
            "SG":  "MAS SF(L)C Act — leveraged products require Capital Markets Services license",
        },
        "DERIVATIVES": {
            "UAE": "UAE VARA Regulations 2023 — derivative virtual asset products require additional licensing",
            "US":  "Commodity Exchange Act — crypto derivatives require CFTC registration",
            "GCC": "GCC VARA-aligned framework — derivative products restricted",
            "KR":  "South Korea VASP Act 2021 — derivative products prohibited",
        },
    }

    def _check(proposed: ProposedRequest) -> ConstraintViolation | None:
        jur  = proposed.jurisdiction
        op   = proposed.operation
        rule = rules.get(jur)
        if rule is None:
            return None
        rule_key = OPERATION_MAP.get(op)
        if rule_key is None:
            return None
        if not rule.get(rule_key, True):
            op_upper = op.split("_")[0]
            reg_source = (
                OPERATION_REGULATORY_SOURCE.get(op_upper, {}).get(jur)
                or rule.get("description", f"{jur} regulatory framework")
            )
            return ConstraintViolation(
                constraint_id=f"JO-{jur}-{op}-001",
                constraint_class=ConstraintClass.JURISDICTION_OPERATION,
                description=(
                    f"Operation {op} is not permitted in {jur} jurisdiction."
                ),
                regulatory_source=reg_source,
                input_fields=("operation", "jurisdiction"),
                input_values={"operation": op, "jurisdiction": jur},
                resolution=(
                    f"{op} is prohibited in {jur}. "
                    "Use SPOT operation or obtain required regulatory license."
                ),
            )
        return None

    return [{"class": ConstraintClass.JURISDICTION_OPERATION, "fn": _check}]


def _build_ethical_sharia_constraints() -> list[dict]:
    """
    ETHICAL_SHARIA class: active only when proposed.ethical_flags contains "SHARIA".
    Loaded from sharia_gate.HALAL_ASSETS / HARAM_ASSETS.
    """
    try:
        from omnix_core.governance.sharia_gate import HALAL_ASSETS, HARAM_ASSETS, HARAM_SECTORS
        halal   = frozenset(HALAL_ASSETS)
        haram   = frozenset(HARAM_ASSETS)
        sectors = frozenset(HARAM_SECTORS)
    except Exception:
        halal   = frozenset({"BTC", "ETH", "SOL", "ADA", "DOT", "AVAX", "LINK"})
        haram   = frozenset({"WBTC"})
        sectors = frozenset({"alcohol", "gambling", "weapons", "interest_bonds"})

    HARAM_OPERATIONS = {"LEVERAGED", "LEVERAGE", "DERIVATIVES", "DERIVATIVE", "SHORT"}

    def _check(proposed: ProposedRequest) -> ConstraintViolation | None:
        if "SHARIA" not in [f.upper() for f in proposed.ethical_flags]:
            return None
        asset = proposed.subject
        op    = proposed.operation

        if asset in haram:
            return ConstraintViolation(
                constraint_id=f"ES-HARAM-ASSET-{asset}-001",
                constraint_class=ConstraintClass.ETHICAL_SHARIA,
                description=f"Asset {asset} is classified HARAM under Sharia compliance framework.",
                regulatory_source=(
                    "AAOIFI Sharia Standards for Islamic Financial Institutions; "
                    "OMNIX Islamic Finance Compliance Framework (OMNIX-PAT-2026-003)"
                ),
                input_fields=("subject", "ethical_flags"),
                input_values={"subject": asset, "ethical_flags": proposed.ethical_flags},
                resolution=(
                    f"{asset} is not permissible under Sharia. "
                    f"Select from Halal-screened assets: BTC, ETH, SOL, ADA, DOT, AVAX."
                ),
            )

        if op in HARAM_OPERATIONS:
            return ConstraintViolation(
                constraint_id=f"ES-HARAM-OP-{op}-001",
                constraint_class=ConstraintClass.ETHICAL_SHARIA,
                description=(
                    f"Operation {op} is classified HARAM under Sharia compliance "
                    "framework (riba/gharar prohibition)."
                ),
                regulatory_source=(
                    "AAOIFI Sharia Standard No. 17 (Investment Sukuk); "
                    "IFSB-1 (Guiding Principles on Risk Management)"
                ),
                input_fields=("operation", "ethical_flags"),
                input_values={"operation": op, "ethical_flags": proposed.ethical_flags},
                resolution=(
                    f"{op} is prohibited under Sharia (riba/gharar). "
                    "Use SPOT operation on Halal-screened assets."
                ),
            )

        if halal and asset not in halal:
            return ConstraintViolation(
                constraint_id=f"ES-UNSCREENED-{asset}-001",
                constraint_class=ConstraintClass.ETHICAL_SHARIA,
                description=(
                    f"Asset {asset} has not been positively screened as HALAL. "
                    "For Sharia-compliant portfolios, only positively screened assets are admissible."
                ),
                regulatory_source=(
                    "AAOIFI Sharia Standards — Positive screening requirement for Islamic investment products"
                ),
                input_fields=("subject", "ethical_flags"),
                input_values={"subject": asset, "ethical_flags": proposed.ethical_flags},
                resolution=(
                    f"{asset} is not on the HALAL-screened asset list. "
                    "Contact compliance to initiate Sharia screening for this asset."
                ),
            )
        return None

    return [{"class": ConstraintClass.ETHICAL_SHARIA, "fn": _check}]


def _build_ethical_esg_constraints() -> list[dict]:
    """
    ETHICAL_ESG class: active when proposed.ethical_flags contains "ESG".
    ESG restrictions are configurable per client via metadata.
    """
    ESG_EXCLUDED_SECTORS: frozenset[str] = frozenset({
        "coal", "tobacco", "weapons", "gambling", "fossil_fuel",
        "deforestation", "child_labor",
    })

    ESG_HIGH_CARBON_ASSETS: frozenset[str] = frozenset({
        "XMR",
    })

    def _check(proposed: ProposedRequest) -> ConstraintViolation | None:
        if "ESG" not in [f.upper() for f in proposed.ethical_flags]:
            return None
        asset = proposed.subject
        client_excluded_sectors: set[str] = set(
            proposed.metadata.get("esg_excluded_sectors", [])
        )
        all_excluded = ESG_EXCLUDED_SECTORS | {s.lower() for s in client_excluded_sectors}

        asset_sector = proposed.metadata.get("asset_sector", "").lower()
        if asset_sector and asset_sector in all_excluded:
            return ConstraintViolation(
                constraint_id=f"EE-ESG-SECTOR-{asset_sector.upper()}-001",
                constraint_class=ConstraintClass.ETHICAL_ESG,
                description=(
                    f"Asset {asset} belongs to sector '{asset_sector}' which is "
                    "excluded by ESG screening criteria."
                ),
                regulatory_source=(
                    "Client ESG Policy; "
                    "UN PRI (Principles for Responsible Investment); "
                    "SFDR (EU Sustainable Finance Disclosure Regulation)"
                ),
                input_fields=("subject", "ethical_flags", "metadata.asset_sector"),
                input_values={"subject": asset, "asset_sector": asset_sector},
                resolution=(
                    f"Asset sector '{asset_sector}' is excluded under ESG policy. "
                    "Select an asset from ESG-compliant sectors."
                ),
            )

        if asset in ESG_HIGH_CARBON_ASSETS:
            return ConstraintViolation(
                constraint_id=f"EE-ESG-CARBON-{asset}-001",
                constraint_class=ConstraintClass.ETHICAL_ESG,
                description=(
                    f"Asset {asset} is classified as high-carbon footprint "
                    "and excluded under ESG energy constraints."
                ),
                regulatory_source="EU Taxonomy Regulation (2020/852); Client ESG Policy",
                input_fields=("subject", "ethical_flags"),
                input_values={"subject": asset, "ethical_flags": proposed.ethical_flags},
                resolution=(
                    f"{asset} is excluded under ESG energy constraints. "
                    "Select a lower-carbon asset."
                ),
            )
        return None

    return [{"class": ConstraintClass.ETHICAL_ESG, "fn": _check}]


# ── Component E: Composable Cross-Domain Constraint Architecture (CCCA) ─────────

class ConstraintRegistry:
    """
    Component E — Unified registry of all constraint evaluator functions.

    Constraints are registered by class and indexed at initialization.
    New constraint classes are added via register() without modifying the SAV
    evaluation logic — the architecture is extensible by addition, not modification.

    Evaluation order (per patent §III.2):
      1. SANCTIONS          (unconditional — highest priority)
      2. JURISDICTION_ASSET
      3. JURISDICTION_OPERATION
      4. ETHICAL_SHARIA
      5. ETHICAL_ESG
      6. CLIENT_SPECIFIC    (furthest restriction, never expansion)
    """
    EVALUATION_ORDER = [
        ConstraintClass.SANCTIONS,
        ConstraintClass.JURISDICTION_ASSET,
        ConstraintClass.JURISDICTION_OPERATION,
        ConstraintClass.ETHICAL_SHARIA,
        ConstraintClass.ETHICAL_ESG,
        ConstraintClass.CLIENT_SPECIFIC,
    ]

    def __init__(self) -> None:
        self._registry: dict[ConstraintClass, list[Callable]] = {
            c: [] for c in ConstraintClass
        }
        self._client_constraints: dict[str, list[Callable]] = {}
        self._initialized = False

    def _load_defaults(self) -> None:
        for entry in _build_sanctions_constraints():
            self._registry[entry["class"]].append(entry["fn"])
        for entry in _build_jurisdiction_asset_constraints():
            self._registry[entry["class"]].append(entry["fn"])
        for entry in _build_jurisdiction_operation_constraints():
            self._registry[entry["class"]].append(entry["fn"])
        for entry in _build_ethical_sharia_constraints():
            self._registry[entry["class"]].append(entry["fn"])
        for entry in _build_ethical_esg_constraints():
            self._registry[entry["class"]].append(entry["fn"])
        self._initialized = True
        logger.info(
            f"[SAE] ConstraintRegistry loaded — "
            + " | ".join(
                f"{c.value}={len(self._registry[c])}"
                for c in ConstraintClass
                if self._registry[c]
            )
        )

    def register(
        self,
        constraint_class: ConstraintClass,
        evaluator_fn: Callable[[ProposedRequest], ConstraintViolation | None],
    ) -> None:
        """
        Register a new constraint evaluator function.
        The function receives a ProposedRequest and returns a ConstraintViolation
        if the request violates the constraint, or None if it passes.
        """
        self._registry[constraint_class].append(evaluator_fn)
        logger.debug(f"[SAE] Registered constraint in class={constraint_class.value}")

    def register_client_constraint(
        self,
        client_id: str,
        evaluator_fn: Callable[[ProposedRequest], ConstraintViolation | None],
    ) -> None:
        """Register a client-specific constraint (furthest restriction only)."""
        if client_id not in self._client_constraints:
            self._client_constraints[client_id] = []
        self._client_constraints[client_id].append(evaluator_fn)

    def evaluate_all(
        self,
        proposed: ProposedRequest,
        mode: EvaluationMode,
    ) -> list[ConstraintViolation]:
        """
        Evaluate proposed request against all registered constraints.
        Returns list of all violations (FULL_AUDIT) or the first (FAST_FAIL).
        """
        if not self._initialized:
            self._load_defaults()

        violations: list[ConstraintViolation] = []

        for constraint_class in self.EVALUATION_ORDER:
            for fn in self._registry[constraint_class]:
                try:
                    violation = fn(proposed)
                except Exception as exc:
                    logger.error(
                        f"[SAE] Constraint evaluator error — "
                        f"class={constraint_class.value}: {exc}. "
                        "Failing closed: treating as PROHIBITED."
                    )
                    violation = ConstraintViolation(
                        constraint_id=f"{constraint_class.value}-EVAL-ERROR",
                        constraint_class=constraint_class,
                        description=f"Constraint evaluator raised exception: {exc}",
                        regulatory_source="Internal — SAE fail-closed policy",
                        input_fields=(),
                        input_values={},
                        resolution="Contact system administrator.",
                    )

                if violation is not None:
                    violations.append(violation)
                    if mode == EvaluationMode.FAST_FAIL:
                        return violations

        if proposed.client_id in self._client_constraints:
            for fn in self._client_constraints[proposed.client_id]:
                try:
                    violation = fn(proposed)
                except Exception as exc:
                    logger.error(f"[SAE] Client constraint error for {proposed.client_id}: {exc}")
                    violation = None
                if violation is not None:
                    violations.append(violation)
                    if mode == EvaluationMode.FAST_FAIL:
                        return violations

        return violations


# ── Component B: Structural Admissibility Validator (SAV) ───────────────────────

class StructuralAdmissibilityValidator:
    """
    Component B — The evaluation engine of the SAE.

    The SAV is the ONLY entity that can construct EvaluationRequest objects.
    It evaluates a ProposedRequest against the full ConstraintRegistry before
    constructing the EvaluationRequest. If any constraint is violated, no
    EvaluationRequest is constructed — the request is rejected at the boundary.

    This is the architectural mechanism that makes the zero-bypass property hold:
    because EvaluationRequest construction is gated behind this validator, and
    because this validator always performs the full constraint evaluation, there
    is no code path that can produce a valid EvaluationRequest for an inadmissible
    request.
    """

    def __init__(self, registry: ConstraintRegistry) -> None:
        self._registry = registry

    def validate_and_construct(
        self,
        proposed: ProposedRequest,
        mode: EvaluationMode = EvaluationMode.FAST_FAIL,
    ) -> EvaluationRequest | StructuredRejectionRecord:
        """
        Evaluate proposed request against the Structural Constraint Schema.

        If ADMISSIBLE: constructs and returns an EvaluationRequest — the
                       only valid input to Layer 1.
        If INADMISSIBLE: returns a StructuredRejectionRecord with full
                         constraint provenance. No EvaluationRequest is created.

        Args:
            proposed: The proposed decision request (not yet validated).
            mode:     FAST_FAIL (default) — halt at first violation.
                      FULL_AUDIT — collect all violations before returning.

        Returns:
            EvaluationRequest if admissible, StructuredRejectionRecord if not.
        """
        t_start = time.perf_counter()
        violations = self._registry.evaluate_all(proposed, mode)
        elapsed_ms = (time.perf_counter() - t_start) * 1000

        if violations:
            rejection = StructuredRejectionRecord(
                violations=violations,
                layer_0_processing_ms=round(elapsed_ms, 3),
            )
            logger.warning(
                f"[SAE] INADMISSIBLE — subject={proposed.subject} "
                f"op={proposed.operation} jur={proposed.jurisdiction} "
                f"domain={proposed.domain} | "
                f"violations={len(violations)} | "
                f"primary={violations[0].constraint_id} | "
                f"elapsed={elapsed_ms:.2f}ms"
            )
            return rejection

        validated_at = datetime.now(timezone.utc).isoformat()
        request = EvaluationRequest(
            _token=EvaluationRequest._SAV_TOKEN,
            proposed=proposed,
            validated_at=validated_at,
        )
        logger.info(
            f"[SAE] ADMISSIBLE — {request} | "
            f"mode={mode.value} | elapsed={elapsed_ms:.2f}ms"
        )
        return request


# ── Main SAE facade ─────────────────────────────────────────────────────────────

class StructuralAdmissibilityEngine:
    """
    Layer 0 — Structural Admissibility Engine (OMNIX-PAT-2026-015).

    Facade combining the ConstraintRegistry (Component A + E) and the
    StructuralAdmissibilityValidator (Component B) into a single entry point.

    Usage:
        sae = StructuralAdmissibilityEngine.get_instance()

        # Financial trading request
        proposed = ProposedRequest(
            subject="XMR",
            operation="SPOT",
            jurisdiction="UAE",
            domain="FINANCIAL_TRADING",
        )
        result = sae.validate(proposed)
        if isinstance(result, StructuredRejectionRecord):
            # Structurally inadmissible — never enters Layer 1
            print(result)
        else:
            # result is an EvaluationRequest — pass to Layer 1 pipeline
            layer1_result = governance_engine.evaluate(result)

        # With Sharia compliance
        proposed_sharia = ProposedRequest(
            subject="WBTC",
            operation="LEVERAGED",
            jurisdiction="UAE",
            ethical_flags=["SHARIA"],
        )
        result = sae.validate(proposed_sharia, mode=EvaluationMode.FULL_AUDIT)
        # Returns StructuredRejectionRecord with all violations (HARAM asset + HARAM op)

    Singleton pattern: get_instance() returns the shared instance,
    initialized with the default constraint registry on first call.
    """

    _instance: StructuralAdmissibilityEngine | None = None

    def __init__(self, registry: ConstraintRegistry | None = None) -> None:
        self._registry = registry or ConstraintRegistry()
        self._validator = StructuralAdmissibilityValidator(self._registry)
        logger.info("[SAE] StructuralAdmissibilityEngine initialized — Layer 0 armed")

    @classmethod
    def get_instance(cls) -> StructuralAdmissibilityEngine:
        """Return the shared SAE singleton (thread-safe lazy initialization)."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton — use in tests only."""
        cls._instance = None

    def validate(
        self,
        proposed: ProposedRequest | dict,
        mode: EvaluationMode = EvaluationMode.FAST_FAIL,
    ) -> EvaluationRequest | StructuredRejectionRecord:
        """
        Layer 0 entry point. Accepts ProposedRequest or a dict for convenience.

        Returns:
            EvaluationRequest         — admissible, ready for Layer 1.
            StructuredRejectionRecord — inadmissible, Layer 1 must never receive this.

        Side-effects:
            - Emits [LAYER_0] ADMITTED / REJECTED log at INFO / WARNING level.
            - Records per-domain metrics in the shared Layer0Metrics instance.
        """
        if isinstance(proposed, dict):
            proposed = ProposedRequest(**proposed)

        domain = (proposed.domain or "GENERIC").upper()
        _t0 = time.perf_counter()
        result = self._validator.validate_and_construct(proposed, mode)
        elapsed_ms = (time.perf_counter() - _t0) * 1000.0

        if isinstance(result, StructuredRejectionRecord):
            v = result.primary_violation
            _layer0_metrics.record_blocked(
                domain,
                v.constraint_class.value if v else "UNKNOWN",
            )
            logger.warning(
                "[LAYER_0] REJECTED | subject=%s op=%s jur=%s domain=%s | "
                "constraint=%s class=%s | audit_id=%s | elapsed=%.2fms",
                proposed.subject, proposed.operation, proposed.jurisdiction, domain,
                v.constraint_id if v else "?",
                v.constraint_class.value if v else "?",
                result.audit_id,
                elapsed_ms,
            )
        else:
            _layer0_metrics.record_admitted(domain)
            logger.info(
                "[LAYER_0] ADMITTED | subject=%s op=%s jur=%s domain=%s | "
                "eval_id=%s | elapsed=%.2fms",
                proposed.subject, proposed.operation, proposed.jurisdiction, domain,
                result.evaluation_id,
                elapsed_ms,
            )

        return result

    def register_constraint(
        self,
        constraint_class: ConstraintClass,
        evaluator_fn: Callable[[ProposedRequest], ConstraintViolation | None],
    ) -> None:
        """Register a new constraint class at runtime (CCCA extensibility)."""
        self._registry.register(constraint_class, evaluator_fn)

    def register_client_constraint(
        self,
        client_id: str,
        evaluator_fn: Callable[[ProposedRequest], ConstraintViolation | None],
    ) -> None:
        """Register a client-specific constraint (further restricts, never expands)."""
        self._registry.register_client_constraint(client_id, evaluator_fn)


# ── Module-level convenience ────────────────────────────────────────────────────

def get_sae() -> StructuralAdmissibilityEngine:
    """Return the shared SAE instance. Alias for StructuralAdmissibilityEngine.get_instance()."""
    return StructuralAdmissibilityEngine.get_instance()
