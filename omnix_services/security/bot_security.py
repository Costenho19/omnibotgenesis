"""
OMNIX Enterprise Bot Security Middleware
=========================================
ADR-083 — Enterprise-grade input validation, rate limiting,
prompt injection defense, and user blocklist for the Telegram bot.

Vulnerabilities addressed:
  [C1] Prompt injection via user_message into AI prompt
  [C2] No per-user rate limiting — AI cost + DoS risk
  [C3] No message length enforcement
  [C4] Unbounded _message_buffers memory leak
  [C5] Bot responds in groups without restriction
  [M1] Internal error details leaked to users
  [M2] No user blocklist
  [M3] DB flooded by auto-registration of unlimited users
  [L1] Unguarded YouTube/URL fetch (SSRF risk surface)
"""

import logging
import re
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

MAX_MESSAGE_LENGTH = 1500          # chars — truncated beyond this
MAX_BUFFER_PER_USER = 5            # messages buffered before oldest is dropped
MAX_HISTORY_PER_USER = 30          # conversation turns kept in memory

# Rate limiting (sliding window per user)
RATE_LIMIT_MESSAGES = 20           # max messages per minute
RATE_LIMIT_WINDOW_SECONDS = 60     # per minute
RATE_LIMIT_BURST = 5               # max back-to-back in 5 s (anti-burst)
RATE_LIMIT_BURST_WINDOW = 5        # seconds for burst window

# Cooldown when limit exceeded (seconds)
RATE_LIMIT_COOLDOWN = 30

# Prompt injection patterns — any match → message sanitized / flagged
_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE | re.DOTALL) for p in [
        r"ignore\s+(all\s+)?(previous|prior|above|preceding)\s+instruction",
        r"forget\s+(all\s+)?(previous|prior|above|your)\s+instruction",
        r"you\s+are\s+now\s+(a\s+)?(?!OMNIX)",
        r"act\s+as\s+(if\s+you\s+(are|were)\s+)?(?!OMNIX)",
        r"new\s+system\s+prompt",
        r"override\s+(your\s+)?(instruction|prompt|rule|directive)",
        r"disregard\s+(your\s+)?(instruction|prompt|rule|guideline)",
        r"bypass\s+(the\s+)?(govern|rule|safety|filter|check|checkpoint)",
        r"you\s+have\s+no\s+(restriction|limit|rule|instruction|constraint)",
        r"print\s+(your|the)\s+(system\s+)?prompt",
        r"reveal\s+(your|the)\s+(system|hidden|internal)\s+(prompt|instruction)",
        r"jailbreak",
        r"dan\s+mode",
        r"developer\s+mode",
        r"sudo\s+mode",
        r"admin\s+mode",
        r"<\s*system\s*>",         # XML-style injection
        r"\[\s*system\s*\]",        # bracket injection
        r"###\s*system",            # markdown injection
        r"---\s*system",
        r"approve\s+(this|the)\s+(trade|decision|operation)\s+without",
        r"execute\s+(this\s+)?(trade|order)\s+now\s+without\s+confirmation",
        r"skip\s+(the\s+)?(governance|checkpoint|validation|approval)",
    ]
]

# Patterns that indicate SSRF-risky URL content to flag in messages
_SSRF_URL_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE) for p in [
        r"https?://(?:localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0|::1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)",
        r"file://",
        r"gopher://",
        r"dict://",
        r"ftp://",
    ]
]

# Safe generic error messages (do NOT expose internals)
_SAFE_ERROR_MSG = "OMNIX no pudo procesar tu solicitud en este momento. Por favor intenta de nuevo."
_RATE_LIMIT_MSG = (
    "⏳ Demasiados mensajes seguidos. "
    f"Por favor espera {RATE_LIMIT_COOLDOWN} segundos antes de continuar."
)
_GROUP_BLOCKED_MSG = (
    "🔒 OMNIX solo atiende en chats privados por razones de seguridad. "
    "Escríbeme directamente."
)


# ─────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────

@dataclass
class SecurityCheckResult:
    allowed: bool = True
    reason: str = ""
    sanitized_message: str = ""
    injection_detected: bool = False
    ssrf_risk: bool = False
    rate_limited: bool = False
    reply_message: Optional[str] = None


@dataclass
class _UserRateState:
    timestamps: deque = field(default_factory=lambda: deque(maxlen=RATE_LIMIT_MESSAGES + 1))
    burst_timestamps: deque = field(default_factory=lambda: deque(maxlen=RATE_LIMIT_BURST + 1))
    cooldown_until: float = 0.0
    total_violations: int = 0


# ─────────────────────────────────────────────
# RATE LIMITER
# ─────────────────────────────────────────────

