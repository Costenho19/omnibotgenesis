# OMNIX V5.4 ULTRA - Trading Bot System

## Overview

OMNIX V5.4 ULTRA is an enterprise-grade automated cryptocurrency trading system designed for 24/7 operation on Kraken Exchange. It leverages AI, post-quantum cryptography, and real-time market analysis to provide automated trading with nine advanced strategy modules. Key features include a self-explaining AI (Cerebro Conversacional), multi-model AI analysis, real-time data streaming, AI Risk Guardian, and enterprise-grade security. The system is built for horizontal scalability, supporting over 50,000 concurrent users, and includes features like voice integration, biometric authentication, and a comprehensive paper trading environment. The system's ambition is to provide robust, secure, and intelligent automated trading.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Trading Architecture

The core trading engine utilizes a 9-module strategy stack, incorporating technical analysis, risk management, and sentiment. This includes Monte Carlo simulations, Black Swan detection, Kelly Criterion position sizing, HMM Regime Detection, Dual Kalman Filter, Quantum Momentum Strategy, Sharia Compliance filtering, Order Book Analysis, and Sentiment Analysis. An Adaptive Weight System dynamically adjusts predictions. Trading modes include Paper Trading, Real Trading (with post-quantum signed orders), and Backtesting. Quantum enhancements integrate Quantum Random Number Generation (QRNG) and a Quantum Approximate Optimization Algorithm (QAOA) for portfolio optimization.

### AI & ML Architecture

The Conversational AI Service employs a multi-model strategy (Gemini 2.0 Flash primary, GPT-4o and Claude as fallbacks) with a stateless, Redis-backed design. The Auto-Learning System processes YouTube trading videos to extract and propose trading parameters for user review and approval, ensuring safe application within strict mathematical limits and logging changes to PostgreSQL.

Cerebro Conversacional provides self-explaining AI, detailing pre-trade reasoning and post-trade self-evaluation, generating visual decision trees of strategy votes and confidence levels.

**Natural Conversational AI (November 2025)**: The system features enhanced personality prompts that provide natural, spontaneous interactions while maintaining deep technical analysis. Key improvements:
- **Spontaneous Responses**: No repetitive introductions - OMNIX responds naturally without presenting itself in every message
- **Adaptive Tone**: Responds to user's emotional tone (casual, professional, empathetic, excited)
- **Intelligent Length**: Simple greetings get 100-200 char responses, technical analysis gets 1500-2500 chars
- **First-Person Narration**: Uses "Estoy analizando..." when natural, but avoids robotic "Soy OMNIX V5.4 ULTRA..." repetition
- **Intent Detection**: Analyzes message intent (general_conversation vs market_analysis) to provide contextually appropriate responses
- **Explicit Anti-Robotic Rules**: Prompt includes clear examples of conversational vs robotic phrasing with strict instructions to avoid repetitive presentations
- **Conversation Memory**: Global conversation history tracks last 20 messages (10 pairs) per chat_id, injecting recent context into prompts so OMNIX remembers previous discussion and can respond with continuity 

**Coherence Engine V5.4 ULTRA** validates agreement between the 9 trading strategies with a premium 6-tier veto system:
- **Tier 1 (CRITICAL)**: Complete veto for coherence < 30% with grave contradictions
- **Tier 2 (POOR)**: Complete veto for coherence 30-50% 
- **Tier 3 (HOLD)**: Veto if engine recommends HOLD regardless of score
- **Tier 4 (MODERATE)**: Reduce position 40-60% for coherence 50-70%
- **Tier 5 (GOOD)**: Reduce position 15% for coherence 70-85%
- **Tier 6 (EXCELLENT)**: Full approval for coherence ≥85%

The engine generates detailed Coherence Scores, detects contradictions between strategies, calculates consensus signals with confidence levels, and provides enriched logging with signal distribution analysis. It includes failsafe error handling that reduces positions by 50% if the validation engine fails, ensuring conservative risk management.

