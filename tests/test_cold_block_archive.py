"""
OMNIX COLD Archive Block — Audit Test Suite
============================================
ADR-163: Immutable Evidence Archive Pipeline
ADR-162: Evidence Lifecycle & Immutable Retention

Coverage:
  · ColdBlockSealer (omnix_core/evidence/cold_block_sealer.py)
  · verify_archive_block() (docs/zenodo/submission_package/omnix_atf_verify.py)
  · All six EAP invariants (EAP-INV-001–006)
  · Cryptographic primitives (Merkle root, canonical hash, determinism)
  · Chain verification (predecessor linkage)
  · Tamper detection (artifact hash, block fields, predecessor)
  · Emergency seal trigger (halt_event / RGC-INV-003)
  · Warm manifest entries and shadow event classification
  · Edge cases: empty blocks, genesis block, unsorted hashes

Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import patch

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Module loading
# ─────────────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent


def _load_verifier():
    verifier_path = ROOT / "docs" / "zenodo" / "submission_package" / "omnix_atf_verify.py"
    spec   = importlib.util.spec_from_file_location("omnix_atf_verify", verifier_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["omnix_atf_verify"] = module
    spec.loader.exec_module(module)
    return module


verifier = _load_verifier()

from omnix_core.evidence.cold_block_sealer import (
    ColdBlockSealer,
    CustodyLogEntry,
    SealResult,
    SealedBlock,
    compute_canonical_hash,
    compute_merkle_root,
    create_warm_manifest_entry,
    classify_shadow_event,
    reduce_shadow_event,
    GENESIS_PREDECESSOR,
    HASH_ALGORITHM_V1,
    OMNIX_VERSION,
    PQC_ALGORITHM,
    IMMUTABLE_CLASSES,
)


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(obj: Dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _make_artifact(
    evidence_class: str = "LEGAL",
    idx: int = 0,
    extra: Optional[Dict] = None,
) -> Dict[str, Any]:
    base = {
        "artifact_id":   f"ATFDR-TEST-{uuid.uuid4().hex[:12].upper()}",
        "evidence_class": evidence_class,
        "domain":        "test",
        "index":         idx,
        "created_at":    "2026-05-15T00:00:00+00:00",
    }
    if extra:
        base.update(extra)
    exclude = {"content_hash", "pqc_signature", "pqc_algorithm"}
    clean   = {k: v for k, v in base.items() if k not in exclude}
    base["content_hash"] = _sha256(_canonical_json(clean))
    return base


def _make_artifacts(n: int, evidence_class: str = "LEGAL") -> List[Dict]:
    return [_make_artifact(evidence_class, i) for i in range(n)]


def _make_block_dict(
    artifacts: Optional[List[Dict]] = None,
    predecessor_hash: str = GENESIS_PREDECESSOR,
    block_id: Optional[str] = None,
    pqc_signature: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a minimal valid COLD block dict (no actual PQC signing)."""
    if artifacts is None:
        artifacts = _make_artifacts(3)
    if block_id is None:
        block_id = "OMNIX-BLOCK-20260515-000001"

    artifact_hashes = [a["content_hash"] for a in artifacts]
    evidence_classes = sorted({a.get("evidence_class", "UNKNOWN") for a in artifacts})
    merkle_root = compute_merkle_root(artifact_hashes)
    now_ns = time.time_ns()

    canonical = compute_canonical_hash(
        block_id=block_id,
        creation_timestamp_ns=now_ns,
        artifact_count=len(artifacts),
        evidence_classes=evidence_classes,
        merkle_root=merkle_root,
        predecessor_block_hash=predecessor_hash,
    )

    return {
        "block_id":               block_id,
        "creation_timestamp_ns":  now_ns,
        "artifact_count":         len(artifacts),
        "evidence_classes":       evidence_classes,
        "canonical_hash":         canonical,
        "predecessor_block_hash": predecessor_hash,
        "integrity_manifest": {
            "artifact_hashes": artifact_hashes,
            "merkle_root":     merkle_root,
            "hash_algorithm":  HASH_ALGORITHM_V1,
        },
        "pqc_signature": pqc_signature,
        "pqc_algorithm": PQC_ALGORITHM,
        "omnix_version": OMNIX_VERSION,
        "sealed_at":     "2026-05-15T00:00:00+00:00",
        "sealed_by":     "test",
        "seal_trigger":  "scheduler",
        "artifact_ids":  [a["artifact_id"] for a in artifacts],
    }


# ─────────────────────────────────────────────────────────────────────────────
# T01 — Merkle root determinism and correctness
# ─────────────────────────────────────────────────────────────────────────────

