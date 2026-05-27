---
name: RCEP Canonicalization Profile
description: Canonicalization separator rules for Route-Complete Evidence Package verifier — which artefacts use SHA-256 vs SHA3-256, compact vs default separators, and the CTCHC genesis continuity approach.
---

# RCEP Canonicalization Profile Registry (ADR-200)

## Rule: Two separator modes co-exist in RCEP v1.0.0

DR and TAR use SHA-256 + compact separators (established in ADR-028/156/157 before RCEP).
All generator-native artefacts (RCR, binding, commit, refusal, outcome, PoGC, source state, BAR) use SHA3-256 + default separators.

This asymmetry is intentional and locked at v1.0.0. Any future verifier must check this registry before changing hash logic.

## Hash canonicalization

| Artefact | Hash | Separators | Excluded fields |
|---|---|---|---|
| Source state | SHA3-256 | default | source_state_hash |
| DR / TAR | SHA-256 | compact | content_hash, pqc_signature, pqc_algorithm |
| RCR / Binding / Commit | SHA3-256 | default | hash field, pqc_signature, pqc_algorithm |
| Refusal / Outcome receipt | SHA3-256 | default | content_hash, pqc_signature, pqc_algorithm |
| BAR content_hash | SHA3-256 | default | canonical 6-field tuple only |
| PoGC | SHA3-256 | default | content_hash, pqc_signature ONLY — pqc_algorithm IS included |

## Signature payload separators

| Artefact | Signing | Separators |
|---|---|---|
| DR / TAR | Sign content_hash.encode() directly (not JSON) | N/A |
| RCR / Binding / Commit | generator _sign_payload | compact |
| BAR | BAREngine (4-field: bar_id, content_hash, governing_receipt_id, created_at) | **default** |
| CTCHC seal | CTCHCEngine (3-field: chain_id, seal_hash, session_id) | **default** |
| PoGC / Refusal / Outcome | generator _sign_payload | compact |

**Why BAR/CTCHC use default:** BAREngine and CTCHCEngine predate RCEP and call json.dumps without separator override. The verifier must use _verify_sig_default for these.

## CTCHC genesis check (cannot re-derive from initialized_at)

initialized_at format varies: Python's isoformat() returns T-separated, but DB round-trip (PostgreSQL TIMESTAMPTZ → Python datetime → str()) returns space-separated. This makes genesis re-derivation unreliable.

**Fix:** verify chain continuity instead:
1. `sealed.governing_receipt_id == governing_receipt_id` (genesis anchors to DR)
2. `links[0].prev_link_hash == sealed.genesis_hash` (chain starts at declared genesis)

This is cryptographically equivalent because seal_hash covers genesis_hash and seal_hash is PQC-signed.

**Why:** Any tampering with genesis_hash would invalidate the Dilithium-3 seal signature. Re-deriving genesis from initialized_at would only add format-fragile logic without additional security.

## PoGC: pqc_algorithm is included in hash

The canonical_fields dict for PoGC includes pqc_algorithm BEFORE hashing. Do NOT exclude it (unlike every other artefact). This binds the algorithm name into the certificate's integrity proof.

## Verified result

52/52 checks PASS, 0 FAIL on both existing and freshly generated packages (2026-05-27).
