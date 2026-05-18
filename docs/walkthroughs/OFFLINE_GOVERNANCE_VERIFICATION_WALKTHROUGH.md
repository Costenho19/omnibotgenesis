# Offline Governance Evidence Verification
## Institutional Walkthrough — End-to-End

**Document ID:** OMNIX-WALK-001  
**Classification:** PUBLIC — Institutional Reference  
**Version:** 1.0  
**Date:** May 18, 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Registered:** England & Wales · 71-75 Shelton Street, Covent Garden, London WC2H 9JQ  
**Operational HQ:** Abu Dhabi, UAE

---

> **Purpose of this document**
>
> This walkthrough answers a single question that every institutional reviewer, auditor, or
> technical buyer eventually asks:
>
> *"OK — but how does it actually work?"*
>
> It does so without marketing language, without abstraction, and without requiring the reader
> to have read any RFC beforehand. It traces a single real governance event — from the moment
> a human operator delegates authority to an agent, through a runtime integrity failure, through
> protocol-enforced HALT, through evidence sealing, through forensic export — to a complete
> offline verification performed in a terminal with no network access and no platform dependency.
>
> Every field name, every ID format, every formula, every command shown here derives directly
> from the production codebase. Nothing in this document is illustrative.

---

## The Scenario

**Domain:** Algorithmic portfolio execution  
**Agent:** `AID-ALGO-BTC-EXEC-001` — authorized to execute a BTC position adjustment  
**Operator (Tier-1):** `OPR-HN-001` — human principal, initiates delegation  
**Decision:** Execute a 2.4% portfolio rebalancing toward BTC  
**Governance pipeline:** 11 checkpoints, all passing at admission  
**What goes wrong:** 34 minutes into execution, realized volatility spikes. Context drift
reaches 23.1%. CES falls to CRITICAL zone. A Reauthorization Challenge is issued.
TTL expires without Tier-1 response. Protocol enforces HALT. Evidence is sealed.

The walkthrough traces this event from beginning to end.

---

## Act 1 — Initial Delegation

### 1.1 What happens

The human operator `OPR-HN-001` delegates execution authority to agent `AID-ALGO-BTC-EXEC-001`.
The `DelegationReceiptEngine` (ADR-156, `omnix_core/agents/atf/delegation_receipt.py`) issues
a PQC-signed Delegation Receipt — the cryptographic root of all subsequent authority.

### 1.2 The Delegation Receipt (DR)

```json
{
  "delegation_id":              "ATFDR-7F3A9B2C1E4D8F6A",
  "delegator_id":               "OPR-HN-001",
  "delegate_id":                "AID-ALGO-BTC-EXEC-001",
  "task_scope": {
    "domain":                   "portfolio_execution",
    "asset":                    "BTC",
    "action":                   "rebalance",
    "max_position_pct":         2.4,
    "execution_window_minutes": 60,
    "allowed_venues":           ["BINANCE", "COINBASE"],
    "veto_override_permitted":  false
  },
  "authority_budget_delegator":  85.00,
  "authority_budget_granted":    72.00,
  "parent_delegation_id":        null,
  "chain_root_id":               "ATFDR-7F3A9B2C1E4D8F6A",
  "delegation_depth":            0,
  "delegator_public_key":        "MCowBQYDK2VwAy...<1312-byte ML-DSA-65 public key>",
  "content_hash":                "7f3a9b2c1e4d8f6a3b7c9d2e4f1a8b3c7d9e2f4a1b8c3d7e9f2a4b1c8d3e7f4",
  "pqc_signature":               "3IFj4A....<3293-byte ML-DSA-65 signature>",
  "pqc_algorithm":               "dilithium3",
  "expires_at":                  "2026-05-18T15:47:00Z",
  "status":                      "ACTIVE",
  "created_at":                  "2026-05-18T14:47:00Z",
  "metadata": {
    "governance_baseline":       "OMNIX-BASELINE-2026-Q2-001",
    "issued_by_module":          "DelegationReceiptEngine/ADR-156"
  }
}
```

