# ADR-165: OMNIX Evidence Package (OEP) Format

**Status:** Accepted  
**Date:** May 15, 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Supersedes:** None  
**Extends:** ADR-163 (Immutable Evidence Archive Pipeline) · ADR-164 (Forensic Verification Portal)  
**Related:** ADR-156 (ATF Public Verifier CLI) · ADR-162 (Evidence Lifecycle & Immutable Retention) ·
            RFC-ATF-1 §7.6 (ATF-INV-006) · EAP-INV-005 (Offline Reconstructability)

---

## Context

The COLD block archive (ADR-163) and the Forensic Verification Portal (ADR-164) together deliver
online verification capability. But institutional forensic practice requires more than online tools.

Regulated industries — financial services, legal, healthcare, defense — handle evidence through
**self-contained packages** that can be:

- Transmitted via secure channel to an auditor
- Stored in a compliance archive for years
- Presented in a regulatory review without any live system access
- Reconstructed by any party years later with only the package and a standard Python installation

SIEM vendors have EVTX bundles. eDiscovery platforms have EDRM packages. Forensic tools have E01
disk images. OMNIX needs its own.

The OMNIX Evidence Package (OEP) is the answer: a cryptographically sealed, self-contained
archive of governance evidence that any auditor can verify without touching OMNIX infrastructure.

### What an auditor currently gets

When an OMNIX operator exports governance evidence today, they export raw database rows —
JSON files with no chain context, no verification script, no custody log, no reconstruction path.
An auditor receiving this cannot independently verify:

1. Whether the evidence was tampered between export and receipt
2. Whether the chain is complete (no blocks excised)
3. Whether the issuer's PQC key is authentic
4. Whether the evidence classes are correctly labeled
5. How to reconstruct the governance timeline

### What an OEP provides

A single `.oep` file that is a ZIP archive containing everything an auditor needs to:

1. Verify every block's hash integrity (offline)
2. Verify PQC signatures against the embedded public key
3. Verify chain continuity from genesis to head
4. Reconstruct the governance timeline from custody logs
5. Produce an independent verification report

---

## Decision

### 1. OEP Physical Format

An OEP is a **ZIP archive** with the `.oep` extension. The file name pattern is:

```
OMNIX-PACKAGE-{YYYYMMDD}-{UUID8}.oep
```

The archive uses ZIP64 for large packages. Compression level: deflate for all files except
`REPORT/forensic_report.html` (stored uncompressed for immediate browser rendering).

**Anti-zip-slip protection:** The `oep_generator.py` MUST validate that no file path resolves
outside the archive root. The `oep_extractor.py` (ADR-165 companion) MUST sanitize all paths.

### 2. Directory Structure

```
OMNIX-PACKAGE-{DATE}-{ID}.oep
├── META/
│   ├── manifest.json              ← Package manifest (signed)
│   └── README.txt                 ← Human-readable instructions
├── BLOCKS/
│   ├── OMNIX-BLOCK-*.json         ← All COLD blocks in chain order
│   └── chain_index.json           ← Ordered block list: [{block_id, canonical_hash, seq}]
├── KEYS/
│   └── public_key.b64             ← Issuer's ML-DSA-65 public key (base64, no headers)
├── VERIFY/
│   ├── omnix_atf_verify.py        ← Offline CLI verifier (verbatim copy, v1.1.0)
│   └── verify_all.sh              ← Shell script verifying all blocks in chain order
├── CUSTODY/
│   └── evidence_custody_log.json  ← Custody log entries for all blocks in package
├── REPORT/
│   └── forensic_report.html       ← Auto-generated forensic reconstruction report (offline HTML)
└── SIGNATURE/
    └── package_signature.json     ← ML-DSA-65 signature over canonical manifest hash
```

### 3. Package Manifest Schema

`META/manifest.json` — canonical, deterministic, field-sorted:

