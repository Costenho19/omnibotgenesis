# OMNIX — Decision Governance Infrastructure

## Overview
OMNIX is a domain-agnostic Decision Governance Infrastructure designed to govern high-stakes automated decisions across various sectors such as digital asset trading, Islamic credit, global insurance claims, and robotics pre-execution safety. It employs a consistent 11-checkpoint pipeline (CP-1 to CP-11), issuing a post-quantum cryptographically signed receipt for every decision.

Harold Nunes — Solo Founder & CEO. Semifinalista Eureka GCC Dubai 2026. Raising $500K pre-seed at $3M pre-money valuation.

---

## User Preferences
### Communication
Simple, everyday language (Spanish primary — English only for external drafts).

### CRITICAL AGENT RULES (MANDATORY — ALWAYS)

> **RULE 1 — LANGUAGE**: Comunicar siempre en español con el usuario. Redactar en inglés solo cuando el usuario pida borradores para terceros (ej. emails a partners, inversores).

> **RULE 2 — WARN BEFORE IRREVERSIBLE ACTIONS**: Before the user performs any irreversible action (publishing to Zenodo, SSRN, uploading to Railway, sending emails, sharing on LinkedIn, deploying), proactively review EVERYTHING that might affect that action and warn BEFORE. Not after. Never after.

> **RULE 3 — PROACTIVE REVIEW**: Before considering any task finished, check for errors, inconsistencies, or pending items the user should know about. Do not wait for the user to discover them. If something could cause a future problem, say it now.

---

## Deployment Policy (CRITICAL)
| Environment | Purpose |
|-------------|---------|
| **Railway** | PRODUCTION (24/7) — bot + web live permanently |
| **Replit** | DEVELOPMENT — code editing and tests only |

**NEVER run the bot on Replit and Railway simultaneously** — Telegram allows only ONE active connection per token.

### Bot Testing Protocol (MANDATORY)
Every time the bot is activated on Replit for testing:
1. Perform the necessary tests.
2. **STOP the bot workflow BEFORE ending the session.**
3. Verify that the workflow is stopped.

---

## Railway Production Architecture (CRITICAL — confirmed Apr 2026)

Railway project has **4 services**:

| Service | URL | What it runs |
|---------|-----|-------------|
| **stellar-hope** | omnixquantum.net | React frontend + Flask API |
| **omnibotgenesis** | omnibotgenesis-production… | Telegram bot |
| **Redis** | internal | Cache / state |
| **Postgres** | internal | Main DB |

### stellar-hope — How it works
- **Root Directory in Railway**: `/omnix_web`
- **Config**: `omnix_web/nixpacks.toml`
- **Start command**: `gunicorn api.server:app --bind 0.0.0.0:$PORT`
- **Flask entry point**: `omnix_web/api/server.py` (imports `api.sandbox`)

> **⚠ CRITICAL**: When fixing web API bugs, edit `omnix_web/api/` — NOT `omnix_dashboard/`. The `omnix_dashboard/` folder is NOT used in Railway production web.

### Key web API files
| File | Purpose |
|------|---------|
| `omnix_web/api/server.py` | Main Flask app — all `/api/*` routes |
| `omnix_web/api/sandbox.py` | 11-checkpoint public governance sandbox |
| `omnix_web/nixpacks.toml` | Railway build + start config |
| `omnix_web/public/whitepaper.pdf` | Whitepaper — persists across builds |

---

## System Architecture

### Core Components
OMNIX employs a hexagonal architecture with an AutoTradingBot, Non-Markovian Memory Kernel, and a 6-Tier Veto System (Coherence Engine). Key capabilities: AI-first command detection, Multilingual Prompt Architecture, Anti-Servile Post-Processing Filter, AI Risk Guardian, CAES, Decision Engine, Monte Carlo VETO Engine, RMS Enforcement, SIV, FTI, RCK, EGL. Multi-Agent Governance System with Hybrid Cryptography (X25519 + Kyber-768 via HKDF), Crypto-Agility Layer, and Quantum-Secure Decision Receipts with RFC 3161-style internal timestamps and rolling Merkle root. All checkpoints are fail-closed.

### 11-Checkpoint Pipeline — matches Zenodo/SSRN published paper exactly (CP-1 to CP-11)

| CP | Name | Signal | Threshold | If Fails |
|----|------|--------|-----------|---------|
| CP-1 | Signal Integrity Validator (SIV) | signal_integrity | ≥ 60 | Rejected at entry — pipeline never opens |
| CP-2 | Probability Assessment | probability_score | ≥ 50 | Blocked — insufficient confidence |
| CP-3 | Risk Evaluation | risk_exposure | ≤ 65 | Blocked — risk limit exceeded |
| CP-4 | Coherence Engine | signal_coherence | ≥ 55 | HOLD — human review (DCI ≥ 70) |
| CP-5 | Trend Validator | trend_persistence | ≥ 50 | Blocked — regime contradiction |
| CP-6 | Stress Testing | stress_resilience | ≥ 35 | Blocked — fails under stress |
| CP-7 | Ethics & Domain Gate | logic_consistency | ≥ 40 | Blocked — ethics violation recorded |
| CP-8 | Threshold & Context Validator | temporal_coherence | ≥ 45 | Blocked — parameter out of range |
| CP-9 | AML Screening | probability_score | ≥ 15 | Blocked — suspicious activity flagged |
| CP-10 | Fraud Detection | logic_consistency | ≥ 30 | Blocked — fraud flag escalated |
| CP-11 | Jurisdiction Compliance | signal_integrity | ≥ 35 | Blocked — jurisdiction violation |

