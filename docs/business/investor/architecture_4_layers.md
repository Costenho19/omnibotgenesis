# OMNIX 4-Layer Security Architecture

**For**: Hub71 Venture Builder Technical Review  
**Version**: V6.5.4e INSTITUTIONAL+  
**Date**: January 2026

---

## Architecture Overview

OMNIX employs a 4-layer defense-in-depth architecture that ensures no trade executes without passing multiple independent validation gates.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LAYER 1: SIGNAL INTELLIGENCE                      │
│  10 AI Strategies + Market Analysis + Regime Detection              │
│  ─────────────────────────────────────────────────────────────────  │
│  Output: Raw signals with confidence scores                         │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LAYER 2: RISK & COHERENCE                         │
│  6-Tier Coherence Engine + Monte Carlo + Black Swan Detector        │
│  ─────────────────────────────────────────────────────────────────  │
│  Output: Validated signals (PASS/REDUCE/VETO)                       │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LAYER 3: EXECUTION PROTOCOL                       │
│  Position Sizing + Kelly Criterion + TWAP/VWAP/ICEBERG              │
│  ─────────────────────────────────────────────────────────────────  │
│  Output: Optimized execution with risk limits                       │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LAYER 4: AUDIT & GOVERNANCE                       │
│  Decision Logger + Shadow Portfolio + Investor Dashboard            │
│  ─────────────────────────────────────────────────────────────────  │
│  Output: Full audit trail + regulatory compliance                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Signal Intelligence

**Purpose**: Generate trading signals from multiple independent sources

### Components

| Component | Function | Confidence Range |
|-----------|----------|------------------|
| EMA Regime Signal | Primary trend direction | 0–40 points |
| HMM Regime Detector | Market state classification | 0–25 points |
| Kalman Filter | Noise reduction, price prediction | 0–15 points |
| Non-Markovian Memory | Historical pattern recognition | 0–15 points |
| Kelly Criterion | Optimal position sizing | Modifier |

### Scoring Logic

```
Total Score = EMA (40) + HMM (25) + Kalman (15) + Memory (15)
Maximum: 95 points (before modifiers)
Minimum for execution: 40 points (after all gates)
```

---

## Layer 2: Risk & Coherence

**Purpose**: Filter out signals that don't meet institutional standards

### 6-Tier Coherence Engine

| Tier | Threshold | Action |
|------|-----------|--------|
| CRITICAL | <20% | BLOCK (immediate) |
| POOR | 20–30% | BLOCK |
| LOW | 30–40% | REDUCE 50% |
| MEDIUM | 40–50% | REDUCE 25% |
| HIGH | 50–70% | PASS |
| EXCELLENT | >70% | PASS (full size) |

### Monte Carlo Validation

- 10,000 scenario simulations per signal
- Win rate threshold: 50%+
- Expected return threshold: 0%+
- Action: SIZE_REDUCE if borderline, VETO if negative

### Black Swan Detector

- Kurtosis analysis for fat-tail detection
- Crash probability calculation
- Risk levels: LOW / MEDIUM / HIGH / EXTREME
- Action: VETO if crash probability > 30%

---

## Layer 3: Execution Protocol

**Purpose**: Optimize execution to minimize slippage and market impact

### Position Sizing (ADR-004)

| Rule | Value | Rationale |
|------|-------|-----------|
| Max Position | $20,000 | Empirical: trades >$10K have 31% WR |
| Kelly Max | 2% | Conservative sizing |
| Spread Minimum | 25 bps | Avoid illiquid pairs |

### Execution Algorithms

| Algorithm | Use Case |
|-----------|----------|
| TWAP | Large orders, time-sensitive |
| VWAP | Volume-weighted optimization |
| ICEBERG | Hidden large orders |

---

## Layer 4: Audit & Governance

**Purpose**: Maintain institutional-grade transparency and compliance

### InstitutionalDecisionLogger V6.5.4

| Event | Description |
|-------|-------------|
| SIGNAL_RECEIVED | Raw signal from strategy |
| COHERENCE_EVAL | Coherence gate result |
| MC_VALIDATION | Monte Carlo result |
| BLACK_SWAN_CHECK | Risk assessment |
| DECISION_MADE | Final trade decision |
| EXECUTION_START | Order submitted |
| EXECUTION_COMPLETE | Order filled |
| POSITION_OPENED | Position active |
| POSITION_CLOSED | Position closed |
| P&L_CALCULATED | Profit/loss recorded |
| AUDIT_COMPLETE | Full trace archived |

### Shadow Portfolio

Tracks every vetoed trade for:
- Counterfactual analysis ("would it have won?")
- Filter calibration recommendations
- Investor transparency

### Investor Dashboard

- Real-time capital protection metrics
- Full trade history with decision traces
- Regime detection visualization
- Learning engine insights

---

## Security Features

### Post-Quantum Cryptography (NIST FIPS-203/204)

| Algorithm | Purpose |
|-----------|---------|
| Kyber-768 | Key encapsulation |
| Dilithium-3 | Digital signatures |

**Status**: First retail trading platform with quantum-resistant security

### Data Protection

- All API keys encrypted at rest
- Redis session isolation per user
- PostgreSQL Row-Level Security (RLS)
- No client-side credential storage

---

## Fail-Closed Architecture

**Core Principle**: If any layer fails or returns an error, the system defaults to BLOCK.

| Scenario | Action |
|----------|--------|
| Coherence calculation fails | BLOCK |
| Monte Carlo timeout | BLOCK |
| API unavailable | BLOCK |
| Unknown error | BLOCK |

This ensures capital is never at risk due to system failures.

---

## Compliance Readiness

| Framework | Status |
|-----------|--------|
| ADGM (Abu Dhabi) | Architecture ready |
| DIFC (Dubai) | Architecture ready |
| SEC (US) | Paper trading only |
| Audit Trail | Grafana/Loki/ELK compatible |

---

## References

- ADR-001: Hexagonal Architecture
- ADR-003: Official Positioning
- ADR-004: Position Sizing Hotfix
- ADR-007: Coherence Threshold Calibration
- ARCHITECTURE.md: Technical deep-dive

---

*Document generated: January 19, 2026*  
*OMNIX V6.5.4e INSTITUTIONAL+*
