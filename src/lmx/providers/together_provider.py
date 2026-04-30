"""Together AI provider implementation."""

from typing import List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from lmx.providers.base import BaseProvider


class TogetherProvider(BaseProvider):
    """Together AI API provider."""

    def _get_available_models(self) -> List[str]:
        return [
            "deepseek-coder-v2",
            "qwen-2.5-72b",
            "llama-3.1-70b",
        ]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
    )
    async def complete(self, model: str, messages: list, **kwargs) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.together.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 1000),
                },
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    @property
    def name(self) -> str:
        return "together"

    @property
    def speed_score(self) -> float:
        return 0.70