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
| `OMNIX_SIGNING_SECRET_KEY_B64` | Dilithium-3 receipt signing | **REQUIRED** — PQC private key (base64). **Missing in Railway — receipts not signed in production.** |
| `OMNIX_SIGNING_PUBLIC_KEY_B64` | Dilithium-3 verification | **REQUIRED** — PQC public key (base64). **Missing in Railway.** |
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

### Critical Gaps — Action Required

1. **`OMNIX_SIGNING_SECRET_KEY_B64`** — Not in Railway. PQC receipts are not signed in production. Copy from Replit Secrets → Railway.
2. **`OMNIX_SIGNING_PUBLIC_KEY_B64`** — Not in Railway. Copy from Replit Secrets → Railway.
3. **`TELEGRAM_ADMIN_USER_ID`** — Not in Railway or Replit. Add your Telegram user ID (obtain via [@userinfobot](https://t.me/userinfobot)).

---

## Stack

*   **Frontend:** React 18, Vite 7, TypeScript, Tailwind CSS
*   **Backend:** Python 3.11, Flask
*   **Database:** PostgreSQL (Railway managed)
*   **Cache / Anti-replay:** Redis (Railway managed)
*   **PQC Library:** Dilithium-3 (ML-DSA-65), Kyber-768
*   **AI Models:** Google Gemini 2.5 Flash (primary) → OpenAI GPT-4o mini → Anthropic Claude (fallbacks)
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

---

## Architecture Decisions

*   **PQC-First Cryptography:** All governance decisions are signed with Dilithium-3. Receipts are W3C Verifiable Credential compatible.
*   **Layered Governance Pipeline:** 4-Layer Defense → 11-checkpoint pipeline. Fail-Closed at every critical juncture (ADR-116).
*   **Adaptive Veto Machine (AVM):** Per-vertical baselines with dynamic calibration, tamper detection, and fail-closed option (ADR-074, ADR-120).
*   **Execution Integrity Layer (ADR-131):** Extends governance from decision to execution — every action produces an `ExecutionReceipt` bound to its originating decision.
*   **Governance Monitoring Layer:** Four real-time audit dashboards backed by live DB tables — Anomaly (ADR-129), Breach (ADR-142), Risk (ADR-143), Execution (ADR-131).
*   **Governance Replay Engine (ADR-145):** Deterministic replay of 5 historical crises (Terra/LUNA, FTX, SVB, COVID, OFAC) with PQC-signed receipts. Live at `/crisis-replay`.
*   **Runtime Authority Matrix (ADR-146):** Explicit four-tier authority model for all runtime governance actions.

---

## User Preferences

*   Always respond to Harold in Spanish.

---

## Gotchas

*   **Gemini Billing:** Requires activation in Google Cloud Console (`console.cloud.google.com`).
*   **React Build:** Run `npm run build` in `omnix_web/` after every frontend change. Commit the `dist/` folder. Railway serves from `dist/`.
*   **Variable names matter:** Flask Dashboard reads `SESSION_SECRET` (not `SECRET_KEY`). Webhook encryption reads `PAYLOAD_ENCRYPTION_KEY` (not `WEBHOOK_ENCRYPTION_KEY`). Using wrong names = silent failures.
*   **PQC Keys in Railway:** `OMNIX_SIGNING_SECRET_KEY_B64` and `OMNIX_SIGNING_PUBLIC_KEY_B64` exist in Replit but not Railway — receipts in production are unsigned until these are added.
*   **API Key Provisioning:** When provisioning B2B API keys via `provision_b2b_client.py`, copy the key immediately — it is only shown once.
*   **Production Safeguards:** Never set `TESTING=true` in production — it bypasses critical security checks.
*   **Database Indices:** Apply `CREATE INDEX idx_fce_domain_event_ts ON filter_calibration_events (domain, event_ts)` for datasets larger than 50K rows (ADR-134).
*   **Oscillation API:** `GET /api/analytics/oscillation` returns a flat response (oscillation_profile, asymmetry, dampening, etc. at top level). The `result` key is deprecated.

---

## Pointers

*   **ADRs:** `docs/adr/` — 146 total. Last: ADR-144 (Auto-Modification Guard) · ADR-145 (Replay Engine) · ADR-146 (Authority Matrix)
*   **Full Architecture:** `docs/current/ARCHITECTURE.md`
*   **Deployment Operations:** `docs/operations/DEPLOYMENT.md`
*   **Python SDK:** `sdk/python/README.md`
*   **Node.js SDK:** `sdk/node/README.md`
*   **Governance Replay:** `omnix_core/simulation/` — ADR-145
*   **Runtime Authority:** `docs/AUTHORITY_MATRIX.md` — ADR-146
*   **Auto-Modification Guard:** `omnix_core/governance/auto_modification_guard.py` — ADR-144
*   **Crisis Replay Page:** `/crisis-replay` — 5 crises, 12 receipts, verifiable independently
*   **Public Receipt Verifier:** `omnix_web/public/omnix_verify.py --mode replay`
