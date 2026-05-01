"""Live pricing cache from LLM providers."""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from platformdirs import user_data_dir


class ModelPricing:
    """Pricing info for a single model."""

    def __init__(
        self,
        provider: str,
        model_id: str,
        input_price_per_1k: float,
        output_price_per_1k: float,
        context_window: int,
        supports_json: bool = False,
        supports_vision: bool = False,
    ):
        self.provider = provider
        self.model_id = model_id
        self.input_price = input_price_per_1k / 1000
        self.output_price = output_price_per_1k / 1000
        self.context_window = context_window
        self.supports_json = supports_json
        self.supports_vision = supports_vision

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a request."""
        return (input_tokens * self.input_price) + (output_tokens * self.output_price)


class PricingCache:
    """Caches pricing data from providers."""

    def __init__(self):
        self.data_dir = Path(user_data_dir("lmx", "my-ai-stack"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "pricing.db"
        self._init_db()
        self._load_static_pricing()

    def _init_db(self):
        """Initialize SQLite cache."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pricing (
                    provider TEXT,
                    model_id TEXT,
                    input_price REAL,
                    output_price REAL,
                    context_window INTEGER,
                    supports_json BOOLEAN,
                    supports_vision BOOLEAN,
                    updated_at TIMESTAMP,
                    PRIMARY KEY (provider, model_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP
                )
            """)

    def _load_static_pricing(self):
        """Load static pricing data (fallback when APIs fail)."""
        self.static_pricing: Dict[str, ModelPricing] = {
            # OpenAI
            "gpt-4o": ModelPricing("openai", "gpt-4o", 2.50, 10.00, 128000, True, True),
            "gpt-4o-mini": ModelPricing("openai", "gpt-4o-mini", 0.15, 0.60, 128000, True, True),
            "o1": ModelPricing("openai", "o1", 15.00, 60.00, 200000, True, False),
            "o3-mini": ModelPricing("openai", "o3-mini", 1.10, 4.40, 200000, True, False),
            # Anthropic
            "claude-3-5-sonnet": ModelPricing("anthropic", "claude-3-5-sonnet", 3.00, 15.00, 200000, True, True),
            "claude-3-5-haiku": ModelPricing("anthropic", "claude-3-5-haiku", 0.80, 4.00, 200000, True, False),
            "claude-3-opus": ModelPricing("anthropic", "claude-3-opus", 15.00, 75.00, 200000, True, True),
            # Groq
            "llama-3.1-70b": ModelPricing("groq", "llama-3.1-70b", 0.59, 0.79, 131072, True, False),
            "llama-3.1-8b": ModelPricing("groq", "llama-3.1-8b", 0.05, 0.08, 131072, True, False),
            "mixtral-8x7b": ModelPricing("groq", "mixtral-8x7b", 0.24, 0.24, 32768, True, False),
            "gemma-2-9b": ModelPricing("groq", "gemma-2-9b", 0.20, 0.20, 8192, True, False),
            # Together AI
            "deepseek-coder-v2": ModelPricing("together", "deepseek-coder-v2", 1.20, 1.20, 128000, True, False),
            "qwen-2.5-72b": ModelPricing("together", "qwen-2.5-72b", 1.20, 1.20, 128000, True, False),
            # Cerebras (wafer-scale GPU, fastest inference)
            "gpt-oss-120b": ModelPricing("cerebras", "gpt-oss-120b", 0.60, 0.60, 128000, True, False),
            "qwen-3-235b-a22b-instruct-2507": ModelPricing("cerebras", "qwen-3-235b-a22b-instruct-2507", 0.80, 0.80, 128000, True, False),
            "llama3.1-8b": ModelPricing("cerebras", "llama3.1-8b", 0.03, 0.03, 131072, True, False),
            "zai-glm-4.7": ModelPricing("cerebras", "zai-glm-4.7", 0.04, 0.04, 131072, True, False),
        }

    async def refresh(self):
        """Refresh pricing from provider APIs (future)."""
        last_update = self._get_last_update()
        if last_update and datetime.now() - last_update < timedelta(hours=1):
            return
        self._save_to_cache()

    def _get_last_update(self) -> Optional[datetime]:
        """Get last cache update time."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT updated_at FROM cache_meta WHERE key = 'last_update'"
            ).fetchone()
            if row:
                return datetime.fromisoformat(row[0])
        return None

    def _save_to_cache(self):
        """Save static pricing to cache."""
        with sqlite3.connect(self.db_path) as conn:
            for model in self.static_pricing.values():
                conn.execute("""
                    INSERT OR REPLACE INTO pricing
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    model.provider,
                    model.model_id,
                    model.input_price * 1000,
                    model.output_price * 1000,
                    model.context_window,
                    model.supports_json,
                    model.supports_vision,
                    datetime.now().isoformat(),
                ))
            conn.execute("""
                INSERT OR REPLACE INTO cache_meta VALUES (?, ?, ?)
            """, ("last_update", datetime.now().isoformat(), datetime.now().isoformat()))

    def get_model(self, model_id: str) -> Optional[ModelPricing]:
        """Get pricing for a specific model."""
        return self.static_pricing.get(model_id)

    def all_models(self):
        """Yield all known model pricings."""
        return list(self.static_pricing.values())
