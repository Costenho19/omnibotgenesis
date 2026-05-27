"""
OMNIX Incident Management Engine — Module 4 of 5 Governance Compliance Modules.

Aligns with:
- EU AI Act: Article 9 (Risk management system) + Article 62 (Reporting of serious incidents)
- NIST AI RMF: MANAGE function (incident response and recovery)

ADR-029: Governance Compliance Modules
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger("OMNIX.Governance.IncidentManagement")

VALID_SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL")
VALID_STATUSES = ("OPEN", "UNDER_REVIEW", "RESOLVED", "CLOSED")


def _get_conn():
    return psycopg.connect(os.environ["DATABASE_URL"])


def _make_incident_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    short = str(uuid.uuid4()).replace("-", "")[:8].upper()
    return f"INC-{ts}-{short}"


def _serialize_row(row: dict) -> dict:
    for f in ("created_at", "resolved_at", "reviewed_at"):
        if row.get(f):
            row[f] = row[f].isoformat()
    if "id" in row:
        row["id"] = str(row["id"])
    return row


class IncidentManagementEngine:
    """
    Structured incident lifecycle management for AI governance events.

    Supports: reporting, review, resolution tracking, and learning log linkage.

    EU AI Act Art. 9: Requires systematic risk management including incident
    identification, analysis, and corrective action documentation.
    EU AI Act Art. 62: Mandates serious incident reporting to competent authorities.
    """

    def report_incident(
        self,
        client_id: str,
        title: str,
        description: str,
        severity: str,
        related_receipt_id: str | None = None,
        reported_by: str | None = None,
    ) -> dict[str, Any]:
        """Create a new incident report."""
        if severity not in VALID_SEVERITIES:
            raise ValueError(f"severity must be one of {VALID_SEVERITIES}")
        if not title or not title.strip():
            raise ValueError("title is required")

        incident_id = _make_incident_id()

        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)
            cur.execute(
                """
                INSERT INTO governance_incidents
                    (client_id, incident_id, severity, title, description,
                     related_receipt_id, reported_by, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'OPEN')
                RETURNING *
                """,
                (
                    client_id, incident_id, severity,
                    title.strip(), description,
                    related_receipt_id, reported_by,
                ),
            )
            row = dict(cur.fetchone())
            conn.commit()

            logger.info(
                f"[INCIDENT] reported id={incident_id} severity={severity} "
                f"client={client_id} by={reported_by}"
            )
            return _serialize_row(row)
        finally:
            conn.close()

    def add_review(
        self,
        incident_id: str,
        reviewer: str,
        findings: str,
        corrective_actions: list | None = None,
    ) -> dict[str, Any]:
        """Add a review to an existing incident and transition it to UNDER_REVIEW."""
        corrective_actions = corrective_actions or []

        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)

            cur.execute(
                "SELECT incident_id FROM governance_incidents WHERE incident_id = %s",
                (incident_id,),
            )
            if not cur.fetchone():
                raise ValueError(f"Incident '{incident_id}' not found")

            cur.execute(
                """
                INSERT INTO governance_incident_reviews
                    (incident_id, reviewer, findings, corrective_actions)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (incident_id, reviewer, findings, json.dumps(corrective_actions)),
            )
            review = dict(cur.fetchone())

            cur.execute(
                "UPDATE governance_incidents SET status='UNDER_REVIEW' WHERE incident_id=%s AND status='OPEN'",
                (incident_id,),
            )
            conn.commit()

            logger.info(f"[INCIDENT] review added to {incident_id} by {reviewer}")
            return _serialize_row(review)
        finally:
            conn.close()

    def resolve_incident(
        self,
        incident_id: str,
        resolved_by: str,
        resolution_note: str,
    ) -> dict[str, Any]:
        """Mark incident as RESOLVED and store the resolution review."""
        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)

            cur.execute(
                "SELECT incident_id, status FROM governance_incidents WHERE incident_id = %s",
                (incident_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Incident '{incident_id}' not found")
            if row["status"] == "RESOLVED":
                raise ValueError(f"Incident '{incident_id}' is already resolved")

            cur.execute(
                """
                INSERT INTO governance_incident_reviews
                    (incident_id, reviewer, findings, corrective_actions)
                VALUES (%s, %s, %s, %s)
                """,
                (incident_id, resolved_by, resolution_note, json.dumps(["CLOSED"])),
            )

            cur.execute(
                """
                UPDATE governance_incidents
                SET status='RESOLVED', resolved_at=NOW()
                WHERE incident_id=%s
                RETURNING *
                """,
                (incident_id,),
            )
            updated = dict(cur.fetchone())
            conn.commit()

            logger.info(f"[INCIDENT] resolved {incident_id} by {resolved_by}")
            return _serialize_row(updated)
        finally:
            conn.close()

    def list_incidents(
        self,
        client_id: str,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """List incidents for a client with optional filters."""
        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)

            conditions = ["client_id = %s"]
            params: list = [client_id]

            if status:
                if status.upper() not in VALID_STATUSES:
                    raise ValueError(f"status must be one of {VALID_STATUSES}")
                conditions.append("status = %s")
                params.append(status.upper())
            if severity:
                if severity.upper() not in VALID_SEVERITIES:
                    raise ValueError(f"severity must be one of {VALID_SEVERITIES}")
                conditions.append("severity = %s")
                params.append(severity.upper())

            where = " AND ".join(conditions)
            cur.execute(
                f"""
                SELECT id, client_id, incident_id, severity, title, status,
                       related_receipt_id, reported_by, created_at, resolved_at
                FROM governance_incidents
                WHERE {where}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                params + [limit, offset],
            )
            return [_serialize_row(dict(r)) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_incident(self, incident_id: str, client_id: str) -> dict | None:
        """Get incident detail with all reviews (client isolation enforced)."""
        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)

            cur.execute(
                "SELECT * FROM governance_incidents WHERE incident_id=%s AND client_id=%s",
                (incident_id, client_id),
            )
            incident = cur.fetchone()
            if not incident:
                return None
            incident = _serialize_row(dict(incident))

            cur.execute(
                "SELECT * FROM governance_incident_reviews WHERE incident_id=%s ORDER BY reviewed_at ASC",
                (incident_id,),
            )
            incident["reviews"] = [_serialize_row(dict(r)) for r in cur.fetchall()]
            return incident
        finally:
            conn.close()

    def link_to_filter_metrics(self, incident_id: str, client_id: str) -> dict[str, Any]:
        """
        Read-only correlation: find filter_calibration_metrics entries
        near the time of this incident. Suggests potential calibration
        issues that may have contributed to the incident.
        Does NOT modify any table.
        """
        conn = _get_conn()
        try:
            cur = conn.cursor(row_factory=dict_row)

            cur.execute(
                "SELECT created_at FROM governance_incidents WHERE incident_id=%s AND client_id=%s",
                (incident_id, client_id),
            )
            row = cur.fetchone()
            if not row:
                return {"error": "Incident not found"}

            incident_time = row["created_at"]

            cur.execute(
                """
                SELECT filter_name, recommendation, created_at
                FROM filter_calibration_metrics
                WHERE created_at BETWEEN %s - INTERVAL '2 hours' AND %s + INTERVAL '2 hours'
                ORDER BY created_at DESC LIMIT 5
                """,
                (incident_time, incident_time),
            )
            correlations = [dict(r) for r in cur.fetchall()]
            for c in correlations:
                if c.get("created_at"):
                    c["created_at"] = c["created_at"].isoformat()

            return {
                "incident_id": incident_id,
                "incident_time": incident_time.isoformat() if incident_time else None,
                "correlated_filter_events": correlations,
                "correlation_window": "±2 hours",
                "note": "Read-only correlation — filter_calibration_metrics not modified",
                "framework": "EU AI Act Art. 9 — learning log integration for systemic risk management",
            }
        except Exception as e:
            logger.warning(f"filter_calibration_metrics not available: {e}")
            return {
                "incident_id": incident_id,
                "correlated_filter_events": [],
                "note": "filter_calibration_metrics table not accessible in this environment",
            }
        finally:
            conn.close()