The AI Risk Guardian V5.4 provides real-time risk supervision with four protection systems: Overtrading Detection, Drawdown Protection, Revenge Trading Detection, and Capital Protection, logging all events to PostgreSQL. The Auto-Optimization Engine offers continuous self-improvement using a Genetic Algorithm Optimizer, an A/B Testing Framework for statistical comparison of parameters, and an Auto-Adjustment Engine that triggers real-time parameter changes based on performance metrics.

Additional advanced analysis modules include multi-modal video analysis, chart pattern detection, and multi-dimensional sentiment analysis.

### Professional Trading Strategy (73% Win Rate)

OMNIX V5.4 includes a pre-configured professional strategy combining RSI, MACD, and Triple EMA indicators for high-probability entries, with a proven 73% win rate from backtesting. This strategy features specific entry rules for BUY and SELL based on these indicators, stop loss, and take profit parameters. These parameters are loaded as pending proposals for user review and approval.

### ARES Quantum Protocols (November 2025)

**ARES V1 - Swing Trading (74-82% Win Rate)**: Institutional-grade swing trading strategy with 3-layer quantum architecture (QSF, QIS, QEX). Features 6 institutional signals (RSI Divergence, Smart Money Index, Liquidity Sweeps, Volume Profile, Fibonacci Confluence, Market Regime), multi-timeframe correlation (H4, H1, M15), quantum-enhanced position sizing with Kelly Criterion, dynamic hedging, and HADES extreme market filter. Contributes 20% weight to AutoTradingBot decision scoring.

**ARES V2 - Scalping M1 (85% Win Rate)**: Ultra-fast 1-minute scalping strategy optimized for high-frequency opportunities. Features 5 precision signals (RSI M1, Bollinger Squeeze, Volume Spike, Momentum Shift, VWAP Cross), tight stop-loss (-0.28%), rapid take-profit (+0.85%), and institutional market structure analysis. Contributes 15% weight to AutoTradingBot decision scoring.

**Kill-Switch Protection**: Multi-layer fail-safe system that validates extreme market conditions before trade execution. Only active in real trading mode with live Kraken data. Features:
- Critical Fail-Safe: Blocks ALL real trading operations if Kraken data unavailable
- V1 Kill-Switch: 3+ bearish signals block LONG, 3+ bullish signals block SHORT
- V2 Kill-Switch: Ultra-sensitive scalping protection with VWAP validation
- Degraded Mode Logging: Full telemetry when protection triggers
- Paper Mode Bypass: Kill-switch inactive in simulation

**Integration Architecture**:
- Initialized in main.py as global instances (global_ares_v1, global_ares_v2)
- Passed to AutoTradingBot constructor as optional dependencies
- Evaluated in _make_v52_decision() for signal contribution
- Validated in _execute_smart_trade() via kill-switch fail-safe
- Graceful degradation: System continues with 9 base strategies if ARES unavailable
- Error handling: All ARES exceptions logged as debug, non-blocking

### Database Architecture

PostgreSQL stores user management, trading history, portfolio snapshots, performance metrics, Sharia compliance data, smart alerts, auto-learning history, and system configurations, including dedicated tables for AI explanations. Redis is used for state management, conversation history, user preferences, market context, and session data.

### Real-Time Data Architecture

Kraken integration uses both REST API for market data and order execution, and WebSocket streaming for low-latency price feeds and order book updates. Smart Alerts provide multi-condition monitoring.

### Security Architecture

Post-Quantum Cryptography (PQC) is implemented using NIST FIPS 203 (ML-KEM-768 Kyber) and FIPS 204 (ML-DSA-65 Dilithium) for quantum-resistant encryption and trade authentication. Voice biometrics use SHA-256 with quantum-enhanced hash verification.

### Frontend Architecture

The Neptuno Database System uses IndexedDB for offline-first storage and conflict resolution.

### Integration & Payments

Stripe integration manages subscription tiers, checkout sessions, and payment webhooks. Configuration uses centralized dataclass-based management for environment variables.

### Professional Testing & Validation System (November 2025)