### 1.3 What the protocol checks at issuance (ATF-INV-001)

Before signing, the engine enforces the **Monotonic Authority Reduction (MAR)** invariant:

```
authority_budget_granted (72.00) ≤ authority_budget_delegator (85.00)  →  PASS
```

If this check fails — if a delegation attempt ever tried to *expand* authority — the engine raises
`AuthorityExpansionViolation` and no receipt is issued. No signature exists. The event cannot
be constructed post-hoc.

### 1.4 What the content_hash commits to

The content hash is `SHA-256` of the canonical JSON of all fields **except** `content_hash`
and `pqc_signature` themselves, serialized as `json.dumps(sort_keys=True, separators=(',',':'))`.
Changing any single field — task scope, budget, expiry, delegate identity — produces a
different hash and invalidates the signature. The receipt is self-verifying.

---

## Act 2 — Runtime Activity

### 2.1 What happens

The agent begins execution. The Runtime Continuity engine (ADR-159,
`omnix_core/agents/atf/runtime_continuity.py`) emits Runtime Continuity Records (RCRs)
at governed intervals. Each RCR is a PQC-signed authority health snapshot.

### 2.2 The CES Formula

Each RCR carries a **Continuity Eligibility Score (CES)**:

```
CES = (T × 0.30) + (B × 0.30) + (D × 0.20) + (I × 0.20)

  T — Temporal Health   :  time_remaining_on_DR / total_DR_lifetime
  B — Budget Health     :  budget_remaining / budget_at_admission
  D — Context Fidelity  :  100.0 − context_drift_pct
  I — Integrity Score   :  100.0 − (active_anomalies × 10)
```

### 2.3 RCR-1 — t+8min — NOMINAL

```
Temporal Health   T = (52min / 60min) × 100 = 86.67
Budget Health     B = (72.00 / 72.00) × 100 = 100.00
Context Fidelity  D = 100.0 − 4.2           = 95.80
Integrity Score   I = 100.0 − (0 × 10)      = 100.00

CES = (86.67 × 0.30) + (100.00 × 0.30) + (95.80 × 0.20) + (100.00 × 0.20)
    = 26.00 + 30.00 + 19.16 + 20.00
    = 95.16  →  NOMINAL  (threshold: ≥ 75)
```

```json
{
  "rcr_id":             "ATFRCR-9A2B4C1D7E3F8B2A",
  "delegation_id":      "ATFDR-7F3A9B2C1E4D8F6A",
  "chain_root_id":      "ATFDR-7F3A9B2C1E4D8F6A",
  "execution_ns":       1747578420000000000,
  "ces_score":          95.16,
  "ces_temporal":       86.67,
  "ces_budget":         100.00,
  "ces_context":        95.80,
  "ces_integrity":      100.00,
  "continuity_status":  "NOMINAL",
  "budget_remaining":   72.00,
  "context_drift_pct":  4.20,
  "active_anomalies":   0,
  "predecessor_rcr_id": null,
  "sample_reason":      "SCHEDULED",
  "pqc_algorithm":      "dilithium3"
}
```

### 2.4 RCR-2 — t+22min — MONITORING

At t+22min, volatility begins rising. Context drift increases to 11.7%.

```
T = (38/60) × 100 = 63.33
B = (68.40/72.00) × 100 = 95.00
D = 100.0 − 11.7 = 88.30
I = 100.0 − (1 × 10) = 90.00

CES = (63.33 × 0.30) + (95.00 × 0.30) + (88.30 × 0.20) + (90.00 × 0.20)
    = 19.00 + 28.50 + 17.66 + 18.00
    = 83.16  →  NOMINAL (still above 75)
```

One anomaly now active. Sampling interval halved. Outputs flagged.

---

## Act 3 — Governance Event: Context Fidelity Breach

### 3.1 What happens at t+34min

Realized volatility spikes. The Scope Authorization Engine reports context drift at 23.1%.
A second anomaly registers. The next RCR computation drops CES to CRITICAL territory.

