# OMNIX — PQC Assurance Tier Demo Guide

**Classification**: Technical Due Diligence — Internal Use  
**Last Updated**: March 2026  
**References**: ADR-022, ADR-031  
**For**: Technical evaluators, institutional partners, security-focused due diligence

---

## Purpose

This document answers the following technical evaluation question:

> "You claim ML-DSA-65 (Level 3) is your baseline. Can you demonstrate Level 5 signing in action? And is the architecture actually configurable or is that just marketing?"

The answer is a runnable script. Both Dilithium-3 (ML-DSA-65) and Dilithium-5 (ML-DSA-87) are operationally available. The tier is selected via a deployment environment variable. No architectural changes required.

---

## How to Run

```bash
# Clone / access the repository, then:

# 1. Show Level 3 in action (enterprise baseline, current production)
python scripts/pqc_level_demo.py --level 3

# 2. Show Level 5 in action (high-assurance configuration)
python scripts/pqc_level_demo.py --level 5

# 3. Side-by-side comparison (recommended for due diligence review)
python scripts/pqc_level_demo.py --compare

# 4. JSON output (for programmatic verification)
python scripts/pqc_level_demo.py --compare --json
```

No environment setup required beyond Python 3.11+ and `pypqc` (already installed).

---

## Expected Output — Level 3 (ML-DSA-65)

```
Level 3 — Dilithium-3 (ML-DSA-65)  [Enterprise Baseline]
------------------------------------------------------------------------
STATUS           : OPERATIONAL
Security Level   : ~192-bit classical security equivalent
Use Case         : Capital-sensitive environments, institutional governance, enterprise deployments

KEY GENERATION
  Public Key     : 1,952 bytes
  Secret Key     : 4,032 bytes
  Time           : ~0.3 ms

GOVERNANCE PAYLOAD SIGNED
  Decision       : BLOCK
  Symbol         : BTC/USD
  Checkpoint     : 6/6
  Signature Size : 3,309 bytes
  Sign Time      : ~0.6 ms

VERIFICATION
  Original Payload   : PASS
  Tampered Payload   : REJECTED (correct)
  Verify Time        : ~0.2 ms
```

---

## Expected Output — Level 5 (ML-DSA-87)

```
Level 5 — Dilithium-5 (ML-DSA-87)  [High-Assurance]
------------------------------------------------------------------------
STATUS           : OPERATIONAL
Security Level   : ~256-bit classical security equivalent
Use Case         : National-grade deployments, regulated environments, maximum assurance

KEY GENERATION
  Public Key     : 2,592 bytes
  Secret Key     : 4,896 bytes
  Time           : ~0.5 ms

GOVERNANCE PAYLOAD SIGNED
  Decision       : BLOCK
  Symbol         : BTC/USD
  Checkpoint     : 6/6
  Signature Size : 4,627 bytes
  Sign Time      : ~0.9 ms

VERIFICATION
  Original Payload   : PASS
  Tampered Payload   : REJECTED (correct)
  Verify Time        : ~0.3 ms
```

---

## Side-by-Side Comparison

| Metric | Level 3 (ML-DSA-65) | Level 5 (ML-DSA-87) |
|--------|---------------------|---------------------|
| Label | Enterprise Baseline | High-Assurance |
| Security | ~192-bit classical equiv. | ~256-bit classical equiv. |
| Public Key Size | 1,952 bytes | 2,592 bytes |
| Secret Key Size | 4,032 bytes | 4,896 bytes |
| Signature Size | 3,309 bytes | 4,627 bytes (+39.8%) |
| Keygen Time | ~0.3 ms | ~0.5 ms |
| Sign Time | ~0.6 ms | ~0.9 ms |
| Verify Time | ~0.2 ms | ~0.3 ms |
| Production Status | Active (default) | Available via config |
| Activate With | `PQC_SIGNING_LEVEL=3` | `PQC_SIGNING_LEVEL=5` |

---

## What This Proves

**1. Both algorithms are operationally available — not roadmap claims.**

The `pypqc` library ships with `dilithium3` and `dilithium5` modules. Both are confirmed functional: key generation, signing, and verification all pass. Tamper detection rejects modified payloads correctly in both tiers.

**2. The architecture is genuinely configurable via deployment environment.**

`omnix_core/security/pqc_config.py` reads `PQC_SIGNING_LEVEL` at service startup and selects the appropriate Dilithium variant. No code changes are required to move between tiers. The selection is:
- Fail-closed: invalid or missing values default to Level 3
- Auditable: the active tier is logged at startup and exposed via `get_security_info()`
- Consistent: the same governance receipt structure, verification API, and caller interface work at both levels

**3. Level 3 is the correct production choice — not a compromise.**

NIST Level 3 (~AES-192 equivalent) is designed for enterprise-grade institutional deployments. Level 5 (~AES-256 equivalent) targets national-grade and state-secrecy environments. Choosing Level 3 for capital-sensitive governance is a deliberate threat-model decision, not a cost cut. The +39.8% signature overhead of Level 5 is material at 700,000+ daily governance evaluations.

---

## How to Change Tier in Production (Railway Deployment)

```
1. Go to Railway project dashboard
2. Navigate to: Variables → Add New Variable
3. Set: PQC_SIGNING_LEVEL = 5
4. Trigger a redeployment (or Railway auto-deploys on variable change)
5. Verify: service logs will show "PQC Signing Level: 5 — ML-DSA-87 (Dilithium-5) [High-Assurance]"
```

This is the complete procedure. There are no other changes required.

---

## Approved Framing for Technical Evaluators

**When asked "Can you show Level 5 signing?"**

> "Yes — run `python scripts/pqc_level_demo.py --level 5`. You will see Dilithium-5 (ML-DSA-87) generate keys, sign a real governance payload structure, and verify it. Both levels are operational. In production today we run Level 3 (ML-DSA-65) — the NIST enterprise baseline appropriate for institutional capital governance. Level 5 is available by setting one environment variable in the deployment configuration."

**When asked about the Level 3 vs Level 5 choice:**

> "Cryptographic level selection is threat-model driven. Level 3 provides ~192-bit classical security — appropriate for capital-sensitive institutional environments where decision integrity and audit trail immutability are the primary concerns. Level 5 (~256-bit) targets national-grade or state-secrecy contexts. We chose Level 3 intentionally, and we built the architecture so clients in higher-assurance environments can configure Level 5 without any code changes."

---

## What NOT to Say

| Statement | Problem |
|-----------|---------|
| "We support dynamic runtime swap between Level 3 and Level 5" | The level is set at deployment startup, not toggled mid-operation |
| "Level 5 is already active in production" | Production uses Level 3 (ML-DSA-65) |
| "Level 3 is just our minimum" | Level 3 is the designed enterprise target, not a floor |
| "Configurable in real-time without restart" | A service restart is required after changing the env var |

---

## Source Files

| File | Purpose |
|------|---------|
| `scripts/pqc_level_demo.py` | Runnable demo — live signing at Level 3 and Level 5 |
| `omnix_core/security/pqc_config.py` | Tier configuration module (reads PQC_SIGNING_LEVEL) |
| `omnix_core/security/pqc_security.py` | PostQuantumSecurity class — uses pqc_config for all signing |
| `docs/reference/adr/ADR-022-post-quantum-cryptography.md` | Base implementation decision record |
| `docs/reference/adr/ADR-031-pqc-configurable-assurance-tiers.md` | Assurance tier architecture decision record |

---

*OMNIX Decision Governance Infrastructure*  
*PQC Due Diligence Demo — Technical Distribution*
