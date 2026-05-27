"""
OMNIX Risk Mapping Engine — Module 1 of 5 Governance Compliance Modules.

Aligns with:
- NIST AI RMF: MAP function (risk identification and classification)
- ISO/IEC 42001: Clause 6.1 (Actions to address risks and opportunities)

ADR-029: Governance Compliance Modules
"""

import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger("OMNIX.Governance.RiskMapping")

VALID_CLASSIFICATIONS = ("CRITICAL", "HIGH", "MEDIUM", "LOW")


def _get_conn():
    return psycopg.connect(os.environ["DATABASE_URL"])


class RiskMappingEngine:
    """
    Domain-agnostic risk classification and threshold mapping engine.

    Allows B2B clients to define and store risk profiles per use case,
    including impact scores across financial, operational, and regulatory
    dimensions. Supports per-client governance threshold customization.

    NIST AI RMF MAP: Identifies, analyzes, and prioritizes AI risks.
    ISO 42001 §6.1: Defines objectives and risk treatment plans.
    """

    def upsert_risk_map(
        self,
        client_id: str,
        use_case: str,
        classification: str,
        impact_financial: int = 50,
        impact_operational: int = 50,
        impact_regulatory: int = 50,
        stakeholders: list | None = None,
        thresholds: dict | None = None,
    ) -> dict[str, Any]:
        """
        Create or update a risk map entry for a client/use_case pair.
        UNIQUE constraint on (client_id, use_case) ensures idempotency.
        """
        if classification not in VALID_CLASSIFICATIONS:
            raise ValueError(f"classification must be one of {VALID_CLASSIFICATIONS}")
        for name, val in [("impact_financial", impact_financial),
                           ("impact_operational", impact_operational),
                           ("impact_regulatory", impact_regulatory)]:
            if not (0 <= val <= 100):
                raise ValueError(f"{name} must be between 0 and 100, got {val}")

        stakeholders = stakeholders or []
        thresholds = thresholds or {}

        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)
            cur.execute(
                """
                INSERT INTO governance_risk_map
                    (client_id, use_case, classification, impact_financial,
                     impact_operational, impact_regulatory, stakeholders, thresholds, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (client_id, use_case) DO UPDATE SET
                    classification     = EXCLUDED.classification,
                    impact_financial   = EXCLUDED.impact_financial,
                    impact_operational = EXCLUDED.impact_operational,
                    impact_regulatory  = EXCLUDED.impact_regulatory,
                    stakeholders       = EXCLUDED.stakeholders,
                    thresholds         = EXCLUDED.thresholds,
                    updated_at         = NOW()
                RETURNING *
                """,
                (
                    client_id, use_case, classification,
                    impact_financial, impact_operational, impact_regulatory,
                    json.dumps(stakeholders), json.dumps(thresholds),
                ),
            )
            row = dict(cur.fetchone())
            conn.commit()
            for f in ("created_at", "updated_at"):
                if row.get(f):
                    row[f] = row[f].isoformat()
            row["id"] = str(row["id"])
            logger.info(f"[RISK_MAP] upserted client={client_id} use_case={use_case} classification={classification}")
            return row
        finally:
            conn.close()

    def get_risk_map(self, client_id: str, use_case: str | None = None) -> list[dict]:
        """Return risk maps for the client, optionally filtered by use_case."""
        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)
            if use_case:
                cur.execute(
                    "SELECT * FROM governance_risk_map WHERE client_id=%s AND use_case=%s ORDER BY updated_at DESC",
                    (client_id, use_case),
                )
            else:
                cur.execute(
                    "SELECT * FROM governance_risk_map WHERE client_id=%s ORDER BY classification, use_case",
                    (client_id,),
                )
            rows = [dict(r) for r in cur.fetchall()]
            for row in rows:
                for f in ("created_at", "updated_at"):
                    if row.get(f):
                        row[f] = row[f].isoformat()
                row["id"] = str(row["id"])
            return rows
        finally:
            conn.close()

    def classify_risk(self, signals: dict[str, float]) -> dict[str, Any]:
        """
        Classify risk level from normalized governance signals (0-100 scale).

        Rules (deterministic, no ML):
        - CRITICAL: probability_score < 30 OR risk_exposure > 80
        - HIGH:     probability_score < 50 OR risk_exposure > 65
        - MEDIUM:   probability_score < 70 OR risk_exposure > 45
        - LOW:      all signals within safe ranges
        """
        prob = signals.get("probability_score", 50)
        risk = signals.get("risk_exposure", 50)
        coherence = signals.get("signal_coherence", 50)
        stress = signals.get("stress_resilience", 50)

        if prob < 30 or risk > 80:
            classification = "CRITICAL"
            reason = f"probability_score={prob:.1f}<30 or risk_exposure={risk:.1f}>80"
        elif prob < 50 or risk > 65:
            classification = "HIGH"
            reason = f"probability_score={prob:.1f}<50 or risk_exposure={risk:.1f}>65"
        elif prob < 70 or risk > 45 or coherence < 40 or stress < 30:
            classification = "MEDIUM"
            reason = f"probability_score={prob:.1f} or risk_exposure={risk:.1f} in medium range"
        else:
            classification = "LOW"
            reason = "All primary signals within safe ranges"

        return {
            "classification": classification,
            "reason": reason,
            "signals_evaluated": {
                "probability_score": prob,
                "risk_exposure": risk,
                "signal_coherence": coherence,
                "stress_resilience": stress,
            },
            "framework": "NIST AI RMF MAP — deterministic rule-based classification",
        }

    def get_thresholds(self, client_id: str, use_case: str) -> dict:
        """
        Return per-client thresholds for a use_case.
        Falls back to OMNIX default checkpoint thresholds if not configured.
        """
        maps = self.get_risk_map(client_id=client_id, use_case=use_case)
        if maps and maps[0].get("thresholds"):
            return maps[0]["thresholds"]
        return {
            "probability_score": {"min": 50, "operator": "gte"},
            "risk_exposure": {"max": 65, "operator": "lte"},
            "signal_coherence": {"min": 55, "operator": "gte"},
            "trend_persistence": {"min": 50, "operator": "gte"},
            "stress_resilience": {"min": 35, "operator": "gte"},
            "logic_consistency": {"min": 40, "operator": "gte"},
            "_source": "OMNIX default checkpoint thresholds (ADR-028)",
        }
