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

## Critical Override Layer — Groups Reference (sandbox.py)

`_apply_critical_override` in `omnix_web/api/sandbox.py` has 5 override branches in priority order:

| Priority | Branch | Trigger | Signal Calibration |
|----------|--------|---------|-------------------|
| 1 | `is_governance_fraud` | Committee override, CEO bypass, anonymous wallets, conflict of interest | probability ~8, risk ~91, coherence ~12 |
| 2 | `is_critical_violation` | Market manipulation, OFAC, Ponzi, ransomware, data breach, deepfake KYC | probability ~8, risk ~92, coherence ~11 |
| 3 | `is_system_integrity` | Cryptographic failure, quantum attack, active cyberattack, DB inconsistency | probability ~6, risk ~92, coherence ~5 |
| 4 | `is_financial_crime_complex` | AML, Sharia, export control, PEP, no oversight, 4 verticals | probability 6-13, risk 78-90, coherence 30-48 |
| 5 | else (lethal/life-critical) | Death, emergency, lethal force, autonomous weapons | probability ~10, risk ~90, coherence ~12 |

### `financial_crime_complex` — Covered Groups (ADR-056 + ADR-057)

| Group | Terms (examples) | Receipt Flag |
|-------|-----------------|-------------|
| Beneficial Owner / AML | `undisclosed beneficial owner`, `offshore spv`, `mauritius spv` | AML red flag — CP-1, CP-9 |
| Islamic Finance / Sharia | `murabaha without sharia`, `no sharia board`, `riba element` | Ethics violation — CP-7 |
| Export Control / Watchlists | `export control list`, `denied parties list`, `eu export control` | Regulatory block — CP-10, CP-11 |
| Multi-jurisdiction gap | `without local legal review`, `multi-jurisdiction without legal` | Jurisdiction violation — CP-11 |
| Artificial time pressure | `72 hours to close`, `close within 72`, `deadline artificial` | Coherence manipulation — CP-4 |
| Trading vertical | `unhedged position`, `no stop-loss`, `oracle manipulation`, `liquidation cascade` | Risk failure — CP-2, CP-3, CP-6 |
| Insurance vertical | `multiple claims same period`, `staged accident`, `pre-existing condition not disclosed` | Fraud signal — CP-10 |
| Robotics vertical | `safety certification not completed`, `human override mechanism disabled`, `sensor fusion failure` | Ethics + Jurisdiction — CP-7, CP-11 |
| **Group 5 — No Oversight** *(ADR-057)* | `no aml officer`, `no compliance officer`, `no due diligence`, `automated approval`, `no oversight` | Governance failure — CP-1, CP-7, CP-9 |
| **Group 7 — PEP** *(ADR-057)* | `politically exposed person`, `senior government official`, `politically connected beneficial` | AML/KYC — CP-9, CP-10 |

### Summary Quality Guard (ADR-057)
When `BLOCKED` + contradictory phrase detected (`low risk`, `moderate risk`, `acceptable risk`, `approved`, etc.):
- **With active override** → `"Governance override activated. This scenario contains patterns that require mandatory human review..."`
- **Without active override** → Generic: `"{n} checkpoint(s) raised a blocking condition — decision stopped before execution."`

---

## Bot Governance Integration (ADR-058)

**Fecha:** 2026-04-06 | **Status:** Accepted

Los comandos de gobernanza del bot de Telegram están en un módulo separado `governance_commands.py`, enlazados mediante asignación post-clase a `EnterpriseTelegramBot`.

### Comandos de gobernanza

| Comando | Acceso | Descripción |
|---------|--------|-------------|
| `/evaluar [escenario]` | Público | Pipeline 11-checkpoint via HTTP → sandbox. Receipt ID en respuesta. Rate limit: 5/hora/user. |
| `/evaluate [scenario]` | Público | Alias inglés |
| `/gobernanza` | Público | Dashboard: Critical Override 7 grupos, posición OMNIX, health ping |
| `/governance` | Público | Alias inglés |
| `/velos` | Admin only | Log Velos gateway: disposition, HTTP status, latencia (query a `velos_push_log`) |
| `/recibo [n]` | Admin only | Últimos N recibos PQC (default 3, max 10; query a `decision_receipts`) |
| `/receipt [n]` | Admin only | Alias inglés |