```json
{
  "manifest_version":      "oep-1.0",
  "package_id":            "OEP-{YYYYMMDD}-{UUID8}",
  "created_at":            "2026-05-15T01:00:00.000000+00:00",
  "generator":             "OMNIX Evidence Archive Pipeline",
  "generator_version":     "1.0.0",
  "algorithms": {
    "hash":      "sha256-v1",
    "signature": "ML-DSA-65 (FIPS 204)",
    "merkle":    "sha256-v1 sorted-join"
  },
  "chain": {
    "head_block_id":    "OMNIX-BLOCK-20260515-000003",
    "head_block_hash":  "sha256:{hex}",
    "genesis_sentinel": "0000000000000000000000000000000000000000000000000000000000000000",
    "block_count":      3,
    "span_ns": {
      "earliest": 1778808655000000000,
      "latest":   1778900000000000000
    }
  },
  "evidence": {
    "total_artifacts":    847,
    "evidence_classes":   ["LEGAL", "PQC", "CONTRACT", "EXCEPTION"],
    "immutable_only":     true
  },
  "custody": {
    "entry_count":        847,
    "log_sha256":         "{sha256 of evidence_custody_log.json}"
  },
  "public_key": {
    "algorithm":          "ML-DSA-65 (FIPS 204)",
    "fingerprint":        "sha256:{first-32-hex-chars-of-sha256(key_bytes)}",
    "file":               "KEYS/public_key.b64"
  },
  "files": [
    { "path": "META/manifest.json",            "sha256": "{hex}", "size_bytes": 1024,   "media_type": "application/json" },
    { "path": "META/README.txt",               "sha256": "{hex}", "size_bytes": 2048,   "media_type": "text/plain" },
    { "path": "BLOCKS/OMNIX-BLOCK-*.json",     "sha256": "{hex}", "size_bytes": 204800, "media_type": "application/json" },
    { "path": "BLOCKS/chain_index.json",       "sha256": "{hex}", "size_bytes": 512,    "media_type": "application/json" },
    { "path": "KEYS/public_key.b64",           "sha256": "{hex}", "size_bytes": 2800,   "media_type": "text/plain" },
    { "path": "VERIFY/omnix_atf_verify.py",   "sha256": "{hex}", "size_bytes": 65536,  "media_type": "text/x-python" },
    { "path": "VERIFY/verify_all.sh",          "sha256": "{hex}", "size_bytes": 1024,   "media_type": "text/x-shellscript" },
    { "path": "CUSTODY/evidence_custody_log.json", "sha256": "{hex}", "size_bytes": 51200, "media_type": "application/json" },
    { "path": "REPORT/forensic_report.html",   "sha256": "{hex}", "size_bytes": 204800, "media_type": "text/html" },
    { "path": "SIGNATURE/package_signature.json", "sha256": "{hex}", "size_bytes": 4096, "media_type": "application/json" }
  ],
  "signature_metadata": {
    "signed_object":   "canonical_manifest_hash",
    "algorithm":       "ML-DSA-65 (FIPS 204)",
    "signed_at":       "2026-05-15T01:00:00.000000+00:00"
  }
}
```

### 4. Package Signature

`SIGNATURE/package_signature.json`:

```json
{
  "package_id":             "OEP-{YYYYMMDD}-{UUID8}",
  "canonical_manifest_hash": "sha256:{sha256 of canonical JSON of manifest}",
  "pqc_signature":          "{base64-ML-DSA-65 signature over canonical_manifest_hash}",
  "pqc_algorithm":          "ML-DSA-65 (FIPS 204)",
  "public_key_fingerprint": "sha256:{fingerprint}",
  "signed_at":              "2026-05-15T01:00:00.000000+00:00"
}
```

**Signing procedure:**
1. Serialize `manifest.json` with `json.dumps(manifest, sort_keys=True, separators=(',', ':'))`
2. Compute `sha256:` + SHA-256 of serialized bytes → `canonical_manifest_hash`
3. Sign `canonical_manifest_hash.encode('utf-8')` with ML-DSA-65 private key
4. Store in `SIGNATURE/package_signature.json`

Note: The `files[]` array in `manifest.json` includes a SHA-256 for `SIGNATURE/package_signature.json`
itself (the signature JSON, not the signature bytes). This creates a complete integrity lattice:
the signature signs the manifest, the manifest hashes every file including the signature file.

### 5. Forensic Reconstruction Report

`REPORT/forensic_report.html` is a self-contained HTML file:

- **No external dependencies** — no CDN, no fonts from Google, no scripts from external URLs
- All CSS inline
- All visualizations rendered via inline SVG
- Sections:
  - Executive Summary (package ID, creation date, block count, verdict)
  - Block Chain (ordered table: ID, timestamp, artifact count, canonical hash, PQC status)
  - Evidence Class Breakdown (table per class: count, first/last timestamp)
  - Authority Timeline (custody log events, ordered by `transition_ns`)
  - Integrity Verification Trace (per-block: merkle ✓/✗, canonical ✓/✗, chain ✓/✗, PQC ✓/✗)
  - Appendix: Verification Instructions (how to run `omnix_atf_verify.py` against each block)
- OMNIX branding, gold/navy color scheme
- Rendered at package generation time; static — no JavaScript required

### 6. verify_all.sh

