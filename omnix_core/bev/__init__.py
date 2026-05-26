"""
OMNIX BEV — Behavioral Execution Verification Layer
RFC-ATF-6 · ADR-181 · ADR-182 · ADR-183 · ADR-194

Layer 6 of the Agent Trust Fabric: receipt-bound behavioral attestation,
continuous constraint conformance measurement, cross-turn coherence proof,
and mandate integrity verification.

Compliance Designation Hierarchy (highest to lowest):
  ATF-BEV-Compliant  — all BEV layers attested (BAR + CCS + CTCHC)
  MANDATE-BOUND      — pristine mandate fidelity: zero violations AND zero warnings
  MANDATE-ALIGNED    — mission-aligned: zero violations, warnings permitted
  (no MIVP tag)      — MIVP inactive or mandate violations recorded

Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from omnix_core.bev.behavioral_anchor_record import BehavioralAnchorRecord, BAREngine
from omnix_core.bev.constraint_conformance_signal import ConstraintConformanceSignal, CCSEngine
from omnix_core.bev.coherence_hash_chain import CoherenceHashChain, CTCHCEngine
from omnix_core.bev.mandate_integrity_verification import (
    MandateBindingRecord,
    MandateAlignmentScore,
    MBRSeal,
    ProxyGuard,
    MIVPEngine,
    MANDATE_BOUND_TAG,
    MANDATE_ALIGNED_TAG,
)

__all__ = [
    # BAR — Behavioral Anchor Record (ADR-181)
    "BehavioralAnchorRecord",
    "BAREngine",
    # CCS — Constraint Conformance Signal (ADR-182)
    "ConstraintConformanceSignal",
    "CCSEngine",
    # CTCHC — Cross-Turn Coherence Hash Chain (ADR-183)
    "CoherenceHashChain",
    "CTCHCEngine",
    # MIVP — Mandate Integrity Verification Protocol (ADR-194)
    "MandateBindingRecord",
    "MandateAlignmentScore",
    "MBRSeal",
    "ProxyGuard",
    "MIVPEngine",
    "MANDATE_BOUND_TAG",
    "MANDATE_ALIGNED_TAG",
]
