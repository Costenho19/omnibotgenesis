# OMNIX — Runtime Authority Matrix

**Version**: 1.0 — May 2026  
**ADR**: ADR-146  
**Status**: Active — Canonical Reference  
**Author**: Harold Nunes — OMNIX QUANTUM LTD  

> This document answers the question every institutional auditor, regulator, and
> enterprise client eventually asks:
>
> *"When this system starts auto-modifying itself — who has final authority over rollback?
> Emergency freeze? Override? Policy update? Domain quarantine?"*

---

## 1. Authority Tiers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      OMNIX RUNTIME AUTHORITY HIERARCHY                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  TIER 1 — PLATFORM OWNER (Harold Nunes, OMNIX QUANTUM LTD)                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Final authority on all decisions, parameters, deployments, overrides │    │
│  │ The only entity that can release BCE freeze or modify genesis anchor  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│           │                                                                   │
│           ▼                                                                   │
│  TIER 2 — SYSTEM AUTOMATED (OMNIX Governance Modules)                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Pre-authorized autonomous actions within Tier 1-defined bounds        │    │
│  │ AVM · MCM · AMG · BCE · CAG · CBG · SPG · TIE · SBE · CTAG          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│           │                                                                   │
│           ▼                                                                   │
│  TIER 3 — CLIENT OPERATOR (B2B Enterprise Clients)                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ API-key authenticated · RBAC enforced · READ / WRITE / ADMIN roles    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│           │                                                                   │
│           ▼                                                                   │
│  TIER 4 — EXTERNAL AUDITOR (Read-Only, Public)                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Receipt verification · No auth required · Permanently open access     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Full Authority Matrix

### 2.1 Decision Governance Actions

| Action | Tier 1 (Human) | Tier 2 (System) | Tier 3 (Client) | Tier 4 (Auditor) | ADR |
|---|---|---|---|---|---|
| Issue BLOCKED verdict | ✅ Manual override | ✅ **Autonomous** | ❌ | ❌ | ADR-116 |
| Issue HOLD verdict | ✅ Manual override | ✅ **Autonomous** | ❌ | ❌ | ADR-116 |
| Issue APPROVED verdict | ✅ Manual override | ✅ **Autonomous** | ❌ | ❌ | ADR-116 |
| Issue NARROW verdict | ✅ Manual override | ✅ **Autonomous** | ❌ | ❌ | ADR-139 |
| Issue QUARANTINE verdict | ✅ Manual override | ✅ **Autonomous** | ❌ | ❌ | ADR-139 |
| Issue REBOUND verdict | ✅ Manual override | ✅ **Autonomous** | ❌ | ❌ | ADR-139 |
| Verify any receipt | ✅ | ✅ | ✅ | ✅ **Public** | ADR-085 |
| Trigger governance evaluation | ✅ | ✅ Auto (trading cycle) | ✅ Via API | ❌ | ADR-028 |

### 2.2 Threshold & Parameter Modification

| Action | Tier 1 (Human) | Tier 2 (System) | Tier 3 (Client) | Tier 4 | ADR |
|---|---|---|---|---|---|
| Modify `checkpoint_thresholds` ≤ 10% delta | ✅ Any time | ✅ Auto + receipt | ❌ | ❌ | ADR-144 |
| Modify `checkpoint_thresholds` > 10% delta | ✅ **Approval required** | 🔄 Gate → Tier 1 Telegram | ❌ | ❌ | ADR-144 |
| Modify genesis AVM snapshot | ✅ **Only Tier 1** | ❌ **Immutable** | ❌ | ❌ | ADR-144 |
| Recalibrate AVM baseline (≤ 80% cap, 72h interval) | ✅ Any time | ✅ Autonomous | ❌ | ❌ | ADR-120 |
| Force AVM recalibration (MCM CRITICAL) | ✅ Any time | ✅ Autonomous | ❌ | ❌ | ADR-118 |
| Tighten thresholds 10% (MCM TIGHTEN) | ✅ Any time | ✅ Via AMG guard | ❌ | ❌ | ADR-118 |
| Override cumulative drift cap (> 30%) | ✅ **Only Tier 1** | ❌ Hard limit | ❌ | ❌ | ADR-144 |
| Set `AVM_AUTO_APPROVE=true` | ✅ **Only Tier 1** | ❌ | ❌ | ❌ | ADR-144 |

