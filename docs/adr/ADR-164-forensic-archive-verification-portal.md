# ADR-164: Forensic Archive Verification Portal

**Status:** Accepted  
**Date:** May 15, 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Supersedes:** None  
**Extends:** ADR-163 (Immutable Evidence Archive Pipeline)  
**Related:** ADR-156 (ATF Public Verifier CLI) · ADR-162 (Evidence Lifecycle) · ADR-165 (OEP Format) ·
            RFC-ATF-1 §7.6 (ATF-INV-006) · EAP-INV-005 (Offline Reconstructability)

---

## Context

ADR-163 established the COLD block archive pipeline and extended `omnix_atf_verify.py` (v1.1.0)
with `--archive-block` verification mode. The result is a fully functional CLI verifier that any
auditor can run locally to verify OMNIX evidence blocks.

The gap: enterprise auditors, regulators, and institutional partners do not run Python CLIs.
They open URLs. The protocol capability is real; the *access surface* is wrong.

The architecture has crossed into forensic-grade territory. The tooling must match.

### What exists today

```
omnix_atf_verify.py v1.1.0
  --archive-block BLOCK.json
  --public-key key.b64
  --verify-chain
  --predecessor-block PREV.json
  → stdout: PASS / INTEGRITY_VIOLATION / CHAIN_BREAK / SIGNATURE_INVALID
```

This is powerful. But it requires:
- Python 3.10+ installed
- `pqc` library (`pip install pypqc`)
- Command-line familiarity
- Local file access

None of these are available at a regulatory presentation or a real-time audit review.

### The required shift

```
BEFORE:  auditor clones repo, installs Python, runs CLI, reads stdout
AFTER:   auditor opens URL, drops block files, sees forensic visualization
```

The shift is not cosmetic. The trust model changes:

> A CLI verifier that runs on OMNIX infrastructure proves nothing independently.
> A browser-side verifier that executes cryptographic verification *locally, in the auditor's
> own browser, without any network call* — that changes the trust relationship fundamentally.

The browser is the auditor's machine. If hash verification and chain integrity checks run there,
OMNIX cannot influence the outcome. That is the institutional-grade proof surface.

---

## Decision

### 1. Two-Plane Verification Architecture

The portal implements verification across two planes with explicit trust hierarchy:

```
┌─────────────────────────────────────────────────────────────────┐
│  PLANE 1: Browser (Local — Auditor Machine)                     │
│                                                                  │
│  SHA-256 merkle recompute     ← SubtleCrypto (native browser)   │
│  Canonical hash recompute     ← deterministic JS (no libs)      │
│  Chain link verification      ← predecessor_block_hash match    │
│  Evidence class checks        ← pure JS                        │
│  ML-DSA-65 signature verify   ← @noble/post-quantum (best-effort)│
│                                                                  │
│  Trust level: CRYPTOGRAPHIC — runs in auditor's browser.        │
│  No OMNIX server involved. Results are auditor-owned.           │
└─────────────────────────────────┬───────────────────────────────┘
                                   │ If signature or env mismatch:
                                   │ escalate to Plane 2
                                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  PLANE 2: Server (/api/forensic/verify — AUTHORITATIVE)         │
│                                                                  │
│  Same pypqc library that signed the block → authoritative PQC   │
│  Identical canonical hash computation      → cross-validates    │
│  Returns: verdict + reasons + audit_trace  → machine-readable   │
│                                                                  │
│  Trust level: INSTITUTIONAL — uses issuer's signing family.     │
│  Required when: Plane 1 PQC reports INCOMPLETE or mismatch.    │
└─────────────────────────────────────────────────────────────────┘
```

**Trust conflict rule (FVP-INV-006):** If Plane 1 = PASS and Plane 2 = any non-PASS verdict,
Plane 2 wins. The UI renders a critical banner: *"Authoritative verification: INVALID"*.
Plane 1 result is retained as a diagnostic trace, not as a binding verdict.

### 2. Verification States

Every block submitted to the portal receives exactly one verdict:

| State | Meaning | Trigger |
|---|---|---|
| `PASS` | All checks pass — block integrity confirmed | Merkle ✓ + canonical hash ✓ + chain ✓ + signature ✓ |
| `INTEGRITY_VIOLATION` | Block content was tampered | Merkle mismatch or canonical hash mismatch |
| `CHAIN_BREAK` | Chain link to predecessor is broken | `predecessor_block_hash` does not match predecessor's `canonical_hash` |
| `SIGNATURE_INVALID` | ML-DSA-65 signature fails verification | PQC verify returns false with valid key |
| `ORPHANED` | Block references a predecessor not provided and cannot be chain-verified | Predecessor block missing from upload set |
| `INCOMPLETE` | Block data is structurally malformed or PQC verification could not complete | Missing required fields or key not provided |

