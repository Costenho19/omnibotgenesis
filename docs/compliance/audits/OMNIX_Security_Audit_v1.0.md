# OMNIX Decision Governance — Security Audit Report v1.0

**Classification**: Confidential — Investor Due Diligence  
**Audit Date**: February 20, 2026  
**Auditor**: OMNIX Security Engineering  
**Scope**: Dashboard API Security Hardening & Stress Validation  
**Internal Build Reference**: 6.5.4e  

---

## Executive Summary

This report documents the institutional-grade security hardening applied to the OMNIX Decision Governance Dashboard infrastructure. The audit covers HTTP security headers, error response sanitization, log redaction, rate limiting, and performance stress testing across all 20 production API endpoints.

**Overall Status: READY**

| Area | Status | Details |
|------|--------|---------|
| Security Headers | PASS | 9/9 required headers present on all endpoints |
| Error Sanitization | PASS | Zero information leakage across all tested endpoints |
| Log Redaction | PASS | 10+ secret patterns actively redacted |
| Rate Limiting | ACTIVE | 300 requests/minute per IP (configurable) |
| Authentication | ACTIVE | Session-based auth + optional Basic Auth for production |
| Performance | PASS | 233.9 req/s sustained, p50 < 57ms |
| Post-Quantum Cryptography | ACTIVE | Dilithium-3 signing + Kyber-768 encapsulation (since Nov 2025) |

---

## 1. Security Controls Matrix

### 1.1 HTTP Security Headers

All API endpoints return the following security headers:

| Header | Value | Purpose | Status |
|--------|-------|---------|--------|
| Strict-Transport-Security | max-age=31536000; includeSubDomains | Force HTTPS for 1 year | ACTIVE |
| Content-Security-Policy | default-src 'self'; script-src [CDN allowlist incl. Plotly, Tailwind, cdnjs]; frame-ancestors 'self' | XSS prevention, framing protection | ACTIVE |
| X-Content-Type-Options | nosniff | MIME type sniffing prevention | ACTIVE |
| X-Frame-Options | SAMEORIGIN | Clickjacking protection | ACTIVE |
| X-XSS-Protection | 1; mode=block | Browser XSS filter | ACTIVE |
| Referrer-Policy | strict-origin-when-cross-origin | Information leakage prevention | ACTIVE |
| Permissions-Policy | camera=(), microphone=(), geolocation=(), payment=() | Feature restriction | ACTIVE |
| Cache-Control | no-store, no-cache, must-revalidate, max-age=0 | Prevent sensitive data caching | ACTIVE |
| X-Request-ID | UUID per request | Audit trail correlation | ACTIVE |

### 1.2 Server Identity Concealment

| Control | Status | Notes |
|---------|--------|-------|
| Server header override | ACTIVE | Displays "OMNIX-DGI" in production (Gunicorn) |
| X-Powered-By removal | ACTIVE | Stripped from all responses |
| Version fingerprinting | MITIGATED | Dev server (Werkzeug) still visible in development only |

### 1.3 Error Response Sanitization

All HTTP error responses (400, 401, 403, 404, 429, 500, 503) return standardized JSON:

```json
{
  "error": "Sanitized message",
  "status": 500,
  "reference": "a1b2c3d4"
}
```

**Sanitization rules applied:**
- Stack traces stripped (Traceback patterns)
- Internal file paths removed (/home/, /app/, /usr/)
- Environment variable names redacted (TOKEN, KEY, SECRET, URL patterns)
- Python exception types replaced with generic messages
- Database connection strings masked
- Configuration instructions removed
- Maximum 200 characters enforced

### 1.4 Log Redaction System

The `SecretRedactionFilter` automatically redacts the following patterns from all application logs:

