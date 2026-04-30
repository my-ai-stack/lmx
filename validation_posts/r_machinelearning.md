# Validation Post: r/machinelearning

**Title:** Show HN-style: Local tool for cost-aware LLM selection with personalized benchmarks

**Body:**

**Problem:** I have 6 provider accounts, no idea which model is best for my specific task, and I'm definitely overpaying.

**Solution:** `lmx` -- benchmark your actual tasks against multiple models, build a preference model, get recommendations that balance cost/quality for YOUR workload.

```bash
lmx benchmark --task my_coding_task --models gpt-4o,claude,deepseek
```

Open source, runs locally, uses your own API keys. No middleman.

**Would this solve your model selection headache?**

Repo: https://github.com/my-ai-stack/lmx
