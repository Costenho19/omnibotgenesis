# OMNIX V6.5.2 INSTITUTIONAL+ - Technical Reference

**Document Version:** 1.0  
**Created:** December 4, 2025  
**Last Updated:** December 4, 2025  
**Status:** 🟡 IN PROGRESS (Auditoría Técnica Fase 1)

---

## 1. Executive Summary

### 1.1 System Overview

OMNIX V6.5.2 INSTITUTIONAL+ is an enterprise-grade automated cryptocurrency and stock trading system designed for:

| Capability | Description |
|------------|-------------|
| **Multi-Market Trading** | Kraken (crypto) + Alpaca (stocks) |
| **User Capacity** | 100,000+ simultaneous users |
| **AI Integration** | Gemini 2.0 Flash, GPT-4o, Claude |
| **Security** | Post-Quantum Cryptography (NIST 2024) |
| **Trading Modes** | Paper Trading ($1M virtual) + Real Trading |
| **Target** | $400K seed funding at $2.5M valuation |

### 1.2 Codebase Statistics

| Metric | Count |
|--------|-------|
| Total Python Packages | 10 |
| Total Python Modules | ~180+ |
| Lines of Code | ~85,000+ |
| Database Tables | 45 |
| Foreign Key Constraints | 41 (91% coverage) |
| Dashboard Endpoints | 25+ |

---

## 2. Package Architecture

### 2.1 Package Inventory

```
omnix/
├── omnix_core/          # Core trading logic (15 modules)
├── omnix_services/      # Service layer (80+ modules in 22 subpackages)
├── omnix_dashboard/     # Flask web dashboard (40+ files)
├── omnix_api/           # REST API & payments (3 modules)
├── omnix_config/        # Configuration management (3 modules)
├── omnix_reports/       # Report generation (1 module)
├── omnix_risk/          # Risk management extensions (6 modules)
├── omnix_strategies/    # Strategy extensions (1 module)
├── omnix_testing/       # Backtesting & validation (15+ modules)
├── scripts/             # Utility scripts (2 files)
├── tests/               # Unit tests (1 file)
└── sql/                 # SQL scripts (2 files)
```

---

## 3. omnix_core/ - Core Trading System

**Purpose:** Central trading engine, strategies, security, caching, and user sessions.  
**Total Modules:** 15+ across 10 subpackages  
**Lines of Code:** ~15,000

### 3.1 Subpackage Inventory

| Subpackage | Files | Primary Purpose | Key Classes |
|------------|-------|-----------------|-------------|
| `bot/` | 2 | Trading automation | `AutoTradingBot`, `PaperTradingManager` |
| `strategies/` | 3 | ARES trading protocols | `AresProtocolV1`, `AresProtocolV2`, `NonMarkovianKernel` |
| `security/` | 2 | Post-Quantum Cryptography | `PostQuantumSecurity` |
| `quantum/` | 4 | QRNG, D-Wave, Physics | `QuantumRandomNumberGenerator`, `DWavePortfolioOptimizer` |
| `cache/` | 2 | Redis caching | `RedisCache`, `RedisStateManager` |
| `sessions/` | 1 | Multi-user sessions | `UserSessionManager`, `UserTradingSession` |
| `context/` | 1 | Real data provider | `OMNIXRealContextProvider` |
| `utils/` | 2 | Logging, rate limiting | `ColoredFormatter`, `RateLimiter` |
| `models/` | 0 | (Empty - placeholder) | - |
| `queue/` | 0 | (Empty - placeholder) | - |
| Root | 1 | Trading system core | `TradingSystem` |

### 3.2 Module Details

#### 3.2.1 omnix_core/trading_system.py (5,487 lines)

**Purpose:** Core trading engine with Kraken integration and advanced modules.

**Key Classes:**
- `TradingSystem`: Main trading engine

**Key Features:**
- Multi-currency trading system with auto-switch
- Post-quantum security integration (Kyber-768, Dilithium-3)
- ARES strategies integration (V1 Swing, V2 Scalping)
- Advanced modules: OrderBook, Volatility, Microstructure, Risk

**Dependencies (Internal):**
```python
from omnix_services.trading_service.analyzers import (
    AdvancedOrderBookAnalyzer, AdvancedVolatilityAnalyzer,
    MicrostructureAnalyzer, AdvancedRiskManagement
)
from omnix_services.trading_service import PostQuantumSecurity
from omnix_services.optimization import MathematicalOptimizer
from omnix_core.strategies.ares_v1 import AresProtocolV1
from omnix_core.strategies.ares_v2 import AresProtocolV2
```

**Dependencies (External):**
- `ccxt` - Crypto exchange connectivity (Kraken)

**⚠️ Issues Detected:**
- 94 LSP diagnostics (mostly type hints and undefined imports)
- Multi-currency system temporarily disabled (line 99)