class TestMerkleRoot:
    def test_empty_block_returns_stable_root(self):
        root = compute_merkle_root([])
        assert root.startswith("sha256:")
        assert len(root) == 71

    def test_empty_block_deterministic(self):
        assert compute_merkle_root([]) == compute_merkle_root([])

    def test_single_hash_stable(self):
        h = "abc123" * 10
        root = compute_merkle_root([h])
        assert root.startswith("sha256:")

    def test_order_independent(self):
        hashes = ["aaaa", "bbbb", "cccc"]
        r1 = compute_merkle_root(hashes)
        r2 = compute_merkle_root(list(reversed(hashes)))
        assert r1 == r2, "Merkle root must be order-independent (hashes are sorted)"

    def test_changes_when_hash_changes(self):
        h1 = ["aaa", "bbb"]
        h2 = ["aaa", "ccc"]
        assert compute_merkle_root(h1) != compute_merkle_root(h2)

    def test_matches_verifier_implementation(self):
        hashes = ["deadbeef" * 8, "cafecafe" * 8]
        sealer_root   = compute_merkle_root(hashes)
        verifier_root = verifier._compute_merkle_root(hashes)
        assert sealer_root == verifier_root, "Sealer and verifier must produce identical Merkle roots"

    def test_sha256_prefix_present(self):
        root = compute_merkle_root(["abc"])
        assert root[:7] == "sha256:"

    def test_multiple_artifacts_stable(self):
        artifacts = _make_artifacts(50)
        hashes = [a["content_hash"] for a in artifacts]
        r1 = compute_merkle_root(hashes)
        r2 = compute_merkle_root(hashes)
        assert r1 == r2


# ─────────────────────────────────────────────────────────────────────────────
# T02 — Canonical hash determinism and correctness
# ─────────────────────────────────────────────────────────────────────────────

class TestCanonicalHash:
    def test_basic_hash_has_prefix(self):
        ch = compute_canonical_hash(
            block_id="OMNIX-BLOCK-20260515-000001",
            creation_timestamp_ns=1000000,
            artifact_count=5,
            evidence_classes=["LEGAL"],
            merkle_root="sha256:abc",
            predecessor_block_hash=GENESIS_PREDECESSOR,
        )
        assert ch.startswith("sha256:")
        assert len(ch) == 71

    def test_deterministic(self):
        kwargs = dict(
            block_id="OMNIX-BLOCK-20260515-000001",
            creation_timestamp_ns=1234567890,
            artifact_count=3,
            evidence_classes=["LEGAL", "PQC"],
            merkle_root="sha256:abc123",
            predecessor_block_hash=GENESIS_PREDECESSOR,
        )
        assert compute_canonical_hash(**kwargs) == compute_canonical_hash(**kwargs)

    def test_classes_order_independent(self):
        base = dict(
            block_id="OMNIX-BLOCK-20260515-000001",
            creation_timestamp_ns=1,
            artifact_count=1,
            merkle_root="sha256:x",
            predecessor_block_hash=GENESIS_PREDECESSOR,
        )
        ch1 = compute_canonical_hash(evidence_classes=["LEGAL", "PQC"], **base)
        ch2 = compute_canonical_hash(evidence_classes=["PQC", "LEGAL"], **base)
        assert ch1 == ch2, "evidence_classes are sorted before hashing"

    def test_changes_on_block_id_change(self):
        kwargs = dict(
            creation_timestamp_ns=1,
            artifact_count=1,
            evidence_classes=["LEGAL"],
            merkle_root="sha256:x",
            predecessor_block_hash=GENESIS_PREDECESSOR,
        )
        ch1 = compute_canonical_hash(block_id="OMNIX-BLOCK-20260515-000001", **kwargs)
        ch2 = compute_canonical_hash(block_id="OMNIX-BLOCK-20260515-000002", **kwargs)
        assert ch1 != ch2

    def test_changes_on_merkle_root_change(self):
        kwargs = dict(
            block_id="OMNIX-BLOCK-20260515-000001",
            creation_timestamp_ns=1,
            artifact_count=1,
            evidence_classes=["LEGAL"],
            predecessor_block_hash=GENESIS_PREDECESSOR,
        )
        ch1 = compute_canonical_hash(merkle_root="sha256:aaa", **kwargs)
        ch2 = compute_canonical_hash(merkle_root="sha256:bbb", **kwargs)
        assert ch1 != ch2

    def test_changes_on_predecessor_change(self):
        kwargs = dict(
            block_id="OMNIX-BLOCK-20260515-000001",
            creation_timestamp_ns=1,
            artifact_count=1,
            evidence_classes=["LEGAL"],
            merkle_root="sha256:x",
        )
        ch1 = compute_canonical_hash(predecessor_block_hash=GENESIS_PREDECESSOR, **kwargs)
        ch2 = compute_canonical_hash(predecessor_block_hash="sha256:otherpred", **kwargs)
        assert ch1 != ch2

    def test_matches_verifier_implementation(self):
        block = _make_block_dict()
        sealer_hash = compute_canonical_hash(
            block_id=block["block_id"],
            creation_timestamp_ns=block["creation_timestamp_ns"],
            artifact_count=block["artifact_count"],
            evidence_classes=block["evidence_classes"],
            merkle_root=block["integrity_manifest"]["merkle_root"],
            predecessor_block_hash=block["predecessor_block_hash"],
        )
        verifier_hash = verifier._compute_block_canonical_hash(block)
        assert sealer_hash == verifier_hash, \
            "Sealer and verifier must produce identical canonical hashes"


# ─────────────────────────────────────────────────────────────────────────────
# T03 — ColdBlockSealer — basic sealing
# ─────────────────────────────────────────────────────────────────────────────

