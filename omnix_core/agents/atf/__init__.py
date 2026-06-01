"""
OMNIX Agent Trust Fabric (ATF)
ADR-156 — Cryptographic agent delegation infrastructure.
ADR-157 — Temporal Authority Admissibility.
ADR-158 — Cross-Domain Trust Portability.
ADR-159 — Runtime Governance Continuity.
ADR-160 — RCR Performance Optimization Layer (RPOL).
ADR-171 — Semantic Governance Interoperability Protocol (SGIP · Layer 4).
ADR-172 — ATF Open Receipt Schema (ATORS) + Standalone Verifier.

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

    RuntimeContinuityEngine       — continuous authority health engine (ADR-159)
    RuntimeContinuityRecord       — ATFRCR-{16HEX} authority health snapshot
    ContinuityEligibilityScore    — composite CES metric (T+B+D+I weighted)
    ContinuityEscalationEvent     — ATFCEE-{16HEX} threshold escalation artifact
    ReauthorizationChallenge      — ATFRC-{16HEX} mid-execution authority renewal
    AuthorityFragmentationViolation — raised when AFG aggregate limit exceeded
    ContinuityHaltError           — raised when HALT is triggered (RGC-INV-003)
    get_rgc_engine                — process-level singleton accessor

    GovernanceRiskTier            — LOW/STANDARD/HIGH/CRITICAL tier enum (ADR-160)
    RCRWriteQueue                 — pooled async DB writer (ADR-160)
    EventDrivenSampler            — event-threshold sampler (ADR-160)
    GovernanceEventType           — governance event enum (ADR-160)
    RCRScheduler                  — adaptive interval scheduler (ADR-160)
    ExecutionProfile              — SHORT/MEDIUM/LONG/STREAMING enum (ADR-160)

    SemanticTermEntry             — STR entry dataclass (ADR-171)
    SemanticPolicyVector          — SPV snapshot dataclass (ADR-171)
    SemanticAlignmentCertificate  — SAC bilateral cert dataclass (ADR-171)
    SemanticGovernanceEngine      — SGIP engine: publish_term/generate_spv/create_sac/verify_sac (ADR-171)
    SGIPError                     — base SGIP exception
    STRImmutabilityViolation      — SGIP-INV-001 violation
    SAC_IncompleteSPV             — SGIP-INV-002 violation
    ATF_CORE_TERM_SET             — tuple of 8 ATF Core Terms
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
from omnix_core.agents.atf.runtime_continuity import (
    RuntimeContinuityEngine,
    RuntimeContinuityRecord,
    ContinuityEligibilityScore,
    ContinuityEscalationEvent,
    ReauthorizationChallenge,
    AuthorityFragmentationViolation,
    ContinuityHaltError,
    get_rgc_engine,
)
from omnix_core.agents.atf.rcr_performance import (
    GovernanceRiskTier,
    RCRWriteQueue,
    EventDrivenSampler,
    GovernanceEventType,
    RCRScheduler,
    ExecutionProfile,
)
from omnix_core.agents.atf.semantic_governance import (
    ATF_CORE_TERM_SET,
    SAC_IncompleteSPV,
    SGIPError,
    STRImmutabilityViolation,
    SemanticAlignmentCertificate,
    SemanticGovernanceEngine,
    SemanticPolicyVector,
    SemanticTermEntry,
    UnknownTermError,
)
from omnix_core.agents.atf.temporal_governance_bridge import (
    TemporalContextSnapshot,
    RegulatoryAlignmentReceipt,
    TemporalMigrationRecord,
    TemporalGovernanceBridge,
)
from omnix_core.agents.atf.counterfactual_governance_engine import (
    CounterfactualForkRecord,
    CounterfactualAttestationToken,
    CounterfactualGovernanceEngine,
    CGEInvariantViolation,
)
from omnix_core.agents.atf.grand_unified_governance_theory import (
    UniversalInvariantReceipt,
    GrandUnifiedGovernanceEngine,
    GUGTInvariantViolation,
    GUGTUnsignedError,
    validate_clause_ref,
    UNIVERSAL_GOVERNANCE_INVARIANTS,
    CONFORMANCE_LEVELS,
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
    "RuntimeContinuityEngine",
    "RuntimeContinuityRecord",
    "ContinuityEligibilityScore",
    "ContinuityEscalationEvent",
    "ReauthorizationChallenge",
    "AuthorityFragmentationViolation",
    "ContinuityHaltError",
    "get_rgc_engine",
    "GovernanceRiskTier",
    "RCRWriteQueue",
    "EventDrivenSampler",
    "GovernanceEventType",
    "RCRScheduler",
    "ExecutionProfile",
    "ATF_CORE_TERM_SET",
    "SemanticTermEntry",
    "SemanticPolicyVector",
    "SemanticAlignmentCertificate",
    "SemanticGovernanceEngine",
    "SGIPError",
    "STRImmutabilityViolation",
    "SAC_IncompleteSPV",
    "UnknownTermError",
    # RFC-ATF-5: TGB (ADR-180)
    "TemporalContextSnapshot",
    "RegulatoryAlignmentReceipt",
    "TemporalMigrationRecord",
    "TemporalGovernanceBridge",
    # RFC-ATF-5: CGE (ADR-178)
    "CounterfactualForkRecord",
    "CounterfactualAttestationToken",
    "CounterfactualGovernanceEngine",
    "CGEInvariantViolation",
    # RFC-ATF-5: GUGT (ADR-179)
    "UniversalInvariantReceipt",
    "GrandUnifiedGovernanceEngine",
    "GUGTInvariantViolation",
    "GUGTUnsignedError",
    "validate_clause_ref",
    "UNIVERSAL_GOVERNANCE_INVARIANTS",
    "CONFORMANCE_LEVELS",
]
