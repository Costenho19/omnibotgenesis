# ADR-169: ATF Connector Fail-Open Admission Semantic

**Status:** ACCEPTED  
**Date:** 2026-05-16  
**Authors:** Harold Nunes — OMNIX QUANTUM LTD  
**Supersedes:** —  
**Related:** ADR-156 (Agent Trust Fabric), ADR-157 (Temporal Authority), ADR-159 (Runtime Continuity)

---

## Context

The `ATFConnector.admit()` method (introduced in ADR-156) bridges the governance decision pipeline with the Agent Trust Fabric. Its job is to resolve the agent's Delegation Receipt, issue a Temporal Admissibility Record (TAR), and return an `ATFContext` embedding proof that the agent was authorized at the exact nanosecond of evaluation.

A critical design question arises: **what happens when ATF admission fails?**

Failure modes include:
- Database unavailable (PostgreSQL unreachable)
- `omnix_core` not importable in the deployment environment
- DR not found (agent ID unknown to the lattice)
- TAR issuance times out
- PQC signing key unavailable

### Two possible designs

**Option A — Fail-closed (hard gate):**  
If ATF admission fails for any reason, the governance evaluation is blocked. No receipt is issued. The pipeline halts until ATF is operational.

**Option B — Fail-open (non-blocking, annotated):**  
ATF admission is attempted. If it fails, the evaluation proceeds without ATF context. The resulting receipt carries `atf_context.admission_status = "NOT_PRESENT"` to record that ATF was absent. The evaluation is not blocked.

---

## Decision

### Option B — Fail-Open with Mandatory Annotation

`ATFConnector.admit()` is **non-blocking by design**. The governance pipeline always produces a receipt. ATF failure is annotated, not silencing.

```python
# ATFConnector.admit() contract (normative):
#
# Returns: ATFContext (always — never raises to caller)
#   - admission_status = "ADMITTED"     → ATF validated, TAR issued
#   - admission_status = "REJECTED"     → ATF ran, agent failed validation
#   - admission_status = "NOT_PRESENT"  → ATF unavailable / not configured
#
# The caller (gov_blueprint.py) reads admission_status and:
#   - Embeds it in the governance receipt
#   - Applies ATF-gated logic only when admission_status == "ADMITTED"
```

### Rationale

#### 1. Governance availability is a first-order requirement

OMNIX governance receipts are issued for high-stakes decisions. A transient database outage in the ATF layer should not prevent a governance evaluation from completing. The receipt without ATF context has full forensic value for the decision itself — it simply lacks the agent trust proof layer.

#### 2. "NOT_PRESENT" is not a silent failure

The `admission_status = "NOT_PRESENT"` field in the receipt is an explicit, PQC-signed, forensically immutable record of ATF absence. Auditors can query all receipts where `atf_context.admission_status != "ADMITTED"` to identify evaluations that lacked agent trust proof. This is more auditable than a hard block that produces no receipt at all.

#### 3. REJECTED is not equivalent to NOT_PRESENT

The current implementation correctly distinguishes:
- `REJECTED`: ATF ran and explicitly denied the agent. The pipeline still proceeds, but the receipt records the rejection. **This is the case that may require hardening** — see invariant below.
- `NOT_PRESENT`: ATF was not reachable. Infrastructure concern, not a trust concern.

#### 4. Consistency with ATF-Stack availability model

ADR-159 (Runtime Continuity) and ADR-160 (RCR Performance Optimization) both accept degraded-mode operation. The ATF stack as a whole is designed for graceful degradation under infrastructure stress. Fail-open at the connector level is consistent with this model.

---

## Invariant

**FAO-INV-001 (Fail-Open Annotation):**  
Every governance receipt MUST carry an `atf_context` field. If ATF admission was not completed (for any reason), `atf_context.admission_status` MUST be set to `"NOT_PRESENT"` or `"REJECTED"` — never omitted. Receipts without an `atf_context` field are malformed.

**FAO-INV-002 (REJECTED annotation):**  
When `admission_status = "REJECTED"`, the receipt MUST record the rejection reason in `atf_context.rejection_reason`. Systems consuming governance receipts MAY apply additional policy based on this field (e.g., require human review for REJECTED evaluations).

**FAO-INV-003 (No silent admission):**  
`ATFConnector.admit()` MUST NOT return `admission_status = "ADMITTED"` if the TAR was not successfully issued and persisted (or persisted to the in-memory store in TESTING mode). Admission without a TAR is a protocol violation.

---

## Future consideration: Configurable fail-closed mode

For deployments where agent governance is mandatory (e.g., regulated financial verticals where every AI action must be provably authorized), a future `ATF_FAIL_CLOSED=true` environment variable MAY be introduced to change `ATFConnector.admit()` behavior: any `NOT_PRESENT` result would cause the pipeline to halt rather than continue.

This is explicitly **not the default** — it would require operator opt-in and is only appropriate where ATF infrastructure reliability can be guaranteed.

**ADR to track this:** Will be filed when the regulated-vertical deployment profile is defined.

---

## Consequences

**Positive:**
- Governance pipeline availability is maximized
- ATF failures are forensically recorded, not lost
- Architecture is consistent across the fail-open ATF stack
- Auditors can detect ATF-absent receipts retroactively

**Negative:**
- REJECTED evaluations still produce governance receipts. If a downstream system relies on those receipts without checking `admission_status`, it may act on an evaluation issued by an unauthorized agent.

**Mitigation:**  
All governance receipt consumers MUST check `atf_context.admission_status` before acting on ATF-gated decisions. This requirement is enforced in `gov_blueprint.py` (line 373: `atf.get("admission_status") == "ADMITTED"`). SDK documentation must reflect this contract.

---

## References

- `omnix_core/agents/atf/atf_connector.py` — implementation  
- `omnix_web/api/gov_blueprint.py` line 373 — caller-side check  
- ADR-156 — Agent Trust Fabric  
- ADR-157 — Temporal Authority  
- ADR-159 — Runtime Governance Continuity  
- RFC-ATF-1 §4 — ATF admission contract  
- Architect Review — May 2026 (OMNIX Institutional Sprint)

---

*OMNIX QUANTUM LTD · Harold Nunes · 2026-05-16*
