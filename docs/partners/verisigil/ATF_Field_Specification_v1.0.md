ATF FIELD SPECIFICATION
Agent Trust Fabric — Trace Format & Field Definitions
Version: 1.4 · Date: 2026-05-22
Issued by: Harold Alberto Nunes Rodelo, ATF / OMNIX QUANTUM LTD
For: VeriSigil AI (Raheem Larry Babatunde) — Bridge Validation Collaboration
Status: Day 1 Deliverable — Sandbox / Evaluation Only

---

## Overview

This document defines the complete field specification for the three core ATF
record types used in the TAR↔TAP and RCR↔Survivability bridge validation:

  - DR  — Delegation Receipt (ATFDR-{16HEX})
  - TAR — Temporal Admissibility Record (ATFTAR-{16HEX})
  - RCR — Runtime Continuity Record (ATFRCR-{16HEX})

All records are PQC-signed (Dilithium-3 / ML-DSA-65, FIPS 204).
All content_hash values are SHA-256 hex digests (no prefix).
All timestamps are ISO 8601 UTC unless noted as nanosecond epoch.

---

## 1. Delegation Receipt (DR)

Record ID format: `ATFDR-{16 uppercase hex characters}`
ADR reference: ADR-156

### 1.1 Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `delegation_id` | string | REQUIRED | Unique DR identifier. Format: `ATFDR-{16HEX}` |
| `delegator_id` | string | REQUIRED | AID or human operator ID issuing the delegation |
| `delegate_id` | string | REQUIRED | AID of the receiving (delegated) agent |
| `task_scope` | object | REQUIRED | Dict describing what the delegate is authorized to do. Arbitrary key-value pairs. |
| `authority_budget_delegator` | float | REQUIRED | Authority budget held by delegator at issuance. Range: 0.0–100.0 |
| `authority_budget_granted` | float | REQUIRED | Authority budget granted to delegate. MUST be ≤ `authority_budget_delegator` (ATF-INV-001 / MAR). |
| `parent_delegation_id` | string | OPTIONAL | DR ID of the delegation that gave delegator its authority. Null if delegator is human root. |
| `chain_root_id` | string | REQUIRED | DR ID of the originating human-root delegation in the chain. |
| `delegation_depth` | integer | REQUIRED | Chain depth. 0 = human root, 1 = first agent, N = Nth sub-agent. |
| `delegator_public_key` | string | REQUIRED | Dilithium-3 public key of delegator, base64-encoded. Used for offline DR signature verification. May be empty string `""` when signing key was not available at issuance time — treat empty string as unsigned. |
| `content_hash` | string | REQUIRED | SHA-256 hex digest of all DR fields except `content_hash`, `pqc_signature`, `pqc_algorithm`. Canonical JSON: `json.dumps(fields, sort_keys=True, separators=(",", ":"), default=str)`. Note: `authority_budget_delegator` and `authority_budget_granted` are rounded to 4dp before hashing. |
| `posture_state_hash` | string | CONDITIONAL | SHA-256 of authority posture at exact moment of DR issuance. Present in all DRs issued after ATF v1.0. Null only in legacy pre-v1.0 records. Committed fields: `delegator_id`, `task_scope`, `authority_budget_delegator` (rounded to 4dp), `authority_budget_granted` (rounded to 4dp), `delegation_depth`, `chain_root_id`, `created_at`. Canonical JSON: `json.dumps(fields, sort_keys=True, separators=(",", ":"))`. Enables SPV binding for TAR↔TAP bridge validation. |
| `pqc_signature` | string | CONDITIONAL | Dilithium-3 (ML-DSA-65) signature over `content_hash`, base64-encoded. Present when signing key is available. |
| `pqc_algorithm` | string | CONDITIONAL | Signing algorithm identifier. Value: `"dilithium3"` |
| `expires_at` | string | OPTIONAL | ISO 8601 UTC expiry timestamp. Null = no expiry. |
| `status` | string | REQUIRED | `ACTIVE` \| `EXPIRED` \| `REVOKED` |
| `created_at` | string | REQUIRED | ISO 8601 UTC timestamp of DR issuance. |
| `metadata` | object | REQUIRED | Extension dict. Empty object `{}` if unused. |

### 1.2 Invariants