### 2.3 Emergency Controls

| Action | Tier 1 (Human) | Tier 2 (System) | Tier 3 (Client) | Tier 4 | ADR |
|---|---|---|---|---|---|
| **Emergency freeze** (BCE activate) | ✅ Any time | ✅ Auto (compromise detection) | ❌ | ❌ | ADR-142 |
| **Release BCE freeze** | ✅ **Only Tier 1** | ❌ | ❌ | ❌ | ADR-142 |
| **Emergency rollback** (AVM thresholds) | ✅ Any time | ✅ Auto T+24h check | ❌ | ❌ | ADR-144 |
| **Domain quarantine** (48h suspend) | ✅ Any time | ✅ CAG auto (vol > 150%) | ❌ | ❌ | ADR-050 |
| **Release domain quarantine early** | ✅ **Only Tier 1** | ❌ (auto-releases T+48h) | ❌ | ❌ | ADR-050 |
| **Override any automated decision** | ✅ **Only Tier 1** | ❌ | ❌ | ❌ | ADR-116 |
| Trigger MCM alert manually | ✅ Any time | ✅ Auto on degradation | ❌ | ❌ | ADR-117 |
| Force anti-loop reset | ✅ **Only Tier 1** | ❌ | ❌ | ❌ | ADR-144 |

### 2.4 Deployment & Architecture

| Action | Tier 1 (Human) | Tier 2 (System) | Tier 3 (Client) | Tier 4 | ADR |
|---|---|---|---|---|---|
| Create new ADR | ✅ **Only Tier 1** | ❌ | ❌ | ❌ | All ADRs |
| Approve architecture change | ✅ **Only Tier 1** | ❌ | ❌ | ❌ | All ADRs |
| Authorize production deployment | ✅ **Only Tier 1** | ❌ | ❌ | ❌ | Ops |
| Run database migrations | ✅ Manual (Railway) | ❌ | ❌ | ❌ | Ops |
| Rotate API keys / PQC keys | ✅ Manual | ❌ | ✅ Own keys | ❌ | ADR-089 |
| Add new crisis scenario (Replay Engine) | ✅ **Only Tier 1** | ❌ | ❌ | ❌ | ADR-145 |

### 2.5 Client & Access Management

| Action | Tier 1 (Human) | Tier 2 (System) | Tier 3 (Client) | Tier 4 | ADR |
|---|---|---|---|---|---|
| Provision new B2B client API key | ✅ `provision_b2b_client.py` | ❌ | ❌ | ❌ | ADR-089 |
| Revoke client API key | ✅ Any time | ✅ Auto (quota exceeded, AML) | ❌ | ❌ | ADR-089 |
| Ban Telegram user | ✅ `/ban` command | ✅ Auto (injection attempts ≥ 3) | ❌ | ❌ | ADR-083 |
| Unban Telegram user | ✅ Admin command | ❌ | ❌ | ❌ | ADR-083 |
| Set per-client quota | ✅ Only ADMIN role | ❌ | ✅ Own client only (ADMIN) | ❌ | ADR-089 |
| Access other client's data | ✅ Admin only | ❌ | ❌ | ❌ | ADR-089 |

### 2.6 Receipt & Evidence Immutability

| Property | Modifiable by Tier 1 | Modifiable by Tier 2 | Notes |
|---|---|---|---|
| Issued governance receipt content | ❌ **Immutable** | ❌ | PQC-signed at issuance |
| Historical receipt records in DB | ❌ **Immutable** | ❌ | No UPDATE/DELETE path |
| Genesis AVM snapshot | ❌ **Immutable** | ❌ | Permanent drift anchor |
| Transparency chain (WAL) | ❌ **Immutable** | ❌ | Append-only |
| Replay receipts (ADR-145) | ❌ **Immutable** | ❌ | SHA-256 sealed at generation |
| Issued scope authorization records | ❌ **Immutable** | ❌ | PQC-signed at issuance — ADR-147 |

### 2.7 Scope Authorization Actions (ADR-147)

> Answers: *"Was the scope itself defensible, who authorized it, and does it remain valid as operational context shifts?"*

