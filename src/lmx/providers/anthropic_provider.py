"""Anthropic provider implementation."""

from typing import List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from lmx.providers.base import BaseProvider


class AnthropicProvider(BaseProvider):
    """Anthropic API provider."""

    def _get_available_models(self) -> List[str]:
        return [
            "claude-3-5-sonnet",
            "claude-3-5-haiku",
            "claude-3-opus",
        ]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError)),
    )
    async def complete(self, model: str, messages: list, **kwargs) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": kwargs.get("max_tokens", 1000),
                    "temperature": kwargs.get("temperature", 0.7),
                },
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def speed_score(self) -> float:
        return 0.80
