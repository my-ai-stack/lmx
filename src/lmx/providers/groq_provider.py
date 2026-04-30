"""Groq provider implementation."""

from typing import List

from lmx.providers.base import BaseProvider


class GroqProvider(BaseProvider):
    """Groq API provider."""

    def _get_available_models(self) -> List[str]:
        return [
            "llama-3.1-70b",
            "llama-3.1-8b",
            "mixtral-8x7b",
            "gemma-2-9b",
        ]

    async def complete(self, model: str, messages: list, **kwargs) -> dict:
        pass

    @property
    def name(self) -> str:
        return "groq"

    @property
    def speed_score(self) -> float:
        return 0.98