class RateLimiter:
    """Sliding-window per-user rate limiter with burst detection."""

    def __init__(self):
        self._states: dict[str, _UserRateState] = defaultdict(_UserRateState)

    def check(self, user_id: str) -> Tuple[bool, str]:
        """
        Returns (allowed, reason).
        allowed=False → user should be told to wait.
        """
        now = time.monotonic()
        state = self._states[user_id]

        # Active cooldown?
        if now < state.cooldown_until:
            remaining = int(state.cooldown_until - now)
            return False, f"cooldown:{remaining}s"

        # Evict old timestamps outside the window
        cutoff_main = now - RATE_LIMIT_WINDOW_SECONDS
        while state.timestamps and state.timestamps[0] < cutoff_main:
            state.timestamps.popleft()

        cutoff_burst = now - RATE_LIMIT_BURST_WINDOW
        while state.burst_timestamps and state.burst_timestamps[0] < cutoff_burst:
            state.burst_timestamps.popleft()

        # Check burst first
        if len(state.burst_timestamps) >= RATE_LIMIT_BURST:
            state.cooldown_until = now + RATE_LIMIT_COOLDOWN
            state.total_violations += 1
            logger.warning(f"[SECURITY] Burst limit hit by user {user_id} (violation #{state.total_violations})")
            return False, "burst_limit"

        # Check per-minute limit
        if len(state.timestamps) >= RATE_LIMIT_MESSAGES:
            state.cooldown_until = now + RATE_LIMIT_COOLDOWN
            state.total_violations += 1
            logger.warning(f"[SECURITY] Rate limit hit by user {user_id} (violation #{state.total_violations})")
            return False, "rate_limit"

        state.timestamps.append(now)
        state.burst_timestamps.append(now)
        return True, ""

    def get_violations(self, user_id: str) -> int:
        return self._states[user_id].total_violations

    def reset(self, user_id: str) -> None:
        if user_id in self._states:
            del self._states[user_id]


# ─────────────────────────────────────────────
# INPUT SANITIZER
# ─────────────────────────────────────────────

class InputSanitizer:
    """
    Detects and neutralizes prompt injection attempts and SSRF-risky URLs.
    The original message is preserved for logging; the AI only sees the
    sanitized version.
    """

    @staticmethod
    def sanitize(message: str) -> Tuple[str, bool, bool]:
        """
        Returns (sanitized_message, injection_detected, ssrf_risk).
        """
        if not message:
            return "", False, False

        injection = False
        ssrf = False

        # Enforce length limit FIRST
        if len(message) > MAX_MESSAGE_LENGTH:
            message = message[:MAX_MESSAGE_LENGTH] + "…"

        # Detect injection patterns
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(message):
                injection = True
                logger.warning(
                    f"[SECURITY] Prompt injection pattern detected: {pattern.pattern[:60]}"
                )
                break

        # Detect SSRF-risky URLs
        for pattern in _SSRF_URL_PATTERNS:
            if pattern.search(message):
                ssrf = True
                logger.warning("[SECURITY] SSRF-risk URL detected in message")
                break

        if injection:
            message = re.sub(
                r"(?i)(ignore|forget|override|bypass|disregard|reveal|print|jailbreak|sudo|admin|developer|dan)\s+",
                "[BLOCKED] ",
                message,
            )
            message = re.sub(r"(?i)(system\s+prompt|new\s+prompt|instruction)", "[REDACTED]", message)

        if ssrf:
            message = re.sub(
                r"https?://(?:localhost|127\.\d+|0\.0\.0\.0|192\.168\.|10\.|172\.\d+\.)[^\s]*",
                "[URL_BLOCKED]",
                message,
                flags=re.IGNORECASE,
            )
            message = re.sub(r"(?:file|gopher|dict|ftp)://[^\s]*", "[URL_BLOCKED]", message, flags=re.IGNORECASE)

        return message, injection, ssrf


# ─────────────────────────────────────────────
# USER BLOCKLIST
# ─────────────────────────────────────────────

class UserBlocklist:
    """
    In-memory blocklist for the lifetime of the bot process.
    Persistent bans require a DB-backed store (future ADR).
    """

    def __init__(self):
        self._blocked: Set[str] = set()

    def block(self, user_id: str, reason: str = "") -> None:
        self._blocked.add(str(user_id))
        logger.warning(f"[SECURITY] User {user_id} added to blocklist. Reason: {reason}")

    def unblock(self, user_id: str) -> None:
        self._blocked.discard(str(user_id))
        logger.info(f"[SECURITY] User {user_id} removed from blocklist")

    def is_blocked(self, user_id: str) -> bool:
        return str(user_id) in self._blocked

    @property
    def count(self) -> int:
        return len(self._blocked)


# ─────────────────────────────────────────────
# ERROR SANITIZER
# ─────────────────────────────────────────────

def safe_error_reply(error: Exception, user_facing: bool = True) -> str:
    """
    Always return a generic message to the user.
    Log the real error internally.
    """
    logger.error(f"[SECURITY] Internal error (not shown to user): {type(error).__name__}: {error}")
    if user_facing:
        return _SAFE_ERROR_MSG
    return ""


# ─────────────────────────────────────────────
# MAIN MIDDLEWARE
# ─────────────────────────────────────────────

