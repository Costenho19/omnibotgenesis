"""
OMNIX — Semantic Governance Version Registry (ISR-008)
ISR-2026-Q2-001 · Engine Version Semantic Contract

Problem:
  engine_version is a free string from an env var. When checkpoint logic
  changes, the version string may not change, making historical receipts
  semantically opaque: a regulator cannot reconstruct what CP-3 meant
  on a specific date without reading git history.

Solution:
  A registry mapping every engine_version to:
    - The checkpoints that existed at that version
    - The semantic meaning of each checkpoint's verdict fields
    - The ADRs governing that version
    - A fingerprint of the checkpoint module source (for CI verification)
    - The governance schema format (what fields are in the receipt)

Usage in receipts:
  Every new receipt includes:
    governance_schema_version   — schema format version (independent of engine logic)
    checkpoint_logic_fingerprint — SHA-256 of checkpoint source at receipt time

CI guard:
  Run assert_version_consistency() in tests/test_engine_version.py.
  It fails if the running code fingerprint doesn't match the registry entry
  for the current OMNIX_VERSION — forcing an explicit registry update
  whenever checkpoint logic changes.

ADR: ISR-008 remediation
"""
from __future__ import annotations

import hashlib
import importlib.util
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("OMNIX.Governance.SemanticVersionRegistry")

CURRENT_SCHEMA_VERSION = "2"


@dataclass
class CheckpointSemantic:
    """Semantic definition of one checkpoint's verdict fields."""
    checkpoint_id: str
    name: str
    adr: str
    verdict_fields: dict[str, str]
    notes: str = ""


@dataclass
class SemanticEntry:
    """Complete semantic contract for one engine version."""
    engine_version: str
    schema_version: str
    released: str
    adrs: list[str]
    checkpoints: list[CheckpointSemantic]
    governance_schema_fields: list[str]
    logic_fingerprint: Optional[str] = None
    notes: str = ""

    @property
    def checkpoint_count(self) -> int:
        """Number of checkpoints defined in this engine version."""
        return len(self.checkpoints)

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_version": self.engine_version,
            "schema_version": self.schema_version,
            "released": self.released,
            "adrs": self.adrs,
            "checkpoint_count": self.checkpoint_count,
            "checkpoints": [
                {
                    "checkpoint_id": c.checkpoint_id,
                    "name": c.name,
                    "adr": c.adr,
                    "verdict_fields": c.verdict_fields,
                    "notes": c.notes,
                }
                for c in self.checkpoints
            ],
            "governance_schema_fields": self.governance_schema_fields,
            "logic_fingerprint": self.logic_fingerprint,
            "notes": self.notes,
        }