| Action | Tier 1 (Human) | Tier 2 (System) | Tier 3 (Client) | Tier 4 (Auditor) | ADR |
|---|---|---|---|---|---|
| Issue scope authorization | ✅ **Only Tier 1** | ❌ | ❌ | ❌ | ADR-147 |
| Flag scope for reapproval (context drift) | ✅ Any time | ✅ **Autonomous** (drift > threshold) | ❌ | ❌ | ADR-147 |
| Reauthorize scope after reapproval | ✅ **Only Tier 1** | ❌ | ❌ | ❌ | ADR-147 |
| Revoke scope (hard, permanent) | ✅ **Only Tier 1** | ❌ | ❌ | ❌ | ADR-147 |
| Read active scope for own domain | ✅ | ✅ | ✅ Own domain | ✅ | ADR-147 |
| Read full scope history | ✅ | ✅ | ❌ | ✅ | ADR-147 |
| Verify scope PQC signature | ✅ | ✅ | ✅ | ✅ **Public** | ADR-147 |

**Scope status lifecycle:**
```
ACTIVE → REAPPROVAL_REQUIRED  (auto: context drift > threshold)
       → SUPERSEDED            (Tier 1: reauthorize())
       → REVOKED               (Tier 1 only: permanent)
REAPPROVAL_REQUIRED → ACTIVE  (Tier 1: reauthorize() → new ACTIVE scope issued)
```

**Trust flags on governance receipts while scope reapproval is pending:**
```
trust_flags.scope_reapproval_pending = true
```
Existing decisions continue — no retroactive revocation. New scope required for clean receipts.

---

## 3. Emergency Protocol — Step-by-Step

### 3.1 Emergency Freeze (BCE Activation)

```
TRIGGER (either):
  A) Tier 1 manual: BCE.activate_containment(operator_id, "manual_trigger", reason)
  B) Tier 2 auto:   BCE.assess_environment() detects timing anomaly | hash mismatch
                    | process anomaly | repeated auth failures

EFFECT:
  All governance decisions → BLOCKED immediately
  All receipts carry trust_flag: CONTAINMENT_ACTIVE

AUDIT TRAIL:
  breach_containment_events table
  BreachEvent.to_dict() logged with operator_id + reason + timestamp

RELEASE (TIER 1 ONLY):
  BCE.release_containment(operator_id, reason)
  Verified against TELEGRAM_ADMIN_USER_ID before execution
```

### 3.2 Emergency Rollback (AVM Thresholds)

```
TRIGGER (either):
  A) Tier 1 manual: rollback_snapshot(domain, db_url, operator_id)
  B) Tier 2 auto:   AMG.check_rollback_condition() at T+24h after deployment
                    Condition: block_rate degraded AND performance below baseline

EFFECT:
  checkpoint_thresholds restored to previous snapshot
  avm_modification_registry: status = ROLLED_BACK
  All subsequent receipts: trust_flag = AMG_ROLLBACK

AUDIT TRAIL:
  avm_modification_registry (permanent)
  diff_proof before/after stored
  Telegram notification to TELEGRAM_ADMIN_USER_ID
```

### 3.3 Domain Quarantine (48h Suspension)

```
TRIGGER (either):
  A) Tier 1 manual: domain_quarantine(domain, reason)
  B) Tier 2 auto:   CAG blocks when volatility_1h_annualized > 1.50 (150%)

EFFECT:
  All decisions for that domain → BLOCKED for 48h
  Trust flag: DOMAIN_SUSPENDED_48H

RELEASE:
  A) Automatic: After 48h if CAG conditions normalize
  B) Tier 1 manual early release at any time

AUDIT TRAIL:
  CAG evaluation log per domain
  BCE event if coincident with breach indicator
```

### 3.4 Override (Tier 1 Only)

```
WHO: Harold Nunes (TELEGRAM_ADMIN_USER_ID, verified at runtime)

HOW: Direct code change + Railway deployment OR Telegram /admin override command

CURRENT STATUS: Zero production overrides exercised (May 2026)

DESIGN PRINCIPLE:
  The system is designed so overrides are never necessary.
  Override capability exists but its exercise is:
  - Fully auditable (all changes version-controlled)
  - Exceptional (not part of normal operation)
  - Documented (creates an ADR amendment)
```

---

## 4. What the System Can Do Without Human Approval

