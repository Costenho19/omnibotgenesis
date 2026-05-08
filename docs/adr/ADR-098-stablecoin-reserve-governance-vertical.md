# ADR-098 — Stablecoin Reserve Governance Vertical

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-04-18 |
| **Author** | Harold Nunes — OMNIX QUANTUM LTD |
| **Scope** | `omnix_web/api/gov_blueprint.py` · `omnix_services/stablecoin_service/` |
| **Replaces** | — |

---

## Context

Stablecoin reserve management represents a distinct governance domain where the consequences of a poor decision — a de-peg event — can propagate systemically across DeFi protocols and institutional portfolios. Existing governance verticals covered trading, credit, and insurance but none addressed the specific risk signals of stablecoin reserves:

- **Collateral ratio monitoring** — reserves must exceed a minimum collateralization ratio at all times
- **De-peg proximity** — price deviation from $1.00 peg triggers graduated governance responses
- **Redemption pressure** — large simultaneous redemption requests require advance governance approval
- **Reserve diversification** — concentration in a single collateral type (e.g., pure-fiat vs. crypto-backed) triggers scrutiny

## Decision

Add `STABLECOIN_RESERVE` as a supported governance domain with dedicated signal schema, AVM baseline, and simulator.

### Signal schema (`_SIGNAL_SCHEMA_SET["stablecoin_reserve"]`)

| Signal | Type | Range | Description |
|---|---|---|---|
| `collateral_ratio` | float | `0.0–5.0` | Reserves / circulating supply |
| `peg_deviation_bps` | float | `0.0–10000.0` | Basis points from $1.00 peg |
| `redemption_pressure` | float | `0.0–1.0` | 24h redemption volume / reserves |
| `reserve_concentration` | float | `0.0–1.0` | Herfindahl index of collateral types |
| `liquidity_buffer` | float | `0.0–1.0` | Liquid reserves / 7-day redemption forecast |

### AVM baseline

Initial calibrated thresholds:
- BLOCK if `collateral_ratio < 1.05` (under-collateralized)
- BLOCK if `peg_deviation_bps > 150` (severe de-peg)
- HOLD if `redemption_pressure > 0.30` (high redemption load)

### Simulator

`omnix_services/stablecoin_service/stablecoin_simulator.py` generates 10 reserve governance decisions per cycle using randomized but realistic signal distributions.

## Consequences

**Positive:**
- OMNIX covers 9 of the 10 target governance domains after this ADR.
- Stablecoin issuers and DeFi protocols have an auditable governance API for reserve management decisions.

**Negative:**
- De-peg scenarios are difficult to simulate realistically; AVM thresholds will require live recalibration after first production use.

## Related

- ADR-052: Islamic Credit Governance (prior vertical)
- ADR-091: Autonomous Agents Governance
- ADR-115: Engine Unification All Verticals
