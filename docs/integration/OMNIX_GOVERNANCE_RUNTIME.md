# OMNIX Governance Runtime

**Version:** 1.1.0  
**Compliance tier:** ATF-BEV-Compliant (highest)  
**PQC algorithm:** ML-DSA-65 (Dilithium-3, FIPS 204)  
**Issuer:** OMNIX QUANTUM LTD · Harold Nunes · UAE/UK  
**ADR:** [ADR-184](../adr/ADR-184-omnix-governance-runtime.md) · [ADR-185](../adr/ADR-185-ogr-bev-security-hardening.md)  
**Standards:** RFC-ATF-1 · RFC-ATF-2 · RFC-ATF-3 · RFC-ATF-4 · RFC-ATF-5 · RFC-ATF-6  
**Audit status:** Post-audit hardened — 267/267 tests passing

---

## What is the OMNIX Governance Runtime?

The OMNIX Governance Runtime (OGR) is the integration product that puts the full
6-layer Agent Trust Fabric to work for any external AI agent in five API calls.

Most governance tools in the market are horizontal slices: they do continuity
tracking (CLARIXO), empirical behavioral measurement (MTCP), or specification
contracts (VeriSigil). They are isolated instruments.

The OGR is different. It is a vertical stack — every call activates all six
layers simultaneously, producing artifacts that are cryptographically bound to
each other and to the policy receipt that authorized the agent in the first place.

Nothing else on the market does this combination:

| Capability                          | OMNIX OGR | CLARIXO | MTCP | VeriSigil |
|-------------------------------------|:---------:|:-------:|:----:|:---------:|
| Full 6-layer ATF activation         | ✅        | ❌      | ❌   | ❌        |
| Post-quantum cryptography (ML-DSA-65)| ✅       | ❌      | ❌   | ❌        |
| Receipt-bound behavioral attestation | ✅       | ❌      | ❌   | ❌        |
| Per-turn conformance signal (CCS)   | ✅        | ❌      | partial| ❌      |
| Anticipatory veto integration       | ✅        | ❌      | ❌   | ❌        |
| Cross-turn coherence hash chain     | ✅        | ❌      | ❌   | ❌        |
| Offline-verifiable session proof    | ✅        | ❌      | ❌   | ❌        |
| Formal invariants (106 total)       | ✅        | ❌      | ❌   | partial   |
| ATF-BEV-Compliant tier              | ✅        | ❌      | ❌   | ❌        |

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                   OMNIX Governance Runtime (OGR)                   │
│                          /v1/govern/                               │
└────────────────────────┬───────────────────────────────────────────┘
                         │  activates simultaneously
        ┌────────────────┼────────────────────────────────────────┐
        │                │                                        │
        ▼                ▼                                        ▼
  ┌──────────┐   ┌──────────────┐   ┌──────────────────────────────┐
  │  ATF L1  │   │   ATF L2     │   │          ATF L6 — BEV        │
  │ Identity │   │  Delegation  │   │                              │
  │  (AIR)   │   │    (DR)      │   │  BAR  ←  per-turn attestation│
  └──────────┘   └──────────────┘   │  CCS  ←  conformance signal  │
                                    │  CTCHC ← coherence chain     │
        ▼                ▼          └──────────────────────────────┘
  ┌──────────┐   ┌──────────────┐
  │  ATF L3  │   │   ATF L4     │
  │ Temporal │   │  Runtime     │
  │  (TAR)   │   │ Continuity   │
  └──────────┘   └──────────────┘
        ▼
  ┌──────────┐
  │  ATF L5  │
  │Cognitive │
  │Governance│
  └──────────┘

Every artifact at every layer:
  • PQC-signed with ML-DSA-65 (FIPS 204)
  • Bound to the governing receipt (policy trace)
  • Offline-verifiable (no OMNIX callback needed)
```

---

## Session Lifecycle

```
1. POST /v1/govern/session/start
   │
   ├─ Validates governing_receipt_id
   ├─ Activates ATF L1–L6
   ├─ Creates CTCHC genesis block (BEV-INV-010)
   └─ Returns session_id + chain_genesis_hash

        ↓  (for each agent turn)

2. POST /v1/govern/session/{id}/turn
   │
   ├─ Creates BAR (PQC-signed, content-hashed)    ← BEV-INV-001/002
   ├─ Computes CCS (conformance score 0.0–1.0)    ← BEV-INV-005/006
   ├─ Appends CTCHC link                           ← BEV-INV-011
   └─ Returns ogr_verdict + should_halt flag

        ↓  (when session is complete)

