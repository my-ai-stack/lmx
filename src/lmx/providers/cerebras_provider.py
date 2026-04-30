"""Cerebras provider implementation."""

from typing import List

from lmx.providers.base import BaseProvider


class CerebrasProvider(BaseProvider):
    """Cerebras API provider."""

    def _get_available_models(self) -> List[str]:
        return [
            "llama-3.1-70b",
            "llama-3.1-8b",
        ]

    async def complete(self, model: str, messages: list, **kwargs) -> dict:
        pass

    @property
    def name(self) -> str:
        return "cerebras"

    @property
    def speed_score(self) -> float:
        return 0.95