| Pattern | Example | Redacted To |
|---------|---------|-------------|
| OpenAI API keys | sk-abc123... | [REDACTED_OPENAI_KEY] |
| Google API keys | AIzaSyB... | [REDACTED_GOOGLE_KEY] |
| Telegram bot tokens | 123456:ABC... | [REDACTED_TELEGRAM_TOKEN] |
| GitHub tokens | ghp_abc... | [REDACTED_GITHUB_TOKEN] |
| PostgreSQL URLs | postgres://user:pass@... | [REDACTED_DB_URL] |
| Redis URLs | redis://... | [REDACTED_REDIS_URL] |
| MongoDB URLs | mongodb://... | [REDACTED_MONGODB_URL] |
| Generic passwords | password=secret | password=[REDACTED] |
| Generic tokens | token=abc123 | token=[REDACTED] |
| Generic secrets | secret=xyz | secret=[REDACTED] |
| Authorization headers | Bearer abc123 | Bearer [REDACTED] |

### 1.5 Rate Limiting

| Parameter | Value | Configurable |
|-----------|-------|--------------|
| Default limit | 300 requests/minute per IP | DASHBOARD_RATE_LIMIT env var |
| Rate limit header | X-RateLimit-Limit | Included in all responses |
| Exempt paths | /api/health (healthchecks) | Hardcoded |
| 429 response | JSON with reference ID | Automatic |

### 1.6 Authentication

| Mode | Mechanism | Environment |
|------|-----------|-------------|
| Session Auth | Cookie-based via /terminal | Development + Production |
| Basic Auth | HTTP Basic (DASHBOARD_USER/DASHBOARD_PASSWORD) | Production (optional) |
| IP Allowlist | DASHBOARD_IP_ALLOWLIST env var | Production (optional) |
| Fail-Closed | 503 if auth required but not configured | Railway production |

---

## 2. Findings and Remediation

### 2.1 FINDING: /api/system/quarantine Information Leakage (REMEDIATED)

**Severity**: HIGH  
**Status**: FIXED  

**Before**: The quarantine endpoint returned a 500 error with internal error messages that revealed environment variable names (TELEGRAM_BOT_TOKEN), configuration file paths (.env.local), and setup instructions.

```json
// BEFORE (VULNERABLE)
{
  "error": "❌ VARIABLE REQUERIDA NO ENCONTRADA: TELEGRAM_BOT_TOKEN\nPor favor configura TELEGRAM_BOT_TOKEN en Replit Secrets o .env.local",
  "success": false
}
```

**After**: The endpoint now returns a clean 503 response when dependencies are unavailable:

```json
// AFTER (SECURED)
{
  "error": "Feature unavailable",
  "reason": "Required service not configured",
  "success": false,
  "reference": "e7588769"
}
```

**Remediation**: Added explicit `ImportError`, `ValueError`, and `RuntimeError` handlers that return 503 with sanitized messages. Generic Exception handler returns 500 with "Internal server error" only.

### 2.2 FINDING: Raw Error Messages in Blueprint Handlers (REMEDIATED)

**Severity**: MEDIUM  
**Status**: FIXED  

**Before**: Multiple blueprint handlers returned `str(e)` in error responses, potentially leaking internal Python exception details, module names, and database error messages.

**After**: The `after_request` security middleware intercepts all JSON error responses (status >= 400) and applies the `_sanitize_error_message` function, which:
1. Detects and blocks Traceback, ModuleNotFoundError, psycopg patterns (returns generic "Internal server error")
2. Strips file paths, environment variable names, Python exception types
3. Redacts database connection strings
4. Limits message length to 200 characters
5. Attaches a reference ID for internal correlation

### 2.3 FINDING: Server Version Fingerprinting (PARTIALLY REMEDIATED)

**Severity**: LOW  
**Status**: MITIGATED (dev only)  

**Details**: Flask's development server (Werkzeug) adds the Server header at the WSGI level, overriding application-level removal. In production (Gunicorn on Railway), the `after_request` handler successfully sets `Server: OMNIX-DGI`.

**Risk**: Development environment only. No impact on production deployment.

---

## 3. Stress Test Evidence

