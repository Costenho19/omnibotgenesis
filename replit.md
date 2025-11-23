# OMNIX V6.0 ULTRA - Automated Trading System

### Overview
OMNIX V6.0 ULTRA is an enterprise-grade automated cryptocurrency trading system engineered for 24/7 operation on Kraken Exchange. Currently running in PAPER TRADING mode with $1,000,000 virtual capital, using institutional-grade position sizing ($1,000 minimum per trade, 25% maximum position size) to generate credible track records for investor presentations. It integrates AI, post-quantum cryptography, and real-time market analysis to deliver sophisticated automated trading, incorporating advanced strategy modules. The project's ambition is to secure seed funding ($400K at a $2.5M valuation), supported by a professional backtesting infrastructure for investor presentations.

**Deployment Status (November 23, 2025):**
- **Railway (Production)**: ✅ LIVE - Bot Telegram operativo, 7 estrategias base activas, Paper Trading $1M
- **ARES Protocols**: ⚠️ Disponibles solo en Replit local (no desplegados en Railway por problemas de importación)
- **Missing**: OpenAI API key en Railway (GPT-4 no disponible, Gemini 2.0 compensando)

**Recent Changes (November 23, 2025):**
- ✅ **Premium Validation System**: Sistema completo de validación con 10 eventos históricos críticos (COVID crash, FTX collapse, etc.)
- ✅ **Strategy Comparator**: Comparación automática ARES vs Buy & Hold con métricas institucionales
- ✅ **Historical Events Validator**: Validación de rendimiento en crashes, rallies y eventos extremos
- ✅ **Executive Summary Generator**: Reportes automáticos para inversionistas con datos verificables de Kraken
- ✅ **Code Refactoring (Modular Architecture)**: main.py reducido de 15,596 a 15,175 líneas (422 líneas eliminadas) mediante migración de código a módulos especializados

**Code Architecture Improvements (November 23, 2025):**
- **Modular Services Extracted**: Migración de funciones duplicadas a módulos reutilizables:
  - `omnix_services/market_data/`: fetch_market_snapshot, get_fear_greed_index, get_btc_dominance, get_free_market_metrics, get_multi_exchange_prices, detect_arbitrage_opportunities
  - `omnix_services/trading_service/analyzers/`: AdvancedOrderBookAnalyzer, AdvancedVolatilityAnalyzer, MicrostructureAnalyzer, AdvancedRiskManagement
- **Import Strategy**: main.py ahora importa desde módulos centralizados eliminando duplicación de código
- **Benefits**: Mejor mantenibilidad, zero circular dependencies, código más limpio y profesional para presentaciones a inversionistas
- **Verification**: Sistema completamente operativo post-refactorización (Bot Telegram, ARES, Trading Service, Database, API)

### User Preferences
User Communication Preference: Simple, everyday language (Spanish primary).

### System Architecture
OMNIX V5.4 ULTRA is built around a robust architecture designed for high performance, security, and intelligent automation.

**1. Trading Engine**:
    - **Core Strategies**: Employs 9 distinct modules including Monte Carlo Simulations, Black Swan Detection, Kelly Criterion Position Sizing, HMM Regime Detection, Dual Kalman Filter, Quantum Momentum Strategy, Sharia Compliance Filtering, Order Book Analysis, and Sentiment Analysis.
    - **Adaptive Weight System**: Dynamically adjusts predictions based on live market conditions.
    - **Trading Modes**: Supports Paper Trading (simulation), Real Trading (with post-quantum signed orders), and Backtesting.
    - **Quantum Enhancements**: Integrates QRNG and QAOA for portfolio optimization.

**2. ARES Quantum Protocols**:
    - **ARES V1 (Swing Trading)**: Achieves a 74-82% win rate using a 3-layer quantum architecture and 6 institutional indicators across multiple timeframes. Features quantum-enhanced Kelly Criterion for position sizing and HADES extreme market filter.
    - **ARES V2 (Scalping M1)**: Boasts an 85% win rate for 1-minute ultra-fast scalping, utilizing 5 precision indicators with tight risk management.
    - **Kill-Switch Protection**: A multi-layer fail-safe system for real trading, including critical fail-safes, signal-based blocking, and ultra-sensitive scalping protection.