- ATF-INV-001 (MAR): `authority_budget_granted` ≤ `authority_budget_delegator`. Violation raises hard error before issuance — no DR is created.
- ATF-INV-002: `chain_root_id` traces back to a human-root delegation (`delegation_depth = 0`).
- ATF-INV-003: `posture_state_hash` is computed before `content_hash`. `content_hash` commits to `posture_state_hash`.

### 1.3 Example

```json
{
  "delegation_id": "ATFDR-A1B2C3D4E5F60001",
  "delegator_id": "AID-COMPLIANCE-A1B2C3D4E5F60001",
  "delegate_id": "AID-AUDIT-F1E2D3C4B5A60007",
  "task_scope": {
    "domain": "compliance",
    "permitted_actions": ["read_evidence", "issue_tar"],
    "max_duration_s": 3600
  },
  "authority_budget_delegator": 80.0,
  "authority_budget_granted": 60.0,
  "parent_delegation_id": "ATFDR-ROOT0000000001",
  "chain_root_id": "ATFDR-ROOT0000000001",
  "delegation_depth": 1,
  "delegator_public_key": "<base64-dilithium3-pubkey>",
  "content_hash": "a3f1c2d4e5b6a7f8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
  "posture_state_hash": "28c1dcbd36bae0faf708af58f72d5cc5103974266b3ab47c52cf76c23bcb1095",
  "pqc_signature": "<base64-dilithium3-signature>",
  "pqc_algorithm": "dilithium3",
  "expires_at": "2026-05-22T10:00:00+00:00",
  "status": "ACTIVE",
  "created_at": "2026-05-21T10:00:00+00:00",
  "metadata": {}
}
```

---

## 2. Temporal Admissibility Record (TAR)

Record ID format: `ATFTAR-{16 uppercase hex characters}`
ADR reference: ADR-157

### 2.1 Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `tar_id` | string | REQUIRED | Unique TAR identifier. Format: `ATFTAR-{16HEX}` |
| `delegation_id` | string | REQUIRED | `ATFDR-{16HEX}` of the authorizing Delegation Receipt |
| `agent_id` | string | REQUIRED | AID of the acting agent. Format: `AID-{DOMAIN}-{16HEX}` |
| `execution_ref` | string | OPTIONAL | Reference to Execution Receipt (ADR-131). Null if not linked. |
| `execution_ns` | integer | REQUIRED | Nanosecond Unix timestamp of the execution event being admitted. |
| `execution_ts` | string | REQUIRED | ISO 8601 UTC timestamp of the execution event. |
| `dr_status_at_admission` | string | REQUIRED | Status of the DR at the moment of TAR admission. Value: `ACTIVE` \| `EXPIRED` \| `REVOKED` |
| `dr_expires_at` | string | OPTIONAL | DR expiry timestamp, copied from the DR. |
| `authority_budget` | float | REQUIRED | Authority budget of the DR at admission time. |
| `domain` | string | REQUIRED | Governance domain identifier (e.g. `"compliance"`, `"trading"`, `"medical_ai"`). |
| `task_action` | string | REQUIRED | The specific action being admitted (e.g. `"read_evidence"`, `"issue_receipt"`). |
| `admission_status` | string | REQUIRED | `ADMITTED` \| `REJECTED` |
| `rejection_reason` | string | OPTIONAL | Human-readable reason for rejection. Null if admitted. |
| `content_hash` | string | REQUIRED | SHA-256 hex digest of all TAR fields except `content_hash`, `pqc_signature`, `pqc_algorithm`. Canonical JSON: `json.dumps(fields, sort_keys=True, separators=(",", ":"), default=str)`. |
| `pqc_signature` | string | CONDITIONAL | Dilithium-3 (ML-DSA-65) signature over `content_hash`, base64-encoded. |
| `pqc_algorithm` | string | CONDITIONAL | `"dilithium3"` |
| `chain_root_id` | string | REQUIRED | `chain_root_id` of the authorizing DR. Enables chain-level traceability. |
| `issued_at` | string | REQUIRED | ISO 8601 UTC timestamp of TAR issuance. |
| `metadata` | object | REQUIRED | Extension dict. |

### 2.2 Invariants