### 3. Browser Verification Engine

The browser engine executes the following steps for each uploaded block:

#### Step 1 — Merkle Root Recompute
```typescript
// Sort artifact hashes, join with "|", SHA-256 via SubtleCrypto
const sorted = [...block.integrity_manifest.artifact_hashes].sort()
const joined = sorted.join('|')
const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(joined))
const recomputed = 'sha256:' + Array.from(new Uint8Array(hash))
  .map(b => b.toString(16).padStart(2, '0')).join('')
// Compare to block.integrity_manifest.merkle_root
```

#### Step 2 — Canonical Hash Recompute
```typescript
// Build canonical object with exact fields and sort_keys
const canonical = {
  artifact_count:         block.artifact_count,
  block_id:               block.block_id,
  creation_timestamp_ns:  block.creation_timestamp_ns,
  evidence_classes:       [...block.evidence_classes].sort(),
  hash_algorithm:         block.integrity_manifest.hash_algorithm,
  merkle_root:            block.integrity_manifest.merkle_root,
  omnix_version:          block.omnix_version,
  predecessor_block_hash: block.predecessor_block_hash,
}
const canonicalJson = JSON.stringify(canonical, Object.keys(canonical).sort())
const hashBytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(canonicalJson))
const recomputed = 'sha256:' + hex(hashBytes)
// Compare to block.canonical_hash
```

#### Step 3 — Chain Link Verification
```typescript
// For multi-block upload: verify predecessor_block_hash matches prev block's canonical_hash
if (block.predecessor_block_hash !== GENESIS_SENTINEL) {
  const pred = blockMap.get(block.predecessor_block_hash)
  if (!pred) return { state: 'ORPHANED' }
  if (block.predecessor_block_hash !== pred.canonical_hash) return { state: 'CHAIN_BREAK' }
}
```

#### Step 4 — ML-DSA-65 Signature (best-effort)
```typescript
import { ml_dsa65 } from '@noble/post-quantum/ml-dsa'
// Attempt verification; wrap in try/catch for wire-format mismatch
// If fails: mark as INCOMPLETE for PQC, not SIGNATURE_INVALID
// Escalate to server for authoritative PQC verdict
```

**Wire compatibility note:** `pypqc` wraps the NIST reference implementation of Dilithium3 /
ML-DSA-65. `@noble/post-quantum` implements FIPS 204 (ML-DSA-65). These use the same underlying
algorithm but may differ in signature serialization across versions. If browser PQC returns false,
the portal does not emit `SIGNATURE_INVALID`; it marks the block `INCOMPLETE` (PQC) and
automatically requests authoritative server verification. Only the server path emits
`SIGNATURE_INVALID`.

### 4. Portal UI — Premium Forensic Visualization

The portal (`/archive-verify`) renders:

#### Upload Zone
- Multi-file drag-drop accepting `.json` COLD block files
- Optional: public key file (`.b64` or `.pem`) upload
- File inventory with instant structural validation
- Block ID auto-detected from filename and JSON content

#### Verdict Panel
- Large verdict badge with color semantics:
  - `PASS`: emerald green — *"Block integrity confirmed"*
  - `INTEGRITY_VIOLATION`: red — *"Content tampered"*
  - `CHAIN_BREAK`: orange — *"Chain continuity broken"*
  - `SIGNATURE_INVALID`: red — *"Cryptographic signature invalid"*
  - `ORPHANED`: amber — *"Predecessor block missing"*
  - `INCOMPLETE`: amber — *"Verification incomplete"*
- Dual result display: *Browser (preliminary)* and *Authoritative (server)*
- Conflict banner when planes disagree

#### Chain Map (SVG — pure React)
- Directed graph of all uploaded blocks
- Nodes: block ID, timestamp, artifact count, evidence classes
- Edges: predecessor relationships
- Node color: verdict state
- GENESIS sentinel shown as root anchor
- Clickable nodes expand block detail panel

#### Evidence Continuity Timeline (Recharts)
- Time axis from earliest block creation to latest
- Evidence class breakdown per block (stacked bar)
- Custody log overlaid as events
- Hover: full block metadata tooltip

#### Block Detail Panel
- Block ID, creation timestamp (ns → human-readable)
- Artifact count, evidence classes
- Merkle root: computed vs stored
- Canonical hash: computed vs stored
- Predecessor link: resolved vs orphaned
- PQC algorithm and signature length
- Custody entries (if available)

#### Export Controls
- *Download Verification Report* — self-contained HTML, no external deps
- *Generate OEP Bundle* — calls `/api/forensic/export`, downloads `.oep`
- *Copy Canonical Hash* — clipboard copy

### 5. Flask API Endpoints

