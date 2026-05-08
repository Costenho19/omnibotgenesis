# ADR-146 — Runtime Authority Matrix: Who Has Final Authority Over What

| Field | Value |
|---|---|
| **Status** | Accepted — Implemented May 2026 |
| **Date** | 2026-05-08 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | Cross-cutting — applies to all OMNIX governance modules |
| **Extends** | ADR-089 (RBAC) · ADR-116 (Fail-Closed) · ADR-142 (BCE) · ADR-144 (AMG) |
| **Full Document** | `docs/AUTHORITY_MATRIX.md` — the canonical runtime authority reference |

---

## 1. Problem Statement

OMNIX now has 14+ automated governance modules: AVM, MCM, AMG, BCE, CAG, CBG, SPG, TIE, SBE, CTAG, and others. Each module can block, hold, recalibrate, or suspend decisions autonomously.

**The gap**: there was no single, explicit document answering:

> *"When this system starts auto-modifying itself — who has final authority over rollback? Emergency freeze? Override? Policy update? Domain quarantine?"*

This question is asked by:
- **Boards and executive committees**: governance accountability
- **Institutional auditors**: authority trail for regulatory compliance
- **Regulators (ADGM, CBUAE, FCA, SEC)**: human-in-the-loop requirements
- **Enterprise clients (GCC, EU)**: vendor due diligence

Without a clear answer, OMNIX governance looks like a black box that self-governs without accountability — the exact problem OMNIX is designed to solve for others.

---

## 2. Decision

Publish an explicit, versioned **Runtime Authority Matrix** (`docs/AUTHORITY_MATRIX.md`) defining:

1. The four authority tiers (Platform Owner → System Automated → Client Operator → External Auditor)
2. Every governance action and who holds final authority over it
3. Emergency protocols: freeze, unfreeze, override, rollback, quarantine
4. What the system can do without human approval vs. what requires it
5. What is permanently immutable (cannot be changed by anyone)

The matrix is versioned with every ADR revision and referenced from `ARCHITECTURE.md`.

---

## 3. Authority Tier Definitions

### Tier 1 — Platform Owner (Harold Nunes, OMNIX QUANTUM LTD)

Final authority on all architectural decisions, parameter boundaries, and deployment approvals. No automated system can override a Tier 1 decision. The platform owner is the only entity that can:
- Approve architectural changes (new ADRs, governance rule modifications)
- Authorize production deployments to Railway
- Override any automated decision in production (no overrides exercised as of May 2026)
- Dissolve or re-scope any automated authority tier

**Auth method**: Manual — version control + Railway deployment + Telegram admin channel

### Tier 2 — System Automated (OMNIX Governance Modules)

Pre-authorized automated authority within bounded parameters defined by Tier 1. The system can:
- Block, hold, or approve individual governance decisions (no bounds)
- Recalibrate AVM baselines within ±80% cap and 72h interval
- Tighten thresholds within AMG bounds (30% cumulative drift from genesis)
- Suspend a domain for 48h via CAG cool-down
- Activate Breach Containment (BCE) when compromise indicators are detected
- Issue PQC-signed receipts for every decision

**Hard limits on Tier 2 automated authority**:
- Cannot exceed cumulative drift cap (AMG, ADR-144)
- Cannot modify genesis snapshot (permanent anchor)
- Cannot release BCE containment (requires Tier 1)
- Cannot approve a threshold change > 10% without Tier 1 via Telegram

### Tier 3 — Client Operator (B2B Enterprise Clients)

Access via API key with RBAC (ADR-089). Three permission levels:
- **READ**: Query receipts, verify signatures, analytics
- **WRITE**: Submit governance evaluation requests
- **ADMIN**: Client management, key rotation, raw audit logs (OMNIX Operators only)

Client operators cannot modify governance parameters, override decisions, or access other clients' data.

### Tier 4 — External Auditor (Read-Only)

Can verify any receipt independently via public endpoints and `omnix_verify.py`. No write authority. Read access is permanently open — no OMNIX account required for receipt verification.

---

## 4. Authority Matrix (Summary)

See `docs/AUTHORITY_MATRIX.md` for the full table with 25+ governance actions.

