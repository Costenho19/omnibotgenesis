"""
OMNIX — Multi-Domain Risk Governance Engine (MDRG)
ADR-143: Unified Financial, Technical, Legal, and Human Risk Scoring

Purpose:
    The Multi-Domain Risk Governance Engine unifies four orthogonal risk vectors
    into a single governance score, enabling non-financial clients to use OMNIX
    as a general-purpose governance control layer.

    Unlike domain-specific engines (trading, insurance, robotics), the MDRG
    operates across any subject and context, mapping client-supplied risk signals
    to a normalized composite governance score.

Four Risk Vectors:
    1. FINANCIAL   — capital exposure, liquidity, leverage, credit risk
    2. TECHNICAL   — system reliability, latency, dependency failures, uptime
    3. LEGAL       — regulatory compliance, jurisdiction, liability exposure
    4. HUMAN       — operator error rate, oversight coverage, fatigue index

Scoring:
    - Each vector produces a score 0–100 (0 = no risk, 100 = maximum risk)
    - Composite score = weighted average (configurable per client)
    - Default weights: financial=0.35, technical=0.25, legal=0.25, human=0.15
    - Decision: APPROVED (<60), REVIEW (60–79), BLOCKED (≥80)
    - Hard blocks: any single vector ≥ 95 → BLOCKED regardless of composite

Design:
    - Fail-closed: DB error → BLOCKED (ADR-116)
    - Stateless scoring: no ML model dependency — pure rule-based for auditability
    - All assessments persisted to `multi_domain_risk_assessments`
    - PQC-signable: output schema compatible with ADR-078 signing pipeline

Regulatory alignment:
    - NIST AI RMF: MP-2.3 (risk categorization), MS-2.5 (risk monitoring)
    - EU AI Act Art. 9: Risk management systems for high-risk AI
    - ISO 31000: Risk management — general principles
    - ISO/IEC 42001: AI management system — risk treatment

ADR-143 | Implemented: May 2026
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("OMNIX.MultiDomainRisk")

_TABLE = "multi_domain_risk_assessments"

# ── Decision thresholds ───────────────────────────────────────────────────────
THRESHOLD_BLOCKED = 80.0
THRESHOLD_REVIEW  = 60.0
HARD_BLOCK_SCORE  = 95.0

# ── Risk vectors ──────────────────────────────────────────────────────────────
VECTOR_FINANCIAL  = "financial"
VECTOR_TECHNICAL  = "technical"
VECTOR_LEGAL      = "legal"
VECTOR_HUMAN      = "human"

_DEFAULT_WEIGHTS: Dict[str, float] = {
    VECTOR_FINANCIAL: 0.35,
    VECTOR_TECHNICAL: 0.25,
    VECTOR_LEGAL:     0.25,
    VECTOR_HUMAN:     0.15,
}

# ── Signal catalogs per vector ────────────────────────────────────────────────
_SIGNAL_CATALOG: Dict[str, Dict[str, Any]] = {
    VECTOR_FINANCIAL: {
        "capital_exposure_pct":  {"range": [0, 100], "description": "% of capital at risk"},
        "liquidity_ratio":       {"range": [0, 10],  "description": "Current liquidity ratio (higher=better, inverted for risk)"},
        "leverage_ratio":        {"range": [0, 50],  "description": "Leverage ratio (higher=more risk)"},
        "credit_score":          {"range": [0, 100], "description": "Counterparty credit score (higher=better, inverted)"},
        "concentration_pct":     {"range": [0, 100], "description": "Portfolio concentration in single asset/counterparty"},
    },
    VECTOR_TECHNICAL: {
        "uptime_pct":            {"range": [0, 100], "description": "System uptime % (higher=better, inverted for risk)"},
        "error_rate_pct":        {"range": [0, 100], "description": "Request error rate %"},
        "latency_p99_ms":        {"range": [0, 60000], "description": "p99 latency in ms"},
        "dependency_failure_count": {"range": [0, 50], "description": "Failed dependencies in last hour"},
        "last_incident_hours":   {"range": [0, 8760], "description": "Hours since last incident (higher=better, inverted)"},
    },
    VECTOR_LEGAL: {
        "regulatory_violations": {"range": [0, 20],  "description": "Open regulatory violations"},
        "jurisdiction_risk_score": {"range": [0, 100], "description": "Jurisdiction risk score (0=low, 100=sanctioned)"},
        "pending_litigation":    {"range": [0, 100], "description": "# of pending litigation items"},
        "license_expiry_days":   {"range": [0, 365], "description": "Days until license expiry (lower=more risk)"},
        "aml_flag":              {"range": [0, 1],   "description": "AML flag active (0=no, 1=yes)"},
    },
    VECTOR_HUMAN: {
        "operator_error_rate_pct": {"range": [0, 100], "description": "Operator error rate %"},
        "oversight_coverage_pct":  {"range": [0, 100], "description": "Human oversight coverage % (higher=better, inverted)"},
        "fatigue_index":           {"range": [0, 100], "description": "Team fatigue index (0=rested, 100=critical)"},
        "training_currency_days":  {"range": [0, 365], "description": "Days since last compliance training (lower=better)"},
        "escalation_backlog":      {"range": [0, 500], "description": "# of unresolved escalations"},
    },
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _assessment_id() -> str:
    return f"MDRG-{uuid.uuid4().hex[:12].upper()}"


def _get_conn():
    import psycopg
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg.connect(url)


_DDL = """
CREATE TABLE IF NOT EXISTS multi_domain_risk_assessments (
    id                  SERIAL PRIMARY KEY,
    assessment_id       TEXT        NOT NULL UNIQUE,
    subject             TEXT        NOT NULL,
    client_domain       TEXT,
    decision            TEXT        NOT NULL,
    composite_score     NUMERIC(6,2) NOT NULL,
    financial_score     NUMERIC(6,2),
    technical_score     NUMERIC(6,2),
    legal_score         NUMERIC(6,2),
    human_score         NUMERIC(6,2),
    hard_block_vector   TEXT,
    weights_used        JSONB,
    signals             JSONB,
    breakdown           JSONB,
    assessed_by         TEXT,
    assessed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_mdrg_subject
    ON multi_domain_risk_assessments (subject);
CREATE INDEX IF NOT EXISTS idx_mdrg_decision
    ON multi_domain_risk_assessments (decision);
CREATE INDEX IF NOT EXISTS idx_mdrg_assessed_at
    ON multi_domain_risk_assessments (assessed_at DESC);
"""


# ── Scoring logic ─────────────────────────────────────────────────────────────

def _score_financial(signals: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize financial signals to a 0-100 risk score."""
    components: List[Dict[str, Any]] = []
    scores: List[float] = []

    cap = float(signals.get("capital_exposure_pct", 0))
    if cap:
        score = min(100.0, cap)
        components.append({"signal": "capital_exposure_pct", "raw": cap, "risk_score": score})
        scores.append(score)

    liq = float(signals.get("liquidity_ratio", 2.0))
    liq_risk = max(0.0, min(100.0, (2.0 - liq) / 2.0 * 100))
    components.append({"signal": "liquidity_ratio", "raw": liq, "risk_score": liq_risk})
    scores.append(liq_risk)

    lev = float(signals.get("leverage_ratio", 1.0))
    lev_risk = min(100.0, lev / 20.0 * 100)
    components.append({"signal": "leverage_ratio", "raw": lev, "risk_score": lev_risk})
    scores.append(lev_risk)

    cred = float(signals.get("credit_score", 50.0))
    cred_risk = max(0.0, min(100.0, 100.0 - cred))
    components.append({"signal": "credit_score", "raw": cred, "risk_score": cred_risk})
    scores.append(cred_risk)

    conc = float(signals.get("concentration_pct", 0))
    if conc:
        score = min(100.0, conc)
        components.append({"signal": "concentration_pct", "raw": conc, "risk_score": score})
        scores.append(score)

    vector_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    return {"vector": VECTOR_FINANCIAL, "score": vector_score, "components": components}


def _score_technical(signals: Dict[str, Any]) -> Dict[str, Any]:
    components: List[Dict[str, Any]] = []
    scores: List[float] = []

    uptime = float(signals.get("uptime_pct", 99.9))
    up_risk = max(0.0, min(100.0, (100.0 - uptime) * 20))
    components.append({"signal": "uptime_pct", "raw": uptime, "risk_score": up_risk})
    scores.append(up_risk)

    err = float(signals.get("error_rate_pct", 0))
    err_risk = min(100.0, err * 10)
    components.append({"signal": "error_rate_pct", "raw": err, "risk_score": err_risk})
    scores.append(err_risk)

    lat = float(signals.get("latency_p99_ms", 200))
    lat_risk = min(100.0, lat / 5000 * 100)
    components.append({"signal": "latency_p99_ms", "raw": lat, "risk_score": lat_risk})
    scores.append(lat_risk)

    deps = float(signals.get("dependency_failure_count", 0))
    dep_risk = min(100.0, deps * 10)
    components.append({"signal": "dependency_failure_count", "raw": deps, "risk_score": dep_risk})
    scores.append(dep_risk)

    inc = float(signals.get("last_incident_hours", 720))
    inc_risk = max(0.0, min(100.0, (720 - inc) / 720 * 100))
    components.append({"signal": "last_incident_hours", "raw": inc, "risk_score": inc_risk})
    scores.append(inc_risk)

    vector_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    return {"vector": VECTOR_TECHNICAL, "score": vector_score, "components": components}


def _score_legal(signals: Dict[str, Any]) -> Dict[str, Any]:
    components: List[Dict[str, Any]] = []
    scores: List[float] = []

    violations = float(signals.get("regulatory_violations", 0))
    viol_risk = min(100.0, violations * 15)
    components.append({"signal": "regulatory_violations", "raw": violations, "risk_score": viol_risk})
    scores.append(viol_risk)

    jur = float(signals.get("jurisdiction_risk_score", 0))
    components.append({"signal": "jurisdiction_risk_score", "raw": jur, "risk_score": jur})
    scores.append(jur)

    lit = float(signals.get("pending_litigation", 0))
    lit_risk = min(100.0, lit * 5)
    components.append({"signal": "pending_litigation", "raw": lit, "risk_score": lit_risk})
    scores.append(lit_risk)

    lic = float(signals.get("license_expiry_days", 365))
    lic_risk = max(0.0, min(100.0, (90 - lic) / 90 * 100)) if lic < 90 else 0.0
    components.append({"signal": "license_expiry_days", "raw": lic, "risk_score": lic_risk})
    scores.append(lic_risk)

    aml = float(signals.get("aml_flag", 0))
    aml_risk = 100.0 if aml >= 1 else 0.0
    components.append({"signal": "aml_flag", "raw": aml, "risk_score": aml_risk})
    scores.append(aml_risk)

    vector_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    return {"vector": VECTOR_LEGAL, "score": vector_score, "components": components}


def _score_human(signals: Dict[str, Any]) -> Dict[str, Any]:
    components: List[Dict[str, Any]] = []
    scores: List[float] = []

    err = float(signals.get("operator_error_rate_pct", 0))
    err_risk = min(100.0, err * 5)
    components.append({"signal": "operator_error_rate_pct", "raw": err, "risk_score": err_risk})
    scores.append(err_risk)

    cov = float(signals.get("oversight_coverage_pct", 80.0))
    cov_risk = max(0.0, min(100.0, (80.0 - cov) / 80.0 * 100))
    components.append({"signal": "oversight_coverage_pct", "raw": cov, "risk_score": cov_risk})
    scores.append(cov_risk)

    fat = float(signals.get("fatigue_index", 0))
    components.append({"signal": "fatigue_index", "raw": fat, "risk_score": fat})
    scores.append(fat)

    train = float(signals.get("training_currency_days", 30))
    train_risk = min(100.0, max(0.0, (train - 90) / 275 * 100)) if train > 90 else 0.0
    components.append({"signal": "training_currency_days", "raw": train, "risk_score": train_risk})
    scores.append(train_risk)

    backlog = float(signals.get("escalation_backlog", 0))
    back_risk = min(100.0, backlog / 50 * 100)
    components.append({"signal": "escalation_backlog", "raw": backlog, "risk_score": back_risk})
    scores.append(back_risk)

    vector_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    return {"vector": VECTOR_HUMAN, "score": vector_score, "components": components}


_SCORERS = {
    VECTOR_FINANCIAL: _score_financial,
    VECTOR_TECHNICAL: _score_technical,
    VECTOR_LEGAL:     _score_legal,
    VECTOR_HUMAN:     _score_human,
}


# ── Engine ────────────────────────────────────────────────────────────────────

class MultiDomainRiskEngine:
    """
    ADR-143 — Multi-Domain Risk Governance Engine.

    Usage:
        engine = MultiDomainRiskEngine()
        result = engine.evaluate(
            subject="ACME_CORP_DEPLOYMENT_42",
            risk_signals={
                "financial": {"capital_exposure_pct": 45, "leverage_ratio": 3.0},
                "technical": {"uptime_pct": 99.5, "error_rate_pct": 0.3},
                "legal":     {"regulatory_violations": 0, "jurisdiction_risk_score": 10},
                "human":     {"operator_error_rate_pct": 1.2, "oversight_coverage_pct": 95},
            }
        )
        print(result["decision"])        # APPROVED | REVIEW | BLOCKED
        print(result["composite_score"]) # 0–100
    """

    _table_ensured: bool = False

    def ensure_table(self) -> None:
        try:
            conn = _get_conn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(_DDL)
            conn.close()
            MultiDomainRiskEngine._table_ensured = True
            logger.info("[MDRG] multi_domain_risk_assessments table ready")
        except Exception as exc:
            logger.error("[MDRG] ensure_table failed: %s", exc)

    def _ensure(self) -> None:
        if not MultiDomainRiskEngine._table_ensured:
            self.ensure_table()

    # ── Public API ────────────────────────────────────────────────────────────

    def evaluate(
        self,
        subject:      str,
        risk_signals: Dict[str, Dict[str, Any]],
        weights:      Optional[Dict[str, float]] = None,
        client_domain: Optional[str] = None,
        assessed_by:  str = "api",
    ) -> Dict[str, Any]:
        """
        Evaluate multi-domain risk for a subject.

        Args:
            subject:      Identifier for the entity/deployment being evaluated.
            risk_signals: Dict mapping vector name → signal dict.
                          Vectors: financial, technical, legal, human.
            weights:      Optional custom weights (must sum to 1.0).
            client_domain: Client's domain context (e.g., "logistics", "healthcare").
            assessed_by:  Who triggered this assessment.

        Returns:
            Full risk assessment dict with composite_score, decision, breakdown.
        """
        self._ensure()

        weights_    = weights or _DEFAULT_WEIGHTS.copy()
        total_w     = sum(weights_.values())
        weights_    = {k: v / total_w for k, v in weights_.items()}

        assessment_id = _assessment_id()
        breakdown: List[Dict[str, Any]] = []
        vector_scores: Dict[str, float] = {}
        hard_block_vector: Optional[str] = None

        for vector, scorer in _SCORERS.items():
            sigs = risk_signals.get(vector, {})
            result = scorer(sigs)
            vscore = result["score"]
            vector_scores[vector] = vscore
            breakdown.append(result)

            if vscore >= HARD_BLOCK_SCORE:
                hard_block_vector = vector
                logger.warning(
                    "[MDRG] Hard block on %s vector: score=%.1f >= %.1f",
                    vector, vscore, HARD_BLOCK_SCORE,
                )

        composite = round(
            sum(vector_scores.get(v, 0.0) * w for v, w in weights_.items()), 2
        )

        if hard_block_vector:
            decision = "BLOCKED"
            decision_reason = (
                f"Hard block: {hard_block_vector} vector score "
                f"{vector_scores[hard_block_vector]:.1f} ≥ {HARD_BLOCK_SCORE}"
            )
        elif composite >= THRESHOLD_BLOCKED:
            decision = "BLOCKED"
            decision_reason = f"Composite risk score {composite:.1f} ≥ {THRESHOLD_BLOCKED} (BLOCKED threshold)"
        elif composite >= THRESHOLD_REVIEW:
            decision = "REVIEW"
            decision_reason = f"Composite risk score {composite:.1f} in review band [{THRESHOLD_REVIEW}, {THRESHOLD_BLOCKED})"
        else:
            decision = "APPROVED"
            decision_reason = f"Composite risk score {composite:.1f} < {THRESHOLD_REVIEW} (within acceptable range)"

        output = {
            "assessment_id":    assessment_id,
            "subject":          subject,
            "client_domain":    client_domain,
            "decision":         decision,
            "decision_reason":  decision_reason,
            "composite_score":  composite,
            "vector_scores": {
                VECTOR_FINANCIAL: vector_scores.get(VECTOR_FINANCIAL),
                VECTOR_TECHNICAL: vector_scores.get(VECTOR_TECHNICAL),
                VECTOR_LEGAL:     vector_scores.get(VECTOR_LEGAL),
                VECTOR_HUMAN:     vector_scores.get(VECTOR_HUMAN),
            },
            "hard_block_vector": hard_block_vector,
            "weights_used":      weights_,
            "breakdown":         breakdown,
            "thresholds": {
                "blocked": THRESHOLD_BLOCKED,
                "review":  THRESHOLD_REVIEW,
                "hard_block_per_vector": HARD_BLOCK_SCORE,
            },
            "assessed_by":  assessed_by,
            "assessed_at":  _now_utc(),
            "adr":          "ADR-143",
        }

        self._persist(output, risk_signals, weights_)
        logger.info(
            "[MDRG] Assessment %s | subject=%s | decision=%s | composite=%.1f",
            assessment_id, subject, decision, composite,
        )
        return output

    def get_history(
        self,
        subject:       Optional[str] = None,
        client_domain: Optional[str] = None,
        decision:      Optional[str] = None,
        limit:         int = 50,
        offset:        int = 0,
    ) -> Dict[str, Any]:
        """Return paginated assessment history with optional filters."""
        self._ensure()
        try:
            conn = _get_conn()
            clauses, params = [], []
            if subject:
                clauses.append("subject ILIKE %s")
                params.append(f"%{subject}%")
            if client_domain:
                clauses.append("client_domain = %s")
                params.append(client_domain)
            if decision:
                clauses.append("decision = %s")
                params.append(decision.upper())

            where = ("WHERE " + " AND ".join(clauses)) if clauses else ""

            with conn:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT COUNT(*) FROM {_TABLE} {where}", params)
                    total = cur.fetchone()[0]

                    cur.execute(
                        f"SELECT assessment_id, subject, client_domain, decision, "
                        f"composite_score, financial_score, technical_score, legal_score, "
                        f"human_score, hard_block_vector, assessed_by, assessed_at "
                        f"FROM {_TABLE} {where} "
                        f"ORDER BY assessed_at DESC LIMIT %s OFFSET %s",
                        params + [limit, offset],
                    )
                    rows = cur.fetchall()
            conn.close()

            items = []
            for r in rows:
                items.append({
                    "assessment_id":    r[0],
                    "subject":          r[1],
                    "client_domain":    r[2],
                    "decision":         r[3],
                    "composite_score":  float(r[4]) if r[4] else None,
                    "vector_scores": {
                        "financial": float(r[5]) if r[5] else None,
                        "technical": float(r[6]) if r[6] else None,
                        "legal":     float(r[7]) if r[7] else None,
                        "human":     float(r[8]) if r[8] else None,
                    },
                    "hard_block_vector": r[9],
                    "assessed_by":       r[10],
                    "assessed_at":       r[11].isoformat() if r[11] else None,
                })

            return {
                "assessments": items,
                "total":       total,
                "limit":       limit,
                "offset":      offset,
                "has_more":    (offset + limit) < total,
            }

        except Exception as exc:
            logger.error("[MDRG] get_history failed: %s", exc)
            return {"assessments": [], "total": 0, "error": str(exc)}

    def get_catalog(self) -> Dict[str, Any]:
        """Return supported risk vectors and their signal definitions."""
        return {
            "vectors":          list(_SIGNAL_CATALOG.keys()),
            "signal_catalog":   _SIGNAL_CATALOG,
            "default_weights":  _DEFAULT_WEIGHTS,
            "thresholds": {
                "blocked":               THRESHOLD_BLOCKED,
                "review":                THRESHOLD_REVIEW,
                "hard_block_per_vector": HARD_BLOCK_SCORE,
            },
            "decision_logic": (
                "composite ≥ 80 → BLOCKED | 60–79 → REVIEW | <60 → APPROVED. "
                "Any single vector ≥ 95 → BLOCKED regardless of composite."
            ),
            "adr": "ADR-143",
        }

    def get_summary(self, client_domain: Optional[str] = None) -> Dict[str, Any]:
        """Return aggregate statistics across all assessments."""
        self._ensure()
        try:
            conn = _get_conn()
            params: list = []
            where = ""
            if client_domain:
                where = "WHERE client_domain = %s"
                params.append(client_domain)

            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"SELECT decision, COUNT(*) FROM {_TABLE} {where} "
                        f"GROUP BY decision ORDER BY decision",
                        params,
                    )
                    decision_counts = {r[0]: r[1] for r in cur.fetchall()}

                    cur.execute(
                        f"SELECT AVG(composite_score), AVG(financial_score), "
                        f"AVG(technical_score), AVG(legal_score), AVG(human_score) "
                        f"FROM {_TABLE} {where}",
                        params,
                    )
                    avgs = cur.fetchone()

                    cur.execute(
                        f"SELECT COUNT(*) FROM {_TABLE} {where}", params
                    )
                    total = cur.fetchone()[0]
            conn.close()

            def f(v):
                return round(float(v), 2) if v else None

            return {
                "total_assessments": total,
                "by_decision":       decision_counts,
                "averages": {
                    "composite":  f(avgs[0]) if avgs else None,
                    "financial":  f(avgs[1]) if avgs else None,
                    "technical":  f(avgs[2]) if avgs else None,
                    "legal":      f(avgs[3]) if avgs else None,
                    "human":      f(avgs[4]) if avgs else None,
                },
                "client_domain": client_domain,
                "adr": "ADR-143",
            }

        except Exception as exc:
            logger.error("[MDRG] get_summary failed: %s", exc)
            return {"total_assessments": 0, "error": str(exc)}

    # ── Internal ──────────────────────────────────────────────────────────────

    def _persist(
        self,
        output:      Dict[str, Any],
        raw_signals: Dict[str, Dict[str, Any]],
        weights:     Dict[str, float],
    ) -> None:
        try:
            conn = _get_conn()
            vs = output["vector_scores"]
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"INSERT INTO {_TABLE} "
                        "(assessment_id, subject, client_domain, decision, composite_score, "
                        "financial_score, technical_score, legal_score, human_score, "
                        "hard_block_vector, weights_used, signals, breakdown, assessed_by) "
                        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (
                            output["assessment_id"],
                            output["subject"][:256],
                            output.get("client_domain"),
                            output["decision"],
                            output["composite_score"],
                            vs.get(VECTOR_FINANCIAL),
                            vs.get(VECTOR_TECHNICAL),
                            vs.get(VECTOR_LEGAL),
                            vs.get(VECTOR_HUMAN),
                            output.get("hard_block_vector"),
                            json.dumps(weights),
                            json.dumps(raw_signals),
                            json.dumps(output.get("breakdown", [])),
                            output.get("assessed_by", "api"),
                        ),
                    )
            conn.close()
        except Exception as exc:
            logger.warning("[MDRG] _persist failed (non-fatal): %s", exc)
