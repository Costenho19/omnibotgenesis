"""
OMNIX Agent Trust Fabric (ATF)
ADR-156 — Cryptographic agent delegation infrastructure.

Exports:
    AgentIdentityEngine   — register and manage agent identities
    DelegationReceiptEngine — issue and verify delegation receipts
    TrustLattice          — DAG of agents and delegations
    AgentIdentity         — data class
    DelegationReceipt     — data class
    VerificationResult    — verification output
    AuthorityExpansionViolation — raised when MAR invariant is violated
"""

from omnix_core.agents.atf.agent_identity import (
    AgentIdentity,
    AgentIdentityEngine,
)
from omnix_core.agents.atf.delegation_receipt import (
    DelegationReceipt,
    DelegationReceiptEngine,
    AuthorityExpansionViolation,
)
from omnix_core.agents.atf.trust_lattice import (
    TrustLattice,
    VerificationResult,
)

__all__ = [
    "AgentIdentity",
    "AgentIdentityEngine",
    "DelegationReceipt",
    "DelegationReceiptEngine",
    "AuthorityExpansionViolation",
    "TrustLattice",
    "VerificationResult",
]
