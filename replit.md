# OMNIX — Decision Governance Infrastructure

## Overview
OMNIX is a domain-agnostic Decision Governance Infrastructure designed to prevent high-stakes decision-making errors in automated systems, particularly in digital asset trading. Its core purpose is to provide reliable, error-free decision governance to protect capital and enhance financial integrity. The project aims to establish a secure and foundational infrastructure for automated decision-making, ensuring financial integrity and capital preservation.

## User Preferences
**Communication**: Simple, everyday language (Spanish primary).

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
> **REGLA OBLIGATORIA**: Cada vez que se active el bot en Replit para testing:
> 1. Realizar las pruebas necesarias
> 2. **APAGAR el workflow del bot ANTES de terminar la sesion**
> 3. Verificar que el workflow este detenido
>
> **Razon**: Telegram solo permite UNA conexion activa por token. Si el bot corre en Replit y Railway al mismo tiempo, habra conflictos y errores de conexion.

### Protocolo de Contexto (OBLIGATORIO)

**Antes de ejecutar cualquier cambio**, revisar la documentación en `docs/` para enriquecer el contexto:

| Prioridad | Archivos | Propósito |
|-----------|----------|-----------|
| **1. Crítico** | `docs/README.md` | Índice principal de documentación |
| **2. Crítico** | `docs/MIGRATION_STATUS.md` | Estado consolidado V7.0 |
| **3. Crítico** | `docs/REAL_SYSTEM_STATUS.md` | Estado real del sistema |
| **4. Arquitectura** | `docs/current/` | ARCHITECTURE.md, HEXAGONAL_MIGRATION_STATUS.md, TECHNICAL_DEBT.md |
| **5. Auditorías** | `docs/compliance/audits/` | DATABASE_AUDIT_REPORT.md, INTERNAL_AUDIT_TRANSPARENCY.md, OMNIX_Security_Audit_v1.0_INTERNAL.md |
| **5b. Seguridad** | `docs/compliance/` | SECURITY_OVERVIEW.md (público/pitch), CRYPTOGRAPHIC_ARCHITECTURE_OVERVIEW.md (institucional) |
| **5c. Data Integrity** | `docs/compliance/REAL_DATA_POLICY.md` | "Todo real, nada inventado" — prohibited patterns, JS helpers, anti-regression tests |
| **6. Historial** | `docs/history/` | Decisiones previas, migraciones, contexto histórico |
| **7. Referencia** | `docs/reference/` | TRACEABILITY_MATRIX.ADR.md, ADRs (incl. ADR-027 Decision Governance Infrastructure) |
| **8. Seguridad** | `docs/reference/adr/ADR-022-post-quantum-cryptography.md` | PQC implementado Nov 2025 (Kyber-768/Dilithium-3) |

**Después de cambios significativos**, actualizar la documentación relevante.

> **CRÍTICO PQC**: Post-Quantum Cryptography YA ESTÁ IMPLEMENTADO desde Nov 2025. La IA NO debe decir "PQC planificado para Q3 2026". Las órdenes de trading se firman con Dilithium-3. Ver ADR-022.

### Investor Challenge Response Framework (ADR-024)

Cuando un inversor pregunte sobre trade-offs comparativos (opportunity cost, risk avoided, buy & hold vs, justify), el bot DEBE responder con estructura:

1.  **NUMBER FIRST**: Abrir con cuantificación (ej: "Opportunity Cost: $847. Risk Avoided: $2,340. Net EV: +$1,493")
2.  **FRAMEWORK SECOND**: Explicar cómo se calculó (fórmulas ADR-020, data freshness)
3.  **POSITIONING THIRD**: Clarificar qué es OMNIX ("governance infrastructure, not BTC hold competitor")

**PROHIBIDO en investor_challenge:**
- "Estamos en fase de aprendizaje" (suena a "confía sin datos")
- "Es difícil cuantificar" sin dar fórmula
- "No es una comparación justa" sin explicar por qué

Ver ADR-024 para keywords de detección y ejemplos.

### Track Record Period Disclosure (OBLIGATORIO)

| Período | Tipo de dinero | Fechas | Trades | P&L | Propósito |
|---------|---------------|--------|--------|-----|-----------|
| **Phase 0 — Real Capital** | **REAL** (Kraken) | Jul 6 – Ago 18, 2025 | 1,115 | -$1,167 (-28.6%) | Capital real sin gobernanza |
| **Learning Baseline** | Paper (simulado) | Nov 2025 - 14 Ene 2026 | 119 | -$15,198.73 | Calibración del motor |
| **Track Record Oficial** | Paper (simulado) | 15 Ene 2026 - presente | 0 | $0 | Validación recalibrada |

> **REGLA CRÍTICA**: Phase 0 = dinero real Kraken. Learning Baseline y Track Record = dinero simulado/paper. NUNCA mezclar en reportes o respuestas al inversor.

### Dashboard Investor Credibility

| Métrica | Comportamiento |
|---------|----------------|
| **Max DD** | Siempre ≤ 0% (normalizado) |
| **Win Rate** | N/A cuando 0 trades en Track Record |
| **Header P&L** | Etiquetado "(Baseline)" para evitar confusión |
| **Est. Loss Avoided** | Capped a $100K con footnote explicativo |

**Fórmula Est. Loss Avoided:**
```
Est. Loss = Cycles × $20K × 2.5% = capped at $100K
```

> **REGLA**: Cuando la IA reporte métricas (P&L, win rate, trades, losses), DEBE agregar al final:
>
> **Nota de Período**: Estos datos corresponden al Learning Baseline (Nov-Dic 2025), fase de calibración. Desde el 15 de enero 2026, el sistema opera con parámetros recalibrados en el Track Record Oficial.

