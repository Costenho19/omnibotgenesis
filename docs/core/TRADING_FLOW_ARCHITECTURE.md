# OMNIX V6.5.4 - Trading Flow Architecture

**Document Version:** 2.0  
**Created:** December 6, 2025  
**Updated:** December 6, 2025 - V6.5.4 Institutional Fixes  
**Status:** ✅ COMPLETE - Execution Flow Documentation

---

## V6.5.4 Institutional Fixes Summary

| Fix | Problem | Solution |
|-----|---------|----------|
| **FIX 1** | Límites verificados al final | Límites verificados AL INICIO del ciclo |
| **FIX 2** | Risk Guardian con límites "blandos" | Hard cap absoluto: min(size, MAX_LIMIT) |
| **FIX 3** | Paper mode bypass de coherencia | Mismas reglas para paper y real |
| **FIX 4** | FLOOR_RESCUE/RECOVERY bias (revenge trading) | Eliminado - cada trade es evento aislado |

---

## 1. High-Level Trading Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     OMNIX V6.5.4 TRADING FLOW (INSTITUTIONAL)               │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │   ENTRY POINTS  │
                              │   main.py       │
                              │   Telegram Bot  │
                              └────────┬────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          AUTO TRADING BOT V6.5.4                             │
│                        (auto_trading_bot.py - 3,950+ lines)                  │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │  Multi-Crypto Scanner (11 pairs)                                       │  │
│  │  • BTC/USD, ETH/USD, SOL/USD, XRP/USD, DOGE/USD, ADA/USD              │  │
│  │  • DOT/USD, LINK/USD, AVAX/USD, MATIC/USD, ATOM/USD                   │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│               V6.5.4 POSITION LIMIT CHECK (FIRST!) - INSTITUTIONAL           │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ _check_position_limit_early() - BEFORE any CPU-intensive analysis      │ │
│  │ • If positions >= max_open_positions: SKIP to SELL-ONLY mode           │ │
│  │ • Saves CPU by avoiding 10-strategy analysis when limit reached        │ │
│  │ • Only processes TP/SL and evaluations in SELL-ONLY mode               │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           10 STRATEGY ANALYSIS                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │ Monte Carlo│  │ Black Swan │  │ Sentiment  │  │   Kelly    │             │
│  │ (10k sims) │  │ Detection  │  │  Analysis  │  │ Criterion  │             │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │ HMM Regime │  │  Kalman    │  │  Quantum   │  │  ARES V1   │             │
│  │ Detection  │  │  Filter    │  │ Momentum   │  │   Swing    │             │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘             │
│  ┌────────────┐  ┌────────────────────────────────────────────┐             │
│  │  ARES V2   │  │        NON-MARKOVIAN KERNEL V6.5           │             │
│  │  Scalping  │  │  K(t-s) = exp(-|t-s|/τ) × [1 + ε×cos(Ω)]  │             │
│  └────────────┘  └────────────────────────────────────────────┘             │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    COHERENCE ENGINE V6.5 - 6-TIER VETO SYSTEM                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ Tier 1: Signal Strength Validation                                      │ │
│  │ Tier 2: Strategy Consensus (≥45% agreement)                             │ │
│  │ Tier 3: Risk Limit Verification                                         │ │
│  │ Tier 4: Regime Alignment Check                                          │ │
│  │ Tier 5: Memory Coherence Score (≥30%)                                   │ │
│  │ Tier 6: Final Execution Approval                                        │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                      Target Win Rate: >55%                                   │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                     CAES V6.5.4 - CONFIDENCE ADAPTIVE ENTRY                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ Position Sizing: multiplier = 0.5 + 2.5 × sigmoid(confidence - 0.5)    │ │
│  │ Range: 0.5x to 3.0x with safety caps                                    │ │
│  │                                                                          │ │
│  │ V6.5.4 INSTITUTIONAL: NO artificial bias applied                        │ │
│  │ • ELIMINADO: FLOOR_RESCUE, RECOVERY (era revenge trading)              │ │
│  │ • Cada trade es un evento estadístico aislado                          │ │
│  │ • Score negativo = NO COMPRAR (sin manipulación)                        │ │
│  │ • Fear & Greed Contrarian mantenido (estrategia válida)                 │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                 AI RISK GUARDIAN V5.4 + V6.5.4 HARD CAP                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ • Overtrading prevention                                                 │ │
│  │ • Drawdown protection                                                    │ │
│  │ • Revenge trading detection                                              │ │
│  │ • Daily loss limits                                                      │ │
│  │ • Position concentration limits                                          │ │
│  │                                                                          │ │
│  │ V6.5.4 INSTITUTIONAL: HARD CAP ABSOLUTO                                 │ │
│  │ • max_trade_size_usd = $20,000 - NUNCA excede este límite               │ │
│  │ • get_adjusted_position_size() aplica: min(size, MAX_LIMIT)             │ │
│  │ • Sin excepciones, sin "recortes suaves"                                 │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
    ┌───────────────────────────┐   ┌───────────────────────────┐
    │      PAPER TRADING        │   │       REAL TRADING        │
    │  (Track Record Mode)      │   │     (Post-Funding)        │
    │                           │   │                           │
    │  PaperTradingManager      │   │  KrakenAPIClient          │
    │  $1M Virtual Balance      │   │  Real Order Execution     │
    │  Real Kraken Prices       │   │  Actual Funds             │
    └─────────────┬─────────────┘   └─────────────┬─────────────┘
                  │                               │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    POSITION MANAGER (DynamicPositionManager)                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ • Open position tracking                                                 │ │
