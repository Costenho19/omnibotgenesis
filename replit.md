# OMNIX V6.5.4 INSTITUTIONAL+ - Automated Trading System

## Overview

OMNIX V6.5.4 INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system designed for 24/7 operation with multi-user support. Its primary purpose is paper trading to build a credible track record for investor presentations, targeting $400K seed funding at $2.5M valuation. Key capabilities include AI integration, post-quantum cryptography, real-time market analysis, Non-Markovian Temporal Memory with On-Chain Data Intelligence, adaptive parameter calibration, institutional portfolio optimization, derivatives trading, and dual-market support for Kraken (crypto) and Alpaca (stocks). The system aims for 20-50 trades/day with a 55%+ win rate, multi-crypto scanning, and tiered signal strengths.

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
-   **Volatility-Based SL/TP Classification V6.5.4**: High-volatility pairs (DOT, AVAX, SOL, LINK, ATOM, POL) use 2.5%/3.5% SL/TP; normal-volatility pairs (BTC, ETH, XRP, LTC, ADA) use 1.5%/2.5%. Function `get_sl_tp_for_symbol()` in AutoTradingBot fallback.

### Multi-User Architecture V6.5.4

-   Supports 100,000+ simultaneous users with isolated trading sessions.
-   Utilizes Redis for fast state management and PostgreSQL for persistence.
-   Employs ThreadPoolExecutor for parallel processing and per-user locks for thread safety.

### Dashboard API Endpoints

-   Provides various API endpoints for system health, trading performance, paper trade history, open positions, real-time prices, market sentiment, database diagnostics, and adaptive engine telemetry.

### Trading Profiles System

-   Configurable profiles (INSTITUTIONAL, PAPER_AGGRESSIVE, BALANCED) to switch between conservative and aggressive settings for trading parameters like Coherence Engine veto, Ramp-Up System, Score Thresholds, HMM VETO, and Regime Change VETO.

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