# ADR-040: Public Governance Sandbox ("Try OMNIX")

**Status**: Accepted
**Date**: 2026-03-15
**Decision Makers**: Harold Nunes (Solo Founder & CEO)

## Context

OMNIX needed a public-facing, no-authentication demonstration that runs the **real** 8-checkpoint governance pipeline — not a frontend simulation. Investors, prospects, and the public should be able to:

1. Describe any high-stakes decision scenario in plain text (English or Spanish)
2. Watch the real governance pipeline evaluate it checkpoint by checkpoint
3. Receive a PQC-signed, publicly verifiable receipt

This serves both as a product demo for and as a credibility differentiator: the sandbox runs the same engine validated across production evaluation cycles.

## Decision

### Architecture

- **Flask Blueprint**: `omnix_dashboard/blueprints/public_sandbox.py`
- **React Page**: `omnix_web/src/pages/PublicGovernanceSandbox.tsx`
- **Route**: `/try` (public, no auth)
- **API Endpoint**: `POST /api/public/sandbox/evaluate`
- **Examples Endpoint**: `GET /api/public/sandbox/examples`

### Flow

1. User submits free-form text (max 500 chars) via React UI
2. Gemini AI (2.5 Flash) interprets the scenario into 8 normalized governance signals (0-100)
3. `GovernanceEvaluationEngine` runs the real 8-checkpoint pipeline
4. `DecisionReceiptEngine` generates a PQC-signed receipt
5. Receipt stored in `decision_receipts` table with `client_id='PUBLIC'`, `domain='public_sandbox'`
6. Receipt verifiable at Railway verification server: `/verify/{receipt_id}`
7. Response includes checkpoint-by-checkpoint results, AI reasoning, and receipt metadata

### Fail-Closed Behavior

If receipt generation or storage fails, the evaluation returns a 500 error. No evaluation is reported as successful without a stored, verifiable receipt.

### Rate Limiting

5 requests per minute per IP address. In-memory rate limiter (suitable for single-instance deployment).

### Security

- No authentication required (public endpoint)
- Input truncated at 500 characters
- Rate limited to prevent Gemini API abuse
- No internal data exposed — only governance decision + public receipt metadata
- Receipts stored with `PUBLIC` client_id to separate from production evaluations

### Import Strategy

Uses `importlib.util.spec_from_file_location()` to load `GovernanceEvaluationEngine` and `DecisionReceiptEngine` directly, bypassing `omnix_core/__init__.py` which triggers `TradingSystem` initialization and `TELEGRAM_BOT_TOKEN` validation.

## Consequences

- Public users can experience the real OMNIX governance pipeline
- Every sandbox evaluation generates a real, verifiable PQC-signed receipt
- Gemini API costs incurred per evaluation (mitigated by rate limiting)
- Sandbox receipts distinguishable from production by `client_id='PUBLIC'`
