# OMNIX QUANTUM — Cost & Sustainability Report

**Document ID:** OMNIX-CSR-2026-001  
**Classification:** OPERATIONAL — Internal  
**Date:** May 10, 2026  
**Author:** Harold Nunes — Founder & Chief Architect, OMNIX QUANTUM LTD  
**Status:** ACTIVE  
**Review cycle:** Monthly

---

> **Purpose of this document:**
> OMNIX QUANTUM is a solo-founded platform. Sustainability is not a secondary concern —
> it is a prerequisite for everything else. This report documents the real monthly cost
> of running OMNIX QUANTUM in production, identifies what can be reduced today,
> and proposes a cost posture for each stage of growth.

---

## 1. Production Infrastructure — Current State

### 1.1 Database (PostgreSQL on Railway)

This is the dominant cost driver.

| Metric | Value |
|---|---|
| Database size | **4,773 MB (4.7 GB)** |
| Total rows | 1,246,407 |
| Tables with data | 53 / 113 |
| Growth rate | ~1,000+ rows/day (simulators active) |

**Top 5 tables by disk size:**

| Table | Size | Rows | Notes |
|---|---|---|---|
| `decision_receipts` | 1,758 MB | 141,971 | Core governance — KEEP |
| `governance_transparency_log` | 811 MB | 139,716 | Audit chain — KEEP |
| `shadow_trade_events` | 757 MB | 83,448 | Sim data — ARCHIVEABLE |
| `decision_receipts_warm` | 617 MB | 70,539 | Warm cache — REVIEW |
| `robot_actions` | 214 MB | 122,615 | Sim data — ARCHIVEABLE |

**Railway PostgreSQL pricing:**
- Storage: ~$0.000231/GB-hour → 4.773 GB × 720 h/month ≈ **$0.79/month storage**
- But Railway Pro plan (required for production): **$20/month base**
- PostgreSQL service add-on: typically bundled in Pro

### 1.2 Redis (Railway)

| Metric | Value |
|---|---|
| Usage | Anti-replay store + session cache |
| Data volume | Small (receipt IDs + session tokens, TTL-based) |
| Railway pricing | ~$0.000231/GB-hour, minimal usage |
| Estimated cost | **< $1/month** |

### 1.3 Web Services (Railway)

| Service | Purpose | Estimated cost |
|---|---|---|
| `stellar-hope` | Flask API + React frontend | ~$5–10/month compute |
| `omnibotgenesis` | Telegram governance bot | ~$5/month compute |

### 1.4 Third-Party APIs

| Service | Usage | Cost |
|---|---|---|
| Google Gemini API | AI governance analysis | Pay-per-use (must be active in GCP billing) |
| OpenAI GPT-4o-mini | Primary AI fallback | Pay-per-use |
| Anthropic Claude | Secondary fallback | Pay-per-use |
| Kraken API | Real trading data | Free (API access) |
| Alpha Vantage | Market data | Free tier (limited calls/min) |
| FRED (Federal Reserve) | Macro data | Free |
| Finnhub | Market data | Free tier |

---

## 2. Estimated Monthly Total

| Component | Estimated monthly cost |
|---|---|
| Railway Pro plan | $20.00 |
| PostgreSQL compute + storage | ~$5.00 |
| Redis | ~$1.00 |
| stellar-hope compute | ~$8.00 |
| omnibotgenesis compute | ~$5.00 |
| AI APIs (Gemini + OpenAI) | $5–20 (usage-dependent) |
| **Total estimate** | **$44–59/month** |

**Conservative estimate: ~$50/month to run OMNIX QUANTUM in full production.**

---

## 3. What Is Driving Cost — The Real Picture

### 3.1 The simulator problem

The 8 domain simulators running continuously in `Flask Dashboard` are writing
thousands of rows per day to simulation tables:

| Simulator | Table | Current rows | Size |
|---|---|---|---|
| Trading | `shadow_trade_events` | 83,448 | 757 MB |
| Robotics | `robot_actions` | 122,615 | 214 MB |
| Insurance | `insurance_claims` | 82,588 | 143 MB |
| Medical AI | `medical_decisions` | 74,386 | 119 MB |
| Autonomous agents | `agent_decisions` | 69,471 | 111 MB |
| Real estate | `property_decisions` | 46,552 | 70 MB |
| Energy | `energy_decisions` | 94,068 | 41 MB |
| Credit | `credit_applications` | 70,333 | 33 MB |

**These tables are simulation data.** They are valuable for demo purposes but are
not governance receipts — they are not cryptographically signed, they are not
part of the audit chain, and they grow unbounded.

**If simulators run 24/7, the DB will be ~9.5 GB in 60 days.**

### 3.2 `decision_receipts_warm` — duplicate data

The `decision_receipts_warm` table (617 MB, 70,539 rows) appears to be a warm cache
or archival index of `decision_receipts`. At 617 MB it is the 4th largest table.
Review whether this data is being actively used or can be pruned.

