"""
OMNIX Governance Reporting Engine — Module 5 of 5 Governance Compliance Modules.

Aligns with:
- NIST AI RMF: GOVERN function (governance, accountability, and transparency)
- ISO/IEC 42001: Clause 10 (Improvement) + Annex A.6 (AI system impact assessment)
- EU AI Act: Article 12 (Record-keeping — traceability and logs for high-risk AI)

Generates structured compliance reports with full decision lineage, suitable
for regulatory submission under EU AI Act Article 12 requirements.

ADR-029: Governance Compliance Modules
"""

import csv
import hashlib
import io
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger("OMNIX.Governance.Reporting")


def _get_conn():
    return psycopg.connect(os.environ["DATABASE_URL"])


class GovernanceReportingEngine:
    """
    Compliance report generator with full decision lineage tracing.

    Reports include:
    - Executive summary (evaluation counts, outcomes, overrides, incidents)
    - Risk maps in effect during the period
    - Performance metrics by checkpoint
    - Drift alerts
    - Human oversight override log
    - Incident summary by severity
    - Decision lineage samples (receipt → checkpoints → veto chain → override → verification URL)

    EU AI Act Art. 12 compliance: All records necessary to assess AI system
    conformity are captured in exportable, hash-verified reports.
    """

    def generate_report(
        self,
        client_id: str,
        period_start: datetime,
        period_end: datetime,
        report_type: str = "COMPLIANCE",
        generated_by: str = "system",
    ) -> dict[str, Any]:
        """Generate a full compliance report for the specified period."""
        conn = _get_conn()
        try:
            report_data = self._collect_report_data(conn, client_id, period_start, period_end)
        finally:
            conn.close()

        report_json = json.dumps(report_data, default=str, sort_keys=True)
        content_hash = "sha256:" + hashlib.sha256(report_json.encode("utf-8")).hexdigest()

        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)
            cur.execute(
                """
                INSERT INTO governance_reports
                    (client_id, period_start, period_end, report_type, content_json, content_hash, generated_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (
                    client_id, period_start, period_end,
                    report_type, json.dumps(report_data, default=str),
                    content_hash, generated_by,
                ),
            )
            row = cur.fetchone()
            conn.commit()
            report_id = str(row["id"])
            created_at = row["created_at"].isoformat()
        finally:
            conn.close()

        logger.info(
            f"[REPORT] generated id={report_id} client={client_id} "
            f"period={period_start.date()}→{period_end.date()} type={report_type}"
        )

        return {
            "report_id": report_id,
            "client_id": client_id,
            "report_type": report_type,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "created_at": created_at,
            "content_hash": content_hash,
            "generated_by": generated_by,
            "regulatory_framework": "NIST AI RMF GOVERN | ISO 42001 §10 | EU AI Act Art. 12",
            "data": report_data,
        }

    def _collect_report_data(
        self,
        conn,
        client_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> dict[str, Any]:
        """Collect all data sections for the compliance report."""
        cur = conn.cursor(row_factory=dict_row)

        # 1. Decision receipts summary
        cur.execute(
            """
            SELECT decision, COUNT(*) as count
            FROM decision_receipts
            WHERE client_id=%s AND created_at BETWEEN %s AND %s
            GROUP BY decision
            """,
            (client_id, period_start, period_end),
        )
        decision_counts: dict[str, int] = {}
        for row in cur.fetchall():
            decision_counts[row["decision"]] = int(row["count"])
        total_evaluations = sum(decision_counts.values())

        # 2. Decision lineage samples (5 representative)
        cur.execute(
            """
            SELECT receipt_id, timestamp_utc, asset, decision, veto_chain, created_at
            FROM decision_receipts
            WHERE client_id=%s AND created_at BETWEEN %s AND %s
            ORDER BY created_at DESC LIMIT 5
            """,
            (client_id, period_start, period_end),
        )
        lineage_samples = []
        for row in cur.fetchall():
            r = dict(row)
            for f in ("timestamp_utc", "created_at"):
                if r.get(f):
                    r[f] = r[f].isoformat()
            r["verifiable_at"] = f"https://omnibotgenesis-production.up.railway.app/api/verify/{r['receipt_id']}"
            lineage_samples.append(r)

        # 3. Risk maps
        cur.execute(
            "SELECT use_case, classification, impact_financial, impact_operational, impact_regulatory, updated_at FROM governance_risk_map WHERE client_id=%s ORDER BY classification",
            (client_id,),
        )
        risk_maps = []
        for row in cur.fetchall():
            r = dict(row)
            if r.get("updated_at"):
                r["updated_at"] = r["updated_at"].isoformat()
            risk_maps.append(r)

        # 4. Performance metrics
        cur.execute(
            """
            SELECT checkpoint_id, AVG(approval_rate) as avg_approval, AVG(block_rate) as avg_block, COUNT(*) as snapshots
            FROM governance_metrics
            WHERE client_id=%s AND created_at BETWEEN %s AND %s
            GROUP BY checkpoint_id ORDER BY checkpoint_id
            """,
            (client_id, period_start, period_end),
        )
        metrics_summary = []
        for row in cur.fetchall():
            r = dict(row)
            for f in ("avg_approval", "avg_block"):
                if r.get(f) is not None:
                    r[f] = float(r[f])
            metrics_summary.append(r)

        # 5. Drift alerts
        cur.execute(
            """
            SELECT signal_name, alert_level, drift_score, detected_at
            FROM governance_drift_log
            WHERE client_id=%s AND created_at BETWEEN %s AND %s AND alert_level IN ('ALERT','WARNING')
            ORDER BY detected_at DESC LIMIT 20
            """,
            (client_id, period_start, period_end),
        )
        drift_alerts = []
        for row in cur.fetchall():
            r = dict(row)
            if r.get("detected_at"):
                r["detected_at"] = r["detected_at"].isoformat()
            r["drift_score"] = float(r["drift_score"]) if r.get("drift_score") else None
            drift_alerts.append(r)

        # 6. Human overrides
        cur.execute(
            """
            SELECT receipt_id, decision_before, decision_after, overridden_by, role, created_at, content_hash, signature_algorithm
            FROM governance_overrides
            WHERE client_id=%s AND created_at BETWEEN %s AND %s
            ORDER BY created_at DESC
            """,
            (client_id, period_start, period_end),
        )
        overrides = []
        for row in cur.fetchall():
            r = dict(row)
            if r.get("created_at"):
                r["created_at"] = r["created_at"].isoformat()
            r["pqc_signed"] = bool(r.get("signature_algorithm") and "UNSIGNED" not in str(r.get("signature_algorithm", "")))
            overrides.append(r)

        # 7. Incidents by severity
        cur.execute(
            """
            SELECT severity, status, COUNT(*) as count
            FROM governance_incidents
            WHERE client_id=%s AND created_at BETWEEN %s AND %s
            GROUP BY severity, status
            ORDER BY severity, status
            """,
            (client_id, period_start, period_end),
        )
        incidents_summary: list[dict] = [dict(r) for r in cur.fetchall()]

        return {
            "report_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "framework": "NIST AI RMF | ISO/IEC 42001 | EU AI Act",
                "eu_ai_act_article": "12 — Record-keeping for high-risk AI systems",
            },
            "executive_summary": {
                "total_evaluations": total_evaluations,
                "decision_breakdown": decision_counts,
                "approval_rate": round(
                    decision_counts.get("APPROVED", 0) / total_evaluations * 100, 2
                ) if total_evaluations > 0 else None,
                "total_overrides": len(overrides),
                "total_incidents": sum(r["count"] for r in incidents_summary),
                "total_drift_alerts": len(drift_alerts),
            },
            "risk_maps": risk_maps,
            "performance_metrics": metrics_summary,
            "drift_alerts": drift_alerts,
            "human_overrides": overrides,
            "incidents_summary": incidents_summary,
            "decision_lineage_samples": lineage_samples,
        }

    def get_report(self, report_id: str, client_id: str) -> dict | None:
        """Retrieve a stored compliance report by ID (client isolation enforced)."""
        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)
            cur.execute(
                "SELECT * FROM governance_reports WHERE id=%s AND client_id=%s",
                (report_id, client_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            row = dict(row)
            row["id"] = str(row["id"])
            for f in ("period_start", "period_end", "created_at"):
                if row.get(f):
                    row[f] = row[f].isoformat()
            return row
        finally:
            conn.close()

    def list_reports(self, client_id: str, limit: int = 20) -> list[dict]:
        """List report metadata (without full content_json) for a client."""
        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)
            cur.execute(
                """
                SELECT id, client_id, period_start, period_end, report_type, content_hash, generated_by, created_at
                FROM governance_reports
                WHERE client_id=%s
                ORDER BY created_at DESC LIMIT %s
                """,
                (client_id, limit),
            )
            rows = [dict(r) for r in cur.fetchall()]
            for row in rows:
                row["id"] = str(row["id"])
                for f in ("period_start", "period_end", "created_at"):
                    if row.get(f):
                        row[f] = row[f].isoformat()
            return rows
        finally:
            conn.close()

    def export_csv(self, report_id: str, client_id: str) -> str | None:
        """
        Export the decision lineage section of a report as CSV.
        Returns CSV string or None if report not found.
        """
        report = self.get_report(report_id, client_id)
        if not report:
            return None

        content = report.get("content_json") or {}
        samples = content.get("decision_lineage_samples", [])

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["receipt_id", "timestamp_utc", "asset", "decision", "veto_chain", "created_at", "verifiable_at"],
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in samples:
            if isinstance(row.get("veto_chain"), list):
                row["veto_chain"] = "|".join(row["veto_chain"])
            writer.writerow(row)

        return output.getvalue()

    def build_lineage(self, receipt_id: str, client_id: str) -> dict[str, Any]:
        """
        Build complete decision lineage for a single receipt:
        signal → checkpoints → veto_chain → decision → override (if any) → verification URL

        EU AI Act Art. 12: Full traceability from input to output.
        """
        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)

            cur.execute(
                """
                SELECT receipt_id, timestamp_utc, asset, decision, veto_chain,
                       policy_version, engine_version, content_hash, signature_algorithm, created_at
                FROM decision_receipts
                WHERE receipt_id=%s AND client_id=%s
                """,
                (receipt_id, client_id),
            )
            receipt = cur.fetchone()
            if not receipt:
                return {"error": f"Receipt '{receipt_id}' not found for this client"}
            receipt = dict(receipt)
            for f in ("timestamp_utc", "created_at"):
                if receipt.get(f):
                    receipt[f] = receipt[f].isoformat()

            cur.execute(
                """
                SELECT id, decision_before, decision_after, overridden_by, role, justification, created_at, signature_algorithm
                FROM governance_overrides
                WHERE receipt_id=%s AND client_id=%s
                ORDER BY created_at DESC LIMIT 1
                """,
                (receipt_id, client_id),
            )
            override = cur.fetchone()
            if override:
                override = dict(override)
                override["id"] = str(override["id"])
                if override.get("created_at"):
                    override["created_at"] = override["created_at"].isoformat()

            return {
                "receipt_id": receipt_id,
                "lineage": {
                    "1_receipt": {
                        "timestamp": receipt.get("timestamp_utc"),
                        "asset": receipt.get("asset"),
                        "policy_version": receipt.get("policy_version"),
                    },
                    "2_checkpoints": {
                        "engine_version": receipt.get("engine_version"),
                        "note": "6-checkpoint fail-closed pipeline (ADR-028)",
                    },
                    "3_decision": {
                        "outcome": receipt.get("decision"),
                        "veto_chain": receipt.get("veto_chain"),
                        "content_hash": receipt.get("content_hash"),
                        "signature_algorithm": receipt.get("signature_algorithm"),
                    },
                    "4_human_oversight": override or {"note": "No human override recorded for this receipt"},
                    "5_verification": {
                        "url": f"https://omnibotgenesis-production.up.railway.app/api/verify/{receipt_id}",
                        "public_key_url": "https://omnibotgenesis-production.up.railway.app/api/public_key",
                    },
                },
                "framework": "EU AI Act Art. 12 — full decision traceability",
            }
        finally:
            conn.close()
