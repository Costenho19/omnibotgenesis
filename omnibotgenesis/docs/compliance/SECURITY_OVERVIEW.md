# OMNIX — Security Overview

**Classification**: Public — Pitch & Investor Distribution  
**Last Updated**: February 2026

---

## Security Posture

OMNIX Decision Governance Infrastructure implements institutional-grade security controls across its entire API surface. The platform has passed internal security hardening and stress validation across all production endpoints with **zero information leakage** under sustained load conditions.

---

## Security Controls

| Area | Status |
|------|--------|
| HTTP Security Headers | Industry-standard headers enforced on all endpoints |
| Error Response Sanitization | No internal details exposed in any error response |
| Log Redaction | Automated redaction of sensitive patterns in all application logs |
| Rate Limiting | Per-IP request throttling with configurable thresholds |
| Authentication | Session-based access control with configurable credentials for production |
| Server Identity | Production server identity concealed from external fingerprinting |
| Cache Control | Sensitive data never cached by intermediaries or browsers |
| Audit Correlation | Every request tagged with a unique reference ID for traceability |

---

## Cryptographic Architecture

OMNIX implements NIST-standardized post-quantum cryptographic algorithms for decision signing and key exchange. Every automated decision is cryptographically signed before execution, providing non-repudiation, tamper-evidence, and a quantum-resistant audit trail.

This capability has been operational since November 2025.

---

## Decision Governance Security

The 6-checkpoint governance architecture provides inherent security through independent validation layers. Each checkpoint can autonomously block a decision, ensuring no single point of failure in the governance chain.

This architecture is domain-agnostic and applies across verticals: capital allocation, credit/lending, insurance underwriting, and supply chain governance.

---

## Compliance Alignment

OMNIX security controls are aligned with core principles of:

- **GDPR** — Data protection and PII handling
- **SOC 2 Security Principles** — Access control, audit logging, encryption
- **MiFID II** — Decision auditability and traceability
- **DORA** — Operational resilience and error isolation

---

## Validation

OMNIX has undergone internal security stress testing and audit. Detailed findings, remediation evidence, and test artifacts are available under NDA in the technical data room.

---

*OMNIX Decision Governance Infrastructure*  
*Security Overview — For authorized distribution*
