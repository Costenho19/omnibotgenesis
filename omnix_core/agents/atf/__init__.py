"""
OMNIX Agent Trust Fabric (ATF)
ADR-156 — Cryptographic agent delegation infrastructure.
ADR-157 — Temporal Authority Admissibility.
ADR-158 — Cross-Domain Trust Portability.

Exports:
    AgentIdentityEngine       — register and manage agent identities
    DelegationReceiptEngine   — issue and verify delegation receipts
    TrustLattice              — DAG of agents and delegations
    AgentIdentity             — data class
    DelegationReceipt         — data class
    VerificationResult        — verification output
    AuthorityExpansionViolation — raised when MAR invariant is violated

    TemporalAuthorityEngine   — issue and verify TARs (ADR-157)
    TemporalAdmissibilityRecord — Temporal Admissibility Record (ADR-157)
    TemporalAdmissibilityError  — raised on temporal check failure

    CrossDomainBridge         — issue and verify DTRs (ADR-158)
    DomainTranslationReceipt  — Domain Translation Receipt (ADR-158)
    CrossDomainAuthorityError — raised when CDTP-INV-001 is violated
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
from omnix_core.agents.atf.temporal_authority import (
    TemporalAdmissibilityRecord,
    TemporalAuthorityEngine,
    TemporalAdmissibilityError,
)
from omnix_core.agents.atf.domain_bridge import (
    DomainTranslationReceipt,
    CrossDomainBridge,
    CrossDomainAuthorityError,
)

__all__ = [
    "AgentIdentity",
    "AgentIdentityEngine",
    "DelegationReceipt",
    "DelegationReceiptEngine",
    "AuthorityExpansionViolation",
    "TrustLattice",
    "VerificationResult",
    "TemporalAdmissibilityRecord",
    "TemporalAuthorityEngine",
    "TemporalAdmissibilityError",
    "DomainTranslationReceipt",
    "CrossDomainBridge",
    "CrossDomainAuthorityError",
]