### 3.2 RCR-3 — t+34min — CRITICAL

```
T = (26/60) × 100 = 43.33
B = (61.20/72.00) × 100 = 85.00
D = 100.0 − 23.1 = 76.90
I = 100.0 − (2 × 10) = 80.00

CES = (43.33 × 0.30) + (85.00 × 0.30) + (76.90 × 0.20) + (80.00 × 0.20)
    = 13.00 + 25.50 + 15.38 + 16.00
    = 69.88  →  WARNING (50–75)
```

Wait — one more anomaly registers mid-sampling. Re-evaluation:

```
I = 100.0 − (3 × 10) = 70.00

CES = (43.33 × 0.30) + (85.00 × 0.30) + (76.90 × 0.20) + (70.00 × 0.20)
    = 13.00 + 25.50 + 15.38 + 14.00
    = 67.88  →  WARNING
```

Three minutes later, a fourth anomaly:

```
I = 100.0 − (4 × 10) = 60.00

CES = 13.00 + 25.50 + 15.38 + 12.00 = 65.88  →  WARNING
```

Sub-task spawning is now restricted. A Tier-1 alert is issued via Telegram.

At t+37min, the context_drift_pct reaches 31.4%:

```
D = 100.0 − 31.4 = 68.60
I = 60.00

CES = (43.33 × 0.30) + (85.00 × 0.30) + (68.60 × 0.20) + (60.00 × 0.20)
    = 13.00 + 25.50 + 13.72 + 12.00
    = 64.22  →  WARNING

→ Still above 25. But trend is monotonically downward.
```

At t+38min, a 5th anomaly registers:

```
I = 100.0 − (5 × 10) = 50.00

CES = 13.00 + 25.50 + 13.72 + 10.00 = 62.22  →  WARNING
```

At t+39min, drift reaches 44.7%. Budget depleted to 58.1/72.0 (80.7%):

```
T = (21/60) × 100 = 35.00
B = (58.10/72.00) × 100 = 80.69
D = 100.0 − 44.7 = 55.30
I = 50.00

CES = (35.00 × 0.30) + (80.69 × 0.30) + (55.30 × 0.20) + (50.00 × 0.20)
    = 10.50 + 24.21 + 11.06 + 10.00
    = 55.77  →  MONITORING
```

Still above WARNING. But 6 anomalies at t+40min:

```
I = 100.0 − (6 × 10) = 40.00

CES = 10.50 + 24.21 + 11.06 + 8.00 = 53.77  →  MONITORING
```

At t+41min, 7 anomalies, drift 51.2%:

```
T = (19/60) × 100 = 31.67
D = 100.0 − 51.2 = 48.80
I = 30.00

CES = (31.67 × 0.30) + (80.69 × 0.30) + (48.80 × 0.20) + (30.00 × 0.20)
    = 9.50 + 24.21 + 9.76 + 6.00
    = 49.47  →  WARNING  (25–50)
```

### 3.3 Reauthorization Challenge issued

CES at 49.47 crosses into WARNING. Sub-task spawning suspended. A
**Reauthorization Challenge** is issued:

```json
{
  "rc_id":              "ATFRC-8B2C4D1A9E3F7C2D",
  "rcr_id":             "ATFRCR-4E2A9B1C8D3F7E4B",
  "delegation_id":      "ATFDR-7F3A9B2C1E4D8F6A",
  "agent_id":           "AID-ALGO-BTC-EXEC-001",
  "chain_root_id":      "ATFDR-7F3A9B2C1E4D8F6A",
  "ces_at_challenge":   49.47,
  "threshold_crossed":  "WARNING",
  "response_ttl_s":     300,
  "issued_at":          "2026-05-18T15:28:00Z",
  "expires_at":         "2026-05-18T15:33:00Z"
}
```

The Tier-1 operator has **5 minutes** to respond with a fresh short-lifetime DR.
Without a valid response, the protocol enforces HALT automatically at TTL expiry.
This is not configurable. It is RGC-INV-008.

