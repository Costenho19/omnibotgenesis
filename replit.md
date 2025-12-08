# OMNIX V6.5.4 INSTITUTIONAL+ - Automated Trading System

## Overview

OMNIX V6.5.4 INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system designed for 24/7 operation with multi-user support. Its primary purpose is paper trading to build a credible track record (500+ trades, 55%+ win rate) for investor presentations, targeting **$1M seed funding at $11.5M pre-money valuation** from UAE/GCC investors. Key capabilities include AI integration, post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory with On-Chain Data Intelligence, adaptive parameter calibration, institutional portfolio optimization, derivatives trading, and dual-market support for Kraken (crypto) and Alpaca (stocks). The system aims for 20-50 trades/day with a 55%+ win rate, multi-crypto scanning, and tiered signal strengths.

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

## System Architecture

### Core Engines

-   **AutoTradingBot V6.5.4 INSTITUTIONAL+**: Multi-crypto scanning, tiered signal strength, ramp-up system, HMM quality filter, drawdown protection, V6.5.4 position limit early-check.
-   **Non-Markovian Memory Kernel V6.5**: Detects regime transitions, recognizes cyclical patterns, performs memory coherence scoring, and integrates on-chain signals.
-   **Coherence Engine V6.5 ULTRA**: 6-Tier Veto System for validating strategy agreement, maintaining consistent thresholds (30%/45%) for trade quality and win rate > 55%.
-   **Multi-Crypto Scanner V6.5**: Scans 11 crypto pairs with proper Kraken symbol mapping.
-   **AI Risk Guardian V5.4**: Monitors for overtrading, drawdown, and prevents revenge trading. Hard cap of $20K max trade size.
-   **Portfolio Management V6.4 INSTITUTIONAL+**: Goldman-Sachs level optimization, Markowitz and Black-Litterman models, dynamic position sizing.
-   **Derivatives Trading Module**: Paper/real trading modes, MarginEngine, KrakenFuturesClient, HedgingService.
-   **Stock Trading Premium V6.3 ULTRA**: 9 active institutional modules: Monte Carlo, Kalman Filter, HMM, ARES-STOCK, Non-Markovian Memory, Coherence Engine, Risk Guardian, Gap Protection, Earnings Protector.
-   **Adaptive Parameter Engine V6.5 ULTRA**: Auto-calibration for ARES strategies based on market regime.
-   **CAES V6.5.4 (Confidence-Adaptive Entry System)**: Dynamic position sizing based on Non-Markovian Kernel confidence using sigmoid aggression function. Caps: 0.5x-3.0x multiplier with safety limits, without artificial bias.
-   **On-Chain Data Intelligence V6.5**: Institutional-grade blockchain analytics using free APIs.
-   **Fear & Greed Contrarian Strategy V6.5.4**: Applies in both paper and real modes with appropriate contrarian and extreme fear boosts.
-   **Web Search Service V6.5.4**: Real-time internet search via Tavily API. Auto-detects queries about news/events/current data. Redis cache (15min TTL), rate limiting (30/min).
-   **Execution Protocol V6.5.4 INSTITUTIONAL+ PREMIUM**: 4-layer institutional-grade trade execution system (Citadel/Jump Trading level) including LiquidityAnalyzer, MicroVolatilityEngine, CrossAssetCorrelationEngine, and ExecutionProtocol orchestrator for dynamic decision-making (TWAP/VWAP/ICEBERG).
-   **InstitutionalDecisionLogger V6.5.4**: Investor-grade audit trail logging for all trade decisions. Emits structured JSON events (TRADE_CANDIDATE, VETO_COHERENCE, VETO_CONSENSUS, VETO_DRAWDOWN, VETO_RISK_GUARDIAN, VETO_HMM_REGIME, VETO_POSITION_LIMIT, TRADE_VALIDATED, TRADE_EXECUTED, TRADE_REJECTED, AI_NARRATIVE) with unique decision_id for lifecycle correlation. Compatible with Grafana/Loki/ELK. Located in `omnix_core/utils/logger.py`.
-   **Volatility-Based SL/TP Classification V6.5.4**: High-volatility pairs (DOT, AVAX, SOL, LINK, ATOM, POL) use 2.5%/4.5% SL/TP; normal-volatility pairs (BTC, ETH, XRP, LTC, ADA) use 1.5%/3.0%. Function `get_sl_tp_for_symbol()` in AutoTradingBot fallback.
-   **InstitutionalMetricsCalculator V6.5.4 PREMIUM** (`omnix_services/analytics/institutional_metrics.py`): Sharpe, Sortino, Calmar ratios calculated per-pair and portfolio-wide. Industry-standard risk-adjusted metrics for UAE/GCC investor presentations.
-   **InstitutionalReportGenerator V6.5.4 PREMIUM** (`omnix_services/analytics/institutional_report.py`): PDF report generator with professional formatting for investors. Includes executive summary, risk metrics, per-pair analysis, and calibration details.
-   **Streamlit Dashboard V6.5.4 PREMIUM** (`omnix_dashboard/streamlit_app.py`): Interactive investor dashboard with Plotly charts, real-time metrics visualization, and performance grade display.

### Multi-User Architecture V6.5.4