- ATF-INV-004: A TAR with `admission_status = ADMITTED` MUST reference a DR with `dr_status_at_admission = ACTIVE`.
- ATF-INV-005: `execution_ns` MUST be ≤ the nanosecond timestamp of `issued_at`.
- TAR-INV-006: DR remaining validity at TAR admission MUST NOT exceed `TAR_MAX_DR_LIFETIME_SECONDS` (86400 s / 24 h). This is a **compiled structural constant** — not configurable by operator or environment variable. Clock skew tolerance: 5 s. DRs with > 24 h remaining at admission time are automatically `REJECTED`. To issue authority beyond 24 h, a fresh DR must be issued, creating a new auditable issuance event.
- TAR is the primary bridge target for TAR↔TAP equivalence mapping. `delegation_id` is the join key.

### 2.3 Example

```json
{
  "tar_id": "ATFTAR-F1E2D3C4B5A60001",
  "delegation_id": "ATFDR-A1B2C3D4E5F60001",
  "agent_id": "AID-AUDIT-F1E2D3C4B5A60007",
  "execution_ref": null,
  "execution_ns": 1748131200000000000,
  "execution_ts": "2026-05-21T10:00:00+00:00",
  "dr_status_at_admission": "ACTIVE",
  "dr_expires_at": "2026-05-22T10:00:00+00:00",
  "authority_budget": 60.0,
  "domain": "compliance",
  "task_action": "read_evidence",
  "admission_status": "ADMITTED",
  "rejection_reason": null,
  "content_hash": "c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
  "pqc_signature": "<base64-dilithium3-signature>",
  "pqc_algorithm": "dilithium3",
  "chain_root_id": "ATFDR-ROOT0000000001",
  "issued_at": "2026-05-21T10:00:01+00:00",
  "metadata": {}
}
```

---

## 3. Runtime Continuity Record (RCR)

Record ID format: `ATFRCR-{16 uppercase hex characters}`
ADR reference: ADR-159

### 3.1 Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `rcr_id` | string | REQUIRED | Unique RCR identifier. Format: `ATFRCR-{16HEX}` |
| `tar_id` | string | REQUIRED | `ATFTAR-{16HEX}` of the admission record this RCR monitors. |
| `delegation_id` | string | REQUIRED | `ATFDR-{16HEX}` of the authorizing DR. |
| `chain_root_id` | string | REQUIRED | Chain root delegation ID. |
| `agent_id` | string | REQUIRED | AID of the running agent. |
| `ces_score` | float | REQUIRED | Continuity Eligibility Score. Range: 0.0–100.0. Formula: `(T×0.30) + (B×0.30) + (D×0.20) + (I×0.20)`. Rounded to 4dp. |
| `continuity_status` | string | REQUIRED | `NOMINAL` (75–100) \| `MONITORING` (50–75) \| `WARNING` (25–50) \| `CRITICAL` (10–25) \| `HALT` (0–10) |
| `ces_temporal` | float | REQUIRED | T component: `(time remaining on DR / total DR lifetime) × 100`. Range: 0.0–100.0. Defaults to 100.0 when DR has no expiry (`dr_expires_at` is null). Rounded to 4dp. |
| `ces_budget` | float | REQUIRED | B component: `(budget remaining / budget at admission) × 100`. Range: 0.0–100.0. Defaults to 100.0 when `budget_at_admission = 0`. Rounded to 4dp. |
| `ces_context` | float | REQUIRED | D component: `100 - context_drift_pct`. Range: 0.0–100.0. Rounded to 4dp. |
| `ces_integrity` | float | REQUIRED | I component: `100 - (active_anomalies × 10)`. Range: 0.0–100.0. Rounded to 4dp. |
| `time_remaining_ns` | integer | OPTIONAL | Remaining DR lifetime in nanoseconds at this snapshot. Null when DR has no expiry (`dr_expires_at` is null). |
| `dr_expires_at` | string | OPTIONAL | ISO 8601 UTC expiry timestamp of the DR. Null if DR has no expiry. |
| `fragmentation_score` | float | REQUIRED | Aggregate budget consumption % across all active sessions sharing the same `chain_root_id`. Formula: `(total_admitted - total_remaining) / total_admitted × 100`. Range: 0.0–100.0 |
| `reauth_challenge_id` | string | OPTIONAL | Reference to ReauthorizationChallenge if issued (`ATFRC-{16HEX}`). Null otherwise. |
| `execution_ns` | integer | REQUIRED | Nanosecond Unix timestamp of the execution event. |
| `execution_ts` | string | REQUIRED | ISO 8601 UTC timestamp of the execution event. |
| `issued_at` | string | REQUIRED | ISO 8601 UTC timestamp of RCR issuance. |
| `budget_at_admission` | float | REQUIRED | Authority budget at the moment of TAR admission. |
| `budget_remaining` | float | REQUIRED | Authority budget remaining at this RCR snapshot. |
| `context_drift_pct` | float | REQUIRED | Context drift percentage at this snapshot. Range: 0.0–100.0 |
| `active_anomalies` | integer | REQUIRED | Count of active governance anomalies at this snapshot. |
| `content_hash` | string | REQUIRED | SHA-256 hex digest of all RCR fields except `content_hash`, `pqc_signature`, `pqc_algorithm`. Canonical JSON: `json.dumps(fields, sort_keys=True, separators=(",", ":"), default=str)`. |
| `pqc_signature` | string | CONDITIONAL | Dilithium-3 (ML-DSA-65) signature over `content_hash`, base64-encoded. |
| `pqc_algorithm` | string | CONDITIONAL | `"dilithium3"` |
| `sample_reason` | string | OPTIONAL | Reason for this RCR snapshot: `SCHEDULED` \| `EXECUTION_COMPLETE` \| `THRESHOLD_BREACH` \| `FRAGMENTATION` \| `EXTERNAL` \| `RC_TTL_EXPIRED`. |
| `escalation_event_id` | string | OPTIONAL | ID of ContinuityEscalationEvent if triggered. Format: `ATFCEE-{16HEX}`. Null otherwise. |
| `predecessor_rcr_id` | string | OPTIONAL | ID of previous RCR in the continuity chain. |
| `metadata` | object | REQUIRED | Extension dict. |

