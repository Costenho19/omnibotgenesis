"""
OMNIX — LLM Input Sanitizer (ISR-017)
ISR-2026-Q2-001 · Prompt Injection Containment Layer

Provides:
  1. User-message sanitization before LLM prompt construction.
  2. Length enforcement to prevent context-window DoS.
  3. Audit logging of detected injection attempts.
  4. Query-isolation helpers to ensure DB queries are bound to the
     authenticated user_id, never to text extracted from user messages.

This module NEVER blocks governance decisions — it only protects the
conversational AI layer (Telegram bot) from prompt-injection attacks.
Governance receipts and the 11-checkpoint pipeline are unaffected.

Return contract (v2 — ISR-017 enriched):
  sanitize_user_message(text) → (sanitized_text, flags: list[str])
  flags is a list of zero or more of: "TRUNCATED", "INJECTION_MARKER", "NULL_INPUT"
  An empty list means no modification was needed.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger("OMNIX.AI.InputSanitizer")

MAX_USER_MESSAGE_CHARS: int = 2000
MAX_MESSAGE_LENGTH: int = MAX_USER_MESSAGE_CHARS

INJECTION_MARKERS: list[str] = [
    r"ignore\s+(all\s+)?previous\s+instructions?",
    r"ignore\s+(all\s+)?prior\s+instructions?",
    r"disregard\s+(all\s+)?previous",
    r"forget\s+(all\s+)?previous",
    r"\[INST\]",
    r"<\|system\|>",
    r"<\|assistant\|>",
    r"<\|user\|>",
    r"\bsystem\s*:",
    r"\bassistant\s*:",
    r"act\s+as\s+(if\s+you\s+are|a\s+different)",
    r"you\s+are\s+now\s+(a|an)\s+",
    r"new\s+persona",
    r"override\s+(your\s+)?(previous\s+)?instructions?",
    r"pretend\s+(you\s+are|to\s+be)",
    r"jailbreak",
    r"dan\s+mode",
    r"developer\s+mode",
    r"ignore\s+your\s+(training|guidelines|rules)",
    r"reveal\s+(your\s+)?(system\s+)?prompt",
    r"print\s+(your\s+)?(system\s+)?prompt",
    r"show\s+(me\s+)?(your\s+)?(system\s+)?prompt",
]

_COMPILED_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE | re.DOTALL) for p in INJECTION_MARKERS
]


def sanitize_user_message(text: Optional[str]) -> tuple[str, list[str]]:
    """
    Sanitize a raw user message before inserting into an LLM prompt.

    Returns:
        (sanitized_text, flags)
        flags: list of zero or more strings — "TRUNCATED", "INJECTION_MARKER", "NULL_INPUT"
        An empty list means the message passed through unchanged.

    Never raises. On any error returns (original_text or "", []) to preserve
    the user's ability to get a response even if sanitization fails.
    """
    if text is None:
        return "", ["NULL_INPUT"]
    if not text:
        return text, []

    try:
        flags: list[str] = []

        if len(text) > MAX_USER_MESSAGE_CHARS:
            logger.warning(
                f"[InputSanitizer][ISR-017] Message truncated: {len(text)} → {MAX_USER_MESSAGE_CHARS} chars"
            )
            _SUFFIX = "… [mensaje truncado por límite de seguridad]"
            text = text[:MAX_USER_MESSAGE_CHARS - len(_SUFFIX)] + _SUFFIX
            flags.append("TRUNCATED")

        for pattern in _COMPILED_PATTERNS:
            if pattern.search(text):
                logger.warning(
                    f"[InputSanitizer][ISR-017] Injection marker detected: "
                    f"pattern='{pattern.pattern[:40]}' "
                    f"message_preview='{text[:80].replace(chr(10), ' ')}'"
                )
                text = pattern.sub("[contenido filtrado]", text)
                if "INJECTION_MARKER" not in flags:
                    flags.append("INJECTION_MARKER")

        return text, flags

    except Exception as exc:
        logger.error(f"[InputSanitizer][ISR-017] Sanitization error (passthrough): {exc}")
        return text if text else "", []


def enforce_query_isolation(
    requested_user_id: Optional[str],
    authenticated_user_id: Optional[str],
) -> Optional[str]:
    """
    Ensure that database queries are scoped to the authenticated user_id,
    never to a user_id extracted from message text.

    Returns the safe user_id to use for DB queries, or None if both are absent.

    If the requested_user_id (from message text) differs from the
    authenticated_user_id, logs a security warning and returns the
    authenticated one.
    """
    if not authenticated_user_id:
        return None

    if requested_user_id and str(requested_user_id) != str(authenticated_user_id):
        logger.warning(
            f"[InputSanitizer][ISR-017] Query isolation violation prevented: "
            f"message requested user_id='{requested_user_id}' "
            f"but authenticated user_id='{authenticated_user_id}'. "
            f"Using authenticated id."
        )

    return authenticated_user_id
