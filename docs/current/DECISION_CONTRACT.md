# OMNIX V6.5.4d Decision Contract

> **Fecha**: December 25, 2025 (Updated)  
> **Versión**: V6.5.4d PRODUCTION_STABLE  
> **Propósito**: Documentación formal del sistema de decisiones para auditoría e inversores

---

## 1. Flujo de Decisión Jerárquico

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECISION FLOW V6.5.4d                        │
├─────────────────────────────────────────────────────────────────┤
│  STEP 1: EMA Signal Generation                                  │
│         ↓                                                       │
│  STEP 2: MC VETO (expected_return < -0.1% || VaR95 > -3%)      │
│         ↓                                                       │
│  STEP 3: RMS VETO (CircuitBreaker + LimitsEngine)              │
│         ↓                                                       │
│  STEP 4: COHERENCE GATE                                         │
│     • veto_critical < 35% → REJECTED                           │
│     • veto_normal < 50% → REJECTED                             │
│         ↓                                                       │
│  STEP 5: SCORING (5 inputs principales)                         │
│         ↓                                                       │
│  STEP 6: Decision + Execution                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Sistema de Scoring (5 Inputs Principales)

### 2.1 Scoring Aditivo (max_score = 105 pts)

| # | Componente | Peso Máximo | Condición Full Score |
|---|------------|-------------|----------------------|
| 1 | **EMA Regime Signal** | 40 pts | LONG/SHORT @ ≥70% confidence |
| 2 | **HMM Regime** | 25 pts | TRENDING regime |
| 3 | **Kalman Filter** | 15 pts | BULLISH trend @ >60% strength |
| 4 | **Non-Markovian Memory** | 15 pts | BUY signal @ >60% confidence |
| 5 | **Kelly Criterion** | 10 pts | optimal_fraction > 5% |

### 2.2 Scoring Parcial

| Componente | Puntuación Media | Condición |
|------------|------------------|-----------|
| EMA Signal | 25 pts | LONG/SHORT @ 50-70% confidence |
| EMA Signal | 12 pts | LONG/SHORT @ <50% confidence |
| Non-Markovian | 8 pts | BUY @ 40-60% confidence |
| Kalman | 53% del peso | BULLISH/BEARISH @ <60% strength |

---

## 3. Veto/Penalty Layer (NO suma a max_score)

### 3.1 Vetos Duros (Bloqueo Inmediato)

| Veto | Condición | Penalización Paper | Penalización Real |
|------|-----------|-------------------|-------------------|
| **MC VETO** | expected_return < -0.1% OR VaR95 > -3% | Bloqueo total | Bloqueo total |
| **RMS VETO** | CircuitBreaker triggered | Bloqueo total | Bloqueo total |
| **COHERENCE_GATE_CRITICAL** | coherence < 35% | Bloqueo total | Bloqueo total |
| **COHERENCE_GATE_LOW** | coherence < 50% | Bloqueo total | Bloqueo total |

### 3.2 Penalizaciones Suaves

| Componente | Condición | Penalty Paper | Penalty Real |
|------------|-----------|---------------|--------------|
| **Monte Carlo** | win_rate < 40% | -10 pts | -20 pts |
| **Black Swan** | risk_level = HIGH OR crash_prob > 30% | -8 pts | -25 pts |
| **Sentiment** | overall_score < 25% | -5 pts | -15 pts |
| **Sentiment** | overall_score > 80% (greed) | -3 pts | -8 pts |
| **Quantum Momentum** | signal ≤ -7 (STRONG SELL) | -10 pts | -20 pts |
| **Quantum Momentum** | signal ≤ -4 (SELL) | -5 pts | -10 pts |

### 3.3 Boosts Tácticos (Excepciones)

| Componente | Condición | Boost Paper | Boost Real |
|------------|-----------|-------------|------------|
| **Fear Contrarian** | sentiment 25-35% | +3 pts | +2 pts |

---

## 4. Umbrales de Decisión

### 4.1 Score Thresholds (PRODUCTION_STABLE)

| Nivel | Umbral | Acción |
|-------|--------|--------|
| `score_very_strong` | ≥ 20 | EXECUTE con full position |
| `score_strong` | ≥ 12 | EXECUTE con position normal |
| `score_moderate` | ≥ 12 | DISABLED (igual que strong) |
| Score < 12 | - | NO TRADE |

### 4.2 Coherence Thresholds

| Umbral | Valor | Efecto |
|--------|-------|--------|
| `veto_critical` | < 35% | BLOCK - señal muy débil |
| `veto_normal` | < 50% | BLOCK - señal débil |
| `warning` | < 60% | Position reduction |
| `good` | ≥ 78% | Full position approval |

---

## 5. Estados de Decisión (decision_trace)

### 5.1 Estados de Bloqueo

```
COHERENCE_GATE_CRITICAL    → Bloqueado por coherence < 35%
COHERENCE_GATE_LOW         → Bloqueado por coherence < 50%
MC_VETO                    → Bloqueado por Monte Carlo analysis
RMS_VETO                   → Bloqueado por Risk Management System
BLACK_SWAN_VETO            → Bloqueado por high crash probability
QUANTUM_VETO               → Bloqueado por strong sell signal
```

### 5.2 Estados de Aprobación

```
COHERENCE_GATE: PASSED     → Señal aprobada para scoring
ARES_REMOVED               → Legacy code eliminado (Dec 24, 2025)
```

---

## 6. Configuración de Perfil Activo

**Perfil**: `PRODUCTION_STABLE V6.5.4d`

```python
min_trade_usd = 150.0
max_position_pct = 0.10
stop_loss_pct = 0.012
take_profit_pct = 0.035
min_confidence = 0.15
trades_per_day_target = 15
```

---

## 7. Trazabilidad y Auditoría

Cada decisión incluye:

1. **decision_trace**: Lista de estados y vetos aplicados
2. **v52_analysis**: Análisis detallado de cada componente
3. **raw_score / max_score**: Puntuación antes de normalización
4. **confidence**: Confianza final (0-100%)
5. **reason**: Lista de razones legibles

---

## 8. Historial de Cambios

| Fecha | Cambio | Autor |
|-------|--------|-------|
| Dec 24, 2025 | Coherence Gate Pre-Scoring | GPT Expert |
| Dec 24, 2025 | Umbrales: critical 25%→35%, normal 40%→50% | GPT Expert |
| Dec 24, 2025 | ARES code eliminado, EMA weight 25→40 | GPT Expert |
| Dec 24, 2025 | HMM weight 15→25, Non-Markovian 12→15 | GPT Expert |
| Dec 24, 2025 | Monte Carlo/Black Swan/Sentiment→Veto only | GPT Expert |
| Dec 25, 2025 | MC Veto threshold: 0% → -0.1% (track record) | Replit Agent |
| Dec 25, 2025 | Fix EC-A1: Auto-start authorization bug | Replit Agent |
| Dec 25, 2025 | Fix: unhashable dict in multi-user loop | Replit Agent |
| Dec 25, 2025 | EMA Signal: min_trend_strength 0.30→0.15 (low-vol) | Replit Agent |
| Dec 25, 2025 | EMA Signal: min_confidence 0.50→0.35 (low-vol) | Replit Agent |

---

*Este documento es parte del sistema de auditoría institucional de OMNIX V6.5.4d*