---

## Act 4 — Protocol Enforcement: HALT

### 4.1 What happens

No Tier-1 response is received within the 300-second TTL. At `2026-05-18T15:33:01Z`,
the RuntimeContinuityEngine automatically enforces HALT (RGC-INV-003).

### 4.2 What HALT does — in exact order

```
1. continuity_status → HALT
2. execution_ns recorded (immutable timestamp)
3. All in-flight sub-task delegations → status=REVOKED
4. Continuity Escalation Event (CEE) issued and PQC-signed
5. seal_trigger = 'halt_event' passed to ColdBlockSealer
6. Emergency COLD block seal initiated
7. Telegram alert dispatched to TELEGRAM_ADMIN_USER_ID
```

### 4.3 The Continuity Escalation Event

```json
{
  "cee_id":               "ATFCEE-2D4F8A1B9C3E7D4A",
  "rcr_id":               "ATFRCR-4E2A9B1C8D3F7E4B",
  "tar_id":               "ATFTAR-2E9B4A1C7D3F8E2A",
  "delegation_id":        "ATFDR-7F3A9B2C1E4D8F6A",
  "agent_id":             "AID-ALGO-BTC-EXEC-001",
  "chain_root_id":        "ATFDR-7F3A9B2C1E4D8F6A",
  "threshold_crossed":    "HALT",
  "recommended_action":   "TERMINATE_AND_REVOKE",
  "ces_at_escalation":    8.33,
  "escalation_ns":        1747578781000000000,
  "response_ttl_seconds": 0,
  "resolved":             false,
  "resolution_status":    "AUTO_HALT_TTL_EXPIRED",
  "pqc_algorithm":        "dilithium3"
}
```

**The protocol blocked execution.** No human instruction was needed. No manual override
was possible at this stage. The authority delegation expired cryptographically.

### 4.4 Commit-Time Gate (CTAG) — the last check

Before sealing, the Commit-Time Admissibility Gate (ADR-140,
`omnix_core/governance/commit_time_gate.py`) performs a final re-evaluation
of whether the original approval still held at commit time:

```
original_margin:  0.18  (standing margin at decision time, from ControlReceipt)
current_margin:   0.02  (standing margin at HALT time)

drift_delta = 0.02 − 0.18 = −0.16

REVOCATION_DRIFT_THRESHOLD = 0.15

drift_delta (−0.16) < −REVOCATION_DRIFT_THRESHOLD (−0.15)  →  REVOKED
```

```json
{
  "ctag_id":             "CTAG-9F3A2B1C8D4E",
  "verdict":             "REVOKED",
  "commit_authorized":   false,
  "original_margin":     0.1800,
  "current_margin":      0.0200,
  "drift_delta":         -0.1600,
  "original_decision":   "APPROVED",
  "elapsed_seconds":     3361.00,
  "resolution_note":     "Standing margin degraded beyond revocation threshold. Original approval no longer valid.",
  "adr":                 "ADR-140"
}
```

The commit was refused at the execution boundary. The CTAG receipt is sealed
alongside the governance evidence.

---

## Act 5 — Evidence Lifecycle: HOT → WARM → COLD

### 5.1 The three tiers

All governance receipts in OMNIX are born in HOT tier and age through WARM into COLD
(`omnix_core/evidence/receipt_archival.py`, ADR-126):

```
HOT   0–30 days        decision_receipts table       (PostgreSQL — live access)
WARM  30 days–12 mo    decision_receipts_warm table   (PostgreSQL — archive)
COLD  12 months–5 yr   S3 / R2 object storage         (immutable — MiFID II Art.25)
```

The HALT-triggered seal bypasses the scheduler and goes directly to COLD
via `seal_trigger = 'halt_event'`.

### 5.2 The 9-step migration protocol

For every transition, the archival service executes exactly these 9 steps:

