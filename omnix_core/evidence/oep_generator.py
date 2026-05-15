import base64
import hashlib
import json
import logging
import os
import time
import uuid
import zipfile
import io
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("OMNIX.OEPGenerator")

@dataclass
class OEPConfig:
    blocks: List[Dict[str, Any]]
    public_key_b64: str
    secret_key_b64: Optional[str] = None
    custody_log_entries: List[Dict[str, Any]] = field(default_factory=list)
    output_path: Path = Path(".")

@dataclass
class OEPResult:
    success: bool
    package_id: str
    oep_path: Optional[Path]
    manifest: Optional[Dict[str, Any]]
    errors: List[str]
    package_size_bytes: int = 0

class OEPGenerator:
    """
    OMNIX Evidence Package (OEP) Generator (ADR-165).
    """
    def __init__(self, config: OEPConfig):
        self.config = config
        self.package_id = f"OEP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    def _canonical_json(self, obj: Any) -> bytes:
        return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def _sha256(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def generate(self) -> OEPResult:
        errors = []
        try:
            oep_filename = f"OMNIX-PACKAGE-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}.oep"
            oep_path = self.config.output_path / oep_filename
            
            # 1. Prepare data
            blocks = sorted(self.config.blocks, key=lambda x: x.get("creation_timestamp_ns", 0))
            chain_index = {
                "blocks": [
                    {
                        "seq": i + 1,
                        "block_id": b["block_id"],
                        "canonical_hash": b["canonical_hash"]
                    } for i, b in enumerate(blocks)
                ]
            }
            
            custody_log = self.config.custody_log_entries
            
            # 2. Generate Forensic Report
            html_report = self._generate_html_report(blocks, custody_log)
            
            # 3. Get verifier script content — resolve relative to workspace root
            _module_dir = Path(__file__).resolve().parent
            _workspace_root = _module_dir.parent.parent  # omnix_core/evidence/ → workspace
            verifier_path = _workspace_root / "docs" / "zenodo" / "submission_package" / "omnix_atf_verify.py"
            if verifier_path.exists():
                with open(verifier_path, "r") as f:
                    verifier_script = f.read()
            else:
                verifier_script = "# Verifier script not found during package generation"
                logger.error("omnix_atf_verify.py not found at %s", verifier_path)

            verify_all_sh = self._generate_verify_sh()
            readme_txt = self._generate_readme()

            # 4. Create ZIP in memory first to calculate hashes for manifest
            buffer = io.BytesIO()
            files_metadata = []
            
            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                def add_file(path, content, media_type):
                    if isinstance(content, str):
                        content_bytes = content.encode("utf-8")
                    else:
                        content_bytes = content
                    zf.writestr(path, content_bytes)
                    files_metadata.append({
                        "path": path,
                        "sha256": self._sha256(content_bytes),
                        "size_bytes": len(content_bytes),
                        "media_type": media_type
                    })

                # BLOCKS
                for b in blocks:
                    add_file(f"BLOCKS/{b['block_id']}.json", json.dumps(b, indent=2), "application/json")
                add_file("BLOCKS/chain_index.json", json.dumps(chain_index, indent=2), "application/json")
                
                # KEYS
                add_file("KEYS/public_key.b64", self.config.public_key_b64, "text/plain")
                
                # VERIFY
                add_file("VERIFY/omnix_atf_verify.py", verifier_script, "text/x-python")
                add_file("VERIFY/verify_all.sh", verify_all_sh, "text/x-shellscript")
                
                # CUSTODY
                add_file("CUSTODY/evidence_custody_log.json", json.dumps(custody_log, indent=2), "application/json")
                
                # REPORT (Store uncompressed)
                zf.writestr("REPORT/forensic_report.html", html_report.encode("utf-8"), zipfile.ZIP_STORED)
                files_metadata.append({
                    "path": "REPORT/forensic_report.html",
                    "sha256": self._sha256(html_report.encode("utf-8")),
                    "size_bytes": len(html_report.encode("utf-8")),
                    "media_type": "text/html"
                })
                
                # README
                add_file("META/README.txt", readme_txt, "text/plain")

            # 5. Manifest
            span_earliest = blocks[0]["creation_timestamp_ns"] if blocks else 0
            span_latest = blocks[-1]["creation_timestamp_ns"] if blocks else 0
            head_block = blocks[-1] if blocks else {"block_id": "NONE", "canonical_hash": "sha256:" + "0"*64}
            
            manifest = {
                "manifest_version": "oep-1.0",
                "package_id": self.package_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "generator": "OMNIX Evidence Archive Pipeline",
                "generator_version": "1.0.0",
                "algorithms": {
                    "hash": "sha256-v1",
                    "signature": "ML-DSA-65 (FIPS 204)",
                    "merkle": "sha256-v1 sorted-join"
                },
                "chain": {
                    "head_block_id": head_block["block_id"],
                    "head_block_hash": head_block["canonical_hash"],
                    "genesis_sentinel": "0" * 64,
                    "block_count": len(blocks),
                    "span_ns": {"earliest": span_earliest, "latest": span_latest}
                },
                "evidence": {
                    "total_artifacts": sum(b.get("artifact_count", 0) for b in blocks),
                    "evidence_classes": sorted(list(set(c for b in blocks for c in b.get("evidence_classes", [])))),
                    "immutable_only": True
                },
                "custody": {
                    "entry_count": len(custody_log),
                    "log_sha256": self._sha256(json.dumps(custody_log, indent=2).encode("utf-8"))
                },
                "public_key": {
                    "algorithm": "ML-DSA-65 (FIPS 204)",
                    "fingerprint": "sha256:" + self._sha256(base64.b64decode(self.config.public_key_b64))[:32],
                    "file": "KEYS/public_key.b64"
                },
                "files": [], # Will fill after signature
                "signature_metadata": {
                    "signed_object": "canonical_manifest_hash",
                    "algorithm": "ML-DSA-65 (FIPS 204)",
                    "signed_at": datetime.now(timezone.utc).isoformat()
                }
            }
            
            # Temporary files list for manifest hashing
            manifest["files"] = sorted(files_metadata, key=lambda x: x["path"])
            
            # Signature
            package_signature = {
                "package_id": self.package_id,
                "canonical_manifest_hash": "sha256:" + self._sha256(self._canonical_json(manifest)),
                "pqc_signature": None,
                "pqc_algorithm": "ML-DSA-65 (FIPS 204)",
                "public_key_fingerprint": manifest["public_key"]["fingerprint"],
                "signed_at": manifest["signature_metadata"]["signed_at"]
            }
            
            if self.config.secret_key_b64:
                sig_bytes = self._sign_with_dilithium(
                    package_signature["canonical_manifest_hash"], self.config.secret_key_b64
                )
                if sig_bytes:
                    package_signature["pqc_signature"] = base64.b64encode(sig_bytes).decode("utf-8")
            
            # Finalize manifest and signature files
            sig_content = json.dumps(package_signature, indent=2)
            sig_bytes = sig_content.encode("utf-8")
            sig_metadata = {
                "path": "SIGNATURE/package_signature.json",
                "sha256": self._sha256(sig_bytes),
                "size_bytes": len(sig_bytes),
                "media_type": "application/json"
            }
            manifest["files"].append(sig_metadata)
            manifest["files"] = sorted(manifest["files"], key=lambda x: x["path"])
            
            # Add manifest.json metadata to its own files list (recursive integrity)
            manifest_content = json.dumps(manifest, indent=2)
            manifest_bytes = manifest_content.encode("utf-8")
            manifest_metadata = {
                "path": "META/manifest.json",
                "sha256": self._sha256(manifest_bytes),
                "size_bytes": len(manifest_bytes),
                "media_type": "application/json"
            }
            # Replace placeholder or add
            manifest["files"] = [f for f in manifest["files"] if f["path"] != "META/manifest.json"]
            manifest["files"].append(manifest_metadata)
            manifest["files"] = sorted(manifest["files"], key=lambda x: x["path"])
            
            # Final re-serialization
            manifest_content = json.dumps(manifest, indent=2)
            
            # 6. Re-create ZIP with final files
            with zipfile.ZipFile(oep_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # Add all files from buffer and the new ones
                zf.writestr("META/manifest.json", manifest_content)
                zf.writestr("SIGNATURE/package_signature.json", sig_content)
                
                # Copy from buffer
                buffer.seek(0)
                with zipfile.ZipFile(buffer, "r") as zf_old:
                    for name in zf_old.namelist():
                        if name not in ["META/manifest.json", "SIGNATURE/package_signature.json"]:
                            zf.writestr(name, zf_old.read(name), compress_type=zf_old.getinfo(name).compress_type)

            return OEPResult(
                success=True,
                package_id=self.package_id,
                oep_path=oep_path,
                manifest=manifest,
                errors=[],
                package_size_bytes=oep_path.stat().st_size
            )

        except Exception as e:
            logger.exception("Failed to generate OEP")
            return OEPResult(False, self.package_id, None, None, [str(e)], 0)

    def _sign_with_dilithium(self, message: str, secret_key_b64: str) -> Optional[bytes]:
        try:
            from pqc.sign import dilithium3 as dil
            sk = base64.b64decode(secret_key_b64)
            sig = dil.sign(message.encode("utf-8"), sk)
            return sig
        except Exception:
            try:
                from omnix_core.security.crypto_providers import get_active_provider
                provider = get_active_provider()
                sk = base64.b64decode(secret_key_b64)
                sig = provider.sign(message.encode("utf-8"), sk)
                return sig
            except Exception:
                return None

    def _generate_html_report(self, blocks: List[Dict], custody_log: List[Dict]) -> str:
        # Simplified HTML report based on ADR-165 requirements
        rows = ""
        for b in blocks:
            rows += f"""
            <tr>
                <td>{b['block_id']}</td>
                <td>{datetime.fromtimestamp(b['creation_timestamp_ns']/1e9, tz=timezone.utc).isoformat()}</td>
                <td>{b['artifact_count']}</td>
                <td><code>{b['canonical_hash'][:20]}...</code></td>
                <td>{'✅ Signed' if b.get('pqc_signature') else '⚠️ Unsigned'}</td>
            </tr>
            """
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>OMNIX Forensic Verification Report</title>
    <style>
        body {{ font-family: 'Inter', sans-serif; background-color: #0A1628; color: #e2e8f0; margin: 0; padding: 40px; }}
        .container {{ max-width: 1000px; margin: auto; }}
        header {{ border-bottom: 2px solid #C9A227; padding-bottom: 20px; margin-bottom: 40px; }}
        h1 {{ color: #C9A227; margin: 0; }}
        .badge {{ background: #C9A227; color: #0A1628; padding: 4px 12px; border-radius: 4px; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #0D1E38; }}
        th {{ color: #C9A227; text-transform: uppercase; font-size: 12px; letter-spacing: 1px; }}
        code {{ background: #0D1E38; padding: 2px 4px; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>OMNIX QUANTUM LTD — Forensic Reconstruction Report</h1>
            <p>Package ID: <span class="badge">{self.package_id}</span></p>
        </header>
        
        <section>
            <h2>Executive Summary</h2>
            <p>This report documents the verification and reconstruction of the governance evidence chain for package <b>{self.package_id}</b>. This package contains {len(blocks)} COLD blocks and {len(custody_log)} custody events.</p>
        </section>

        <section>
            <h2>Block Chain Table</h2>
            <table>
                <thead>
                    <tr>
                        <th>Block ID</th>
                        <th>Created At (UTC)</th>
                        <th>Artifacts</th>
                        <th>Canonical Hash</th>
                        <th>PQC Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </section>
        
        <footer>
            <p style="margin-top: 40px; font-size: 12px; color: #94a3b8;">Generated by OMNIX Evidence Archive Pipeline v1.0.0 · {datetime.now(timezone.utc).isoformat()}</p>
        </footer>
    </div>
</body>
</html>
        """
        return html

    def _generate_verify_sh(self) -> str:
        return """#!/usr/bin/env bash
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
"""

    def _generate_readme(self) -> str:
        return f"""OMNIX Evidence Package (OEP)
Package ID: {self.package_id}
Generated: {datetime.now(timezone.utc).isoformat()}

This package contains cryptographically sealed governance evidence.

VERIFICATION INSTRUCTIONS:
1. Ensure Python 3.10+ is installed.
2. Install the PQC library: pip install pypqc
3. Run the verification script:
   cd VERIFY/ && bash verify_all.sh

Independent verifier tool is located at VERIFY/omnix_atf_verify.py.

OMNIX QUANTUM LTD
"""