│  │ • Dynamic TP/SL adjustment                                               │ │
│  │ • Symbol tracking per user                                               │ │
│  │ • P&L calculation                                                        │ │
│  │ • Trade evaluation scheduling                                            │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    DATABASE SERVICE (PostgreSQL + Redis)                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ PostgreSQL (Railway):                                                    │ │
│  │ • paper_trading_trades - Trade history                                   │ │
│  │ • paper_trading_positions - Open positions                               │ │
│  │ • paper_trading_balances - Balance tracking                              │ │
│  │ • balance_history - P&L over time                                        │ │
│  │                                                                          │ │
│  │ Redis (Railway):                                                         │ │
│  │ • Session state caching                                                  │ │
│  │ • Rate limiting                                                          │ │
│  │ • Real-time price cache                                                  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Trading Cycle

### 2.1 Entry Point (main.py)

```python
# main.py - Line 1-70
# 1. Clean Python cache
# 2. Configure logging
# 3. Load environment (DATABASE_URL, API keys)
# 4. Initialize modules (Stock Trading, Stripe, AI)
# 5. Start AutoTradingBot
# 6. Run Telegram bot polling
```

### 2.2 AutoTradingBot Initialization

```python
# auto_trading_bot.py
class AutoTradingBot:
    def __init__(self):
        # Initialize 10 strategies
        self.strategies = {
            'monte_carlo': MonteCarloSimulator(),
            'black_swan': BlackSwanDetector(),
            'sentiment': SentimentAnalyzer(),
            'kelly': KellyCriterion(),
            'hmm': HMMRegimeDetector(),
            'kalman': KalmanFilter(),
            'quantum_momentum': QuantumMomentum(),
            'ares_v1': AresProtocolV1(),
            'ares_v2': AresProtocolV2(),
            'non_markovian': NonMarkovianKernel()
        }
        
        # Initialize support modules
        self.coherence_engine = CoherenceEngine()
        self.caes = CAESModule()
        self.risk_guardian = AIRiskGuardian()
        self.position_manager = DynamicPositionManager()
        self.database = DatabaseServiceEnterprise()
```

### 2.3 Trading Cycle Execution

```python
async def run_trading_cycle(self):
    """Main trading loop - runs every 60 seconds"""
    
    # Step 1: Scan all 11 crypto pairs
    for pair in self.CRYPTO_PAIRS:
        signal = await self.analyze_pair(pair)
        
        if signal.strength >= SignalStrength.MODERATE:
            # Step 2: Coherence Engine validation
            coherence_result = self.coherence_engine.validate(signal)
            
            if coherence_result.approved:
                # Step 3: CAES position sizing
                position_size = self.caes.calculate_size(
                    confidence=signal.confidence,
                    sub_regime=self.detect_sub_regime()
                )
                
                # Step 4: Risk Guardian final check
                if self.risk_guardian.approve_trade(signal, position_size):
                    # Step 5: Execute trade
                    await self.execute_trade(pair, signal, position_size)
```

---

## 3. Strategy Analysis Pipeline

### 3.1 Monte Carlo Simulation

```python
class MonteCarloSimulator:
    """10,000 path simulations for probability estimation"""
    
    def simulate(self, price_data, num_paths=10000):
        # Generate price paths using GBM
        # Calculate probability of profit
        # Return confidence score (0-1)
```

### 3.2 ARES V1 (Swing Trading)

