"""
OMNIX Immutable Evidence Archive Pipeline — COLD Block Sealer
=============================================================
ADR-163: Immutable Evidence Archive Pipeline
EAP-INV-001–006 enforcement at block-seal time.

Responsibilities:
  · Collect artifacts from HOT/WARM tier
  · Compute artifact Merkle root
  · Compute block canonical_hash (deterministic, field-committed)
  · Sign canonical_hash with ML-DSA-65 (Dilithium-3)
  · Write COLD block as JSON manifest (+ optional Parquet)
  · Write custody log entries for every sealed artifact
  · Validate chain continuity before sealing (EAP-INV-003)
  · Support HALT-triggered emergency sealing (RGC-INV-003)

This module is the mechanical implementation of the ADR-162 retention policy.
ADR-163 defines the pipeline; ADR-162 defines what goes into it.

Sealing is an APPEND-ONLY operation. Blocks are never modified after seal.
The public verifier (omnix_atf_verify.py) can reconstruct and verify any
sealed block offline, without platform access (EAP-INV-005).

Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("OMNIX.ColdBlockSealer")

# ─────────────────────────────────────────────────────────────────────────────
# Protocol constants (canonical — must match omnix_atf_verify.py)
# ─────────────────────────────────────────────────────────────────────────────

OMNIX_VERSION      = "1.0.0"
HASH_ALGORITHM_V1  = "sha256-v1"
PQC_ALGORITHM      = "ML-DSA-65 (FIPS 204)"
GENESIS_PREDECESSOR = "0" * 64

IMMUTABLE_CLASSES  = frozenset({"LEGAL", "PQC", "CONTRACT", "EXCEPTION"})
ALL_EVIDENCE_CLASSES = frozenset({
    "LEGAL", "PQC", "CONTRACT", "EXCEPTION",
    "TELEMETRY", "SAMPLE", "SHADOW_NOMINAL", "OPS",
})

# Block ID format: OMNIX-BLOCK-{YYYYMMDD}-{seq:06d}
BLOCK_ID_TEMPLATE = "OMNIX-BLOCK-{date}-{seq:06d}"

# ─────────────────────────────────────────────────────────────────────────────
# Cryptographic primitives (mirrors omnix_atf_verify.py exactly)
# ─────────────────────────────────────────────────────────────────────────────

def _canonical_json(obj: Dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_prefixed(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def compute_merkle_root(artifact_hashes: List[str]) -> str:
    """
    Compute deterministic Merkle root from a list of artifact content hashes.

    Algorithm: sha256("|".join(sorted(hashes)))
    Hashes are sorted to ensure determinism regardless of insertion order.
    Returns a 'sha256:' prefixed hex string.
    """
    if not artifact_hashes:
        return _sha256_prefixed(b"OMNIX-EMPTY-BLOCK")
    combined = "|".join(sorted(artifact_hashes))
    return _sha256_prefixed(combined.encode("utf-8"))


def compute_canonical_hash(
    block_id: str,
    creation_timestamp_ns: int,
    artifact_count: int,
    evidence_classes: List[str],
    merkle_root: str,
    predecessor_block_hash: str,
    omnix_version: str = OMNIX_VERSION,
    hash_algorithm: str = HASH_ALGORITHM_V1,
) -> str:
    """
    Compute the canonical hash of a COLD archive block.

    This hash commits to all identifying block fields. It is what the
    ML-DSA-65 signature covers. The verifier uses this exact function
    to reconstruct and check the hash offline (EAP-INV-005).

    Committed fields (sorted canonical JSON → SHA-256 → 'sha256:' prefix):
      block_id, creation_timestamp_ns, artifact_count,
      evidence_classes (sorted list), hash_algorithm,
      merkle_root, omnix_version, predecessor_block_hash
    """
    committed = {
        "block_id":              block_id,
        "creation_timestamp_ns": creation_timestamp_ns,
        "artifact_count":        artifact_count,
        "evidence_classes":      sorted(evidence_classes),
        "hash_algorithm":        hash_algorithm,
        "merkle_root":           merkle_root,
        "omnix_version":         omnix_version,
        "predecessor_block_hash": predecessor_block_hash,
    }
    return _sha256_prefixed(_canonical_json(committed))


def _sign_with_dilithium(message: str, secret_key_b64: str) -> Optional[str]:
    """
    Sign a message (canonical_hash) with ML-DSA-65 (Dilithium-3).

    Args:
        message:        The canonical_hash string (will be UTF-8 encoded).
        secret_key_b64: Base64-encoded Dilithium-3 secret key.

    Returns:
        Base64-encoded signature string, or None if PQC library unavailable.
    """
    try:
        from pqc.sign import dilithium3 as dil
        sk  = base64.b64decode(secret_key_b64)
        sig = dil.sign(message.encode("utf-8"), sk)
        return base64.b64encode(sig).decode("utf-8")
    except ImportError:
        pass
    except Exception:
        return None

    try:
        from omnix_core.security.crypto_providers import get_active_provider
        provider = get_active_provider()
        sk  = base64.b64decode(secret_key_b64)
        sig = provider.sign(message.encode("utf-8"), sk)
        return base64.b64encode(sig).decode("utf-8")
    except Exception:
        pass

    logger.warning("PQC library unavailable — block will be sealed without ML-DSA-65 signature")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Block and manifest data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SealedBlock:
    """
    A fully sealed COLD archive block (ADR-163 §1 Stage 3).

    This is the canonical block format as defined in ADR-163.
    The verifier (omnix_atf_verify.py --archive-block) expects
    this exact structure.
    """
    block_id:               str
    creation_timestamp_ns:  int
    artifact_count:         int
    evidence_classes:       List[str]
    canonical_hash:         str
    predecessor_block_hash: str
    integrity_manifest:     Dict[str, Any]
    pqc_signature:          Optional[str]
    pqc_algorithm:          str
    omnix_version:          str

    # Sealer metadata (not part of canonical hash — audit only)
    sealed_at:              str
    sealed_by:              str
    seal_trigger:           str   # 'scheduler' | 'halt_event' | 'admin'
    artifact_ids:           List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @property
    def block_file_name(self) -> str:
        return f"{self.block_id}.json"

    @property
    def is_pqc_signed(self) -> bool:
        return self.pqc_signature is not None


@dataclass
class CustodyLogEntry:
    """
    Evidence custody log entry (ADR-163 §5).

    Every HOT→WARM and WARM→COLD transition creates one of these.
    The custody_log table is itself classified as LEGAL evidence
    and can never be deleted or modified.
    """
    custody_id:          str
    artifact_id:         str
    evidence_class:      str
    transition:          str          # 'HOT->WARM' | 'WARM->COLD' | 'EMERGENCY_COLD'
    from_hash:           str
    to_hash:             str
    block_id:            Optional[str]
    triggered_by:        str          # 'scheduler' | 'halt_event' | 'admin'
    transition_ns:       int
    integrity_verified:  bool
    verified_at:         Optional[str]
    notes:               Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SealResult:
    """Result of a block seal operation."""
    success:          bool
    block:            Optional[SealedBlock]
    custody_entries:  List[CustodyLogEntry]
    block_file:       Optional[str]
    errors:           List[str]
    warnings:         List[str]
    seal_duration_ms: float


# ─────────────────────────────────────────────────────────────────────────────
# Block ID registry (in-process sequence counter)
# ─────────────────────────────────────────────────────────────────────────────

# ── P0-003 / ADR-167: Distributed block ID sequence ─────────────────────────
# In-process counters reset on restart and are not shared across processes or
# Railway dynos. Two concurrent processes sealing on the same date would both
# generate OMNIX-BLOCK-YYYYMMDD-000001, creating a block ID collision that makes
# the chain irrecoverably ambiguous for forensic reconstruction.
#
# Resolution: Use Redis INCR on a per-date key (atomic, cross-process, cross-dyno).
# Redis INCR is guaranteed to be atomic even under concurrent writers — this is
# exactly the use case Redis was designed for.
#
# Fallback strategy: if Redis is unavailable (local dev, testing), fall back to
# a process-local counter with a WARNING. The fallback is ONLY acceptable in
# non-production environments. Production MUST have REDIS_URL set.
#
# Key schema: omnix:block_seq:{date_str}  (e.g. omnix:block_seq:20260515)
# TTL: 30 days (blocks are daily — the key is no longer needed after the day)
# ─────────────────────────────────────────────────────────────────────────────

_block_sequence_cache: Dict[str, int] = {}  # fallback: local dev / test only
_redis_client: Optional[Any] = None         # lazy-initialized


def _get_redis_client() -> Optional[Any]:
    """Lazy-initialize a Redis client from REDIS_URL. Returns None if unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    redis_url = os.environ.get("REDIS_URL")
    if not redis_url:
        return None
    try:
        import redis as _redis_lib
        _redis_client = _redis_lib.from_url(redis_url, decode_responses=True, socket_timeout=2.0)
        _redis_client.ping()
        return _redis_client
    except Exception as _e:
        logger.warning("Redis unavailable for block ID sequencing: %s", _e)
        return None


