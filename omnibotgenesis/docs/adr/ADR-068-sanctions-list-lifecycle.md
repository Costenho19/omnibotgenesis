# ADR-068: Sanctions List Lifecycle — OFAC Expansion + Staleness Metadata

**Status:** Accepted  
**Date:** 2026-04-09  
**Author:** Harold Nunes (OMNIX QUANTUM LTD)  
**Companion ADRs:** ADR-066 (Epistemic Transparency), ADR-067 (AML Frequency)

---

## Context

The `JurisdictionGate` (CP-11) performs OFAC sanctions screening for asset symbols. The pre-ADR-068 implementation had two critical gaps:

### Gap 1: Critically sparse list (2 entries)

```python
OFAC_SANCTIONED_ASSETS = {"XMR", "XMR/USD"}
```

Only Monero was listed. Major OFAC-designated protocols and tokens — Tornado Cash (Aug 2022 SDN designation), Sinbad (Nov 2023), Blender, ChipMixer, Railgun, and known Lazarus Group vectors — were absent. Any trade in these sanctioned assets would pass CP-11 undetected.

### Gap 2: No version metadata or staleness detection

The list had no date stamp, no version, and no mechanism to detect when it had last been updated. A 2-year-old list would present identically to a fresh one.

---

## Decision

### 1. Expand the OFAC list to materially representative coverage

```python
OFAC_LIST_VERSION = "2025-Q4-v1"
OFAC_LIST_DATE = date(2025, 12, 1)
OFAC_STALE_WARNING_DAYS = 90

OFAC_SANCTIONED_ASSETS: frozenset[str] = frozenset({
    # Privacy coins — long-standing AML concern
    "XMR", "XMR/USD", "XMR/USDT",
    # Tornado Cash — OFAC SDN August 2022 (08-08-2022)
    "TORNADO", "TORNADO_CASH", "TORN", "TORN/USD", "TORN/USDT",
    # Sinbad mixer — OFAC SDN November 2023
    "SINBAD",
    # Blender.io mixer — OFAC SDN May 2022
    "BLENDER",
    # ChipMixer — OFAC SDN March 2023
    "CHIPMIXER",
    # Railgun — cited in multiple enforcement actions
    "RAILGUN", "RAIL", "RAIL/USD",
    # Known Lazarus Group (DPRK) vectors (March 2022 SDN action)
    "LAZARUS_BRIDGE", "HARMONY_BRIDGE",
})
```

### 2. Add staleness detection

`_check_ofac_staleness()` static method on `JurisdictionGate`:
- Computes `(today - OFAC_LIST_DATE).days`
- If age > `OFAC_STALE_WARNING_DAYS` (90 days): emits `WARNING` log
- If `JURISDICTION_OFAC_STRICT_MODE=true`: additionally emits `ERROR` log (operational alert for regulatory clients)

The method does **not** block the pipeline — it is an operational alert, not a gate veto.

---

## Consequences

### Positive

1. **Material sanctions coverage** — The list now covers the major OFAC SDN designations relevant to crypto since 2022.
2. **Audit trail** — `OFAC_LIST_VERSION` and `OFAC_LIST_DATE` appear in logs and can be included in PQC receipts, giving regulators a verifiable timestamp of the list used.
3. **Operational hygiene** — Staleness detection means the team will be alerted when the list needs refreshing rather than silently using an outdated list.
4. **STRICT_MODE for regulated clients** — Enterprise clients subject to stricter AML regimes can set `JURISDICTION_OFAC_STRICT_MODE=true` for escalated logging.

### Negative / Mitigations

- **List is not exhaustive** — No hardcoded list can match OFAC's live SDN list. This ADR provides "materially representative coverage" for demo, pre-seed, and early production. Production regulatory deployments should integrate a live OFAC SDN API feed. This is tracked as a future architecture decision.
- **No automatic refresh** — The staleness warning is passive. Refresh requires updating `OFAC_LIST_DATE` and `OFAC_LIST_VERSION` and redeploying. This is acceptable for the current scale.

---

## STRICT_MODE Reference

| Environment Variable | Default | Effect |
|---------------------|---------|--------|
| `JURISDICTION_OFAC_STRICT_MODE` | `false` | When `true`, staleness emits ERROR-level log (not just WARNING) |

---

## Implementation

### Files Modified

- `omnix_core/governance/jurisdiction_gate.py` — `OFAC_LIST_VERSION`, `OFAC_LIST_DATE`, `OFAC_STALE_WARNING_DAYS` constants; `OFAC_SANCTIONED_ASSETS` expanded to ~18 entries; `_check_ofac_staleness()` static method added.

### Tests Added

- `tests/test_compliance_gates.py::TestJurisdictionGateEpistemicTransparency`:
  - `test_ofac_list_version_exists` — version + date constants present
  - `test_ofac_list_has_meaningful_entries` — > 5 entries (regression guard against 2-entry list)
  - `test_ofac_tornado_cash_in_list` — TORNADO/TORNADO_CASH present
  - `test_ofac_sinbad_in_list` — SINBAD present

---

## Future Work

- Integrate OFAC SDN live API feed (replaces static list)
- Extend `_check_ofac_staleness()` to emit a structured audit event (not just log) for compliance dashboards
- Add `OFAC_LIST_VERSION` to PQC receipt payload