class TestColdBlockSealer:
    def test_seal_returns_success(self, tmp_path):
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        arts    = _make_artifacts(5)
        result  = sealer.seal(arts)
        assert result.success
        assert result.block is not None

    def test_seal_creates_json_file(self, tmp_path):
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        arts    = _make_artifacts(3)
        result  = sealer.seal(arts)
        assert result.block_file is not None
        assert Path(result.block_file).exists()

    def test_sealed_block_has_correct_artifact_count(self, tmp_path):
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        arts    = _make_artifacts(7)
        result  = sealer.seal(arts)
        assert result.block.artifact_count == 7

    def test_sealed_block_id_format(self, tmp_path):
        import re
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        result  = sealer.seal(_make_artifacts(2))
        assert re.match(r"^OMNIX-BLOCK-\d{8}-\d{6}$", result.block.block_id)

    def test_sealed_block_json_is_parseable(self, tmp_path):
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        result = sealer.seal(_make_artifacts(3))
        with open(result.block_file) as f:
            data = json.load(f)
        assert data["block_id"] == result.block.block_id

    def test_merkle_root_in_block(self, tmp_path):
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        arts    = _make_artifacts(4)
        result  = sealer.seal(arts)
        stored_merkle = result.block.integrity_manifest["merkle_root"]
        hashes  = [a["content_hash"] for a in arts]
        assert stored_merkle == compute_merkle_root(hashes)

    def test_canonical_hash_matches_recompute(self, tmp_path):
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        arts    = _make_artifacts(4)
        result  = sealer.seal(arts)
        b = result.block
        recomputed = compute_canonical_hash(
            block_id=b.block_id,
            creation_timestamp_ns=b.creation_timestamp_ns,
            artifact_count=b.artifact_count,
            evidence_classes=b.evidence_classes,
            merkle_root=b.integrity_manifest["merkle_root"],
            predecessor_block_hash=b.predecessor_block_hash,
        )
        assert recomputed == b.canonical_hash

    def test_seal_produces_custody_entries(self, tmp_path):
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        arts    = _make_artifacts(5)
        result  = sealer.seal(arts)
        assert len(result.custody_entries) == 5

    def test_custody_entries_have_block_id(self, tmp_path):
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        arts    = _make_artifacts(3)
        result  = sealer.seal(arts)
        for entry in result.custody_entries:
            assert entry.block_id == result.block.block_id

    def test_custody_entries_have_transition(self, tmp_path):
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        result  = sealer.seal(_make_artifacts(2), trigger="scheduler")
        for entry in result.custody_entries:
            assert entry.transition == "WARM->COLD"

    def test_genesis_predecessor_when_no_predecessor(self, tmp_path):
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        result  = sealer.seal(_make_artifacts(2))
        assert result.block.predecessor_block_hash == GENESIS_PREDECESSOR

    def test_predecessor_hash_used_when_provided(self, tmp_path):
        sealer   = ColdBlockSealer(output_dir=str(tmp_path))
        pred_block = _make_block_dict()
        result   = sealer.seal(_make_artifacts(2), predecessor_block=pred_block)
        assert result.block.predecessor_block_hash == pred_block["canonical_hash"]

    def test_seal_with_no_content_hash_fails(self, tmp_path):
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        bad_art = {"artifact_id": "X", "evidence_class": "LEGAL"}
        result  = sealer.seal([bad_art])
        assert not result.success
        assert any("EAP-INV-001" in e for e in result.errors)

    def test_empty_block_succeeds_with_warning(self, tmp_path):
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        result  = sealer.seal([])
        assert result.success
        assert result.block.artifact_count == 0
        assert any("empty" in w.lower() for w in result.warnings)

    def test_omnix_version_in_block(self, tmp_path):
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        result  = sealer.seal(_make_artifacts(2))
        assert result.block.omnix_version == OMNIX_VERSION

    def test_seal_trigger_recorded(self, tmp_path):
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        result  = sealer.seal(_make_artifacts(2), trigger="admin")
        assert result.block.seal_trigger == "admin"

    def test_seal_duration_positive(self, tmp_path):
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        result  = sealer.seal(_make_artifacts(2))
        assert result.seal_duration_ms >= 0

    def test_multiple_seals_get_sequential_ids(self, tmp_path):
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        r1 = sealer.seal(_make_artifacts(2))
        r2 = sealer.seal(_make_artifacts(2))
        assert r1.block.block_id != r2.block.block_id

    def test_evidence_classes_sorted_in_block(self, tmp_path):
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        arts    = (
            _make_artifacts(2, "TELEMETRY")
            + _make_artifacts(2, "LEGAL")
            + _make_artifacts(2, "PQC")
        )
        result  = sealer.seal(arts)
        classes = result.block.evidence_classes
        assert classes == sorted(classes)

    def test_artifact_hashes_stored_in_manifest(self, tmp_path):
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        arts    = _make_artifacts(5)
        result  = sealer.seal(arts)
        hashes  = result.block.integrity_manifest["artifact_hashes"]
        expected = [a["content_hash"] for a in arts]
        assert set(hashes) == set(expected)

    def test_hash_algorithm_is_v1(self, tmp_path):
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        result  = sealer.seal(_make_artifacts(2))
        assert result.block.integrity_manifest["hash_algorithm"] == HASH_ALGORITHM_V1