```python
class AresProtocolV1:
    """55-65% win rate target, swing timeframe"""
    
    LAYERS = {
        'ANF': 'Adaptive Noise Filter',    # Filters 90% of noise
        'ISA': 'Institutional Signal Analysis',  # 6 signals
        'SXE': 'Smart Execution Engine'    # Hedge fund execution
    }
    
    def analyze(self, candles):
        # Layer 1: ANF filtering
        filtered = self.anf.filter(candles)
        
        # Layer 2: ISA signals
        signals = self.isa.analyze(filtered)
        
        # Layer 3: SXE execution decision
        return self.sxe.decide(signals)
```

### 3.3 Non-Markovian Kernel

```python
class NonMarkovianKernel:
    """Memory-based temporal analysis"""
    
    def compute_kernel(self, t, s):
        """K(t-s) = exp(-|t-s|/τ) × [1 + ε × cos(Ω(t-s))]"""
        tau = 12  # hours
        epsilon = 0.35
        omega = 0.523  # radians
        
        delta = abs(t - s)
        decay = np.exp(-delta / tau)
        oscillation = 1 + epsilon * np.cos(omega * delta)
        
        return decay * oscillation
    
    def get_memory_weighted_signal(self, history):
        """Weight historical signals by kernel"""
        weights = [self.compute_kernel(now, t) for t in history.times]
        return np.average(history.signals, weights=weights)
```

---

## 4. Coherence Engine (6-Tier Veto)

```python
class CoherenceEngine:
    """Validates strategy agreement before execution"""
    
    THRESHOLDS = {
        'quality': 0.30,      # 30% minimum score
        'consensus': 0.45,    # 45% strategy agreement
        'win_rate_target': 0.55  # 55% target
    }
    
    def validate(self, signal):
        result = ValidationResult()
        
        # Tier 1: Signal strength
        if signal.strength < SignalStrength.MODERATE:
            result.add_veto("Signal too weak")
            return result
        
        # Tier 2: Strategy consensus
        agreeing = sum(1 for s in self.strategies if s.agrees(signal))
        consensus = agreeing / len(self.strategies)
        if consensus < self.THRESHOLDS['consensus']:
            result.add_veto(f"Low consensus: {consensus:.1%}")
            return result
        
        # Tier 3: Risk limits
        if not self.risk_limiter.check(signal):
            result.add_veto("Risk limit exceeded")
            return result
        
        # Tier 4: Regime alignment
        if not self.regime_aligned(signal):
            result.add_veto("Regime mismatch")
            return result
        
        # Tier 5: Memory coherence
        coherence = self.non_markovian.get_coherence_score()
        if coherence < self.THRESHOLDS['quality']:
            result.add_veto(f"Low coherence: {coherence:.1%}")
            return result
        
        # Tier 6: Final approval
        result.approved = True
        return result
```

---

## 5. CAES Position Sizing

```python
class CAESModule:
    """Confidence-Adaptive Entry System"""
    
    def calculate_size(self, confidence, sub_regime):
        # Sigmoid aggression function
        base = 0.5 + 2.5 * self.sigmoid(confidence - 0.5)
        
        # V6.5.4: No artificial bias applied
        # boost = 1.0 (eliminated FLOOR_RESCUE/RECOVERY)
        
        # Apply limits
        multiplier = min(3.0, max(0.5, base * boost))
        
        return self.base_position * multiplier
    
    def get_regime_boost(self, sub_regime):
        BOOSTS = {
            'FLOOR_RESCUE': 1.30,
            'RECOVERY': 1.20,
            'NEUTRAL': 1.10,
            'MOMENTUM': 1.05
        }
        return BOOSTS.get(sub_regime, 1.0)
    
    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x * 10))
```

---

## 6. Trade Execution Flow

### 6.1 Paper Trading (Current Mode)

```python
class PaperTradingManager:
    """Simulated trading with real prices"""
    
    async def execute_paper_trade(self, user_id, pair, side, amount_usd):
        # Get real price from Kraken
        price = await self.kraken_client.get_price(pair)
        
        # Calculate units
        units = amount_usd / price
        
        # Record trade in database
        trade_id = await self.db.insert_paper_trade(
            user_id=user_id,
            symbol=pair,
            side=side,
            entry_price=price,
            units=units,
            amount_usd=amount_usd
        )
        
        # Update position
        await self.position_manager.open_position(
            trade_id=trade_id,
            symbol=pair,
            entry_price=price,
            units=units
        )
        
        # Update balance
        await self.db.update_paper_balance(user_id, -amount_usd)
        
        return trade_id
```

### 6.2 Position Manager