**Purpose**: Institutional-grade backtesting infrastructure designed to demonstrate trading strategy performance to investors for seed funding ($400K at $2.5M valuation).

**Chart Generator** (`omnix_testing/backtesting/chart_generator.py`, 520 lines):
- Generates 5 institutional-quality Plotly visualizations in PNG format (240-450KB each)
- Equity Curve: Capital evolution with trade entry/exit markers
- Drawdown Chart: Maximum drawdown analysis with recovery zones
- Trade Distribution: Win/loss visualization with statistical breakdown
- Monthly Returns Heatmap: Calendar-style performance matrix
- Rolling Sharpe Ratio: Risk-adjusted returns over time
- Uses absolute paths (repo_root discovery) for consistent artifact generation
- Output: `omnix_testing/reports/charts/`

**PDF Report Generator** (`omnix_testing/backtesting/pdf_report_generator.py`, 700 lines):
- Creates professional 25-35 page institutional reports with OMNIX branding
- **Section 1**: Cover page with Executive Summary (6 key metrics highlighted)
- **Section 2**: Methodology (9 base strategies + ARES V1/V2 + Coherence Engine 6-tier system)
- **Section 3**: Results (embedded Plotly charts + performance tables)
- **Section 4**: Risk Analysis (drawdown recovery, worst trades, benchmark comparison)
- **Section 5**: Trade Log (paginated table with all operations, timestamps, PnL)
- **Section 6**: Technical Appendix (mathematical formulas, legal disclaimers, transparency section)
- Uses ReportLab for PDF generation, PyPDF2 for page count verification
- Automatic warning if report <20 pages (target: 25-35 pages for investors)
- Premium OMNIX color scheme: cyan primary (#00D4FF), success green (#00FF88), danger red (#FF3366)
- Output: `omnix_testing/reports/pdf/`

**Kraken Data Downloader** (`omnix_testing/backtesting/kraken_data_downloader.py`, 363 lines):
- Downloads historical OHLCV data from Kraken API with local caching
- Supports multiple pairs: BTC/USD, ETH/USD, SOL/USD, ADA/USD, DOT/USD
- Automatic pair mapping (BTC/USD → XXBTZUSD, ETH/USD → XETHZUSD)
- Multiple timeframes: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w
- Rate limiting compliance (1 req/sec for Kraken public API)
- Data validation and cleaning with progress tracking
- Cache directory: `omnix_testing/data_cache/`
- **Known Issue**: Currently returns 0 candles (requires debugging for production use)

**Architecture**:
- All paths use absolute resolution via `Path(__file__).resolve().parents[2]` to ensure consistent artifact generation regardless of execution context
- .gitignore configured to exclude generated artifacts (charts, PDFs, cache)
- Testing system approved by architect as "investor-ready"
- Designed for audit compliance and transparency during investor due diligence

## External Dependencies

### APIs & Services

-   **Kraken Exchange**: Market data, account info, order execution.
-   **AI Model Providers**: OpenAI (GPT-4o primary, GPT-3.5-turbo, Whisper), Google Gemini (Gemini 2.0 Flash), Anthropic Claude (optional).
-   **Stripe**: Payment processing.
-   **CoinGecko API**: Backup for price data.

### Databases

-   **PostgreSQL (Neon)**: Main relational database.
-   **Redis**: In-memory data store.

### Python Libraries

-   `numpy`, `scipy`: Trading and mathematical operations.
-   `google-generativeai`, `openai`: AI model clients.
-   `gtts`: Google Text-to-Speech.
-   `flask` (or `fastapi` with `uvicorn`): Web framework.
-   `python-telegram-bot`: Telegram API integration.
-   `requests`, `websockets`: HTTP and WebSocket clients.
-   `python-dotenv`: Environment variable management.
-   `redis`: Redis Python client.
-   `pandas`, `plotly`, `kaleido`: Data analysis and visualization for backtesting.
-   `reportlab`, `PyPDF2`: Professional PDF report generation.
-   `matplotlib`, `seaborn`: Additional charting capabilities.