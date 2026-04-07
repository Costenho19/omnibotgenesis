# OMNIX Python SDK

Official client library for the OMNIX Decision Governance API.

## Installation

Copy `omnix_sdk.py` into your project directory. A pip package is coming soon.

## Quick Start

```python
from omnix_sdk import OmnixClient

client = OmnixClient(api_key="OMNIX-your-key-here")

result = client.evaluate({
    "signal_integrity": 75,
    "probability_score": 68,
    "risk_exposure": 42,
    "signal_coherence": 60,
    "trend_persistence": 55,
    "stress_resilience": 48,
    "logic_consistency": 65,
    "temporal_coherence": 58,
    "domain": "trading",
    "asset": "BTC/USD",
    "scenario": "Long position pre-execution — 2% capital"
})

print(result["decision"])          # "APPROVED" | "BLOCKED" | "HOLD"
print(result["receipt_id"])        # "OMNIX-a3f8e2..."
print(result["pqc_signed"])        # True
print(result["checkpoints_passed"]) # 11
```

## Signal Reference

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `signal_integrity` | int | 0–100 | Input data quality score |
| `probability_score` | int | 0–100 | Confidence in the decision |
| `risk_exposure` | int | 0–100 | Risk level — **lower is safer** |
| `signal_coherence` | int | 0–100 | Internal signal consistency |
| `trend_persistence` | int | 0–100 | Trend alignment score |
| `stress_resilience` | int | 0–100 | Resilience under stress |
| `logic_consistency` | int | 0–100 | Logical coherence |
| `temporal_coherence` | int | 0–100 | Time-context validity |
| `domain` | str | — | `trading`, `credit`, `insurance`, `robotics` |
| `asset` | str | — | Asset or entity identifier |
| `scenario` | str | — | Human-readable description |

## Methods

```python
# Evaluate a decision
client.evaluate(signals: dict) -> dict

# Get a specific receipt
client.get_receipt(receipt_id: str) -> dict

# List your receipts (paginated)
client.list_receipts(page=1, per_page=20) -> dict

# Download due diligence report
client.get_due_diligence_report(format="json") -> dict
client.get_due_diligence_report(format="pdf")  -> dict  # includes download URL

# Regulatory frameworks catalog
client.get_regulatory_catalog() -> dict
```

## Error Handling

```python
from omnix_sdk import OmnixClient, OmnixAuthError, OmnixRateLimitError, OmnixAPIError

try:
    result = client.evaluate(signals)
except OmnixAuthError:
    print("Invalid or expired API key")
except OmnixRateLimitError:
    print("Rate limit — retry after 60s")
except OmnixAPIError as e:
    print(f"API error {e}: {e}")
```

## API Key

Your key format: `OMNIX-<40 alphanumeric characters>`

Pass via constructor: `OmnixClient(api_key="OMNIX-...")` or set env var:
```bash
export OMNIX_API_KEY="OMNIX-..."
```

## Contact

- Web: https://omnixquantum.net
- Email: contacto@omnixquantum.net
