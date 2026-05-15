# OMNIX Platform Key Rotation & Compromise Response Runbook

**Document ID:** OMNIX-SEC-2026-001-B  
**Classification:** CONFIDENTIAL — restricted to platform operators  
**Owner:** Harold Nunes — OMNIX QUANTUM LTD (UK)  
**Operative Headquarters:** UAE  
**Last Updated:** 2026-05-15  
**ADR Reference:** ADR-167  
**Status:** ACTIVE

---

## CRITICAL NOTICE

The OMNIX platform signing key is a long-lived ML-DSA-65 (FIPS 204) key pair. It is the root of trust for all evidence archive blocks and OEP packages issued by the platform. **Compromise, loss, or unauthorized disclosure of the private key component (`OMNIX_SIGNING_SECRET_KEY_B64`) permanently undermines the integrity guarantee of all blocks signed with it.**

This runbook must be read by all operators with access to Railway environment variables. It must be reviewed quarterly, or within 30 days of any key-adjacent security incident.

---

## Section 1 — Key Generation Procedure

### 1.1 Prerequisites

Before generating a new platform key pair:

1. Ensure you are operating on a trusted, air-gapped or physically secured machine.
2. Verify that `pypqc` is installed: `pip install pypqc` and `python3 -c "from pqc.sign import dilithium3; print('OK')"`.
3. Confirm the reason for key generation (initial setup or rotation — see trigger criteria in Section 3).
4. Ensure at least one other trusted party is present or informed (two-person rule recommended).

### 1.2 Generation Command

```python
#!/usr/bin/env python3
"""
OMNIX ML-DSA-65 Platform Key Generation
Run on a trusted, isolated machine. Store outputs in a secure vault immediately.
"""
from pqc.sign import dilithium3
import base64, hashlib, json
from datetime import datetime, timezone

# Generate keypair
pk, sk = dilithium3.keypair()

pk_b64 = base64.b64encode(pk).decode("utf-8")
sk_b64 = base64.b64encode(sk).decode("utf-8")
fingerprint = "sha256:" + hashlib.sha256(pk).hexdigest()
generated_at = datetime.now(timezone.utc).isoformat()

print("=" * 60)
print("OMNIX PLATFORM KEY GENERATION OUTPUT")
print("=" * 60)
print(f"Generated at:     {generated_at}")
print(f"Algorithm:        ML-DSA-65 (FIPS 204)")
print(f"Public key size:  {len(pk)} bytes")
print(f"Secret key size:  {len(sk)} bytes")
print(f"Fingerprint:      {fingerprint}")
print()
print("PUBLIC KEY (OMNIX_SIGNING_PUBLIC_KEY_B64):")
print(pk_b64)
print()
print("SECRET KEY (OMNIX_SIGNING_SECRET_KEY_B64) — KEEP CONFIDENTIAL:")
print(sk_b64)
print()
print("Store the secret key in a secure vault (HSM, encrypted secrets manager).")
print("NEVER store the secret key in source control, logs, or plaintext files.")
print()

# Write key record (public information only)
key_record = {
    "generated_at": generated_at,
    "algorithm": "ML-DSA-65 (FIPS 204)",
    "public_key_fingerprint": fingerprint,
    "public_key_b64": pk_b64,
    "key_size_bytes": {"public": len(pk), "secret": len(sk)},
}
with open(f"omnix_key_{fingerprint[7:15]}.pub.json", "w") as f:
    json.dump(key_record, f, indent=2)
print(f"Public key record written to: omnix_key_{fingerprint[7:15]}.pub.json")
```

### 1.3 Post-Generation Steps

1. Immediately store the secret key in Railway environment variables (`OMNIX_SIGNING_SECRET_KEY_B64`).
2. Store the public key in Railway environment variables (`OMNIX_SIGNING_PUBLIC_KEY_B64`).
3. Set `OMNIX_SIGNING_KEY_PUBLISHED_AT` to the generation timestamp.
4. Record the fingerprint in `docs/security/PLATFORM_KEY_REGISTRY.md` (Section 7, Key History table).
5. Verify the keys round-trip correctly before taking any blocks into production:

```python
from pqc.sign import dilithium3
import base64

pk_b64 = "<OMNIX_SIGNING_PUBLIC_KEY_B64>"
sk_b64 = "<OMNIX_SIGNING_SECRET_KEY_B64>"

pk = base64.b64decode(pk_b64)
sk = base64.b64decode(sk_b64)

test_msg = b"OMNIX-KEY-VERIFICATION-TEST-2026"
sig = dilithium3.sign(test_msg, sk)
dilithium3.verify(sig, test_msg, pk)  # raises ValueError if invalid
print("KEYPAIR VERIFIED: signing and verification round-trip OK")
```