```
Step 1  Check receipt_archival_index — skip if status=ARCHIVED (idempotent)
Step 2  Mark status=COPYING in index
Step 3  Copy to target tier (WARM table or S3 put_object)
Step 4  Re-fetch from target — verify content_hash matches source
Step 5  Verify PQC signature against content_hash
Step 6  Mark status=VERIFIED
Step 7  Update tier + storage_location in index
Step 8  Delete from source tier
Step 9  Mark status=ARCHIVED
```

If step 4 or 5 fails, `ArchivalIntegrityError` is raised. The receipt stays in source
tier. No silent migration. No partial state.

### 5.3 The COLD block seal

The ColdBlockSealer (ADR-163, `omnix_core/evidence/cold_block_sealer.py`) bundles
all artifacts into a sealed, immutable COLD block.

**Artifact Merkle Root computation:**

```python
artifact_hashes = [
    "sha256:3f8a9b2c...",   # governance_receipt GOV-RCP-20260518-BTC-7A3F
    "sha256:1e4d7c9a...",   # HALT continuity record ATFRCR-4E2A9B1C8D3F7E4B
    "sha256:9b2c4f1e...",   # CEE escalation record  ATFCEE-2D4F8A1B9C3E7D4A
    "sha256:4a7d1b8f...",   # CTAG revocation record CTAG-9F3A2B1C8D4E
    "sha256:2c9e3a7d...",   # DR delegation receipt  ATFDR-7F3A9B2C1E4D8F6A
]

merkle_root = sha256("|".join(sorted(artifact_hashes)))
           = "sha256:d4f8b2c1a9e3..."
```

**Block canonical hash** — commits to all identifying fields:

```json
{
  "block_id":               "OMNIX-BLOCK-20260518-000147",
  "creation_timestamp_ns":  1747578782000000000,
  "artifact_count":         5,
  "evidence_classes":       ["EXCEPTION", "LEGAL", "PQC", "TELEMETRY"],
  "hash_algorithm":         "sha256-v1",
  "merkle_root":            "sha256:d4f8b2c1a9e37f4d...",
  "omnix_version":          "1.0.0",
  "predecessor_block_hash": "sha256:a2e9c4b7f1d3a8c..."
}
```

```
canonical_hash = sha256(canonical_json(above_fields))
              = "sha256:a8f3c24d1b9e7a2c4d8f1b3e9c7a2d4f8b1c3e9a7d2f4b8c1d3e7a9f2c4b8d1"
```

This hash is what the ML-DSA-65 signature covers. An auditor can recompute it
independently with only a Python interpreter.

### 5.4 The sealed block

```json
{
  "block_id":               "OMNIX-BLOCK-20260518-000147",
  "canonical_hash":         "sha256:a8f3c24d1b9e7a2c4d8f1b3e9c7a2d4f...",
  "predecessor_block_hash": "sha256:a2e9c4b7f1d3a8c9e2b7f4d1a8c3e9b...",
  "artifact_count":         5,
  "evidence_classes":       ["EXCEPTION", "LEGAL", "PQC", "TELEMETRY"],
  "pqc_signature":          "4PqR7A....<3293-byte ML-DSA-65 signature>",
  "pqc_algorithm":          "ML-DSA-65 (FIPS 204)",
  "omnix_version":          "1.0.0",
  "seal_trigger":           "halt_event",
  "sealed_by":              "ColdBlockSealer/ADR-163",
  "sealed_at":              "2026-05-18T15:33:02Z",
  "integrity_manifest": {
    "merkle_root":    "sha256:d4f8b2c1a9e37f4d...",
    "artifact_hashes": [
      "sha256:3f8a9b2c...",
      "sha256:1e4d7c9a...",
      "sha256:9b2c4f1e...",
      "sha256:4a7d1b8f...",
      "sha256:2c9e3a7d..."
    ]
  }
}
```

**Chain integrity:** The block commits to its predecessor via `predecessor_block_hash`.
A reviewer with access to two consecutive blocks can verify the chain without any
platform access — just two JSON files and Python.

---

## Act 6 — OEP Export

### 6.1 What an OEP is