3. POST /v1/govern/session/{id}/close
   │
   ├─ Seals CTCHC (covers all links)               ← BEV-INV-013
   ├─ PQC-signs the seal                           ← BEV-INV-014
   └─ Returns session proof summary

        ↓  (retrieve proof for audit/submission)

4. GET /v1/govern/session/{id}/proof
   │
   └─ Full Behavioral Attestation Chain:
      • All BARs
      • CCS trend
      • CTCHC chain + seal
      • Offline verification result

5. GET /v1/govern/compliance/{id}
   └─ ATF-BEV-Compliant report (regulatory/audit)
```

---

## New Artifact Classes (RFC-ATF-6)

### Behavioral Anchor Record (BAR)
A BAR is a PQC-signed attestation of a single agent output turn, cryptographically
bound to the governing receipt that authorized the action.

```json
{
  "bar_id": "BAR-A3F2B1C4D5E6F7A8",
  "session_id": "OGR-9B8A7C6D5E4F3A2B1C0D",
  "agent_id": "AID-finance-001",
  "turn_index": 0,
  "output_hash": "sha3-256:a1b2c3d4...",
  "governing_receipt_id": "RCP-001",
  "constraint_set_hash": "sha3-256:e5f6a7b8...",
  "atf_layer": "BEV-L6",
  "content_hash": "sha3-256:c1d2e3f4...",
  "bar_status": "VALID",
  "halt_reason": null,
  "pqc_signature": "ML-DSA-65:...",
  "pqc_algorithm": "ml-dsa-65",
  "created_at": "2026-05-23T10:00:00Z"
}
```

**Key invariants:**
- `BEV-INV-001`: every governed turn produces a BAR before output is delivered
- `BEV-INV-002`: `content_hash = SHA3-256(output_hash + receipt_id + turn_index)`
- `BEV-INV-004`: BAR is verifiable offline — all inputs are embedded

### Constraint Conformance Signal (CCS)
A CCS is a per-turn measurement of how tightly the agent's output conforms to
the policy constraints defined in the governing receipt.

```json
{
  "ccs_id": "CCS-B2C3D4E5F6A7B8C9",
  "session_id": "OGR-9B8A7C6D5E4F3A2B1C0D",
  "bar_id": "BAR-A3F2B1C4D5E6F7A8",
  "turn_index": 0,
  "conformance_score": 0.9500,
  "drift_delta": 0.0500,
  "cumulative_drift": 0.0500,
  "constraints_evaluated": 4,
  "constraints_violated": 0,
  "violated_constraints": [],
  "verdict": "CONFORMANT",
  "watchdog_triggered": false,
  "chain_link_hash": "sha3-256:f1a2b3c4...",
  "computed_at": "2026-05-23T10:00:00Z"
}
```

**Verdicts:** `CONFORMANT` → `WARNING` → `CRITICAL` → `HALT`

**Key invariants:**
- `BEV-INV-006`: score ∈ [0.0, 1.0]
- `BEV-INV-007`: CRITICAL → AGVP watchdog triggered
- `BEV-INV-008`: cumulative drift > threshold → HALT (default 35%)

### Cross-Turn Coherence Hash Chain (CTCHC)
The CTCHC links every turn of a session into a tamper-evident chain anchored to
the governing receipt. Any modification to any past turn breaks the chain.

```
genesis:  SHA3-256(session_id + receipt_id + "OMNIX-CTCHC-GENESIS")
link[0]:  SHA3-256(genesis || turn_0_hash || receipt_id)
link[1]:  SHA3-256(link[0] || turn_1_hash || receipt_id)
link[n]:  SHA3-256(link[n-1] || turn_n_hash || receipt_id)
seal:     SHA3-256(genesis + all_links + tip_hash)  — PQC-signed
```

**Key invariants:**
- `BEV-INV-011`: `link = H(prev ‖ turn ‖ receipt)`
- `BEV-INV-012`: gaps in turn sequence → verification fails
- `BEV-INV-013`: seal covers complete chain
- `BEV-INV-014`: seal is ML-DSA-65 signed before OEP export

---

## Constraint Set Reference

Define constraints in the `constraint_set` field of `session/start`:

```json
{
  "constraint_set": {
    "max_output_length": 2000,
    "max_turns": 50,
    "halt_on_keywords": ["execute trade", "transfer funds"],
    "warn_on_keywords": ["market speculation"],
    "forbidden_topics": ["personal financial advice"],
    "required_keywords": []
  }
}
```

| Field                | Type         | Effect on BAR status    |
|---------------------|-------------|------------------------|
| `max_output_length`  | int          | VIOLATION if exceeded  |
| `max_turns`          | int          | HALTED at limit        |
| `halt_on_keywords`   | list[str]    | HALTED on match        |
| `warn_on_keywords`   | list[str]    | WARNING on match       |
| `forbidden_topics`   | list[str]    | CCS violation scored   |
| `required_keywords`  | list[str]    | CCS violation if absent|

---

## OGR Verdict Reference

| Verdict      | should_halt | Meaning                                           |
|-------------|:-----------:|---------------------------------------------------|
| `CONFORMANT` | false       | All constraints satisfied, session healthy        |
| `WARNING`    | false       | Soft boundary approached, watchdog monitoring     |
| `CRITICAL`   | false*      | Hard constraint risk, AGVP watchdog triggered     |
| `HALT`       | **true**    | Session must stop. Output MUST NOT be delivered   |

*CRITICAL does not halt autonomously, but should trigger human review.

---

## Compliance Tier: ATF-BEV-Compliant

Every session started via the OGR automatically qualifies for the
**ATF-BEV-Compliant** designation — the sixth and highest tier in the
OMNIX governance hierarchy.

```
ATF-BEV-Compliant     ← OGR (all 6 layers)
ATF-L5-Compliant
ATF-L4-Compliant
ATF-L3-Compliant
ATF-L2-Compliant
ATF-L1-Compliant
```

The compliance report (`GET /v1/govern/compliance/{id}`) documents
per-invariant pass/fail for all 18 BEV invariants (BEV-INV-001–018) plus
OGR-INV-001 and the 6 ATF layer attestations. It is suitable for:
- Regulatory submission (AI Act, DOGE, UAE CRAE)
- Partner due diligence
- Third-party governance audit
- Insurance underwriting evidence

---

## Offline Verification

Every OGR proof is self-contained and offline-verifiable.

To verify a sealed session proof without any OMNIX API access:

```python
import hashlib, json