6. Destroy the secret key from all local machines after successful Railway upload.

---

## Section 2 — Key Custody Assumptions

### 2.1 Current Custody Model

| Component | Location | Access Control |
|---|---|---|
| Secret key (`OMNIX_SIGNING_SECRET_KEY_B64`) | Railway environment variable | Railway account credentials — MFA required |
| Public key (`OMNIX_SIGNING_PUBLIC_KEY_B64`) | Railway environment variable | Public-facing — also embedded in OEPs |
| Key publication record | `docs/security/PLATFORM_KEY_REGISTRY.md` | Git repository — commit history provides audit trail |
| Fingerprint (DNS TXT) | `_omnix-key.omnixquantum.net` | DNS registrar credentials |

### 2.2 Custody Gaps and Accepted Risks

**Accepted risk — No HSM:** The secret key is stored in a cloud environment variable, not in a Hardware Security Module. This is a known limitation of the current infrastructure. Mitigation: Railway encrypts environment variables at rest; access requires Railway account MFA; secret is never written to disk or logs by the platform.

**Accepted risk — Single custodian:** Currently, only the platform owner (Harold Nunes) has direct Railway access. This creates a single-person dependency. Future mitigation: add a designated deputy with Railway access for business continuity.

**Non-accepted risk — Key in source control:** The private key MUST NEVER appear in any git commit, log file, plaintext config, or debug output. The platform code has no path that logs or exposes the key material.

### 2.3 Future Enhancement Path

