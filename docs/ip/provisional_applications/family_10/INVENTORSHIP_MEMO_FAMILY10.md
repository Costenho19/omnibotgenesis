# INVENTORSHIP MEMO — FAMILY 10
## OMNIX-PAT-2026-010

**Invention:** Append-Only PQC Merkle Transparency Chain
**Inventor:** Harold Alberto Nunes Rodelo — April 19, 2026

## INVENTIVE CONTRIBUTIONS

1. **Rolling Merkle Accumulator for Governance Receipts:** Design of the incremental O(1) Merkle accumulation formula (SHA256(prev_root || new_hash)) applied specifically to governance decision receipts — enabling compact cryptographic commitment to a complete decision history with no recomputation overhead.

2. **Internal RFC 3161-Style Timestamping:** Design of the internal trusted timestamp mechanism including nonce, policy label, and TST hash — eliminating external TSA dependency while maintaining RFC 3161-compatible integrity guarantees.

3. **Deletion Detection via Hash Linkage:** Design of the chain linkage structure that detects both modification and deletion of entries without reference to any external record.

4. **Public Verification Without Content Disclosure:** Design of the public API that enables third-party chain integrity verification using only hashes — without exposing the plaintext content of governance decisions.

5. **PQC Signing Per Entry with Provider Dispatch:** Integration of the crypto-agility provider architecture (ADR-043) into the chain, enabling per-entry PQC signatures with correct algorithm dispatch at verification time.

## REDUCTION TO PRACTICE
`omnix_core/evidence/transparency_chain.py` — operational since March 2026 (ADR-044).
Git hash: [RETRIEVE BEFORE FILING]
