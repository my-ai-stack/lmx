"""Provider registry and discovery."""

import os
from typing import Dict, List

from lmx.providers.base import BaseProvider


def get_available_providers() -> Dict[str, BaseProvider]:
    """Discover and instantiate available providers.

    A provider is available if its API key is set in environment.
    """
    providers = {}

    from lmx.providers.openai_provider import OpenAIProvider
    from lmx.providers.anthropic_provider import AnthropicProvider
    from lmx.providers.groq_provider import GroqProvider
    from lmx.providers.together_provider import TogetherProvider
    from lmx.providers.cerebras_provider import CerebrasProvider

    provider_map = {
        "openai": (OpenAIProvider, "OPENAI_API_KEY"),
        "anthropic": (AnthropicProvider, "ANTHROPIC_API_KEY"),
        "groq": (GroqProvider, "GROQ_API_KEY"),
        "together": (TogetherProvider, "TOGETHER_API_KEY"),
        "cerebras": (CerebrasProvider, "CEREBRAS_API_KEY"),
    }

    for name, (cls, env_key) in provider_map.items():
        api_key = os.environ.get(env_key)
        if api_key:
            try:
                providers[name] = cls(api_key=api_key)
            except Exception:
                pass

    return providers
