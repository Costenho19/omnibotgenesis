# Getting Started with the OMNIX Governance Runtime

5 API calls. Full 6-layer governance. ATF-BEV-Compliant.

---

## Prerequisites

- An API key provisioned via `provision_b2b_client.py`
- A governing receipt ID (from a prior `/api/governance/evaluate` call, or use
  `DEMO-RECEIPT-001` for sandbox testing)
- Base URL: your OMNIX deployment (e.g. `https://omnixquantum.net`)

---

## Step 1 — Start a governed session

```bash
curl -X POST https://omnixquantum.net/v1/govern/session/start \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{
    "agent_id": "my-finance-agent-v1",
    "governing_receipt_id": "RCP-2026-ABC123",
    "domain": "finance",
    "vertical": "investment_advisory",
    "policy_name": "mifid2-retail-client",
    "constraint_set": {
      "max_output_length": 2000,
      "max_turns": 100,
      "halt_on_keywords": ["execute trade", "wire transfer"],
      "forbidden_topics": ["guaranteed returns", "insider information"],
      "warn_on_keywords": ["leveraged product"]
    }
  }'
```

**Response:**
```json
{
  "status": "session_started",
  "session_id": "OGR-9B8A7C6D5E4F3A2B1C0D",
  "governing_receipt_id": "RCP-2026-ABC123",
  "chain_genesis_hash": "a1b2c3d4e5f6...",
  "chain_id": "CTCHC-F1E2D3C4B5A6",
  "compliance_tier": "ATF-BEV-Compliant",
  "atf_layers_active": [
    "ATF-L1-Identity",
    "ATF-L2-Delegation",
    "ATF-L3-TemporalAuthority",
    "ATF-L4-RuntimeContinuity",
    "ATF-L5-CognitiveGovernance",
    "ATF-L6-BehavioralVerification"
  ]
}
```

Save the `session_id` — you will need it for every turn.

---

## Step 2 — Record each agent turn

Before you deliver your agent's output to the user, pass it through the OGR.
If `should_halt` is `true`, **do not deliver the output**.

```bash
curl -X POST https://omnixquantum.net/v1/govern/session/OGR-.../turn \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{
    "output_text": "Based on your risk profile, diversified ETFs provide..."
  }'
```

**Response:**
```json
{
  "status": "turn_recorded",
  "session_id": "OGR-9B8A7C6D5E4F3A2B1C0D",
  "turn_index": 0,
  "bar": {
    "bar_id": "BAR-A3F2B1C4D5E6F7A8",
    "bar_status": "VALID",
    "pqc_signed": true,
    "pqc_algorithm": "ml-dsa-65"
  },
  "ccs": {
    "ccs_id": "CCS-B2C3D4E5F6A7B8C9",
    "conformance_score": 0.9750,
    "cumulative_drift": 0.0250,
    "verdict": "CONFORMANT",
    "watchdog_triggered": false
  },
  "ctchc": {
    "chain_link_hash": "f1a2b3c4d5e6..."
  },
  "should_halt": false,
  "ogr_verdict": "CONFORMANT"
}
```

**Check `should_halt` before delivering the output:**
```python
result = requests.post(f"{base_url}/v1/govern/session/{session_id}/turn",
    json={"output_text": agent_output}, headers=headers).json()

if result["should_halt"]:
    # Do NOT deliver the output.
    # Log result["halt_reason"] for audit trail.
    raise GovernanceHalt(result["halt_reason"])

# Safe to deliver
return agent_output
```

---

## Step 3 — Close the session

When the interaction ends, seal the session. This PQC-signs the complete
coherence hash chain — the proof is now immutable and offline-verifiable.

```bash
curl -X POST https://omnixquantum.net/v1/govern/session/OGR-.../close \
  -H "X-API-Key: YOUR_KEY" \
  -d '{"package_oep": false}'
```

**Response:**
```json
{
  "status": "session_closed",
  "session_status": "CLOSED",
  "turn_count": 12,
  "chain_seal": {
    "chain_id": "CTCHC-F1E2D3C4B5A6",
    "is_sealed": true,
    "seal_hash": "d1e2f3a4b5c6...",
    "pqc_sealed": true,
    "pqc_algorithm": "ml-dsa-65"
  },
  "ccs_final": {
    "avg_conformance": 0.9583,
    "cumulative_drift": 0.0500,
    "last_verdict": "CONFORMANT"
  },
  "compliance_tier": "ATF-BEV-Compliant",
  "offline_verifiable": true
}
```

---

## Step 4 — Retrieve the proof

```bash
curl https://omnixquantum.net/v1/govern/session/OGR-.../proof \
  -H "X-API-Key: YOUR_KEY"
```

The proof contains all BARs, the full CCS history, the CTCHC chain, and the
offline verification result. Store this proof for your compliance records.

---

## Step 5 — Generate a compliance report

```bash
curl https://omnixquantum.net/v1/govern/compliance/OGR-... \
  -H "X-API-Key: YOUR_KEY"
```

