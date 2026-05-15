import sys
import os
import importlib.util
import json
import logging
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pathlib import Path
import tempfile
import io

# Bootstrap omnix_core
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WORKSPACE_ROOT = os.path.dirname(BASE_DIR)
if _WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, _WORKSPACE_ROOT)

from omnix_core.evidence.oep_generator import OEPGenerator, OEPConfig

logger = logging.getLogger("OMNIX.ForensicAPI")

forensic_bp = Blueprint('forensic_bp', __name__)

# Note: Limiter is usually initialized in server.py, but we'll use a local one if needed 
# or assume the main app will handle it. Blueprint-level limiting:
# We don't have the 'limiter' object here, but we can define it if server.py exports it.
# For now, we'll just define the routes.

def _load_verifier():
    """Load the standalone verifier tool dynamically."""
    verifier_path = os.path.join(_WORKSPACE_ROOT, "docs", "zenodo", "submission_package", "omnix_atf_verify.py")
    if not os.path.exists(verifier_path):
        logger.error(f"Verifier not found at {verifier_path}")
        return None
    
    spec = importlib.util.spec_from_file_location("omnix_atf_verify", verifier_path)
    if spec is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules["omnix_atf_verify"] = module
    if spec.loader:
        spec.loader.exec_module(module)
    return module

verifier = _load_verifier()

@forensic_bp.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        "status": "ok",
        "verifier_version": "1.1.0",
        "algorithms": ["ML-DSA-65"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@forensic_bp.route('/verify', methods=['POST'])
def verify_block():
    """
    Authoritative server-side verification (Plane 2).
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing request body", "verdict": "INCOMPLETE"}), 400
        
        block = data.get("block")
        public_key_b64 = data.get("public_key_b64")
        predecessor_block = data.get("predecessor_block")
        
        if not block:
            return jsonify({"error": "Missing block data", "verdict": "INCOMPLETE"}), 400
        
        if not verifier:
            return jsonify({"error": "Verifier module unavailable", "verdict": "INCOMPLETE"}), 500
        
        # Call standalone verifier's verify_archive_block
        # Note: verify_archive_block(block, public_key_override=None, verify_chain=False, predecessor_block=None)
        
        verify_chain = predecessor_block is not None
        
        result = verifier.verify_archive_block(
            block,
            public_key_override=public_key_b64,
            verify_chain=verify_chain,
            predecessor_block=predecessor_block
        )
        
        # Convert VerificationReport to dict
        checks = {
            "merkle_valid": result.merkle_valid,
            "canonical_valid": result.canonical_valid,
            "chain_valid": result.chain_valid,
            "signature_valid": result.pqc_signature_valid
        }
        
        return jsonify({
            "verdict": result.verdict,
            "reasons": result.failure_reasons,
            "checks": checks,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "verifier_version": "1.1.0"
        })

    except Exception as e:
        logger.exception("Error in /api/forensic/verify")
        return jsonify({"error": str(e), "verdict": "INCOMPLETE"}), 500

@forensic_bp.route('/export', methods=['POST'])
def export_oep():
    """
    Generate and download OEP package.
    """
    try:
        # Support both JSON and form data (multipart)
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
            if 'blocks' in data:
                data['blocks'] = json.loads(data['blocks'])
            if 'custody_entries' in data:
                data['custody_entries'] = json.loads(data['custody_entries'])
        
        blocks = data.get("blocks", [])
        public_key_b64 = data.get("public_key_b64")
        secret_key_b64 = data.get("secret_key_b64")
        custody_entries = data.get("custody_entries", [])
        
        if not blocks or not public_key_b64:
            return jsonify({"error": "Missing blocks or public_key_b64", "verdict": "INCOMPLETE"}), 400
            
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = OEPConfig(
                blocks=blocks,
                public_key_b64=public_key_b64,
                secret_key_b64=secret_key_b64,
                custody_log_entries=custody_entries,
                output_path=Path(tmp_dir)
            )
            
            generator = OEPGenerator(config)
            result = generator.generate()
            
            if not result.success:
                return jsonify({"error": "Package generation failed", "details": result.errors, "verdict": "INCOMPLETE"}), 500
                
            return send_file(
                str(result.oep_path),
                mimetype="application/zip",
                as_attachment=True,
                download_name=os.path.basename(str(result.oep_path))
            )

    except Exception as e:
        logger.exception("Error in /api/forensic/export")
        return jsonify({"error": str(e), "verdict": "INCOMPLETE"}), 500
