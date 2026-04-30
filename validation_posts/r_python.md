# Validation Post: r/Python

**Title:** lmx -- A CLI tool that picks the cheapest LLM for your Python task

**Body:**

Built a Python CLI that saves me from overpaying for LLM APIs. It classifies your task (code, summarization, creative, etc.), checks live pricing across providers, and recommends the best model for your budget.

```bash
pip install lmx
export OPENAI_API_KEY="sk-..."
export GROQ_API_KEY="gsk_..."

lmx "Debug this asyncio error" --code
# Recommends GPT-4o ($0.023) with DeepSeek Coder alternative ($0.009)
```

Stack: Typer, Rich, SQLite, httpx. Fully typed, async, tested.

**Feedback welcome -- would you use this?**

https://github.com/my-ai-stack/lmx
