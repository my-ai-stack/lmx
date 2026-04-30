"""OpenAI provider implementation."""

from typing import List

from lmx.providers.base import BaseProvider


class OpenAIProvider(BaseProvider):
    """OpenAI API provider."""

    def _get_available_models(self) -> List[str]:
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "o1",
            "o3-mini",
        ]

    async def complete(self, model: str, messages: list, **kwargs) -> dict:
        pass

    @property
    def name(self) -> str:
        return "openai"

    @property
    def speed_score(self) -> float:
        return 0.85
