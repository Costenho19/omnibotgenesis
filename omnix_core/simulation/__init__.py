"""
OMNIX — Governance Simulation Layer
=====================================
ADR-145 · Governance Replay Engine

Provides programmatic replay of historical crisis events through the
OMNIX governance pipeline, producing standardized, verifiable receipts.

Modules:
    crisis_scenarios  — Structured crisis scenario library (5 events)
    governance_replay — GovernanceReplayEngine (unified replay engine)

Quick start:
    from omnix_core.simulation.governance_replay import GovernanceReplayEngine

    engine = GovernanceReplayEngine()
    report = engine.replay_all_scenarios()
    print(report.to_markdown())
"""

from omnix_core.simulation.crisis_scenarios import (
    CRISIS_SCENARIOS,
    CrisisScenario,
    SignalState,
    get_scenario,
    list_scenarios,
)


def _lazy_replay():
    from omnix_core.simulation.governance_replay import (
        GovernanceReplayEngine,
        SignedReplayReceipt,
        ScenarioReplayResult,
        FullReplayReport,
    )
    return GovernanceReplayEngine, SignedReplayReceipt, ScenarioReplayResult, FullReplayReport


try:
    from omnix_core.simulation.governance_replay import (
        GovernanceReplayEngine,
        SignedReplayReceipt,
        ScenarioReplayResult,
        FullReplayReport,
    )
except Exception:
    pass

__all__ = [
    "GovernanceReplayEngine",
    "SignedReplayReceipt",
    "ScenarioReplayResult",
    "FullReplayReport",
    "CRISIS_SCENARIOS",
    "CrisisScenario",
    "SignalState",
    "get_scenario",
    "list_scenarios",
]
