[![PyPI version](https://img.shields.io/pypi/v/lmx.svg)](https://pypi.org/project/lmx/)
[![PyPI downloads](https://img.shields.io/pypi/dm/lmx.svg)](https://pypi.org/project/lmx/)
[![HuggingFace Spaces](https://img.shields.io/badge/🤗%20Spaces-lmx-blue)](https://huggingface.co/spaces/my-ai-stack/lmx)
[![GitHub stars](https://img.shields.io/github/stars/my-ai-stack/lmx.svg)](https://github.com/my-ai-stack/lmx)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

# lmx — The Smart Model Picker for LLMs
# lmx — The Smart Model Picker for LLMs

> **Stop guessing which model to use. Let `lmx` pick the right one — every time.**

`lmx` is a developer CLI that analyzes your task, checks live pricing across every LLM provider you have configured, and recommends the optimal model at the lowest possible cost. It runs 100% locally, tracks your spend across all providers, and learns your preferences over time.

---

## ✨ Why lmx?

- **Save money** — Don't pay GPT-4o rates for tasks Llama 3.1 handles at 1/50th the cost
- **Zero guesswork** — Budget-aware scoring picks the right model for your actual task, not just the cheapest or most powerful
- **Always fast** — Groq's Llama 3.1 70B for simple tasks; o1 for production-grade code. `lmx` knows the difference
- **100% local** — Your API keys never leave your machine. No telemetry, no third-party calls
- **Multi-provider** — OpenAI, Anthropic, Groq, Together AI, Cerebras. Every model, one CLI

---

## 🚀 Quick Start

```bash
pip install lmx
```

Configure your API keys:

```bash
# Add to ~/.zshenv (or ~/.bashrc)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GROQ_API_KEY="gsk-..."
export TOGETHER_API_KEY="..."
export CEREBRAS_API_KEY="..."

source ~/.zshenv
lmx providers   # Verify all providers are active
```

Pick a model:

```bash
lmx pick "Summarize this 10-page legal contract" --budget 0.01
lmx pick "Write a Python API server" --code --budget 5.00
```

---

## 📦 Features

### Smart Model Selection
- **Task classifier** — Zero-shot keyword matching across 6 task types: summarization, code, creative, reasoning, extraction, batch. No API call needed.
- **Budget-aware scoring** — Three-tier scoring that adapts to your budget:
  - Low budget (< $0.50): cost efficiency dominates
  - Medium budget ($0.50–$5.00): quality starts competing with cost
  - High budget (≥ $5.00): quality primary, cost almost irrelevant
- **Benchmark-backed quality scores** — Real HumanEval/MBPP pass@k data, not marketing claims

### Multi-Provider Support
- **5 providers, 16+ models** — OpenAI (4), Anthropic (3), Groq (4), Together AI (3), Cerebras (2)
- **Live context windows** — Respects each model's actual context limit
- **Automatic fallback chain** — Alternatives queued if primary hits rate limits

### Spend Intelligence
- **Unified usage history** — All provider API calls logged to a single SQLite database
- **Savings recommendations** — "You could have saved $X this month using Groq for summaries"
- **Per-model cost tracking** — See exactly how much each recommendation actually cost

### Developer Experience
- **Interactive mode** — TUI walkthrough for exploring models and tradeoffs
- **JSON output** — `lmx pick "task" --json` for scripting and CI integration
- **Stdin support** — `echo "task" | lmx pick --stdin` for CI/CD pipelines
- **ENV overrides** — `LMX_BUDGET`, `LMX_JSON`, `LMX_VERBOSE` environment variable support
- **Configurable weights** — Override default quality/cost/speed weights per task
- **Rich CLI output** — Colorized, formatted output that actually looks good
- **Structured logging** — Privacy-safe task hashing, provider health tracking

### Production-Ready
- **Actual API inference** — All 5 providers make real httpx calls, not stubs
- **Retry with backoff** — Exponential backoff (3 attempts) on timeout/rate-limit errors
- **Model-family token estimation** — OpenAI (0.25x), Anthropic/LLaMA (0.30x) chars-to-tokens
- **Quality scores versioned** — Benchmark-pinned to 2026-05-01 with source attribution

---

## 📋 Command Reference

| Command | Description |
|---------|-------------|
| `lmx pick "task" [flags]` | Get a model recommendation |
| `lmx interactive` | Interactive TUI walkthrough |
| `lmx providers` | Show configured providers and model counts |
| `lmx list-models` | List every available model with pricing |
| `lmx history [flags]` | Browse usage history |
| `lmx config` | View and edit configuration |

### Pick Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--budget`, `-b` | Max cost in USD | `0.05` |
| `--code`, `-c` | Force code task type | — |
| `--batch` | Force batch task type | — |
| `--models`, `-m` | Restrict to specific models | all |
| `--json`, `-j` | JSON output | — |
| `--verbose`, `-v` | Verbose scoring details | — |
| `--stdin` | Read task from stdin (CI/CD) | — |

---

## 🏗️ Architecture

```
lmx pick "Summarize this contract" --budget 0.05
│
├─ Task Classifier (local keyword matching)
│   └─ Output: TaskType.SUMMARIZATION
│
├─ Provider Discovery
│   └─ Loads active providers from environment
│       (OpenAI, Anthropic, Groq, Together AI, Cerebras)
│
├─ Pricing Cache (SQLite, refreshed hourly)
│   └─ Per-model: input/output pricing, context window
│
└─ Recommendation Engine
    ├─ Filter: models within budget × 10
    ├─ Score: quality × 0.40 + cost_efficiency × 0.35 + speed × 0.25
    │         (adjusted by budget tier)
    └─ Sort: top 5 → primary + 2 alternatives
```

---

## 🌍 Supported Providers

### OpenAI
| Model | Context | Strengths |
|-------|---------|-----------|
| `gpt-4o` | 128K | Best overall quality |
| `gpt-4o-mini` | 128K | Fast, cheap, nearGPT-4o quality |
| `o1` | 200K | Reasoning-heavy tasks, production code |
| `o3-mini` | 200K | Compact reasoning |

### Anthropic
| Model | Context | Strengths |
|-------|---------|-----------|
| `claude-3-5-sonnet` | 200K | Best-in-class instruction following |
| `claude-3-5-haiku` | 200K | Fast, affordable Sonnet-quality |
| `claude-3-opus` | 200K | Maximum capability, highest cost |

### Groq
| Model | Context | Strengths |
|-------|---------|-----------|
| `llama-3.1-70b` | 131K | Best price/quality for general tasks |
| `llama-3.1-8b` | 131K | Cheapest model, great for simple tasks |
| `mixtral-8x7b` | 131K | Strong code performance at low cost |
| `gemma-2-9b` | 131K | Lightweight, efficient |

### Together AI
| Model | Context | Strengths |
|-------|---------|-----------|
| `deepseek-coder-v2` | 128K | Best code quality per dollar |
| `qwen-2.5-72b` | 128K | Strong general reasoning, Arabic/Chinese |
| `llama-3.1-70b` | 131K | Same model, different pricing tier |

### Cerebras
| Model | Context | Strengths |
|-------|---------|-----------|
| `llama-3.1-70b` | 131K | Ultra-low latency (wafer-scale GPU) |
| `llama-3.1-8b` | 131K | Fastest possible inference |

---

## ⚙️ Configuration

`lmx` stores config at `~/.config/lmx/config.yaml` (auto-created on first run):

```yaml
# Spending sensitivity: high | medium | low
preferences:
  cost_sensitivity: medium
  quality_threshold: 0.75

# Default budget (USD) when --budget not specified
defaults:
  budget: 0.05
  fallback: true

# Composite score weights (must sum to 1.0)
weights:
  quality: 0.40
  cost: 0.35
  speed: 0.25
```

---

## 📊 Scoring Details

The composite score adapts based on your budget. Quality scores are version-pinned to 2026-05-01 using LMSYS Chatbot Arena, OpenCompass, and HuggingFace Open LLM Leaderboard data.

### Low budget (< $0.50)
```
score = quality × 0.25 + cost_efficiency × 0.50 + speed × 0.25
```

### Medium budget ($0.50 – $5.00)
```
score = quality × 0.45 + cost_efficiency × 0.30 + speed × 0.25
```

### High budget (≥ $5.00)
```
score = quality × 0.55 + speed × 0.30 + premium_bonus
# quality_boost = min(quality × 1.3, 1.0) capped at 1.0
# premium_bonus up to +0.12 for models costing > 30% of budget
```

Budget filter: any model with estimated cost > `budget × 10` is excluded before scoring.

---

## 🧪 Testing

```bash
cd lmx
python3 -m pytest tests/ -v
```

---

## 🤝 Contributing

Contributions welcome. Key areas for improvement:

- **Eval benchmark runner** — Run HumanEval/MBPP against all available models, feed real pass@k scores back into the recommender
- **Spend dashboard** — `lmx spend` command to show monthly savings by task type
- **Ollama local provider** — Add local models to the ranking (no API cost)

---

## 📄 License

MIT — see [LICENSE](LICENSE)