# ─────────────────────────────────────────────────────────────────────────────
# T04 — Chain sealing (predecessor linkage)
# ─────────────────────────────────────────────────────────────────────────────

class TestChainSealing:
    def test_chain_of_three_blocks(self, tmp_path):
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        r1 = sealer.seal(_make_artifacts(3))
        r2 = sealer.seal(_make_artifacts(3), predecessor_block=r1.block.to_dict())
        r3 = sealer.seal(_make_artifacts(3), predecessor_block=r2.block.to_dict())

        assert r2.block.predecessor_block_hash == r1.block.canonical_hash
        assert r3.block.predecessor_block_hash == r2.block.canonical_hash

    def test_chain_links_are_canonical_hashes(self, tmp_path):
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        r1 = sealer.seal(_make_artifacts(2))
        r2 = sealer.seal(_make_artifacts(2), predecessor_block=r1.block.to_dict())
        assert r2.block.predecessor_block_hash == r1.block.canonical_hash

    def test_missing_canonical_in_predecessor_fails(self, tmp_path):
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        bad_pred = {"block_id": "OMNIX-BLOCK-20260515-000001"}
        result   = sealer.seal(_make_artifacts(2), predecessor_block=bad_pred)
        assert not result.success
        assert any("EAP-INV-003" in e for e in result.errors)


# ─────────────────────────────────────────────────────────────────────────────
# T05 — Emergency seal (halt_event / RGC-INV-003)
# ─────────────────────────────────────────────────────────────────────────────

class TestEmergencySeal:
    def test_emergency_seal_only_immutable_classes(self, tmp_path):
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        arts   = (
            _make_artifacts(3, "LEGAL")
            + _make_artifacts(3, "TELEMETRY")
            + _make_artifacts(2, "EXCEPTION")
        )
        result = sealer.seal_emergency(arts, chain_root_id="ATFDR-ROOT-001")
        assert result.success
        # Only LEGAL and EXCEPTION should be in the block
        assert result.block.artifact_count == 5

    def test_emergency_seal_trigger_is_halt_event(self, tmp_path):
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        arts   = _make_artifacts(3, "EXCEPTION")
        result = sealer.seal_emergency(arts, chain_root_id="ATFDR-ROOT-002")
        assert result.block.seal_trigger == "halt_event"

    def test_emergency_seal_custody_transition(self, tmp_path):
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        arts   = _make_artifacts(3, "LEGAL")
        result = sealer.seal_emergency(arts, chain_root_id="ATFDR-ROOT-003")
        for entry in result.custody_entries:
            assert entry.transition == "EMERGENCY_COLD"

    def test_emergency_seal_no_immutable_arts_fails(self, tmp_path):
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        arts   = _make_artifacts(5, "TELEMETRY")
        result = sealer.seal_emergency(arts, chain_root_id="ATFDR-ROOT-004")
        assert not result.success
        assert any("IMMUTABLE" in e for e in result.errors)


# ─────────────────────────────────────────────────────────────────────────────
# T06 — verify_archive_block() — PASS cases
# ─────────────────────────────────────────────────────────────────────────────

class TestVerifyArchiveBlockPass:
    def test_valid_block_passes(self):
        block  = _make_block_dict()
        result = verifier.verify_archive_block(block)
        assert result.verdict == "PASS"

    def test_valid_block_merkle_valid(self):
        block  = _make_block_dict()
        result = verifier.verify_archive_block(block)
        assert result.merkle_valid

    def test_valid_block_canonical_hash_valid(self):
        block  = _make_block_dict()
        result = verifier.verify_archive_block(block)
        assert result.canonical_hash_valid

    def test_valid_block_no_failure_reasons(self):
        block  = _make_block_dict()
        result = verifier.verify_archive_block(block)
        assert result.failure_reasons == []

    def test_valid_genesis_block_passes(self):
        block  = _make_block_dict(predecessor_hash=GENESIS_PREDECESSOR)
        result = verifier.verify_archive_block(block)
        assert result.verdict == "PASS"
        assert result.predecessor_hash_valid

    def test_valid_block_artifact_count_matches(self):
        arts   = _make_artifacts(8)
        block  = _make_block_dict(artifacts=arts)
        result = verifier.verify_archive_block(block)
        assert result.artifact_hashes_valid
        assert result.artifact_hashes_count == 8

    def test_block_with_predecessor_passes(self):
        pred   = _make_block_dict(block_id="OMNIX-BLOCK-20260515-000001")
        block  = _make_block_dict(
            block_id="OMNIX-BLOCK-20260515-000002",
            predecessor_hash=pred["canonical_hash"],
        )
        result = verifier.verify_archive_block(block, predecessor_block=pred)
        assert result.verdict == "PASS"
        assert result.predecessor_hash_valid
        assert result.chain_verified

    def test_sealed_block_passes_verification(self, tmp_path):
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        r      = sealer.seal(_make_artifacts(6))
        result = verifier.verify_archive_block(r.block.to_dict())
        assert result.verdict == "PASS"

    def test_sealed_chain_all_pass(self, tmp_path):
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        r1 = sealer.seal(_make_artifacts(3))
        r2 = sealer.seal(_make_artifacts(3), predecessor_block=r1.block.to_dict())
        r3 = sealer.seal(_make_artifacts(3), predecessor_block=r2.block.to_dict())

        d1 = r1.block.to_dict()
        d2 = r2.block.to_dict()
        d3 = r3.block.to_dict()

        assert verifier.verify_archive_block(d1).verdict == "PASS"
        assert verifier.verify_archive_block(d2, predecessor_block=d1).verdict == "PASS"
        assert verifier.verify_archive_block(d3, predecessor_block=d2).verdict == "PASS"

    def test_empty_block_passes(self, tmp_path):
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        r      = sealer.seal([])
        result = verifier.verify_archive_block(r.block.to_dict())
        assert result.verdict == "PASS"

    def test_block_without_pqc_signature_passes_hash_checks(self):
        block  = _make_block_dict(pqc_signature=None)
        result = verifier.verify_archive_block(block)
        assert result.merkle_valid
        assert result.canonical_hash_valid
        assert not result.pqc_checked
        assert result.verdict == "PASS"