### Published Research (permanent DOIs)
- **Zenodo v2**: https://doi.org/10.5281/zenodo.19378059
- **SSRN**: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6507559
- (First papers: Zenodo 10.5281/zenodo.19056919, SSRN 6321298)

### External Governance API (Flask Dashboard — B2B, Port 5000)
`omnix_dashboard/blueprints/governance.py` — 6-checkpoint B2B pipeline (separate from the 11-checkpoint public sandbox). RBAC auth, PQC-signed receipts, NIST AI RMF / ISO 42001 / EU AI Act aligned.

### Public Verification Server (Railway — Port 8000)
Standalone `aiohttp` server. Public receipt verification. Zero internal data exposure. SHA-256 hash chains + Dilithium-3 PQC signatures.

### Web Infrastructure
| Port | Environment | Purpose |
|------|-------------|---------|
| `$PORT` Railway | Production | gunicorn: Flask + React dist |
| 3000 | Replit dev | Vite dev server |
| 5000 | Replit dev | Flask Dashboard (local/internal) |
| 8000 | Railway | Public verification server |

---

## Security / PQC Rules

**PQC Communication Tier Rules (CRITICAL):**
| Tier | Audience | Allowed | Prohibited |
|------|-----------|---------|-----------|
| External | Bot, web | "NIST-standardized algorithms", "post-quantum cryptography" | FIPS 203/204, algorithm names |
| Institutional | Investors | Dilithium-3, Kyber-768, "NIST-standardized" | FIPS 203/204 |
| Internal | ADRs, code | Everything | N/A |

**Kyber-768 is a KEM, NOT a data encryption algorithm.** Data encryption = AES/Fernet.

**Legal Language:**
- "NIST-standardized algorithms" — NEVER "FIPS 204/203"
- "Aligned with core SOC 2 security control principles" — NEVER "SOC 2 compliant"
- "Designed for ADGM/SEC regulatory frameworks" — NEVER "ADGM compliance ready"
- Footer: "Abu Dhabi, UAE" — no ADGM affiliation implied

---

## Investor / Business Rules

### Track Record Disclosure (MANDATORY)
| Period | Money | Dates | Trades | P&L |
|--------|-------|-------|--------|-----|
| Phase 0 — Real Capital | **REAL** (Kraken) | Jul 6 – Aug 18, 2025 | 1,115 | -$1,167 |
| Learning Baseline | Paper | Nov 2025 – Jan 14, 2026 | 119 | -$15,198.73 |
| Official Track Record | Paper | Jan 15, 2026 – present | 0 | $0 |

> NEVER mix real and simulated money in reports or investor responses.

### Pricing
- Shadow Mode: Free
- Advisory: $8K/month
- Enterprise: $20K–$35K/month
- Custom: Contact us
- Burn rate: $34,500/month = 14.5 months runway. Break-even = 2 enterprise clients.

### Contact
- WhatsApp: +1 (650) 507-8293
- Email: contacto@omnixquantum.net

### Branding Policy
- **Never show version** (V6.5.4e INSTITUTIONAL+) in any user/investor-facing surface
- External identity: "OMNIX Decision Governance" — no version numbers
- Harold Nunes: only name visible. If asked about technical help: "I've worked with contract developers and infrastructure consultants"

---

## External Dependencies
- **Kraken**: Crypto data and order execution
- **Alpaca**: Stock data and historical bars
- **Google Gemini (Flash)**: Primary AI model
- **OpenAI (GPT-4o, Whisper)**: AI services
- **Anthropic Claude**: AI fallback
- **ElevenLabs**: Text-to-speech
- **CoinGecko**: Backup crypto prices
- **Alternative.me**: Fear and Greed Index
- **Finnhub**: Market news and sentiment
- **Alpha Vantage**: Technical indicators
- **Tavily**: Real-time web search
- **Stripe**: Payment processing
- **ANU QRNG**: Quantum random numbers
- **PostgreSQL (Railway)**: Main persistence
- **Redis (Railway)**: Caching, state management, rate limiting

---

## B2B API Key System (ADR-051)

### Overview
Every B2B client (e.g. Velos) gets a unique API key. All their evaluations are tagged with their `client_id` in `decision_receipts`. Harold can query usage at any time for billing.

### Database Tables
| Table | Purpose |
|-------|---------|
| `b2b_clients` | One row per client: `client_id`, `api_key_hash` (SHA-256, never plaintext), `name`, `email`, `role`, `is_active`, `last_seen_at` |
| `decision_receipts` | Every evaluation: `client_id` column links to the client. Public sandbox uses `'PUBLIC'`. |
| `client_thresholds` | Per-client override of the 11 checkpoint thresholds (ADR-037). |

