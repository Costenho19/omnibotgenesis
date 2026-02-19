# OMNIX Risk Guardian™

**Version**: OMNIX Advanced Tier  
**Document Type**: Product Feature Sheet  
**Classification**: Investor Confidential  
**Audience**: Institutional Investors, Risk Officers, Compliance Teams  
**Last Updated**: January 23, 2026

---

## Executive Summary

**OMNIX Risk Guardian™** is the multi-layer risk orchestration system at the core of OMNIX. It enforces capital preservation through independent validation layers that must unanimously approve every trade before execution.

> "No single signal can override the collective judgment of all risk systems."

### Key Metrics

| Metric | Value |
|--------|-------|
| Capital Preservation Rate | 98.5% |
| Independent Risk Layers | 6 |
| Maximum Per-Trade Exposure | 5% |
| Maximum Portfolio Drawdown | 15% |
| Minimum Edge Confirmation | 3 consecutive cycles |

---

## Risk Objectives

OMNIX Risk Guardian is designed to achieve:

1. **Capital Preservation First** — Protect principal before seeking returns
2. **Transparent Decision-Making** — Every blocked trade is logged with rationale
3. **Governance Compliance** — Full audit trail for institutional requirements
4. **Tail Risk Protection** — Black Swan detection prevents exposure during market stress

---

## Risk Architecture

### The 6-Layer Veto System

Every potential trade must pass through all layers. **Any single layer can block execution.**

```
┌─────────────────────────────────────────────────────────────┐
│                    INCOMING SIGNAL                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: MONTE CARLO VALIDATION                            │
│  • 10,000 simulation paths per decision                     │
│  • VETO if Expected Return < 0%                             │
│  • VETO if VaR95 worse than -3%                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: RMS LIMITS ENGINE                                 │
│  • Pre-trade validation active                              │
│  • Maximum 5% per single trade                              │
│  • Maximum 15% portfolio drawdown                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: COHERENCE ENGINE (6-TIER)                         │
│  • Validates signal agreement across indicators             │
│  • CRITICAL VETO if coherence < 35%                         │
│  • NORMAL VETO if coherence < 50%                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 4: BLACK SWAN DETECTOR                               │
│  • Real-time tail event monitoring                          │
│  • VETO on SEVERE or EXTREME events                         │
│  • Reduced exposure on MEDIUM severity                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 5: EDGE CONFIRMATION WINDOW (ECW)                    │
│  • Requires 3 consecutive positive cycles                   │
│  • Win Rate ≥ 52% (above break-even)                        │
│  • Expected Return > 0%                                     │
│  • Black Swan ≤ MEDIUM                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 6: FINAL DECISION GATE                               │
│  • Consolidates all layer approvals                         │
│  • Generates decision_trace for audit                       │
│  • Logs FINAL_DECISION_REASON                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    TRADE EXECUTED or BLOCKED
```

---

## Operational Controls

### Kill-Switch (Automatic Halt)

OMNIX includes automatic circuit-breaker functionality:

| Trigger | Action |
|---------|--------|
| Portfolio drawdown exceeds limit | Halt all trading |
| Multiple consecutive losses | Reduce position sizing |
| System anomaly detected | Pause for manual review |
| Black Swan EXTREME | Immediate trade halt |

### Capital Preservation Mode

The default operating mode prioritizes preservation:

| Setting | Value |
|---------|-------|
| Leverage | Disabled by default |
| Position sizing | Conservative (Kelly fraction reduced) |
| Asset eligibility | Major pairs only (BTC, ETH) |
| Strategy mode | SNIPER (precision over volume) |

### Drawdown Governor

| Parameter | Limit |
|-----------|-------|
| Maximum single-trade loss | 5% of portfolio |
| Maximum portfolio drawdown | 15% |
| Recovery mode trigger | 10% drawdown |
| Recovery action | 50% position size reduction |

### Exposure Limits

| Asset Class | Maximum Exposure |
|-------------|------------------|
| Single position | 5% |
| Correlated assets | Combined limit enforced |
| High volatility periods | Reduced exposure |
| Black Swan events | Zero new exposure |