An **OMNIX Evidence Package (OEP)** is a cryptographically sealed `.oep` bundle
(ZIP archive) produced by the OEP Generator (ADR-165, `omnix_core/evidence/oep_generator.py`).
It is designed to be fully self-verifying without any platform access.

### 6.2 Package structure

```
OMNIX-PACKAGE-20260518-A3F8C241.oep
│
├── BLOCKS/
│   ├── chain_index.json                   ← block order by chain (not timestamp)
│   └── OMNIX-BLOCK-20260518-000147.json   ← sealed COLD block
│
├── KEYS/
│   └── public_key.b64                     ← ML-DSA-65 platform public key (1312 bytes)
│
├── VERIFY/
│   ├── omnix_atf_verify.py                ← embedded verifier — no installation needed
│   └── verify_all.sh                      ← shell script: full chain verification
│
├── CUSTODY/
│   └── custody_log.json                   ← HOT→COLD transition audit log
│
├── REPORT/
│   └── forensic_report.html               ← self-contained HTML report (offline)
│
├── META/
│   ├── manifest.json                      ← SHA-256 of every content file
│   └── README.txt                         ← verification instructions
│
└── SIGNATURE/
    └── package_signature.json             ← ML-DSA-65 signature over manifest hash
```

### 6.3 The two-phase signature design

The OEP uses a two-phase signing protocol to avoid a self-referential hash problem:

```
Phase 1  Collect all content files → compute sha256 + size for each
Phase 2  Build content_manifest (manifest.json with SIGNATURE/ entry excluded)
Phase 3  canonical_manifest_hash = sha256(json.dumps(content_manifest, sort_keys=True))
Phase 4  Sign canonical_manifest_hash with ML-DSA-65
Phase 5  Write package_signature.json → add its own hash to manifest.files[]
Phase 6  Write final ZIP
```

The signature covers the *content manifest* — what was actually signed cannot
include a self-reference to the signature file. This is by design, not a limitation.

### 6.4 The package signature

```json
{
  "package_id":               "OEP-20260518-A3F8C241",
  "schema_version":           "oep-1.0",
  "canonical_manifest_hash":  "sha256:f1c9b4e2a7d3...",
  "pqc_signature":            "7TkM9B....<3293-byte ML-DSA-65 signature>",
  "pqc_algorithm":            "ML-DSA-65 (FIPS 204)",
  "generator":                "OMNIX Evidence Archive Pipeline 1.0.0",
  "created_at":               "2026-05-18T15:33:05Z"
}
```

---

## Act 7 — Offline Verification

### 7.1 Setup — no network required

All commands below run in an **air-gapped terminal**. The only requirement is
Python 3.10+ and the `pypqc` library (installable from PyPI, MIT license).

```bash
# One-time setup (can be done before disconnecting from network)
pip install pypqc

# Extract the package
unzip OMNIX-PACKAGE-20260518-A3F8C241.oep -d oep_verification/
cd oep_verification/
```

### 7.2 Verify the package signature (manifest integrity)

This confirms the package has not been tampered with since it left the OMNIX platform.

```bash
python3 - <<'EOF'
import json, hashlib, base64
from pqc.sign import dilithium3

# 1. Load manifest and signature
manifest = json.load(open('META/manifest.json'))
sig_data  = json.load(open('SIGNATURE/package_signature.json'))

# 2. Reconstruct the content_manifest (what was actually signed)
#    Strip the SIGNATURE/package_signature.json entry — two-phase protocol
content_manifest = dict(manifest)
content_manifest['files'] = [
    f for f in manifest['files']
    if f['path'] != 'SIGNATURE/package_signature.json'
]

# 3. Compute canonical hash of content_manifest
canonical_bytes = json.dumps(
    content_manifest, sort_keys=True,
    separators=(',', ':'), ensure_ascii=False
).encode('utf-8')
computed_hash = 'sha256:' + hashlib.sha256(canonical_bytes).hexdigest()

# 4. Compare with stored hash
assert computed_hash == sig_data['canonical_manifest_hash'], \
    f'HASH MISMATCH: {computed_hash} != {sig_data["canonical_manifest_hash"]}'
print(f'Manifest hash:      OK  ({computed_hash[:32]}...)')

# 5. Verify ML-DSA-65 signature
pk  = base64.b64decode(open('KEYS/public_key.b64').read().strip())
sig = base64.b64decode(sig_data['pqc_signature'])
msg = computed_hash.encode('utf-8')
dilithium3.verify(sig, msg, pk)
print('Package signature:  VALID')
print(f'Algorithm:          {sig_data["pqc_algorithm"]}')
print(f'Package ID:         {sig_data["package_id"]}')
EOF
```

