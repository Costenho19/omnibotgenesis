# OMNIX QUANTUM — Decision Governance Infrastructure

OMNIX QUANTUM provides a robust decision governance platform that enables auditable, AI-driven, and cryptographically secured decision-making for enterprises across various verticals.

## Run & Operate

*   **Run (Development):** `python run_services.py` (starts bot, Flask dashboard, and simulators)
*   **Run (Production API):** `python api/server.py`
*   **Build (Frontend):** `cd omnix_web && npm run build && cd ..` (commit `dist/` folder after every frontend change)
*   **Database Migrations:** Railway handles DDL automatically via idempotent `CREATE TABLE IF NOT EXISTS` calls on first request.

---

## Environment Variables — Canonical Reference

Variables are read with these **exact names** in the source code. Use the same names in Railway and Replit Secrets.

### Flask Web API (`omnix_web/api/server.py`)

| Variable | Where read | Status |
|---|---|---|
| `DATABASE_URL` | `get_db_connection()` | **REQUIRED** — PostgreSQL connection string |
| `REDIS_URL` | anti-replay + cache | **REQUIRED** — Redis connection string |
| `GEMINI_API_KEY` | AI governance engine | **REQUIRED** — Google Gemini billing must be active |
| `OMNIX_WEB_URL` | webhook callbacks | **REQUIRED** — e.g. `https://omnixquantum.net` |
| `VITE_RAILWAY_API_URL` | frontend build-time var | **REQUIRED** — public API URL for React app |
| `OMNIX_SIGNING_SECRET_KEY_B64` | Dilithium-3 receipt signing | **REQUIRED** — PQC private key (base64). Present in Railway ✓ |
| `OMNIX_SIGNING_PUBLIC_KEY_B64` | Dilithium-3 verification | **REQUIRED** — PQC public key (base64). Present in Railway ✓ |
| `PAYLOAD_ENCRYPTION_KEY` | `gov_blueprint.py` — Fernet webhook encryption | REQUIRED for encrypted webhooks |
| `OPENAI_API_KEY` | AI fallback chain | Optional |
| `ANTHROPIC_API_KEY` | AI fallback chain | Optional |
| `FINNHUB_API_KEY` | market data | Optional |
| `ALPHA_VANTAGE_API_KEY` | market data | Optional |
| `ADMIN_ALLOWED_IPS` | admin-only endpoints | Optional — comma-separated IPs |
| `OMNIX_ANTI_REPLAY_MODE` | `strict` or `best_effort` | Optional (default: `best_effort`) |
| `AVM_FAIL_CLOSED` | `true` = halt on DB failure | Optional (default: false) |

### Flask Dashboard (`omnix_dashboard/app.py`)

| Variable | Where read | Status |
|---|---|---|
| `SESSION_SECRET` | `app.config['SECRET_KEY']` — Flask sessions | **REQUIRED** — present in Railway ✓ |
| `DATABASE_URL` | shared with web API | **REQUIRED** |
| `GEMINI_API_KEY` | AI analysis | **REQUIRED** |
| `DASHBOARD_API_KEY` | dashboard auth | Optional |

### Telegram Bot (`omnix_services/telegram_service/enterprise_bot.py`)

| Variable | Where read | Status |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | bot initialization | **REQUIRED** — present in Railway ✓ |
| `TELEGRAM_ADMIN_USER_ID` | admin commands gate | **REQUIRED** — **MISSING in Railway and Replit** — bot starts but admin commands are disabled |

### Trading Engine

| Variable | Status |
|---|---|
| `KRAKEN_API_KEY` / `KRAKEN_API_SECRET` | Present in Railway ✓ |
| `COINBASE_API_KEY` / `COINBASE_PASSPHRASE` / `COINBASE_SECRET` | Present in Railway ✓ |
| `PAPER_MODE` | Present in Railway ✓ |
| `TRADING_MODE` / `TRADING_PROFILE` | Present in Railway ✓ |

### Critical Gaps — Resueltos ✓

1. **`OMNIX_SIGNING_SECRET_KEY_B64`** — Present in Replit ✓ · Present in Railway ✓
2. **`OMNIX_SIGNING_PUBLIC_KEY_B64`** — Present in Replit ✓ · Present in Railway ✓
3. **`TELEGRAM_ADMIN_USER_ID`** — Present in Replit ✓ (7014748854). Agregar a Railway si el bot corre allí.

---

## Stack

*   **Frontend:** React 18, Vite 7, TypeScript, Tailwind CSS
*   **Backend:** Python 3.11, Flask
*   **Database:** PostgreSQL (Railway managed)
*   **Cache / Anti-replay:** Redis (Railway managed)
*   **PQC Library:** Dilithium-3 (ML-DSA-65), Kyber-768
*   **AI Models:** OpenAI GPT-4o-mini (primary) → GPT-4o → Google Gemini 2.5 Flash → Anthropic Claude (fallbacks)
*   **Build Tool:** npm (React), Python setuptools (SDKs)

