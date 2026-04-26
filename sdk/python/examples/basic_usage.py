"""
OMNIX SDK — Basic Usage Examples
=================================
pip install omnix-quantum
"""

from omnix import OmnixClient, OmnixGovernanceBlock

API_KEY = "OMNIX-your-key-here"

client = OmnixClient(api_key=API_KEY)

# ── Example 1: Trading decision ────────────────────────────────────────────

receipt = client.evaluate(
    domain  = "trading",
    asset   = "BTC/USD",
    signals = {
        "price":      94200,
        "volume":     1.5,
        "volatility": 0.18,
    },
)

print(receipt)
print(f"Decision     : {receipt.decision}")
print(f"Receipt ID   : {receipt.receipt_id}")
print(f"Hash         : {receipt.content_hash}")
print(f"Signature    : {receipt.signature_algorithm}")
print(f"Checkpoints  : {receipt.checkpoints_passed}/11 passed")
print(f"Verify at    : {receipt.verify_url}")


# ── Example 2: Islamic credit decision ────────────────────────────────────

receipt = client.evaluate(
    domain  = "islamic_credit",
    asset   = "SME-AE-001",
    signals = {
        "debt_to_income":   32,
        "collateral_ratio": 1.4,
        "sharia_compliant": True,
    },
)
print(f"\nCredit: {receipt}")


# ── Example 3: Raise on block ─────────────────────────────────────────────

strict_client = OmnixClient(api_key=API_KEY, raise_on_block=True)

try:
    receipt = strict_client.evaluate(
        domain  = "trading",
        asset   = "XMR/USD",
        signals = {"price": 142, "volume": 0.5, "volatility": 0.95},
    )
except OmnixGovernanceBlock as e:
    print(f"\nBLOCKED: {e}")
    print(f"Veto chain: {e.receipt.get('veto_chain')}")


# ── Example 4: Verify a receipt independently ──────────────────────────────

result = client.verify("OMNIX-TRD-a3f8b2c1d4e5f6a7")
print(f"\nVerification: hash_valid={result.get('hash_valid')} | sig_valid={result.get('signature_valid')}")


# ── Example 5: Fetch public trust registry (no auth needed) ───────────────

registry = client.trust_registry()
print(f"\nTrust registry: {len(registry.get('issuers', []))} issuer(s)")


# ── Example 6: Fetch active public key (no auth needed) ───────────────────

pub = client.public_key()
print(f"\nPublic key algorithm : {pub.get('key', {}).get('algorithm')}")
print(f"Key fingerprint (sha256): {pub.get('key', {}).get('fingerprint_sha256')}")
