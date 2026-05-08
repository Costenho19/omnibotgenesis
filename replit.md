# OMNIX QUANTUM — Decision Governance Infrastructure

OMNIX QUANTUM provides a robust decision governance platform that enables auditable, AI-driven, and cryptographically secured decision-making for enterprises across various verticals.

## Run & Operate

*   **Run (Development):** `python run_services.py` (starts bot, Flask dashboard, and simulators)
*   **Run (Production API):** `python api/server.py`
*   **Build (Frontend):** `cd omnix_web && npm run build && cd ..` (commit `dist/` folder)
*   **Database Migrations:** Railway automatically handles DDL.
*   **Environment Variables:**
    *   `SECRET_KEY`: Flask sessions key. **REQUIRED**
    *   `TELEGRAM_ADMIN_USER_ID`: Your Telegram user ID for admin commands. **REQUIRED**
    *   `OMNIX_SIGNING_SECRET_KEY_B64`: Post-Quantum Cryptography (PQC) private key (Dilithium-3). **REQUIRED**
    *   `OMNIX_SIGNING_PUBLIC_KEY_B64`: PQC public key (Dilithium-3). **REQUIRED**
    *   `VITE_RAILWAY_API_URL`: Public URL for the frontend to connect to the API. **REQUIRED**
    *   `DATABASE_URL`: PostgreSQL connection string (auto-injected by Railway).
    *   `REDIS_URL`: Redis connection for anti-replay.
    *   `TELEGRAM_BOT_TOKEN`: Token for the Telegram bot.
    *   `GEMINI_API_KEY`: Google Gemini API key (activate billing).
    *   `OMNIX_WEB_URL`: URL of the web API (e.g., `https://omnixquantum.net`).
    *   `ADMIN_ALLOWED_IPS`: Comma-separated list of IPs for admin endpoints.
    *   `WEBHOOK_ENCRYPTION_KEY`: Fernet key for encrypting webhook secrets.
    *   `OMNIX_ANTI_REPLAY_MODE`: `strict` or `best_effort` (default).
    *   `AVM_FAIL_CLOSED`: `true` to halt on DB failure or tampered AVM snapshot.

## Stack

*   **Frontend:** React, Vite
*   **Backend:** Python (Flask)
*   **Database:** PostgreSQL
*   **Cache/Queue:** Redis
*   **ORM:** SQLAlchemy (implied)
*   **Validation:** Pydantic (implied by schema validation ADRs)
*   **Build Tool:** npm (for React), Python build (for SDKs)
*   **PQC Library:** Dilithium-3, Kyber-768
*   **AI Models:** Google Gemini 2.5 Flash (primary), OpenAI GPT-4o mini, Anthropic Claude (fallbacks)

## Where things live

*   `/omnix_web/`: React frontend and Python API (`api/server.py`).
    *   `omnix_web/src/pages/`: Frontend pages (e.g., `CommercialLanding.tsx`, `InvestorCommandCenter.tsx`, `AuditDashboard.tsx`).
    *   `omnix_web/api/`: Main API blueprints (`gov_blueprint.py`, `sandbox.py`, `server.py`).
*   `/omnix_dashboard/`: Flask dashboard (`app.py`) and its blueprints (`governance.py`, `trading.py`, vertical-specific blueprints).
*   `/omnix_services/`: Telegram bot (`telegram_service/enterprise_bot.py`) and various AI/coherence/trading services.
*   `/omnix_core/`: Core governance logic (`governance/`), PQC security (`security/pqc_security.py`), decision receipts (`decision_receipt.py`), anti-replay (`anti_replay.py`).
*   `/sdk/`: Python and Node.js SDKs.
*   `/docs/adr/`: Architecture Decision Records (ADRs). **Source of truth for architectural decisions.**
*   `/.well-known/`: OpenID4VCI and OMNIX ARF profile metadata. **Source of truth for public API/credential discovery.**
*   `omnix_core/governance/jurisdiction_gate.py`: Defines supported jurisdictions.
*   `omnix_web/api/omnix_engine/vc_revocation.py`: W3C StatusList2021 implementation.
*   `omnix_core/governance/conditional_bind_gate.py`: Conditional Bind Gate logic.
*   `omnix_core/governance/state_provenance_guard.py`: State Provenance Guard logic.
*   `omnix_core/evidence/receipt_archival.py`: Receipt archival (HOT/WARM/COLD storage).
*   `omnix_core/governance/oversight_surface.py`: Oversight Surface Engine for human supervision quality.
*   `omnix_core/governance/unified_control_layer.py`: MOD-014 UDCL — UnifiedDecisionControlLayer, PillarResult, ControlReceipt (ADR-138).
*   Database schema for `decision_receipts`, `b2b_clients`, `avm_calibration_snapshots`, `client_thresholds`, `vc_revocation_registry`, `execution_receipts`, `udcl_control_receipts` etc. is defined implicitly by the Python models and `ensure_table()` calls.

