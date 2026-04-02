# OMNIX — Decision Governance Infrastructure

## Overview
OMNIX is a domain-agnostic Decision Governance Infrastructure designed to govern high-stakes automated decisions across various sectors such as digital asset trading, Islamic credit, global insurance claims, and robotics pre-execution safety. It employs a consistent 11-checkpoint pipeline, including a Context Admission Gate (CAG) and Trajectory Invariant Enforcement (TIE), issuing a post-quantum cryptographically signed receipt for every decision. The project aims to establish a robust and auditable framework for automated decision-making.

Harold Nunes is the Solo Founder & CEO. The project is raising $500K pre-seed at a $3M pre-money valuation.

## User Preferences
### Communication
Simple, everyday language (Spanish primary).

### CRITICAL AGENT RULES (MANDATORY — ALWAYS)

> **RULE 1 — LANGUAGE**: EVERYTHING in English must be translated into Spanish before being presented to the user. Interfaces, messages, options, forms, instructions — EVERYTHING in Spanish. If something appears in English on screen or in a document and the user has to read it, translate it BEFORE they see it.

> **RULE 2 — WARN BEFORE IRREVERSIBLE ACTIONS**: Before the user performs any irreversible action (publishing to Zenodo, SSRN, uploading to Railway, sending emails, sharing on LinkedIn, deploying), proactively review EVERYTHING that might affect that action and warn BEFORE. Not after. Never after.

> **RULE 3 — PROACTIVE REVIEW**: Before considering any task finished, check for errors, inconsistencies, or pending items the user should know about. Do not wait for the user to discover them. If something could cause a future problem, say it now.

### Deployment Policy (CRITICAL)
- **Railway**: PRODUCTION (24/7) for bot + web.
- **Replit**: DEVELOPMENT for code editing and tests only.
- NEVER run the bot on Replit and Railway simultaneously due to Telegram's single active connection per token policy.

### Bot Testing Protocol (MANDATORY)
Every time the bot is activated on Replit for testing:
1. Perform the necessary tests.
2. **STOP the bot workflow BEFORE ending the session.**
3. Verify that the workflow is stopped.

## System Architecture

### Core Components and Design Patterns
OMNIX employs a hexagonal architecture featuring an AutoTradingBot, Non-Markovian Memory Kernel, and a 6-Tier Veto System (Coherence Engine). Key capabilities include AI-first command detection, Multilingual Prompt Architecture, Anti-Servile Post-Processing Filter, AI Risk Guardian, Confidence-Adaptive Entry System (CAES), Decision Engine, Monte Carlo VETO Engine, RMS Enforcement, Signal Integrity Validator (SIV), Forward Trajectory Implicator (FTI), Regime-Conditioned Kelly (RCK), and an Exit Governance Layer (EGL). It uses a Multi-Agent Governance System for weighted consensus, supported by Hybrid Cryptography (X25519 + Kyber-768 via HKDF), a Crypto-Agility Layer, and Quantum-Secure Decision Receipts with RFC 3161-style internal timestamps and a rolling Merkle root. All checkpoints are designed to be fail-closed.

### Key Gates and Vertical Controls
The system integrates a Context Admission Gate (CAG), Trajectory Invariant Enforcement (TIE), AML Governance Gate (CP-9), Fraud Detection Gate (CP-10), and Islamic Credit Governance Vertical. Decisions follow an 11-checkpoint pipeline (CP-0 to CP-10) and are PQC-signed.

### Public Sandbox — 11-Checkpoint Pipeline (`omnix_web/api/sandbox.py`)
This sandbox executes decisions through an 11-checkpoint pipeline, each with specific signal thresholds:
- CP-0: Signal Integrity Validation (≥ 60)
- CP-1: Probability Check (≥ 50)
- CP-2: Risk Limits (≤ 65)
- CP-3: Signal Coherence (≥ 55)
- CP-4: Trend Persistence (≥ 50)
- CP-5: Stress Resilience (≥ 35)
- CP-6: Logic Consistency (≥ 40)
- CP-7: Temporal Coherence (≥ 45)
- CP-8: Edge Confirmation (≥ 40)
- CP-9: AML Gate (≥ 15)
- CP-10: Fraud Detection Gate (≥ 30)

### Scoring Logic
Decision scoring combines EMA Regime Signal, HMM Regime, Kalman Filter, Non-Markovian Memory, and Kelly Criterion, enhanced by veto/penalty layers from Monte Carlo, Black Swan, Sentiment, and Quantum Momentum analyses.

### Shadow Portfolio + Learning Engine
A counterfactual analysis system continuously monitors vetoed trades to calibrate internal filters.

### Decision Contradiction Index (DCI)
The DCI quantifies internal signal divergence; a value of 70 or higher mandates a HOLD decision.

### Dashboard Features
The dashboard provides a Dual Win Rate Framework, enriched AI context, System Health Score, Live Status, Calibration Progress, and Recommended Actions.

### External Governance API (Flask Dashboard — B2B)
A B2B Flask endpoint (`omnix_dashboard/blueprints/governance.py`) allows external systems to submit signals to OMNIX's 6-checkpoint governance pipeline, returning a PQC-signed governance receipt. It features RBAC authentication, supports 6 normalized signals, and operates in a fail-closed manner. It is extended by five additive governance modules aligning with NIST AI RMF, ISO/IEC 42001, and the EU AI Act. This is a separate pipeline from the public sandbox.

### Public Verification Server (Railway)
A standalone `aiohttp` web server offers public receipt verification endpoints, ensuring zero internal data exposure through SHA-256 hash chains and Dilithium-3 PQC signatures.

### Public Governance Sandbox (`/try`)
This React page (`PublicGovernanceSandbox.tsx`) with a Flask backend (`omnix_web/api/sandbox.py`) allows users to interpret free-form scenarios into governance signals via Gemini AI, run them through the 11-checkpoint pipeline, and receive a PQC-signed receipt. It is rate-limited and requires no authentication.

### Public Decision Verification Page (`/verify/:receiptId`)
This React page (`PublicDecisionVerify.tsx`) displays governance decisions in English and Spanish, including decision status, a visual representation of the 11-checkpoint pipeline, a cryptographic integrity block, and an independent verification call to action. It's powered by Flask (`GET /api/public/verify/<receipt_id>`) and is rate-limited.

### Web Infrastructure (Production — Railway stellar-hope)
- **Railway's `$PORT`**: gunicorn serves Flask backend and React distribution.
- **Port 8000 on Railway**: Public verification `aiohttp` server.

## External Dependencies

### APIs and Services
- **Kraken Exchange**: Crypto data and order execution.
- **Alpaca**: Stock data and historical bars.
- **Google Gemini (Flash)**: Primary AI model.
- **OpenAI (GPT-4o, Whisper)**: AI services.
- **Anthropic Claude**: AI fallback.
- **ElevenLabs**: Text-to-speech.
- **CoinGecko**: Backup crypto prices.
- **Alternative.me**: Fear and Greed Index.
- **Finnhub**: Market news and sentiment.
- **Alpha Vantage**: Technical indicators.
- **Tavily**: Real-time web search for AI responses.
- **Stripe**: Payment processing.
- **ANU QRNG**: Quantum random numbers.

### Databases
- **PostgreSQL (Railway)**: Main persistence layer.
- **Redis (Railway)**: Caching, state management, and rate limiting.