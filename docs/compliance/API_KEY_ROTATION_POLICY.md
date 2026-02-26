# OMNIX Decision Governance — API Key Rotation Policy

**Classification**: Internal — Operations & Security  
**Version**: 1.0  
**Effective Date**: February 25, 2026  
**Last Audit**: February 25, 2026 — Result: CLEAN (zero hardcoded secrets found)  
**Next Review**: May 25, 2026  

---

## 1. Purpose

This policy establishes the formal procedure for managing, auditing, and rotating all API keys and secrets used by the OMNIX system. It documents the current state of credential hygiene and provides a repeatable process for maintaining it.

---

## 2. Current Credential Inventory

All credentials are stored exclusively as environment variables — never hardcoded in source code. Audit of February 25, 2026 confirmed zero hardcoded values across all four source directories (`omnix_core/`, `omnix_services/`, `omnix_dashboard/`, `omnix_web/`).

| Credential | Purpose | Storage | Rotation Tier |
|------------|---------|---------|---------------|
| `KRAKEN_API_KEY` | Live trading execution | Railway Secret | Tier 1 — Quarterly |
| `KRAKEN_SECRET` | Live trading signing | Railway Secret | Tier 1 — Quarterly |
| `TELEGRAM_BOT_TOKEN` | Bot communication | Railway Secret | Tier 1 — Quarterly |
| `DATABASE_URL` | PostgreSQL connection | Railway Secret | Tier 2 — Semi-annual |
| `REDIS_URL` | Cache connection | Railway Secret | Tier 2 — Semi-annual |
| `SESSION_SECRET` | Flask session signing | Railway + Replit Secret | Tier 2 — Semi-annual |
| `OPENAI_API_KEY` | AI inference | Railway Secret | Tier 2 — Semi-annual |
| `GEMINI_API_KEY` | AI inference (primary) | Railway Secret | Tier 2 — Semi-annual |
| `ALPHA_VANTAGE_API_KEY` | Technical indicators | Replit Secret | Tier 3 — Annual |
| `FINNHUB_API_KEY` | Market news | Replit Secret | Tier 3 — Annual |
| `TAVILY_API_KEY` | Web search | Replit Secret | Tier 3 — Annual |

---

## 3. Rotation Tiers

| Tier | Credentials | Frequency | Reason |
|------|-------------|-----------|--------|
| **Tier 1 — Critical** | Trading keys, Bot token | Every 90 days | Direct financial exposure if compromised |
| **Tier 2 — High** | Database, AI services, Session | Every 180 days | Service disruption risk |
| **Tier 3 — Standard** | Data APIs | Every 365 days | Read-only access, limited blast radius |

---

## 4. Rotation Schedule

| Credential | Last Rotated | Next Due | Status |
|------------|-------------|----------|--------|
| `KRAKEN_API_KEY` | Nov 2025 (initial setup) | **May 25, 2026** | ⚠️ Due Q2 2026 |
| `KRAKEN_SECRET` | Nov 2025 (initial setup) | **May 25, 2026** | ⚠️ Due Q2 2026 |
| `TELEGRAM_BOT_TOKEN` | Nov 2025 (initial setup) | **May 25, 2026** | ⚠️ Due Q2 2026 |
| `DATABASE_URL` | Nov 2025 (initial setup) | Aug 25, 2026 | ✅ Current |
| `REDIS_URL` | Nov 2025 (initial setup) | Aug 25, 2026 | ✅ Current |
| `SESSION_SECRET` | Nov 2025 (initial setup) | Aug 25, 2026 | ✅ Current |
| `OPENAI_API_KEY` | Nov 2025 (initial setup) | Aug 25, 2026 | ✅ Current |
| `GEMINI_API_KEY` | Nov 2025 (initial setup) | Aug 25, 2026 | ✅ Current |
| `ALPHA_VANTAGE_API_KEY` | Nov 2025 (initial setup) | Nov 2026 | ✅ Current |
| `FINNHUB_API_KEY` | Nov 2025 (initial setup) | Nov 2026 | ✅ Current |
| `TAVILY_API_KEY` | Nov 2025 (initial setup) | Nov 2026 | ✅ Current |

---

## 5. Standard Rotation Procedure

### 5.1 Pre-Rotation Checklist

- [ ] Confirm bot is in PAPER_MODE=TRUE before rotating trading keys
- [ ] Notify maintenance window (rotation takes ~5 minutes)
- [ ] Have new key ready before deleting old one

### 5.2 Rotation Steps (Railway)

1. Generate new key from the provider's dashboard (Kraken, OpenAI, etc.)
2. Go to Railway → Project → Variables
3. Update the variable value with the new key
4. Trigger a Railway redeploy (automatic on variable change)
5. Verify bot startup logs show `✅ [KEY_NAME]: ***REDACTED***`
6. Confirm bot responds to `/status` command in Telegram
7. Delete the old key from the provider's dashboard
8. Update the "Last Rotated" date in this document

### 5.3 Rotation Steps (Replit Secrets)

1. Generate new key from provider
2. Go to Replit → Secrets tab
3. Update the secret value
4. Restart affected workflows
5. Confirm no errors in workflow logs

---

## 6. Emergency Rotation Procedure

Activate immediately if any of the following occur:

- Suspected key exposure (public repository commit, shared log)
- Unauthorized access detected in Railway logs
- Security researcher disclosure
- Provider notifies of suspicious activity

**Emergency steps:**
1. Revoke the exposed key immediately at the provider
2. Generate a new key
3. Update in Railway/Replit within 15 minutes
4. Check Railway logs for unauthorized use in the last 24 hours
5. Document the incident with timestamp and scope

---

## 7. Audit Log

| Date | Auditor | Scope | Result | Action Taken |
|------|---------|-------|--------|--------------|
| Feb 25, 2026 | Security Audit (internal) | Full source scan — 4 directories | CLEAN — zero hardcoded secrets | None required |

---

## 8. References

- Security Audit Report: `docs/compliance/audits/OMNIX_Security_Audit_v1.0_INTERNAL.md`
- CTO/SRE Audit: `docs/compliance/audits/CTO_SRE_SECURITY_AUDIT_JAN21_2026.md`
- Security Overview (public): `docs/compliance/SECURITY_OVERVIEW.md`
