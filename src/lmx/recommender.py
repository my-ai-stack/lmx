"""Core recommendation engine."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from lmx.classifier import TaskType
from lmx.pricing import ModelPricing, PricingCache
from lmx.preferences import PreferenceManager
from lmx.providers.base import BaseProvider


@dataclass
class Recommendation:
    """A single model recommendation."""

    provider: str
    model_id: str
    task_type: TaskType
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost: float
    context_window: int
    quality_score: float
    speed_score: float
    fallback_for: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model_id,
            "task_type": self.task_type.value,
            "estimated_cost": round(self.estimated_cost, 4),
            "context_window": self.context_window,
            "quality_score": round(self.quality_score, 2),
            "speed_score": round(self.speed_score, 2),
            "fallback_for": self.fallback_for,
        }


# Quality scores — version pinned to 2026-05-01 based on public benchmark data
# Sources: LMSYS Chatbot Arena, OpenCompass, HuggingFace Open LLM Leaderboard
QUALITY_SCORES = {
    TaskType.SUMMARIZATION: {
        "claude-3-5-sonnet": 0.94,
        "claude-3-opus": 0.96,
        "gpt-4o": 0.92,
        "o1": 0.93,
        "llama-3.1-70b": 0.78,
        "deepseek-coder-v2": 0.72,
        "gpt-4o-mini": 0.80,
        "llama-3.1-8b": 0.70,
        "mixtral-8x7b": 0.74,
    },
    TaskType.CODE: {
        "claude-3-5-sonnet": 0.94,
        "claude-3-opus": 0.96,
        "gpt-4o": 0.96,
        "o1": 0.97,
        "o3-mini": 0.95,
        "deepseek-coder-v2": 0.91,
        "llama-3.1-70b": 0.82,
        "gpt-4o-mini": 0.84,
        "llama-3.1-8b": 0.72,
        "qwen-2.5-72b": 0.80,
    },
    TaskType.CREATIVE: {
        "claude-3-5-sonnet": 0.88,
        "gpt-4o": 0.90,
        "llama-3.1-70b": 0.82,
        "claude-3-opus": 0.92,
        "gpt-4o-mini": 0.80,
        "qwen-2.5-72b": 0.78,
    },
    TaskType.REASONING: {
        "o1": 0.98,
        "o3-mini": 0.95,
        "claude-3-opus": 0.94,
        "claude-3-5-sonnet": 0.90,
        "gpt-4o": 0.88,
    },
    TaskType.EXTRACTION: {
        "claude-3-5-sonnet": 0.92,
        "gpt-4o": 0.90,
        "llama-3.1-70b": 0.80,
        "gpt-4o-mini": 0.82,
    },
    TaskType.CHAT: {
        "claude-3-5-sonnet": 0.90,
        "gpt-4o": 0.90,
        "llama-3.1-70b": 0.85,
        "gpt-4o-mini": 0.82,
    },
    TaskType.BATCH: {
        "llama-3.1-70b": 0.82,
        "gpt-4o-mini": 0.85,
        "claude-3-5-haiku": 0.80,
        "mixtral-8x7b": 0.78,
        "llama-3.1-8b": 0.72,
    },
}

# Output token estimates per task type (model output, not input)
TOKEN_ESTIMATES = {
    TaskType.SUMMARIZATION: 800,     # short-to-medium response
    TaskType.CODE: 1500,             # verbose code generation
    TaskType.CREATIVE: 600,          # short creative output
    TaskType.REASONING: 2000,        # detailed explanation
    TaskType.EXTRACTION: 400,        # concise extraction
    TaskType.CHAT: 500,              # conversational
    TaskType.BATCH: 300,             # short batch items
}


def estimate_tokens(task: str, model_id: str = "") -> tuple[int, int]:
    """Estimate tokens from task string.
    
    Uses model-family-aware approximation:
    - OpenAI (gpt-*): ~4 chars/token
    - Anthropic (claude-*): ~3.3 chars/token
    - LLaMA/Grok/Together (llama, mixtral, gemma, deepseek, qwen): ~3.3 chars/token
    - Default: ~4 chars/token
    """
    if model_id.startswith("gpt"):
        input_tokens = max(50, int(len(task) * 0.25))
    elif model_id.startswith("claude"):
        input_tokens = max(50, int(len(task) * 0.30))
    elif any(m in model_id for m in ["llama", "mixtral", "gemma", "deepseek", "qwen"]):
        input_tokens = max(50, int(len(task) * 0.30))
    else:
        input_tokens = max(50, int(len(task) * 0.25))
    return input_tokens, 0  # output estimated per task type in _score_model


class Recommender:
    """Recommends the best model for a task."""

    def __init__(self, pricing: PricingCache, preferences: PreferenceManager):
        self.pricing = pricing
        self.preferences = preferences

    async def recommend(
        self,
        task: str,
        task_type: TaskType,
        budget: float,
        providers: Dict[str, BaseProvider],
        model_filter: Optional[List[str]] = None,
    ) -> List[Recommendation]:
        """Get ranked recommendations for a task."""

        candidates = []
        for provider_name, provider in providers.items():
            for model_id in provider.available_models:
                if model_filter and model_id not in model_filter:
                    continue

                pricing = self.pricing.get_model(model_id)
                if pricing:
                    candidates.append((provider_name, model_id, pricing, provider))

        scored = []
        for provider_name, model_id, pricing, provider in candidates:
            rec = self._score_model(
                provider_name, model_id, pricing, provider, task_type, task, budget
            )
            if rec and rec.estimated_cost <= budget * 10:
                scored.append(rec)

        scored.sort(key=lambda r: self._composite_score(r, budget=budget), reverse=True)

        if scored:
            primary = scored[0]
            for alt in scored[1:3]:
                alt.fallback_for = primary.model_id

        return scored[:5]

    def _score_model(
        self,
        provider: str,
        model_id: str,
        pricing: ModelPricing,
        provider_obj: BaseProvider,
        task_type: TaskType,
        task: str,
        budget: float,
    ) -> Optional[Recommendation]:
        """Score a single model for a task."""

        output_tokens = TOKEN_ESTIMATES.get(task_type, 1000)
        input_tokens, _ = estimate_tokens(task, model_id)

        if pricing.context_window < input_tokens:
            return None

        cost = pricing.estimate_cost(input_tokens, output_tokens)

        quality = QUALITY_SCORES.get(task_type, {}).get(
            model_id, 0.75
        )

        speed = provider_obj.speed_score

        quality = self.preferences.adjust_quality(model_id, quality)

        return Recommendation(
            provider=provider,
            model_id=model_id,
            task_type=task_type,
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens,
            estimated_cost=cost,
            context_window=pricing.context_window,
            quality_score=quality,
            speed_score=speed,
        )

    def _composite_score(self, rec: Recommendation, budget: float = 1.0) -> float:
        """Calculate composite score for ranking.

        Budget-aware: at low budgets, cost dominates. At high budgets,
        quality becomes the primary factor and cost barely matters.
        """
        weights = self.preferences.get_weights()

        if budget < 0.5:
            # Low budget: cost efficiency is king
            cost_score = 1.0 / (1.0 + rec.estimated_cost * 50)
            return rec.quality_score * 0.3 + cost_score * 0.45 + rec.speed_score * 0.25

        elif budget < 5.0:
            # Medium budget: quality matters more
            cost_ratio = max(0, 1.0 - rec.estimated_cost / budget)
            return rec.quality_score * 0.45 + cost_ratio * 0.30 + rec.speed_score * 0.25

        else:
            # High budget: quality is primary, with a premium bonus for expensive
            # quality models that offsets their cost disadvantage slightly.
            quality_boost = min(rec.quality_score * 1.3, 1.0)
            # Premium bonus: expensive quality models (cost > 30% of budget) get a
            # small bonus up to +0.12 to reflect that higher quality justifies cost
            premium_bonus = (
                min((rec.estimated_cost - budget * 0.3) / (budget * 3), 0.12)
                if rec.estimated_cost > budget * 0.3 else 0.0
            )
            return quality_boost * 0.55 + rec.speed_score * 0.30 + premium_bonus
