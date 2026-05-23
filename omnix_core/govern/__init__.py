"""
OMNIX Governance Runtime (OGR)
ADR-184 · RFC-ATF-1 through RFC-ATF-6

The single integration point for the full 6-layer Agent Trust Fabric.
One call activates identity, delegation, temporal authority, runtime
continuity, cognitive governance, and behavioral verification simultaneously.

Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from omnix_core.govern.governance_runtime import GovernanceRuntime, OGRSession

__all__ = ["GovernanceRuntime", "OGRSession"]
