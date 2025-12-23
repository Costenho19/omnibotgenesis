# OMNIX V6.5.4d INSTITUTIONAL+

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
The system supports both single-user (OWNER role) and multi-user modes, with a Flask Dashboard for API and web terminal, and a Streamlit Dashboard for interactive visualization. AuthorizationService is integrated into AutoTradingBot, supporting granular permissions and user roles (FREE, BASIC, PRO, PREMIUM, OWNER).

Recent enhancements include an Asset Quarantine System for capital protection, a Real-Time Latency Monitor for system performance, a Price Stale Detection System to prevent trading on outdated prices, and an Admin Alerts System for critical events. The UI has been refactored for an "Investor-Ready" presentation, eliminating negative language and showing only verified data or loading states. Investor-Grade Automated Responses, triggered by context scoring or forced activation, provide institutional language for investor queries.

#### Autotrading Command (Dec 23, 2025)
- **BUG FIX**: `/autotrading activar ACEPTO` saves `risk_disclosure_accepted=True` before toggle
- **LANGUAGE**: All disclaimers use institutional language (no "disclaimer de riesgo", no "podrías perder todo")
- **PERSISTENCE**: Once started with `/autotrading start`, state is saved to PostgreSQL and survives Railway restarts
- **OWNER**: Must start autotrading once; state persists in DB for continuous 24/7 operation

### Trading Profiles System
Configurable profiles (e.g., INSTITUTIONAL, PAPER_AGGRESSIVE, PRODUCTION_STABLE) adjust trading parameters. `PRODUCTION_STABLE V6.5.4c` is the active profile.

### Hexagonal Architecture (V7.0 - Structure Complete, Activation Pending)
The system employs a hexagonal architecture with 20 ports (17 driven + 3 driver) and 22 adapters. All feature flags are currently `false`, meaning the system operates with legacy code. Activation is planned via the Strangler Fig pattern.

### AI Service Architecture
Refactored with SOLID principles and dependency injection, integrating interfaces and providers (Gemini, OpenAI, Anthropic). It features a voice service, AI-first command detection (only `/` prefixed messages are commands), and an AI-First Multilingual Prompt Architecture with English system prompts, dynamic language detection (using `fast-langdetect` and Gemini AI), and a Chain-of-Thought Framework. Language detection is concurrency-safe and uses Redis for persistence.

### Error Handling System
An `ai_error_handler.py` provides an `ErrorClassifier` with 8 categories, SDK-specific error detection, intelligent retry/failover with exponential backoff for retryable errors, and structured logging.

### Web Search Service Architecture
Structured with an `IntentDetector`, `SearchManager`, and `TavilySearch` client for intent-based web searches.

### Current Project Structure
The project is structured with `src/omnix/` containing the hexagonal V7.0 architecture, while `omnix_core/`, `omnix_services/`, `omnix_config/`, `omnix_dashboard/`, and `omnix_api/` contain essential legacy components.

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