def _next_block_id(date_str: Optional[str] = None) -> str:
    """
    Generate the next deterministic block ID for today's date.

    Sequence source (in priority order):
      1. Redis INCR on key 'omnix:block_seq:{date_str}' — atomic, distributed,
         collision-free across all processes and Railway dynos.
      2. In-process counter — fallback for local dev and testing ONLY.
         WARNING: Not safe for multi-process/multi-dyno deployments.
         Production MUST have REDIS_URL set (P0-003 / ADR-167).
    """
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")

    redis = _get_redis_client()
    if redis is not None:
        try:
            redis_key = f"omnix:block_seq:{date_str}"
            seq = redis.incr(redis_key)
            # 30-day TTL — keeps Redis tidy; key persists well past the sealing date
            redis.expire(redis_key, 30 * 24 * 3600, nx=True)
            return BLOCK_ID_TEMPLATE.format(date=date_str, seq=seq)
        except Exception as _redis_err:
            logger.error(
                "Redis INCR failed for block_seq:%s — falling back to in-process counter. "
                "This may produce duplicate block IDs in multi-process deployments. "
                "Error: %s",
                date_str, _redis_err,
            )

    # ── In-process fallback (dev / test only) ────────────────────────────────
    testing = os.environ.get("TESTING", "").lower() in ("1", "true")
    if not testing and not os.environ.get("REDIS_URL"):
        logger.warning(
            "[BlockID] REDIS_URL not set — using in-process sequence counter. "
            "Block ID uniqueness is NOT guaranteed across multiple processes or dynos. "
            "Set REDIS_URL in production to prevent block ID collisions (P0-003)."
        )
    _block_sequence_cache.setdefault(date_str, 0)
    _block_sequence_cache[date_str] += 1
    seq = _block_sequence_cache[date_str]
    return BLOCK_ID_TEMPLATE.format(date=date_str, seq=seq)


