# ADR-038 — Sandbox Evaluation Module

**Status**: IMPLEMENTED — March 12, 2026  
**Author**: Harold Nunes (Founder — OMNIX Quantum)  
**Tags**: B2B, sandbox, client-experience, commercial

---

## Context

B2B clients need to test OMNIX governance evaluations before committing to production integration. Without a sandbox environment, the sales cycle is longer, adoption is slower, and clients feel uncertain about how the pipeline behaves with their specific signals.

A sandbox that uses **identical logic** to production builds confidence faster than any documentation.

## Decision

Implement a client-facing sandbox evaluation module with the following properties:

- **Same engine**: Uses `GovernanceEvaluationEngine` from `omnix_core/governance/external_evaluator.py` — identical checkpoint logic, identical thresholds (unless overridden).
- **Isolated storage**: Results stored in `sandbox_sessions` and `sandbox_evaluations` tables — never written to `decision_receipts` (production chain).
- **PQC receipt**: Each sandbox evaluation receives a `sandbox_receipt_id` (format: `OMNIX-SB-XXXXXXXX`) — authentic identifier, not on public verification chain.
- **Sessions**: Clients create named sessions (`SB-XXXXXXXXXXXXXXXXX`) to organize test runs. Sessions expire after 7 days.
- **Rate limit**: 30 evaluations/min (vs. 10/min production) — sandbox encourages exploration.
- **Evaluation cap**: 100 evaluations per session — prevents abuse.

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/governance/sandbox/sessions` | Create sandbox session |
| `GET` | `/api/governance/sandbox/sessions` | List client's sessions |
| `GET` | `/api/governance/sandbox/sessions/<id>` | Session detail + evaluations |
| `DELETE` | `/api/governance/sandbox/sessions/<id>` | Delete/reset session |
| `POST` | `/api/governance/sandbox/evaluate` | Run sandbox evaluation |
| `GET` | `/api/governance/sandbox/schema` | Signal schema documentation |

## Database Tables

```sql
sandbox_sessions (
    id, session_id, client_id, name, description,
    evaluation_count, created_at, expires_at, last_evaluation_at
)

sandbox_evaluations (
    id, evaluation_id, session_id, client_id, asset, domain,
    signals, decision, decision_score, checkpoints_passed,
    checkpoints_total, veto_chain, decision_trace,
    receipt_id, created_at
)
```

## Commercial Rationale

- Reduces sales cycle: clients self-validate before committing to production.
- Reduces support burden: clients explore edge cases without contacting OMNIX.
- Increases conversion: clients who test convert at higher rates than those who don't.
- Differentiator: no competing governance infrastructure offers client-facing sandbox.

## Files

- `omnix_dashboard/blueprints/governance_sandbox.py` — Blueprint implementation
- `omnix_dashboard/blueprints/__init__.py` — Export added
- `omnix_dashboard/app.py` — Blueprint registered

## Constraints

- Sandbox evaluations do NOT appear on `omnixquantum.net/verify` — they are isolated.
- Sandbox receipt IDs (`OMNIX-SB-*`) are distinct from production receipt IDs (`OMNIX-*`).
- Per-client threshold overrides (ADR-037) do NOT apply in sandbox (uses defaults for clean comparison).
- PAYLOAD_ENCRYPTION_KEY is not applied to sandbox signals (no production data at rest concern).
