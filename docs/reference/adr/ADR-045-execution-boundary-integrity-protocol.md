# ADR-045: Execution Boundary Integrity Protocol (EBIP)

**Status**: Accepted  
**Date**: March 2026  
**Author**: Harold Nunes, OMNIX Architecture  
**Category**: Governance Integrity / Execution Safety  
**Related**: ADR-022, ADR-028, ADR-033, ADR-036, ADR-044

---

## Context

The OMNIX governance pipeline enforces an 8-checkpoint admissibility model. Signals are evaluated sequentially; any single checkpoint failure results in a BLOCKED decision. This is the correct design for fail-closed governance.

However, three deeper problems remain unaddressed:

### Problem 1 — Incomplete Admissibility Model

A system can enforce admissibility rules with precision while those rules contain internal contradictions. For example: a signal set reporting high expected probability AND high risk exposure simultaneously passes all checkpoints yet represents an internally contradictory state. The boundary is enforced; the epistemics inside the boundary are broken.

> Reference: George-Adrian Caboc's critique of incomplete admissibility models. OMNIX addressed this through the **Admissibility Consistency Validator (ACV)**.

### Problem 2 — Criteria Mutability

An evaluation engine that does not cryptographically commit to its criteria before evaluation begins cannot prove those criteria were not changed to match a desired outcome. This is a structural gap in any governance receipt system — the receipt proves what decision was made, but not whether the criteria were stable at the time of evaluation.

### Problem 3 — Path-Dependency Within the Admissible Space

Even with a correct admissibility model, a decision-making system can develop concentration, path-dependency, and edge-seeking behavior entirely within the admissible space. No single decision violates any boundary. Yet the distribution of decisions over time reveals systematic bias.

> Reference: Mar Vincent Jambrich's observation about behavioral monitoring layers that detect patterns across decisions rather than within decisions. OMNIX addressed this through the **Navigation Pattern Monitor (NPM)** and **Concentration Predictor (CP)**.

---

## Decision

Implement the **Execution Boundary Integrity Protocol (EBIP)** as a four-component layer that operates at the execution boundary of the governance pipeline.

**Location**: `omnix_services/governance_service/execution_integrity.py`  
**Pattern**: Pre/post evaluation hooks. Fail gracefully — EBIP never blocks the main pipeline.

---

## The Four Components

### Component 1 — Admissibility Consistency Validator (ACV)

**Class**: `AdmissibilityConsistencyValidator`

Validates that input signals are internally consistent **before** checkpoints run.

Contradiction rules detected:

| Rule | Condition | Severity |
|------|-----------|----------|
| HIGH_PROBABILITY_HIGH_RISK | prob > 80 AND risk > 75 | HIGH |
| HIGH_COHERENCE_LOW_PERSISTENCE | coherence > 80 AND persistence < 25 | MEDIUM |
| HIGH_RESILIENCE_HIGH_EXPOSURE | resilience > 85 AND risk > 70 | MEDIUM |
| LOW_LOGIC_HIGH_APPROVAL_SIGNALS | logic < 20 AND prob > 75 AND coherence > 75 | HIGH |
| ALL_SIGNALS_EXTREME | All signals > 90 or < 10 simultaneously | HIGH |

**Output**: `consistency_score` (0–100), `contradictions[]`, `is_consistent` boolean.

**Persistence**: HIGH violations are logged to `admissibility_violations` table with signal snapshot for audit.

```python
validator = AdmissibilityConsistencyValidator()
result = validator.validate(signals)
# result.consistency_score = 85.0
# result.contradictions = [{"type": "HIGH_PROBABILITY_HIGH_RISK", "severity": "HIGH"}]
```

---

### Component 2 — Execution Commitment Protocol (ECP)

**Class**: `ExecutionCommitmentProtocol`

Creates a cryptographic commitment to evaluation criteria **before** evaluation runs. This approximates Zero-Knowledge Proof (ZKP) commitment scheme semantics without requiring full ZKP infrastructure.

**Commitment structure**:
```
nonce + signals_hash + criteria_hash + timestamp_ns → SHA-256 → commitment_hash
```

**Properties**:
- `signals_hash`: SHA-256 of canonical signal JSON — proves signals weren't changed
- `criteria_hash`: SHA-256 of sorted checkpoint IDs — proves criteria weren't changed
- `nonce`: 16-byte cryptographic random — prevents preimage attacks
- `committed_at_ns`: nanosecond precision timestamp

**Verification**: Anyone with the commitment can verify that signals and criteria match the committed values. The commitment_hash is embedded in governance receipts.

```python
ecp = ExecutionCommitmentProtocol()
commitment = ecp.create_commitment(signals, checkpoint_ids, asset)
# Before evaluation: commitment.commitment_hash sealed

# After evaluation: verify
result = ecp.verify_commitment(commitment, signals, checkpoint_ids)
# result.is_valid = True — criteria were not changed
```

**Institutional framing**: "Cryptographic pre-commitment to evaluation criteria. Governance receipts prove not only what decision was made, but that criteria were sealed before the result was known."

---

### Component 3 — Navigation Pattern Monitor (NPM)

**Class**: `NavigationPatternMonitor`