-   Supports 100,000+ simultaneous users with isolated trading sessions.
-   Utilizes Redis for fast state management and PostgreSQL for persistence.
-   Employs ThreadPoolExecutor for parallel processing and per-user locks for thread safety.

### Dashboard Architecture (V6.5.4 PREMIUM)

-   **Flask Dashboard** (port 5000): Primary API and web terminal for operations
    - `/api/metrics/institutional`: Portfolio-wide and per-pair Sharpe/Sortino/Calmar
    - `/api/report/pdf`: Professional PDF report for investor presentations
    - `/api/system/calibration`: WIN_RATE_OPTIMIZED profile calibration data
    - All standard endpoints for health, trades, market data, signals
-   **Streamlit Dashboard** (port 8080): Interactive investor visualization
    - Consumes Flask API via `OmnixAPIClient` class
    - Dark theme with Plotly charts
    - Performance grade display (A/B/C/D based on Sharpe)
    - Per-pair analysis tables
-   **API Client** (`omnix_dashboard/api_client.py`): Service-to-service communication
    - Configurable base URL via `OMNIX_API_URL` environment variable
    - Defaults to `http://localhost:5000` for local development

### Trading Profiles System

-   Configurable profiles (INSTITUTIONAL, PAPER_AGGRESSIVE, BALANCED, PAPER_OPTIMIZED, WIN_RATE_OPTIMIZED) to switch between conservative and aggressive settings for trading parameters like Coherence Engine veto, Ramp-Up System, Score Thresholds, HMM VETO, and Regime Change VETO.
-   **WIN_RATE_OPTIMIZED V2 PREMIUM (Dec 8, 2025)**: Institutional-grade profile with per-pair calibration. Trades BTC/USD, XRP/USD, ADA/USD, LINK/USD. Uses `PairCalibration` system with tiers (PROVEN/CALIBRATING/EXCLUDED). Differentiated SL/TP per symbol: BTC/XRP (1.2%/3.5%), ADA (0.9%/2.0%), LINK (1.0%/2.5%). Max position sizing: BTC $50K, XRP $40K, LINK $30K, ADA $25K. Portfolio weights: BTC 40%, XRP 30%, ADA 15%, LINK 15%. **Circuit Breaker por par**: BTC/XRP max 2% drawdown diario, ADA/LINK max 1%. Check interval 15s. Set `TRADING_PROFILE=WIN_RATE_OPTIMIZED` in Railway to activate.

### Migration Tools (V6.5.4 Premium)

-   **Migration Watchdog** (`scripts/migration_watchdog.py`): Closes orphan positions in excluded symbols before profile switch. Modes: `analyze`, `execute`, `force`.
-   **Migration Test Suite** (`scripts/test_migration.py`): Automated verification of profile config, symbol filters, and no orphan positions.
-   **Symbol Filter**: Blocks trades in non-allowed symbols. Logs JSON events for audit trail.
-   **Premium Observability**: Structured JSON logs for SL/TP triggers with Prometheus metrics.

### Architecture Modernization V7.0 (Planned)

-   Planned refactoring to Hexagonal Architecture with Ports & Adapters, SOLID Principles, and Dependency Injection using `dependency-injector` for a more modular and maintainable codebase.

## External Dependencies

### APIs and Services

-   **Kraken Exchange**: Primary crypto data and order execution.
-   **Alpaca**: Stock data and historical bars.
-   **Google Gemini (2.0 Flash)**: Primary AI model.
-   **OpenAI (GPT-4o, Whisper)**: AI services and transcription.
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

## Recent Changes (December 8, 2025)

### Panel Premium V6.5.4 Updates

-   **InstitutionalMetricsCalculator** (`omnix_services/analytics/institutional_metrics.py`): Sharpe, Sortino, Calmar ratios calculated per-pair and portfolio-wide using daily equity curves. Industry-standard risk-adjusted metrics for UAE/GCC investor presentations.
-   **Monte Carlo Real Simulation**: 10,000 numpy iterations per horizon (30/90/180 days) for PDF reports - genuine stochastic simulation, not static calculations.
-   **PDF Report Generator** (`omnix_services/analytics/institutional_report.py`): 989-line institutional PDF with 6 sections: cover, benchmarks, Monte Carlo projections, team/governance, roadmap 2026, architecture.
-   **Centralized Finnhub Service**: `/api/news` now uses centralized `finnhub_service` pattern - eliminates 422/429 API errors and provides consistent key handling.
-   **OmnixAPIClient Separation**: Complete service isolation enforced - Streamlit consumes Flask API exclusively via `OmnixAPIClient`, no direct backend imports.
-   **Streamlit Sidebar**: Replaced placeholder image with styled gradient text "OMNIX V6.5.4".
-   **Type Safety**: Fixed Optional type annotations in `api_client.py` and `institutional_report.py` - 0 LSP errors.

### System Audit Status

| Component | Status |
|-----------|--------|
| Flask Dashboard (5000) | 12/12 widgets OK |
| PostgreSQL | 42 tables, 27 real trades |
| PDF Generation | 13.6 KB output verified |
| API Endpoints | All 200 OK |
| Browser Console | No errors (Tailwind CDN warning only) |