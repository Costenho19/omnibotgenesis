"""
OMNIX INSTITUTIONAL+ - Style Renderer Protocol

Defines the contract for response formatting and visual styling.
Separates presentation logic from AI generation.
"""

from typing import Protocol, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ResponseStyle(Enum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    PREMIUM = "premium"
    INSTITUTIONAL = "institutional"


class Platform(Enum):
    TELEGRAM = "telegram"
    WEB = "web"
    API = "api"


@dataclass
class RenderOptions:
    style: ResponseStyle = ResponseStyle.PREMIUM
    platform: Platform = Platform.TELEGRAM
    include_emojis: bool = True
    include_signature: bool = True
    max_length: Optional[int] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class StyleRendererProtocol(Protocol):
    """
    Protocol for response styling and formatting.
    
    Responsibilities:
    - Apply visual formatting to AI responses
    - Adapt output for different platforms (Telegram, Web, API)
    - Handle institutional branding
    """

    def render_response(
        self,
        content: str,
        options: RenderOptions
    ) -> str:
        """Apply styling to raw AI response."""
        ...

    def format_for_platform(
        self,
        content: str,
        platform: Platform
    ) -> str:
        """Format content for specific platform."""
        ...

    def add_signature(
        self,
        content: str,
        style: ResponseStyle
    ) -> str:
        """Add OMNIX signature/branding to response."""
        ...

    def truncate_response(
        self,
        content: str,
        max_length: int
    ) -> str:
        """Truncate response while preserving structure."""
        ...