Tracks the distribution of decisions over rolling windows. Detects concentration, path-dependency, and edge-seeking behavior **within** the admissible space — the patterns that admissibility alone cannot govern.

**Alert levels**:

| Level | Condition | Meaning |
|-------|-----------|---------|
| NOMINAL | Balanced distribution | No concerning patterns |
| WATCH | Mild concentration | Monitoring intensified |
| CAUTION | Significant concentration or path-dependency | Review recommended |
| CRITICAL | Extreme concentration | Admissibility model may be miscalibrated |

**Metrics computed**:
- `concentration_score`: Herfindahl-style measure of decision distribution skew
- `path_dependency_score`: Composite of blocked_pct trend + consistency violation rate
- `navigation_health_score`: 100 − (0.5 × concentration + 0.5 × path_dependency)

**Persistence**: Every decision recorded to `navigation_patterns` table with full distribution snapshot.

---

### Component 4 — Concentration Predictor (CP)

**Class**: `ConcentrationPredictor`

Predicts concentration risk before it emerges — not after. Uses trend analysis on the last N navigation windows to detect whether the decision distribution is converging toward concentration.

**Algorithm**:
1. Load last N `navigation_patterns` records with resolved alert levels
2. Split into recent half and older half
3. Compute `blocked_pct_trend` and `concentration_trend` as delta between halves
4. Score: trend magnitude × 50pts + current level × 30pts
5. Map to: LOW / MEDIUM / HIGH / CRITICAL + confidence %

```
blocked_trend > 15 → +50 pts
concentration_trend > 20 → +40 pts
current_blocked_pct > 75 → +30 pts
```

---

## Integration Points

### Pre-Evaluation

```python
ebip = get_ebip()
pre_context = ebip.pre_evaluation(signals, checkpoint_ids, asset)
# → consistency validation
# → commitment sealed
# → navigation health read
# → concentration predicted
```

### Post-Evaluation

```python
integrity_report = ebip.post_evaluation(
    pre_context, decision, signals, checkpoint_ids, dominant_checkpoint, asset, receipt_id
)
# → commitment verified
# → decision recorded to navigation_patterns
# → consistency violations logged if any
# → execution_integrity_score computed
```

### Dashboard API

```
GET /api/governance/execution-integrity
```
Returns current EBIP system status (no auth required — read-only health endpoint).

---

## Database Tables

### `navigation_patterns`
Records every evaluated decision with distribution snapshot.

| Column | Type | Purpose |
|--------|------|---------|
| `total_decisions` | INTEGER | Decisions in window |
| `approved_pct / blocked_pct / hold_pct` | NUMERIC | Distribution |
| `concentration_score` | NUMERIC | Herfindahl-style measure |
| `path_dependency_score` | NUMERIC | Trend-based measure |
| `alert_level` | VARCHAR | NOMINAL / WATCH / CAUTION / CRITICAL |
| `predicted_concentration_risk` | VARCHAR | CP output |
| `consistency_violations` | INTEGER | ACV violations in window |

### `admissibility_violations`
Audit log for high-severity consistency contradictions.

| Column | Type | Purpose |
|--------|------|---------|
| `receipt_id` | VARCHAR | Links to `decision_receipts` |
| `violation_type` | VARCHAR | ACV rule name |
| `signals_snapshot` | JSONB | Full signal set at time of violation |
| `consistency_score` | NUMERIC | Score at time of violation |

---

## Fail-Safe Design

All four components are wrapped in try/except at every integration point. If EBIP fails:
- Pre-evaluation failure: evaluation proceeds without pre-context
- Post-evaluation failure: decision is committed, EBIP report omitted
- DB failure: in-memory fallback values returned, no pipeline impact

**The main governance pipeline is never blocked by EBIP.**

---

## Execution Integrity Score

The post-evaluation report produces a single `execution_integrity_score` (0–100):

```
Start: 100
− 30  if commitment verification fails
− 10  per HIGH-severity consistency violation
− 20  if navigation alert level is CRITICAL
− 10  if navigation alert level is CAUTION
```

This score is included in governance receipts and accessible via the dashboard API.

---

## Consequences

**Positive:**
- Admissibility model now self-validates for internal consistency
- Criteria immutability is cryptographically provable at receipt level
- Path-dependency detected before concentration is established
- Predictive warning gives time to recalibrate before a governance failure

**Tradeoffs:**
- Minor latency addition for ACV and ECP (~1ms total, fail-graceful)
- DB writes for every decision (navigation_patterns table) — append-only, low cost
- Concentration prediction requires minimum 3 historical windows for meaningful output

---

## Institutional Framing

> "OMNIX doesn't just enforce admissibility at each decision boundary. It monitors the behavioral trajectory of the decision engine over time — detecting concentration, path-dependency, and criteria drift before they produce governance failures. This is the difference between a gate and a governance system."

---

## Implementation

**Files:**
- `omnix_services/governance_service/execution_integrity.py` — all 4 components
- `omnix_services/governance_service/__init__.py` — module init
- `omnix_dashboard/blueprints/governance.py` — API endpoint added

**Tables created automatically on first use:**
- `navigation_patterns`
- `admissibility_violations`