---

#### 3.2.2 omnix_core/bot/auto_trading_bot.py (3,270 lines)

**Purpose:** 24/7 automated trading bot with 10 institutional strategies.

**Key Class:** `AutoTradingBot`

**10 Trading Strategies:**
1. Monte Carlo - Probability validation (10,000 simulations)
2. Black Swan - Extreme condition detection (Kurtosis/Skewness)
3. Sentiment Analysis - Market timing
4. Kelly Criterion - Mathematical position sizing
5. HMM Regime Detection - Market regime classification
6. Kalman Filter - Adaptive signal filtering
7. Quantum Momentum - 6-component proprietary strategy
8. ARES V1 - Swing Trading (55-65% win rate)
9. ARES V2 - Scalping M1 (60-70% win rate)
10. Non-Markovian Kernel - Temporal memory K(t-s)

**Dependencies (Internal):**
```python
from omnix_services.monitoring import get_metrics_engine, AIRiskGuardian
from omnix_services.optimization import AdaptiveWeightSystem, AutoLearningSystem
from omnix_services.ai_service import get_conversational_brain
from omnix_services.ai_service.video import VideoLearningAnalyzer
from omnix_services.coherence_service import CoherenceEngine
from omnix_services.risk_management import (
    MemoryRiskAdapter, LimitsEngine, CircuitBreaker, 
    PositionMonitor, AlertDispatcher
)
from omnix_services.adaptive_engine import AdaptiveParameterEngine
from omnix_core.sessions import UserSessionManager
from omnix_core.strategies.non_markovian_kernel import NonMarkovianKernel
```

**⚠️ Issues Detected:**
- 122 LSP diagnostics
- Multiple conditional imports with fallbacks

---

#### 3.2.3 omnix_core/bot/paper_trading.py (657 lines)

**Purpose:** Simulated trading with real Kraken data.

**Key Class:** `PaperTradingManager`

**Key Features:**
- Initial balance: $1,000,000 USD virtual
- Real Kraken prices for simulation
- Kraken fees: 26 basis points (0.26%)
- Full P&L tracking

**Dependencies (Internal):**
- `database_service` for persistence
- `trading_service` for market data

---

#### 3.2.4 omnix_core/strategies/ares_v1.py (680 lines)

**Purpose:** ARES Protocol V1 - Institutional Swing Trading

**Key Class:** `AresProtocolV1`

**Architecture (3 Layers):**
1. **ANF (Adaptive Noise Filter):** Filters 90% of low-value trades
2. **ISA (Institutional Signal Analysis):** 6 professional signals
3. **SXE (Smart Execution Engine):** Hedge fund-style execution

**Win Rate Target:** 55%-65% (backtested)

**Position Sizing:**
- Normal (4/6 signals): 2.7%
- Strong (5/6 signals): 6.2%
- ARES (6/6 signals): 11.5%

**Risk Parameters:**
- Take Profit Long: [1.25%, 3.40%, 5.80%]
- Stop Loss Long: -0.95%

---

#### 3.2.5 omnix_core/strategies/ares_v2.py (588 lines)

**Purpose:** ARES Protocol V2 - Scalping M1 (1-minute)

**Key Class:** `AresProtocolV2`

**Win Rate Target:** 60%-70% (backtested)

**Risk Parameters:**
- Stop Loss: -0.28% (ultra-tight for M1)
- Take Profit: [0.85%, 1.70%, 2.90%]
- TP Portions: [50%, 30%, 20%]

**Kill-Switch Conditions:**
- 3 consecutive losses → 15 min cooldown
- Model divergence > 0.70
- Volatility > 80%

---

#### 3.2.6 omnix_core/strategies/non_markovian_kernel.py (631 lines)

**Purpose:** Quantum-inspired temporal memory for regime detection.

**Key Class:** `NonMarkovianKernel`

**Kernel Equation:**
```
K(t-s) = exp(-|t-s|/τ) × [1 + ε × cos(Ω(t-s))]
```

**Parameters:**
- τ (tau) = 12 hours - Memory decay constant
- ε (epsilon) = 0.35 - Oscillation amplitude
- Ω (omega) = 0.523 rad - Oscillation frequency
- Window = 168 periods (1 week hourly)

**Applications:**
- Enhanced regime detection
- Cyclical pattern recognition
- Long-range correlation analysis
- On-chain signal integration (15% weight)

---

#### 3.2.7 omnix_core/security/pqc_security.py (469 lines)

**Purpose:** Post-Quantum Cryptography using NIST 2024 standards.

**Key Class:** `PostQuantumSecurity`

**Algorithms:**
- **ML-KEM-768 (Kyber-768):** Key encapsulation
- **ML-DSA-65 (Dilithium-3):** Digital signatures

