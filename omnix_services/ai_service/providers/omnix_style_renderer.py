"""
OMNIX INSTITUTIONAL+ - Omnix Style Renderer

Concrete implementation of StyleRendererProtocol.
Delegates to existing VisualStylesManager for backward compatibility.

Part of Phase 2: Complete DI Container (AI Service Refactoring Roadmap)
"""

import re
from typing import Optional, TYPE_CHECKING
from omnix_core.utils.logger import get_logger
from omnix_config import VERSION_BANNER
from omnix_services.ai_service.interfaces.style_renderer import (
    StyleRendererProtocol,
    RenderOptions,
    ResponseStyle,
    Platform,
)

if TYPE_CHECKING:
    from omnix_services.ai_service.ai_styles import VisualStylesManager

logger = get_logger(__name__)


SIGNATURE_BY_STYLE = {
    ResponseStyle.MINIMAL: "",
    ResponseStyle.STANDARD: "\n\n— OMNIX",
    ResponseStyle.PREMIUM: f"\n\n━━━━━━━━━━━━\n🤖 OMNIX {VERSION_BANNER}",
    ResponseStyle.INSTITUTIONAL: f"\n\n━━━━━━━━━━━━━━━━━━━━\n🏦 OMNIX {VERSION_BANNER} PREMIUM\n🔐 Enterprise-Grade Trading Intelligence"
}


PLATFORM_LIMITS = {
    Platform.TELEGRAM: 4000,  # Telegram hard limit is 4096, keep buffer for emoji/formatting
    Platform.WEB: 10000,
    Platform.API: 50000,
}


class OmnixStyleRenderer:
    """
    Concrete implementation of StyleRendererProtocol.
    
    Wraps the existing VisualStylesManager while providing
    a clean interface that follows the protocol contract.
    
    Features:
    - Response styling with emojis and formatting
    - Platform-specific formatting (Telegram, Web, API)
    - Institutional branding
    - Intelligent truncation
    """
    
    def __init__(self, styles_manager: Optional["VisualStylesManager"] = None):
        """
        Initialize with optional VisualStylesManager.
        
        Args:
            styles_manager: Existing styles manager to delegate to.
                          If None, will be lazy-loaded.
        """
        self._styles_manager = styles_manager
        self._initialized = False
        logger.info("OmnixStyleRenderer created (lazy initialization)")
    
    def _ensure_initialized(self) -> None:
        """Lazy initialization of styles manager."""
        if self._initialized:
            return
        
        if self._styles_manager is None:
            try:
                from omnix_services.ai_service.ai_styles import VisualStylesManager
                self._styles_manager = VisualStylesManager()
                logger.info("VisualStylesManager loaded")
            except ImportError as e:
                logger.error(f"Failed to load VisualStylesManager: {e}")
        
        self._initialized = True
    
    def render_response(
        self,
        content: str,
        options: RenderOptions
    ) -> str:
        """
        Apply styling to raw AI response.
        
        Applies:
        1. Platform-specific formatting
        2. Emoji enhancement (if enabled)
        3. Signature (if enabled)
        4. Length truncation (if needed)
        """
        self._ensure_initialized()
        
        if not content:
            return ""
        
        result = content
        
        result = self.format_for_platform(result, options.platform)
        
        if options.include_emojis and self._styles_manager:
            result = self._apply_emoji_enhancements(result)
        
        if options.include_signature:
            result = self.add_signature(result, options.style)
        
        max_length = options.max_length or PLATFORM_LIMITS.get(options.platform, 4096)
        if len(result) > max_length:
            result = self.truncate_response(result, max_length)
        
        return result
    
    def format_for_platform(
        self,
        content: str,
        platform: Platform
    ) -> str:
        """
        Format content for specific platform.
        
        - Telegram: Markdown-compatible, emoji-rich
        - Web: HTML-compatible
        - API: Plain text, minimal formatting
        """
        if platform == Platform.TELEGRAM:
            return self._format_for_telegram(content)
        elif platform == Platform.WEB:
            return self._format_for_web(content)
        elif platform == Platform.API:
            return self._format_for_api(content)
        
        return content
    
    def add_signature(
        self,
        content: str,
        style: ResponseStyle
    ) -> str:
        """Add OMNIX signature/branding to response."""
        signature = SIGNATURE_BY_STYLE.get(style, "")
        
        if signature and not content.endswith(signature):
            return content + signature
        
        return content
    
    def truncate_response(
        self,
        content: str,
        max_length: int
    ) -> str:
        """
        Truncate response while preserving structure.
        
        Tries to cut at sentence or paragraph boundaries.
        Adds ellipsis to indicate truncation.
        """
        if len(content) <= max_length:
            return content
        
        ellipsis = "\n\n... [respuesta truncada]"
        target_length = max_length - len(ellipsis)
        
        truncated = content[:target_length]
        
        last_paragraph = truncated.rfind("\n\n")
        if last_paragraph > target_length * 0.7:
            truncated = truncated[:last_paragraph]
        else:
            last_sentence = max(
                truncated.rfind(". "),
                truncated.rfind(".\n"),
                truncated.rfind("? "),
                truncated.rfind("! ")
            )
            if last_sentence > target_length * 0.7:
                truncated = truncated[:last_sentence + 1]
        
        return truncated + ellipsis
    
    def _format_for_telegram(self, content: str) -> str:
        """Format content for Telegram."""
        result = content
        
        result = re.sub(r'\*\*(.+?)\*\*', r'*\1*', result)
        
        return result
    
    def _format_for_web(self, content: str) -> str:
        """Format content for Web display."""
        result = content
        
        result = result.replace("\n", "<br>")
        result = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', result)
        result = re.sub(r'\*(.+?)\*', r'<em>\1</em>', result)
        
        return result
    
    def _format_for_api(self, content: str) -> str:
        """Format content for API response (minimal formatting)."""
        result = content
        
        result = re.sub(r'[^\w\s\.\,\!\?\:\;\-\n]', '', result)
        
        return result.strip()
    
    def _apply_emoji_enhancements(self, content: str) -> str:
        """Apply emoji enhancements using VisualStylesManager."""
        if self._styles_manager is None:
            return content
        
        try:
            if hasattr(self._styles_manager, 'premium_transformations'):
                result = content
                for word, replacement in self._styles_manager.premium_transformations.items():
                    pattern = re.compile(re.escape(word), re.IGNORECASE)
                    result = pattern.sub(replacement, result, count=1)
                return result
        except Exception as e:
            logger.warning(f"Error applying emoji enhancements: {e}")
        
        return content