### Variables de entorno requeridas (bot en Railway)

| Variable | Descripción |
|----------|-------------|
| `OMNIX_WEB_URL` | URL del servicio stellar-hope en Railway. En prod: `https://stellar-hope.railway.app`. Default dev: `http://localhost:5000`. **CRÍTICO: configurar antes del redeploy del bot.** |
| `DATABASE_URL` | PostgreSQL — ya configurado. Para `/velos` y `/recibo`. |

### Archivos afectados (ADR-058)

```
omnix_services/telegram_service/
├── enterprise_bot.py          # Import + binding + handlers + /version, /start, /help actualizados
└── commands/
    ├── __init__.py
    └── governance_commands.py # 4 handlers: evaluar, gobernanza, velos, recibo
docs/reference/adr/
└── ADR-058-bot-governance-integration.md
```

---

## Executive Audit Dashboard (ADR-059)

**Fecha:** 2026-04-06 | **Status:** Accepted

Panel ejecutivo accesible en `/audit`. Traduce los recibos PQC técnicos a lenguaje de negocio para CFOs, reguladores y directivos — sin exponer scores internos, thresholds ni nombres de señales propietarias.

### Arquitectura

| Capa | Detalle |
|------|---------|
| **Ruta frontend** | `/audit` → `AuditDashboard.tsx` |
| **Endpoint protegido** | `GET /api/governance/audit/decisions` (API key requerida) |
| **Endpoint demo público** | `GET /api/public/audit-demo` (sin autenticación, datos sintéticos) |
| **Traducción veto_chain** | `_parse_veto_chain_executive()` — extrae CP-id + status, mapea a label + executive_reason en inglés ejecutivo. **NUNCA expone scores, thresholds, operadores ni nombres de señales.** |
| **Fuente de datos** | Tabla `decision_receipts` (receipt_id, asset, domain, decision, veto_chain, timestamp) |

### Qué muestra el dashboard

- **KPI bar**: Total decisiones, Aprobadas, Bloqueadas, % aprobación
- **Domain breakdown**: Por vertical (Trading, Crédito Islámico, Seguros, Robótica) con barra de aprobación
- **Tabla de decisiones**: receipt_id, timestamp, dominio, badge APPROVED/BLOCKED — clickeable
- **Panel de detalle**: Resultados de cada checkpoint (CP-1 → CP-11 + CAG/TIE/PQC) en lenguaje ejecutivo + badge PQC SIGNED / CHAIN LINKED
- **Filtros**: por dominio, por resultado (APPROVED / BLOCKED)
- **Modo demo/live toggle**: Demo usa datos sintéticos sin API key; Live requiere API key

### Archivos afectados (ADR-059)

```
omnix_web/src/pages/AuditDashboard.tsx   # Nueva página React (KPI, filtros, tabla, panel detalle)
omnix_web/src/App.tsx                     # Ruta /audit añadida
omnix_web/src/pages/InvestorCommandCenter.tsx  # Link "Executive Audit" → /audit añadido
omnix_web/api/gov_blueprint.py            # 2 endpoints nuevos + traducción veto_chain
docs/reference/adr/ADR-059-executive-audit-dashboard.md
```

---