## Architecture decisions

*   **PQC-First Cryptography:** All governance decisions are signed with Dilithium-3 for post-quantum security and can be verified via W3C Verifiable Credentials.
*   **Layered Governance Pipeline:** Decisions flow through a "4-Layer Defense" architecture, culminating in an 11-checkpoint pipeline, with Fail-Closed policies at each critical juncture (ADR-116).
*   **Adaptive Veto Machine (AVM):** Each governance vertical has its own AVM baseline that dynamically calibrates thresholds and auto-recalibrates based on performance, with built-in tamper detection and fail-closed options (ADR-074, ADR-120).
*   **Observational Capture Resistance:** Mechanisms like AVM Genesis Anchor and WAL Chain Verification are implemented to detect degradation in the evaluative framework that local compensatory logic might miss (P1, P2, P3, P4 — Insight Amanulla Khan).
*   **Execution Integrity Layer (ADR-131):** Extends governance from decision to execution, ensuring every action produces an `ExecutionReceipt`, pre-captures `ExecutionIntent`, and binds decisions to executions for full auditability.

## Product

*   **AI-Powered Governance:** Provides real-time, auditable governance decisions across **10 live domains**: Trading, Islamic Credit, Insurance, Robotics, Medical AI, Autonomous Agents, Energy, Real Estate, Stablecoin Reserve, Defense. Each domain has a premium interactive governance demo at `/governance-demo-{domain}`.
*   **Cryptographically Secure Receipts:** Generates Post-Quantum Cryptography (PQC) signed receipts for every decision, publicly verifiable and W3C Verifiable Credential compatible.
*   **B2B API:** Offers a robust API for enterprise clients with API key authentication, RBAC, per-client quotas, webhooks, and Python/Node.js SDKs.
*   **Telegram Bot Interface:** An enterprise-grade Telegram bot allows users to interact with the governance engine, query data, and manage client access.
*   **Live Dashboards:** Provides multiple web dashboards (Investor Command Center, Audit Dashboard, Client Portal, vertical-specific dashboards) for real-time metrics, audit trails, and performance monitoring.
*   **Compliance & Audit Tools:** Includes features like StatusList2021 for VC revocation, State Provenance Guard, Conditional Bind Gate, and detailed logging for regulatory compliance and institutional audits.

## User preferences

*   _Populate as you build_

## Gotchas

*   **Gemini Billing:** Gemini API requires billing activation in Google Cloud Console (`console.cloud.google.com`) to remove usage limits.
*   **React Build:** Remember to run `npm run build` in `omnix_web/` and commit the `dist/` folder before pushing to `main` for Railway deployments.
*   **API Key Provisioning:** When provisioning new B2B API keys via `provision_b2b_client.py`, copy the key immediately as it's only displayed once.
*   **Production Safeguards:** Avoid setting `TESTING=true` in production environments; it bypasses critical security checks.
*   **Database Indices:** Ensure `CREATE INDEX idx_fce_domain_event_ts ON filter_calibration_events (domain, event_ts)` is applied for datasets larger than 50K rows, as per ADR-134.

## Pointers

*   **ADRs:** `docs/adr/` — 144 total (ADR-142: Breach Containment · ADR-143: Multi-Domain Risk · ADR-144: Auto-Modification Guard)
*   **Full Architecture:** `docs/current/ARCHITECTURE.md`
*   **Deployment Operations:** `docs/operations/DEPLOYMENT.md`
*   **Governance Modules Roadmap:** `docs/DASHBOARD_IMPROVEMENT_BACKLOG.md` § GOVERNANCE MODULES ROADMAP (Mar 2026)
*   **Python SDK Documentation:** `sdk/python/README.md`
*   **Node.js SDK Documentation:** `sdk/node/README.md`
*   **W3C Verifiable Credentials:** `omnixquantum.net/eidas` (frontend page)
*   **Auto-Modification Guard:** `omnix_core/governance/auto_modification_guard.py` — AMG central module (ADR-144)