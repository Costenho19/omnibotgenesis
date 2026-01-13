# OMNIX Dashboard Improvement Backlog

**Created:** January 13, 2026  
**Last Updated:** January 13, 2026  
**Reference:** ADR-006-dashboard-improvement-proposals.md

## Priority Legend

| Priority | Timeline | Description |
|----------|----------|-------------|
| P0 | TODAY | Critical bugs affecting credibility |
| P1 | THIS WEEK | High-impact UX improvements |
| P2 | NEXT WEEK | Nice-to-have features |
| P3 | BACKLOG | Future considerations |

---

## P0: Critical Fixes (TODAY)

### BUG-001: WR Dir Shows 0.0% Instead of 37.8%

**Location:** Trade History Widget  
**File:** `omnix_dashboard/blueprints/core.py`  
**Problem:** Trade History API didn't return `win_rate_directional`  
**Fix:** Added SQL aggregate `SUM(CASE WHEN profit_pct > 0 THEN 1 ELSE 0 END)` to API  
**Status:** [x] COMPLETED (Jan 13, 2026)

### BUG-002: Fee Eroded Shows 0 Instead of 21

**Location:** Trade History Widget  
**File:** `omnix_dashboard/blueprints/core.py`  
**Problem:** Fee-eroded count not returned by API  
**Fix:** Added SQL aggregate `SUM(CASE WHEN profit_pct > 0 AND profit_loss < 0 THEN 1 ELSE 0 END)` to API  
**Status:** [x] COMPLETED (Jan 13, 2026)

### BUG-003: "Protected" Metric is Misleading

**Location:** Header  
**Files:** `omnix_dashboard/templates/terminal.html`  
**Problem:** "$31.4M Protected" implies $31.4M at risk when capital is $1M  
**Fix:** Renamed to "Notional Blocked" with explanatory tooltip  
**Status:** [x] COMPLETED (Jan 13, 2026)

---

## P1: UX Improvements (THIS WEEK)

### FEAT-001: System Health Score Widget

**Description:** Visual health indicator showing system status at a glance  
**Components:**
- Risk Controls score
- Data Quality score
- Win Rate score (calibrating)
- Latency score
- Uptime score
- Overall score (weighted average)

**Status:** [ ] Not Started

### FEAT-002: Live Status Section

**Description:** Real-time view of what the system is doing NOW  
**Components:**
- Current action (HOLD/ANALYZING/EXECUTING)
- Reason for action
- Active vetos per pair
- Time until next analysis

**Status:** [ ] Not Started

### FEAT-003: Quick Insights (Auto-Generated)

**Description:** AI-generated actionable insights based on current data  
**Components:**
- Toxic symbols identification
- Best performing conditions
- Current system mode
- Alpha vs benchmark

**Status:** [ ] Not Started

### FEAT-004: Calibration Progress Bar

**Description:** Visual progress toward system optimization  
**Components:**
- Phase 1: Data Collection (100%)
- Phase 2: Pattern Analysis (65%)
- Phase 3: Threshold Optimization (30%)
- Phase 4: Live Deployment (0%)
- ETA for each phase

**Status:** [ ] Not Started

### FEAT-005: Recommended Actions

**Description:** Suggested next steps for Harold  
**Components:**
- Urgent actions with reasoning
- Review items with context
- Confirmation of correct decisions

**Status:** [ ] Not Started

---

## P2: Nice-to-Have (NEXT WEEK)

### FEAT-006: Comparative Metrics Table

**Description:** OMNIX vs BTC Hold vs Average Bot comparison  
**Metrics:** Return, Max DD, Win Rate, Sharpe, Alpha

### FEAT-007: P&L Breakdown Visual

**Description:** Detailed P&L by symbol and by reason  
**Components:** Bar charts, percentages, trend indicators

### FEAT-008: Risk Heatmap

**Description:** Visual grid of risk levels per symbol  
**Metrics:** Coherence, Volatility, Black Swan, Overall Risk

### FEAT-009: Real-Time Decision Log

**Description:** Scrolling log of all decisions  
**Features:** Timestamps, actions, reasons, filters

### FEAT-010: Regime Detection Dashboard

**Description:** Current market regime with historical performance  
**Components:** Regime indicator, confidence, duration, performance by regime

### FEAT-011: Trade History Filters

**Description:** Filter and sort trade history  
**Filters:** Wins/Losses, Symbol, Date Range, Show/Hide columns

### FEAT-012: Collapsible Advanced Sections

**Description:** Mobile-friendly collapsed sections  
**Sections:** Advanced Metrics, Detailed History, Model Parameters

---

## P3: Backlog (Future)

### FEAT-013: Expected vs Actual Analysis

**Description:** Monte Carlo predictions vs actual results

### FEAT-014: Model Confidence Dashboard

**Description:** Per-strategy reliability scores

### FEAT-015: Veto Effectiveness Analysis

**Description:** Detailed veto breakdown with effectiveness metrics

---

## Progress Tracking

| ID | Description | Priority | Status | Assigned | Completed |
|----|-------------|----------|--------|----------|-----------|
| BUG-001 | WR Dir 0.0% | P0 | DONE | Agent | Jan 13, 2026 |
| BUG-002 | Fee Eroded 0 | P0 | DONE | Agent | Jan 13, 2026 |
| BUG-003 | Protected misleading | P0 | DONE | Agent | Jan 13, 2026 |
| FEAT-001 | System Health Score | P1 | Not Started | - | - |
| FEAT-002 | Live Status | P1 | Not Started | - | - |
| FEAT-003 | Quick Insights | P1 | Not Started | - | - |
| FEAT-004 | Calibration Progress | P1 | Not Started | - | - |
| FEAT-005 | Recommended Actions | P1 | Not Started | - | - |

---

## Notes

- All fixes must maintain ADR-002 (Honest Framing)
- All metrics must follow ADR-005 (Dual Win Rate Framework)
- Dashboard target score: 9.5/10 (current: 7.5/10)
