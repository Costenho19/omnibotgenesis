# OMNIX — Decision Governance Infrastructure

## Overview
OMNIX is a domain-agnostic Decision Governance Infrastructure designed to govern high-stakes automated decisions across various sectors like digital asset trading, Islamic credit, global insurance claims, and robotics pre-execution safety. It employs a consistent 11-checkpoint pipeline, including a Context Admission Gate (CAG) and Trajectory Invariant Enforcement (TIE), issuing a post-quantum cryptographically signed receipt for every decision. The project aims to establish a robust and auditable framework for automated decision-making.

## User Preferences
### Communication
Simple, everyday language (Spanish primary).

### CRITICAL AGENT RULES (MANDATORY — ALWAYS)

> **RULE 1 — LANGUAGE**: EVERYTHING in English must be translated into Spanish before being presented to the user. Interfaces, messages, options, forms, instructions — EVERYTHING in Spanish. If something appears in English on screen or in a document and the user has to read it, translate it BEFORE they see it.

> **RULE 2 — WARN BEFORE IRREVERSIBLE ACTIONS**: Before the user performs any irreversible action (publishing to Zenodo, SSRN, uploading to Railway, sending emails, sharing on LinkedIn, deploying), proactively review EVERYTHING that might affect that action and warn BEFORE. Not after. Never after.

> **RULE 3 — PROACTIVE REVIEW**: Before considering any task finished, check for errors, inconsistencies, or pending items the user should know about. Do not wait for the user to discover them. If something could cause a future problem, say it now.

### Deployment Policy (CRITICAL)
| Environment | Purpose | Status |
|-------------|---------|--------|
| **Railway** | PRODUCTION (24/7) | Bot runs permanently |
| **Replit** | DEVELOPMENT | Code editing and tests only |

**NEVER run the bot on Replit and Railway simultaneously** - Telegram allows only ONE active connection per token.

### Workflow for Debugging
1.  **Railway Logs**: User provides logs directly for debugging
2.  **DO NOT start bot locally** - Use Railway logs provided
3.  **Code sync**: GitHub -> Railway auto-deploy from main branch
4.  **After testing on Replit**: ALWAYS stop workflow before ending session

### Bot Testing Protocol (MANDATORY)
> **MANDATORY RULE**: Every time the bot is activated on Replit for testing:
> 1. Perform the necessary tests
> 2. **STOP the bot workflow BEFORE ending the session**
> 3. Verify that the workflow is stopped
>
> **Reason**: Telegram only allows ONE active connection per token. If the bot runs on Replit and Railway at the same time, there will be conflicts and connection errors.

### Context Protocol (MANDATORY)

**Before executing any changes**, review the documentation in `docs/` to enrich the context:

| Priority | Files | Purpose |
|-----------|----------|-----------|
| **1. Critical** | `docs/README.md` | Main documentation index |
| **2. Critical** | `docs/MIGRATION_STATUS.md` | Consolidated V7.0 status |
| **3. Critical** | `docs/REAL_SYSTEM_STATUS.md` | Real system status |
| **4. Architecture** | `docs/current/` | ARCHITECTURE.md, HEXAGONAL_MIGRATION_STATUS.md, TECHNICAL_DEBT.md |
| **5. Audits** | `docs/compliance/audits/` | DATABASE_AUDIT_REPORT.md, INTERNAL_AUDIT_TRANSPARENCY.md, OMNIX_Security_Audit_v1.0_INTERNAL.md |
| **5b. Security** | `docs/compliance/` | SECURITY_OVERVIEW.md (public/pitch), CRYPTOGRAPHIC_ARCHITECTURE_OVERVIEW.md (institutional) |
| **5c. Data Integrity** | `docs/compliance/REAL_DATA_POLICY.md` | "All real, nothing invented" — prohibited patterns, JS helpers, anti-regression tests |
| **6. History** | `docs/history/` | Previous decisions, migrations, historical context |
| **7. Reference** | `docs/reference/` | TRACEABILITY_MATRIX.ADR.md, ADRs (incl. ADR-027 Decision Governance Infrastructure) |
| **8. Security** | `docs/reference/adr/ADR-022-post-quantum-cryptography.md` | PQC implemented Nov 2025 (Kyber-768/Dilithium-3) |

**After significant changes**, update the relevant documentation.

> **CRITICAL PQC**: Post-Quantum Cryptography IS ALREADY IMPLEMENTED since Nov 2025. The AI MUST NOT say "PQC planned for Q3 2026". Trading orders are signed with Dilithium-3. See ADR-022.

### Investor Challenge Response Framework (ADR-024)

When an investor asks about comparative trade-offs (opportunity cost, risk avoided, buy & hold vs, justify), the bot MUST respond with structure:

1.  **NUMBER FIRST**: Open with quantification (e.g., "Opportunity Cost: $847. Risk Avoided: $2,340. Net EV: +$1,493")
2.  **FRAMEWORK SECOND**: Explain how it was calculated (ADR-020 formulas, data freshness)
3.  **POSITIONING THIRD**: Clarify what OMNIX is ("governance infrastructure, not BTC hold competitor")

