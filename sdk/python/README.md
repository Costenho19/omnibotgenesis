# OMNIX Quantum — Python SDK

Decision governance infrastructure with post-quantum cryptographic proof.

```bash
pip install omnix-quantum
```

```python
from omnix import OmnixClient

client = OmnixClient(api_key="OMNIX-...")

receipt = client.evaluate(
    domain  = "trading",
    asset   = "BTC/USD",
    signals = {"price": 94200, "volume": 1.5, "volatility": 0.18},
)

print(receipt)
# ✅ APPROVED | OMNIX-TRD-a3f8b2c1d4e5f6a7 | 11/11 gates passed | sig: Dilithium-3 (NIST FIPS 204)
```

---

## What OMNIX does

Before a decision executes, OMNIX validates it through 11 independent governance checkpoints — and issues a cryptographically signed receipt as proof.

- **Governance verdict**: APPROVED · BLOCKED · HOLD
- **Cryptographic proof**: SHA-256 hash + Dilithium-3 signature (NIST FIPS 204)
- **Independently verifiable**: anyone can verify the receipt offline, without OMNIX
- **5-year retention**: HOT → WARM → COLD archival (MiFID II compliant)
- **10 domains live**: trading, Islamic credit, insurance, robotics, medical AI, energy, real estate, agents, stablecoin, defense

---

## Installation

```bash
pip install omnix-quantum
```

No dependencies. Requires Python ≥ 3.8.

---

## Quick start

### Basic evaluation

```python
from omnix import OmnixClient

client = OmnixClient(api_key="OMNIX-your-key-here")

receipt = client.evaluate(
    domain  = "islamic_credit",
    asset   = "SME-AE-001",
    signals = {
        "debt_to_income":   32,
        "collateral_ratio": 1.4,
        "sharia_compliant": True,
    },
)

print(receipt.decision)            # "APPROVED"
print(receipt.receipt_id)          # "OMNIX-CRD-a3f8b2c1d4e5f6a7"
print(receipt.content_hash)        # "sha256:3a7f1b2c..."
print(receipt.signature_algorithm) # "Dilithium-3 (NIST FIPS 204)"
print(receipt.checkpoints_passed)  # 11
print(receipt.approved)            # True
```

### One-liner

```python
from omnix import evaluate

receipt = evaluate(
    domain  = "energy",
    asset   = "SOLAR-GRID-07",
    signals = {"capacity_mw": 240, "grid_stability": 0.95, "carbon_offset": 840},
    api_key = "OMNIX-...",
)
```

### Raise on block

```python
from omnix import OmnixClient, OmnixGovernanceBlock

client = OmnixClient(api_key="OMNIX-...", raise_on_block=True)

try:
    receipt = client.evaluate(
        domain  = "trading",
        asset   = "XMR/USD",
        signals = {"price": 142, "volume": 0.5, "volatility": 0.95},
    )
except OmnixGovernanceBlock as e:
    print(f"Blocked by: {e.receipt.get('veto_chain')}")
```

---

## Supported domains

| Domain | Example asset |
|--------|--------------|
| `trading` | `BTC/USD`, `ETH/USD` |
| `islamic_credit` | `SME-AE-001`, `RETAIL-KSA-042` |
| `insurance` | `AUTO-CLAIM-887`, `HEALTH-UK-221` |
| `energy` | `SOLAR-GRID-07`, `WIND-FARM-12` |
| `robotics` | `ARM-UNIT-33`, `AGV-FLEET-07` |
| `medical` | `DRUG-APPROVAL-91`, `SURGERY-PLAN-04` |
| `real_estate` | `PROP-UAE-1042`, `REIT-UK-05` |
| `agents` | `AI-AGENT-FINANCE-01` |
| `stablecoin` | `USDC-REDEMPTION-887` |

---

## Receipt object

Every `GovernanceReceipt` has:

```python
receipt.receipt_id           # "OMNIX-TRD-a3f8b2c1d4e5f6a7"
receipt.decision             # "APPROVED" | "BLOCKED" | "HOLD"
receipt.approved             # True / False
receipt.blocked              # True / False
receipt.content_hash         # SHA-256 of canonical payload
receipt.signature            # Dilithium-3 PQC signature (base64)
receipt.signature_algorithm  # "Dilithium-3 (NIST FIPS 204)"
receipt.policy_version       # "6.5.4e"
receipt.jurisdiction         # "UAE" | "EU" | "UK" | "US" | ...
receipt.checkpoints_passed   # 11
receipt.checkpoints_blocked  # 0
receipt.veto_chain           # [] or ["AML_GATE: VETO", ...]
receipt.checkpoints          # List[CheckpointResult]
receipt.verify_url           # "https://omnixquantum.net/verify/OMNIX-TRD-..."
receipt.raw                  # Full response dict
```

---

## Verify a receipt independently

Any receipt can be verified offline — no OMNIX server needed during verification.

```bash
# Download the verifier
curl -O https://omnixquantum.net/omnix_verify.py

# Optional: install PQC library for full signature verification
pip install pqcrypto

# Verify
python omnix_verify.py receipt.json
```

Or programmatically:

```python
result = client.verify("OMNIX-TRD-a3f8b2c1d4e5f6a7")
print(result["hash_valid"])       # True
print(result["signature_valid"])  # True
print(result["overall_valid"])    # True
```

---

## Error handling

```python
from omnix import (
    OmnixAuthError,       # Invalid API key
    OmnixValidationError, # Malformed request
    OmnixGovernanceBlock, # Decision was BLOCKED (raise_on_block=True only)
    OmnixRateLimitError,  # Too many requests
    OmnixServerError,     # Server-side error
    OmnixNetworkError,    # Cannot reach OMNIX
)

try:
    receipt = client.evaluate(domain="trading", asset="BTC/USD", signals={...})
except OmnixAuthError:
    print("Check your API key")
except OmnixValidationError as e:
    print(f"Bad request: {e.errors}")
except OmnixRateLimitError as e:
    print(f"Retry after {e.retry_after}s")
except OmnixNetworkError:
    print("Cannot reach OMNIX")
```

---

## Public endpoints (no auth required)

```python
# Trust registry
registry = client.trust_registry()

# Current signing public key (RFC 8615)
pub = client.public_key()
print(pub["key"]["algorithm"])           # "dilithium3"
print(pub["key"]["fingerprint_sha256"])  # "3a7f1b2c..."
```

---

## Links

- **Docs**: [omnixquantum.net/docs](https://omnixquantum.net/docs)
- **API reference**: [omnixquantum.net/integration](https://omnixquantum.net/integration)
- **Try it live**: [omnixquantum.net/try](https://omnixquantum.net/try)
- **Independent verification**: [omnixquantum.net/verify-independently](https://omnixquantum.net/verify-independently)
- **Trust registry**: [omnixquantum.net/api/trust/registry](https://omnixquantum.net/api/trust/registry)
- **DID document**: `did:web:omnixquantum.net`

---

## License

MIT — OMNIX Quantum Ltd · omnixquantum.net
