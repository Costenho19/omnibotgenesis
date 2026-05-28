---
name: RTE-001 Verifier Signature Patterns
description: Critical sig verification patterns for OMNIX-RTE-001 (ADR-201) — arg order, canonical fields, CTCHC seal, fpdf2 encoding.
---

# RTE-001 Verifier Signature Patterns

**ADR:** ADR-201  
**Artifact:** scripts/verify_treasury_execution_trace.py  
**Status:** 101/101 PASS

## PQC Signature Verification Arg Order

`pqc.verify_signature(sig_bytes, raw_message, pk_bytes)` — this is the correct order.

**Why:** The arg order in the omnix_core PQC module is (sig, message, pk), NOT (message, sig, pk). Getting this wrong produces silent False returns or exceptions.

## DR / TAR Signature Pattern

DR and TAR sign over `content_hash.encode("utf-8")` directly — NOT a JSON payload.

```python
raw = dr.get("content_hash", "").encode("utf-8")
ok = pqc.verify_signature(bytes.fromhex(sig_hex), raw, pk_bytes)
```

**Why:** DR/TAR use compact JSON separators for the hash, but sign the raw hash string bytes, not a re-serialized JSON dict.

## BAR Canonical 6-Field Tuple

`content_hash = SHA3-256(json.dumps({session_id, agent_id, turn_index, output_hash, governing_receipt_id, constraint_set_hash}, sort_keys=True))`

The 6th field is `constraint_set_hash`, NOT `bar_id`.

BAR signature payload (default separators): `{bar_id, content_hash, governing_receipt_id, created_at}`

## CTCHC Seal Pattern

Seal hash is 7-field: `{chain_id, session_id, governing_receipt_id, genesis_hash, turn_count, link_hashes, tip_hash}`  
- `turn_count = len(ordered_links)`  
- `link_hashes = [lk.chain_link_hash for lk in ordered_links]`  
- `tip_hash = sealed.get("current_tip_hash")`

Seal signature payload (default separators): `{chain_id, seal_hash, session_id}`

Link hash: `SHA3-256(json.dumps({prev, turn, receipt}, sort_keys=True))` where `turn` = turn_hash stored in the link dict.

## fpdf2 Core Font Unicode Fix

When using fpdf2 with Helvetica/Courier (core fonts), any non-latin-1 character raises `FPDFUnicodeEncodingException`.

**Fix:** Override `normalize_text` in FPDF subclass WITHOUT calling `super()`:

```python
def normalize_text(self, text: str) -> str:
    for ch, rep in _UNSAFE.items():
        text = text.replace(ch, rep)
    return text.encode("latin-1", errors="replace").decode("latin-1")
```

Calling `super().normalize_text(text)` re-raises the exception even after replacement. Must bypass it entirely.

**Why:** fpdf2 `super().normalize_text()` raises before returning on any non-latin-1 char. The catch-all `errors="replace"` handles all residual non-latin-1 characters safely.
