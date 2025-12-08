"""
OMNIX INSTITUTIONAL+ - Fake Implementations for Testing

Provides mock AI providers and gateways for unit testing.
These fakes implement the same interfaces as real providers
but return predictable responses without making API calls.
"""

import logging
from typing import Optional, List, Dict, Any, AsyncIterator
from dependency_injector import containers, providers

from ..interfaces.ai_gateway import (
    TextGenerationRequest,
    TextGenerationResponse,
    ModelInfo,
    ModelProvider,
)
from ..providers.base_provider import BaseAIProvider
from ..providers.routing_gateway import RoutingAIGateway

logger = logging.getLogger(__name__)


class FakeAIProvider(BaseAIProvider):
    """
    Fake AI provider for testing.
    
    Returns configurable responses without making real API calls.
    """

    def __init__(
        self,
        provider_type: ModelProvider = ModelProvider.GEMINI,
        default_response: str = "This is a test response from FakeAIProvider.",
        should_fail: bool = False,
        latency_ms: float = 50.0,
    ):
        self._provider_type = provider_type
        self._default_response = default_response
        self._should_fail = should_fail
        self._latency_ms = latency_ms
        self._call_count = 0
        self._last_request: Optional[TextGenerationRequest] = None
        super().__init__(api_key="fake-key")

    def _initialize(self) -> None:
        self._available = True

    @property
    def provider_type(self) -> ModelProvider:
        return self._provider_type

    @property
    def default_model(self) -> str:
        return f"fake-{self._provider_type.value}-model"

    def get_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                provider=self._provider_type,
                model_name=self.default_model,
                max_tokens=4096,
                supports_vision=False,
                supports_streaming=True,
                cost_per_1k_tokens=0.0,
            )
        ]

    async def generate_text(
        self,
        request: TextGenerationRequest
    ) -> TextGenerationResponse:
        self._call_count += 1
        self._last_request = request

        if self._should_fail:
            return TextGenerationResponse(
                content="",
                provider_used=self._provider_type,
                model_used=self.default_model,
                success=False,
                error_message="Fake error for testing",
            )

        return TextGenerationResponse(
            content=self._default_response,
            provider_used=self._provider_type,
            model_used=self.default_model,
            tokens_used=len(self._default_response.split()),
            latency_ms=self._latency_ms,
            success=True,
        )

    async def generate_text_stream(
        self,
        request: TextGenerationRequest
    ) -> AsyncIterator[str]:
        """Stream text from fake provider."""
        self._call_count += 1
        self._last_request = request

        if self._should_fail:
            yield "[Error: Fake error for testing]"
            return

        words = self._default_response.split()
        for word in words:
            yield word + " "

    def get_call_count(self) -> int:
        return self._call_count

    def get_last_request(self) -> Optional[TextGenerationRequest]:
        return self._last_request

    def reset(self) -> None:
        self._call_count = 0
        self._last_request = None


class FakeAIGateway(RoutingAIGateway):
    """
    Fake AI gateway for testing.
    
    Pre-configured with FakeAIProvider instances.
    """

    def __init__(
        self,
        default_response: str = "Test response from FakeAIGateway.",
        should_fail: bool = False,
    ):
        self._fake_gemini = FakeAIProvider(
            provider_type=ModelProvider.GEMINI,
            default_response=default_response,
            should_fail=should_fail,
        )
        self._fake_openai = FakeAIProvider(
            provider_type=ModelProvider.OPENAI,
            default_response=default_response,
            should_fail=should_fail,
        )

        super().__init__(
            providers={
                ModelProvider.GEMINI: self._fake_gemini,
                ModelProvider.OPENAI: self._fake_openai,
            },
            primary_provider=ModelProvider.GEMINI,
        )

    def get_fake_gemini(self) -> FakeAIProvider:
        return self._fake_gemini

    def get_fake_openai(self) -> FakeAIProvider:
        return self._fake_openai


def create_test_container(
    default_response: str = "Test response.",
    should_fail: bool = False,
) -> "TestAIServiceContainer":
    """
    Create a test container with fake providers.
    
    Usage:
        container = create_test_container()
        gateway = container.ai_gateway()
        response = await gateway.generate_text(request)
        assert response.success
    """

    class TestAIServiceContainer(containers.DeclarativeContainer):
        fake_gateway = providers.Singleton(
            FakeAIGateway,
            default_response=default_response,
            should_fail=should_fail,
        )

        ai_gateway = fake_gateway

    return TestAIServiceContainer()