### API Key Rules
- Format: `OMNIX-<40 random alphanumeric chars>`
- Storage: ONLY the SHA-256 hash is stored — plaintext is shown once and never again
- Role: `standard` (B2B evaluation) or `admin` (Harold — can create/manage clients)
- Revocation: `is_active = FALSE` — instant, no code change needed
- Header to use: `X-API-Key: <api_key>`

### Creating a New Client (Railway Production)
```bash
# Create the Velos partner client
railway run python scripts/provision_b2b_client.py \
    --client-id  velos-partner \
    --name       "Velos Capital" \
    --email      naimat@veloscapital.com \
    --role       standard

# Create Harold's admin key (first time only)
railway run python scripts/provision_b2b_client.py \
    --client-id  omnix-admin \
    --name       "OMNIX Admin" \
    --email      contacto@omnixquantum.net \
    --role       admin

# List all clients
railway run python scripts/provision_b2b_client.py --client-id any --list

# Rotate a key (old key instantly invalid)
railway run python scripts/provision_b2b_client.py --client-id velos-partner --rotate

# Deactivate a client (revoke access)
railway run python scripts/provision_b2b_client.py --client-id velos-partner --deactivate
```

### Admin API Endpoints (require admin API key)
| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/governance/admin/usage` | Monthly usage all clients — for billing |
| `GET` | `/api/governance/admin/usage/<client_id>` | Detailed usage for one client |
| `GET` | `/api/governance/admin/clients` | List all clients |
| `POST` | `/api/governance/admin/clients` | Create client via API |
| `DELETE` | `/api/governance/admin/clients/<id>` | Deactivate client |
| `POST` | `/api/governance/admin/clients/<id>/rotate` | Rotate API key |

### Usage Report Example (how Harold checks Velos billing)
```bash
curl -H "X-API-Key: <harold-admin-key>" \
     "https://omnixquantum.net/api/governance/admin/usage/velos-partner?months=3"
# Returns: monthly breakdown of APPROVED/BLOCKED/HOLD evaluations tagged client_id='velos-partner'
```

### Velos Integration Flow
```
Naimat's system
    → POST /api/governance/evaluate  (header: X-API-Key: OMNIX-<velos-key>)
    → OMNIX runs 11-checkpoint pipeline
    → Receipt generated, saved to decision_receipts (client_id='velos-partner')
    → JSON response returned to Naimat
    → Naimat pushes receipt to velos-gateway for 60s Auth_Hash window
Monthly: Harold queries usage endpoint → sees exact count → emits invoice
```

---

## Recent Fixes (Apr 2026)
| Commit | Fix |
|--------|-----|
| Apr-2026 | **Competitive moat — 3 improvements**: (1) CP-11 Jurisdiction Gate now covers 13 jurisdictions: UAE, EU, US, GCC, **UK, SG, JP, AU, CA, BR, KR, CH**, GLOBAL. File: `omnix_core/governance/jurisdiction_gate.py` + bundled to `omnix_web/api/omnix_engine/jurisdiction_gate.py` for Railway. (2) Decision analytics endpoint added: `GET /api/analytics/decisions` — aggregated patterns (by domain, by checkpoint, 30-day trend, B2B clients). File: `omnix_web/api/server.py`. (3) Integration quickstart: `GET /api/governance/quickstart` — curl + Python examples for 5-step B2B onboarding. File: `omnix_web/api/gov_blueprint.py`. |
| ADR-052 | Velos Gateway Push (final) — `POST /api/governance/evaluate` for `client_id='velos-partner'` triggers a non-blocking push to `https://velos-gateway.onrender.com/api/v1/intercept`. Features: semaphore (max 10 threads), full disposition audit log (SENT/SKIPPED/ERROR + latency_ms + skip_reason), config-driven client ID via `VELOS_CLIENT_ID` env var. Token: `VELOS_GATEWAY_TOKEN` (set in Railway). Files: `omnix_dashboard/blueprints/governance.py` (dashboard) + `omnix_web/api/gov_blueprint.py` (Railway standalone copy — KEEP IN SYNC). B2B endpoint now accessible at omnixquantum.net via `omnix_web/api/server.py` → `api.gov_blueprint`. |
| ADR-051 | Added B2B client usage reporting endpoints (`/api/governance/admin/usage`). Added `scripts/provision_b2b_client.py` to create Velos API key on Railway. Documented full billing flow in replit.md. |
| `b9d6606f` | Aligned all checkpoints to CP-1→CP-11 matching published Zenodo/SSRN paper. Added CP-11 Jurisdiction Compliance. Renamed CP-7 Ethics & Domain Gate, CP-8 Threshold & Context Validator. |
| `cb826eca` | Removed CP-11/CP-7b from InstitutionalPage (cleanup before full alignment) |
| `039d00f5` | Fixed production backend from 8 to 11 checkpoints (root cause: `omnix_web/api/sandbox.py`) |
| `d93d1adb` | React: removed opacity-30, dynamic title, whitepaper moved to `public/` |
