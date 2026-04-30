"""Tests for recommender."""

import pytest

from lmx.classifier import TaskType
from lmx.pricing import PricingCache
from lmx.preferences import PreferenceManager
from lmx.recommender import Recommender


@pytest.fixture
def recommender():
    pricing = PricingCache()
    prefs = PreferenceManager()
    return Recommender(pricing, prefs)


@pytest.mark.asyncio
async def test_recommend_summarization(recommender):
    class MockProvider:
        available_models = ["gpt-4o", "claude-3-5-sonnet", "llama-3.1-70b"]
        speed_score = 0.85
        name = "mock"

    providers = {
        "openai": MockProvider(),
        "anthropic": MockProvider(),
        "groq": MockProvider(),
    }

    recs = await recommender.recommend(
        task="Summarize this",
        task_type=TaskType.SUMMARIZATION,
        budget=0.10,
        providers=providers,
    )

    assert len(recs) > 0
    assert recs[0].quality_score > 0.7