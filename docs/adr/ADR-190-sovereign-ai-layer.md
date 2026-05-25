# ADR-190 — OMNIX Sovereign AI Layer (SAL)

**Status:** Accepted
**Author:** Harold Nunes
**Date:** 2026-05-25
**Related:** ADR-009 (Brevity First), ADR-184 (OGR), ADR-191 (Executive View)

---

## Context

OMNIX depends on three external AI providers: Google Gemini (primary), OpenAI GPT-4o,
and Anthropic Claude. This creates three classes of dependency risk:

1. **Vendor lock-in** — If any provider changes pricing, access terms, or shuts down a
   model, OMNIX governance decisions are disrupted.
2. **Sovereignty gap** — Every governance decision passes through infrastructure owned
   by Google or Microsoft. Regulated industries (defense, sovereign wealth funds, central
   banks) cannot accept this.
3. **Brand positioning** — Competitors can claim "we don't depend on Big Tech AI."
   OMNIX cannot currently make that claim.

**Competing approaches examined:**
- On-premise GPU cluster: capital-intensive, operationally complex, not viable for Replit/Railway.
- Self-hosted Ollama: requires GPU hardware, not available in current infrastructure.
- Fine-tuned proprietary model: correct long-term direction (RFC-ATF-6 corpus), but
  requires weeks of preparation.

**Solution selected:** Add **Groq** as a 4th AI provider using the Llama-3.3-70b-versatile
open-source model. Groq runs Llama-3 on proprietary LPU hardware — the model weights are
open-source (Meta license), inference is fast (500+ tok/s), and the API is OpenAI-compatible.
Add **Mistral AI** as a 5th provider (Mistral-large-latest) for European regulatory alignment.

When `OMNIX_AI_SOVEREIGN_MODE=true`, the provider chain inverts: Groq (Llama-3) leads,
followed by Mistral. Google/OpenAI/Anthropic become fallbacks only.

---

## Decision

### SAL-001: OMNIX Sovereign AI Layer

Introduce a fifth provider slot — **Groq/Llama-3** — and a sixth — **Mistral** — in the
`AIModelsManager`. The `OMNIX_AI_SOVEREIGN_MODE` environment variable controls chain order:

```
OMNIX_AI_SOVEREIGN_MODE=false (default):
  Gemini → OpenAI → Anthropic → Groq → Mistral

OMNIX_AI_SOVEREIGN_MODE=true (sovereign):
  Groq/Llama-3 → Mistral → Gemini → OpenAI → Anthropic
```

### SAL-002: Provider Identifiers

| Provider | Model | Identifier prefix | API base |
|---|---|---|---|
| Groq | llama-3.3-70b-versatile | `groq-` | https://api.groq.com/openai/v1 |
| Mistral | mistral-large-latest | `mistral-` | https://api.mistral.ai/v1 |

Both providers expose an OpenAI-compatible REST API. The Groq client reuses `AsyncOpenAI`
with `base_url` override. Mistral uses `httpx` async calls.

### SAL-003: Environment Variables

| Variable | Description | Default |
|---|---|---|
| `GROQ_API_KEY` | Groq API key | None (provider skipped if absent) |
| `MISTRAL_API_KEY` | Mistral API key | None (provider skipped if absent) |
| `OMNIX_AI_SOVEREIGN_MODE` | `true` = open-source models lead | `false` |

### SAL-004: Logging and Telemetry

Every generation call logs the provider used. In sovereign mode, the log prefix changes:
```
[AI-SOVEREIGN] PRIMARY → GROQ/LLAMA-3
```
This allows operators to audit which model class made each governance recommendation.

---

## Invariants

- **SAL-INV-001:** When `OMNIX_AI_SOVEREIGN_MODE=true`, Groq/Llama-3 MUST be attempted
  before any Big-Tech provider.
- **SAL-INV-002:** Provider absence (missing API key) MUST NOT halt the chain — the next
  available provider is used.
- **SAL-INV-003:** All providers share the same response validation logic
  (`_validate_response`). No provider receives relaxed quality standards.
- **SAL-INV-004:** The Groq and Mistral providers MUST use the same timeout (30s) and
  exponential backoff (0.5s base) as existing providers.

---

## Consequences

**Positive:**
- OMNIX can truthfully claim "sovereign mode: zero dependency on Google/OpenAI"
- Positions OMNIX competitively against UHG-Tech OMNEX, CLARIXO, and similar vendors
- Opens regulated verticals (defense, central banking) that require AI sovereignty
- Mistral's EU headquarters adds eIDAS/EU AI Act alignment narrative

**Negative:**
- Two additional API keys to manage (GROQ_API_KEY, MISTRAL_API_KEY)
- Llama-3.3-70b may produce shorter governance analyses than GPT-4o — mitigated by
  system prompt engineering

**Neutral:**
- Fine-tuning OMNIX corpus onto Llama-3 (Sovereign Level 2) remains the next step —
  tracked in RFC-ATF-6 roadmap.