- **Phase 2:** AWS KMS or Azure Key Vault integration for secret key storage. Platform uses KMS for signing operations, never handles raw key bytes.
- **Phase 3:** Hardware Security Module (HSM) with key ceremony documentation and split-custody (Shamir's Secret Sharing for key recovery).

---

## Section 3 — Rotation Triggers

A key rotation MUST be initiated under any of the following conditions:

| Trigger | Severity | Response Time |
|---|---|---|
| **T1** — Private key confirmed or suspected compromised | CRITICAL | Immediately (< 1 hour) |
| **T2** — Railway account credentials leaked or unauthorized access detected | CRITICAL | < 4 hours |
| **T3** — Custodian (operator) departure | HIGH | Within 5 business days |
| **T4** — Railway account takeover or breach | CRITICAL | Immediately (< 1 hour) |
| **T5** — FIPS 204 standard deprecated or ML-DSA-65 broken | HIGH | Per NIST guidance |
| **T6** — Scheduled rotation (operational policy) | LOW | Annually — planned |
| **T7** — Third-party audit recommendation | MEDIUM | Within 30 days |
| **T8** — Key age exceeds 3 years | LOW | Planned rotation |

**Annual rotation policy:** Even absent a security trigger, the platform key should be rotated annually. This limits the blast radius of an undetected compromise and exercises the rotation procedure under non-emergency conditions.

---

## Section 4 — Emergency Compromise Response Procedure

Use this procedure when trigger T1, T2, or T4 is confirmed.

### Phase 1 — Immediate Containment (< 1 hour)

1. **Invalidate Railway access immediately:**
   - Log in to Railway at https://railway.app
   - Navigate to Settings → Account → API Tokens
   - Revoke all tokens
   - Change Railway account password immediately
   - Disable any active sessions

2. **Preserve forensic state:**
   - Screenshot or export the Railway audit log showing last 24h of environment variable access.
   - Do NOT delete any logs or change environment variables yet — preserve evidence first.
   - Record the exact time of compromise discovery.

3. **Internal incident declaration:**
   - Create incident record: `OMNIX-INC-YYYY-MMDD-001`
   - Record: discovery time, suspected vector, scope (which key, which Railway environment), last known good timestamp.

### Phase 2 — Key Revocation (< 4 hours)

4. **Generate new key pair** (Section 1 procedure) on a clean machine that was NOT involved in the incident.

5. **Deploy new keys to Railway:**
   - Update `OMNIX_SIGNING_SECRET_KEY_B64` and `OMNIX_SIGNING_PUBLIC_KEY_B64` in Railway.
   - Update `OMNIX_SIGNING_KEY_PUBLISHED_AT` to the new generation timestamp.
   - Restart all Railway services.

6. **Verify new key is active:**
   ```bash
   curl https://omnixquantum.net/api/forensic/platform-key | python3 -m json.tool
   ```
   Confirm `fingerprint` matches the new key's expected value.

### Phase 3 — Revocation Communication (< 24 hours)

7. **Update DNS TXT record:**
   - Log in to DNS registrar.
   - Update `_omnix-key.omnixquantum.net` TXT record to new fingerprint.
   - Set TTL to 300s (5 minutes) to accelerate propagation.
   - Verify propagation: `dig TXT _omnix-key.omnixquantum.net @8.8.8.8`

8. **Update PLATFORM_KEY_REGISTRY.md:**
   - Add new key version to the Key History table (Section 7).
   - Mark old key as `REVOKED` with revocation date and reason.
   - Commit and push.

9. **Update Zenodo** (if applicable):
   - If the compromise affects the key published in the Zenodo research package,
     submit an updated deposit with the new public key and a compromise notice.
   - Zenodo deposits are immutable — create a new version (v2.0.0) with a clear notice
     in the README explaining the key change.

10. **Notify affected parties:**
    - Identify all B2B clients and counterparties who have received OEP packages signed with the compromised key.
    - Send notification: "OMNIX PLATFORM KEY ROTATION NOTICE — Action Required" (see template below).
    - Provide re-verification instructions for their existing packages.

### Notification Template

```
SUBJECT: OMNIX QUANTUM LTD — Platform Signing Key Rotation Notice [OMNIX-INC-YYYY-MMDD-001]

Dear [Counterparty/Client],

OMNIX QUANTUM LTD has rotated its ML-DSA-65 platform signing key.

Old key fingerprint: sha256:<old-fingerprint>
New key fingerprint: sha256:<new-fingerprint>
Effective date: [DATE]

ACTION REQUIRED:
OEP packages you have received signed with the old key remain cryptographically valid.
However, if you need to confirm the signing authority for regulatory or legal purposes,
please contact us to receive a re-issued attestation letter.

No action is required for ongoing platform use — new OEPs will be generated with the new key.

To verify the current platform key:
  curl https://omnixquantum.net/api/forensic/platform-key
  dig TXT _omnix-key.omnixquantum.net

Regards,
Harold Nunes
OMNIX QUANTUM LTD
```

---

## Section 5 — Historical Evidence Treatment

### 5.1 Key Rotation (Non-Compromise)

When a key is rotated without a compromise event, all evidence blocks signed with the old key remain **fully valid**. The rotation does not invalidate historical evidence.

**Policy:** After a planned rotation, the platform maintains and publishes the historical public key alongside the current key. Any auditor or verifier can obtain the old public key from the key history record to verify pre-rotation evidence.

**Where to find historical keys:**
- `docs/security/PLATFORM_KEY_REGISTRY.md` — Key History table (Section 7) includes all retired public keys.
- Zenodo deposits — historical versions of the research package contain the key in use at deposit time.

### 5.2 Key Compromise Event

When a key is rotated due to a confirmed or suspected compromise, historical evidence enters a **trust-reduced state**:

| Evidence Age | Policy |
|---|---|
| Pre-compromise and predating attack window | VALID — blocks sealed before the suspected compromise time retain full integrity. The attacker could not retroactively tamper with already-written blocks. |
| Within the attack window | UNCERTAIN — if the attacker had the private key during this period, they could have forged blocks. These blocks require additional corroboration. |
| Post-compromise discovery (new key) | VALID — new key is not affected by old compromise. |

**Operational guidance:** If a compromise window is identified, any blocks sealed during that window should be corroborated by additional evidence sources (database logs, WAL records, external timestamps). Contact OMNIX QUANTUM LTD for a formal forensic assessment.

### 5.3 Non-Retroactive Tamper Resistance

Once a block is sealed (append-only, stored in PostgreSQL), an attacker with the private key CANNOT retroactively modify the block's content — the `canonical_hash` is cryptographically committed. However, they COULD create new blocks with forged content and sign them as if they were from the platform.

The practical risk of forgery is limited by: (a) the sealed block is also stored in the platform database, (b) the custody log entries are independent evidence, and (c) the block IDs are sequenced (gaps would be visible).

---

## Section 6 — Revocation Communication

### 6.1 Communication Channels

| Channel | Update Timeframe | Audience |
|---|---|---|
| `/api/forensic/platform-key` HTTP endpoint | Immediate (upon Railway deploy) | Machines, APIs, automated systems |
| DNS TXT record | < 72 hours | Any party able to query DNS |
| `docs/security/PLATFORM_KEY_REGISTRY.md` | < 24 hours | Technical operators, auditors |
| Zenodo record | < 7 days | Researchers, institutional auditors |
| Direct client notification | < 24 hours for critical / < 7 days for planned | B2B clients, contractual counterparties |
| Web portal banner | < 4 hours for compromise / < 24 hours for planned | Web portal users |

### 6.2 Minimum Disclosure for Non-Compromise Rotations

For planned annual rotations:
1. Publish 30-day advance notice on the web portal.
2. Notify B2B clients via email 14 days before rotation.
3. Keep old key fingerprint in the registry with status `RETIRED` (not `REVOKED`).
4. Old key remains verifiable for historical evidence for at least 5 years.

---

## Section 7 — New Fingerprint Publication Process

After generating a new key, publish the fingerprint in this exact sequence:

1. **Immediate (< 1 hour):** Deploy to Railway, verify via API.
2. **< 4 hours:** Update `docs/security/PLATFORM_KEY_REGISTRY.md` key history table.
3. **< 4 hours:** Update `docs/ARCHITECTURE_INDEX.md` if needed.
4. **< 24 hours:** Update DNS TXT record `_omnix-key.omnixquantum.net`.
5. **< 48 hours:** Post fingerprint in a pinned announcement on the web portal.
6. **< 7 days:** Submit updated Zenodo deposit with new public key.
7. **< 7 days:** Notify all active B2B clients.

**Fingerprint publication format:**

All public communications must include the fingerprint in this exact format:
```
OMNIX Platform Key (ML-DSA-65 / FIPS 204)
Fingerprint: sha256:<64-hex-characters>
Published: <ISO-8601 date>
Verified at: https://omnixquantum.net/api/forensic/platform-key
```

---

## Section 8 — Backward Verification Policy

### 8.1 Policy Statement

> Evidence blocks and OEP packages signed with a **retired (non-compromised)** platform key remain valid evidence indefinitely.

OMNIX QUANTUM LTD commits to:
1. Maintaining all historical public keys in the key registry for a minimum of **10 years** after retirement.
2. Making historical public keys available via the platform API (future: `/api/forensic/platform-key?version=N`).
3. Including all historical public keys in Zenodo research package updates.

### 8.2 Verification of Historical Evidence

To verify a block signed with a retired key:

```python
import hashlib, base64

# Retrieve the public key for the correct key version from the registry
# (docs/security/PLATFORM_KEY_REGISTRY.md, Section 7)
old_pk_b64 = "<historical public key>"
old_pk_bytes = base64.b64decode(old_pk_b64)
old_fingerprint = "sha256:" + hashlib.sha256(old_pk_bytes).hexdigest()

# Compare with the key in the OEP
pkg_pk_b64 = open("KEYS/public_key.b64").read().strip()
pkg_fingerprint = "sha256:" + hashlib.sha256(base64.b64decode(pkg_pk_b64)).hexdigest()

if pkg_fingerprint == old_fingerprint:
    print(f"Key matches retired platform key version: {version}")
    print("Evidence is verifiable. Proceed with PQC signature verification.")
```

### 8.3 Compromise-Adjacent Evidence

Evidence sealed within a suspected compromise window requires:
1. Formal written attestation from OMNIX QUANTUM LTD.
2. Corroborating evidence from independent sources (database timestamps, WAL records).
3. If for legal proceedings: contact OMNIX QUANTUM LTD for an expert declaration.

---

## Section 9 — Operator Responsibilities

### 9.1 Primary Operator (Platform Owner)

**Harold Nunes — OMNIX QUANTUM LTD**

- Sole authority to generate new platform keys.
- Responsible for all custody decisions.
- Must complete Section 4 emergency procedure personally or designate a qualified deputy in advance.
- Must review this runbook quarterly and attest to its accuracy.

### 9.2 Designated Deputy (To Be Appointed)

A designated deputy should be appointed for business continuity. This person must:
- Have documented access to Railway credentials (stored in a sealed envelope or secure vault, not shared electronically).
- Be familiar with this runbook.
- Know the location of all key custody records.

**Current status:** Deputy not yet designated. This is a known risk (OMNIX-SEC-2026-001 tracking item).

### 9.3 Third-Party Auditors

Third-party security auditors who discover a suspected key compromise must:
1. Contact Harold Nunes immediately via official OMNIX QUANTUM LTD contact.
2. Provide: date of discovery, nature of suspected compromise, any evidence collected.
3. NOT attempt to verify or exploit the compromise independently.

### 9.4 B2B Client Operators

B2B clients who believe they have received a fraudulent OEP (fingerprint mismatch with platform registry) must:
1. Not use the OEP as evidence until verified.
2. Contact OMNIX QUANTUM LTD immediately with: package ID, package date, fingerprint in package.
3. Preserve the suspect OEP file without modification.

---

## Section 10 — Required Audit Logs

The following events MUST be logged in the OMNIX platform audit log, with sufficient detail to reconstruct the timeline in a post-incident review:

### 10.1 Key-Adjacent Events (Auto-Generated by Platform)

| Event | Log Message Format | Required Fields |
|---|---|---|
| Non-platform key used in `/verify` | `[ForensicAPI/verify] Non-platform key used` | `provided_fingerprint`, `platform_fingerprint`, `client_ip`, `timestamp` |
| Export called with platform key | `[ForensicAPI/export] KEY_SOURCE=PLATFORM` | `client_id`, `block_count`, `package_id`, `key_source`, `timestamp` |
| Export called with caller key | `[ForensicAPI/export] KEY_SOURCE=CALLER` | `client_id`, `block_count`, `package_id`, `key_source`, `timestamp` |
| Rate limit exceeded on `/verify` | Flask-Limiter 429 response | `client_ip`, `endpoint`, `timestamp` |
| Rate limit exceeded on `/export` | Flask-Limiter 429 response | `client_ip`, `endpoint`, `timestamp` |

### 10.2 Manual Events (Operator Must Record)

| Event | Where to Record | Required Fields |
|---|---|---|
| Key generation | `PLATFORM_KEY_REGISTRY.md` §7 + incident log | `generated_at`, `fingerprint`, `operator`, `reason` |
| Key deployed to Railway | Incident log | `deploy_time`, `key_fingerprint`, `operator`, `railway_env` |
| Key rotation completed | `PLATFORM_KEY_REGISTRY.md` §7 | `old_fingerprint`, `new_fingerprint`, `rotation_date`, `reason` |
| Compromise declared | Incident log OMNIX-INC-* | `declared_at`, `suspected_vector`, `discovery_source`, `scope` |
| Client notification sent | CRM/email system | `recipient`, `sent_at`, `old_fingerprint`, `new_fingerprint` |
| Runbook review completed | Git commit to this file | `reviewed_by`, `review_date`, `changes_made` |

### 10.3 Railway Audit Log Preservation

Railway provides an audit log of environment variable changes. This log must be:
- Exported and archived at every key rotation event.
- Preserved for a minimum of 5 years.
- Included in any incident investigation.

To export: Railway Dashboard → Project → Settings → Activity → Export.

### 10.4 Incident Log Format

For every key-adjacent security incident, create a file at:
```
docs/security/incidents/OMNIX-INC-YYYY-MMDD-NNN.md
```

Minimum content:
```markdown
# Incident: OMNIX-INC-YYYY-MMDD-NNN

**Severity:** CRITICAL | HIGH | MEDIUM
**Status:** OPEN | CONTAINED | RESOLVED
**Declared:** [ISO-8601 timestamp]
**Declared by:** [Operator name]

## Summary
[1-paragraph description]

## Timeline
- [timestamp] — [event]

## Impact Assessment
[Affected keys, blocks, clients]

## Response Actions
[Actions taken with timestamps]

## Resolution
[How resolved, new state]

## Lessons Learned
[What to improve]
```

---

## Appendix A — Key Verification Quick Reference

```bash
# Verify current platform key fingerprint via API
curl -s https://omnixquantum.net/api/forensic/platform-key \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['fingerprint'])"

# Verify via DNS (no HTTP required)
dig TXT _omnix-key.omnixquantum.net +short

# Compute fingerprint from a public key file
python3 -c "
import hashlib, base64, sys
pk_b64 = open(sys.argv[1]).read().strip()
pk = base64.b64decode(pk_b64)
print('sha256:' + hashlib.sha256(pk).hexdigest())
" KEYS/public_key.b64

# Test keypair round-trip
python3 -c "
from pqc.sign import dilithium3
import base64, os
pk_b64 = os.environ['OMNIX_SIGNING_PUBLIC_KEY_B64']
sk_b64 = os.environ['OMNIX_SIGNING_SECRET_KEY_B64']
pk = base64.b64decode(pk_b64); sk = base64.b64decode(sk_b64)
msg = b'OMNIX-KEYPAIR-TEST'
sig = dilithium3.sign(msg, sk)
dilithium3.verify(sig, msg, pk)
print('KEYPAIR OK')
"
```

---

## Appendix B — Runbook Change History

| Date | Version | Author | Summary |
|---|---|---|---|
| 2026-05-15 | 1.0 | Harold Nunes | Initial runbook — addresses OMNIX-SEC-2026-001 |