---

## Where Things Live

*   `/omnix_web/` — React frontend + Python Flask API (`api/server.py`).
    *   `omnix_web/src/pages/` — All frontend pages (46 pages, 36 routes).
    *   `omnix_web/api/` — API blueprints: `gov_blueprint.py`, `sandbox.py`, `server.py`.
    *   `omnix_web/dist/` — Compiled React app served by Flask in production.
*   `/omnix_dashboard/` — Flask operations dashboard (`app.py`) + blueprints.
*   `/omnix_services/` — Telegram bot (`telegram_service/enterprise_bot.py`) + AI/coherence/trading services.
*   `/omnix_core/` — Core governance logic, PQC security, decision receipts, anti-replay, simulation.
    *   `omnix_core/simulation/` — GovernanceReplayEngine (ADR-145) + 5 crisis scenarios.
    *   `omnix_core/governance/unified_control_layer.py` — UDCL, ADR-138.
    *   `omnix_core/security/pqc_security.py` — Dilithium-3 signing/verification.
*   `/sdk/` — Python SDK (`sdk/python/`) and Node.js SDK (`sdk/node/`).
*   `/docs/adr/` — Architecture Decision Records (146 total). **Source of truth.**
*   `/docs/current/ARCHITECTURE.md` — Full architecture reference.
*   `/docs/AUTHORITY_MATRIX.md` — Runtime Authority Matrix (ADR-146).
*   `/.well-known/` — OpenID4VCI and OMNIX ARF profile metadata.

---

## Database Tables (auto-created on first request)

| Table | Module | ADR |
|---|---|---|
| `decision_receipts` | governance pipeline | ADR-028 |
| `b2b_clients` | B2B API | ADR-052 |
| `avm_calibration_snapshots` | Adaptive Veto Machine | ADR-074/120 |
| `client_thresholds` | per-client config | ADR-052 |
| `vc_revocation_registry` | W3C StatusList2021 | ADR-096 |
| `execution_receipts` | Execution Integrity Layer | ADR-131 |
| `udcl_control_receipts` | Unified Decision Control Layer | ADR-138 |
| `anomaly_recommendations` | Anomaly Response Engine | ADR-129 |
| `breach_events` | Breach Containment Engine | ADR-142 |
| `risk_assessments` | Multi-Domain Risk Governance | ADR-143 |
| `book_leads` | CRM / lead capture | — |
| `governance_scope_authorizations` | Scope Authorization Record | ADR-147 |

---

## Architecture Decisions

*   **PQC-First Cryptography:** All governance decisions are signed with Dilithium-3. Receipts are W3C Verifiable Credential compatible.
*   **Layered Governance Pipeline:** 4-Layer Defense → 11-checkpoint pipeline. Fail-Closed at every critical juncture (ADR-116).
*   **Adaptive Veto Machine (AVM):** Per-vertical baselines with dynamic calibration, tamper detection, and fail-closed option (ADR-074, ADR-120).
*   **Execution Integrity Layer (ADR-131):** Extends governance from decision to execution — every action produces an `ExecutionReceipt` bound to its originating decision.
*   **Governance Monitoring Layer:** Four real-time audit dashboards backed by live DB tables — Anomaly (ADR-129), Breach (ADR-142), Risk (ADR-143), Execution (ADR-131).
*   **Governance Replay Engine (ADR-145):** Deterministic replay of 5 historical crises (Terra/LUNA, FTX, SVB, COVID, OFAC) with PQC-signed receipts. Live at `/crisis-replay`.
*   **Runtime Authority Matrix (ADR-146):** Explicit four-tier authority model for all runtime governance actions.
*   **Scope Authorization Record (ADR-147):** Every governance scope is PQC-signed at issuance with full defensibility criteria (who, why, under what context). AVM-integrated context drift detection triggers formal reapproval when operational context shifts beyond threshold. Answers Rehan Kausar's CAIO question: "Was the scope itself defensible?"

---

## User Preferences

*   Always respond to Harold in Spanish.
*   **Arquitectura inamovible:** React SPA = único frontend. Flask/API = único backend. Nunca crear rutas de página en blueprints Flask que dupliquen rutas del SPA. Nunca usar `render_template` para páginas que ya existen en React. Toda ruta de página nueva va en `omnix_web/src/pages/` y se registra en el router React. Flask solo sirve APIs y el `dist/index.html` para el SPA catch-all. **Excepción explícita:** `/terminal` y `/classic` son dashboards internos de operaciones (Bloomberg-style trading terminal) que viven en Jinja2 — son herramientas internas, no páginas públicas, y no aplica la regla React.

---

## Gotchas