**Standards:** NIST FIPS 203 + FIPS 204

**Dependencies (External):**
- `pypqc` library for real PQC operations

**Key Methods:**
- `generate_keypair_encryption()` - Kyber key generation
- `encapsulate_secret()` - Key encapsulation
- `sign_trading_order()` - Order signing with Dilithium

---

#### 3.2.8 omnix_core/security/pqc_encryption.py (200 lines)

**Purpose:** Simulated PQC operations (fallback when pypqc unavailable)

**Functions:**
- `cifrar_con_dilithium()` - Simulated Dilithium signing
- `verificar_firma_dilithium()` - Simulated verification
- `generar_claves_kyber()` - Simulated Kyber key generation
- `intercambio_claves_kyber()` - Simulated key exchange
- `encrypt_aes_quantum()` - AES with "quantum" key

**⚠️ Note:** This is a SIMULATION for when real PQC is unavailable.

---

#### 3.2.9 omnix_core/quantum/enhancements.py (588 lines)

**Purpose:** Quantum enhancements with ANU QRNG and D-Wave.

**Key Classes:**
- `QuantumRandomNumberGenerator` - Real quantum random numbers from ANU
- `QuantumPortfolioOptimizer` - Portfolio optimization

**ANU QRNG API:**
- Endpoint: `https://qrng.anu.edu.au/API/jsonI.php`
- Batch size: 1024 numbers per request
- Cache TTL: 1 hour
- Error cooldown: 5 minutes

**Fallback:** numpy.random when API unavailable

---

#### 3.2.10 omnix_core/quantum/physics_validator.py (4,460 lines)

**Purpose:** PhD-level quantum optics and QRNG physics validator.

**Key Class:** `QuantumPhysicsValidator`

**Verified Formulas (24 total):**
- Homodyne variance: σ² = (hν/4) × Δf
- Shot noise limit: P_shot = 2eI × Δf
- Vacuum fluctuations: ΔE × Δt ≥ ℏ/2
- Wigner Function
- Quantum Fisher Information
- Bell/CHSH inequality
- Von Neumann entropy
- ...and more

**Purpose:** Prevents AI hallucination of incorrect physics

---

#### 3.2.11 omnix_core/quantum/testing_framework.py (853 lines)

**Purpose:** Quantum physics testing for AI response validation.

**Key Class:** `QuantumTestingFramework`

**Features:**
- 24 test cases (one per verified formula)
- Tests mathematical CORRECTNESS, not just symbol presence
- Automated daily testing for investor confidence

---

#### 3.2.12 omnix_core/quantum/dwave_qaoa.py (351 lines)

**Purpose:** D-Wave Leap quantum annealing integration.

**Key Class:** `DWavePortfolioOptimizer`

**Features:**
- Real quantum computing via D-Wave Leap
- Hybrid CQM Solver for complex constraints
- Direct QPU access available

**Requirements:**
- D-Wave Leap account
- `DWAVE_API_TOKEN` environment variable
- `dwave-ocean-sdk` package

---

#### 3.2.13 omnix_core/cache/redis_cache.py (187 lines)

**Purpose:** Enterprise Redis cache management.

**Key Class:** `RedisCache`

**Performance:**
- 10x faster responses
- 50K+ concurrent users capacity

**Features:**
- URL-based connection (Railway)
- Host/port fallback
- Automatic connection testing
- TTL-based caching

---

#### 3.2.14 omnix_core/cache/redis_state.py (349 lines)

**Purpose:** Stateless architecture for horizontal scaling.

**Key Classes:**
- `RedisStateManager` - Base state management
- `RedisConversationHistory` - Chat history (10 messages, 24h TTL)
- `RedisUserPreferences` - User settings
- `RedisTradingState` - Trading session state

---

#### 3.2.15 omnix_core/sessions/user_session_manager.py (562 lines)

**Purpose:** Multi-user session management for 100K+ users.

**Key Classes:**
- `UserSessionManager` - Session orchestration
- `UserTradingSession` - Individual session state
- `SessionStatus` - Enum (INACTIVE, ACTIVE, PAUSED, EMERGENCY_STOP)

**Session State:**
- Trading status (running, paused, emergency_stop)
- Balance and positions
- Trade statistics (wins, losses, P&L)
- Risk parameters

**Storage:** Redis (horizontal scaling) + PostgreSQL (persistence)

---

#### 3.2.16 omnix_core/context/real_data_provider.py (314 lines)

**Purpose:** Centralized real data injection for AI responses.

**Key Class:** `OMNIXRealContextProvider`

**Data Sources:**
- Auto-trading status
- Paper trading balance
- Market data (Kraken prices)
- Open positions
- Recent trades

**Cache:** 30-second TTL to avoid excessive API calls

---