### 3.1 Test Configuration

| Parameter | Value |
|-----------|-------|
| Total Requests | 2,000 |
| Concurrent Workers | 50 |
| Duration | 8.55 seconds |
| Throughput | 233.9 requests/second |
| Target | http://localhost:5000 (all 20 endpoints) |

### 3.2 Latency Percentiles (milliseconds)

| Endpoint | p50 | p95 | p99 | Error Rate |
|----------|-----|-----|-----|------------|
| /api/health | 5.7 | 36.7 | 70.0 | 0.0% |
| /api/core/trades | 55.3 | 631.1 | 720.4 | 0.0% |
| /api/core/performance | 57.2 | 636.5 | 716.9 | 0.0% |
| /api/core/balance | 56.0 | 632.2 | 727.9 | 0.0% |
| /api/core/decisions | 53.1 | 628.2 | 706.3 | 0.0% |
| /api/core/portfolio | 48.6 | 642.0 | 780.0 | 0.0% |
| /api/core/equity_curve | 47.6 | 625.2 | 742.6 | 0.0% |
| /api/core/win_rate_dual | 47.3 | 632.1 | 736.8 | 0.0% |
| /api/core/pnl_breakdown | 44.8 | 100.7 | 808.5 | 0.0% |
| /api/core/drawdown_chart | 43.5 | 102.7 | 1293.1 | 0.0% |
| /api/market/btc | 44.6 | 128.7 | 1281.7 | 0.0% |
| /api/market/sentiment | 42.3 | 116.0 | 761.6 | 0.0% |
| /api/market/time_heatmap | 43.1 | 632.8 | 778.7 | 0.0% |
| /api/intelligence/shadow | 43.6 | 98.3 | 1349.3 | 0.0% |
| /api/intelligence/learning | 41.6 | 84.3 | 755.6 | 0.0% |
| /api/intelligence/regime | 43.2 | 645.4 | 787.2 | 0.0% |
| /api/intelligence/correlation_heatmap | 43.1 | 109.7 | 743.2 | 0.0% |
| /api/intelligence/dci | 40.5 | 100.6 | 738.9 | 0.0% |
| /api/system/version | 41.3 | 114.1 | 734.7 | 0.0% |
| /api/system/quarantine | 9.8 | 53.7 | 119.2 | 100.0% (503 expected) |

### 3.3 Security Verification Results

| Check | Result |
|-------|--------|
| Security headers present on all 20 endpoints | PASS |
| No information leakage in error responses | PASS (0 leaks detected) |
| No Traceback strings in any response | PASS |
| No API keys/tokens in any response | PASS |
| No internal file paths in any response | PASS |
| No database URLs in any response | PASS |
| No environment variable names in error responses | PASS |
| Quarantine returns 503 (not 500) when service unavailable | PASS |

### 3.4 Information Leakage Scan

The stress test scanned all endpoint responses for 14 leak patterns including:
- Python tracebacks and file references
- OpenAI/Google/GitHub/Telegram API key patterns
- Database connection strings (PostgreSQL, Redis, MongoDB)
- Internal path references (/home/runner/, /app/)
- Environment variable names in error context

**Result: ZERO leaks detected across 2,000 requests.**

---

## 4. Endpoint Status Summary