# ─────────────────────────────────────────────────────────────────────────────
# Pre-seal validation
# ─────────────────────────────────────────────────────────────────────────────

def _validate_artifacts_for_seal(
    artifacts: List[Dict[str, Any]],
    trigger: str,
) -> Tuple[List[str], List[str]]:
    """
    Validate artifacts before sealing. Returns (errors, warnings).

    EAP-INV-004: Immutable class artifacts must be in complete canonical form.
    EAP-INV-001: All artifacts must have a content_hash.
    """
    errors: List[str] = []
    warnings: List[str] = []

    for idx, artifact in enumerate(artifacts):
        aid = artifact.get("artifact_id") or artifact.get("id") or f"[{idx}]"

        if "content_hash" not in artifact:
            errors.append(
                f"EAP-INV-001: Artifact {aid} has no content_hash — cannot seal"
            )

        evidence_class = artifact.get("evidence_class", "")
        if not evidence_class:
            warnings.append(f"Artifact {aid} has no evidence_class — treating as UNKNOWN")
        elif evidence_class not in ALL_EVIDENCE_CLASSES:
            warnings.append(f"Artifact {aid} has unrecognised evidence_class: '{evidence_class}'")

        if evidence_class in IMMUTABLE_CLASSES:
            if not artifact.get("pqc_signatures") and not artifact.get("pqc_signature"):
                warnings.append(
                    f"EAP-INV-002 advisory: IMMUTABLE artifact {aid} ({evidence_class})"
                    f" has no PQC signature"
                )

    if not artifacts:
        warnings.append("Sealing an empty block — artifact_count=0")

    return errors, warnings


# ─────────────────────────────────────────────────────────────────────────────
# COLD Block Sealer
# ─────────────────────────────────────────────────────────────────────────────