# Verify a single BAR
canonical = json.dumps({
    "session_id": bar["session_id"],
    "agent_id": bar["agent_id"],
    "turn_index": bar["turn_index"],
    "output_hash": bar["output_hash"],
    "governing_receipt_id": bar["governing_receipt_id"],
    "constraint_set_hash": bar["constraint_set_hash"],
}, sort_keys=True)
assert hashlib.sha3_256(canonical.encode()).hexdigest() == bar["content_hash"]

# Verify CTCHC chain walk
prev = chain["genesis_hash"]
for link in sorted(links, key=lambda x: x["turn_index"]):
    payload = json.dumps({
        "prev": prev,
        "turn": link["turn_hash"],
        "receipt": link["governing_receipt_id"],
    }, sort_keys=True)
    expected = hashlib.sha3_256(payload.encode()).hexdigest()
    assert expected == link["chain_link_hash"]
    prev = link["chain_link_hash"]
```

---

## API Reference Summary

| Method | Endpoint                                | Description                          |
|--------|----------------------------------------|--------------------------------------|
| POST   | `/v1/govern/session/start`             | Initialize governed session          |
| POST   | `/v1/govern/session/{id}/turn`         | Record agent turn (BAR+CCS+CTCHC)   |
| GET    | `/v1/govern/session/{id}/proof`        | Full Behavioral Attestation Chain    |
| POST   | `/v1/govern/session/{id}/close`        | Seal CTCHC + close session           |
| GET    | `/v1/govern/session/{id}/status`       | Live governance status               |
| GET    | `/v1/govern/sessions`                  | List sessions                        |
| POST   | `/v1/govern/verify`                    | Offline artifact verification        |
| GET    | `/v1/govern/compliance/{id}`           | ATF-BEV-Compliant report             |
| GET    | `/v1/govern/manifest`                  | OGR capability manifest              |

---

## Full Invariant Registry — BEV + OGR

The compliance report (`GET /v1/govern/compliance/{id}`) evaluates every invariant
below per-session. All 19 must pass for `overall_pass: true`.

### Behavioral Anchor Record (BAR) — ADR-181

| Invariant    | Description |
|-------------|-------------|
| `BEV-INV-001` | Every governed turn produces a BAR **before** the output is delivered |
| `BEV-INV-002` | `content_hash = SHA3-256(output_hash ‖ receipt_id ‖ turn_index)` |
| `BEV-INV-003` | A HALTED BAR immediately halts the session; session enters forensic state |
| `BEV-INV-004` | Every BAR is verifiable offline — all inputs are embedded in the artifact |
| `BEV-INV-015` | Empty `output_text` → BAR status `VIOLATION` (no silent outputs allowed) |
| `BEV-INV-016` | BAR identifier MUST follow the `BAR-{HEX16}` canonical format |

### Constraint Conformance Signal (CCS) — ADR-182

| Invariant    | Description |
|-------------|-------------|
| `BEV-INV-005` | Every BAR produces a CCS in the same atomic step |
| `BEV-INV-006` | Conformance score ∈ [0.0, 1.0] — never outside this range |
| `BEV-INV-007` | Verdict `CRITICAL` → AGVP watchdog triggered |
| `BEV-INV-008` | Cumulative drift > threshold → verdict `HALT` (default threshold: 35%) |
| `BEV-INV-009` | CCS history is append-only and hash-linked per session |
| `BEV-INV-017` | Drift accumulator is isolated per `session_id` and preserved across process restarts |

### Cross-Turn Coherence Hash Chain (CTCHC) — ADR-183

| Invariant    | Description |
|-------------|-------------|
| `BEV-INV-010` | Chain is initialized (genesis block) before the first BAR is created |
| `BEV-INV-011` | `link[n] = SHA3-256(link[n-1] ‖ turn_hash ‖ receipt_id)` |
| `BEV-INV-012` | Gaps in turn sequence → chain verification fails |
| `BEV-INV-013` | Seal covers the complete chain (all links from genesis to tip) |
| `BEV-INV-014` | Seal is ML-DSA-65 signed before any OEP export |
| `BEV-INV-018` | Every link's `receipt_id` MUST match the chain's governing receipt |

### OGR Orchestrator — ADR-184

| Invariant    | Description |
|-------------|-------------|
| `OGR-INV-001` | A session MUST activate all 6 ATF layers simultaneously — partial activation is not ATF-BEV-Compliant |

---

## Security Hardening Notes

This section documents security properties that were validated during the
post-deployment audit (ADR-185) and are now permanently enforced.

### Cache Coherence Guarantee

> Any code path that mutates persisted state also reflects that mutation in the
> corresponding in-process cache entry.

This is a correctness requirement, not a performance note. Omitting a cache
write-back is a bug that produces stale state (incorrect `session_status`,
`chain_sealed`, `turn_count`) visible to callers between the DB commit and the
next process restart. All three cache write-backs (session cache, chain cache,
links cache) are now enforced after every state-mutating operation.

### No-DB Operation

The full OGR session lifecycle — `session/start` → `session/{id}/turn` (N times)
→ `session/{id}/close` → `session/{id}/proof` — is fully functional without a
`DATABASE_URL`. The CTCHC engine maintains `_chain_cache` and `_links_cache`
in memory; the CCS engine maintains `_drift_cache`; the session cache maintains
`_session_cache`. All caches are write-through: data is written to both memory
and the DB whenever a DB connection is available.

This makes the runtime safe for:
- Automated test suites (no DB setup required)
- Python SDK integration testing
- Sandbox/demo environments
- Short-lived single-process deployments

For production multi-dyno deployments: use `DATABASE_URL`. The in-memory caches
are per-process and do not survive restart or cross-dyno routing.

### Input Validation at API Boundary

All query parameters are validated before reaching the database layer:
- `GET /v1/govern/sessions?status=X` — `X` must be one of `ACTIVE`, `CLOSED`,
  `HALTED`, `EXPIRED`. Invalid values return HTTP 400.
- `POST /v1/govern/verify?artifact_type=X` — `X` must be one of `BAR`, `CTCHC`,
  `SESSION`. CCS is not offline-verifiable; it requires DB access and is
  available through `GET /v1/govern/compliance/{id}` instead.

### Offline Verification Scope

| Artifact | Offline verifiable | Method |
|----------|--------------------|--------|
| BAR      | ✅ Yes              | `SHA3-256(canonical_fields) == content_hash` |
| CTCHC    | ✅ Yes              | Walk the chain: `H(prev ‖ turn ‖ receipt) == link_hash` for each link |
| SESSION  | ✅ Yes              | `OGR-INV-001` check + `chain_sealed` flag |
| CCS      | ❌ No               | Use `GET /v1/govern/compliance/{id}` (DB read) |

---

*OMNIX Governance Runtime v1.1.0 · OMNIX QUANTUM LTD · Harold Nunes · May 2026*  
*ADR-184 (amended by ADR-185) · RFC-ATF-1 through RFC-ATF-6*
 