*   **Gemini Billing:** Requires activation in Google Cloud Console (`console.cloud.google.com`).
*   **React Build:** Run `npm run build` in `omnix_web/` after every frontend change. Commit the `dist/` folder. Railway serves from `dist/`.
*   **Variable names matter:** Flask Dashboard reads `SESSION_SECRET` (not `SECRET_KEY`). Webhook encryption reads `PAYLOAD_ENCRYPTION_KEY` (not `WEBHOOK_ENCRYPTION_KEY`). Using wrong names = silent failures.
*   **PQC Keys in Railway:** `OMNIX_SIGNING_SECRET_KEY_B64` and `OMNIX_SIGNING_PUBLIC_KEY_B64` exist in Replit but not Railway — receipts in production are unsigned until these are added.
*   **API Key Provisioning:** When provisioning B2B API keys via `provision_b2b_client.py`, copy the key immediately — it is only shown once.
*   **Production Safeguards:** Never set `TESTING=true` in production — it bypasses critical security checks (suppresses AVM Telegram alerts, skips snapshot scheduler thread, skips simulators).
*   **PQC Keys in Railway (URGENT):** `OMNIX_SIGNING_SECRET_KEY_B64` and `OMNIX_SIGNING_PUBLIC_KEY_B64` must be added to Railway — production receipts are SHA-256 only until then. Without them, every Railway restart generates new ephemeral keys and ALL previous receipts become permanently unverifiable (FMR-001).
*   **Anti-Replay Mode in Railway (URGENT):** Set `OMNIX_ANTI_REPLAY_MODE=strict` in Railway. Default `best_effort` allows receipt replay across dynos when Redis is unavailable — cross-dyno split possible in multi-replica deployments (FMR-004).
*   **ADMIN_ALLOWED_IPS in Railway:** Required for `/api/book-leads-admin` to be accessible. Without it, only `127.0.0.1` can call it (safe default but verify in Railway context).
*   **AMG Threshold Env Vars are Security Parameters:** `AVM_MAX_CUMULATIVE_DRIFT_PCT` (default 30%) and `AVM_APPROVAL_THRESHOLD_PCT` (default 10%) must never be set above 50% in production — doing so silently degrades the cumulative drift guard. Treat them as security-sensitive, not operational config.
*   **AVM_AUTO_APPROVE:** Never set `AVM_AUTO_APPROVE=true` in production — disables the AMG approval gate entirely. If accidentally set, the engine now logs an `ERROR`-level warning on every invocation.
*   **OMNIX-DEMO-DASHBOARD-KEY:** The dashboard pages (Anomaly, Breach, Risk, Execution) send `X-API-Key: OMNIX-DEMO-DASHBOARD-KEY`. The server accepts this as a read-only dashboard identity (`role=read`). This is intentional — these dashboards are public-facing audit views. Override with `DASHBOARD_API_KEY` env var in Railway to use a custom key. Admin endpoints (`require_admin=True`) are never bypassed by this key.
*   **/crisis-replay page:** The UI displays hardcoded receipt data (hashes are real, generated by GovernanceReplayEngine at build time). The engine (ADR-145) is fully functional and callable via Python — the UI does not call it dynamically at runtime.
*   **Database Indices:** Apply `CREATE INDEX idx_fce_domain_event_ts ON filter_calibration_events (domain, event_ts)` for datasets larger than 50K rows (ADR-134).
*   **Oscillation API:** `GET /api/analytics/oscillation` returns a flat response (oscillation_profile, asymmetry, dampening, etc. at top level). The `result` key is deprecated.

---

## Pointers

*   **ADRs:** `docs/adr/` — 147 total. Last: ADR-145 (Replay Engine) · ADR-146 (Authority Matrix) · ADR-147 (Scope Authorization Record)
*   **Full Architecture:** `docs/current/ARCHITECTURE.md`
*   **Deployment Operations:** `docs/operations/DEPLOYMENT.md`
*   **Python SDK:** `sdk/python/README.md`
*   **Node.js SDK:** `sdk/node/README.md`
*   **Governance Replay:** `omnix_core/simulation/` — ADR-145
*   **Runtime Authority:** `docs/AUTHORITY_MATRIX.md` — ADR-146
*   **Auto-Modification Guard:** `omnix_core/governance/auto_modification_guard.py` — ADR-144
*   **Crisis Replay Page:** `/crisis-replay` — 5 crises, 12 receipts, verifiable independently (UI is static; hashes are real)
*   **Public Receipt Verifier:** `omnix_web/public/omnix_verify.py --mode replay`
*   **Scope Authorization Engine:** `omnix_core/governance/scope_authorization_engine.py` — ADR-147
*   **Hidden Gap Audit — Stage 1:** `docs/HIDDEN_GAP_AUDIT_REPORT.md` — HGA-2026-Q2-001 (Mayo 2026)
*   **Governance Deep Risk Report — Stage 2:** `docs/GOVERNANCE_DEEP_RISK_REPORT.md` — HGA-2026-Q2-002 (Mayo 2026)
*   **Governance Failure Mode Report — Stage 3:** `docs/GOVERNANCE_FAILURE_MODE_REPORT.md` — HGA-2026-Q3-001 (Mayo 2026) — 11 failure modes, 4 collapse scenarios, 5 crypto trust risks, replay fidelity classification