### 3.2 Invariants

- RGC-INV-001: Every RCR MUST be anchored to a valid TAR (`tar_id` must resolve).
- RGC-INV-002: CES MUST be computed from real-time values only — no cached inputs.
- RGC-INV-003: `HALT` tier terminates execution and revokes in-flight sub-tasks.
- RGC-INV-005: All RCRs are PQC-signed and immutable after issuance.
- RGC-INV-006: RCR chain is acyclic — `issued_at` MUST be strictly monotonically increasing per execution session.
- RCR is the bridge target for RCR↔Survivability receipt mapping. Join key: `tar_id`.

### 3.3 Example

```json
{
  "rcr_id": "ATFRCR-D1C2B3A4E5F60001",
  "tar_id": "ATFTAR-F1E2D3C4B5A60001",
  "delegation_id": "ATFDR-A1B2C3D4E5F60001",
  "chain_root_id": "ATFDR-ROOT0000000001",
  "agent_id": "AID-AUDIT-F1E2D3C4B5A60007",
  "ces_score": 92.7,
  "continuity_status": "NOMINAL",
  "ces_temporal": 87.0,
  "ces_budget": 92.0,
  "ces_context": 95.0,
  "ces_integrity": 100.0,
  "execution_ns": 1748131200000000000,
  "execution_ts": "2026-05-21T10:00:00+00:00",
  "issued_at": "2026-05-21T13:07:12+00:00",
  "budget_at_admission": 60.0,
  "budget_remaining": 55.2,
  "context_drift_pct": 5.0,
  "active_anomalies": 0,
  "time_remaining_ns": 75168000000000,
  "dr_expires_at": "2026-05-22T10:00:00+00:00",
  "fragmentation_score": 8.0,
  "reauth_challenge_id": null,
  "content_hash": "d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7",
  "pqc_signature": "<base64-dilithium3-signature>",
  "pqc_algorithm": "dilithium3",
  "sample_reason": "SCHEDULED",
  "escalation_event_id": null,
  "predecessor_rcr_id": null,
  "metadata": {}
}
```

---

## 4. Cross-Record Traceability

The three records form a traceable chain:

```
DR (ATFDR-...)
  └── TAR (ATFTAR-...) — references delegation_id
        └── RCR (ATFRCR-...) — references tar_id + delegation_id
```

Join path for TAR↔TAP bridge:
  `TAR.delegation_id` → `DR.delegation_id` → `DR.posture_state_hash`

Join path for RCR↔Survivability bridge:
  `RCR.tar_id` → `TAR.tar_id` → `TAR.delegation_id` → `DR.chain_root_id`

---

## 5. Signature Verification

Steps 1–3 are identical for all three record types:

