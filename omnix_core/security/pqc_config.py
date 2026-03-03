"""
OMNIX — PQC Assurance Tier Configuration
=========================================
Centralizes cryptographic signing level selection.
Level is set via PQC_SIGNING_LEVEL environment variable.

Default:  Level 3 (ML-DSA-65 / Dilithium-3) — enterprise-grade baseline
Optional: Level 5 (ML-DSA-87 / Dilithium-5) — high-assurance / national-grade

ADR-031 — PQC Configurable Assurance Tiers
"""

import os
import logging

_logger = logging.getLogger("OMNIX.PQC.Config")

_raw_level = os.environ.get("PQC_SIGNING_LEVEL", "3").strip()

try:
    _requested_level = int(_raw_level)
    if _requested_level not in (3, 5):
        _logger.warning(
            f"PQC_SIGNING_LEVEL={_raw_level!r} is not a supported tier (3 or 5). "
            "Failing closed to Level 3 (ML-DSA-65)."
        )
        _requested_level = 3
except ValueError:
    _logger.warning(
        f"PQC_SIGNING_LEVEL={_raw_level!r} is not a valid integer. "
        "Failing closed to Level 3 (ML-DSA-65)."
    )
    _requested_level = 3

SIGNING_LEVEL: int = _requested_level

if SIGNING_LEVEL == 5:
    try:
        from pqc.sign import dilithium5 as SIGNING_MODULE
        ALGORITHM_NAME = "Dilithium-5 (ML-DSA-87)"
        ML_DSA_VARIANT = "ML-DSA-87"
        SECURITY_LEVEL_DESC = "NIST Level 5 (~256-bit classical security equivalent)"
        KEY_SIZES = {
            "public_key": "2592 bytes",
            "secret_key": "4864 bytes",
            "signature": "~4627 bytes",
        }
        NIST_STANDARD = "FIPS 204 — ML-DSA-87 (internal reference)"
        _logger.info("PQC Signing Level: 5 — ML-DSA-87 (Dilithium-5) [High-Assurance]")
    except ImportError:
        _logger.error(
            "dilithium5 not available in pypqc. Failing closed to Level 3."
        )
        SIGNING_LEVEL = 3

if SIGNING_LEVEL == 3:
    try:
        from pqc.sign import dilithium3 as SIGNING_MODULE
        ALGORITHM_NAME = "Dilithium-3 (ML-DSA-65)"
        ML_DSA_VARIANT = "ML-DSA-65"
        SECURITY_LEVEL_DESC = "NIST Level 3 (~192-bit classical security equivalent)"
        KEY_SIZES = {
            "public_key": "1952 bytes",
            "secret_key": "4000 bytes",
            "signature": "~3309 bytes",
        }
        NIST_STANDARD = "FIPS 204 — ML-DSA-65 (internal reference)"
        _logger.info("PQC Signing Level: 3 — ML-DSA-65 (Dilithium-3) [Enterprise Baseline]")
    except ImportError:
        SIGNING_MODULE = None  # type: ignore
        ALGORITHM_NAME = "Dilithium-3 (ML-DSA-65)"
        ML_DSA_VARIANT = "ML-DSA-65"
        SECURITY_LEVEL_DESC = "NIST Level 3 (~192-bit classical security equivalent)"
        KEY_SIZES = {
            "public_key": "1952 bytes",
            "secret_key": "4000 bytes",
            "signature": "~3309 bytes",
        }
        NIST_STANDARD = "FIPS 204 — ML-DSA-65 (internal reference)"
        _logger.warning("pypqc not available — PQC signing disabled.")

AVAILABLE_TIERS = {
    3: {
        "label": "Enterprise Baseline",
        "algorithm": "Dilithium-3 (ML-DSA-65)",
        "ml_dsa": "ML-DSA-65",
        "security_desc": "~192-bit classical security equivalent",
        "use_case": "Capital-sensitive environments, institutional governance, enterprise-grade assurance",
        "env_var": "PQC_SIGNING_LEVEL=3",
    },
    5: {
        "label": "High-Assurance",
        "algorithm": "Dilithium-5 (ML-DSA-87)",
        "ml_dsa": "ML-DSA-87",
        "security_desc": "~256-bit classical security equivalent",
        "use_case": "National-grade deployments, state-secrecy environments, maximum assurance configurations",
        "env_var": "PQC_SIGNING_LEVEL=5",
    },
}