**PROHIBITED in investor_challenge:**
- "We are in a learning phase" (sounds like "trust without data")
- "It's difficult to quantify" without giving a formula
- "It's not a fair comparison" without explaining why

See ADR-024 for detection keywords and examples.

### Track Record Period Disclosure (MANDATORY)

| Period | Money Type | Dates | Trades | P&L | Purpose |
|---------|---------------|--------|--------|-----|-----------|
| **Phase 0 — Real Capital** | **REAL** (Kraken) | Jul 6 – Aug 18, 2025 | 1,115 | -$1,167 (-28.6%) | Real capital without governance |
| **Learning Baseline** | Paper (simulated) | Nov 2025 - Jan 14, 2026 | 119 | -$15,198.73 | Engine calibration |
| **Official Track Record** | Paper (simulated) | Jan 15, 2026 - present | 0 | $0 | Recalibrated validation |

> **CRITICAL RULE**: Phase 0 = real Kraken money. Learning Baseline and Track Record = simulated/paper money. NEVER mix in reports or investor responses.

### Dashboard Investor Credibility

| Metric | Behavior |
|---------|----------------|
| **Max DD** | Always ≤ 0% (normalized) |
| **Win Rate** | N/A when 0 trades in Track Record |
| **Header P&L** | Labeled "(Baseline)" to avoid confusion |
| **Est. Loss Avoided** | Capped at $100K with explanatory footnote |

**Est. Loss Avoided Formula:**
```
Est. Loss = Cycles × $20K × 2.5% = capped at $100K
```

> **RULE**: When the AI reports metrics (P&L, win rate, trades, losses), it MUST add at the end:
>
> **Period Note**: This data corresponds to the Learning Baseline (Nov-Dec 2025), calibration phase. Since January 15, 2026, the system operates with recalibrated parameters in the Official Track Record.

**Does NOT apply to**: greetings, commands, technical questions without metrics. See ADR-023.

### Security Documentation Strategy
**3-Tier Documentation Architecture:**

| Tier | Document | Audience | Content |
|------|----------|----------|---------|
| **Public** | `docs/compliance/SECURITY_OVERVIEW.md` | Pitch / Data Room | No exact metrics, high-level narrative |
| **Institutional** | `docs/compliance/CRYPTOGRAPHIC_ARCHITECTURE_OVERVIEW.md` | Institutional investors | PQC as strategic differentiator, governance advantages |
| **Internal** | `docs/compliance/audits/OMNIX_Security_Audit_v1.0_INTERNAL.md` | Due diligence deep dive | Full technical metrics, detailed audit results |

**Legal Language Rules:**
- Use "NIST-standardized algorithms" — NEVER "FIPS 204" or "FIPS 203"
- Use "Aligned with core SOC 2 security control principles" — NEVER "SOC 2 compliant" or "SOC 2 aligned"
- Use "Designed for ADGM/SEC regulatory frameworks" — NEVER "ADGM compliance ready"
- ADGM badge on web: "Designed for Compliance" (not "Target Jurisdiction")
- Footer/copyright: "Abu Dhabi, UAE" — no ADGM affiliation implied

**PQC Communication Tier Rules (CRITICAL — updated Feb 2026):**
| Tier | Audience | Allowed Language | Prohibited |
|------|-----------|-------------------|-----------|
| External | Bot, Telegram, web | "NIST-standardized algorithms", "post-quantum cryptography" | FIPS 203/204, "NIST Level 3", algorithm names |
| Institutional | Investors, partners | Names (Dilithium-3, Kyber-768), "NIST-standardized" | FIPS 203/204, "NIST Level 3 security equivalent" |
| Internal | ADRs, audits, code | All, including FIPS and NIST Level 3 | N/A |

**Kyber-768 is a KEM (Key Encapsulation Mechanism), NOT a data encryption algorithm.** Saying "Kyber-768 for data encryption" is a technical error that damages institutional credibility. Data encryption is done by AES/Fernet. See ADR-022.

### Team Narrative
-   **Harold Nunes**: Solo Founder & CEO — only name visible in all surfaces
-   **Ivan/Iván Guzman**: Removed from ALL files (code, docs, web, reports, audit)
-   If asked about technical help: "I've worked with contract developers and infrastructure consultants"

### Branding Policy
**Strategy**: Invisible internal versioning, stable external identity (like Stripe).

| Surface | Branding | Version |
|-------------------|---------|---------|
| **Dashboard UI** | "OMNIX Decision Governance" | None visible |
| **Bot AI Responses** | "OMNIX Decision Governance" | None visible |
| **Telegram Messages** | "OMNIX Decision Governance" | None visible |
| **Business/Investor Docs** | "OMNIX" or "OMNIX — Decision Governance Infrastructure" | None visible |
| **Technical Docs (H1)** | "OMNIX — [Topic]" | "Internal Build Reference: 6.5.4e" in metadata |
| **Source Code Constants** | N/A (internal) | VERSION = "6.5.4e", VERSION_NAME = "INSTITUTIONAL+" |
| **Source Code Docstrings** | N/A (internal) | May reference INSTITUTIONAL+ (internal only) |
| **Historical ADRs/Audits** | Preserved as-is | Historical context maintained |