# ─────────────────────────────────────────────────────────────────────────────
# T07 — verify_archive_block() — tamper detection
# ─────────────────────────────────────────────────────────────────────────────

class TestVerifyArchiveBlockTamper:
    def test_tampered_artifact_hash_fails_merkle(self):
        block = _make_block_dict()
        block["integrity_manifest"]["artifact_hashes"][0] = "tampered" * 8
        result = verifier.verify_archive_block(block)
        assert not result.merkle_valid
        assert any("EAP-INV-001" in r for r in result.failure_reasons)

    def test_tampered_block_id_fails_canonical(self):
        block = _make_block_dict()
        block["block_id"] = "OMNIX-BLOCK-20260101-999999"
        result = verifier.verify_archive_block(block)
        assert not result.canonical_hash_valid
        assert any("EAP-INV-001" in r for r in result.failure_reasons)

    def test_tampered_merkle_root_fails_canonical(self):
        block = _make_block_dict()
        block["integrity_manifest"]["merkle_root"] = "sha256:tampered"
        result = verifier.verify_archive_block(block)
        assert not result.canonical_hash_valid or not result.merkle_valid
        assert result.verdict == "INTEGRITY_VIOLATION"

    def test_tampered_artifact_count_fails(self):
        block = _make_block_dict(_make_artifacts(5))
        block["artifact_count"] = 99
        result = verifier.verify_archive_block(block)
        assert not result.canonical_hash_valid or not result.artifact_hashes_valid
        assert result.verdict in {"INTEGRITY_VIOLATION", "CHAIN_BREAK", "SIGNATURE_INVALID"}

    def test_tampered_predecessor_fails_chain(self):
        pred  = _make_block_dict(block_id="OMNIX-BLOCK-20260515-000001")
        block = _make_block_dict(
            block_id="OMNIX-BLOCK-20260515-000002",
            predecessor_hash=pred["canonical_hash"],
        )
        pred["canonical_hash"] = "sha256:tampered"
        result = verifier.verify_archive_block(block, predecessor_block=pred)
        assert not result.predecessor_hash_valid
        assert "EAP-INV-003" in "\n".join(result.failure_reasons)

    def test_removed_artifact_hash_fails(self):
        arts  = _make_artifacts(5)
        block = _make_block_dict(arts)
        block["integrity_manifest"]["artifact_hashes"].pop()
        result = verifier.verify_archive_block(block)
        assert not result.merkle_valid or not result.artifact_hashes_valid

    def test_extra_artifact_hash_fails(self):
        arts  = _make_artifacts(3)
        block = _make_block_dict(arts)
        block["integrity_manifest"]["artifact_hashes"].append("sha256:" + "x" * 64)
        result = verifier.verify_archive_block(block)
        assert not result.merkle_valid

    def test_changed_omnix_version_fails_canonical(self):
        block = _make_block_dict()
        block["omnix_version"] = "9.9.9"
        result = verifier.verify_archive_block(block)
        assert not result.canonical_hash_valid

    def test_changed_evidence_classes_fails_canonical(self):
        block = _make_block_dict()
        block["evidence_classes"] = ["SAMPLE", "TELEMETRY"]
        result = verifier.verify_archive_block(block)
        assert not result.canonical_hash_valid


# ─────────────────────────────────────────────────────────────────────────────
# T08 — verify_archive_block() — chain verdict codes
# ─────────────────────────────────────────────────────────────────────────────