---

## Validation Evidence

### Decision Audit Trail

Every decision is logged with complete traceability:

```json
{
  "decision_type": "BLOCKED",
  "timestamp": "2026-01-23T08:30:00Z",
  "symbol": "BTC/USD",
  "veto_source": "COHERENCE_GATE",
  "veto_reason": "Coherence 42% < threshold 50%",
  "monte_carlo": {
    "win_rate": "48.2%",
    "expected_return": "-0.3%"
  },
  "ecw_status": "WAITING (1/3 cycles)",
  "black_swan_severity": "LOW"
}
```

### Blocked Trades Visibility

The dashboard displays:

- **Capital at Risk**: Current exposure percentage
- **Blocked Decisions**: Count and reasons
- **Risk State**: SAFE / CAUTION / LOCKED
- **Veto History**: Which layers blocked which trades

### Reference Documentation

| Document | Purpose |
|----------|---------|
| ADR-019 | Edge Confirmation Window specification |
| ADR-018 | Decision Contradiction Index |
| ADR-021 | Shadow Trade Metrics VIEW |
| system_state_manifest.json | Authoritative system configuration |

---

## Outcomes

### What Risk Guardian Delivers

| Outcome | Mechanism |
|---------|-----------|
| **98.5% Capital Preserved** | Multi-layer veto prevents impulsive trades |
| **Transparent Blocking** | Every veto logged with rationale |
| **Patience Over Speed** | ECW requires edge persistence, not reaction |
| **Tail Risk Protection** | Black Swan detector halts during stress |
| **Governance Ready** | Full audit trail for compliance |

### What Risk Guardian Prevents

| Prevention | How |
|------------|-----|
| False positive trades | Coherence Engine filters signal noise |
| Overtrading | ECW requires 3-cycle confirmation |
| Catastrophic loss | Drawdown Governor enforces limits |
| Unauthorized execution | Cryptographic order signing (experimenting with PQC) |
| Emotional decisions | AI governance, no manual override |

---

## Institutional Mode

### "Institutional Safe Mode" Toggle

When enabled:

| Setting | Behavior |
|---------|----------|
| Aggressive strategies | Disabled |
| Leverage | Zero |
| Assets | Major pairs only (BTC, ETH) |
| Objective | Maximum capital preservation |
| Trade frequency | Reduced (quality over quantity) |

> This mode prioritizes preservation over returns—designed for capital that cannot afford experimental risk.

---

## Auditability as Competitive Moat

> "Every decision is logged, traceable, and reviewable."

Few trading systems can make this claim. OMNIX provides:

| Audit Feature | Description |
|---------------|-------------|
| **Full decision trace** | Every trade (executed or blocked) logged with complete rationale |
| **Veto attribution** | Which layer blocked, why, with all input metrics |
| **Temporal query** | Historical decisions queryable by date range |
| **Export capability** | Decision logs exportable for external audit |
| **No hidden logic** | All rules documented in ADR format |

This level of auditability is rare in algorithmic trading—and essential for institutional capital.

---

## Governance & Compliance

### Audit Capabilities

| Capability | Status |
|------------|--------|
| Decision trace logging | Operational |
| Trade rationale export | Available |
| Veto history query | SQL VIEW available |
| Risk state monitoring | Real-time dashboard |

### Compliance Features

| Feature | Description |
|---------|-------------|
| Read-only investor view | Dashboard access without control |
| Decision transparency | Full rationale for every action |
| No hidden overrides | All decisions follow same rules |
| PQC security | Experimenting with NIST-aligned quantum-resistant signing |

---

## Disclaimer

OMNIX Risk Guardian is a risk management system, not a guarantee of returns or capital preservation. The 98.5% capital preservation rate reflects historical paper trading performance. All trading involves risk. This document does not constitute financial advice.

---

**Reference Documents**:
- `docs/REAL_SYSTEM_STATUS.md` — System state
- `docs/reference/adr/ADR-019-edge-confirmation-window.md` — ECW details
- `omnix_config/system_state_manifest.json` — Configuration source