Returns an ATF-BEV-Compliant report with per-invariant pass/fail for all
18 BEV invariants (BEV-INV-001–018) plus OGR-INV-001. Suitable for
regulatory submission or partner audit.

---

## Python integration example

```python
import requests

BASE_URL = "https://omnixquantum.net"
HEADERS  = {"X-API-Key": "YOUR_KEY", "Content-Type": "application/json"}

class OGRClient:
    def __init__(self, agent_id: str, governing_receipt_id: str, constraint_set: dict = None):
        resp = requests.post(f"{BASE_URL}/v1/govern/session/start", headers=HEADERS, json={
            "agent_id": agent_id,
            "governing_receipt_id": governing_receipt_id,
            "constraint_set": constraint_set or {},
        }).json()
        self.session_id = resp["session_id"]
        self.genesis_hash = resp["chain_genesis_hash"]

    def govern_turn(self, output_text: str) -> str:
        """Pass agent output through OGR. Raises on HALT."""
        result = requests.post(
            f"{BASE_URL}/v1/govern/session/{self.session_id}/turn",
            headers=HEADERS,
            json={"output_text": output_text},
        ).json()
        if result.get("should_halt"):
            raise RuntimeError(f"OGR HALT: {result.get('halt_reason')}")
        return output_text

    def close(self) -> dict:
        return requests.post(
            f"{BASE_URL}/v1/govern/session/{self.session_id}/close",
            headers=HEADERS,
            json={},
        ).json()

    def get_compliance_report(self) -> dict:
        return requests.get(
            f"{BASE_URL}/v1/govern/compliance/{self.session_id}",
            headers=HEADERS,
        ).json()


# Usage
ogr = OGRClient(
    agent_id="my-agent-v1",
    governing_receipt_id="RCP-2026-ABC123",
    constraint_set={"max_turns": 50, "halt_on_keywords": ["execute trade"]},
)

for user_msg in conversation:
    agent_output = my_agent.generate(user_msg)
    safe_output = ogr.govern_turn(agent_output)  # raises if HALT
    deliver_to_user(safe_output)

result = ogr.close()
print(f"Session sealed. PQC seal: {result['chain_seal']['seal_hash']}")

report = ogr.get_compliance_report()
print(f"Compliance: {report['overall_pass']} — {report['compliance_tier']}")
```

---

## What you get per session

| Artifact            | Count          | PQC-signed | Offline verifiable |
|--------------------|---------------|:----------:|:-----------------:|
| Behavioral Anchor Records (BAR) | 1 per turn | ✅ | ✅ |
| Constraint Conformance Signals (CCS) | 1 per turn | — | via chain hash |
| CTCHC links | 1 per turn | — | ✅ (hash walk) |
| CTCHC seal | 1 per session | ✅ | ✅ |
| Compliance report | on demand | — | from stored artifacts |

---

## Troubleshooting

| Error                                 | Cause                                  | Fix                                        |
|--------------------------------------|----------------------------------------|--------------------------------------------|
| `governing_receipt_id is required`   | Missing receipt in start call          | Provide a valid receipt ID                 |
| `OGR session not found`              | Wrong session_id                       | Use session_id from start response         |
| `Session is not ACTIVE`              | Halted or closed session               | Start a new session                        |
| `Chain not initialized`              | Bug: turn before start                 | Always call start before turn              |
| `should_halt: true`                  | Policy violation in output             | Do not deliver output. Log halt_reason.    |
| `Invalid status value`               | `?status=` param not in allowlist      | Use one of: `ACTIVE`, `CLOSED`, `HALTED`, `EXPIRED` |

---

## Security and Correctness Guarantees

The OGR has been through a structured post-deployment audit (ADR-185).
The following guarantees hold unconditionally:

**1. Full lifecycle works without a database.**  
The engines maintain in-memory caches (`_chain_cache`, `_links_cache`,
`_drift_cache`, `_session_cache`). You can run start → turn(s) → close → proof
with no `DATABASE_URL` — all results are correct. Use `DATABASE_URL` in
production for persistence across restarts.

**2. `turn_count` is always accurate.**  
The session object tracks `turn_count` incrementally on every `record_turn()`
call. It is never recomputed from a DB query. The `close_session` and `get_proof`
responses both read from this value.

**3. `get_session()` reflects closed/halted state immediately.**  
Cache is updated synchronously after every state-mutating operation — no
window where a caller sees stale `ACTIVE` status after a close.

**4. `overall_pass: true` in the compliance report is trustworthy.**  
It gates on all 19 invariants: 18 BEV (INV-001–018) and OGR-INV-001. No
invariant is silently excluded.

**5. All input parameters are validated at the API boundary.**  
`?status=`, `?artifact_type=`, and all required JSON body fields are validated
before reaching any engine. Invalid inputs return HTTP 400 with a descriptive
error — never silent wrong-output.

---

*OMNIX Governance Runtime Getting Started · v1.1.0 · OMNIX QUANTUM LTD · May 2026*  
*ADR-184 (amended by ADR-185) · RFC-ATF-1 through RFC-ATF-6*
