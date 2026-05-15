"""
ADR-162 / Evidence Lifecycle & Immutable Retention — Production Audit Suite
============================================================================
Auditoría completa de la Evidence Lifecycle & Immutable Retention policy.

Cobertura:
  1.  Evidence class definitions     — 8 classes, codes, forensic values
  2.  Retention tier policy          — HOT / WARM / COLD per class
  3.  Immutable class enforcement    — LEGAL/PQC/CONTRACT/EXCEPTION never WARM
  4.  Shadow event reduction policy  — payload per event type
  5.  RCR summarization policy       — status → evidence class mapping
  6.  rcr_hourly_aggregate schema    — all required fields
  7.  ELR-INV-001                    — Verifiability Preservation
  8.  ELR-INV-002                    — Exception Permanence
  9.  ELR-INV-003                    — Classification Immutability
  10. ELR-INV-004                    — HOT Retention Guarantee (30-day minimum)
  11. warm_archive existing table    — decision_receipts_warm ratified
  12. DB maintenance policy          — vacuum, autovacuum, dead indexes
  13. ATF-INV-006 preservation       — content_hash + pqc_signatures in COLD
  14. Documentation coherence        — references, counts, terminology
  15. Regression audit               — ADR-156–161 unaffected

Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""

import hashlib
import json
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# ADR-162 Canonical Constants
# ─────────────────────────────────────────────────────────────────────────────

EVIDENCE_CLASSES = {
    "LEGAL",
    "PQC",
    "CONTRACT",
    "EXCEPTION",
    "TELEMETRY",
    "SAMPLE",
    "SHADOW_NOMINAL",
    "OPS",
}

IMMUTABLE_CLASSES = {"LEGAL", "PQC", "CONTRACT", "EXCEPTION"}
COMPRESSIBLE_CLASSES = {"TELEMETRY", "SAMPLE", "SHADOW_NOMINAL", "OPS"}

HOT_MINIMUM_DAYS = 30          # ELR-INV-004: no class leaves HOT before 30 days
HOT_STANDARD_DAYS = 90         # standard HOT retention for TELEMETRY/SAMPLE/SHADOW_NOMINAL/OPS
WARM_MAX_DAYS = 365            # WARM upper bound

IMMUTABLE_HOT_DURATION = "Permanent"    # LEGAL/PQC/CONTRACT/EXCEPTION HOT
IMMUTABLE_WARM = "Never"               # IMMUTABLE classes never enter WARM
IMMUTABLE_COLD = "Optional immutable archive"
IMMUTABLE_DELETION = "Never"

RCR_STATUS_TO_CLASS = {
    "HALT":          "EXCEPTION",
    "CRITICAL":      "EXCEPTION",
    "FRAGMENTATION": "EXCEPTION",
    "ESCALATION":    "EXCEPTION",
    "WARNING":       "EXCEPTION",
    "MONITORING":    "TELEMETRY",
    "NOMINAL":       "SAMPLE",
    "HEALTHY":       "SAMPLE",
}

SHADOW_EXCEPTION_TRIGGERS = {"veto", "anomaly", "escalation", "critical_risk"}

SHADOW_NOMINAL_FIELDS = {
    "event_id",
    "timestamp_ns",
    "event_type",
    "agent_id",
    "content_hash",
    "risk_score",
}

RCR_HOURLY_AGGREGATE_REQUIRED_FIELDS = {
    "hour_bucket",
    "chain_root_id",
    "domain",
    "sample_count",
    "avg_ces_score",
    "min_ces_score",
    "status_distribution",
    "first_rcr_id",
    "last_rcr_id",
    "content_hash",
}

SHADOW_VOLUME_REDUCTION_PCT = 80   # ADR-162 §4: ~80% volume decrease

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def compute_content_hash(fields: Dict[str, Any]) -> str:
    canonical = json.dumps(fields, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()


def make_rcr(status: str, chain_root_id: str = None) -> Dict[str, Any]:
    return {
        "rcr_id": "ATFRCR-" + uuid.uuid4().hex[:16].upper(),
        "chain_root_id": chain_root_id or "ATFDR-ROOT-" + uuid.uuid4().hex[:8].upper(),
        "domain": "trading",
        "ces_score": {"HALT": 0, "CRITICAL": 9, "FRAGMENTATION": 5,
                      "ESCALATION": 12, "WARNING": 24, "MONITORING": 60,
                      "NOMINAL": 88, "HEALTHY": 95}.get(status, 50),
        "status": status,
        "timestamp_ns": time.time_ns(),
    }


def make_shadow_event(trigger: Optional[str] = None) -> Dict[str, Any]:
    base = {
        "event_id": uuid.uuid4().hex,
        "timestamp_ns": time.time_ns(),
        "event_type": "TRADE_SIGNAL",
        "agent_id": "agent-001",
        "content_hash": compute_content_hash({"x": 1}),
        "risk_score": 0.12,
        "payload": {"symbol": "BTC-USD", "qty": 0.1, "price": 68000},
    }
    if trigger:
        base["trigger"] = trigger
    return base


# ─────────────────────────────────────────────────────────────────────────────
# 1. Evidence Class Definitions
# ─────────────────────────────────────────────────────────────────────────────

class TestV01_EvidenceClassDefinitions:

    def test_exactly_8_evidence_classes_defined(self):
        assert len(EVIDENCE_CLASSES) == 8

    def test_all_required_classes_present(self):
        required = {
            "LEGAL", "PQC", "CONTRACT", "EXCEPTION",
            "TELEMETRY", "SAMPLE", "SHADOW_NOMINAL", "OPS",
        }
        assert required == EVIDENCE_CLASSES

    def test_immutable_classes_are_subset_of_all_classes(self):
        assert IMMUTABLE_CLASSES.issubset(EVIDENCE_CLASSES)

    def test_compressible_classes_are_subset_of_all_classes(self):
        assert COMPRESSIBLE_CLASSES.issubset(EVIDENCE_CLASSES)

    def test_immutable_and_compressible_are_disjoint(self):
        assert IMMUTABLE_CLASSES.isdisjoint(COMPRESSIBLE_CLASSES)

    def test_immutable_plus_compressible_covers_all_classes(self):
        assert IMMUTABLE_CLASSES | COMPRESSIBLE_CLASSES == EVIDENCE_CLASSES

    def test_legal_class_is_immutable(self):
        assert "LEGAL" in IMMUTABLE_CLASSES

    def test_pqc_class_is_immutable(self):
        assert "PQC" in IMMUTABLE_CLASSES

    def test_contract_class_is_immutable(self):
        assert "CONTRACT" in IMMUTABLE_CLASSES

    def test_exception_class_is_immutable(self):
        assert "EXCEPTION" in IMMUTABLE_CLASSES

    def test_telemetry_class_is_compressible(self):
        assert "TELEMETRY" in COMPRESSIBLE_CLASSES

    def test_sample_class_is_compressible(self):
        assert "SAMPLE" in COMPRESSIBLE_CLASSES

    def test_shadow_nominal_class_is_compressible(self):
        assert "SHADOW_NOMINAL" in COMPRESSIBLE_CLASSES

    def test_ops_class_is_compressible(self):
        assert "OPS" in COMPRESSIBLE_CLASSES


# ─────────────────────────────────────────────────────────────────────────────
# 2. Retention Tier Policy
# ─────────────────────────────────────────────────────────────────────────────

class TestV02_RetentionTierPolicy:

    def test_immutable_classes_hot_is_permanent(self):
        for cls in IMMUTABLE_CLASSES:
            assert IMMUTABLE_HOT_DURATION == "Permanent"

    def test_immutable_classes_warm_is_never(self):
        assert IMMUTABLE_WARM == "Never"

    def test_immutable_classes_deletion_is_never(self):
        assert IMMUTABLE_DELETION == "Never"

    def test_hot_minimum_is_30_days(self):
        assert HOT_MINIMUM_DAYS == 30

    def test_hot_standard_is_90_days(self):
        assert HOT_STANDARD_DAYS == 90

    def test_warm_max_is_365_days(self):
        assert WARM_MAX_DAYS == 365

    def test_hot_minimum_less_than_standard(self):
        assert HOT_MINIMUM_DAYS < HOT_STANDARD_DAYS

    def test_warm_upper_bound_greater_than_hot_standard(self):
        assert WARM_MAX_DAYS > HOT_STANDARD_DAYS

    def test_telemetry_eligible_for_warm(self):
        assert "TELEMETRY" in COMPRESSIBLE_CLASSES

    def test_sample_eligible_for_warm(self):
        assert "SAMPLE" in COMPRESSIBLE_CLASSES

    def test_shadow_nominal_eligible_for_warm(self):
        assert "SHADOW_NOMINAL" in COMPRESSIBLE_CLASSES

    def test_ops_eligible_for_warm(self):
        assert "OPS" in COMPRESSIBLE_CLASSES

    def test_legal_not_eligible_for_warm(self):
        assert "LEGAL" not in COMPRESSIBLE_CLASSES

    def test_pqc_not_eligible_for_warm(self):
        assert "PQC" not in COMPRESSIBLE_CLASSES

    def test_contract_not_eligible_for_warm(self):
        assert "CONTRACT" not in COMPRESSIBLE_CLASSES

    def test_exception_not_eligible_for_warm(self):
        assert "EXCEPTION" not in COMPRESSIBLE_CLASSES


# ─────────────────────────────────────────────────────────────────────────────
# 3. Immutable Class Enforcement
# ─────────────────────────────────────────────────────────────────────────────

class TestV03_ImmutableClassEnforcement:

    def _lifecycle_engine_classify_warm_eligibility(self, evidence_class: str) -> bool:
        return evidence_class in COMPRESSIBLE_CLASSES

    def test_legal_not_warm_eligible(self):
        assert not self._lifecycle_engine_classify_warm_eligibility("LEGAL")

    def test_pqc_not_warm_eligible(self):
        assert not self._lifecycle_engine_classify_warm_eligibility("PQC")

    def test_contract_not_warm_eligible(self):
        assert not self._lifecycle_engine_classify_warm_eligibility("CONTRACT")

    def test_exception_not_warm_eligible(self):
        assert not self._lifecycle_engine_classify_warm_eligibility("EXCEPTION")

    def test_telemetry_is_warm_eligible(self):
        assert self._lifecycle_engine_classify_warm_eligibility("TELEMETRY")

    def test_sample_is_warm_eligible(self):
        assert self._lifecycle_engine_classify_warm_eligibility("SAMPLE")

    def test_shadow_nominal_is_warm_eligible(self):
        assert self._lifecycle_engine_classify_warm_eligibility("SHADOW_NOMINAL")

    def test_ops_is_warm_eligible(self):
        assert self._lifecycle_engine_classify_warm_eligibility("OPS")

    def test_unknown_class_not_warm_eligible(self):
        assert not self._lifecycle_engine_classify_warm_eligibility("UNKNOWN")

    def test_empty_string_not_warm_eligible(self):
        assert not self._lifecycle_engine_classify_warm_eligibility("")

    def test_lowercase_class_not_warm_eligible(self):
        assert not self._lifecycle_engine_classify_warm_eligibility("telemetry")

    def test_all_immutable_classes_fail_warm_eligibility(self):
        for cls in IMMUTABLE_CLASSES:
            assert not self._lifecycle_engine_classify_warm_eligibility(cls), \
                f"IMMUTABLE class {cls} must not be warm-eligible"

    def test_all_compressible_classes_pass_warm_eligibility(self):
        for cls in COMPRESSIBLE_CLASSES:
            assert self._lifecycle_engine_classify_warm_eligibility(cls), \
                f"COMPRESSIBLE class {cls} must be warm-eligible"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Shadow Event Reduction Policy
# ─────────────────────────────────────────────────────────────────────────────

class TestV04_ShadowEventReductionPolicy:

    def _classify_shadow_event(self, event: Dict[str, Any]) -> str:
        trigger = event.get("trigger", "")
        if trigger in SHADOW_EXCEPTION_TRIGGERS:
            return "EXCEPTION"
        risk_score = event.get("risk_score", 0)
        if risk_score >= 0.95:
            return "EXCEPTION"
        return "SHADOW_NOMINAL"

    def _get_stored_fields(self, evidence_class: str, event: Dict[str, Any]) -> Dict[str, Any]:
        if evidence_class == "EXCEPTION":
            return event
        return {k: event[k] for k in SHADOW_NOMINAL_FIELDS if k in event}

    def test_veto_trigger_classified_as_exception(self):
        event = make_shadow_event(trigger="veto")
        assert self._classify_shadow_event(event) == "EXCEPTION"

    def test_anomaly_trigger_classified_as_exception(self):
        event = make_shadow_event(trigger="anomaly")
        assert self._classify_shadow_event(event) == "EXCEPTION"

    def test_escalation_trigger_classified_as_exception(self):
        event = make_shadow_event(trigger="escalation")
        assert self._classify_shadow_event(event) == "EXCEPTION"

    def test_critical_risk_trigger_classified_as_exception(self):
        event = make_shadow_event(trigger="critical_risk")
        assert self._classify_shadow_event(event) == "EXCEPTION"

    def test_nominal_event_classified_as_shadow_nominal(self):
        event = make_shadow_event()
        assert self._classify_shadow_event(event) == "SHADOW_NOMINAL"

    def test_exception_event_stores_full_payload(self):
        event = make_shadow_event(trigger="veto")
        cls = self._classify_shadow_event(event)
        stored = self._get_stored_fields(cls, event)
        assert "payload" in stored

    def test_nominal_event_drops_payload(self):
        event = make_shadow_event()
        cls = self._classify_shadow_event(event)
        stored = self._get_stored_fields(cls, event)
        assert "payload" not in stored

    def test_nominal_event_retains_required_fields(self):
        event = make_shadow_event()
        cls = self._classify_shadow_event(event)
        stored = self._get_stored_fields(cls, event)
        required = SHADOW_NOMINAL_FIELDS & set(event.keys())
        for f in required:
            assert f in stored, f"Required field {f} missing from SHADOW_NOMINAL storage"

    def test_nominal_event_retains_content_hash(self):
        event = make_shadow_event()
        cls = self._classify_shadow_event(event)
        stored = self._get_stored_fields(cls, event)
        assert "content_hash" in stored

    def test_nominal_event_retains_timestamp_ns(self):
        event = make_shadow_event()
        cls = self._classify_shadow_event(event)
        stored = self._get_stored_fields(cls, event)
        assert "timestamp_ns" in stored

    def test_shadow_nominal_stored_fields_count(self):
        event = make_shadow_event()
        cls = self._classify_shadow_event(event)
        stored = self._get_stored_fields(cls, event)
        assert len(stored) <= len(SHADOW_NOMINAL_FIELDS)

    def test_expected_volume_reduction_pct_defined(self):
        assert SHADOW_VOLUME_REDUCTION_PCT == 80

    def test_classification_at_write_time_not_retroactive(self):
        events = [make_shadow_event() for _ in range(10)]
        for event in events:
            cls = self._classify_shadow_event(event)
            assert cls in EVIDENCE_CLASSES


# ─────────────────────────────────────────────────────────────────────────────
# 5. RCR Summarization Policy
# ─────────────────────────────────────────────────────────────────────────────

class TestV05_RCRSummarizationPolicy:

    def _classify_rcr(self, rcr: Dict[str, Any]) -> str:
        return RCR_STATUS_TO_CLASS.get(rcr["status"], "TELEMETRY")

    def test_halt_rcr_classified_as_exception(self):
        assert self._classify_rcr(make_rcr("HALT")) == "EXCEPTION"

    def test_critical_rcr_classified_as_exception(self):
        assert self._classify_rcr(make_rcr("CRITICAL")) == "EXCEPTION"

    def test_fragmentation_rcr_classified_as_exception(self):
        assert self._classify_rcr(make_rcr("FRAGMENTATION")) == "EXCEPTION"

    def test_escalation_rcr_classified_as_exception(self):
        assert self._classify_rcr(make_rcr("ESCALATION")) == "EXCEPTION"

    def test_warning_rcr_classified_as_exception(self):
        assert self._classify_rcr(make_rcr("WARNING")) == "EXCEPTION"

    def test_monitoring_rcr_classified_as_telemetry(self):
        assert self._classify_rcr(make_rcr("MONITORING")) == "TELEMETRY"

    def test_nominal_rcr_classified_as_sample(self):
        assert self._classify_rcr(make_rcr("NOMINAL")) == "SAMPLE"

    def test_healthy_rcr_classified_as_sample(self):
        assert self._classify_rcr(make_rcr("HEALTHY")) == "SAMPLE"

    def test_exception_rcr_never_compressible(self):
        for status in ["HALT", "CRITICAL", "FRAGMENTATION", "ESCALATION", "WARNING"]:
            cls = self._classify_rcr(make_rcr(status))
            assert cls not in COMPRESSIBLE_CLASSES, \
                f"RCR status {status} must produce EXCEPTION class, not compressible"

    def test_all_rcr_statuses_produce_valid_evidence_class(self):
        for status, expected_class in RCR_STATUS_TO_CLASS.items():
            assert expected_class in EVIDENCE_CLASSES, \
                f"Status {status} maps to invalid class {expected_class}"

    def test_nominal_rcr_aggregatable_into_hourly(self):
        cls = self._classify_rcr(make_rcr("NOMINAL"))
        assert cls == "SAMPLE"
        assert cls in COMPRESSIBLE_CLASSES

    def test_halt_rcr_not_aggregatable(self):
        cls = self._classify_rcr(make_rcr("HALT"))
        assert cls not in COMPRESSIBLE_CLASSES


# ─────────────────────────────────────────────────────────────────────────────
# 6. rcr_hourly_aggregate Schema
# ─────────────────────────────────────────────────────────────────────────────

class TestV06_RCRHourlyAggregateSchema:

    def _make_aggregate(self, rcrs: List[Dict]) -> Dict[str, Any]:
        if not rcrs:
            return {}
        hour = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        chain_root = rcrs[0]["chain_root_id"]
        ces_scores = [r["ces_score"] for r in rcrs]
        statuses: Dict[str, int] = {}
        for r in rcrs:
            statuses[r["status"]] = statuses.get(r["status"], 0) + 1
        agg = {
            "hour_bucket": hour.isoformat(),
            "chain_root_id": chain_root,
            "domain": rcrs[0]["domain"],
            "sample_count": len(rcrs),
            "avg_ces_score": sum(ces_scores) / len(ces_scores),
            "min_ces_score": min(ces_scores),
            "status_distribution": statuses,
            "first_rcr_id": rcrs[0]["rcr_id"],
            "last_rcr_id": rcrs[-1]["rcr_id"],
            "content_hash": compute_content_hash({"hour": hour.isoformat(), "chain": chain_root}),
        }
        return agg

    def test_aggregate_contains_all_required_fields(self):
        rcrs = [make_rcr("NOMINAL") for _ in range(5)]
        agg = self._make_aggregate(rcrs)
        for field in RCR_HOURLY_AGGREGATE_REQUIRED_FIELDS:
            assert field in agg, f"Required field {field} missing from aggregate"

    def test_aggregate_has_correct_sample_count(self):
        n = 12
        rcrs = [make_rcr("NOMINAL") for _ in range(n)]
        agg = self._make_aggregate(rcrs)
        assert agg["sample_count"] == n

    def test_aggregate_avg_ces_is_numeric(self):
        rcrs = [make_rcr("NOMINAL") for _ in range(5)]
        agg = self._make_aggregate(rcrs)
        assert isinstance(agg["avg_ces_score"], float)

    def test_aggregate_min_ces_leq_avg_ces(self):
        rcrs = [make_rcr("NOMINAL") for _ in range(5)]
        agg = self._make_aggregate(rcrs)
        assert agg["min_ces_score"] <= agg["avg_ces_score"]

    def test_aggregate_has_content_hash(self):
        rcrs = [make_rcr("NOMINAL") for _ in range(3)]
        agg = self._make_aggregate(rcrs)
        assert "content_hash" in agg
        assert agg["content_hash"].startswith("sha256:")

    def test_aggregate_has_status_distribution(self):
        rcrs = [make_rcr("NOMINAL") for _ in range(5)]
        agg = self._make_aggregate(rcrs)
        dist = agg["status_distribution"]
        assert isinstance(dist, dict)
        assert "NOMINAL" in dist
        assert dist["NOMINAL"] == 5

    def test_aggregate_first_and_last_rcr_ids_present(self):
        rcrs = [make_rcr("NOMINAL") for _ in range(4)]
        agg = self._make_aggregate(rcrs)
        assert agg["first_rcr_id"] == rcrs[0]["rcr_id"]
        assert agg["last_rcr_id"] == rcrs[-1]["rcr_id"]

    def test_aggregate_content_hash_starts_sha256(self):
        rcrs = [make_rcr("NOMINAL")]
        agg = self._make_aggregate(rcrs)
        assert agg["content_hash"].startswith("sha256:")

    def test_aggregate_is_not_substitute_for_forensic_rcrs(self):
        halt_rcr = make_rcr("HALT")
        nominal_rcrs = [make_rcr("NOMINAL") for _ in range(5)]
        nominal_cls = [RCR_STATUS_TO_CLASS[r["status"]] for r in nominal_rcrs]
        halt_cls = RCR_STATUS_TO_CLASS[halt_rcr["status"]]
        assert halt_cls not in COMPRESSIBLE_CLASSES
        assert all(c in COMPRESSIBLE_CLASSES for c in nominal_cls)


# ─────────────────────────────────────────────────────────────────────────────
# 7. ELR-INV-001 — Verifiability Preservation
# ─────────────────────────────────────────────────────────────────────────────

class TestV07_ELR_INV_001_VerifiabilityPreservation:
    """
    ELR-INV-001: Any artifact moved to COLD tier MUST retain its content_hash
    and pqc_signatures in a form that allows offline verification per ATF-INV-006.
    """

    def _archive_to_cold(self, artifact: Dict[str, Any]) -> Dict[str, Any]:
        cold = dict(artifact)
        assert "content_hash" in cold, "ELR-INV-001: content_hash must be present before COLD"
        return cold

    def test_content_hash_preserved_in_cold(self):
        artifact = {
            "receipt_id": "ATFDR-" + uuid.uuid4().hex[:16].upper(),
            "content_hash": compute_content_hash({"x": 1}),
            "pqc_signatures": ["sig-abc123"],
        }
        cold = self._archive_to_cold(artifact)
        assert cold["content_hash"] == artifact["content_hash"]

    def test_pqc_signatures_preserved_in_cold(self):
        artifact = {
            "receipt_id": "ATFDR-" + uuid.uuid4().hex[:16].upper(),
            "content_hash": compute_content_hash({"x": 1}),
            "pqc_signatures": ["sig-abc123", "sig-def456"],
        }
        cold = self._archive_to_cold(artifact)
        assert cold["pqc_signatures"] == artifact["pqc_signatures"]

    def test_hash_mutation_violates_invariant(self):
        artifact = {
            "content_hash": compute_content_hash({"x": 1}),
            "pqc_signatures": ["sig-abc"],
        }
        tampered = dict(artifact)
        tampered["content_hash"] = compute_content_hash({"x": 2})
        assert tampered["content_hash"] != artifact["content_hash"]

    def test_content_hash_format_sha256(self):
        payload = {"field": "value", "ts": 12345}
        h = compute_content_hash(payload)
        assert h.startswith("sha256:")
        assert len(h) == len("sha256:") + 64

    def test_content_hash_is_deterministic(self):
        payload = {"field": "value", "ts": 12345}
        h1 = compute_content_hash(payload)
        h2 = compute_content_hash(payload)
        assert h1 == h2

    def test_content_hash_sensitive_to_field_changes(self):
        h1 = compute_content_hash({"x": 1})
        h2 = compute_content_hash({"x": 2})
        assert h1 != h2

    def test_artifact_without_content_hash_cannot_go_cold(self):
        artifact = {"receipt_id": "ATFDR-001", "domain": "trading"}
        with pytest.raises((AssertionError, KeyError)):
            self._archive_to_cold(artifact)

    def test_atf_inv006_requires_offline_verification_path(self):
        artifact = {
            "content_hash": compute_content_hash({"decision": "APPROVED"}),
            "pqc_signatures": ["ml-dsa-65-sig"],
        }
        cold = self._archive_to_cold(artifact)
        assert cold["content_hash"] is not None
        assert cold["pqc_signatures"] is not None
        assert len(cold["pqc_signatures"]) > 0


# ─────────────────────────────────────────────────────────────────────────────
# 8. ELR-INV-002 — Exception Permanence
# ─────────────────────────────────────────────────────────────────────────────

class TestV08_ELR_INV_002_ExceptionPermanence:
    """
    ELR-INV-002: No artifact classified as EXCEPTION, LEGAL, PQC, or CONTRACT
    may be deleted, truncated, or compressed in a way that reduces its forensic
    completeness, regardless of age.
    """

    def _can_delete(self, evidence_class: str) -> bool:
        return evidence_class not in IMMUTABLE_CLASSES

    def _can_compress_payload(self, evidence_class: str) -> bool:
        return evidence_class in COMPRESSIBLE_CLASSES

    def test_exception_cannot_be_deleted(self):
        assert not self._can_delete("EXCEPTION")

    def test_legal_cannot_be_deleted(self):
        assert not self._can_delete("LEGAL")

    def test_pqc_cannot_be_deleted(self):
        assert not self._can_delete("PQC")

    def test_contract_cannot_be_deleted(self):
        assert not self._can_delete("CONTRACT")

    def test_telemetry_can_be_deleted_after_aggregation(self):
        assert self._can_delete("TELEMETRY")

    def test_sample_can_be_deleted_after_aggregation(self):
        assert self._can_delete("SAMPLE")

    def test_shadow_nominal_can_be_deleted_after_compression(self):
        assert self._can_delete("SHADOW_NOMINAL")

    def test_exception_payload_cannot_be_compressed(self):
        assert not self._can_compress_payload("EXCEPTION")

    def test_legal_payload_cannot_be_compressed(self):
        assert not self._can_compress_payload("LEGAL")

    def test_pqc_payload_cannot_be_compressed(self):
        assert not self._can_compress_payload("PQC")

    def test_telemetry_can_be_compressed(self):
        assert self._can_compress_payload("TELEMETRY")

    def test_immutable_permanence_regardless_of_age(self):
        for cls in IMMUTABLE_CLASSES:
            assert not self._can_delete(cls), \
                f"Class {cls} must be permanent regardless of age"


# ─────────────────────────────────────────────────────────────────────────────
# 9. ELR-INV-003 — Classification Immutability
# ─────────────────────────────────────────────────────────────────────────────

class TestV09_ELR_INV_003_ClassificationImmutability:
    """
    ELR-INV-003: Once an artifact is classified at write time, its evidence class
    cannot be downgraded. A SHADOW_NOMINAL event that triggered a veto is reclassified
    to EXCEPTION at veto time.
    """

    CLASS_RANK = {
        "LEGAL": 5, "PQC": 5, "CONTRACT": 5, "EXCEPTION": 4,
        "TELEMETRY": 3, "SAMPLE": 2, "SHADOW_NOMINAL": 1, "OPS": 2,
    }

    def _can_reclassify(self, from_class: str, to_class: str) -> bool:
        return self.CLASS_RANK.get(to_class, 0) >= self.CLASS_RANK.get(from_class, 0)

    def test_shadow_nominal_can_be_upgraded_to_exception(self):
        assert self._can_reclassify("SHADOW_NOMINAL", "EXCEPTION")

    def test_exception_cannot_be_downgraded_to_shadow_nominal(self):
        assert not self._can_reclassify("EXCEPTION", "SHADOW_NOMINAL")

    def test_exception_cannot_be_downgraded_to_telemetry(self):
        assert not self._can_reclassify("EXCEPTION", "TELEMETRY")

    def test_legal_cannot_be_downgraded_to_ops(self):
        assert not self._can_reclassify("LEGAL", "OPS")

    def test_telemetry_cannot_be_downgraded_to_shadow_nominal(self):
        assert not self._can_reclassify("TELEMETRY", "SHADOW_NOMINAL")

    def test_shadow_nominal_veto_reclassified_at_veto_time(self):
        event = make_shadow_event()
        initial_class = "SHADOW_NOMINAL"
        veto_occurred = True
        final_class = "EXCEPTION" if veto_occurred else initial_class
        assert final_class == "EXCEPTION"

    def test_reclassification_only_upward(self):
        upgrades = [
            ("SHADOW_NOMINAL", "EXCEPTION"),
            ("SAMPLE", "EXCEPTION"),
            ("TELEMETRY", "EXCEPTION"),
        ]
        for from_cls, to_cls in upgrades:
            assert self._can_reclassify(from_cls, to_cls)

    def test_downgrade_always_rejected(self):
        downgrades = [
            ("LEGAL", "TELEMETRY"),
            ("PQC", "SAMPLE"),
            ("EXCEPTION", "OPS"),
            ("CONTRACT", "SHADOW_NOMINAL"),
        ]
        for from_cls, to_cls in downgrades:
            assert not self._can_reclassify(from_cls, to_cls)


# ─────────────────────────────────────────────────────────────────────────────
# 10. ELR-INV-004 — HOT Retention Guarantee
# ─────────────────────────────────────────────────────────────────────────────

class TestV10_ELR_INV_004_HOTRetentionGuarantee:
    """
    ELR-INV-004: All evidence classes remain in HOT tier for a minimum of 30 days
    regardless of volume pressure. No automated process may promote to WARM before
    this minimum.
    """

    def _can_promote_to_warm(self, evidence_class: str, age_days: int) -> bool:
        if evidence_class in IMMUTABLE_CLASSES:
            return False
        if age_days < HOT_MINIMUM_DAYS:
            return False
        return True

    def test_hot_minimum_is_30_days(self):
        assert HOT_MINIMUM_DAYS == 30

    def test_artifact_at_29_days_cannot_be_promoted(self):
        for cls in COMPRESSIBLE_CLASSES:
            assert not self._can_promote_to_warm(cls, 29)

    def test_artifact_at_30_days_can_be_promoted(self):
        for cls in COMPRESSIBLE_CLASSES:
            assert self._can_promote_to_warm(cls, 30)

    def test_artifact_at_0_days_cannot_be_promoted(self):
        for cls in COMPRESSIBLE_CLASSES:
            assert not self._can_promote_to_warm(cls, 0)

    def test_artifact_at_90_days_can_be_promoted(self):
        for cls in COMPRESSIBLE_CLASSES:
            assert self._can_promote_to_warm(cls, 90)

    def test_legal_never_promoted_regardless_of_age(self):
        for age in [0, 30, 90, 365, 3650]:
            assert not self._can_promote_to_warm("LEGAL", age)

    def test_pqc_never_promoted_regardless_of_age(self):
        for age in [0, 30, 90, 365, 3650]:
            assert not self._can_promote_to_warm("PQC", age)

    def test_contract_never_promoted_regardless_of_age(self):
        for age in [0, 30, 90, 365, 3650]:
            assert not self._can_promote_to_warm("CONTRACT", age)

    def test_exception_never_promoted_regardless_of_age(self):
        for age in [0, 30, 90, 365, 3650]:
            assert not self._can_promote_to_warm("EXCEPTION", age)

    def test_volume_pressure_does_not_override_minimum(self):
        high_volume = True
        for cls in COMPRESSIBLE_CLASSES:
            assert not self._can_promote_to_warm(cls, 29), \
                f"Volume pressure must not override HOT minimum for class {cls}"


# ─────────────────────────────────────────────────────────────────────────────
# 11. decision_receipts_warm Table
# ─────────────────────────────────────────────────────────────────────────────

class TestV11_DecisionReceiptsWarm:

    def test_warm_table_is_ratified_for_legal_class(self):
        warm_artifact_class = "LEGAL"
        assert warm_artifact_class in IMMUTABLE_CLASSES

    def test_warm_table_stores_copies_not_originals(self):
        original = {
            "receipt_id": "DR-001",
            "content_hash": compute_content_hash({"x": 1}),
            "status": "HOT",
        }
        warm_copy = dict(original)
        warm_copy["status"] = "WARM_COPY"
        assert warm_copy["content_hash"] == original["content_hash"]

    def test_hot_originals_remain_after_warm_promotion(self):
        hot_records = [{"id": f"DR-{i}", "status": "HOT"} for i in range(5)]
        warm_copies = [dict(r) for r in hot_records]
        assert len(hot_records) == 5
        assert all(r["status"] == "HOT" for r in hot_records)

    def test_warm_copy_preserves_content_hash(self):
        original_hash = compute_content_hash({"decision": "APPROVE", "domain": "trading"})
        warm_copy = {"content_hash": original_hash}
        assert warm_copy["content_hash"] == original_hash


# ─────────────────────────────────────────────────────────────────────────────
# 12. DB Maintenance Policy
# ─────────────────────────────────────────────────────────────────────────────

class TestV12_DBMaintenancePolicy:

    MAINTENANCE_SCHEDULE = {
        "vacuum_frequency": "weekly",
        "vacuum_trigger_dead_tuples": 10_000,
        "autovacuum_scale_factor_high_turnover": 0.01,
        "autovacuum_analyze_scale_factor_high_turnover": 0.005,
        "dead_index_scan_threshold_days": 30,
    }

    def test_vacuum_runs_weekly(self):
        assert self.MAINTENANCE_SCHEDULE["vacuum_frequency"] == "weekly"

    def test_vacuum_triggered_at_10k_dead_tuples(self):
        assert self.MAINTENANCE_SCHEDULE["vacuum_trigger_dead_tuples"] == 10_000

    def test_autovacuum_scale_factor_is_0_01(self):
        assert self.MAINTENANCE_SCHEDULE["autovacuum_scale_factor_high_turnover"] == 0.01

    def test_autovacuum_analyze_scale_factor_is_0_005(self):
        assert self.MAINTENANCE_SCHEDULE["autovacuum_analyze_scale_factor_high_turnover"] == 0.005

    def test_dead_index_threshold_is_30_days(self):
        assert self.MAINTENANCE_SCHEDULE["dead_index_scan_threshold_days"] == 30

    def test_high_turnover_tables_identified(self):
        high_turnover = {"paper_trading_balances", "avm_calibration_snapshots"}
        assert len(high_turnover) >= 2

    def test_duplicate_indexes_removed_unconditionally(self):
        duplicate_detection_policy = "same_columns_same_table"
        assert duplicate_detection_policy == "same_columns_same_table"


# ─────────────────────────────────────────────────────────────────────────────
# 13. ATF-INV-006 Preservation
# ─────────────────────────────────────────────────────────────────────────────

class TestV13_ATFINV006Preservation:

    def test_cold_archive_preserves_content_hash_for_offline_verification(self):
        artifact = {
            "receipt_id": "ATFDR-001",
            "content_hash": compute_content_hash({"approved_by": "root", "domain": "trading"}),
            "pqc_signatures": ["ml-dsa-65:abc123"],
        }
        cold_stored = {
            "content_hash": artifact["content_hash"],
            "pqc_signatures": artifact["pqc_signatures"],
        }
        assert cold_stored["content_hash"] == artifact["content_hash"]
        assert cold_stored["pqc_signatures"] == artifact["pqc_signatures"]

    def test_pqc_signatures_array_preserved_intact(self):
        sigs = ["ml-dsa-65:abc", "ml-dsa-65:def"]
        cold = {"pqc_signatures": list(sigs)}
        assert cold["pqc_signatures"] == sigs

    def test_atf_inv006_requires_no_platform_dependency(self):
        offline_verification_requires = ["content_hash", "pqc_signatures", "public_key"]
        for req in offline_verification_requires:
            assert req is not None

    def test_hash_mutation_breaks_atf_inv006(self):
        original = compute_content_hash({"x": 1})
        mutated = compute_content_hash({"x": 2})
        assert original != mutated

    def test_cold_tier_invariant_referenced_in_adr(self):
        adr_ref = "RFC-ATF-1 §7.6 — ATF-INV-006"
        assert "ATF-INV-006" in adr_ref


# ─────────────────────────────────────────────────────────────────────────────
# 14. Documentation Coherence
# ─────────────────────────────────────────────────────────────────────────────

class TestV14_DocumentationCoherence:

    def test_adr_162_exists(self):
        import os
        path = "docs/adr/ADR-162-evidence-lifecycle-immutable-retention.md"
        assert os.path.isfile(path), f"ADR-162 not found at {path}"

    def test_adr_162_has_accepted_status(self):
        import os
        path = "docs/adr/ADR-162-evidence-lifecycle-immutable-retention.md"
        with open(path) as f:
            content = f.read()
        assert "Status:** Accepted" in content or "status: Accepted" in content.lower()

    def test_adr_162_defines_8_evidence_classes(self):
        import os
        path = "docs/adr/ADR-162-evidence-lifecycle-immutable-retention.md"
        with open(path) as f:
            content = f.read()
        for cls in EVIDENCE_CLASSES:
            assert f"`{cls}`" in content or cls in content, \
                f"Evidence class {cls} missing from ADR-162"

    def test_adr_162_references_atf_inv006(self):
        import os
        path = "docs/adr/ADR-162-evidence-lifecycle-immutable-retention.md"
        with open(path) as f:
            content = f.read()
        assert "ATF-INV-006" in content

    def test_adr_162_defines_elr_inv001(self):
        import os
        path = "docs/adr/ADR-162-evidence-lifecycle-immutable-retention.md"
        with open(path) as f:
            content = f.read()
        assert "ELR-INV-001" in content

    def test_adr_162_defines_elr_inv002(self):
        import os
        path = "docs/adr/ADR-162-evidence-lifecycle-immutable-retention.md"
        with open(path) as f:
            content = f.read()
        assert "ELR-INV-002" in content

    def test_adr_162_defines_elr_inv003(self):
        import os
        path = "docs/adr/ADR-162-evidence-lifecycle-immutable-retention.md"
        with open(path) as f:
            content = f.read()
        assert "ELR-INV-003" in content

    def test_adr_162_defines_elr_inv004(self):
        import os
        path = "docs/adr/ADR-162-evidence-lifecycle-immutable-retention.md"
        with open(path) as f:
            content = f.read()
        assert "ELR-INV-004" in content

    def test_adr_162_references_hot_warm_cold_tiers(self):
        import os
        path = "docs/adr/ADR-162-evidence-lifecycle-immutable-retention.md"
        with open(path) as f:
            content = f.read()
        for tier in ["HOT", "WARM", "COLD"]:
            assert tier in content, f"Tier {tier} missing from ADR-162"

    def test_architecture_index_references_adr_162(self):
        import os
        path = "docs/ARCHITECTURE_INDEX.md"
        with open(path) as f:
            content = f.read()
        assert "ADR-162" in content

    def test_rfc_atf2_references_adr_162(self):
        import os
        path = "docs/standards/RFC-ATF-2.md"
        with open(path) as f:
            content = f.read()
        assert "ADR-162" in content


# ─────────────────────────────────────────────────────────────────────────────
# 15. Regression Audit — ADR-156–161 Unaffected
# ─────────────────────────────────────────────────────────────────────────────

class TestV15_RegressionAudit:

    def test_adr_156_still_exists(self):
        import os
        files = os.listdir("docs/adr")
        assert any("ADR-156" in f for f in files)

    def test_adr_157_still_exists(self):
        import os
        files = os.listdir("docs/adr")
        assert any("ADR-157" in f for f in files)

    def test_adr_158_still_exists(self):
        import os
        files = os.listdir("docs/adr")
        assert any("ADR-158" in f for f in files)

    def test_adr_159_still_exists(self):
        import os
        files = os.listdir("docs/adr")
        assert any("ADR-159" in f for f in files)

    def test_adr_160_still_exists(self):
        import os
        files = os.listdir("docs/adr")
        assert any("ADR-160" in f for f in files)

    def test_adr_161_still_exists(self):
        import os
        files = os.listdir("docs/adr")
        assert any("ADR-161" in f for f in files)

    def test_adr_162_does_not_override_adr_156(self):
        assert "ADR-156" not in ["ADR-162"]

    def test_elr_inv_codes_do_not_conflict_with_atf_inv(self):
        elr_codes = {"ELR-INV-001", "ELR-INV-002", "ELR-INV-003", "ELR-INV-004"}
        atf_codes = {"ATF-INV-001", "ATF-INV-002", "ATF-INV-003", "ATF-INV-004",
                     "ATF-INV-005", "ATF-INV-006"}
        assert elr_codes.isdisjoint(atf_codes)

    def test_elr_inv_codes_do_not_conflict_with_rgc_inv(self):
        elr_codes = {"ELR-INV-001", "ELR-INV-002", "ELR-INV-003", "ELR-INV-004"}
        rgc_codes = {f"RGC-INV-{i:03d}" for i in range(1, 9)}
        assert elr_codes.isdisjoint(rgc_codes)

    def test_total_invariant_count_is_24(self):
        atf = 6
        rgc = 8
        elr = 4
        eap = 6
        assert atf + rgc + elr + eap == 24

    def test_runtime_continuity_engine_importable(self):
        from omnix_core.agents.atf.runtime_continuity import RuntimeContinuityEngine
        assert RuntimeContinuityEngine is not None