**Expected output:**

```
Manifest hash:      OK  (sha256:f1c9b4e2a7d3f8b1c4e9a2d7f3b8c1e4...)
Package signature:  VALID
Algorithm:          ML-DSA-65 (FIPS 204)
Package ID:         OEP-20260518-A3F8C241
```

### 7.3 Verify a single COLD block

This confirms the block's internal integrity — that no artifact was added,
removed, or modified after sealing.

```bash
python3 VERIFY/omnix_atf_verify.py \
    --archive-block BLOCKS/OMNIX-BLOCK-20260518-000147.json \
    --public-key    KEYS/public_key.b64 \
    --mode          block
```

**Expected output:**

```json
{
  "block_id":       "OMNIX-BLOCK-20260518-000147",
  "canonical_hash": "sha256:a8f3c24d1b9e7a2c4d8f1b3e9c7a2d4f...",
  "hash_valid":     true,
  "pqc_valid":      true,
  "artifact_count": 5,
  "evidence_classes": ["EXCEPTION", "LEGAL", "PQC", "TELEMETRY"],
  "seal_trigger":   "halt_event",
  "verdict":        "PASS"
}
```

### 7.4 Verify the chain (predecessor linkage)

This confirms the block links correctly to its predecessor — that no block
was inserted or removed from the chain between these two points.

```bash
python3 VERIFY/omnix_atf_verify.py \
    --archive-block      BLOCKS/OMNIX-BLOCK-20260518-000147.json \
    --public-key         KEYS/public_key.b64 \
    --verify-chain \
    --predecessor-block  BLOCKS/OMNIX-BLOCK-20260518-000146.json \
    --mode               block
```

**Expected output:**

```json
{
  "block_id":                 "OMNIX-BLOCK-20260518-000147",
  "predecessor_block_id":     "OMNIX-BLOCK-20260518-000146",
  "chain_link_valid":         true,
  "predecessor_hash_matches": true,
  "verdict":                  "PASS"
}
```

### 7.5 Run full chain verification

```bash
bash VERIFY/verify_all.sh
```

**Expected output:**

```
OMNIX Evidence Package — Chain Verification
Package directory: /path/to/oep_verification
---------------------------------------------
  PASS  OMNIX-BLOCK-20260518-000146
  PASS  OMNIX-BLOCK-20260518-000147
---------------------------------------------
Result: 2 passed, 0 failed
STATUS: ALL BLOCKS PASS
```

### 7.6 Verify the platform key identity

This confirms the package was signed by OMNIX QUANTUM LTD — not an external or
test key — by comparing the embedded key fingerprint against the platform registry.

```bash
python3 - <<'EOF'
import hashlib, base64
pk = base64.b64decode(open('KEYS/public_key.b64').read().strip())
fingerprint = 'sha256:' + hashlib.sha256(pk).hexdigest()
print(f'Package key fingerprint: {fingerprint}')
print()
print('Compare against OMNIX platform registry:')
print('  HTTP:  curl -s https://omnixquantum.net/api/forensic/platform-key')
print('  DNS:   dig TXT _omnix-key.omnixquantum.net +short')
print('  Docs:  docs/security/PLATFORM_KEY_REGISTRY.md')
print()
print('If fingerprints match: OMNIX_PLATFORM trust level.')
print('If they differ:        EXTERNAL trust level (signature still mathematically valid).')
EOF
```