These actions happen autonomously (Tier 2) with full audit trail but no prior human sign-off:

| Action | Module | Bound |
|---|---|---|
| Block any governance decision | All checkpoint modules | None — fail-closed always |
| Approve any governance decision | All checkpoint modules | All 11 checkpoints must pass |
| Recalibrate AVM baseline | AVM (ADR-120) | ≤ 80% delta, ≥ 72h interval |
| Tighten thresholds 10% | MCM → AMG (ADR-118, 144) | AMG 6-invariant check |
| Auto-rollback thresholds | AMG (ADR-144) | T+24h performance degradation |
| Activate BCE freeze | BCE (ADR-142) | Compromise indicators confirmed |
| Domain 48h suspension | CAG (ADR-050) | Vol > 150% annualized |
| Issue PQC-signed receipts | Receipt layer (ADR-096) | Per decision — always |
| Block MCM re-trigger (anti-loop) | AMG (ADR-144) | ≥ 2 remediations in 24h |
| Flag AUTO_MODIFIED trust | AMG (ADR-144) | Any auto-threshold change |
| Ban user after 3 injection attempts | Bot Security (ADR-083) | Threshold: 3 attempts |
| Revoke client key at quota | RBAC (ADR-089) | Quota defined at provisioning |

---

## 5. What Requires Human Approval (Tier 1)

These actions are **blocked until Tier 1 explicitly authorizes**:

| Action | Block Mechanism | Auth Channel |
|---|---|---|
| Threshold change > 10% | AMG approval gate | Telegram message to admin |
| Release BCE emergency freeze | BCE release check | Direct code call with operator_id |
| New ADR / architecture change | Manual only | GitHub commit + Railway deploy |
| New B2B client provisioning | `provision_b2b_client.py` | Manual execution |
| New crisis scenario (Replay Engine) | Data object PR | Manual code change |
| Genesis snapshot modification | Hard immutability | Not possible by design |

---

## 6. Accountability Chain

```
Every governance decision traces:
  Signal Input
    → Checkpoint Evaluation (which CP failed, score, threshold)
      → Decision (APPROVED | BLOCKED | HOLD | NARROW | QUARANTINE | REBOUND)
        → PQC-Signed Receipt (Dilithium-3 / SHA-256)
          → Transparency Chain Entry (WAL append-only)
            → Independent Verification (public, no auth required)

Every parameter change traces:
  Trigger (AVM | MCM | manual)
    → AMG.run_guard() (6 invariant checks)
      → avm_modification_registry record (permanent)
        → Diff proof (AMG-DIFF-v1:{sha256}:{algo})
          → Telegram notification (if approval gate hit)
            → Rollback check at T+24h
```

---

## 7. Regulatory Alignment

| Framework | Requirement | OMNIX Implementation |
|---|---|---|
| **EU AI Act Art. 14** | Human oversight measures for high-risk AI | Tier 1 retains final override; AMG gate > 10%; BCE requires Tier 1 release |
| **EU AI Act Art. 9** | Risk management system | BCE + AMG + MCM + this matrix |
| **NIST AI RMF GV-1.1** | AI governance policies documented | This document + ADR-146 |
| **NIST AI RMF MS-2.5** | Incident response plan | BCE protocol §3.1 above |
| **ISO/IEC 42001 §6.1** | AI risk management | Full authority matrix with accountability chain |
| **FATF R.16** | Wire transfer due diligence | CP-9 AML + mandatory SAR + Tier 1 override audit |
| **UAE CBUAE** | Consumer protection, AI governance | RBAC + receipt verifiability + Tier 4 public access |
| **ADGM Digital Assets Reg.** | Governance trail for digital asset decisions | PQC-signed receipts + transparency chain |
| **NIS2 Directive** | Critical infrastructure AI incident handling | BCE emergency freeze + release protocol |
| **MiCA Art. 30** | Stablecoin reserve governance | Stablecoin vertical + CAG + AMG |

---

## 8. Versioning

This matrix is versioned with every ADR update. Changes require a Tier 1 decision (new ADR or amendment).

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-05-08 | Initial publication — ADR-146 |

---

*OMNIX QUANTUM — Decision Governance Infrastructure*  
*ADR-146 · Runtime Authority Matrix v1.0*  
*omnixquantum.net*