**NO aplica para**: saludos, comandos, preguntas técnicas sin métricas. Ver ADR-023.

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
| Tier | Audiencia | Lenguaje permitido | Prohibido |
|------|-----------|-------------------|-----------|
| External | Bot, Telegram, web | "NIST-standardized algorithms", "post-quantum cryptography" | FIPS 203/204, "NIST Level 3", nombres de algoritmos |
| Institutional | Inversores, partners | Nombres (Dilithium-3, Kyber-768), "NIST-standardized" | FIPS 203/204, "NIST Level 3 security equivalent" |
| Internal | ADRs, audits, código | Todo, incluyendo FIPS y NIST Level 3 | N/A |

**Kyber-768 es un KEM (Key Encapsulation Mechanism), NO un algoritmo de cifrado de datos.** Decir "Kyber-768 for data encryption" es un error técnico que daña la credibilidad institucional. El cifrado de datos lo hace AES/Fernet. Ver ADR-022.

### Team Narrative
-   **Harold Nunes**: Solo Founder & CEO — only name visible in all surfaces
-   **Ivan/Iván Guzman**: Removed from ALL files (code, docs, web, reports, audit)
-   If asked about technical help: "I've worked with contract developers and infrastructure consultants"
-   `institutional_report.py` team section: generic "contract developers" line, no individual names

### Branding Policy
**Strategy**: Invisible internal versioning, stable external identity (like Stripe).

| Surface | Branding | Version |
|-------------------|---------|
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
OMNIX utilizes a hexagonal architecture with an AutoTradingBot, Non-Markovian Memory Kernel, and a 6-Tier Veto System (Coherence Engine). It integrates multiple AI providers with AI-first command detection, a Multilingual Prompt Architecture, and an Anti-Servile Post-Processing Filter. Key features include an AI Risk Guardian, Confidence-Adaptive Entry System (CAES), Decision Engine, Monte Carlo VETO Engine, and RMS Enforcement. Signal Integrity Validator (SIV), Forward Trajectory Implicator (FTI), Regime-Conditioned Kelly (RCK), and an Exit Governance Layer (EGL) are central. A Multi-Agent Governance System uses 3 specialized agents for weighted consensus. Hybrid Cryptography (X25519 + Kyber-768 via HKDF) and a Crypto-Agility Layer are implemented, alongside Quantum-Secure Decision Receipts with RFC 3161-style internal timestamps and a rolling Merkle root.

**Context Admission Gate (CAG):** A session-level pre-admission gate that evaluates 4 global market condition parameters before any signal enters the 8-checkpoint pipeline.

### Hierarchical Veto Flow
Entry decisions pass through an 8-checkpoint pipeline, while exit decisions follow a 3-gate EGL pipeline. All checkpoints generate PQC-signed receipts and operate in a fail-safe manner.

### Scoring Logic
Decision scoring combines inputs from EMA Regime Signal, HMM Regime, Kalman Filter, Non-Markovian Memory, and Kelly Criterion, with additional veto/penalty layers from Monte Carlo, Black Swan, Sentiment, and Quantum Momentum analyses.

### Shadow Portfolio + Learning Engine
A counterfactual analysis system monitors vetoed trades to refine filter calibration.

### Decision Contradiction Index (DCI)
The DCI quantifies internal signal divergence to explain HOLD decisions; a high DCI (≥70) mandates a HOLD.

### Dashboard Features
The dashboard provides a Dual Win Rate Framework, enriched AI context, System Health Score, Live Status, Calibration Progress, and Recommended Actions. Dashboards are built using Flask and Streamlit.

### External Governance API (Flask Dashboard — Port 5000)
This B2B endpoint allows external systems to submit signals for processing through OMNIX's 6-checkpoint governance pipeline, returning a PQC-signed governance receipt. It uses RBAC authentication, supports 6 normalized signals, and operates in a fail-closed manner. Custom checkpoint thresholds are stored in PostgreSQL, with fail-closed fallback to defaults. Client payloads are encrypted at rest using Fernet.

### Governance Compliance Modules
Five additive governance modules extend the External Governance API, aligning with NIST AI RMF, ISO/IEC 42001, and the EU AI Act. These modules introduce new PostgreSQL tables and REST endpoints for Risk Mapping, Measurement & Monitoring, Human Oversight, Incident Management, and Governance Reporting.

### Public Verification Server (Railway — Port 8000)
A standalone `aiohttp` web server provides public receipt verification endpoints, ensuring zero internal data exposure through SHA-256 hash chains and Dilithium-3 PQC signatures.

### Public Governance Sandbox (/try)
A public, no-auth sandbox (React + Flask) allows Gemini AI to interpret free-form scenarios into 8 governance signals, run them through the REAL 8-checkpoint pipeline, and store a PQC-signed receipt. The receipt CTA links to the local `/verify/:receiptId` page for a human-readable governance report.

### Public Decision Verification Page (/verify/:receiptId)
A human-readable React page displays any governance decision in plain English and Spanish, showing: decision status banner (APPROVED/BLOCKED/HOLD), 8 checkpoint pipeline visualization, cryptographic integrity block, and independent verification CTA. It is powered by a Flask API (`GET /api/public/verify/<receipt_id>`) and is rate-limited (30 req/min) without requiring authentication.

### Web Infrastructure
The project uses a multi-port architecture: OMNIX Web (Port 3000) for public landing pages (React + Vite), Flask Dashboard (Port 5000) for internal demonstrations and public API, and the Verification Server (Port 8000) for independent receipt validation.

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