**Rule**: NEVER use "V6.5.4e INSTITUTIONAL+" or version strings in any user-facing, investor-facing, or bot-facing output.

## System Architecture

### Core Components and Design Patterns
OMNIX utilizes a hexagonal architecture with an AutoTradingBot, Non-Markovian Memory Kernel, and a 6-Tier Veto System (Coherence Engine). Key capabilities include AI-first command detection, Multilingual Prompt Architecture, Anti-Servile Post-Processing Filter, AI Risk Guardian, Confidence-Adaptive Entry System (CAES), Decision Engine, Monte Carlo VETO Engine, RMS Enforcement, Signal Integrity Validator (SIV), Forward Trajectory Implicator (FTI), Regime-Conditioned Kelly (RCK), and an Exit Governance Layer (EGL). A Multi-Agent Governance System ensures weighted consensus, supported by Hybrid Cryptography (X25519 + Kyber-768 via HKDF), a Crypto-Agility Layer, and Quantum-Secure Decision Receipts with RFC 3161-style internal timestamps and a rolling Merkle root. All checkpoints are fail-closed.

### Key Gates and Vertical Controls
The system integrates a Context Admission Gate (CAG), Trajectory Invariant Enforcement (TIE), AML Governance Gate (CP-9), Fraud Detection Gate (CP-10), Jurisdiction Compliance Gate (CP-11), and Islamic Credit Governance Vertical. Decisions follow an 11-checkpoint pipeline and are PQC-signed.

### Scoring Logic
Decision scoring combines EMA Regime Signal, HMM Regime, Kalman Filter, Non-Markovian Memory, and Kelly Criterion, enhanced by veto/penalty layers from Monte Carlo, Black Swan, Sentiment, and Quantum Momentum analyses.

### Shadow Portfolio + Learning Engine
A counterfactual analysis system continuously monitors vetoed trades to calibrate internal filters.

### Decision Contradiction Index (DCI)
The DCI quantifies internal signal divergence; a value of 70 or higher mandates a HOLD decision.

### Dashboard Features
The dashboard provides a Dual Win Rate Framework, enriched AI context, System Health Score, Live Status, Calibration Progress, and Recommended Actions, built with Flask and Streamlit.

### External Governance API (Flask Dashboard — Port 5000)
A B2B Flask endpoint allows external systems to submit signals to OMNIX's 6-checkpoint governance pipeline, returning a PQC-signed governance receipt. It features RBAC authentication, supports 6 normalized signals, and operates in a fail-closed manner. This API is extended by five additive governance modules for Risk Mapping, Measurement & Monitoring, Human Oversight, Incident Management, and Governance Reporting, aligning with NIST AI RMF, ISO/IEC 42001, and the EU AI Act.

### Public Verification Server (Railway — Port 8000)
A standalone `aiohttp` web server offers public receipt verification endpoints, ensuring zero internal data exposure through SHA-256 hash chains and Dilithium-3 PQC signatures.

### Public Governance Sandbox (/try)
A public, no-authentication sandbox (React + Flask) allows Gemini AI to interpret free-form scenarios into governance signals, run them through the REAL 11-checkpoint pipeline, and store a PQC-signed receipt.

### Public Decision Verification Page (/verify/:receiptId)
A human-readable React page displays governance decisions in English and Spanish, showing: decision status, 11-checkpoint pipeline visualization, cryptographic integrity block, and independent verification CTA. It is powered by a Flask API (`GET /api/public/verify/<receipt_id>`) and is rate-limited without authentication.

### Web Infrastructure
The web infrastructure employs a multi-port architecture: OMNIX Web (Port 3000) for public landing pages (React + Vite), Flask Dashboard (Port 5000) for internal demonstrations and public API, and the Verification Server (Port 8000) for independent receipt validation.

## External Dependencies

### APIs and Services
-   **Kraken Exchange**: Crypto data and order execution.
-   **Alpaca**: Stock data and historical bars.
-   **Google Gemini (2.5 Flash)**: Primary AI model.
-   **OpenAI (GPT-4o, Whisper)**: AI services.
-   **Anthropic Claude**: AI fallback.
-   **ElevenLabs**: Text-to-speech.
-   **CoinGecko**: Backup crypto prices.
-   **Alternative.me**: Fear and Greed Index.
-   **Finnhub**: Market news and sentiment.
-   **Alpha Vantage**: Technical indicators.
-   **Tavily**: Real-time web search for AI responses.
-   **Stripe**: Payment processing.
-   **ANU QRNG**: Quantum random numbers.

### Databases
-   **PostgreSQL (Railway)**: Main persistence.
-   **Redis (Railway)**: Caching, state management, and rate limiting.