_CHECKPOINTS_V6 = [
    CheckpointSemantic(
        checkpoint_id="SAE",
        name="Structural Admissibility Engine",
        adr="ADR-040",
        verdict_fields={
            "admissible": "bool — True if signal structure passes all 4 SAE pillars",
            "pillar_results": "list of {pillar, passed, reason}",
        },
    ),
    CheckpointSemantic(
        checkpoint_id="SPG",
        name="State Provenance Guard",
        adr="ADR-141",
        verdict_fields={
            "admissible": "bool — True if state provenance is verifiable",
        },
    ),
    CheckpointSemantic(
        checkpoint_id="CBG",
        name="Conditional Bind Gate",
        adr="ADR-139",
        verdict_fields={
            "admissible": "bool — True if binding conditions are met",
        },
    ),
    CheckpointSemantic(
        checkpoint_id="CAG",
        name="Context Admission Gate",
        adr="ADR-042",
        verdict_fields={
            "admissible": "bool — True if global market conditions are within baseline",
            "global_volatility": "float — VIX proxy used at evaluation time",
        },
    ),
    CheckpointSemantic(
        checkpoint_id="CP-1",
        name="Regulatory Pre-Screen",
        adr="ADR-028",
        verdict_fields={
            "admissible": "bool — True if asset passes regulatory pre-screen",
        },
    ),
    CheckpointSemantic(
        checkpoint_id="CP-2",
        name="Signal Completeness",
        adr="ADR-028",
        verdict_fields={
            "admissible": "bool — True if all required signal fields are present and non-null",
        },
    ),
    CheckpointSemantic(
        checkpoint_id="CP-3",
        name="Signal Coherence",
        adr="ADR-028",
        verdict_fields={
            "admissible": "bool — True if signals are internally consistent",
            "coherence_score": "float 0-100 — cross-signal agreement score",
        },
    ),
    CheckpointSemantic(
        checkpoint_id="CP-4",
        name="Trajectory Invariant",
        adr="ADR-028",
        verdict_fields={
            "admissible": "bool — True if signal trajectory is within invariant bounds",
        },
    ),
    CheckpointSemantic(
        checkpoint_id="CP-5",
        name="AML Gate",
        adr="ADR-055",
        verdict_fields={
            "admissible": "bool — True if AML patterns absent",
            "evaluation_state": "EVALUATED | DISABLED | FAIL_CLOSED",
        },
    ),
    CheckpointSemantic(
        checkpoint_id="CP-6",
        name="Sharia Gate",
        adr="ADR-061",
        verdict_fields={
            "admissible": "bool — True if asset is halal-compliant or gate disabled",
            "sharia_score": "float 0-100 — compliance score (0 = not evaluated, 100 = maximum uncertainty)",
            "evaluation_state": "EVALUATED | DISABLED | FAILSAFE",
            "note": "sharia_score=0.0 means gate was DISABLED (not evaluated), NOT that it failed",
        },
    ),
    CheckpointSemantic(
        checkpoint_id="CP-7",
        name="Fraud Gate",
        adr="ADR-057",
        verdict_fields={
            "admissible": "bool — True if fraud patterns absent",
            "integrity_score": "float 0-100 — fraud integrity score (0 = not evaluated or FAIL_CLOSED)",
            "evaluation_state": "EVALUATED | DISABLED | FAIL_CLOSED",
        },
    ),
    CheckpointSemantic(
        checkpoint_id="CP-8",
        name="Commit-Time Gate",
        adr="ADR-028",
        verdict_fields={
            "admissible": "bool — True if signal timing is within commit window",
        },
    ),
    CheckpointSemantic(
        checkpoint_id="CP-9",
        name="Standing Boundary Engine",
        adr="ADR-028",
        verdict_fields={
            "admissible": "bool — True if signal is within position/exposure bounds",
        },
    ),
    CheckpointSemantic(
        checkpoint_id="CP-10",
        name="AVM (Assumption Validity Monitor)",
        adr="ADR-074",
        verdict_fields={
            "is_valid": "bool — True if live signals match calibration baseline within drift_threshold",
            "drift_score": "float — max deviation from calibrated baseline across all signals",
            "snapshot_id": "str — ID of the calibration snapshot used for comparison",
            "parameter_version": "str — version of the calibration parameters",
        },
    ),
    CheckpointSemantic(
        checkpoint_id="CP-11",
        name="Jurisdiction Gate",
        adr="ADR-059",
        verdict_fields={
            "admissible": "bool — True if asset/action permitted in client jurisdiction",
            "jurisdiction": "str — jurisdiction code applied",
            "ofac_list_version": "str — OFAC SDN list version used at evaluation time",
        },
    ),
]

_GOVERNANCE_SCHEMA_FIELDS_V2 = [
    "receipt_id", "timestamp", "issued_at_ms", "ttl_epoch_ms", "ttl_ms",
    "asset", "decision", "veto_chain", "policy_version", "engine_version",
    "prev_hash", "signing_provider", "signing_key_id", "domain",
    "sharia_compliance", "aml_compliance", "fraud_compliance",
    "jurisdiction_compliance", "context_admission", "avm_result",
    "content_hash", "signature_algorithm", "pqc_signature",
    "governance_schema_version", "checkpoint_logic_fingerprint",
]

SEMANTIC_REGISTRY: dict[str, SemanticEntry] = {
    "6.5.4e": SemanticEntry(
        engine_version="6.5.4e",
        schema_version="1",
        released="2026-03-01",
        adrs=[
            "ADR-028", "ADR-040", "ADR-042", "ADR-044", "ADR-055",
            "ADR-057", "ADR-059", "ADR-061", "ADR-074", "ADR-116",
            "ADR-131", "ADR-138", "ADR-139", "ADR-141", "ADR-145",
            "ADR-146", "ADR-147",
        ],
        checkpoints=_CHECKPOINTS_V6,
        governance_schema_fields=[
            "receipt_id", "timestamp", "issued_at_ms", "ttl_epoch_ms", "ttl_ms",
            "asset", "decision", "veto_chain", "policy_version", "engine_version",
            "prev_hash", "signing_provider", "signing_key_id", "domain",
            "sharia_compliance", "aml_compliance", "fraud_compliance",
            "jurisdiction_compliance", "context_admission", "avm_result",
            "content_hash", "signature_algorithm", "pqc_signature",
        ],
        notes=(
            "Pre-registry version. Receipts from this version are hash-verifiable "
            "and PQC-signature-verifiable but do not include checkpoint_logic_fingerprint. "
            "Semantic reconstruction relies on veto_chain field and ADR documentation."
        ),
    ),
    "6.6.0": SemanticEntry(
        engine_version="6.6.0",
        schema_version="2",
        released="2026-05-09",
        adrs=[
            "ADR-028", "ADR-040", "ADR-042", "ADR-044", "ADR-055",
            "ADR-057", "ADR-059", "ADR-061", "ADR-074", "ADR-116",
            "ADR-131", "ADR-138", "ADR-139", "ADR-141", "ADR-145",
            "ADR-146", "ADR-147",
        ],
        checkpoints=_CHECKPOINTS_V6,
        governance_schema_fields=_GOVERNANCE_SCHEMA_FIELDS_V2,
        notes=(
            "ISR-2026-Q2-001 remediations applied: semantic version registry (ISR-008), "
            "payload key versioning (ISR-021), transparency chain durability (ISR-013), "
            "prompt injection containment (ISR-017). "
            "New receipt fields: governance_schema_version, checkpoint_logic_fingerprint."
        ),
    ),
}


