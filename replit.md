# OMNIX V6.5.4d INSTITUTIONAL+

---
## MANDATORY PROTOCOL - READ FIRST
---

> **BEFORE making ANY code changes, you MUST review the documentation in `docs/` to understand the current system state.**
> 
> **AFTER making significant changes, you MUST update the relevant documentation.**
> 
> **Failure to follow this protocol leads to inconsistencies, bugs, and wasted effort.**

See [Protocolo de Contexto](#protocolo-de-contexto-obligatorio) below for the complete checklist.

---

## Overview
OMNIX V6.5.4d INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system. Its primary purpose is paper trading to build a credible track record for investor presentations, targeting $1M seed funding at an $11.5M pre-money valuation. Key capabilities include AI integration, post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory, adaptive parameter calibration, institutional portfolio optimization, derivatives trading, and dual-market support for Kraken (crypto) and Alpaca (stocks). The system aims for 3-5 trades/day with a 55%+ win rate, multi-crypto scanning, and tiered signal strengths.

## User Preferences
**Communication**: Simple, everyday language (Spanish primary).

### Deployment Policy (CRITICAL)
| Environment | Purpose | Status |
|-------------|---------|--------|
| **Railway** | PRODUCTION (24/7) | Bot runs permanently |
| **Replit** | DEVELOPMENT | Code editing and tests only |

**NEVER run the bot on Replit and Railway simultaneously** - Telegram allows only ONE active connection per token.

### Workflow for Debugging
1. **Railway Logs**: User provides logs directly for debugging
2. **DO NOT start bot locally** - Use Railway logs provided
3. **Code sync**: GitHub -> Railway auto-deploy from main branch
4. **After testing on Replit**: ALWAYS stop workflow before ending session

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
| **5. Auditorías** | `docs/compliance/audits/` | DATABASE_AUDIT_REPORT.md, INTERNAL_AUDIT_TRANSPARENCY.md |
| **6. Historial** | `docs/history/` | Decisiones previas, migraciones, contexto histórico |
| **7. Referencia** | `docs/reference/` | TRACEABILITY_MATRIX.md, ADRs |

**Después de cambios significativos**, actualizar la documentación relevante.

## System Architecture

### Core Engines
The system integrates AutoTradingBot, Non-Markovian Memory Kernel, Coherence Engine (6-Tier Veto System), AI Risk Guardian, Portfolio Management, CAES (Confidence-Adaptive Entry System), On-Chain Data Intelligence, Execution Protocol, InstitutionalDecisionLogger, and InstitutionalMetricsCalculator.

### Multi-User and Dashboard Architecture

> **ADVERTENCIA CRÍTICA (Dec 20, 2025):** La arquitectura multi-usuario documentada NO está implementada.
> 
> **Estado Real:**
> - `user_id` hardcodeado a `'7014748854'` (Harold) en 6 ubicaciones de AutoTradingBot
> - `UserSessionManager` NO EXISTE (documentación aspiracional)
> - Row-Level Security NO implementado en PostgreSQL
> - 2 usuarios simultáneos compartirían posiciones y balances
>
> **Documentación completa:** `docs/current/MULTI_USER_ARCHITECTURE.md`

**Capacidad TEÓRICA:** 100,000+ usuarios simultáneos con sesiones aisladas.  
**Capacidad REAL:** Single-tenant (todos los trades van a una cuenta).

Features a Flask Dashboard for API and web terminal, and a Streamlit Dashboard for interactive visualization.

### Trading Profiles System
Configurable profiles (e.g., INSTITUTIONAL, PAPER_AGGRESSIVE, PRODUCTION_STABLE) adjust trading parameters. `PRODUCTION_STABLE V6.5.4c` is the active profile.

### Hexagonal Architecture (V7.0 Migration Completed)
The system fully employs a hexagonal architecture, with all 17 ports and 19 adapters implemented, including Bootstrap & Config, Domain & Application layers, and Infrastructure Adapters (KrakenAdapter, GeminiAdapter). A feature flag `USE_APP_LAYER=true` confirms the new application layer is active.

### AI Service Architecture
Refactored with SOLID principles and dependency injection, integrating interfaces and providers (Gemini, OpenAI, Anthropic). Features include a voice service for dual text+audio responses (when `VOICE_SERVICE_AVAILABLE=true`) and AI-first command detection where only messages starting with `/` are treated as commands, otherwise text is sent to AI. The system uses an AI-First Multilingual Prompt Architecture with all system prompts rewritten in English, a Prompt Specification Layer, dynamic language detection, and a Chain-of-Thought Framework.

#### AI-First Multilingual Concurrency (Dec 19, 2025)
- **Concurrency-Safe Language Detection**: Uses `threading.Lock` for sync paths and `asyncio.to_thread()` for async paths to prevent language bleed between concurrent users
- **Redis Language Persistence**: Stores detected language per `chat_id` with 24h TTL for fallback scenarios (`omnix:user_language:{chat_id}`)
- **English Universal Placeholders**: All fallback/error messages are minimal English only - AI generates localized responses
- **NO Hardcoded Multilingual Dictionaries**: AI-first means Gemini generates all localized content based on system prompt directive

### Error Handling System
An `ai_error_handler.py` provides an `ErrorClassifier` with 8 categories, SDK-specific error detection, intelligent retry/failover with exponential backoff for retryable errors, and structured logging.

### Web Search Service Architecture
Structured with an `IntentDetector`, `SearchManager`, and `TavilySearch` client for intent-based web searches.

### Current Project Structure
The project is structured with `src/omnix/` containing the hexagonal V7.0 architecture (ports, infrastructure, domain, application, bootstrap), while `omnix_core/`, `omnix_services/`, `omnix_config/`, `omnix_dashboard/`, and `omnix_api/` contain essential legacy components.

## External Dependencies

### APIs and Services
-   **Kraken Exchange**: Primary crypto data and order execution.
-   **Alpaca**: Stock data and historical bars.
-   **Google Gemini (2.0 Flash)**: Primary AI model.
-   **OpenAI (GPT-4o, Whisper)**: AI services.
-   **Anthropic Claude**: AI fallback.
-   **CoinGecko**: Backup crypto prices.
-   **Alternative.me**: Fear and Greed Index.
-   **Finnhub**: Market news and sentiment.
-   **Alpha Vantage**: Technical indicators.
-   **Tavily**: Real-time web search for AI responses.
-   **ANU QRNG**: Quantum random numbers.

### Databases
-   **PostgreSQL (Railway)**: Main persistence for trades, analysis, conversations, balance history, derivatives, community intelligence, risk management, adaptive engine data, and user settings.
-   **Redis (Railway)**: Caching, state management, and rate limiting.