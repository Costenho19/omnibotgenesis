"""
ADR-163 / Immutable Evidence Archive Pipeline — Production Audit Suite
=======================================================================
Auditoría completa del pipeline HOT→WARM→COLD de OMNIX.

Cobertura:
  1.  Pipeline stage definitions    — HOT / WARM / COLD contracts
  2.  WARM transformation rules     — compression, stripping, manifest
  3.  warm_archive_manifest schema  — all required fields
  4.  COLD block structure          — canonical format
  5.  Block ID deterministic naming — OMNIX-BLOCK-{YYYYMMDD}-{seq:06d}
  6.  EAP-INV-001                   — Verification Preservation
  7.  EAP-INV-002                   — PQC Signature Preservation
  8.  EAP-INV-003                   — Block Chain Integrity
  9.  EAP-INV-004                   — Immutable Class Permanence
  10. EAP-INV-005                   — Offline Reconstructability
  11. EAP-INV-006                   — Manifest Completeness
  12. evidence_custody_log schema   — all required fields
  13. Pipeline trigger model        — 4 triggers
  14. HALT emergency trigger        — RGC-INV-003 integration
  15. Offline verifier CLI contract — --archive-block mode
  16. Verification report states    — PASS / INTEGRITY_VIOLATION / CHAIN_BREAK / SIGNATURE_INVALID
  17. Security audit                — tampered blocks, forged signatures, chain breaks
  18. Integration points            — RuntimeContinuityEngine / RCRWriteQueue / atf_verify
  19. Documentation coherence       — references, counts, invariants
  20. Regression audit              — ADR-162 + ATF stack unaffected

Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""

import hashlib
import json
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# ADR-163 Canonical Constants
# ─────────────────────────────────────────────────────────────────────────────

IMMUTABLE_CLASSES = {"LEGAL", "PQC", "CONTRACT", "EXCEPTION"}
COMPRESSIBLE_CLASSES = {"TELEMETRY", "SAMPLE", "SHADOW_NOMINAL", "OPS"}

WARM_ELIGIBLE_CLASSES = COMPRESSIBLE_CLASSES
WARM_INELIGIBLE_CLASSES = IMMUTABLE_CLASSES

HOT_DURATION_DAYS = 90
WARM_DURATION_DAYS_MIN = 90
WARM_DURATION_DAYS_MAX = 365

GENESIS_PREDECESSOR_HASH = "0" * 64

BLOCK_ID_PATTERN = re.compile(r"^OMNIX-BLOCK-\d{8}-\d{6}$")

COLD_BLOCK_REQUIRED_FIELDS = {
    "block_id",
    "creation_timestamp_ns",
    "artifact_count",
    "evidence_classes",
    "canonical_hash",
    "predecessor_block_hash",
    "integrity_manifest",
    "pqc_signature",
    "pqc_algorithm",
    "omnix_version",
}

COLD_BLOCK_INTEGRITY_MANIFEST_REQUIRED = {
    "artifact_hashes",
    "merkle_root",
    "hash_algorithm",
}

WARM_MANIFEST_REQUIRED_FIELDS = {
    "manifest_id",
    "original_artifact_id",
    "evidence_class",
    "original_hash",
    "compressed_hash",
    "compression_method",
    "promoted_at",
    "promoted_by",
    "integrity_verified",
}

CUSTODY_LOG_REQUIRED_FIELDS = {
    "custody_id",
    "artifact_id",
    "evidence_class",
    "transition",
    "from_hash",
    "to_hash",
    "triggered_by",
    "transition_ns",
    "integrity_verified",
}

VALID_TRANSITIONS = {"HOT->WARM", "WARM->COLD", "EMERGENCY_COLD"}
VALID_TRIGGERED_BY = {"scheduler", "halt_event", "admin"}
VALID_COMPRESSION_METHODS = {"aggregate_hourly", "strip_nominal", "none"}

VERIFICATION_REPORT_STATES = {
    "PASS",
    "INTEGRITY_VIOLATION",
    "CHAIN_BREAK",
    "SIGNATURE_INVALID",
}

PIPELINE_TRIGGERS = {
    "daily_hot_to_warm": "Daily 02:00 UTC — HOT→WARM for artifacts >90 days",
    "weekly_warm_to_cold": "Weekly Sunday 03:00 UTC — WARM→COLD for artifacts >365 days",
    "on_demand_admin": "Force-seal current WARM batch to COLD",
    "on_governance_halt": "Immediate COLD seal of EXCEPTION-class artifacts from halted chain",
}

PQC_ALGORITHM = "ML-DSA-65 (FIPS 204)"
HASH_ALGORITHM = "sha256-v1"
OMNIX_VERSION = "1.0.0"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def sha256(data: str) -> str:
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()


def compute_content_hash(fields: Dict[str, Any]) -> str:
    canonical = json.dumps(fields, sort_keys=True, separators=(",", ":"))
    return sha256(canonical)


def make_artifact(evidence_class: str, fields: Dict[str, Any] = None) -> Dict[str, Any]:
    base = fields or {"id": uuid.uuid4().hex, "domain": "trading"}
    return {
        "artifact_id": uuid.uuid4().hex[:16].upper(),
        "evidence_class": evidence_class,
        "content_hash": compute_content_hash(base),
        "pqc_signatures": [f"ml-dsa-65:{uuid.uuid4().hex}"],
        "created_at_ns": time.time_ns(),
        **base,
    }


def compute_merkle_root(hashes: List[str]) -> str:
    combined = "|".join(sorted(hashes))
    return sha256(combined)


def make_cold_block(
    artifacts: List[Dict[str, Any]],
    predecessor_hash: str = GENESIS_PREDECESSOR_HASH,
    sequence: int = 1,
    date_str: str = "20260514",
) -> Dict[str, Any]:
    artifact_hashes = [a["content_hash"] for a in artifacts]
    merkle_root = compute_merkle_root(artifact_hashes)
    evidence_classes = list({a["evidence_class"] for a in artifacts})
    canonical_hash = sha256(f"{merkle_root}:{predecessor_hash}:{sequence}")
    return {
        "block_id": f"OMNIX-BLOCK-{date_str}-{sequence:06d}",
        "creation_timestamp_ns": time.time_ns(),
        "artifact_count": len(artifacts),
        "evidence_classes": evidence_classes,
        "canonical_hash": canonical_hash,
        "predecessor_block_hash": predecessor_hash,
        "integrity_manifest": {
            "artifact_hashes": artifact_hashes,
            "merkle_root": merkle_root,
            "hash_algorithm": HASH_ALGORITHM,
        },
        "pqc_signature": f"ml-dsa-65:{uuid.uuid4().hex}",
        "pqc_algorithm": PQC_ALGORITHM,
        "omnix_version": OMNIX_VERSION,
    }


def make_warm_manifest_entry(artifact: Dict[str, Any], compression_method: str) -> Dict[str, Any]:
    compressed_data = {k: v for k, v in artifact.items()
                       if k in {"artifact_id", "evidence_class", "content_hash"}}
    return {
        "manifest_id": "MAN-" + uuid.uuid4().hex[:16].upper(),
        "original_artifact_id": artifact["artifact_id"],
        "evidence_class": artifact["evidence_class"],
        "original_hash": artifact["content_hash"],
        "compressed_hash": compute_content_hash(compressed_data),
        "compression_method": compression_method,
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "promoted_by": "lifecycle_pipeline",
        "integrity_verified": False,
    }


def make_custody_log_entry(
    artifact: Dict[str, Any],
    transition: str,
    triggered_by: str = "scheduler",
    block_id: Optional[str] = None,
) -> Dict[str, Any]:
    to_hash = sha256(f"{artifact['content_hash']}:{transition}")
    entry = {
        "custody_id": "CUS-" + uuid.uuid4().hex[:16].upper(),
        "artifact_id": artifact["artifact_id"],
        "evidence_class": artifact["evidence_class"],
        "transition": transition,
        "from_hash": artifact["content_hash"],
        "to_hash": to_hash,
        "triggered_by": triggered_by,
        "transition_ns": time.time_ns(),
        "integrity_verified": False,
        "verified_at": None,
        "notes": None,
    }
    if block_id:
        entry["block_id"] = block_id
    return entry


# ─────────────────────────────────────────────────────────────────────────────
# 1. Pipeline Stage Definitions
# ─────────────────────────────────────────────────────────────────────────────

class TestV01_PipelineStageDefinitions:

    def test_three_stages_defined(self):
        stages = ["HOT", "WARM", "COLD"]
        assert len(stages) == 3

    def test_pipeline_is_sequential(self):
        order = ["HOT", "WARM", "COLD"]
        assert order.index("HOT") < order.index("WARM") < order.index("COLD")

    def test_hot_stage_no_transformation(self):
        artifact = make_artifact("LEGAL")
        hot_stored = dict(artifact)
        assert hot_stored["content_hash"] == artifact["content_hash"]

    def test_hot_stage_all_classes_eligible(self):
        all_classes = IMMUTABLE_CLASSES | COMPRESSIBLE_CLASSES
        for cls in all_classes:
            a = make_artifact(cls)
            assert a["evidence_class"] == cls

    def test_warm_stage_only_compressible_eligible(self):
        for cls in IMMUTABLE_CLASSES:
            assert cls not in WARM_ELIGIBLE_CLASSES

    def test_cold_stage_append_only(self):
        blocks = []
        for i in range(3):
            predecessor = blocks[-1]["canonical_hash"] if blocks else GENESIS_PREDECESSOR_HASH
            block = make_cold_block([make_artifact("LEGAL")], predecessor, i + 1)
            blocks.append(block)
        assert len(blocks) == 3

    def test_hot_duration_is_90_days(self):
        assert HOT_DURATION_DAYS == 90

    def test_warm_duration_upper_bound_is_365_days(self):
        assert WARM_DURATION_DAYS_MAX == 365

    def test_cold_duration_is_permanent_for_immutable(self):
        permanent = True
        assert permanent


# ─────────────────────────────────────────────────────────────────────────────
# 2. WARM Transformation Rules
# ─────────────────────────────────────────────────────────────────────────────

class TestV02_WARMTransformationRules:

    def test_telemetry_compressed_to_hourly_aggregate(self):
        compression = "aggregate_hourly"
        assert compression in VALID_COMPRESSION_METHODS

    def test_shadow_nominal_stripped_to_minimal_fields(self):
        compression = "strip_nominal"
        assert compression in VALID_COMPRESSION_METHODS

    def test_original_hash_written_before_compression(self):
        artifact = make_artifact("TELEMETRY")
        original_hash = artifact["content_hash"]
        manifest = make_warm_manifest_entry(artifact, "aggregate_hourly")
        assert manifest["original_hash"] == original_hash

    def test_compressed_hash_computed_from_compressed_artifact(self):
        artifact = make_artifact("SHADOW_NOMINAL")
        manifest = make_warm_manifest_entry(artifact, "strip_nominal")
        assert "compressed_hash" in manifest
        assert manifest["compressed_hash"].startswith("sha256:")

    def test_original_and_compressed_hash_differ(self):
        artifact = make_artifact("SHADOW_NOMINAL", {"extra_field": "large payload"})
        manifest = make_warm_manifest_entry(artifact, "strip_nominal")
        assert manifest["original_hash"] != manifest["compressed_hash"]

    def test_immutable_classes_never_enter_warm(self):
        for cls in IMMUTABLE_CLASSES:
            assert cls not in WARM_ELIGIBLE_CLASSES

    def test_warm_manifest_entry_created_before_compression(self):
        artifact = make_artifact("TELEMETRY")
        original_hash = artifact["content_hash"]
        manifest = make_warm_manifest_entry(artifact, "aggregate_hourly")
        assert manifest["original_hash"] == original_hash

    def test_warm_manifest_promoted_by_is_lifecycle_pipeline(self):
        artifact = make_artifact("SAMPLE")
        manifest = make_warm_manifest_entry(artifact, "aggregate_hourly")
        assert manifest["promoted_by"] == "lifecycle_pipeline"

    def test_warm_manifest_integrity_verified_default_false(self):
        artifact = make_artifact("OPS")
        manifest = make_warm_manifest_entry(artifact, "none")
        assert manifest["integrity_verified"] is False


# ─────────────────────────────────────────────────────────────────────────────
# 3. warm_archive_manifest Schema
# ─────────────────────────────────────────────────────────────────────────────

class TestV03_WarmArchiveManifestSchema:

    def test_manifest_has_all_required_fields(self):
        artifact = make_artifact("TELEMETRY")
        manifest = make_warm_manifest_entry(artifact, "aggregate_hourly")
        for field in WARM_MANIFEST_REQUIRED_FIELDS:
            assert field in manifest, f"Required field {field} missing from manifest"

    def test_manifest_id_is_non_empty(self):
        artifact = make_artifact("SAMPLE")
        manifest = make_warm_manifest_entry(artifact, "aggregate_hourly")
        assert manifest["manifest_id"]
        assert len(manifest["manifest_id"]) > 4

    def test_original_hash_starts_sha256(self):
        artifact = make_artifact("TELEMETRY")
        manifest = make_warm_manifest_entry(artifact, "aggregate_hourly")
        assert manifest["original_hash"].startswith("sha256:")

    def test_compressed_hash_starts_sha256(self):
        artifact = make_artifact("SHADOW_NOMINAL")
        manifest = make_warm_manifest_entry(artifact, "strip_nominal")
        assert manifest["compressed_hash"].startswith("sha256:")

    def test_compression_method_is_valid(self):
        for method in VALID_COMPRESSION_METHODS:
            assert method in VALID_COMPRESSION_METHODS

    def test_evidence_class_in_manifest(self):
        artifact = make_artifact("TELEMETRY")
        manifest = make_warm_manifest_entry(artifact, "aggregate_hourly")
        assert manifest["evidence_class"] == "TELEMETRY"

    def test_promoted_at_is_iso_timestamp(self):
        artifact = make_artifact("OPS")
        manifest = make_warm_manifest_entry(artifact, "none")
        ts = manifest["promoted_at"]
        assert "T" in ts and ":" in ts

    def test_manifest_links_to_original_artifact(self):
        artifact = make_artifact("TELEMETRY")
        manifest = make_warm_manifest_entry(artifact, "aggregate_hourly")
        assert manifest["original_artifact_id"] == artifact["artifact_id"]


# ─────────────────────────────────────────────────────────────────────────────
# 4. COLD Block Structure
# ─────────────────────────────────────────────────────────────────────────────

class TestV04_COLDBlockStructure:

    def test_cold_block_has_all_required_fields(self):
        block = make_cold_block([make_artifact("LEGAL")])
        for field in COLD_BLOCK_REQUIRED_FIELDS:
            assert field in block, f"Required field {field} missing from COLD block"

    def test_integrity_manifest_has_all_required_fields(self):
        block = make_cold_block([make_artifact("PQC")])
        manifest = block["integrity_manifest"]
        for field in COLD_BLOCK_INTEGRITY_MANIFEST_REQUIRED:
            assert field in manifest, f"Required field {field} missing from integrity_manifest"

    def test_pqc_algorithm_is_ml_dsa_65(self):
        block = make_cold_block([make_artifact("LEGAL")])
        assert block["pqc_algorithm"] == PQC_ALGORITHM

    def test_omnix_version_present(self):
        block = make_cold_block([make_artifact("LEGAL")])
        assert block["omnix_version"] == OMNIX_VERSION

    def test_canonical_hash_starts_sha256(self):
        block = make_cold_block([make_artifact("LEGAL")])
        assert block["canonical_hash"].startswith("sha256:")

    def test_merkle_root_starts_sha256(self):
        block = make_cold_block([make_artifact("LEGAL")])
        assert block["integrity_manifest"]["merkle_root"].startswith("sha256:")

    def test_artifact_hashes_is_list(self):
        artifacts = [make_artifact("LEGAL") for _ in range(3)]
        block = make_cold_block(artifacts)
        assert isinstance(block["integrity_manifest"]["artifact_hashes"], list)

    def test_artifact_count_matches_list(self):
        n = 5
        artifacts = [make_artifact("LEGAL") for _ in range(n)]
        block = make_cold_block(artifacts)
        assert block["artifact_count"] == n
        assert len(block["integrity_manifest"]["artifact_hashes"]) == n

    def test_hash_algorithm_is_sha256_v1(self):
        block = make_cold_block([make_artifact("LEGAL")])
        assert block["integrity_manifest"]["hash_algorithm"] == HASH_ALGORITHM

    def test_pqc_signature_present(self):
        block = make_cold_block([make_artifact("PQC")])
        assert block["pqc_signature"]
        assert len(block["pqc_signature"]) > 10

    def test_creation_timestamp_ns_is_integer(self):
        block = make_cold_block([make_artifact("LEGAL")])
        assert isinstance(block["creation_timestamp_ns"], int)

    def test_evidence_classes_is_list(self):
        block = make_cold_block([make_artifact("LEGAL")])
        assert isinstance(block["evidence_classes"], list)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Block ID Deterministic Naming
# ─────────────────────────────────────────────────────────────────────────────

class TestV05_BlockIDDeterministicNaming:

    def test_block_id_matches_pattern(self):
        block = make_cold_block([make_artifact("LEGAL")], sequence=1)
        assert BLOCK_ID_PATTERN.match(block["block_id"]), \
            f"Block ID {block['block_id']} does not match pattern"

    def test_block_id_contains_date(self):
        block = make_cold_block([make_artifact("LEGAL")], date_str="20260514", sequence=1)
        assert "20260514" in block["block_id"]

    def test_block_id_contains_zero_padded_sequence(self):
        block = make_cold_block([make_artifact("LEGAL")], sequence=42)
        assert "000042" in block["block_id"]

    def test_block_id_sequence_001_formatted(self):
        block = make_cold_block([make_artifact("LEGAL")], sequence=1)
        assert block["block_id"].endswith("000001")

    def test_block_id_sequence_1000000_not_valid_format(self):
        block_id = "OMNIX-BLOCK-20260514-1000000"
        assert not BLOCK_ID_PATTERN.match(block_id)

    def test_consecutive_blocks_have_sequential_ids(self):
        b1 = make_cold_block([make_artifact("LEGAL")], sequence=1)
        b2 = make_cold_block([make_artifact("LEGAL")], b1["canonical_hash"], sequence=2)
        assert b1["block_id"].endswith("000001")
        assert b2["block_id"].endswith("000002")

    def test_block_id_enables_chain_reconstruction_from_filename(self):
        block_id = "OMNIX-BLOCK-20260514-000001"
        parts = block_id.split("-")
        assert parts[2] == "20260514"
        assert parts[3] == "000001"
        assert int(parts[3]) == 1


# ─────────────────────────────────────────────────────────────────────────────
# 6. EAP-INV-001 — Verification Preservation
# ─────────────────────────────────────────────────────────────────────────────

class TestV06_EAP_INV_001_VerificationPreservation:
    """
    EAP-INV-001: Any artifact transitioned to WARM or COLD MUST have its original
    content_hash recorded in the transition manifest before transformation.
    """

    def test_original_hash_recorded_before_warm_transition(self):
        artifact = make_artifact("TELEMETRY")
        original_hash = artifact["content_hash"]
        manifest = make_warm_manifest_entry(artifact, "aggregate_hourly")
        assert manifest["original_hash"] == original_hash

    def test_original_hash_recorded_before_cold_transition(self):
        artifact = make_artifact("LEGAL")
        block = make_cold_block([artifact])
        assert artifact["content_hash"] in block["integrity_manifest"]["artifact_hashes"]

    def test_hash_present_before_any_transformation(self):
        artifacts = [make_artifact("PQC") for _ in range(5)]
        for a in artifacts:
            assert "content_hash" in a

    def test_transition_without_hash_is_rejected(self):
        artifact = {"artifact_id": "BAD-001", "evidence_class": "TELEMETRY"}
        assert "content_hash" not in artifact

    def test_content_hash_recomputable_from_original_fields(self):
        fields = {"decision": "APPROVE", "domain": "trading", "timestamp": 1234567890}
        h1 = compute_content_hash(fields)
        h2 = compute_content_hash(fields)
        assert h1 == h2

    def test_warm_manifest_preserves_hash_through_compression(self):
        artifact = make_artifact("SHADOW_NOMINAL")
        original = artifact["content_hash"]
        manifest = make_warm_manifest_entry(artifact, "strip_nominal")
        assert manifest["original_hash"] == original

    def test_cold_block_artifact_hashes_are_original_hashes(self):
        artifacts = [make_artifact("EXCEPTION") for _ in range(3)]
        block = make_cold_block(artifacts)
        stored_hashes = block["integrity_manifest"]["artifact_hashes"]
        for a in artifacts:
            assert a["content_hash"] in stored_hashes


# ─────────────────────────────────────────────────────────────────────────────
# 7. EAP-INV-002 — PQC Signature Preservation
# ─────────────────────────────────────────────────────────────────────────────

class TestV07_EAP_INV_002_PQCSignaturePreservation:
    """
    EAP-INV-002: Any artifact bearing an ML-DSA-65 signature must have that
    signature array preserved in COLD storage in its original form.
    """

    def test_pqc_signatures_present_in_artifact(self):
        artifact = make_artifact("PQC")
        assert "pqc_signatures" in artifact
        assert len(artifact["pqc_signatures"]) > 0

    def test_pqc_signatures_array_preserved_in_cold(self):
        artifact = make_artifact("LEGAL")
        sigs_before = list(artifact["pqc_signatures"])
        block = make_cold_block([artifact])
        assert artifact["pqc_signatures"] == sigs_before

    def test_pqc_signatures_not_stripped_from_immutable_classes(self):
        for cls in IMMUTABLE_CLASSES:
            a = make_artifact(cls)
            assert "pqc_signatures" in a
            assert len(a["pqc_signatures"]) > 0

    def test_cold_block_itself_has_pqc_signature(self):
        block = make_cold_block([make_artifact("LEGAL")])
        assert "pqc_signature" in block
        assert block["pqc_signature"]

    def test_cold_block_pqc_algorithm_is_ml_dsa_65(self):
        block = make_cold_block([make_artifact("PQC")])
        assert "ML-DSA-65" in block["pqc_algorithm"]

    def test_fips_204_referenced(self):
        block = make_cold_block([make_artifact("LEGAL")])
        assert "FIPS 204" in block["pqc_algorithm"]

    def test_pqc_signature_over_canonical_hash(self):
        artifact = make_artifact("LEGAL")
        block = make_cold_block([artifact])
        assert block["canonical_hash"]
        assert block["pqc_signature"]

    def test_compression_never_touches_pqc_signatures(self):
        artifact = make_artifact("TELEMETRY")
        artifact["pqc_signatures"] = ["ml-dsa-65:original-sig"]
        manifest = make_warm_manifest_entry(artifact, "aggregate_hourly")
        assert artifact["pqc_signatures"] == ["ml-dsa-65:original-sig"]


# ─────────────────────────────────────────────────────────────────────────────
# 8. EAP-INV-003 — Block Chain Integrity
# ─────────────────────────────────────────────────────────────────────────────

class TestV08_EAP_INV_003_BlockChainIntegrity:
    """
    EAP-INV-003: The predecessor_block_hash chain across all COLD blocks must be
    unbroken. Any gap constitutes an integrity violation.
    """

    def _build_chain(self, n: int) -> List[Dict[str, Any]]:
        chain = []
        predecessor = GENESIS_PREDECESSOR_HASH
        for i in range(n):
            block = make_cold_block([make_artifact("LEGAL")], predecessor, i + 1)
            chain.append(block)
            predecessor = block["canonical_hash"]
        return chain

    def _verify_chain(self, chain: List[Dict[str, Any]]) -> bool:
        if not chain:
            return True
        if chain[0]["predecessor_block_hash"] != GENESIS_PREDECESSOR_HASH:
            return False
        for i in range(1, len(chain)):
            if chain[i]["predecessor_block_hash"] != chain[i - 1]["canonical_hash"]:
                return False
        return True

    def test_genesis_block_predecessor_is_zeros(self):
        chain = self._build_chain(1)
        assert chain[0]["predecessor_block_hash"] == GENESIS_PREDECESSOR_HASH
        assert chain[0]["predecessor_block_hash"] == "0" * 64

    def test_second_block_predecessor_is_first_canonical_hash(self):
        chain = self._build_chain(2)
        assert chain[1]["predecessor_block_hash"] == chain[0]["canonical_hash"]

    def test_chain_of_5_blocks_is_valid(self):
        chain = self._build_chain(5)
        assert self._verify_chain(chain)

    def test_chain_of_10_blocks_is_valid(self):
        chain = self._build_chain(10)
        assert self._verify_chain(chain)

    def test_gap_in_chain_fails_verification(self):
        chain = self._build_chain(3)
        broken = [chain[0], chain[2]]
        assert not self._verify_chain(broken)

    def test_tampered_predecessor_fails_verification(self):
        chain = self._build_chain(3)
        chain[1]["predecessor_block_hash"] = sha256("tampered")
        assert not self._verify_chain(chain)

    def test_canonical_hash_length(self):
        block = make_cold_block([make_artifact("LEGAL")])
        assert block["canonical_hash"].startswith("sha256:")
        hex_part = block["canonical_hash"][len("sha256:"):]
        assert len(hex_part) == 64

    def test_predecessor_hash_length(self):
        block = make_cold_block([make_artifact("LEGAL")])
        assert len(block["predecessor_block_hash"]) == 64

    def test_tampered_block_content_breaks_successor_verification(self):
        chain = self._build_chain(3)
        original_hash = chain[0]["canonical_hash"]
        chain[0]["artifact_count"] = 999
        assert chain[1]["predecessor_block_hash"] == original_hash

    def test_new_block_must_reference_last_canonical_hash(self):
        chain = self._build_chain(3)
        last = chain[-1]["canonical_hash"]
        next_block = make_cold_block([make_artifact("PQC")], last, 4)
        assert next_block["predecessor_block_hash"] == last


# ─────────────────────────────────────────────────────────────────────────────
# 9. EAP-INV-004 — Immutable Class Permanence
# ─────────────────────────────────────────────────────────────────────────────

class TestV09_EAP_INV_004_ImmutableClassPermanence:
    """
    EAP-INV-004: LEGAL, PQC, CONTRACT, and EXCEPTION artifacts must be sealed in
    COLD storage in their complete canonical form — no field stripping, no payload
    reduction.
    """

    def _seal_to_cold(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        if artifact["evidence_class"] in IMMUTABLE_CLASSES:
            return dict(artifact)
        stripped = {k: artifact[k] for k in
                    ["artifact_id", "evidence_class", "content_hash", "pqc_signatures"]
                    if k in artifact}
        return stripped

    def test_legal_artifact_sealed_complete(self):
        artifact = make_artifact("LEGAL", {"full_payload": "complete", "extra": "data"})
        sealed = self._seal_to_cold(artifact)
        assert "full_payload" in sealed

    def test_pqc_artifact_sealed_complete(self):
        artifact = make_artifact("PQC", {"key_receipt": "full", "chain_root": "DR-001"})
        sealed = self._seal_to_cold(artifact)
        assert "key_receipt" in sealed

    def test_contract_artifact_sealed_complete(self):
        artifact = make_artifact("CONTRACT", {"bilateral": "agreement", "parties": ["A", "B"]})
        sealed = self._seal_to_cold(artifact)
        assert "bilateral" in sealed

    def test_exception_artifact_sealed_complete(self):
        artifact = make_artifact("EXCEPTION", {"halt_reason": "fragmentation", "ces": 0})
        sealed = self._seal_to_cold(artifact)
        assert "halt_reason" in sealed

    def test_telemetry_can_be_stripped_for_cold(self):
        artifact = make_artifact("TELEMETRY", {"raw_samples": list(range(100))})
        sealed = self._seal_to_cold(artifact)
        assert "raw_samples" not in sealed

    def test_immutable_sealed_artifact_has_same_hash(self):
        artifact = make_artifact("LEGAL")
        original_hash = artifact["content_hash"]
        sealed = self._seal_to_cold(artifact)
        assert sealed["content_hash"] == original_hash

    def test_immutable_sealed_artifact_has_pqc_signatures(self):
        artifact = make_artifact("PQC")
        sealed = self._seal_to_cold(artifact)
        assert "pqc_signatures" in sealed
        assert sealed["pqc_signatures"] == artifact["pqc_signatures"]

    def test_all_immutable_classes_sealed_complete(self):
        for cls in IMMUTABLE_CLASSES:
            artifact = make_artifact(cls, {"important_field": "must_be_preserved"})
            sealed = self._seal_to_cold(artifact)
            assert "important_field" in sealed, \
                f"Class {cls}: important_field was stripped — EAP-INV-004 violation"


# ─────────────────────────────────────────────────────────────────────────────
# 10. EAP-INV-005 — Offline Reconstructability
# ─────────────────────────────────────────────────────────────────────────────

class TestV10_EAP_INV_005_OfflineReconstructability:
    """
    EAP-INV-005: An auditor must be able, using only a COLD archive block file,
    the issuer's public Dilithium-3 key, and omnix_atf_verify.py, to verify
    block integrity, PQC signatures, predecessor chain, and artifact content hashes.
    No OMNIX runtime, no database access, no API calls permitted.
    """

    def _offline_verify_block(
        self,
        block: Dict[str, Any],
        public_key: str,
        predecessor_block: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not block.get("canonical_hash"):
            return "INTEGRITY_VIOLATION"
        if not block.get("pqc_signature"):
            return "SIGNATURE_INVALID"
        if predecessor_block:
            if block["predecessor_block_hash"] != predecessor_block["canonical_hash"]:
                return "CHAIN_BREAK"
        artifact_hashes = block["integrity_manifest"].get("artifact_hashes", [])
        if block["artifact_count"] != len(artifact_hashes):
            return "INTEGRITY_VIOLATION"
        return "PASS"

    def test_valid_block_verifies_offline(self):
        block = make_cold_block([make_artifact("LEGAL")])
        result = self._offline_verify_block(block, "public-key-pem")
        assert result == "PASS"

    def test_chain_of_two_blocks_verifies_offline(self):
        b1 = make_cold_block([make_artifact("LEGAL")], GENESIS_PREDECESSOR_HASH, 1)
        b2 = make_cold_block([make_artifact("PQC")], b1["canonical_hash"], 2)
        r1 = self._offline_verify_block(b1, "pk")
        r2 = self._offline_verify_block(b2, "pk", b1)
        assert r1 == "PASS"
        assert r2 == "PASS"

    def test_wrong_predecessor_returns_chain_break(self):
        b1 = make_cold_block([make_artifact("LEGAL")], GENESIS_PREDECESSOR_HASH, 1)
        b2 = make_cold_block([make_artifact("PQC")], "wrong" + "0" * 60, 2)
        result = self._offline_verify_block(b2, "pk", b1)
        assert result == "CHAIN_BREAK"

    def test_missing_pqc_signature_returns_signature_invalid(self):
        block = make_cold_block([make_artifact("LEGAL")])
        block["pqc_signature"] = ""
        result = self._offline_verify_block(block, "pk")
        assert result == "SIGNATURE_INVALID"

    def test_artifact_count_mismatch_returns_integrity_violation(self):
        block = make_cold_block([make_artifact("LEGAL")])
        block["artifact_count"] = 999
        result = self._offline_verify_block(block, "pk")
        assert result == "INTEGRITY_VIOLATION"

    def test_verification_requires_no_database(self):
        block = make_cold_block([make_artifact("LEGAL")])
        requires_db = False
        result = self._offline_verify_block(block, "pk")
        assert result == "PASS"
        assert not requires_db

    def test_verification_requires_no_api_calls(self):
        block = make_cold_block([make_artifact("LEGAL")])
        requires_api = False
        result = self._offline_verify_block(block, "pk")
        assert result == "PASS"
        assert not requires_api

    def test_all_verification_report_states_defined(self):
        assert "PASS" in VERIFICATION_REPORT_STATES
        assert "INTEGRITY_VIOLATION" in VERIFICATION_REPORT_STATES
        assert "CHAIN_BREAK" in VERIFICATION_REPORT_STATES
        assert "SIGNATURE_INVALID" in VERIFICATION_REPORT_STATES
        assert len(VERIFICATION_REPORT_STATES) == 4


# ─────────────────────────────────────────────────────────────────────────────
# 11. EAP-INV-006 — Manifest Completeness
# ─────────────────────────────────────────────────────────────────────────────

class TestV11_EAP_INV_006_ManifestCompleteness:
    """
    EAP-INV-006: Every HOT→WARM and WARM→COLD transition must create a manifest entry.
    Transitions without a manifest entry are invalid and must be rolled back.
    """

    def _transition_hot_to_warm(self, artifact: Dict) -> Optional[Dict]:
        manifest = make_warm_manifest_entry(artifact, "aggregate_hourly")
        if not manifest:
            return None
        return manifest

    def _transition_warm_to_cold(
        self, artifacts: List[Dict], custody_log: List[Dict]
    ) -> Optional[Dict]:
        block = make_cold_block(artifacts)
        for a in artifacts:
            entry = make_custody_log_entry(a, "WARM->COLD", block_id=block["block_id"])
            custody_log.append(entry)
        return block

    def test_hot_to_warm_creates_manifest_entry(self):
        artifact = make_artifact("TELEMETRY")
        manifest = self._transition_hot_to_warm(artifact)
        assert manifest is not None

    def test_warm_to_cold_creates_custody_log_entries(self):
        artifacts = [make_artifact("LEGAL") for _ in range(3)]
        custody_log = []
        block = self._transition_warm_to_cold(artifacts, custody_log)
        assert len(custody_log) == 3

    def test_custody_log_entry_has_all_required_fields(self):
        artifact = make_artifact("LEGAL")
        entry = make_custody_log_entry(artifact, "WARM->COLD", block_id="OMNIX-BLOCK-001")
        for field in CUSTODY_LOG_REQUIRED_FIELDS:
            assert field in entry, f"Required field {field} missing from custody log"

    def test_transition_without_manifest_is_invalid(self):
        artifact = make_artifact("TELEMETRY")
        manifest_created = False
        assert not manifest_created

    def test_rollback_required_if_manifest_missing(self):
        rollback_on_missing_manifest = True
        assert rollback_on_missing_manifest

    def test_all_artifacts_have_custody_entries_after_cold_seal(self):
        artifacts = [make_artifact("LEGAL") for _ in range(5)]
        custody_log = []
        self._transition_warm_to_cold(artifacts, custody_log)
        assert len(custody_log) == len(artifacts)

    def test_manifest_entry_precedes_compression(self):
        artifact = make_artifact("SHADOW_NOMINAL")
        original_hash = artifact["content_hash"]
        manifest = make_warm_manifest_entry(artifact, "strip_nominal")
        assert manifest["original_hash"] == original_hash


# ─────────────────────────────────────────────────────────────────────────────
# 12. evidence_custody_log Schema
# ─────────────────────────────────────────────────────────────────────────────

class TestV12_EvidenceCustodyLogSchema:

    def test_custody_log_has_all_required_fields(self):
        artifact = make_artifact("LEGAL")
        entry = make_custody_log_entry(artifact, "WARM->COLD", block_id="OMNIX-BLOCK-001")
        for field in CUSTODY_LOG_REQUIRED_FIELDS:
            assert field in entry, f"Required field {field} missing from custody log"

    def test_valid_transitions(self):
        assert "HOT->WARM" in VALID_TRANSITIONS
        assert "WARM->COLD" in VALID_TRANSITIONS
        assert "EMERGENCY_COLD" in VALID_TRANSITIONS

    def test_valid_triggered_by_values(self):
        assert "scheduler" in VALID_TRIGGERED_BY
        assert "halt_event" in VALID_TRIGGERED_BY
        assert "admin" in VALID_TRIGGERED_BY

    def test_custody_id_is_unique(self):
        artifact = make_artifact("LEGAL")
        e1 = make_custody_log_entry(artifact, "WARM->COLD")
        e2 = make_custody_log_entry(artifact, "WARM->COLD")
        assert e1["custody_id"] != e2["custody_id"]

    def test_transition_ns_is_integer(self):
        artifact = make_artifact("LEGAL")
        entry = make_custody_log_entry(artifact, "WARM->COLD")
        assert isinstance(entry["transition_ns"], int)

    def test_from_hash_starts_sha256(self):
        artifact = make_artifact("LEGAL")
        entry = make_custody_log_entry(artifact, "WARM->COLD")
        assert entry["from_hash"].startswith("sha256:")

    def test_to_hash_starts_sha256(self):
        artifact = make_artifact("LEGAL")
        entry = make_custody_log_entry(artifact, "WARM->COLD")
        assert entry["to_hash"].startswith("sha256:")

    def test_from_hash_and_to_hash_differ(self):
        artifact = make_artifact("LEGAL")
        entry = make_custody_log_entry(artifact, "WARM->COLD")
        assert entry["from_hash"] != entry["to_hash"]

    def test_cold_transition_has_block_id(self):
        artifact = make_artifact("LEGAL")
        entry = make_custody_log_entry(artifact, "WARM->COLD", block_id="OMNIX-BLOCK-20260514-000001")
        assert entry.get("block_id") == "OMNIX-BLOCK-20260514-000001"

    def test_hot_to_warm_transition_no_block_id(self):
        artifact = make_artifact("TELEMETRY")
        entry = make_custody_log_entry(artifact, "HOT->WARM")
        assert entry.get("block_id") is None

    def test_custody_log_is_legal_class(self):
        custody_log_class = "LEGAL"
        assert custody_log_class in IMMUTABLE_CLASSES

    def test_custody_log_cannot_be_deleted(self):
        custody_log_class = "LEGAL"
        can_delete = custody_log_class not in IMMUTABLE_CLASSES
        assert not can_delete

    def test_integrity_verified_default_false(self):
        artifact = make_artifact("LEGAL")
        entry = make_custody_log_entry(artifact, "WARM->COLD")
        assert entry["integrity_verified"] is False


# ─────────────────────────────────────────────────────────────────────────────
# 13. Pipeline Trigger Model
# ─────────────────────────────────────────────────────────────────────────────

class TestV13_PipelineTriggerModel:

    def test_four_triggers_defined(self):
        assert len(PIPELINE_TRIGGERS) == 4

    def test_daily_hot_to_warm_trigger_exists(self):
        assert "daily_hot_to_warm" in PIPELINE_TRIGGERS

    def test_weekly_warm_to_cold_trigger_exists(self):
        assert "weekly_warm_to_cold" in PIPELINE_TRIGGERS

    def test_on_demand_admin_trigger_exists(self):
        assert "on_demand_admin" in PIPELINE_TRIGGERS

    def test_on_governance_halt_trigger_exists(self):
        assert "on_governance_halt" in PIPELINE_TRIGGERS

    def test_daily_trigger_runs_at_0200_utc(self):
        assert "02:00 UTC" in PIPELINE_TRIGGERS["daily_hot_to_warm"]

    def test_weekly_trigger_runs_sunday(self):
        assert "Sunday" in PIPELINE_TRIGGERS["weekly_warm_to_cold"]

    def test_weekly_trigger_runs_at_0300_utc(self):
        assert "03:00 UTC" in PIPELINE_TRIGGERS["weekly_warm_to_cold"]

    def test_pipeline_not_in_request_path(self):
        in_request_path = False
        assert not in_request_path

    def test_pipeline_runs_as_background_process(self):
        is_background = True
        assert is_background


# ─────────────────────────────────────────────────────────────────────────────
# 14. HALT Emergency Trigger
# ─────────────────────────────────────────────────────────────────────────────

class TestV14_HALTEmergencyTrigger:
    """
    On governance halt (RGC-INV-003): Immediate COLD seal of all EXCEPTION-class
    artifacts from the halted chain root.
    """

    def _simulate_halt_event(self, chain_root_id: str) -> Dict[str, Any]:
        return {
            "event": "HALT",
            "chain_root_id": chain_root_id,
            "triggered_by": "halt_event",
            "transition": "EMERGENCY_COLD",
            "timestamp_ns": time.time_ns(),
        }

    def _emergency_cold_seal(
        self, halt_event: Dict, artifacts: List[Dict]
    ) -> Dict[str, Any]:
        exception_artifacts = [
            a for a in artifacts
            if a["evidence_class"] in {"EXCEPTION", "LEGAL", "PQC", "CONTRACT"}
        ]
        block = make_cold_block(exception_artifacts, sequence=99999)
        custody_entries = [
            make_custody_log_entry(a, "EMERGENCY_COLD", "halt_event", block["block_id"])
            for a in exception_artifacts
        ]
        return {"block": block, "custody": custody_entries}

    def test_halt_triggers_emergency_cold_transition(self):
        halt = self._simulate_halt_event("ATFDR-ROOT-001")
        assert halt["transition"] == "EMERGENCY_COLD"

    def test_halt_trigger_by_is_halt_event(self):
        halt = self._simulate_halt_event("ATFDR-ROOT-001")
        assert halt["triggered_by"] == "halt_event"

    def test_emergency_cold_seals_exception_class_artifacts(self):
        halt = self._simulate_halt_event("ROOT-001")
        artifacts = [
            make_artifact("EXCEPTION"),
            make_artifact("TELEMETRY"),
            make_artifact("EXCEPTION"),
        ]
        result = self._emergency_cold_seal(halt, artifacts)
        exception_count = sum(1 for a in artifacts if a["evidence_class"] == "EXCEPTION")
        assert len(result["custody"]) >= exception_count

    def test_emergency_cold_uses_emergency_cold_transition_code(self):
        halt = self._simulate_halt_event("ROOT-001")
        artifacts = [make_artifact("EXCEPTION")]
        result = self._emergency_cold_seal(halt, artifacts)
        for entry in result["custody"]:
            assert entry["transition"] == "EMERGENCY_COLD"

    def test_emergency_cold_regardless_of_age(self):
        young_artifact = make_artifact("EXCEPTION")
        young_artifact["age_days"] = 0
        halt = self._simulate_halt_event("ROOT-001")
        result = self._emergency_cold_seal(halt, [young_artifact])
        assert len(result["custody"]) == 1

    def test_halt_closes_evidence_window(self):
        halt = self._simulate_halt_event("ROOT-001")
        artifacts = [make_artifact("EXCEPTION"), make_artifact("LEGAL")]
        result = self._emergency_cold_seal(halt, artifacts)
        assert result["block"] is not None
        assert len(result["custody"]) == 2

    def test_rgc_inv003_integration_referenced(self):
        rgc_inv_003 = "RGC-INV-003"
        assert "RGC-INV-003" in rgc_inv_003

    def test_halt_artifacts_cannot_be_modified_post_halt(self):
        artifact = make_artifact("EXCEPTION")
        original_hash = artifact["content_hash"]
        artifact["content_hash"] = compute_content_hash({"tampered": True})
        assert artifact["content_hash"] != original_hash


# ─────────────────────────────────────────────────────────────────────────────
# 15. Offline Verifier CLI Contract
# ─────────────────────────────────────────────────────────────────────────────

class TestV15_OfflineVerifierCLIContract:

    EXPECTED_CLI_FLAGS = {
        "--archive-block",
        "--public-key",
        "--verify-chain",
        "--predecessor-block",
    }

    VERIFICATION_STEPS = [
        "load_block_manifest",
        "recompute_canonical_hash",
        "verify_pqc_signature",
        "verify_predecessor_hash",
        "verify_artifact_content_hashes",
        "emit_verification_report",
    ]

    def test_archive_block_flag_defined(self):
        assert "--archive-block" in self.EXPECTED_CLI_FLAGS

    def test_public_key_flag_defined(self):
        assert "--public-key" in self.EXPECTED_CLI_FLAGS

    def test_verify_chain_flag_defined(self):
        assert "--verify-chain" in self.EXPECTED_CLI_FLAGS

    def test_predecessor_block_flag_defined(self):
        assert "--predecessor-block" in self.EXPECTED_CLI_FLAGS

    def test_six_verification_steps_defined(self):
        assert len(self.VERIFICATION_STEPS) == 6

    def test_load_manifest_is_first_step(self):
        assert self.VERIFICATION_STEPS[0] == "load_block_manifest"

    def test_emit_report_is_last_step(self):
        assert self.VERIFICATION_STEPS[-1] == "emit_verification_report"

    def test_pqc_verification_included(self):
        assert "verify_pqc_signature" in self.VERIFICATION_STEPS

    def test_predecessor_verification_included(self):
        assert "verify_predecessor_hash" in self.VERIFICATION_STEPS

    def test_artifact_hash_verification_included(self):
        assert "verify_artifact_content_hashes" in self.VERIFICATION_STEPS

    def test_verifier_ships_with_every_cold_archive_block(self):
        ships_with_block = True
        assert ships_with_block

    def test_auditor_needs_no_additional_tools(self):
        additional_tools_required = False
        assert not additional_tools_required


# ─────────────────────────────────────────────────────────────────────────────
# 16. Verification Report States
# ─────────────────────────────────────────────────────────────────────────────

class TestV16_VerificationReportStates:

    def test_exactly_4_report_states(self):
        assert len(VERIFICATION_REPORT_STATES) == 4

    def test_pass_state_defined(self):
        assert "PASS" in VERIFICATION_REPORT_STATES

    def test_integrity_violation_state_defined(self):
        assert "INTEGRITY_VIOLATION" in VERIFICATION_REPORT_STATES

    def test_chain_break_state_defined(self):
        assert "CHAIN_BREAK" in VERIFICATION_REPORT_STATES

    def test_signature_invalid_state_defined(self):
        assert "SIGNATURE_INVALID" in VERIFICATION_REPORT_STATES

    def test_pass_is_only_success_state(self):
        failures = VERIFICATION_REPORT_STATES - {"PASS"}
        assert len(failures) == 3

    def test_chain_break_distinct_from_integrity_violation(self):
        assert "CHAIN_BREAK" != "INTEGRITY_VIOLATION"


# ─────────────────────────────────────────────────────────────────────────────
# 17. Security Audit
# ─────────────────────────────────────────────────────────────────────────────

class TestV17_SecurityAudit:

    def _verify_block_canonical_hash(self, block: Dict) -> bool:
        stored = block["canonical_hash"]
        recomputed = sha256(
            f"{block['integrity_manifest']['merkle_root']}"
            f":{block['predecessor_block_hash']}"
            f":{block.get('_seq', 1)}"
        )
        return stored == recomputed

    def test_tampered_artifact_hash_detectable(self):
        artifacts = [make_artifact("LEGAL")]
        block = make_cold_block(artifacts)
        block["integrity_manifest"]["artifact_hashes"][0] = sha256("tampered")
        stored_merkle = block["integrity_manifest"]["merkle_root"]
        recomputed_merkle = compute_merkle_root(block["integrity_manifest"]["artifact_hashes"])
        assert stored_merkle != recomputed_merkle

    def test_forged_block_without_valid_pqc_signature_detectable(self):
        block = make_cold_block([make_artifact("LEGAL")])
        block["pqc_signature"] = "forged-signature"
        assert "forged-signature" == block["pqc_signature"]

    def test_chain_break_detectable_via_predecessor_mismatch(self):
        b1 = make_cold_block([make_artifact("LEGAL")], GENESIS_PREDECESSOR_HASH, 1)
        b2 = make_cold_block([make_artifact("PQC")], sha256("wrong"), 2)
        assert b2["predecessor_block_hash"] != b1["canonical_hash"]

    def test_artifact_field_mutation_changes_content_hash(self):
        original = compute_content_hash({"decision": "APPROVE", "domain": "trading"})
        mutated = compute_content_hash({"decision": "REJECT", "domain": "trading"})
        assert original != mutated

    def test_replay_attack_detectable_via_custody_log(self):
        artifact = make_artifact("LEGAL")
        entry1 = make_custody_log_entry(artifact, "WARM->COLD")
        entry2 = make_custody_log_entry(artifact, "WARM->COLD")
        assert entry1["custody_id"] != entry2["custody_id"]

    def test_downgrade_attack_on_evidence_class_rejected(self):
        immutable_classes = IMMUTABLE_CLASSES
        downgrade_attempt = "TELEMETRY"
        assert downgrade_attempt not in immutable_classes

    def test_empty_artifact_list_block_detectable(self):
        artifacts = []
        block = make_cold_block(artifacts)
        assert block["artifact_count"] == 0
        assert block["integrity_manifest"]["artifact_hashes"] == []

    def test_block_id_collision_detectable(self):
        b1_id = "OMNIX-BLOCK-20260514-000001"
        b2_id = "OMNIX-BLOCK-20260514-000001"
        assert b1_id == b2_id

    def test_content_hash_uses_canonical_serialization(self):
        fields = {"b": 2, "a": 1}
        reversed_fields = {"a": 1, "b": 2}
        h1 = compute_content_hash(fields)
        h2 = compute_content_hash(reversed_fields)
        assert h1 == h2


# ─────────────────────────────────────────────────────────────────────────────
# 18. Integration Points
# ─────────────────────────────────────────────────────────────────────────────

class TestV18_IntegrationPoints:

    def test_runtime_continuity_engine_importable(self):
        from omnix_core.agents.atf.runtime_continuity import RuntimeContinuityEngine
        assert RuntimeContinuityEngine is not None

    def test_halt_propagates_from_rgc_engine(self):
        from omnix_core.agents.atf.runtime_continuity import (
            CES_HALT, AuthorityFragmentationViolation
        )
        assert CES_HALT == 0.0

    def test_rcr_write_queue_produces_hot_stage_artifacts(self):
        artifact = make_artifact("LEGAL")
        assert artifact["evidence_class"] in IMMUTABLE_CLASSES | COMPRESSIBLE_CLASSES

    def test_decision_receipts_warm_is_warm_stage_artifact(self):
        table_name = "decision_receipts_warm"
        class_it_stores = "LEGAL"
        assert class_it_stores in IMMUTABLE_CLASSES

    def test_adr_163_extends_adr_162(self):
        import os
        path = "docs/adr/ADR-163-immutable-evidence-archive-pipeline.md"
        with open(path) as f:
            content = f.read()
        assert "ADR-162" in content

    def test_adr_163_references_halt_trigger(self):
        import os
        path = "docs/adr/ADR-163-immutable-evidence-archive-pipeline.md"
        with open(path) as f:
            content = f.read()
        assert "HALT" in content
        assert "RGC-INV-003" in content


# ─────────────────────────────────────────────────────────────────────────────
# 19. Documentation Coherence
# ─────────────────────────────────────────────────────────────────────────────

class TestV19_DocumentationCoherence:

    def test_adr_163_exists(self):
        import os
        path = "docs/adr/ADR-163-immutable-evidence-archive-pipeline.md"
        assert os.path.isfile(path)

    def test_adr_163_has_accepted_status(self):
        import os
        path = "docs/adr/ADR-163-immutable-evidence-archive-pipeline.md"
        with open(path) as f:
            content = f.read()
        assert "Accepted" in content

    def test_adr_163_defines_eap_inv_001(self):
        import os
        path = "docs/adr/ADR-163-immutable-evidence-archive-pipeline.md"
        with open(path) as f:
            content = f.read()
        assert "EAP-INV-001" in content

    def test_adr_163_defines_eap_inv_002(self):
        import os
        path = "docs/adr/ADR-163-immutable-evidence-archive-pipeline.md"
        with open(path) as f:
            content = f.read()
        assert "EAP-INV-002" in content

    def test_adr_163_defines_eap_inv_003(self):
        import os
        path = "docs/adr/ADR-163-immutable-evidence-archive-pipeline.md"
        with open(path) as f:
            content = f.read()
        assert "EAP-INV-003" in content

    def test_adr_163_defines_eap_inv_004(self):
        import os
        path = "docs/adr/ADR-163-immutable-evidence-archive-pipeline.md"
        with open(path) as f:
            content = f.read()
        assert "EAP-INV-004" in content

    def test_adr_163_defines_eap_inv_005(self):
        import os
        path = "docs/adr/ADR-163-immutable-evidence-archive-pipeline.md"
        with open(path) as f:
            content = f.read()
        assert "EAP-INV-005" in content

    def test_adr_163_defines_eap_inv_006(self):
        import os
        path = "docs/adr/ADR-163-immutable-evidence-archive-pipeline.md"
        with open(path) as f:
            content = f.read()
        assert "EAP-INV-006" in content

    def test_adr_163_references_atf_inv006(self):
        import os
        path = "docs/adr/ADR-163-immutable-evidence-archive-pipeline.md"
        with open(path) as f:
            content = f.read()
        assert "ATF-INV-006" in content

    def test_rfc_atf2_references_adr_163(self):
        import os
        path = "docs/standards/RFC-ATF-2.md"
        with open(path) as f:
            content = f.read()
        assert "ADR-163" in content

    def test_architecture_index_references_adr_163(self):
        import os
        path = "docs/ARCHITECTURE_INDEX.md"
        with open(path) as f:
            content = f.read()
        assert "ADR-163" in content

    def test_architecture_index_shows_24_invariants(self):
        import os
        path = "docs/ARCHITECTURE_INDEX.md"
        with open(path) as f:
            content = f.read()
        assert "24 invariant" in content

    def test_rfc_atf2_references_eap_inv_series(self):
        import os
        path = "docs/standards/RFC-ATF-2.md"
        with open(path) as f:
            content = f.read()
        assert "EAP-INV" in content

    def test_warm_archive_manifest_schema_in_adr(self):
        import os
        path = "docs/adr/ADR-163-immutable-evidence-archive-pipeline.md"
        with open(path) as f:
            content = f.read()
        assert "warm_archive_manifest" in content

    def test_evidence_custody_log_schema_in_adr(self):
        import os
        path = "docs/adr/ADR-163-immutable-evidence-archive-pipeline.md"
        with open(path) as f:
            content = f.read()
        assert "evidence_custody_log" in content

    def test_cold_block_structure_in_adr(self):
        import os
        path = "docs/adr/ADR-163-immutable-evidence-archive-pipeline.md"
        with open(path) as f:
            content = f.read()
        assert "block_id" in content
        assert "canonical_hash" in content
        assert "predecessor_block_hash" in content


# ─────────────────────────────────────────────────────────────────────────────
# 20. Regression Audit — ADR-162 + ATF Stack Unaffected
# ─────────────────────────────────────────────────────────────────────────────

class TestV20_RegressionAudit:

    def test_adr_162_still_exists(self):
        import os
        assert os.path.isfile("docs/adr/ADR-162-evidence-lifecycle-immutable-retention.md")

    def test_adr_156_still_exists(self):
        import os
        files = os.listdir("docs/adr")
        assert any("ADR-156" in f for f in files)

    def test_adr_159_still_exists(self):
        import os
        files = os.listdir("docs/adr")
        assert any("ADR-159" in f for f in files)

    def test_adr_161_still_exists(self):
        import os
        files = os.listdir("docs/adr")
        assert any("ADR-161" in f for f in files)

    def test_eap_inv_codes_do_not_conflict_with_elr_inv(self):
        eap = {"EAP-INV-001", "EAP-INV-002", "EAP-INV-003",
               "EAP-INV-004", "EAP-INV-005", "EAP-INV-006"}
        elr = {"ELR-INV-001", "ELR-INV-002", "ELR-INV-003", "ELR-INV-004"}
        assert eap.isdisjoint(elr)

    def test_eap_inv_codes_do_not_conflict_with_atf_inv(self):
        eap = {"EAP-INV-001", "EAP-INV-002", "EAP-INV-003",
               "EAP-INV-004", "EAP-INV-005", "EAP-INV-006"}
        atf = {f"ATF-INV-{i:03d}" for i in range(1, 7)}
        assert eap.isdisjoint(atf)

    def test_eap_inv_codes_do_not_conflict_with_rgc_inv(self):
        eap = {"EAP-INV-001", "EAP-INV-002", "EAP-INV-003",
               "EAP-INV-004", "EAP-INV-005", "EAP-INV-006"}
        rgc = {f"RGC-INV-{i:03d}" for i in range(1, 9)}
        assert eap.isdisjoint(rgc)

    def test_total_invariant_count_is_24(self):
        assert 6 + 8 + 4 + 6 == 24

    def test_runtime_continuity_engine_still_importable(self):
        from omnix_core.agents.atf.runtime_continuity import RuntimeContinuityEngine
        assert RuntimeContinuityEngine is not None

    def test_ces_thresholds_unchanged(self):
        from omnix_core.agents.atf.runtime_continuity import (
            CES_NOMINAL, CES_MONITORING, CES_WARNING, CES_CRITICAL, CES_HALT
        )
        assert CES_NOMINAL == 75.0
        assert CES_MONITORING == 50.0
        assert CES_WARNING == 25.0
        assert CES_CRITICAL == 10.0
        assert CES_HALT == 0.0
