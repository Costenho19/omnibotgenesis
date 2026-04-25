# ADR-124 — Oversight Surface Engine (OSE): Governing the Quality of Human Oversight Moments

**Status:** ACCEPTED  
**Date:** 2026-04-25  
**Author:** OMNIX Quantum Ltd — Harold Alberto Nunes Rodelo  
**Scope:** `omnix_core/governance/oversight_surface.py` · `omnix_web/api/oversight_bp.py`

---

## Context

> *"Defining which decisions are allowed to exist doesn't by itself guarantee that those
> decisions remain governable once they are presented to a human. Even within admissible
> states, the way information is structured, timed and framed can still shape — and limit —
> how judgment is actually formed."*
>
> — José Luis Tudela, Founder ANTROPOLOGIC / Researcher on Operational Human Oversight
>   under the EU AI Act, 2026.

**The gap OMNIX had before this ADR:**

OMNIX governs *admissibility* (CAG, SAE, AVM, exit governance) — what decisions are
allowed to exist. But once a decision was flagged for human review, OMNIX had no control
over:

- **When** the reviewer actually saw the decision.
- **How** the information was structured when it arrived.
- **How long** the reviewer deliberated before acting.
- **Whether** the reviewer's action was substantive or a rubber-stamp.

The EU AI Act (Article 14) requires *meaningful* human oversight of high-risk AI, not
merely its theoretical availability. The OSE closes this gap by governing the oversight
moment itself.

---

## Decision

Introduce an **Oversight Surface Engine (OSE)** — a new governance module that operates
*after* a decision is produced by the OMNIX engine and *before* the human review action
is recorded. It enforces three properties:

### 1 — Deliberation Window

Minimum time (default: **30 seconds**) that must elapse between the moment the oversight
UI is presented to the reviewer (`open_session`) and when the reviewer can submit
(`submit_review`). Prevents rubber-stamping.

### 2 — Framing Governance

Required fields that must be present in the `decision_snapshot` presented to the
reviewer. Missing fields lower the Framing Score, which feeds into the EQS.

Default required fields:
- `risk_score` — quantified risk of the decision
- `domain` — governance domain (trading, medical, etc.)
- `original_decision` — AI's recommendation (APPROVED / BLOCKED / HOLD)
- `block_reason` — reason for any block/veto

### 3 — Override Friction

When a reviewer wants to override an AI's BLOCKED decision (`action=OVERRIDDEN`), a
structured justification of at least **50 characters** is mandatory. This creates an
audit trail of human reasoning and deters casual overrides.

---

## Epistemic Quality Score (EQS)

A composite metric (0.0–1.0) computed at session submission time:

```
EQS = (time_score × 0.40) + (framing_score × 0.40) + (justification_score × 0.20)

time_score         = min(1.0, deliberation_seconds / (DELIBERATION_WINDOW × 2))
framing_score      = (present required fields) / (total required fields)
justification_score = 1.0 if action ≠ OVERRIDDEN
                    = min(1.0, len(justification) / 200) if action = OVERRIDDEN
```

| Label   | EQS range |
|---------|-----------|
| HIGH    | ≥ 0.85   |
| MEDIUM  | ≥ 0.60   |
| LOW     | ≥ 0.35   |
| MINIMAL | < 0.35   |

The EQS is stored in `oversight_sessions` and is available via
`GET /api/oversight/sessions/<id>/eqs`.

---

## Design Constraints

- **Purely additive** — does not modify `decision_receipts`, `governance_overrides`,
  or any existing table. An oversight session is a metadata record *about* the oversight
  moment, complementary to existing audit chains.
- **Immutable receipt chain preserved** — same principle as `human_oversight.py` (ADR-029).
- **Optional integration** — existing governance flows are not changed. Clients opt in by
  creating an oversight session when routing a decision to human review.

---

## New Database Table

```sql
CREATE TABLE oversight_sessions (
    session_id              VARCHAR(64)  PRIMARY KEY,
    decision_id             VARCHAR(128) NOT NULL,
    reviewer_id             VARCHAR(128),
    domain                  VARCHAR(64),
    original_decision       VARCHAR(32),
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    presented_at            TIMESTAMPTZ,
    submitted_at            TIMESTAMPTZ,
    action                  VARCHAR(32),          -- CONFIRMED | OVERRIDDEN | ESCALATED
    justification           TEXT,
    deliberation_seconds    FLOAT,
    framing_score           FLOAT,
    eqs_score               FLOAT,
    status                  VARCHAR(32)  NOT NULL DEFAULT 'PENDING',
    decision_snapshot       JSONB,
    metadata                JSONB
);
```

---

## API Endpoints

All endpoints require `X-API-Key` authentication (B2B RBAC, same as `/api/governance/*`).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/oversight/sessions` | standard | Create oversight session |
| GET  | `/api/oversight/sessions` | standard | List sessions (filtered) |
| GET  | `/api/oversight/sessions/<id>` | standard | Get session details |
| POST | `/api/oversight/sessions/<id>/open` | standard | Mark presented (timer starts) |
| POST | `/api/oversight/sessions/<id>/submit` | standard | Submit review with EQS |
| GET  | `/api/oversight/sessions/<id>/eqs` | standard | EQS breakdown |
| POST | `/api/oversight/sessions/expire` | **admin** | Expire stale sessions |

### Session Lifecycle

```
PENDING → OPEN → SUBMITTED
        ↘         ↗
          EXPIRED (after SESSION_EXPIRY_HOURS = 48h)
```

---

## Regulatory Alignment

| Framework | Article / Section | How OSE addresses it |
|-----------|-------------------|----------------------|
| EU AI Act | Art. 14(4)(a) | Deliberation window ensures humans have *sufficient time* to exercise oversight |
| EU AI Act | Art. 14(4)(b) | Framing governance ensures humans are *aware of the risks* |
| EU AI Act | Art. 14(4)(c) | Override friction ensures humans can *interpret and override* with accountability |
| NIST AI RMF | GOVERN 1.7 | EQS provides measurable oversight quality metric |
| NIST AI RMF | MANAGE 4.1 | Session lifecycle enables structured human intervention |

---

## Configuration Constants

| Constant | Default | Description |
|----------|---------|-------------|
| `DELIBERATION_WINDOW_SECONDS` | 30 | Minimum open→submit time |
| `OVERRIDE_MIN_JUSTIFICATION_CHARS` | 50 | Minimum override explanation length |
| `SESSION_EXPIRY_HOURS` | 48 | PENDING/OPEN sessions expire after this |
| `FRAMING_REQUIRED_FIELDS` | 4 fields | Fields required for full framing score |

---

## Files Created

- `omnix_core/governance/oversight_surface.py` — OSE engine
- `omnix_web/api/oversight_bp.py` — Flask blueprint with 7 endpoints
- `docs/adr/ADR-124-oversight-surface-engine.md` — this document
- DB table `oversight_sessions` — created at server startup via `ensure_schema()`

## Test Coverage

- `tests/test_oversight_surface.py` — unit tests for OSE engine
- All 70 existing tests continue to pass (no regressions)

---

## Security Classification

- **Category:** Human Oversight Quality Enforcement  
- **OWASP relevance:** A09 (Logging Failures — EQS provides oversight quality audit trail)  
- **Governance layer:** Layer 0 (Infrastructure) + Layer 2 (Human Oversight)  
- **Railway production impact:** ✅ Safe — additive table + new endpoints only
