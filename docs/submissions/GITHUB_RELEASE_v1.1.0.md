# GitHub Release — v1.1.0

**Tag:** `v1.1.0`
**Referencia interna:** OMNIX-REL-2026-001
**Fecha:** Mayo 2026

---

## Texto exacto del release (pegar en GitHub)

### Title
```
v1.1.0 — ATF Runtime Governance Continuity + RFC-ATF-2
```

### Body

```markdown
## OMNIX QUANTUM v1.1.0 — Agent Trust Fabric: Runtime Governance Continuity

This release completes the Agent Trust Fabric (ATF) protocol stack with the
Runtime Governance Continuity layer (ADR-159), extends the formal standard
to RFC-ATF-2, and ships a multi-protocol public verifier.

### New: RFC-ATF-2 — Runtime Governance Continuity Standard

`docs/standards/RFC-ATF-2.md` — IETF-style extension to RFC-ATF-1.

Closes the Runtime Governance Gap: the structural absence of continuous
authority supervision between execution admission (TAR) and completion.
14 total ATF invariants (6 from RFC-ATF-1 + 8 new RGC invariants).

### New: ADR-159 — Runtime Governance Continuity (RGC)

`omnix_core/agents/atf/runtime_continuity.py`

- **Runtime Continuity Record (RCR)** — `ATFRCR-{16HEX}` — PQC-signed
  authority health snapshots anchored to the admission TAR, emitted at
  governed intervals throughout long-running executions.

- **Continuity Eligibility Score (CES)** — composite metric
  `(T×0.30) + (B×0.30) + (D×0.20) + (I×0.20)` across temporal health,
  budget health, context fidelity, and integrity signal.

- **CES Threshold Levels** — NOMINAL (≥75) · MONITORING (≥50) ·
  WARNING (≥25) · CRITICAL (≥10) · HALT (<10).

- **Authority Fragmentation Guard (AFG)** — `RGC-INV-004` — aggregate
  budget enforcement across concurrent sub-agents sharing a chain root.
  Closes fragmentation attack vector that individual-level MAR cannot detect.

- **Continuity Escalation Event (CEE)** — `ATFCEE-{16HEX}` — PQC-signed
  artifact issued on every threshold transition.

- **Reauthorization Challenge (RC)** — `ATFRC-{16HEX}` — signed
  mid-execution authority renewal protocol with automatic HALT on TTL expiry.

- **8 new invariants** — RGC-INV-001 through RGC-INV-008.

- **9 new API endpoints** — `/api/atf/continuity/*` + `/api/atf/escalations/*`

- **82 tests** — `tests/test_runtime_governance_continuity.py` — 82/82 passing.

### New: ADR-157 — Temporal Authority Admissibility (TAR)

`omnix_core/agents/atf/temporal_authority.py`

Nanosecond-precise proof that a Delegation Receipt was valid at the exact
moment of execution admission. Closes the point-of-admission governance gap.
`ATFTAR-{16HEX}` · TAR-INV-001/005 · API: `/api/atf/temporal/*`

### New: ADR-158 — Cross-Domain Trust Portability (DTR)

`omnix_core/agents/atf/domain_bridge.py`

Domain Translation Receipts for cross-domain authority transfer with
per-domain-pair discount schedules. `ATFDTR-{16HEX}` · CDTP-INV-001/006
· API: `/api/atf/translate/*`

### New: ATF Multi-Protocol Verifier

`/atf-verify` — rebuilt from single-artifact to multi-protocol.

Verifies DR (RFC-ATF-1 L2) · TAR (ADR-157 L3) · RCR (RFC-ATF-2 L4).
Features animated CES gauge, continuity chain visualization, ATF stack
layer indicator. Independent verification — no account required (ATF-INV-006).

### Publications

| Document | Status | Reference |
|---|---|---|
| RFC-ATF-1 | Published | DOI: 10.5281/zenodo.20155016 · SSRN: 6757339 |
| RFC-ATF-2 | Draft | `docs/standards/RFC-ATF-2.md` |
| TLA+ Spec | Published | Included in Zenodo v1.0.0 archive |

### ATF Protocol Stack — Complete

| Layer | Artifact | Standard | Status |
|---|---|---|---|
| L1 | AIR (Agent Identity Record) | RFC-ATF-1 §4 | ✓ |
| L2 | DR (Delegation Receipt) | RFC-ATF-1 §5 | ✓ |
| L3 | TAR (Temporal Admissibility Record) | ADR-157 | ✓ |
| L3 | DTR (Domain Translation Receipt) | ADR-158 | ✓ |
| L4 | RCR (Runtime Continuity Record) | RFC-ATF-2 §5 | ✓ |

### Upgrade Notes

- No breaking changes to RFC-ATF-1 artifacts (DR, AIR, Trust Lattice).
- New DB tables: `atf_runtime_continuity`, `atf_continuity_escalations`,
  `atf_temporal_records`, `atf_domain_bridges` — auto-created on first request.
- New env var: `RGC_SAMPLE_INTERVAL_SECONDS` (optional, default per profile).
- New env var: `AFG_FRAGMENTATION_LIMIT` (optional, default 0.90).

### Compliance

EU AI Act Art. 9/13 · DORA Art. 9 · MiCA Recital 65 ·
SOC 2 CC6 · ISO 27001 A.9.4 · NIST AI RMF Govern 1.4
```

---

## Pasos para crear el release en GitHub

1. Ir a `https://github.com/Costenho19/omnibotgenesis/releases/new`
2. **Tag version:** `v1.1.0` (crear tag nuevo sobre commit `0a19e611`)
3. **Target:** `main`
4. **Release title:** `v1.1.0 — ATF Runtime Governance Continuity + RFC-ATF-2`
5. Pegar el cuerpo del release de arriba
6. Adjuntar (opcional): PDF de RFC-ATF-2 cuando esté listo
7. Marcar como **Latest release**
8. Publicar
