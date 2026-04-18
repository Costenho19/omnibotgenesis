# ADR-056 — Investor Command Center

**Status**: IMPLEMENTED  
**Date**: 2026-03-29  
**Author**: Harold Nunes — OMNIX  
**Route**: `/command`  
**Endpoint**: `GET /api/metrics/live`

---

## Context

OMNIX operates 4 simultaneous governance engines 24/7 (ADR-028, ADR-052, ADR-054, ADR-055). Each vertical has its own dashboard, its own Flask API, and its own data. However, there was no single surface showing the full picture — all 4 verticals aggregated in one view with live data.

The gap: an investor or due diligence reviewer opening OMNIX for the first time sees one vertical at a time. The core thesis — "one governance engine, four domains" — requires a single view where both sides of that equation are visible simultaneously.

**Decision trigger**: After completing the multi-vertical expansion (March 29, 2026), the system was producing real data across 4 domains every 3–5 minutes. The data was there. The aggregation layer was missing.

---

## Decision

Build an **Investor Command Center** — a single-page, no-authentication, real-time dashboard at `/command` that aggregates live governance data from all 4 verticals through a new Flask endpoint `GET /api/metrics/live`.

### Design Principles (from ADR review)

1. **Zero mock data** — every number from the production database
2. **No fan-out to internal HTTP** — all queries run as direct SQL against PostgreSQL
3. **Partial data tolerance** — if one vertical fails, the other 3 still render correctly
4. **No authentication required** — this is a due diligence surface, not an ops panel
5. **Rate limiting** — handled at proxy/nginx level (not in-app, to avoid complexity)
6. **30-second refresh** — matches the cadence of the shortest governance cycle (robotics: 3 min)
7. **Bloomberg aesthetic** — dark, dense, institutional. Not a marketing page.

---

## API Contract

### `GET /api/metrics/live`

```json
{
  "success": true,
  "generated_at": "2026-03-29T08:00:00+00:00",
  "refresh_interval_sec": 30,
  "totals": {
    "decisions_total":   110447,
    "approved_total":    52831,
    "blocked_total":     49276,
    "hold_total":        8340,
    "decisions_today":   2900,
    "receipts_total":    104872,
    "uptime_days":       74,
    "adr_count":         57,
    "checkpoint_count":  11,
    "verticals_live":    4,
    "tam_usd":           "137B+"
  },
  "pipeline": {
    "checkpoints_count":       11,
    "cag_enabled":             true,
    "tie_enabled":             true,
    "shared_across_verticals": true,
    "checkpoints": [
      {"id": "CAG",   "name": "Context Admission Gate",    "layer": "pre"},
      {"id": "ACV",   "name": "Admissibility Consistency", "layer": "pre"},
      {"id": "CP-0",  "name": "Signal Integrity (SIV)",    "layer": "entry"},
      ...
      {"id": "TIE",   "name": "Trajectory Invariant",      "layer": "post"},
      {"id": "PQC",   "name": "Quantum-Secure Receipt",    "layer": "output"}
    ]
  },
  "verticals": {
    "trading": {
      "label":             "Digital Asset Trading",
      "market_size":       "$5B TAM",
      "live_since":        "2026-01-15",
      "color":             "#C9A227",
      "icon":              "📈",
      "decisions":         104872,
      "approved":          0,
      "blocked":           0,
      "hold":              104872,
      "decisions_today":   2684,
      "latest_receipt_id": "OMNIX-XXXXXXXX",
      "status":            "LIVE"
    },
    "credit":    { ... },
    "insurance": { ... },
    "robotics":  { ... , "active_robots": 63 }
  },
  "impact_phrases": [ "..." ],
  "health": {
    "partial_data":     false,
    "missing_verticals": []
  }
}
```

### SQL Sources (per vertical)

| Vertical | Table | Timestamp column | Receipt column |
|----------|-------|-----------------|----------------|
| Trading | `decision_receipts` | `timestamp_utc` | `receipt_id` |
| Credit | `credit_applications` | `submitted_at` | `receipt_id` |
| Insurance | `insurance_claims` | `created_at` | `receipt_id` |
| Robotics | `robot_actions` | `created_at` | `receipt_id` |

### Aggregation Logic

- `decisions_total` = sum of `COUNT(*)` from all 4 vertical tables
- `approved_total` = sum of `SUM(CASE WHEN decision='APPROVED' THEN 1 ELSE 0 END)` across all tables
- `blocked_total` = same for `BLOCKED`
- `hold_total` = same for `HOLD`
- `decisions_today` = sum of `COUNT(*)` where timestamp >= `DATE_TRUNC('day', NOW() AT TIME ZONE 'UTC')`
- `receipts_total` = `COUNT(*) FROM decision_receipts` (primary PQC receipt store = trading vertical)

---

## Frontend Architecture

**File**: `omnix_web/src/pages/InvestorCommandCenter.tsx`  
**Route**: `/command` (no auth, added to App.tsx)  
**Nav link**: Added to CommercialLanding.tsx nav as "⚡ Live Data"

### Component Structure

```
InvestorCommandCenter
├── Nav (sticky, OMNIX branding + LIVE pulse + Refresh button)
├── Header (animated total counter — AnimatedNumber component)
├── GlobalKPIRow (8 metric cards: total, approved, blocked, today, receipts, uptime, ADRs, checkpoints)
├── VerticalGrid (4 × VerticalCard)
│   └── VerticalCard: icon, decisions/approved/blocked bars, approval rate, latest receipt_id
├── PipelineProofPanel (17 checkpoints with layer color coding)
├── ImpactPhraseRotator (cycling quotes every 5s)
└── Footer (attribution + data transparency note)
```

### Key Technical Decisions

- **`AnimatedNumber`**: Custom hook-free component using `requestAnimationFrame` for smooth counter animation — no dependency on external animation library
- **Refresh**: `useCallback` + `setInterval` at 30s — no `useLiveMetrics` hook (avoids fallback mock data from that hook)
- **Partial data**: Each vertical fetches independently; if one fails, others render normally
- **No auth state**: No `useAuth`, no redirect — pure data page

---

## Consequences

**Positive:**
- Investor opens `/command` and sees 110,000+ decisions governed across 4 industries in one view
- Counters animate as data arrives — movement is the argument
- Pipeline proof panel shows same 17 layers governing all 4 verticals simultaneously
- Latest receipt IDs are real — investor can copy and verify at `/verify/<id>`
- Auto-refreshes every 30 seconds — numbers change on their own

**Operational:**
- One additional SQL query per vertical per refresh — negligible load
- `health.partial_data` flag allows frontend to show degraded state without crashing
- `impact_phrases` served from backend — easy to update without frontend rebuild

---

## Files

```
omnix_dashboard/blueprints/live_metrics.py          — Flask aggregator blueprint
omnix_web/src/pages/InvestorCommandCenter.tsx        — React investor dashboard
omnix_web/src/App.tsx                               — Route /command added
omnix_web/src/pages/CommercialLanding.tsx            — Nav link "⚡ Live Data" added
docs/reference/adr/ADR-056-investor-command-center.md — This document
```