def _compute_logic_fingerprint() -> str:
    """
    Compute SHA-256 fingerprint of the checkpoint source files.
    Used to detect when checkpoint logic changes without a version bump.
    Changes to these files MUST be accompanied by a new registry entry.
    """
    checkpoint_files = [
        "omnix_core/governance/external_evaluator.py",
        "omnix_core/governance/structural_admissibility_engine.py",
        "omnix_core/governance/context_admission_gate.py",
        "omnix_core/governance/aml_gate.py",
        "omnix_core/governance/sharia_gate.py",
        "omnix_core/governance/fraud_gate.py",
        "omnix_core/governance/jurisdiction_gate.py",
        "omnix_core/governance/assumption_validity_monitor.py",
        "omnix_core/governance/commit_time_gate.py",
        "omnix_core/governance/standing_boundary_engine.py",
        "omnix_core/governance/trajectory_invariant_engine.py",
        "omnix_core/governance/state_provenance_guard.py",
        "omnix_core/governance/conditional_bind_gate.py",
    ]
    h = hashlib.sha256()
    for rel_path in sorted(checkpoint_files):
        p = Path(rel_path)
        if not p.exists():
            p = Path(os.getcwd()) / rel_path
        if p.exists():
            try:
                h.update(p.read_bytes())
            except Exception as exc:
                logger.debug(f"[SemanticRegistry] Could not read {rel_path}: {exc}")
                h.update(rel_path.encode())
        else:
            h.update(rel_path.encode())
    return h.hexdigest()


def get_current_entry() -> SemanticEntry:
    """Return the registry entry for the currently running engine version."""
    version = os.environ.get("OMNIX_VERSION", "6.5.4e")
    entry = SEMANTIC_REGISTRY.get(version)
    if entry is None:
        logger.warning(
            f"[SemanticRegistry][ISR-008] engine_version '{version}' not found in registry. "
            f"Known versions: {list(SEMANTIC_REGISTRY.keys())}. "
            f"Add an entry to semantic_version_registry.py when releasing a new version."
        )
        entry = SEMANTIC_REGISTRY.get("6.6.0") or list(SEMANTIC_REGISTRY.values())[-1]
    return entry


def get_historical_entry(version: str) -> Optional[SemanticEntry]:
    """Return the registry entry for a historical engine version (for receipt reconstruction)."""
    return SEMANTIC_REGISTRY.get(version)


def current_fingerprint() -> str:
    """Return the logic fingerprint of the currently running checkpoint code."""
    return _compute_logic_fingerprint()


def assert_version_consistency() -> None:
    """
    CI guard — raises AssertionError if the running checkpoint code fingerprint
    does not match the registry entry for the current engine version.

    This forces engineers to update the registry whenever checkpoint logic changes.
    Run this in tests/test_engine_version.py.
    """
    version = os.environ.get("OMNIX_VERSION", "6.5.4e")
    entry = SEMANTIC_REGISTRY.get(version)

    if entry is None:
        raise AssertionError(
            f"engine_version '{version}' (from OMNIX_VERSION env var) "
            f"is not in SEMANTIC_REGISTRY. "
            f"Add an entry to omnix_core/governance/semantic_version_registry.py."
        )

    if entry.schema_version == "1":
        logger.info(
            f"[SemanticRegistry] Version '{version}' is a pre-registry version — "
            f"fingerprint check skipped."
        )
        return

    running_fingerprint = _compute_logic_fingerprint()

    if entry.logic_fingerprint is None:
        logger.warning(
            f"[SemanticRegistry] Version '{version}' has no logic_fingerprint in registry. "
            f"Current fingerprint: {running_fingerprint}. "
            f"Update the registry entry with this fingerprint."
        )
        return

    if running_fingerprint != entry.logic_fingerprint:
        raise AssertionError(
            f"[ISR-008] Checkpoint logic has changed without a version bump!\n"
            f"engine_version = '{version}'\n"
            f"Registry fingerprint: {entry.logic_fingerprint}\n"
            f"Running fingerprint:  {running_fingerprint}\n"
            f"Either update OMNIX_VERSION and add a new entry to SEMANTIC_REGISTRY, "
            f"or update the 'logic_fingerprint' for version '{version}' if this was "
            f"an intentional but non-breaking change."
        )

    logger.info(
        f"[SemanticRegistry] Version '{version}' fingerprint matches registry. "
        f"Checkpoint logic is consistent."
    )