| Action | Tier 1 (Human) | Tier 2 (System) | Tier 3 (Client) | Tier 4 (Auditor) |
|---|---|---|---|---|
| Block a governance decision | ✅ Final | ✅ Autonomous | ❌ | ❌ |
| Emergency freeze (BCE) | ✅ Final | ✅ Auto-activate | ❌ | ❌ |
| Release BCE freeze | ✅ **Only Tier 1** | ❌ | ❌ | ❌ |
| Threshold modification > 10% | ✅ Approval required | 🔄 Gate → Tier 1 | ❌ | ❌ |
| Threshold modification ≤ 10% | ✅ Override any time | ✅ Auto with receipt | ❌ | ❌ |
| Domain quarantine (48h) | ✅ Final | ✅ CAG autonomous | ❌ | ❌ |
| Rollback thresholds | ✅ Manual any time | ✅ Auto T+24h check | ❌ | ❌ |
| Architectural change (ADR) | ✅ **Only Tier 1** | ❌ | ❌ | ❌ |
| Receipt issuance | ✅ Via deployment | ✅ Per decision | ❌ ✅ Trigger | ✅ Verify |
| Genesis snapshot modification | ✅ **Only Tier 1** | ❌ **Immutable** | ❌ | ❌ |
| Verify any receipt | ✅ | ✅ | ✅ | ✅ (public) |

---

## 5. Emergency Protocol

### 5.1 Emergency Freeze
**Who can activate**: Tier 1 (manual) or Tier 2 automated (BCE compromise detection)  
**Effect**: All governance decisions return BLOCKED immediately. No execution possible.  
**Duration**: Until explicitly released  
**Release authority**: **Tier 1 only** — `BreachContainmentEngine.release_containment(operator_id, reason)`  
**Audit trail**: Every activation and release generates a `breach_containment_events` DB record

### 5.2 Emergency Rollback
**Who can activate**: Tier 1 (manual any time) or Tier 2 automated (AMG T+24h performance check)  
**Effect**: Previous AVM snapshot restored; `AMG_ROLLBACK` trust flag on all subsequent receipts  
**Scope**: Threshold rollback only — genesis snapshot is immutable  
**Audit trail**: `avm_modification_registry` with `status=ROLLED_BACK`

### 5.3 Domain Quarantine
**Who can activate**: Tier 1 (manual) or CAG autonomous (volatility threshold)  
**Effect**: Domain suspended — all decisions BLOCKED for 48h cool-down  
**Release**: Automatic after 48h if CAG conditions normalize, or Tier 1 manual override  
**Audit trail**: CAG evaluation log + BCE event if coincident with breach

### 5.4 Override Authority
**Who can override**: **Tier 1 only**  
**Scope**: Any automated decision in production  
**Current status**: Zero production overrides exercised (as of May 2026)  
**Design principle**: The system is designed to need zero overrides. Override capability exists but its exercise would be auditable and exceptional.

### 5.5 Policy Update
**Who can approve**: **Tier 1 only**  
**Process**: New ADR → code change → production deployment → governance receipt  
**Immutable after deployment**: All receipts issued under previous policy remain valid — receipts are backward-compatible

---

## 6. Immutability Guarantees

These properties cannot be changed by any party — including Tier 1:

| Property | Why Immutable |
|---|---|
| Issued governance receipts | PQC-signed at issuance — hash tamper-evident |
| Genesis AVM snapshot | Permanent anchor for cumulative drift measurement (ADR-144) |
| Historical receipt content | Once in `decision_receipts` table — no UPDATE, no DELETE path |
| Transparency chain entries | Append-only WAL chain (ADR-Evidence) |

---

## 7. RBAC Summary (ADR-089)

| Role | Permissions |
|---|---|
| `omnix_admin` | Full: read + write + client management + raw audit logs |
| `enterprise_client` | Write: submit evaluation requests; Read: own receipts |
| `auditor` | Read: all receipts, verify signatures, analytics |
| `public` | Read: any receipt via `/api/public/verify/<id>`; no auth required |

---

## 8. Regulatory Alignment

| Framework | Requirement | OMNIX Implementation |
|---|---|---|
| EU AI Act Art. 9 | Human oversight for high-risk AI | Tier 1 retains final override authority |
| EU AI Act Art. 14 | Human control measures | AMG approval gate > 10% threshold |
| NIST AI RMF GV-1.1 | AI governance policies | This ADR + AUTHORITY_MATRIX.md |
| NIST AI RMF MS-2.5 | Incident response | BCE emergency freeze protocol |
| ISO/IEC 42001 | AI management system | BCE + AMG + MCM + this matrix |
| FATF Recommendation 16 | Wire transfer monitoring | CP-9 AML + mandatory SAR filing |
| UAE CBUAE Reg. | Consumer protection | Tier 3 RBAC + receipt verifiability |

---

## 9. Related

| Document | Relation |
|---|---|
| `docs/AUTHORITY_MATRIX.md` | Full 25-action authority table — canonical reference |
| ADR-089 — RBAC Enforcement | Permission levels for Tier 3 (B2B clients) |
| ADR-116 — Fail-Closed Policy | Automated block authority (Tier 2) |
| ADR-142 — Breach Containment | Emergency freeze mechanism |
| ADR-144 — Auto-Modification Guard | Limits on Tier 2 threshold modification authority |
| ADR-145 — Governance Replay Engine | Scenario approval authority (Tier 1) |
