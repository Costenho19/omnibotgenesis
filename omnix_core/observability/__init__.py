"""
OMNIX Governance Observability Layer (GOL) — ADR-198

Public API surface for the observability module.

Usage:
    from omnix_core.observability import (
        GovernanceMetricsRegistry,
        GovernancePhaseTimer,
        MetricsSnapshot,
        PHASE_SESSION_START,
        PHASE_TURN_RECORD,
        PHASE_CTCHC_HASH,
        PHASE_BAR_SIGN,
        PHASE_CCS_COMPUTE,
        PHASE_MIVP_MAS,
        PHASE_DB_WRITE,
        PHASE_SESSION_CLOSE,
    )

    registry = GovernanceMetricsRegistry.get_instance()
    with registry.phase_timer(session_id, PHASE_CTCHC_HASH):
        ...
    snapshot = registry.export_snapshot()
"""

from omnix_core.observability.metrics import (
    GovernanceMetricsRegistry,
    GovernancePhaseTimer,
    GovernanceSessionMetric,
    MetricsSnapshot,
    LatencyHistogram,
    ErrorCounter,
    PHASE_SESSION_START,
    PHASE_TURN_RECORD,
    PHASE_SESSION_CLOSE,
    PHASE_SESSION_HALT,
    PHASE_CTCHC_HASH,
    PHASE_BAR_SIGN,
    PHASE_CCS_COMPUTE,
    PHASE_MIVP_MAS,
    PHASE_DB_WRITE,
    MANDATE_BOUND,
    MANDATE_ALIGNED,
    UNCERTIFIED,
)

__all__ = [
    "GovernanceMetricsRegistry",
    "GovernancePhaseTimer",
    "GovernanceSessionMetric",
    "MetricsSnapshot",
    "LatencyHistogram",
    "ErrorCounter",
    "PHASE_SESSION_START",
    "PHASE_TURN_RECORD",
    "PHASE_SESSION_CLOSE",
    "PHASE_SESSION_HALT",
    "PHASE_CTCHC_HASH",
    "PHASE_BAR_SIGN",
    "PHASE_CCS_COMPUTE",
    "PHASE_MIVP_MAS",
    "PHASE_DB_WRITE",
    "MANDATE_BOUND",
    "MANDATE_ALIGNED",
    "UNCERTIFIED",
]