**`POST /api/forensic/verify`**
```json
Request:  { "block": {…block JSON…}, "public_key_b64": "…", "predecessor_block": null }
Response: {
  "verdict":   "PASS",
  "reasons":   [],
  "checks": {
    "merkle_valid":    true,
    "canonical_valid": true,
    "chain_valid":     true,
    "signature_valid": true
  },
  "verified_at": "2026-05-15T01:00:00.000000+00:00",
  "verifier_version": "1.1.0"
}
```

**`POST /api/forensic/export`**
- Accepts: block JSON files + public key + custody log (optional)
- Returns: `application/zip` with `Content-Disposition: attachment; filename=OMNIX-PACKAGE-{ID}.oep`

**`GET /api/forensic/status`**
- Returns: verifier version, algorithm support, server health

### 6. Portal Invariants

**FVP-INV-001 — Canonical Determinism:**  
The browser's canonical hash computation MUST produce bit-identical output to `_compute_block_canonical_hash()` in `omnix_atf_verify.py` for the same input. Any divergence is a critical bug; no workaround is permitted.

**FVP-INV-002 — Merkle Recomputability:**  
The browser MUST recompute the Merkle root from `integrity_manifest.artifact_hashes` using the
`sha256-v1` algorithm. If `hash_algorithm` in the block is not `sha256-v1`, the portal MUST
render `INCOMPLETE` and refuse to emit any passing verdict.

**FVP-INV-003 — Chain Continuity:**  
When multiple blocks are uploaded, the portal MUST verify the full predecessor chain against
uploaded blocks. Gaps in the chain yield `ORPHANED`. The GENESIS sentinel (`"0"*64`) is the
only valid root; any other missing predecessor is an orphan.

**FVP-INV-004 — PQC Authoritative Boundary:**  
The portal MUST NOT emit `SIGNATURE_INVALID` from browser-side PQC alone. Browser PQC failure
yields `INCOMPLETE (PQC)`. Only the server path (`/api/forensic/verify`) may emit
`SIGNATURE_INVALID` — using the same `pypqc` family as the signing implementation.

**FVP-INV-005 — Server Availability:**  
The portal MUST remain functional for hash/chain verification when the server is unreachable.
All non-PQC checks run browser-side unconditionally. The server API is supplementary, not
required, for Merkle and canonical hash verdicts.

**FVP-INV-006 — Trust Conflict Resolution:**  
When Plane 1 (browser) and Plane 2 (server) disagree, the server verdict is binding. The UI
MUST surface a critical conflict notice. The browser result is retained as diagnostic context,
not as a binding assertion. Fail-closed: any server error during authoritative verification
causes the PQC verdict to remain `INCOMPLETE`, never `PASS`.

---

## Implementation Notes

- Route: `/archive-verify` — registered in `App.tsx`
- Component: `omnix_web/src/pages/ArchiveVerifierPage.tsx`
- Flask endpoints: `omnix_web/api/forensic_blueprint.py` — registered as blueprint `forensic_bp` in `server.py`
- URL prefix: `/api/forensic`
- Rate limit: 10 requests/minute on `/api/forensic/export`, 60/minute on `/api/forensic/verify`
- `MAX_CONTENT_LENGTH` for forensic endpoints: 50 MB (blocks can be large)
- The portal must not log block content server-side (privacy)

---

## Consequences

### Positive
- **Trust model shift.** Browser-side hash verification removes OMNIX from the verification trust chain for all non-PQC checks. An auditor verifying in their own browser cannot be deceived about hash integrity by OMNIX.
- **Zero installation.** Any party with the block file and a browser can verify integrity within 10 seconds.
- **Premium audit surface.** Forensic visualization (chain map, timeline, verdict panels) elevates the perceived protocol maturity significantly — this is the gap between "research prototype" and "institutional infrastructure."
- **Regulatory readiness.** EU AI Act Art. 13/14 requires transparency for high-risk AI systems. A live, independently verifiable audit portal is a direct regulatory response.

### Neutral
- **@noble/post-quantum dependency.** Adds ~180 KB gzipped to the bundle. Acceptable for an audit tool.
- **Wire compatibility uncertainty.** Browser PQC is best-effort pending cross-library test vector validation.

### Negative
- **OEP generation is server-side.** The full bundle generation requires server compute and signing. Browser-only users cannot generate OEP packages.

---

## References

- ADR-163 — Immutable Evidence Archive Pipeline (block format, canonical hash algorithm)
- ADR-165 — OMNIX Evidence Package (OEP) Format (forensic export)
- ADR-156 — ATF Public Verifier CLI (`omnix_atf_verify.py` v1.1.0)
- RFC-ATF-1 §7.6 — ATF-INV-006 (Independent Verifiability)
- EAP-INV-005 — Offline Reconstructability
- FIPS 204 — ML-DSA-65 (Module-Lattice-Based Digital Signature Standard)
