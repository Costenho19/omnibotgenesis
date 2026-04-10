# ADR-078: Signing Key Persistence

**Status:** ACCEPTED  
**Date:** 2026-04-09  
**Author:** Harold Nunes, OMNIX QUANTUM LTD  
**Scope:** `omnix_core/evidence/decision_receipt.py`

---

## Context

`DecisionReceiptEngine._init_keys()` previously generated a new Dilithium-3 keypair
on every instantiation. This meant:

1. Every process restart produced new keys.
2. Receipts signed before the restart could not be re-verified with the new public key.
3. Third-party verifiers receiving the public key would lose verification capability
   on any restart.

This is incompatible with the enterprise PKI requirement: a receipt signed today
must remain verifiable in six months.

---

## Decision

Load signing keys from environment variables at startup:

| Variable | Content | Required |
|----------|---------|----------|
| `OMNIX_SIGNING_SECRET_KEY_B64` | Base64-encoded Dilithium-3 secret key (~4000 bytes → ~5336 chars) | No (see modes below) |
| `OMNIX_SIGNING_PUBLIC_KEY_B64` | Base64-encoded Dilithium-3 public key (~1952 bytes → ~2604 chars) | If secret key is set |

### Key Modes

`OMNIX_KEY_MODE` environment variable:

| Mode | Secret key absent | Secret key present |
|------|------------------|-------------------|
| `ephemeral_dev` (default) | Generate ephemeral keys; log WARNING + public fingerprint | Load from env; run self-test |
| `required` | Fail startup — refuse to generate ephemeral keys | Load from env; run self-test |

### Self-Test

After loading (or generating) keys, a sign/verify self-test is always performed:
```python
test_msg = b"OMNIX-KEY-SELFTEST"
sig = provider.sign(test_msg, secret_key)
assert provider.verify(sig, test_msg, public_key), "Key self-test failed"
```

If self-test fails → startup error logged; engine falls back to SHA-256-only mode.

### Security Constraints

- Private key material **NEVER** appears in logs. Violation of this is a critical security error.
- On ephemeral key generation: log only the **public key fingerprint** (SHA-256 of public key, hex):
  ```
  [WARNING] Ephemeral signing keys generated. Public key fingerprint: a3b4c5...
             Set OMNIX_SIGNING_SECRET_KEY_B64 and OMNIX_SIGNING_PUBLIC_KEY_B64 for persistence.
  ```
- Public key is safe to log and is also exposed via `/api/receipts/public-key` endpoint (ADR-079).

### Key ID

A `key_id` (SHA-256 fingerprint of the public key, hex[:16]) is attached to every
receipt and to the public key endpoint response. This allows verifiers to detect key rotation.

---

## Key Capture Procedure (for operators)

When running in `ephemeral_dev` mode, capture keys from logs on first startup:

```bash
# In the OMNIX Dashboard startup logs, find:
# [WARNING] Ephemeral signing keys — set env vars to persist:
# OMNIX_SIGNING_SECRET_KEY_B64=<base64>
# OMNIX_SIGNING_PUBLIC_KEY_B64=<base64>
# Copy both to Railway Environment → Variables → Save → Redeploy
```

---

## Consequences

### Positive
- Past receipts remain verifiable across restarts with the same key pair
- Third-party verifiers receive a stable public key
- Self-test prevents silent use of corrupted keys

### Negative / Risks
- Base64-encoded Dilithium-3 keys are ~5-6 KB — large for environment variables
  but within Railway limits (Railway supports up to 32 KB per variable)
- `required` mode prevents startup if env var is misconfigured — mitigated by clear error messages

---

## References

- ADR-079: PKI Verification Endpoint
- `omnix_core/evidence/decision_receipt.py`
- `omnix_core/security/crypto_providers.py`