class TestVerifyArchiveBlockVerdicts:
    def test_clean_block_is_pass(self):
        block  = _make_block_dict()
        result = verifier.verify_archive_block(block)
        assert result.verdict == verifier.VERDICT_PASS

    def test_tampered_hash_is_integrity_violation(self):
        block = _make_block_dict()
        block["integrity_manifest"]["artifact_hashes"] = ["tamperedhash" * 5]
        result = verifier.verify_archive_block(block)
        assert result.verdict == verifier.VERDICT_INTEGRITY_VIOLATION

    def test_broken_chain_is_chain_break(self):
        pred  = _make_block_dict(block_id="OMNIX-BLOCK-20260515-000001")
        block = _make_block_dict(
            block_id="OMNIX-BLOCK-20260515-000002",
            predecessor_hash=pred["canonical_hash"],
        )
        pred["canonical_hash"] = "sha256:" + "0" * 64
        result = verifier.verify_archive_block(block, predecessor_block=pred)
        assert result.verdict in {
            verifier.VERDICT_CHAIN_BREAK,
            verifier.VERDICT_INTEGRITY_VIOLATION,
        }

    def test_result_has_block_id(self):
        block  = _make_block_dict()
        result = verifier.verify_archive_block(block)
        assert result.block_id == block["block_id"]

    def test_result_has_artifact_count(self):
        arts   = _make_artifacts(9)
        block  = _make_block_dict(arts)
        result = verifier.verify_archive_block(block)
        assert result.artifact_count == 9

    def test_result_has_evidence_classes(self):
        arts   = (
            _make_artifacts(3, "LEGAL")
            + _make_artifacts(3, "PQC")
        )
        block  = _make_block_dict(arts)
        result = verifier.verify_archive_block(block)
        assert "LEGAL" in result.evidence_classes
        assert "PQC" in result.evidence_classes


# ─────────────────────────────────────────────────────────────────────────────
# T09 — verify_archive_block() — JSON output round-trip
# ─────────────────────────────────────────────────────────────────────────────

class TestVerifyBlockJsonOutput:
    def test_sealed_block_json_round_trip(self, tmp_path):
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        r      = sealer.seal(_make_artifacts(5))

        with open(r.block_file) as f:
            loaded = json.load(f)

        result = verifier.verify_archive_block(loaded)
        assert result.verdict == "PASS"

    def test_block_dict_round_trip_through_json(self):
        block        = _make_block_dict(_make_artifacts(4))
        round_tripped = json.loads(json.dumps(block))
        result       = verifier.verify_archive_block(round_tripped)
        assert result.verdict == "PASS"

    def test_sealed_block_to_dict_round_trip(self, tmp_path):
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        r      = sealer.seal(_make_artifacts(3))
        result = verifier.verify_archive_block(r.block.to_dict())
        assert result.verdict == "PASS"


# ─────────────────────────────────────────────────────────────────────────────
# T10 — Public key loading (_load_public_key_b64)
# ─────────────────────────────────────────────────────────────────────────────

class TestPublicKeyLoading:
    def test_b64_file_loaded(self, tmp_path):
        key_content = base64.b64encode(b"demo-public-key-bytes").decode()
        key_file    = tmp_path / "omnix_demo_public_key.b64"
        key_file.write_text(key_content)
        loaded = verifier._load_public_key_b64(str(key_file))
        assert loaded == key_content

    def test_raw_b64_string_passed_through(self):
        key = base64.b64encode(b"demo-public-key-bytes").decode()
        assert verifier._load_public_key_b64(key) == key

    def test_pem_file_strips_headers(self, tmp_path):
        pem_content = (
            "-----BEGIN PUBLIC KEY-----\n"
            "YWJjZGVmZ2hpamtsbW5vcA==\n"
            "-----END PUBLIC KEY-----\n"
        )
        pem_file = tmp_path / "key.pem"
        pem_file.write_text(pem_content)
        loaded = verifier._load_public_key_b64(str(pem_file))
        assert "BEGIN" not in loaded
        assert "END" not in loaded


# ─────────────────────────────────────────────────────────────────────────────
# T11 — Warm manifest entries (EAP-INV-001 / EAP-INV-006)
# ─────────────────────────────────────────────────────────────────────────────

class TestWarmManifestEntry:
    def test_warm_manifest_requires_content_hash(self):
        artifact = {"artifact_id": "X", "evidence_class": "TELEMETRY"}
        with pytest.raises(ValueError, match="EAP-INV-001"):
            create_warm_manifest_entry(artifact, "aggregate_hourly")

    def test_warm_manifest_preserves_original_hash(self):
        art     = _make_artifact("TELEMETRY")
        entry   = create_warm_manifest_entry(art, "strip_nominal")
        assert entry["original_hash"] == art["content_hash"]

    def test_warm_manifest_has_manifest_id(self):
        art   = _make_artifact("TELEMETRY")
        entry = create_warm_manifest_entry(art, "aggregate_hourly")
        assert entry["manifest_id"].startswith("MAN-")

    def test_warm_manifest_compression_method_recorded(self):
        art   = _make_artifact("SAMPLE")
        entry = create_warm_manifest_entry(art, "strip_nominal")
        assert entry["compression_method"] == "strip_nominal"

    def test_warm_manifest_no_compression(self):
        art   = _make_artifact("LEGAL")
        entry = create_warm_manifest_entry(art, "none")
        assert entry["original_hash"] == entry["compressed_hash"]


# ─────────────────────────────────────────────────────────────────────────────
# T12 — Shadow event classification (ADR-162 §4)
# ─────────────────────────────────────────────────────────────────────────────