## Recent Fixes (Apr 2026)
| Commit | Fix |
|--------|-----|
| ADR-061 | **Persistent IP Blocklist**: DB-backed `blocked_ips` PostgreSQL table with 30s in-memory cache (thread-safe). Auto-bans any IP that triggers rate limit 3+ times in 10 minutes → 1-hour ban persisted to DB, survives Railway restarts. Enforcement at two points: `_require_auth()` + `api_governance_evaluate()`. Telegram notification to Harold on every auto-ban. `_auto_ban_ip()` runs in daemon thread — zero pipeline latency impact. Existing in-memory brute-force lockout (ADR-052) unchanged. Files: `omnix_web/api/gov_blueprint.py`. |
| ADR-062 | **Premium Features**: (1) Regulatory Mapping Engine — `omnix_engine/regulatory_mapping.py` maps all 11 CPs to EU AI Act, DORA, NIST AI RMF, ISO 42001, CA SB 243, GDPR, FATF, Basel III. `regulatory_alignment` field now in every evaluate response. Public endpoint `GET /api/governance/regulatory/catalog`. (2) Due Diligence PDF Package — `omnix_engine/due_diligence.py` + `GET /api/governance/due-diligence-report?format=pdf&days=N`. Premium branded PDF: logo, KPIs, domain breakdown, regulatory table, attestation. Auth required. (3) Python SDK — `omnix_sdk/python/omnix_sdk.py` (stdlib only, no deps). (4) Node.js SDK — `omnix_sdk/node/index.js` (stdlib only). Both SDKs: evaluate, get_receipt, list_receipts, due_diligence_report, regulatory_catalog. (5) Client Portal — `/client` → `ClientDashboard.tsx`. API key auth, KPIs, domain breakdown, regulatory framework badges, receipt table, PDF download, SDK quickstart. Link added to InvestorCommandCenter. ADR-062 written. |
| ADR-060 | **Guided Investor Demo** (`/demo`): 4 stages — scenario selection (4 verticals), animated 11-checkpoint pipeline (real API call), decision receipt with PQC badge, full-picture narrative connecting Bot + Command Center + Audit Dashboard. Fallback determinístico si falla la API. Link "2-Min Investor Demo" en InvestorCommandCenter. |
| ADR-059 | **Executive Audit Dashboard**: Página `/audit` con KPIs, domain breakdown, tabla de decisiones filtrable y panel de detalle. Endpoint `/api/public/audit-demo` (público, sintético) + `/api/governance/audit/decisions` (API key). Traducción server-side de veto_chain a lenguaje ejecutivo — scores, thresholds y señales propietarias nunca expuestos en respuesta API. Badge PQC SIGNED + CHAIN LINKED por decisión. Link "Executive Audit" añadido al InvestorCommandCenter. ADR-059 escrito. |
| ADR-058 | **Bot Governance Integration**: Módulo `governance_commands.py` separado con 4 handlers (`/evaluar`, `/gobernanza`, `/velos`, `/recibo`). Enlazados a `EnterpriseTelegramBot` post-clase. `/evaluar` usa HTTP POST a `OMNIX_WEB_URL`, rate limit 5/hora/user. `/velos` y `/recibo` son admin-only, query directo a PostgreSQL. Stubs de fallback si el módulo falla. `/version`, `/start`, `/help` actualizados con posicionamiento de governance platform. Arquitecto revisó patrón de integración. |
| ADR-057 | **Critical Override Hybrid Expansion**: Added Group 5 (No Human Oversight) and Group 7 (Politically Exposed Persons/PEP) to `financial_crime_complex` branch of `_apply_critical_override`. Extended Summary Quality Guard to catch `"moderate risk"`, `"acceptable risk"`, `"low risk profile"` — replaces with spec-mandated override message when active override detected. 24/24 tests pass. Files: `omnix_web/api/sandbox.py`. |
| Apr-2026c | **ADR-053 — Generic Webhook System + Receipt-by-ID + Key Expiry Warning**: (1) All B2B clients can register an HTTPS webhook URL via `PUT /api/governance/admin/clients/<id>/webhook`. Every decision evaluation pushes a PQC-signed payload signed with HMAC-SHA256 in `X-OMNIX-Signature` header. Delivery log in `webhook_delivery_log` table with per-client stats. SSRF guard rejects private/loopback CIDRs. Secrets encrypted at rest with Fernet (`WEBHOOK_ENCRYPTION_KEY` env var optional). (2) `GET /api/governance/receipts/<receipt_id>` — fetch a single receipt by ID with strict tenant isolation (IDOR-proof). (3) Key expiry warning: `key_expiry_warning.expires_in_days` appears in evaluate response when <14 days remain. Files: `omnix_web/api/gov_auth_rbac.py`, `omnix_web/api/gov_blueprint.py`. |
| Apr-2026b | **ADR-052 — Security hardening (4 measures)**: (1) Brute force lockout: 5 failed auth attempts from same IP → 15 min lockout. (2) API key expiry: new/rotated keys expire in 90 days (`key_expires_at` column in `b2b_clients`). (3) Security headers on all responses: X-Content-Type-Options, X-Frame-Options, HSTS, XSS-Protection, Referrer-Policy, Permissions-Policy. (4) Admin IP allowlist: set `ADMIN_ALLOWED_IPS` env var in Railway (comma-separated IPs) to restrict `/api/governance/admin/*` to your IP only. Files: `omnix_web/api/gov_blueprint.py`, `omnix_web/api/gov_auth_rbac.py`, `omnix_web/api/server.py`. |
| Apr-2026 | **Competitive moat — 3 improvements**: (1) CP-11 Jurisdiction Gate now covers 13 jurisdictions: UAE, EU, US, GCC, **UK, SG, JP, AU, CA, BR, KR, CH**, GLOBAL. File: `omnix_core/governance/jurisdiction_gate.py` + bundled to `omnix_web/api/omnix_engine/jurisdiction_gate.py` for Railway. (2) Decision analytics endpoint added: `GET /api/analytics/decisions` — aggregated patterns (by domain, by checkpoint, 30-day trend, B2B clients). File: `omnix_web/api/server.py`. (3) Integration quickstart: `GET /api/governance/quickstart` — curl + Python examples for 5-step B2B onboarding. File: `omnix_web/api/gov_blueprint.py`. |
| ADR-052 | Velos Gateway Push (final) — `POST /api/governance/evaluate` for `client_id='velos-partner'` triggers a non-blocking push to `https://velos-gateway.onrender.com/api/v1/intercept`. Features: semaphore (max 10 threads), full disposition audit log (SENT/SKIPPED/ERROR + latency_ms + skip_reason), config-driven client ID via `VELOS_CLIENT_ID` env var. Token: `VELOS_GATEWAY_TOKEN` (set in Railway). Files: `omnix_dashboard/blueprints/governance.py` (dashboard) + `omnix_web/api/gov_blueprint.py` (Railway standalone copy — KEEP IN SYNC). B2B endpoint now accessible at omnixquantum.net via `omnix_web/api/server.py` → `api.gov_blueprint`. |
| ADR-051 | Added B2B client usage reporting endpoints (`/api/governance/admin/usage`). Added `scripts/provision_b2b_client.py` to create Velos API key on Railway. Documented full billing flow in replit.md. |
| `b9d6606f` | Aligned all checkpoints to CP-1→CP-11 matching published Zenodo/SSRN paper. Added CP-11 Jurisdiction Compliance. Renamed CP-7 Ethics & Domain Gate, CP-8 Threshold & Context Validator. |
| `cb826eca` | Removed CP-11/CP-7b from InstitutionalPage (cleanup before full alignment) |
| `039d00f5` | Fixed production backend from 8 to 11 checkpoints (root cause: `omnix_web/api/sandbox.py`) |
| `d93d1adb` | React: removed opacity-30, dynamic title, whitepaper moved to `public/` |

