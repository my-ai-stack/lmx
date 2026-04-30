"""Task classification -- zero-shot with local heuristics."""

from enum import Enum


class TaskType(str, Enum):
    SUMMARIZATION = "summarization"
    CODE = "code"
    CREATIVE = "creative"
    REASONING = "reasoning"
    EXTRACTION = "extraction"
    CHAT = "chat"
    BATCH = "batch"
    UNKNOWN = "unknown"


TASK_KEYWORDS = {
    TaskType.SUMMARIZATION: [
        "summarize", "summary", "tl;dr", "tldr", "condense", "abstract",
        "brief", "overview", "recap", "digest", "synopsis",
    ],
    TaskType.CODE: [
        "code", "debug", "error", "fix", "function", "script", "program",
        "python", "javascript", "rust", "go", "typescript", "bug",
        "compile", "syntax", "refactor", "implement", "algorithm",
    ],
    TaskType.CREATIVE: [
        "description", "write", "draft", "create", "generate", "story",
        "poem", "blog", "article", "essay", "copy", "headline", "caption",
        "creative", "brainstorm", "ideate",
    ],
    TaskType.REASONING: [
        "analyze", "compare", "evaluate", "assess", "explain", "why",
        "reason", "logic", "deduce", "infer", "critique", "review",
        "pros and cons", "advantages", "disadvantages",
    ],
    TaskType.EXTRACTION: [
        "extract", "pull", "scrape", "parse", "find", "locate",
        "identify", "detect", "classify", "tag", "label",
        "entities", "keywords", "data",
    ],
    TaskType.BATCH: [
        "batch", "bulk", "many", "100", "50", "1000", "multiple", "all",
        "every", "each", "list of", "process", "generate",
    ],
}


def classify_task(task: str, code: bool = False, batch: bool = False) -> TaskType:
    """Classify a task description into a task type.

    Uses fast keyword matching. No API calls.
    """
    task_lower = task.lower()

    if code:
        return TaskType.CODE
    if batch:
        return TaskType.BATCH

    scores = {}
    for task_type, keywords in TASK_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in task_lower)
        if score > 0:
            scores[task_type] = score

    if scores:
        return max(scores, key=scores.get)

    return TaskType.CHAT