#### 3.2.17 omnix_core/utils/logger.py (141 lines)

**Purpose:** Centralized enterprise logging.

**Key Classes:**
- `ColoredFormatter` - Console output (development)
- `StructuredFormatter` - JSON-like output (production)

**Features:**
- Rotating file handlers
- Structured logging with user_id, request_id
- Exception tracking

---

#### 3.2.18 omnix_core/utils/rate_limiter.py (221 lines)

**Purpose:** API abuse prevention with Token Bucket algorithm.

**Key Class:** `RateLimiter`

**Features:**
- Redis-backed distributed limiting
- Configurable requests/window
- Graceful fallback (fail open) when Redis unavailable

---

### 3.3 Empty Modules (Placeholders)

| Module | Status | Notes |
|--------|--------|-------|
| `omnix_core/models/__init__.py` | Empty | Placeholder for data models |
| `omnix_core/queue/__init__.py` | Empty | Placeholder for job queue |
| `omnix_core/strategies/__init__.py` | Empty | Missing exports |
| `omnix_core/security/__init__.py` | Empty | Missing exports |

---

## 4. omnix_services/ - Service Layer

**Status:** 🟡 Pending detailed analysis

**Total Subpackages:** 22  
**Estimated Modules:** 80+

### 4.1 Subpackage Inventory (Preliminary)

| Subpackage | Primary Purpose |
|------------|-----------------|
| `adaptive_engine/` | Auto-calibration for ARES strategies |
| `ai_service/` | Gemini, GPT-4o, Claude integration |
| `alerts/` | Smart alert system |
| `analytics/` | Chart patterns, Fibonacci, Volume |
| `coherence_service/` | 6-Tier Veto System |
| `community_intelligence/` | Signal contributions, rewards |
| `concurrency/` | Resource and cache management |
| `database_service/` | DatabaseGateway, DatabaseManager |
| `derivatives/` | Futures, margin, hedging |
| `market_data/` | Kraken data, sentiment, news |
| `market_intelligence/` | Alpha Vantage, Fear & Greed, Finnhub |
| `monitoring/` | Metrics, Risk Guardian, Performance |
| `notifications/` | Telegram, daily summaries |
| `on_chain_service/` | Whale tracking, exchange flows |
| `optimization/` | Auto-learner, ML modules |
| `portfolio_management/` | Institutional portfolio engines |
| `risk_management/` | Circuit breaker, limits, alerts |
| `stock_trading/` | Alpaca integration, stock analysis |
| `telegram_service/` | Bot commands, callbacks |
| `trading_service/` | Kraken client, paper trading |
| `user_settings/` | User preferences |
| `voice_service/` | Voice commands |

---

## 5. omnix_dashboard/ - Web Dashboard

**Status:** 🟡 Pending detailed analysis

**Structure:**
- 6 Flask Blueprints
- 11 JavaScript components
- 25+ API endpoints

---

## 6. Database Integration

**Status:** ✅ Audited (See DATABASE_AUDIT_REPORT.md)

| Metric | Value |
|--------|-------|
| Total Tables | 45 |
| Foreign Keys | 41 (91% coverage) |
| Phase 3 | Complete (Dec 4, 2025) |

---

## 7. Legacy and Obsolete Code

**Status:** 🟡 Pending analysis

### 7.1 Preliminary Findings

| Location | Type | Description |
|----------|------|-------------|
| `omnix_core/security/pqc_encryption.py` | Potential Legacy | Simulated PQC when `pqc_security.py` provides real implementation |
| `omnix_core/models/__init__.py` | Empty | Placeholder never implemented |
| `omnix_core/queue/__init__.py` | Empty | Placeholder never implemented |

---

## 8. Dependency Matrix

### 8.1 External Dependencies (Key)

| Package | Purpose | Used By |
|---------|---------|---------|
| `ccxt` | Crypto exchange API | TradingSystem, KrakenClient |
| `redis` | Caching, state | RedisCache, UserSessionManager |
| `psycopg` | PostgreSQL v3 | DatabaseGateway, DatabaseManager |
| `pypqc` | Post-quantum crypto | PostQuantumSecurity |
| `numpy` | Numerical computing | All strategies, quantum |
| `scipy` | Scientific computing | ARES protocols |
| `flask` | Web framework | Dashboard |
| `google-generativeai` | Gemini AI | AI Service |
| `openai` | GPT-4o | AI Service |
| `anthropic` | Claude | AI Service |
| `python-telegram-bot` | Telegram | TelegramService |

---

## 9. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Dec 4, 2025 | Agent | Initial omnix_core/ inventory complete |

---

**Next Steps:**
1. Complete omnix_services/ detailed analysis
2. Complete omnix_dashboard/ analysis
3. Database-to-code mapping
4. Legacy code identification
5. Final document compilation
