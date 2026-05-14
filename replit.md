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

*   **ADRs:** `docs/adr/` — 155 total. Last: ADR-152 (GTPD) · ADR-153 (NUA) · ADR-154 (Receipt Genealogy) · ADR-155 (Chain Completeness Score)
*   **Governance Baseline:** `docs/GOVERNANCE_BASELINE.md` — OMNIX-BASELINE-2026-Q2-001 · 11 invariants · 151 ADRs · Architecture Freeze
*   **ISR Remediation modules:** `omnix_core/governance/assumption_validity_monitor.py` (ISR-001 registry) · `omnix_core/governance/avm_db_bridge.py` (ISR-001 tenant DDL) · `omnix_core/governance/semantic_version_registry.py` (ISR-008) · `omnix_core/evidence/decision_receipt.py` (ISR-008+ISR-010 hash_version) · `omnix_core/evidence/receipt_wal.py` (ISR-012 WAL) · `omnix_core/evidence/transparency_chain.py` (ISR-013 retry+pending · ISR-022 read-path verify) · `omnix_services/ai_service/input_sanitizer.py` (ISR-017) · `omnix_core/evidence/payload_key_manager.py` (ISR-021) · `omnix_web/api/gov_blueprint.py` (ISR-017+ISR-021 wired)
*   **LLM Isolation Boundary:** `omnix_core/governance/llm_isolation_boundary.py` — ADR-148 · 22 approved signal keys · crossing log · strict mode
*   **Memory Context Governance:** `omnix_core/governance/memory_context_auditor.py` — ADR-151 · INV-011 · ContextSnapshot · MemoryAttestationRecord (MAR) · PQC-signed · 5 contamination layers · context drift detection · audit_context() convenience API · bidirectional receipt↔MAR chain · 91 tests
*   **Replay Fidelity:** `omnix_core/simulation/governance_replay.py` — ADR-149 · ReplayFidelityClass · verify_replay_chain() · v1.1.0
*   **Operational Readiness:** `omnix_core/ops/health_check.py` + `omnix_core/ops/operational_alerts.py` + `omnix_web/api/health_blueprint.py` — ADR-150 · /api/health · /api/health/live · /api/health/ready · Telegram ops alerts
*   **RC-1 Release Notes:** `docs/operations/RC1_RELEASE_NOTES.md` — v6.6.0 · 150 ADRs · 233 tests · 10 invariants
*   **RC-1 Verification Script:** `scripts/verify_rc1.py` — `python scripts/verify_rc1.py`
*   **Architecture Page:** `/architecture` — 6 interactive diagrams · pipeline · receipt lifecycle · LLM boundary · tenant isolation · trust anchor · authority matrix
*   **Institutional Demo:** `/show` — Demo narrativa de 6 pasos · evaluación en vivo con API real · receipt verificable · crisis replay FTX · DR stats · CTA book demo
*   **Health Monitoring Runbook:** `docs/operations/HEALTH_MONITORING.md` — OMNIX-OPS-001 · incident runbooks INC-001–004
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
*   **External Trust and Defensibility Report — Stage 4:** `docs/EXTERNAL_TRUST_AND_DEFENSIBILITY_REPORT.md` — HGA-2026-Q4-001 (Mayo 2026) — adversarial verifier tests, legal wording audit (52 claims), trust anchor validation, multi-instance consistency, enterprise security review, chain-of-custody gaps, 17 ranked actions
*   **Institutional Survivability Report — Stage 5:** `docs/INSTITUTIONAL_SURVIVABILITY_REPORT.md` — ISR-2026-Q2-001 (Mayo 2026) — 23 risk vectors, multi-tenant isolation gaps (AVM singleton ISR-001 CRITICAL), long-term replay fragility (ISR-008 CRITICAL), prompt injection (ISR-017), economic attack vectors, jurisdictional conflict gaps, institutional corruption vectors, dependency failure modes, future evolution risks
*   **ISR Remediation — Stage 5 Implementation:** `tests/test_isr_remediation.py` — 54 tests · 54 passing · ISR-001 ✓ ISR-008 ✓ ISR-013 ✓ ISR-017 ✓ ISR-021 ✓
*   **RC-1 Production Verification Report:** `docs/operations/RC1_PRODUCTION_VERIFICATION.md` — OMNIX-PVR-2026-001 · May 10, 2026 · 6/6 subsystems UP · pqc_mode=dilithium3-persistent · wal_pending=0 · Evidence baseline for institutional demos and audits
*   **Backup & Disaster Recovery Runbook:** `docs/operations/BACKUP_RUNBOOK.md` — OMNIX-OPS-002 · Procedure completa: pg_dump, env vars, PQC key backup, git bundle, recovery scenarios
*   **Disaster Recovery Test Report:** `docs/operations/DISASTER_RECOVERY_TEST.md` — OMNIX-DRT-2026-001 · May 10, 2026 · 7/7 fases PASSED · 500/500 firmas PQC válidas · AVM 11/11 · Replay Engine operativo · RTO ~4h confirmado · Hallazgo clave: receipts son auto-verificables (clave embebida)
*   **Cost & Sustainability Report:** `docs/operations/COST_SUSTAINABILITY_REPORT.md` — OMNIX-CSR-2026-001 · Mayo 2026 · DB=4.77GB · ~$50/month · análisis de reducción · postura por etapa de crecimiento
*   **Agent Trust Fabric (ATF):** `omnix_core/agents/atf/` — ADR-156 · Criptografía AI→AI · AgentIdentity (AID) · DelegationReceipt (ATFDR) · TrustLattice (DAG) · Monotonic Authority Reduction (MAR) · Verificación independiente sin acceso a plataforma · ATF Chain Completeness Score · API: `/api/atf/*` · Página: `/agent-trust-fabric` · Tests: `tests/test_agent_trust_fabric.py`
*   **ATF Formal Standard (RFC-ATF-1):** `docs/standards/RFC-ATF-1.md` — Especificación IETF-style completa · ABNF grammar · 6 invariantes · 3 niveles de compliance · security considerations · algoritmo ML-DSA-65 (FIPS 204)
*   **ATF Public Verifier CLI:** `omnix_web/public/omnix_atf_verify.py` — Verificador offline standalone · modos: receipt / chain / agent / replay · sin acceso a plataforma (ATF-INV-006) · output JSON · color terminal
*   **ATF Public Verifier Page:** `/atf-verify` — Página React pública para verificar DRs · verificación por ID o JSON pegado · resultado visual completo · CCS display
*   **Temporal Authority (ADR-157):** `omnix_core/agents/atf/temporal_authority.py` — TemporalAdmissibilityRecord (ATFTAR-{16HEX}) · TemporalAuthorityEngine · prueba nanosegundo-precisa de autoridad en el momento de ejecución · TAR-INV-001/005 · DB: atf_temporal_records · API: `/api/atf/temporal/*`
*   **Cross-Domain Trust (ADR-158):** `omnix_core/agents/atf/domain_bridge.py` — DomainTranslationReceipt (ATFDTR-{16HEX}) · CrossDomainBridge · descuento por par de dominios (HEALTHCARE→FINANCE: 30%, etc.) · CDTP-INV-001/006 · DB: atf_domain_bridges · API: `/api/atf/translate/*`
*   **TLA+ Formal Verification:** `docs/formal/ATF-TLA-SPEC.tla` + `docs/formal/ATF-FORMAL-VERIFICATION.md` — 5 propiedades formales: MAR, MAR Chain, Acyclicity, ChainRootConsistency, Immutability · Misma metodología que AWS DynamoDB
*   **ATF ADR-157:** `docs/adr/ADR-157-temporal-authority-admissibility.md`
*   **ATF ADR-158:** `docs/adr/ADR-158-cross-domain-trust-portability.md`
*   **ATF Governance Connector:** `omnix_core/agents/atf/atf_connector.py` — ATFConnector · ATFContext · embed_in_receipt() · verify_chain() · bridges governance pipeline with DR+TAR+GovernanceReceipt triple · non-blocking (ATF failure never halts governance) · usage: `ATFConnector.admit(agent_id, delegation_id, task_action, execution_ref)` → `ATFConnector.embed_in_receipt(receipt, atf_ctx)`
*   **ATF Standard Page:** `/atf-standard` — página pública RFC-ATF-1 · premium phrase · 4 proof claims · trust chain diagram · quick verifier widget · JSON examples (DR/TAR/DTR/Receipt+ATF) · standards track · CLI verifier · regulatory alignment (EU AI Act, DORA, MiCA, SOC 2, ISO 27001, NIST AI RMF) · priority banner
*   **Priority Record:** `docs/zenodo/OMNIX-ATF-PRIORITY-RECORD.md` — OMNIX-PAR-2026-ATF-001 · anchor hash d7082c2c1df7b0a2bd3c6f586f6f59143df8eaede369354e3f8afeb7c0c2b2f5 · Zenodo submission guide · SSRN abstract · GitHub release YAML · arXiv abstract · distinction from W3C VC/JWT/OAuth/LangChain
*   **ATF Claims Audit (INTERNAL):** `docs/OMNIX-ATF-CLAIMS-AUDIT.md` — OMNIX-AUDIT-ATF-2026-001 · 6 GREEN claims (state confidently) · 7 YELLOW claims (qualified language) · 3 RED actions (fix applied) · recommended public positioning statement · next actions checklist
*   **ATF Whitepaper (Institutional):** `docs/atf/OMNIX-ATF-WHITEPAPER.md` — OMNIX-WP-ATF-2026-001 · ~22pp · RFC/NIST/IETF style · Problem Statement · Architecture · Invariants · Crypto spec · TAR protocol · Cross-domain · GovernanceReceipt integration · Compliance levels · Interoperability · Threat references · References
*   **ATF Threat Model (Formal):** `docs/atf/ATF-THREAT-MODEL.md` — OMNIX-TM-ATF-2026-001 · 9 threat classes · STRIDE + ATF taxonomy · TM-001 Replay · TM-002 DR Forgery · TM-003 Privilege Amplification · TM-004 Clock Drift · TM-005 Chain Poisoning · TM-006 Orphan Delegation · TM-007 DAG Cycle · TM-008 Cross-TAR Forgery · TM-009 Budget Inflation · residual risk table · deployment recommendations
*   **ATF Explained (Plain Language):** `/atf-explained` — Página pública non-technical · One-liner hero · 4 sentence breakdown · analogy (power of attorney for AI) · 3 documents explained in plain language · who needs this and why · links to technical docs
*   **ATF Submission Guide:** `docs/zenodo/OMNIX-ATF-SUBMISSION-GUIDE.md` — OMNIX-SUB-ATF-2026-001 · Step-by-step: GitHub tag → Zenodo DOI → SSRN → arXiv · exact metadata fields · exact release body · BibTeX block · timeline (Day 0-2)
*   **SSRN Preprint (PUBLISHED):** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6757339 — Abstract ID 6757339 · Submitted 2026-05-13 · Under review · Title: RFC-ATF-1: Agent Trust Fabric
*   **Zenodo (PUBLISHED):** https://doi.org/10.5281/zenodo.20155016 — DOI: 10.5281/zenodo.20155016 · Published 2026-05-13 · Version 1.0.0 · 3 files (PDF + RFC-ATF-1.md + ATF-TLA-SPEC.tla)
*   **RFC-ATF-2 (DRAFT):** `docs/standards/RFC-ATF-2.md` — OMNIX QUANTUM Open Standard · May 2026 · Extension to RFC-ATF-1 · Covers RGC (ADR-159): RCR, CES, AFG, Escalation Protocol, RC Protocol · 8 new invariants (RGC-INV-001–008) · 14 total ATF invariants · ATF-RGC-Compliant compliance tier · Wire format, persistence schema, 9 API endpoints · Compliance: EU AI Act Art.9/13, DORA, MiCA, SOC 2, ISO 27001, NIST AI RMF · Pending Zenodo submission
*   **ATF Multi-Protocol Verifier:** `/atf-verify` — Verifica DR (RFC-ATF-1) · TAR (ADR-157) · RCR (RFC-ATF-2) · CES gauge animado · cadena de continuidad visual · stack L1–L4 indicator · CLI commands · completely rebuilt from single-artifact to multi-protocol
*   **ATF Differentiator Validation Report:** `docs/audits/ATF-DIFFERENTIATOR-VALIDATION.md` — OMNIX-AUDIT-ATF-DV-2026-001 · 55/55 tests PASS (100%) · 11 áreas: DR, MAR, Lattice, TAR, Triple Chain, Offline, Replay, CrossDomain, PublicVerifier, Invariants, Threats · Código real sin mocks · Script: `scripts/atf_deep_audit.py`
*   **Runtime Governance Continuity (ADR-159):** `omnix_core/agents/atf/runtime_continuity.py` — ATFRCR-{16HEX} · RuntimeContinuityEngine · ContinuityEligibilityScore (CES = T×0.30 + B×0.30 + D×0.20 + I×0.20) · 5 niveles (NOMINAL/MONITORING/WARNING/CRITICAL/HALT) · AuthorityFragmentationGuard (RGC-INV-004) · ContinuityEscalationEvent (ATFCEE-{16HEX}) · ReauthorizationChallenge (ATFRC-{16HEX}) · 82 tests PASS · API: `/api/atf/continuity/*` + `/api/atf/escalations/*` · ADR: `docs/adr/ADR-159-runtime-governance-continuity.md` · Cierra el gap de gobernanza en tiempo de ejecución identificado por Akhilesh Warik · 5 claims de patente documentados