---

## 4. Cost Reduction Options — Right Now

### Option A: Simulator throttling (Immediate — saves ~$5–8/month in DB growth)

Cap simulator output to avoid unbounded growth:
- Run simulators on a cron schedule (every 4 hours instead of continuous)
- OR: add a row-count cap per domain (e.g., max 100K rows per sim table)
- Keep the most recent N rows, archive or delete older ones

**Impact:** Prevents DB from doubling every 30 days. No loss of governance capability.

### Option B: Simulation table archival (Short-term — saves ~2 GB DB space)

Move old simulation rows to a compressed archive table or simply delete rows
older than 90 days. These are not governance receipts — they are demo data.

**Impact:** Could reduce DB from 4.7 GB to ~2.5 GB, cutting storage costs ~45%.

### Option C: Turn off Flask Dashboard in Railway (Immediate — saves ~$5/month)

The Flask Dashboard (`omnix_dashboard`) runs as a separate process on Railway.
If it is not being actively used for external demos, it can be stopped in Railway.
It can be restarted on demand before any demo.

**Impact:** Saves ~$5/month. Zero impact on production governance or API.

### Option D: Downgrade Railway tier if under usage (Review)

Railway Pro at $20/month includes more compute than a solo founder needs in pre-revenue
phase. Review actual compute usage in Railway dashboard and consider whether Hobby plan
($5/month) meets current needs.

**Caveat:** Hobby plan has limitations on uptime and service count. Verify before downgrading.

---

## 5. What Must Stay — Non-Negotiable

| Component | Why it must stay |
|---|---|
| PostgreSQL — `decision_receipts` | 142K governance receipts — irrecoverable if lost |
| PostgreSQL — `governance_transparency_log` | Audit chain — required for verification |
| PostgreSQL — `avm_calibration_snapshots` | AVM baselines — required for governance |
| PostgreSQL — `b2b_clients` | Client registry |
| Redis | Anti-replay protection — required for strict mode |
| stellar-hope (web API) | Production endpoint at omnixquantum.net |
| `OMNIX_SIGNING_SECRET_KEY_B64` in Railway | PQC signing key — losing it means no new signed receipts |

---

## 6. What Can Wait — Phased Investment

| Capability | When to add | Estimated cost |
|---|---|---|
| Cold storage (S3/Backblaze/Wasabi) | Before institutional pilot | $2–5/month |
| UptimeRobot monitoring | This week | Free |
| Automated backup cron | RC-2 | Free (Railway cron) |
| Load balancer / CDN | When traffic > 100 req/min | $10–20/month |
| Multi-dyno scaling | When pilot is live | $20+/month |
| Dedicated staging environment | Before B2B sales | $20/month |

---

## 7. Sustainability Posture by Stage

### Stage 0 — Today (Pre-pilot, solo founder)

**Target cost: $35–45/month**

Actions:
- Keep stellar-hope + PostgreSQL + Redis + omnibotgenesis
- Throttle simulators (avoid unbounded DB growth)
- Archive or cap simulation tables
- Keep Flask Dashboard OFF in Railway (run locally when needed)
- Use Gemini free tier + OpenAI pay-per-use carefully

### Stage 1 — First Pilot (1–3 enterprise clients)

**Target cost: $60–100/month**

Actions:
- Enable staging environment
- Add cold storage backup
- Add UptimeRobot + Better Stack monitoring
- Keep simulators running for demo capability

### Stage 2 — Revenue (3+ paying clients)

**Target cost: $150–300/month**

Infrastructure pays for itself at this point. Focus shifts from cost reduction
to reliability and scaling.

---

## 8. The Honest Assessment

OMNIX QUANTUM costs approximately **$50/month** to run in full production today.

For a solo founder in pre-revenue stage, this is:
- Manageable if resources permit
- Worth protecting — shutting down and restarting Railway would not be trivial
- The biggest risk is **not cost** — it is **time**: keeping the platform running,
  the DB healthy, and the keys secure while also building the business

**Recommended immediate actions:**
1. Throttle simulators to prevent DB doubling in 30 days (free)
2. Set up UptimeRobot monitoring for omnixquantum.net/api/health/live (free)
3. Back up Railway signing key to password manager (free, critical)
4. Review Railway dashboard for actual compute usage and optimize if possible

---

## 9. Monthly Tracking

| Month | DB size | Monthly cost | Notes |
|---|---|---|---|
| May 2026 | 4.77 GB | ~$50 | Baseline — this report |
| June 2026 | Target < 5.5 GB | Target < $55 | With simulator throttling |
| July 2026 | Target < 6 GB | Target < $60 | With archival |

---

*OMNIX QUANTUM — Cost & Sustainability Report OMNIX-CSR-2026-001*  
*May 10, 2026 · Internal document · Harold Nunes — Founder*