---

## 🗺️ ROADMAP — MEJORAS FUTURAS (no construir sin cliente confirmado)

| ID | Idea | Origen | Prioridad |
|----|------|---------|-----------|
| ROAD-001 | **CP-0 Privacy Gate** — Checkpoint previo al pipeline que escanea el payload de entrada con regex/patrones buscando PII (SSN, DOB, pasaporte, tarjeta de crédito). Si detecta PII no esperado → BLOCKED con receipt. Para verticales EdTech / Salud Mental. Diferenciador vs. SASI: OMNIX bloquea la decisión, SASI redacta el dato en tránsito. Son complementarios, no competidores. | Conversación LinkedIn con Stephen Calhoun (SASI), Abr 2026 | Media — activar cuando haya cliente EdTech/HealthTech concreto |
| ROAD-002 | **Webhook retry logic** — El sistema de webhooks actual hace 1 intento. Añadir retry con backoff exponencial (3 intentos: 5s, 30s, 5min) y dead-letter queue para payloads fallidos. | ADR-053 deuda técnica | Baja |
| ROAD-003 | **SDK Java / Go** — Ampliar la cobertura de SDKs para equipos enterprise que usan Java (bancos) o Go (fintechs). Misma filosofía: un solo archivo, sin dependencias externas. | Observación comercial | Baja — post-ronda |
| ROAD-004 | **Multi-tenant Client Portal** — El portal `/client` actual es single-tenant (1 API key). Versión multi-tenant donde un administrador ve todos sus sub-clientes bajo una sola sesión. Para enterprise con filiales. | Arquitectura futura | Baja — post-ronda |
