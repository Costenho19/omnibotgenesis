# ADR-041: Multi-Agent Decision Governance

**Status**: Accepted  
**Date**: March 2026  
**Author**: Harold Nunes, OMNIX Architecture  
**Category**: Governance Architecture  

---

## Context

OMNIX V6.5.4e governs trading decisions through an 8-checkpoint pipeline using signals derived from internal technical indicators (EMA, HMM, Kalman, Non-Markovian Kernel). These signals are computed within a single processing path.

The system lacks an independent, multi-source signal layer that:
- Aggregates technical, sentiment, and risk signals from separate autonomous sources
- Provides a weighted consensus as external validation before the governance pipeline
- Logs each agent's reasoning independently for audit and calibration

This ADR introduces a Multi-Agent Governance Layer that runs in parallel with the existing pipeline as an **additive, non-blocking** component.

---

## Decision

Build a `omnix_services/agents/` subsystem with 3 specialized agents and 1 orchestrator:

### Agents

| Agent | Data Sources | Weight | Purpose |
|-------|-------------|--------|---------|
| **SignalAgent** | Kraken OHLC + Alpha Vantage RSI/MACD | 0.45 | Technical market signal |
| **RiskAgent** | PostgreSQL bot_state + Redis risk keys | 0.30 | Portfolio risk environment |
| **SentimentAgent** | Finnhub news + Tavily search + Fear & Greed | 0.25 | Market context and sentiment |

### Orchestrator

Runs all 3 agents with `asyncio.gather(return_exceptions=True)`.

**Consensus formula:**
```
score = Σ(weight_i × signal_value_i × confidence_norm_i)
signal_value: BUY=+1, HOLD=0, SELL=-1
confidence_norm: confidence / 100
```

**Signal thresholds:**
- `score > +0.20` → BUY
- `score < -0.20` → SELL
- else → HOLD

**Disagreement rule:**
If all 3 agents return mutually exclusive signals (BUY + SELL + HOLD simultaneously):
- Consensus = HOLD
- confidence capped at 35
- `requires_stronger_core_signal = True`

### Integration

Injected into `auto_trading_bot.py` via feature flag:

```python
ENABLE_MULTI_AGENT_GOVERNANCE = os.environ.get("ENABLE_MULTI_AGENT_GOVERNANCE", "false").lower() == "true"
```

When enabled, `OrchestratorResult` is available in the decision context as `external_agent_consensus`.
When disabled (default), existing pipeline behavior is **100% unchanged**.

### Persistence

Each run is stored in `agent_orchestrator_runs` PostgreSQL table (JSONB for component details).

---

## File Structure

```
omnix_services/agents/
├── __init__.py           # Public API
├── models.py             # AgentResult, OrchestratorResult, enums
├── base_agent.py         # Abstract base with fallback/timeout
├── signal_agent.py       # Kraken + Alpha Vantage
├── sentiment_agent.py    # Finnhub + Tavily + Fear & Greed
├── risk_agent.py         # DB bot_state + Redis
├── orchestrator.py       # Parallel runner + weighted consensus
└── repository.py         # PostgreSQL persistence
```

---

## Consequences

### Positive
- Independent multi-source signal validation before governance pipeline
- Each agent fails gracefully (HOLD + confidence=0) without breaking the pipeline
- Full audit trail per agent per decision (JSONB in DB)
- Feature-flagged: zero risk to existing production behavior
- Domain-agnostic pattern — can be extended to other verticals

### Negative / Risks
- Additional API calls (Kraken, Alpha Vantage, Finnhub, Tavily) increase latency by ~100-500ms
- Agent results are advisory only — pipeline continues regardless
- Risk of over-reliance on agent consensus if weights are not properly calibrated

### Mitigations
- 8-12s timeout per agent; orchestrator never blocks the pipeline
- Feature flag default OFF — Railway deployment unaffected until explicitly enabled
- Calibration review after 30 days of parallel shadow operation

---

## Alternatives Considered

1. **Single monolithic signal aggregator** — Rejected: lacks independent fallback per source, harder to audit
2. **Replacing internal signals with agent signals** — Rejected: removes proven governance logic
3. **Synchronous sequential execution** — Rejected: too slow (~30s total), asyncio parallel is ~10s

---

## Rollback

```bash
# Disable immediately without redeploy:
ENABLE_MULTI_AGENT_GOVERNANCE=false  # (default)

# Remove from pipeline:
# Revert hook in auto_trading_bot.py (see ADR-041 integration section)
```

---

## Related ADRs

- ADR-027: Decision Governance Infrastructure — category definition
- ADR-033: Signal Integrity Validator (SIV) — CP-0 data quality gate
- ADR-036: Exit Governance Layer — 3-gate exit pipeline
- ADR-040: Public Governance Sandbox
