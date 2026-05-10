# OMNIX QUANTUM — Backup & Disaster Recovery Runbook

**Document:** OMNIX-OPS-002  
**Date:** May 2026  
**Author:** Harold Nunes — OMNIX QUANTUM LTD  
**Authority:** TIER-1 (ADR-146)  
**Status:** ACTIVE — Required before institutional demo

---

> **Why this document exists:**
> OMNIX QUANTUM now holds 150 ADRs, 10 invariants, 8 ISR remediations, 142,000+
> governance receipts, PQC signing keys, and calibration snapshots accumulated over months.
> This value cannot be reconstructed from memory. A single misconfigured Railway deletion
> or expired subscription would cause permanent institutional data loss.
>
> This runbook defines exactly what to back up, where, and how often.

---

## 1. What Must Be Backed Up — Priority Order

### TIER A — Irrecoverable if Lost

| Asset | Location | Why Critical |
|---|---|---|
| `OMNIX_SIGNING_SECRET_KEY_B64` | Railway secret | Without this, all existing receipts become unverifiable forever |
| `OMNIX_SIGNING_PUBLIC_KEY_B64` | Railway secret | Required for receipt verification endpoint |
| `DATABASE_URL` | Railway secret | Connection to 142,000+ receipts |
| `REDIS_URL` | Railway secret | Anti-replay state |
| PostgreSQL full dump | Railway → pg_dump | All governance receipts, AVM snapshots, client data |

### TIER B — Recoverable but Painful

| Asset | Location | Why Important |
|---|---|---|
| All ADRs (`docs/adr/`) | Git repository | Architecture decisions — loss = institutional amnesia |
| All audit reports (`docs/*.md`) | Git repository | HGA, ISR, FMR, ETD reports — 5 stages of institutional hardening |
| `docs/GOVERNANCE_BASELINE.md` | Git repository | The frozen baseline contract |
| `docs/operations/RC1_*.md` | Git repository | RC-1 verification evidence |
| `omnix_web/dist/` | Git repository | Built frontend — Railway serves from this |

### TIER C — Reconstructible

| Asset | Recovery path |
|---|---|
| Source code | Git repository (Replit + GitHub) |
| `requirements.txt`, `nixpacks.toml` | Reconstructible from code |
| Railway service configuration | Documented in `docs/operations/DEPLOYMENT.md` |

---

## 2. Environment Variables — Full Backup Checklist

**Do this now, before institutional demo.**

Copy every variable from Railway into a secure, encrypted document (e.g. 1Password, Bitwarden, or an encrypted local file). Do not store in plain text.

### stellar-hope service (web API)

```
DATABASE_URL
REDIS_URL
GEMINI_API_KEY
OMNIX_WEB_URL
OMNIX_SIGNING_SECRET_KEY_B64        ← CRITICAL — back up first
OMNIX_SIGNING_PUBLIC_KEY_B64        ← CRITICAL — back up first
PAYLOAD_ENCRYPTION_KEY
OMNIX_ANTI_REPLAY_MODE
SESSION_SECRET
OPENAI_API_KEY
ANTHROPIC_API_KEY
ADMIN_ALLOWED_IPS
DASHBOARD_API_KEY
```

### omnibotgenesis service (Telegram bot)

```
TELEGRAM_BOT_TOKEN
TELEGRAM_ADMIN_USER_ID
DATABASE_URL
REDIS_URL
GEMINI_API_KEY
OPENAI_API_KEY
KRAKEN_API_KEY
KRAKEN_API_SECRET
COINBASE_API_KEY
COINBASE_PASSPHRASE
COINBASE_SECRET
PAPER_MODE
TRADING_MODE
TRADING_PROFILE
OMNIX_SIGNING_SECRET_KEY_B64
OMNIX_SIGNING_PUBLIC_KEY_B64
```

---

## 3. PostgreSQL Backup — Procedure

### 3.1 Pre-Demo Snapshot (Manual)

Run this before any institutional demo:

```bash
# Get DATABASE_URL from Railway dashboard or Replit secrets
export DATABASE_URL="postgresql://..."

# Full dump — all tables, all data
pg_dump "$DATABASE_URL" \
  --format=custom \
  --file="omnix_backup_$(date +%Y%m%d_%H%M%S).dump" \
  --verbose

# Verify the dump
pg_restore --list omnix_backup_*.dump | head -20
```

Store the `.dump` file in:
- Local encrypted drive
- Google Drive (encrypted zip)
- AWS S3 bucket (if available)

### 3.2 What the Dump Contains

| Table | Rows (approx.) | Criticality |
|---|---|---|
| `decision_receipts` | 142,000+ | CRITICAL — governance history |
| `avm_calibration_snapshots` | 11 | HIGH — AVM baselines |
| `execution_receipts` | variable | HIGH — execution integrity |
| `udcl_control_receipts` | variable | HIGH — unified control layer |
| `b2b_clients` | variable | HIGH — client registry |
| `client_thresholds` | variable | HIGH — per-client config |
| `breach_events` | variable | MEDIUM |
| `risk_assessments` | variable | MEDIUM |
| `anomaly_recommendations` | variable | MEDIUM |
| `book_leads` | variable | LOW |

### 3.3 Restore Procedure

```bash
# Create a new database first (Railway → Add PostgreSQL)
export NEW_DATABASE_URL="postgresql://..."

# Restore
pg_restore \
  --dbname="$NEW_DATABASE_URL" \
  --format=custom \
  --verbose \
  omnix_backup_YYYYMMDD_HHMMSS.dump
```

---

## 4. Git Repository Backup

The git repository contains all source code, ADRs, and documentation.

### 4.1 Verify the repo is pushed

```bash
git --no-optional-locks log --oneline -5
git --no-optional-locks remote -v
```

### 4.2 Create a local archive

```bash
# Full git bundle — includes all branches and history
git bundle create omnix_quantum_$(date +%Y%m%d).bundle --all

# Verify the bundle
git bundle verify omnix_quantum_*.bundle
```

Store this `.bundle` file alongside the DB dump.

### 4.3 Critical directories to confirm exist in the repo

```
docs/adr/                        ← 150 ADRs
docs/GOVERNANCE_BASELINE.md      ← Frozen baseline
docs/operations/RC1_*.md         ← RC-1 evidence
docs/INSTITUTIONAL_*.md          ← ISR audit report
omnix_web/dist/                  ← Built frontend
```

---

## 5. PQC Key Backup — Special Procedure

The Dilithium-3 signing key (`OMNIX_SIGNING_SECRET_KEY_B64`) deserves its own section
because losing it means every existing receipt becomes permanently unverifiable.

### 5.1 Backup the key

```bash
# If you have access to the Railway secret value:
# 1. Go to Railway → stellar-hope → Variables
# 2. Find OMNIX_SIGNING_SECRET_KEY_B64
# 3. Copy the value
# 4. Store in password manager under "OMNIX PQC Signing Key — DO NOT LOSE"

# Also back up the public key (safe to store plainly):
# OMNIX_SIGNING_PUBLIC_KEY_B64
```

### 5.2 Verify the key is the same in both services

The same signing key must be in both `stellar-hope` and `omnibotgenesis`.
If they differ, receipts from the bot cannot be verified by the web endpoint.

### 5.3 Key rotation (future)

Key rotation is a Migration Plan event (see `docs/GOVERNANCE_BASELINE.md` §3).
It requires:
1. Filing an ADR
2. A re-verification strategy for historical receipts
3. A new Production Verification Report (`OMNIX-PVR-2026-002`)

---

## 6. Backup Schedule

| Backup | Frequency | Trigger |
|---|---|---|
| PostgreSQL `pg_dump` | Monthly + before every institutional demo | Manual |
| Git bundle | After every major release or ADR batch | Manual |
| Railway env vars export | After any env var change | Manual — paste to password manager |
| PQC key verification | Quarterly | Confirm `pqc_mode: dilithium3-persistent` in `/api/health` |