```bash
#!/usr/bin/env bash
# OMNIX Evidence Package — Full Chain Verification
# Verifies all blocks in chain order using embedded verifier and key
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(dirname "$SCRIPT_DIR")"
VERIFIER="$SCRIPT_DIR/omnix_atf_verify.py"
PUBKEY="$PKG_DIR/KEYS/public_key.b64"

echo "OMNIX Evidence Package — Chain Verification"
echo "Package: $(basename "$PKG_DIR")"
echo "---------------------------------------------"
PREV=""
PASS=0; FAIL=0
while IFS= read -r BLOCK; do
  ARGS=(--archive-block "$BLOCK" --public-key "$PUBKEY" --mode block)
  [[ -n "$PREV" ]] && ARGS+=(--verify-chain --predecessor-block "$PREV")
  if python3 "$VERIFIER" "${ARGS[@]}" 2>/dev/null | grep -q '"verdict": "PASS"'; then
    echo "  PASS  $(basename "$BLOCK")"
    ((PASS++)); PREV="$BLOCK"
  else
    echo "  FAIL  $(basename "$BLOCK")"
    ((FAIL++))
  fi
done < <(python3 -c "
import json, sys
idx = json.load(open('$PKG_DIR/BLOCKS/chain_index.json'))
for e in idx['blocks']:
    print('$PKG_DIR/BLOCKS/' + e['block_id'] + '.json')
")
echo "---------------------------------------------"
echo "Result: $PASS passed, $FAIL failed"
[[ $FAIL -eq 0 ]] && echo "STATUS: ALL BLOCKS PASS" || { echo "STATUS: INTEGRITY FAILURE"; exit 1; }
```

### 7. OEP Package Invariants

**OEP-INV-001 — Offline Self-Containment:**  
An OEP MUST be verifiable with only the package file and a standard Python 3.10+ installation
with `pypqc`. No network access, no OMNIX credentials, no external dependencies are permitted
during verification.

**OEP-INV-002 — File Integrity Lattice:**  
Every file in the OEP MUST appear in `files[]` in `manifest.json` with its correct SHA-256.
A package containing any file not listed in the manifest is invalid. A package where any listed
file's hash does not match the stored hash is invalid.

**OEP-INV-003 — Mandatory Package Signature:**  
`SIGNATURE/package_signature.json` MUST be present and MUST contain a valid ML-DSA-65 signature
over the canonical manifest hash. An OEP without a valid package signature is not a valid OEP.

**OEP-INV-004 — Chain Completeness:**  
If a block in `BLOCKS/` references a `predecessor_block_hash` that is not the GENESIS sentinel,
the predecessor block MUST also appear in `BLOCKS/`. An OEP with a chain gap is invalid.

**OEP-INV-005 — Embedded Public Key:**  
`KEYS/public_key.b64` MUST contain the public key that verifies the blocks and the package
signature. Referencing a key by URL is not permitted — the key must be embedded.

**OEP-INV-006 — Schema Version Lock:**  
`manifest_version` MUST be `"oep-1.0"` for packages generated under this ADR. Future schema
changes require a new version string and a new ADR. Parsers MUST reject unknown versions.

---

## oep_generator.py Interface

```python
from omnix_core.evidence.oep_generator import OEPGenerator, OEPConfig

config = OEPConfig(
    blocks=[block1_dict, block2_dict, block3_dict],
    public_key_b64="...",
    secret_key_b64="...",         # for package signature
    custody_log_entries=[...],    # optional
    output_path=Path("/tmp/output")
)
gen = OEPGenerator(config)
result = gen.generate()           # → OEPResult
# result.oep_path: Path to .oep file
# result.package_id: OEP-...
# result.manifest: dict
# result.errors: list[str]
```

---

## Consequences

### Positive
- **Institutional artifact.** The OEP is a forensic-grade deliverable comparable to EnCase
  packages or EDRM exports — something a compliance officer can file, archive, and audit.
- **Standard positions.** Defining the format under OMNIX ADR creates a versioned standard
  that third-party tools can implement. This is the first step toward ATF-3 interoperability.
- **No trust dependency.** An auditor receiving an OEP is not trusting OMNIX's live
  infrastructure — they are trusting the embedded math (SHA-256, ML-DSA-65, chain links).
- **Longevity.** An OEP created today remains self-verifiable in 10 years as long as the
  `omnix_atf_verify.py` embedded in it runs on the Python version available then.

### Neutral
- **ZIP format.** Chosen for universal support. Not a custom binary format — deliberately.
- **Package size.** A 3-block chain with 1000 artifacts generates approximately 2–5 MB OEP.
  The embedded verifier script adds ~65 KB. Negligible at any storage tier.

### Negative
- **Private key required.** Package signing requires the ML-DSA-65 private key at generation
  time. Without it, the package signature is absent and OEP-INV-003 fails. Operators must
  have key access at export time.

---

## References

- ADR-163 — Immutable Evidence Archive Pipeline (block format)
- ADR-164 — Forensic Archive Verification Portal (web UI, trust model)
- ADR-156 — ATF Public Verifier CLI (embedded in `VERIFY/`)
- EAP-INV-005 — Offline Reconstructability
- OEP-INV-001 through OEP-INV-006 (this ADR)
- FIPS 204 — ML-DSA-65
- RFC 1951 — DEFLATE compression (ZIP)
- EDRM (Electronic Discovery Reference Model) — forensic package design reference