```python
class DynamicPositionManager:
    """Tracks and manages open positions"""
    
    async def monitor_positions(self):
        """Continuous position monitoring loop"""
        positions = await self.db.get_open_positions()
        
        for position in positions:
            current_price = await self.get_price(position.symbol)
            
            # Calculate unrealized P&L
            pnl = self.calculate_pnl(position, current_price)
            
            # Check TP/SL
            if pnl >= position.take_profit:
                await self.close_position(position, "Take Profit")
            elif pnl <= position.stop_loss:
                await self.close_position(position, "Stop Loss")
            
            # Dynamic TP/SL adjustment
            await self.adjust_targets(position, current_price)
```

---

## 7. Database Persistence

### 7.1 Trade Recording

```sql
-- Paper trade insertion
INSERT INTO paper_trading_trades (
    user_id, symbol, side, entry_price, 
    units, amount_usd, timestamp, status
) VALUES ($1, $2, $3, $4, $5, $6, NOW(), 'open');

-- Position tracking
INSERT INTO paper_trading_positions (
    trade_id, user_id, symbol, entry_price,
    units, take_profit, stop_loss, status
) VALUES ($1, $2, $3, $4, $5, $6, $7, 'open');
```

### 7.2 Balance Updates

```sql
-- Record balance change
INSERT INTO balance_history (
    user_id, balance, change_amount, 
    change_type, timestamp
) VALUES ($1, $2, $3, $4, NOW());

-- Update paper balance
UPDATE paper_trading_balances 
SET balance = balance + $2, updated_at = NOW()
WHERE user_id = $1;
```

---

## 8. Signal Tiering System

| Tier | Strength | Confidence | Action |
|------|----------|------------|--------|
| **WEAK** | <30% | <0.4 | No trade |
| **MODERATE** | 30-50% | 0.4-0.6 | Small position (0.5x) |
| **STRONG** | 50-70% | 0.6-0.8 | Normal position (1.0x) |
| **ULTRA** | >70% | >0.8 | Enhanced position (up to 3.0x) |

---

## 9. V6.5.4 Institutional Practices

### 9.1 No Artificial Bias (ELIMINATED in V6.5.4)

```python
# V6.5.4: NO artificial bias applied
# Each trade is an isolated statistical event
# Score negativo = NO COMPRAR (sin manipulación)

# ELIMINADO (era revenge trading):
# - FLOOR_RESCUE: Compraba cuando score era muy negativo
# - RECOVERY: Compraba cuando score era negativo
# - Track Record Accelerator: 1.3x boost primeros 50 trades

# MANTENIDO (estrategia válida):
# Fear & Greed Contrarian - comprar en miedo extremo
if fear_greed_index < 25:  # Extreme fear (valid contrarian strategy)
    buy_signal_boost *= 1.4  # 40% boost
```

### 9.2 Same Rules for Paper and Real Mode

```python
# V6.5.4: Mismas reglas para PAPER y REAL mode
# La integridad de la señal es más importante que "probar el sistema"
# Esto genera un track record REPLICABLE en trading real

if coherence_score < veto_critical:
    # SIEMPRE bloquear - sin bypass de paper mode
    decision['should_trade'] = False
    
# V6.5.4: Sin reducciones suaves en paper mode
# Si el Risk Guardian bloquea, bloquea. Punto.
```

### 9.3 Hard Cap Absoluto

```python
# V6.5.4: Hard cap en Risk Guardian
max_trade_size = self.config.get('max_trade_size_usd', 20000)
adjusted_size = min(calculated_size, max_trade_size)  # NUNCA excede
```

---

## 10. Multi-User Session Management

```python
class UserSessionManager:
    """100,000+ simultaneous user support"""
    
    def __init__(self):
        self.redis = RedisStateManager()
        self.db = DatabaseServiceEnterprise()
        self.executor = ThreadPoolExecutor(max_workers=50)
        self.user_locks = {}
    
    async def get_session(self, user_id):
        # Check Redis cache first
        session = await self.redis.get(f"session:{user_id}")
        if session:
            return session
        
        # Load from database
        session = await self.db.get_user_session(user_id)
        
        # Cache for 5 minutes
        await self.redis.set(f"session:{user_id}", session, ex=300)
        
        return session
    
    async def execute_user_trade(self, user_id, trade_params):
        # Per-user locking for thread safety
        async with self.get_lock(user_id):
            session = await self.get_session(user_id)
            return await self.trading_bot.execute_trade(session, trade_params)
```

---

## Document Changelog

| Date | Version | Changes |
|------|---------|---------|
| Dec 6, 2025 | 2.0 | V6.5.4 Institutional Fixes - eliminated bias, hard cap, no paper bypass |
| Dec 6, 2025 | 1.0 | Initial trading flow architecture documentation |
