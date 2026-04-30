# Validation Post: r/selfhosted

**Title:** lmx -- Local LLM model picker that runs entirely on your machine

**Body:**

No SaaS, no data leaving your machine, no vendor lock-in. `lmx` reads your API keys from env, maintains a local SQLite cache of pricing, and recommends models based on your preferences.

```bash
lmx "Summarize this 50-page PDF" --budget 0.05
```

Everything stays local:
- Pricing cache: ~/.local/share/lmx/pricing.db
- Usage history: ~/.local/share/lmx/history.db
- Config: ~/.config/lmx/config.yaml

**Would you use a local tool for LLM cost optimization?**

https://github.com/my-ai-stack/lmx
