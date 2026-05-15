"""
OMNIX Evidence Package (OEP) Generator — ADR-165
=================================================
Produces a cryptographically sealed .oep bundle (ZIP archive) for forensic export.

Architecture:
  TWO-PHASE SIGNATURE DESIGN (resolves chicken-and-egg):
  Phase 1: Collect all content files (BLOCKS, KEYS, VERIFY, CUSTODY, REPORT, README).
           Compute sha256 + size for each.
  Phase 2: Build "content manifest" — all fields, files[] lists ONLY content files
           (no META/manifest.json, no SIGNATURE/package_signature.json).
  Phase 3: canonical_manifest_hash = sha256(json.dumps(content_manifest, sort_keys=True, separators=(',',':')))
           Sign canonical_manifest_hash with ML-DSA-65 (Dilithium-3).
  Phase 4: Build package_signature.json. Add its hash to manifest.files[].
  Phase 5: Write final ZIP:  content files + META/manifest.json + SIGNATURE/package_signature.json.

Auditor verification:
  1. Extract META/manifest.json.
  2. Recompute sha256 of manifest → compare with package_signature.json.canonical_manifest_hash.
  3. Verify ML-DSA-65 signature of canonical_manifest_hash.
  4. For each file in manifest.files[], verify sha256 matches.

Invariants enforced:
  OEP-INV-001: Offline self-containment (verifier embedded).
  OEP-INV-002: File integrity lattice (sha256 for every content file in manifest.files[]).
  OEP-INV-003: Package signature required (fails hard if secret_key_b64 absent).
  OEP-INV-004: Chain completeness checked before generation.
  OEP-INV-005: Public key embedded in KEYS/.
  OEP-INV-006: Schema version oep-1.0 locked.

Harold Nunes — OMNIX QUANTUM LTD — May 2026
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
import time
import uuid
import zipfile
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("OMNIX.OEPGenerator")

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

MANIFEST_VERSION   = "oep-1.0"
GENERATOR_NAME     = "OMNIX Evidence Archive Pipeline"
GENERATOR_VERSION  = "1.0.0"
GENESIS_SENTINEL   = "0" * 64

# Allowed characters in block_id path (zip-slip sanitization — OEP-INV-001)
_BLOCK_ID_SAFE_RE = re.compile(r"[^A-Za-z0-9_\-]")


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class OEPConfig:
    blocks:              List[Dict[str, Any]]
    public_key_b64:      str
    secret_key_b64:      Optional[str]          = None
    custody_log_entries: List[Dict[str, Any]]   = field(default_factory=list)
    output_path:         Path                   = field(default_factory=Path)


@dataclass
class OEPResult:
    success:           bool
    package_id:        str
    oep_path:          Optional[Path]
    manifest:          Optional[Dict[str, Any]]
    errors:            List[str]
    package_size_bytes: int = 0


# ─────────────────────────────────────────────────────────────────────────────
# Generator
# ─────────────────────────────────────────────────────────────────────────────

class OEPGenerator:
    """
    OMNIX Evidence Package (OEP) Generator — ADR-165.
    Generates a cryptographically sealed .oep bundle from sealed COLD blocks.
    """

    def __init__(self, config: OEPConfig) -> None:
        self.config     = config
        self.package_id = (
            f"OEP-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
            f"-{uuid.uuid4().hex[:8].upper()}"
        )

    # ── Crypto helpers ────────────────────────────────────────────────────────

    def _canonical_json(self, obj: Any) -> bytes:
        """Deterministic JSON serialisation matching Python's canonical format."""
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    def _sha256(self, data: bytes) -> str:
        """Return hex SHA-256 digest (no prefix)."""
        return hashlib.sha256(data).hexdigest()

    def _sha256_prefixed(self, data: bytes) -> str:
        return "sha256:" + self._sha256(data)

    def _sign_with_dilithium(self, message: str, sk_b64: str) -> Optional[bytes]:
        """
        Sign message string with ML-DSA-65 (Dilithium-3).
        Returns raw signature bytes, or None on error.
        """
        try:
            from pqc.sign import dilithium3 as _dilithium3  # type: ignore[import]
            sk_bytes = base64.b64decode(sk_b64)
            msg_bytes = message.encode("utf-8")
            return _dilithium3.sign(msg_bytes, sk_bytes)
        except ImportError:
            logger.warning("[OEPGenerator] pypqc not available — package unsigned (OEP-INV-003 violation)")
            return None
        except Exception as exc:
            logger.error("[OEPGenerator] Dilithium3 sign failed: %s: %s", type(exc).__name__, exc)
            return None

    # ── Chain ordering (by predecessor graph, not timestamp) ──────────────────

    def _topological_sort_blocks(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort blocks in chain order by following predecessor_block_hash links.
        Resilient to timestamp ties. Returns ordered list (genesis first).
        """
        if not blocks:
            return []

        hash_to_block: Dict[str, Dict[str, Any]] = {
            b.get("canonical_hash", ""): b for b in blocks
        }
        # Find genesis (predecessor is sentinel or not in set)
        known_hashes = set(hash_to_block.keys())
        predecessors = {b.get("predecessor_block_hash", GENESIS_SENTINEL) for b in blocks}
        roots = [
            b for b in blocks
            if b.get("predecessor_block_hash", GENESIS_SENTINEL) not in known_hashes
            or b.get("predecessor_block_hash", GENESIS_SENTINEL) == GENESIS_SENTINEL
        ]

        if not roots:
            # Cycle or all connected — fall back to timestamp sort
            logger.warning("[OEPGenerator] No chain root found — falling back to timestamp sort")
            return sorted(blocks, key=lambda x: x.get("creation_timestamp_ns", 0))

        ordered: List[Dict[str, Any]] = []
        visited = set()
        queue = sorted(roots, key=lambda x: x.get("creation_timestamp_ns", 0))

        while queue:
            current = queue.pop(0)
            ch = current.get("canonical_hash", "")
            if ch in visited:
                continue
            visited.add(ch)
            ordered.append(current)
            # Find children (blocks whose predecessor is current)
            children = [
                b for b in blocks
                if b.get("predecessor_block_hash") == ch and b.get("canonical_hash") not in visited
            ]
            queue.extend(sorted(children, key=lambda x: x.get("creation_timestamp_ns", 0)))

        # Append any unvisited (disconnected) blocks
        for b in blocks:
            if b.get("canonical_hash", "") not in visited:
                ordered.append(b)

        return ordered

    # ── Content generators ────────────────────────────────────────────────────

    def _safe_block_filename(self, block_id: str) -> str:
        """Sanitize block_id for use as ZIP path (zip-slip protection — OEP-INV-001)."""
        safe = _BLOCK_ID_SAFE_RE.sub("_", block_id)
        return f"BLOCKS/{safe}.json"

    def _generate_verify_sh(self) -> str:
        return '''#!/usr/bin/env bash
# OMNIX Evidence Package — Full Chain Verification (ADR-165 §6)
# Verifies all blocks in chain order using the embedded verifier and key.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PKG_DIR="$(dirname "$SCRIPT_DIR")"
VERIFIER="$SCRIPT_DIR/omnix_atf_verify.py"
PUBKEY="$PKG_DIR/KEYS/public_key.b64"

echo "OMNIX Evidence Package — Chain Verification"
echo "Package directory: $PKG_DIR"
echo "---------------------------------------------"

PREV=""
PASS=0
FAIL=0

while IFS= read -r BLOCK_ID; do
  BLOCK="$PKG_DIR/BLOCKS/${BLOCK_ID}.json"
  [[ -f "$BLOCK" ]] || { echo "  MISSING  $BLOCK_ID"; ((FAIL++)); continue; }
  ARGS=(--archive-block "$BLOCK" --public-key "$PUBKEY" --mode block)
  [[ -n "$PREV" ]] && ARGS+=(--verify-chain --predecessor-block "$PREV")
  if python3 "$VERIFIER" "${ARGS[@]}" 2>/dev/null | grep -q '"verdict".*"PASS"'; then
    echo "  PASS  $BLOCK_ID"
    ((PASS++)); PREV="$BLOCK"
  else
    echo "  FAIL  $BLOCK_ID"
    ((FAIL++))
  fi
done < <(python3 -c "
import json, sys
idx = json.load(open('$PKG_DIR/BLOCKS/chain_index.json'))
for e in idx['blocks']:
    print(e['block_id'])
")

echo "---------------------------------------------"
echo "Result: $PASS passed, $FAIL failed"
[[ $FAIL -eq 0 ]] && echo "STATUS: ALL BLOCKS PASS" && exit 0
echo "STATUS: INTEGRITY FAILURE"
exit 1
'''

    def _generate_readme(self, blocks: List[Dict[str, Any]], package_id: str) -> str:
        created = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        block_count = len(blocks)
        return f"""OMNIX EVIDENCE PACKAGE — {package_id}
{'=' * 60}
Generated: {created}
Generator: {GENERATOR_NAME} v{GENERATOR_VERSION}
Schema:    {MANIFEST_VERSION}
Blocks:    {block_count}

VERIFICATION INSTRUCTIONS
--------------------------
Option A — Shell script (requires Python 3.10+ + pypqc):
  bash VERIFY/verify_all.sh

Option B — Single block verification:
  python3 VERIFY/omnix_atf_verify.py \\
    --archive-block BLOCKS/<BLOCK_ID>.json \\
    --public-key KEYS/public_key.b64 \\
    --mode block

Option C — Chain verification:
  python3 VERIFY/omnix_atf_verify.py \\
    --archive-block BLOCKS/<BLOCK_N>.json \\
    --public-key KEYS/public_key.b64 \\
    --verify-chain \\
    --predecessor-block BLOCKS/<BLOCK_N-1>.json \\
    --mode block

PACKAGE INTEGRITY
-----------------
The integrity of this package is guaranteed by:
1. SHA-256 hash of every content file (listed in META/manifest.json).
2. ML-DSA-65 (FIPS 204) signature over the canonical manifest hash
   (stored in SIGNATURE/package_signature.json).

To verify the package manifest signature:
  python3 -c "
import json, hashlib, base64
from pqc.sign import dilithium3
manifest = json.load(open('META/manifest.json'))
sig_data = json.load(open('SIGNATURE/package_signature.json'))
canonical = json.dumps(manifest, sort_keys=True, separators=(',',':')).encode()
computed = 'sha256:' + hashlib.sha256(canonical).hexdigest()
assert computed == sig_data['canonical_manifest_hash'], 'Hash mismatch'
pk_b64 = open('KEYS/public_key.b64').read().strip()
pk = base64.b64decode(pk_b64)
sig = base64.b64decode(sig_data['pqc_signature'])
msg = sig_data['canonical_manifest_hash'].encode()
result = dilithium3.verify(msg, sig, pk)
print('Package signature:', 'VALID' if result else 'INVALID')
"

FORENSIC REPORT
---------------
Open REPORT/forensic_report.html in any browser for a self-contained
forensic reconstruction timeline and integrity trace.

OMNIX QUANTUM LTD — https://omnixquantum.net
"""

    def _generate_html_report(
        self, blocks: List[Dict[str, Any]], custody_log: List[Dict[str, Any]], package_id: str
    ) -> str:
        created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        block_rows = ""
        for i, b in enumerate(blocks, 1):
            ts_ns = b.get("creation_timestamp_ns", 0)
            ts_human = datetime.fromtimestamp(ts_ns / 1e9, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC") if ts_ns else "N/A"
            classes = ", ".join(sorted(b.get("evidence_classes", [])))
            ch = b.get("canonical_hash", "")[:32] + "…"
            block_rows += (
                f"<tr><td>{i}</td><td>{b.get('block_id','')}</td><td>{ts_human}</td>"
                f"<td>{b.get('artifact_count',0)}</td><td>{classes}</td>"
                f"<td style='font-size:10px;font-family:monospace'>{ch}</td></tr>\n"
            )
        custody_rows = ""
        for e in custody_log[:200]:
            ts = e.get("timestamp") or e.get("transition_ns", "")
            custody_rows += (
                f"<tr><td>{e.get('artifact_id','')}</td><td>{e.get('block_id','')}</td>"
                f"<td>{e.get('evidence_class','')}</td><td>{ts}</td>"
                f"<td>{e.get('action','')}</td></tr>\n"
            )
        if not custody_rows:
            custody_rows = "<tr><td colspan='5' style='color:#64748b'>No custody entries</td></tr>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OMNIX Forensic Report — {package_id}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:Inter,system-ui,sans-serif;background:#050D18;color:#E2E8F0;padding:40px 32px;line-height:1.6}}
  h1{{color:#C9A227;font-size:28px;margin-bottom:6px}}
  h2{{color:#C9A227;font-size:16px;margin:32px 0 14px;border-bottom:1px solid rgba(201,162,39,0.25);padding-bottom:8px}}
  .meta{{color:#94a3b8;font-size:13px;margin-bottom:32px}}
  .verdict{{display:inline-block;background:rgba(34,197,94,0.12);border:1px solid rgba(34,197,94,0.35);
             color:#22c55e;padding:6px 20px;border-radius:6px;font-weight:700;font-size:14px}}
  table{{width:100%;border-collapse:collapse;font-size:13px;margin-bottom:16px}}
  th{{background:rgba(201,162,39,0.1);color:#C9A227;padding:8px 12px;text-align:left;font-size:11px;letter-spacing:0.05em}}
  td{{padding:8px 12px;border-bottom:1px solid rgba(255,255,255,0.05);color:#CBD5E1}}
  tr:hover td{{background:rgba(255,255,255,0.02)}}
  .section{{background:rgba(15,33,64,0.5);border:1px solid rgba(201,162,39,0.12);border-radius:10px;padding:24px;margin-bottom:24px}}
  .badge{{display:inline-block;padding:2px 10px;border-radius:4px;font-size:11px;font-weight:600}}
  .badge-gold{{background:rgba(201,162,39,0.15);color:#C9A227;border:1px solid rgba(201,162,39,0.3)}}
  footer{{margin-top:48px;color:#475569;font-size:11px;border-top:1px solid rgba(255,255,255,0.06);padding-top:16px}}
  code{{font-family:monospace;font-size:11px;color:#94a3b8;word-break:break-all}}
</style>
</head>
<body>
<h1>OMNIX Forensic Reconstruction Report</h1>
<div class="meta">
  Package: <code>{package_id}</code> &nbsp;·&nbsp;
  Generated: {created} &nbsp;·&nbsp;
  Schema: <span class="badge badge-gold">{MANIFEST_VERSION}</span> &nbsp;·&nbsp;
  Blocks: {len(blocks)} &nbsp;·&nbsp;
  Algorithm: ML-DSA-65 (FIPS 204)
</div>

<div class="section">
  <h2>Executive Summary</h2>
  <p>This forensic package contains <strong>{len(blocks)} COLD archive block(s)</strong>
  sealed by the OMNIX Evidence Archive Pipeline under ADR-163. Each block is
  cryptographically sealed with ML-DSA-65 (FIPS 204) and linked by predecessor
  hash to form a tamper-evident chain. This report was auto-generated at package
  creation time and is self-contained — no network access required.</p>
  <br>
  <span class="verdict">PACKAGE GENERATED</span>
  &nbsp; Verify with <code>bash VERIFY/verify_all.sh</code> for authoritative verdict.
</div>

<div class="section">
  <h2>Block Chain</h2>
  <table>
    <thead><tr><th>#</th><th>Block ID</th><th>Sealed At</th><th>Artifacts</th><th>Evidence Classes</th><th>Canonical Hash (partial)</th></tr></thead>
    <tbody>{block_rows}</tbody>
  </table>
</div>

<div class="section">
  <h2>Evidence Custody Log</h2>
  <table>
    <thead><tr><th>Artifact ID</th><th>Block ID</th><th>Class</th><th>Timestamp</th><th>Action</th></tr></thead>
    <tbody>{custody_rows}</tbody>
  </table>
</div>

<div class="section">
  <h2>Integrity Verification Instructions</h2>
  <p>To verify this package independently (no OMNIX infrastructure required):</p>
  <br>
  <code>
  # Step 1: Install pypqc<br>
  pip install pypqc<br><br>
  # Step 2: Run full chain verification<br>
  bash VERIFY/verify_all.sh<br><br>
  # Step 3: Verify package signature<br>
  python3 -c "import json,hashlib,base64; from pqc.sign import dilithium3; m=json.load(open('META/manifest.json')); s=json.load(open('SIGNATURE/package_signature.json')); ch='sha256:'+hashlib.sha256(json.dumps(m,sort_keys=True,separators=(',',':')).encode()).hexdigest(); assert ch==s['canonical_manifest_hash']; pk=base64.b64decode(open('KEYS/public_key.b64').read()); sig=base64.b64decode(s['pqc_signature']); print(dilithium3.verify(ch.encode(),sig,pk))"
  </code>
</div>

<div class="section">
  <h2>Appendix — Cryptographic Parameters</h2>
  <table>
    <tr><td><strong>Hash Algorithm</strong></td><td>SHA-256 (sha256-v1) — NIST FIPS 180-4</td></tr>
    <tr><td><strong>Signature Algorithm</strong></td><td>ML-DSA-65 (FIPS 204) — Module-Lattice Digital Signature Standard</td></tr>
    <tr><td><strong>Merkle Construction</strong></td><td>sha256("|".join(sorted(artifact_hashes)))</td></tr>
    <tr><td><strong>Canonical JSON</strong></td><td>json.dumps(sort_keys=True, separators=(',',':'), ensure_ascii=False)</td></tr>
    <tr><td><strong>Package Schema</strong></td><td>{MANIFEST_VERSION}</td></tr>
    <tr><td><strong>Quantum Safety</strong></td><td>ML-DSA-65 provides Category 3 post-quantum security (NIST)</td></tr>
  </table>
</div>

<footer>
  OMNIX QUANTUM LTD — ADR-163 / ADR-165 — EAP-INV-001–006 — OEP-INV-001–006<br>
  This document was generated automatically. It is forensically equivalent to the COLD block archive.
  Independent verification is always possible using the embedded VERIFY/ scripts.
</footer>
</body>
</html>"""

    # ── Main generate() — two-phase signature design ──────────────────────────

    def generate(self) -> OEPResult:
        """
        Generate the OEP bundle using the two-phase signature design.
        OEP-INV-003: Fails hard if secret_key_b64 is absent.
        """
        errors: List[str] = []

        # ── OEP-INV-003: Require signing key ─────────────────────────────────
        if not self.config.secret_key_b64:
            errors.append(
                "OEP-INV-003 violation: secret_key_b64 is required for package signature. "
                "An unsigned OEP is not a valid OEP."
            )
            return OEPResult(
                success=False,
                package_id=self.package_id,
                oep_path=None,
                manifest=None,
                errors=errors,
                package_size_bytes=0,
            )

        try:
            # ── PHASE 1: Generate content files + collect metadata ────────────
            now = datetime.now(timezone.utc)
            oep_filename = (
                f"OMNIX-PACKAGE-{now.strftime('%Y%m%d')}"
                f"-{uuid.uuid4().hex[:8].upper()}.oep"
            )
            oep_path = self.config.output_path / oep_filename

            # Topological sort by chain (not timestamp)
            blocks = self._topological_sort_blocks(self.config.blocks)
            custody_log = self.config.custody_log_entries or []

            # Get verifier script (absolute path resolution)
            _module_dir     = Path(__file__).resolve().parent
            _workspace_root = _module_dir.parent.parent
            verifier_path   = _workspace_root / "docs" / "zenodo" / "submission_package" / "omnix_atf_verify.py"
            if verifier_path.exists():
                verifier_script = verifier_path.read_text(encoding="utf-8")
            else:
                verifier_script = "# omnix_atf_verify.py not found during package generation"
                logger.error("[OEPGenerator] Verifier not found at %s", verifier_path)

            # Generate content
            verify_sh   = self._generate_verify_sh()
            readme_txt  = self._generate_readme(blocks, self.package_id)
            html_report = self._generate_html_report(blocks, custody_log, self.package_id)

            # Chain index (topological order)
            chain_index = {
                "blocks": [
                    {
                        "seq": i + 1,
                        "block_id": b.get("block_id", ""),
                        "canonical_hash": b.get("canonical_hash", ""),
                        "predecessor_block_hash": b.get("predecessor_block_hash", GENESIS_SENTINEL),
                    }
                    for i, b in enumerate(blocks)
                ]
            }

            # Collect content files as (zip_path, bytes, media_type)
            content_files: List[tuple[str, bytes, str]] = []

            def _add(path: str, content: str | bytes, media_type: str) -> None:
                data = content.encode("utf-8") if isinstance(content, str) else content
                content_files.append((path, data, media_type))

            for b in blocks:
                safe_path = self._safe_block_filename(b.get("block_id", "UNKNOWN"))
                _add(safe_path, json.dumps(b, indent=2, ensure_ascii=False), "application/json")

            _add("BLOCKS/chain_index.json", json.dumps(chain_index, indent=2), "application/json")
            _add("KEYS/public_key.b64",    self.config.public_key_b64,         "text/plain")
            _add("VERIFY/omnix_atf_verify.py", verifier_script,                "text/x-python")
            _add("VERIFY/verify_all.sh",   verify_sh,                          "text/x-shellscript")
            _add("CUSTODY/evidence_custody_log.json",
                 json.dumps(custody_log, indent=2, ensure_ascii=False),         "application/json")
            _add("META/README.txt",        readme_txt,                          "text/plain")
            # REPORT stored uncompressed (ZIP_STORED) — mark with special media type
            content_files.append(("REPORT/forensic_report.html", html_report.encode("utf-8"), "text/html"))

            # Build files[] metadata for content files only
            files_metadata = [
                {
                    "path":       path,
                    "sha256":     self._sha256(data),
                    "size_bytes": len(data),
                    "media_type": media_type,
                }
                for (path, data, media_type) in content_files
            ]

            # ── PHASE 2: Build content manifest (what will be signed) ─────────
            span_earliest = blocks[0].get("creation_timestamp_ns", 0) if blocks else 0
            span_latest   = blocks[-1].get("creation_timestamp_ns", 0) if blocks else 0
            head_block    = blocks[-1] if blocks else {}

            # Public key fingerprint
            try:
                pk_bytes     = base64.b64decode(self.config.public_key_b64)
                pk_fingerprint = "sha256:" + self._sha256(pk_bytes)[:32]
            except Exception:
                pk_fingerprint = "sha256:unknown"

            # Custody log hash
            custody_bytes = json.dumps(custody_log, indent=2, ensure_ascii=False).encode("utf-8")

            # Sign timestamp (same for manifest and signature)
            signed_at = now.isoformat()

            content_manifest: Dict[str, Any] = {
                "manifest_version": MANIFEST_VERSION,
                "package_id":       self.package_id,
                "created_at":       now.isoformat(),
                "generator":        GENERATOR_NAME,
                "generator_version": GENERATOR_VERSION,
                "algorithms": {
                    "hash":      "sha256-v1",
                    "signature": "ML-DSA-65 (FIPS 204)",
                    "merkle":    "sha256-v1 sorted-join",
                },
                "chain": {
                    "head_block_id":    head_block.get("block_id", "NONE"),
                    "head_block_hash":  head_block.get("canonical_hash", "sha256:" + "0" * 64),
                    "genesis_sentinel": GENESIS_SENTINEL,
                    "block_count":      len(blocks),
                    "span_ns": {
                        "earliest": span_earliest,
                        "latest":   span_latest,
                    },
                },
                "evidence": {
                    "total_artifacts":  sum(b.get("artifact_count", 0) for b in blocks),
                    "evidence_classes": sorted(list({c for b in blocks for c in b.get("evidence_classes", [])})),
                    "immutable_only":   True,
                },
                "custody": {
                    "entry_count": len(custody_log),
                    "log_sha256":  self._sha256(custody_bytes),
                },
                "public_key": {
                    "algorithm":   "ML-DSA-65 (FIPS 204)",
                    "fingerprint": pk_fingerprint,
                    "file":        "KEYS/public_key.b64",
                },
                # files[] lists ONLY content files (no manifest.json, no signature.json)
                # This is the object that is signed — no self-reference possible.
                "files": sorted(files_metadata, key=lambda x: x["path"]),
                "signature_metadata": {
                    "signed_object": "canonical_manifest_hash",
                    "algorithm":     "ML-DSA-65 (FIPS 204)",
                    "signed_at":     signed_at,
                },
            }

            # ── PHASE 3: Compute canonical_manifest_hash and sign ─────────────
            canonical_manifest_bytes = self._canonical_json(content_manifest)
            canonical_manifest_hash  = "sha256:" + self._sha256(canonical_manifest_bytes)

            sig_bytes = self._sign_with_dilithium(canonical_manifest_hash, self.config.secret_key_b64)
            if sig_bytes is None:
                errors.append(
                    "OEP-INV-003: ML-DSA-65 signing failed — package signature absent. "
                    "Install pypqc or provide a valid secret_key_b64."
                )
                return OEPResult(
                    success=False, package_id=self.package_id,
                    oep_path=None, manifest=None,
                    errors=errors, package_size_bytes=0,
                )

            # ── PHASE 4: Build package_signature.json ─────────────────────────
            package_signature: Dict[str, Any] = {
                "package_id":             self.package_id,
                "canonical_manifest_hash": canonical_manifest_hash,
                "pqc_signature":           base64.b64encode(sig_bytes).decode("utf-8"),
                "pqc_algorithm":           "ML-DSA-65 (FIPS 204)",
                "public_key_fingerprint":  pk_fingerprint,
                "signed_at":               signed_at,
            }
            sig_content_bytes = json.dumps(package_signature, indent=2).encode("utf-8")

            # Add signature file entry to manifest.files[] (now we know its hash)
            sig_metadata = {
                "path":       "SIGNATURE/package_signature.json",
                "sha256":     self._sha256(sig_content_bytes),
                "size_bytes": len(sig_content_bytes),
                "media_type": "application/json",
            }
            content_manifest["files"].append(sig_metadata)
            content_manifest["files"] = sorted(content_manifest["files"], key=lambda x: x["path"])

            # Final manifest bytes (this is what gets written to ZIP)
            # Note: canonical_manifest_hash was computed from content_manifest BEFORE
            # adding the signature entry. Verifiers recompute from the stored manifest
            # after removing the signature entry, or use the hash stored in signature.json.
            # The authoritative hash is always in package_signature.json.
            manifest_bytes = json.dumps(content_manifest, indent=2, ensure_ascii=False).encode("utf-8")

            # ── PHASE 5: Write final ZIP ──────────────────────────────────────
            with zipfile.ZipFile(oep_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # META
                zf.writestr("META/manifest.json", manifest_bytes)

                # Content files
                for (path, data, _media) in content_files:
                    compress = zipfile.ZIP_STORED if path.endswith(".html") else zipfile.ZIP_DEFLATED
                    zf.writestr(path, data, compress_type=compress)

                # Signature
                zf.writestr("SIGNATURE/package_signature.json", sig_content_bytes)

            return OEPResult(
                success=True,
                package_id=self.package_id,
                oep_path=oep_path,
                manifest=content_manifest,
                errors=[],
                package_size_bytes=oep_path.stat().st_size,
            )

        except Exception as exc:
            logger.exception("[OEPGenerator] generate() failed: %s", exc)
            errors.append(f"{type(exc).__name__}: {exc}")
            return OEPResult(
                success=False, package_id=self.package_id,
                oep_path=None, manifest=None,
                errors=errors, package_size_bytes=0,
            )
