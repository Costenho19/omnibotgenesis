# ADR-083: Enterprise Bot Security Middleware

**Status:** ACCEPTED  
**Date:** April 2026  
**Author:** Harold Nunes, OMNIX QUANTUM LTD  
**Scope:** `omnix_services/security/bot_security.py` · `omnix_services/telegram_service/enterprise_bot.py` · `omnix_services/telegram_service/commands/governance_commands.py`

---

## Context

A security audit of the OMNIX Telegram bot identified 8 vulnerabilities across 3 severity
tiers. The bot had no input validation layer, no per-user rate limiting, no prompt injection
defense, and no user blocklist. These gaps created risks for AI cost abuse, DoS attacks,
data leakage, and prompt injection by malicious users.

---

## Vulnerabilities addressed

| ID | Severity | Description |
|----|----------|-------------|
| C1 | CRITICAL | Prompt injection via `user_message` injected directly into AI prompt |
| C2 | CRITICAL | No per-user rate limiting — AI cost + DoS risk |
| C3 | HIGH | No message length enforcement — unbounded AI token consumption |
| C4 | HIGH | Unbounded `_message_buffers` memory leak per user |
| C5 | HIGH | Bot responds in group chats without restriction |
| M1 | MEDIUM | Internal error details (stack traces) leaked to users |
| M2 | MEDIUM | No user blocklist — no way to stop abusive users |
| M3 | MEDIUM | DB auto-registration of unlimited users — flood risk |
| L1 | LOW | Unguarded YouTube/URL fetch — SSRF risk surface |

---

## Decision

A `BotSecurityMiddleware` class is the single entry point for all security checks.
Every message passes through it before reaching the AI or any handler.

### Architecture

```
User message (Telegram)
    ↓
BotSecurityMiddleware.check(user_id, chat_type, raw_message)
    ↓
1. Blocklist check          → blocked? → "Tu acceso ha sido suspendido"
2. Group chat restriction   → group? → "Solo chats privados"
3. Rate limiting (sliding window)
   - 10 messages / 60 s
   - 3 burst / 5 s
   - Cooldown: 30 s on violation
4. Message length truncation (≤ 1500 chars)
5. Prompt injection detection (20+ regex patterns)
   - Injection → keywords sanitized + auto-block after 3rd attempt
6. SSRF-risky URL detection
   - Localhost / RFC-1918 / file:// / gopher:// → [URL_BLOCKED]
    ↓
SecurityCheckResult
    ↓
Bot uses result.sanitized_message for AI processing
```

### Prompt injection patterns (20+ patterns)

Patterns detected and neutralized (partial list):
- `ignore all previous instructions`
- `forget your instructions` / `override your directives`
- `you are now [X]` / `act as [X]` (where X is not OMNIX)
- `new system prompt` / `jailbreak` / `DAN mode`
- `developer mode` / `sudo mode` / `admin mode`
- XML injection: `<system>` / `[system]` / `### system`
- Finance-specific: `approve this trade without confirmation` / `skip the governance checkpoint`

### Rate limiting (RateLimiter class)

| Parameter | Value |
|-----------|-------|
| Window | 60 seconds (sliding) |
| Max messages | 10 per window |
| Burst window | 5 seconds |
| Max burst | 3 messages |
| Cooldown on violation | 30 seconds |
| Auto-block threshold | 3 injection attempts |

### Memory protection

- `_message_buffers`: capped at 5 messages per user (`MAX_BUFFER_PER_USER`)
- `_conversation_history`: capped at 30 turns per user (`MAX_HISTORY_PER_USER`)

### Error sanitization

`safe_error_reply()` — always returns a generic message to the user. The real error is
logged internally with `[SECURITY]` prefix. Users never see stack traces or internal state.

---

## Addendum — `/impact` command (Governance Impact Score)

The `/impact` command was added as part of ADR-083 to give Harold and admin users a
real-time view of the governance pipeline's impact across all domains.

### Governance Impact Score (GIS) formula

```
GIS (0-100) =
  70                                      (base: pipeline operational)
  + min(15, containment_rate × 0.15)      (up to +15 for risk containment)
  + min(10, domains_active × 1.4)         (up to +10 for active domains)
  + 5 if total_decisions > 1000           (+5 for sustained volume)
```

### Output

```
┌─ GIS: 94/100 ───────────────────┐
│ █████████░ │
└──────────────────────────────────┘

📊 DECISIONES — Últimos 7 días
  Trading        ✅ 42 aprobadas  🔴 8 bloqueadas
  Crédito        ✅ 31 aprobadas  🔴 5 bloqueadas
  ...

📈 RESUMEN GLOBAL (histórico)
  Evaluaciones totales:  1,012,500
  BLOCKED:                 287,000 (28.4% contención)
  APPROVED:                725,500
```

### Access
- `/impact` — registered in `enterprise_bot.py` as a CommandHandler
- Available to all users (no admin restriction)

---

## Files

| File | Role |
|------|------|
| `omnix_services/security/bot_security.py` | `BotSecurityMiddleware`, `RateLimiter`, `InputSanitizer`, `UserBlocklist`, `safe_error_reply` |
| `omnix_services/telegram_service/enterprise_bot.py` | Middleware initialization (lines 506–512), security check in `handle_message` (line 3444), `/impact` handler (line 980) |
| `omnix_services/telegram_service/commands/governance_commands.py` | `impact_command()` — GIS calculation + multi-domain DB queries |

---

## References

- ADR-052: Brute force lockout (B2B API complement)
- ADR-061: Persistent IP blocklist (web API complement)
- ADR-082: W3C Verifiable Credentials (bot-side output complement)
