"""User preference management."""

import sqlite3
from pathlib import Path
from typing import Dict, Optional

import yaml
from platformdirs import user_config_dir, user_data_dir


class PreferenceManager:
    """Manages user preferences and usage history."""

    def __init__(self):
        self.config_dir = Path(user_config_dir("lmx", "my-ai-stack"))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = Path(user_data_dir("lmx", "my-ai-stack"))
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.config_path = self.config_dir / "config.yaml"
        self.db_path = self.data_dir / "history.db"

        self._init_db()
        self._load_config()

    def _init_db(self):
        """Initialize usage history database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    task TEXT,
                    task_type TEXT,
                    provider TEXT,
                    model_id TEXT,
                    estimated_cost REAL,
                    actual_cost REAL,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    success BOOLEAN
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS savings (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    task TEXT,
                    recommended_model TEXT,
                    expensive_model TEXT,
                    savings_amount REAL
                )
            """)

    def _load_config(self):
        """Load or create default config."""
        if not self.config_path.exists():
            default_config = {
                "preferences": {
                    "cost_sensitivity": "medium",
                    "quality_threshold": 0.80,
                    "speed_priority": False,
                },
                "defaults": {
                    "budget": 0.05,
                    "fallback": True,
                },
                "weights": {
                    "quality": 0.40,
                    "cost": 0.35,
                    "speed": 0.25,
                },
            }
            with open(self.config_path, "w") as f:
                yaml.dump(default_config, f, default_flow_style=False)

        with open(self.config_path) as f:
            self.config = yaml.safe_load(f)

    @property
    def default_budget(self) -> float:
        return self.config.get("defaults", {}).get("budget", 0.05)

    def get_weights(self) -> Dict[str, float]:
        """Get scoring weights based on preferences."""
        weights = self.config.get("weights", {
            "quality": 0.40,
            "cost": 0.35,
            "speed": 0.25,
        })

        sensitivity = self.config.get("preferences", {}).get("cost_sensitivity", "medium")
        if sensitivity == "high":
            weights = {"quality": 0.30, "cost": 0.50, "speed": 0.20}
        elif sensitivity == "low":
            weights = {"quality": 0.55, "cost": 0.20, "speed": 0.25}

        return weights

    def adjust_quality(self, model_id: str, base_score: float) -> float:
        """Adjust quality score based on user feedback history."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT AVG(quality_feedback) FROM (
                    SELECT 5 as quality_feedback FROM usage WHERE model_id = ? AND success = 1
                    UNION ALL
                    SELECT 3 FROM usage WHERE model_id = ? AND success = 0
                )
            """, (model_id, model_id)).fetchone()

            if row and row[0]:
                user_avg = row[0] / 5.0
                return (base_score * 0.85) + (user_avg * 0.15)

        return base_score

    def log_usage(
        self,
        task: str,
        task_type: str,
        provider: str,
        model_id: str,
        estimated_cost: float,
        actual_cost: Optional[float] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        success: bool = True,
    ):
        """Log a request for history tracking."""
        from datetime import datetime

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO usage
                (timestamp, task, task_type, provider, model_id, estimated_cost,
                 actual_cost, input_tokens, output_tokens, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                task[:500],
                task_type,
                provider,
                model_id,
                estimated_cost,
                actual_cost,
                input_tokens,
                output_tokens,
                success,
            ))

    def get_total_spend(self, period: str = "this-month") -> float:
        """Get total spend for a period."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT SUM(actual_cost) FROM usage
                WHERE actual_cost IS NOT NULL
            """).fetchone()
            return row[0] or 0.0

    def get_savings(self) -> float:
        """Get potential savings from usage history."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT SUM(savings_amount) FROM savings
            """).fetchone()
            return row[0] or 0.0

    def get_history(self, limit: int = 20):
        """Get recent usage history."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT timestamp, task, task_type, provider, model_id,
                       estimated_cost, actual_cost, success
                FROM usage
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return rows

    def display_config(self) -> str:
        """Return formatted config for display."""
        with open(self.config_path) as f:
            return f.read()