1. Recompute `content_hash` from all fields except `content_hash`, `pqc_signature`, `pqc_algorithm`
2. Canonical JSON: `json.dumps(fields, sort_keys=True, separators=(",", ":"), default=str)`
3. SHA-256 hex of UTF-8 encoded canonical JSON

Step 4 differs by record type:

**DR:** Verify Dilithium-3 signature over `content_hash.encode("utf-8")` using `DR.delegator_public_key` (the key is embedded in the DR itself — no external key required).

**TAR and RCR:** Verify Dilithium-3 signature over `content_hash.encode("utf-8")` using the OMNIX platform public key.

OMNIX platform public key (ML-DSA-65 / Dilithium-3, base64):
Shared separately. See integration comms for current value.

---

## 6. Domain Values (Common)

Recognized `domain` values:

| Value | Description |
|---|---|
| `compliance` | ISO 27001 / regulatory compliance |
| `trading` | Autonomous trading governance |
| `medical_ai` | Medical AI recommendation governance |
| `defense_governance` | Defense / national security AI |
| `insurance` | Insurance underwriting AI |
| `real_estate` | Real estate AI decisions |
| `energy_governance` | Energy sector AI |
| `islamic_credit` | Islamic finance credit AI |
| `stablecoin` | Stablecoin / DeFi governance |
| `crisis` | Crisis response AI |
| `autonomous_agent` | General autonomous agent |
| `robotics` | Robotics governance |

---

## 7. Revision History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-05-21 | Initial release — Day 1 deliverable for VeriSigil bridge validation |
| 1.1 | 2026-05-22 | RCR field names corrected to match implementation: ces→ces_score, ces_tier→continuity_status, temporal_health→ces_temporal, budget_health→ces_budget, context_fidelity→ces_context, integrity_score→ces_integrity. Added budget_at_admission, budget_remaining, context_drift_pct, active_anomalies, sample_reason, escalation_event_id, predecessor_rcr_id. |
| 1.2 | 2026-05-22 | CES component ranges corrected: 0.0–1.0 → 0.0–100.0 for ces_temporal, ces_budget, ces_context, ces_integrity. Component formulas corrected (no /100 division). Added missing RCR fields: time_remaining_ns, dr_expires_at, fragmentation_score, reauth_challenge_id. Example JSON values corrected. Fixed RGC-INV-006 reference from issued_at_ns to issued_at. DR signature verification corrected: uses DR.delegator_public_key, not platform key. TAR/RCR use platform key. Canonical JSON updated to include default=str for all three record types. |
| 1.3 | 2026-05-22 | sample_reason values corrected: removed ANOMALY_DETECTED/MANUAL, added THRESHOLD_BREACH/FRAGMENTATION/EXTERNAL/RC_TTL_EXPIRED. fragmentation_score range corrected: 0.0–1.0 → 0.0–100.0, formula documented. Example fragmentation_score corrected: 0.08 → 8.0. posture_state_hash: added float rounding (4dp), canonical JSON format, status changed to CONDITIONAL. ces_score example corrected: 82.5 → 92.7. posture_state_hash example hash replaced with real computed value. DR signature uses delegator_public_key (not platform key); added empty-string note. CES components: documented 4dp rounding and ces_temporal=100.0 default when no expiry. time_remaining_ns corrected to OPTIONAL. escalation_event_id format ATFCEE-{16HEX} added. robotics domain added. canonical JSON updated to include default=str for content_hash in all three record types. |
| 1.4 | 2026-05-22 | TAR-INV-006 added: compiled 24h DR lifetime staleness bound (TAR_MAX_DR_LIFETIME_SECONDS=86400, not configurable). DR example expires_at corrected: 26h → 24h (was violating TAR-INV-006 and would auto-REJECT). All three examples updated to 24h expiry. RCR example time_remaining_ns corrected: 93600000000000 → 75168000000000 (consistent with ces_temporal=87.0 over 24h DR). RCR example issued_at corrected: 10:01:00 → 13:07:12 (consistent with time_remaining_ns). DR example delegator_id corrected to 16-hex format: AID-COMPLIANCE-A1B2C3D4E5F60001. DR example delegate_id corrected to 16-hex format: AID-AUDIT-F1E2D3C4B5A60007. TAR and RCR agent_id aligned with DR delegate_id. posture_state_hash recomputed with corrected delegator_id. TAR and RCR content_hash descriptions updated to include default=str. ces_score documented as rounded to 4dp. |