| Endpoint | Status | Category | Notes |
|----------|--------|----------|-------|
| /api/health | 200 OK | System | Healthcheck (no auth required) |
| /api/core/trades | 200 OK | Core | Session auth required |
| /api/core/performance | 200 OK | Core | Session auth required |
| /api/core/balance | 200 OK | Core | Session auth required |
| /api/core/decisions | 200 OK | Core | Session auth required |
| /api/core/portfolio | 200 OK | Core | Session auth required |
| /api/core/equity_curve | 200 OK | Core | Session auth required |
| /api/core/win_rate_dual | 200 OK | Core | Session auth required |
| /api/core/pnl_breakdown | 200 OK | Core | Session auth required |
| /api/core/drawdown_chart | 200 OK | Core | Session auth required |
| /api/market/btc | 200 OK | Market | Session auth required |
| /api/market/sentiment | 200 OK | Market | Session auth required |
| /api/market/time_heatmap | 200 OK | Market | Session auth required |
| /api/intelligence/shadow | 200 OK | Intelligence | Session auth required |
| /api/intelligence/learning | 200 OK | Intelligence | Session auth required |
| /api/intelligence/regime | 200 OK | Intelligence | Session auth required |
| /api/intelligence/correlation_heatmap | 200 OK | Intelligence | Session auth required |
| /api/intelligence/dci | 200 OK | Intelligence | Session auth required |
| /api/system/version | 200 OK | System | Session auth required |
| /api/system/quarantine | 503 | System | Expected (bot token not in dashboard env) |

---

## 5. Architecture Security Features

### 5.1 Post-Quantum Cryptography (Active Since November 2025)

OMNIX implements NIST-approved post-quantum cryptographic algorithms:

| Algorithm | Purpose | Standard |
|-----------|---------|----------|
| CRYSTALS-Dilithium Level 3 | Digital signatures (trade order signing) | FIPS 204 |
| CRYSTALS-Kyber-768 | Key encapsulation (secure key exchange) | FIPS 203 |

All trading decisions are cryptographically signed before execution, providing:
- Non-repudiation of automated decisions
- Tamper-evident decision audit trail
- Quantum-resistant security posture

### 5.2 Decision Governance Architecture

The 6-checkpoint veto architecture provides inherent security through decision validation:

1. **Monte Carlo Simulation** — Statistical validation of trade viability
2. **Risk Management System** — Position sizing and exposure limits
3. **Adaptive Coherence Gate** — Signal quality filtering
4. **Edge Confirmation Window** — Temporal persistence verification
5. **Scoring Engine** — Multi-factor signal aggregation
6. **Final Decision Gate** — Consensus-based execution authorization

Each checkpoint can independently VETO a decision, ensuring no single point of failure in the governance chain.

---

## 6. Compliance Posture

| Regulation | Relevance | Status |
|------------|-----------|--------|
| GDPR (Data Protection) | User data handling | Controls in place (log redaction, no PII in errors) |
| SOC 2 Type I (Security) | Security controls | Aligned (access control, audit logging, encryption) |
| MiFID II (Financial) | Decision auditability | Supported (decision_trace, PQC signatures) |
| DORA (Digital Resilience) | Operational resilience | Rate limiting, error isolation, graceful degradation |

---

## 7. Recommendations

### Immediate (Pre-Investment)
- [x] Security headers on all endpoints
- [x] Error response sanitization
- [x] Log redaction system
- [x] Rate limiting
- [x] Quarantine endpoint remediated

### Short-Term (Post-Investment)
- [ ] WAF integration (Cloudflare or AWS WAF)
- [ ] Automated security scanning in CI/CD pipeline
- [ ] SOC 2 Type II certification process
- [ ] Penetration testing by independent firm
- [ ] SIEM integration for security event correlation

### Long-Term
- [ ] ISO 27001 certification
- [ ] Bug bounty program
- [ ] Hardware Security Module (HSM) integration for PQC key management
- [ ] Zero-trust network architecture

---

## Appendix A: Test Artifacts

| Artifact | Location |
|----------|----------|
| Stress test script | `scripts/omnix_stress_audit.py` |
| Full results (JSON) | `output/stress_results.json` |
| Summary report | `output/stress_summary.md` |
| Security middleware | `omnix_dashboard/utils/auth.py` |
| PQC implementation | `omnix_core/security/pqc_security.py` |
| This audit report | `docs/compliance/audits/OMNIX_Security_Audit_v1.0.md` |

---

*OMNIX Decision Governance Infrastructure — Security Audit Report v1.0*  
*Confidential — For authorized investor due diligence purposes only*
