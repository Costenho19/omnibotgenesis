# OMNIX V6.5.2 INSTITUTIONAL+ - Automated Trading System

## Overview

OMNIX V6.5.2 INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system designed for 24/7 operation with multi-user support for 100,000+ simultaneous users. Its primary purpose is paper trading to build a credible track record for investor presentations, targeting $400K seed funding at $2.5M valuation. Key capabilities include AI integration, post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory with On-Chain Data Intelligence, adaptive parameter calibration, institutional portfolio optimization, derivatives trading, and dual-market support for Kraken (crypto) and Alpaca (stocks). The system aims for 20-50 trades/day with a 55%+ win rate, multi-crypto scanning, and tiered signal strengths.

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
> 2. **APAGAR el workflow del bot ANTES de terminar la sesión**
> 3. Verificar que el workflow esté detenido
>
> **Razón**: Telegram solo permite UNA conexión activa por token. Si el bot corre en Replit y Railway al mismo tiempo, habrá conflictos y errores de conexión.

## System Architecture

### Core Engines

The system integrates several core engines:
-   **AutoTradingBot V6.4 PREMIUM**: Multi-crypto scanning, tiered signal strength, ramp-up system, HMM quality filter, drawdown protection.
-   **Non-Markovian Memory Kernel V6.5**: Detects regime transitions, recognizes cyclical patterns, performs memory coherence scoring, and integrates on-chain signals.
-   **Coherence Engine V6.5 ULTRA**: 6-Tier Veto System for validating strategy agreement, maintaining consistent thresholds (30%/45%) for trade quality and win rate > 55%.
-   **Multi-Crypto Scanner V6.5**: Scans 11 crypto pairs with proper Kraken symbol mapping.
-   **AI Risk Guardian V5.4**: Monitors for overtrading, drawdown, and prevents revenge trading.
-   **Portfolio Management V6.4 INSTITUTIONAL+**: Implements Goldman-Sachs level optimization, including Markowitz and Black-Litterman models, dynamic position sizing, exposure management, and risk detection.
-   **Derivatives Trading Module**: Supports paper/real trading modes, includes MarginEngine, KrakenFuturesClient, HedgingService, and FundingArbitrageAnalyzer.
-   **Stock Trading Premium V6.3 ULTRA**: Integrates 9 active institutional modules: Monte Carlo, Kalman Filter, HMM, ARES-STOCK, Non-Markovian Memory, Coherence Engine, Risk Guardian, Gap Protection, and Earnings Protector.
-   **Adaptive Parameter Engine V6.5 ULTRA**: Auto-calibration system for ARES strategies based on market regime.
-   **On-Chain Data Intelligence V6.5**: Provides institutional-grade blockchain analytics using free APIs for whale tracking, exchange flow, and smart money signals.

### Multi-User Architecture V6.5.2

Supports 100,000+ simultaneous users with isolated trading sessions, utilizing Redis for fast state management and PostgreSQL for persistence. Employs a ThreadPoolExecutor for parallel processing and per-user locks for thread safety.

### UI/UX Decisions

A web dashboard built with Flask provides multiple views (main, terminal-style, classic) and comprehensive API endpoints. The frontend uses Modular CSS (BEM Methodology) and Modular JavaScript (IIFE Pattern), with Jinja2 template inheritance. Key features include a dynamic status bar updating via `/api/health` and a prominent "PAPER TRADING" badge. Frontend JavaScript modules (`api.js`, `common.js`, `charts.js`) handle API calls with retry logic, shared logic, and efficient chart updates using `Plotly.react()` for delta rendering.

### Backend Architecture

The backend uses a Flask Blueprints architecture for modularity, with an application factory pattern, connection pooling for PostgreSQL, and modular route organization. ARES strategies are instantiated at the module level. All modules use tuple-based rows `row[n]` for database access.

### Dashboard API Endpoints

Provides endpoints for system health (`/api/health`), trading performance (`/api/metrics`), trade history (`/api/trades`), open positions with live prices (`/api/positions`), real-time crypto prices (`/api/ticker`), market sentiment (`/api/fear-greed`), and more.

### Data Flow

Market Data (Kraken/Alpaca) feeds into the Non-Markovian Kernel, boosted by On-Chain Intelligence, leading to Regime Detection and Signal Generation. This feeds the Adaptive Parameter Engine, which, after Coherence Engine Validation and a Risk Guardian Check, executes trades. Trades are persisted in PostgreSQL, and notifications are sent via Telegram.

### Project Structure

Organized into `omnix_core/` (core trading logic), `omnix_services/` (various system services), `omnix_dashboard/` (Flask web interface), `omnix_api/` (REST API), and `omnix_testing/` (validation suite).

## External Dependencies

### APIs and Services

-   **Kraken Exchange**: Primary crypto data and order execution.
-   **Alpaca**: Stock data and historical bars.
-   **Google Gemini (2.0 Flash)**: Primary AI model.
-   **OpenAI (GPT-4o, Whisper)**: AI services and transcription.
-   **Anthropic Claude**: AI fallback.
-   **CoinGecko**: Backup crypto prices and position fallback.
-   **ClankApp**: Whale transaction tracking.
-   **Arkham Intelligence**: Wallet identity enrichment.
-   **Alternative.me**: Fear and Greed Index.
-   **Finnhub**: Market news and sentiment.
-   **Alpha Vantage**: Technical indicators.
-   **ANU QRNG**: Quantum random numbers.

### Databases

-   **PostgreSQL (Railway)**: Main persistence for trades, analysis, conversations, balance history, derivatives, community intelligence, risk management, adaptive engine data, and user settings.
-   **Redis (Railway)**: Used for caching, state management, and rate limiting.

### Key Python Libraries

-   **Core Trading**: numpy, scipy, ccxt, pandas
-   **AI/ML**: google-generativeai, openai, anthropic
-   **Telegram**: python-telegram-bot
-   **Database**: psycopg (v3), redis
-   **HTTP**: requests, aiohttp, httpx, websockets
-   **Security**: pypqc (post-quantum)
-   **Reporting**: plotly, kaleido, reportlab, PyPDF2