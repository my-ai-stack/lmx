# Validation Post: r/LocalLLaMA

**Title:** I built a CLI that tells me which LLM to use for any task -- saves me $200+/month

**Body:**

I got tired of overpaying for GPT-4o on tasks that Llama 3.1 handled fine. Built `lmx` -- a local CLI that analyzes your task, checks live pricing across providers you have keys for, and recommends the optimal model.

```bash
lmx "Summarize this contract" --budget 0.01
# Recommends Claude 3.5 Sonnet with Groq fallback
# Shows: cost, quality score, why this model, 2 alternatives
```

Also tracks spend across all your keys: "You could have saved $180 this month using Groq for summaries."

Supports OpenAI, Anthropic, Groq, Together, Cerebras. 100% local -- your keys, your data.

**Would you use this? What features would make it indispensable?**

GitHub: https://github.com/my-ai-stack/lmx