class ColdBlockSealer:
    """
    Seals COLD archive blocks from a set of evidence artifacts.

    Usage:
        sealer = ColdBlockSealer(
            output_dir="/path/to/cold_archive",
            secret_key_b64=os.environ["OMNIX_SIGNING_SECRET_KEY_B64"],
        )

        # Regular weekly seal
        result = sealer.seal(artifacts, trigger="scheduler")

        # Emergency seal on HALT (RGC-INV-003)
        result = sealer.seal(artifacts, trigger="halt_event", predecessor_block=last_block)

    Output:
        Writes OMNIX-BLOCK-YYYYMMDD-NNNNNN.json to output_dir.
        Optionally writes Parquet if pyarrow is installed.
        Returns SealResult with custody log entries for DB insertion.
    """

    def __init__(
        self,
        output_dir: str = "cold_archive",
        secret_key_b64: Optional[str] = None,
        write_parquet: bool = False,
    ):
        self.output_dir     = Path(output_dir)
        self.secret_key_b64 = secret_key_b64 or os.environ.get(
            "OMNIX_SIGNING_SECRET_KEY_B64", ""
        ).strip()
        self.write_parquet  = write_parquet
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def seal(
        self,
        artifacts: List[Dict[str, Any]],
        trigger: str = "scheduler",
        predecessor_block: Optional[Dict[str, Any]] = None,
        date_str: Optional[str] = None,
        sealed_by: str = "omnix_archive_pipeline",
    ) -> SealResult:
        """
        Seal a set of artifacts into a COLD archive block.

        Args:
            artifacts:         List of artifact dicts. Each MUST have content_hash.
            trigger:           'scheduler' | 'halt_event' | 'admin'
            predecessor_block: Dict of the previous sealed block (for chain continuity).
                               If None, this block is treated as potentially genesis.
            date_str:          Date string for block ID (YYYYMMDD). Defaults to today UTC.
            sealed_by:         Identity of the sealing process.

        Returns:
            SealResult with the sealed block and custody log entries.
        """
        t_start  = time.monotonic()
        errors:   List[str] = []
        warnings: List[str] = []

        # ── Pre-seal validation ──────────────────────────────────────────────
        val_errors, val_warnings = _validate_artifacts_for_seal(artifacts, trigger)
        errors.extend(val_errors)
        warnings.extend(val_warnings)

        if errors:
            return SealResult(
                success=False, block=None, custody_entries=[],
                block_file=None, errors=errors, warnings=warnings,
                seal_duration_ms=0.0,
            )

        # ── Block ID and timestamp ───────────────────────────────────────────
        block_id = _next_block_id(date_str)
        now_ns   = time.time_ns()
        now_iso  = datetime.now(timezone.utc).isoformat()

        # ── Predecessor hash ─────────────────────────────────────────────────
        if predecessor_block is not None:
            predecessor_hash = predecessor_block.get("canonical_hash", "")
            if not predecessor_hash:
                errors.append("EAP-INV-003: predecessor_block has no canonical_hash")
                return SealResult(
                    success=False, block=None, custody_entries=[],
                    block_file=None, errors=errors, warnings=warnings,
                    seal_duration_ms=0.0,
                )
        else:
            predecessor_hash = GENESIS_PREDECESSOR
            if trigger != "scheduler":
                warnings.append(
                    "No predecessor block provided — block will use genesis sentinel. "
                    "This is only correct for the very first COLD block in the archive."
                )

        # ── Artifact metadata ────────────────────────────────────────────────
        artifact_hashes = [
            a.get("content_hash", "") for a in artifacts
        ]
        artifact_ids = [
            a.get("artifact_id") or a.get("id") or f"UNKNOWN-{i}"
            for i, a in enumerate(artifacts)
        ]
        evidence_classes = sorted({
            a.get("evidence_class", "UNKNOWN") for a in artifacts
        })

        # ── Merkle root (Step 2 in verifier) ────────────────────────────────
        merkle_root = compute_merkle_root(artifact_hashes)

        # ── Canonical hash (Step 3 in verifier) ─────────────────────────────
        canonical_hash = compute_canonical_hash(
            block_id=block_id,
            creation_timestamp_ns=now_ns,
            artifact_count=len(artifacts),
            evidence_classes=evidence_classes,
            merkle_root=merkle_root,
            predecessor_block_hash=predecessor_hash,
        )

        # ── PQC signature (Step 4 in verifier) ──────────────────────────────
        pqc_signature: Optional[str] = None
        if self.secret_key_b64:
            pqc_signature = _sign_with_dilithium(canonical_hash, self.secret_key_b64)
            if pqc_signature:
                logger.info(f"Block {block_id}: ML-DSA-65 signature applied")
            else:
                warnings.append(
                    f"Block {block_id}: PQC signing failed — pypqc unavailable. "
                    f"Block sealed without ML-DSA-65 signature (EAP-INV-002 not satisfied)."
                )
        else:
            warnings.append(
                f"Block {block_id}: No signing key configured — block sealed without PQC signature. "
                f"Set OMNIX_SIGNING_SECRET_KEY_B64 to enable EAP-INV-002 compliance."
            )

        # ── Assemble block ───────────────────────────────────────────────────
        block = SealedBlock(
            block_id=block_id,
            creation_timestamp_ns=now_ns,
            artifact_count=len(artifacts),
            evidence_classes=evidence_classes,
            canonical_hash=canonical_hash,
            predecessor_block_hash=predecessor_hash,
            integrity_manifest={
                "artifact_hashes": artifact_hashes,
                "merkle_root":     merkle_root,
                "hash_algorithm":  HASH_ALGORITHM_V1,
            },
            pqc_signature=pqc_signature,
            pqc_algorithm=PQC_ALGORITHM,
            omnix_version=OMNIX_VERSION,
            sealed_at=now_iso,
            sealed_by=sealed_by,
            seal_trigger=trigger,
            artifact_ids=artifact_ids,
        )

        # ── Write block file ─────────────────────────────────────────────────
        block_file_path = self.output_dir / block.block_file_name
        block_dict      = block.to_dict()

        try:
            with open(block_file_path, "w") as f:
                json.dump(block_dict, f, indent=2)
            logger.info(f"Block sealed: {block_file_path}")
        except OSError as exc:
            errors.append(f"Failed to write block file: {exc}")
            return SealResult(
                success=False, block=block, custody_entries=[],
                block_file=None, errors=errors, warnings=warnings,
                seal_duration_ms=(time.monotonic() - t_start) * 1000,
            )

        # ── Optional Parquet output ──────────────────────────────────────────
        if self.write_parquet:
            try:
                import pyarrow as pa
                import pyarrow.parquet as pq
                table = pa.table({
                    "block_id":        [block_id],
                    "canonical_hash":  [canonical_hash],
                    "artifact_count":  [len(artifacts)],
                    "merkle_root":     [merkle_root],
                    "predecessor_hash": [predecessor_hash],
                    "pqc_signature":   [pqc_signature or ""],
                    "created_ns":      [now_ns],
                    "manifest_json":   [json.dumps(block_dict, indent=2)],
                })
                parquet_path = str(block_file_path).replace(".json", ".parquet")
                pq.write_table(table, parquet_path)
                logger.info(f"Parquet written: {parquet_path}")
            except ImportError:
                warnings.append("pyarrow not installed — Parquet output skipped (JSON only).")
            except Exception as exc:
                warnings.append(f"Parquet write failed: {exc}")

        # ── Custody log entries ──────────────────────────────────────────────
        transition    = "EMERGENCY_COLD" if trigger == "halt_event" else "WARM->COLD"
        to_hash_block = _sha256_prefixed(f"{canonical_hash}:{trigger}".encode())

        custody_entries: List[CustodyLogEntry] = []
        for artifact in artifacts:
            entry = CustodyLogEntry(
                custody_id=        "CUS-" + uuid.uuid4().hex[:16].upper(),
                artifact_id=       artifact.get("artifact_id") or artifact.get("id") or "UNKNOWN",
                evidence_class=    artifact.get("evidence_class", "UNKNOWN"),
                transition=        transition,
                from_hash=         artifact.get("content_hash", ""),
                to_hash=           to_hash_block,
                block_id=          block_id,
                triggered_by=      trigger,
                transition_ns=     now_ns,
                integrity_verified=False,
                verified_at=       None,
                notes=             f"Sealed in {block_id}",
            )
            custody_entries.append(entry)

        logger.info(
            f"Block {block_id} sealed: {len(artifacts)} artifacts, "
            f"trigger={trigger}, pqc={'YES' if pqc_signature else 'NO'}"
        )

        return SealResult(
            success=True,
            block=block,
            custody_entries=custody_entries,
            block_file=str(block_file_path),
            errors=errors,
            warnings=warnings,
            seal_duration_ms=(time.monotonic() - t_start) * 1000,
        )

    def seal_emergency(
        self,
        artifacts: List[Dict[str, Any]],
        chain_root_id: str,
        predecessor_block: Optional[Dict[str, Any]] = None,
    ) -> SealResult:
        """
        Emergency COLD seal triggered by a governance HALT (RGC-INV-003).

        Filters artifacts to only EXCEPTION-class (and other immutable classes)
        from the halted chain, then seals immediately regardless of age.
        This prevents any post-halt modification of the evidence trail.

        ADR-163 §4: On governance halt trigger.
        """
        logger.warning(
            f"EMERGENCY COLD SEAL triggered — chain_root: {chain_root_id}. "
            f"Sealing {len(artifacts)} artifacts immediately."
        )
        emergency_artifacts = [
            a for a in artifacts
            if a.get("evidence_class") in IMMUTABLE_CLASSES
        ]
        if not emergency_artifacts:
            return SealResult(
                success=False, block=None, custody_entries=[],
                block_file=None,
                errors=["No IMMUTABLE-class artifacts to emergency-seal"],
                warnings=[], seal_duration_ms=0.0,
            )

        return self.seal(
            artifacts=emergency_artifacts,
            trigger="halt_event",
            predecessor_block=predecessor_block,
            sealed_by=f"halt_event:{chain_root_id}",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Warm manifest writer
# ─────────────────────────────────────────────────────────────────────────────

def create_warm_manifest_entry(
    artifact: Dict[str, Any],
    compression_method: str,
    compressed_artifact: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a warm_archive_manifest entry before any compression occurs.
    EAP-INV-001 + EAP-INV-006: original hash MUST be recorded before transformation.

    Args:
        artifact:            Original artifact dict with content_hash.
        compression_method:  'aggregate_hourly' | 'strip_nominal' | 'none'
        compressed_artifact: Compressed artifact dict (if already computed).

    Returns:
        warm_archive_manifest row dict.
    """
    original_hash = artifact.get("content_hash", "")
    if not original_hash:
        raise ValueError(
            f"EAP-INV-001: artifact {artifact.get('artifact_id', '?')} "
            f"has no content_hash — cannot create WARM manifest entry"
        )

    if compressed_artifact is not None:
        compressed_data = _canonical_json(compressed_artifact)
        compressed_hash = _sha256_prefixed(compressed_data)
    else:
        compressed_hash = original_hash

    return {
        "manifest_id":           "MAN-" + uuid.uuid4().hex[:16].upper(),
        "original_artifact_id":  artifact.get("artifact_id") or artifact.get("id") or "UNKNOWN",
        "evidence_class":        artifact.get("evidence_class", "UNKNOWN"),
        "original_hash":         original_hash,
        "compressed_hash":       compressed_hash,
        "compression_method":    compression_method,
        "promoted_at":           datetime.now(timezone.utc).isoformat(),
        "promoted_by":           "lifecycle_pipeline",
        "integrity_verified":    False,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Shadow event reducer (ADR-162 §4)
# ─────────────────────────────────────────────────────────────────────────────

SHADOW_NOMINAL_FIELDS = frozenset({
    "event_id", "timestamp_ns", "event_type",
    "agent_id", "content_hash", "risk_score",
})

SHADOW_EXCEPTION_TRIGGERS = frozenset({
    "veto", "anomaly", "escalation", "critical_risk",
})


def classify_shadow_event(event: Dict[str, Any]) -> str:
    """
    Classify a shadow_trade_event at write time (ADR-162 §4).
    Returns the evidence class: 'EXCEPTION' or 'SHADOW_NOMINAL'.
    """
    trigger    = event.get("trigger", "")
    risk_score = float(event.get("risk_score", 0))

    if trigger in SHADOW_EXCEPTION_TRIGGERS:
        return "EXCEPTION"
    if risk_score >= 0.95:
        return "EXCEPTION"
    return "SHADOW_NOMINAL"


def reduce_shadow_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Strip a SHADOW_NOMINAL event to its minimal required fields (ADR-162 §4).
    EXCEPTION events are returned unchanged.
    """
    cls = classify_shadow_event(event)
    if cls == "EXCEPTION":
        return dict(event)
    return {k: event[k] for k in SHADOW_NOMINAL_FIELDS if k in event}