class TestShadowEventClassification:
    def test_veto_trigger_is_exception(self):
        event = {"trigger": "veto", "risk_score": 0.5}
        assert classify_shadow_event(event) == "EXCEPTION"

    def test_anomaly_trigger_is_exception(self):
        event = {"trigger": "anomaly", "risk_score": 0.3}
        assert classify_shadow_event(event) == "EXCEPTION"

    def test_critical_risk_is_exception(self):
        event = {"trigger": "nominal", "risk_score": 0.98}
        assert classify_shadow_event(event) == "EXCEPTION"

    def test_low_risk_nominal_is_shadow_nominal(self):
        event = {"trigger": "nominal", "risk_score": 0.20}
        assert classify_shadow_event(event) == "SHADOW_NOMINAL"

    def test_reduce_shadow_nominal_strips_payload(self):
        event = {
            "event_id":   "E001",
            "timestamp_ns": 123456,
            "event_type": "TRADE",
            "agent_id":   "AID-TEST",
            "content_hash": "abc",
            "risk_score": 0.1,
            "trigger":    "nominal",
            "extra_field": "should_be_removed",
            "large_payload": {"lots": "of", "data": "here"},
        }
        reduced = reduce_shadow_event(event)
        assert "extra_field" not in reduced
        assert "large_payload" not in reduced
        assert "event_id" in reduced
        assert "content_hash" in reduced

    def test_reduce_exception_preserves_all(self):
        event = {
            "event_id": "E002",
            "trigger":  "veto",
            "risk_score": 0.5,
            "full_payload": {"important": "data"},
            "veto_reason":  "risk_limit_exceeded",
        }
        reduced = reduce_shadow_event(event)
        assert "full_payload" in reduced
        assert "veto_reason" in reduced


# ─────────────────────────────────────────────────────────────────────────────
# T13 — EAP invariant enforcement (protocol-level)
# ─────────────────────────────────────────────────────────────────────────────

class TestEAPInvariants:
    """
    Protocol-level enforcement of EAP-INV-001–006.
    These tests verify the mechanical invariants, not just the data structure.
    """

    def test_eap_inv_001_artifact_missing_content_hash_blocked(self, tmp_path):
        """EAP-INV-001: Artifacts without content_hash cannot be sealed."""
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        result = sealer.seal([{"artifact_id": "X", "evidence_class": "LEGAL"}])
        assert not result.success

    def test_eap_inv_001_content_hash_present_in_manifest(self, tmp_path):
        """EAP-INV-001: Every artifact's content_hash is in the manifest."""
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        arts   = _make_artifacts(4)
        result = sealer.seal(arts)
        manifest_hashes = set(result.block.integrity_manifest["artifact_hashes"])
        for art in arts:
            assert art["content_hash"] in manifest_hashes

    def test_eap_inv_002_unsigned_block_warns(self, tmp_path):
        """EAP-INV-002: Block without PQC key generates warning, not error."""
        sealer = ColdBlockSealer(output_dir=str(tmp_path), secret_key_b64="")
        result = sealer.seal(_make_artifacts(2))
        assert result.success
        assert any("PQC" in w or "signing" in w.lower() for w in result.warnings)

    def test_eap_inv_003_missing_canonical_in_predecessor_blocked(self, tmp_path):
        """EAP-INV-003: Predecessor without canonical_hash is rejected."""
        sealer   = ColdBlockSealer(output_dir=str(tmp_path))
        bad_pred = {"block_id": "OMNIX-BLOCK-20260101-000001"}
        result   = sealer.seal(_make_artifacts(2), predecessor_block=bad_pred)
        assert not result.success

    def test_eap_inv_003_chain_continuity_verified_at_seal(self, tmp_path):
        """EAP-INV-003: Second block's predecessor_hash links to first block."""
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        r1 = sealer.seal(_make_artifacts(3))
        r2 = sealer.seal(_make_artifacts(3), predecessor_block=r1.block.to_dict())
        assert r2.block.predecessor_block_hash == r1.block.canonical_hash

    def test_eap_inv_004_legal_artifacts_included_fully(self, tmp_path):
        """EAP-INV-004: LEGAL class artifacts are sealed completely."""
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        legal   = _make_artifacts(3, "LEGAL")
        result  = sealer.seal(legal)
        assert result.success
        assert result.block.artifact_count == 3

    def test_eap_inv_005_block_verifiable_offline(self, tmp_path):
        """EAP-INV-005: Sealed block passes offline verification (no runtime)."""
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        r      = sealer.seal(_make_artifacts(5))
        result = verifier.verify_archive_block(r.block.to_dict())
        assert result.verdict == "PASS"

    def test_eap_inv_005_chain_verifiable_offline(self, tmp_path):
        """EAP-INV-005: Chain of blocks is verifiable without platform access."""
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        r1 = sealer.seal(_make_artifacts(3))
        r2 = sealer.seal(_make_artifacts(3), predecessor_block=r1.block.to_dict())
        res2 = verifier.verify_archive_block(
            r2.block.to_dict(),
            predecessor_block=r1.block.to_dict(),
        )
        assert res2.verdict == "PASS"
        assert res2.chain_verified

    def test_eap_inv_006_custody_entry_per_artifact(self, tmp_path):
        """EAP-INV-006: Every sealed artifact gets a custody log entry."""
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        n      = 12
        result = sealer.seal(_make_artifacts(n))
        assert len(result.custody_entries) == n

    def test_eap_inv_006_custody_ids_unique(self, tmp_path):
        """EAP-INV-006: Custody IDs must be globally unique."""
        sealer  = ColdBlockSealer(output_dir=str(tmp_path))
        result  = sealer.seal(_make_artifacts(10))
        ids     = [e.custody_id for e in result.custody_entries]
        assert len(ids) == len(set(ids))


