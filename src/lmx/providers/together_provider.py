"""Together AI provider implementation."""

from typing import List

from lmx.providers.base import BaseProvider


class TogetherProvider(BaseProvider):
    """Together AI API provider."""

    def _get_available_models(self) -> List[str]:
        return [
            "deepseek-coder-v2",
            "qwen-2.5-72b",
            "llama-3.1-70b",
        ]

    async def complete(self, model: str, messages: list, **kwargs) -> dict:
        pass

    @property
    def name(self) -> str:
        return "together"

    @property
    def speed_score(self) -> float:
        return 0.70