class BotSecurityMiddleware:
    """
    Single entry point for all security checks.

    Usage in handle_message:
        result = security.check(user_id, chat_type, raw_message)
        if not result.allowed:
            await update.message.reply_text(result.reply_message)
            return
        # Use result.sanitized_message for AI processing
    """

    def __init__(self, allow_groups: bool = False):
        self.rate_limiter = RateLimiter()
        self.sanitizer = InputSanitizer()
        self.blocklist = UserBlocklist()
        self.allow_groups = allow_groups
        self._injection_count: dict[str, int] = defaultdict(int)
        self._auto_block_threshold = 3   # auto-block after N injection attempts

    @staticmethod
    def _is_admin(uid: str) -> bool:
        """Returns True if uid matches the admin user — admin bypasses rate limiting.
        Uses settings.TELEGRAM_ADMIN_ID which has a hardcoded fallback, so it works
        even when TELEGRAM_ADMIN_USER_ID is not set in the environment."""
        try:
            from omnix_config.settings import settings
            admin_id = str(settings.TELEGRAM_ADMIN_ID)
        except Exception:
            import os
            admin_id = os.environ.get("TELEGRAM_ADMIN_USER_ID", "")
        return bool(admin_id) and str(uid) == admin_id

    def check(
        self,
        user_id: str,
        chat_type: str,
        message: str,
    ) -> SecurityCheckResult:
        """
        Full security pipeline. Returns SecurityCheckResult.
        result.allowed == False means stop processing and send result.reply_message.
        result.sanitized_message should replace the original message for AI.
        """
        uid = str(user_id)

        # 1. Blocklist
        if self.blocklist.is_blocked(uid):
            logger.warning(f"[SECURITY] Blocked user {uid} attempted message")
            return SecurityCheckResult(
                allowed=False,
                reason="user_blocked",
                reply_message="🚫 Tu acceso a OMNIX ha sido suspendido.",
            )

        # 2. Group filter
        if not self.allow_groups and chat_type in ("group", "supergroup", "channel"):
            return SecurityCheckResult(
                allowed=False,
                reason="group_not_allowed",
                reply_message=_GROUP_BLOCKED_MSG,
            )

        # 3. Rate limiting — admin bypasses entirely
        if self._is_admin(uid):
            allowed, limit_reason = True, ""
        else:
            allowed, limit_reason = self.rate_limiter.check(uid)
        if not allowed:
            violations = self.rate_limiter.get_violations(uid)
            if violations >= 10:
                self.blocklist.block(uid, reason="persistent_rate_limit_abuse")
            return SecurityCheckResult(
                allowed=False,
                reason=limit_reason,
                rate_limited=True,
                reply_message=_RATE_LIMIT_MSG,
            )

        # 4. Input sanitization + injection detection
        sanitized, injection, ssrf = self.sanitizer.sanitize(message)

        if injection:
            self._injection_count[uid] += 1
            count = self._injection_count[uid]
            logger.warning(
                f"[SECURITY] User {uid} injection attempt #{count}"
            )
            if count >= self._auto_block_threshold:
                self.blocklist.block(uid, reason=f"repeated_injection_attempts:{count}")
                return SecurityCheckResult(
                    allowed=False,
                    reason="auto_blocked_injection",
                    injection_detected=True,
                    reply_message="🚫 Actividad sospechosa detectada. Acceso suspendido.",
                )
            return SecurityCheckResult(
                allowed=False,
                reason="prompt_injection_detected",
                injection_detected=True,
                sanitized_message=sanitized,
                reply_message=(
                    "⚠️ Tu mensaje contiene patrones no permitidos por las políticas de seguridad de OMNIX. "
                    "Por favor reformula tu consulta."
                ),
            )

        if ssrf:
            logger.warning(f"[SECURITY] SSRF-risk URL from user {uid} — message blocked")
            return SecurityCheckResult(
                allowed=False,
                reason="ssrf_risk",
                ssrf_risk=True,
                sanitized_message=sanitized,
                reply_message="⚠️ El mensaje contiene URLs no permitidas.",
            )

        return SecurityCheckResult(
            allowed=True,
            sanitized_message=sanitized,
            injection_detected=False,
            ssrf_risk=False,
        )

    def admin_block(self, target_user_id: str, reason: str = "admin_action") -> None:
        """Called from /ban command (future ADR)."""
        self.blocklist.block(target_user_id, reason=reason)

    def admin_unblock(self, target_user_id: str) -> None:
        self.blocklist.unblock(target_user_id)

    def reset_rate_limit(self, user_id: str) -> None:
        """Admin: manually reset a user's rate limit."""
        self.rate_limiter.reset(user_id)

    def get_stats(self) -> dict:
        return {
            "blocked_users": self.blocklist.count,
            "injection_attempts": dict(self._injection_count),
        }


# ─────────────────────────────────────────────
# SINGLETON
# ─────────────────────────────────────────────

_middleware_instance: Optional[BotSecurityMiddleware] = None


def get_security_middleware(allow_groups: bool = False) -> BotSecurityMiddleware:
    global _middleware_instance
    if _middleware_instance is None:
        _middleware_instance = BotSecurityMiddleware(allow_groups=allow_groups)
        logger.info("[SECURITY] BotSecurityMiddleware initialized — enterprise mode active")
    return _middleware_instance