# ─────────────────────────────────────────────────────────────────────────────
# T14 — SealedBlock dataclass and serialization
# ─────────────────────────────────────────────────────────────────────────────

class TestSealedBlockDataclass:
    def test_to_dict_has_all_required_fields(self, tmp_path):
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        r      = sealer.seal(_make_artifacts(3))
        d      = r.block.to_dict()
        required = [
            "block_id", "creation_timestamp_ns", "artifact_count",
            "evidence_classes", "canonical_hash", "predecessor_block_hash",
            "integrity_manifest", "pqc_algorithm", "omnix_version",
            "sealed_at", "sealed_by", "seal_trigger", "artifact_ids",
        ]
        for field in required:
            assert field in d, f"Missing required field: {field}"

    def test_block_file_name_property(self, tmp_path):
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        r      = sealer.seal(_make_artifacts(2))
        assert r.block.block_file_name.endswith(".json")
        assert r.block.block_id in r.block.block_file_name

    def test_is_pqc_signed_false_without_key(self, tmp_path):
        # Mock _sign_with_dilithium to return None (simulates no PQC key configured)
        import omnix_core.evidence.cold_block_sealer as sealer_module
        with patch.object(sealer_module, "_sign_with_dilithium", return_value=None):
            with patch.dict(os.environ, {"OMNIX_SIGNING_SECRET_KEY_B64": ""}, clear=False):
                sealer = ColdBlockSealer(output_dir=str(tmp_path), secret_key_b64="")
                r      = sealer.seal(_make_artifacts(2))
        assert not r.block.is_pqc_signed

    def test_to_json_is_valid_json(self, tmp_path):
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        r      = sealer.seal(_make_artifacts(2))
        parsed = json.loads(r.block.to_json())
        assert parsed["block_id"] == r.block.block_id

    def test_custody_entry_to_dict_serializable(self, tmp_path):
        sealer = ColdBlockSealer(output_dir=str(tmp_path))
        r      = sealer.seal(_make_artifacts(2))
        for entry in r.custody_entries:
            d = entry.to_dict()
            json.dumps(d)  # Must not raise


# ─────────────────────────────────────────────────────────────────────────────
# T15 — Verifier GENESIS_PREDECESSOR handling
# ─────────────────────────────────────────────────────────────────────────────

class TestGenesisBlock:
    def test_genesis_sentinel_is_64_zeros(self):
        assert GENESIS_PREDECESSOR == "0" * 64
        assert len(GENESIS_PREDECESSOR) == 64

    def test_genesis_block_passes_chain_check(self):
        block  = _make_block_dict(predecessor_hash=GENESIS_PREDECESSOR)
        result = verifier.verify_archive_block(block)
        assert result.predecessor_hash_valid
        assert result.chain_verified

    def test_non_genesis_without_predecessor_warns(self):
        non_genesis_pred = "sha256:" + "a" * 64
        block  = _make_block_dict(predecessor_hash=non_genesis_pred)
        result = verifier.verify_archive_block(block)
        assert any("predecessor" in w.lower() or "genesis" in w.lower()
                   for w in result.warnings)

    def test_verifier_genesis_constant_matches_sealer(self):
        assert verifier.GENESIS_PREDECESSOR == GENESIS_PREDECESSOR


# ─────────────────────────────────────────────────────────────────────────────
# T16 — Verifier protocol constants
# ─────────────────────────────────────────────────────────────────────────────

class TestVerifierConstants:
    def test_verdict_constants_defined(self):
        assert verifier.VERDICT_PASS                == "PASS"
        assert verifier.VERDICT_INTEGRITY_VIOLATION == "INTEGRITY_VIOLATION"
        assert verifier.VERDICT_CHAIN_BREAK         == "CHAIN_BREAK"
        assert verifier.VERDICT_SIGNATURE_INVALID   == "SIGNATURE_INVALID"

    def test_verifier_version_is_1_1_0(self):
        assert verifier.VERIFIER_VERSION == "1.1.0"

    def test_hash_algorithm_v1_constant(self):
        assert HASH_ALGORITHM_V1 == "sha256-v1"

    def test_immutable_classes_set(self):
        assert "LEGAL"     in IMMUTABLE_CLASSES
        assert "PQC"       in IMMUTABLE_CLASSES
        assert "CONTRACT"  in IMMUTABLE_CLASSES
        assert "EXCEPTION" in IMMUTABLE_CLASSES
        assert "TELEMETRY" not in IMMUTABLE_CLASSES