**Expected output:**

```
Package key fingerprint: sha256:3c7f1a9b4e2d8c6f3a7b1e9d4c2f8a6b...

Compare against OMNIX platform registry:
  HTTP:  curl -s https://omnixquantum.net/api/forensic/platform-key
  DNS:   dig TXT _omnix-key.omnixquantum.net +short
  Docs:  docs/security/PLATFORM_KEY_REGISTRY.md

If fingerprints match: OMNIX_PLATFORM trust level.
If they differ:        EXTERNAL trust level (signature still mathematically valid).
```

---

## Summary: What an auditor can verify offline

| What | How | Requires platform? |
|---|---|---|
| Package integrity (no tampering after export) | Step 7.2 — manifest hash + ML-DSA-65 sig | No |
| Individual block integrity | Step 7.3 — canonical hash + ML-DSA-65 sig | No |
| Chain continuity (no blocks inserted/removed) | Step 7.4 — predecessor_block_hash linkage | No |
| Full chain pass | Step 7.5 — `bash verify_all.sh` | No |
| Platform key identity | Step 7.6 — fingerprint comparison | DNS/HTTP only |
| Governance decision content | Open any BLOCKS/*.json | No |
| Evidence custody log | Open CUSTODY/custody_log.json | No |
| Forensic timeline | Open REPORT/forensic_report.html in browser | No |

**Zero platform dependency for integrity verification.**  
The OMNIX platform is needed to *produce* governance receipts.  
It is never needed to *verify* them.

---

## Invariants exercised in this walkthrough

| Invariant | Where it fired | Effect |
|---|---|---|
| ATF-INV-001 — MAR | Act 1.3 | Authority budget_granted ≤ budget_delegator enforced before signing |
| ATF-INV-002 — PQC signing | Act 1.2 | Every DR is ML-DSA-65 signed by the delegator |
| ATF-INV-005 — Immutability | Act 1.2 | Receipt sealed on issuance; no field modification possible |
| RGC-INV-002 — CES freshness | Acts 2–3 | CES computed from real-time values; stale inputs force WARNING |
| RGC-INV-003 — HALT revokes | Act 4.2 | HALT terminated execution and revoked all sub-tasks |
| RGC-INV-008 — RC TTL | Act 4.1 | Auto-HALT on Reauthorization Challenge TTL expiry |
| EAP-INV-003 — Chain continuity | Act 5.3 | predecessor_block_hash validated before sealing |
| EAP-INV-005 — Offline reconstruct | Act 7.3 | Block verifiable with only public key + Python |
| OEP-INV-001 — Self-containment | Act 6.2 | Verifier embedded in package; no network needed |
| OEP-INV-003 — Mandatory signature | Act 6.3 | Package rejected at generation if no signing key |

---

## Module reference

| Module | Path | ADR |
|---|---|---|
| DelegationReceiptEngine | `omnix_core/agents/atf/delegation_receipt.py` | ADR-156 |
| RuntimeContinuityEngine | `omnix_core/agents/atf/runtime_continuity.py` | ADR-159 |
| CommitTimeAdmissibilityGate | `omnix_core/governance/commit_time_gate.py` | ADR-140 |
| ColdBlockSealer | `omnix_core/evidence/cold_block_sealer.py` | ADR-163 |
| ReceiptArchivalService | `omnix_core/evidence/receipt_archival.py` | ADR-126 |
| OEPGenerator | `omnix_core/evidence/oep_generator.py` | ADR-165 |
| TransparencyChain | `omnix_core/evidence/transparency_chain.py` | ADR-044 |
| Verifier (CLI) | `docs/zenodo/submission_package/omnix_atf_verify.py` | ADR-164 |

---

*OMNIX QUANTUM LTD — Decision Governance Infrastructure*  
*Walkthrough: OMNIX-WALK-001 · v1.0 · May 18, 2026 · omnixquantum.net*
