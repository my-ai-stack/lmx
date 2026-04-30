"""Anthropic provider implementation."""

from typing import List

from lmx.providers.base import BaseProvider


class AnthropicProvider(BaseProvider):
    """Anthropic API provider."""

    def _get_available_models(self) -> List[str]:
        return [
            "claude-3-5-sonnet",
            "claude-3-5-haiku",
            "claude-3-opus",
        ]

    async def complete(self, model: str, messages: list, **kwargs) -> dict:
        pass

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def speed_score(self) -> float:
        return 0.80
