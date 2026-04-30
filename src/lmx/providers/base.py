"""Base provider interface."""

from abc import ABC, abstractmethod
from typing import List


class BaseProvider(ABC):
    """Abstract base for LLM providers."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.available_models: List[str] = self._get_available_models()

    @abstractmethod
    def _get_available_models(self) -> List[str]:
        """Return list of available model IDs for this provider."""
        pass

    @abstractmethod
    async def complete(self, model: str, messages: list, **kwargs) -> dict:
        """Send a completion request."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @property
    def speed_score(self) -> float:
        """Relative speed score for this provider (0-1)."""
        return 0.70