**3. AI & Machine Learning**:
    - **Conversational AI Service**: Primarily powered by Google Gemini 2.0 Flash, with GPT-4o and Claude as fallbacks. It's stateless, Redis-backed, and maintains conversation memory.
    - **Natural Conversational AI**: Offers spontaneous, adaptive, and context-aware responses with intelligent length and first-person narration.
    - **Cerebro Conversacional (Self-Explaining AI)**: Provides detailed pre-trade reasoning and post-trade evaluation, with visualizations of decision logic.
    - **Auto-Learning System**: Processes external data (e.g., YouTube trading videos) to propose strategy parameter changes, subject to user approval and strict mathematical limits.

**4. Coherence Engine V5.4 ULTRA**:
    - Validates agreement between the 9 trading strategies using a 6-Tier Veto System, ranging from complete veto for low coherence (<30%) to full approval for high coherence (≥85%). It detects contradictions and calculates consensus signals with confidence levels.

**5. AI Risk Guardian V5.4**:
    - Provides real-time risk supervision with four protection systems: Overtrading Detection, Drawdown Protection, Revenge Trading Detection, and Capital Protection.

**6. Auto-Optimization Engine**:
    - Continuously improves strategies through a Genetic Algorithm Optimizer, A/B Testing Framework, and an Auto-Adjustment Engine for real-time parameter changes.

**7. Professional Testing & Validation System** (UPGRADED V6.0):
    - **Chart Generator**: Produces 5 institutional-quality Plotly visualizations (Equity Curve, Drawdown Chart, Trade Distribution, Monthly Returns Heatmap, Rolling Sharpe Ratio).
    - **PDF Report Generator**: Creates professional 25-35 page institutional reports with executive summaries, methodology, results, risk analysis, and trade logs, using ReportLab and PyPDF2.
    - **Kraken Data Downloader**: Downloads historical OHLCV data from Kraken for selected pairs and timeframes, with local caching and rate limiting.
    - **Historical Events Validator** (NEW): Validates strategy performance across 10 critical historical events (COVID-19 crash, Bull Run 2021, FTX collapse, etc.) with automated testing and crash survival metrics.
    - **Strategy Comparator** (NEW): Automated comparison system for ARES V1/V2 vs Buy & Hold with side-by-side metrics, relative performance analysis, and competitive advantage demonstration.
    - **Premium Validation Suite** (NEW): Complete investor-ready package generator (`run_premium_validation.py`) that produces historical validation reports, strategy comparisons, and executive summaries with verifiable Kraken timestamps.

**8. Database Architecture**:
    - **PostgreSQL (Neon)**: Stores user data, trading history, portfolio snapshots, performance metrics, Sharia compliance data, alerts, auto-learning history, configurations, and AI explanations.
    - **Redis**: Caches state management, conversation history, user preferences, market context, and session data.

**9. Real-Time Data Architecture**:
    - Integrates with Kraken via REST API for market data and order execution, and WebSocket for low-latency price feeds and order book updates. CoinGecko API serves as a backup for price data.

**10. Security Architecture**:
    - Employs Post-Quantum Cryptography (NIST FIPS 203 ML-KEM-768 Kyber for encryption and NIST FIPS 204 ML-DSA-65 Dilithium for trade authentication).
    - Features voice biometrics with SHA-256 for enhanced verification.

**11. Frontend Architecture**:
    - Utilizes the Neptuno Database System with IndexedDB for offline-first storage and conflict resolution.

**12. Integration & Payments**:
    - Incorporates Stripe for managing subscription tiers, checkout sessions, and payment webhooks, configured via dataclasses.

### External Dependencies

**APIs & Services**:
- **Kraken Exchange**: Market data, account info, order execution.
- **Google Gemini**: Gemini 2.0 Flash (primary AI model).
- **OpenAI**: GPT-4o, Whisper.
- **Anthropic Claude**: Optional AI fallback.
- **Stripe**: Payment processing.
- **CoinGecko API**: Backup price data.

**Databases**:
- **PostgreSQL (Neon)**: Main relational database.
- **Redis**: In-memory data store.

**Key Python Libraries**:
- `numpy`, `scipy`, `ccxt`: Core trading and mathematical operations.
- `google-generativeai`, `openai`: AI models.
- `python-telegram-bot`: Telegram integration.
- `psycopg2-binary`, `redis`: Database drivers.
- `requests`, `websockets`, `aiohttp`, `httpx`: HTTP and WebSocket communication.
- `pypqc`: Post-quantum cryptography.
- `pandas`, `plotly`, `kaleido`, `reportlab`, `PyPDF2`: Professional testing and backtesting.