---

## 7. Disaster Recovery Scenarios

### Scenario A — Railway account suspended

1. Restore PostgreSQL from latest `pg_dump` to a new provider (Supabase, Neon, Render)
2. Update `DATABASE_URL` in new deployment
3. Deploy from Git bundle to Render/Fly.io/new Railway account
4. Restore all env vars from password manager
5. Verify `GET /api/health` → all subsystems UP

**RTO (Recovery Time Objective):** ~4 hours with this runbook  
**RPO (Recovery Point Objective):** Data since last `pg_dump`

### Scenario B — Signing key lost

**Impact:** All existing receipts permanently unverifiable — institutional trust compromised.

Prevention: Back up the key before this ever happens (Section 5.1).  
Recovery: None — the key cannot be recovered or regenerated if lost.

### Scenario C — Database corrupted or deleted

1. Run `POST /api/health/reconcile-wal` immediately to flush any in-memory WAL
2. Restore from latest `pg_dump` to a fresh DB
3. Update `DATABASE_URL` if the connection string changed
4. Verify `decision_receipts` row count matches pre-corruption count

### Scenario D — Replit account lost / project deleted

1. Restore from Git bundle: `git clone omnix_quantum_YYYYMMDD.bundle`
2. Reconfigure Railway services as per `docs/operations/DEPLOYMENT.md`
3. Restore env vars from password manager
4. Redeploy

---

## 8. Self-Verifying Receipts — Key Finding from OMNIX-DRT-2026-001

Discovered during the May 10, 2026 DR test:

**OMNIX receipts are self-verifying.** Each receipt in `decision_receipts` embeds the
public key that signed it in the `public_key` field. This means:

1. Verification does not require external key registry access
2. Receipts remain verifiable even if the signing key is rotated in the future
3. The backup is cryptographically self-sufficient — no external dependency

**Correct verification approach:**

```python
from pqc.sign import dilithium3
import base64

# Use the public key EMBEDDED IN THE RECEIPT, not an external key
pk_bytes  = base64.b64decode(receipt['public_key'])
sig_bytes = base64.b64decode(receipt['signature'])
message   = receipt['content_hash'].encode('utf-8')

# dilithium3.verify raises ValueError on failure, returns None on success
dilithium3.verify(sig_bytes, message, pk_bytes)
```

**Key epochs found in production (as of May 10, 2026):**

| Key fingerprint | Receipts | Period |
|---|---|---|
| `85d5b178afeb01ce` | 174 (of first 500) | Primary persistent epoch |
| `754f3e2d4ac4ba13` | 167 | Second persistent epoch |
| `6b01c588f5cefdb5` | 132 | Third persistent epoch |
| *(8 others)* | 27 | Earlier epochs (pre-persistence) |

All 11 epochs verified correctly during OMNIX-DRT-2026-001.

**Critical action:** Back up `OMNIX_SIGNING_SECRET_KEY_B64` from Railway to a password
manager. Without it, new receipts cannot be signed with the established key.
Old receipts remain verifiable via their embedded public key regardless.

---

## 9. Verification After Any Restore

After any backup restore, run the full verification suite:

```bash
# 1. Health check — all 6 subsystems must be UP
curl "https://omnixquantum.net/api/health?alerts=false" | python3 -m json.tool

# 2. PQC mode must be dilithium3-persistent
# Look for: "pqc_mode": "dilithium3-persistent"

# 3. WAL must be clean
# Look for: "wal_pending": 0

# 4. Receipt count sanity check
# Look for: "decision_receipts accessible — N rows"
# N should be >= pre-restore count
```

A successful restore is documented by creating a new Production Verification Report
(`OMNIX-PVR-2026-00N`) following the template in `docs/operations/RC1_PRODUCTION_VERIFICATION.md`.

---

*OMNIX QUANTUM — Backup & Disaster Recovery Runbook OMNIX-OPS-002*  
*May 2026 · omnixquantum.net*  
*Authority: Harold Nunes — TIER-1 (ADR-146)*
